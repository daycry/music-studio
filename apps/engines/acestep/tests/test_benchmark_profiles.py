"""Identidad y opciones medibles del benchmark; dobles CPU, sin GPU."""

from types import SimpleNamespace

import pytest
from test_adapter import module


@pytest.mark.parametrize(
    "checkpoint,identity,steps,cfg",
    [
        ("acestep-v15-base", "ace-step-1.5-base", 32, True),
        ("acestep-v15-xl-turbo", "ace-step-1.5-xl-turbo", 8, False),
    ],
)
def test_profiles_preserve_identity_and_controls(checkpoint, identity, steps, cfg):
    descriptor = module("descriptor")
    assert descriptor.model_id(checkpoint) == identity
    desc = descriptor.descriptor(checkpoint=checkpoint)
    assert desc.id == identity
    assert not any(task.verified for task in desc.tasks.values())
    schema = desc.tasks["music.instrumental"].params_schema["properties"]
    assert ("guidance_scale" in schema) == cfg
    request = {
        "task": "music.instrumental",
        "model_id": identity,
        "params": {"style": "test", "duration_s": 30},
        "seed": 1,
        "n_outputs": 1,
    }
    values, _ = module("adapter").generation_options(request, 0, checkpoint)
    assert values["inference_steps"] == steps
    assert values["guidance_scale"] == 7


def test_unknown_checkpoint_cannot_alias_turbo():
    with pytest.raises(Exception, match="MODEL_NOT_FOUND"):
        module("descriptor").model_id("unknown")


def test_int8_options_require_effective_offload():
    options = module("adapter").load_options("offload-int8", "acestep-v15-xl-turbo")
    assert options["quantization"] == "int8_weight_only"
    assert options["offload_to_cpu"] and options["offload_dit_to_cpu"]
    assert not options["compile_model"]


def test_int8_downgrade_is_rejected_and_only_decoder_counts():
    adapter = module("adapter")
    assert callable(getattr(adapter, "verify_int8_runtime", None)), (
        "Falta guarda INT8 efectiva"
    )
    runtime = SimpleNamespace(dit=SimpleNamespace(quantization=None))
    with pytest.raises(Exception, match="INTERNAL"):
        adapter.verify_int8_runtime(runtime)


def test_direct_clock_synchronizes_without_subtracting_load():
    adapter = module("adapter")
    assert callable(getattr(adapter, "timed_generation", None)), "Falta reloj directo"
    events = []
    stamps = iter((10_000_000_000, 12_000_000_000))
    cuda = SimpleNamespace(synchronize=lambda: events.append("sync"))
    result, timing = adapter.timed_generation(
        SimpleNamespace(torch=SimpleNamespace(cuda=cuda)),
        lambda: events.append("generate") or "result",
        clock=lambda: next(stamps),
    )
    assert result == "result" and events == ["sync", "generate", "sync"]
    assert timing["inference_s"] == 2
    assert timing["cuda_sync"] is True
    assert timing["infer_start_ns"] == 10_000_000_000


def test_resource_root_reaches_adapter_and_factory(monkeypatch, tmp_path):
    adapter = module("adapter")
    import inspect

    assert "resource_root" in inspect.signature(adapter.AceStepAdapter).parameters, (
        "Falta raíz efectiva"
    )
    selected = tmp_path / "models"
    model = adapter.AceStepAdapter(resource_root=selected)
    assert model.checkpoints == selected / "ace-step-1.5/checkpoints"


def test_xl_silence_latent_is_audited_safetensors():
    components = module("descriptor").locked_model()["components"]
    xl = next(c for c in components if c["id"] == "acestep-v15-xl-turbo")
    latent = next(f for f in xl["files"] if f["path"] == "silence_latent.pt")
    assert latent["format"] == "pickle", "XL no clasifica su entrada pickle"
    assert latent["converted"]["dest"] == "silence_latent.safetensors"
    turbo = next(c for c in components if c["id"] == "acestep-v15-turbo")
    audited = next(f for f in turbo["files"] if f["path"] == latent["path"])
    assert latent["sha256"] == audited["sha256"]
    assert latent["converted"] == audited["converted"]


def test_each_warm_run_resets_peak_and_cold_preserves_load_peak(monkeypatch, tmp_path):
    import numpy as np
    from engine_common.runtime import CancelToken

    adapter = module("adapter")
    monkeypatch.setattr(adapter, "preflight", lambda *args, **kwargs: {})
    peak = [1000 * 1024**2]
    reset_calls = []

    def reset():
        reset_calls.append(True)
        peak[0] = 100 * 1024**2

    def generate(*args, **kwargs):
        peak[0] = max(peak[0], 200 * 1024**2)
        return SimpleNamespace(
            success=True, audios=[{"tensor": np.zeros((2, 8)), "sample_rate": 48000}]
        )

    runtime = SimpleNamespace(
        torch=SimpleNamespace(
            cuda=SimpleNamespace(
                synchronize=lambda: None,
                max_memory_allocated=lambda: peak[0],
                reset_peak_memory_stats=reset,
            )
        ),
        dit=None,
        lm=None,
        generate_music=generate,
        GenerationParams=lambda **kwargs: kwargs,
        GenerationConfig=lambda **kwargs: kwargs,
    )
    model = adapter.AceStepAdapter()
    model.runtime = runtime
    model._include_load_peak = True
    request = {
        "task": "music.instrumental",
        "params": {"style": "test", "duration_s": 30},
        "seed": 1,
        "n_outputs": 1,
    }
    first = tmp_path / "cold"
    second = tmp_path / "warm"
    first.mkdir()
    second.mkdir()
    cold = model.generate(request, first, lambda event: None, CancelToken())
    warm = model.generate(request, second, lambda event: None, CancelToken())
    assert cold["vram_peak_mb"] == 1000 and warm["vram_peak_mb"] == 200
    assert len(reset_calls) == 2
    assert warm["result"]["inference_timings"][0]["audio_duration_s"] == 8 / 48000


def test_int8_requires_all_decoder_linears_and_pinned_versions(monkeypatch):
    import sys

    adapter = module("adapter")

    class Quantized:
        tensor_impl = SimpleNamespace(
            get_plain=lambda: (SimpleNamespace(dtype="int8"), None, None)
        )

    class Linear:
        def __init__(self, quantized=True):
            self.weight = Quantized() if quantized else object()

    layers = [("decoder.linear", Linear())]
    runtime = SimpleNamespace(
        torch=SimpleNamespace(
            __version__="2.10.0+cu128", nn=SimpleNamespace(Linear=Linear), int8="int8"
        ),
        dit=SimpleNamespace(
            quantization="int8_weight_only",
            offload_to_cpu=True,
            offload_dit_to_cpu=True,
            model=SimpleNamespace(named_modules=lambda: iter(layers)),
        ),
    )
    monkeypatch.setitem(sys.modules, "torchao", SimpleNamespace(__version__="0.16.0"))
    monkeypatch.setitem(
        sys.modules, "torchao.dtypes", SimpleNamespace(AffineQuantizedTensor=Quantized)
    )
    assert adapter.verify_int8_runtime(runtime)["quantized_linear_count"] == 1
    layers.append(("decoder.other", Linear(False)))
    with pytest.raises(Exception, match="INTERNAL"):
        adapter.verify_int8_runtime(runtime)
