"""Shift opcional: validación y propagación CPU sin pesos ni GPU."""

from types import SimpleNamespace

import pytest
from jsonschema import ValidationError, validate
from test_adapter import module


def request(shift=None):
    params = {"style": "synthetic", "duration_s": 30}
    if shift is not None:
        params["shift"] = shift
    return {"task": "music.instrumental", "params": params, "seed": 1, "n_outputs": 1}


def test_descriptor_shift_optional():
    desc = module("descriptor").descriptor()
    for name, task in desc.tasks.items():
        schema = task.params_schema
        assert schema["properties"]["shift"] == {
            "type": "number",
            "minimum": 1,
            "maximum": 5,
        }
        assert schema["required"] == ["style", "duration_s"] + (
            ["lyrics", "language"] if name == "music.song" else []
        )
        assert not task.verified
        assert all(not feature.verified for feature in task.features.values())
    schema = desc.tasks["music.instrumental"].params_schema
    for value in [1, 3, 5, 2.5]:
        validate(request(value)["params"], schema)
    for value in [0, 6, float("inf"), float("-inf"), True, "3", None]:
        with pytest.raises(ValidationError):
            validate({**request()["params"], "shift": value}, schema)


@pytest.mark.parametrize("value", [1, 3, 5, 2.5])
def test_adapter_propagates_shift(value):
    values, _ = module("adapter").generation_options(request(value), 0)
    assert values["shift"] == value


@pytest.mark.parametrize(
    "value",
    [
        0,
        6,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        "3",
        None,
        10**400,
        -(10**400),
    ],
    ids=[
        "zero",
        "six",
        "nan",
        "inf",
        "negative-inf",
        "bool",
        "string",
        "null",
        "huge-positive",
        "huge-negative",
    ],
)
def test_adapter_rejects_invalid_shift(value):
    from engine_common import EngineError

    invalid = request()
    invalid["params"]["shift"] = value
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        module("adapter").generation_options(invalid, 0)


def test_adapter_omission_preserves_upstream_default():
    values, _ = module("adapter").generation_options(request(), 0)
    assert values.get("shift", 1) == 1


def test_shift_reaches_generation_params(tmp_path, monkeypatch):
    from engine_common.runtime import CancelToken

    adapter = module("adapter")
    model = adapter.AceStepAdapter()
    captured = []
    native_calls = []

    def token_preflight(variant, **kwargs):
        native_calls.append((variant, kwargs))
        return {"kind": "planned", "request_sha256": adapter.digest(variant)}

    # Runtime sintético: la medición nativa real se cubre en test_preflight.
    monkeypatch.setattr(adapter, "preflight", token_preflight)

    def generate_music(dit, lm, params, config, **kwargs):
        captured.append(params.shift)
        return SimpleNamespace(
            success=True, audios=[{"tensor": None, "sample_rate": 48000}]
        )

    model.runtime = SimpleNamespace(
        dit=SimpleNamespace(),
        lm=SimpleNamespace(),
        GenerationParams=lambda **kwargs: SimpleNamespace(**kwargs),
        GenerationConfig=lambda **kwargs: SimpleNamespace(**kwargs),
        generate_music=generate_music,
        torch=SimpleNamespace(cuda=SimpleNamespace(max_memory_allocated=lambda: 0)),
    )
    monkeypatch.setattr(adapter, "write_wav", lambda *args: None)
    model.generate(request(3), tmp_path, lambda event: None, CancelToken())
    assert captured == [3]
    assert len(native_calls) == 1
    assert native_calls[0][0]["seed"] == 1
    assert native_calls[0][0]["n_outputs"] == 1
    assert native_calls[0][0]["params"]["shift"] == 3
    assert native_calls[0][1]["checkpoint"] == model.checkpoint
