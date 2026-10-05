"""Verificación real de 30 s; ejecutar sólo tras permiso/condición VRAM externa."""

import json
import os
import time
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.gpu

# Asociada al fixture, fuera de JobRequest: el engine no modela autoría de canción.
LYRICS_DECLARATION = {
    "declared": True,
    "source": "assistant_created_for_this_test",
    "description": "Letra sintética original creada por el asistente para esta prueba de 30 segundos.",
    "scope": "test_real_30_seconds_and_unload",
}


def test_real_30_seconds_and_unload():
    import numpy as np
    import soundfile as sf
    from engine_acestep import create_app
    from fastapi.testclient import TestClient

    assert os.environ.get("STUDIO_ENGINE_CONTAINER") == "1", (
        "Requiere imagen engine-acestep"
    )
    assert os.environ.get("STUDIO_ALLOW_UNVERIFIED") == "1", (
        "La prueba requiere opt-in explícito de desarrollo"
    )
    assert LYRICS_DECLARATION["declared"]
    token = os.environ["STUDIO_ENGINE_TOKEN"]
    headers = {"X-Studio-Engine-Token": token}
    # ULID sintáctico nuevo; no persiste entidades de canción/take.
    job_id = "01" + uuid.uuid4().hex[:24].upper().translate(
        str.maketrans("ILOU", "1234")
    )
    root = Path("/data")
    with TestClient(create_app()) as client:
        before = client.get("/v1/health", headers=headers).json()
        request = {
            "job_id": job_id,
            "task": "music.song",
            "model_id": "ace-step-1.5-turbo",
            "mode": "bf16",
            "inputs": [],
            "params": {
                "style": "Warm acoustic pop, steady drums, clear Spanish vocals",
                "lyrics": "[Verse]\nLa mañana trae una canción\nY la luz despierta el corazón\n[Chorus]\nCantaremos al salir el sol\nCon el viento suena nuestra voz",
                "language": "es",
                "vocal_language": "es",
                "duration_s": 30,
                "bpm": 94,
                "key": "C major",
            },
            "seed": 42,
            "n_outputs": 1,
            "output_dir": f"tmp/{job_id}/",
            "timeout_s": 600,
        }
        response = client.post("/v1/jobs", json=request, headers=headers)
        assert response.status_code == 202, response.text
        events = [
            json.loads(line)
            for line in client.get(
                f"/v1/jobs/{job_id}/events", headers=headers
            ).text.splitlines()
        ]
        terminal = [
            event for event in events if event["type"] in {"done", "error", "cancelled"}
        ]
        assert len(terminal) == 1 and terminal[0]["type"] == "done", terminal
        result = terminal[0]["data"]
        samples, rate = sf.read(
            root / result["artifacts"][0]["path"], dtype="float32", always_2d=True
        )
        assert rate == 48000 and samples.shape[1] == 2
        assert abs(len(samples) / rate - 30) <= 0.1
        assert np.isfinite(samples).all() and np.sqrt(np.mean(samples**2)) > 1e-5
        assert sf.info(root / result["artifacts"][0]["path"]).subtype == "FLOAT"
        telemetry = result["telemetry"]
        assert telemetry["load_s"] > 0 and telemetry["run_s"] > 0
        assert telemetry["vram_peak_mb"] > 0 and telemetry["vram_cap_mb"] > 0
        assert telemetry["mode"] == "bf16" and len(telemetry["model_revision"]) == 40
        assert not telemetry["spilled"]
        supervisor = client.app.state.supervisor
        child = supervisor.process
        assert child is not None and child.poll() is None
        assert client.post("/v1/unload", headers=headers).status_code == 200
        assert child.poll() is not None and supervisor.pid is None
        time.sleep(1)
        after = client.get("/v1/health", headers=headers).json()
        assert after["loaded"] is None
        assert after["gpu"]["free_mb"] >= before["gpu"]["free_mb"] - 128
        print(
            json.dumps(
                {
                    "job_id": job_id,
                    "telemetry": telemetry,
                    "free_mb_before": before["gpu"]["free_mb"],
                    "free_mb_after": after["gpu"]["free_mb"],
                    "events": len(events),
                    "sample_rate": rate,
                    "samples": len(samples),
                    "rms": float(np.sqrt(np.mean(samples**2))),
                    "lyrics_declaration": LYRICS_DECLARATION,
                },
                sort_keys=True,
            )
        )
