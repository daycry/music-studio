"""Contrato /v1, independiente de frameworks GPU."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

CONTRACT_VERSION = "1"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ErrorCode(str, Enum):
    INVALID_PARAMS = "INVALID_PARAMS"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    WEIGHTS_MISMATCH = "WEIGHTS_MISMATCH"
    VRAM_EXCEEDED = "VRAM_EXCEEDED"
    BUSY = "BUSY"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INTERNAL = "INTERNAL"


def relative_path(value: str) -> str:
    if not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Ruta relativa POSIX requerida")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in value.split("/"):
        raise ValueError("Ruta fuera de data/")
    return value


class Input(ContractModel):
    role: str
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: str
    _path = field_validator("path")(relative_path)


class JobRequest(ContractModel):
    job_id: str = Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")
    task: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    mode: str | None = None
    inputs: list[Input] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    seed: int | None = Field(default=None, ge=0)
    n_outputs: int = Field(default=1, ge=1, le=64)
    output_dir: str
    timeout_s: int = Field(gt=0)
    _path = field_validator("output_dir")(relative_path)

    @model_validator(mode="after")
    def confined_output(self):
        if self.output_dir.rstrip("/") != f"tmp/{self.job_id}":
            raise ValueError("output_dir debe ser tmp/<job_id>/")
        return self


class Telemetry(ContractModel):
    load_s: float = Field(default=0, ge=0)
    run_s: float = Field(default=0, ge=0)
    rtf: float | None = Field(default=None, ge=0)
    vram_peak_mb: float = Field(default=0, ge=0)
    vram_cap_mb: float = Field(default=0, ge=0)
    spilled: bool = False
    mode: str
    model_revision: str
    extra: dict[str, Any] = Field(default_factory=dict)


class Artifact(ContractModel):
    output_index: int = Field(ge=0)
    path: str
    media_type: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    meta: dict[str, Any] = Field(default_factory=dict)
    _path = field_validator("path")(relative_path)


class StageData(ContractModel):
    stage: str


class ProgressData(ContractModel):
    fraction: float = Field(ge=0, le=1)
    step: int | None = None
    total: int | None = None
    output_index: int | None = None
    eta_s: float | None = None


class DeltaData(ContractModel):
    text: str


class LogData(ContractModel):
    level: str
    message: str


class DoneData(ContractModel):
    artifacts: list[Artifact]
    result: dict[str, Any] | None = None
    telemetry: Telemetry


class ErrorData(ContractModel):
    code: ErrorCode
    message: str
    retryable: bool


class CancelledData(ContractModel):
    telemetry: Telemetry


EVENT_DATA = {
    "stage": StageData,
    "progress": ProgressData,
    "delta": DeltaData,
    "artifact": Artifact,
    "log": LogData,
    "done": DoneData,
    "error": ErrorData,
    "cancelled": CancelledData,
}


class Event(ContractModel):
    seq: int = Field(ge=1)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    job_id: str = Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")
    type: Literal[
        "stage", "progress", "delta", "artifact", "log", "done", "error", "cancelled"
    ]
    data: dict[str, Any]

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler.resolve_ref_schema(handler(core_schema))
        # El discriminante vive en type; data conserva el mismo formato en /v1.
        schema["allOf"] = [
            {
                "if": {"properties": {"type": {"const": event_type}}},
                "then": {
                    "properties": {"data": handler(TypeAdapter(model).core_schema)}
                },
            }
            for event_type, model in EVENT_DATA.items()
        ]
        return schema

    @model_validator(mode="after")
    def typed_data(self):
        self.data = (
            EVENT_DATA[self.type].model_validate(self.data).model_dump(mode="json")
        )
        return self


class Feature(ContractModel):
    verified: bool


class InputDescriptor(ContractModel):
    role: str
    media_types: list[str]
    required: bool


class OutputDescriptor(ContractModel):
    media_type: str
    count: int = Field(default=1, ge=1)


class TaskDescriptor(ContractModel):
    verified: bool
    checkpoint: str | None = None
    device: Literal["gpu", "cpu"]
    params_schema: dict[str, Any]
    features: dict[str, Feature] = Field(default_factory=dict)
    inputs: list[InputDescriptor] = Field(default_factory=list)
    outputs: list[OutputDescriptor] = Field(default_factory=list)
    limits: dict[str, Any] = Field(default_factory=dict)
    cost_model: dict[str, Any] | None = None


class Provider(ContractModel):
    type: Literal["local", "external"]
    name: str | None = None


class Weight(ContractModel):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0)
    format: Literal["safetensors", "gguf", "onnx"]
    _path = field_validator("path")(relative_path)


class Mode(ContractModel):
    id: str
    vram_mb: float | None = Field(default=None, ge=0)
    notes: str


class ModelDescriptor(ContractModel):
    id: str
    family: str
    version: str
    revision: str
    license: str
    commercial_use: bool
    training_data: str
    provider: Provider
    weights: list[Weight]
    modes: list[Mode]
    tasks: dict[str, TaskDescriptor]


class LoadRequest(ContractModel):
    model_id: str
    mode: str | None = None


class LoadedModel(ContractModel):
    model_id: str
    mode: str


class GpuInfo(ContractModel):
    total_mb: float = Field(ge=0)
    free_mb: float = Field(ge=0)
    cap_mb: float = Field(ge=0)


class Health(ContractModel):
    contract_version: str = CONTRACT_VERSION
    engine_id: str
    engine_version: str
    image_digest: str
    state: Literal["idle", "loading", "busy", "error"]
    loaded: LoadedModel | None = None
    gpu: GpuInfo
    job_id: str | None = None


class Estimate(ContractModel):
    eta_s: float = Field(ge=0)
    vram_mb: float = Field(ge=0)
    cost_eur: float | None = Field(default=None, ge=0)


class JobStatus(ContractModel):
    job_id: str
    state: Literal["loading", "busy", "done", "error", "cancelled"]
    seq: int = Field(ge=0)


class Contract(ContractModel):
    contract_version: Literal["1"] = "1"
    request: JobRequest
    event: Event
    telemetry: Telemetry
    model: ModelDescriptor
    health: Health
    estimate: Estimate
    load: LoadRequest
    status: JobStatus
    stage: StageData
    progress: ProgressData
    delta: DeltaData
    artifact: Artifact
    log: LogData
    done: DoneData
    error: ErrorData
    cancelled: CancelledData


def contract_schema() -> dict[str, Any]:
    return Contract.model_json_schema()
