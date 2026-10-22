"""Efectos y cursor atómicos; buffer efímero publicado tras el commit."""

import asyncio
from collections import deque
from copy import deepcopy
from threading import RLock
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.migrations.job_attempt_invariants import validate_contract
from app.models import Analysis, Job, JobAttempt, Song, Take, User, new_id, utc_now
from app.publication import (
    CommitPublication,
    PublicationCoordinator,
    _confirmed_rollback,
)
from app.sse import (
    MAX_SAFE_INTEGER,
    PUBLIC_TYPES,
    CertifiedPublication,
    PublicPayloadError,
    PublicRecord,
    ResetPlan,
    StreamClosed,
    TrustedFeedScope,
    TrustedScope,
    bounded_json,
    certify_publication,
    parse_cursor,
    scope_matches,
    validate_certification,
    validate_record,
)

from .admission import writer


class EventBus:
    def __init__(self, capacity: int = 256) -> None:
        if capacity < 1:
            raise ValueError("Positive bus capacity required")
        self.buffer = deque(maxlen=capacity)
        self._ring = deque(maxlen=capacity)
        self._lock = RLock()
        self._epoch = uuid4().hex
        self._seq = 1  # Reservado para bootstrap futuro; ningún ID cero.
        self._subscribers = set()
        self._notifications = set()
        self._shutdown = False

    @property
    def epoch(self) -> str:
        with self._lock:
            return self._epoch

    @property
    def cursor(self) -> str:
        with self._lock:
            return f"{self._epoch}:{self._seq}"

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def subscribe(
        self, scope: TrustedScope | TrustedFeedScope, cursor: str | None = None
    ) -> "Subscription":
        if not isinstance(scope, TrustedScope) and type(scope) is not TrustedFeedScope:
            raise PublicPayloadError("INVALID_SCOPE")
        parsed = parse_cursor(cursor) if cursor is not None else None
        loop = asyncio.get_running_loop()
        with self._lock:
            if self._shutdown:
                raise StreamClosed("shutdown")
            if len(self._subscribers | self._notifications) >= 32:
                raise StreamClosed("limit")
            reason = None
            if parsed is None:
                reason = "bootstrap"
            elif parsed.epoch != self._epoch:
                reason = "epoch"
            elif parsed.seq > self._seq:
                reason = "ahead"
            elif parsed.seq < (self._ring[0].seq - 1 if self._ring else self._seq):
                reason = "expired"
            sub = Subscription(self, scope, loop)
            sub.reset = ResetPlan(reason, self.cursor) if reason else None
            if not reason:
                sub._replay.extend(
                    record
                    for record in self._ring
                    if record.seq > parsed.seq and scope_matches(scope, record)
                )
            self._subscribers.add(sub)
            return sub

    def mark_gap(self) -> None:
        """Vía independiente de publish; barrera aftercommit aún pendiente."""
        with self._lock:
            self._epoch, self._seq = uuid4().hex, 1
            self._ring.clear()
            for sub in tuple(self._subscribers):
                sub._close_locked("gap")

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True
            for sub in tuple(self._subscribers):
                sub._close_locked("shutdown")

    def publish(self, envelope: dict[str, Any] | CertifiedPublication) -> None:
        """Compatibilidad legacy: mismos efectos y retorno None."""
        self.publish_confirmed(envelope)

    def publish_confirmed(
        self, envelope: dict[str, Any] | CertifiedPublication
    ) -> bool:
        """Confirma exclusivamente la aceptación de este evento bajo el lock."""
        authority = None
        certified = type(envelope) is CertifiedPublication
        if certified:
            authority = envelope.authority
            envelope = envelope.envelope
        with self._lock:
            # Buffer interno intacto y por referencia, como antes.
            self.buffer.append(envelope)
            if self._shutdown:
                return False
            try:
                bounded_json(envelope)
                if type(envelope) is not dict:
                    raise PublicPayloadError()
                kind = envelope.get("type")
                if type(kind) is not str or kind not in PUBLIC_TYPES | {"job.error"}:
                    raise PublicPayloadError("INVALID_EVENT_TYPE")
                owned = deepcopy(envelope)
                if self._seq == MAX_SAFE_INTEGER:
                    self.mark_gap()
                record = PublicRecord(self._epoch, self._seq + 1, owned, authority)
                validate_record(record)
                if certified:
                    validate_certification(record)
            except (PublicPayloadError, TypeError, KeyError):
                # No fabrica un terminal engine failed tras el commit.
                self.mark_gap()
                return False
            self._seq += 1
            self._ring.append(record)
            for sub in tuple(self._subscribers):
                if scope_matches(sub.scope, record):
                    if len(sub._pending) >= 64:
                        sub._close_locked("overflow")
                    else:
                        sub._pending.append(record)
                        sub._wake_locked()
            return True


class Subscription:
    """Un lector async; publicación nativa y notificación coalescida."""

    def __init__(self, bus, scope, loop):
        self.bus, self.scope, self._loop = bus, scope, loop
        self.reset = None
        self._replay, self._pending = deque(), deque()
        self._event = asyncio.Event()
        self._closed = None
        self._waiting = self._scheduled = self._reading = False

    def _wake_locked(self):
        if not self._waiting or self._scheduled:
            return
        self._scheduled = True
        self.bus._notifications.add(self)
        try:
            self._loop.call_soon_threadsafe(self._notify)
        except RuntimeError:
            self._scheduled = False
            self.bus._notifications.discard(self)
            self._waiting = False
            self._close_locked("loop_closed")

    def _notify(self):
        with self.bus._lock:
            self._scheduled = False
            self.bus._notifications.discard(self)
            self._event.set()

    def _close_locked(self, reason):
        if self._closed is not None:
            return
        self._closed = reason
        self._replay.clear()
        self._pending.clear()
        self.bus._subscribers.discard(self)
        self._wake_locked()

    def close(self):
        with self.bus._lock:
            self._close_locked("closed")

    async def next(self):
        if asyncio.get_running_loop() is not self._loop:
            raise StreamClosed("loop_mismatch")
        with self.bus._lock:
            if self._reading:
                raise StreamClosed("concurrent_reader")
            self._reading = True
        try:
            while True:
                with self.bus._lock:
                    if self._closed is not None:
                        raise StreamClosed(self._closed)
                    queue = self._replay if self._replay else self._pending
                    if queue:
                        record = queue.popleft()
                        return PublicRecord(
                            record.epoch,
                            record.seq,
                            deepcopy(record.envelope),
                            record.authority,
                        )
                    self._event.clear()
                    self._waiting = True
                await self._event.wait()
                with self.bus._lock:
                    self._waiting = False
        except asyncio.CancelledError:
            self.close()
            raise
        finally:
            with self.bus._lock:
                self._waiting = self._reading = False


class EventConsumer:
    def __init__(self, engine, owner_id, bus, *, coordinator=None):
        self.engine, self.owner_id, self.bus = engine, owner_id, bus
        self.coordinator = coordinator
        if coordinator is not None and type(coordinator) is not PublicationCoordinator:
            raise TypeError("Explicit shared PublicationCoordinator required")

    def accept(self, attempt_id, engine_id, value):
        event = validate_contract(value, "event")
        # Serialización de entrada fuera de la futura barrera compartida.
        stamp = event.model_dump(mode="json")["ts"]
        if self.coordinator is not None:
            return self.coordinator.commit_and_publish(
                lambda: self._commit_coordinated(attempt_id, engine_id, event, stamp),
                self.bus,
            ).value
        # Compatibilidad legacy: conserva su propagación histórica de publish.
        batch = self._commit(attempt_id, engine_id, event, stamp)
        for envelope in batch.publications:
            self.bus.publish(envelope)
        return batch.value

    def _commit(self, attempt_id, engine_id, event, stamp):
        with Session(self.engine) as session, session.begin():
            batch = self._prepare_batch(session, attempt_id, engine_id, event, stamp)
        return batch

    @staticmethod
    def _rollback_and_close(session, transaction, primary):
        """Limpieza real; secundarios separados sin sustituir el primario."""
        confirmed = True
        for label, cleanup in (
            (
                "rollback",
                transaction.rollback if transaction is not None else session.rollback,
            ),
            ("close", session.close),
        ):
            try:
                cleanup()
            except BaseException as secondary:  # noqa: BLE001 -- limpieza incierta
                confirmed = False
                errors = getattr(primary, "_publication_secondary_errors", ())
                primary._publication_secondary_errors = (*errors, (label, secondary))
                primary.add_note(
                    f"Secondary {label} failure during transaction cleanup"
                )
        return confirmed

    def _commit_coordinated(self, attempt_id, engine_id, event, stamp):
        session = Session(self.engine)
        try:
            transaction = session.begin()
        except BaseException as primary:  # begin incierto, incluso interrupción
            self._rollback_and_close(session, None, primary)
            raise
        try:
            batch = self._prepare_batch(session, attempt_id, engine_id, event, stamp)
        except BaseException as primary:  # frontera precommit explícita
            traceback = primary.__traceback__
            if self._rollback_and_close(session, transaction, primary):
                return _confirmed_rollback(primary, traceback)
            raise
        # Entrar a commit destruye la posibilidad de certificar rollback unchanged.
        try:
            transaction.commit()
        except BaseException as primary:  # puede haber persistido
            self._rollback_and_close(session, transaction, primary)
            raise
        session.close()
        return batch

    @staticmethod
    def _persist_analysis(session, job, event):
        """Persist the domain result after a successful analysis terminal."""
        if job.task != "audio.beats" or event.type != "done" or job.cancel_requested_at:
            return
        result = event.data.get("result") or {}
        if (
            not isinstance(result, dict)
            or result.get("task") != "audio.beats"
            or not isinstance(result.get("analysis"), dict)
            or not isinstance(result.get("stages"), list)
            or len(result["stages"]) != 1
        ):
            raise ValueError("ANALYSIS_RESULT_INVALID")
        stage = result["stages"][0]
        if (
            not isinstance(stage, dict)
            or stage.get("task") != "audio.beats"
            or not isinstance(stage.get("model_id"), str)
            or not stage["model_id"]
            or not isinstance(stage.get("revision"), str)
            or not stage["revision"]
        ):
            raise ValueError("ANALYSIS_RESULT_INVALID")
        inputs = job.request.get("inputs", [])
        references = [
            item.get("ref")
            for item in inputs
            if isinstance(item, dict)
            and item.get("role") == "master"
            and isinstance(item.get("ref"), dict)
        ]
        if len(references) != 1 or references[0].get("type") != "take":
            raise ValueError("ANALYSIS_INPUT_INVALID")
        take = session.get(Take, references[0].get("id"))
        if not (
            take
            and take.owner_id == job.owner_id
            and take.song_id == job.song_id
            and take.status == "ready"
            and not take.deleted_at
        ):
            raise ValueError("ANALYSIS_INPUT_INVALID")
        bounded_json(result["analysis"])
        stamp = utc_now()
        current = session.scalar(
            select(Analysis).where(
                Analysis.take_id == take.id,
                Analysis.kind == "beats",
                Analysis.analyzer_id == stage["model_id"],
                Analysis.deleted_at.is_(None),
            )
        )
        if current is None:
            session.add(
                Analysis(
                    id=new_id(),
                    owner_id=job.owner_id,
                    take_id=take.id,
                    kind="beats",
                    analyzer_id=stage["model_id"],
                    analyzer_version=stage["revision"],
                    lyrics_version_id=take.lyrics_version_id,
                    data=result["analysis"],
                    created_at=stamp,
                    updated_at=stamp,
                )
            )
        else:
            current.analyzer_version = stage["revision"]
            current.lyrics_version_id = take.lyrics_version_id
            current.data = result["analysis"]
            current.updated_at = stamp

    def _prepare_batch(self, session, attempt_id, engine_id, event, stamp):
        writer(session)
        attempt = session.get(JobAttempt, attempt_id)
        job = session.get(Job, attempt.job_id) if attempt else None
        song = session.get(Song, job.song_id) if job else None
        user = session.get(User, self.owner_id)
        if not (
            job
            and attempt
            and song
            and user
            and user.name == "local"
            and not user.deleted_at
            and not song.deleted_at
            and not song.is_dependency_only
            and not job.deleted_at
            and not attempt.deleted_at
            and job.owner_id == attempt.owner_id == song.owner_id == self.owner_id
            and job.attempt == attempt.ordinal
            and job.engine_id == attempt.engine_id == engine_id
            and event.job_id == attempt_id
        ):
            raise ValueError("Event ownership mismatch")
        if event.seq <= attempt.last_seq:
            if (
                event.type in {"done", "error", "cancelled"}
                and event != attempt.terminal
            ):
                raise ValueError("Contradictory terminal replay")
            if (
                attempt.terminal is not None
                and event.seq == attempt.last_seq
                and event != attempt.terminal
            ):
                raise ValueError("Contradictory terminal replay")
            return CommitPublication(False, ())
        if attempt.terminal is not None or event.seq != attempt.last_seq + 1:
            raise ValueError("Event sequence or terminal contradiction")
        if job.status not in {"running", "interrupted"}:
            raise ValueError("Inactive logical job")
        if event.type == "stage":
            job.stage = event.data["stage"]
        elif event.type == "progress":
            job.progress = event.data["fraction"]
        elif event.type in {"done", "error", "cancelled"}:
            status = {
                "done": "succeeded",
                "error": "failed",
                "cancelled": "cancelled",
            }[event.type]
            attempt.status, attempt.terminal = status, event
            job.status = "cancelled" if job.cancel_requested_at else status
            job.finished_at = stamp
            if event.type == "error":
                job.error_code, job.error = (
                    event.data["code"],
                    event.data["message"],
                )
            else:
                job.telemetry = event.data["telemetry"]
        attempt.last_seq, attempt.updated_at = event.seq, stamp
        job.updated_at = stamp
        self._persist_analysis(session, job, event)
        notification = (
            "cancelled"
            if event.type == "done" and job.cancel_requested_at
            else event.type
        )
        envelope = {
            "job_id": job.id,
            "attempt_id": attempt.id,
            "type": "job." + notification,
            "ts": stamp,
            "data": {"status": job.status, **event.data},
        }
        # Sólo estas filas reales dan autoridad; nunca campos del engine.
        publication = envelope
        if notification != "delta":
            try:
                publication = certify_publication(
                    envelope, owner_id=job.owner_id, song_id=song.id
                )
            except PublicPayloadError:
                # Evento engine válido sin proyección pública válida: no
                # revertir la transacción. publish legacy invalida el epoch.
                # delta no participa del feed, aunque su forma sea pública.
                pass
        batch = CommitPublication(True, (publication,))
        return batch
