"""Writer antes de decisiones; selección por lotes y reserva inicial durable."""

import json
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone

from engine_contract import JobRequest, LoadRequest
from sqlalchemy import case, func, or_, select, text, tuple_, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, JobDependency, Song, User, new_id
from app.worker.contracts import CapturedProvenance, canonical_sha256

from .inputs import ResolutionError, stage_inputs
from .provenance import MUSIC_TASKS, SelectedProvenance, reported_digest
from .resolver import snapshot, snapshot_values


def writer(session):
    session.execute(text("UPDATE snapshot_clock SET revision=revision WHERE id=1"))


class PreclaimResolutionError(ResolutionError):
    """Entrada rechazada antes de cualquier escritura de job/intento."""


def occupancy_filters(owner_id):
    """Return the shared durable reservation predicates for a local owner."""
    active = Job.status.in_(["running", "interrupted"])
    active_attempt = (
        select(JobAttempt.id)
        .where(
            JobAttempt.job_id == Job.id,
            JobAttempt.ordinal == Job.attempt,
            JobAttempt.owner_id == owner_id,
            JobAttempt.terminal.is_(None),
            JobAttempt.deleted_at.is_(None),
        )
        .exists()
    )
    support_job = (
        select(Song.id)
        .where(
            Song.id == Job.song_id,
            Song.owner_id == owner_id,
            Song.deleted_at.is_(None),
            Song.is_dependency_only.is_(True),
        )
        .exists()
    )
    occupied = or_(
        Job.status == "running",
        active_attempt,
        support_job,
        (Job.status == "interrupted") & (Job.lane == "gpu"),
    )
    return active, occupied, Job.owner_id == owner_id, Job.deleted_at.is_(None)


@dataclass(frozen=True)
class Claim:
    job_id: str
    attempt_id: str
    request: JobRequest
    load_options: LoadRequest
    selected_provenance: "SelectedProvenance | None" = None


class Admission:
    def __init__(
        self,
        engine,
        owner_id,
        *,
        clock=lambda: datetime.now(timezone.utc),
        nightly_window="01:00-07:00",
        synthetic_registry=None,
    ):
        self.engine, self.owner_id, self.clock = engine, owner_id, clock
        self.nightly_window = nightly_window
        from .synthetic_registry import SyntheticRegistry

        self.synthetic_registry = (
            synthetic_registry
            if synthetic_registry is not None
            else SyntheticRegistry()
        )

    def _now(self):
        now = self.clock()
        if now.utcoffset() is None or now.utcoffset().total_seconds() != 0:
            raise ValueError("UTC admission clock required")
        return now

    def _query(self):
        return (
            select(Job)
            .join(Song, Song.id == Job.song_id)
            .join(User, User.id == Job.owner_id)
            .where(
                Job.id.in_(select(text("id")).select_from(text("dispatchable_job"))),
                Job.owner_id == self.owner_id,
                User.name == "local",
                User.deleted_at.is_(None),
                Song.owner_id == self.owner_id,
                Song.deleted_at.is_(None),
                Song.is_dependency_only.is_(False),
                Job.deleted_at.is_(None),
                Job.cancel_requested_at.is_(None),
                Job.status.in_(["queued", "blocked"]),
                Job.lane.in_(["gpu", "cpu"]),
            )
        )

    @staticmethod
    def _dependency_map(session, jobs):
        result = {job.id: [] for job in jobs}
        ids = list(result)
        for start in range(0, len(ids), 400):
            rows = session.execute(
                select(
                    JobDependency.job_id,
                    Job.status,
                    Job.owner_id,
                    Job.deleted_at,
                    Job.song_id,
                    JobDependency.owner_id.label("edge_owner"),
                )
                .join(Job, Job.id == JobDependency.depends_on_job_id)
                .where(
                    JobDependency.job_id.in_(ids[start : start + 400]),
                    JobDependency.deleted_at.is_(None),
                )
            )
            for row in rows:
                result[row.job_id].append(row)
        return result

    def _dependencies(self, job, parents, now, session=None, *, window=None):
        owned = all(
            p.owner_id == self.owner_id
            and p.edge_owner == self.owner_id
            and p.song_id == job.song_id
            and not p.deleted_at
            for p in parents
        )
        if owned and any(p.status in {"failed", "cancelled"} for p in parents):
            job.status, job.error_code = "failed", "DEPENDENCY_FAILED"
            job.error = "Una dependencia ha terminado sin éxito"
            job.finished_at = now.isoformat().replace("+00:00", "Z")
        elif not owned or any(p.status != "succeeded" for p in parents):
            job.status = "blocked"
        elif (
            job.status == "blocked"
            and session is not None
            and job.request.get("inputs")
        ):
            from .references import references_available

            if references_available(job, session, window=window):
                job.status = "queued"

    def _eligible(self, job, parents, now):
        if job.status != "queued" or job.attempt != 0 or not 1 <= job.max_attempts <= 3:
            return False
        if job.not_before and datetime.fromisoformat(job.not_before) > now:
            return False
        if job.priority == "nightly":
            start, end = self.nightly_window.split("-")
            time = now.strftime("%H:%M")
            inside = start <= time < end if start < end else time >= start or time < end
            if not inside:
                return False
        return all(
            p.status == "succeeded" and p.owner_id == self.owner_id and not p.deleted_at
            for p in parents
        )

    @staticmethod
    def _order(job):
        return (
            {"interactive": 0, "normal": 1, "batch": 2, "nightly": 3}[job.priority],
            datetime.fromisoformat(job.created_at),
            job.id,
        )

    def candidates(self, job_id=None, *, limit=None):
        if limit is not None:
            pages = self.candidate_batches(job_id, size=limit)
            try:
                return next((page for page in pages if page), [])
            finally:
                pages.close()
        with Session(self.engine, expire_on_commit=False) as session, session.begin():
            writer(session)
            now = self._now()
            query = self._query()
            if job_id is not None:
                query = query.where(Job.id == job_id)
            jobs = list(session.scalars(query))
            parents = self._dependency_map(session, jobs)
            chosen = []
            from .references import preload_references

            ordered = sorted(jobs, key=self._order)
            for start in range(0, len(ordered), 400):
                batch = ordered[start : start + 400]
                window = preload_references(session, batch)
                for job in batch:
                    self._dependencies(
                        job, parents[job.id], now, session, window=window
                    )
                    if self._eligible(job, parents[job.id], now):
                        chosen.append(job)
            session.flush()
            for job in chosen:
                session.expunge(job)
            return chosen

    def candidate_batches(self, job_id=None, *, size=400, reader=None):
        """Snapshot de lectura finito; writer y objetos limitados a cada página.

        El snapshot WAL excluye inserciones posteriores, incluso con fechas antiguas.
        La reserva sigue siendo autoridad sobre el estado actual, no esta lectura.
        """
        if not 1 <= size <= 400:
            raise ValueError("Candidate page must contain 1..400 jobs")
        priority = case(
            {"interactive": 0, "normal": 1, "batch": 2, "nightly": 3},
            value=Job.priority,
        )
        # julianday redondea fracciones: claves textuales UTC a microsegundos.
        stamp = func.replace(func.replace(Job.created_at, "Z", ""), "+00:00", "")
        seconds = func.replace(func.substr(stamp, 1, 19), " ", "T")
        fraction = case(
            (
                func.substr(stamp, 20, 1) == ".",
                func.substr(func.substr(stamp, 21) + "000000", 1, 6),
            ),
            else_="000000",
        )
        order = (priority, seconds, fraction, Job.id)
        cursor = None
        now = self._now()
        context = Session(self.engine) if reader is None else nullcontext(reader)
        with (
            context as snapshot_reader,
            snapshot_reader.begin()
            if not snapshot_reader.in_transaction()
            else nullcontext(),
        ):
            query = self._query()
            if job_id is not None:
                query = query.where(Job.id == job_id)
            while True:
                page_query = query
                if cursor is not None:
                    page_query = page_query.where(tuple_(*order) > cursor)
                projected = not (
                    snapshot_reader.identity_map
                    or snapshot_reader.new
                    or snapshot_reader.dirty
                    or snapshot_reader.deleted
                )
                if projected:
                    # Atributos mapeados: mismos procesadores y autoflush ORM.
                    # Todas las columnas, incluida telemetry, se consumen al listar.
                    columns = tuple(
                        getattr(Job, attribute.key)
                        for attribute in Job.__mapper__.column_attrs
                    )
                    page_query = page_query.with_only_columns(
                        *columns, maintain_column_froms=True
                    )
                    cursor_columns = tuple(
                        value.label(f"snapshot_cursor_{index}")
                        for index, value in enumerate(order)
                    )
                else:
                    cursor_columns = order
                page = list(
                    snapshot_reader.execute(
                        page_query.add_columns(*cursor_columns)
                        .order_by(*order)
                        .limit(size)
                    )
                )
                if not page:
                    return
                if projected:
                    cursor = tuple(page[-1][len(columns) :])
                    sources = {
                        row._mapping["id"]: snapshot_values(row._mapping)
                        for row in page
                    }
                else:
                    cursor = tuple(page[-1][1:])
                    sources = {row[0].id: snapshot(row[0]) for row in page}
                    # Solo esta página: retries comparte el identity map.
                    for row in page:
                        snapshot_reader.expunge(row[0])
                with (
                    Session(self.engine, expire_on_commit=False) as session,
                    session.begin(),
                ):
                    writer(session)
                    current = list(
                        session.scalars(self._query().where(Job.id.in_(sources)))
                    )
                    parents = self._dependency_map(session, current)
                    from .references import preload_references

                    window = preload_references(session, current)
                    chosen = []
                    for job in sorted(current, key=self._order):
                        if snapshot(job) != sources[job.id]:
                            continue
                        self._dependencies(
                            job, parents[job.id], now, session, window=window
                        )
                        if self._eligible(job, parents[job.id], now):
                            chosen.append(job)
                    session.flush()
                    for job in chosen:
                        session.expunge(job)
                yield chosen
                if len(page) < size:
                    return

    def select(self, job_id=None):
        candidates = self.candidates(job_id)
        return candidates[0] if candidates else None

    def reserve(self, resolved):
        # Copia y SHA completos antes de adquirir writer; el llamador async usa to_thread.
        body = json.loads(resolved.payload)
        selected = resolved.selected_provenance
        if selected is not None:
            request, load = resolved.freeze(resolved.job_id)
            if (
                not selected.authorized(self.synthetic_registry)
                or not selected.binds(request, load)
                or selected.engine_id != resolved.engine_id
            ):
                raise PreclaimResolutionError("Selected provenance mismatch")
        try:
            from .references import check_job_references

            with Session(self.engine) as reader:
                source = reader.get(Job, resolved.job_id)
                if source is None:
                    return None
                if (
                    check_job_references(self.engine, source, resolved.data_dir)
                    != body["inputs"]
                ):
                    raise ResolutionError("Resolved reference changed")
            staged = stage_inputs(resolved.data_dir, body["inputs"])
        except ResolutionError as exc:
            raise PreclaimResolutionError(str(exc)) from exc
        durable = False
        aid = None
        try:
            with Session(self.engine) as session, session.begin():
                writer(session)
                now = self._now()
                job = session.scalar(self._query().where(Job.id == resolved.job_id))
                if (
                    job is None
                    or resolved.owner_id != self.owner_id
                    or snapshot(job) != resolved.source
                ):
                    return None
                parents = self._dependency_map(session, [job])[job.id]
                self._dependencies(job, parents, now, session)
                if not self._eligible(job, parents, now):
                    return None
                # ``interrupted`` is an uncertain reservation. It must count
                # for support jobs even when recovery stopped before an
                # attempt row was written. A running row is itself a live
                # reservation; an interrupted normal orphan is historical
                # residue and is excluded until recovery has an attempt.
                active, occupied, owned, live = occupancy_filters(self.owner_id)
                active_rows = (
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.lane == resolved.lane,
                        active,
                        occupied,
                        owned,
                        live,
                    )
                )
                count = session.scalar(active_rows)
                if count >= {"gpu": 1, "cpu": 2}[resolved.lane]:
                    return None
                if resolved.lane == "gpu" and session.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.engine_id == resolved.engine_id,
                        active,
                        occupied,
                        owned,
                        live,
                    )
                ):
                    return None
                # Sólo estos rechazos son conocidos preclaim; commit/probe/cleanup
                # no se reclasifican, aunque también arrojen ResolutionError.
                try:
                    from .references import resolve_references

                    if (
                        resolve_references(
                            job, session, resolved.data_dir, verify=False
                        )
                        != body["inputs"]
                    ):
                        raise ResolutionError("Input changed during admission")
                    staged.check()
                except ResolutionError as exc:
                    raise PreclaimResolutionError(str(exc)) from exc
                if (
                    session.scalar(
                        select(JobAttempt.id).where(JobAttempt.job_id == job.id)
                    )
                    is not None
                ):
                    return None
                aid = new_id()
                body.update(job_id=aid, output_dir="tmp/" + aid, inputs=staged.wires)
                from app.migrations.job_attempt_invariants import validate_contract

                request = validate_contract(body, "request")
                options = validate_contract(
                    {"model_id": resolved.model_id, "mode": resolved.mode}, "load"
                )
                stamp = now.isoformat(timespec="microseconds").replace("+00:00", "Z")
                changed = session.execute(
                    update(Job)
                    .where(
                        Job.id == job.id,
                        Job.status == "queued",
                        Job.attempt == 0,
                        Job.cancel_requested_at.is_(None),
                    )
                    .values(
                        status="running",
                        lane=resolved.lane,
                        attempt=1,
                        engine_id=resolved.engine_id,
                        model_id=resolved.model_id,
                        started_at=stamp,
                        updated_at=stamp,
                    )
                ).rowcount
                if changed != 1:
                    return None
                session.add(
                    JobAttempt(
                        id=aid,
                        owner_id=self.owner_id,
                        job_id=job.id,
                        ordinal=1,
                        engine_id=resolved.engine_id,
                        model_id=resolved.model_id,
                        mode=resolved.mode,
                        engine_request=request,
                        load_options=options,
                        created_at=stamp,
                        updated_at=stamp,
                    )
                )
                session.flush()
                claim = Claim(job.id, aid, request, options, selected)
            durable = True
            return claim
        finally:
            if not durable and aid is not None:
                # Un fallo al observar commit no demuestra rollback; lectura independiente.
                try:
                    with Session(self.engine) as check:
                        durable = check.get(JobAttempt, aid) is not None
                except SQLAlchemyError:
                    durable = True
            if not durable:
                staged.cleanup()

    def _send_authority(self, session, claim, *, allow_submitted=False):
        job = session.get(Job, claim.job_id)
        attempt = session.get(JobAttempt, claim.attempt_id)
        song = session.get(Song, job.song_id) if job else None
        owner = session.get(User, self.owner_id)
        valid = bool(
            job
            and attempt
            and song
            and owner
            and owner.name == "local"
            and not owner.deleted_at
            and job.owner_id == self.owner_id
            and song.owner_id == self.owner_id
            and not song.deleted_at
            and not song.is_dependency_only
            and not job.deleted_at
            and not job.cancel_requested_at
            and job.status
            in ({"running", "interrupted"} if allow_submitted else {"running"})
            and job.attempt == attempt.ordinal
            and attempt.status
            in ({"prepared", "submitted"} if allow_submitted else {"prepared"})
            and attempt.owner_id == self.owner_id
            and attempt.job_id == job.id
            and not attempt.deleted_at
            and attempt.terminal is None
            and attempt.last_seq == 0
            and attempt.engine_request == claim.request
            and attempt.load_options == claim.load_options
            and job.engine_id == attempt.engine_id
            and job.model_id == attempt.model_id
            and job.task == claim.request.task
        )
        return attempt if valid else None

    def may_prepare_send(self, claim):
        """Autoridad previa a observación/captura; no habilita submit."""
        with Session(self.engine) as session:
            return self._send_authority(session, claim) is not None

    def _bound_capture(self, claim, value):
        selected = claim.selected_provenance
        return bool(
            selected is not None
            and selected.authorized(self.synthetic_registry)
            and value.evidence_kind == selected.evidence_kind
            and value.synthetic_binding == selected.synthetic_binding
            and selected.binds(claim.request, claim.load_options)
            and value.descriptor == selected.descriptor
            and (
                value.engine_id,
                value.engine_version,
                value.contract_version,
                value.task,
                value.load,
            )
            == (
                selected.engine_id,
                selected.engine_version,
                selected.contract_version,
                selected.task,
                selected.load,
            )
            and value.expected_image_digest == selected.expected_image_digest
            and value.reported_image_digest
            == reported_digest(json.loads(selected.resolve_health_json)["image_digest"])
        )

    def capture_provenance(
        self, claim, provenance, provenance_sha256, *, allow_submitted=False
    ):
        """CAS nullable write-once; SHA y validación antes del writer SQLite."""
        try:
            value = CapturedProvenance.model_validate_json(provenance.model_dump_json())
            if canonical_sha256(value) != provenance_sha256 or not self._bound_capture(
                claim, value
            ):
                return False
        except (ValueError, TypeError):
            return False
        with Session(self.engine) as session, session.begin():
            writer(session)
            if not self._bound_capture(claim, value):
                return False
            attempt = self._send_authority(
                session, claim, allow_submitted=allow_submitted
            )
            if attempt is None or attempt.engine_id != value.engine_id:
                return False
            if attempt.provenance is not None or attempt.provenance_sha256 is not None:
                return (
                    attempt.provenance == value
                    and attempt.provenance_sha256 == provenance_sha256
                )
            # La recuperación nunca crea evidencia retrospectiva.
            if allow_submitted:
                return False
            attempt.provenance, attempt.provenance_sha256 = value, provenance_sha256
            session.flush()
        return True

    def may_send(self, claim):
        with Session(self.engine) as session:
            attempt = self._send_authority(session, claim)
            if attempt is None:
                return False
            if claim.request.task not in MUSIC_TASKS:
                return attempt.provenance is None and attempt.provenance_sha256 is None
            try:
                value = CapturedProvenance.model_validate(attempt.provenance)
                return (
                    self._bound_capture(claim, value)
                    and canonical_sha256(value) == attempt.provenance_sha256
                )
            except (ValueError, TypeError):
                return False

    def acknowledge(self, claim):
        with Session(self.engine) as session, session.begin():
            writer(session)
            job, attempt = (
                session.get(Job, claim.job_id),
                session.get(JobAttempt, claim.attempt_id),
            )
            if not (
                job
                and attempt
                and job.owner_id == self.owner_id
                and job.status == "running"
                and not job.cancel_requested_at
                and not job.deleted_at
                and job.attempt == attempt.ordinal
                and attempt.status == "prepared"
            ):
                return False
            attempt.status = "submitted"
            return True

    def backend_active(self, engine_id, *, except_job=None):
        with Session(self.engine) as session:
            return bool(
                session.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.engine_id == engine_id,
                        Job.status.in_(["running", "interrupted"]),
                        Job.id != except_job,
                    )
                )
            )

    def gpu_active(self):
        with Session(self.engine) as session:
            return bool(
                session.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(
                        Job.lane == "gpu", Job.status.in_(["running", "interrupted"])
                    )
                )
            )
