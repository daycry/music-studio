"""Durable, fail-closed receipt for the project storage lifecycle.

The receipt records only a monotonic lifecycle.  It does not attach a disk,
mount a filesystem, or infer ownership from a filename; those operations stay
in the platform executor and must provide evidence before advancing a phase.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

PHASES = (
    "reserved",
    "raw_verified",
    "vhdx_verified",
    "published",
    "attached",
    "validated",
)
_OPERATION_ID = re.compile(r"[0-9A-Z]{26}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ReceiptError(ValueError):
    """Receipt missing identity, phase or evidence required for recovery."""


def _canonical_uuid(value: object) -> bool:
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _validate_evidence(phase: str, evidence: Mapping[str, object]) -> None:
    if not isinstance(evidence, Mapping):
        raise ReceiptError("evidencia invalida")
    if phase == "reserved":
        if evidence:
            raise ReceiptError("evidencia invalida para reserved")
        return
    required = {
        "raw_verified": ("raw_sha256", "raw_size", "uuid"),
        "vhdx_verified": ("vhdx_sha256", "vhdx_size"),
        "published": ("final_path", "file_id"),
        "attached": ("device", "mountpoint"),
        "validated": ("noreplace", "fs_type"),
    }[phase]
    if any(key not in evidence for key in required):
        raise ReceiptError("evidencia incompleta")
    if phase == "raw_verified":
        if not _SHA256.fullmatch(
            evidence["raw_sha256"] if isinstance(evidence["raw_sha256"], str) else ""
        ):
            raise ReceiptError("evidencia raw invalida")
        if not _positive_int(evidence["raw_size"]) or not _canonical_uuid(
            evidence["uuid"]
        ):
            raise ReceiptError("evidencia raw invalida")
    elif phase == "vhdx_verified":
        if not _SHA256.fullmatch(
            evidence["vhdx_sha256"] if isinstance(evidence["vhdx_sha256"], str) else ""
        ) or not _positive_int(evidence["vhdx_size"]):
            raise ReceiptError("evidencia vhdx invalida")
    elif phase == "published":
        if (
            not isinstance(evidence["final_path"], str)
            or not evidence["final_path"]
            or not isinstance(evidence["file_id"], str)
            or not evidence["file_id"]
        ):
            raise ReceiptError("evidencia publicada invalida")
    elif phase == "attached":
        if (
            not isinstance(evidence["device"], str)
            or not evidence["device"].startswith("/dev/")
            or not isinstance(evidence["mountpoint"], str)
            or not evidence["mountpoint"].startswith("/")
        ):
            raise ReceiptError("evidencia de montaje invalida")
    elif phase == "validated":
        if evidence["noreplace"] is not True or evidence["fs_type"] != "ext4":
            raise ReceiptError("evidencia de validacion invalida")


def _validate_history(history: object, phase: str) -> tuple[dict[str, object], ...]:
    if not isinstance(history, list) or len(history) != PHASES.index(phase) + 1:
        raise ReceiptError("historial de fases invalido")
    normalized: list[dict[str, object]] = []
    for index, item in enumerate(history):
        if not isinstance(item, dict) or item.get("phase") != PHASES[index]:
            raise ReceiptError("historial de fases invalido")
        evidence = item.get("evidence")
        if not isinstance(evidence, Mapping):
            raise ReceiptError("historial de fases invalido")
        _validate_evidence(PHASES[index], evidence)
        normalized.append({"phase": PHASES[index], "evidence": dict(evidence)})
    return tuple(normalized)


@dataclass(frozen=True)
class StorageReceipt:
    schema_version: int
    operation_id: str
    phase: str
    disk_path: str
    size_bytes: int
    history: tuple[dict[str, object], ...]

    @classmethod
    def reserve(
        cls, *, project_root: str | Path, operation_id: str, size_bytes: int
    ) -> StorageReceipt:
        if not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(
            operation_id
        ):
            raise ReceiptError("operation_id invalido")
        if not _positive_int(size_bytes):
            raise ReceiptError("size_bytes invalido")
        root = Path(project_root)
        if not root.is_absolute() or root.is_symlink():
            raise ReceiptError("raiz de proyecto invalida")
        disk_path = (root / "data" / "_storage" / "studio-data.vhdx").as_posix()
        return cls(
            1,
            operation_id,
            "reserved",
            disk_path,
            size_bytes,
            ({"phase": "reserved", "evidence": {}},),
        )

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != 1
            or self.phase not in PHASES
            or not isinstance(self.operation_id, str)
            or not _OPERATION_ID.fullmatch(self.operation_id)
        ):
            raise ReceiptError("cabecera de recibo invalida")
        if (
            not isinstance(self.disk_path, str)
            or not self.disk_path
            or not Path(self.disk_path).is_absolute()
            or not _positive_int(self.size_bytes)
        ):
            raise ReceiptError("identidad de recibo invalida")
        if not isinstance(self.history, tuple):
            raise ReceiptError("historial de recibo invalido")
        if any(
            not isinstance(item, dict)
            or set(item) != {"phase", "evidence"}
            or not isinstance(item["phase"], str)
            or not isinstance(item["evidence"], dict)
            for item in self.history
        ):
            raise ReceiptError("historial de recibo invalido")
        _validate_history(list(self.history), self.phase)

    def advance(self, phase: str, evidence: Mapping[str, object]) -> StorageReceipt:
        if self.phase == PHASES[-1]:
            raise ReceiptError("recibo terminal")
        current = PHASES.index(self.phase)
        if phase not in PHASES or PHASES.index(phase) != current + 1:
            raise ReceiptError("transicion de fase invalida")
        payload = dict(evidence)
        _validate_evidence(phase, payload)
        if phase == "published" and payload["final_path"] != self.disk_path:
            raise ReceiptError("ruta publicada no coincide")
        return StorageReceipt(
            self.schema_version,
            self.operation_id,
            phase,
            self.disk_path,
            self.size_bytes,
            self.history + ({"phase": phase, "evidence": payload},),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operation_id": self.operation_id,
            "phase": self.phase,
            "disk_path": self.disk_path,
            "size_bytes": self.size_bytes,
            "history": [dict(item) for item in self.history],
        }

    def to_bytes(self) -> bytes:
        return (
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

    @classmethod
    def from_dict(cls, payload: object) -> StorageReceipt:
        if not isinstance(payload, dict):
            raise ReceiptError("recibo no es un objeto")
        try:
            schema_version = payload["schema_version"]
            operation_id = payload["operation_id"]
            phase = payload["phase"]
            disk_path = payload["disk_path"]
            size_bytes = payload["size_bytes"]
            history = payload["history"]
        except KeyError as exc:
            raise ReceiptError("recibo incompleto") from exc
        if (
            type(schema_version) is not int
            or not isinstance(operation_id, str)
            or not isinstance(phase, str)
            or not isinstance(disk_path, str)
        ):
            raise ReceiptError("cabecera de recibo invalida")
        normalized = _validate_history(history, phase)
        return cls(
            schema_version, operation_id, phase, disk_path, size_bytes, normalized
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> StorageReceipt:
        if not isinstance(payload, bytes):
            raise ReceiptError("bytes requeridos")
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReceiptError("JSON de recibo invalido") from exc
        return cls.from_dict(value)
