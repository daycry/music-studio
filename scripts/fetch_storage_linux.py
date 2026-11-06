"""Adquisicion confinada del sysroot Linux para ADR-0069.

Este script solo descarga/verifica paquetes y prepara un sysroot privado dentro
del checkout. No instala paquetes, no inicia servicios y no monta discos.
"""

from __future__ import annotations

import argparse
import ctypes
import gzip
import hashlib
import io
import json
import lzma
import os
import posixpath
import shutil
import stat
import tarfile
import time
import urllib.request
import uuid
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "tools/storage-linux.lock.json"
MAX_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 100_000
MAX_EXPANDED_BYTES = 2 * 1024 * 1024 * 1024
CHUNK = 1024 * 1024


class InputError(ValueError):
    """Entrada o paquete no acreditado; no se publica nada."""


def _plain(path: Path, *, directory: bool = False):
    info = path.lstat()
    expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if (
        stat.S_ISLNK(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
        or not expected
    ):
        raise InputError("ruta enlazada o tipo no permitido")
    return info


def _root(value):
    base = ROOT.resolve(strict=True)
    path = base if value is None else Path(value).absolute()
    if path != path.resolve(strict=False) or not path.is_relative_to(base):
        raise InputError("root fuera del repositorio o ambiguo")
    current = base
    for part in path.relative_to(base).parts:
        current /= part
        if current.exists():
            _plain(current, directory=True)
    return path


def _load_pin():
    try:
        pin = json.loads(LOCK.read_text("utf-8"))
        packages = pin["packages"]
        if (
            pin["schema_version"] != 1
            or pin["dest"]
            != "tools/storage-linux/debian-bookworm-amd64/bundle-2026-10-09"
        ):
            raise KeyError
        if not isinstance(packages, list) or not packages:
            raise KeyError
        names = set()
        for item in packages:
            if not isinstance(item["package"], str) or item["package"] in names:
                raise KeyError
            names.add(item["package"])
            if (
                not isinstance(item["bytes"], int)
                or not 1 <= item["bytes"] <= MAX_PACKAGE_BYTES
                or not isinstance(item["sha256"], str)
                or len(item["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in item["sha256"])
                or not item["url"].startswith(
                    ("https://deb.debian.org/", "https://security.debian.org/")
                )
            ):
                raise KeyError
        if not pin["executables"] or any(
            not isinstance(path, str) or path.startswith("/")
            for path in pin["executables"]
        ):
            raise KeyError
        return pin
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InputError("lock storage-linux invalido") from exc


def _digest(path: Path, expected_bytes: int | None = None):
    before = _plain(path)
    if expected_bytes is not None and before.st_size != expected_bytes:
        raise InputError("tamanio de paquete no coincide")
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK):
            count += len(chunk)
            if count > MAX_PACKAGE_BYTES:
                raise InputError("paquete excede el limite")
            digest.update(chunk)
    after = _plain(path)
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise InputError("paquete cambio durante la lectura")
    return {"sha256": digest.hexdigest(), "bytes": count}


def _verify_package(path: Path, item: dict):
    actual = _digest(path, item["bytes"])
    if actual != {"sha256": item["sha256"], "bytes": item["bytes"]}:
        raise InputError(f"hash o tamanio no coincide: {item['package']}")


def _ar_members(payload: bytes):
    if not payload.startswith(b"!<arch>\n"):
        raise InputError("DEB sin cabecera ar")
    result = {}
    offset = 8
    while offset < len(payload):
        if len(result) >= 32 or offset + 60 > len(payload):
            raise InputError("cabecera ar truncada o demasiados miembros")
        header = payload[offset : offset + 60]
        offset += 60
        if header[58:60] != b"`\n":
            raise InputError("cabecera ar invalida")
        name = header[:16].decode("ascii", errors="strict").strip().rstrip("/")
        if not name or name in result or name.startswith("/"):
            raise InputError("miembro ar ambiguo")
        try:
            size = int(header[48:58].decode("ascii").strip())
        except ValueError as exc:
            raise InputError("tamanio ar invalido") from exc
        if size < 0 or size > MAX_EXPANDED_BYTES or offset + size > len(payload):
            raise InputError("miembro ar fuera de limites")
        result[name] = payload[offset : offset + size]
        offset += size + size % 2
    if (
        offset != len(payload)
        or "data.tar.xz" not in result
        and "data.tar.gz" not in result
    ):
        raise InputError("DEB sin data.tar.xz/data.tar.gz")
    return result


def _data_tar(payload: bytes):
    members = _ar_members(payload)
    compressed = members.get("data.tar.xz") or members.get("data.tar.gz")
    try:
        raw = (
            lzma.LZMADecompressor(
                format=lzma.FORMAT_XZ, memlimit=256 * CHUNK
            ).decompress(compressed)
            if "data.tar.xz" in members
            else gzip.decompress(compressed)
        )
    except (EOFError, lzma.LZMAError, OSError) as exc:
        raise InputError("data.tar comprimido invalido") from exc
    if len(raw) > MAX_EXPANDED_BYTES:
        raise InputError("data.tar expandido excede el limite")
    try:
        result = []
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
            for member in archive:
                content = (
                    archive.extractfile(member).read() if member.isfile() else None
                )
                result.append((member, content))
        return result
    except tarfile.TarError as exc:
        raise InputError("data.tar invalido") from exc


def _relative(name: str):
    name = name.removeprefix("./")
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or any("\\" in part or "\x00" in part for part in path.parts)
        or len(path.parts) > 64
    ):
        raise InputError("ruta TAR insegura")
    return "/".join(path.parts)


def _ensure_parent(path: Path, stage: Path):
    parent = path.parent
    if not parent.is_relative_to(stage):
        raise InputError("ruta fuera del stage")
    parent.mkdir(parents=True, exist_ok=True)
    current = stage
    for part in parent.relative_to(stage).parts:
        current /= part
        _plain(current, directory=True)


def _read_archive(path: Path):
    info = _plain(path)
    if info.st_size > MAX_PACKAGE_BYTES:
        raise InputError("paquete demasiado grande")
    return _data_tar(path.read_bytes())


def _extract_packages(package_paths, pin, stage):
    symlinks = {}
    hardlinks = {}
    aliases = {}
    files = {}
    directories = set()
    for item, package_path in zip(pin["packages"], package_paths):
        _verify_package(package_path, item)
        for member, content in _read_archive(package_path):
            relative = _relative(member.name)
            destination = stage / Path(*relative.split("/"))
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                _plain(destination, directory=True)
                directories.add(relative)
                continue
            if member.isdev() or member.isfifo():
                raise InputError("tipo TAR especial rechazado")
            _ensure_parent(destination, stage)
            if member.islnk():
                target = _relative(member.linkname)
                if (
                    relative in aliases
                    or destination.exists()
                    or destination.is_symlink()
                ):
                    raise InputError("colision de hardlink")
                aliases[relative] = target
                hardlinks[relative] = target
                continue
            if member.issym():
                if member.linkname.startswith("/"):
                    target_text = posixpath.normpath(member.linkname.lstrip("/"))
                else:
                    target_text = posixpath.normpath(
                        posixpath.join(
                            str(PurePosixPath(relative).parent), member.linkname
                        )
                    )
                target = PurePosixPath(target_text)
                if (
                    target.is_absolute()
                    or target_text in {"", ".", ".."}
                    or target_text.startswith("../")
                ):
                    raise InputError("symlink TAR fuera del sysroot")
                if destination.exists() or destination.is_symlink():
                    raise InputError("colision de symlink")
                symlinks[relative] = str(target)
                aliases[relative] = str(target)
                continue
            if (
                not member.isfile()
                or member.size < 0
                or member.size > MAX_PACKAGE_BYTES
            ):
                raise InputError("archivo TAR no permitido")
            data = content
            if data is None:
                raise InputError("archivo TAR sin contenido")
            digest = hashlib.sha256(data).hexdigest()
            if relative in symlinks:
                raise InputError("colision archivo/symlink")
            if destination.exists():
                if not destination.is_file() or destination.read_bytes() != data:
                    raise InputError("colision de paquetes")
            else:
                destination.write_bytes(data)
            destination.chmod(member.mode & 0o777)
            files[relative] = {"sha256": digest, "bytes": len(data)}

    # Materializar aliases como copias regulares mantiene el sysroot portable en Windows.
    def materialize(relative, stack=()):
        if relative in stack:
            raise InputError("ciclo de enlaces en sysroot")
        destination = stage / Path(*relative.split("/"))
        if relative not in aliases:
            if not destination.exists() or destination.is_symlink():
                raise InputError(f"enlace sin objetivo acreditado: {relative}")
            return destination
        source = materialize(aliases[relative], (*stack, relative))
        if source.is_file():
            data = source.read_bytes()
            destination.write_bytes(data)
            destination.chmod(0o644)
            files[relative] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        elif source.is_dir():
            if destination.exists() or destination.is_symlink():
                raise InputError(f"colision de directorio enlazado: {relative}")
            shutil.copytree(source, destination)
            for copied in destination.rglob("*"):
                if copied.is_file() and not copied.is_symlink():
                    key = copied.relative_to(stage).as_posix()
                    files[key] = {
                        "sha256": hashlib.sha256(copied.read_bytes()).hexdigest(),
                        "bytes": copied.stat().st_size,
                    }
        else:
            raise InputError(f"enlace sin objetivo regular: {relative}")
        return destination

    for relative in aliases:
        materialize(relative)
    copyrights = {}
    for item in pin["packages"]:
        notice = stage / "usr/share/doc" / item["package"] / "copyright"
        if not notice.is_file() or notice.is_symlink():
            raise InputError(f"copyright Debian ausente: {item['package']}")
        copyrights[item["package"]] = {
            "path": notice.relative_to(stage).as_posix(),
            "sha256": hashlib.sha256(notice.read_bytes()).hexdigest(),
            "bytes": notice.stat().st_size,
        }
    for executable in pin["executables"]:
        path = stage / Path(*executable.split("/"))
        if not path.is_file() or path.is_symlink():
            raise InputError(f"ejecutable ausente: {executable}")
        path.chmod(path.stat().st_mode | 0o111)
    return (
        files,
        sorted(directories),
        {"symlinks": symlinks, "hardlinks": hardlinks},
        copyrights,
    )


def _publish(stage: Path, destination: Path):
    if os.name == "nt":
        os.rename(stage, destination)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise InputError("Linux sin renameat2; no publicar")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(stage), -100, os.fsencode(destination), 1):
        raise OSError(ctypes.get_errno(), "publicacion sin reemplazo rechazada")


def _package_paths(source: Path, pin):
    if not source.is_dir() or source.is_symlink():
        raise InputError("directorio de DEB invalido")
    paths = []
    for item in pin["packages"]:
        exact = source / f"{item['package']}.deb"
        candidates = (
            [exact]
            if exact.is_file()
            else sorted(source.glob(f"{item['package']}_*.deb"))
        )
        if len(candidates) != 1:
            raise InputError(f"DEB local ausente o ambiguo: {item['package']}")
        _plain(candidates[0])
        paths.append(candidates[0])
    return paths


def _download(path: Path, item):
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if not newurl.startswith(
                ("https://deb.debian.org/", "https://security.debian.org/")
            ):
                raise InputError("redirect fuera de Debian fijado")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(Redirect())
    deadline = time.monotonic() + 600
    with opener.open(item["url"], timeout=30) as response, path.open("xb") as output:
        total = 0
        while chunk := response.read(CHUNK):
            total += len(chunk)
            if total > item["bytes"] or time.monotonic() > deadline:
                raise InputError("descarga de DEB excede limites")
            output.write(chunk)
    _verify_package(path, item)


def _check(destination: Path, pin):
    _plain(destination, directory=True)
    metadata = json.loads((destination / ".provenance.json").read_text("utf-8"))
    if metadata["pin"] != pin:
        raise InputError("provenance no coincide con lock")
    actual = {}
    for parent, _, names in os.walk(destination, followlinks=False):
        for name in names:
            path = Path(parent) / name
            if name in {".owner", ".provenance.json"} and path.parent == destination:
                continue
            _plain(path)
            relative = path.relative_to(destination).as_posix()
            actual[relative] = _digest(path)
    if actual != metadata["files"]:
        raise InputError("sysroot alterado o incompleto")
    for package, notice in metadata["copyrights"].items():
        path = destination / Path(*notice["path"].split("/"))
        if not path.is_file() or _digest(path) != {
            "sha256": notice["sha256"],
            "bytes": notice["bytes"],
        }:
            raise InputError(f"copyright alterado: {package}")
    for executable in pin["executables"]:
        path = destination / Path(*executable.split("/"))
        if not path.is_file() or (os.name != "nt" and not path.stat().st_mode & 0o111):
            raise InputError("ejecutable no verificable")


def acquire(source=None, *, root=None, download=False, check=False):
    if (
        type(download) is not bool
        or type(check) is not bool
        or sum((source is not None, download, check)) != 1
    ):
        raise InputError("elige exactamente import-local, download o check")
    root = _root(root)
    pin = _load_pin()
    destination = root / pin["dest"]
    if check:
        _check(destination, pin)
        return destination
    if destination.exists() or destination.is_symlink():
        raise InputError("destino existente preservado")
    package_paths = []
    if source is not None:
        source = Path(source).absolute()
        if not source.is_relative_to(ROOT.resolve()) or source.resolve() != source:
            raise InputError("source fuera del repositorio o ambiguo")
        package_paths = _package_paths(source, pin)
    else:
        cache = ROOT / ".cache/fetch/storage-linux"
        cache.mkdir(parents=True, exist_ok=True)
        for item in pin["packages"]:
            path = cache / f"{item['sha256']}.deb"
            if not path.exists():
                _download(path, item)
            else:
                _verify_package(path, item)
            package_paths.append(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / f".stage-{uuid.uuid4().hex}"
    stage.mkdir()
    try:
        files, directories, aliases, copyrights = _extract_packages(
            package_paths, pin, stage
        )
        (stage / ".owner").write_text(uuid.uuid4().hex, encoding="ascii")
        (stage / ".provenance.json").write_text(
            json.dumps(
                {
                    "pin": pin,
                    "files": files,
                    "directories": directories,
                    "materialized_aliases": aliases,
                    "copyrights": copyrights,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        _check(stage, pin)
        _publish(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=False)
    return destination


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError(message)


def main(argv=None):
    parser = _Parser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--import-local", type=Path)
    group.add_argument("--download", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path)
    try:
        args = parser.parse_args(argv)
        destination = acquire(
            args.import_local, root=args.root, download=args.download, check=args.check
        )
        print(f"storage Linux verificado: {destination.relative_to(ROOT)}")
        return 0
    except (InputError, OSError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"storage Linux NO LISTO: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
