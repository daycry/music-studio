import hashlib
import json

import engine_analysis
import pytest
from engine_common import EngineError
from engine_common.runtime import CancelToken


def test_descriptors_declare_safe_models_cpu_beats_and_unverified_tasks():
    factory = getattr(engine_analysis, "descriptors", None)
    assert callable(factory), "Faltan los descriptores del engine"
    models = factory()
    tasks = {name: task for model in models for name, task in model.tasks.items()}
    assert set(tasks) == {
        "audio.transcribe",
        "audio.align_lyrics",
        "audio.clap",
        "audio.aesthetics",
        "audio.beats",
    }
    assert tasks["audio.beats"].device == "cpu"
    assert all(not task.verified for task in tasks.values())
    assert all(
        weight.format == "safetensors" for model in models for weight in model.weights
    )
    assert all(task.inputs[0].required for task in tasks.values())
    assert tasks["audio.clap"].params_schema["required"] == ["text"]


def test_transcription_descriptor_includes_aligner_dependency_weights():
    model = next(
        model for model in engine_analysis.descriptors() if model.id == "qwen3-asr-1.7b"
    )
    assert any(
        weight.path.startswith("qwen3-forcedaligner-0.6b/") for weight in model.weights
    ), "Falta declarar el peso del alineador secuencial"


def test_second_transcription_reloads_asr_after_releasing_aligner(tmp_path):
    backend = Backend()
    engine = adapter(backend)
    engine.load("qwen3-asr-1.7b", "bf16", 8000, 12000)
    engine.generate(
        request("audio.transcribe", "qwen3-asr-1.7b"),
        tmp_path,
        lambda e: None,
        CancelToken(),
    )
    backend.events.clear()
    engine.generate(
        request("audio.transcribe", "qwen3-asr-1.7b"),
        tmp_path,
        lambda e: None,
        CancelToken(),
    )
    assert backend.events[:2] == [
        ("release", "qwen3-forcedaligner-0.6b"),
        ("load", "qwen3-asr-1.7b"),
    ]


@pytest.mark.parametrize(
    "changes",
    [
        {"n_outputs": 2},
        {"task": "audio.beats"},
        {"inputs": []},
        {
            "inputs": [
                {"role": "audio", "path": "a.wav"},
                {"role": "audio", "path": "b.wav"},
            ]
        },
    ],
)
def test_adapter_rejects_invalid_task_and_audio_count(tmp_path, changes):
    backend = Backend()
    engine = adapter(backend)
    payload = {
        **request("audio.clap", "clap-larger-music", {"text": "music"}),
        **changes,
    }
    with pytest.raises(EngineError) as error:
        engine.generate(payload, tmp_path, lambda e: None, CancelToken())
    assert error.value.code == "INVALID_PARAMS"
    assert not backend.events


def test_preflight_rejects_multiple_outputs_and_extra_input_roles():
    from engine_analysis import server

    preflight = getattr(server, "preflight", None)
    assert callable(preflight), "Falta validación temprana de número de salidas y roles"
    for changes in [
        {"n_outputs": 2},
        {
            "inputs": [
                {"role": "audio", "path": "a.wav"},
                {"role": "image", "path": "b.png"},
            ]
        },
    ]:
        with pytest.raises(EngineError) as error:
            preflight(
                {
                    **request("audio.clap", "clap-larger-music", {"text": "music"}),
                    **changes,
                }
            )
        assert error.value.code == "INVALID_PARAMS"


class Backend:
    def __init__(self):
        self.events = []
        self.active = None

    def load(self, model_id, mode, cap_mb, total_mb):
        assert self.active is None, "Dos modelos residentes"
        self.events.append(("load", model_id))
        self.active = model_id

    def release(self):
        self.events.append(("release", self.active))
        self.active = None

    def run(self, task, audio, params):
        self.events.append(("run", task, dict(params)))
        return {
            "audio.transcribe": {"text": "hola mundo", "language": "Spanish"},
            "audio.align_lyrics": {
                "words": [
                    {"text": "hola", "start_s": 0.1, "end_s": 0.3},
                    {"text": "mundo", "start_s": 0.4, "end_s": 0.8},
                ]
            },
            "audio.clap": {"score": 0.42, "text_tokens": 4, "text_truncated": False},
            "audio.aesthetics": {"CE": 3.0, "CU": 4.0, "PC": 5.0, "PQ": 6.0},
            "audio.beats": {
                "bpm": 120.0,
                "beats_s": [0.0, 0.5, 1.0],
                "downbeats_s": [0.0],
            },
        }[task]


def adapter(backend):
    factory = getattr(engine_analysis, "AnalysisAdapter", None)
    assert callable(factory), "Falta el adaptador de análisis"
    return factory(backend=backend)


def request(task, model_id, params=None):
    return {
        "task": task,
        "model_id": model_id,
        "params": params or {},
        "inputs": [{"role": "audio", "path": "fixture.wav"}],
        "n_outputs": 1,
    }


@pytest.mark.parametrize(
    "task,model_id,key",
    [
        ("audio.clap", "clap-larger-music", "score"),
        ("audio.aesthetics", "audiobox-aesthetics", "PQ"),
        ("audio.beats", "beat-this", "bpm"),
    ],
)
def test_analysis_returns_raw_json_artifact(tmp_path, task, model_id, key):
    engine = adapter(Backend())
    engine.load(model_id, "cpu" if task == "audio.beats" else "bf16", 8000, 12000)
    result = engine.generate(
        request(task, model_id, {"text": "music"} if task == "audio.clap" else {}),
        tmp_path,
        lambda e: None,
        CancelToken(),
    )
    artifact = result["artifacts"][0]
    output = tmp_path / "analysis.json"
    assert artifact["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert key in json.loads(output.read_text())["analysis"]
    assert artifact["media_type"] == "application/json"


def test_transcription_releases_asr_before_aligning_recognized_text(tmp_path):
    backend = Backend()
    engine = adapter(backend)
    engine.load("qwen3-asr-1.7b", "bf16", 8000, 12000)
    result = engine.generate(
        request("audio.transcribe", "qwen3-asr-1.7b"),
        tmp_path,
        lambda e: None,
        CancelToken(),
    )
    assert backend.events[:4] == [
        ("load", "qwen3-asr-1.7b"),
        ("run", "audio.transcribe", {}),
        ("release", "qwen3-asr-1.7b"),
        ("load", "qwen3-forcedaligner-0.6b"),
    ]
    assert backend.events[4][2] == {"text": "hola mundo", "language": "Spanish"}
    assert result["result"]["analysis"]["text"] == "hola mundo"
    assert len(result["result"]["analysis"]["words"]) == 2
    assert engine.loaded_id == "qwen3-forcedaligner-0.6b"


def test_invalid_alignment_is_explicit_error(tmp_path):
    backend = Backend()
    original = backend.run
    backend.run = lambda task, audio, params: (
        {"words": [{"text": "hola", "start_s": 2, "end_s": 1}]}
        if task == "audio.align_lyrics"
        else original(task, audio, params)
    )
    engine = adapter(backend)
    engine.load("qwen3-asr-1.7b", "bf16", 8000, 12000)
    with pytest.raises(EngineError) as error:
        engine.generate(
            request("audio.transcribe", "qwen3-asr-1.7b"),
            tmp_path,
            lambda e: None,
            CancelToken(),
        )
    assert "Tiempos" in error.value.message
    assert not (tmp_path / "analysis.json").exists()
