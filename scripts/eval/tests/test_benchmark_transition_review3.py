"""Fronteras review3; CPU sintética, sin adquisición GPU."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("method", ["wddm_auto_v1", "wddm_auto_v2", "unknown_policy"])
@pytest.mark.parametrize("entry", ["session", "run", "sample"])
@pytest.mark.parametrize("resume", [False, True])
def test_live_entry_rejects_before_any_effect(
    monkeypatch, tmp_path, method, entry, resume
):
    import benchmark
    import benchmark_observation
    import benchmark_runner

    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("live_resource_touched")

    folder = tmp_path / "untouched"
    folder.mkdir()
    anchor = folder / "predecessor.json"
    anchor.write_bytes(b'{"ordinal":7}')
    observers = SimpleNamespace(
        observation_method=method,
        observation_context={},
        sample=forbidden,
        previous_sample={"ordinal": 7},
        previous_episode={"ordinal": 7},
    )
    monkeypatch.setattr(benchmark, "validate_prerequisites", forbidden)
    monkeypatch.setattr(benchmark, "DockerBackend", forbidden)
    monkeypatch.setattr(benchmark, "OllamaState", forbidden)
    monkeypatch.setattr(benchmark, "GpuLease", forbidden)
    api = SimpleNamespace(request=forbidden, events=forbidden)
    error = (
        "unknown_observation_method"
        if method == "unknown_policy"
        else "auto_legacy_policy_read_only_new_session_required"
    )
    with pytest.raises(ValueError, match=error):
        if entry == "session":
            benchmark.run_session(
                {"observation_method": method},
                folder,
                {},
                root=tmp_path,
                observer_factory=forbidden,
                api_factory=forbidden,
                resume=resume,
            )
        elif entry == "run":
            benchmark_runner.execute_run(
                {"observation_method": method},
                {"job_id": "CPU"},
                api,
                observers,
                folder,
                {"job_id": "CPU"},
            )
        else:
            benchmark_observation.acquire_sample(observers, folder / "accepted.ndjson")
    assert calls == []
    assert list(folder.iterdir()) == [anchor]
    assert anchor.read_bytes() == b'{"ordinal":7}'
    assert observers.previous_sample == {"ordinal": 7}
    assert observers.previous_episode == {"ordinal": 7}


@pytest.mark.parametrize("primary_type", [ValueError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("where", ["call", "check"])
def test_operation_primary_survives_secondary_close(primary_type, where):
    from benchmark_coordinator import ContinuousCoordinator

    acquirer = SimpleNamespace(
        observation_method="wddm_auto_v3", observation_context={}
    )
    coordinator = ContinuousCoordinator(acquirer)
    coordinator.started = True
    primary = primary_type("primary_operation")
    cause = OSError("original_cause")
    primary.__cause__ = cause
    secondary = RuntimeError("cleanup_token=SECRET")
    calls = []

    class Worker:
        job = None

        def __init__(self):
            self.ownership = {"pid": 123, "creation_time": 456}

        def call(self, payload, **kwargs):
            calls.append("call")
            if where == "call":
                raise primary
            coordinator.failure = primary
            return {"value": "result"}

        def close(self, **kwargs):
            calls.append("close")
            raise secondary

    with pytest.raises(BaseException) as caught:
        coordinator.run_owned(
            "CPU", Worker(), {"operation": "CPU", "arguments": {}}, timeout_s=1
        )
    if where == "call":
        assert caught.value is primary
        assert caught.value.__cause__ is cause
    else:
        assert isinstance(caught.value, RuntimeError)
        assert caught.value.__cause__ is primary
    assert calls == ["call", "close"]
    assert coordinator.active is None
    event = coordinator.events[-1]
    assert event["cleanup_error"]["type"] == "RuntimeError"
    assert "SECRET" not in json.dumps(event["cleanup_error"])
    assert event["cleanup_error"]["message_sha256"]


@pytest.fixture
def native_episode():
    import test_benchmark_episode_v3 as fixture

    return fixture.episode_factory.__wrapped__()


@pytest.mark.parametrize("close_fails", [False, True])
@pytest.mark.parametrize("journal_fails", [False, True])
def test_binding_failure_closes_started_native_sampler(
    monkeypatch, tmp_path, native_episode, close_fails, foreign_control, journal_fails
):
    import benchmark
    import benchmark_coordinator
    import benchmark_episode
    from benchmark_process import process_alive

    acquirer, context = native_episode()
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
    plan["runs"] = [{}] * 160
    folder = tmp_path / "session"
    folder.mkdir()
    prerequisites = {
        "observation": {"method": "wddm_auto_v3", "context": context},
        "exclusive_gpu_authorized": True,
        "browser": {},
    }
    monkeypatch.setattr(benchmark_episode, "EpisodeAcquirer", lambda **kwargs: acquirer)
    instances = []
    original_class = benchmark_coordinator.ContinuousCoordinator

    class TrackingCoordinator(original_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.close_count = 0
            instances.append(self)

        def close(self, **kwargs):
            self.close_count += 1
            super().close(**kwargs)
            if close_fails:
                raise RuntimeError("secondary_native_close")

    monkeypatch.setattr(
        benchmark_coordinator, "ContinuousCoordinator", TrackingCoordinator
    )
    primary = OSError("binding_disk_failure")
    write = benchmark.exclusive_json
    lease_calls = []

    def fail_binding(path, value):
        if Path(path).name == "audit-transport-binding.json":
            assert instances[0].sampler.is_alive()
            raise primary
        if journal_fails and (
            Path(path).name.startswith("recovery-")
            or Path(path).name == "supervisor-final-audit.json"
        ):
            raise OSError("secondary_journal_disk_failure")
        return write(path, value)

    monkeypatch.setattr(benchmark, "exclusive_json", fail_binding)

    def forbidden_factory(*args, **kwargs):
        lease_calls.append("factory")
        raise AssertionError("runtime_started_before_binding")

    observed_closed = False
    try:
        with pytest.raises(OSError) as caught:
            benchmark.run_session_v3(
                plan,
                folder,
                prerequisites,
                root=tmp_path,
                runtime_factory=forbidden_factory,
            )
        assert caught.value is primary
        observed_closed = not instances[0].sampler.is_alive()
        assert observed_closed, "started_sampler_leaked_after_binding_failure"
        assert instances[0].close_count == 1
        assert lease_calls == []
        assert process_alive(foreign_control.ownership["pid"])
        evidence = acquirer.worker.close_evidence
        assert evidence["job_empty"] and evidence["reader_joined"]
        assert evidence["ownership"]["creation_time"] > 0
        assert not process_alive(evidence["ownership"]["pid"])
        (tmp_path / "binding-own-cleanup.json").write_text(json.dumps(evidence))
    finally:
        if instances and not observed_closed:
            try:
                instances[0].close()
            except RuntimeError:
                pass
        acquirer.close()


def test_lost_native_lease_ack_is_durably_quarantined(
    monkeypatch, tmp_path, native_episode, foreign_control
):
    import benchmark
    from benchmark_coordinator import ContinuousCoordinator
    from benchmark_process import OwnedProcess, WorkerFailure, process_alive
    from benchmark_runtime import GpuLease

    observer, context = native_episode()
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
    plan["runs"] = [{}] * 160
    folder = tmp_path / "session"
    folder.mkdir()
    prerequisites = {
        "observation": {"method": "wddm_auto_v3", "context": context},
        "exclusive_gpu_authorized": True,
        "browser": {},
    }
    lease_path = tmp_path / ".cache/dev-cycle/t09/gpu.lock"
    handler = tmp_path / "lease_provider.py"
    handler.write_text(
        """import json
from pathlib import Path
from benchmark_runtime import GpuLease
class Fixture:
 def __init__(self,config):self.config=config
 def __call__(self,payload,emit):
  if payload["operation"]=="verify_plan":return {"verified":True}
  if payload["operation"]=="lease_acquire":
   owner=json.loads(Path(self.config["owner_path"]).read_text())
   path=Path(self.config["root"])/".cache/dev-cycle/t09/gpu.lock"
   ticket=Path(self.config["plan_path"]).parent/"lease-intent.json"
   saved=json.loads(ticket.read_text()) if ticket.exists() else None
   Path(self.config["plan_path"]).parent.joinpath("ticket-at-call.json").write_text(json.dumps(saved))
   from benchmark_runtime import BenchmarkOperationProvider
   provider=BenchmarkOperationProvider.__new__(BenchmarkOperationProvider)
   provider.root=Path(self.config["root"])
   provider.owner=owner
   provider.lease=GpuLease(path,owner,holder_pid=self.config["supervisor_pid"])
   BenchmarkOperationProvider.__call__(provider,payload,emit)
   emit({"lease_created":True})
   raise RuntimeError("ORIGINAL_LEASE_ACK_LOST")
  raise AssertionError("unexpected_operation")
 def close(self):pass
""",
        encoding="utf-8",
    )
    workers = []
    recovery_calls = []

    def factory(config, **kwargs):
        if not kwargs:
            recovery_calls.append("failure_before_reconcile")
            raise OSError("recovery_unavailable")
        worker = OwnedProcess(config, f"{handler}:Fixture")
        workers.append(worker)
        return worker

    coordinator = ContinuousCoordinator(observer)
    try:
        coordinator.__enter__()
        with pytest.raises(WorkerFailure, match="worker_pipe_eof"):
            benchmark.run_session_v3(
                plan,
                folder,
                prerequisites,
                root=tmp_path,
                coordinator=coordinator,
                runtime_factory=factory,
            )
        assert lease_path.exists()
        lock = json.loads(lease_path.read_text())
        assert lock.get("quarantined") is True, "lost_ACK_reservation_left_reclaimable"
        ticket = json.loads((folder / "ticket-at-call.json").read_text())
        assert ticket["ack_state"] == "unknown"
        assert ticket["owner"] == lock["owner"]
        assert ticket["pid"] == lock["pid"]
        assert ticket["creation_time"] > 0 and ticket["nonce"]
        recovery = json.loads(next(folder.glob("recovery-*.json")).read_text())
        assert recovery["disposition"] == "unknown_quarantined"
        assert recovery["reservation_retained"] is True
        assert recovery_calls == []  # No resource exists to reconcile before lease ACK.
        for resume in (False, True):
            with pytest.raises(ValueError, match="quarantined"):
                GpuLease(lease_path, lock).acquire(resume=resume)
        with pytest.raises(ValueError, match="reconciliation"):
            GpuLease(lease_path, lock).release()
        assert not list(folder.rglob("submission-intent.json"))
        assert process_alive(foreign_control.ownership["pid"])
        assert (
            lock["nonce"] == ticket["nonce"]
            and lock["creation_time"] == ticket["creation_time"]
        )
        for worker in workers:
            assert (
                worker.close_evidence["job_empty"]
                and worker.close_evidence["reader_joined"]
            )
            assert worker.close_evidence["ownership"]["creation_time"] > 0
            assert not process_alive(worker.close_evidence["ownership"]["pid"])
            (tmp_path / "lease-own-cleanup.json").write_text(
                json.dumps(worker.close_evidence)
            )
    finally:
        coordinator.close()
        for worker in workers:
            worker.close(graceful=False)


@pytest.mark.parametrize("resume", [False, True])
def test_cli_legacy_rejects_before_backend(monkeypatch, tmp_path, resume):
    import benchmark

    calls = []

    def forbidden(*args, **kwargs):
        calls.append("effect")
        raise AssertionError("CLI_backend_before_legacy_guard")

    monkeypatch.setattr(benchmark, "DockerBackend", forbidden)
    monkeypatch.setattr(benchmark, "validate_prerequisites", forbidden)
    monkeypatch.setattr(benchmark, "render_report", forbidden)
    monkeypatch.setattr(benchmark, "verify_plan", lambda *args: None)
    monkeypatch.setattr(benchmark, "finished_session", lambda *args, **kwargs: None)
    plan = {
        "observation_method": "wddm_auto_v2",
        "prerequisites_sha256": None,
        "session_id": "0" * 26,
        "runs": [],
    }
    monkeypatch.setattr(benchmark, "read_json", lambda *args: plan)
    (tmp_path / "input.json").write_text("{}")
    (tmp_path / "prerequisites.json").write_text("{}")
    argv = ["--prerequisites", str(tmp_path / "prerequisites.json")]
    if resume:
        folder = tmp_path / ".cache/dev-cycle/t09/runtime" / plan["session_id"]
        folder.mkdir(parents=True)
        (folder / "groups").mkdir()
        argv += ["--resume", plan["session_id"]]
    else:
        argv += [
            "--inputs",
            str(tmp_path / "input.json"),
            "--image",
            "CPU",
            "--observation-method",
            "wddm_auto_v2",
        ]
    assert benchmark.main(argv, root=tmp_path) == 2
    assert calls == []
    assert not (tmp_path / "eval/results/benchmark-5070.md").exists()


def test_startup_primary_survives_close_failure(monkeypatch):
    from benchmark_coordinator import ContinuousCoordinator

    acquirer = SimpleNamespace(
        observation_method="wddm_auto_v3", observation_context={}
    )
    coordinator = ContinuousCoordinator(acquirer)
    primary = KeyboardInterrupt("startup_primary")
    closed = []
    monkeypatch.setattr(coordinator.sampler, "start", lambda: None)

    def fail():
        raise primary

    def close():
        closed.append(True)
        raise RuntimeError("startup_cleanup_secret")

    monkeypatch.setattr(coordinator, "check", fail)
    monkeypatch.setattr(coordinator, "close", close)
    with pytest.raises(BaseException) as caught:
        coordinator.__enter__()
    assert caught.value is primary
    assert closed == [True]
    assert coordinator.events[-1]["cleanup_error"]["type"] == "RuntimeError"


def test_owned_constructor_primary_survives_secondary_close(monkeypatch):
    from benchmark_coordinator import ContinuousCoordinator, CoordinatedOwnedProcess
    from benchmark_process import OwnedProcess

    coordinator = ContinuousCoordinator(
        SimpleNamespace(observation_method="wddm_auto_v3", observation_context={})
    )
    coordinator.started = True
    primary = SystemExit("constructor_primary")
    calls = []

    def fail(self, *args, **kwargs):
        self.closed = False
        raise primary

    def close(self, **kwargs):
        calls.append("close")
        raise RuntimeError("constructor_secondary")

    monkeypatch.setattr(OwnedProcess, "__init__", fail)
    monkeypatch.setattr(CoordinatedOwnedProcess, "close", close)
    with pytest.raises(BaseException) as caught:
        CoordinatedOwnedProcess({}, "CPU:Fixture", coordinator=coordinator)
    assert caught.value is primary
    assert calls == ["close"] and coordinator.active is None
    assert coordinator.events[-1]["cleanup_error"]["type"] == "RuntimeError"


@pytest.fixture
def foreign_control(tmp_path):
    from benchmark_process import OwnedProcess, process_alive

    handler = tmp_path / "foreign_control.py"
    handler.write_text(
        "class Fixture:\n def __init__(self,config):pass\n def __call__(self,payload,emit):return {}\n def close(self):pass\n"
    )
    worker = OwnedProcess({}, f"{handler}:Fixture")
    try:
        assert worker.ownership["creation_time"] > 0
        yield worker
        assert process_alive(worker.ownership["pid"])
    finally:
        worker.close()
        (tmp_path / "foreign-control-own-cleanup.json").write_text(
            json.dumps(worker.close_evidence)
        )


def test_native_start_failure_closes_owned_acquirer(
    monkeypatch, tmp_path, native_episode, foreign_control
):
    from benchmark_coordinator import ContinuousCoordinator
    from benchmark_process import process_alive

    acquirer, _context = native_episode()
    coordinator = ContinuousCoordinator(acquirer)
    primary = OSError("thread_start_failed")

    def fail():
        raise primary

    monkeypatch.setattr(coordinator.sampler, "start", fail)
    try:
        with pytest.raises(OSError) as caught:
            coordinator.__enter__()
        assert caught.value is primary
        assert acquirer.worker.close_evidence is not None, (
            "acquirer_leaked_before_thread_start"
        )
        assert acquirer.worker.close_evidence["reader_joined"]
        assert acquirer.worker.close_evidence["job_empty"]
        assert process_alive(foreign_control.ownership["pid"])
        (tmp_path / "start-own-cleanup.json").write_text(
            json.dumps(acquirer.worker.close_evidence)
        )
    finally:
        acquirer.close()


def test_coordinator_constructor_failure_closes_native_acquirer(
    monkeypatch, tmp_path, native_episode, foreign_control
):
    import benchmark
    import benchmark_coordinator
    import benchmark_episode
    from benchmark_process import process_alive

    acquirer, context = native_episode()
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
    plan["runs"] = [{}] * 160
    folder = tmp_path / "session"
    folder.mkdir()
    prerequisites = {
        "observation": {"method": "wddm_auto_v3", "context": context},
        "exclusive_gpu_authorized": True,
        "browser": {},
    }
    primary = OSError("constructor_thread_failure")
    monkeypatch.setattr(benchmark_episode, "EpisodeAcquirer", lambda **kwargs: acquirer)

    def fail(*args, **kwargs):
        raise primary

    monkeypatch.setattr(benchmark_coordinator, "ContinuousCoordinator", fail)
    try:
        with pytest.raises(OSError) as caught:
            benchmark.run_session_v3(plan, folder, prerequisites, root=tmp_path)
        assert caught.value is primary
        assert acquirer.worker.close_evidence is not None, (
            "native_acquirer_leaked_on_constructor"
        )
        assert (
            acquirer.worker.close_evidence["job_empty"]
            and acquirer.worker.close_evidence["reader_joined"]
        )
        assert process_alive(foreign_control.ownership["pid"])
        (tmp_path / "constructor-own-cleanup.json").write_text(
            json.dumps(acquirer.worker.close_evidence)
        )
    finally:
        acquirer.close()


@pytest.mark.parametrize("foreign", [False, True])
def test_ack_unknown_dead_owner_and_foreign_reservation(
    tmp_path, foreign_control, foreign
):
    from benchmark_evidence import exclusive_json
    from benchmark_process import OwnedProcess, process_alive
    from benchmark_runtime import GpuLease, recover_owned_runtime

    owner = {"session_id": "CPU", "owner": "OWN", "plan_sha256": "PLAN"}
    owner_path = tmp_path / "owner.json"
    exclusive_json(owner_path, owner)
    handler = tmp_path / "dead_owner.py"
    handler.write_text(
        "class Fixture:\n def __init__(self,config):pass\n def __call__(self,payload,emit):return {}\n def close(self):pass\n"
    )
    dead = OwnedProcess({}, f"{handler}:Fixture")
    identity = dict(dead.ownership)
    dead.close()
    assert not process_alive(identity["pid"])
    ticket = {
        **owner,
        "pid": identity["pid"],
        "creation_time": identity["creation_time"],
        "nonce": "CPU-NONCE",
        "ack_state": "unknown",
    }
    intent_path = tmp_path / "lease-intent.json"
    exclusive_json(intent_path, ticket)
    path = tmp_path / "private-gpu.lock"
    saved = {**ticket, "owner": "FOREIGN" if foreign else "OWN"}
    if foreign:
        saved["pid"] = foreign_control.ownership["pid"]
        saved["creation_time"] = foreign_control.ownership["creation_time"]
    exclusive_json(path, saved)
    preimage = path.read_bytes()
    calls = []

    def forbidden(config):
        calls.append("capacity_recovery")
        raise AssertionError("no_capacity_retry")

    result = recover_owned_runtime(
        {
            "root": str(tmp_path),
            "owner_path": str(owner_path),
            "lease_path": str(path),
            "lease_intent_path": str(intent_path),
        },
        None,
        None,
        runtime_factory=forbidden,
    )
    assert calls == []
    assert process_alive(foreign_control.ownership["pid"])
    if foreign:
        assert path.read_bytes() == preimage
        assert result["reservation_state"] == "foreign_untouched"
        assert result["reservation_retained"] is False
    else:
        assert json.loads(path.read_text())["quarantined"] is True
        assert result["reservation_retained"] is True
        for resume in (False, True):
            with pytest.raises(ValueError, match="quarantined"):
                GpuLease(path, owner).acquire(resume=resume)
        with pytest.raises(ValueError, match="reconciliation"):
            GpuLease(path, owner).release()
        # This fake owner has an actual empty Job and no model/resource/API.
        assert dead.close_evidence["job_empty"] and dead.close_evidence["reader_joined"]
        GpuLease(path, owner).release(reconciled=True)
        assert not path.exists()
    (tmp_path / "dead-owner-cleanup.json").write_text(json.dumps(dead.close_evidence))
    (tmp_path / "reservation-recovery.json").write_text(json.dumps(result))
