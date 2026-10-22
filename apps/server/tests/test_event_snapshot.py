"""Snapshot cerrado y feed interno: los DTOs no acreditan autoridad SQL."""

import asyncio
import json
from copy import deepcopy

import pytest
from app.event_dtos import MAX_SAFE_INTEGER, JobStateDTO
from app.event_snapshot import build_snapshot
from app.models import new_id
from app.queue.events import EventBus
from app.sse import (
    CertifiedPublication,
    PublicPayloadError,
    PublicRecord,
    TrustedFeedScope,
    TrustedScope,
    certify_publication,
    encode_frame,
)

EPOCH = "a" * 32
STAMP = "2026-10-09T04:00:00.000Z"
OWNER = "0" * 26
SONG = "0" * 25 + "1"


def job(n, status="running", **updates):
    value = {
        "job_id": f"{n:026d}",
        "song_id": SONG,
        "status": status,
        "attempt_id": None,
        "stage": None,
        "progress": None,
        "error_code": None,
    }
    value.update(updates)
    return JobStateDTO.model_validate(value)


def snapshot(active=(), known=(), **changes):
    values = {
        "active": active,
        "known": known,
        "epoch": EPOCH,
        "high_water": 17,
        "ts": STAMP,
        "snapshot_id": "b" * 32,
        "reason": "bootstrap",
    }
    values.update(changes)
    return build_snapshot(**values)


def bodies(frames):
    return [json.loads(frame.split(b"data: ", 1)[1]) for frame in frames]


def test_snapshot_deduplicates_orders_and_confirms_only_end():
    active = [job(3), job(1), job(3)]
    known = [job(2, "succeeded"), job(1), job(2, "succeeded")]
    frames = snapshot(active, known)
    controls = bodies(frames)
    assert [v["data"]["phase"] for v in controls] == ["begin", "chunk", "end"]
    assert controls[0]["data"]["active_count"] == 2
    assert controls[0]["data"]["known_count"] == 1
    assert [v["job_id"] for v in controls[1]["data"]["jobs"]] == [
        job(n).job_id for n in (1, 2, 3)
    ]
    assert all(
        v["id"] == 17 and v["ts"] == STAMP and v["data"]["snapshot_id"] == "b" * 32
        for v in controls
    )
    assert all(b"\nid:" not in frame for frame in frames[:-1])
    assert b"id: " + (EPOCH + ":17").encode() in frames[-1]
    assert controls[1]["data"]["jobs"][0]["progress"] is None


def test_empty_snapshot_has_begin_and_end():
    assert [v["data"]["phase"] for v in bodies(snapshot())] == ["begin", "end"]


def test_maximum_snapshot_17_chunks_and_worst_case_complete_frame_bound():
    # Todos los strings del DTO tienen alfabeto ASCII sin escapes. El número
    # positivo float más largo <=24 caracteres; aquí se usa un caso de 23.
    updates = {
        "attempt_id": "7" + "Z" * 25,
        "stage": "Z" * 64,
        "error_code": "Z" * 64,
        "progress": 2.2250738585072014e-308,
    }
    active = [job(n, "interrupted", **updates) for n in range(1000)]
    known = [job(n, "cancelled", **updates) for n in range(1000, 1064)]
    frames = snapshot(active, known, high_water=MAX_SAFE_INTEGER)
    controls = bodies(frames)
    assert len(frames) == 19 and controls[0]["data"]["chunk_count"] == 17
    assert sum(len(v["data"]["jobs"]) for v in controls[1:-1]) == 1064
    assert max(len(frame) for frame in frames) <= 65536
    # Cota independiente conservadora por claves/literales + máximos actuales:
    # 512 bytes/job, 1024 para todo el control y las líneas SSE.
    assert 64 * 512 + 1024 <= 65536
    assert (
        max(
            len(json.dumps(v.model_dump(), separators=(",", ":")))
            for v in active + known
        )
        <= 512
    )


@pytest.mark.parametrize(
    "change",
    [
        {"active": [job(n) for n in range(1001)]},
        {"known": [job(n, "failed") for n in range(65)]},
        {"active": [job(1, "succeeded")]},
        {"known": [job(1)]},
        {"epoch": "bad"},
        {"high_water": 0},
        {"high_water": True},
        {"high_water": MAX_SAFE_INTEGER + 1},
        {"ts": "private/path"},
        {"snapshot_id": "bad"},
        {"reason": "private-token"},
        {"active": [job(1).model_dump()]},
        {"active": [job(1), JobStateDTO.model_construct(job_id="private/path")]},
    ],
)
def test_preflight_rejects_invalid_inputs_without_partial_output(change):
    with pytest.raises(ValueError):
        snapshot(**change)


def test_conflicting_duplicate_is_rejected_before_any_frames():
    with pytest.raises(ValueError):
        snapshot([job(1), job(1, progress=0.5)])


def envelope(jid=None, **updates):
    value = {
        "job_id": jid or new_id(),
        "type": "job.progress",
        "ts": STAMP,
        "data": {"fraction": 0.5},
    }
    value.update(updates)
    return value


def trusted(value, owner=OWNER, song=SONG):
    # Fixture de autoridad explícita. En producción sólo el server, después
    # de sus checks DB, puede invocar este certificado; no es autenticación.
    return certify_publication(value, owner_id=owner, song_id=song)


def test_explicit_authority_certificate_matches_global_feed():
    certified = trusted(envelope())
    record = PublicRecord(EPOCH, 2, certified.envelope, certified.authority)
    assert TrustedFeedScope(OWNER).matches(record)


def test_feed_accepts_1064_distinct_jobs_without_per_subscriber_id_set():
    async def run():
        bus = EventBus()
        scope = TrustedFeedScope(OWNER)
        sub = bus.subscribe(scope, bus.cursor)
        for _ in range(1064):
            value = envelope()
            bus.publish(trusted(value))
            record = await asyncio.wait_for(sub.next(), 1)
            assert value["job_id"].encode() in encode_frame(record, scope)
        assert len(bus._ring) == 256 and not sub._pending
        assert not hasattr(scope, "job_ids")
        sub.close()

    asyncio.run(run())


def test_feed_replay_deepcopy_certification_and_private_metadata():
    async def run():
        bus = EventBus()
        cursor = bus.cursor
        original = envelope()
        certified = trusted(original)
        original["job_id"] = new_id()
        bus.publish(deepcopy(certified))
        sub = bus.subscribe(TrustedFeedScope(OWNER, SONG), cursor)
        record = await asyncio.wait_for(sub.next(), 1)
        assert record.envelope["job_id"] != original["job_id"]
        frame = encode_frame(record, sub.scope)
        assert b"owner_id" not in frame and b"public_scope_verified" not in frame
        record.envelope["job_id"] = new_id()
        assert encode_frame(record, sub.scope) is None
        sub.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "fault", ["plain", "flag", "foreign_owner", "foreign_song", "delta", "system"]
)
def test_feed_denies_uncertified_and_foreign_or_escalating_records(fault):
    async def run():
        bus = EventBus()
        scope = TrustedFeedScope(OWNER, SONG)
        sub = bus.subscribe(scope, bus.cursor)
        value = envelope()
        if fault == "flag":
            value.update(owner_id=OWNER, song_id=SONG, public_scope_verified=True)
        elif fault == "delta":
            value.update(type="job.delta", data={"text": "private prompt"})
        elif fault == "system":
            value.update(type="system.status", data={"status": "ready"})
        if fault in {"plain", "flag"}:
            bus.publish(value)
        elif fault in {"delta", "system"}:
            with pytest.raises(PublicPayloadError):
                trusted(value)
        else:
            bus.publish(
                trusted(
                    value,
                    owner=new_id() if fault == "foreign_owner" else OWNER,
                    song=new_id() if fault == "foreign_song" else SONG,
                )
            )
        assert not sub._pending and not sub._replay
        sub.close()

    asyncio.run(run())


@pytest.mark.parametrize("bad", [None, {}, lambda _: True, TrustedScope("local")])
def test_feed_scope_is_explicit_and_validated(bad):
    with pytest.raises(PublicPayloadError):
        TrustedFeedScope(bad)


@pytest.mark.parametrize(
    "fault", ["job", "song", "owner", "entity_id", "entity_type", "data_id", "ts"]
)
def test_certification_rejects_spoofed_canonical_identity(fault):
    value = envelope()
    owner, song = OWNER, SONG
    if fault == "job":
        value["job_id"] = "path/to/job"
    if fault == "song":
        song = "private"
    if fault == "owner":
        owner = True
    if fault in {"entity_id", "entity_type", "data_id"}:
        value.update(
            type="entity.updated",
            entity_id=new_id(),
            data={"type": "take", "id": new_id()},
        )
        if fault != "data_id":
            value["data"]["id"] = value["entity_id"]
        if fault == "entity_id":
            value["entity_id"] = value["data"]["id"] = "path"
        if fault == "entity_type":
            value["data"]["type"] = "system"
    if fault == "ts":
        value["ts"] = "invalid"
    with pytest.raises(PublicPayloadError):
        trusted(value, owner, song)


def test_certified_entity_updated_has_canonical_public_pair():
    async def run():
        bus = EventBus()
        scope = TrustedFeedScope(OWNER)
        sub = bus.subscribe(scope, bus.cursor)
        identity = new_id()
        value = {
            "entity_id": identity,
            "type": "entity.updated",
            "ts": STAMP,
            "data": {"type": "take", "id": identity, "path": "/private"},
        }
        bus.publish(trusted(value))
        frame = encode_frame(await asyncio.wait_for(sub.next(), 1), scope)
        assert json.loads(frame.split(b"data: ")[1])["data"] == {
            "type": "take",
            "id": identity,
        }
        sub.close()

    asyncio.run(run())


@pytest.mark.parametrize("authority", [True, None, {}, ("owner", "song")])
def test_forged_certification_is_rejected_without_permission_or_uncaught_error(
    authority,
):
    bus = EventBus()
    old = bus.epoch
    bus.publish(CertifiedPublication(envelope(), authority))
    assert bus.epoch != old and not bus._ring


def test_mutated_certificate_cannot_change_identity_or_owner():
    for key, value in [
        ("job_id", new_id()),
        ("owner_id", new_id()),
        ("song_id", new_id()),
        ("type", "system.status"),
    ]:
        bus = EventBus()
        certified = trusted(envelope())
        certified.envelope[key] = value
        old = bus.epoch
        bus.publish(certified)
        assert bus.epoch != old and not bus._ring
