"""Sensor CPU simulado; autoridad, procesos, archivos y relojes Windows reales."""

import copy
import importlib.util
import json
import os
import time
import uuid
from pathlib import Path

import pytest

PRIVATE = Path(os.environ["STUDIO_CANONICAL_TEST_ROOT"])


@pytest.fixture
def actual_sensor_factory():
    # Only relocate the existing CPU sensor fixture, never replace authority.
    source = Path("scripts/eval/tests/test_benchmark_episode_v3.py").read_text(
        encoding="utf-8"
    )
    root = PRIVATE / uuid.uuid4().hex
    root.mkdir(parents=True)
    source = source.replace(
        'PHASE = Path.cwd() / ".cache/dev-cycle/t09/publication-v3-implementation"',
        f"PHASE = Path({str(root)!r})",
    )
    fixture = root / "sensor_factory.py"
    fixture.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("integration_sensor", fixture)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    factory = module.episode_factory.__wrapped__()
    owned = []

    def make(**config):
        if config.get("exit_second"):
            fixture = next(root.rglob("sensor_fixture.py"))
            fixture.write_text(
                fixture.read_text(encoding="utf-8").replace(
                    "self.count+=1",
                    'self.count+=1\n        if self.config.get("exit_second") and self.count>1:\n            import os; os._exit(17)',
                ),
                encoding="utf-8",
            )
        acquirer, context = factory(**config)
        owned.append(acquirer)
        return acquirer, context, root

    yield make
    for acquirer in reversed(owned):
        acquirer.close()


def test_real_episode_publishes_only_after_canonical_confirm(actual_sensor_factory):
    from benchmark_canonical_integration import bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    try:
        acquirer.acquire("baseline")
        assert canonical.publication is not None, "accepted before canonical ingestion"
        assert acquirer.previous_receipt is canonical.last_receipt
        assert canonical.publication["confirmed"] <= (
            acquirer.previous_receipt["start"]["monotonic_ns"] + 2_000_000_000
        )
    finally:
        canonical.close()


def test_real_rejected_completion_becomes_negative_head(actual_sensor_factory):
    from benchmark_canonical_runtime import CanonicalChannel

    acquirer, _, root = actual_sensor_factory(invalid=True)
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    try:
        with pytest.raises(ValueError, match="observability_lost"):
            acquirer.acquire("baseline")
        error = None
        try:
            canonical.ingest_latest()
        except (KeyError, ValueError, RuntimeError) as caught:
            error = caught
        assert error is None, f"real rejected completion adapter failed: {error!r}"
        assert canonical.last_attempt["status"] == "rejected"
        assert canonical.last_receipt is None
        with pytest.raises((OSError, ValueError, RuntimeError, KeyError)):
            canonical.request_view(
                kind="status", deadline_ns=time.perf_counter_ns() + 2_000_000_000
            )
    finally:
        canonical.close()


def provider_config(root):
    plan = {"session_id": "cpu", "plan_sha256": "p"}
    owner = {**plan, "owner": "own"}
    plan_path, owner_path = root / "plan.json", root / "owner.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    owner_path.write_text(json.dumps(owner), encoding="utf-8")
    return {
        "root": str(root),
        "plan_path": str(plan_path),
        "owner_path": str(owner_path),
        "token": "cpu-fixture-only",
    }


def test_actual_provider_forged_audit_denied_before_emit(tmp_path):
    from benchmark_canonical_integration import _canonical_operation_provider

    provider = _canonical_operation_provider(provider_config(tmp_path))
    emitted = []
    error = None
    try:
        provider(
            {
                "operation": "audit_begin",
                "arguments": {
                    "characters": 0,
                    "sha256": "caller",
                    "validated": True,
                    "canonical_mux_v1": True,
                    "root": str(tmp_path),
                },
            },
            emitted.append,
        )
    except ValueError as caught:
        error = caught
    assert error is not None, "actual provider accepted caller audit authority"
    assert emitted == [], "guard must run before progress or effects"


def test_actual_runtime_reads_independent_fresh_typed_status(actual_sensor_factory):
    from benchmark_canonical_integration import bind_acquirer, bind_runtime
    from benchmark_canonical_runtime import CanonicalChannel, CanonicalPosition
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_process import OwnedProcess

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    worker = OwnedProcess(
        provider_config(root),
        "benchmark_canonical_integration:_canonical_operation_provider",
    )
    coordinator = ContinuousCoordinator(acquirer, interval_s=0.15)
    try:
        coordinator.__enter__()
        runtime = RuntimeChannel(coordinator, worker)
        bind_runtime(runtime, canonical)
        error = None
        try:
            value = runtime.audit_publications()
        except (OSError, ValueError, RuntimeError, KeyError) as caught:
            error = caught
        assert worker.seq == 0, (
            "independent status sent audit_begin to operation worker"
        )
        assert error is None, repr(error)
        assert isinstance(getattr(value, "position", value), CanonicalPosition), (
            "audit returned legacy worker status"
        )
        assert worker.seq == 0, "status touched long operation worker"
        other = runtime.audit_publications()
        assert other is not value, "every read needs fresh accreditation"
    finally:
        coordinator.close()
        canonical.close()
        worker.close()


def test_factory_owns_actual_workers_and_fresh_consumer_binding(actual_sensor_factory):
    from benchmark_canonical_integration import (
        consume_runtime,
        create_session,
        source_seals,
    )
    from benchmark_process import decode

    acquirer, _, root = actual_sensor_factory()
    config = decode(acquirer.worker._trusted_config_bytes)
    acquirer.close()
    handler = next(root.rglob("sensor_fixture.py"))
    with create_session(
        root=config["root"],
        context_path=config["context_path"],
        private_root=root / "canonical",
        stream="stable-session",
        sensor_config={},
        operation_config=provider_config(root),
        sensor_handler=f"{handler}:Fixture",
        expected_sources=source_seals(f"{handler}:Fixture"),
        interval_s=0.3,
    ) as session:
        consumer = object()
        view = session.read(kind="base", consumer=consumer)
        assert view.position.kind == "base"
        assert session.operation_worker.seq == 0
        with pytest.raises(ValueError):
            consume_runtime(session.runtime, copy.copy(view), consumer=consumer)
        with pytest.raises(ValueError):
            consume_runtime(session.runtime, view, consumer=object())
        current = consume_runtime(session.runtime, view, consumer=consumer)
        assert current.position.token != view.position.token
        with pytest.raises(ValueError):
            consume_runtime(session.runtime, view, consumer=consumer)
        assert all(worker.ownership["job_member"] for worker in session.workers)
        session.runtime.write_json(
            root / "ordinary.json",
            {"validated": True, "caller_effect": "not_certification"},
        )
        assert (
            json.loads((root / "ordinary.json").read_text())["caller_effect"]
            == "not_certification"
        )
        seq = session.operation_worker.seq
        for action in ("audit_begin", "row", "args_begin"):
            with pytest.raises(ValueError, match="consumer_not_migrated"):
                session.runtime.operation(action, {"action": "audit_validate"})
        assert session.operation_worker.seq == seq
    assert all(worker.closed for worker in session.workers)


@pytest.mark.parametrize(
    "action",
    [
        "audit_begin",
        "audit_fragment",
        "audit_validate",
        "audit_delta_status",
        "audit_delta_begin",
        "audit_delta_fragment",
        "audit_delta_commit",
        "audit_delta_future",
        "calibration_export",
        "accreditation",
        "refresh_accreditation",
        "row",
    ],
)
@pytest.mark.parametrize(
    "route", ["direct", "args_begin", "args_fragment", "args_execute"]
)
def test_actual_provider_closes_every_unmigrated_route(tmp_path, action, route):
    from benchmark_canonical_integration import _canonical_operation_provider

    provider = _canonical_operation_provider(provider_config(tmp_path))
    provider.arguments_header = {"action": action}
    emitted = []
    arguments = {
        "action": action,
        "characters": 0,
        "index": 0,
        "text": "",
        "validated": True,
    }
    with pytest.raises(ValueError, match="canonical_consumer_not_migrated"):
        provider(
            {
                "operation": action if route == "direct" else route,
                "arguments": arguments,
            },
            emitted.append,
        )
    assert emitted == []
    assert not hasattr(provider, "audit_header")
    assert not hasattr(provider, "audit_value")


def test_phase_changes_preserve_ordinal_and_exact_canonical_receipts(
    actual_sensor_factory,
):
    from benchmark_canonical_integration import bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session-stream"
    )
    bind_acquirer(acquirer, canonical)
    try:
        for ordinal, phase in enumerate(("baseline", "readiness", "load-unload"), 1):
            acquirer.acquire(phase)
            assert acquirer.previous_receipt is canonical.last_receipt
            assert acquirer.previous_receipt["ordinal"] == ordinal
            assert canonical.publication["commit"]["cursor"] == ordinal
            assert canonical.last_attempt["receipt"] is canonical.last_receipt
            request = json.loads(
                (
                    acquirer.root
                    / acquirer.previous_receipt["episode_id"]
                    / "request.json"
                ).read_text()
            )
            assert request["request"]["stream"] == phase
            assert canonical.binding["stream"] == "session-stream"
    finally:
        canonical.close()


def test_accepted_then_rejected_invalidates_old_positive_head(actual_sensor_factory):
    from benchmark_canonical_integration import bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    try:
        acquirer.acquire("baseline")
        old = canonical.request_view(deadline_ns=time.perf_counter_ns() + 2_000_000_000)
        # EpisodeProvider itself rejects raw-only requests; no policy/authority double.
        with pytest.raises(ValueError, match="observability_lost"):
            acquirer.acquire("readiness", enforce=False)
        assert canonical.last_attempt["status"] == "rejected"
        assert "receipt" not in canonical.last_attempt
        assert canonical.publication["commit"]["cursor"] == 2
        assert canonical.last_receipt is acquirer.previous_receipt is None
        assert len(acquirer.receipts) == 1
        with pytest.raises(ValueError):
            canonical._resolve_position(old)
        with pytest.raises((OSError, ValueError, RuntimeError, KeyError)):
            canonical.request_view(deadline_ns=time.perf_counter_ns() + 2_000_000_000)
    finally:
        canonical.close()


@pytest.mark.parametrize(
    "fault", ["late-confirm", "publish-failure", "capture-failure", "interrupt"]
)
def test_real_failures_revoke_preserve_raw_never_publish(
    actual_sensor_factory, monkeypatch, fault
):
    from benchmark_canonical_integration import bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_process import WorkerFailure

    acquirer, _, root = actual_sensor_factory(
        **({"block_stage": "sampling"} if fault == "interrupt" else {})
    )
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    original = canonical.worker.call

    def call(payload, **kwargs):
        if fault == "publish-failure" and payload["operation"] == "publish":
            raise WorkerFailure("own_publication_failure")
        if fault == "capture-failure" and payload["operation"] == "end":
            # Mutate actual original bytes before the real child capture.
            directory = next(acquirer.root.glob("*/raw-1.json"))
            directory.write_bytes(b"{broken original")
        result = original(payload, **kwargs)
        if fault == "late-confirm" and payload["operation"] == "confirm":
            time.sleep(max(0, (kwargs["deadline_ns"] - time.perf_counter_ns()) / 1e9))
        return result

    monkeypatch.setattr(canonical.worker, "call", call)
    try:
        with pytest.raises(WorkerFailure):
            acquirer.acquire("baseline")
        assert acquirer.receipts == []
        assert acquirer.previous_receipt is acquirer.last_record is None
        assert acquirer.attempts[-1]["status"] == "interrupted"
        assert canonical.publication is None
        assert canonical.worker.closed
        assert list(acquirer.root.rglob("progress-*.json")), "RAW/progress must survive"
    finally:
        canonical.close()


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (200, b'{"state":"idle"}', None),
        (403, b'{"code":"DENIED"}', "DENIED"),
        (500, b"broken", "HTTP_ERROR"),
        (200, b"broken", "TRANSPORT_UNAVAILABLE"),
    ],
)
def test_real_engine_api_parses_cpu_external_transport(
    monkeypatch, status, body, expected
):
    """HTTP socket bytes simulated, actual EngineApi and HTTP parser; no network."""
    import io

    import benchmark_runtime as runtime

    sent, closed = [], []

    class Socket:
        def setsockopt(self, *args):
            pass

        def settimeout(self, timeout):
            assert timeout > 0

        def sendall(self, value):
            sent.append(value)

        def makefile(self, mode, **kwargs):
            return io.BytesIO(
                f"HTTP/1.1 {status} CPU\r\nContent-Length: {len(body)}\r\n\r\n".encode()
                + body
            )

        def close(self):
            closed.append(True)

    monkeypatch.setattr(runtime.socket, "create_connection", lambda *a, **kw: Socket())
    api = runtime.EngineApi(12345, "CPU-TOKEN", timeout=1)
    if expected:
        with pytest.raises(runtime.ApiError) as caught:
            api.request("POST", "/cpu", {"x": 1})
        assert caught.value.code == expected
    else:
        assert api.request_before("GET", "/cpu", deadline=time.monotonic() + 1) == {
            "state": "idle"
        }
    assert closed
    assert b"X-Studio-Engine-Token: CPU-TOKEN" in b"".join(sent)


@pytest.mark.parametrize(
    "body,status",
    [
        (b'\n{"type":"progress","seq":1}\n{"type":"done","seq":2}\n', 200),
        (b"broken\n", 200),
        (b'{"type":"progress","seq":1}\n', 200),
        (b"", 503),
    ],
)
def test_real_engine_events_cpu_socket_stream(monkeypatch, body, status):
    import io

    import benchmark_runtime as runtime

    class Socket:
        def setsockopt(self, *args):
            pass

        def settimeout(self, timeout):
            pass

        def sendall(self, value):
            pass

        def makefile(self, *a, **kw):
            return io.BytesIO(
                f"HTTP/1.1 {status} CPU\r\nContent-Length: {len(body)}\r\n\r\n".encode()
                + body
            )

        def close(self):
            pass

    monkeypatch.setattr(runtime.socket, "create_connection", lambda *a, **kw: Socket())
    api = runtime.EngineApi(12345, "CPU")
    if status == 503:
        with pytest.raises(runtime.ApiError, match="HTTP_ERROR"):
            api.events("own", 7, timeout=1)
    else:
        events = api.events("own", 7, timeout=1)
        assert [event["seq"] for event in events] == (
            [1, 2] if b"done" in body else [1] if b"progress" in body else []
        )


def test_real_gpu_lease_cpu_files_quarantine_and_foreign_identity(
    tmp_path, monkeypatch
):
    import benchmark_runtime as runtime

    owner = {"session_id": "CPU", "plan_sha256": "PLAN", "owner": "OWN"}
    lease = runtime.GpuLease(tmp_path / "lease.json", owner)
    lease.quarantine()
    with pytest.raises(ValueError, match="quarantined"):
        lease.acquire(resume=True)
    with pytest.raises(ValueError, match="quarantined"):
        lease.release()
    lease.release(reconciled=True)
    lease.acquire()
    lease.quarantine()
    assert json.loads(lease.path.read_text())["quarantined"]
    lease.release(reconciled=True)
    lease.path.write_text(json.dumps({**owner, "pid": 123}))
    monkeypatch.setattr(runtime, "pid_alive", lambda pid: False)
    lease.claim.write_text(json.dumps({**owner, "pid": 124}))
    lease.acquire(resume=True)
    assert list(tmp_path.glob("*.previous-*"))
    claimed = json.loads(lease.claim.read_text())
    lease.claim.write_text(json.dumps({**claimed, "owner": "FOREIGN"}))
    with pytest.raises(ValueError):
        lease.release()
    lease.claim.write_text(json.dumps(claimed))
    lease.release()
    with pytest.raises(ValueError):
        runtime.GpuLease(tmp_path / "invalid", owner, holder_pid=True)


def test_real_ollama_state_simulated_external_executor_only():
    from types import SimpleNamespace

    from benchmark_runtime import OllamaState

    models = ["CPU-model"]
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        if argv[-2:] == ["stop", "CPU-model"]:
            models.clear()
        if "run" in argv:
            models.append("CPU-model")
        return SimpleNamespace(
            returncode=0, stdout="NAME SIZE\n" + "".join(m + " 1\n" for m in models)
        )

    state = OllamaState(execute=execute)
    snapshot = state.snapshot()
    state.discharge(snapshot)
    assert models == []
    assert state.restore(snapshot)["restored"]
    assert models == ["CPU-model"]
    with pytest.raises(ValueError, match="conflict"):
        state.restore(snapshot)
    with pytest.raises(ValueError):
        OllamaState(execute=lambda *a, **kw: SimpleNamespace(returncode=1)).snapshot()
    assert all(argv[:5] == ["wsl", "-d", "Ubuntu", "-e", "ollama"] for argv in calls)


def test_actual_provider_legacy_effects_and_large_transfer(tmp_path):
    from benchmark_plan import digest
    from benchmark_runtime import BenchmarkOperationProvider

    provider = BenchmarkOperationProvider(provider_config(tmp_path))
    emitted = []

    def call(action, args):
        return provider({"operation": action, "arguments": args}, emitted.append)

    value = {"own": "CPU" * 3000}
    arguments = {"path": str(tmp_path / "large.json"), "value": value}
    serialized = json.dumps(arguments)
    assert call(
        "args_begin",
        {
            "action": "write_json",
            "characters": len(serialized),
            "sha256": digest(arguments),
        },
    ) == {"started": True}
    for index, offset in enumerate(range(0, len(serialized), 1200)):
        call(
            "args_fragment",
            {"index": index, "text": serialized[offset : offset + 1200]},
        )
    call("args_execute", {})
    assert call("read_json", {"path": str(tmp_path / "large.json")}) == value
    assert call("exists", {"path": str(tmp_path / "large.json")})
    call(
        "append_record",
        {
            "path": str(tmp_path / "rows.jsonl"),
            "value": {"run_id": "cpu", "valid": False},
        },
    )
    assert (
        call("read_records", {"path": str(tmp_path / "rows.jsonl")})[0]["valid"]
        is False
    )
    assert call("audit_begin", {"characters": 0, "sha256": "caller"}) == {
        "started": True
    }
    assert emitted
    with pytest.raises(ValueError):
        call("unknown", {})
    provider.close()


def test_integrated_provider_ignores_caller_audit_bootstrap_before_io(tmp_path):
    from benchmark_canonical_integration import _canonical_operation_provider

    config = provider_config(tmp_path)
    config.update(
        audit_binding_path=str(tmp_path / "does-not-exist.json"),
        audit_binding_sha256="caller",
    )
    error = None
    try:
        provider = _canonical_operation_provider(config)
    except (OSError, ValueError) as caught:
        error = caught
    assert error is None, "integrated provider consulted caller audit bootstrap"
    assert provider.audit_prefix is None


def test_actual_docker_backend_and_provider_legacy_cpu_dependency_fixture(
    tmp_path, monkeypatch
):
    """Real provider/backend/lease; daemon, socket and Ollama executors simulated."""
    from types import SimpleNamespace

    import benchmark_runtime as runtime

    provider = runtime.BenchmarkOperationProvider(provider_config(tmp_path))
    provider.plan.update(
        image_id="CPU-IMAGE", observation_method="wddm_auto_v3", source_hashes={}
    )
    calls = []
    config = {
        "config_id": "CPU",
        "checkpoint": "acestep-v15-base",
        "lm": "acestep-5Hz-lm-0.6B",
        "mode": "bf16",
    }
    receipt = {
        "container_id": "CPU-ID",
        "session_id": "cpu",
        "plan_sha256": "p",
        "owner": "own",
        "port": 12345,
        "config_id": "CPU",
        "storage": "bind",
    }
    inspection = {
        "Id": "CPU-ID",
        "Image": "CPU-IMAGE",
        "Name": "/" + runtime.container_name(provider.plan, config, "bind"),
        "Config": {
            "Labels": {
                "studio.t09.session": "cpu",
                "studio.t09.plan": "p",
                "studio.t09.owner": "own",
            }
        },
        "HostConfig": {
            "PortBindings": {"8101/tcp": [{"HostIp": "127.0.0.1", "HostPort": "12345"}]}
        },
        "State": {"Running": True, "Pid": 123},
    }

    def execute(argv, **kwargs):
        calls.append((argv, kwargs))
        if argv[:2] == ["docker", "inspect"]:
            out = json.dumps([inspection])
        elif argv[:3] == ["docker", "image", "inspect"]:
            out = "CPU-IMAGE"
        elif argv[:2] == ["docker", "create"]:
            out = "CPU-ID"
        elif argv[:2] == ["docker", "exec"]:
            out = "true"
        else:
            out = "CPU-ACK"
        return SimpleNamespace(returncode=0, stdout=out)

    backend = runtime.DockerBackend(root=tmp_path, execute=execute)
    provider.backend = backend
    monkeypatch.setattr(runtime, "choose_port", lambda: 12345)
    emitted = []

    def call(action, args=None):
        return provider({"operation": action, "arguments": args or {}}, emitted.append)

    folder = tmp_path / "group"
    folder.mkdir()
    assert (
        call("create", {"config": config, "folder": str(folder), "storage": "bind"})[
            "container_id"
        ]
        == "CPU-ID"
    )
    assert (
        call("create", {"config": config, "folder": str(folder), "storage": "bind"})[
            "container_id"
        ]
        == "CPU-ID"
    )
    assert sum(argv[:2] == ["docker", "create"] for argv, _ in calls) == 1
    assert call("attach", {"receipt": receipt}) == receipt
    assert (
        call("recover", {"folder": str(folder), "config": config, "storage": "bind"})
        == receipt
    )
    call("start")
    call("source_check")
    assert backend.image_id("CPU-IMAGE") == "CPU-IMAGE"

    class Api:
        loaded = True

        def request(self, method, path, body=None, **kw):
            if path == "/v1/unload":
                self.loaded = False
                return {"unloaded": True}
            return {
                "state": "idle",
                "loaded": {} if self.loaded else None,
                "job_id": None,
            }

        def events(self, *args, **kwargs):
            return [{"type": "done", "synthetic_cpu": True}]

    provider.api = Api()
    assert call("health")["state"] == "idle"
    assert (
        call(
            "api", {"method": "GET", "path": "/v1/health", "body": None, "timeout": 1}
        )["state"]
        == "idle"
    )
    assert call("events", {"job_id": "cpu", "after": 0, "timeout": 1})[0][
        "synthetic_cpu"
    ]
    assert call("cleanup")["removed"]
    assert call("terminate_owned")["removed"]

    def ollama(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout="NAME SIZE\n")

    provider.ollama = runtime.OllamaState(execute=ollama)
    before = call("ollama_snapshot")
    assert call("ollama_discharge", {"state": before})["discharged"]
    assert call("ollama_restore", {"state": before})["restored"]
    call("lease_acquire")
    call("lease_release")
    with pytest.raises(runtime.ApiError):
        runtime.DockerBackend(
            execute=lambda *a, **kw: SimpleNamespace(returncode=1)
        ).inspect("CPU")
    inspection["Image"] = "foreign"
    with pytest.raises(ValueError, match="image_conflict"):
        backend.recover_create(provider.plan, config, "bind", "own", 12345)
    inspection["Image"] = "CPU-IMAGE"
    inspection["Config"]["Labels"]["studio.t09.owner"] = "FOREIGN"
    with pytest.raises(ValueError):
        call("attach", {"receipt": receipt})
    assert all(argv[0] == "docker" for argv, _ in calls)


def test_actual_legacy_delta_provider_verifies_real_sensor_inventory(
    actual_sensor_factory,
):
    from benchmark_audit import segment_header
    from benchmark_plan import digest
    from benchmark_runtime import BenchmarkOperationProvider

    acquirer, context, root = actual_sensor_factory()
    config = provider_config(root)
    plan = json.loads(Path(config["plan_path"]).read_text())
    plan.update(
        {
            k: context[k]
            for k in ("session_id", "plan_sha256", "image_id", "lock_sha256")
        }
    )
    Path(config["plan_path"]).write_text(json.dumps(plan))
    Path(config["owner_path"]).write_text(
        json.dumps(
            {
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": "own",
            }
        )
    )
    binding = {"root": str(acquirer.root), "context": context, "stream": "CPU-legacy"}
    binding_path = root / "audit-binding.json"
    binding_path.write_text(json.dumps(binding))
    config.update(
        audit_binding_path=str(binding_path), audit_binding_sha256=digest(binding)
    )
    provider = BenchmarkOperationProvider(config)
    emitted = []

    def call(action, args=None):
        return provider({"operation": action, "arguments": args or {}}, emitted.append)

    sample = acquirer.acquire("baseline")
    segment = {
        "receipts": acquirer.receipts,
        "attempts": acquirer.attempts,
        "records": [
            {"sample": sample, "supervisor_receipt": acquirer.previous_receipt}
        ],
    }
    status = call("audit_delta_status")
    header, serialized = segment_header(status, segment)
    call("audit_delta_begin", header)
    for index, offset in enumerate(range(0, len(serialized), 1200)):
        call(
            "audit_delta_fragment",
            {"index": index, "text": serialized[offset : offset + 1200]},
        )
    committed = call("audit_delta_commit")
    assert committed["validated"] == 1
    assert provider.validate_delta(provider.audit_prefix.value, segment) == digest(
        segment
    )
    snapshot = {"root": str(acquirer.root), "context": context, **segment}
    serialized = json.dumps(snapshot)
    call("audit_begin", {"characters": len(serialized), "sha256": digest(snapshot)})
    for index, offset in enumerate(range(0, len(serialized), 1200)):
        call(
            "audit_fragment",
            {"index": index, "text": serialized[offset : offset + 1200]},
        )
    assert call("audit_validate")["validated"] == 1
    assert provider.audit_value["receipts"] == acquirer.receipts
    with pytest.raises(ValueError):
        call("audit_delta_unknown")


def test_session_partial_birth_preserves_primary_and_owns_cleanup(
    actual_sensor_factory, monkeypatch
):
    import benchmark_canonical_integration as integration
    from benchmark_process import decode

    acquirer, _, root = actual_sensor_factory()
    config = decode(acquirer.worker._trusted_config_bytes)
    acquirer.close()
    handler = next(root.rglob("sensor_fixture.py"))
    captured = []
    original = integration.bind_runtime

    def fail(runtime, canonical):
        original(runtime, canonical)
        captured.extend((runtime.worker, canonical.worker, canonical.sensor))
        raise ValueError("own_partial_birth_primary")

    monkeypatch.setattr(integration, "bind_runtime", fail)
    with pytest.raises(ValueError, match="own_partial_birth_primary"):
        integration.create_session(
            root=config["root"],
            context_path=config["context_path"],
            private_root=root / "canonical",
            stream="session",
            sensor_config={},
            operation_config=provider_config(root),
            sensor_handler=f"{handler}:Fixture",
            expected_sources=integration.source_seals(f"{handler}:Fixture"),
        )
    assert len(captured) == 3
    assert all(
        worker.closed and worker.process.poll() is not None for worker in captured
    )
    assert all(worker.close_evidence is not None for worker in captured)


def test_configuration_changed_read_revokes_all_owned_workers(actual_sensor_factory):
    import benchmark_canonical_integration as integration
    from benchmark_process import decode

    acquirer, _, root = actual_sensor_factory()
    config = decode(acquirer.worker._trusted_config_bytes)
    acquirer.close()
    handler = next(root.rglob("sensor_fixture.py"))
    op = provider_config(root)
    session = integration.create_session(
        root=config["root"],
        context_path=config["context_path"],
        private_root=root / "canonical",
        stream="session",
        sensor_config={},
        operation_config=op,
        sensor_handler=f"{handler}:Fixture",
        expected_sources=integration.source_seals(f"{handler}:Fixture"),
    )
    try:
        old = session.read()
        Path(op["owner_path"]).write_text('{"owner":"caller"}')
        with pytest.raises(ValueError, match="configuration_changed"):
            session.read()
        assert all(worker.closed for worker in session.workers), (
            "configuration change retained live authority"
        )
        with pytest.raises(ValueError):
            integration.consume_runtime(session.runtime, old)
    finally:
        session.close()


def test_real_legacy_runtime_delta_and_integrated_internal_reads(actual_sensor_factory):
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_plan import digest
    from benchmark_process import OwnedProcess

    acquirer, context, root = actual_sensor_factory()
    config = provider_config(root)
    plan = {
        k: context[k] for k in ("session_id", "plan_sha256", "image_id", "lock_sha256")
    }
    Path(config["plan_path"]).write_text(json.dumps(plan))
    Path(config["owner_path"]).write_text(
        json.dumps(
            {
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": "CPU",
            }
        )
    )
    binding = {
        "root": str(acquirer.root),
        "context": context,
        "stream": "legacy-session",
    }
    path = root / "binding.json"
    path.write_text(json.dumps(binding))
    config.update(audit_binding_path=str(path), audit_binding_sha256=digest(binding))
    worker = OwnedProcess(config, "benchmark_runtime:BenchmarkOperationProvider")
    coordinator = ContinuousCoordinator(acquirer, interval_s=0.3)
    try:
        coordinator.__enter__()
        channel = RuntimeChannel(coordinator, worker, audit_binding=binding)
        first = channel.audit_publications()
        assert first["validated"] >= 1
        coordinator.wait_samples(1, timeout_s=3)
        second = channel.audit_publications()
        assert second["validated"] > first["validated"]
        assert channel.audit_publications()["validated"] >= second["validated"]
        assert all(item["audit_only"] for item in (first, second))
    finally:
        coordinator.close()
        worker.close()


@pytest.mark.parametrize("xl", [False, True])
def test_actual_legacy_provider_cpu_error_row_not_gpu_acceptance(
    actual_sensor_factory, xl
):
    from benchmark_plan import digest
    from benchmark_runtime import BenchmarkOperationProvider

    acquirer, context, root = actual_sensor_factory()
    provider = BenchmarkOperationProvider(provider_config(root))
    sample = acquirer.acquire("baseline")
    snapshot = {
        "root": str(acquirer.root),
        "context": context,
        "receipts": acquirer.receipts,
        "attempts": acquirer.attempts,
        "records": [
            {"sample": sample, "supervisor_receipt": acquirer.previous_receipt}
        ],
    }
    emitted = []

    def call(action, args):
        return provider({"operation": action, "arguments": args}, emitted.append)

    text = json.dumps(snapshot)
    call("audit_begin", {"characters": len(text), "sha256": digest(snapshot)})
    for index, offset in enumerate(range(0, len(text), 1200)):
        call("audit_fragment", {"index": index, "text": text[offset : offset + 1200]})
    call("audit_validate", {})
    folder = root / "cpu-row"
    folder.mkdir()
    for name, value in {
        "terminal": {
            "type": "error",
            "data": {"code": "VRAM_EXCEEDED" if xl else "CPU_NO_INFERENCE"},
        },
        "request": {},
        "estimate": {},
    }.items():
        (folder / (name + ".json")).write_text(json.dumps(value))

    class Api:
        def request(self, *args, **kwargs):
            return {"gpu": {"cap_mb": 9000}, "synthetic_cpu": True}

    provider.api = Api()
    row = call(
        "row",
        {
            "folder": str(folder),
            "run": {"run_id": "CPU-ERROR"},
            "first_ordinal": 1,
            "last_ordinal": 1,
            "baseline_ordinals": [1],
            "config": {"config_id": "xl-turbo-lm06-int8" if xl else "CPU"},
            "resource_root": "/cpu-no-weights",
            "storage_fields": {"synthetic_cpu": True, "native_gpu": False},
        },
    )
    assert row["valid"] is False and row["native_gpu"] is False
    assert row["status"] == ("hardware_not_feasible" if xl else "error")
    assert (folder / "row.json").exists() and (folder / "seal.json").exists()


@pytest.mark.parametrize("case", ["absent", "foreign", "identity", "owned", "invalid"])
def test_real_recovery_cpu_intent_no_worker_or_external_effects(tmp_path, case):
    from benchmark_runtime import recover_owned_runtime

    owner = {"session_id": "cpu", "plan_sha256": "p", "owner": "own"}
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps(owner))
    intent = {**owner, "pid": os.getpid(), "creation_time": 123, "nonce": "CPU"}
    if case == "invalid":
        intent["owner"] = "foreign"
    intent_path = tmp_path / "intent.json"
    intent_path.write_text(json.dumps(intent))
    lease_path = tmp_path / "lease.json"
    if case not in {"absent", "invalid"}:
        value = {**intent}
        if case == "foreign":
            value["owner"] = "foreign"
        if case == "identity":
            value["nonce"] = "foreign"
        lease_path.write_text(json.dumps(value))
    before = lease_path.read_bytes() if lease_path.exists() else None
    config = {
        "root": str(tmp_path),
        "owner_path": str(owner_path),
        "lease_path": str(lease_path),
        "lease_intent_path": str(intent_path),
    }
    result = recover_owned_runtime(config, None, None, release_lease=True)
    assert result["uncertain"] and result["remote_request_cancelled"] is False
    if case == "owned":
        assert json.loads(lease_path.read_text())["quarantined"]
        assert result["reservation_state"] == "owned_ack_unknown"
    elif before is not None:
        assert lease_path.read_bytes() == before
    else:
        assert not lease_path.exists()


def test_read_binding_and_request_validation_actual_objects(actual_sensor_factory):
    import benchmark_canonical_integration as integration
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_process import OwnedProcess

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    worker = OwnedProcess(
        provider_config(root),
        "benchmark_canonical_integration:_canonical_operation_provider",
    )
    coordinator = ContinuousCoordinator(acquirer, interval_s=0.5)
    try:
        with pytest.raises(ValueError):
            integration.bind_acquirer(object(), canonical)
        integration.bind_acquirer(acquirer, canonical)
        with pytest.raises(ValueError):
            integration.bind_acquirer(acquirer, canonical)
        coordinator.__enter__()
        channel = RuntimeChannel(coordinator, worker)
        with pytest.raises(ValueError):
            integration.read_runtime(channel)
        integration.bind_runtime(channel, canonical)
        with pytest.raises(ValueError):
            integration.bind_runtime(channel, canonical)
        for kind, timeout in (("row", 2), ("status", 0)):
            with pytest.raises(ValueError):
                integration.read_runtime(channel, kind=kind, timeout_s=timeout)
        assert channel._audit_publications().position.kind == "status"
        assert channel._audit_delta().position.kind == "status"
        old = integration.read_runtime(channel)
        worker.close()
        with pytest.raises(ValueError, match="identity_lost"):
            integration.consume_runtime(channel, old)
    finally:
        coordinator.close()
        canonical.close()
        worker.close()


def test_runtime_private_worker_binding_denies_swap_before_effects(
    actual_sensor_factory,
):
    from benchmark_canonical_integration import bind_acquirer, bind_runtime
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_process import OwnedProcess

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    worker = OwnedProcess(
        provider_config(root),
        "benchmark_canonical_integration:_canonical_operation_provider",
    )
    foreign = OwnedProcess(
        provider_config(root), "benchmark_runtime:BenchmarkOperationProvider"
    )
    coordinator = ContinuousCoordinator(acquirer, interval_s=0.5)
    try:
        coordinator.__enter__()
        channel = RuntimeChannel(coordinator, worker)
        bind_runtime(channel, canonical)
        channel.worker = foreign
        error = None
        try:
            channel.write_json(root / "forged-effect.json", {"approved": True})
        except (OSError, ValueError, RuntimeError, KeyError) as caught:
            error = caught
        assert error is not None, "runtime worker swap bypassed private binding"
        assert foreign.seq == 0 and not (root / "forged-effect.json").exists()
    finally:
        coordinator.close()
        canonical.close()
        worker.close()
        foreign.close()


def test_accepted_namespace_does_not_admit_rejected_original(actual_sensor_factory):
    from benchmark_canonical_runtime import CanonicalChannel

    acquirer, _, root = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    try:
        acquirer.acquire("baseline")
        directory = acquirer.root / acquirer.previous_receipt["episode_id"]
        (directory / "rejected.json").write_text('{"status":"caller"}')
        error = None
        try:
            canonical.ingest_latest()
        except (OSError, ValueError, RuntimeError, KeyError) as caught:
            error = caught
        assert error is not None, (
            "accepted attempt admitted reject-only original namespace"
        )
        assert canonical.publication is None and canonical.worker.closed
    finally:
        canonical.close()


def test_eight_real_witnesses_allow_ninth_coordinator_ingest(actual_sensor_factory):
    import threading

    from benchmark_canonical_integration import bind_acquirer, bind_runtime
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_process import OwnedProcess

    acquirer, _, root = actual_sensor_factory()
    fixture = root / "observed_witness.py"
    fixture.write_text(
        """import time,json
from pathlib import Path
from benchmark_canonical_runtime import CanonicalProvider
def factory(config):
    provider=CanonicalProvider(config)
    witness=provider.state._witness
    read=provider.read_steps
    active=[False]
    def observed(registration,deadline):
        result=witness(registration,deadline)
        if active[0]:
            with Path(__file__).with_name("witnesses.jsonl").open("a") as f:
                f.write(json.dumps({"monotonic_ns":time.perf_counter_ns(),"real_witness_completed":True})+"\\n")
            time.sleep(.09)
        return result
    def steps(payload,deadline):
        iterator=read(payload,deadline)
        try:
            while True:
                active[0]=True
                try:value=next(iterator)
                except StopIteration as done:return done.value
                finally:active[0]=False
                yield value
        finally:iterator.close()
    provider.state._witness=observed
    provider.read_steps=steps
    return provider
""",
        encoding="utf-8",
    )
    canonical = CanonicalChannel(
        acquirer.worker,
        private_root=root / "canonical",
        stream="session",
        trusted_handler=f"{fixture}:factory",
    )
    bind_acquirer(acquirer, canonical)
    worker = OwnedProcess(
        provider_config(root),
        "benchmark_canonical_integration:_canonical_operation_provider",
    )
    coordinator = ContinuousCoordinator(acquirer, interval_s=0.3)
    values, errors = [], []
    reader = None
    try:
        coordinator.__enter__()
        coordinator.wait_samples(7, timeout_s=6)
        with coordinator.condition:
            assert len(coordinator.records) == 8
        channel = RuntimeChannel(coordinator, worker)
        bind_runtime(channel, canonical)

        def read():
            try:
                values.append(channel.audit_publications())
            except (OSError, ValueError, RuntimeError, KeyError) as error:
                errors.append(error)

        reader = threading.Thread(target=read)
        reader.start()
        deadline = time.monotonic() + 2
        witness_path = root / "witnesses.jsonl"
        while not witness_path.exists() and time.monotonic() < deadline:
            time.sleep(0.002)
        assert witness_path.exists()
        coordinator.set_phase("readiness")
        with coordinator.condition:
            while len(coordinator.records) < 9:
                coordinator.check()
                remaining = deadline - time.monotonic()
                assert remaining > 0
                coordinator.condition.wait(remaining)
            assert coordinator.records[8]["supervisor_receipt"]["ordinal"] == 9
            assert reader.is_alive(), "ninth ingest waited for complete prefix read"
        reader.join(timeout=2)
        assert not errors and not reader.is_alive()
        assert values[0].position.cursor == 8
        assert len(witness_path.read_text().splitlines()) == 8
        assert worker.seq == 0
        assert canonical.binding["stream"] == "session"
    finally:
        coordinator.close()
        canonical.close()
        worker.close()
        if reader is not None:
            reader.join(timeout=2)


def test_actual_sensor_eof_after_acceptance_removes_positive_publication(
    actual_sensor_factory,
):
    from benchmark_canonical_integration import bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_process import WorkerFailure

    acquirer, _, root = actual_sensor_factory(exit_second=True)
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    try:
        acquirer.acquire("baseline")
        old = canonical.request_view(deadline_ns=time.perf_counter_ns() + 2_000_000_000)
        raw_before = {
            str(path): path.read_bytes() for path in acquirer.root.rglob("raw-*.json")
        }
        with pytest.raises(WorkerFailure, match="eof"):
            acquirer.acquire("readiness")
        assert len(acquirer.receipts) == 1 and acquirer.previous_receipt is None
        assert acquirer.attempts[-1]["status"] == "interrupted"
        assert canonical.publication is None, (
            "EOF retained previous positive publication head"
        )
        assert canonical.worker.closed
        with pytest.raises(ValueError):
            canonical._resolve_position(old)
        assert all(Path(path).read_bytes() == data for path, data in raw_before.items())
    finally:
        canonical.close()


@pytest.mark.parametrize("recording_fault", ["none", "record", "safe_record"])
def test_firstcause_canonical_cleanup_recording_keeps_native_primary(
    actual_sensor_factory, monkeypatch, recording_fault
):
    """Fallos controlados tras ingesta real; no fallo espontáneo del kernel."""
    import benchmark_coordinator as coordinator
    from benchmark_canonical_integration import CanonicalSession, bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_process import WorkerFailure

    class PrimaryFailure(WorkerFailure):
        pass

    acquirer, _, root = actual_sensor_factory()
    foreign, _, _ = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    session = CanonicalSession()
    session.acquirer, session.canonical = acquirer, canonical
    # Strong references precede faults and remain owned through assertion/rescue.
    workers = session.workers
    native_refs = tuple((w, w.process, w.job, w.reader) for w in workers)
    foreign_birth = dict(foreign.worker.ownership)
    primary = PrimaryFailure("controlled_canonical_ingest_primary")
    calls = []
    original_ingest = canonical.ingest_latest
    original_terminate = canonical.worker.job.terminate
    original_sensor_close = acquirer.worker.close
    original_record = coordinator.cleanup_error_record
    original_safe = coordinator.safe_cleanup_error_record
    primary_traceback = []

    def ingest_failure():
        result = original_ingest()
        assert result and canonical.publication is not None
        assert all(w.reader.is_alive() for w in workers)
        calls.append(("ingest", time.perf_counter_ns()))
        try:
            raise primary
        except PrimaryFailure:
            primary_traceback.append(primary.__traceback__)
            raise

    def terminate_failure():
        calls.append(("canonical_job_terminate", time.perf_counter_ns()))
        original_terminate()
        raise OSError("controlled_canonical_job_termination_error")

    def record_failure(error):
        calls.append(("record", time.perf_counter_ns(), type(error).__name__))
        raise OSError("controlled_secondary_record_io_error")

    def sensor_close(**kwargs):
        calls.append(("sensor_close", time.perf_counter_ns()))
        return original_sensor_close(**kwargs)

    monkeypatch.setattr(canonical, "ingest_latest", ingest_failure)
    monkeypatch.setattr(canonical.worker.job, "terminate", terminate_failure)
    monkeypatch.setattr(acquirer.worker, "close", sensor_close)
    if recording_fault == "record":
        monkeypatch.setattr(coordinator, "cleanup_error_record", record_failure)
    elif recording_fault == "safe_record":
        monkeypatch.setattr(coordinator, "safe_cleanup_error_record", record_failure)
    try:
        with pytest.raises(BaseException) as caught:
            acquirer.acquire("controlled-firstcause-canonical")
        (root / "firstcause-before-rescue.json").write_text(
            json.dumps(
                {
                    "controlled_faults": True,
                    "recording_fault": recording_fault,
                    "calls": calls,
                    "caught_type": type(caught.value).__name__,
                    "primary_identity_preserved": caught.value is primary,
                    "native": [
                        {
                            "ownership": w.ownership,
                            "closed": w.closed,
                            "exit": p.poll(),
                            "reader_alive": r.is_alive(),
                            "cleanup": w.close_evidence,
                        }
                        for w, p, _, r in native_refs
                    ],
                    "interrupted": acquirer.last_interrupted,
                    "foreign_alive": foreign.worker.process.poll() is None,
                }
            ),
            encoding="utf-8",
        )
        # Assertions happen BEFORE any rescue of the original native references.
        assert caught.value is primary, (
            "secondary recording replaced canonical ingestion primary"
        )
        assert type(caught.value) is PrimaryFailure
        traceback = caught.value.__traceback__
        while traceback is not primary_traceback[0] and traceback is not None:
            traceback = traceback.tb_next
        assert traceback is primary_traceback[0]
        assert [c[0] for c in calls].count("sensor_close") == 1
        if recording_fault != "none":
            assert [c[0] for c in calls].count("record") == 1
        assert acquirer.attempts[-1]["status"] == "interrupted"
        assert acquirer.last_interrupted is acquirer.attempts[-1]["interrupted"]
        assert acquirer.receipts == [] and acquirer.previous_receipt is None
        assert acquirer.last_record is None and canonical.publication is None
        assert canonical.positions == {} and canonical.last_receipt is None
        evidence = canonical.worker.close_evidence
        assert evidence["resources_returned"] is False
        assert evidence["disposition"] == "UNKNOWN_QUARANTINED"
        secondary = primary.evidence["canonical_cleanup_error"]
        assert secondary["type"] == "WorkerFailure"
        if recording_fault != "none":
            assert secondary["message_sha256"] is None
            assert secondary["observed"] is None
        assert acquirer.worker.close_evidence is not None
        assert all(w.closed and p.poll() is not None for w, p, _, _ in native_refs)
        assert foreign.worker.process.poll() is None
        assert foreign.worker.job.evidence(foreign.worker.process) == foreign_birth
        assert foreign.worker.seq == 0
    finally:
        monkeypatch.setattr(canonical, "ingest_latest", original_ingest)
        monkeypatch.setattr(canonical.worker.job, "terminate", original_terminate)
        monkeypatch.setattr(acquirer.worker, "close", original_sensor_close)
        monkeypatch.setattr(coordinator, "cleanup_error_record", original_record)
        monkeypatch.setattr(coordinator, "safe_cleanup_error_record", original_safe)
        session.close()
        foreign.close()
        assert all(
            p.poll() is not None and not r.is_alive() for _, p, _, r in native_refs
        )


@pytest.mark.parametrize("frontier", ["observation", "begin"])
@pytest.mark.parametrize(
    "recording_fault", ["none", "record", "safe_record", "storage"]
)
def test_firstcause_inside_real_canonical_ingest_keeps_primary(
    actual_sensor_factory, monkeypatch, frontier, recording_fault
):
    """Ingesta real y Jobs reales; fallos secundarios controlados antes del rescate."""
    import benchmark_coordinator as coordinator
    from benchmark_canonical_integration import CanonicalSession, bind_acquirer
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_process import WorkerFailure

    class PrimaryFailure(WorkerFailure):
        pass

    class FailingRecords(list):
        def append(self, record):
            raise OSError("controlled_record_storage_failure")

    acquirer, _, root = actual_sensor_factory()
    foreign, _, _ = actual_sensor_factory()
    canonical = CanonicalChannel(
        acquirer.worker, private_root=root / "canonical", stream="session"
    )
    bind_acquirer(acquirer, canonical)
    session = CanonicalSession()
    session.acquirer, session.canonical = acquirer, canonical
    workers = session.workers
    native_refs = tuple((w, w.process, w.job, w.reader) for w in workers)
    foreign_birth = dict(foreign.worker.ownership)
    primary = PrimaryFailure("controlled_inside_ingest_primary")
    primary_traceback, calls = [], []
    original_evidence = acquirer.worker.job.evidence
    original_call = canonical.worker.call
    original_terminate = canonical.worker.job.terminate
    original_record = coordinator.cleanup_error_record
    original_safe = coordinator.safe_cleanup_error_record
    original_records = canonical.cleanup_errors

    def fail_primary():
        assert all(w.reader.is_alive() for w in workers)
        try:
            raise primary
        except PrimaryFailure:
            primary_traceback.append(primary.__traceback__)
            raise

    def evidence(process):
        value = original_evidence(process)
        # Constructor evidence and sensor acquisition remain real and intact.
        import inspect

        if inspect.currentframe().f_back.f_code.co_name == "_ingest_latest":
            assert value == acquirer.worker.ownership
            calls.append("observation")
            fail_primary()
        return value

    def begin(payload, **kwargs):
        value = original_call(payload, **kwargs)
        assert payload["operation"] == "begin"
        calls.append("begin")
        fail_primary()
        return value

    def terminate():
        calls.append("terminate")
        original_terminate()
        raise OSError("controlled_native_termination_failure")

    def record(error):
        calls.append("record")
        raise OSError("controlled_secondary_record_failure")

    if frontier == "observation":
        monkeypatch.setattr(acquirer.worker.job, "evidence", evidence)
    else:
        monkeypatch.setattr(canonical.worker, "call", begin)
    monkeypatch.setattr(canonical.worker.job, "terminate", terminate)
    if recording_fault == "record":
        monkeypatch.setattr(coordinator, "cleanup_error_record", record)
    elif recording_fault == "safe_record":
        monkeypatch.setattr(coordinator, "safe_cleanup_error_record", record)
    elif recording_fault == "storage":
        canonical.cleanup_errors = FailingRecords()
    try:
        with pytest.raises(BaseException) as caught:
            acquirer.acquire("inside-firstcause")
        (root / "inside-firstcause-before-rescue.json").write_text(
            json.dumps(
                {
                    "frontier": frontier,
                    "recording_fault": recording_fault,
                    "caught_type": type(caught.value).__name__,
                    "primary_identity": caught.value is primary,
                    "calls": calls,
                    "traceback": [
                        {
                            "file": frame.filename,
                            "line": frame.lineno,
                            "name": frame.name,
                        }
                        for frame in __import__("traceback").extract_tb(
                            caught.value.__traceback__
                        )
                    ],
                    "native": [
                        {
                            "ownership": w.ownership,
                            "worker_ref": id(w),
                            "process_ref": id(p),
                            "job_ref": id(j),
                            "reader_ref": id(r),
                            "exit": p.poll(),
                            "reader_alive": r.is_alive(),
                            "cleanup": w.close_evidence,
                        }
                        for w, p, j, r in native_refs
                    ],
                    "foreign_alive": foreign.worker.process.poll() is None,
                    "foreign_birth": foreign.worker.job.evidence(
                        foreign.worker.process
                    ),
                    "interrupted": acquirer.last_interrupted,
                }
            ),
            encoding="utf-8",
        )
        assert caught.value is primary, "inner cleanup recording replaced primary"
        assert type(caught.value) is PrimaryFailure
        trace = caught.value.__traceback__
        while trace is not None and trace is not primary_traceback[0]:
            trace = trace.tb_next
        assert trace is primary_traceback[0]
        assert calls.count(frontier) == 1 and calls.count("terminate") == 1
        assert acquirer.attempts[-1]["status"] == "interrupted"
        assert acquirer.receipts == [] and acquirer.previous_receipt is None
        assert acquirer.last_record is None and canonical.publication is None
        assert canonical.positions == {} and canonical.last_receipt is None
        assert canonical.worker.close_evidence["resources_returned"] is False
        assert canonical.worker.close_evidence["disposition"] == "UNKNOWN_QUARANTINED"
        if recording_fault != "storage":
            assert len(canonical.cleanup_errors) == 1
            secondary = canonical.cleanup_errors[0]
            assert secondary["type"] == "WorkerFailure"
            if recording_fault in {"record", "safe_record"}:
                assert secondary["message_sha256"] is None
                assert secondary["observed"] is None
        assert all(w.closed and p.poll() is not None for w, p, _, _ in native_refs)
        assert foreign.worker.process.poll() is None
        assert foreign.worker.job.evidence(foreign.worker.process) == foreign_birth
        assert foreign.worker.seq == 0
    finally:
        monkeypatch.setattr(acquirer.worker.job, "evidence", original_evidence)
        monkeypatch.setattr(canonical.worker, "call", original_call)
        monkeypatch.setattr(canonical.worker.job, "terminate", original_terminate)
        monkeypatch.setattr(coordinator, "cleanup_error_record", original_record)
        monkeypatch.setattr(coordinator, "safe_cleanup_error_record", original_safe)
        canonical.cleanup_errors = original_records
        session.close()
        foreign.close()
        assert all(
            p.poll() is not None and not r.is_alive() for _, p, _, r in native_refs
        )
