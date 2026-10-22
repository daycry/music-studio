"""Autoridad sintética empaquetada, independiente del catálogo recibido (ADR-0062)."""

import re
from dataclasses import dataclass, field

from engine_contract import ModelDescriptor

from app.worker.contracts import (
    CapturedProvenance,
    SyntheticBinding,
    SyntheticCapturedDescriptor,
    SyntheticImplementation,
    canonical_sha256,
    synthetic_origin,
)

MOCK_ORIGIN = "http://engine-mock:8199"
MOCK_IMPLEMENTATION = {
    "name": "engine-mock",
    "revision": "synthetic-v1",
    "source_sha256": "4dad4770a82e9bfed486a8fad885deb893473fe94d665f81e48cc9be01d408f1",
    "common_source_sha256": "53fa2a4ccb3a9beb171eb0cae11edc3352dd5c7a21d462152880f44e7fabf096",
}


def packaged_mock_descriptor():
    """Receta literal CPU; no importa el adapter ni interpreta /models."""
    tasks = (
        "music.song",
        "music.instrumental",
        "music.retake",
        "music.extend",
        "music.repaint",
        "music.cover",
        "music.complete",
        "audio.stems",
        "audio.beats",
        "audio.key",
        "audio.transcribe",
        "audio.align_lyrics",
        "audio.clap",
        "audio.aesthetics",
        "text.generate",
        "image.generate",
        "image.edit",
        "image.depth",
        "video.i2v",
        "video.flf2v",
        "video.t2v",
        "video.lipsync",
        "video.upscale",
        "train.lora",
    )
    features = (
        "timbre_ref",
        "lora",
        "negative_prompt",
        "bpm",
        "key",
        "lyrics",
        "style",
        "duration_s",
        "seed",
        "language",
        "instrumental",
        "reference_image",
        "resolution",
        "fps",
        "strength",
        "guidance_scale",
    )

    def media_type(task):
        if task.startswith("music.") or task == "audio.stems":
            return "audio/wav"
        if task.startswith("image."):
            return "image/png"
        if task.startswith("video."):
            return "video/mp4"
        return {
            "text.generate": "text/plain",
            "train.lora": "application/octet-stream",
        }.get(task, "application/json")

    return ModelDescriptor(
        id="mock",
        family="mock",
        version="1",
        revision="synthetic-v1",
        license="All rights reserved",
        commercial_use=True,
        training_data="Sintético; sin datos de entrenamiento",
        provider={"type": "local"},
        weights=[],
        modes=[{"id": "cpu", "vram_mb": 0, "notes": "Sin GPU"}],
        tasks={
            task: {
                "verified": True,
                "device": "cpu",
                "params_schema": {
                    "type": "object",
                    "properties": {
                        "duration_s": {
                            "type": "number",
                            "exclusiveMinimum": 0,
                            "maximum": 600,
                        },
                        "style": {"type": "string"},
                        "lyrics": {"type": "string"},
                        "language": {"type": "string"},
                        "negative_prompt": {"type": "string"},
                        "key": {"type": "string"},
                        "time_signature": {"type": "string"},
                        "bpm": {"type": "number"},
                        "inference_steps": {"type": "integer", "minimum": 1},
                        "_mock": {"type": "object"},
                    },
                },
                "inputs": (
                    [
                        {
                            "role": "master",
                            "media_types": ["audio/wav", "audio/flac"],
                            "required": True,
                        }
                    ]
                    if task == "audio.beats"
                    else []
                ),
                "features": {feature: {"verified": True} for feature in features},
                "outputs": [{"media_type": media_type(task), "count": 1}],
                "limits": {"duration_s": [0.001, 600]},
            }
            for task in tasks
        },
    )


@dataclass(frozen=True, eq=False)
class TrustedSyntheticEntry:
    backend: object
    descriptor: SyntheticCapturedDescriptor
    binding: SyntheticBinding

    def __post_init__(self):
        if type(self.binding) is SyntheticBinding:
            SyntheticBinding.model_validate_json(self.binding.model_dump_json())
        if type(self.descriptor) is SyntheticCapturedDescriptor:
            SyntheticCapturedDescriptor(self.descriptor.root)
        if (
            type(self.descriptor) is not SyntheticCapturedDescriptor
            or type(self.binding) is not SyntheticBinding
            or self.binding.descriptor_sha256 != canonical_sha256(self.descriptor)
            or self.binding.origin != synthetic_origin(self.backend.origin)
        ):
            raise ValueError("Invalid trusted synthetic entry")

    @classmethod
    def from_descriptor(
        cls,
        backend,
        descriptor,
        *,
        recipe_id,
        scope,
        engine_id,
        engine_version,
        implementation,
        contract_version="1",
        expected_image_digest=None,
    ):
        snapshot = SyntheticCapturedDescriptor(descriptor)
        implementation = SyntheticImplementation.model_validate(implementation)
        binding = SyntheticBinding(
            version=1,
            recipe_id=recipe_id,
            scope=scope,
            origin=synthetic_origin(backend.origin),
            engine_id=engine_id,
            engine_version=engine_version,
            contract_version=contract_version,
            descriptor_sha256=canonical_sha256(snapshot),
            implementation=implementation,
            implementation_sha256=canonical_sha256(implementation),
            expected_image_digest=expected_image_digest,
        )
        return cls(backend, snapshot, binding)


@dataclass(frozen=True, eq=False)
class SyntheticLease:
    _registry: object
    _entry: TrustedSyntheticEntry
    binding: SyntheticBinding


@dataclass(frozen=True, eq=False)
class SyntheticRegistry:
    entries: tuple[TrustedSyntheticEntry, ...] = ()
    _issued: dict = field(default_factory=dict, init=False, repr=False, compare=False)

    def __post_init__(self):
        entries = tuple(self.entries)
        if len(entries) > 128 or any(
            type(entry) is not TrustedSyntheticEntry for entry in entries
        ):
            raise ValueError("Invalid synthetic composition")
        keys = [
            (
                id(entry.backend),
                entry.binding.descriptor_sha256,
                entry.binding.engine_id,
                entry.binding.engine_version,
                entry.binding.contract_version,
            )
            for entry in entries
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("Conflicting synthetic composition")
        object.__setattr__(self, "entries", entries)

    def validate_backends(self, backends):
        if any(
            not any(entry.backend is backend for backend in backends.values())
            or synthetic_origin(entry.backend.origin) != entry.binding.origin
            for entry in self.entries
        ):
            raise ValueError("Synthetic composition/backend mismatch")

    def _lease(self, entry):
        if entry not in self._issued:
            self._issued[entry] = SyntheticLease(self, entry, entry.binding)
        return self._issued[entry]

    def select(self, backend, descriptor, health):
        try:
            snapshot = SyntheticCapturedDescriptor(descriptor)
            digest = health.image_digest
            if digest != "unknown" and (
                not isinstance(digest, str)
                or re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is None
            ):
                return None
            for entry in self.entries:
                binding = entry.binding
                if (
                    backend is entry.backend
                    and snapshot == entry.descriptor
                    and synthetic_origin(backend.origin) == binding.origin
                    and (
                        health.engine_id,
                        health.engine_version,
                        health.contract_version,
                    )
                    == (
                        binding.engine_id,
                        binding.engine_version,
                        binding.contract_version,
                    )
                    and (
                        binding.expected_image_digest is None
                        or digest == binding.expected_image_digest
                    )
                ):
                    return self._lease(entry)
        except (ValueError, TypeError, AttributeError):
            pass
        return None

    def check(self, lease, binding):
        try:
            return (
                type(lease) is SyntheticLease
                and lease._registry is self
                and self._issued.get(lease._entry) is lease
                and lease.binding == lease._entry.binding == binding
                and synthetic_origin(lease._entry.backend.origin) == binding.origin
            )
        except (ValueError, TypeError, AttributeError):
            return False

    def rebind(self, captured, *, backend):
        captured = CapturedProvenance.model_validate_json(captured.model_dump_json())
        for entry in self.entries:
            if (
                captured.evidence_kind == "synthetic"
                and backend is entry.backend
                and captured.synthetic_binding == entry.binding
                and captured.descriptor == entry.descriptor
                and synthetic_origin(backend.origin) == entry.binding.origin
            ):
                return self._lease(entry)
        raise ValueError("Synthetic capture has no fresh composition authority")


def packaged_mock_registry(backends, origins):
    backend = backends.get("mock")
    if backend is None or synthetic_origin(origins.get("mock", "")) != MOCK_ORIGIN:
        return SyntheticRegistry()
    if synthetic_origin(backend.origin) != MOCK_ORIGIN:
        return SyntheticRegistry()
    return SyntheticRegistry(
        (
            TrustedSyntheticEntry.from_descriptor(
                backend,
                packaged_mock_descriptor(),
                recipe_id="packaged-engine-mock-cpu-v1",
                scope="product",
                engine_id="mock",
                engine_version="0.1.0",
                implementation=MOCK_IMPLEMENTATION,
            ),
        )
    )
