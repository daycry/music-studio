"""Regresión R04-S01: fechas explícitas en el sobre durable, wire intacto."""

import copy
import json
import sqlite3
from pathlib import Path

import pytest
from app import models, snapshots
from app.backup import backup, restore_backup
from app.db import create_db_engine
from app.migrations.job_attempt_invariants import validate_contract
from engine_contract import Event
from jsonschema import Draft202012Validator
from jsonschema import ValidationError as SchemaValidationError
from sqlalchemy.orm import Session
from test_job_attempt_schema import ATTEMPT, SONG, error, insert_raw, row
from test_job_attempt_schema import engine as attempt_engine

EXPECTED_ERROR = b'{"data":{"code":"INTERNAL","message":"fixture","retryable":false},"job_id":"01K70000000000000000000003","seq":4,"ts":"2026-10-07T00:00:00Z","type":"error"}'


@pytest.fixture
def engine():
    yield from attempt_engine.__wrapped__()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@pytest.mark.parametrize("operation", ["insert", "update"])
def test_missing_ts_sql_rejected(engine, operation):
    terminal = error()
    del terminal["ts"]
    if operation == "insert":
        value = row()
        value.update(status="failed", last_seq=4, terminal=terminal)
        with pytest.raises(sqlite3.IntegrityError):
            insert_raw(engine, value)
    else:
        insert_raw(engine, row())
        with (
            sqlite3.connect(engine.url.database) as connection,
            pytest.raises(sqlite3.IntegrityError),
        ):
            connection.execute(
                "UPDATE job_attempt SET status='failed',last_seq=4,terminal=? WHERE id=?",
                (json.dumps(terminal), ATTEMPT),
            )
        assert snapshots.project(engine, SONG)["rows"]["job_attempt"] == [row()]


@pytest.mark.parametrize("boundary", ["helper", "orm", "snapshot"])
def test_missing_ts_durable_rejected(engine, boundary):
    terminal = error()
    del terminal["ts"]
    value = row()
    value.update(status="failed", last_seq=4, terminal=terminal)
    expected_error = SchemaValidationError if boundary == "snapshot" else ValueError
    with pytest.raises(expected_error):
        if boundary == "helper":
            validate_contract(terminal, "event")
        elif boundary == "orm":
            models.JobAttempt(**value)
        else:
            document = snapshots.project(engine, SONG)
            document["rows"]["job_attempt"] = [value]
            snapshots.validate(document, Path(engine.url.database).parent)


@pytest.mark.parametrize(
    "timestamp", [None, "invalid", "2026-10-07T00:00:00", "2026-10-07T01:00:00+01:00"]
)
def test_invalid_ts_sql_and_helper(engine, timestamp):
    terminal = error()
    terminal["ts"] = timestamp
    with pytest.raises(ValueError):
        validate_contract(terminal, "event")
    value = row()
    value.update(status="failed", last_seq=4, terminal=terminal)
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)


EXPECTED_CANCELLED = b'{"data":{"telemetry":{"extra":{},"load_s":0.0,"mode":"bf16","model_revision":"fixture","rtf":null,"run_s":0.0,"spilled":false,"vram_cap_mb":0.0,"vram_peak_mb":0.0}},"job_id":"01K70000000000000000000003","seq":4,"ts":"2026-10-07T00:00:00Z","type":"cancelled"}'
EXPECTED_DONE = b'{"data":{"artifacts":[],"result":null,"telemetry":{"extra":{},"load_s":0.0,"mode":"bf16","model_revision":"fixture","rtf":null,"run_s":0.0,"spilled":false,"vram_cap_mb":0.0,"vram_peak_mb":0.0}},"job_id":"01K70000000000000000000003","seq":4,"ts":"2026-10-07T00:00:00Z","type":"done"}'


@pytest.mark.parametrize(
    "status,expected_bytes",
    [
        ("failed", EXPECTED_ERROR),
        ("cancelled", EXPECTED_CANCELLED),
        ("succeeded", EXPECTED_DONE),
    ],
)
def test_stable_terminal_reads_project_restore_backup(engine, status, expected_bytes):
    terminal = json.loads(expected_bytes)
    assert canonical(terminal) == expected_bytes
    value = row()
    value.update(status=status, last_seq=4, terminal=terminal)
    insert_raw(engine, value)
    for _ in range(3):
        with Session(engine) as session:
            actual = session.get(models.JobAttempt, ATTEMPT).terminal
            assert type(actual) is Event
            assert canonical(actual.model_dump(mode="json")) == expected_bytes
    document = snapshots.project(engine, SONG)
    assert document["rows"]["job_attempt"] == [value]
    expected_document_bytes = canonical(document)
    for _ in range(3):
        assert canonical(snapshots.project(engine, SONG)) == expected_document_bytes
    directory = Path(engine.url.database).parent
    snapshot_db = directory / "snapshot-restored.sqlite"
    snapshots.restore_new(snapshot_db, copy.deepcopy(document), directory)
    backup_db = directory / "backup-restored.sqlite"
    archive = backup(Path(engine.url.database), directory / "backups")
    restore_backup(archive, backup_db)
    for destination in (snapshot_db, backup_db):
        restored = create_db_engine(destination)
        try:
            for _ in range(2):
                assert (
                    canonical(snapshots.project(restored, SONG))
                    == expected_document_bytes
                )
            snapshots.restore(restored, copy.deepcopy(document), directory)
            assert (
                canonical(snapshots.project(restored, SONG)) == expected_document_bytes
            )
        finally:
            restored.dispose()


def test_materialized_wire_event_accepted(engine):
    terminal = error()
    del terminal["ts"]
    actual = Event.model_validate(terminal)
    assert "ts" not in Event.model_json_schema()["required"]
    assert type(validate_contract(actual, "event")) is Event
    value = row()
    value.update(status="failed", last_seq=4, terminal=actual)
    with Session(engine) as session:
        session.add(models.JobAttempt(**value))
        session.commit()
    with Session(engine) as session:
        assert session.get(models.JobAttempt, ATTEMPT).terminal.ts == actual.ts


def test_durable_schema_requires_ts_only_in_attempt(engine):
    paths = [
        Path("packages/contracts/song-v1.schema.json"),
        Path("apps/server/app/models/song-v1.schema.json"),
    ]
    assert paths[0].read_bytes() == paths[1].read_bytes()
    schema = json.loads(paths[0].read_bytes())
    assert "ts" in schema["$defs"]["attempt_Event"]["required"]
    validator = Draft202012Validator(schema)
    document = snapshots.project(engine, SONG)
    validator.validate(document)
    insert_raw(engine, row())
    document = snapshots.project(engine, SONG)
    validator.validate(document)
    value = document["rows"]["job_attempt"][0]
    value.update(status="failed", last_seq=4, terminal=error())
    validator.validate(document)
    del value["terminal"]["ts"]
    assert list(validator.iter_errors(document))
