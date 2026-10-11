"""Planificación privada pura de composición por muestras, sin render."""

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from functools import wraps
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from app.creative import recipes
from app.creative.recipes import SHA256, ULID, CapturedRecipe, ToolSelection

MAX_FRAMES = 2**63 - 1
MAX_RATE = 2**31 - 1


def exact_int(value):
    if type(value) is not int:
        raise ValueError("integer required")
    return value


def exact_float(value):
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("finite float required")
    return value


FrameCount = Annotated[int, BeforeValidator(exact_int), Field(ge=1, le=MAX_FRAMES)]
Rate = Annotated[int, BeforeValidator(exact_int), Field(ge=1, le=MAX_RATE)]
Channels = Annotated[Literal[1, 2], BeforeValidator(exact_int)]
Duration = Annotated[float, BeforeValidator(exact_float), Field(gt=0)]
BufferId = Literal["parent_a", "parent_b", "engine", "converted_b", "converted_engine"]


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, revalidate_instances="always"
    )


class AudioFormat(Model):
    sample_rate: Rate
    channels: Channels


class MeasurementRef(Model):
    evidence_id: ULID
    evidence_sha256: SHA256
    evidence_kind: Literal["measured", "synthetic"]


class BufferFacts(Model):
    buffer_id: BufferId
    sha256: SHA256
    format: AudioFormat
    frames: FrameCount
    duration_s: Duration
    measurement: MeasurementRef

    @model_validator(mode="after")
    def measured_duration(self):
        if self.duration_s != float(self.frames / self.format.sample_rate):
            raise CompositionError("COMPOSITION_DURATION_MISMATCH")
        return self


def array(value):
    if type(value) not in (tuple, list):
        raise ValueError("array required")
    return tuple(value)


FrameIndex = Annotated[int, BeforeValidator(exact_int), Field(ge=0, le=MAX_FRAMES)]


def positive_span(value):
    if value[0] >= value[1]:
        raise CompositionError("COMPOSITION_INVALID")
    return value


FrameSpan = Annotated[
    tuple[FrameIndex, FrameIndex], BeforeValidator(array), AfterValidator(positive_span)
]


def nominal_range(value):
    if value[0] > value[1]:
        raise CompositionError("COMPOSITION_INVALID")
    return value


NominalFrameRange = Annotated[
    tuple[FrameIndex, FrameIndex], BeforeValidator(array), AfterValidator(nominal_range)
]
ParentRole = Literal["source", "crossfade_a", "crossfade_b"]
Envelope = Literal["identity", "linear_in", "linear_out"]
Operation = Literal[
    "variation_request",
    "variation_audio",
    "extend",
    "repaint",
    "cover",
    "trim",
    "fade",
    "crossfade",
]


class ParentFacts(Model):
    parent_id: ULID
    asset_id: ULID
    root_id: ULID
    role: ParentRole
    buffer: BufferFacts


class EngineFacts(Model):
    recipe_sha256: SHA256
    descriptor_sha256: SHA256
    output_shape: Literal["full", "region"]
    buffer: BufferFacts
    result: MeasurementRef


class ConversionRequirement(Model):
    conversion_id: Literal["b_to_target", "engine_to_target"]
    input_buffer_id: Literal["parent_b", "engine"]
    input_sha256: SHA256
    input_format: AudioFormat
    target_format: AudioFormat
    recipe_sha256: SHA256
    tool: ToolSelection
    channel_policy: Literal[
        "identity", "mono_to_stereo_duplicate", "stereo_to_mono_average"
    ]
    resample_policy: Literal["identity", "soxr_pinned"]


class ConvertedFacts(Model):
    requirement: ConversionRequirement
    buffer: BufferFacts
    evidence: MeasurementRef
    conversion_scope: FrameSpan


class BoundaryResolution(Model):
    key: Literal[
        "trim_start",
        "trim_stop",
        "repaint_start",
        "repaint_stop",
        "extend_at",
        "fade_in_length",
        "fade_out_length",
        "crossfade_length",
    ]
    buffer_id: BufferId
    seconds_decimal: Annotated[str, Field(max_length=32)]
    rate: Rate
    frame: FrameIndex
    anchor: Literal["decimal_half_up", "buffer_start", "buffer_end"]


class RenderTerm(Model):
    buffer_id: BufferId
    span: FrameSpan
    envelope: Envelope


class RenderPiece(Model):
    kind: Literal["copy", "fade", "crossfade"]
    dst: FrameSpan
    terms: Annotated[
        tuple[RenderTerm, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]

    @model_validator(mode="after")
    def coherent(self):
        expected = (
            ("linear_out", "linear_in")
            if self.kind == "crossfade"
            else ("identity",)
            if self.kind == "copy"
            else None
        )
        envelopes = tuple(t.envelope for t in self.terms)
        if (
            expected is not None
            and envelopes != expected
            or self.kind == "fade"
            and (len(envelopes) != 1 or envelopes[0] not in {"linear_in", "linear_out"})
        ):
            raise CompositionError("COMPOSITION_INVALID")
        count = self.dst[1] - self.dst[0]
        if any(t.span[1] - t.span[0] != count for t in self.terms):
            raise CompositionError("COMPOSITION_INVALID")
        if self.kind != "copy":
            envelope_length(count)
        return self


class ResolvedMapOp(Model):
    op: Literal["keep", "fade", "regen", "append", "convert"]
    effect: Literal["keep", "fade", "regen", "append"] | None
    src: FrameSpan | None
    nominal_src: NominalFrameRange | None
    dst: FrameSpan
    render_buffer_id: BufferId
    render_span: FrameSpan
    conversion_id: Literal["b_to_target", "engine_to_target"] | None
    envelope: Envelope
    claim: Literal[
        "direct_copy", "transformed", "generated", "declared_keep_unverified"
    ]

    @model_validator(mode="after")
    def coherent(self):
        kind = self.effect if self.op == "convert" else self.op
        if self.op == "convert":
            if self.effect is None or self.conversion_id is None:
                raise CompositionError("COMPOSITION_INVALID")
            if self.conversion_id == "b_to_target":
                valid = (
                    self.render_buffer_id == "converted_b"
                    and kind in {"keep", "fade"}
                    and self.nominal_src is not None
                    and self.src is None
                    and self.claim == "transformed"
                )
            else:
                valid = (
                    self.render_buffer_id == "converted_engine"
                    and kind in {"keep", "regen", "append"}
                    and self.nominal_src is None
                    and self.claim
                    == ("declared_keep_unverified" if kind == "keep" else "generated")
                    and (self.src is not None if kind == "keep" else self.src is None)
                )
            if not valid:
                raise CompositionError("COMPOSITION_INVALID")
        else:
            if (
                self.effect is not None
                or self.conversion_id is not None
                or self.nominal_src is not None
                or self.render_buffer_id in {"converted_b", "converted_engine"}
            ):
                raise CompositionError("COMPOSITION_INVALID")
            if kind in {"keep", "fade"}:
                if self.src is None or self.claim not in (
                    {"transformed"}
                    if kind == "fade"
                    else {"direct_copy", "declared_keep_unverified"}
                ):
                    raise CompositionError("COMPOSITION_INVALID")
            elif self.src is not None or self.claim != "generated":
                raise CompositionError("COMPOSITION_INVALID")
        if kind == "fade":
            if self.envelope not in {"linear_in", "linear_out"}:
                raise CompositionError("COMPOSITION_INVALID")
            envelope_length(self.dst[1] - self.dst[0])
        elif self.envelope != "identity":
            raise CompositionError("COMPOSITION_INVALID")
        if self.dst[1] - self.dst[0] != self.render_span[1] - self.render_span[0]:
            raise CompositionError("COMPOSITION_INVALID")
        if (
            self.src is not None
            and self.src[1] - self.src[0] != self.dst[1] - self.dst[0]
        ):
            raise CompositionError("COMPOSITION_INVALID")
        return self


class ResolvedEdgeMap(Model):
    kind: Literal["resolved_frames"]
    parent_id: ULID
    role: ParentRole
    source_format: AudioFormat
    destination_format: AudioFormat
    source_frames: FrameCount
    destination_frames: FrameCount
    ops: Annotated[
        tuple[ResolvedMapOp, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=3),
    ]


class CompositionPlanV1(Model):
    kind: Literal["creative_composition"]
    schema_version: Literal[1]
    recipe_sha256: SHA256
    operation: Operation
    root_id: ULID
    output_shape: Literal["full", "region"] | None
    descriptor_sha256: SHA256 | None
    status: Literal["resolved_unrendered"]
    target_format: AudioFormat
    inputs: Annotated[
        tuple[ParentFacts, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    engine: EngineFacts | None
    conversions: Annotated[
        tuple[ConvertedFacts, ...], BeforeValidator(array), Field(max_length=1)
    ]
    resolutions: Annotated[
        tuple[BoundaryResolution, ...], BeforeValidator(array), Field(max_length=12)
    ]
    pieces: Annotated[
        tuple[RenderPiece, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=3),
    ]
    edges: Annotated[
        tuple[ResolvedEdgeMap, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    output_frames: FrameCount
    output_duration_s: Duration

    @model_validator(mode="before")
    @classmethod
    def version(cls, value):
        if type(value) is dict and (
            type(value.get("schema_version")) is not int
            or value.get("schema_version") != 1
            or value.get("kind") != "creative_composition"
        ):
            raise CompositionError("COMPOSITION_VERSION_UNSUPPORTED")
        return value

    @model_validator(mode="after")
    def coherent(self):
        if self.output_duration_s != float(
            self.output_frames / self.target_format.sample_rate
        ):
            raise CompositionError("COMPOSITION_DURATION_MISMATCH")
        if (
            self.root_id != min(p.root_id for p in self.inputs)
            or len(self.inputs) != (2 if self.operation == "crossfade" else 1)
            or len(self.edges) != len(self.inputs)
        ):
            raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
        buffers = {p.buffer.buffer_id: p.buffer for p in self.inputs}
        if len(buffers) != len(self.inputs) or tuple(buffers) != (
            ("parent_a", "parent_b") if self.operation == "crossfade" else ("parent_a",)
        ):
            raise CompositionError("COMPOSITION_INVALID")
        if self.engine is None:
            if (
                self.operation not in {"trim", "fade", "crossfade"}
                or self.output_shape is not None
                or self.descriptor_sha256 is not None
            ):
                raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
        else:
            if (
                self.operation in {"trim", "fade", "crossfade"}
                or self.engine.output_shape != self.output_shape
                or self.engine.recipe_sha256 != self.recipe_sha256
                or self.engine.descriptor_sha256 != self.descriptor_sha256
                or self.engine.buffer.buffer_id != "engine"
            ):
                raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
            buffers["engine"] = self.engine.buffer
        conversions = {}
        for fact in self.conversions:
            req = fact.requirement
            original = buffers.get(req.input_buffer_id)
            expected_id = (
                "converted_b"
                if req.conversion_id == "b_to_target"
                else "converted_engine"
            )
            if (
                original is None
                or req.conversion_id in conversions
                or req.recipe_sha256 != self.recipe_sha256
                or req.input_sha256 != original.sha256
                or req.input_format != original.format
                or req.target_format != self.target_format
                or fact.buffer.format != self.target_format
                or fact.buffer.buffer_id != expected_id
                or fact.conversion_scope != (0, original.frames)
            ):
                raise CompositionError("COMPOSITION_INVALID")
            buffers[expected_id] = fact.buffer
            conversions[req.conversion_id] = fact
        cursor = 0
        for piece in self.pieces:
            if piece.dst[0] != cursor:
                raise CompositionError("COMPOSITION_INVALID")
            cursor = piece.dst[1]
            for term in piece.terms:
                self.check_render(term.buffer_id, term.span, buffers)
            if piece.kind == "crossfade" and (
                self.operation != "crossfade"
                or piece.terms[0].buffer_id != "parent_a"
                or piece.terms[1].buffer_id not in {"parent_b", "converted_b"}
            ):
                raise CompositionError("COMPOSITION_INVALID")
        if cursor != self.output_frames:
            raise CompositionError("COMPOSITION_INVALID")
        for parent, edge in zip(self.inputs, self.edges, strict=True):
            if (
                edge.parent_id,
                edge.role,
                edge.source_format,
                edge.source_frames,
                edge.destination_format,
                edge.destination_frames,
            ) != (
                parent.parent_id,
                parent.role,
                parent.buffer.format,
                parent.buffer.frames,
                self.target_format,
                self.output_frames,
            ):
                raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
            previous = None
            for op in edge.ops:
                if previous is not None and op.dst[0] != previous:
                    raise CompositionError("COMPOSITION_INVALID")
                previous = op.dst[1]
                if (
                    op.dst[1] > self.output_frames
                    or op.src is not None
                    and op.src[1] > parent.buffer.frames
                    or op.nominal_src is not None
                    and op.nominal_src[1] > parent.buffer.frames
                ):
                    raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")
                self.check_render(op.render_buffer_id, op.render_span, buffers)
                if op.conversion_id is not None and op.conversion_id not in conversions:
                    raise CompositionError("COMPOSITION_FACTS_REQUIRED")
                if (
                    op.conversion_id == "b_to_target"
                    and parent.buffer.buffer_id != "parent_b"
                ):
                    raise CompositionError("COMPOSITION_INVALID")
                if op.claim == "direct_copy" and (
                    op.render_buffer_id != parent.buffer.buffer_id
                    or op.render_span != op.src
                    or parent.buffer.format != self.target_format
                ):
                    raise CompositionError("COMPOSITION_INVALID")
                if op.claim == "declared_keep_unverified" and (
                    self.output_shape != "full"
                    or op.render_buffer_id not in {"engine", "converted_engine"}
                ):
                    raise CompositionError("COMPOSITION_INVALID")
                if op.op == "fade" and (
                    op.render_buffer_id != parent.buffer.buffer_id
                    or op.render_span != op.src
                ):
                    raise CompositionError("COMPOSITION_INVALID")
                if op.claim == "generated" and op.render_buffer_id not in {
                    "engine",
                    "converted_engine",
                }:
                    raise CompositionError("COMPOSITION_INVALID")
        identities = tuple((r.key, r.buffer_id) for r in self.resolutions)
        if len(set(identities)) != len(identities):
            raise CompositionError("COMPOSITION_INVALID")
        for resolution in self.resolutions:
            facts = buffers.get(resolution.buffer_id)
            if (
                facts is None
                or resolution.rate != facts.format.sample_rate
                or resolution.frame > facts.frames
            ):
                raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")
            decimal = resolution.seconds_decimal
            if (
                not math.isfinite(float(decimal))
                or repr(float(decimal)) != decimal
                or float(decimal) < 0
            ):
                raise CompositionError("COMPOSITION_INVALID")
        return self

    def check_render(self, buffer_id, span, buffers):
        facts = buffers.get(buffer_id)
        if facts is None or facts.format != self.target_format:
            raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
        if span[1] > facts.frames:
            raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")


@dataclass(frozen=True)
class CapturedCompositionPlan:
    value: CompositionPlanV1
    payload: bytes
    sha256: str


def encode(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf8")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def capture(plan):
    payload = encode(plan.model_dump(mode="json"))
    return CapturedCompositionPlan(plan, payload, digest(payload))


class CompositionError(ValueError):
    def __init__(self, code, field=None):
        self.code, self.field = code, field
        super().__init__(code)


def private_errors(function):
    """Los errores del borde nunca conservan los datos de entrada."""

    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except CompositionError as error:
            code = error.code
        except ValidationError as error:
            code = "COMPOSITION_INVALID"
            for detail in error.errors(include_url=False, include_input=False):
                if detail["type"] == "less_than_equal" and detail.get("ctx", {}).get(
                    "le"
                ) in {MAX_FRAMES, MAX_RATE}:
                    code = "COMPOSITION_LIMIT_EXCEEDED"
                    break
                if detail["type"] == "missing" and set(detail["loc"]) & {
                    "measurement",
                    "evidence",
                    "result",
                    "buffer",
                }:
                    code = "COMPOSITION_FACTS_REQUIRED"
                    break
                nested = detail.get("ctx", {}).get("error")
                if isinstance(nested, CompositionError):
                    code = nested.code
                    break
        except (
            ValueError,
            TypeError,
            RecursionError,
            OverflowError,
            AttributeError,
            KeyError,
        ):
            code = "COMPOSITION_INVALID"
        raise CompositionError(code)

    return call


@private_errors
def round_frame(seconds, sample_rate):
    if (
        type(seconds) not in (int, float)
        or type(sample_rate) is not int
        or sample_rate < 1
        or seconds < 0
    ):
        raise CompositionError("COMPOSITION_INVALID")
    if sample_rate > MAX_RATE:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
    try:
        seconds = float(seconds)
    except OverflowError:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED") from None
    if not math.isfinite(seconds):
        raise CompositionError("COMPOSITION_INVALID")
    value = Fraction(repr(seconds)) * sample_rate
    result = (2 * value.numerator + value.denominator) // (2 * value.denominator)
    if sample_rate > MAX_RATE or value > MAX_FRAMES or result > MAX_FRAMES:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
    return result


@private_errors
def resolve_region(region, facts):
    facts = BufferFacts.model_validate(facts)
    if type(region) is not tuple or len(region) != 2:
        raise CompositionError("COMPOSITION_INVALID")
    start, stop = region
    if (
        type(start) not in (int, float)
        or type(stop) not in (int, float)
        or start >= stop
    ):
        raise CompositionError("COMPOSITION_INVALID")
    resolved = boundary(start, facts), boundary(stop, facts)
    if resolved[0] >= resolved[1]:
        raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
    return resolved


def boundary(seconds, facts):
    if type(seconds) in (int, float) and seconds == facts.duration_s:
        return facts.frames
    index = round_frame(seconds, facts.format.sample_rate)
    if Fraction(repr(float(seconds))) > Fraction(
        facts.frames, facts.format.sample_rate
    ):
        raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")
    return index


@private_errors
def conversion_requirements(recipe, *, parents, engine):
    structure_limit(parents)
    structure_limit(engine)
    inputs, engine = context(recipe, parents, engine)
    return requirements(recipe, inputs, engine)


def requirements(recipe, inputs, engine):
    target = inputs[0].buffer.format
    original = (
        inputs[1].buffer
        if recipe.value.operation.kind == "crossfade"
        else engine.buffer
        if recipe.value.operation.kind in {"extend", "repaint"}
        else None
    )
    if original is None or original.format == target:
        return ()
    tools = tuple(t for t in recipe.value.executor.tools if t.tool_id == "ffmpeg")
    if not tools:
        raise CompositionError("COMPOSITION_FACTS_REQUIRED")
    if len(tools) != 1:
        raise CompositionError("COMPOSITION_INVALID")
    channel_policy = (
        "identity"
        if original.format.channels == target.channels
        else "mono_to_stereo_duplicate"
        if original.format.channels == 1
        else "stereo_to_mono_average"
    )
    return (
        ConversionRequirement(
            conversion_id="b_to_target"
            if original.buffer_id == "parent_b"
            else "engine_to_target",
            input_buffer_id=original.buffer_id,
            input_sha256=original.sha256,
            input_format=original.format,
            target_format=target,
            recipe_sha256=recipe.sha256,
            tool=tools[0],
            channel_policy=channel_policy,
            resample_policy="identity"
            if original.format.sample_rate == target.sample_rate
            else "soxr_pinned",
        ),
    )


def close_conversion(recipe, inputs, engine, converted):
    needed = requirements(recipe, inputs, engine)
    if len(converted) != len(needed):
        raise CompositionError(
            "COMPOSITION_FACTS_REQUIRED"
            if len(converted) < len(needed)
            else "COMPOSITION_INVALID"
        )
    result = tuple(ConvertedFacts.model_validate(c) for c in converted)
    for fact, req in zip(result, needed, strict=True):
        original = (
            inputs[1].buffer if req.conversion_id == "b_to_target" else engine.buffer
        )
        expected_id = (
            "converted_b" if req.conversion_id == "b_to_target" else "converted_engine"
        )
        if (
            fact.requirement != req
            or fact.buffer.format != req.target_format
            or fact.buffer.buffer_id != expected_id
            or fact.conversion_scope != (0, original.frames)
        ):
            raise CompositionError("COMPOSITION_INVALID")
    return result


def frame_limit(value):
    if value < 0 or value > MAX_FRAMES:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
    return value


def structure_limit(value, depth=0, seen=None):
    if depth > 20:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
    if seen is None:
        seen = set()
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if type(value) in (tuple, list, dict):
        if len(value) > 256:
            raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
        if id(value) in seen:
            raise CompositionError("COMPOSITION_INVALID")
        seen.add(id(value))
        for item in value.values() if type(value) is dict else value:
            structure_limit(item, depth + 1, seen)
        seen.remove(id(value))


def context(recipe, parents, engine):
    if not isinstance(recipe, CapturedRecipe) or type(parents) is not tuple:
        raise CompositionError("COMPOSITION_INVALID")
    try:
        restored = recipes.read_recipe(
            recipe.payload, schema_version=1, expected_sha256=recipe.sha256
        )
    except recipes.RecipeError:
        raise CompositionError("COMPOSITION_HASH_MISMATCH") from None
    if encode(restored.value.model_dump(mode="json")) != encode(
        recipe.value.model_dump(mode="json")
    ):
        raise CompositionError("COMPOSITION_HASH_MISMATCH")
    inputs = tuple(ParentFacts.model_validate(p) for p in parents)
    if len(inputs) != len(recipe.value.parents):
        raise CompositionError(
            "COMPOSITION_FACTS_REQUIRED"
            if len(inputs) < len(recipe.value.parents)
            else "COMPOSITION_CONTEXT_MISMATCH"
        )
    for index, (facts, snapshot) in enumerate(
        zip(inputs, recipe.value.parents, strict=True)
    ):
        if (
            facts.parent_id,
            facts.asset_id,
            facts.root_id,
            facts.role,
            facts.buffer.buffer_id,
            facts.buffer.format.sample_rate,
            facts.buffer.format.channels,
        ) != (
            snapshot.ref.id,
            snapshot.asset.ref.id,
            snapshot.root_id,
            snapshot.role,
            "parent_a" if index == 0 else "parent_b",
            snapshot.asset.sample_rate,
            snapshot.asset.channels,
        ):
            raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
        if facts.buffer.sha256 != snapshot.asset.sha256:
            raise CompositionError("COMPOSITION_HASH_MISMATCH")
        if facts.buffer.duration_s != snapshot.asset.duration_s:
            raise CompositionError("COMPOSITION_DURATION_MISMATCH")
    if min(p.root_id for p in inputs) != recipe.value.root_id:
        raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
    selection = recipe.value.executor
    if selection.kind == "cpu_edit":
        if engine is not None:
            raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
    else:
        if engine is None:
            raise CompositionError("COMPOSITION_FACTS_REQUIRED")
        engine = EngineFacts.model_validate(engine)
        if (
            engine.recipe_sha256 != recipe.sha256
            or engine.descriptor_sha256 != selection.descriptor_sha256
        ):
            raise CompositionError("COMPOSITION_HASH_MISMATCH")
        if (
            engine.output_shape != selection.output_shape
            or engine.buffer.buffer_id != "engine"
        ):
            raise CompositionError("COMPOSITION_CONTEXT_MISMATCH")
    return inputs, engine


@private_errors
def build_composition_plan(recipe, *, parents, engine, converted):
    if type(converted) is not tuple:
        raise CompositionError("COMPOSITION_INVALID")
    structure_limit(parents)
    structure_limit(engine)
    structure_limit(converted)
    inputs, engine = context(recipe, parents, engine)
    converted = close_conversion(recipe, inputs, engine, converted)
    source = inputs[0].buffer
    operation = recipe.value.operation
    target = (
        engine.buffer.format
        if operation.kind in {"variation_request", "variation_audio", "cover"}
        else source.format
    )
    pieces, resolutions, ops = [], [], []
    other_ops = []

    def resolve(key, seconds, facts=source):
        index = boundary(seconds, facts)
        resolutions.append(
            BoundaryResolution(
                key=key,
                buffer_id=facts.buffer_id,
                seconds_decimal=repr(float(seconds)),
                rate=facts.format.sample_rate,
                frame=index,
                anchor="buffer_start"
                if seconds == 0
                else "buffer_end"
                if float(seconds) == facts.duration_s
                else "decimal_half_up",
            )
        )
        return index

    def direct(kind, src, dst, envelope="identity"):
        if dst[0] == dst[1]:
            return
        pieces.append(
            RenderPiece(
                kind="copy" if kind == "keep" else "fade",
                dst=dst,
                terms=(
                    RenderTerm(buffer_id=source.buffer_id, span=src, envelope=envelope),
                ),
            )
        )
        ops.append(
            ResolvedMapOp(
                op=kind,
                effect=None,
                src=src,
                nominal_src=None,
                dst=dst,
                render_buffer_id=source.buffer_id,
                render_span=src,
                conversion_id=None,
                envelope=envelope,
                claim="direct_copy" if kind == "keep" else "transformed",
            )
        )

    if operation.kind == "trim":
        start = resolve("trim_start", operation.region[0])
        stop = resolve("trim_stop", operation.region[1])
        total = stop - start
        if total <= 0:
            raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
        direct("keep", (start, stop), (0, total))
    elif operation.kind == "fade":
        incoming = (
            0
            if operation.fade_in_s is None
            else resolve("fade_in_length", operation.fade_in_s)
        )
        outgoing = (
            0
            if operation.fade_out_s is None
            else resolve("fade_out_length", operation.fade_out_s)
        )
        total = source.frames
        for seconds, count in (
            (operation.fade_in_s, incoming),
            (operation.fade_out_s, outgoing),
        ):
            if seconds is not None:
                envelope_length(count)
        if incoming + outgoing > total:
            raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")
        direct("fade", (0, incoming), (0, incoming), "linear_in")
        direct("keep", (incoming, total - outgoing), (incoming, total - outgoing))
        direct(
            "fade", (total - outgoing, total), (total - outgoing, total), "linear_out"
        )
    elif operation.kind in {"repaint", "extend"}:
        construction = converted[0].buffer if converted else engine.buffer
        if operation.kind == "repaint":
            start = resolve("repaint_start", operation.region[0])
            stop = resolve("repaint_stop", operation.region[1])
            if start >= stop:
                raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
        else:
            start = resolve("extend_at", operation.at_s)
            stop = source.frames
        suffix = source.frames - stop
        generated_kind = "regen" if operation.kind == "repaint" else "append"
        generated = (
            construction.frames
            if engine.output_shape == "region"
            else construction.frames - start - suffix
        )
        if generated <= 0:
            raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
        total = frame_limit(start + generated + suffix)
        for kind, src, dst, render_span in [
            ("keep", (0, start), (0, start), (0, start)),
            (
                generated_kind,
                None,
                (start, start + generated),
                (0, generated)
                if engine.output_shape == "region"
                else (start, start + generated),
            ),
            (
                "keep",
                (stop, source.frames),
                (start + generated, total),
                (stop, source.frames)
                if engine.output_shape == "region"
                else (start + generated, total),
            ),
        ]:
            if dst[0] == dst[1]:
                continue
            render_id = (
                "parent_a"
                if kind == "keep" and engine.output_shape == "region"
                else construction.buffer_id
            )
            is_converted = render_id == "converted_engine"
            ops.append(
                ResolvedMapOp(
                    op="convert" if is_converted else kind,
                    effect=kind if is_converted else None,
                    src=src,
                    nominal_src=None,
                    dst=dst,
                    render_buffer_id=render_id,
                    render_span=render_span,
                    conversion_id="engine_to_target" if is_converted else None,
                    envelope="identity",
                    claim="generated"
                    if kind != "keep"
                    else "direct_copy"
                    if engine.output_shape == "region"
                    else "declared_keep_unverified",
                )
            )
            if engine.output_shape == "region":
                pieces.append(
                    RenderPiece(
                        kind="copy",
                        dst=dst,
                        terms=(
                            RenderTerm(
                                buffer_id=render_id,
                                span=render_span,
                                envelope="identity",
                            ),
                        ),
                    )
                )
        if engine.output_shape == "full":
            pieces.append(
                RenderPiece(
                    kind="copy",
                    dst=(0, total),
                    terms=(
                        RenderTerm(
                            buffer_id=construction.buffer_id,
                            span=(0, total),
                            envelope="identity",
                        ),
                    ),
                )
            )
    elif operation.kind == "crossfade":
        other = inputs[1].buffer
        construction = converted[0].buffer if converted else other
        length = resolve("crossfade_length", operation.duration_s)
        native_length = resolve("crossfade_length", operation.duration_s, other)
        if converted:
            resolve("crossfade_length", operation.duration_s, construction)
        envelope_length(length)
        if native_length <= 0:
            raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
        if length > construction.frames:
            raise CompositionError("COMPOSITION_OUT_OF_BOUNDS")
        total = frame_limit(source.frames + construction.frames - length)
        direct("keep", (0, source.frames - length), (0, source.frames - length))
        dst = (source.frames - length, source.frames)
        terms = (
            RenderTerm(
                buffer_id="parent_a",
                span=(source.frames - length, source.frames),
                envelope="linear_out",
            ),
            RenderTerm(
                buffer_id=construction.buffer_id, span=(0, length), envelope="linear_in"
            ),
        )
        pieces.append(RenderPiece(kind="crossfade", dst=dst, terms=terms))
        ops.append(
            ResolvedMapOp(
                op="fade",
                effect=None,
                src=terms[0].span,
                nominal_src=None,
                dst=dst,
                render_buffer_id="parent_a",
                render_span=terms[0].span,
                conversion_id=None,
                envelope="linear_out",
                claim="transformed",
            )
        )

        def b_op(kind, span, nominal, dst, envelope):
            return ResolvedMapOp(
                op="convert" if converted else kind,
                effect=kind if converted else None,
                src=None if converted else span,
                nominal_src=nominal if converted else None,
                dst=dst,
                render_buffer_id=construction.buffer_id,
                render_span=span,
                conversion_id="b_to_target" if converted else None,
                envelope=envelope,
                claim="transformed" if converted or kind == "fade" else "direct_copy",
            )

        other_ops.append(
            b_op("fade", (0, length), (0, native_length), dst, "linear_in")
        )
        if length < construction.frames:
            span = (length, construction.frames)
            dst = (source.frames, total)
            pieces.append(
                RenderPiece(
                    kind="copy",
                    dst=dst,
                    terms=(
                        RenderTerm(
                            buffer_id=construction.buffer_id,
                            span=span,
                            envelope="identity",
                        ),
                    ),
                )
            )
            other_ops.append(
                b_op("keep", span, (native_length, other.frames), dst, "identity")
            )
    else:
        total = engine.buffer.frames
        span = (0, total)
        pieces.append(
            RenderPiece(
                kind="copy",
                dst=span,
                terms=(RenderTerm(buffer_id="engine", span=span, envelope="identity"),),
            )
        )
        ops.append(
            ResolvedMapOp(
                op="regen",
                effect=None,
                src=None,
                nominal_src=None,
                dst=span,
                render_buffer_id="engine",
                render_span=span,
                conversion_id=None,
                envelope="identity",
                claim="generated",
            )
        )
    edge = ResolvedEdgeMap(
        kind="resolved_frames",
        parent_id=inputs[0].parent_id,
        role=inputs[0].role,
        source_format=source.format,
        destination_format=target,
        source_frames=source.frames,
        destination_frames=total,
        ops=tuple(ops),
    )
    edges = (edge,)
    if other_ops:
        edges += (
            ResolvedEdgeMap(
                kind="resolved_frames",
                parent_id=inputs[1].parent_id,
                role=inputs[1].role,
                source_format=other.format,
                destination_format=source.format,
                source_frames=other.frames,
                destination_frames=total,
                ops=tuple(other_ops),
            ),
        )
    return capture(
        CompositionPlanV1(
            kind="creative_composition",
            schema_version=1,
            recipe_sha256=recipe.sha256,
            operation=operation.kind,
            root_id=recipe.value.root_id,
            output_shape=engine.output_shape if engine else None,
            descriptor_sha256=engine.descriptor_sha256 if engine else None,
            status="resolved_unrendered",
            target_format=target,
            inputs=inputs,
            engine=engine,
            conversions=converted,
            resolutions=tuple(resolutions),
            pieces=tuple(pieces),
            edges=edges,
            output_frames=total,
            output_duration_s=float(total / target.sample_rate),
        )
    )


def envelope_length(count):
    if count == 0:
        raise CompositionError("COMPOSITION_INTERVAL_COLLAPSED")
    if count == 1:
        raise CompositionError("COMPOSITION_ENVELOPE_TOO_SHORT")


@private_errors
def read_composition_plan(payload, *, expected_sha256, recipe):
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf"):
        raise CompositionError("COMPOSITION_INVALID")
    if len(payload) > 1024 * 1024:
        raise CompositionError("COMPOSITION_LIMIT_EXCEEDED")
    if digest(payload) != expected_sha256:
        raise CompositionError("COMPOSITION_HASH_MISMATCH")

    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise CompositionError("COMPOSITION_INVALID")
            value[key] = item
        return value

    def nonfinite(_):
        raise CompositionError("COMPOSITION_INVALID")

    data = json.loads(
        payload.decode("utf8"), object_pairs_hook=pairs, parse_constant=nonfinite
    )
    structure_limit(data)
    if type(data) is not dict:
        raise CompositionError("COMPOSITION_INVALID")
    if (
        type(data.get("schema_version")) is not int
        or data.get("schema_version") != 1
        or data.get("kind") != "creative_composition"
    ):
        raise CompositionError("COMPOSITION_VERSION_UNSUPPORTED")
    plan = CompositionPlanV1.model_validate(data)
    if plan.recipe_sha256 != recipe.sha256:
        raise CompositionError("COMPOSITION_HASH_MISMATCH")
    if encode(plan.model_dump(mode="json")) != payload:
        raise CompositionError("COMPOSITION_INVALID")
    replay = build_composition_plan(
        recipe, parents=plan.inputs, engine=plan.engine, converted=plan.conversions
    )
    if replay.payload != payload:
        raise CompositionError("COMPOSITION_INVALID")
    return replay


@private_errors
def composition_bytes(plan):
    if isinstance(plan, CapturedCompositionPlan):
        payload = composition_bytes(plan.value)
        if payload != plan.payload or digest(payload) != plan.sha256:
            raise CompositionError("COMPOSITION_HASH_MISMATCH")
        return payload
    if not isinstance(plan, CompositionPlanV1):
        raise CompositionError("COMPOSITION_INVALID")
    return encode(CompositionPlanV1.model_validate(plan).model_dump(mode="json"))


@private_errors
def composition_sha256(plan):
    return digest(composition_bytes(plan))
