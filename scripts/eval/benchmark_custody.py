"""Cápsulas individuales de bytes originales con custodia nativa de Windows.

El caller aporta sellos previamente confiados; un SHA coincidente y la identidad
del store NO autentican al proveedor, ni certifican aceptación semántica,
cadencia o continuidad histórica. No implementa packs, FINAL ni integración.
Linux falla cerrado: los permisos/advisory locks no demuestran inmutabilidad.

capture(deadline=...) usa un único límite monotónico absoluto, incluyendo
validación, pins, índice, lectura/hash de fuentes y relectura/hash del contenedor.
Cada entrada cuesta una apertura/pin y dos lecturas completas de su longitud
(hash previo a cualquier grabación y copia bajo el mismo pin);
la verificación final relee el contenedor completo (máximo 64 MiB). read cuesta
comprobar identidades y un ReadFile de hasta 256 KiB, sin releer el historial.
Las llamadas síncronas al kernel no se cancelan: si retornan tarde se rechaza
el resultado. Se serializan operaciones; close libera sólo handles propios,
conserva las cápsulas en disco y revoca acceso. Limpieza incierta conserva
referencias en cuarentena explícita; no acredita devolución de recursos.
"""

from __future__ import annotations

import ctypes
import hashlib
import math
import os
import re
import struct
import sys
import threading
import time
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

MAX_CAPSULE = 64 * 1024 * 1024
MAX_ENTRIES = 128
MAX_READ = 256 * 1024
_CHUNK = 256 * 1024
_HEADER = struct.Struct("<8sI")
_ENTRY = struct.Struct("<64sQQ32s")
_MAGIC = b"BCAP0001"
_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,63}\Z")
_SEAL = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[0-9a-f]{32}\Z")


class CustodyError(RuntimeError):
    """No hay bytes acreditables mediante esta operación de custodia."""


class UnsupportedPlatform(CustodyError):
    """La plataforma no proporciona protección nativa demostrada."""


@dataclass(frozen=True)
class SourceEntry:
    name: str
    path: Path
    length: int
    seal: str


@dataclass(frozen=True)
class CapsuleRef:
    """Identificador opaco ligado a una instancia; no es un certificado."""

    store_id: str
    capsule_id: str


@dataclass(frozen=True)
class _IndexEntry:
    name: str
    offset: int
    length: int
    seal: str


@dataclass
class _Capsule:
    pin: _Pin
    entries: dict[str, _IndexEntry]
    seal: str


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD),
        ("created", wintypes.FILETIME),
        ("accessed", wintypes.FILETIME),
        ("written", wintypes.FILETIME),
        ("volume", wintypes.DWORD),
        ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD),
        ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD),
        ("index_low", wintypes.DWORD),
    ]


def _platform():
    return os.name


_DLL = None
# Retiene referencias incluso si el caller pierde el pin durante unwinding.
# Sólo terminar el worker PROPIO con ownership PID/creation/Job certificado
# permite declarar recursos devueltos tras unknown_quarantined. No self-kill.
_QUARANTINED_PINS = []


def _native():
    global _DLL
    if _platform() != "nt":
        raise UnsupportedPlatform("Se requiere custodia nativa Windows")
    if _DLL is None:
        dll = ctypes.WinDLL("kernel32", use_last_error=True)
        try:
            dll.CompareObjectHandles = ctypes.WinDLL(
                "kernelbase", use_last_error=True
            ).CompareObjectHandles
        except (AttributeError, OSError) as error:
            raise UnsupportedPlatform(
                "CompareObjectHandles no disponible; custodia rechazada"
            ) from error
        signatures = {
            "CreateFileW": (
                [
                    wintypes.LPCWSTR,
                    wintypes.DWORD,
                    wintypes.DWORD,
                    ctypes.c_void_p,
                    wintypes.DWORD,
                    wintypes.DWORD,
                    wintypes.HANDLE,
                ],
                wintypes.HANDLE,
            ),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "SetHandleInformation": (
                [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD],
                wintypes.BOOL,
            ),
            "GetHandleInformation": (
                [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)],
                wintypes.BOOL,
            ),
            "GetFileInformationByHandle": (
                [wintypes.HANDLE, ctypes.POINTER(_FileInformation)],
                wintypes.BOOL,
            ),
            "GetFinalPathNameByHandleW": (
                [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD],
                wintypes.DWORD,
            ),
            "SetFilePointerEx": (
                [
                    wintypes.HANDLE,
                    ctypes.c_longlong,
                    ctypes.POINTER(ctypes.c_longlong),
                    wintypes.DWORD,
                ],
                wintypes.BOOL,
            ),
            "ReadFile": (
                [
                    wintypes.HANDLE,
                    ctypes.c_void_p,
                    wintypes.DWORD,
                    ctypes.POINTER(wintypes.DWORD),
                    ctypes.c_void_p,
                ],
                wintypes.BOOL,
            ),
            "GetCurrentProcess": ([], wintypes.HANDLE),
            "DuplicateHandle": (
                [
                    wintypes.HANDLE,
                    wintypes.HANDLE,
                    wintypes.HANDLE,
                    ctypes.POINTER(wintypes.HANDLE),
                    wintypes.DWORD,
                    wintypes.BOOL,
                    wintypes.DWORD,
                ],
                wintypes.BOOL,
            ),
            "CompareObjectHandles": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(dll, name)
            function.argtypes = arguments
            function.restype = result
        _DLL = dll
    return _DLL


def _check_deadline(deadline):
    if (
        type(deadline) not in (int, float)
        or not math.isfinite(deadline)
        or time.monotonic() >= deadline
    ):
        raise CustodyError("Deadline monotónico vencido o inválido")


def _integer(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise CustodyError("Entero fuera del límite cerrado")


def _name(value):
    if (
        not isinstance(value, str)
        or not _NAME.fullmatch(value)
        or ".." in value
        or value.endswith(".")
    ):
        raise CustodyError("Nombre no canónico")


def _path(value):
    if not isinstance(value, (str, Path)):
        raise CustodyError("Tipo de ruta no permitido")
    path = Path(value)
    if (
        not path.is_absolute()
        or str(path).startswith(("\\\\", "\\?"))
        or ".." in path.parts
        or any(":" in part for part in path.parts[1:])
    ):
        raise CustodyError("Se requiere ruta local absoluta sin aliases")
    return path


class _Pin:
    def __init__(self, path, *, directory=False):
        self.path = _path(path)
        self.directory = directory
        self.handle = None
        self._guard = None
        self.disposition = "owned"
        self._protected = False
        dll = _native()
        # SHARE_READ sólo: niega escritores/delete previos y posteriores.
        flags = 0x00200000 | (0x02000000 if directory else 0)
        handle = dll.CreateFileW(str(self.path), 0x80000000, 1, None, 3, flags, None)
        if handle == ctypes.c_void_p(-1).value:
            raise CustodyError(
                f"No se puede adquirir pin nativo: {ctypes.get_last_error()}"
            )
        self.handle = handle
        try:
            guard = wintypes.HANDLE()
            process = dll.GetCurrentProcess()
            if not dll.DuplicateHandle(
                process, handle, process, ctypes.byref(guard), 0, False, 2
            ):
                raise CustodyError("No se puede custodiar identidad del handle")
            self._guard = guard.value
            # Witness no reciclable por CloseHandle ordinario. No protege contra
            # código comprometido que retire/reinstale flags dentro del proceso.
            if not dll.SetHandleInformation(self._guard, 2, 2):
                raise CustodyError("No se puede proteger witness nativo")
            self._protected = True
            self._witness()
            self.identity = self._identity()
            attributes = self.identity[-1]
            if attributes & 0x400 or bool(attributes & 0x10) != directory:
                raise CustodyError("Reparse u objeto de tipo inesperado")
            self.verify()
        except BaseException:
            _release([self])
            raise

    def _witness(self):
        flags = wintypes.DWORD()
        if (
            self.disposition == "unknown_quarantined"
            or not self._protected
            or self._guard is None
            or not _native().GetHandleInformation(self._guard, ctypes.byref(flags))
            or not flags.value & 2
        ):
            raise CustodyError("Witness nativo perdido o protección modificada")

    def _identity(self):
        self._witness()
        info = _FileInformation()
        if self._guard is not None and not _native().CompareObjectHandles(
            self.handle, self._guard
        ):
            raise CustodyError(
                "Handle perdido o reutilizado para otro objeto de kernel"
            )
        if not self.handle or not _native().GetFileInformationByHandle(
            self.handle, ctypes.byref(info)
        ):
            raise CustodyError("Se perdió el handle nativo")
        return (
            info.volume,
            info.index_high,
            info.index_low,
            0 if self.directory else (info.size_high << 32) | info.size_low,
            info.attributes & 0x410,
        )

    def verify(self):
        if self._identity() != self.identity:
            raise CustodyError("Identidad nativa modificada")
        buffer = ctypes.create_unicode_buffer(32768)
        count = _native().GetFinalPathNameByHandleW(self.handle, buffer, len(buffer), 0)
        if not 0 < count < len(buffer) or os.path.normcase(
            buffer.value.removeprefix("\\\\?\\")
        ) != os.path.normcase(str(self.path)):
            raise CustodyError("Sustitución de ruta o pérdida de identidad")

    def read(self, offset, length, deadline):
        _check_deadline(deadline)
        _integer(offset, MAX_CAPSULE)
        _integer(length, _CHUNK)
        self.verify()
        if offset + length > self.identity[3]:
            raise CustodyError("Lectura fuera del objeto nativo")
        dll = _native()
        if not dll.SetFilePointerEx(self.handle, offset, None, 0):
            raise CustodyError("No se pudo establecer offset nativo")
        buffer = ctypes.create_string_buffer(length)
        count = wintypes.DWORD()
        if (
            not dll.ReadFile(self.handle, buffer, length, ctypes.byref(count), None)
            or count.value != length
        ):
            raise CustodyError("ReadFile incompleto o fallido")
        self.verify()
        _check_deadline(deadline)
        return buffer.raw

    def close(self):
        if self.disposition == "released":
            return
        if self.disposition == "unknown_quarantined":
            raise CustodyError("unknown_quarantined: referencias conservadas")
        dll = _native()
        try:
            if self._protected:
                self._witness()
            # Antes de instalar protección, ambas referencias recién creadas
            # siguen siendo propias; no se publican ni se comparan por filepath.
            if self.handle is not None:
                if (
                    not self._protected
                    or dll.CompareObjectHandles(self.handle, self._guard)
                ) and not dll.CloseHandle(self.handle):
                    raise CustodyError("CloseHandle principal falló")
                # Un slot distinto al witness no se cierra: ajeno o ya perdido.
                self.handle = None
            if self._guard is not None:
                if self._protected and not dll.SetHandleInformation(self._guard, 2, 0):
                    raise CustodyError("No se pudo desproteger witness propio")
                if not dll.CloseHandle(self._guard):
                    raise CustodyError("CloseHandle witness falló")
                self._guard = None
            self.disposition = "released"
        except CustodyError as error:
            self.disposition = "unknown_quarantined"
            if not any(pin is self for pin in _QUARANTINED_PINS):
                _QUARANTINED_PINS.append(self)
            raise CustodyError(f"unknown_quarantined: {error}") from error


def _release(pins):
    """Intenta todos; conserva el fallo primario y explicita limpieza incierta."""
    primary = sys.exception()
    errors = []
    for pin in pins:
        try:
            pin.close()
        except CustodyError as error:
            errors.append(error)
    if errors:
        if primary is not None:
            for error in errors:
                primary.add_note(str(error))
        else:
            raise CustodyError("unknown_quarantined: limpieza incompleta") from errors[
                0
            ]


def _parents(path):
    return list(reversed(path.parents))


class CustodyStore:
    """Namespace nuevo propio bajo private_root; nunca abre cápsulas ajenas.

    Los IDs no resuelven en otra instancia. No admite roots de autoridad,
    referencias legacy, importación de cápsulas ni packs. El caller conserva
    las fuentes y debe validarlas de nuevo para FINAL en su capa semántica.
    """

    def __init__(self, private_root: Path):
        _native()
        self._lock = threading.RLock()
        self._closed = False
        self._lost = False
        self._capsules = {}
        self._pins = []
        self.store_id = uuid.uuid4().hex
        root = _path(private_root)
        self._directory = root / ("custody-" + self.store_id)
        try:
            for directory in [*_parents(root), root]:
                self._pins.append(_Pin(directory, directory=True))
            self._directory.mkdir()
            self._pins.append(_Pin(self._directory, directory=True))
        except BaseException:
            _release(reversed(self._pins))
            raise

    def _live(self, deadline):
        _check_deadline(deadline)
        if self._closed or self._lost:
            raise CustodyError("Store cerrado o custodia perdida")
        try:
            for pin in self._pins:
                pin.verify()
        except CustodyError:
            self._lost = True
            raise
        _check_deadline(deadline)

    def capture(self, entries: list[SourceEntry], *, deadline: float) -> CapsuleRef:
        """Verifica sellos del caller; devuelve sólo cápsula revalidada y pinned."""
        with self._lock:
            self._live(deadline)
            if (
                type(entries) not in (list, tuple)
                or not 1 <= len(entries) <= MAX_ENTRIES
            ):
                raise CustodyError("Número de entradas fuera del límite")
            entries = tuple(entries)
            index = {}
            offset = _HEADER.size + len(entries) * _ENTRY.size
            for entry in entries:
                if not isinstance(entry, SourceEntry):
                    raise CustodyError("Entrada de fuente inválida")
                _name(entry.name)
                _integer(entry.length, MAX_CAPSULE)
                if (
                    not isinstance(entry.seal, str)
                    or not _SEAL.fullmatch(entry.seal)
                    or entry.name in index
                ):
                    raise CustodyError("Sello inválido o entrada duplicada")
                index[entry.name] = _IndexEntry(
                    entry.name, offset, entry.length, entry.seal
                )
                offset += entry.length
                _integer(offset, MAX_CAPSULE)
                _check_deadline(deadline)
            capsule_id = uuid.uuid4().hex
            path = self._directory / (capsule_id + ".cap")
            source_pins = []
            parent_pins = []
            pin = None
            created = False
            try:
                # Pin TODOS los originales antes de copiar: rechaza writers previos.
                for entry in entries:
                    source_path = _path(entry.path)
                    for parent in _parents(source_path):
                        parent_pins.append(_Pin(parent, directory=True))
                        _check_deadline(deadline)
                    source_pin = _Pin(source_path)
                    source_pins.append(source_pin)
                    if source_pin.identity[3] != entry.length:
                        raise CustodyError("Longitud original distinta del sello")
                    _check_deadline(deadline)
                for entry, source_pin in zip(entries, source_pins, strict=True):
                    original_digest = hashlib.sha256()
                    for position in range(0, entry.length, _CHUNK):
                        original_digest.update(
                            source_pin.read(
                                position, min(_CHUNK, entry.length - position), deadline
                            )
                        )
                    if original_digest.hexdigest() != entry.seal:
                        raise CustodyError("Fuente no verificada; no se graba cápsula")
                    _check_deadline(deadline)
                expected = hashlib.sha256()
                with path.open("xb") as output:
                    created = True
                    header = _HEADER.pack(_MAGIC, len(index)) + b"".join(
                        _ENTRY.pack(
                            e.name.encode("ascii"),
                            e.offset,
                            e.length,
                            bytes.fromhex(e.seal),
                        )
                        for e in index.values()
                    )
                    output.write(header)
                    expected.update(header)
                    for entry, source_pin in zip(entries, source_pins, strict=True):
                        digest = hashlib.sha256()
                        for position in range(0, entry.length, _CHUNK):
                            data = source_pin.read(
                                position, min(_CHUNK, entry.length - position), deadline
                            )
                            digest.update(data)
                            output.write(data)
                            expected.update(data)
                            _check_deadline(deadline)
                        if digest.hexdigest() != entry.seal:
                            raise CustodyError(
                                "Bytes originales no coinciden con sello confiado"
                            )
                    output.flush()
                    os.fsync(output.fileno())
                _check_deadline(deadline)
                # No aceptación en la ventana writer->pin: después se relee todo.
                pin = _Pin(path)
                verified = self._verify_capsule(
                    pin, index, expected.hexdigest(), deadline
                )
                for resource in [*source_pins, *parent_pins]:
                    resource.close()
                    _check_deadline(deadline)
                source_pins.clear()
                parent_pins.clear()
                self._live(deadline)
                pin.verify()
                _check_deadline(deadline)
                self._capsules[capsule_id] = _Capsule(
                    pin, verified, expected.hexdigest()
                )
                pin = None
                return CapsuleRef(self.store_id, capsule_id)
            except OSError as error:
                raise CustodyError("Fallo de IO durante captura") from error
            finally:
                _release(
                    [*([pin] if pin is not None else []), *source_pins, *parent_pins]
                )
                if created and capsule_id not in self._capsules:
                    # Namespace propio pinned; no recorrer ni borrar paths ajenos.
                    try:
                        path.unlink()
                    except OSError:
                        pass  # Cuarentena privada no anunciada; nunca se reimporta.

    def _verify_capsule(self, pin, expected_index, expected_seal, deadline):
        """Reconstruye índice desde bytes pinned y verifica TODO el contenedor."""
        _check_deadline(deadline)
        total = pin.identity[3]
        _integer(total, MAX_CAPSULE)
        magic, count = _HEADER.unpack(pin.read(0, _HEADER.size, deadline))
        if magic != _MAGIC or not 1 <= count <= MAX_ENTRIES:
            raise CustodyError("Magic/count del contenedor inválidos")
        encoded_index = pin.read(_HEADER.size, count * _ENTRY.size, deadline)
        cursor = _HEADER.size + count * _ENTRY.size
        decoded = {}
        for number in range(count):
            encoded_name, offset, length, seal = _ENTRY.unpack_from(
                encoded_index, number * _ENTRY.size
            )
            try:
                name = encoded_name.rstrip(b"\0").decode("ascii")
                _name(name)
            except (UnicodeError, CustodyError) as error:
                raise CustodyError("Nombre no canónico en índice") from error
            if encoded_name != name.encode("ascii").ljust(64, b"\0") or name in decoded:
                raise CustodyError("Padding inválido o nombre duplicado")
            _integer(offset, MAX_CAPSULE)
            _integer(length, MAX_CAPSULE)
            if offset != cursor:
                raise CustodyError("Offsets no contiguos en índice cerrado")
            cursor += length
            _integer(cursor, MAX_CAPSULE)
            decoded[name] = _IndexEntry(name, offset, length, seal.hex())
            _check_deadline(deadline)
        if cursor != total or decoded != expected_index:
            raise CustodyError("Índice/longitud no coincide con fuentes verificadas")
        digest = hashlib.sha256()
        for offset in range(0, total, _CHUNK):
            digest.update(pin.read(offset, min(_CHUNK, total - offset), deadline))
        if digest.hexdigest() != expected_seal:
            raise CustodyError("Contenedor protegido no coincide con bytes originales")
        pin.verify()
        _check_deadline(deadline)
        return decoded

    def read(
        self, ref: CapsuleRef, name: str, *, offset: int, length: int, deadline: float
    ) -> bytes:
        """Lee sólo bytes pedidos del índice cerrado; no acepta rutas ni autoridad."""
        with self._lock:
            self._live(deadline)
            if (
                not isinstance(ref, CapsuleRef)
                or type(ref.store_id) is not str
                or type(ref.capsule_id) is not str
                or not _ID.fullmatch(ref.store_id)
                or not _ID.fullmatch(ref.capsule_id)
                or ref.store_id != self.store_id
                or ref.capsule_id not in self._capsules
            ):
                raise CustodyError("Referencia ajena o desconocida")
            _name(name)
            _integer(offset, MAX_CAPSULE)
            _integer(length, MAX_READ)
            capsule = self._capsules[ref.capsule_id]
            entry = capsule.entries.get(name)
            if entry is None or offset + length > entry.length:
                raise CustodyError("Lectura fuera del índice cerrado")
            try:
                result = capsule.pin.read(entry.offset + offset, length, deadline)
            except CustodyError:
                self._lost = True
                raise
            _check_deadline(deadline)
            return result

    def close(self):
        with self._lock:
            self._closed = True
            _release(
                [
                    *(capsule.pin for capsule in self._capsules.values()),
                    *reversed(self._pins),
                ]
            )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
