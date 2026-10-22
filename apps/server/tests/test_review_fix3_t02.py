"""Regresiones SQLite reales para promoción y colisiones por lotes."""

import json
import re
import sqlite3
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import create_db_engine, migrate
from app.models import Song
from app.snapshots import project, restore
from sqlalchemy import event, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_persistence_t02 import populate_project, song_rows
from test_review_fix2_t02 import scaled_project, support_import

PHASE = Path.cwd() / ".cache/dev-cycle/m1/t02-review-fix3"


@pytest.fixture
def database():
    directory = PHASE / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    path = directory / "studio.sqlite"
    migrate(path)
    return path


@pytest.mark.parametrize("writer", ["sql", "core", "orm", "bulk"])
@pytest.mark.parametrize("content", [False, True])
def test_r02_12_ordinary_promotion_rejected(database, writer, content):
    engine, first, second, original = support_import(database)
    changes = {"is_dependency_only": False}
    if content:
        changes["title"] = "unvalidated promotion"
    before = project(engine, second)
    try:
        with pytest.raises(IntegrityError, match="Support"):
            if writer == "sql":
                with engine.begin() as c:
                    c.exec_driver_sql(
                        "UPDATE song SET "
                        + ",".join(k + "=?" for k in changes)
                        + " WHERE id=?",
                        (*changes.values(), first),
                    )
            elif writer == "core":
                with engine.begin() as c:
                    c.execute(update(Song).where(Song.id == first).values(**changes))
            else:
                with Session(engine) as s:
                    if writer == "bulk":
                        s.query(Song).filter(Song.id == first).update(changes)
                    else:
                        row = s.get(Song, first)
                        for name, value in changes.items():
                            setattr(row, name, value)
                    s.commit()
        with engine.connect() as c:
            assert (
                c.exec_driver_sql(
                    "SELECT is_dependency_only FROM song WHERE id=?", (first,)
                ).scalar_one()
                == 1
            )
            assert not c.exec_driver_sql(
                "SELECT song_id FROM song_fts WHERE song_id=?", (first,)
            ).all()
            assert not c.exec_driver_sql(
                "SELECT id FROM dispatchable_job WHERE song_id=?", (first,)
            ).all()
            assert not c.exec_driver_sql("SELECT * FROM snapshot_import").all()
        assert project(engine, second) == before
        restore(engine, original, database.parent / "restored")
        assert project(engine, first) == original
    finally:
        engine.dispose()


def restore_queries(database, size):
    song = scaled_project(database, size)
    source = create_db_engine(database)
    document = project(source, song)
    source.dispose()
    target = database.parent / ("target-" + str(size) + ".sqlite")
    migrate(target)
    engine = create_db_engine(target)
    queries = []

    def record(c, cursor, sql, parameters, context, many):
        if sql.lstrip().upper().startswith("SELECT"):
            queries.append({"sql": sql, "parameters": list(parameters)})

    event.listen(engine, "before_cursor_execute", record)
    try:
        restore(engine, document, database.parent / ("data-" + str(size)))
        captured = list(queries)
        assert project(engine, song) == document
        (PHASE / ("queries-" + str(size) + "-" + uuid4().hex + ".json")).write_text(
            json.dumps(captured, indent=2)
        )
        individual = [
            q
            for q in captured
            if re.search(r"FROM (take|asset)\s+WHERE \1\.id =", q["sql"])
        ]
        return captured, individual
    finally:
        engine.dispose()


def test_r02_18_restore_405_810_bounded_queries(database):
    queries, individual = restore_queries(database, 405)
    assert len(individual) == 0, len(individual)
    assert len(queries) < 100, len(queries)


def test_r02_18_small_large_and_foreign_roots(database):
    small, _ = restore_queries(database, 20)
    large, _ = restore_queries(database, 200)
    for _ in range(31):
        song_rows(database)
    foreign, _ = restore_queries(database, 200)
    assert len(large) <= len(small) + 5
    assert len(foreign) == len(large)
    for query in large:
        for placeholders in re.findall(r" IN \(([^()]*)\)", query["sql"]):
            assert placeholders.count("?") <= 400
    (PHASE / ("scaling-" + uuid4().hex + ".json")).write_text(
        json.dumps(
            {"20": len(small), "200": len(large), "200_plus_31_foreign": len(foreign)}
        )
    )


def test_r02_18_collision_before_exception_and_serialized(database):
    engine, first, second, original = support_import(database)
    before = project(engine, second)
    observations = []

    def record(c, cursor, sql, parameters, context, many):
        if sql.startswith("SELECT ") and "FROM user" in sql and not observations:
            with (
                sqlite3.connect(engine.url.database, timeout=0) as foreign,
                pytest.raises(sqlite3.OperationalError, match="locked"),
            ):
                foreign.execute(
                    "UPDATE song SET title='concurrent' WHERE id=?", (second,)
                )
            assert not c.exec_driver_sql("SELECT * FROM snapshot_import").all()
            observations.append(True)

    event.listen(engine, "before_cursor_execute", record)
    try:
        restore(engine, original, database.parent / "restored")
        assert observations == [True]
        assert project(engine, first) == original
        event.remove(engine, "before_cursor_execute", record)
        with engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE artwork SET prompt='actual conflict' WHERE song_id=?", (first,)
            )
        stable = project(engine, first)
        opened = []

        def watch(c, cursor, sql, parameters, context, many):
            if sql.startswith("INSERT INTO snapshot_import"):
                opened.append(sql)

        event.listen(engine, "before_cursor_execute", watch)
        with pytest.raises(ValueError, match="Row collision"):
            restore(engine, original, database.parent / "restored")
        assert opened == []
        assert project(engine, first) == stable
        with engine.connect() as c:
            assert not c.exec_driver_sql("SELECT * FROM snapshot_import").all()
            assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
        # IDs and original consumer still refer to their original rows.
        assert {r["id"] for r in project(engine, second)["rows"]["song"]} == {
            r["id"] for r in before["rows"]["song"]
        }
    finally:
        engine.dispose()


def test_r02_12_bookkeeping_global_edits_and_no_demotion(database):
    engine, first, second, _original = support_import(database)
    try:
        restore(engine, project(engine, second), database.parent / "restored")
        with engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE id=?",
                (first,),
            )
            c.exec_driver_sql("UPDATE collection SET name='global edit'")
            c.exec_driver_sql("UPDATE character SET description='global edit'")
        with pytest.raises(IntegrityError, match="Support"), engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE song SET title='edited support' WHERE id=?", (first,)
            )
        with pytest.raises(IntegrityError, match="demoted"), engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE song SET is_dependency_only=1 WHERE id=?", (second,)
            )
        with engine.connect() as c:
            assert (
                c.exec_driver_sql(
                    "SELECT is_dependency_only FROM song WHERE id=?", (first,)
                ).scalar_one()
                == 1
            )
            assert (
                c.exec_driver_sql(
                    "SELECT is_dependency_only FROM song WHERE id=?", (second,)
                ).scalar_one()
                == 0
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("failure", ["collision", "insert"])
def test_r02_18_mixed_existing_missing_atomic_rollback(database, failure):
    engine, first, second, original = support_import(database)
    before = project(engine, second)
    attempted = deepcopy(original)
    writes = []

    def record(c, cursor, sql, parameters, context, many):
        if sql.startswith(
            ("INSERT INTO snapshot_import", "UPDATE song SET is_dependency_only=0")
        ):
            writes.append(sql)

    event.listen(engine, "before_cursor_execute", record)
    try:
        with engine.connect() as c:
            existing = set(c.exec_driver_sql("SELECT id FROM take").scalars())
            missing = {r["id"] for r in original["rows"]["take"]} - existing
            assert existing and missing
            counts = {
                table: c.exec_driver_sql(f'SELECT count(*) FROM "{table}"').scalar_one()
                for table in original["rows"]
            }
        if failure == "collision":
            attempted["rows"]["song"][0]["title"] = "incompatible existing identity"
            error, message = ValueError, "Row collision"
        else:
            with engine.begin() as c:
                c.exec_driver_sql(
                    "CREATE TRIGGER private_fail_import BEFORE INSERT ON take "
                    "BEGIN SELECT RAISE(ABORT,'private injected insert failure'); END"
                )
            error, message = IntegrityError, "private injected"
        with pytest.raises(error, match=message):
            restore(engine, attempted, database.parent / "restored")
        if failure == "insert":
            assert len(writes) == 2
            with engine.begin() as c:
                c.exec_driver_sql("DROP TRIGGER private_fail_import")
        else:
            assert writes == []
        with engine.connect() as c:
            assert {
                table: c.exec_driver_sql(f'SELECT count(*) FROM "{table}"').scalar_one()
                for table in original["rows"]
            } == counts
            assert (
                c.exec_driver_sql(
                    "SELECT is_dependency_only FROM song WHERE id=?", (first,)
                ).scalar_one()
                == 1
            )
            assert not c.exec_driver_sql("SELECT * FROM snapshot_import").all()
            assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
        assert project(engine, second) == before
        restore(engine, original, database.parent / "restored")
        assert project(engine, first) == original
    finally:
        engine.dispose()


@pytest.mark.parametrize("populated", [False, True])
@pytest.mark.parametrize("baseline", ["0003", "0002", "0001", "base"])
def test_fix3_additive_migration_cycles(database, populated, baseline):
    from alembic import command
    from alembic.config import Config

    song = populate_project(database) if populated else None
    engine = create_db_engine(database)
    before = project(engine, song) if song else None
    engine.dispose()
    config = Config()
    config.set_main_option(
        "script_location", str(Path("apps/server/app/migrations").resolve())
    )
    config.attributes["database_path"] = database
    command.downgrade(config, baseline)
    with sqlite3.connect(database) as c:
        assert not c.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'fix3_%'"
        ).fetchall()
        if baseline == "0003":
            assert c.execute("SELECT version_num FROM alembic_version").fetchone() == (
                "0003",
            )
    command.upgrade(config, "0004")
    engine = create_db_engine(database)
    try:
        with engine.connect() as c:
            assert (
                c.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).scalar_one()
                == "0004"
            )
            assert (
                c.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE name='fix3_song_promotion'"
                ).scalar_one()
                == "fix3_song_promotion"
            )
            assert not c.exec_driver_sql("PRAGMA foreign_key_check").all()
        if before is not None and baseline != "base":
            assert project(engine, song) == before
    finally:
        engine.dispose()
