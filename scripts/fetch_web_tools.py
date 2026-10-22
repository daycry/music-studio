"""Node/pnpm portátiles fijados: extracción segura y sondas Windows (ADR-0048)."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
import time
import urllib.request
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ".studio-web-origin.json"
PINS = {
    "node": {
        "version": "22.23.2",
        "url": "https://nodejs.org/dist/v22.23.2/node-v22.23.2-win-x64.zip",
        "asset": "node-v22.23.2-win-x64.zip",
        "sha256": "1177b4137ba5adaa56354ae40f1080c7450e8ae09cecb47da459d1c52ac99f97",
        "bytes": 35683585,
        "dest": "tools/node/22.23.2/win-x64",
        "prefix": "node-v22.23.2-win-x64",
        "kind": "zip",
        "license": "MIT + third-party notices",
    },
    "pnpm": {
        "version": "9.12.0",
        "url": "https://registry.npmjs.org/pnpm/-/pnpm-9.12.0.tgz",
        "asset": "pnpm-9.12.0.tgz",
        "sha256": "a61b67ff6cc97af864564f4442556c22a04f2e5a7714fbee76a1011361d9b726",
        "bytes": 4542556,
        "shasum": "87cb0f58b64bfb9103677375d7e99e12a3ddbf23",
        "integrity": "sha512-Sr9yUITXvLr71yi/x77mHy95H5d/2HVCs1edyyNQTRcNRjN5ReTGZIXNEtWIoMDlcO2cR358zdhQfPBfP5Lqyg==",
        "dest": "tools/pnpm/9.12.0",
        "prefix": "package",
        "kind": "tar",
        "license": "MIT + third-party notices",
    },
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(path: Path, root: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    boundary = Path(os.path.abspath(root))
    if not absolute.is_relative_to(boundary):
        raise ValueError("Ruta fuera del proyecto")
    for candidate in (absolute, *absolute.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Enlace/reparse prohibido: {candidate}")
    if not absolute.resolve().is_relative_to(boundary.resolve()):
        raise ValueError("Ruta resuelta fuera del proyecto")
    return absolute


def verify_archive(path: Path, pin: dict) -> None:
    if path.stat().st_size != pin["bytes"] or digest(path) != pin["sha256"]:
        raise ValueError("Archivo no coincide en bytes/SHA-256")
    for field, algorithm in (("shasum", "sha1"), ("integrity", "sha512")):
        if field not in pin:
            continue
        with path.open("rb") as stream:
            hashed = hashlib.file_digest(stream, algorithm)
        actual = (
            hashed.hexdigest()
            if field == "shasum"
            else "sha512-" + base64.b64encode(hashed.digest()).decode("ascii")
        )
        if actual != pin[field]:
            raise ValueError(f"Archivo no coincide en {field}")


def member_path(name: str, prefix: str) -> str:
    parts = name.rstrip("/").split("/")
    if len(name) > 240 or any(len(part) > 255 for part in parts):
        raise ValueError("Ruta excede longitud permitida")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{family}{i}" for family in ("COM", "LPT") for i in range(1, 10)
    }
    if any(c in name for c in ("\\", ":", "\x00")) or name.startswith("/"):
        raise ValueError("Ruta de archivo insegura")
    for part in parts:
        if (
            part in ("", ".", "..")
            or part.endswith((".", " "))
            or any(ord(c) < 32 or c in '<>"|?*' for c in part)
            or part.split(".")[0].upper() in reserved
        ):
            raise ValueError("Componente inseguro")
    if parts[0] != prefix:
        raise ValueError("Prefijo incorrecto")
    relative = "/".join(parts[1:])
    if relative == MANIFEST:
        raise ValueError("Manifiesto reservado")
    return relative


def archive_members(archive, kind):
    if kind == "zip":
        for item in archive.infolist():
            mode = item.external_attr >> 16
            if (
                item.external_attr & 0x400
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                or (stat.S_ISDIR(mode) and not item.is_dir())
            ):
                raise ValueError("Tipo ZIP/enlace/reparse prohibido")
            yield (
                item,
                item.filename,
                item.is_dir(),
                item.file_size,
                item.external_attr >> 16,
            )
    else:
        for item in archive:
            if not (item.isfile() or item.isdir()) or item.sparse is not None:
                raise ValueError("Tipo TAR/enlace/sparse prohibido")
            yield item, item.name, item.isdir(), item.size, item.mode


def open_archive(path, kind):
    if kind == "zip":
        return zipfile.ZipFile(path)
    if kind == "tar":
        return tarfile.open(path, "r:gz")
    raise ValueError("Formato no autorizado")


def read_member(archive, item, kind):
    return archive.open(item) if kind == "zip" else archive.extractfile(item)


def inspect_archive(
    path: Path,
    kind: str,
    prefix: str,
    *,
    files=10000,
    file_bytes=150000000,
    total_bytes=300000000,
    ratio=500,
) -> dict:
    result, entries = {}, {}
    total = 0
    with open_archive(path, kind) as stream:
        for count, (item, name, directory, size, mode) in enumerate(
            archive_members(stream, kind), 1
        ):
            if count > files or size < 0 or size > file_bytes:
                raise ValueError("Límite de miembros/tamaño excedido")
            total += size
            if total > total_bytes or total > max(1, path.stat().st_size) * ratio:
                raise ValueError("Límite de descompresión excedido")
            relative = member_path(name, prefix)
            key = relative.casefold()
            if key in entries:
                raise ValueError("Miembro duplicado o colisión")
            entries[key] = directory
            if directory:
                if size:
                    raise ValueError("Directorio con datos")
                continue
            if not relative:
                raise ValueError("Raíz debe ser directorio")
            if kind == "zip" and size > max(1, item.compress_size) * ratio:
                raise ValueError("Ratio ZIP excesivo")
            hashed = hashlib.sha256()
            actual = 0
            with read_member(stream, item, kind) as payload:
                while chunk := payload.read(1024 * 1024):
                    actual += len(chunk)
                    if actual > size or actual > file_bytes:
                        raise ValueError("Tamaño real excedido")
                    hashed.update(chunk)
            if actual != size:
                raise ValueError("Tamaño real incorrecto")
            result[relative] = {
                "bytes": actual,
                "sha256": hashed.hexdigest(),
                "executable": bool(mode & 0o111),
            }
    for key in entries:
        for parent in Path(key).parents:
            if parent.as_posix() in entries and not entries[parent.as_posix()]:
                raise ValueError("Archivo usado como directorio")
    return result


def verify_identity(dest: Path, name: str) -> None:
    if name == "pnpm":
        package = json.loads((dest / "package.json").read_text(encoding="utf-8"))
        if (
            package.get("name") != name
            or package.get("version") != PINS[name]["version"]
        ):
            raise ValueError("Identidad/version pnpm incorrecta")
        if not all(
            (dest / relative).is_file()
            for relative in ("bin/pnpm.cjs", "dist/pnpm.cjs")
        ):
            raise ValueError("Runtime pnpm incompleto")
    elif name != "node" or not (dest / "node.exe").is_file():
        raise ValueError("Runtime Node Windows incompleto")


def verify_project(root: Path) -> None:
    path = safe_path(root / "package.json", root)
    if (
        json.loads(path.read_text(encoding="utf-8")).get("packageManager")
        != "pnpm@9.12.0"
    ):
        raise ValueError("packageManager debe fijar pnpm@9.12.0")


def origin(pin, manifest):
    return {"source": pin, "files": manifest}


def check_disk(dest: Path, manifest: dict, pin: dict) -> None:
    safe_path(dest, dest)
    if not dest.is_dir():
        raise ValueError("Falta herramienta")
    directories = {
        parent.as_posix()
        for name in manifest
        for parent in Path(name).parents
        if parent != Path(".")
    }
    found = {}
    for path in dest.rglob("*"):
        safe_path(path, dest)
        name = path.relative_to(dest).as_posix()
        if path.is_dir():
            if name not in directories:
                raise ValueError("Directorio extra no verificado")
        elif name != MANIFEST:
            if not path.is_file() or path.stat().st_nlink != 1:
                raise ValueError("Archivo especial/hardlink prohibido")
            if name not in manifest:
                raise ValueError("Archivo extra no verificado")
            found[name] = {
                "bytes": path.stat().st_size,
                "sha256": digest(path),
                "executable": manifest[name]["executable"],
            }
    if found != manifest:
        raise ValueError("Disco alterado/incompleto; conservar destino")
    if pin:
        metadata = dest / MANIFEST
        if (
            not metadata.is_file()
            or metadata.stat().st_nlink != 1
            or json.loads(metadata.read_text(encoding="utf-8")) != origin(pin, manifest)
        ):
            raise ValueError("Procedencia no acreditada; no sobrescribir destino")


def extract(root: Path, path: Path, name: str, pin: dict, manifest: dict) -> Path:
    safe_path(path, root)
    verify_archive(path, pin)
    if inspect_archive(path, pin["kind"], pin["prefix"]) != manifest:
        raise ValueError("Manifiesto no coincide con archivo verificado")
    dest = safe_path(root / pin["dest"], root)
    if dest.exists():
        check_disk(dest, manifest, pin)
        verify_identity(dest, name)
        return dest
    parent = safe_path(root / ".cache/fetch", root)
    parent.mkdir(parents=True, exist_ok=True)
    stage = safe_path(parent / ("web-stage-" + uuid.uuid4().hex), root)
    stage.mkdir()
    try:
        with open_archive(path, pin["kind"]) as stream:
            for item, member, directory, size, mode in archive_members(
                stream, pin["kind"]
            ):
                relative = member_path(member, pin["prefix"])
                if not relative or directory:
                    continue
                target = safe_path(stage / relative, stage)
                target.parent.mkdir(parents=True, exist_ok=True)
                copied = 0
                with (
                    read_member(stream, item, pin["kind"]) as payload,
                    target.open("xb") as output,
                ):
                    while chunk := payload.read(1024 * 1024):
                        copied += len(chunk)
                        if copied > manifest[relative]["bytes"]:
                            raise ValueError("Archivo cambiado durante extracción")
                        output.write(chunk)
                if os.name != "nt":
                    target.chmod(0o755 if mode & 0o111 else 0o644)
        check_disk(stage, manifest, {})
        verify_identity(stage, name)
        (stage / MANIFEST).write_text(
            json.dumps(origin(pin, manifest), sort_keys=True, indent=2),
            encoding="utf-8",
        )
        check_disk(stage, manifest, pin)
        verify_archive(path, pin)
        safe_path(dest, root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(dest)
        return dest
    finally:
        if stage.exists():
            safe_path(stage, root)
            for entry in stage.rglob("*"):
                safe_path(entry, stage)
            shutil.rmtree(stage)


def build_environment(root: Path, inherited=None) -> dict:
    inherited = os.environ if inherited is None else inherited
    env = {
        key: value
        for key, value in inherited.items()
        if key.upper() in {"SYSTEMROOT", "COMSPEC", "WINDIR", "SYSTEMDRIVE"}
    }
    base = safe_path(root / ".cache/dev-cycle/m1/t08-web-portable-tools/runtime", root)
    locations = {
        "PNPM_HOME": "pnpm-home",
        "npm_config_store_dir": "store",
        "npm_config_cache": "cache",
        "npm_config_cache_dir": "cache",
        "npm_config_state_dir": "state",
        "npm_config_global_dir": "global",
        "XDG_CACHE_HOME": "xdg-cache",
        "XDG_CONFIG_HOME": "xdg-config",
        "XDG_DATA_HOME": "xdg-data",
        "XDG_STATE_HOME": "xdg-state",
        "TEMP": "temp",
        "TMP": "temp",
    }
    for key, relative in locations.items():
        path = safe_path(base / relative, root)
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    settings = {
        "manage-package-manager-versions": "false",
        "package-manager-strict": "true",
        "package-manager-strict-version": "true",
        "engine-strict": "true",
    }
    config = "".join(f"{key}={value}\n" for key, value in settings.items())
    for key, filename in (
        ("npm_config_userconfig", "user.npmrc"),
        ("npm_config_globalconfig", "global.npmrc"),
    ):
        path = safe_path(base / filename, root)
        if not path.exists():
            with path.open("x", encoding="utf-8") as stream:
                stream.write(config)
        elif path.read_text(encoding="utf-8") != config:
            raise ValueError("Configuración privada alterada; no sobrescribir")
        env[key] = str(path)
    env.update(
        {
            "npm_config_" + key.replace("-", "_"): value
            for key, value in settings.items()
        }
    )
    env["PATH"] = str(safe_path(root / PINS["node"]["dest"], root))
    return env


def download(root: Path, pin: dict) -> Path:
    directory = safe_path(root / ".cache/fetch", root)
    directory.mkdir(parents=True, exist_ok=True)
    path = safe_path(
        directory / ("web-archive-" + uuid.uuid4().hex + "-" + pin["asset"]), root
    )
    started = time.monotonic()
    received = 0
    try:
        with (
            urllib.request.urlopen(pin["url"], timeout=30) as response,
            path.open("xb") as output,
        ):
            while chunk := response.read(1024 * 1024):
                received += len(chunk)
                if received > pin["bytes"] or time.monotonic() - started > 180:
                    raise ValueError("Descarga excede tamaño/plazo")
                output.write(chunk)
        verify_archive(path, pin)
        return path
    except Exception:
        if path.exists():
            safe_path(path, root).unlink()
        raise


def prepare(root: Path, archive_dir: Path | None, check: bool) -> dict:
    verify_project(root)
    lock = json.loads(
        safe_path(root / "tools/tools.lock.json", root).read_text(encoding="utf-8")
    )
    if lock.get("schema_version") != 1:
        raise ValueError("Schema de tools.lock incorrecto")
    if archive_dir is not None:
        archive_dir = safe_path(archive_dir, root)
    for name, pin in PINS.items():
        if lock["tools"].get(name) != pin:
            raise ValueError("Lock portable no coincide con pins incorporados")
    result = {}
    for name, pin in PINS.items():
        path = safe_path(
            archive_dir / pin["asset"]
            if archive_dir is not None
            else root / ".cache/fetch" / ("web-pinned-" + pin["asset"]),
            root,
        )
        if not path.is_file():
            if check or archive_dir is not None:
                raise ValueError(f"Falta archivo oficial verificado: {path}")
            downloaded = download(root, pin)
            safe_path(path, root)
            if path.exists():
                raise ValueError(
                    "Caché aparecida simultáneamente; conservar ambos archivos"
                )
            downloaded.rename(path)
        verify_archive(path, pin)
        manifest = inspect_archive(path, pin["kind"], pin["prefix"])
        dest = safe_path(root / pin["dest"], root)
        if check:
            check_disk(dest, manifest, pin)
            verify_identity(dest, name)
        else:
            dest = extract(root, path, name, pin, manifest)
        result[name] = {"dest": dest, "archive": path, "manifest": manifest}
    return result


def probe(root: Path, prepared: dict) -> list:
    if os.name != "nt":
        raise ValueError("Solo runtime Windows certificado por estos pins")
    verify_project(root)
    environment = build_environment(root)
    node = safe_path(prepared["node"]["dest"] / "node.exe", root)
    pnpm = safe_path(prepared["pnpm"]["dest"] / "bin/pnpm.cjs", root)
    records = []
    for argv, expected in (
        ([str(node), "--version"], "v22.23.2"),
        ([str(node), str(pnpm), "--version"], "9.12.0"),
    ):
        for name, tool in prepared.items():
            verify_archive(tool["archive"], PINS[name])
            fresh = inspect_archive(
                tool["archive"], PINS[name]["kind"], PINS[name]["prefix"]
            )
            check_disk(tool["dest"], fresh, PINS[name])
            verify_identity(tool["dest"], name)
        started = datetime.now(UTC).isoformat()
        out = subprocess.run(
            argv,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
        )
        record = {
            "utc": started,
            "cwd": str(root),
            "argv": argv,
            "exit": out.returncode,
            "stdout": out.stdout,
            "stderr": out.stderr,
            "executable_sha256": digest(node),
            "pnpm_cjs_sha256": digest(pnpm),
            "configured_paths": {
                key: value
                for key, value in environment.items()
                if key != "PATH" and str(root) in value
            },
        }
        records.append(record)
        if out.returncode or out.stdout.strip() != expected:
            raise ValueError("Sonda no lista: " + json.dumps(record))
    for name, tool in prepared.items():
        verify_archive(tool["archive"], PINS[name])
        check_disk(
            tool["dest"],
            inspect_archive(tool["archive"], PINS[name]["kind"], PINS[name]["prefix"]),
            PINS[name],
        )
    return records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Comprobar sin descargar ni extraer"
    )
    parser.add_argument(
        "--archive-dir", type=Path, help="Archivos oficiales dentro del proyecto"
    )
    args = parser.parse_args(argv)
    try:
        prepared = prepare(ROOT, args.archive_dir, args.check)
        print(json.dumps({"ready": True, "probes": probe(ROOT, prepared)}, indent=2))
        return 0
    except (
        ValueError,
        OSError,
        KeyError,
        tarfile.TarError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as exc:
        print(f"NO LISTO: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
