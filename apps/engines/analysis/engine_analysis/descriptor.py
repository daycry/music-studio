"""Capacidades conservadoras, siempre derivadas del lock local."""

import json
from pathlib import Path

from engine_common import EngineError
from engine_contract import ModelDescriptor

# Lista del commit Qwen fijado; esta validación ligera no importa torch en HTTP.
LANGUAGES = (
    "Chinese",
    "English",
    "Cantonese",
    "Arabic",
    "German",
    "French",
    "Spanish",
    "Portuguese",
    "Indonesian",
    "Italian",
    "Korean",
    "Russian",
    "Thai",
    "Vietnamese",
    "Japanese",
    "Turkish",
    "Hindi",
    "Malay",
    "Dutch",
    "Swedish",
    "Danish",
    "Finnish",
    "Polish",
    "Czech",
    "Filipino",
    "Persian",
    "Greek",
    "Romanian",
    "Hungarian",
    "Macedonian",
)


def validate_language(language):
    if language is not None and language not in LANGUAGES:
        raise EngineError("INVALID_PARAMS", "Idioma no soportado")


TASKS = {
    "qwen3-asr-1.7b": "audio.transcribe",
    "qwen3-forcedaligner-0.6b": "audio.align_lyrics",
    "clap-larger-music": "audio.clap",
    "audiobox-aesthetics": "audio.aesthetics",
    "beat-this": "audio.beats",
}


def model_root():
    return (
        Path("/models")
        if Path("/.dockerenv").is_file()
        else Path(__file__).resolve().parents[4] / "models"
    )


def read_lock(root=None):
    return json.loads(((root or model_root()) / "models.lock.json").read_text())[
        "models"
    ]


def descriptors(root=None):
    lock = read_lock(root)
    result = []
    for model_id, task in TASKS.items():
        entry = lock[model_id]
        files = entry.get("files", [entry.get("file")])
        weights = []
        for file in files:
            safe = file.get("converted", file)
            if file["format"] == "safetensors" or "converted" in file:
                weights.append(
                    {
                        "path": f"{model_id}/{safe.get('dest', file['path'])}",
                        "sha256": safe["sha256"],
                        "bytes": safe["bytes"],
                        "format": "safetensors",
                    }
                )
        properties = {}
        if task == "audio.transcribe":
            dependency = "qwen3-forcedaligner-0.6b"
            for file in lock[dependency]["files"]:
                if file["format"] == "safetensors":
                    weights.append(
                        {
                            "path": f"{dependency}/{file['path']}",
                            "sha256": file["sha256"],
                            "bytes": file["bytes"],
                            "format": "safetensors",
                        }
                    )
        required = []
        if task in {"audio.clap", "audio.align_lyrics"}:
            properties["text"] = {"type": "string", "minLength": 1, "maxLength": 32768}
            required.append("text")
        if task in {"audio.transcribe", "audio.align_lyrics"}:
            properties["language"] = {"type": "string", "enum": list(LANGUAGES)}
        if task == "audio.align_lyrics":
            required.append("language")
        cpu = task == "audio.beats"
        result.append(
            ModelDescriptor(
                id=model_id,
                family="analysis",
                version="1",
                revision=entry.get(
                    "revision", entry["file"]["sha256"] if "file" in entry else ""
                ),
                license=entry["license"],
                commercial_use=True,
                training_data="Según la ficha del proveedor fijada en el lock; no auditado independientemente.",
                provider={"type": "local"},
                weights=weights,
                modes=[
                    {
                        "id": "cpu" if cpu else "bf16",
                        "notes": "Pendiente de medición real",
                    }
                ],
                tasks={
                    task: {
                        "verified": False,
                        "device": "cpu" if cpu else "gpu",
                        "params_schema": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                            "additionalProperties": False,
                        },
                        "inputs": [
                            {
                                "role": "audio",
                                "media_types": ["audio/wav", "audio/flac"],
                                "required": True,
                            }
                        ],
                        "outputs": [{"media_type": "application/json", "count": 1}],
                        "limits": {
                            "duration_s": [
                                0,
                                180 if task == "audio.align_lyrics" else 600,
                            ]
                        },
                    }
                },
            )
        )
    return result
