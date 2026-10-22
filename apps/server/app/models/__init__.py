"""Entidades persistentes del estudio, sin cascadas de borrado."""

import secrets
from datetime import datetime, timezone

from engine_contract import Event, JobRequest, LoadRequest
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DefaultClause,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates
from sqlalchemy.types import TypeDecorator

from app.migrations.cpu_publication_invariants import validate_connection, validate_row
from app.migrations.job_attempt_invariants import validate_attempt, validate_contract
from app.worker.contracts import CapturedProvenance, PostPlan, PreparedPackage


class Seed(TypeDecorator):
    """Entero sin límite, almacenado como decimal canónico en SQLite."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str) and value.isascii() and value.isdecimal():
            value = int(value)
        if type(value) is not int or value < 0:
            raise ValueError("Seed must be a non-negative integer")
        return str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else int(value)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def new_id() -> str:
    value = (
        int(datetime.now(timezone.utc).timestamp() * 1000) << 80
    ) | secrets.randbits(80)
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return "".join(alphabet[(value >> shift) & 31] for shift in range(125, -1, -5))


class Base(DeclarativeBase):
    pass


class Common:
    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("user.id", deferrable=True, initially="DEFERRED"), index=True
    )
    created_at: Mapped[str] = mapped_column(Text, default=utc_now)
    updated_at: Mapped[str] = mapped_column(Text, default=utc_now, onupdate=utc_now)
    deleted_at: Mapped[str | None] = mapped_column(Text, index=True)


def ref(target):
    return mapped_column(
        ForeignKey(target, deferrable=True, initially="DEFERRED"), index=True
    )


def enum(column, values):
    return CheckConstraint(
        f"{column} IN ({','.join(repr(v) for v in values.split())})",
        name=f"ck_{column}",
    )


class User(Common, Base):
    __tablename__ = "user"
    name: Mapped[str] = mapped_column(Text, unique=True)
    __table_args__ = (CheckConstraint("name = 'local'"),)


class Collection(Common, Base):
    __tablename__ = "collection"
    name: Mapped[str] = mapped_column(Text)
    cover_artwork_id: Mapped[str | None] = ref("artwork.id")


class Song(Common, Base):
    __tablename__ = "song"
    is_dependency_only: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    snapshot_dirty: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )
    snapshot_generation: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    collection_id: Mapped[str | None] = ref("collection.id")
    title: Mapped[str] = mapped_column(Text)
    artist: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    style_prompt: Mapped[str] = mapped_column(Text, default="")
    negative_prompt: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    current_lyrics_version_id: Mapped[str | None] = ref("lyrics_version.id")
    master_take_id: Mapped[str | None] = ref("take.id")
    cover_artwork_id: Mapped[str | None] = ref("artwork.id")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    rev: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        enum("status", "draft in_progress final archived"),
        CheckConstraint("rev >= 1"),
        Index("ix_song_library", "owner_id", "deleted_at", "updated_at"),
    )


class LyricsVersion(Common, Base):
    __tablename__ = "lyrics_version"
    song_id: Mapped[str] = ref("song.id")
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    declaration: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[str | None] = ref("lyrics_version.id")
    sha256: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        enum("source", "manual assistant import"),
        enum("declaration", "own assistant public_domain licensed"),
    )


class Take(Common, Base):
    __tablename__ = "take"
    song_id: Mapped[str] = ref("song.id")
    job_id: Mapped[str] = ref("job.id")
    lyrics_version_id: Mapped[str | None] = ref("lyrics_version.id")
    status: Mapped[str] = mapped_column(Text, default="queued")
    batch_id: Mapped[str] = mapped_column(String(26), index=True)
    variant_index: Mapped[int] = mapped_column(Integer, default=0)
    root_id: Mapped[str] = ref("take.id")
    derivation: Mapped[str] = mapped_column(Text)
    task: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(Text)
    seed: Mapped[int] = mapped_column(Seed)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_s: Mapped[float | None]
    sample_rate: Mapped[int | None]
    rating: Mapped[int | None]
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    label: Mapped[str | None] = mapped_column(Text)
    commercial_use: Mapped[bool] = mapped_column(Boolean)
    error_code: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        enum("status", "queued running ready failed cancelled"),
        enum(
            "derivation", "original variant extend repaint cover complete remaster edit"
        ),
        CheckConstraint("variant_index >= 0"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5"),
        CheckConstraint("duration_s IS NULL OR duration_s >= 0"),
        CheckConstraint("sample_rate IS NULL OR sample_rate > 0"),
    )


class LineageEdge(Common, Base):
    __tablename__ = "lineage_edge"
    child_type: Mapped[str] = mapped_column(Text)
    child_id: Mapped[str] = mapped_column(String(26), index=True)
    parent_type: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[str] = mapped_column(String(26), index=True)
    role: Mapped[str] = mapped_column(Text)
    section_map: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    __table_args__ = (
        UniqueConstraint("child_type", "child_id", "parent_type", "parent_id", "role"),
        CheckConstraint("child_type != parent_type OR child_id != parent_id"),
    )


class Asset(Common, Base):
    __tablename__ = "asset"
    subject_type: Mapped[str] = mapped_column(Text)
    subject_id: Mapped[str] = mapped_column(String(26), index=True)
    role: Mapped[str] = mapped_column(Text)
    path: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    bytes: Mapped[int] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (
        enum(
            "subject_type",
            "take artwork shot_version render export character lora cli_run",
        ),
        CheckConstraint("bytes >= 0"),
    )


class Upload(Common, Base):
    __tablename__ = "upload"
    kind: Mapped[str] = mapped_column(Text)
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    rights: Mapped[str] = mapped_column(Text)
    real_person: Mapped[bool] = mapped_column(Boolean, default=False)
    consent: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        enum("kind", "audio image"),
        enum("rights", "own licensed consented public_domain"),
        enum("consent", "self consented n_a"),
        CheckConstraint("NOT real_person OR consent IN ('self','consented')"),
    )


class Analysis(Common, Base):
    __tablename__ = "analysis"
    take_id: Mapped[str] = ref("take.id")
    kind: Mapped[str] = mapped_column(Text)
    analyzer_id: Mapped[str] = mapped_column(Text)
    analyzer_version: Mapped[str] = mapped_column(Text)
    lyrics_version_id: Mapped[str | None] = ref("lyrics_version.id")
    data: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (
        UniqueConstraint("take_id", "kind", "analyzer_id"),
        enum("kind", "beats sections key loudness lyrics_timing"),
    )


class Artwork(Common, Base):
    __tablename__ = "artwork"
    song_id: Mapped[str | None] = ref("song.id")
    kind: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    upload_id: Mapped[str | None] = ref("upload.id")
    job_id: Mapped[str | None] = ref("job.id")
    prompt: Mapped[str | None] = mapped_column(Text)
    model_id: Mapped[str | None] = mapped_column(Text)
    seed: Mapped[int | None] = mapped_column(Seed)
    rights: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        enum("kind", "cover keyframe background"),
        enum("source", "generated upload"),
        enum("rights", "own licensed consented public_domain"),
    )


class Character(Common, Base):
    __tablename__ = "character"
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    consent: Mapped[str] = mapped_column(Text)
    consent_note: Mapped[str | None] = mapped_column(Text)
    sheet_artwork_id: Mapped[str | None] = ref("artwork.id")
    lora_asset_id: Mapped[str | None] = ref("asset.id")
    __table_args__ = (
        enum("kind", "real_person fictional animal object"),
        enum("consent", "self consented fictional"),
        CheckConstraint("kind != 'real_person' OR consent IN ('self','consented')"),
    )


class CharacterRef(Common, Base):
    __tablename__ = "character_ref"
    character_id: Mapped[str] = ref("character.id")
    upload_id: Mapped[str | None] = ref("upload.id")
    artwork_id: Mapped[str | None] = ref("artwork.id")
    view: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("(upload_id IS NULL) != (artwork_id IS NULL)"),
        CheckConstraint(
            "view IS NULL OR view IN ('front','profile','full','expression')"
        ),
    )


class Preset(Common, Base):
    __tablename__ = "preset"
    kind: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (enum("kind", "style voice visual full"),)


class VideoProject(Common, Base):
    __tablename__ = "video_project"
    song_id: Mapped[str] = ref("song.id")
    take_id: Mapped[str] = ref("take.id")
    title: Mapped[str] = mapped_column(Text)
    aspect: Mapped[str] = mapped_column(Text)
    level_preset: Mapped[str] = mapped_column(Text)
    visual_style: Mapped[str] = mapped_column(Text)
    treatment: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="planning")
    timeline: Mapped[dict] = mapped_column(JSON)
    rev: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        enum("aspect", "16:9 9:16 1:1"),
        enum("level_preset", "N0 N1 N2 N3"),
        enum("status", "planning generating editing rendered"),
        CheckConstraint("rev >= 1"),
    )


class VideoCharacter(Common, Base):
    __tablename__ = "video_character"
    video_project_id: Mapped[str] = ref("video_project.id")
    character_id: Mapped[str] = ref("character.id")
    role: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("video_project_id", "character_id", "role"),
        enum("role", "performer cast"),
    )


class Shot(Common, Base):
    __tablename__ = "shot"
    video_project_id: Mapped[str] = ref("video_project.id")
    key: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    current_version_id: Mapped[str | None] = ref("shot_version.id")
    __table_args__ = (
        UniqueConstraint("video_project_id", "key"),
        enum("kind", "lyric still still_motion i2v singer t2v"),
    )


class ShotVersion(Common, Base):
    __tablename__ = "shot_version"
    shot_id: Mapped[str] = ref("shot.id")
    job_id: Mapped[str | None] = ref("job.id")
    prompt: Mapped[str] = mapped_column(Text)
    camera: Mapped[str | None] = mapped_column(Text)
    seed: Mapped[int | None] = mapped_column(Seed)
    model_id: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(Text, default="local")
    status: Mapped[str] = mapped_column(Text, default="queued")
    keyframe_asset_id: Mapped[str | None] = ref("asset.id")
    clip_asset_id: Mapped[str | None] = ref("asset.id")
    focus_point: Mapped[list | None] = mapped_column(JSON(none_as_null=True))
    __table_args__ = (enum("status", "queued running ready failed cancelled"),)


class Render(Common, Base):
    __tablename__ = "render"
    video_project_id: Mapped[str] = ref("video_project.id")
    timeline_rev: Mapped[int] = mapped_column(Integer)
    aspect: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    subtitles: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued")
    asset_id: Mapped[str | None] = ref("asset.id")
    __table_args__ = (
        enum("aspect", "16:9 9:16 1:1"),
        enum("kind", "full short preview"),
        enum("subtitles", "burned srt none"),
        enum("status", "queued running ready failed cancelled"),
        CheckConstraint("timeline_rev >= 1"),
    )


class Export(Common, Base):
    __tablename__ = "export"
    song_id: Mapped[str] = ref("song.id")
    kind: Mapped[str] = mapped_column(Text)
    target: Mapped[str | None] = mapped_column(Text)
    asset_id: Mapped[str | None] = ref("asset.id")
    expires_at: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        enum("kind", "audio stems video lyrics project_zip"),
        CheckConstraint(
            "target IS NULL OR target IN ('streaming','broadcast','podcast')"
        ),
    )


class Job(Common, Base):
    __tablename__ = "job"
    task: Mapped[str] = mapped_column(Text)
    lane: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(Text, default="normal")
    not_before: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued")
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    engine_id: Mapped[str | None] = mapped_column(Text)
    model_id: Mapped[str | None] = mapped_column(Text)
    request: Mapped[dict] = mapped_column(JSON)
    stage: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[float | None]
    error_code: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    telemetry: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    song_id: Mapped[str | None] = ref("song.id")
    started_at: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[str | None] = mapped_column(Text)
    cancel_requested_at: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        enum("lane", "gpu cpu remote"),
        enum("priority", "interactive normal batch nightly"),
        enum("status", "queued blocked running succeeded failed cancelled interrupted"),
        CheckConstraint(
            "attempt >= 0 AND max_attempts >= 1 AND attempt <= max_attempts"
        ),
        CheckConstraint("progress IS NULL OR progress BETWEEN 0 AND 1"),
        Index("ix_job_schedule", "lane", "status", "not_before"),
    )


class ContractJSON(TypeDecorator):
    """JSON contractual tipado; nunca normaliza una petición inválida."""

    impl = JSON
    cache_ok = True

    def __init__(self, kind):
        super().__init__(none_as_null=True)
        self.kind = kind

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return validate_contract(value, self.kind).model_dump(mode="json")

    def process_result_value(self, value, dialect):
        return None if value is None else validate_contract(value, self.kind)


class WorkerJSON(TypeDecorator):
    """Contratos privados reales, separados de los contratos de engine."""

    impl = JSON
    cache_ok = True

    def __init__(self, model):
        super().__init__(none_as_null=True)
        self.model = model

    def process_bind_param(self, value, dialect):
        return (
            None
            if value is None
            else self.model.model_validate(value).model_dump(mode="json")
        )

    def process_result_value(self, value, dialect):
        return None if value is None else self.model.model_validate(value)


class JobAttempt(Common, Base):
    __tablename__ = "job_attempt"
    job_id: Mapped[str] = ref("job.id")
    ordinal: Mapped[int] = mapped_column(Integer)
    engine_id: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(Text)
    mode: Mapped[str | None] = mapped_column(Text)
    engine_request: Mapped[JobRequest] = mapped_column(ContractJSON("request"))
    load_options: Mapped[LoadRequest] = mapped_column(ContractJSON("load"))
    last_seq: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(Text, default="prepared")
    terminal: Mapped[Event | None] = mapped_column(ContractJSON("event"))
    provenance: Mapped[CapturedProvenance | None] = mapped_column(
        WorkerJSON(CapturedProvenance)
    )
    provenance_sha256: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (
        UniqueConstraint("job_id", "ordinal"),
        enum("status", "prepared submitted succeeded failed cancelled"),
        CheckConstraint("typeof(ordinal)='integer' AND ordinal>=1"),
        CheckConstraint("typeof(last_seq)='integer' AND last_seq>=0"),
        CheckConstraint("length(engine_id)>0 AND length(model_id)>0"),
        *(
            CheckConstraint(
                f"{key} IS NULL OR (json_valid({key}) AND json_type({key})='object')"
            )
            for key in ("engine_request", "load_options", "terminal")
        ),
    )

    @validates("engine_request", "load_options", "terminal")
    def typed_contract(self, key, value):
        if value is None:
            return None
        return validate_contract(
            value,
            {"engine_request": "request", "load_options": "load", "terminal": "event"}[
                key
            ],
        )


@event.listens_for(JobAttempt, "before_insert")
@event.listens_for(JobAttempt, "before_update")
def validate_job_attempt(mapper, connection, target):
    # Los defaults de SQLAlchemy se materializan después del hook.
    if inspect(target).pending:
        for key, default in (
            ("id", new_id),
            ("created_at", utc_now),
            ("updated_at", utc_now),
            ("last_seq", lambda: 0),
            ("status", lambda: "prepared"),
        ):
            if getattr(target, key) is None:
                setattr(target, key, default())
    validate_attempt(
        {
            column.name: getattr(target, column.name)
            for column in JobAttempt.__table__.columns
        }
    )


class CpuExecution(Common, Base):
    __tablename__ = "cpu_execution"
    job_id: Mapped[str] = ref("job.id")
    ordinal: Mapped[int] = mapped_column(Integer)
    handler: Mapped[str] = mapped_column(Text, default="post.audio")
    handler_version: Mapped[int] = mapped_column(Integer, default=1)
    contract_version: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(Text, default="prepared")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    plan: Mapped[PostPlan] = mapped_column(WorkerJSON(PostPlan))
    plan_sha256: Mapped[str] = mapped_column(String(64))
    outcome: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    error_code: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[str | None] = mapped_column(Text)
    supervisor_epoch: Mapped[str | None] = mapped_column(Text)
    lease_token: Mapped[str | None] = mapped_column(Text)
    process_identity: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    cleanup_state: Mapped[str] = mapped_column(Text, default="unknown")
    __table_args__ = (UniqueConstraint("job_id", "ordinal"),)


class PublicationIntent(Common, Base):
    __tablename__ = "publication_intent"
    song_id: Mapped[str] = ref("song.id")
    take_id: Mapped[str] = ref("take.id")
    output_index: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Seed)
    state: Mapped[str] = mapped_column(Text, default="reserved")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    active_revision_id: Mapped[str | None] = ref("publication_intent_revision.id")
    error_code: Mapped[str | None] = mapped_column(Text)
    committed_at: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("take_id"),)


class PublicationIntentRevision(Common, Base):
    __tablename__ = "publication_intent_revision"
    intent_id: Mapped[str] = ref("publication_intent.id")
    cpu_execution_id: Mapped[str] = ref("cpu_execution.id")
    song_id: Mapped[str] = ref("song.id")
    post_job_id: Mapped[str] = ref("job.id")
    generation_job_id: Mapped[str] = ref("job.id")
    winning_attempt_id: Mapped[str] = ref("job_attempt.id")
    winning_ordinal: Mapped[int] = mapped_column(Integer)
    terminal_seq: Mapped[int] = mapped_column(Integer)
    terminal_sha256: Mapped[str] = mapped_column(String(64))
    take_id: Mapped[str] = ref("take.id")
    output_index: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Seed)
    provenance_sha256: Mapped[str] = mapped_column(String(64))
    source_sha256: Mapped[str] = mapped_column(String(64))
    stage_path: Mapped[str] = mapped_column(Text)
    final_path: Mapped[str] = mapped_column(Text)
    package: Mapped[PreparedPackage | None] = mapped_column(WorkerJSON(PreparedPackage))
    package_sha256: Mapped[str | None] = mapped_column(String(64))
    error_code: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint(
            "intent_id", "generation_job_id", "winning_attempt_id", "output_index"
        ),
    )


@event.listens_for(CpuExecution, "before_insert")
@event.listens_for(CpuExecution, "before_update")
@event.listens_for(PublicationIntentRevision, "before_insert")
@event.listens_for(PublicationIntentRevision, "before_update")
@event.listens_for(JobAttempt, "before_insert")
@event.listens_for(JobAttempt, "before_update")
def validate_worker_row(mapper, connection, target):
    if inspect(target).pending:
        for key, default in (
            ("id", new_id),
            ("created_at", utc_now),
            ("updated_at", utc_now),
        ):
            if getattr(target, key) is None:
                setattr(target, key, default())
    row = {
        column.name: getattr(target, column.name) for column in target.__table__.columns
    }
    validate_row(target.__tablename__, row)
    validate_connection(connection, target.__tablename__, row)


class JobDependency(Common, Base):
    __tablename__ = "job_dependency"
    job_id: Mapped[str] = ref("job.id")
    depends_on_job_id: Mapped[str] = ref("job.id")
    __table_args__ = (
        UniqueConstraint("job_id", "depends_on_job_id"),
        CheckConstraint("job_id != depends_on_job_id"),
    )


class Setting(Common, Base):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(Text)
    value: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("owner_id", "key"),)


class Provider(Common, Base):
    __tablename__ = "provider"
    function: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("owner_id", "function", "name"),)


# Contra SQL directo también: las validaciones no dependen exclusivamente del ORM.
for _table in Base.metadata.tables.values():
    for _column in _table.columns:
        _key = _column.name
        _quoted = '"' + _key + '"'
        if (
            _key == "id"
            or _key.endswith("_id")
            and _key not in {"model_id", "engine_id", "analyzer_id"}
        ):
            _table.append_constraint(
                CheckConstraint(
                    f"length({_quoted})=26 AND substr({_quoted},1,1) BETWEEN '0' AND '7' AND {_quoted} NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'"
                )
            )
        if _key.endswith("_at") or _key == "not_before":
            _table.append_constraint(
                CheckConstraint(
                    f"{_quoted} IS NULL OR (substr({_quoted},-1)='Z' AND datetime({_quoted}) IS NOT NULL)"
                )
            )
        if isinstance(_column.type, JSON):
            _table.append_constraint(
                CheckConstraint(
                    f"{_quoted} IS NULL OR (json_valid({_quoted}) AND json_type({_quoted})='{('array' if _key in {'tags', 'focus_point'} else 'object')}')"
                )
            )
        if isinstance(_column.type, Boolean):
            _table.append_constraint(CheckConstraint(f"{_quoted} IN (0,1)"))
        if isinstance(_column.type, Float):
            _table.append_constraint(
                CheckConstraint(f"abs({_quoted}) <= 1.7976931348623157e308")
            )
        if _key == "seed":
            _table.append_constraint(
                CheckConstraint(
                    f"length({_quoted})>0 AND {_quoted} NOT GLOB '*[^0-9]*' AND ({_quoted}='0' OR substr({_quoted},1,1)!='0')"
                )
            )
        if _key == "sha256" or _key.endswith("_sha256"):
            _table.append_constraint(
                CheckConstraint(
                    f"length({_quoted})=64 AND {_quoted} NOT GLOB '*[^0-9a-f]*'"
                )
            )
        if _key == "path":
            _table.append_constraint(
                CheckConstraint(
                    f"length({_quoted})>0 AND substr({_quoted},1,1)!='/' AND instr({_quoted},':')=0 AND instr({_quoted},char(92))=0 AND instr('/'||{_quoted}||'/','/../')=0"
                )
            )
        if _key == "resolution":
            _table.append_constraint(
                CheckConstraint(
                    "resolution NOT GLOB '*[^0-9x]*' AND instr(resolution,'x')>1 AND instr(substr(resolution,instr(resolution,'x')+1),'x')=0 AND CAST(substr(resolution,1,instr(resolution,'x')-1) AS INTEGER)>0 AND CAST(substr(resolution,instr(resolution,'x')+1) AS INTEGER)>0"
                )
            )
        if _key == "focus_point":
            _table.append_constraint(
                CheckConstraint(
                    "focus_point IS NULL OR (json_array_length(focus_point)=2 AND json_type(focus_point,'$[0]') IN ('integer','real') AND json_type(focus_point,'$[1]') IN ('integer','real') AND json_extract(focus_point,'$[0]') BETWEEN 0 AND 1 AND json_extract(focus_point,'$[1]') BETWEEN 0 AND 1)"
                )
            )
        if _column.default is not None:
            _default = _column.default.arg
            if not callable(_default):
                _column.server_default = DefaultClause(
                    str(int(_default)) if isinstance(_default, bool) else str(_default)
                )
            elif _key in {"tags", "params", "meta", "config"}:
                _column.server_default = DefaultClause("[]" if _key == "tags" else "{}")
