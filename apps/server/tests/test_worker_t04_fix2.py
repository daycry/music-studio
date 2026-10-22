"""T-04 fix2: marca ``launching`` recuperable, sondas con backoff y barrido con reintento."""
# ruff: noqa: RUF059

import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import models
from sqlalchemy.orm import Session
from test_worker_resume import (
    DEAD,
    _lane_world,
    _request_cancel,
    _reserved_world,
)
from test_worker_t04_fix1 import _cpu_row, _plan

LAUNCHING = {"launching": True}


def _launch_and_fail(service, engine, tmp_path, monkeypatch, launch):
    """Reanuda y falla al crear el grupo, como hace ``execute_job`` en su except."""
    from app.worker import execution as execution_module
    from test_worker_publication_invariants import EXECUTION, POST

    assert service.claim_resume(POST) == EXECUTION
    monkeypatch.setattr(execution_module, "LinuxGroup", launch)
    service.publisher.receipt_hashes[EXECUTION] = "d" * 64
    service.publisher.prepared_contexts[EXECUTION] = SimpleNamespace(payload=b"{}")
    monkeypatch.setattr(
        service,
        "_prepare",
        lambda plan, execution_id, resume=False: (_cpu_row(engine), Path(tmp_path)),
    )
    with pytest.raises(RuntimeError):
        service.execute(_plan(engine), execution_id=EXECUTION, resume=True)
    assert service.fail_plan(POST, "RuntimeError") is False


def _identity(engine):
    from test_worker_publication_invariants import EXECUTION

    with Session(engine) as session:
        return session.get(models.CpuExecution, EXECUTION).process_identity


# --- N1 (a): fallo en este proceso antes de que exista un hijo ---------------


def test_n1a_launch_failure_without_child_clears_the_marker(tmp_path, monkeypatch):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)

    def launch(*args, **kwargs):
        raise RuntimeError("Popen falló")

    try:
        _launch_and_fail(service, engine, tmp_path, monkeypatch, launch)
        assert _identity(engine) is None  # «nunca lanzado»
        _request_cancel(engine)
        service._backoff.clear()
        assert service.cancel_interrupted(POST) is True
        with Session(engine) as session:
            assert session.get(models.Job, POST).status == "cancelled"
    finally:
        engine.dispose()


def test_n1a_launch_failure_without_child_is_resumable_after_restart(
    tmp_path, monkeypatch
):
    from test_worker_publication_invariants import POST
    from test_worker_startup_staging import _service

    engine, service = _reserved_world(tmp_path)

    def launch(*args, **kwargs):
        raise RuntimeError("Popen falló")

    try:
        _launch_and_fail(service, engine, tmp_path, monkeypatch, launch)
        restarted = _service(engine, tmp_path)
        restarted._birth_probe = lambda pid: None
        restarted._group_probe = lambda leader: False
        restarted.reconcile_startup()
        assert restarted.resumable_jobs() == [POST]
    finally:
        engine.dispose()


def test_n1a_failure_after_popen_keeps_the_marker(tmp_path, monkeypatch):
    """Si pudo llegar a lanzarse algo, no se afirma que no hay proceso."""
    from app.worker import custody_linux

    class Half:  # grupo registrado con su Popen ya hecho
        process = SimpleNamespace(pid=1)

    engine, service = _reserved_world(tmp_path)
    half = Half()

    def launch(*args, **kwargs):
        custody_linux.LINUX_GROUPS.add(half)
        raise RuntimeError("falló tras Popen")

    try:
        try:
            _launch_and_fail(service, engine, tmp_path, monkeypatch, launch)
        finally:
            custody_linux.LINUX_GROUPS.discard(half)
        assert _identity(engine) == LAUNCHING
    finally:
        engine.dispose()


# --- N1 (b): tras un reinicio, prueba sin pid ---------------------------------


def _fake_proc(root, processes):
    """Árbol mínimo de ``/proc``: ``self/stat`` y un ``cmdline`` por proceso."""
    root = Path(root)
    (root / "self").mkdir(parents=True)
    (root / "self" / "stat").write_text("1 (x) S 0 0 0")
    for pid, (state, argv) in processes.items():
        (root / str(pid)).mkdir()
        (root / str(pid) / "stat").write_text(f"{pid} (p) {state} 1 {pid} {pid}")
        (root / str(pid) / "cmdline").write_bytes(b"\0".join(argv) + b"\0")
    return root


def test_n1b_execution_probe_finds_supervisor_child_and_ffmpeg(tmp_path):
    from app.worker.execution import _probe_execution

    execution = "01K70000000000000000000006"
    proc = _fake_proc(
        Path(tmp_path) / "proc",
        {
            10: ("S", [b"python", b"supervisor.py", b"audio", execution.encode()]),
            11: ("S", [b"ffmpeg", f"/x/.pending-{execution}/t".encode()]),
            12: ("S", [b"python", b"other.py"]),
        },
    )
    assert _probe_execution(execution, proc=proc) is True
    assert _probe_execution("01K7ZZZZZZZZZZZZZZZZZZZZZZ", proc=proc) is False


def test_n1b_execution_probe_ignores_zombies_and_needs_proc(tmp_path):
    from app.worker.execution import _probe_execution

    execution = "01K70000000000000000000006"
    proc = _fake_proc(
        Path(tmp_path) / "proc", {10: ("Z", [b"python", execution.encode()])}
    )
    assert _probe_execution(execution, proc=proc) is False
    with pytest.raises(OSError, match="PROC_UNAVAILABLE"):
        _probe_execution(execution, proc=Path(tmp_path) / "no-proc")


def _launching_world(tmp_path):
    from app.migrations.cpu_publication_invariants import cas
    from test_worker_publication_invariants import EXECUTION

    engine, service = _reserved_world(tmp_path, identity=LAUNCHING)
    return engine, service, EXECUTION, cas


def test_n1b_launching_after_restart_is_dead_when_nothing_runs_for_the_execution(
    tmp_path,
):
    from test_worker_publication_invariants import POST

    engine, service, execution, _ = _launching_world(tmp_path)
    service._execution_probe = lambda execution_id: False
    try:
        assert service.resumable_jobs() == [POST]
        _request_cancel(engine)
        assert service.cancel_interrupted(POST) is True
    finally:
        engine.dispose()


def test_n1b_launching_after_restart_is_not_dead_if_a_process_still_belongs_to_it(
    tmp_path,
):
    from test_worker_publication_invariants import POST

    engine, service, execution, _ = _launching_world(tmp_path)
    seen = []

    def alive(execution_id):
        seen.append(execution_id)
        return True

    service._execution_probe = alive
    try:
        assert service.resumable_jobs() == []
        assert seen == [execution]
        _request_cancel(engine)
        assert service.cancel_interrupted(POST) is False
    finally:
        engine.dispose()


def test_n1b_launching_without_proc_proves_nothing(tmp_path):
    engine, service, _, _ = _launching_world(tmp_path)

    def no_proc(execution_id):
        raise OSError("PROC_UNAVAILABLE")

    service._execution_probe = no_proc
    try:
        assert service.resumable_jobs() == []
    finally:
        engine.dispose()


def test_n1c_resume_after_restart_with_launching_marker_claims_the_execution(tmp_path):
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service, _, _ = _launching_world(tmp_path)
    service._execution_probe = lambda execution_id: False
    try:
        assert service.claim_resume(POST) == EXECUTION
        assert _identity(engine) is None
    finally:
        engine.dispose()


# --- N5: las sondas llevan backoff y el backoff se poda -----------------------


def test_n5_unproven_probe_is_not_repeated_every_tick(tmp_path):
    engine, service = _reserved_world(tmp_path)
    probes = []

    def alive(pid):
        probes.append(pid)
        return DEAD["birth"]

    service._birth_probe = alive
    try:
        for _ in range(5):
            assert service.resumable_jobs() == []
        assert len(probes) == 1
        service._backoff.clear()
        service.resumable_jobs()
        assert len(probes) == 2
    finally:
        engine.dispose()


def test_n5_expired_backoff_entries_are_pruned(tmp_path):
    engine, service, _ = _lane_world(tmp_path, ["queued"])
    service.backoff_s = 0.01
    try:
        for index in range(50):
            service._back_off(("probe", f"old-{index}"))
        time.sleep(0.05)
        service._back_off(("probe", "fresh"))
        assert list(service._backoff) == [("probe", "fresh")]
    finally:
        engine.dispose()


# --- N3: el reencolado limpia también el run dir huérfano ---------------------


def test_n3_requeue_removes_the_orphan_run_dir_but_keeps_known_ones(tmp_path):
    from test_worker_publication_invariants import EXECUTION

    engine, service, ids = _lane_world(tmp_path, ["running"])
    base = Path(tmp_path) / "data" / "tmp" / "_server_cpu"
    orphan = base / "01K7ORPHAN000000000000000A"
    foreign = base / "not-a-ulid"
    for folder in (orphan, foreign):
        folder.mkdir(parents=True)
        (folder / "post-plan.json").write_bytes(b"{}")
    try:
        service.reconcile_startup()
        assert not orphan.exists()
        assert foreign.exists()
        assert EXECUTION  # el id conocido de una cpu_execution real se respeta en fix1
    finally:
        engine.dispose()


# --- N2: un borrado fallido se reintenta --------------------------------------


def test_n2_failed_removal_is_deferred_and_retried(monkeypatch):
    import os
    from uuid import uuid4

    from app.db import create_db_engine, migrate
    from app.queue.cleanup import CancelSweeper
    from test_dispatcher_recovery import settings

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    migrate(root / "studio.sqlite")
    engine = create_db_engine(root / "studio.sqlite")
    try:
        data = settings().data_dir
        from test_dispatcher_recovery import prepared

        jid, owner, claim = prepared(engine)
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE job SET status='cancelled', updated_at=? WHERE id=?",
                (models.utc_now(), jid),
            )
        attempt_dir = data / "tmp" / claim.attempt_id
        attempt_dir.mkdir(parents=True)
        (attempt_dir / "raw.wav").write_bytes(b"x")
        real = shutil.rmtree
        calls = {"n": 0}

        def flaky(path, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("busy")
            return real(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", flaky)
        sweeper = CancelSweeper(engine, owner, data)
        sweeper.MARGIN_S = 0
        sweeper.run(force=True)
        assert attempt_dir.exists() and jid in sweeper.deferred
        time.sleep(0.01)
        sweeper.run()  # `since` ya avanzó: solo el aplazado lo recupera
        assert not attempt_dir.exists()
        assert jid not in sweeper.deferred
    finally:
        engine.dispose()
