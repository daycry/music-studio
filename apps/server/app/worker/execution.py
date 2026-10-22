"""Padre local de post.audio; custodia retenida hasta join real."""

import hashlib
import json
import logging
import os
import re
import secrets
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty

from audio_post.manifest import safe_path
from audio_post.private_context import PreparedContext, prepare_context_once
from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, snapshots
from app.migrations.cpu_publication_invariants import cas, validate_connection
from app.queue.cleanup import remove_data_dir, sweep_cancelled

from .contracts import (
    PerTakeResult,
    PostPlan,
    TakeFailure,
    TakeSuccess,
    canonical_sha256,
)
from .custody import Owner
from .custody_linux import LINUX_GROUPS, LinuxGroup
from .packages import (
    MAX_PLAN_BYTES,
    canonical_bytes,
    read_file,
    stage,
    tool,
    write_once,
)
from .planning import compose_post_plan, load_tool_pin
from .publications import Publisher


def _probe_birth(pid):
    """Instante de nacimiento (``starttime``) de ``pid`` o ``None`` si ya no existe.

    Solo Linux (``/proc``): sin él no hay forma honesta de probar una muerte y
    se lanza ``OSError`` (el llamador no confirma nada).
    """
    if not Path("/proc/self/stat").exists():
        raise OSError("PROC_UNAVAILABLE")
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return None
    fields = text.rsplit(")", 1)[1].split()
    if fields[0] in {"Z", "X"}:
        return None  # terminado aunque nadie lo haya recogido aún
    return int(fields[19])


def _probe_group(leader):
    """``True`` si queda algún proceso vivo en el grupo/sesión de ``leader``.

    Un líder zombi o ausente no prueba que el grupo haya muerto: sus hijos pueden
    seguir escribiendo. Sin ``/proc`` no se puede saber y se lanza ``OSError``.
    """
    proc = Path("/proc")
    if not (proc / "self" / "stat").exists():
        raise OSError("PROC_UNAVAILABLE")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue  # terminó mientras se recorría
        if fields[0] in {"Z", "X"}:
            continue
        if leader in (int(fields[2]), int(fields[3])):
            return True
    return False


def _probe_execution(execution_id, proc=Path("/proc")):
    """``True`` si algún proceso vivo pertenece a la ejecución ``execution_id``.

    El supervisor y el hijo se lanzan con el id de ejecución en su ``argv``
    (``custody_linux``), y FFmpeg con rutas ``.pending-<exec>``: siempre aparece
    en ``/proc/*/cmdline``. Prueba de muerte sin pid para la marca ``launching``.
    Sin ``/proc`` no se puede saber y se lanza ``OSError``.
    """
    proc = Path(proc)
    if not (proc / "self" / "stat").exists():
        raise OSError("PROC_UNAVAILABLE")
    needle = execution_id.encode()
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] in {"Z", "X"}:
                continue
            if needle in (entry / "cmdline").read_bytes():
                return True
        except (FileNotFoundError, ProcessLookupError, IndexError):
            continue  # terminó mientras se recorría
    return False


_ULID = re.compile(r"[0-9A-Z]{26}")
_LAUNCHING = {"launching": True}


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
        self._birth_probe = _probe_birth
        self._group_probe = _probe_group
        self._execution_probe = _probe_execution
        self._resumed = set()
        self._skipped = {}
        self._owner_jobs = {}
        self._backoff = {}
        self.backoff_s = 5.0

    def _live_jobs(self):
        """Jobs con ejecución viva o custodia retenida en este proceso."""
        with self._guard:
            return set(self.job_executions) | set(self._owner_jobs.values())

    def _backed_off(self, key):
        with self._guard:
            return self._backoff.get(key, 0.0) > time.monotonic()

    def _back_off(self, key):
        with self._guard:
            now = time.monotonic()
            for stale in [k for k, until in self._backoff.items() if until <= now]:
                del self._backoff[stale]
            self._backoff[key] = now + self.backoff_s

    def _occupied_slots(self, executor, live=None):
        """Slots CPU ocupados: todo owner vivo o retenido más los ``running`` de SQL.

        ``live`` es un snapshot de ``_live_jobs()`` tomado FUERA de la barrera del
        coordinador (orden único: ``_guard`` antes que la barrera). Un owner vivo
        ocupa slot aunque su fila esté borrada o cambiase de estado; un
        ``interrupted`` sin dueño (reinicio), un borrado o el de otro owner, no.
        """
        if live is None:
            live = self._live_jobs()
        mine = (
            models.Job.owner_id == self.owner_id
            if self.owner_id is not None
            else models.Job.owner_id.is_not(None)
        )
        sql = executor.scalar(
            select(func.count())
            .select_from(models.Job)
            .where(
                models.Job.lane == "cpu",
                models.Job.deleted_at.is_(None),
                mine,
                models.Job.status == "running",
                models.Job.id.not_in(live),
            )
        )
        return sql + len(live)

    def claim_job(self, job_id):
        """Atomically acquire one of the two server CPU slots for post.audio."""
        stamp = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        with Session(self.engine) as session, session.begin():
            job = session.get(models.Job, job_id)
            active = self._occupied_slots(session)
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
            self._requeue_orphans(session, stamp)
            session.flush()
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
                if execution.state == "interrupted" and job.status == "interrupted":
                    continue  # ya reconciliado: un segundo arranque no reescribe nada
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
            self._clean_orphan_inputs()
        except Exception:  # noqa: BLE001 -- la limpieza nunca aborta el arranque
            self.log.error("worker.cleanup.failed")
        return count

    def _requeue_orphans(self, session, stamp):
        """Posts ``running``/``interrupted`` sin ninguna ``cpu_execution`` (I1).

        Murieron tras ``claim_job`` y antes de reservar su ejecución: no hay
        proceso ni staging propio que proteger, así que vuelven a ``queued``.
        """
        has_execution = (
            select(models.CpuExecution.id)
            .where(models.CpuExecution.job_id == models.Job.id)
            .exists()
        )
        live = self._live_jobs()
        for job in session.scalars(
            select(models.Job).where(
                models.Job.task == "post.audio",
                models.Job.lane == "cpu",
                models.Job.status.in_(["running", "interrupted"]),
                models.Job.deleted_at.is_(None),
                self._owner_filter(),
                ~has_execution,
                models.Job.id.not_in(live),
            )
        ):
            job.status = "queued"
            job.attempt = 0
            job.started_at = None
            job.error_code = None
            job.error = None
            job.updated_at = stamp

    def _clean_orphan_inputs(self):
        """Copias parciales de ``_prepare`` sin ``cpu_execution`` (nombre ULID).

        Las entradas de engine usan ``uuid4().hex`` y nunca casan con un ULID.
        """
        for folder in ("_server_inputs", "_server_cpu"):
            self._clean_orphan_folder(folder)

    def _clean_orphan_folder(self, folder):
        base = self.root / "data" / "tmp" / folder
        if not base.is_dir() or self._link(base):
            return
        with self.engine.connect() as connection:
            known = {
                row[0]
                for row in connection.exec_driver_sql("SELECT id FROM cpu_execution")
            }
        with self._guard:
            alive = set(self.owners) | set(self.job_executions.values())
        for entry in sorted(base.iterdir()):
            if _ULID.fullmatch(entry.name) and entry.name not in known | alive:
                remove_data_dir(
                    self.root / "data",
                    "tmp",
                    folder,
                    entry.name,
                    log=self.log,
                )

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

    def _process_dead(self, identity, execution_id=None):
        """Prueba de muerte del proceso anterior a partir de su identidad durable.

        ``None``: nunca llegó a lanzarse un workload con ese lease. Con identidad
        ``{leader, birth}`` se compara el ``starttime`` actual de ese pid: ausente
        o distinto (pid reutilizado tras reiniciar el contenedor) prueba la
        muerte. Cualquier otra cosa (identidad ilegible, sin ``/proc``) no prueba
        nada y la custodia sigue ``unknown``.
        """
        if identity is None:
            return True
        if not isinstance(identity, dict):
            return False
        if identity == _LAUNCHING:
            # Marca previa al lanzamiento: no hay pid. Sin id de ejecución o sin
            # /proc no se prueba nada; si no queda ningún proceso de la ejecución,
            # nunca llegó a lanzarse o ya murió.
            if execution_id is None:
                return False
            try:
                return not self._execution_probe(execution_id)
            except (OSError, ValueError):
                return False
        leader, birth = identity.get("leader"), identity.get("birth")
        if type(leader) is not int or type(birth) is not int or leader <= 0:
            return False
        try:
            current = self._birth_probe(leader)
            if current is not None and current == birth:
                return False  # el líder sigue vivo
            # Líder ausente, zombi o pid reutilizado: aún hay que ver su grupo.
            return not self._group_probe(leader)
        except (OSError, ValueError, IndexError):
            return False

    def _owner_filter(self):
        if self.owner_id is not None:
            return models.Job.owner_id == self.owner_id
        return models.Job.owner_id.is_not(None)

    def resumable_jobs(self):
        """Posts ``interrupted`` cuyo proceso anterior se prueba muerto (CA-1)."""
        with Session(self.engine) as session:
            rows = list(
                session.execute(
                    select(
                        models.Job.id,
                        models.CpuExecution.id,
                        models.CpuExecution.process_identity,
                    )
                    .join(
                        models.CpuExecution,
                        models.CpuExecution.job_id == models.Job.id,
                    )
                    .where(
                        models.Job.task == "post.audio",
                        models.Job.lane == "cpu",
                        models.Job.status == "interrupted",
                        models.Job.cancel_requested_at.is_(None),
                        models.Job.deleted_at.is_(None),
                        self._owner_filter(),
                        models.CpuExecution.state == "interrupted",
                        models.CpuExecution.deleted_at.is_(None),
                    )
                    .order_by(models.Job.created_at, models.Job.id)
                )
            )
        with self._guard:
            alive, tried = set(self.owners), set(self._resumed)
        ready = []
        for job_id, execution_id, identity in rows:
            key = ("probe", execution_id)
            if execution_id in alive or job_id in tried or self._backed_off(key):
                continue
            if self._process_dead(identity, execution_id):
                ready.append(job_id)
            else:
                self._back_off(key)  # no se recorre /proc en cada tick
        return ready

    def claim_resume(self, job_id):
        """``interrupted → running`` sobre la misma ``cpu_execution`` (opción A).

        Con la muerte del proceso anterior probada, la custodia pasa de
        ``unknown`` a ``confirmed`` y la ejecución de ``interrupted`` a
        ``prepared`` con un lease y un epoch nuevos, que son las únicas
        transiciones que ya admiten los triggers. Devuelve el id de la
        ejecución a reanudar o ``None`` si no procede.

        Orden único de locks: todo lo que necesita ``_guard`` (snapshots de
        owners y ocupación) y todas las lecturas baratas ocurren ANTES de entrar
        en la barrera del coordinador; dentro de ella no se toma ``_guard``. Un
        rechazo no abre transacción ni invalida el feed, y se recuerda un rato.
        """
        key = ("resume", job_id)
        with self._guard:
            if job_id in self._resumed or job_id in self.job_executions:
                return None
            alive = set(self.owners)
        if self._backed_off(key):
            return None
        live = self._live_jobs()
        stamp = models.utc_now()

        def read(executor):
            job = (
                executor.execute(
                    select(models.Job.__table__).where(
                        models.Job.id == job_id,
                        models.Job.task == "post.audio",
                        models.Job.lane == "cpu",
                        models.Job.status == "interrupted",
                        models.Job.deleted_at.is_(None),
                        models.Job.cancel_requested_at.is_(None),
                        self._owner_filter(),
                    )
                )
                .mappings()
                .one_or_none()
            )
            cpu = (
                executor.execute(
                    select(models.CpuExecution.__table__)
                    .where(
                        models.CpuExecution.job_id == job_id,
                        models.CpuExecution.state == "interrupted",
                        models.CpuExecution.deleted_at.is_(None),
                    )
                    .order_by(models.CpuExecution.ordinal.desc())
                    .limit(1)
                )
                .mappings()
                .one_or_none()
            )
            return job, cpu

        with Session(self.engine) as session:
            job, cpu = read(session)
            if job is None or cpu is None:
                return None
            if (
                cpu["id"] in alive
                or not self._process_dead(cpu["process_identity"], cpu["id"])
                or self._occupied_slots(session) >= 2
            ):
                self._back_off(key)
                return None

        def claim(connection):
            job, cpu = read(connection)
            if (
                job is None
                or cpu is None
                or cpu["id"] in alive
                or not self._process_dead(cpu["process_identity"], cpu["id"])
                or self._occupied_slots(connection, live=live) >= 2
            ):
                return None
            revision = cas(
                connection,
                "cpu_execution",
                cpu["id"],
                cpu["revision"],
                "interrupted",
                cleanup_state="confirmed",
            )
            cas(
                connection,
                "cpu_execution",
                cpu["id"],
                revision,
                "prepared",
                supervisor_epoch=secrets.token_hex(16),
                lease_token=secrets.token_hex(16),
                process_identity=None,
                error_code=None,
            )
            connection.execute(
                models.Job.__table__.update()
                .where(models.Job.id == job_id)
                .values(status="running", error_code=None, error=None, updated_at=stamp)
            )
            return cpu["id"]

        execution_id = self.publisher.transaction(
            claim, wrote=lambda value: value is not None
        )
        if execution_id is None:
            self._back_off(key)
            return None
        with self._guard:
            self._resumed.add(job_id)
        return execution_id

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
        """Claim, plan and execute one durable ``post.audio`` job.

        Un post ``interrupted`` con la muerte del proceso anterior probada se
        reanuda sobre su misma ``cpu_execution``; si no, se reclama como nuevo.
        """
        resume = False
        if execution_id is None:
            execution_id = self.claim_resume(job_id)
            resume = execution_id is not None
        if not resume:
            execution_id = execution_id or models.new_id()
            if not self.claim_job(job_id):
                return None
        with self._guard:
            self.job_executions[job_id] = execution_id
        try:
            plan = self.plan_for_job(job_id, execution_id)
            return self.execute(plan, execution_id=execution_id, resume=resume)
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

    def _prepare(self, plan, execution_id, resume=False):
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
        if previous is not None and resume:
            return self._prepare_resume(
                plan,
                execution_id,
                previous,
                raw,
                context,
                prepared_context,
                context_seals,
            )
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

    def _prepare_resume(
        self, plan, execution_id, previous, raw, context, prepared_context, seals
    ):
        """Reanuda una ejecución ``prepared`` tras ``claim_resume`` (CA-1).

        Las intents ``reserved`` se vuelven a procesar desde el WAV crudo; las que
        ya salieron de ``reserved`` se republican desde su staging (que T-05
        conserva) y se excluyen del hijo con ``resume-skip.json``.
        """
        if previous["plan_sha256"] != canonical_sha256(plan):
            raise ValueError("PROVENANCE_MISMATCH")
        if previous["state"] != "prepared" or previous["cleanup_state"] != "confirmed":
            raise ValueError("CPU_CUSTODY_UNKNOWN")
        with self.engine.connect() as connection:
            states = {
                entry.authority.take_id: self.publisher.intent(connection, entry)[
                    "state"
                ]
                for entry in plan.takes
            }
        pending = [e for e in plan.takes if states[e.authority.take_id] == "reserved"]
        skipped = [e for e in plan.takes if states[e.authority.take_id] != "reserved"]
        packaged = [
            e
            for e in skipped
            if states[e.authority.take_id] in {"prepared", "renamed", "committed"}
        ]
        context_raw = prepared_context.payload
        if packaged:
            context, digest = self.publisher.receipt_from_history(
                plan, execution_id, context_raw, entries=packaged
            )
            prepared_context = PreparedContext(
                value=context, payload=context_raw, digest=digest
            )
        else:
            digest = prepared_context.digest
            self._put_receipt(context_raw, digest)
        self.publisher.contexts[execution_id] = context
        self.publisher.receipt_hashes[execution_id] = digest
        self.publisher.prepared_contexts[execution_id] = prepared_context
        self.publisher.context_seals[execution_id] = seals
        self._skipped[execution_id] = {e.authority.take_id for e in skipped}
        if not pending:
            return previous, None
        with self.engine.connect() as connection:
            terminal = (
                connection.execute(
                    select(models.JobAttempt.__table__).where(
                        models.JobAttempt.id
                        == plan.takes[0].authority.winning_attempt_id
                    )
                )
                .mappings()
                .one()["terminal"]
                .model_dump(mode="json")
            )
        for entry in pending:
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
            expected_copy = f"data/tmp/_server_inputs/{execution_id}/{entry.authority.output_index}.wav"
            if entry.copied_source.path != expected_copy:
                raise ValueError("UNSAFE_PATH")
            payload = read_file(safe_path(self.root, entry.source.path))
            if (
                len(payload) != entry.source.bytes
                or hashlib.sha256(payload).hexdigest() != entry.source.sha256
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            copied = safe_path(self.root, expected_copy)
            copied.parent.mkdir(parents=True, exist_ok=True)
            if copied.exists():
                if read_file(copied) != payload:
                    raise ValueError("PROVENANCE_MISMATCH")
            else:
                write_once(copied, payload)
            # Una salida a medias del hijo muerto no se reutiliza jamás.
            remove_data_dir(
                self.root / "data",
                "songs",
                entry.authority.song_id,
                "takes",
                f".pending-{execution_id}",
                entry.authority.take_id,
                log=self.log,
                extra={"song_id": entry.authority.song_id},
            )
            if stage(self.root, execution_id, entry).exists():
                raise ValueError("UNSAFE_PATH")
        run = safe_path(self.root, f"data/tmp/_server_cpu/{execution_id}")
        run.mkdir(parents=True, exist_ok=True)
        plan_file = run / "post-plan.json"
        if plan_file.exists():
            if read_file(plan_file, limit=MAX_PLAN_BYTES) != raw:
                raise ValueError("PROVENANCE_MISMATCH")
        else:
            write_once(plan_file, raw)
        marker = run / "resume-skip.json"
        if marker.exists():
            marker.unlink()
        write_once(
            marker,
            canonical_bytes({"skip": sorted(e.authority.take_id for e in skipped)}),
        )
        return previous, run

    def _finish(self, plan, execution_id, results):
        """``draining → finished`` con el post cerrado, y limpieza de lo crudo."""

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
                "mixed" if ready and failed else "all_ready" if ready else "all_failed"
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

    def _finish_replay(self, plan, execution_id, cpu):
        """Reanudación sin nada que reprocesar: republica y cierra la ejecución."""

        def running(connection):
            self.publisher.authority(connection, plan, execution_id)
            return cas(
                connection,
                "cpu_execution",
                execution_id,
                cpu["revision"],
                "running",
            )

        self.publisher.transaction(running)
        self.publisher.reconcile(plan, execution_id)
        results = self._stored_results(plan, execution_id)
        if len(results) != len(plan.takes):
            raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY")
        return self._finish(plan, execution_id, results)

    def execute(self, plan, *, execution_id, resume=False):

        # One local invocation owns this execution; SQLite CAS is still the
        # durable authority, and the shared coordinator governs every commit.
        with self._guard:
            if execution_id in self.owners:
                raise ValueError("CPU_EXECUTION_ACTIVE")
            cpu, run = self._prepare(plan, execution_id, resume=resume)
            if run is None:
                if resume:
                    return self._finish_replay(plan, execution_id, cpu)
                self.publisher.reconcile(plan, execution_id)
                return self._stored_results(plan, execution_id)
            skipped = self._skipped.pop(execution_id, set())
            # Rastro durable ANTES de lanzar: si el server muere entre el lanzamiento
            # y la CAS que guarda la identidad real, no se prueba una muerte falsa.
            launching = self.publisher.transaction(
                lambda connection: cas(
                    connection,
                    "cpu_execution",
                    execution_id,
                    cpu["revision"],
                    "prepared",
                    process_identity={"launching": True},
                ),
                wrote=lambda value: True,
            )
            cpu = dict(cpu, revision=launching)
            known = set(LINUX_GROUPS)
            try:
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
            except BaseException:
                # Sin ningún grupo nuevo (ni Popen) se sabe que no se lanzó nada:
                # la marca vuelve a «nunca lanzado» para poder cancelar/reanudar.
                if not any(hasattr(g, "process") for g in set(LINUX_GROUPS) - known):
                    try:
                        self.publisher.transaction(
                            lambda connection: cas(
                                connection,
                                "cpu_execution",
                                execution_id,
                                cpu["revision"],
                                "prepared",
                                process_identity=None,
                            ),
                            wrote=lambda value: True,
                        )
                    except Exception:  # noqa: BLE001 -- se conserva el error primario
                        self.log.error("worker.cleanup.failed")
                raise
            owner = Owner(group, execution_id, cpu["supervisor_epoch"], 3600)
            self.owners[execution_id] = owner
            self._owner_jobs[execution_id] = plan.post_job_id
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
            if not receipt.release_gate or len(results) != len(plan.takes) - len(
                skipped
            ):
                raise ValueError("CPU_CUSTODY_UNKNOWN")
            if skipped:
                # Las ya empaquetadas en el intento anterior se republican desde su
                # staging y aportan su resultado almacenado.
                self.publisher.reconcile(plan, execution_id)
                stored = [
                    r
                    for r in self._stored_results(plan, execution_id)
                    if r.take_id in skipped
                ]
                if len(stored) != len(skipped):
                    raise ValueError("CPU_EXECUTION_REQUIRES_RECOVERY")
                results.extend(stored)

            return self._finish(plan, execution_id, results)
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
                    self._owner_jobs.pop(execution_id, None)

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
            # Sin ejecución viva en este proceso (p. ej. tras un reinicio): se
            # cancela el post interrumpido si se prueba la muerte del anterior.
            return self.cancel_interrupted(job_id)
        self.cancel(execution_id)
        return True

    _TERMINAL = ("finished", "failed", "cancelled")

    def cancel_interrupted(self, job_id):
        """Cancela un ``post.audio`` ``interrupted`` sin dueño vivo (CA-3).

        Solo con prueba de muerte del proceso anterior: la custodia pasa a
        ``confirmed`` y la ``cpu_execution`` y sus intents quedan en estados
        finales válidos. Sin prueba no cambia nada, no abre transacción ni
        invalida el feed, devuelve ``False`` y no se vuelve a sondear enseguida.
        """
        key = ("cancel", job_id)
        with self._guard:
            live = set(self.owners)
            if job_id in self.job_executions:
                return False
        if self._backed_off(key):
            return False
        stamp = models.utc_now()
        songs = []

        def read(executor):
            job = (
                executor.execute(
                    select(models.Job.__table__).where(
                        models.Job.id == job_id,
                        models.Job.task == "post.audio",
                        models.Job.status == "interrupted",
                        models.Job.deleted_at.is_(None),
                        models.Job.cancel_requested_at.is_not(None),
                        self._owner_filter(),
                    )
                )
                .mappings()
                .one_or_none()
            )
            if job is None:
                return None, []
            executions = (
                executor.execute(
                    select(models.CpuExecution.__table__).where(
                        models.CpuExecution.job_id == job_id,
                        models.CpuExecution.deleted_at.is_(None),
                        models.CpuExecution.state.not_in(self._TERMINAL),
                    )
                )
                .mappings()
                .all()
            )
            return job, executions

        def proven(executions):
            return not any(
                row["id"] in live
                or not self._process_dead(row["process_identity"], row["id"])
                for row in executions
            )

        with Session(self.engine) as session:
            job, executions = read(session)
            if job is None or not proven(executions):
                self._back_off(key)
                return False

        def cancel(connection):
            job, executions = read(connection)
            if job is None or not proven(executions):
                return False
            for row in executions:
                revision = row["revision"]
                if row["state"] in {"running", "draining"}:
                    revision = cas(
                        connection,
                        "cpu_execution",
                        row["id"],
                        revision,
                        "interrupted",
                        cleanup_state="confirmed",
                    )
                cas(
                    connection,
                    "cpu_execution",
                    row["id"],
                    revision,
                    "cancelled",
                    cleanup_state="confirmed",
                    error_code="CANCELLED",
                    finished_at=stamp,
                )
                self._cancel_intents(connection, row["id"], job["song_id"])
            connection.execute(
                models.Job.__table__.update()
                .where(models.Job.id == job_id)
                .values(
                    status="cancelled",
                    finished_at=stamp,
                    updated_at=stamp,
                    error_code=None,
                    error=None,
                )
            )
            songs.append(job["song_id"])
            return True

        if not self.publisher.transaction(cancel, wrote=bool):
            self._back_off(key)
            return False
        for song_id in songs:
            try:
                snapshots.publish(self.engine, song_id, self.root / "data")
            except Exception:  # noqa: BLE001 -- el snapshot nunca deshace la cancelación
                self.log.error("worker.cleanup.failed", extra={"job_id": job_id})
        try:
            sweep_cancelled(self.engine, self.owner_id, self.root / "data", self.log)
        except Exception:  # noqa: BLE001 -- la limpieza nunca aborta
            self.log.error("worker.cleanup.failed", extra={"job_id": job_id})
        for song_id in songs:  # un fallo del barrido no impide quitar el staging
            try:
                self._remove_stages(song_id, job_id)
            except Exception:  # noqa: BLE001 -- la limpieza nunca aborta
                self.log.error("worker.cleanup.failed", extra={"job_id": job_id})
        return True

    def _cancel_intents(self, connection, execution_id, song_id):
        """Intents de una ejecución cancelada a estados finales (como ``fail``)."""
        rows = (
            connection.execute(
                select(
                    models.PublicationIntent.__table__,
                    models.PublicationIntentRevision.id.label("revision_id"),
                )
                .join(
                    models.PublicationIntentRevision.__table__,
                    models.PublicationIntentRevision.intent_id
                    == models.PublicationIntent.id,
                )
                .where(
                    models.PublicationIntentRevision.cpu_execution_id == execution_id
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            if row["state"] not in {"reserved", "prepared", "renamed"}:
                continue  # committed conserva su take ready; el resto ya es final
            target = "quarantined" if row["state"] == "renamed" else "cancelled"
            connection.execute(
                models.PublicationIntentRevision.__table__.update()
                .where(
                    models.PublicationIntentRevision.id == row["active_revision_id"],
                    models.PublicationIntentRevision.error_code.is_(None),
                )
                .values(error_code="CANCELLED")
            )
            connection.execute(
                models.Take.__table__.update()
                .where(models.Take.id == row["take_id"], models.Take.status != "ready")
                .values(status="cancelled", error_code="CANCELLED")
            )
            cas(
                connection,
                "publication_intent",
                row["id"],
                row["revision"],
                target,
                error_code="CANCELLED",
            )

    def _remove_stages(self, song_id, job_id):
        """Quita ``takes/.pending-<exec>`` de las ejecuciones canceladas del post."""
        with Session(self.engine) as session:
            executions = list(
                session.scalars(
                    select(models.CpuExecution.id).where(
                        models.CpuExecution.job_id == job_id
                    )
                )
            )
        for execution_id in executions:
            remove_data_dir(
                self.root / "data",
                "songs",
                song_id,
                "takes",
                f".pending-{execution_id}",
                log=self.log,
                extra={"job_id": job_id, "song_id": song_id},
            )
