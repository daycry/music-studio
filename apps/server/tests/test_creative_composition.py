"""Invariantes sintéticos del compositor puro; no prueba audio ni autoridad."""

import math
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.creative import composition as c
from app.creative import recipes as r
from pydantic import ValidationError
from test_creative_recipes import (
    context,
    crossfade,
    inference,
    sha,
    uid,
    variation,
    wire,
)


def captured(
    kind="trim",
    *,
    region=(2.05, 7.15),
    incoming=1.05,
    outgoing=2.05,
    duration=2.05,
    at=7.0,
    shape="region",
    b_rate=10,
    b_channels=2,
):
    data = (
        crossfade()
        if kind == "crossfade"
        else context()
        if kind in {"trim", "fade"}
        else variation()
        if kind == "variation_request"
        else inference(kind)
    )
    data["parents"][0]["asset"].update(sample_rate=10, channels=2)
    if kind == "crossfade":
        data["parents"][1]["asset"].update(
            sample_rate=b_rate, channels=b_channels, duration_s=8.0
        )
        data["operation"] = {"kind": kind, "duration_s": duration}
    elif kind in {"trim", "repaint"}:
        data["operation"] = {"kind": kind, "region": list(region)}
    elif kind == "fade":
        data["operation"] = {
            "kind": kind,
            "fade_in_s": incoming,
            "fade_out_s": outgoing,
        }
    elif kind == "extend":
        data["operation"] = {"kind": kind, "at_s": at}
    if kind in {"trim", "fade", "crossfade"}:
        data["executor"]["output_format"].update(sample_rate=10, channels=2)
    else:
        data["executor"]["output_shape"] = (
            shape if kind in {"extend", "repaint"} else "full"
        )
        if kind in {"extend", "repaint"}:
            params = (
                {"point": at}
                if kind == "extend"
                else {"start": region[0], "end": region[1]}
            )
            coords = (
                {"at_s": "point", "t0": None, "t1": None}
                if kind == "extend"
                else {"at_s": None, "t0": "start", "t1": "end"}
            )
            desc = data["executor"]["descriptor"].wire
            desc["tasks"][data["executor"]["task"]]["params_schema"]["properties"] = {
                key: {"type": "number"} for key in params
            }
            frozen = r.FrozenDescriptor.capture(desc, evidence_kind="learned")
            data["executor"].update(
                params=params,
                coordinate_params=coords,
                descriptor=frozen,
                descriptor_sha256=frozen.sha256,
            )
    pseudo = SimpleNamespace(
        operation=SimpleNamespace(**data["operation"]),
        parents=[
            SimpleNamespace(asset=SimpleNamespace(**p["asset"]))
            for p in data["parents"]
        ],
    )
    for parent, maps in zip(data["parents"], r.expected_maps(pseudo), strict=True):
        parent["section_map"]["ops"] = [
            {
                "op": k,
                "src": None if s is None else list(s),
                "dst": None if d is None else list(d),
            }
            for k, s, d in maps
        ]
    recipe = r.capture_recipe(data)
    parents = tuple(
        {
            "parent_id": p.ref.id,
            "asset_id": p.asset.ref.id,
            "root_id": p.root_id,
            "role": p.role,
            "buffer": buffer(
                "parent_a" if i == 0 else "parent_b",
                int(p.asset.duration_s * p.asset.sample_rate),
                p.asset.sample_rate,
                p.asset.channels,
                p.asset.sha256,
            ),
        }
        for i, p in enumerate(recipe.value.parents)
    )
    return recipe, parents


def engine_facts(recipe, frames=25, rate=10, channels=2):
    return {
        "recipe_sha256": recipe.sha256,
        "descriptor_sha256": recipe.value.executor.descriptor_sha256,
        "output_shape": recipe.value.executor.output_shape,
        "buffer": buffer("engine", frames, rate, channels, "c" * 64),
        "result": measurement(),
    }


def build(recipe, parents, engine=None, converted=()):
    return c.build_composition_plan(
        recipe, parents=parents, engine=engine, converted=converted
    )


def measurement():
    return {
        "evidence_id": "0" * 25 + "1",
        "evidence_sha256": "e" * 64,
        "evidence_kind": "synthetic",
    }


def buffer(buffer_id="parent_a", frames=100, rate=10, channels=2, sha="a" * 64):
    return {
        "buffer_id": buffer_id,
        "frames": frames,
        "format": {"sample_rate": rate, "channels": channels},
        "sha256": sha,
        "duration_s": float(frames / rate),
        "measurement": measurement(),
    }


def test_ac02_decimal_half_up():
    assert c.round_frame(0.05, 10) == 1
    assert c.round_frame(0.15, 10) == 2
    assert c.round_frame(1.005, 100) == 101
    assert c.round_frame(5e-2, 10) == 1
    assert c.round_frame(-0.0, 10) == 0


def test_ac04_exact_numbers():
    for seconds, rate in [
        (True, 10),
        ("0.05", 10),
        (Decimal("0.05"), 10),
        (0.05, True),
        (float("nan"), 10),
        (float("inf"), 10),
        (-1, 10),
        (1, 0),
        (1, 1.0),
    ]:
        with pytest.raises(c.CompositionError) as error:
            c.round_frame(seconds, rate)
        assert error.value.code == "COMPOSITION_INVALID"


def test_ac05_round_limits():
    assert c.round_frame(1, 2**31 - 1) == 2**31 - 1
    for seconds, rate in [(1e308, 10), (2**63, 1), (1, 2**31), (10**400, 10)]:
        with pytest.raises(c.CompositionError) as error:
            c.round_frame(seconds, rate)
        assert error.value.code == "COMPOSITION_LIMIT_EXCEEDED"


def test_ac04_facts_strict_dto():
    good = buffer()
    assert c.BufferFacts(**good).frames == 100
    for field, value in [
        ("frames", True),
        ("frames", 0),
        ("duration_s", 10),
        ("duration_s", "10.0"),
        ("duration_s", float("inf")),
        ("frames", 2**63),
        ("sha256", "secret"),
    ]:
        with pytest.raises((ValidationError, c.CompositionError)):
            c.BufferFacts(**dict(good, **{field: value}))
    for fmt in [
        {"sample_rate": True, "channels": 2},
        {"sample_rate": 10, "channels": True},
        {"sample_rate": 2**31, "channels": 2},
        {"sample_rate": 10, "channels": 3},
    ]:
        with pytest.raises((ValidationError, c.CompositionError)):
            c.BufferFacts(**dict(good, format=fmt))
    assert c.BufferFacts(**buffer(frames=2**63 - 1, rate=1)).frames == 2**63 - 1


def test_ac06_measured_duration():
    assert c.BufferFacts(**buffer()).duration_s == 10.0
    with pytest.raises((c.CompositionError, ValidationError)) as error:
        c.BufferFacts(**dict(buffer(), duration_s=10.01))
    assert "COMPOSITION_DURATION_MISMATCH" in str(error.value)


def test_ac07_anchored_bounds():
    facts = c.BufferFacts(**buffer(frames=7, rate=3))
    assert c.resolve_region((0.0, facts.duration_s), facts) == (0, 7)
    for region in [
        (0.0, math.nextafter(facts.duration_s, math.inf)),
        (-0.1, 1.0),
        (1.0, 3.0),
    ]:
        with pytest.raises(c.CompositionError) as error:
            c.resolve_region(region, facts)
        assert error.value.code in {"COMPOSITION_OUT_OF_BOUNDS", "COMPOSITION_INVALID"}


def test_ac03_collapsed_region():
    facts = c.BufferFacts(**buffer())
    assert c.resolve_region((0.0, 0.2), facts) == (0, 2)
    with pytest.raises(c.CompositionError) as error:
        c.resolve_region((0.01, 0.02), facts)
    assert error.value.code == "COMPOSITION_INTERVAL_COLLAPSED"


def test_ac01_trim_and_fade_counts():
    recipe, parents = captured()
    plan = build(recipe, parents).value
    assert (plan.output_frames, plan.output_duration_s) == (51, 5.1)
    assert plan.pieces[0].terms[0].span == (21, 72)
    assert plan.edges[0].ops[0].dst == (0, 51)
    recipe, parents = captured("fade")
    plan = build(recipe, parents).value
    assert [p.dst for p in plan.pieces] == [(0, 11), (11, 79), (79, 100)]
    assert [p.kind for p in plan.pieces] == ["fade", "copy", "fade"]
    assert [o.envelope for o in plan.edges[0].ops] == [
        "linear_in",
        "identity",
        "linear_out",
    ]


def test_ac03_envelope_minimum():
    for length, code in [
        (0.01, "COMPOSITION_INTERVAL_COLLAPSED"),
        (0.1, "COMPOSITION_ENVELOPE_TOO_SHORT"),
    ]:
        recipe, parents = captured("fade", incoming=length, outgoing=None)
        with pytest.raises(c.CompositionError) as error:
            build(recipe, parents)
        assert error.value.code == code
    recipe, parents = captured("fade", incoming=0.2, outgoing=None)
    assert build(recipe, parents).value.pieces[0].dst == (0, 2)


def test_ac06_parent_binding():
    recipe, parents = captured()
    assert (
        build(recipe, parents).value.inputs[0].parent_id
        == recipe.value.parents[0].ref.id
    )
    for field, value, code in [
        ("asset_id", uid(99), "COMPOSITION_CONTEXT_MISMATCH"),
        ("parent_id", uid(99), "COMPOSITION_CONTEXT_MISMATCH"),
        ("root_id", uid(99), "COMPOSITION_CONTEXT_MISMATCH"),
        ("role", "crossfade_a", "COMPOSITION_CONTEXT_MISMATCH"),
    ]:
        with pytest.raises(c.CompositionError) as error:
            build(recipe, (dict(parents[0], **{field: value}),))
        assert error.value.code == code
    with pytest.raises(c.CompositionError) as error:
        build(recipe, (dict(parents[0], buffer=buffer(sha="d" * 64)),))
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"


def test_ac08_crossfade_dual_edges():
    recipe, parents = captured("crossfade")
    plan = build(recipe, parents).value
    assert plan.output_frames == 159
    assert [piece.dst for piece in plan.pieces] == [(0, 79), (79, 100), (100, 159)]
    assert [t.envelope for t in plan.pieces[1].terms] == ["linear_out", "linear_in"]
    assert [edge.role for edge in plan.edges] == ["crossfade_a", "crossfade_b"]
    assert [op.dst for op in plan.edges[1].ops] == [(79, 100), (100, 159)]
    assert plan.edges[1].source_frames == 80
    with pytest.raises(c.CompositionError):
        build(recipe, parents[::-1])
    with pytest.raises(c.CompositionError):
        build(recipe, parents[:1])


def conversion(recipe, parents, engine=None, frames=81):
    requirements = c.conversion_requirements(recipe, parents=parents, engine=engine)
    assert len(requirements) == 1, "formats differ: exactly one conversion is required"
    requirement = requirements[0]
    original = (
        parents[1]["buffer"]
        if requirement.conversion_id == "b_to_target"
        else engine["buffer"]
    )
    return {
        "requirement": requirement,
        "buffer": buffer(
            "converted_b"
            if requirement.conversion_id == "b_to_target"
            else "converted_engine",
            frames,
            requirement.target_format.sample_rate,
            requirement.target_format.channels,
            "d" * 64,
        ),
        "evidence": measurement(),
        "conversion_scope": (0, original["frames"]),
    }


def test_ac09_conversion_preflight_and_closed_facts():
    recipe, parents = captured("crossfade", b_rate=20, b_channels=1, duration=2.0)
    req = c.conversion_requirements(recipe, parents=parents, engine=None)
    assert len(req) == 1 and req[0].channel_policy == "mono_to_stereo_duplicate"
    assert req[0].resample_policy == "soxr_pinned"
    assert req[0].tool == recipe.value.executor.tools[0]
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents)
    assert error.value.code == "COMPOSITION_FACTS_REQUIRED"

    cf = conversion(recipe, parents)
    plan = build(recipe, parents, converted=(cf,)).value
    assert plan.output_frames == 161
    bops = plan.edges[1].ops
    assert [o.op for o in bops] == ["convert", "convert"]
    assert [o.effect for o in bops] == ["fade", "keep"]
    assert [o.nominal_src for o in bops] == [(0, 40), (40, 160)]
    assert all(o.src is None and o.claim == "transformed" for o in bops)
    assert plan.conversions[0].conversion_scope == (0, 160)
    for wrong in [
        dict(cf, conversion_scope=(0, 159)),
        dict(cf, buffer=buffer("converted_b", 81, 20, 2, "d" * 64)),
    ]:
        with pytest.raises(c.CompositionError):
            build(recipe, parents, converted=(wrong,))


def test_ac15_frozen_nested_and_wrapper():
    from dataclasses import FrozenInstanceError

    recipe, parents = captured()
    old = (recipe.payload, recipe.sha256)
    plan = build(recipe, parents)
    original = plan.payload
    with pytest.raises(ValidationError):
        plan.value.inputs[0].buffer.frames = 99
    with pytest.raises(ValidationError):
        plan.value.output_frames = 9
    with pytest.raises(FrozenInstanceError):
        plan.sha256 = "b" * 64
    parents[0]["buffer"]["frames"] = 9
    plan.value.model_dump(mode="json")["pieces"].clear()
    assert plan.payload == original and (recipe.payload, recipe.sha256) == old


def test_ac11_repaint_region_and_full_counts():
    for shape in ["region", "full"]:
        recipe, parents = captured("repaint", region=(2.0, 4.0), shape=shape)
        plan = build(
            recipe,
            parents,
            engine_facts(recipe, frames=25 if shape == "region" else 105),
        ).value
        assert plan.output_frames == 105 and plan.output_duration_s == 10.5
        assert [op.dst for op in plan.edges[0].ops] == [(0, 20), (20, 45), (45, 105)]
        assert plan.edges[0].ops[-1].src == (40, 100)
        assert len(plan.pieces) == (3 if shape == "region" else 1)
        if shape == "region":
            assert [piece.terms[0].span for piece in plan.pieces] == [
                (0, 20),
                (0, 25),
                (40, 100),
            ]
        else:
            assert plan.pieces[0].terms[0].span == (0, 105)

    recipe, parents = captured("repaint", region=(2.0, 4.0), shape="full")
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents, engine_facts(recipe, frames=80))
    assert error.value.code == "COMPOSITION_INTERVAL_COLLAPSED"
    assert build(recipe, parents, engine_facts(recipe, frames=81)).value.edges[0].ops[
        1
    ].dst == (20, 21)


def test_ac12_variations_and_cover_native_full():
    for kind in ["variation_request", "variation_audio", "cover"]:
        recipe, parents = captured(kind)
        engine = engine_facts(recipe, frames=37, rate=20, channels=1)
        assert c.conversion_requirements(recipe, parents=parents, engine=engine) == ()
        plan = build(recipe, parents, engine).value
        assert (plan.output_frames, plan.output_duration_s) == (37, 1.85)
        assert (plan.target_format.sample_rate, plan.target_format.channels) == (20, 1)
        assert len(plan.pieces) == 1 and plan.pieces[0].terms[0].span == (0, 37)
        op = plan.edges[0].ops[0]
        assert op.op == "regen" and op.src is None and op.claim == "generated"


def test_ac10_empty_nominal_tail_is_real_dependency():
    recipe, parents = captured("crossfade", b_rate=20, b_channels=1, duration=8.0)
    cf = conversion(recipe, parents, frames=81)
    plan = build(recipe, parents, converted=(cf,)).value
    tail = plan.edges[1].ops[-1]
    assert tail.nominal_src == (160, 160) and tail.src is None
    assert tail.render_span == (80, 81) and tail.dst == (100, 101)
    assert plan.output_frames == 101 and plan.conversions[0].conversion_scope == (
        0,
        160,
    )
    assert (
        len(
            build(recipe, parents, converted=(conversion(recipe, parents, frames=80),))
            .value.edges[1]
            .ops
        )
        == 1
    )
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents, converted=(conversion(recipe, parents, frames=79),))
    assert error.value.code == "COMPOSITION_OUT_OF_BOUNDS"


def test_ac12_engine_binding_and_shape():
    recipe, parents = captured()
    with pytest.raises(c.CompositionError) as error:
        c.conversion_requirements(
            recipe, parents=parents, engine={"buffer": buffer("engine")}
        )
    assert error.value.code == "COMPOSITION_CONTEXT_MISMATCH"
    recipe, parents = captured("repaint", region=(2.0, 4.0))
    engine = engine_facts(recipe)
    assert c.conversion_requirements(recipe, parents=parents, engine=engine) == ()
    for override, code in [
        ({"output_shape": "full"}, "COMPOSITION_CONTEXT_MISMATCH"),
        ({"recipe_sha256": "f" * 64}, "COMPOSITION_HASH_MISMATCH"),
        ({"descriptor_sha256": "f" * 64}, "COMPOSITION_HASH_MISMATCH"),
    ]:
        with pytest.raises(c.CompositionError) as error:
            c.conversion_requirements(
                recipe, parents=parents, engine=dict(engine, **override)
            )
        assert error.value.code == code
    with pytest.raises(c.CompositionError) as error:
        c.conversion_requirements(recipe, parents=parents, engine=None)
    assert error.value.code == "COMPOSITION_FACTS_REQUIRED"


def test_ac14_full_keep_is_not_proven_copy():
    for shape, claim in [
        ("region", "direct_copy"),
        ("full", "declared_keep_unverified"),
    ]:
        recipe, parents = captured("repaint", region=(2.0, 4.0), shape=shape)
        plan = build(
            recipe,
            parents,
            engine_facts(recipe, frames=25 if shape == "region" else 105),
        ).value
        assert [op.claim for op in plan.edges[0].ops] == [claim, "generated", claim]
        assert plan.status == "resolved_unrendered"
        assert plan.edges[0].ops[0].render_buffer_id == (
            "parent_a" if shape == "region" else "engine"
        )
        assert not ({"fidelity", "clipping", "passed"} & plan.model_dump().keys())


def test_ac13_extend_edges_and_measured_output():
    for shape in ["region", "full"]:
        recipe, parents = captured("extend", at=7.0, shape=shape)
        plan = build(
            recipe,
            parents,
            engine_facts(recipe, frames=40 if shape == "region" else 110),
        ).value
        assert plan.output_frames == 110 and plan.output_duration_s == 11.0
        assert [op.op for op in plan.edges[0].ops] == ["keep", "append"]
        assert [op.dst for op in plan.edges[0].ops] == [(0, 70), (70, 110)]
        assert len(plan.pieces) == (2 if shape == "region" else 1)
    for at, expected in [(0.0, 40), (10.0, 140)]:
        recipe, parents = captured("extend", at=at)
        plan = build(recipe, parents, engine_facts(recipe, frames=40)).value
        assert plan.output_frames == expected
        assert len(plan.edges[0].ops) == (1 if at == 0.0 else 2)
    recipe, parents = captured("extend", at=7.0, shape="full")
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents, engine_facts(recipe, frames=70))
    assert error.value.code == "COMPOSITION_INTERVAL_COLLAPSED"
    for shape in ["region", "full"]:
        recipe, parents = captured("repaint", region=(0.0, 10.0), shape=shape)
        plan = build(recipe, parents, engine_facts(recipe, frames=25)).value
        assert plan.output_frames == 25 and len(plan.edges[0].ops) == 1


def test_ac11_engine_conversion_local_grid():
    for shape, native_frames, measured_frames, expected in [
        ("region", 40, 20, 100),
        ("full", 210, 105, 105),
    ]:
        recipe, parents = captured(
            "repaint",
            region=(6.0, 8.0) if shape == "region" else (2.0, 4.0),
            shape=shape,
        )
        engine = engine_facts(recipe, frames=native_frames, rate=20, channels=1)
        cf = conversion(recipe, parents, engine, measured_frames)
        plan = build(recipe, parents, engine, (cf,)).value
        assert plan.output_frames == expected
        assert plan.conversions[0].conversion_scope == (0, native_frames)
        assert len(plan.resolutions) == 2
        assert all(res.buffer_id == "parent_a" for res in plan.resolutions)
        if shape == "region":
            assert [piece.dst for piece in plan.pieces] == [
                (0, 60),
                (60, 80),
                (80, 100),
            ]
            assert plan.edges[0].ops[1].render_span == (0, 20)
        else:
            assert all(
                op.op == "convert" and op.conversion_id == "engine_to_target"
                for op in plan.edges[0].ops
            )
            assert [op.effect for op in plan.edges[0].ops] == ["keep", "regen", "keep"]
            assert plan.pieces[0].terms[0].span == (0, 105)


def test_ac17_pure_wrapper_boundary(monkeypatch):
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(c))
    imports = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(
        name
        and name.split(".")[0]
        in {
            "torch",
            "numpy",
            "subprocess",
            "sqlite3",
            "sqlalchemy",
            "soundfile",
            "pathlib",
            "os",
        }
        for name in imports
    )
    recipe, parents = captured()
    legitimate = build(recipe, parents).payload
    forged = r.CapturedRecipe(recipe.value, recipe.payload, "f" * 64)
    with pytest.raises(c.CompositionError) as error:
        build(forged, parents)
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"
    forged = r.CapturedRecipe(
        recipe.value.model_copy(update={"root_id": uid(99)}),
        recipe.payload,
        recipe.sha256,
    )
    with pytest.raises(c.CompositionError) as error:
        build(forged, parents)
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"
    monkeypatch.setattr(
        "builtins.open",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("I/O forbidden")),
    )
    assert build(recipe, parents).payload == legitimate


def test_ac18_sanitized_api_errors():
    recipe, parents = captured()
    secret = "/private/lyrics/token-secret-12345"
    wrong = (dict(parents[0], buffer=dict(parents[0]["buffer"], frames=secret)),)
    with pytest.raises(c.CompositionError) as error:
        build(recipe, wrong)
    assert error.value.code == "COMPOSITION_INVALID"
    assert str(error.value) == error.value.code and error.value.field is None
    assert error.value.__cause__ is None and error.value.__context__ is None
    assert secret not in repr(error.value)
    with pytest.raises(c.CompositionError) as error:
        c.round_frame(10**400, 10)
    assert error.value.__cause__ is None and error.value.__context__ is None


def test_ac16_codec_replay_rejects_tampered_plan():
    import copy

    recipe, parents = captured()
    plan = build(recipe, parents)
    assert c.composition_bytes(plan) == plan.payload == c.composition_bytes(plan.value)
    assert (
        c.composition_sha256(plan)
        == sha(plan.payload)
        == c.composition_sha256(plan.value)
    )
    restored = c.read_composition_plan(
        plan.payload, expected_sha256=plan.sha256, recipe=recipe
    )
    assert restored == plan
    assert (recipe.payload, recipe.sha256) == (
        r.read_recipe(
            recipe.payload, schema_version=1, expected_sha256=recipe.sha256
        ).payload,
        recipe.sha256,
    )
    base = plan.value.model_dump(mode="json")
    changes = [
        lambda d: d.update(output_frames=52),
        lambda d: d["resolutions"][0].update(frame=20),
        lambda d: d["pieces"][0].update(dst=[0, 50]),
        lambda d: d["edges"][0]["ops"][0].update(claim="transformed"),
        lambda d: d.update(extra="private-secret"),
        lambda d: d.update(schema_version=True),
        lambda d: d.update(kind="PostPlan"),
        lambda d: d["inputs"][0].update(root_id=uid(99)),
    ]
    for change in changes:
        data = copy.deepcopy(base)
        change(data)
        payload = wire(data)
        with pytest.raises(c.CompositionError):
            c.read_composition_plan(
                payload, expected_sha256=sha(payload), recipe=recipe
            )
    for payload in [
        plan.payload + b"\n",
        b'{"kind":"creative_composition","kind":"creative_composition"}',
        b"\xef\xbb\xbf" + plan.payload,
    ]:
        with pytest.raises(c.CompositionError):
            c.read_composition_plan(
                payload, expected_sha256=sha(payload), recipe=recipe
            )
    with pytest.raises(c.CompositionError) as error:
        c.read_composition_plan(plan.payload, expected_sha256="f" * 64, recipe=recipe)
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"


def test_ac05_sum_and_codec_limits():
    recipe, parents = captured("extend", at=10.0)
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents, engine_facts(recipe, frames=2**63 - 1))
    assert error.value.code == "COMPOSITION_LIMIT_EXCEEDED"
    for value in [
        {"items": [0] * 257},
        {
            "x": {
                "x": {
                    "x": {
                        "x": {
                            "x": {
                                "x": {
                                    "x": {
                                        "x": {
                                            "x": {
                                                "x": {
                                                    "x": {
                                                        "x": {
                                                            "x": {
                                                                "x": {
                                                                    "x": {
                                                                        "x": {
                                                                            "x": {
                                                                                "x": {
                                                                                    "x": {
                                                                                        "x": {
                                                                                            "x": {
                                                                                                "x": 1
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "x" * (1024 * 1024 + 1),
    ]:
        payload = wire(value)
        with pytest.raises(c.CompositionError) as error:
            c.read_composition_plan(
                payload, expected_sha256=sha(payload), recipe=recipe
            )
        assert error.value.code == "COMPOSITION_LIMIT_EXCEEDED"
    facts = c.BufferFacts(**buffer(frames=2**63 - 1, rate=1))
    assert c.resolve_region((0.0, facts.duration_s), facts) == (0, 2**63 - 1)


def test_ac16_dto_global_invariants():
    import copy

    recipe, parents = captured("crossfade", b_rate=20, b_channels=1, duration=8.0)
    plan = build(recipe, parents, converted=(conversion(recipe, parents),)).value
    good = plan.model_dump(mode="json")
    changes = [
        lambda d: d.update(output_duration_s=10.2),
        lambda d: d.update(schema_version=True),
        lambda d: d["pieces"][0]["terms"][0].update(span=[0, 21]),
        lambda d: d["pieces"][1].update(kind="copy"),
        lambda d: d["pieces"][1]["terms"][0].update(envelope="linear_in"),
        lambda d: d["edges"][1]["ops"][1].update(src=[159, 160]),
        lambda d: d["edges"][1]["ops"][1].update(nominal_src=[161, 161]),
        lambda d: d["edges"][1]["ops"][1].update(
            op="keep", effect=None, conversion_id=None
        ),
        lambda d: d["edges"][0]["ops"][0].update(nominal_src=[0, 1]),
        lambda d: d["edges"][1].update(source_frames=161),
        lambda d: d["pieces"][0].update(dst=[1, 21]),
        lambda d: d["edges"][0]["ops"][0].update(render_span=[0, 101]),
    ]
    for change in changes:
        data = copy.deepcopy(good)
        change(data)
        with pytest.raises((c.CompositionError, ValidationError)):
            c.CompositionPlanV1.model_validate(data)


def test_ac02_signed_zero_wrapper_is_exact():
    recipe, parents = captured(region=(-0.0, 2.0))
    assert b"-0.0" in recipe.payload
    plan = build(recipe, parents)
    assert plan.value.resolutions[0].seconds_decimal == "-0.0"
    altered_op = recipe.value.operation.model_copy(update={"region": (0.0, 2.0)})
    forged = r.CapturedRecipe(
        recipe.value.model_copy(update={"operation": altered_op}),
        recipe.payload,
        recipe.sha256,
    )
    with pytest.raises(c.CompositionError) as error:
        build(forged, parents)
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"


def test_ac05_preflight_limits_before_context():
    recipe, parents = captured()
    assert c.conversion_requirements(recipe, parents=parents, engine=None) == ()
    with pytest.raises(c.CompositionError) as error:
        c.conversion_requirements(recipe, parents=parents * 257, engine=None)
    assert error.value.code == "COMPOSITION_LIMIT_EXCEEDED"


@pytest.mark.parametrize(
    "region",
    [
        (1.0, 1.0),
        (2.0, 1.0),
        (-1.0, 1.0),
        (0.0, 11.0),
        (True, 2.0),
        ("0", 2.0),
        (0.0, float("nan")),
        (0.0, float("inf")),
        (0.0, Decimal(2)),
        [0.0, 2.0],
    ],
)
def test_ac01_region_negatives_paired(region):
    facts = c.BufferFacts(**buffer())
    assert c.resolve_region((2.05, 7.15), facts) == (21, 72)
    with pytest.raises(c.CompositionError):
        c.resolve_region(region, facts)


@pytest.mark.parametrize(
    "kind",
    [
        "trim",
        "fade",
        "crossfade",
        "extend",
        "repaint",
        "variation_audio",
        "variation_request",
        "cover",
    ],
)
def test_ac16_replay_every_operation(kind):
    recipe, parents = captured(kind)
    engine = None if kind in {"trim", "fade", "crossfade"} else engine_facts(recipe)
    plan = build(recipe, parents, engine)
    assert (
        c.read_composition_plan(
            plan.payload, expected_sha256=plan.sha256, recipe=recipe
        )
        == plan
    )


def test_ac08_roots_are_original_roots():
    recipe, parents = captured("crossfade")
    data = recipe.value.model_dump(mode="json")
    data["root_id"] = uid(1)
    data["parents"][0]["root_id"] = uid(3)
    data["parents"][1]["root_id"] = uid(1)
    recipe = r.capture_recipe(data)
    parents = (dict(parents[0], root_id=uid(3)), dict(parents[1], root_id=uid(1)))
    plan = build(recipe, parents).value
    assert plan.root_id == uid(1) != min(p["parent_id"] for p in parents)
    assert [e.role for e in plan.edges] == ["crossfade_a", "crossfade_b"]


@pytest.mark.parametrize(
    "bad",
    ["format", "duration", "engine_id", "extra", "empty", "duplicates", "wrong_tuple"],
)
def test_ac06_binding_negatives_paired(bad):
    recipe, parents = captured()
    assert build(recipe, parents).value.output_frames == 51
    p = dict(parents[0])
    if bad == "format":
        p["buffer"] = buffer(rate=20, frames=200)
    elif bad == "duration":
        p["buffer"] = buffer(frames=99)
    elif bad == "engine_id":
        p["buffer"] = buffer("engine")
    elif bad == "extra":
        p["path"] = "secret-path"
    supplied = (
        ()
        if bad == "empty"
        else (p, p)
        if bad == "duplicates"
        else [p]
        if bad == "wrong_tuple"
        else (p,)
    )
    with pytest.raises(c.CompositionError) as error:
        build(recipe, supplied)
    assert error.value.__context__ is None and error.value.__cause__ is None


@pytest.mark.parametrize(
    "bad",
    [
        "scope_empty",
        "scope_partial",
        "evidence_missing",
        "requirement_pin",
        "wrong_id",
        "wrong_hash",
        "extra_conversion",
        "wrong_type",
        "frames_boolean",
    ],
)
def test_ac09_conversion_negatives_paired(bad):
    recipe, parents = captured("crossfade", b_rate=20, b_channels=1)
    cf = conversion(recipe, parents)
    assert (
        build(recipe, parents, converted=(cf,)).value.conversions[0].buffer.frames == 81
    )
    if bad == "scope_empty":
        cf["conversion_scope"] = (0, 0)
    elif bad == "scope_partial":
        cf["conversion_scope"] = (1, 160)
    elif bad == "evidence_missing":
        cf.pop("evidence")
    elif bad in {"requirement_pin", "wrong_hash"}:
        req = cf["requirement"].model_dump(mode="json")
        if bad == "requirement_pin":
            req["tool"]["revision"] = "changed"
        else:
            req["input_sha256"] = "f" * 64
        cf["requirement"] = req
    elif bad == "wrong_id":
        cf["buffer"]["buffer_id"] = "engine"
    elif bad == "frames_boolean":
        cf["buffer"]["frames"] = True
    converted = (
        (cf, cf)
        if bad == "extra_conversion"
        else [cf]
        if bad == "wrong_type"
        else (cf,)
    )
    with pytest.raises(c.CompositionError):
        build(recipe, parents, converted=converted)


@pytest.mark.parametrize(
    "kind,kwargs",
    [
        ("fade", {"incoming": 0.1, "outgoing": None}),
        ("crossfade", {"duration": 0.1}),
        ("crossfade", {"duration": 0.01}),
        ("trim", {"region": (0.01, 0.02)}),
    ],
)
def test_ac03_plan_collapses_paired(kind, kwargs):
    good, good_parents = captured(kind)
    assert build(good, good_parents).value.output_frames > 0
    recipe, parents = captured(kind, **kwargs)
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents)
    assert error.value.code in {
        "COMPOSITION_INTERVAL_COLLAPSED",
        "COMPOSITION_ENVELOPE_TOO_SHORT",
    }


@pytest.mark.parametrize(
    "incoming,outgoing", [(4.96, 5.04), (10.0, None), (None, 10.0), (None, 2.05)]
)
def test_ac01_fade_empty_center_omitted(incoming, outgoing):
    recipe, parents = captured("fade", incoming=incoming, outgoing=outgoing)
    plan = build(recipe, parents).value
    assert plan.output_frames == 100
    assert all(p.dst[0] < p.dst[1] for p in plan.pieces)
    assert sum(p.dst[1] - p.dst[0] for p in plan.pieces) == 100


@pytest.mark.parametrize(
    "payload",
    [
        b"[]",
        b"{",
        b"null",
        b'{"schema_version":1,"kind":"creative_composition","x":NaN}',
        b"\xff",
        b'{"kind":"creative_composition","schema_version":1.0}',
        b'{"kind":"creative_composition","schema_version":0}',
    ],
)
def test_ac16_bad_wire_sanitized(payload):
    recipe, parents = captured()
    plan = build(recipe, parents)
    assert (
        c.read_composition_plan(
            plan.payload, expected_sha256=plan.sha256, recipe=recipe
        )
        == plan
    )
    with pytest.raises(c.CompositionError) as error:
        c.read_composition_plan(payload, expected_sha256=sha(payload), recipe=recipe)
    assert str(error.value) == error.value.code and error.value.__context__ is None


@pytest.mark.parametrize(
    "rate,channels,channel_policy,resample_policy",
    [
        (10, 1, "mono_to_stereo_duplicate", "identity"),
        (20, 2, "identity", "soxr_pinned"),
        (10, 2, None, None),
    ],
)
def test_ac10_conversion_policies(rate, channels, channel_policy, resample_policy):
    recipe, parents = captured("crossfade", b_rate=rate, b_channels=channels)
    requirements = c.conversion_requirements(recipe, parents=parents, engine=None)
    if channel_policy is None:
        assert requirements == ()
        plan = build(recipe, parents)
    else:
        assert requirements[0].channel_policy == channel_policy
        assert requirements[0].resample_policy == resample_policy
        plan = build(recipe, parents, converted=(conversion(recipe, parents),))
    assert (
        c.read_composition_plan(
            plan.payload, expected_sha256=plan.sha256, recipe=recipe
        )
        == plan
    )


def test_ac10_stereo_to_mono_policy():
    recipe, parents = captured("crossfade")
    data = recipe.value.model_dump(mode="json")
    data["parents"][0]["asset"]["channels"] = 1
    data["executor"]["output_format"]["channels"] = 1
    recipe = r.capture_recipe(data)
    parents = (dict(parents[0], buffer=buffer(channels=1)), parents[1])
    requirement = c.conversion_requirements(recipe, parents=parents, engine=None)[0]
    assert (
        requirement.channel_policy == "stereo_to_mono_average"
        and requirement.resample_policy == "identity"
    )


def test_ac18_missing_measurement_is_facts_required():
    recipe, parents = captured("crossfade", b_rate=20, b_channels=1)
    cf = conversion(recipe, parents)
    assert build(recipe, parents, converted=(cf,)).value.output_frames == 160
    for missing in ["evidence", "measurement"]:
        absent = dict(cf)
        absent["buffer"] = dict(cf["buffer"])
        if missing == "evidence":
            absent.pop("evidence")
        else:
            absent["buffer"].pop("measurement")
        with pytest.raises(c.CompositionError) as error:
            build(recipe, parents, converted=(absent,))
        assert error.value.code == "COMPOSITION_FACTS_REQUIRED"


def test_ac04_resolve_revalidates_facts():
    good = c.BufferFacts(**buffer())
    assert c.resolve_region((0.0, 1.0), good) == (0, 10)
    for bad in [
        good.model_copy(update={"frames": True}),
        good.model_copy(update={"duration_s": 11.0}),
    ]:
        with pytest.raises(c.CompositionError):
            c.resolve_region((0.0, 1.0), bad)


def test_ac05_numeric_dto_overflow_code():
    recipe, parents = captured()
    assert build(recipe, parents).value.output_frames == 51
    for field, value in [
        ("frames", 2**63),
        ("format", {"sample_rate": 2**31, "channels": 2}),
    ]:
        altered = (
            dict(parents[0], buffer=dict(parents[0]["buffer"], **{field: value})),
        )
        with pytest.raises(c.CompositionError) as error:
            build(recipe, altered)
        assert error.value.code == "COMPOSITION_LIMIT_EXCEEDED"


def test_ac14_map_sources_follow_claims():
    import copy

    recipe, parents = captured("repaint", region=(2.0, 4.0))
    plan = build(recipe, parents, engine_facts(recipe)).value
    data = plan.model_dump(mode="json")
    changed = copy.deepcopy(data)
    changed["edges"][0]["ops"][1].update(
        render_buffer_id="parent_a", render_span=[0, 25]
    )
    with pytest.raises((c.CompositionError, ValidationError)):
        c.CompositionPlanV1.model_validate(changed)
    changed = copy.deepcopy(data)
    changed["edges"][0]["ops"][0].update(
        op="fade",
        claim="transformed",
        envelope="linear_in",
        render_buffer_id="engine",
        render_span=[0, 20],
    )
    with pytest.raises((c.CompositionError, ValidationError)):
        c.CompositionPlanV1.model_validate(changed)


def test_ac09_no_pin_no_conversion_and_extra_facts():
    recipe, parents = captured("crossfade", b_rate=20, b_channels=1)
    assert (
        c.conversion_requirements(recipe, parents=parents, engine=None)[0].tool.tool_id
        == "ffmpeg"
    )
    data = recipe.value.model_dump(mode="json")
    data["executor"]["tools"][0]["tool_id"] = "decoder"
    without_pin = r.capture_recipe(data)
    with pytest.raises(c.CompositionError) as error:
        c.conversion_requirements(without_pin, parents=parents, engine=None)
    assert error.value.code == "COMPOSITION_FACTS_REQUIRED"
    extra = conversion(recipe, parents)
    ordinary, ordinary_parents = captured("crossfade")
    with pytest.raises(c.CompositionError) as error:
        build(ordinary, ordinary_parents, converted=(extra,))
    assert error.value.code == "COMPOSITION_INVALID"


def test_ac16_closed_wire_collections_and_spans():
    import copy

    recipe, parents = captured()
    plan = build(recipe, parents)
    original = plan.value.model_dump(mode="json")
    for field, bad in [
        ("dst", [0, 0]),
        ("src", [30, 20]),
        ("nominal_src", [21, 72]),
        ("render_span", [0, 0]),
    ]:
        data = copy.deepcopy(original)
        data["edges"][0]["ops"][0][field] = bad
        payload = wire(data)
        with pytest.raises(c.CompositionError):
            c.read_composition_plan(
                payload, expected_sha256=sha(payload), recipe=recipe
            )
    for value in [object(), {}, "private-token"]:
        with pytest.raises(c.CompositionError):
            c.composition_bytes(value)
    tampered = c.CapturedCompositionPlan(plan.value, plan.payload + b"\n", plan.sha256)
    with pytest.raises(c.CompositionError) as error:
        c.composition_bytes(tampered)
    assert error.value.code == "COMPOSITION_HASH_MISMATCH"


@pytest.mark.parametrize("shape", ["full", "region"])
def test_ac12_extend_converted_shape_once(shape):
    recipe, parents = captured("extend", shape=shape)
    engine = engine_facts(recipe, 80 if shape == "region" else 220, rate=20)
    cf = conversion(recipe, parents, engine, 40 if shape == "region" else 110)
    plan = build(recipe, parents, engine, (cf,))
    assert plan.value.output_frames == 110 and plan.value.output_duration_s == 11.0
    assert len(plan.value.pieces) == (2 if shape == "region" else 1)
    assert plan.value.edges[0].ops[-1].op == "convert"
    assert plan.value.edges[0].ops[-1].effect == "append"
    assert plan.value.edges[0].ops[-1].render_span == (
        (0, 40) if shape == "region" else (70, 110)
    )
    assert (
        c.read_composition_plan(
            plan.payload, expected_sha256=plan.sha256, recipe=recipe
        )
        == plan
    )


def test_ac01_fade_sum_exceeds_frames_after_rounding():
    recipe, parents = captured("fade", incoming=4.95, outgoing=5.05)
    assert recipe.value.operation.fade_in_s + recipe.value.operation.fade_out_s == 10.0
    assert parents[0]["buffer"]["frames"] == 100
    assert parents[0]["buffer"]["format"]["sample_rate"] == 10
    assert (c.round_frame(4.95, 10), c.round_frame(5.05, 10)) == (50, 51)
    with pytest.raises(c.CompositionError) as error:
        build(recipe, parents)
    assert error.value.code == "COMPOSITION_OUT_OF_BOUNDS"
    assert str(error.value) == "COMPOSITION_OUT_OF_BOUNDS"
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_ac01_fade_sum_exact_frames_after_rounding():
    recipe, parents = captured("fade", incoming=4.96, outgoing=5.04)
    assert (c.round_frame(4.96, 10), c.round_frame(5.04, 10)) == (50, 50)
    plan = build(recipe, parents).value
    assert (plan.output_frames, plan.output_duration_s) == (100, 10.0)
    assert [(r.key, r.frame) for r in plan.resolutions] == [
        ("fade_in_length", 50),
        ("fade_out_length", 50),
    ]
    assert [p.kind for p in plan.pieces] == ["fade", "fade"]
    assert [p.dst for p in plan.pieces] == [(0, 50), (50, 100)]
    assert [p.terms[0].span for p in plan.pieces] == [(0, 50), (50, 100)]
    assert [p.terms[0].envelope for p in plan.pieces] == ["linear_in", "linear_out"]
    assert [o.op for o in plan.edges[0].ops] == ["fade", "fade"]
    assert [o.src for o in plan.edges[0].ops] == [(0, 50), (50, 100)]
    assert [o.dst for o in plan.edges[0].ops] == [(0, 50), (50, 100)]
    assert [o.envelope for o in plan.edges[0].ops] == ["linear_in", "linear_out"]
