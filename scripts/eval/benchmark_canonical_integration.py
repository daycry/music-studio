"""Corte opt-in: asociaciones del supervisor por identidad privada."""

import hashlib
import json
import secrets
import time
import weakref
from dataclasses import dataclass
from pathlib import Path

_ACQUIRERS = weakref.WeakKeyDictionary()
_PROVIDERS = weakref.WeakSet()
_RUNTIMES = weakref.WeakKeyDictionary()
_SESSIONS = weakref.WeakKeyDictionary()


def source_seals(sensor_handler="benchmark_episode:EpisodeProvider"):
    """Inventory for trusted supervisor configuration, never caller approval."""
    import importlib.util

    from benchmark_episode import confined

    name = sensor_handler.rsplit(":", 1)[0]
    handler = (
        Path(name)
        if name.endswith(".py")
        else Path(importlib.util.find_spec(name).origin)
    )
    repo = Path(__file__).resolve().parents[2]
    paths = list((repo / "scripts/eval").glob("*.py"))
    paths += [
        confined(handler),
        repo / "scripts/env.ps1",
        repo / "pyproject.toml",
        repo / "uv.lock",
    ]
    return {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def _check_sources(session):
    if source_seals(session._sensor_handler) != session._sources:
        raise ValueError("canonical_effective_sources_changed")
    for path, data in session._configuration:
        if Path(path).read_bytes() != data:
            raise ValueError("canonical_trusted_configuration_changed")


class CanonicalSession:
    """Own only resources born here; raw files survive all revocations."""

    def __init__(self):
        self.acquirer = self.canonical = self.coordinator = None
        self.operation_worker = self.runtime = None
        self.cleanup_errors = []
        self.closed = False

    @property
    def workers(self):
        return tuple(
            w
            for w in (
                self.acquirer.worker if self.acquirer else None,
                self.canonical.worker if self.canonical else None,
                self.operation_worker,
            )
            if w is not None
        )

    def read(self, *, kind="status", timeout_s=2, consumer=None):
        if self.closed:
            raise ValueError("canonical_session_closed")
        return read_runtime(
            self.runtime, kind=kind, timeout_s=timeout_s, consumer=consumer
        )

    def close(self):
        if self.closed:
            return
        self.closed = True
        errors = []
        for resource in (
            self.coordinator,
            self.canonical,
            self.acquirer,
            self.operation_worker,
        ):
            if resource is not None:
                try:
                    resource.close()
                except BaseException as error:  # noqa: BLE001 - cleanup must preserve primary even on interruption
                    from benchmark_coordinator import cleanup_error_record

                    self.cleanup_errors.append(cleanup_error_record(error))
                    errors.append(error)
        if self.runtime in _RUNTIMES:
            _RUNTIMES[self.runtime]["view"] = None
        if errors:
            raise errors[0]

    def __enter__(self):
        if self.closed:
            raise ValueError("canonical_session_closed")
        return self

    def __exit__(self, kind, value, traceback):
        try:
            self.close()
        except BaseException:
            if kind is None:
                raise


def create_session(
    *,
    root,
    context_path,
    private_root,
    stream,
    sensor_config,
    operation_config,
    expected_sources,
    sensor_handler="benchmark_episode:EpisodeProvider",
    interval_s=1,
    startup_timeout_s=15,
):
    """Code-trusted opt-in factory; never called by benchmark.py or JSON RPC."""
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_episode import EpisodeAcquirer, confined
    from benchmark_process import OwnedProcess, decode, encode

    if not isinstance(stream, str) or not stream or startup_timeout_s <= 0:
        raise ValueError("canonical_session_configuration_invalid")
    session = CanonicalSession()
    session._sensor_handler = sensor_handler
    session._sources = dict(expected_sources)
    # Immutable bytes before ANY birth; config is not an authority marker.
    operation_config = decode(encode(operation_config))
    sensor_config = decode(encode(sensor_config))
    paths = [
        confined(context_path),
        confined(operation_config["plan_path"]),
        confined(operation_config["owner_path"]),
    ]
    session._configuration = tuple((str(path), path.read_bytes()) for path in paths)
    _check_sources(session)
    plan = json.loads(session._configuration[1][1])
    for relative, expected in plan.get("source_hashes", {}).items():
        path = confined(Path(operation_config["root"]) / relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("canonical_plan_source_changed")
    deadline = time.perf_counter_ns() + int(startup_timeout_s * 1e9)

    def remaining():
        left = (deadline - time.perf_counter_ns()) / 1e9
        if left <= 0:
            raise TimeoutError("canonical_total_bootstrap_deadline")
        _check_sources(session)
        return min(5, left)

    try:
        session.acquirer = EpisodeAcquirer(
            root=root,
            context_path=context_path,
            sensor_config=sensor_config,
            trusted_handler=sensor_handler,
            startup_timeout_s=remaining(),
        )
        remaining()
        session.canonical = CanonicalChannel(
            session.acquirer.worker, private_root=private_root, stream=stream
        )
        remaining()
        bind_acquirer(session.acquirer, session.canonical)
        session.coordinator = ContinuousCoordinator(
            session.acquirer, interval_s=interval_s
        )
        session.operation_worker = OwnedProcess(
            operation_config,
            "benchmark_canonical_integration:_canonical_operation_provider",
            startup_timeout_s=remaining(),
        )
        remaining()
        session.coordinator.__enter__()
        remaining()
        session.runtime = RuntimeChannel(session.coordinator, session.operation_worker)
        bind_runtime(session.runtime, session.canonical)
        _SESSIONS[session.runtime] = session
        canonical_for_runtime(session.runtime)
        return session
    except BaseException:
        try:
            session.close()
        except BaseException as cleanup:  # noqa: BLE001 - retain secondary cleanup without masking birth failure
            from benchmark_coordinator import cleanup_error_record

            session.cleanup_errors.append(cleanup_error_record(cleanup))
        raise


def bind_runtime(runtime, canonical):
    from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
    from benchmark_process import OwnedProcess

    if (
        type(runtime) is not RuntimeChannel
        or type(runtime.coordinator) is not ContinuousCoordinator
        or type(runtime.worker) is not OwnedProcess
        or canonical_for_acquirer(runtime.coordinator.acquirer) is not canonical
        or runtime in _RUNTIMES
    ):
        raise ValueError("canonical_real_runtime_binding_required")
    _RUNTIMES[runtime] = {
        "canonical": canonical,
        "coordinator": runtime.coordinator,
        "worker": runtime.worker,
        "ownership": dict(runtime.worker.ownership),
        "view": None,
        "consumer": None,
        "request": None,
    }


def canonical_for_runtime(runtime):
    binding = _RUNTIMES.get(runtime)
    if binding is None:
        return None
    session = _SESSIONS.get(runtime)
    if session is not None:
        if session.closed:
            raise ValueError("canonical_session_closed")
        try:
            _check_sources(session)
        except BaseException:
            binding["view"] = None
            try:
                session.close()
            except BaseException as cleanup:  # noqa: BLE001 - original seal failure remains primary
                from benchmark_coordinator import cleanup_error_record

                session.cleanup_errors.append(cleanup_error_record(cleanup))
            raise
    worker = binding["worker"]
    canonical = binding["canonical"]
    if (
        runtime.worker is not worker
        or runtime.coordinator is not binding["coordinator"]
        or canonical_for_acquirer(runtime.coordinator.acquirer) is not canonical
        or worker.closed
        or canonical.worker.closed
        or canonical.sensor.closed
        or worker.job.evidence(worker.process) != binding["ownership"]
        or canonical.sensor.job.evidence(canonical.sensor.process)
        != canonical.binding["sensor"]
        or canonical.worker.job.evidence(canonical.worker.process)
        != canonical.worker.ownership
    ):
        binding["view"] = None
        raise ValueError("canonical_session_identity_lost")
    return canonical


@dataclass(frozen=True, eq=False)
class CanonicalRead:
    position: object
    request_id: str


def read_runtime(runtime, *, kind="status", timeout_s=2, consumer=None):
    canonical = canonical_for_runtime(runtime)
    if canonical is None:
        raise ValueError("canonical_runtime_unbound")
    if kind not in {"status", "base"} or timeout_s <= 0:
        raise ValueError("canonical_read_request_invalid")
    binding = _RUNTIMES[runtime]
    binding["view"] = None
    request_id = secrets.token_hex(16)
    position = canonical.request_view(
        kind=kind, deadline_ns=time.perf_counter_ns() + int(timeout_s * 1e9)
    )
    canonical_for_runtime(runtime)
    canonical._resolve_position(position)
    view = CanonicalRead(position, request_id)
    binding.update(
        view=view,
        request=request_id,
        consumer=runtime if consumer is None else consumer,
    )
    return view


def consume_runtime(runtime, view, *, consumer=None, timeout_s=2):
    canonical = canonical_for_runtime(runtime)
    binding = _RUNTIMES.get(runtime)
    owner = runtime if consumer is None else consumer
    if (
        canonical is None
        or type(view) is not CanonicalRead
        or binding["view"] is not view
        or binding["request"] != view.request_id
        or binding["consumer"] is not owner
    ):
        raise ValueError("canonical_foreign_or_stale_read")
    canonical._resolve_position(view.position)
    # Identity grants only a new request; it never skips independent accreditation.
    return read_runtime(
        runtime, kind=view.position.kind, timeout_s=timeout_s, consumer=owner
    )


def bind_acquirer(acquirer, canonical):
    from benchmark_canonical_runtime import CanonicalChannel
    from benchmark_episode import EpisodeAcquirer

    if type(acquirer) is not EpisodeAcquirer or type(canonical) is not CanonicalChannel:
        raise ValueError("canonical_real_acquirer_channel_required")
    if canonical.sensor is not acquirer.worker or acquirer in _ACQUIRERS:
        raise ValueError("canonical_acquirer_identity_changed")
    _ACQUIRERS[acquirer] = canonical


def canonical_for_acquirer(acquirer):
    canonical = _ACQUIRERS.get(acquirer)
    if canonical is not None and canonical.sensor is not acquirer.worker:
        raise ValueError("canonical_acquirer_identity_changed")
    return canonical


def _closed_operation(action):
    return action in {
        "audit_begin",
        "audit_fragment",
        "audit_validate",
        "calibration_export",
        "accreditation",
        "refresh_accreditation",
        "row",
    } or action.startswith("audit_delta_")


def guard_runtime_operation(runtime, action, arguments):
    if canonical_for_runtime(runtime) is None:
        return
    indirect = arguments.get("action") if action == "args_begin" else None
    if _closed_operation(action) or (
        indirect is not None and _closed_operation(indirect)
    ):
        raise ValueError("canonical_consumer_not_migrated")


def guard_provider(provider, payload):
    if provider not in _PROVIDERS:
        return
    action = payload["operation"]
    indirect = (
        payload.get("arguments", {}).get("action") if action == "args_begin" else None
    )
    pending = (
        getattr(provider, "arguments_header", {}).get("action")
        if action in {"args_fragment", "args_execute"}
        else None
    )
    if any(
        _closed_operation(value)
        for value in (action, indirect, pending)
        if value is not None
    ):
        raise ValueError("canonical_consumer_not_migrated")


def _canonical_operation_provider(config):
    from benchmark_runtime import BenchmarkOperationProvider

    # No legacy audit state in the long worker, including constructor bootstrap.
    config = {
        key: value
        for key, value in config.items()
        if key not in {"audit_binding_path", "audit_binding_sha256"}
    }
    provider = BenchmarkOperationProvider(config)
    _PROVIDERS.add(provider)
    return provider
