"""Contratos CPU cerrados; coherencia de claims sin autoridad de ejecución."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.creative import composition as c
from app.creative import recipes as r
from app.worker.contracts import (
    FileReference,
    PostPlan,
    PreparedPackage,
    RelativePath,
    SourceReference,
)

ULID = r.ULID
SHA256 = r.SHA256


class CpuContractError(ValueError):
    """Error privado del codec, sin entrada ni evidencia productiva."""

    def __init__(self, code="CPU_PACKAGE_INVALID"):
        self.code = code
        super().__init__(code)


def require(condition, code="CPU_PACKAGE_INVALID"):
    if not condition:
        raise CpuContractError(code)


def integer(value):
    require(type(value) is int and 0 <= value <= 2**63 - 1)
    return value


def floating(value):
    require(type(value) is float and math.isfinite(value))
    return value


NonnegativeInt = Annotated[int, BeforeValidator(integer)]
PositiveInt = Annotated[int, BeforeValidator(integer), Field(gt=0)]
FiniteFloat = Annotated[float, BeforeValidator(floating)]
Duration = Annotated[float, BeforeValidator(floating), Field(gt=0)]


def array(value):
    require(type(value) in (list, tuple) and len(value) <= 256)
    return tuple(value)


def encode(value):
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    json_guard(value)
    payload = r.encode(value)
    require(len(payload) <= 1024 * 1024)
    return payload


def json_guard(value):
    """Reubica solo LyricsContext en posiciones declaradas del schema CPU."""
    paths = (
        {
            "cpu_edit_plan": (
                ("request", "recipe", "lyrics"),
                ("provenance", "lyrics"),
            ),
            "creative_recipe": (("recipe", "lyrics"),),
            "cpu_edit_provenance": (("lyrics",),),
            "cpu_prepared_package": (("provenance", "lyrics"),),
        }.get(value.get("kind"), ())
        if type(value) is dict and type(value.get("kind")) is str
        else ()
    )
    if type(value) is dict and set(value) == set(r.LyricsContext.model_fields):
        paths = ((),)
    if (
        type(value) is dict
        and "lyrics" in value
        and ("lyrics",) not in paths
        and set(value) != set(r.CreativeRecipeV1.model_fields)
    ):
        r.json_guard(value["lyrics"], path=("non_schema_lyrics",))
    guarded = value
    for path in paths:
        original = guarded
        for key in path:
            if type(original) is not dict or key not in original:
                break
            original = original[key]
        else:
            context = r.LyricsContext.model_validate(original)
            r.json_guard({"lyrics": context.model_dump(mode="json")})
            replacement = dict(original)
            replacement["versions"] = [
                {**version, "text": ""} for version in original["versions"]
            ]
            guarded = replace_json_path(guarded, path, replacement)
    r.json_guard(guarded, allow_namespaces=True)


def replace_json_path(value, path, replacement):
    if not path:
        return replacement
    key, *rest = path
    return {**value, key: replace_json_path(value[key], rest, replacement)}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def decode(payload, expected_sha256):
    require(type(payload) is bytes)
    require(digest(payload) == expected_sha256, "CPU_HASH_MISMATCH")
    value = r.parse(payload)
    require(type(value) is dict and encode(value) == payload)
    return value


def decode_cpu(payload, expected_sha256, kind):
    value = decode(payload, expected_sha256)
    require(
        value.get("kind") == kind
        and type(value.get("version")) is int
        and value.get("version") == 2,
        "CPU_CONTRACT_UNSUPPORTED",
    )
    return value


class Model(BaseModel):
    model_config = ConfigDict(
        strict=True, frozen=True, extra="forbid", allow_inf_nan=False
    )

    @model_validator(mode="before")
    @classmethod
    def exact_literals(cls, value):
        if type(value) is dict:
            for name in (
                "version",
                "handler_version",
                "output_index",
                "channels",
                "max_passes",
                "output_bits",
                "index",
            ):
                if name in value:
                    require(type(value[name]) is int)
            for name in ("ceiling_dbtp", "max_lufs_delta"):
                if name in value:
                    floating(value[name])
        return value


class ReservationRef(Model):
    type: Literal["cpu_pre_render_reservation"]
    id: ULID


class EdgeRef(Model):
    type: Literal["lineage_edge"]
    id: ULID


class CpuParentBinding(Model):
    edge_ref: EdgeRef
    parent_ref: r.TakeRef
    asset_ref: r.AssetRef
    manifest_ref: r.AssetRef
    role: Literal["source", "crossfade_a", "crossfade_b"]
    master_sha256: SHA256
    manifest_sha256: SHA256
    resolved_map: c.ResolvedEdgeMap


class CpuTakeReservationV2(Model):
    reservation_ref: ReservationRef
    take_ref: r.TakeRef
    output_index: Literal[0]
    root_id: ULID
    parent_bindings: Annotated[
        tuple[CpuParentBinding, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    stage_path: RelativePath
    final_path: RelativePath


class CpuEditProvenanceV2(Model):
    kind: Literal["cpu_edit_provenance"]
    version: Literal[2]
    provider: Literal["local"]
    executor: Literal["server_cpu"]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    execution_id: ULID
    recipe_sha256: SHA256
    composition_sha256: SHA256
    parents: Annotated[
        tuple[r.ParentSnapshot, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    lyrics: r.LyricsContext
    tools: Annotated[
        tuple[r.ToolSelection, ...], BeforeValidator(array), Field(min_length=1)
    ]
    commercial_use: bool


class CpuEditPlanV2(Model):
    kind: Literal["cpu_edit_plan"]
    version: Literal[2]
    handler: Literal["audio.edit"]
    handler_version: Literal[1]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    execution_id: ULID
    execution_ordinal: PositiveInt
    request: r.CreativeRequestV1
    request_sha256: SHA256
    composition: c.CompositionPlanV1
    composition_sha256: SHA256
    provenance: CpuEditProvenanceV2
    provenance_sha256: SHA256
    reservation: CpuTakeReservationV2

    @model_validator(mode="after")
    def coherent(self):
        request = r.read_request(
            encode(self.request), expected_sha256=self.request_sha256
        )
        recipe = request.recipe
        c.read_composition_plan(
            encode(self.composition),
            expected_sha256=self.composition_sha256,
            recipe=recipe,
        )
        value = recipe.value
        require(value.executor.kind == "cpu_edit" and value.derivation == "edit")
        for name in ("owner_id", "song_id", "job_id"):
            require(
                getattr(self, name)
                == getattr(value, name)
                == getattr(self.provenance, name)
            )
        require(self.provenance.execution_id == self.execution_id)
        require(self.provenance.recipe_sha256 == recipe.sha256)
        require(self.provenance.composition_sha256 == self.composition_sha256)
        require(
            self.provenance.parents == value.parents
            and self.provenance.lyrics == value.lyrics
            and self.provenance.tools == value.executor.tools
            and self.provenance.commercial_use == value.commercial_use
        )
        require(
            digest(encode(self.provenance)) == self.provenance_sha256,
            "CPU_HASH_MISMATCH",
        )
        reservation = self.reservation
        require(
            reservation.take_ref.id == value.take_id
            and reservation.root_id == value.root_id == self.composition.root_id
        )
        require(
            reservation.stage_path
            == f"songs/{self.song_id}/takes/.pending-{self.execution_id}/{value.take_id}"
        )
        require(reservation.final_path == f"songs/{self.song_id}/takes/{value.take_id}")
        require(len(reservation.parent_bindings) == len(value.parents))
        require(
            len({binding.edge_ref.id for binding in reservation.parent_bindings})
            == len(reservation.parent_bindings)
        )
        for binding, parent, edge in zip(
            reservation.parent_bindings,
            value.parents,
            self.composition.edges,
            strict=True,
        ):
            require(
                binding.parent_ref == parent.ref
                and binding.asset_ref == parent.asset.ref
                and binding.manifest_ref == parent.asset.manifest_ref
            )
            require(
                binding.role == parent.role
                and binding.master_sha256 == parent.asset.sha256
                and binding.manifest_sha256 == parent.asset.manifest_sha256
                and binding.resolved_map == edge
            )
        return self


@dataclass(frozen=True)
class CapturedCpuEditPlan:
    value: CpuEditPlanV2
    payload: bytes
    sha256: str


def read_cpu_edit_plan(
    payload: bytes, *, expected_sha256: SHA256
) -> CapturedCpuEditPlan:
    value = CpuEditPlanV2.model_validate(
        decode_cpu(payload, expected_sha256, "cpu_edit_plan")
    )
    require(encode(value) == payload)
    return CapturedCpuEditPlan(value, payload, expected_sha256)


def capture_cpu_edit_plan(
    *,
    request: r.CreativeRequestV1,
    composition: c.CapturedCompositionPlan,
    execution_id: ULID,
    execution_ordinal: int,
    reservation: CpuTakeReservationV2,
) -> CapturedCpuEditPlan:
    require(
        type(request) is r.CreativeRequestV1
        and type(composition) is c.CapturedCompositionPlan
        and type(reservation) is CpuTakeReservationV2
    )
    require(
        encode(composition.value) == composition.payload
        and digest(composition.payload) == composition.sha256,
        "CPU_HASH_MISMATCH",
    )
    recipe = request.recipe
    provenance = CpuEditProvenanceV2(
        kind="cpu_edit_provenance",
        version=2,
        provider="local",
        executor="server_cpu",
        owner_id=recipe.owner_id,
        song_id=recipe.song_id,
        job_id=recipe.job_id,
        execution_id=execution_id,
        recipe_sha256=request.recipe_sha256,
        composition_sha256=composition.sha256,
        parents=recipe.parents,
        lyrics=recipe.lyrics,
        tools=recipe.executor.tools,
        commercial_use=recipe.commercial_use,
    )
    value = CpuEditPlanV2(
        kind="cpu_edit_plan",
        version=2,
        handler="audio.edit",
        handler_version=1,
        owner_id=recipe.owner_id,
        song_id=recipe.song_id,
        job_id=recipe.job_id,
        execution_id=execution_id,
        execution_ordinal=execution_ordinal,
        request=request,
        request_sha256=digest(encode(request)),
        composition=composition.value,
        composition_sha256=composition.sha256,
        provenance=provenance,
        provenance_sha256=digest(encode(provenance)),
        reservation=reservation,
    )
    payload = encode(value)
    return read_cpu_edit_plan(payload, expected_sha256=digest(payload))


class CpuEvidenceRefV2(Model):
    evidence_id: ULID
    evidence_sha256: SHA256
    evidence_kind: Literal["measured", "synthetic"]
    role: Literal["decode", "convert", "render", "measure", "terminal", "close"]


class MeasuredCpuSourceV2(Model):
    file: SourceReference
    frames: PositiveInt
    sample_rate: PositiveInt
    channels: Literal[1, 2]
    measurement: CpuEvidenceRefV2
    render: CpuEvidenceRefV2

    @model_validator(mode="after")
    def coherent(self):
        floating(self.file.duration_s)
        integer(self.file.bytes)
        require(self.file.duration_s == float(self.frames / self.sample_rate))
        require(self.measurement.role == "measure" and self.render.role == "render")
        require(self.file.media_type in ("audio/wav", "audio/flac"))
        return self


class EffectiveCpuEdgeV2(Model):
    binding: CpuParentBinding
    map: c.ResolvedEdgeMap
    measurement: CpuEvidenceRefV2

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.map == self.binding.resolved_map and self.measurement.role == "measure"
        )
        return self


class ExecutedToolV2(Model):
    selection: r.ToolSelection
    execution: CpuEvidenceRefV2

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.selection.runtime_verified
            and self.execution.role in ("render", "convert", "measure")
        )
        return self


class CpuEditReceiptV2(Model):
    kind: Literal["cpu_edit_receipt"]
    version: Literal[2]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    execution_id: ULID
    take_id: ULID
    reservation_id: ULID
    output_index: Literal[0]
    plan_sha256: SHA256
    recipe_sha256: SHA256
    composition_sha256: SHA256
    provenance_sha256: SHA256
    source: MeasuredCpuSourceV2
    effective_edges: Annotated[
        tuple[EffectiveCpuEdgeV2, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=2),
    ]
    tools: Annotated[
        tuple[ExecutedToolV2, ...], BeforeValidator(array), Field(min_length=1)
    ]
    terminal_ref: CpuEvidenceRefV2
    terminal_status: Literal["succeeded"]
    commercial_use: bool

    @model_validator(mode="after")
    def coherent(self):
        extension = "wav" if self.source.file.media_type == "audio/wav" else "flac"
        require(
            self.source.file.path
            == f"data/tmp/{self.job_id}/{self.execution_id}/render.{extension}"
        )
        require(self.terminal_ref.role == "terminal")
        return self


@dataclass(frozen=True)
class CapturedCpuEditReceipt:
    value: CpuEditReceiptV2
    payload: bytes
    sha256: str


def checked_plan(plan):
    require(type(plan) is CapturedCpuEditPlan)
    read = read_cpu_edit_plan(plan.payload, expected_sha256=plan.sha256)
    require(read.value == plan.value)
    return read


def read_cpu_receipt(
    payload: bytes, *, expected_sha256: SHA256, plan: CapturedCpuEditPlan
) -> CapturedCpuEditReceipt:
    p = checked_plan(plan).value
    value = CpuEditReceiptV2.model_validate(
        decode_cpu(payload, expected_sha256, "cpu_edit_receipt")
    )
    require(encode(value) == payload)
    for name in (
        "owner_id",
        "song_id",
        "job_id",
        "execution_id",
        "composition_sha256",
        "provenance_sha256",
    ):
        require(getattr(value, name) == getattr(p, name))
    require(
        value.plan_sha256 == plan.sha256
        and value.recipe_sha256 == p.request.recipe_sha256
    )
    require(
        value.take_id == p.reservation.take_ref.id
        and value.reservation_id == p.reservation.reservation_ref.id
    )
    require(
        tuple(edge.binding for edge in value.effective_edges)
        == p.reservation.parent_bindings
    )
    require(tuple(tool.selection for tool in value.tools) == p.provenance.tools)
    require(value.commercial_use == p.provenance.commercial_use)
    require(
        value.source.frames == p.composition.output_frames
        and value.source.sample_rate == p.composition.target_format.sample_rate
        and value.source.channels == p.composition.target_format.channels
    )
    return CapturedCpuEditReceipt(value, payload, expected_sha256)


class CpuClosureBindingV2(Model):
    kind: Literal["cpu_closure"]
    version: Literal[2]
    execution_id: ULID
    plan_sha256: SHA256
    receipt_sha256: SHA256
    close_ref: CpuEvidenceRefV2
    status: Literal["confirmed"]

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.close_ref.role == "close"
            and self.close_ref.evidence_kind == "measured"
        )
        return self


class CpuPublicationBindingV2(Model):
    kind: Literal["cpu_publication_binding"]
    version: Literal[2]
    owner_id: ULID
    song_id: ULID
    post_job_id: ULID
    cpu_execution_id: ULID
    reservation_id: ULID
    intent_id: ULID
    intent_revision_id: ULID
    take_id: ULID
    output_index: Literal[0]
    bound_execution_revision: PositiveInt
    bound_intent_revision: PositiveInt
    plan_sha256: SHA256
    recipe_sha256: SHA256
    composition_sha256: SHA256
    provenance_sha256: SHA256
    receipt_sha256: SHA256
    source_sha256: SHA256
    stage_path: RelativePath
    final_path: RelativePath


class CpuPublicationAuthorityV2(Model):
    kind: Literal["cpu_publication_authority"]
    version: Literal[2]
    origin_kind: Literal["cpu_edit"]
    owner_id: ULID
    song_id: ULID
    post_job_id: ULID
    cpu_execution_id: ULID
    reservation_id: ULID
    intent_id: ULID
    intent_revision_id: ULID
    take_id: ULID
    output_index: Literal[0]
    plan_sha256: SHA256
    recipe_sha256: SHA256
    composition_sha256: SHA256
    provenance_sha256: SHA256
    receipt_sha256: SHA256
    source_sha256: SHA256
    closure: CpuClosureBindingV2

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.closure.execution_id == self.cpu_execution_id
            and self.closure.plan_sha256 == self.plan_sha256
            and self.closure.receipt_sha256 == self.receipt_sha256
        )
        return self


class CpuMasterMeasurementV2(Model):
    frames: PositiveInt
    sample_rate: PositiveInt
    channels: Literal[1, 2]
    duration_s: Duration
    integrated_lufs: FiniteFloat
    true_peak_dbtp: FiniteFloat
    evidence: CpuEvidenceRefV2

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.duration_s == float(self.frames / self.sample_rate)
            and self.evidence.role == "measure"
            and self.evidence.evidence_kind == "measured"
        )
        return self


class PreparedPackageCPU(Model):
    kind: Literal["cpu_prepared_package"]
    version: Literal[2]
    authority: CpuPublicationAuthorityV2
    provenance: CpuEditProvenanceV2
    receipt: CpuEditReceiptV2
    master: FileReference
    listen: FileReference
    peaks: FileReference
    manifest: FileReference
    master_measurement: CpuMasterMeasurementV2

    @model_validator(mode="after")
    def coherent(self):
        a = self.authority
        require(
            digest(encode(self.receipt)) == a.receipt_sha256
            and digest(encode(self.provenance)) == a.provenance_sha256,
            "CPU_HASH_MISMATCH",
        )
        receipt = self.receipt
        for name in (
            "owner_id",
            "song_id",
            "take_id",
            "reservation_id",
            "output_index",
            "plan_sha256",
            "recipe_sha256",
            "composition_sha256",
            "provenance_sha256",
        ):
            require(getattr(a, name) == getattr(receipt, name))
        require(
            a.post_job_id == receipt.job_id
            and a.cpu_execution_id == receipt.execution_id
            and a.source_sha256 == receipt.source.file.sha256
        )
        for name in ("owner_id", "song_id", "recipe_sha256", "composition_sha256"):
            require(getattr(a, name) == getattr(self.provenance, name))
        require(
            self.provenance.job_id == a.post_job_id
            and self.provenance.execution_id == a.cpu_execution_id
        )
        base = f"data/songs/{a.song_id}/takes/{a.take_id}/"
        for role, filename, media in (
            ("master", "master.flac", "audio/flac"),
            ("listen", "listen.mp3", "audio/mpeg"),
            ("peaks", "peaks.json", "application/json"),
            ("manifest", "manifest.json", "application/json"),
        ):
            file = getattr(self, role)
            require(file.path == base + filename and file.media_type == media)
            integer(file.bytes)
        return self


@dataclass(frozen=True)
class CapturedCpuPackage:
    value: PreparedPackageCPU
    payload: bytes
    sha256: str


def read_cpu_package(
    payload: bytes,
    *,
    expected_sha256: SHA256,
    plan: CapturedCpuEditPlan,
    receipt: CapturedCpuEditReceipt,
    binding: CpuPublicationBindingV2,
) -> CapturedCpuPackage:
    p = checked_plan(plan).value
    require(
        type(receipt) is CapturedCpuEditReceipt
        and type(binding) is CpuPublicationBindingV2
    )
    read = read_cpu_receipt(receipt.payload, expected_sha256=receipt.sha256, plan=plan)
    require(read.value == receipt.value)
    # Revalidate typed caller values too; model_construct/copy is not a validation gate.
    bound = CpuPublicationBindingV2.model_validate(
        decode(encode(binding), digest(encode(binding)))
    )
    value = PreparedPackageCPU.model_validate(
        decode_cpu(payload, expected_sha256, "cpu_prepared_package")
    )
    require(
        encode(value) == payload
        and value.provenance == p.provenance
        and value.receipt == receipt.value
    )
    require(
        bound.stage_path == p.reservation.stage_path
        and bound.final_path == p.reservation.final_path
    )
    for name in type(bound).model_fields:
        if name not in (
            "kind",
            "version",
            "bound_execution_revision",
            "bound_intent_revision",
            "stage_path",
            "final_path",
        ):
            require(getattr(bound, name) == getattr(value.authority, name))
    return CapturedCpuPackage(value, payload, expected_sha256)


class PreviewPolicyV2(Model):
    kind: Literal["attenuation_pair"]
    version: Literal[1]
    ceiling_dbtp: Literal[-1.0]
    max_lufs_delta: Literal[0.5]
    max_passes: Literal[3]
    output_media_type: Literal["audio/flac"]
    output_bits: Literal[24]
    window: Literal["common_absolute"]


class CpuPreviewRequestV2(Model):
    kind: Literal["cpu_preview_request"]
    version: Literal[2]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    parents: Annotated[
        tuple[r.ParentSnapshot, r.ParentSnapshot], BeforeValidator(array)
    ]
    policy: PreviewPolicyV2
    tools: Annotated[
        tuple[r.ToolSelection, ...], BeforeValidator(array), Field(min_length=1)
    ]
    commercial_use: bool

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.parents[0].ref.id != self.parents[1].ref.id
            and self.parents[0].asset.ref.id != self.parents[1].asset.ref.id
        )
        rights = [tool.commercial_use for tool in self.tools]
        require(len({tool.tool_id for tool in self.tools}) == len(self.tools))
        for parent in self.parents:
            asset = parent.asset
            require(
                parent.owner_id == self.owner_id == asset.owner_id
                and parent.song_id == self.song_id
                and parent.job_id != self.job_id
            )
            require(
                parent.role == "source"
                and asset.subject_id == parent.ref.id
                and asset.ref.id != asset.manifest_ref.id
            )
            require(
                asset.rights.manifest_sha256 == asset.manifest_sha256
                and parent.commercial_use == asset.rights.commercial_use
            )
            rights.extend(
                (
                    parent.commercial_use,
                    asset.rights.commercial_use,
                    *(item.commercial_use for item in asset.rights.inputs),
                )
            )
        require(self.commercial_use == all(rights))
        return self


class CpuPreviewPlanV2(Model):
    kind: Literal["cpu_preview_plan"]
    version: Literal[2]
    handler: Literal["audio.compare"]
    handler_version: Literal[1]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    execution_id: ULID
    execution_ordinal: PositiveInt
    request: CpuPreviewRequestV2
    request_sha256: SHA256

    @model_validator(mode="after")
    def coherent(self):
        for name in ("owner_id", "song_id", "job_id"):
            require(getattr(self, name) == getattr(self.request, name))
        require(
            digest(encode(self.request)) == self.request_sha256, "CPU_HASH_MISMATCH"
        )
        return self


@dataclass(frozen=True)
class CapturedCpuPreviewPlan:
    value: CpuPreviewPlanV2
    payload: bytes
    sha256: str


def capture_cpu_preview_plan(
    *, request: CpuPreviewRequestV2, execution_id: ULID, execution_ordinal: int
) -> CapturedCpuPreviewPlan:
    require(type(request) is CpuPreviewRequestV2)
    value = CpuPreviewPlanV2(
        kind="cpu_preview_plan",
        version=2,
        handler="audio.compare",
        handler_version=1,
        owner_id=request.owner_id,
        song_id=request.song_id,
        job_id=request.job_id,
        execution_id=execution_id,
        execution_ordinal=execution_ordinal,
        request=request,
        request_sha256=digest(encode(request)),
    )
    payload = encode(value)
    return read_cpu_preview_plan(payload, expected_sha256=digest(payload))


def read_cpu_preview_plan(
    payload: bytes, *, expected_sha256: SHA256
) -> CapturedCpuPreviewPlan:
    value = CpuPreviewPlanV2.model_validate(
        decode_cpu(payload, expected_sha256, "cpu_preview_plan")
    )
    require(encode(value) == payload)
    return CapturedCpuPreviewPlan(value, payload, expected_sha256)


class PreviewMeasureV2(Model):
    side: Literal["a", "b"]
    source_sha256: SHA256
    integrated_lufs: FiniteFloat
    true_peak_dbtp: FiniteFloat
    gain_db: FiniteFloat
    measurement: CpuEvidenceRefV2

    @model_validator(mode="after")
    def coherent(self):
        require(self.measurement.role == "measure" and self.gain_db <= 0.0)
        return self


class PreviewPassV2(Model):
    index: Literal[1, 2, 3]
    target_lufs: FiniteFloat
    inputs: Annotated[tuple[PreviewMeasureV2, PreviewMeasureV2], BeforeValidator(array)]
    outputs: Annotated[
        tuple[PreviewMeasureV2, PreviewMeasureV2], BeforeValidator(array)
    ]

    @model_validator(mode="after")
    def coherent(self):
        require(
            tuple(item.side for item in self.inputs)
            == ("a", "b")
            == tuple(item.side for item in self.outputs)
        )
        for source, output in zip(self.inputs, self.outputs, strict=True):
            require(
                source.gain_db == 0.0
                and output.gain_db == self.target_lufs - source.integrated_lufs
            )
        return self


class PreviewOutputV2(Model):
    side: Literal["a", "b"]
    source_parent_id: ULID
    file: SourceReference
    frames: PositiveInt
    sample_rate: PositiveInt
    channels: Literal[1, 2]
    measurement: PreviewMeasureV2
    manifest: FileReference

    @model_validator(mode="after")
    def coherent(self):
        floating(self.file.duration_s)
        integer(self.file.bytes)
        integer(self.manifest.bytes)
        require(
            self.file.duration_s == float(self.frames / self.sample_rate)
            and self.file.media_type == "audio/flac"
        )
        require(
            self.measurement.side == self.side
            and self.measurement.source_sha256 == self.file.sha256
        )
        require(self.manifest.media_type == "application/json")
        return self


class CpuPreviewClosureV2(Model):
    kind: Literal["cpu_preview_closure"]
    version: Literal[2]
    execution_id: ULID
    plan_sha256: SHA256
    close_ref: CpuEvidenceRefV2
    status: Literal["confirmed"]

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.close_ref.role == "close"
            and self.close_ref.evidence_kind == "measured"
        )
        return self


class CpuPreviewReceiptV2(Model):
    kind: Literal["cpu_preview_receipt"]
    version: Literal[2]
    owner_id: ULID
    song_id: ULID
    job_id: ULID
    execution_id: ULID
    plan_sha256: SHA256
    request_sha256: SHA256
    source_bindings: Annotated[
        tuple[r.ParentSnapshot, r.ParentSnapshot], BeforeValidator(array)
    ]
    policy: PreviewPolicyV2
    tools: Annotated[
        tuple[ExecutedToolV2, ...], BeforeValidator(array), Field(min_length=1)
    ]
    passes: Annotated[
        tuple[PreviewPassV2, ...],
        BeforeValidator(array),
        Field(min_length=1, max_length=3),
    ]
    outputs: Annotated[tuple[PreviewOutputV2, PreviewOutputV2], BeforeValidator(array)]
    terminal_ref: CpuEvidenceRefV2
    terminal_status: Literal["succeeded"]
    closure: CpuPreviewClosureV2
    commercial_use: bool

    @model_validator(mode="after")
    def coherent(self):
        require(
            self.closure.execution_id == self.execution_id
            and self.closure.plan_sha256 == self.plan_sha256
            and self.terminal_ref.role == "terminal"
        )
        require(tuple(output.side for output in self.outputs) == ("a", "b"))
        first = self.passes[0]
        ceiling = self.policy.ceiling_dbtp
        expected_target = min(
            *(item.integrated_lufs for item in first.inputs),
            *(
                item.integrated_lufs + ceiling - item.true_peak_dbtp
                for item in first.inputs
            ),
        )
        require(first.target_lufs == expected_target)
        for index, pass_ in enumerate(self.passes, 1):
            require(pass_.index == index and pass_.inputs == first.inputs)
            if index > 1:
                previous = self.passes[index - 2]
                require(
                    any(output.true_peak_dbtp > ceiling for output in previous.outputs)
                    and pass_.target_lufs < previous.target_lufs
                )
        last = self.passes[-1]
        require(
            abs(last.outputs[0].integrated_lufs - last.outputs[1].integrated_lufs)
            <= self.policy.max_lufs_delta
        )
        require(all(output.true_peak_dbtp <= ceiling for output in last.outputs))
        for parent, source, output, measured in zip(
            self.source_bindings, first.inputs, self.outputs, last.outputs, strict=True
        ):
            require(
                source.source_sha256 == parent.asset.sha256
                and output.source_parent_id == parent.ref.id
                and output.measurement == measured
            )
            require(
                output.file.path
                == f"data/tmp/{self.job_id}/{self.execution_id}/preview-{output.side}.flac"
            )
            require(
                output.manifest.path
                == f"data/tmp/{self.job_id}/{self.execution_id}/manifest.json"
            )
        require(self.outputs[0].manifest == self.outputs[1].manifest)
        return self


@dataclass(frozen=True)
class CapturedCpuPreviewReceipt:
    value: CpuPreviewReceiptV2
    payload: bytes
    sha256: str


def read_cpu_preview_receipt(
    payload: bytes, *, expected_sha256: SHA256, plan: CapturedCpuPreviewPlan
) -> CapturedCpuPreviewReceipt:
    require(type(plan) is CapturedCpuPreviewPlan)
    checked = read_cpu_preview_plan(plan.payload, expected_sha256=plan.sha256)
    require(checked.value == plan.value)
    p = checked.value
    value = CpuPreviewReceiptV2.model_validate(
        decode_cpu(payload, expected_sha256, "cpu_preview_receipt")
    )
    require(encode(value) == payload)
    for name in ("owner_id", "song_id", "job_id", "execution_id", "request_sha256"):
        require(getattr(value, name) == getattr(p, name))
    require(
        value.plan_sha256 == plan.sha256
        and value.source_bindings == p.request.parents
        and value.policy == p.request.policy
        and value.commercial_use == p.request.commercial_use
    )
    require(tuple(tool.selection for tool in value.tools) == p.request.tools)
    return CapturedCpuPreviewReceipt(value, payload, expected_sha256)


CpuFailureCode = Literal[
    "CPU_CONTEXT_INVALID",
    "CPU_CONTRACT_UNSUPPORTED",
    "CPU_HASH_MISMATCH",
    "CPU_EVIDENCE_REQUIRED",
    "CPU_SOURCE_CHANGED",
    "CPU_RIGHTS_CHANGED",
    "CPU_RENDER_FAILED",
    "CPU_MEASUREMENT_FAILED",
    "CPU_CUSTODY_UNKNOWN",
    "CPU_CAS_STALE",
    "CPU_PACKAGE_INVALID",
    "CANCELLED",
]


class CpuEditOutcomeV2(Model):
    kind: Literal["cpu_edit_outcome"]
    version: Literal[2]
    take_id: ULID
    receipt_sha256: SHA256 | None
    status: Literal["ready", "failed", "cancelled"]
    code: CpuFailureCode | None

    @model_validator(mode="after")
    def coherent(self):
        require(
            (
                self.status == "ready"
                and self.receipt_sha256 is not None
                and self.code is None
            )
            or (self.status != "ready" and self.code is not None)
        )
        return self


class CpuPreviewOutcomeV2(Model):
    kind: Literal["cpu_preview_outcome"]
    version: Literal[2]
    status: Literal["ready", "failed", "cancelled"]
    receipt_sha256: SHA256 | None
    code: CpuFailureCode | None

    @model_validator(mode="after")
    def coherent(self):
        require(
            (
                self.status == "ready"
                and self.receipt_sha256 is not None
                and self.code is None
            )
            or (self.status != "ready" and self.code is not None)
        )
        return self


def read_execution_plan(
    payload: bytes,
    *,
    handler: str,
    handler_version: int,
    contract_version: int,
    expected_sha256: SHA256,
) -> PostPlan | CapturedCpuEditPlan | CapturedCpuPreviewPlan:
    require(
        type(handler) is str
        and type(handler_version) is int
        and type(contract_version) is int,
        "CPU_CONTRACT_UNSUPPORTED",
    )
    dispatch = (handler, handler_version, contract_version)
    if dispatch == ("audio.edit", 1, 2):
        return read_cpu_edit_plan(payload, expected_sha256=expected_sha256)
    if dispatch == ("audio.compare", 1, 2):
        return read_cpu_preview_plan(payload, expected_sha256=expected_sha256)
    require(dispatch == ("post.audio", 1, 1), "CPU_CONTRACT_UNSUPPORTED")
    require(
        type(payload) is bytes and digest(payload) == expected_sha256,
        "CPU_HASH_MISMATCH",
    )
    # Original model reader/serializer: do not add keys or rehash legacy wire.
    value = r.parse(payload)
    require(
        type(value) is dict
        and "kind" not in value
        and type(value.get("version")) is int
        and value.get("version") == 1,
        "CPU_CONTRACT_UNSUPPORTED",
    )
    return PostPlan.model_validate(value)


def read_intent_package(
    payload: bytes,
    *,
    origin_kind: str,
    expected_sha256: SHA256,
    plan: PostPlan | CapturedCpuEditPlan,
    receipt: CapturedCpuEditReceipt | None,
    binding: CpuPublicationBindingV2 | None,
) -> PreparedPackage | CapturedCpuPackage:
    if origin_kind == "cpu_edit":
        require(
            type(plan) is CapturedCpuEditPlan
            and type(receipt) is CapturedCpuEditReceipt
            and type(binding) is CpuPublicationBindingV2,
            "CPU_CONTRACT_UNSUPPORTED",
        )
        return read_cpu_package(
            payload,
            expected_sha256=expected_sha256,
            plan=plan,
            receipt=receipt,
            binding=binding,
        )
    require(
        origin_kind == "inference"
        and type(plan) is PostPlan
        and receipt is None
        and binding is None,
        "CPU_CONTRACT_UNSUPPORTED",
    )
    require(
        type(payload) is bytes and digest(payload) == expected_sha256,
        "CPU_HASH_MISMATCH",
    )
    checked = PostPlan.model_validate(r.parse(plan.model_dump_json().encode()))
    data = r.parse(payload)
    require(
        type(data) is dict and "kind" not in data and "version" not in data,
        "CPU_CONTRACT_UNSUPPORTED",
    )
    value = PreparedPackage.model_validate(data)
    require(any(entry.authority == value.authority for entry in checked.takes))
    return value
