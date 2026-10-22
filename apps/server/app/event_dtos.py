"""DTOs públicos cerrados y controles SSE puros, sin autoridad ni DB.

La allowlist protege la forma, no detecta secretos disfrazados de etiquetas.
El ensamblador futuro comprueba consistencia entre chunks y pertenencia.
"""

import re
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SAFE_INTEGER = 9007199254740991
MAX_FRAME_BYTES = 65536
ULID = Annotated[str, Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$", max_length=26)]
PublicLabel = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$", max_length=64)]
SnapshotId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$", max_length=32)]
ChunkCount = Annotated[int, Field(ge=0, le=17)]
_CURSOR = re.compile(r"([0-9a-f]{32}):([1-9][0-9]{0,15})", re.ASCII)


class _ClosedDTO(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )


class SessionCredentialDTO(_ClosedDTO):
    """El bootstrap autorizado exporta intencionadamente la credencial pública."""

    session_token: Annotated[
        str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$", max_length=64, repr=False)
    ]
    expires_in_s: Annotated[int, Field(ge=1, le=28800)]


class JobStateDTO(_ClosedDTO):
    job_id: ULID
    song_id: ULID
    status: Literal[
        "queued",
        "blocked",
        "running",
        "interrupted",
        "succeeded",
        "failed",
        "cancelled",
    ]
    attempt_id: ULID | None
    stage: PublicLabel | None
    progress: Annotated[float, Field(ge=0, le=1)] | None
    error_code: PublicLabel | None


class SnapshotBeginDTO(_ClosedDTO):
    status: Literal["snapshot"]
    phase: Literal["begin"]
    snapshot_id: SnapshotId
    reason: Literal["bootstrap", "epoch", "expired", "ahead"]
    active_count: Annotated[int, Field(ge=0, le=1000)]
    known_count: Annotated[int, Field(ge=0, le=64)]
    chunk_count: ChunkCount


class SnapshotChunkDTO(_ClosedDTO):
    status: Literal["snapshot"]
    phase: Literal["chunk"]
    snapshot_id: SnapshotId
    index: Annotated[int, Field(ge=0, le=16)]
    jobs: Annotated[list[JobStateDTO], Field(min_length=1, max_length=64)]


class SnapshotEndDTO(_ClosedDTO):
    status: Literal["snapshot"]
    phase: Literal["end"]
    snapshot_id: SnapshotId
    chunk_count: ChunkCount
    cursor: Annotated[str, Field(max_length=96)]

    @field_validator("cursor")
    @classmethod
    def valid_cursor(cls, value: str) -> str:
        match = _CURSOR.fullmatch(value)
        if match is None or int(match[2]) > MAX_SAFE_INTEGER:
            raise ValueError("INVALID_CURSOR")
        return value


class SnapshotControlDTO(_ClosedDTO):
    id: Annotated[int, Field(ge=1, le=MAX_SAFE_INTEGER)]
    type: Literal["system.status"]
    ts: Annotated[
        str,
        Field(
            pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$",
            max_length=24,
        ),
    ]
    data: Annotated[
        SnapshotBeginDTO | SnapshotChunkDTO | SnapshotEndDTO,
        Field(discriminator="phase"),
    ]

    @field_validator("ts")
    @classmethod
    def valid_stamp(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            raise ValueError("INVALID_TIMESTAMP") from None
        return value

    @model_validator(mode="after")
    def matching_end_cursor(self) -> Self:
        if (
            isinstance(self.data, SnapshotEndDTO)
            and int(self.data.cursor.split(":")[1]) != self.id
        ):
            raise ValueError("INVALID_CURSOR")
        return self


def encode_snapshot_control(dto: SnapshotControlDTO) -> bytes:
    """Sólo end confirma el cursor; cada body conserva H idéntico."""
    # Revalidar hijos: listas mutables o model_construct no hacen autoridad.
    dto = SnapshotControlDTO.model_validate(dto.model_dump())
    text = "event: system.status\n"
    if isinstance(dto.data, SnapshotEndDTO):
        text += f"id: {dto.data.cursor}\n"
    text += f"data: {dto.model_dump_json()}\n\n"
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_FRAME_BYTES:
        raise ValueError("FRAME_TOO_LARGE")
    return encoded
