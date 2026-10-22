"""Adaptación pura: contexto preautorizado, sin HTTP, SQL ni snapshots."""

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

MAX_SAFE_INTEGER = 9007199254740991
MAX_FRAME_BYTES = 64 * 1024
HEARTBEAT_SECONDS = 15
PUBLIC_TYPES = frozenset(
    {
        "job.created",
        "job.stage",
        "job.progress",
        "job.delta",
        "job.done",
        "job.failed",
        "job.cancelled",
        "entity.updated",
        "system.status",
    }
)
_CURSOR = re.compile(r"([0-9a-f]{32}):([1-9][0-9]{0,15})", re.ASCII)
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", re.ASCII)
_LABEL = re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII)


class PublicPayloadError(ValueError):
    """Error finito sin eco de datos privados."""

    def __init__(self, code: str = "INVALID_PAYLOAD"):
        self.code = code
        super().__init__(code)


class StreamClosed(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class Cursor:
    epoch: str
    seq: int

    @property
    def wire(self) -> str:
        return f"{self.epoch}:{self.seq}"


def parse_cursor(value: str) -> Cursor:
    # ASCII hace len == bytes, sin asignación UTF-8 antes del límite.
    if type(value) is not str or len(value) > 96 or not value.isascii():
        raise PublicPayloadError("INVALID_CURSOR")
    match = _CURSOR.fullmatch(value)
    if match is None or int(match[2]) > MAX_SAFE_INTEGER:
        raise PublicPayloadError("INVALID_CURSOR")
    return Cursor(match[1], int(match[2]))


@dataclass(frozen=True)
class TrustedScope:
    """Permisos ya resueltos por integración futura, nunca por filtro cliente.

    Un cursor sin contexto no permite detectar un cambio de filtro. La futura
    web debe borrar el cursor al cambiarlo. owner_id no autentica por sí solo.
    """

    owner_id: str
    job_ids: frozenset[str] = field(default_factory=frozenset)
    allow_delta: bool = False
    song_id: str | None = None
    entity_ids: frozenset[str] = field(default_factory=frozenset)
    allow_system: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.owner_id) is not str
            or not self.owner_id
            or len(self.owner_id) > 64
            or type(self.job_ids) is not frozenset
            or len(self.job_ids) > 64
            or type(self.entity_ids) is not frozenset
            or len(self.entity_ids) > 64
            or any(
                type(v) is not str or not v or len(v) > 64
                for v in self.job_ids | self.entity_ids
            )
            or type(self.allow_delta) is not bool
            or type(self.allow_system) is not bool
            or (
                self.song_id is not None
                and (
                    type(self.song_id) is not str
                    or not self.song_id
                    or len(self.song_id) > 64
                )
            )
        ):
            raise PublicPayloadError("INVALID_SCOPE")

    def matches(self, envelope: dict[str, Any]) -> bool:
        if type(envelope) is not dict:
            return False
        if "owner_id" in envelope and envelope["owner_id"] != self.owner_id:
            return False
        if self.song_id is not None and envelope.get("song_id") != self.song_id:
            return False
        kind = envelope.get("type")
        if kind == "system.status":
            return self.allow_system
        if kind == "entity.updated":
            identity = envelope.get("entity_id")
            return type(identity) is str and identity in self.entity_ids
        identity = envelope.get("job_id")
        return type(identity) is str and identity in self.job_ids


@dataclass(frozen=True)
class PublicRecord:
    epoch: str
    seq: int
    envelope: dict[str, Any]
    authority: object = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class TrustedFeedScope:
    """Feed interno de owner fijo; no autentica ni reautoriza replay en DB.

    No exponer por HTTP hasta conectar writers, invalidación y bind autorizado.
    Sin conjuntos de jobs crecientes; autoridad sólo por certificado publisher.
    """

    owner_id: str
    song_id: str | None = None
    allow_delta: bool = field(default=False, init=False)
    allow_system: bool = field(default=False, init=False)

    def __post_init__(self):
        _ulid(self.owner_id)
        if self.song_id is not None:
            _ulid(self.song_id)

    def matches(self, record) -> bool:
        if type(record) is not PublicRecord:
            return False
        authority = record.authority
        if (
            type(authority) is not _FeedAuthority
            or authority._seal is not _CERTIFICATION
            or authority.owner_id != self.owner_id
            or (self.song_id is not None and authority.song_id != self.song_id)
        ):
            return False
        try:
            identity, entity_type = _feed_identity(record.envelope)
            validate_record(record)
        except (PublicPayloadError, TypeError, KeyError):
            return False
        return (
            authority.kind == record.envelope["type"]
            and authority.identity == identity
            and authority.entity_type == entity_type
            and record.envelope.get("owner_id", authority.owner_id)
            == authority.owner_id
            and record.envelope.get("song_id", authority.song_id) == authority.song_id
        )


_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", re.ASCII)
_CERTIFICATION = object()
_FEED_ENTITY_TYPES = frozenset(
    {
        "song",
        "take",
        "lyrics",
        "artwork",
        "video_project",
        "shot",
        "shot_version",
        "render",
        "analysis",
        "asset",
    }
)


def _ulid(value):
    if type(value) is not str or _ULID.fullmatch(value) is None:
        raise PublicPayloadError("INVALID_FEED_IDENTITY")
    return value


def _feed_identity(envelope):
    if type(envelope) is not dict:
        raise PublicPayloadError()
    kind = envelope.get("type")
    if type(kind) is not str or kind in {"job.delta", "system.status"}:
        raise PublicPayloadError("INVALID_FEED_EVENT")
    if kind == "entity.updated":
        identity = _ulid(envelope.get("entity_id"))
        data = envelope.get("data")
        if (
            type(data) is not dict
            or type(data.get("type")) is not str
            or data["type"] not in _FEED_ENTITY_TYPES
            or data.get("id") != identity
        ):
            raise PublicPayloadError("INVALID_FEED_ENTITY")
        return identity, data["type"]
    if kind not in PUBLIC_TYPES | {"job.error"}:
        raise PublicPayloadError("INVALID_FEED_EVENT")
    identity = _ulid(envelope.get("job_id"))
    if "attempt_id" in envelope:
        _ulid(envelope["attempt_id"])
    return identity, None


@dataclass(frozen=True)
class _FeedAuthority:
    owner_id: str
    song_id: str
    kind: str
    identity: str
    entity_type: str | None
    _seal: object = field(repr=False, compare=False)

    def __deepcopy__(self, memo):
        # Inmutable: conservar la identidad del sello, sin exportarlo a JSON.
        return self


@dataclass(frozen=True)
class CertifiedPublication:
    """Sobre interno emitido después de checks DB del publisher del server.

    No aceptarlo de JSON ni interpretar public_scope_verified como permiso.
    La fábrica no consulta SQL: la integración debe acreditar sus argumentos.
    """

    envelope: dict[str, Any]
    authority: _FeedAuthority = field(repr=False)


def certify_publication(envelope, *, owner_id, song_id):
    from copy import deepcopy

    _ulid(owner_id)
    _ulid(song_id)
    bounded_json(envelope)
    identity, entity_type = _feed_identity(envelope)
    if (
        envelope.get("owner_id", owner_id) != owner_id
        or envelope.get("song_id", song_id) != song_id
    ):
        raise PublicPayloadError("INVALID_FEED_AUTHORITY")
    validate_record(PublicRecord("0" * 32, 1, envelope))
    authority = _FeedAuthority(
        owner_id, song_id, envelope["type"], identity, entity_type, _CERTIFICATION
    )
    return CertifiedPublication(deepcopy(envelope), authority)


def scope_matches(scope: TrustedScope | TrustedFeedScope, record: PublicRecord) -> bool:
    if type(scope) is TrustedFeedScope:
        return scope.matches(record)
    return scope.matches(record.envelope)


def validate_certification(record: PublicRecord) -> None:
    authority = record.authority
    if type(authority) is not _FeedAuthority or not TrustedFeedScope(
        authority.owner_id
    ).matches(record):
        raise PublicPayloadError("INVALID_FEED_CERTIFICATE")


@dataclass(frozen=True)
class ResetPlan:
    """Plan de recuperación; no contiene DTOs ni estado SQL inventados."""

    reason: Literal["bootstrap", "epoch", "expired", "ahead"]
    cursor: str


def bounded_json(value: Any) -> None:
    """Preflight antes de deepcopy/JSON: volumen, profundidad y tipos finitos."""
    remaining = MAX_FRAME_BYTES
    nodes = 4096

    def visit(item: Any, depth: int) -> None:
        nonlocal remaining, nodes
        nodes -= 1
        if nodes < 0 or depth > 8:
            raise PublicPayloadError("PAYLOAD_LIMIT")
        if type(item) is str:
            if len(item) > remaining:
                raise PublicPayloadError("PAYLOAD_LIMIT")
            try:
                remaining -= len(item.encode("utf-8")) + 2
            except UnicodeError:
                raise PublicPayloadError() from None
        elif item is None or type(item) is bool:
            remaining -= 5
        elif type(item) in (int, float):
            if (type(item) is int and abs(item) > MAX_SAFE_INTEGER) or (
                type(item) is float and not math.isfinite(item)
            ):
                raise PublicPayloadError()
            remaining -= 32
        elif type(item) is dict:
            if len(item) > nodes:
                raise PublicPayloadError("PAYLOAD_LIMIT")
            for key, child in item.items():
                if type(key) is not str:
                    raise PublicPayloadError()
                visit(key, depth + 1)
                visit(child, depth + 1)
            remaining -= len(item) * 2 + 2
        elif type(item) is list:
            if len(item) > nodes:
                raise PublicPayloadError("PAYLOAD_LIMIT")
            for child in item:
                visit(child, depth + 1)
            remaining -= len(item) + 2
        else:
            raise PublicPayloadError()
        if remaining < 0:
            raise PublicPayloadError("PAYLOAD_LIMIT")

    visit(value, 0)


def _timestamp(value: Any) -> str:
    if type(value) is not str or len(value) > 27 or _STAMP.fullmatch(value) is None:
        raise PublicPayloadError("INVALID_TIMESTAMP")
    try:
        stamp = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise PublicPayloadError("INVALID_TIMESTAMP") from None
    return stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _label(value: Any) -> str:
    if type(value) is not str or _LABEL.fullmatch(value) is None:
        raise PublicPayloadError()
    return value


def _public_body(record: PublicRecord, allow_delta: bool) -> dict[str, Any]:
    envelope = record.envelope
    if type(envelope) is not dict:
        raise PublicPayloadError()
    if type(record.seq) is not int or not 1 <= record.seq <= MAX_SAFE_INTEGER:
        raise PublicPayloadError("INVALID_CURSOR")
    if type(record.epoch) is not str or len(record.epoch) != 32:
        raise PublicPayloadError("INVALID_CURSOR")
    parse_cursor(f"{record.epoch}:{record.seq}")
    kind = envelope.get("type")
    kind = "job.failed" if kind == "job.error" else kind
    if type(kind) is not str or kind not in PUBLIC_TYPES:
        raise PublicPayloadError("INVALID_EVENT_TYPE")
    if (kind.startswith("job.") and "job_id" not in envelope) or (
        kind == "entity.updated" and "entity_id" not in envelope
    ):
        raise PublicPayloadError()
    data = envelope.get("data")
    if type(data) is not dict:
        raise PublicPayloadError()
    if kind == "entity.updated" and not {"type", "id"} <= data.keys():
        raise PublicPayloadError()
    public: dict[str, Any] = {}
    for key in (
        ()
        if kind == "entity.updated"
        else ("job_id", "attempt_id", "song_id", "entity_id")
    ):
        if key in envelope:
            public[key] = _label(envelope[key])
    # Sin message, request, result, telemetry, terminal ni rutas privadas.
    fields = {
        "job.created": ("status",),
        "job.stage": ("status", "stage"),
        "job.progress": ("status", "fraction"),
        "job.delta": ("status",),
        "job.done": ("status",),
        "job.failed": ("status", "code", "retryable"),
        "job.cancelled": ("status",),
        "entity.updated": ("type", "id"),
        "system.status": ("status",),
    }[kind]
    for key in fields:
        if key not in data:
            continue
        value = data[key]
        if key == "fraction":
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                raise PublicPayloadError()
        elif key == "retryable":
            if type(value) is not bool:
                raise PublicPayloadError()
        else:
            value = _label(value)
        public[key] = value
    if kind == "job.delta" and allow_delta and "text" in data:
        if type(data["text"]) is not str:
            raise PublicPayloadError()
        public["text"] = data["text"]
    body = {
        "id": record.seq,
        "type": kind,
        "ts": _timestamp(envelope.get("ts")),
        "data": public,
    }
    bounded_json(body)
    return body


def validate_record(record: PublicRecord) -> None:
    """Valida forma del publicador, sin fabricar una autorización de entrega."""
    body = _public_body(record, allow_delta=True)
    _frame_size(record, body)


def public_event(
    record: PublicRecord, scope: TrustedScope | TrustedFeedScope
) -> dict[str, Any] | None:
    # Ni acceso al payload ni serialización antes del predicado autorizado.
    if not scope_matches(scope, record):
        return None
    return _public_body(record, scope.allow_delta)


def _frame_size(record: PublicRecord, body: dict[str, Any]) -> None:
    """Cuenta bytes JSON escapados antes de asignar cadenas/frames completos."""

    def size(value: Any) -> int:
        if type(value) is str:
            total = 2
            for char in value:
                code = ord(char)
                total += (
                    2
                    if char in '\\"\b\f\n\r\t'
                    else 6
                    if code < 32
                    else 1
                    if code < 128
                    else 2
                    if code < 2048
                    else 3
                    if code < 65536
                    else 4
                )
            return total
        if type(value) is dict:
            return (
                2
                + max(0, len(value) - 1)
                + sum(size(k) + 1 + size(v) for k, v in value.items())
            )
        if type(value) is list:
            return 2 + max(0, len(value) - 1) + sum(size(v) for v in value)
        if value is None:
            return 4
        if type(value) is bool:
            return 4 if value else 5
        return len(str(value))

    header = len(f"id: {record.epoch}:{record.seq}\nevent: {body['type']}\ndata: ") + 2
    if header + size(body) > MAX_FRAME_BYTES:
        raise PublicPayloadError("FRAME_LIMIT")


def encode_frame(
    record: PublicRecord, scope: TrustedScope | TrustedFeedScope
) -> bytes | None:
    body = public_event(record, scope)
    if body is None:
        return None
    _frame_size(record, body)
    chunks = [
        f"id: {record.epoch}:{record.seq}\nevent: {body['type']}\ndata: ".encode(
            "ascii"
        )
    ]
    size = len(chunks[0]) + 2
    for piece in json.JSONEncoder(
        ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).iterencode(body):
        chunk = piece.encode("utf-8")
        size += len(chunk)
        if size > MAX_FRAME_BYTES:
            raise PublicPayloadError("FRAME_LIMIT")
        chunks.append(chunk)
    return b"".join(chunks) + b"\n\n"


def heartbeat() -> bytes:
    return b": keep-alive\n\n"
