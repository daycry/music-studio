"""Borrado seguro de ``data/tmp`` de los jobs terminales (M1/T-04 CA-3, M1/T-17).

Reglas de T-05 (ADR-0089 §2): nunca se sigue un symlink ni una junction, nada
sale de ``data/`` y un fallo es un evento fijo (``worker.cleanup.failed``), no
una excepción que aborte el bucle de la cola.
"""

import json
import logging
import re
import shutil
import time
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models

from .cancellation import local_jobs

LIVE = ("queued", "blocked", "running", "interrupted")
TERMINAL = ("succeeded", "failed", "cancelled")
PERMANENT = "permanent"  # fallo que reintentar no arregla
_HEX = re.compile(r"[0-9a-f]{32}")
IN_CHUNK = 500  # SQLite limita las variables de una sentencia (32.766 por defecto)
_REPORTED = set()  # fallos permanentes ya registrados en este proceso
_REPORTED_CAP = 10000


def _chunks(items, size=None):
    items = list(items)
    size = size or IN_CHUNK
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _report_permanent(log, extra, key):
    """Registra un fallo permanente una sola vez por proceso y destino."""
    if key in _REPORTED:
        return PERMANENT
    if len(_REPORTED) >= _REPORTED_CAP:
        _REPORTED.clear()
    _REPORTED.add(key)
    log.error("worker.cleanup.failed", extra=extra)
    return PERMANENT


_PART = re.compile(r"(?:\.pending-)?[0-9A-Za-z_]+")


def _link(path):
    return path.is_symlink() or path.is_junction()


def remove_data_dir(data_dir, *parts, log=None, extra=None):
    """Borra ``data/<parts>`` si es un directorio propio.

    ``True`` lo borró, ``False`` no había nada que borrar, ``None`` falló de
    forma transitoria (``OSError``: se puede reintentar) y ``PERMANENT`` falló
    de forma que reintentar no arregla (parte inválida, enlace, no-directorio o
    fuera de ``data/``). Todo fallo se registra como evento fijo.
    """
    log = log or logging.getLogger(__name__)
    extra = extra or {}
    if not parts or not all(isinstance(p, str) and _PART.fullmatch(p) for p in parts):
        return _report_permanent(log, extra, ("invalid", repr(parts)))
    data = Path(data_dir)
    key = (str(data), parts)
    try:
        chain = [data]
        for part in parts:
            chain.append(chain[-1] / part)
        target = chain[-1]
        if not any(_link(p) or p.exists() for p in chain[1:]):
            return False
        if any(_link(p) for p in chain):
            return _report_permanent(log, extra, key)
        if not target.exists():
            return False
        if not target.is_dir() or not target.resolve().is_relative_to(data.resolve()):
            return _report_permanent(log, extra, key)
        shutil.rmtree(target)
        log.info("worker.staging.removed", extra=extra)
        return True
    except OSError:
        log.error("worker.cleanup.failed", extra=extra)
        return None


def needed_by_live_job(session, job_id):
    """Otro job vivo depende de las salidas crudas de ``job_id``."""
    return (
        session.scalar(
            select(models.JobDependency.id)
            .join(models.Job, models.Job.id == models.JobDependency.job_id)
            .where(
                models.JobDependency.depends_on_job_id == job_id,
                models.JobDependency.deleted_at.is_(None),
                models.Job.status.in_(LIVE),
                models.Job.deleted_at.is_(None),
            )
            .limit(1)
        )
        is not None
    )


def _generation_id(job):
    request = job.request if isinstance(job.request, dict) else {}
    inputs = request.get("inputs")
    if isinstance(inputs, list) and inputs and isinstance(inputs[0], dict):
        ref = inputs[0].get("ref")
        if isinstance(ref, dict) and isinstance(ref.get("id"), str):
            return ref["id"]
    return None


def _terminal_ids(session, owner_id, statuses=TERMINAL):
    """Ids de los jobs terminales locales, sin hidratar nada (consulta barata)."""
    query = local_jobs(owner_id).where(models.Job.status.in_(list(statuses)))
    return list(session.scalars(query.with_only_columns(models.Job.id)))


def _staged_input(path):
    """``tmp/_server_inputs/<hex>/<n>`` de ``queue/inputs.py`` → ``<hex>``."""
    parts = path.split("/") if isinstance(path, str) else []
    if len(parts) == 4 and parts[:2] == ["tmp", "_server_inputs"]:
        return parts[2] if _HEX.fullmatch(parts[2]) else None
    return None


def _staged_names(raw):
    try:
        items = json.loads(raw) if isinstance(raw, str) else (raw or [])
    except ValueError:
        return set()
    names = set()
    for item in items if isinstance(items, list) else []:
        name = _staged_input(item.get("path")) if isinstance(item, dict) else None
        if name:
            names.add(name)
    return names


def _will_retry(job, rows):
    """El retry x2 todavía puede recoger este ``failed`` (alineado con ``Retry``).

    Replica ``Retry.eligible`` (estado, intentos, ``attempt.status == failed``,
    terminal ``error`` retryable) más los carriles que el reintento nunca toca
    (``remote``) y el caso en que ``reserve`` lo rechazaría siempre: un
    ``VRAM_EXCEEDED`` que ya se probó en ``offload``. Lo que depende del catálogo
    vivo (engine o modelo cambiado) no se replica: esos jobs quedan aparcados
    con su propio backoff y no consumen el presupuesto del histórico.
    """
    if not (
        job.status == "failed"
        and job.lane in {"gpu", "cpu"}
        and not job.cancel_requested_at
        and job.attempt
        and type(job.max_attempts) is int
        and 1 <= job.attempt < job.max_attempts <= 3
    ):
        return False
    last = next(
        (
            r
            for r in rows
            if r.ordinal == job.attempt
            and r.deleted_at is None
            and r.status == "failed"
            and r.kind == "error"
            and r.retryable == "true"
        ),
        None,
    )
    if last is None:
        return False
    if last.code == "VRAM_EXCEEDED" and any(r.mode == "offload" for r in rows):
        return False
    return True


def terminal_targets(session, owner_id, ids=None, statuses=TERMINAL, report=None):
    """``(job_id, (partes...))`` de lo que un job terminal ya no necesita.

    Cubre los directorios de TODOS los attempts del job (también los abandonados
    por el reintento), las entradas staged de sus peticiones y, para un post, sus
    ``_server_inputs/<exec>`` y ``_server_cpu/<exec>``. No toca nada que un job
    vivo necesite ni lo que un reintento automático pendiente va a reutilizar.
    Solo lee las columnas que usa (nada de provenance ni terminales completos).
    ``report`` recoge ``deferred`` (otro job vivo lo necesita) y ``waiting``
    (reintento automático pendiente): ninguno de los dos queda resuelto.
    """
    if ids is None:
        ids = _terminal_ids(session, owner_id, statuses)
    targets, deferred, waiting = [], set(), set()
    if not ids:
        if report is not None:
            report.update(deferred=deferred, waiting=waiting)
        return targets
    jobs, attempts = [], {}
    for part in _chunks(ids):
        jobs += session.execute(
            select(
                models.Job.id,
                models.Job.task,
                models.Job.lane,
                models.Job.status,
                models.Job.attempt,
                models.Job.max_attempts,
                models.Job.cancel_requested_at,
                func.json_extract(models.Job.request, "$.inputs[0].ref.id").label(
                    "gen"
                ),
            ).where(models.Job.id.in_(part))
        ).all()
        for row in session.execute(
            select(
                models.JobAttempt.job_id,
                models.JobAttempt.id,
                models.JobAttempt.ordinal,
                models.JobAttempt.status,
                models.JobAttempt.mode,
                models.JobAttempt.deleted_at,
                func.json_extract(models.JobAttempt.engine_request, "$.inputs").label(
                    "inputs"
                ),
                func.json_extract(models.JobAttempt.terminal, "$.type").label("kind"),
                func.json_extract(models.JobAttempt.terminal, "$.data.code").label(
                    "code"
                ),
                func.json_type(models.JobAttempt.terminal, "$.data.retryable").label(
                    "retryable"
                ),
            ).where(models.JobAttempt.job_id.in_(part))
        ):
            attempts.setdefault(row.job_id, []).append(row)
    for job in jobs:
        if needed_by_live_job(session, job.id):
            deferred.add(job.id)
            continue
        rows = attempts.get(job.id, [])
        if _will_retry(job, rows):
            waiting.add(job.id)  # el retry x2 reutiliza sus entradas congeladas
            continue
        staged = set()
        for row in rows:
            targets.append((job.id, ("tmp", row.id)))
            staged |= _staged_names(row.inputs)
        for name in sorted(staged):
            targets.append((job.id, ("tmp", "_server_inputs", name)))
        if job.task != "post.audio":
            continue
        for execution_id in session.scalars(
            select(models.CpuExecution.id).where(models.CpuExecution.job_id == job.id)
        ):
            targets.append((job.id, ("tmp", "_server_cpu", execution_id)))
            targets.append((job.id, ("tmp", "_server_inputs", execution_id)))
        generation = job.gen if isinstance(job.gen, str) else None
        if generation is None:
            continue
        if needed_by_live_job(session, generation):
            deferred.add(job.id)
            continue
        for attempt_id in session.scalars(
            select(models.JobAttempt.id).where(models.JobAttempt.job_id == generation)
        ):
            targets.append((job.id, ("tmp", attempt_id)))
    if report is not None:
        report.update(deferred=deferred, waiting=waiting)
    return targets


cancelled_targets = terminal_targets


def _remove_targets(targets, data_dir, log, failed=None):
    removed = 0
    for job_id, parts in targets:
        outcome = remove_data_dir(data_dir, *parts, log=log, extra={"job_id": job_id})
        removed += outcome is True
        if outcome is None and failed is not None:
            failed.add(job_id)  # transitorio: se reintenta; PERMANENT no
    return removed


def sweep_cancelled(engine, owner_id, data_dir, log=None):
    """Barrido completo de ``data/tmp`` de los cancelados. Idempotente."""
    with Session(engine) as session:
        targets = terminal_targets(session, owner_id, statuses=("cancelled",))
    return _remove_targets(targets, data_dir, log)


class TerminalSweeper:
    """Barrido de ``data/tmp`` de los terminales, por conjunto de «resueltos».

    No depende de ningún reloj ni de ``updated_at``: en cada pasada se lee solo la
    lista de ids terminales (sin hidratar) y se descartan los ya resueltos.
    El histórico NUEVO se procesa de ``BUDGET`` en ``BUDGET``; ``pending`` es lo
    que queda de él y solo mientras sea > 0 conviene volver a llamar enseguida.

    Un job queda resuelto al limpiarse del todo, al registrar un fallo permanente
    (una vez por proceso) o tras ``MAX_RETRIES`` fallos transitorios. Los que no se
    pueden resolver aún (otro job vivo los necesita, o un reintento automático va a
    reutilizar sus entradas) quedan APARCADOS: se reevalúan cada ``PARK_S``
    segundos con su propio presupuesto, de modo que ni consumen el del histórico
    nuevo (sin inanición) ni mantienen la cadencia rápida. Los fallos transitorios
    se reintentan en cada pasada. El estado vive en memoria: sin migración.
    """

    BUDGET = 200
    MAX_RETRIES = 5
    PARK_S = 10.0

    def __init__(self, engine, owner_id, data_dir, log=None):
        self.engine, self.owner_id = engine, owner_id
        self.data_dir, self.log = data_dir, log
        self.resolved, self.failures = set(), {}
        self.parked, self.needed, self.transient = {}, set(), set()
        self.last_scanned, self.pending = 0, 0

    @property
    def deferred(self):
        return self.needed | self.transient

    def run(self, force=False):
        if force:
            self.resolved, self.failures = set(), {}
            self.parked, self.needed, self.transient = {}, set(), set()
        now = time.monotonic()
        report = {}
        with Session(self.engine) as session:
            current = set(_terminal_ids(session, self.owner_id))
            self.resolved &= current  # un job que dejó de ser terminal se reevalúa
            self.transient &= current
            for gone in set(self.parked) - current:
                del self.parked[gone]
            self.needed &= current
            fresh = sorted(
                current - self.resolved - set(self.parked) - self.transient,
                reverse=True,
            )
            new = fresh[: self.BUDGET]
            self.pending = len(fresh) - len(new)
            due = [j for j, until in self.parked.items() if until <= now]
            batch = list(
                dict.fromkeys(new + due[: self.BUDGET] + sorted(self.transient))
            )
            targets = terminal_targets(session, self.owner_id, ids=batch, report=report)
        self.last_scanned = len(batch)
        failed = set()
        removed = _remove_targets(targets, self.data_dir, self.log, failed)
        for job_id in failed:
            self.failures[job_id] = self.failures.get(job_id, 0) + 1
        gave_up = {j for j in failed if self.failures[j] >= self.MAX_RETRIES}
        retrying = failed - gave_up
        self.transient = (self.transient - set(batch)) | retrying
        parked = report["deferred"] | report["waiting"]
        for job_id in batch:
            self.parked.pop(job_id, None)
            self.needed.discard(job_id)
        for job_id in parked:
            self.parked[job_id] = now + self.PARK_S
        self.needed |= report["deferred"]
        self.resolved |= set(batch) - parked - retrying
        for job_id in set(batch) - failed:
            self.failures.pop(job_id, None)
        for job_id in gave_up:
            self.failures.pop(job_id, None)
        return removed


CancelSweeper = TerminalSweeper
