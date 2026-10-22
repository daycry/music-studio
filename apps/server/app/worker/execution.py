"""Padre local de post.audio; custodia retenida hasta join real."""

import hashlib
import json
import logging
import os
import secrets
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty

from audio_post.manifest import safe_path
from audio_post.private_context import PreparedContext, prepare_context_once
from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.migrations.cpu_publication_invariants import cas, validate_connection

from .contracts import (
    PerTakeResult,
    PostPlan,
    TakeFailure,
    TakeSuccess,
    canonical_sha256,
)
from .custody import Owner
from .custody_linux import LinuxGroup
from .packages import (
    MAX_PLAN_BYTES,
    canonical_bytes,
    read_file,
    tool,
    write_once,
)
from .planning import compose_post_plan, load_tool_pin
from .publications import Publisher


class CpuAudioService:
    def __init__(
        self, engine, root, *, coordinator, bus, ffmpeg, owner_id=None, logger=None
    ):
        self.log = logger or logging.getLogger(__name__)
        self.engine, self.root, self.ffmpeg = engine, Path(root), Path(ffmpeg)
        self.owner_id = owner_id
        self.publisher = Publisher(engine, root, coordinator, bus)
        self.owners = {}
        self.job_executions = {}
        self._guard = threading.RLock()

    def claim_job(self, job_id):
        """Atomically acquire one of the two server CPU slots for post.audio."""
        stamp = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        with Session(self.engine) as session, session.begin():
            job = session.get(models.Job, job_id)
            active = session.scalar(
                select(func.count())
                .select_from(models.Job)
                .where(
                    models.Job.lane == "cpu",
                    models.Job.status.in_(["running", "interrupted"]),
                )
            )
            if (
                not job
                or job.task != "post.audio"
                or job.lane != "cpu"
                or (self.owner_id is not None and job.owner_id != self.owner_id)
                or job.status != "queued"
                or job.attempt != 0
                or job.cancel_requested_at is not None
                or active >= 2
            ):
                return False
            job.status = "running"
            job.attempt = 1
            job.started_at = stamp
            job.updated_at = stamp
            return True

    def plan_for_job(self, job_id, execution_id):
        """Read the winning generation chain and compose its private plan."""
        with Session(self.engine) as session:
            post = session.get(models.Job, job_id)
            if (
                not post
                or post.task != "post.audio"
                or (self.owner_id is not None and post.owner_id != self.owner_id)
            ):
                raise ValueError("POST_JOB_INVALID")
            inputs = post.request.get("inputs", [])
            if not isinstance(inputs, list) or not inputs:
                raise ValueError("POST_INPUTS_INVALID")
            generation_id = inputs[0].get("ref", {}).get("id")
            generation = session.get(models.Job, generation_id)
            if not generation:
                raise ValueError("POST_CHAIN_NOT_READY")
            attempt = session.scalar(
                select(models.JobAttempt).where(
                    models.JobAttempt.job_id == generation.id,
                    models.JobAttempt.ordinal == generation.attempt,
                    models.JobAttempt.deleted_at.is_(None),
                )
            )
            takes = list(
                session.scalars(
                    select(models.Take)
                    .where(
                        models.Take.job_id == generation.id,
                        models.Take.owner_id == post.owner_id,
                        models.Take.song_id == post.song_id,
                        models.Take.deleted_at.is_(None),
                    )
                    .order_by(models.Take.variant_index)
                )
            )
            artifacts = (
                attempt.terminal.data["artifacts"]
                if attempt and attempt.terminal and attempt.terminal.type == "done"
                else []
            )
            return compose_post_plan(
                post=post,
                generation=generation,
                attempt=attempt,
                takes=takes,
                artifacts=artifacts,
                root=self.root,
                execution_id=execution_id,
                tool_pin=load_tool_pin(),
            )

    def fail_plan(self, job_id, code):
        """Durably fail a plan that could not be composed before custody."""
        stamp = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        with Session(self.engine) as session, session.begin():
            job = session.get(models.Job, job_id)
            if not job or job.status not in {"queued", "running"}:
                return False
            custody_unknown = session.scalar(
                select(models.CpuExecution.id).where(
                    models.CpuExecution.job_id == job_id,
                    models.CpuExecution.state.not_in(
                        ["finished", "failed", "cancelled"]
                    ),
                )
            )
            if custody_unknown is not None:
                job.status = "interrupted"
                job.error_code = "CPU_CUSTODY_UNKNOWN"
                job.error = "La custodia del proceso CPU no estÃ¡ confirmada"
                job.updated_at = stamp
                return False
            job.status = "failed"
            job.error_code = code
            job.error = code
            job.finished_at = stamp
            job.updated_at = stamp
            takes = session.scalars(
                select(models.Take).where(
                    models.Take.job_id == job_id,
                    models.Take.status.in_(["queued", "running"]),
                    models.Take.deleted_at.is_(None),
                )
            )
            for take in takes:
                take.status = "failed"
                take.error_code = code
                take.updated_at = stamp
            return True

    def reconcile_startup(self):
        """Leave pre-existing CPU custody explicitly interrupted after restart."""
        stamp = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        with Session(self.engine) as session, session.begin():
            rows = session.execute(
                select(models.Job, models.CpuExecution)
                .join(models.CpuExecution, models.CpuExecution.job_id == models.Job.id)
                .where(
                    models.Job.task == "post.audio",
                    models.Job.status.in_(["running", "interrupted"]),
                    models.CpuExecution.state.not_in(
                        ["finished", "failed", "cancelled"]
                    ),
                    models.CpuExecution.deleted_at.is_(None),
                )
            )
            count = 0
            for job, execution in rows:
                job.status = "interrupted"
                job.error_code = "CPU_CUSTODY_UNKNOWN"
                job.error = "El server se reiniciÃ³ con custodia CPU activa"
                job.updated_at = stamp
                execution.state = "interrupted"
                execution.cleanup_state = "unknown"
                execution.error_code = "CPU_CUSTODY_UNKNOWN"
                execution.revision += 1
                execution.updated_at = stamp
                count += 1
        try:
            self._clean_staging()
        except Exception:  # noqa: BLE001 -- la limpieza nunca aborta el arranque
            self.log.error("worker.cleanup.failed")
        return count

    @staticmethod
    def _link(path):
        """Symlink o junction de Windows: nunca se recorre ni se mueve (CWE-59)."""
        return path.is_symlink() or path.is_junction()

    def _inside_data(self, *paths):
        data = (self.root / "data").resolve()
        return all(p.resolve().is_relative_to(data) for p in paths)

    def _remove_empty_stage(self, plan, execution_id):
        """Quita ``takes/.pending-<exec>`` ya vacío tras publicar (``rmdir``, nunca rmtree)."""
        extra = {"song_id": plan.song_id}
        try:
            takes_dir = self.root / "data" / "songs" / plan.song_id / "takes"
            stage = takes_dir / f".pending-{execution_id}"
            if (
                self._link(takes_dir)
                or self._link(stage)
                or not stage.is_dir()
                or not self._inside_data(takes_dir, stage)
            ):
                return
            stage.rmdir()
            self.log.info("worker.staging.removed", extra=extra)
        except OSError:
            self.log.error("worker.cleanup.failed", extra=extra)

    def _clean_staging(self):
        """Limpieza de arranque (ADR-0089 §2); la fila SQLite manda.

        Se ejecuta tras el commit de la reconciliación. Nunca destruye lo único que
        permitiría recuperar: staging con intent ``prepared`` se conserva y un
        directorio final sin fila ``take`` se mueve a ``data/trash/orphans``.
        """
        data = self.root / "data"
        songs = data / "songs"
        if (
            self._link(data)
            or not songs.is_dir()
            or self._link(songs)
            or not self._inside_data(songs)
        ):
            return
        with self.engine.connect() as connection:
            executions = {
                row.id: row.state
                for row in connection.exec_driver_sql(
                    "SELECT id,state FROM cpu_execution"
                )
            }
            prepared = {
                row[0]
                for row in connection.exec_driver_sql(
                    "SELECT DISTINCT r.cpu_execution_id FROM publication_intent_revision r "
                    "JOIN publication_intent i ON i.id=r.intent_id "
                    "WHERE i.state='prepared'"
                )
            }
            takes = {
                row.id: row.status
                for row in connection.exec_driver_sql("SELECT id,status FROM take")
            }
        with self._guard:
            alive = set(self.owners)
        for song in sorted(songs.iterdir()):
            takes_dir = song / "takes"
            if (
                self._link(song)
                or not song.is_dir()
                or self._link(takes_dir)
                or not takes_dir.is_dir()
                or not self._inside_data(takes_dir)
            ):
                continue
            extra = {"song_id": song.name}
            for entry in sorted(takes_dir.iterdir()):
                if self._link(entry) or not entry.is_dir():
                    continue
                try:
                    if not self._inside_data(entry):
                        self.log.warning("worker.cleanup.failed", extra=extra)
                    elif entry.name.startswith(".pending-"):
                        self._clean_pending(entry, executions, prepared, alive, extra)
                    elif entry.name not in takes:
                        self._quarantine_orphan(entry, extra)
                    elif takes[entry.name] != "ready":
                        self.log.info("worker.take.not_ready", extra=extra)
                except OSError:
                    self.log.error("worker.cleanup.failed", extra=extra)

    def _clean_pending(self, entry, executions, prepared, alive, extra):
        execution_id = entry.name[len(".pending-") :]
        if execution_id in alive:
            return
        if execution_id in prepared:
            self.log.info("worker.staging.kept", extra=extra)
            return
        state = executions.get(execution_id)
        if state is None or state in {"finished", "failed", "cancelled", "interrupted"}:
            shutil.rmtree(entry)
            self.log.info("worker.staging.removed", extra=extra)

    def _quarantine_orphan(self, entry, extra):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        data = self.root / "data"
        trash, orphans = data / "trash", data / "trash" / "orphans"
        for folder in (trash, orphans):
            if self._link(folder):
                self.log.error("worker.cleanup.failed", extra=extra)
                return
            if not folder.exists():
                folder.mkdir()
        destination = orphans / f"{entry.name}-{stamp}"
        if not self._inside_data(entry, orphans, destination.parent):
            self.log.error("worker.cleanup.failed", extra=extra)
            return
        shutil.move(str(entry), str(destination))
        self.log.warning("worker.orphan.quarantined", extra=extra)

    def pending_cancellations(self):
        with Session(self.engine) as session:
            query = select(models.Job.id).where(
                models.Job.task == "post.audio",
                models.Job.lane == "cpu",
                models.Job.status.in_(["running", "interrupted"]),
                models.Job.cancel_requested_at.is_not(None),
                models.Job.deleted_at.is_(None),
            )
            if self.owner_id is not None:
                query = query.where(models.Job.owner_id == self.owner_id)
            return list(session.scalars(query))

    def execute_job(self, job_id, *, execution_id=None):
        """Claim, plan and execute one durable ``post.audio`` job."""
        execution_id = execution_id or models.new_id()
        if not self.claim_job(job_id):
            return None
        with self._guard:
            self.job_executions[job_id] = execution_id
        try:
            plan = self.plan_for_job(job_id, execution_id)
            return self.execute(plan, execution_id=execution_id)
        except BaseException as error:
            self.fail_plan(job_id, str(error) or "POST_PLAN_INVALID")
            raise
        finally:
            with self._guard:
                self.job_executions.pop(job_id, None)

    def _put_receipt(self, payload, digest):
        target = safe_path(self.root, f"data/private-contexts/{digest}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            write_once(target, payload)
        except FileExistsError:
            if (
                hasattr(os, "getuid") and target.stat().st_uid != os.getuid()
            ) or read_file(target, limit=MAX_PLAN_BYTES) != payload:
                raise ValueError("PROVENANCE_MISMATCH") from None

    def _cleanup_raw_outputs(self, plan):
        """Remove only accepted engine-attempt directories from this plan.

        The winning attempt identity is captured in the immutable authority
        chain.  Requiring each source to match that identity keeps cleanup
        confined to ``data/tmp/<attempt_id>`` and avoids deleting arbitrary
        paths supplied by an engine or a request.
        """
        directories = set()
        for entry in plan.takes:
            attempt_id = entry.authority.winning_attempt_id
            prefix = f"data/tmp/{attempt_id}/"
            if not entry.source.path.startswith(prefix):
                raise ValueError("UNSAFE_PATH")
            directories.add(safe_path(self.root, f"data/tmp/{attempt_id}"))
        for directory in directories:
            if directory.exists():
                shutil.rmtree(directory)

    def _prepare(self, plan, execution_id):
        plan = PostPlan.model_validate_json(plan.model_dump_json())
        raw = canonical_bytes(plan)
        if len(raw) > MAX_PLAN_BYTES:
            raise ValueError("PLAN_TOO_LARGE")
        if hashlib.sha256(raw).hexdigest() != canonical_sha256(plan):
            raise ValueError("PROVENANCE_MISMATCH")
        tool(self.ffmpeg, plan)
        with self.engine.connect() as connection:
            previous = (
                connection.execute(
                    select(models.CpuExecution.__table__).where(
                        models.CpuExecution.id == execution_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            winner = (
                connection.execute(
                    select(models.JobAttempt.__table__).where(
                        models.JobAttempt.id
                        == plan.takes[0].authority.winning_attempt_id
                    )
                )
                .mappings()
                .one()
            )
            context, context_seals = self.publisher.capture_context(connection, plan)
        prepared_context = prepare_context_once(context)
        context_raw, digest = prepared_context.payload, prepared_context.digest
        if len(raw) + len(context_raw) > MAX_PLAN_BYTES:
            raise ValueError("PLAN_TOO_LARGE")
        if previous is not None:
            if previous["plan_sha256"] != canonical_sha256(plan):
                raise ValueError("PROVENANCE_MISMATCH")
            if previous["cleanup_state"] != "confirmed":
                raise ValueError("CPU_CUSTODY_UNKNOWN")
            context, digest = self.publisher.receipt_from_history(
                plan, execution_id, context_raw
            )
            prepared_context = PreparedContext(
                value=context, payload=context_raw, digest=digest
            )
            self.publisher.contexts[execution_id] = context
            self.publisher.receipt_hashes[execution_id] = digest
            self.publisher.prepared_contexts[execution_id] = prepared_context
            self.publisher.context_seals[execution_id] = context_seals
            return previous, None
        self._put_receipt(context_raw, digest)
        self.publisher.contexts[execution_id] = context
        self.publisher.receipt_hashes[execution_id] = digest
        self.publisher.prepared_contexts[execution_id] = prepared_context
        self.publisher.context_seals[execution_id] = context_seals
        terminal = winner["terminal"].model_dump(mode="json")
        # Exact artifact provenance, not merely same hash/family/index.
        for entry in plan.takes:
            artifacts = [
                a
                for a in terminal["data"]["artifacts"]
                if a["output_index"] == entry.authority.output_index
            ]
            if len(artifacts) != 1 or (
                entry.source.path,
                entry.source.sha256,
                entry.source.media_type,
            ) != (
                "data/" + artifacts[0]["path"],
                artifacts[0]["sha256"],
                artifacts[0]["media_type"],
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            if not entry.source.path.startswith(
                f"data/tmp/{entry.authority.winning_attempt_id}/"
            ):
                raise ValueError("UNSAFE_PATH")
            expected_copy = f"data/tmp/_server_inputs/{execution_id}/{entry.authority.output_index}.wav"
            if entry.copied_source.path != expected_copy:
                raise ValueError("UNSAFE_PATH")
            source = safe_path(self.root, entry.source.path)
            copied = safe_path(self.root, expected_copy)
            payload = read_file(source)
            if (
                len(payload) != entry.source.bytes
                or hashlib.sha256(payload).hexdigest() != entry.source.sha256
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            copied.parent.mkdir(parents=True, exist_ok=True)
            write_once(copied, payload)
        run = safe_path(self.root, f"data/tmp/_server_cpu/{execution_id}")
        run.mkdir(parents=True, exist_ok=False)
        write_once(run / "post-plan.json", raw)
        epoch = secrets.token_hex(16)
        cpu = {
            "id": execution_id,
            "owner_id": plan.owner_id,
            "job_id": plan.post_job_id,
            "ordinal": 1,
            "state": "prepared",
            "revision": 1,
            "plan": plan,
            "plan_sha256": canonical_sha256(plan),
            "handler": "post.audio",
            "handler_version": 1,
            "contract_version": 1,
            "supervisor_epoch": epoch,
            "lease_token": secrets.token_hex(16),
            "process_identity": None,
            "cleanup_state": "unknown",
        }

        def reserve(connection):
            connection.execute(models.CpuExecution.__table__.insert().values(**cpu))
            stored = (
                connection.execute(
                    select(models.CpuExecution.__table__).where(
                        models.CpuExecution.id == execution_id
                    )
                )
                .mappings()
                .one()
            )
            validate_connection(connection, "cpu_execution", dict(stored))
            self.publisher.authority(connection, plan, execution_id)
            for entry in plan.takes:
                a = entry.authority
                identifier = models.new_id()
                revision_id = models.new_id()
                connection.execute(
                    models.PublicationIntent.__table__.insert().values(
                        id=identifier,
                        owner_id=plan.owner_id,
                        song_id=plan.song_id,
                        take_id=a.take_id,
                        output_index=a.output_index,
                        seed=a.seed,
                        state="reserved",
                        revision=1,
                    )
                )
                connection.execute(
                    models.PublicationIntentRevision.__table__.insert().values(
                        id=revision_id,
                        **a.model_dump(),
                        intent_id=identifier,
                        cpu_execution_id=execution_id,
                        source_sha256=entry.source.sha256,
                        stage_path=f"songs/{a.song_id}/takes/.pending-{execution_id}/{a.take_id}",
                        final_path=f"songs/{a.song_id}/takes/{a.take_id}",
                    )
                )
                cas(
                    connection,
                    "publication_intent",
                    identifier,
                    1,
                    "reserved",
                    active_revision_id=revision_id,
                )
            return dict(stored)

        stored = self.publisher.transaction(reserve)
        return stored, run

    def execute(self, plan, *, execution_id):
        # One local invocation owns this execution; SQLite CAS is still the
        # durable authority, and the shared coordinator governs every commit.
        with self._guard:
            if execution_id in self.owners:
                raise ValueError("CPU_EXECUTION_ACTIVE")
            cpu, run = self._prepare(plan, execution_id)
            if run is None:
                self.publisher.reconcile(plan, execution_id)
                return self._stored_results(plan, execution_id)
            group = LinuxGroup(
                "audio",
                run,
                execution_id,
                cpu["supervisor_epoch"],
                audio_root=self.root,
                plan_sha256=cpu["plan_sha256"],
                plan_bytes=len(canonical_bytes(plan)),
                context_sha256=self.publisher.receipt_hashes[execution_id],
                context_bytes=len(
                    self.publisher.prepared_contexts[execution_id].payload
                ),
            )
            owner = Owner(group, execution_id, cpu["supervisor_epoch"], 3600)
            self.owners[execution_id] = owner
        results = []
        try:

            def running(connection):
                self.publisher.authority(connection, plan, execution_id)
                return cas(
                    connection,
                    "cpu_execution",
                    execution_id,
                    cpu["revision"],
                    "running",
                    process_identity={
                        "leader": group.disposition["leader"],
                        "birth": group.disposition["birth"],
                    },
                )

            self.publisher.transaction(running)
            owner.start()
            seen = set()
            while not owner.done.is_set() or not owner.messages.empty():
                try:
                    message = owner.receive(0.1)
                except Empty:
                    continue
                if message["kind"] == "take_result":
                    result = TypeAdapter(PerTakeResult).validate_python(
                        message["payload"]
                    )
                    plan.validate_result(result)
                    if result.take_id in seen:
                        raise ValueError("PROVENANCE_MISMATCH")
                    seen.add(result.take_id)
                    entry = next(
                        e for e in plan.takes if e.authority.take_id == result.take_id
                    )
                    if isinstance(result, TakeSuccess):
                        self.publisher.publish(plan, execution_id, entry, result)
                    else:
                        self.publisher.fail(plan, execution_id, entry, result.code)
                    results.append(result)
            receipt = owner.join(20)
            if not receipt.release_gate or len(results) != len(plan.takes):
                raise ValueError("CPU_CUSTODY_UNKNOWN")

            def complete(connection):
                current = self.publisher.authority(connection, plan, execution_id)
                draining = cas(
                    connection,
                    "cpu_execution",
                    execution_id,
                    current["revision"],
                    "draining",
                    cleanup_state="confirmed",
                )
                self.publisher._complete_post(connection, plan, results)
                ready = [r.take_id for r in results if isinstance(r, TakeSuccess)]
                failed = [r.take_id for r in results if not isinstance(r, TakeSuccess)]
                kind = (
                    "mixed"
                    if ready and failed
                    else "all_ready"
                    if ready
                    else "all_failed"
                )
                return cas(
                    connection,
                    "cpu_execution",
                    execution_id,
                    draining,
                    "finished",
                    outcome={
                        "kind": kind,
                        "ready_take_ids": ready,
                        "failed_take_ids": failed,
                    },
                    finished_at=models.utc_now(),
                )

            self.publisher.transaction(complete)
            self._cleanup_raw_outputs(plan)
            self._remove_empty_stage(plan, execution_id)
            return tuple(results)
        except BaseException as primary:
            owner.cancel()
            if owner.finalizer.ident is not None:
                owner.join(20)
            else:
                group.contain_unknown()
            if owner.receipt is not None and owner.receipt.release_gate:
                try:

                    def interrupted(connection):
                        current = (
                            connection.execute(
                                select(models.CpuExecution.__table__).where(
                                    models.CpuExecution.id == execution_id
                                )
                            )
                            .mappings()
                            .one()
                        )
                        if (
                            current["state"] == "running"
                            and current["lease_token"] == cpu["lease_token"]
                            and current["supervisor_epoch"] == cpu["supervisor_epoch"]
                        ):
                            cas(
                                connection,
                                "cpu_execution",
                                execution_id,
                                current["revision"],
                                "interrupted",
                                cleanup_state="confirmed",
                            )

                    self.publisher.transaction(interrupted)
                except Exception:  # noqa: BLE001 -- preservar error primario y estado incierto.
                    primary.add_note("CPU custody metadata update failed")
            raise
        finally:
            if owner.receipt is not None and owner.receipt.release_gate:
                with self._guard:
                    self.owners.pop(execution_id, None)

    def _stored_results(self, plan, execution_id):
        results = []
        for entry in plan.takes:
            with self.engine.connect() as connection:
                intent = self.publisher.intent(connection, entry)
                revision = (
                    connection.execute(
                        select(models.PublicationIntentRevision.__table__).where(
                            models.PublicationIntentRevision.id
                            == intent["active_revision_id"]
                        )
                    )
                    .mappings()
                    .one()
                )
            if intent["state"] == "committed":
                final = (
                    self.root
                    / f"data/songs/{plan.song_id}/takes/{entry.authority.take_id}"
                )
                manifest = json.loads(
                    read_file(final / "manifest.json", limit=MAX_PLAN_BYTES)
                )
                results.append(
                    TakeSuccess(
                        status="success",
                        take_id=entry.authority.take_id,
                        output_index=entry.authority.output_index,
                        package=revision["package"],
                        duration_s=entry.source.duration_s,
                        integrated_lufs=manifest["post"]["lufs_out"],
                        true_peak_dbtp=manifest["post"]["true_peak_dbtp"],
                    )
                )
            elif intent["state"] in {"failed", "cancelled"}:
                code = intent["error_code"] or revision["error_code"]
                if code is None:
                    raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY")
                try:
                    results.append(
                        TakeFailure(
                            status="failure",
                            take_id=entry.authority.take_id,
                            output_index=entry.authority.output_index,
                            code=code,
                        )
                    )
                except ValueError:
                    raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY") from None
        return tuple(results)

    def cancel(self, execution_id):
        with self._guard:
            owner = self.owners.get(execution_id)
        if owner is not None:
            owner.cancel()

    def cancel_job(self, job_id):
        with self._guard:
            execution_id = self.job_executions.get(job_id)
        if execution_id is None:
            return False
        self.cancel(execution_id)
        return True
