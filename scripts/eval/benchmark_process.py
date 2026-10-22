"""Proceso persistente Windows, RPC JSON acotado y Ã¡rbol propio terminable.

API estable: OwnedProcess(config, trusted_handler) / OwnedWorker; trusted_handler
es ``ruta-local.py:Factory`` o ``module:Factory``, elegido por cÃ³digo del root,
nunca por JSON entrante. Factory(config) produce callable(payload, emit) y close().
call(payload, *, deadline_ns) acepta exclusivamente operation + arguments JSON.
El plazo absoluto perf_counter_ns incluye envÃ­o, recepciÃ³n y validaciÃ³n del padre;
el arranque tiene presupuesto separado startup_timeout_s (5s por defecto).
El resultado contiene value, progress real, relojes del padre y ownership verificado.
WorkerFailure / WorkerDeadline conservan progress, evidence y incomplete_invalid.
No interpreta el resultado del handler como prueba de commit: el siguiente integrador
debe validar sus propios bytes/recibo en el padre dentro del mismo deadline.

Cada frame tiene <=256KiB; peticiones <=4096 bytes; 64 progresos como mÃ¡ximo.
JSON finito, sin claves duplicadas, identidad/seq estrictas. Un lector propio de
pipe termina tras matar el Job (hijo y descendientes). El cierre verifica proceso,
Job vacÃ­o y lector unido. Se reserva 250ms para terminar antes del plazo original;
Windows no ofrece planificaciÃ³n de tiempo real y puede excederlo por scheduling.
DXGI/PDH y cualquier recurso del handler quedan exclusivamente en el hijo.
"""

import ctypes
import importlib
import importlib.util
import json
import math
import os
import queue
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

from benchmark_clock import utc_now
from benchmark_startup import StartupBudget

MAX_FRAME = 262144
MAX_REQUEST = 4096
MAX_PROGRESS = 64
RESERVE_NS = 250_000_000


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def encode(value, limit=MAX_FRAME):
    data = json.dumps(value, allow_nan=False, separators=(",", ":")).encode() + b"\n"
    if len(data) > limit:
        raise ValueError("frame_oversized")
    return data


def decode(data, limit=MAX_FRAME):
    if len(data) > limit or not data.endswith(b"\n"):
        raise ValueError("frame_oversized_or_truncated")
    return json.loads(
        data,
        object_pairs_hook=_pairs,
        parse_float=_finite_float,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")),
    )


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite_json")
    return number


class WorkerFailure(RuntimeError):
    status = "incomplete_invalid"

    def __init__(self, message, *, progress=(), evidence=None):
        super().__init__(message)
        self.progress = list(progress)
        self.evidence = evidence or {}
        self.partial_raw = self.progress[-1]["value"] if self.progress else None


class WorkerDeadline(WorkerFailure):
    pass


# Registros originales, nunca autoridad derivada de PID/JSON. Una syscall
# pendiente conserva su stack y todas sus referencias incluso al salir el caller.
_QUARANTINE = set()


class _BirthRecord:
    def __init__(self, owned, budget):
        self.owned = owned
        self.budget = budget
        self.revoked = False
        self.process = self.job = self.thread = None
        self.done = threading.Event()
        self.failure = None
        self.failure_ns = None
        self.actors = []
        self.actors_lock = threading.Lock()
        self.cleanup_thread = None
        self.cleanup_failure = None
        self.cleanup_reported = False
        self.cleanup_lock = threading.Lock()
        self.cleanup_done = threading.Event()
        self.cleanup_confirmed = False
        self.cleanup_evidence = None

    def revoke(self):
        # SÃ³lo cambia False -> True; no toma locks de transporte ni hace IO.
        self.revoked = True

    def check(self):
        if self.revoked or not self.budget.remaining_ns():
            self.revoke()
            raise WorkerDeadline("startup_deadline_expired")


class _NativeAction:
    """Custodia de una operaciÃ³n nativa propia; no ejecuta validadores externos."""

    def __init__(self, owned, action):
        self.owned = owned
        self.action = action
        self.done = threading.Event()
        self.value = self.failure = None
        self.failure_ns = None
        self.thread = threading.Thread(target=self.run, name="owned-native-action")

    def run(self):
        try:
            self.value = self.action()
        except BaseException as failure:  # noqa: BLE001 - custodiar primera causa, incluidos interrupts
            self.failure_ns = time.perf_counter_ns()
            self.failure = failure
        finally:
            self.done.set()

    def wait(self, deadline_ns):
        record = self.owned._birth_record
        with record.actors_lock:
            if record.revoked or time.perf_counter_ns() >= deadline_ns:
                record.revoke()
                raise WorkerDeadline("native_action_revoked")
            record.actors.append(self)
            try:
                self.thread.start()
            except BaseException:  # No se despachó el actor; conservar primera causa.
                record.actors.remove(self)
                raise
        remaining = max(0, (deadline_ns - time.perf_counter_ns()) / 1e9)
        completed = self.done.wait(remaining)
        if not completed:
            self.owned._birth_record.revoke()
        else:
            self.thread.join(
                timeout=max(0, (deadline_ns - time.perf_counter_ns()) / 1e9)
            )
        # El fallo ya observado dentro de D tiene prioridad sobre scheduling.
        if self.failure is not None and self.failure_ns < deadline_ns:
            failure = self.failure
            self.failure = None
            if time.perf_counter_ns() >= deadline_ns:
                self.owned._birth_record.revoke()
            self.owned._retire_joined_actions()
            if self.owned._birth_record.revoked:
                try:
                    self.owned.close(graceful=False, deadline_ns=deadline_ns)
                except BaseException as cleanup:  # noqa: BLE001 - primera causa intacta, cleanup sólo secundario
                    from benchmark_coordinator import safe_cleanup_error_record

                    if self.owned.close_evidence is None:
                        self.owned.close_evidence = {}
                    self.owned.close_evidence["cleanup_error"] = (
                        safe_cleanup_error_record(cleanup)
                    )
                self.owned._publish_cleanup_if_joined()
                if isinstance(failure, WorkerFailure):
                    failure.evidence["cleanup"] = self.owned.close_evidence
            raise failure
        if (
            not completed
            or self.thread.is_alive()
            or time.perf_counter_ns() >= deadline_ns
            or self.owned._birth_record.revoked
        ):
            self.owned._birth_record.revoke()
            raise WorkerDeadline("native_action_completion_late")
        value = self.value
        self.owned._retire_joined_actions()
        self.owned._publish_cleanup_if_joined()
        if self.failure is not None:
            raise self.failure
        return value


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64),
        ("job_time", ctypes.c_int64),
        ("flags", wintypes.DWORD),
        ("minimum", ctypes.c_size_t),
        ("maximum", ctypes.c_size_t),
        ("active_limit", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority", wintypes.DWORD),
        ("scheduling", wintypes.DWORD),
    ]


class _Limits(ctypes.Structure):
    _fields_ = [
        ("basic", _BasicLimits),
        ("io", ctypes.c_uint64 * 6),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process", ctypes.c_size_t),
        ("peak_job", ctypes.c_size_t),
    ]


class _Accounting(ctypes.Structure):
    _fields_ = [
        ("times", ctypes.c_int64 * 4),
        ("faults", wintypes.DWORD),
        ("total", wintypes.DWORD),
        ("active", wintypes.DWORD),
        ("terminated", wintypes.DWORD),
    ]


def kernel():
    if os.name != "nt":
        raise ValueError("windows_required")
    dll = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetInformationJobObject": (
            [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD],
            wintypes.BOOL,
        ),
        "QueryInformationJobObject": (
            [
                wintypes.HANDLE,
                ctypes.c_int,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.c_void_p,
            ],
            wintypes.BOOL,
        ),
        "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        "IsProcessInJob": (
            [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)],
            wintypes.BOOL,
        ),
        "GetProcessTimes": (
            [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4,
            wintypes.BOOL,
        ),
        "GetProcessId": ([wintypes.HANDLE], wintypes.DWORD),
        "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        "OpenProcess": (
            [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD],
            wintypes.HANDLE,
        ),
        "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
    }
    for name, (args, result) in signatures.items():
        getattr(dll, name).argtypes = args
        getattr(dll, name).restype = result
    return dll


def process_alive(pid):
    dll = kernel()
    handle = dll.OpenProcess(0x100000, False, pid)
    if not handle:
        return False
    try:
        return dll.WaitForSingleObject(handle, 0) == 258
    finally:
        dll.CloseHandle(handle)


class WindowsJob:
    def __init__(self):
        self.dll = kernel()
        self.handle = self.dll.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _Limits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway
        if not self.dll.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process):
        if not self.dll.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        return self.evidence(process)

    def evidence(self, process):
        handle = int(process._handle)
        member = wintypes.BOOL()
        times = [wintypes.FILETIME() for _ in range(4)]
        if (
            not self.dll.IsProcessInJob(handle, self.handle, ctypes.byref(member))
            or not member.value
        ):
            raise ValueError("job_membership_unverified")
        if self.dll.GetProcessId(handle) != process.pid:
            raise ValueError("pid_identity_unverified")
        if not self.dll.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            raise ValueError("creation_time_unverified")
        return {
            "pid": process.pid,
            "creation_time": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
            "job_member": True,
        }

    def active(self):
        value = _Accounting()
        if not self.dll.QueryInformationJobObject(
            self.handle, 1, ctypes.byref(value), ctypes.sizeof(value), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.active

    def terminate(self):
        if self.handle and not self.dll.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def member_handles(self):
        """Retain verified member handles to observe actual kernel completion."""
        buffer = ctypes.create_string_buffer(8 + 128 * ctypes.sizeof(ctypes.c_size_t))
        if not self.dll.QueryInformationJobObject(
            self.handle, 3, buffer, len(buffer), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        count = ctypes.c_uint32.from_buffer(buffer, 4).value
        if count > 128:
            raise ValueError("owned_member_limit")
        handles = []
        try:
            for index in range(count):
                pid = ctypes.c_size_t.from_buffer(
                    buffer, 8 + index * ctypes.sizeof(ctypes.c_size_t)
                ).value
                handle = self.dll.OpenProcess(0x101000, False, pid)
                if not handle:  # Already exited, no kill by PID.
                    continue
                member = wintypes.BOOL()
                if (
                    not self.dll.IsProcessInJob(
                        handle, self.handle, ctypes.byref(member)
                    )
                    or not member.value
                ):
                    self.dll.CloseHandle(handle)
                    raise ValueError("member_identity_unverified")
                handles.append(handle)
            return handles
        except Exception:
            for handle in handles:
                self.dll.CloseHandle(handle)
            raise

    def close(self):
        if self.handle:
            self.dll.CloseHandle(self.handle)
            self.handle = None


class OwnedProcess:
    def __init__(
        self,
        config,
        trusted_handler,
        *,
        startup_timeout_s=5,
        startup_deadline_ns=None,
    ):
        budget = StartupBudget.from_timeout(
            startup_timeout_s, deadline_ns=startup_deadline_ns
        )
        self.closed = False
        self._lifecycle = threading.Lock()
        self._cleanup_claimed = False
        self._cleanup_done = threading.Event()
        self._writers = []
        self.reader_eof = False
        self._read_rejection = None
        self._handler_closed = False
        self._trusted_config_bytes = encode(config, MAX_REQUEST)
        self._last_completion = None
        self._mux = None
        self.process = self.reader = self.job = None
        self.ownership = {}
        self.close_evidence = None
        self.seq = 0
        self.messages = queue.Queue(maxsize=MAX_PROGRESS + 2)
        self.lock = threading.Lock()
        # Validate all startup bytes before creating resources.
        gate = encode(
            {"gate": True, "handler": trusted_handler, "config": config}, MAX_REQUEST
        )
        self._birth_record = _BirthRecord(self, budget)
        if config.get("canonical_mux_v1") is True:
            from benchmark_canonical_runtime import ParentMux

            class StartupMux(ParentMux):
                @property
                def live(mux):
                    return mux._live and not self._birth_record.revoked

                @live.setter
                def live(mux, value):
                    mux._live = bool(value) and not self._birth_record.revoked

            self._mux = StartupMux(self)
            gate = self._mux.gate(config, trusted_handler)
        startup_deadline = budget.deadline_ns
        try:
            self._birth_record.check()
            # El deadline tambiÃ©n se comprueba en el protocolo hijo antes de
            # importar el handler: un write fÃ­sicamente tardÃ­o no da efectos.
            gated = decode(gate, MAX_REQUEST)
            gated["startup_deadline_ns"] = startup_deadline
            gate = encode(gated, MAX_REQUEST)
            record = self._birth_record
            record.thread = threading.Thread(
                target=self._birth,
                args=(gate, config, trusted_handler),
                name="owned-native-birth",
            )
            _QUARANTINE.add(record)
            record.thread.start()
            if not record.done.wait(budget.remaining_s()):
                record.revoke()
                if record.failure is not None and record.failure_ns < startup_deadline:
                    raise record.failure
                raise WorkerDeadline("native_birth_deadline")
            record.thread.join(timeout=budget.remaining_s())
            if record.failure is not None and record.failure_ns < startup_deadline:
                raise record.failure
            record.check()
            if record.failure is not None:
                raise record.failure
            self.reader = threading.Thread(
                target=self._read, name=f"owned-pipe-{self.pid}"
            )
            self.reader.start()
            self._native(lambda: self._send_gate(gate), startup_deadline)
            ready = self._receive(startup_deadline)
            if ready != {"type": "ready", "pid": self.pid}:
                raise ValueError("startup_identity_invalid")
            if (
                self._native(lambda: self.job.evidence(self.process), startup_deadline)
                != self.ownership
            ):
                raise ValueError("startup_identity_changed")
            if time.perf_counter_ns() >= startup_deadline:
                raise WorkerDeadline("startup_completion_late")
            if self._mux:
                self._native(
                    lambda: self._mux.activate(startup_deadline), startup_deadline
                )
            record.check()
        except BaseException as failure:
            self._birth_record.revoke()
            self._startup_cleanup_deadline_ns = startup_deadline
            try:
                BaseException.__setattr__(failure, "_owned_cleanup_resource", self)
            except BaseException:  # noqa: BLE001,S110 - traceback y quarantine conservan self
                pass
            try:
                self.close(graceful=False)
            except BaseException as cleanup:  # noqa: BLE001 - preservar identidad y traceback del error de arranque
                # Conservar el recurso propio incluso si el constructor no retorna.
                # El traceback original retiene tambiÃ©n este frame y su self si
                # la excepciÃ³n impide adjuntar una referencia explÃ­cita.
                try:
                    BaseException.__setattr__(failure, "_owned_cleanup_resource", self)
                except BaseException:  # noqa: BLE001,S110 - custodia secundaria: nunca sustituir la primera causa
                    pass
                try:
                    from benchmark_coordinator import safe_cleanup_error_record

                    record = safe_cleanup_error_record(cleanup)
                    if self.close_evidence is None:
                        self.close_evidence = {}
                    self.close_evidence["cleanup_error"] = record
                    self.close_evidence["resources_returned"] = False
                    self.close_evidence["disposition"] = "UNKNOWN_QUARANTINED"
                    if isinstance(failure, WorkerFailure):
                        failure.evidence["cleanup_error"] = record
                        failure.evidence["cleanup"] = self.close_evidence
                except BaseException:  # noqa: BLE001,S110 - el registro secundario nunca sustituye el arranque
                    pass
            raise

    def _birth(self, gate, config, trusted_handler):
        """SÃ³lo construcciÃ³n nativa confiada; sin handler/hash/validadores."""
        record = self._birth_record
        try:
            record.check()
            # Publicar la referencia ANTES del setter coordinado, que puede fallar.
            record.job = WindowsJob()
            self.job = record.job
            record.check()
            record.process = subprocess.Popen(
                [sys._base_executable, str(Path(__file__).resolve()), "--owned-child"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.process = record.process
            self.pid = self.process.pid
            record.check()
            self.ownership = self.job.assign(self.process)
            record.check()
        except BaseException as failure:  # noqa: BLE001 - custodiar primera causa, incluidos interrupts
            record.failure_ns = time.perf_counter_ns()
            record.failure = failure
        finally:
            record.done.set()
            if record.revoked:
                # El objeto tardÃ­o jamÃ¡s recibe gate. SÃ³lo se reconcilian sus
                # handles originales; la custodia permanece UNKNOWN hasta proof.
                self.close(graceful=False)
                if record.cleanup_thread:
                    # SÃ³lo el actor retenido espera aquÃ­; nunca el caller bajo D.
                    record.cleanup_thread.join()

    def _native(self, action, deadline_ns):
        if self._birth_record.revoked or time.perf_counter_ns() >= deadline_ns:
            self._birth_record.revoke()
            raise WorkerDeadline("native_action_revoked")
        return _NativeAction(self, action).wait(deadline_ns)

    def _retire_joined_actions(self):
        """Retirar sólo tras join real; nunca soltar un actor pendiente."""
        record = self._birth_record
        with record.actors_lock:
            for action in list(record.actors):
                if action.thread.ident is not None and not action.thread.is_alive():
                    action.thread.join(timeout=0)
                    record.actors.remove(action)
                    action.action = None
                    action.value = None

    def _custody_resolved(self):
        """Admisión interna: éxito sin actores o cierre propio confirmado."""
        record = getattr(self, "_birth_record", None)
        if record is None:
            return getattr(self, "process", None) is None and self.job is None
        self._publish_cleanup_if_joined()
        with record.actors_lock:
            pending = bool(record.actors)
        pending = pending or (
            record.thread is not None
            and (record.thread.ident is None or record.thread.is_alive())
            or record.cleanup_thread is not None
            and (
                record.cleanup_thread.ident is None or record.cleanup_thread.is_alive()
            )
            or any(
                writer.ident is None or writer.is_alive() for writer in self._writers
            )
        )
        if pending:
            return False
        if not record.revoked:
            return True
        return bool(
            record.cleanup_confirmed
            and self.close_evidence
            and self.close_evidence.get("disposition") == "CLOSED_CONFIRMED"
            and (self.reader is None or not self.reader.is_alive())
            and self.job is not None
            and self.job.handle is None
            and self.process is not None
            and self.process._handle.closed
            and self.process.stdin.closed
            and self.process.stdout.closed
        )

    def _publish_cleanup_if_joined(self):
        record = self._birth_record
        self._retire_joined_actions()
        if (
            record.thread is not None
            and record.thread.ident is not None
            and not record.thread.is_alive()
        ):
            record.thread.join(timeout=0)
        if (
            record.cleanup_thread is not None
            and record.cleanup_thread.ident is not None
            and not record.cleanup_thread.is_alive()
        ):
            record.cleanup_thread.join(timeout=0)
        joined = (
            (
                record.thread is None
                or record.thread.ident is not None
                and not record.thread.is_alive()
            )
            and record.cleanup_thread is not None
            and record.cleanup_thread.ident is not None
            and not record.cleanup_thread.is_alive()
            and all(not action.thread.is_alive() for action in record.actors)
        )
        if (
            record.cleanup_confirmed
            and record.cleanup_failure is None
            and joined
            and record.cleanup_evidence
        ):
            self.close_evidence = record.cleanup_evidence
            self.close_evidence["resources_returned"] = True
            self.close_evidence["disposition"] = "CLOSED_CONFIRMED"
            self.close_evidence["transport_join_observed_ns"] = time.perf_counter_ns()
            _QUARANTINE.discard(record)

    def _send_gate(self, gate):
        self._birth_record.check()
        return self.process.stdin.write(gate)

    def _read(self):
        drained_frames = drained_bytes = 0
        try:
            while True:
                draining = self._mux and self._mux._remote_error is not None
                if draining and (
                    time.perf_counter_ns() >= self._mux._drain_deadline_ns
                    or drained_frames >= MAX_PROGRESS + 2
                    or drained_bytes >= (MAX_PROGRESS + 2) * (MAX_FRAME + 1)
                ):
                    raise ValueError("revoked_pipe_drain_limit")
                frame = self.process.stdout.readline(MAX_FRAME + 1)
                if not frame:
                    self.reader_eof = True
                    raise ValueError("worker_pipe_eof")
                if draining:
                    drained_frames += 1
                    drained_bytes += len(frame)
                try:
                    value = decode(frame)
                    if self._mux and "mac" in value:
                        self._mux.deliver(value)
                    elif draining:
                        raise ValueError("epoch_revoked")
                    else:
                        self.messages.put_nowait(value)
                except (ValueError, TypeError, RecursionError, queue.Full) as error:
                    if not self._mux or self._mux._remote_error is None:
                        raise
                    # Logical rejection remains a fact; only the independently
                    # authenticated terminal permits physical EOF observation.
                    if self._read_rejection is None:
                        self._read_rejection = str(error)
                    continue
        except (OSError, ValueError, TypeError, RecursionError, queue.Full) as error:
            if self._mux:
                self._mux.fail(error)
            try:
                self.messages.put_nowait(error)
            except queue.Full:
                pass

    def _receive(self, deadline_ns):
        remaining = (deadline_ns - time.perf_counter_ns()) / 1e9
        if remaining <= 0:
            raise WorkerDeadline("original_deadline_expired")
        try:
            message = self.messages.get(timeout=remaining)
        except queue.Empty as error:
            raise WorkerDeadline("worker_deadline") from error
        if isinstance(message, Exception):
            raise WorkerFailure(str(message)) from message
        return message

    def call(self, payload, *, deadline_ns):
        if self._mux:
            return self._native(
                lambda: self._mux.call(payload, deadline_ns=deadline_ns), deadline_ns
            )
        started = time.perf_counter_ns()
        started_utc = utc_now()
        progress = []
        if not self.lock.acquire(blocking=False):
            raise WorkerFailure("concurrent_call_rejected")
        try:
            if self.closed:
                raise WorkerFailure("worker_closed")
            if type(deadline_ns) is not int:
                raise ValueError("deadline_invalid")
            if (
                not isinstance(payload, dict)
                or set(payload) - {"operation", "arguments"}
                or not isinstance(payload.get("operation"), str)
            ):
                raise ValueError("closed_operation_payload_required")
            self.seq += 1
            request = encode({"seq": self.seq, "payload": payload}, MAX_REQUEST)
            cutoff = deadline_ns - RESERVE_NS
            if time.perf_counter_ns() >= cutoff:
                raise WorkerDeadline("insufficient_original_budget")
            if (
                self._native(lambda: self.job.evidence(self.process), cutoff)
                != self.ownership
            ):
                raise WorkerFailure("worker_identity_changed")
            self._native(lambda: self.process.stdin.write(request), cutoff)
            expected = 0
            while True:
                message = self._receive(cutoff)
                if (
                    not isinstance(message, dict)
                    or type(message.get("seq")) is not int
                    or type(message.get("index")) is not int
                    or message.get("seq") != self.seq
                    or message.get("index") != expected
                ):
                    raise WorkerFailure("stale_or_reordered_reply")
                expected += 1
                if message.get("type") == "progress":
                    if len(progress) >= MAX_PROGRESS or set(message) != {
                        "type",
                        "seq",
                        "index",
                        "utc",
                        "monotonic_ns",
                        "value",
                    }:
                        raise WorkerFailure("invalid_progress")
                    if (
                        not isinstance(message["utc"], str)
                        or type(message["monotonic_ns"]) is not int
                    ):
                        raise WorkerFailure("invalid_progress_clock")
                    progress.append(message)
                    continue
                if message.get("type") == "error":
                    raise WorkerFailure(message.get("error", "worker_operation_failed"))
                if message.get("type") != "result" or set(message) != {
                    "type",
                    "seq",
                    "index",
                    "value",
                }:
                    raise WorkerFailure("invalid_result")
                # Parent observes actual complete frame, validates ownership and time.
                if (
                    self._native(lambda: self.job.evidence(self.process), cutoff)
                    != self.ownership
                ):
                    raise WorkerFailure("worker_identity_changed")
                result = {
                    "value": message["value"],
                    "progress": progress,
                    "parent_started_utc": started_utc,
                    "parent_finished_utc": utc_now(),
                    "parent_started_monotonic_ns": started,
                    "ownership": dict(self.ownership),
                    "parent_completion_verified": True,
                }
                finished = time.perf_counter_ns()
                if finished >= cutoff:
                    raise WorkerDeadline("completion_late")
                result["parent_finished_monotonic_ns"] = finished
                # Private provenance: immutable request bytes and actual observed
                # completion, never a consumer's approval boolean. No RAW history.
                self._last_completion = (
                    encode(decode(request, MAX_REQUEST)["payload"], MAX_REQUEST),
                    {
                        **{
                            k: v
                            for k, v in result.items()
                            if k not in {"value", "progress"}
                        },
                        "value": decode(encode(message["value"])),
                    },
                )
                return result
        except BaseException as error:
            evidence = {
                "ownership": dict(self.ownership),
                "parent_started_utc": started_utc,
                "parent_started_monotonic_ns": started,
            }
            try:
                self.close(graceful=False)
            except (OSError, ValueError, RuntimeError) as cleanup:
                evidence["cleanup_error"] = str(cleanup)
            evidence["parent_finished_monotonic_ns"] = time.perf_counter_ns()
            evidence["parent_finished_utc"] = utc_now()
            evidence["cleanup"] = self.close_evidence
            if not isinstance(error, Exception):
                raise
            cls = WorkerDeadline if isinstance(error, WorkerDeadline) else WorkerFailure
            raise cls(str(error), progress=progress, evidence=evidence) from error
        finally:
            self.lock.release()

    def close(self, *, graceful=True, deadline_ns=None):
        record = self._birth_record
        record.revoke()
        deadline = getattr(
            self, "_startup_cleanup_deadline_ns", time.perf_counter_ns() + 220_000_000
        )
        if deadline_ns is not None:
            deadline = min(deadline, deadline_ns)
        # Nunca limpiar concurrentemente un resultado de birth aÃºn no recibido.
        if record.thread and record.thread.is_alive() and not record.done.is_set():
            self.close_evidence = {
                "resources_returned": False,
                "disposition": "UNKNOWN_QUARANTINED",
                "birth_pending": True,
            }
            return

        def clean():
            try:
                self._close_owned(graceful=graceful)
            except BaseException as failure:  # noqa: BLE001 - custodiar primera causa, incluidos interrupts
                record.cleanup_failure = failure
            finally:
                record.cleanup_done.set()

        if not record.cleanup_lock.acquire(
            timeout=max(0, (deadline - time.perf_counter_ns()) / 1e9)
        ):
            self.close_evidence = {
                "resources_returned": False,
                "disposition": "UNKNOWN_QUARANTINED",
                "cleanup_pending": True,
            }
            return
        try:
            start_cleanup = record.cleanup_thread is None
            if start_cleanup:
                record.cleanup_thread = threading.Thread(
                    target=clean, name="owned-native-cleanup"
                )
                record.cleanup_thread.start()
        finally:
            record.cleanup_lock.release()
        record.cleanup_done.wait(max(0, (deadline - time.perf_counter_ns()) / 1e9))
        record.cleanup_thread.join(
            timeout=max(0, (deadline - time.perf_counter_ns()) / 1e9)
        )
        if record.cleanup_thread.is_alive():
            self.close_evidence = {
                "resources_returned": False,
                "disposition": "UNKNOWN_QUARANTINED",
                "cleanup_pending": True,
            }
            return
        if record.cleanup_failure is not None and not record.cleanup_reported:
            record.cleanup_reported = True
            raise record.cleanup_failure
        joined = (record.thread is None or not record.thread.is_alive()) and all(
            not action.thread.is_alive() for action in record.actors
        )
        if (
            self.close_evidence
            and self.close_evidence.get("resources_returned")
            and joined
        ):
            _QUARANTINE.discard(record)
        elif self.close_evidence:
            self.close_evidence["resources_returned"] = False
            self.close_evidence["disposition"] = "UNKNOWN_QUARANTINED"

    def _close_owned(self, *, graceful=True):
        with self._lifecycle:
            first = not self.closed
            self.closed = True
        if self._mux:
            self._mux.fail(WorkerFailure("epoch_revoked"))
            graceful = False
        if first and graceful and self.process and self.process.poll() is None:
            # A pipe write may block in the kernel. It never owns the cleanup claim.
            def shutdown():
                try:
                    self.process.stdin.write(encode({"shutdown": True}, MAX_REQUEST))
                except (OSError, ValueError):
                    pass

            writer = threading.Thread(target=shutdown, name="owned-graceful-writer")
            with self._lifecycle:
                if not self._cleanup_claimed:
                    self._writers.append(writer)
                else:
                    writer = None
            if writer:
                writer.start()
                writer.join(timeout=0.03)
                if not writer.is_alive() and not self._cleanup_claimed:
                    try:
                        self._handler_closed = self._receive(
                            time.perf_counter_ns() + 30_000_000
                        ) == {"type": "closed", "pid": self.pid}
                    except (OSError, ValueError, RuntimeError):
                        pass
        with self._lifecycle:
            claimed = not self._cleanup_claimed
            self._cleanup_claimed = True
        if not claimed:
            if threading.current_thread() is not self.reader:
                self._cleanup_done.wait(timeout=0.22)
            return
        try:
            self._cleanup(graceful=False)
        finally:
            self._cleanup_done.set()

    def abort_owned(self, reason):
        """Revoca sin esperar writer/RPC; termina exclusivamente el Job original."""
        if not isinstance(reason, str) or not reason:
            raise ValueError("abort_reason_required")
        self.close(graceful=False)
        return self.close_evidence

    def _cleanup(self, *, graceful=False):
        errors = []
        member_handles = []
        cleanup_deadline = getattr(
            self, "_startup_cleanup_deadline_ns", time.perf_counter_ns() + 220_000_000
        )
        cleanup_started = time.perf_counter_ns()
        job_empty = False
        ownership_verified = False
        process_signalled = False
        members_signalled = []
        handler_closed = self._handler_closed
        try:
            # Terminar puede despertar RPC/pipe, pero ningún handle se cierra
            # mientras un actor nativo aún pueda usar sus objetos originales.
            with self._birth_record.actors_lock:
                actors = list(self._birth_record.actors)
            if any(action.thread.is_alive() for action in actors) and self.job:
                try:
                    self.job.terminate()
                except (OSError, ValueError, RuntimeError) as error:
                    errors.append(str(error))
            for action in actors:
                action.thread.join()
            self._retire_joined_actions()
            if self.job:
                if self.process and self.ownership:
                    try:
                        ownership_verified = (
                            self.job.evidence(self.process) == self.ownership
                        )
                        if not ownership_verified:
                            errors.append("cleanup_original_ownership_changed")
                    except (OSError, ValueError, RuntimeError) as error:
                        errors.append(str(error))
                try:
                    member_handles = self.job.member_handles()
                except (OSError, ValueError, RuntimeError) as error:
                    errors.append(str(error))
                try:
                    self.job.terminate()
                except (OSError, ValueError, RuntimeError) as error:
                    errors.append(str(error))
                    # KILL_ON_JOB_CLOSE is a second, still ownership-scoped way
                    # to wake readers even if TerminateJobObject failed.
                    self.job.close()
            if self.process:
                # Assignment can fail, but the gated process cannot spawn: kill
                # only our Popen handle, never enumerate names or foreign PIDs.
                if self.process.poll() is None:
                    try:
                        self.process.kill()
                    except OSError as error:
                        errors.append(str(error))
                try:
                    self.process.wait(
                        timeout=max(
                            0,
                            min(
                                0.05, (cleanup_deadline - time.perf_counter_ns()) / 1e9
                            ),
                        )
                    )
                except subprocess.TimeoutExpired:
                    # El caller ya no espera; este actor conserva los handles
                    # hasta observar el exit real de su Popen original.
                    self.process.wait()
                milliseconds = max(
                    0, min(50, (cleanup_deadline - time.perf_counter_ns()) // 1_000_000)
                )
                status = self.job.dll.WaitForSingleObject(
                    int(self.process._handle), milliseconds
                )
                if status == 258:
                    # Sin nueva ventana para el caller. El actor de cleanup
                    # retiene el handle exacto hasta el join nativo real.
                    status = self.job.dll.WaitForSingleObject(
                        int(self.process._handle), 0xFFFFFFFF
                    )
                if status != 0:
                    errors.append("owned_process_not_signalled")
                else:
                    process_signalled = True
            if self.job:
                wait_end = min(cleanup_deadline, time.perf_counter_ns() + 50_000_000)
                for handle in member_handles:
                    milliseconds = max(
                        0, (wait_end - time.perf_counter_ns()) // 1_000_000
                    )
                    status = self.job.dll.WaitForSingleObject(handle, milliseconds)
                    if status == 258:
                        status = self.job.dll.WaitForSingleObject(handle, 0xFFFFFFFF)
                    signalled = status == 0
                    members_signalled.append(signalled)
                    if not signalled:
                        errors.append("owned_member_not_signalled")
            if self.reader:
                if threading.current_thread() is not self.reader:
                    self.reader.join(
                        timeout=max(
                            0,
                            min(
                                0.05, (cleanup_deadline - time.perf_counter_ns()) / 1e9
                            ),
                        )
                    )
                if self.reader.is_alive():
                    self.reader.join()
            for writer in self._writers:
                writer._started.wait(
                    timeout=max(0, (cleanup_deadline - time.perf_counter_ns()) / 1e9)
                )
                if writer.ident is not None:
                    writer.join(
                        timeout=max(
                            0, (cleanup_deadline - time.perf_counter_ns()) / 1e9
                        )
                    )
                if writer.ident is None or writer.is_alive():
                    writer._started.wait()
                    writer.join()
            if self.job and self.job.handle:
                end = cleanup_deadline
                while self.job.active() and time.perf_counter_ns() < end:
                    time.sleep(0.001)
                if self.job.active():
                    errors.append("owned_job_not_empty")
                else:
                    job_empty = True
        finally:
            if self.job:
                for handle in member_handles:
                    self.job.dll.CloseHandle(handle)
                self.job.close()
            if self.process:
                for pipe in (self.process.stdin, self.process.stdout):
                    if pipe:
                        pipe.close()
                if self.process.poll() is not None:
                    self.process._handle.Close()
            self.close_evidence = {
                "ownership": dict(self.ownership),
                "started_monotonic_ns": cleanup_started,
                "finished_monotonic_ns": time.perf_counter_ns(),
                "finished_utc": utc_now(),
                "job_empty": job_empty,
                "verified_member_count": len(member_handles),
                "members_signalled": members_signalled,
                "process_signalled": process_signalled,
                "original_ownership_verified": ownership_verified,
                "reader_joined": self.reader is None or not self.reader.is_alive(),
                "reader_eof": self.reader_eof,
                "protocol_rejection": self._read_rejection,
                "writer_joined": all(
                    w.ident is not None and not w.is_alive() for w in self._writers
                ),
                "process_exit_code": self.process.returncode if self.process else None,
                "handler_close_observed": handler_closed,
                "errors": errors,
            }
            confirmed = (
                not errors
                and ownership_verified
                and process_signalled
                and all(members_signalled)
                and job_empty
                and self.close_evidence["reader_joined"]
                and self.close_evidence["writer_joined"]
                and (self.reader_eof or self.reader is None)
                and self.process is not None
                and self.process.returncode is not None
            )
            self._birth_record.cleanup_confirmed = confirmed
            confirmed = confirmed and all(
                not action.thread.is_alive() for action in self._birth_record.actors
            )
            self.close_evidence["resources_returned"] = confirmed
            self.close_evidence["disposition"] = (
                "CLOSED_CONFIRMED" if confirmed else "UNKNOWN_QUARANTINED"
            )
            self._birth_record.cleanup_evidence = self.close_evidence
        if errors:
            raise WorkerFailure(";".join(errors))


OwnedWorker = OwnedProcess


def _load_factory(reference):
    module_name, name = reference.rsplit(":", 1)
    if module_name.endswith(".py"):
        path = Path(module_name).resolve()
        if not path.is_relative_to(Path(__file__).resolve().parents[2]):
            raise ValueError("handler_outside_repository")
        spec = importlib.util.spec_from_file_location("trusted_owned_handler", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        spec = importlib.util.find_spec(module_name)
        if (
            not spec
            or not spec.origin
            or not Path(spec.origin)
            .resolve()
            .is_relative_to(Path(__file__).resolve().parents[2])
        ):
            raise ValueError("handler_outside_repository")
        module = importlib.import_module(module_name)
    return getattr(module, name)


def _child():
    incoming, outgoing = sys.stdin.buffer, sys.stdout.buffer
    gate = decode(incoming.readline(MAX_REQUEST + 1), MAX_REQUEST)
    if gate.get("gate") is not True:
        raise ValueError("startup_gate_missing")
    if "startup_deadline_ns" in gate:
        StartupBudget(gate.pop("startup_deadline_ns")).check()
    if gate.get("mode") == "canonical_mux_v1":
        from benchmark_canonical_runtime import serve_mux

        return serve_mux(gate, incoming, outgoing)
    # Only now may trusted handler imports or constructors execute.
    handler = _load_factory(gate["handler"])(gate["config"])
    handler_closed = False
    wire_lock = threading.Lock()
    try:
        outgoing.write(encode({"type": "ready", "pid": os.getpid()}))
        outgoing.flush()
        while True:
            frame = incoming.readline(MAX_REQUEST + 1)
            if not frame:
                return
            request = decode(frame, MAX_REQUEST)
            if request == {"shutdown": True}:
                handler.close()
                handler_closed = True
                outgoing.write(encode({"type": "closed", "pid": os.getpid()}))
                outgoing.flush()
                return
            seq, index = request["seq"], 0

            def emit(value, *, request_seq=seq):
                nonlocal index
                # Handlers may acquire sensors in parallel. The protocol index
                # and the framed pipe write must advance atomically; otherwise
                # two callbacks can publish the same index or interleave bytes.
                with wire_lock:
                    if index >= MAX_PROGRESS:
                        raise ValueError("progress_limit")
                    frame_index = index
                    index += 1
                    outgoing.write(
                        encode(
                            {
                                "type": "progress",
                                "seq": request_seq,
                                "index": frame_index,
                                "utc": utc_now(),
                                "monotonic_ns": time.perf_counter_ns(),
                                "value": value,
                            }
                        )
                    )
                    outgoing.flush()

            try:
                value = handler(request["payload"], emit)
            except Exception as error:  # noqa: BLE001 - worker boundary must serialize every handler failure
                with wire_lock:
                    outgoing.write(
                        encode(
                            {
                                "type": "error",
                                "seq": seq,
                                "index": index,
                                "error": f"{type(error).__name__}: {error}",
                            }
                        )
                    )
                    outgoing.flush()
                return
            with wire_lock:
                outgoing.write(
                    encode(
                        {"type": "result", "seq": seq, "index": index, "value": value}
                    )
                )
                outgoing.flush()
    finally:
        if not handler_closed:
            handler.close()


if __name__ == "__main__":
    _child()
