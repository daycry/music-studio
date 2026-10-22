"""Políticas WDDM selladas; v2 readquiere sin aceptar originales discordantes."""

import json
import math
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

from benchmark_clock import timezone_offset_ticks, utc_now
from benchmark_plan import digest, file_hash, project_path


def observation_policy(method="wddm_auto_v1"):
    if method not in {"wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"}:
        raise ValueError("observation_method_unknown")
    policy = {
        "version": method,
        "samples": 10,
        "interval_s": 1,
        "dedicated_abs_mb": 128,
        "dedicated_rel": 0.02,
        "response_mb": 512,
        "query_max_s": 2,
        "pair_skew_s": 1,
        "tick_max_s": 2.5,
        "freshness_s": 900,
        "margin_mb": 512,
        "idle_max_mb": 1600,
        "shared_min_mb": 32,
        "shared_sigma": 3,
        "shared_ticks": 2,
        "counter_type": 0x00010100,
        "format_flags": 0x1200,
        "raw_unit": "bytes",
        "conversion": "bytes/2**20",
    }
    if method in {"wddm_auto_v2", "wddm_auto_v3"}:
        # WDDM can lag NVML briefly while a model is loading. Two bounded
        # reacquisitions keep the sample inside the same episode/deadline
        # without accepting a dedicated-memory disagreement.
        policy.update(reacquisition_max_retries=2, episode_max_s=2)
    if method == "wddm_auto_v3":
        policy.update(
            publication_schema="owned_episode_v3", supervisor_receipt_required=True
        )
    return policy


def policy_hash(policy=None):
    return digest(observation_policy() if policy is None else policy)


def validate_policy(policy):
    if not isinstance(policy, dict) or policy != observation_policy(
        policy.get("version")
    ):
        raise ValueError("auto_policy_changed_new_version_required")
    return policy


def stamp(value):
    try:
        fraction = re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.(\d{1,7}))?(?:\+00:00|Z)",
            value,
        )
        if fraction is None:
            raise ValueError()
        result = datetime.fromisoformat(value)
        if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
            raise ValueError()
        delta = result - datetime(1970, 1, 1, tzinfo=timezone.utc)
        seconds = Fraction(delta.days * 86400 + delta.seconds)
        digits = fraction[1] or ""
        return seconds + (Fraction(int(digits), 10 ** len(digits)) if digits else 0)
    except (TypeError, AttributeError, ValueError):
        raise ValueError("auto_timestamp_invalid") from None


def now_stamp(value=None):
    if isinstance(value, Fraction):
        return value
    return stamp(utc_now() if value is None else value.isoformat())


def number(value):
    return type(value) in {int, float} and math.isfinite(value) and value >= 0


def filetime(value):
    if type(value) is not int or value <= 0:
        raise ValueError("auto_filetime_invalid")
    return Fraction(value - 116444736000000000, 10000000)


def normalized_filetime(windows, raw, normalized=None):
    clock = windows.get("filetime_clock")
    if clock is None:
        raise ValueError("auto_filetime_conversion_invalid")
    try:
        if (
            set(clock) != {"basis", "conversion", "timezone_before", "timezone_after"}
            or clock["basis"] != "local"
            or clock["conversion"] != "LocalFileTimeToFileTime"
            or clock["timezone_before"] != clock["timezone_after"]
            or type(normalized) is not int
            or raw - normalized != timezone_offset_ticks(clock["timezone_before"])
        ):
            raise ValueError()
        filetime(raw)
        return filetime(normalized)
    except (ValueError, KeyError, TypeError):
        raise ValueError("auto_filetime_conversion_invalid") from None


def bracket(value, now):
    try:
        start, end = stamp(value["started_utc"]), stamp(value["finished_utc"])
        a, b = value["started_monotonic_ns"], value["finished_monotonic_ns"]
        if (
            type(a) is not int
            or type(b) is not int
            or a < 0
            or b < a
            or end < start
            or end > now
            or (b - a) / 1e9 > 2
            or end - start > 2
            or abs((b - a) / 1e9 - (end - start)) > 0.1
        ):
            raise ValueError()
        return (start + end) / 2, a, b
    except (KeyError, TypeError, ValueError):
        raise ValueError("auto_query_bracket_invalid") from None


def acquisition_context(context, method="wddm_auto_v1"):
    """Snapshot fixed before acquisition, persisted inside each original."""
    return json.loads(
        json.dumps(
            {**context, "policy_sha256": policy_hash(observation_policy(method))}
        )
    )


def require_acquisition(original, context, method="wddm_auto_v1"):
    if original.get("acquisition_context") != acquisition_context(context, method):
        raise ValueError("auto_acquisition_context_mismatch")


def acquisition_end(sample):
    """Completion of all recorded queries, including those following Windows."""
    return max(
        stamp(sample["operations"][key]["finished_utc"])
        for key in ("nvml", "windows", "wsl", "browser")
    )


def confidence(method="wddm_auto_v1"):
    return {
        "method": method,
        "shared_validation_level": "provider_verified",
        "shared_independent_validation": False,
        "task_manager_contrast": "conflicting_historical",
        "limitations": [
            "adapter_aggregate_not_child_attribution",
            "dedicated_nvml_does_not_calibrate_shared",
            "blank_browser_not_product_ui",
            "no_causal_zero_spill",
            "artistic_quality_requires_listening",
        ],
    }


def validate_samples(
    samples,
    context,
    *,
    now=None,
    idle=False,
    previous=None,
    historical=False,
    continuous=False,
    method="wddm_auto_v1",
    _dedicated=True,
):
    now = now_stamp(now)
    if not isinstance(samples, list) or not samples or (idle and len(samples) != 10):
        raise ValueError("auto_samples_required")
    last = previous
    for sample in samples:
        try:
            if sample.get("errors") or not sample.get("wsl"):
                raise ValueError("auto_observability_lost")
            if method in {"wddm_auto_v2", "wddm_auto_v3"} and any(
                not number(sample["wsl"].get(key))
                for key in ("mem_available_mb", "swap_used_mb")
            ):
                raise ValueError("auto_observability_lost")
            require_acquisition(sample, context, method)
            t, mono = stamp(sample["timestamp"]), sample["monotonic_ns"]
            if (
                type(mono) is not int
                or mono < 0
                or t > now
                or (not historical and now - t > 900)
            ):
                raise ValueError("auto_sample_expired_or_future")
            ops = sample["operations"]
            bounds = {
                k: bracket(ops[k], now) for k in ("windows", "nvml", "browser", "wsl")
            }
            # The pre-call clocks anchor every real query, including its native clock.
            for key, (_, started, finished) in bounds.items():
                op = ops[key]
                start, end = stamp(op["started_utc"]), stamp(op["finished_utc"])
                if (
                    start < t
                    or started < mono
                    or abs((started - mono) / 1e9 - (start - t)) > 0.1
                    or abs((finished - mono) / 1e9 - (end - t)) > 0.1
                    or (not historical and now - start > 900)
                ):
                    raise ValueError("auto_operation_sample_clock_mismatch")
            if min(stamp(ops[k]["started_utc"]) for k in bounds) - t > 0.1:
                raise ValueError("auto_operation_sample_clock_mismatch")
            if abs(bounds["windows"][0] - bounds["nvml"][0]) > 1:
                raise ValueError("auto_dedicated_pair_skew")
            win, nvml, browser = sample["windows"], sample["nvml"], sample["browser"]
            collection = bracket(win["collection"], now)
            query = normalized_filetime(
                win, win["query_filetime"], win.get("query_utc_filetime")
            )
            if not (
                stamp(win["collection"]["started_utc"])
                <= query
                <= stamp(win["collection"]["finished_utc"])
            ):
                raise ValueError("auto_collection_timestamp_invalid")
            if (
                type(win["collect_return"]) is not int
                or win["collect_return"] != 0
                or win["windows_build"] != context["windows_build"]
                or win["scope"] != "adapter_aggregate"
                or win["gpu_mapping_status"] != "resolved"
                or win["adapter_luid"] != context["adapter_luid"]
            ):
                raise ValueError("auto_mapping_or_status_invalid")
            match = re.fullmatch(
                r"luid_0x([0-9a-fA-F]{8})_0x([0-9a-fA-F]{8})_phys_[0-9]+",
                win["instance"],
            )
            if (
                not match
                or [int(match[1], 16), int(match[2], 16)] != context["adapter_luid"]
            ):
                raise ValueError("auto_luid_invalid")
            adapters = [
                a
                for a in win["dxgi_inventory"]
                if a["vendor_id"] == 0x10DE
                and a["description"] == "NVIDIA GeForce RTX 5070"
            ]
            if (
                len(adapters) != 1
                or [adapters[0]["luid_high"] & 0xFFFFFFFF, adapters[0]["luid_low"]]
                != context["adapter_luid"]
            ):
                raise ValueError("auto_inventory_ambiguous")
            if (
                nvml["driver_version"] != context["driver_version"]
                or nvml["uuid"] != context["nvml_uuid"]
                or nvml["name"] != "NVIDIA GeForce RTX 5070"
                or not nvml["uuid"]
            ):
                raise ValueError("auto_nvml_identity_invalid")
            if (
                any(not number(nvml[k]) for k in ("used_mb", "free_mb", "total_mb"))
                or nvml["free_mb"] <= 512
                or (idle and nvml["used_mb"] > 1600)
            ):
                raise ValueError("auto_nvml_invalid_or_idle")
            for name in ("shared_mb", "dedicated_mb"):
                counter = win["counters"][name]
                if (
                    win["counters"]["shared_mb"]["path"]
                    == win["counters"]["dedicated_mb"]["path"]
                ):
                    raise ValueError("auto_counter_paths_mixed")
                if (
                    counter["counter_type"] != 0x10100
                    or counter["raw_counter_type"] != 0x10100
                    or counter["info_counter_type"] != 0x10100
                    or counter["info_return"] != 0
                    or type(counter["scale"]) is not int
                    or counter["raw_unit"] != "bytes"
                    or counter["format_flags"] != 0x1200
                    or counter["conversion"] != "bytes/2**20"
                    or type(counter["default_scale"]) is not int
                    or any(
                        type(counter[k]) is not int or counter[k] != 0
                        for k in ("raw_return", "format_return", "info_return")
                    )
                    or any(
                        type(counter[k]) is not int or counter[k] not in (0, 1)
                        for k in ("raw_cstatus", "formatted_cstatus")
                    )
                    or any(
                        not number(counter[k]) for k in ("raw_value", "formatted_value")
                    )
                    or not number(win[name])
                    or f"({win['instance']})" not in counter["path"]
                    or not math.isclose(
                        counter["raw_value"], counter["formatted_value"], abs_tol=1
                    )
                    or not math.isclose(
                        win[name], counter["formatted_value"] / 2**20, abs_tol=1e-8
                    )
                    or not (
                        stamp(win["collection"]["started_utc"])
                        <= normalized_filetime(
                            win,
                            counter["raw_filetime"],
                            counter.get("raw_utc_filetime"),
                        )
                        <= stamp(win["collection"]["finished_utc"])
                    )
                ):
                    raise ValueError("auto_counter_invalid")
            if (
                method == "wddm_auto_v1"
                and _dedicated
                and abs(win["dedicated_mb"] - nvml["used_mb"])
                > max(128, 0.02 * nvml["used_mb"])
            ):
                raise ValueError("auto_dedicated_disagreement")
            if (
                any(
                    browser[k] != context["browser_identity"][k]
                    for k in ("pid", "hwnd", "creation_time", "executable")
                )
                or browser["executable"]
                not in {"msedge.exe", "chrome.exe", "firefox.exe"}
                or type(browser["creation_time"]) is not int
                or browser["creation_time"] <= 0
                or browser["visible"] is not True
                or browser["iconic"] is not False
                or len(browser["rect"]) != 4
                or browser["rect"][2] <= browser["rect"][0]
                or browser["rect"][3] <= browser["rect"][1]
            ):
                raise ValueError("auto_browser_identity_or_visibility_invalid")
            if last:
                gap = (mono - last["monotonic_ns"]) / 1e9
                previous_query = last["windows"]["query_filetime"]
                if (
                    not 0 < gap <= (900 if continuous else 2.5)
                    or t <= stamp(last["timestamp"])
                    or win["query_filetime"] <= previous_query
                ):
                    raise ValueError("auto_replayed_or_paused_sample")
                for name in ("shared_mb", "dedicated_mb"):
                    if (
                        win["counters"][name]["raw_filetime"]
                        <= last["windows"]["counters"][name]["raw_filetime"]
                    ):
                        raise ValueError("auto_replayed_counter")
                if any(
                    bounds[k][1] <= last["operations"][k]["started_monotonic_ns"]
                    for k in bounds
                ):
                    raise ValueError("auto_replayed_operation")
            # Collection is inside the Windows operation, not the sample's pre-call clock.
            if (
                not bounds["windows"][1]
                <= collection[1]
                <= collection[2]
                <= bounds["windows"][2]
            ):
                raise ValueError("auto_collection_bracket_mismatch")
            if _dedicated and abs(win["dedicated_mb"] - nvml["used_mb"]) > max(
                128, 0.02 * nvml["used_mb"]
            ):
                raise ValueError("auto_dedicated_disagreement")
        except (KeyError, TypeError, IndexError, AttributeError):
            raise ValueError("auto_sample_incomplete") from None
        last = sample
    return confidence(method)


def validate_calibration(
    phases,
    lifecycle,
    context,
    *,
    now=None,
    method="wddm_auto_v1",
    trusted_receipts=None,
    trusted_attempts=None,
):
    if method == "wddm_auto_v3":
        from benchmark_calibration_v3 import select_phases

        phases, whole_chain = select_phases(
            phases,
            lifecycle,
            context,
            now=now,
            trusted_receipts=trusted_receipts,
            trusted_attempts=trusted_attempts,
        )
        from benchmark_calibration_v3 import validate_lifecycle

        validate_lifecycle(lifecycle, context)
        reference_now = now_stamp(now)
        recovery = acquisition_end(phases["unloaded"][-1])
        live = [s for s in whole_chain if stamp(s["timestamp"]) > recovery]
        if live:
            if not 0 <= reference_now - acquisition_end(live[-1]) <= 900:
                raise ValueError("auto_continuity_expired_or_not_started")
            now = recovery
    now = now_stamp(now)
    if set(phases) != {"baseline", "loaded", "unloaded"} or any(
        len(v) != 10 for v in phases.values()
    ):
        raise ValueError("auto_calibration_samples_required")
    for phase in phases:
        validate_samples(
            phases[phase], context, now=now, idle=phase != "loaded", method=method
        )
    baseline, loaded, unloaded = (phases[k] for k in ("baseline", "loaded", "unloaded"))
    try:
        load, unload = lifecycle["loaded"], lifecycle["unloaded"]
        if (
            load["event"] not in {"load_finished", "done", "health_loaded"}
            or not load["job_id"]
            or unload["event"] != "health_unloaded"
            or unload["loaded"] is not None
            or not acquisition_end(baseline[-1])
            < stamp(load["observed_at"])
            <= stamp(loaded[0]["timestamp"])
            or not acquisition_end(loaded[-1])
            < stamp(unload["observed_at"])
            <= stamp(unloaded[0]["timestamp"])
        ):
            raise ValueError("auto_phase_transition_invalid")
    except (KeyError, TypeError):
        raise ValueError("auto_phase_transition_missing") from None
    for source, key in (("windows", "dedicated_mb"), ("nvml", "used_mb")):
        base = statistics.mean(s[source][key] for s in baseline)
        plateau = min(s[source][key] for s in loaded)
        recovery = max(s[source][key] for s in unloaded)
        if plateau - base < 512 or plateau - recovery < 512:
            raise ValueError("auto_dedicated_response_missing")
    recovered_at = (
        max(
            unloaded[-1]["operations"].values(),
            key=lambda op: stamp(op["finished_utc"]),
        )["finished_utc"]
        if method in {"wddm_auto_v2", "wddm_auto_v3"}
        else unloaded[-1]["operations"]["windows"]["finished_utc"]
    )
    if now - stamp(recovered_at) > 900:
        raise ValueError("auto_accreditation_expired")
    return {
        **confidence(method),
        "recovered_at": recovered_at,
    }


def read_sealed(item, root):
    try:
        path = project_path(Path(root) / item["path"], Path(root))
        if (
            not path.is_file()
            or path.stat().st_size != item["bytes"]
            or file_hash(path) != item["sha256"]
        ):
            raise ValueError("auto_evidence_seal_mismatch")
        return path
    except (KeyError, TypeError, OSError):
        raise ValueError("auto_evidence_missing") from None


def validate_auto(
    observation,
    root,
    *,
    plan=None,
    now=None,
    continued_samples=None,
    _seen=None,
    trusted_receipts=None,
    trusted_attempts=None,
):
    """Originals and context are mandatory; calibration_pass claims are ignored."""
    try:
        method = observation.get("method")
        continued_records = continued_samples or []
        seen = set() if _seen is None else set(_seen)
        identity = digest(observation)
        if method == "wddm_auto_v3" and len(seen) >= 16:
            raise ValueError("auto_accreditation_chain_depth")
        if identity in seen:
            raise ValueError("auto_accreditation_chain_cycle")
        seen.add(identity)
        if set(observation) - {"previous_accreditation"} != {
            "method",
            "policy",
            "policy_sha256",
            "context",
            "evidence",
            "viewport",
            "binding",
        } or method not in {"wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"}:
            raise ValueError("auto_prerequisite_schema_invalid")
        validate_policy(observation["policy"])
        expected_policy_hash = policy_hash(observation_policy(method))
        if (
            observation["policy"]["version"] != method
            or observation["policy_sha256"] != expected_policy_hash
        ):
            raise ValueError("auto_policy_seal_invalid")
        context = observation["context"]
        if method == "wddm_auto_v3":
            from benchmark_calibration_v3 import safe_path

            safe_path(root)
            for relative in context.get("source_hashes", {}):
                safe_path(Path(root) / relative, Path(root))
            safe_path(Path(root) / "models/models.lock.json", Path(root))
        required = {
            "session_id",
            "plan_sha256",
            "source_hashes",
            "image_id",
            "lock_sha256",
            "driver_version",
            "windows_build",
            "nvml_uuid",
            "adapter_luid",
            "browser_identity",
        }
        if set(context) != required or any(not context[k] for k in required):
            raise ValueError("auto_context_missing")
        if plan is None or any(
            context[k] != plan[k]
            for k in (
                "session_id",
                "plan_sha256",
                "source_hashes",
                "image_id",
                "lock_sha256",
            )
        ):
            raise ValueError("auto_plan_context_mismatch")
        if (
            plan.get("observation_method") != method
            or plan.get("observation_policy_sha256") != expected_policy_hash
        ):
            raise ValueError("auto_plan_policy_mismatch")
        if method in {"wddm_auto_v2", "wddm_auto_v3"}:
            from benchmark_plan import source_hashes

            if (
                context["source_hashes"] != source_hashes(Path(root))
                or len(plan.get("runs", [])) != 160
            ):
                raise ValueError("auto_complete_source_and_matrix_required")
        for relative, sha in context["source_hashes"].items():
            if file_hash(project_path(Path(root) / relative, Path(root))) != sha:
                raise ValueError("auto_source_changed")
        if file_hash(Path(root) / "models/models.lock.json") != context["lock_sha256"]:
            raise ValueError("auto_lock_changed")
        evidence = observation["evidence"]
        required_evidence = {"baseline", "loaded", "unloaded", "lifecycle", "host"}
        if method == "wddm_auto_v2":
            required_evidence.add("continuity")
        if method == "wddm_auto_v3":
            required_evidence.add("publications")
            from benchmark_calibration_v3 import safe_path

            for item in (*evidence.values(), observation["viewport"]["evidence"]):
                safe_path(Path(root) / item["path"], Path(root))
        if set(evidence) != required_evidence:
            raise ValueError("auto_original_evidence_required")
        lifecycle = json.loads(
            read_sealed(evidence["lifecycle"], root).read_text(encoding="utf-8")
        )
        if method == "wddm_auto_v3":
            from benchmark_calibration_v3 import select_phases

            publication = json.loads(
                read_sealed(evidence["publications"], root).read_text(encoding="utf-8")
            )
            if set(publication) != {"root", "receipts", "attempts"}:
                raise ValueError("v3_supervised_calibration_schema_required")
            v3_envelope = {
                **publication,
                "root": safe_path(Path(root) / publication["root"], Path(root)),
                "phases": {
                    phase: json.loads(
                        read_sealed(evidence[phase], root).read_text(encoding="utf-8")
                    )
                    for phase in ("baseline", "loaded", "unloaded")
                },
            }
            phases, v3_chain = select_phases(
                v3_envelope,
                lifecycle,
                context,
                now=now,
                trusted_receipts=trusted_receipts,
                trusted_attempts=trusted_attempts,
            )
            if continued_records and continued_records != publication["receipts"]:
                raise ValueError("v3_continuity_full_chain_required")
            continued_samples = v3_chain
        else:
            phases = {
                name: [
                    json.loads(line)
                    for line in read_sealed(evidence[name], root)
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                for name in ("baseline", "loaded", "unloaded")
            }
        phase_records = phases.copy()
        if method == "wddm_auto_v2":
            from benchmark_runner import read_records

            chain = read_records(read_sealed(evidence["continuity"], root))
            accepted_samples(
                chain, context, now=now, historical=True, complete_chain=True
            )
            if continued_records and (
                any("episode" not in record for record in continued_records)
                or continued_records[: len(chain)] != chain
            ):
                raise ValueError("auto_episode_continuity_prefix_invalid")
            chain_hashes = {digest(record) for record in chain}
            for phase, records in phases.items():
                item = evidence[phase]
                if set(item) != {"path", "sha256", "bytes", "originals", "episodes"}:
                    raise ValueError("auto_episode_original_evidence_required")
                raw = read_records(read_sealed(item["originals"], root))
                episodes = read_records(read_sealed(item["episodes"], root))
                if (
                    episodes != records
                    or raw
                    != [
                        ref["original"]
                        for record in records
                        for ref in record["episode"]["originals"]
                    ]
                    or any(digest(record) not in chain_hashes for record in records)
                ):
                    raise ValueError("auto_episode_original_evidence_mismatch")
                phases[phase] = accepted_samples(
                    records, context, now=now, idle=phase != "loaded", historical=True
                )
            continued_samples = accepted_samples(
                continued_samples or [],
                context,
                now=now,
                historical=True,
                complete_chain=True,
            )
        lifecycle = json.loads(
            read_sealed(evidence["lifecycle"], root).read_text(encoding="utf-8")
        )
        if method == "wddm_auto_v2" and any(
            record["episode"]["phase_started_utc"]
            != (None if phase == "baseline" else lifecycle[phase]["observed_at"])
            for phase, records in phase_records.items()
            for record in records
        ):
            raise ValueError("auto_calibration_phase_context_mismatch")
        host = json.loads(
            read_sealed(evidence["host"], root).read_text(encoding="utf-8")
        )
        require_acquisition(host, context, method)
        for values in phases.values():
            for value in values:
                require_acquisition(value, context, method)
        for point in lifecycle.values():
            require_acquisition(point, context, method)
        if any(
            host[k] != context[k]
            for k in (
                "driver_version",
                "windows_build",
                "nvml_uuid",
                "adapter_luid",
                "browser_identity",
            )
        ):
            raise ValueError("auto_host_context_mismatch")
        for phase in ("loaded", "unloaded"):
            point = lifecycle[phase]
            if method == "wddm_auto_v3":
                safe_path(Path(root) / point["proof"]["path"], Path(root))
            proof = json.loads(
                read_sealed(point["proof"], root).read_text(encoding="utf-8")
            )
            require_acquisition(proof, context, method)
            if stamp(proof["finished_utc"]) != stamp(point["observed_at"]) or stamp(
                proof["started_utc"]
            ) > stamp(proof["finished_utc"]):
                raise ValueError("auto_lifecycle_proof_time_mismatch")
            if phase == "loaded":
                if point["event"] == "health_loaded":
                    loaded = proof["response"].get("loaded")
                    if (
                        not isinstance(loaded, dict)
                        or not loaded.get("model_id")
                        or loaded.get("mode") not in {"bf16", "offload-int8"}
                    ):
                        raise ValueError("auto_loaded_health_proof_invalid")
                else:
                    from benchmark_evidence import validate_events

                    events = proof["events"]
                    validate_events(
                        events,
                        point["job_id"],
                        require_terminal=point["event"] == "done",
                    )
                    candidates = [
                        event for event in events if event["type"] == point["event"]
                    ]
                    if not candidates or (
                        point["event"] == "done"
                        and candidates[-1].get("data", {}).get("executed") is not True
                    ):
                        raise ValueError("auto_loaded_event_proof_invalid")
            elif (
                proof["response"].get("loaded", "missing") is not None
                or proof["response"].get("state") != "idle"
            ):
                raise ValueError("auto_unloaded_health_proof_invalid")
        view = observation["viewport"]
        viewport_original = json.loads(
            read_sealed(view["evidence"], root).read_text(encoding="utf-8")
        )
        require_acquisition(viewport_original, context, method)
        if any(
            viewport_original[k] != view[k]
            for k in ("url", "tab_id", "browser_id", "visible", "observed_at")
        ):
            raise ValueError("auto_viewport_original_mismatch")
        if (
            view["url"] != "about:blank"
            or not view["tab_id"]
            or not view["browser_id"]
            or view["visible"] is not True
            or stamp(view["observed_at"]) > now_stamp(now)
        ):
            raise ValueError("auto_viewport_invalid")
        if observation["binding"] != "unproven":
            # No current supported API proves the native HWND-to-tab binding.
            raise ValueError("auto_browser_binding_unsupported")
        reference_now = now_stamp(now)
        calibration_end = stamp(
            phases["unloaded"][-1]["operations"]["windows"]["finished_utc"]
        )
        if calibration_end > reference_now:
            raise ValueError("auto_calibration_future")
        # A historical window may validate old rows, but cannot admit future queries.
        if any(
            acquisition_end(value) > reference_now
            for values in phases.values()
            for value in values
        ):
            raise ValueError("auto_query_bracket_invalid")
        calibration_completion = acquisition_end(phases["unloaded"][-1])
        continued_samples = continued_samples or []
        for value in continued_samples:
            require_acquisition(value, context, method)
        for left, right in pairwise(continued_samples):
            if (
                stamp(right["timestamp"]) <= stamp(left["timestamp"])
                or right["monotonic_ns"] <= left["monotonic_ns"]
            ):
                raise ValueError("auto_accreditation_chain_replayed_or_reordered")
        segment_start = stamp(phases["baseline"][0]["timestamp"])
        older = [s for s in continued_samples if stamp(s["timestamp"]) < segment_start]
        pilot = [
            s
            for s in continued_samples
            if segment_start <= stamp(s["timestamp"]) <= calibration_end
        ]
        live = [s for s in continued_samples if stamp(s["timestamp"]) > calibration_end]
        pilot_originals = (
            {digest(record["sample"]) for record in chain}
            if method == "wddm_auto_v2"
            else {digest(s) for s in v3_chain}
            if method == "wddm_auto_v3"
            else {digest(s) for values in phases.values() for s in values}
        )
        if any(digest(s) not in pilot_originals for s in pilot):
            raise ValueError("auto_continuity_uncertified_pilot_sample")
        previous = observation.get("previous_accreditation")
        if previous is not None:
            if method == "wddm_auto_v3":
                safe_path(Path(root) / previous["path"], Path(root))
            previous_observation = json.loads(
                read_sealed(previous, root).read_text(encoding="utf-8")
            )
            if previous_observation["context"] != context:
                raise ValueError("auto_accreditation_chain_context_mismatch")
            if method == "wddm_auto_v3":
                if previous_observation["method"] != method:
                    raise ValueError("v3_previous_method_mismatch")
                for item in previous_observation["evidence"].values():
                    safe_path(Path(root) / item["path"], Path(root))
                prior_publication = json.loads(
                    read_sealed(
                        previous_observation["evidence"]["publications"], root
                    ).read_text(encoding="utf-8")
                )
                prior_count = len(prior_publication["receipts"])
                prior_attempt_count = len(prior_publication["attempts"])
                if (
                    prior_publication["root"] != publication["root"]
                    or prior_publication["receipts"]
                    != publication["receipts"][:prior_count]
                    or prior_publication["attempts"]
                    != publication["attempts"][:prior_attempt_count]
                    or not 0 < prior_count < len(publication["receipts"])
                ):
                    raise ValueError("v3_previous_full_chain_prefix_required")
                prior_refs = json.loads(
                    read_sealed(
                        previous_observation["evidence"]["unloaded"], root
                    ).read_text(encoding="utf-8")
                )
                prior_index = next(
                    (
                        i
                        for i, receipt in enumerate(publication["receipts"])
                        if receipt["episode_id"] == prior_refs[-1]["episode_id"]
                    ),
                    None,
                )
                if prior_index is None or prior_index >= prior_count:
                    raise ValueError("v3_previous_phase_reference_invalid")
                previous_end_samples = [v3_chain[prior_index]]
            else:
                previous_end_samples = [
                    json.loads(line)
                    for line in read_sealed(
                        previous_observation["evidence"]["unloaded"], root
                    )
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
            if method == "wddm_auto_v2":
                previous_end_samples = accepted_samples(
                    previous_end_samples, context, now=now, historical=True
                )
            previous_end = acquisition_end(previous_end_samples[-1])
            history_end = max([previous_end] + [acquisition_end(s) for s in older])
            if method == "wddm_auto_v3":
                history_end = max(
                    [history_end]
                    + [
                        stamp(receipt["observed_utc"])
                        for receipt in publication["receipts"]
                        if receipt["ordinal"]
                        < next(
                            r["ordinal"]
                            for r in publication["receipts"]
                            if r["episode_id"]
                            == v3_envelope["phases"]["baseline"][0]["episode_id"]
                        )
                    ]
                )
            if history_end >= segment_start:
                raise ValueError("auto_accreditation_chain_overlap")
            validate_auto(
                previous_observation,
                root,
                plan=plan,
                now=history_end,
                continued_samples=(
                    prior_publication["receipts"]
                    if method == "wddm_auto_v3"
                    else [
                        record
                        for record in continued_records
                        if stamp(record["sample"]["timestamp"]) < segment_start
                    ]
                    if method == "wddm_auto_v2"
                    else older
                ),
                _seen=seen,
                trusted_receipts=(
                    trusted_receipts[:prior_count] if method == "wddm_auto_v3" else None
                ),
                trusted_attempts=(
                    trusted_attempts[:prior_attempt_count]
                    if method == "wddm_auto_v3"
                    else None
                ),
            )
        elif older and method != "wddm_auto_v3":
            raise ValueError("auto_continuity_history_requires_accreditation_chain")
        continued_samples = live
        if continued_samples:
            # Validate each segment in its own window; never renew old rows retroactively.
            first = stamp(continued_samples[0]["timestamp"])
            last = stamp(continued_samples[-1]["operations"]["windows"]["finished_utc"])
            if (
                not 0 <= first - calibration_completion <= 900
                or not 0 <= reference_now - last <= 900
            ):
                raise ValueError("auto_continuity_expired_or_not_started")
            validate_samples(
                continued_samples,
                context,
                now=reference_now,
                historical=True,
                continuous=True,
                method=method,
            )
            calibration_now = calibration_completion
        else:
            calibration_now = reference_now
        result = validate_calibration(
            v3_envelope if method == "wddm_auto_v3" else phases,
            lifecycle,
            context,
            now=reference_now if method == "wddm_auto_v3" else calibration_now,
            method=method,
            trusted_receipts=trusted_receipts,
            trusted_attempts=trusted_attempts,
        )
        return {
            **result,
            "context": context,
            "policy_sha256": expected_policy_hash,
            "browser_binding": "unproven",
            "viewport": view,
        }
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as error:
        detail = str(error) or "unspecified"
        raise ValueError(
            f"auto_prerequisite_incomplete:{type(error).__name__}:{detail}"
        ) from None


def guard_sample(observers, sample):
    context = getattr(observers, "observation_context", None)
    if context is not None:
        try:
            validate_samples(
                [sample], context, previous=getattr(observers, "previous_sample", None)
            )
        except ValueError as error:
            raise ValueError("observability_lost_" + str(error)) from None
        observers.previous_sample = sample
        if not hasattr(observers, "continued_samples"):
            observers.continued_samples = []
        observers.continued_samples.append(sample)
        if getattr(observers, "continuity_path", None) is not None:
            from benchmark_runner import append_record

            append_record(observers.continuity_path, sample)
    return sample


def episode_decision(
    originals,
    context,
    *,
    previous=None,
    now=None,
    idle=False,
    historical=False,
    completion=None,
    phase_started_utc=None,
    method="wddm_auto_v2",
):
    """Recompute recovery from full raw queries, never an accepted/success claim."""
    if not isinstance(originals, list) or not 1 <= len(originals) <= 3:
        raise ValueError("auto_episode_original_count_invalid")
    first = originals[0]
    for index, value in enumerate(originals):
        validate_samples(
            [value],
            context,
            now=now,
            previous=previous,
            historical=historical,
            method=method,
            _dedicated=False,
        )
        if idle and value["nvml"]["used_mb"] > 1600:
            raise ValueError("auto_nvml_invalid_or_idle")
        if phase_started_utc is not None and stamp(value["timestamp"]) < stamp(
            phase_started_utc
        ):
            raise ValueError("auto_phase_transition_invalid")
        end = acquisition_end(value)
        mono_end = max(
            op["finished_monotonic_ns"] for op in value["operations"].values()
        )
        if completion is not None and index == len(originals) - 1:
            completed_utc, completed_mono = completion
            completed = stamp(completed_utc)
            if (
                type(completed_mono) is not int
                or completed < end
                or completed_mono < mono_end
                or completed > now_stamp(now)
                or abs(
                    (completed_mono - first["monotonic_ns"]) / 1e9
                    - (completed - stamp(first["timestamp"]))
                )
                > 0.1
            ):
                raise ValueError("auto_episode_completion_clock_invalid")
            end, mono_end = completed, completed_mono
        if (
            end - stamp(first["timestamp"]) > 2
            or mono_end - first["monotonic_ns"] > 2_000_000_000
        ):
            raise ValueError("auto_episode_deadline_exhausted")
        if previous is not None:
            # Measure the gap from the prior acquisition end to current completion.
            # The independent start-to-start tick guard remains in validate_samples.
            # Comparing with the previous start double-counts its sensor work
            # and rejects a valid chain when the current Windows query is slow.
            previous_end = acquisition_end(previous)
            previous_mono_end = max(
                op["finished_monotonic_ns"]
                for op in previous["operations"].values()
            )
            if (
                end - previous_end > 2.5
                or mono_end - previous_mono_end > 2_500_000_000
            ):
                raise ValueError("auto_replayed_or_paused_sample")
        if index:
            before = originals[index - 1]
            validate_samples(
                [value],
                context,
                now=now,
                previous=before,
                historical=historical,
                method=method,
                _dedicated=False,
            )
            if any(
                stamp(op["started_utc"]) < acquisition_end(before)
                or op["started_monotonic_ns"]
                < max(b["finished_monotonic_ns"] for b in before["operations"].values())
                for op in value["operations"].values()
            ):
                raise ValueError("auto_episode_partial_reuse")
        mismatch = abs(
            value["windows"]["dedicated_mb"] - value["nvml"]["used_mb"]
        ) > max(128, 0.02 * value["nvml"]["used_mb"])
        if not mismatch:
            if index != len(originals) - 1:
                raise ValueError("auto_episode_unnecessary_retry")
            return value
        if index == len(originals) - 1:
            raise ValueError("auto_dedicated_disagreement")
    return None


def validate_episode(
    record, context, *, previous_record=None, now=None, historical=False, idle=False
):
    try:
        episode = record["episode"]
        if set(record) != {"episode", "sample"} or set(episode) != {
            "version",
            "ordinal",
            "context",
            "previous_episode_sha256",
            "predecessor",
            "started_utc",
            "deadline_utc_ticks",
            "originals",
            "accepted_sha256",
            "idle",
            "completed_utc",
            "completed_monotonic_ns",
            "phase_started_utc",
        }:
            raise ValueError("auto_episode_schema_invalid")
        if episode["version"] != "wddm_auto_v2" or episode[
            "context"
        ] != acquisition_context(context, "wddm_auto_v2"):
            raise ValueError("auto_episode_context_mismatch")
        if (
            type(episode["ordinal"]) is not int
            or episode["ordinal"] < 1
            or type(episode["idle"]) is not bool
        ):
            raise ValueError("auto_episode_ordinal_invalid")
        predecessor = episode["predecessor"]
        if previous_record is not None:
            if (
                episode["ordinal"] != previous_record["episode"]["ordinal"] + 1
                or episode["previous_episode_sha256"]
                != digest(previous_record["episode"])
                or predecessor != previous_record["sample"]
            ):
                raise ValueError("auto_episode_chain_invalid")
        elif episode["ordinal"] == 1 and episode["previous_episode_sha256"] is not None:
            raise ValueError("auto_episode_chain_invalid")
        if predecessor is not None:
            validate_samples(
                [predecessor], context, now=now, historical=True, method="wddm_auto_v2"
            )
        originals = []
        for index, reference in enumerate(episode["originals"], 1):
            if (
                set(reference) != {"ordinal", "sha256", "original"}
                or reference["ordinal"] != index
                or digest(reference["original"]) != reference["sha256"]
            ):
                raise ValueError("auto_episode_original_seal_invalid")
            originals.append(reference["original"])
        accepted = episode_decision(
            originals,
            context,
            previous=predecessor,
            now=now,
            historical=historical,
            idle=idle or episode["idle"],
            completion=(episode["completed_utc"], episode["completed_monotonic_ns"]),
            phase_started_utc=episode["phase_started_utc"],
        )
        if (
            accepted is None
            or record["sample"] != accepted
            or episode["accepted_sha256"] != digest(accepted)
            or episode["started_utc"] != originals[0]["timestamp"]
            or episode["deadline_utc_ticks"]
            != str(stamp(originals[0]["timestamp"]) + 2)
        ):
            raise ValueError("auto_episode_acceptance_invalid")
        return accepted
    except (KeyError, TypeError, IndexError, AttributeError):
        raise ValueError("auto_episode_incomplete") from None


def accepted_samples(
    records,
    context=None,
    *,
    now=None,
    idle=False,
    historical=False,
    complete_chain=False,
    publication_root=None,
    trusted_receipts=None,
    attempts=None,
    trusted_attempts=None,
):
    if any("supervisor_receipt" in record for record in records):
        from benchmark_episode import read_publications, summary

        if (
            context is None
            or publication_root is None
            or trusted_receipts is None
            or any(
                set(record) != {"supervisor_receipt", "sample"} for record in records
            )
        ):
            raise ValueError("v3_supervisor_evidence_required")
        receipts = [record["supervisor_receipt"] for record in records]
        samples = read_publications(
            publication_root,
            receipts,
            context,
            trusted_receipts=trusted_receipts,
            attempts=attempts,
            trusted_attempts=trusted_attempts,
            now=now,
            historical=historical,
            idle=idle,
        )
        if [summary(sample) for sample in samples] != [
            record["sample"] for record in records
        ]:
            raise ValueError("v3_summary_mismatch")
        return samples
    if any(
        record.get("schema") == "validated_v3_summary"
        or isinstance(record.get("acquisition_context"), dict)
        and record["acquisition_context"].get("policy_sha256")
        == policy_hash(observation_policy("wddm_auto_v3"))
        for record in records
    ):
        raise ValueError("v3_supervisor_evidence_required")
    if not records or "episode" not in records[0]:
        if any("episode" in value for value in records):
            raise ValueError("auto_episode_mixed_records")
        return records
    if context is None:
        raise ValueError("auto_episode_context_required")
    result, last = [], None
    for record in records:
        if (
            complete_chain
            and last is None
            and (
                record["episode"]["ordinal"] != 1
                or record["episode"]["predecessor"] is not None
            )
        ):
            raise ValueError("auto_episode_chain_missing_origin")
        result.append(
            validate_episode(
                record,
                context,
                previous_record=last,
                now=now,
                idle=idle,
                historical=historical,
            )
        )
        last = record
    return result


def read_acquisitions(
    path,
    context=None,
    *,
    now=None,
    idle=False,
    historical=False,
    method=None,
    supervisor_receipts=None,
    trusted_receipts=None,
    attempts=None,
    trusted_attempts=None,
):
    """Match the accepted stream to every independently persisted raw original."""
    from benchmark_runner import read_records

    if method == "wddm_auto_v3":
        from benchmark_episode import read_publications, summary

        if context is None or supervisor_receipts is None or trusted_receipts is None:
            raise ValueError("v3_supervisor_evidence_required")
        samples = read_publications(
            path,
            supervisor_receipts,
            context,
            trusted_receipts=trusted_receipts,
            attempts=attempts,
            trusted_attempts=trusted_attempts,
            now=now,
            historical=historical,
            idle=idle,
        )
        return [
            {"supervisor_receipt": receipt, "sample": summary(sample)}
            for receipt, sample in zip(supervisor_receipts, samples)
        ]
    if method is not None and method not in {"wddm_auto_v1", "wddm_auto_v2"}:
        raise ValueError("observation_method_unknown")

    path = Path(path)
    records = read_records(path)
    raw_path = path.with_name(path.name + ".originals.ndjson")
    if raw_path.exists():
        if not records or any("episode" not in value for value in records):
            raise ValueError("auto_episode_original_evidence_required")
        if read_records(
            path.with_name(path.name + ".episodes.ndjson")
        ) != records or read_records(raw_path) != [
            reference["original"]
            for record in records
            for reference in record["episode"]["originals"]
        ]:
            raise ValueError("auto_episode_original_evidence_mismatch")
    elif any("episode" in value for value in records):
        raise ValueError("auto_episode_original_evidence_required")
    accepted_samples(records, context, now=now, idle=idle, historical=historical)
    return records


def episode_clock():
    return utc_now(), time.perf_counter_ns()


def acquire_sample(observers, path, *, idle=False, enforce=True):
    """Persist complete originals before classification; at most one fresh retry."""
    from benchmark_runner import append_record

    path = Path(path)
    method = getattr(observers, "observation_method", "wddm_auto_v1")
    if method in {"wddm_auto_v1", "wddm_auto_v2"}:
        raise ValueError("auto_legacy_policy_read_only_new_session_required")
    if method not in {"task_manager_v1", "wddm_auto_v3"}:
        raise ValueError("unknown_observation_method")
    if method == "wddm_auto_v3":
        from benchmark_episode import EpisodeAcquirer

        if not isinstance(observers, EpisodeAcquirer):
            raise ValueError("v3_owned_episode_provider_required")
        return observers.acquire(path, idle=idle, enforce=enforce)
    if method != "wddm_auto_v2":
        value = observers.sample()
        append_record(path, value)
        if enforce:
            guard_sample(observers, value)
        return value
    context = getattr(observers, "observation_context", None)
    if context is None:
        raise ValueError("auto_context_missing")
    context = json.loads(json.dumps(context))
    previous = getattr(observers, "previous_sample", None)
    previous_episode = getattr(observers, "previous_episode", None)
    phase_started_utc = getattr(observers, "phase_started_utc", None)
    originals = []
    raw_path = path.with_name(path.name + ".originals.ndjson")
    attempts_path = path.with_name(path.name + ".episodes.ndjson")
    for _ in range(2):
        value = observers.sample()
        append_record(raw_path, value)
        if not enforce:
            # Cancellation observes an already owned job after a guard failure.
            # These raw records cannot enter accepted continuity or metrics.
            return value
        originals.append(value)
        episode = {
            "version": method,
            "ordinal": 1
            if previous_episode is None
            else previous_episode["ordinal"] + 1,
            "context": acquisition_context(context, method),
            "previous_episode_sha256": None
            if previous_episode is None
            else digest(previous_episode),
            "predecessor": previous,
            "started_utc": originals[0].get("timestamp"),
            "deadline_utc_ticks": None,
            "originals": [
                {"ordinal": i, "sha256": digest(v), "original": v}
                for i, v in enumerate(originals, 1)
            ],
            "accepted_sha256": None,
            "idle": idle,
            "phase_started_utc": phase_started_utc,
        }
        try:
            episode["deadline_utc_ticks"] = str(stamp(originals[0]["timestamp"]) + 2)
            episode["completed_utc"], episode["completed_monotonic_ns"] = (
                episode_clock()
            )
            accepted = episode_decision(
                originals,
                context,
                previous=previous,
                idle=idle,
                completion=(
                    episode["completed_utc"],
                    episode["completed_monotonic_ns"],
                ),
                phase_started_utc=phase_started_utc,
            )
        except ValueError as error:
            append_record(attempts_path, {"episode": episode, "error": str(error)})
            raise ValueError("observability_lost_" + str(error)) from None
        if accepted is None:
            continue
        episode["accepted_sha256"] = digest(accepted)
        record = {"episode": episode, "sample": accepted}
        validate_episode(record, context)
        append_record(attempts_path, record)
        append_record(path, record)
        if enforce:
            observers.previous_sample, observers.previous_episode = accepted, episode
            if not hasattr(observers, "continued_samples"):
                observers.continued_samples = []
            observers.continued_samples.append(record)
            if getattr(observers, "continuity_path", None) is not None:
                append_record(observers.continuity_path, record)
        return accepted
    raise ValueError("observability_lost_auto_dedicated_disagreement")


def monitored_operation(operation, observers, folder, stem, *, interval_s=1):
    """Observe an owned blocking lifecycle call without changing transport or ownership."""
    path = Path(folder) / (stem + "-observers.ndjson")
    acquire_sample(observers, path)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(operation)
        while True:
            next_tick = time.monotonic() + interval_s
            acquire_sample(observers, path)
            if future.done():
                return future.result()
            time.sleep(max(0, next_tick - time.monotonic()))


def build_auto_prerequisites(
    plan,
    context,
    originals,
    viewport_path,
    *,
    root,
    exclusive_gpu_authorized,
    now=None,
    previous_accreditation_path=None,
    trusted_receipts=None,
    trusted_attempts=None,
):
    """Root supplies real originals after pilot; never synthesizes a calibration."""

    def sealed(relative):
        if plan["observation_method"] == "wddm_auto_v3":
            from benchmark_calibration_v3 import safe_path

            safe_path(Path(root) / relative, Path(root))
        path = project_path(Path(root) / relative, Path(root))
        return {
            "path": path.relative_to(Path(root)).as_posix(),
            "sha256": file_hash(path),
            "bytes": path.stat().st_size,
        }

    viewport_seal = sealed(viewport_path)
    viewport = json.loads(read_sealed(viewport_seal, root).read_text(encoding="utf-8"))
    observation = {
        "method": plan["observation_method"],
        "policy": observation_policy(plan["observation_method"]),
        "policy_sha256": policy_hash(observation_policy(plan["observation_method"])),
        "context": context,
        "evidence": {key: sealed(path) for key, path in originals.items()},
        "viewport": {**viewport, "evidence": viewport_seal},
        "binding": "unproven",
    }
    if observation["method"] == "wddm_auto_v2":
        for phase in ("baseline", "loaded", "unloaded"):
            relative = originals[phase]
            observation["evidence"][phase].update(
                originals=sealed(str(relative) + ".originals.ndjson"),
                episodes=sealed(str(relative) + ".episodes.ndjson"),
            )
    if previous_accreditation_path is not None:
        observation["previous_accreditation"] = sealed(previous_accreditation_path)
    if exclusive_gpu_authorized is not True:
        raise ValueError("auto_exclusive_gpu_authorization_required")
    validate_auto(
        observation,
        root,
        plan=plan,
        now=now,
        trusted_receipts=trusted_receipts,
        trusted_attempts=trusted_attempts,
    )
    return {
        "observation": observation,
        "browser": context["browser_identity"],
        "exclusive_gpu_authorized": True,
    }
