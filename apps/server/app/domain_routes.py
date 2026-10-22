"""API de dominio M1: canciones, letras y entrada de generaciones."""

import hashlib
import json
import logging
import math
import re
import shutil
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from audio_post.manifest import safe_path
from engine_contract import JobRequest
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import exists, or_, select, text
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, Response

from . import models
from .api_models import (
    EstimateResultDTO,
    ModelsDTO,
    PeaksDTO,
    ProblemDTO,
    SystemInfoDTO,
)
from .errors import problem
from .event_routes import _credential
from .local_sessions import SessionError
from .lyrics import parse_lyrics
from .queue.admission import writer
from .queue.cancellation import Cancellation
from .queue.chains import GenerationChains, ResolutionError
from .queue.manual_retry import ManualRetry


class SongCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(min_length=1, max_length=200)
    artist: str | None = Field(default=None, max_length=200)
    style_prompt: str = Field(default="", max_length=4000)
    negative_prompt: str | None = Field(default=None, max_length=4000)
    language: str | None = Field(default=None, max_length=32)
    tags: list[str] = Field(default_factory=list, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)
    collection_id: str | None = None


class SongPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    artist: str | None = Field(default=None, max_length=200)
    status: Literal["draft", "in_progress", "final", "archived"] | None = None
    style_prompt: str | None = Field(default=None, max_length=4000)
    negative_prompt: str | None = Field(default=None, max_length=4000)
    language: str | None = Field(default=None, max_length=32)
    tags: list[str] | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)
    collection_id: str | None = None


class CollectionCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1, max_length=200)


class CollectionPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str | None = Field(default=None, min_length=1, max_length=200)


class LyricsCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=32768)
    declaration: Literal["own", "assistant", "public_domain", "licensed"]
    source: Literal["manual", "assistant", "import"] = "manual"


class GenerationCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    song_id: str | None = None
    task: Literal["music.song", "music.instrumental"]
    lyrics: str | None = Field(default=None, max_length=32768)
    lyrics_declaration: (
        Literal["own", "assistant", "public_domain", "licensed"] | None
    ) = None
    style_prompt: str = Field(default="", max_length=4000)
    language: str | None = Field(default=None, max_length=32)
    params: dict = Field(default_factory=dict)
    seed: int | None = Field(default=None, ge=0, le=2**64 - 1)
    n_outputs: int = Field(default=1, ge=1, le=4)
    model_id: str | None = Field(default=None, max_length=128)


class TakePatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    rating: int | None = Field(default=None, ge=1, le=5)
    favorite: bool | None = None
    label: str | None = Field(default=None, max_length=200)


class MasterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    take_id: str


class EstimateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    task: str = Field(min_length=1, max_length=128)
    model_id: str = Field(min_length=1, max_length=128)
    params: dict = Field(default_factory=dict)
    seed: int | None = Field(default=None, ge=0, le=2**64 - 1)
    n_outputs: int = Field(default=1, ge=1, le=64)
    timeout_s: int = Field(default=300, gt=0, le=3600)


TRASH_RETENTION = timedelta(days=30)

DEFAULT_DURATION_S = 30
MAX_DURATION_S = 600
# Roles de asset con ruta real; el resto no publica URL.
ASSET_ROUTES = {"master": "master", "listen": "audio", "peaks": "peaks"}


def _params_with_duration(params, task):
    """Valida `duration_s` (0, 600] y aplica los 30 s por defecto en tareas music.*.

    Lanza ValueError si viene y no es un número finito en rango; el resolver
    sigue aplicando los límites más estrictos del descriptor del modelo.
    """
    params = dict(params)
    if "duration_s" in params:
        value = params["duration_s"]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0 < value <= MAX_DURATION_S
        ):
            raise ValueError("INVALID_DURATION")
    elif task.startswith("music."):
        params["duration_s"] = DEFAULT_DURATION_S
    return params


def _download_names(title, take_id, extension):
    """Devuelve (nombre ASCII seguro, nombre Unicode saneado) para `attachment`."""
    clean = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]+', "_", title or "")
    clean = re.sub(r"\.{2,}", ".", clean).strip(" ._") or "cancion"
    clean = clean[:80].strip(" ._") or "cancion"
    ascii_title = (
        unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode("ascii")
    )
    ascii_title = re.sub(r"[^A-Za-z0-9._ -]+", "_", ascii_title).strip(" ._")
    ascii_title = ascii_title or "cancion"
    return (
        f"{ascii_title}-{take_id}.{extension}",
        f"{clean}-{take_id}.{extension}",
    )


_OPENAPI_SONG = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "artist": {"type": ["string", "null"]},
        "status": {"type": "string"},
        "style_prompt": {"type": "string"},
        "collection_id": {"type": ["string", "null"]},
        "negative_prompt": {"type": ["string", "null"]},
        "language": {"type": ["string", "null"]},
        "tags": {"type": "array", "items": {}},
        "notes": {"type": ["string", "null"]},
        "current_lyrics_version_id": {"type": ["string", "null"]},
        "master_take_id": {"type": ["string", "null"]},
        "updated_at": {"type": "string"},
        "created_at": {"type": "string"},
        "deleted_at": {"type": ["string", "null"]},
        "purge_after": {"type": ["string", "null"]},
    },
    "required": [
        "id",
        "title",
        "artist",
        "collection_id",
        "status",
        "style_prompt",
        "negative_prompt",
        "language",
        "tags",
        "notes",
        "current_lyrics_version_id",
        "master_take_id",
        "updated_at",
        "created_at",
    ],
}
_OPENAPI_ASSET = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        "url": {"type": "string"},
        "media_type": {"type": "string"},
        "bytes": {"type": "integer", "minimum": 0},
        "sha256": {"type": "string"},
    },
    "required": ["role", "url", "media_type", "bytes", "sha256"],
}
_OPENAPI_TAKE = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "song_id": {"type": "string"},
        "job_id": {"type": ["string", "null"]},
        "lyrics_version_id": {"type": ["string", "null"]},
        "status": {"type": "string"},
        "batch_id": {"type": ["string", "null"]},
        "variant_index": {"type": "integer", "minimum": 0},
        "root_id": {"type": ["string", "null"]},
        "derivation": {"type": "string"},
        "task": {"type": "string"},
        "model_id": {"type": "string"},
        "model_version": {"type": ["string", "null"]},
        "seed": {"type": ["integer", "null"]},
        "params": {"type": "object"},
        "duration_s": {"type": ["number", "null"]},
        "sample_rate": {"type": ["integer", "null"]},
        "rating": {"type": ["integer", "null"]},
        "favorite": {"type": "boolean"},
        "label": {"type": ["string", "null"]},
        "commercial_use": {"type": "boolean"},
        "error_code": {"type": ["string", "null"]},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "assets": {"type": "object", "additionalProperties": _OPENAPI_ASSET},
        "lineage": {"type": "array", "items": {"type": "object"}},
    },
    "required": [
        "id",
        "song_id",
        "job_id",
        "lyrics_version_id",
        "status",
        "batch_id",
        "variant_index",
        "root_id",
        "derivation",
        "task",
        "model_id",
        "model_version",
        "seed",
        "params",
        "duration_s",
        "sample_rate",
        "rating",
        "favorite",
        "label",
        "commercial_use",
        "error_code",
        "created_at",
        "updated_at",
    ],
}

_OPENAPI_COLLECTION = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "cover_artwork_id": {"type": ["string", "null"]},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
    },
    "required": ["id", "name", "cover_artwork_id", "created_at", "updated_at"],
}
_OPENAPI_LYRICS = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "song_id": {"type": "string"},
        "text": {"type": "string"},
        "source": {"type": "string"},
        "declaration": {"type": "string"},
        "sha256": {"type": "string"},
        "created_at": {"type": "string"},
    },
    "required": [
        "id",
        "song_id",
        "text",
        "source",
        "declaration",
        "sha256",
        "created_at",
    ],
}


def _openapi_page(item_schema):
    return {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": item_schema},
            "next": {"type": ["string", "null"]},
        },
        "required": ["items", "next"],
    }


def _openapi_items(item_schema):
    return {
        "type": "object",
        "properties": {"items": {"type": "array", "items": item_schema}},
        "required": ["items"],
    }


def _json_response(schema, description):
    return {
        "description": description,
        "content": {"application/json": {"schema": schema}},
    }


def _model_response(model, description):
    return {"description": description, "model": model}


def _take_dict(take, *, assets=None, lineage=None):
    result = {
        "id": take.id,
        "song_id": take.song_id,
        "job_id": take.job_id,
        "lyrics_version_id": take.lyrics_version_id,
        "status": take.status,
        "batch_id": take.batch_id,
        "variant_index": take.variant_index,
        "root_id": take.root_id,
        "derivation": take.derivation,
        "task": take.task,
        "model_id": take.model_id,
        "model_version": take.model_version,
        "seed": take.seed,
        "params": take.params,
        "duration_s": take.duration_s,
        "sample_rate": take.sample_rate,
        "rating": take.rating,
        "favorite": take.favorite,
        "label": take.label,
        "commercial_use": take.commercial_use,
        "error_code": take.error_code,
        "created_at": take.created_at,
        "updated_at": take.updated_at,
    }
    if assets is not None:
        result["assets"] = {
            asset.role: {
                "role": asset.role,
                "media_type": asset.media_type,
                "bytes": asset.bytes,
                "sha256": asset.sha256,
                "url": f"/api/takes/{take.id}/{ASSET_ROUTES[asset.role]}",
            }
            for asset in assets
            if asset.role in ASSET_ROUTES
        }
    if lineage is not None:
        result["lineage"] = lineage
    return result


_DOWNLOAD_PARAM = {
    "name": "download",
    "in": "query",
    "required": False,
    "description": "1 o true: Content-Disposition attachment en lugar de inline",
    "schema": {"type": "string", "enum": ["0", "1", "true", "false"]},
}


def _responses():
    return {
        status: {
            "description": text,
            "content": {
                "application/problem+json": {"schema": ProblemDTO.model_json_schema()}
            },
        }
        for status, text in [
            (401, "Session required"),
            (403, "Forbidden"),
            (404, "Not found"),
            (409, "Conflict"),
            (422, "Invalid parameters"),
            (503, "Service unavailable"),
        ]
    }


def _auth(request):
    token = _credential(request, b"x-studio-session-token")
    registry = getattr(request.app.state, "session_registry", None)
    engine = getattr(request.app.state, "db", None)
    if registry is None or engine is None:
        raise SessionError("SERVICE_UNAVAILABLE")
    return registry.validate(token), engine


def _song_dict(song):
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "collection_id": song.collection_id,
        "status": song.status,
        "style_prompt": song.style_prompt,
        "negative_prompt": song.negative_prompt,
        "language": song.language,
        "tags": song.tags,
        "notes": song.notes,
        "current_lyrics_version_id": song.current_lyrics_version_id,
        "master_take_id": song.master_take_id,
        "created_at": song.created_at,
        "updated_at": song.updated_at,
    }


def _trash_song_dict(song):
    result = _song_dict(song)
    deleted_at = datetime.fromisoformat(song.deleted_at.replace("Z", "+00:00"))
    result["deleted_at"] = song.deleted_at
    result["purge_after"] = (
        (deleted_at + TRASH_RETENTION)
        .astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
    return result


def _owned_song(session, owner_id, song_id):
    song = session.scalar(
        select(models.Song).where(
            models.Song.id == song_id,
            models.Song.owner_id == owner_id,
            models.Song.deleted_at.is_(None),
            models.Song.is_dependency_only.is_(False),
        )
    )
    if song is None:
        raise SessionError("FORBIDDEN_SCOPE")
    return song


def _owned_deleted_song(session, owner_id, song_id):
    song = session.scalar(
        select(models.Song).where(
            models.Song.id == song_id,
            models.Song.owner_id == owner_id,
            models.Song.deleted_at.is_not(None),
            models.Song.is_dependency_only.is_(False),
        )
    )
    if song is None:
        raise SessionError("NOT_FOUND")
    return song


def _owned_collection(session, owner_id, collection_id):
    collection = session.scalar(
        select(models.Collection).where(
            models.Collection.id == collection_id,
            models.Collection.owner_id == owner_id,
            models.Collection.deleted_at.is_(None),
        )
    )
    if collection is None:
        raise SessionError("FORBIDDEN_SCOPE")
    return collection


def _create_song(request: Request, payload: SongCreateDTO):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            song = models.Song(
                owner_id=binding.owner_id,
                title=payload.title,
                artist=payload.artist,
                style_prompt=payload.style_prompt,
                negative_prompt=payload.negative_prompt,
                language=payload.language,
                tags=payload.tags,
                notes=payload.notes,
                collection_id=payload.collection_id,
            )
            if payload.collection_id is not None:
                _owned_collection(session, binding.owner_id, payload.collection_id)
            session.add(song)
            session.flush()
            result = _song_dict(song)
        return JSONResponse(result, status_code=201)
    except SessionError as error:
        return problem(error.code)


def _list_songs(request: Request):
    try:
        binding, engine = _auth(request)
        params = request.query_params
        try:
            limit = int(params.get("limit", "100"))
            if not 1 <= limit <= 100:
                raise ValueError
            cursor = params.get("cursor")
            if cursor:
                stamp, sep, song_id = cursor.partition("|")
                if not sep or not stamp or not song_id or len(song_id) != 26:
                    raise ValueError
            else:
                stamp = song_id = None
        except (TypeError, ValueError):
            return problem("INVALID_PARAMS")
        query_text = params.get("q")
        collection_id = params.get("collection_id")
        status_filter = params.get("status")
        model_id = params.get("model_id")
        favorite_filter = params.get("favorite")
        tag_filter = params.get("tag")
        updated_after = params.get("updated_after")
        updated_before = params.get("updated_before")
        if status_filter and status_filter not in {
            "draft",
            "in_progress",
            "final",
            "archived",
        }:
            return problem("INVALID_PARAMS")
        if favorite_filter not in {None, "true", "false"}:
            return problem("INVALID_PARAMS")
        with Session(engine) as session:
            conditions = [
                models.Song.owner_id == binding.owner_id,
                models.Song.deleted_at.is_(None),
                models.Song.is_dependency_only.is_(False),
            ]
            if collection_id:
                _owned_collection(session, binding.owner_id, collection_id)
                conditions.append(models.Song.collection_id == collection_id)
            if query_text:
                try:
                    matches = list(
                        session.execute(
                            text(
                                "SELECT song_id FROM song_fts WHERE song_fts MATCH :query LIMIT 1000"
                            ),
                            {"query": query_text},
                        ).scalars()
                    )
                except Exception:  # noqa: BLE001 - FTS parser boundary
                    return problem("INVALID_PARAMS")
                conditions.append(models.Song.id.in_(matches or [""]))
            if status_filter:
                conditions.append(models.Song.status == status_filter)
            if model_id:
                conditions.append(
                    exists(
                        select(models.Take.id).where(
                            models.Take.song_id == models.Song.id,
                            models.Take.model_id == model_id,
                            models.Take.deleted_at.is_(None),
                        )
                    )
                )
            if favorite_filter is not None:
                conditions.append(
                    exists(
                        select(models.Take.id).where(
                            models.Take.song_id == models.Song.id,
                            models.Take.favorite.is_(favorite_filter == "true"),
                            models.Take.deleted_at.is_(None),
                        )
                    )
                )
            if tag_filter:
                conditions.append(
                    text(
                        "EXISTS (SELECT 1 FROM json_each(song.tags) WHERE json_each.value = :tag_filter)"
                    )
                )
            if updated_after:
                conditions.append(models.Song.updated_at >= updated_after)
            if updated_before:
                conditions.append(models.Song.updated_at <= updated_before)
            if stamp is not None:
                conditions.append(
                    or_(
                        models.Song.updated_at < stamp,
                        (models.Song.updated_at == stamp) & (models.Song.id < song_id),
                    )
                )
            statement = (
                select(models.Song)
                .where(*conditions)
                .order_by(models.Song.updated_at.desc(), models.Song.id.desc())
                .limit(limit + 1)
            )
            if tag_filter:
                statement = statement.params(tag_filter=tag_filter)
            rows = list(session.scalars(statement))
        page, more = rows[:limit], rows[limit:]
        next_cursor = f"{page[-1].updated_at}|{page[-1].id}" if more and page else None
        return {"items": [_song_dict(song) for song in page], "next": next_cursor}
    except SessionError as error:
        return problem(error.code)


def _list_song_trash(request: Request):
    try:
        binding, engine = _auth(request)
        params = request.query_params
        try:
            limit = int(params.get("limit", "100"))
            if not 1 <= limit <= 100:
                raise ValueError
            cursor = params.get("cursor")
            if cursor:
                stamp, sep, song_id = cursor.partition("|")
                if not sep or not stamp or not song_id or len(song_id) != 26:
                    raise ValueError
            else:
                stamp = song_id = None
        except (TypeError, ValueError):
            return problem("INVALID_PARAMS")
        with Session(engine) as session:
            conditions = [
                models.Song.owner_id == binding.owner_id,
                models.Song.deleted_at.is_not(None),
                models.Song.is_dependency_only.is_(False),
            ]
            if stamp is not None:
                conditions.append(
                    or_(
                        models.Song.deleted_at < stamp,
                        (models.Song.deleted_at == stamp) & (models.Song.id < song_id),
                    )
                )
            rows = list(
                session.scalars(
                    select(models.Song)
                    .where(*conditions)
                    .order_by(models.Song.deleted_at.desc(), models.Song.id.desc())
                    .limit(limit + 1)
                )
            )
        page, more = rows[:limit], rows[limit:]
        next_cursor = f"{page[-1].deleted_at}|{page[-1].id}" if more and page else None
        return {"items": [_trash_song_dict(song) for song in page], "next": next_cursor}
    except SessionError as error:
        return problem(error.code)


def _get_song(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            return _song_dict(_owned_song(session, binding.owner_id, song_id))
    except SessionError as error:
        return problem(error.code)


def _patch_song(request: Request, song_id: str, payload: SongPatchDTO):
    try:
        binding, engine = _auth(request)
        changes = payload.model_dump(exclude_none=True)
        if not changes:
            raise ValueError("INVALID_PARAMS")
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_song(session, binding.owner_id, song_id)
            if "collection_id" in changes and changes["collection_id"] is not None:
                _owned_collection(session, binding.owner_id, changes["collection_id"])
            for key, value in changes.items():
                setattr(song, key, value)
            song.rev += 1
            session.flush()
            result = _song_dict(song)
        return result
    except SessionError as error:
        return problem(error.code)
    except ValueError:
        return problem("INVALID_PARAMS")


def _delete_song(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_song(session, binding.owner_id, song_id)
            song.deleted_at = models.utc_now()
            song.rev += 1
        return Response(status_code=204)
    except SessionError as error:
        return problem(error.code)


def _restore_song(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_deleted_song(session, binding.owner_id, song_id)
            song.deleted_at = None
            song.rev += 1
            session.flush()
            result = _song_dict(song)
        return result
    except SessionError as error:
        return problem(error.code)


def _purge_song(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_deleted_song(session, binding.owner_id, song_id)
            deleted_at = datetime.fromisoformat(song.deleted_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < deleted_at + TRASH_RETENTION:
                return problem("PURGE_RETENTION")
            related = (
                session.scalar(
                    select(models.LyricsVersion.id)
                    .where(models.LyricsVersion.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.Take.id)
                    .where(models.Take.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.Job.id).where(models.Job.song_id == song.id).limit(1)
                )
                or session.scalar(
                    select(models.Artwork.id)
                    .where(models.Artwork.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.VideoProject.id)
                    .where(models.VideoProject.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.Export.id)
                    .where(models.Export.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.PublicationIntent.id)
                    .where(models.PublicationIntent.song_id == song.id)
                    .limit(1)
                )
                or session.scalar(
                    select(models.PublicationIntentRevision.id)
                    .where(models.PublicationIntentRevision.song_id == song.id)
                    .limit(1)
                )
            )
            if related is not None:
                return problem("PURGE_PROTECTED")
            session.delete(song)
        return Response(status_code=204)
    except SessionError as error:
        return problem(error.code)


def _create_lyrics(request: Request, song_id: str, payload: LyricsCreateDTO):
    try:
        binding, engine = _auth(request)
        parsed = parse_lyrics(payload.text)
        if parsed["annotations"]:
            return problem("INVALID_PARAMS")
        digest = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_song(session, binding.owner_id, song_id)
            lyrics = models.LyricsVersion(
                owner_id=binding.owner_id,
                song_id=song.id,
                text=payload.text,
                source=payload.source,
                declaration=payload.declaration,
                sha256=digest,
            )
            session.add(lyrics)
            session.flush()
            song.current_lyrics_version_id = lyrics.id
            result = {
                "id": lyrics.id,
                "song_id": lyrics.song_id,
                "text": lyrics.text,
                "source": lyrics.source,
                "declaration": lyrics.declaration,
                "sha256": lyrics.sha256,
                "created_at": lyrics.created_at,
            }
        return JSONResponse(result, status_code=201)
    except SessionError as error:
        return problem(error.code)


def _list_lyrics(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            song = _owned_song(session, binding.owner_id, song_id)
            rows = session.scalars(
                select(models.LyricsVersion)
                .where(
                    models.LyricsVersion.song_id == song.id,
                    models.LyricsVersion.deleted_at.is_(None),
                )
                .order_by(models.LyricsVersion.created_at.desc())
            )
            return {
                "items": [
                    {
                        "id": row.id,
                        "song_id": row.song_id,
                        "text": row.text,
                        "source": row.source,
                        "declaration": row.declaration,
                        "sha256": row.sha256,
                        "created_at": row.created_at,
                    }
                    for row in rows
                ]
            }
    except SessionError as error:
        return problem(error.code)


async def _create_generation(request: Request, payload: GenerationCreateDTO):
    created_song = payload.song_id is None
    created_lyrics_id = None
    previous_lyrics_id = None
    song_id = payload.song_id
    try:
        binding, engine = _auth(request)
        if payload.task == "music.song" and (
            not payload.lyrics or payload.lyrics_declaration is None
        ):
            return problem("LYRICS_DECLARATION_REQUIRED")
        if payload.task == "music.song" and parse_lyrics(payload.lyrics)["warnings"]:
            return problem("INVALID_PARAMS")
        if payload.task == "music.instrumental" and payload.lyrics is not None:
            return problem("INVALID_PARAMS")
        try:
            base_params = _params_with_duration(payload.params, payload.task)
        except ValueError:
            return problem("INVALID_PARAMS")
        if payload.song_id is None:
            with Session(engine) as session, session.begin():
                writer(session)
                song = models.Song(
                    owner_id=binding.owner_id,
                    title="Sin título",
                    style_prompt=payload.style_prompt,
                    language=payload.language,
                )
                session.add(song)
                session.flush()
                song_id = song.id
        else:
            song_id = payload.song_id
            with Session(engine) as session:
                _owned_song(session, binding.owner_id, song_id)
        lyrics_version_id = None
        if payload.lyrics is not None:
            digest = hashlib.sha256(payload.lyrics.encode("utf-8")).hexdigest()
            with Session(engine) as session, session.begin():
                writer(session)
                song = _owned_song(session, binding.owner_id, song_id)
                previous_lyrics_id = song.current_lyrics_version_id
                version = models.LyricsVersion(
                    owner_id=binding.owner_id,
                    song_id=song.id,
                    text=payload.lyrics,
                    source="manual",
                    declaration=payload.lyrics_declaration,
                    sha256=digest,
                )
                session.add(version)
                session.flush()
                song.current_lyrics_version_id = version.id
                lyrics_version_id = version.id
                created_lyrics_id = version.id
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        if resolver is None:
            raise SessionError("SERVICE_UNAVAILABLE")
        chain = await GenerationChains(engine, binding.owner_id, resolver).create(
            song_id,
            task=payload.task,
            request={
                "params": {
                    **base_params,
                    "style": payload.style_prompt,
                    **(
                        {
                            "lyrics": payload.lyrics,
                            **(
                                {"language": payload.language}
                                if payload.language is not None
                                else {}
                            ),
                        }
                        if payload.task == "music.song"
                        else {}
                    ),
                },
                "seed": payload.seed if payload.seed is not None else 0,
                "n_outputs": payload.n_outputs,
            },
            model_id=payload.model_id,
            lyrics_version_id=lyrics_version_id,
        )
        return {
            "song_id": song_id,
            "generation_job_id": chain.generation_job_id,
            "post_job_id": chain.post_job_id,
            "take_ids": list(chain.take_ids),
            "beat_job_ids": list(chain.beat_job_ids),
        }
    except SessionError as error:
        return problem(error.code)
    except ResolutionError:
        # La canción/letra se crean antes de resolver porque el resolver exige
        # una entidad durable. Si la resolución falla, compensar sólo lo que
        # esta petición creó para no dejar borradores huérfanos.
        try:
            with Session(engine) as session, session.begin():
                writer(session)
                if created_song and song_id is not None:
                    song = session.get(models.Song, song_id)
                    if song is not None:
                        song.current_lyrics_version_id = None
                        session.flush()
                        for version in session.scalars(
                            select(models.LyricsVersion).where(
                                models.LyricsVersion.song_id == song_id
                            )
                        ):
                            session.delete(version)
                        session.delete(song)
                elif created_lyrics_id is not None:
                    song = session.get(models.Song, song_id)
                    if (
                        song is not None
                        and song.current_lyrics_version_id == created_lyrics_id
                    ):
                        song.current_lyrics_version_id = previous_lyrics_id
                    version = session.get(models.LyricsVersion, created_lyrics_id)
                    if version is not None:
                        session.delete(version)
        except Exception:  # noqa: BLE001 - preserve the original API error
            logging.getLogger(__name__).warning("generation.cleanup_failed")
        return problem("INVALID_PARAMS")


def _create_collection(request: Request, payload: CollectionCreateDTO):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            collection = models.Collection(owner_id=binding.owner_id, name=payload.name)
            session.add(collection)
            session.flush()
            return JSONResponse(
                {
                    "id": collection.id,
                    "name": collection.name,
                    "cover_artwork_id": collection.cover_artwork_id,
                    "created_at": collection.created_at,
                    "updated_at": collection.updated_at,
                },
                status_code=201,
            )
    except SessionError as error:
        return problem(error.code)


def _list_collections(request: Request):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            rows = session.scalars(
                select(models.Collection)
                .where(
                    models.Collection.owner_id == binding.owner_id,
                    models.Collection.deleted_at.is_(None),
                )
                .order_by(
                    models.Collection.updated_at.desc(), models.Collection.id.desc()
                )
            )
            return {
                "items": [
                    {
                        "id": row.id,
                        "name": row.name,
                        "cover_artwork_id": row.cover_artwork_id,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    }
                    for row in rows
                ]
            }
    except SessionError as error:
        return problem(error.code)


def _patch_collection(
    request: Request, collection_id: str, payload: CollectionPatchDTO
):
    try:
        binding, engine = _auth(request)
        if payload.name is None:
            return problem("INVALID_PARAMS")
        with Session(engine) as session, session.begin():
            writer(session)
            collection = _owned_collection(session, binding.owner_id, collection_id)
            collection.name = payload.name
            session.flush()
            return {
                "id": collection.id,
                "name": collection.name,
                "cover_artwork_id": collection.cover_artwork_id,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at,
            }
    except SessionError as error:
        return problem(error.code)


def _owned_take(session, owner_id, take_id):
    take = session.scalar(
        select(models.Take).where(
            models.Take.id == take_id,
            models.Take.owner_id == owner_id,
            models.Take.deleted_at.is_(None),
        )
    )
    if take is None:
        raise SessionError("FORBIDDEN_SCOPE")
    return take


def _asset_path(request, asset):
    root = request.app.state.settings.data_dir
    path = safe_path(root, f"{asset.path}")
    if not path.is_file() or path.is_symlink() or path.stat().st_size != asset.bytes:
        raise FileNotFoundError(asset.path)
    return path


def _take_detail(request: Request, take_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            take = _owned_take(session, binding.owner_id, take_id)
            assets = list(
                session.scalars(
                    select(models.Asset).where(
                        models.Asset.owner_id == binding.owner_id,
                        models.Asset.subject_type == "take",
                        models.Asset.subject_id == take.id,
                        models.Asset.deleted_at.is_(None),
                    )
                )
            )
            edges = list(
                session.scalars(
                    select(models.LineageEdge).where(
                        models.LineageEdge.owner_id == binding.owner_id,
                        models.LineageEdge.child_type == "take",
                        models.LineageEdge.child_id == take.id,
                        models.LineageEdge.deleted_at.is_(None),
                    )
                )
            )
            lineage = [
                {
                    "parent_type": edge.parent_type,
                    "parent_id": edge.parent_id,
                    "role": edge.role,
                    "section_map": edge.section_map,
                }
                for edge in edges
            ]
            return _take_dict(take, assets=assets, lineage=lineage)
    except SessionError as error:
        return problem(error.code)
    except (FileNotFoundError, ValueError):
        return problem("NOT_FOUND")


def _list_song_takes(request: Request, song_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            song = _owned_song(session, binding.owner_id, song_id)
            takes = list(
                session.scalars(
                    select(models.Take)
                    .where(
                        models.Take.owner_id == binding.owner_id,
                        models.Take.song_id == song.id,
                        models.Take.deleted_at.is_(None),
                    )
                    .order_by(
                        models.Take.variant_index.asc(), models.Take.created_at.desc()
                    )
                )
            )
            assets_by_take = {}
            for asset in session.scalars(
                select(models.Asset).where(
                    models.Asset.owner_id == binding.owner_id,
                    models.Asset.subject_type == "take",
                    models.Asset.subject_id.in_([take.id for take in takes]),
                    models.Asset.deleted_at.is_(None),
                )
            ):
                assets_by_take.setdefault(asset.subject_id, []).append(asset)
            return {
                "items": [
                    _take_dict(take, assets=assets_by_take.get(take.id, []))
                    for take in takes
                ]
            }
    except SessionError as error:
        return problem(error.code)


def _patch_take(request: Request, take_id: str, payload: TakePatchDTO):
    try:
        binding, engine = _auth(request)
        changes = payload.model_dump(exclude_none=True)
        if not changes:
            raise ValueError("INVALID_PARAMS")
        with Session(engine) as session, session.begin():
            writer(session)
            take = _owned_take(session, binding.owner_id, take_id)
            for key, value in changes.items():
                setattr(take, key, value)
            session.flush()
            return _take_dict(take)
    except SessionError as error:
        return problem(error.code)
    except ValueError as error:
        return problem(str(error))


def _delete_take(request: Request, take_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            take = _owned_take(session, binding.owner_id, take_id)
            take.deleted_at = models.utc_now()
            if take.status not in {"failed", "cancelled"}:
                take.status = "cancelled"
        return Response(status_code=204)
    except SessionError as error:
        return problem(error.code)


def _restore_take(request: Request, take_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            take = session.scalar(
                select(models.Take).where(
                    models.Take.id == take_id, models.Take.owner_id == binding.owner_id
                )
            )
            if take is None:
                raise SessionError("FORBIDDEN_SCOPE")
            if take.deleted_at is None:
                return _take_dict(take)
            song = _owned_song(session, binding.owner_id, take.song_id)
            take.deleted_at = None
            if take.status == "cancelled" and take.error_code is None:
                take.status = "ready" if take.id == song.master_take_id else "queued"
            return _take_dict(take)
    except SessionError as error:
        return problem(error.code)


def _asset_response(
    request: Request, take_id: str, role: str, *, range_header=None, download=False
):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            take = _owned_take(session, binding.owner_id, take_id)
            song_title = session.scalar(
                select(models.Song.title).where(models.Song.id == take.song_id)
            )
            asset = session.scalar(
                select(models.Asset).where(
                    models.Asset.owner_id == binding.owner_id,
                    models.Asset.subject_type == "take",
                    models.Asset.subject_id == take.id,
                    models.Asset.role == role,
                    models.Asset.deleted_at.is_(None),
                )
            )
            if asset is None:
                return problem("NOT_FOUND")
            path = _asset_path(request, asset)
            size = asset.bytes
            start, end = 0, size - 1
            status = 200
            if range_header:
                if not range_header.startswith("bytes=") or "," in range_header:
                    return Response(
                        status_code=416, headers={"Content-Range": f"bytes */{size}"}
                    )
                spec = range_header[6:]
                left, sep, right = spec.partition("-")
                try:
                    if not sep or (not left and not right):
                        raise ValueError
                    if left:
                        start = int(left)
                        end = int(right) if right else size - 1
                    else:
                        suffix = int(right)
                        if suffix <= 0:
                            raise ValueError
                        start, end = max(0, size - suffix), size - 1
                    if start < 0 or start >= size or end < start:
                        raise ValueError
                    end = min(end, size - 1)
                except (TypeError, ValueError):
                    return Response(
                        status_code=416, headers={"Content-Range": f"bytes */{size}"}
                    )
                status = 206
            with path.open("rb") as stream:
                stream.seek(start)
                payload = stream.read(end - start + 1)
        extension = {"audio/mpeg": "mp3", "audio/flac": "flac", "audio/wav": "wav"}.get(
            asset.media_type, "bin"
        )
        if download:
            safe_name, full_name = _download_names(song_title, take_id, extension)
            disposition = (
                f'attachment; filename="{safe_name}"; '
                f"filename*=UTF-8''{quote(full_name, safe='')}"
            )
        else:
            disposition = f'inline; filename="{take_id}-{role}.{extension}"'
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(payload)),
            "Content-Disposition": disposition,
        }
        if status == 206:
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        return Response(
            payload, status_code=status, media_type=asset.media_type, headers=headers
        )
    except SessionError as error:
        return problem(error.code)
    except (FileNotFoundError, ValueError):
        return problem("NOT_FOUND")


def _wants_download(request: Request):
    return request.query_params.get("download") in {"1", "true"}


def _take_audio(request: Request, take_id: str):
    return _asset_response(
        request,
        take_id,
        "listen",
        range_header=request.headers.get("range"),
        download=_wants_download(request),
    )


def _take_master(request: Request, take_id: str):
    return _asset_response(
        request,
        take_id,
        "master",
        range_header=request.headers.get("range"),
        download=_wants_download(request),
    )


def _take_peaks(request: Request, take_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            _owned_take(session, binding.owner_id, take_id)
            asset = session.scalar(
                select(models.Asset).where(
                    models.Asset.owner_id == binding.owner_id,
                    models.Asset.subject_type == "take",
                    models.Asset.subject_id == take_id,
                    models.Asset.role == "peaks",
                    models.Asset.deleted_at.is_(None),
                )
            )
            if asset is None:
                return problem("NOT_FOUND")
            path = _asset_path(request, asset)
            return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
    except SessionError as error:
        return problem(error.code)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return problem("NOT_FOUND")


def _take_analysis(request: Request, take_id: str):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session:
            _owned_take(session, binding.owner_id, take_id)
            rows = session.scalars(
                select(models.Analysis).where(
                    models.Analysis.owner_id == binding.owner_id,
                    models.Analysis.take_id == take_id,
                    models.Analysis.deleted_at.is_(None),
                )
            )
            return {
                "items": [
                    {
                        "id": row.id,
                        "kind": row.kind,
                        "analyzer_id": row.analyzer_id,
                        "analyzer_version": row.analyzer_version,
                        "lyrics_version_id": row.lyrics_version_id,
                        "data": row.data,
                    }
                    for row in rows
                ]
            }
    except SessionError as error:
        return problem(error.code)


def _set_master(request: Request, song_id: str, payload: MasterDTO):
    try:
        binding, engine = _auth(request)
        with Session(engine) as session, session.begin():
            writer(session)
            song = _owned_song(session, binding.owner_id, song_id)
            take = _owned_take(session, binding.owner_id, payload.take_id)
            if take.song_id != song.id or take.status != "ready":
                return problem("INVALID_PARAMS")
            song.master_take_id = take.id
            song.rev += 1
            return _song_dict(song)
    except SessionError as error:
        return problem(error.code)


def _cancel_job(request: Request, job_id: str):
    try:
        binding, engine = _auth(request)
        changed = Cancellation(engine, binding.owner_id).request(job_id)
        return JSONResponse(
            {"job_id": job_id, "cancel_requested": changed}, status_code=202
        )
    except SessionError as error:
        return problem(error.code)
    except ValueError:
        return problem("FORBIDDEN_SCOPE")


async def _retry_job(request: Request, job_id: str):
    try:
        binding, engine = _auth(request)
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        if resolver is None:
            return problem("SERVICE_UNAVAILABLE")
        result = await ManualRetry(engine, binding.owner_id, resolver).retry(job_id)
        if result is None:
            return problem("CONFLICT")
        return JSONResponse(
            {
                "generation_job_id": result.generation_job_id,
                "post_job_id": result.post_job_id,
                "take_ids": list(result.take_ids),
                "beat_job_ids": list(result.beat_job_ids),
            },
            status_code=202,
        )
    except SessionError as error:
        return problem(error.code)
    except ResolutionError:
        return problem("CONFLICT")


async def _list_models(request: Request):
    try:
        _binding, _engine = _auth(request)
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        if resolver is None:
            return problem("SERVICE_UNAVAILABLE")
        items = []
        for backend in resolver.backends.values():
            try:
                health, models = await resolver._catalog(backend)
            except Exception:  # noqa: BLE001,S112 - catalog is an observation boundary
                continue
            for model in models:
                value = model.model_dump(mode="json")
                value["engine_id"] = health.engine_id
                value["engine_version"] = health.engine_version
                items.append(value)
        return {"items": items}
    except SessionError as error:
        return problem(error.code)


async def _estimate_generation(request: Request, payload: EstimateDTO):
    try:
        _binding, _engine = _auth(request)
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        if resolver is None:
            return problem("SERVICE_UNAVAILABLE")
        try:
            params = _params_with_duration(payload.params, payload.task)
        except ValueError:
            return problem("INVALID_PARAMS")
        for backend in resolver.backends.values():
            try:
                _health, descriptors = await resolver._catalog(backend)
            except Exception:  # noqa: BLE001,S112 - catalog is an observation boundary
                continue
            if not any(model.id == payload.model_id for model in descriptors):
                continue
            job_id = models.new_id()
            estimate = await backend.estimate(
                JobRequest(
                    job_id=job_id,
                    task=payload.task,
                    model_id=payload.model_id,
                    inputs=[],
                    params=params,
                    seed=payload.seed,
                    n_outputs=payload.n_outputs,
                    output_dir=f"tmp/{job_id}",
                    timeout_s=payload.timeout_s,
                )
            )
            return estimate.model_dump(mode="json")
        return problem("INVALID_PARAMS")
    except SessionError as error:
        return problem(error.code)
    except (TypeError, ValueError):
        return problem("INVALID_PARAMS")
    except Exception:  # noqa: BLE001 - engine observation is an availability boundary
        return problem("SERVICE_UNAVAILABLE")


async def _unload_system(request: Request):
    try:
        _binding, _engine = _auth(request)
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        if resolver is None:
            return problem("SERVICE_UNAVAILABLE")
        freed = 0.0
        for backend in resolver.backends.values():
            result = await backend.unload()
            freed += result.freed_mb
        return {"freed_mb": freed}
    except SessionError as error:
        return problem(error.code)
    except Exception:  # noqa: BLE001 - engine observation is an availability boundary
        return problem("SERVICE_UNAVAILABLE")


async def _system_info(request: Request):
    try:
        binding, engine = _auth(request)
        runtime = getattr(request.app.state, "queue", None)
        resolver = getattr(runtime, "resolver", None)
        engines = []
        models_info = []
        gpu = None
        for backend in getattr(resolver, "backends", {}).values():
            try:
                health = await backend.health()
                health_data = health.model_dump(mode="json")
                engines.append(health_data)
                if gpu is None and isinstance(health_data.get("gpu"), dict):
                    gpu = health_data["gpu"]
            except Exception:  # noqa: BLE001 - status endpoint is best effort
                engines.append({"state": "error"})
            if resolver is not None:
                try:
                    _health, descriptors = await resolver._catalog(backend)
                    for descriptor in descriptors:
                        value = descriptor.model_dump(mode="json")
                        value["tasks"] = {
                            task: {
                                "verified": details.get("verified", False)
                                if isinstance(details, dict)
                                else getattr(details, "verified", False),
                                "device": details.get("device")
                                if isinstance(details, dict)
                                else getattr(details, "device", None),
                                "params_schema": details.get("params_schema")
                                if isinstance(details, dict)
                                else getattr(details, "params_schema", None),
                                "features": details.get("features", {})
                                if isinstance(details, dict)
                                else getattr(details, "features", {}),
                            }
                            for task, details in value.get("tasks", {}).items()
                        }
                        models_info.append(value)
                except Exception:  # noqa: BLE001,S110 - catalog is a best-effort view
                    pass
        with Session(engine) as session:
            queue = {
                status: session.scalar(
                    select(models.Job.id)
                    .where(
                        models.Job.owner_id == binding.owner_id,
                        models.Job.status == status,
                    )
                    .limit(1)
                )
                is not None
                for status in ("queued", "blocked", "running")
            }
        disk = shutil.disk_usage(request.app.state.settings.data_dir)
        ram = {"total_bytes": None, "free_bytes": None}
        try:
            memory = {}
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                key, value = line.split(":", 1)
                memory[key] = int(value.strip().split()[0]) * 1024
            ram = {
                "total_bytes": memory.get("MemTotal"),
                "free_bytes": memory.get("MemAvailable"),
            }
        except (FileNotFoundError, OSError, ValueError):
            pass
        return {
            "gpu": gpu,
            "ram": ram,
            "engines": engines,
            "models": models_info,
            "queue": queue,
            "disk": {"total_bytes": disk.total, "free_bytes": disk.free},
        }
    except SessionError as error:
        return problem(error.code)


def register_domain_routes(application):
    application.add_api_route(
        "/api/collections",
        _list_collections,
        methods=["GET"],
        operation_id="list_collections",
        responses={
            200: _json_response(_openapi_items(_OPENAPI_COLLECTION), "Collections"),
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/collections",
        _create_collection,
        methods=["POST"],
        operation_id="create_collection",
        response_model=None,
        status_code=201,
        responses={201: _json_response(_OPENAPI_COLLECTION, "Created"), **_responses()},
    )
    application.add_api_route(
        "/api/collections/{collection_id}",
        _patch_collection,
        methods=["PATCH"],
        operation_id="patch_collection",
        responses={
            200: _json_response(_OPENAPI_COLLECTION, "Collection"),
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/songs",
        _list_songs,
        methods=["GET"],
        operation_id="list_songs",
        responses={
            200: {
                "description": "Song page",
                "content": {
                    "application/json": {"schema": _openapi_page(_OPENAPI_SONG)}
                },
            },
            **_responses(),
        },
        openapi_extra={
            "parameters": [
                {
                    "name": "q",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "cursor",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
                {
                    "name": "collection_id",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "status",
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "string",
                        "enum": ["draft", "in_progress", "final", "archived"],
                    },
                },
                {
                    "name": "model_id",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "favorite",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "boolean"},
                },
                {
                    "name": "tag",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "updated_after",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "format": "date-time"},
                },
                {
                    "name": "updated_before",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "format": "date-time"},
                },
            ]
        },
    )
    application.add_api_route(
        "/api/songs",
        _create_song,
        methods=["POST"],
        operation_id="create_song",
        response_model=None,
        responses={201: {"description": "Created"}, **_responses()},
    )
    application.add_api_route(
        "/api/songs/trash",
        _list_song_trash,
        methods=["GET"],
        operation_id="list_song_trash",
        responses={
            200: {
                "description": "Trash page",
                "content": {
                    "application/json": {"schema": _openapi_page(_OPENAPI_SONG)}
                },
            },
            **_responses(),
        },
        openapi_extra={
            "parameters": [
                {
                    "name": "cursor",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
            ]
        },
    )
    application.add_api_route(
        "/api/songs/{song_id}",
        _get_song,
        methods=["GET"],
        operation_id="get_song",
        responses={
            200: {
                "description": "Song",
                "content": {"application/json": {"schema": _OPENAPI_SONG}},
            },
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/songs/{song_id}/restore",
        _restore_song,
        methods=["POST"],
        operation_id="restore_song",
        responses={200: _json_response(_OPENAPI_SONG, "Restored song"), **_responses()},
    )
    application.add_api_route(
        "/api/songs/{song_id}/purge",
        _purge_song,
        methods=["POST"],
        operation_id="purge_song",
        status_code=204,
        responses=_responses(),
    )
    application.add_api_route(
        "/api/songs/{song_id}",
        _patch_song,
        methods=["PATCH"],
        operation_id="patch_song",
        responses={200: _json_response(_OPENAPI_SONG, "Song"), **_responses()},
    )
    application.add_api_route(
        "/api/songs/{song_id}",
        _delete_song,
        methods=["DELETE"],
        operation_id="delete_song",
        status_code=204,
        responses=_responses(),
    )
    application.add_api_route(
        "/api/songs/{song_id}/lyrics",
        _list_lyrics,
        methods=["GET"],
        operation_id="list_song_lyrics",
        responses={
            200: _json_response(_openapi_items(_OPENAPI_LYRICS), "Lyrics versions"),
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/songs/{song_id}/lyrics",
        _create_lyrics,
        methods=["POST"],
        operation_id="create_song_lyrics",
        responses={201: {"description": "Created"}, **_responses()},
    )
    application.add_api_route(
        "/api/generations",
        _create_generation,
        methods=["POST"],
        operation_id="create_generation",
        responses={202: {"description": "Queued"}, **_responses()},
        status_code=202,
    )
    application.add_api_route(
        "/api/takes/{take_id}",
        _take_detail,
        methods=["GET"],
        operation_id="get_take",
        responses={
            200: {
                "description": "Take",
                "content": {"application/json": {"schema": _OPENAPI_TAKE}},
            },
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/songs/{song_id}/takes",
        _list_song_takes,
        methods=["GET"],
        operation_id="list_song_takes",
        responses={
            200: {
                "description": "Takes",
                "content": {
                    "application/json": {"schema": _openapi_items(_OPENAPI_TAKE)}
                },
            },
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/takes/{take_id}",
        _patch_take,
        methods=["PATCH"],
        operation_id="patch_take",
        responses={200: _json_response(_OPENAPI_TAKE, "Take"), **_responses()},
    )
    application.add_api_route(
        "/api/takes/{take_id}",
        _delete_take,
        methods=["DELETE"],
        operation_id="delete_take",
        status_code=204,
        responses=_responses(),
    )
    application.add_api_route(
        "/api/takes/{take_id}/restore",
        _restore_take,
        methods=["POST"],
        operation_id="restore_take",
        responses={200: _json_response(_OPENAPI_TAKE, "Restored take"), **_responses()},
    )
    application.add_api_route(
        "/api/takes/{take_id}/audio",
        _take_audio,
        methods=["GET"],
        operation_id="get_take_audio",
        response_class=Response,
        openapi_extra={"parameters": [_DOWNLOAD_PARAM]},
        responses={
            200: {
                "description": "MPEG audio",
                "content": {
                    "audio/mpeg": {"schema": {"type": "string", "format": "binary"}}
                },
            },
            206: {
                "description": "Partial MPEG audio",
                "content": {
                    "audio/mpeg": {"schema": {"type": "string", "format": "binary"}}
                },
            },
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/takes/{take_id}/master",
        _take_master,
        methods=["GET"],
        operation_id="get_take_master",
        response_class=Response,
        openapi_extra={"parameters": [_DOWNLOAD_PARAM]},
        responses={
            200: {
                "description": "FLAC audio",
                "content": {
                    "audio/flac": {"schema": {"type": "string", "format": "binary"}}
                },
            },
            206: {
                "description": "Partial FLAC audio",
                "content": {
                    "audio/flac": {"schema": {"type": "string", "format": "binary"}}
                },
            },
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/takes/{take_id}/peaks",
        _take_peaks,
        methods=["GET"],
        operation_id="get_take_peaks",
        responses={200: _model_response(PeaksDTO, "Peaks"), **_responses()},
    )
    application.add_api_route(
        "/api/takes/{take_id}/analysis",
        _take_analysis,
        methods=["GET"],
        operation_id="get_take_analysis",
        responses=_responses(),
    )
    application.add_api_route(
        "/api/songs/{song_id}/master",
        _set_master,
        methods=["POST"],
        operation_id="set_song_master",
        responses=_responses(),
    )
    application.add_api_route(
        "/api/jobs/{job_id}/cancel",
        _cancel_job,
        methods=["POST"],
        operation_id="cancel_job",
        status_code=202,
        responses=_responses(),
    )
    application.add_api_route(
        "/api/jobs/{job_id}/retry",
        _retry_job,
        methods=["POST"],
        operation_id="retry_job",
        status_code=202,
        responses=_responses(),
    )
    application.add_api_route(
        "/api/models",
        _list_models,
        methods=["GET"],
        operation_id="list_models",
        responses={200: _model_response(ModelsDTO, "Models"), **_responses()},
    )
    application.add_api_route(
        "/api/generations/estimate",
        _estimate_generation,
        methods=["POST"],
        operation_id="estimate_generation",
        responses={
            200: _model_response(EstimateResultDTO, "Estimate"),
            **_responses(),
        },
    )
    application.add_api_route(
        "/api/system/unload",
        _unload_system,
        methods=["POST"],
        operation_id="unload_system",
        responses=_responses(),
    )
    application.add_api_route(
        "/api/system",
        _system_info,
        methods=["GET"],
        operation_id="system_info",
        responses={
            200: _model_response(SystemInfoDTO, "System status"),
            **_responses(),
        },
    )
