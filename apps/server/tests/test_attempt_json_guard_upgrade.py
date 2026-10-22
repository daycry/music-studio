"""Rechazo SQL portable de sintaxis JSON; preparación privada T-04."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
import test_job_attempt_schema as baseline
from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.engine import Engine

LEGACY_GUARDS_SHA256 = (
    "d308741ee5114969a7055b486db7089b7acf1ae4f83b386e11ec586e663c95da"
)


@pytest.fixture
def engine(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "PHASE", tmp_path)
    fixture = baseline.engine.__wrapped__()
    result = next(fixture)
    try:
        yield result
    finally:
        try:
            next(fixture)
        except StopIteration:
            pass


@pytest.mark.parametrize("operation", ["INSERT", "UPDATE", "REPLACE"])
@pytest.mark.parametrize("column", ["engine_request", "load_options", "terminal"])
@pytest.mark.parametrize("raw", ["{", '{"bad":Infinity}', '{"bad":NaN}'])
def test_invalid_json_is_atomic_integrity_error(engine, operation, column, raw):
    if operation == "UPDATE":
        baseline.insert_raw(engine, baseline.row())
    value = baseline.row()
    encoded = {
        key: json.dumps(item)
        if key in {"engine_request", "load_options", "terminal"} and item is not None
        else item
        for key, item in value.items()
    }
    encoded[column] = raw
    with sqlite3.connect(engine.url.database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        before = connection.execute("SELECT * FROM job_attempt ORDER BY id").fetchall()
        clock = connection.execute("SELECT * FROM snapshot_clock").fetchall()
        songs = connection.execute("SELECT * FROM song ORDER BY id").fetchall()
        if operation == "UPDATE":
            statement = f"UPDATE job_attempt SET {column}=? WHERE id=?"
            parameters = (raw, baseline.ATTEMPT)
        else:
            verb = "INSERT OR REPLACE" if operation == "REPLACE" else "INSERT"
            statement = (
                verb
                + " INTO job_attempt ("
                + ",".join(encoded)
                + ") VALUES ("
                + ",".join("?" for _ in encoded)
                + ")"
            )
            parameters = tuple(encoded.values())
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(statement, parameters)
        assert (
            connection.execute("SELECT * FROM job_attempt ORDER BY id").fetchall()
            == before
        )
        assert connection.execute("SELECT * FROM snapshot_clock").fetchall() == clock
        assert connection.execute("SELECT * FROM song ORDER BY id").fetchall() == songs
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]


def migration_config(engine):
    config = Config()
    config.set_main_option(
        "script_location", str(Path(baseline.__file__).parent.parent / "app/migrations")
    )
    config.attributes["database_path"] = Path(engine.url.database)
    return config


def custody(engine):
    with sqlite3.connect(engine.url.database) as connection:
        schema = connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT IN ('attempt_validate_insert','attempt_validate_update') "
            "ORDER BY type,name"
        ).fetchall()
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name!='alembic_version' ORDER BY name"
        ).fetchall()
        rows = {}
        for (name,) in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            rows[name] = sorted(
                connection.execute("SELECT * FROM " + quoted).fetchall(), key=repr
            )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        return schema, rows


def guards(engine):
    with sqlite3.connect(engine.url.database) as connection:
        return dict(
            connection.execute(
                "SELECT name,sql FROM sqlite_master WHERE name IN "
                "('attempt_validate_insert','attempt_validate_update')"
            ).fetchall()
        )


def assert_legacy_guards(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == LEGACY_GUARDS_SHA256


def populated(engine):
    baseline.insert_raw(engine, baseline.row())
    with sqlite3.connect(engine.url.database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("UPDATE job_attempt SET status='submitted',last_seq=3")
        connection.execute(
            "UPDATE job_attempt SET status='failed',last_seq=4,terminal=?",
            (json.dumps(baseline.error()),),
        )


@pytest.mark.parametrize("has_data", [False, True])
def test_upgrade_downgrade_preserves_custody_and_legacy_guards(engine, has_data):
    config = migration_config(engine)
    command.downgrade(config, "0006")
    original_guards = guards(engine)
    assert_legacy_guards(original_guards)
    if has_data:
        populated(engine)
    before = custody(engine)
    command.upgrade(config, "head")
    assert custody(engine) == before
    current = guards(engine)
    assert set(current) == set(original_guards)
    for name, original in original_guards.items():
        prefix = "".join(
            f'SELECT RAISE(ABORT,\'Invalid attempt JSON\') WHERE NEW."{column}" IS NOT NULL AND NOT json_valid(NEW."{column}");'
            for column in ("engine_request", "load_options", "terminal")
        )
        assert current[name] == original.replace(" BEGIN ", " BEGIN " + prefix, 1)
    command.downgrade(config, "0006")
    assert guards(engine) == original_guards
    assert custody(engine) == before
    command.upgrade(config, "head")
    assert guards(engine) == current
    assert custody(engine) == before


def test_upgrade_failure_rolls_back_both_guards_and_version(engine):
    config = migration_config(engine)
    command.downgrade(config, "0006")
    populated(engine)
    before = custody(engine)
    original = guards(engine)

    def reject_second_create(connection, cursor, statement, parameters, context, many):
        if (
            statement.startswith("CREATE TRIGGER attempt_validate_update")
            and "Invalid attempt JSON" in statement
        ):
            raise RuntimeError("injected second guard failure")

    event.listen(Engine, "before_cursor_execute", reject_second_create)
    try:
        with pytest.raises(RuntimeError, match="injected second guard failure"):
            command.upgrade(config, "head")
    finally:
        event.remove(Engine, "before_cursor_execute", reject_second_create)
    assert guards(engine) == original
    assert custody(engine) == before
    with sqlite3.connect(engine.url.database) as connection:
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() == [("0006",)]


def test_valid_attempt_lifecycle_and_replace_remain_guarded(engine):
    populated(engine)
    before = custody(engine)
    with pytest.raises(sqlite3.IntegrityError):
        value = baseline.row()
        encoded = {
            key: json.dumps(item)
            if key in {"engine_request", "load_options", "terminal"}
            and item is not None
            else item
            for key, item in value.items()
        }
        with sqlite3.connect(engine.url.database) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO job_attempt ("
                + ",".join(encoded)
                + ") VALUES ("
                + ",".join("?" for _ in encoded)
                + ")",
                tuple(encoded.values()),
            )
    assert custody(engine) == before
    value = baseline.row()
    value["id"] = "01K70000000000000000000004"
    value["ordinal"] = 2
    value["engine_request"]["job_id"] = value["id"]
    value["engine_request"]["output_dir"] = "tmp/" + value["id"]
    baseline.insert_raw(engine, value)
    with sqlite3.connect(engine.url.database) as connection:
        assert connection.execute(
            "SELECT id,status,last_seq FROM job_attempt ORDER BY ordinal"
        ).fetchall() == [(baseline.ATTEMPT, "failed", 4), (value["id"], "prepared", 0)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
