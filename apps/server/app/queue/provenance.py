"""Selección inmutable y evidencia musical previa al envío (ADR-0060)."""

import json
from dataclasses import dataclass

from app.worker.contracts import (
    CapturedDescriptor,
    CapturedLoad,
    CapturedProvenance,
    ObservedModel,
    SyntheticBinding,
    SyntheticCapturedDescriptor,
    canonical_sha256,
)

from .synthetic_registry import SyntheticRegistry

MUSIC_TASKS = frozenset({"music.song", "music.instrumental"})


@dataclass(frozen=True)
class SelectedProvenance:
    descriptor: CapturedDescriptor
    engine_id: str
    engine_version: str
    contract_version: str
    task: str
    load: CapturedLoad
    resolve_health_json: str
    expected_image_digest: str | None = None
    evidence_kind: str = "learned"
    synthetic_binding: SyntheticBinding | None = None
    registry: SyntheticRegistry | None = None
    lease: object = None

    @classmethod
    def select(
        cls, descriptor, health, task, model_id, mode, *, backend=None, registry=None
    ):
        registry = registry if registry is not None else SyntheticRegistry()
        lease = registry.select(backend, descriptor, health)
        selected = cls(
            SyntheticCapturedDescriptor(descriptor)
            if lease
            else CapturedDescriptor(descriptor),
            health.engine_id,
            health.engine_version,
            health.contract_version,
            task,
            CapturedLoad(model_id=model_id, mode=mode),
            health.model_dump_json(),
            lease.binding.expected_image_digest if lease else None,
            "synthetic" if lease else "learned",
            lease.binding if lease else None,
            registry if lease else None,
            lease,
        )
        # Valida el descriptor seleccionado, sin convertir el residente OTHER
        # de la planificación en una observación de la carga que aún no ocurrió.
        CapturedProvenance(
            descriptor=selected.descriptor,
            engine_id=selected.engine_id,
            engine_version=selected.engine_version,
            contract_version=selected.contract_version,
            task=selected.task,
            load=selected.load,
            observed_model=None,
            expected_image_digest=selected.expected_image_digest,
            reported_image_digest=reported_digest(health.image_digest),
            evidence_kind=selected.evidence_kind,
            synthetic_binding=selected.synthetic_binding,
        )
        return selected

    @classmethod
    def from_captured(cls, captured, *, backend=None, registry=None):
        captured = CapturedProvenance.model_validate_json(captured.model_dump_json())
        lease = None
        if captured.evidence_kind == "synthetic":
            if registry is None:
                raise ValueError("Fresh synthetic composition required")
            lease = registry.rebind(captured, backend=backend)
        return cls(
            captured.descriptor,
            captured.engine_id,
            captured.engine_version,
            captured.contract_version,
            captured.task,
            captured.load,
            json.dumps({"image_digest": captured.reported_image_digest or "unknown"}),
            captured.expected_image_digest,
            captured.evidence_kind,
            captured.synthetic_binding,
            registry if lease else None,
            lease,
        )

    def authorized(self, registry=None):
        if self.evidence_kind == "learned":
            return (
                self.synthetic_binding is None
                and self.lease is None
                and self.registry is None
            )
        return bool(
            self.evidence_kind == "synthetic"
            and self.registry is not None
            and (registry is None or registry is self.registry)
            and self.registry.check(self.lease, self.synthetic_binding)
            and type(self.descriptor) is SyntheticCapturedDescriptor
            and canonical_sha256(self.descriptor)
            == self.synthetic_binding.descriptor_sha256
            and (self.engine_id, self.engine_version, self.contract_version)
            == (
                self.synthetic_binding.engine_id,
                self.synthetic_binding.engine_version,
                self.synthetic_binding.contract_version,
            )
            and self.expected_image_digest
            == self.synthetic_binding.expected_image_digest
        )

    def binds(self, request, load):
        return (
            self.authorized()
            and request.task == self.task
            and request.model_id == load.model_id == self.load.model_id
            and request.mode == load.mode == self.load.mode
        )


def reported_digest(value):
    """Sólo el literal del contrato representa ausencia de digest."""
    if value == "unknown":
        return None
    import re

    if (
        not isinstance(value, str)
        or re.fullmatch(r"sha256:[a-f0-9]{64}", value) is None
    ):
        raise ValueError("Invalid known image digest")
    return value


def capture_before_send(selected, request, load, health, *, require_loaded):
    if not selected.binds(request, load):
        raise ValueError("Selected request/load mismatch")
    if (
        (health.engine_id, health.engine_version, health.contract_version)
        != (selected.engine_id, selected.engine_version, selected.contract_version)
        or health.contract_version != "1"
        or health.image_digest
        != json.loads(selected.resolve_health_json)["image_digest"]
        or health.state != "idle"
        or health.job_id is not None
    ):
        raise ValueError("Fresh health identity/state mismatch")
    if require_loaded and health.loaded is None:
        raise ValueError("Load not observed")
    observed = (
        ObservedModel(model_id=health.loaded.model_id, mode=health.loaded.mode)
        if health.loaded is not None
        else None
    )
    return CapturedProvenance(
        descriptor=selected.descriptor,
        engine_id=selected.engine_id,
        engine_version=selected.engine_version,
        contract_version=selected.contract_version,
        task=selected.task,
        load=selected.load,
        observed_model=observed,
        expected_image_digest=selected.expected_image_digest,
        reported_image_digest=reported_digest(health.image_digest),
        evidence_kind=selected.evidence_kind,
        synthetic_binding=selected.synthetic_binding,
    )
