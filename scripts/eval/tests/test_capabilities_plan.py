"""Contrato CPU de la matriz; ausencia funcional también falla por comportamiento."""

import importlib
import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.eval.capabilities import load_text
from scripts.eval.capabilities_native import native_values


def module():
    name = "scripts.eval.capabilities_plan"
    if importlib.util.find_spec(name) is None:
        return type("Missing", (), {"matrix": staticmethod(list)})()
    return importlib.import_module(name)


INSTRUMENTAL_ROWS = [r for r in module().matrix() if r["case"] == "music.instrumental"]


@pytest.mark.parametrize(
    "row",
    INSTRUMENTAL_ROWS,
    ids=lambda r: f"{r['profile']}-{r['surface']}-{r['seed']}",
)
def test_instrumental_request_uses_dedicated_sealed_caption_and_lyrics(row):
    root = Path(__file__).resolve().parents[3]
    fixture = load_text(root / "data/inputs/t10-capabilities/original-text-v1")
    before = deepcopy(fixture)
    assert "lead vocals" in fixture["style"]
    assert "No vocals, speech or humming" in fixture["instrumental_style"]
    request = module().request_for(row, fixture)
    assert request["params"]["style"] == fixture["instrumental_style"]
    assert request["params"]["lyrics"] == "[Instrumental]"
    assert request["task"] == "music.instrumental"
    assert request["seed"] == row["seed"]
    assert request["params"]["language"] == "es"
    assert request["params"]["inference_steps"] == row["inference_steps"]
    assert request["params"]["shift"] == row["shift"]
    if row["profile"] == "turbo":
        assert "guidance_scale" not in request["params"]
    else:
        assert request["params"]["guidance_scale"] == row["guidance_scale"]
    values = native_values(row, request, fixture)
    assert values["caption"] == fixture["instrumental_style"]
    assert values["lyrics"] == "[Instrumental]" and values["instrumental"] is True
    assert values["thinking"] is True and values["lm_cfg_scale"] == 2.0
    assert values["vocal_language"] == "es"
    assert not any(
        values[k]
        for k in (
            "enable_normalization",
            "use_cot_metas",
            "use_cot_caption",
            "use_cot_language",
        )
    )
    assert fixture == before


@pytest.mark.parametrize("caption", [None, "", " \n\t", 3, [], {}])
def test_instrumental_request_rejects_missing_or_malformed_caption(caption):
    fixture = {"style": "Lead vocals singing", "lyrics": "[Verse]\nSing this"}
    if caption is not None:
        fixture["instrumental_style"] = caption
    with pytest.raises(ValueError, match="instrumental_style_prerequisite"):
        module().request_for(INSTRUMENTAL_ROWS[0], fixture)


@pytest.mark.parametrize(
    "case",
    [c for c in module().OPERATIONS + module().FEATURES if c != "music.instrumental"],
)
def test_other_cases_preserve_song_text_and_feature_controls(case):
    fixture = {
        "style": "Lead vocals singing\n",
        "lyrics": "[Verse]\nCanción original\n",
        "references": {
            "A": {"path": "data/inputs/a.wav"},
            "B": {"path": "data/inputs/b.wav"},
        },
        "lora": {"path": "own-lora"},
    }
    before = deepcopy(fixture)
    for row in module().matrix():
        if row["case"] != case:
            continue
        request = module().request_for(row, fixture)
        assert request["params"]["style"] == fixture["style"]
        assert request["params"]["lyrics"] == fixture["lyrics"]
        for name in ("negative_prompt", "bpm", "key"):
            if name in row["control"] and row["control"][name] is not None:
                assert request["params"][name] == row["control"][name]
        if case == "lora":
            assert request["params"]["lora"] == "own-lora"
    assert fixture == before


def test_matrix_contains_all_cases_surfaces_controls_and_profiles():
    rows = module().matrix()
    cases = {r["case"] for r in rows}
    assert cases == {
        "music.song",
        "music.instrumental",
        "music.retake",
        "music.extend",
        "music.repaint",
        "music.cover",
        "music.complete",
        "audio.stems",
        "negative_prompt",
        "bpm",
        "key",
        "timbre_ref",
        "lora",
    }
    assert {r["surface"] for r in rows} == {"v1", "native_lab"}
    assert {r["profile"] for r in rows} == {"turbo", "sft", "base"}
    assert all(r["verdict"] is None and not r["verified"] for r in rows)
    native = [r for r in rows if r["surface"] == "native_lab"]
    assert {
        r["control"]["track_name"] for r in native if r["case"] == "audio.stems"
    } == {"vocals", "drums", "bass", "guitar"}
    extend = next(r for r in native if r["case"] == "music.extend")
    assert extend["control"] == {
        "pad_s": 30,
        "repainting_start": 60,
        "repainting_end": 90,
    }
    assert {
        r["control"]["retake_variance"] for r in native if r["case"] == "music.retake"
    } == {0, 0.2}
