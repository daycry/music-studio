"""T-17: ningún job terminal deja temporales en ``data/tmp`` que nadie necesite."""
# ruff: noqa: F401, F811, RUF059

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import models
from app.queue.cleanup import TerminalSweeper
from app.queue.events import EventBus, EventConsumer
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_dispatcher_recovery import engine, prepared, settings


def _tmp(*parts):
    path = settings().data_dir.joinpath("tmp", *parts)
    path.mkdir(parents=True, exist_ok=True)
    (path / "raw.wav").write_bytes(b"raw")
    return path


def _sweep(engine, owner, **kwargs):
    sweeper = TerminalSweeper(engine, owner, settings().data_dir, **kwargs)
    sweeper.MARGIN_S = 0
    sweeper.run(force=True)
    return sweeper


def _finish(engine, owner, claim, kind, *, retryable=False):
    """Lleva el attempt a terminal por la vía real del consumidor de eventos."""
    consumer = EventConsumer(engine, owner, EventBus())
    if kind == "done":
        event = {
            "job_id": claim.attempt_id,
            "seq": 1,
            "ts": models.utc_now(),
            "type": "done",
            "data": {
                "artifacts": [],
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        }
    else:
        event = {
            "job_id": claim.attempt_id,
            "seq": 1,
            "ts": models.utc_now(),
            "type": "error",
            "data": {"code": "INTERNAL", "message": "x", "retryable": retryable},
        }
    consumer.accept(claim.attempt_id, "mock", event)


# --- CA-1 ---------------------------------------------------------------------


def test_ca1_succeeded_job_loses_its_attempt_tmp(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "done")
    _sweep(engine, owner)
    assert not raw.exists()


def test_ca1_every_attempt_of_a_terminal_job_is_removed(engine):
    from test_job_attempt_schema import insert_raw, request, row

    jid, owner, claim = prepared(engine)
    raw_first = _tmp(claim.attempt_id)
    second = models.new_id()
    value = dict(
        row(),
        id=second,
        job_id=jid,
        owner_id=owner,
        ordinal=2,
        engine_request=dict(request(), job_id=second, output_dir=f"tmp/{second}"),
    )
    insert_raw(engine, value)
    raw_second = _tmp(second)
    _finish(engine, owner, claim, "done")
    _sweep(engine, owner)
    # el attempt 1 queda abandonado respecto al 2 (CA-2) y también se borra
    assert not raw_first.exists() and not raw_second.exists()


def test_ca1_nonretryable_failed_job_is_cleaned(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "error", retryable=False)
    _sweep(engine, owner)
    assert not raw.exists()


def test_ca1_failed_job_that_can_still_be_retried_keeps_its_tmp(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "error", retryable=True)
    _sweep(engine, owner)
    assert raw.exists()


def test_ca1_retryable_failed_job_without_attempts_left_is_cleaned(engine):
    jid, owner, claim = prepared(engine)
    with Session(engine) as session, session.begin():
        session.get(models.Job, jid).max_attempts = 1
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "error", retryable=True)
    _sweep(engine, owner)
    assert not raw.exists()


def test_ca1_running_job_keeps_everything(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _sweep(engine, owner)
    assert raw.exists()


def _bare_job(engine, staged_name):
    """Job running con un único attempt cuya petición apunta a una entrada staged."""
    from test_dispatcher_admission import add
    from test_job_attempt_schema import insert_raw, request, row

    jid, owner = add(
        engine, status="running", engine_id="mock", model_id="mock", attempt=1
    )
    aid = models.new_id()
    wire = dict(request()["inputs"][0], path=f"tmp/_server_inputs/{staged_name}/0")
    insert_raw(
        engine,
        dict(
            row(),
            id=aid,
            job_id=jid,
            owner_id=owner,
            engine_request=dict(
                request(), job_id=aid, output_dir=f"tmp/{aid}", inputs=[wire]
            ),
        ),
    )
    return jid, owner, SimpleNamespace(attempt_id=aid)


def test_ca1_staged_engine_inputs_of_a_terminal_job_are_removed(engine):
    jid, owner, claim = _bare_job(engine, "ab" * 16)
    staged = _tmp("_server_inputs", "ab" * 16)
    unattributed = _tmp("_server_inputs", "cd" * 16)
    _finish(engine, owner, claim, "done")
    _sweep(engine, owner)
    assert not staged.exists()
    assert unattributed.exists()  # no se puede atribuir a ningún job: no se toca


def test_ca1_staged_inputs_of_a_live_job_and_of_a_retryable_failure_are_kept(engine):
    jid, owner, claim = _bare_job(engine, "ef" * 16)
    staged = _tmp("_server_inputs", "ef" * 16)
    _sweep(engine, owner)
    assert staged.exists()  # job vivo
    _finish(engine, owner, claim, "error", retryable=True)
    _sweep(engine, owner)
    assert staged.exists()  # el reintento reutiliza las entradas congeladas


def test_ca1_terminal_post_loses_its_exec_dirs(tmp_path):
    from test_worker_publication_invariants import EXECUTION, OWNER, POST
    from test_worker_startup_staging import _interrupted_world

    engine, _ = _interrupted_world(tmp_path)
    root = Path(tmp_path) / "data" / "tmp"
    dirs = [root / "_server_inputs" / EXECUTION, root / "_server_cpu" / EXECUTION]
    for folder in dirs:
        folder.mkdir(parents=True)
        (folder / "x").write_bytes(b"x")
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE job SET status='succeeded', finished_at=? WHERE id=?",
                (models.utc_now(), POST),
            )
        TerminalSweeper(engine, OWNER, Path(tmp_path) / "data").run(force=True)
        assert not any(folder.exists() for folder in dirs)
    finally:
        engine.dispose()


def test_ca4_generation_needed_by_a_pending_beats_job_is_kept(engine):
    from test_queue_cancel_cleanup import _dependent

    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    beats = _dependent(engine, jid, owner, "queued")
    _finish(engine, owner, claim, "done")
    sweeper = _sweep(engine, owner)
    assert raw.exists() and jid in sweeper.deferred
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE job SET status='succeeded', updated_at=:u WHERE id=:i"),
            {"i": beats, "u": models.utc_now()},
        )
    sweeper.run()  # lo aplazado se reintenta sin releer el histórico
    assert not raw.exists()


# --- CA-3: permanentes vs transitorios -----------------------------------------


def _junction(link, target):
    if sys.platform != "win32":
        pytest.skip("las junctions son de Windows")
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
        capture_output=True,
    )


def test_ca3_permanent_failure_is_logged_once_and_not_retried(engine, caplog):
    jid, owner, claim = prepared(engine)
    outside = Path(settings().data_dir).parent / f"out-{claim.attempt_id}"
    outside.mkdir()
    (outside / "keep.bin").write_bytes(b"external")
    tmp = settings().data_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    link = tmp / claim.attempt_id
    _junction(link, outside)
    _finish(engine, owner, claim, "done")
    try:
        with caplog.at_level(logging.INFO):
            sweeper = _sweep(engine, owner)
            sweeper.run()
            sweeper.run()
        assert jid not in sweeper.deferred
        assert caplog.text.count("worker.cleanup.failed") == 1
        assert (outside / "keep.bin").read_bytes() == b"external"
    finally:
        os.rmdir(link)


def test_ca3_non_directory_target_is_permanent(engine, caplog):
    jid, owner, claim = prepared(engine)
    target = settings().data_dir / "tmp" / claim.attempt_id
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"i am a file")
    _finish(engine, owner, claim, "done")
    with caplog.at_level(logging.INFO):
        sweeper = _sweep(engine, owner)
        sweeper.run()
    assert jid not in sweeper.deferred
    assert caplog.text.count("worker.cleanup.failed") == 1
    target.unlink()


def test_ca3_transient_failure_is_retried_up_to_a_cap(engine, monkeypatch):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "done")
    calls = []

    def busy(path, *args, **kwargs):
        calls.append(path)
        raise OSError("busy")

    monkeypatch.setattr(shutil, "rmtree", busy)
    sweeper = _sweep(engine, owner)
    for _ in range(20):
        sweeper.run()
    assert len(calls) == sweeper.MAX_RETRIES == 5
    assert jid not in sweeper.deferred
    assert raw.exists()


def test_ca3_transient_failure_recovers_when_it_clears(engine, monkeypatch):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "done")
    real = shutil.rmtree
    state = {"n": 0}

    def flaky(path, *args, **kwargs):
        state["n"] += 1
        if state["n"] < 3:
            raise OSError("busy")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", flaky)
    sweeper = _sweep(engine, owner)
    sweeper.run()
    sweeper.run()
    assert not raw.exists()
    assert jid not in sweeper.deferred
