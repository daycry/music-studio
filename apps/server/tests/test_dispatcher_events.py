"""Atomicidad SQLite y bus limitado sin inventar salidas."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from app.models import Analysis, Job, JobAttempt, Take, new_id
from app.queue.events import EventBus, EventConsumer
from sqlalchemy import event as sql_event
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414
from test_dispatcher_recovery import event, prepared


def test_native_event_effect_cursor_commit_and_replay(engine):
    jid, owner, claim = prepared(engine)
    bus = EventBus(2)
    consumer = EventConsumer(engine, owner, bus)
    stage = event(claim.attempt_id, "stage", {"stage": "generating"})
    progress = event(claim.attempt_id, "progress", {"fraction": 0.5}, 2)
    done = event(
        claim.attempt_id,
        "done",
        {
            "artifacts": [],
            "result": {"text": "actual synthetic result"},
            "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
        },
        3,
    )
    for value in (stage, progress, done):
        assert consumer.accept(claim.attempt_id, "mock", value)
    for value in (stage, progress, done):
        assert not consumer.accept(claim.attempt_id, "mock", value)
    with Session(engine) as session:
        job, attempt = session.get(Job, jid), session.get(JobAttempt, claim.attempt_id)
        assert (job.stage, job.progress, job.status, attempt.last_seq) == (
            "generating",
            0.5,
            "succeeded",
            3,
        )
        assert attempt.terminal.data["result"]["text"] == "actual synthetic result"
        assert job.telemetry["mode"] == "bf16"
    assert [value["type"] for value in bus.buffer] == ["job.progress", "job.done"]


def test_audio_beats_terminal_persists_analysis_for_ready_take(engine):
    jid, owner, claim = prepared(engine)
    take_id = new_id()
    with Session(engine) as session:
        job = session.get(Job, jid)
        session.add(
            Take(
                id=take_id,
                owner_id=owner,
                song_id=job.song_id,
                job_id=jid,
                status="ready",
                batch_id=take_id,
                variant_index=0,
                root_id=take_id,
                derivation="original",
                task="music.instrumental",
                model_id="mock",
                model_version="1",
                seed=17,
                commercial_use=True,
            )
        )
        job.task = "audio.beats"
        job.lane = "cpu"
        job.request = {
            "params": {},
            "inputs": [{"role": "master", "ref": {"type": "take", "id": take_id}}],
        }
        session.commit()
    value = event(
        claim.attempt_id,
        "done",
        {
            "artifacts": [],
            "result": {
                "task": "audio.beats",
                "analysis": {
                    "bpm": 120.0,
                    "beats_s": [0.0, 0.5],
                    "downbeats_s": [0.0],
                },
                "stages": [
                    {"task": "audio.beats", "model_id": "beat-this", "revision": "r1"}
                ],
            },
            "telemetry": {"mode": "cpu", "model_revision": "r1"},
        },
    )

    EventConsumer(engine, owner, EventBus()).accept(claim.attempt_id, "mock", value)

    with Session(engine) as session:
        row = session.scalar(
            select(Analysis).where(
                Analysis.take_id == take_id, Analysis.kind == "beats"
            )
        )
        assert row is not None
        assert (row.analyzer_id, row.analyzer_version, row.data["bpm"]) == (
            "beat-this",
            "r1",
            120.0,
        )


@pytest.mark.parametrize(
    "fault",
    [
        "owner",
        "engine",
        "foreign_job",
        "gap",
        "typed",
        "deleted",
        "ordinal",
        "contradiction",
    ],
)
def test_invalid_events_fail_closed_without_cursor_or_publish(engine, fault):
    jid, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, new_id() if fault == "owner" else owner, bus)
    value = event(claim.attempt_id, "stage", {"stage": "generating"})
    engine_id = "foreign" if fault == "engine" else "mock"
    if fault == "foreign_job":
        value.job_id = new_id()
    if fault == "gap":
        value.seq = 2
    if fault == "typed":
        value.data = {"stage": 12}
    if fault in {"deleted", "ordinal"}:
        with Session(engine) as session, session.begin():
            job = session.get(Job, jid)
            if fault == "deleted":
                job.deleted_at = "2026-10-08T02:00:00Z"
            else:
                job.attempt = 2
    if fault == "contradiction":
        done = event(
            claim.attempt_id,
            "done",
            {
                "artifacts": [],
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        )
        consumer.accept(claim.attempt_id, "mock", done)
        bus.buffer.clear()
    with pytest.raises(ValueError):
        consumer.accept(claim.attempt_id, engine_id, value)
    with Session(engine) as session:
        assert session.get(JobAttempt, claim.attempt_id).last_seq == (
            1 if fault == "contradiction" else 0
        )
    assert not bus.buffer


def test_independent_native_writers_accept_same_event_once(engine):
    _, owner, claim = prepared(engine)
    consumer = EventConsumer(engine, owner, EventBus())
    value = event(claim.attempt_id, "progress", {"fraction": 0.25})
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(
                lambda _: consumer.accept(claim.attempt_id, "mock", value), range(2)
            )
        )
    assert sorted(results) == [False, True]
    assert len(consumer.bus.buffer) == 1


@pytest.mark.parametrize("failure", ["commit", "after_commit"])
def test_commit_failure_or_bus_failure_preserves_replay_semantics(engine, failure):
    _, owner, claim = prepared(engine)
    bus = EventBus()
    consumer = EventConsumer(engine, owner, bus)
    value = event(
        claim.attempt_id,
        "done",
        {"artifacts": [], "telemetry": {"mode": "bf16", "model_revision": "synthetic"}},
    )

    def fail(*args):
        raise RuntimeError("synthetic fault")

    if failure == "commit":
        sql_event.listen(engine, "commit", fail)
    else:
        bus.publish = fail
    try:
        with pytest.raises(RuntimeError, match="synthetic fault"):
            consumer.accept(claim.attempt_id, "mock", value)
    finally:
        if failure == "commit":
            sql_event.remove(engine, "commit", fail)
    with Session(engine) as session:
        attempt = session.get(JobAttempt, claim.attempt_id)
        assert attempt.last_seq == (0 if failure == "commit" else 1)
    bus.publish = EventBus.publish.__get__(bus)
    assert consumer.accept(claim.attempt_id, "mock", value) == (failure == "commit")
    assert len(bus.buffer) == (1 if failure == "commit" else 0)


@pytest.mark.parametrize("first", ["cancel", "success"])
def test_terminal_cancel_race_preserves_transaction_winner(engine, first):
    from app.queue.cancellation import Cancellation

    jid, owner, claim = prepared(engine)
    consumer = EventConsumer(engine, owner, EventBus())
    cancellation = Cancellation(engine, owner)
    value = event(
        claim.attempt_id,
        "done",
        {"artifacts": [], "telemetry": {"mode": "bf16", "model_revision": "synthetic"}},
    )
    if first == "cancel":
        assert cancellation.request(jid)
    consumer.accept(claim.attempt_id, "mock", value)
    if first == "success":
        assert not cancellation.request(jid)
    with Session(engine) as session:
        assert session.get(Job, jid).status == (
            "cancelled" if first == "cancel" else "succeeded"
        )
        assert session.get(JobAttempt, claim.attempt_id).terminal == value


def test_success_after_cancel_does_not_publish_success_notification(engine):
    from app.queue.cancellation import Cancellation

    jid, owner, claim = prepared(engine)
    bus = EventBus()
    Cancellation(engine, owner).request(jid)
    EventConsumer(engine, owner, bus).accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "done",
            {
                "artifacts": [],
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        ),
    )
    assert [message["type"] for message in bus.buffer] == ["job.cancelled"], (
        "Late success announced despite durable cancellation"
    )


def test_contradictory_old_terminal_is_not_silently_treated_as_duplicate(engine):
    _, owner, claim = prepared(engine)
    consumer = EventConsumer(engine, owner, EventBus())
    consumer.accept(
        claim.attempt_id, "mock", event(claim.attempt_id, "stage", {"stage": "actual"})
    )
    consumer.accept(
        claim.attempt_id,
        "mock",
        event(claim.attempt_id, "progress", {"fraction": 0.5}, 2),
    )
    with pytest.raises(ValueError, match="terminal"):
        consumer.accept(
            claim.attempt_id,
            "mock",
            event(
                claim.attempt_id,
                "error",
                {
                    "code": "INTERNAL",
                    "message": "contradictory old terminal",
                    "retryable": True,
                },
            ),
        )
