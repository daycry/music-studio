"""Rechazo transaccional confirmado con SQLite y lectores reales."""

import asyncio

import pytest
from app.models import Job
from app.publication import PublicationCoordinator
from app.queue.events import EventBus, EventConsumer
from app.sse import TrustedFeedScope
from sqlalchemy.orm import Session
from test_dispatcher_admission import add, admission, resolve
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414
from test_dispatcher_recovery import event, prepared


class PublicationInterruption(BaseException):
    pass


@pytest.mark.parametrize("boundary", ["callback", "publish"])
def test_coordinator_interruption_and_gap_secondary_preserve_primary(
    engine, monkeypatch, boundary
):
    from app.publication import CommitPublication

    _jid, owner, claim = prepared(engine)

    async def run():
        bus = EventBus()
        coordinator = PublicationCoordinator()
        consumer = EventConsumer(engine, owner, bus, coordinator=coordinator)
        cursor = bus.cursor
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.1}),
        )
        reader = bus.subscribe(TrustedFeedScope(owner), cursor)
        epoch = bus.epoch
        primary, secondary = KeyboardInterrupt("primary"), SystemExit("gap secondary")
        gap = bus.mark_gap

        def failed_gap():
            gap()  # Actual bus invalidation before declared secondary injection.
            raise secondary

        def interrupted(*args):
            raise primary

        monkeypatch.setattr(bus, "mark_gap", failed_gap)
        if boundary == "publish":
            monkeypatch.setattr(bus, "publish_confirmed", interrupted)
        callback = (
            interrupted
            if boundary == "callback"
            else lambda: CommitPublication("durable", ({},))
        )
        try:
            with pytest.raises(KeyboardInterrupt) as raised:
                coordinator.commit_and_publish(callback, bus)
            assert raised.value is primary
            assert bus.epoch != epoch and reader._closed == "gap"
            if boundary == "callback":
                assert ("mark_gap", secondary) in primary._publication_secondary_errors
        finally:
            reader.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "interrupt", [KeyboardInterrupt, SystemExit, PublicationInterruption]
)
@pytest.mark.parametrize(
    "boundary",
    ["prepare", "begin", "commit", "rollback", "close", "both", "constructor"],
)
def test_real_writer_interruption_cleanup(engine, monkeypatch, interrupt, boundary):
    """Declared Python boundary injection; SQL, commit, bus and reader are real."""
    import app.queue.events as events_module

    jid, owner, claim = prepared(engine)

    async def run():
        bus = EventBus()
        consumer = EventConsumer(
            engine, owner, bus, coordinator=PublicationCoordinator()
        )
        cursor = bus.cursor
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.1}),
        )
        reader = bus.subscribe(TrustedFeedScope(owner), cursor)
        before_db, before_feed = database(engine), feed(bus, (reader,))
        primary = interrupt("actual injected interruption", 17)
        secondaries = {label: interrupt(label) for label in ("rollback", "close")}
        observed, sessions, calls = [], [], []
        prepare = events_module.EventConsumer._prepare_batch

        def throw():
            try:
                raise primary
            except BaseException as error:
                observed.append(error.__traceback__)
                raise

        def injected_prepare(self, session, *args):
            batch = prepare(self, session, *args)
            session.flush()  # Actual UPDATE acquires SQLite writer before interruption.
            if boundary in {"prepare", "rollback", "close", "both"}:
                throw()
            return batch

        class InterruptedSession(Session):
            def __init__(self, *args, **kwargs):
                if boundary == "constructor":
                    throw()
                super().__init__(*args, **kwargs)
                sessions.append(self)

            def begin(self, *args, **kwargs):
                transaction = super().begin(*args, **kwargs)
                if boundary == "begin":
                    throw()
                commit, rollback = transaction.commit, transaction.rollback

                def real_commit_then_interrupt():
                    calls.append("commit")
                    commit()  # Real durable commit, never a fake successful commit.
                    throw()

                def real_rollback():
                    calls.append("rollback")
                    rollback()
                    if boundary in {"rollback", "both"}:
                        raise secondaries["rollback"]

                monkeypatch.setattr(transaction, "rollback", real_rollback)
                if boundary == "commit":
                    monkeypatch.setattr(
                        transaction, "commit", real_commit_then_interrupt
                    )
                return transaction

            def rollback(self):
                calls.append("rollback")
                return super().rollback()

            def close(self):
                calls.append("close")
                super().close()
                if boundary in {"close", "both"}:
                    raise secondaries["close"]

        monkeypatch.setattr(events_module, "Session", InterruptedSession)
        monkeypatch.setattr(
            events_module.EventConsumer, "_prepare_batch", injected_prepare
        )
        try:
            with pytest.raises(interrupt) as raised:
                consumer.accept(
                    claim.attempt_id,
                    "mock",
                    event(claim.attempt_id, "progress", {"fraction": 0.9}, seq=2),
                )
            assert raised.value is primary and primary.args == (
                "actual injected interruption",
                17,
            )
            tail = primary.__traceback__
            while tail.tb_next:
                tail = tail.tb_next
            assert tail is observed[0]  # Same held original traceback node.
            if boundary == "constructor":
                assert not sessions and not calls
            else:
                assert "close" in calls
                assert all(not session.in_transaction() for session in sessions)
                assert all(not session.identity_map for session in sessions)
            if boundary == "prepare":
                assert calls == ["rollback", "close"]
                assert database(engine) == before_db
                assert feed(bus, (reader,)) == before_feed
            else:
                assert bus.epoch != before_feed[0] and not bus._ring
                assert reader._closed == "gap"
                if boundary == "commit":
                    with Session(engine) as session:
                        assert session.get(Job, jid).progress == 0.9
                    assert database(engine) != before_db
                else:
                    assert database(engine) == before_db
                if boundary in {"rollback", "close", "both"}:
                    assert calls == ["rollback", "close"]
                    for label in ("rollback", "close"):
                        if boundary in {label, "both"}:
                            assert (
                                label,
                                secondaries[label],
                            ) in primary._publication_secondary_errors
        finally:
            for session in sessions:
                Session.close(session)
            reader.close()

    asyncio.run(run())


def database(engine):
    connection = engine.raw_connection()
    try:
        return tuple(connection.driver_connection.iterdump())
    finally:
        connection.close()


def feed(bus, subscriptions):
    return (
        bus.epoch,
        bus.cursor,
        tuple(bus._ring),
        tuple(bus.buffer),
        bus.subscriber_count,
        tuple(
            (tuple(sub._replay), tuple(sub._pending), sub._closed)
            for sub in subscriptions
        ),
    )


@pytest.mark.parametrize(
    "rejection", ["identity", "sequence", "owner", "ordinal", "terminal", "replay"]
)
def test_confirmed_rejection_preserves_database_and_all_readers(engine, rejection):
    jid, owner, claim = prepared(engine)
    other_jid, other_owner = add(
        engine,
        task="audio.beats",
        lane="cpu",
        request={"params": {}, "mode": "bf16", "seed": 3, "timeout_s": 60},
    )
    adm = admission(engine, other_owner)
    other = adm.reserve(resolve(adm.select(other_jid)))
    assert other is not None

    async def run():
        bus = EventBus()
        consumer = EventConsumer(
            engine, owner, bus, coordinator=PublicationCoordinator()
        )
        cursor = bus.cursor
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.1}),
        )
        reader = bus.subscribe(TrustedFeedScope(owner), cursor)
        other_reader = bus.subscribe(TrustedFeedScope(other_owner), cursor)
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.2}, seq=2),
        )
        other_consumer = EventConsumer(
            engine, other_owner, bus, coordinator=consumer.coordinator
        )
        assert other_consumer.accept(
            other.attempt_id,
            "mock",
            event(other.attempt_id, "progress", {"fraction": 0.3}),
        )
        assert reader._replay and reader._pending and bus._ring
        value = event(claim.attempt_id, "progress", {"fraction": 0.4}, seq=3)
        message = "Event ownership mismatch"
        if rejection == "identity":
            value = event(other.attempt_id, "progress", {"fraction": 0.4}, seq=3)
        elif rejection == "sequence":
            value = event(claim.attempt_id, "progress", {"fraction": 0.4}, seq=4)
            message = "Event sequence or terminal contradiction"
        elif rejection == "owner":
            consumer = EventConsumer(
                engine,
                "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                bus,
                coordinator=consumer.coordinator,
            )
        elif rejection == "ordinal":
            with Session(engine) as session, session.begin():
                session.get(Job, jid).attempt += 1
        elif rejection in {"terminal", "replay"}:
            terminal = event(
                claim.attempt_id,
                "error",
                {"code": "INTERNAL", "message": "original", "retryable": False},
                seq=3,
            )
            assert consumer.accept(claim.attempt_id, "mock", terminal)
            if rejection == "terminal":
                value = event(claim.attempt_id, "progress", {"fraction": 0.4}, seq=4)
                message = "Event sequence or terminal contradiction"
            else:
                value = event(
                    claim.attempt_id,
                    "error",
                    {
                        "code": "INTERNAL",
                        "message": "contradiction",
                        "retryable": False,
                    },
                    seq=3,
                )
                message = "Contradictory terminal replay"
        before_db = database(engine)
        before_feed = feed(bus, (reader, other_reader))
        with pytest.raises(ValueError, match=message):
            consumer.accept(claim.attempt_id, "mock", value)
        assert database(engine) == before_db
        assert feed(bus, (reader, other_reader)) == before_feed
        assert reader._closed is None and other_reader._closed is None
        with Session(engine) as session:
            assert session.get(Job, other_jid).progress == 0.3
        reader.close()
        other_reader.close()

    asyncio.run(run())


@pytest.mark.parametrize("rejection", ["identity", "sequence", "replay"])
def test_rejection_rethrows_actual_primary_with_original_traceback_tail(
    engine, monkeypatch, rejection
):
    import app.queue.events as events_module

    _jid, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, owner, bus, coordinator=PublicationCoordinator())
    if rejection == "replay":
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(
                claim.attempt_id,
                "error",
                {"code": "INTERNAL", "message": "original", "retryable": False},
            ),
        )
        value = event(
            claim.attempt_id,
            "error",
            {"code": "INTERNAL", "message": "different", "retryable": False},
        )
    else:
        value = event(
            claim.attempt_id
            if rejection == "sequence"
            else "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "progress",
            {"fraction": 0.5},
            seq=2,
        )
    observed = []
    original = events_module.EventConsumer._prepare_batch

    def passthrough(self, *args):
        try:
            return original(self, *args)
        except ValueError as primary:
            # Observer only: actual validation exception, no substituted exception.
            observed.append((primary, primary.__traceback__))
            raise

    monkeypatch.setattr(events_module.EventConsumer, "_prepare_batch", passthrough)
    before = database(engine), feed(bus, ())
    with pytest.raises(ValueError) as raised:
        consumer.accept(claim.attempt_id, "mock", value)
    assert len(observed) == 1 and raised.value is observed[0][0]
    trace = raised.value.__traceback__
    while trace is not None and trace is not observed[0][1]:
        trace = trace.tb_next
    assert trace is observed[0][1]
    assert raised.value.__cause__ is None
    assert (database(engine), feed(bus, ())) == before


@pytest.mark.parametrize(
    "failure",
    [
        "begin",
        "commit-before",
        "commit-persist",
        "rollback-before",
        "rollback-after",
        "close-before",
        "close-after",
        "close-after-commit",
    ],
)
def test_uncertain_transaction_retains_primary_and_marks_real_gap(
    engine, monkeypatch, failure
):
    import app.queue.events as events_module

    jid, owner, claim = prepared(engine)

    async def run():
        bus = EventBus()
        consumer = EventConsumer(
            engine, owner, bus, coordinator=PublicationCoordinator()
        )
        cursor = bus.cursor
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.1}),
        )
        reader = bus.subscribe(TrustedFeedScope(owner), cursor)
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(claim.attempt_id, "progress", {"fraction": 0.2}, seq=2),
        )
        before_db = database(engine)
        old_epoch = bus.epoch
        boundary_error = RuntimeError("injected " + failure)
        observed = []
        sessions = []
        prepare = events_module.EventConsumer._prepare_batch

        def passthrough(self, *args):
            try:
                return prepare(self, *args)
            except ValueError as primary:
                observed.append(primary)
                raise

        class ObservedSession(Session):
            """Real SQLAlchemy Session; declared boundary fault injection only."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                sessions.append(self)

            def begin(self, *args, **kwargs):
                if failure == "begin":
                    raise boundary_error
                transaction = super().begin(*args, **kwargs)
                commit = transaction.commit
                rollback = transaction.rollback

                def injected_commit():
                    if failure == "commit-persist":
                        commit()
                    raise boundary_error

                def injected_rollback():
                    if failure == "rollback-after":
                        rollback()
                    raise boundary_error

                if failure.startswith("commit-"):
                    monkeypatch.setattr(transaction, "commit", injected_commit)
                if failure.startswith("rollback-"):
                    monkeypatch.setattr(transaction, "rollback", injected_rollback)
                return transaction

            def close(self):
                if failure in {"close-after", "close-after-commit"}:
                    super().close()
                if failure.startswith("close-"):
                    raise boundary_error
                return super().close()

        monkeypatch.setattr(events_module, "Session", ObservedSession)
        monkeypatch.setattr(events_module.EventConsumer, "_prepare_batch", passthrough)
        rejected = failure.startswith("rollback-") or failure in {
            "close-before",
            "close-after",
        }
        value = event(
            "01ARZ3NDEKTSV4RRFFQ69G5FAV" if rejected else claim.attempt_id,
            "progress",
            {"fraction": 0.9},
            seq=3,
        )
        try:
            with pytest.raises(Exception) as raised:
                consumer.accept(claim.attempt_id, "mock", value)
            if rejected:
                assert len(observed) == 1 and raised.value is observed[0]
                label = "rollback" if failure.startswith("rollback-") else "close"
                assert (
                    label,
                    boundary_error,
                ) in raised.value._publication_secondary_errors
                assert any(label in note for note in raised.value.__notes__)
            else:
                assert raised.value is boundary_error
            assert bus.epoch != old_epoch and not bus._ring
            assert (
                reader._closed == "gap" and not reader._replay and not reader._pending
            )
            if failure in {"commit-persist", "close-after-commit"}:
                with Session(engine) as session:
                    assert session.get(Job, jid).progress == 0.9
                assert database(engine) != before_db
            else:
                assert database(engine) == before_db
        finally:
            # Close owned actual sessions via original implementation after fault observation.
            for session in sessions:
                Session.close(session)
            reader.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "result", ["bool", "json", "error", "object", "invalid-seal", "subclass"]
)
def test_untrusted_callback_result_cannot_confirm_rollback(engine, result):
    from dataclasses import replace

    from app.publication import _ConfirmedRollback

    _jid, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, owner, bus, coordinator=PublicationCoordinator())
    assert consumer.accept(
        claim.attempt_id, "mock", event(claim.attempt_id, "progress", {"fraction": 0.1})
    )
    old_epoch = bus.epoch
    before = database(engine)
    primary = ValueError("ordinary")

    class ForgedSubclass(_ConfirmedRollback):
        pass

    values = {
        "bool": True,
        "json": {"rollback": True},
        "error": primary,
        "object": object(),
        "invalid-seal": _ConfirmedRollback(primary, None, object()),
        "subclass": ForgedSubclass(primary, None, object()),
    }
    if result == "invalid-seal":
        valid = consumer._commit_coordinated(
            claim.attempt_id,
            "mock",
            event("01ARZ3NDEKTSV4RRFFQ69G5FAV", "progress", {"fraction": 0.2}, seq=2),
            "2026-10-08T02:00:00Z",
        )
        values[result] = replace(valid, _seal=object())
    with pytest.raises(TypeError, match="INVALID_COMMIT_RESULT"):
        consumer.coordinator.commit_and_publish(lambda: values[result], bus)
    assert bus.epoch != old_epoch and not bus._ring
    assert database(engine) == before


def test_generic_callback_value_error_is_uncertain(engine):
    _jid, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, owner, bus, coordinator=PublicationCoordinator())
    assert consumer.accept(
        claim.attempt_id, "mock", event(claim.attempt_id, "progress", {"fraction": 0.1})
    )
    old_epoch = bus.epoch
    before = database(engine)
    primary = ValueError("no transactional evidence")

    def callback():
        raise primary

    with pytest.raises(ValueError) as raised:
        consumer.coordinator.commit_and_publish(callback, bus)
    assert raised.value is primary and bus.epoch != old_epoch and not bus._ring
    assert database(engine) == before


def test_confirmed_outcome_is_immutable_and_legacy_error_remains_original(
    engine, monkeypatch
):
    from dataclasses import FrozenInstanceError

    jid, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, owner, bus)
    value = event("01ARZ3NDEKTSV4RRFFQ69G5FAV", "progress", {"fraction": 0.2})
    observed = []
    original = consumer._prepare_batch

    def passthrough(*args):
        try:
            return original(*args)
        except ValueError as primary:
            observed.append(primary)
            raise

    monkeypatch.setattr(consumer, "_prepare_batch", passthrough)
    before = database(engine), feed(bus, ())
    with pytest.raises(ValueError, match="Event ownership mismatch") as raised:
        consumer.accept(claim.attempt_id, "mock", value)
    assert raised.value is observed[0]
    assert (database(engine), feed(bus, ())) == before
    result = consumer._commit_coordinated(
        claim.attempt_id, "mock", value, "2026-10-08T02:00:00Z"
    )
    with pytest.raises(FrozenInstanceError):
        result.primary = RuntimeError("replacement")
    assert result.primary is observed[-1]
    with Session(engine) as session:
        assert session.get(Job, jid).progress is None
