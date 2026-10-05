import json
import wave

import engine_mock as mock
import pytest


def test_catalog_outputs(tmp_path):
    assert hasattr(mock, "MockAdapter"), "Mock del catálogo todavía no implementado"
    from engine_common import CancelToken

    descriptor = mock.MockAdapter().descriptor
    expected = {
        "music.song",
        "music.instrumental",
        "music.retake",
        "music.extend",
        "music.repaint",
        "music.cover",
        "music.complete",
        "audio.stems",
        "audio.beats",
        "audio.key",
        "audio.transcribe",
        "audio.align_lyrics",
        "audio.clap",
        "audio.aesthetics",
        "text.generate",
        "image.generate",
        "image.edit",
        "image.depth",
        "video.i2v",
        "video.flf2v",
        "video.t2v",
        "video.lipsync",
        "video.upscale",
        "train.lora",
    }
    assert set(descriptor.tasks) == expected
    assert descriptor.tasks["audio.beats"].device == "cpu"
    for task in sorted(expected):
        events = []
        output = tmp_path / task
        output.mkdir()
        adapter = mock.MockAdapter(stage_delay_ms=0)
        result = adapter.generate(
            {"task": task, "params": {"duration_s": 0.1}, "n_outputs": 1, "seed": 7},
            output,
            events.append,
            CancelToken(),
        )
        if task == "text.generate":
            assert "[Verse]" in result["result"]["text"]
            assert any(e[0] == "delta" for e in events)
        else:
            assert result["artifacts"]
            for artifact in result["artifacts"]:
                assert (output / artifact["filename"]).stat().st_size > 0


def test_audio_and_failure_directives(tmp_path):
    assert hasattr(mock, "MockAdapter"), "Audio y directivas ausentes"
    from engine_common import CancelToken, EngineError

    adapter = mock.MockAdapter(stage_delay_ms=0)
    request = {
        "task": "music.song",
        "params": {"duration_s": 0.125},
        "n_outputs": 2,
        "seed": 7,
    }
    result = adapter.generate(request, tmp_path, lambda event: None, CancelToken())
    assert [a["meta"]["seed"] for a in result["artifacts"]] == [7, 8]
    with wave.open(str(tmp_path / result["artifacts"][0]["filename"])) as audio:
        assert (audio.getframerate(), audio.getnchannels(), audio.getnframes()) == (
            48000,
            2,
            6000,
        )
    request["params"]["style"] = "@mock:fail_once=PROVIDER_ERROR @mock:retryable"
    with pytest.raises(EngineError) as error:
        adapter.generate(request, tmp_path, lambda event: None, CancelToken())
    assert error.value.code == "PROVIDER_ERROR" and error.value.retryable
    assert adapter.generate(request, tmp_path, lambda event: None, CancelToken())[
        "artifacts"
    ]
    request["params"] = {"_mock": {"fail": "TIMEOUT", "retryable": True}}
    with pytest.raises(EngineError, match="TIMEOUT"):
        adapter.generate(request, tmp_path, lambda event: None, CancelToken())


def test_media_and_analysis(tmp_path):
    assert hasattr(mock, "MockAdapter"), "Medios sintéticos ausentes"
    from engine_common import CancelToken

    adapter = mock.MockAdapter(stage_delay_ms=0)
    for task, signature in [("image.generate", b"\x89PNG"), ("video.t2v", b"ftyp")]:
        result = adapter.generate(
            {"task": task, "params": {"duration_s": 0.1}},
            tmp_path,
            lambda e: None,
            CancelToken(),
        )
        content = (tmp_path / result["artifacts"][0]["filename"]).read_bytes()
        assert signature in content[:32]
    result = adapter.generate(
        {"task": "audio.beats", "params": {"duration_s": 2}},
        tmp_path,
        lambda e: None,
        CancelToken(),
    )
    data = json.loads((tmp_path / result["artifacts"][0]["filename"]).read_text())
    assert data["bpm"] == 120 and data["beats"] == [0, 0.5, 1, 1.5]
