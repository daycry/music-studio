"""CPU synthetic clocks with real guards and real owned operation threads."""

import importlib
import threading
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def continuity(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "tests"))
    fixtures = importlib.import_module("test_benchmark_observation")
    observation = importlib.import_module("benchmark_observation")
    runner = importlib.import_module("benchmark_runner")
    state = SimpleNamespace(t=0.0, release=threading.Event(), worker=None, due=None)

    def sleep(seconds):
        state.t += seconds
        # Yield to the real operation thread without using wall time as test time.
        threading.Event().wait(0.001)

    monkeypatch.setattr(
        observation, "time", SimpleNamespace(monotonic=lambda: state.t, sleep=sleep)
    )
    monkeypatch.setattr(observation, "utc_now", lambda: fixtures.utc(state.t + 1))

    class Sensors:
        observation_context = fixtures.CONTEXT

        def sample(self):
            state.t += 0.02
            if state.due is not None and state.t >= state.due:
                state.release.set()
            return fixtures.sample(state.t)

    class Api:
        def __init__(self, delayed_path, error=None):
            self.calls = []
            self.delayed_path = delayed_path
            self.error = error

        def request(self, method, path, body=None):
            self.calls.append((method, path))
            if path == self.delayed_path:
                if threading.current_thread() is threading.main_thread():
                    state.t += 15
                else:
                    state.worker = threading.current_thread()
                    state.due = state.t + 15
                    assert state.release.wait(5), "CPU test operation was not released"
                if self.error is not None:
                    raise self.error
            return {"job_id": "J", "state": "done"}

        def events(self, *args, **kwargs):
            return [{"seq": 1, "job_id": "J", "type": "error", "data": {}}]

    plan = {
        "observation_method": "wddm_auto_v1",
        "timeouts": {"observation_s": 1},
        "observer_policy": {"interval_s": 0},
    }
    return SimpleNamespace(
        runner=runner,
        observation=observation,
        state=state,
        Sensors=Sensors,
        Api=Api,
        plan=plan,
    )


def test_slow_estimate_preserves_continuity_before_single_submission(
    continuity, tmp_path
):
    c = continuity
    sensors, api = c.Sensors(), c.Api("/v1/estimate")
    terminal = c.runner.execute_run(
        c.plan, {"job_id": "J"}, api, sensors, tmp_path, {"job_id": "J"}
    )
    assert terminal["type"] == "error"
    assert api.calls == [("POST", "/v1/estimate"), ("POST", "/v1/jobs")]
    records = c.runner.read_records(tmp_path / "estimate-observers.ndjson")
    assert len(records) >= 15
    assert sensors.previous_sample == sensors.continued_samples[-1]
    assert c.state.worker is not None and not c.state.worker.is_alive()
    assert (tmp_path / "accepted.json").exists()


def test_slow_resume_query_preserves_continuity_without_resubmission(
    continuity, tmp_path
):
    c = continuity
    c.runner.exclusive_json(tmp_path / "submission-intent.json", {"job_id": "J"})
    sensors, api = c.Sensors(), c.Api("/v1/jobs/J")
    terminal = c.runner.execute_run(
        c.plan, {"job_id": "J"}, api, sensors, tmp_path, {"job_id": "J"}
    )
    assert terminal["type"] == "error"
    assert api.calls == [("GET", "/v1/jobs/J")]
    assert len(c.runner.read_records(tmp_path / "resume-status-observers.ndjson")) >= 15
    assert not (tmp_path / "accepted.json").exists()
    assert c.state.worker is not None and not c.state.worker.is_alive()


def test_estimate_failure_preserves_no_intent_and_joins_operation(continuity, tmp_path):
    c = continuity
    api = c.Api("/v1/estimate", c.runner.ApiError("TRANSPORT_UNAVAILABLE"))
    with pytest.raises(c.runner.ApiError, match="TRANSPORT_UNAVAILABLE"):
        c.runner.execute_run(
            c.plan, {"job_id": "J"}, api, c.Sensors(), tmp_path, {"job_id": "J"}
        )
    assert api.calls == [("POST", "/v1/estimate")]
    assert not (tmp_path / "submission-intent.json").exists()
    assert not (tmp_path / "estimate.json").exists()
    assert c.state.worker is not None and not c.state.worker.is_alive()


def test_loss_during_estimate_prevents_submission_and_waits_owned_thread(
    continuity, tmp_path
):
    c = continuity
    api = c.Api("/v1/estimate")

    class LostSensor(c.Sensors):
        def sample(self):
            value = super().sample()
            if c.state.t > 3:
                # Model the in-flight transport completing as observation fails.
                c.state.release.set()
                value["errors"] = ["synthetic_windows_unavailable"]
            return value

    sensors = LostSensor()
    with pytest.raises(ValueError, match="observability_lost"):
        c.runner.execute_run(
            c.plan, {"job_id": "J"}, api, sensors, tmp_path, {"job_id": "J"}
        )
    assert api.calls == [("POST", "/v1/estimate")]
    assert not (tmp_path / "submission-intent.json").exists()
    assert not (tmp_path / "accepted.json").exists()
    assert c.state.worker is not None and not c.state.worker.is_alive()
    assert sensors.previous_sample == sensors.continued_samples[-1]


@pytest.mark.parametrize("code", ["NOT_FOUND", "TRANSPORT_UNAVAILABLE"])
def test_resume_failure_keeps_intent_without_duplicate_job(continuity, tmp_path, code):
    c = continuity
    c.runner.exclusive_json(tmp_path / "submission-intent.json", {"job_id": "J"})
    original = (tmp_path / "submission-intent.json").read_bytes()
    api = c.Api("/v1/jobs/J", c.runner.ApiError(code))
    expected = ValueError if code == "NOT_FOUND" else c.runner.ApiError
    with pytest.raises(
        expected, match="missing_existing_job" if code == "NOT_FOUND" else code
    ):
        c.runner.execute_run(
            c.plan, {"job_id": "J"}, api, c.Sensors(), tmp_path, {"job_id": "J"}
        )
    assert api.calls == [("GET", "/v1/jobs/J")]
    assert (tmp_path / "submission-intent.json").read_bytes() == original
    assert not (tmp_path / "accepted.json").exists()
    assert c.state.worker is not None and not c.state.worker.is_alive()


@pytest.mark.parametrize(
    "status",
    [{"job_id": "foreign", "state": "done"}, {"job_id": "J", "state": "unknown"}],
)
def test_resume_identity_and_state_constraints_remain(continuity, tmp_path, status):
    c = continuity
    c.runner.exclusive_json(tmp_path / "submission-intent.json", {"job_id": "J"})
    api = c.Api("unused")
    base_request = api.request

    def request(*args):
        base_request(*args)
        return status

    api.request = request
    with pytest.raises(
        ValueError, match="resume_job_identity_mismatch|unknown_job_state"
    ):
        c.runner.execute_run(
            c.plan, {"job_id": "J"}, api, c.Sensors(), tmp_path, {"job_id": "J"}
        )
    assert api.calls == [("GET", "/v1/jobs/J")]
    assert not (tmp_path / "accepted.json").exists()


def test_manual_method_keeps_synchronous_requests(continuity, tmp_path, monkeypatch):
    c = continuity
    plan = {**c.plan, "observation_method": "task_manager_v1"}
    api = c.Api("/v1/estimate")
    monkeypatch.setattr(
        c.runner, "observe_job", lambda *args, **kwargs: ({"type": "error"}, [])
    )
    monkeypatch.setattr(
        c.runner,
        "monitored_operation",
        lambda *args: pytest.fail("Manual branch started automatic monitor"),
    )
    terminal = c.runner.execute_run(
        plan, {"job_id": "J"}, api, c.Sensors(), tmp_path, {"job_id": "J"}
    )
    assert terminal == {"type": "error"}
    assert api.calls == [("POST", "/v1/estimate"), ("POST", "/v1/jobs")]


def test_saved_terminal_requires_matching_event_evidence(continuity, tmp_path):
    c = continuity
    c.runner.exclusive_json(tmp_path / "terminal.json", {"type": "done"})
    c.runner.append_record(
        tmp_path / "events.ndjson",
        {"seq": 1, "job_id": "J", "type": "error", "data": {}},
    )
    api = c.Api("unused")
    with pytest.raises(ValueError, match="terminal_evidence_mismatch"):
        c.runner.execute_run(
            c.plan, {"job_id": "J"}, api, c.Sensors(), tmp_path, {"job_id": "J"}
        )
    assert not api.calls


def test_resume_rejects_request_mutation_before_monitor_or_api(continuity, tmp_path):
    c = continuity
    c.runner.exclusive_json(tmp_path / "request.json", {"job_id": "J", "seed": 1})
    api = c.Api("unused")
    with pytest.raises(ValueError, match="resume_request_changed"):
        c.runner.execute_run(
            c.plan,
            {"job_id": "J"},
            api,
            c.Sensors(),
            tmp_path,
            {"job_id": "J", "seed": 2},
        )
    assert not api.calls


def test_manual_prerequisites_remain_hash_and_authorization_bound(continuity, tmp_path):
    c = continuity
    evidence = tmp_path / "owned.txt"
    evidence.write_text("Synthetic CPU manual evidence", encoding="utf-8")
    seal = {"evidence_path": evidence.name, "sha256": c.runner.file_hash(evidence)}
    observation = {
        **seal,
        "gpu": "NVIDIA GeForce RTX 5070",
        "observed_at": "2026-10-07T00:00:00Z",
        "shared_mb": 40,
    }
    value = {
        "task_manager": {"baseline": observation, "representative": observation},
        "browser": {**seal, "pid": 4, "hwnd": 9},
        "exclusive_gpu_authorized": True,
    }
    assert c.runner.validate_prerequisites(value, tmp_path) == value
    with pytest.raises(ValueError, match="exclusive_gpu_prerequisite_required"):
        c.runner.validate_prerequisites(
            {**value, "exclusive_gpu_authorized": False}, tmp_path
        )
    with pytest.raises(ValueError, match="visible_browser_identity_required"):
        c.runner.validate_prerequisites(
            {**value, "browser": {**value["browser"], "pid": 0}}, tmp_path
        )
    evidence.write_text("Altered original", encoding="utf-8")
    with pytest.raises(ValueError, match="task_manager_evidence_hash_mismatch"):
        c.runner.validate_prerequisites(value, tmp_path)


@pytest.mark.parametrize("valid_samples", [True, False])
def test_auto_summary_does_not_certify_a_continuity_gap(continuity, valid_samples):
    c = continuity
    fixtures = importlib.import_module("test_benchmark_observation")
    baseline = [fixtures.sample(i) for i in range(10)]
    samples = [fixtures.sample(i) for i in range(11, 21)]
    if not valid_samples:
        samples[-1] = fixtures.sample(30)
    timing = {
        "clock": "perf_counter_ns_cuda_synchronized",
        "cuda_sync": True,
        "infer_start_ns": 0,
        "infer_end_ns": 1_000_000_000,
        "inference_s": 1,
        "audio_duration_s": 30,
        "rtf": 1 / 30,
    }
    terminal = {
        "type": "done",
        "data": {
            "telemetry": {
                "load_s": 1,
                "run_s": 2,
                "vram_peak_mb": 1200,
                "vram_cap_mb": 10000,
                "spilled": False,
                "extra": {"inference_timings": [timing]},
            }
        },
    }
    row = c.runner.summarize_run(
        {"job_id": "J"},
        terminal,
        samples,
        baseline,
        output_valid=True,
        fidelity_valid=True,
        observation_context=fixtures.CONTEXT,
        now=fixtures.NOW + timedelta(seconds=31),
    )
    assert row["valid"] is valid_samples
    if not valid_samples:
        assert row["shared_gpu_observed"] is None
        assert "replayed_or_paused" in row["observation_error"]
