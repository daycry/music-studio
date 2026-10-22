"""Regresión portable: procesamiento CLAP real, sin pesos ni CUDA."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

torch = pytest.importorskip(
    "torch",
    reason="Requiere runtime CPU del engine Docker; no instalar torch en el host",
)
pytest.importorskip("transformers", reason="Requiere dependencias del engine Docker")
from engine_analysis.backend import LocalBackend
from engine_common import EngineError
from transformers import (
    ClapFeatureExtractor,
    ClapProcessor,
    ClapTextConfig,
    RobertaTokenizer,
)
from transformers.models.gpt2.tokenization_gpt2 import bytes_to_unicode

TEST_TEXT = "Music with singing and soft piano in the background"


def synthetic_processor(tmp_path):
    vocab = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3, "<mask>": 4}
    for character in bytes_to_unicode().values():
        if character not in vocab:
            vocab[character] = len(vocab)
    vocab_path = tmp_path / "vocab.json"
    merges_path = tmp_path / "merges.txt"
    vocab_path.write_text(json.dumps(vocab), encoding="utf-8")
    merges_path.write_text("#version: 0.2\n", encoding="utf-8")
    tokenizer = RobertaTokenizer(
        vocab_file=str(vocab_path), merges_file=str(merges_path), model_max_length=512
    )
    extractor = ClapFeatureExtractor(
        sampling_rate=48000, padding="repeatpad", truncation="fusion"
    )
    return ClapProcessor(feature_extractor=extractor, tokenizer=tokenizer)


class EmbeddingDouble:
    def __init__(self):
        self.config = SimpleNamespace(
            text_config=ClapTextConfig(max_position_embeddings=514)
        )
        self.received = None

    def __call__(self, **values):
        self.received = values
        return SimpleNamespace(
            audio_embeds=torch.tensor([[1.0, 0.0, 0.0]]),
            text_embeds=torch.tensor([[1.0, 1.0, 0.0]]),
        )


@pytest.mark.parametrize("duration_s", [30, 1], ids=["long_30s", "short_1s"])
def test_clap_real_route_preserves_complete_text_and_audio_metadata(
    tmp_path, duration_s
):
    assert not torch.cuda.is_initialized()
    np.random.seed(0)
    sample_rate = 48000
    ticks = np.arange(sample_rate * duration_s, dtype=np.float32) / sample_rate
    mono = (0.15 * np.sin(2 * np.pi * 440 * ticks)).astype(np.float32)
    audio = tmp_path / "synthetic.wav"
    sf.write(audio, mono, sample_rate, subtype="PCM_16")
    processor = synthetic_processor(tmp_path)
    model = EmbeddingDouble()
    backend = LocalBackend(tmp_path / "unused-model-directory")
    backend.processor, backend.model, backend.device = processor, model, "cpu"
    expected_tokens = processor.tokenizer(
        [TEST_TEXT], return_tensors="pt", padding=True, truncation=False
    )["input_ids"]
    backend_source = Path(
        __import__("engine_analysis.backend", fromlist=["__file__"]).__file__
    )
    provenance = {
        "duration_s": duration_s,
        "fixture_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "backend_sha256": hashlib.sha256(backend_source.read_bytes()).hexdigest(),
        "cuda_initialized_before": torch.cuda.is_initialized(),
    }
    (tmp_path / "provenance.json").write_text(json.dumps(provenance, indent=2))
    # La ruta productiva completa debe pasar: no sustituir procesado ni funciones.
    try:
        result = backend.run("audio.clap", audio, {"text": TEST_TEXT})
    except Exception as error:
        provenance["error_type"] = type(error).__name__
        provenance["error"] = str(error)
        raise
    finally:
        provenance["cuda_initialized_after"] = torch.cuda.is_initialized()
        provenance["model_called"] = model.received is not None
        if model.received is not None:
            provenance["transport"] = {
                key: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                    "device": str(value.device),
                }
                for key, value in model.received.items()
            }
            provenance["complete_text"] = torch.equal(
                model.received["input_ids"], expected_tokens
            )
        (tmp_path / "provenance.json").write_text(json.dumps(provenance, indent=2))
        print(
            f"CLAP route CPU: duration={duration_s}, cuda_initialized_after={torch.cuda.is_initialized()}, model_called={model.received is not None}"
        )
    values = model.received
    assert set(values) == {"input_features", "is_longer", "input_ids", "attention_mask"}
    assert values["input_features"].shape == (1, 4, 1001, 64)
    assert values["input_features"].dtype == torch.bfloat16
    assert (
        values["is_longer"].shape == (1, 1) and values["is_longer"].dtype == torch.bool
    )
    assert values["input_ids"].dtype == torch.int64
    assert torch.equal(values["input_ids"], expected_tokens)
    assert all(value.device.type == "cpu" for value in values.values())
    assert result["text_tokens"] == expected_tokens.shape[-1]
    assert result["text_token_limit"] == 512
    assert result["text_truncated"] is False
    assert result["audio_duration_s"] == duration_s
    assert result["audio_window_s"] == 10
    assert result["score"] == pytest.approx(2**-0.5)
    assert not torch.cuda.is_initialized()
    print(
        f"CLAP route CPU: duration={duration_s}, complete_text=True, weights_loaded=False, cuda_initialized=False"
    )


def test_clap_real_tokenizer_rejects_excess_text_before_model(tmp_path):
    processor = synthetic_processor(tmp_path)
    model = EmbeddingDouble()
    backend = LocalBackend(tmp_path / "unused-model-directory")
    backend.processor, backend.model, backend.device = processor, model, "cpu"
    audio = tmp_path / "short.wav"
    sf.write(audio, np.zeros(48000, dtype=np.float32), 48000)
    with pytest.raises(EngineError) as error:
        backend.run("audio.clap", audio, {"text": "a" * 700})
    assert error.value.code == "INVALID_PARAMS"
    assert model.received is None
    assert not torch.cuda.is_initialized()
