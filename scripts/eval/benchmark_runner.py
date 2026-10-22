"""Lote /v1 observado; un timeout de observaciÃ³n nunca relanza inferencia."""

import json
import math
import os
import statistics
import time
from pathlib import Path

from benchmark_evidence import exclusive_json, validate_events
from benchmark_observation import (
    accepted_samples,
    acquire_sample,
    confidence,
    monitored_operation,
    validate_auto,
    validate_samples,
)
from benchmark_observers import shared_assessment
from benchmark_plan import ROOT, digest, file_hash, new_id, project_path
from benchmark_runtime import ApiError, resume_action


class ObservationTimeout(RuntimeError):
    pass


def execute_run_v3(plan, run, api, coordinator, folder, request):
    """Envío, estado e I/O aislados; sólo el sampler adquiere episodios."""
    coordinator.check()
    folder = Path(folder)
    exists = lambda path: api.operation("exists", {"path": str(path)})
    terminal_path = folder / "terminal.json"
    job_id = run["job_id"]
    if exists(terminal_path):
        terminal = api.read_json(terminal_path)
        events = api.operation("read_records", {"path": str(folder / "events.ndjson")})
        if terminal != validate_events(events, job_id):
            raise ValueError("terminal_evidence_mismatch")
        return terminal
    if exists(folder / "request.json"):
        if api.read_json(folder / "request.json") != request:
            raise ValueError("resume_request_changed")
    else:
        api.write_json(folder / "request.json", request)
    intent = folder / "submission-intent.json"
    if exists(intent):
        try:
            status = api.request("GET", f"/v1/jobs/{job_id}")
        except ApiError as error:
            if error.code == "NOT_FOUND":
                raise ValueError("missing_existing_job_requires_new_attempt") from None
            raise
        resume_action({"job_id": job_id}, status)
    else:
        # ACE-Step valida perfiles y hashes de entrada durante /estimate; en
        # una GPU real esa preflight puede tardar varios segundos antes de
        # devolver el presupuesto. El timeout HTTP por defecto de 5 s no es
        # suficiente y provoca TRANSPORT_DEADLINE antes del primer POST.
        estimate = api.request("POST", "/v1/estimate", request, timeout=120)
        api.write_json(folder / "estimate.json", estimate)
        coordinator.check()
        # Persistir antes del POST; consultar el mismo ID si se pierde el ACK.
        api.write_json(
            intent,
            {
                "job_id": job_id,
                "request_sha256": digest(request),
                "action": "submit_once",
            },
        )
        coordinator.check()
        accepted = api.request("POST", "/v1/jobs", request, timeout=120)
        if accepted.get("job_id") != job_id:
            raise ValueError("submitted_job_identity_mismatch")
        api.write_json(folder / "accepted.json", accepted)
    events_path = folder / "events.ndjson"
    events = api.operation("read_records", {"path": str(events_path)})
    deadline = time.monotonic() + plan["timeouts"]["observation_s"]
    while time.monotonic() < deadline:
        coordinator.check()
        terminal = validate_events(events, job_id, require_terminal=False)
        if terminal is not None:
            api.write_json(terminal_path, terminal)
            return terminal
        for event in api.events(
            job_id, len(events), timeout=min(1, deadline - time.monotonic())
        ):
            validate_events(events + [event], job_id, require_terminal=False)
            api.operation("append_record", {"path": str(events_path), "value": event})
            events.append(event)
        if not events or events[-1]["type"] not in {"done", "error", "cancelled"}:
            try:
                status = api.request("GET", f"/v1/jobs/{job_id}", deadline=deadline)
                if status.get("job_id") != job_id:
                    raise ValueError("job_identity_conflict")
            except ApiError as error:
                if error.code not in {"TRANSPORT_DEADLINE", "TRANSPORT_UNAVAILABLE"}:
                    raise
    api.write_json(
        folder / f"observation-timeout-{new_id()}.json",
        {"job_id": job_id, "resume_required": True, "action": "query_same_job"},
    )
    raise ObservationTimeout("existing_job_preserved_resume_required")


def execute_run(plan, run, api, observers, folder, request):
    method = plan.get("observation_method", "task_manager_v1")
    if method in {"wddm_auto_v1", "wddm_auto_v2"}:
        raise ValueError("auto_legacy_policy_read_only_new_session_required")
    if method not in {"task_manager_v1", "wddm_auto_v3"}:
        raise ValueError("unknown_observation_method")
    if plan.get("observation_method") == "wddm_auto_v3":
        from benchmark_coordinator import ContinuousCoordinator

        if (
            not isinstance(observers, ContinuousCoordinator)
            or getattr(api, "coordinator", None) is not observers
        ):
            raise ValueError("v3_continuous_owned_runtime_required")
        return execute_run_v3(plan, run, api, observers, folder, request)
    if plan.get("observation_method") == "wddm_auto_v2" and (
        getattr(observers, "observation_method", None) != "wddm_auto_v2"
        or getattr(observers, "observation_context", None) is None
    ):
        raise ValueError("auto_observer_policy_context_required")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    terminal_path = folder / "terminal.json"
    if terminal_path.exists():
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
        if terminal != validate_events(
            read_records(folder / "events.ndjson"), run["job_id"]
        ):
            raise ValueError("terminal_evidence_mismatch")
        return terminal
    request_path = folder / "request.json"
    if request_path.exists():
        if json.loads(request_path.read_text(encoding="utf-8")) != request:
            raise ValueError("resume_request_changed")
    else:
        exclusive_json(request_path, request)
    if plan.get("observation_method") in {"wddm_auto_v1", "wddm_auto_v2"}:
        acquire_sample(
            observers, folder / ("pre-submit-observation-" + new_id() + ".ndjson")
        )
    intent = folder / "submission-intent.json"
    if intent.exists():
        try:
            status = (
                monitored_operation(
                    lambda: api.request("GET", f"/v1/jobs/{run['job_id']}"),
                    observers,
                    folder,
                    "resume-status",
                )
                if plan.get("observation_method") in {"wddm_auto_v1", "wddm_auto_v2"}
                else api.request("GET", f"/v1/jobs/{run['job_id']}")
            )
        except ApiError as error:
            if error.code == "NOT_FOUND":
                raise ValueError("missing_existing_job_requires_new_attempt") from None
            raise
        resume_action({"job_id": run["job_id"]}, status)
    else:
        estimate = (
            monitored_operation(
                lambda: api.request("POST", "/v1/estimate", request),
                observers,
                folder,
                "estimate",
            )
            if plan.get("observation_method") in {"wddm_auto_v1", "wddm_auto_v2"}
            else api.request("POST", "/v1/estimate", request)
        )
        exclusive_json(folder / "estimate.json", estimate)
        exclusive_json(
            intent,
            {
                "job_id": run["job_id"],
                "request_sha256": digest(request),
                "action": "submit_once",
            },
        )
        accepted = (
            monitored_operation(
                lambda: api.request("POST", "/v1/jobs", request),
                observers,
                folder,
                "submission",
            )
            if plan.get("observation_method") in {"wddm_auto_v1", "wddm_auto_v2"}
            else api.request("POST", "/v1/jobs", request)
        )
        if accepted.get("job_id") != run["job_id"]:
            raise ValueError("submitted_job_identity_mismatch")
        exclusive_json(folder / "accepted.json", accepted)
    terminal, _ = observe_job(
        api,
        observers,
        run["job_id"],
        folder,
        observation_s=plan["timeouts"]["observation_s"],
        interval_s=plan["observer_policy"]["interval_s"],
    )
    exclusive_json(terminal_path, terminal)
    return terminal


def append_record(path, value):
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


def read_records(path):
    path = Path(path)
    return (
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def observe_job(
    api,
    observers,
    job_id,
    folder,
    *,
    observation_s=3700,
    interval_s=1,
    clock=time.monotonic,
    sleep=time.sleep,
    enforce_observation=True,
):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    events_path = folder / "events.ndjson"
    events = read_records(events_path)
    terminal = validate_events(events, job_id, require_terminal=False)
    if terminal:
        return terminal, read_records(folder / "observers.ndjson")
    deadline = clock() + observation_s
    status = {"job_id": job_id, "state": "unknown", "query_required": True}
    while clock() < deadline:
        sample_started = clock()
        acquire_sample(
            observers, folder / "observers.ndjson", enforce=enforce_observation
        )
        after = len(events)
        query_deadline = min(deadline, sample_started + interval_s)
        if clock() >= query_deadline and clock() < deadline:
            # A slow sensor degrades cadence, but must not starve job observation.
            query_deadline = min(deadline, clock() + interval_s)
        remaining = query_deadline - clock()
        batch = (
            api.events(
                job_id,
                after,
                timeout=max(0, remaining),
            )
            if remaining > 0 or (interval_s == 0 and clock() < deadline)
            else []
        )
        if clock() >= deadline:
            break
        for event in batch:
            validate_events(events + [event], job_id, require_terminal=False)
            append_record(events_path, event)
            events.append(event)
        terminal = validate_events(events, job_id, require_terminal=False)
        if terminal:
            return terminal, read_records(folder / "observers.ndjson")
        if clock() < query_deadline or not hasattr(api, "request_before"):
            try:
                status = (
                    api.request_before(
                        "GET", f"/v1/jobs/{job_id}", deadline=query_deadline
                    )
                    if hasattr(api, "request_before")
                    else api.request("GET", f"/v1/jobs/{job_id}")
                )
                if status.get("job_id") != job_id:
                    raise ValueError("job_identity_conflict")
            except ApiError as error:
                if error.code not in {"TRANSPORT_DEADLINE", "TRANSPORT_UNAVAILABLE"}:
                    raise
        sleep(max(0, min(deadline - clock(), interval_s - (clock() - sample_started))))
    timeout_path = folder / "observation-timeout.json"
    if timeout_path.exists():
        timeout_path = folder / f"observation-timeout-{new_id()}.json"
    exclusive_json(
        timeout_path,
        {
            "job_id": job_id,
            "observed_status": status,
            "resume_required": True,
            "action": "query_same_job",
        },
    )
    raise ObservationTimeout("existing_job_preserved_resume_required")


def validate_prerequisites(
    value,
    root=ROOT,
    *,
    plan=None,
    now=None,
    continued_samples=None,
    trusted_receipts=None,
    trusted_attempts=None,
):
    method = value.get("observation", {}).get("method", "task_manager_v1")
    if method in {"wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"}:
        if "task_manager" in value or value.get("exclusive_gpu_authorized") is not True:
            raise ValueError("auto_prerequisite_discriminator_invalid")
        accreditation = validate_auto(
            value["observation"],
            root,
            plan=plan,
            now=now,
            continued_samples=continued_samples,
            **(
                {
                    "trusted_receipts": trusted_receipts,
                    "trusted_attempts": trusted_attempts,
                }
                if method == "wddm_auto_v3"
                else {}
            ),
        )
        browser = accreditation["context"]["browser_identity"]
        if value.get("browser") != browser:
            raise ValueError("auto_browser_context_mismatch")
        return {**value, "accreditation": accreditation}
    if method != "task_manager_v1":
        raise ValueError("observation_method_unknown")
    if plan and plan.get("observation_method", "task_manager_v1") != method:
        raise ValueError("observation_method_mismatch")
    observation = value.get("task_manager")
    if not isinstance(observation, dict) or set(observation) != {
        "baseline",
        "representative",
    }:
        raise ValueError("task_manager_manual_evidence_required")
    for item in observation.values():
        if (
            item.get("gpu") != "NVIDIA GeForce RTX 5070"
            or not item.get("observed_at")
            or type(item.get("shared_mb")) not in {int, float}
        ):
            raise ValueError("task_manager_manual_evidence_invalid")
        path = project_path(root / item["evidence_path"], root)
        if file_hash(path) != item["sha256"]:
            raise ValueError("task_manager_evidence_hash_mismatch")
    browser = value.get("browser", {})
    if (
        type(browser.get("pid")) is not int
        or type(browser.get("hwnd")) is not int
        or browser["pid"] <= 0
        or browser["hwnd"] <= 0
    ):
        raise ValueError("visible_browser_identity_required")
    path = project_path(root / browser["evidence_path"], root)
    if file_hash(path) != browser["sha256"]:
        raise ValueError("browser_evidence_hash_mismatch")
    if value.get("exclusive_gpu_authorized") is not True:
        raise ValueError("exclusive_gpu_prerequisite_required")
    return value


def summarize_run(
    run,
    terminal,
    samples,
    baseline,
    *,
    output_valid,
    fidelity_valid,
    observation_context=None,
    now=None,
    v3_evidence=None,
):
    method = (
        "wddm_auto_v3"
        if v3_evidence is not None
        else "wddm_auto_v2"
        if samples and "episode" in samples[0]
        else "wddm_auto_v1"
    )
    records = samples
    v3_breaks = None
    if v3_evidence is not None:
        from benchmark_episode import read_json

        chain = v3_evidence["records"]
        validated = accepted_samples(
            chain,
            observation_context,
            now=now,
            historical=True,
            publication_root=v3_evidence["publication_root"],
            trusted_receipts=v3_evidence["trusted_receipts"],
            attempts=v3_evidence["attempts"],
            trusted_attempts=v3_evidence["trusted_attempts"],
        )
        positions = {digest(record): i for i, record in enumerate(chain)}

        def select(selected):
            indices = [positions[digest(record)] for record in selected]
            if indices != sorted(set(indices)):
                raise ValueError("v3_row_replayed_or_reordered_reference")
            return [validated[index] for index in indices]

        samples, baseline = select(samples), select(baseline)
        v3_breaks = [
            len(
                read_json(
                    Path(v3_evidence["publication_root"])
                    / record["supervisor_receipt"]["episode_id"]
                    / "prepared.json"
                )["raw_refs"]
            )
            > 1
            for record in records
        ]
    else:
        samples = accepted_samples(
            samples, observation_context, now=now, historical=True
        )
        baseline = accepted_samples(
            baseline, observation_context, now=now, idle=True, historical=True
        )
    row = {
        **run,
        "status": terminal["type"],
        "valid": False,
        "load_s": None,
        "run_s": None,
        "inference_s": None,
        "audio_duration_s": None,
        "rtf": None,
        "vram_peak_mb": None,
        "vram_cap_mb": None,
        "spilled_engine": None,
        "shared_gpu_peak_mb": None,
        "shared_gpu_observed": None,
        "wsl_mem_available_mb": None,
        "wsl_swap_used_mb": None,
        "sensor_errors": [],
    }
    data = terminal.get("data", {})
    telemetry = data.get("telemetry", {})
    for key in ("load_s", "run_s", "vram_peak_mb", "vram_cap_mb"):
        row[key] = telemetry.get(key)
    row["spilled_engine"] = telemetry.get("spilled")
    timings = telemetry.get("extra", {}).get("inference_timings", [])
    timing_valid = False
    if len(timings) == 1:
        t = timings[0]
        try:
            timing_valid = (
                t["clock"] == "perf_counter_ns_cuda_synchronized"
                and t["cuda_sync"] is True
                and t["infer_end_ns"] >= t["infer_start_ns"]
                and math.isclose(
                    t["inference_s"], (t["infer_end_ns"] - t["infer_start_ns"]) / 1e9
                )
                and t["audio_duration_s"] > 0
                and math.isclose(t["rtf"], t["inference_s"] / t["audio_duration_s"])
            )
            if timing_valid:
                row.update(
                    {k: t[k] for k in ("inference_s", "audio_duration_s", "rtf")}
                )
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            pass
    shared = shared_assessment(
        [
            s.get("windows", {}).get("shared_mb") if s.get("windows") else None
            for s in baseline
        ],
        [
            s.get("windows", {}).get("shared_mb") if s.get("windows") else None
            for s in samples
        ],
    )
    if method == "wddm_auto_v2":
        shared = shared_assessment(
            [s["windows"]["shared_mb"] for s in baseline],
            [s["windows"]["shared_mb"] for s in samples],
            breaks=[len(r["episode"]["originals"]) > 1 for r in records],
        )
    if method == "wddm_auto_v3":
        shared = shared_assessment(
            [s["windows"]["shared_mb"] for s in baseline],
            [s["windows"]["shared_mb"] for s in samples],
            breaks=v3_breaks,
        )
    row["shared_gpu_observed"], row["shared_gpu_peak_mb"] = (
        shared["observed"],
        shared["peak_mb"],
    )
    row["shared_baseline_mb"], row["shared_tolerance_mb"] = (
        shared["baseline_mb"],
        shared["tolerance_mb"],
    )
    for name, source in (
        ("idle_vram_used_mb", "used_mb"),
        ("idle_vram_free_mb", "free_mb"),
    ):
        values = [
            s["nvml"][source]
            for s in baseline
            if s.get("nvml")
            and type(s["nvml"].get(source)) in {int, float}
            and math.isfinite(s["nvml"][source])
        ]
        row[name] = statistics.median(values) if values else None
    memories = [
        s["wsl"]["mem_available_mb"]
        for s in samples
        if s.get("wsl") and s["wsl"].get("mem_available_mb") is not None
    ]
    swaps = [
        s["wsl"]["swap_used_mb"]
        for s in samples
        if s.get("wsl") and s["wsl"].get("swap_used_mb") is not None
    ]
    row["wsl_mem_available_mb"] = min(memories) if memories else None
    row["wsl_swap_used_mb"] = max(swaps) if swaps else None
    sensor_valid = bool(samples) and all(
        not s.get("errors")
        and s.get("browser", {}).get("visible") is True
        and s.get("windows", {}).get("gpu_mapping_status") == "resolved"
        and s.get("nvml") is not None
        and s.get("wsl") is not None
        for s in samples
    )
    if observation_context is not None:
        row.update(confidence(method))
        try:
            validate_samples(
                baseline,
                observation_context,
                now=now,
                idle=True,
                historical=True,
                method=method,
            )
            validate_samples(
                samples, observation_context, now=now, historical=True, method=method
            )
        except ValueError as error:
            sensor_valid = False
            row["observation_error"] = str(error)
            row["shared_gpu_observed"] = None
            row["shared_gpu_peak_mb"] = None
            shared["observed"] = None
    row["sensor_errors"] = sorted({e for s in samples for e in s.get("errors", [])})
    cap_valid = (
        type(row["vram_peak_mb"]) in {int, float}
        and type(row["vram_cap_mb"]) in {int, float}
        and 0 < row["vram_cap_mb"]
        and 0 <= row["vram_peak_mb"] <= row["vram_cap_mb"]
    )
    row["valid"] = bool(
        terminal["type"] == "done"
        and timing_valid
        and sensor_valid
        and cap_valid
        and shared["observed"] is not None
        and output_valid
        and fidelity_valid
    )
    if terminal["type"] == "error":
        row["error_code"] = data.get("code")
    return row


def verify_outputs(root, request, terminal, *, config, resource_root, estimate):
    """Hash + duraciÃ³n WAV + fidelidad planned/captured antes de aceptar una fila."""
    if terminal["type"] != "done":
        return False, False, {}
    data = terminal["data"]
    artifacts = data.get("artifacts", [])
    if len(artifacts) != 1 or artifacts[0].get("output_index") != 0:
        raise ValueError("output_count_mismatch")
    artifact = artifacts[0]
    expected = f"tmp/{request['job_id']}/output-0.wav"
    if artifact.get("path") != expected:
        raise ValueError("output_ownership_mismatch")
    wav = project_path(root / "data" / expected, root)
    if file_hash(wav) != artifact["sha256"]:
        raise ValueError("output_hash_mismatch")
    import soundfile as sf

    info = sf.info(wav)
    duration = info.frames / info.samplerate
    # Fuente fijada dce621: target WAV redondea a 0,1 s; la matriz usa
    # segundos enteros. conditioning_target cuantiza a latentes de 1920
    # muestras (25 Hz). Admitimos sÃ³lo un frame latente + un frame PCM,
    # nunca un porcentaje que crezca con la duraciÃ³n solicitada.
    tolerance_s = (1920 + 1) / 48000
    if not math.isclose(
        duration, request["params"]["duration_s"], rel_tol=0, abs_tol=tolerance_s
    ):
        raise ValueError("wav_requested_duration_mismatch")
    t = data["telemetry"]["extra"]["inference_timings"][0]
    if (
        info.samplerate != 48000
        or info.channels != 2
        or not math.isclose(duration, t["audio_duration_s"])
    ):
        raise ValueError("wav_timing_mismatch")
    result = data["result"]
    refs = result["input_receipts"]
    if (
        len(refs) != 1
        or refs[0].get("filename") != "input-receipt-0.json"
        or refs[0].get("output_index") != 0
    ):
        raise ValueError("input_receipt_count_mismatch")
    receipt_path = project_path(
        root / "data/tmp" / request["job_id"] / refs[0]["filename"], root
    )
    if file_hash(receipt_path) != refs[0]["sha256"]:
        raise ValueError("input_receipt_hash_mismatch")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    planned, captured = receipt["planned"], receipt["captured"]
    requested = request["params"]
    values = planned["effective"]["params"]
    expected_values = {
        "caption": requested["style"],
        "lyrics": requested["lyrics"],
        "vocal_language": requested.get("vocal_language", requested["language"]),
        "duration": requested["duration_s"],
        "seed": request["seed"],
        "bpm": requested.get("bpm"),
        "keyscale": requested.get("key", ""),
        "enable_normalization": False,
        "lm_negative_prompt": requested.get("negative_prompt", "NO USER INPUT"),
        "inference_steps": config["params"]["inference_steps"],
        "guidance_scale": config["params"].get("guidance_scale", 7),
        "shift": config["params"]["shift"],
        "use_cot_caption": False,
        "use_cot_language": False,
        "use_cot_metas": False,
    }
    if any(values.get(k) != v for k, v in expected_values.items()):
        raise ValueError("effective_input_mismatch")
    expected_config = {
        "batch_size": 1,
        "use_random_seed": False,
        "seeds": [1],
        "allow_lm_batch": False,
    }
    if planned["effective"]["config"] != expected_config:
        raise ValueError("effective_config_mismatch")
    effective = result["runtime_effective"]
    if (
        planned["receipt_version"] != 2
        or planned["profile_revision"] != "dce621408bee8c31b4fcf4811682eb9359e1bc94"
        or planned["profile_sha256"]
        != "157c33bd4ea04cd9e9a5b42094ce8a3ee1d772cf002797a398b44f56c724f4f9"
        or digest(planned["source_hashes"]) != planned["profile_sha256"]
        or digest(planned["request"]) != planned["request_sha256"]
        or digest(planned["effective"]) != planned["effective_sha256"]
        or digest(planned) != captured["planned_sha256"]
        or captured["output_index"] != 0
        or any(planned["request"].get(k) != v for k, v in request.items())
        or planned["checkpoint"]["id"] != config["checkpoint"]
        or any(effective.get(k) != config[k] for k in ("checkpoint", "lm", "mode"))
        or effective.get("resource_root") != resource_root
        or effective.get("lm_backend") != "pt"
        or estimate["input_budget"]["effective_sha256"] != planned["effective_sha256"]
        or captured["flags"].get("thinking") is not True
    ):
        raise ValueError("input_fidelity_mismatch")
    for key in ("inference_steps", "shift", "guidance_scale", "audio_cover_strength"):
        expected = config["params"].get(key, 7 if key == "guidance_scale" else 1)
        if captured["flags"].get(key) != expected:
            raise ValueError("effective_controls_mismatch")
    if captured["flags"]["lm_cfg_scale"] != 2 or any(
        captured["flags"][key] is not False
        for key in ("use_cot_caption", "use_cot_language", "use_cot_metas")
    ):
        raise ValueError("effective_lm_flags_mismatch")
    boundaries = {b["stage"]: b for b in captured["boundaries"]}
    if (
        len(captured["boundaries"]) != 5
        or len(boundaries) != 5
        or set(boundaries)
        != {
            "lm_arguments",
            "lm_formatted_prompt",
            "dit_arguments",
            "dit_resolution",
            "dit_tokens",
        }
    ):
        raise ValueError("capture_boundaries_missing")
    expected_metadata = {
        "duration": int(requested["duration_s"]),
        "language": expected_values["vocal_language"],
    }
    for key in ("bpm", "keyscale", "timesignature"):
        value = values.get(key)
        if (
            value is not None
            and value != ""
            and (key == "bpm" or value.lower() != "n/a")
        ):
            expected_metadata[key] = value
    if (
        planned["effective"].get("lm_metadata") != expected_metadata
        or boundaries["lm_arguments"].get("metadata") != expected_metadata
    ):
        raise ValueError("effective_lm_metadata_mismatch")
    # Les prÃ©images des kwargs dynamiques (codes LM, dÃ©fauts natifs) ne sont
    # pas capturÃ©es. Ce contrÃ´le vÃ©rifie la forme et la provenance du reÃ§u,
    # sans prÃ©tendre reconstruire ces hashes Ã  partir des seuls flags.
    hashes = [
        boundaries[stage].get("arguments_sha256")
        for stage in ("lm_arguments", "dit_arguments")
    ]
    hashes += [
        boundaries["lm_formatted_prompt"].get("cfg_sha256"),
        captured.get("generation_params_sha256"),
        captured.get("generation_config_sha256"),
    ]
    if any(
        not isinstance(h, str)
        or len(h) != 64
        or any(c not in "0123456789abcdef" for c in h)
        for h in hashes
    ):
        raise ValueError("capture_hash_invalid")
    if (
        boundaries["lm_formatted_prompt"].get("reserve_tokens")
        != planned["lm"]["reserve_tokens"]
    ):
        raise ValueError("lm_budget_mismatch")
    if boundaries["dit_resolution"].get("has_audio_codes") is not True:
        raise ValueError("fresh_lm_codes_missing")
    for name in ("conditional", "unconditional"):
        branch = planned["lm"][name]
        if (
            planned["lm"]["context_policy"] != 4096
            or planned["lm"]["reserve_tokens"] != int(requested["duration_s"] * 5) + 10
            or type(branch["count"]) is not int
            or not 0 <= branch["count"] <= 4096 - planned["lm"]["reserve_tokens"]
        ):
            raise ValueError("lm_budget_mismatch")
        if boundaries["lm_formatted_prompt"][name] != planned["lm"][name]:
            raise ValueError("lm_token_mismatch")
    resolution = boundaries["dit_resolution"]
    branch = planned["dit"]["candidates"][resolution["resolved_task"]]
    if any(
        resolution[k] != branch[k]
        for k in (
            "initial_task",
            "resolved_task",
            "has_audio_codes",
            "instruction_sha256",
        )
    ):
        raise ValueError("dit_resolution_mismatch")
    for name in ("text", "lyrics"):
        if type(branch[name]["count"]) is not int or not 0 <= branch[name]["count"] <= (
            256 if name == "text" else 2048
        ):
            raise ValueError("dit_budget_mismatch")
        if boundaries["dit_tokens"][name] != {
            k: branch[name][k] for k in ("count", "tokens_sha256")
        }:
            raise ValueError("dit_token_mismatch")
    if config["mode"] == "offload-int8" and (
        effective.get("int8", {}).get("quantization") != "int8_weight_only"
        or effective["int8"].get("quantized_linear_count", 0) <= 0
    ):
        raise ValueError("effective_int8_missing")
    return (
        True,
        True,
        {
            "wav_sha256": artifact["sha256"],
            "input_receipt_sha256": refs[0]["sha256"],
            "request_sha256": planned["request_sha256"],
            "effective_sha256": planned["effective_sha256"],
            "output_bytes": wav.stat().st_size,
            "frames": info.frames,
            "sample_rate": info.samplerate,
            "dynamic_arguments_hash_validation": "format_and_receipt_provenance_only",
        },
    )
