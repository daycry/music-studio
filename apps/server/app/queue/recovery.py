"""Reconcilia la misma identidad sin reiniciar cursores por conjetura."""

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, utc_now

from .admission import occupancy_filters, writer
from .cancellation import local_jobs
from .inputs import (
    ResolutionError,
    StagedInputs,
    confined_path,
    file_identity,
    verified_file,
)


class Recovery:
    def __init__(self, engine, owner, data_dir):
        self.engine, self.owner, self.data_dir = engine, owner, Path(data_dir)

    def startup(self):
        with Session(self.engine) as session, session.begin():
            writer(session)
            for job in session.scalars(
                local_jobs(self.owner).where(Job.status == "running")
            ):
                job.status = "interrupted"
                job.error = "Reconciliación del intento durable pendiente"

    def uncertain(self, aid, reason):
        with Session(self.engine) as session, session.begin():
            writer(session)
            attempt = session.get(JobAttempt, aid)
            job = (
                session.scalar(local_jobs(self.owner).where(Job.id == attempt.job_id))
                if attempt
                else None
            )
            if (
                job
                and job.attempt == attempt.ordinal
                and attempt.terminal is None
                and job.status in {"running", "interrupted"}
            ):
                job.status, job.error, job.updated_at = "interrupted", reason, utc_now()

    @staticmethod
    def lost_event(attempt):
        """Terminal ``error`` retryable: el engine confirmó que no conserva el intento.

        El retry x2 existente lo recoge (attempt nuevo, misma semilla, hasta
        ``max_attempts``); no se reenvía nada por conjetura.
        """
        return {
            "job_id": attempt.id,
            "seq": attempt.last_seq + 1,
            "ts": utc_now(),
            "type": "error",
            "data": {
                "code": "INTERNAL",
                "message": "El engine no conserva el intento tras el reinicio",
                "retryable": True,
            },
        }

    def current(self, aid):
        with Session(self.engine, expire_on_commit=False) as session:
            attempt = session.get(JobAttempt, aid)
            job = (
                session.scalar(local_jobs(self.owner).where(Job.id == attempt.job_id))
                if attempt
                else None
            )
            if not (
                job
                and attempt.owner_id == self.owner
                and not attempt.deleted_at
                and job.attempt == attempt.ordinal
                and job.engine_id == attempt.engine_id
            ):
                return None
            return attempt, job.cancel_requested_at

    def safe_inputs(self, attempt):
        wires, identities = [], []
        for item in attempt.engine_request.inputs:
            wire = item.model_dump(mode="json")
            if not wire["path"].startswith("tmp/_server_inputs/"):
                raise ResolutionError("Frozen input lacks server ownership")
            verified_file(self.data_dir, wire)
            wires.append(wire)
            identities.append(file_identity(confined_path(self.data_dir, wire["path"])))
        return StagedInputs(self.data_dir, None, wires, tuple(identities))

    def safe_absent(self, attempt):
        self.safe_inputs(attempt)
        output = self.data_dir / attempt.engine_request.output_dir
        for path in (self.data_dir, self.data_dir / "tmp", output):
            if path.is_symlink() or (
                hasattr(path, "is_junction") and path.is_junction()
            ):
                return False
        # Un directorio preexistente vacío tampoco acredita propiedad.
        return attempt.last_seq == 0 and not output.exists() and not output.is_symlink()

    def other_active(self, job_id, lane, engine_id):
        with Session(self.engine) as session:
            active, occupied, owned, live = occupancy_filters(self.owner)
            return bool(
                session.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.id != job_id,
                        active,
                        occupied,
                        owned,
                        live,
                        (Job.lane == lane) | (Job.engine_id == engine_id),
                    )
                )
            )
