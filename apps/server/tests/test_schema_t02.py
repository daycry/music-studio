"""Contrato de esquema inicial, independiente del ORM."""

import importlib.util
import sqlite3
from pathlib import Path
from uuid import uuid4

TABLES = {
    "user",
    "collection",
    "song",
    "lyrics_version",
    "take",
    "lineage_edge",
    "asset",
    "upload",
    "analysis",
    "artwork",
    "character",
    "character_ref",
    "preset",
    "video_project",
    "video_character",
    "shot",
    "shot_version",
    "render",
    "export",
    "job",
    "job_dependency",
    "setting",
    "provider",
}


def test_schema_complete():
    root = (
        Path.cwd()
        / ".cache/dev-cycle/m1/t02-normal-implementation/fixtures"
        / uuid4().hex
    )
    root.mkdir(parents=True)
    path = root / "studio.sqlite"
    if importlib.util.find_spec("app.db") is not None:
        from app.db import migrate

        migrate(path)
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert TABLES <= tables, f"Faltan tablas: {sorted(TABLES - tables)}"
        for table in TABLES:
            columns = {
                row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
            }
            assert {
                "id",
                "owner_id",
                "created_at",
                "updated_at",
                "deleted_at",
            } <= columns
        user = connection.execute('SELECT id,owner_id,name FROM "user"').fetchone()
        assert user[0] == user[1] and user[2] == "local" and len(user[0]) == 26
    from app.db import create_db_engine

    engine = create_db_engine(path)
    with engine.connect() as first, engine.connect() as second:
        for connection in (first, second):
            assert (
                connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"
            )
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    engine.dispose()
