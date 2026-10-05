"""Descriptor conservador; las capacidades esperan validación de T-10."""

import json
import os
from pathlib import Path

from engine_contract import ModelDescriptor

MODEL_ID = "ace-step-1.5-turbo"
CHECKPOINT = "acestep-v15-turbo"
LM = "acestep-5Hz-lm-0.6B"
TRAINING_DATA = (
    "Professionally licensed music tracks.\n"
    "A vast collection of public domain and royalty-free music.\n"
    "High-quality audio generated via advanced MIDI-to-Audio conversion."
)


def model_root():
    return (
        Path("/models")
        if Path("/.dockerenv").is_file()
        else Path(__file__).resolve().parents[3] / "models"
    )


def locked_model(lock_path=None):
    return json.loads(Path(lock_path or model_root() / "models.lock.json").read_text())[
        "models"
    ]["ace-step-1.5"]


def descriptor(lock_path=None, checkpoint=None, lm=None):
    checkpoint = checkpoint or os.getenv("STUDIO_ACESTEP_CHECKPOINT", CHECKPOINT)
    lm = lm or os.getenv("STUDIO_ACESTEP_LM", LM)
    lock = locked_model(lock_path)
    components = {c["id"]: c for c in lock["components"]}
    selected = [
        components[name] for name in (checkpoint, lm, "vae", "Qwen3-Embedding-0.6B")
    ]
    weights = []
    remote_code = []
    for component in selected:
        for file in component["files"]:
            if file["format"] == "remote_code":
                remote_code.append(
                    {
                        "path": f"ace-step-1.5/checkpoints/{component['dest_subdir']}/{file['path']}",
                        "sha256": file["sha256"],
                    }
                )
            safe = file.get("converted", file)
            fmt = "safetensors" if "converted" in file else file["format"]
            if fmt in {"safetensors", "gguf", "onnx"}:
                weights.append(
                    {
                        "path": f"ace-step-1.5/checkpoints/{component['dest_subdir']}/{safe.get('dest', file['path'])}",
                        "sha256": safe["sha256"],
                        "bytes": safe["bytes"],
                        "format": fmt,
                    }
                )
    properties = {
        "style": {"type": "string", "minLength": 1, "maxLength": 16384},
        "lyrics": {"type": "string", "maxLength": 32768},
        "duration_s": {"type": "number", "minimum": 10, "maximum": 600},
        "language": {"type": "string", "minLength": 1},
        "vocal_language": {"type": "string", "minLength": 1},
        "bpm": {"type": "integer", "minimum": 30, "maximum": 300},
        "shift": {"type": "number", "minimum": 1, "maximum": 5},
        "key": {"type": "string"},
        "time_signature": {
            "type": "string",
            "pattern": "^[1-9][0-9]?/(1|2|4|8|16|32)$",
        },
        "negative_prompt": {"type": "string"},
    }
    return ModelDescriptor(
        id=MODEL_ID,
        family="ace-step",
        version="1.5",
        revision=components[checkpoint]["revision"],
        license="MIT",
        commercial_use=True,
        training_data=TRAINING_DATA,
        provider={"type": "local"},
        weights=weights,
        remote_code=remote_code,
        modes=[
            {
                "id": mode,
                "notes": "BF16, PT/SDPA, sin INT8 ni compile; VRAM pendiente de medición",
            }
            for mode in ("bf16", "offload")
        ],
        tasks={
            task: {
                "verified": False,
                "checkpoint": checkpoint,
                "device": "gpu",
                "params_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": ["style", "duration_s"]
                    + (["lyrics", "language"] if task == "music.song" else []),
                    "additionalProperties": False,
                },
                "features": {
                    feature: {"verified": False}
                    for feature in (
                        "negative_prompt",
                        "bpm",
                        "key",
                        "timbre_ref",
                        "lora",
                    )
                },
                "outputs": [{"media_type": "audio/wav", "count": 1}],
                "limits": {"duration_s": [10, 600], "languages_tested": []},
            }
            for task in ("music.song", "music.instrumental")
        },
    )
