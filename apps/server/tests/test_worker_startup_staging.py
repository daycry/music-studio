"""Arranque: limpia los staging huérfanos de ejecuciones no confirmadas (ADR-0089 §2)."""

from pathlib import Path

from app import models
from app.db import create_db_engine, migrate
from app.publication import PublicationCoordinator
from app.worker.execution import CpuAudioService
from sqlalchemy.orm import Session


def _interrupted_world(tmp_path):
    from test_worker_publication_invariants import (
        JOB,
        POST,
        SONG,
        TAKE,
        attach_provenance,
        common,
        execution,
        insert_raw,
        post_request,
        row,
        terminal,
    )

    database = Path(tmp_path) / "data" / "studio.sqlite"
    database.parent.mkdir(parents=True)
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(models.Song(**common(SONG), title="reconcile"))
        session.flush()
        session.add(
            models.Job(
                **common(JOB),
                song_id=SONG,
                task="music.instrumental",
                lane="gpu",
                status="succeeded",
                attempt=1,
                request={"seed": 17},
            )
        )
        session.add(
            models.Job(
                **common(POST),
                song_id=SONG,
                task="post.audio",
                lane="cpu",
                status="running",
                attempt=1,
                request=post_request(),
            )
        )
        session.add(
            models.JobDependency(
                **common("01K70000000000000000000009"),
                job_id=POST,
                depends_on_job_id=JOB,
            )
        )
        session.add(
            models.Take(
                **common(TAKE),
                song_id=SONG,
                job_id=JOB,
                status="queued",
                batch_id=JOB,
                variant_index=0,
                root_id=TAKE,
                derivation="original",
                task="music.instrumental",
                model_id="mock",
                model_version="1.5",
                seed=17,
                commercial_use=True,
            )
        )
        attempt = row()
        attempt.update(status="succeeded", last_seq=1, terminal=terminal())
        session.add(models.JobAttempt(**attempt))
        session.commit()
    attach_provenance(engine)
    insert_raw(engine, "cpu_execution", execution())

    return engine, database


def test_startup_removes_orphan_pending_staging(tmp_path):
    from test_worker_publication_invariants import EXECUTION, SONG, TAKE, common

    engine, _ = _interrupted_world(tmp_path)
    takes = Path(tmp_path) / "data" / "songs" / SONG / "takes"
    pending = takes / f".pending-{EXECUTION}" / TAKE
    pending.mkdir(parents=True)
    (pending / "master.flac").write_bytes(b"half written")
    foreign = takes / ".pending-01K7ZZZZZZZZZZZZZZZZZZZZZZ"
    foreign.mkdir()
    final = takes / TAKE
    final.mkdir()
    (final / "master.flac").write_bytes(b"published")
    service = CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=tmp_path / "ffmpeg",
        owner_id=common(SONG)["owner_id"],
    )
    try:
        assert service.reconcile_startup() == 1
        assert not (takes / f".pending-{EXECUTION}").exists()
        assert not foreign.exists()  # sin fila cpu_execution: huérfano (ADR-0089 §2)
        assert (final / "master.flac").read_bytes() == b"published"
    finally:
        engine.dispose()


# --- fix1: la fila SQLite manda; no se destruye lo único que permite recuperar ---

OTHER_EXEC = "01K7YYYYYYYYYYYYYYYYYYYYYY"
ORPHAN_TAKE = "01K7XXXXXXXXXXXXXXXXXXXXXX"


def _service(engine, tmp_path):
    from test_worker_publication_invariants import SONG, common

    return CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=tmp_path / "ffmpeg",
        owner_id=common(SONG)["owner_id"],
    )


def _takes_dir(tmp_path):
    from test_worker_publication_invariants import SONG

    path = Path(tmp_path) / "data" / "songs" / SONG / "takes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _make_prepared_intent(engine):
    import json

    from app.migrations.cpu_publication_invariants import cas
    from test_worker_publication_invariants import (
        INTENT,
        REVISION,
        canonical_sha256,
        content,
        insert_raw,
        intent,
        package,
    )

    insert_raw(engine, "publication_intent", intent())
    insert_raw(engine, "publication_intent_revision", content())
    with engine.begin() as connection:
        cas(
            connection,
            "publication_intent",
            INTENT,
            1,
            "reserved",
            active_revision_id=REVISION,
        )
    value = package()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package=?,package_sha256=? WHERE id=?",
            (json.dumps(value), canonical_sha256(value), REVISION),
        )
        cas(connection, "publication_intent", INTENT, 2, "prepared")


def test_startup_keeps_staging_with_prepared_intent(tmp_path):
    from test_worker_publication_invariants import EXECUTION, TAKE

    engine, _ = _interrupted_world(tmp_path)
    _make_prepared_intent(engine)
    pending = _takes_dir(tmp_path) / f".pending-{EXECUTION}" / TAKE
    pending.mkdir(parents=True)
    (pending / "master.flac").write_bytes(b"only copy")
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert (pending / "master.flac").read_bytes() == b"only copy"
    finally:
        engine.dispose()


def test_startup_removes_pending_without_execution_row(tmp_path):
    engine, _ = _interrupted_world(tmp_path)
    orphan = _takes_dir(tmp_path) / f".pending-{OTHER_EXEC}" / "x"
    orphan.mkdir(parents=True)
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert not orphan.parent.exists()
    finally:
        engine.dispose()


def test_startup_removes_pending_of_terminal_execution(tmp_path):
    from test_worker_publication_invariants import EXECUTION

    engine, _ = _interrupted_world(tmp_path)
    from app.migrations.cpu_publication_invariants import cas

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job SET status='failed',finished_at='2026-10-22T00:00:00Z' WHERE id IN (SELECT job_id FROM cpu_execution)"
        )
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            1,
            "failed",
            error_code="AUDIO_INVALID",
            finished_at="2026-10-22T00:00:00Z",
            cleanup_state="confirmed",
        )
    stale = _takes_dir(tmp_path) / f".pending-{EXECUTION}" / "x"
    stale.mkdir(parents=True)
    try:
        assert _service(engine, tmp_path).reconcile_startup() == 0
        assert not stale.parent.exists()
    finally:
        engine.dispose()


def test_startup_moves_final_dir_without_take_row_to_trash(tmp_path):
    engine, _ = _interrupted_world(tmp_path)
    final = _takes_dir(tmp_path) / ORPHAN_TAKE
    final.mkdir()
    (final / "master.flac").write_bytes(b"maybe a take")
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert not final.exists()
        moved = list((Path(tmp_path) / "data/trash/orphans").glob(f"{ORPHAN_TAKE}-*"))
        assert len(moved) == 1
        assert (moved[0] / "master.flac").read_bytes() == b"maybe a take"
    finally:
        engine.dispose()


def test_startup_never_touches_take_with_row(tmp_path):
    from test_worker_publication_invariants import TAKE

    engine, _ = _interrupted_world(tmp_path)
    folder = _takes_dir(tmp_path) / TAKE
    folder.mkdir()
    (folder / "master.flac").write_bytes(b"kept")
    try:
        for status in ("queued", "ready"):
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    "UPDATE take SET status=? WHERE id=?", (status, TAKE)
                )
            _service(engine, tmp_path).reconcile_startup()
            assert (folder / "master.flac").read_bytes() == b"kept"
    finally:
        engine.dispose()


def test_startup_skips_execution_alive_in_this_process(tmp_path):
    from test_worker_publication_invariants import EXECUTION

    engine, _ = _interrupted_world(tmp_path)
    live = _takes_dir(tmp_path) / f".pending-{EXECUTION}" / "x"
    live.mkdir(parents=True)
    service = _service(engine, tmp_path)
    service.owners[EXECUTION] = object()
    try:
        service.reconcile_startup()
        assert live.exists()
    finally:
        engine.dispose()


def test_startup_cleanup_error_does_not_abort(tmp_path, monkeypatch, caplog):
    import shutil

    from test_worker_publication_invariants import EXECUTION

    engine, _ = _interrupted_world(tmp_path)
    broken = _takes_dir(tmp_path) / f".pending-{EXECUTION}"
    broken.mkdir()
    other = _takes_dir(tmp_path) / f".pending-{OTHER_EXEC}"
    other.mkdir()

    real = shutil.rmtree

    def flaky(path, *args, **kwargs):
        if Path(path).name == broken.name:
            raise OSError("boom")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", flaky)
    try:
        assert _service(engine, tmp_path).reconcile_startup() == 1
        assert broken.exists() and not other.exists()
        assert "worker.cleanup.failed" in caplog.text
        assert "boom" not in caplog.text
    finally:
        engine.dispose()


# --- fix2: junctions (CWE-59) y logs al fichero del server ---


def _junction(link, target):
    import subprocess
    import sys

    import pytest

    if sys.platform != "win32":
        pytest.skip("las junctions son de Windows")
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
        capture_output=True,
    )


def _unlink_junction(link):
    import os

    os.rmdir(link)  # quita la junction sin tocar el destino


def test_startup_does_not_follow_junction_takes(tmp_path):
    from test_worker_publication_invariants import SONG

    engine, _ = _interrupted_world(tmp_path)
    outside = Path(tmp_path) / "outside"
    (outside / ORPHAN_TAKE).mkdir(parents=True)
    (outside / ORPHAN_TAKE / "secret").write_bytes(b"external")
    (outside / f".pending-{OTHER_EXEC}").mkdir()
    song = Path(tmp_path) / "data" / "songs" / SONG
    song.mkdir(parents=True, exist_ok=True)
    link = song / "takes"
    _junction(link, outside)
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert (outside / ORPHAN_TAKE / "secret").read_bytes() == b"external"
        assert (outside / f".pending-{OTHER_EXEC}").exists()
        assert not (Path(tmp_path) / "data/trash/orphans").exists()
    finally:
        _unlink_junction(link)
        engine.dispose()


def test_startup_does_not_move_into_junction_trash(tmp_path):
    engine, _ = _interrupted_world(tmp_path)
    outside = Path(tmp_path) / "outside-trash"
    outside.mkdir()
    trash = Path(tmp_path) / "data" / "trash"
    trash.mkdir(parents=True)
    _junction(trash / "orphans", outside)
    final = _takes_dir(tmp_path) / ORPHAN_TAKE
    final.mkdir()
    (final / "master.flac").write_bytes(b"maybe a take")
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert list(outside.iterdir()) == []
        assert (final / "master.flac").read_bytes() == b"maybe a take"
    finally:
        _unlink_junction(trash / "orphans")
        engine.dispose()


def test_startup_does_not_move_into_junction_data_trash(tmp_path):
    engine, _ = _interrupted_world(tmp_path)
    outside = Path(tmp_path) / "outside-data-trash"
    (outside / "orphans").mkdir(parents=True)
    trash = Path(tmp_path) / "data" / "trash"
    _junction(trash, outside)
    final = _takes_dir(tmp_path) / ORPHAN_TAKE
    final.mkdir()
    try:
        _service(engine, tmp_path).reconcile_startup()
        assert list((outside / "orphans").iterdir()) == []
        assert final.exists()
    finally:
        _unlink_junction(trash)
        engine.dispose()


def test_startup_cleanup_events_reach_server_log(tmp_path):
    import re
    from types import SimpleNamespace

    from app.logging import configure_logging
    from test_worker_publication_invariants import SONG, TAKE, common

    engine, _ = _interrupted_world(tmp_path)
    takes = _takes_dir(tmp_path)
    (takes / f".pending-{OTHER_EXEC}").mkdir()
    (takes / ORPHAN_TAKE).mkdir()
    (takes / TAKE).mkdir()  # fila take en `queued`
    logger = configure_logging(SimpleNamespace(data_dir=Path(tmp_path) / "data"))
    service = CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=tmp_path / "ffmpeg",
        owner_id=common(SONG)["owner_id"],
        logger=logger,
    )
    try:
        service.reconcile_startup()
        for handler in logger.handlers:
            handler.flush()
        text = (Path(tmp_path) / "data/logs/server.log").read_text(encoding="utf-8")
        for event in (
            "worker.staging.removed",
            "worker.orphan.quarantined",
            "worker.take.not_ready",
        ):
            assert event in text
        assert "[redacted]" not in text
        assert f'"song_id": "{SONG}"' in text
        assert not re.search(r"[A-Za-z]:|\\|/|\.pending", text)
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        engine.dispose()


# --- fix3/H3: tras publicar no queda `.pending-<exec>` vacío ---


def _plan_for(tmp_path):
    from types import SimpleNamespace

    from test_worker_publication_invariants import SONG

    return SimpleNamespace(song_id=SONG)


def test_empty_stage_removed_after_execution(tmp_path):
    from test_worker_publication_invariants import EXECUTION

    engine, _ = _interrupted_world(tmp_path)
    stage = _takes_dir(tmp_path) / f".pending-{EXECUTION}"
    stage.mkdir()
    try:
        _service(engine, tmp_path)._remove_empty_stage(_plan_for(tmp_path), EXECUTION)
        assert not stage.exists()
    finally:
        engine.dispose()


def test_non_empty_stage_is_left_for_startup_cleanup(tmp_path):
    from test_worker_publication_invariants import EXECUTION, TAKE

    engine, _ = _interrupted_world(tmp_path)
    stage = _takes_dir(tmp_path) / f".pending-{EXECUTION}" / TAKE
    stage.mkdir(parents=True)
    try:
        _service(engine, tmp_path)._remove_empty_stage(_plan_for(tmp_path), EXECUTION)
        assert stage.exists()
    finally:
        engine.dispose()


def test_empty_stage_junction_is_not_followed(tmp_path):
    from test_worker_publication_invariants import EXECUTION, SONG

    engine, _ = _interrupted_world(tmp_path)
    outside = Path(tmp_path) / "outside-empty"
    outside.mkdir()
    song = Path(tmp_path) / "data" / "songs" / SONG
    song.mkdir(parents=True, exist_ok=True)
    link = song / "takes"
    _junction(link, outside)
    (outside / f".pending-{EXECUTION}").mkdir()
    try:
        _service(engine, tmp_path)._remove_empty_stage(_plan_for(tmp_path), EXECUTION)
        assert (outside / f".pending-{EXECUTION}").exists()
    finally:
        _unlink_junction(link)
        engine.dispose()


def test_empty_stage_error_is_an_event_not_an_abort(tmp_path, monkeypatch, caplog):
    from test_worker_publication_invariants import EXECUTION

    engine, _ = _interrupted_world(tmp_path)
    stage = _takes_dir(tmp_path) / f".pending-{EXECUTION}"
    stage.mkdir()

    def boom(self):
        raise OSError("boom")

    monkeypatch.setattr(Path, "rmdir", boom)
    try:
        _service(engine, tmp_path)._remove_empty_stage(_plan_for(tmp_path), EXECUTION)
        assert "worker.cleanup.failed" in caplog.text
        assert "boom" not in caplog.text
    finally:
        engine.dispose()
