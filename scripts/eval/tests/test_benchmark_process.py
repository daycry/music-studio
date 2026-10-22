"""Real Windows subprocess tests; fixture sensors are explicitly simulated."""

import io
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest


def api():
    path = Path(__file__).parents[1] / "benchmark_process.py"
    assert path.is_file(), "bounded owned process API has not been implemented"
    return __import__("benchmark_process")


def test_owned_api_exists_behaviorally():
    module = api()
    assert callable(module.OwnedProcess)
    assert callable(module.OwnedProcess.call)
    assert callable(module.OwnedProcess.close)


@pytest.fixture
def tmp_path():
    path = Path(os.environ["STUDIO_TEST_ROOT"]) / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path


@pytest.fixture
def fixture_module(tmp_path):
    path = tmp_path / "trusted_fixture.py"
    path.write_text(
        """import os, subprocess, sys, threading, time
class Handler:
    def __init__(self, config):
        self.config = config
        self.count = 0
        if config.get("marker"):
            open(config["marker"], "w").write("handler imported after gate")
    def __call__(self, payload, emit):
        self.count += 1
        op = payload["operation"]
        if op == "block":
            child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"])
            emit({"sensor":"simulated", "descendant_pid":child.pid})
            time.sleep(60)
        if op in {"prepare", "persist_block"}:
            prepared = payload["arguments"]["prepared"]
            with open(prepared,"w") as stream:
                stream.write('{"owned":true}')
                stream.flush()
                os.fsync(stream.fileno())
            emit({"prepared":prepared, "sensor":"simulated_persistence_handler"})
            if op == "persist_block":
                time.sleep(60)
            return {"prepared":prepared}
        if op == "commit":
            args = payload["arguments"]
            os.replace(args["prepared"], args["committed"])
            return {"committed":args["committed"]}
        if op == "huge":
            return "x" * 300000
        if op == "wire":
            sys.stdout.buffer.write(payload["arguments"]["frame"].encode())
            sys.stdout.buffer.flush()
            time.sleep(60)
        if op == "native_block":
            from benchmark_windows import WindowsGpuMemory
            windows = WindowsGpuMemory("NVIDIA GeForce RTX 5070")
            windows.progress_callback = lambda raw: emit({"source":"real_windows_raw", "raw":raw})
            windows.pdh.PdhGetCounterInfoW = lambda *args: time.sleep(60)
            windows.sample()
        if op == "fail":
            emit({"sensor":"simulated", "raw":12})
            raise ValueError("real subsequent failure")
        if op == "concurrent_emit":
            barrier = threading.Barrier(8)
            errors = []
            def send(index):
                try:
                    barrier.wait()
                    for offset in range(8):
                        emit({"thread":index, "offset":offset, "payload":"x" * 2048})
                except BaseException as error:
                    errors.append(repr(error))
            threads = [threading.Thread(target=send, args=(index,)) for index in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            if errors:
                raise RuntimeError(";".join(errors))
            return {"concurrent": True}
        return {"sensor":"simulated", "pid":os.getpid(), "count":self.count}
    def close(self):
        pass
""",
        encoding="utf-8",
    )
    return str(path)


def worker(fixture_module, **config):
    return api().OwnedProcess(config, f"{fixture_module}:Handler")


def test_persistent_pid_and_close(fixture_module):
    process = worker(fixture_module)
    try:
        first = process.call(
            {"operation": "echo"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
        second = process.call(
            {"operation": "echo"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
        assert first["value"]["pid"] == second["value"]["pid"] == process.pid
        assert second["value"]["count"] == 2
        assert first["ownership"]["job_member"] is True
        assert first["ownership"]["creation_time"] > 0
        assert (
            first["parent_finished_monotonic_ns"]
            >= first["parent_started_monotonic_ns"]
        )
    finally:
        process.close()
        process.close()
    assert not process.reader.is_alive()
    assert process.process.poll() is not None


def test_block_preserves_progress_and_kills_descendant(fixture_module):
    module = api()
    process = worker(fixture_module)
    deadline = time.perf_counter_ns() + 800_000_000
    with pytest.raises(module.WorkerDeadline) as caught:
        process.call({"operation": "block"}, deadline_ns=deadline)
    assert caught.value.progress[0]["value"]["sensor"] == "simulated"
    descendant = caught.value.progress[0]["value"]["descendant_pid"]
    assert not module.process_alive(descendant)
    assert time.perf_counter_ns() < deadline + 150_000_000
    assert not process.reader.is_alive()
    assert caught.value.status == "incomplete_invalid"


def test_failure_keeps_actual_progress(fixture_module):
    module = api()
    process = worker(fixture_module)
    with pytest.raises(module.WorkerFailure) as caught:
        process.call(
            {"operation": "fail"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
    assert caught.value.progress[0]["value"]["raw"] == 12
    assert "real subsequent failure" in str(caught.value)
    assert not process.reader.is_alive()


def test_huge_reply_is_bounded(fixture_module):
    module = api()
    process = worker(fixture_module)
    with pytest.raises(module.WorkerFailure):
        process.call(
            {"operation": "huge"}, deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
    assert not process.reader.is_alive()


def test_expired_original_deadline_is_not_reset(fixture_module):
    module = api()
    process = worker(fixture_module)
    with pytest.raises(module.WorkerDeadline):
        process.call({"operation": "echo"}, deadline_ns=time.perf_counter_ns() - 1)
    assert process.process.poll() is not None


def test_gate_precedes_trusted_constructor(fixture_module, tmp_path, monkeypatch):
    module = api()
    marker = tmp_path / "startup-marker"
    fixture = Path(fixture_module)
    fixture.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('module import after gate')\n"
        + fixture.read_text()
    )
    original = module.WindowsJob.assign
    observed = []

    def assign(job, process):
        time.sleep(0.05)  # Give the unassigned child a real scheduling opportunity.
        assert not marker.exists()
        observed.append(process.pid)
        return original(job, process)

    monkeypatch.setattr(module.WindowsJob, "assign", assign)
    process = worker(fixture_module, marker=str(marker))
    try:
        assert marker.exists()
        assert observed == [process.pid]
    finally:
        process.close()


def test_failed_assignment_never_opens_handler_gate(
    fixture_module, tmp_path, monkeypatch
):
    module = api()
    marker = tmp_path / "forbidden-marker"
    processes = []

    def refuse(job, process):
        processes.append(process)
        raise ValueError("simulated_assignment_failure")

    monkeypatch.setattr(module.WindowsJob, "assign", refuse)
    with pytest.raises(ValueError, match="assignment_failure"):
        worker(fixture_module, marker=str(marker))
    assert not marker.exists()
    assert processes[0].poll() is not None


def test_no_foreign_termination(fixture_module):
    foreign = subprocess.Popen(
        [sys._base_executable, "-c", "import time;time.sleep(60)"]
    )
    try:
        process = worker(fixture_module)
        process.close()
        assert foreign.poll() is None
        assert api().process_alive(foreign.pid)
    finally:
        foreign.terminate()
        foreign.wait(timeout=2)


@pytest.mark.parametrize(
    "frame",
    [
        '{"type":"result","seq":0,"index":0,"value":{}}\n',
        '{"type":"result","seq":1,"index":2,"value":{}}\n',
        '{"type":"result","seq":true,"index":0,"value":{}}\n',
        '{"type":"result","seq":1,"index":0,"value":NaN}\n',
        '{"type":"result","seq":1,"index":0,"value":1e400}\n',
        '{"type":"result","seq":1,"seq":1,"index":0,"value":null}\n',
        "not json\n",
        "x" * 262145,
    ],
    ids=[
        "stale",
        "reordered",
        "bool-seq",
        "nan",
        "overflow",
        "duplicate",
        "malformed",
        "oversized",
    ],
)
def test_actual_wire_rejections(fixture_module, frame):
    # Huge frames cannot fit the incoming RPC, so a trusted fixture creates them.
    module = api()
    if len(frame) > 4000:
        path = Path(fixture_module)
        path.write_text(
            path.read_text().replace(
                'payload["arguments"]["frame"].encode()', '("x"*262145).encode()'
            )
        )
        frame = "huge"
    process = worker(fixture_module)
    with pytest.raises(module.WorkerFailure):
        process.call(
            {"operation": "wire", "arguments": {"frame": frame}},
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )
    assert not process.reader.is_alive()
    assert process.process.poll() is not None


def test_concurrent_progress_frames_keep_protocol_order(fixture_module):
    process = worker(fixture_module)
    try:
        result = process.call(
            {"operation": "concurrent_emit"},
            deadline_ns=time.perf_counter_ns() + 5_000_000_000,
        )
        assert result["value"] == {"concurrent": True}
        assert len(result["progress"]) == 64
    finally:
        process.close()


def test_truncated_reply_eof(fixture_module):
    path = Path(fixture_module)
    path.write_text(
        path.read_text().replace(
            'time.sleep(60)\n        if op == "native_block"',
            'os._exit(3)\n        if op == "native_block"',
        )
    )
    process = worker(fixture_module)
    with pytest.raises(api().WorkerFailure, match="truncated"):
        process.call(
            {"operation": "wire", "arguments": {"frame": '{"type":'}},
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )
    assert not process.reader.is_alive()


def test_real_native_raw_before_later_block(fixture_module):
    process = worker(fixture_module)
    with pytest.raises(api().WorkerDeadline) as caught:
        process.call(
            {"operation": "native_block"},
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )
    values = [p["value"]["raw"] for p in caught.value.progress]
    assert any(
        v.get("counters", {}).get("shared_mb", {}).get("raw_filetime", 0) > 0
        for v in values
    )
    assert not process.reader.is_alive()


def test_child_protocol_inprocess_trusted_fixture(fixture_module, monkeypatch):
    """Exercise child EOF/close without kill so coverage sees protocol control flow."""
    module = api()
    incoming = io.BytesIO(
        module.encode(
            {"gate": True, "handler": f"{fixture_module}:Handler", "config": {}}
        )
        + module.encode({"seq": 1, "payload": {"operation": "echo"}})
    )
    outgoing = io.BytesIO()
    monkeypatch.setattr(module.sys, "stdin", type("Input", (), {"buffer": incoming})())
    monkeypatch.setattr(
        module.sys, "stdout", type("Output", (), {"buffer": outgoing})()
    )
    module._child()
    frames = outgoing.getvalue().splitlines(keepends=True)
    assert module.decode(frames[0])["type"] == "ready"
    assert module.decode(frames[1])["value"]["sensor"] == "simulated"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"operation": "echo", "command": "bad"},
        {"operation": 3},
        {"operation": "echo", "arguments": float("inf")},
    ],
)
def test_invalid_input_closes(fixture_module, payload):
    process = worker(fixture_module)
    with pytest.raises(api().WorkerFailure):
        process.call(payload, deadline_ns=time.perf_counter_ns() + 2_000_000_000)
    assert not process.reader.is_alive()


def test_startup_block_bounded(fixture_module):
    path = Path(fixture_module)
    path.write_text(
        path.read_text().replace(
            "self.config = config", "time.sleep(60)\n        self.config = config"
        )
    )
    start = time.perf_counter_ns()
    with pytest.raises(api().WorkerDeadline):
        api().OwnedProcess({}, f"{fixture_module}:Handler", startup_timeout_s=0.3)
    assert time.perf_counter_ns() - start < 700_000_000


def test_same_worker_prepared_commit_and_blocked_persistence(fixture_module, tmp_path):
    module = api()
    prepared, committed = tmp_path / "prepared.json", tmp_path / "committed.json"
    process = worker(fixture_module)
    pid = process.pid
    try:
        result = process.call(
            {"operation": "prepare", "arguments": {"prepared": str(prepared)}},
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )
        assert prepared.read_text() == '{"owned":true}'
        assert result["progress"][0]["value"]["prepared"] == str(prepared)
        process.call(
            {
                "operation": "commit",
                "arguments": {"prepared": str(prepared), "committed": str(committed)},
            },
            deadline_ns=time.perf_counter_ns() + 2_000_000_000,
        )
        assert committed.read_text() == '{"owned":true}'
        assert process.pid == pid
        deadline = time.perf_counter_ns() + 800_000_000
        with pytest.raises(module.WorkerDeadline) as caught:
            process.call(
                {
                    "operation": "persist_block",
                    "arguments": {"prepared": str(prepared)},
                },
                deadline_ns=deadline,
            )
        assert caught.value.progress[0]["value"]["prepared"] == str(prepared)
        assert prepared.exists()
        assert not process.reader.is_alive()
    finally:
        process.close()


def test_kill_on_job_close_fallback_wakes_owned_reader(fixture_module, monkeypatch):
    module = api()
    process = worker(fixture_module)

    def fail_terminate():
        raise OSError("simulated TerminateJobObject failure")

    monkeypatch.setattr(process.job, "terminate", fail_terminate)
    with pytest.raises(module.WorkerDeadline) as caught:
        process.call(
            {"operation": "block"}, deadline_ns=time.perf_counter_ns() + 800_000_000
        )
    assert "cleanup_error" in caught.value.evidence
    descendant = caught.value.progress[0]["value"]["descendant_pid"]
    assert not module.process_alive(descendant)
    assert process.close_evidence["reader_joined"] is True
    assert not process.reader.is_alive()
    process.close()


def test_enumeration_failure_still_terminates_and_joins(fixture_module, monkeypatch):
    module = api()
    process = worker(fixture_module)

    def fail_enumeration():
        raise ValueError("simulated member enumeration failure")

    monkeypatch.setattr(process.job, "member_handles", fail_enumeration)
    with pytest.raises(module.WorkerFailure, match="enumeration failure"):
        process.close(graceful=False)
    assert process.close_evidence["job_empty"] is True
    assert not process.reader.is_alive()
    assert not module.process_alive(process.pid)


@pytest.mark.parametrize("recording_fault", [False, True])
def test_firstcause_startup_keeps_original_after_native_cleanup_fault(
    fixture_module, monkeypatch, recording_fault
):
    """Controlled startup/TerminateJobObject faults; actual owned Job and reader."""
    import benchmark_coordinator as coordinator

    module = api()
    primary = module.WorkerFailure("controlled_startup_firstcause")
    original_receive = module.OwnedProcess._receive
    retained = []

    def receive(owned, deadline):
        ready = original_receive(owned, deadline)
        assert ready == {"type": "ready", "pid": owned.pid}
        assert owned.ownership["job_member"] is True
        assert owned.reader.is_alive()
        retained.append(owned)

        def terminate_fault():
            raise OSError("controlled_owned_job_termination_fault")

        monkeypatch.setattr(owned.job, "terminate", terminate_fault)
        raise primary

    def recording_error(error):
        raise RuntimeError("controlled_secondary_recording_fault")

    monkeypatch.setattr(module.OwnedProcess, "_receive", receive)
    if recording_fault:
        monkeypatch.setattr(coordinator, "cleanup_error_record", recording_error)
    try:
        with pytest.raises(BaseException) as caught:
            module.OwnedProcess({}, f"{fixture_module}:Handler")
        assert caught.value is primary
        assert type(caught.value) is module.WorkerFailure
        assert primary._owned_cleanup_resource is retained[0]
        assert primary.evidence["cleanup_error"]["type"] == "WorkerFailure"
        assert retained[0].close_evidence["resources_returned"] is False
        assert retained[0].close_evidence["disposition"] == "UNKNOWN_QUARANTINED"
    finally:
        for owned in retained:
            owned.close(graceful=False)
            assert owned.process.poll() is not None
            assert not owned.reader.is_alive()


def test_firstcause_successful_startup_does_not_swallow_native_cleanup_fault(
    fixture_module, monkeypatch
):
    """No primary error: a controlled fault on the real Job remains a failure."""
    module = api()
    owned = worker(fixture_module)

    def terminate_fault():
        raise OSError("controlled_cleanup_without_primary")

    monkeypatch.setattr(owned.job, "terminate", terminate_fault)
    try:
        with pytest.raises(
            module.WorkerFailure, match="controlled_cleanup_without_primary"
        ):
            owned.close(graceful=False)
        assert owned.close_evidence["resources_returned"] is False
    finally:
        owned.close(graceful=False)
        assert owned.process.poll() is not None
        assert not owned.reader.is_alive()


def test_firstcause_startup_reference_recording_cannot_replace_primary(
    fixture_module, monkeypatch
):
    """Controlled reference recording fault after actual startup and Job cleanup."""
    module = api()

    class PrimaryFailure(module.WorkerFailure):
        @property
        def _owned_cleanup_resource(self):
            return None

        @_owned_cleanup_resource.setter
        def _owned_cleanup_resource(self, owned):
            raise OSError("controlled_secondary_reference_recording_fault")

    primary = PrimaryFailure("controlled_startup_firstcause")
    owned = module.OwnedProcess.__new__(module.OwnedProcess)
    original_receive = module.OwnedProcess._receive

    def receive(actual, deadline):
        ready = original_receive(actual, deadline)
        assert ready == {"type": "ready", "pid": actual.pid}
        assert actual is owned and actual.ownership["job_member"] is True
        assert actual.reader.is_alive()

        def terminate_fault():
            raise OSError("controlled_owned_job_termination_fault")

        monkeypatch.setattr(actual.job, "terminate", terminate_fault)
        raise primary

    monkeypatch.setattr(module.OwnedProcess, "_receive", receive)
    try:
        with pytest.raises(BaseException) as caught:
            owned.__init__({}, f"{fixture_module}:Handler")
        assert caught.value is primary
        assert type(caught.value) is PrimaryFailure
        assert primary.evidence["cleanup_error"]["type"] == "WorkerFailure"
        assert owned.close_evidence["resources_returned"] is False
        # The original traceback retains the real owned object when an explicit
        # exception attribute cannot be written; no resource is declared returned.
        traceback = primary.__traceback__
        retained = False
        while traceback is not None:
            retained |= traceback.tb_frame.f_locals.get("self") is owned
            traceback = traceback.tb_next
        assert retained
    finally:
        owned.close(graceful=False)
        assert owned.process.poll() is not None
        assert not owned.reader.is_alive()
