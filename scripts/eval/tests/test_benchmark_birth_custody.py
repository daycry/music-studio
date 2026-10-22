"""Windows CPU benigno. Demora controlada tras Popen real, no syscall bloqueada.

Los eventos, threads, poll y escrituras de witness son observadores declarados.
El test retiene sus objetos nativos; eso no acredita custodia de producciÃƒÂ³n.
Ejecutar sÃƒÂ³lo tras la barrera terminal del ensayo SSE sensible.
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import benchmark_process as process_api
import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Job real requerido")


@pytest.fixture
def native_fixture():
    root = Path(os.environ["STUDIO_TEST_ROOT"]) / uuid.uuid4().hex
    root.mkdir(parents=True)
    fixture = root / "birth_handler.py"
    fixture.write_text(
        "from pathlib import Path\n"
        "class Handler:\n"
        "    def __init__(self, config):\n"
        "        Path(config['marker']).write_text('gate reached')\n"
        "    def __call__(self, payload, emit):\n"
        "        return {'echo': payload['operation']}\n"
        "    def close(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    source = fixture.read_bytes()
    (root / "birth_handler.before.py").write_bytes(source)
    (root / "fixture-before.json").write_text(
        json.dumps(
            {
                "utc_ns": time.time_ns(),
                "monotonic_ns": time.perf_counter_ns(),
                "path": str(fixture),
                "sha256": hashlib.sha256(source).hexdigest(),
            }
        )
    )
    return root, fixture, root / "handler-started.txt"


def test_actual_native_positive_bootstrap(native_fixture):
    root, fixture, marker = native_fixture
    worker = process_api.OwnedProcess({"marker": str(marker)}, f"{fixture}:Handler")
    try:
        original = worker.ownership.copy()
        response = worker.call(
            {"operation": "echo"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
        assert response["value"] == {"echo": "echo"}
        assert marker.read_text() == "gate reached"
        assert worker.job.evidence(worker.process) == original
    finally:
        worker.close(graceful=False)
    (root / "positive-close.json").write_text(json.dumps(worker.close_evidence))
    assert worker.close_evidence["resources_returned"] is True


def test_actual_native_absolute_deadline_caps_default(native_fixture, monkeypatch):
    root, fixture, marker = native_fixture
    original = process_api.WindowsJob.assign
    observations = []

    def delayed_assignment(job, native):
        observations.append((job, native, time.perf_counter_ns()))
        time.sleep(0.3)  # Controlled delay before real native assignment.
        return original(job, native)

    monkeypatch.setattr(process_api.WindowsJob, "assign", delayed_assignment)
    deadline = time.perf_counter_ns() + 100_000_000
    with pytest.raises(process_api.WorkerDeadline) as caught:
        process_api.OwnedProcess(
            {"marker": str(marker)},
            f"{fixture}:Handler",
            startup_deadline_ns=deadline,
        )
    returned = time.perf_counter_ns()
    owned = caught.value._owned_cleanup_resource
    (root / "assignment-before-assert.json").write_text(
        json.dumps(
            {
                "deadline_ns": deadline,
                "returned_ns": returned,
                "native_pid_observed": observations[0][1].pid,
                "revoked": owned._birth_record.revoked,
            }
        )
    )
    assert returned < deadline + 150_000_000
    assert owned._birth_record.revoked
    owned._birth_record.thread.join(3)
    assert not owned._birth_record.thread.is_alive()
    assert not marker.exists()
    assert observations[0][1].poll() is not None
    assert owned._birth_record.process is observations[0][1]


def test_episode_entry_budget_includes_real_context_read(native_fixture, monkeypatch):
    import copy

    import benchmark_episode as episode
    from test_benchmark_observation import CONTEXT

    root, fixture, marker = native_fixture
    fixture = root / "episode_handler.py"
    fixture.write_text(
        "from pathlib import Path\nclass Handler:\n"
        "    def __init__(self, config):\n"
        "        Path(config['sensor_config']['marker']).write_text('gate reached')\n"
        "    def __call__(self, payload, emit): return {}\n"
        "    def close(self): pass\n"
    )
    (root / "episode_handler.before.py").write_bytes(fixture.read_bytes())
    context = root / "context.json"
    context.write_text(json.dumps(copy.deepcopy(CONTEXT)))
    (root / "context.before.json").write_bytes(context.read_bytes())
    original = episode.read_json
    observed = []

    def delayed_read(path):
        value = original(path)  # Actual fixture read; controlled delay afterwards.
        observed.append(time.perf_counter_ns())
        time.sleep(1.2)
        return value

    monkeypatch.setattr(episode, "read_json", delayed_read)
    started = time.perf_counter_ns()
    result = failure = None
    try:
        result = episode.EpisodeAcquirer(
            root=root / "publications",
            context_path=context,
            sensor_config={"marker": str(marker)},
            trusted_handler=f"{fixture}:Handler",
            startup_timeout_s=1,
        )
    except BaseException as error:  # noqa: BLE001 - testigo conserva la excepción original
        failure = error
    finally:
        if result is not None:
            result.close()
    (root / "episode-entry-before-assert.json").write_text(
        json.dumps(
            {
                "started_ns": started,
                "returned_ns": time.perf_counter_ns(),
                "actual_read_ns": observed,
                "failure_type": type(failure).__name__,
                "native_returned": result is not None,
            }
        )
    )
    assert isinstance(failure, process_api.WorkerDeadline)


@pytest.fixture
def actual_episode(native_fixture):
    import importlib.util

    root, _, _ = native_fixture
    original = Path.cwd() / "scripts/eval/tests/test_benchmark_episode_v3.py"
    source = original.read_text(encoding="utf-8")
    source = source.replace(
        'PHASE = Path.cwd() / ".cache/dev-cycle/t09/publication-v3-implementation"',
        f"PHASE = Path({str(root)!r})",
    )
    private = root / "private_episode_test.py"
    private.write_text(source, encoding="utf-8")
    (root / "private_episode_test.before.py").write_bytes(private.read_bytes())
    spec = importlib.util.spec_from_file_location("private_episode_test", private)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    make = module.episode_factory.__wrapped__()
    observer, _ = make()
    try:
        yield observer
    finally:
        observer.close()


def test_coordinator_shared_startup_deadline_and_original_episode_window(
    actual_episode, native_fixture
):
    from benchmark_coordinator import ContinuousCoordinator, CoordinatedOwnedProcess

    deadline = time.perf_counter_ns() + 1_500_000_000
    service = ContinuousCoordinator(
        actual_episode, interval_s=0.1, startup_deadline_ns=deadline
    )
    with service:
        assert service._startup_budget.deadline_ns == deadline
        _, fixture, marker = native_fixture
        worker = CoordinatedOwnedProcess(
            {"marker": str(marker)},
            f"{fixture}:Handler",
            coordinator=service,
            startup_deadline_ns=deadline,
        )
        try:
            assert worker._birth_record.budget.deadline_ns == deadline
            assert worker.job.evidence(worker.process) == worker.ownership
            assert marker.exists()
        finally:
            worker.close(graceful=False)
        assert actual_episode.worker.ownership["job_member"] is True
        request = actual_episode.worker._last_completion[0]
        data = process_api.decode(request)["arguments"]
        assert data["deadline_ns"] == data["start"]["monotonic_ns"] + 2_000_000_000


def test_coordinator_condition_wait_is_bounded_and_retained(actual_episode):
    from benchmark_coordinator import ContinuousCoordinator

    deadline = time.perf_counter_ns() + 100_000_000
    service = ContinuousCoordinator(actual_episode, startup_deadline_ns=deadline)
    release = threading.Event()
    held = threading.Event()

    def hold():
        with service.condition:
            held.set()
            release.wait(3)

    holder = threading.Thread(target=hold, name="controlled-original-condition-holder")
    holder.start()
    assert held.wait(1)
    try:
        with pytest.raises(TimeoutError):
            service.__enter__()
        returned = time.perf_counter_ns()
        witness = {
            "deadline_ns": deadline,
            "returned_ns": returned,
            "holder_alive": holder.is_alive(),
            "stop": service.stop.is_set(),
        }
        (
            Path(os.environ["STUDIO_TEST_ROOT"]) / "condition-before-assert.json"
        ).write_text(json.dumps(witness))
        assert returned < deadline + 150_000_000
        assert service.stop.is_set()
        assert service._startup_cleanup_thread.is_alive()
    finally:
        release.set()
        holder.join(3)
        service._startup_cleanup_thread.join(3)


def test_delayed_actual_popen_revokes_before_late_gate(native_fixture, monkeypatch):
    root, fixture, marker = native_fixture
    original_popen = subprocess.Popen
    foreign = original_popen(
        [sys._base_executable, "-c", "import time; time.sleep(60)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    release = threading.Event()
    born = threading.Event()
    witness = {
        "kind": "controlled delay AFTER actual Popen return; not blocked OS call"
    }
    strong = []
    outcome = []

    def delayed_popen(*args, **kwargs):
        witness["native_enter_ns"] = time.perf_counter_ns()
        native = original_popen(*args, **kwargs)
        strong.append(native)
        witness["native_return_ns"] = time.perf_counter_ns()
        witness["pid"] = native.pid  # Observation only; never authority for cleanup.
        witness["argv"] = args[0]
        born.set()
        release.wait(10)
        witness["wrapper_release_ns"] = time.perf_counter_ns()
        return native

    def construct():
        witness["caller_enter_ns"] = time.perf_counter_ns()
        try:
            outcome.append(
                process_api.OwnedProcess(
                    {"marker": str(marker)}, f"{fixture}:Handler", startup_timeout_s=0.2
                )
            )
        except BaseException as error:  # noqa: BLE001 - testigo conserva la excepción original
            outcome.append(error)
        finally:
            witness["caller_return_ns"] = time.perf_counter_ns()

    monkeypatch.setattr(process_api.subprocess, "Popen", delayed_popen)
    caller = threading.Thread(target=construct, name="test-controlled-birth-caller")
    caller.start()
    try:
        assert born.wait(3), "actual Popen did not produce the controlled witness"
        caller.join(0.5)
        witness["observation_ns"] = time.perf_counter_ns()
        witness["caller_pending"] = caller.is_alive()
        witness["owned_poll"] = strong[0].poll()
        witness["foreign_poll"] = foreign.poll()
        witness["marker_before_release"] = marker.exists()
        (root / "before-assertion-witness.json").write_text(json.dumps(witness))
        assert not caller.is_alive(), (
            "caller blocked past original startup budget in native birth"
        )
        assert isinstance(outcome[0], process_api.WorkerDeadline)
        assert not marker.exists()
        # Strong original production record is required, independently of test refs.
        owned = outcome[0]._owned_cleanup_resource
        record = owned._birth_record
        assert record.revoked is True
        # The wrapper has not returned its Popen yet. Production cannot claim
        # a handle it has not received: its retained actor owns the native
        # result through the wrapper's stack until the actual return.
        assert record.process is None
        assert record.thread.is_alive()
        assert foreign.poll() is None
        release.set()
        record.thread.join(3)
        caller.join(3)
        assert record.process is strong[0]
        assert not marker.exists(), "late native result received handler gate"
        assert record.revoked is True
        assert strong[0].poll() is not None
        assert foreign.poll() is None
    finally:
        release.set()
        caller.join(5)
        for result in outcome:
            if isinstance(result, process_api.OwnedProcess):
                result.close(graceful=False)
        for native in strong:
            if native.poll() is None:
                native.kill()  # Only the original object created by this test.
            native.wait(timeout=3)
            for pipe in (native.stdin, native.stdout, native.stderr):
                if pipe is not None:
                    pipe.close()
        foreign.kill()
        foreign.wait(timeout=3)
        witness["test_cleanup_ns"] = time.perf_counter_ns()
        witness["caller_joined"] = not caller.is_alive()
        witness["foreign_exit"] = foreign.returncode
        witness["owned_exits"] = [native.returncode for native in strong]
        (root / "final-witness.json").write_text(json.dumps(witness))
