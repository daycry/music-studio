"""Pruebas reales: sin dobles, sin descargar pesos ni fabricar tiempos."""

import hashlib
import json
import math
import os
import struct
import uuid
import wave
from pathlib import Path

import pytest
from engine_analysis import create_app
from engine_common.runtime import CpuGpu
from engine_contract import relative_path
from fastapi.testclient import TestClient

pytestmark = pytest.mark.gpu


def analyze(task, model_id, audio, params=None):
    root = Path("/data")
    path = root / relative_path(audio)
    assert path.is_file(), (
        "Configura STUDIO_ANALYSIS_TEST_AUDIO con un audio real dentro de data/"
    )
    job_id = "01" + uuid.uuid4().hex[:24].upper().translate(
        str.maketrans("ILOU", "1234")
    )
    headers = {"X-Studio-Engine-Token": os.environ["STUDIO_ENGINE_TOKEN"]}
    request = {
        "job_id": job_id,
        "task": task,
        "model_id": model_id,
        "inputs": [
            {
                "role": "audio",
                "path": audio,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "media_type": "audio/wav",
            }
        ],
        "params": params or {},
        "output_dir": f"tmp/{job_id}",
        "timeout_s": 600,
    }
    kwargs = {"gpu": CpuGpu()} if task == "audio.beats" else {}
    with TestClient(create_app(**kwargs)) as client:
        assert client.post("/v1/jobs", headers=headers, json=request).status_code == 202
        response = client.get(f"/v1/jobs/{job_id}/events", headers=headers)
        events = [json.loads(line) for line in response.text.splitlines()]
        terminals = [
            event for event in events if event["type"] in {"done", "error", "cancelled"}
        ]
        assert len(terminals) == 1, events
        assert terminals[0]["type"] == "done", terminals[0]
        result = terminals[0]["data"]["result"]
        supervisor = client.app.state.supervisor
        assert supervisor.alive and supervisor.pid != os.getpid()
        assert client.post("/v1/unload", headers=headers).status_code == 200
        assert not supervisor.alive
        return result


def test_transcribe_real_audio_returns_recognized_text_and_word_times():
    result = analyze(
        "audio.transcribe",
        "qwen3-asr-1.7b",
        os.getenv("STUDIO_ANALYSIS_TEST_AUDIO", ""),
    )
    assert result["analysis"]["text"].strip()
    assert all(
        word["end_s"] >= word["start_s"] >= 0 for word in result["analysis"]["words"]
    )
    assert [stage["model_id"] for stage in result["stages"]] == [
        "qwen3-asr-1.7b",
        "qwen3-forcedaligner-0.6b",
    ]


def test_clap_real_audio_returns_finite_cosine_similarity():
    result = analyze(
        "audio.clap",
        "clap-larger-music",
        os.getenv("STUDIO_ANALYSIS_TEST_AUDIO", ""),
        {"text": "Music with singing"},
    )
    assert math.isfinite(result["analysis"]["score"])
    assert -1 <= result["analysis"]["score"] <= 1
    assert result["analysis"]["text_truncated"] is False


def test_aesthetics_real_audio_returns_four_finite_axes():
    result = analyze(
        "audio.aesthetics",
        "audiobox-aesthetics",
        os.getenv("STUDIO_ANALYSIS_TEST_AUDIO", ""),
    )
    assert set(result["analysis"]) == {"CE", "CU", "PC", "PQ"}
    assert all(math.isfinite(value) for value in result["analysis"].values())


def test_beats_cpu_returns_120_bpm_with_two_bpm_tolerance():
    filename = f"tmp/t08-click-{uuid.uuid4().hex}.wav"
    path = Path("/data") / filename
    sample_rate, seconds = 22050, 30
    path.parent.mkdir(exist_ok=True, parents=True)
    try:
        with wave.open(str(path), "wb") as stream:
            stream.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
            stream.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        int(
                            25000
                            * math.exp(-offset / 200)
                            * math.sin(2 * math.pi * 1000 * offset / sample_rate)
                        ),
                    )
                    if (offset := sample % (sample_rate // 2)) < 2200
                    else b"\0\0"
                    for sample in range(sample_rate * seconds)
                )
            )
        result = analyze("audio.beats", "beat-this", filename)
        print(
            f"beat_this CPU: BPM={result['analysis']['bpm']:.6f}; tolerance=120±2; beats={len(result['analysis']['beats_s'])}"
        )
        assert abs(result["analysis"]["bpm"] - 120) <= 2
    finally:
        path.unlink(missing_ok=True)
