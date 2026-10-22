"""Intención durable separada del terminal confirmado del engine."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, Song, User, utc_now

from .admission import writer


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
    def __init__(self, engine, owner):
        self.engine, self.owner = engine, owner

    def request(self, job_id):
        with Session(self.engine) as session, session.begin():
            writer(session)
            job = session.scalar(local_jobs(self.owner).where(Job.id == job_id))
            if job is None:
                raise ValueError("Local job absent")
            if job.status in {"succeeded", "failed", "cancelled"}:
                return False
            if job.cancel_requested_at is None:
                job.cancel_requested_at = utc_now()
            if job.attempt == 0:
                job.status, job.finished_at = "cancelled", utc_now()
            return True

    def pending(self):
        with Session(self.engine) as session, session.begin():
            writer(session)
            result = []
            for job in session.scalars(
                local_jobs(self.owner).where(Job.cancel_requested_at.is_not(None))
            ):
                if job.status in {"queued", "blocked"} and job.attempt == 0:
                    job.status, job.finished_at = "cancelled", utc_now()
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
            return result
