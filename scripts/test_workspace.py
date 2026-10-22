"""Temporales propios de pytest dentro de la caché del proyecto."""

from __future__ import annotations

import os
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = ".studio-test-owner"
_OWNED = {}


@dataclass(frozen=True)
class Workspace:
    path: Path
    base: Path
    token: str

    def cleanup(self):
        """Revalida custodia por borrado; check/unlink conserva una ventana TOCTOU."""
        if (
            _OWNED.get(self.path) != self.token
            or self.path.parent != self.base
            or len(self.path.name) != 32
            or any(c not in "0123456789abcdef" for c in self.path.name)
        ):
            raise ValueError("Workspace ajeno; no eliminar")
        checked_path(self.path)
        root_info = self.path.lstat()
        marker = self.path / MARKER
        checked_path(marker)
        if (
            not marker.is_file()
            or marker.stat().st_nlink != 1
            or marker.read_text(encoding="ascii") != self.token
        ):
            raise ValueError("Marcador alterado; no eliminar")
        entries = []
        directories = {self.path: root_info}

        def identity(info):
            return (
                info.st_dev,
                info.st_ino,
                info.st_mode,
                # Enumeration can change this observed bit on a stable directory.
                getattr(info, "st_file_attributes", 0)
                & (~0x10000000 if stat.S_ISDIR(info.st_mode) else -1),
                getattr(info, "st_reparse_tag", 0),
            )

        def check_parents(path):
            checked_path(path.parent)
            for parent in (path.parent, *path.parent.parents):
                if parent in directories and identity(parent.lstat()) != identity(
                    directories[parent]
                ):
                    raise ValueError("Directorio cambiado durante limpieza")

        def check_owner():
            if (
                _OWNED.get(self.path) != self.token
                or self.path.parent != self.base
                or len(self.path.name) != 32
                or any(c not in "0123456789abcdef" for c in self.path.name)
            ):
                raise ValueError("Workspace ajeno; no eliminar")
            checked_path(marker)
            check_parents(marker)
            info = marker.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or marker.read_text(encoding="ascii") != self.token
            ):
                raise ValueError("Marcador alterado durante limpieza")

        def collect(directory):
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    path = Path(entry.path)
                    check_parents(path)
                    info = path.lstat()
                    reparse = getattr(info, "st_file_attributes", 0) & 0x400
                    link = stat.S_ISLNK(info.st_mode) or reparse
                    if reparse and getattr(info, "st_reparse_tag", 0) not in (
                        0xA0000003,  # junction
                        0xA000000C,  # symlink
                    ):
                        raise ValueError("Reparse desconocido; no eliminar")
                    directory_entry = stat.S_ISDIR(info.st_mode) or (
                        link and bool(getattr(info, "st_file_attributes", 0) & 0x10)
                    )
                    if directory_entry and not link:
                        directories[path] = info
                        collect(path)
                    elif not link and not stat.S_ISREG(info.st_mode):
                        raise ValueError("Entrada especial; no eliminar")
                    entries.append((path, directory_entry, info))

        collect(self.path)
        for path, directory, info in entries:
            if path == marker:
                continue
            check_parents(path)
            if identity(path.lstat()) != identity(info):
                raise ValueError("Entrada cambiada durante limpieza")
            check_owner()
            if directory:
                path.rmdir()
            else:
                path.unlink()
        checked_path(marker)
        check_parents(marker)
        if (
            marker.stat().st_nlink != 1
            or marker.read_text(encoding="ascii") != self.token
        ):
            raise ValueError("Marcador alterado durante limpieza")
        check_owner()
        marker.unlink()
        try:
            # El marcador acaba de retirarse: sólo identidad/registro propios.
            checked_path(self.path)
            check_parents(marker)
            if _OWNED.get(self.path) != self.token:
                raise ValueError("Workspace ajeno; no eliminar")
            self.path.rmdir()
        except OSError:
            checked_path(self.path)
            if _OWNED.get(self.path) == self.token and identity(
                self.path.lstat()
            ) == identity(root_info):
                # Exclusivo: nunca sobrescribir/re-mintar un marcador ajeno.
                with marker.open("x", encoding="ascii") as stream:
                    stream.write(self.token)
            raise
        del _OWNED[self.path]


def workspace_base(namespace=None, *, root=None):
    if root is not None and Path(os.path.abspath(root)) != ROOT:
        raise ValueError("El caller no redefine la raíz real del proyecto")
    raw = Path(
        namespace
        if namespace is not None
        else os.environ.get("STUDIO_TEST_ROOT", ".cache/pytest-tmp")
    )
    if ".." in raw.parts or (raw.drive and not raw.is_absolute()):
        raise ValueError("Namespace con escape léxico")
    base = Path(os.path.abspath(raw if raw.is_absolute() else ROOT / raw))
    checked_path(base)
    return base


def checked_path(path):
    cache = ROOT / ".cache"
    if not path.is_relative_to(cache) or path == cache:
        raise ValueError("Namespace fuera de la caché real del proyecto")
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Enlace/reparse prohibido en namespace")
    if not path.resolve().is_relative_to(cache.resolve()):
        raise ValueError("Namespace resuelto fuera de caché")
    return path


def create_workspace(namespace=None, *, root=None):
    base = workspace_base(namespace, root=root)
    base.mkdir(parents=True, exist_ok=True)
    path = checked_path(base / uuid.uuid4().hex)
    path.mkdir()
    token = uuid.uuid4().hex
    (path / MARKER).write_text(token, encoding="ascii")
    _OWNED[path] = token
    return Workspace(path, base, token)


@contextmanager
def workspace(namespace=None, *, root=None):
    owned = create_workspace(namespace, root=root)
    try:
        yield owned.path
    finally:
        owned.cleanup()
