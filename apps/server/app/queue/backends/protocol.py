"""Nueve operaciones async y acuses locales que faltan en engine_contract."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from engine_contract import (
    Estimate,
    Event,
    Health,
    JobRequest,
    JobStatus,
    LoadedModel,
    LoadRequest,
    ModelDescriptor,
)
from pydantic import BaseModel, ConfigDict, Field


class BackendFailure(RuntimeError):
    """Observación desconocida; jamás equivale a terminal ni ausencia."""

    def __init__(self, code="UNKNOWN"):
        self.code = code
        super().__init__("Engine observation failed: " + code)


class UnloadResult(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    freed_mb: float = Field(ge=0, allow_inf_nan=False)


class Submission(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    job_id: str = Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")


class CancelAck(Submission):
    """Recepción de cancelación; no demuestra que terminó el proceso."""


@dataclass(frozen=True)
class ConfirmedAbsent:
    job_id: str


@runtime_checkable
class EngineBackend(Protocol):
    @property
    def origin(self) -> str: ...
    async def health(self) -> Health: ...
    async def models(self) -> list[ModelDescriptor]: ...
    async def load(self, request: LoadRequest) -> LoadedModel: ...
    async def unload(self) -> UnloadResult: ...
    async def estimate(self, request: JobRequest) -> Estimate: ...
    async def submit(self, request: JobRequest) -> Submission: ...
    async def status(self, attempt_id: str) -> JobStatus | ConfirmedAbsent: ...
    def events(self, attempt_id: str, after: int = 0) -> AsyncIterator[Event]: ...
    async def cancel(self, attempt_id: str) -> CancelAck: ...
