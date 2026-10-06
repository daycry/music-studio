"""Controles SFT y Turbo, sin importar torch ni cargar pesos."""

from types import SimpleNamespace

import pytest
from jsonschema import ValidationError, validate
from test_adapter import module


def request(**params):
    return {
        "task": "music.instrumental",
        "params": {"style": "synthetic", "duration_s": 30, **params},
        "seed": 1,
        "n_outputs": 1,
    }


def test_descriptor_sft_identity_and_limits():
    desc = module("descriptor").descriptor(checkpoint="acestep-v15-sft")
    assert desc.id == "ace-step-1.5-sft"
    assert all(not task.verified for task in desc.tasks.values())
    schema = desc.tasks["music.instrumental"].params_schema
    assert schema["properties"]["inference_steps"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 200,
    }
    assert schema["properties"]["guidance_scale"] == {
        "type": "number",
        "minimum": 1,
        "maximum": 20,
    }
    validate(request(inference_steps=50, guidance_scale=7)["params"], schema)
    turbo = module("descriptor").descriptor()
    assert turbo.id == "ace-step-1.5-turbo"
    schema = turbo.tasks["music.instrumental"].params_schema
    assert schema["properties"]["inference_steps"]["maximum"] == 8
    assert "guidance_scale" not in schema["properties"]
    with pytest.raises(ValidationError):
        validate(request(guidance_scale=7)["params"], schema)


def test_factory_sft_identity(monkeypatch, tmp_path):
    from engine_common import CpuGpu
    from fastapi.testclient import TestClient

    monkeypatch.setenv("STUDIO_ACESTEP_CHECKPOINT", "acestep-v15-sft")
    app = module("engine_acestep").create_app(
        token="test", data_dir=tmp_path, gpu=CpuGpu()
    )
    with TestClient(app) as client:
        models = client.get(
            "/v1/models", headers={"X-Studio-Engine-Token": "test"}
        ).json()
    assert models[0]["id"] == "ace-step-1.5-sft"


def test_adapter_sft_load_identity():
    from engine_common import EngineError

    model = module("adapter").AceStepAdapter(checkpoint="acestep-v15-sft")
    with pytest.raises(EngineError, match="VRAM_EXCEEDED"):
        model.load("ace-step-1.5-sft", "bf16", 0, 100)
    with pytest.raises(EngineError, match="MODEL_NOT_FOUND"):
        model.load("ace-step-1.5-turbo", "bf16", 0, 100)


@pytest.mark.parametrize(
    "checkpoint,steps,cfg",
    [
        ("acestep-v15-turbo", 8, 7.0),
        ("acestep-v15-sft", 50, 7.0),
    ],
)
def test_effective_defaults(checkpoint, steps, cfg):
    adapter = module("adapter")
    # Identidad explícita del request /v1, también sin HTTP.
    req = request()
    req["model_id"] = module("descriptor").model_id(checkpoint)
    params, _ = adapter.generation_options(req, 0)
    assert params.get("inference_steps") == steps
    assert params.get("guidance_scale") == cfg


@pytest.mark.parametrize(
    "model,params",
    [
        ("ace-step-1.5-turbo", {"inference_steps": 9}),
        ("ace-step-1.5-sft", {"inference_steps": 201}),
        ("ace-step-1.5-sft", {"inference_steps": True}),
        ("ace-step-1.5-sft", {"inference_steps": 2.5}),
        ("ace-step-1.5-sft", {"inference_steps": None}),
        ("ace-step-1.5-sft", {"inference_steps": 0}),
        ("ace-step-1.5-turbo", {"guidance_scale": 7}),
        ("ace-step-1.5-sft", {"guidance_scale": float("nan")}),
        ("ace-step-1.5-sft", {"guidance_scale": float("inf")}),
        ("ace-step-1.5-sft", {"guidance_scale": True}),
        ("ace-step-1.5-sft", {"guidance_scale": 0}),
        ("ace-step-1.5-sft", {"guidance_scale": 21}),
        ("ace-step-1.5-sft", {"guidance_scale": "7"}),
        ("ace-step-1.5-sft", {"guidance_scale": 10**400}),
    ],
)
def test_direct_invalid_controls(model, params):
    from engine_common import EngineError

    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        module("adapter").generation_options(
            {**request(**params), "model_id": model}, 0
        )


def test_generation_effective_steps_and_cancellation(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from engine_common.runtime import CancelToken, EngineError

    adapter = module("adapter")
    monkeypatch.setattr(adapter, "preflight", lambda *a, **k: {})
    observed = []

    @contextmanager
    def hooks(runtime, token, progress, total):
        observed.append(total)
        yield

    monkeypatch.setattr(adapter, "step_hooks", hooks)
    token = CancelToken()

    def run(dit, lm, params, config, **kwargs):
        observed.append((params.inference_steps, params.guidance_scale))
        token.cancel()
        return SimpleNamespace(success=False)

    model = adapter.AceStepAdapter(checkpoint="acestep-v15-sft")
    model.runtime = SimpleNamespace(
        dit=None,
        lm=None,
        GenerationParams=lambda **kw: SimpleNamespace(**kw),
        GenerationConfig=lambda **kw: kw,
        generate_music=run,
    )
    with pytest.raises(EngineError, match="CANCELLED"):
        model.generate(
            request(inference_steps=23, guidance_scale=4),
            tmp_path,
            lambda e: None,
            token,
        )
    assert observed == [23, (23, 4)]


@pytest.mark.parametrize(
    "params,steps,cfg",
    [({}, 50, 7), ({"inference_steps": 35, "guidance_scale": 4}, 35, 4)],
)
def test_native_sft_effective_receipt(params, steps, cfg):
    from pathlib import Path

    class Tokenizer:
        def __call__(self, text, **kwargs):
            assert kwargs == {"truncation": False}
            return {"input_ids": [1, 2, 3]}

        def apply_chat_template(self, messages, **kwargs):
            return str(messages)

    req = {**request(**params), "model_id": "ace-step-1.5-sft"}
    source = (
        Path(__file__).resolve().parents[4] / ".cache/dev-cycle/t17/upstream-acestep"
    )
    receipt = module("preflight").native_plan(req, Tokenizer(), Tokenizer(), source)
    assert receipt["effective"]["inference_steps"] == steps
    assert receipt["effective"]["guidance_scale"] == cfg
    assert receipt["effective"]["params"]["inference_steps"] == steps


def test_dit_boundary_rejects_inference_drift():
    from engine_common import EngineError

    seen = []
    values = {
        "caption": "synthetic",
        "lyrics": "[Instrumental]",
        "vocal_language": "unknown",
        "duration": 30,
        "bpm": None,
        "keyscale": "",
        "inference_steps": 50,
        "guidance_scale": 7,
    }
    kwargs = {
        "captions": values["caption"],
        "lyrics": values["lyrics"],
        "vocal_language": "unknown",
        "audio_duration": 30,
        "bpm": None,
        "key_scale": "",
        "time_signature": "",
        "inference_steps": 8,
        "guidance_scale": 7,
    }
    runtime = SimpleNamespace(
        lm=None, dit=SimpleNamespace(generate_music=lambda **kw: seen.append(kw))
    )
    adapter = module("adapter")
    with (
        adapter.input_capture(runtime, {}, values, 0),
        pytest.raises(EngineError, match="INVALID_PARAMS"),
    ):
        runtime.dit.generate_music(**kwargs)
    assert seen == []
