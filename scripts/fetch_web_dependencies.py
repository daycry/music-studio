"""Importación local de tgz oficiales opacos; nunca descarga ni extrae (ADR-0052).

El directorio completo se publica de una vez, sin reemplazar cargas existentes.
En Windows se fijan ancestros con handles que deniegan DELETE durante cada IO.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
LOCK = "tools/web-dependencies.lock.json"
ARCHIVE_ROOT = "tools/web-dependencies/archives"
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_BATCH_BYTES = 4 * 1024 * 1024 * 1024
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{family}{number}" for family in ("COM", "LPT") for number in range(1, 10)
}


class InputError(ValueError):
    """Entrada rechazada; el prefijo identifica el error para la CLI."""


def relative_name(name: str) -> str:
    """Nombre portable sin aliases de Windows, ADS ni componentes ambiguos."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise InputError("UNSAFE_PATH: nombre relativo inválido")
    for part in name.split("/"):
        if (
            part in ("", ".", "..")
            or len(part) > 255
            or part.endswith((" ", "."))
            or any(ord(c) < 32 or c in ':<>"|?*' for c in part)
            or part.split(".")[0].upper() in RESERVED
        ):
            raise InputError("UNSAFE_PATH: componente reservado o ambiguo")
    return name


def safe_path(root: Path, path: Path) -> Path:
    # Windows convierte NUL en \\.\NUL incluso dentro de abspath; validar antes.
    if str(path).startswith(("\\\\.\\", "\\\\?\\")):
        raise InputError("UNSAFE_PATH: namespace de dispositivos")
    for part in Path(path).parts[1:]:
        if part.split(".")[0].upper() in RESERVED or part.endswith((" ", ".")):
            raise InputError("UNSAFE_PATH: nombre reservado")
    root = Path(os.path.abspath(root))
    if not root.is_relative_to(ROOT):
        raise InputError("OUTSIDE_ROOT: límite distinto del repositorio")
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(root):
        raise InputError("OUTSIDE_ROOT: ruta fuera del repositorio")
    relative = path.relative_to(root).as_posix()
    if relative != ".":
        relative_name(relative)
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise InputError("UNSAFE_PATH: enlace, junction o reparse")
        if candidate != path and not stat.S_ISDIR(info.st_mode):
            raise InputError("UNSAFE_PATH: ancestro no es directorio")
    if os.path.normcase(str(path.resolve())) != os.path.normcase(str(path)):
        raise InputError("UNSAFE_PATH: alias de ruta")
    return path


def identity(info):
    # lstat Windows infiere bits ejecutables por sufijo; fstat no lo hace.
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _windows_handle(path: Path, directory: bool):
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    # Sin FILE_SHARE_DELETE; los archivos también deniegan escritura concurrente.
    handle = create(
        str(path),
        0x80000000,
        3 if directory else 1,
        None,
        3,
        0x02200000,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise InputError(f"UNSAFE_IO: {ctypes.get_last_error()}")
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    return handle, close


@contextmanager
def ancestors(root: Path, path: Path):
    """Revalida ancestros y fija su identidad nativa durante la operación."""
    path = safe_path(root, path)
    handles = []
    snapshots = {}
    try:
        for parent in reversed(path.parents):
            if not parent.exists():
                continue
            before = parent.lstat()
            if os.name == "nt":
                handle, close = _windows_handle(parent, True)
                handles.append((handle, close))
            else:
                fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                handles.append((fd, os.close))
            if identity(parent.lstat()) != identity(before):
                raise InputError("INPUT_CHANGED: ancestro sustituido")
            snapshots[parent] = identity(before)
        safe_path(root, path)
        yield path
        safe_path(root, path)
        if any(identity(p.lstat()) != value for p, value in snapshots.items()):
            raise InputError("INPUT_CHANGED: ancestro cambió durante IO")
    finally:
        for handle, close in reversed(handles):
            close(handle)


def read_file(root: Path, path: Path, limit: int = MAX_ARCHIVE_BYTES) -> bytes:
    with ancestors(root, path):
        try:
            before = path.lstat()
        except FileNotFoundError as exc:
            raise InputError(f"MISSING_INPUT: {path.name}") from exc
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise InputError("UNSAFE_FILE: especial o hardlink")
        if before.st_size > limit:
            raise InputError("INPUT_LIMIT: archivo demasiado grande")
        if os.name == "nt":
            import msvcrt

            handle, _ = _windows_handle(path, False)
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        else:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if identity(os.fstat(stream.fileno())) != identity(before):
                raise InputError("INPUT_CHANGED: archivo sustituido")
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        if (
            len(data) != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_nlink != 1
        ):
            raise InputError("INPUT_CHANGED: tamaño/fecha cambiados")
        if identity(path.lstat()) != identity(before):
            raise InputError("INPUT_CHANGED: identidad cambiada")
        return data


def metadata(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def authoritative(root: Path, name: str, data: bytes) -> None:
    """ROOT es la autoridad; --root selecciona entradas, nunca nuevos pins."""
    if root != ROOT and metadata(data) != metadata(read_file(ROOT, ROOT / name)):
        raise InputError("LOCK_MISMATCH: metadata distinta de ROOT autoritativo")


def verified(data: bytes, row: dict) -> None:
    if metadata(data) != {"bytes": row["bytes"], "sha256": row["sha256"]}:
        raise InputError("INTEGRITY: bytes/SHA256 no coinciden")
    if "integrity" in row:
        sri = "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode(
            "ascii"
        )
        if sri != row["integrity"]:
            raise InputError("INTEGRITY: SRI SHA512 no coincide")


def load_lock(root: Path) -> tuple[dict, dict]:
    raw = read_file(root, root / LOCK, 2 * 1024 * 1024)
    try:
        lock = json.loads(raw)
        rows = lock["artifacts"]
        if (
            lock["schema_version"] != 1
            or lock["artifact_count"] != 609
            or len(rows) != 609
        ):
            raise ValueError("609 entradas obligatorias")
        shas, packages = set(), set()
        total = 0
        for row in rows:
            sha = row["sha256"]
            if not re.fullmatch("[a-f0-9]{64}", sha):
                raise ValueError("SHA256")
            if row["archive_path"] != f"{ARCHIVE_ROOT}/{sha}.tgz":
                raise ValueError("destino")
            if (
                type(row["bytes"]) is not int
                or not 0 < row["bytes"] <= MAX_ARCHIVE_BYTES
            ):
                raise ValueError("tamaño")
            sri = row["integrity"]
            if (
                not isinstance(sri, str)
                or not sri.startswith("sha512-")
                or len(base64.b64decode(sri[7:], validate=True)) != 64
            ):
                raise ValueError("SRI")
            package = row["name"] + "@" + row["version"]
            if sha in shas or package in packages:
                raise ValueError("duplicado")
            shas.add(sha)
            packages.add(package)
            total += row["bytes"]
        if total > MAX_BATCH_BYTES:
            raise ValueError("lote excesivo")
    except (KeyError, TypeError, ValueError) as exc:
        raise InputError("INVALID_LOCK: metadata inválida") from exc
    authoritative(root, LOCK, raw)
    pnpm = read_file(root, root / "pnpm-lock.yaml", 2 * 1024 * 1024)
    if hashlib.sha256(pnpm).hexdigest() != lock["pnpm_lock_sha256"]:
        raise InputError("LOCK_MISMATCH: pnpm-lock SHA256")
    # Sólo sección packages; snapshots de peers no son otra distribución.
    package_text = (
        pnpm.decode("utf-8").split("\npackages:\n", 1)[-1].split("\nsnapshots:\n", 1)[0]
    )
    blocks = re.findall(
        r"^  ([^\n]+):\n((?:    [^\n]*\n|\n)*)", package_text, re.MULTILINE
    )
    resolutions = {key.strip("'"): body for key, body in blocks}
    for row in rows:
        if f"integrity: {row['integrity']}" not in resolutions.get(
            row["name"] + "@" + row["version"], ""
        ):
            raise InputError("LOCK_MISMATCH: paquete/SRI pnpm")
    return lock, {LOCK: metadata(raw), "pnpm-lock.yaml": metadata(pnpm)}


def list_files(root: Path, directory: Path, maximum: int) -> list[Path]:
    safe_path(root, directory)
    if not directory.is_dir():
        raise InputError("MISSING_INPUT: directorio de archivos")
    with ancestors(root, directory / "unused"):
        paths = sorted(directory.iterdir())
        if len(paths) > maximum:
            raise InputError("INPUT_LIMIT: demasiadas entradas")
        for path in paths:
            safe_path(root, path)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise InputError("UNSAFE_FILE: entrada especial o hardlink")
        return paths


def check_archives(root: Path, lock: dict) -> dict[Path, dict]:
    directory = root / ARCHIVE_ROOT
    paths = list_files(root, directory, 609)
    expected = {row["sha256"] + ".tgz": row for row in lock["artifacts"]}
    if {p.name for p in paths} != set(expected):
        raise InputError("ARCHIVE_SET: publicación incompleta o ajena")
    result = {}
    for path in paths:
        row = expected[path.name]
        verified(read_file(root, path), row)
        result[path] = row
    return result


def unchanged(root: Path, frozen: dict) -> None:
    for name, row in frozen.items():
        verified(read_file(root, root / name), row)


def rename_new(source: Path, destination: Path) -> None:
    """Rename atómico que nunca sustituye ni siquiera un directorio vacío ajeno."""
    if os.name == "nt":
        os.rename(source, destination)
    else:
        libc = ctypes.CDLL(None, use_errno=True)
        rename = getattr(libc, "renameat2", None)
        if rename is None:
            raise InputError("UNSUPPORTED_ATOMIC_PUBLISH: renameat2 necesario")
        if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
            raise OSError(ctypes.get_errno(), "renameat2 no-replace")


class Publication:
    """Stage propio y lease exclusivo; cleanup sólo de las entradas creadas."""

    def __init__(self, root: Path, destination: Path):
        self.root = root
        self.destination = safe_path(root, destination)
        self.stage = destination.parent / (".web-input-" + uuid.uuid4().hex)
        self.files = {}
        self.directories = {}
        self.lease = destination.parent / (".web-input-" + destination.name + ".lock")
        self.guard = None
        self.lease_fd = None
        self.published = False

    def __enter__(self):
        safe_path(self.root, self.destination)
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        self.guard = ancestors(self.root, self.destination)
        self.guard.__enter__()
        try:
            self.lease_fd = os.open(
                self.lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
            self.lease_identity = identity(os.fstat(self.lease_fd))
            if self.destination.exists():
                raise InputError("DESTINATION_EXISTS: no sustituir salida")
            self.stage.mkdir(mode=0o700)
            self.directories[self.stage] = identity(self.stage.lstat())
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def write(self, name: str, data: bytes, executable: bool = False):
        target = self.stage / relative_name(name)
        with ancestors(self.root, target):
            for parent in reversed(target.parents):
                if parent.is_relative_to(self.stage) and parent not in self.directories:
                    parent.mkdir(mode=0o700)
                    self.directories[parent] = identity(parent.lstat())
            with target.open("xb") as stream:
                self.files[target] = metadata(data)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            target.chmod(0o755 if executable else 0o644)
            verified(read_file(self.root, target), self.files[target])

    def audit(self):
        actual = set()
        for directory, expected in self.directories.items():
            safe_path(self.root, directory)
            if identity(directory.lstat()) != expected:
                raise InputError("STAGE_CHANGED: directorio sustituido")
            actual.update(directory.iterdir())
        if actual != set(self.files) | (set(self.directories) - {self.stage}):
            raise InputError("STAGE_CHANGED: entrada ajena; conservar stage")
        for path, row in self.files.items():
            verified(read_file(self.root, path), row)

    def publish(self):
        self.audit()
        safe_path(self.root, self.destination)
        if self.destination.exists():
            raise InputError("DESTINATION_EXISTS: carrera de publicación")
        rename_new(self.stage, self.destination)
        self.published = True

    def __exit__(self, *error):
        try:
            if not self.published and self.stage.exists():
                # Nunca borrar un stage al que alguien añadió contenido extranjero.
                self.audit()
                for path in self.files:
                    path.unlink()
                for path in sorted(
                    self.directories, key=lambda p: len(p.parts), reverse=True
                ):
                    path.rmdir()
        finally:
            if self.lease_fd is not None:
                os.close(self.lease_fd)
                if identity(self.lease.lstat()) == self.lease_identity:
                    self.lease.unlink()
            if self.guard is not None:
                self.guard.__exit__(*error)


def import_local(root: Path, source: Path) -> dict:
    root, source = Path(os.path.abspath(root)), Path(os.path.abspath(source))
    safe_path(ROOT, root)
    lock, frozen = load_lock(root)
    destination = root / ARCHIVE_ROOT
    safe_path(root, destination)
    if destination.exists():
        check_archives(root, lock)
    safe_path(root, source)
    if (
        source == destination
        or destination.is_relative_to(source)
        or source.is_relative_to(destination)
    ):
        raise InputError("UNSAFE_PATH: fuente y destino se solapan")
    rows = {row["sha256"]: row for row in lock["artifacts"]}
    found = {}
    paths = list_files(root, source, 609)
    for path in paths:
        if path.suffix != ".tgz":
            raise InputError("UNKNOWN_ARCHIVE: sólo tgz fijados")
        data = read_file(root, path)
        sha = hashlib.sha256(data).hexdigest()
        if sha not in rows:
            raise InputError("UNKNOWN_ARCHIVE: hash no fijado")
        if sha in found:
            raise InputError("AMBIGUOUS_ARCHIVE: dos entradas para el mismo hash")
        verified(data, rows[sha])
        found[sha] = path
    if set(found) != set(rows):
        raise InputError(
            f"MISSING_ARCHIVES: faltan {len(set(rows) - set(found))}; nada publicado"
        )
    unchanged(root, frozen)
    if destination.exists():
        return {"verified": len(rows), "published": False}
    with Publication(root, destination) as publication:
        for sha, row in rows.items():
            data = read_file(root, found[sha])
            verified(data, row)
            publication.write(sha + ".tgz", data)
        for sha, path in found.items():
            verified(read_file(root, path), rows[sha])
        if list_files(root, source, 609) != paths:
            raise InputError("INPUT_CHANGED: conjunto fuente cambiado")
        unchanged(root, frozen)
        publication.publish()
    return {"verified": len(rows), "published": True}


def check(root: Path) -> dict:
    root = Path(os.path.abspath(root))
    safe_path(ROOT, root)
    lock, frozen = load_lock(root)
    check_archives(root, lock)
    unchanged(root, frozen)
    return {"verified": 609, "published": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Importar/verificar tgz locales fijados; sin red"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--import-local", type=Path)
    group.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--check-integrity",
        action="store_true",
        help="Siempre obligatorio; flag explícito compatible",
    )
    args = parser.parse_args(argv)
    try:
        result = (
            import_local(args.root, args.import_local)
            if args.import_local
            else check(args.root)
        )
    except (InputError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
