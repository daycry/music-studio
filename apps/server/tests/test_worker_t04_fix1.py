"""T-04 fix1: huérfanos sin cpu_execution, orden de locks, gaps SSE, carril y barrido."""
# ruff: noqa: RUF059  (helpers importados de otros tests)

import threading
import time
from pathlib import Path
from types import SimpleNamespace

from app import models
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_worker_resume import (
    DEAD,
    _lane_world,
    _request_cancel,
    _reserved_world,
)


class Spy:
    """Bus espía: cuenta las invalidaciones (``mark_gap``) que cortan los SSE."""

    def __init__(self):
        self.gaps = 0

    def mark_gap(self):
        self.gaps += 1

    def publish_confirmed(self, envelope):
        return True


def _states(engine, ids):
    with Session(engine) as session:
        return [
            (session.get(models.Job, i).status, session.get(models.Job, i).attempt)
            for i in ids
        ]


# --- I1: post sin cpu_execution tras un reinicio ------------------------------


def test_i1_running_post_without_execution_is_requeued(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["running", "running", "queued"])
    try:
        assert service.reconcile_startup() == 0  # nada que marcar interrupted
        assert _states(engine, ids) == [("queued", 0), ("queued", 0), ("queued", 0)]
        # y se reclaman de nuevo: el carril no queda ocupado por fantasmas
        assert [service.claim_job(i) for i in ids] == [True, True, False]
    finally:
        engine.dispose()


def test_i1_interrupted_post_without_execution_is_requeued(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["interrupted", "interrupted"])
    try:
        service.reconcile_startup()
        assert _states(engine, ids) == [("queued", 0), ("queued", 0)]
    finally:
        engine.dispose()


def test_i1_post_with_live_execution_in_this_process_is_left_alone(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["running"])
    service.job_executions[ids[0]] = "exec"
    try:
        service.reconcile_startup()
        assert _states(engine, ids) == [("running", 1)]
    finally:
        engine.dispose()


def test_i1_post_with_execution_is_not_requeued(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    try:
        assert _states(engine, [POST]) == [("interrupted", 1)]
    finally:
        engine.dispose()


def test_i1_orphan_partial_inputs_are_removed_but_foreign_dirs_kept(tmp_path):
    from test_worker_publication_invariants import EXECUTION

    engine, service, ids = _lane_world(tmp_path, ["running"])
    base = Path(tmp_path) / "data" / "tmp" / "_server_inputs"
    orphan = base / "01K7ORPHAN000000000000000A"
    engine_staged = base / ("ab" * 16)  # entradas de engine: uuid4().hex
    known = base / EXECUTION
    for folder in (orphan, engine_staged, known):
        folder.mkdir(parents=True)
        (folder / "0.wav").write_bytes(b"x")
    try:
        service.reconcile_startup()
        assert not orphan.exists()
        assert engine_staged.exists()
    finally:
        engine.dispose()


# --- B1: un solo orden de locks (``_guard`` antes que la barrera) -------------


def test_b1_claim_resume_never_takes_guard_inside_the_barrier(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    in_proof, a_has_guard = threading.Event(), threading.Event()
    outcome = {}
    real = service._process_dead

    def slow_dead(identity):
        in_proof.set()
        a_has_guard.wait(5)
        return real(identity)

    service._process_dead = slow_dead

    def a():  # como execute(): ``_guard`` y luego la barrera del coordinador
        in_proof.wait(5)
        with service._guard:
            a_has_guard.set()
            try:
                service.publisher.transaction(lambda connection: 1)
                outcome["a"] = "ok"
            except Exception as error:  # noqa: BLE001
                outcome["a"] = type(error).__name__

    def b():
        outcome["b"] = service.claim_resume(POST)

    threads = [threading.Thread(target=b), threading.Thread(target=a)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(15)
    try:
        assert outcome["a"] == "ok"
        assert outcome["b"] is not None
    finally:
        engine.dispose()


def test_b1_cancel_never_takes_guard_inside_the_barrier(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    _request_cancel(engine)
    in_proof, a_has_guard = threading.Event(), threading.Event()
    outcome = {}
    real = service._process_dead

    def slow_dead(identity):
        in_proof.set()
        a_has_guard.wait(5)
        return real(identity)

    service._process_dead = slow_dead

    def a():
        in_proof.wait(5)
        with service._guard:
            a_has_guard.set()
            try:
                service.publisher.transaction(lambda connection: 1)
                outcome["a"] = "ok"
            except Exception as error:  # noqa: BLE001
                outcome["a"] = type(error).__name__

    def b():
        outcome["b"] = service.cancel_interrupted(POST)

    threads = [threading.Thread(target=b), threading.Thread(target=a)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(15)
    try:
        assert outcome["a"] == "ok"
        assert outcome["b"] is True
    finally:
        engine.dispose()


# --- B2: lo rechazado no invalida el feed ni se reintenta a 0,1 s -------------


def test_b2_refused_cancel_marks_no_gap_and_is_not_retried_hot(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    spy = Spy()
    service.publisher.bus = spy
    probes = []

    def alive(pid):
        probes.append(pid)
        return DEAD["birth"]

    service._birth_probe = alive
    _request_cancel(engine)
    try:
        for _ in range(5):
            assert service.cancel_job(POST) is False
        assert spy.gaps == 0
        assert len(probes) == 1  # el rechazo se recuerda: no se vuelve a sondear
    finally:
        engine.dispose()


def test_b2_refused_resume_marks_no_gap(tmp_path, monkeypatch):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    spy = Spy()
    service.publisher.bus = spy
    monkeypatch.setattr(service, "_occupied_slots", lambda session, **kw: 2)
    try:
        for _ in range(5):
            service._resumed.clear()
            assert service.claim_resume(POST) is None
        assert spy.gaps == 0
    finally:
        engine.dispose()


def test_b2_effective_claim_and_cancel_still_invalidate_the_feed(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    spy = Spy()
    service.publisher.bus = spy
    try:
        assert service.claim_resume(POST) is not None
        assert spy.gaps == 1
    finally:
        engine.dispose()


def test_b2_backoff_expires(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    service.backoff_s = 0.05
    service._birth_probe = lambda pid: DEAD["birth"]
    _request_cancel(engine)
    try:
        assert service.cancel_job(POST) is False
        service._birth_probe = lambda pid: None
        assert service.cancel_job(POST) is False  # aún en espera
        time.sleep(0.1)
        assert service.cancel_job(POST) is True
    finally:
        engine.dispose()


# --- B3: todo owner vivo ocupa un slot ----------------------------------------


def test_b3_retained_owner_occupies_a_slot_after_job_executions_empties(tmp_path):
    engine, service, ids = _lane_world(
        tmp_path, ["interrupted", "interrupted", "queued"]
    )
    service.owners["exec-a"] = object()
    service._owner_jobs["exec-a"] = ids[0]
    service.owners["exec-b"] = object()
    service._owner_jobs["exec-b"] = ids[1]
    try:
        assert service.claim_job(ids[2]) is False
    finally:
        engine.dispose()


def test_b3_live_owner_counts_even_if_the_job_row_was_deleted(tmp_path):
    engine, service, ids = _lane_world(
        tmp_path, ["running+deleted", "running", "queued"]
    )
    service.owners["exec-a"] = object()
    service._owner_jobs["exec-a"] = ids[0]
    try:
        assert service.claim_job(ids[2]) is False
    finally:
        engine.dispose()


def test_b3_not_double_counted_when_both_sql_running_and_live(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["running", "queued"])
    service.job_executions[ids[0]] = "exec-a"
    service.owners["exec-a"] = object()
    service._owner_jobs["exec-a"] = ids[0]
    try:
        assert service.claim_job(ids[1]) is True  # solo hay 1 slot ocupado
    finally:
        engine.dispose()


# --- m2: otro owner no ocupa slot ---------------------------------------------


def test_m2_jobs_of_another_owner_do_not_occupy_a_slot(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["running", "running", "queued"])
    other = CpuAudioServiceFor(engine, tmp_path, "01K7OTHEROWNER000000000000")
    try:
        with Session(engine) as session:
            assert other._occupied_slots(session) == 0
            assert service._occupied_slots(session) == 2
    finally:
        engine.dispose()


def CpuAudioServiceFor(engine, tmp_path, owner):
    from app.publication import PublicationCoordinator
    from app.worker.execution import CpuAudioService

    return CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=Path(tmp_path) / "ffmpeg",
        owner_id=owner,
    )


# --- m1 / B4: la prueba de muerte --------------------------------------------


def test_m1_launching_marker_is_not_a_proof_of_death(tmp_path):
    engine, service, _ = _lane_world(tmp_path, ["queued"])
    try:
        assert service._process_dead({"launching": True}) is False
        assert service._process_dead(None) is True
    finally:
        engine.dispose()


def test_m1_identity_is_recorded_before_the_group_is_launched(tmp_path, monkeypatch):
    """Si el server muere entre lanzar el grupo y guardar la identidad, no es muerte."""
    from app.worker import execution as execution_module
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service = _reserved_world(tmp_path)
    assert service.claim_resume(POST) == EXECUTION
    seen = {}

    class Boom(Exception):
        pass

    def launch(*args, **kwargs):
        with Session(engine) as session:
            seen["identity"] = session.get(
                models.CpuExecution, EXECUTION
            ).process_identity
        raise Boom

    monkeypatch.setattr(execution_module, "LinuxGroup", launch)
    plan = _plan(engine)
    service.publisher.receipt_hashes[EXECUTION] = "d" * 64
    service.publisher.prepared_contexts[EXECUTION] = SimpleNamespace(payload=b"{}")
    monkeypatch.setattr(
        service,
        "_prepare",
        lambda plan, execution_id, resume=False: (_cpu_row(engine), Path(tmp_path)),
    )
    try:
        try:
            service.execute(plan, execution_id=EXECUTION, resume=True)
        except Boom:
            pass
        assert seen["identity"] == {"launching": True}
    finally:
        engine.dispose()


def _plan(engine):
    from app.worker.contracts import PostPlan
    from test_worker_publication_invariants import EXECUTION

    with Session(engine) as session:
        return PostPlan.model_validate(session.get(models.CpuExecution, EXECUTION).plan)


def _cpu_row(engine):
    from test_worker_publication_invariants import EXECUTION

    with engine.connect() as connection:
        return dict(
            connection.execute(
                select(models.CpuExecution.__table__).where(
                    models.CpuExecution.id == EXECUTION
                )
            )
            .mappings()
            .one()
        )


def test_b4_surviving_group_member_is_not_death(tmp_path):
    engine, service = _reserved_world(tmp_path)
    try:
        service._birth_probe = lambda pid: None  # el líder ya no está
        service._group_probe = lambda leader: True  # pero queda un miembro
        assert service._process_dead(DEAD) is False
        service._group_probe = lambda leader: False
        assert service._process_dead(DEAD) is True
    finally:
        engine.dispose()


def test_b4_without_proc_nothing_is_proven(tmp_path):
    engine, service = _reserved_world(tmp_path)

    def no_proc(leader):
        raise OSError("PROC_UNAVAILABLE")

    try:
        service._group_probe = no_proc
        assert service._process_dead(DEAD) is False
    finally:
        engine.dispose()


# --- D1: el barrido no relee todo el histórico --------------------------------


def _cancelled_engine_jobs(engine, count):
    from test_dispatcher_admission import add

    ids = []
    for _ in range(count):
        jid, owner = add(engine, status="cancelled", finished_at="2026-10-22T00:00:00Z")
        ids.append(jid)
    return ids, owner


def test_d1_sweeper_scans_history_once_then_only_what_changed():
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
        _, owner = _cancelled_engine_jobs(engine, 3)
        sweeper = CancelSweeper(engine, owner, settings().data_dir)
        sweeper.MARGIN_S = 0
        sweeper.run(force=True)
        assert sweeper.last_scanned == 3  # arranque: histórico completo
        sweeper.run()
        assert sweeper.last_scanned == 0  # nada nuevo: no se relee el histórico
        _cancelled_engine_jobs(engine, 1)
        sweeper.run()
        assert sweeper.last_scanned == 1
    finally:
        engine.dispose()
