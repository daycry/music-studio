"""Nuevo job lógico, request idéntica; sólo takes failed del job original."""

import asyncio
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, JobDependency, Take, new_id

from .admission import writer
from .chains import add_dependents, live_song, validate_lyrics, validate_request
from .inputs import ResolutionError
from .resolver import snapshot


class ManualRetry:
    def __init__(self, engine, owner_id, resolver):
        self.engine, self.owner_id, self.resolver = engine, owner_id, resolver

    async def retry(self, job_id, *, take_ids=None):
        if take_ids is not None and (
            not isinstance(take_ids, (tuple, list))
            or not take_ids
            or len(take_ids) > 64
            or any(not isinstance(tid, str) for tid in take_ids)
            or len(set(take_ids)) != len(take_ids)
        ):
            raise ResolutionError("Unique selected take IDs required")
        old, takes = await asyncio.to_thread(self._read, job_id, take_ids)
        if not takes:
            return None
        source = snapshot(old)
        await self.resolver.resolve(old, engine=self.engine)
        return await asyncio.to_thread(
            self._claim, old, source, tuple(t.id for t in takes)
        )

    def _failed_post_indices(self, session, old):
        """Autentica el fallo CPU por su arista propia y sus salidas enlazadas."""
        posts = list(
            session.scalars(
                select(Job)
                .join(JobDependency, JobDependency.job_id == Job.id)
                .where(
                    JobDependency.depends_on_job_id == old.id,
                    JobDependency.owner_id == self.owner_id,
                    JobDependency.deleted_at.is_(None),
                    Job.task == "post.audio",
                    Job.owner_id == self.owner_id,
                    Job.song_id == old.song_id,
                    Job.status == "failed",
                    Job.deleted_at.is_(None),
                    Job.cancel_requested_at.is_(None),
                    Job.error_code.is_not(None),
                    Job.finished_at.is_not(None),
                )
            )
        )
        indices = set()
        for post in posts:
            edges = list(
                session.scalars(
                    select(JobDependency)
                    .where(
                        JobDependency.job_id == post.id,
                        JobDependency.deleted_at.is_(None),
                    )
                    .limit(2)
                )
            )
            if (
                len(edges) != 1
                or edges[0].owner_id != self.owner_id
                or not post.error_code
            ):
                continue
            items = post.request.get("inputs", [])
            if not isinstance(items, list) or not items:
                continue
            bound = []
            for item in items:
                if not (
                    isinstance(item, dict)
                    and set(item) == {"role", "ref", "output_index"}
                    and item["role"] == "source"
                    and item["ref"] == {"type": "job", "id": old.id}
                    and type(item["output_index"]) is int
                    and item["output_index"] >= 0
                ):
                    break
                bound.append(item["output_index"])
            else:
                if len(set(bound)) == len(bound):
                    indices.update(bound)
        return indices

    def _selection(self, session, old, take_ids):
        live_song(session, self.owner_id, old.song_id)
        if (
            old.owner_id != self.owner_id
            or old.deleted_at
            or old.status not in {"failed", "succeeded"}
            or old.cancel_requested_at
        ):
            raise ResolutionError("Owned terminal generation required")
        count, seed = validate_request(old)
        needs_post_failure = False
        if old.attempt:
            attempt = session.scalar(
                select(JobAttempt).where(
                    JobAttempt.job_id == old.id,
                    JobAttempt.ordinal == old.attempt,
                    JobAttempt.owner_id == self.owner_id,
                    JobAttempt.deleted_at.is_(None),
                )
            )
            if not (
                attempt
                and attempt.terminal
                and attempt.status in {"failed", "succeeded"}
                and attempt.terminal.type
                == {"failed": "error", "succeeded": "done"}[attempt.status]
                and attempt.terminal.job_id == attempt.id
                and attempt.terminal.seq == attempt.last_seq
                and attempt.engine_id == old.engine_id
                and (old.status != "succeeded" or attempt.status == "succeeded")
            ):
                raise ResolutionError(
                    "Uncertain attempt requires reconciliation, not manual retry"
                )
            needs_post_failure = attempt.status == "succeeded"
        elif old.status == "succeeded":
            raise ResolutionError("Successful generation requires durable done")
        query = select(Take).where(
            Take.job_id == old.id,
            Take.owner_id == self.owner_id,
            Take.song_id == old.song_id,
            Take.status == "failed",
            Take.deleted_at.is_(None),
        )
        if take_ids is not None:
            query = query.where(Take.id.in_(take_ids))
        takes = list(session.scalars(query.order_by(Take.variant_index).limit(65)))
        if len(takes) > 64 or take_ids is not None and len(takes) != len(take_ids):
            raise ResolutionError(
                "Every selected take must be owned live failed original"
            )
        if takes and needs_post_failure:
            eligible = self._failed_post_indices(session, old)
            bound = [t for t in takes if t.variant_index in eligible]
            if not bound or take_ids is not None and len(bound) != len(takes):
                raise ResolutionError("Authenticated own downstream failure required")
            takes = bound
        if (
            len({t.variant_index for t in takes}) != len(takes)
            or len({t.batch_id for t in takes}) > 1
        ):
            raise ResolutionError("Original variant identities mismatch")
        for take in takes:
            if (
                not 0 <= take.variant_index < count
                or take.seed != seed + take.variant_index
                or take.task != old.task
                or take.model_id != old.model_id
                or take.params != old.request.get("params", {})
            ):
                raise ResolutionError("Take must match original immutable request")
            validate_lyrics(session, old, take.lyrics_version_id)
        # La generación no adquiere nuevas aristas ni adopta dependencias ajenas.
        if session.scalar(
            select(JobDependency.id).where(
                JobDependency.job_id == old.id, JobDependency.deleted_at.is_(None)
            )
        ):
            raise ResolutionError("Generation dependency mismatch")
        return takes

    def _read(self, job_id, take_ids):
        with Session(self.engine, expire_on_commit=False) as session:
            old = session.get(Job, job_id)
            if old is None:
                raise ResolutionError("Original job absent")
            takes = self._selection(session, old, take_ids)
            return old, takes

    def _claim(self, old, source, take_ids):
        with Session(self.engine) as session, session.begin():
            writer(session)
            current = session.get(Job, old.id)
            if current is None or snapshot(current) != source:
                raise ResolutionError("Original job changed during manual retry")
            # Otra conexión puede haber reclamado ya todas o algunas filas.
            remaining = list(
                session.scalars(
                    select(Take.id).where(
                        Take.id.in_(take_ids),
                        Take.job_id == current.id,
                        Take.status == "failed",
                        Take.owner_id == self.owner_id,
                        Take.song_id == current.song_id,
                        Take.deleted_at.is_(None),
                    )
                )
            )
            if not remaining:
                return None
            if set(remaining) != set(take_ids):
                raise ResolutionError("Concurrent partial take claim")
            takes = self._selection(session, current, take_ids)
            job = Job(
                id=new_id(),
                owner_id=self.owner_id,
                song_id=current.song_id,
                task=current.task,
                lane="gpu",
                priority=current.priority,
                not_before=current.not_before,
                model_id=current.model_id,
                engine_id=current.engine_id,
                request=deepcopy(current.request),
                status="queued",
                attempt=0,
                max_attempts=3,
            )
            session.add(job)
            session.flush()
            for take in takes:
                take.status, take.job_id = "queued", job.id
            session.flush()
            return add_dependents(session, job, takes)
