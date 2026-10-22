"""DTO públicos de la API del server."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class HealthDTO(BaseModel):
    status: Literal["running"]
    process: Literal["server"]


class ProblemDTO(BaseModel):
    type: Literal["about:blank"] = "about:blank"
    title: str
    status: int
    detail: str
    code: Literal[
        "INVALID_HOST",
        "FORBIDDEN_ORIGIN",
        "INVALID_PARAMS",
        "LYRICS_DECLARATION_REQUIRED",
        "NOT_FOUND",
        "METHOD_NOT_ALLOWED",
        "CONFLICT",
        "PURGE_RETENTION",
        "PURGE_PROTECTED",
        "INTERNAL",
        "SESSION_REQUIRED",
        "FORBIDDEN_SCOPE",
        "SESSION_LIMIT",
        "SNAPSHOT_LIMIT",
        "SERVICE_UNAVAILABLE",
    ]


class _OpenDTO(BaseModel):
    """Respuesta que puede crecer con campos opcionales del engine."""

    model_config = ConfigDict(extra="allow")


class EstimateResultDTO(_OpenDTO):
    eta_s: float
    vram_mb: float
    cost_eur: float | None = None


class PeaksDTO(_OpenDTO):
    version: int | None = None
    channels: int | None = None
    length: int | None = None
    data: list[list[list[float]]]


class ModelItemDTO(_OpenDTO):
    id: str
    family: str | None = None
    version: str | None = None
    revision: str | None = None
    license: str | None = None
    commercial_use: bool | None = None
    training_data: str | None = None
    provider: dict[str, Any] | None = None
    weights: list[dict[str, Any]] | None = None
    remote_code: list[dict[str, Any]] | None = None
    modes: list[dict[str, Any]] | None = None
    tasks: dict[str, dict[str, Any]] | None = None
    engine_id: str | None = None
    engine_version: str | None = None


class ModelsDTO(BaseModel):
    items: list[ModelItemDTO]


class SystemTaskDTO(_OpenDTO):
    verified: bool = False
    device: str | None = None
    params_schema: dict[str, Any] | None = None
    features: dict[str, Any] = {}


class SystemModelDTO(ModelItemDTO):
    tasks: dict[str, SystemTaskDTO] | None = None


class SystemGpuDTO(_OpenDTO):
    total_mb: float | None = None
    free_mb: float | None = None
    cap_mb: float | None = None


class SystemEngineDTO(_OpenDTO):
    state: str
    engine_id: str | None = None
    engine_version: str | None = None
    gpu: SystemGpuDTO | None = None


class SystemBytesDTO(BaseModel):
    total_bytes: int | None = None
    free_bytes: int | None = None


class SystemQueueDTO(BaseModel):
    queued: bool
    blocked: bool
    running: bool


class SystemInfoDTO(BaseModel):
    gpu: SystemGpuDTO | None
    ram: SystemBytesDTO
    engines: list[SystemEngineDTO]
    models: list[SystemModelDTO]
    queue: SystemQueueDTO
    disk: SystemBytesDTO
