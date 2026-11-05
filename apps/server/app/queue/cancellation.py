"""Intención durable separada del terminal confirmado del engine."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, Song, User, utc_now
from app.publication import (
    CommitPublication,
    PublicationCoordinator,
    _confirmed_rollback,
)

from .admission import writer
from .terminal_takes import terminalize_placeholders


def local_jobs(owner):
    return (
        select(Job)
        .join(Song, Song.id == Job.song_id)
        .join(User, User.id == Job.owner_id)
        .where(
            Job.owner_id == owner,
            Song.owner_id == owner,
            User.name == "local",
            User.deleted_at.is_(None),
            Song.deleted_at.is_(None),
            Song.is_dependency_only.is_(False),
            Job.deleted_at.is_(None),
        )
    )


class Cancellation:
    def __init__(self, engine, owner, *, coordinator=None, bus=None):
        self.engine, self.owner = engine, owner
        if (coordinator is None) != (bus is None) or (
            coordinator is not None and type(coordinator) is not PublicationCoordinator
        ):
            raise TypeError("Explicit shared coordinator and bus required")
        self.coordinator, self.bus = coordinator, bus

    def _transaction(self, operation):
        def commit():
            rejected = None
            try:
                with Session(self.engine) as session, session.begin():
                    try:
                        writer(session)
                        value, wrote = operation(session)
                    except BaseException as primary:
                        rejected = primary
                        raise
            except BaseException as primary:
                # Sólo tras rollback Y close confirmados. Un fallo de commit o
                # limpieza conserva incertidumbre y el coordinador invalida.
                if primary is rejected:
                    return _confirmed_rollback(primary, primary.__traceback__)
                raise
            return CommitPublication(value, (), invalidate=wrote)

        if self.coordinator is not None:
            return self.coordinator.commit_and_publish(commit, self.bus).value
        from app.publication import _ConfirmedRollback

        batch = commit()
        if type(batch) is _ConfirmedRollback:
            raise batch.primary.with_traceback(batch.traceback)
        return batch.value

    def request(self, job_id):
        def operation(session):
            job = session.scalar(local_jobs(self.owner).where(Job.id == job_id))
            if job is None:
                raise ValueError("Local job absent")
            if job.status in {"succeeded", "failed", "cancelled"}:
                return False, False
            wrote = False
            if job.cancel_requested_at is None:
                job.cancel_requested_at = utc_now()
                wrote = True
            if job.attempt == 0:
                job.status, job.finished_at = "cancelled", utc_now()
                terminalize_placeholders(session, job, job.finished_at)
                wrote = True
            return True, wrote

        return self._transaction(operation)

    def pending(self):
        def operation(session):
            result = []
            wrote = False
            for job in session.scalars(
                local_jobs(self.owner).where(Job.cancel_requested_at.is_not(None))
            ):
                if job.status in {"queued", "blocked"} and job.attempt == 0:
                    job.status, job.finished_at = "cancelled", utc_now()
                    terminalize_placeholders(session, job, job.finished_at)
                    wrote = True
                elif job.status in {"running", "interrupted"}:
                    attempt = session.scalar(
                        select(JobAttempt).where(
                            JobAttempt.job_id == job.id,
                            JobAttempt.ordinal == job.attempt,
                            JobAttempt.owner_id == self.owner,
                            JobAttempt.deleted_at.is_(None),
                            JobAttempt.terminal.is_(None),
                        )
                    )
                    if attempt:
                        result.append((attempt.id, attempt.engine_id))
            return result, wrote

        return self._transaction(operation)
