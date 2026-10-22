"""Pruebas CPU de readquisición completa; no acreditan GPU."""

import copy
import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from test_benchmark_observation import CONTEXT, NOW, sample


def v2(value):
    from benchmark_observation import acquisition_context

    value["acquisition_context"] = acquisition_context(CONTEXT, "wddm_auto_v2")
    return value


def disagreement(second):
    value = sample(second, 8996)
    value["nvml"]["used_mb"] = 9304
    return value


def test_monitored_transition_recovers_with_new_complete_original(
    harness_module, monkeypatch, tmp_path
):
    module = harness_module("benchmark_observation")
    monkeypatch.setattr(
        module, "now_stamp", lambda value=None: module.stamp(sample(20)["timestamp"])
    )
    values = iter([v2(disagreement(1)), v2(sample(1.134, 8996)), v2(sample(2, 8996))])
    last = []

    def acquire():
        value = next(values)
        last[:] = [value]
        return value

    monkeypatch.setattr(
        module,
        "episode_clock",
        lambda: (
            max(op["finished_utc"] for op in last[0]["operations"].values()),
            max(op["finished_monotonic_ns"] for op in last[0]["operations"].values()),
        ),
    )
    observer = SimpleNamespace(
        observation_context=copy.deepcopy(CONTEXT),
        observation_method="wddm_auto_v2",
        sample=acquire,
    )
    assert (
        module.monitored_operation(lambda: "finished", observer, tmp_path, "transition")
        == "finished"
    )
    assert observer.previous_sample["nvml"]["used_mb"] == 8996


def test_episode_completion_uses_previous_acquisition_end_for_continuity():
    """A slow current acquisition must not double-count the prior sample work."""
    from benchmark_observation import episode_decision

    previous = v2(sample(0))
    current = v2(sample(1.754))
    completion = (sample(2.505)["timestamp"], int(1002.505 * 10**9))

    # The receipt is 2.505 s after the previous sample start, but only 2.495 s
    # after its acquisition end. This is a valid continuous chain.
    assert episode_decision(
        [current],
        CONTEXT,
        previous=previous,
        completion=completion,
        now=NOW + timedelta(seconds=10),
        method="wddm_auto_v2",
    ) == current


def test_episode_completion_still_rejects_gap_after_previous_acquisition_end():
    from benchmark_observation import episode_decision, validate_samples

    previous = v2(sample(0))
    current = v2(sample(1.754))
    validate_samples(
        [current],
        CONTEXT,
        previous=previous,
        now=NOW + timedelta(seconds=10),
        method="wddm_auto_v2",
    )
    with pytest.raises(ValueError, match="auto_replayed_or_paused_sample"):
        episode_decision(
            [current],
            CONTEXT,
            previous=previous,
            completion=(sample(2.7)["timestamp"], int(1002.7 * 10**9)),
            now=NOW + timedelta(seconds=10),
            method="wddm_auto_v2",
        )


@pytest.fixture
def recovery(harness_module, monkeypatch, tmp_path):
    module = harness_module("benchmark_observation")
    monkeypatch.setattr(module, "utc_now", lambda: sample(100)["timestamp"])
    calls = []
    values = []

    def acquire():
        calls.append(len(calls))
        value = copy.deepcopy(values.pop(0))
        sensors.last_raw = value
        return value

    sensors = SimpleNamespace(
        observation_context=copy.deepcopy(CONTEXT),
        observation_method="wddm_auto_v2",
        sample=acquire,
    )

    def completion_clock():
        operations = sensors.last_raw.get("operations", {})
        return (
            max(op["finished_utc"] for op in operations.values())
            if operations
            else sample(100)["timestamp"],
            max(op["finished_monotonic_ns"] for op in operations.values())
            if operations
            else sample(100)["monotonic_ns"],
        )

    monkeypatch.setattr(module, "episode_clock", completion_clock)
    return SimpleNamespace(
        module=module,
        sensors=sensors,
        values=values,
        calls=calls,
        path=tmp_path / "accepted.ndjson",
    )


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_raw_persisted_before_decision_and_rejected_original_retained(
    recovery, monkeypatch
):
    c = recovery
    c.values[:] = [v2(disagreement(1)), v2(sample(1.134, 8996))]
    originals = copy.deepcopy(c.values)
    decide = c.module.episode_decision

    def inspect(values, *args, **kwargs):
        assert read(c.path.with_name(c.path.name + ".originals.ndjson")) == values
        return decide(values, *args, **kwargs)

    monkeypatch.setattr(c.module, "episode_decision", inspect)
    value = c.module.acquire_sample(c.sensors, c.path)
    assert value == originals[-1]
    assert c.calls == [0, 1]
    assert read(c.path)[0]["sample"] == originals[-1]
    with pytest.raises(ValueError, match="dedicated_disagreement"):
        c.module.validate_samples([originals[0]], CONTEXT, method="wddm_auto_v2")
    assert read(c.path.with_name(c.path.name + ".originals.ndjson")) == originals


def test_known_lifecycle_boundary_prevents_retry_before_dedicated_classification(
    recovery,
):
    c = recovery
    c.sensors.phase_started_utc = sample(2)["timestamp"]
    c.values[:] = [v2(disagreement(1)), v2(sample(1.134, 8996))]
    with pytest.raises(ValueError, match="phase_transition"):
        c.module.acquire_sample(c.sensors, c.path)
    assert len(c.calls) == 1 and not c.path.exists()


@pytest.mark.parametrize(
    "invalid",
    [
        "browser",
        "counter",
        "identity",
        "wsl",
        "unavailable",
        "collection",
        "cadence",
        "context",
        "skew",
    ],
)
def test_competing_invalid_never_retries(recovery, invalid):
    c = recovery
    value = v2(disagreement(1))
    if invalid == "browser":
        value["browser"]["visible"] = False
    elif invalid == "counter":
        value["windows"]["counters"]["shared_mb"]["raw_cstatus"] = 7
    elif invalid == "identity":
        value["nvml"]["uuid"] = "foreign"
    elif invalid == "wsl":
        value["wsl"]["mem_available_mb"] = None
    elif invalid == "unavailable":
        value["errors"] = ["browser_unavailable"]
    elif invalid == "collection":
        value["windows"]["collection"]["finished_monotonic_ns"] += 100_000_000
    elif invalid == "cadence":
        c.sensors.previous_sample = v2(sample(-3))
    elif invalid == "context":
        value["acquisition_context"]["session_id"] = "foreign"
    elif invalid == "skew":
        value["operations"]["nvml"]["finished_utc"] = sample(3)["timestamp"]
        value["operations"]["nvml"]["finished_monotonic_ns"] += 2_000_000_000
    c.values[:] = [value, v2(sample(1.134, 8996))]
    with pytest.raises(ValueError, match="observability_lost"):
        c.module.acquire_sample(c.sensors, c.path)
    assert len(c.calls) == 1
    assert not c.path.exists()
    assert len(read(c.path.with_name(c.path.name + ".originals.ndjson"))) == 1


@pytest.mark.parametrize(
    "failure",
    [
        "second_mismatch",
        "deadline",
        "tick",
        "partial",
        "second_browser",
        "second_context",
    ],
)
def test_second_acquisition_cannot_reset_budget_or_hide_other_failures(
    recovery, failure
):
    c = recovery
    first, second = v2(disagreement(1)), v2(sample(1.134, 8996))
    if failure == "second_mismatch":
        second = v2(disagreement(1.134))
    elif failure == "deadline":
        second = v2(sample(3.001, 8996))
    elif failure == "tick":
        c.sensors.previous_sample = v2(sample(0))
        second = v2(sample(2.6, 8996))
    elif failure == "partial":
        second["operations"]["browser"] = copy.deepcopy(first["operations"]["browser"])
    elif failure == "second_browser":
        second["browser"]["visible"] = False
    elif failure == "second_context":
        second["acquisition_context"]["plan_sha256"] = "foreign"
    c.values[:] = [first, second, v2(sample(4, 8996))]
    with pytest.raises(ValueError, match="observability_lost"):
        c.module.acquire_sample(c.sensors, c.path)
    assert len(c.calls) == 2 and len(c.values) == 1
    assert not c.path.exists()
    assert read(c.path.with_name(c.path.name + ".originals.ndjson")) == [first, second]


@pytest.mark.parametrize(
    "tamper",
    [
        "omit",
        "reorder",
        "dupe",
        "partial",
        "context",
        "accepted",
        "claim",
        "deadline",
        "ordinal",
        "hash",
        "predecessor",
        "version",
    ],
)
def test_offline_recomputes_recovery_and_rejects_forged_episode(recovery, tamper):
    c = recovery
    c.values[:] = [v2(disagreement(1)), v2(sample(1.134, 8996))]
    c.module.acquire_sample(c.sensors, c.path)
    record = read(c.path)[0]
    assert c.module.validate_episode(record, CONTEXT) == record["sample"]
    episode = record["episode"]
    if tamper == "omit":
        episode["originals"].pop(0)
    elif tamper == "reorder":
        episode["originals"].reverse()
    elif tamper == "dupe":
        episode["originals"][1] = copy.deepcopy(episode["originals"][0])
    elif tamper == "partial":
        first, second = (r["original"] for r in episode["originals"])
        second["operations"]["browser"] = first["operations"]["browser"]
        episode["originals"][1]["sha256"] = c.module.digest(second)
        episode["accepted_sha256"] = c.module.digest(second)
        record["sample"] = second
    elif tamper == "context":
        episode["context"]["session_id"] = "foreign"
    elif tamper == "accepted":
        record["sample"] = episode["originals"][0]["original"]
        episode["accepted_sha256"] = c.module.digest(record["sample"])
    elif tamper == "claim":
        episode["accepted"] = True
    elif tamper == "deadline":
        episode["deadline_utc_ticks"] = str(c.module.stamp(sample(20)["timestamp"]))
    elif tamper == "ordinal":
        episode["ordinal"] = 0
    elif tamper == "hash":
        episode["originals"][0]["sha256"] = "0" * 64
    elif tamper == "predecessor":
        episode["predecessor"] = v2(sample(2))
    elif tamper == "version":
        episode["version"] = "wddm_auto_v1"
    with pytest.raises(ValueError):
        c.module.validate_episode(record, CONTEXT)


@pytest.mark.parametrize(
    "tamper", ["omit", "reorder", "duplicate", "previous", "context", "mix", "truncate"]
)
def test_continuity_chain_rejects_missing_or_replayed_episodes(recovery, tamper):
    c = recovery
    c.values[:] = [v2(sample(i)) for i in (1, 2, 3)]
    for _ in range(3):
        c.module.acquire_sample(c.sensors, c.path)
    records = read(c.path)
    assert len(c.module.accepted_samples(records, CONTEXT, complete_chain=True)) == 3
    if tamper == "omit":
        records.pop(1)
    elif tamper == "reorder":
        records[1:] = reversed(records[1:])
    elif tamper == "duplicate":
        records[1] = records[0]
    elif tamper == "previous":
        records[1]["episode"]["previous_episode_sha256"] = "0" * 64
    elif tamper == "context":
        records[1]["sample"]["acquisition_context"]["image_id"] = "foreign"
    elif tamper == "mix":
        records[1] = records[1]["sample"]
    elif tamper == "truncate":
        records = records[1:]
    with pytest.raises(ValueError):
        c.module.accepted_samples(records, CONTEXT, complete_chain=True)


def test_shared_sustained_ticks_break_at_reacquisition(harness_module):
    module = harness_module("benchmark_observers")
    assert module.shared_assessment([40] * 10, [100, 100])["observed"] is True
    assert (
        module.shared_assessment([40] * 10, [100, 100], breaks=[False, True])[
            "observed"
        ]
        is False
    )
    assert (
        module.shared_assessment(
            [40] * 10, [100, 100, 100], breaks=[False, True, False]
        )["observed"]
        is True
    )


def test_baseline_keeps_ten_accepted_and_all_rejections(recovery, harness_module):
    c = recovery
    cli = harness_module("benchmark")
    c.values[:] = [v2(disagreement(0)), v2(sample(0.134))] + [
        v2(sample(i)) for i in range(1, 10)
    ]
    # A low idle NVML disagreeing with PDH, without changing idle threshold.
    c.values[0] = v2(sample(0))
    c.values[0]["nvml"]["used_mb"] = 1500
    result = cli.observed_baseline(
        c.sensors, c.path.parent, interval=0, sleep=lambda _: None
    )
    assert len(result) == 10 and len(c.calls) == 11
    baseline = c.path.parent / "baseline.ndjson"
    assert len(read(baseline)) == 10
    assert len(read(baseline.with_name("baseline.ndjson.originals.ndjson"))) == 11


def test_cleanup_records_raw_without_accepting_failed_sensors(recovery):
    c = recovery
    failed = {"errors": ["windows_unavailable"]}
    c.values[:] = [failed]
    assert c.module.acquire_sample(c.sensors, c.path, enforce=False) == failed
    assert not c.path.exists() and not hasattr(c.sensors, "previous_sample")
    assert read(c.path.with_name(c.path.name + ".originals.ndjson")) == [failed]


@pytest.mark.parametrize(
    "tamper", ["omit_raw", "omit_episode", "missing_raw", "missing_accepted"]
)
def test_metrics_read_requires_every_persisted_original(recovery, tamper):
    c = recovery
    c.values[:] = [v2(disagreement(1)), v2(sample(1.134, 8996))]
    c.module.acquire_sample(c.sensors, c.path)
    assert c.module.read_acquisitions(c.path, CONTEXT) == read(c.path)
    raw_path = c.path.with_name(c.path.name + ".originals.ndjson")
    if tamper == "omit_raw":
        raw_path.write_text(json.dumps(read(raw_path)[-1]) + "\n")
    elif tamper == "omit_episode":
        c.path.with_name(c.path.name + ".episodes.ndjson").write_text("")
    elif tamper == "missing_raw":
        raw_path.unlink()
    else:
        c.path.unlink()
    with pytest.raises(ValueError, match="original_evidence"):
        c.module.read_acquisitions(c.path, CONTEXT)


def test_valid_first_sample_never_consumes_extra_query(recovery):
    c = recovery
    c.values[:] = [v2(sample(1)), v2(sample(2))]
    assert c.module.acquire_sample(c.sensors, c.path) == v2(sample(1))
    assert len(c.calls) == 1 and len(c.values) == 1
    with pytest.raises(ValueError, match="unnecessary_retry"):
        c.module.episode_decision([v2(sample(1)), v2(sample(2))], CONTEXT)


def test_v2_runner_cannot_fall_back_to_unguarded_legacy_observers(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    calls = []

    class Api:
        def request(self, *args):
            calls.append(args)
            return {"job_id": "j"}

        def events(self, *args, **kwargs):
            return [{"seq": 1, "job_id": "j", "type": "error", "data": {}}]

    with pytest.raises(ValueError, match="observer_policy_context"):
        runner.execute_run(
            {
                "observation_method": "wddm_auto_v2",
                "timeouts": {"observation_s": 1},
                "observer_policy": {"interval_s": 0},
            },
            {"job_id": "j"},
            Api(),
            SimpleNamespace(sample=lambda: {"errors": []}),
            tmp_path,
            {},
        )
    assert not calls


def test_episode_deadline_includes_browser_after_last_windows_query(recovery):
    c = recovery
    second = v2(sample(2, 8996))
    second["operations"]["browser"]["finished_utc"] = sample(3.001)["timestamp"]
    second["operations"]["browser"]["finished_monotonic_ns"] = sample(3.001)[
        "monotonic_ns"
    ]
    c.values[:] = [v2(disagreement(1)), second]
    with pytest.raises(ValueError, match="episode_deadline"):
        c.module.acquire_sample(c.sensors, c.path)
    assert len(c.calls) == 2 and not c.path.exists()


@pytest.mark.parametrize("delayed_attempt", [1, 2])
def test_persistence_time_is_included_in_fixed_episode_deadline(
    recovery, monkeypatch, delayed_attempt
):
    c = recovery
    runner = __import__("benchmark_runner")
    completion = [1.01]
    acquire, persist = c.sensors.sample, runner.append_record

    def sample_at_clock():
        value = acquire()
        completion[0] = float(
            c.module.acquisition_end(value) - c.module.stamp(NOW.isoformat())
        )
        return value

    def delayed_persistence(path, value):
        persist(path, value)
        if str(path).endswith(".originals.ndjson") and len(c.calls) == delayed_attempt:
            completion[0] += 2.1

    c.sensors.sample = sample_at_clock
    monkeypatch.setattr(c.module, "utc_now", lambda: sample(completion[0])["timestamp"])
    monkeypatch.setattr(
        c.module.time, "perf_counter_ns", lambda: int((1000 + completion[0]) * 1e9)
    )
    monkeypatch.setattr(runner, "append_record", delayed_persistence)
    monkeypatch.setattr(
        c.module,
        "episode_clock",
        lambda: (c.module.utc_now(), c.module.time.perf_counter_ns()),
    )
    c.values[:] = [v2(disagreement(1)), v2(sample(1.134, 8996))]
    with pytest.raises(ValueError, match="episode_deadline"):
        c.module.acquire_sample(c.sensors, c.path)
    assert len(c.calls) == delayed_attempt and not c.path.exists()


def test_v2_policy_preserves_every_legacy_numeric_limit(harness_module):
    module = harness_module("benchmark_observation")
    legacy, new = module.observation_policy(), module.observation_policy("wddm_auto_v2")
    assert all(new[key] == value for key, value in legacy.items() if key != "version")
    assert new["reacquisition_max_retries"] == 2 and new["episode_max_s"] == 2
    assert module.policy_hash(legacy) != module.policy_hash(new)
    assert module.validate_policy(new) == new
    assert module.confidence("wddm_auto_v2")["shared_independent_validation"] is False


def test_calibration_lifecycle_waits_for_all_queries(harness_module):
    module = harness_module("benchmark_observation")
    phases = {
        name: [v2(sample(i, 8000 if name == "loaded" else 1200)) for i in ticks]
        for name, ticks in {
            "baseline": range(10),
            "loaded": range(11, 21),
            "unloaded": range(22, 32),
        }.items()
    }
    lifecycle = {
        "loaded": {
            "event": "done",
            "job_id": "j",
            "observed_at": sample(10)["timestamp"],
        },
        "unloaded": {
            "event": "health_unloaded",
            "loaded": None,
            "observed_at": sample(21)["timestamp"],
        },
    }
    assert (
        module.validate_calibration(
            phases,
            lifecycle,
            CONTEXT,
            now=NOW + timedelta(seconds=32),
            method="wddm_auto_v2",
        )["method"]
        == "wddm_auto_v2"
    )
    phases["baseline"][-1]["operations"]["browser"]["finished_utc"] = sample(10.1)[
        "timestamp"
    ]
    phases["baseline"][-1]["operations"]["browser"]["finished_monotonic_ns"] += (
        1_090_000_000
    )
    with pytest.raises(ValueError, match="phase_transition"):
        module.validate_calibration(
            phases,
            lifecycle,
            CONTEXT,
            now=NOW + timedelta(seconds=32),
            method="wddm_auto_v2",
        )


def sealed_calibration(c, prepared=None):
    from benchmark_plan import matrix_runs, source_hashes

    root, module = c.path.parent, c.module
    (root / "models").mkdir(exist_ok=True)
    (root / "models/models.lock.json").write_text("{}")
    (root / "scripts/eval").mkdir(parents=True, exist_ok=True)
    (root / "scripts/eval/benchmark.py").write_text("# CPU synthetic source")
    context = copy.deepcopy(CONTEXT)
    context["source_hashes"] = source_hashes(root)
    context["lock_sha256"] = module.file_hash(root / "models/models.lock.json")
    if prepared is not None:
        context.update(
            {
                key: prepared[key]
                for key in (
                    "session_id",
                    "plan_sha256",
                    "source_hashes",
                    "image_id",
                    "lock_sha256",
                )
            }
        )
    c.sensors.observation_context = context
    c.sensors.continuity_path = root / "continuity.ndjson"
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
        observation_method="wddm_auto_v2",
        runs=matrix_runs(),
        observation_policy_sha256=module.policy_hash(
            module.observation_policy("wddm_auto_v2")
        ),
    )
    if prepared is not None:
        plan = prepared

    def bind(value):
        value["acquisition_context"] = module.acquisition_context(
            context, "wddm_auto_v2"
        )
        return value

    def seal(path):
        return {
            "path": path.name,
            "sha256": module.file_hash(path),
            "bytes": path.stat().st_size,
        }

    def save(name, value):
        path = root / name
        path.write_text(json.dumps(value))
        return seal(path)

    evidence = {}
    for phase, ticks in {
        "baseline": range(10),
        "loaded": range(11, 21),
        "unloaded": range(22, 32),
    }.items():
        c.sensors.phase_started_utc = (
            None
            if phase == "baseline"
            else sample(10.01 if phase == "loaded" else 21.01)["timestamp"]
        )
        for tick in ticks:
            raw = bind(sample(tick, 8000 if phase == "loaded" else 1200))
            c.values[:] = [raw]
            if phase == "loaded" and tick == 11:
                rejected = copy.deepcopy(raw)
                rejected["nvml"]["used_mb"] = 8300
                c.values[:] = [rejected, bind(sample(11.134, 8000))]
            module.acquire_sample(
                c.sensors, root / (phase + ".ndjson"), idle=phase != "loaded"
            )
        path = root / (phase + ".ndjson")
        evidence[phase] = {
            **seal(path),
            "originals": seal(root / (phase + ".ndjson.originals.ndjson")),
            "episodes": seal(root / (phase + ".ndjson.episodes.ndjson")),
        }
    lifecycle = {}
    for phase, tick in (("loaded", 10), ("unloaded", 21)):
        response = (
            {"loaded": {"model_id": "CPU", "mode": "bf16"}}
            if phase == "loaded"
            else {"loaded": None, "state": "idle"}
        )
        proof = save(
            phase + "-proof.json",
            bind(
                {
                    "response": response,
                    "started_utc": sample(tick)["timestamp"],
                    "finished_utc": sample(tick + 0.01)["timestamp"],
                }
            ),
        )
        lifecycle[phase] = bind(
            {
                "event": "health_loaded" if phase == "loaded" else "health_unloaded",
                "observed_at": sample(tick + 0.01)["timestamp"],
                "proof": proof,
                **({"job_id": "CPU"} if phase == "loaded" else {"loaded": None}),
            }
        )
    evidence["lifecycle"] = save("lifecycle.json", lifecycle)
    evidence["host"] = save(
        "host.json",
        bind(
            {
                k: context[k]
                for k in (
                    "driver_version",
                    "windows_build",
                    "nvml_uuid",
                    "adapter_luid",
                    "browser_identity",
                )
            }
        ),
    )
    evidence["continuity"] = seal(c.sensors.continuity_path)
    viewport = bind(
        {
            "url": "about:blank",
            "tab_id": "CPU",
            "browser_id": "CPU",
            "visible": True,
            "observed_at": sample(0)["timestamp"],
        }
    )
    viewport["evidence"] = save("viewport.json", copy.deepcopy(viewport))
    observation = {
        "method": "wddm_auto_v2",
        "policy": module.observation_policy("wddm_auto_v2"),
        "policy_sha256": plan["observation_policy_sha256"],
        "context": context,
        "evidence": evidence,
        "viewport": viewport,
        "binding": "unproven",
    }
    return root, observation, plan


def test_sealed_v2_calibration_has_ten_accepts_per_phase_and_retains_rejections(
    recovery,
):
    c = recovery
    root, observation, plan = sealed_calibration(c)
    result = c.module.validate_auto(observation, root, plan=plan)
    assert result["method"] == "wddm_auto_v2"
    assert len(read(root / "loaded.ndjson")) == 10
    assert len(read(root / "loaded.ndjson.originals.ndjson")) == 11
    continued = read(root / "continuity.ndjson")
    assert (
        c.module.validate_auto(
            observation, root, plan=plan, continued_samples=continued
        )["shared_validation_level"]
        == "provider_verified"
    )
    originals = {
        key: observation["evidence"][key]["path"] for key in observation["evidence"]
    }
    built = c.module.build_auto_prerequisites(
        plan,
        observation["context"],
        originals,
        "viewport.json",
        root=root,
        exclusive_gpu_authorized=True,
    )
    assert built["observation"]["policy"] == observation["policy"]


@pytest.mark.parametrize(
    "tamper",
    [
        "raw_omit",
        "raw_order",
        "raw_dupe",
        "episode_omit",
        "context",
        "chain_omit",
        "prefix",
        "policy_label",
        "source_omit",
        "matrix",
    ],
)
def test_sealed_v2_offline_rejects_resealed_omission_or_claim(recovery, tamper):
    c = recovery
    root, observation, plan = sealed_calibration(c)
    item = observation["evidence"]["loaded"]
    if tamper in {"raw_omit", "raw_order", "raw_dupe"}:
        target = item["originals"]
        values = read(root / target["path"])
        if tamper == "raw_omit":
            values.pop(0)
        elif tamper == "raw_order":
            values.reverse()
        else:
            values[1] = values[0]
    elif tamper == "episode_omit":
        target = item["episodes"]
        values = read(root / target["path"])[1:]
    elif tamper == "chain_omit":
        target = observation["evidence"]["continuity"]
        values = read(root / target["path"])
        values.pop(1)
    elif tamper == "prefix":
        values = read(root / "continuity.ndjson")[1:]
        with pytest.raises(ValueError):
            c.module.validate_auto(
                observation, root, plan=plan, continued_samples=values
            )
        return
    elif tamper == "context":
        observation["context"]["image_id"] = "foreign"
    elif tamper == "policy_label":
        observation["method"] = "wddm_auto_v1"
    elif tamper == "source_omit":
        observation["context"]["source_hashes"] = plan["source_hashes"] = {}
    elif tamper == "matrix":
        plan["runs"].pop()
    if tamper in {"raw_omit", "raw_order", "raw_dupe", "episode_omit", "chain_omit"}:
        path = root / target["path"]
        path.write_text("\n".join(json.dumps(value) for value in values) + "\n")
        target.update(sha256=c.module.file_hash(path), bytes=path.stat().st_size)
    with pytest.raises(ValueError):
        c.module.validate_auto(observation, root, plan=plan)


@pytest.mark.parametrize("resume", [False, True])
def test_runner_recovers_transient_without_duplicate_inference_or_resume_submit(
    recovery, harness_module, resume
):
    c = recovery
    runner = harness_module("benchmark_runner")
    calls = []
    c.values[:] = [v2(disagreement(0)), v2(sample(0.134, 8996))] + [
        v2(sample(0.3 + i * 0.15, 8996)) for i in range(40)
    ]

    class Api:
        def request(self, method, path, body=None):
            calls.append((method, path))
            return {"job_id": "j", "state": "generating"}

        def events(self, *args, **kwargs):
            return [{"seq": 1, "job_id": "j", "type": "error", "data": {}}]

    plan = {
        "observation_method": "wddm_auto_v2",
        "timeouts": {"observation_s": 2},
        "observer_policy": {"interval_s": 0},
    }
    if resume:
        runner.exclusive_json(c.path.parent / "submission-intent.json", {"job_id": "j"})
    for _ in range(2):
        assert (
            runner.execute_run(
                plan, {"job_id": "j"}, Api(), c.sensors, c.path.parent, {"job_id": "j"}
            )["type"]
            == "error"
        )
    assert calls.count(("POST", "/v1/jobs")) == (0 if resume else 1)
    assert calls == (
        [("GET", "/v1/jobs/j")]
        if resume
        else [("POST", "/v1/estimate"), ("POST", "/v1/jobs")]
    )
    originals = [
        value
        for path in c.path.parent.glob("*.originals.ndjson")
        for value in read(path)
    ]
    assert any(v["nvml"]["used_mb"] == 9304 for v in originals)
    assert c.sensors.previous_episode["ordinal"] >= 4


def test_new_plan_requires_exact_source_set_and_policy_version(
    harness_module, tmp_path
):
    from test_benchmark_integration_cpu import prepared_plan

    planner = harness_module("benchmark_plan")
    old = prepared_plan(planner, tmp_path)
    inputs = {
        "fixtures_by_duration": {
            k: {"path": v["path"], "sha256": v["sha256"]}
            for k, v in old["fixtures_by_duration"].items()
        }
    }
    (tmp_path / "scripts/eval").mkdir(parents=True)
    source = tmp_path / "scripts/eval/benchmark.py"
    source.write_text("# CPU fixture")
    plan = planner.build_plan(
        inputs,
        image_id="CPU",
        prerequisites_sha256=None,
        root=tmp_path,
        observation_method="wddm_auto_v2",
    )
    planner.verify_plan(plan, tmp_path)
    assert len(plan["runs"]) == 160 and plan["source_hashes"] == planner.source_hashes(
        tmp_path
    )
    plan["source_hashes"] = {}
    plan["plan_sha256"] = planner.digest(
        {k: v for k, v in plan.items() if k != "plan_sha256"}
    )
    with pytest.raises(ValueError, match="complete_source"):
        planner.verify_plan(plan, tmp_path)


@pytest.mark.parametrize("preparation_gap", [0, 3])
def test_v2_session_preserves_owned_cleanup_and_fails_closed_on_preparation_gap(
    recovery, harness_module, monkeypatch, preparation_gap
):
    import threading

    from benchmark_plan import configurations

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
            clock.t += preparation_gap
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
    if preparation_gap:
        with pytest.raises(ValueError, match="replayed_or_paused"):
            cli.run_session(plan, folder, prerequisites, **kwargs)
        assert not any(path == "/v1/jobs" for _, path, _ in calls)
        assert len(list(folder.glob("groups/*/baseline.ndjson.originals.ndjson"))) == 1
    else:
        rows = cli.run_session(plan, folder, prerequisites, **kwargs)
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


@pytest.mark.parametrize("outcome", ["rows", "timeout", "guard_failure"])
def test_v2_cli_resumes_exact_sealed_plan_and_keeps_incomplete_output_truthful(
    recovery, harness_module, monkeypatch, outcome
):
    c = recovery
    planner, cli = harness_module("benchmark_plan"), harness_module("benchmark")
    root = c.path.parent
    (root / "models").mkdir()
    (root / "models/models.lock.json").write_text("{}")
    (root / "scripts/eval").mkdir(parents=True)
    (root / "scripts/eval/benchmark.py").write_text("# CPU synthetic source")
    inputs = {"fixtures_by_duration": {}}
    for duration in planner.DURATIONS:
        path = root / f"input-{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "duration_s": duration,
                        "lyrics": "CPU original",
                        "style": "CPU",
                        "language": "es",
                    },
                }
            )
        )
        inputs["fixtures_by_duration"][str(duration)] = {
            "path": path.name,
            "sha256": planner.file_hash(path),
        }
    plan = planner.build_plan(
        inputs,
        image_id=CONTEXT["image_id"],
        prerequisites_sha256=None,
        root=root,
        observation_method="wddm_auto_v2",
    )
    root, observation, plan = sealed_calibration(c, prepared=plan)
    folder = root / ".cache/dev-cycle/t09/runtime" / plan["session_id"]
    folder.mkdir(parents=True)
    cli.exclusive_json(folder / "plan.json", plan)
    plan_original = (folder / "plan.json").read_bytes()
    prerequisites = root / "prerequisites.json"
    cli.exclusive_json(
        prerequisites,
        {
            "observation": observation,
            "browser": CONTEXT["browser_identity"],
            "exclusive_gpu_authorized": True,
        },
    )
    calls = []

    def measured(plan, folder, prerequisites, **kwargs):
        calls.append(plan)
        assert kwargs["resume"] is True and len(plan["runs"]) == 160
        assert prerequisites["accreditation"]["method"] == "wddm_auto_v2"
        if outcome == "timeout":
            raise cli.ObservationTimeout("owned_job_preserved")
        if outcome == "guard_failure":
            (folder / "groups").mkdir()
            raise ValueError("observability_lost_auto_episode_deadline_exhausted")
        return []

    monkeypatch.setattr(cli, "run_session", measured)
    argv = ["--resume", plan["session_id"], "--prerequisites", str(prerequisites)]
    result = cli.main(
        argv, root=root, backend=SimpleNamespace(image_id=lambda image: image)
    )
    assert result == (75 if outcome == "timeout" else 2) and calls == [plan]
    assert (folder / "plan.json").read_bytes() == plan_original
    public = root / "eval/results/benchmark-5070.md"
    if outcome != "timeout":
        assert "wddm_auto_v2" in public.read_text()
        assert "provider_verified" in public.read_text()
        assert "shared_independent_validation=false" in public.read_text()
    if outcome == "rows":
        assert json.loads((folder / "summary.json").read_text())["complete"] is False
        assert cli.main(argv, root=root, backend=SimpleNamespace()) == 2
        assert calls == [plan]
