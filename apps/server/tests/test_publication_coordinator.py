"""Commit SQLite real y barrera compartida, sin HTTP ni wiring del runtime."""

import asyncio
import sqlite3
from threading import Event, Thread

import pytest
from app.models import Job, JobAttempt
from app.publication import (
    CommitPublication,
    PublicationCoordinator,
    PublicationTimeout,
)
from app.queue.events import EventBus, EventConsumer
from app.sse import TrustedFeedScope, encode_frame
from sqlalchemy.orm import Session
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414
from test_dispatcher_recovery import event, prepared


def test_sqlite_commit_precedes_publication_and_durable_return(tmp_path):
    path = tmp_path / "real.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE state(value INTEGER)")
    observed = []

    class Bus:
        def publish_confirmed(self, envelope):
            with sqlite3.connect(path) as reader:
                observed.append(
                    (reader.execute("SELECT value FROM state").fetchone()[0], envelope)
                )
            return True

        def mark_gap(self):
            pytest.fail("No gap for a successful publication")

    def commit():
        with sqlite3.connect(path) as db:
            db.execute("INSERT INTO state VALUES (7)")
            batch = CommitPublication("durable", ({"type": "test"},))
        return batch

    outcome = PublicationCoordinator().commit_and_publish(commit, Bus())
    assert observed == [(7, {"type": "test"})]
    assert outcome.value == "durable" and outcome.published


def test_two_owned_threads_snapshot_cannot_cross_commit_publication(tmp_path):
    path = tmp_path / "ordering.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE state(value INTEGER)")
        db.execute("INSERT INTO state VALUES (0)")
    coordinator = PublicationCoordinator()
    publication_entered, release, snapshot_started, snapshot_done = (
        Event() for _ in range(4)
    )
    trace, errors = [], []

    class Bus:
        def publish_confirmed(self, envelope):
            trace.append("publish-enter")
            publication_entered.set()
            assert release.wait(1)
            trace.append("publish-exit")
            return True

        def mark_gap(self):
            errors.append("unexpected-gap")

    def commit():
        with sqlite3.connect(path) as db:
            db.execute("UPDATE state SET value=9")
            batch = CommitPublication(9, ({},))
        with sqlite3.connect(path) as reader:
            assert reader.execute("SELECT value FROM state").fetchone() == (9,)
        trace.append("committed")
        return batch

    def writer_thread():
        try:
            coordinator.commit_and_publish(commit, Bus())
        except BaseException as error:  # noqa: BLE001 -- recoger fallo del hilo propio
            errors.append(error)

    def snapshot_thread():
        snapshot_started.set()
        try:
            with coordinator.barrier(), sqlite3.connect(path) as reader:
                trace.append(
                    (
                        "snapshot",
                        reader.execute("SELECT value FROM state").fetchone()[0],
                    )
                )
            snapshot_done.set()
        except BaseException as error:  # noqa: BLE001 -- recoger fallo del hilo propio
            errors.append(error)

    threads = [Thread(target=writer_thread), Thread(target=snapshot_thread)]
    try:
        threads[0].start()
        assert publication_entered.wait(1)
        threads[1].start()
        assert snapshot_started.wait(1)
        assert not snapshot_done.wait(0.03)
    finally:
        release.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(2)
    assert all(not thread.is_alive() for thread in threads)
    assert not errors
    assert trace == ["committed", "publish-enter", "publish-exit", ("snapshot", 9)]


@pytest.mark.parametrize("gap_failure", [False, True])
def test_publish_failure_keeps_real_committed_value(tmp_path, gap_failure):
    path = tmp_path / "durable.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE state(value INTEGER)")
    primary = RuntimeError("publisher")
    calls = []

    class Bus:
        def publish_confirmed(self, value):
            calls.append("publish")
            raise primary

        def mark_gap(self):
            calls.append("gap")
            if gap_failure:
                raise RuntimeError("gap")

    def commit():
        with sqlite3.connect(path) as db:
            db.execute("INSERT INTO state VALUES (3)")
            batch = CommitPublication(3, ({}, {}))
        return batch

    outcome = PublicationCoordinator().commit_and_publish(commit, Bus())
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT value FROM state").fetchall() == [(3,)]
    assert outcome.value == 3 and not outcome.published
    assert outcome.publication_error is primary
    assert bool(outcome.gap_error) == gap_failure
    assert calls == ["publish", "gap"]


@pytest.mark.parametrize("gap_failure", [False, True])
def test_commit_uncertainty_preserves_primary_exception(gap_failure):
    primary = RuntimeError("commit uncertain")
    calls = []

    class Bus:
        def publish_confirmed(self, value):
            calls.append("publish")

        def mark_gap(self):
            calls.append("gap")
            if gap_failure:
                raise RuntimeError("secondary")

    def commit():
        raise primary

    with pytest.raises(RuntimeError) as raised:
        PublicationCoordinator().commit_and_publish(commit, Bus())
    assert raised.value is primary
    assert calls == ["gap"]
    if gap_failure:
        assert "mark_gap" in primary.__notes__[0]


def test_intentionally_omitted_publication_marks_gap():
    bus = EventBus()
    old = bus.epoch
    result = PublicationCoordinator().commit_and_publish(
        lambda: CommitPublication(1, (), invalidate=True), bus
    )
    assert result.value == 1 and result.published and bus.epoch != old
    assert result.confirmed_count == 0 and not bus._ring


def test_reentrant_barrier_and_timeout_with_owned_thread():
    coordinator = PublicationCoordinator(acquisition_timeout=0.02)
    held, release = Event(), Event()
    errors = []

    def holder():
        try:
            with coordinator.barrier(), coordinator.barrier():
                held.set()
                assert release.wait(1)
        except BaseException as error:  # noqa: BLE001 -- recoger fallo del hilo propio
            errors.append(error)

    thread = Thread(target=holder)
    thread.start()
    try:
        assert held.wait(1)
        with pytest.raises(PublicationTimeout), coordinator.barrier():
            pytest.fail("Acquired occupied barrier")
    finally:
        release.set()
        thread.join(2)
    assert not thread.is_alive() and not errors
    with coordinator.barrier():
        pass


@pytest.mark.parametrize("timeout", [0, -1, 3, True, float("nan"), float("inf"), "2"])
def test_invalid_deadlines(timeout):
    with pytest.raises(ValueError):
        PublicationCoordinator(acquisition_timeout=timeout)


@pytest.mark.parametrize("events", [[], tuple({} for _ in range(1065))])
def test_batch_is_finite_before_commit(events):
    with pytest.raises(ValueError):
        CommitPublication(None, events)


def test_consumer_certifies_from_db_with_optional_shared_coordinator(engine):
    jid, owner, claim = prepared(engine)

    async def run():
        bus = EventBus()
        scope = TrustedFeedScope(owner)
        subscription = bus.subscribe(scope, bus.cursor)
        consumer = EventConsumer(
            engine, owner, bus, coordinator=PublicationCoordinator()
        )
        value = event(claim.attempt_id, "progress", {"fraction": 0.25})
        assert consumer.accept(claim.attempt_id, "mock", value)
        record = await asyncio.wait_for(subscription.next(), 1)
        frame = encode_frame(record, scope)
        assert jid.encode() in frame and b"owner_id" not in frame
        assert b"public_scope_verified" not in frame
        assert not consumer.accept(claim.attempt_id, "mock", value)
        with Session(engine) as session:
            assert session.get(Job, jid).progress == 0.25
            assert session.get(JobAttempt, claim.attempt_id).last_seq == 1
        subscription.close()

    asyncio.run(run())


def test_consumer_publication_fault_does_not_become_engine_failure(engine):
    jid, owner, claim = prepared(engine)

    class BrokenBus(EventBus):
        def publish_confirmed(self, value):
            raise RuntimeError("after durable commit")

    bus = BrokenBus()
    epoch = bus.epoch
    consumer = EventConsumer(engine, owner, bus, coordinator=PublicationCoordinator())
    value = event(
        claim.attempt_id,
        "done",
        {"artifacts": [], "telemetry": {"mode": "bf16", "model_revision": "synthetic"}},
    )
    assert consumer.accept(claim.attempt_id, "mock", value)
    assert bus.epoch != epoch
    with Session(engine) as session:
        assert session.get(Job, jid).status == "succeeded"
        assert session.get(JobAttempt, claim.attempt_id).terminal == value


@pytest.mark.parametrize("coordinated", [False, True])
def test_consumer_valid_engine_private_label_keeps_durable_state_and_gap(
    engine, coordinated
):
    jid, owner, claim = prepared(engine)
    bus = EventBus()
    epoch = bus.epoch
    consumer = EventConsumer(
        engine,
        owner,
        bus,
        coordinator=PublicationCoordinator() if coordinated else None,
    )
    value = event(claim.attempt_id, "stage", {"stage": "private/path with spaces"})
    assert consumer.accept(claim.attempt_id, "mock", value)
    assert bus.epoch != epoch and not bus._ring
    with Session(engine) as session:
        assert session.get(Job, jid).stage == "private/path with spaces"
        assert session.get(JobAttempt, claim.attempt_id).last_seq == 1


@pytest.mark.parametrize(
    "mode", ["invalid-stage", "invalid-certificate", "shutdown", "valid"]
)
def test_real_bus_acknowledges_only_ring_acceptance_after_sqlite_commit(tmp_path, mode):
    """B01 causal: actual bus and SQLite, no publisher double."""
    from dataclasses import replace

    from app.sse import certify_publication

    path = tmp_path / "ack.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE state(value INTEGER)")
    bus = EventBus()
    epoch = bus.epoch
    envelope = {
        "job_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "type": "job.stage",
        "ts": "2026-10-08T02:00:00Z",
        "data": {"stage": "running"},
    }
    if mode == "invalid-stage":
        envelope["data"]["stage"] = "private/path with spaces"
    elif mode == "invalid-certificate":
        certified = certify_publication(
            envelope,
            owner_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
            song_id="01ARZ3NDEKTSV4RRFFQ69G5FAX",
        )
        envelope = replace(
            certified, authority=replace(certified.authority, _seal=object())
        )
    elif mode == "shutdown":
        bus.shutdown()

    def commit():
        with sqlite3.connect(path) as db:
            db.execute("INSERT INTO state VALUES (17)")
            batch = CommitPublication(17, (envelope,))
        return batch

    outcome = PublicationCoordinator().commit_and_publish(commit, bus)
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT value FROM state").fetchall() == [(17,)]
    assert outcome.value == 17
    assert len(bus.buffer) == 1
    assert bool(bus._ring) == (mode == "valid")
    assert outcome.published == (mode == "valid")
    assert outcome.confirmed_count == (1 if mode == "valid" else 0)
    if mode == "valid":
        assert outcome.publication_error is None
        assert bus.epoch == epoch
    else:
        assert outcome.publication_error is not None
        assert bus.epoch != epoch


@pytest.mark.parametrize("ack", [None, False, 1])
def test_mock_publisher_unknown_ack_is_not_success(tmp_path, ack):
    """Double explícito; no forma parte del RED causal con bus real."""
    path = tmp_path / "unknown.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE state(value INTEGER)")
    appended = []

    class Bus:
        def publish_confirmed(self, envelope):
            appended.append(envelope)
            return ack

        def mark_gap(self):
            appended.append("gap")

    def commit():
        with sqlite3.connect(path) as db:
            db.execute("INSERT INTO state VALUES (1)")
        return CommitPublication(1, ({},))

    outcome = PublicationCoordinator().commit_and_publish(commit, Bus())
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT value FROM state").fetchone() == (1,)
    assert outcome.value == 1 and not outcome.published
    assert outcome.confirmed_count == 0
    assert str(outcome.publication_error) == "PUBLICATION_NOT_CONFIRMED"
    assert appended == [{}, "gap"]
