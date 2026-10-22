"""El snapshot portable conserva evidencia sintética real y aprendida histórica."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app import models, snapshots
from app.db import create_db_engine, migrate
from app.queue.synthetic_registry import packaged_mock_registry
from app.worker.contracts import CapturedProvenance, PostPlan, canonical_sha256
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema import ValidationError as SchemaValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from test_job_attempt_schema import ATTEMPT, JOB, OWNER, SONG, UTC, row
from test_worker_publication_invariants import plan as learned_plan
from test_worker_publication_invariants import provenance as learned

OUTPUT = Path.cwd() / ".cache/dev-cycle/m1/t05-snapshot-synthetic-schema-fix1"
SCHEMAS = (
    Path("apps/server/app/models/song-v1.schema.json"),
    Path("packages/contracts/song-v1.schema.json"),
)


def provenance_schemas():
    schema = json.loads(SCHEMAS[0].read_bytes())
    attempt = schema["properties"]["rows"]["properties"]["job_attempt"]["items"]
    execution = schema["properties"]["rows"]["properties"]["cpu_execution"]["items"]
    return (
        attempt["properties"]["provenance"]["anyOf"][0],
        execution["properties"]["plan"]["properties"]["provenance"],
    )


def expand(value, definitions):
    if isinstance(value, list):
        return [expand(item, definitions) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        result = expand(definitions[value["$ref"].split("/")[-1]], definitions)
        result.update(
            {
                key: expand(item, definitions)
                for key, item in value.items()
                if key != "$ref"
            }
        )
        return result
    return {key: expand(item, definitions) for key, item in value.items()}


def synthetic():
    backend = SimpleNamespace(origin="http://engine-mock:8199")
    entry = packaged_mock_registry({"mock": backend}, {"mock": backend.origin}).entries[
        0
    ]
    return CapturedProvenance(
        descriptor=entry.descriptor,
        engine_id=entry.binding.engine_id,
        engine_version=entry.binding.engine_version,
        contract_version="1",
        task="music.instrumental",
        load={"model_id": "mock", "mode": "cpu"},
        observed_model={"model_id": "mock", "mode": "cpu"},
        expected_image_digest=None,
        reported_image_digest=None,
        evidence_kind="synthetic",
        synthetic_binding=entry.binding,
    )


@pytest.fixture
def engine():
    directory = OUTPUT / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    database = directory / "studio.sqlite"
    migrate(database)
    result = create_db_engine(database)
    with Session(result) as session:
        session.add(
            models.Song(
                id=SONG, owner_id=OWNER, title="Fixture", created_at=UTC, updated_at=UTC
            )
        )
        session.flush()
        session.add(
            models.Job(
                id=JOB,
                owner_id=OWNER,
                song_id=SONG,
                task="music.instrumental",
                lane="gpu",
                request={"seed": 17},
                status="running",
                created_at=UTC,
                updated_at=UTC,
            )
        )
        session.commit()
    try:
        yield result
    finally:
        result.dispose()


def test_packaged_synthetic_snapshot_publish_and_roundtrip(engine):
    evidence = synthetic()
    value = row()
    value["mode"] = "cpu"
    value["engine_request"]["mode"] = "cpu"
    value["load_options"]["mode"] = "cpu"
    value.update(provenance=evidence, provenance_sha256=canonical_sha256(evidence))
    with Session(engine) as session:
        session.add(models.JobAttempt(**value))
        session.commit()
    directory = Path(engine.url.database).parent
    document = snapshots.project(engine, SONG)
    actual = document["rows"]["job_attempt"][0]["provenance"]
    assert actual == evidence.model_dump(mode="json")
    assert actual["descriptor"]["weights"] == []
    assert actual["synthetic_binding"]["recipe_id"] == "packaged-engine-mock-cpu-v1"
    snapshots.publish(engine, SONG, directory)
    published = json.loads((directory / "songs" / SONG / "song.json").read_bytes())
    assert published == document
    destination = directory / "restored.sqlite"
    snapshots.restore_new(destination, published, directory)
    restored = create_db_engine(destination)
    try:
        assert snapshots.project(restored, SONG) == document
        with Session(restored) as session:
            attempt = session.get(models.JobAttempt, ATTEMPT)
            assert attempt.provenance == evidence
            assert attempt.provenance_sha256 == canonical_sha256(evidence)
    finally:
        restored.dispose()


def test_schema_mirrors_and_nested_binding_follow_authoritative_dto():
    assert SCHEMAS[0].read_bytes() == SCHEMAS[1].read_bytes()
    schema = json.loads(SCHEMAS[0].read_bytes())
    Draft202012Validator.check_schema(schema)
    dto = CapturedProvenance.model_json_schema()
    binding = expand(dto["$defs"]["SyntheticBinding"], dto["$defs"])
    for provenance in provenance_schemas():
        legacy, synthetic_schema = provenance["anyOf"]
        assert legacy["additionalProperties"] is False
        assert synthetic_schema["additionalProperties"] is False
        assert synthetic_schema["properties"]["synthetic_binding"] == binding
        assert set(synthetic_schema["required"]) == set(dto["required"]) | {
            "evidence_kind",
            "synthetic_binding",
        }
        assert set(synthetic_schema["properties"]) == set(dto["properties"])
        for name in set(dto["properties"]) - {
            "descriptor",
            "evidence_kind",
            "synthetic_binding",
        }:
            expected = expand(dto["properties"][name], dto["$defs"])
            actual = synthetic_schema["properties"][name]
            assert actual == expected


@pytest.mark.parametrize("kind", ["synthetic", "learned"])
def test_structural_provenance_accepts_typed_serialization(kind):
    payload = synthetic().model_dump(mode="json") if kind == "synthetic" else learned()
    typed = CapturedProvenance.model_validate(payload)
    assert typed.model_dump(mode="json") == payload
    if kind == "learned":
        assert "evidence_kind" not in payload and "synthetic_binding" not in payload
        assert payload["descriptor"]["weights"]
    for schema in provenance_schemas():
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def test_synthetic_post_plan_serialization_matches_snapshot_schema():
    value = learned_plan()
    evidence = synthetic()
    value["provenance"] = evidence.model_dump(mode="json")
    for take in value["takes"]:
        take["authority"]["provenance_sha256"] = canonical_sha256(evidence)
    serialized = PostPlan.model_validate(value).model_dump(mode="json")
    schema = json.loads(SCHEMAS[0].read_bytes())
    plan_schema = schema["properties"]["rows"]["properties"]["cpu_execution"]["items"][
        "properties"
    ]["plan"]
    Draft202012Validator(plan_schema, format_checker=FormatChecker()).validate(
        serialized
    )
    assert serialized["provenance"] == evidence.model_dump(mode="json")
    assert serialized["takes"][0]["authority"]["provenance_sha256"] == canonical_sha256(
        evidence
    )


@pytest.mark.parametrize("scope", ["product", "test"])
@pytest.mark.parametrize("digest", [None, "sha256:" + "a" * 64])
def test_binding_scope_and_nullable_image_are_typed_and_portable(scope, digest):
    value = synthetic().model_dump(mode="json")
    value["expected_image_digest"] = value["reported_image_digest"] = digest
    value["synthetic_binding"]["scope"] = scope
    value["synthetic_binding"]["expected_image_digest"] = digest
    serialized = CapturedProvenance.model_validate(value).model_dump(mode="json")
    for schema in provenance_schemas():
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(
            serialized
        )


@pytest.mark.parametrize(
    "fraud",
    [
        "missing_kind",
        "invalid_kind",
        "missing_binding",
        "null_binding",
        "empty_binding",
        "binding_extra",
        "implementation_extra",
        "missing_implementation_hash",
        "invalid_hash",
        "invalid_binding_version",
        "invalid_scope",
        "invalid_contract",
        "invalid_digest",
        "invalid_origin_shape",
        "invalid_recipe_shape",
        "invalid_descriptor_shape",
        "descriptor_extra",
        "provider_extra",
        "mode_extra",
        "task_extra",
        "weights",
        "remote_code",
        "top_extra",
        "learned_with_binding",
    ],
)
def test_structural_synthetic_rejects_malformed_evidence(fraud):
    value = synthetic().model_dump(mode="json")
    binding = value["synthetic_binding"]
    if fraud == "missing_kind":
        value.pop("evidence_kind")
    elif fraud == "invalid_kind":
        value["evidence_kind"] = "unknown"
    elif fraud == "missing_binding":
        value.pop("synthetic_binding")
    elif fraud == "null_binding":
        value["synthetic_binding"] = None
    elif fraud == "empty_binding":
        value["synthetic_binding"] = {}
    elif fraud == "binding_extra":
        binding["extra"] = "untrusted"
    elif fraud == "implementation_extra":
        binding["implementation"]["extra"] = "untrusted"
    elif fraud == "missing_implementation_hash":
        binding["implementation"].pop("source_sha256")
    elif fraud == "invalid_hash":
        binding["descriptor_sha256"] = "not-a-hash"
    elif fraud == "invalid_binding_version":
        binding["version"] = True
    elif fraud == "invalid_scope":
        binding["scope"] = "external"
    elif fraud == "invalid_contract":
        binding["contract_version"] = "2"
    elif fraud == "invalid_digest":
        binding["expected_image_digest"] = "sha256:bad"
    elif fraud == "invalid_origin_shape":
        binding["origin"] = []
    elif fraud == "invalid_recipe_shape":
        binding["recipe_id"] = ""
    elif fraud == "invalid_descriptor_shape":
        value["descriptor"] = "{}"
    elif fraud == "descriptor_extra":
        value["descriptor"]["extra"] = "untrusted"
    elif fraud == "provider_extra":
        value["descriptor"]["provider"]["extra"] = "untrusted"
    elif fraud == "mode_extra":
        value["descriptor"]["modes"][0]["extra"] = "untrusted"
    elif fraud == "task_extra":
        value["descriptor"]["tasks"]["music.instrumental"]["extra"] = "untrusted"
    elif fraud == "weights":
        value["descriptor"]["weights"] = copy.deepcopy(
            learned()["descriptor"]["weights"]
        )
    elif fraud == "remote_code":
        value["descriptor"]["remote_code"] = [
            {"path": "models/code.py", "sha256": "a" * 64}
        ]
    elif fraud == "top_extra":
        value["extra"] = "untrusted"
    elif fraud == "learned_with_binding":
        value["evidence_kind"] = "learned"
    with pytest.raises(ValidationError):
        CapturedProvenance.model_validate(value)
    for schema in provenance_schemas():
        with pytest.raises(SchemaValidationError):
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


@pytest.mark.parametrize("shape", ["legacy_missing", "nullable"])
def test_nullable_and_legacy_attempt_snapshots_remain_portable(engine, shape):
    value = row()
    if shape == "nullable":
        value.update(provenance=None, provenance_sha256=None)
    with Session(engine) as session:
        session.add(models.JobAttempt(**value))
        session.commit()
    document = snapshots.project(engine, SONG)
    projected = document["rows"]["job_attempt"][0]
    if shape == "legacy_missing":
        assert "provenance" not in projected and "provenance_sha256" not in projected
    else:
        # Project preserves the historical omission of paired NULL evidence.
        projected.update(provenance=None, provenance_sha256=None)
    snapshots.validate(document, Path(engine.url.database).parent)
