"""Nuevo job lógico, request idéntica; sólo takes failed del job original."""

import asyncio
from copy import deepcopy

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Job,
    JobAttempt,
    JobDependency,
    LineageEdge,
    PublicationIntent,
    PublicationIntentRevision,
    Take,
    new_id,
)

from .admission import writer
from .chains import add_dependents, live_song, validate_lyrics, validate_request
from .inputs import ResolutionError
from .resolver import snapshot


class ManualRetry:
    def __init__(self, engine, owner_id, resolver):
        self.engine, self.owner_id, self.resolver = engine, owner_id, resolver

    def _claimed_parents(self, old):
        return (
            select(LineageEdge.parent_id)
            .join(Take, Take.id == LineageEdge.child_id)
            .where(
                LineageEdge.owner_id == self.owner_id,
                LineageEdge.parent_type == "take",
                LineageEdge.child_type == "take",
                LineageEdge.role == "retry",
                LineageEdge.deleted_at.is_(None),
                Take.owner_id == self.owner_id,
                Take.song_id == old.song_id,
            )
        )

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
                    or_(
                        and_(Job.status == "failed", Job.error_code.is_not(None)),
                        and_(Job.status == "succeeded", Job.error_code.is_(None)),
                    ),
                    Job.deleted_at.is_(None),
                    Job.cancel_requested_at.is_(None),
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
                or post.status == "failed"
                and not post.error_code
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
                    if post.status == "succeeded":
                        # A completed batch can contain TakeFailure. Authenticate
                        # its active durable revision, never caller-supplied DTOs
                        # or an obsolete failure from an earlier GPU attempt.
                        bound = session.scalars(
                            select(PublicationIntent.output_index)
                            .join(
                                PublicationIntentRevision,
                                PublicationIntentRevision.id
                                == PublicationIntent.active_revision_id,
                            )
                            .join(Take, Take.id == PublicationIntent.take_id)
                            .join(
                                JobAttempt,
                                JobAttempt.id
                                == PublicationIntentRevision.winning_attempt_id,
                            )
                            .where(
                                PublicationIntent.owner_id == self.owner_id,
                                PublicationIntent.song_id == old.song_id,
                                PublicationIntent.deleted_at.is_(None),
                                PublicationIntent.state == "failed",
                                PublicationIntent.error_code.is_not(None),
                                PublicationIntent.error_code != "",
                                PublicationIntentRevision.intent_id
                                == PublicationIntent.id,
                                PublicationIntentRevision.owner_id == self.owner_id,
                                PublicationIntentRevision.song_id == old.song_id,
                                PublicationIntentRevision.deleted_at.is_(None),
                                PublicationIntentRevision.post_job_id == post.id,
                                PublicationIntentRevision.generation_job_id == old.id,
                                PublicationIntentRevision.winning_ordinal
                                == old.attempt,
                                PublicationIntentRevision.take_id == Take.id,
                                PublicationIntentRevision.output_index
                                == Take.variant_index,
                                PublicationIntentRevision.output_index
                                == PublicationIntent.output_index,
                                PublicationIntentRevision.error_code
                                == PublicationIntent.error_code,
                                JobAttempt.job_id == old.id,
                                JobAttempt.ordinal == old.attempt,
                                Take.job_id == old.id,
                                Take.status == "failed",
                                Take.owner_id == self.owner_id,
                                Take.song_id == old.song_id,
                                Take.deleted_at.is_(None),
                                Take.error_code == PublicationIntent.error_code,
                                Take.variant_index.in_(bound),
                            )
                        )
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
            Take.id.not_in(self._claimed_parents(old)),
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
                        Take.id.not_in(self._claimed_parents(current)),
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
            retry_takes = []
            batch_id = new_id()
            for take in takes:
                if session.scalar(
                    select(PublicationIntent.id).where(
                        PublicationIntent.take_id == take.id
                    )
                ):
                    child_id = new_id()
                    child = Take(
                        id=child_id,
                        owner_id=self.owner_id,
                        song_id=take.song_id,
                        job_id=job.id,
                        lyrics_version_id=take.lyrics_version_id,
                        status="queued",
                        batch_id=batch_id,
                        variant_index=take.variant_index,
                        root_id=child_id,
                        derivation="variant",
                        task=take.task,
                        model_id=take.model_id,
                        model_version=take.model_version,
                        seed=take.seed,
                        params=deepcopy(take.params),
                        commercial_use=take.commercial_use,
                    )
                    session.add(child)
                    session.flush()
                    session.add(
                        LineageEdge(
                            owner_id=self.owner_id,
                            child_type="take",
                            child_id=child.id,
                            parent_type="take",
                            parent_id=take.id,
                            role="retry",
                        )
                    )
                    # The canonical-root trigger assigns the inherited root
                    # once the edge exists; a bare new take must root at itself.
                    session.flush()
                    session.refresh(child)
                    retry_takes.append(child)
                else:
                    take.status, take.job_id = "queued", job.id
                    retry_takes.append(take)
            session.flush()
            return add_dependents(session, job, retry_takes)
