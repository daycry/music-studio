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
    sweeper.PARK_S = 0
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


# --- fix1: cómo se detecta qué barrer ----------------------------------------


def test_fix1_permanent_failure_is_logged_once_per_process_with_production_values(
    engine, caplog
):
    jid, owner, claim = prepared(engine)
    target = settings().data_dir / "tmp" / claim.attempt_id
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"file")
    _finish(engine, owner, claim, "done")
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)  # sin tocar nada
    try:
        with caplog.at_level(logging.INFO):
            for _ in range(5):
                sweeper.run()
        assert caplog.text.count("worker.cleanup.failed") == 1
        assert jid not in sweeper.deferred
    finally:
        target.unlink()


def test_fix1_terminal_with_engine_clock_behind_is_swept(engine):
    from datetime import datetime, timedelta, timezone

    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.run()  # el job sigue running
    behind = (
        (datetime.now(timezone.utc) - timedelta(seconds=30))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
    EventConsumer(engine, owner, EventBus()).accept(
        claim.attempt_id,
        "mock",
        {
            "job_id": claim.attempt_id,
            "seq": 1,
            "ts": behind,  # reloj del engine atrasado: job.updated_at queda en el pasado
            "type": "done",
            "data": {
                "artifacts": [],
                "telemetry": {"mode": "bf16", "model_revision": "s"},
            },
        },
    )
    for _ in range(3):
        sweeper.run()
    assert not raw.exists()


def test_fix1_steady_state_does_not_rescan_resolved_jobs(engine):
    jid, owner, claim = prepared(engine)
    _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "done")
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.run()
    assert sweeper.last_scanned == 1
    statements = []
    from sqlalchemy import event as sa_event

    sa_event.listen(
        engine, "before_cursor_execute", lambda *a: statements.append(a[2]), named=False
    )
    sweeper.run()
    assert sweeper.last_scanned == 0
    assert len(statements) <= 2  # solo la consulta de ids


def test_fix1_budget_spreads_a_large_backlog_over_several_passes(engine):
    owner = None
    raws = []
    for _ in range(5):
        jid, owner, claim = prepared(engine)
        raws.append(_tmp(claim.attempt_id))
        _finish(engine, owner, claim, "done")
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.BUDGET = 2
    sweeper.run()
    assert sweeper.last_scanned == 2 and sweeper.pending == 3
    sweeper.run()
    sweeper.run()
    assert sweeper.pending == 0
    assert not any(raw.exists() for raw in raws)


def test_fix1_sweep_reads_only_the_columns_it_needs(engine):
    from sqlalchemy import event as sa_event

    jid, owner, claim = prepared(engine)
    _finish(engine, owner, claim, "error", retryable=True)
    statements = []
    sa_event.listen(engine, "before_cursor_execute", lambda *a: statements.append(a[2]))
    TerminalSweeper(engine, owner, settings().data_dir).run()
    text_ = "\n".join(statements)
    assert "job_attempt.provenance" not in text_
    assert "job_attempt.load_options" not in text_


def test_fix1_runtime_start_does_not_wait_for_the_sweep(engine, monkeypatch):
    import asyncio
    import time

    from app.queue import cleanup
    from app.queue.runtime import QueueRuntime
    from test_dispatcher_recovery import RecordedBackend

    calls = []

    def slow(self, force=False):
        calls.append(time.monotonic())
        time.sleep(1.0)
        return 0

    monkeypatch.setattr(cleanup.TerminalSweeper, "run", slow)
    backend = RecordedBackend()

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        began = time.monotonic()
        await runtime.start()
        try:
            assert time.monotonic() - began < 0.9
            assert calls == []  # el barrido inicial lo hace el bucle, no start()
        finally:
            await runtime.close()

    asyncio.run(run())


# --- CA-4 (gap 3): regresiones con jobs reales --------------------------------


def test_fix1_generation_with_a_real_pending_beats_job_keeps_its_tmp(engine):
    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    song = Session(engine).get(models.Job, jid).song_id
    beats = models.new_id()
    with Session(engine) as session, session.begin():
        session.add(
            models.Job(
                id=beats,
                owner_id=owner,
                song_id=song,
                task="audio.beats",
                lane="cpu",
                status="blocked",
                request={"params": {}, "inputs": []},
            )
        )
        session.flush()
        session.add(
            models.JobDependency(
                id=models.new_id(), owner_id=owner, job_id=beats, depends_on_job_id=jid
            )
        )
    _finish(engine, owner, claim, "done")
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.PARK_S = 0
    sweeper.run()
    assert raw.exists()
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE job SET status='succeeded', finished_at=:f WHERE id=:i"),
            {"i": beats, "f": models.utc_now()},
        )
    sweeper.run()
    assert not raw.exists()


def test_fix1_manual_retry_still_works_after_the_sweep(engine):
    import asyncio

    from app.models import Job, Take
    from app.queue.manual_retry import ManualRetry
    from test_queue_chains import create, services
    from test_queue_manual_retry import own_post_failure
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    own_post_failure(engine, chain)
    raw = _tmp(claim.attempt_id)
    data_dir = settings().data_dir
    TerminalSweeper(engine, owner, data_dir).run()
    assert not raw.exists()  # post fallido: nadie vivo necesita el WAV crudo
    new = asyncio.run(
        ManualRetry(engine, owner, resolver).retry(chain.generation_job_id)
    )
    assert new is not None
    with Session(engine) as s:
        assert s.get(Job, new.generation_job_id).status == "queued"
        assert s.get(Take, chain.take_ids[2]).job_id == new.generation_job_id


# --- fix2 ------------------------------------------------------------------------


def test_fix2_parked_jobs_do_not_starve_old_history_nor_keep_the_fast_cadence(engine):
    raws = []
    for _ in range(3):  # histórico viejo: se puede limpiar
        jid, owner, claim = prepared(engine)
        raws.append(_tmp(claim.attempt_id))
        _finish(engine, owner, claim, "done")
    for _ in range(5):  # más nuevos, con reintento pendiente: nunca se resuelven
        jid, owner, claim = prepared(engine)
        raws.append(_tmp(claim.attempt_id))
        _finish(engine, owner, claim, "error", retryable=True)
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.BUDGET = 2
    passes = 0
    while sweeper.pending or passes == 0:
        sweeper.run()
        passes += 1
        assert passes <= 6  # (3 + 5) / 2 + margen: el presupuesto avanza siempre
    assert not any(raw.exists() for raw in raws[:3])  # los viejos sí se barrieron
    assert all(raw.exists() for raw in raws[3:])  # lo pendiente de reintento, no
    assert sweeper.pending == 0  # cadencia lenta: solo hay aparcados
    sweeper.run()
    assert sweeper.last_scanned == 0  # los aparcados esperan su turno


def test_fix2_parked_jobs_are_reevaluated_after_their_own_backoff(engine):
    import time

    jid, owner, claim = prepared(engine)
    raw = _tmp(claim.attempt_id)
    _finish(engine, owner, claim, "error", retryable=True)
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.PARK_S = 0.2
    sweeper.run()
    assert raw.exists() and jid in sweeper.parked
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE job SET max_attempts=1, attempt=1 WHERE id=:i"), {"i": jid}
        )
    sweeper.run()
    assert raw.exists()  # aún en espera
    time.sleep(0.3)
    sweeper.run()
    assert not raw.exists() and jid not in sweeper.parked


def test_fix2_runtime_fast_cadence_only_while_new_history_remains():
    import asyncio
    import time

    from app.queue.runtime import QueueRuntime

    async def run(pending):
        runtime = object.__new__(QueueRuntime)
        runtime.owner_id, runtime.settings = "o", SimpleNamespace(data_dir=Path("."))
        runtime.engine, runtime.sweep_s, runtime._sweep_at = None, 2.0, 0.0
        runtime._sweeper = SimpleNamespace(run=lambda force=False: 0, pending=pending)

        async def dbcall(function, *args):
            return function(*args)

        runtime.dbcall = dbcall
        await runtime._sweep_cancelled()
        return runtime._sweep_at

    assert asyncio.run(run(7)) == 0.0  # queda histórico: siguiente trozo ya
    assert asyncio.run(run(0)) > time.monotonic() + 1  # solo aparcados: 2 s


def _bare(engine, **overrides):
    from test_dispatcher_admission import add
    from test_job_attempt_schema import insert_raw, request, row

    lane = overrides.pop("lane", "gpu")
    mode = overrides.pop("mode", "bf16")
    jid, owner = add(
        engine,
        status="running",
        engine_id="mock",
        model_id="mock",
        attempt=1,
        lane=lane,
    )
    aid = models.new_id()
    insert_raw(
        engine,
        dict(
            row(),
            id=aid,
            job_id=jid,
            owner_id=owner,
            mode=mode,
            load_options={"model_id": "mock", "mode": mode},
            engine_request=dict(
                request(), job_id=aid, output_dir=f"tmp/{aid}", mode=mode
            ),
        ),
    )
    return jid, owner, SimpleNamespace(attempt_id=aid)


def _error(engine, owner, claim, code):
    EventConsumer(engine, owner, EventBus()).accept(
        claim.attempt_id,
        "mock",
        {
            "job_id": claim.attempt_id,
            "seq": 1,
            "ts": models.utc_now(),
            "type": "error",
            "data": {"code": code, "message": "x", "retryable": True},
        },
    )


def test_fix2_vram_exceeded_in_offload_will_never_be_retried_so_it_is_cleaned(engine):
    jid, owner, claim = _bare(engine, mode="offload")
    raw = _tmp(claim.attempt_id)
    _error(engine, owner, claim, "VRAM_EXCEEDED")
    TerminalSweeper(engine, owner, settings().data_dir).run()
    assert not raw.exists()


def test_fix2_vram_exceeded_in_bf16_can_still_retry_in_offload_so_it_is_kept(engine):
    jid, owner, claim = _bare(engine, mode="bf16")
    raw = _tmp(claim.attempt_id)
    _error(engine, owner, claim, "VRAM_EXCEEDED")
    TerminalSweeper(engine, owner, settings().data_dir).run()
    assert raw.exists()


def test_fix2_real_chain_generation_raw_goes_when_the_post_ends_beats_wait(engine):
    from test_queue_chains import create, services
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    raw = resolver.data_dir / "tmp" / claim.attempt_id
    assert raw.exists()
    sweeper = TerminalSweeper(engine, owner, resolver.data_dir)
    sweeper.PARK_S = 0
    sweeper.run()
    assert raw.exists()  # el post (vivo) lo necesita
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE job SET status='succeeded', finished_at=:f WHERE id=:i"),
            {"i": chain.post_job_id, "f": models.utc_now()},
        )
    sweeper.run()
    # beats lee el asset publicado en songs/, no el WAV crudo: la generación se limpia,
    assert not raw.exists()
    # pero el post sigue aplazado mientras sus beats (que dependen de él) esperan
    assert chain.post_job_id in sweeper.deferred
    with engine.begin() as connection:
        for beat in chain.beat_job_ids:
            connection.execute(
                text("UPDATE job SET status='succeeded', finished_at=:f WHERE id=:i"),
                {"i": beat, "f": models.utc_now()},
            )
    sweeper.run()
    assert chain.post_job_id not in sweeper.deferred


def test_fix2_sweep_cancelled_does_not_relog_a_permanent_failure(engine, caplog):
    from app.queue.cleanup import sweep_cancelled

    jid, owner, claim = prepared(engine)
    target = settings().data_dir / "tmp" / claim.attempt_id
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"file")
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE job SET status='cancelled', finished_at=:f WHERE id=:i"),
            {"i": jid, "f": models.utc_now()},
        )
    try:
        with caplog.at_level(logging.INFO):
            for _ in range(4):
                sweep_cancelled(engine, owner, settings().data_dir)
        assert caplog.text.count("worker.cleanup.failed") == 1
    finally:
        target.unlink()


def test_fix2_in_clauses_are_chunked(engine, monkeypatch):
    import sqlite3

    from app.queue import cleanup
    from sqlalchemy import event as sa_event
    from test_dispatcher_admission import add

    for _ in range(30):
        add(engine, status="cancelled", finished_at="2026-10-22T00:00:00Z")
    owner = Session(engine).scalar(text("SELECT id FROM user LIMIT 1"))
    monkeypatch.setattr(cleanup, "IN_CHUNK", 8, raising=False)

    @sa_event.listens_for(engine, "connect")
    def limit(dbapi_connection, record):
        dbapi_connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 12)

    engine.dispose()  # fuerza conexiones nuevas con el límite
    cleanup.sweep_cancelled(engine, owner, settings().data_dir)
    sweeper = TerminalSweeper(engine, owner, settings().data_dir)
    sweeper.run()


def test_fix2_a_failing_sweep_does_not_skip_stage_removal(tmp_path, monkeypatch):
    from app.worker import execution as execution_module
    from test_worker_publication_invariants import POST
    from test_worker_resume import _request_cancel, _reserved_world, _tmp_dirs

    engine, service = _reserved_world(tmp_path)
    dirs = _tmp_dirs(tmp_path)
    _request_cancel(engine)

    def boom(*args, **kwargs):
        raise OSError("barrido roto")

    monkeypatch.setattr(execution_module, "sweep_cancelled", boom)
    try:
        assert service.cancel_job(POST) is True
        assert not dirs["stage"].exists()
    finally:
        engine.dispose()
