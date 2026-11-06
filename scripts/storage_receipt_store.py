"""Lease de sólo lectura de un recibo existente, sin commit ni ciclo de vida.

La exclusión usa sharing nativo Windows y retiene todos los ancestros. No
crea, adopta, guarda, avanza fases ni concede autoridad sobre el disco.
"""

from __future__ import annotations

import ctypes
import re
from builtins import BaseExceptionGroup
from ctypes import wintypes as w
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from threading import RLock
from typing import Self

from studio_storage_guard.receipt import StorageReceipt

from scripts.storage_operator import _QueryNative
from scripts.storage_windows import CustodyError, HandleMetadata


@dataclass(frozen=True)
class ReceiptSnapshot:
    """Bytes exactos y parseo del mismo handle; el caller conserva los bytes.

    StorageReceipt contiene diccionarios mutables: cada lectura devuelve un
    parseo nuevo. La autoridad de comparación reside en payload e identity.
    """

    payload: bytes
    receipt: StorageReceipt
    identity: tuple[int, bytes]


@dataclass(frozen=True)
class ReceiptCloseUncertainty:
    """Diagnóstico sin autoridad ni número de handle reutilizable.

    CloseHandle pudo ejecutarse antes del fallo o interrupción. Si el objeto
    sigue abierto, sólo terminar el proceso propietario asegura liberación;
    este registro nunca permite reintentar el cierre ni recuperar por ruta.
    """

    path: str
    identity: tuple[int, bytes] | None
    directory: bool
    cause: BaseException


class _ReceiptNative(_QueryNative):
    def __init__(self):
        super().__init__()
        self.kernel.SetFilePointerEx.argtypes = [
            w.HANDLE,
            ctypes.c_longlong,
            ctypes.c_void_p,
            w.DWORD,
        ]
        self.kernel.SetFilePointerEx.restype = w.BOOL
        self.kernel.ReadFile.argtypes = [
            w.HANDLE,
            ctypes.c_void_p,
            w.DWORD,
            ctypes.POINTER(w.DWORD),
            ctypes.c_void_p,
        ]
        self.kernel.ReadFile.restype = w.BOOL

    def open(self, path, *, directory):
        # READ_DATA para archivo, EXECUTE/TRAVERSE para directorios: sharing
        # efectivo, no sólo READ_ATTRIBUTES. Sólo FILE_SHARE_READ; OPEN_EXISTING.
        access = 0x100080 | (0x20 if directory else 1)
        handle = self.kernel.CreateFileW(path, access, 1, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def read(self, handle, size):
        self.checked(self.kernel.SetFilePointerEx(handle, 0, None, 0))
        buffer, amount = ctypes.create_string_buffer(size), w.DWORD()
        self.checked(
            self.kernel.ReadFile(handle, buffer, size, ctypes.byref(amount), None)
        )
        if amount.value != size:
            raise CustodyError("lectura incompleta del recibo")
        return buffer.raw[: amount.value]


def _local_path(value):
    raw = str(value)
    path = PureWindowsPath(raw)
    if (
        not path.is_absolute()
        or path.drive.startswith("\\\\")
        or re.search(r"[\\/]{2}", raw)
        or re.search(r"(?:^|[\\/])(?:\.|\.\.)(?:[\\/]|$)", raw)
        or any(
            part.endswith((".", " ")) or any(c in part for c in ":\x00")
            for part in path.parts[1:]
        )
    ):
        raise ValueError("ruta absoluta local canónica requerida")
    return path


class ReceiptLease:
    """Retiene identidad y exclusión nativa hasta close, sin escrituras."""

    def __init__(self):
        raise TypeError("usar ReceiptLease.open_existing(project, path)")

    @classmethod
    def open_existing(cls, project: str | Path, path: str | Path) -> Self:
        root, target = _local_path(project), _local_path(path)
        if not target.is_relative_to(root) or target == root:
            raise ValueError("recibo debe estar dentro del proyecto")
        lease = object.__new__(cls)
        lease._native, lease._handles, lease._closed = _ReceiptNative(), [], False
        lease._lock = RLock()
        lease._uncertain = False
        lease._close_error = None
        lease._close_uncertainties = []
        lease._root = root
        try:
            current = PureWindowsPath("\\\\?\\" + target.anchor)
            components = (None,) + target.parts[1:]
            for index, component in enumerate(components):
                if component is not None:
                    current /= component
                directory = index != len(components) - 1
                handle = lease._native.open(str(current), directory=directory)
                lease._handles.append((handle, str(current), None, directory))
                metadata = lease._native.inspect(handle)
                if (
                    metadata.directory != directory
                    or metadata.final_path.casefold() != str(current).casefold()
                ):
                    raise CustodyError("ruta/tipo por handle no coincide")
                lease._handles[-1] = handle, str(current), metadata.identity, directory
            lease.revalidate()
            return lease
        except BaseException as primary:
            lease._cleanup_after(primary)
            raise

    def revalidate(self) -> HandleMetadata:
        with self._lock:
            if (
                self._closed
                or self._uncertain
                or not self._handles
                or any(item[2] is None for item in self._handles)
            ):
                raise CustodyError("lease cerrada o incierta")
            for handle, path, identity, directory in self._handles:
                metadata = self._native.inspect(handle)
                if (
                    metadata.identity != identity
                    or metadata.directory != directory
                    or metadata.final_path.casefold() != path.casefold()
                ):
                    raise CustodyError("identidad/ruta del recibo alterada")
            return metadata

    def read_snapshot(self) -> ReceiptSnapshot:
        # Incluye ambas consultas y SEEK+READ sobre el puntero compartido.
        # Nunca retiene este lock durante el cuerpo del context manager.
        with self._lock:
            before = self.revalidate()
            if not 0 < before.size <= 1024 * 1024:
                raise CustodyError("tamaño de recibo fuera del límite de 1 MiB")
            payload = self._native.read(self._handles[-1][0], before.size)
            after = self.revalidate()
            if before != after:
                raise CustodyError("recibo cambió durante lectura")
            receipt = StorageReceipt.from_bytes(payload)
            if (
                receipt.disk_path
                != (self._root / "data/_storage/studio-data.vhdx").as_posix()
            ):
                raise CustodyError("recibo no corresponde al proyecto")
            return ReceiptSnapshot(payload, receipt, before.identity)

    def assert_expected(self, expected: bytes) -> None:
        with self._lock:
            if not isinstance(expected, bytes):
                raise TypeError("snapshot esperado debe ser bytes")
            if self.read_snapshot().payload != expected:
                raise CustodyError("snapshot esperado obsoleto; conservar recibo")

    @property
    def close_uncertainties(self) -> tuple[ReceiptCloseUncertainty, ...]:
        with self._lock:
            return tuple(self._close_uncertainties)

    def close(self) -> None:
        with self._lock:
            if self._close_error is not None:
                raise self._close_error
            failures = []
            self._closed = True
            while self._handles:
                entry = self._handles[-1]
                try:
                    # Invalidar autoridad ANTES de CloseHandle: su valor puede
                    # reutilizarse aunque una interrupción o fallo impida saberlo.
                    self._handles.pop()
                    self._native.close(entry[0])
                except BaseException as error:  # noqa: BLE001 - conservar también interrupciones y cerrar el resto
                    error.add_note(
                        "CloseHandle uncertain: no reintentar; la finalización del proceso propietario puede ser necesaria"
                    )
                    self._uncertain = True
                    self._close_uncertainties.append(
                        ReceiptCloseUncertainty(entry[1], entry[2], entry[3], error)
                    )
                    failures.append(error)
            if failures:
                self._close_error = BaseExceptionGroup(
                    "receipt lease close uncertain", failures
                )
                raise self._close_error

    def _cleanup_after(self, primary):
        try:
            self.close()
        except BaseException as cleanup:  # noqa: BLE001 - no ocultar la causa primaria con cleanup
            raise BaseExceptionGroup(
                "fallo primario y cleanup uncertain", [primary, cleanup]
            ) from None

    def __enter__(self) -> Self:
        try:
            self.revalidate()
            return self
        except BaseException as primary:
            self._cleanup_after(primary)
            raise

    def __exit__(self, kind, error, traceback):
        if error is not None:
            self._cleanup_after(error)
        else:
            self.close()
