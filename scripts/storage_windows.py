"""Custodia nativa Windows para la provisión offline de ADR-0069.

Las capacidades propias proceden exclusivamente de FILE_CREATE. El cierre
libera handles y conserva los objetos: no hay adopción ni recuperación por
nombre. No monta discos ni ejecuta herramientas/engines.
"""

import ctypes
import hashlib
import os
import re
import subprocess
import time
from ctypes import wintypes as w
from dataclasses import dataclass
from pathlib import PureWindowsPath


class CustodyError(RuntimeError):
    """La autoridad/identidad no puede acreditarse; conservar y abortar."""


@dataclass(frozen=True)
class HandleMetadata:
    volume_serial: int
    file_id: bytes
    final_path: str
    size: int
    allocated: int
    links: int
    directory: bool
    attributes: int

    @property
    def identity(self):
        return self.volume_serial, self.file_id


class _FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_ulonglong), ("identifier", ctypes.c_ubyte * 16)]


class _Standard(ctypes.Structure):
    _fields_ = [("allocated", ctypes.c_longlong), ("size", ctypes.c_longlong),
                ("links", w.DWORD), ("pending", ctypes.c_ubyte), ("directory", ctypes.c_ubyte)]


class _Tag(ctypes.Structure):
    _fields_ = [("attributes", w.DWORD), ("tag", w.DWORD)]


class _Unicode(ctypes.Structure):
    _fields_ = [("length", w.USHORT), ("maximum", w.USHORT), ("buffer", w.LPWSTR)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [("length", w.ULONG), ("root", w.HANDLE),
                ("name", ctypes.POINTER(_Unicode)), ("attributes", w.ULONG),
                ("security", ctypes.c_void_p), ("quality", ctypes.c_void_p)]


class _IoStatus(ctypes.Structure):
    _fields_ = [("status", ctypes.c_void_p), ("information", ctypes.c_size_t)]


class _Rename(ctypes.Structure):
    _fields_ = [("replace", ctypes.c_ubyte), ("root", w.HANDLE), ("length", w.DWORD), ("name", w.WCHAR * 1)]


class _Startup(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR), ("title", w.LPWSTR),
                ("x", w.DWORD), ("y", w.DWORD), ("width", w.DWORD), ("height", w.DWORD),
                ("x_chars", w.DWORD), ("y_chars", w.DWORD), ("fill", w.DWORD), ("flags", w.DWORD),
                ("show", w.WORD), ("reserved_bytes", w.WORD), ("reserved_data", ctypes.c_void_p),
                ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]


class _StartupEx(ctypes.Structure):
    _fields_ = [("startup", _Startup), ("attributes", ctypes.c_void_p)]


class _ProcessInfo(ctypes.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]


class _JobBasicLimit(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong), ("flags", w.DWORD),
                ("min_working", ctypes.c_size_t), ("max_working", ctypes.c_size_t), ("active_limit", w.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class _JobLimits(ctypes.Structure):
    _fields_ = [("basic", _JobBasicLimit), ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [("user_time", ctypes.c_longlong), ("kernel_time", ctypes.c_longlong),
                ("period_user", ctypes.c_longlong), ("period_kernel", ctypes.c_longlong),
                ("faults", w.DWORD), ("total", w.DWORD), ("active", w.DWORD), ("terminated", w.DWORD)]


class _Native:
    def __init__(self):
        if os.name != "nt":
            raise CustodyError("se requiere Windows nativo")
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.nt = ctypes.WinDLL("ntdll", use_last_error=True)
        self._new_handles = set()
        declarations = {
            "CreateFileW": ([w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "GetFileInformationByHandleEx": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "GetFinalPathNameByHandleW": ([w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD], w.DWORD),
            "GetFileType": ([w.HANDLE], w.DWORD),
            "SetFileInformationByHandle": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "DeviceIoControl": ([w.HANDLE, w.DWORD, ctypes.c_void_p, w.DWORD, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL),
            "SetFilePointerEx": ([w.HANDLE, ctypes.c_longlong, ctypes.c_void_p, w.DWORD], w.BOOL),
            "SetEndOfFile": ([w.HANDLE], w.BOOL),
            "ReadFile": ([w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL),
            "WriteFile": ([w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL),
            "FlushFileBuffers": ([w.HANDLE], w.BOOL),
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            "InitializeProcThreadAttributeList": ([ctypes.c_void_p, w.DWORD, w.DWORD, ctypes.POINTER(ctypes.c_size_t)], w.BOOL),
            "UpdateProcThreadAttribute": ([ctypes.c_void_p, w.DWORD, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p], w.BOOL),
            "DeleteProcThreadAttributeList": ([ctypes.c_void_p], None),
            "CreateProcessW": ([w.LPCWSTR, w.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, w.BOOL, w.DWORD, ctypes.c_void_p, w.LPCWSTR, ctypes.POINTER(_Startup), ctypes.POINTER(_ProcessInfo)], w.BOOL),
            "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
            "GetExitCodeProcess": ([w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
        }
        for name, (args, result) in declarations.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result
        self.nt.NtCreateFile.argtypes = [ctypes.POINTER(w.HANDLE), w.ULONG, ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatus), ctypes.c_void_p, w.ULONG, w.ULONG, w.ULONG, w.ULONG, ctypes.c_void_p, w.ULONG]
        self.nt.NtCreateFile.restype = ctypes.c_long
        self.nt.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
        self.nt.RtlNtStatusToDosError.restype = w.ULONG

    @staticmethod
    def checked(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def inspect(self, handle):
        identifier, standard, tag = _FileId(), _Standard(), _Tag()
        for kind, value in ((18, identifier), (1, standard), (9, tag)):
            self.checked(self.kernel.GetFileInformationByHandleEx(handle, kind, ctypes.byref(value), ctypes.sizeof(value)))
        name = ctypes.create_unicode_buffer(32768)
        count = self.checked(self.kernel.GetFinalPathNameByHandleW(handle, name, len(name), 0))
        if count >= len(name) or self.kernel.GetFileType(handle) != 1 or tag.attributes & 0x400 or standard.pending or standard.links != 1:
            raise CustodyError("objeto no regular, alias/reparse, hardlink o pendiente de borrar")
        return HandleMetadata(identifier.volume, bytes(identifier.identifier), name.value, standard.size, standard.allocated, standard.links, bool(standard.directory), tag.attributes)

    def open_volume_root(self, anchor):
        handle = self.kernel.CreateFileW(anchor, 0x100080, 3, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def child(self, parent, name, directory, create):
        buffer = ctypes.create_unicode_buffer(name)
        byte_length = len(name.encode("utf-16-le"))
        unicode = _Unicode(byte_length, byte_length + 2, ctypes.cast(buffer, w.LPWSTR))
        attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent, ctypes.pointer(unicode), 0x40, None, None)
        handle, status = w.HANDLE(), _IoStatus()
        access = 0x100080 | (0x20 if directory else 3) | (0x10000 if create else 0)
        options = 0x200020 | (1 if directory else 0x40)
        result = self.nt.NtCreateFile(ctypes.byref(handle), access, ctypes.byref(attributes), ctypes.byref(status), None, 0x80, 3, 2 if create else 1, options, None, 0)
        if result < 0:
            raise ctypes.WinError(self.nt.RtlNtStatusToDosError(result))
        if status.information != (2 if create else 1):
            self.kernel.CloseHandle(handle)
            raise CustodyError("NtCreateFile no acreditó creación/apertura esperada")
        if create:
            self._new_handles.add(handle.value)
        return handle.value

    def producer(self, argv, cwd):
        job = self.checked(self.kernel.CreateJobObjectW(None, None))
        attribute_list = None
        initialized = False
        try:
            limits = _JobLimits()
            limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE; sin BREAKAWAY_OK.
            self.checked(self.kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            amount = ctypes.c_size_t()
            result = self.kernel.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(amount))
            if result or ctypes.get_last_error() != 122 or not amount.value:
                raise CustodyError("tamaño de lista de atributos no acreditado")
            attribute_list = ctypes.create_string_buffer(amount.value)
            self.checked(self.kernel.InitializeProcThreadAttributeList(attribute_list, 1, 0, ctypes.byref(amount)))
            initialized = True
            jobs = (w.HANDLE * 1)(job)
            self.checked(self.kernel.UpdateProcThreadAttribute(attribute_list, 0, 0x2000D, jobs, ctypes.sizeof(jobs), None, None))
            startup, process = _StartupEx(), _ProcessInfo()
            startup.startup.cb = ctypes.sizeof(startup)
            startup.attributes = ctypes.addressof(attribute_list)
            command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
            self.checked(self.kernel.CreateProcessW(argv[0], command, None, None, False, 0x08080000, None, cwd, ctypes.cast(ctypes.byref(startup), ctypes.POINTER(_Startup)), ctypes.byref(process)))
            self.checked(self.kernel.CloseHandle(process.thread))
            return _Producer(self, job, process.process, argv)
        except BaseException:
            self.kernel.CloseHandle(job)
            raise
        finally:
            if initialized:
                self.kernel.DeleteProcThreadAttributeList(attribute_list)


def _component(name):
    if not isinstance(name, str) or not name or name in {".", ".."} or any(character in name for character in '\\/:\x00') or name.endswith((".", " ")) or len(name.encode("utf-16-le")) > 510:
        raise ValueError("nombre hijo simple requerido")
    return name


class _Guard:
    def __init__(self, custody, handle, path, directory):
        if isinstance(self, (OwnedDirectory, OwnedFile)):
            if handle not in custody._native._new_handles:
                raise CustodyError("autoridad de creación kernel nueva requerida")
            custody._native._new_handles.remove(handle)
        self._custody, self._handle, self._path = custody, handle, path
        self._initial = custody._native.inspect(handle)
        if isinstance(self, OwnedFile) and self._initial.size != 0:
            raise CustodyError("archivo nuevo no vacío; conservar bytes inesperados")
        if self._initial.directory != directory or self._initial.final_path.casefold() != path.casefold():
            raise CustodyError("ruta/tipo por handle difiere del padre acreditado")

    def inspect(self):
        if self._handle is None or self._custody._closed:
            raise CustodyError("capacidad cerrada")
        actual = self._custody._native.inspect(self._handle)
        if actual.identity != self._initial.identity or actual.directory != self._initial.directory or actual.final_path.casefold() != self._path.casefold():
            raise CustodyError("identidad/ruta de capacidad alterada")
        return actual


class OwnedDirectory(_Guard):
    def discard(self):
        self.inspect()
        disposition = ctypes.c_ubyte(1)
        self._custody._native.checked(self._custody._native.kernel.SetFileInformationByHandle(self._handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)))
        self._custody._close_guard(self)


class OwnedFile(_Guard):
    def discard(self, seal):
        if getattr(self, "_published", False):
            raise CustodyError("archivo publicado; conservar")
        if seal is not getattr(self, "_seal", None) or not isinstance(seal, _Seal):
            raise CustodyError("sello propio vivo requerido")
        self.seal(seal.sha256)
        disposition = ctypes.c_ubyte(1)
        native = self._custody._native
        native.checked(native.kernel.SetFileInformationByHandle(self._handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)))
        self._custody._close_guard(self)

    def promote_no_replace(self, name, seal):
        _component(name)
        if seal is not getattr(self, "_seal", None) or not isinstance(seal, _Seal):
            raise CustodyError("sello propio vivo requerido")
        self.seal(seal.sha256)
        parent = self._custody._scope
        parent.inspect()
        target = str(PureWindowsPath(parent._path) / name)
        encoded = target.encode("utf-16-le")
        buffer = ctypes.create_string_buffer(_Rename.name.offset + len(encoded) + 2)
        rename = _Rename.from_buffer(buffer)
        rename.replace, rename.root, rename.length = 0, None, len(encoded)
        ctypes.memmove(ctypes.addressof(buffer) + _Rename.name.offset, encoded, len(encoded))
        native = self._custody._native
        native.checked(native.kernel.SetFileInformationByHandle(self._handle, 3, buffer, len(buffer)))
        self._path = target
        self._published = True
        self.inspect()

    def seal(self, expected_sha256):
        if any(not producer._reaped or producer._result != 0 for producer in getattr(self, "_producers", ())):
            raise CustodyError("productor no reapado con éxito; conservar")
        if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise ValueError("SHA-256 esperado requerido")
        before = self.inspect()
        digest = hashlib.sha256()
        offset = 0
        while offset < before.size:
            payload = self.read(offset=offset, size=min(1024 * 1024, before.size - offset))
            if not payload:
                raise CustodyError("lectura incompleta al sellar")
            digest.update(payload)
            offset += len(payload)
        after = self.inspect()
        if after.identity != before.identity or after.size != before.size or digest.hexdigest() != expected_sha256:
            raise CustodyError("hash/tamaño propio inesperado; conservar")
        if getattr(self, "_seal", None) is None:
            self._seal = _Seal(before.identity, expected_sha256, before.size)
        return self._seal

    def write(self, payload, *, offset=0):
        self.inspect()
        if any(not producer._reaped or producer._result != 0 for producer in getattr(self, "_producers", ())):
            raise CustodyError("productor no reapado con éxito; conservar")
        if getattr(self, "_seal", None) is not None:
            raise CustodyError("archivo sellado; escritura rechazada")
        if not isinstance(payload, bytes) or not isinstance(offset, int) or offset < 0:
            raise ValueError("bytes y desplazamiento no negativo requeridos")
        native = self._custody._native
        native.checked(native.kernel.SetFilePointerEx(self._handle, offset, None, 0))
        written = w.DWORD()
        native.checked(native.kernel.WriteFile(self._handle, payload, len(payload), ctypes.byref(written), None))
        if written.value != len(payload):
            raise CustodyError("escritura incompleta")
        native.checked(native.kernel.FlushFileBuffers(self._handle))

    def read(self, *, offset=0, size=1024 * 1024):
        self.inspect()
        if not isinstance(size, int) or not 0 <= size <= 1024 * 1024 or not isinstance(offset, int) or offset < 0:
            raise ValueError("lectura limitada a 1 MiB y desplazamiento no negativo")
        native = self._custody._native
        native.checked(native.kernel.SetFilePointerEx(self._handle, offset, None, 0))
        buffer, amount = ctypes.create_string_buffer(size), w.DWORD()
        native.checked(native.kernel.ReadFile(self._handle, buffer, size, ctypes.byref(amount), None))
        return buffer.raw[:amount.value]


@dataclass(frozen=True)
class _Seal:
    identity: tuple[int, bytes]
    sha256: str
    size: int


class _Producer:
    """Árbol de procesos en un job propio; no acredita vida de un contenedor.

    El controlador anfitrión es confiable. El executor debe esperar su terminal
    real antes de permitir que el hijo controlador termine con éxito.
    """

    def __init__(self, native, job, process, argv):
        self._native, self._job, self._process, self._argv = native, job, process, argv
        self._reaped, self._result = False, None

    def wait(self, timeout=None):
        if self._reaped:
            return self._result
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            accounting = _Accounting()
            self._native.checked(self._native.kernel.QueryInformationJobObject(self._job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None))
            status = self._native.kernel.WaitForSingleObject(self._process, 0)
            if status not in {0, 258}:
                raise CustodyError("espera del productor no acreditada")
            if status == 0 and accounting.active == 0:
                result = w.DWORD()
                self._native.checked(self._native.kernel.GetExitCodeProcess(self._process, ctypes.byref(result)))
                self._result = result.value
                self._native.checked(self._native.kernel.CloseHandle(self._process))
                self._native.checked(self._native.kernel.CloseHandle(self._job))
                self._process, self._job, self._reaped = None, None, True
                return self._result
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(self._argv, timeout)
            time.sleep(0.01)


class WindowsCustody:
    """Retiene ancestros y autoridad sobre objetos creados en un ámbito fijo.

    El ámbito debe existir. Nunca crea padres, sigue enlaces ni abre archivos
    existentes como objetos propios. No libera un guardián para mutar por ruta.
    """

    def __init__(self, project_root, scope_relative):
        self._native = _Native()
        self._guards = []
        self._producers = []
        self._closed = False
        root = PureWindowsPath(project_root)
        scope = PureWindowsPath(scope_relative)
        if not root.is_absolute() or root.drive.startswith("\\\\") or any(part in {".", ".."} for part in root.parts + scope.parts) or scope.is_absolute():
            raise ValueError("raíz absoluta local y ámbito relativo requeridos")
        scope_parts = scope.parts
        if not (scope_parts == ("data", "_storage") or len(scope_parts) >= 3 and scope_parts[:2] == (".cache", "dev-cycle")):
            raise ValueError("ámbito de almacenamiento fuera del proyecto")
        for part in root.parts[1:] + scope_parts:
            _component(part)
        try:
            parent = self._register(self._native.open_volume_root(root.anchor), "\\\\?\\" + root.anchor, True)
            for part in root.parts[1:] + scope_parts:
                parent.inspect()
                path = str(PureWindowsPath(parent._path) / part)
                parent = self._register(self._native.child(parent._handle, part, True, False), path, True)
            self._scope = parent
        except BaseException:
            self.close()
            raise

    def _register(self, handle, path, directory, own=False):
        try:
            kind = (OwnedDirectory if directory else OwnedFile) if own else _Guard
            guard = kind(self, handle, path, directory)
        except BaseException:
            self._native.kernel.CloseHandle(handle)
            raise
        self._guards.append(guard)
        return guard

    def create_directory(self, name):
        _component(name)
        self._scope.inspect()
        path = str(PureWindowsPath(self._scope._path) / name)
        return self._register(self._native.child(self._scope._handle, name, True, True), path, True, own=True)

    def create_sparse_file(self, name, size_bytes=64 * 1024**3, *, parent=None):
        _component(name)
        if type(size_bytes) is not int or not 0 <= size_bytes <= 64 * 1024**3:
            raise ValueError("tamaño sparse inválido")
        if parent is None:
            parent = self._scope
        elif not isinstance(parent, OwnedDirectory) or parent._custody is not self:
            raise CustodyError("padre propio vivo requerido")
        parent.inspect()
        path = str(PureWindowsPath(parent._path) / name)
        file = self._register(self._native.child(parent._handle, name, False, True), path, False, own=True)
        returned = w.DWORD()
        self._native.checked(self._native.kernel.DeviceIoControl(file._handle, 0x900C4, None, 0, None, 0, ctypes.byref(returned), None))
        self._native.checked(self._native.kernel.SetFilePointerEx(file._handle, size_bytes, None, 0))
        self._native.checked(self._native.kernel.SetEndOfFile(file._handle))
        self._native.checked(self._native.kernel.FlushFileBuffers(file._handle))
        actual = file.inspect()
        if actual.size != size_bytes or not actual.attributes & 0x200:
            raise CustodyError("filesystem no acreditó sparse/tamaño solicitado")
        return file

    def start_producer(self, argv, files):
        if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(arg, str) for arg in argv):
            raise ValueError("argv explícito requerido")
        if not isinstance(files, (list, tuple)) or not files or len({id(file) for file in files}) != len(files):
            raise ValueError("lista única de capacidades propias requerida")
        for file in files:
            if not isinstance(file, OwnedFile) or file._custody is not self or getattr(file, "_seal", None) is not None:
                raise CustodyError("archivo propio no sellado requerido")
            file.inspect()
            if any(not producer._reaped or producer._result != 0 for producer in getattr(file, "_producers", ())):
                raise CustodyError("productor previo no reapado con éxito; conservar")
        producer = self._native.producer(argv, self._scope._path)
        self._producers.append(producer)
        for file in files:
            if not hasattr(file, "_producers"):
                file._producers = []
            file._producers.append(producer)
        return producer

    def _close_guard(self, guard):
        if guard._handle is not None:
            self._native.checked(self._native.kernel.CloseHandle(guard._handle))
            guard._handle = None

    def close(self):
        if any(not producer._reaped for producer in self._producers):
            raise CustodyError("productor propio pendiente de reap; guardianes retenidos")
        for guard in reversed(self._guards):
            self._close_guard(guard)
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
