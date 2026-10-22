"""Regresiones de transición: procesos CPU reales y escrituras tardías.

Los sensores de los episodios son sintéticos y no acreditan GPU.
"""

import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from test_benchmark_reacquisition import recovery as recovery_fixture
from test_benchmark_reacquisition import sample, v2


@pytest.fixture
def recovery(harness_module, monkeypatch, tmp_path):
    return recovery_fixture.__wrapped__(harness_module, monkeypatch, tmp_path)


@pytest.fixture
def tmp_path():
    path = (
        Path(__file__).resolve().parents[3]
        / ".cache/dev-cycle/t09/transition-fix2/test-temporaries"
        / uuid4().hex
    )
    path.mkdir(parents=True)
    return path


def test_blocked_source_process_must_be_interrupted_within_episode(recovery):
    c = recovery
    children = []

    def blocked_source():
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(2.2)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        children.append(child)
        child.wait(timeout=5)
        c.sensors.last_raw = v2(sample(1))
        return c.sensors.last_raw

    c.sensors.sample = blocked_source
    started = time.perf_counter()
    try:
        try:
            c.module.acquire_sample(c.sensors, c.path)
        except ValueError:
            pass
        elapsed = time.perf_counter() - started
        print({"elapsed_s": elapsed, "pids": [p.pid for p in children]})
        assert elapsed < 2.1, (
            "blocked source was not interrupted at the original deadline"
        )
        assert not c.path.exists(), "blocked episode published accepted data"
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)


@pytest.mark.parametrize("delay_stage", ["validation", "accepted", "continuity"])
def test_real_late_work_cannot_publish_or_advance(recovery, monkeypatch, delay_stage):
    import benchmark_runner

    c = recovery
    c.values[:] = [v2(sample(1))]
    c.sensors.continuity_path = c.path.parent / "continuity.ndjson"
    append = benchmark_runner.append_record
    validate = c.module.validate_episode

    def delayed_append(path, value):
        if (delay_stage == "accepted" and path == c.path) or (
            delay_stage == "continuity" and path == c.sensors.continuity_path
        ):
            time.sleep(2.2)
        return append(path, value)

    def delayed_validation(*args, **kwargs):
        if delay_stage == "validation":
            time.sleep(2.2)
        return validate(*args, **kwargs)

    monkeypatch.setattr(benchmark_runner, "append_record", delayed_append)
    monkeypatch.setattr(c.module, "validate_episode", delayed_validation)
    started = time.perf_counter()
    error = None
    try:
        c.module.acquire_sample(c.sensors, c.path)
    except ValueError as caught:
        error = str(caught)
    print(
        {
            "stage": delay_stage,
            "elapsed_s": time.perf_counter() - started,
            "error": error,
        }
    )
    assert error is not None, "late completed work was accepted using the earlier clock"
    assert not hasattr(c.sensors, "previous_episode"), "late work advanced continuity"


def test_native_pdh_raw_survives_later_clock_failure(harness_module, monkeypatch):
    """Recursos PDH/DXGI reales; fallo inducido después de leer los contadores."""
    module = harness_module("benchmark_windows")
    collector = module.WindowsGpuMemory("NVIDIA GeForce RTX 5070")
    original = module.timezone_snapshot
    calls = []

    def changed_zone():
        value = original()
        calls.append(value)
        if len(calls) > 1:
            value = dict(value)
            value["bias_minutes"] += 1
        return value

    monkeypatch.setattr(module, "timezone_snapshot", changed_zone)
    try:
        with pytest.raises(ValueError, match="pdh_filetime_clock_changed") as caught:
            collector.sample()
        partial = getattr(caught.value, "partial_sample", None)
        assert partial is not None, (
            "actual returned PDH RAW was discarded after clock failure"
        )
        assert partial["collect_return"] == 0
        assert set(partial["counters"]) == {"shared_mb", "dedicated_mb"}
        assert all("raw_value" in counter for counter in partial["counters"].values())
        assert partial["status"] == "incomplete_invalid"
        print({"native_partial": partial})
        from types import SimpleNamespace

        from benchmark_observers import Observers

        calls.clear()
        observer = Observers(
            collector,
            browser={},
            execute=lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="MemAvailable: 100 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB",
            ),
        )
        monkeypatch.setattr(observer, "nvidia", dict)
        monkeypatch.setattr(collector, "browser_heartbeat", lambda _: {})
        raw = observer.sample()
        assert "windows_unavailable" in raw["errors"]
        assert raw["windows"]["status"] == "incomplete_invalid"
        assert set(raw["windows"]["counters"]) == {"shared_mb", "dedicated_mb"}
    finally:
        collector.close()
        assert collector.query is None


def test_native_raw_survives_counter_metadata_failure(harness_module, monkeypatch):
    module = harness_module("benchmark_windows")
    collector = module.WindowsGpuMemory("NVIDIA GeForce RTX 5070")
    monkeypatch.setattr(collector.pdh, "PdhGetCounterInfoW", lambda *args: 1)
    try:
        with pytest.raises(ValueError, match="pdh_metadata_unavailable") as caught:
            collector.sample()
        partial = caught.value.partial_sample
        counter = partial["counters"].get("shared_mb")
        assert counter is not None, (
            "returned PDH RAW disappeared on subsequent metadata failure"
        )
        assert counter["raw_return"] == 0
        assert counter["raw_value"] >= 0
        assert counter["info_return"] is None
        assert partial["status"] == "incomplete_invalid"
    finally:
        collector.close()


def test_real_three_second_preparation_preserves_continuity(
    recovery, harness_module, monkeypatch
):
    import threading
    from types import SimpleNamespace

    from benchmark_plan import configurations
    from test_benchmark_reacquisition import sealed_calibration

    c = recovery
    root, observation, plan = sealed_calibration(c)
    cli = harness_module("benchmark")
    plan["configs"] = configurations()
    plan["timeouts"] = {"observation_s": 3}
    plan["observer_policy"] = {"interval_s": 0}
    folder = root / "session"
    folder.mkdir()
    (root / "data/tmp").mkdir(parents=True)
    clock = SimpleNamespace(t=31.1, wall=0, last_raw=None)
    calls = []

    def sleep(seconds):
        clock.wall += seconds
        threading.Event().wait(0.001)

    monkeypatch.setattr(
        c.module, "time", SimpleNamespace(monotonic=lambda: clock.wall, sleep=sleep)
    )
    monkeypatch.setattr(c.module, "utc_now", lambda: sample(clock.t + 1)["timestamp"])
    monkeypatch.setattr(
        c.module,
        "episode_clock",
        lambda: (
            max(op["finished_utc"] for op in clock.last_raw["operations"].values()),
            max(
                op["finished_monotonic_ns"]
                for op in clock.last_raw["operations"].values()
            ),
        ),
    )
    original_baseline = cli.observed_baseline
    monkeypatch.setattr(
        cli,
        "observed_baseline",
        lambda sensors, path: original_baseline(
            sensors, path, interval=0, sleep=lambda _: None
        ),
    )
    monkeypatch.setattr(
        cli,
        "run_request",
        lambda plan, run, root: {"job_id": run["job_id"], "task": "music.song"},
    )

    class Sensors:
        def nvidia(self):
            return {"name": "NVIDIA GeForce RTX 5070", "used_mb": 1200}

        def sample(self):
            clock.t += 0.05
            value = sample(clock.t)
            clock.last_raw = value
            value["acquisition_context"] = c.module.acquisition_context(
                self.observation_context, "wddm_auto_v2"
            )
            return value

    class Api:
        def request(self, method, path, body=None):
            calls.append((method, path, body))
            if path == "/v1/health":
                return {"state": "idle", "job_id": None, "loaded": None}
            if path == "/v1/jobs":
                return {"job_id": body["job_id"]}
            return {}

        def events(self, job, *args, **kwargs):
            return [{"seq": 1, "job_id": job, "type": "error", "data": {}}]

    class Backend:
        def create(self, plan, config, storage, owner, port, token):
            started = time.perf_counter()
            time.sleep(3)
            elapsed = time.perf_counter() - started
            assert elapsed >= 3
            print({"create_elapsed_s": elapsed, "backend": "synthetic"})
            clock.t += 3
            resource = (
                "/models"
                if storage == "bind"
                else f"/studio/.cache/benchmark/{plan['session_id']}/models"
            )
            cli.exclusive_json(
                root / "data/tmp" / f"t09-storage-{config['group_id']}.json",
                {
                    "resource_root": resource,
                    "destination_lock_sha256": plan["lock_sha256"],
                    "source_lock_sha256": plan["lock_sha256"],
                    "copy_s": 0,
                },
            )
            return {"port": port, "container_id": "CPU-own-" + config["group_id"]}

        def start(self, receipt):
            pass

        def inspect(self, container):
            return {"State": {"Running": True}}

        def verify_image_sources(self, receipt, plan):
            pass

        def cleanup(self, receipt, api):
            calls.append(("cleanup", receipt["container_id"], None))
            return {"removed": True}

    restored = []
    ollama = SimpleNamespace(
        snapshot=lambda: {"models": []},
        discharge=lambda _: None,
        restore=lambda state: restored.append(state) or {},
    )
    prerequisites = {
        "observation": observation,
        "browser": observation["context"]["browser_identity"],
        "exclusive_gpu_authorized": True,
    }
    kwargs = {
        "root": root,
        "backend": Backend(),
        "observer_factory": lambda _: Sensors(),
        "api_factory": lambda *args: Api(),
        "ollama": ollama,
        "token": "CPU",
    }
    try:
        rows = cli.run_session(plan, folder, prerequisites, **kwargs)
    finally:
        assert len(restored) == 1
        assert not (root / ".cache/dev-cycle/t09/gpu.lock").exists()
        assert any(method == "cleanup" for method, _, _ in calls)
    assert len(rows) == 160 and all(row["status"] == "error" for row in rows)
    submitted = [
        body["job_id"]
        for method, path, body in calls
        if method == "POST" and path == "/v1/jobs"
    ]
    assert len(submitted) == len(set(submitted)) == 160
    assert len([method for method, _, _ in calls if method == "cleanup"]) == 40
    assert len(restored) == 1
    assert not (root / ".cache/dev-cycle/t09/gpu.lock").exists()
