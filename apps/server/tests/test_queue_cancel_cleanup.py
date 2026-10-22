"""T-04 CA-3: cancelar borra data/tmp/<attempt> cuando nadie más lo necesita."""
# ruff: noqa: F811, RUF059  (los fixtures se importan de otro test)

import logging
import subprocess
import sys
from pathlib import Path

import pytest
from app import models
from app.queue.cleanup import sweep_cancelled
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_dispatcher_recovery import engine, prepared, settings  # noqa: F401


def _tmp(*parts):
    path = settings().data_dir.joinpath("tmp", *parts)
    path.mkdir(parents=True, exist_ok=True)
    (path / "raw.wav").write_bytes(b"raw")
    return path


def _status(engine, jid, status):
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE job SET status=:s, finished_at='2026-10-22T00:00:00Z', updated_at=:u WHERE id=:i"
            ),
            {"s": status, "i": jid, "u": models.utc_now()},
        )


def test_cancelled_engine_job_loses_its_attempt_tmp(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _status(engine, jid, "cancelled")
    assert sweep_cancelled(engine, owner, settings().data_dir) == 1
    assert not raw.exists()
    # idempotente
    assert sweep_cancelled(engine, owner, settings().data_dir) == 0


def test_running_engine_job_keeps_its_tmp(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    assert sweep_cancelled(engine, owner, settings().data_dir) == 0
    assert raw.exists()


def _dependent(engine, jid, owner, status, *, reads=False):
    request = {"inputs": []}
    if reads:
        request = {
            "inputs": [
                {"role": "source", "ref": {"type": "job", "id": jid}, "output_index": 0}
            ]
        }
    post = models.new_id()
    with Session(engine) as session, session.begin():
        song = session.get(models.Job, jid).song_id
        session.add(
            models.Job(
                id=post,
                owner_id=owner,
                song_id=song,
                task="post.audio",
                lane="cpu",
                status=status,
                attempt=0 if status == "queued" else 1,
                request=request,
            )
        )
        session.flush()
        session.add(
            models.JobDependency(
                id=models.new_id(),
                owner_id=owner,
                job_id=post,
                depends_on_job_id=jid,
            )
        )
    return post


def test_tmp_needed_by_another_live_job_is_kept(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _dependent(engine, jid, owner, "queued")
    _status(engine, jid, "cancelled")
    assert sweep_cancelled(engine, owner, settings().data_dir) == 0
    assert raw.exists()


def test_cancelled_post_releases_generation_raw_when_nobody_else_needs_it(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _dependent(engine, jid, owner, "cancelled", reads=True)
    assert sweep_cancelled(engine, owner, settings().data_dir) == 1
    assert not raw.exists()


def test_cancelled_post_keeps_generation_raw_if_a_sibling_post_is_live(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _dependent(engine, jid, owner, "cancelled", reads=True)
    _dependent(engine, jid, owner, "queued")
    assert sweep_cancelled(engine, owner, settings().data_dir) == 0
    assert raw.exists()


def _junction(link, target):
    if sys.platform != "win32":
        pytest.skip("las junctions son de Windows")
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
        capture_output=True,
    )


def test_cleanup_never_follows_a_junction(engine, caplog):
    import os

    jid, owner, claim = prepared(engine)
    outside = Path(settings().data_dir).parent / f"outside-{claim.attempt_id}"
    outside.mkdir()
    (outside / "keep.bin").write_bytes(b"external")
    tmp = settings().data_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    link = tmp / claim.attempt_id
    _junction(link, outside)
    _status(engine, jid, "cancelled")
    try:
        with caplog.at_level(logging.INFO):
            assert sweep_cancelled(engine, owner, settings().data_dir) == 0
        assert (outside / "keep.bin").read_bytes() == b"external"
        assert "worker.cleanup.failed" in caplog.text
    finally:
        os.rmdir(link)


def test_cleanup_error_is_an_event_not_an_abort(engine, monkeypatch, caplog):
    import shutil

    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _status(engine, jid, "cancelled")

    def boom(path, *args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(shutil, "rmtree", boom)
    with caplog.at_level(logging.INFO):
        assert sweep_cancelled(engine, owner, settings().data_dir) == 0
    assert raw.exists()
    assert "worker.cleanup.failed" in caplog.text
    assert "boom" not in caplog.text


def test_runtime_sweeps_cancelled_jobs_at_start_and_while_running(engine):
    import asyncio

    from app.queue.runtime import QueueRuntime
    from test_dispatcher_recovery import RecordedBackend

    first, owner, claim_first = prepared(engine)
    raw_first = _tmp(claim_first.attempt_id)
    _status(engine, first, "cancelled")
    backend = RecordedBackend()

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        runtime.sweep_s = 0.05
        await runtime.start()
        try:
            await asyncio.sleep(0.4)
            assert not raw_first.exists()  # barrido de arranque, hecho por el bucle
            second, _, claim_second = await asyncio.to_thread(prepared, engine)
            raw_second = _tmp(claim_second.attempt_id)
            _status(engine, second, "cancelled")
            await asyncio.sleep(0.6)
            assert not raw_second.exists()  # barrido periódico del bucle
        finally:
            await runtime.close()

    asyncio.run(run())
