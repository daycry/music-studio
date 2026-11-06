"""Contrato CPU puro con contexto sintético; no aceptación del motor."""

import copy
import hashlib
import json
from types import MappingProxyType

import pytest
from app.creative import recipes as r
from pydantic import ValidationError


def uid(n):
    return "0" * 24 + f"{n:02d}"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def wire(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def tool():
    return {
        "tool_id": "ffmpeg",
        "lock_sha256": "a" * 64,
        "revision": "commit",
        "archive_sha256": "b" * 64,
        "recipe_revision": "commit",
        "license": "LGPL",
        "commercial_use": True,
        "runtime_verified": False,
    }


def context(kind="trim"):
    asset = {
        "ref": {"type": "asset", "id": uid(5)},
        "owner_id": uid(1),
        "subject_type": "take",
        "subject_id": uid(4),
        "role": "master",
        "sha256": "a" * 64,
        "bytes": 42,
        "media_type": "audio/flac",
        "duration_s": 10.0,
        "sample_rate": 48000,
        "channels": 2,
        "manifest_ref": {"type": "asset", "id": uid(6)},
        "manifest_sha256": "b" * 64,
        "rights": {
            "kind": "generated_take",
            "manifest_sha256": "b" * 64,
            "commercial_use": True,
            "inputs": [],
        },
    }
    parent = {
        "ref": {"type": "take", "id": uid(4)},
        "owner_id": uid(1),
        "song_id": uid(2),
        "job_id": uid(7),
        "root_id": uid(4),
        "role": "source",
        "status": "ready",
        "asset": asset,
        "origin": {
            "kind": "inference",
            "model_id": "test-model",
            "model_version": "1",
            "seed": 17,
        },
        "lyrics_version_ids": [],
        "section_map": {
            "kind": "requested_seconds",
            "ops": [{"op": "keep", "src": [2.0, 8.0], "dst": [0.0, 6.0]}],
        },
        "commercial_use": True,
    }
    return {
        "owner_id": uid(1),
        "song_id": uid(2),
        "job_id": uid(3),
        "take_id": uid(8),
        "root_id": uid(4),
        "derivation": "edit",
        "operation": {"kind": kind, "region": [2.0, 8.0]},
        "executor": {
            "kind": "cpu_edit",
            "task": "audio.edit",
            "tools": [tool()],
            "output_format": {"sample_rate": 48000, "channels": 2},
        },
        "parents": [parent],
        "lyrics": {
            "mode": "instrumental",
            "versions": [],
            "target_version_id": None,
            "parent_bindings": [{"parent_id": uid(4), "version_ids": []}],
            "commercial_use": True,
        },
        "required_features": [],
        "sampling": {"index_rule": "round_half_up", "interval": "half_open"},
        "commercial_use": True,
    }


def inference(kind="variation_audio"):
    c = context()
    task = {
        "variation_audio": "music.retake",
        "extend": "music.extend",
        "repaint": "music.repaint",
        "cover": "music.cover",
        "variation_request": "music.instrumental",
    }[kind]
    descriptor = {
        "id": "test-model",
        "family": "synthetic",
        "version": "1",
        "revision": "fixed",
        "license": "test",
        "commercial_use": True,
        "training_data": "synthetic",
        "provider": {"type": "local"},
        "weights": [
            {
                "path": "test.safetensors",
                "sha256": "a" * 64,
                "bytes": 10,
                "format": "safetensors",
            }
        ],
        "modes": [{"id": "cpu", "notes": "synthetic"}],
        "tasks": {
            task: {
                "verified": True,
                "device": "cpu",
                "params_schema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                "inputs": []
                if kind == "variation_request"
                else [
                    {"role": "source", "media_types": ["audio/flac"], "required": True}
                ],
                "outputs": [{"media_type": "audio/flac"}],
            }
        },
    }
    frozen = r.FrozenDescriptor.capture(descriptor, evidence_kind="learned")
    c["executor"] = {
        "kind": "inference",
        "task": task,
        "model_id": "test-model",
        "model_version": "1",
        "engine_id": "test",
        "engine_version": "1",
        "contract_version": "1",
        "mode": "cpu",
        "expected_image_digest": None,
        "descriptor": frozen,
        "descriptor_sha256": frozen.sha256,
        "evidence_kind": "learned",
        "synthetic_binding": None,
        "params": {},
        "coordinate_params": {"at_s": None, "t0": None, "t1": None},
        "seed": 18,
        "timeout_s": 60,
        "output_shape": "full",
        "tools": [tool()],
    }
    c["operation"] = {"kind": kind}
    c["derivation"] = "variant" if kind.startswith("variation") else kind
    c["parents"][0]["section_map"]["ops"] = [{"op": "regen", "src": None, "dst": None}]
    return c


def reject(c, code=None):
    with pytest.raises(r.RecipeError) as e:
        r.capture_recipe(c)
    if code:
        assert e.value.code == code
    assert str(e.value) == e.value.code


def test_capture_freezes_nested_context():
    c = context()
    captured = r.capture_recipe(c)
    payload, digest = captured.payload, captured.sha256
    c["parents"][0]["asset"]["rights"]["inputs"].append({"token": "unsafe"})
    c["parents"][0]["section_map"]["ops"][0]["src"][0] = 7
    dumped = captured.value.model_dump(mode="json")
    dumped["executor"]["tools"][0]["runtime_verified"] = True
    assert captured.payload == payload and captured.sha256 == digest == sha(payload)
    assert captured.value.parents[0].asset.rights.inputs == ()
    with pytest.raises(ValidationError):
        captured.value.song_id = uid(9)


def test_legacy_preserves_raw_and_absence():
    raw = b' { "seed" : 17 }\n'
    view = r.read_request(raw, expected_sha256=sha(raw))
    assert view.value == {"seed": 17}
    assert view.raw_payload == raw and view.raw_sha256 == sha(raw)
    assert view.canonical_payload == b'{"seed":17}'
    assert view.present_fields == ("seed",)
    view.value["params"] = {}
    assert view.value == {"seed": 17}


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c.update(extra=1),
        lambda c: c["operation"].update(region=[True, 8]),
        lambda c: c["parents"][0]["asset"].update(duration_s=float("nan")),
        lambda c: c.update(owner_id="bad"),
        lambda c: c["executor"].update(seed=0),
        lambda c: c["parents"][0].update(owner_id=uid(9)),
        lambda c: c["parents"][0].update(ref={"type": "take", "id": uid(8)}),
        lambda c: c["parents"][0]["asset"].update(subject_id=uid(9)),
        lambda c: c["parents"][0]["asset"].update(
            manifest_ref={"type": "asset", "id": uid(5)}
        ),
        lambda c: c["parents"][0]["asset"]["rights"].update(manifest_sha256="c" * 64),
        lambda c: c.update(root_id=uid(9)),
        lambda c: c["parents"][0]["section_map"]["ops"][0].update(dst=[0, 7]),
        lambda c: c["executor"]["tools"].append(tool()),
        lambda c: c["executor"]["tools"][0].update(commercial_use=False),
        lambda c: c["executor"].update(tools=[]),
        lambda c: c["lyrics"].update(declaration="own"),
    ],
)
def test_cpu_rejects_invalid_context(change):
    c = context()
    change(c)
    reject(c)


def test_inference_projection_has_only_effective_engine_fields():
    c = inference()
    captured = r.capture_recipe(c)
    req = r.project_input_requirements(captured)[0]
    assert (
        req.asset_role == "master"
        and req.engine_role == "source"
        and req.asset_id == uid(5)
    )
    resolved = r.ResolvedRecipeInput(
        asset_id=uid(5),
        role="source",
        path="songs/test/master.flac",
        sha256="a" * 64,
        media_type="audio/flac",
    )
    out = r.project_engine_request(captured, attempt_id=uid(9), inputs=(resolved,))
    assert (
        out.job_id == uid(9)
        and out.output_dir == f"tmp/{uid(9)}"
        and out.n_outputs == 1
    )
    assert out.inputs[0].role == "source" and out.seed == 18 and out.params == {}
    assert "owner_id" not in out.model_dump()
    out.params["unsafe"] = 1
    assert captured.value.executor.params.wire == {}


def test_new_request_roundtrip_rejects_tampering():
    cap = r.capture_request(context())
    assert (
        r.read_request(cap.payload, expected_sha256=cap.sha256).payload == cap.payload
    )
    assert (
        r.read_recipe(
            cap.recipe.payload, schema_version=1, expected_sha256=cap.recipe.sha256
        ).payload
        == cap.recipe.payload
    )
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(cap.payload, expected_sha256="0" * 64)
    changed = cap.value.model_dump(mode="json")
    changed["recipe"]["executor"]["tools"][0]["revision"] = "changed"
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(wire(changed))


@pytest.mark.parametrize("value", [True, 1.0, "1", 2, None])
def test_versions_never_fall_back_to_legacy(value):
    with pytest.raises(r.RecipeError, match="RECIPE_VERSION_UNSUPPORTED"):
        r.read_request({"kind": "creative_recipe", "schema_version": value})


@pytest.mark.parametrize(
    "raw",
    [b'{"seed":1,"seed":2}', b'{"seed":NaN}', b"\xef\xbb\xbf{}", b"{}{}", b"\xff"],
)
def test_read_rejects_invalid_json(raw):
    with pytest.raises(r.RecipeError):
        r.read_request(raw)


@pytest.mark.parametrize("key", ["pAsS_word", "ｔｏｋｅｎ", "Authorization", "headers"])
def test_legacy_secret_keys_sanitized(key):
    with pytest.raises(r.RecipeError) as e:
        r.read_request({"params": {key: "do-not-echo"}})
    assert e.value.code == "RECIPE_SECRET_FORBIDDEN"
    assert key not in str(e.value) and "do-not-echo" not in str(e.value)


def test_legacy_artistic_text_and_large_seed_are_not_rewritten():
    c = {
        "params": {
            "lyrics": "mi token\r\n[Verse]" + "ñ" * 33000,
            "tokenizer": "token",
            "max_tokens": 10,
            "token_budget": 5,
        },
        "seed": 2**90,
        "mode": None,
    }
    view = r.read_request(c)
    assert view.value == c and view.raw_payload is None and view.raw_sha256 is None
    assert "inputs" not in view.value


@pytest.mark.parametrize(
    "blob",
    [
        "-----BEGIN PRIVATE KEY-----",
        "Bearer abcdefghijklmnop",
        "https://user:pass@example.invalid/",
    ],
)
def test_legacy_secret_blobs_rejected(blob):
    with pytest.raises(r.RecipeError, match="RECIPE_SECRET_FORBIDDEN"):
        r.read_request({"params": {"lyrics": blob}})


def crossfade():
    c = context()
    c["operation"] = {"kind": "crossfade", "duration_s": 2}
    a = c["parents"][0]
    b = copy.deepcopy(a)
    a["role"] = "crossfade_a"
    b.update(
        ref={"type": "take", "id": uid(9)},
        root_id=uid(9),
        role="crossfade_b",
        job_id=uid(10),
    )
    b["asset"].update(
        ref={"type": "asset", "id": uid(11)},
        subject_id=uid(9),
        manifest_ref={"type": "asset", "id": uid(12)},
    )
    a["section_map"]["ops"] = [
        {"op": "keep", "src": [0, 8], "dst": [0, 8]},
        {"op": "fade", "src": [8, 10], "dst": [8, 10]},
    ]
    b["section_map"]["ops"] = [
        {"op": "fade", "src": [0, 2], "dst": [8, 10]},
        {"op": "keep", "src": [2, 10], "dst": [10, 18]},
    ]
    c["parents"].append(b)
    c["lyrics"]["parent_bindings"].append({"parent_id": uid(9), "version_ids": []})
    return c


def attach_lyrics(c, index, n, text="[Verse]\r\nmi token ñ", declaration="assistant"):
    v = {
        "id": uid(n),
        "owner_id": uid(1),
        "song_id": uid(2),
        "parent_id": None,
        "text": text,
        "sha256": sha(text.encode()),
        "source": "assistant",
        "declaration": declaration,
    }
    c["lyrics"]["versions"].append(v)
    c["parents"][index]["lyrics_version_ids"] = [uid(n)]
    c["lyrics"]["parent_bindings"][index]["version_ids"] = [uid(n)]
    return v


def test_crossfade_keeps_both_parents_and_composite_authorship():
    c = crossfade()
    attach_lyrics(c, 0, 13)
    attach_lyrics(c, 1, 14, declaration="licensed")
    c["lyrics"].update(mode="composite")
    cap = r.capture_recipe(c)
    assert tuple(p.ref.id for p in cap.value.parents) == (uid(4), uid(9))
    assert tuple(v.declaration for v in cap.value.lyrics.versions) == (
        "assistant",
        "licensed",
    )
    assert cap.value.root_id == uid(4) and cap.value.lyrics.target_version_id is None
    c["parents"][1]["section_map"]["ops"][0]["dst"][0] = 0
    assert cap.value.parents[1].section_map.ops[0].dst == (8.0, 10.0)


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["parents"].reverse(),
        lambda c: c["parents"].pop(),
        lambda c: c["parents"][1].update(ref=c["parents"][0]["ref"]),
        lambda c: c["operation"].update(duration_s=11),
        lambda c: c["lyrics"].update(mode="single", target_version_id=uid(13)),
    ],
)
def test_crossfade_rejects_lost_or_inverted_history(change):
    c = crossfade()
    change(c)
    reject(c)


def test_lyrics_text_crlf_exact_and_large_new_text():
    c = context()
    text = "[Verse]\r\n" + "ñ" * 9000
    attach_lyrics(c, 0, 13, text)
    c["lyrics"].update(mode="single", target_version_id=uid(13))
    cap = r.capture_recipe(c)
    assert cap.value.lyrics.versions[0].text == text
    assert cap.value.lyrics.versions[0].sha256 == sha(text.encode())


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["lyrics"]["versions"][0].update(sha256="0" * 64),
        lambda c: c["lyrics"]["versions"][0].update(song_id=uid(9)),
        lambda c: c["lyrics"]["versions"][0].pop("declaration"),
        lambda c: c["lyrics"]["versions"][0].update(parent_id=uid(13)),
        lambda c: c["lyrics"].update(target_version_id=uid(14)),
    ],
)
def test_lyrics_rejects_discordant_history(change):
    c = context()
    attach_lyrics(c, 0, 13)
    c["lyrics"].update(mode="single", target_version_id=uid(13))
    change(c)
    reject(c)


def variation():
    c = inference("variation_request")
    req = {
        "job_id": uid(15),
        "task": "music.instrumental",
        "model_id": "test-model",
        "mode": "cpu",
        "inputs": [],
        "params": {},
        "seed": 16,
        "n_outputs": 2,
        "output_dir": f"tmp/{uid(15)}",
        "timeout_s": 60,
    }
    c["operation"]["basis"] = {
        "generation_job_id": uid(7),
        "winning_attempt_id": uid(15),
        "take_id": uid(4),
        "output_index": 1,
        "request_sha256": sha(wire(req)),
        "request": req,
        "lyrics_version_id": None,
    }
    return c


def test_variation_request_conserves_selected_effective_output():
    c = variation()
    cap = r.capture_recipe(c)
    assert cap.value.operation.basis.output_index == 1
    assert (
        cap.value.operation.basis.request.wire["seed"] == 16
        and cap.value.executor.seed == 18
    )
    assert r.project_input_requirements(cap) == ()
    out = r.project_engine_request(cap, attempt_id=uid(16), inputs=())
    assert out.n_outputs == 1 and out.seed == 18 and out.output_dir == f"tmp/{uid(16)}"


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["executor"].update(seed=17),
        lambda c: c["executor"].update(timeout_s=61),
        lambda c: c["executor"].update(mode=None),
        lambda c: c["operation"]["basis"].update(output_index=0),
        lambda c: c["operation"]["basis"]["request"].pop("inputs"),
        lambda c: c["operation"]["basis"].update(take_id=uid(9)),
        lambda c: c["operation"]["basis"].update(request_sha256="0" * 64),
    ],
)
def test_variation_rejects_reconstructed_or_changed_basis(change):
    c = variation()
    change(c)
    reject(c)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(provider={"type": "external"}),
        lambda d: d.update(weights=[]),
        lambda d: d["weights"][0].update(path="../weights"),
        lambda d: d["modes"][0].update(extra=True),
        lambda d: d.update(modes=[]),
    ],
)
def test_descriptor_rejects_unsafe_or_unclosed_snapshots(change):
    c = inference()
    d = c["executor"]["descriptor"].wire
    change(d)
    with pytest.raises(r.RecipeError):
        r.FrozenDescriptor.capture(d, evidence_kind="learned")


def test_descriptor_namespace_defaults_and_read_do_not_rewrite():
    d = inference()["executor"]["descriptor"].wire
    schema = d["tasks"]["music.retake"]["params_schema"]
    schema["properties"] = {
        k: {"type": "string"}
        for k in ("token", "tokenizer", "max_tokens", "token_budget")
    }
    d["provider"].pop("name")
    payload = wire(d)
    frozen = r.FrozenDescriptor.read(
        payload, expected_sha256=sha(payload), evidence_kind="learned"
    )
    assert frozen.payload == payload and "name" not in frozen.wire["provider"]
    frozen.value.provider.name = "mutated"
    frozen.wire["tasks"].clear()
    assert frozen.payload == payload
    captured = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    assert captured.wire["provider"]["name"] is None


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["executor"].update(descriptor_sha256="0" * 64),
        lambda c: c["executor"].update(mode="unknown"),
        lambda c: c["executor"].update(seed=True),
        lambda c: c["executor"].update(evidence_kind="synthetic"),
        lambda c: c["executor"].update(params={"password": "hidden"}),
        lambda c: c["executor"].update(params={"extra": 1}),
        lambda c: c.update(required_features=["unknown"]),
    ],
)
def test_inference_rejects_incoherent_selection(change):
    c = inference()
    change(c)
    reject(c)


@pytest.mark.parametrize(
    "inputs",
    [
        [],
        [{"role": "source", "media_types": ["audio/wav"], "required": True}],
        [{"role": "other", "media_types": ["audio/flac"], "required": True}],
        [{"role": "source", "media_types": ["audio/flac"], "required": True}] * 2,
        [
            {"role": "source", "media_types": ["audio/flac"], "required": True},
            {"role": "timbre", "media_types": ["audio/flac"], "required": True},
        ],
    ],
)
def test_inference_input_capabilities_exact(inputs):
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["inputs"] = inputs
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(descriptor=frozen, descriptor_sha256=frozen.sha256)
    reject(c)


def test_cpu_engine_projection_is_forbidden():
    cap = r.capture_recipe(context())
    with pytest.raises(r.RecipeError, match="RECIPE_CONTEXT_MISMATCH"):
        r.project_input_requirements(cap)
    with pytest.raises(r.RecipeError, match="RECIPE_CONTEXT_MISMATCH"):
        r.project_engine_request(cap, attempt_id=uid(9), inputs=())


@pytest.mark.parametrize(
    "path", ["/abs", "a//b", "a/./b", "a/../b", "C:/x", "a\\b", "https://host/x"]
)
def test_projection_rejects_unsafe_paths(path):
    with pytest.raises((r.RecipeError, ValueError)):
        r.ResolvedRecipeInput(
            asset_id=uid(5),
            role="source",
            path=path,
            sha256="a" * 64,
            media_type="audio/flac",
        )


@pytest.mark.parametrize(
    "schema",
    [
        True,
        {},
        {"type": "object", "properties": {}},
        {
            "type": "object",
            "properties": {"nested": {"type": "object"}},
            "additionalProperties": False,
        },
    ],
)
def test_params_schema_requires_closed_object(schema):
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"] = schema
    if schema is True:
        # El contrato público exige dict; la variante vacía descubre un root abierto.
        d["tasks"]["music.retake"]["params_schema"] = {}
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(descriptor=frozen, descriptor_sha256=frozen.sha256)
    reject(c)


def test_bool_channels_are_not_integer_channels():
    c = context()
    c["parents"][0]["asset"]["channels"] = True
    c["executor"]["output_format"]["channels"] = True
    reject(c)


def schema_context(schema, params):
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"] = schema
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen, descriptor_sha256=frozen.sha256, params=params
    )
    return c


def test_schema_object_union_must_be_closed():
    schema = {
        "type": "object",
        "properties": {"payload": {"type": ["object", "null"]}},
        "additionalProperties": False,
    }
    reject(schema_context(schema, {"payload": {"undeclared": 42}}), "RECIPE_INVALID")


@pytest.mark.parametrize(
    "child,value",
    [
        pytest.param({"type": "string", "required": []}, "text", id="string-required"),
        pytest.param(
            {"type": "integer", "minProperties": 0}, 3, id="integer-minProperties"
        ),
        pytest.param(
            {"type": "array", "propertyNames": {"type": "string"}},
            [1, "text"],
            id="array-propertyNames",
        ),
    ],
)
def test_schema_object_keywords_do_not_close_explicit_nonobjects(child, value):
    schema = {
        "type": "object",
        "properties": {"payload": child},
        "additionalProperties": False,
    }
    params = {"payload": value}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params


@pytest.mark.parametrize(
    "child",
    [
        {"type": ["object", "string"], "required": []},
        {"required": []},
        {"minProperties": 0},
        {"properties": {}},
    ],
)
def test_schema_admitting_objects_still_requires_explicit_closure(child):
    schema = {
        "type": "object",
        "properties": {"payload": child},
        "additionalProperties": False,
    }
    reject(schema_context(schema, {"payload": {"undeclared": 42}}), "RECIPE_INVALID")


@pytest.mark.parametrize(
    "child,value",
    [
        ({"type": "null"}, None),
        ({"type": "boolean"}, True),
        ({"type": "number"}, 1.5),
        ({"type": "integer"}, 3),
        ({"type": "string"}, "text"),
        ({"type": "array", "items": {"type": "number"}}, [1, 2.5]),
        ({"type": ["string", "null"]}, None),
    ],
)
def test_schema_explicit_nonobject_types_remain_validated(child, value):
    schema = {
        "type": "object",
        "properties": {"payload": child},
        "additionalProperties": False,
    }
    params = {"payload": value}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params
    reject(schema_context(schema, {"payload": {"undeclared": 42}}), "RECIPE_INVALID")


def test_schema_property_named_properties_is_data_map_entry():
    schema = {
        "type": "object",
        "properties": {"properties": {"type": "string"}},
        "additionalProperties": False,
    }
    params = {"properties": "artistic setting"}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params


def test_schema_const_object_is_data_not_schema():
    schema = {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "properties": {"type": {"type": "string"}},
                "additionalProperties": False,
                "const": {"type": "object"},
            }
        },
        "additionalProperties": False,
    }
    params = {"payload": {"type": "object"}}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params


@pytest.mark.parametrize("ref", ["#", "#node"])
def test_schema_recursive_local_ref_is_supported(ref):
    schema = {
        "$anchor": "node",
        "type": "object",
        "properties": {"child": {"$ref": ref}},
        "additionalProperties": False,
    }
    params = {"child": {"child": {}}}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params


@pytest.mark.parametrize(
    "keyword", ["allOf", "anyOf", "oneOf", "items", "prefixItems", "contains"]
)
def test_schema_object_union_closed_in_combinators_and_arrays(keyword):
    child = {"type": ["object", "null"]}
    nested = (
        {keyword: [child]}
        if keyword in {"allOf", "anyOf", "oneOf", "prefixItems"}
        else {keyword: child}
    )
    schema = {
        "type": "object",
        "properties": {"payload": nested},
        "additionalProperties": False,
    }
    reject(schema_context(schema, {}), "RECIPE_INVALID")


def test_schema_internal_pointer_to_open_union_is_rejected():
    schema = {
        "type": "object",
        "properties": {"payload": {"$ref": "#/$defs/payload"}},
        "additionalProperties": False,
        "$defs": {"payload": {"type": ["object", "null"]}},
    }
    reject(schema_context(schema, {"payload": {"undeclared": 42}}), "RECIPE_INVALID")
    schema["$defs"]["payload"].update(properties={}, additionalProperties=False)
    captured = r.capture_recipe(schema_context(schema, {"payload": None}))
    assert captured.value.executor.params.wire == {"payload": None}


@pytest.mark.parametrize("keyword", ["const", "default", "enum", "examples"])
def test_schema_literal_values_are_not_walked_as_schemas(keyword):
    literal = {"type": "object", "properties": {"properties": "artistic setting"}}
    child = {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "properties": {
                "type": "object",
                "properties": {"properties": {"type": "string"}},
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
        keyword: [literal] if keyword in {"enum", "examples"} else literal,
    }
    schema = {
        "type": "object",
        "properties": {"payload": child},
        "additionalProperties": False,
    }
    params = {"payload": literal}
    captured = r.capture_recipe(schema_context(schema, params))
    assert captured.value.executor.params.wire == params


def fade_context(incoming, outgoing, pieces):
    c = context()
    c["operation"] = {"kind": "fade", "fade_in_s": incoming, "fade_out_s": outgoing}
    c["parents"][0]["section_map"]["ops"] = [
        {"op": kind, "src": [a, b], "dst": [a, b]} for kind, a, b in pieces
    ]
    return c


def test_fix1_fade_partition_preserves_parent_coordinates():
    pieces = [("fade", 0, 2), ("keep", 2, 7), ("fade", 7, 10)]
    captured = r.capture_recipe(fade_context(2, 3, pieces))
    ops = captured.value.parents[0].section_map.ops
    assert [(op.op, op.src, op.dst) for op in ops] == [
        (kind, (float(a), float(b)), (float(a), float(b))) for kind, a, b in pieces
    ]
    reject(fade_context(2, 3, [("keep", 0, 10)]), "RECIPE_INVALID")


@pytest.mark.parametrize(
    "incoming,outgoing,pieces",
    [
        (10, None, [("fade", 0, 10)]),
        (None, 10, [("fade", 0, 10)]),
        (4, 6, [("fade", 0, 4), ("fade", 4, 10)]),
        (None, 2, [("keep", 0, 8), ("fade", 8, 10)]),
    ],
)
def test_fix1_fade_omits_zero_length_pieces(incoming, outgoing, pieces):
    captured = r.capture_recipe(fade_context(incoming, outgoing, pieces))
    ops = captured.value.parents[0].section_map.ops
    assert [(op.op, op.src, op.dst) for op in ops] == [
        (kind, (float(a), float(b)), (float(a), float(b))) for kind, a, b in pieces
    ]


def test_fix1_fade_requires_at_least_one_envelope():
    reject(fade_context(None, None, [("keep", 0, 10)]), "RECIPE_INVALID")


@pytest.mark.parametrize("incoming,outgoing", [(11, None), (None, 11), (6, 5)])
def test_fix1_fade_rejects_exceeding_parent_duration(incoming, outgoing):
    reject(fade_context(incoming, outgoing, [("keep", 0, 10)]), "RECIPE_INVALID")


@pytest.mark.parametrize(
    "kind,fields,maps",
    [
        (
            "fade",
            {"fade_in_s": 2, "fade_out_s": 3},
            [
                {"op": "fade", "src": [0, 2], "dst": [0, 2]},
                {"op": "keep", "src": [2, 7], "dst": [2, 7]},
                {"op": "fade", "src": [7, 10], "dst": [7, 10]},
            ],
        ),
        (
            "fade",
            {"fade_in_s": 10, "fade_out_s": None},
            [{"op": "fade", "src": [0, 10], "dst": [0, 10]}],
        ),
    ],
)
def test_fade_captures_only_nonempty_partition(kind, fields, maps):
    c = context()
    c["operation"] = dict(kind=kind, **fields)
    c["parents"][0]["section_map"]["ops"] = maps
    cap = r.capture_recipe(c)
    assert len(cap.value.parents[0].section_map.ops) == len(maps)
    c["operation"]["fade_in_s"] = 11
    reject(c)


@pytest.mark.parametrize(
    "kind,fields,maps,coordinates,params",
    [
        (
            "extend",
            {"at_s": 10},
            [
                {"op": "keep", "src": [0, 10], "dst": [0, 10]},
                {"op": "append", "src": None, "dst": None},
            ],
            {"at_s": "point", "t0": None, "t1": None},
            {"point": 10},
        ),
        (
            "extend",
            {"at_s": 0},
            [{"op": "append", "src": None, "dst": None}],
            {"at_s": "point", "t0": None, "t1": None},
            {"point": 0},
        ),
        (
            "repaint",
            {"region": [0, 10]},
            [{"op": "regen", "src": None, "dst": None}],
            {"at_s": None, "t0": "start", "t1": "end"},
            {"start": 0, "end": 10},
        ),
        (
            "repaint",
            {"region": [2, 8]},
            [
                {"op": "keep", "src": [0, 2], "dst": [0, 2]},
                {"op": "regen", "src": None, "dst": None},
                {"op": "keep", "src": [8, 10], "dst": None},
            ],
            {"at_s": None, "t0": "start", "t1": "end"},
            {"start": 2, "end": 8},
        ),
    ],
)
def test_extend_repaint_coordinates_and_maps_are_exact(
    kind, fields, maps, coordinates, params
):
    c = inference(kind)
    c["operation"] = dict(kind=kind, **fields)
    c["parents"][0]["section_map"]["ops"] = maps
    d = c["executor"]["descriptor"].wire
    d["tasks"][c["executor"]["task"]]["params_schema"]["properties"] = {
        k: {"type": "number"} for k in params
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen,
        descriptor_sha256=frozen.sha256,
        coordinate_params=coordinates,
        params=params,
        output_shape="region",
    )
    cap = r.capture_recipe(c)
    assert cap.value.executor.params.wire == params
    c["executor"]["params"][next(iter(params))] = 99
    reject(c)


@pytest.mark.parametrize(
    "value", [float("inf"), (1, 2), b"x", {"a": {"b": [float("nan")]}}]
)
def test_frozen_json_rejects_non_json(value):
    with pytest.raises((r.RecipeError, ValueError)):
        r.FrozenJSON.model_validate(value)


def test_dynamic_cycles_and_limits_are_rejected():
    c = context()
    c["extra"] = c
    reject(c)
    for extra in ([0] * 257, "x" * 8193):
        c = context()
        c["extra"] = extra
        reject(c)
    deep = {}
    node = deep
    for _ in range(22):
        node["child"] = {}
        node = node["child"]
    c = context()
    c["extra"] = deep
    reject(c)


def test_new_read_does_not_normalize_noncanonical_seconds_or_whitespace():
    cap = r.capture_request(context())
    data = cap.value.model_dump(mode="json")
    data["recipe"]["operation"]["region"][0] = 2
    data["recipe_sha256"] = sha(wire(data["recipe"]))
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(wire(data))
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(b" " + cap.payload)


@pytest.mark.parametrize(
    "legacy",
    [
        {
            "inputs": [
                {
                    "role": "source",
                    "ref": {"type": "job", "id": uid(7)},
                    "output_index": 0,
                }
            ]
        },
        {
            "params": {},
            "inputs": [{"role": "master", "ref": {"type": "take", "id": uid(4)}}],
        },
        {"seed": None, "mode": None},
    ],
)
def test_legacy_snapshot_job_requests_preserve_presence(legacy):
    # Fragmento del rows.job real: no se pretende validar un snapshot completo.
    snapshot = {
        "version": 1,
        "song_id": uid(2),
        "rows": {"job": [{"request": copy.deepcopy(legacy)}]},
    }
    before = wire(snapshot)
    view = r.read_request(snapshot["rows"]["job"][0]["request"])
    assert view.value == legacy and wire(snapshot) == before


def test_projection_wrong_resolved_identity_is_rejected():
    cap = r.capture_recipe(inference())
    for field, value in [
        ("asset_id", uid(9)),
        ("sha256", "b" * 64),
        ("media_type", "audio/wav"),
    ]:
        item = {
            "asset_id": uid(5),
            "role": "source",
            "path": "songs/test/master.flac",
            "sha256": "a" * 64,
            "media_type": "audio/flac",
        }
        item[field] = value
        with pytest.raises(r.RecipeError):
            r.project_engine_request(
                cap, attempt_id=uid(9), inputs=(r.ResolvedRecipeInput(**item),)
            )
    with pytest.raises(r.RecipeError):
        r.project_engine_request(cap, attempt_id=uid(9), inputs=())


def test_params_and_descriptor_are_deeply_frozen():
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"]["properties"] = {
        "nested": {
            "type": "object",
            "properties": {"values": {"type": "array", "items": {"type": "number"}}},
            "additionalProperties": False,
        }
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen,
        descriptor_sha256=frozen.sha256,
        params={"nested": {"values": [1, -0.0]}},
    )
    cap = r.capture_recipe(c)
    before = cap.payload
    c["executor"]["params"]["nested"]["values"].append(2)
    cap.value.executor.params.wire["nested"]["values"].append(3)
    cap.value.executor.descriptor.wire["tasks"].clear()
    cap.value.executor.descriptor.value.tasks.clear()
    assert cap.payload == before and b"-0.0" in before
    reordered = dict(reversed(list(context().items())))
    assert r.capture_recipe(reordered).sha256 == r.capture_recipe(context()).sha256


def test_mapping_callers_are_copied():
    c = context()
    cap = r.capture_recipe(MappingProxyType(c))
    assert cap.sha256 == r.capture_recipe(c).sha256
    view = r.read_request(MappingProxyType({"seed": 17}))
    assert view.value == {"seed": 17} and view.raw_payload is None


def test_synthetic_descriptor_and_binding_are_captured_without_runtime_authority():
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["weights"] = []
    desc = r.FrozenDescriptor.capture(d, evidence_kind="synthetic")
    implementation = {
        "name": "test",
        "revision": "fixed",
        "source_sha256": "a" * 64,
        "common_source_sha256": "b" * 64,
    }
    binding = {
        "version": 1,
        "recipe_id": "test",
        "scope": "test",
        "origin": "http://127.0.0.1:8119",
        "engine_id": "test",
        "engine_version": "1",
        "contract_version": "1",
        "descriptor_sha256": desc.sha256,
        "implementation": implementation,
        "implementation_sha256": sha(wire(implementation)),
        "expected_image_digest": None,
    }
    c["executor"].update(
        descriptor=desc,
        descriptor_sha256=desc.sha256,
        evidence_kind="synthetic",
        synthetic_binding=binding,
    )
    cap = r.capture_recipe(c)
    assert cap.value.executor.synthetic_binding.scope == "test"
    assert not cap.value.executor.tools[0].runtime_verified
    binding["engine_id"] = "other"
    reject(c)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["tasks"]["music.retake"].update(verified=False),
        lambda d: d["tasks"]["music.retake"]["params_schema"].update(
            **{"$ref": "https://example.invalid/schema"}
        ),
        lambda d: d["tasks"]["music.retake"].update(
            features={"fidelity": {"verified": False}}
        ),
    ],
)
def test_unverified_task_feature_or_external_schema_never_enables_selection(change):
    c = inference()
    d = c["executor"]["descriptor"].wire
    change(d)
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(descriptor=frozen, descriptor_sha256=frozen.sha256)
    if "fidelity" in d["tasks"]["music.retake"]["features"]:
        c["required_features"] = ["fidelity"]
    reject(c)


def test_descriptor_token_namespace_is_allowed_but_actual_token_param_is_not():
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"]["properties"] = {
        "token": {"type": "string"},
        "max_tokens": {"type": "integer"},
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen, descriptor_sha256=frozen.sha256, params={"max_tokens": 10}
    )
    r.capture_recipe(c)
    c["executor"]["params"] = {"token": "actual-secret"}
    reject(c, "RECIPE_SECRET_FORBIDDEN")


def test_instrumental_variant_preserves_historical_lyrics():
    c = variation()
    attach_lyrics(c, 0, 13)
    cap = r.capture_recipe(c)
    assert cap.value.lyrics.mode == "instrumental"
    assert cap.value.lyrics.versions[0].id == uid(13)
    assert "lyrics" not in cap.value.executor.params.wire


def test_rights_and_pins_commercial_flags_are_conjunctive():
    c = context()
    c["parents"][0]["asset"]["rights"]["inputs"] = [
        {
            "ref": {"type": "upload", "id": uid(13)},
            "sha256": "c" * 64,
            "rights": "licensed",
            "consent": "n_a",
            "real_person": False,
            "commercial_use": False,
        }
    ]
    c["commercial_use"] = False
    cap = r.capture_recipe(c)
    assert cap.value.parents[0].asset.rights.inputs[0].rights == "licensed"
    c["commercial_use"] = True
    reject(c)
    c["commercial_use"] = False
    c["parents"][0]["asset"]["rights"]["inputs"][0]["real_person"] = True
    reject(c, "RIGHTS_DECLARATION_REQUIRED")


@pytest.mark.parametrize(
    "bad",
    [
        {"inputs": [{"role": "source", "ref": {"type": "job", "id": "bad"}}]},
        {
            "inputs": [
                {"role": "source", "ref": {"type": "job", "id": uid(3)}, "path": "a"}
            ]
        },
        {
            "inputs": [
                {
                    "role": "source",
                    "ref": {"type": "job", "id": uid(3)},
                    "output_index": True,
                }
            ]
        },
        {"seed": True},
        {"params": []},
        {"n_outputs": 65},
        {"timeout_s": 0},
        {"mode": 1},
        {"required_features": [1]},
        {"unknown": 1},
    ],
)
def test_legacy_invalid_fields_are_not_coerced(bad):
    with pytest.raises(r.RecipeError):
        r.read_request(bad)


@pytest.mark.parametrize(
    "extra_path",
    [
        ("operation",),
        ("sampling",),
        ("executor", "output_format"),
        ("parents", 0),
        ("parents", 0, "asset"),
        ("parents", 0, "asset", "ref"),
        ("parents", 0, "asset", "rights"),
        ("parents", 0, "origin"),
        ("parents", 0, "section_map"),
        ("parents", 0, "section_map", "ops", 0),
        ("lyrics",),
        ("lyrics", "parent_bindings", 0),
        ("executor", "tools", 0),
    ],
)
def test_each_nested_dto_is_closed(extra_path):
    c = context()
    node = c
    for key in extra_path:
        node = node[key]
    node["extra"] = 1
    reject(c)


def test_one_mebibyte_recipe_limit_applies_to_frozen_backing():
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"]["properties"] = {
        "values": {"type": "array", "items": {"type": "string"}}
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen,
        descriptor_sha256=frozen.sha256,
        params={"values": ["x" * 8192] * 129},
    )
    reject(c)


def test_canonical_functions_use_valid_dtos_and_raw_hash_contracts():
    cap = r.capture_request(context())
    for value in (cap, cap.value):
        assert r.canonical_bytes(value) == cap.payload
        assert r.canonical_sha256(value) == cap.sha256
    for value in (cap.recipe, cap.recipe.value):
        assert r.canonical_bytes(value) == cap.recipe.payload
    with pytest.raises(r.RecipeError):
        r.canonical_bytes({})
    data = cap.value.model_dump(mode="json")
    assert r.read_request(data, expected_sha256=sha(wire(data))).payload == cap.payload
    with pytest.raises(r.RecipeError, match="RECIPE_HASH_MISMATCH"):
        r.read_request(data, expected_sha256="0" * 64)


def test_dynamic_descriptor_named_key_cannot_hide_credentials():
    with pytest.raises(r.RecipeError, match="RECIPE_SECRET_FORBIDDEN"):
        r.read_request({"params": {"descriptor": {"token": "private"}}})


def test_basis_params_require_exact_json_types():
    c = variation()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.instrumental"]["params_schema"]["properties"] = {
        "amount": {"type": "number"}
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen, descriptor_sha256=frozen.sha256, params={"amount": 1.0}
    )
    c["operation"]["basis"]["request"]["params"] = {"amount": 1}
    c["operation"]["basis"]["request_sha256"] = sha(
        wire(c["operation"]["basis"]["request"])
    )
    reject(c, "RECIPE_CONTEXT_MISMATCH")


def test_private_error_does_not_retain_pydantic_context():
    c = context()
    c["operation"]["extra"] = "private-artistic-history"
    with pytest.raises(r.RecipeError) as caught:
        r.capture_recipe(c)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert "private-artistic-history" not in str(caught.value)


def test_long_lyrics_exception_does_not_apply_to_nested_params():
    c = inference()
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.retake"]["params_schema"]["properties"] = {
        "nested": {
            "type": "object",
            "properties": {"lyrics": {"type": "string"}},
            "additionalProperties": False,
        }
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    c["executor"].update(
        descriptor=frozen,
        descriptor_sha256=frozen.sha256,
        params={"nested": {"lyrics": "ñ" * 9000}},
    )
    reject(c)


def test_vocal_variation_preserves_exact_effective_lyrics_and_authorship():
    c = variation()
    text = "[Verse]\r\n" + "ñ" * 9000
    attach_lyrics(c, 0, 13, text, declaration="assistant")
    c["lyrics"].update(mode="single", target_version_id=uid(13))
    d = c["executor"]["descriptor"].wire
    d["tasks"]["music.song"] = d["tasks"].pop("music.instrumental")
    d["tasks"]["music.song"]["params_schema"]["properties"] = {
        "lyrics": {"type": "string"},
        "style": {"type": "string"},
    }
    frozen = r.FrozenDescriptor.capture(d, evidence_kind="learned")
    params = {"lyrics": text, "style": "pop local"}
    c["executor"].update(
        task="music.song",
        descriptor=frozen,
        descriptor_sha256=frozen.sha256,
        params=params,
    )
    basis = c["operation"]["basis"]
    basis["lyrics_version_id"] = uid(13)
    basis["request"].update(task="music.song", params=copy.deepcopy(params))
    basis["request_sha256"] = sha(wire(basis["request"]))
    cap = r.capture_recipe(c)
    assert cap.value.lyrics.versions[0].declaration == "assistant"
    assert (
        r.project_engine_request(cap, attempt_id=uid(16), inputs=()).params["lyrics"]
        == text
    )
    params["lyrics"] = "otra letra actual"
    reject(c)
