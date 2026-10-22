"""Dobles CPU de fronteras upstream: recursos locales y carga estricta."""

import contextlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from engine_analysis.backend import LocalBackend


@pytest.fixture
def libraries(monkeypatch):
    import engine_analysis.backend as backend_module

    monkeypatch.setattr(
        backend_module,
        "read_lock",
        lambda root: {
            "beat-this": {
                "file": {
                    "sha256": "8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331"
                }
            }
        },
    )
    torch = MagicMock()
    torch.inference_mode = contextlib.nullcontext
    torch.cuda.max_memory_allocated.return_value = 100 * 1024**2
    monkeypatch.setitem(sys.modules, "torch", torch)
    model = MagicMock()
    model.to.return_value = model
    model.eval.return_value = model
    state = {"model.test": "tensor"}
    safe = SimpleNamespace(load_file=MagicMock(return_value=state))
    monkeypatch.setitem(sys.modules, "safetensors.torch", safe)
    return torch, model, safe


def test_clap_constructs_local_config_and_strict_converted_weights(
    monkeypatch, libraries
):
    _, model, _ = libraries
    config, processor = MagicMock(), MagicMock()
    classes = SimpleNamespace(
        ClapConfig=config,
        ClapProcessor=processor,
        ClapModel=MagicMock(return_value=model),
    )
    monkeypatch.setitem(sys.modules, "transformers", classes)
    backend = LocalBackend(Path("models"))
    backend._load_clap(Path("models/clap"), [Path("models/clap/converted.safetensors")])
    model.load_state_dict.assert_called_once_with({"model.test": "tensor"}, strict=True)
    config.from_pretrained.assert_called_once_with(
        "models\\clap" if sys.platform == "win32" else "models/clap",
        local_files_only=True,
    )
    assert processor.from_pretrained.call_args.kwargs["local_files_only"] is True


@pytest.mark.parametrize("model_id", ["qwen3-asr-1.7b", "qwen3-forcedaligner-0.6b"])
def test_qwen_safe_offline_loader_never_attaches_second_model(
    monkeypatch, libraries, model_id
):
    _, model, _ = libraries
    auto_model = SimpleNamespace(from_pretrained=MagicMock(return_value=(model, {})))
    processor = SimpleNamespace(from_pretrained=MagicMock(return_value="processor"))
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoModel=auto_model, AutoProcessor=processor),
    )
    asr, aligner = MagicMock(), MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "qwen_asr",
        SimpleNamespace(Qwen3ASRModel=asr, Qwen3ForcedAligner=aligner),
    )
    monkeypatch.setitem(
        sys.modules,
        "qwen_asr.inference.qwen3_forced_aligner",
        SimpleNamespace(Qwen3ForceAlignProcessor=MagicMock()),
    )
    backend = LocalBackend(Path("models"))
    backend._load_qwen(Path("models/qwen"), model_id)
    kwargs = auto_model.from_pretrained.call_args.kwargs
    assert kwargs["use_safetensors"] and kwargs["local_files_only"]
    assert kwargs["trust_remote_code"] is False
    if model_id == "qwen3-asr-1.7b":
        assert asr.call_args.kwargs["forced_aligner"] is None
        aligner.assert_not_called()
    else:
        asr.assert_not_called()


def test_aesthetics_bypasses_unsafe_upstream_setup(monkeypatch, libraries, tmp_path):
    _, model, _ = libraries

    class Predictor:
        def __init__(self, *args, **kwargs):
            pytest.fail("No debe ejecutarse setup_model upstream")

    normalize = lambda **values: values
    monkeypatch.setitem(
        sys.modules,
        "audiobox_aesthetics.infer",
        SimpleNamespace(AesPredictor=Predictor, Normalize=normalize),
    )
    monkeypatch.setitem(
        sys.modules,
        "audiobox_aesthetics.model.aes",
        SimpleNamespace(AesMultiOutput=MagicMock(return_value=model)),
    )
    config = {"precision": "32", "target_transform": {"CE": {"mean": 5, "std": 1}}}
    (tmp_path / "config.json").write_text(json.dumps(config))
    backend = LocalBackend(tmp_path)
    backend._load_aesthetics(tmp_path, [tmp_path / "model.safetensors"])
    assert backend.model.target_transform == config["target_transform"]
    assert model.enable_autocast is True, "Audiobox debe activar BF16 explícitamente"
    model.load_state_dict.assert_called_once_with({"model.test": "tensor"}, strict=True)


def test_beats_reconstructs_audited_architecture_and_strict_prefix(
    monkeypatch, libraries
):
    _, model, _ = libraries

    class Predictor:
        def __init__(self):
            pytest.fail("No debe ejecutarse loader pickle upstream")

    def beat_this(spect_dim=128, transformer_dim=512, stem_dim=32):
        assert (spect_dim, transformer_dim, stem_dim) == (128, 512, 32)
        return model

    monkeypatch.setitem(
        sys.modules, "beat_this.inference", SimpleNamespace(Audio2Beats=Predictor)
    )
    monkeypatch.setitem(
        sys.modules, "beat_this.model.beat_tracker", SimpleNamespace(BeatThis=beat_this)
    )
    monkeypatch.setitem(
        sys.modules,
        "beat_this.model.postprocessor",
        SimpleNamespace(Postprocessor=MagicMock()),
    )
    monkeypatch.setitem(
        sys.modules, "beat_this.preprocessing", SimpleNamespace(LogMelSpect=MagicMock())
    )
    backend = LocalBackend(Path("models"))
    backend._load_beats(Path("models/beat"), [Path("models/beat/final0.safetensors")])
    model.load_state_dict.assert_called_once_with({"test": "tensor"}, strict=True)


@pytest.mark.parametrize(
    "task",
    [
        "audio.transcribe",
        "audio.align_lyrics",
        "audio.aesthetics",
        "audio.beats",
    ],
)
def test_real_dispatch_contract_with_cpu_double_audio(monkeypatch, libraries, task):
    _, model, _ = libraries
    monkeypatch.setitem(
        sys.modules,
        "soundfile",
        SimpleNamespace(
            read=lambda *args, **kwargs: (np.ones((16000, 1), dtype="float32"), 16000)
        ),
    )
    backend = LocalBackend(Path("models"))
    backend.model = model
    model.transcribe.return_value = [SimpleNamespace(text="hola", language="Spanish")]
    model.align.return_value = [
        [SimpleNamespace(text="hola", start_time=0.1, end_time=0.5)]
    ]
    model.forward.return_value = [{"CE": 1, "CU": 2, "PC": 3, "PQ": 4}]
    if task == "audio.beats":
        model.return_value = (np.arange(0, 1.5, 0.5), np.array([0]))
    result = backend.run(
        task, Path("fixture.wav"), {"text": "hola", "language": "Spanish"}
    )
    assert isinstance(result, dict)
    if task == "audio.transcribe":
        assert result == {
            "text": "hola",
            "language": "Spanish",
            "segments": [
                {"text": "hola", "language": "Spanish", "start_s": 0, "end_s": 1}
            ],
        }
        assert model.transcribe.call_args.kwargs["return_time_stamps"] is False
    elif task == "audio.align_lyrics":
        assert result["words"] == [{"text": "hola", "start_s": 0.1, "end_s": 0.5}]
    elif task == "audio.beats":
        assert result["bpm"] == 120
    else:
        assert result == {"CE": 1, "CU": 2, "PC": 3, "PQ": 4}


def test_release_drops_references_and_clears_gpu_allocator(libraries):
    torch, model, _ = libraries
    backend = LocalBackend(Path("models"))
    backend.model = backend.processor = model
    backend.device = "cuda:0"
    backend.release()
    assert backend.model is None and backend.processor is None
    torch.cuda.empty_cache.assert_called_once()
    torch.cuda.synchronize.assert_called_once()
