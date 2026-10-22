"""Plan privado del benchmark; ninguna medición ni importación de torch."""

import hashlib
import json
import secrets
import time
from pathlib import Path

DURATIONS = (30, 60, 180, 300)
CONFIGS = (
    ("turbo-lm06", "turbo", "0.6B", "bf16", 8, None),
    ("turbo-lm17", "turbo", "1.7B", "bf16", 8, None),
    ("sft-lm06", "sft", "0.6B", "bf16", 50, 7),
    ("base-lm06", "base", "0.6B", "bf16", 32, 7),
    ("xl-turbo-lm06-int8", "xl-turbo", "0.6B", "offload-int8", 8, None),
)
ROOT = Path(__file__).resolve().parents[2]
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_id():
    value = (time.time_ns() // 1_000_000 << 80) | secrets.randbits(80)
    return "".join(ALPHABET[(value >> shift) & 31] for shift in range(125, -1, -5))


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_hashes(root):
    return {
        str(p.relative_to(root).as_posix()): file_hash(p)
        for folder in (
            root / "scripts/eval",
            root / "apps/engines/acestep",
            root / "apps/engines/common/engine_common",
        )
        for p in sorted(folder.rglob("*.py"))
        if "tests" not in p.relative_to(root).parts
        and ".cache" not in p.relative_to(root).parts
    }


def project_path(value, root=ROOT):
    path = Path(value).resolve()
    if not path.is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError("path_outside_project")
    return path


def configurations():
    return [
        {
            "config_id": config,
            "model_id": f"ace-step-1.5-{variant}",
            "checkpoint": f"acestep-v15-{variant}",
            "lm": f"acestep-5Hz-lm-{lm}",
            "mode": mode,
            "params": {
                "inference_steps": steps,
                "shift": 1,
                **({"guidance_scale": cfg} if cfg else {}),
            },
            "lm_backend": "pt",
            "lm_context": 4096,
            "lm_cfg_scale": 2,
            "thinking": True,
            "compile": False,
        }
        for config, variant, lm, mode, steps, cfg in CONFIGS
    ]


def matrix_runs():
    runs = []
    for config_index, config in enumerate(configurations()):
        for duration_index, duration in enumerate(DURATIONS):
            arms = (
                ("bind", "container_copy")
                if (config_index + duration_index) % 2 == 0
                else ("container_copy", "bind")
            )
            for storage in arms:
                for repetition in range(4):
                    runs.append(
                        {
                            "run_id": new_id(),
                            "job_id": new_id(),
                            "config_id": config["config_id"],
                            "duration_s": duration,
                            "storage": storage,
                            "mode": config["mode"],
                            "phase": "process_cold" if repetition == 0 else "warm",
                            "repetition": repetition,
                        }
                    )
    return runs


def validate_input(value, duration):
    if (
        not isinstance(value.get("authorship"), dict)
        or value["authorship"].get("declared") is not True
        or value["authorship"].get("basis")
        not in {"original", "authorized", "public_domain"}
    ):
        raise ValueError("authorship_required")
    if set(value) - {"task", "params", "authorship"}:
        raise ValueError("reused_or_unknown_input_fields")
    params = value.get("params", {})
    allowed = {
        "style",
        "lyrics",
        "duration_s",
        "language",
        "vocal_language",
        "bpm",
        "key",
        "time_signature",
        "negative_prompt",
    }
    if not isinstance(params, dict) or set(params) - allowed:
        raise ValueError("reused_or_unknown_params")
    if (
        type(params.get("duration_s")) not in {int, float}
        or params["duration_s"] != duration
    ):
        raise ValueError("duration_mismatch")
    if (
        value.get("task") != "music.song"
        or not isinstance(params.get("lyrics"), str)
        or not params["lyrics"]
        or not params.get("style")
        or not params.get("language")
    ):
        raise ValueError("song_input_required")
    return value


def build_plan(
    inputs,
    *,
    image_id,
    prerequisites_sha256,
    root=ROOT,
    observation_method="wddm_auto_v3",
):
    """Inputs JSON: fixtures_by_duration: {"30": {path, sha256}, ...}."""
    if set(inputs.get("fixtures_by_duration", {})) != {str(d) for d in DURATIONS}:
        raise ValueError("all_durations_required")
    fixtures = {}
    for duration in DURATIONS:
        item = inputs["fixtures_by_duration"][str(duration)]
        path = project_path(root / item["path"], root)
        actual = file_hash(path)
        if actual != item["sha256"]:
            raise ValueError("fixture_hash_mismatch")
        value = validate_input(
            json.loads(path.read_text(encoding="utf-8-sig")), duration
        )
        fixtures[str(duration)] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": actual,
            "input_sha256": digest(value),
            "fixture_id": f"fixture-{duration}",
        }
    sources = source_hashes(root)
    lock = root / "models/models.lock.json"
    plan = {
        "schema_version": 1,
        "session_id": new_id(),
        "matrix": "default",
        "seed": 1,
        "n_outputs": 1,
        "batch_size": 1,
        "durations_s": list(DURATIONS),
        "configs": configurations(),
        "runs": matrix_runs(),
        "fixtures_by_duration": fixtures,
        "source_hashes": sources,
        "lock_sha256": file_hash(lock),
        "image_id": image_id,
        "prerequisites_sha256": prerequisites_sha256,
        "repeat_policy": {"process_cold": 1, "warm": 3},
        "filesystem_cache": "uncontrolled",
        "timeouts": {"job_s": 3600, "observation_s": 3700},
        "observer_policy": {
            "interval_s": 1,
            "baseline_samples": 10,
            "margin_mb": 512,
            "max_idle_used_mb": 1600,
            "minimum_shared_tolerance_mb": 32,
        },
    }
    if observation_method not in {
        "task_manager_v1",
        "wddm_auto_v1",
        "wddm_auto_v2",
        "wddm_auto_v3",
    }:
        raise ValueError("observation_method_unknown")
    plan["observation_method"] = observation_method
    if observation_method in {"wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"}:
        from benchmark_observation import observation_policy, policy_hash

        plan["observation_policy"] = observation_policy(observation_method)
        plan["observation_policy_sha256"] = policy_hash(plan["observation_policy"])
    if observation_method == "wddm_auto_v3":
        plan["publication_schema"] = "owned_episode_v3"
    for run in plan["runs"]:
        run["fixture_sha256"] = fixtures[str(run["duration_s"])]["sha256"]
    plan["plan_sha256"] = digest(plan)
    return plan


def verify_plan(plan, root=ROOT):
    body = {k: v for k, v in plan.items() if k != "plan_sha256"}
    if (
        digest(body) != plan["plan_sha256"]
        or file_hash(root / "models/models.lock.json") != plan["lock_sha256"]
    ):
        raise ValueError("plan_or_lock_changed")
    if plan.get("observation_method") in {
        "wddm_auto_v1",
        "wddm_auto_v2",
        "wddm_auto_v3",
    }:
        from benchmark_observation import policy_hash, validate_policy

        validate_policy(plan.get("observation_policy"))
        if plan.get("observation_policy_sha256") != policy_hash(
            plan["observation_policy"]
        ):
            raise ValueError("auto_policy_seal_invalid")
        if plan["observation_policy"]["version"] != plan["observation_method"]:
            raise ValueError("auto_plan_policy_mismatch")
        if plan["observation_method"] in {"wddm_auto_v2", "wddm_auto_v3"} and (
            plan["source_hashes"] != source_hashes(root) or len(plan["runs"]) != 160
        ):
            raise ValueError("auto_complete_source_and_matrix_required")
        if plan["observation_method"] == "wddm_auto_v3" and (
            plan.get("publication_schema") != "owned_episode_v3"
            or "scripts/eval/benchmark_coordinator.py" not in plan["source_hashes"]
            or "scripts/eval/benchmark_episode.py" not in plan["source_hashes"]
        ):
            raise ValueError("v3_new_plan_and_coordinator_sources_required")
    for relative, sha in plan["source_hashes"].items():
        if file_hash(project_path(root / relative, root)) != sha:
            raise ValueError("source_changed")
    for duration, fixture in plan["fixtures_by_duration"].items():
        path = project_path(root / fixture["path"], root)
        if file_hash(path) != fixture["sha256"]:
            raise ValueError("fixture_changed")
        validate_input(json.loads(path.read_text(encoding="utf-8-sig")), int(duration))


def run_request(plan, run, root=ROOT):
    fixture = plan["fixtures_by_duration"][str(run["duration_s"])]
    path = project_path(root / fixture["path"], root)
    if file_hash(path) != fixture["sha256"]:
        raise ValueError("fixture_changed")
    value = validate_input(
        json.loads(path.read_text(encoding="utf-8-sig")), run["duration_s"]
    )
    config = next(c for c in plan["configs"] if c["config_id"] == run["config_id"])
    return {
        "job_id": run["job_id"],
        "task": value["task"],
        "model_id": config["model_id"],
        "mode": config["mode"],
        "params": {**value["params"], **config["params"]},
        "seed": 1,
        "n_outputs": 1,
        "timeout_s": plan["timeouts"]["job_s"],
        "output_dir": f"tmp/{run['job_id']}",
    }
