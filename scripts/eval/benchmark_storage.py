"""Preparación CPU en guest propio: mismo layout, lock y bytes seguros."""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

from benchmark_plan import ROOT, file_hash

COPY_POLICY = "monotonic_bounded_sync_v2"
COPY_RATE_BYTES_PER_S = 128 * 1024**2
COPY_CHUNK_BYTES = 8 * 1024**2


def storage_capacity(destination, required_bytes):
    existing = Path(destination)
    while not existing.exists():
        existing = existing.parent
    free = shutil.disk_usage(existing).free
    if free < required_bytes * 1.05 + 512 * 1024**2:
        raise ValueError("insufficient_container_storage")
    return {
        "free_bytes_before": free,
        "required_bytes": required_bytes,
        "margin_bytes": 512 * 1024**2,
    }


def selected_components(source, names):
    lock = json.loads((source / "models.lock.json").read_text(encoding="utf-8"))
    lookup = {c["id"]: c for c in lock["models"]["ace-step-1.5"]["components"]}
    try:
        return [lookup[name] for name in names]
    except KeyError:
        raise ValueError("missing_weights_component") from None


def verify_selected(source, components):
    records = []
    checkpoint_root = source / "ace-step-1.5/checkpoints"
    for component in components:
        directory = checkpoint_root / component["dest_subdir"]
        allowed = set()
        for file in component["files"]:
            if file["format"] == "pickle" and "converted" not in file:
                raise ValueError("unsafe_pickle")
            if (
                file["path"].endswith((".pt", ".bin", ".pth", ".ckpt"))
                and file["format"] != "pickle"
            ):
                raise ValueError("unsafe_pickle_metadata")
            safe = file.get("converted", file)
            relative = Path(component["dest_subdir"]) / safe.get("dest", file["path"])
            path = checkpoint_root / relative
            if (
                path.is_symlink()
                or not path.resolve().is_relative_to(checkpoint_root.resolve())
                or not path.is_file()
            ):
                raise ValueError("missing_weights_or_unsafe_path")
            if (
                path.stat().st_size != safe["bytes"]
                or file_hash(path) != safe["sha256"]
            ):
                raise ValueError("weights_mismatch")
            allowed.add(path.relative_to(directory).as_posix())
            if file["format"] == "pickle":
                allowed.add(file["path"])
            records.append(
                {
                    "relative": f"ace-step-1.5/checkpoints/{relative.as_posix()}",
                    "bytes": safe["bytes"],
                    "sha256": safe["sha256"],
                }
            )
        for path in directory.rglob("*"):
            if (
                path.is_file()
                and path.suffix
                in {
                    ".py",
                    ".bin",
                    ".pt",
                    ".pth",
                    ".ckpt",
                    ".safetensors",
                    ".gguf",
                    ".onnx",
                }
                and path.relative_to(directory).as_posix() not in allowed
            ):
                raise ValueError("unexpected_weights_or_code")
    return records


def prepare_storage(source, destination, names):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    started = time.perf_counter_ns()
    components = selected_components(source, names)
    records = verify_selected(source, components)
    verified = time.perf_counter_ns()
    source_lock = file_hash(source / "models.lock.json")
    copying = destination != source
    capacity = None
    if copying:
        if not destination.is_relative_to(ROOT / ".cache"):
            raise ValueError("copy_outside_project_cache")
        capacity = storage_capacity(
            destination,
            sum(r["bytes"] for r in records)
            + (source / "models.lock.json").stat().st_size,
        )
        if destination.exists():
            raise ValueError("copy_destination_exists")
        destination.mkdir(parents=True)
        copy_deadline_ns = time.monotonic_ns()
        for relative in ["models.lock.json", *(r["relative"] for r in records)]:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with (source / relative).open("rb") as reader, target.open("xb") as writer:
                while chunk := reader.read(COPY_CHUNK_BYTES):
                    # Compartido entre archivos, sin crédito por pausas previas.
                    copy_deadline_ns = max(copy_deadline_ns, time.monotonic_ns())
                    writer.write(chunk)
                    writer.flush()
                    os.fsync(writer.fileno())
                    copy_deadline_ns += (
                        len(chunk) * 10**9 + COPY_RATE_BYTES_PER_S - 1
                    ) // COPY_RATE_BYTES_PER_S
                    while (remaining_ns := copy_deadline_ns - time.monotonic_ns()) > 0:
                        time.sleep(remaining_ns / 1e9)
    copied = time.perf_counter_ns()
    actual = verify_selected(destination, selected_components(destination, names))
    if records != actual or source_lock != file_hash(destination / "models.lock.json"):
        raise ValueError("copy_mismatch")
    finished = time.perf_counter_ns()
    return {
        "version": 1,
        "storage": "container_copy" if copying else "bind",
        "resource_root": str(destination),
        "source_lock_sha256": source_lock,
        "destination_lock_sha256": file_hash(destination / "models.lock.json"),
        "files": records,
        "source_verify_s": (verified - started) / 1e9,
        "copy_s": (copied - verified) / 1e9 if copying else 0,
        "destination_verify_s": (finished - copied) / 1e9,
        "copy_bytes": sum(r["bytes"] for r in records) if copying else 0,
        "copy_policy": COPY_POLICY if copying else None,
        "copy_rate_bytes_per_s": COPY_RATE_BYTES_PER_S if copying else None,
        "copy_chunk_bytes": COPY_CHUNK_BYTES if copying else None,
        "capacity": capacity,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="/models")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--lm", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    receipt = prepare_storage(
        args.source,
        args.destination,
        [args.checkpoint, args.lm, "vae", "Qwen3-Embedding-0.6B"],
    )
    from benchmark_evidence import exclusive_json

    exclusive_json(args.receipt, receipt)
    if args.serve:
        if not Path("/.dockerenv").is_file() or os.name != "posix":
            raise ValueError("guest_container_required")
        # La preparación es CPU y root sólo del guest; el servicio pierde UID antes de CUDA.
        os.setgid(10001)
        os.setuid(10001)
        os.chdir("/studio/apps/engines/acestep")
        os.execvp(
            "uvicorn",
            [
                "uvicorn",
                "engine_acestep:create_app",
                "--factory",
                "--host",
                "0.0.0.0",
                "--port",
                "8101",
            ],
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError):
        # No trazas/rutas personales ni inputs en logs del contenedor.
        print("benchmark_storage: preparation_failed", file=sys.stderr)
        sys.exit(2)
