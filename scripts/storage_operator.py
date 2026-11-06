"""Binding de consulta Windows de un disco publicado; no ejecuta provisión.

Los handles retienen archivo y ancestros sin compartir DELETE. No conceden
escritura, creación, borrado ni adopción; el recibo sigue siendo published.
La identidad es FILE_ID_INFO, nunca el hash inicial que cambia en runtime.
"""

from __future__ import annotations

import ctypes
import os
import re
from ctypes import wintypes as w
from pathlib import Path, PureWindowsPath
from typing import Self

from studio_storage_guard.receipt import ReceiptError, StorageReceipt

from scripts.storage_windows import CustodyError, HandleMetadata


class _FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_ulonglong), ("identifier", ctypes.c_ubyte * 16)]


class _Standard(ctypes.Structure):
    _fields_ = [
        ("allocated", ctypes.c_longlong),
        ("size", ctypes.c_longlong),
        ("links", w.DWORD),
        ("pending", ctypes.c_ubyte),
        ("directory", ctypes.c_ubyte),
    ]


class _Tag(ctypes.Structure):
    _fields_ = [("attributes", w.DWORD), ("tag", w.DWORD)]


class _QueryNative:
    """Sólo abre/consulta/cierra handles existentes; sin syscalls de mutación."""

    def __init__(self):
        if os.name != "nt":
            raise CustodyError("se requiere Windows nativo")
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        declarations = {
            "CreateFileW": (
                [
                    w.LPCWSTR,
                    w.DWORD,
                    w.DWORD,
                    ctypes.c_void_p,
                    w.DWORD,
                    w.DWORD,
                    w.HANDLE,
                ],
                w.HANDLE,
            ),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "GetFileInformationByHandleEx": (
                [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD],
                w.BOOL,
            ),
            "GetFinalPathNameByHandleW": (
                [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD],
                w.DWORD,
            ),
            "GetFileType": ([w.HANDLE], w.DWORD),
        }
        for name, (arguments, result) in declarations.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result

    @staticmethod
    def checked(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def open(self, path):
        # READ_ATTRIBUTES|SYNCHRONIZE|EXECUTE/TRAVERSE; READ|WRITE sharing.
        # Windows ignora denyDELETE con sólo metadatos (probe nativo):
        # EXECUTE/TRAVERSE activa la comprobación de sharing sin READ_DATA.
        # Esta clase no ejecuta archivos ni concede operaciones de ejecución.
        # OPEN_EXISTING, BACKUP_SEMANTICS|OPEN_REPARSE_POINT; no seguir el final.
        handle = self.kernel.CreateFileW(path, 0x1000A0, 3, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def inspect(self, handle):
        identifier, standard, tag = _FileId(), _Standard(), _Tag()
        for kind, value in ((18, identifier), (1, standard), (9, tag)):
            self.checked(
                self.kernel.GetFileInformationByHandleEx(
                    handle, kind, ctypes.byref(value), ctypes.sizeof(value)
                )
            )
        name = ctypes.create_unicode_buffer(32768)
        count = self.checked(
            self.kernel.GetFinalPathNameByHandleW(handle, name, len(name), 0)
        )
        if (
            count >= len(name)
            or self.kernel.GetFileType(handle) != 1
            or tag.attributes & 0x400
            or standard.pending
            or standard.links != 1
        ):
            raise CustodyError(
                "objeto no regular, reparse, hardlink o pendiente de borrar"
            )
        return HandleMetadata(
            identifier.volume,
            bytes(identifier.identifier),
            name.value,
            standard.size,
            standard.allocated,
            standard.links,
            bool(standard.directory),
            tag.attributes,
        )

    def close(self, handle):
        self.checked(self.kernel.CloseHandle(handle))


class PublishedDiskBinding:
    """Lease de consulta de StorageReceipt, no una capacidad OwnedFile.

    El contrato de recibo no contiene identidad independiente del proyecto:
    se exige su ubicación canónica y se retienen todos sus ancestros reales.
    El caller aporta un StorageReceipt validado; no se adopta un recibo por ruta.
    """

    def __init__(self):
        raise TypeError("usar PublishedDiskBinding.open(project_root, receipt)")

    @classmethod
    def open(
        cls, project_root: str | Path, receipt: StorageReceipt
    ) -> PublishedDiskBinding:
        if not isinstance(receipt, StorageReceipt):
            raise ReceiptError("StorageReceipt requerido")
        snapshot = receipt.to_bytes()
        validated = StorageReceipt.from_bytes(snapshot)
        if validated.phase != "published":
            raise ReceiptError("recibo debe estar en published")
        root = PureWindowsPath(project_root)
        if (
            not root.is_absolute()
            or root.drive.startswith("\\\\")
            or ".." in root.parts
        ):
            raise ValueError("raíz absoluta local canónica requerida")
        for part in root.parts[1:]:
            if any(character in part for character in ":\x00") or part.endswith(
                (".", " ")
            ):
                raise ValueError("componente de raíz no canónico")
        final = root / "data" / "_storage" / "studio-data.vhdx"
        evidence = validated.history[-1]["evidence"]
        if (
            validated.disk_path != final.as_posix()
            or evidence["final_path"] != final.as_posix()
        ):
            raise ReceiptError("ruta publicada no coincide con proyecto")
        identity = evidence["file_id"]
        if not isinstance(identity, str) or not re.fullmatch(
            r"(?:0|[1-9][0-9]*):[0-9a-f]{32}", identity
        ):
            raise ReceiptError("identidad FILE_ID_INFO publicada inválida")
        volume, identifier = identity.split(":")
        expected = int(volume), bytes.fromhex(identifier)
        lease = object.__new__(cls)
        lease._native = _QueryNative()
        lease._handles = []
        lease._closed = False
        lease._receipt, lease._snapshot, lease._expected = receipt, snapshot, expected
        try:
            path = PureWindowsPath("\\\\?\\" + root.anchor)
            components = (
                (None,) + root.parts[1:] + ("data", "_storage", "studio-data.vhdx")
            )
            for index, component in enumerate(components):
                if component is not None:
                    path = path / component
                handle = lease._native.open(str(path))
                # Registrar inmediatamente: cualquier fallo de inspect cierra el handle.
                lease._handles.append((handle, str(path), None))
                metadata = lease._native.inspect(handle)
                if (
                    metadata.directory != (index != len(components) - 1)
                    or metadata.final_path.casefold() != str(path).casefold()
                ):
                    raise CustodyError("ruta/tipo de handle no coincide")
                lease._handles[-1] = handle, str(path), metadata.identity
            lease.revalidate()
            return lease
        except BaseException:
            lease.close()
            raise

    def revalidate(self) -> HandleMetadata:
        if self._closed:
            raise CustodyError("binding cerrado")
        if self._receipt.to_bytes() != self._snapshot:
            raise CustodyError("recibo alterado durante binding")
        for index, (handle, path, identity) in enumerate(self._handles):
            metadata = self._native.inspect(handle)
            if (
                metadata.identity != identity
                or metadata.final_path.casefold() != path.casefold()
                or metadata.directory != (index != len(self._handles) - 1)
            ):
                raise CustodyError("identidad/ruta de binding alterada")
        if metadata.identity != self._expected:
            raise CustodyError("identidad publicada no coincide")
        if self._receipt.to_bytes() != self._snapshot:
            raise CustodyError("recibo alterado durante binding")
        return metadata

    def close(self) -> None:
        while self._handles:
            handle, _, _ = self._handles[-1]
            self._native.close(handle)
            self._handles.pop()
        self._closed = True

    def __enter__(self) -> Self:
        try:
            self.revalidate()
        except BaseException as error:
            # Python no llama __exit__ si __enter__ falla: liberar esta lease.
            try:
                self.close()
            except BaseException as cleanup_error:
                raise error from cleanup_error
            raise
        return self

    def __exit__(self, *_):
        self.close()
