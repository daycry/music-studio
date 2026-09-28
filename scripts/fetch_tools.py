#!/usr/bin/env python
"""Descarga y verifica herramientas fijadas en `tools/tools.lock.json`
(hoy solo ffmpeg BtbN `win64-lgpl`, entorno.md §2). Idempotente: si el zip y la
extracción ya están verificados, no vuelve a descargar salvo `--force`.

Uso:
    uv run scripts/fetch_tools.py                 # descarga + verifica + extrae
    uv run scripts/fetch_tools.py --check          # solo verifica lo ya extraído
    uv run scripts/fetch_tools.py --force          # vuelve a descargar aunque ya esté
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages" / "weights"))

from weights.hashing import sha256_file
from weights.lock import load_lock
from weights.seal import write_seal
from weights.verify import verify_file

REQUIRED_BUILDCONF = ("--enable-libmp3lame", "--enable-libsoxr", "--enable-libopus")
FORBIDDEN_BUILDCONF = ("--enable-gpl", "--enable-nonfree")


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Descargando {url} -> {dest}")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def _find_ffmpeg_exe(extract_dir: Path) -> Path | None:
    for p in extract_dir.rglob("ffmpeg.exe"):
        return p
    for p in extract_dir.rglob("ffmpeg"):
        if p.is_file():
            return p
    return None


def _check_buildconf(ffmpeg_exe: Path) -> tuple[bool, str]:
    try:
        out = subprocess.run(
            [str(ffmpeg_exe), "-buildconf"], capture_output=True, text=True, timeout=30, check=False
        )
    except OSError as exc:
        return False, f"no se pudo ejecutar {ffmpeg_exe}: {exc}"
    conf = out.stdout + out.stderr
    missing = [flag for flag in REQUIRED_BUILDCONF if flag not in conf]
    present_forbidden = [flag for flag in FORBIDDEN_BUILDCONF if flag in conf]
    if missing:
        return False, f"faltan flags obligatorios en -buildconf: {missing}"
    if present_forbidden:
        return False, f"-buildconf incluye flags prohibidos: {present_forbidden}"
    return True, conf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="solo verificar, no descargar")
    parser.add_argument("--force", action="store_true", help="volver a descargar aunque ya esté")
    args = parser.parse_args()

    lock_path = ROOT / "tools" / "tools.lock.json"
    lock = load_lock(lock_path)
    ffmpeg = lock["tools"]["ffmpeg"]

    dest_dir = ROOT / ffmpeg["dest"]
    zip_dest = ROOT / ".cache" / "fetch" / Path(ffmpeg["url"]).name

    if args.check:
        exe = _find_ffmpeg_exe(dest_dir)
        if exe is None:
            print(f"FALTA: no hay ffmpeg extraído en {dest_dir}")
            return 1
        ok, detail = _check_buildconf(exe)
        if not ok:
            print(f"FALLO buildconf: {detail}")
            return 1
        print("ffmpeg win64-lgpl OK")
        return 0

    if not args.force and zip_dest.exists():
        result = verify_file(zip_dest, ffmpeg["sha256"], ffmpeg["bytes"])
        if not result.ok:
            print(f"zip existente no verifica ({result.reason}), se vuelve a descargar")
            _download(ffmpeg["url"], zip_dest)
    else:
        _download(ffmpeg["url"], zip_dest)

    digest = sha256_file(zip_dest)
    if digest != ffmpeg["sha256"]:
        print(f"ERROR: sha256 del zip descargado no coincide con el lock: {digest} != {ffmpeg['sha256']}")
        return 1
    write_seal(zip_dest, digest)

    if dest_dir.exists() and not args.force:
        exe = _find_ffmpeg_exe(dest_dir)
    else:
        exe = None

    if exe is None:
        print(f"Extrayendo en {dest_dir}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_dest) as zf:
            zf.extractall(dest_dir)
        exe = _find_ffmpeg_exe(dest_dir)
        if exe is None:
            print("ERROR: no se encontró ffmpeg.exe tras extraer")
            return 1

    ok, detail = _check_buildconf(exe)
    if not ok:
        print(f"ERROR: {detail}")
        return 1

    print(f"ffmpeg win64-lgpl OK ({exe})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
