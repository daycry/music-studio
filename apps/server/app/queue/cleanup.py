"""Borrado seguro de ``data/tmp`` de los jobs cancelados (M1/T-04, CA-3).

Reglas de T-05 (ADR-0089 §2): nunca se sigue un symlink ni una junction, nada
sale de ``data/`` y un fallo es un evento fijo (``worker.cleanup.failed``), no
una excepción que aborte el bucle de la cola.
"""

import logging
import re
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

from .cancellation import local_jobs

LIVE = ("queued", "blocked", "running", "interrupted")
_PART = re.compile(r"(?:\.pending-)?[0-9A-Za-z_]+")


def _link(path):
    return path.is_symlink() or path.is_junction()


def remove_data_dir(data_dir, *parts, log=None, extra=None):
    """Borra ``data/<parts>`` si es un directorio propio; devuelve si lo borró."""
    log = log or logging.getLogger(__name__)
    extra = extra or {}
    if not parts or not all(isinstance(p, str) and _PART.fullmatch(p) for p in parts):
        log.error("worker.cleanup.failed", extra=extra)
        return False
    data = Path(data_dir)
    try:
        chain = [data]
        for part in parts:
            chain.append(chain[-1] / part)
        target = chain[-1]
        if not any(_link(p) or p.exists() for p in chain[1:]):
            return False
        if any(_link(p) for p in chain):
            log.error("worker.cleanup.failed", extra=extra)
            return False
        if not target.exists():
            return False
        if not target.is_dir() or not target.resolve().is_relative_to(data.resolve()):
            log.error("worker.cleanup.failed", extra=extra)
            return False
        shutil.rmtree(target)
        log.info("worker.staging.removed", extra=extra)
        return True
    except OSError:
        log.error("worker.cleanup.failed", extra=extra)
        return False


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


def cancelled_targets(session, owner_id):
    """``(job_id, (partes...))`` de lo que un job cancelado ya no necesita."""
    targets = []
    cancelled = local_jobs(owner_id).where(models.Job.status == "cancelled")
    for job in session.scalars(cancelled):
        if needed_by_live_job(session, job.id):
            continue
        for attempt_id in session.scalars(
            select(models.JobAttempt.id).where(models.JobAttempt.job_id == job.id)
        ):
            targets.append((job.id, ("tmp", attempt_id)))
        if job.task != "post.audio":
            continue
        for execution_id in session.scalars(
            select(models.CpuExecution.id).where(models.CpuExecution.job_id == job.id)
        ):
            targets.append((job.id, ("tmp", "_server_cpu", execution_id)))
            targets.append((job.id, ("tmp", "_server_inputs", execution_id)))
        generation = _generation_id(job)
        if generation is None or needed_by_live_job(session, generation):
            continue
        for attempt_id in session.scalars(
            select(models.JobAttempt.id).where(models.JobAttempt.job_id == generation)
        ):
            targets.append((job.id, ("tmp", attempt_id)))
    return targets


def sweep_cancelled(engine, owner_id, data_dir, log=None):
    """Borra ``data/tmp/<attempt>`` y temporales de posts cancelados. Idempotente."""
    with Session(engine) as session:
        targets = cancelled_targets(session, owner_id)
    removed = 0
    for job_id, parts in targets:
        removed += bool(
            remove_data_dir(data_dir, *parts, log=log, extra={"job_id": job_id})
        )
    return removed
