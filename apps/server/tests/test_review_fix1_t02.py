"""Regresiones de revisiÃ³n1, sobre SQLite y fuentes de producciÃ³n reales."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import create_db_engine, migrate
from app.snapshots import project, reconcile
from test_persistence_t02 import populate_project, song_rows


@pytest.fixture
def database():
    directory = (
        Path.cwd() / ".cache/dev-cycle/m1/t02-review-fix1/fixtures" / uuid4().hex
    )
    directory.mkdir(parents=True)
    path = directory / "studio.sqlite"
    migrate(path)
    return path


def test_r02_01_direct_root_write(database):
    populate_project(database)
    with sqlite3.connect(database) as db:
        parent, child = db.execute(
            'SELECT parent_id,child_id FROM lineage_edge WHERE child_type="take"'
        ).fetchone()
        with pytest.raises(sqlite3.IntegrityError, match="root"):
            db.execute("UPDATE take SET root_id=? WHERE id=?", (child, parent))


def test_r02_02_inverse_artwork_move(database):
    from app.models import Artwork, LineageEdge, new_id
    from sqlalchemy.orm import Session

    first, owner = song_rows(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        artworks = [
            Artwork(
                id=new_id(),
                owner_id=owner,
                song_id=first,
                kind="cover",
                source="upload",
                rights="own",
            )
            for _ in range(2)
        ]
        session.add_all(artworks)
        session.flush()
        session.add(
            LineageEdge(
                owner_id=owner,
                child_type="artwork",
                child_id=artworks[1].id,
                parent_type="artwork",
                parent_id=artworks[0].id,
                role="source",
            )
        )
        session.commit()
        identifier = artworks[1].id
    engine.dispose()
    with (
        sqlite3.connect(database) as db,
        pytest.raises(sqlite3.IntegrityError, match="lineage"),
    ):
        db.execute("UPDATE artwork SET song_id=? WHERE id=?", (second, identifier))


def test_r02_04_reconcile_isolates_bad_projection(database, monkeypatch):
    from app import snapshots

    first, _ = song_rows(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    original = snapshots.publish

    def publish(bound, identifier, directory):
        if identifier == first:
            raise ValueError("synthetic private secret/path")
        return original(bound, identifier, directory)

    monkeypatch.setattr(snapshots, "publish", publish)
    reconcile(engine, database.parent)
    assert (database.parent / "songs" / second / "song.json").is_file()
    engine.dispose()


@pytest.mark.parametrize("damage", ["missing_fts", "foreign_keys"])
def test_r02_05_due_rejects_unrestorable_recent_copy(database, damage):
    from app.backup import backup, due

    song_rows(database)
    now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    directory = database.parent / "backups"
    candidate = backup(database, directory, now)
    with closing(sqlite3.connect(candidate)) as db, db:
        if damage == "missing_fts":
            db.execute("DROP TABLE song_fts")
        else:
            db.execute("UPDATE song SET collection_id='01K70000000000000000000001'")
    assert due(database, directory, now) is not None


def test_r02_08_artwork_edge_does_not_update_takes(database):
    from app.models import Artwork, LineageEdge, new_id
    from sqlalchemy.orm import Session

    song = populate_project(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        owner = (
            session.connection()
            .exec_driver_sql("SELECT owner_id FROM song WHERE id=?", (song,))
            .scalar_one()
        )
        items = [
            Artwork(
                id=new_id(),
                owner_id=owner,
                song_id=song,
                kind="cover",
                source="upload",
                rights="own",
            )
            for _ in range(2)
        ]
        session.add_all(items)
        session.flush()
        session.connection().exec_driver_sql(
            "CREATE TABLE observed_take_updates (id TEXT)"
        )
        session.connection().exec_driver_sql(
            "CREATE TRIGGER observe_take AFTER UPDATE ON take BEGIN INSERT INTO observed_take_updates VALUES(NEW.id); END"
        )
        session.add(
            LineageEdge(
                owner_id=owner,
                child_type="artwork",
                child_id=items[1].id,
                parent_type="artwork",
                parent_id=items[0].id,
                role="source",
            )
        )
        session.commit()
        assert (
            session.connection()
            .exec_driver_sql("SELECT count(*) FROM observed_take_updates")
            .scalar_one()
            == 0
        )
    engine.dispose()


def test_r02_09_fts_delete_uses_indexed_identity(database):
    with sqlite3.connect(database) as db:
        sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' AND name='song_fts_update'"
        ).fetchone()[0]
        assert "DELETE FROM song_fts WHERE song_id=" not in sql
        assert "rowid" in sql
        plan = db.execute(
            "EXPLAIN QUERY PLAN DELETE FROM song_fts WHERE rowid=1"
        ).fetchall()
        assert any("INDEX" in row[3] for row in plan)


def test_r02_06_real_safe_log(database, monkeypatch):
    import asyncio
    from types import SimpleNamespace

    from app import backup as module
    from app import snapshots
    from app.logging import configure_logging

    song_rows(database)
    settings = SimpleNamespace(data_dir=database.parent)
    logger = configure_logging(settings)
    engine = create_db_engine(database, data_dir=database.parent)

    def fail(*args, **kwargs):
        raise ValueError("SECRET/private/path")

    monkeypatch.setattr(snapshots, "publish", fail)
    from app.models import Song
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        session.query(Song).one().notes = "trigger snapshot failure"
        session.commit()
    monkeypatch.setattr(module, "due", fail)

    async def exercise():
        scheduler = module.DailyBackup(database, database.parent / "backups", logger)
        await scheduler.initial()
        scheduler.executor.shutdown(wait=True)

    asyncio.run(exercise())
    records = [
        json.loads(line)
        for line in (database.parent / "logs/server.log").read_text().splitlines()
    ]
    assert {"snapshot.failed", "backup.failed"} <= {row["msg"] for row in records}
    assert "SECRET" not in json.dumps(records)
    engine.dispose()


@pytest.mark.parametrize("reference", ["collection", "character"])
def test_r02_03_shared_global_roundtrip(database, reference):
    from app.models import (
        Artwork,
        Character,
        Collection,
        Job,
        Song,
        Take,
        VideoCharacter,
        VideoProject,
        new_id,
    )
    from app.snapshots import restore, validate
    from sqlalchemy.orm import Session

    first = populate_project(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        original = session.get(Song, first)
        target = session.get(Song, second)
        if reference == "collection":
            session.get(Collection, original.collection_id).cover_artwork_id = (
                session.query(Artwork).filter(Artwork.song_id == first).one().id
            )
            target.collection_id = original.collection_id
        else:
            character = session.query(Character).one()
            job = Job(
                owner_id=target.owner_id,
                song_id=second,
                task="music.song",
                lane="gpu",
                request={},
            )
            session.add(job)
            session.flush()
            tid = new_id()
            take = Take(
                id=tid,
                root_id=tid,
                owner_id=target.owner_id,
                song_id=second,
                job_id=job.id,
                batch_id=new_id(),
                derivation="original",
                task="music.song",
                model_id="mock",
                model_version="1",
                seed=0,
                commercial_use=True,
            )
            session.add(take)
            session.flush()
            video = VideoProject(
                owner_id=target.owner_id,
                song_id=second,
                take_id=tid,
                title="shared",
                aspect="16:9",
                level_preset="N0",
                visual_style="still",
                treatment="test",
                timeline={
                    "version": 1,
                    "fps": "24/1",
                    "duration_s": 1,
                    "shots": [],
                    "subtitles": {
                        "style": "karaoke",
                        "position": "bottom",
                        "font": "Inter",
                    },
                    "titles": [],
                },
            )
            session.add(video)
            session.flush()
            session.add(
                VideoCharacter(
                    owner_id=target.owner_id,
                    video_project_id=video.id,
                    character_id=character.id,
                    role="cast",
                )
            )
        session.commit()
    document = project(engine, second)
    validate(document, database.parent)
    assert [row["id"] for row in document["rows"]["song"]] == [second]
    assert [row["id"] for row in document["dependencies"]["rows"]["song"]] == [first]
    # Root A's analysis is not needed by its selected take/support selections.
    assert not document["dependencies"]["rows"]["analysis"]
    target = database.parent / "restored.sqlite"
    migrate(target)
    restored = create_db_engine(target)
    restore(restored, document, database.parent / "restored")
    with restored.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT id FROM song WHERE is_dependency_only=0"
        ).scalars().all() == [second]
        assert connection.exec_driver_sql(
            "SELECT id FROM song WHERE is_dependency_only=1"
        ).scalars().all() == [first]
        assert connection.exec_driver_sql(
            "SELECT song_id FROM song_fts"
        ).scalars().all() == [second]
    assert project(restored, second) == document
    restored.dispose()
    engine.dispose()


def test_r02_07_local_commit_queries_and_mtimes(database):
    from app.models import Take
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    first, _ = song_rows(database)
    second = populate_project(database)
    engine = create_db_engine(database, data_dir=database.parent)
    reconcile(engine, database.parent)
    before = (database.parent / "songs" / first / "song.json").stat().st_mtime_ns
    queries = []

    @event.listens_for(engine, "before_cursor_execute")
    def record(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    with Session(engine) as session:
        session.query(Take).filter(Take.song_id == second).first().rating = 4
        session.commit()
    assert (
        database.parent / "songs" / first / "song.json"
    ).stat().st_mtime_ns == before
    assert not any("FROM take" in sql and "WHERE" not in sql for sql in queries)
    engine.dispose()


def test_r02_07_global_consumers_and_unrelated_support_sibling(database):
    from app.models import Analysis, Artwork, Collection, Song
    from sqlalchemy.orm import Session

    first = populate_project(database)
    second, _ = song_rows(database)
    third, _ = song_rows(database)
    engine = create_db_engine(database, data_dir=database.parent)
    with Session(engine) as session:
        collection = session.query(Collection).one()
        artwork = session.query(Artwork).one()
        collection.cover_artwork_id = artwork.id
        session.get(Song, second).collection_id = collection.id
        session.commit()
        aid = artwork.id
    paths = {
        identifier: database.parent / "songs" / identifier / "song.json"
        for identifier in (first, second, third)
    }
    before = {identifier: path.stat().st_mtime_ns for identifier, path in paths.items()}
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE artwork SET prompt=? WHERE id=?", ("new shared prompt", aid)
        )
    reconcile(engine, database.parent)
    after = {identifier: path.stat().st_mtime_ns for identifier, path in paths.items()}
    assert after[first] != before[first] and after[second] != before[second]
    assert after[third] == before[third]
    with Session(engine) as session:
        session.query(Analysis).one().data = {"beats": [0, 2]}
        session.commit()
    assert paths[second].stat().st_mtime_ns == after[second]
    engine.dispose()


def test_r02_07_generation_race_retains_dirty(database, monkeypatch):
    from app import snapshots

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    original = snapshots.os.replace

    def concurrent_change(source, target):
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE song SET title=? WHERE id=?", ("concurrent title", song)
            )
        return original(source, target)

    monkeypatch.setattr(snapshots.os, "replace", concurrent_change)
    snapshots.publish(engine, song, database.parent)
    with engine.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (song,)
            ).scalar_one()
            == 1
        )
    monkeypatch.setattr(snapshots.os, "replace", original)
    reconcile(engine, database.parent)
    document = json.loads((database.parent / "songs" / song / "song.json").read_text())
    assert document["rows"]["song"][0]["title"] == "concurrent title"
    engine.dispose()


def test_r02_04_clean_missing_snapshot_startup_repair(database):
    from app.snapshots import publish

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    publish(engine, song, database.parent)
    target = database.parent / "songs" / song / "song.json"
    target.unlink()
    reconcile(engine, database.parent, startup=True)
    assert target.is_file()
    engine.dispose()


def test_import_new_adopts_snapshot_owner_before_seed(database):
    from app import snapshots

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    document = project(engine, song)
    old = document["rows"]["user"][0]["id"]
    owner = "01K70000000000000000000009"
    for rows in document["rows"].values():
        for row in rows:
            row["owner_id"] = owner
    document["rows"]["user"][0]["id"] = owner
    target = database.parent / "custom-owner.sqlite"
    snapshots.restore_new(target, document, database.parent / "custom-owner")
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT id,owner_id FROM user").fetchall() == [(owner, owner)]
        assert db.execute("SELECT owner_id FROM song").fetchall() == [(owner,)]
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
    assert old != owner
    engine.dispose()


@pytest.mark.parametrize("populated", [False, True])
def test_additive_migration_cycle(database, populated):
    from alembic import command
    from alembic.config import Config

    config = Config()
    config.set_main_option(
        "script_location", str(Path("apps/server/app/migrations").resolve())
    )
    config.attributes["database_path"] = database
    # First restore the private database to the immutable baseline revision.
    command.downgrade(config, "0001")
    with sqlite3.connect(database) as db:
        original = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'song_fts%' AND name NOT LIKE 'sqlite_%' AND name!='alembic_version'"
        ).fetchall()
        assert len(original) == 23
        if populated:
            db.execute(
                "INSERT INTO song(id,owner_id,title,created_at,updated_at) VALUES('01K70000000000000000000001','01K70000000000000000000000','baseline','2026-10-07T00:00:00Z','2026-10-07T00:00:00Z')"
            )
        before = db.execute("SELECT * FROM song").fetchall()
    command.upgrade(config, "0002")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0002",
        )
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        if populated:
            assert db.execute(
                "SELECT is_dependency_only,snapshot_dirty,snapshot_generation FROM song"
            ).fetchone() == (0, 1, 0)
    command.downgrade(config, "0001")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT * FROM song").fetchall() == before
        assert db.execute("SELECT count(*) FROM song_fts").fetchone()[0] == int(
            populated
        )
    command.upgrade(config, "0002")
    with sqlite3.connect(database) as db:
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("SELECT count(*) FROM song_fts_identity").fetchone()[
            0
        ] == int(populated)


def test_restore_collision_rolls_back_complete_union(database):
    from copy import deepcopy

    from app.snapshots import restore

    song = populate_project(database)
    engine = create_db_engine(database)
    original = project(engine, song)
    altered = deepcopy(original)
    altered["rows"]["artwork"][0]["prompt"] = "conflicting prompt"
    with pytest.raises(ValueError, match="collision"):
        restore(engine, altered, database.parent)
    assert project(engine, song) == original
    engine.dispose()


def test_restore_checks_existing_media_bytes(database):
    from app.snapshots import restore

    song = populate_project(database)
    engine = create_db_engine(database)
    document = project(engine, song)
    directory = database.parent / "media-conflict"
    relative = document["rows"]["upload"][0]["path"]
    target = directory / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"actual wrong bytes")
    with pytest.raises(ValueError, match="media"):
        restore(engine, document, directory)
    assert target.read_bytes() == b"actual wrong bytes"
    engine.dispose()


@pytest.mark.parametrize(
    "damage", ["owner", "duplicate", "extraneous", "selection", "nonfinite"]
)
def test_import_adverse_union_rejected(database, damage):
    from copy import deepcopy

    from app.snapshots import validate
    from jsonschema import ValidationError

    song = populate_project(database)
    engine = create_db_engine(database)
    original = project(engine, song)
    document = deepcopy(original)
    if damage == "owner":
        document["rows"]["take"][0]["owner_id"] = "01K70000000000000000000009"
    elif damage == "duplicate":
        document["rows"]["take"].append(deepcopy(document["rows"]["take"][0]))
    elif damage == "extraneous":
        row = deepcopy(document["rows"]["upload"][0])
        row["id"] = "01K70000000000000000000009"
        document["rows"]["upload"].append(row)
    elif damage == "selection":
        document["rows"]["song"][0]["master_take_id"] = "01K70000000000000000000009"
    else:
        document["rows"]["job"][0]["request"]["invalid"] = float("inf")
    with pytest.raises((ValueError, ValidationError)):
        validate(document, database.parent)
    assert project(engine, song) == original
    engine.dispose()


def test_r02_08_take_descendants_only_and_delete_recompute(database):
    from app.models import Job, LineageEdge, Take, new_id
    from sqlalchemy.orm import Session

    song = populate_project(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        job = session.query(Job).filter(Job.task == "music.song").one()
        independent = new_id()
        session.add(
            Take(
                id=independent,
                owner_id=job.owner_id,
                song_id=song,
                job_id=job.id,
                batch_id=new_id(),
                root_id=independent,
                derivation="original",
                task="music.song",
                model_id="mock",
                model_version="1",
                seed=0,
                commercial_use=True,
            )
        )
        session.flush()
        edge = session.query(LineageEdge).filter(LineageEdge.child_type == "take").one()
        child = edge.child_id
        session.connection().exec_driver_sql("CREATE TABLE root_updates (id TEXT)")
        session.connection().exec_driver_sql(
            "CREATE TRIGGER observe_roots AFTER UPDATE OF root_id ON take BEGIN INSERT INTO root_updates VALUES(NEW.id); END"
        )
        session.delete(edge)
        session.commit()
        assert session.connection().exec_driver_sql(
            "SELECT id FROM root_updates"
        ).scalars().all() == [child]
        assert session.get(Take, child).root_id == child
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            session.get(Take, independent).root_id = child
            session.commit()
        session.rollback()
    engine.dispose()


def test_real_sqlite_index_plans(database):
    with sqlite3.connect(database) as db:
        queries = [
            "SELECT root_id FROM snapshot_member WHERE entity_type='artwork' AND entity_id='x'",
            "SELECT id FROM asset WHERE subject_type='character' AND subject_id='x'",
            "SELECT id FROM lineage_edge WHERE child_type='take' AND child_id='x'",
            "SELECT id FROM song WHERE is_dependency_only=0 AND snapshot_dirty=1",
            "SELECT rowid FROM song_fts_identity WHERE song_id='x'",
        ]
        plans = {
            query: db.execute("EXPLAIN QUERY PLAN " + query).fetchall()
            for query in queries
        }
        assert all(
            any("SEARCH" in row[3] and "INDEX" in row[3] for row in plan)
            for plan in plans.values()
        ), plans


def test_r02_04_bad_song_does_not_block_server_start(database):
    import asyncio

    from app.main import create_app
    from app.settings import Settings

    song = populate_project(database)
    good, _ = song_rows(database)
    # Prepare the database at the server's configured path, preserving FK/WAL.
    root = database.parent / "startup"
    from app.backup import backup, restore_backup

    root.joinpath("db").mkdir(parents=True)
    copy = backup(database, database.parent / "startup-copy")
    restore_backup(copy, root / "db/studio.sqlite")
    with sqlite3.connect(root / "db/studio.sqlite") as db:
        db.execute("UPDATE video_project SET timeline=? WHERE song_id=?", ("{}", song))

    async def exercise():
        application = create_app(
            Settings(_env_file=None, data_dir=root, engine_token="synthetic-test-token")
        )
        async with application.router.lifespan_context(application):
            assert (root / "songs" / good / "song.json").is_file()
            with application.state.db.connect() as connection:
                assert (
                    connection.exec_driver_sql(
                        "SELECT snapshot_dirty FROM song WHERE id=?", (song,)
                    ).scalar_one()
                    == 1
                )

    asyncio.run(exercise())
    assert "snapshot.failed" in (root / "logs/server.log").read_text()


def test_support_root_rejects_publication_until_promotion(database):
    from app.models import Artwork, Collection, Song
    from app.snapshots import publish, restore
    from sqlalchemy.orm import Session

    first = populate_project(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        collection = session.query(Collection).one()
        collection.cover_artwork_id = session.query(Artwork).one().id
        session.get(Song, second).collection_id = collection.id
        session.commit()
    dependent = project(engine, second)
    complete = project(engine, first)
    target = database.parent / "promotion.sqlite"
    migrate(target)
    restored = create_db_engine(target)
    restore(restored, dependent, database.parent / "promotion")
    with restored.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT count(*) FROM dispatchable_job"
            ).scalar_one()
            == 0
        )
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError), restored.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE song SET title=? WHERE id=?", ("ordinary edit", first)
        )
    with pytest.raises(ValueError, match="support"):
        project(restored, first)
    with pytest.raises(ValueError, match="support"):
        publish(restored, first, database.parent / "promotion")
    restore(restored, complete, database.parent / "promotion")
    assert project(restored, first) == complete
    with restored.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT count(*) FROM song WHERE is_dependency_only=0"
            ).scalar_one()
            == 2
        )
    restored.dispose()
    engine.dispose()


def test_purge_empty_published_project_cleans_local_metadata(database):
    from app.snapshots import publish

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    publish(engine, song, database.parent)
    with engine.begin() as connection:
        connection.exec_driver_sql("DELETE FROM song WHERE id=?", (song,))
    with engine.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT count(*) FROM snapshot_member"
            ).scalar_one()
            == 0
        )
        assert (
            connection.exec_driver_sql(
                "SELECT count(*) FROM song_fts_identity"
            ).scalar_one()
            == 0
        )
    engine.dispose()


def test_dependency_hash_uses_sqlite_typed_numeric_normalization(database):
    from app.models import Artwork, Collection, Job, Song
    from app.snapshots import validate
    from sqlalchemy.orm import Session

    first = populate_project(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.query(Job).filter(Job.task == "music.song").one().progress = 0.0
        collection = session.query(Collection).one()
        collection.cover_artwork_id = session.query(Artwork).one().id
        session.get(Song, second).collection_id = collection.id
        session.commit()
    document = project(engine, second)
    assert document["dependencies"]["rows"]["song"][0]["id"] == first
    job = next(
        row
        for row in document["dependencies"]["rows"]["job"]
        if row["task"] == "music.song"
    )
    assert type(job["progress"]) is float
    job["progress"] = 0
    validate(document, database.parent)
    engine.dispose()


def test_r02_07_query_count_independent_of_unrelated_library(database):
    from app.models import Song
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    song = populate_project(database)
    engine = create_db_engine(database, data_dir=database.parent)
    reconcile(engine, database.parent)
    statements = []

    @event.listens_for(engine, "before_cursor_execute")
    def record(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    with engine.connect() as connection:
        identifier = connection.exec_driver_sql(
            "SELECT id FROM take WHERE song_id=? LIMIT 1", (song,)
        ).scalar_one()

    def edit(rating):
        statements.clear()
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE take SET rating=? WHERE id=?", (rating, identifier)
            )
        reconcile(engine, database.parent)
        return list(statements)

    small = edit(2)
    with Session(engine) as session:
        owner = session.query(Song).filter(Song.id == song).one().owner_id
        session.add_all(
            [
                Song(owner_id=owner, title=f"unrelated {index}", style_prompt="")
                for index in range(40)
            ]
        )
        session.commit()
    large = edit(3)
    assert len(small) == len(large) and len(large) < 200
    assert all("WHERE" in statement for statement in large if "FROM take" in statement)
    (database.parent / "query-count-proof.json").write_text(
        json.dumps(
            {
                "small_library_roots": 1,
                "large_library_roots": 41,
                "small_select_count": len(small),
                "large_select_count": len(large),
                "large_select_sql": large,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    engine.dispose()


def test_r02_07_old_new_character_ref_consumers(database):
    from app.models import Artwork, Character, CharacterRef, Collection, Song
    from sqlalchemy.orm import Session

    first = populate_project(database)
    consumer, _ = song_rows(database)
    unrelated, _ = song_rows(database)
    engine = create_db_engine(database, data_dir=database.parent)
    with Session(engine) as session:
        collection = session.query(Collection).one()
        collection.cover_artwork_id = session.query(Artwork).one().id
        session.get(Song, consumer).collection_id = collection.id
        character = session.query(Character).one()
        other = Character(
            owner_id=character.owner_id,
            name="unreferenced",
            description="fixture",
            kind="fictional",
            consent="fictional",
        )
        session.add(other)
        session.commit()
        ref = session.query(CharacterRef).one().id
        other_id = other.id
    before = {
        identifier: (database.parent / "songs" / identifier / "song.json")
        .stat()
        .st_mtime_ns
        for identifier in (first, consumer, unrelated)
    }
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE character_ref SET character_id=? WHERE id=?", (other_id, ref)
        )
    reconcile(engine, database.parent)
    after = {
        identifier: (database.parent / "songs" / identifier / "song.json")
        .stat()
        .st_mtime_ns
        for identifier in before
    }
    assert after[first] != before[first]
    assert after[consumer] == before[consumer] and after[unrelated] == before[unrelated]
    engine.dispose()
