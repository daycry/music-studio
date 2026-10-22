"""Contrato puro; no acredita ensamblado SQL ni autorización del contenido."""

import json
import math
import os
from pathlib import Path

import pytest
from app.event_dtos import (
    JobStateDTO,
    SessionCredentialDTO,
    SnapshotControlDTO,
    encode_snapshot_control,
)
from pydantic import ValidationError

ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEX = "a" * 32
STAMP = "2026-10-09T00:00:00.123Z"


def job(**changes):
    return dict(
        job_id=ULID,
        song_id=ULID,
        status="running",
        attempt_id=None,
        stage=None,
        progress=None,
        error_code=None,
        **changes,
    )


def control(phase="begin", **changes):
    data = {"status": "snapshot", "phase": phase, "snapshot_id": HEX}
    if phase == "begin":
        data.update(reason="bootstrap", active_count=0, known_count=0, chunk_count=0)
    elif phase == "chunk":
        data.update(index=0, jobs=[job()])
    else:
        data.update(chunk_count=0, cursor=f"{HEX}:1")
    data.update(changes)
    return {"id": 1, "type": "system.status", "ts": STAMP, "data": data}


def test_unknown_null_preserved_and_canonical_fields():
    dto = JobStateDTO(**job())
    assert list(dto.model_dump()) == [
        "job_id",
        "song_id",
        "status",
        "attempt_id",
        "stage",
        "progress",
        "error_code",
    ]
    assert dto.model_dump()["progress"] is None
    assert json.loads(dto.model_dump_json()) == job()


@pytest.mark.parametrize(
    "key",
    [
        "request",
        "terminal",
        "owner_id",
        "raw_path",
        "error_message",
        "lyrics",
        "telemetry",
        "engine_token",
    ],
)
def test_private_extra_fields_rejected(key):
    value = job()
    value[key] = "private_secret"
    with pytest.raises(ValidationError):
        JobStateDTO(**value)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("progress", True),
        ("progress", "0.5"),
        ("progress", math.nan),
        ("progress", math.inf),
        ("progress", -0.1),
        ("progress", 1.1),
        ("stage", "x" * 65),
        ("stage", "raw/path"),
        ("stage", "\ud800"),
        ("error_code", "é"),
        ("error_code", "a\nb"),
        ("status", "done"),
        ("job_id", "8" + "A" * 25),
        ("song_id", "local"),
        ("attempt_id", True),
    ],
)
def test_strict_job_bounds(field, bad):
    value = job()
    value[field] = bad
    with pytest.raises(ValidationError):
        JobStateDTO(**value)


@pytest.mark.parametrize(
    "status",
    ["queued", "blocked", "running", "interrupted", "succeeded", "failed", "cancelled"],
)
def test_valid_public_job_status(status):
    value = job()
    value.update(
        status=status,
        attempt_id=ULID,
        progress=1,
        stage="render",
        error_code="PUBLIC_FAILURE",
    )
    assert JobStateDTO(**value).model_dump() == value


def test_credential_exact_schema():
    dto = SessionCredentialDTO(session_token="public_token", expires_in_s=28800)
    assert dto.model_dump() == {"session_token": "public_token", "expires_in_s": 28800}
    assert "public_token" not in repr(dto)
    with pytest.raises(ValidationError):
        SessionCredentialDTO(
            session_token="public_token", expires_in_s=28800, owner_id=ULID
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"session_token": "a\nb"},
        {"session_token": "x" * 65},
        {"session_token": "\ud800"},
        {"expires_in_s": True},
        {"expires_in_s": "28800"},
        {"expires_in_s": 0},
        {"expires_in_s": 28801},
        {"expires_in_s": math.inf},
    ],
)
def test_credential_strict_bounds(changes):
    value = {"session_token": "public_token", "expires_in_s": 28800}
    value.update(changes)
    with pytest.raises(ValidationError):
        SessionCredentialDTO(**value)


@pytest.mark.parametrize("phase", ["begin", "chunk", "end"])
def test_controls_frame_phase_and_wire_commit(phase):
    value = control(phase)
    dto = SnapshotControlDTO(**value)
    frame = encode_snapshot_control(dto)
    assert frame.startswith(b"event: system.status\n")
    assert frame.endswith(b"\n\n")
    lines = frame.decode("utf-8").splitlines()
    assert (
        json.loads(next(line[6:] for line in lines if line.startswith("data: ")))
        == value
    )
    ids = [line for line in lines if line.startswith("id:")]
    assert ids == ([f"id: {HEX}:1"] if phase == "end" else [])


@pytest.mark.parametrize(
    "phase,key,bad",
    [
        ("begin", "active_count", 1001),
        ("begin", "active_count", True),
        ("begin", "known_count", 65),
        ("begin", "chunk_count", 18),
        ("begin", "reason", "invalid"),
        ("begin", "snapshot_id", "a" * 33),
        ("chunk", "index", 17),
        ("chunk", "index", -1),
        ("chunk", "jobs", []),
        ("chunk", "jobs", [job()] * 65),
        ("end", "cursor", f"{HEX}:2"),
        ("end", "cursor", f"{HEX}:0"),
        ("end", "cursor", f"{HEX}:9007199254740992"),
        ("end", "cursor", f"{HEX}:1\nid: evil"),
        ("end", "chunk_count", True),
    ],
)
def test_control_data_bounds(phase, key, bad):
    with pytest.raises(ValidationError):
        SnapshotControlDTO(**control(phase, **{key: bad}))


@pytest.mark.parametrize(
    "key,bad",
    [
        ("id", 0),
        ("id", True),
        ("id", "1"),
        ("id", 9007199254740992),
        ("type", "job.progress"),
        ("ts", "2026-10-09T00:00:00Z"),
        ("ts", "2026-02-30T00:00:00.123Z"),
        ("ts", "2026-10-09T00:00:00.123+00:00"),
        ("ts", "x\ndata: secret"),
    ],
)
def test_control_envelope_bounds(key, bad):
    value = control()
    value[key] = bad
    with pytest.raises(ValidationError):
        SnapshotControlDTO(**value)


def test_control_closed_discriminator_and_schema():
    for where in ("outer", "inner"):
        value = control()
        target = value if where == "outer" else value["data"]
        target["engine_token"] = "secret"
        with pytest.raises(ValidationError):
            SnapshotControlDTO(**value)
    with pytest.raises(ValidationError):
        SnapshotControlDTO(**control("unknown"))
    schema = SnapshotControlDTO.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["data"]["discriminator"]["propertyName"] == "phase"
    assert all(
        item.get("additionalProperties") is False
        for item in schema["$defs"].values()
        if item.get("type") == "object"
    )


def test_worst_chunk_encoded_and_empty_snapshot():
    value = job()
    value.update(
        job_id="7" + "Z" * 25,
        song_id="7" + "Z" * 25,
        attempt_id="7" + "Z" * 25,
        status="interrupted",
        stage="X" * 64,
        error_code="E" * 64,
        progress=1.2345678901234567e-100,
    )
    chunk = control("chunk", index=16, jobs=[value] * 64)
    chunk["id"] = 9007199254740991
    dto = SnapshotControlDTO(**chunk)
    frame = encode_snapshot_control(dto)
    assert len(frame) < 65536
    artifact = Path(os.environ["STUDIO_TEST_ROOT"])
    (artifact / "worst-chunk.sse").write_bytes(frame)
    (artifact / "worst-chunk.json").write_text(dto.model_dump_json(), encoding="utf-8")
    assert math.ceil((1000 + 64) / 64) == 17
    for phase in ("begin", "end"):
        assert (
            len(encode_snapshot_control(SnapshotControlDTO(**control(phase)))) < 65536
        )


def test_end_cursor_max_safe_and_repeated_body_id():
    value = control("end", cursor=f"{HEX}:9007199254740991", chunk_count=17)
    value["id"] = 9007199254740991
    assert b"id: " + value["data"]["cursor"].encode() in encode_snapshot_control(
        SnapshotControlDTO(**value)
    )
    assert (
        SnapshotControlDTO(**control("begin")).id
        == SnapshotControlDTO(**control("chunk")).id
        == 1
    )
