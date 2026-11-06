"""Inspección local readonly; ningún resultado admite una cadena del journal."""

import ctypes
import os
import struct
import threading
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


class NativeObservationError(Exception):
    code = "NATIVE_OBSERVATION_UNACCREDITED"


class IOCompletionUnaccreditedError(NativeObservationError):
    code = "IO_COMPLETION_UNACCREDITED"


def _validate_component(name):
    if type(name) is not str or not name or name in (".", ".."):
        raise NativeObservationError("Componente inválido")
    if any(ord(c) < 32 or c in '\\/:*?"<>|' for c in name) or name[-1] in ". ":
        raise NativeObservationError("Componente inválido")
    try:
        encoded = name.encode("utf-16-le")
    except UnicodeError as error:
        raise NativeObservationError("UTF16 inválido") from error
    if len(encoded) > 510:
        raise NativeObservationError("Componente fuera de límites")
    stem = name.split(".", 1)[0].upper()
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(
        prefix + digit for prefix in ("COM", "LPT") for digit in "123456789¹²³"
    )
    if stem in reserved:
        raise NativeObservationError("Nombre de dispositivo no admitido")
    return name


class _ObservationContext:
    def __init__(self, api=None):
        self.lock = _OBSERVATION_LOCK
        self.api = _observation_api() if api is None else api
        self.owned = set()

    def check(self):
        if _RETAINED is not None:
            raise IOCompletionUnaccreditedError(
                "Retirada del proceso propietario requerida"
            )

    def retain(self, arena):
        global _RETAINED
        if _RETAINED is None:
            _RETAINED = (
                self,
                getattr(self, "_geometry_custody", arena),
                tuple(_LIVE_CONTEXTS),
                arena,  # Preserve the entered metadata arena as well as geometry.
            )
        raise IOCompletionUnaccreditedError("Completion no acreditada; retirar owner")

    def call(self, arena, function, *args, pending=None):
        self.check()
        # Resolve binding/arguments before entered. No finally may release this arena.
        try:
            returned = function(*args)
            if pending is not None and pending(returned):
                self.retain(arena)
            return returned
        except BaseException as error:  # noqa: BLE001 - conserva ownership incluso ante interrupción
            try:
                self.retain(arena)
            except IOCompletionUnaccreditedError as failure:
                raise failure from error


class _BorrowedDirectory:
    """Owner confiable conserva adquisición y coopera con context.lock hasta reap.

    Una referencia al owner no evita un CloseHandle externo. No acredita cadena,
    modo de apertura del parent, ACL ni autoridad de un root de producto.
    """

    def __init__(self, owner, context):
        self.owner, self.context = owner, context

    @property
    def _handle(self):
        return self.owner.handle


class _ObservedHandle:
    def __init__(self, handle, kind, parent):
        self._acquisition = (
            handle,
            parent,
            parent.context,
            parent.owner,
            parent._handle,
        )
        self._handle, self.kind = handle, kind
        self.parent, self.context = parent, parent.context
        self._close_observation = None
        self.context.owned.add(self)
        _LIVE_CONTEXTS.add(self.context)

    def close(self):
        with self.context.lock:
            previous = self._close_observation
            if previous is not None:
                return previous
            acquisition = self._handle
            arena = _CallArena(self)
            arena.acquisition = acquisition
            unknown = _LocalCloseObservation("unknown", ("IO_COMPLETION_UNACCREDITED",))
            try:
                # Reserve idempotence before revoking authority or entering native.
                self._close_observation = unknown
                self._handle = None
                if _RETAINED is not None:
                    return unknown
                else:
                    accepted = bool(self.context.api.CloseHandle(acquisition))
                    reasons = () if accepted else ("CloseHandleFalse",)
                    result = _LocalCloseObservation(
                        "closed" if accepted else "unknown", reasons
                    )
                    self._close_observation = result
                    if accepted:
                        self.context.owned.remove(self)
                        if not self.context.owned:
                            _LIVE_CONTEXTS.discard(self.context)
                    else:
                        self.context.retain(arena)
                    return result
            except BaseException as error:  # noqa: BLE001 - una interrupción requiere reap
                self._handle = None
                if (
                    self._close_observation is None
                    or self._close_observation is unknown
                    or self._close_observation.state == "closed"
                ):
                    self._close_observation = _LocalCloseObservation(
                        "unknown", (type(error).__name__,)
                    )
                # Keep this owner even if interrupted halfway through deregistration.
                self.context.owned.add(self)
                _LIVE_CONTEXTS.add(self.context)
                try:
                    self.context.retain(arena)
                except IOCompletionUnaccreditedError:
                    pass
                return self._close_observation

    def __enter__(self):
        return self

    def __exit__(self, kind, primary, traceback):
        observation = self.close()
        if observation.state == "closed":
            return False
        if primary is None:
            raise NativeObservationError("Cierre del contexto no acreditado")
        primary.add_note("Cleanup separado: " + ",".join(observation.causes))
        return False


def _open_relative_existing(parent, name, kind):
    _validate_component(name)
    if (
        type(parent) is not _BorrowedDirectory
        or type(kind) is not str
        or kind not in ("directory", "file")
    ):
        raise NativeObservationError("Parent o tipo no liberado")
    context = parent.context
    with context.lock:
        context.check()
        read_handle_metadata(parent)
        encoded = name.encode("utf-16-le")
        arena = _CallArena(parent)
        arena.name = ctypes.create_string_buffer(encoded + b"\0\0")
        arena.unicode = _UnicodeString(
            len(encoded), len(encoded) + 2, ctypes.addressof(arena.name)
        )
        arena.attributes = _ObjectAttributes(
            ctypes.sizeof(_ObjectAttributes),
            parent._handle,
            ctypes.pointer(arena.unicode),
            OBJ_DONT_REPARSE,
            None,
            None,
        )
        arena.iosb = _IoStatusBlock()
        arena.output = ctypes.c_void_p()
        directory = kind == "directory"
        access = (
            READ_CONTROL
            | SYNCHRONIZE
            | FILE_READ_ATTRIBUTES
            | (FILE_TRAVERSE if directory else FILE_READ_DATA)
        )
        share = FILE_SHARE_READ | (FILE_SHARE_WRITE if directory else 0)
        options = (
            FILE_SYNCHRONOUS_IO_NONALERT
            | FILE_OPEN_REPARSE_POINT
            | (FILE_DIRECTORY_FILE if directory else FILE_NON_DIRECTORY_FILE)
        )
        child = None
        try:
            # Custody spans native return, recognition and wrapper registration.
            status = context.call(
                arena,
                context.api.NtCreateFile,
                ctypes.byref(arena.output),
                access,
                ctypes.byref(arena.attributes),
                ctypes.byref(arena.iosb),
                None,
                0,
                share,
                FILE_OPEN,
                options,
                None,
                0,
                pending=lambda result: result == STATUS_PENDING,
            )
            if status != STATUS_SUCCESS:
                raise NativeObservationError("FILE_OPEN no acreditado")
            value = arena.output.value
            if not _valid_observed_handle(value):
                raise NativeObservationError("Adquisición propia inválida")
            child = _ObservedHandle(value, kind, parent)
            if arena.iosb.Information != FILE_OPENED:
                raise NativeObservationError("Resultado no es FILE_OPENED")
            read_handle_metadata(child)
            return child
        except IOCompletionUnaccreditedError:
            # The retained query arena owns child -> parent -> cooperative owner.
            raise
        except NativeObservationError as primary:
            if child is not None:
                cleanup = child.close()
                if cleanup.state != "closed":
                    primary.add_note("Cleanup separado: cierre no acreditado")
            raise
        except BaseException as error:  # noqa: BLE001 - custodia de adquisición sin transferir
            try:
                context.retain(arena)
            except IOCompletionUnaccreditedError as failure:
                raise failure from error


def read_handle_metadata(observed):
    if type(observed) not in (_BorrowedDirectory, _ObservedHandle):
        raise NativeObservationError("Observador local requerido")
    context = observed.context
    with context.lock:
        context.check()
        handle = observed._handle
        if not _valid_observed_handle(handle):
            raise NativeObservationError("Observador retirado")
        expected = (
            "directory" if type(observed) is _BorrowedDirectory else observed.kind
        )
        arena = _CallArena(observed)
        file_type = context.call(arena, context.api.GetFileType, handle)
        if file_type != FILE_TYPE_DISK:
            raise NativeObservationError("Sólo objeto disk local")
        arena.identity, arena.attributes, arena.standard = (
            _FileIdInfo(),
            _FileAttributeTagInfo(),
            _FileStandardInfo(),
        )
        for info, buffer in (
            (FileIdInfo, arena.identity),
            (FileAttributeTagInfo, arena.attributes),
            (FileStandardInfo, arena.standard),
        ):
            returned = context.call(
                arena,
                context.api.GetFileInformationByHandleEx,
                handle,
                info,
                ctypes.byref(buffer),
                ctypes.sizeof(buffer),
                pending=lambda result: (
                    not result and ctypes.get_last_error() == ERROR_IO_PENDING
                ),
            )
            if not returned:
                raise NativeObservationError("Metadata no disponible")
        arena.path = ctypes.create_unicode_buffer(32768)
        length = context.call(
            arena,
            context.api.GetFinalPathNameByHandleW,
            handle,
            arena.path,
            len(arena.path),
            0,
            pending=lambda result: (
                not result and ctypes.get_last_error() == ERROR_IO_PENDING
            ),
        )
        if not 0 < length < len(arena.path):
            raise NativeObservationError("Longitud de ruta no acreditada")
        path = arena.path.value
        _validate_final_path(path)
        identity, attrs, standard = arena.identity, arena.attributes, arena.standard
        actual = "directory" if standard.Directory else "file"
        if (
            attrs.FileAttributes
            & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DEVICE)
            or attrs.ReparseTag
            or standard.DeletePending
            or standard.Directory not in (0, 1)
            or bool(attrs.FileAttributes & FILE_ATTRIBUTE_DIRECTORY)
            != bool(standard.Directory)
            or actual != expected
            or not standard.NumberOfLinks
            or (actual == "file" and standard.NumberOfLinks != 1)
            or standard.EndOfFile < 0
            or standard.AllocationSize < 0
            or (actual == "file" and standard.AllocationSize < standard.EndOfFile)
        ):
            raise NativeObservationError("Metadata fuera de política local")
        return MetadataObservation(
            identity.VolumeSerialNumber,
            bytes(identity.FileId.Identifier),
            path,
            actual,
            attrs.FileAttributes,
            attrs.ReparseTag,
            standard.NumberOfLinks,
            bool(standard.DeletePending),
            standard.EndOfFile,
            standard.AllocationSize,
            tuple(bytes(buffer) for buffer in (identity, attrs, standard)),
        )


# SDK/WDK constants: ntifs.h, ntdef.h, winnt.h, minwinbase.h.
# Microsoft Learn primary ABI sources recorded in primary-sources.json.
FILE_READ_DATA = 0x1
FILE_TRAVERSE = 0x20
FILE_READ_ATTRIBUTES = 0x80
READ_CONTROL = 0x20000
SYNCHRONIZE = 0x100000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
FILE_DIRECTORY_FILE = 0x1
FILE_SYNCHRONOUS_IO_NONALERT = 0x20
FILE_NON_DIRECTORY_FILE = 0x40
FILE_OPEN_REPARSE_POINT = 0x200000
FILE_OPEN = 1
FILE_OPENED = 1
OBJ_DONT_REPARSE = 0x1000
STATUS_SUCCESS = 0
STATUS_PENDING = 0x103
ERROR_IO_PENDING = 997
FILE_TYPE_DISK = 1
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_DEVICE = 0x40
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FileStandardInfo = 1
FileAttributeTagInfo = 9
FileIdInfo = 18
_RETAINED = None
_OBSERVATION_LOCK = threading.RLock()
_LIVE_CONTEXTS = set()


class _UnicodeString(ctypes.Structure):
    _fields_ = [
        ("Length", ctypes.c_uint16),
        ("MaximumLength", ctypes.c_uint16),
        ("Buffer", ctypes.c_void_p),
    ]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("Length", ctypes.c_uint32),
        ("RootDirectory", ctypes.c_void_p),
        ("ObjectName", ctypes.POINTER(_UnicodeString)),
        ("Attributes", ctypes.c_uint32),
        ("SecurityDescriptor", ctypes.c_void_p),
        ("SecurityQualityOfService", ctypes.c_void_p),
    ]


class _StatusUnion(ctypes.Union):
    _fields_ = [("Status", ctypes.c_int32), ("Pointer", ctypes.c_void_p)]


class _IoStatusBlock(ctypes.Structure):
    _anonymous_ = ("status",)
    _fields_ = [("status", _StatusUnion), ("Information", ctypes.c_size_t)]


class _FileId128(ctypes.Structure):
    _fields_ = [("Identifier", ctypes.c_ubyte * 16)]


class _FileIdInfo(ctypes.Structure):
    _fields_ = [("VolumeSerialNumber", ctypes.c_uint64), ("FileId", _FileId128)]


class _FileAttributeTagInfo(ctypes.Structure):
    _fields_ = [("FileAttributes", ctypes.c_uint32), ("ReparseTag", ctypes.c_uint32)]


class _FileStandardInfo(ctypes.Structure):
    _fields_ = [
        ("AllocationSize", ctypes.c_int64),
        ("EndOfFile", ctypes.c_int64),
        ("NumberOfLinks", ctypes.c_uint32),
        ("DeletePending", ctypes.c_ubyte),
        ("Directory", ctypes.c_ubyte),
    ]


class _CallArena:
    def __init__(self, owner):
        self.owner = owner


_GEOMETRY_SOURCE = "nt-volume-sector11+nt-file-alignment17/v1"
_SECTOR_FIELDS = (
    "logical_bytes_per_sector",
    "physical_bytes_per_sector_for_atomicity",
    "physical_bytes_per_sector_for_performance",
    "filesystem_effective_physical_bytes_per_sector_for_atomicity",
    "flags",
    "sector_alignment_offset",
    "partition_alignment_offset",
)


class _FileFsSectorSizeInformation(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in _SECTOR_FIELDS]


class _FileAlignmentInformation(ctypes.Structure):
    _fields_ = [("AlignmentRequirement", ctypes.c_uint32)]


@dataclass(frozen=True)
class NtSectorSizeObservation:
    information_class: int
    requested_bytes: int
    ntstatus: int
    iosb_status: int
    information: int
    raw: bytes
    logical_bytes_per_sector: int
    physical_bytes_per_sector_for_atomicity: int
    physical_bytes_per_sector_for_performance: int
    filesystem_effective_physical_bytes_per_sector_for_atomicity: int
    flags: int
    sector_alignment_offset: int
    partition_alignment_offset: int


@dataclass(frozen=True)
class NtAlignmentObservation:
    information_class: int
    requested_bytes: int
    ntstatus: int
    iosb_status: int
    information: int
    raw: bytes
    alignment_mask: int


@dataclass(frozen=True)
class GeometryObservation:
    source: str
    sector: NtSectorSizeObservation
    alignment: NtAlignmentObservation
    parent_before: "MetadataObservation"
    object_before: "MetadataObservation"
    object_after: "MetadataObservation"
    parent_after: "MetadataObservation"


@dataclass(frozen=True)
class GeometryDiagnostic:
    source: str
    candidate_b: int | None
    causes: tuple[str, ...]


def derive_geometry_candidate(observation):
    """Calcula un número lógico readonly; nunca acredita capacidad nativa."""
    if (
        type(observation) is not GeometryObservation
        or type(observation.sector) is not NtSectorSizeObservation
        or type(observation.alignment) is not NtAlignmentObservation
    ):
        return GeometryDiagnostic(_GEOMETRY_SOURCE, None, ("RAW_INVALID",))
    sector = observation.sector
    operands = tuple(getattr(sector, name) for name in _SECTOR_FIELDS) + (
        observation.alignment.alignment_mask,
    )
    if any(type(n) is not int or not 0 <= n <= 0xFFFFFFFF for n in operands):
        return GeometryDiagnostic(_GEOMETRY_SOURCE, None, ("RAW_INVALID",))
    sizes = tuple(getattr(sector, name) for name in _SECTOR_FIELDS[:4])
    causes = [] if _geometry_raw_valid(observation) else ["RAW_INVALID"]
    if 0 in sizes:
        causes.append("GEOMETRY_SIZE_UNKNOWN")
    if any(n and (not 512 <= n <= 65536 or n & (n - 1)) for n in sizes):
        causes.append("GEOMETRY_SIZE_INVALID")
    valid_sizes = all(n and 512 <= n <= 65536 and not n & (n - 1) for n in sizes)
    if valid_sizes and any(n < sizes[0] or n % sizes[0] for n in sizes[1:]):
        causes.append("GEOMETRY_SIZE_INCOHERENT")
    mask = observation.alignment.alignment_mask
    valid_mask = mask in (0, 1, 3, 7, 15, 31, 63, 127, 255, 511)
    if not valid_mask:
        causes.append("GEOMETRY_ALIGNMENT_MASK_INVALID")
    if sector.flags & ~15:
        causes.append("GEOMETRY_FLAGS_UNKNOWN")
    offsets = (sector.sector_alignment_offset, sector.partition_alignment_offset)
    if 0xFFFFFFFF in offsets:
        causes.append("GEOMETRY_OFFSET_UNKNOWN")
    if sector.flags & 1 and offsets[0] not in (0, 0xFFFFFFFF):
        causes.append("GEOMETRY_ALIGNMENT_CONTRADICTION")
    if any(n not in (0, 0xFFFFFFFF) for n in offsets):
        causes.append("GEOMETRY_OFFSET_NOT_ACCREDITED")
    if sector.flags & 3 != 3:
        causes.append("GEOMETRY_ALIGNMENT_NOT_CORROBORATED")
    candidate = None
    if valid_sizes and valid_mask:
        alignment_bytes = mask + 1
        candidate = max(*sizes, alignment_bytes)
        if (
            not 512 <= candidate <= 65536
            or candidate & (candidate - 1)
            or any(candidate % n for n in (*sizes, alignment_bytes))
        ):
            causes.append("GEOMETRY_B_OUT_OF_WIRE")
    return GeometryDiagnostic(
        _GEOMETRY_SOURCE, None if causes else candidate, tuple(causes)
    )


def _geometry_raw_valid(observed):
    if (
        type(observed) is not GeometryObservation
        or type(observed.source) is not str
        or observed.source != _GEOMETRY_SOURCE
    ):
        return False
    if any(
        type(value) is not MetadataObservation
        for value in (
            observed.parent_before,
            observed.object_before,
            observed.object_after,
            observed.parent_after,
        )
    ):
        return False
    for value, expected_type, info_class, size, fields in (
        (observed.sector, NtSectorSizeObservation, 11, 28, _SECTOR_FIELDS),
        (observed.alignment, NtAlignmentObservation, 17, 4, ("alignment_mask",)),
    ):
        if type(value) is not expected_type:
            return False
        for name, expected in (
            ("information_class", info_class),
            ("requested_bytes", size),
            ("ntstatus", 0),
            ("iosb_status", 0),
            ("information", size),
        ):
            if (
                type(getattr(value, name)) is not int
                or getattr(value, name) != expected
            ):
                return False
        numbers = tuple(getattr(value, name) for name in fields)
        if any(type(n) is not int or not 0 <= n <= 0xFFFFFFFF for n in numbers):
            return False
        if (
            type(value.raw) is not bytes
            or len(value.raw) != size
            or struct.unpack("<" + "I" * len(fields), value.raw) != numbers
        ):
            return False
    return True


def read_handle_geometry(observed):
    """Dos consultas readonly de la misma adquisición; no abre ni cierra."""
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise PlatformUnsupportedError("Se requiere Windows de 64 bits")
    if (
        type(observed) is not _ObservedHandle
        or type(observed.context) is not _ObservationContext
    ):
        raise NativeObservationError("Adquisición propia requerida")
    context = observed.context
    with context.lock:
        context.check()
        parent = observed.parent
        if (
            type(parent) is not _BorrowedDirectory
            or parent.context is not context
            or observed not in context.owned
            or not _valid_observed_handle(observed._handle)
            or observed._close_observation is not None
        ):
            raise NativeObservationError("Acquisición retirada o parent ajeno")
        acquisition = observed._acquisition
        _check_geometry_acquisition(observed, acquisition)
        _check_geometry_abi()
        try:
            functions = (
                context.api.NtQueryVolumeInformationFile,
                context.api.NtQueryInformationFile,
            )
        except AttributeError as error:
            raise NativeObservationError("Binding de geometría ausente") from error
        if not all(callable(function) for function in functions):
            raise NativeObservationError("Binding de geometría inválido")
        parent_before = read_handle_metadata(parent)
        _check_geometry_acquisition(observed, acquisition)
        object_before = read_handle_metadata(observed)
        _check_geometry_acquisition(observed, acquisition)
        if parent_before.volume_serial != object_before.volume_serial:
            raise NativeObservationError("Volumen del parent inconsistente")
        arena = _CallArena(observed)
        arena.parent, arena.context = parent, context
        arena.acquisition = acquisition
        arena.buffers = (_FileFsSectorSizeInformation(), _FileAlignmentInformation())
        arena.iosbs = (_IoStatusBlock(), _IoStatusBlock())
        for buffer, iosb, size in zip(arena.buffers, arena.iosbs, (28, 4), strict=True):
            ctypes.memset(ctypes.addressof(buffer), 0xA5, size)
            iosb.Status, iosb.Information = -2147483648, 2**64 - 1
        arguments = tuple(
            (
                observed._handle,
                ctypes.byref(iosb),
                ctypes.byref(buffer),
                size,
                info_class,
            )
            for buffer, iosb, size, info_class in zip(
                arena.buffers, arena.iosbs, (28, 4), (11, 17), strict=True
            )
        )
        responses = []
        context._geometry_custody = arena
        try:
            for index, (function, args) in enumerate(
                zip(functions, arguments, strict=True)
            ):
                _check_geometry_acquisition(observed, acquisition, complete=True)
                status = context.call(
                    arena,
                    function,
                    *args,
                    pending=lambda returned: returned == STATUS_PENDING,
                )
                if status != STATUS_SUCCESS:
                    raise _GeometryCompleteRejection("Query NT no acreditada")
                _check_geometry_acquisition(observed, acquisition, complete=True)
                iosb, size, info_class = arena.iosbs[index], args[3], args[4]
                if iosb.Status != STATUS_SUCCESS or iosb.Information != size:
                    raise _GeometryCompleteRejection(
                        "Completion geométrica inconsistente"
                    )
                raw = bytes(arena.buffers[index])
                fields = struct.unpack("<7I" if index == 0 else "<I", raw)
                result_type = (
                    NtSectorSizeObservation if index == 0 else NtAlignmentObservation
                )
                responses.append(
                    result_type(
                        info_class,
                        size,
                        status,
                        iosb.Status,
                        iosb.Information,
                        raw,
                        *fields,
                    )
                )
            try:
                object_after = read_handle_metadata(observed)
                _check_geometry_acquisition(observed, acquisition, complete=True)
                parent_after = read_handle_metadata(parent)
                _check_geometry_acquisition(observed, acquisition, complete=True)
            except IOCompletionUnaccreditedError:
                raise
            except NativeObservationError as error:
                raise _GeometryCompleteRejection(
                    "Postmetadata no acreditada"
                ) from error
            if parent_before != parent_after or object_before != object_after:
                raise _GeometryCompleteRejection("Identidad de geometría cambió")
            result = GeometryObservation(
                _GEOMETRY_SOURCE,
                *responses,
                parent_before,
                object_before,
                object_after,
                parent_after,
            )
            del context._geometry_custody
            return result
        except _GeometryCompleteRejection as error:
            try:
                del context._geometry_custody
            except BaseException as interruption:  # noqa: BLE001 - fallo de transferencia
                try:
                    context.retain(arena)
                except IOCompletionUnaccreditedError as failure:
                    raise failure from interruption
            raise NativeObservationError(str(error)) from error
        except BaseException as error:  # noqa: BLE001 - retiene ambas arenas hasta reap
            try:
                context.retain(arena)
            except IOCompletionUnaccreditedError as failure:
                raise failure from error


class _GeometryCompleteRejection(NativeObservationError):
    """Rechazo privado sólo después de retorno acreditado."""


def _check_geometry_acquisition(observed, acquisition, *, complete=False):
    handle, parent, context, parent_owner, parent_handle = acquisition
    if (
        observed._handle != handle
        or type(observed._handle) is not int
        or observed.parent is not parent
        or observed.context is not context
        or parent.context is not context
        or parent.owner is not parent_owner
        or parent._handle != parent_handle
        or observed not in context.owned
        or observed._close_observation is not None
        or not _valid_observed_handle(parent._handle)
    ):
        error_type = _GeometryCompleteRejection if complete else NativeObservationError
        raise error_type("Acquisición original revocada")


def _check_geometry_abi():
    if (
        ctypes.sizeof(_IoStatusBlock),
        ctypes.alignment(_IoStatusBlock),
        _IoStatusBlock.status.offset,
        _IoStatusBlock.Information.offset,
    ) != (16, 8, 0, 8):
        raise NativeObservationError("ABI IOSB inválida")
    for struct_type, size, names in (
        (_FileFsSectorSizeInformation, 28, _SECTOR_FIELDS),
        (_FileAlignmentInformation, 4, ("AlignmentRequirement",)),
    ):
        if ctypes.sizeof(struct_type) != size or ctypes.alignment(struct_type) != 4:
            raise NativeObservationError("ABI geométrica inválida")
        if struct_type._fields_ != [(name, ctypes.c_uint32) for name in names]:
            raise NativeObservationError("Tipos ABI geométrica inválidos")
        if tuple(getattr(struct_type, name).offset for name in names) != tuple(
            range(0, size, 4)
        ):
            raise NativeObservationError("Offsets ABI geométrica inválidos")


@dataclass(frozen=True)
class MetadataObservation:
    """Copias readonly sin HANDLE; no admisión de store ni cadena."""

    volume_serial: int
    file_id: bytes
    final_path: str
    kind: str
    attributes: int
    reparse_tag: int
    links: int
    delete_pending: bool
    eof: int
    allocation: int
    raw: tuple[bytes, ...]


@dataclass(frozen=True)
class _LocalCloseObservation:
    state: str
    causes: tuple[str, ...] = ()


def _valid_observed_handle(value):
    return type(value) is int and 0 < value < 2**64 - 2


def _validate_final_path(path):
    if not (
        path.startswith("\\\\?\\")
        and len(path) >= 7
        and path[4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        and path[5:7] == ":\\"
    ):
        raise NativeObservationError("Ruta local normalizada requerida")
    parts = path[7:].split("\\")
    if parts == [""]:
        return
    for component in parts:
        _validate_component(component)


def _observation_api():
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise PlatformUnsupportedError("Se requiere Windows de 64 bits")
    try:
        return _ObservationApi()
    except (OSError, AttributeError) as error:
        raise NativeObservationError("Binding NT/Win32 no disponible") from error


class _ObservationApi:
    """Binding privado sin operaciones de escritura, wait, cancel ni retry."""

    def __init__(self):
        kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        nt = ctypes.WinDLL("ntdll.dll", use_last_error=True)
        pointer, dword, boolean = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
        signatures = [
            (
                nt,
                "NtCreateFile",
                [
                    ctypes.POINTER(pointer),
                    dword,
                    ctypes.POINTER(_ObjectAttributes),
                    ctypes.POINTER(_IoStatusBlock),
                    ctypes.POINTER(ctypes.c_int64),
                    dword,
                    dword,
                    dword,
                    dword,
                    pointer,
                    dword,
                ],
                ctypes.c_int32,
            ),
            (
                nt,
                "NtQueryVolumeInformationFile",
                [
                    pointer,
                    ctypes.POINTER(_IoStatusBlock),
                    pointer,
                    dword,
                    ctypes.c_int32,
                ],
                ctypes.c_int32,
            ),
            (
                nt,
                "NtQueryInformationFile",
                [
                    pointer,
                    ctypes.POINTER(_IoStatusBlock),
                    pointer,
                    dword,
                    ctypes.c_int32,
                ],
                ctypes.c_int32,
            ),
            (
                kernel,
                "GetFileInformationByHandleEx",
                [pointer, ctypes.c_int32, pointer, dword],
                boolean,
            ),
            (
                kernel,
                "GetFinalPathNameByHandleW",
                [pointer, ctypes.c_wchar_p, dword, dword],
                dword,
            ),
            (kernel, "GetFileType", [pointer], dword),
            (kernel, "CloseHandle", [pointer], boolean),
        ]
        for lib, name, args, result in signatures:
            function = getattr(lib, name)
            function.argtypes, function.restype = args, result
            setattr(self, name, function)
