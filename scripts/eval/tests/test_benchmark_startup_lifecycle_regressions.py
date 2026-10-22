"""Custodia Windows propia; barreras pasantes, sin bloqueo físico de syscalls.

El doble acquirer sólo configura el coordinador en memoria. Los procesos, Jobs,
pipes y consultas de los casos nativos son reales y exclusivos de cada fixture.
"""

import json
import os
import threading
import time
import uuid
import weakref
from pathlib import Path
from types import SimpleNamespace

import benchmark_coordinator as coordinator_api
import benchmark_process as process_api
import pytest


def service():
    coordinator = coordinator_api.ContinuousCoordinator(
        SimpleNamespace(observation_method="wddm_auto_v3", observation_context={})
    )
    # Scheduling fixture only: no sampler/OS observation is claimed.
    coordinator.started = True
    return coordinator


def joined_cleanup(worker):
    record = worker._birth_record
    if record.thread is not None:
        record.thread.join(3)
        assert not record.thread.is_alive()
    for actor in list(record.actors):
        actor.thread.join(3)
        assert not actor.thread.is_alive()
    worker.close(graceful=False)
    if record.cleanup_thread is not None:
        record.cleanup_thread.join(3)
        assert not record.cleanup_thread.is_alive()
    worker._publish_cleanup_if_joined()
    if worker.process is not None:
        assert worker.process.poll() is not None
        assert worker.process.returncode is not None
        assert worker.process.stdin.closed and worker.process.stdout.closed
        assert worker.process._handle.closed
    assert worker.job is None or worker.job.handle is None
    assert worker.reader is None or not worker.reader.is_alive()
    assert all(not writer.is_alive() for writer in worker._writers)


@pytest.fixture
def native_case():
    if os.name != "nt":
        pytest.skip("Windows Job real requerido")
    root = Path(os.environ["STUDIO_TEST_ROOT"]) / uuid.uuid4().hex
    root.mkdir(parents=True)
    handler = root / "handler.py"
    handler.write_text(
        "class Handler:\n"
        "    def __init__(self, config): pass\n"
        "    def __call__(self, payload, emit): return payload['operation']\n"
        "    def close(self): pass\n",
        encoding="utf8",
    )
    (root / "handler.before.py").write_bytes(handler.read_bytes())
    owned = []

    def create(*, coordinator=None, **kwargs):
        try:
            if coordinator is None:
                worker = process_api.OwnedProcess({}, f"{handler}:Handler", **kwargs)
            else:
                worker = coordinator_api.CoordinatedOwnedProcess(
                    {}, f"{handler}:Handler", coordinator=coordinator, **kwargs
                )
        except BaseException as error:
            worker = getattr(error, "_owned_cleanup_resource", None)
            if worker is not None:
                owned.append(worker)
            raise
        owned.append(worker)
        return worker

    create.owned = owned
    yield create, root
    proofs = []
    for worker in owned:
        joined_cleanup(worker)
        proofs.append(worker.close_evidence)
    (root / "trusted-fixture-closure.json").write_text(json.dumps(proofs))


def test_completed_actual_worker_actions_release_references(native_case, monkeypatch):
    create, root = native_case
    refs = []
    original = process_api._NativeAction.__init__

    def observe(actor, owned, action):
        original(actor, owned, action)
        refs.append((weakref.ref(actor), weakref.ref(action)))

    monkeypatch.setattr(process_api._NativeAction, "__init__", observe)
    worker = create()
    for _ in range(40):
        assert (
            worker.call(
                {"operation": "echo"},
                deadline_ns=time.perf_counter_ns() + 2_000_000_000,
            )["value"]
            == "echo"
        )
    retained = sum(
        actor() is not None or closure() is not None for actor, closure in refs
    )
    (root / "retention-before-assert.json").write_text(
        json.dumps({"calls": 40, "observed_actions": len(refs), "retained": retained})
    )
    assert retained == 0, "joined actions still retain closures/results"


def test_predeadline_native_failure_survives_late_caller(native_case, monkeypatch):
    create, _ = native_case
    worker = create()
    primary = OSError("actual evidence followed by controlled failure")
    original = process_api._NativeAction.__init__

    def delayed_observer(actor, owned, action):
        original(actor, owned, action)
        wait = actor.done.wait

        def scheduled_after_deadline(timeout=None):
            result = wait(timeout)
            time.sleep(0.15)  # Caller scheduling injection, not kernel delay.
            return result

        actor.done.wait = scheduled_after_deadline

    monkeypatch.setattr(process_api._NativeAction, "__init__", delayed_observer)
    captured = []

    def actual_failure():
        assert worker.job.evidence(worker.process) == worker.ownership
        captured.append(time.perf_counter_ns())
        raise primary

    deadline = time.perf_counter_ns() + 100_000_000
    with pytest.raises(BaseException) as caught:
        worker._native(actual_failure, deadline)
    assert captured[0] < deadline < time.perf_counter_ns()
    assert caught.value is primary
    assert any(
        frame.name == "actual_failure"
        for frame in __import__("traceback").extract_tb(primary.__traceback__)
    )


def test_predeadline_birth_failure_survives_late_caller(native_case, monkeypatch):
    create, _ = native_case
    primary = OSError("controlled failure after actual assignment")
    assign = process_api.WindowsJob.assign
    init = process_api._BirthRecord.__init__
    captured = []

    def failed_assignment(job, child):
        assign(job, child)
        captured.append(time.perf_counter_ns())
        raise primary

    def delayed_observer(record, owned, budget):
        init(record, owned, budget)
        wait = record.done.wait

        def scheduled_after_deadline(timeout=None):
            result = wait(timeout)
            time.sleep(0.3)
            return result

        record.done.wait = scheduled_after_deadline

    monkeypatch.setattr(process_api.WindowsJob, "assign", failed_assignment)
    monkeypatch.setattr(process_api._BirthRecord, "__init__", delayed_observer)
    deadline = time.perf_counter_ns() + 250_000_000
    with pytest.raises(BaseException) as caught:
        create(startup_deadline_ns=deadline)
    assert captured[0] < deadline < time.perf_counter_ns()
    assert caught.value is primary


def test_final_coordinator_check_cleanup_keeps_original_deadline(
    native_case, monkeypatch
):
    create, root = native_case
    coordinator = service()
    base = process_api.OwnedProcess.__init__
    close = process_api.OwnedProcess.close
    observed = []
    deadline = time.perf_counter_ns() + 600_000_000
    locked = threading.Event()
    release_cleanup = threading.Event()
    blocker = None
    cleanup = process_api.OwnedProcess._cleanup

    def stalled_cleanup(worker, **kwargs):
        assert release_cleanup.wait(2)
        return cleanup(worker, **kwargs)

    def completed_base(worker, *args, **kwargs):
        nonlocal blocker
        base(worker, *args, **kwargs)
        create.owned.append(worker)
        observed.append(("base", time.perf_counter_ns()))

        def hold_final_condition():
            with coordinator.condition:
                locked.set()
                time.sleep(max(0, (deadline - time.perf_counter_ns()) / 1e9) + 0.02)

        blocker = threading.Thread(
            target=hold_final_condition, name="u1-final-condition-witness"
        )
        blocker.start()
        assert locked.wait(1)

    def observed_close(worker, **kwargs):
        observed.append(
            ("cleanup_deadline", getattr(worker, "_startup_cleanup_deadline_ns", None))
        )
        return close(worker, **kwargs)

    monkeypatch.setattr(process_api.OwnedProcess, "__init__", completed_base)
    monkeypatch.setattr(process_api.OwnedProcess, "close", observed_close)
    monkeypatch.setattr(process_api.OwnedProcess, "_cleanup", stalled_cleanup)
    try:
        with pytest.raises(TimeoutError):
            create(coordinator=coordinator, startup_deadline_ns=deadline)
        returned = time.perf_counter_ns()
    finally:
        release_cleanup.set()
        if blocker is not None:
            blocker.join(2)
            assert not blocker.is_alive()
    (root / "final-condition-deadline.json").write_text(json.dumps(observed))
    assert observed[0][0] == "base" and observed[0][1] < deadline
    assert observed[1] == ("cleanup_deadline", deadline)
    assert returned < deadline + 120_000_000, "cleanup waited on a fresh budget after D"


@pytest.mark.parametrize("assertion", ["handles", "reservation"])
def test_pending_actual_native_query_keeps_handles_and_reservation(
    native_case, monkeypatch, assertion
):
    create, root = native_case
    coordinator = service()
    original = process_api.WindowsJob.evidence
    entered, release = threading.Event(), threading.Event()
    calls = []
    close = process_api.OwnedProcess.close

    def scheduled_after_cleanup(worker, **kwargs):
        result = close(worker, **kwargs)
        if (
            assertion == "reservation"
            and worker._birth_record.cleanup_thread is not None
        ):
            # Let already-finished cleanup join before the constructor's finally.
            # On corrected code the cleanup remains pending behind the query.
            worker._birth_record.cleanup_thread.join(0.1)
        return result

    def blocked_query(job, child):
        # Assignment evidence is first; startup verification is second.
        calls.append((job, child))
        if len(calls) == 2:
            entered.set()
            assert release.wait(2)
        return original(job, child)

    monkeypatch.setattr(process_api.WindowsJob, "evidence", blocked_query)
    monkeypatch.setattr(process_api.OwnedProcess, "close", scheduled_after_cleanup)
    try:
        with pytest.raises(process_api.WorkerDeadline) as caught:
            create(coordinator=coordinator, startup_timeout_s=1)
        worker = caught.value._owned_cleanup_resource
        assert entered.is_set()
        time.sleep(0.06)
        job, child = calls[1]
        same_open = bool(
            job.handle
            and not child._handle.closed
            and not child.stdin.closed
            and not child.stdout.closed
        )
        reserved = coordinator.active is worker
        (root / "pending-query.json").write_text(
            json.dumps({"same_open": same_open, "reserved": reserved})
        )
        if assertion == "handles":
            assert same_open, "exact handles closed while query still pending"
        else:
            assert reserved, "reservation released with native query pending"
    finally:
        release.set()
    joined_cleanup(worker)
    assert worker.close_evidence["disposition"] == "CLOSED_CONFIRMED"
    following = create(coordinator=coordinator)
    assert (
        following.call(
            {"operation": "after-query"},
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )["value"]
        == "after-query"
    )


def test_joined_late_birth_allows_next_coordinated_operation(native_case, monkeypatch):
    create, _ = native_case
    coordinator = service()
    original = process_api.WindowsJob.assign

    def delayed_assignment(job, child):
        result = original(job, child)
        time.sleep(0.3)
        return result

    monkeypatch.setattr(process_api.WindowsJob, "assign", delayed_assignment)
    with pytest.raises(process_api.WorkerDeadline) as caught:
        create(coordinator=coordinator, startup_timeout_s=0.15)
    worker = caught.value._owned_cleanup_resource
    assert coordinator.active is worker
    joined_cleanup(worker)
    monkeypatch.setattr(process_api.WindowsJob, "assign", original)
    following = create(coordinator=coordinator)
    assert (
        following.call(
            {"operation": "next"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )["value"]
        == "next"
    )
    assert worker.close_evidence["disposition"] == "CLOSED_CONFIRMED"


def test_invalid_oversized_gate_does_not_quarantine_empty_resources():
    before = set(process_api._QUARANTINE)
    config = {"text": "x" * 3900}
    assert (
        len(process_api.encode(config, process_api.MAX_REQUEST))
        < process_api.MAX_REQUEST
    )
    for _ in range(40):
        with pytest.raises(ValueError, match="frame_oversized"):
            process_api.OwnedProcess(config, "x" * 300 + ":Handler")
    assert set(process_api._QUARANTINE) == before, (
        "invalid gates retain empty birth records"
    )


def test_next_admission_does_not_reconcile_a_live_operation(native_case, monkeypatch):
    create, root = native_case
    coordinator = service()
    worker = create()
    receive = worker._receive
    entered, release = threading.Event(), threading.Event()
    outcome = []

    def caller_barrier(deadline_ns):
        entered.set()
        assert release.wait(2)
        return receive(deadline_ns)

    monkeypatch.setattr(worker, "_receive", caller_barrier)

    def operation():
        try:
            outcome.append(
                coordinator.run_owned(
                    "echo", worker, {"operation": "echo"}, timeout_s=2
                )
            )
        except BaseException as error:  # noqa: BLE001 - recoger primera causa del caller observado
            outcome.append(error)

    caller = threading.Thread(target=operation, name="u1-live-operation-witness")
    caller.start()
    try:
        assert entered.wait(1)
        assert worker.job.evidence(worker.process) == worker.ownership
        with pytest.raises(RuntimeError, match="v3_parallel_operation_forbidden"):
            create(coordinator=coordinator)
    finally:
        release.set()
        caller.join(3)
        assert not caller.is_alive()
        (root / "live-operation-witness.json").write_text(
            json.dumps(
                {
                    "outcome_types": [type(value).__name__ for value in outcome],
                    "caller_joined": True,
                }
            )
        )
    assert len(outcome) == 1 and isinstance(outcome[0], dict)
    assert outcome[0]["value"] == "echo"
