"""Contrato público exacto y rechazo finito de entradas inválidas."""

import asyncio
import json

import pytest
from app.queue.events import EventBus
from app.sse import (
    MAX_SAFE_INTEGER,
    PublicPayloadError,
    PublicRecord,
    TrustedScope,
    bounded_json,
    encode_frame,
    heartbeat,
    parse_cursor,
    public_event,
)

SCOPE = TrustedScope(owner_id="local", job_ids=frozenset({"job"}), allow_delta=True)
EPOCH = "a" * 32


def record(kind="job.delta", data=None, ts="2026-10-08T02:00:00Z", seq=2):
    return PublicRecord(
        EPOCH,
        seq,
        {
            "job_id": "job",
            "type": kind,
            "ts": ts,
            "data": {"text": "línea\nsegunda 😀"} if data is None else data,
        },
    )


def test_filter_before_data_and_error_privacy():
    foreign = PublicRecord(EPOCH, 2, {"job_id": "foreign", "data": object()})
    assert public_event(foreign, SCOPE) is None
    value = public_event(
        record(
            "job.error",
            {
                "code": "INTERNAL",
                "message": "token=SECRET /tmp/private",
                "retryable": True,
                "engine_request": {"token": "SECRET"},
            },
        ),
        SCOPE,
    )
    assert value == {
        "id": 2,
        "type": "job.failed",
        "ts": "2026-10-08T02:00:00.000Z",
        "data": {"job_id": "job", "code": "INTERNAL", "retryable": True},
    }
    assert public_event(record(), TrustedScope("local", frozenset({"job"})))[
        "data"
    ] == {"job_id": "job"}

    async def run():
        bus = EventBus()
        sub = bus.subscribe(SCOPE, bus.cursor)
        bus.publish(
            {
                "job_id": "foreign",
                "type": "job.progress",
                "ts": "2026-10-08T02:00:00Z",
                "data": {"fraction": 0.5},
            }
        )
        bus.publish(record("job.progress", {"fraction": 0.2}).envelope)
        assert (await sub.next()).seq == 3
        sub.close()

    asyncio.run(run())


def test_wire_utf8_timestamps_bytes_and_cursor_boundaries():
    frame = encode_frame(record(), SCOPE)
    lines = frame.decode("utf-8").splitlines()
    assert lines[0] == f"id: {EPOCH}:2"
    assert lines[1] == "event: job.delta"
    body = json.loads(lines[2][6:])
    assert set(body) == {"id", "type", "ts", "data"}
    assert body["ts"] == "2026-10-08T02:00:00.000Z"
    assert body["data"]["text"] == "línea\nsegunda 😀"
    assert len(lines) == 4
    assert heartbeat() == b": keep-alive\n\n"
    assert parse_cursor(f"{EPOCH}:{MAX_SAFE_INTEGER}").seq == MAX_SAFE_INTEGER
    for bad in (
        "x" * 97,
        f"{EPOCH}:0",
        f"{EPOCH}:01",
        f"{EPOCH}:{MAX_SAFE_INTEGER + 1}",
        f"{EPOCH}:1\n",
        "é" * 49,
        "A" * 32 + ":2",
    ):
        with pytest.raises(PublicPayloadError):
            parse_cursor(bad)
    for bad in (
        record(ts="2026-02-30T00:00:00Z"),
        record(data={"text": "x" * 65536}),
        record(data={"text": "\ud800"}),
        record("evil\nevent"),
        record(seq=True),
        record("job.progress", {"fraction": float("nan")}),
        record(data={"text": {"token": "secret"}}),
    ):
        with pytest.raises(PublicPayloadError):
            encode_frame(bad, SCOPE)


def test_scopes_public_types_and_finite_shape_errors():
    assert parse_cursor(EPOCH + ":2").wire == EPOCH + ":2"
    assert encode_frame(PublicRecord(EPOCH, 2, {"job_id": "foreign"}), SCOPE) is None
    for envelope in (
        {"job_id": "job", "owner_id": "foreign"},
        {"job_id": []},
        [],
        {"job_id": "job", "song_id": "other"},
    ):
        scope = TrustedScope("local", frozenset({"job"}), song_id="song")
        assert not scope.matches(envelope)
    assert not TrustedScope("local").matches({"type": "system.status"})
    cases = (
        ("job.created", {"status": "queued"}),
        ("job.stage", {"stage": "generating"}),
        ("job.done", {"status": "succeeded", "result": {"text": "SECRET"}}),
        ("job.cancelled", {"status": "cancelled"}),
        ("job.failed", {"code": "INTERNAL", "retryable": False}),
        ("entity.updated", {"type": "take", "id": "entity"}),
        ("system.status", {"status": "ready"}),
    )
    for kind, data in cases:
        scope = TrustedScope(
            "local",
            frozenset({"job"}),
            entity_ids=frozenset({"entity"}),
            allow_system=True,
        )
        item = record(kind, data)
        item.envelope["entity_id"] = "entity"
        item.envelope["attempt_id"] = "attempt"
        assert (
            json.loads(encode_frame(item, scope).decode().split("data: ")[1])["type"]
            == kind
        )
        if kind == "entity.updated":
            assert json.loads(
                encode_frame(item, scope).decode().split("data: ")[1]
            ) == {
                "id": 2,
                "type": kind,
                "ts": "2026-10-08T02:00:00.000Z",
                "data": {"type": "take", "id": "entity"},
            }
    for data, kind in (
        ({"retryable": 1}, "job.failed"),
        ({"type": "take", "id": True}, "entity.updated"),
        ({"stage": "token=/secret"}, "job.stage"),
        ({"fraction": True}, "job.progress"),
    ):
        item = record(kind, data)
        item.envelope["entity_id"] = "entity"
        scope = TrustedScope(
            "local", frozenset({"job"}), entity_ids=frozenset({"entity"})
        )
        with pytest.raises(PublicPayloadError):
            encode_frame(item, scope)
    for bad in (
        record(data=[]),
        record(ts=3),
        PublicRecord("bad", 2, record().envelope),
    ):
        with pytest.raises(PublicPayloadError):
            encode_frame(bad, SCOPE)
    for kwargs in (
        {"owner_id": ""},
        {"owner_id": "local", "job_ids": {"job"}},
        {"owner_id": "local", "song_id": 3},
        {"owner_id": "local", "allow_delta": 1},
    ):
        with pytest.raises(PublicPayloadError):
            TrustedScope(**kwargs)
    nested = "value"
    for _ in range(10):
        nested = [nested]
    for bad in (
        nested,
        [0] * 5000,
        {"x": object()},
        {1: "value"},
        {"x": float("inf")},
        {"x": MAX_SAFE_INTEGER + 1},
        {"x": "\ud800"},
        {"x": "😀" * 20000},
        {"x": None, "y": [False]},
    ):
        if bad == {"x": None, "y": [False]}:
            bounded_json(bad)
        else:
            with pytest.raises(PublicPayloadError):
                bounded_json(bad)
    with pytest.raises(PublicPayloadError, match="FRAME_LIMIT"):
        encode_frame(record(data={"text": "\n" * 40000}), SCOPE)


@pytest.mark.parametrize("private_fields", [False, True])
def test_entity_updated_canonical_frame_and_private_fields(private_fields):
    scope = TrustedScope("local", entity_ids=frozenset({"take01"}))
    item = PublicRecord(
        EPOCH,
        2,
        {
            "type": "entity.updated",
            "entity_id": "take01",
            "job_id": "job",
            "attempt_id": "attempt",
            "song_id": "song",
            "ts": "2026-10-08T02:00:00Z",
            "data": {
                "type": "take",
                "id": "take01",
                "entity_type": "private",
                "entity_id": "private",
                "revision": 7,
                "callerPrivateFields": {"token": "SECRET"},
            },
        },
    )
    if not private_fields:
        item.envelope["data"] = {"type": "take", "id": "take01"}
    frame = encode_frame(item, scope)
    assert (
        frame
        == (
            f"id: {EPOCH}:2\nevent: entity.updated\ndata: "
            '{"id":2,"type":"entity.updated","ts":"2026-10-08T02:00:00.000Z",'
            '"data":{"type":"take","id":"take01"}}\n\n'
        ).encode()
    )


@pytest.mark.parametrize("field", ["type", "id"])
@pytest.mark.parametrize(
    "bad", [None, True, 1, [], {}, "", "x" * 65, "é", "a\n", "token=/secret"]
)
def test_entity_updated_bounded_canonical_strings(field, bad):
    data = {"type": "take", "id": "take01"}
    data[field] = bad
    item = PublicRecord(
        EPOCH,
        2,
        {
            "type": "entity.updated",
            "entity_id": "take01",
            "ts": "2026-10-08T02:00:00Z",
            "data": data,
        },
    )
    with pytest.raises(PublicPayloadError):
        encode_frame(item, TrustedScope("local", entity_ids=frozenset({"take01"})))


@pytest.mark.parametrize("data", [{}, {"type": "take"}, {"id": "take01"}])
def test_entity_updated_requires_canonical_pair(data):
    item = PublicRecord(
        EPOCH,
        2,
        {
            "type": "entity.updated",
            "entity_id": "take01",
            "ts": "2026-10-08T02:00:00Z",
            "data": data,
        },
    )
    with pytest.raises(PublicPayloadError):
        encode_frame(item, TrustedScope("local", entity_ids=frozenset({"take01"})))
