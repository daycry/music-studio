"""Preparación explícita y acotada de FFmpeg Linux; no ejecuta sus binarios."""

import argparse
import ctypes
import hashlib
import json
import lzma
import os
import shutil
import stat
import sys
import tarfile
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_ENTRIES = 10000
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_EXPANDED_BYTES = 1024 * 1024 * 1024
CHUNK = 1024 * 1024
RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(10)),
    *(f"lpt{i}" for i in range(10)),
}
INTERNAL = {".archive.tar.xz", ".provenance.json", ".owner"}


class InputError(ValueError):
    """Entrada inválida o custodia no acreditada; CLI termina con código 2."""


def _load_pin():
    # Sólo el lock del checkout autoritativo, nunca el root de salida.
    pin = json.loads((ROOT / "tools/ffmpeg-linux.lock.json").read_text("utf-8"))
    candidate = pin["candidate"]
    if (
        pin["schema_version"] != 1
        or pin["archive_format"] != "tar.xz"
        or not isinstance(candidate["bytes"], int)
        or isinstance(candidate["bytes"], bool)
        or not 0 < candidate["bytes"] <= 256 * CHUNK
        or len(candidate["sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in candidate["sha256"])
        or not candidate["url"].startswith(
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
        )
        or candidate["url"].rsplit("/", 1)[-1] != candidate["asset"]
        or pin["dest"] != "tools/ffmpeg-linux/n9.0.2-17-g2a571b6068"
    ):
        raise InputError("Lock Linux inválido")
    return pin


def _plain(path, directory=False):
    info = path.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    ):
        raise InputError("Ruta enlazada o de tipo no permitido")
    return info


def _root(value):
    if value is not None and not isinstance(value, (str, Path)):
        raise InputError("root debe ser una ruta")
    base = ROOT.resolve()
    path = base if value is None else Path(value).absolute()
    if not path.is_relative_to(base):
        raise InputError("root fuera del repositorio")
    for part in [
        base,
        *[
            base.joinpath(*path.relative_to(base).parts[:i])
            for i in range(1, len(path.relative_to(base).parts) + 1)
        ],
    ]:
        _plain(part, directory=True)
    if path.resolve() != path:
        raise InputError("root ambiguo")
    return path


def _parents(path, root):
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        _plain(current, directory=True)


def _digest(path, limit):
    before = _plain(path)
    if before.st_size > limit:
        raise InputError("Archivo excede el límite")
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK):
            count += len(chunk)
            if count > limit:
                raise InputError("Archivo creció fuera del límite")
            digest.update(chunk)
    after = _plain(path)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise InputError("Archivo cambió durante la lectura")
    return {"sha256": digest.hexdigest(), "bytes": count}


def _verify_archive(path, pin):
    expected = {k: pin["candidate"][k] for k in ("sha256", "bytes")}
    if _digest(path, expected["bytes"]) != expected:
        raise InputError("SHA-256 o tamaño del archivo original no coincide")


class _BoundedXZ:
    """Descompresión incremental con límites de memoria y bytes, incluidos headers."""

    def __init__(self, stream):
        self.stream = stream
        self.decoder = lzma.LZMADecompressor(
            format=lzma.FORMAT_XZ, memlimit=128 * CHUNK
        )
        self.total = 0

    def read(self, size):
        output = bytearray()
        while len(output) < size and not self.decoder.eof:
            block = self.stream.read(65536) if self.decoder.needs_input else b""
            if self.decoder.needs_input and not block:
                raise InputError("XZ truncado")
            piece = self.decoder.decompress(block, max_length=size - len(output))
            self.total += len(piece)
            if self.total > MAX_EXPANDED_BYTES:
                raise InputError("XZ expandido excede el límite")
            output.extend(piece)
        return bytes(output)


class _Info(tarfile.TarInfo):
    headers = 0

    @classmethod
    def frombuf(cls, buf, encoding, errors):
        cls.headers += 1
        if cls.headers > MAX_ENTRIES:
            raise InputError("Demasiados headers TAR")
        for field in (buf[:100], buf[345:500]):
            if b"\0" in field and field.split(b"\0", 1)[1].strip(b"\0"):
                raise InputError("NUL ambiguo en nombre TAR")
        return super().frombuf(buf, encoding, errors)

    def _proc_pax(self, tarfile):
        if self.size > 8192:
            raise InputError("Metadatos TAR excesivos")
        return super()._proc_pax(tarfile)

    def _proc_gnulong(self, tarfile):
        if self.size > 4096:
            raise InputError("Nombre TAR excesivo")
        return super()._proc_gnulong(tarfile)


def _name(member, prefix):
    name = member.name
    if member.isdir() and name.endswith("/"):
        name = name[:-1]
    parts = name.split("/")
    if len(name) > 1024 or not parts or len(parts) > 32:
        raise InputError("Nombre TAR excesivo")
    for part in parts:
        if (
            not part
            or part in (".", "..")
            or part[-1] in " ."
            or any(ord(c) < 32 or c in '\\:<>"|?*' for c in part)
            or part.split(".", 1)[0].casefold() in RESERVED
        ):
            raise InputError("Miembro TAR inseguro")
    if prefix is not None and parts[0] != prefix:
        raise InputError("Prefijo TAR ambiguo")
    if parts[0].casefold() in INTERNAL or any(
        p.casefold() in INTERNAL for p in parts[1:]
    ):
        raise InputError("Nombre reservado para procedencia")
    if not member.isdir() and len(parts) < 2:
        raise InputError("Miembro sin prefijo de release")
    return parts[0], "/".join(parts[1:])


def _payload(archive, stage=None):
    files = {}
    directories = set()
    seen = {}
    spellings = {}
    prefix = None
    count = total = 0
    with archive.open("rb") as source:
        info_type = type("BoundedInfo", (_Info,), {"headers": 0})
        with tarfile.open(
            fileobj=_BoundedXZ(source), mode="r|", tarinfo=info_type
        ) as tar:
            for member in tar:
                count += 1
                if count > MAX_ENTRIES:
                    raise InputError("Demasiados miembros TAR")
                if (
                    member.type
                    not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
                    or member.sparse is not None
                ):
                    raise InputError("Enlace o miembro especial TAR rechazado")
                prefix, relative = _name(member, prefix)
                parts = relative.split("/")
                for i in range(1, len(parts) + 1):
                    spelling = "/".join(parts[:i])
                    old = spellings.setdefault(spelling.casefold(), spelling)
                    if old != spelling:
                        raise InputError("Directorio o miembro ambiguo por mayúsculas")
                key = relative.casefold()
                if key in seen:
                    raise InputError("Miembro TAR duplicado")
                for other, kind in seen.items():
                    if (
                        key.startswith(other + "/")
                        and kind == "file"
                        or other.startswith(key + "/")
                        and member.isfile()
                    ):
                        raise InputError("Colisión archivo/directorio")
                seen[key] = "directory" if member.isdir() else "file"
                parts = relative.split("/")
                for i in range(1, len(parts)):
                    directories.add("/".join(parts[:i]))
                if member.size < 0 or member.size > MAX_FILE_BYTES:
                    raise InputError("Miembro TAR excede el límite")
                total += member.size
                if total > MAX_EXPANDED_BYTES:
                    raise InputError("Carga expandida excesiva")
                if member.isdir():
                    if relative:
                        directories.add(relative)
                    if stage and relative:
                        (stage / relative).mkdir(parents=True, exist_ok=True)
                    continue
                digest = hashlib.sha256()
                stream = tar.extractfile(member)
                target = None
                try:
                    if stage:
                        path = stage / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        target = path.open("xb")
                    remaining = member.size
                    while remaining:
                        chunk = stream.read(min(CHUNK, remaining))
                        if not chunk:
                            raise InputError("Miembro TAR truncado")
                        remaining -= len(chunk)
                        digest.update(chunk)
                        if target:
                            target.write(chunk)
                finally:
                    if target:
                        target.close()
                    stream.close()
                executable = relative in ("bin/ffmpeg", "bin/ffprobe")
                if stage:
                    (stage / relative).chmod(0o755 if executable else 0o644)
                files[relative] = {"sha256": digest.hexdigest(), "bytes": member.size}
    if not {"bin/ffmpeg", "bin/ffprobe"}.issubset(files) or not any(
        "license" in p.casefold() or "copying" in p.casefold() for p in files
    ):
        raise InputError("Carga incompleta: binarios o licencia ausentes")
    return files, sorted(directories)


def _publish(stage, dest):
    if os.name == "nt":
        os.rename(stage, dest)  # Windows rename no reemplaza un destino existente.
    else:
        # Linux renameat2(RENAME_NOREPLACE); sin fallback que reemplace destinos.
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(stage), -100, os.fsencode(dest), 1):
            raise OSError(ctypes.get_errno(), "No se pudo publicar sin reemplazo")


def _cleanup(path, token, identity):
    if not path.exists():
        return
    try:
        info = _plain(path, directory=True)
        if (info.st_dev, info.st_ino) != identity or (
            path / ".owner"
        ).read_text() != token:
            raise InputError("Custodia de cleanup UNKNOWN; se conserva")
        # No seguir junctions ni enlaces introducidos en la fase propia.
        for parent, dirs, files in os.walk(path, followlinks=False):
            for name in dirs:
                _plain(Path(parent) / name, directory=True)
            for name in files:
                _plain(Path(parent) / name)
        shutil.rmtree(path)
    except OSError as exc:
        raise InputError("Cleanup UNKNOWN; se conserva lo restante") from exc


def _cleanup_lock(path, token, identity, marked):
    # Antes del marcador sólo se acredita el nacimiento y la identidad del vacío.
    # Nunca se recorre ni se borra recursivamente un lock con entradas ajenas.
    try:
        info = _plain(path, directory=True)
        if identity is None or (info.st_dev, info.st_ino) != identity:
            raise InputError("Custodia de lock UNKNOWN; se conserva")
        entries = list(path.iterdir())
        if marked:
            owner = path / ".owner"
            if entries != [owner]:
                raise InputError("Entradas de lock UNKNOWN; se conserva")
            _plain(owner)
            if owner.read_text() != token:
                raise InputError("Marcador de lock UNKNOWN; se conserva")
            owner.unlink()
        elif entries:
            raise InputError("Lock sin marcador acreditado UNKNOWN; se conserva")
        path.rmdir()  # Sólo vacío; una entrada concurrente impide eliminarlo.
    except OSError as exc:
        raise InputError("Cleanup de lock UNKNOWN; se conserva") from exc


def _check(dest, pin):
    _plain(dest, directory=True)
    archive = dest / ".archive.tar.xz"
    _verify_archive(archive, pin)
    expected, directories = _payload(archive)
    provenance = dest / ".provenance.json"
    if _plain(provenance).st_size > 8 * CHUNK:
        raise InputError("Procedencia excede el límite")
    with provenance.open("rb") as stream:
        raw = stream.read(8 * CHUNK + 1)
    if len(raw) > 8 * CHUNK:
        raise InputError("Procedencia creció fuera del límite")
    metadata = json.loads(raw)
    if metadata != {"pin": pin, "files": expected, "directories": directories}:
        raise InputError("Cadena de procedencia no coincide")
    actual = set()
    actual_dirs = set()
    for parent, dirs, names in os.walk(dest, followlinks=False):
        for name in dirs:
            path = Path(parent) / name
            _plain(path, directory=True)
            actual_dirs.add(path.relative_to(dest).as_posix())
        for name in names:
            path = Path(parent) / name
            info = _plain(path)
            if info.st_mode & 0o7000:
                raise InputError("Modo privilegiado rechazado")
            relative = path.relative_to(dest).as_posix()
            if (
                sys.platform == "linux"
                and relative in ("bin/ffmpeg", "bin/ffprobe")
                and info.st_mode & 0o111 != 0o111
            ):
                raise InputError("Binario Linux sin modo ejecutable normalizado")
            actual.add(relative)
            if (
                relative in expected
                and _digest(path, MAX_FILE_BYTES) != expected[relative]
            ):
                raise InputError("Carga publicada alterada")
    if actual != set(expected) | {
        ".archive.tar.xz",
        ".provenance.json",
        ".owner",
    } or actual_dirs != set(directories):
        raise InputError("Carga publicada incompleta o contiene archivos ajenos")


def _download(path, pin):
    deadline = time.monotonic() + 600

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            # GitHub entrega el asset por HTTPS mediante URL firmada del CDN.
            if not newurl.startswith("https://release-assets.githubusercontent.com/"):
                raise InputError("Redirect fuera del CDN oficial")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(NoRedirect())
    with (
        opener.open(pin["candidate"]["url"], timeout=30) as response,
        path.open("xb") as out,
    ):
        count = 0
        while chunk := response.read(CHUNK):
            if time.monotonic() > deadline:
                raise InputError("Descarga superó el plazo de 600 segundos")
            count += len(chunk)
            if count > pin["candidate"]["bytes"]:
                raise InputError("Descarga excede el tamaño fijado")
            out.write(chunk)
    _verify_archive(path, pin)


def acquire(source=None, *, root=None, download=False, check=False):
    if source is not None and not isinstance(source, (str, Path)):
        raise InputError("source debe ser una ruta")
    if (
        type(download) is not bool
        or type(check) is not bool
        or sum((source is not None, download, check)) != 1
    ):
        raise InputError("Elige exactamente import-local, download o check")
    root = _root(root)
    pin = _load_pin()
    dest = root / pin["dest"]
    # Rechaza enlaces existentes antes de cualquier efecto.
    for parent in reversed(dest.parents):
        if parent.is_relative_to(root) and parent.exists():
            _plain(parent, directory=True)
    if check:
        _check(dest, pin)
        return dest
    if dest.exists() or dest.is_symlink():
        raise InputError("Destino existente preservado; usa --check")
    if source is not None:
        source = Path(source).absolute()
        if not source.is_relative_to(ROOT.resolve()) or source.resolve() != source:
            raise InputError("Archivo local fuera del repositorio o enlazado")
        _verify_archive(source, pin)
    _parents(dest.parent, root)
    lock = dest.parent / ".acquisition-lock"
    lock.mkdir()  # Exclusión propia, no se borra un lock preexistente.
    token = uuid.uuid4().hex
    stage = dest.parent / (".stage-" + token)
    lock_identity = None
    lock_marked = False
    stage_identity = None
    try:
        info = _plain(lock, directory=True)
        lock_identity = (info.st_dev, info.st_ino)
        (lock / ".owner").write_text(token)
        lock_marked = True
        stage.mkdir()
        info = _plain(stage, directory=True)
        stage_identity = (info.st_dev, info.st_ino)
        (stage / ".owner").write_text(token)
        archive = stage / ".archive.tar.xz"
        if download:
            cache = ROOT / ".cache/fetch/ffmpeg-linux-acquisition"
            _parents(cache, ROOT)
            cached = cache / (pin["candidate"]["sha256"] + ".tar.xz")
            if cached.exists():
                _verify_archive(cached, pin)
            else:
                _download(archive, pin)
                # El hardlink publica bytes completos sin reemplazar entradas ajenas.
                os.link(archive, cached)
                _verify_archive(cached, pin)
            source = cached
        if not archive.exists():
            with source.open("rb") as inp, archive.open("xb") as out:
                remaining = pin["candidate"]["bytes"] + 1
                while remaining and (chunk := inp.read(min(CHUNK, remaining))):
                    out.write(chunk)
                    remaining -= len(chunk)
        _verify_archive(archive, pin)
        files, directories = _payload(archive, stage)
        (stage / ".provenance.json").write_text(
            json.dumps(
                {"pin": pin, "files": files, "directories": directories}, sort_keys=True
            ),
            "utf-8",
        )
        _check(stage, pin)
        _publish(stage, dest)
        return dest
    finally:
        try:
            if stage_identity is not None:
                _cleanup(stage, token, stage_identity)
        finally:
            _cleanup_lock(lock, token, lock_identity, lock_marked)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError(message)


def main(argv=None):
    try:
        parser = _Parser(description=__doc__)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--import-local", type=Path)
        group.add_argument("--download", action="store_true")
        group.add_argument("--check", action="store_true")
        parser.add_argument("--root", type=Path)
        args = parser.parse_args(argv)
        dest = acquire(
            args.import_local, root=args.root, download=args.download, check=args.check
        )
        print(f"FFmpeg Linux verificado: {dest.relative_to(ROOT)}")
        return 0
    except (
        InputError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        tarfile.TarError,
        lzma.LZMAError,
        KeyboardInterrupt,
    ) as exc:
        print(
            f"Preparación rechazada: {type(exc).__name__}: {str(exc)[:240]}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
