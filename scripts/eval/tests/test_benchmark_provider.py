"""Contrato proxy y sonda Windows real de sólo lectura, sin inferencia."""

import copy
import json
import subprocess
import time
from pathlib import Path

import pytest
from benchmark_process import WorkerDeadline, process_alive
from benchmark_provider import IsolatedObservers, NativeProvider


def test_native_probe_real_persistent_cleanup():
    provider = IsolatedObservers(browser={})
    pid = provider.worker.pid
    try:
        first = provider.native_probe()
        second = provider.native_probe()
        assert first["status"] == "partial_native_probe"
        assert first["full_calibration"] is False
        assert first["windows"]["adapter_luid"] == second["windows"]["adapter_luid"]
        assert first["windows"]["query_filetime"] > 0
        assert set(first["windows"]["counters"]) == {"shared_mb", "dedicated_mb"}
        assert provider.worker.pid == pid
        assert provider.last_result["progress"]
        out = (
            Path(__file__).resolve().parents[3]
            / ".cache/dev-cycle/t09/isolated-provider-implementation/native-probe.json"
        )
        out.write_text(json.dumps(provider.last_result, indent=2), encoding="utf-8")
    finally:
        provider.close()
        provider.close()
    assert not process_alive(pid)
    assert not provider.worker.reader.is_alive()
    assert provider.worker.close_evidence["job_empty"] is True
    assert provider.worker.close_evidence["errors"] == []
    (out.parent / "native-cleanup.json").write_text(
        json.dumps(provider.worker.close_evidence, indent=2), encoding="utf-8"
    )


def test_proxy_original_deadline_and_partial_failure():
    provider = IsolatedObservers(browser={})
    with pytest.raises(WorkerDeadline) as caught:
        provider.sample(deadline_ns=time.perf_counter_ns() - 1)
    assert provider.last_raw["status"] == "incomplete_invalid"
    assert caught.value.partial_raw is provider.last_raw


def test_native_operations_closed_and_resources_reused(monkeypatch):
    import benchmark_observers
    import benchmark_windows

    class SimulatedWindows:
        instance = "simulated_counter"
        query = True

        def __init__(self, name):
            assert name == "NVIDIA GeForce RTX 5070"

        def sample(self):
            value = {"instance": self.instance, "sensor": "simulated"}
            self.progress_callback(value)
            return value

        def close(self):
            self.query = None

    class SimulatedObservers:
        def __init__(self, windows, **kwargs):
            self.windows = windows

        def nvidia(self):
            return {"sensor": "simulated_nvml"}

        def sample(self):
            value = {"sensor": "simulated", "context": self.observation_context}
            self.progress_callback(value)
            return value

    monkeypatch.setattr(benchmark_windows, "WindowsGpuMemory", SimulatedWindows)
    monkeypatch.setattr(benchmark_observers, "Observers", SimulatedObservers)
    with pytest.raises(ValueError, match="config"):
        NativeProvider({"command": "bad"})
    handler = NativeProvider({"browser": {}})
    try:
        with pytest.raises(ValueError, match="provider_operation_invalid"):
            handler({"operation": "arbitrary_command"}, lambda _: None)
        with pytest.raises(ValueError, match="provider_arguments_invalid"):
            handler(
                {"operation": "native_probe", "arguments": {"command": "anything"}},
                lambda _: None,
            )
        with pytest.raises(ValueError, match="payload"):
            handler({"operation": "sample", "command": "bad"}, lambda _: None)
        assert (
            handler({"operation": "nvidia"}, lambda _: None)["sensor"]
            == "simulated_nvml"
        )
        assert handler(
            {
                "operation": "sample",
                "arguments": {"observation_context": {"id": "simulation"}},
            },
            lambda _: None,
        )["context"] == {"id": "simulation"}
        values = []
        value = handler({"operation": "native_probe"}, values.append)
        assert values[0]["source"] == "windows_raw"
        assert value["windows"]["instance"] == handler.windows.instance
    finally:
        handler.close()
    assert handler.windows.query is None


def test_observer_progress_precedes_next_sensor_and_retains_partial():
    from benchmark_observers import Observers
    from benchmark_windows import IncompleteWindowsSample

    events, snapshots = [], []

    def progress(value):
        snapshots.append(copy.deepcopy(value))
        events.append("progress")

    class SimulatedWindows:
        def sample(self):
            assert snapshots[-1]["nvml"]["used_mb"] == 1
            events.append("windows")
            raise IncompleteWindowsSample(
                "simulated metadata failure",
                {"sensor": "simulated_partial", "shared_mb": 2},
            )

        def browser_heartbeat(self, browser):
            assert snapshots[-1]["wsl"]["mem_available_mb"] == 1
            events.append("browser")
            return {"sensor": "simulated_browser"}

    def execute(args, **kwargs):
        if args[0] == "nvidia-smi":
            events.append("nvml")
            return subprocess.CompletedProcess(
                args, 0, "GPU-simulated, NVIDIA GeForce RTX 5070, 10, 1, 9"
            )
        assert snapshots[-1]["windows"]["shared_mb"] == 2
        events.append("wsl_simulated")
        return subprocess.CompletedProcess(args, 0, "MemAvailable: 1024 kB")

    observer = Observers(
        SimulatedWindows(), browser={}, execute=execute, progress_callback=progress
    )
    value = observer.sample()
    assert events == [
        "progress",
        "nvml",
        "progress",
        "windows",
        "progress",
        "wsl_simulated",
        "progress",
        "browser",
        "progress",
    ]
    assert value["errors"] == ["windows_unavailable"]
    assert snapshots[2]["windows"]["sensor"] == "simulated_partial"
    assert set(value["operations"]) == {"nvml", "windows", "wsl", "browser"}


def test_proxy_simulated_context_nvidia_reuses_pid():
    # Own fixture directory, bypass repository-wide tmp_path outside this unit.
    import uuid

    path = (
        Path(__file__).resolve().parents[3]
        / ".cache/dev-cycle/t09/isolated-provider-implementation/fixtures"
        / uuid.uuid4().hex
    )
    path.mkdir(parents=True)
    handler = path / "proxy_fixture.py"
    handler.write_text("""class Handler:
    def __init__(self, config):
        self.count = 0
    def __call__(self, payload, emit):
        self.count += 1
        emit({"sensor":"simulated", "arguments":payload["arguments"]})
        return {"operation":payload["operation"], "arguments":payload["arguments"], "count":self.count, "sensor":"simulated"}
    def close(self):
        pass
""")
    observer = IsolatedObservers(browser={}, trusted_handler=f"{handler}:Handler")
    try:
        observer.observation_context = {"simulation_id": "test"}
        observer.observation_method = "simulation_only"
        first = observer.sample()
        pid = observer.worker.pid
        second = observer.nvidia()
        assert first["arguments"]["observation_context"] == {"simulation_id": "test"}
        assert second["arguments"]["observation_method"] == "simulation_only"
        assert second["count"] == 2
        assert observer.worker.pid == pid
    finally:
        observer.close()
