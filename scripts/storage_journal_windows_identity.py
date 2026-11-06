"""Principal privado Windows; no concede autoridad sobre archivos."""

import importlib
import os
import platform
import struct
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum

from . import storage_journal_windows_io as _io

_MODULE_INSTANCE = sys.modules[__name__]


class _AdmissionScope(Enum):
    CANDIDATE_READ_ONLY = "CANDIDATE_READ_ONLY"
    PRODUCT_CHAIN_CANDIDATE = "PRODUCT_CHAIN_CANDIDATE"
    OWNED_PROBE_CANDIDATE = "OWNED_PROBE_CANDIDATE"


class _Opaque:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("CAPABILITY_INVALID") from None

    def __reduce_ex__(self, protocol):
        raise TypeError("CAPABILITY_INVALID") from None

    def __repr__(self):
        return "<" + type(self).__name__ + ">"


class _CpuDeployerAuthority(_Opaque):
    __slots__ = ()


class _CpuAdmission(_Opaque):
    __slots__ = ()


class _CpuIssuer(_Opaque):
    __slots__ = ()


class _CpuSecurityPolicy(_Opaque):
    __slots__ = ()


class _CpuPolicyEpoch(_Opaque):
    __slots__ = ()


class _DeployerAuthority(_Opaque):
    __slots__ = ()


class _IdentitySession(_Opaque):
    __slots__ = ()


class _NativeIssuer(_Opaque):
    __slots__ = ()


class _EffectivePrincipalObservation(_Opaque):
    __slots__ = ()


class _SecurityPolicy(_Opaque):
    __slots__ = ()


class _PolicyEpoch(_Opaque):
    __slots__ = ()


class _AcquisitionAdmission(_Opaque):
    __slots__ = ()


class _AdmissionPin(_Opaque):
    __slots__ = ()


@dataclass(frozen=True)
class _CpuIdentityOps:
    execute: object


@dataclass(frozen=True)
class _IdentityOps:
    execute: object


@dataclass
class _CpuAuthorityRecord:
    capability: _CpuDeployerAuthority
    ops: _CpuIdentityOps
    principal_sid: bytes
    primary_group_sid: bytes
    pid: int
    source: str = "cpu_double"
    state: str = "live"
    admissions: dict = field(default_factory=dict)
    token_stamp: object = None
    calls: list = field(default_factory=list)
    frame: object = None
    counters: dict = field(default_factory=lambda: {"observations": 0, "subcalls": 0})
    threads: dict = field(default_factory=dict)
    issuer_ref: object = None
    policy_ref: object = None
    epoch_ref: object = None
    lock: object = field(default_factory=threading.RLock)
    pins: dict = field(default_factory=dict)
    owner_refs: dict = field(default_factory=dict)
    pin_slots_reserved: int = 0


_CPU_AUTHORITIES = {}
_CPU_CAPABILITIES = {}


@dataclass
class _CpuRootRecord:
    capability: object
    authority_ref: object
    pid: int
    source: str = "cpu_double"
    doctrine: str = "storage-nt-security-s1"
    state: str = "live"


def _sid_bytes(data):
    if type(data) is not bytes or not 12 <= len(data) <= 68:
        raise ValueError("PRINCIPAL_UNACCREDITED") from None
    if data[0] != 1 or not 1 <= data[1] <= 15 or len(data) != 8 + 4 * data[1]:
        raise ValueError("PRINCIPAL_UNACCREDITED") from None
    return data


def _assemble_cpu_identity_session(ops, *, principal_sid, primary_group_sid):
    if type(ops) is not _CpuIdentityOps or not callable(ops.execute):
        raise ValueError("CAPABILITY_INVALID") from None
    principal_sid, primary_group_sid = (
        _sid_bytes(principal_sid),
        _sid_bytes(primary_group_sid),
    )
    authority = object.__new__(_CpuDeployerAuthority)
    _CPU_AUTHORITIES[authority] = _CpuAuthorityRecord(
        authority, ops, principal_sid, primary_group_sid, os.getpid()
    )
    record = _CPU_AUTHORITIES[authority]
    record.issuer_ref = object.__new__(_CpuIssuer)
    record.policy_ref = object.__new__(_CpuSecurityPolicy)
    record.epoch_ref = object.__new__(_CpuPolicyEpoch)
    for capability in (record.issuer_ref, record.policy_ref, record.epoch_ref):
        _CPU_CAPABILITIES[capability] = _CpuRootRecord(
            capability, authority, os.getpid()
        )
    return authority


def _bootstrap_current_deployer():
    if not (
        os.name == "nt"
        and sys.platform == "win32"
        and sys.maxsize == 2**63 - 1
        and platform.machine().casefold() in {"amd64", "x86_64"}
    ):
        _fail("PLATFORM_UNSUPPORTED", "bootstrap")
    _require_canonical_identity_instance()
    return _bootstrap_native()


def _require_canonical_identity_instance():
    if (
        sys.modules.get("scripts.storage_journal_windows_identity")
        is not _MODULE_INSTANCE
        or sys.modules.get("scripts.storage_journal_windows_io") is not _io
    ):
        _fail("OWNER_RETIRE_REQUIRED", "bootstrap")


def _validate_current_admission(admission):
    if type(admission) is not _AcquisitionAdmission:
        _fail("ADMISSION_REQUIRED", "issue")
    with _io._REGISTRY_LOCK:
        row = _io._IDENTITY_CAPABILITIES.get(admission)
    if type(row) is not _AdmissionRecord or row.capability is not admission:
        _fail("ADMISSION_REQUIRED", "issue")
    authority, session = _authority_record(row.principal_ratification_ref, "issue")
    _native_live(session, "issue")
    if (
        row.pid != os.getpid()
        or row.source != "native_windows_x64"
        or row.issuer_ref is not authority.issuer_ref
        or row.policy_ref is not authority.policy_ref
        or row.epoch_ref is not authority.epoch_ref
        or row.state != "live"
        or row.scope
        not in {
            _AdmissionScope.CANDIDATE_READ_ONLY,
            _AdmissionScope.PRODUCT_CHAIN_CANDIDATE,
        }
        or row.principal_sid != authority.principal_sid
        or row.primary_group_sid != authority.primary_group_sid
        or row.effective_context_ref not in session.observations
    ):
        _fail("CAPABILITY_REVOKED", "issue")


def _bind_acquisition_owner(admission, *, owner):
    if type(admission) is not _AcquisitionAdmission:
        _fail("ADMISSION_REQUIRED", "pin")
    _validate_current_admission(admission)
    acquisition = importlib.import_module(
        ".storage_journal_windows_acquisition", __package__
    )
    owner_row = acquisition._owner_record(owner, "owner")
    if (
        owner_row.source != "native_windows_x64"
        or owner_row.state is not acquisition._OwnerState.BUILDING
        or owner_row.admission_ref is not admission
        or not owner_row.lock._is_owned()
        or not _io._NATIVE_BOUNDARY_LOCK._is_owned()
    ):
        _fail("CAPABILITY_INVALID", "pin")
    with _io._REGISTRY_LOCK:
        admission_row = _io._IDENTITY_CAPABILITIES[admission]
    authority, session = _authority_record(
        admission_row.principal_ratification_ref, "pin"
    )
    with session.lock:
        _validate_current_admission(admission)
        if owner in session.owner_refs:
            _fail("CAPABILITY_INVALID", "pin")
        if len(session.owner_refs) >= 4:
            _fail("OWNER_RETIRE_REQUIRED", "pin")
        if (
            owner_row.pid != session.pid
            or owner_row.principal_sid != authority.principal_sid
            or owner_row.primary_group_sid != authority.primary_group_sid
            or owner_row.policy_ref is not session.policy_ref
            or owner_row.epoch_ref is not session.epoch_ref
        ):
            _fail("CAPABILITY_INVALID", "pin")
        session.owner_refs[owner] = owner_row


def _bind_cpu_acquisition_owner(admission, *, owner):
    if type(admission) is not _CpuAdmission:
        _fail("ADMISSION_REQUIRED", "pin")
    source = next(
        (
            record
            for record in _CPU_AUTHORITIES.values()
            if admission in record.admissions
        ),
        None,
    )
    if source is None:
        _fail("ADMISSION_REQUIRED", "pin")
    acquisition, owner_row, _ = _acquisition_pin_target(owner, "pin")
    if (
        owner_row.source != "cpu_double"
        or owner_row.state is not acquisition._OwnerState.LIVE
        or owner_row.admission_ref is not None
    ):
        _fail("CAPABILITY_INVALID", "pin")
    with source.lock:
        _cpu_admission_current(source, admission, "pin")
        if (
            owner_row.principal_sid != source.principal_sid
            or owner_row.primary_group_sid != source.primary_group_sid
        ):
            _fail("PRINCIPAL_UNACCREDITED", "pin")
        owner_row.admission_ref = admission
        owner_row.policy_ref = source.policy_ref
        owner_row.epoch_ref = source.epoch_ref
        source.owner_refs[owner] = owner_row


def _pin_current_acquisition_admission(admission, *, owner):
    if type(admission) is not _AcquisitionAdmission:
        _fail("ADMISSION_REQUIRED", "pin")
    _validate_current_admission(admission)
    acquisition, owner_row, frame = _acquisition_pin_target(owner, "pin")
    with _io._REGISTRY_LOCK:
        admission_row = _io._IDENTITY_CAPABILITIES[admission]
    authority, session = _authority_record(
        admission_row.principal_ratification_ref, "pin"
    )
    if (
        owner_row.source != "native_windows_x64"
        or session.owner_refs.get(owner) is not owner_row
        or owner_row.admission_ref is not admission
        or owner_row.policy_ref is not session.policy_ref
        or owner_row.epoch_ref is not session.epoch_ref
    ):
        _fail("CAPABILITY_INVALID", "pin")
    if (
        owner_row.state
        not in {acquisition._OwnerState.LIVE, acquisition._OwnerState.CLOSING}
        or frame.phase is not acquisition._CallPhase.RESERVED
        or frame.admission_pin is not None
    ):
        _fail("CAPABILITY_REVOKED", "pin")
    if owner_row.state is acquisition._OwnerState.CLOSING and frame.operation not in {
        "close",
        "owner",
    }:
        _fail("CAPABILITY_REVOKED", "pin")
    _pin_scope(admission_row.scope, frame, acquisition, "pin")
    session.lock.acquire()
    registered = False
    try:
        _validate_current_admission(admission)
        counters = session.counters
        if (
            type(session.pin_slots_reserved) is not int
            or not 0 <= session.pin_slots_reserved < 2048
            or set(counters) != {"observations", "subcalls"}
            or any(type(v) is not int or v < 0 for v in counters.values())
            or counters["observations"] > 8190
            or counters["subcalls"] > 229376 - 56
            or any(
                row.state in {"reserved", "active", "unknown"}
                for row in session.pins.values()
            )
        ):
            _revoke_session(session)
            _fail("OWNER_RETIRE_REQUIRED", "pin")
        pin = object.__new__(_AdmissionPin)
        row = _AdmissionPinRecord(
            pin,
            admission,
            owner,
            session.capability,
            os.getpid(),
            threading.current_thread(),
            threading.get_native_id(),
            None,
            None,
            "reserved",
            frame,
            session.issuer_ref,
            authority.principal_sid,
            authority.primary_group_sid,
            session.policy_ref,
            session.epoch_ref,
            frame.boundary_lease_ref,
        )
        session.pins[pin] = row
        _register_identity(pin, row)
        session.pin_slots_reserved += 1
        frame.admission_pin = pin
        registered = True
        observation = _observe_current_effective_principal(session.capability)
        row.pre_observation_ref = observation
        observed = session.observations[observation]
        if (
            observed.principal_sid != authority.principal_sid
            or observed.primary_group_sid != authority.primary_group_sid
            or observed.token_stamp != authority.token_stamp
        ):
            _revoke_session(session)
            row.state = "revoked"
            session.lock.release()
            _fail("PRINCIPAL_UNACCREDITED", "pin")
        row.state = "active"
        return pin
    except BaseException as error:
        if not registered:
            session.lock.release()
            raise
        if row.state == "revoked":
            raise
        observed = next(reversed(session.observations.values()), None)
        if (
            observed is not None
            and _finished_custody_error(session, observed.frame_ref, error)
            and session.state != "unknown"
            and not _io._KERNEL_POISONED
        ):
            row.state = "revoked"
            session.lock.release()
            raise
        row.state = "unknown"
        row.error = error
        _native_poison(session, error)
        if (
            observed is not None
            and _finished_custody_error(session, observed.frame_ref, error)
            and error.cleanup is not None
        ):
            _fail(
                error.diagnostic.code,
                "pin",
                error.diagnostic.win32_error,
                cleanup=error.cleanup,
            )
        _fail("RESOURCE_UNKNOWN", "pin")


def _complete_acquisition_admission_pin(pin, *, owner):
    row, session = _native_pin_record(pin, owner, "complete")
    if row.state == "completed":
        return
    acquisition, _, frame = _acquisition_pin_target(owner, "complete")
    if (
        row.state != "active"
        or frame is not row.target_frame_ref
        or not session.lock._is_owned()
        or frame.phase is not acquisition._CallPhase.RETURNED
    ):
        _fail("CAPABILITY_INVALID", "complete")
    query_started = False
    recognized_error = None
    try:
        _validate_current_admission(row.admission_ref)
        with _io._REGISTRY_LOCK:
            admission = _io._IDENTITY_CAPABILITIES[row.admission_ref]
        authority, _ = _authority_record(
            admission.principal_ratification_ref, "complete"
        )
        owner_row = acquisition._owner_record(owner, "info")
        if (
            session.owner_refs.get(owner) is not owner_row
            or owner_row.admission_ref is not row.admission_ref
            or owner_row.policy_ref is not row.policy_ref
            or owner_row.epoch_ref is not row.epoch_ref
            or row.boundary_lease_ref is not frame.boundary_lease_ref
        ):
            _fail("CAPABILITY_INVALID", "complete")
        _pin_scope(admission.scope, frame, acquisition, "complete")
        pre = session.observations.get(row.pre_observation_ref)
        if (
            type(pre) is not _EffectiveObservationRecord
            or pre.capability is not row.pre_observation_ref
            or pre.state != "live"
            or pre.session_ref is not session.capability
            or pre.issuer_ref is not row.issuer_ref
        ):
            _fail("CAPABILITY_INVALID", "complete")
        query_started = True
        observation = _observe_current_effective_principal(session.capability)
        row.post_observation_ref = observation
        observed = session.observations[observation]
        if (
            observed.principal_sid != pre.principal_sid
            or observed.primary_group_sid != pre.primary_group_sid
            or observed.token_stamp != pre.token_stamp
            or observed.principal_sid != authority.principal_sid
            or observed.primary_group_sid != authority.primary_group_sid
            or observed.token_stamp != authority.token_stamp
        ):
            _revoke_session(session)
            row.state = "revoked"
            session.lock.release()
            recognized_error = IdentityError(
                IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "complete")
            )
            raise recognized_error from None
        _validate_current_admission(row.admission_ref)
        _pin_scope(admission.scope, frame, acquisition, "complete")
        row.state = "completed"
        session.lock.release()
    except BaseException as error:  # custodia fuerte de outputs y leases
        if error is recognized_error:
            raise
        observed = next(reversed(session.observations.values()), None)
        if (
            type(error) is IdentityError
            and (
                not query_started
                or (
                    observed is not None
                    and _finished_custody_error(session, observed.frame_ref, error)
                )
            )
            and session.state != "unknown"
            and not _io._KERNEL_POISONED
        ):
            _revoke_session(session)
            row.state = "revoked"
            session.lock.release()
            raise
        row.state = "unknown"
        row.error = error
        _native_poison(session, error)
        if type(error) is IdentityError and error.cleanup is not None:
            _fail(error.diagnostic.code, "complete", cleanup=error.cleanup)
        _fail("RESOURCE_UNKNOWN", "complete")


def _abort_acquisition_admission_pin(pin, *, owner):
    row, session = _native_pin_record(pin, owner, "complete")
    if row.state == "aborted":
        return
    acquisition, _, frame = _acquisition_pin_target(owner, "complete")
    if (
        row.state != "active"
        or frame is not row.target_frame_ref
        or not session.lock._is_owned()
        or frame.phase is not acquisition._CallPhase.RESERVED
    ):
        _fail("CAPABILITY_INVALID", "complete")
    row.state = "aborted"
    session.lock.release()


def _validate_acquisition_backend_pin(pin, *, owner, frame):
    row, session = _native_pin_record(pin, owner, "pin")
    acquisition, owner_row, target = _acquisition_pin_target(owner, "pin")
    if (
        target is not frame
        or row.target_frame_ref is not frame
        or frame.admission_pin is not pin
        or frame.phase is not acquisition._CallPhase.ENTERED
        or row.state != "active"
        or not session.lock._is_owned()
        or row.boundary_lease_ref is not frame.boundary_lease_ref
    ):
        _fail("CAPABILITY_INVALID", "pin")
    if (
        owner_row.source != "native_windows_x64"
        or session.owner_refs.get(owner) is not owner_row
        or owner_row.admission_ref is not row.admission_ref
        or owner_row.policy_ref is not row.policy_ref
        or owner_row.epoch_ref is not row.epoch_ref
    ):
        _fail("CAPABILITY_INVALID", "pin")
    if (
        owner_row.state
        not in {acquisition._OwnerState.LIVE, acquisition._OwnerState.CLOSING}
        or (
            owner_row.state is acquisition._OwnerState.CLOSING
            and frame.operation != "close"
        )
        or frame.operation
        not in {"locate", "descriptor", "open_anchor", "open_component", "close"}
    ):
        _fail("CAPABILITY_REVOKED", "pin")
    _validate_current_admission(row.admission_ref)
    with _io._REGISTRY_LOCK:
        admission = _io._IDENTITY_CAPABILITIES[row.admission_ref]
    _pin_scope(admission.scope, frame, acquisition, "pin")
    observed = session.observations.get(row.pre_observation_ref)
    authority, _ = _authority_record(admission.principal_ratification_ref, "pin")
    if (
        type(observed) is not _EffectiveObservationRecord
        or observed.capability is not row.pre_observation_ref
        or observed.state != "live"
        or observed.session_ref is not session.capability
        or observed.issuer_ref is not row.issuer_ref
        or observed.principal_sid != row.principal_sid
        or observed.primary_group_sid != row.primary_group_sid
        or observed.token_stamp != authority.token_stamp
    ):
        _fail("PRINCIPAL_UNACCREDITED", "pin")


def _native_pin_record(pin, owner, operation):
    if type(pin) is not _AdmissionPin:
        _fail("ADMISSION_REQUIRED", operation)
    with _io._REGISTRY_LOCK:
        row = _io._IDENTITY_CAPABILITIES.get(pin)
    if type(row) is not _AdmissionPinRecord or row.capability is not pin:
        _fail("ADMISSION_REQUIRED", operation)
    _pin_thread_owner(row, owner, operation)
    try:
        session = _io._registered_native_session(row.session_ref)
    except _io.KernelMemoryError:
        _fail("CAPABILITY_INVALID", operation)
    if (
        session.pins.get(pin) is not row
        or row.issuer_ref is not session.issuer_ref
        or row.policy_ref is not session.policy_ref
        or row.epoch_ref is not session.epoch_ref
    ):
        _fail("CAPABILITY_INVALID", operation)
    return row, session


def _pin_cpu_acquisition_admission(admission, *, owner):
    if type(admission) is not _CpuAdmission:
        _fail("ADMISSION_REQUIRED", "pin")
    source = next(
        (
            record
            for record in _CPU_AUTHORITIES.values()
            if admission in record.admissions
        ),
        None,
    )
    if source is None:
        _fail("ADMISSION_REQUIRED", "pin")
    acquisition, owner_row, frame = _acquisition_pin_target(owner, "pin")
    admission_row = _cpu_admission_current(source, admission, "pin")
    _pin_scope(admission_row.scope, frame, acquisition, "pin")
    if (
        source.pin_slots_reserved >= 2048
        or source.counters["observations"] > 8190
        or source.counters["subcalls"] > 229376 - 56
        or any(row.state in {"reserved", "active"} for row in source.pins.values())
    ):
        _revoke_cpu_pin_source(source)
        _fail("OWNER_RETIRE_REQUIRED", "pin")
    source.lock.acquire()
    pin = object.__new__(acquisition._CpuAdmissionPin)
    row = _CpuAdmissionPinRecord(
        pin,
        admission,
        owner,
        source.capability,
        os.getpid(),
        threading.current_thread(),
        threading.get_native_id(),
        None,
        None,
        "reserved",
        frame,
    )
    source.pins[pin] = row
    source.pin_slots_reserved += 1
    source.owner_refs[owner] = owner_row
    frame.admission_pin = pin
    try:
        observed = _cpu_observe(source)
        if observed != (
            admission_row.principal_sid,
            admission_row.primary_group_sid,
            source.token_stamp,
        ):
            _revoke_cpu_pin_source(source)
            row.state = "revoked"
            source.lock.release()
            _fail("PRINCIPAL_UNACCREDITED", "pin")
        row.pre_observation_ref = observed
        row.state = "active"
        frame.admission_pin = pin
        return pin
    except IdentityError:
        raise
    except BaseException:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
        row.state = "unknown"
        _poison_cpu(source)
        _fail("RESOURCE_UNKNOWN", "pin")


def _complete_cpu_acquisition_admission_pin(pin, *, owner):
    source = next(
        (record for record in _CPU_AUTHORITIES.values() if pin in record.pins), None
    )
    if source is None:
        _fail("ADMISSION_REQUIRED", "complete")
    row = source.pins[pin]
    _pin_thread_owner(row, owner, "complete")
    if row.state == "completed":
        return
    _acquisition, _owner_row, frame = _acquisition_pin_target(owner, "complete")
    if (
        frame is not row.target_frame_ref
        or not source.lock._is_owned()
        or row.state != "active"
        or (
            type(_owner_row.admission_ref) is _CpuAdmission
            and frame.phase is not _acquisition._CallPhase.RETURNED
        )
    ):
        _fail("CAPABILITY_INVALID", "complete")
    admission = _cpu_admission_current(source, row.admission_ref, "complete")
    try:
        observed = _cpu_observe(source)
        row.post_observation_ref = observed
        if observed != row.pre_observation_ref or observed != (
            admission.principal_sid,
            admission.primary_group_sid,
            source.token_stamp,
        ):
            _revoke_cpu_pin_source(source)
            row.state = "revoked"
            source.lock.release()
            _fail("PRINCIPAL_UNACCREDITED", "complete")
        row.state = "completed"
        source.lock.release()
    except IdentityError:
        raise
    except BaseException:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
        row.state = "unknown"
        _poison_cpu(source)
        _fail("RESOURCE_UNKNOWN", "complete")


def _abort_cpu_acquisition_admission_pin(pin, *, owner):
    source = next(
        (record for record in _CPU_AUTHORITIES.values() if pin in record.pins), None
    )
    if source is None:
        _fail("ADMISSION_REQUIRED", "complete")
    row = source.pins[pin]
    _pin_thread_owner(row, owner, "complete")
    if row.state == "aborted":
        return
    acquisition, _, frame = _acquisition_pin_target(owner, "complete")
    if (
        frame is not row.target_frame_ref
        or frame.phase is not acquisition._CallPhase.RESERVED
        or row.state != "active"
        or not source.lock._is_owned()
    ):
        _fail("CAPABILITY_INVALID", "complete")
    row.state = "aborted"
    source.lock.release()


@dataclass
class _CpuAdmissionPinRecord:
    capability: object
    admission_ref: object
    owner_ref: object
    session_ref: object
    pid: int
    thread_ref: object
    thread_id: int
    pre_observation_ref: object
    post_observation_ref: object
    state: str
    target_frame_ref: object


@dataclass
class _AdmissionPinRecord(_CpuAdmissionPinRecord):
    issuer_ref: object
    principal_sid: bytes
    primary_group_sid: bytes
    policy_ref: object
    epoch_ref: object
    boundary_lease_ref: object
    error: object = None


def _acquisition_pin_target(owner, operation):
    acquisition = importlib.import_module(
        ".storage_journal_windows_acquisition", __package__
    )
    try:
        record = acquisition._owner_record(owner, "locate")
    except acquisition.AcquisitionError:
        _fail("CAPABILITY_INVALID", operation)
    if (
        not record.lock._is_owned()
        or not _io._NATIVE_BOUNDARY_LOCK._is_owned()
        or len(record.inflight) != 1
    ):
        _fail("CAPABILITY_INVALID", operation)
    call = record.inflight[0]
    if (
        type(call) is not acquisition._AcquisitionCallRecord
        or type(call.frame) is not acquisition._AcquisitionCallFrame
    ):
        _fail("CAPABILITY_INVALID", operation)
    frame = call.frame
    if frame.owner_ref is not owner:
        _fail("OWNER_MISMATCH", operation)
    with _io._REGISTRY_LOCK:
        binding = _io._BOUNDARY_LEASES.get(frame.boundary_lease_ref)
    if type(frame.boundary_lease_ref) is not _io._KernelBoundaryLease or binding != (
        os.getpid(),
        threading.current_thread(),
        threading.get_native_id(),
    ):
        _fail("CAPABILITY_INVALID", operation)
    if record.source not in {"cpu_double", "native_windows_x64"}:
        _fail("CAPABILITY_INVALID", operation)
    return acquisition, record, frame


def _pin_scope(scope, frame, acquisition, operation):
    if (
        type(scope) is not _AdmissionScope
        or scope is _AdmissionScope.OWNED_PROBE_CANDIDATE
    ):
        _fail("ADMISSION_REQUIRED", operation)
    if scope is _AdmissionScope.CANDIDATE_READ_ONLY and frame.operation in {
        "open_anchor",
        "open_component",
    }:
        profile = frame.record_ref.profile if frame.record_ref is not None else None
        if profile not in {
            acquisition._AcquireProfile.ANCHOR_CANDIDATE,
            acquisition._AcquireProfile.PARENT_EXISTING,
            acquisition._AcquireProfile.READ_EXISTING,
        }:
            _fail("ADMISSION_REQUIRED", operation)


def _cpu_admission_current(source, admission, operation):
    row = source.admissions.get(admission)
    if (
        type(row) is not _AdmissionRecord
        or row.capability is not admission
        or row.source != "cpu_double"
        or source.source != "cpu_double"
        or source.pid != os.getpid()
    ):
        _fail("ADMISSION_REQUIRED", operation)
    if source.state != "live" or row.state != "live":
        _fail("CAPABILITY_REVOKED", operation)
    if (
        row.issuer_ref is not source.issuer_ref
        or row.policy_ref is not source.policy_ref
        or row.epoch_ref is not source.epoch_ref
    ):
        _fail("CAPABILITY_REVOKED", operation)
    return row


def _revoke_cpu_pin_source(source):
    source.state = "revoked"
    for row in source.admissions.values():
        row.state = "revoked"


def _pin_thread_owner(row, owner, operation):
    if (
        row.owner_ref is not owner
        or row.pid != os.getpid()
        or row.thread_ref is not threading.current_thread()
        or row.thread_id != threading.get_native_id()
    ):
        _fail("OWNER_MISMATCH", operation)


@dataclass(frozen=True)
class _TokenBoolResult:
    success: bool
    error: int | None = None


_CODES = {
    "PLATFORM_UNSUPPORTED",
    "ABI_UNACCREDITED",
    "ADMISSION_REQUIRED",
    "CAPABILITY_INVALID",
    "OWNER_MISMATCH",
    "CAPABILITY_REVOKED",
    "PRINCIPAL_UNACCREDITED",
    "OWNER_RETIRE_REQUIRED",
    "RESOURCE_UNKNOWN",
}
_IDENTITY_OPERATIONS = {
    "bootstrap",
    "issue",
    "pin",
    "complete",
    "revoke",
    "close",
    "query",
}


@dataclass(frozen=True)
class IdentityDiagnostic:
    code: str
    operation: str
    win32_error: int | None = None
    ntstatus: int | None = None

    def __post_init__(self):
        if type(self.code) is not str:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.code not in _CODES:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if type(self.operation) is not str:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.operation not in _IDENTITY_OPERATIONS:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.win32_error is not None and type(self.win32_error) is not int:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.win32_error is not None and not 0 <= self.win32_error < 2**32:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.ntstatus is not None:
            raise ValueError("DIAGNOSTIC_INVALID") from None


@dataclass(frozen=True)
class IdentityCloseOutcome:
    state: str
    diagnostics: tuple = ()

    def __post_init__(self):
        if type(self.state) is not str:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.state not in {"closed", "unknown"}:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if type(self.diagnostics) is not tuple:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if any(type(item) is not IdentityDiagnostic for item in self.diagnostics):
            raise ValueError("DIAGNOSTIC_INVALID") from None


@dataclass(frozen=True)
class IdentityInfo:
    state: str
    source: str
    admissions: int
    threads: int
    pins: int
    observations: int
    scopes: tuple

    def __post_init__(self):
        if type(self.state) is not str:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.state not in {"live", "revoked", "unknown", "closed"}:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if type(self.source) is not str:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if self.source not in {"cpu_double", "native_windows_x64"}:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if any(
            type(count) is not int
            for count in (self.admissions, self.threads, self.pins, self.observations)
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None
        for count, maximum in (
            (self.admissions, 4),
            (self.threads, 8),
            (self.pins, 2048),
            (self.observations, 8192),
        ):
            if count < 0 or count > maximum:
                raise ValueError("DIAGNOSTIC_INVALID") from None
        if type(self.scopes) is not tuple:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if len(self.scopes) > 2:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if any(type(scope) is not str for scope in self.scopes):
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if any(
            scope not in {"CANDIDATE_READ_ONLY", "PRODUCT_CHAIN_CANDIDATE"}
            for scope in self.scopes
        ):
            raise ValueError("DIAGNOSTIC_INVALID") from None


class IdentityError(Exception):
    def __init__(self, diagnostic, cleanup=None):
        if type(diagnostic) is not IdentityDiagnostic:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        if cleanup is not None and type(cleanup) is not IdentityCloseOutcome:
            raise ValueError("DIAGNOSTIC_INVALID") from None
        self.diagnostic = diagnostic
        self.cleanup = cleanup
        super().__init__(diagnostic.code + "/" + diagnostic.operation)


def _fail(code, operation, win32_error=None, cleanup=None):
    raise IdentityError(
        IdentityDiagnostic(code, operation, win32_error), cleanup
    ) from None


@dataclass(frozen=True)
class _ContextPseudoResult:
    value: int


@dataclass(frozen=True)
class _TokenStamp:
    TokenId: tuple
    AuthenticationId: tuple
    ModifiedId: tuple
    TokenType: int = 1


@dataclass
class _QueryStep:
    function: str
    offset: int = 0
    return_offset: int = 0
    info_class: int = 0
    sizing: bool = False
    capacity: int = 0
    token: int = 0


@dataclass
class _CpuFrame:
    storage: bytearray = field(default_factory=lambda: bytearray(131328))
    base: int = 4096
    plan: list = field(default_factory=list)
    handles: dict = field(default_factory=dict)
    thread_ref: object = field(default_factory=threading.current_thread)
    thread_id: int = field(default_factory=threading.get_native_id)
    pid: int = field(default_factory=os.getpid)
    semantic_rejection: object = None
    semantic_known: bool = False
    cleanup_complete: bool = False
    public_error: object = None


@dataclass
class _CpuTokenCallRecord:
    ordinal: int
    function: str
    phase: str
    session_ref: object
    frame_ref: _CpuFrame
    input_ranges: tuple
    output_ranges: tuple
    preimage: bytes
    raw_result: object = None
    error: object = None
    recognized_handle: int | None = None
    close_attempted: bool = False


def _poison_cpu(record, error=None):
    record.state = "unknown"
    with _io._REGISTRY_LOCK:
        _io._KERNEL_POISONED = True
    if record.calls and error is not None and record.calls[-1].error is None:
        record.calls[-1].error = error


@_io._boundary_method
def _cpu_call(record, frame, step):
    if type(record) is _IdentitySessionRecord:
        return _native_call(record, frame, step)
    if _io._KERNEL_POISONED:
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    if (
        record.pid != os.getpid()
        or frame.pid != os.getpid()
        or frame.thread_ref is not threading.current_thread()
        or frame.thread_id != threading.get_native_id()
    ):
        raise ValueError("OWNER_MISMATCH") from None
    if record.state != "live":
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    ordinal = len(frame.plan)
    if ordinal >= 28:
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    for previous in record.calls:
        if previous.frame_ref is frame and previous.phase == "recognized":
            previous.preimage = b""
    frame.plan.append(step)
    ranges = ()
    if step.function.startswith("Open"):
        ranges = ((step.offset, 8),)
        frame.storage[step.offset : step.offset + 8] = bytes(8)
    elif step.function == "GetTokenInformation":
        ranges = ((step.return_offset, 4),)
        frame.storage[step.return_offset : step.return_offset + 4] = bytes(4)
        if not step.sizing:
            ranges += ((step.offset, step.capacity),)
            frame.storage[step.offset : step.offset + step.capacity] = (
                b"\xa5" * step.capacity
            )
    if not _sdk_step_ranges_valid(step, ranges):
        _reject_principal(None)
    call = _CpuTokenCallRecord(
        ordinal,
        step.function,
        "reserved",
        record.capability,
        frame,
        (),
        ranges,
        bytes(frame.storage),
    )
    record.calls.append(call)
    result = None
    try:
        call.phase = "entered"
        if step.function == "CloseHandle":
            if frame.handles.get(step.token) is not False:
                raise ValueError()
            frame.handles[step.token] = True
            call.close_attempted = True
        result = record.ops.execute(call)
        call.raw_result = result
        call.phase = "returned"
        _recognize_callback_result(step, result)
        call.phase = "recognized"
        return result, call
    except BaseException as error:  # noqa: BLE001 - custodia fuerte de la frontera
        if call.raw_result is None and result is not None:
            call.raw_result = result
        call.error = error
        _poison_cpu(record, error)
        raise ValueError("RESOURCE_UNKNOWN") from None


class _SemanticRejection(ValueError):
    """Only a frame-issued, recognized rejection permits known cleanup."""


def _reject_principal(frame):
    if frame is None:
        raise ValueError("PRINCIPAL_UNACCREDITED") from None
    error = _SemanticRejection("PRINCIPAL_UNACCREDITED")
    frame.semantic_rejection = error
    raise error from None


def _recognized_rejection(record, frame, error):
    return (
        type(error) is _SemanticRejection
        and frame.semantic_rejection is error
        and record.state != "unknown"
        and bool(record.calls)
        and record.calls[-1].frame_ref is frame
        and record.calls[-1].phase == "recognized"
        and all(
            not call.function.startswith("Open")
            or not call.raw_result.success
            or call.recognized_handle in frame.handles
            for call in record.calls
            if call.frame_ref is frame and call.phase == "recognized"
        )
    )


def _cpu_open(record, frame, *, thread, offset):
    pseudo = "GetCurrentThread" if thread else "GetCurrentProcess"
    pseudo_result, _ = _cpu_call(record, frame, _QueryStep(pseudo))
    frame.current_pseudo = pseudo_result.value
    result, call = _cpu_call(
        record,
        frame,
        _QueryStep("OpenThreadToken" if thread else "OpenProcessToken", offset=offset),
    )
    handle = struct.unpack_from("<Q", frame.storage, offset)[0]
    if not result.success:
        if handle != 0:
            record.state = "unknown"
            raise ValueError("RESOURCE_UNKNOWN") from None
        if result.error == 1008 and thread:
            return None
        _reject_principal(frame)
    if (
        type(handle) is not int
        or handle <= 0
        or handle >= 2**64 - 6
        or handle in frame.handles
    ):
        record.state = "unknown"
        raise ValueError("RESOURCE_UNKNOWN") from None
    frame.handles[handle] = False
    call.recognized_handle = handle
    if thread:
        _reject_principal(frame)
    return handle


def _cpu_fetch(record, frame, *, token, info_class, offset, return_offset):
    result, _ = _cpu_call(
        record,
        frame,
        _QueryStep(
            "GetTokenInformation", offset, return_offset, info_class, True, 0, token
        ),
    )
    capacity = struct.unpack_from("<I", frame.storage, return_offset)[0]
    minimum, maximum = {1: (28, 65536), 5: (20, 65536), 8: (4, 4), 10: (56, 56)}[
        info_class
    ]
    if result.success or result.error != 122:
        _reject_principal(frame)
    if capacity < minimum or capacity > maximum:
        _reject_principal(frame)
    result, _ = _cpu_call(
        record,
        frame,
        _QueryStep(
            "GetTokenInformation",
            offset,
            return_offset,
            info_class,
            False,
            capacity,
            token,
        ),
    )
    length = struct.unpack_from("<I", frame.storage, return_offset)[0]
    if not result.success:
        _reject_principal(frame)
    if length < minimum or length > capacity:
        _reject_principal(frame)
    return bytes(frame.storage[offset : offset + length])


def _stamp(data, *, frame=None):
    if type(data) is not bytes:
        _reject_principal(frame)
    if len(data) != 56:
        _reject_principal(frame)
    if struct.unpack_from("<i", data, 24)[0] != 1:
        _reject_principal(frame)
    return _TokenStamp(
        *(struct.unpack_from("<Ii", data, offset) for offset in (0, 8, 48))
    )


@_io._boundary_method
def _cpu_observe(record):
    _cpu_preflight(record)
    try:
        return _cpu_observe_impl(record)
    except BaseException as error:  # incluso post-TRUE conserva custodia
        if record.frame is not None and _finished_custody_error(
            record, record.frame, error
        ):
            raise
        if (
            record.frame is not None
            and record.frame.semantic_rejection is error
            and record.frame.semantic_known
            and record.frame.cleanup_complete
            and record.state == "revoked"
            and not _io._KERNEL_POISONED
        ):
            raise
        _poison_cpu(record, error)
        if record.frame is not None and record.frame.semantic_known:
            _raise_primary_cleanup_unknown("PRINCIPAL_UNACCREDITED", frame=record.frame)
        raise ValueError("RESOURCE_UNKNOWN") from None


def _cpu_preflight(record):
    if _io._KERNEL_POISONED:
        if record.state != "unknown":
            record.state = "revoked"
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    if record.frame is not None:
        record.state = "revoked"
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    counters = record.counters
    if (
        type(counters) is not dict
        or set(counters) != {"observations", "subcalls"}
        or any(type(v) is not int or v < 0 for v in counters.values())
        or counters["observations"] >= 8192
        or counters["subcalls"] > 229376 - 28
    ):
        record.state = "revoked"
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    thread, thread_id = threading.current_thread(), threading.get_native_id()
    if thread not in record.threads and len(record.threads) >= 8:
        record.state = "revoked"
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    if thread in record.threads and record.threads[thread] != thread_id:
        record.state = "revoked"
        raise ValueError("OWNER_MISMATCH") from None
    record.threads[thread] = thread_id
    counters["observations"] += 1
    counters["subcalls"] += 28


def _cpu_observe_impl(record):
    frame = _CpuFrame()
    record.frame = frame
    primary = None
    observed = None
    try:
        _cpu_open(record, frame, thread=True, offset=0)
        first = _cpu_open(record, frame, thread=False, offset=8)
        before = _stamp(
            _cpu_fetch(
                record, frame, token=first, info_class=10, offset=64, return_offset=32
            ),
            frame=frame,
        )
        token_type = _cpu_fetch(
            record, frame, token=first, info_class=8, offset=56, return_offset=36
        )
        if struct.unpack("<i", token_type)[0] != 1:
            _reject_principal(frame)
        user = _cpu_fetch(
            record, frame, token=first, info_class=1, offset=256, return_offset=40
        )
        sid = _parse_sid(user, base=frame.base + 256, header=16, user=True, frame=frame)
        group = _cpu_fetch(
            record, frame, token=first, info_class=5, offset=65792, return_offset=44
        )
        group_sid = _parse_sid(
            group, base=frame.base + 65792, header=8, user=False, frame=frame
        )
        after = _stamp(
            _cpu_fetch(
                record, frame, token=first, info_class=10, offset=120, return_offset=48
            ),
            frame=frame,
        )
        current = _cpu_open(record, frame, thread=False, offset=16)
        now = _stamp(
            _cpu_fetch(
                record,
                frame,
                token=current,
                info_class=10,
                offset=176,
                return_offset=52,
            ),
            frame=frame,
        )
        if before != after:
            _reject_principal(frame)
        if before != now:
            _reject_principal(frame)
        _cpu_open(record, frame, thread=True, offset=24)
        observed = (sid, group_sid, before)
    except _SemanticRejection as error:
        if not _recognized_rejection(record, frame, error):
            raise
        frame.semantic_known = True
        primary = str(error)
    if record.state == "unknown":
        raise ValueError("RESOURCE_UNKNOWN") from None
    for handle in reversed(tuple(frame.handles)):
        try:
            result, _ = _cpu_call(
                record, frame, _QueryStep("CloseHandle", token=handle)
            )
        except BaseException as error:
            _poison_cpu(record, error)
            if primary:
                _raise_primary_cleanup_unknown(primary, frame=frame)
            raise
        if not result.success:
            _poison_cpu(record)
            if primary:
                _raise_primary_cleanup_unknown(primary, result.error, frame=frame)
            raise ValueError("RESOURCE_UNKNOWN") from None
    if primary:
        record.state = "revoked"
        frame.cleanup_complete = True
        raise frame.semantic_rejection from None
    if (
        frame.pid != os.getpid()
        or frame.thread_ref is not threading.current_thread()
        or frame.thread_id != threading.get_native_id()
    ):
        record.state = "revoked"
        raise ValueError("OWNER_MISMATCH") from None
    record.frame = None
    frame.storage.clear()
    frame.handles.clear()
    for call in record.calls:
        if call.frame_ref is frame:
            call.recognized_handle = None
            call.raw_result = None
            call.preimage = b""
    return observed


def _issue_cpu_acquisition_admission(authority, *, scope):
    if type(authority) is not _CpuDeployerAuthority:
        raise ValueError("CAPABILITY_INVALID") from None
    record = _CPU_AUTHORITIES.get(authority)
    if (
        record is None
        or record.capability is not authority
        or record.pid != os.getpid()
    ):
        raise ValueError("CAPABILITY_INVALID") from None
    if type(record) is not _CpuAuthorityRecord or record.source != "cpu_double":
        raise ValueError("CAPABILITY_INVALID") from None
    for capability, expected in (
        (record.issuer_ref, _CpuIssuer),
        (record.policy_ref, _CpuSecurityPolicy),
        (record.epoch_ref, _CpuPolicyEpoch),
    ):
        root = _CPU_CAPABILITIES.get(capability)
        if (
            type(capability) is not expected
            or type(root) is not _CpuRootRecord
            or root.capability is not capability
            or root.authority_ref is not authority
            or root.pid != os.getpid()
            or root.source != "cpu_double"
            or root.doctrine != "storage-nt-security-s1"
        ):
            raise ValueError("CAPABILITY_INVALID") from None
        if root.state != "live":
            raise ValueError("CAPABILITY_REVOKED") from None
    if (
        type(scope) is not _AdmissionScope
        or scope is _AdmissionScope.OWNED_PROBE_CANDIDATE
    ):
        raise ValueError("ADMISSION_REQUIRED") from None
    if record.state != "live":
        raise ValueError("CAPABILITY_REVOKED") from None
    if (
        len(record.admissions) >= 4
        or sum(item.scope is scope for item in record.admissions.values()) >= 2
    ):
        record.state = "revoked"
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    observed = _cpu_observe(record)
    sid, group, stamp = observed
    if (
        sid != record.principal_sid
        or group != record.primary_group_sid
        or record.token_stamp not in (None, stamp)
    ):
        record.state = "revoked"
        raise ValueError("PRINCIPAL_UNACCREDITED") from None
    record.token_stamp = stamp
    admission = object.__new__(_CpuAdmission)
    record.admissions[admission] = _AdmissionRecord(
        admission,
        record.issuer_ref,
        record.pid,
        scope,
        sid,
        group,
        authority,
        observed,
        "cpu_double",
        record.policy_ref,
        record.epoch_ref,
    )
    return admission


def _parse_sid(data, *, base, header, user, frame=None):
    if (
        type(data) is not bytes
        or type(base) is not int
        or not 0 < base < 2**64
        or type(header) is not int
        or type(user) is not bool
        or header != (16 if user else 8)
        or not header + 12 <= len(data) <= 65536
        or base > 2**64 - len(data)
    ):
        _reject_principal(frame)
    pointer = struct.unpack_from("<Q", data)[0]
    if user and struct.unpack_from("<I", data, 8)[0] != 0:
        _reject_principal(frame)
    if pointer % 4 or pointer < base + header or pointer - base > len(data) - 8:
        _reject_principal(frame)
    offset = pointer - base
    revision, count = data[offset : offset + 2]
    size = 8 + 4 * count
    if revision != 1 or not 1 <= count <= 15 or size > len(data) - offset:
        _reject_principal(frame)
    return bytes(data[offset : offset + size])


@dataclass
class _IdentitySessionRecord:
    capability: object
    issuer_ref: object
    pid: int
    source: str = "native_windows_x64"
    state: str = "building"
    workspace_context: object = None
    workspace_arena: object = None
    workspace_sdk_length: int = 131328
    workspace_k1_length: int = 131584
    workspace_alignment: int = 512
    workspace_requested: int = 132095
    workspace_tail: int = 256
    policy_ref: object = None
    epoch_ref: object = None
    authority_ref: object = None
    lock: object = field(default_factory=threading.RLock)
    threads: dict = field(default_factory=dict)
    admissions: dict = field(default_factory=dict)
    pins: dict = field(default_factory=dict)
    observations: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    counters: dict = field(default_factory=lambda: {"observations": 0, "subcalls": 0})
    outcome: object = None
    owner_refs: dict = field(default_factory=dict)
    pin_slots_reserved: int = 0


@dataclass
class _NativeIssuerRecord:
    capability: object
    session_ref: object
    pid: int
    source: str
    bindings_ref: object = None
    state: str = "building"


@dataclass
class _DeployerAuthorityRecord:
    capability: object
    session_ref: object
    issuer_ref: object
    pid: int
    principal_sid: bytes
    primary_group_sid: bytes
    ratification_observation_ref: object
    token_stamp: _TokenStamp
    policy_ref: object
    epoch_ref: object
    state: str = "live"


@dataclass
class _EffectiveObservationRecord:
    capability: object
    session_ref: object
    issuer_ref: object
    pid: int
    thread_ref: object
    thread_id: int
    principal_sid: bytes
    primary_group_sid: bytes
    token_stamp: object
    policy_ref: object
    epoch_ref: object
    state: str
    frame_ref: object


@dataclass
class _SecurityPolicyRecord:
    capability: object
    session_ref: object
    issuer_ref: object
    doctrine: str = "storage-nt-security-s1"
    state: str = "live"


@dataclass
class _PolicyEpochRecord:
    capability: object
    session_ref: object
    policy_ref: object
    issuer_ref: object
    pid: int
    state: str = "live"


@dataclass
class _AdmissionRecord:
    capability: object
    issuer_ref: object
    pid: int
    scope: _AdmissionScope
    principal_sid: bytes
    primary_group_sid: bytes
    principal_ratification_ref: object
    effective_context_ref: object
    source: str
    policy_ref: object
    epoch_ref: object
    state: str = "live"


class _TokenObservationPermit(_Opaque):
    __slots__ = ()


@dataclass
class _NativeFrame(_CpuFrame):
    permit_ref: object = None
    workspace_pin: object = None
    observation_ref: object = None
    current_pseudo: int = 0


@dataclass
class _TokenCallRecord(_CpuTokenCallRecord):
    pass


def _register_identity(capability, record):
    with _io._REGISTRY_LOCK:
        _io._IDENTITY_CAPABILITIES[capability] = record


def _native_live(session, operation, *, building=False):
    with _io._REGISTRY_LOCK:
        poisoned = _io._KERNEL_POISONED
        issuer = _io._IDENTITY_CAPABILITIES.get(session.issuer_ref)
    if poisoned or session.state == "unknown":
        _fail("OWNER_RETIRE_REQUIRED", operation)
    if (
        session.pid != os.getpid()
        or type(session.pid) is not int
        or session.source != "native_windows_x64"
        or type(issuer) is not _NativeIssuerRecord
        or type(session.issuer_ref) is not _NativeIssuer
        or issuer.capability is not session.issuer_ref
        or issuer.session_ref is not session.capability
        or issuer.pid != session.pid
        or issuer.source != session.source
        or type(issuer.bindings_ref) is not _IdentityOps
    ):
        _fail("CAPABILITY_INVALID", operation)
    allowed = {"live", "building"} if building else {"live"}
    if session.state not in allowed or issuer.state not in allowed:
        _fail("CAPABILITY_REVOKED", operation)
    if session.state == "live":
        with _io._REGISTRY_LOCK:
            policy = _io._IDENTITY_CAPABILITIES.get(session.policy_ref)
            epoch = _io._IDENTITY_CAPABILITIES.get(session.epoch_ref)
        if (
            type(session.policy_ref) is not _SecurityPolicy
            or type(policy) is not _SecurityPolicyRecord
            or policy.capability is not session.policy_ref
            or policy.session_ref is not session.capability
            or policy.issuer_ref is not session.issuer_ref
            or policy.doctrine != "storage-nt-security-s1"
            or policy.state != "live"
            or type(session.epoch_ref) is not _PolicyEpoch
            or type(epoch) is not _PolicyEpochRecord
            or epoch.capability is not session.epoch_ref
            or epoch.session_ref is not session.capability
            or epoch.policy_ref is not session.policy_ref
            or epoch.issuer_ref is not session.issuer_ref
            or epoch.pid != session.pid
            or epoch.state != "live"
        ):
            _fail("CAPABILITY_REVOKED", operation)


def _authority_record(authority, operation):
    if type(authority) is not _DeployerAuthority:
        _fail("CAPABILITY_INVALID", operation)
    with _io._REGISTRY_LOCK:
        row = _io._IDENTITY_CAPABILITIES.get(authority)
    if type(row) is not _DeployerAuthorityRecord or row.capability is not authority:
        _fail("CAPABILITY_INVALID", operation)
    try:
        session = _io._registered_native_session(row.session_ref)
    except _io.KernelMemoryError:
        _fail("CAPABILITY_INVALID", operation)
    if (
        session.authority_ref is not authority
        or row.pid != os.getpid()
        or row.issuer_ref is not session.issuer_ref
        or row.policy_ref is not session.policy_ref
        or row.epoch_ref is not session.epoch_ref
    ):
        _fail("CAPABILITY_INVALID", operation)
    return row, session


def _native_poison(session, error=None):
    _io._kernel_domain_poison_identity(session.capability)
    if session.calls and error is not None and session.calls[-1].error is None:
        session.calls[-1].error = error
    for row in session.admissions.values():
        row.state = "unknown"
    with _io._REGISTRY_LOCK:
        for capability in (
            session.authority_ref,
            session.epoch_ref,
            session.issuer_ref,
        ):
            row = _io._IDENTITY_CAPABILITIES.get(capability)
            if row is not None:
                row.state = "unknown"


def _raise_custody_error(frame, code, operation, win32_error=None, cleanup=None):
    error = IdentityError(IdentityDiagnostic(code, operation, win32_error), cleanup)
    frame.public_error = error
    raise error from None


def _finished_custody_error(record, frame, error):
    # La identidad del objeto no acredita una fase de limpieza terminada.
    if frame.public_error is not error or type(error) is not IdentityError:
        return False
    if record.state == "unknown" and _io._KERNEL_POISONED:
        return error.cleanup is not None and error.cleanup.state == "unknown"
    return (
        frame.cleanup_complete
        and record.state == "revoked"
        and not _io._KERNEL_POISONED
        and error.cleanup is None
    )


def _raise_primary_cleanup_unknown(primary, error=None, *, frame):
    _raise_custody_error(
        frame,
        primary,
        "query",
        cleanup=IdentityCloseOutcome(
            "unknown", (IdentityDiagnostic("RESOURCE_UNKNOWN", "close", error),)
        ),
    )


def _validate_native_call(call, ops):
    if type(call) is not _TokenCallRecord or type(call.frame_ref) is not _NativeFrame:
        _fail("CAPABILITY_INVALID", "query")
    session = _io._registered_native_session(call.session_ref)
    _native_live(session, "query", building=True)
    frame = call.frame_ref
    observation = session.observations.get(frame.observation_ref)
    issuer = _io._IDENTITY_CAPABILITIES[session.issuer_ref]
    if (
        issuer.bindings_ref is not ops
        or not _registered_call_reference(session.calls, call)
        or call.phase != "entered"
        or type(call.ordinal) is not int
        or call.ordinal != len(frame.plan) - 1
        or type(observation) is not _EffectiveObservationRecord
        or observation.frame_ref is not frame
        or observation.state != "building"
        or type(frame.permit_ref) is not _TokenObservationPermit
        or _io._IDENTITY_CAPABILITIES.get(frame.permit_ref) is not observation
        or frame.thread_ref is not threading.current_thread()
        or frame.thread_id != threading.get_native_id()
        or frame.pid != os.getpid()
        or observation.policy_ref is not session.policy_ref
        or observation.epoch_ref is not session.epoch_ref
    ):
        _fail("CAPABILITY_INVALID", "query")
    step = frame.plan[call.ordinal]
    if type(step) is not _QueryStep or step.function != call.function:
        _fail("CAPABILITY_INVALID", "query")
    if not _sdk_step_ranges_valid(step, call.output_ranges) or call.input_ranges != ():
        _fail("CAPABILITY_INVALID", "query")
    layout = {1: (256, 65536, 40), 5: (65792, 65536, 44), 8: (56, 4, 36), 10: None}
    if step.function == "GetTokenInformation":
        if (
            step.info_class not in layout
            or step.token not in frame.handles
            or frame.handles[step.token] is not False
        ):
            _fail("CAPABILITY_INVALID", "query")
        expected = layout[step.info_class]
        if step.info_class == 10:
            expected = {64: (64, 56, 32), 120: (120, 56, 48), 176: (176, 56, 52)}.get(
                step.offset
            )
        if (
            expected is None
            or step.offset != expected[0]
            or step.return_offset != expected[2]
            or type(step.capacity) is not int
            or not 0 <= step.capacity <= expected[1]
            or step.sizing
            and step.capacity != 0
            or not step.sizing
            and step.capacity <= 0
        ):
            _fail("CAPABILITY_INVALID", "query")
    elif step.function in {"OpenThreadToken", "OpenProcessToken"}:
        if step.offset not in (
            {0, 24} if step.function == "OpenThreadToken" else {8, 16}
        ):
            _fail("CAPABILITY_INVALID", "query")
    elif step.function == "CloseHandle":
        if (
            step.token not in frame.handles
            or not call.close_attempted
            or frame.handles[step.token] is not True
        ):
            _fail("CAPABILITY_INVALID", "query")
    elif step.function not in {"GetCurrentProcess", "GetCurrentThread"}:
        _fail("CAPABILITY_INVALID", "query")
    address = _io._identity_workspace_address(frame.workspace_pin)
    if address != frame.base:
        _fail("CAPABILITY_INVALID", "query")
    return session, frame, step, address


def _registered_call_reference(calls, call):
    return any(registered is call for registered in calls)


def _native_call(session, frame, step):
    _native_live(session, "query", building=True)
    if (
        frame.thread_ref is not threading.current_thread()
        or frame.thread_id != threading.get_native_id()
    ):
        raise ValueError("OWNER_MISMATCH") from None
    if len(frame.plan) >= 28:
        raise ValueError("OWNER_RETIRE_REQUIRED") from None
    for previous in session.calls:
        if previous.frame_ref is frame and previous.phase == "recognized":
            previous.preimage = b""
    ranges = ()
    if step.function.startswith("Open"):
        ranges = ((step.offset, 8),)
        frame.storage[step.offset : step.offset + 8] = bytes(8)
    elif step.function == "GetTokenInformation":
        ranges = ((step.return_offset, 4),)
        frame.storage[step.return_offset : step.return_offset + 4] = bytes(4)
        if not step.sizing:
            ranges += ((step.offset, step.capacity),)
            sentinel = (
                b"\xff\xff\xff\x7f" if step.info_class == 8 else b"\xa5" * step.capacity
            )
            frame.storage[step.offset : step.offset + step.capacity] = sentinel
    frame.plan.append(step)
    call = _TokenCallRecord(
        len(frame.plan) - 1,
        step.function,
        "reserved",
        session.capability,
        frame,
        (),
        ranges,
        bytes(frame.storage),
    )
    session.calls.append(call)
    result = None
    try:
        for offset, length in ranges:
            _io._arena_copy_in(
                session.workspace_context,
                session.workspace_arena,
                offset=offset,
                data=bytes(frame.storage[offset : offset + length]),
            )
        call.phase = "entered"
        if step.function == "CloseHandle":
            if frame.handles.get(step.token) is not False:
                raise ValueError()
            frame.handles[step.token] = True
            call.close_attempted = True
        issuer = _io._IDENTITY_CAPABILITIES[session.issuer_ref]
        result = issuer.bindings_ref.execute(call)
        call.raw_result = result
        call.phase = "returned"
        frame.storage[:] = _io._arena_copy_out(
            session.workspace_context, session.workspace_arena, offset=0, length=131328
        )
        _recognize_callback_result(step, result)
        call.phase = "recognized"
        return result, call
    except BaseException as error:  # noqa: BLE001 - ninguna ENTRY incierta se reintenta
        if call.raw_result is None and result is not None:
            call.raw_result = result
        _native_poison(session, error)
        raise ValueError("RESOURCE_UNKNOWN") from None


def _observe_current_effective_principal(session):
    record = _io._registered_native_session(session)
    _native_live(record, "query", building=True)
    counters = record.counters
    if (
        set(counters) != {"observations", "subcalls"}
        or any(type(v) is not int or v < 0 for v in counters.values())
        or counters["observations"] >= 8192
        or counters["subcalls"] > 229376 - 28
    ):
        _revoke_session(record)
        _fail("OWNER_RETIRE_REQUIRED", "query")
    thread, native_id = threading.current_thread(), threading.get_native_id()
    if thread not in record.threads and len(record.threads) >= 8:
        _revoke_session(record)
        _fail("OWNER_RETIRE_REQUIRED", "query")
    if thread in record.threads and record.threads[thread] != native_id:
        _revoke_session(record)
        _fail("OWNER_MISMATCH", "query")
    record.threads[thread] = native_id
    counters["observations"] += 1
    counters["subcalls"] += 28
    capability = object.__new__(_EffectivePrincipalObservation)
    frame = _NativeFrame()
    frame.permit_ref = object.__new__(_TokenObservationPermit)
    frame.observation_ref = capability
    observation = _EffectiveObservationRecord(
        capability,
        session,
        record.issuer_ref,
        os.getpid(),
        thread,
        native_id,
        b"",
        b"",
        None,
        record.policy_ref,
        record.epoch_ref,
        "building",
        frame,
    )
    record.observations[capability] = observation
    _register_identity(capability, observation)
    _register_identity(frame.permit_ref, observation)
    try:
        frame.workspace_pin = _io._pin_identity_workspace(
            session, record.workspace_arena
        )
        frame.base = _io._identity_workspace_address(frame.workspace_pin)
        primary = None
        observed = None
        try:
            _cpu_open(record, frame, thread=True, offset=0)
            first = _cpu_open(record, frame, thread=False, offset=8)
            before = _stamp(
                _cpu_fetch(
                    record,
                    frame,
                    token=first,
                    info_class=10,
                    offset=64,
                    return_offset=32,
                ),
                frame=frame,
            )
            token_type = _cpu_fetch(
                record, frame, token=first, info_class=8, offset=56, return_offset=36
            )
            if struct.unpack("<i", token_type)[0] != 1:
                _reject_principal(frame)
            user = _cpu_fetch(
                record, frame, token=first, info_class=1, offset=256, return_offset=40
            )
            sid = _parse_sid(
                user, base=frame.base + 256, header=16, user=True, frame=frame
            )
            group = _cpu_fetch(
                record, frame, token=first, info_class=5, offset=65792, return_offset=44
            )
            group_sid = _parse_sid(
                group, base=frame.base + 65792, header=8, user=False, frame=frame
            )
            after = _stamp(
                _cpu_fetch(
                    record,
                    frame,
                    token=first,
                    info_class=10,
                    offset=120,
                    return_offset=48,
                ),
                frame=frame,
            )
            current = _cpu_open(record, frame, thread=False, offset=16)
            now = _stamp(
                _cpu_fetch(
                    record,
                    frame,
                    token=current,
                    info_class=10,
                    offset=176,
                    return_offset=52,
                ),
                frame=frame,
            )
            if before != after or before != now:
                _reject_principal(frame)
            _cpu_open(record, frame, thread=True, offset=24)
            observed = (sid, group_sid, before)
        except _SemanticRejection as error:
            if not _recognized_rejection(record, frame, error):
                raise
            frame.semantic_known = True
            primary = str(error)
        if record.state == "unknown":
            _fail("RESOURCE_UNKNOWN", "query")
        for handle in reversed(tuple(frame.handles)):
            try:
                result, _ = _native_call(
                    record, frame, _QueryStep("CloseHandle", token=handle)
                )
            except BaseException as error:
                _native_poison(record, error)
                if primary:
                    _raise_primary_cleanup_unknown(primary, frame=frame)
                raise
            if not result.success:
                _native_poison(record)
                if primary:
                    _raise_primary_cleanup_unknown(primary, result.error, frame=frame)
                _raise_custody_error(frame, "RESOURCE_UNKNOWN", "close", result.error)
        if primary:
            _revoke_session(record)
            frame.cleanup_complete = True
            _raise_custody_error(frame, primary, "query")
        if (
            frame.pid != os.getpid()
            or frame.thread_ref is not threading.current_thread()
            or frame.thread_id != threading.get_native_id()
        ):
            _revoke_session(record)
            frame.cleanup_complete = True
            _raise_custody_error(frame, "OWNER_MISMATCH", "query")
        (
            observation.principal_sid,
            observation.primary_group_sid,
            observation.token_stamp,
        ) = observed
        observation.state = "live"
        frame.storage.clear()
        frame.handles.clear()
        for call in record.calls:
            if call.frame_ref is frame:
                call.recognized_handle = None
                call.raw_result = None
                call.preimage = b""
        _io._retire_identity_workspace_pin(frame.workspace_pin)
        return capability
    except BaseException as error:
        if _finished_custody_error(record, frame, error):
            raise
        _native_poison(record, error)
        if frame.semantic_known:
            _raise_primary_cleanup_unknown("PRINCIPAL_UNACCREDITED", frame=frame)
        _fail("RESOURCE_UNKNOWN", "query")


def _bootstrap_native():
    _require_canonical_identity_instance()
    try:
        _io._kernel_identity_bootstrap_claim()
    except _io.KernelMemoryError:
        _fail("OWNER_RETIRE_REQUIRED", "bootstrap")
    with _identity_domain("bootstrap"):
        session = object.__new__(_IdentitySession)
        issuer = object.__new__(_NativeIssuer)
        record = _IdentitySessionRecord(session, issuer, os.getpid())
        issuer_record = _NativeIssuerRecord(
            issuer, session, os.getpid(), "native_windows_x64"
        )
        with _io._REGISTRY_LOCK:
            _io._LIVE_IDENTITY_SESSIONS[session] = record
            _io._IDENTITY_CAPABILITIES[issuer] = issuer_record
        with record.lock:
            try:
                from . import storage_journal_windows_abi as abi

                issuer_record.bindings_ref = abi._new_native_identity_backend()
                record.workspace_context = _io._new_memory_context()
                record.workspace_arena = _io._allocate_aligned(
                    record.workspace_context, length=131584, alignment=512
                )
                observation = _observe_current_effective_principal(session)
                observed = record.observations[observation]
                policy = object.__new__(_SecurityPolicy)
                epoch = object.__new__(_PolicyEpoch)
                authority = object.__new__(_DeployerAuthority)
                _register_identity(
                    policy, _SecurityPolicyRecord(policy, session, issuer)
                )
                _register_identity(
                    epoch,
                    _PolicyEpochRecord(epoch, session, policy, issuer, os.getpid()),
                )
                authority_record = _DeployerAuthorityRecord(
                    authority,
                    session,
                    issuer,
                    os.getpid(),
                    observed.principal_sid,
                    observed.primary_group_sid,
                    observation,
                    observed.token_stamp,
                    policy,
                    epoch,
                )
                _register_identity(authority, authority_record)
                record.policy_ref, record.epoch_ref, record.authority_ref = (
                    policy,
                    epoch,
                    authority,
                )
                observed.policy_ref, observed.epoch_ref = policy, epoch
                issuer_record.state = record.state = "live"
                return authority
            except BaseException as error:  # noqa: BLE001 - bootstrap consumido incluso si falla
                if record.state == "unknown" or _io._KERNEL_POISONED:
                    _native_poison(record, error)
                    if type(error) is IdentityError and error.cleanup is not None:
                        _fail(error.diagnostic.code, "bootstrap", cleanup=error.cleanup)
                    _fail("RESOURCE_UNKNOWN", "bootstrap")
                record.state = issuer_record.state = "revoked"
                outcome = (
                    _io._close_memory_context(record.workspace_context)
                    if record.workspace_context is not None
                    else None
                )
                if outcome is not None and outcome.state != "closed":
                    _native_poison(record, error)
                    _fail("RESOURCE_UNKNOWN", "bootstrap")
                code = (
                    error.diagnostic.code
                    if isinstance(error, IdentityError)
                    else "ABI_UNACCREDITED"
                )
                _fail(code, "bootstrap")


def _revoke_session(session):
    if session.state not in {"unknown", "closed"}:
        session.state = "revoked"
    with _io._REGISTRY_LOCK:
        for capability in (session.authority_ref, session.epoch_ref):
            record = _io._IDENTITY_CAPABILITIES.get(capability)
            if record is not None and record.state not in {"unknown", "closed"}:
                record.state = "revoked"
        for record in session.admissions.values():
            if record.state not in {"unknown", "closed"}:
                record.state = "revoked"


@contextmanager
def _identity_domain(operation):
    try:
        with _io._kernel_domain() as lease:
            yield lease
    except _io.KernelMemoryError as error:
        _fail(error.diagnostic.code, operation)


def _issue_acquisition_admission(deployer_authority, *, scope):
    authority = deployer_authority
    if (
        type(scope) is not _AdmissionScope
        or scope is _AdmissionScope.OWNED_PROBE_CANDIDATE
    ):
        _fail("ADMISSION_REQUIRED", "issue")
    row, session = _authority_record(authority, "issue")
    with _identity_domain("issue"), session.lock:
        _native_live(session, "issue")
        if row.state != "live":
            _fail("CAPABILITY_REVOKED", "issue")
        if (
            len(session.admissions) >= 4
            or sum(r.scope is scope for r in session.admissions.values()) >= 2
        ):
            _revoke_session(session)
            _fail("OWNER_RETIRE_REQUIRED", "issue")
        observation = _observe_current_effective_principal(session.capability)
        observed = session.observations[observation]
        if (
            observed.principal_sid != row.principal_sid
            or observed.primary_group_sid != row.primary_group_sid
            or observed.token_stamp != row.token_stamp
        ):
            _revoke_session(session)
            _fail("PRINCIPAL_UNACCREDITED", "issue")
        admission = object.__new__(_AcquisitionAdmission)
        record = _AdmissionRecord(
            admission,
            session.issuer_ref,
            session.pid,
            scope,
            row.principal_sid,
            row.primary_group_sid,
            authority,
            observation,
            session.source,
            session.policy_ref,
            session.epoch_ref,
        )
        session.admissions[admission] = record
        _register_identity(admission, record)
        return admission


def _identity_info(deployer_authority):
    _, session = _authority_record(deployer_authority, "query")
    with _io._REGISTRY_LOCK:
        return IdentityInfo(
            session.state,
            session.source,
            len(session.admissions),
            len(session.threads),
            len(session.pins),
            session.counters["observations"],
            tuple(sorted({r.scope.name for r in session.admissions.values()})),
        )


def _revoke_deployer_authority(deployer_authority):
    _, session = _authority_record(deployer_authority, "revoke")
    with _io._NATIVE_BOUNDARY_LOCK, session.lock:
        _revoke_session(session)


def _close_deployer_authority(deployer_authority):
    _, session = _authority_record(deployer_authority, "close")
    with _io._NATIVE_BOUNDARY_LOCK, session.lock:
        if session.outcome is not None:
            return session.outcome
        _revoke_session(session)
        session.outcome = IdentityCloseOutcome(
            "unknown", (IdentityDiagnostic("OWNER_RETIRE_REQUIRED", "close"),)
        )
        if (
            any(
                type(pin) is not _AdmissionPinRecord
                or pin.state not in {"completed", "aborted", "revoked"}
                or pin.error is not None
                for pin in session.pins.values()
            )
            or any(
                owner.state.value != "closed"
                or owner.outcome is None
                or owner.outcome.state != "closed"
                or owner.control is not None
                or owner.inflight
                or owner.backings
                or owner.ops is not None
                for owner in session.owner_refs.values()
            )
            or session.state == "unknown"
            or _io._KERNEL_POISONED
        ):
            return session.outcome
        outcome = _io._close_memory_context(session.workspace_context)
        if outcome.state != "closed":
            _native_poison(session)
            session.outcome = IdentityCloseOutcome(
                "unknown", (IdentityDiagnostic("RESOURCE_UNKNOWN", "close"),)
            )
            return session.outcome
        session.state = "closed"
        session.outcome = IdentityCloseOutcome("closed")
        with _io._REGISTRY_LOCK:
            _io._CLOSED_IDENTITY_SESSIONS[session.capability] = session
            _io._LIVE_IDENTITY_SESSIONS.pop(session.capability, None)
        return session.outcome


def _sdk_step_ranges_valid(step, ranges):
    if type(step) is not _QueryStep:
        return False
    if (
        type(step.function) is not str
        or type(step.sizing) is not bool
        or any(
            type(v) is not int or v < 0
            for v in (
                step.offset,
                step.return_offset,
                step.info_class,
                step.capacity,
                step.token,
            )
        )
        or type(ranges) is not tuple
        or any(
            type(pair) is not tuple
            or len(pair) != 2
            or any(type(v) is not int or v < 0 for v in pair)
            for pair in ranges
        )
    ):
        return False
    if step.function in {"GetCurrentProcess", "GetCurrentThread", "CloseHandle"}:
        return ranges == ()
    if step.function in {"OpenThreadToken", "OpenProcessToken"}:
        slots = {0, 24} if step.function == "OpenThreadToken" else {8, 16}
        return step.offset in slots and ranges == ((step.offset, 8),)
    if step.function != "GetTokenInformation":
        return False
    layouts = {1: (256, 28, 65536, 40), 5: (65792, 20, 65536, 44), 8: (56, 4, 4, 36)}
    if step.info_class == 10:
        spec = {
            64: (64, 56, 56, 32),
            120: (120, 56, 56, 48),
            176: (176, 56, 56, 52),
        }.get(step.offset)
    else:
        spec = layouts.get(step.info_class)
    if spec is None or step.offset != spec[0] or step.return_offset != spec[3]:
        return False
    expected = ((step.return_offset, 4),)
    if step.sizing:
        return step.capacity == 0 and ranges == expected
    return spec[1] <= step.capacity <= spec[2] and ranges == expected + (
        (step.offset, step.capacity),
    )


def _recognize_callback_result(step, result):
    if step.function.startswith("GetCurrent"):
        if type(result) is not _ContextPseudoResult:
            raise ValueError()
        if type(result.value) is not int or result.value not in range(2**64 - 6, 2**64):
            raise ValueError()
    if not step.function.startswith("GetCurrent"):
        if type(result) is not _TokenBoolResult:
            raise ValueError()
        if type(result.success) is not bool:
            raise ValueError()
        if result.error is not None and (
            type(result.error) is not int or not 0 <= result.error < 2**32
        ):
            raise ValueError()
        if (
            result.success
            and result.error is not None
            or not result.success
            and result.error is None
        ):
            raise ValueError()
