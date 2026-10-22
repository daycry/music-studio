"""Regresiones CPU de transición review2; sin recursos GPU."""

import importlib.util
import inspect
import json
import threading
from pathlib import Path

import pytest
from benchmark_coordinator import ContinuousCoordinator

PRIVATE = Path.cwd() / ".cache/dev-cycle/t09/transition-review2-adjudicated-fix"


def test_t03_observation_deadline_preserves_advertised_existing_job(monkeypatch):
    import benchmark
    from benchmark_runner import ObservationTimeout

    spec = importlib.util.spec_from_file_location(
        "transition_native_session_fixture",
        PRIVATE / "fixtures2/test_benchmark_coordinator_v3.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native = module.fake_runtime.__wrapped__()
    original = benchmark.execute_run

    def short_observation(plan, *args, **kwargs):
        plan = {**plan, "timeouts": {**plan["timeouts"], "observation_s": 0.1}}
        return original(plan, *args, **kwargs)

    monkeypatch.setattr(benchmark, "execute_run", short_observation)
    with pytest.raises(ObservationTimeout):
        module.test_native_session_pilot_accreditation_four_original_rows_and_uncertain_cleanup(
            lambda name: __import__(name),
            module.episode_factory.__wrapped__(),
            native,
            monkeypatch,
            True,
        )
    folder = native[0]
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(row["action"] == "POST /v1/jobs" for row in trace) == 1
    assert list(folder.rglob("submission-intent.json"))
    recovery = json.loads(next(folder.glob("recovery-*.json")).read_text())
    assert recovery["cleanup"]["removed"] is True
    assert (folder / "resource.json").exists(), (
        "query_same_job anunciado pero recurso propio eliminado"
    )


def test_t06_finished_session_revalidates_canonical_full_raw():
    import benchmark
    from benchmark_evidence import exclusive_json, seal_files
    from benchmark_plan import digest

    spec = importlib.util.spec_from_file_location(
        "transition_private_calibration",
        PRIVATE / "fixtures/test_benchmark_calibration_v3.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generator = module.calibration.__wrapped__()
    calibration = next(generator)
    try:
        observation, plan, case = module.auto_case.__wrapped__(calibration)
        prerequisites = module.observation.build_auto_prerequisites(
            plan,
            observation["context"],
            {k: v["path"] for k, v in observation["evidence"].items()},
            observation["viewport"]["evidence"]["path"],
            root=Path.cwd(),
            exclusive_gpu_authorized=True,
            trusted_receipts=case["receipts"],
            trusted_attempts=case["attempts"],
        )
        folder = case["root"].parent / "finished-session"
        folder.mkdir()
        anchor = {
            "kind": "audit_after_graceful_shutdown",
            "failure": None,
            "publication_root": str(case["root"]),
            "context": observation["context"],
            "receipts": case["receipts"],
            "attempts": case["attempts"],
        }
        for name, value in {
            "plan": plan,
            "summary": {"rows": 160, "complete": True},
            "supervisor-final-audit": anchor,
        }.items():
            exclusive_json(folder / (name + ".json"), value)
        exclusive_json(folder / "seal.json", seal_files(folder))
        assert (
            benchmark.finished_session(
                folder,
                prerequisites=prerequisites,
                supervisor_anchor_sha256=digest(anchor),
            )
            == 0
        )
    finally:
        generator.close()


class ClosingAcquirer:
    observation_method = "wddm_auto_v3"

    def __init__(self):
        self.observation_context = {}
        self.receipts = []
        self.attempts = []
        self.previous_receipt = None
        self.closing = threading.Event()
        self.release = threading.Event()

    def acquire(self, phase, *, idle):
        return {"phase": phase}

    def close(self):
        self.closing.set()
        assert self.release.wait(2)
        raise ValueError("native_close_failure")


def test_t04_close_propagates_sampler_failure_after_last_audit():
    acquirer = ClosingAcquirer()
    coordinator = ContinuousCoordinator(acquirer)
    coordinator.__enter__()
    coordinator.stop.set()
    assert acquirer.closing.wait(2)
    acquirer.release.set()
    with pytest.raises(
        RuntimeError, match="v3_continuous_observation_failed"
    ) as caught:
        # Compatibilidad del reproducer con la API anterior: su close manual
        # ocultaba el fallo. El propietario pide ahora comprobación final.
        options = (
            {"raise_failure": True}
            if "raise_failure" in inspect.signature(coordinator.close).parameters
            else {}
        )
        coordinator.close(**options)
    assert isinstance(caught.value.__cause__, ValueError)
    assert not coordinator.sampler.is_alive()


def test_t05_success_publishes_custody_and_record_together():
    acquirer = ClosingAcquirer()
    coordinator = ContinuousCoordinator(acquirer)
    publications = []
    original = coordinator._custody

    def capture(phase, sample=None):
        original(phase, sample)
        with coordinator.condition:
            publications.append((len(coordinator.receipts), len(coordinator.records)))

    coordinator._custody = capture

    def acquire(phase, *, idle):
        acquirer.receipts = [{"ordinal": 1}]
        acquirer.previous_receipt = acquirer.receipts[0]
        coordinator.stop.set()
        return {"accepted": True}

    acquirer.acquire = acquire
    acquirer.release.set()
    coordinator._sample()
    assert publications == [(1, 1)]


def test_t04_shutdown_preserves_first_failure_cause():
    acquirer = ClosingAcquirer()
    coordinator = ContinuousCoordinator(acquirer)
    first = ValueError("acquisition_failed")
    coordinator._fail(first)
    coordinator._fail(OSError("cleanup_failed"))
    assert coordinator.failure is first
    assert coordinator.events[-1]["cleanup_error"] == "cleanup_failed"


def test_t05_rejected_attempt_remains_without_accepted_record():
    acquirer = ClosingAcquirer()
    coordinator = ContinuousCoordinator(acquirer)
    failure = ValueError("rejected_acquisition")

    def reject(phase, *, idle):
        acquirer.attempts = [{"status": "rejected", "reason": "synthetic"}]
        raise failure

    acquirer.acquire = reject
    acquirer.release.set()
    coordinator._sample()
    assert coordinator.records == []
    assert coordinator.attempts == acquirer.attempts
    assert coordinator.failure is failure


def test_t05_native_auditor_reads_coherent_publication_at_barrier():
    from benchmark_coordinator import RuntimeChannel
    from benchmark_process import OwnedProcess

    spec = importlib.util.spec_from_file_location(
        "transition_atomic_native_fixture",
        PRIVATE / "fixtures2/test_benchmark_coordinator_v3.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observer, _ = module.episode_factory.__wrapped__()()
    native = module.fake_runtime.__wrapped__()
    worker = OwnedProcess(native[2], native[3])
    coordinator = ContinuousCoordinator(observer)
    published = threading.Event()
    resume = threading.Event()
    original = coordinator._custody
    startup_errors = []

    def barrier(phase, sample=None):
        original(phase, sample)
        if not published.is_set():
            published.set()
            assert resume.wait(2)

    coordinator._custody = barrier

    def start():
        try:
            coordinator.__enter__()
        except BaseException as error:  # noqa: BLE001 - devolver también interrupciones del hilo de startup al test
            startup_errors.append(error)

    starter = threading.Thread(target=start)
    starter.start()
    try:
        assert published.wait(2)
        channel = RuntimeChannel(coordinator, worker)
        result = channel.audit_publications()
        assert result["audit_only"] is True
        assert result["validated"] == 1
    finally:
        resume.set()
        starter.join(3)
        coordinator.close()
        worker.close()
    assert not startup_errors
    assert not starter.is_alive()
    assert not coordinator.sampler.is_alive()
    assert worker.close_evidence["job_empty"] is True
    assert worker.close_evidence["reader_joined"] is True


def test_adjudicated_unknown_cleanup_retains_reservation():
    from benchmark_runtime import recover_owned_runtime

    calls = []

    class Worker:
        def __init__(self):
            self.close_evidence = {"job_empty": True, "reader_joined": True}

        def call(self, payload, **kwargs):
            action = payload["operation"]
            calls.append(action)
            if action == "terminate_owned":
                raise OSError("original_cleanup_ack_unknown")
            return {"value": {}}

        def close(self):
            pass

    result = recover_owned_runtime(
        {},
        {"folder": "synthetic"},
        None,
        release_lease=True,
        runtime_factory=lambda config: Worker(),
    )
    assert result["disposition"] == "unknown_quarantined"
    assert result["reservation_retained"] is True
    assert "lease_release" not in calls
    assert result["error"] == "original_cleanup_ack_unknown"


def test_adjudicated_quarantine_blocks_dead_owner_resume(tmp_path, monkeypatch):
    import benchmark_runtime as runtime

    owner = {"session_id": "CPU", "owner": "OWN", "plan_sha256": "PLAN"}
    lease = runtime.GpuLease(tmp_path / "lease.json", owner)
    lease.path.write_text(json.dumps({**owner, "pid": 123, "quarantined": True}))
    monkeypatch.setattr(runtime, "pid_alive", lambda pid: False)
    before = lease.path.read_bytes()
    with pytest.raises(ValueError, match="quarantined"):
        lease.acquire(resume=True)
    assert lease.path.read_bytes() == before


def test_adjudicated_quarantine_reservation_is_owned_and_durable(tmp_path):
    from benchmark_runtime import GpuLease

    owner = {"session_id": "CPU", "owner": "OWN", "plan_sha256": "PLAN"}
    lease = GpuLease(tmp_path / "lease.json", owner)
    lease.quarantine()
    assert json.loads(lease.path.read_text())["quarantined"] is True
    lease.quarantine()
    foreign = {**owner, "owner": "FOREIGN", "pid": 999}
    lease.path.write_text(json.dumps(foreign))
    before = lease.path.read_bytes()
    with pytest.raises(ValueError, match="owner_changed"):
        lease.quarantine()
    assert lease.path.read_bytes() == before


def test_adjudicated_quarantine_cannot_be_freed_without_reconciliation(tmp_path):
    from benchmark_runtime import GpuLease

    owner = {"session_id": "CPU", "owner": "OWN", "plan_sha256": "PLAN"}
    lease = GpuLease(tmp_path / "lease.json", owner)
    lease.quarantine()
    before = lease.path.read_bytes()
    with pytest.raises(ValueError, match="reconciliation"):
        lease.release()
    assert lease.path.read_bytes() == before


def test_adjudicated_runtime_ignores_caller_reconciliation_until_owned_removal(
    tmp_path,
):
    from benchmark_runtime import BenchmarkOperationProvider, GpuLease

    owner = {"session_id": "CPU", "owner": "OWN", "plan_sha256": "PLAN"}
    provider = BenchmarkOperationProvider.__new__(BenchmarkOperationProvider)
    provider.lease = GpuLease(tmp_path / "lease.json", owner)
    provider.lease.quarantine()
    provider.owned_removed = False
    provider.receipt = {"container_id": "CPU-OWN"}
    provider.backend = type(
        "OwnCPU", (), {"terminate_owned": lambda self, receipt: {"removed": True}}
    )()
    with pytest.raises(ValueError, match="reconciliation"):
        provider(
            {"operation": "lease_release", "arguments": {"reconciled": True}},
            lambda value: None,
        )
    assert provider.lease.path.exists()
    assert (
        provider({"operation": "terminate_owned", "arguments": {}}, lambda value: None)[
            "removed"
        ]
        is True
    )
    assert (
        provider({"operation": "lease_release", "arguments": {}}, lambda value: None)[
            "released"
        ]
        is True
    )
    assert not provider.lease.path.exists()


def test_t04_main_valid160_restore_and_shutdown_failure_is_incomplete(
    tmp_path, monkeypatch, capsys
):
    import benchmark as cli
    from benchmark_evidence import complete_matrix, exclusive_json

    session = "01M49HZQ7K5WFE9PA1N3WDN92K"
    plan = {
        "session_id": session,
        "observation_method": "wddm_auto_v3",
        "prerequisites_sha256": None,
        "runs": [{"run_id": str(i), "config_id": "CPU-SYNTHETIC"} for i in range(160)],
    }
    rows = [{**run, "valid": True, "synthetic_cpu": True} for run in plan["runs"]]
    assert complete_matrix(plan, rows)
    for name in ("inputs.json", "prerequisites.json"):
        exclusive_json(tmp_path / name, {})
    monkeypatch.setattr(cli, "build_plan", lambda *a, **k: plan)
    monkeypatch.setattr(
        cli, "render_report", lambda *a: "Synthetic CPU; no calibration"
    )

    def session_result(plan, folder, *a, **k):
        exclusive_json(
            folder / "restore.json", {"restored": True, "synthetic_cpu": True}
        )
        exclusive_json(
            folder / "supervisor-final-audit.json",
            {
                "kind": "audit_after_graceful_shutdown",
                "failure": "original_native_close_failure",
            },
        )
        return rows

    monkeypatch.setattr(cli, "run_session", session_result)
    result = cli.main(
        [
            "--inputs",
            str(tmp_path / "inputs.json"),
            "--image",
            "CPU",
            "--prerequisites",
            str(tmp_path / "prerequisites.json"),
            "--observation-method",
            "wddm_auto_v3",
        ],
        root=tmp_path,
    )
    folder = tmp_path / ".cache/dev-cycle/t09/runtime" / session
    assert result != 0
    assert json.loads((folder / "summary.json").read_text())["complete"] is False
    assert (
        json.loads((folder / "supervisor-final-audit.json").read_text())["failure"]
        == "original_native_close_failure"
    )
    assert "complete=false" in capsys.readouterr().out


def test_adjudicated_native_timeout_records_removed_disposition(monkeypatch):
    import benchmark
    from benchmark_runner import ObservationTimeout

    spec = importlib.util.spec_from_file_location(
        "adjudicated_native", PRIVATE / "fixtures2/test_benchmark_coordinator_v3.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native = module.fake_runtime.__wrapped__()
    original = benchmark.execute_run

    def short(plan, *args, **kwargs):
        return original(
            {**plan, "timeouts": {**plan["timeouts"], "observation_s": 0.1}},
            *args,
            **kwargs,
        )

    monkeypatch.setattr(benchmark, "execute_run", short)
    with pytest.raises(ObservationTimeout):
        module.test_native_session_pilot_accreditation_four_original_rows_and_uncertain_cleanup(
            lambda name: __import__(name),
            module.episode_factory.__wrapped__(),
            native,
            monkeypatch,
            True,
        )
    folder = native[0]
    recovery = json.loads(next(folder.glob("recovery-*.json")).read_text())
    assert recovery["disposition"] == "removed"
    assert recovery["uncertain"] is False
    assert recovery["reservation_retained"] is False
    assert (
        recovery["worker_cleanup"]["job_empty"]
        and recovery["worker_cleanup"]["reader_joined"]
    )
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(row["action"] == "POST /v1/jobs" for row in trace) == 1
    assert not (folder / "resource.json").exists()
    assert list(folder.rglob("submission-intent.json"))
    assert recovery["jobs"][0]["cursor"] == 0
    assert recovery["jobs"][0]["terminal_sha256"] is None
    assert recovery["original_error"] == "existing_job_preserved_resume_required"
    assert recovery["supersedes_provisional_query_same_job"] is True


def test_adjudicated_native_partial_event_preserves_original_timeout_and_bytes(
    monkeypatch,
):
    import benchmark
    from benchmark_runner import ObservationTimeout

    spec = importlib.util.spec_from_file_location(
        "partial_event_native", PRIVATE / "fixtures2/test_benchmark_coordinator_v3.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native = module.fake_runtime.__wrapped__()
    original = benchmark.execute_run
    raw = b'{"seq":'
    partial_paths = []

    def partial(plan, *args, **kwargs):
        try:
            return original(
                {**plan, "timeouts": {**plan["timeouts"], "observation_s": 0.1}},
                *args,
                **kwargs,
            )
        except ObservationTimeout:
            path = Path(args[3]) / "events.ndjson"
            path.write_bytes(raw)
            partial_paths.append(path)
            raise

    monkeypatch.setattr(benchmark, "execute_run", partial)
    with pytest.raises(
        ObservationTimeout, match="existing_job_preserved_resume_required"
    ):
        module.test_native_session_pilot_accreditation_four_original_rows_and_uncertain_cleanup(
            lambda name: __import__(name),
            module.episode_factory.__wrapped__(),
            native,
            monkeypatch,
            True,
        )
    recovery = json.loads(next(native[0].glob("recovery-*.json")).read_text())
    assert recovery["original_error"] == "existing_job_preserved_resume_required"
    assert recovery["jobs"][0]["cursor"] is None
    assert recovery["jobs"][0]["inventory_error"]
    assert partial_paths[0].read_bytes() == raw


@pytest.mark.parametrize("method", ["wddm_auto_v1", "wddm_auto_v2", "wddm_auto_v3"])
def test_adjudicated_main_timeout_message_preserves_legacy_promises(
    tmp_path, monkeypatch, capsys, method
):
    import benchmark as cli
    from benchmark_evidence import exclusive_json
    from benchmark_runner import ObservationTimeout

    plan = {
        "session_id": "01M49HZQ7K5WFE9PA1N3WDN92K",
        "observation_method": method,
        "prerequisites_sha256": None,
        "runs": [],
        "image_id": "CPU",
    }
    for name in ("inputs.json", "prerequisites.json"):
        exclusive_json(tmp_path / name, {})
    monkeypatch.setattr(cli, "build_plan", lambda *a, **k: plan)
    monkeypatch.setattr(cli, "validate_prerequisites", lambda *a, **k: {})
    # Los planes antiguos conservan su control de hash independiente.
    plan["prerequisites_sha256"] = cli.file_hash(tmp_path / "prerequisites.json")

    def timeout(plan, folder, *a, **k):
        exclusive_json(folder / "recovery-test.json", {"disposition": "removed"})
        raise ObservationTimeout("original_observation_timeout")

    monkeypatch.setattr(cli, "run_session", timeout)
    backend = type("CPU", (), {"image_id": lambda self, image: image})()
    assert (
        cli.main(
            [
                "--inputs",
                str(tmp_path / "inputs.json"),
                "--image",
                "CPU",
                "--prerequisites",
                str(tmp_path / "prerequisites.json"),
                "--observation-method",
                method,
            ],
            root=tmp_path,
            backend=backend,
        )
        == 75
    )
    message = capsys.readouterr().out
    if method == "wddm_auto_v3":
        assert "disposition=removed" in message and "plan nuevo" in message
        assert "consulta el mismo job" not in message and "resume=" not in message
    else:
        assert "consulta el mismo job, sin relanzarlo" in message
