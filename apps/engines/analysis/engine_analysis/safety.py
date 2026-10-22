"""Recursos estrictos: SHA-256 y formatos seguros, sin fallback remoto."""

import hashlib
from pathlib import Path

from engine_common import EngineError

from .descriptor import read_lock

LOADER_SUFFIXES = {
    ".json",
    ".txt",
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
    ".ckpt",
    ".py",
}


def verify_model(root, model_id):
    root = Path(root).resolve()
    try:
        entry = read_lock(root)[model_id]
        directory = root / model_id
        files = entry.get("files", [entry.get("file")])
        allowed, weights = set(), []
        for item in files:
            safe = item.get("converted", item)
            filename = safe.get("dest", item["path"])
            path = directory / filename
            if (
                not path.resolve().is_relative_to(root)
                or path.is_symlink()
                or not path.is_file()
            ):
                raise ValueError("Recurso ausente o enlazado")
            allowed.add(path.resolve())
            if path.stat().st_size != safe["bytes"]:
                raise ValueError("Tamaño incorrecto")
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != safe["sha256"]:
                    raise ValueError("SHA incorrecto")
            if item["format"] == "safetensors" or "converted" in item:
                if path.suffix != ".safetensors":
                    raise ValueError("Formato no seguro")
                weights.append(path)
        for path in directory.rglob("*"):
            if path.suffix in LOADER_SUFFIXES and path.resolve() not in allowed:
                raise ValueError("Recurso no fijado")
        if not weights:
            raise ValueError("Sin pesos seguros")
        return directory, weights
    except (KeyError, OSError, ValueError, TypeError):
        raise EngineError(
            "WEIGHTS_MISMATCH", "Pesos o recursos distintos del lock"
        ) from None
