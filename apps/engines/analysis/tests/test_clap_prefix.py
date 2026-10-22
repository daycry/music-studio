"""Compatibilidad real del prefijo CLAP del checkpoint, sin pesos ni CUDA."""

import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

torch = pytest.importorskip("torch", reason="Requiere el runtime del engine Docker")
pytest.importorskip("transformers")
from engine_analysis.backend import LocalBackend
from transformers import ClapConfig, ClapProcessor
from transformers.models.clap.modeling_clap import ClapAudioEncoder, ClapAudioPatchEmbed


class RealAudioPrefix:
    """Ejecuta hasta Conv2d real; el doble empieza después de esa frontera."""

    def __init__(self, config):
        self.config = config
        audio_config = config.audio_config
        self.batch_norm = (
            torch.nn.BatchNorm2d(audio_config.num_mel_bins)
            .to(dtype=torch.bfloat16)
            .eval()
        )
        self.patch_embed = (
            ClapAudioPatchEmbed(audio_config).to(dtype=torch.bfloat16).eval()
        )
        self.reshape_spec = SimpleNamespace(
            spec_size=audio_config.spec_size,
            freq_ratio=audio_config.spec_size // audio_config.num_mel_bins,
        )
        self.received = self.projected = None

    def __call__(self, **values):
        self.received = values
        normalized = self.batch_norm(
            values["input_features"].transpose(1, 3)
        ).transpose(1, 3)
        image = ClapAudioEncoder.reshape_mel2img(self.reshape_spec, normalized)
        self.projected = self.patch_embed(image)
        return SimpleNamespace(
            audio_embeds=torch.ones(1, 2), text_embeds=torch.ones(1, 2)
        )


@pytest.mark.parametrize("duration_s", [1, 30], ids=["short_1s", "long_30s"])
def test_clap_checkpoint_real_projection_preserves_text_and_window(
    tmp_path, duration_s
):
    directory = (
        Path(os.environ.get("STUDIO_MODELS_DIR", "/models")) / "clap-larger-music"
    )
    if not (directory / "config.json").is_file():
        pytest.skip("Requiere recursos locales del checkpoint CLAP montados")
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(2)
    config = ClapConfig.from_pretrained(str(directory), local_files_only=True)
    processor = ClapProcessor.from_pretrained(
        str(directory), local_files_only=True, trust_remote_code=False
    )
    assert config.audio_config.enable_fusion is False
    assert processor.feature_extractor.truncation == "rand_trunc"
    model = RealAudioPrefix(config)
    backend = LocalBackend(directory.parent)
    backend.model, backend.processor, backend.device = model, processor, "cpu"
    audio = tmp_path / "synthetic.wav"
    sf.write(audio, np.zeros(24000 * duration_s, dtype=np.float32), 24000)
    text = "Music with singing and soft piano in the background"
    expected = processor.tokenizer(
        [text], return_tensors="pt", padding=True, truncation=False
    )["input_ids"]
    result = backend.run("audio.clap", audio, {"text": text})
    assert model.patch_embed.proj.in_channels == 1
    assert model.received["input_features"].shape == (1, 1, 1001, 64)
    assert model.received["input_features"].dtype == torch.bfloat16
    assert model.projected.dtype == torch.bfloat16
    assert torch.equal(model.received["input_ids"], expected)
    assert result["text_tokens"] == expected.shape[-1]
    assert result["text_truncated"] is False
    assert result["audio_duration_s"] == duration_s
    assert result["audio_window_s"] == 10
    assert not torch.cuda.is_initialized()
