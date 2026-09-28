"""Hash y utilidades de fichero (ADR-0006 §7)."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 4 * 1024 * 1024


def sha256_file(path: str | Path, chunk_size: int = _CHUNK) -> str:
    """SHA-256 completo de un fichero, en streaming (no carga todo en memoria)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
