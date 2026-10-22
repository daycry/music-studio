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
        assert foreign.exists()  # no es de una ejecución conocida: no se toca
        assert (final / "master.flac").read_bytes() == b"published"
    finally:
        engine.dispose()
