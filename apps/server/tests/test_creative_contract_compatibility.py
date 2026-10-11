"""Regresión contractual con JSON sintético, sin BD, audio ni custodia."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from app import snapshots
from app.creative import recipes as r
from app.worker.contracts import PostPlan, canonical_sha256
from audio_post.manifest import _validate as validate_manifest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaError
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures/creative"
KINDS = (
    "variation_request",
    "variation_audio",
    "extend",
    "repaint",
    "cover",
    "trim",
    "fade",
    "crossfade",
)
INDEX = json.loads((FIXTURES / "fixture-index.json").read_bytes())
SCHEMA = json.loads(
    (ROOT / "packages/contracts/creative-recipe-v1.schema.json").read_bytes()
)


@pytest.mark.parametrize(
    "damage",
    (
        "tools_empty",
        "parents_empty",
        "parents_three",
        "ops_empty",
        "ops_four",
        "crossfade_zero",
        "crossfade_negative",
        "extend_negative",
        "fade_negative",
        "asset_zero",
    ),
)
def test_schema_rejects_local_constraint_recipe_mutants(damage):
    kind = (
        "crossfade"
        if damage.startswith("crossfade")
        else "extend"
        if damage == "extend_negative"
        else "fade"
        if damage == "fade_negative"
        else "trim"
    )
    value = json.loads((FIXTURES / f"recipe-{kind}.json").read_bytes())
    if damage == "tools_empty":
        value["executor"]["tools"] = []
    elif damage == "parents_empty":
        value["parents"] = []
    elif damage == "parents_three":
        value["parents"] *= 3
    elif damage.startswith("ops_"):
        value["parents"][0]["section_map"]["ops"] *= 0 if damage == "ops_empty" else 4
    elif damage.startswith("crossfade"):
        value["operation"]["duration_s"] = 0 if damage == "crossfade_zero" else -1
    elif damage == "extend_negative":
        value["operation"]["at_s"] = -1
    elif damage == "fade_negative":
        value["operation"]["fade_in_s"] = -1
    else:
        value["parents"][0]["asset"]["duration_s"] = 0
    raw = r.encode(value)
    with pytest.raises(r.RecipeError, match="RECIPE_INVALID"):
        r.read_recipe(
            raw, schema_version=1, expected_sha256=hashlib.sha256(raw).hexdigest()
        )
    with pytest.raises(SchemaError):
        Draft202012Validator(SCHEMA).validate(value)


@pytest.mark.parametrize(
    "dto,field,bad,good",
    (
        ("CpuSelection", "tools", [], 1),
        ("SectionMapIntent", "ops", [], 1),
        ("SectionMapIntent", "ops", 4, 3),
        ("Crossfade", "duration_s", 0, 0.01),
        ("Crossfade", "duration_s", -1, 1),
        ("Extend", "at_s", -1, 0),
        ("MasterAssetSnapshot", "duration_s", 0, 0.01),
        ("MasterAssetSnapshot", "bytes", 0, 1),
        ("MasterAssetSnapshot", "sample_rate", 0, 1),
        ("Fade", "fade_in_s", 0, 0.01),
    ),
)
def test_isolated_dto_local_constraints_with_paired_boundaries(dto, field, bad, good):
    trim = json.loads((FIXTURES / "recipe-trim.json").read_bytes())
    values = {
        "CpuSelection": trim["executor"],
        "SectionMapIntent": trim["parents"][0]["section_map"],
        "MasterAssetSnapshot": trim["parents"][0]["asset"],
        "Crossfade": {"kind": "crossfade", "duration_s": 1.0},
        "Extend": {"kind": "extend", "at_s": 0.0},
        "Fade": {"kind": "fade", "fade_in_s": 1.0, "fade_out_s": None},
    }
    valid, invalid = copy.deepcopy(values[dto]), copy.deepcopy(values[dto])
    if isinstance(valid[field], list):
        valid[field] = valid[field] * good
        invalid[field] = invalid[field] * bad if isinstance(bad, int) else bad
    else:
        valid[field], invalid[field] = good, bad
    model = getattr(r, dto)
    model.model_validate(valid)
    with pytest.raises((ValidationError, r.RecipeError)):
        model.model_validate(invalid)
    local_schema = {"$ref": f"#/$defs/{dto}", "$defs": SCHEMA["$defs"]}
    validator = Draft202012Validator(local_schema)
    validator.validate(valid)
    with pytest.raises(SchemaError):
        validator.validate(invalid)


def test_fixture_integrity_inventory_and_synthetic_declaration():
    assert INDEX["synthetic"] is True and INDEX["fixture_set_version"] == 1
    assert set(INDEX["files"]) == {p.name for p in FIXTURES.glob("*.json")} - {
        "fixture-index.json"
    }
    for name, receipt in INDEX["files"].items():
        payload = (FIXTURES / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == receipt["sha256"]
        assert len(payload) == receipt["bytes"]
    assert (
        hashlib.sha256(
            (ROOT / "packages/contracts/creative-recipe-v1.schema.json").read_bytes()
        ).hexdigest()
        == INDEX["recipe_schema_sha256"]
    )


def test_recipe_schema_is_valid_draft_and_describes_serialized_objects():
    Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert (
        SCHEMA["$defs"]["InferenceSelection"]["properties"]["params"]["type"]
        == "object"
    )
    assert (
        SCHEMA["$defs"]["EffectiveRequestBasis"]["properties"]["request"]["type"]
        == "object"
    )
    assert (
        SCHEMA["$defs"]["InferenceSelection"]["properties"]["descriptor"]["$ref"]
        == "#/$defs/ModelDescriptor"
    )


def test_all_schema_nodes_have_effective_local_constraint_keywords():
    def visit(node):
        if isinstance(node, dict):
            if node.get("type") == "array":
                assert not {"minLength", "maxLength"} & node.keys()
            if node.get("type") in {"number", "integer"}:
                assert not {"gt", "ge", "lt", "le"} & node.keys()
            for keyword in (
                "$defs",
                "properties",
                "patternProperties",
                "dependentSchemas",
            ):
                for child in node.get(keyword, {}).values():
                    visit(child)
            for keyword in (
                "items",
                "contains",
                "additionalProperties",
                "not",
                "if",
                "then",
                "else",
                "propertyNames",
            ):
                if keyword in node:
                    visit(node[keyword])
            for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
                for child in node.get(keyword, []):
                    visit(child)

    visit(SCHEMA)
    # String limits remain string limits, rather than blind keyword replacement.
    revision = SCHEMA["$defs"]["ToolSelection"]["properties"]["revision"]
    assert revision["minLength"] == 1 and revision["maxLength"] == 512


@pytest.mark.parametrize("kind", KINDS)
def test_frozen_recipe_wire_schema_codec_hash_and_envelope_agree(kind):
    raw = (FIXTURES / f"recipe-{kind}.json").read_bytes()
    expected = INDEX["files"][f"recipe-{kind}.json"]["sha256"]
    captured = r.read_recipe(raw, schema_version=1, expected_sha256=expected)
    value = json.loads(raw)
    Draft202012Validator(SCHEMA).validate(value)
    assert captured.value.operation.kind == kind
    assert captured.payload == raw and captured.sha256 == expected
    request = (FIXTURES / f"request-{kind}.json").read_bytes()
    envelope = r.read_request(
        request, expected_sha256=INDEX["files"][f"request-{kind}.json"]["sha256"]
    )
    assert envelope.recipe.payload == raw and envelope.recipe.sha256 == expected
    before = captured.payload
    dumped = captured.value.model_dump(mode="json")
    dumped["parents"][0]["asset"]["sha256"] = "0" * 64
    assert captured.payload == before
    assert all(not tool.runtime_verified for tool in captured.value.executor.tools)


@pytest.mark.parametrize("kind", ("trim", "fade", "crossfade"))
def test_cpu_recipes_do_not_manufacture_engine_authority(kind):
    raw = (FIXTURES / f"recipe-{kind}.json").read_bytes()
    captured = r.read_recipe(
        raw, schema_version=1, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    assert captured.value.executor.kind == "cpu_edit"
    assert set(json.loads(raw)["executor"]) == {
        "kind",
        "task",
        "tools",
        "output_format",
    }
    with pytest.raises(r.RecipeError):
        r.project_engine_request(captured, attempt_id="0" * 24 + "16", inputs=())


def test_inference_projection_preserves_selected_request_without_enabling_model():
    raw = (FIXTURES / "recipe-variation_request.json").read_bytes()
    captured = r.read_recipe(
        raw, schema_version=1, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    assert r.project_input_requirements(captured) == ()
    projected = r.project_engine_request(
        captured, attempt_id="0" * 24 + "16", inputs=()
    )
    assert projected.seed == 18 and projected.n_outputs == 1
    assert projected.output_dir == "tmp/" + "0" * 24 + "16"
    assert captured.value.operation.basis.request.wire["seed"] == 16
    assert captured.value.operation.basis.output_index == 1


def test_crossfade_keeps_both_requested_parent_maps_without_measured_claim():
    value = json.loads((FIXTURES / "recipe-crossfade.json").read_bytes())
    assert [p["role"] for p in value["parents"]] == ["crossfade_a", "crossfade_b"]
    assert [p["section_map"]["kind"] for p in value["parents"]] == [
        "requested_seconds"
    ] * 2
    assert value["parents"][1]["section_map"]["ops"][0]["dst"] == [8.0, 10.0]
    assert value["sampling"] == {"index_rule": "round_half_up", "interval": "half_open"}
    assert "execution_id" not in value and "measured_duration_s" not in value


@pytest.mark.parametrize("damage", ("extra", "shape", "identity", "tool_hash", "map"))
def test_incompatible_new_recipe_rejected_even_with_recomputed_outer_hash(damage):
    value = json.loads((FIXTURES / "recipe-trim.json").read_bytes())
    if damage == "extra":
        value["executor"]["winning_attempt_id"] = value["job_id"]
    elif damage == "shape":
        value["operation"]["region"] = [2.0]
    elif damage == "identity":
        value["parents"][0]["song_id"] = "0" * 24 + "99"
    elif damage == "tool_hash":
        value["executor"]["tools"][0]["archive_sha256"] = "invalid"
    else:
        value["parents"][0]["section_map"]["ops"][0]["dst"] = [0.0, 7.0]
    raw = r.encode(value)
    with pytest.raises(r.RecipeError):
        r.read_recipe(
            raw, schema_version=1, expected_sha256=hashlib.sha256(raw).hexdigest()
        )


@pytest.mark.parametrize(
    "damage", ("extra", "shape", "tool_hash", "descriptor_extra", "frozen_string")
)
def test_wire_schema_negative_control_rejects_incompatible_shape(damage):
    kind = (
        "variation_audio" if damage in {"descriptor_extra", "frozen_string"} else "trim"
    )
    value = json.loads((FIXTURES / f"recipe-{kind}.json").read_bytes())
    if damage == "extra":
        value["executor"]["model_id"] = "invented-cpu-model"
    elif damage == "shape":
        value["operation"]["region"] = [2.0]
    elif damage == "tool_hash":
        value["executor"]["tools"][0]["archive_sha256"] = "invalid"
    elif damage == "descriptor_extra":
        value["executor"]["descriptor"]["modes"][0]["secret"] = "synthetic"
    else:
        value["executor"]["params"] = "{}"
    with pytest.raises(SchemaError):
        Draft202012Validator(SCHEMA).validate(value)


@pytest.mark.parametrize("version", (2, True, "1", None))
def test_future_or_invalid_recipe_version_never_falls_back_to_legacy(version):
    value = json.loads((FIXTURES / "request-trim.json").read_bytes())
    value["schema_version"] = version
    with pytest.raises(r.RecipeError, match="RECIPE_VERSION_UNSUPPORTED"):
        r.read_request(r.encode(value))


def test_changed_bytes_or_embedded_hash_cannot_be_normalized_away():
    raw = (FIXTURES / "request-trim.json").read_bytes()
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(raw + b" ", expected_sha256=hashlib.sha256(raw).hexdigest())
    value = json.loads(raw)
    value["recipe"]["executor"]["tools"][0]["revision"] = "changed"
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(r.encode(value))


@pytest.mark.parametrize("name", ("seed-only", "null-large", "post"))
def test_historical_request_bytes_hash_and_absent_fields_survive(name):
    raw = (FIXTURES / f"legacy-request-{name}.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    view = r.read_request(raw, expected_sha256=digest)
    assert view.raw_payload == raw and view.raw_sha256 == digest
    assert view.value == json.loads(raw)
    assert view.present_fields == tuple(sorted(json.loads(raw)))
    assert "kind" not in view.value and "schema_version" not in view.value
    if name == "seed-only":
        assert view.canonical_payload == b'{"seed":17}' and "params" not in view.value
    if name == "null-large":
        assert view.value["mode"] is None and view.value["seed"] == 2**90


def test_historical_engine_postplan_keeps_engine_origin_and_digest():
    raw = (FIXTURES / "engine-postplan-v1.json").read_bytes()
    plan = PostPlan.model_validate_json(raw)
    assert plan.version == 1 and plan.handler == "post.audio"
    assert plan.takes[0].authority.seed == 2**80
    assert canonical_sha256(plan) == INDEX["postplan_canonical_sha256"]
    assert "origin" not in json.loads(raw)


@pytest.mark.parametrize("damage", ("version", "extra", "authority", "shape"))
def test_historical_engine_reader_rejects_incompatible_plan(damage):
    value = json.loads((FIXTURES / "engine-postplan-v1.json").read_bytes())
    if damage == "version":
        value["version"] = 2
    elif damage == "extra":
        value["origin"] = {"kind": "cpu_edit"}
    elif damage == "authority":
        value["takes"][0]["authority"]["winning_attempt_id"] = "invalid"
    else:
        value["takes"] = "not-an-array"
    with pytest.raises(ValidationError):
        PostPlan.model_validate(value)


def test_historical_manifest_reader_and_schema_mirror_remain_compatible():
    value = json.loads((FIXTURES / "manifest-v1.json").read_bytes())
    before = copy.deepcopy(value)
    validate_manifest(value)
    assert value == before and value["manifest_version"] == 1
    assert (ROOT / "packages/contracts/manifest-v1.schema.json").read_bytes() == (
        ROOT / "packages/audio-post/audio_post/manifest-v1.schema.json"
    ).read_bytes()


@pytest.mark.parametrize("damage", ("version", "private", "shape"))
def test_manifest_reader_rejects_incompatible_contract(damage):
    value = json.loads((FIXTURES / "manifest-v1.json").read_bytes())
    if damage == "version":
        value["manifest_version"] = 2
    elif damage == "private":
        value["lyrics"] = "texto privado sintético"
    else:
        value["outputs"] = "not-an-array"
    with pytest.raises(ValueError):
        validate_manifest(value)


def test_song_snapshot_real_reader_keeps_seed_only_historical_shape(tmp_path):
    value = json.loads((FIXTURES / "song-snapshot-v1.json").read_bytes())
    before = copy.deepcopy(value)
    snapshots.validate(value, tmp_path)
    assert value == before and value["rows"]["job"][0]["request"] == {"seed": 17}
    assert (
        ROOT / "packages/contracts/song-v1.schema.json"
    ).read_bytes() == snapshots.SCHEMA.read_bytes()
    assert snapshots.canonical_row(
        {"id": "historical", "provenance": None, "provenance_sha256": None}
    ) == {"id": "historical"}
    row = value["rows"]["job"][0]
    assert snapshots.digest(row, "job") == snapshots.digest(copy.deepcopy(row), "job")
    changed = copy.deepcopy(row)
    changed["request"] = {"seed": 18}
    assert snapshots.digest(row, "job") != snapshots.digest(changed, "job")


@pytest.mark.parametrize(
    "damage", ("version", "identity", "owner", "extra", "request_secret")
)
def test_song_snapshot_reader_rejects_incompatible_or_foreign_closure(tmp_path, damage):
    value = json.loads((FIXTURES / "song-snapshot-v1.json").read_bytes())
    if damage == "version":
        value["version"] = 2
    elif damage == "identity":
        value["song_id"] = "0" * 24 + "99"
    elif damage == "owner":
        value["rows"]["job"][0]["owner_id"] = "0" * 24 + "99"
    elif damage == "extra":
        value["public_recipe"] = {}
    else:
        value["rows"]["job"][0]["request"]["access_token"] = "fixture-secret"
    with pytest.raises((ValueError, SchemaError)):
        snapshots.validate(value, tmp_path)
