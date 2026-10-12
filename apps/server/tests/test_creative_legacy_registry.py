"""El replay M1 y Song v1 no consumen metadata de revisiones futuras."""

import importlib
from contextlib import contextmanager

import pytest
from alembic import command
from alembic.config import Config
from app import snapshots
from app.db import create_db_engine
from app.models import Base
from sqlalchemy import Column, Integer, Table, Text
from test_persistence_t02 import populate_project
from test_worker_publication_invariants import engine as _publication_engine
from test_worker_publication_invariants import execution, reserve

engine = _publication_engine


@contextmanager
def evolved_metadata(names=None):
    """Instala futuro antes de recargar lectores, sin alterar la BD histórica."""
    names = names or (
        "song",
        "take",
        "cpu_execution",
        "publication_intent",
        "publication_intent_revision",
        "job",
        "job_attempt",
        "job_dependency",
    )
    columns = []
    for name in names:
        column = Column("future_m2", Integer)
        Base.metadata.tables[name].append_column(column)
        columns.append((name, column))
    future = Table(
        "future_m2_table", Base.metadata, Column("id", Text, primary_key=True)
    )
    from app.migrations import (
        cpu_publication_invariants,
        fix1_invariants,
        fix2_invariants,
        legacy_m1_registry,
    )

    importlib.reload(legacy_m1_registry)
    importlib.reload(cpu_publication_invariants)
    importlib.reload(fix1_invariants)
    importlib.reload(fix2_invariants)
    importlib.reload(snapshots)
    try:
        yield
    finally:
        Base.metadata.remove(future)
        for name, column in columns:
            Base.metadata.tables[name]._columns.remove(column)
        importlib.reload(snapshots)


@pytest.fixture
def future_metadata():
    with evolved_metadata():
        yield


def upgrade(path, revision):
    config = Config()
    config.set_main_option(
        "script_location", str(snapshots.Path(__file__).parents[1] / "app/migrations")
    )
    config.attributes["database_path"] = path
    command.upgrade(config, revision)


@pytest.mark.parametrize("revision", ["0006", "0007"])
def test_replay_guards_ignore_future_columns(tmp_path, future_metadata, revision):
    path = tmp_path / "historical.sqlite"
    upgrade(path, revision)
    engine = create_db_engine(path)
    try:
        with engine.connect() as connection:
            guards = (
                connection.exec_driver_sql(
                    "SELECT sql FROM sqlite_master WHERE type='trigger'"
                )
                .scalars()
                .all()
            )
            assert not [guard for guard in guards if "future_m2" in guard]
    finally:
        engine.dispose()


def test_registry_matches_historical_ddl(tmp_path, future_metadata):
    from app.migrations.legacy_m1_registry import TABLES

    path = tmp_path / "registry.sqlite"
    upgrade(path, "0007")
    engine = create_db_engine(path)
    try:
        with engine.connect() as connection:
            for name, table in TABLES.items():
                columns = connection.exec_driver_sql(
                    f'PRAGMA table_info("{name}")'
                ).all()
                assert set(table.columns.keys()) == {column[1] for column in columns}
                links = connection.exec_driver_sql(
                    f'PRAGMA foreign_key_list("{name}")'
                ).all()
                assert {
                    (fk.parent.name, fk.target_fullname) for fk in table.foreign_keys
                } == {(link[3], link[2] + "." + link[4]) for link in links}
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "trigger",
    [
        "support_song_edit",
        "fix2_clock_song_update",
        "dirty_song_update_old",
        "dirty_song_update_new",
    ],
)
def test_historical_song_guard_ignores_future_column(
    tmp_path, future_metadata, trigger
):
    path = tmp_path / "song-guard.sqlite"
    upgrade(path, "0007")
    engine = create_db_engine(path)
    try:
        with engine.connect() as connection:
            guard = connection.exec_driver_sql(
                "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
                (trigger,),
            ).scalar_one()
            assert "future_m2" not in guard
    finally:
        engine.dispose()


def test_projection_ignores_future_metadata_before_reload(tmp_path, future_metadata):
    path = tmp_path / "projection.sqlite"
    upgrade(path, "0007")
    engine = create_db_engine(path)
    try:
        with engine.begin() as connection:
            owner = connection.exec_driver_sql('SELECT id FROM "user"').scalar_one()
            song = "00000000000000000000000001"
            connection.exec_driver_sql(
                "INSERT INTO song(id,owner_id,title,created_at,updated_at) VALUES (?,?,?, ?,?)",
                (
                    song,
                    owner,
                    "Histórica",
                    "2026-10-10T00:00:00Z",
                    "2026-10-10T00:00:00Z",
                ),
            )
        projected = snapshots.project(engine, song)
        assert "future_m2_table" not in projected["rows"]
        assert "future_m2" not in projected["rows"]["song"][0]
    finally:
        engine.dispose()


def capture(connection):
    schema = connection.exec_driver_sql(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).all()
    names = (
        connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        .scalars()
        .all()
    )
    rows = {
        name: sorted(
            connection.exec_driver_sql(f'SELECT * FROM "{name}"').all(), key=repr
        )
        for name in names
    }
    columns = {
        name: connection.exec_driver_sql(f'PRAGMA table_info("{name}")').all()
        for name in names
    }
    return schema, rows, columns


@pytest.mark.parametrize("revision", ["0006", "0007"])
def test_populated_reinstall_and_projection_are_byte_equivalent(tmp_path, revision):
    from app.migrations import cpu_publication_invariants

    path = tmp_path / "populated.sqlite"
    upgrade(path, revision)
    song = populate_project(path)
    engine = create_db_engine(path)
    try:
        before = snapshots.project(engine, song)
        digests = {
            name: [snapshots.digest(row, name) for row in rows]
            for name, rows in before["rows"].items()
        }
        with engine.connect() as connection, connection.begin() as transaction:
            cpu_publication_invariants.uninstall(connection)
            cpu_publication_invariants.install(connection)
            stored = capture(connection)
            transaction.rollback()
        with evolved_metadata():
            with engine.connect() as connection, connection.begin() as transaction:
                cpu_publication_invariants.uninstall(connection)
                cpu_publication_invariants.install(connection)
                actual = capture(connection)
                assert actual[0] == stored[0]
                assert actual[2] == stored[2]
                for name in stored[1]:
                    assert actual[1][name] == stored[1][name], name
                transaction.rollback()
            after = snapshots.project(engine, song)
            assert after == before
            assert {
                name: [snapshots.digest(row, name) for row in rows]
                for name, rows in after["rows"].items()
            } == digests
    finally:
        engine.dispose()


@pytest.mark.parametrize("value", [None, 0, 2**100, str(2**100)])
def test_frozen_seed_sql_roundtrip(tmp_path, value):
    from app.migrations.legacy_m1_registry import Seed
    from sqlalchemy import literal, select

    engine = create_db_engine(tmp_path / "seed.sqlite")
    try:
        with engine.connect() as connection:
            assert connection.execute(
                select(literal(value, type_=Seed()))
            ).scalar_one() == (None if value is None else int(value))
    finally:
        engine.dispose()


@pytest.mark.parametrize("value", [True, -1, "-1", "١", 1.5])
def test_frozen_seed_rejects_noncanonical_sql_bind(tmp_path, value):
    from app.migrations.legacy_m1_registry import Seed
    from sqlalchemy import literal, select
    from sqlalchemy.exc import StatementError

    engine = create_db_engine(tmp_path / "invalid-seed.sqlite")
    try:
        with (
            engine.connect() as connection,
            pytest.raises(StatementError, match="Seed must be a non-negative integer"),
        ):
            connection.execute(select(literal(value, type_=Seed())))
    finally:
        engine.dispose()


@pytest.mark.parametrize("name", ["job", "job_attempt", "take", "job_dependency"])
def test_legacy_authority_queries_ignore_future_columns(engine, name):
    from app.migrations import cpu_publication_invariants

    reserve(engine)
    with evolved_metadata((name,)), engine.connect() as connection:
        cpu_publication_invariants.validate_connection(
            connection, "cpu_execution", execution()
        )
