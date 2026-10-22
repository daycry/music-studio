"""Cadencia v3 continua; un sampler y operaciones en procesos propios.

El sampler es el único consumidor de EpisodeAcquirer. No hace I/O de auditoría
en el padre. Recibos e inventario se copian al regresar cada adquisición,
incluido el último recibo que aún no tiene audit en el hijo. Cada operación
corre en OwnedProcess; fallo del sampler termina su Job sin cerrar sus pipes
desde otro hilo. El llamador de call recoge EOF y hace cleanup/join del lector.
No puede cancelar acciones ya entregadas a Docker: se conserva incertidumbre
y se reconcilia ownership antes de cualquier nueva creación/envío.
"""

import copy
import hashlib
import json
import threading
import time
from contextlib import contextmanager

from benchmark_episode import clock
from benchmark_process import OwnedProcess, WorkerFailure
from benchmark_startup import StartupBudget

_STARTUP_QUARANTINE = set()


@contextmanager
def _budget_condition(condition, budget):
    if not condition.acquire(timeout=budget.remaining_s()):
        raise TimeoutError("startup_condition_deadline")
    try:
        budget.check()
        yield
    finally:
        condition.release()


def cleanup_error_record(error):
    """Custodia secundaria sin publicar mensajes con credenciales o rutas."""
    # No ejecutar __str__ arbitrario ni conservar mensajes sin cota.
    args = BaseException.args.__get__(error)
    message = args[0][:4096] if args and type(args[0]) is str else ""
    return {
        "type": type(error).__name__[:128],
        "message_sha256": hashlib.sha256(
            message.encode("utf-8", errors="replace")
        ).hexdigest(),
        "observed": clock(),
    }


def safe_cleanup_error_record(error):
    """El fallo de custodia secundaria tampoco puede sustituir la primera causa."""
    record = {
        "type": type(error).__name__[:128],
        "message_sha256": None,
        "observed": None,
    }
    try:
        return cleanup_error_record(error)
    except BaseException:  # noqa: BLE001 - el registro es secundario; identidad tipada y tiempos UNKNOWN
        return record


class ContinuousCoordinator:
    observation_method = "wddm_auto_v3"

    def __init__(self, acquirer, *, interval_s=1, startup_deadline_ns=None):
        if startup_deadline_ns is not None:
            StartupBudget(startup_deadline_ns)
        self._startup_deadline_ns = startup_deadline_ns
        self._startup_cleanup_thread = None
        if acquirer.observation_method != self.observation_method:
            raise ValueError("v3_acquirer_required")
        if not 0 < interval_s <= 2.5:
            raise ValueError("v3_cadence_invalid")
        self.acquirer = acquirer
        self.observation_context = acquirer.observation_context
        self.interval_s = interval_s
        self.condition = threading.Condition()
        self._startup_notification = threading.Event()
        self.stop = threading.Event()
        self.failure = None
        self.receipts = []
        self.attempts = []
        self.records = []
        self.events = []
        self.transitions = []
        self.phase = {"name": "startup", "idle": False, "started": clock()}
        self.active = None
        self.started = False
        self.sampler = threading.Thread(
            target=self._sample, name="t09-v3-continuous-sampler", daemon=False
        )

    def __enter__(self):
        budget = StartupBudget.from_timeout(2.5, deadline_ns=self._startup_deadline_ns)
        self._startup_budget = budget
        try:
            with _budget_condition(self.condition, budget):
                if self.started or self.stop.is_set():
                    raise RuntimeError("v3_coordinator_cannot_restart")
                self.sampler.start()
                self.started = True
            while True:
                with _budget_condition(self.condition, budget):
                    self.check()
                    if self.records:
                        budget.check()
                        break
                remaining = budget.remaining_s()
                if remaining <= 0:
                    raise TimeoutError("v3_startup_samples_timeout")
                # Condition.wait reacquiere RLock sin cota. Este evento sólo
                # despierta: la autoridad se revalida con acquire acotado.
                self._startup_notification.wait(min(0.01, remaining))
                self._startup_notification.clear()
        except BaseException:
            self.stop.set()
            _STARTUP_QUARANTINE.add(self)

            def clean():
                try:
                    self.close()
                except BaseException as cleanup:  # noqa: BLE001 - preservar primera causa
                    self.events.append(
                        {"cleanup_error": safe_cleanup_error_record(cleanup)}
                    )

            self._startup_cleanup_thread = threading.Thread(
                target=clean, name="coordinator-startup-cleanup"
            )
            self._startup_cleanup_thread.start()
            self._startup_cleanup_thread.join(timeout=budget.remaining_s())
            raise
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            self.close()
        else:
            try:
                self.close()
            except BaseException as cleanup:  # noqa: BLE001 - preservar la excepción del cuerpo
                try:
                    self.events.append(
                        {"cleanup_error": safe_cleanup_error_record(cleanup)}
                    )
                except BaseException:  # noqa: BLE001,S110 - ni el almacenamiento sustituye la primera causa
                    pass
        if kind is None and self.failure is not None:
            raise RuntimeError("v3_continuous_observation_failed") from self.failure

    def check(self):
        with self.condition:
            if self.failure is not None:
                raise RuntimeError("v3_continuous_observation_failed") from self.failure
            if not self.started or self.stop.is_set():
                raise RuntimeError("v3_coordinator_not_running")

    def set_phase(self, name, *, idle=False, started=None):
        if not isinstance(name, str) or not name or type(idle) is not bool:
            raise ValueError("v3_phase_invalid")
        with self.condition:
            self.check()
            self.phase = {"name": name, "idle": idle, "started": started or clock()}
            self.transitions.append(copy.deepcopy(self.phase))
            self.condition.notify_all()
            self._startup_notification.set()

    def _custody(self, phase, sample=None):
        # El sampler es el único escritor; custodia independiente del proveedor.
        with self.condition:
            self.receipts.extend(
                copy.deepcopy(self.acquirer.receipts[len(self.receipts) :])
            )
            self.attempts.extend(
                copy.deepcopy(self.acquirer.attempts[len(self.attempts) :])
            )
            if sample is not None:
                self.records.append(
                    {
                        "phase": phase["name"],
                        "phase_started": phase["started"],
                        "idle": phase["idle"],
                        "sample": copy.deepcopy(sample),
                        "supervisor_receipt": copy.deepcopy(
                            self.acquirer.previous_receipt
                        ),
                    }
                )
            self.condition.notify_all()

    def _fail(self, error):
        with self.condition:
            if self.failure is None:
                self.failure = error
            else:
                self.events.append({"cleanup_error": str(error), "observed": clock()})
            # Evitar close simultáneo con call: terminar únicamente el Job.
            if self.active is not None and self.active.job is not None:
                try:
                    self.active.job.terminate()
                except (OSError, RuntimeError, ValueError) as cleanup:
                    self.events.append(
                        {"cleanup_error": str(cleanup), "observed": clock()}
                    )
            self.stop.set()
            self._startup_notification.set()
            self.condition.notify_all()

    def _sample(self):
        previous_start = None
        try:
            while not self.stop.is_set():
                started = time.perf_counter_ns()
                if (
                    previous_start is not None
                    and started - previous_start > 2_500_000_000
                ):
                    raise WorkerFailure("v3_sampler_cadence_lost")
                previous_start = started
                with self.condition:
                    phase = copy.deepcopy(self.phase)
                self.acquirer.phase_started_utc = (
                    None if phase["name"] == "baseline" else phase["started"]["utc"]
                )
                try:
                    sample = self.acquirer.acquire(phase["name"], idle=phase["idle"])
                except BaseException:
                    self._custody(phase)
                    raise
                self._custody(phase, sample)
                self.stop.wait(
                    max(0, self.interval_s - (time.perf_counter_ns() - started) / 1e9)
                )
        except (Exception, KeyboardInterrupt, SystemExit) as error:  # noqa: BLE001 - frontera del sampler: todo fallo cancela el Job propio
            self._fail(error)
        finally:
            try:
                self.acquirer.close()
            except (Exception, KeyboardInterrupt, SystemExit) as error:  # noqa: BLE001 - preservar fallo de cleanup y despertar al propietario
                self._fail(error)

    def wait_samples(self, count, *, timeout_s=30):
        if type(count) is not int or count < 1 or timeout_s <= 0:
            raise ValueError("v3_wait_invalid")
        with self.condition:
            # Esperar count registros nuevos sobre la misma cadencia.
            target = len(self.records) + count
            deadline = time.monotonic() + timeout_s
            while len(self.records) < target:
                self.check()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("v3_samples_wait_timeout")
                self.condition.wait(remaining)
            self.check()
            return copy.deepcopy(self.records[-count:])

    def run_owned(self, phase, worker, payload, *, timeout_s, idle=False):
        if timeout_s <= 0:
            raise ValueError("v3_operation_timeout_invalid")
        self.set_phase(phase, idle=idle)
        event = {
            "phase": phase,
            "started": clock(),
            "ownership": copy.deepcopy(worker.ownership),
            "operation": payload["operation"],
        }
        with self.condition:
            self.check()
            self._reconcile_active()
            if self.active is not None:
                raise RuntimeError("v3_parallel_operation_forbidden")
            self.active = worker
        try:
            result = worker.call(
                payload, deadline_ns=time.perf_counter_ns() + int(timeout_s * 1e9)
            )
            self.check()
            event["result_observed"] = clock()
            return result
        except BaseException as error:
            event["error"] = str(error)
            event["progress"] = copy.deepcopy(getattr(error, "progress", []))
            event["evidence"] = copy.deepcopy(getattr(error, "evidence", {}))
            if payload["operation"] == "create" or (
                payload["operation"] == "api"
                and payload["arguments"].get("method") == "POST"
            ):
                event["remote_action_uncertain"] = True
                event["recovery_action"] = "reconcile_owned_identity_without_replay"
            # El llamador propietario cierra sus pipes; el sampler termina el Job.
            try:
                worker.close(graceful=False)
            except BaseException as cleanup:  # noqa: BLE001 - preservar primera causa y custodiar fallo secundario
                event["cleanup_error"] = cleanup_error_record(cleanup)
            raise
        finally:
            with self.condition:
                if self.active is worker and worker._custody_resolved():
                    self.active = None
                event["finished"] = clock()
                event["sampler_failed"] = self.failure is not None
                self.events.append(event)

    def _reconcile_active(self):
        # Sólo la custodia propia puede acreditar sus joins y cierre real.
        # Se llama bajo condition; el guard de fallo sigue siendo anterior.
        if (
            isinstance(self.active, OwnedProcess)
            and getattr(self.active, "closed", False)
            and self.active._custody_resolved()
        ):
            self.active = None

    def collect_phase(self, name, count=10, *, idle=False, started=None, timeout_s=30):
        self.set_phase(name, idle=idle, started=started)
        with self.condition:
            marker = copy.deepcopy(self.phase["started"])
            deadline = time.monotonic() + timeout_s
            while True:
                self.check()
                selected = [
                    r
                    for r in self.records
                    if r["phase"] == name and r["phase_started"] == marker
                ]
                if len(selected) >= count:
                    return copy.deepcopy(selected[:count])
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("v3_phase_samples_timeout")
                self.condition.wait(remaining)

    def close(self, *, raise_failure=False):
        self.stop.set()
        with self.condition:
            if self.active is not None and self.active.job is not None:
                self.active.job.terminate()
            self.condition.notify_all()
        if self.started:
            self.sampler.join(timeout=2.5)
            if self.sampler.is_alive():
                raise RuntimeError("v3_sampler_not_joined")
        else:
            self.acquirer.close()
        if raise_failure and self.failure is not None:
            raise RuntimeError("v3_continuous_observation_failed") from self.failure


class CoordinatedOwnedProcess(OwnedProcess):
    """Registra también startup; usa el Job original, sin tocar su protocolo.

    El Job se publica sólo después de crearlo en OwnedProcess. Si el sampler
    falló durante esa creación, se termina antes de abrir el proceso gated.
    Una vez asignado, TerminateJobObject despierta el lector del constructor.
    Sólo el constructor/caller hace close/join; el sampler nunca cierra pipes.
    """

    def __init__(
        self,
        config,
        trusted_handler,
        *,
        coordinator,
        startup_timeout_s=5,
        startup_deadline_ns=None,
    ):
        budget = StartupBudget.from_timeout(
            startup_timeout_s, deadline_ns=startup_deadline_ns
        )
        self.coordinator = coordinator
        self._owned_job = None
        with _budget_condition(coordinator.condition, budget):
            coordinator.set_phase("operation-provider-startup")
            coordinator.check()
            coordinator._reconcile_active()
            if coordinator.active is not None:
                raise RuntimeError("v3_parallel_operation_forbidden")
            coordinator.active = self
        try:
            super().__init__(
                config,
                trusted_handler,
                startup_timeout_s=startup_timeout_s,
                startup_deadline_ns=budget.deadline_ns,
            )
            with _budget_condition(coordinator.condition, budget):
                coordinator.check()
        except BaseException as failure:
            if hasattr(self, "closed"):
                self._startup_cleanup_deadline_ns = budget.deadline_ns
                BaseException.__setattr__(failure, "_owned_cleanup_resource", self)
                try:
                    self.close(graceful=False)
                except BaseException as cleanup:  # noqa: BLE001 - preservar primera causa y custodiar fallo secundario
                    coordinator.events.append(
                        {"cleanup_error": cleanup_error_record(cleanup)}
                    )
            raise
        finally:
            # Un nacimiento/cleanup pendiente conserva la reserva original.
            acquired = coordinator.condition.acquire(timeout=budget.remaining_s())
            if acquired:
                try:
                    if coordinator.active is self and self._custody_resolved():
                        coordinator.active = None
                finally:
                    coordinator.condition.release()

    @property
    def job(self):
        return self._owned_job

    @job.setter
    def job(self, value):
        self._owned_job = value
        if value is not None:
            with self.coordinator.condition:
                if (
                    self.coordinator.failure is not None
                    or self.coordinator.stop.is_set()
                ):
                    value.terminate()
                    raise WorkerFailure("v3_sampler_failed_during_owned_startup")


class RuntimeChannel:
    """RPC acotado; mismo coordinador para preparación, API y auditoría."""

    def __init__(self, coordinator, worker, *, audit_binding=None):
        coordinator.check()
        self.coordinator = coordinator
        self.worker = worker
        self.transport = threading.RLock()
        self.audit_binding = audit_binding
        self.audit_status = None

    @contextmanager
    def transaction(self):
        if not self.transport.acquire(blocking=False):
            raise RuntimeError("v3_parallel_channel_forbidden")
        try:
            yield
        finally:
            self.transport.release()

    def operation(self, name, arguments, *, timeout_s=120, idle=False, phase=None):
        with self.transaction():
            return self._operation(
                name, arguments, timeout_s=timeout_s, idle=idle, phase=phase
            )

    def _operation(self, name, arguments, *, timeout_s=120, idle=False, phase=None):
        from benchmark_canonical_integration import guard_runtime_operation

        guard_runtime_operation(self, name, arguments)
        from benchmark_plan import digest
        from benchmark_process import encode

        deadline = time.monotonic() + timeout_s

        def rpc(action, args):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.worker.close(graceful=False)
                raise TimeoutError("v3_operation_transfer_deadline")
            return self.coordinator.run_owned(
                phase or name,
                self.worker,
                {"operation": action, "arguments": args},
                timeout_s=remaining,
                idle=idle,
            )["value"]

        payload = {"operation": name, "arguments": arguments}
        if len(encode(payload, 64 * 1024**2)) < 3500:
            result = rpc(name, arguments)
        else:
            serialized = json.dumps(
                arguments, ensure_ascii=True, allow_nan=False, separators=(",", ":")
            )
            rpc(
                "args_begin",
                {
                    "action": name,
                    "characters": len(serialized),
                    "sha256": digest(arguments),
                },
            )
            for index, offset in enumerate(range(0, len(serialized), 1200)):
                rpc(
                    "args_fragment",
                    {"index": index, "text": serialized[offset : offset + 1200]},
                )
            result = rpc("args_execute", {})
        if isinstance(result, dict) and "api_error" in result:
            from benchmark_runtime import ApiError

            raise ApiError(result["api_error"], result.get("status"))
        return result

    def request(self, method, path, body=None, *, timeout=5, deadline=None):
        if deadline is not None:
            timeout = min(timeout, deadline - time.monotonic())
        return self.operation(
            "api",
            {"method": method, "path": path, "body": body, "timeout": timeout},
            timeout_s=timeout + 0.5,
            phase=(
                "submit"
                if method == "POST" and path == "/v1/jobs"
                else "load-unload"
                if path == "/v1/unload"
                else "status"
                if path.startswith("/v1/jobs/")
                else "readiness"
                if path == "/v1/health"
                else "estimate"
            ),
        )

    def events(self, job_id, after=0, *, timeout=1):
        return self.operation(
            "events",
            {"job_id": job_id, "after": after, "timeout": timeout},
            timeout_s=timeout + 0.5,
        )

    def write_json(self, path, value):
        return self.operation("write_json", {"path": str(path), "value": value})

    def read_json(self, path):
        return self.operation("read_json", {"path": str(path)})

    def close(self):
        self.worker.close()

    def audit_publications(self):
        """Transfiere las anclas de memoria por RPC acotado al auditor propio."""
        from benchmark_canonical_integration import canonical_for_runtime, read_runtime

        if canonical_for_runtime(self) is not None:
            return read_runtime(self)
        with self.transaction():
            return self._audit_publications()

    def _audit_publications(self):
        from benchmark_canonical_integration import canonical_for_runtime, read_runtime

        if canonical_for_runtime(self) is not None:
            return read_runtime(self)
        if self.audit_binding is not None:
            return self._audit_delta()
        with self.coordinator.condition:
            snapshot = {
                "root": str(self.coordinator.acquirer.root),
                "context": copy.deepcopy(self.coordinator.observation_context),
                "receipts": copy.deepcopy(self.coordinator.receipts),
                "attempts": copy.deepcopy(self.coordinator.attempts),
                "records": copy.deepcopy(self.coordinator.records),
            }
        from benchmark_plan import digest

        serialized = json.dumps(
            snapshot, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        )
        self.operation(
            "audit_begin", {"sha256": digest(snapshot), "characters": len(serialized)}
        )
        for index, offset in enumerate(range(0, len(serialized), 1200)):
            self.operation(
                "audit_fragment",
                {"index": index, "text": serialized[offset : offset + 1200]},
            )
        return self.operation("audit_validate", {}, timeout_s=3600)

    def _audit_delta(self):
        from benchmark_canonical_integration import canonical_for_runtime, read_runtime

        if canonical_for_runtime(self) is not None:
            return read_runtime(self)
        from benchmark_audit import COLLECTIONS, segment_header

        if self.audit_status is None:
            self.audit_status = self.operation("audit_delta_status", {})
        status = self.audit_status
        if status["stream"] != self.audit_binding["stream"]:
            raise ValueError("delta_stream_mismatch")
        with self.coordinator.condition:
            if (
                str(self.coordinator.acquirer.root) != self.audit_binding["root"]
                or self.coordinator.observation_context != self.audit_binding["context"]
            ):
                raise ValueError("delta_supervisor_binding_mismatch")
            target = {
                name: len(getattr(self.coordinator, name)) for name in COLLECTIONS
            }
        while status["positions"] != target:
            first = status["positions"]
            # Segmentos por intento: un rechazo no desplaza los índices de
            # recibos/registros ni permite publicar una aceptación sin inventario.
            with self.coordinator.condition:
                attempts = self.coordinator.attempts[
                    first["attempts"] : min(target["attempts"], first["attempts"] + 32)
                ]
                count = sum(a["status"] == "accepted" for a in attempts)
                segment = {
                    "attempts": copy.deepcopy(attempts),
                    "receipts": copy.deepcopy(
                        self.coordinator.receipts[
                            first["receipts"] : first["receipts"] + count
                        ]
                    ),
                    "records": copy.deepcopy(
                        self.coordinator.records[
                            first["records"] : first["records"] + count
                        ]
                    ),
                }
            if not attempts:
                raise ValueError("delta_supervisor_inventory_incomplete")
            header, serialized = segment_header(status, segment)
            self.operation("audit_delta_begin", header)
            for index, offset in enumerate(range(0, len(serialized), 1200)):
                self.operation(
                    "audit_delta_fragment",
                    {"index": index, "text": serialized[offset : offset + 1200]},
                )
            status = self.operation("audit_delta_commit", {}, timeout_s=3600)
            if (
                status["positions"] != header["last"]
                or status["prefix"] != header["prefix"]
            ):
                raise ValueError("delta_commit_ack_invalid")
            self.audit_status = status
        confirmed = self.operation("audit_delta_status", {})
        if confirmed != status:
            raise ValueError("delta_verified_prefix_changed")
        return confirmed
