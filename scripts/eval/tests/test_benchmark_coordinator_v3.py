"""Integración CPU sintética explícita; procesos y relojes reales."""

import copy
import importlib.util
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from benchmark_episode import read_publications
from benchmark_process import OwnedProcess, process_alive

PHASE = Path.cwd() / ".cache/dev-cycle/t09/continuous-coordinator-implementation"


@pytest.mark.parametrize("recording_fault", [False, True])
def test_firstcause_context_body_keeps_original_after_native_cleanup_fault(
    episode_factory, monkeypatch, recording_fault
):
    """Actual coordinator-owned native resources, controlled body/Job faults."""
    import benchmark_coordinator as module

    observer, _ = episode_factory()
    service = module.ContinuousCoordinator(observer)
    primary = LookupError("controlled_context_body_firstcause")

    def terminate_fault():
        raise OSError("controlled_owned_coordinator_job_termination_fault")

    def recording_error(error):
        raise RuntimeError("controlled_secondary_recording_fault")

    # An unstarted coordinator owns the actual acquirer and closes it on exit.
    # Exercise __exit__ with Python's real context-manager exception protocol.
    class Context:
        def __enter__(self):
            return service

        def __exit__(self, kind, value, traceback):
            return service.__exit__(kind, value, traceback)

    assert observer.worker.ownership["job_member"] is True
    assert observer.worker.reader.is_alive()
    monkeypatch.setattr(observer.worker.job, "terminate", terminate_fault)
    if recording_fault:
        monkeypatch.setattr(module, "cleanup_error_record", recording_error)
    try:
        with pytest.raises(BaseException) as caught, Context():
            raise primary
        assert caught.value is primary
        assert type(caught.value) is LookupError
        assert service.events[-1]["cleanup_error"]["type"] == "WorkerFailure"
        assert observer.worker.close_evidence["resources_returned"] is False
        assert observer.worker.close_evidence["disposition"] == "UNKNOWN_QUARANTINED"
    finally:
        observer.close()
        assert observer.worker.process.poll() is not None
        assert not observer.worker.reader.is_alive()


def test_firstcause_successful_body_does_not_swallow_native_cleanup_fault(
    episode_factory, monkeypatch
):
    """No body error: actual coordinator resource cleanup fault must propagate."""
    import benchmark_coordinator as module
    from benchmark_process import WorkerFailure

    observer, _ = episode_factory()
    service = module.ContinuousCoordinator(observer)

    def terminate_fault():
        raise OSError("controlled_cleanup_without_primary")

    monkeypatch.setattr(observer.worker.job, "terminate", terminate_fault)
    try:
        with pytest.raises(WorkerFailure, match="controlled_cleanup_without_primary"):
            service.__exit__(None, None, None)
        assert observer.worker.close_evidence["resources_returned"] is False
    finally:
        observer.close()
        assert observer.worker.process.poll() is not None
        assert not observer.worker.reader.is_alive()


@pytest.mark.parametrize("serve", [False, True])
def test_storage_cli_copies_real_cpu_bytes_and_refuses_host_service(
    harness_module, monkeypatch, serve
):
    import hashlib

    storage = harness_module("benchmark_storage")
    folder = PHASE / "storage-cli-cpu" / uuid.uuid4().hex
    source, target = folder / "source", folder / "copy"
    components = []
    for name in ("CPU-CHECKPOINT", "CPU-LM", "vae", "Qwen3-Embedding-0.6B"):
        blob = ("explicit-synthetic-CPU:" + name).encode()
        directory = source / "ace-step-1.5/checkpoints" / name
        directory.mkdir(parents=True)
        (directory / "fixture.safetensors").write_bytes(blob)
        components.append(
            {
                "id": name,
                "dest_subdir": name,
                "files": [
                    {
                        "path": "fixture.safetensors",
                        "format": "safetensors",
                        "bytes": len(blob),
                        "sha256": hashlib.sha256(blob).hexdigest(),
                    }
                ],
            }
        )
    (source / "models.lock.json").write_text(
        json.dumps({"models": {"ace-step-1.5": {"components": components}}})
    )
    receipt = folder / "receipt.json"
    argv = [
        "benchmark_storage",
        "--source",
        str(source),
        "--destination",
        str(target),
        "--checkpoint",
        "CPU-CHECKPOINT",
        "--lm",
        "CPU-LM",
        "--receipt",
        str(receipt),
    ]
    if serve:
        argv.append("--serve")
    monkeypatch.setattr(sys, "argv", argv)
    if serve:
        with pytest.raises(ValueError, match="guest_container_required"):
            storage.main()
    else:
        assert storage.main() == 0
    result = json.loads(receipt.read_text())
    assert result["source_lock_sha256"] == result["destination_lock_sha256"]
    assert result["copy_bytes"] > 0 and len(result["files"]) == 4
    for component in components:
        relative = (
            Path("ace-step-1.5/checkpoints") / component["id"] / "fixture.safetensors"
        )
        assert (source / relative).read_bytes() == (target / relative).read_bytes()


def test_native_lease_uses_supervisor_pid_and_preserves_live_foreign_owner(
    harness_module,
):
    """Archivo de lease aislado CPU; ningún recurso GPU se solicita."""
    import os

    runtime = harness_module("benchmark_runtime")
    folder = PHASE / "lease-cpu" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    owner = {"session_id": "CPU", "owner": "CPU-OWNER", "plan_sha256": "CPU-PLAN"}
    lease = runtime.GpuLease(
        folder / "isolated-fake-lease.json", owner, holder_pid=os.getpid()
    )
    child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"])
    try:
        assert runtime.pid_alive(child.pid)
        lease.path.write_text(
            json.dumps({**owner, "owner": "FOREIGN", "pid": child.pid})
        )
        before = lease.path.read_bytes()
        with pytest.raises(ValueError, match="gpu_lock_owned_or_live"):
            lease.acquire(resume=True)
        assert lease.path.read_bytes() == before
        assert runtime.pid_alive(child.pid)
        child.terminate()
        child.wait(timeout=5)
        assert not runtime.pid_alive(child.pid)
        lease.path.write_text(json.dumps({**owner, "pid": child.pid}))
        lease.acquire(resume=True)
        assert json.loads(lease.claim.read_text())["pid"] == os.getpid()
        lease.release()
        assert not lease.path.exists() and not lease.claim.exists()
        lease.acquire()
        assert json.loads(lease.path.read_text())["pid"] == os.getpid()
        with pytest.raises(ValueError, match="gpu_lock_owned_or_live"):
            lease.acquire(resume=True)
        lease.release()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)


@pytest.mark.parametrize("running", [False, True])
def test_fake_daemon_cleanup_verifies_ownership_and_unload_before_removal(
    harness_module, running
):
    """Ejecutor en memoria; usa el backend productivo, nunca Docker real."""
    from types import SimpleNamespace

    runtime = harness_module("benchmark_runtime")
    receipt = {
        "container_id": "CPU-OWN",
        "owner": "CPU",
        "session_id": "CPU",
        "plan_sha256": "CPU",
    }
    calls, loaded = [], [True]
    inspection = {
        "Id": "CPU-OWN",
        "Config": {
            "Labels": {
                "studio.t09.owner": "CPU",
                "studio.t09.session": "CPU",
                "studio.t09.plan": "CPU",
            }
        },
        "State": {"Running": running, "Pid": 10 if running else 0},
    }

    def execute(argv, **kwargs):
        calls.append((argv, kwargs))
        assert kwargs["timeout"] <= 120
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps([inspection]) if argv[1] == "inspect" else "CPU-ACK",
        )

    class Api:
        def request(self, method, path):
            calls.append((["api", method, path], {}))
            if path == "/v1/unload":
                loaded[0] = False
                return {"unloaded": True}
            return {
                "state": "idle",
                "job_id": None,
                "loaded": {"model_id": "CPU"} if loaded[0] else None,
            }

    backend = runtime.DockerBackend(execute=execute)
    result = backend.cleanup(receipt, Api())
    assert result["removed"] and result["unloaded"]
    assert calls[-1][0] == ["docker", "rm", "CPU-OWN"]
    if running:
        unload = next(
            i
            for i, (argv, _) in enumerate(calls)
            if argv == ["api", "POST", "/v1/unload"]
        )
        stop = next(
            i for i, (argv, _) in enumerate(calls) if argv[:2] == ["docker", "stop"]
        )
        assert unload < stop < len(calls) - 1
    inspection["Config"]["Labels"]["studio.t09.owner"] = "FOREIGN"
    before = len(calls)
    with pytest.raises(ValueError, match="ownership"):
        backend.terminate_owned(receipt)
    assert len(calls) == before + 1


def test_historical_v3_prerequisites_require_external_custody(
    harness_module, monkeypatch
):
    runner = harness_module("benchmark_runner")
    receipts, attempts = [{"external": "receipt"}], [{"external": "attempt"}]
    seen = []

    def canonical(observation, root, **kwargs):
        seen.append(kwargs)
        assert kwargs.get("trusted_receipts") is receipts
        assert kwargs.get("trusted_attempts") is attempts
        return {"context": {"browser_identity": "fixture"}}

    monkeypatch.setattr(runner, "validate_auto", canonical)
    prerequisites = {
        "observation": {"method": "wddm_auto_v3"},
        "exclusive_gpu_authorized": True,
        "browser": "fixture",
    }
    try:
        result = runner.validate_prerequisites(
            prerequisites, trusted_receipts=receipts, trusted_attempts=attempts
        )
    except TypeError:
        result = None
    assert result is not None, (
        "lectura v3 no entrega custodia externa al validador canónico"
    )
    assert seen


def test_fragment_transfer_rejects_parallel_channel_before_mutating_worker(
    harness_module, episode_factory, fake_runtime, monkeypatch
):
    import threading
    from contextlib import closing

    module = harness_module("benchmark_coordinator")
    folder, _plan, config, handler = fake_runtime
    worker = OwnedProcess(config, handler)
    observer, _ = episode_factory()
    service = module.ContinuousCoordinator(observer)
    ready, release = threading.Event(), threading.Event()
    errors = []
    with closing(worker), service:
        channel = module.RuntimeChannel(service, worker)
        original = service.run_owned

        def held(phase, owned, payload, **kwargs):
            result = original(phase, owned, payload, **kwargs)
            if payload["operation"] == "args_begin":
                ready.set()
                assert release.wait(5)
            return result

        monkeypatch.setattr(service, "run_owned", held)

        def transfer():
            try:
                channel.write_json(folder / "large-own.json", {"text": "CPU" * 4000})
            except (OSError, ValueError, RuntimeError, AssertionError) as error:
                errors.append(error)

        thread = threading.Thread(target=transfer)
        thread.start()
        try:
            assert ready.wait(3)
            try:
                channel.write_json(folder / "parallel.json", {"value": 1})
            except RuntimeError as error:
                rejected = "v3_parallel_channel_forbidden" in str(error)
            else:
                rejected = False
            assert rejected, "otro hilo entró entre fragmentos del mismo transporte"
        finally:
            release.set()
            thread.join(timeout=5)
        assert not thread.is_alive() and not errors
        assert not (folder / "parallel.json").exists()
        assert (
            json.loads((folder / "large-own.json").read_text())["text"] == "CPU" * 4000
        )


def test_finished_v3_requires_external_digest_before_reading_sealed_anchors(
    harness_module, tmp_path, monkeypatch
):
    cli = harness_module("benchmark")
    planner = harness_module("benchmark_plan")
    from benchmark_evidence import exclusive_json, seal_files

    folder = tmp_path / "finished-v3"
    folder.mkdir()
    exclusive_json(folder / "plan.json", {"observation_method": "wddm_auto_v3"})
    exclusive_json(folder / "summary.json", {"rows": 4, "complete": False})
    anchor = {
        "kind": "audit_after_graceful_shutdown",
        "receipts": [{"external": "receipt", "observed_utc": "2026-10-07T00:00:00Z"}],
        "attempts": [{"external": "attempt"}],
        "failure": None,
        "context": {},
        "publication_root": str(folder),
    }
    publication_path = folder / "publications.json"
    exclusive_json(
        publication_path,
        {"receipts": anchor["receipts"], "attempts": anchor["attempts"]},
    )
    exclusive_json(folder / "supervisor-final-audit.json", anchor)
    exclusive_json(folder / "seal.json", seal_files(folder))
    calls = []

    def canonical(value, root, **kwargs):
        assert kwargs["trusted_receipts"] == anchor["receipts"]
        assert kwargs["trusted_attempts"] == anchor["attempts"]
        calls.append(kwargs)

    monkeypatch.setattr(cli, "validate_prerequisites", canonical)
    monkeypatch.setattr(
        harness_module("benchmark_episode"),
        "read_publications",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(cli, "read_sealed", lambda value, root: publication_path)
    try:
        result = cli.finished_session(
            folder,
            prerequisites={
                "observation": {
                    "method": "wddm_auto_v3",
                    "evidence": {"publications": {}},
                }
            },
            supervisor_anchor_sha256=planner.digest(anchor),
        )
    except TypeError:
        result = None
    assert result == 2, "cierre v3 sin entrada explícita de digest externo"
    assert calls
    with pytest.raises(ValueError, match="external_supervisor_anchor"):
        cli.finished_session(
            folder, prerequisites={}, supervisor_anchor_sha256="0" * 64
        )
    with pytest.raises(ValueError, match="external_supervisor_anchor"):
        cli.finished_session(folder, prerequisites={})


@pytest.fixture
def episode_factory():
    # Clonar sólo la salida; conservar las pruebas históricas.
    path = PHASE / "fixtures" / "episode_fixture.py"
    spec = importlib.util.spec_from_file_location("coordinator_episode_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    make = module.episode_factory.__wrapped__()

    def fresh(**config):
        from benchmark_episode import EpisodeAcquirer
        from benchmark_plan import file_hash, source_hashes

        observer, context = make(**config)
        fixture_folder = observer.root.parents[1]
        observer.close()
        context["source_hashes"] = source_hashes(Path.cwd())
        context["lock_sha256"] = file_hash(Path.cwd() / "models/models.lock.json")
        (fixture_folder / "context.json").write_text(
            json.dumps(context), encoding="utf-8"
        )
        observer = EpisodeAcquirer(
            root=fixture_folder / uuid.uuid4().hex / "fresh-publications",
            context_path=fixture_folder / "context.json",
            trusted_handler=f"{fixture_folder / 'sensor_fixture.py'}:Fixture",
            sensor_config=config,
        )
        return observer, context

    return fresh


@pytest.fixture
def operation_worker():
    folder = PHASE / "operations" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    handler = folder / "handler.py"
    handler.write_text(
        """import time, subprocess, sys
class Operation:
    def __init__(self, config):pass
    def __call__(self,payload,emit):
        args=payload["arguments"]
        if args.get("descendant"):
            child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])
            emit({"descendant_pid":child.pid})
        emit({"phase":payload["operation"]})
        time.sleep(args.get("delay",0))
        return {"phase":payload["operation"],"completed_ns":time.perf_counter_ns()}
    def close(self):pass
""",
        encoding="utf-8",
    )
    worker = OwnedProcess({}, f"{handler}:Operation")
    yield worker
    worker.close()


def coordinator(harness_module, observer):
    module = harness_module("benchmark_coordinator")
    if not hasattr(module, "ContinuousCoordinator"):
        observer.close()
    assert hasattr(module, "ContinuousCoordinator"), "coordinador continuo ausente"
    return module.ContinuousCoordinator(observer)


@pytest.mark.parametrize("phase", ["create", "start", "source-hash", "copy"])
def test_same_sampler_observes_three_second_preparation(
    harness_module, episode_factory, operation_worker, phase
):
    observer, context = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        before = len(service.receipts)
        result = service.run_owned(
            phase,
            operation_worker,
            {"operation": phase, "arguments": {"delay": 3}},
            timeout_s=5,
        )
        assert result["value"]["phase"] == phase
        assert len(service.receipts) >= before + 2
        assert (
            service.events[-1]["finished"]["monotonic_ns"]
            > service.events[-1]["started"]["monotonic_ns"] + 3_000_000_000
        )
        assert {record["phase"] for record in service.records[before:]} == {phase}
        service.set_phase("ready", idle=True)
        service.wait_samples(2, timeout_s=4)
    assert not service.sampler.is_alive()
    assert not observer.worker.reader.is_alive()
    assert observer.worker.close_evidence["job_empty"]
    samples = read_publications(
        observer.root,
        service.receipts,
        context,
        trusted_receipts=copy.deepcopy(service.receipts),
        attempts=service.attempts,
        trusted_attempts=copy.deepcopy(service.attempts),
        historical=True,
    )
    assert len(samples) == len(service.receipts)
    gaps = [
        (b["start"]["monotonic_ns"] - a["start"]["monotonic_ns"]) / 1e9
        for a, b in zip(service.receipts, service.receipts[1:])
    ]
    assert gaps and max(gaps) <= 2.5
    assert all(b["previous_receipt_sha256"] is not None for b in service.receipts[1:])


def test_sampler_failure_stops_owned_operation_and_preserves_foreign(
    harness_module, episode_factory, operation_worker
):
    observer, _ = episode_factory()
    fixture_folder = observer.root.parents[1]
    context_path = fixture_folder / "context.json"
    observer.close()
    late = fixture_folder / "late_failure.py"
    late.write_text(
        """import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location("own_sensor",Path(__file__).with_name("sensor_fixture.py"))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Sensor(module.Sensor):
    def __call__(self,payload,emit):
        if self.count: self.config["block_stage"]="sampling"
        return super().__call__(payload,emit)
class Fixture(module.Fixture):
    def make_sensor(self,config):return Sensor(config)
""",
        encoding="utf-8",
    )
    from benchmark_episode import EpisodeAcquirer

    observer = EpisodeAcquirer(
        root=fixture_folder / "late-publications",
        context_path=context_path,
        trusted_handler=f"{late}:Fixture",
    )
    service = coordinator(harness_module, observer)
    foreign = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    started = time.perf_counter_ns()
    try:
        with pytest.raises(RuntimeError), service:
            service.run_owned(
                "blocked-preparation",
                operation_worker,
                {
                    "operation": "prepare",
                    "arguments": {"delay": 20, "descendant": True},
                },
                timeout_s=25,
            )
        assert (time.perf_counter_ns() - started) / 1e9 < 3
        assert not process_alive(operation_worker.pid)
        assert not operation_worker.reader.is_alive()
        assert not observer.worker.reader.is_alive()
        assert not service.sampler.is_alive()
        assert service.failure is not None
        assert service.attempts[-1]["status"] == "interrupted"
        assert foreign.poll() is None
    finally:
        foreign.terminate()
        foreign.wait(timeout=3)


def test_no_parallel_acquisition_or_phase_reset(harness_module, episode_factory):
    observer, _ = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        service.wait_samples(2, timeout_s=4)
        predecessor = copy.deepcopy(service.receipts[-1])
        service.set_phase("loaded", idle=False)
        service.wait_samples(1, timeout_s=3)
        from benchmark_plan import digest

        assert service.receipts[-1]["previous_receipt_sha256"] == digest(predecessor)
    assert len({r["episode_id"] for r in service.receipts}) == len(service.receipts)


def test_offline_anchors_cannot_be_replaced(harness_module, episode_factory):
    observer, context = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        service.wait_samples(2, timeout_s=4)
    forged = copy.deepcopy(service.receipts)
    forged[-1]["observed_monotonic_ns"] += 1
    with pytest.raises(ValueError, match="anchor"):
        read_publications(
            observer.root, forged, context, trusted_receipts=service.receipts
        )


def test_default_cli_policy_is_v3(harness_module):
    args = (
        harness_module("benchmark")
        .parser()
        .parse_args(
            ["--inputs", "inputs.json", "--prerequisites", "prerequisites.json"]
        )
    )
    assert args.observation_method == "wddm_auto_v3"


def test_v3_runner_requires_continuous_owner_before_any_post(harness_module):
    runner = harness_module("benchmark_runner")

    class Forbidden:
        def request(self, *args, **kwargs):
            pytest.fail("POST sin coordinador continuo")

    with pytest.raises(ValueError, match="continuous"):
        runner.execute_run(
            {"observation_method": "wddm_auto_v3"},
            {},
            Forbidden(),
            None,
            PHASE / "forbidden-run",
            {},
        )


def test_create_ack_loss_reconciles_without_duplicate_or_foreign_cleanup(
    harness_module,
):
    runtime = harness_module("benchmark_runtime")
    assert hasattr(runtime.DockerBackend, "recover_create"), (
        "recuperación propia ausente"
    )
    receipt = {
        "container_id": "own",
        "owner": "o",
        "session_id": "s",
        "plan_sha256": "p",
        "port": 8200,
        "storage": "bind",
        "config_id": "c",
    }
    calls = []
    backend = runtime.DockerBackend()

    def call(argv, **kwargs):
        calls.append(argv)
        assert "create" not in argv
        assert "foreign" not in argv
        return json.dumps(
            [
                {
                    "Id": "own",
                    "Name": "/music-studio-t09-s-g",
                    "Image": "image",
                    "HostConfig": {
                        "PortBindings": {
                            "8101/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8200"}]
                        }
                    },
                    "Config": {
                        "Labels": {
                            "studio.t09.owner": "o",
                            "studio.t09.session": "s",
                            "studio.t09.plan": "p",
                        }
                    },
                }
            ]
        )

    backend.call = call
    recovered = backend.recover_create(
        {"session_id": "s", "plan_sha256": "p", "image_id": "image"},
        {"config_id": "c", "group_id": "g"},
        "bind",
        "o",
        8200,
    )
    assert recovered == receipt
    assert len(calls) == 1


@pytest.fixture
def fake_runtime():
    """Backend y engine CPU propios sintéticos; ningún daemon real."""
    folder = PHASE / "fake-runtime" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    plan = {
        "observation_method": "wddm_auto_v3",
        "session_id": "CPU-SYNTHETIC",
        "plan_sha256": "CPU-PLAN",
        "image_id": "CPU-IMAGE",
        "lock_sha256": "CPU-LOCK",
        "timeouts": {"observation_s": 8},
    }
    (folder / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (folder / "owner.json").write_text(
        json.dumps(
            {
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": "CPU-OWNED",
            }
        ),
        encoding="utf-8",
    )
    handler = folder / "fake.py"
    handler.write_text(
        """import json,time
from pathlib import Path
import benchmark_runtime as runtime
from benchmark_clock import utc_now
from benchmark_evidence import exclusive_json
class FakeBackend:
    def __init__(self,folder):self.folder=folder
    def image_id(self,image):return "CPU-IMAGE"
    def trace(self,action):
        with (self.folder/"trace.jsonl").open("a",encoding="utf-8") as f:
            f.write(json.dumps({"action":action,"utc":utc_now(),"monotonic_ns":time.perf_counter_ns(),"synthetic_cpu":True})+"\\n")
    def create(self,plan,config,storage,owner,port,token):
        self.trace("create")
        (self.folder/"container-name").write_text(runtime.container_name(plan,config,storage))
        receipt={"container_id":"CPU-OWN","owner":owner,"session_id":plan["session_id"],"plan_sha256":plan["plan_sha256"],"port":port,"config_id":config["config_id"],"storage":storage}
        exclusive_json(self.folder/"resource.json",receipt)
        time.sleep(3)
        if (self.folder/"lose-ack").exists():raise runtime.ApiError("TRANSPORT_UNAVAILABLE")
        return receipt
    def inspect(self,identity):
        receipt=json.loads((self.folder/"resource.json").read_text())
        self.trace("inspect")
        return {"Id":receipt["container_id"],"Name":"/"+(self.folder/"container-name").read_text(),"Image":"CPU-IMAGE","HostConfig":{"PortBindings":{"8101/tcp":[{"HostIp":"127.0.0.1","HostPort":str(receipt["port"])}]}},"Config":{"Labels":{"studio.t09.owner":receipt["owner"],"studio.t09.session":receipt["session_id"],"studio.t09.plan":receipt["plan_sha256"]}}}
    def recover_create(self,*args):
        self.trace("recover")
        receipt=json.loads((self.folder/"resource.json").read_text())
        runtime.assert_owner(receipt,self.inspect(receipt["container_id"]))
        return receipt
    def start(self,receipt):
        self.trace("start");time.sleep(3)
    def verify_image_sources(self,receipt,plan):
        self.trace("source_hash_copy");time.sleep(3)
        path=Path.cwd()/"data/tmp/t09-storage-CPU-GROUP.json"
        # Private fake storage receipt path supplied by new prepare interface.
        exclusive_json(self.folder/"storage.json",{"resource_root":"/models","destination_lock_sha256":plan["lock_sha256"],"source_lock_sha256":plan["lock_sha256"],"copy_s":3,"synthetic_cpu":True})
    def terminate_owned(self,receipt):
        runtime.assert_owner(receipt,self.inspect(receipt["container_id"]))
        self.trace("remove_owned");(self.folder/"resource.json").unlink();(self.folder/"loaded").unlink(missing_ok=True)
        return {"removed":True,"container_id":receipt["container_id"],"synthetic_cpu":True}
    def cleanup(self,receipt,api):return self.terminate_owned(receipt)
class FakeApi:
    folder=None
    def __init__(self,*args,**kwargs):self.job_id=None;self.events_started=None;self.submits=0
    def request(self,method,path,body=None,**kwargs):
        with (self.folder/"trace.jsonl").open("a") as f:f.write(json.dumps({"action":method+" "+path,"utc":utc_now(),"monotonic_ns":time.perf_counter_ns(),"synthetic_cpu":True})+"\\n")
        if path=="/v1/health":return {"state":"idle","loaded":{"model_id":"CPU-MODEL","mode":"bf16"} if (self.folder/"loaded").exists() else None,"gpu":{"used_mb":1000}}
        if path=="/v1/estimate":return {"synthetic_cpu":True}
        if method=="POST" and path=="/v1/jobs":
            self.submits+=1
            self.job_id=body["job_id"];(self.folder/"loaded").write_text("synthetic_cpu")
            if (self.folder/"lose-post-ack").exists():raise runtime.ApiError("TRANSPORT_UNAVAILABLE")
            return {"job_id":self.job_id}
        if path=="/v1/unload":
            (self.folder/"loaded").unlink(missing_ok=True);return {"unloaded":True}
        if path.startswith("/v1/jobs/"):return {"job_id":path.rsplit("/",1)[-1],"state":"done"}
        return {"unloaded":True}
    def events(self,job_id,after,**kwargs):
        if after:return []
        if self.events_started is None:self.events_started=time.monotonic()
        time.sleep(min(kwargs.get("timeout",1),max(0,3-(time.monotonic()-self.events_started))))
        if time.monotonic()-self.events_started<3:return []
        error=self.session_mode and self.submits>1
        return [{"seq":1,"job_id":job_id,"type":"error" if error else "done","timestamp":utc_now(),"data":{"synthetic_cpu":True,"code":"CPU_SYNTHETIC_NO_INFERENCE"} if error else {"synthetic_cpu":True}}]
class Fixture(runtime.BenchmarkOperationProvider):
    def __init__(self,config):
        import os,site,uuid
        self.cov=None
        if os.environ.get("T09_NATIVE_COVERAGE_CONFIG"):
            site.addsitedir(str(Path.cwd()/".venv/Lib/site-packages"))
            import coverage
            self.cov=coverage.Coverage(config_file=os.environ["T09_NATIVE_COVERAGE_CONFIG"],data_file=os.environ["T09_NATIVE_COVERAGE_PREFIX"]+"."+str(os.getpid())+"."+uuid.uuid4().hex)
            self.cov.start()
        super().__init__(config)
        self.backend=FakeBackend(Path(config["plan_path"]).parent)
        FakeApi.folder=self.backend.folder;FakeApi.session_mode=config.get("session_mode",False);runtime.EngineApi=FakeApi
        runtime.choose_port=lambda:18200
        self.audit_delay=config.get("audit_delay",0)
        self.session_mode=config.get("session_mode",False)
    def __call__(self,payload,emit):
        try:return self.dispatch(payload,emit)
        except Exception:
            import traceback
            (self.backend.folder/"native-error.log").write_text(traceback.format_exc(),encoding="utf-8")
            raise
        finally:
            if self.cov is not None:self.cov.save()
    def close(self):
        if self.cov is not None:self.cov.stop();self.cov.save()
    def dispatch(self,payload,emit):
        if self.session_mode:
            action,args=payload["operation"],payload["arguments"]
            if action in {"lease_acquire","lease_release","ollama_discharge"}:return {"synthetic_cpu":True}
            if action=="ollama_snapshot":return {"models":[],"distro":"SYNTHETIC-CPU"}
            if action=="ollama_restore":return {"restored":True,"models":[],"synthetic_cpu":True}
            if action=="read_json" and "/data/tmp/t09-storage-" in args["path"].replace("\\\\","/"):
                return json.loads((self.backend.folder/"storage.json").read_text())
            if action=="cleanup":
                result=super().__call__(payload,emit)
                return {"api_error":"CPU_STOP_AFTER_OWNED_GROUP_ACK_UNKNOWN","status":503}
        if payload["operation"]=="audit_validate":time.sleep(self.audit_delay)
        return super().__call__(payload,emit)
""",
        encoding="utf-8",
    )
    config = {
        "root": str(Path.cwd()),
        "plan_path": str(folder / "plan.json"),
        "owner_path": str(folder / "owner.json"),
        "token": "SYNTHETIC-NOT-A-SECRET",
    }
    return folder, plan, config, f"{handler}:Fixture"


def test_native_full_preparation_then_v3_runner_no_duplicate_post(
    harness_module, episode_factory, fake_runtime
):
    cli = harness_module("benchmark")
    assert hasattr(cli, "prepare_group_v3"), "préparation v3 continue absente"
    from benchmark_coordinator import RuntimeChannel

    folder, plan, config, handler = fake_runtime
    observer, context = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        worker = OwnedProcess(config, handler)
        channel = RuntimeChannel(service, worker)
        try:
            receipt, storage = cli.prepare_group_v3(
                plan,
                {"config_id": "CPU-CONFIG", "group_id": "CPU-GROUP"},
                "bind",
                folder / "group",
                channel,
                storage_path=folder / "storage.json",
            )
            assert storage["synthetic_cpu"] and receipt["container_id"] == "CPU-OWN"
            run = {"job_id": "CPU-JOB", "run_id": "CPU-RUN"}
            runner = harness_module("benchmark_runner")
            terminal = runner.execute_run(
                plan, run, channel, service, folder / "run", {"job_id": run["job_id"]}
            )
            assert terminal["data"]["synthetic_cpu"]
            assert (
                runner.execute_run(
                    plan,
                    run,
                    channel,
                    service,
                    folder / "run",
                    {"job_id": run["job_id"]},
                )
                == terminal
            )
            channel.operation("cleanup", {})
        finally:
            channel.close()
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(row["action"] == "POST /v1/jobs" for row in trace) == 1
    assert sum(row["action"] == "create" for row in trace) == 1
    assert not (folder / "resource.json").exists()
    submit = next(
        row["monotonic_ns"] for row in trace if row["action"] == "POST /v1/jobs"
    )
    assert all(
        row["monotonic_ns"] < submit
        for row in trace
        if row["action"] in {"create", "start", "source_hash_copy"}
    )
    samples = read_publications(
        observer.root,
        service.receipts,
        context,
        trusted_receipts=service.receipts,
        attempts=service.attempts,
        trusted_attempts=service.attempts,
        historical=True,
    )
    assert len(samples) >= 12


def test_supervisor_audit_runs_without_pausing_sampler(
    harness_module, episode_factory, fake_runtime
):
    from benchmark_coordinator import RuntimeChannel

    assert hasattr(RuntimeChannel, "audit_publications"), (
        "auditoría con anclas IPC ausente"
    )
    _folder, _, config, handler = fake_runtime
    config["audit_delay"] = 3
    observer, _ = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        worker = OwnedProcess(config, handler)
        channel = RuntimeChannel(service, worker)
        try:
            service.wait_samples(2, timeout_s=4)
            count = len(service.receipts)
            audit = channel.audit_publications()
            assert audit["validated"] >= count
            assert len(service.receipts) >= count + 3
            assert len(audit["supervisor_anchor_sha256"]) == 64
            assert service.receipts[-1] == observer.receipts[-1]
        finally:
            channel.close()
    assert not worker.reader.is_alive()
    assert not observer.worker.reader.is_alive()


def test_calibration_builder_uses_real_owned_states_and_full_raw(
    harness_module, episode_factory, fake_runtime
):
    cli = harness_module("benchmark")
    assert hasattr(cli, "collect_calibration_v3"), (
        "builder de calibración supervisada ausente"
    )
    from benchmark_coordinator import RuntimeChannel
    from benchmark_episode import EpisodeAcquirer

    folder, plan, config, handler = fake_runtime
    observer, context = episode_factory()
    fixture_folder = observer.root.parents[1]
    observer.close()
    sensor = fixture_folder / "owned_state_sensor.py"
    sensor.write_text(
        """import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location("own_sensor",Path(__file__).with_name("sensor_fixture.py"))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Sensor(module.Sensor):
    def __call__(self,payload,emit):
        raw=super().__call__(payload,emit)
        used=8000 if Path(self.config["loaded_path"]).exists() else 1200
        raw["nvml"]["used_mb"]=used;raw["nvml"]["free_mb"]=raw["nvml"]["total_mb"]-used
        raw["windows"]["dedicated_mb"]=used
        c=raw["windows"]["counters"]["dedicated_mb"];c["raw_value"]=c["formatted_value"]=used*2**20
        return raw
class Fixture(module.Fixture):
    def make_sensor(self,config):return Sensor(config)
""",
        encoding="utf-8",
    )
    observer = EpisodeAcquirer(
        root=fixture_folder / "state-publications",
        context_path=fixture_folder / "context.json",
        trusted_handler=f"{sensor}:Fixture",
        sensor_config={"loaded_path": str(folder / "loaded")},
    )
    service = coordinator(harness_module, observer)
    with service:
        worker = OwnedProcess(config, handler)
        channel = RuntimeChannel(service, worker)
        try:
            cli.prepare_group_v3(
                plan,
                {"config_id": "CPU-CONFIG", "group_id": "CPU-GROUP"},
                "bind",
                folder / "group",
                channel,
                storage_path=folder / "storage.json",
            )
            result = cli.collect_calibration_v3(
                plan,
                {"job_id": "CPU-PILOT", "run_id": "CPU-PILOT"},
                {"job_id": "CPU-PILOT"},
                folder / "pilot",
                channel,
            )
            assert result["calibration"]["shared_independent_validation"] is False
            assert set(result["phases"]) == {"baseline", "loaded", "unloaded"}
            assert all(len(refs) == 10 for refs in result["phases"].values())
            assert result["terminal"]["data"]["synthetic_cpu"]
            channel.operation("cleanup", {})
        finally:
            channel.close()
    from benchmark_observation import validate_calibration

    envelope = {
        "root": observer.root,
        "receipts": service.receipts[: result["receipt_count"]],
        "attempts": service.attempts[: result["attempt_count"]],
        "phases": result["phases"],
    }
    assert validate_calibration(
        envelope,
        result["lifecycle"],
        context,
        method="wddm_auto_v3",
        trusted_receipts=envelope["receipts"],
        trusted_attempts=envelope["attempts"],
    )["recovered_at"]


def test_v3_metrics_recompute_anchored_raw_and_keep_confidence(
    harness_module, episode_factory
):
    import inspect

    runner = harness_module("benchmark_runner")
    observer, context = episode_factory()
    records = []
    try:
        for index in range(12):
            observer.acquire("baseline" if index < 10 else "run", idle=index < 10)
            records.append(copy.deepcopy(observer.last_record))
    finally:
        observer.close()
    evidence = {
        "publication_root": observer.root,
        "records": records,
        "trusted_receipts": copy.deepcopy(observer.receipts),
        "attempts": copy.deepcopy(observer.attempts),
        "trusted_attempts": copy.deepcopy(observer.attempts),
    }
    kwargs = (
        {"v3_evidence": evidence}
        if "v3_evidence" in inspect.signature(runner.summarize_run).parameters
        else {}
    )
    row = runner.summarize_run(
        {"run_id": "CPU-METRICS"},
        {"type": "done", "data": {}},
        records[10:],
        records[:10],
        output_valid=False,
        fidelity_valid=False,
        observation_context=context,
        **kwargs,
    )
    assert row["method"] == "wddm_auto_v3"
    assert row["shared_independent_validation"] is False
    assert row["shared_gpu_observed"] is False
    assert row["valid"] is False


def test_v3_session_dispatches_continuous_path_before_legacy_gpu_calls(
    harness_module, monkeypatch
):
    cli = harness_module("benchmark")
    assert hasattr(cli, "run_session_v3"), "orquestación de sesión v3 ausente"
    sentinel = []

    def owned(*args, **kwargs):
        sentinel.append((args, kwargs))
        return [{"synthetic_cpu": True}]

    monkeypatch.setattr(cli, "run_session_v3", owned)
    result = cli.run_session(
        {"observation_method": "wddm_auto_v3"}, PHASE / "dispatch", {}
    )
    assert result == [{"synthetic_cpu": True}]
    assert len(sentinel) == 1


@pytest.mark.parametrize("own_service", [False, True])
def test_native_session_pilot_accreditation_four_original_rows_and_uncertain_cleanup(
    harness_module, episode_factory, fake_runtime, monkeypatch, own_service
):
    """Plan160 conservado; límite CPU explícito tras un grupo propio."""
    import ast

    from benchmark_clock import utc_now
    from benchmark_episode import EpisodeAcquirer
    from benchmark_observation import acquisition_context
    from benchmark_plan import build_plan, file_hash
    from benchmark_runtime import ApiError

    cli = harness_module("benchmark")
    folder, _, _config, handler = fake_runtime
    fixtures = {}
    for duration in (30, 60, 180, 300):
        path = folder / f"input-{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "lyrics": "Letra sintética CPU propia",
                        "style": "fixture CPU",
                        "language": "es",
                        "duration_s": duration,
                    },
                }
            ),
            encoding="utf-8",
        )
        fixtures[str(duration)] = {
            "path": path.relative_to(Path.cwd()).as_posix(),
            "sha256": file_hash(path),
        }
    plan = build_plan(
        {"fixtures_by_duration": fixtures},
        image_id="CPU-IMAGE",
        prerequisites_sha256=None,
    )
    (folder / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (folder / "owner.json").write_text(
        json.dumps(
            {
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": "CPU-OWNED",
            }
        ),
        encoding="utf-8",
    )
    observer, context = episode_factory()
    fixture_folder = observer.root.parents[1]
    observer.close()
    context.update(
        {
            key: plan[key]
            for key in (
                "session_id",
                "plan_sha256",
                "source_hashes",
                "image_id",
                "lock_sha256",
            )
        }
    )
    (fixture_folder / "context.json").write_text(json.dumps(context), encoding="utf-8")
    # Reutilizar SOLO nuestro seam nuevo, conservando su reloj real.
    parsed = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(
        node
        for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_calibration_builder_uses_real_owned_states_and_full_raw"
    )
    sensor_text = next(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("import importlib.util")
    )
    sensor = fixture_folder / "session_state_sensor.py"
    sensor.write_text(sensor_text, encoding="utf-8")
    observer = EpisodeAcquirer(
        root=fixture_folder / "session-publications",
        context_path=fixture_folder / "context.json",
        trusted_handler=f"{sensor}:Fixture",
        sensor_config={"loaded_path": str(folder / "loaded")},
    )
    acquisition = acquisition_context(context, "wddm_auto_v3")
    host = {
        **{
            key: context[key]
            for key in (
                "driver_version",
                "windows_build",
                "nvml_uuid",
                "adapter_luid",
                "browser_identity",
            )
        },
        "acquisition_context": acquisition,
        "synthetic_cpu": True,
    }
    viewport = {
        "url": "about:blank",
        "tab_id": "CPU-SYNTHETIC-TAB",
        "browser_id": "CPU-SYNTHETIC-BROWSER",
        "visible": True,
        "observed_at": utc_now(),
        "acquisition_context": acquisition,
        "synthetic_cpu": True,
    }
    (folder / "host.json").write_text(json.dumps(host), encoding="utf-8")
    (folder / "viewport.json").write_text(json.dumps(viewport), encoding="utf-8")
    seed = {
        "observation": {
            "method": "wddm_auto_v3",
            "context": context,
            "evidence": {
                "host": {
                    "path": (folder / "host.json").relative_to(Path.cwd()).as_posix()
                }
            },
            "viewport": {
                "evidence": {
                    "path": (folder / "viewport.json")
                    .relative_to(Path.cwd())
                    .as_posix()
                }
            },
        },
        "browser": context["browser_identity"],
        "exclusive_gpu_authorized": True,
    }
    service = coordinator(harness_module, observer)
    workers = []

    def factory(owned_config, *, coordinator=None):
        from benchmark_coordinator import CoordinatedOwnedProcess

        worker = (
            CoordinatedOwnedProcess(
                {**owned_config, "session_mode": True}, handler, coordinator=coordinator
            )
            if coordinator is not None
            else OwnedProcess({**owned_config, "session_mode": True}, handler)
        )
        workers.append(worker)
        return worker

    from contextlib import nullcontext

    owned_acquirers = []
    if own_service:
        service.close()

        def synthetic_owned_acquirer(**kwargs):
            kwargs.update(
                trusted_handler=f"{sensor}:Fixture",
                sensor_config={"loaded_path": str(folder / "loaded")},
            )
            acquired = EpisodeAcquirer(**kwargs)
            owned_acquirers.append(acquired)
            return acquired

        monkeypatch.setattr(
            harness_module("benchmark_episode"),
            "EpisodeAcquirer",
            synthetic_owned_acquirer,
        )
    with (
        nullcontext() if own_service else service,
        pytest.raises(ApiError, match="CPU_STOP_AFTER"),
    ):
        cli.run_session(
            plan,
            folder,
            seed,
            token="SYNTHETIC-NOT-A-SECRET",
            coordinator=None if own_service else service,
            runtime_factory=factory,
        )
    rows = [
        json.loads(path.read_text()) for path in (folder / "runs").glob("*/row.json")
    ]
    assert len(rows) == 4
    assert {row["run_id"] for row in rows} == {
        run["run_id"] for run in plan["runs"][:4]
    }
    assert all(
        row["method"] == "wddm_auto_v3"
        and row["valid"] is False
        and row["shared_independent_validation"] is False
        for row in rows
    )
    assert len(plan["runs"]) == 160
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(row["action"] == "create" for row in trace) == 1
    assert sum(row["action"] == "POST /v1/jobs" for row in trace) == 5
    recovery = json.loads(next(folder.glob("recovery-*.json")).read_text())
    assert recovery["uncertain"] is True
    assert recovery["remote_request_cancelled"] is False
    assert all(
        not worker.reader.is_alive() and worker.close_evidence["job_empty"]
        for worker in workers
    )
    if own_service:
        anchor = json.loads((folder / "supervisor-final-audit.json").read_text())
        assert (
            anchor["kind"] == "audit_after_graceful_shutdown"
            and anchor["failure"] is None
        )
        assert anchor["receipts"][-1] == owned_acquirers[0].receipts[-1]
        assert anchor["attempts"] == owned_acquirers[0].attempts
        assert not owned_acquirers[0].worker.reader.is_alive()
        assert owned_acquirers[0].worker.close_evidence["job_empty"]


def test_sampler_failure_interrupts_operation_provider_startup(
    harness_module, episode_factory
):
    module = harness_module("benchmark_coordinator")
    observer, _ = episode_factory()
    fixture_folder = observer.root.parents[1]
    observer.close()
    late = fixture_folder / "late_startup_failure.py"
    late.write_text(
        """import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location("own_sensor",Path(__file__).with_name("sensor_fixture.py"))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Sensor(module.Sensor):
    def __call__(self,payload,emit):
        if self.count:self.config["block_stage"]="sampling"
        return super().__call__(payload,emit)
class Fixture(module.Fixture):
    def make_sensor(self,config):return Sensor(config)
""",
        encoding="utf-8",
    )
    from benchmark_episode import EpisodeAcquirer

    observer = EpisodeAcquirer(
        root=fixture_folder / "startup-failure-publications",
        context_path=fixture_folder / "context.json",
        trusted_handler=f"{late}:Fixture",
    )
    startup = fixture_folder / "blocked_operation_startup.py"
    startup.write_text(
        """import time
class Operation:
    def __init__(self,config):time.sleep(20)
    def __call__(self,payload,emit):return {}
    def close(self):pass
""",
        encoding="utf-8",
    )
    service = coordinator(harness_module, observer)
    worker = None
    started = time.perf_counter_ns()
    try:
        with pytest.raises(RuntimeError), service:
            if hasattr(module, "CoordinatedOwnedProcess"):
                worker = module.CoordinatedOwnedProcess.__new__(
                    module.CoordinatedOwnedProcess
                )
                worker.__init__({}, f"{startup}:Operation", coordinator=service)
            else:
                worker = OwnedProcess.__new__(OwnedProcess)
                worker.__init__({}, f"{startup}:Operation")
        assert (time.perf_counter_ns() - started) / 1e9 < 3
        assert not worker.reader.is_alive()
        assert worker.close_evidence["job_empty"]
    finally:
        if worker is not None and hasattr(worker, "closed"):
            worker.close()


def test_native_lost_create_ack_recovers_own_identity_without_create_retry(
    harness_module, episode_factory, fake_runtime
):
    from benchmark_coordinator import RuntimeChannel
    from benchmark_runtime import ApiError

    folder, _, config, handler = fake_runtime
    (folder / "lose-ack").write_text("synthetic acknowledgement loss", encoding="utf-8")
    foreign = folder / "foreign-container.json"
    foreign.write_text('{"owner":"FOREIGN"}', encoding="utf-8")
    observer, _ = episode_factory()
    service = coordinator(harness_module, observer)
    args = {
        "config": {"config_id": "CPU-CONFIG", "group_id": "CPU-GROUP"},
        "storage": "bind",
        "folder": str(folder / "group"),
    }
    with service:
        worker = OwnedProcess(config, handler)
        channel = RuntimeChannel(service, worker)
        try:
            with pytest.raises(ApiError, match="TRANSPORT_UNAVAILABLE"):
                channel.operation("create", args, timeout_s=5)
            assert (folder / "group/create-intent.json").is_file()
            receipt = channel.operation("create", args, timeout_s=5)
            assert receipt["container_id"] == "CPU-OWN"
            channel.operation("terminate_owned", {})
        finally:
            channel.close()
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(event["action"] == "create" for event in trace) == 1
    assert sum(event["action"] == "recover" for event in trace) == 1
    assert foreign.read_text() == '{"owner":"FOREIGN"}'


def test_native_lost_post_ack_queries_same_job_without_post_retry(
    harness_module, episode_factory, fake_runtime
):
    from benchmark_coordinator import RuntimeChannel
    from benchmark_runtime import ApiError

    folder, plan, config, handler = fake_runtime
    observer, _ = episode_factory()
    service = coordinator(harness_module, observer)
    with service:
        worker = OwnedProcess(config, handler)
        channel = RuntimeChannel(service, worker)
        try:
            channel.operation(
                "create",
                {
                    "config": {"config_id": "CPU-CONFIG", "group_id": "CPU-GROUP"},
                    "storage": "bind",
                    "folder": str(folder / "group"),
                },
                timeout_s=5,
            )
            (folder / "lose-post-ack").write_text(
                "synthetic acknowledgement loss", encoding="utf-8"
            )
            run = {"run_id": "CPU-POST", "job_id": "CPU-POST"}
            runner = harness_module("benchmark_runner")
            with pytest.raises(ApiError, match="TRANSPORT_UNAVAILABLE"):
                runner.execute_run(
                    plan,
                    run,
                    channel,
                    service,
                    folder / "run",
                    {"job_id": run["job_id"]},
                )
            terminal = runner.execute_run(
                plan, run, channel, service, folder / "run", {"job_id": run["job_id"]}
            )
            assert terminal["job_id"] == run["job_id"]
            channel.operation("terminate_owned", {})
        finally:
            channel.close()
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(event["action"] == "POST /v1/jobs" for event in trace) == 1
    assert any(event["action"] == "GET /v1/jobs/CPU-POST" for event in trace)


@pytest.mark.parametrize("change", ["foreign_owner", "foreign_port", "foreign_name"])
def test_recovery_rejects_foreign_resources_before_cleanup(harness_module, change):
    runtime = harness_module("benchmark_runtime")
    receipt = {
        "container_id": "OWN",
        "session_id": "s",
        "plan_sha256": "p",
        "owner": "o",
        "port": 18200,
    }
    inspection = {
        "Id": "OWN",
        "Name": "/owned-name",
        "Config": {
            "Labels": {
                "studio.t09.session": "s",
                "studio.t09.plan": "p",
                "studio.t09.owner": "o",
            }
        },
        "HostConfig": {
            "PortBindings": {"8101/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18200"}]}
        },
    }
    if change == "foreign_owner":
        inspection["Config"]["Labels"]["studio.t09.owner"] = "FOREIGN"
    elif change == "foreign_port":
        inspection["HostConfig"]["PortBindings"]["8101/tcp"][0]["HostPort"] = "FOREIGN"
    else:
        inspection["Name"] = "/FOREIGN"
    with pytest.raises(ValueError, match="conflict"):
        runtime.assert_owner(receipt, inspection)
        runtime.assert_endpoint(receipt, inspection, expected_name="owned-name")


def test_sampler_failure_during_create_ack_reconciles_and_removes_only_own(
    harness_module, episode_factory, fake_runtime
):
    import ast

    from benchmark_coordinator import CoordinatedOwnedProcess, RuntimeChannel
    from benchmark_episode import EpisodeAcquirer
    from benchmark_process import WorkerFailure
    from benchmark_runtime import recover_owned_runtime

    folder, _, config, handler = fake_runtime
    observer, _ = episode_factory()
    fixture_folder = observer.root.parents[1]
    observer.close()
    parsed = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(
        node
        for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_sampler_failure_interrupts_operation_provider_startup"
    )
    text = next(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("import importlib.util")
    )
    late = fixture_folder / "during_create_failure.py"
    late.write_text(text, encoding="utf-8")
    observer = EpisodeAcquirer(
        root=fixture_folder / "during-create-publications",
        context_path=fixture_folder / "context.json",
        trusted_handler=f"{late}:Fixture",
    )
    service = coordinator(harness_module, observer)
    foreign = folder / "foreign-container.json"
    foreign.write_text('{"owner":"FOREIGN"}', encoding="utf-8")
    args = {
        "config": {"config_id": "CPU-CONFIG", "group_id": "CPU-GROUP"},
        "storage": "bind",
        "folder": str(folder / "group"),
    }
    with pytest.raises(WorkerFailure), service:
        worker = CoordinatedOwnedProcess(config, handler, coordinator=service)
        channel = RuntimeChannel(service, worker)
        channel.operation("create", args, timeout_s=5)
    assert worker.close_evidence["job_empty"] and not worker.reader.is_alive()
    assert service.attempts[-1]["status"] == "interrupted"
    assert (folder / "resource.json").exists()
    recovery = recover_owned_runtime(
        config, args, None, runtime_factory=lambda values: OwnedProcess(values, handler)
    )
    assert recovery["uncertain"] is False
    assert recovery["cleanup"]["removed"] is True
    assert recovery["remote_request_cancelled"] is False
    assert not (folder / "resource.json").exists()
    assert foreign.read_text() == '{"owner":"FOREIGN"}'
    trace = [
        json.loads(line) for line in (folder / "trace.jsonl").read_text().splitlines()
    ]
    assert sum(event["action"] == "create" for event in trace) == 1
    assert sum(event["action"] == "recover" for event in trace) == 1
