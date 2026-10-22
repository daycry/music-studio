"""Escenarios nuevos de review2, con SQLite real y pruebas acotadas."""

import copy
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import create_db_engine, migrate
from app.models import Shot, ShotVersion, new_id
from app.snapshots import project, publish, reconcile, restore, validate
from sqlalchemy import event, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_persistence_t02 import populate_project, song_rows

PHASE = Path.cwd() / ".cache/dev-cycle/m1/t02-review-fix2-dispatch1"


@pytest.fixture
def database():
    directory = PHASE / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    path = directory / "studio.sqlite"
    migrate(path)
    return path


@pytest.mark.parametrize("move", ["shot", "video_project"])
@pytest.mark.parametrize("writer", ["sql", "core", "orm"])
def test_r02_10_transitive_job_move(database, move, writer):
    first = populate_project(database)
    with sqlite3.connect(database) as c:
        c.execute("DELETE FROM setting")
        c.execute("DELETE FROM provider")
    second = populate_project(database)
    engine = create_db_engine(database)
    with engine.begin() as c:
        video, take = c.exec_driver_sql(
            "SELECT id,take_id FROM video_project WHERE song_id=?", (second,)
        ).one()
        shot, old_video = c.exec_driver_sql(
            "SELECT s.id,s.video_project_id FROM shot s JOIN video_project v ON s.video_project_id=v.id WHERE v.song_id=?",
            (first,),
        ).one()
        job = c.exec_driver_sql(
            "SELECT id FROM job WHERE song_id=? LIMIT 1", (first,)
        ).scalar_one()
        c.exec_driver_sql("UPDATE shot SET current_version_id=NULL WHERE id=?", (shot,))
        c.exec_driver_sql("UPDATE shot SET key=? WHERE id=?", ("moving", shot))
        c.exec_driver_sql(
            "UPDATE shot_version SET job_id=? WHERE shot_id=?", (job, shot)
        )
    from app.models import VideoProject

    model = Shot if move == "shot" else VideoProject
    identifier = shot if move == "shot" else old_video
    changes = (
        {"video_project_id": video}
        if move == "shot"
        else {"song_id": second, "take_id": take}
    )
    try:
        if writer == "sql":
            with sqlite3.connect(database) as c, pytest.raises(sqlite3.IntegrityError):
                c.execute(
                    "UPDATE "
                    + move
                    + " SET "
                    + ",".join(k + "=?" for k in changes)
                    + " WHERE id=?",
                    (*changes.values(), identifier),
                )
        elif writer == "core":
            with pytest.raises(IntegrityError), engine.begin() as c:
                c.execute(update(model).where(model.id == identifier).values(**changes))
        else:
            with Session(engine) as s:
                row = s.get(model, identifier)
                for k, v in changes.items():
                    setattr(row, k, v)
                with pytest.raises(IntegrityError):
                    s.commit()
                s.rollback()
        assert project(engine, first)["song_id"] == first
    finally:
        engine.dispose()


@pytest.mark.parametrize("writer", ["sql", "orm", "json"])
def test_r02_11_selection_own_shot(database, writer):
    song = populate_project(database)
    engine = create_db_engine(database)
    with Session(engine) as s:
        shot = s.query(Shot).one()
        other = Shot(
            owner_id=shot.owner_id,
            video_project_id=shot.video_project_id,
            key="other",
            kind="still",
        )
        s.add(other)
        s.flush()
        version = ShotVersion(owner_id=shot.owner_id, shot_id=other.id, prompt="other")
        s.add(version)
        s.commit()
        sid, vid = shot.id, version.id
    # Remove the extra timeline shot from root? It must exist in the timeline.
    with engine.begin() as c:
        timeline = json.loads(
            c.exec_driver_sql("SELECT timeline FROM video_project").scalar_one()
        )
        extra = copy.deepcopy(timeline["shots"][0])
        extra["key"] = "other"
        timeline["shots"].append(extra)
        c.exec_driver_sql(
            "UPDATE video_project SET timeline=?", (json.dumps(timeline),)
        )
    before = project(engine, song)
    if writer == "json":
        bad = copy.deepcopy(before)
        next(r for r in bad["rows"]["shot"] if r["id"] == sid)["current_version_id"] = (
            vid
        )
        with pytest.raises(ValueError, match="selection|selected|shot"):
            validate(bad, database.parent)
    elif writer == "sql":
        with sqlite3.connect(database) as c, pytest.raises(sqlite3.IntegrityError):
            c.execute("UPDATE shot SET current_version_id=? WHERE id=?", (vid, sid))
    else:
        with Session(engine) as s:
            s.get(Shot, sid).current_version_id = vid
            with pytest.raises(IntegrityError):
                s.commit()
            s.rollback()
    assert project(engine, song) == before
    engine.dispose()


def support_import(database):
    first = populate_project(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    with engine.begin() as c:
        collection = c.exec_driver_sql(
            "SELECT collection_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        cover = c.exec_driver_sql(
            "SELECT cover_artwork_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        c.exec_driver_sql(
            "UPDATE collection SET cover_artwork_id=? WHERE id=?", (cover, collection)
        )
        c.exec_driver_sql(
            "UPDATE song SET collection_id=? WHERE id=?", (collection, second)
        )
        version = c.exec_driver_sql("SELECT id FROM shot_version LIMIT 1").scalar_one()
        owner = c.exec_driver_sql(
            "SELECT owner_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        c.exec_driver_sql(
            "INSERT INTO lineage_edge(id,owner_id,child_type,child_id,parent_type,parent_id,role,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                new_id(),
                owner,
                "artwork",
                cover,
                "shot_version",
                version,
                "source",
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        )
    original = project(engine, first)
    consumer = project(engine, second)
    target = database.parent / "support.sqlite"
    migrate(target)
    restored = create_db_engine(target)
    restore(restored, consumer, database.parent / "restored")
    engine.dispose()
    return restored, first, second, original


@pytest.mark.parametrize(
    "table,field,value",
    [
        ("take", "rating", 5),
        ("lyrics_version", "text", "edited"),
        ("artwork", "prompt", "edited"),
    ],
)
def test_r02_12_support_content_update(database, table, field, value):
    engine, first, second, original = support_import(database)
    with pytest.raises(IntegrityError), engine.begin() as c:
        c.exec_driver_sql(
            f"UPDATE {table} SET {field}=? WHERE song_id=?", (value, first)
        )
    assert project(engine, second)["dependencies"]["rows"][table]
    restore(engine, original, database.parent / "restored")
    assert project(engine, first) == original
    engine.dispose()


@pytest.mark.parametrize("entity", ["collection", "artwork"])
def test_r02_13_new_dependency_second_connection(database, monkeypatch, entity):
    from app import snapshots

    first = populate_project(database)
    second, _ = song_rows(database)
    engine = create_db_engine(database)
    publish(engine, second, database.parent)
    with engine.begin() as c:
        collection = c.exec_driver_sql(
            "SELECT collection_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        cover = c.exec_driver_sql(
            "SELECT cover_artwork_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        c.exec_driver_sql(
            "UPDATE collection SET cover_artwork_id=? WHERE id=?", (cover, collection)
        )
        c.exec_driver_sql(
            "UPDATE song SET collection_id=? WHERE id=?", (collection, second)
        )
    original = snapshots.validate
    changed = []

    def interleave(document, directory):
        original(document, directory)
        if not changed:
            with sqlite3.connect(database, timeout=1) as foreign:
                foreign.execute(
                    "UPDATE collection SET name=? WHERE id=?"
                    if entity == "collection"
                    else "UPDATE artwork SET prompt=? WHERE id=?",
                    (
                        "concurrent real commit",
                        collection if entity == "collection" else cover,
                    ),
                )
            changed.append(True)

    monkeypatch.setattr(snapshots, "validate", interleave)
    publish(engine, second, database.parent)
    with engine.connect() as c:
        dirty = c.exec_driver_sql(
            "SELECT snapshot_dirty FROM song WHERE id=?", (second,)
        ).scalar_one()
    saved = json.loads(
        (database.parent / "songs" / second / "song.json").read_text(encoding="utf-8")
    )
    assert changed and (dirty == 1 or saved == project(engine, second))
    monkeypatch.setattr(snapshots, "validate", original)
    reconcile(engine, database.parent)
    assert json.loads(
        (database.parent / "songs" / second / "song.json").read_text(encoding="utf-8")
    ) == project(engine, second)
    engine.dispose()


def test_r02_14_due_candidate_lock_cancellation(database):
    import asyncio

    from app.backup import DailyBackup, backup

    candidate = backup(database, database.parent / "backups")
    held, release = threading.Event(), threading.Event()

    def hold():
        with sqlite3.connect(candidate) as c:
            c.execute("BEGIN EXCLUSIVE")
            held.set()
            release.wait(8)
            c.rollback()

    locker = threading.Thread(target=hold)
    locker.start()
    assert held.wait(2)

    async def exercise():
        scheduler = DailyBackup(database, candidate.parent, logging.getLogger("fix2"))
        scheduler.start()
        await asyncio.sleep(0.15)
        close = asyncio.create_task(scheduler.close())
        done, _ = await asyncio.wait({close}, timeout=0.7)
        cancelled_before_release = bool(done)
        release.set()
        await asyncio.wait_for(close, 6)
        assert all(not t.is_alive() for t in scheduler.executor._threads)
        assert cancelled_before_release, (
            "Candidate backup ignored cancellation until foreign EXCLUSIVE lock released"
        )

    try:
        asyncio.run(exercise())
    finally:
        release.set()
        locker.join(9)
    assert not locker.is_alive()
    assert not list(candidate.parent.glob(".backup-*"))


def test_r02_17_due_reads_latest_valid_only(database, monkeypatch):
    from app import backup as module

    now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    directory = database.parent / "backups"
    for days in range(14):
        module.backup(database, directory, now - timedelta(days=days))
    opened = []
    connect = sqlite3.connect

    def recording(path, *args, **kwargs):
        if "studio-backup-" in str(path):
            opened.append(str(path))
        return connect(path, *args, **kwargs)

    monkeypatch.setattr(module.sqlite3, "connect", recording)
    assert module.due(database, directory, now) is None
    assert len(opened) == 1, opened


def scaled_project(database, count):
    from app.models import Analysis, Asset, Job, LineageEdge, Take

    song, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as s:
        job = Job(
            owner_id=owner, song_id=song, task="music.song", lane="gpu", request={}
        )
        s.add(job)
        s.flush()
        root = None
        for i in range(count):
            identifier = new_id()
            take = Take(
                id=identifier,
                root_id=identifier,
                owner_id=owner,
                song_id=song,
                job_id=job.id,
                batch_id=new_id(),
                derivation="original",
                task="music.song",
                model_id="mock",
                model_version="1",
                seed=i,
                commercial_use=True,
            )
            s.add(take)
            s.flush()
            s.add(
                Analysis(
                    owner_id=owner,
                    take_id=identifier,
                    kind="beats",
                    analyzer_id="mock",
                    analyzer_version="1",
                    data={},
                )
            )
            for role in ("master", "listen"):
                s.add(
                    Asset(
                        owner_id=owner,
                        subject_type="take",
                        subject_id=identifier,
                        role=role,
                        path=f"songs/{song}/takes/{identifier}/{role}.flac",
                        media_type="audio/flac",
                        sha256="c" * 64,
                        bytes=12,
                    )
                )
            if root:
                s.add(
                    LineageEdge(
                        owner_id=owner,
                        child_type="take",
                        child_id=identifier,
                        parent_type="take",
                        parent_id=root,
                        role="source",
                    )
                )
            else:
                root = identifier
        s.commit()
    engine.dispose()
    return song


def test_r02_15_native_select_count_scaling(database):
    small = scaled_project(database, 20)
    large = scaled_project(database, 200)
    engine = create_db_engine(database)
    counts = []
    queries = []

    def record(c, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    for song in (small, large):
        queries.clear()
        document = project(engine, song)
        validate(document, database.parent)
        counts.append(len(queries))
    for _ in range(41):
        song_rows(database)
    queries.clear()
    project(engine, large)
    assert len(queries) == counts[1]
    (PHASE / ("worker-query-counts-" + uuid4().hex + ".json")).write_text(
        json.dumps(
            {"20": counts[0], "200": counts[1], "200_plus_41_other": len(queries)}
        )
    )
    assert counts[1] <= counts[0] * 2 + 10, counts
    assert all("WHERE" in sql.upper().split() for sql in queries), queries
    engine.dispose()


def test_r02_16_in_memory_lookup_scaling(database):
    counts = []

    class Counted(dict):
        operations = 0

        def get(self, key, default=None):
            type(self).operations += 1
            return super().get(key, default)

        def __getitem__(self, key):
            type(self).operations += 1
            return super().__getitem__(key)

    for size in (20, 200):
        song = scaled_project(database, size)
        engine = create_db_engine(database)
        document = project(engine, song)
        for table, rows in document["rows"].items():
            document["rows"][table] = [Counted(row) for row in rows]
        Counted.operations = 0
        validate(document, database.parent)
        counts.append(Counted.operations)
        engine.dispose()
    (PHASE / ("worker-memory-counts-" + uuid4().hex + ".json")).write_text(
        json.dumps({"20": counts[0], "200": counts[1]})
    )
    assert counts[1] <= counts[0] * 15, counts


@pytest.mark.parametrize(
    "operation",
    [
        "delete",
        "insert",
        "move_out",
        "move_in",
        "asset",
        "lineage",
        "analysis",
        "shot_version",
        "bulk",
    ],
)
def test_support_content_associations_are_protected(database, operation):
    engine, first, second, _original = support_import(database)
    with engine.connect() as c:
        take = c.exec_driver_sql(
            "SELECT id FROM take WHERE song_id=? LIMIT 1", (first,)
        ).scalar_one()
        owner = c.exec_driver_sql(
            "SELECT owner_id FROM song WHERE id=?", (first,)
        ).scalar_one()
        artwork = c.exec_driver_sql(
            "SELECT id FROM artwork WHERE song_id=?", (first,)
        ).scalar_one()
        version = c.exec_driver_sql(
            "SELECT v.id FROM shot_version v JOIN shot s ON s.id=v.shot_id JOIN video_project p ON p.id=s.video_project_id WHERE p.song_id=?",
            (first,),
        ).scalar_one()
    statements = {
        "delete": ("DELETE FROM artwork WHERE id=?", (artwork,)),
        "insert": (
            "INSERT INTO lyrics_version(id,owner_id,song_id,text,source,declaration,sha256,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                new_id(),
                owner,
                first,
                "new",
                "manual",
                "own",
                "a" * 64,
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        ),
        "move_out": ("UPDATE artwork SET song_id=? WHERE id=?", (second, artwork)),
        "move_in": (
            "INSERT INTO artwork(id,owner_id,song_id,kind,source,rights,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                new_id(),
                owner,
                second,
                "cover",
                "upload",
                "own",
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        ),
        "asset": (
            "UPDATE asset SET role=? WHERE subject_type=? AND subject_id=?",
            ("listen", "take", take),
        ),
        "lineage": (
            "UPDATE lineage_edge SET role=? WHERE child_type=?",
            ("edited", "artwork"),
        ),
        "analysis": (
            "INSERT INTO analysis(id,owner_id,take_id,kind,analyzer_id,analyzer_version,data,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                new_id(),
                owner,
                take,
                "beats",
                "new",
                "1",
                "{}",
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        ),
        "shot_version": (
            "UPDATE shot_version SET prompt=? WHERE id=?",
            ("edited", version),
        ),
    }
    if operation == "bulk":
        from app.models import Take

        with Session(engine) as s:
            with pytest.raises(IntegrityError, match="Support"):
                s.query(Take).filter(Take.song_id == first).update({"rating": 4})
            s.rollback()
    elif operation == "move_in":
        sql, parameters = statements[operation]
        with engine.begin() as c:
            c.exec_driver_sql(sql, parameters)
        with pytest.raises(IntegrityError, match="Support"), engine.begin() as c:
            c.exec_driver_sql(
                "UPDATE artwork SET song_id=? WHERE id=?", (first, parameters[0])
            )
    else:
        with pytest.raises(IntegrityError, match="Support"), engine.begin() as c:
            c.exec_driver_sql(*statements[operation])
    # Shared globals are still independently editable and invalidate consumers.
    with engine.begin() as c:
        c.exec_driver_sql("UPDATE collection SET name=?", ("global edit",))
        c.exec_driver_sql("UPDATE character SET description=?", ("global edit",))
    with engine.connect() as c:
        assert not c.exec_driver_sql("SELECT song_id FROM snapshot_import").fetchall()
    engine.dispose()


@pytest.mark.parametrize("populated", [False, True])
@pytest.mark.parametrize("baseline", ["0002", "0001", "base"])
def test_fix2_empty_populated_migration_cycles(database, populated, baseline):
    from alembic import command
    from alembic.config import Config

    song = populate_project(database) if populated else None
    engine = create_db_engine(database)
    before = project(engine, song) if populated else None
    engine.dispose()
    config = Config()
    config.set_main_option(
        "script_location", str(Path("apps/server/app/migrations").resolve())
    )
    config.attributes["database_path"] = database
    command.downgrade(config, baseline)
    with sqlite3.connect(database) as c:
        assert not c.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'fix2_%' OR name IN ('snapshot_import','snapshot_clock')"
        ).fetchall()
        if baseline == "0002":
            assert c.execute("SELECT version_num FROM alembic_version").fetchone() == (
                "0002",
            )
    command.upgrade(config, "0003")
    engine = create_db_engine(database)
    with engine.connect() as c:
        assert (
            c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
            == "0003"
        )
        assert (
            c.exec_driver_sql("SELECT count(*) FROM snapshot_import").scalar_one() == 0
        )
        assert not c.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if before is not None and baseline != "base":
        assert project(engine, song) == before
    engine.dispose()


def test_r02_17_corrupt_latest_falls_back_native(database, monkeypatch):
    from app import backup as module

    now = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    directory = database.parent / "backups"
    module.backup(database, directory, now - timedelta(hours=2))
    bad = module.backup(database, directory, now - timedelta(hours=1))
    with sqlite3.connect(bad) as c:
        c.execute("DROP TABLE song_fts")
    opened = []
    connect = sqlite3.connect

    def record(path, *args, **kwargs):
        if "studio-backup-" in str(path):
            opened.append(str(path))
        return connect(path, *args, **kwargs)

    monkeypatch.setattr(module.sqlite3, "connect", record)
    assert module.due(database, directory, now) is None
    assert len(opened) == 2
    assert bad.name in opened[0]


def test_projection_large_in_batches(database):
    song = scaled_project(database, 405)
    engine = create_db_engine(database)
    document = project(engine, song)
    validate(document, database.parent)
    assert len(document["rows"]["take"]) == 405
    assert len(document["rows"]["asset"]) == 810
    target = database.parent / "large.sqlite"
    migrate(target)
    restored = create_db_engine(target)
    restore(restored, document, database.parent / "large")
    assert project(restored, song) == document
    restored.dispose()
    engine.dispose()


def test_support_additional_dependencies_then_original_promotion(database):
    from app.models import Artwork, Collection, Song

    restored, first, second, original = support_import(database)
    source = create_db_engine(database)
    third, owner = song_rows(database)
    with Session(source) as s:
        artwork = Artwork(
            owner_id=owner,
            song_id=first,
            kind="cover",
            source="upload",
            rights="own",
            prompt="new dependency",
        )
        s.add(artwork)
        s.flush()
        collection = Collection(
            owner_id=owner, name="Additional", cover_artwork_id=artwork.id
        )
        s.add(collection)
        s.flush()
        s.get(Song, third).collection_id = collection.id
        s.commit()
        aid = artwork.id
    third_document = project(source, third)
    restore(restored, third_document, database.parent / "restored")
    with restored.connect() as c:
        assert (
            c.exec_driver_sql(
                "SELECT is_dependency_only FROM song WHERE id=?", (first,)
            ).scalar_one()
            == 1
        )
        assert (
            c.exec_driver_sql(
                "SELECT prompt FROM artwork WHERE id=?", (aid,)
            ).scalar_one()
            == "new dependency"
        )
    # Promote the now complete source, preserving all formerly imported rows.
    full = project(source, first)
    restore(restored, full, database.parent / "restored")
    assert project(restored, first) == full
    assert (
        project(restored, second)["dependencies"]["rows"]["song"][0]
        == original["rows"]["song"][0]
    )
    source.dispose()
    restored.dispose()


def test_scheduler_does_not_duplicate_initial_check(database, monkeypatch):
    import asyncio

    from app import backup as module

    calls = []
    due = module.due

    def record(*args, **kwargs):
        calls.append(True)
        return due(*args, **kwargs)

    monkeypatch.setattr(module, "due", record)

    async def exercise():
        scheduler = module.DailyBackup(
            database, database.parent / "backups", logging.getLogger("fix2")
        )
        await scheduler.initial()
        scheduler.start()
        await asyncio.sleep(0.1)
        await scheduler.close()

    asyncio.run(exercise())
    assert len(calls) == 1


@pytest.mark.parametrize("failure", ["file", "commit"])
def test_publisher_failure_pending_and_repair(database, monkeypatch, failure):
    from app import snapshots

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    publish(engine, song, database.parent)
    with engine.begin() as c:
        c.exec_driver_sql("UPDATE song SET title=? WHERE id=?", ("new content", song))
    if failure == "file":
        original = snapshots.os.replace

        def fail(*args):
            raise OSError("private file failure")

        monkeypatch.setattr(snapshots.os, "replace", fail)
        with pytest.raises(OSError):
            publish(engine, song, database.parent)
        monkeypatch.setattr(snapshots.os, "replace", original)
    else:

        def break_commit(c):
            c.exec_driver_sql(
                "INSERT INTO snapshot_member(root_id,entity_type,entity_id) VALUES(?,?,?)",
                ("01K70000000000000000000099", "song", song),
            )

        event.listen(engine, "commit", break_commit)
        with pytest.raises(IntegrityError):
            publish(engine, song, database.parent)
        event.remove(engine, "commit", break_commit)
    with engine.connect() as c:
        assert (
            c.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (song,)
            ).scalar_one()
            == 1
        )
    reconcile(engine, database.parent)
    assert json.loads(
        (database.parent / "songs" / song / "song.json").read_text(encoding="utf-8")
    ) == project(engine, song)
    assert not list((database.parent / "songs" / song).glob(".song-*"))
    engine.dispose()


def test_wal_generation_and_projection_same_snapshot(database):
    song, _ = song_rows(database)
    engine = create_db_engine(database)
    changed = []

    def interleave(c, cursor, statement, parameters, context, many):
        if "SELECT song.is_dependency_only" in statement and not changed:
            with sqlite3.connect(database) as foreign:
                foreign.execute(
                    "UPDATE song SET title=? WHERE id=?", ("new WAL commit", song)
                )
            changed.append(True)

    event.listen(engine, "before_cursor_execute", interleave)
    publish(engine, song, database.parent)
    event.remove(engine, "before_cursor_execute", interleave)
    saved = json.loads(
        (database.parent / "songs" / song / "song.json").read_text(encoding="utf-8")
    )
    assert saved["rows"]["song"][0]["title"] == "Horizonte"
    with engine.connect() as c:
        assert (
            c.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (song,)
            ).scalar_one()
            == 1
        )
    reconcile(engine, database.parent)
    assert (
        json.loads(
            (database.parent / "songs" / song / "song.json").read_text(encoding="utf-8")
        )["rows"]["song"][0]["title"]
        == "new WAL commit"
    )
    engine.dispose()


def test_competing_native_publish_never_cleans_stale_file(database, monkeypatch):
    from app import snapshots

    song, _ = song_rows(database)
    engine = create_db_engine(database)
    other = create_db_engine(database)
    replacement = snapshots.os.replace
    changed = []

    def compete(source, target):
        if not changed:
            changed.append(True)
            with other.begin() as c:
                c.exec_driver_sql(
                    "UPDATE song SET title=? WHERE id=?", ("competing content", song)
                )
            publish(other, song, database.parent)
        return replacement(source, target)

    monkeypatch.setattr(snapshots.os, "replace", compete)
    publish(engine, song, database.parent)
    with engine.connect() as c:
        assert (
            c.exec_driver_sql(
                "SELECT snapshot_dirty FROM song WHERE id=?", (song,)
            ).scalar_one()
            == 1
        )
    monkeypatch.setattr(snapshots.os, "replace", replacement)
    reconcile(engine, database.parent)
    assert json.loads(
        (database.parent / "songs" / song / "song.json").read_text(encoding="utf-8")
    ) == project(other, song)
    engine.dispose()
    other.dispose()


@pytest.mark.parametrize("valid", [True, False])
def test_deferred_initial_shot_selection(database, valid):
    song = populate_project(database)
    engine = create_db_engine(database)
    before = project(engine, song)
    with engine.connect() as c:
        owner, video = c.exec_driver_sql("SELECT owner_id,id FROM video_project").one()
        oldshot = c.exec_driver_sql("SELECT id FROM shot").scalar_one()
    shot, version = new_id(), new_id()

    def construct(c):
        c.exec_driver_sql(
            "INSERT INTO shot(id,owner_id,video_project_id,key,kind,current_version_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                shot,
                owner,
                video,
                "new",
                "still",
                version,
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        )
        c.exec_driver_sql(
            "INSERT INTO shot_version(id,owner_id,shot_id,prompt,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (
                version,
                owner,
                shot if valid else oldshot,
                "initial",
                "2026-10-07T00:00:00Z",
                "2026-10-07T00:00:00Z",
            ),
        )

    if valid:
        with engine.begin() as c:
            construct(c)
        with engine.connect() as c:
            assert (
                c.exec_driver_sql(
                    "SELECT shot_id FROM shot_version WHERE id=?", (version,)
                ).scalar_one()
                == shot
            )
    else:
        with pytest.raises(IntegrityError, match="shot selection"), engine.begin() as c:
            construct(c)
        assert project(engine, song) == before
    engine.dispose()
