"""Intención durable por toma; rename no-clobber y commit son fases separadas."""

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path

from audio_post.manifest import safe_path
from audio_post.private_context import PreparedContext, prepare_context
from sqlalchemy import select

from app import models, snapshots
from app.migrations.cpu_publication_invariants import cas, validate_connection
from app.migrations.job_attempt_invariants import validate_contract
from app.publication import CommitPublication

from .contracts import PreparedPackage, TakeFailure, canonical_sha256
from .packages import (
    FILES,
    canonical_bytes,
    fsync_directory,
    identity,
    read_file,
    stage,
    verify_package,
    write_once,
)

_FALLBACK_ERRNOS = {errno.EINVAL, errno.ENOSYS}


def _native_noreplace(source, destination):
    """``renameat2(RENAME_NOREPLACE)``; ``OSError(ENOSYS)`` si la plataforma no lo ofrece."""
    try:
        rename = ctypes.CDLL(None, use_errno=True).renameat2
    except (AttributeError, OSError, TypeError):
        raise OSError(errno.ENOSYS, os.strerror(errno.ENOSYS)) from None
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def rename_noreplace(source, destination):
    """Publica sin pisar: ``renameat2`` y, si el FS no lo soporta, ausencia + rename.

    El destino es único por construcción (``takes/<take_ulid>``) y la fila SQLite
    es la autoridad, así que el fallback sin atomicidad no abre una carrera real.
    """
    if source.parent.stat().st_dev != destination.parent.stat().st_dev:
        raise ValueError("UNSAFE_PATH")
    try:
        _native_noreplace(source, destination)
    except OSError as error:
        if error.errno not in _FALLBACK_ERRNOS:
            raise
        if os.path.lexists(destination):
            raise FileExistsError(
                errno.EEXIST, os.strerror(errno.EEXIST), str(destination)
            ) from None
        os.rename(source, destination)
    for directory in (source.parent, destination.parent):
        try:
            fsync_directory(directory)
        except PermissionError:
            if os.name != "nt":  # Windows no abre directorios para fsync
                raise


class Publisher:
    def __init__(self, engine, root, coordinator, bus):
        self.engine, self.root, self.coordinator, self.bus = (
            engine,
            Path(root),
            coordinator,
            bus,
        )
        self.contexts = {}
        self.context_seals = {}
        self.receipt_hashes = {}
        self.prepared_contexts: dict[str, PreparedContext] = {}

    def _context_rows(self, connection, plan):
        ids = tuple(entry.authority.take_id for entry in plan.takes)
        placeholders = ",".join("?" for _ in ids)
        request = connection.exec_driver_sql(
            "SELECT engine_request FROM job_attempt WHERE id=?",
            (plan.takes[0].authority.winning_attempt_id,),
        ).scalar_one()
        generation = tuple(
            connection.exec_driver_sql(
                "SELECT owner_id,song_id,task,request,deleted_at FROM job WHERE id=?",
                (plan.generation_job_id,),
            ).one()
        )
        takes = [
            tuple(row)
            for row in connection.exec_driver_sql(
                "SELECT id,owner_id,song_id,root_id,derivation,params,model_id,model_version,commercial_use,deleted_at,variant_index,seed,task,job_id,lyrics_version_id "
                f"FROM take WHERE id IN ({placeholders}) ORDER BY id",
                ids,
            )
        ]
        edges = [
            tuple(row)
            for row in connection.exec_driver_sql(
                "SELECT id,owner_id,child_id,parent_type,parent_id,role,section_map,deleted_at "
                f"FROM lineage_edge WHERE child_type='take' AND child_id IN ({placeholders}) ORDER BY id",
                ids,
            )
        ]
        lyric_ids = tuple(sorted({row[-1] for row in takes if row[-1] is not None}))
        lyrics = (
            [
                tuple(row)
                for row in connection.exec_driver_sql(
                    "SELECT id,owner_id,song_id,text,sha256,declaration,deleted_at FROM lyrics_version WHERE id IN ("
                    + ",".join("?" for _ in lyric_ids)
                    + ") ORDER BY id",
                    lyric_ids,
                )
            ]
            if lyric_ids
            else []
        )
        return {
            "request": request,
            "generation": generation,
            "takes": takes,
            "edges": edges,
            "lyrics": lyrics,
        }

    def capture_context(self, connection, plan):
        seals = self._context_rows(connection, plan)
        takes, edges = seals["takes"], seals["edges"]
        if len(takes) != len(plan.takes):
            raise ValueError("PROVENANCE_MISMATCH")
        request = validate_contract(json.loads(seals["request"]), "request").model_dump(
            mode="json"
        )
        generation = seals["generation"]
        if (
            generation[:3] != (plan.owner_id, plan.song_id, request["task"])
            or generation[4] is not None
        ):
            raise ValueError("PROVENANCE_MISMATCH")
        logical = json.loads(generation[3])
        lyrics = {row[0]: row for row in seals["lyrics"]}
        expected = {entry.authority.take_id: entry.authority for entry in plan.takes}
        context = {
            "version": 1,
            "winning_request_sha256": hashlib.sha256(
                canonical_bytes(request)
            ).hexdigest(),
            "captured_request": request,
            "song_id": plan.song_id,
            "takes": {},
        }
        for take in takes:
            (
                identifier,
                owner,
                song,
                root_id,
                derivation,
                take_params,
                model_id,
                model_version,
                commercial,
                deleted,
                output_index,
                seed,
                task,
                job_id,
                lyrics_id,
            ) = take
            if owner != plan.owner_id or song != plan.song_id or deleted is not None:
                raise ValueError("PROVENANCE_MISMATCH")
            authority = expected[identifier]
            if (
                output_index != authority.output_index
                or int(seed) != authority.seed
                or request["seed"] + output_index != authority.seed
                or task != request["task"]
                or job_id != plan.generation_job_id
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            proof = None
            if task == "music.song":
                lyric = lyrics.get(lyrics_id)
                if (
                    lyric is None
                    or lyric[1:3] != (owner, song)
                    or lyric[6] is not None
                    or lyric[5] not in {"own", "assistant", "public_domain", "licensed"}
                ):
                    raise ValueError("PROVENANCE_MISSING")
                if (
                    logical.get("params", {}).get("lyrics") != lyric[3]
                    or request["params"].get("lyrics") != lyric[3]
                    or hashlib.sha256(lyric[3].encode("utf-8")).hexdigest() != lyric[4]
                ):
                    raise ValueError("PROVENANCE_MISMATCH")
                proof = {
                    "lyrics_version_id": lyric[0],
                    "sha256": lyric[4],
                    "declaration": lyric[5],
                }
            elif (
                lyrics_id is not None
                or logical.get("params", {}).get("lyrics")
                or request["params"].get("lyrics")
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            parents = []
            sections = []
            for edge in edges:
                (
                    _,
                    edge_owner,
                    child_id,
                    parent_type,
                    parent_id,
                    role,
                    section,
                    edge_deleted,
                ) = edge
                if child_id == identifier and edge_deleted is None:
                    if edge_owner != plan.owner_id:
                        raise ValueError("PROVENANCE_MISMATCH")
                    parents.append({"type": parent_type, "id": parent_id, "role": role})
                    sections.append(
                        json.loads(section) if section is not None else None
                    )
            if sections and any(section != sections[0] for section in sections):
                raise ValueError("LINEAGE_CONTEXT_UNREPRESENTABLE")
            context["takes"][identifier] = {
                "output_index": output_index,
                "root_id": root_id,
                "params": json.loads(take_params),
                "model_id": model_id,
                "model_version": model_version,
                "commercial_use": bool(commercial),
                "lyrics": proof,
                "lineage": {
                    "parents": parents,
                    "derivation": derivation,
                    "section_map": sections[0] if sections else None,
                },
            }
        return context, seals

    def revalidate_context(self, connection, plan, execution_id):
        # Raw SQL comparisons only: no context encoding/hash or file reads.
        if self._context_rows(connection, plan) != self.context_seals[execution_id]:
            raise ValueError("PROVENANCE_MISMATCH")

    def receipt_from_history(self, plan, execution_id, current_bytes, entries=None):
        """The old manifest SHA in SQL chooses the receipt, never fresh SQL.

        ``entries`` acota la historia a las takes ya empaquetadas (reanudación).
        """
        accepted = None
        for entry in plan.takes if entries is None else entries:
            with self.engine.connect() as connection:
                intent = self.intent(connection, entry)
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
            package = revision["package"]
            if package is None:
                # A replay may reuse a historical failure, but an in-flight
                # intent without its immutable package is only a partial
                # execution.  Returning a sibling's receipt here would let
                # ``reconcile`` skip this take and make ``_stored_results``
                # report a false success.
                if intent["state"] in {"reserved", "prepared", "renamed"}:
                    raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY")
                continue
            if (
                package.authority != entry.authority
                or canonical_sha256(package) != revision["package_sha256"]
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            pending = stage(self.root, execution_id, entry)
            final = safe_path(
                self.root, f"data/songs/{plan.song_id}/takes/{entry.authority.take_id}"
            )
            directory = (
                pending
                if pending.exists() and intent["state"] != "committed"
                else final
            )
            payload = read_file(directory / "manifest.json", limit=16777216)
            if (
                len(payload) != package.manifest.bytes
                or hashlib.sha256(payload).hexdigest() != package.manifest.sha256
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            reference = json.loads(payload).get("private_context")
            if type(reference) is not dict or set(reference) != {"sha256"}:
                raise ValueError("PROVENANCE_MISMATCH")
            digest = reference["sha256"]
            if (
                type(digest) is not str
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            receipt_bytes = read_file(
                safe_path(self.root, f"data/private-contexts/{digest}.json"),
                limit=16777216,
            )
            value = json.loads(receipt_bytes)
            canonical, actual = prepare_context(value)
            if (
                canonical != receipt_bytes
                or actual != digest
                or receipt_bytes != current_bytes
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            if accepted is not None and accepted[1] != digest:
                raise ValueError("PROVENANCE_MISMATCH")
            accepted = value, digest
        if accepted is None:
            raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY")
        return accepted

    def transaction(self, callback):
        def commit():
            with self.engine.begin() as connection:
                value = callback(connection)
            # State changed durably: clients must reconcile until allwriters
            # composition assigns the actual application event builder.
            return CommitPublication(value=value, publications=(), invalidate=True)

        return self.coordinator.commit_and_publish(commit, self.bus).value

    def _complete_post(self, connection, plan, results):
        """Close ``post.audio`` and durably reject beats for failed takes.

        The CPU worker owns the post job, while the queue admission loop owns
        dispatch.  Finishing here makes the dependency edge visible to the
        next admission pass without allowing a failed take to leave its beat
        job blocked forever.
        """
        post = (
            connection.execute(
                select(models.Job.__table__).where(models.Job.id == plan.post_job_id)
            )
            .mappings()
            .one()
        )
        if post["status"] not in {"running", "interrupted", "succeeded"}:
            raise ValueError("PROVENANCE_MISMATCH")
        failed = {
            result.take_id for result in results if isinstance(result, TakeFailure)
        }
        if post["status"] != "succeeded":
            connection.execute(
                models.Job.__table__.update()
                .where(models.Job.id == plan.post_job_id)
                .values(
                    status="succeeded",
                    stage="published",
                    finished_at=models.utc_now(),
                    error_code=None,
                    error=None,
                )
            )
        if not failed:
            return
        dependents = connection.execute(
            select(models.Job.__table__)
            .join(
                models.JobDependency.__table__,
                models.JobDependency.job_id == models.Job.id,
            )
            .where(
                models.JobDependency.depends_on_job_id == plan.post_job_id,
                models.JobDependency.deleted_at.is_(None),
                models.Job.task == "audio.beats",
                models.Job.deleted_at.is_(None),
            )
        ).mappings()
        for beat in dependents:
            inputs = beat["request"].get("inputs", [])
            take_id = next(
                (
                    item.get("ref", {}).get("id")
                    for item in inputs
                    if item.get("ref", {}).get("type") == "take"
                ),
                None,
            )
            if take_id in failed and beat["status"] in {"blocked", "queued"}:
                connection.execute(
                    models.Job.__table__.update()
                    .where(models.Job.id == beat["id"])
                    .values(
                        status="failed",
                        error_code="DEPENDENCY_FAILED",
                        error="La toma no está disponible para el análisis",
                        finished_at=models.utc_now(),
                    )
                )

    def authority(self, connection, plan, execution_id, *, allow_cancel=False):
        self.revalidate_context(connection, plan, execution_id)
        cpu = (
            connection.execute(
                select(models.CpuExecution.__table__).where(
                    models.CpuExecution.id == execution_id
                )
            )
            .mappings()
            .one()
        )
        if cpu["plan_sha256"] != canonical_sha256(plan):
            raise ValueError("PROVENANCE_MISMATCH")
        validate_connection(connection, "cpu_execution", dict(cpu))
        post = (
            connection.execute(
                select(models.Job.__table__).where(models.Job.id == plan.post_job_id)
            )
            .mappings()
            .one()
        )
        gen = (
            connection.execute(
                select(models.Job.__table__).where(
                    models.Job.id == plan.generation_job_id
                )
            )
            .mappings()
            .one()
        )
        if post["deleted_at"] is not None or (
            post["cancel_requested_at"] is not None and not allow_cancel
        ):
            raise ValueError("CANCELLED")
        if (
            gen["status"] != "succeeded"
            or gen["attempt"] != plan.takes[0].authority.winning_ordinal
        ):
            raise ValueError("PROVENANCE_MISMATCH")
        song = (
            connection.execute(
                select(models.Song.__table__).where(models.Song.id == plan.song_id)
            )
            .mappings()
            .one()
        )
        if song["deleted_at"] is not None or song["owner_id"] != plan.owner_id:
            raise ValueError("PROVENANCE_MISMATCH")
        return cpu

    def intent(self, connection, entry):
        return (
            connection.execute(
                select(models.PublicationIntent.__table__).where(
                    models.PublicationIntent.take_id == entry.authority.take_id
                )
            )
            .mappings()
            .one()
        )

    def publish(self, plan, execution_id, entry, result):
        context = self.contexts[execution_id]
        prepared_context = self.prepared_contexts.get(execution_id)
        directory = stage(self.root, execution_id, entry)
        final = (
            self.root
            / f"data/songs/{entry.authority.song_id}/takes/{entry.authority.take_id}"
        )
        with self.engine.connect() as connection:
            intent = self.intent(connection, entry)
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
            verify_package(
                plan,
                entry,
                revision["package"],
                final,
                context,
                data_root=self.root / "data",
                prepared_context=prepared_context,
            )
            with self.coordinator.barrier(), self.engine.connect() as connection:
                self.authority(connection, plan, execution_id, allow_cancel=True)
            snapshots.publish(self.engine, plan.song_id, self.root / "data")
            return "committed"
        package = result.package if result is not None else revision["package"]
        if not isinstance(package, PreparedPackage):
            raise TypeError("PROVENANCE_MISMATCH")
        package_sha = canonical_sha256(package)
        run = self.root / f"data/tmp/_server_cpu/{execution_id}"
        receipt_path = run / f"publication-{intent['id']}.json"
        if intent["state"] == "reserved":
            verified = verify_package(
                plan,
                entry,
                package,
                directory,
                context,
                data_root=self.root / "data",
                prepared_context=prepared_context,
            )
            if {p.name for p in directory.iterdir()} != {f[1] for f in FILES}:
                raise ValueError("UNSAFE_PATH")
            info = directory.lstat()
            marker = {
                "execution_id": execution_id,
                "intent_id": intent["id"],
                "revision_id": revision["id"],
                "package_sha256": package_sha,
                "directory": [info.st_dev, info.st_ino, info.st_mode, info.st_uid],
            }
            write_once(receipt_path, canonical_bytes(marker))

            def prepare(connection):
                self.authority(connection, plan, execution_id)
                current = self.intent(connection, entry)
                if current["active_revision_id"] != revision["id"]:
                    raise ValueError("PROVENANCE_MISMATCH")
                for basename, metadata in verified.items():
                    if identity(directory / basename) != metadata:
                        raise ValueError("PROVENANCE_MISMATCH")
                connection.execute(
                    models.PublicationIntentRevision.__table__.update()
                    .where(
                        models.PublicationIntentRevision.id == revision["id"],
                        models.PublicationIntentRevision.package.is_(None),
                    )
                    .values(package=package, package_sha256=package_sha)
                )
                return cas(
                    connection,
                    "publication_intent",
                    current["id"],
                    intent["revision"],
                    "prepared",
                )

            prepared_revision = self.transaction(prepare)
        else:
            if revision["package_sha256"] != package_sha:
                raise ValueError("PROVENANCE_MISMATCH")
            prepared_revision = intent["revision"]
        marker = json.loads(read_file(receipt_path, limit=65536))
        if (
            marker["execution_id"],
            marker["intent_id"],
            marker["revision_id"],
            marker["package_sha256"],
        ) != (execution_id, intent["id"], revision["id"], package_sha):
            raise ValueError("PROVENANCE_MISMATCH")
        if directory.exists():
            verify_package(
                plan,
                entry,
                package,
                directory,
                context,
                data_root=self.root / "data",
                prepared_context=prepared_context,
            )
            rename_noreplace(directory, final)
        info = final.lstat()
        if [info.st_dev, info.st_ino, info.st_mode, info.st_uid] != marker["directory"]:
            raise ValueError("PROVENANCE_MISMATCH")
        verified = verify_package(
            plan,
            entry,
            package,
            final,
            context,
            data_root=self.root / "data",
            prepared_context=prepared_context,
        )
        manifest = json.loads(read_file(final / "manifest.json", limit=16777216))
        master_meta = next(
            o["meta"] for o in manifest["outputs"] if o["role"] == "master"
        )

        def commit(connection):
            self.authority(connection, plan, execution_id)
            current = self.intent(connection, entry)
            if current["active_revision_id"] != revision["id"]:
                raise ValueError("PROVENANCE_MISMATCH")
            for basename, metadata in verified.items():
                if identity(final / basename) != metadata:
                    raise ValueError("PROVENANCE_MISMATCH")
            number = current["revision"]
            if current["state"] == "prepared":
                number = cas(
                    connection,
                    "publication_intent",
                    current["id"],
                    prepared_revision,
                    "renamed",
                )
            elif current["state"] != "renamed":
                raise ValueError("PROVENANCE_MISMATCH")
            for role, _, _ in FILES:
                reference = getattr(package, role)
                connection.execute(
                    models.Asset.__table__.insert().values(
                        id=models.new_id(),
                        owner_id=plan.owner_id,
                        subject_type="take",
                        subject_id=entry.authority.take_id,
                        role=role,
                        path=reference.path[5:],
                        media_type=reference.media_type,
                        sha256=reference.sha256,
                        bytes=reference.bytes,
                        meta={},
                    )
                )
            # Audio/manifest bytes already validated outside; no file IO here.
            connection.execute(
                models.Take.__table__.update()
                .where(models.Take.id == entry.authority.take_id)
                .values(
                    status="ready",
                    error_code=None,
                    duration_s=entry.source.duration_s,
                    sample_rate=master_meta["sample_rate"],
                )
            )
            cas(
                connection,
                "publication_intent",
                current["id"],
                number,
                "committed",
                committed_at=models.utc_now(),
            )
            return "committed"

        outcome = self.transaction(commit)
        snapshots.publish(self.engine, plan.song_id, self.root / "data")
        return outcome

    def fail(self, plan, execution_id, entry, code):
        def failure(connection):
            self.authority(
                connection, plan, execution_id, allow_cancel=code == "CANCELLED"
            )
            current = self.intent(connection, entry)
            if current["state"] == "committed":
                return
            if current["state"] == "renamed":
                cas(
                    connection,
                    "publication_intent",
                    current["id"],
                    current["revision"],
                    "quarantined",
                    error_code=code,
                )
                return
            target = "cancelled" if code == "CANCELLED" else "failed"
            connection.execute(
                models.PublicationIntentRevision.__table__.update()
                .where(
                    models.PublicationIntentRevision.id
                    == current["active_revision_id"],
                    models.PublicationIntentRevision.error_code.is_(None),
                )
                .values(error_code=code)
            )
            connection.execute(
                models.Take.__table__.update()
                .where(models.Take.id == entry.authority.take_id)
                .values(status=target, error_code=code)
            )
            cas(
                connection,
                "publication_intent",
                current["id"],
                current["revision"],
                target,
                error_code=code,
            )

        self.transaction(failure)
        snapshots.publish(self.engine, plan.song_id, self.root / "data")

    def reconcile(self, plan, execution_id):
        outcomes = []
        for entry in plan.takes:
            with self.engine.connect() as connection:
                current = self.intent(connection, entry)
            if current["state"] in {"prepared", "renamed", "committed"}:
                outcomes.append(self.publish(plan, execution_id, entry, None))
        return outcomes
