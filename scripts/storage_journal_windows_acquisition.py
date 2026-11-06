"""Adquisición candidata privada: interfaz pendiente, sin efectos ni autoridad."""

import importlib
import os
import platform
import re
import struct
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum

from . import storage_journal_windows_identity as _identity
from . import storage_journal_windows_io as _io

_OPS = {
    "owner",
    "locate",
    "descriptor",
    "open_anchor",
    "open_component",
    "info",
    "close",
    "owner_close",
}
_CODE_OPERATIONS = {
    "PLATFORM_UNSUPPORTED": {"owner"},
    "ABI_UNACCREDITED": {"owner"},
    "ADMISSION_REQUIRED": {
        "owner",
        "locate",
        "descriptor",
        "open_anchor",
        "open_component",
    },
    "PRINCIPAL_UNACCREDITED": {
        "owner",
        "locate",
        "descriptor",
        "open_anchor",
        "open_component",
    },
    "SECURITY_UNACCREDITED": {"open_component"},
    "CAPABILITY_INVALID": _OPS,
    "OWNER_MISMATCH": _OPS,
    "CAPABILITY_REVOKED": _OPS,
    "CAPABILITY_IN_USE": {"close"},
    "PROFILE_INVALID": {"open_component"},
    "DISPOSITION_INVALID": {"open_component"},
    "DESCRIPTOR_INVALID": {"descriptor", "open_component"},
    "COMPONENT_INVALID": {"locate", "open_component"},
    "ANCHOR_UNACCREDITED": {"locate", "open_anchor"},
    "ACQUISITION_LIMIT": {
        "owner",
        "locate",
        "descriptor",
        "open_anchor",
        "open_component",
    },
    "OPEN_FAILED": {"open_anchor", "open_component"},
    "NOT_FOUND": {"open_anchor", "open_component"},
    "CONFLICT": {"open_component"},
    "SHARING_CONFLICT": {"open_anchor", "open_component"},
    "ACCESS_DENIED": {"open_anchor", "open_component"},
    "RESOURCE_UNKNOWN": _OPS - {"info"},
    "OWNER_RETIRE_REQUIRED": _OPS - {"info"},
}


class _OwnerState(Enum):
    BUILDING = "building"
    LIVE = "live"
    UNKNOWN = "unknown"
    CLOSING = "closing"
    CLOSED = "closed"
    REVOKED = "revoked"


class _AuxiliaryState(Enum):
    BUILDING = "building"
    LIVE = "live"
    REVOKED = "revoked"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class _CallPhase(Enum):
    RESERVED = "reserved"
    ENTERED = "entered"
    ACKNOWLEDGED = "acknowledged"
    RETURNED = "returned"
    COMPLETED = "completed"
    ACKNOWLEDGING = "acknowledging"
    UNKNOWN = "unknown"


@dataclass
class _AnchorLocatorRecord:
    capability: object
    owner_ref: object
    source: str
    state: _AuxiliaryState = _AuxiliaryState.BUILDING
    root_dos: str = ""
    guid: str = ""
    target: str = ""
    nt_name: str = ""
    arena_refs: tuple = ()


@dataclass
class _AcquisitionCallFrame:
    owner_ref: object
    operation: str
    phase: _CallPhase = _CallPhase.RESERVED
    locator_record: object = None
    project_location: str = ""
    slot_index: int | None = None
    record_ref: object = None
    parent_ref: object = None
    descriptor_ref: object = None
    access: int = 0
    share: int = 0
    options: int = 0
    nt_disposition: int = 0
    file_attributes: int = 0
    object_attributes: int = 0x40
    name_bytes: bytes = b""
    descriptor_record: object = None
    arena_refs: tuple = ()
    boundary_lease_ref: object = None
    admission_pin: object = None
    call_record_ref: object = None

    @property
    def profile(self):
        return self.record_ref.profile if self.record_ref is not None else None

    @property
    def disposition(self):
        return self.record_ref.disposition if self.record_ref is not None else None

    @property
    def locator_ref(self):
        return (
            self.locator_record.capability if self.locator_record is not None else None
        )


class _AcquisitionState(Enum):
    RESERVED = "reserved"
    CANDIDATE = "candidate"
    ENTERED = "entered"
    FAILED = "failed"
    UNKNOWN = "unknown"
    CLOSING = "closing"
    CLOSED = "closed"
    REVOKED = "revoked"


@dataclass
class _AcquisitionRecord:
    capability: object
    owner_ref: object
    slot_index: int
    parent_ref: object
    profile: object
    disposition: object
    descriptor_ref: object = None
    completion: object = None
    state: _AcquisitionState = _AcquisitionState.RESERVED
    child_pins: int = 0
    outcome: object = None
    native_close_attempted: bool = False
    diagnostic: object = None
    info_snapshot: object = None


@dataclass(frozen=True)
class AcquisitionDiagnostic:
    code: str
    operation: str
    win32_error: int | None = None
    ntstatus: int | None = None

    def __post_init__(self):
        if (
            type(self.code) is not str
            or type(self.operation) is not str
            or self.operation not in _CODE_OPERATIONS.get(self.code, set())
            or any(
                value is not None
                and (type(value) is not int or not 0 <= value <= 2**32 - 1)
                for value in (self.win32_error, self.ntstatus)
            )
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


class AcquisitionError(Exception):
    def __init__(self, diagnostic, cleanup=None):
        if type(diagnostic) is not AcquisitionDiagnostic or (
            cleanup is not None and type(cleanup) is not AcquisitionCloseOutcome
        ):
            raise ValueError("ERROR_INVALID") from None
        self.diagnostic = diagnostic
        self.cleanup = cleanup
        super().__init__(diagnostic.code + "/" + diagnostic.operation)


@dataclass(frozen=True)
class AcquisitionCloseOutcome:
    state: str
    causes: tuple = ()

    def __post_init__(self):
        if (
            type(self.state) is not str
            or self.state not in {"closed", "unknown"}
            or type(self.causes) is not tuple
            or any(type(cause) is not AcquisitionDiagnostic for cause in self.causes)
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


def _fail(code, operation, *, ntstatus=None):
    raise AcquisitionError(
        AcquisitionDiagnostic(code, operation, ntstatus=ntstatus)
    ) from None


def _owner_record(owner, operation):
    with _io._REGISTRY_LOCK:
        record = (
            (
                _LIVE_ACQUISITION_OWNERS.get(owner)
                or _CLOSED_ACQUISITION_OWNERS.get(owner)
            )
            if type(owner) is _AcquisitionOwner
            else None
        )
    if (
        type(record) is not _AcquisitionOwnerRecord
        or record.capability is not owner
        or record.pid != os.getpid()
    ):
        _fail("CAPABILITY_INVALID", operation)
    return record


def _begin_call_pin(record, frame):
    if record.admission_ref is None:
        return
    try:
        if record.source == "cpu_double":
            _identity._pin_cpu_acquisition_admission(
                record.admission_ref, owner=record.capability
            )
        else:
            _identity._pin_current_acquisition_admission(
                record.admission_ref, owner=record.capability
            )
    except _identity.IdentityError as error:
        call = next(call for call in record.inflight if call.frame is frame)
        if record.source == "cpu_double":
            source = next(
                (
                    source
                    for source in _identity._CPU_AUTHORITIES.values()
                    if frame.admission_pin in source.pins
                ),
                None,
            )
            pin_row = (
                source.pins.get(frame.admission_pin) if source is not None else None
            )
        else:
            with _io._REGISTRY_LOCK:
                pin_row = _io._IDENTITY_CAPABILITIES.get(frame.admission_pin)
            try:
                source = (
                    _io._registered_native_session(pin_row.session_ref)
                    if type(pin_row) is _identity._AdmissionPinRecord
                    else None
                )
            except _io.KernelMemoryError:
                source = None
        _preserve_admission_cleanup_failure(record, call, source, error)
        if (
            pin_row is not None
            and pin_row.state == "revoked"
            and not _io._KERNEL_POISONED
        ):
            if frame.operation == "close":
                record.state = _OwnerState.REVOKED
                failure = AcquisitionError(
                    AcquisitionDiagnostic("OWNER_RETIRE_REQUIRED", "close")
                )
                call.error = error
                call.recognized_error = failure
                raise failure from None
            _retire_preentry_call(record, call)
            failure = AcquisitionError(
                AcquisitionDiagnostic(error.diagnostic.code, frame.operation)
            )
            call.recognized_error = failure
            raise failure from None
        _unknown(record, call, error)


def _retire_preentry_call(record, call):
    frame = call.frame
    if frame.operation == "locate":
        transient = frame.arena_refs[1:]
        frame.locator_record.state = _AuxiliaryState.CLOSED
    elif frame.operation == "descriptor":
        transient = frame.arena_refs[1:]
        frame.descriptor_record.state = _AuxiliaryState.CLOSED
        frame.descriptor_record.arena = None
    else:
        transient = frame.arena_refs[-1:]
        frame.record_ref.state = _AcquisitionState.FAILED
        record.handles -= 1
        if frame.parent_ref is not None:
            record.acquisitions[frame.parent_ref].child_pins -= 1
    for arena in transient:
        record.backings.remove(arena)
        arena.state = _AuxiliaryState.CLOSED
        arena.overlay = None
        arena.native_base = 0
        arena.storage = bytearray()
    record.inflight.remove(call)
    frame.arena_refs = (record.control,)
    frame.phase = _CallPhase.ACKNOWLEDGED


def _precheck_bound_admission(record, operation, profile=None):
    if record.admission_ref is None:
        return
    admission = record.admission_ref
    try:
        if record.source == "cpu_double":
            source = next(
                (
                    source
                    for source in _identity._CPU_AUTHORITIES.values()
                    if admission in source.admissions
                ),
                None,
            )
            if source is None:
                _fail("ADMISSION_REQUIRED", operation)
            row = _identity._cpu_admission_current(source, admission, "pin")
        else:
            _identity._validate_current_admission(admission)
            with _io._REGISTRY_LOCK:
                row = _io._IDENTITY_CAPABILITIES[admission]
            _, source = _identity._authority_record(
                row.principal_ratification_ref, "pin"
            )
        if (
            source.owner_refs.get(record.capability) is not record
            or record.policy_ref is not source.policy_ref
            or record.epoch_ref is not source.epoch_ref
        ):
            _fail("CAPABILITY_INVALID", operation)
        counters = source.counters
        if (
            type(source.pin_slots_reserved) is not int
            or not 0 <= source.pin_slots_reserved < 2048
            or set(counters) != {"observations", "subcalls"}
            or any(type(v) is not int or v < 0 for v in counters.values())
            or counters["observations"] > 8190
            or counters["subcalls"] > 229376 - 56
        ):
            if record.source == "cpu_double":
                _identity._revoke_cpu_pin_source(source)
            else:
                _identity._revoke_session(source)
            _fail("OWNER_RETIRE_REQUIRED", operation)
        if (
            row.scope is _identity._AdmissionScope.CANDIDATE_READ_ONLY
            and profile is not None
            and profile
            not in {
                _AcquireProfile.ANCHOR_CANDIDATE,
                _AcquireProfile.PARENT_EXISTING,
                _AcquireProfile.READ_EXISTING,
            }
        ):
            _fail("ADMISSION_REQUIRED", operation)
    except _identity.IdentityError as error:
        code = error.diagnostic.code
        if operation not in _CODE_OPERATIONS.get(code, set()):
            code = "RESOURCE_UNKNOWN"
        _fail(code, operation)


def _finish_call_pin(record, frame):
    if frame.admission_pin is None:
        return
    try:
        if record.source == "cpu_double":
            _identity._complete_cpu_acquisition_admission_pin(
                frame.admission_pin, owner=record.capability
            )
        else:
            _identity._complete_acquisition_admission_pin(
                frame.admission_pin, owner=record.capability
            )
    except _identity.IdentityError as error:
        call = next(call for call in record.inflight if call.frame is frame)
        if record.source == "cpu_double":
            source = next(
                (
                    source
                    for source in _identity._CPU_AUTHORITIES.values()
                    if frame.admission_pin in source.pins
                ),
                None,
            )
            pin_row = (
                source.pins.get(frame.admission_pin) if source is not None else None
            )
        else:
            with _io._REGISTRY_LOCK:
                pin_row = _io._IDENTITY_CAPABILITIES.get(frame.admission_pin)
            try:
                source = (
                    _io._registered_native_session(pin_row.session_ref)
                    if type(pin_row) is _identity._AdmissionPinRecord
                    else None
                )
            except _io.KernelMemoryError:
                source = None
        _preserve_admission_cleanup_failure(record, call, source, error)
        if (
            pin_row is not None
            and pin_row.state == "revoked"
            and not _io._KERNEL_POISONED
        ):
            record.state = _OwnerState.REVOKED
            if frame.record_ref is not None:
                frame.record_ref.state = _AcquisitionState.REVOKED
            for auxiliary in (frame.locator_record, frame.descriptor_record):
                if auxiliary is not None:
                    auxiliary.state = _AuxiliaryState.REVOKED
            call.error = error
            code = (
                error.diagnostic.code
                if frame.operation != "close"
                else "OWNER_RETIRE_REQUIRED"
            )
            failure = AcquisitionError(AcquisitionDiagnostic(code, frame.operation))
            call.recognized_error = failure
            raise failure from None
        _unknown(record, call, error)


def _preserve_admission_cleanup_failure(record, call, source, error):
    query_frame = None
    if type(source) is _identity._CpuAuthorityRecord:
        query_frame = source.frame
    elif type(source) is _identity._IdentitySessionRecord:
        observation = next(reversed(source.observations.values()), None)
        if (
            type(observation) is _identity._EffectiveObservationRecord
            and source.observations.get(observation.capability) is observation
        ):
            query_frame = observation.frame_ref
    provenance_error = query_frame.public_error if query_frame is not None else None
    if (
        type(provenance_error) is not _identity.IdentityError
        or not (error is provenance_error or error.__context__ is provenance_error)
        or error.cleanup is not provenance_error.cleanup
        or error.diagnostic.code != provenance_error.diagnostic.code
        or type(error.cleanup) is not _identity.IdentityCloseOutcome
        or error.cleanup.state != "unknown"
        or call.frame.operation
        not in _CODE_OPERATIONS.get(error.diagnostic.code, set())
        or not _identity._finished_custody_error(source, query_frame, provenance_error)
    ):
        return
    _retain_unknown(record, call, provenance_error)
    cleanup = AcquisitionCloseOutcome(
        "unknown",
        tuple(
            AcquisitionDiagnostic(
                "RESOURCE_UNKNOWN",
                call.frame.operation,
                win32_error=diagnostic.win32_error,
            )
            for diagnostic in error.cleanup.diagnostics
        ),
    )
    failure = AcquisitionError(
        AcquisitionDiagnostic(
            error.diagnostic.code,
            call.frame.operation,
            win32_error=error.diagnostic.win32_error,
        ),
        cleanup,
    )
    call.recognized_error = failure
    raise failure from None


@contextmanager
def _owner_domain(owner, operation):
    try:
        with _io._kernel_domain() as boundary:
            record = _owner_record(owner, operation)
            with record.lock:
                _owner_record(owner, operation)
                if record.state is not _OwnerState.LIVE:
                    _fail("CAPABILITY_REVOKED", operation)
                previous = record.boundary_lease_ref
                record.boundary_lease_ref = boundary
                try:
                    yield record
                    _compact_completed_pin_frames(record, operation)
                finally:
                    record.boundary_lease_ref = previous
    except _io.KernelMemoryError as error:
        _fail(error.diagnostic.code, operation)


def _compact_completed_pin_frames(record, operation):
    if record.admission_ref is None:
        return
    if record.source == "cpu_double":
        source = next(
            (
                source
                for source in _identity._CPU_AUTHORITIES.values()
                if record.admission_ref in source.admissions
            ),
            None,
        )
    else:
        with _io._REGISTRY_LOCK:
            admission = _io._IDENTITY_CAPABILITIES.get(record.admission_ref)
        _, source = _identity._authority_record(
            admission.principal_ratification_ref, "complete"
        )
    if source is None:
        return
    originals = []
    try:
        for pin in source.pins.values():
            frame = pin.target_frame_ref
            if (
                pin.owner_ref is not record.capability
                or pin.state != "completed"
                or type(frame) is not _AcquisitionCallFrame
                or frame.phase is not _CallPhase.ACKNOWLEDGED
                or frame.call_record_ref is None
            ):
                continue
            original = frame.__dict__
            originals.append((frame, original))
            summary = {
                name: field.default
                for name, field in _AcquisitionCallFrame.__dataclass_fields__.items()
            }
            summary.update(
                owner_ref=frame.owner_ref,
                operation=frame.operation,
                phase=frame.phase,
                arena_refs=(record.control,),
                boundary_lease_ref=frame.boundary_lease_ref,
                admission_pin=frame.admission_pin,
            )
            frame.__dict__ = summary
    except BaseException as error:  # noqa: BLE001 - conserva preimágenes originales; no reconstruye buffers
        for frame, original in originals:
            frame.__dict__ = original
        for pin in source.pins.values():
            frame = pin.target_frame_ref
            if (
                pin.owner_ref is record.capability
                and pin.state == "completed"
                and type(frame) is _AcquisitionCallFrame
                and frame.call_record_ref is not None
            ):
                _retain_unknown(record, frame.call_record_ref, error)
        _fail("RESOURCE_UNKNOWN", operation)


def _owned(record, capability, expected, registry, operation):
    if type(capability) is not expected:
        _fail("CAPABILITY_INVALID", operation)
    row = registry.get(capability)
    if row is None:
        with _io._REGISTRY_LOCK:
            others = tuple(_LIVE_ACQUISITION_OWNERS.values())
        if any(
            capability in other.acquisitions or capability in other.locators
            for other in others
            if other is not record
        ):
            _fail("OWNER_MISMATCH", operation)
        _fail("CAPABILITY_INVALID", operation)
    if row.capability is not capability or row.owner_ref is not record.capability:
        _fail("CAPABILITY_INVALID", operation)
    return row


def _component_bytes(name, operation):
    if (
        type(name) is not str
        or not name
        or name in {".", ".."}
        or name[-1] in {".", " "}
    ):
        _fail("COMPONENT_INVALID", operation)
    if any(ord(char) < 32 or char in '\\/:*?"<>|' for char in name):
        _fail("COMPONENT_INVALID", operation)
    stem = name.split(".", 1)[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} or (
        len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[-1] in "123456789¹²³"
    ):
        _fail("COMPONENT_INVALID", operation)
    try:
        encoded = name.encode("utf-16-le", "strict")
    except UnicodeError:
        _fail("COMPONENT_INVALID", operation)
    if len(encoded) > 510:
        _fail("COMPONENT_INVALID", operation)
    return encoded


def _project_bytes(path):
    if (
        type(path) is not str
        or len(path) < 3
        or not path[0].isascii()
        or not path[0].isalpha()
        or path[1:3] != ":\\"
    ):
        _fail("COMPONENT_INVALID", "locate")
    for part in path[3:].split("\\") if len(path) > 3 else ():
        _component_bytes(part, "locate")
    try:
        encoded = path.encode("utf-16-le", "strict")
    except UnicodeError:
        _fail("COMPONENT_INVALID", "locate")
    if len(encoded) > 32766:
        _fail("COMPONENT_INVALID", "locate")
    return encoded


def _decode_utf16z(data, capacity):
    if (
        type(data) is not bytes
        or type(capacity) is not int
        or not 1 <= capacity <= 32768
        or len(data) < capacity * 2
    ):
        _fail("ANCHOR_UNACCREDITED", "locate")
    end = next(
        (
            offset
            for offset in range(0, capacity * 2, 2)
            if data[offset : offset + 2] == b"\0\0"
        ),
        None,
    )
    if end is None:
        _fail("ANCHOR_UNACCREDITED", "locate")
    try:
        return data[:end].decode("utf-16-le", "strict")
    except UnicodeError:
        _fail("ANCHOR_UNACCREDITED", "locate")


def _decode_device_multisz(data, count):
    if (
        type(data) is not bytes
        or type(count) is not int
        or not 1 <= count <= 32768
        or len(data) < count * 2
    ):
        _fail("ANCHOR_UNACCREDITED", "locate")
    try:
        values = data[: count * 2].decode("utf-16-le", "strict").split("\0")
    except UnicodeError:
        _fail("ANCHOR_UNACCREDITED", "locate")
    if (
        len(values) != 3
        or values[1:] != ["", ""]
        or not re.fullmatch(r"\\Device\\HarddiskVolume[0-9]{1,20}", values[0])
    ):
        _fail("ANCHOR_UNACCREDITED", "locate")
    return values[0]


_QUARANTINED_ACQUISITION_OWNERS = _io._QUARANTINED_ACQUISITION_OWNERS


def _retain_unknown(record, call, error=None):
    with _io._REGISTRY_LOCK:
        _io._KERNEL_POISONED = True
        _QUARANTINED_ACQUISITION_OWNERS[record.capability] = record
    record.state = _OwnerState.UNKNOWN
    call.error = error
    if not any(item is call for item in record.inflight):
        record.inflight.append(call)
    for arena in call.frame.arena_refs:
        if not any(item is arena for item in record.backings):
            record.backings.append(arena)
    call.frame.phase = _CallPhase.UNKNOWN
    if call.frame.record_ref is not None:
        call.frame.record_ref.state = _AcquisitionState.UNKNOWN
    for row in (call.frame.descriptor_record, call.frame.locator_record):
        if row is not None:
            row.state = _AuxiliaryState.UNKNOWN


def _unknown(record, call, error=None):
    _retain_unknown(record, call, error)
    failure = AcquisitionError(
        AcquisitionDiagnostic("RESOURCE_UNKNOWN", call.frame.operation)
    )
    call.recognized_error = failure
    raise failure from None


def _create_completion(record, call):
    result = call.return_value
    if type(result) is not _NativeCreateCompletion or (
        type(result.return_status) is not int
        or type(result.iosb_status) is not int
        or type(result.information) is not int
        or type(result.iosb_unchanged) is not bool
        or not 0 <= result.return_status <= 2**32 - 1
        or not 0 <= result.iosb_status <= 2**32 - 1
        or not 0 <= result.information <= 2**64 - 1
    ):
        _unknown(record, call)
    storage = record.control.storage
    slot = call.frame.slot_index
    base = record.control.aligned_offset
    handle = struct.unpack_from("<Q", storage, base + slot * 8)[0]
    union, info = struct.unpack_from("<QQ", storage, base + 2048 + slot * 16)
    returned = struct.unpack_from("<I", storage, base + 6144 + slot * 4)[0]
    before_base = call.preimage_offset
    preimage = call.preimage[
        before_base + 2048 + slot * 16 : before_base + 2064 + slot * 16
    ]
    unchanged = storage[base + 2048 + slot * 16 : base + 2064 + slot * 16] == preimage
    if (
        returned != result.return_status
        or (union & 0xFFFFFFFF) != result.iosb_status
        or union >> 32 != 0
        or info != result.information
        or unchanged is not result.iosb_unchanged
    ):
        _unknown(record, call)
    status = result.return_status
    expected = (
        1 if call.frame.record_ref.disposition is _Disposition.OPEN_EXISTING else 2
    )
    if status == 0:
        if union != 0 or info != expected or not 0 < handle < 2**64 - 6:
            _unknown(record, call)
        for other in record.acquisitions.values():
            if (
                other is not call.frame.record_ref
                and other.state
                in {
                    _AcquisitionState.CANDIDATE,
                    _AcquisitionState.ENTERED,
                    _AcquisitionState.UNKNOWN,
                }
                and struct.unpack_from("<Q", storage, base + other.slot_index * 8)[0]
                == handle
            ):
                _unknown(record, call)
        return result
    if (
        status >> 30 == 3
        and handle == 0
        and (unchanged or (union == status and info == 0))
    ):
        code = {
            0xC0000034: "NOT_FOUND",
            0xC000003A: "NOT_FOUND",
            0xC0000043: "SHARING_CONFLICT",
            0xC0000022: "ACCESS_DENIED",
        }.get(status, "OPEN_FAILED")
        if (
            status == 0xC0000035
            and call.frame.record_ref.disposition is _Disposition.CREATE_NEW
        ):
            code = "CONFLICT"
        row = call.frame.record_ref
        diagnostic = AcquisitionDiagnostic(code, call.frame.operation, ntstatus=status)
        failure = AcquisitionError(diagnostic)
        name_arena = call.frame.arena_refs[-1]
        before_backings = tuple(record.backings)
        before_inflight = tuple(record.inflight)
        before_handles = record.handles
        parent_row = record.acquisitions.get(row.parent_ref)
        before_pins = parent_row.child_pins if parent_row is not None else None
        before_arena = (
            name_arena.state,
            name_arena.overlay,
            name_arena.native_base,
            name_arena.storage,
        )
        before_refs = call.frame.arena_refs
        before_preimage = call.preimage
        before_result = call.return_value
        before_diagnostic = row.diagnostic
        try:
            row.state = _AcquisitionState.FAILED
            row.diagnostic = diagnostic
            record.handles -= 1
            if parent_row is not None:
                parent_row.child_pins -= 1
            record.inflight.remove(call)
            # No quitar la carga conservando bytes en la historia de pins.
            record.backings.remove(name_arena)
            name_arena.state = _AuxiliaryState.CLOSED
            name_arena.overlay = None
            name_arena.native_base = 0
            name_arena.storage = bytearray()
            call.frame.arena_refs = (record.control,)
            call.preimage = b""
            call.return_value = None
            call.frame.phase = _CallPhase.ACKNOWLEDGED
            call.recognized_error = failure
            raise failure from None
        except BaseException as error:  # restaurar custodia ante cortes del ACK
            if error is failure:
                # El traceback reconocido sigue en la historia de pins. Tras el
                # ACK ya no debe custodiar el backing original del rollback.
                before_arena = None
                raise
            record.backings[:] = before_backings
            record.inflight[:] = before_inflight
            record.handles = before_handles
            if parent_row is not None:
                parent_row.child_pins = before_pins
            (
                name_arena.state,
                name_arena.overlay,
                name_arena.native_base,
                name_arena.storage,
            ) = before_arena
            call.frame.arena_refs = before_refs
            call.preimage = before_preimage
            call.return_value = before_result
            call.recognized_error = None
            row.diagnostic = before_diagnostic
            raise
    _unknown(record, call)


@dataclass
class _AcquisitionCallRecord:
    frame: _AcquisitionCallFrame
    preimage: bytes
    return_value: object = None
    error: object = None
    recognized_error: object = None
    charge: tuple = ()
    subcalls: list = field(default_factory=list)
    preimage_offset: int = 0

    @property
    def primary(self):
        return (
            self.recognized_error.diagnostic
            if type(self.recognized_error) is AcquisitionError
            else None
        )

    @property
    def cleanup(self):
        return (
            self.recognized_error.cleanup
            if type(self.recognized_error) is AcquisitionError
            else None
        )


class _SdkFunction(Enum):
    NT_CREATE_FILE = "NtCreateFile"
    CLOSE_HANDLE = "CloseHandle"
    VOLUME_PATH = "GetVolumePathNameW"
    VOLUME_NAME = "GetVolumeNameForVolumeMountPointW"
    DOS_DEVICE = "QueryDosDeviceW"
    DRIVE_TYPE = "GetDriveTypeW"
    WELL_KNOWN_SID = "CreateWellKnownSid"
    VALID_SID = "IsValidSid"
    SID_LENGTH = "GetLengthSid"
    INITIALIZE_SD = "InitializeSecurityDescriptor"
    INITIALIZE_ACL = "InitializeAcl"
    ADD_ACE = "AddAccessAllowedAce"
    SET_OWNER = "SetSecurityDescriptorOwner"
    SET_GROUP = "SetSecurityDescriptorGroup"
    SET_DACL = "SetSecurityDescriptorDacl"
    SET_CONTROL = "SetSecurityDescriptorControl"
    VALID_SD = "IsValidSecurityDescriptor"
    GET_CONTROL = "GetSecurityDescriptorControl"
    GET_OWNER = "GetSecurityDescriptorOwner"
    GET_GROUP = "GetSecurityDescriptorGroup"
    GET_DACL = "GetSecurityDescriptorDacl"


@dataclass
class _SdkCallRecord:
    function: _SdkFunction
    ordinal: int
    phase: _CallPhase
    arena_refs: tuple
    output_ranges: tuple
    preimage: tuple
    all_args: tuple
    return_scalar: int | None = None
    win32_error: int | None = None
    error: object = None


class _SegmentName(Enum):
    CONTROL = "control"
    PRINCIPAL_SID = "principal_sid"
    GROUP_SID = "group_sid"
    SYSTEM_SID = "system_sid"
    ADMIN_SID = "admin_sid"
    PROJECT_INPUT = "project_input"
    ROOT_INPUT = "root_input"
    GUID_INPUT = "guid_input"
    DEVICE_INPUT = "device_input"
    UTF16_OUTPUT = "utf16_output"
    UNICODE_NAME = "unicode_name"
    UNICODE_STRING = "unicode_string"
    OBJECT_ATTRIBUTES = "object_attributes"
    ABSOLUTE_SD = "absolute_sd"
    DACL = "dacl"
    SDK_OUTPUTS = "sdk_outputs"


class _AcquisitionOwner(_identity._Opaque):
    __slots__ = ()


class _AnchorLocator(_identity._Opaque):
    __slots__ = ()


class _OwnedAcquisition(_identity._Opaque):
    __slots__ = ()


class _ClosedDescriptor(_identity._Opaque):
    __slots__ = ()


class _CpuAdmissionPin(_identity._Opaque):
    __slots__ = ()


class _AcquireProfile(Enum):
    ANCHOR_CANDIDATE = "ANCHOR_CANDIDATE"
    PARENT_EXISTING = "PARENT_EXISTING"
    PARENT_CREATE_FILE = "PARENT_CREATE_FILE"
    PARENT_CREATE_DOMAIN = "PARENT_CREATE_DOMAIN"
    READ_EXISTING = "READ_EXISTING"
    WRITER_EXISTING = "WRITER_EXISTING"
    CREATE_FILE = "CREATE_FILE"
    CREATE_DIRECTORY = "CREATE_DIRECTORY"


class _Disposition(Enum):
    OPEN_EXISTING = "OPEN_EXISTING"
    CREATE_NEW = "CREATE_NEW"


class _NewObjectRole(Enum):
    FILE_JOURNAL = "FILE_JOURNAL"
    DIRECTORY_DOMAIN = "DIRECTORY_DOMAIN"


@dataclass(frozen=True)
class _DescriptorCompletion:
    success: bool
    diagnostic: object = None


@dataclass
class _ClosedDescriptorRecord:
    capability: object
    owner_ref: object
    role: _NewObjectRole
    mask: int
    trustees: tuple
    acl_length: int
    arena: object
    state: _AuxiliaryState = _AuxiliaryState.BUILDING
    getter_outputs: tuple = ()


def _new_closed_descriptor(owner, *, role):
    with _owner_domain(owner, "descriptor") as record:
        _precheck_bound_admission(record, "descriptor")
        if type(role) is not _NewObjectRole:
            _fail("DESCRIPTOR_INVALID", "descriptor")
        if len(record.descriptors) >= 8 or record.inflight:
            _fail("ACQUISITION_LIMIT", "descriptor")
        mask = {
            _NewObjectRole.FILE_JOURNAL: 0x00120083,
            _NewObjectRole.DIRECTORY_DOMAIN: 0x001200A6,
        }[role]
        trustees = tuple(
            dict.fromkeys(
                (
                    record.principal_sid,
                    bytes.fromhex("010100000000000512000000"),
                    bytes.fromhex("01020000000000052000000020020000"),
                )
            )
        )
        acl_length = 8 + sum(8 + len(sid) for sid in trustees)
        (arena,) = _reserve_layouts(
            record,
            "descriptor",
            (((_SegmentName.ABSOLUTE_SD, 40, 8), (_SegmentName.DACL, acl_length, 4)),),
        )
        descriptor = object.__new__(_ClosedDescriptor)
        row = _ClosedDescriptorRecord(
            descriptor, owner, role, mask, trustees, acl_length, arena
        )
        record.descriptors[descriptor] = row
        frame = _AcquisitionCallFrame(
            owner,
            "descriptor",
            descriptor_record=row,
            arena_refs=(record.control, arena),
            boundary_lease_ref=record.boundary_lease_ref,
        )
        call = _AcquisitionCallRecord(frame, bytes(arena.storage))
        frame.call_record_ref = call
        record.inflight.append(call)
        _begin_call_pin(record, frame)
        frame.phase = _CallPhase.ENTERED
        try:
            call.return_value = record.ops.descriptor(frame)
            frame.phase = _CallPhase.RETURNED
            _finish_call_pin(record, frame)
            _aux_completion(record, call, _DescriptorCompletion)
            _validate_descriptor(record, call)
            frame.phase = _CallPhase.ACKNOWLEDGED
            record.inflight.remove(call)
            row.state = _AuxiliaryState.LIVE
            return descriptor
        except AcquisitionError as error:
            if error is call.recognized_error:
                raise
            _unknown(record, call, error)
        except BaseException as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
            _unknown(record, call, error)


def _aux_completion(record, call, expected_type):
    result = call.return_value
    if type(result) is not expected_type or type(result.success) is not bool:
        _unknown(record, call)
    if result.success:
        if result.diagnostic is not None:
            _unknown(record, call)
        return
    diagnostic = result.diagnostic
    if (
        type(diagnostic) is not AcquisitionDiagnostic
        or diagnostic.operation != call.frame.operation
        or diagnostic.win32_error == 997
    ):
        _unknown(record, call)
    if diagnostic.code not in {"DESCRIPTOR_INVALID", "ANCHOR_UNACCREDITED"}:
        _unknown(record, call)
    row = call.frame.descriptor_record or call.frame.locator_record
    row.state = _AuxiliaryState.CLOSED
    if call.frame.descriptor_record is not None:
        record.backings.remove(row.arena)
        row.arena = None
    else:
        for arena in call.frame.arena_refs:
            if arena is not record.control and any(
                item is arena for item in record.backings
            ):
                record.backings.remove(arena)
    record.inflight.remove(call)
    call.frame.phase = _CallPhase.ACKNOWLEDGED
    failure = AcquisitionError(diagnostic)
    call.recognized_error = failure
    raise failure from None


def _validate_descriptor(record, call):
    row = call.frame.descriptor_record
    data = memoryview(row.arena.storage)[
        row.arena.aligned_offset : row.arena.aligned_offset + row.arena.logical_length
    ]
    owner_pointer = record.control.native_base + 9216
    group_pointer = record.control.native_base + 9284
    acl_pointer = row.arena.native_base + 40
    expected_header = (1, 0, 0x1004, owner_pointer, group_pointer, 0, acl_pointer)
    expected_getters = (
        0x1004,
        1,
        owner_pointer,
        False,
        group_pointer,
        False,
        True,
        acl_pointer,
        False,
    )
    if (
        struct.unpack_from("<BBH4xQQQQ", data, 0) != expected_header
        or row.getter_outputs != expected_getters
    ):
        _unknown(record, call)
    if struct.unpack_from("<BBHHH", data, 40) != (
        2,
        0,
        row.acl_length,
        len(row.trustees),
        0,
    ):
        _unknown(record, call)
    offset = 48
    for sid in row.trustees:
        if (
            struct.unpack_from("<BBHI", data, offset) != (0, 0, 8 + len(sid), row.mask)
            or data[offset + 8 : offset + 8 + len(sid)] != sid
        ):
            _unknown(record, call)
        offset += 8 + len(sid)


@dataclass(frozen=True)
class _NativeCreateCompletion:
    return_status: int
    iosb_status: int
    information: int
    iosb_unchanged: bool


@dataclass(frozen=True)
class _NativeCloseCompletion:
    success: bool
    win32_error: int | None = None


@dataclass(frozen=True)
class _LocatorCompletion:
    success: bool
    diagnostic: object = None


def _locate_anchor(owner, *, project_location):
    with _owner_domain(owner, "locate") as record:
        _precheck_bound_admission(record, "locate")
        encoded = _project_bytes(project_location)
        if len(record.locators) >= 4 or record.inflight:
            _fail("ACQUISITION_LIMIT", "locate")
        inputs, outputs = _reserve_layouts(
            record,
            "locate",
            (
                ((_SegmentName.PROJECT_INPUT, 32768, 2),),
                ((_SegmentName.UTF16_OUTPUT, 65536, 2),),
            ),
        )
        inputs.storage[: len(encoded)] = encoded
        locator = object.__new__(_AnchorLocator)
        row = _AnchorLocatorRecord(locator, owner, record.source)
        record.locators[locator] = row
        frame = _AcquisitionCallFrame(
            owner,
            "locate",
            locator_record=row,
            project_location=project_location,
            arena_refs=(record.control, inputs, outputs),
            boundary_lease_ref=record.boundary_lease_ref,
        )
        call = _AcquisitionCallRecord(
            frame, bytes(record.control.storage), charge=(3, 108565, 0)
        )
        frame.call_record_ref = call
        record.inflight.append(call)
        _begin_call_pin(record, frame)
        frame.phase = _CallPhase.ENTERED
        try:
            call.return_value = record.ops.locate(frame)
            frame.phase = _CallPhase.RETURNED
            _finish_call_pin(record, frame)
            _aux_completion(record, call, _LocatorCompletion)
            if (
                any(
                    type(value) is not str
                    for value in (row.root_dos, row.guid, row.target, row.nt_name)
                )
                or row.root_dos.casefold() != project_location[:3].casefold()
                or not re.fullmatch(
                    r"Volume\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}",
                    row.guid,
                )
                or not re.fullmatch(r"\\Device\\HarddiskVolume[0-9]{1,20}", row.target)
                or row.nt_name != "\\??\\" + row.guid + "\\"
            ):
                _unknown(record, call)
            record.backings.remove(inputs)
            record.backings.remove(outputs)
            (persistent,) = _reserve_layouts(
                record,
                "locate",
                (
                    (
                        (_SegmentName.ROOT_INPUT, 8, 2),
                        (_SegmentName.GUID_INPUT, 100, 2),
                        (_SegmentName.DEVICE_INPUT, 128, 2),
                        (_SegmentName.UNICODE_NAME, 100, 2),
                    ),
                ),
            )
            row.arena_refs = (persistent,)
            for segment, value in zip(
                persistent.segments,
                (row.root_dos, row.guid, row.target, row.nt_name),
                strict=True,
            ):
                data = value.encode("utf-16-le") + b"\0\0"
                persistent.storage[segment[1] : segment[1] + len(data)] = data
            frame.phase = _CallPhase.ACKNOWLEDGED
            record.inflight.remove(call)
            row.state = _AuxiliaryState.LIVE
            return locator
        except AcquisitionError as error:
            if error is call.recognized_error:
                raise
            _unknown(record, call, error)
        except BaseException as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
            _unknown(record, call, error)


def _open_owned_anchor(owner, locator):
    with _owner_domain(owner, "open_anchor") as record:
        locator_record = _owned(
            record, locator, _AnchorLocator, record.locators, "open_anchor"
        )
        return _open(
            record,
            None,
            b"",
            _AcquireProfile.ANCHOR_CANDIDATE,
            _Disposition.OPEN_EXISTING,
            None,
            locator_record,
        )


_RECIPES = {
    _AcquireProfile.ANCHOR_CANDIDATE: (0x001200A0, 3, 0x00200021),
    _AcquireProfile.PARENT_EXISTING: (0x001200A0, 3, 0x00200021),
    _AcquireProfile.PARENT_CREATE_FILE: (0x001200A2, 3, 0x00200021),
    _AcquireProfile.PARENT_CREATE_DOMAIN: (0x001200A6, 3, 0x00200021),
    _AcquireProfile.READ_EXISTING: (0x00120081, 1, 0x00200068),
    _AcquireProfile.WRITER_EXISTING: (0x00120083, 0, 0x0020006A),
    _AcquireProfile.CREATE_FILE: (0x00120083, 0, 0x0020006A),
    _AcquireProfile.CREATE_DIRECTORY: (0x001200A6, 3, 0x00200021),
}


def _open(record, parent, name, profile, disposition, descriptor, locator=None):
    operation = "open_anchor" if parent is None else "open_component"
    _precheck_bound_admission(record, operation, profile)
    if record.handles >= 64 or record.next_slot >= 256 or record.inflight:
        _fail("ACQUISITION_LIMIT", operation)
    unicode_name = locator.nt_name.encode("utf-16-le") if locator is not None else name
    requested = ((len(unicode_name) + 9) & ~7) + 71
    if (
        len(record.backings) >= 8
        or requested > 131072
        or sum(arena.requested_bytes for arena in record.backings) + requested > 1048576
    ):
        _fail("ACQUISITION_LIMIT", operation)
    owner = record.capability
    access, share, options = _RECIPES[profile]
    frame = _AcquisitionCallFrame(
        owner,
        operation,
        locator_record=locator,
        parent_ref=parent,
        descriptor_ref=descriptor,
        access=access,
        share=share,
        options=options,
        nt_disposition=2 if disposition is _Disposition.CREATE_NEW else 1,
        file_attributes=0x80
        if profile is _AcquireProfile.CREATE_FILE
        else 0x10
        if profile is _AcquireProfile.CREATE_DIRECTORY
        else 0,
        name_bytes=name,
        arena_refs=(record.control,),
        boundary_lease_ref=record.boundary_lease_ref,
    )
    call = _AcquisitionCallRecord(frame, bytes(record.control.storage))
    frame.call_record_ref = call
    record.inflight.append(call)
    try:
        (name_arena,) = _reserve_layouts(
            record,
            operation,
            (
                (
                    (_SegmentName.UNICODE_NAME, len(unicode_name) + 2, 2),
                    (_SegmentName.UNICODE_STRING, 16, 8),
                    (_SegmentName.OBJECT_ATTRIBUTES, 48, 8),
                ),
            ),
        )
        frame.arena_refs = (
            (record.control,)
            + (locator.arena_refs if locator is not None else ())
            + (
                (record.descriptors[descriptor].arena,)
                if descriptor is not None
                else ()
            )
            + (name_arena,)
        )
        name_arena.storage[: len(unicode_name)] = unicode_name
        acquisition = object.__new__(_OwnedAcquisition)
        row = _AcquisitionRecord(
            acquisition,
            owner,
            record.next_slot,
            parent,
            profile,
            disposition,
            descriptor,
        )
        frame.record_ref = row
        record.next_slot += 1
        record.handles += 1
        record.acquisitions[acquisition] = row
        if parent is not None:
            record.acquisitions[parent].child_pins += 1
        slot = row.slot_index
        frame.slot_index = slot
        base = record.control.aligned_offset
        struct.pack_into("<Q", record.control.storage, base + slot * 8, 0)
        struct.pack_into(
            "<QQ",
            record.control.storage,
            base + 2048 + slot * 16,
            0x7FFFFFFF,
            2**64 - 1,
        )
        call.preimage = bytes(record.control.storage)
        call.preimage_offset = base
        _begin_call_pin(record, frame)
        frame.phase = _CallPhase.ENTERED
        row.state = _AcquisitionState.ENTERED
        call.return_value = record.ops.open(frame)
        frame.phase = _CallPhase.RETURNED
        _finish_call_pin(record, frame)
        row.completion = _create_completion(record, call)
        frame.phase = _CallPhase.COMPLETED
        try:
            row.info_snapshot = AcquisitionInfo(
                row.profile.value, row.disposition.value, "candidate", record.source
            )
        except (MemoryError, RuntimeError) as error:
            if type(error) not in {MemoryError, RuntimeError}:
                raise
            _rollback_registration(record, call, error)
        frame.phase = _CallPhase.ACKNOWLEDGING
        record.inflight.remove(call)
        record.backings.remove(name_arena)
        frame.phase = _CallPhase.ACKNOWLEDGED
        row.state = _AcquisitionState.CANDIDATE
        return acquisition
    except AcquisitionError as error:
        if error is call.recognized_error:
            raise
        _unknown(record, call, error)
    except BaseException as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
        _unknown(record, call, error)


def _rollback_registration(record, call, primary):
    frame = call.frame
    row = frame.record_ref
    call.error = primary
    cleanup = None
    try:
        record.rollback_calls.append(call)
        record.inflight.remove(call)
        outcome = _close_acquisition(record.capability, row.capability)
        if outcome.state == "closed":
            name_arena = frame.arena_refs[-1]
            record.backings.remove(name_arena)
            name_arena.state = _AuxiliaryState.CLOSED
            name_arena.overlay = None
            name_arena.native_base = 0
            name_arena.storage = bytearray()
            record.rollback_calls.remove(call)
            frame.arena_refs = (record.control,)
            frame.phase = _CallPhase.ACKNOWLEDGED
            call.preimage = b""
            call.return_value = None
            call.error = None
        else:
            cleanup = outcome
            frame.phase = _CallPhase.UNKNOWN
    except BaseException as secondary:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
        call.cleanup_error = secondary
        _retain_unknown(record, call, primary)
        cleanup = AcquisitionCloseOutcome(
            "unknown", (AcquisitionDiagnostic("RESOURCE_UNKNOWN", "close"),)
        )
    diagnostic = AcquisitionDiagnostic("OPEN_FAILED", frame.operation)
    row.diagnostic = diagnostic
    failure = AcquisitionError(diagnostic, cleanup)
    call.recognized_error = failure
    raise failure from None


def _open_owned_component(owner, parent, name, profile, disposition, descriptor=None):
    operation = "open_component"
    with _owner_domain(owner, operation) as record:
        row = _owned(record, parent, _OwnedAcquisition, record.acquisitions, operation)
        if row.state is not _AcquisitionState.CANDIDATE:
            _fail("CAPABILITY_REVOKED", operation)
        if row.profile not in {
            _AcquireProfile.ANCHOR_CANDIDATE,
            _AcquireProfile.PARENT_EXISTING,
            _AcquireProfile.PARENT_CREATE_FILE,
            _AcquireProfile.PARENT_CREATE_DOMAIN,
        }:
            _fail("CAPABILITY_INVALID", operation)
        if (
            type(profile) is not _AcquireProfile
            or profile is _AcquireProfile.ANCHOR_CANDIDATE
        ):
            _fail("PROFILE_INVALID", operation)
        creating = profile in {
            _AcquireProfile.CREATE_FILE,
            _AcquireProfile.CREATE_DIRECTORY,
        }
        if type(disposition) is not _Disposition or disposition is not (
            _Disposition.CREATE_NEW if creating else _Disposition.OPEN_EXISTING
        ):
            _fail("DISPOSITION_INVALID", operation)
        if descriptor is not None and not creating:
            _fail("DESCRIPTOR_INVALID", operation)
        if creating:
            role = (
                _NewObjectRole.FILE_JOURNAL
                if profile is _AcquireProfile.CREATE_FILE
                else _NewObjectRole.DIRECTORY_DOMAIN
            )
            descriptor_row = (
                record.descriptors.get(descriptor)
                if type(descriptor) is _ClosedDescriptor
                else None
            )
            if (
                descriptor_row is None
                or descriptor_row.capability is not descriptor
                or descriptor_row.owner_ref is not owner
                or descriptor_row.role is not role
                or descriptor_row.state is not _AuxiliaryState.LIVE
            ):
                _fail("DESCRIPTOR_INVALID", operation)
            guard = record.admitted_parents.get(parent)
            if (
                record.source != "cpu_double"
                or type(guard) is not _CpuParentAdmission
                or guard.owner_ref is not owner
                or guard.parent_ref is not parent
                or guard.role is not role
            ):
                # K4b no ha liberado un emisor nominal. Nunca adoptar un guard CPU,
                # SID, bool o path como una admisión S1 nativa.
                _fail("SECURITY_UNACCREDITED", operation)
        return _open(
            record,
            parent,
            _component_bytes(name, operation),
            profile,
            disposition,
            descriptor,
        )


def _close_acquisition(owner, acquisition):
    record = _owner_record(owner, "close")
    with _io._NATIVE_BOUNDARY_LOCK, record.lock:
        row = _owned(
            record, acquisition, _OwnedAcquisition, record.acquisitions, "close"
        )
        if row.outcome is not None:
            return row.outcome
        if _io._KERNEL_POISONED:
            row.outcome = AcquisitionCloseOutcome(
                "unknown", (AcquisitionDiagnostic("OWNER_RETIRE_REQUIRED", "close"),)
            )
            return row.outcome
        if row.child_pins:
            revoked = {row.capability}
            for descendant in record.acquisitions.values():
                if descendant.capability in revoked or descendant.parent_ref in revoked:
                    revoked.add(descendant.capability)
                    if descendant.state is _AcquisitionState.CANDIDATE:
                        descendant.state = _AcquisitionState.REVOKED
            _fail("CAPABILITY_IN_USE", "close")
        with _io._kernel_domain() as boundary:
            outcome = _close_registered_acquisition(record, row, owner, boundary)
            if outcome.state == "closed":
                _compact_completed_pin_frames(record, "close")
            return outcome


def _close_registered_acquisition(record, row, owner, boundary):
    before_handles = record.handles
    before_parent_pins = (
        record.acquisitions[row.parent_ref].child_pins
        if row.parent_ref is not None
        else None
    )
    row.state = _AcquisitionState.CLOSING
    reserved = AcquisitionCloseOutcome(
        "unknown", (AcquisitionDiagnostic("RESOURCE_UNKNOWN", "close"),)
    )
    row.outcome = reserved
    frame = _AcquisitionCallFrame(
        owner,
        "close",
        slot_index=row.slot_index,
        record_ref=row,
        arena_refs=(record.control,),
        boundary_lease_ref=boundary,
    )
    call = _AcquisitionCallRecord(frame, bytes(record.control.storage))
    frame.call_record_ref = call
    record.inflight.append(call)
    try:
        _begin_call_pin(record, frame)
        row.native_close_attempted = True
        frame.phase = _CallPhase.ENTERED
        call.return_value = record.ops.close(frame)
        frame.phase = _CallPhase.RETURNED
        _finish_call_pin(record, frame)
        result = call.return_value
        raw = struct.unpack_from(
            "<i",
            record.control.storage,
            record.control.aligned_offset + 7168 + row.slot_index * 4,
        )[0]
        if (
            type(result) is not _NativeCloseCompletion
            or type(result.success) is not bool
            or result.success is not True
            or result.win32_error is not None
            or raw == 0
        ):
            raise ValueError("CLOSE_COMPLETION_UNKNOWN")
        frame.phase = _CallPhase.COMPLETED
        outcome = AcquisitionCloseOutcome("closed")
        record.handles -= 1
        if row.parent_ref is not None:
            record.acquisitions[row.parent_ref].child_pins -= 1
        record.inflight.remove(call)
        frame.phase = _CallPhase.ACKNOWLEDGED
        row.state = _AcquisitionState.CLOSED
        row.outcome = outcome
        return outcome
    except BaseException as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
        if (
            error is call.recognized_error
            and frame.phase is _CallPhase.RESERVED
            and not row.native_close_attempted
        ):
            return reserved
        record.handles = before_handles
        if before_parent_pins is not None:
            record.acquisitions[row.parent_ref].child_pins = before_parent_pins
        if call not in record.inflight:
            record.inflight.append(call)
        row.outcome = reserved
        _retain_unknown(record, call, error)
        return reserved


def _close_acquisition_owner(owner):
    record = _owner_record(owner, "owner_close")
    with _io._NATIVE_BOUNDARY_LOCK, record.lock:
        if record.outcome is not None:
            return record.outcome
        record.outcome = AcquisitionCloseOutcome(
            "unknown", (AcquisitionDiagnostic("RESOURCE_UNKNOWN", "owner_close"),)
        )
        if record.inflight:
            record.state = _OwnerState.UNKNOWN
            return record.outcome
        record.state = _OwnerState.CLOSING
        for row in record.acquisitions.values():
            if row.state is _AcquisitionState.CANDIDATE:
                row.state = _AcquisitionState.REVOKED
        for row in reversed(tuple(record.acquisitions.values())):
            if row.state in {_AcquisitionState.CLOSED, _AcquisitionState.FAILED}:
                continue
            if (
                row.parent_ref is not None
                and record.acquisitions[row.parent_ref].slot_index >= row.slot_index
            ):
                with _io._REGISTRY_LOCK:
                    _io._KERNEL_POISONED = True
                record.state = _OwnerState.UNKNOWN
                return record.outcome
            outcome = _close_acquisition(owner, row.capability)
            if outcome.state != "closed":
                record.state = _OwnerState.UNKNOWN
                return record.outcome
        for row in record.locators.values():
            row.state = _AuxiliaryState.CLOSED
            row.arena_refs = ()
            row.root_dos = row.guid = row.target = row.nt_name = ""
        for row in record.descriptors.values():
            row.state = _AuxiliaryState.CLOSED
            row.arena = None
            row.getter_outputs = ()
        for arena in record.backings:
            arena.state = _AuxiliaryState.CLOSED
            arena.overlay = None
            arena.native_base = 0
            arena.storage = bytearray()
        record.backings.clear()
        record.control = None
        record.ops = None
        record.state = _OwnerState.CLOSED
        record.outcome = AcquisitionCloseOutcome("closed")
        with _io._REGISTRY_LOCK:
            _CLOSED_ACQUISITION_OWNERS[owner] = record
            _LIVE_ACQUISITION_OWNERS.pop(owner, None)
        return record.outcome


def _new_native_acquisition_owner(admission):
    if type(admission) is not _identity._AcquisitionAdmission:
        _fail("ADMISSION_REQUIRED", "owner")
    try:
        with _io._kernel_domain():
            _identity._validate_current_admission(admission)
            _identity._require_canonical_identity_instance()
            if (
                os.name != "nt"
                or sys.platform != "win32"
                or sys.maxsize != 2**63 - 1
                or platform.machine().casefold() not in {"amd64", "x86_64"}
            ):
                _fail("PLATFORM_UNSUPPORTED", "owner")
            with _io._REGISTRY_LOCK:
                if _io._ACQUISITION_OWNERS_EMITTED >= 4:
                    _fail("ACQUISITION_LIMIT", "owner")
                admission_row = _io._IDENTITY_CAPABILITIES[admission]
            abi = importlib.import_module(".storage_journal_windows_abi", __package__)
            try:
                ops = abi._new_native_acquisition_backend()
            except Exception:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
                _fail("ABI_UNACCREDITED", "owner")
            owner = object.__new__(_AcquisitionOwner)
            record = _AcquisitionOwnerRecord(
                owner,
                os.getpid(),
                "native_windows_x64",
                ops,
                admission_row.principal_sid,
                admission_row.primary_group_sid,
                state=_OwnerState.BUILDING,
                admission_ref=admission,
                policy_ref=admission_row.policy_ref,
                epoch_ref=admission_row.epoch_ref,
            )
            with _io._REGISTRY_LOCK:
                _io._ACQUISITION_OWNERS_EMITTED += 1
                _io._ACQUISITION_CAPABILITY_CLASS = _AcquisitionOwner
                _LIVE_ACQUISITION_OWNERS[owner] = record
            with record.lock:
                _identity._bind_acquisition_owner(admission, owner=owner)
                _initialise_control(record)
                record.state = _OwnerState.LIVE
            return owner
    except _io.KernelMemoryError as error:
        _fail(error.diagnostic.code, "owner")
    except _identity.IdentityError as error:
        code = error.diagnostic.code
        _fail(
            code
            if code
            in {"ADMISSION_REQUIRED", "CAPABILITY_REVOKED", "OWNER_RETIRE_REQUIRED"}
            else "ADMISSION_REQUIRED",
            "owner",
        )


def _seed_cpu_parent_admission(owner, parent, *, role):
    with _owner_domain(owner, "open_component") as record:
        if record.source != "cpu_double" or type(role) is not _NewObjectRole:
            _fail("SECURITY_UNACCREDITED", "open_component")
        _owned(record, parent, _OwnedAcquisition, record.acquisitions, "open_component")
        record.admitted_parents[parent] = _CpuParentAdmission(owner, parent, role)


@dataclass(frozen=True)
class _CpuParentAdmission:
    owner_ref: object
    parent_ref: object
    role: _NewObjectRole


@dataclass(frozen=True)
class AcquisitionInfo:
    profile: str
    disposition: str
    state: str
    provenance: str

    def __post_init__(self):
        if (
            type(self.profile) is not str
            or self.profile not in {profile.value for profile in _AcquireProfile}
            or type(self.disposition) is not str
            or self.disposition not in {value.value for value in _Disposition}
            or type(self.state) is not str
            or self.state not in {"candidate", "revoked", "closed", "unknown"}
            or type(self.provenance) is not str
            or self.provenance not in {"cpu_double", "native_windows_x64"}
        ):
            raise ValueError("INFO_INVALID") from None


def _acquisition_info(owner, acquisition):
    record = _owner_record(owner, "info")
    with record.lock:
        row = _owned(
            record, acquisition, _OwnedAcquisition, record.acquisitions, "info"
        )
        if row.state not in {
            _AcquisitionState.CANDIDATE,
            _AcquisitionState.REVOKED,
            _AcquisitionState.CLOSED,
            _AcquisitionState.UNKNOWN,
        }:
            _fail("CAPABILITY_INVALID", "info")
        if row.state is _AcquisitionState.CANDIDATE:
            return row.info_snapshot
        return AcquisitionInfo(
            row.profile.value, row.disposition.value, row.state.value, record.source
        )


@dataclass
class _CallArena:
    owner_ref: object
    logical_length: int
    requested_bytes: int
    storage: bytearray
    native_base: int = 0
    segments: tuple = ()
    aligned_offset: int = 0
    state: _AuxiliaryState = _AuxiliaryState.LIVE
    overlay: object = None


@dataclass
class _AcquisitionOwnerRecord:
    capability: object
    pid: int
    source: str
    ops: object
    principal_sid: bytes
    primary_group_sid: bytes
    control: object = None
    state: _OwnerState = _OwnerState.LIVE
    lock: object = field(default_factory=threading.RLock)
    backings: list = field(default_factory=list)
    handles: int = 0
    next_slot: int = 0
    inflight: list = field(default_factory=list)
    rollback_calls: list = field(default_factory=list)
    locators: dict = field(default_factory=dict)
    descriptors: dict = field(default_factory=dict)
    admitted_parents: dict = field(default_factory=dict)
    acquisitions: dict = field(default_factory=dict)
    outcome: object = None
    admission_ref: object = None
    policy_ref: object = None
    epoch_ref: object = None
    boundary_lease_ref: object = None


_LIVE_ACQUISITION_OWNERS = _io._LIVE_ACQUISITION_OWNERS
_CLOSED_ACQUISITION_OWNERS = _io._CLOSED_ACQUISITION_OWNERS


@dataclass(frozen=True)
class _AcquisitionOps:
    open: object
    close: object
    locate: object
    descriptor: object


def _reserve_layouts(record, operation, plans):
    layouts = []
    for plan in plans:
        offset = 0
        segments = []
        for name, length, alignment in plan:
            offset = (offset + alignment - 1) & -alignment
            segments.append((name, offset, length, alignment))
            offset += length
        logical = (offset + 7) & ~7
        layouts.append((logical, logical + 7, tuple(segments)))
    if (
        len(record.backings) + len(layouts) > 8
        or any(requested > 131072 for _, requested, _ in layouts)
        or sum(arena.requested_bytes for arena in record.backings)
        + sum(layout[1] for layout in layouts)
        > 1048576
    ):
        _fail("ACQUISITION_LIMIT", operation)
    arenas = tuple(
        _CallArena(
            record.capability,
            logical,
            requested,
            bytearray(requested),
            segments=segments,
        )
        for logical, requested, segments in layouts
    )
    record.backings.extend(arenas)
    return arenas


def _assemble_cpu_acquisition_owner(ops, *, principal_sid, primary_group_sid):
    if type(ops) is not _AcquisitionOps or not all(
        callable(function)
        for function in (ops.open, ops.close, ops.locate, ops.descriptor)
    ):
        _fail("CAPABILITY_INVALID", "owner")
    for sid in (principal_sid, primary_group_sid):
        if (
            type(sid) is not bytes
            or len(sid) < 12
            or sid[0] != 1
            or not 1 <= sid[1] <= 15
            or len(sid) != 8 + sid[1] * 4
        ):
            _fail("PRINCIPAL_UNACCREDITED", "owner")
    with _io._NATIVE_BOUNDARY_LOCK, _io._REGISTRY_LOCK:
        if _io._KERNEL_POISONED:
            _fail("OWNER_RETIRE_REQUIRED", "owner")
        if _io._ACQUISITION_OWNERS_EMITTED >= 4:
            _fail("ACQUISITION_LIMIT", "owner")
        if (
            _io._ACQUISITION_CAPABILITY_CLASS is not None
            and _io._ACQUISITION_CAPABILITY_CLASS is not _AcquisitionOwner
            and _LIVE_ACQUISITION_OWNERS
        ):
            _io._KERNEL_POISONED = True
            _fail("OWNER_RETIRE_REQUIRED", "owner")
        _io._ACQUISITION_CAPABILITY_CLASS = _AcquisitionOwner
        _io._ACQUISITION_OWNERS_EMITTED += 1
    owner = object.__new__(_AcquisitionOwner)
    record = _AcquisitionOwnerRecord(
        owner, os.getpid(), "cpu_double", ops, principal_sid, primary_group_sid
    )
    with _io._REGISTRY_LOCK:
        _LIVE_ACQUISITION_OWNERS[owner] = record
    _initialise_control(record)
    return owner


def _initialise_control(record):
    record.control = _CallArena(
        record.capability,
        10240,
        10247,
        bytearray(10247),
        segments=((_SegmentName.CONTROL, 0, 10240, 8),),
    )
    record.control.storage[9216 : 9216 + len(record.principal_sid)] = (
        record.principal_sid
    )
    record.control.storage[9284 : 9284 + len(record.primary_group_sid)] = (
        record.primary_group_sid
    )
    struct.pack_into(
        "<II",
        record.control.storage,
        9488,
        len(record.principal_sid),
        len(record.primary_group_sid),
    )
    record.backings.append(record.control)


@contextmanager
def _owner_pin_boundary(owner):
    """Frontera metadata del owner antes de ENTRY; no ejecuta backend K2."""
    with _owner_domain(owner, "owner") as record:
        if record.inflight:
            _fail("ACQUISITION_LIMIT", "owner")
        frame = _AcquisitionCallFrame(
            owner,
            "owner",
            arena_refs=(record.control,),
            boundary_lease_ref=record.boundary_lease_ref,
        )
        call = _AcquisitionCallRecord(
            frame, bytes(record.control.storage), charge=(1, 10247, 0)
        )
        record.inflight.append(call)
        try:
            yield frame
        finally:
            if frame.admission_pin is None and frame.phase is _CallPhase.RESERVED:
                record.inflight.remove(call)
            elif (
                type(frame.admission_pin) is _CpuAdmissionPin
                and frame.phase is _CallPhase.RESERVED
            ):
                source = next(
                    (
                        source
                        for source in _identity._CPU_AUTHORITIES.values()
                        if frame.admission_pin in source.pins
                    ),
                    None,
                )
                if source is not None and source.pins[frame.admission_pin].state in {
                    "completed",
                    "aborted",
                    "revoked",
                }:
                    record.inflight.remove(call)
            elif (
                type(frame.admission_pin) is _identity._AdmissionPin
                and frame.phase is _CallPhase.RESERVED
            ):
                with _io._REGISTRY_LOCK:
                    pin_row = _io._IDENTITY_CAPABILITIES.get(frame.admission_pin)
                if (
                    type(pin_row) is _identity._AdmissionPinRecord
                    and pin_row.target_frame_ref is frame
                    and pin_row.state in {"completed", "aborted", "revoked"}
                ):
                    record.inflight.remove(call)
