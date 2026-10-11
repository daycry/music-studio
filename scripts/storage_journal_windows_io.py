"""Custodia privada de memoria; no concede autoridad sobre archivos."""

import importlib
import os
import platform
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field

SIZE_T_MAX = 2**64 - 1
MAX_LENGTH = 1114112
MAX_COUNT = 8
MAX_LOGICAL = 8912896
MAX_REQUESTED = 9437176
_REGISTRY_LOCK = threading.RLock()
_LIVE_MEMORY_CONTEXTS = {}
_QUARANTINED_MEMORY_CONTEXTS = {}
_KERNEL_POISONED = False
_OPERATIONS = {"allocate", "info", "copy_in", "copy_out", "close", "context_close"}
_CODE_OPERATIONS = {
    "PLATFORM_UNSUPPORTED": {"context"},
    "ABI_UNACCREDITED": {"bind"},
    "CAPABILITY_INVALID": _OPERATIONS,
    "CAPABILITY_REVOKED": _OPERATIONS,
    "OWNER_MISMATCH": _OPERATIONS,
    "INTEGER_INVALID": {"allocate", "copy_in", "copy_out"},
    "RANGE_INVALID": {"allocate", "copy_in", "copy_out"},
    "ALIGNMENT_INVALID": {"allocate", "copy_in", "copy_out"},
    "OVERFLOW": {"allocate", "copy_in", "copy_out"},
    "ARENA_LIMIT": {"allocate", "copy_in", "copy_out"},
    "ALLOCATION_FAILED": {"allocate"},
    "RESOURCE_UNKNOWN": _OPERATIONS - {"info"},
    "OWNER_RETIRE_REQUIRED": _OPERATIONS - {"info"},
}


@dataclass(frozen=True)
class FailureDiagnostic:
    code: str
    operation: str
    win32_error: int | None = None
    ntstatus: int | None = None

    def __post_init__(self):
        if (
            type(self.code) is not str
            or type(self.operation) is not str
            or self.operation not in _CODE_OPERATIONS.get(self.code, set())
            or not _uint32(self.win32_error)
            or self.ntstatus is not None
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


@dataclass(frozen=True)
class CloseOutcome:
    state: str
    causes: tuple[FailureDiagnostic, ...] = ()

    def __post_init__(self):
        if (
            type(self.state) is not str
            or self.state not in {"closed", "unknown"}
            or type(self.causes) is not tuple
            or any(type(x) is not FailureDiagnostic for x in self.causes)
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


@dataclass(frozen=True)
class ArenaInfo:
    length: int
    alignment: int
    state: str
    provenance: str

    def __post_init__(self):
        if (
            type(self.length) is not int
            or type(self.alignment) is not int
            or self.length <= 0
            or self.alignment <= 0
            or type(self.state) is not str
            or self.state not in {"live", "revoked", "closed", "unknown"}
            or type(self.provenance) is not str
            or self.provenance not in {"cpu_double", "native_windows_x64"}
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


@dataclass(frozen=True)
class _AllocResult:
    base: int | None
    win32_error: int | None = None


@dataclass(frozen=True)
class _BoolResult:
    success: bool
    win32_error: int | None = None


@dataclass(frozen=True)
class _MemoryOps:
    allocate: object
    release: object
    copy_in: object
    copy_out: object


class KernelMemoryError(Exception):
    def __init__(self, diagnostic, cleanup=None):
        if type(diagnostic) is not FailureDiagnostic or (
            cleanup is not None and type(cleanup) is not CloseOutcome
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None
        self.diagnostic = diagnostic
        self.cleanup = cleanup
        super().__init__(diagnostic.code + "/" + diagnostic.operation)


class _MemoryContext:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("CAPABILITY_INVALID")

    def __repr__(self):
        return "<_MemoryContext>"

    def __reduce_ex__(self, protocol):
        raise TypeError("CAPABILITY_INVALID")


class AlignedArena:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("CAPABILITY_INVALID")

    def __repr__(self):
        return "<AlignedArena>"

    def __reduce_ex__(self, protocol):
        raise TypeError("CAPABILITY_INVALID")


@dataclass
class _MemoryCallRecord:
    operation: str
    arguments: tuple
    result: object = None
    error: BaseException | None = None


@dataclass
class _AllocationRecord:
    base: int
    address: int
    length: int
    alignment: int
    requested: int
    state: str = "live"
    outcome: CloseOutcome | None = None


@dataclass
class _ContextRecord:
    context: object
    ops: _MemoryOps
    provenance: str
    pid: int
    nonce: object = field(default_factory=object)
    lock: object = field(default_factory=threading.RLock)
    state: str = "live"
    charge: tuple = (0, 0, 0)
    allocations: dict = field(default_factory=dict)
    inflight: list = field(default_factory=list)
    outcome: CloseOutcome | None = None


def _fail(code, operation, error=None, cleanup=None):
    raise KernelMemoryError(
        FailureDiagnostic(code, operation, error), cleanup
    ) from None


def _poison(record, call, error=None):
    global _KERNEL_POISONED
    call.error = error
    record.state = "unknown"
    for allocation in record.allocations.values():
        if allocation.state != "closed":
            allocation.state = "unknown"
    with _REGISTRY_LOCK:
        _KERNEL_POISONED = True
        _QUARANTINED_MEMORY_CONTEXTS[record.context] = record


@contextmanager
def _pinned(context, operation):
    if type(context) is not _MemoryContext:
        _fail("CAPABILITY_INVALID", operation)
    with _REGISTRY_LOCK:
        record = _LIVE_MEMORY_CONTEXTS.get(context)
    if record is None or record.context is not context:
        _fail("CAPABILITY_INVALID", operation)
    with record.lock:
        if record.pid != os.getpid():
            _fail("OWNER_MISMATCH", operation)
        yield record


def _live(record, operation):
    with _REGISTRY_LOCK:
        poisoned = _KERNEL_POISONED
    if poisoned or record.state == "unknown":
        _fail("OWNER_RETIRE_REQUIRED", operation)
    if record.state != "live":
        _fail("CAPABILITY_REVOKED", operation)


def _owned_arena(record, arena, operation):
    if type(arena) is not AlignedArena:
        _fail("CAPABILITY_INVALID", operation)
    allocation = record.allocations.get(arena)
    if allocation is None:
        with _REGISTRY_LOCK:
            belongs_elsewhere = any(
                arena in r.allocations for r in _LIVE_MEMORY_CONTEXTS.values()
            )
        _fail(
            "OWNER_MISMATCH" if belongs_elsewhere else "CAPABILITY_INVALID", operation
        )
    return allocation


def _charge(record, count, logical, requested):
    record.charge = tuple(
        a + b for a, b in zip(record.charge, (count, logical, requested), strict=True)
    )


def _uint32(value):
    return value is None or (type(value) is int and 0 <= value <= 2**32 - 1)


def _new_memory_context():
    if not (
        os.name == "nt"
        and sys.platform == "win32"
        and sys.maxsize == 2**63 - 1
        and platform.machine().casefold() in {"amd64", "x86_64"}
    ):
        raise KernelMemoryError(
            FailureDiagnostic("PLATFORM_UNSUPPORTED", "context")
        ) from None
    with _REGISTRY_LOCK:
        if _KERNEL_POISONED:
            _fail("OWNER_RETIRE_REQUIRED", "allocate")
    try:
        abi = importlib.import_module(".storage_journal_windows_abi", __package__)
        ops = abi._new_native_memory_backend()
    except BaseException:  # noqa: BLE001 - frontera cerrada, interrupciones retenidas
        _fail("ABI_UNACCREDITED", "bind")
    return _assemble_memory_context(ops, provenance="native_windows_x64")


def _assemble_memory_context(ops, *, provenance):
    if (
        type(ops) is not _MemoryOps
        or type(provenance) is not str
        or provenance not in {"cpu_double", "native_windows_x64"}
        or not all(
            callable(x) for x in (ops.allocate, ops.release, ops.copy_in, ops.copy_out)
        )
    ):
        _fail("CAPABILITY_INVALID", "allocate")
    with _REGISTRY_LOCK:
        if _KERNEL_POISONED:
            _fail("OWNER_RETIRE_REQUIRED", "allocate")
        context = object.__new__(_MemoryContext)
        _LIVE_MEMORY_CONTEXTS[context] = _ContextRecord(
            context, ops, provenance, os.getpid()
        )
    return context


def _checked_reservation_size(length, alignment, size_t_max):
    if any(type(x) is not int for x in (length, alignment, size_t_max)):
        _fail("INTEGER_INVALID", "allocate")
    if length < 0 or alignment <= 0 or size_t_max < 0:
        _fail("RANGE_INVALID", "allocate")
    if length > size_t_max or alignment - 1 > size_t_max - length:
        _fail("OVERFLOW", "allocate")
    return length + alignment - 1


def _allocate_aligned(context, *, length, alignment):
    with _pinned(context, "allocate") as record:
        _live(record, "allocate")
        requested = _checked_reservation_size(length, alignment, SIZE_T_MAX)
        if length <= 0:
            _fail("RANGE_INVALID", "allocate")
        if (
            alignment < 512
            or alignment > 65536
            or alignment & (alignment - 1)
            or length % alignment
        ):
            _fail("ALIGNMENT_INVALID", "allocate")
        count, logical, reserved = record.charge
        if (
            length > MAX_LENGTH
            or count >= MAX_COUNT
            or logical + length > MAX_LOGICAL
            or reserved + requested > MAX_REQUESTED
        ):
            _fail("ARENA_LIMIT", "allocate")
        call = _MemoryCallRecord("allocate", (requested,))
        _charge(record, 1, length, requested)
        record.inflight.append(call)
        internal_error = False
        try:
            _backend_gate(record, "allocate")
            result = record.ops.allocate(requested)
            _acknowledge_result(call, result)
            if type(result) is not _AllocResult or not _uint32(result.win32_error):
                raise ValueError()
            if result.base is None:
                if result.win32_error is None:
                    raise ValueError()
                _charge(record, -1, -length, -requested)
                record.inflight.remove(call)
                internal_error = True
                _fail("ALLOCATION_FAILED", "allocate", result.win32_error)
            base = result.base
            if (
                type(base) is not int
                or not 0 < base <= SIZE_T_MAX
                or requested > SIZE_T_MAX - base
                or result.win32_error is not None
            ):
                raise ValueError()
            address = (base + alignment - 1) & ~(alignment - 1)
            if (
                address < base
                or address + length > base + requested
                or address % alignment
            ):
                raise ValueError()
            arena = object.__new__(AlignedArena)
            allocation = _AllocationRecord(base, address, length, alignment, requested)
            try:
                _register_allocation(record, arena, allocation)
            except Exception as error:  # noqa: BLE001 - rollback acreditado, primaria retenida
                call.error = error
                # Completion acreditada; la reserva aún es propia y retenida.
                record.allocations[arena] = allocation
                cleanup = _close_owned(record, allocation, acquisition_call=call)
                internal_error = True
                _fail("RESOURCE_UNKNOWN", "allocate", cleanup=cleanup)
            record.inflight.remove(call)
            return arena
        except BaseException as error:
            if internal_error:
                raise
            _poison(record, call, error)
            _fail("RESOURCE_UNKNOWN", "allocate")


def _arena_info(context, arena):
    with _pinned(context, "info") as record:
        allocation = _owned_arena(record, arena, "info")
        with _REGISTRY_LOCK:
            state = (
                "unknown"
                if _KERNEL_POISONED and allocation.state != "closed"
                else allocation.state
            )
        return ArenaInfo(
            allocation.length, allocation.alignment, state, record.provenance
        )


def _arena_copy_in(context, arena, *, offset, data):
    with _pinned(context, "copy_in") as record:
        allocation = _copy_ready(
            record, arena, offset, len(data) if type(data) is bytes else None, "copy_in"
        )
        if type(data) is not bytes:
            _fail("INTEGER_INVALID", "copy_in")
        if not data:
            return
        call = _MemoryCallRecord("copy_in", (allocation, data, offset))
        record.inflight.append(call)
        try:
            _backend_gate(record, "copy_in")
            result = record.ops.copy_in(allocation.address + offset, data)
            _acknowledge_result(call, result)
            if result is not None:
                raise ValueError()
            record.inflight.remove(call)
        except BaseException as error:  # noqa: BLE001 - custodia fuerte ante interrupcion
            _poison(record, call, error)
            _fail("RESOURCE_UNKNOWN", "copy_in")


def _arena_copy_out(context, arena, *, offset, length):
    with _pinned(context, "copy_out") as record:
        allocation = _copy_ready(record, arena, offset, length, "copy_out")
        if length == 0:
            return b""
        call = _MemoryCallRecord("copy_out", (allocation, offset, length))
        record.inflight.append(call)
        try:
            _backend_gate(record, "copy_out")
            result = record.ops.copy_out(allocation.address + offset, length)
            _acknowledge_result(call, result)
            if type(result) is not bytes or len(result) != length:
                raise ValueError()
            copied = bytes(bytearray(result))
            record.inflight.remove(call)
            return copied
        except BaseException as error:  # noqa: BLE001 - custodia fuerte ante interrupcion
            _poison(record, call, error)
            _fail("RESOURCE_UNKNOWN", "copy_out")


def _copy_ready(record, arena, offset, length, operation):
    _live(record, operation)
    allocation = _owned_arena(record, arena, operation)
    if allocation.state != "live":
        _fail("CAPABILITY_REVOKED", operation)
    if type(offset) is not int or type(length) is not int:
        _fail("INTEGER_INVALID", operation)
    if (
        offset < 0
        or length < 0
        or offset > allocation.length
        or length > allocation.length - offset
    ):
        _fail("RANGE_INVALID", operation)
    return allocation


def _backend_gate(record, operation):
    with _REGISTRY_LOCK:
        if _KERNEL_POISONED or record.state == "unknown":
            _fail("OWNER_RETIRE_REQUIRED", operation)


def _close_arena(context, arena):
    with _pinned(context, "close") as record:
        allocation = _owned_arena(record, arena, "close")
        return _close_owned(record, allocation)


def _close_owned(record, allocation, *, acquisition_call=None):
    if allocation.outcome is not None:
        return allocation.outcome
    allocation.state = "revoked"
    allocation.outcome = CloseOutcome(
        "unknown", (FailureDiagnostic("RESOURCE_UNKNOWN", "close"),)
    )
    with _REGISTRY_LOCK:
        poisoned = _KERNEL_POISONED
    if poisoned or record.state == "unknown":
        allocation.state = "unknown"
        with _REGISTRY_LOCK:
            _QUARANTINED_MEMORY_CONTEXTS[record.context] = record
        return allocation.outcome
    call = _MemoryCallRecord("close", (allocation, allocation.base))
    record.inflight.append(call)
    reserved_outcome = allocation.outcome
    retained_charge = record.charge
    retained_calls = tuple(record.inflight)
    try:
        _backend_gate(record, "close")
        result = record.ops.release(allocation.base)
        _acknowledge_result(call, result)
        if (
            type(result) is not _BoolResult
            or type(result.success) is not bool
            or not _uint32(result.win32_error)
        ):
            raise ValueError()
        if not result.success or result.win32_error is not None:
            if not result.success and _uint32(result.win32_error):
                allocation.outcome = CloseOutcome(
                    "unknown",
                    (
                        FailureDiagnostic(
                            "RESOURCE_UNKNOWN", "close", result.win32_error
                        ),
                    ),
                )
            raise ValueError()
        closed_outcome = CloseOutcome("closed")
        _charge(record, -1, -allocation.length, -allocation.requested)
        record.inflight.remove(call)
        if acquisition_call is not None:
            record.inflight.remove(acquisition_call)
        allocation.state = "closed"
        allocation.outcome = closed_outcome
        return allocation.outcome
    except BaseException as error:  # noqa: BLE001 - custodia fuerte ante interrupcion
        # El TRUE sólo acredita la llamada. Una publicación interrumpida no
        # acredita el cierre: restaurar reserva, cuota y custodia sin otro free.
        allocation.state = "unknown"
        if allocation.outcome is not None and allocation.outcome.state == "closed":
            allocation.outcome = reserved_outcome
        record.charge = retained_charge
        record.inflight[:] = retained_calls
        _poison(record, call, error)
    return allocation.outcome


def _close_memory_context(context):
    with _pinned(context, "context_close") as record:
        if record.outcome is not None:
            return record.outcome
        record.outcome = CloseOutcome(
            "unknown", (FailureDiagnostic("RESOURCE_UNKNOWN", "context_close"),)
        )
        reserved_outcome = record.outcome
        if record.state == "live":
            record.state = "revoked"
        for allocation in record.allocations.values():
            if allocation.state == "live":
                allocation.state = "revoked"
        with _REGISTRY_LOCK:
            if _KERNEL_POISONED or record.state == "unknown":
                record.state = "unknown"
                _QUARANTINED_MEMORY_CONTEXTS[context] = record
                for allocation in record.allocations.values():
                    if allocation.state != "closed":
                        allocation.state = "unknown"
                return record.outcome
        causes = []
        try:
            for allocation in reversed(tuple(record.allocations.values())):
                outcome = _close_owned(record, allocation)
                causes.extend(outcome.causes)
            if causes:
                record.outcome = CloseOutcome("unknown", tuple(causes))
            else:
                closed_outcome = CloseOutcome("closed")
                record.state = "closed"
                record.outcome = closed_outcome
            return record.outcome
        except BaseException as error:  # noqa: BLE001 - custodia fuerte ante interrupcion
            record.outcome = reserved_outcome
            call = _MemoryCallRecord("context_close", (context,))
            record.inflight.append(call)
            _poison(record, call, error)
        return record.outcome


def _register_allocation(record, arena, allocation):
    record.allocations[arena] = allocation


def _acknowledge_result(call, result):
    call.result = result
