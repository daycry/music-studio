"""Reserva atómica de retries confirmados desde la petición congelada."""

from contextlib import nullcontext
from datetime import datetime, timezone

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, new_id, utc_now

from .admission import Claim, occupancy_filters, writer
from .cancellation import local_jobs
from .inputs import verified_file
from .resolver import Resolver


class FrozenRetryResolver(Resolver):
    """Validación fresca del catálogo sobre bytes ya congelados, no refs de dominio."""

    def _inputs(self, job, engine):
        wires = [item.model_dump(mode="json") for item in job._frozen_retry_inputs]
        for wire in wires:
            verified_file(self.data_dir, wire)
        return wires


class Retry:
    def __init__(self, engine, owner):
        self.engine, self.owner = engine, owner

    @staticmethod
    def eligible(job, attempt):
        try:
            due = job.not_before is None or (
                isinstance(job.not_before, str)
                and datetime.fromisoformat(job.not_before) <= datetime.now(timezone.utc)
            )
        except (ValueError, TypeError):
            return False
        return bool(
            job.status == "failed"
            and not job.cancel_requested_at
            and due
            and type(job.attempt) is int
            and type(job.max_attempts) is int
            and 1 <= job.attempt < job.max_attempts <= 3
            and attempt.ordinal == job.attempt
            and attempt.status == "failed"
            and attempt.terminal is not None
            and attempt.terminal.type == "error"
            and attempt.terminal.data["retryable"] is True
        )

    def candidates(self):
        pages = self.candidate_batches()
        try:
            for page in pages:
                yield from page
        finally:
            pages.close()

    def candidate_batches(self, *, size=400, reader=None):
        """Snapshot finito y páginas acotadas; eligible y reserve son autoridad."""
        if not 1 <= size <= 400:
            raise ValueError("Retry page must contain 1..400 jobs")
        now = datetime.now(timezone.utc).isoformat()
        priority = case(
            {"interactive": 0, "normal": 1, "batch": 2, "nightly": 3},
            value=Job.priority,
        )
        # Normaliza el segundo/offset sin perder las fracciones para FIFO.
        stamp = func.replace(func.replace(Job.created_at, "Z", ""), "+00:00", "")
        second = func.replace(func.substr(stamp, 1, 19), " ", "T")
        fraction = case(
            (
                func.substr(stamp, 20, 1) == ".",
                func.substr(func.substr(stamp, 21) + "000000", 1, 6),
            ),
            else_="000000",
        )
        order = (priority, second, fraction, Job.id)
        query = (
            local_jobs(self.owner)
            .add_columns(JobAttempt)
            .join(
                JobAttempt,
                (JobAttempt.job_id == Job.id) & (JobAttempt.ordinal == Job.attempt),
            )
            .where(
                Job.status == "failed",
                Job.cancel_requested_at.is_(None),
                Job.lane.in_(["gpu", "cpu"]),
                Job.attempt >= 1,
                Job.attempt < Job.max_attempts,
                Job.max_attempts <= 3,
                JobAttempt.owner_id == self.owner,
                JobAttempt.deleted_at.is_(None),
                JobAttempt.status == "failed",
                func.json_extract(JobAttempt.terminal, "$.type") == "error",
                func.json_type(JobAttempt.terminal, "$.data.retryable") == "true",
                # SQLite redondea al milisegundo: sólo prefiltra; Python decide
                # con UTC/microsegundos exactos, incluidos offsets ya validados.
                or_(
                    Job.not_before.is_(None),
                    func.julianday(Job.not_before) <= func.julianday(now),
                ),
            )
        )
        context = (
            Session(self.engine, expire_on_commit=False)
            if reader is None
            else nullcontext(reader)
        )
        with (
            context as session,
            session.begin() if not session.in_transaction() else nullcontext(),
        ):
            rows = session.execute(
                query.order_by(*order).execution_options(yield_per=size)
            )
            try:
                for page in rows.partitions(size):
                    chosen = []
                    for job, attempt in page:
                        if self.eligible(job, attempt):
                            chosen.append((job, attempt))
                        session.expunge(job)
                        session.expunge(attempt)
                    yield chosen
            finally:
                rows.close()

    @staticmethod
    def frozen_job(job, attempt, mode):
        body = attempt.engine_request.model_dump(mode="json")
        values = {
            column.name: getattr(job, column.name) for column in Job.__table__.columns
        }
        values["request"] = {
            key: body[key] for key in ("params", "seed", "n_outputs", "timeout_s")
        }
        values["request"]["mode"] = mode
        values["engine_id"], values["model_id"] = attempt.engine_id, attempt.model_id
        values["task"] = body["task"]
        frozen = Job(**values)
        frozen._frozen_retry_inputs = attempt.engine_request.inputs
        return frozen

    def reserve(self, job_id, previous_id, resolved):
        from .recovery import Recovery

        recovery = Recovery(self.engine, self.owner, resolved.data_dir)
        current = recovery.current(previous_id)
        if current is None:
            return None
        proof = recovery.safe_inputs(current[0])
        with Session(self.engine) as session, session.begin():
            writer(session)
            job = session.scalar(local_jobs(self.owner).where(Job.id == job_id))
            previous = session.get(JobAttempt, previous_id)
            if not (
                job
                and previous
                and previous.owner_id == self.owner
                and not previous.deleted_at
                and self.eligible(job, previous)
            ):
                return None
            if (resolved.engine_id, resolved.model_id, resolved.lane) != (
                previous.engine_id,
                previous.model_id,
                job.lane,
            ):
                return None
            active, occupied, owned, live = occupancy_filters(self.owner)
            if (
                session.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(Job.lane == job.lane, active, occupied, owned, live)
                )
                >= {"gpu": 1, "cpu": 2}[job.lane]
            ):
                return None
            if session.scalar(
                select(func.count())
                .select_from(Job)
                .where(
                    Job.engine_id == previous.engine_id,
                    active,
                    occupied,
                    owned,
                    live,
                )
            ):
                return None
            if resolved.mode != previous.mode:
                if (
                    resolved.mode != "offload"
                    or previous.terminal.data["code"] != "VRAM_EXCEEDED"
                ):
                    return None
                if session.scalar(
                    select(JobAttempt.id).where(
                        JobAttempt.job_id == job.id, JobAttempt.mode == "offload"
                    )
                ):
                    return None
            proof.check()
            aid, stamp = new_id(), utc_now()
            body = previous.engine_request.model_dump(mode="json")
            body.update(job_id=aid, output_dir="tmp/" + aid, mode=resolved.mode)
            options = previous.load_options.model_dump(mode="json")
            options["mode"] = resolved.mode
            attempt = JobAttempt(
                id=aid,
                owner_id=self.owner,
                job_id=job.id,
                ordinal=job.attempt + 1,
                engine_id=previous.engine_id,
                model_id=previous.model_id,
                mode=resolved.mode,
                engine_request=body,
                load_options=options,
                created_at=stamp,
                updated_at=stamp,
            )
            session.add(attempt)
            job.attempt += 1
            job.status, job.error, job.error_code, job.finished_at = (
                "running",
                None,
                None,
                None,
            )
            job.updated_at = stamp
            session.flush()
            selected = resolved.selected_provenance
            if selected is not None and not selected.binds(
                attempt.engine_request, attempt.load_options
            ):
                raise ValueError("Retry selected request/load mismatch")
            claim = Claim(
                job.id, aid, attempt.engine_request, attempt.load_options, selected
            )
        return claim
