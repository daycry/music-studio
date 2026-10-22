"""Frontera HTTP de la sesión local."""

import asyncio
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, Response, StreamingResponse

from .api_models import ProblemDTO
from .errors import problem
from .event_dtos import JobStateDTO, SessionCredentialDTO
from .event_snapshot import build_snapshot
from .local_sessions import SessionError
from .models import Job, JobAttempt, Song, User
from .sse import (
    HEARTBEAT_SECONDS,
    PublicPayloadError,
    StreamClosed,
    TrustedScope,
    encode_frame,
    heartbeat,
    parse_cursor,
)

_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", re.ASCII)


def local_owner(engine):
    """Consulta sólo User, sin propietario de reserva."""
    try:
        with engine.connect() as connection:
            owners = (
                connection.execute(
                    select(User.id)
                    .where(User.name == "local", User.deleted_at.is_(None))
                    .limit(2)
                )
                .scalars()
                .all()
            )
    except SQLAlchemyError:
        return None
    if len(owners) != 1 or not _ULID.fullmatch(owners[0]):
        return None
    return owners[0]


def _responses():
    return {
        status: {
            "description": description,
            "content": {
                "application/problem+json": {"schema": ProblemDTO.model_json_schema()}
            },
        }
        for status, description in [
            (401, "Session required"),
            (403, "Forbidden"),
            (422, "Invalid parameters"),
            (503, "Service unavailable"),
        ]
    }


def _header_contract(name, bootstrap=False):
    return {
        "parameters": [
            {
                "name": name,
                "in": "header",
                "required": True,
                "schema": {
                    "type": "string",
                    **(
                        {"const": "1"}
                        if bootstrap
                        else {"maxLength": 64, "pattern": "^[A-Za-z0-9_-]{1,64}$"}
                    ),
                },
            }
        ]
    }


def _credential(request, name):
    values = [value for key, value in request.scope["headers"] if key.lower() == name]
    if len(values) != 1 or not 1 <= len(values[0]) <= 64:
        raise SessionError("SESSION_REQUIRED")
    try:
        return values[0].decode("ascii")
    except UnicodeDecodeError:
        raise SessionError("SESSION_REQUIRED") from None


def _header(request, name, *, required=False):
    values = [value for key, value in request.scope["headers"] if key.lower() == name]
    if len(values) > 1 or (required and len(values) != 1):
        raise PublicPayloadError("INVALID_PARAMS")
    if not values:
        return None
    try:
        value = values[0].decode("ascii")
    except UnicodeDecodeError:
        raise PublicPayloadError("INVALID_PARAMS") from None
    if not value or len(value) > 4096:
        raise PublicPayloadError("INVALID_PARAMS")
    return value


def _scope_filter(request):
    if len(request.scope.get("query_string", b"")) > 4096:
        raise PublicPayloadError("INVALID_PARAMS")
    song_values = []
    known_values = []
    for key, value in request.query_params.multi_items():
        if key == "song_id":
            song_values.append(value)
        elif key == "known_job_id":
            known_values.append(value)
        else:
            raise PublicPayloadError("INVALID_PARAMS")
    if len(song_values) > 1 or (
        song_values and _ULID.fullmatch(song_values[0]) is None
    ):
        raise PublicPayloadError("INVALID_PARAMS")
    if (
        len(known_values) > 64
        or len(set(known_values)) != len(known_values)
        or any(_ULID.fullmatch(value) is None for value in known_values)
    ):
        raise PublicPayloadError("INVALID_PARAMS")
    return song_values[0] if song_values else None, frozenset(known_values)


def _job_ids(engine, owner_id, song_id):
    with Session(engine) as session:
        query = select(Job.id).where(
            Job.owner_id == owner_id,
            Job.deleted_at.is_(None),
        )
        if song_id is not None:
            query = query.where(Job.song_id == song_id)
        return frozenset(session.scalars(query).all())


def _job_states(engine, owner_id, song_id, known_ids):
    with Session(engine) as session:
        query = select(Job).where(
            Job.owner_id == owner_id,
            Job.deleted_at.is_(None),
        )
        if song_id is not None:
            query = query.where(Job.song_id == song_id)
        jobs = list(session.scalars(query).all())
        by_id = {job.id: job for job in jobs}
        for job_id in known_ids:
            if job_id not in by_id:
                continue
        selected = [
            job
            for job in jobs
            if job.status in {"queued", "blocked", "running", "interrupted"}
            or job.id in known_ids
        ]
        selected.sort(key=lambda job: job.id)
        if len(selected) > 1064:
            raise ValueError("SNAPSHOT_LIMIT")
        attempts = {}
        if selected:
            rows = session.scalars(
                select(JobAttempt).where(
                    JobAttempt.job_id.in_([job.id for job in selected]),
                    JobAttempt.ordinal.in_([job.attempt for job in selected]),
                    JobAttempt.deleted_at.is_(None),
                )
            )
            attempts = {(row.job_id, row.ordinal): row for row in rows}
        return [
            JobStateDTO(
                job_id=job.id,
                song_id=job.song_id,
                status=job.status,
                attempt_id=(
                    attempt.id
                    if (attempt := attempts.get((job.id, job.attempt)))
                    else None
                ),
                stage=job.stage,
                progress=job.progress,
                error_code=job.error_code,
            )
            for job in selected
        ]


async def public_events(request: Request):
    """Stream only public, owner-bound events from the local runtime bus."""
    try:
        token = _credential(request, b"x-studio-session-token")
        registry = getattr(request.app.state, "session_registry", None)
        engine = getattr(request.app.state, "db", None)
        runtime = getattr(request.app.state, "queue", None)
        bus = getattr(runtime, "bus", None)
        if registry is None or engine is None or bus is None:
            raise SessionError("SERVICE_UNAVAILABLE")
        binding = registry.validate(token)
        song_id, known_ids = _scope_filter(request)
        if song_id is not None:
            with Session(engine) as session:
                # Membership is resolved by the jobs query below; no client
                # supplied owner id is ever trusted.
                exists = session.scalar(
                    select(Song.id)
                    .where(
                        Song.id == song_id,
                        Song.owner_id == binding.owner_id,
                        Song.deleted_at.is_(None),
                    )
                    .limit(1)
                )
            if exists is None:
                raise SessionError("FORBIDDEN_SCOPE")
        job_ids = await asyncio.to_thread(_job_ids, engine, binding.owner_id, song_id)
        if not known_ids <= job_ids:
            raise SessionError("FORBIDDEN_SCOPE")
        scope = TrustedScope(
            binding.owner_id,
            job_ids=job_ids,
            song_id=song_id,
            allow_system=True,
        )
        cursor = _header(request, b"last-event-id")
        subscription = bus.subscribe(scope, cursor)
        initial = ()
        if subscription.reset is not None:
            parsed = parse_cursor(subscription.reset.cursor)
            active = await asyncio.to_thread(
                _job_states, engine, binding.owner_id, song_id, frozenset()
            )
            known = await asyncio.to_thread(
                _job_states, engine, binding.owner_id, song_id, known_ids
            )
            stamp = (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            active = [
                value
                for value in active
                if value.status in {"queued", "blocked", "running", "interrupted"}
            ]
            initial = build_snapshot(
                active=active,
                known=known,
                epoch=parsed.epoch,
                high_water=parsed.seq,
                ts=stamp,
                snapshot_id=uuid4().hex,
                reason=subscription.reset.reason,
            )
    except SessionError as error:
        return problem(error.code)
    except PublicPayloadError:
        return problem("INVALID_PARAMS")
    except ValueError as error:
        return problem(
            "SNAPSHOT_LIMIT"
            if str(error) in {"SNAPSHOT_LIMIT", "FRAME_TOO_LARGE"}
            else "INVALID_PARAMS"
        )
    except (RuntimeError, SQLAlchemyError):
        return problem("SERVICE_UNAVAILABLE")

    async def stream():
        try:
            for frame in initial:
                yield frame
            while True:
                if await request.is_disconnected():
                    break
                try:
                    record = await asyncio.wait_for(
                        subscription.next(), timeout=HEARTBEAT_SECONDS
                    )
                except asyncio.TimeoutError:
                    yield heartbeat()
                    continue
                except StreamClosed:
                    break
                frame = encode_frame(record, scope)
                if frame is not None:
                    yield frame
        finally:
            subscription.close()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _empty_request(request, forbidden_header):
    if request.scope.get("query_string"):
        return False
    headers = request.scope["headers"]
    if len(headers) > 128:
        return False
    lengths = [v for k, v in headers if k.lower() == b"content-length"]
    if len(lengths) > 1 or (lengths and lengths != [b"0"]):
        return False
    if any(
        k.lower()
        in {
            b"transfer-encoding",
            b"authorization",
            b"x-studio-engine-token",
            forbidden_header,
        }
        for k, _ in headers
    ):
        return False
    try:
        message = await asyncio.wait_for(request.receive(), timeout=1.0)
    except TimeoutError:
        return False
    return (
        message["type"] == "http.request"
        and not message.get("body")
        and not message.get("more_body", False)
    )


async def bootstrap_local_session(request: Request):
    try:
        if _credential(request, b"x-studio-session-bootstrap") != "1":
            raise SessionError("SESSION_REQUIRED")
        if not await _empty_request(request, b"x-studio-session-token"):
            return problem("INVALID_PARAMS")
        owner = getattr(request.app.state, "session_owner_id", None)
        registry = getattr(request.app.state, "session_registry", None)
        engine = getattr(request.app.state, "db", None)
        if owner is None or registry is None or engine is None:
            raise SessionError("SERVICE_UNAVAILABLE")
        current = await asyncio.to_thread(local_owner, engine)
        if current != owner:
            raise SessionError("SERVICE_UNAVAILABLE")
        dto = registry.issue(owner)
        return JSONResponse(dto.model_dump(), headers={"Cache-Control": "no-store"})
    except SessionError as error:
        return problem(error.code)


async def revoke_local_session(request: Request):
    try:
        token = _credential(request, b"x-studio-session-token")
        if not await _empty_request(request, b"x-studio-session-bootstrap"):
            return problem("INVALID_PARAMS")
        registry = getattr(request.app.state, "session_registry", None)
        if registry is None:
            raise SessionError("SERVICE_UNAVAILABLE")
        registry.revoke(registry.validate(token))
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
    except SessionError as error:
        return problem(error.code)


def register_session_routes(application):
    """Registra rutas propias de cada factoría conservando las rutas anteriores."""
    application.add_api_route(
        "/api/session/bootstrap",
        bootstrap_local_session,
        methods=["POST"],
        operation_id="bootstrap_local_session",
        response_model=SessionCredentialDTO,
        responses=_responses(),
        openapi_extra=_header_contract("X-Studio-Session-Bootstrap", True),
    )
    application.add_api_route(
        "/api/session",
        revoke_local_session,
        methods=["DELETE"],
        operation_id="revoke_local_session",
        status_code=204,
        responses=_responses(),
        openapi_extra=_header_contract("X-Studio-Session-Token"),
    )
    application.add_api_route(
        "/api/events",
        public_events,
        methods=["GET"],
        operation_id="public_events",
        responses=_responses(),
        openapi_extra=_header_contract("X-Studio-Session-Token"),
    )
