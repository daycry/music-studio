#!/usr/bin/env python
"""Descarga reproducible y segura de modelos (ADR-0006, docs/arquitectura/modelos.md).

Lee `models/models.lock.json`: cada fichero LFS/normal se descarga y se
verifica por SHA-256; los pickle se convierten una vez con
`packages/weights/weights/convert.py` y el original se borra (solo queda el
`.safetensors`); los `.py` de `trust_remote_code` se verifican igual que un
peso. Todo queda bajo `HF_HOME=models/.hf-cache` (scripts/env.ps1|.sh) y cada
fichero final lleva su sello `.verified` (ADR-0006 §7). Idempotente: si el
fichero de destino ya existe y verifica, no se vuelve a descargar.

Uso:
    uv run scripts/fetch_models.py --model ace-step-1.5        # descarga + convierte + verifica
    uv run scripts/fetch_models.py --model ace-step-1.5 --check  # solo verifica lo ya en disco
    uv run scripts/fetch_models.py --model qwen3-asr-1.7b
    uv run scripts/fetch_models.py --model ace-step-1.5 --include-optional  # también XL-turbo (~20 GB)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages" / "weights"))

os.environ.setdefault("HF_HOME", str(ROOT / "models" / ".hf-cache"))

from huggingface_hub import hf_hub_download
from weights.convert import convert_torch_pickle_zip
from weights.lock import load_lock
from weights.seal import write_seal
from weights.verify import verify_file


def _download_hf(repo: str, revision: str, repo_path: str) -> Path:
    p = hf_hub_download(repo, repo_path, revision=revision, cache_dir=os.environ["HF_HOME"])
    return Path(p)


def _download_url(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"  Descargando {url}")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def _process_file(
    *,
    fetch_src: callable,
    dest_dir: Path,
    file_entry: dict,
    check_only: bool,
    force: bool,
) -> tuple[bool, str]:
    """Descarga (o verifica) un fichero del lock. Devuelve (ok, mensaje)."""
    fmt = file_entry.get("format", "metadata")
    rel_path = file_entry["path"]

    if fmt == "pickle":
        conv = file_entry["converted"]
        final_dest = dest_dir / conv["dest"]
        if check_only:
            if conv["sha256"] is None:
                return False, f"{rel_path}: lock sin hash convertido (rellénalo tras descargar)"
            r = verify_file(final_dest, conv["sha256"], conv["bytes"])
            return r.ok, f"{conv['dest']}: {'OK' if r.ok else r.reason}"

        if not force and final_dest.exists() and conv["sha256"]:
            r = verify_file(final_dest, conv["sha256"], conv["bytes"])
            if r.ok:
                return True, f"{conv['dest']}: OK (ya presente)"

        src = fetch_src(rel_path)
        src_result = verify_file(src, file_entry["sha256"], file_entry["bytes"])
        if not src_result.ok:
            return False, f"{rel_path}: original no verifica: {src_result.reason}"

        result = convert_torch_pickle_zip(src, final_dest)
        if result.sha256_original != file_entry["sha256"]:
            return False, f"{rel_path}: hash original cambió tras convertir (inesperado)"

        # Guarda los hashes reales del convertido en el lock in-place (se
        # persiste en main()). El original se borra: solo queda el safetensors
        # (criterio de aceptación de T-02).
        conv["sha256"] = result.sha256_converted
        conv["bytes"] = result.bytes_converted
        write_seal(final_dest, result.sha256_converted)
        try:
            src.unlink()
        except OSError:
            pass
        return True, f"{conv['dest']}: OK (convertido, {result.tensor_count} tensores)"

    # metadata / safetensors / remote_code: copia directa verificada
    final_dest = dest_dir / rel_path
    if check_only:
        r = verify_file(final_dest, file_entry["sha256"], file_entry["bytes"])
        return r.ok, f"{rel_path}: {'OK' if r.ok else r.reason}"

    if not force and final_dest.exists():
        r = verify_file(final_dest, file_entry["sha256"], file_entry["bytes"])
        if r.ok:
            return True, f"{rel_path}: OK (ya presente)"

    src = fetch_src(rel_path)
    r = verify_file(src, file_entry["sha256"], file_entry["bytes"])
    if not r.ok:
        return False, f"{rel_path}: {r.reason}"

    final_dest.parent.mkdir(parents=True, exist_ok=True)
    if final_dest.resolve() != src.resolve():
        # move, no copy: el fichero ya vive verificado en el caché de HF y no
        # hace falta guardarlo dos veces (ADR-0005, todo dentro de la carpeta,
        # sin duplicar gigas). Si el move falla (discos distintos, fichero
        # bloqueado), se cae a copiar+borrar.
        if final_dest.exists():
            final_dest.unlink()
        try:
            os.replace(src, final_dest)
        except OSError:
            final_dest.write_bytes(src.read_bytes())
            try:
                src.unlink()
            except OSError:
                pass
    write_seal(final_dest, file_entry["sha256"])
    return True, f"{rel_path}: OK"


def _run_component(comp: dict, dest_root: Path, check_only: bool, force: bool, include_optional: bool) -> list[tuple[bool, str]]:
    if comp.get("optional") and not include_optional:
        return [(True, f"{comp['id']}: opcional, omitido (usa --include-optional para bajarlo)")]

    dest_dir = dest_root / comp["dest_subdir"]

    def fetch_src(rel_path: str) -> Path:
        repo_path = f"{comp['repo_subdir']}/{rel_path}" if comp["repo_subdir"] else rel_path
        return _download_hf(comp["repo"], comp["revision"], repo_path)

    results = []
    for f in comp["files"]:
        ok, msg = _process_file(
            fetch_src=fetch_src, dest_dir=dest_dir, file_entry=f, check_only=check_only, force=force
        )
        results.append((ok, f"{comp['id']}/{msg}"))
    return results


def _run_hf_repo_model(model: dict, check_only: bool, force: bool) -> list[tuple[bool, str]]:
    dest_dir = ROOT / model["dest"]

    def fetch_src(rel_path: str) -> Path:
        return _download_hf(model["repo"], model["revision"], rel_path)

    results = []
    for f in model["files"]:
        ok, msg = _process_file(
            fetch_src=fetch_src, dest_dir=dest_dir, file_entry=f, check_only=check_only, force=force
        )
        results.append((ok, msg))
    return results


def _run_url_model(model: dict, check_only: bool, force: bool) -> list[tuple[bool, str]]:
    dest_dir = ROOT / model["dest"]
    file_entry = model["file"]

    def fetch_src(rel_path: str) -> Path:
        cache = ROOT / ".cache" / "fetch" / rel_path
        if not cache.exists():
            _download_url(model["url"], cache)
        return cache

    ok, msg = _process_file(
        fetch_src=fetch_src, dest_dir=dest_dir, file_entry=file_entry, check_only=check_only, force=force
    )
    return [(ok, msg)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="clave en models.lock.json['models']")
    parser.add_argument("--check", action="store_true", help="solo verificar, no descargar")
    parser.add_argument("--force", action="store_true", help="volver a descargar aunque ya verifique")
    parser.add_argument("--include-optional", action="store_true", help="incluir componentes optional:true (p.ej. XL-turbo)")
    args = parser.parse_args()

    lock_path = ROOT / "models" / "models.lock.json"
    lock = load_lock(lock_path)
    if args.model not in lock["models"]:
        print(f"ERROR: '{args.model}' no está en {lock_path}")
        return 1
    model = lock["models"][args.model]

    print(f"HF_HOME={os.environ['HF_HOME']}")
    results: list[tuple[bool, str]] = []
    if model["kind"] == "ace-step-checkpoints":
        dest_root = ROOT / model["dest"]
        for comp in model["components"]:
            results.extend(
                _run_component(comp, dest_root, args.check, args.force, args.include_optional)
            )
    elif model["kind"] == "hf-repo":
        results.extend(_run_hf_repo_model(model, args.check, args.force))
    elif model["kind"] == "url":
        results.extend(_run_url_model(model, args.check, args.force))
    else:
        print(f"ERROR: kind desconocido: {model['kind']}")
        return 1

    for ok, msg in results:
        print(("  OK  " if ok else "  FAIL") + " " + msg)

    if not args.check:
        lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")

    failed = [m for ok, m in results if not ok]
    if failed:
        print(f"\n{len(failed)} fichero(s) fallaron")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
