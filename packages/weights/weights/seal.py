"""Sello `.verified` (ADR-0006 §7): tamaño + mtime + hash, para no recalcular el
SHA-256 completo en cada carga. Si el sello no coincide con el fichero (tamaño o
mtime distintos), se recalcula el hash completo y se compara contra el lock.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .hashing import sha256_file

_SEAL_SUFFIX = ".verified"


@dataclass(frozen=True)
class Seal:
    size: int
    mtime_ns: int
    sha256: str


def seal_path(file_path: str | Path) -> Path:
    return Path(str(file_path) + _SEAL_SUFFIX)


def read_seal(file_path: str | Path) -> Seal | None:
    p = seal_path(file_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return Seal(size=data["size"], mtime_ns=data["mtime_ns"], sha256=data["sha256"])
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def write_seal(file_path: str | Path, sha256: str) -> Seal:
    p = Path(file_path)
    st = p.stat()
    seal = Seal(size=st.st_size, mtime_ns=st.st_mtime_ns, sha256=sha256)
    seal_path(file_path).write_text(
        json.dumps({"size": seal.size, "mtime_ns": seal.mtime_ns, "sha256": seal.sha256}),
        encoding="utf-8",
    )
    return seal


def verified_sha256(file_path: str | Path) -> str:
    """Devuelve el SHA-256 del fichero, usando el sello si tamaño+mtime coinciden
    (evita recalcular el hash completo). Si no hay sello o no coincide, recalcula
    y reescribe el sello.
    """
    p = Path(file_path)
    st = p.stat()
    seal = read_seal(p)
    if seal is not None and seal.size == st.st_size and seal.mtime_ns == st.st_mtime_ns:
        return seal.sha256
    digest = sha256_file(p)
    write_seal(p, digest)
    return digest
