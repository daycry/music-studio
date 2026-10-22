"""Orquestación dentro del hijo; salida cruda sin persistencia de dominio."""

import hashlib
import json
import math
import os
from pathlib import Path

from engine_common import EngineError

from .descriptor import TASKS, model_root, read_lock, validate_language


def validate_words(words):
    if not isinstance(words, list) or not words:
        raise EngineError("INTERNAL", "Tiempos de alineación ausentes")
    previous = 0.0
    for word in words:
        start, end = word.get("start_s"), word.get("end_s")
        if (
            not isinstance(word.get("text"), str)
            or not word["text"]
            or not all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                for value in (start, end)
            )
            or start < previous
            or end < start
        ):
            raise EngineError("INTERNAL", "Tiempos de alineación inválidos")
        previous = end


class AnalysisAdapter:
    def __init__(self, backend=None, models_dir=None, data_dir=None):
        self.models_dir = Path(models_dir) if models_dir else model_root()
        self.data_dir = Path(data_dir or os.getenv("STUDIO_DATA_DIR", "/data"))
        if backend is None:
            from .backend import LocalBackend

            backend = LocalBackend(self.models_dir)
        self.backend = backend
        self.loaded_id = None
        self.mode = None
        self.cap_mb = self.total_mb = 0

    def load(self, model_id, mode, cap_mb, total_mb):
        if model_id not in TASKS:
            raise EngineError("MODEL_NOT_FOUND")
        if mode != ("cpu" if model_id == "beat-this" else "bf16"):
            raise EngineError("INVALID_PARAMS", "Modo no declarado")
        if self.loaded_id:
            self.backend.release()
            self.loaded_id = None
        self.backend.load(model_id, mode, cap_mb, total_mb)
        self.loaded_id, self.mode = model_id, mode
        self.cap_mb, self.total_mb = cap_mb, total_mb

    def generate(self, request, output_dir, emit, token):
        task, model_id = request["task"], request["model_id"]
        if TASKS.get(model_id) != task or request.get("n_outputs", 1) != 1:
            raise EngineError("INVALID_PARAMS", "Tarea o número de salidas inválido")
        audio_inputs = [item for item in request["inputs"] if item["role"] == "audio"]
        if len(audio_inputs) != 1:
            raise EngineError("INVALID_PARAMS", "Se requiere una entrada de audio")
        audio = (self.data_dir / audio_inputs[0]["path"]).resolve()
        if not audio.is_relative_to(self.data_dir.resolve()):
            raise EngineError("INVALID_PARAMS", "Entrada fuera de data")
        token.check()
        params = request.get("params", {})
        if task in {"audio.transcribe", "audio.align_lyrics"}:
            validate_language(params.get("language"))
        if self.loaded_id != model_id:
            self.load(
                model_id,
                "cpu" if model_id == "beat-this" else "bf16",
                self.cap_mb,
                self.total_mb,
            )
        emit(("stage", {"stage": "analyzing"}))
        analysis = self.backend.run(task, audio, params)
        stages = [{"task": task, "model_id": model_id}]
        token.check()
        if task == "audio.transcribe":
            if (
                not isinstance(analysis.get("text"), str)
                or not analysis["text"].strip()
                or not analysis.get("language")
            ):
                raise EngineError("INTERNAL", "Transcripción vacía o idioma ausente")
            self.backend.release()
            self.loaded_id = None
            token.check()
            aligner = "qwen3-forcedaligner-0.6b"
            emit(("stage", {"stage": "loading_aligner"}))
            self.load(aligner, "bf16", self.cap_mb, self.total_mb)
            aligned = self.backend.run(
                "audio.align_lyrics",
                audio,
                {"segments": analysis["segments"]}
                if "segments" in analysis
                else {"text": analysis["text"], "language": analysis["language"]},
            )
            validate_words(aligned.get("words"))
            analysis = {**analysis, "words": aligned["words"]}
            stages.append(
                {
                    "task": "audio.align_lyrics",
                    "model_id": aligner,
                    "text_source": "recognized_transcript",
                }
            )
        elif task == "audio.align_lyrics":
            validate_words(analysis.get("words"))
        lock = read_lock(self.models_dir)
        for stage in stages:
            entry = lock[stage["model_id"]]
            stage["revision"] = entry.get(
                "revision", entry.get("file", {}).get("sha256")
            )
        token.check()
        result = {"task": task, "analysis": analysis, "stages": stages}
        output = Path(output_dir) / "analysis.json"
        output.write_text(
            json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        return {
            "artifacts": [
                {
                    "output_index": 0,
                    "filename": output.name,
                    "media_type": "application/json",
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                    "meta": {"task": task},
                }
            ],
            "result": result,
            "vram_peak_mb": getattr(self.backend, "peak_mb", 0),
        }
