"""Fakes explícitos CPU; ninguna acreditación GPU real."""

import copy
import json
from datetime import datetime, timedelta, timezone

import pytest

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)
BROWSER = {"pid": 4, "hwnd": 9, "creation_time": 123, "executable": "msedge.exe"}
CONTEXT = {
    "session_id": "synthetic-session",
    "plan_sha256": "a" * 64,
    "source_hashes": {"synthetic.py": "b" * 64},
    "lock_sha256": "c" * 64,
    "image_id": "sha256:" + "d" * 64,
    "driver_version": "synthetic",
    "windows_build": "synthetic",
    "nvml_uuid": "GPU-synthetic",
    "adapter_luid": [0, 4660],
    "browser_identity": BROWSER,
}
INSTANCE = "luid_0x00000000_0x00001234_phys_0"
UTC_ZONE = {
    "id": 0,
    "bias_minutes": 0,
    "standard_bias_minutes": 0,
    "daylight_bias_minutes": 0,
    "standard_name": "CPU UTC",
    "daylight_name": "CPU UTC",
    "standard_date": [0] * 8,
    "daylight_date": [0] * 8,
}


def utc(second):
    return (NOW + timedelta(seconds=second)).isoformat()


def bracket(second):
    return {
        "started_utc": utc(second),
        "finished_utc": utc(second + 0.01),
        "started_monotonic_ns": int((second + 1000) * 1e9),
        "finished_monotonic_ns": int((second + 1000.01) * 1e9),
    }


def sample(second, used=1200, *, context=None):
    from benchmark_observation import acquisition_context

    counters = {}
    for name, amount in (("shared_mb", 40), ("dedicated_mb", used)):
        counters[name] = {
            "counter_type": 65792,
            "raw_unit": "bytes",
            "default_scale": -6,
            "scale": 0,
            "raw_counter_type": 0x10100,
            "info_counter_type": 0x10100,
            "info_return": 0,
            "format_flags": 0x1200,
            "conversion": "bytes/2**20",
            "raw_cstatus": 0,
            "raw_return": 0,
            "format_return": 0,
            "formatted_cstatus": 0,
            "raw_value": amount * 2**20,
            "formatted_value": amount * 2**20,
            "raw_filetime": int((NOW.timestamp() + 11644473600 + second) * 1e7),
            "raw_utc_filetime": int((NOW.timestamp() + 11644473600 + second) * 1e7),
            "path": f"\\GPU Adapter Memory({INSTANCE})\\{name}",
        }
    return {
        "acquisition_context": acquisition_context(
            CONTEXT if context is None else context
        ),
        "timestamp": utc(second),
        "monotonic_ns": int((second + 1000) * 1e9),
        "errors": [],
        "operations": {
            k: bracket(second) for k in ("nvml", "windows", "browser", "wsl")
        },
        "nvml": {
            "driver_version": "synthetic",
            "uuid": "GPU-synthetic",
            "name": "NVIDIA GeForce RTX 5070",
            "total_mb": 12227,
            "used_mb": used,
            "free_mb": 12227 - used,
        },
        "windows": {
            "windows_build": "synthetic",
            "scope": "adapter_aggregate",
            "gpu_mapping_status": "resolved",
            "instance": INSTANCE,
            "adapter_luid": [0, 4660],
            "dxgi_inventory": [
                {
                    "vendor_id": 0x10DE,
                    "description": "NVIDIA GeForce RTX 5070",
                    "luid_high": 0,
                    "luid_low": 4660,
                }
            ],
            "shared_mb": 40,
            "dedicated_mb": used,
            "query_filetime": int((NOW.timestamp() + 11644473600 + second) * 1e7),
            "query_utc_filetime": int((NOW.timestamp() + 11644473600 + second) * 1e7),
            "filetime_clock": {
                "basis": "local",
                "conversion": "LocalFileTimeToFileTime",
                "timezone_before": copy.deepcopy(UTC_ZONE),
                "timezone_after": copy.deepcopy(UTC_ZONE),
            },
            "collect_return": 0,
            "counters": counters,
            "collection": bracket(second),
        },
        "browser": {
            **BROWSER,
            "visible": True,
            "iconic": False,
            "rect": [0, 0, 100, 100],
        },
        "wsl": {"mem_available_mb": 10000, "swap_used_mb": 0},
    }


def validator(module, name):
    function = getattr(module, name, None)
    assert callable(function), f"Falta {name} con validación sustantiva"
    return function


def test_policy_is_versioned_sealed_and_has_fixed_thresholds(harness_module):
    module = harness_module("benchmark_observation")
    policy = validator(module, "observation_policy")()
    assert policy["version"] == "wddm_auto_v1"
    assert (
        policy["samples"],
        policy["dedicated_abs_mb"],
        policy["dedicated_rel"],
        policy["response_mb"],
        policy["freshness_s"],
    ) == (10, 128, 0.02, 512, 900)
    assert module.policy_hash(policy) == module.policy_hash(module.observation_policy())
    policy["response_mb"] = 0
    with pytest.raises(ValueError, match="policy"):
        module.validate_policy(policy)


def test_identical_values_with_fresh_timestamps_are_valid(harness_module):
    module = harness_module("benchmark_observation")
    validate = validator(module, "validate_samples")
    assert (
        validate(
            [sample(i) for i in range(10)],
            CONTEXT,
            now=NOW + timedelta(seconds=10),
            idle=True,
        )["shared_validation_level"]
        == "provider_verified"
    )


@pytest.mark.parametrize(
    "case",
    [
        "status",
        "nan",
        "unit",
        "future",
        "replay",
        "mapping",
        "browser_reuse",
        "hidden",
        "iconic",
        "rect",
        "skew",
        "query_duration",
        "raw_time",
        "nvml_identity",
        "idle",
    ],
)
def test_invalid_samples_are_rejected(harness_module, case):
    module = harness_module("benchmark_observation")
    validate = validator(module, "validate_samples")
    samples = [sample(i) for i in range(10)]
    bad = samples[-1]
    if case == "status":
        bad["windows"]["counters"]["shared_mb"]["raw_cstatus"] = 7
    elif case == "nan":
        bad["windows"]["shared_mb"] = float("nan")
    elif case == "unit":
        bad["windows"]["counters"]["shared_mb"]["raw_unit"] = "MiB"
    elif case == "future":
        bad["operations"]["windows"]["finished_utc"] = utc(100)
    elif case == "replay":
        samples[-1] = copy.deepcopy(samples[-2])
    elif case == "mapping":
        bad["windows"]["adapter_luid"] = [0, 999]
    elif case == "browser_reuse":
        bad["browser"]["creation_time"] = 124
    elif case == "hidden":
        bad["browser"]["visible"] = False
    elif case == "iconic":
        bad["browser"]["iconic"] = True
    elif case == "rect":
        bad["browser"]["rect"] = [0, 0, 0, 100]
    elif case == "skew":
        bad["operations"]["nvml"] = bracket(6)
    elif case == "query_duration":
        bad["windows"]["collection"]["finished_monotonic_ns"] += int(3e9)
    elif case == "raw_time":
        bad["windows"]["counters"]["shared_mb"]["raw_filetime"] = 1
    elif case == "nvml_identity":
        bad["nvml"]["uuid"] = "GPU-other"
    elif case == "idle":
        bad["nvml"]["used_mb"] = 1700
    with pytest.raises(ValueError):
        validate(samples, CONTEXT, now=NOW + timedelta(seconds=10), idle=True)


def test_calibration_requires_real_phase_transition_and_response(harness_module):
    module = harness_module("benchmark_observation")
    validate = validator(module, "validate_calibration")
    phases = {
        "baseline": [sample(i) for i in range(10)],
        "loaded": [sample(i, 8000) for i in range(11, 21)],
        "unloaded": [sample(i) for i in range(22, 32)],
    }
    lifecycle = {
        "loaded": {
            "event": "load_finished",
            "observed_at": utc(10),
            "job_id": "pilot-job",
        },
        "unloaded": {
            "event": "health_unloaded",
            "observed_at": utc(21),
            "loaded": None,
        },
    }
    result = validate(phases, lifecycle, CONTEXT, now=NOW + timedelta(seconds=32))
    assert result["shared_independent_validation"] is False
    assert result["task_manager_contrast"] == "conflicting_historical"
    invalid = copy.deepcopy(phases)
    invalid["loaded"] = [sample(i, 1200) for i in range(11, 21)]
    with pytest.raises(ValueError, match="response"):
        validate(invalid, lifecycle, CONTEXT, now=NOW + timedelta(seconds=32))
    lifecycle["loaded"]["observed_at"] = utc(15)
    with pytest.raises(ValueError, match="phase"):
        validate(phases, lifecycle, CONTEXT, now=NOW + timedelta(seconds=32))


def test_calibration_rejects_pause_and_dedicated_disagreement(harness_module):
    module = harness_module("benchmark_observation")
    validate = validator(module, "validate_calibration")
    phases = {
        "baseline": [sample(i) for i in range(10)],
        "loaded": [sample(i, 8000) for i in range(11, 21)],
        "unloaded": [sample(i) for i in range(22, 32)],
    }
    lifecycle = {
        "loaded": {
            "event": "load_finished",
            "observed_at": utc(10),
            "job_id": "pilot-job",
        },
        "unloaded": {
            "event": "health_unloaded",
            "observed_at": utc(21),
            "loaded": None,
        },
    }
    with pytest.raises(ValueError, match="expired"):
        validate(phases, lifecycle, CONTEXT, now=NOW + timedelta(seconds=1000))
    phases["loaded"][0]["nvml"]["used_mb"] = 7000
    with pytest.raises(ValueError, match="dedicated"):
        validate(phases, lifecycle, CONTEXT, now=NOW + timedelta(seconds=32))


def test_auto_prerequisite_rejects_shape_only_claim(harness_module):
    runner = harness_module("benchmark_runner")
    with pytest.raises(ValueError, match="auto"):
        runner.validate_prerequisites(
            {
                "observation": {"method": "wddm_auto_v1", "calibration_pass": True},
                "exclusive_gpu_authorized": True,
            }
        )


def test_observation_loss_stops_before_submission(harness_module, tmp_path):
    runner = harness_module("benchmark_runner")
    calls = []

    class Sensors:
        observation_context = CONTEXT

        def sample(self):
            return {"errors": ["windows_unavailable"]}

    class Api:
        def request(self, *args):
            calls.append(args)
            return {"job_id": "j"}

        def events(self, *args, **kwargs):
            return [{"seq": 1, "job_id": "j", "type": "error", "data": {}}]

    with pytest.raises(ValueError, match="observability"):
        runner.execute_run(
            {
                "observation_method": "wddm_auto_v1",
                "timeouts": {"observation_s": 1},
                "observer_policy": {"interval_s": 0},
            },
            {"job_id": "j"},
            Api(),
            Sensors(),
            tmp_path,
            {"job_id": "j"},
        )
    assert not calls and not (tmp_path / "submission-intent.json").exists()


def test_windows_pdh_records_raw_type_scale_time_and_noscale(harness_module):
    import ctypes
    from types import SimpleNamespace

    windows = harness_module("benchmark_windows")
    collector = windows.WindowsGpuMemory.__new__(windows.WindowsGpuMemory)
    collector.instance = INSTANCE
    collector.adapters = sample(0)["windows"]["dxgi_inventory"]
    collector.paths = {
        name: f"\\GPU Adapter Memory({INSTANCE})\\{name}"
        for name in ("shared_mb", "dedicated_mb")
    }
    collector.query = ctypes.c_void_p(9)
    collector.counters = {
        "shared_mb": ctypes.c_void_p(1),
        "dedicated_mb": ctypes.c_void_p(2),
    }

    def collect(query, out):
        out._obj.value = int(
            (datetime.now(timezone.utc).timestamp() + 11644473600) * 1e7
        )
        return 0

    def raw(counter, typeptr, out):
        typeptr._obj.value = 0x10100
        out._obj.CStatus = 0
        out._obj.FirstValue = 40 * 2**20
        tick = int((datetime.now(timezone.utc).timestamp() + 11644473600) * 1e7)
        out._obj.TimeStamp.dwLowDateTime = tick & 0xFFFFFFFF
        out._obj.TimeStamp.dwHighDateTime = tick >> 32
        return 0

    formats = []

    def formatted(counter, fmt, typeptr, out):
        formats.append(fmt)
        typeptr._obj.value = 0x10100 if typeptr is not None else 0
        out._obj.CStatus = 0
        out._obj.doubleValue = 40 * 2**20
        return 0

    def info(counter, explain, size, out):
        size._obj.value = 512
        if out is not None:
            data = ctypes.cast(out, ctypes.POINTER(windows.CounterInfo)).contents
            data.dwType = 0x10100
            data.lScale = 0
            data.lDefaultScale = -6
        return 0

    collector.pdh = SimpleNamespace(
        PdhCollectQueryData=lambda q: 0,
        PdhCollectQueryDataWithTime=collect,
        PdhGetRawCounterValue=raw,
        PdhGetFormattedCounterValue=formatted,
        PdhGetCounterInfoW=info,
    )
    result = collector.sample()
    assert result.get("query_filetime", 0) > 0, "Falta timestamp PDH nativo"
    assert formats == [0x1200, 0x1200]
    assert result["counters"]["shared_mb"]["raw_value"] == 40 * 2**20
    assert result["counters"]["shared_mb"]["default_scale"] == -6
    assert result["adapter_luid"] == [0, 4660]


def test_each_observer_query_has_its_own_bracket(harness_module):
    from types import SimpleNamespace

    module = harness_module("benchmark_observers")

    class Windows:
        def sample(self):
            return {"shared_mb": 1}

        def browser_heartbeat(self, browser):
            return {"visible": True}

    def execute(args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="GPU-x, NVIDIA GeForce RTX 5070, 12227, 1200, 11027"
            if args[0] == "nvidia-smi"
            else "MemAvailable: 1024 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB",
        )

    result = module.Observers(Windows(), browser={}, execute=execute).sample()
    assert set(result.get("operations", {})) == {"nvml", "windows", "wsl", "browser"}, (
        "Faltan brackets por llamada"
    )
    assert all(
        value["finished_monotonic_ns"] >= value["started_monotonic_ns"]
        for value in result["operations"].values()
    )


def test_parallel_observers_overlap_slow_wsl_and_windows(harness_module):
    import threading
    from types import SimpleNamespace

    module = harness_module("benchmark_observers")
    barrier = threading.Barrier(2)

    class Windows:
        def sample(self):
            barrier.wait(timeout=0.5)
            return {"shared_mb": 1}

        def browser_heartbeat(self, browser):
            return {"visible": True}

    def execute(args, **kwargs):
        if args[0] == "nvidia-smi":
            return SimpleNamespace(
                returncode=0,
                stdout="GPU-x, NVIDIA GeForce RTX 5070, 12227, 1200, 11027",
            )
        barrier.wait(timeout=0.5)
        return SimpleNamespace(
            returncode=0,
            stdout="MemAvailable: 1024 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB",
        )

    result = module.Observers(
        Windows(), browser={}, execute=execute, parallel_operations=True
    ).sample()
    assert result["errors"] == []
    assert set(result["operations"]) == {"nvml", "windows", "wsl", "browser"}


def test_observer_anchors_sample_to_first_query_when_startup_is_slow(
    harness_module, monkeypatch
):
    """La marca final debe representar el inicio de la primera consulta real."""
    from types import SimpleNamespace

    module = harness_module("benchmark_observers")
    base = "2026-10-10T13:20:00.0000000+00:00"
    utc_values = iter(
        [
            base,
            "2026-10-10T13:20:00.2500000+00:00",
            "2026-10-10T13:20:00.2600000+00:00",
            "2026-10-10T13:20:00.2700000+00:00",
            "2026-10-10T13:20:00.2800000+00:00",
            "2026-10-10T13:20:00.2900000+00:00",
            "2026-10-10T13:20:00.3000000+00:00",
            "2026-10-10T13:20:00.3100000+00:00",
            "2026-10-10T13:20:00.3200000+00:00",
        ]
    )
    mono_values = iter(
        [
            1_000_000_000,
            1_250_000_000,
            1_260_000_000,
            1_270_000_000,
            1_280_000_000,
            1_290_000_000,
            1_300_000_000,
            1_310_000_000,
            1_320_000_000,
        ]
    )
    monkeypatch.setattr(module, "utc_now", lambda: next(utc_values))
    monkeypatch.setattr(module.time, "perf_counter_ns", lambda: next(mono_values))

    class Windows:
        def sample(self):
            return {"shared_mb": 1}

        def browser_heartbeat(self, browser):
            return {"visible": True}

    def execute(args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "GPU-x, NVIDIA GeForce RTX 5070, 12227, 1200, 11027"
                if args[0] == "nvidia-smi"
                else "MemAvailable: 1024 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB"
            ),
        )

    value = module.Observers(Windows(), browser={}, execute=execute).sample()
    assert value["timestamp"] == "2026-10-10T13:20:00.2500000+00:00"
    assert value["monotonic_ns"] == 1_250_000_000


def test_browser_reuse_minimization_and_empty_rect_are_rejected_natively(
    harness_module, monkeypatch
):
    import ctypes
    from types import SimpleNamespace

    windows = harness_module("benchmark_windows")

    class Function:
        def __init__(self, operation):
            self.operation = operation

        def __call__(self, *args):
            return self.operation(*args)

    state = {"creation": 123, "iconic": 0, "rect": [0, 0, 100, 100]}

    def pid(hwnd, out):
        out._obj.value = 4
        return 1

    def image(handle, flags, out, size):
        out.value = "C:\\private\\msedge.exe"
        return 1

    def times(handle, created, *args):
        created._obj.dwLowDateTime = state["creation"]
        return 1

    def rect(hwnd, out):
        out._obj.left, out._obj.top, out._obj.right, out._obj.bottom = state["rect"]
        return 1

    user = SimpleNamespace(
        **{
            k: Function(v)
            for k, v in {
                "IsWindow": lambda h: 1,
                "IsWindowVisible": lambda h: 1,
                "IsIconic": lambda h: state["iconic"],
                "GetWindowRect": rect,
                "GetWindowThreadProcessId": pid,
            }.items()
        }
    )
    kernel = SimpleNamespace(
        **{
            k: Function(v)
            for k, v in {
                "OpenProcess": lambda *a: 1,
                "QueryFullProcessImageNameW": image,
                "GetProcessTimes": times,
                "CloseHandle": lambda h: None,
            }.items()
        }
    )
    monkeypatch.setattr(
        ctypes, "WinDLL", lambda name: user if name == "user32" else kernel
    )
    result = windows.WindowsGpuMemory.browser_heartbeat(BROWSER)
    assert (
        result.get("creation_time") == 123
        and result.get("iconic") is False
        and result.get("rect") == [0, 0, 100, 100]
    ), "Falta heartbeat de identidad persistente"
    state["creation"] = 124
    assert not windows.WindowsGpuMemory.browser_heartbeat(BROWSER)["visible"]
    state["creation"] = 123
    state["iconic"] = 1
    assert not windows.WindowsGpuMemory.browser_heartbeat(BROWSER)["visible"]
    state["iconic"] = 0
    state["rect"] = [0, 0, 0, 0]
    assert not windows.WindowsGpuMemory.browser_heartbeat(BROWSER)["visible"]


def test_auto_plan_seals_policy_without_changing_nominal_matrix(
    harness_module, tmp_path
):
    import inspect

    planner = harness_module("benchmark_plan")
    assert "observation_method" in inspect.signature(planner.build_plan).parameters, (
        "Falta política sellada antes del piloto"
    )
    (tmp_path / "models").mkdir()
    (tmp_path / "models/models.lock.json").write_text("{}")
    fixtures = {}
    for duration in planner.DURATIONS:
        path = tmp_path / f"{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "lyrics": "CPU",
                        "style": "test",
                        "language": "es",
                        "duration_s": duration,
                    },
                }
            )
        )
        fixtures[str(duration)] = {"path": path.name, "sha256": planner.file_hash(path)}
    plan = planner.build_plan(
        {"fixtures_by_duration": fixtures},
        image_id="sha256:synthetic",
        prerequisites_sha256=None,
        root=tmp_path,
        observation_method="wddm_auto_v1",
    )
    module = harness_module("benchmark_observation")
    assert plan["observation_policy_sha256"] == module.policy_hash()
    assert len(plan["runs"]) == 160 and plan["observation_method"] == "wddm_auto_v1"
    planner.verify_plan(plan, tmp_path)
    plan["observation_policy"]["response_mb"] = 0
    plan["plan_sha256"] = planner.digest(
        {k: v for k, v in plan.items() if k != "plan_sha256"}
    )
    with pytest.raises(ValueError, match="policy"):
        planner.verify_plan(plan, tmp_path)


def test_auto_report_publishes_confidence_and_never_zero_spill(harness_module):
    evidence = harness_module("benchmark_evidence")
    report = evidence.render_report(
        {
            "session_id": "synthetic",
            "runs": [],
            "configs": [],
            "observation_method": "wddm_auto_v1",
            "observation_policy_sha256": "a" * 64,
        },
        [],
    )
    assert (
        "provider_verified" in report
        and "shared_independent_validation=false" in report
        and "conflicting_historical" in report
    ), "Falta confianza limitada explícita"
    assert "no acredita ausencia causal" in report


def sealed_case(tmp_path, module):
    context = copy.deepcopy(CONTEXT)
    (tmp_path / "models").mkdir()
    lock = tmp_path / "models/models.lock.json"
    lock.write_text("{}")
    source = tmp_path / "synthetic.py"
    source.write_text("CPU fixture only")
    context["source_hashes"] = {"synthetic.py": module.file_hash(source)}
    context["lock_sha256"] = module.file_hash(lock)
    plan = {
        k: context[k]
        for k in (
            "session_id",
            "plan_sha256",
            "source_hashes",
            "image_id",
            "lock_sha256",
        )
    }
    plan.update(
        observation_method="wddm_auto_v1",
        observation_policy_sha256=module.policy_hash(),
    )

    def seal(name, value, ndjson=False):
        if ndjson:
            for item in value:
                item["acquisition_context"] = module.acquisition_context(context)
        elif name == "lifecycle.json":
            for item in value.values():
                item["acquisition_context"] = module.acquisition_context(context)
        else:
            value["acquisition_context"] = module.acquisition_context(context)
        path = tmp_path / name
        path.write_text(
            "\n".join(json.dumps(item) for item in value) + "\n"
            if ndjson
            else json.dumps(value)
        )
        return {
            "path": name,
            "sha256": module.file_hash(path),
            "bytes": path.stat().st_size,
        }

    phases = {
        k: [sample(i, 8000 if k == "loaded" else 1200) for i in indexes]
        for k, indexes in {
            "baseline": range(10),
            "loaded": range(11, 21),
            "unloaded": range(22, 32),
        }.items()
    }
    host = {
        k: context[k]
        for k in (
            "driver_version",
            "windows_build",
            "nvml_uuid",
            "adapter_luid",
            "browser_identity",
        )
    }
    loaded_proof = seal(
        "loaded-proof.json",
        {
            "response": {"loaded": {"model_id": "synthetic", "mode": "bf16"}},
            "started_utc": utc(10),
            "finished_utc": utc(10.01),
        },
    )
    unload_proof = seal(
        "unloaded-proof.json",
        {
            "response": {"loaded": None, "state": "idle"},
            "started_utc": utc(21),
            "finished_utc": utc(21.01),
        },
    )
    lifecycle = {
        "loaded": {
            "event": "health_loaded",
            "observed_at": utc(10.01),
            "job_id": "pilot-job",
            "proof": loaded_proof,
        },
        "unloaded": {
            "event": "health_unloaded",
            "observed_at": utc(21.01),
            "loaded": None,
            "proof": unload_proof,
        },
    }
    evidence = {k: seal(k + ".ndjson", v, True) for k, v in phases.items()}
    evidence.update(
        lifecycle=seal("lifecycle.json", lifecycle), host=seal("host.json", host)
    )
    obs = {
        "method": "wddm_auto_v1",
        "policy": module.observation_policy(),
        "policy_sha256": module.policy_hash(),
        "context": context,
        "evidence": evidence,
        "viewport": {
            "acquisition_context": module.acquisition_context(context),
            "url": "about:blank",
            "tab_id": "own",
            "browser_id": "own-browser",
            "visible": True,
            "observed_at": utc(0),
            "evidence": seal(
                "viewport.json",
                {
                    "url": "about:blank",
                    "visible": True,
                    "tab_id": "own",
                    "browser_id": "own-browser",
                    "observed_at": utc(0),
                },
            ),
        },
        "binding": "unproven",
    }
    return obs, plan


def test_original_receipt_validates_context_and_actual_seal(harness_module, tmp_path):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    result = module.validate_auto(
        obs, tmp_path, plan=plan, now=NOW + timedelta(seconds=32)
    )
    assert (
        result["shared_validation_level"] == "provider_verified"
        and result["context"] == obs["context"]
    )
    (tmp_path / "loaded.ndjson").write_text("[]")
    with pytest.raises(ValueError, match="seal"):
        module.validate_auto(obs, tmp_path, plan=plan, now=NOW + timedelta(seconds=32))


@pytest.mark.parametrize(
    "case",
    [
        "proof",
        "viewport",
        "host",
        "policy",
        "session",
        "source",
        "lock",
        "path",
        "pause",
    ],
)
def test_receipt_rejects_forged_replayed_or_mixed_originals(
    harness_module, tmp_path, case
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    if case == "proof":
        path = tmp_path / "loaded-proof.json"
        path.write_text(
            json.dumps(
                {
                    "response": {"loaded": None},
                    "started_utc": utc(10),
                    "finished_utc": utc(10.01),
                }
            )
        )
        lifecycle = json.loads((tmp_path / "lifecycle.json").read_text())
        lifecycle["loaded"]["proof"].update(
            sha256=module.file_hash(path), bytes=path.stat().st_size
        )
        (tmp_path / "lifecycle.json").write_text(json.dumps(lifecycle))
        obs["evidence"]["lifecycle"].update(
            sha256=module.file_hash(tmp_path / "lifecycle.json"),
            bytes=(tmp_path / "lifecycle.json").stat().st_size,
        )
    elif case == "viewport":
        obs["viewport"]["tab_id"] = "other-tab"
    elif case == "host":
        obs["context"]["driver_version"] = "other-driver"
    elif case == "policy":
        obs["policy"]["response_mb"] = 1
        obs["policy_sha256"] = module.policy_hash(obs["policy"])
    elif case == "session":
        plan["session_id"] = "other-session"
    elif case == "source":
        (tmp_path / "synthetic.py").write_text("changed")
    elif case == "lock":
        (tmp_path / "models/models.lock.json").write_text('{"changed":true}')
    elif case == "path":
        obs["evidence"]["baseline"]["path"] = "../outside"
    now = NOW + timedelta(seconds=1000 if case == "pause" else 32)
    with pytest.raises(ValueError):
        module.validate_auto(obs, tmp_path, plan=plan, now=now)


def test_auto_baseline_does_not_accept_numeric_claims_without_metadata(
    harness_module, tmp_path
):
    cli = harness_module("benchmark")

    class Sensor:
        observation_context = CONTEXT

        def sample(self):
            return {
                "errors": [],
                "browser": {"visible": True},
                "nvml": {"used_mb": 1200},
                "windows": {"shared_mb": 40, "gpu_mapping_status": "resolved"},
            }

    with pytest.raises(ValueError, match="observability"):
        cli.observed_baseline(Sensor(), tmp_path, interval=0, sleep=lambda s: None)


def test_auto_mode_can_prepare_policy_before_pilot_without_gpu(
    harness_module, tmp_path
):
    cli = harness_module("benchmark")
    options = {action.dest for action in cli.parser()._actions}
    assert "observation_method" in options, "Falta modo automático explícito en CLI"


def test_observation_loss_inflight_preserves_samples_and_stops_polling(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    calls = []

    class Sensor:
        observation_context = CONTEXT

        def sample(self):
            return {"errors": ["windows_unavailable"]}

    class Api:
        def events(self, *args, **kwargs):
            calls.append("events")
            return []

        def request(self, *args):
            calls.append("status")
            return {"job_id": "j"}

    with pytest.raises(ValueError, match="observability"):
        runner.observe_job(
            Api(), Sensor(), "j", tmp_path, observation_s=1, interval_s=0
        )
    assert not calls and (tmp_path / "observers.ndjson").exists()


def test_finished_auto_session_requires_same_substantive_prerequisites(
    harness_module, tmp_path
):
    cli = harness_module("benchmark")
    evidence = harness_module("benchmark_evidence")
    evidence.exclusive_json(tmp_path / "summary.json", {"complete": True, "rows": 160})
    evidence.exclusive_json(
        tmp_path / "plan.json", {"observation_method": "wddm_auto_v1"}
    )
    evidence.exclusive_json(tmp_path / "seal.json", evidence.seal_files(tmp_path))
    with pytest.raises(ValueError, match="auto"):
        cli.finished_session(tmp_path)


def test_continuous_matrix_does_not_expire_by_pilot_age(harness_module, tmp_path):
    import inspect

    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    assert "continued_samples" in inspect.signature(module.validate_auto).parameters, (
        "Falta vigencia por continuidad y no por edad del piloto"
    )
    continuous = [sample(i, 8000, context=obs["context"]) for i in range(32, 1000)]
    assert (
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=1000),
            continued_samples=continuous,
        )["shared_validation_level"]
        == "provider_verified"
    )
    with pytest.raises(ValueError, match="paused"):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=1000),
            continued_samples=[
                sample(32, context=obs["context"]),
                sample(999, context=obs["context"]),
            ],
        )
    with pytest.raises(ValueError):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=1900),
            continued_samples=continuous,
        )


def test_owned_lifecycle_operation_is_observed_while_waiting(harness_module, tmp_path):
    import threading

    module = harness_module("benchmark_observation")
    run = validator(module, "monitored_operation")
    event = threading.Event()
    ticks = []

    class Sensor:
        def sample(self):
            ticks.append(1)
            if len(ticks) == 2:
                event.set()
            return {"browser": {"visible": True}}

    def operation():
        assert event.wait(1), "No sensores mientras API esperaba"
        return "loaded"

    assert run(operation, Sensor(), tmp_path, "load", interval_s=0) == "loaded"
    assert len((tmp_path / "load-observers.ndjson").read_text().splitlines()) >= 2


@pytest.mark.parametrize(
    "case",
    [
        "driver",
        "build",
        "raw_type",
        "info_type",
        "info_return",
        "status_bool",
        "same_path",
    ],
)
def test_live_metadata_is_checked_against_accreditation(harness_module, case):
    module = harness_module("benchmark_observation")
    s = sample(0)
    s["nvml"]["driver_version"] = "synthetic"
    s["windows"]["windows_build"] = "synthetic"
    for c in s["windows"]["counters"].values():
        c.update(
            raw_counter_type=0x10100, info_counter_type=0x10100, info_return=0, scale=0
        )
    module.validate_samples([s], CONTEXT, now=NOW + timedelta(seconds=1))
    if case == "driver":
        s["nvml"]["driver_version"] = "other"
    elif case == "build":
        s["windows"]["windows_build"] = "other"
    elif case == "raw_type":
        s["windows"]["counters"]["shared_mb"]["raw_counter_type"] = 1
    elif case == "info_type":
        s["windows"]["counters"]["shared_mb"]["info_counter_type"] = 1
    elif case == "info_return":
        s["windows"]["counters"]["shared_mb"]["info_return"] = 1
    elif case == "status_bool":
        s["windows"]["counters"]["shared_mb"]["raw_cstatus"] = False
    elif case == "same_path":
        s["windows"]["counters"]["shared_mb"]["path"] = s["windows"]["counters"][
            "dedicated_mb"
        ]["path"]
    with pytest.raises(ValueError):
        module.validate_samples([s], CONTEXT, now=NOW + timedelta(seconds=1))


def test_prerequisite_builder_uses_original_files_and_revalidates(
    harness_module, tmp_path
):
    module = harness_module("benchmark_observation")
    build = validator(module, "build_auto_prerequisites")
    obs, plan = sealed_case(tmp_path, module)
    value = build(
        plan,
        obs["context"],
        {key: item["path"] for key, item in obs["evidence"].items()},
        obs["viewport"]["evidence"]["path"],
        root=tmp_path,
        exclusive_gpu_authorized=True,
        now=NOW + timedelta(seconds=32),
    )
    assert value["observation"] == obs and value["browser"] == BROWSER
    (tmp_path / "loaded.ndjson").write_text("")
    with pytest.raises(ValueError):
        build(
            plan,
            obs["context"],
            {key: item["path"] for key, item in obs["evidence"].items()},
            obs["viewport"]["evidence"]["path"],
            root=tmp_path,
            exclusive_gpu_authorized=True,
            now=NOW + timedelta(seconds=32),
        )


def test_monitor_rejects_observability_before_owned_submission(
    harness_module, tmp_path
):
    module = harness_module("benchmark_observation")
    calls = []

    class Sensor:
        observation_context = CONTEXT

        def sample(self):
            return {"errors": ["windows_unavailable"]}

    with pytest.raises(ValueError, match="observability"):
        module.monitored_operation(
            lambda: calls.append("submitted"),
            Sensor(),
            tmp_path,
            "submission",
            interval_s=0,
        )
    assert calls == [], "Se inició una operación antes de comprobar su observabilidad"


def test_legacy_visible_window_is_still_accepted_without_auto_identity(
    harness_module, monkeypatch
):
    import ctypes
    from types import SimpleNamespace

    windows = harness_module("benchmark_windows")

    class Function:
        def __init__(self, fn):
            self.fn = fn

        def __call__(self, *args):
            return self.fn(*args)

    def pid(hwnd, out):
        out._obj.value = 4
        return 1

    def image(handle, flags, out, size):
        out.value = "C:\\private\\msedge.exe"
        return 1

    def times(handle, created, *args):
        created._obj.dwLowDateTime = 123
        return 1

    def rect(hwnd, out):
        out._obj.right = 100
        out._obj.bottom = 100
        return 1

    user = SimpleNamespace(
        **{
            k: Function(v)
            for k, v in {
                "IsWindow": lambda h: 1,
                "IsWindowVisible": lambda h: 1,
                "IsIconic": lambda h: 0,
                "GetWindowRect": rect,
                "GetWindowThreadProcessId": pid,
            }.items()
        }
    )
    kernel = SimpleNamespace(
        **{
            k: Function(v)
            for k, v in {
                "OpenProcess": lambda *a: 1,
                "QueryFullProcessImageNameW": image,
                "GetProcessTimes": times,
                "CloseHandle": lambda h: None,
            }.items()
        }
    )
    monkeypatch.setattr(
        ctypes, "WinDLL", lambda name: user if name == "user32" else kernel
    )
    assert windows.WindowsGpuMemory.browser_heartbeat({"pid": 4, "hwnd": 9})[
        "visible"
    ], "La política auto invalidó la identidad histórica permitida por task_manager_v1"


@pytest.mark.parametrize("part", ["all_operations", "raw_filetime", "utc_monotonic"])
def test_sample_clock_cannot_refresh_old_acquisition(harness_module, part):
    module = harness_module("benchmark_observation")
    value = sample(0)
    if part == "all_operations":
        value.update(timestamp=utc(1000), monotonic_ns=int(2000e9))
    elif part == "raw_filetime":
        value = sample(1000)
        value["windows"]["counters"]["shared_mb"]["raw_filetime"] = sample(999)[
            "windows"
        ]["query_filetime"]
    else:
        value["operations"]["wsl"]["started_monotonic_ns"] += int(500e9)
        value["operations"]["wsl"]["finished_monotonic_ns"] += int(500e9)
    with pytest.raises(ValueError):
        module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1001))


def test_acquisition_originals_cannot_be_lent_to_another_session(
    harness_module, tmp_path
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    obs["context"].update(session_id="borrowed-session", plan_sha256="e" * 64)
    plan.update(session_id="borrowed-session", plan_sha256="e" * 64)
    with pytest.raises(ValueError, match="acquisition"):
        module.validate_auto(obs, tmp_path, plan=plan, now=NOW + timedelta(seconds=32))


def test_reaccreditation_preserves_previous_segment_without_recertifying_it(
    harness_module, tmp_path
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    old = tmp_path / "previous.json"
    old.write_text(json.dumps(obs))
    historical = [sample(i, 8000, context=obs["context"]) for i in range(32, 91)]
    for phase, offset, used in (
        ("baseline", 1000, 1200),
        ("loaded", 1011, 8000),
        ("unloaded", 1022, 1200),
    ):
        path = tmp_path / ("new-" + phase + ".ndjson")
        path.write_text(
            "\n".join(
                json.dumps(sample(i, used, context=obs["context"]))
                for i in range(offset, offset + 10)
            )
            + "\n"
        )
        obs["evidence"][phase] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": module.file_hash(path),
        }
    for phase, offset in (("loaded", 1010), ("unloaded", 1021)):
        path = tmp_path / ("new-" + phase + "-proof.json")
        point = json.loads((tmp_path / "lifecycle.json").read_text())[phase]
        proof = json.loads((tmp_path / point["proof"]["path"]).read_text())
        proof.update(started_utc=utc(offset), finished_utc=utc(offset + 0.01))
        path.write_text(json.dumps(proof))
        point.update(
            observed_at=utc(offset + 0.01),
            proof={
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": module.file_hash(path),
            },
        )
        if phase == "loaded":
            lifecycle = {phase: point}
        else:
            lifecycle[phase] = point
    path = tmp_path / "new-lifecycle.json"
    path.write_text(json.dumps(lifecycle))
    obs["evidence"]["lifecycle"] = {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": module.file_hash(path),
    }
    obs["previous_accreditation"] = {
        "path": old.name,
        "bytes": old.stat().st_size,
        "sha256": module.file_hash(old),
    }
    original = old.read_bytes()
    live = [sample(i, 8000, context=obs["context"]) for i in range(1032, 1040)]
    result = module.validate_auto(
        obs,
        tmp_path,
        plan=plan,
        now=NOW + timedelta(seconds=1040),
        continued_samples=historical + live,
    )
    assert result["shared_validation_level"] == "provider_verified"
    assert old.read_bytes() == original
    built = module.build_auto_prerequisites(
        plan,
        obs["context"],
        {k: v["path"] for k, v in obs["evidence"].items()},
        "viewport.json",
        root=tmp_path,
        exclusive_gpu_authorized=True,
        now=NOW + timedelta(seconds=1040),
        previous_accreditation_path="previous.json",
    )
    assert (
        built["observation"]["previous_accreditation"] == obs["previous_accreditation"]
    )
    with pytest.raises(ValueError):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=1040),
            continued_samples=live + historical,
        )
    with pytest.raises(ValueError):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=1940),
            continued_samples=historical + live,
        )


def test_monitor_period_does_not_add_sampling_cost(
    harness_module, tmp_path, monkeypatch
):
    import threading

    module = harness_module("benchmark_observation")
    clock = [0.0]
    calls = []
    finished = threading.Event()

    def sleep(duration):
        calls.append(duration)
        clock[0] += duration

    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module.time, "sleep", sleep)

    class Sensor:
        def sample(self):
            clock[0] += 1.6
            if clock[0] >= 8:
                finished.set()
            return {"browser": {"visible": True}}

    def operation():
        assert finished.wait(2)
        return "done"

    assert (
        module.monitored_operation(operation, Sensor(), tmp_path, "slow", interval_s=1)
        == "done"
    )
    assert not any(c > 0 for c in calls), (
        "Se añadió espera al muestreo que ya supera el periodo"
    )


@pytest.mark.parametrize("resident", [False, True])
def test_resume_uses_history_and_rebaselines_only_when_idle(
    harness_module, tmp_path, monkeypatch, resident
):
    from types import SimpleNamespace

    module = harness_module("benchmark_observation")
    cli = harness_module("benchmark")
    now = NOW + timedelta(seconds=1000)

    class Clock(datetime):
        @staticmethod
        def now(tz):
            return now

    monkeypatch.setattr(module, "datetime", Clock)
    monkeypatch.setattr(module, "utc_now", lambda: Clock.now(timezone.utc).isoformat())
    monkeypatch.setattr(
        cli,
        "validate_prerequisites",
        lambda *a, **k: {
            "browser": BROWSER,
            "accreditation": {"context": CONTEXT},
            "observation": {},
        },
    )
    monkeypatch.setattr(cli, "validate_auto", lambda *a, **k: None)
    monkeypatch.setattr(module, "guard_sample", lambda *a: None)
    monkeypatch.setattr(cli, "wait_health", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "GpuLease",
        lambda *a: SimpleNamespace(acquire=lambda **k: None, release=lambda: None),
    )
    fresh = []
    monkeypatch.setattr(
        cli,
        "observed_baseline",
        lambda *a: fresh.append(True) or [sample(990 + i) for i in range(10)],
    )

    class ReachedRun(Exception):
        pass

    def execute(*args, **kwargs):
        raise ReachedRun()

    monkeypatch.setattr(cli, "execute_run", execute)
    monkeypatch.setattr(cli, "run_request", lambda *a: {})
    plan = {
        "observation_method": "wddm_auto_v1",
        "session_id": "synthetic-session",
        "plan_sha256": "a" * 64,
        "image_id": "synthetic",
        "lock_sha256": "lock",
        "configs": [{"config_id": "config"}],
        "runs": [
            {
                "run_id": str(i),
                "job_id": "j" + str(i),
                "config_id": "config",
                "duration_s": 30,
                "storage": "bind",
                "phase": "process_warm",
            }
            for i in range(4)
        ],
    }
    folder = tmp_path / "session"
    group = folder / "groups/0"
    group.mkdir(parents=True)
    (group / "baseline.ndjson").write_text(
        "\n".join(json.dumps(sample(i)) for i in range(10)) + "\n"
    )
    before = (group / "baseline.ndjson").read_bytes()
    (tmp_path / "data/tmp").mkdir(parents=True)
    (tmp_path / "data/tmp/t09-storage-0.json").write_text(
        json.dumps(
            {
                "resource_root": "/models",
                "destination_lock_sha256": "lock",
                "source_lock_sha256": "lock",
            }
        )
    )

    class Sensor:
        def nvidia(self):
            return {
                "name": "NVIDIA GeForce RTX 5070",
                "used_mb": 8000 if resident else 1200,
            }

        def sample(self):
            return sample(999, 8000 if resident else 1200)

    class Api:
        def request(self, *a):
            return {
                "loaded": {"model_id": "x"} if resident else None,
                "state": "running" if resident else "idle",
            }

    class Backend:
        def create(self, *a):
            return {"port": 1, "container_id": "own"}

        def start(self, *a):
            pass

        def verify_image_sources(self, *a):
            pass

        def cleanup(self, *a):
            return {"removed": True}

    ollama = SimpleNamespace(
        snapshot=lambda: {"models": []}, discharge=lambda s: None, restore=lambda s: {}
    )
    with pytest.raises(ReachedRun):
        cli.run_session(
            plan,
            folder,
            {},
            root=tmp_path,
            backend=Backend(),
            observer_factory=lambda w: Sensor(),
            api_factory=lambda *a: Api(),
            ollama=ollama,
            token="synthetic",
            resume=True,
        )
    assert fresh == ([] if resident else [True])
    assert (group / "baseline.ndjson").read_bytes() == before


@pytest.mark.parametrize("artifact", ["baseline", "host", "proof", "viewport"])
def test_builder_requires_acquisition_context_inside_each_original(
    harness_module, tmp_path, artifact
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    name = {
        "baseline": "baseline.ndjson",
        "host": "host.json",
        "proof": "loaded-proof.json",
        "viewport": "viewport.json",
    }[artifact]
    path = tmp_path / name
    if artifact == "baseline":
        values = [json.loads(line) for line in path.read_text().splitlines()]
        values[0].pop("acquisition_context")
        path.write_text("\n".join(json.dumps(v) for v in values) + "\n")
    else:
        value = json.loads(path.read_text())
        value.pop("acquisition_context")
        path.write_text(json.dumps(value))
    if artifact == "proof":
        lifecycle_path = tmp_path / "lifecycle.json"
        lifecycle = json.loads(lifecycle_path.read_text())
        lifecycle["loaded"]["proof"].update(
            bytes=path.stat().st_size, sha256=module.file_hash(path)
        )
        lifecycle_path.write_text(json.dumps(lifecycle))
    # The builder seals bytes itself, so this exercises original contents, not stale envelopes.
    with pytest.raises(ValueError):
        module.build_auto_prerequisites(
            plan,
            obs["context"],
            {k: v["path"] for k, v in obs["evidence"].items()},
            "viewport.json",
            root=tmp_path,
            exclusive_gpu_authorized=True,
            now=NOW + timedelta(seconds=32),
        )


def test_guard_rejects_live_sample_acquired_in_another_session(
    harness_module, monkeypatch
):
    from types import SimpleNamespace

    module = harness_module("benchmark_observation")

    class Clock(datetime):
        @staticmethod
        def now(tz):
            return NOW + timedelta(seconds=1)

    monkeypatch.setattr(module, "datetime", Clock)
    monkeypatch.setattr(module, "utc_now", lambda: Clock.now(timezone.utc).isoformat())
    value = sample(0, context={**CONTEXT, "session_id": "other"})
    sensors = SimpleNamespace(observation_context=CONTEXT)
    with pytest.raises(ValueError, match="acquisition"):
        module.guard_sample(sensors, value)


@pytest.mark.parametrize("case", ["context", "overlap", "unsealed"])
def test_accreditation_chain_rejects_mixed_or_overlapping_originals(
    harness_module, tmp_path, case
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    previous = copy.deepcopy(obs)
    if case == "context":
        previous["context"]["session_id"] = "other"
    path = tmp_path / "previous.json"
    path.write_text(json.dumps(previous))
    obs["previous_accreditation"] = {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": module.file_hash(path),
    }
    if case == "unsealed":
        path.write_text("{}")
    with pytest.raises(ValueError, match="context|overlap|seal"):
        module.validate_auto(obs, tmp_path, plan=plan, now=NOW + timedelta(seconds=32))


def test_observer_persists_context_snapshot_before_sensor_calls(harness_module):
    from types import SimpleNamespace

    module = harness_module("benchmark_observers")
    observation = harness_module("benchmark_observation")
    expected = observation.acquisition_context(CONTEXT)
    context = copy.deepcopy(CONTEXT)

    def execute(args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="MemAvailable: 1024000 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n",
        )

    sensor = module.Observers(
        SimpleNamespace(sample=dict, browser_heartbeat=lambda b: {}),
        browser=BROWSER,
        execute=execute,
    )
    sensor.observation_context = context

    def nvidia():
        context["session_id"] = "changed_during_call"
        return {"used_mb": 1200}

    sensor.nvidia = nvidia
    value = sensor.sample()
    assert value["acquisition_context"] == expected
    assert sensor.observation_context["session_id"] != expected["session_id"]


@pytest.mark.parametrize("case", ["unaccredited_history", "changed_pilot"])
def test_continuity_cannot_recertify_history_or_replace_pilot_samples(
    harness_module, tmp_path, case
):
    module = harness_module("benchmark_observation")
    obs, plan = sealed_case(tmp_path, module)
    value = sample(
        -1 if case == "unaccredited_history" else 5, 5000, context=obs["context"]
    )
    with pytest.raises(ValueError, match="history_requires|uncertified_pilot"):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=32),
            continued_samples=[value],
        )


def sequential_chain_case(tmp_path, module):
    """Two sealed CPU pilots with real acquisition order, plus their own live ticks."""
    previous, plan = sealed_case(tmp_path, module)

    def sequential(value):
        second = (datetime.fromisoformat(value["timestamp"]) - NOW).total_seconds()
        for key, offset, duration in (
            ("nvml", 0, 0.01),
            ("windows", 0.02, 0.01),
            ("wsl", 0.04, 0.20),
            ("browser", 0.25, 0.01),
        ):
            op = bracket(second + offset)
            op["finished_utc"] = utc(second + offset + duration)
            op["finished_monotonic_ns"] = int((second + offset + duration + 1000) * 1e9)
            value["operations"][key] = op
        value["windows"]["collection"] = copy.deepcopy(value["operations"]["windows"])
        native_time = int((NOW.timestamp() + 11644473600 + second + 0.025) * 1e7)
        value["windows"]["query_filetime"] = native_time
        value["windows"]["query_utc_filetime"] = native_time
        for counter in value["windows"]["counters"].values():
            counter["raw_filetime"] = native_time
            counter["raw_utc_filetime"] = native_time
        return value

    def seal(path):
        return {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": module.file_hash(path),
        }

    # Make both pilots sequential; all native timestamps and prior seals remain checked.
    for phase in ("baseline", "loaded", "unloaded"):
        path = tmp_path / previous["evidence"][phase]["path"]
        values = [
            sequential(json.loads(line)) for line in path.read_text().splitlines()
        ]
        path.write_text("\n".join(json.dumps(v) for v in values) + "\n")
        previous["evidence"][phase] = seal(path)
    previous_path = tmp_path / "previous.json"
    previous_path.write_text(json.dumps(previous))

    def shifted(value, key=None):
        if key == "acquisition_context":
            return value
        if isinstance(value, dict):
            return {k: shifted(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [shifted(v) for v in value]
        if key in {"timestamp", "started_utc", "finished_utc", "observed_at"}:
            return (datetime.fromisoformat(value) + timedelta(seconds=100)).isoformat()
        if key in {"monotonic_ns", "started_monotonic_ns", "finished_monotonic_ns"}:
            return value + 100 * 10**9
        if key in {
            "raw_filetime",
            "query_filetime",
            "raw_utc_filetime",
            "query_utc_filetime",
        }:
            return value + 100 * 10**7
        return value

    current = copy.deepcopy(previous)
    for name in (
        "loaded-proof",
        "unloaded-proof",
        "baseline",
        "loaded",
        "unloaded",
        "lifecycle",
        "host",
        "viewport",
    ):
        ndjson = name in {"baseline", "loaded", "unloaded"}
        original = tmp_path / (name + (".ndjson" if ndjson else ".json"))
        values = (
            [json.loads(line) for line in original.read_text().splitlines()]
            if ndjson
            else json.loads(original.read_text())
        )
        values = shifted(values)
        if name == "lifecycle":
            for phase in ("loaded", "unloaded"):
                values[phase]["proof"] = seal(
                    tmp_path / ("current-" + phase + "-proof.json")
                )
        path = tmp_path / ("current-" + original.name)
        path.write_text(
            "\n".join(json.dumps(v) for v in values) + "\n"
            if ndjson
            else json.dumps(values)
        )
        if name in current["evidence"]:
            current["evidence"][name] = seal(path)
        elif name == "viewport":
            current["viewport"].update(observed_at=utc(100), evidence=seal(path))
    current["previous_accreditation"] = seal(previous_path)
    history = [
        sequential(sample(i, context=previous["context"])) for i in range(32, 91)
    ]
    live = [sequential(sample(i, context=previous["context"])) for i in range(132, 141)]
    return current, plan, history + live


@pytest.mark.parametrize("history_ticks", [True, False])
def test_sequential_queries_preserve_accredited_history(
    harness_module, tmp_path, history_ticks
):
    module = harness_module("benchmark_observation")
    obs, plan, samples = sequential_chain_case(tmp_path, module)
    module.validate_samples(
        samples[:59], obs["context"], now=NOW + timedelta(seconds=90.3), continuous=True
    )
    if not history_ticks:
        samples = samples[59:]
    result = module.validate_auto(
        obs,
        tmp_path,
        plan=plan,
        now=NOW + timedelta(seconds=141),
        continued_samples=samples,
    )
    assert result["shared_validation_level"] == "provider_verified"
    assert result["shared_independent_validation"] is False
    assert result["browser_binding"] == "unproven"


@pytest.mark.parametrize(
    "case,reason",
    [
        ("wsl_duration", "auto_query_bracket_invalid"),
        ("browser_duration", "auto_query_bracket_invalid"),
        ("skew", "auto_dedicated_pair_skew"),
        ("clock", "auto_query_bracket_invalid"),
        ("pause", "auto_continuity_expired_or_not_started"),
        ("future", "auto_query_bracket_invalid"),
        ("expired", "auto_continuity_expired_or_not_started"),
        ("original", "seal"),
    ],
)
def test_sequential_chain_keeps_temporal_and_original_guards(
    harness_module, tmp_path, case, reason
):
    module = harness_module("benchmark_observation")
    obs, plan, samples = sequential_chain_case(tmp_path, module)
    now = NOW + timedelta(seconds=141)
    bad = samples[58]
    if case in {"wsl_duration", "browser_duration"}:
        key = case.split("_")[0]
        start = datetime.fromisoformat(bad["operations"][key]["started_utc"])
        bad["operations"][key]["finished_utc"] = (
            start + timedelta(seconds=2.01)
        ).isoformat()
        bad["operations"][key]["finished_monotonic_ns"] = (
            bad["operations"][key]["started_monotonic_ns"] + 2010000000
        )
    elif case == "skew":
        bad["operations"]["windows"] = bracket(91.1)
    elif case == "clock":
        bad["operations"]["browser"]["finished_monotonic_ns"] += 200000000
    elif case == "pause":
        samples[59:] = [sample(i, context=obs["context"]) for i in range(1033, 1041)]
        now = NOW + timedelta(seconds=1041)
    elif case == "future":
        now = NOW + timedelta(seconds=140.1)
    elif case == "expired":
        now = NOW + timedelta(seconds=1041)
    elif case == "original":
        (tmp_path / "previous.json").write_text("{}")
    with pytest.raises(ValueError, match=reason):
        module.validate_auto(
            obs, tmp_path, plan=plan, now=now, continued_samples=samples
        )


@pytest.mark.parametrize("operation", ["wsl", "browser"])
@pytest.mark.parametrize("continuity", [True, False])
@pytest.mark.parametrize("future", [True, False])
def test_pilot_acquisition_respects_external_now(
    harness_module, tmp_path, operation, continuity, future
):
    module = harness_module("benchmark_observation")
    obs, plan, _ = sequential_chain_case(tmp_path, module)
    path = tmp_path / obs["evidence"]["unloaded"]["path"]
    values = [json.loads(line) for line in path.read_text().splitlines()]
    # Windows stays at 131.02..131.03; the later query is still bounded and sealed.
    intervals = (
        {"wsl": (131.04, 132.24), "browser": (132.25, 132.26)}
        if operation == "wsl"
        else {"browser": (131.25, 132.26)}
    )
    for name, (start, end) in intervals.items():
        values[-1]["operations"][name].update(
            started_utc=utc(start),
            finished_utc=utc(end),
            started_monotonic_ns=int((start + 1000) * 1e9),
            finished_monotonic_ns=int((end + 1000) * 1e9),
        )
    path.write_text("\n".join(json.dumps(v) for v in values) + "\n")
    obs["evidence"]["unloaded"].update(
        bytes=path.stat().st_size, sha256=module.file_hash(path)
    )
    now = NOW + timedelta(seconds=132.1 if future else 134)
    live = [sample(132 if future else 133, context=obs["context"])]
    if future:
        with pytest.raises(ValueError, match="auto_query_bracket_invalid"):
            module.validate_samples(values, obs["context"], now=now)
        with pytest.raises(ValueError, match="auto_query_bracket_invalid"):
            module.validate_auto(
                obs,
                tmp_path,
                plan=plan,
                now=now,
                continued_samples=live if continuity else [],
            )
    else:
        result = module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=now,
            continued_samples=live if continuity else [],
        )
        assert result["shared_validation_level"] == "provider_verified"


def test_continuity_starts_after_complete_pilot_acquisition(harness_module, tmp_path):
    module = harness_module("benchmark_observation")
    obs, plan, _ = sequential_chain_case(tmp_path, module)
    path = tmp_path / obs["evidence"]["unloaded"]["path"]
    values = [json.loads(line) for line in path.read_text().splitlines()]
    values[-1]["operations"]["browser"].update(
        finished_utc=utc(132.26),
        finished_monotonic_ns=int(1132.26 * 1e9),
    )
    path.write_text("\n".join(json.dumps(v) for v in values) + "\n")
    obs["evidence"]["unloaded"].update(
        bytes=path.stat().st_size, sha256=module.file_hash(path)
    )
    with pytest.raises(ValueError, match="auto_continuity_expired_or_not_started"):
        module.validate_auto(
            obs,
            tmp_path,
            plan=plan,
            now=NOW + timedelta(seconds=133),
            continued_samples=[sample(132, context=obs["context"])],
        )


def test_filetime_and_seven_digit_utc_preserve_native_100ns_order(harness_module):
    from fractions import Fraction

    module = harness_module("benchmark_observation")
    query = module.filetime(134358072800888324)
    assert query == Fraction(17913336800888324, 10000000)
    assert module.stamp("2026-10-07T00:41:20.0888323+00:00") < query
    assert query < module.stamp("2026-10-07T00:41:20.0888325+00:00")


def test_submicrosecond_native_query_is_valid_only_inside_exact_bracket(harness_module):
    module = harness_module("benchmark_observation")
    value = sample(0)
    value["windows"]["collection"].update(
        started_utc="2026-10-07T00:00:00.0088323+00:00",
        finished_utc="2026-10-07T00:00:00.0088325+00:00",
        started_monotonic_ns=1000008832300,
        finished_monotonic_ns=1000008832500,
    )
    value["windows"]["query_filetime"] = 134358048000088324
    value["windows"]["query_utc_filetime"] = 134358048000088324
    for counter in value["windows"]["counters"].values():
        counter["raw_filetime"] = value["windows"]["query_filetime"]
        counter["raw_utc_filetime"] = value["windows"]["query_filetime"]
    assert module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))
    value["windows"]["query_filetime"] += 2
    value["windows"]["query_utc_filetime"] += 2
    with pytest.raises(ValueError, match="auto_collection_timestamp_invalid"):
        module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))


def local_filetime_sample():
    value = sample(0)
    zone = {
        "id": 2,
        "bias_minutes": -60,
        "standard_bias_minutes": 0,
        "daylight_bias_minutes": -60,
        "standard_name": "CPU standard",
        "daylight_name": "CPU daylight",
        "standard_date": [0, 10, 0, 5, 2, 0, 0, 0],
        "daylight_date": [0, 3, 0, 5, 2, 0, 0, 0],
    }
    value["windows"]["filetime_clock"] = {
        "basis": "local",
        "conversion": "LocalFileTimeToFileTime",
        "timezone_before": zone,
        "timezone_after": copy.deepcopy(zone),
    }
    win = value["windows"]
    win["query_utc_filetime"] = win["query_filetime"]
    win["query_filetime"] += 72000000000
    for counter in win["counters"].values():
        counter["raw_utc_filetime"] = counter["raw_filetime"]
        counter["raw_filetime"] += 72000000000
    return value


def test_native_local_filetime_is_preserved_and_utc_conversion_is_checked(
    harness_module,
):
    module = harness_module("benchmark_observation")
    value = local_filetime_sample()
    original = copy.deepcopy(value)
    assert module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))
    assert value == original


@pytest.mark.parametrize(
    "case", ["query", "counter", "zone_change", "bias", "conversion", "missing"]
)
def test_inconsistent_native_filetime_conversion_is_rejected(harness_module, case):
    module = harness_module("benchmark_observation")
    value = local_filetime_sample()
    win = value["windows"]
    if case == "query":
        win["query_utc_filetime"] += 1
    elif case == "counter":
        win["counters"]["shared_mb"]["raw_utc_filetime"] += 1
    elif case == "zone_change":
        win["filetime_clock"]["timezone_after"]["id"] = 1
    elif case == "bias":
        win["filetime_clock"]["timezone_before"]["bias_minutes"] = 0
        win["filetime_clock"]["timezone_after"]["bias_minutes"] = 0
    elif case == "conversion":
        win["filetime_clock"]["conversion"] = "assumed_offset"
    else:
        del win["query_utc_filetime"]
    with pytest.raises(ValueError, match="auto_filetime_conversion_invalid"):
        module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))


def test_native_sample_without_explicit_clock_basis_cannot_qualify(harness_module):
    module = harness_module("benchmark_observation")
    value = sample(0)
    value["windows"].pop("filetime_clock", None)
    value["windows"].pop("query_utc_filetime", None)
    for counter in value["windows"]["counters"].values():
        counter.pop("raw_utc_filetime", None)
    with pytest.raises(ValueError, match="auto_filetime_conversion_invalid"):
        module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))


def test_implicit_now_preserves_native_submicrosecond_finish(
    harness_module, monkeypatch
):
    module = harness_module("benchmark_observation")
    value = sample(0)
    for operation in value["operations"].values():
        operation["finished_utc"] = "2026-10-07T00:00:00.0100004+00:00"

    class Clock(datetime):
        @staticmethod
        def now(tz):
            return NOW + timedelta(seconds=0.01)

    monkeypatch.setattr(module, "datetime", Clock)
    monkeypatch.setattr(module, "utc_now", lambda: Clock.now(timezone.utc).isoformat())
    monkeypatch.setattr(
        module, "utc_now", lambda: "2026-10-07T00:00:00.0100004+00:00", raising=False
    )
    assert module.validate_samples([value], CONTEXT)


@pytest.mark.parametrize(
    "state,bias,standard,daylight",
    [
        (0, 0, 0, 0),
        (1, -60, 0, -60),
        (2, -60, 0, -60),
        (1, 300, 0, -60),
        (2, 300, 0, -60),
        (0, -330, 0, 0),
    ],
)
def test_native_timezone_conversion_handles_utc_signed_offsets_and_dst(
    harness_module, state, bias, standard, daylight
):
    module = harness_module("benchmark_observation")
    value = sample(0)
    win = value["windows"]
    zone = win["filetime_clock"]["timezone_before"]
    zone.update(
        id=state,
        bias_minutes=bias,
        standard_bias_minutes=standard,
        daylight_bias_minutes=daylight,
    )
    if state in {1, 2}:
        zone["standard_date"] = [0, 10, 0, 5, 2, 0, 0, 0]
        zone["daylight_date"] = [0, 3, 0, 5, 2, 0, 0, 0]
    win["filetime_clock"]["timezone_after"] = copy.deepcopy(zone)
    offset = -(bias + (daylight if state == 2 else standard)) * 60 * 10000000
    win["query_filetime"] += offset
    for counter in win["counters"].values():
        counter["raw_filetime"] += offset
    assert module.validate_samples([value], CONTEXT, now=NOW + timedelta(seconds=1))


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-07T00:00:00.12345678+00:00",
        "2026-10-07T00:00:00.1234567+02:00",
        "2026-10-07T00:00:00.1234567",
        "invalid",
    ],
)
def test_exact_timestamp_parser_rejects_unsupported_precision_or_non_utc(
    harness_module, text
):
    with pytest.raises(ValueError, match="auto_timestamp_invalid"):
        harness_module("benchmark_observation").stamp(text)


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-07T00:00:00.0000001+00:00:00",
        "2026-10-07T00:00:00,0000001+00:00",
        "2026-10-07T00:00:00+00:00:00.0000001",
    ],
)
def test_noncanonical_timestamp_cannot_silently_drop_fraction(harness_module, text):
    with pytest.raises(ValueError, match="auto_timestamp_invalid"):
        harness_module("benchmark_observation").stamp(text)
