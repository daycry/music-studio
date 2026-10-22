"""DTO públicos de la API del server."""

from typing import Literal

from pydantic import BaseModel


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
