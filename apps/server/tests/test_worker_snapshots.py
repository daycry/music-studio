"""Snapshots U2b1: cierre real SQLite, historial y campos privados."""

import json
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app import models, snapshots
from app.db import create_db_engine
from jsonschema import ValidationError as SchemaValidationError
from sqlalchemy import event
from test_job_attempt_schema import engine as _legacy_engine
from test_worker_publication_invariants import (
    EXECUTION,
    INTENT,
    JOB,
    REVISION,
    SONG,
    execution,
    reserve,
)
from test_worker_publication_invariants import (
    engine as _publication_engine,
)

engine = _publication_engine
legacy_engine = _legacy_engine


def test_portable_row_drops_operational_identity():
    row = execution()
    projected = snapshots.canonical_row(row)
    assert set(projected) == set(row) - {
        "supervisor_epoch",
        "lease_token",
        "process_identity",
        "cleanup_state",
    }
    assert "private-lease" not in json.dumps(projected)


def test_snapshot_causal_closure_private_roundtrip(engine):
    reserve(engine)
    directory = Path(engine.url.database).parent
    document = snapshots.project(engine, SONG)
    assert [v["id"] for v in document["rows"]["cpu_execution"]] == [EXECUTION]
    assert [v["id"] for v in document["rows"]["publication_intent"]] == [INTENT]
    assert [v["id"] for v in document["rows"]["publication_intent_revision"]] == [
        REVISION
    ]
    assert all(
        x not in json.dumps(document)
        for x in ("private-lease", "private-epoch", "process_identity", "cleanup_state")
    )
    snapshots.validate(document, directory)
    destination = directory / "restored.sqlite"
    snapshots.restore_new(destination, document, directory)
    restored = create_db_engine(destination)
    try:
        with restored.connect() as connection:
            row = connection.exec_driver_sql(
                "SELECT state,lease_token,supervisor_epoch,process_identity,cleanup_state FROM cpu_execution"
            ).one()
            assert row == ("interrupted", None, None, None, "unknown")
        after = snapshots.project(restored, SONG)
        assert (
            after["rows"]["publication_intent_revision"]
            == document["rows"]["publication_intent_revision"]
        )
        snapshots.restore(
            restored, document, directory
        )  # repeat portable import is idempotent
    finally:
        restored.dispose()


@pytest.mark.parametrize("fraud", ["winner", "index", "terminal", "secret", "package"])
def test_snapshot_validates_causal_fraud(engine, fraud):
    reserve(engine)
    doc = snapshots.project(engine, SONG)
    value = doc["rows"]["publication_intent_revision"][0]
    if fraud == "winner":
        value["winning_attempt_id"] = JOB
    if fraud == "index":
        value["output_index"] = 1
    if fraud == "terminal":
        value["terminal_sha256"] = "f" * 64
    if fraud == "secret":
        doc["rows"]["job_attempt"][0]["provenance"]["ciphertext"] = "private"
    if fraud == "package":
        value["package"] = {"token": "private"}
    with pytest.raises((ValueError, SchemaValidationError)):
        snapshots.validate(doc, Path(engine.url.database).parent)


def test_new_rows_dirty_and_backup_private(engine):
    from app.backup import backup, restore_backup

    directory = Path(engine.url.database).parent
    snapshots.publish(engine, SONG, directory)
    reserve(engine)
    with engine.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (SONG,)
            ).scalar_one()
            == 1
        )
    source = backup(Path(engine.url.database), directory / "backups")
    destination = directory / "backup.sqlite"
    restore_backup(source, destination)
    restored = create_db_engine(destination)
    try:
        with restored.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT lease_token FROM cpu_execution"
                ).scalar_one()
                == "private-lease"
            )
        assert snapshots.project(restored, SONG) == snapshots.project(engine, SONG)
    finally:
        restored.dispose()


def test_populated_0005_projection_and_upgrade(engine):
    config = Config()
    config.set_main_option(
        "script_location", str(Path(models.__file__).parents[1] / "migrations")
    )
    config.attributes["database_path"] = Path(engine.url.database)
    command.downgrade(config, "0005")
    before = snapshots.project(engine, SONG)
    attempt = before["rows"]["job_attempt"][0]
    assert "provenance" not in attempt and "provenance_sha256" not in attempt
    assert "error_code" not in before["rows"]["take"][0]
    with engine.connect() as connection:
        assert "provenance" not in [
            r[1] for r in connection.exec_driver_sql("PRAGMA table_info(job_attempt)")
        ]
    command.upgrade(config, "head")
    assert snapshots.project(engine, SONG) == before
    destination = Path(engine.url.database).parent / "legacy-restored.sqlite"
    snapshots.restore_new(destination, before, destination.parent)
    restored = create_db_engine(destination)
    try:
        assert snapshots.project(restored, SONG) == before
    finally:
        restored.dispose()


@pytest.mark.parametrize("count", [20, 200, 405])
def test_current_extensions_add_fixed_queries_without_per_attempt_calls(
    legacy_engine, count
):
    from test_job_attempt_schema import insert_raw, row

    for ordinal in range(1, count + 1):
        value = row()
        identifier = "01K700" + str(ordinal + 100).zfill(20)
        value.update(id=identifier, ordinal=ordinal)
        value["engine_request"].update(
            job_id=identifier, output_dir="tmp/" + identifier
        )
        insert_raw(legacy_engine, value)
    document = snapshots.project(legacy_engine, SONG)
    statements = []

    def observe(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(legacy_engine, "before_cursor_execute", observe)
    try:
        snapshots.restore(
            legacy_engine, document, Path(legacy_engine.url.database).parent
        )
    finally:
        event.remove(legacy_engine, "before_cursor_execute", observe)
    pages = (count + 399) // 400
    assert len(statements) == 29 + 3 * pages
    assert sum("FROM job_attempt" in s for s in statements) == pages + 1
    for table in ("cpu_execution", "publication_intent", "publication_intent_revision"):
        assert sum("FROM " + table + " \n" in s for s in statements) == 1
    assert sum("pragma_table_info" in s for s in statements) == 1
    assert snapshots.project(legacy_engine, SONG) == document
    coverage_file = os.environ.get("COVERAGE_FILE")
    folder = (
        Path(coverage_file).parent
        if coverage_file
        else Path(".cache/pytest/sql-purpose")
    )
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"sql-purpose-{count}.json").write_text(
        json.dumps(
            {
                "count": count,
                "pages": pages,
                "statements": statements,
                "extension_queries": 3,
                "capability_query": 1,
            },
            indent=2,
        ),
        encoding="utf8",
    )
