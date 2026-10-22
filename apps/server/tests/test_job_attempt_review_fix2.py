"""R04-B02: calendario durable y Common legibles tras SQL nativo."""

import json
import sqlite3
from datetime import datetime

import pytest
from app import models
from app.migrations.job_attempt_invariants import validate_attempt
from engine_contract import Event
from sqlalchemy.orm import Session
from test_job_attempt_review_fix1 import engine as attempt_engine
from test_job_attempt_schema import ATTEMPT, error, insert_raw, row

INVALID = [
    "2026-02-30T00:00:00Z",
    "2026-02-29T00:00:00Z",
    "2024-02-30T00:00:00Z",
    "2024-02-31T00:00:00Z",
    "2026-04-31T00:00:00Z",
    "1900-02-29T00:00:00Z",
    "0000-01-01T00:00:00Z",
    "2026-01-01T24:00:00Z",
    "2026-01-01T00:60:00Z",
    "2026-01-01T00:00:60Z",
]
VALID = [
    "2000-02-29T00:00:00Z",
    "2024-02-29T23:59:59Z",
    "1900-02-28T23:59:59Z",
    "0001-01-01T00:00:00Z",
    "9999-12-31T23:59:59Z",
    "2026-04-30T23:59:59Z",
    "2026-03-01T00:00:00.1Z",
    "2024-02-29T12:34:56.123456Z",
    "2024-02-29T12:34:56.123456789Z",
]


@pytest.fixture
def engine():
    yield from attempt_engine.__wrapped__()


def write_timestamp(engine, field, timestamp, operation):
    value = row()
    if field == "terminal":
        terminal = error()
        terminal["ts"] = timestamp
        changes = {"status": "failed", "last_seq": 4, "terminal": terminal}
    else:
        changes = {field: timestamp}
    if operation == "insert":
        value.update(changes)
        insert_raw(engine, value)
    else:
        insert_raw(engine, value)
        with sqlite3.connect(engine.url.database) as connection:
            connection.execute(
                "UPDATE job_attempt SET "
                + ",".join(k + "=?" for k in changes)
                + " WHERE id=?",
                tuple(
                    json.dumps(v) if k == "terminal" else v for k, v in changes.items()
                )
                + (ATTEMPT,),
            )


@pytest.mark.parametrize("operation", ["insert", "update"])
@pytest.mark.parametrize("timestamp", INVALID)
def test_impossible_terminal_sql(engine, operation, timestamp):
    terminal = error()
    terminal["ts"] = timestamp
    with pytest.raises(ValueError):
        Event.model_validate_json(json.dumps(terminal), strict=True)
    with pytest.raises(sqlite3.IntegrityError):
        write_timestamp(engine, "terminal", timestamp, operation)


@pytest.mark.parametrize("field", ["created_at", "updated_at", "deleted_at"])
@pytest.mark.parametrize("operation", ["insert", "update"])
def test_impossible_common_sql(engine, field, operation):
    timestamp = "2026-02-30T00:00:00Z"
    with pytest.raises(ValueError):
        validate_attempt(row() | {field: timestamp})
    with pytest.raises(sqlite3.IntegrityError):
        write_timestamp(engine, field, timestamp, operation)


@pytest.mark.parametrize("timestamp", VALID)
@pytest.mark.parametrize("operation", ["insert", "update"])
def test_valid_terminal_sql_readable(engine, timestamp, operation):
    write_timestamp(engine, "terminal", timestamp, operation)
    with Session(engine) as session:
        actual = session.get(models.JobAttempt, ATTEMPT)
        assert actual.status == "failed"
        assert actual.last_seq == 4
        assert actual.terminal.ts == datetime.fromisoformat(timestamp)
        assert actual.terminal.type == "error"


@pytest.mark.parametrize("timestamp", VALID)
@pytest.mark.parametrize("field", ["created_at", "updated_at", "deleted_at"])
def test_valid_common_sql_readable(engine, timestamp, field):
    write_timestamp(engine, field, timestamp, "insert")
    with Session(engine) as session:
        actual = session.get(models.JobAttempt, ATTEMPT)
        assert getattr(actual, field) == timestamp
        assert actual.status == "prepared"
        assert actual.terminal is None
