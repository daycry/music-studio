"""Contratos privados: payloads sintÃ©ticos, sin GPU, BD ni archivos musicales."""

import copy
import hashlib
import json

import pytest
from app.worker.contracts import (
    CapturedProvenance,
    PerTakeResult,
    PostPlan,
    PreparedPackage,
    PublicationAuthority,
    canonical_sha256,
)
from pydantic import TypeAdapter, ValidationError

ID = "01M49HZQ7K5WFE9PA1N3WDN92K"
ID2 = "01M49HZQ7K5WFE9PA1N3WDN92M"
SHA = "a" * 64


def provenance():
    return {
        "engine_id": "acestep",
        "engine_version": "1.5",
        "contract_version": "1",
        "expected_image_digest": None,
        "reported_image_digest": None,
        "task": "music.song",
        "load": {"model_id": "model", "mode": "bf16"},
        "observed_model": {"model_id": "model", "mode": "bf16"},
        "descriptor": {
            "id": "model",
            "family": "ace",
            "version": "1.5",
            "revision": "pinned",
            "license": "MIT",
            "commercial_use": True,
            "training_data": "reported",
            "provider": {"type": "local"},
            "weights": [
                {
                    "path": "models/model.safetensors",
                    "sha256": SHA,
                    "bytes": 1,
                    "format": "safetensors",
                }
            ],
            "modes": [{"id": "bf16", "notes": "default"}],
            "tasks": {
                "music.song": {"verified": True, "device": "gpu", "params_schema": {}}
            },
        },
    }


def authority(index=0, take=ID):
    return {
        "owner_id": ID,
        "song_id": ID,
        "post_job_id": ID,
        "generation_job_id": ID,
        "winning_attempt_id": ID,
        "winning_ordinal": 1,
        "terminal_seq": 1,
        "terminal_sha256": SHA,
        "take_id": take,
        "output_index": index,
        "seed": 2**80,
        "provenance_sha256": canonical_sha256(
            CapturedProvenance.model_validate(provenance())
        ),
    }


def plan():
    a = authority()
    f = {
        "path": f"data/tmp/{ID}/0.wav",
        "sha256": SHA,
        "media_type": "audio/wav",
        "bytes": 1,
        "duration_s": 1.0,
    }
    return {
        "version": 1,
        "handler": "post.audio",
        "handler_version": 1,
        "owner_id": ID,
        "song_id": ID,
        "post_job_id": ID,
        "generation_job_id": ID,
        "request_sha256": SHA,
        "tool_pin_sha256": SHA,
        "provenance": provenance(),
        "takes": [
            {
                "authority": a,
                "source": f,
                "copy": {**f, "path": f"data/tmp/{ID}/copy.wav"},
            }
        ],
    }


def package():
    p = {}
    for role, name, media in [
        ("master", "master.flac", "audio/flac"),
        ("listen", "listen.mp3", "audio/mpeg"),
        ("peaks", "peaks.json", "application/json"),
        ("manifest", "manifest.json", "application/json"),
    ]:
        p[role] = {
            "path": f"data/songs/{ID}/takes/{ID}/{name}",
            "sha256": SHA,
            "bytes": 1,
            "media_type": media,
        }
    return dict(authority=authority(), **p)


def test_rejects_authority_negative_seed():
    with pytest.raises(ValidationError):
        PublicationAuthority.model_validate({**authority(), "seed": -1})


def test_valid_plan_digest_and_immutable():
    p = PostPlan.model_validate(plan())
    assert p.takes[0].authority.seed == 2**80
    assert canonical_sha256(p) == canonical_sha256(json.loads(p.model_dump_json()))
    assert canonical_sha256(p) != canonical_sha256(
        {**json.loads(p.model_dump_json()), "request_sha256": "b" * 64}
    )
    with pytest.raises(ValidationError):
        p.handler_version = 2
    with pytest.raises(ValidationError):
        p.takes[0].authority.seed = 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("output_index", 64),
        ("output_index", -1),
        ("seed", True),
        ("winning_ordinal", 0),
        ("terminal_seq", 0),
        ("take_id", "invalid"),
        ("terminal_sha256", "z" * 64),
        ("lease_token", "secret"),
    ],
)
def test_authority_boundaries(field, value):
    with pytest.raises(ValidationError):
        PublicationAuthority.model_validate({**authority(), field: value})


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(
            expected_image_digest="sha256:" + SHA,
            reported_image_digest="sha256:" + "b" * 64,
        ),
        lambda p: p["load"].update(model_id="other"),
        lambda p: p["load"].update(mode="other"),
        lambda p: p["observed_model"].update(mode="other"),
        lambda p: p["descriptor"]["tasks"]["music.song"].update(verified=False),
        lambda p: p["descriptor"]["tasks"]["music.song"]["params_schema"].update(
            token="secret"
        ),
        lambda p: p["descriptor"]["tasks"]["music.song"]["params_schema"].update(
            x=float("nan")
        ),
        lambda p: p["descriptor"].update(commercial_use="true"),
        lambda p: p["descriptor"].update(extra="ignored"),
        lambda p: p["load"].update(headers={}),
        lambda p: p.update(engine_id="x" * 513),
        lambda p: p.update(contract_version="2"),
    ],
)
def test_provenance_rejections(mutate):
    p = provenance()
    mutate(p)
    with pytest.raises(ValidationError):
        CapturedProvenance.model_validate(p)


def test_provenance_unknown_separate_and_detached_descriptor():
    raw = provenance()
    raw["expected_image_digest"] = "sha256:" + SHA
    p = CapturedProvenance.model_validate(raw)
    assert p.reported_image_digest is None
    before = canonical_sha256(p)
    raw["descriptor"]["revision"] = "changed"
    detached = p.descriptor.value
    detached.revision = "changed"
    assert canonical_sha256(p) == before
    assert p.descriptor.value.license == "MIT"


@pytest.mark.parametrize(
    "path",
    [
        "/a",
        "C:/a",
        "a\\b",
        "a/../b",
        "a/./b",
        "a//b",
        "a/",
        "a\n/b",
        "a\x00/b",
        "a/CON",
        "a/b.",
        "a/b ",
    ],
)
def test_plan_unsafe_paths(path):
    p = plan()
    p["takes"][0]["source"]["path"] = path
    with pytest.raises(ValidationError):
        PostPlan.model_validate(p)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["takes"].append(copy.deepcopy(p["takes"][0])),
        lambda p: p["takes"].append(
            {**copy.deepcopy(p["takes"][0]), "authority": authority(0, ID2)}
        ),
        lambda p: p["takes"][0]["authority"].update(song_id=ID2),
        lambda p: p["takes"][0]["authority"].update(provenance_sha256="b" * 64),
        lambda p: p["takes"][0]["copy"].update(sha256="b" * 64),
        lambda p: p["takes"][0]["source"].update(duration_s=float("inf")),
        lambda p: p["takes"][0]["source"].update(bytes=0),
        lambda p: p.update(takes=[]),
        lambda p: p.update(process_identity={}),
    ],
)
def test_plan_consistency(mutate):
    p = plan()
    mutate(p)
    with pytest.raises(ValidationError):
        PostPlan.model_validate(p)


def test_results_and_package():
    pkg = PreparedPackage.model_validate(package())
    adapter = TypeAdapter(PerTakeResult)
    good = {
        "status": "success",
        "take_id": ID,
        "output_index": 0,
        "package": pkg.model_dump(mode="json"),
        "duration_s": 1.0,
        "integrated_lufs": -14.0,
        "true_peak_dbtp": -1.2,
    }
    assert adapter.validate_python(good).package == pkg
    assert (
        adapter.validate_python(
            {
                "status": "failure",
                "take_id": ID,
                "output_index": 0,
                "code": "AUDIO_TRANSCODE_FAILED",
            }
        ).code
        == "AUDIO_TRANSCODE_FAILED"
    )
    for patch in [
        {"take_id": ID2},
        {"output_index": 1},
        {"duration_s": float("nan")},
        {"lease_token": "secret"},
        {"status": "other"},
    ]:
        with pytest.raises(ValidationError):
            adapter.validate_python({**good, **patch})
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {"status": "failure", "take_id": ID, "output_index": 0, "code": "arbitrary"}
        )
    for role in ["master", "listen", "peaks", "manifest"]:
        bad = package()
        bad[role]["path"] = f"data/songs/{ID}/takes/{ID2}/wrong"
        with pytest.raises(ValidationError):
            PreparedPackage.model_validate(bad)
    bad = package()
    bad["extra"] = {}
    with pytest.raises(ValidationError):
        PreparedPackage.model_validate(bad)


def test_strict_versions_and_boolean_measurements():
    for field in ("version", "handler_version"):
        p = plan()
        p[field] = True
        with pytest.raises(ValidationError):
            PostPlan.model_validate(p)
    adapter = TypeAdapter(PerTakeResult)
    for field in ("duration_s", "integrated_lufs", "true_peak_dbtp"):
        p = {
            "status": "success",
            "take_id": ID,
            "output_index": 0,
            "package": package(),
            "duration_s": 1.0,
            "integrated_lufs": -14.0,
            "true_peak_dbtp": -1.0,
        }
        p[field] = True
        with pytest.raises(ValidationError):
            adapter.validate_python(p)


def test_sparse_original_indices_and_boundary_count():
    p = plan()
    p["takes"][0]["authority"]["output_index"] = 63
    assert PostPlan.model_validate(p).takes[0].authority.output_index == 63
    p = plan()
    template = p["takes"][0]
    p["takes"] = []
    for i in range(64):
        entry = copy.deepcopy(template)
        entry["authority"] = authority(i, f"{ID[:23]}{i:03d}")
        # ULID suffix decimal conserva 26 caracteres y el Ã­ndice original.
        p["takes"].append(entry)
    assert len(PostPlan.model_validate(p).takes) == 64
    p["takes"].append(copy.deepcopy(p["takes"][0]))
    with pytest.raises(ValidationError):
        PostPlan.model_validate(p)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["descriptor"].update(weights=[]),
        lambda p: p["descriptor"].update(modes=[]),
        lambda p: p["descriptor"]["provider"].update(type="external"),
        lambda p: p["descriptor"]["weights"][0].update(path="a/../weight"),
        lambda p: p["descriptor"].update(remote_code=[{"path": "/bad", "sha256": SHA}]),
        lambda p: p["descriptor"].update(license=""),
        lambda p: p["descriptor"]["tasks"]["music.song"].update(
            features={"x": {"verified": True, "secret": "hidden"}}
        ),
        lambda p: p["descriptor"]["tasks"]["music.song"]["params_schema"].update(
            x=[0] * 257
        ),
        lambda p: p["descriptor"]["tasks"]["music.song"]["params_schema"].update(
            x="x" * 8193
        ),
        lambda p: p["descriptor"]["tasks"]["music.song"]["params_schema"].update(
            x=object()
        ),
    ],
)
def test_descriptor_evidence_boundaries(mutate):
    p = provenance()
    mutate(p)
    with pytest.raises(ValidationError):
        CapturedProvenance.model_validate(p)


def test_canonical_order_and_deep_json_bound():
    assert (
        canonical_sha256({"b": 2, "a": "Ã±"})
        == hashlib.sha256('{"a":"Ã±","b":2}'.encode()).hexdigest()
    )
    value = {}
    for _ in range(22):
        value = {"x": value}
    with pytest.raises(ValueError):
        canonical_sha256(value)
    with pytest.raises(ValueError):
        canonical_sha256({"x": float("inf")})
    with pytest.raises(ValueError):
        canonical_sha256({1: "bad"})
    with pytest.raises(ValueError):
        canonical_sha256({"x": "control\x01"})


def test_captured_public_types_and_null_load_mode():
    from engine_contract import ModelDescriptor

    raw = provenance()
    raw["descriptor"] = ModelDescriptor.model_validate(raw["descriptor"])
    raw["load"]["mode"] = None
    raw["observed_model"] = None
    p = CapturedProvenance.model_validate(raw)
    assert p.observed_model is None
    assert CapturedProvenance.model_validate_json(p.model_dump_json()) == p
    equal = provenance()
    equal.update(
        expected_image_digest="sha256:" + SHA, reported_image_digest="sha256:" + SHA
    )
    assert (
        CapturedProvenance.model_validate(equal).reported_image_digest
        == equal["reported_image_digest"]
    )


def test_terminal_and_copy_authority_rejections():
    p = plan()
    entry = copy.deepcopy(p["takes"][0])
    entry["authority"] = authority(1, ID2)
    p["takes"].append(entry)
    p["takes"][1]["authority"]["terminal_seq"] = 2
    with pytest.raises(ValidationError):
        PostPlan.model_validate(p)
    p = plan()
    p["takes"][0]["copy"]["path"] = p["takes"][0]["source"]["path"]
    with pytest.raises(ValidationError):
        PostPlan.model_validate(p)
    p = package()
    p["master"]["media_type"] = "audio/mpeg"
    with pytest.raises(ValidationError):
        PreparedPackage.model_validate(p)


@pytest.mark.parametrize("path", ["data/a\u0085b", "data/a\u202eb", "data/a\u200bb"])
def test_unicode_path_controls(path):
    raw = plan()
    raw["takes"][0]["source"]["path"] = path
    with pytest.raises(ValidationError):
        PostPlan.model_validate(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner_id", ID2),
        ("song_id", ID2),
        ("post_job_id", ID2),
        ("generation_job_id", ID2),
        ("winning_attempt_id", ID2),
        ("winning_ordinal", 2),
        ("terminal_seq", 2),
        ("terminal_sha256", "b" * 64),
        ("seed", 9),
        ("provenance_sha256", "b" * 64),
    ],
)
def test_result_requires_full_plan_authority(field, value):
    raw = package()
    raw["authority"][field] = value
    if field == "song_id":
        for role in ("master", "listen", "peaks", "manifest"):
            raw[role]["path"] = raw[role]["path"].replace(
                f"songs/{ID}/", f"songs/{ID2}/"
            )
    result = TypeAdapter(PerTakeResult).validate_python(
        {
            "status": "success",
            "take_id": ID,
            "output_index": 0,
            "package": raw,
            "duration_s": 1.0,
            "integrated_lufs": -14.0,
            "true_peak_dbtp": -1.0,
        }
    )
    with pytest.raises(ValueError):
        PostPlan.model_validate(plan()).validate_result(result)


def test_result_plan_membership_and_valid_outcomes():
    p = PostPlan.model_validate(plan())
    adapter = TypeAdapter(PerTakeResult)
    success = adapter.validate_python(
        {
            "status": "success",
            "take_id": ID,
            "output_index": 0,
            "package": package(),
            "duration_s": 1.0,
            "integrated_lufs": -14.0,
            "true_peak_dbtp": -1.0,
        }
    )
    failure = adapter.validate_python(
        {
            "status": "failure",
            "take_id": ID,
            "output_index": 0,
            "code": "TAKE_POST_FAILED",
        }
    )
    assert p.validate_result(success) == success
    assert p.validate_result(failure) == failure
    wrong = adapter.validate_python(
        {
            "status": "failure",
            "take_id": ID2,
            "output_index": 0,
            "code": "TAKE_POST_FAILED",
        }
    )
    with pytest.raises(ValueError):
        p.validate_result(wrong)
