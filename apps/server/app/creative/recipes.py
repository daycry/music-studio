"""Recetas privadas ADR-0077: captura pura sin autoridad de ejecución."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Annotated, Literal, get_args, get_origin
from urllib.parse import urlsplit

from engine_contract import Input, JobRequest, ModelDescriptor
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    RootModel,
    ValidationError,
    model_validator,
)
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012

from app.queue.inputs import ResolutionError
from app.queue.resolver import closed_schema
from app.worker.contracts import SyntheticBinding

ULID = Annotated[str, Field(pattern=r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")]
SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Text = Annotated[str, Field(min_length=1, max_length=512)]
PositiveInt = Annotated[int, Field(gt=0)]
Seed = Annotated[int, Field(ge=0, le=2**64 - 1)]
HistoricalSeed = Annotated[int, Field(ge=0)]
Media = Literal["audio/flac", "audio/wav"]
SECRET_KEYS = frozenset(
    [
        "secret",
        "secrets",
        "token",
        "accesstoken",
        "refreshtoken",
        "apitoken",
        "enginetoken",
        "studioenginetoken",
        "studiotoken",
        "password",
        "passwd",
        "credential",
        "credentials",
        "ciphertext",
        "authorization",
        "proxyauthorization",
        "header",
        "headers",
        "apikey",
        "providerapikey",
        "privatekey",
    ]
)
TRANSPORT_KEYS = frozenset(
    ["path", "outputdir", "url", "headers", "credentials", "scripts", "commands", "ref"]
)


class RecipeError(ValueError):
    def __init__(self, code: str, field: str | None = None):
        self.code, self.field = code, field
        super().__init__(code)


def private_errors(function):
    """Rompe cadenas de excepción que puedan conservar entrada privada."""

    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RecipeError as error:
            code, field = error.code, error.field
        except (ValidationError, TypeError, ValueError, RecursionError, OverflowError):
            code, field = "RECIPE_INVALID", None
        # Fuera del handler: ni __context__ ni __cause__ retienen la entrada.
        raise RecipeError(code, field)

    return call


def fail(code="RECIPE_INVALID", field=None):
    raise RecipeError(code, field)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def encode(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def key_name(key):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", key).casefold())


def string_guard(value):
    if any(
        0xD800 <= ord(c) <= 0xDFFF or ord(c) == 0 or (ord(c) < 32 and c not in "\t\r\n")
        for c in value
    ):
        fail()
    if re.search(
        r"-----BEGIN (?:(?:RSA|EC|OPENSSH) )?PRIVATE KEY-----", value
    ) or re.search(r"Bearer [A-Za-z0-9._~+/=\-]{16,}", value):
        fail("RECIPE_SECRET_FORBIDDEN")
    try:
        parsed = urlsplit(value)
    except ValueError:
        return
    if parsed.username is not None or parsed.password is not None:
        fail("RECIPE_SECRET_FORBIDDEN")


def json_guard(
    value, *, legacy=False, namespace=False, allow_namespaces=False, path=(), seen=None
):
    if seen is None:
        seen = set()
    if not legacy and len(path) > 20:
        fail()
    if type(value) in (bool, int) or value is None:
        return
    if type(value) is float:
        if not math.isfinite(value):
            fail()
        return
    if type(value) is str:
        string_guard(value)
        lyric_param = path in {
            ("executor", "params", "lyrics"),
            ("operation", "basis", "request", "params", "lyrics"),
        }
        lyric_text = (
            len(path) == 4
            and path[:2] == ("lyrics", "versions")
            and type(path[2]) is int
            and path[3] == "text"
        )
        style_param = path in {
            ("executor", "params", "style"),
            ("operation", "basis", "request", "params", "style"),
        }
        limit = 32768 if lyric_param or lyric_text else 4000 if style_param else 8192
        if not legacy and len(value) > limit:
            fail()
        return
    if (
        type(value) not in (dict, list)
        or id(value) in seen
        or not legacy
        and len(value) > 256
    ):
        fail()
    seen.add(id(value))
    try:
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    fail()
                string_guard(key)
                if not legacy and len(key) > 8192:
                    fail()
                if not namespace and key_name(key) in SECRET_KEYS:
                    fail("RECIPE_SECRET_FORBIDDEN")
                if (
                    not namespace
                    and "params" in path
                    and key_name(key) in TRANSPORT_KEYS
                ):
                    fail("RECIPE_SECRET_FORBIDDEN")
                json_guard(
                    item,
                    legacy=legacy,
                    namespace=namespace
                    or allow_namespaces
                    and path in {("executor",), ("recipe", "executor")}
                    and key in {"descriptor", "synthetic_binding"},
                    allow_namespaces=allow_namespaces,
                    path=(*path, key),
                    seen=seen,
                )
        else:
            for i, item in enumerate(value):
                json_guard(
                    item,
                    legacy=legacy,
                    namespace=namespace,
                    allow_namespaces=allow_namespaces,
                    path=(*path, i),
                    seen=seen,
                )
    finally:
        seen.remove(id(value))


def parse(payload, *, limit=1024 * 1024):
    if (
        type(payload) is not bytes
        or len(payload) > limit
        or payload.startswith(b"\xef\xbb\xbf")
    ):
        fail()

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail()
            result[key] = value
        return result

    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda _: fail(),
        )
    except (UnicodeError, ValueError, RecursionError) as e:
        if isinstance(e, RecipeError):
            raise
        fail()


def seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        fail()
    return float(value)


Seconds = Annotated[float, BeforeValidator(seconds)]
NonnegativeSeconds = Annotated[Seconds, Field(ge=0)]
PositiveSeconds = Annotated[Seconds, Field(gt=0)]


def exact_integer(value):
    if type(value) is not int:
        fail()
    return value


Channels = Annotated[Literal[1, 2], BeforeValidator(exact_integer)]


def interval(value):
    if type(value) is not list or len(value) != 2:
        fail()
    a, b = map(seconds, value)
    if not 0 <= a < b:
        fail()
    return (a, b)


Interval = Annotated[tuple[float, float], BeforeValidator(interval)]


def array(value):
    if type(value) is list:
        return tuple(value)
    if type(value) is tuple:
        return value
    fail()


class PrivateModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, allow_inf_nan=False
    )


class FrozenJSON(RootModel[str]):
    model_config = ConfigDict(frozen=True, strict=True)

    @model_validator(mode="before")
    @classmethod
    def freeze(cls, value):
        if isinstance(value, cls):
            return value.root
        path = (
            ("operation", "basis", "request")
            if type(value) is dict and {"job_id", "output_dir"} <= value.keys()
            else ("executor", "params")
        )
        json_guard(value, path=path)
        return encode(value).decode("utf-8")

    @property
    def wire(self):
        return json.loads(self.root)


class FrozenJSONObject(FrozenJSON):
    @model_validator(mode="before")
    @classmethod
    def object_only(cls, value):
        if not isinstance(value, FrozenJSON) and type(value) is not dict:
            fail()
        return value


FrozenObject = Annotated[
    FrozenJSONObject, PlainSerializer(lambda v: v.wire, return_type=dict)
]


def closed_model(annotation, value):
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is list and type(value) is list:
        for item in value:
            closed_model(args[0], item)
    elif origin is dict and type(value) is dict:
        for item in value.values():
            closed_model(args[1], item)
    elif (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
        and type(value) is dict
    ):
        if value.keys() - annotation.model_fields.keys():
            fail()
        for key, item in value.items():
            closed_model(annotation.model_fields[key].annotation, item)
    elif args:
        for candidate in args:
            closed_model(candidate, value)


def safe_path(value):
    if (
        type(value) is not str
        or not value
        or ":" in value
        or "\\" in value
        or any(ord(c) < 32 for c in value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        fail()
    return value


@dataclass(frozen=True)
class FrozenDescriptor:
    payload: bytes
    sha256: str

    @classmethod
    @private_errors
    def capture(cls, value, *, evidence_kind):
        if isinstance(value, ModelDescriptor):
            value = value.model_dump(mode="json")
        elif isinstance(value, Mapping):
            value = dict(value)
        model = descriptor_validate(value, evidence_kind)
        data = model.model_dump(mode="json")
        descriptor_validate(data, evidence_kind)
        payload = encode(data)
        if len(payload) > 1024 * 1024:
            fail()
        return cls(payload, digest(payload))

    @classmethod
    @private_errors
    def read(cls, payload, *, expected_sha256, evidence_kind):
        if type(payload) is not bytes:
            fail()
        if digest(payload) != expected_sha256:
            fail("RECIPE_HASH_MISMATCH")
        data = parse(payload)
        descriptor_validate(data, evidence_kind)
        if encode(data) != payload:
            fail("RECIPE_HASH_MISMATCH")
        return cls(payload, expected_sha256)

    @property
    def wire(self):
        return json.loads(self.payload)

    @property
    def value(self):
        return ModelDescriptor.model_validate(self.wire, strict=True)


def descriptor_validate(value, evidence_kind):
    json_guard(value, namespace=True)
    closed_model(ModelDescriptor, value)
    try:
        model = ModelDescriptor.model_validate(value, strict=True)
    except ValidationError as error:
        for item in error.errors(include_input=False):
            cause = item.get("ctx", {}).get("error")
            if isinstance(cause, RecipeError):
                raise RecipeError(cause.code, cause.field) from None
        fail()
    if (
        evidence_kind not in {"learned", "synthetic"}
        or model.provider.type != "local"
        or not 1 <= len(model.modes) <= 64
    ):
        fail()
    if (
        evidence_kind == "learned"
        and not 1 <= len(model.weights) <= 64
        or evidence_kind == "synthetic"
        and (model.weights or model.remote_code)
    ):
        fail()
    for key in ("id", "family", "version", "revision", "license", "training_data"):
        if not 1 <= len(getattr(model, key)) <= 512:
            fail()
    for item in (*model.weights, *model.remote_code):
        safe_path(item.path)
    return model


Descriptor = Annotated[
    FrozenDescriptor, PlainSerializer(lambda v: v.wire, return_type=dict)
]


class TakeRef(PrivateModel):
    type: Literal["take"]
    id: ULID


class AssetRef(PrivateModel):
    type: Literal["asset"]
    id: ULID


class UploadRef(PrivateModel):
    type: Literal["upload"]
    id: ULID


class InputRights(PrivateModel):
    ref: UploadRef
    sha256: SHA256
    rights: Literal["own", "licensed", "consented", "public_domain"]
    consent: Literal["self", "consented", "n_a"]
    real_person: bool
    commercial_use: bool

    @model_validator(mode="after")
    def consent_check(self):
        if self.real_person and self.consent == "n_a":
            fail("RIGHTS_DECLARATION_REQUIRED")
        return self


class ParentRights(PrivateModel):
    kind: Literal["generated_take"]
    manifest_sha256: SHA256
    commercial_use: bool
    inputs: Annotated[tuple[InputRights, ...], BeforeValidator(array)]


class MasterAssetSnapshot(PrivateModel):
    ref: AssetRef
    owner_id: ULID
    subject_type: Literal["take"]
    subject_id: ULID
    role: Literal["master"]
    sha256: SHA256
    bytes: PositiveInt
    media_type: Media
    duration_s: PositiveSeconds
    sample_rate: PositiveInt
    channels: Channels
    manifest_ref: AssetRef
    manifest_sha256: SHA256
    rights: ParentRights


class ParentInference(PrivateModel):
    kind: Literal["inference"]
    model_id: Text
    model_version: Text
    seed: HistoricalSeed


class ParentCpuEdit(PrivateModel):
    kind: Literal["cpu_edit"]
    recipe_sha256: SHA256
    execution_id: ULID


class MapIntentOp(PrivateModel):
    op: Literal["keep", "regen", "append", "fade"]
    src: Interval | None
    dst: Interval | None


class SectionMapIntent(PrivateModel):
    kind: Literal["requested_seconds"]
    ops: Annotated[
        tuple[MapIntentOp, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=3),
    ]


class ParentSnapshot(PrivateModel):
    ref: TakeRef
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    root_id: ULID
    role: Literal["source", "crossfade_a", "crossfade_b"]
    status: Literal["ready"]
    asset: MasterAssetSnapshot
    origin: Annotated[ParentInference | ParentCpuEdit, Field(discriminator="kind")]
    lyrics_version_ids: Annotated[tuple[ULID, ...], BeforeValidator(array)]
    section_map: SectionMapIntent
    commercial_use: bool


class LyricsVersionSnapshot(PrivateModel):
    id: ULID
    owner_id: ULID
    song_id: ULID
    parent_id: ULID | None
    text: Annotated[str, Field(max_length=32768)]
    sha256: SHA256
    source: Literal["manual", "assistant", "import"]
    declaration: Literal["own", "assistant", "public_domain", "licensed"]


class LyricsParentBinding(PrivateModel):
    parent_id: ULID
    version_ids: Annotated[tuple[ULID, ...], BeforeValidator(array)]


class LyricsContext(PrivateModel):
    mode: Literal["single", "instrumental", "composite"]
    versions: Annotated[tuple[LyricsVersionSnapshot, ...], BeforeValidator(array)]
    target_version_id: ULID | None
    parent_bindings: Annotated[tuple[LyricsParentBinding, ...], BeforeValidator(array)]
    commercial_use: bool


class ToolSelection(PrivateModel):
    tool_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]{1,128}$")]
    lock_sha256: SHA256
    revision: Text
    archive_sha256: SHA256
    recipe_revision: Text
    license: Text
    commercial_use: bool
    runtime_verified: bool


class CoordinateParams(PrivateModel):
    at_s: Annotated[str, Field(min_length=1, max_length=128)] | None
    t0: Annotated[str, Field(min_length=1, max_length=128)] | None
    t1: Annotated[str, Field(min_length=1, max_length=128)] | None


class InferenceSelection(PrivateModel):
    kind: Literal["inference"]
    task: Literal[
        "music.song",
        "music.instrumental",
        "music.retake",
        "music.extend",
        "music.repaint",
        "music.cover",
    ]
    model_id: Text
    model_version: Text
    engine_id: Text
    engine_version: Text
    contract_version: Literal["1"]
    mode: Text | None
    expected_image_digest: (
        Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")] | None
    )
    descriptor: Descriptor
    descriptor_sha256: SHA256
    evidence_kind: Literal["learned", "synthetic"]
    synthetic_binding: SyntheticBinding | None
    params: FrozenObject
    coordinate_params: CoordinateParams
    seed: Seed
    timeout_s: PositiveInt
    output_shape: Literal["full", "region"]
    tools: Annotated[
        tuple[ToolSelection, ...], BeforeValidator(array), Field(min_length=1)
    ]


class OutputFormat(PrivateModel):
    sample_rate: PositiveInt
    channels: Channels


class CpuSelection(PrivateModel):
    kind: Literal["cpu_edit"]
    task: Literal["audio.edit"]
    tools: Annotated[
        tuple[ToolSelection, ...], BeforeValidator(array), Field(min_length=1)
    ]
    output_format: OutputFormat


class EffectiveRequestBasis(PrivateModel):
    generation_job_id: ULID
    winning_attempt_id: ULID
    take_id: ULID
    output_index: Annotated[int, Field(ge=0, le=63)]
    request_sha256: SHA256
    request: FrozenObject
    lyrics_version_id: ULID | None


class VariationRequest(PrivateModel):
    kind: Literal["variation_request"]
    basis: EffectiveRequestBasis


class VariationAudio(PrivateModel):
    kind: Literal["variation_audio"]


class Extend(PrivateModel):
    kind: Literal["extend"]
    at_s: NonnegativeSeconds


class Repaint(PrivateModel):
    kind: Literal["repaint"]
    region: Interval


class Cover(PrivateModel):
    kind: Literal["cover"]


class Trim(PrivateModel):
    kind: Literal["trim"]
    region: Interval


class Fade(PrivateModel):
    kind: Literal["fade"]
    fade_in_s: PositiveSeconds | None
    fade_out_s: PositiveSeconds | None


class Crossfade(PrivateModel):
    kind: Literal["crossfade"]
    duration_s: PositiveSeconds


class Sampling(PrivateModel):
    index_rule: Literal["round_half_up"]
    interval: Literal["half_open"]


class CreativeRecipeV1(PrivateModel):
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    take_id: ULID
    root_id: ULID
    derivation: Literal["variant", "extend", "repaint", "cover", "edit"]
    operation: Annotated[
        VariationRequest
        | VariationAudio
        | Extend
        | Repaint
        | Cover
        | Trim
        | Fade
        | Crossfade,
        Field(discriminator="kind"),
    ]
    executor: Annotated[InferenceSelection | CpuSelection, Field(discriminator="kind")]
    parents: Annotated[
        tuple[ParentSnapshot, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    lyrics: LyricsContext
    required_features: Annotated[tuple[Text, ...], BeforeValidator(array)]
    sampling: Sampling
    commercial_use: bool

    @model_validator(mode="after")
    def coherent(self):
        validate_recipe(self)
        return self


class CreativeRequestV1(PrivateModel):
    kind: Literal["creative_recipe"]
    schema_version: Literal[1]
    recipe: CreativeRecipeV1
    recipe_sha256: SHA256

    @model_validator(mode="before")
    @classmethod
    def version(cls, value):
        if type(value) is dict and (
            type(value.get("schema_version")) is not int
            or value.get("schema_version") != 1
            or value.get("kind") != "creative_recipe"
        ):
            fail("RECIPE_VERSION_UNSUPPORTED")
        return value


@dataclass(frozen=True)
class CapturedRecipe:
    value: CreativeRecipeV1
    payload: bytes
    sha256: str


@dataclass(frozen=True)
class CapturedRequest:
    value: CreativeRequestV1
    payload: bytes
    sha256: str
    recipe: CapturedRecipe


@dataclass(frozen=True)
class LegacyRequestView:
    raw_payload: bytes | None
    raw_sha256: str | None
    canonical_payload: bytes
    canonical_sha256: str
    present_fields: tuple[str, ...]
    format: Literal["m1_unversioned"] = "m1_unversioned"

    @property
    def value(self):
        return json.loads(self.canonical_payload)


class RecipeInputRequirement(PrivateModel):
    parent_id: ULID
    asset_id: ULID
    asset_role: Literal["master"]
    engine_role: Literal["source"]
    sha256: SHA256
    media_type: Media


class ResolvedRecipeInput(PrivateModel):
    asset_id: ULID
    role: Literal["source"]
    path: Annotated[str, BeforeValidator(safe_path)]
    sha256: SHA256
    media_type: Media


def ordered_unique(values):
    values = tuple(values)
    if tuple(sorted(set(values))) != values:
        fail()


def ideal_equal(a, b):
    if a is None or b is None:
        return a is b
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(
            ideal_equal(x, y) for x, y in zip(a, b, strict=True)
        )
    if type(a) in (float, int) and type(b) in (float, int):
        return math.isclose(a, b, abs_tol=1e-9, rel_tol=0)
    return a == b


def expected_maps(recipe):
    op, parents = recipe.operation, recipe.parents
    duration = parents[0].asset.duration_s

    def piece(kind, src=None, dst=None):
        return (kind, src, dst)

    if op.kind in {"variation_request", "variation_audio", "cover"}:
        return [[piece("regen")]]
    if op.kind == "extend":
        if op.at_s > duration:
            fail()
        return [
            [
                *([piece("keep", (0.0, op.at_s), (0.0, op.at_s))] if op.at_s else []),
                piece("append"),
            ]
        ]
    if op.kind in {"trim", "repaint"}:
        start, end = op.region
        if end > duration:
            fail()
        if op.kind == "trim":
            return [[piece("keep", (start, end), (0.0, end - start))]]
        return [
            [
                *([piece("keep", (0.0, start), (0.0, start))] if start else []),
                piece("regen"),
                *([piece("keep", (end, duration))] if end < duration else []),
            ]
        ]
    if op.kind == "fade":
        incoming = 0.0 if op.fade_in_s is None else op.fade_in_s
        outgoing = 0.0 if op.fade_out_s is None else op.fade_out_s
        if incoming + outgoing == 0.0 or incoming + outgoing > duration:
            fail()
        intervals = (
            ("fade", 0.0, incoming),
            ("keep", incoming, duration - outgoing),
            ("fade", duration - outgoing, duration),
        )
        return [[piece(kind, (a, b), (a, b)) for kind, a, b in intervals if a < b]]
    d, other = op.duration_s, parents[1].asset.duration_s
    if d > min(duration, other):
        fail()
    return [
        [
            *(
                [piece("keep", (0.0, duration - d), (0.0, duration - d))]
                if duration > d
                else []
            ),
            piece("fade", (duration - d, duration), (duration - d, duration)),
        ],
        [
            piece("fade", (0.0, d), (duration - d, duration)),
            *(
                [piece("keep", (d, other), (duration, duration + other - d))]
                if other > d
                else []
            ),
        ],
    ]


def validate_lyrics(recipe):
    lyrics = recipe.lyrics
    ordered_unique(v.id for v in lyrics.versions)
    versions = {v.id: v for v in lyrics.versions}
    used = set()
    if len(lyrics.parent_bindings) != len(recipe.parents):
        fail("RECIPE_CONTEXT_MISMATCH")
    for parent, binding in zip(recipe.parents, lyrics.parent_bindings, strict=True):
        ordered_unique(binding.version_ids)
        ordered_unique(parent.lyrics_version_ids)
        if (
            binding.parent_id != parent.ref.id
            or binding.version_ids != parent.lyrics_version_ids
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
        used.update(binding.version_ids)
    if lyrics.target_version_id:
        used.add(lyrics.target_version_id)
    if used != set(versions):
        fail("RECIPE_CONTEXT_MISMATCH")
    for v in versions.values():
        if (
            v.owner_id != recipe.owner_id
            or v.song_id != recipe.song_id
            or v.parent_id == v.id
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
        if digest(v.text.encode("utf-8")) != v.sha256:
            fail("RECIPE_HASH_MISMATCH")
    if lyrics.mode == "single":
        if lyrics.target_version_id not in versions:
            fail("LYRICS_DECLARATION_REQUIRED")
    elif lyrics.target_version_id is not None:
        fail("RECIPE_CONTEXT_MISMATCH")
    if lyrics.mode == "instrumental" and not versions and not lyrics.commercial_use:
        fail("RECIPE_CONTEXT_MISMATCH")
    if recipe.executor.kind == "cpu_edit":
        bindings = [p.lyrics_version_ids for p in recipe.parents]
        if all(not ids for ids in bindings):
            mode, target = "instrumental", None
        elif all(ids == bindings[0] and len(ids) == 1 for ids in bindings):
            mode, target = "single", bindings[0][0]
        else:
            mode, target = "composite", None
        if (lyrics.mode, lyrics.target_version_id) != (mode, target):
            fail("RECIPE_CONTEXT_MISMATCH")
    else:
        selection = recipe.executor
        params = selection.params.wire
        if selection.task == "music.instrumental":
            if lyrics.mode != "instrumental" or "lyrics" in params:
                fail("RECIPE_CONTEXT_MISMATCH")
        elif "lyrics" in params:
            if (
                lyrics.mode != "single"
                or params["lyrics"] != versions[lyrics.target_version_id].text
            ):
                fail("RECIPE_CONTEXT_MISMATCH")
        elif selection.task == "music.song":
            fail("LYRICS_DECLARATION_REQUIRED")
        elif recipe.operation.kind != "variation_request":
            ids = recipe.parents[0].lyrics_version_ids
            mode, target = (
                ("single", ids[0])
                if len(ids) == 1
                else (("composite", None) if ids else ("instrumental", None))
            )
            if (lyrics.mode, lyrics.target_version_id) != (mode, target):
                fail("RECIPE_CONTEXT_MISMATCH")
        if recipe.operation.kind == "variation_audio":
            ids = recipe.parents[0].lyrics_version_ids
            if (
                lyrics.target_version_id is not None
                and (lyrics.target_version_id,) != ids
            ):
                fail("RECIPE_CONTEXT_MISMATCH")


def validate_schema(schema):
    try:
        closed_schema(schema)
        Draft202012Validator.check_schema(schema)
    except (ResolutionError, SchemaError, TypeError, ValueError):
        fail()
    root, visited = schema, set()
    while isinstance(root, dict) and "$ref" in root:
        ref = root["$ref"]
        if ref in visited or not ref.startswith("#/"):
            fail()
        visited.add(ref)
        try:
            root = schema
            for part in ref[2:].split("/"):
                root = root[part.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError):
            fail()
    if (
        not isinstance(root, dict)
        or root.get("type") != "object"
        or root.get("additionalProperties") is not False
    ):
        fail()

    seen = set()
    resolver = (
        Registry()
        .with_resource(
            "", Resource.from_contents(schema, default_specification=DRAFT202012)
        )
        .resolver()
    )

    def walk(node):
        # Only schema positions: property names and const/default/enum are data.
        if not isinstance(node, dict) or id(node) in seen:
            return
        seen.add(id(node))
        types = node.get("type")
        object_type = types == "object" or (
            isinstance(types, list) and "object" in types
        )
        object_keywords = {
            "properties",
            "patternProperties",
            "additionalProperties",
            "unevaluatedProperties",
            "propertyNames",
            "required",
            "dependentRequired",
            "dependentSchemas",
            "minProperties",
            "maxProperties",
        }
        implicit_object = "type" not in node and object_keywords.intersection(node)
        if (object_type or implicit_object) and node.get(
            "additionalProperties"
        ) is not False:
            fail()
        if "$ref" in node:
            try:
                target = resolver.lookup(node["$ref"]).contents
            except (Unresolvable, KeyError, TypeError, ValueError):
                fail()
            walk(target)
        for keyword in (
            "$defs",
            "definitions",
            "properties",
            "patternProperties",
            "dependentSchemas",
        ):
            for child in node.get(keyword, {}).values():
                walk(child)
        for keyword in (
            "additionalProperties",
            "unevaluatedProperties",
            "propertyNames",
            "items",
            "additionalItems",
            "unevaluatedItems",
            "contains",
            "not",
            "if",
            "then",
            "else",
        ):
            walk(node.get(keyword))
        for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
            for child in node.get(keyword, []):
                walk(child)
        # Legacy dependencies can be property-name arrays or schemas.
        for child in node.get("dependencies", {}).values():
            walk(child)

    walk(schema)


def check_inputs(selection, inputs):
    specs = selection.descriptor.value.tasks[selection.task].inputs
    roles = {s.role: s for s in specs}
    if len(roles) != len(specs) or len({x[0] for x in inputs}) != len(inputs):
        fail()
    supplied = {role for role, _ in inputs}
    if any(s.required and s.role not in supplied for s in specs):
        fail("CAPABILITY_UNAVAILABLE")
    for role, media in inputs:
        if role not in roles or media not in roles[role].media_types:
            fail("CAPABILITY_UNAVAILABLE")


def validate_selection(recipe):
    selection, op = recipe.executor, recipe.operation
    ordered_unique(t.tool_id for t in selection.tools)
    if selection.kind == "cpu_edit":
        asset = recipe.parents[0].asset
        if (selection.output_format.sample_rate, selection.output_format.channels) != (
            asset.sample_rate,
            asset.channels,
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
        if recipe.required_features:
            fail("RECIPE_CONTEXT_MISMATCH")
        return
    desc = selection.descriptor.value
    if selection.descriptor_sha256 != selection.descriptor.sha256:
        fail("RECIPE_HASH_MISMATCH")
    if desc.id != selection.model_id or desc.version != selection.model_version:
        fail("RECIPE_CONTEXT_MISMATCH")
    if selection.mode is not None and selection.mode not in {m.id for m in desc.modes}:
        fail("RECIPE_CONTEXT_MISMATCH")
    task = desc.tasks.get(selection.task)
    if task is None or not task.verified:
        fail("CAPABILITY_UNAVAILABLE")
    for name in recipe.required_features:
        if name not in task.features or not task.features[name].verified:
            fail("CAPABILITY_UNAVAILABLE")
    params = selection.params.wire
    for name in params:
        if name in task.features and not task.features[name].verified:
            fail("CAPABILITY_UNAVAILABLE")
    validate_schema(task.params_schema)
    try:
        if (
            next(Draft202012Validator(task.params_schema).iter_errors(params), None)
            is not None
        ):
            fail()
    except RecipeError:
        raise
    except (Unresolvable, KeyError, TypeError, ValueError):
        fail()
    binding = selection.synthetic_binding
    if selection.evidence_kind == "learned" and binding is not None:
        fail("RECIPE_CONTEXT_MISMATCH")
    if selection.evidence_kind == "synthetic" and (
        binding is None
        or (
            binding.descriptor_sha256,
            binding.engine_id,
            binding.engine_version,
            binding.contract_version,
            binding.expected_image_digest,
        )
        != (
            selection.descriptor_sha256,
            selection.engine_id,
            selection.engine_version,
            selection.contract_version,
            selection.expected_image_digest,
        )
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    coordinates = selection.coordinate_params
    names = (coordinates.at_s, coordinates.t0, coordinates.t1)
    if op.kind == "extend":
        if names[0] is None or names[1:] != (None, None):
            fail("RECIPE_CONTEXT_MISMATCH")
        bindings = [(names[0], op.at_s)]
    elif op.kind == "repaint":
        if names[0] is not None or None in names[1:] or names[1] == names[2]:
            fail("RECIPE_CONTEXT_MISMATCH")
        bindings = list(zip(names[1:], op.region, strict=True))
    else:
        if names != (None, None, None):
            fail("RECIPE_CONTEXT_MISMATCH")
        bindings = []
    for name, expected in bindings:
        spec = task.params_schema.get("properties", {}).get(name, {})
        if (
            spec.get("type") not in {"number", "integer"}
            or type(params.get(name)) not in (int, float)
            or not ideal_equal(params[name], expected)
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
    if (
        op.kind in {"variation_request", "variation_audio", "cover"}
        and selection.output_shape != "full"
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    check_inputs(
        selection,
        []
        if op.kind == "variation_request"
        else [("source", recipe.parents[0].asset.media_type)],
    )


def validate_basis(recipe):
    basis, selection, parent = (
        recipe.operation.basis,
        recipe.executor,
        recipe.parents[0],
    )
    request = basis.request.wire
    fields = {
        "job_id",
        "task",
        "model_id",
        "mode",
        "inputs",
        "params",
        "seed",
        "n_outputs",
        "output_dir",
        "timeout_s",
    }
    if set(request) != fields:
        fail("RECIPE_CONTEXT_MISMATCH")
    closed_model(JobRequest, request)
    try:
        JobRequest.model_validate(request, strict=True)
    except ValidationError:
        fail()
    if digest(encode(request)) != basis.request_sha256:
        fail("RECIPE_HASH_MISMATCH")
    if (
        type(request["seed"]) is not int
        or basis.output_index >= request["n_outputs"]
        or request["seed"] + basis.output_index > 2**64 - 1
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    if (
        parent.origin.kind != "inference"
        or request["inputs"]
        or request["task"] not in {"music.song", "music.instrumental"}
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    if (
        basis.take_id,
        basis.generation_job_id,
        basis.lyrics_version_id,
        request["job_id"],
        request["output_dir"],
    ) != (
        parent.ref.id,
        parent.job_id,
        recipe.lyrics.target_version_id,
        basis.winning_attempt_id,
        f"tmp/{basis.winning_attempt_id}",
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    if (
        parent.origin.seed != request["seed"] + basis.output_index
        or selection.seed == parent.origin.seed
        or parent.origin.model_version != selection.model_version
        or parent.origin.model_id != selection.model_id
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    for field in ("task", "model_id", "mode", "timeout_s"):
        if request[field] != getattr(selection, field):
            fail("RECIPE_CONTEXT_MISMATCH")
    if encode(request["params"]) != encode(selection.params.wire):
        fail("RECIPE_CONTEXT_MISMATCH")


def validate_recipe(recipe):
    op = recipe.operation.kind
    cpu = op in {"trim", "fade", "crossfade"}
    if (recipe.executor.kind == "cpu_edit") != cpu:
        fail("RECIPE_CONTEXT_MISMATCH")
    derivation = "edit" if cpu else "variant" if op.startswith("variation") else op
    if recipe.derivation != derivation or len(recipe.parents) != (
        2 if op == "crossfade" else 1
    ):
        fail("RECIPE_CONTEXT_MISMATCH")
    if not cpu:
        task = {
            "variation_audio": "music.retake",
            "extend": "music.extend",
            "repaint": "music.repaint",
            "cover": "music.cover",
        }.get(op)
        if (
            task
            and recipe.executor.task != task
            or op == "variation_request"
            and recipe.executor.task not in {"music.song", "music.instrumental"}
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
    ids, assets = set(), set()
    for i, parent in enumerate(recipe.parents):
        asset = parent.asset
        role = ("crossfade_a", "crossfade_b")[i] if op == "crossfade" else "source"
        if (
            parent.owner_id != recipe.owner_id
            or parent.song_id != recipe.song_id
            or parent.job_id == recipe.job_id
            or parent.ref.id == recipe.take_id
            or parent.ref.id in ids
            or parent.role != role
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
        ids.add(parent.ref.id)
        if (
            asset.subject_id != parent.ref.id
            or asset.owner_id != recipe.owner_id
            or asset.ref.id == asset.manifest_ref.id
            or asset.ref.id in assets
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
        assets.add(asset.ref.id)
        if asset.rights.manifest_sha256 != asset.manifest_sha256:
            fail("RECIPE_HASH_MISMATCH")
        if parent.commercial_use != asset.rights.commercial_use:
            fail("RECIPE_CONTEXT_MISMATCH")
    if recipe.root_id != min(p.root_id for p in recipe.parents):
        fail("RECIPE_CONTEXT_MISMATCH")
    for parent, expected in zip(recipe.parents, expected_maps(recipe), strict=True):
        actual = [(p.op, p.src, p.dst) for p in parent.section_map.ops]
        if not ideal_equal(actual, expected):
            fail()
    ordered_unique(recipe.required_features)
    validate_lyrics(recipe)
    validate_selection(recipe)
    if op == "variation_request":
        validate_basis(recipe)
    rights = [
        recipe.lyrics.commercial_use,
        *(t.commercial_use for t in recipe.executor.tools),
    ]
    for parent in recipe.parents:
        rights.extend(
            [
                parent.commercial_use,
                parent.asset.rights.commercial_use,
                *(i.commercial_use for i in parent.asset.rights.inputs),
            ]
        )
    if not cpu:
        rights.append(recipe.executor.descriptor.value.commercial_use)
    if recipe.commercial_use != all(rights):
        fail("RECIPE_CONTEXT_MISMATCH")


def prepare(value, *, reading=False):
    if not isinstance(value, Mapping):
        fail()
    value = dict(value)
    selection = value.get("executor")
    if type(selection) is dict and selection.get("kind") == "inference":
        selection = dict(selection)
        value["executor"] = selection
        descriptor = selection.get("descriptor")
        evidence = selection.get("evidence_kind")
        if isinstance(descriptor, FrozenDescriptor):
            descriptor = FrozenDescriptor.read(
                descriptor.payload,
                expected_sha256=descriptor.sha256,
                evidence_kind=evidence,
            )
        elif reading:
            descriptor = FrozenDescriptor.read(
                encode(descriptor),
                expected_sha256=selection.get("descriptor_sha256"),
                evidence_kind=evidence,
            )
        else:
            descriptor = FrozenDescriptor.capture(descriptor, evidence_kind=evidence)
        selection["descriptor"] = descriptor.wire
        binding = selection.get("synthetic_binding")
        if isinstance(binding, SyntheticBinding):
            selection["synthetic_binding"] = binding.model_dump(mode="json")
    json_guard(value, allow_namespaces=True)
    if len(encode(value)) > 1024 * 1024:
        fail()
    if type(selection) is dict and selection.get("kind") == "inference":
        selection["descriptor"] = descriptor
    try:
        return CreativeRecipeV1.model_validate(value)
    except ValidationError as error:
        for item in error.errors(include_input=False):
            cause = item.get("ctx", {}).get("error")
            if isinstance(cause, RecipeError):
                raise RecipeError(cause.code, cause.field) from None
            if item.get("type") == "missing" and item["loc"][-1] == "declaration":
                fail("LYRICS_DECLARATION_REQUIRED")
            if item.get("type") == "missing" and "rights" in item["loc"]:
                fail("RIGHTS_DECLARATION_REQUIRED")
        fail()


@private_errors
def capture_recipe(value):
    model = prepare(value)
    payload = encode(model.model_dump(mode="json"))
    if len(payload) > 1024 * 1024:
        fail()
    return CapturedRecipe(model, payload, digest(payload))


@private_errors
def capture_request(value):
    recipe = value if isinstance(value, CapturedRecipe) else capture_recipe(value)
    model = CreativeRequestV1(
        kind="creative_recipe",
        schema_version=1,
        recipe=recipe.value,
        recipe_sha256=recipe.sha256,
    )
    payload = encode(model.model_dump(mode="json"))
    if len(payload) > 1024 * 1024:
        fail()
    return CapturedRequest(model, payload, digest(payload), recipe)


@private_errors
def read_recipe(payload, *, schema_version, expected_sha256):
    if type(schema_version) is not int or schema_version != 1:
        fail("RECIPE_VERSION_UNSUPPORTED")
    if type(payload) is not bytes:
        fail()
    if digest(payload) != expected_sha256:
        fail("RECIPE_HASH_MISMATCH")
    value = prepare(parse(payload), reading=True)
    if encode(value.model_dump(mode="json")) != payload:
        fail("RECIPE_HASH_MISMATCH")
    return CapturedRecipe(value, payload, expected_sha256)


@private_errors
def read_request(payload, *, expected_sha256=None):
    raw = payload if type(payload) is bytes else None
    if raw is not None:
        if expected_sha256 is not None and digest(raw) != expected_sha256:
            fail("RECIPE_HASH_MISMATCH")
        data = parse(raw, limit=16 * 1024 * 1024)
    else:
        if not isinstance(payload, Mapping):
            fail()
        payload = dict(payload)
        json_guard(payload, legacy=True, allow_namespaces=True)
        data = parse(encode(payload), limit=16 * 1024 * 1024)
        if expected_sha256 is not None and digest(encode(data)) != expected_sha256:
            fail("RECIPE_HASH_MISMATCH")
    if type(data) is not dict:
        fail()
    if "kind" in data or "schema_version" in data:
        if (
            data.get("kind") != "creative_recipe"
            or type(data.get("schema_version")) is not int
            or data.get("schema_version") != 1
        ):
            fail("RECIPE_VERSION_UNSUPPORTED")
        if set(data) != {"kind", "schema_version", "recipe", "recipe_sha256"}:
            fail()
        recipe = read_recipe(
            encode(data["recipe"]),
            schema_version=1,
            expected_sha256=data["recipe_sha256"],
        )
        captured = capture_request(recipe)
        if (
            raw is not None
            and raw != captured.payload
            or encode(data) != captured.payload
        ):
            fail("RECIPE_HASH_MISMATCH")
        return captured
    legacy_validate(data)
    canonical = encode(data)
    return LegacyRequestView(
        raw,
        digest(raw) if raw is not None else None,
        canonical,
        digest(canonical),
        tuple(sorted(data)),
    )


def legacy_validate(value):
    if type(value) is not dict or value.keys() - {
        "params",
        "inputs",
        "seed",
        "n_outputs",
        "timeout_s",
        "mode",
        "required_features",
    }:
        fail()
    json_guard(value, legacy=True)
    if "params" in value and type(value["params"]) is not dict:
        fail()
    for key in ("seed", "n_outputs", "timeout_s"):
        if (
            key in value
            and not (key == "seed" and value[key] is None)
            and (
                type(value[key]) is not int
                or value[key] < (0 if key == "seed" else 1)
                or key == "n_outputs"
                and value[key] > 64
            )
        ):
            fail()
    if "mode" in value and value["mode"] is not None and type(value["mode"]) is not str:
        fail()
    if "required_features" in value and (
        type(value["required_features"]) is not list
        or any(type(x) is not str for x in value["required_features"])
    ):
        fail()
    if "inputs" in value:
        if type(value["inputs"]) is not list:
            fail()
        for item in value["inputs"]:
            if (
                type(item) is not dict
                or item.keys() - {"role", "ref", "output_index"}
                or not {"role", "ref"} <= item.keys()
                or type(item["role"]) is not str
            ):
                fail()
            ref = item["ref"]
            if (
                type(ref) is not dict
                or set(ref) != {"type", "id"}
                or ref["type"] not in {"take", "asset", "upload", "job"}
                or type(ref["id"]) is not str
                or re.fullmatch(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", ref["id"]) is None
            ):
                fail()
            if "output_index" in item and (
                type(item["output_index"]) is not int
                or not 0 <= item["output_index"] <= 63
            ):
                fail()


@private_errors
def canonical_bytes(value):
    if isinstance(value, (CapturedRecipe, CapturedRequest)):
        return value.payload
    if isinstance(value, (CreativeRecipeV1, CreativeRequestV1)):
        return encode(value.model_dump(mode="json"))
    fail()


@private_errors
def canonical_sha256(value):
    return digest(canonical_bytes(value))


@private_errors
def project_input_requirements(recipe):
    value = recipe.value
    if value.executor.kind != "inference":
        fail("RECIPE_CONTEXT_MISMATCH")
    if value.operation.kind == "variation_request":
        check_inputs(value.executor, [])
        return ()
    parent = value.parents[0]
    check_inputs(value.executor, [("source", parent.asset.media_type)])
    return (
        RecipeInputRequirement(
            parent_id=parent.ref.id,
            asset_id=parent.asset.ref.id,
            asset_role="master",
            engine_role="source",
            sha256=parent.asset.sha256,
            media_type=parent.asset.media_type,
        ),
    )


@private_errors
def project_engine_request(recipe, *, attempt_id, inputs):
    requirements = project_input_requirements(recipe)
    if type(inputs) is not tuple or len(inputs) != len(requirements):
        fail("RECIPE_CONTEXT_MISMATCH")
    if any(not isinstance(item, ResolvedRecipeInput) for item in inputs):
        fail()
    check_inputs(recipe.value.executor, [(i.role, i.media_type) for i in inputs])
    for requirement, item in zip(requirements, inputs, strict=True):
        if (item.asset_id, item.role, item.sha256, item.media_type) != (
            requirement.asset_id,
            requirement.engine_role,
            requirement.sha256,
            requirement.media_type,
        ):
            fail("RECIPE_CONTEXT_MISMATCH")
    selection = recipe.value.executor
    try:
        return JobRequest(
            job_id=attempt_id,
            task=selection.task,
            model_id=selection.model_id,
            mode=selection.mode,
            inputs=[
                Input(
                    role=i.role, path=i.path, sha256=i.sha256, media_type=i.media_type
                )
                for i in inputs
            ],
            params=selection.params.wire,
            seed=selection.seed,
            timeout_s=selection.timeout_s,
            n_outputs=1,
            output_dir=f"tmp/{attempt_id}",
        )
    except ValidationError:
        fail()
