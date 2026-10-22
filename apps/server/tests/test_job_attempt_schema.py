"""Identidad durable e invariantes de intentos, sin ejecutar dispatcher."""

import copy
import hashlib
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app import models, snapshots
from app.db import create_db_engine, migrate
from jsonschema import ValidationError as SchemaValidationError
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

PHASE = Path.cwd() / ".cache/dev-cycle/m1/t04-attempts-unit"
OWNER = "01K70000000000000000000000"
SONG = "01K70000000000000000000001"
JOB = "01K70000000000000000000002"
ATTEMPT = "01K70000000000000000000003"
UTC = "2026-10-07T00:00:00.000000Z"
# Golden congelado de 0004, capturado antes de añadir la relación.
BASELINE_DDL_SHA256 = "2c233c2899c0e21a2ed6a89da0ed04e199fbe583212471b10bf4d0ff62c15d08"
LEGACY_SNAPSHOT = json.loads(
    '{"rows":{"analysis":[],"artwork":[],"asset":[],"character":[],"character_ref":[],"collection":[],"export":[],"job":[{"attempt":0,"cancel_requested_at":null,"created_at":"2026-10-07T00:00:00.000000Z","deleted_at":null,"engine_id":null,"error":null,"error_code":null,"finished_at":null,"id":"01K70000000000000000000002","lane":"gpu","max_attempts":3,"model_id":null,"not_before":null,"owner_id":"01K70000000000000000000000","priority":"normal","progress":null,"request":{"seed":17},"song_id":"01K70000000000000000000001","stage":null,"started_at":null,"status":"running","task":"music.instrumental","telemetry":null,"updated_at":"2026-10-07T00:00:00.000000Z"}],"job_dependency":[],"lineage_edge":[],"lyrics_version":[],"render":[],"shot":[],"shot_version":[],"song":[{"artist":null,"collection_id":null,"cover_artwork_id":null,"created_at":"2026-10-07T00:00:00.000000Z","current_lyrics_version_id":null,"deleted_at":null,"id":"01K70000000000000000000001","language":null,"master_take_id":null,"negative_prompt":null,"notes":null,"owner_id":"01K70000000000000000000000","rev":1,"status":"draft","style_prompt":"","tags":[],"title":"Fixture","updated_at":"2026-10-07T00:00:00.000000Z"}],"take":[],"upload":[],"user":[{"created_at":"2026-10-07T00:00:00.000000Z","deleted_at":null,"id":"01K70000000000000000000000","name":"local","owner_id":"01K70000000000000000000000","updated_at":"2026-10-07T00:00:00.000000Z"}],"video_character":[],"video_project":[]},"song_id":"01K70000000000000000000001","version":1}'
)


def ddl_hash(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


@pytest.fixture
def engine():
    directory = PHASE / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    database = directory / "studio.sqlite"
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(
            models.Song(
                id=SONG, owner_id=OWNER, title="Fixture", created_at=UTC, updated_at=UTC
            )
        )
        session.flush()
        session.add(
            models.Job(
                id=JOB,
                owner_id=OWNER,
                song_id=SONG,
                task="music.instrumental",
                lane="gpu",
                request={"seed": 17},
                status="running",
                created_at=UTC,
                updated_at=UTC,
            )
        )
        session.commit()
    try:
        yield engine
    finally:
        engine.dispose()


def request():
    return {
        "job_id": ATTEMPT,
        "task": "music.instrumental",
        "model_id": "mock",
        "mode": "bf16",
        "inputs": [
            {
                "role": "reference",
                "path": "uploads/reference.wav",
                "sha256": "a" * 64,
                "media_type": "audio/wav",
            }
        ],
        "params": {"duration_s": 30},
        "seed": 17,
        "n_outputs": 2,
        "output_dir": "tmp/" + ATTEMPT,
        "timeout_s": 60,
    }


def row():
    return {
        "id": ATTEMPT,
        "owner_id": OWNER,
        "created_at": UTC,
        "updated_at": UTC,
        "deleted_at": None,
        "job_id": JOB,
        "ordinal": 1,
        "engine_id": "mock",
        "model_id": "mock",
        "mode": "bf16",
        "engine_request": request(),
        "load_options": {"model_id": "mock", "mode": "bf16"},
        "last_seq": 0,
        "status": "prepared",
        "terminal": None,
    }


def error():
    return {
        "seq": 4,
        "ts": "2026-10-07T00:00:00Z",
        "job_id": ATTEMPT,
        "type": "error",
        "data": {"code": "INTERNAL", "message": "fixture", "retryable": False},
    }


def insert_raw(engine, value):
    assert "job_attempt" in inspect(engine).get_table_names(), (
        "Durable attempts are absent"
    )
    encoded = {
        k: json.dumps(v)
        if k in {"engine_request", "load_options", "terminal"} and v is not None
        else v
        for k, v in value.items()
    }
    with sqlite3.connect(engine.url.database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT INTO job_attempt ("
            + ",".join(encoded)
            + ") VALUES ("
            + ",".join("?" for _ in encoded)
            + ")",
            tuple(encoded.values()),
        )


def test_attempt_typed_roundtrip(engine):
    assert hasattr(models, "JobAttempt"), "Typed attempt model is absent"
    with Session(engine) as session:
        attempt = models.JobAttempt(**row())
        session.add(attempt)
        session.commit()
        session.expire_all()
        restored = session.get(models.JobAttempt, ATTEMPT)
        from engine_contract import JobRequest, LoadRequest

        assert isinstance(restored.engine_request, JobRequest)
        assert isinstance(restored.load_options, LoadRequest)
        assert restored.engine_request.model_dump(mode="json") == request()
        assert (
            restored.status == "prepared"
            and restored.ordinal == 1
            and restored.last_seq == 0
        )
        with pytest.raises((ValueError, TypeError)):
            restored.engine_request.seed = 18


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "bad"),
        ("owner_id", "bad"),
        ("job_id", "bad"),
        ("ordinal", 0),
        ("ordinal", -1),
        ("ordinal", 1.5),
        ("last_seq", -1),
        ("last_seq", 0.5),
        ("status", "running"),
        ("created_at", "tomorrow"),
        ("updated_at", "2026-10-07T00:00:00+01:00"),
        ("deleted_at", "invalid"),
        ("engine_id", ""),
        ("model_id", ""),
        ("terminal", error()),
        ("status", "succeeded"),
    ],
)
def test_direct_sql_strict_common(engine, field, value):
    value_row = row()
    value_row[field] = value
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value_row)


@pytest.mark.parametrize(
    "mutation",
    [
        {"job_id": JOB},
        {"model_id": "other"},
        {"mode": "offload"},
        {"output_dir": "tmp/" + JOB},
        {"seed": -1},
        {"seed": "17"},
        {"seed": True},
        {"timeout_s": 0},
        {"timeout_s": "60"},
        {"n_outputs": 65},
        {"n_outputs": True},
        {"task": ""},
        {"params": []},
        {"params": {"bad": float("inf")}},
        {"params": {"authorization": "fixture"}},
        {
            "inputs": [
                {
                    "role": "reference",
                    "path": "../outside",
                    "sha256": "a" * 64,
                    "media_type": "audio/wav",
                }
            ]
        },
        {
            "inputs": [
                {
                    "role": "reference",
                    "path": "uploads/x",
                    "sha256": "A" * 64,
                    "media_type": "audio/wav",
                }
            ]
        },
        {
            "inputs": [
                {
                    "role": "reference",
                    "path": "C:/outside",
                    "sha256": "a" * 64,
                    "media_type": "audio/wav",
                }
            ]
        },
        {"unknown": 1},
    ],
)
def test_direct_sql_request_contract(engine, mutation):
    value = row()
    value["engine_request"].update(mutation)
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)


@pytest.mark.parametrize(
    "options",
    [
        {"model_id": "other", "mode": "bf16"},
        {"model_id": "mock", "mode": "offload"},
        {"model_id": "mock", "mode": 1},
        {"model_id": "mock", "token": "fixture"},
        {},
    ],
)
def test_direct_sql_load_contract(engine, options):
    value = row()
    value["load_options"] = options
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", "17"),
        ("n_outputs", True),
        ("timeout_s", "60"),
        ("params", {"bad": float("nan")}),
    ],
)
def test_orm_strict_request(engine, field, value):
    assert hasattr(models, "JobAttempt"), "Typed attempt model is absent"
    value_row = row()
    value_row["engine_request"][field] = value
    with pytest.raises((ValueError, StatementError)), Session(engine) as session:
        session.add(models.JobAttempt(**value_row))
        session.flush()


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", JOB),
        ("owner_id", JOB),
        ("job_id", ATTEMPT),
        ("ordinal", 2),
        ("engine_id", "other"),
        ("model_id", "other"),
        ("mode", "offload"),
        ("created_at", "2026-10-08T00:00:00Z"),
        ("engine_request", {**request(), "seed": 18}),
        ("load_options", {"model_id": "other", "mode": "bf16"}),
    ],
)
def test_sql_bulk_reservation_frozen(engine, field, value):
    insert_raw(engine, row())
    encoded = json.dumps(value) if isinstance(value, dict) else value
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            f"UPDATE job_attempt SET {field}=? WHERE id=?", (encoded, ATTEMPT)
        )
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT ordinal,last_seq,status FROM job_attempt"
        ).one() == (1, 0, "prepared")


@pytest.mark.parametrize(
    "mutation",
    [
        {"seq": 3},
        {"job_id": JOB},
        {"type": "stage", "data": {"stage": "generating"}},
        {"data": {"code": "UNKNOWN", "message": "bad", "retryable": False}},
        {"data": {"code": "INTERNAL", "message": "bad", "retryable": "false"}},
        {"ts": "2026-10-07T00:00:00+01:00"},
    ],
)
def test_terminal_contract_consistency(engine, mutation):
    value = row()
    terminal = error()
    terminal.update(mutation)
    value.update(last_seq=4, status="failed", terminal=terminal)
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)


def test_cursor_and_terminal_atomic_restore(engine):
    insert_raw(engine, row())
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET status='submitted',last_seq=3 WHERE id=?",
            (ATTEMPT,),
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET status='failed',terminal=? WHERE id=?",
            (json.dumps(error()), ATTEMPT),
        )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET status='failed',terminal=?,last_seq=4 WHERE id=?",
            (json.dumps(error()), ATTEMPT),
        )
    document = snapshots.project(engine, SONG)
    attempt = document["rows"]["job_attempt"][0]
    assert attempt == {**row(), "status": "failed", "last_seq": 4, "terminal": error()}
    snapshots.validate(document, Path(engine.url.database).parent)
    destination = Path(engine.url.database).parent / "restored.sqlite"
    snapshots.restore_new(destination, document, destination.parent)
    restored_engine = create_db_engine(destination)
    try:
        assert snapshots.project(restored_engine, SONG) == document
    finally:
        restored_engine.dispose()


def test_unique_ordinal_and_soft_delete(engine):
    insert_raw(engine, row())
    value = row()
    value["id"] = "01K70000000000000000000004"
    value["engine_request"]["job_id"] = value["id"]
    value["engine_request"]["output_dir"] = "tmp/" + value["id"]
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE job SET deleted_at=? WHERE id=?", (UTC, JOB))
        connection.exec_driver_sql(
            "UPDATE job_attempt SET deleted_at=? WHERE id=?", (UTC, ATTEMPT)
        )
    assert (
        snapshots.project(engine, SONG)["rows"]["job_attempt"][0]["deleted_at"] == UTC
    )


def test_owner_and_parent_guard(engine):
    value = row()
    value["owner_id"] = JOB
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, value)
    insert_raw(engine, row())
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql("UPDATE job SET owner_id=? WHERE id=?", (JOB, JOB))


def test_legacy_snapshot_without_attempts(engine):
    document = snapshots.project(engine, SONG)
    assert "job_attempt" in document["rows"], "New exports must include attempts"
    del document["rows"]["job_attempt"]
    snapshots.validate(document, Path(engine.url.database).parent)
    destination = Path(engine.url.database).parent / "legacy.sqlite"
    snapshots.restore_new(destination, document, destination.parent)
    restored = create_db_engine(destination)
    try:
        result = snapshots.project(restored, SONG)
        assert result["rows"]["job"][0]["status"] == "running"
        assert result["rows"]["job_attempt"] == []
        assert {
            k: v for k, v in result["rows"].items() if k != "job_attempt"
        } == document["rows"]
    finally:
        restored.dispose()


def test_invalid_snapshot_request_and_collision(engine):
    insert_raw(engine, row())
    document = snapshots.project(engine, SONG)
    invalid = copy.deepcopy(document)
    invalid["rows"]["job_attempt"][0]["engine_request"]["job_id"] = JOB
    with pytest.raises(ValueError):
        snapshots.validate(invalid, Path(engine.url.database).parent)
    invalid = copy.deepcopy(document)
    invalid["rows"]["job_attempt"][0]["engine_request"]["seed"] = 18
    with pytest.raises(ValueError, match="collision"):
        snapshots.restore(engine, invalid, Path(engine.url.database).parent)
    assert snapshots.project(engine, SONG) == document


def test_dirty_and_clock_direct_sql(engine):
    directory = Path(engine.url.database).parent
    snapshots.publish(engine, SONG, directory)
    with engine.connect() as connection:
        before = connection.exec_driver_sql(
            "SELECT revision FROM snapshot_clock"
        ).scalar_one()
    insert_raw(engine, row())
    with engine.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (SONG,)
            ).scalar_one()
            == 1
        )
        assert (
            connection.exec_driver_sql(
                "SELECT revision FROM snapshot_clock"
            ).scalar_one()
            > before
        )
    snapshots.reconcile(engine, directory)
    target = directory / "songs" / SONG / "song.json"
    assert json.loads(target.read_text())["rows"]["job_attempt"][0]["id"] == ATTEMPT
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET last_seq=3,status='submitted'"
        )
    snapshots.reconcile(engine, directory, startup=True)
    assert json.loads(target.read_text())["rows"]["job_attempt"][0]["last_seq"] == 3
    with engine.begin() as connection:
        connection.exec_driver_sql("DELETE FROM job_attempt")
    snapshots.reconcile(engine, directory)
    assert json.loads(target.read_text())["rows"]["job_attempt"] == []


def test_migration_preserves_historical_ddl(engine):
    config = Config()
    config.set_main_option(
        "script_location", str(Path(models.__file__).parents[1] / "migrations")
    )
    config.attributes["database_path"] = Path(engine.url.database)
    assert "job_attempt" in inspect(engine).get_table_names(), "Migration 0005 absent"
    command.downgrade(config, "0004")
    assert "job_attempt" not in inspect(engine).get_table_names()
    baseline = BASELINE_DDL_SHA256
    with engine.connect() as connection:
        actual = dict(
            connection.exec_driver_sql(
                "SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
            ).all()
        )
    assert ddl_hash(actual) == baseline
    command.upgrade(config, "head")
    assert "job_attempt" in inspect(engine).get_table_names()
    assert snapshots.project(engine, SONG)["rows"]["job"][0]["request"] == {"seed": 17}


def test_schema_copies_backward_compatible(engine):
    root = Path.cwd()
    assert (root / "packages/contracts/song-v1.schema.json").read_bytes() == (
        root / "apps/server/app/models/song-v1.schema.json"
    ).read_bytes()
    legacy = copy.deepcopy(LEGACY_SNAPSHOT)
    snapshots.validate(legacy, Path(engine.url.database).parent)
    assert set(legacy["rows"]) == set(snapshots.TABLES) - {
        "job_attempt",
        "cpu_execution",
        "publication_intent",
        "publication_intent_revision",
    }


def test_nested_request_is_frozen(engine):
    with Session(engine) as session:
        session.add(models.JobAttempt(**row()))
        session.commit()
        session.expire_all()
        attempt = session.get(models.JobAttempt, ATTEMPT)
        with pytest.raises(TypeError):
            attempt.engine_request.params["duration_s"] = 99
        with pytest.raises((ValueError, TypeError)):
            attempt.engine_request.inputs[0].path = "uploads/changed.wav"
        with pytest.raises((ValueError, TypeError, AttributeError)):
            attempt.engine_request.inputs.append(attempt.engine_request.inputs[0])


@pytest.mark.parametrize("boundary", ["sql", "orm", "snapshot"])
def test_nested_unknown_fields_never_discarded(engine, boundary):
    value = row()
    value["engine_request"]["inputs"][0]["discarded"] = "must not silently vanish"
    if boundary == "sql":
        with pytest.raises(sqlite3.IntegrityError):
            insert_raw(engine, value)
    elif boundary == "orm":
        with pytest.raises((ValueError, StatementError)), Session(engine) as session:
            session.add(models.JobAttempt(**value))
            session.flush()
    else:
        insert_raw(engine, row())
        document = snapshots.project(engine, SONG)
        document["rows"]["job_attempt"][0]["engine_request"] = value["engine_request"]
        with pytest.raises((ValueError, SchemaValidationError)):
            snapshots.validate(document, Path(engine.url.database).parent)


@pytest.mark.parametrize("where", ["envelope", "data"])
def test_terminal_unknown_fields_rejected_without_discard(engine, where):
    value = row()
    value.update(status="failed", last_seq=4, terminal=error())
    (value["terminal"] if where == "envelope" else value["terminal"]["data"])[
        "discarded"
    ] = "keep or reject"
    with pytest.raises((ValueError, StatementError)), Session(engine) as session:
        session.add(models.JobAttempt(**value))
        session.flush()


def test_attempt_support_closure_and_consumers(engine):
    other_song = "01K70000000000000000000005"
    other_job = "01K70000000000000000000006"
    sibling_job = "01K70000000000000000000007"
    collection = "01K70000000000000000000008"
    artwork = "01K70000000000000000000009"
    unrelated = "01K70000000000000000000010"
    with Session(engine) as session:
        session.add_all(
            [
                models.Song(id=other_song, owner_id=OWNER, title="Support"),
                models.Song(id=unrelated, owner_id=OWNER, title="Unrelated"),
            ]
        )
        session.flush()
        session.add_all(
            [
                models.Job(
                    id=other_job,
                    owner_id=OWNER,
                    song_id=other_song,
                    task="music.instrumental",
                    lane="gpu",
                    request={},
                ),
                models.Job(
                    id=sibling_job,
                    owner_id=OWNER,
                    song_id=other_song,
                    task="music.instrumental",
                    lane="gpu",
                    request={},
                ),
            ]
        )
        session.flush()
        session.add(
            models.Artwork(
                id=artwork,
                owner_id=OWNER,
                song_id=other_song,
                job_id=other_job,
                kind="cover",
                source="generated",
                rights="own",
            )
        )
        session.flush()
        session.add(
            models.Collection(
                id=collection, owner_id=OWNER, name="Shared", cover_artwork_id=artwork
            )
        )
        session.flush()
        session.get(models.Song, SONG).collection_id = collection
        session.commit()
    value = row()
    value["job_id"] = other_job
    insert_raw(engine, value)
    document = snapshots.project(engine, SONG)
    assert document["rows"]["job_attempt"] == []
    assert document["dependencies"]["rows"]["job_attempt"][0]["id"] == ATTEMPT
    assert [v["id"] for v in document["dependencies"]["rows"]["job"]] == [other_job]
    directory = Path(engine.url.database).parent
    for song in (SONG, other_song, unrelated):
        snapshots.publish(engine, song, directory)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET status='submitted',last_seq=3"
        )
    with engine.connect() as connection:
        dirty = dict(
            connection.exec_driver_sql("SELECT id,snapshot_dirty FROM song").all()
        )
    assert dirty == {SONG: 1, other_song: 1, unrelated: 0}
    document = snapshots.project(engine, SONG)
    destination = directory / "support.sqlite"
    snapshots.restore_new(destination, document, directory)
    restored = create_db_engine(destination)
    try:
        assert snapshots.project(restored, SONG) == document
        with pytest.raises(IntegrityError), restored.begin() as connection:
            connection.exec_driver_sql("UPDATE job_attempt SET last_seq=4")
        forged = copy.deepcopy(document)
        forged["dependencies"]["provenance"]["row_digests"][
            "job_attempt/" + ATTEMPT
        ] = "0" * 64
        with pytest.raises(ValueError, match="provenance"):
            snapshots.validate(forged, directory)
    finally:
        restored.dispose()


def test_parent_move_invalidates_old_new_consumers(engine):
    insert_raw(engine, row())
    other = "01K70000000000000000000005"
    with Session(engine) as session:
        session.add(models.Song(id=other, owner_id=OWNER, title="Destination"))
        session.commit()
    directory = Path(engine.url.database).parent
    for song in (SONG, other):
        snapshots.publish(engine, song, directory)
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE job SET song_id=? WHERE id=?", (other, JOB))
    with engine.connect() as connection:
        assert all(
            v == 1
            for v in connection.exec_driver_sql(
                "SELECT snapshot_dirty FROM song"
            ).scalars()
        )
    assert snapshots.project(engine, SONG)["rows"]["job_attempt"] == []
    assert snapshots.project(engine, other)["rows"]["job_attempt"][0]["id"] == ATTEMPT


def test_backup_restores_attempt_native(engine):
    from app.backup import backup, restore_backup

    value = row()
    value.update(status="failed", last_seq=4, terminal=error())
    insert_raw(engine, value)
    directory = Path(engine.url.database).parent
    document = snapshots.project(engine, SONG)
    source = backup(Path(engine.url.database), directory / "backups")
    destination = directory / "backup-restored.sqlite"
    restore_backup(source, destination)
    restored = create_db_engine(destination)
    try:
        assert snapshots.project(restored, SONG) == document
        with restored.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        with pytest.raises(IntegrityError), restored.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE job_attempt SET engine_request=?",
                (json.dumps({**request(), "seed": 18}),),
            )
    finally:
        restored.dispose()


def test_project_historical_revision_without_fabricated_attempts(engine):
    config = Config()
    config.set_main_option(
        "script_location", str(Path(models.__file__).parents[1] / "migrations")
    )
    config.attributes["database_path"] = Path(engine.url.database)
    command.downgrade(config, "0003")
    document = snapshots.project(engine, SONG)
    assert document["rows"]["job_attempt"] == []
    assert document["rows"]["job"][0]["status"] == "running"
    snapshots.validate(document, Path(engine.url.database).parent)


def test_orm_terminal_data_strict(engine):
    value = row()
    value.update(status="failed", last_seq=4, terminal=error())
    value["terminal"]["data"]["retryable"] = "false"
    with pytest.raises((ValueError, StatementError)), Session(engine) as session:
        session.add(models.JobAttempt(**value))
        session.flush()


def test_reservation_retains_typed_freeze_without_session_expiration(engine):
    from engine_contract import JobRequest, LoadRequest

    with Session(engine, expire_on_commit=False) as session:
        attempt = models.JobAttempt(**row())
        session.add(attempt)
        session.commit()
        assert isinstance(attempt.engine_request, JobRequest)
        assert isinstance(attempt.load_options, LoadRequest)
        with pytest.raises(TypeError):
            attempt.engine_request.params["duration_s"] = 99


@pytest.mark.parametrize("count", [20, 200, 405])
def test_attempt_restore_queries_batched(engine, count):
    from sqlalchemy import event

    value = row()
    database = engine.url.database
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        for ordinal in range(1, count + 1):
            current = copy.deepcopy(value)
            current["id"] = "01K700" + str(ordinal + 100).zfill(20)
            current["ordinal"] = ordinal
            current["engine_request"]["job_id"] = current["id"]
            current["engine_request"]["output_dir"] = "tmp/" + current["id"]
            encoded = {
                k: json.dumps(v)
                if k in {"engine_request", "load_options", "terminal"} and v is not None
                else v
                for k, v in current.items()
            }
            connection.execute(
                "INSERT INTO job_attempt ("
                + ",".join(encoded)
                + ") VALUES ("
                + ",".join("?" for _ in encoded)
                + ")",
                tuple(encoded.values()),
            )
    document = snapshots.project(engine, SONG)
    selects = []

    @event.listens_for(engine, "before_cursor_execute")
    def observe(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    snapshots.restore(engine, document, Path(database).parent)
    checks = [sql for sql in selects if "FROM job_attempt" in sql]
    # Una lectura de colisiones por lote y una lectura de proyección.
    assert len(checks) == (count + 399) // 400 + 1
    assert len(selects) == 29 + 3 * ((count + 399) // 400)
    assert snapshots.project(engine, SONG) == document


@pytest.mark.parametrize("populated", [False, True])
def test_native_0004_0005_0004_head(populated):
    directory = PHASE / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    path = directory / "cycle.sqlite"
    config = Config()
    config.set_main_option(
        "script_location", str(Path(models.__file__).parents[1] / "migrations")
    )
    config.attributes["database_path"] = path
    command.upgrade(config, "0004")
    engine = create_db_engine(path)
    try:
        assert "job_attempt" not in inspect(engine).get_table_names()
        if populated:
            with Session(engine) as session:
                session.add(
                    models.Song(
                        id=SONG,
                        owner_id=OWNER,
                        title="Before",
                        created_at=UTC,
                        updated_at=UTC,
                    )
                )
                session.flush()
                session.add(
                    models.Job(
                        id=JOB,
                        owner_id=OWNER,
                        song_id=SONG,
                        task="music.instrumental",
                        lane="gpu",
                        status="running",
                        request={"seed": 17},
                        created_at=UTC,
                        updated_at=UTC,
                    )
                )
                session.commit()
        command.upgrade(config, "0005")
        assert "job_attempt" in inspect(engine).get_table_names()
        if populated:
            insert_raw(engine, row())
            assert snapshots.project(engine, SONG)["rows"]["job_attempt"][0] == row()
        command.downgrade(config, "0004")
        assert "job_attempt" not in inspect(engine).get_table_names()
        with engine.connect() as connection:
            actual = dict(
                connection.exec_driver_sql(
                    "SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
                ).all()
            )
        assert ddl_hash(actual) == BASELINE_DDL_SHA256
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).scalar_one()
                == "0007"
            )
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        if populated:
            document = snapshots.project(engine, SONG)
            assert document["rows"]["job"][0]["request"] == {"seed": 17}
            assert document["rows"]["job"][0]["status"] == "running"
            assert document["rows"]["job_attempt"] == []
    finally:
        engine.dispose()


@pytest.mark.parametrize("field", ["status", "last_seq"])
def test_orm_updates_never_reset_invalid_null_to_default(engine, field):
    with Session(engine) as session:
        session.add(models.JobAttempt(**row()))
        session.commit()
        attempt = session.get(models.JobAttempt, ATTEMPT)
        setattr(attempt, field, None)
        with pytest.raises((ValueError, StatementError)):
            session.flush()


def test_direct_sql_replace_cannot_rewrite_reservation(engine):
    insert_raw(engine, row())
    value = row()
    value["engine_request"]["seed"] = 18
    encoded = {
        k: json.dumps(v)
        if k in {"engine_request", "load_options", "terminal"} and v is not None
        else v
        for k, v in value.items()
    }
    with (
        pytest.raises(sqlite3.IntegrityError),
        sqlite3.connect(engine.url.database) as connection,
    ):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT OR REPLACE INTO job_attempt ("
            + ",".join(encoded)
            + ") VALUES ("
            + ",".join("?" for _ in encoded)
            + ")",
            tuple(encoded.values()),
        )
    assert (
        snapshots.project(engine, SONG)["rows"]["job_attempt"][0]["engine_request"][
            "seed"
        ]
        == 17
    )
