"""Benchmark T-09 canónico: /v1 real, planes privados y informe redactado."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from benchmark_evidence import (
    complete_matrix,
    enrich_rows,
    exclusive_json,
    render_report,
    seal_files,
    validate_seal,
)
from benchmark_observation import (
    accepted_samples,
    acquire_sample,
    monitored_operation,
    read_acquisitions,
    read_sealed,
    stamp,
    validate_auto,
    validate_samples,
)
from benchmark_observers import Observers
from benchmark_plan import (
    ROOT,
    build_plan,
    file_hash,
    new_id,
    project_path,
    run_request,
    verify_plan,
)
from benchmark_runner import (
    ObservationTimeout,
    execute_run,
    read_records,
    summarize_run,
    validate_prerequisites,
    verify_outputs,
)
from benchmark_runtime import (
    ApiError,
    DockerBackend,
    EngineApi,
    GpuLease,
    OllamaState,
    assert_owner,
    choose_port,
    wait_health,
)
from benchmark_windows import WindowsGpuMemory


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def prepare_group_v3(
    plan, config, storage, folder, channel, *, storage_path=None, readiness_s=3600
):
    """Creación, arranque, hashes, copia y readiness bajo el mismo sampler v3."""
    channel.coordinator.check()
    receipt = channel.operation(
        "create",
        {
            "config": config,
            "storage": storage,
            "folder": str(folder),
        },
        timeout_s=120,
        phase="container-create",
    )
    channel.operation("start", {}, timeout_s=120, phase="container-start")
    deadline = time.monotonic() + readiness_s
    while True:
        channel.coordinator.check()
        if time.monotonic() >= deadline:
            raise ApiError("CONTAINER_START_TIMEOUT")
        try:
            health = channel.operation(
                "health",
                {},
                timeout_s=min(5.5, deadline - time.monotonic()),
                phase="readiness",
            )
            if health.get("state") == "idle":
                break
        except ApiError as error:
            if error.code not in {"TRANSPORT_UNAVAILABLE", "TRANSPORT_DEADLINE"}:
                raise
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    channel.operation("source_check", {}, timeout_s=3600, phase="source-hash-copy")
    storage_path = (
        storage_path or ROOT / "data/tmp" / f"t09-storage-{config['group_id']}.json"
    )
    storage_receipt = channel.read_json(storage_path)
    expected = (
        "/models"
        if storage == "bind"
        else f"/studio/.cache/benchmark/{plan['session_id']}/models"
    )
    if (
        storage_receipt.get("resource_root") != expected
        or storage_receipt.get("destination_lock_sha256") != plan["lock_sha256"]
        or storage_receipt.get("source_lock_sha256") != plan["lock_sha256"]
    ):
        raise ValueError("storage_receipt_mismatch")
    channel.coordinator.check()
    return receipt, storage_receipt


def collect_calibration_v3(plan, run, request, folder, channel):
    """Piloto/baseline/load/unload reales sobre un solo sampler persistente.

    No determina si un sensor es sintético: los tests se identifican aparte.
    El validador canónico recomputa RAW/context/commit con anclas IPC externas.
    Una respuesta de salud cargada/descargada es obligatoria antes de cada fase.
    """
    from benchmark_episode import clock
    from benchmark_observation import acquisition_context
    from benchmark_plan import digest

    coordinator = channel.coordinator
    context = acquisition_context(coordinator.observation_context, "wddm_auto_v3")
    folder = Path(folder)
    baseline = coordinator.collect_phase("baseline", idle=True)
    terminal = execute_run(plan, run, channel, coordinator, folder / "run", request)
    lifecycle = {}
    phases = {"baseline": baseline}
    for phase in ("loaded", "unloaded"):
        if phase == "unloaded":
            channel.request("POST", "/v1/unload")
        before = clock()
        response = channel.request("GET", "/v1/health")
        finished = clock()
        if (
            response.get("state") != "idle"
            or (phase == "loaded" and not isinstance(response.get("loaded"), dict))
            or (phase == "unloaded" and response.get("loaded", "missing") is not None)
        ):
            raise ValueError("v3_calibration_owned_state_invalid")
        proof = {
            "kind": "audit_of_observed_response",
            "acquisition_context": context,
            "started_utc": before["utc"],
            "finished_utc": finished["utc"],
            "response": response,
        }
        proof_path = folder / (phase + "-health-proof.json")
        seal = channel.write_json(proof_path, proof)
        point = {
            "event": "health_loaded" if phase == "loaded" else "health_unloaded",
            "job_id": run["job_id"],
            "observed_at": finished["utc"],
            "acquisition_context": context,
            "proof": {**seal, "path": proof_path.relative_to(ROOT).as_posix()},
        }
        if phase == "unloaded":
            point["loaded"] = None
        lifecycle[phase] = point
        phases[phase] = coordinator.collect_phase(
            phase, idle=phase != "loaded", started=finished
        )
    references = {
        phase: [
            {
                "episode_id": r["supervisor_receipt"]["episode_id"],
                "receipt_sha256": digest(r["supervisor_receipt"]),
            }
            for r in records
        ]
        for phase, records in phases.items()
    }
    channel.audit_publications()
    phase_ordinals = {
        phase: [r["supervisor_receipt"]["ordinal"] for r in records]
        for phase, records in phases.items()
    }
    exported = channel.operation(
        "calibration_export",
        {
            "folder": str(folder),
            "phase_ordinals": phase_ordinals,
            "lifecycle": lifecycle,
        },
        timeout_s=3600,
    )
    return {
        **exported,
        "terminal": terminal,
        "phases": references,
        "lifecycle": lifecycle,
    }


def run_session_v3(
    plan,
    folder,
    prerequisites,
    *,
    root=ROOT,
    token=None,
    resume=False,
    coordinator=None,
    runtime_factory=None,
):
    """Una sesi?n, un sampler, piloto nuevo y matriz conservando sus IDs."""
    import copy

    from benchmark_coordinator import (
        ContinuousCoordinator,
        CoordinatedOwnedProcess,
        RuntimeChannel,
        cleanup_error_record,
    )
    from benchmark_episode import EpisodeAcquirer, clock
    from benchmark_plan import digest

    folder, root = Path(folder), Path(root)
    observation = prerequisites.get("observation", {})
    context = observation.get("context", {})
    if (
        observation.get("method") != "wddm_auto_v3"
        or prerequisites.get("exclusive_gpu_authorized") is not True
    ):
        raise ValueError("v3_fresh_context_and_exclusive_authorization_required")
    if any(
        context.get(key) != plan[key]
        for key in (
            "session_id",
            "plan_sha256",
            "source_hashes",
            "image_id",
            "lock_sha256",
        )
    ):
        raise ValueError("v3_new_plan_context_required")
    if len(plan["runs"]) != 160:
        raise ValueError("auto_complete_source_and_matrix_required")
    own_service = coordinator is None
    if own_service and resume and (folder / "owner.json").exists():
        # Une nouvelle cadence ne pardonne jamais une interruption précédente.
        raise ValueError("v3_broken_session_requires_owned_recovery_new_plan")
    owner_path = folder / "owner.json"
    owner = (
        read_json(owner_path)
        if owner_path.exists()
        else {
            "owner": new_id(),
            "session_id": plan["session_id"],
            "plan_sha256": plan["plan_sha256"],
        }
    )
    if not owner_path.exists():
        exclusive_json(owner_path, owner)
    config = {
        "root": str(root),
        "plan_path": str(folder / "plan.json"),
        "owner_path": str(owner_path),
        "token": token or os.environ.get("STUDIO_ENGINE_TOKEN"),
        "supervisor_pid": os.getpid(),
    }
    channel = None
    before = None
    active_group = None
    lease_acquired = False
    rows = []
    if own_service:
        context_path = folder / "observation-context.json"
        exclusive_json(context_path, context)
        acquirer = EpisodeAcquirer(
            root=folder / "publications",
            context_path=context_path,
            sensor_config={"browser": prerequisites["browser"]},
        )
        try:
            coordinator = ContinuousCoordinator(acquirer)
        except BaseException as primary:
            try:
                acquirer.close()
            except BaseException as cleanup:  # noqa: BLE001 - preservar primera causa y custodiar fallo secundario
                from benchmark_coordinator import cleanup_error_record

                record = cleanup_error_record(cleanup)
                primary.add_note(f"owned_acquirer_cleanup={record}")
                try:
                    exclusive_json(
                        folder / f"initialization-cleanup-{new_id()}.json", record
                    )
                except BaseException as journal_error:  # noqa: BLE001 - preservar primera causa y custodiar fallo secundario
                    primary.add_note(
                        f"cleanup_journal={cleanup_error_record(journal_error)}"
                    )
            raise
        coordinator.__enter__()
    elif coordinator.observation_context != context:
        raise ValueError("v3_coordinator_context_mismatch")
    try:
        audit_binding = {
            "root": str(coordinator.acquirer.root),
            "context": context,
            "stream": new_id(),
        }
        binding_path = folder / "audit-transport-binding.json"
        exclusive_json(binding_path, audit_binding)
        config.update(
            audit_binding_path=str(binding_path),
            audit_binding_sha256=digest(audit_binding),
        )
        worker = (
            runtime_factory(config, coordinator=coordinator)
            if runtime_factory
            else CoordinatedOwnedProcess(
                config,
                "benchmark_runtime:BenchmarkOperationProvider",
                coordinator=coordinator,
            )
        )
        channel = RuntimeChannel(coordinator, worker, audit_binding=audit_binding)
        channel.operation("verify_plan", {}, timeout_s=3600, phase="source-plan-check")
        from benchmark_runtime import supervisor_identity

        lease_intent_path = folder / "lease-intent.json"
        lease_intent = {
            **owner,
            **supervisor_identity(),
            "nonce": new_id(),
            "ack_state": "unknown",
            "operation": "lease_acquire",
        }
        exclusive_json(lease_intent_path, lease_intent)
        config["lease_intent_path"] = str(lease_intent_path)
        channel.operation(
            "lease_acquire", {"resume": resume, "intent_path": str(lease_intent_path)}
        )
        lease_acquired = True
        config["lease_acknowledged"] = True
        exclusive_json(
            folder / "lease-ack.json",
            {"nonce": lease_intent["nonce"], "ack_state": "acquired"},
        )
        before = channel.operation("ollama_snapshot", {}, timeout_s=120)
        channel.write_json(folder / "ollama-before.json", before)
        channel.operation("ollama_discharge", {"state": before}, timeout_s=3600)
        accreditation = None
        accreditation_path = None
        for offset in range(0, 160, 4):
            group = plan["runs"][offset : offset + 4]
            group_folder = folder / "groups" / group[0]["run_id"]
            selected_config = {
                **next(
                    c
                    for c in plan["configs"]
                    if c["config_id"] == group[0]["config_id"]
                ),
                "group_id": group[0]["run_id"],
            }
            active_group = {
                "folder": str(group_folder),
                "config": selected_config,
                "storage": group[0]["storage"],
            }
            _receipt, storage = prepare_group_v3(
                plan,
                selected_config,
                group[0]["storage"],
                group_folder,
                channel,
                storage_path=root
                / "data/tmp"
                / f"t09-storage-{group[0]['run_id']}.json",
            )
            storage_seal = channel.write_json(group_folder / "storage.json", storage)
            if accreditation is None:
                pilot = {
                    **group[0],
                    "run_id": new_id(),
                    "job_id": new_id(),
                    "parent_run_id": group[0]["run_id"],
                    "purpose": "v3_calibration_pilot",
                }
                pilot_folder = folder / "pilot-v3"
                channel.write_json(pilot_folder / "pilot.json", pilot)
                request = channel.operation("request_for_run", {"run": pilot})
                calibration = collect_calibration_v3(
                    plan, pilot, request, pilot_folder, channel
                )
                originals = {
                    **calibration["originals"],
                    "host": observation["evidence"]["host"]["path"],
                }
                accreditation = channel.operation(
                    "accreditation",
                    {
                        "originals": originals,
                        "viewport_path": observation["viewport"]["evidence"]["path"],
                        "exclusive_gpu_authorized": True,
                    },
                    timeout_s=3600,
                )
                accreditation_path = pilot_folder / "prerequisites.json"
                channel.write_json(accreditation_path, accreditation)
            baseline_records = coordinator.collect_phase("baseline", idle=True)
            baseline_ordinals = [
                r["supervisor_receipt"]["ordinal"] for r in baseline_records
            ]
            for run in group:
                coordinator.check()
                channel.audit_publications()
                renewed = channel.operation(
                    "refresh_accreditation",
                    {
                        "observation_path": str(accreditation_path),
                        "path": str(group_folder / f"publications-{new_id()}.json"),
                    },
                    timeout_s=3600,
                )
                accreditation_path = group_folder / f"prerequisites-{new_id()}.json"
                channel.write_json(
                    accreditation_path,
                    {
                        "observation": renewed["observation"],
                        "browser": prerequisites["browser"],
                        "exclusive_gpu_authorized": True,
                    },
                )
                if run["phase"] == "process_cold":
                    channel.request("POST", "/v1/unload")
                    if (
                        channel.request("GET", "/v1/health").get("loaded", "missing")
                        is not None
                    ):
                        raise ValueError("cold_process_not_unloaded")
                first_ordinal = coordinator.receipts[-1]["ordinal"] + 1
                request = channel.operation("request_for_run", {"run": run})
                run_folder = folder / "runs" / run["run_id"]
                execute_run(plan, run, channel, coordinator, run_folder, request)
                coordinator.wait_samples(1, timeout_s=3)
                last_ordinal = coordinator.receipts[-1]["ordinal"]
                channel.audit_publications()
                row = channel.operation(
                    "row",
                    {
                        "run": run,
                        "config": selected_config,
                        "folder": str(run_folder),
                        "resource_root": storage["resource_root"],
                        "baseline_ordinals": baseline_ordinals,
                        "first_ordinal": first_ordinal,
                        "last_ordinal": last_ordinal,
                        "storage_fields": {
                            "storage_receipt_sha256": storage_seal["sha256"],
                            "copy_s": storage["copy_s"],
                        },
                    },
                    timeout_s=3600,
                )
                rows.append(row)
            cleanup = channel.operation(
                "cleanup", {}, timeout_s=120, phase="engine-cleanup"
            )
            channel.write_json(group_folder / "cleanup.json", cleanup)
            coordinator.collect_phase("post-unload", count=1, idle=True, timeout_s=3)
            active_group = None
        restored = channel.operation(
            "ollama_restore", {"state": before}, timeout_s=3600
        )
        channel.write_json(folder / "restore.json", restored)
        channel.operation("lease_release", {})
        lease_acquired = False
        channel.audit_publications()
        return rows
    except BaseException as primary:
        try:
            # Reconciliar sólo la identidad propia; no repetir create ni POST.
            from benchmark_runtime import recover_owned_runtime

            recovery = (
                recover_owned_runtime(
                    config,
                    active_group,
                    before,
                    release_lease=lease_acquired,
                    runtime_factory=runtime_factory,
                )
                if channel is not None
                else {"disposition": "not_started", "reservation_retained": False}
            )
            recovery["original_error"] = str(sys.exc_info()[1])
            recovery["action"] = "new_v3_plan_after_owned_reconciliation_without_replay"
            recovery["supersedes_provisional_query_same_job"] = (
                recovery["disposition"] != "terminal_preserved"
            )
            recovery["jobs"] = []
            from benchmark_runner import read_records

            for intent_path in sorted(folder.rglob("submission-intent.json")):
                job = {
                    "job_id": None,
                    "intent_path": intent_path.relative_to(folder).as_posix(),
                    "intent_sha256": None,
                    "cursor": None,
                    "events_sha256": None,
                    "terminal_sha256": None,
                }
                try:
                    job["intent_sha256"] = file_hash(intent_path)
                    job["job_id"] = read_json(intent_path)["job_id"]
                    terminal_path = intent_path.parent / "terminal.json"
                    if terminal_path.exists():
                        job["terminal_sha256"] = file_hash(terminal_path)
                    events_path = intent_path.parent / "events.ndjson"
                    if events_path.exists():
                        job["events_sha256"] = file_hash(events_path)
                    job["cursor"] = len(read_records(events_path))
                except (OSError, ValueError, KeyError, TypeError) as inventory_error:
                    # Custodiar los bytes parciales no convierte un cursor desconocido
                    # en cero ni sustituye la causa que activó la recuperación.
                    job["inventory_error"] = str(inventory_error)
                recovery["jobs"].append(job)
            exclusive_json(folder / f"recovery-{new_id()}.json", recovery)
        except BaseException as secondary:  # noqa: BLE001 - preservar primera causa y custodiar fallo secundario
            from benchmark_coordinator import cleanup_error_record

            record = cleanup_error_record(secondary)
            coordinator.events.append({"recovery_error": record})
            primary.add_note(f"owned_recovery_secondary={record}")
        raise
    finally:
        original_error = sys.exc_info()[1]
        shutdown_error = None
        try:
            if channel is not None:
                channel.close()
        except BaseException as error:  # noqa: BLE001 - terminar ambos recursos y conservar el fallo original
            shutdown_error = error
        if own_service:
            try:
                coordinator.close(raise_failure=True)
            except BaseException as error:  # noqa: BLE001 - audit final obligatorio incluso si falla el cierre
                if shutdown_error is None:
                    shutdown_error = error
            # Audit final tras shutdown; no atribuir timestamps de escritura original.
            final = {
                "kind": "audit_after_graceful_shutdown",
                "audited_at": clock(),
                "context": context,
                "publication_root": str(coordinator.acquirer.root),
                "receipts": copy.deepcopy(coordinator.receipts),
                "attempts": copy.deepcopy(coordinator.attempts),
                "events": copy.deepcopy(coordinator.events),
                "shutdown_error": None
                if shutdown_error is None
                else cleanup_error_record(shutdown_error),
                "failure": None
                if coordinator.failure is None and shutdown_error is None
                else str(coordinator.failure or shutdown_error),
            }
            try:
                exclusive_json(folder / "supervisor-final-audit.json", final)
                print(
                    f"benchmark: supervisor_anchor_sha256={digest(final)} receipts={len(final['receipts'])} attempts={len(final['attempts'])}"
                )
            except BaseException as error:  # noqa: BLE001 - audit final obligatorio incluso si falla el cierre
                from benchmark_coordinator import cleanup_error_record

                record = cleanup_error_record(error)
                coordinator.events.append({"final_audit_error": record})
                if original_error is not None:
                    original_error.add_note(f"final_audit_secondary={record}")
                if shutdown_error is None:
                    shutdown_error = error
        if shutdown_error is not None and original_error is None:
            raise shutdown_error


def engine_token(root):
    token = os.environ.get("STUDIO_ENGINE_TOKEN")
    if not token:
        from dotenv import dotenv_values

        token = dotenv_values(root / ".env").get("STUDIO_ENGINE_TOKEN")
    if not token:
        raise ValueError("engine_token_required")
    return token


def observed_baseline(observers, folder, *, interval=1, sleep=time.sleep):
    samples = []
    for _ in range(10):
        sample_started = time.monotonic()
        value = acquire_sample(observers, folder / "baseline.ndjson", idle=True)
        samples.append(value)
        sleep(max(0, interval - (time.monotonic() - sample_started)))
    if any(
        s.get("errors")
        or not s.get("browser", {}).get("visible")
        or not s.get("nvml")
        or s["nvml"]["used_mb"] > 1600
        or not s.get("windows")
        or s["windows"].get("shared_mb") is None
        or s["windows"].get("gpu_mapping_status") != "resolved"
        for s in samples
    ):
        raise ValueError("baseline_or_browser_or_wddm_invalid")
    if getattr(observers, "observation_context", None) is not None:
        validate_samples(
            samples,
            observers.observation_context,
            idle=True,
            method=getattr(observers, "observation_method", "wddm_auto_v1"),
        )
    return samples


def group_attempt(folder, nominal, *, retry=False):
    """Linaje aditivo: cada intento conserva IDs, recursos y pruebas anteriores."""
    base = folder / "groups" / nominal[0]["run_id"]
    attempts = sorted(base.glob("retry-attempt-*.json"))
    if attempts:
        saved = read_json(attempts[-1])
        group = saved["runs"]
        if any(
            r["parent_run_id"] != n["run_id"] or r["parent_job_id"] != n["job_id"]
            for r, n in zip(group, nominal, strict=True)
        ):
            raise ValueError("retry_lineage_mismatch")
        path = base / "attempts" / saved["attempt_id"]
    else:
        group, path = nominal, base
    cleaned = sorted(path.glob("cleanup-after-error-*.json"))
    if retry and cleaned and not (path / "cleanup.json").exists():
        receipt = read_json(cleaned[-1])
        if receipt.get("removed") is not True:
            raise ValueError("cleanup_not_verified")
        if receipt.get("submission_possible"):
            if all(
                (folder / "runs" / r["run_id"] / "row.json").exists() for r in group
            ):
                for run in group:
                    run_folder = folder / "runs" / run["run_id"]
                    validate_seal(run_folder, read_json(run_folder / "seal.json"))
                exclusive_json(
                    path / "cleanup.json", {**receipt, "recovered_from_error": True}
                )
                return group, path
            raise ValueError("removed_container_has_submitted_job_requires_inspection")
        attempt_id = new_id()
        replacement = [
            {
                **n,
                "run_id": new_id(),
                "job_id": new_id(),
                "parent_run_id": n["run_id"],
                "parent_job_id": n["job_id"],
                "previous_run_id": r["run_id"],
            }
            for n, r in zip(nominal, group, strict=True)
        ]
        exclusive_json(
            base / f"retry-attempt-{attempt_id}.json",
            {
                "attempt_id": attempt_id,
                "previous_container_id": receipt["container_id"],
                "runs": replacement,
            },
        )
        group, path = replacement, base / "attempts" / attempt_id
    return group, path


def session_rows(folder, plan):
    rows = []
    actual = {}
    for offset in range(0, len(plan["runs"]), 4):
        nominal = plan["runs"][offset : offset + 4]
        group, _ = group_attempt(folder, nominal)
        actual.update({n["run_id"]: r for n, r in zip(nominal, group, strict=True)})
    for nominal in plan["runs"]:
        run = actual[nominal["run_id"]]
        path = folder / "runs" / run["run_id"] / "row.json"
        if path.exists():
            row = read_json(path)
            if row.get("run_id") != run["run_id"] or row.get("job_id") != run["job_id"]:
                raise ValueError("row_identity_mismatch")
            seal = folder / "runs" / run["run_id"] / "seal.json"
            if not seal.exists():
                raise ValueError("row_seal_missing")
            validate_seal(path.parent, read_json(seal))
            rows.append(
                {
                    **row,
                    "actual_run_id": run["run_id"],
                    "actual_job_id": run["job_id"],
                    "run_id": nominal["run_id"],
                    "job_id": nominal["job_id"],
                }
            )
    return enrich_rows(rows)


def run_session(
    plan,
    folder,
    prerequisites,
    *,
    root=ROOT,
    backend=None,
    observer_factory=None,
    api_factory=EngineApi,
    ollama=None,
    token=None,
    resume=False,
    coordinator=None,
    runtime_factory=None,
):
    if plan.get("observation_method") == "wddm_auto_v3":
        return run_session_v3(
            plan,
            folder,
            prerequisites,
            root=root,
            token=token,
            resume=resume,
            coordinator=coordinator,
            runtime_factory=runtime_factory,
        )
    method = plan.get("observation_method", "task_manager_v1")
    if method in {"wddm_auto_v1", "wddm_auto_v2"}:
        raise ValueError("auto_legacy_policy_read_only_new_session_required")
    if method != "task_manager_v1":
        raise ValueError("unknown_observation_method")
    automatic = False
    if automatic:
        prerequisites = validate_prerequisites(
            prerequisites,
            root,
            plan=plan,
            continued_samples=read_records(folder / "observation-continuity.ndjson"),
        )
    if (folder / "restore.json").exists() and all(
        (
            group_attempt(folder, plan["runs"][offset : offset + 4])[1] / "cleanup.json"
        ).exists()
        for offset in range(0, len(plan["runs"]), 4)
    ):
        return session_rows(folder, plan)
    backend = backend or DockerBackend(root=root)
    ollama = ollama or OllamaState()
    token = token or engine_token(root)
    owner_path = folder / "owner.json"
    if owner_path.exists():
        owner = read_json(owner_path)
    else:
        owner = {
            "owner": new_id(),
            "session_id": plan["session_id"],
            "plan_sha256": plan["plan_sha256"],
        }
        exclusive_json(owner_path, owner)
    if any(owner.get(k) != plan[k] for k in ("session_id", "plan_sha256")):
        raise ValueError("session_owner_mismatch")
    lease = GpuLease(root / ".cache/dev-cycle/t09/gpu.lock", owner)
    lease.acquire(resume=resume)
    current_receipt = None
    current_api = None
    active_run = None
    observations = None
    state_path = folder / "ollama-before.json"
    preserve = False
    all_clean = True
    create_uncertain = False
    try:
        before = read_json(state_path) if state_path.exists() else ollama.snapshot()
        if not state_path.exists():
            exclusive_json(state_path, before)
        ollama.discharge(before)
        gpu = (
            Observers(None, browser={}).nvidia()
            if observer_factory is None
            else observer_factory(None).nvidia()
        )
        windows = WindowsGpuMemory(gpu["name"]) if observer_factory is None else None
        observations = (
            Observers(windows, browser=prerequisites["browser"])
            if observer_factory is None
            else observer_factory(windows)
        )
        if automatic:
            observations.observation_context = prerequisites["accreditation"]["context"]
            observations.observation_method = plan["observation_method"]
            observations.previous_sample = None
            observations.previous_episode = None
            observations.continued_samples = read_records(
                folder / "observation-continuity.ndjson"
            )
            if (
                plan["observation_method"] == "wddm_auto_v2"
                and not observations.continued_samples
            ):
                from benchmark_runner import append_record

                observations.continued_samples = read_records(
                    read_sealed(
                        prerequisites["observation"]["evidence"]["continuity"], root
                    )
                )
                for record in observations.continued_samples:
                    append_record(folder / "observation-continuity.ndjson", record)
            if (
                observations.continued_samples
                and plan["observation_method"] == "wddm_auto_v2"
            ):
                accepted_samples(
                    observations.continued_samples,
                    observations.observation_context,
                    historical=True,
                    complete_chain=True,
                )
                observations.previous_sample = observations.continued_samples[-1][
                    "sample"
                ]
                observations.previous_episode = observations.continued_samples[-1][
                    "episode"
                ]
            observations.continuity_path = folder / "observation-continuity.ndjson"
        if windows is not None:
            metadata = folder / "windows-mapping.json"
            if not metadata.exists():
                exclusive_json(
                    metadata,
                    {
                        "adapters": windows.adapters,
                        "instance": windows.instance,
                        "paths": windows.paths,
                        "nvml": gpu,
                    },
                )
        if gpu["name"] != "NVIDIA GeForce RTX 5070" or (
            gpu["used_mb"] > 1600 and not resume
        ):
            raise ValueError("gpu_baseline_failed")
        for offset in range(0, len(plan["runs"]), 4):
            if automatic:
                validate_auto(
                    prerequisites["observation"],
                    root,
                    plan=plan,
                    continued_samples=observations.continued_samples,
                )
            nominal_group = plan["runs"][offset : offset + 4]
            group, group_folder = group_attempt(folder, nominal_group, retry=resume)
            if len(group) != 4 or any(
                (r["config_id"], r["duration_s"], r["storage"])
                != (group[0]["config_id"], group[0]["duration_s"], group[0]["storage"])
                for r in group
            ):
                raise ValueError("invalid_run_group")
            group_id = group[0]["run_id"]
            group_folder.mkdir(parents=True, exist_ok=True)
            if (group_folder / "cleanup.json").exists():
                if not all(
                    (folder / "runs" / r["run_id"] / "row.json").exists() for r in group
                ):
                    raise ValueError("cleaned_group_has_missing_rows")
                continue
            config = {
                **next(
                    c
                    for c in plan["configs"]
                    if c["config_id"] == group[0]["config_id"]
                ),
                "group_id": group_id,
            }
            container_receipt = group_folder / "container.json"
            if container_receipt.exists():
                current_receipt = read_json(container_receipt)
                inspection = backend.inspect(current_receipt["container_id"])
                assert_owner(current_receipt, inspection)
                if inspection.get("Image") != plan["image_id"]:
                    raise ValueError("resume_image_changed")
            else:
                intent_path = group_folder / "create-intent.json"
                if intent_path.exists():
                    # No duplicate container after uncertain create acknowledgement.
                    raise ValueError("container_create_intent_needs_owner_recovery")
                exclusive_json(
                    intent_path,
                    {**owner, "group_id": group_id, "storage": group[0]["storage"]},
                )
                create_uncertain = True
                current_receipt = backend.create(
                    plan,
                    config,
                    group[0]["storage"],
                    owner["owner"],
                    choose_port(),
                    token,
                )
                exclusive_json(container_receipt, current_receipt)
                backend.start(current_receipt)
            current_api = api_factory(current_receipt["port"], token)
            # Preparation hashes/copying may be long; this is not measured load.
            wait_health(
                current_api,
                backend,
                current_receipt,
                deadline=time.monotonic() + 3600,
                allow_active=resume and container_receipt.exists(),
            )
            backend.verify_image_sources(current_receipt, plan)
            storage_path = project_path(
                root / "data/tmp" / f"t09-storage-{group_id}.json", root
            )
            storage_receipt = read_json(storage_path)
            resource_root = (
                "/models"
                if group[0]["storage"] == "bind"
                else f"/studio/.cache/benchmark/{plan['session_id']}/models"
            )
            if (
                storage_receipt["resource_root"] != resource_root
                or storage_receipt["destination_lock_sha256"] != plan["lock_sha256"]
                or storage_receipt["source_lock_sha256"] != plan["lock_sha256"]
            ):
                raise ValueError("storage_receipt_mismatch")
            if not (group_folder / "storage.json").exists():
                exclusive_json(group_folder / "storage.json", storage_receipt)
            if automatic and plan["observation_method"] == "wddm_auto_v1":
                observations.previous_sample = None
            baseline_file = group_folder / "baseline.ndjson"
            if baseline_file.exists():
                baseline_records = read_acquisitions(
                    baseline_file,
                    getattr(observations, "observation_context", None),
                    idle=True,
                    historical=resume,
                )
                baseline = accepted_samples(
                    baseline_records,
                    getattr(observations, "observation_context", None),
                    idle=True,
                    historical=resume,
                )
                if len(baseline) != 10:
                    raise ValueError("baseline_evidence_incomplete")
                if automatic:
                    validate_samples(
                        baseline,
                        observations.observation_context,
                        idle=True,
                        historical=resume,
                        method=plan["observation_method"],
                    )
            else:
                baseline = observed_baseline(observations, group_folder)
            if automatic and resume:
                # The old baseline remains historical during an owned active job.
                # A new idle baseline is acquired only after actual health proves idle.
                health = current_api.request("GET", "/v1/health")
                if (
                    health.get("loaded", "missing") is None
                    and health.get("state") == "idle"
                ):
                    fresh_folder = group_folder / ("resume-baseline-" + new_id())
                    fresh_folder.mkdir()
                    baseline = observed_baseline(observations, fresh_folder)
            # Legacy resume observation preserves its original evidence.
            if resume:
                resume_sample = acquire_sample(
                    observations, group_folder / f"resume-observation-{new_id()}.ndjson"
                )
                if not resume_sample.get("browser", {}).get("visible"):
                    raise ValueError("resume_browser_not_visible")
            for run in group:
                active_run = run
                run_folder = folder / "runs" / run["run_id"]
                row_file = run_folder / "row.json"
                if row_file.exists():
                    validate_seal(run_folder, read_json(run_folder / "seal.json"))
                    continue
                request = run_request(plan, run, root)
                if (
                    run["phase"] == "process_cold"
                    and not (run_folder / "submission-intent.json").exists()
                ):
                    if automatic:
                        monitored_operation(
                            lambda api=current_api: api.request("POST", "/v1/unload"),
                            observations,
                            group_folder,
                            "cold-unload",
                        )
                    else:
                        current_api.request("POST", "/v1/unload")
                    health = current_api.request("GET", "/v1/health")
                    if health["loaded"] is not None:
                        raise ValueError("cold_process_not_unloaded")
                    if automatic:
                        acquire_sample(
                            observations, group_folder / "cold-unload-observers.ndjson"
                        )
                terminal = execute_run(
                    plan, run, current_api, observations, run_folder, request
                )
                samples = read_acquisitions(
                    run_folder / "observers.ndjson",
                    getattr(observations, "observation_context", None),
                )
                estimate = read_json(run_folder / "estimate.json")
                output_valid, fidelity_valid, output = verify_outputs(
                    root,
                    request,
                    terminal,
                    config=config,
                    resource_root=resource_root,
                    estimate=estimate,
                )
                row = summarize_run(
                    run,
                    terminal,
                    samples,
                    baseline,
                    output_valid=output_valid,
                    fidelity_valid=fidelity_valid,
                    observation_context=getattr(
                        observations, "observation_context", None
                    ),
                )
                row.update(output)
                row["storage_receipt_sha256"] = file_hash(group_folder / "storage.json")
                row["copy_s"] = storage_receipt["copy_s"]
                if (
                    config["config_id"] == "xl-turbo-lm06-int8"
                    and row.get("error_code") == "VRAM_EXCEEDED"
                ):
                    cap = (
                        current_api.request("GET", "/v1/health")
                        .get("gpu", {})
                        .get("cap_mb")
                    )
                    if type(cap) in {int, float} and cap > 0:
                        row["status"] = "hardware_not_feasible"
                        row["hardware_evidence_sha256"] = file_hash(
                            run_folder / "terminal.json"
                        )
                        row["vram_cap_mb"] = cap
                exclusive_json(row_file, row)
                exclusive_json(run_folder / "seal.json", seal_files(run_folder))
            active_run = None
            wait_health(
                current_api, backend, current_receipt, deadline=time.monotonic() + 30
            )
            if automatic:
                acquire_sample(
                    observations, group_folder / "pre-unload-observers.ndjson"
                )
            cleanup = (
                monitored_operation(
                    lambda receipt=current_receipt, api=current_api: backend.cleanup(
                        receipt, api
                    ),
                    observations,
                    group_folder,
                    "cleanup",
                )
                if automatic
                else backend.cleanup(current_receipt, current_api)
            )
            exclusive_json(group_folder / "cleanup.json", cleanup)
            current_receipt = current_api = None
            create_uncertain = False
            acquire_sample(
                observations, group_folder / "post-unload-observation.ndjson", idle=True
            )
        restored = ollama.restore(before)
        exclusive_json(folder / "restore.json", restored)
        lease.release()
        return session_rows(folder, plan)
    except ObservationTimeout:
        preserve = True
        raise
    except (Exception, KeyboardInterrupt):
        # Cancel only the existing own job; failure to see terminal preserves the resource.
        if create_uncertain and current_api is None:
            all_clean = False
        if current_receipt is not None and current_api is not None:
            try:
                if active_run is not None:
                    run_folder = folder / "runs" / active_run["run_id"]
                    if (run_folder / "submission-intent.json").exists() and not (
                        run_folder / "terminal.json"
                    ).exists():
                        current_api.request(
                            "DELETE", f"/v1/jobs/{active_run['job_id']}"
                        )
                        from benchmark_runner import observe_job

                        terminal, _ = observe_job(
                            current_api,
                            observations,
                            active_run["job_id"],
                            run_folder,
                            observation_s=60,
                            enforce_observation=False,
                        )
                        exclusive_json(run_folder / "terminal.json", terminal)
                cleanup = backend.cleanup(current_receipt, current_api)
                exclusive_json(
                    group_folder / f"cleanup-after-error-{new_id()}.json",
                    {
                        **cleanup,
                        "container_id": current_receipt["container_id"],
                        "submission_possible": any(
                            (
                                folder / "runs" / r["run_id"] / "submission-intent.json"
                            ).exists()
                            for r in group
                        ),
                    },
                )
            except (Exception, KeyboardInterrupt):  # noqa: BLE001 - restauración; nunca ocultar bloqueo de recursos
                all_clean = False
        if all_clean:
            try:
                if state_path.exists():
                    exclusive_json(
                        folder / f"restore-after-error-{new_id()}.json",
                        ollama.restore(read_json(state_path)),
                    )
                lease.release()
            except (Exception, KeyboardInterrupt):  # noqa: BLE001 - restauración; nunca ocultar bloqueo de recursos
                preserve = True
        else:
            preserve = True
        raise
    finally:
        if (
            observations is not None
            and getattr(observations, "windows", None) is not None
        ):
            observations.windows.close()
        if preserve:
            exclusive_json(
                folder / f"resume-required-{new_id()}.json",
                {
                    "existing_resources_preserved": True,
                    "job_id": active_run["job_id"] if active_run else None,
                    "session_id": plan["session_id"],
                },
            )


def parser():
    value = argparse.ArgumentParser(
        description="Medición real de la matriz T-09; prepare-only no publica benchmark."
    )
    value.add_argument("--matrix", choices=["default"], default="default")
    value.add_argument("--inputs", default=os.getenv("STUDIO_BENCHMARK_INPUTS"))
    value.add_argument(
        "--prerequisites", default=os.getenv("STUDIO_BENCHMARK_PREREQUISITES")
    )
    value.add_argument("--image", default=os.getenv("STUDIO_BENCHMARK_IMAGE"))
    value.add_argument("--prepare-only", action="store_true")
    value.add_argument(
        "--observation-method",
        choices=["task_manager_v1", "wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"],
        default="wddm_auto_v3",
    )
    value.add_argument("--resume")
    value.add_argument(
        "--supervisor-anchor-sha256",
        help="Digest externo del audit final del supervisor para releer un cierre v3",
    )
    return value


def finished_session(
    folder, *, root=ROOT, prerequisites=None, supervisor_anchor_sha256=None
):
    """Releer un cierre sellado sin relanzar recursos ni publicar otra vista."""
    if not (folder / "summary.json").exists():
        return None
    validate_seal(folder, read_json(folder / "seal.json"))
    saved_plan = (
        read_json(folder / "plan.json") if (folder / "plan.json").exists() else {}
    )
    if saved_plan.get("observation_method") in {
        "wddm_auto_v1",
        "wddm_auto_v2",
        "wddm_auto_v3",
    }:
        if prerequisites is None:
            raise ValueError("auto_finished_prerequisites_required")
        external = {}
        continued = read_records(folder / "observation-continuity.ndjson")
        if saved_plan.get("observation_method") == "wddm_auto_v3":
            from benchmark_calibration_v3 import safe_path
            from benchmark_episode import read_publications
            from benchmark_plan import digest

            anchor = read_json(folder / "supervisor-final-audit.json")
            if (
                not supervisor_anchor_sha256
                or digest(anchor) != supervisor_anchor_sha256
            ):
                raise ValueError("external_supervisor_anchor_required_or_mismatch")
            if (
                anchor.get("kind") != "audit_after_graceful_shutdown"
                or anchor.get("failure") is not None
            ):
                raise ValueError("external_supervisor_anchor_failed_session")
            read_publications(
                safe_path(anchor["publication_root"], root),
                anchor["receipts"],
                anchor["context"],
                trusted_receipts=anchor["receipts"],
                attempts=anchor["attempts"],
                trusted_attempts=anchor["attempts"],
                historical=True,
            )
            publication = read_json(
                read_sealed(
                    prerequisites["observation"]["evidence"]["publications"], root
                )
            )
            receipts = anchor["receipts"][: len(publication["receipts"])]
            attempts = anchor["attempts"][: len(publication["attempts"])]
            if (
                publication["receipts"] != receipts
                or publication["attempts"] != attempts
            ):
                raise ValueError("external_supervisor_anchor_prefix_mismatch")
            external = {
                "trusted_receipts": receipts,
                "trusted_attempts": attempts,
                "now": stamp(receipts[-1]["observed_utc"]),
            }
            continued = receipts
        validate_prerequisites(
            prerequisites,
            root,
            plan=saved_plan,
            continued_samples=continued,
            **external,
        )
    summary = read_json(folder / "summary.json")
    print(
        f"benchmark: rows={summary['rows']} complete={str(summary['complete']).lower()}"
    )
    return 0 if summary["complete"] else 2


def main(argv=None, *, root=ROOT, backend=None):
    args = parser().parse_args(argv)
    root = Path(root).resolve()
    folder = None
    plan = None
    try:
        if args.resume:
            if (
                not all(c in "0123456789ABCDEFGHJKMNPQRSTVWXYZ" for c in args.resume)
                or len(args.resume) != 26
            ):
                raise ValueError("invalid_session_id")
            folder = project_path(
                root / ".cache/dev-cycle/t09/runtime" / args.resume, root
            )
            plan = read_json(folder / "plan.json")
            if plan.get("observation_method") != "wddm_auto_v3":
                verify_plan(plan, root)
            finished = finished_session(
                folder,
                root=root,
                prerequisites=read_json(project_path(args.prerequisites, root))
                if args.prerequisites
                else None,
                supervisor_anchor_sha256=args.supervisor_anchor_sha256,
            )
            if finished is not None:
                return finished
            if plan.get("observation_method") in {"wddm_auto_v1", "wddm_auto_v2"}:
                raise ValueError("auto_legacy_policy_read_only_new_session_required")
            if not args.prerequisites:
                raise ValueError("prerequisites_required")
        else:
            if not args.inputs or not args.image:
                print(
                    "benchmark: configuration_required (--inputs, --image; ejecución real también --prerequisites)"
                )
                return 2
            if not args.prepare_only and args.observation_method in {
                "wddm_auto_v1",
                "wddm_auto_v2",
            }:
                raise ValueError("auto_legacy_policy_read_only_new_session_required")
            inputs_path = project_path(args.inputs, root)
            prerequisite_path = (
                project_path(args.prerequisites, root) if args.prerequisites else None
            )
            if not args.prepare_only and prerequisite_path is None:
                raise ValueError("prerequisites_required")
            backend = backend or DockerBackend(root=root)
            image_id = (
                args.image
                if args.prepare_only or args.observation_method == "wddm_auto_v3"
                else backend.image_id(args.image)
            )
            plan = build_plan(
                read_json(inputs_path),
                image_id=image_id,
                prerequisites_sha256=file_hash(prerequisite_path)
                if prerequisite_path
                else None,
                root=root,
                observation_method=args.observation_method,
            )
            folder = root / ".cache/dev-cycle/t09/runtime" / plan["session_id"]
            folder.mkdir(parents=True, exist_ok=False)
            exclusive_json(folder / "plan.json", plan)
        print(f"benchmark: session={plan['session_id']} jobs={len(plan['runs'])}")
        if args.prepare_only:
            print("benchmark: CPU plan preparado; ninguna medición ni informe público")
            return 0
        prerequisite_path = project_path(args.prerequisites, root)
        if (
            not (
                plan.get("observation_method")
                in {"wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"}
                and plan["prerequisites_sha256"] is None
            )
            and file_hash(prerequisite_path) != plan["prerequisites_sha256"]
        ):
            raise ValueError("prerequisites_changed_new_session_required")
        prerequisites = read_json(prerequisite_path)
        if plan.get("observation_method") != "wddm_auto_v3":
            prerequisites = validate_prerequisites(
                prerequisites,
                root,
                plan=plan,
                continued_samples=read_records(
                    folder / "observation-continuity.ndjson"
                ),
            )
        backend = backend or DockerBackend(root=root)
        if (
            plan.get("observation_method") != "wddm_auto_v3"
            and backend.image_id(plan["image_id"]) != plan["image_id"]
        ):
            raise ValueError("image_changed")
        rows = run_session(
            plan,
            folder,
            prerequisites,
            root=root,
            backend=backend,
            resume=bool(args.resume),
        )
        report = render_report(plan, rows)
        public = root / "eval/results/benchmark-5070.md"
        public.parent.mkdir(parents=True, exist_ok=True)
        # Informe versionado de evidencia exclusivo; la vista pública es la sesión recién medida.
        with (folder / "report.md").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(report)
        public.write_text(report, encoding="utf-8", newline="\n")
        complete = complete_matrix(plan, rows) and (folder / "restore.json").exists()
        if plan.get("observation_method") == "wddm_auto_v3":
            final_path = folder / "supervisor-final-audit.json"
            final = read_json(final_path) if final_path.exists() else {}
            complete = (
                complete
                and final.get("kind") == "audit_after_graceful_shutdown"
                and "failure" in final
                and final["failure"] is None
            )
        exclusive_json(
            folder / "summary.json",
            {
                "complete": complete,
                "rows": len(rows),
                "report_sha256": file_hash(public),
                "session_id": plan["session_id"],
            },
        )
        exclusive_json(folder / "seal.json", seal_files(folder))
        print(f"benchmark: rows={len(rows)} complete={str(complete).lower()}")
        return 0 if complete else 2
    except ObservationTimeout:
        if plan.get("observation_method") == "wddm_auto_v3":
            dispositions = sorted(folder.glob("recovery-*.json")) if folder else []
            disposition = (
                read_json(dispositions[-1]).get("disposition", "unknown_quarantined")
                if dispositions
                else "unknown_quarantined"
            )
            print(
                f"benchmark: observation_timeout; disposition={disposition}; evidencia conservada; acreditación v3 requiere plan nuevo"
            )
        else:
            print(
                f"benchmark: observation_timeout; resume={plan['session_id']}; consulta el mismo job, sin relanzarlo"
            )
        return 75
    except (ApiError, OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        # Errores privados pueden incluir inputs/rutas; sólo una etiqueta pública estable.
        print(
            "benchmark: incomplete_or_preflight_failed; consultar evidencia privada de sesión"
        )
        if folder is not None:
            code = getattr(error, "code", None)
            if (
                code is None
                and type(error) is ValueError
                and str(error).replace("_", "").isalnum()
            ):
                code = str(error)
            exclusive_json(
                folder / f"failure-{new_id()}.json",
                {
                    "status": "incomplete_or_preflight_failed",
                    "code": code or type(error).__name__,
                    "session_id": plan["session_id"],
                },
            )
            if (
                folder / "groups"
            ).exists() and code != "auto_legacy_policy_read_only_new_session_required":
                report = render_report(plan, session_rows(folder, plan))
                with (folder / f"partial-report-{new_id()}.md").open(
                    "x", encoding="utf-8"
                ) as stream:
                    stream.write(report)
                public = root / "eval/results/benchmark-5070.md"
                public.parent.mkdir(parents=True, exist_ok=True)
                public.write_text(report, encoding="utf-8", newline="\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
