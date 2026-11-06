"""Codecs CPU puros: fixtures sintéticas, sin autoridad runtime/publicación."""

import hashlib
import json
from pathlib import Path

import pytest
from app.creative import durable_contracts as d
from app.creative import recipes as r
from test_creative_composition import build, captured
from test_creative_recipes import attach_lyrics, uid


def encoded(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def plan_wire(
    kind="trim",
    *,
    verified=False,
    lyrics_mode="instrumental",
    noncommercial=False,
    cpu_parent=False,
    lyrics_text="[Verse]\r\ne\u0301 y ñ",
):
    recipe, parents = captured(kind)
    if verified or lyrics_mode != "instrumental" or noncommercial or cpu_parent:
        changed = recipe.value.model_dump(mode="json")
        if verified:
            for tool in changed["executor"]["tools"]:
                tool["runtime_verified"] = True
        if lyrics_mode != "instrumental":
            attach_lyrics(changed, 0, 13, text=lyrics_text)
            if lyrics_mode == "composite":
                attach_lyrics(changed, 1, 14, declaration="licensed")
            changed["lyrics"].update(
                mode=lyrics_mode,
                target_version_id=uid(13) if lyrics_mode == "single" else None,
            )
        if noncommercial:
            changed["executor"]["tools"][0]["commercial_use"] = False
            changed["commercial_use"] = False
        if cpu_parent:
            changed["parents"][0]["origin"] = {
                "kind": "cpu_edit",
                "recipe_sha256": "c" * 64,
                "execution_id": uid(78),
            }
        recipe = r.capture_recipe(changed)
    request = r.capture_request(recipe)
    composition = build(recipe, parents)
    value = recipe.value
    bindings = [
        {
            "edge_ref": {"type": "lineage_edge", "id": uid(80 + i)},
            "parent_ref": p.ref.model_dump(),
            "asset_ref": p.asset.ref.model_dump(),
            "manifest_ref": p.asset.manifest_ref.model_dump(),
            "role": p.role,
            "master_sha256": p.asset.sha256,
            "manifest_sha256": p.asset.manifest_sha256,
            "resolved_map": edge.model_dump(mode="json"),
        }
        for i, (p, edge) in enumerate(
            zip(value.parents, composition.value.edges, strict=True)
        )
    ]
    provenance = {
        "kind": "cpu_edit_provenance",
        "version": 2,
        "provider": "local",
        "executor": "server_cpu",
        "owner_id": value.owner_id,
        "song_id": value.song_id,
        "job_id": value.job_id,
        "execution_id": uid(70),
        "recipe_sha256": recipe.sha256,
        "composition_sha256": composition.sha256,
        "parents": [p.model_dump(mode="json") for p in value.parents],
        "lyrics": value.lyrics.model_dump(mode="json"),
        "tools": [t.model_dump(mode="json") for t in value.executor.tools],
        "commercial_use": value.commercial_use,
    }
    return {
        "kind": "cpu_edit_plan",
        "version": 2,
        "handler": "audio.edit",
        "handler_version": 1,
        "owner_id": value.owner_id,
        "song_id": value.song_id,
        "job_id": value.job_id,
        "execution_id": uid(70),
        "execution_ordinal": 1,
        "request": request.value.model_dump(mode="json"),
        "request_sha256": request.sha256,
        "composition": composition.value.model_dump(mode="json"),
        "composition_sha256": composition.sha256,
        "provenance": provenance,
        "provenance_sha256": digest(encoded(provenance)),
        "reservation": {
            "reservation_ref": {"type": "cpu_pre_render_reservation", "id": uid(71)},
            "take_ref": {"type": "take", "id": value.take_id},
            "output_index": 0,
            "root_id": value.root_id,
            "parent_bindings": bindings,
            "stage_path": f"songs/{value.song_id}/takes/.pending-{uid(70)}/{value.take_id}",
            "final_path": f"songs/{value.song_id}/takes/{value.take_id}",
        },
    }


def read_plan(value):
    payload = encoded(value)
    return d.read_cpu_edit_plan(payload, expected_sha256=digest(payload))


def test_plan_roundtrip_all_fields_and_three_cpu_operations():
    for kind in ("trim", "fade", "crossfade"):
        value = plan_wire(kind)
        result = read_plan(value)
        assert result.value.model_dump(mode="json") == value
        assert result.payload == encoded(value)
        assert result.sha256 == digest(result.payload)
        assert result.value.reservation.reservation_ref.id == uid(71)
        assert "batch_id" not in type(result.value.reservation).model_fields
        value["execution_ordinal"] = 99
        assert result.value.execution_ordinal == 1
        with pytest.raises(ValueError):
            result.value.execution_ordinal = 99


def test_capture_plan_revalidates_wrappers_and_preserves_synthetic_preflight():
    for kind in ("trim", "fade", "crossfade"):
        recipe, parents = captured(kind)
        request = r.capture_request(recipe)
        composition = build(recipe, parents)
        reservation = d.CpuTakeReservationV2.model_validate(
            plan_wire(kind)["reservation"]
        )
        result = d.capture_cpu_edit_plan(
            request=request.value,
            composition=composition,
            execution_id=uid(70),
            execution_ordinal=1,
            reservation=reservation,
        )
        assert result.payload == encoded(plan_wire(kind))
        assert result.value.provenance.parents == recipe.value.parents
        assert result.value.provenance.tools == recipe.value.executor.tools
        assert (
            result.value.composition.inputs[0].buffer.measurement.evidence_kind
            == "synthetic"
        )
        # Pure capture neither transforms claims nor emits runtime authority.
        assert not hasattr(result, "publish")
        from dataclasses import replace

        with pytest.raises(ValueError):
            d.capture_cpu_edit_plan(
                request=request.value,
                composition=replace(composition, sha256="0" * 64),
                execution_id=uid(70),
                execution_ordinal=1,
                reservation=reservation,
            )


def evidence(role, *, measured=False):
    return {
        "evidence_id": uid(90),
        "evidence_sha256": "e" * 64,
        "evidence_kind": "measured" if measured else "synthetic",
        "role": role,
    }


def receipt_wire(plan):
    p = plan.value
    return {
        "kind": "cpu_edit_receipt",
        "version": 2,
        "owner_id": p.owner_id,
        "song_id": p.song_id,
        "job_id": p.job_id,
        "execution_id": p.execution_id,
        "take_id": p.reservation.take_ref.id,
        "reservation_id": p.reservation.reservation_ref.id,
        "output_index": 0,
        "plan_sha256": plan.sha256,
        "recipe_sha256": p.request.recipe_sha256,
        "composition_sha256": p.composition_sha256,
        "provenance_sha256": p.provenance_sha256,
        "source": {
            "file": {
                "path": f"data/tmp/{p.job_id}/{p.execution_id}/render.wav",
                "sha256": p.request.recipe.parents[0].asset.sha256,
                "media_type": "audio/wav",
                "bytes": 400,
                "duration_s": p.composition.output_duration_s,
            },
            "frames": p.composition.output_frames,
            "sample_rate": p.composition.target_format.sample_rate,
            "channels": p.composition.target_format.channels,
            "measurement": evidence("measure"),
            "render": evidence("render"),
        },
        "effective_edges": [
            {
                "binding": b.model_dump(mode="json"),
                "map": b.resolved_map.model_dump(mode="json"),
                "measurement": evidence("measure"),
            }
            for b in p.reservation.parent_bindings
        ],
        "tools": [
            {"selection": t.model_dump(mode="json"), "execution": evidence("render")}
            for t in p.provenance.tools
        ],
        "terminal_ref": evidence("terminal"),
        "terminal_status": "succeeded",
        "commercial_use": p.provenance.commercial_use,
    }


def read_receipt(value, plan):
    payload = encoded(value)
    return d.read_cpu_receipt(payload, expected_sha256=digest(payload), plan=plan)


def test_receipt_roundtrip_own_domains_measured_source_and_synthetic_claims():
    for kind in ("trim", "fade", "crossfade"):
        plan = read_plan(plan_wire(kind, verified=True))
        value = receipt_wire(plan)
        result = read_receipt(value, plan)
        assert result.value.model_dump(mode="json") == value
        assert result.payload == encoded(value) and result.sha256 == digest(
            result.payload
        )
        assert (
            result.value.source.file.duration_s
            == result.value.source.frames / result.value.source.sample_rate
        )
        assert (
            result.value.source.file.sha256
            == plan.value.request.recipe.parents[0].asset.sha256
        )
        assert result.value.terminal_ref.evidence_kind == "synthetic"
        assert not hasattr(result, "verified_cpu_evidence")
        value["source"]["frames"] += 1
        assert result.value.source.frames == plan.value.composition.output_frames


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("reservation_id",), uid(72)),
        (("take_id",), uid(72)),
        (("execution_id",), uid(72)),
        (("owner_id",), uid(72)),
        (("song_id",), uid(72)),
        (("job_id",), uid(72)),
        (("plan_sha256",), "0" * 64),
        (("recipe_sha256",), "0" * 64),
        (("composition_sha256",), "0" * 64),
        (("provenance_sha256",), "0" * 64),
        (("source", "frames"), 1),
        (("source", "sample_rate"), 11),
        (("source", "channels"), 1),
        (("source", "file", "duration_s"), 10.0),
        (("source", "file", "path"), "data/tmp/wrong/render.wav"),
        (("source", "file", "media_type"), "audio/flac"),
        (("source", "measurement", "role"), "render"),
        (("source", "render", "role"), "measure"),
        (("terminal_ref", "role"), "close"),
        (("effective_edges", 0, "measurement", "role"), "decode"),
        (("effective_edges", 0, "binding", "edge_ref", "id"), uid(72)),
        (("tools", 0, "selection", "archive_sha256"), "0" * 64),
        (("tools", 0, "selection", "runtime_verified"), False),
        (("tools", 0, "execution", "role"), "terminal"),
        (("commercial_use",), False),
        (("version",), True),
        (("output_index",), False),
        (("source", "frames"), True),
        (("source", "file", "duration_s"), 5),
    ],
)
def test_receipt_rejects_independent_cross_binding_mutations(path, replacement):
    plan = read_plan(plan_wire(verified=True))
    value = receipt_wire(plan)
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(ValueError):
        read_receipt(value, plan)


def binding_wire(plan, receipt):
    p = plan.value
    return {
        "kind": "cpu_publication_binding",
        "version": 2,
        "owner_id": p.owner_id,
        "song_id": p.song_id,
        "post_job_id": p.job_id,
        "cpu_execution_id": p.execution_id,
        "reservation_id": p.reservation.reservation_ref.id,
        "intent_id": uid(73),
        "intent_revision_id": uid(74),
        "take_id": p.reservation.take_ref.id,
        "output_index": 0,
        "bound_execution_revision": 3,
        "bound_intent_revision": 1,
        "plan_sha256": plan.sha256,
        "recipe_sha256": p.request.recipe_sha256,
        "composition_sha256": p.composition_sha256,
        "provenance_sha256": p.provenance_sha256,
        "receipt_sha256": receipt.sha256,
        "source_sha256": receipt.value.source.file.sha256,
        "stage_path": p.reservation.stage_path,
        "final_path": p.reservation.final_path,
    }


def package_wire(plan, receipt):
    binding = binding_wire(plan, receipt)
    authority = {
        key: value
        for key, value in binding.items()
        if key
        not in (
            "stage_path",
            "final_path",
            "bound_execution_revision",
            "bound_intent_revision",
        )
    }
    authority.update(
        kind="cpu_publication_authority",
        origin_kind="cpu_edit",
        closure={
            "kind": "cpu_closure",
            "version": 2,
            "execution_id": plan.value.execution_id,
            "plan_sha256": plan.sha256,
            "receipt_sha256": receipt.sha256,
            "close_ref": evidence("close", measured=True),
            "status": "confirmed",
        },
    )
    base = f"data/songs/{plan.value.song_id}/takes/{receipt.value.take_id}/"
    files = {
        role: {
            "path": base + filename,
            "sha256": "f" * 64,
            "bytes": 400,
            "media_type": media,
        }
        for role, filename, media in (
            ("master", "master.flac", "audio/flac"),
            ("listen", "listen.mp3", "audio/mpeg"),
            ("peaks", "peaks.json", "application/json"),
            ("manifest", "manifest.json", "application/json"),
        )
    }
    source = receipt.value.source
    return dict(
        kind="cpu_prepared_package",
        version=2,
        authority=authority,
        provenance=plan.value.provenance.model_dump(mode="json"),
        receipt=receipt.value.model_dump(mode="json"),
        **files,
        master_measurement={
            "frames": source.frames,
            "sample_rate": source.sample_rate,
            "channels": source.channels,
            "duration_s": source.file.duration_s,
            "integrated_lufs": -18.0,
            "true_peak_dbtp": -1.5,
            "evidence": evidence("measure", measured=True),
        },
    )


def package_context():
    plan = read_plan(plan_wire(verified=True))
    receipt = read_receipt(receipt_wire(plan), plan)
    return plan, receipt


def test_package_roundtrip_final_ids_are_separate_from_plan_and_receipt():
    plan, receipt = package_context()
    binding = d.CpuPublicationBindingV2.model_validate(binding_wire(plan, receipt))
    value = package_wire(plan, receipt)
    # A caller supplies only typed, coherent claims; this is not a row resolver.
    payload = encoded(value)
    result = d.read_cpu_package(
        payload,
        expected_sha256=digest(payload),
        plan=plan,
        receipt=receipt,
        binding=binding,
    )
    assert result.value.model_dump(mode="json") == value
    assert result.payload == payload and result.sha256 == digest(payload)
    assert plan.payload == encoded(plan_wire(verified=True))
    assert "intent_id" not in json.loads(plan.payload)["reservation"]
    assert "intent_id" not in json.loads(receipt.payload)
    assert result.value.authority.closure.receipt_sha256 == receipt.sha256
    assert not hasattr(result, "publish")


def test_package_rejects_other_final_publication_binding():
    plan, receipt = package_context()
    value = package_wire(plan, receipt)
    value["authority"]["intent_id"] = uid(75)
    payload = encoded(value)
    binding = d.CpuPublicationBindingV2.model_validate(binding_wire(plan, receipt))
    with pytest.raises(ValueError):
        d.read_cpu_package(
            payload,
            expected_sha256=digest(payload),
            plan=plan,
            receipt=receipt,
            binding=binding,
        )


def preview_plan_wire():
    cpu = plan_wire("crossfade", verified=True)
    parents = cpu["request"]["recipe"]["parents"]
    for parent in parents:
        parent["role"] = "source"
    request = {
        "kind": "cpu_preview_request",
        "version": 2,
        "owner_id": cpu["owner_id"],
        "song_id": cpu["song_id"],
        "job_id": cpu["job_id"],
        "parents": parents,
        "policy": {
            "kind": "attenuation_pair",
            "version": 1,
            "ceiling_dbtp": -1.0,
            "max_lufs_delta": 0.5,
            "max_passes": 3,
            "output_media_type": "audio/flac",
            "output_bits": 24,
            "window": "common_absolute",
        },
        "tools": cpu["provenance"]["tools"],
        "commercial_use": True,
    }
    return {
        "kind": "cpu_preview_plan",
        "version": 2,
        "handler": "audio.compare",
        "handler_version": 1,
        "owner_id": cpu["owner_id"],
        "song_id": cpu["song_id"],
        "job_id": cpu["job_id"],
        "execution_id": uid(76),
        "execution_ordinal": 1,
        "request": request,
        "request_sha256": digest(encoded(request)),
    }


def test_preview_plan_is_own_typed_namespace_without_fake_take():
    value = preview_plan_wire()
    payload = encoded(value)
    result = d.read_cpu_preview_plan(payload, expected_sha256=digest(payload))
    assert result.value.model_dump(mode="json") == value
    assert result.payload == payload and result.sha256 == digest(payload)
    assert "take_id" not in value and "reservation" not in value
    captured_value = d.capture_cpu_preview_plan(
        request=result.value.request,
        execution_id=value["execution_id"],
        execution_ordinal=1,
    )
    assert captured_value == result
    assert (
        result.value.request.parents[0].ref.id != result.value.request.parents[1].ref.id
    )


def preview_receipt_wire(plan):
    p = plan.value
    inputs = [
        {
            "side": side,
            "source_sha256": parent.asset.sha256,
            "integrated_lufs": lufs,
            "true_peak_dbtp": peak,
            "gain_db": 0.0,
            "measurement": evidence("measure"),
        }
        for side, parent, lufs, peak in zip(
            ("a", "b"), p.request.parents, (-18.0, -16.0), (-2.0, -3.0), strict=True
        )
    ]
    outputs = [
        {
            "side": side,
            "source_sha256": sha * 64,
            "integrated_lufs": -18.0,
            "true_peak_dbtp": peak,
            "gain_db": gain,
            "measurement": evidence("measure"),
        }
        for side, sha, peak, gain in zip(
            ("a", "b"), ("c", "d"), (-2.0, -5.0), (0.0, -2.0), strict=True
        )
    ]
    files = [
        {
            "side": side,
            "source_parent_id": parent.ref.id,
            "file": {
                "path": f"data/tmp/{p.job_id}/{p.execution_id}/preview-{side}.flac",
                "sha256": measure["source_sha256"],
                "media_type": "audio/flac",
                "bytes": 100,
                "duration_s": parent.asset.duration_s,
            },
            "frames": int(parent.asset.duration_s * parent.asset.sample_rate),
            "sample_rate": parent.asset.sample_rate,
            "channels": parent.asset.channels,
            "measurement": measure,
            "manifest": {
                "path": f"data/tmp/{p.job_id}/{p.execution_id}/manifest.json",
                "sha256": "f" * 64,
                "media_type": "application/json",
                "bytes": 100,
            },
        }
        for side, parent, measure in zip(
            ("a", "b"), p.request.parents, outputs, strict=True
        )
    ]
    return {
        "kind": "cpu_preview_receipt",
        "version": 2,
        "owner_id": p.owner_id,
        "song_id": p.song_id,
        "job_id": p.job_id,
        "execution_id": p.execution_id,
        "plan_sha256": plan.sha256,
        "request_sha256": p.request_sha256,
        "source_bindings": [
            parent.model_dump(mode="json") for parent in p.request.parents
        ],
        "policy": p.request.policy.model_dump(mode="json"),
        "tools": [
            {"selection": tool.model_dump(mode="json"), "execution": evidence("render")}
            for tool in p.request.tools
        ],
        "passes": [
            {"index": 1, "target_lufs": -18.0, "inputs": inputs, "outputs": outputs}
        ],
        "outputs": files,
        "terminal_ref": evidence("terminal"),
        "terminal_status": "succeeded",
        "closure": {
            "kind": "cpu_preview_closure",
            "version": 2,
            "execution_id": p.execution_id,
            "plan_sha256": plan.sha256,
            "close_ref": evidence("close", measured=True),
            "status": "confirmed",
        },
        "commercial_use": p.request.commercial_use,
    }


def test_preview_receipt_full_roundtrip_and_attenuation_claims():
    payload = encoded(preview_plan_wire())
    plan = d.read_cpu_preview_plan(payload, expected_sha256=digest(payload))
    value = preview_receipt_wire(plan)
    payload = encoded(value)
    result = d.read_cpu_preview_receipt(
        payload, expected_sha256=digest(payload), plan=plan
    )
    assert result.payload == payload and result.sha256 == digest(payload)
    assert result.value.model_dump(mode="json") == value
    assert tuple(output.side for output in result.value.outputs) == ("a", "b")
    assert result.value.outputs[1].measurement.gain_db == -2.0
    assert not hasattr(result, "ready_take_ids")
    assert "receipt_sha256" not in result.value.closure.model_dump()


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("execution_id",), uid(77)),
        (("plan_sha256",), "0" * 64),
        (("request_sha256",), "0" * 64),
        (("owner_id",), uid(77)),
        (("source_bindings", 0, "asset", "sha256"), "0" * 64),
        (("policy", "max_passes"), True),
        (("commercial_use",), False),
        (("passes", 0, "index"), 2),
        (("passes", 0, "target_lufs"), -16.0),
        (("passes", 0, "inputs", 0, "gain_db"), 1.0),
        (("passes", 0, "outputs", 1, "gain_db"), -1.0),
        (("passes", 0, "outputs", 1, "integrated_lufs"), -16.0),
        (("passes", 0, "outputs", 0, "true_peak_dbtp"), 0.0),
        (("outputs", 0, "side"), "b"),
        (("outputs", 0, "source_parent_id"), uid(77)),
        (("outputs", 0, "file", "sha256"), "0" * 64),
        (("outputs", 0, "file", "path"), "data/tmp/wrong.flac"),
        (("outputs", 0, "file", "duration_s"), 1.0),
        (("outputs", 0, "manifest", "media_type"), "audio/wav"),
        (("closure", "execution_id"), uid(77)),
        (("closure", "plan_sha256"), "0" * 64),
        (("closure", "close_ref", "role"), "terminal"),
        (("closure", "close_ref", "evidence_kind"), "synthetic"),
        (("terminal_ref", "role"), "close"),
        (("tools", 0, "selection", "runtime_verified"), False),
    ],
)
def test_preview_receipt_rejects_independent_mutations(path, replacement):
    payload = encoded(preview_plan_wire())
    plan = d.read_cpu_preview_plan(payload, expected_sha256=digest(payload))
    value = preview_receipt_wire(plan)
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    payload = encoded(value)
    with pytest.raises(ValueError):
        d.read_cpu_preview_receipt(payload, expected_sha256=digest(payload), plan=plan)


def test_outcomes_reject_ready_without_receipt_and_failed_without_code():
    for model, kind, extra in (
        (d.CpuEditOutcomeV2, "cpu_edit_outcome", {"take_id": uid(8)}),
        (d.CpuPreviewOutcomeV2, "cpu_preview_outcome", {}),
    ):
        valid = dict(
            kind=kind,
            version=2,
            status="ready",
            receipt_sha256="a" * 64,
            code=None,
            **extra,
        )
        assert model.model_validate(valid).model_dump() == valid
        with pytest.raises(ValueError):
            model.model_validate({**valid, "receipt_sha256": None})
        for status in ("failed", "cancelled"):
            failed = {
                **valid,
                "status": status,
                "receipt_sha256": None,
                "code": "CANCELLED",
            }
            assert model.model_validate(failed).model_dump() == failed
            with pytest.raises(ValueError):
                model.model_validate({**failed, "code": None})


def test_dispatch_exact_cpu_tuples_and_package_branch():
    plan, receipt = package_context()
    read = d.read_execution_plan(
        plan.payload,
        handler="audio.edit",
        handler_version=1,
        contract_version=2,
        expected_sha256=plan.sha256,
    )
    assert read == plan
    payload = encoded(preview_plan_wire())
    preview = d.read_execution_plan(
        payload,
        handler="audio.compare",
        handler_version=1,
        contract_version=2,
        expected_sha256=digest(payload),
    )
    assert preview.value.model_dump(mode="json") == preview_plan_wire()
    payload = encoded(package_wire(plan, receipt))
    package = d.read_intent_package(
        payload,
        origin_kind="cpu_edit",
        expected_sha256=digest(payload),
        plan=plan,
        receipt=receipt,
        binding=d.CpuPublicationBindingV2.model_validate(binding_wire(plan, receipt)),
    )
    assert package.payload == payload
    for handler, hv, cv in (
        ("audio.edit", True, 2),
        ("audio.edit", 1, True),
        ("audio.edit", 1, 1),
        ("post.audio", 1, 2),
        ("audio.compare", 1, 2),
        ("unsupported", 1, 2),
    ):
        with pytest.raises(ValueError):
            d.read_execution_plan(
                plan.payload,
                handler=handler,
                handler_version=hv,
                contract_version=cv,
                expected_sha256=plan.sha256,
            )


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("version",), True),
        (("version",), 3),
        (("handler_version",), True),
        (("handler",), "post.audio"),
        (("execution_ordinal",), True),
        (("execution_ordinal",), 0),
        (("execution_ordinal",), 2**63),
        (("execution_id",), "bad"),
        (("owner_id",), uid(79)),
        (("song_id",), uid(79)),
        (("job_id",), uid(79)),
        (("request_sha256",), "0" * 64),
        (("composition_sha256",), "0" * 64),
        (("provenance_sha256",), "0" * 64),
        (("provenance", "execution_id"), uid(79)),
        (("provenance", "parents"), []),
        (("provenance", "tools"), []),
        (("reservation", "take_ref", "id"), uid(79)),
        (("reservation", "root_id"), uid(79)),
        (("reservation", "output_index"), False),
        (("reservation", "stage_path"), "songs/wrong"),
        (("reservation", "final_path"), "songs/wrong"),
        (("reservation", "parent_bindings"), []),
        (("reservation", "parent_bindings", 0, "role"), "crossfade_a"),
        (("reservation", "parent_bindings", 0, "parent_ref", "id"), uid(79)),
        (("reservation", "parent_bindings", 0, "asset_ref", "id"), uid(79)),
        (("reservation", "parent_bindings", 0, "manifest_ref", "id"), uid(79)),
        (("reservation", "parent_bindings", 0, "master_sha256"), "0" * 64),
        (("reservation", "parent_bindings", 0, "manifest_sha256"), "0" * 64),
    ],
)
def test_plan_rejects_independent_mutations(path, replacement):
    value = plan_wire()
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(ValueError):
        read_plan(value)


@pytest.mark.parametrize(
    "extra",
    [
        "batch_id",
        "intent_ref",
        "revision_ref",
        "source_sha256",
        "receipt",
        "seed",
        "model_id",
    ],
)
def test_plan_reservation_forbids_future_authority_and_duplicate_batch(extra):
    value = plan_wire()
    value["reservation"][extra] = uid(79)
    with pytest.raises(ValueError):
        read_plan(value)


@pytest.mark.parametrize(
    "damage",
    [
        "hash",
        "whitespace",
        "newline",
        "bom",
        "duplicate",
        "nonfinite",
        "depth",
        "collection",
        "size",
        "invalid_utf8",
        "json_scalar",
        "string_payload",
    ],
)
def test_plan_reader_rejects_json_hash_canonical_and_resource_damage(damage):
    raw = encoded(plan_wire())
    if damage == "whitespace":
        raw = json.dumps(plan_wire()).encode()
    elif damage == "newline":
        raw += b"\n"
    elif damage == "bom":
        raw = b"\xef\xbb\xbf" + raw
    elif damage == "duplicate":
        raw = b'{"version":2,' + raw[1:]
    elif damage == "nonfinite":
        raw = raw.replace(b'"execution_ordinal":1', b'"execution_ordinal":NaN')
    elif damage == "depth":
        raw = b'{"extra":' + b"[" * 22 + b"0" + b"]" * 22 + b"}"
    elif damage == "collection":
        raw = encoded({"extra": [0] * 257})
    elif damage == "size":
        raw = b'{"extra":"' + b"a" * (1024 * 1024) + b'"}'
    elif damage == "invalid_utf8":
        raw = b'{"extra":"\xff"}'
    elif damage == "json_scalar":
        raw = b"null"
    if damage == "string_payload":
        with pytest.raises(ValueError):
            d.read_cpu_edit_plan(raw.decode(), expected_sha256=digest(raw))
    else:
        with pytest.raises(ValueError):
            d.read_cpu_edit_plan(
                raw, expected_sha256="0" * 64 if damage == "hash" else digest(raw)
            )


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("authority", "cpu_execution_id"), uid(79)),
        (("authority", "reservation_id"), uid(79)),
        (("authority", "receipt_sha256"), "0" * 64),
        (("authority", "closure", "execution_id"), uid(79)),
        (("authority", "closure", "receipt_sha256"), "0" * 64),
        (("authority", "closure", "close_ref", "evidence_kind"), "synthetic"),
        (("master", "path"), "data/songs/wrong/master.flac"),
        (("listen", "media_type"), "audio/flac"),
        (("master_measurement", "duration_s"), 1.0),
        (("master_measurement", "integrated_lufs"), 0),
        (("master_measurement", "evidence", "role"), "render"),
        (("master_measurement", "evidence", "evidence_kind"), "synthetic"),
        (("provenance", "commercial_use"), False),
        (("receipt", "commercial_use"), False),
    ],
)
def test_package_rejects_independent_mutations(path, replacement):
    plan, receipt = package_context()
    value = package_wire(plan, receipt)
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    payload = encoded(value)
    with pytest.raises(ValueError):
        d.read_cpu_package(
            payload,
            expected_sha256=digest(payload),
            plan=plan,
            receipt=receipt,
            binding=d.CpuPublicationBindingV2.model_validate(
                binding_wire(plan, receipt)
            ),
        )


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("request", "parents", 1, "ref", "id"), uid(4)),
        (("request", "parents", 0, "role"), "crossfade_a"),
        (("request", "parents", 0, "owner_id"), uid(79)),
        (("request", "parents", 0, "song_id"), uid(79)),
        (("request", "parents", 0, "job_id"), uid(3)),
        (("request", "parents", 0, "asset", "subject_id"), uid(79)),
        (("request", "parents", 0, "asset", "rights", "manifest_sha256"), "0" * 64),
        (("request", "commercial_use"), False),
        (("execution_ordinal",), False),
        (("request_sha256",), "0" * 64),
        (("version",), True),
    ],
)
def test_preview_plan_rejects_independent_context_mutations(path, replacement):
    value = preview_plan_wire()
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    payload = encoded(value)
    with pytest.raises(ValueError):
        d.read_cpu_preview_plan(payload, expected_sha256=digest(payload))


def test_legacy_dispatch_preserves_golden_bytes_hash_and_original_reader_shape():
    from app.worker.contracts import PostPlan, PreparedPackage
    from test_worker_publication_invariants import package
    from test_worker_publication_invariants import plan as original_plan

    golden = Path(__file__).parent / "fixtures/creative/engine-postplan-v1.json"
    raw = golden.read_bytes()
    wanted = digest(raw)
    result = d.read_execution_plan(
        raw,
        handler="post.audio",
        handler_version=1,
        contract_version=1,
        expected_sha256=wanted,
    )
    assert type(result) is PostPlan
    assert result == PostPlan.model_validate_json(raw)
    assert golden.read_bytes() == raw and digest(golden.read_bytes()) == wanted
    original = original_plan()
    raw = encoded(original)
    parsed = d.read_execution_plan(
        raw,
        handler="post.audio",
        handler_version=1,
        contract_version=1,
        expected_sha256=digest(raw),
    )
    assert parsed.model_dump(mode="json") == original
    raw_package = encoded(package())
    parsed_package = d.read_intent_package(
        raw_package,
        origin_kind="inference",
        expected_sha256=digest(raw_package),
        plan=parsed,
        receipt=None,
        binding=None,
    )
    assert type(parsed_package) is PreparedPackage
    assert parsed_package.model_dump(mode="json") == package()
    assert "kind" not in json.loads(raw_package) and "version" not in json.loads(
        raw_package
    )
    # Historic omitted learned evidence stays omitted. A zero seed remains a seed.
    learned = json.loads(golden.read_bytes())
    learned["takes"][0]["authority"]["seed"] = 0
    raw = encoded(learned)
    zero = d.read_execution_plan(
        raw,
        handler="post.audio",
        handler_version=1,
        contract_version=1,
        expected_sha256=digest(raw),
    )
    assert zero.takes[0].authority.seed == 0
    assert zero.model_dump(mode="json")["provenance"] == learned["provenance"]


def test_unknown_cpu_versions_and_cpu_to_m1_fail_with_contract_unsupported():
    plan, _receipt = package_context()
    future = json.loads(plan.payload)
    future["version"] = 3
    payload = encoded(future)
    with pytest.raises(ValueError) as caught:
        d.read_cpu_edit_plan(payload, expected_sha256=digest(payload))
    assert getattr(caught.value, "code", None) == "CPU_CONTRACT_UNSUPPORTED"
    with pytest.raises(ValueError) as caught:
        d.read_execution_plan(
            plan.payload,
            handler="post.audio",
            handler_version=1,
            contract_version=1,
            expected_sha256=plan.sha256,
        )
    assert getattr(caught.value, "code", None) == "CPU_CONTRACT_UNSUPPORTED"


def test_plan_lyrics_context_antecedents_and_false_commercial_use_are_exact():
    for kind, mode in (("trim", "single"), ("crossfade", "composite")):
        value = plan_wire(
            kind, verified=True, lyrics_mode=mode, noncommercial=True, cpu_parent=True
        )
        plan = read_plan(value)
        assert plan.value.provenance.lyrics == plan.value.request.recipe.lyrics
        assert plan.value.provenance.lyrics.mode == mode
        assert plan.value.provenance.parents[0].origin.kind == "cpu_edit"
        assert not plan.value.provenance.commercial_use
        assert b"e\xcc\x81" in plan.payload and b"\xc3\xa9" not in plan.payload
        receipt = read_receipt(receipt_wire(plan), plan)
        assert not receipt.value.commercial_use
        package = package_wire(plan, receipt)
        payload = encoded(package)
        result = d.read_cpu_package(
            payload,
            expected_sha256=digest(payload),
            plan=plan,
            receipt=receipt,
            binding=d.CpuPublicationBindingV2.model_validate(
                binding_wire(plan, receipt)
            ),
        )
        assert (
            result.value.provenance.lyrics.model_dump(mode="json")
            == value["provenance"]["lyrics"]
        )


def test_historical_retry_plans_derive_separate_groups_without_rebinding_old_capture():
    first = read_plan(plan_wire(verified=True))
    second_wire = json.loads(first.payload)
    second_wire["execution_id"] = uid(78)
    second_wire["execution_ordinal"] = 2
    second_wire["provenance"]["execution_id"] = uid(78)
    second_wire["provenance_sha256"] = digest(encoded(second_wire["provenance"]))
    second_wire["reservation"]["reservation_ref"]["id"] = uid(79)
    second_wire["reservation"]["stage_path"] = second_wire["reservation"][
        "stage_path"
    ].replace(uid(70), uid(78))
    second = read_plan(second_wire)
    assert first.value.reservation.reservation_ref.id == uid(71)
    assert second.value.reservation.reservation_ref.id == uid(79)
    assert (
        first.value.request == second.value.request
        and first.value.composition == second.value.composition
    )
    assert first.sha256 != second.sha256
    old_receipt = read_receipt(receipt_wire(first), first)
    with pytest.raises(ValueError):
        d.read_cpu_receipt(
            old_receipt.payload, expected_sha256=old_receipt.sha256, plan=second
        )
    own_receipt = read_receipt(receipt_wire(second), second)
    assert own_receipt.value.reservation_id == uid(79)


def test_preview_second_pass_is_allowed_only_for_lowering_failed_peak_target():
    import copy

    payload = encoded(preview_plan_wire())
    plan = d.read_cpu_preview_plan(payload, expected_sha256=digest(payload))
    value = preview_receipt_wire(plan)
    second = copy.deepcopy(value["passes"][0])
    second.update(index=2, target_lufs=-19.0)
    value["passes"][0]["outputs"][0]["true_peak_dbtp"] = -0.5
    for output in second["outputs"]:
        output["integrated_lufs"] = -19.0
        output["gain_db"] -= 1.0
    value["passes"].append(second)
    for output, measure in zip(value["outputs"], second["outputs"], strict=True):
        output["measurement"] = measure
    payload = encoded(value)
    result = d.read_cpu_preview_receipt(
        payload, expected_sha256=digest(payload), plan=plan
    )
    assert (
        len(result.value.passes) == 2 and result.value.passes[-1].target_lufs == -19.0
    )
    value["passes"][1]["target_lufs"] = -17.0
    payload = encoded(value)
    with pytest.raises(ValueError):
        d.read_cpu_preview_receipt(payload, expected_sha256=digest(payload), plan=plan)


def test_package_dispatch_rejects_preview_missing_binding_and_mixed_branches():
    plan, receipt = package_context()
    payload = encoded(package_wire(plan, receipt))
    for origin, passed_plan, passed_receipt, passed_binding in (
        ("inference", plan, receipt, None),
        ("cpu_edit", plan, None, None),
        ("cpu_preview", plan, receipt, None),
    ):
        with pytest.raises(ValueError):
            d.read_intent_package(
                payload,
                origin_kind=origin,
                expected_sha256=digest(payload),
                plan=passed_plan,
                receipt=passed_receipt,
                binding=passed_binding,
            )


@pytest.mark.parametrize("length", [8192, 8193, 32768])
def test_nested_lyrics_plan_preserves_t02_text_without_normalization(length):
    text = "e\u0301\r\n" + "ñ" * (length - 4)
    wire = plan_wire(lyrics_mode="single", lyrics_text=text)
    plan = read_plan(wire)
    assert plan.payload == encoded(wire)
    assert plan.value.provenance.lyrics.versions[0].text == text
    assert d.encode(plan.value) == plan.payload
    request = r.read_request(
        encoded(wire["request"]), expected_sha256=wire["request_sha256"]
    )
    composition = d.c.read_composition_plan(
        encoded(wire["composition"]),
        expected_sha256=wire["composition_sha256"],
        recipe=request.recipe,
    )
    capture = d.capture_cpu_edit_plan(
        request=request.value,
        composition=composition,
        execution_id=plan.value.execution_id,
        execution_ordinal=plan.value.execution_ordinal,
        reservation=plan.value.reservation,
    )
    assert capture.payload == plan.payload


@pytest.mark.parametrize("length", [8192, 8193, 32768])
def test_nested_lyrics_package_preserves_t02_text(length):
    text = "x" * length
    plan = read_plan(plan_wire(verified=True, lyrics_mode="single", lyrics_text=text))
    receipt = read_receipt(receipt_wire(plan), plan)
    wire = package_wire(plan, receipt)
    payload = encoded(wire)
    package = d.read_cpu_package(
        payload,
        expected_sha256=digest(payload),
        plan=plan,
        receipt=receipt,
        binding=d.CpuPublicationBindingV2.model_validate(binding_wire(plan, receipt)),
    )
    assert package.payload == payload
    assert package.value.provenance.lyrics.versions[0].text == text


@pytest.mark.parametrize(
    "location",
    [
        "other",
        "false_context",
        "preview_fake_context",
        "context_extras",
        "too_long",
        "secret",
        "depth",
        "entries",
    ],
)
def test_contextual_lyrics_does_not_relax_other_json_guards(location):
    wire = plan_wire(lyrics_mode="single")
    if location == "other":
        wire["extra"] = "x" * 8193
    elif location == "false_context":
        wire["extra"] = {"lyrics": {"versions": [{"text": "x" * 8193}]}}
    elif location == "preview_fake_context":
        wire = preview_plan_wire()["request"]
        wire["lyrics"] = plan_wire(lyrics_mode="single", lyrics_text="x" * 8193)[
            "provenance"
        ]["lyrics"]
    elif location == "context_extras":
        wire["provenance"]["lyrics"]["extra"] = "x" * 8193
    elif location == "too_long":
        wire["provenance"]["lyrics"]["versions"][0]["text"] = "x" * 32769
    elif location == "secret":
        wire["provenance"]["lyrics"]["versions"][0]["text"] = "Bearer " + "a" * 20
    elif location == "depth":
        wire["extra"] = json.loads("[" * 21 + "0" + "]" * 21)
    else:
        wire["extra"] = [0] * 257
    with pytest.raises(ValueError):
        d.encode(wire)
    raw = encoded(wire)
    with pytest.raises(ValueError):
        d.decode(raw, digest(raw))


def test_standalone_lyrics_context_preserves_t02_limit():
    wire = plan_wire(lyrics_mode="single", lyrics_text="x" * 32768)["provenance"][
        "lyrics"
    ]
    context = r.LyricsContext.model_validate(wire)
    raw = encoded(wire)
    assert d.encode(context) == raw
    assert d.decode(raw, digest(raw)) == wire


@pytest.mark.parametrize(
    "name",
    [
        "version",
        "handler_version",
        "output_index",
        "channels",
        "max_passes",
        "output_bits",
        "index",
    ],
)
def test_literal_integer_fields_reject_boolean_before_pydantic_coercion(name):
    assert d.Model.exact_literals({name: 1}) == {name: 1}
    with pytest.raises(d.CpuContractError):
        d.Model.exact_literals({name: True})


@pytest.mark.parametrize("name", ["ceiling_dbtp", "max_lufs_delta"])
def test_literal_float_fields_reject_integer_before_pydantic_coercion(name):
    assert d.Model.exact_literals({name: 1.0}) == {name: 1.0}
    with pytest.raises(d.CpuContractError):
        d.Model.exact_literals({name: 1})


@pytest.mark.parametrize("value", [True, -1, 2**63, 1.0])
def test_integer_contract_rejects_each_independent_invalid_domain(value):
    assert d.integer(0) == 0 and d.integer(2**63 - 1) == 2**63 - 1
    with pytest.raises(d.CpuContractError):
        d.integer(value)


@pytest.mark.parametrize("value", [1, True, float("nan"), float("inf"), -float("inf")])
def test_float_contract_rejects_each_independent_invalid_domain(value):
    assert d.floating(0.0) == 0.0
    with pytest.raises(d.CpuContractError):
        d.floating(value)


def test_encoder_rejects_large_total_payload_with_bounded_individual_fields():
    wire = {str(i): "x" * 8192 for i in range(130)}
    with pytest.raises(d.CpuContractError):
        d.encode(wire)


def test_decoder_requires_matching_hash_before_accepting_payload():
    raw = encoded({"ok": True})
    with pytest.raises(d.CpuContractError, match="CPU_HASH_MISMATCH"):
        d.decode(raw, "0" * 64)


@pytest.mark.parametrize(
    "raw",
    [b"null", b'{ "ok": true}', b'{"ok":true}\n'],
    ids=["scalar", "spacing", "newline"],
)
def test_decoder_requires_object_and_canonical_bytes(raw):
    with pytest.raises(d.CpuContractError):
        d.decode(raw, digest(raw))


def coherent_fixture(root):
    import copy

    plan = read_plan(plan_wire(verified=True))
    if root == "edit":
        return plan.value
    receipt = read_receipt(receipt_wire(plan), plan)
    if root == "receipt":
        return receipt.value
    if root == "package":
        return d.PreparedPackageCPU.model_validate(package_wire(plan, receipt))
    raw = encoded(preview_plan_wire())
    preview = d.read_cpu_preview_plan(raw, expected_sha256=digest(raw))
    if root == "preview":
        return preview.value
    wire = preview_receipt_wire(preview)
    if root == "preview_second":
        second = copy.deepcopy(wire["passes"][0])
        second.update(index=2, target_lufs=-19.0)
        wire["passes"][0]["outputs"][0]["true_peak_dbtp"] = -0.5
        for output in second["outputs"]:
            output["integrated_lufs"] = -19.0
            output["gain_db"] -= 1.0
        wire["passes"].append(second)
        for output, measure in zip(wire["outputs"], second["outputs"], strict=True):
            output["measurement"] = measure
    return d.CpuPreviewReceiptV2.model_validate(wire)


def copied_field(value, path, replacement):
    from pydantic import BaseModel

    if not path:
        return replacement
    key, *tail = path
    if isinstance(value, BaseModel):
        return value.model_copy(
            update={key: copied_field(getattr(value, key), tail, replacement)}
        )
    items = list(value)
    items[key] = copied_field(items[key], tail, replacement)
    return tuple(items)


COHERENT_INVALID_CONTEXTS = [
    (
        "CpuEditPlanV2-262-provenance_sha256",
        {
            "root": "edit",
            "object_path": [],
            "path": ["provenance_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuEditPlanV2-262-provenance",
        {
            "root": "edit",
            "object_path": [],
            "path": ["provenance", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-267-root_id",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "root_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditPlanV2-267-id",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "take_ref", "id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditPlanV2-271-stage_path",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "stage_path"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-275-final_path",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "final_path"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-248-owner_id",
        {
            "root": "edit",
            "object_path": [],
            "path": ["owner_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditPlanV2-248-job_id",
        {
            "root": "edit",
            "object_path": [],
            "path": ["job_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditPlanV2-287-parent_ref",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "parent_ref", "type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-287-asset_ref",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "asset_ref", "type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-287-manifest_ref",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "manifest_ref", "type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-292-role",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditPlanV2-292-master_sha256",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "master_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuEditPlanV2-292-manifest_sha256",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "manifest_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuEditPlanV2-292-resolved_map",
        {
            "root": "edit",
            "object_path": [],
            "path": ["reservation", "parent_bindings", 0, "resolved_map", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "MeasuredCpuSourceV2-394-frames",
        {
            "root": "receipt",
            "object_path": ["source"],
            "path": ["frames"],
            "replacement": 52,
        },
    ),
    (
        "MeasuredCpuSourceV2-394-sample_rate",
        {
            "root": "receipt",
            "object_path": ["source"],
            "path": ["sample_rate"],
            "replacement": 11,
        },
    ),
    (
        "MeasuredCpuSourceV2-394-duration_s",
        {
            "root": "receipt",
            "object_path": ["source"],
            "path": ["file", "duration_s"],
            "replacement": 6.1,
        },
    ),
    (
        "MeasuredCpuSourceV2-395-role",
        {
            "root": "receipt",
            "object_path": ["source"],
            "path": ["measurement", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "MeasuredCpuSourceV2-396-media_type",
        {
            "root": "receipt",
            "object_path": ["source"],
            "path": ["file", "media_type"],
            "replacement": "wrong",
        },
    ),
    (
        "EffectiveCpuEdgeV2-407-map",
        {
            "root": "receipt",
            "object_path": ["effective_edges", 0],
            "path": ["map", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "EffectiveCpuEdgeV2-407-role",
        {
            "root": "receipt",
            "object_path": ["effective_edges", 0],
            "path": ["map", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "EffectiveCpuEdgeV2-407-resolved_map",
        {
            "root": "receipt",
            "object_path": ["effective_edges", 0],
            "path": ["binding", "resolved_map", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "ExecutedToolV2-419-runtime_verified",
        {
            "root": "receipt",
            "object_path": ["tools", 0],
            "path": ["selection", "runtime_verified"],
            "replacement": False,
        },
    ),
    (
        "ExecutedToolV2-419-role",
        {
            "root": "receipt",
            "object_path": ["tools", 0],
            "path": ["execution", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditReceiptV2-456-job_id",
        {
            "root": "receipt",
            "object_path": [],
            "path": ["job_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditReceiptV2-456-execution_id",
        {
            "root": "receipt",
            "object_path": [],
            "path": ["execution_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuEditReceiptV2-456-path",
        {
            "root": "receipt",
            "object_path": [],
            "path": ["source", "file", "path"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditReceiptV2-456-file",
        {
            "root": "receipt",
            "object_path": [],
            "path": ["source", "file", "media_type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuEditReceiptV2-460-role",
        {
            "root": "receipt",
            "object_path": [],
            "path": ["terminal_ref", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuClosureBindingV2-528-evidence_kind",
        {
            "root": "package",
            "object_path": ["authority", "closure"],
            "path": ["close_ref", "evidence_kind"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuClosureBindingV2-528-role",
        {
            "root": "package",
            "object_path": ["authority", "closure"],
            "path": ["close_ref", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPublicationAuthorityV2-582-cpu_execution_id",
        {
            "root": "package",
            "object_path": ["authority"],
            "path": ["cpu_execution_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPublicationAuthorityV2-582-plan_sha256",
        {
            "root": "package",
            "object_path": ["authority"],
            "path": ["plan_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPublicationAuthorityV2-582-receipt_sha256",
        {
            "root": "package",
            "object_path": ["authority"],
            "path": ["receipt_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPublicationAuthorityV2-582-execution_id",
        {
            "root": "package",
            "object_path": ["authority"],
            "path": ["closure", "execution_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuMasterMeasurementV2-601-frames",
        {
            "root": "package",
            "object_path": ["master_measurement"],
            "path": ["frames"],
            "replacement": 52,
        },
    ),
    (
        "CpuMasterMeasurementV2-601-sample_rate",
        {
            "root": "package",
            "object_path": ["master_measurement"],
            "path": ["sample_rate"],
            "replacement": 11,
        },
    ),
    (
        "CpuMasterMeasurementV2-601-duration_s",
        {
            "root": "package",
            "object_path": ["master_measurement"],
            "path": ["duration_s"],
            "replacement": 6.1,
        },
    ),
    (
        "CpuMasterMeasurementV2-601-evidence_kind",
        {
            "root": "package",
            "object_path": ["master_measurement"],
            "path": ["evidence", "evidence_kind"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuMasterMeasurementV2-601-role",
        {
            "root": "package",
            "object_path": ["master_measurement"],
            "path": ["evidence", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "PreparedPackageCPU-624-receipt_sha256",
        {
            "root": "package",
            "object_path": [],
            "path": ["authority", "receipt_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "PreparedPackageCPU-624-provenance",
        {
            "root": "package",
            "object_path": [],
            "path": ["provenance", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "PreparedPackageCPU-624-receipt",
        {
            "root": "package",
            "object_path": [],
            "path": ["receipt", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "PreparedPackageCPU-642-source_sha256",
        {
            "root": "package",
            "object_path": [],
            "path": ["authority", "source_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "PreparedPackageCPU-641-reservation_id",
        {
            "root": "package",
            "object_path": [],
            "path": ["authority", "reservation_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "PreparedPackageCPU-641-output_index",
        {
            "root": "package",
            "object_path": [],
            "path": ["authority", "output_index"],
            "replacement": 1,
        },
    ),
    (
        "PreparedPackageCPU-641-plan_sha256",
        {
            "root": "package",
            "object_path": [],
            "path": ["authority", "plan_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "PreparedPackageCPU-661-path",
        {
            "root": "package",
            "object_path": [],
            "path": ["master", "path"],
            "replacement": "wrong",
        },
    ),
    (
        "PreparedPackageCPU-661-media_type",
        {
            "root": "package",
            "object_path": [],
            "path": ["master", "media_type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewRequestV2-774-commercial_use",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["commercial_use"],
            "replacement": False,
        },
    ),
    (
        "CpuPreviewRequestV2-753-owner_id",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["owner_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewRequestV2-753-song_id",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["song_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewRequestV2-758-role",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["parents", 0, "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewRequestV2-758-id",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["parents", 0, "ref", "id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewRequestV2-758-subject_id",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["parents", 0, "asset", "subject_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewRequestV2-763-manifest_sha256",
        {
            "root": "preview",
            "object_path": ["request"],
            "path": ["parents", 0, "asset", "manifest_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewPlanV2-795-request_sha256",
        {
            "root": "preview",
            "object_path": [],
            "path": ["request_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewPlanV2-795-request",
        {
            "root": "preview",
            "object_path": [],
            "path": ["request", "kind"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewPlanV2-794-owner_id",
        {
            "root": "preview",
            "object_path": [],
            "path": ["owner_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewPlanV2-794-song_id",
        {
            "root": "preview",
            "object_path": [],
            "path": ["song_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewPlanV2-794-job_id",
        {
            "root": "preview",
            "object_path": [],
            "path": ["job_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "PreviewMeasureV2-849-gain_db",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0, "inputs", 0],
            "path": ["gain_db"],
            "replacement": 1.0,
        },
    ),
    (
        "PreviewMeasureV2-849-role",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0, "inputs", 0],
            "path": ["measurement", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "PreviewPassV2-863-side",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0],
            "path": ["inputs", 0, "side"],
            "replacement": "wrong",
        },
    ),
    (
        "PreviewPassV2-869-target_lufs",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0],
            "path": ["target_lufs"],
            "replacement": -17.0,
        },
    ),
    (
        "PreviewPassV2-869-integrated_lufs",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0],
            "path": ["inputs", 0, "integrated_lufs"],
            "replacement": -17.0,
        },
    ),
    (
        "PreviewPassV2-869-gain_db",
        {
            "root": "preview_receipt",
            "object_path": ["passes", 0],
            "path": ["inputs", 0, "gain_db"],
            "replacement": 1.0,
        },
    ),
    (
        "PreviewOutputV2-891-frames",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["frames"],
            "replacement": 101,
        },
    ),
    (
        "PreviewOutputV2-891-sample_rate",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["sample_rate"],
            "replacement": 11,
        },
    ),
    (
        "PreviewOutputV2-891-media_type",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["file", "media_type"],
            "replacement": "wrong",
        },
    ),
    (
        "PreviewOutputV2-891-duration_s",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["file", "duration_s"],
            "replacement": 11.0,
        },
    ),
    (
        "PreviewOutputV2-895-side",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["side"],
            "replacement": "wrong",
        },
    ),
    (
        "PreviewOutputV2-895-sha256",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["file", "sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "PreviewOutputV2-895-source_sha256",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["measurement", "source_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "PreviewOutputV2-899-media_type",
        {
            "root": "preview_receipt",
            "object_path": ["outputs", 0],
            "path": ["manifest", "media_type"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewClosureV2-913-evidence_kind",
        {
            "root": "preview_receipt",
            "object_path": ["closure"],
            "path": ["close_ref", "evidence_kind"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewClosureV2-913-role",
        {
            "root": "preview_receipt",
            "object_path": ["closure"],
            "path": ["close_ref", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-949-plan_sha256",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["plan_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewReceiptV2-949-role",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["terminal_ref", "role"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-949-execution_id",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["closure", "execution_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewReceiptV2-964-target_lufs",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "target_lufs"],
            "replacement": -17.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-964-integrated_lufs",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "inputs", 0, "integrated_lufs"],
            "replacement": -17.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-964-true_peak_dbtp",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "inputs", 0, "true_peak_dbtp"],
            "replacement": 0.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-974-max_lufs_delta",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["policy", "max_lufs_delta"],
            "replacement": -0.5,
        },
    ),
    (
        "CpuPreviewReceiptV2-995-manifest",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["outputs", 0, "manifest", "sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewReceiptV2-966-index",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "index"],
            "replacement": 2,
        },
    ),
    (
        "CpuPreviewReceiptV2-966-inputs",
        {
            "root": "preview_second",
            "object_path": [],
            "path": ["passes", 0, "inputs", 0, "side"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-source_parent_id",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["outputs", 0, "source_parent_id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-id",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["source_bindings", 0, "ref", "id"],
            "replacement": "0000000000000000000000000Z",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-sha256",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["source_bindings", 0, "asset", "sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-measurement",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["outputs", 0, "measurement", "side"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-source_sha256",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["outputs", 0, "measurement", "source_sha256"],
            "replacement": "0000000000000000000000000000000000000000000000000000000000000000",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-side",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "outputs", 0, "side"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-982-true_peak_dbtp",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "outputs", 0, "true_peak_dbtp"],
            "replacement": -1.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-982-gain_db",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["passes", 0, "outputs", 0, "gain_db"],
            "replacement": 1.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-987-path",
        {
            "root": "preview_receipt",
            "object_path": [],
            "path": ["outputs", 0, "file", "path"],
            "replacement": "wrong",
        },
    ),
    (
        "CpuPreviewReceiptV2-969-ceiling_dbtp",
        {
            "root": "preview_second",
            "object_path": [],
            "path": ["policy", "ceiling_dbtp"],
            "replacement": 0.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-969-target_lufs",
        {
            "root": "preview_second",
            "object_path": [],
            "path": ["passes", 1, "target_lufs"],
            "replacement": -18.0,
        },
    ),
    (
        "CpuPreviewReceiptV2-969-true_peak_dbtp",
        {
            "root": "preview_second",
            "object_path": [],
            "path": ["passes", 0, "outputs", 0, "true_peak_dbtp"],
            "replacement": -1.5,
        },
    ),
]


@pytest.mark.parametrize(
    "criterion,case",
    COHERENT_INVALID_CONTEXTS,
    ids=[x[0] for x in COHERENT_INVALID_CONTEXTS],
)
def test_coherence_rejects_independent_invalid_binding(criterion, case):
    value = coherent_fixture(case["root"])
    for key in case["object_path"]:
        value = getattr(value, key) if isinstance(key, str) else value[key]
    assert value.coherent() == value
    invalid = copied_field(value, case["path"], case["replacement"])
    with pytest.raises(ValueError):
        invalid.coherent()


CORRELATED_BINDINGS = [
    (
        "receipt_binding_owner_id",
        "package",
        ("receipt", "owner_id"),
        "0000000000000000000000000Z",
    ),
    (
        "receipt_binding_song_id",
        "package",
        ("receipt", "song_id"),
        "0000000000000000000000000Z",
    ),
    (
        "receipt_binding_take_id",
        "package",
        ("receipt", "take_id"),
        "0000000000000000000000000Z",
    ),
    (
        "receipt_binding_reservation_id",
        "package",
        ("receipt", "reservation_id"),
        "0000000000000000000000000Z",
    ),
    ("receipt_binding_output_index", "package", ("receipt", "output_index"), 1),
    (
        "receipt_binding_plan_sha256",
        "package",
        ("receipt", "plan_sha256"),
        "0000000000000000000000000000000000000000000000000000000000000000",
    ),
    (
        "receipt_binding_recipe_sha256",
        "package",
        ("receipt", "recipe_sha256"),
        "0000000000000000000000000000000000000000000000000000000000000000",
    ),
    (
        "receipt_binding_composition_sha256",
        "package",
        ("receipt", "composition_sha256"),
        "0000000000000000000000000000000000000000000000000000000000000000",
    ),
    (
        "receipt_binding_provenance_sha256",
        "package",
        ("receipt", "provenance_sha256"),
        "0000000000000000000000000000000000000000000000000000000000000000",
    ),
] + [
    ("plan_song_context", "edit", None, None),
    ("provenance_execution", "edit", ("provenance", "execution_id"), uid(79)),
    ("provenance_recipe", "edit", ("provenance", "recipe_sha256"), "0" * 64),
    ("provenance_composition", "edit", ("provenance", "composition_sha256"), "0" * 64),
    (
        "provenance_parents",
        "edit",
        ("provenance", "parents", 0, "asset", "sha256"),
        "0" * 64,
    ),
    ("provenance_lyrics", "edit", ("provenance", "lyrics", "commercial_use"), False),
    ("provenance_tools", "edit", ("provenance", "tools", 0, "revision"), "different"),
    ("provenance_rights", "edit", ("provenance", "commercial_use"), False),
    ("package_owner", "package", ("provenance", "owner_id"), uid(79)),
    ("package_song", "package", ("provenance", "song_id"), uid(79)),
    ("package_recipe", "package", ("provenance", "recipe_sha256"), "0" * 64),
    ("package_composition", "package", ("provenance", "composition_sha256"), "0" * 64),
    ("package_job", "package", ("provenance", "job_id"), uid(79)),
    ("package_execution", "package", ("provenance", "execution_id"), uid(79)),
    ("distinct_parent_refs", "preview", None, None),
    ("distinct_parent_assets", "preview", None, None),
    ("distinct_tools", "preview", None, None),
    ("unique_edges", "crossfade", None, None),
    ("output_order", "preview_receipt", None, None),
    ("last_peak_a", "preview_receipt", None, None),
    ("last_peak_b", "preview_receipt", None, None),
    ("manifest_namespace", "preview_receipt", None, None),
]


def correlated_fixture(criterion, root, path, replacement):
    if root == "crossfade":
        value = read_plan(plan_wire("crossfade", verified=True)).value
    else:
        value = coherent_fixture(root)
    if root == "preview":
        value = value.request
    assert value.coherent() == value
    if criterion == "plan_song_context":
        invalid = value.model_copy(update={"song_id": uid(79)})
        invalid = copied_field(
            invalid,
            ("reservation", "stage_path"),
            value.reservation.stage_path.replace(value.song_id, uid(79)),
        )
        return copied_field(
            invalid,
            ("reservation", "final_path"),
            value.reservation.final_path.replace(value.song_id, uid(79)),
        )
    if path is not None and path[0] == "receipt":
        invalid = copied_field(value, path, replacement)
        return copied_field(
            invalid, ("authority", "receipt_sha256"), digest(d.encode(invalid.receipt))
        )
    if path is not None:
        invalid = copied_field(value, path, replacement)
        sha = digest(d.encode(invalid.provenance))
        if root == "edit":
            return invalid.model_copy(update={"provenance_sha256": sha})
        invalid = copied_field(invalid, ("authority", "provenance_sha256"), sha)
        invalid = copied_field(invalid, ("receipt", "provenance_sha256"), sha)
        return copied_field(
            invalid, ("authority", "receipt_sha256"), digest(d.encode(invalid.receipt))
        )
    if criterion == "distinct_parent_refs":
        return copied_field(
            value, ("parents", 1, "ref", "id"), value.parents[0].ref.id
        ).model_copy(
            update={
                "parents": (
                    value.parents[0],
                    copied_field(
                        value.parents[1], ("ref", "id"), value.parents[0].ref.id
                    ).model_copy(
                        update={
                            "asset": value.parents[1].asset.model_copy(
                                update={"subject_id": value.parents[0].ref.id}
                            )
                        }
                    ),
                )
            }
        )
    if criterion == "distinct_parent_assets":
        return copied_field(
            value, ("parents", 1, "asset", "ref", "id"), value.parents[0].asset.ref.id
        )
    if criterion == "distinct_tools":
        return value.model_copy(update={"tools": (*value.tools, value.tools[0])})
    if criterion == "unique_edges":
        return copied_field(
            value,
            ("reservation", "parent_bindings", 1, "edge_ref", "id"),
            value.reservation.parent_bindings[0].edge_ref.id,
        )
    if criterion == "output_order":
        # Reorder the entire pair consistently; only the namespace's a,b ordering is invalid.
        pass_ = value.passes[0].model_copy(
            update={
                "inputs": tuple(reversed(value.passes[0].inputs)),
                "outputs": tuple(reversed(value.passes[0].outputs)),
            }
        )
        return value.model_copy(
            update={
                "outputs": tuple(reversed(value.outputs)),
                "source_bindings": tuple(reversed(value.source_bindings)),
                "passes": (pass_,),
            }
        )
    if criterion.startswith("last_peak_"):
        index = 0 if criterion.endswith("a") else 1
        invalid = copied_field(
            value, ("passes", 0, "outputs", index, "true_peak_dbtp"), 0.0
        )
        return copied_field(
            invalid, ("outputs", index, "measurement", "true_peak_dbtp"), 0.0
        )
    if criterion == "manifest_namespace":
        invalid = copied_field(
            value, ("outputs", 0, "manifest", "path"), "data/tmp/wrong/manifest.json"
        )
        return copied_field(
            invalid, ("outputs", 1, "manifest", "path"), "data/tmp/wrong/manifest.json"
        )
    raise AssertionError(criterion)


@pytest.mark.parametrize(
    "criterion,root,path,replacement",
    CORRELATED_BINDINGS,
    ids=[x[0] for x in CORRELATED_BINDINGS],
)
def test_coherence_rejects_consistently_resigned_invalid_context(
    criterion, root, path, replacement
):
    invalid = correlated_fixture(criterion, root, path, replacement)
    with pytest.raises(ValueError):
        invalid.coherent()


@pytest.mark.parametrize(
    "value", [{"wrong": 1}, "wrong", [0] * 257], ids=["object", "string", "excess"]
)
def test_cpu_array_guard_rejects_nonarray_and_excess_entries(value):
    assert d.array([1, 2]) == (1, 2)
    with pytest.raises(d.CpuContractError):
        d.array(value)


@pytest.mark.parametrize(
    "field,value", [("kind", "wrong"), ("version", True), ("version", 3)]
)
def test_cpu_decoder_discriminator_is_exact(field, value):
    wire = {"kind": "cpu_edit_plan", "version": 2}
    wire[field] = value
    raw = encoded(wire)
    with pytest.raises(d.CpuContractError, match="CPU_CONTRACT_UNSUPPORTED"):
        d.decode_cpu(raw, digest(raw), "cpu_edit_plan")


@pytest.mark.parametrize("cls", [d.CpuEditOutcomeV2, d.CpuPreviewOutcomeV2])
@pytest.mark.parametrize(
    "damage", ["receipt", "ready_code", "failed_code", "cancelled_code"]
)
def test_cpu_outcome_status_binds_receipt_and_failure_code(cls, damage):
    extra = {"take_id": uid(8)} if cls is d.CpuEditOutcomeV2 else {}
    kind = "cpu_edit_outcome" if extra else "cpu_preview_outcome"
    value = cls.model_validate(
        dict(
            kind=kind,
            version=2,
            status="ready",
            receipt_sha256="a" * 64,
            code=None,
            **extra,
        )
    )
    if damage == "receipt":
        invalid = value.model_copy(update={"receipt_sha256": None})
    elif damage == "ready_code":
        invalid = value.model_copy(update={"code": "CANCELLED"})
    else:
        invalid = value.model_copy(
            update={"status": "failed" if damage == "failed_code" else "cancelled"}
        )
    with pytest.raises(d.CpuContractError):
        invalid.coherent()


def test_cpu_plan_rejects_valid_inference_recipe_and_matching_composition():
    from test_creative_composition import engine_facts

    original = read_plan(plan_wire(verified=True)).value
    recipe, parents = captured("variation_request")
    request = r.capture_request(recipe)
    composition = build(recipe, parents, engine=engine_facts(recipe))
    provenance = original.provenance.model_copy(
        update={
            "recipe_sha256": recipe.sha256,
            "composition_sha256": composition.sha256,
            "parents": recipe.value.parents,
            "lyrics": recipe.value.lyrics,
            "tools": recipe.value.executor.tools,
            "commercial_use": recipe.value.commercial_use,
        }
    )
    bindings = tuple(
        binding.model_copy(
            update={
                "parent_ref": parent.ref,
                "asset_ref": parent.asset.ref,
                "manifest_ref": parent.asset.manifest_ref,
                "role": parent.role,
                "master_sha256": parent.asset.sha256,
                "manifest_sha256": parent.asset.manifest_sha256,
                "resolved_map": edge,
            }
        )
        for binding, parent, edge in zip(
            original.reservation.parent_bindings,
            recipe.value.parents,
            composition.value.edges,
            strict=True,
        )
    )
    invalid = original.model_copy(
        update={
            "request": request.value,
            "request_sha256": request.sha256,
            "composition": composition.value,
            "composition_sha256": composition.sha256,
            "provenance": provenance,
            "provenance_sha256": digest(d.encode(provenance)),
            "reservation": original.reservation.model_copy(
                update={"root_id": recipe.value.root_id, "parent_bindings": bindings}
            ),
        }
    )
    # Both inputs remain valid in their own inherited APIs; only CPU admission is invalid.
    assert (
        r.read_request(request.payload, expected_sha256=request.sha256).value
        == request.value
    )
    assert (
        d.c.read_composition_plan(
            composition.payload, expected_sha256=composition.sha256, recipe=recipe
        ).value
        == composition.value
    )
    with pytest.raises(d.CpuContractError):
        invalid.coherent()


def test_reservation_cardinality_reports_cpu_contract_error_before_zip():
    value = read_plan(plan_wire(verified=True)).value
    binding = value.reservation.parent_bindings[0]
    duplicate_parent = binding.model_copy(
        update={"edge_ref": binding.edge_ref.model_copy(update={"id": uid(81)})}
    )
    invalid = value.model_copy(
        update={
            "reservation": value.reservation.model_copy(
                update={"parent_bindings": (binding, duplicate_parent)}
            )
        }
    )
    with pytest.raises(d.CpuContractError, match="CPU_PACKAGE_INVALID"):
        invalid.coherent()


@pytest.mark.parametrize(
    "field,replacement",
    [("engine", {}), ("output_shape", "full"), ("descriptor_sha256", "0" * 64)],
)
def test_inherited_composition_reader_rejects_inference_claims_for_cpu_recipe(
    field, replacement
):
    recipe, _ = captured()
    wire = plan_wire()
    wire["composition"][field] = replacement
    raw = encoded(wire["composition"])
    with pytest.raises(ValueError):
        d.c.read_composition_plan(raw, expected_sha256=digest(raw), recipe=recipe)


def test_decoder_bytes_type_has_private_cpu_error_taxonomy():
    raw = bytearray(encoded({"ok": True}))
    with pytest.raises(d.CpuContractError):
        d.decode(raw, digest(raw))


@pytest.mark.parametrize("kind", [[], {}], ids=["list", "dict"])
def test_public_cpu_reader_rejects_nonhashable_kind_with_contract_error(kind):
    raw = encoded({"kind": kind, "version": 2})
    with pytest.raises(d.CpuContractError, match="CPU_CONTRACT_UNSUPPORTED") as error:
        d.read_cpu_edit_plan(raw, expected_sha256=digest(raw))
    assert error.value.code == "CPU_CONTRACT_UNSUPPORTED"


@pytest.mark.parametrize(
    "kind",
    [None, False, 1, 1.0, [], {}, "unknown"],
    ids=["null", "bool", "int", "float", "list", "dict", "unknown-string"],
)
def test_malformed_discriminator_retains_json_roundtrip_and_typed_dispatch(kind):
    wire = {"kind": kind, "version": 2}
    raw = encoded(wire)
    assert d.encode(wire) == raw
    assert d.decode(raw, digest(raw)) == wire
    with pytest.raises(d.CpuContractError, match="CPU_CONTRACT_UNSUPPORTED") as error:
        d.read_execution_plan(
            raw,
            handler="audio.edit",
            handler_version=1,
            contract_version=2,
            expected_sha256=digest(raw),
        )
    assert error.value.code == "CPU_CONTRACT_UNSUPPORTED"
