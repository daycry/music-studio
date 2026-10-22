import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from engine_common import EngineError


def backend_module():
    name = "engine_analysis.backend"
    assert importlib.util.find_spec(name) is not None, (
        "Faltan loaders locales de los cinco modelos"
    )
    return importlib.import_module(name)


def test_beats_loading_never_initializes_cuda(monkeypatch):
    module = backend_module()

    class Cuda:
        def __getattr__(self, name):
            pytest.fail(f"Beats consultó CUDA: {name}")

    import sys

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=Cuda()))
    monkeypatch.setattr(
        module,
        "verify_model",
        lambda root, model_id: (
            root / model_id,
            [root / model_id / "final0.safetensors"],
        ),
    )
    calls = []
    monkeypatch.setattr(
        module.LocalBackend,
        "_load_beats",
        lambda self, directory, weights: calls.append((directory, weights)),
    )
    engine = module.LocalBackend(Path("models"))
    engine.load("beat-this", "cpu", 0, 0)
    engine.release()
    assert calls[0][0] == Path("models/beat-this")
    assert engine.model is None


def test_gpu_load_recomputes_budget_before_each_model(monkeypatch):
    module = backend_module()
    import sys

    fractions = []
    cuda = SimpleNamespace(
        is_available=lambda: True,
        set_per_process_memory_fraction=lambda fraction: fractions.append(fraction),
        reset_peak_memory_stats=lambda: None,
        max_memory_allocated=lambda: 0,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    monkeypatch.setattr(
        module, "verify_model", lambda root, model_id: (root / model_id, [])
    )
    monkeypatch.setattr(module, "gpu_snapshot", lambda: (12000, 7000))
    monkeypatch.setattr(module.LocalBackend, "_load_qwen", lambda *args: None)
    engine = module.LocalBackend(Path("models"))
    engine.load("qwen3-asr-1.7b", "bf16", 9000, 12000)
    assert fractions == [(7000 - 512) / 12000]
    assert engine.cap_mb == 6488


def test_clap_rejects_text_truncation_instead_of_silent_score():
    module = backend_module()
    processor = SimpleNamespace(
        tokenizer=lambda text, **kwargs: {"input_ids": list(range(90))}
    )
    config = SimpleNamespace(text_config=SimpleNamespace(max_position_embeddings=77))
    with pytest.raises(EngineError) as error:
        module.clap_text_budget(processor, config, "long text")
    assert error.value.code == "INVALID_PARAMS"
