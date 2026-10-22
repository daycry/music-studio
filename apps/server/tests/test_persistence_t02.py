"""Pruebas de persistencia con datos sintéticos y rutas privadas."""

import sqlite3
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import migrate


def test_schema_finite_json_numbers(database):
    from app.db import create_db_engine

    song_id = populate_project(database)
    engine = create_db_engine(database)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job SET request=? WHERE song_id=?", ('{"invalid":1e999}', song_id)
        )
    engine.dispose()


def test_backup_cancelled_task_closes_executor(database):
    import asyncio
    import logging

    from app.backup import DailyBackup

    async def exercise():
        scheduler = DailyBackup(
            database, database.parent / "backups", logging.getLogger("studio-test")
        )
        scheduler.start()
        await asyncio.sleep(0.01)
        scheduler.task.cancel()
        try:
            await scheduler.close()
        except asyncio.CancelledError:
            pass
        assert scheduler.executor._shutdown, "Executor vivo tras cancelar la tarea"
        assert all(not thread.is_alive() for thread in scheduler.executor._threads)

    asyncio.run(exercise())


from sqlalchemy.exc import IntegrityError


@pytest.fixture
def database():
    directory = (
        Path.cwd()
        / ".cache/dev-cycle/m1/t02-normal-implementation/fixtures"
        / uuid4().hex
    )
    directory.mkdir(parents=True)
    path = directory / "studio.sqlite"
    migrate(path)
    return path


def song_rows(path):
    from app.db import create_db_engine
    from app.models import Song, User
    from sqlalchemy.orm import Session

    engine = create_db_engine(path)
    with Session(engine) as session:
        owner = session.query(User).one().id
        song = Song(owner_id=owner, title="Horizonte", style_prompt="pop")
        session.add(song)
        session.commit()
        result = song.id, owner
    engine.dispose()
    return result


def test_fts_current_lyrics_and_trash(database):
    from app.db import create_db_engine
    from app.models import LyricsVersion, Song
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        lyric = LyricsVersion(
            owner_id=owner,
            song_id=song_id,
            text="luciernagas",
            source="manual",
            declaration="own",
            sha256="a" * 64,
        )
        session.add(lyric)
        session.flush()
        session.get(Song, song_id).current_lyrics_version_id = lyric.id
        session.commit()
    with sqlite3.connect(database) as connection:
        found = connection.execute(
            "SELECT song_id FROM song_fts WHERE song_fts MATCH 'luciernagas'"
        ).fetchall()
        assert found == [(song_id,)]
        connection.execute(
            "UPDATE song SET deleted_at='2026-10-07T00:00:00Z' WHERE id=?", (song_id,)
        )
        assert connection.execute("SELECT count(*) FROM song_fts").fetchone()[0] == 0
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM song_fts").fetchone()[0] == 1
    engine.dispose()


def test_backup_restores_wal_and_fts(database):
    import importlib.util

    song_id, _ = song_rows(database)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("UPDATE song SET title='Aurora' WHERE id=?", (song_id,))
    connection.commit()
    assert Path(str(database) + "-wal").exists()
    assert importlib.util.find_spec("app.backup") is not None, "Falta backup nativo"
    from app.backup import backup

    copy = backup(database, database.parent / "backups")
    with sqlite3.connect(copy) as restored:
        assert restored.execute("SELECT title FROM song").fetchone() == ("Aurora",)
        assert restored.execute(
            "SELECT song_id FROM song_fts WHERE song_fts MATCH 'Aurora'"
        ).fetchone() == (song_id,)
        assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    connection.close()


def test_lineage_multiparent_root_and_trash(database):
    from app.db import create_db_engine
    from app.models import Job, LineageEdge, Take, new_id, utc_now
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        job = Job(
            owner_id=owner, song_id=song_id, task="music.song", lane="gpu", request={}
        )
        session.add(job)
        session.flush()
        takes = []
        for _ in range(3):
            identifier = new_id()
            take = Take(
                id=identifier,
                owner_id=owner,
                song_id=song_id,
                job_id=job.id,
                batch_id=new_id(),
                root_id=identifier,
                derivation="original",
                task="music.song",
                model_id="mock",
                model_version="1",
                seed=str(2**100),
                commercial_use=True,
            )
            session.add(take)
            takes.append(take)
        session.flush()
        for index, parent in enumerate(takes[:2]):
            session.add(
                LineageEdge(
                    owner_id=owner,
                    child_type="take",
                    child_id=takes[2].id,
                    parent_type="take",
                    parent_id=parent.id,
                    role=f"crossfade_{index}",
                )
            )
        session.commit()
        session.refresh(takes[2])
        assert takes[2].root_id == min(take.id for take in takes[:2])
        takes[0].deleted_at = utc_now()
        session.commit()
        assert session.get(Take, takes[2].id) is not None
        assert session.query(LineageEdge).count() == 2
        with pytest.raises(IntegrityError):
            session.add(
                LineageEdge(
                    owner_id=owner,
                    child_type="take",
                    child_id=takes[0].id,
                    parent_type="take",
                    parent_id=takes[2].id,
                    role="source",
                )
            )
            session.commit()
        session.rollback()
    engine.dispose()


def test_snapshot_roundtrip(database):
    import importlib.util

    song_id, _ = song_rows(database)
    assert importlib.util.find_spec("app.snapshots") is not None, (
        "Falta snapshot restaurable"
    )
    from app.db import create_db_engine
    from app.snapshots import project, publish, restore

    engine = create_db_engine(database)
    document = project(engine, song_id)
    data_dir = database.parent / "data"
    publish(engine, song_id, data_dir)
    assert (data_dir / "songs" / song_id / "song.json").is_file()
    target = database.parent / "restore.sqlite"
    migrate(target)
    restored_engine = create_db_engine(target)
    restore(restored_engine, document, data_dir)
    assert project(restored_engine, song_id) == document
    engine.dispose()
    restored_engine.dispose()


def test_snapshot_after_commit(database):
    from app.db import create_db_engine
    from app.models import Song
    from sqlalchemy.orm import Session

    data_dir = database.parent / "data"
    try:
        engine = create_db_engine(database, data_dir=data_dir)
    except TypeError:
        engine = create_db_engine(database)
    with Session(engine) as session:
        owner = session.execute(
            __import__("sqlalchemy").text('SELECT id FROM "user"')
        ).scalar_one()
        song = Song(owner_id=owner, title="Cambiante", style_prompt="")
        session.add(song)
        session.commit()
        target = data_dir / "songs" / song.id / "song.json"
        assert target.is_file(), "No se publica snapshot tras commit"
        song.title = "Actualizada"
        session.commit()
        import json

        assert (
            json.loads(target.read_text(encoding="utf-8"))["rows"]["song"][0]["title"]
            == "Actualizada"
        )
    engine.dispose()


def test_snapshot_after_commit_serializes_reconcile(database, monkeypatch):
    from app import snapshots
    from app.db import create_db_engine
    from app.models import Song
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    data_dir = database.parent / "data"
    engine = create_db_engine(database, data_dir=data_dir)
    with engine.connect() as connection:
        owner = connection.execute(text('SELECT id FROM "user"')).scalar_one()
    first_entered = threading.Event()
    release_first = threading.Event()
    state = {"active": 0, "maximum": 0, "calls": 0}
    state_lock = threading.Lock()
    errors = []

    def reconcile(*_args, **_kwargs):
        with state_lock:
            state["calls"] += 1
            state["active"] += 1
            state["maximum"] = max(state["maximum"], state["active"])
            call = state["calls"]
        if call == 1:
            first_entered.set()
            assert release_first.wait(2)
        with state_lock:
            state["active"] -= 1

    monkeypatch.setattr(snapshots, "_reconcile", reconcile)

    def writer(title):
        try:
            with Session(engine) as session:
                session.add(Song(owner_id=owner, title=title, style_prompt=""))
                session.commit()
        except BaseException as error:  # noqa: BLE001 - recoger el hilo propio
            errors.append(error)

    threads = [
        threading.Thread(target=writer, args=(f"Cancion {i}",)) for i in range(2)
    ]
    for thread in threads:
        thread.start()
    assert first_entered.wait(2)
    time.sleep(0.05)
    with state_lock:
        assert state["maximum"] == 1
    release_first.set()
    for thread in threads:
        thread.join(2)
    assert all(not thread.is_alive() for thread in threads)
    assert not errors
    assert state["calls"] == 2
    engine.dispose()


def test_schema_ordinary_owner_constraint(database):
    from app.db import create_db_engine
    from app.models import Collection, new_id
    from sqlalchemy.orm import Session

    _, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        collection = Collection(owner_id=owner, name="Colección")
        session.add(collection)
        session.commit()
        other = new_id()
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.exec_driver_sql(
                'UPDATE "user" SET id=?,owner_id=?', (other, other)
            )
        # La FK diferida debe rechazar esta operación al confirmar: ya existen hijos.
    engine.dispose()


def test_backup_lifespan_startup_and_shutdown(database):
    from app.main import create_app
    from app.settings import Settings
    from starlette.testclient import TestClient

    root = database.parent / "runtime-data"
    settings = Settings(
        _env_file=None, engine_token="synthetic-test-token", data_dir=root
    )
    app = create_app(settings)
    with TestClient(app):
        assert (root / "db/studio.sqlite").is_file(), "Lifespan no migra la BD"
        assert hasattr(app.state, "backup"), "Falta tarea de backup"
    assert app.state.backup.task.done()
    assert list((root / "backups").glob("studio-backup-*.sqlite"))


def test_schema_timeline_contract():
    import json

    from jsonschema import Draft202012Validator

    path = Path("packages/contracts/timeline-v1.schema.json")
    assert path.is_file(), "Falta contrato timeline-v1"
    schema = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    validator.validate(
        {
            "version": 1,
            "fps": "24/1",
            "duration_s": 5.0,
            "shots": [
                {
                    "key": "s01",
                    "t0": 0.0,
                    "t1": 5.0,
                    "section": "verse",
                    "lyrics": "hola",
                    "transition_in": {"type": "cut"},
                    "characters": [],
                }
            ],
            "subtitles": {"style": "karaoke", "position": "bottom", "font": "Inter"},
            "titles": [],
        }
    )
    assert list(
        validator.iter_errors(
            {
                "version": 1,
                "fps": "0/0",
                "duration_s": -1,
                "shots": [],
                "subtitles": {},
                "titles": [],
            }
        )
    )


@pytest.mark.parametrize(
    "column,value",
    [("id", "invalid"), ("updated_at", "yesterday"), ("tags", "NaN"), ("rev", 0)],
)
def test_schema_rejects_invalid_raw_values(database, column, value):
    from app.db import create_db_engine

    song_id, _ = song_rows(database)
    engine = create_db_engine(database)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            f'UPDATE song SET "{column}"=? WHERE id=?', (value, song_id)
        )
    engine.dispose()


def test_schema_lyrics_crosssong(database):
    from app.db import create_db_engine
    from app.models import LyricsVersion, Song
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    other_id, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        lyric = LyricsVersion(
            owner_id=owner,
            song_id=other_id,
            text="Otra",
            source="manual",
            declaration="own",
            sha256="b" * 64,
        )
        session.add(lyric)
        session.commit()
        session.get(Song, song_id).current_lyrics_version_id = lyric.id
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()


def test_schema_external_asset_rejected(database):
    from app.db import create_db_engine
    from app.models import Asset, new_id
    from sqlalchemy.orm import Session

    _, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(
            Asset(
                owner_id=owner,
                subject_type="cli_run",
                subject_id=new_id(),
                role="master",
                path="cli/test.flac",
                media_type="audio/flac",
                sha256="a" * 64,
                bytes=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()


def test_schema_job_dependency_cycle(database):
    from app.db import create_db_engine
    from app.models import Job, JobDependency
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        jobs = [
            Job(owner_id=owner, song_id=song_id, task="test", lane="cpu", request={})
            for _ in range(3)
        ]
        session.add_all(jobs)
        session.commit()
        for child, parent in zip(jobs[1:], jobs):
            session.add(
                JobDependency(
                    owner_id=owner, job_id=child.id, depends_on_job_id=parent.id
                )
            )
        session.commit()
        session.add(
            JobDependency(
                owner_id=owner, job_id=jobs[0].id, depends_on_job_id=jobs[2].id
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()


def populate_project(path):
    from app.db import create_db_engine
    from app.models import (
        Analysis,
        Artwork,
        Asset,
        Character,
        CharacterRef,
        Collection,
        Export,
        Job,
        JobDependency,
        LineageEdge,
        LyricsVersion,
        Preset,
        Provider,
        Render,
        Setting,
        Shot,
        ShotVersion,
        Song,
        Take,
        Upload,
        VideoCharacter,
        VideoProject,
        new_id,
    )
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(path)
    engine = create_db_engine(path)
    with Session(engine) as session:

        def add(cls, **values):
            entity = cls(id=new_id(), owner_id=owner, **values)
            session.add(entity)
            session.flush()
            return entity

        collection = add(Collection, name="Sintética")
        lyric = add(
            LyricsVersion,
            song_id=song_id,
            text="luciernagas azules",
            source="manual",
            declaration="own",
            sha256="a" * 64,
        )
        job = add(
            Job,
            song_id=song_id,
            task="music.song",
            lane="gpu",
            request={"seed": 2**100},
        )
        second_job = add(
            Job, song_id=song_id, task="audio.analysis", lane="cpu", request={}
        )
        add(JobDependency, job_id=second_job.id, depends_on_job_id=job.id)
        identifier = new_id()
        take = Take(
            id=identifier,
            owner_id=owner,
            song_id=song_id,
            job_id=job.id,
            lyrics_version_id=lyric.id,
            batch_id=new_id(),
            root_id=identifier,
            derivation="original",
            task="music.song",
            model_id="mock",
            model_version="1",
            seed=str(2**100),
            commercial_use=True,
        )
        session.add(take)
        session.flush()
        child_id = new_id()
        child = Take(
            id=child_id,
            owner_id=owner,
            song_id=song_id,
            job_id=job.id,
            lyrics_version_id=lyric.id,
            batch_id=new_id(),
            root_id=child_id,
            derivation="extend",
            task="music.extend",
            model_id="mock",
            model_version="1",
            seed="0",
            commercial_use=True,
        )
        session.add(child)
        session.flush()
        add(
            LineageEdge,
            child_type="take",
            child_id=child.id,
            parent_type="take",
            parent_id=take.id,
            role="source",
        )
        add(
            Analysis,
            take_id=take.id,
            kind="beats",
            analyzer_id="synthetic",
            analyzer_version="1",
            data={"beats": [0, 1]},
        )
        upload = add(
            Upload,
            kind="image",
            path="uploads/synthetic.png",
            sha256="b" * 64,
            media_type="image/png",
            rights="own",
            real_person=False,
            consent="n_a",
        )
        artwork = add(
            Artwork,
            song_id=song_id,
            kind="cover",
            source="upload",
            upload_id=upload.id,
            rights="own",
        )
        character = add(
            Character,
            name="Personaje",
            description="Ficticio",
            kind="fictional",
            consent="fictional",
            sheet_artwork_id=artwork.id,
        )
        add(CharacterRef, character_id=character.id, upload_id=upload.id, view="front")
        add(Preset, kind="style", name="Estilo", payload={})
        timeline = {
            "version": 1,
            "fps": "24/1",
            "duration_s": 5,
            "shots": [
                {
                    "key": "s01",
                    "t0": 0,
                    "t1": 5,
                    "section": "verse",
                    "lyrics": "hola",
                    "transition_in": {"type": "cut"},
                    "characters": [character.id],
                }
            ],
            "subtitles": {"style": "karaoke", "position": "bottom", "font": "Inter"},
            "titles": [],
        }
        video = add(
            VideoProject,
            song_id=song_id,
            take_id=take.id,
            title="Vídeo",
            aspect="16:9",
            level_preset="N0",
            visual_style="still",
            treatment="test",
            timeline=timeline,
        )
        add(
            VideoCharacter,
            video_project_id=video.id,
            character_id=character.id,
            role="cast",
        )
        shot = add(Shot, video_project_id=video.id, key="s01", kind="still")
        version = add(ShotVersion, shot_id=shot.id, prompt="test")
        shot.current_version_id = version.id
        add(
            Render,
            video_project_id=video.id,
            timeline_rev=1,
            aspect="16:9",
            resolution="1920x1080",
            kind="preview",
            subtitles="none",
        )
        add(Export, song_id=song_id, kind="lyrics", expires_at="2026-10-14T00:00:00Z")
        add(
            Asset,
            subject_type="take",
            subject_id=take.id,
            role="master",
            path=f"songs/{song_id}/takes/{take.id}/master.flac",
            media_type="audio/flac",
            sha256="c" * 64,
            bytes=12,
        )
        add(Setting, key="ui.locale", value={"locale": "es"})
        add(Provider, function="text", name="disabled", config={})
        song = session.get(Song, song_id)
        song.collection_id = collection.id
        song.current_lyrics_version_id = lyric.id
        song.master_take_id = take.id
        song.cover_artwork_id = artwork.id
        session.commit()
    engine.dispose()
    return song_id


def test_snapshot_full_project_roundtrip(database):
    from app.db import create_db_engine
    from app.snapshots import project, restore

    song_id = populate_project(database)
    engine = create_db_engine(database)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE take SET deleted_at='2026-10-07T00:00:00Z' WHERE derivation='original'"
        )
    document = project(engine, song_id)
    assert document["rows"]["take"][0]["seed"] in {0, 2**100}
    target = database.parent / "full-restore.sqlite"
    migrate(target)
    restored = create_db_engine(target)
    restore(restored, document, database.parent / "data")
    assert project(restored, song_id) == document
    engine.dispose()
    restored.dispose()


def test_schema_populated_migration_cycle(database):
    from alembic import command
    from alembic.config import Config

    populate_project(database)
    config = Config("apps/server/alembic.ini")
    config.attributes["database_path"] = database
    command.upgrade(config, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM take").fetchone() == (2,)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM take").fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_backup_failure_and_owned_retention(database, monkeypatch):
    import hashlib
    import os
    from datetime import datetime, timedelta, timezone

    from app.backup import backup, due

    directory = database.parent / "backups"
    now = datetime(2026, 10, 7, tzinfo=timezone.utc)
    old = backup(database, directory, now - timedelta(days=15))
    foreign = directory / "important.sqlite"
    foreign.write_text("ajeno", encoding="utf-8")
    good = backup(database, directory, now)
    assert not old.exists()
    assert foreign.read_text(encoding="utf-8") == "ajeno"
    assert due(database, directory, now + timedelta(hours=1)) is None
    digest = hashlib.sha256(good.read_bytes()).hexdigest()

    def fail(*args):
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        backup(database, directory, now + timedelta(days=1))
    assert hashlib.sha256(good.read_bytes()).hexdigest() == digest
    assert not list(directory.glob(".backup-*.sqlite"))


def test_snapshot_collisions_and_paths_leave_database_unchanged(database):
    import copy

    from app.db import create_db_engine
    from app.snapshots import project, restore

    song_id = populate_project(database)
    engine = create_db_engine(database)
    document = project(engine, song_id)
    collision = copy.deepcopy(document)
    collision["rows"]["song"][0]["title"] = "Colisión"
    with pytest.raises(ValueError, match="collision"):
        restore(engine, collision, database.parent / "data")
    bad = copy.deepcopy(document)
    bad["rows"]["asset"][0]["path"] = "../../outside.flac"
    with pytest.raises(ValueError, match="path"):
        restore(engine, bad, database.parent / "data")
    assert project(engine, song_id) == document
    engine.dispose()


def test_snapshot_rejects_secrets_and_invalid_timeline(database):
    import copy

    from app.db import create_db_engine
    from app.snapshots import project, validate

    song_id = populate_project(database)
    engine = create_db_engine(database)
    document = project(engine, song_id)
    bad = copy.deepcopy(document)
    bad["rows"]["job"][0]["request"]["api_key"] = "synthetic-secret"
    with pytest.raises(ValueError, match="secret"):
        validate(bad, database.parent / "data")
    bad = copy.deepcopy(document)
    bad["rows"]["video_project"][0]["timeline"]["shots"][0]["t1"] = 8
    with pytest.raises(ValueError, match="timeline"):
        validate(bad, database.parent / "data")
    engine.dispose()


def test_schema_take_job_crosssong(database):
    from app.db import create_db_engine
    from app.models import Job, Take, new_id
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    other_id, _ = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        job = Job(owner_id=owner, song_id=other_id, task="test", lane="gpu", request={})
        session.add(job)
        session.commit()
        identifier = new_id()
        session.add(
            Take(
                id=identifier,
                owner_id=owner,
                song_id=song_id,
                job_id=job.id,
                batch_id=new_id(),
                root_id=identifier,
                derivation="original",
                task="test",
                model_id="mock",
                model_version="1",
                seed="0",
                commercial_use=True,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()


def test_backup_concurrent_commit(database):
    from app.backup import backup

    song_id, _ = song_rows(database)
    committed = []

    def progress(status, remaining, total):
        if not committed:
            with sqlite3.connect(database) as writer:
                writer.execute(
                    "UPDATE song SET title='Concurrente' WHERE id=?", (song_id,)
                )
            committed.append(True)

    try:
        copy = backup(database, database.parent / "backups", progress=progress)
    except TypeError:
        copy = backup(database, database.parent / "backups")
    assert committed, "No hay commit real durante el backup"
    with sqlite3.connect(copy) as restored:
        assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        # El snapshot de backup puede preceder al commit concurrente; ambos son íntegros.
        assert restored.execute("SELECT title FROM song").fetchone()[0] in {
            "Horizonte",
            "Concurrente",
        }


def test_snapshot_symlink_directory_rejected(database):
    import os

    from app.db import create_db_engine
    from app.snapshots import publish

    song_id, _ = song_rows(database)
    root = database.parent / "data"
    root.mkdir()
    (root / "songs").mkdir()
    target = root / "other"
    target.mkdir()
    try:
        os.symlink(target, root / "songs" / song_id, target_is_directory=True)
    except OSError:
        pytest.skip("Este host no permite crear symlinks; prueba Linux en Docker")
    engine = create_db_engine(database)
    with pytest.raises(ValueError, match="symlink"):
        publish(engine, song_id, root)
    assert not (target / "song.json").exists()
    engine.dispose()


def test_lineage_unbounded_seed_is_integer(database):
    from app.db import create_db_engine
    from app.models import Job, Take, new_id
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        job = Job(owner_id=owner, song_id=song_id, task="test", lane="gpu", request={})
        session.add(job)
        session.flush()
        identifier = new_id()
        take = Take(
            id=identifier,
            owner_id=owner,
            song_id=song_id,
            job_id=job.id,
            batch_id=new_id(),
            root_id=identifier,
            derivation="original",
            task="test",
            model_id="mock",
            model_version="1",
            seed=2**100,
            commercial_use=True,
        )
        session.add(take)
        session.commit()
        session.expire_all()
        assert session.get(Take, identifier).seed == 2**100
    engine.dispose()


def test_schema_ids_are_immutable(database):
    from app.db import create_db_engine
    from app.models import Collection, new_id
    from sqlalchemy.orm import Session

    _, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        collection = Collection(owner_id=owner, name="Inmutable")
        session.add(collection)
        session.commit()
        collection.id = new_id()
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()


def test_schema_resolution_and_focus_point(database):
    from app.db import create_db_engine

    populate_project(database)
    engine = create_db_engine(database)
    for table, column, value in [
        ("render", "resolution", "0x1080"),
        ("render", "resolution", "1920x-1"),
        ("shot_version", "focus_point", "[1.5,0]"),
    ]:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.exec_driver_sql(f'UPDATE "{table}" SET "{column}"=?', (value,))
    engine.dispose()


def test_schema_referenced_lyrics_cannot_move_song(database):
    from app.db import create_db_engine

    song_id = populate_project(database)
    other_id, _ = song_rows(database)
    engine = create_db_engine(database)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE lyrics_version SET song_id=? WHERE song_id=?", (other_id, song_id)
        )
    engine.dispose()


def test_fts_rebuild_uses_current_selection(database):
    from app import db

    song_id = populate_project(database)
    engine = db.create_db_engine(database)
    with engine.begin() as connection:
        connection.exec_driver_sql("DELETE FROM song_fts")
        connection.exec_driver_sql(
            "INSERT INTO song_fts(song_id,title,style_prompt,lyrics) VALUES(?,?,?,?)",
            (song_id, "Obsoleta", "", "retirada"),
        )
    if hasattr(db, "rebuild_fts"):
        db.rebuild_fts(engine)
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT song_id FROM song_fts WHERE song_fts MATCH 'luciernagas'"
        ).fetchall() == [(song_id,)]
        assert (
            connection.exec_driver_sql(
                "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'retirada'"
            ).scalar_one()
            == 0
        )
    engine.dispose()


def test_snapshot_rejects_wrong_root_before_restore(database):
    from app.db import create_db_engine
    from app.snapshots import project, validate

    song_id = populate_project(database)
    engine = create_db_engine(database)
    document = project(engine, song_id)
    child = next(
        row for row in document["rows"]["take"] if row["derivation"] == "extend"
    )
    child["root_id"] = child["id"]
    with pytest.raises(ValueError, match="root"):
        validate(document, database.parent / "data")
    engine.dispose()


def test_backup_real_restore_to_new_database(database):
    import app.backup as module
    from app.db import create_db_engine

    song_id = populate_project(database)
    copy = module.backup(database, database.parent / "backups")
    target = database.parent / "restored-backup.sqlite"
    assert hasattr(module, "restore_backup"), "Falta restauración explícita del backup"
    module.restore_backup(copy, target)
    engine = create_db_engine(target)
    with engine.begin() as connection:
        assert connection.exec_driver_sql(
            "SELECT song_id FROM song_fts WHERE song_fts MATCH 'luciernagas'"
        ).fetchall() == [(song_id,)]
        assert (
            connection.exec_driver_sql("SELECT count(*) FROM lineage_edge").scalar_one()
            == 1
        )
        connection.exec_driver_sql(
            "UPDATE song SET title='Restaurada' WHERE id=?", (song_id,)
        )
        assert connection.exec_driver_sql(
            "SELECT song_id FROM song_fts WHERE song_fts MATCH 'Restaurada'"
        ).fetchall() == [(song_id,)]
    with pytest.raises(FileExistsError):
        module.restore_backup(copy, target)
    engine.dispose()


def test_fts_lyrics_switch_update_delete_and_restore(database):
    from app.db import create_db_engine
    from app.models import LyricsVersion, Song
    from sqlalchemy.orm import Session

    song_id, owner = song_rows(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        old = LyricsVersion(
            owner_id=owner,
            song_id=song_id,
            text="retirada",
            source="manual",
            declaration="own",
            sha256="a" * 64,
        )
        current = LyricsVersion(
            owner_id=owner,
            song_id=song_id,
            text="vigente",
            source="manual",
            declaration="own",
            sha256="b" * 64,
        )
        session.add_all([old, current])
        session.flush()
        session.get(Song, song_id).current_lyrics_version_id = old.id
        session.commit()
        session.get(Song, song_id).current_lyrics_version_id = current.id
        session.commit()
        current.text = "actualizada"
        session.commit()
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'retirada OR vigente'"
                ).scalar_one()
                == 0
            )
            assert (
                connection.exec_driver_sql(
                    "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'actualizada'"
                ).scalar_one()
                == 1
            )
        current.deleted_at = "2026-10-07T00:00:00Z"
        session.commit()
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'actualizada'"
                ).scalar_one()
                == 0
            )
        current.deleted_at = None
        session.commit()
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'actualizada'"
                ).scalar_one()
                == 1
            )
    engine.dispose()


def test_snapshot_failure_keeps_committed_database_and_reconciles(
    database, monkeypatch
):
    import json
    import os

    from app.db import create_db_engine
    from app.models import Song, User
    from app.snapshots import reconcile
    from sqlalchemy.orm import Session

    root = database.parent / "data"
    engine = create_db_engine(database, data_dir=root)
    with Session(engine) as session:
        song = Song(
            owner_id=session.query(User).one().id, title="Antes", style_prompt=""
        )
        session.add(song)
        session.commit()
        identifier = song.id
        target = root / "songs" / identifier / "song.json"
        replace = os.replace

        def fail(*args):
            raise OSError("synthetic snapshot failure")

        monkeypatch.setattr(os, "replace", fail)
        song.title = "Confirmada"
        session.commit()
        assert (
            json.loads(target.read_text(encoding="utf-8"))["rows"]["song"][0]["title"]
            == "Antes"
        )
        session.expire_all()
        assert session.get(Song, identifier).title == "Confirmada"
        monkeypatch.setattr(os, "replace", replace)
        reconcile(engine, root)
        assert (
            json.loads(target.read_text(encoding="utf-8"))["rows"]["song"][0]["title"]
            == "Confirmada"
        )
    engine.dispose()
