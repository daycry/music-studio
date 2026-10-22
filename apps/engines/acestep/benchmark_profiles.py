"""Perfiles explícitos; disponibilidad de pesos no acredita capacidades."""

from dataclasses import dataclass

from engine_common import EngineError


@dataclass(frozen=True)
class CheckpointProfile:
    checkpoint: str
    model_id: str
    family_variant: str
    default_steps: int
    max_steps: int
    cfg_supported: bool
    default_cfg: float = 7.0
    modes: tuple[str, ...] = ("bf16", "offload")


PROFILES = tuple(
    CheckpointProfile(
        f"acestep-v15-{variant}",
        f"ace-step-1.5-{variant}",
        variant.replace("-", "_"),
        steps,
        maximum,
        cfg,
        modes=("bf16", "offload", "offload-int8")
        if variant == "xl-turbo"
        else ("bf16", "offload"),
    )
    for variant, steps, maximum, cfg in (
        ("turbo", 8, 8, False),
        ("sft", 50, 200, True),
        ("base", 32, 200, True),
        ("xl-turbo", 8, 8, False),
    )
)


def checkpoint_profile(checkpoint):
    for profile in PROFILES:
        if profile.checkpoint == checkpoint:
            return profile
    raise EngineError("MODEL_NOT_FOUND", "Checkpoint desconocido")


def identity_profile(model_id):
    for profile in PROFILES:
        if profile.model_id == model_id:
            return profile
    raise EngineError("MODEL_NOT_FOUND", "Identidad desconocida")
