"""Inspección local readonly; ningún resultado admite una cadena del journal."""

import ctypes
import os
import struct
from contextlib import contextmanager
from dataclasses import dataclass, field

MAX_DESCRIPTOR = 1024 * 1024
SYSTEM_SID = b"\x01\x01\x00\x00\x00\x00\x00\x05\x12\x00\x00\x00"
ADMINISTRATORS_SID = b"\x01\x02\x00\x00\x00\x00\x00\x05\x20\x00\x00\x00\x20\x02\x00\x00"
_NATIVE_OBSERVATION = object()


class SecurityInspectionError(Exception):
    """Consulta no acreditada; los detalles no contienen rutas ni cuentas."""

    code = "SECURITY_UNACCREDITED"


class PlatformUnsupportedError(SecurityInspectionError):
    code = "PLATFORM_UNSUPPORTED"


@dataclass(frozen=True)
class _Ace:
    kind: int
    flags: int
    mask: int
    trustee: bytes


@dataclass(frozen=True)
class _Descriptor:
    owner: bytes
    group: bytes
    control: int
    aces: tuple[_Ace, ...]


@dataclass(frozen=True)
class SecurityObservation:
    """Copia inmutable de SD sin handle; construirla no acredita origen nativo.

    El sello sólo distingue la consulta realizada en este proceso. No protege
    contra código malicioso dentro del controller ni representa una capability.
    """

    raw: bytes
    _origin: object = field(default=None, init=False, repr=False, compare=False)

    @property
    def owner(self) -> bytes:
        return _parse_descriptor(self.raw).owner

    @property
    def group(self) -> bytes:
        return _parse_descriptor(self.raw).group

    @property
    def control(self) -> int:
        return _parse_descriptor(self.raw).control


def _sid_at(raw: bytes, offset: int, limit: int) -> tuple[bytes, int]:
    if offset < 0 or offset + 8 > limit:
        raise SecurityInspectionError("SID truncado")
    revision, count = raw[offset : offset + 2]
    end = offset + 8 + count * 4
    if revision != 1 or count > 15 or end > limit:
        raise SecurityInspectionError("SID inválido")
    return raw[offset:end], end


def _valid_sid(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise SecurityInspectionError("SID requiere bytes")
    value, end = _sid_at(raw, 0, len(raw))
    if end != len(raw):
        raise SecurityInspectionError("SID con bytes sobrantes")
    return value


def _parse_descriptor(raw: bytes) -> _Descriptor:
    if type(raw) is not bytes or not 20 <= len(raw) <= MAX_DESCRIPTOR:
        raise SecurityInspectionError("Descriptor fuera de límites")
    revision, reserved, control, owner, group, sacl, dacl = struct.unpack_from(
        "<BBHIIII", raw
    )
    if (
        revision != 1
        or reserved
        or control & ~0x950F
        or control & 0x8004 != 0x8004
        or sacl
    ):
        raise SecurityInspectionError("Descriptor no interpretable")
    for offset in (owner, group, dacl):
        if offset < 20 or offset % 4 or offset >= len(raw):
            raise SecurityInspectionError("Offset inválido o DACL NULL")
    owner_sid, owner_end = _sid_at(raw, owner, len(raw))
    group_sid, group_end = _sid_at(raw, group, len(raw))
    if dacl + 8 > len(raw):
        raise SecurityInspectionError("ACL truncada")
    acl_rev, reserved1, size, count, reserved2 = struct.unpack_from("<BBHHH", raw, dacl)
    end = dacl + size
    if (
        acl_rev not in (2, 4)
        or reserved1
        or reserved2
        or size < 8
        or end > len(raw)
        or not count
    ):
        raise SecurityInspectionError("ACL inválida o vacía")
    ranges = sorted(((owner, owner_end), (group, group_end), (dacl, end)))
    previous = 20
    for start, stop in ranges:
        if start < previous or any(raw[previous:start]):
            raise SecurityInspectionError("Descriptor solapado o hueco no nulo")
        previous = stop
    if previous != len(raw):
        raise SecurityInspectionError("Descriptor con bytes sobrantes")
    aces = []
    cursor = dacl + 8
    for _ in range(count):
        if cursor + 8 > end:
            raise SecurityInspectionError("ACE truncada")
        kind, flags, ace_size, mask = struct.unpack_from("<BBHI", raw, cursor)
        stop = cursor + ace_size
        if ace_size < 16 or ace_size % 4 or stop > end:
            raise SecurityInspectionError("Longitud ACE inválida")
        trustee, sid_end = _sid_at(raw, cursor + 8, stop)
        if sid_end != stop:
            raise SecurityInspectionError("ACE con bytes sobrantes")
        aces.append(_Ace(kind, flags, mask, trustee))
        cursor = stop
    if any(raw[cursor:end]):
        raise SecurityInspectionError("Relleno ACL no nulo")
    return _Descriptor(owner_sid, group_sid, control, tuple(aces))


@dataclass(frozen=True)
class SecurityDiagnostic:
    """Condición suficiente local; jamás capacidad o admisión de cadena."""

    local_sufficient: bool
    native_observed: bool
    reasons: tuple[str, ...] = ()


def evaluate_security(observation, principal, role):
    native = (
        type(observation) is SecurityObservation
        and observation._origin is _NATIVE_OBSERVATION
    )
    try:
        _valid_sid(principal)
        if role not in ("journal", "protected_domain", "existing_parent"):
            raise SecurityInspectionError("Papel no liberado")
        raw = (
            observation.raw if type(observation) is SecurityObservation else observation
        )
        parsed = _parse_descriptor(raw)
        _evaluate_descriptor(parsed, principal, role)
    except SecurityInspectionError as error:
        return SecurityDiagnostic(False, native, (str(error),))
    return SecurityDiagnostic(True, native)


def _mapped_rights(mask: int) -> int:
    if mask & ~0xF01F01FF:
        raise SecurityInspectionError("Máscara desconocida")
    mapped = mask & 0x1F01FF
    for generic, specific in (
        (0x80000000, 0x120089),
        (0x40000000, 0x120116),
        (0x20000000, 0x1200A0),
        (0x10000000, 0x1F01FF),
    ):
        if mask & generic:
            mapped |= specific
    return mapped


def _evaluate_descriptor(parsed: _Descriptor, principal: bytes, role: str) -> None:
    trusted = {principal, _valid_sid(SYSTEM_SID), _valid_sid(ADMINISTRATORS_SID)}
    new = role != "existing_parent"
    if parsed.owner not in ({principal} if new else trusted):
        raise SecurityInspectionError(
            "Owner fuera de la allowlist; excepción TI pendiente"
        )
    if new and not parsed.control & 0x1000:
        raise SecurityInspectionError("DACL nueva no protegida")
    previous_rank = -1
    dangerous = {
        "journal": 0xD0116,
        "protected_domain": 0xD0156,
        "existing_parent": 0xD0150,
    }[role]
    for entry in parsed.aces:
        if entry.kind not in (0, 1) or entry.flags & ~0x1F:
            raise SecurityInspectionError("Tipo o flags ACE no soportados")
        if entry.flags & 0x0C and not entry.flags & 0x03:
            raise SecurityInspectionError("IO/NP sin propagación")
        if (
            entry.trustee[2:8] == b"\x00\x00\x00\x00\x00\x03"
            or entry.trustee == b"\x01\x01\x00\x00\x00\x00\x00\x05\x0a\x00\x00\x00"
        ):
            raise SecurityInspectionError("Trustee genérico no ratificado")
        rights = _mapped_rights(entry.mask)
        rank = (2 if entry.flags & 0x10 else 0) + (1 if entry.kind == 0 else 0)
        if rank < previous_rank:
            raise SecurityInspectionError("Orden DACL no canónico")
        previous_rank = rank
        outsider = entry.trustee not in trusted
        if new and (entry.kind != 0 or entry.flags & 0x10 or outsider):
            raise SecurityInspectionError("Descriptor nuevo no cerrado")
        if entry.kind == 0 and outsider:
            if not entry.flags & 0x08 and rights & dangerous:
                raise SecurityInspectionError("ALLOW outsider efectivo peligroso")
            if entry.flags & 0x03 and rights & 0xD0156:
                raise SecurityInspectionError("Propagación peligrosa no acreditada")


def read_handle_security(handle):
    """Obtiene una copia diagnóstica; el handle del caller es prestado."""
    binding = _windows_api()
    if type(handle) is not int or handle <= 0 or handle >= 2**64 - 1:
        raise SecurityInspectionError("Handle prestado inválido")
    with _owned_resource(binding.LocalFree, local_free=True) as allocation:
        outcome = binding.GetSecurityInfo(
            handle, 1, 7, None, None, None, None, ctypes.byref(allocation)
        )
        if outcome != 0 or allocation.value is None:
            raise SecurityInspectionError("Consulta OWNER/GROUP/DACL fallida")
        if not binding.IsValidSecurityDescriptor(allocation):
            raise SecurityInspectionError("Descriptor nativo inválido")
        size = binding.GetSecurityDescriptorLength(allocation)
        if size < 20 or size > MAX_DESCRIPTOR:
            raise SecurityInspectionError("Descriptor nativo fuera de límites")
        flags = ctypes.c_uint16()
        version = ctypes.c_uint32()
        available = binding.GetSecurityDescriptorControl(
            allocation, ctypes.byref(flags), ctypes.byref(version)
        )
        if not available:
            raise SecurityInspectionError("Control nativo no disponible")
        copied = ctypes.string_at(allocation, size)
        decoded = _parse_descriptor(copied)
        if version.value != 1 or decoded.control != flags.value:
            raise SecurityInspectionError("Control nativo inconsistente")
        result = SecurityObservation(copied)
        if type(binding) is _WindowsApi:
            object.__setattr__(result, "_origin", _NATIVE_OBSERVATION)
        return result


def current_security_principal():
    """Acredita TokenUser sin aceptar impersonación ni autoridad del owner."""
    binding = _windows_api()
    with _owned_resource(binding.CloseHandle) as owned_token:
        thread_has_token = binding.OpenThreadToken(
            binding.GetCurrentThread(), 8, 1, ctypes.byref(owned_token)
        )
        thread_error = ctypes.get_last_error()
        _reject_pseudo_handle(owned_token)
        if thread_has_token:
            raise SecurityInspectionError("Impersonación no ratificada")
        if thread_error != 1008 or owned_token.value is not None:
            raise SecurityInspectionError("Ausencia de impersonación no acreditada")
        opened = binding.OpenProcessToken(
            binding.GetCurrentProcess(), 8, ctypes.byref(owned_token)
        )
        _reject_pseudo_handle(owned_token)
        if not opened or owned_token.value is None:
            raise SecurityInspectionError("Token de proceso no disponible")
        capacity = ctypes.c_uint32()
        sizing = binding.GetTokenInformation(
            owned_token, 1, None, 0, ctypes.byref(capacity)
        )
        if sizing or ctypes.get_last_error() != 122:
            raise SecurityInspectionError("Consulta de tamaño TokenUser fallida")
        if capacity.value < 16 or capacity.value > 65536:
            raise SecurityInspectionError("Tamaño TokenUser fuera de límites")
        storage = ctypes.create_string_buffer(capacity.value)
        fetched = binding.GetTokenInformation(
            owned_token, 1, storage, len(storage), ctypes.byref(capacity)
        )
        if not fetched:
            raise SecurityInspectionError("Lectura TokenUser fallida")
        if capacity.value < 16 or capacity.value > len(storage):
            raise SecurityInspectionError("Longitud TokenUser inconsistente")
        base = ctypes.addressof(storage)
        end = base + capacity.value
        sid_address = ctypes.c_void_p.from_buffer(storage).value
        if sid_address is None or not base + 16 <= sid_address <= end - 8:
            raise SecurityInspectionError("SID TokenUser fuera de buffer")
        header = ctypes.string_at(sid_address, 8)
        sid_size = 8 + 4 * header[1]
        if sid_size > 68 or sid_address + sid_size > end:
            raise SecurityInspectionError("SID TokenUser truncado")
        user_sid = _valid_sid(ctypes.string_at(sid_address, sid_size))
        if not binding.IsValidSid(sid_address):
            raise SecurityInspectionError("SID TokenUser nativo inválido")
        if binding.GetLengthSid(sid_address) != sid_size:
            raise SecurityInspectionError("Longitud SID nativa inconsistente")
        return user_sid


def _reject_pseudo_handle(token):
    if token.value is None or token.value < 2**64 - 2:
        return
    token.value = None
    raise SecurityInspectionError("Pseudo-handle no es un token propio")


@contextmanager
def _owned_resource(cleanup, *, local_free=False):
    owned = ctypes.c_void_p()
    active_error = None
    try:
        yield owned
    except BaseException as failure:
        active_error = failure
        if isinstance(failure, Exception) and not isinstance(
            failure, SecurityInspectionError
        ):
            active_error = SecurityInspectionError("Consulta nativa no acreditada")
            raise active_error from failure
        raise
    finally:
        saved = owned.value
        owned.value = None
        can_release = saved is not None and (local_free or saved < 2**64 - 2)
        if can_release:
            try:
                returned = cleanup(saved)
                failed = returned is not None if local_free else not returned
                if failed:
                    raise SecurityInspectionError("Cleanup de recurso propio falló")
            except BaseException as cleanup_error:
                if active_error is not None:
                    active_error.add_note(
                        f"Cleanup separado: {type(cleanup_error).__name__}"
                    )
                elif isinstance(cleanup_error, Exception) and not isinstance(
                    cleanup_error, SecurityInspectionError
                ):
                    raise SecurityInspectionError(
                        "Cleanup de recurso propio falló"
                    ) from cleanup_error
                else:
                    raise


def _windows_api():
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise PlatformUnsupportedError("Se requiere Windows de 64 bits")
    try:
        return _WindowsApi()
    except (OSError, AttributeError) as error:
        raise SecurityInspectionError("Binding Win32 no disponible") from error


class _WindowsApi:
    """ABI explícita: DWORD/BOOL de 32 bits, punteros de 64 bits."""

    def __init__(self):
        adv = ctypes.WinDLL("advapi32.dll", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        pointer, dword, boolean = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
        signatures = [
            (kernel, "GetCurrentProcess", [], pointer),
            (kernel, "GetCurrentThread", [], pointer),
            (kernel, "CloseHandle", [pointer], boolean),
            (kernel, "LocalFree", [pointer], pointer),
            (
                adv,
                "OpenThreadToken",
                [pointer, dword, boolean, ctypes.POINTER(pointer)],
                boolean,
            ),
            (
                adv,
                "OpenProcessToken",
                [pointer, dword, ctypes.POINTER(pointer)],
                boolean,
            ),
            (
                adv,
                "GetTokenInformation",
                [pointer, dword, pointer, dword, ctypes.POINTER(dword)],
                boolean,
            ),
            (adv, "IsValidSid", [pointer], boolean),
            (adv, "GetLengthSid", [pointer], dword),
            (
                adv,
                "GetSecurityInfo",
                [
                    pointer,
                    ctypes.c_int32,
                    dword,
                    ctypes.POINTER(pointer),
                    ctypes.POINTER(pointer),
                    ctypes.POINTER(pointer),
                    ctypes.POINTER(pointer),
                    ctypes.POINTER(pointer),
                ],
                dword,
            ),
            (adv, "IsValidSecurityDescriptor", [pointer], boolean),
            (adv, "GetSecurityDescriptorLength", [pointer], dword),
            (
                adv,
                "GetSecurityDescriptorControl",
                [pointer, ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(dword)],
                boolean,
            ),
        ]
        for lib, name, args, result in signatures:
            function = getattr(lib, name)
            function.argtypes, function.restype = args, result
            setattr(self, name, function)
