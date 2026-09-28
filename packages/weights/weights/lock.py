"""Carga y validación mínima de `models.lock.json` / `tools.lock.json`
(ADR-0006 §6-7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LockError(ValueError):
    pass


def load_lock(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise LockError(f"lock no encontrado: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LockError(f"lock con JSON inválido: {p}: {exc}") from exc
    if "schema_version" not in data:
        raise LockError(f"lock sin schema_version: {p}")
    return data
