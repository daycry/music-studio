"""Regresiones CPU: fragmentos reconocidos, offsets y errores de entrada."""

import json
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf
import torch
from engine_analysis.adapter import AnalysisAdapter
from engine_analysis.backend import LocalBackend
from engine_common import EngineError, worker
from engine_common.runtime import CancelToken
from qwen_asr.inference.utils import SUPPORTED_LANGUAGES


@pytest.mark.parametrize("duration,sample_rate", [(450, 16000), (600, 22050)])
def test_long_transcription_aligns_recognized_fragments_with_real_offsets(
    tmp_path, duration, sample_rate
):
    audio = tmp_path / "long.wav"
    sf.write(audio, np.zeros(duration * sample_rate, dtype=np.float32), sample_rate)
    backend = LocalBackend(tmp_path)
    events = []

    class Asr:
        def transcribe(self, audio, language, return_time_stamps):
            duration = len(audio[0]) / audio[1]
            events.append(("asr", duration))
            index = sum(event[0] == "asr" for event in events)
            return [SimpleNamespace(text=f"word{index}", language="English")]

    class Aligner:
        def align(self, audio, text, language):
            duration = len(audio[0]) / audio[1]
            events.append(("align", duration, text, language))
            return [
                [SimpleNamespace(text=text, start_time=duration - 1, end_time=duration)]
            ]

    def load(model_id, *args):
        assert backend.model is None
        events.append(("load", model_id))
        backend.model = Asr() if model_id == "qwen3-asr-1.7b" else Aligner()

    def release():
        events.append(("release",))
        backend.model = None

    backend.load, backend.release = load, release
    (tmp_path / "models.lock.json").write_text(
        json.dumps(
            {
                "models": {
                    "qwen3-asr-1.7b": {"revision": "asr"},
                    "qwen3-forcedaligner-0.6b": {"revision": "align"},
                }
            }
        )
    )
    engine = AnalysisAdapter(backend, tmp_path, tmp_path)
    result = engine.generate(
        {
            "task": "audio.transcribe",
            "model_id": "qwen3-asr-1.7b",
            "inputs": [{"role": "audio", "path": "long.wav"}],
            "params": {},
        },
        tmp_path,
        lambda event: None,
        CancelToken(),
    )["result"]["analysis"]
    durations = [180, 180, 90] if duration == 450 else [180, 180, 180, 60]
    assert [event[1] for event in events if event[0] == "asr"] == durations
    assert [event[1:] for event in events if event[0] == "align"] == [
        (length, f"word{index}", "English") for index, length in enumerate(durations, 1)
    ]
    assert sum(event[0] == "release" for event in events) == 1
    assert events.index(("release",)) > max(
        i for i, e in enumerate(events) if e[0] == "asr"
    )
    assert result["text"] == "".join(
        f"word{index}" for index in range(1, len(durations) + 1)
    )
    assert [word["end_s"] for word in result["words"]] == list(np.cumsum(durations))
    assert not torch.cuda.is_initialized()


def test_real_aligner_parsing_uses_segment_audio_text_language_and_offsets(tmp_path):
    from qwen_asr import Qwen3ForcedAligner
    from qwen_asr.inference.qwen3_forced_aligner import Qwen3ForceAlignProcessor
    from transformers import BatchFeature

    audio = tmp_path / "long.wav"
    sf.write(audio, np.zeros(450 * 16000, dtype=np.float32), 16000)
    calls = []

    class Processor:
        def __call__(self, text, audio, **kwargs):
            calls.append((text, len(audio[0]) / 16000))
            return BatchFeature({"input_ids": torch.tensor([[9, 9]])})

    def thinker(**kwargs):
        logits = torch.zeros(1, 2, 5000)
        length = calls[-1][1]
        logits[0, 0, round((length - 1.04) / 0.08)] = 1
        logits[0, 1, round(length / 0.08)] = 1
        return SimpleNamespace(logits=logits)

    model = SimpleNamespace(
        device=torch.device("cpu"),
        dtype=torch.float32,
        config=SimpleNamespace(timestamp_token_id=9, timestamp_segment_time=80),
        thinker=thinker,
    )
    backend = LocalBackend(tmp_path)
    backend.model = Qwen3ForcedAligner(model, Processor(), Qwen3ForceAlignProcessor())
    segments = [
        {"start_s": 0, "end_s": 180, "text": "hello", "language": "English"},
        {"start_s": 180, "end_s": 360, "text": "", "language": ""},
        {"start_s": 360, "end_s": 450, "text": "hola", "language": "Spanish"},
    ]
    words = backend.run("audio.align_lyrics", audio, {"segments": segments})["words"]
    assert [duration for text, duration in calls] == [180, 90]
    assert [word["text"] for word in words] == ["hello", "hola"]
    assert [word["end_s"] for word in words] == [180, 450]
    assert words[-1]["start_s"] > 399.92
    assert not torch.cuda.is_initialized()


@pytest.mark.parametrize(
    "error,expected",
    [
        (RuntimeError("internal"), "INTERNAL"),
        (ValueError("internal value"), "INTERNAL"),
        (EngineError("VRAM_EXCEEDED"), "VRAM_EXCEEDED"),
    ],
)
def test_worker_keeps_model_errors_distinct_from_invalid_inputs(
    tmp_path, monkeypatch, error, expected
):
    audio = tmp_path / "input.wav"
    sf.write(audio, np.zeros(16000, dtype=np.float32), 16000)

    def fail(**kwargs):
        raise error

    backend = LocalBackend(tmp_path)
    backend.model = SimpleNamespace(transcribe=fail)
    messages = []
    monkeypatch.setattr(worker, "send", messages.append)
    adapter = SimpleNamespace(
        generate=lambda *args: backend.run(
            "audio.transcribe", audio, {"language": "English"}
        )
    )
    worker.run(adapter, {}, tmp_path, CancelToken())
    assert messages[-1]["code"] == expected


def test_light_language_enum_matches_pinned_upstream_and_preflight():
    from engine_analysis.descriptor import LANGUAGES
    from engine_analysis.server import preflight

    assert list(LANGUAGES) == SUPPORTED_LANGUAGES
    with pytest.raises(EngineError) as error:
        preflight(
            {
                "task": "audio.transcribe",
                "inputs": [{"role": "audio"}],
                "params": {"language": "not-a-language"},
            }
        )
    assert error.value.code == "INVALID_PARAMS"


def test_worker_keeps_audio_system_failure_internal(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise sf.LibsndfileError(2)

    monkeypatch.setattr(sf, "read", fail)
    backend = LocalBackend(tmp_path)
    messages = []
    monkeypatch.setattr(worker, "send", messages.append)
    adapter = SimpleNamespace(
        generate=lambda *args: backend.run("audio.beats", "input.wav", {})
    )
    worker.run(adapter, {}, tmp_path, CancelToken())
    assert messages[-1]["code"] == "INTERNAL"


def test_transcription_preserves_silent_intervals_and_mixed_languages(tmp_path):
    audio = tmp_path / "mixed.wav"
    sf.write(audio, np.zeros(450 * 16000, dtype=np.float32), 16000)
    results = iter(
        [
            SimpleNamespace(text="hello ", language="English"),
            SimpleNamespace(text="", language=""),
            SimpleNamespace(text="hola", language="Spanish"),
        ]
    )
    backend = LocalBackend(tmp_path)
    backend.model = SimpleNamespace(transcribe=lambda **kwargs: [next(results)])
    result = backend.run("audio.transcribe", audio, {})
    assert result["text"] == "hello hola"
    assert result["language"] == "English,Spanish"
    assert result["segments"] == [
        {"start_s": 0, "end_s": 180, "text": "hello ", "language": "English"},
        {"start_s": 180, "end_s": 360, "text": "", "language": ""},
        {"start_s": 360, "end_s": 450, "text": "hola", "language": "Spanish"},
    ]


def test_independent_alignment_declares_and_enforces_180_seconds(tmp_path):
    import engine_analysis

    descriptor = next(
        model
        for model in engine_analysis.descriptors()
        if model.id == "qwen3-forcedaligner-0.6b"
    )
    assert descriptor.tasks["audio.align_lyrics"].limits["duration_s"] == [0, 180]
    audio = tmp_path / "long.wav"
    sf.write(audio, np.zeros(181 * 16000, dtype=np.float32), 16000)
    backend = LocalBackend(tmp_path)
    backend.model = SimpleNamespace(
        align=lambda **kwargs: pytest.fail("No debe alinear audio largo")
    )
    with pytest.raises(EngineError) as error:
        backend.run(
            "audio.align_lyrics", audio, {"text": "hello", "language": "English"}
        )
    assert error.value.code == "INVALID_PARAMS"


@pytest.mark.parametrize("case", ["language", "audio"])
def test_worker_classifies_invalid_input_without_hiding_internal(
    tmp_path, monkeypatch, case
):
    audio = tmp_path / "input.wav"
    if case == "audio":
        audio.write_bytes(b"not audio")
    else:
        sf.write(audio, np.zeros(16000, dtype=np.float32), 16000)
    backend = LocalBackend(tmp_path)

    class Model:
        def transcribe(self, **kwargs):
            from qwen_asr.inference.utils import (
                normalize_language_name,
                validate_language,
            )

            validate_language(normalize_language_name(kwargs["language"]))
            raise RuntimeError("internal sentinel")

    backend.model = Model()
    messages = []
    monkeypatch.setattr(worker, "send", messages.append)
    adapter = SimpleNamespace(
        generate=lambda *args: backend.run(
            "audio.transcribe",
            audio,
            {"language": "not-a-language" if case == "language" else "English"},
        )
    )
    worker.run(adapter, {}, tmp_path, CancelToken())
    assert messages[-1]["code"] == "INVALID_PARAMS"
    assert not torch.cuda.is_initialized()
