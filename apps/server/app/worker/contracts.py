"""Contrato privado de post.audio (ADR-0055), sin efectos externos.

Valida evidencia capturada; no acredita confianza, hashes de archivos, SQL/CAS,
procesos ni custodia. El descriptor se conserva como JSON canÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³nico inmutable y
su accessor devuelve el ModelDescriptor real separado, nunca una referencia mutable.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from typing import Annotated, Any, Literal, get_args, get_origin
from urllib.parse import urlsplit

from engine_contract import LoadRequest, ModelDescriptor
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    RootModel,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)

Text = Annotated[str, Field(min_length=1, max_length=512)]
ULID = Annotated[str, Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$", max_length=26)]
SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$", max_length=64)]
ImageDigest = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$", max_length=71)]
PositiveInt = Annotated[int, Field(gt=0)]
Seed = Annotated[int, Field(ge=0)]
OutputIndex = Annotated[int, Field(ge=0, le=63)]
PositiveFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class PrivateModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        allow_inf_nan=False,
        serialize_by_alias=True,
    )


def _json_guard(value: Any, depth: int = 0) -> None:
    """JSON acotado, finito, sin campos que transporten secretos."""
    if depth > 20:
        raise ValueError("JSON demasiado profundo")
    if value is None or type(value) is bool or type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("JSON no finito")
        return
    if type(value) is str:
        if len(value) > 8192 or any(ord(c) < 32 for c in value):
            raise ValueError(
                "Cadena JSON invÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡lida"
            )
        return
    if type(value) in (list, dict):
        if len(value) > 256:
            raise ValueError("JSON demasiado grande")
        if isinstance(value, dict):
            for key in value:
                if type(key) is not str or len(key) > 512:
                    raise ValueError(
                        "Clave JSON invÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡lida"
                    )
                normalized = re.sub(r"[^a-z0-9]", "", key.lower())
                if any(
                    word in normalized
                    for word in (
                        "secret",
                        "token",
                        "password",
                        "credential",
                        "ciphertext",
                        "authorization",
                        "header",
                        "apikey",
                        "privatekey",
                    )
                ):
                    raise ValueError("Secretos prohibidos")
                _json_guard(key, depth + 1)
            values = value.values()
        else:
            values = value
        for item in values:
            _json_guard(item, depth + 1)
        return
    raise ValueError("SÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³lo JSON")


def _canonical(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    _json_guard(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    """SHA del JSON canÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³nico UTF-8; no hash ni comprobaciÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³n de archivos."""
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _closed_models(annotation: Any, value: Any) -> None:
    """No permitir extras ignorados por los modelos pÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âºblicos /v1."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list and isinstance(value, list):
        for item in value:
            _closed_models(args[0], item)
    elif origin is dict and isinstance(value, dict):
        for item in value.values():
            _closed_models(args[1], item)
    elif (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
        and isinstance(value, dict)
    ):
        if value.keys() - annotation.model_fields.keys():
            raise ValueError("Campo desconocido en evidencia /v1")
        for name, item in value.items():
            _closed_models(annotation.model_fields[name].annotation, item)
    elif args:
        for candidate in args:
            _closed_models(candidate, value)


class CapturedDescriptor(RootModel[str]):
    """Snapshot exacto, profundamente inmutable del descriptor /v1 real.

    JSON en la frontera, texto canÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³nico dentro. value es una copia separada.
    """

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def capture(cls, value):
        if isinstance(value, cls):
            return value.root
        if isinstance(value, ModelDescriptor):
            value = value.model_dump(mode="json")
        if isinstance(value, str):
            value = json.loads(value)
        _json_guard(value)
        _closed_models(ModelDescriptor, value)
        descriptor = ModelDescriptor.model_validate(value, strict=True)
        if cls is CapturedDescriptor and (
            not descriptor.weights or len(descriptor.weights) > 64
        ):
            raise ValueError("Evidencia de pesos requerida")
        if cls is SyntheticCapturedDescriptor and (
            descriptor.weights or descriptor.remote_code
        ):
            raise ValueError("Synthetic evidence cannot contain weights or remote code")
        if not descriptor.modes or len(descriptor.modes) > 64:
            raise ValueError("Modos requeridos")
        if descriptor.provider.type != "local":
            raise ValueError(
                "MÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âºsica local requerida"
            )
        for weight in descriptor.weights:
            confined_path(weight.path)
        for remote in descriptor.remote_code:
            confined_path(remote.path)
        for name in (
            descriptor.id,
            descriptor.family,
            descriptor.version,
            descriptor.revision,
            descriptor.license,
            descriptor.training_data,
        ):
            if not name or len(name) > 512:
                raise ValueError(
                    "Identidad del descriptor invÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡lida"
                )
        return _canonical(descriptor)

    @field_serializer("root")
    def payload(self, value):
        return json.loads(value)

    @property
    def value(self) -> ModelDescriptor:
        return ModelDescriptor.model_validate_json(self.root)


class SyntheticCapturedDescriptor(CapturedDescriptor):
    """Snapshot sin pesos; valida forma, nunca concede autoridad del registro."""

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler(core_schema)
        # El compilador JSON1 existente expande este snapshot a ModelDescriptor.
        schema["title"] = "CapturedDescriptor"
        return schema


def synthetic_origin(value: str) -> str:
    if type(value) is not str or not value or len(value) > 256:
        raise ValueError("Invalid synthetic origin")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or not value.isascii()
        or any(ord(char) < 33 for char in value)
    ):
        raise ValueError("Invalid synthetic origin")
    # Fuerza validación del puerto y conserva la identidad exacta configurada.
    _port = parsed.port
    return value.rstrip("/")


class SyntheticImplementation(PrivateModel):
    name: Text
    revision: Text
    source_sha256: SHA256
    common_source_sha256: SHA256


class SyntheticBinding(PrivateModel):
    version: Literal[1]
    recipe_id: Annotated[str, Field(min_length=1, max_length=128)]
    scope: Literal["product", "test"]
    origin: Annotated[str, Field(max_length=256), BeforeValidator(synthetic_origin)]
    engine_id: Text
    engine_version: Text
    contract_version: Literal["1"]
    descriptor_sha256: SHA256
    implementation: SyntheticImplementation
    implementation_sha256: SHA256
    expected_image_digest: ImageDigest | None

    @field_validator("recipe_id")
    @classmethod
    def recipe_identity(cls, value):
        if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", value) is None:
            raise ValueError("Invalid synthetic recipe identity")
        return value

    @model_validator(mode="before")
    @classmethod
    def exact_version(cls, value):
        if isinstance(value, dict) and type(value.get("version")) is not int:
            raise ValueError("Synthetic binding version must be an integer")
        return value

    @model_validator(mode="after")
    def implementation_fingerprint(self):
        if canonical_sha256(self.implementation) != self.implementation_sha256:
            raise ValueError("Synthetic implementation fingerprint mismatch")
        return self


class CapturedLoad(PrivateModel):
    """Opciones exactas del LoadRequest vigente (sin opciones inventadas)."""

    model_id: Text
    mode: Text | None

    @model_validator(mode="after")
    def public_contract(self):
        LoadRequest.model_validate(self.model_dump(), strict=True)
        return self


class ObservedModel(PrivateModel):
    model_id: Text
    mode: Text


class CapturedProvenance(PrivateModel):
    descriptor: CapturedDescriptor | SyntheticCapturedDescriptor
    engine_id: Text
    engine_version: Text
    contract_version: Literal["1"]
    task: Literal["music.song", "music.instrumental"]
    load: CapturedLoad
    observed_model: ObservedModel | None
    expected_image_digest: ImageDigest | None
    reported_image_digest: ImageDigest | None
    evidence_kind: Literal["learned", "synthetic"] = "learned"
    synthetic_binding: SyntheticBinding | None = None

    @model_validator(mode="before")
    @classmethod
    def explicit_evidence_branch(cls, value):
        if not isinstance(value, dict):
            return value
        value = dict(value)
        kind = value.get("evidence_kind", "learned")
        if kind not in {"learned", "synthetic"}:
            raise ValueError("Invalid evidence kind")
        descriptor = value.get("descriptor")
        if kind == "learned":
            if value.get("synthetic_binding") is not None or isinstance(
                descriptor, SyntheticCapturedDescriptor
            ):
                raise ValueError("Learned evidence cannot carry synthetic binding")
            dtype = CapturedDescriptor
        else:
            if value.get("synthetic_binding") is None or (
                isinstance(descriptor, CapturedDescriptor)
                and type(descriptor) is not SyntheticCapturedDescriptor
            ):
                raise ValueError("Synthetic evidence requires its exact branch")
            dtype = SyntheticCapturedDescriptor
        if isinstance(descriptor, CapturedDescriptor):
            descriptor = descriptor.root
        value["descriptor"] = dtype(descriptor)
        return value

    @model_serializer(mode="wrap")
    def historical_learned_shape(self, handler):
        result = handler(self)
        if self.evidence_kind == "learned":
            result.pop("evidence_kind", None)
            result.pop("synthetic_binding", None)
        return result

    @model_validator(mode="after")
    def consistent(self):
        descriptor = self.descriptor.value
        if self.evidence_kind == "synthetic":
            binding = self.synthetic_binding
            if (
                type(self.descriptor) is not SyntheticCapturedDescriptor
                or binding is None
                or binding.descriptor_sha256 != canonical_sha256(self.descriptor)
                or (binding.engine_id, binding.engine_version, binding.contract_version)
                != (self.engine_id, self.engine_version, self.contract_version)
                or binding.expected_image_digest != self.expected_image_digest
            ):
                raise ValueError("Synthetic binding and captured evidence mismatch")
        elif type(self.descriptor) is not CapturedDescriptor or self.synthetic_binding:
            raise ValueError("Learned evidence branch mismatch")
        if self.load.model_id != descriptor.id:
            raise ValueError("Carga y descriptor distintos")
        if self.load.mode is not None and self.load.mode not in {
            m.id for m in descriptor.modes
        }:
            raise ValueError("Modo no declarado")
        if self.observed_model is not None and (
            self.observed_model.model_id != self.load.model_id
            or (
                self.load.mode is not None
                and self.observed_model.mode != self.load.mode
            )
            or self.observed_model.mode not in {m.id for m in descriptor.modes}
        ):
            raise ValueError("Modelo observado distinto")
        task = descriptor.tasks.get(self.task)
        if task is None or task.verified is not True:
            raise ValueError("Tarea no verificada")
        if (
            self.expected_image_digest is not None
            and self.reported_image_digest is not None
            and self.expected_image_digest != self.reported_image_digest
        ):
            raise ValueError("Imagen observada distinta de la esperada")
        _json_guard(self.model_dump(mode="json"))
        return self


class PublicationAuthority(PrivateModel):
    owner_id: ULID
    song_id: ULID
    post_job_id: ULID
    generation_job_id: ULID
    winning_attempt_id: ULID
    winning_ordinal: PositiveInt
    terminal_seq: PositiveInt
    terminal_sha256: SHA256
    take_id: ULID
    output_index: OutputIndex
    seed: Seed
    provenance_sha256: SHA256


def confined_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError("Ruta invÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡lida")
    if any(unicodedata.category(c) in ("Cc", "Cf", "Cs") for c in value) or any(
        c in value for c in '\\:*?"<>|'
    ):
        raise ValueError("Ruta POSIX requerida")
    parts = value.split("/")
    for part in parts:
        if not part or part in (".", "..") or part.endswith((".", " ")):
            raise ValueError("Alias de ruta prohibido")
        if part.split(".")[0].upper() in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(10)),
            *(f"LPT{i}" for i in range(10)),
        }:
            raise ValueError("Nombre reservado Windows")
    return value


RelativePath = Annotated[str, Field(max_length=1024), BeforeValidator(confined_path)]


class FileReference(PrivateModel):
    path: RelativePath
    sha256: SHA256
    media_type: Literal["audio/wav", "audio/flac", "audio/mpeg", "application/json"]
    bytes: PositiveInt


class SourceReference(FileReference):
    media_type: Literal["audio/wav", "audio/flac", "audio/mpeg"]
    duration_s: PositiveFloat


class TakeEntry(PrivateModel):
    authority: PublicationAuthority
    source: SourceReference
    copied_source: SourceReference = Field(alias="copy")

    @model_validator(mode="after")
    def same_copy(self):
        if self.source.model_dump(exclude={"path"}) != self.copied_source.model_dump(
            exclude={"path"}
        ):
            raise ValueError("Copia distinta de la fuente")
        if self.source.path == self.copied_source.path:
            raise ValueError("La copia requiere otra referencia")
        return self


def _entries(value):
    if type(value) is list:
        return tuple(value)
    return value


class PostPlan(PrivateModel):
    version: Literal[1]
    handler: Literal["post.audio"]
    handler_version: Literal[1]
    owner_id: ULID
    song_id: ULID
    post_job_id: ULID
    generation_job_id: ULID
    request_sha256: SHA256
    tool_pin_sha256: SHA256
    provenance: CapturedProvenance
    takes: Annotated[
        tuple[TakeEntry, ...],
        BeforeValidator(_entries),
        Field(min_length=1, max_length=64),
    ]

    @model_validator(mode="before")
    @classmethod
    def strict_versions(cls, value):
        if isinstance(value, dict) and any(
            type(value.get(k)) is not int for k in ("version", "handler_version")
        ):
            raise ValueError("Versiones enteras requeridas")
        return value

    @model_validator(mode="after")
    def matching_authorities(self):
        ids, indices = set(), set()
        digest = canonical_sha256(self.provenance)
        first = self.takes[0].authority
        for entry in self.takes:
            a = entry.authority
            if a.take_id in ids or a.output_index in indices:
                raise ValueError(
                    "Toma o ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â­ndice repetido"
                )
            ids.add(a.take_id)
            indices.add(a.output_index)
            for field in ("owner_id", "song_id", "post_job_id", "generation_job_id"):
                if getattr(a, field) != getattr(self, field):
                    raise ValueError("Autoridad del plan distinta")
            for field in (
                "winning_attempt_id",
                "winning_ordinal",
                "terminal_seq",
                "terminal_sha256",
            ):
                if getattr(a, field) != getattr(first, field):
                    raise ValueError("Terminal ganador distinto")
            if a.provenance_sha256 != digest:
                raise ValueError("SHA de procedencia distinto")
        return self

    def validate_result(self, result: PerTakeResult) -> PerTakeResult:
        """ComparaciÃ³n pura; el padre debe aportar un resultado ya validado."""
        if not isinstance(result, (TakeSuccess, TakeFailure)):
            raise TypeError("Resultado tipado requerido")
        expected = next(
            (
                entry.authority
                for entry in self.takes
                if entry.authority.take_id == result.take_id
                and entry.authority.output_index == result.output_index
            ),
            None,
        )
        if expected is None:
            raise ValueError("Resultado fuera del plan")
        if isinstance(result, TakeSuccess) and result.package.authority != expected:
            raise ValueError("Autoridad completa del resultado distinta")
        return result


class PreparedPackage(PrivateModel):
    """Metadatos cerrados. manifest tiene SHA propio, no se autoenumera."""

    authority: PublicationAuthority
    master: FileReference
    listen: FileReference
    peaks: FileReference
    manifest: FileReference

    @model_validator(mode="after")
    def exact_files(self):
        base = f"data/songs/{self.authority.song_id}/takes/{self.authority.take_id}/"
        for role, name, media in (
            ("master", "master.flac", "audio/flac"),
            ("listen", "listen.mp3", "audio/mpeg"),
            ("peaks", "peaks.json", "application/json"),
            ("manifest", "manifest.json", "application/json"),
        ):
            file = getattr(self, role)
            if file.path != base + name or file.media_type != media:
                raise ValueError("Paquete final distinto")
        return self


# CÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³digos locales del post; no son terminales ni errores pÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âºblicos de engine.
PostFailureCode = Literal[
    "UNSAFE_PATH",
    "AUDIO_TRANSCODE_FAILED",
    "AUDIO_MEASUREMENT_FAILED",
    "AUDIO_TARGET_UNREACHABLE",
    "AUDIO_INVALID",
    "PROVENANCE_MISSING",
    "PROVENANCE_MISMATCH",
    "TAKE_POST_FAILED",
    "CANCELLED",
]


class TakeSuccess(PrivateModel):
    status: Literal["success"]
    take_id: ULID
    output_index: OutputIndex
    package: PreparedPackage
    duration_s: PositiveFloat
    integrated_lufs: FiniteFloat
    true_peak_dbtp: FiniteFloat

    @model_validator(mode="after")
    def matching_take(self):
        if (
            self.take_id != self.package.authority.take_id
            or self.output_index != self.package.authority.output_index
        ):
            raise ValueError("Resultado de otra toma")
        return self


class TakeFailure(PrivateModel):
    status: Literal["failure"]
    take_id: ULID
    output_index: OutputIndex
    code: PostFailureCode


PerTakeResult = Annotated[TakeSuccess | TakeFailure, Field(discriminator="status")]
