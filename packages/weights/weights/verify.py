"""Verificación de ficheros contra el lock (ADR-0006 §7): hash completo al
descargar, sello `.verified` (tamaño+mtime+hash) para no recalcular en cada
carga, y recálculo si el sello no cuadra.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .seal import verified_sha256


@dataclass(frozen=True)
class VerifyResult:
    path: Path
    ok: bool
    reason: str = ""


def verify_file(path: str | Path, expected_sha256: str, expected_bytes: int | None = None) -> VerifyResult:
    p = Path(path)
    if not p.exists():
        return VerifyResult(p, False, "no existe")
    if expected_bytes is not None and p.stat().st_size != expected_bytes:
        return VerifyResult(
            p, False, f"tamaño distinto: {p.stat().st_size} != {expected_bytes}"
        )
    digest = verified_sha256(p)
    if digest != expected_sha256:
        return VerifyResult(p, False, f"sha256 distinto: {digest} != {expected_sha256}")
    return VerifyResult(p, True)


def verify_remote_code(path: str | Path, expected_sha256: str) -> VerifyResult:
    """Los `.py` de `trust_remote_code` se verifican igual que un peso: si el
    hash no coincide con el lock, no se usan (ADR-0006 §5).
    """
    return verify_file(path, expected_sha256)
