"""Calibración sintética CPU; episodios, proceso y relojes reales, sin GPU."""

import copy
import importlib.util
import inspect
import json
import threading
from pathlib import Path

import benchmark_observation as observation
import pytest
from benchmark_clock import utc_now
from benchmark_plan import digest, file_hash, source_hashes

PRIVATE = Path.cwd() / ".cache/dev-cycle/t09/v3-calibration-adapter-implementation"


@pytest.fixture(scope="module")
def calibration():
    spec = importlib.util.spec_from_file_location(
        "private_episode_fixture", PRIVATE / "test_benchmark_episode_v3.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    make = module.episode_factory.__wrapped__()
    observer, context = make()
    # Replace the trusted CPU fixture before starting its replacement process.
    observer.close()
    context["source_hashes"] = source_hashes(Path.cwd())
    context["lock_sha256"] = file_hash(Path.cwd() / "models/models.lock.json")
    context_path = observer.root.parents[1] / "context.json"
    context_path.write_text(json.dumps(context), encoding="utf-8")
    fixture = max(
        module.PHASE.glob("v3-fixtures/*/sensor_fixture.py"),
        key=lambda p: p.stat().st_mtime_ns,
    )
    text = fixture.read_text(encoding="utf-8")
    text = text.replace(
        "raw=values.sample(0)",
        'raw=values.sample(0, 8000 if Path(__file__).with_name("phase.txt").read_text()=="loaded" else 1200)',
    )
    fixture.write_text(text, encoding="utf-8")
    fixture.with_name("phase.txt").write_text("baseline", encoding="utf-8")
    observer, context = make()
    phases = {}
    lifecycle = {}
    proofs = {}
    viewport_at = utc_now()
    try:
        for phase in ("baseline", "loaded", "unloaded"):
            fixture.with_name("phase.txt").write_text(phase, encoding="utf-8")
            if phase != "baseline":
                observed = utc_now()
                proofs[phase] = {
                    "started_utc": observed,
                    "finished_utc": observed,
                    "response": {
                        "loaded": {"model_id": "synthetic-cpu", "mode": "bf16"}
                    }
                    if phase == "loaded"
                    else {"loaded": None, "state": "idle"},
                    "acquisition_context": observation.acquisition_context(
                        context, "wddm_auto_v3"
                    ),
                    "test_scope": "CPU synthetic lifecycle; no engine or GPU load",
                }
                lifecycle[phase] = {
                    "event": "health_loaded"
                    if phase == "loaded"
                    else "health_unloaded",
                    "job_id": "synthetic-cpu-lifecycle",
                    "observed_at": observed,
                    **({"loaded": None} if phase == "unloaded" else {}),
                }
                observer.phase_started_utc = observed
            refs = []
            for _ in range(10):
                observer.acquire(phase, idle=phase != "loaded")
                receipt = observer.receipts[-1]
                refs.append(
                    {
                        "episode_id": receipt["episode_id"],
                        "receipt_sha256": digest(receipt),
                    }
                )
            phases[phase] = refs
        for phase, proof in proofs.items():
            path = observer.root.parent / (phase + "-standalone-proof.json")
            path.write_text(json.dumps(proof), encoding="utf-8")
            lifecycle[phase]["proof"] = {
                "path": path.relative_to(Path.cwd()).as_posix(),
                "sha256": file_hash(path),
                "bytes": path.stat().st_size,
            }
            lifecycle[phase]["acquisition_context"] = observation.acquisition_context(
                context, "wddm_auto_v3"
            )
        yield (
            {
                "root": observer.root,
                "receipts": copy.deepcopy(observer.receipts),
                "attempts": copy.deepcopy(observer.attempts),
                "phases": phases,
            },
            lifecycle,
            context,
            proofs,
            viewport_at,
        )
    finally:
        observer.close()


def validate(case, lifecycle, context, **kwargs):
    # RED harness exercises the existing discriminator, rather than failing on
    # a keyword unsupported by the old API. Once added, both anchors are passed.
    parameters = inspect.signature(observation.validate_calibration).parameters
    kwargs = {key: value for key, value in kwargs.items() if key in parameters}
    return observation.validate_calibration(
        case,
        lifecycle,
        context,
        method="wddm_auto_v3",
        now=observation.stamp(utc_now()),
        **kwargs,
    )


def test_actual_v3_production_calibration_accepts_full_anchored_chain(calibration):
    case, lifecycle, context, _, _ = calibration
    result = validate(
        case,
        lifecycle,
        context,
        trusted_receipts=copy.deepcopy(case["receipts"]),
        trusted_attempts=copy.deepcopy(case["attempts"]),
    )
    assert result["recovered_at"]
    assert result["shared_independent_validation"] is False


def test_self_declared_receipts_are_not_trusted(calibration):
    case, lifecycle, context, _, _ = calibration
    with pytest.raises(ValueError, match="supervisor"):
        validate(case, lifecycle, context)


@pytest.mark.parametrize(
    "change",
    [
        "omit",
        "duplicate",
        "phase_order",
        "phase_time",
        "context",
        "raw",
        "late_commit",
        "replay",
        "omitted_attempt",
        "missing_proof",
        "failed_lifecycle",
    ],
)
def test_v3_rejects_actual_publication_or_phase_tampering(calibration, change):
    original, lifecycle, context, _, _ = calibration
    case, lifecycle, context = (
        copy.deepcopy(original),
        copy.deepcopy(lifecycle),
        copy.deepcopy(context),
    )
    anchors = copy.deepcopy(original["receipts"])
    attempts = copy.deepcopy(original["attempts"])
    restore = None
    if change == "omit":
        case["receipts"].pop()
    elif change == "duplicate":
        case["phases"]["loaded"][0] = case["phases"]["baseline"][0]
    elif change == "phase_order":
        case["phases"]["loaded"].reverse()
    elif change == "phase_time":
        lifecycle["loaded"]["observed_at"] = lifecycle["unloaded"]["observed_at"]
    elif change == "context":
        context["session_id"] = "another-epoch"
    elif change == "late_commit":
        case["receipts"][0]["observed_monotonic_ns"] = (
            case["receipts"][0]["deadline_ns"] + 1
        )
        anchors = copy.deepcopy(case["receipts"])
        case["attempts"][0]["receipt"] = copy.deepcopy(case["receipts"][0])
        attempts = copy.deepcopy(case["attempts"])
    elif change == "replay":
        case["receipts"].append(case["receipts"][0])
        anchors = copy.deepcopy(case["receipts"])
    elif change == "omitted_attempt":
        case["attempts"].pop()
    elif change == "missing_proof":
        lifecycle["loaded"].pop("proof")
    elif change == "failed_lifecycle":
        lifecycle["unloaded"]["event"] = "failed"
    elif change == "raw":
        path = case["root"] / case["receipts"][0]["episode_id"] / "raw-1.json"
        restore = path, path.read_bytes()
        value = json.loads(restore[1])
        value["errors"] = ["altered"]
        path.write_text(json.dumps(value), encoding="utf-8")
    try:
        with pytest.raises(ValueError):
            validate(
                case,
                lifecycle,
                context,
                trusted_receipts=anchors,
                trusted_attempts=attempts,
            )
    finally:
        if restore:
            restore[0].write_bytes(restore[1])


@pytest.fixture
def auto_case(calibration):
    case, lifecycle, context, proofs, viewport_at = copy.deepcopy(calibration)
    folder = case["root"].parent / (
        "auto-" + case["phases"]["baseline"][0]["episode_id"]
    )
    folder.mkdir(exist_ok=True)

    def seal(name, value):
        path = folder / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return {
            "path": path.relative_to(Path.cwd()).as_posix(),
            "sha256": file_hash(path),
            "bytes": path.stat().st_size,
        }

    evidence = {p: seal(p + ".json", refs) for p, refs in case["phases"].items()}
    for phase in proofs:
        lifecycle[phase]["proof"] = seal(phase + "-proof.json", proofs[phase])
        lifecycle[phase]["acquisition_context"] = observation.acquisition_context(
            context, "wddm_auto_v3"
        )
    evidence["lifecycle"] = seal("lifecycle.json", lifecycle)
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
    host["acquisition_context"] = observation.acquisition_context(
        context, "wddm_auto_v3"
    )
    evidence["host"] = seal("host.json", host)
    evidence["publications"] = seal(
        "publications.json",
        {
            k: (
                case["root"].relative_to(Path.cwd()).as_posix()
                if k == "root"
                else case[k]
            )
            for k in ("root", "receipts", "attempts")
        },
    )
    view = {
        "url": "about:blank",
        "tab_id": "synthetic-own",
        "browser_id": "synthetic-browser",
        "visible": True,
        "observed_at": viewport_at,
        "acquisition_context": observation.acquisition_context(context, "wddm_auto_v3"),
    }
    obs = {
        "method": "wddm_auto_v3",
        "policy": observation.observation_policy("wddm_auto_v3"),
        "policy_sha256": observation.policy_hash(
            observation.observation_policy("wddm_auto_v3")
        ),
        "context": context,
        "evidence": evidence,
        "viewport": {**view, "evidence": seal("viewport.json", view)},
        "binding": "unproven",
    }
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
        observation_method="wddm_auto_v3",
        observation_policy_sha256=obs["policy_sha256"],
        runs=[{} for _ in range(160)],
    )
    return obs, plan, case


def auto_validate(obs, plan, case, **kwargs):
    anchors = {
        "trusted_receipts": copy.deepcopy(case["receipts"]),
        "trusted_attempts": copy.deepcopy(case["attempts"]),
    }
    anchors.update(kwargs)
    parameters = inspect.signature(observation.validate_auto).parameters
    anchors = {k: v for k, v in anchors.items() if k in parameters}
    return observation.validate_auto(obs, Path.cwd(), plan=plan, **anchors)


def test_auto_v3_and_existing_builder_accept_supervised_evidence(auto_case):
    obs, plan, case = auto_case
    assert auto_validate(obs, plan, case)["context"] == obs["context"]
    result = observation.build_auto_prerequisites(
        plan,
        obs["context"],
        {k: v["path"] for k, v in obs["evidence"].items()},
        obs["viewport"]["evidence"]["path"],
        root=Path.cwd(),
        exclusive_gpu_authorized=True,
        trusted_receipts=case["receipts"],
        trusted_attempts=case["attempts"],
    )
    assert result["observation"] == obs


def test_auto_prerequisite_incomplete_retains_shape_cause(auto_case):
    obs, plan, case = auto_case
    obs["viewport"].pop("evidence")
    with pytest.raises(ValueError, match=r"auto_prerequisite_incomplete:KeyError:.*evidence"):
        auto_validate(obs, plan, case)


@pytest.mark.parametrize(
    "change",
    [
        "missing_anchors",
        "incomplete160",
        "source_subset",
        "browser",
        "binding",
        "image",
        "viewport",
        "lifecycle",
        "continued_summary",
        "v2_promotion",
    ],
)
def test_auto_v3_common_gates_still_fail_closed(auto_case, change):
    obs, plan, case = auto_case
    kwargs = {}
    if change == "missing_anchors":
        kwargs.update(trusted_receipts=None, trusted_attempts=None)
    elif change == "incomplete160":
        plan["runs"].pop()
    elif change == "source_subset":
        obs["context"]["source_hashes"].pop(next(iter(obs["context"]["source_hashes"])))
        plan["source_hashes"] = obs["context"]["source_hashes"]
    elif change == "browser":
        obs["context"]["browser_identity"]["pid"] += 1
    elif change == "binding":
        obs["binding"] = "proven"
    elif change == "image":
        plan["image_id"] = "different"
    elif change == "viewport":
        obs["viewport"]["visible"] = False
    elif change == "lifecycle":
        path = Path(obs["evidence"]["lifecycle"]["path"])
        value = json.loads(path.read_text())
        value["unloaded"]["event"] = "failed"
        path.write_text(json.dumps(value))
        obs["evidence"]["lifecycle"].update(
            sha256=file_hash(path), bytes=path.stat().st_size
        )
    elif change == "continued_summary":
        kwargs["continued_samples"] = [{"schema": "validated_v3_summary"}]
    elif change == "v2_promotion":
        obs["method"] = "wddm_auto_v2"
    with pytest.raises(ValueError):
        auto_validate(obs, plan, case, **kwargs)


@pytest.mark.parametrize(
    "change",
    [
        "plain_samples",
        "empty_inventory",
        "outside_root",
        "phase_count",
        "phase_seal",
        "unknown_field",
        "expired",
        "future",
        "proof_time",
        "unload_failed",
        "loaded_missing_model",
    ],
)
def test_standalone_v3_is_not_a_summary_or_freshness_bypass(calibration, change):
    case, lifecycle, context, _, _ = copy.deepcopy(calibration)
    now = observation.stamp(utc_now())
    restore = None
    if change == "plain_samples":
        case = {"baseline": [{}] * 10, "loaded": [{}] * 10, "unloaded": [{}] * 10}
    elif change == "empty_inventory":
        case["attempts"] = []
    elif change == "outside_root":
        case["root"] = Path.cwd().parent
    elif change == "phase_count":
        case["phases"]["baseline"].pop()
    elif change == "phase_seal":
        case["phases"]["loaded"][0]["receipt_sha256"] = "0" * 64
    elif change == "unknown_field":
        case["phases"]["loaded"][0]["self_attested"] = True
    elif change == "expired":
        now += 901
    elif change == "future":
        now -= 901
    else:
        phase = "unloaded" if change == "unload_failed" else "loaded"
        path = Path(lifecycle[phase]["proof"]["path"])
        restore = path, path.read_bytes()
        proof = json.loads(restore[1])
        if change == "proof_time":
            proof["finished_utc"] = "2099-01-01T00:00:00+00:00"
        elif change == "unload_failed":
            proof["response"]["state"] = "error"
        else:
            proof["response"]["loaded"].pop("model_id")
        path.write_text(json.dumps(proof), encoding="utf-8")
        lifecycle[phase]["proof"].update(
            sha256=file_hash(path), bytes=path.stat().st_size
        )
    try:
        with pytest.raises(ValueError):
            observation.validate_calibration(
                case,
                lifecycle,
                context,
                method="wddm_auto_v3",
                now=now,
                trusted_receipts=calibration[0]["receipts"],
                trusted_attempts=calibration[0]["attempts"],
            )
    finally:
        if restore:
            restore[0].write_bytes(restore[1])


def test_real_full_chain_live_continuity_and_prior_accreditation():
    generator = calibration.__wrapped__()
    first = next(generator)
    observer = generator.gi_frame.f_locals["observer"]
    sensor_fixture = generator.gi_frame.f_locals["fixture"]
    stop, lock, errors = threading.Event(), threading.Lock(), []
    sampler = None
    try:
        prior, plan, prior_case = auto_case.__wrapped__(first)
        assert auto_validate(prior, plan, prior_case)["recovered_at"]
        # The first seal is captured before writing another accreditation, and
        # refers to its immutable 30-publication prefix, not a relabeled v2 file.
        prior_path = prior_case["root"].parent / "prior-accreditation.json"
        # auto_case(live) writes the same folder; rebuild a dedicated prefix seal.
        prefix = prior_case["root"].parent / "prior-publications.json"
        prefix.write_text(
            json.dumps(
                {
                    "root": prior_case["root"].relative_to(Path.cwd()).as_posix(),
                    "receipts": prior_case["receipts"],
                    "attempts": prior_case["attempts"],
                }
            ),
            encoding="utf-8",
        )
        prior["evidence"]["publications"] = {
            "path": prefix.relative_to(Path.cwd()).as_posix(),
            "sha256": file_hash(prefix),
            "bytes": prefix.stat().st_size,
        }
        prior_path.write_text(json.dumps(prior), encoding="utf-8")
        phases, lifecycle, proofs = {}, {}, {}
        for phase in ("baseline", "loaded", "unloaded"):
            sensor_fixture.with_name("phase.txt").write_text(phase, encoding="utf-8")
            observed = utc_now()
            observer.phase_started_utc = None if phase == "baseline" else observed
            if phase != "baseline":
                lifecycle[phase] = {
                    "event": "health_loaded"
                    if phase == "loaded"
                    else "health_unloaded",
                    "job_id": "synthetic-cpu-second-lifecycle",
                    "observed_at": observed,
                    "acquisition_context": observation.acquisition_context(
                        first[2], "wddm_auto_v3"
                    ),
                    **({"loaded": None} if phase == "unloaded" else {}),
                }
                proofs[phase] = {
                    **first[3][phase],
                    "started_utc": observed,
                    "finished_utc": observed,
                }
            refs = []
            for _ in range(10):
                observer.acquire(phase, idle=phase != "loaded")
                receipt = observer.receipts[-1]
                refs.append(
                    {
                        "episode_id": receipt["episode_id"],
                        "receipt_sha256": digest(receipt),
                    }
                )
            phases[phase] = refs
        second_case = {
            "root": observer.root,
            "receipts": copy.deepcopy(observer.receipts),
            "attempts": copy.deepcopy(observer.attempts),
            "phases": phases,
        }
        second, plan, case = auto_case.__wrapped__(
            (second_case, lifecycle, first[2], proofs, first[4])
        )
        second["previous_accreditation"] = {
            "path": prior_path.relative_to(Path.cwd()).as_posix(),
            "sha256": file_hash(prior_path),
            "bytes": prior_path.stat().st_size,
        }

        def sampling():
            try:
                while not stop.is_set():
                    with lock:
                        observer.acquire("continuity", idle=True)
                    stop.wait(0.1)
            except (ValueError, RuntimeError, OSError) as error:
                errors.append(str(error))

        sampler = threading.Thread(target=sampling)
        sampler.start()
        assert auto_validate(second, plan, case)["context"] == first[2]
        live_case = copy.deepcopy(second_case)
        with lock:
            live_case["receipts"] = copy.deepcopy(observer.receipts)
            live_case["attempts"] = copy.deepcopy(observer.attempts)
        live_obs, plan, live_case = auto_case.__wrapped__(
            (live_case, lifecycle, first[2], proofs, first[4])
        )
        assert auto_validate(
            live_obs, plan, live_case, continued_samples=live_case["receipts"]
        )["recovered_at"]
        for mutation in ("method", "context", "overlap"):
            modified = copy.deepcopy(prior)
            if mutation == "method":
                modified["method"] = "wddm_auto_v2"
            elif mutation == "context":
                modified["context"]["session_id"] = "other-epoch"
            else:
                modified["evidence"]["unloaded"] = second["evidence"]["unloaded"]
            prior_path.write_text(json.dumps(modified), encoding="utf-8")
            second["previous_accreditation"].update(
                sha256=file_hash(prior_path), bytes=prior_path.stat().st_size
            )
            with pytest.raises(ValueError):
                auto_validate(second, plan, case)
    finally:
        stop.set()
        if sampler is not None:
            sampler.join(timeout=3)
            assert not sampler.is_alive()
            assert errors == []
        generator.close()
