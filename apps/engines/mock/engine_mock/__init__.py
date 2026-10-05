"""Adapter sintético local: catálogo completo, sin GPU ni pesos externos."""

import json
import math
import os
import re
import struct
import subprocess
import wave
import zlib
from pathlib import Path

from engine_common import CpuGpu, EngineError, create_app
from engine_contract import ErrorCode, ModelDescriptor

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TASKS = [
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
]
FEATURES = [
    "timbre_ref",
    "lora",
    "negative_prompt",
    "bpm",
    "key",
    "lyrics",
    "style",
    "duration_s",
    "seed",
    "language",
    "instrumental",
    "reference_image",
    "resolution",
    "fps",
    "strength",
    "guidance_scale",
]


def media_type(task):
    if task.startswith("music.") or task == "audio.stems":
        return "audio/wav"
    if task.startswith("image."):
        return "image/png"
    if task.startswith("video."):
        return "video/mp4"
    if task == "text.generate":
        return "text/plain"
    if task == "train.lora":
        return "application/octet-stream"
    return "application/json"


def descriptor():
    schema = {
        "type": "object",
        "properties": {
            "duration_s": {"type": "number", "exclusiveMinimum": 0, "maximum": 600},
            "_mock": {"type": "object"},
        },
    }
    return ModelDescriptor(
        id="mock",
        family="mock",
        version="1",
        revision="synthetic-v1",
        license="All rights reserved",
        commercial_use=True,
        training_data="Sintético; sin datos de entrenamiento",
        provider={"type": "local"},
        weights=[],
        modes=[{"id": "cpu", "vram_mb": 0, "notes": "Sin GPU"}],
        tasks={
            task: {
                "verified": True,
                "device": "cpu",
                "params_schema": schema,
                "features": {feature: {"verified": True} for feature in FEATURES},
                "outputs": [{"media_type": media_type(task), "count": 1}],
                "limits": {"duration_s": [0.001, 600]},
            }
            for task in TASKS
        },
    )


def write_png(path):
    def chunk(kind, content):
        return (
            struct.pack(">I", len(content))
            + kind
            + content
            + struct.pack(">I", zlib.crc32(kind + content))
        )

    pixels = b"".join(
        b"\x00" + b"".join(bytes((x * 4, y * 4, 128)) for x in range(64))
        for y in range(64)
    )
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def write_audio(path, duration, token):
    count = round(duration * 48000)
    with wave.open(str(path), "wb") as output:
        output.setparams((2, 2, 48000, count, "NONE", "not compressed"))
        for start in range(0, count, 4096):
            token.check()
            frames = bytearray()
            for index in range(start, min(start + 4096, count)):
                t = index / 48000
                value = round(
                    6000
                    * math.sin(2 * math.pi * (220 * t + 440 * t * t / (2 * duration)))
                )
                frames.extend(struct.pack("<hh", value, value))
            output.writeframesraw(frames)


def write_video(path, duration, token):
    binary = next(
        iter(
            (PROJECT_ROOT / "tools" / "ffmpeg").glob(
                "*/bin/ffmpeg.exe" if os.name == "nt" else "*/bin/ffmpeg"
            )
        ),
        None,
    )
    if binary is None:
        raise EngineError("INTERNAL", "Falta el ffmpeg local verificado")
    command = [
        str(binary),
        "-v",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=blue:s=64x64:r=24",
        "-t",
        str(duration),
        "-c:v",
        "mpeg4",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    with subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) as process:
        try:
            while process.poll() is None:
                token.wait(0.02)
            if process.returncode:
                raise EngineError("INTERNAL", "No se pudo generar el vídeo sintético")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class MockAdapter:
    def __init__(self, stage_delay_ms=None):
        self.descriptor = descriptor()
        self.delay = (
            max(
                0,
                int(
                    os.environ.get("MOCK_STAGE_DELAY_MS", "10")
                    if stage_delay_ms is None
                    else stage_delay_ms
                ),
            )
            / 1000
        )
        self.seen = set()

    def load(self, model_id, mode, cap_mb, total_mb):
        if model_id != "mock":
            raise EngineError("MODEL_NOT_FOUND")
        if mode != "cpu":
            raise EngineError("INVALID_PARAMS")

    def generate(self, request, output, emit, token):
        params = request.get("params", {})
        task = request["task"]
        if task not in self.descriptor.tasks:
            raise EngineError("INVALID_PARAMS")
        prompt = str(params.get("style", params.get("prompt", "")))
        options = dict(params.get("_mock", {}))
        for key, value in re.findall(r"@mock:(fail_once|fail)=([A-Z_]+)", prompt):
            options[key] = value
        options["retryable"] = bool(
            options.get("retryable") or "@mock:retryable" in prompt
        )
        failure = options.get("fail")
        if options.get("fail_once") and prompt not in self.seen:
            self.seen.add(prompt)
            failure = options["fail_once"]
        if failure:
            code = (
                failure if failure in {e.value for e in ErrorCode} else "INVALID_PARAMS"
            )
            raise EngineError(code, retryable=options["retryable"])
        duration = float(params.get("duration_s", 1))
        if not 0 < duration <= 600:
            raise EngineError("INVALID_PARAMS")
        for stage in ("generating", "decoding"):
            token.check()
            emit(("stage", {"stage": stage}))
            token.wait(self.delay)
        if task == "text.generate":
            text = "[Verse]\nLorem ipsum canta al sol\n[Chorus]\nLa música vive en tu voz\n"
            for line in text.splitlines(keepends=True):
                token.check()
                emit(("delta", {"text": line}))
                token.wait(self.delay)
            return {"artifacts": [], "result": {"text": text}}
        artifacts = []
        count = request.get("n_outputs", 1)
        if task == "audio.stems":
            count *= 2
        for index in range(count):
            token.check()
            mime = media_type(task)
            extension = {
                "audio/wav": "wav",
                "image/png": "png",
                "video/mp4": "mp4",
                "application/json": "json",
                "application/octet-stream": "safetensors",
            }[mime]
            filename = f"output-{index}.{extension}"
            path = output / filename
            if mime == "audio/wav":
                write_audio(path, duration, token)
            elif mime == "image/png":
                write_png(path)
            elif mime == "video/mp4":
                write_video(path, duration, token)
            elif task == "train.lora":
                header = json.dumps(
                    {"mock": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}}
                ).encode()
                header += b" " * (-len(header) % 8)
                path.write_bytes(
                    struct.pack("<Q", len(header)) + header + struct.pack("<f", 0)
                )
            else:
                data = {
                    "beats": [i / 2 for i in range(math.ceil(duration * 2))],
                    "downbeats": [i * 2 for i in range(math.ceil(duration / 2))],
                    "bpm": 120,
                    "key": "C",
                    "text": "Lorem ipsum",
                    "words": [{"text": "Lorem", "start_s": 0, "end_s": duration}],
                    "score": 0.5,
                    "task": task,
                }
                path.write_text(json.dumps(data), encoding="utf-8")
            seed = request.get("seed")
            artifacts.append(
                {
                    "filename": filename,
                    "output_index": index,
                    "media_type": mime,
                    "meta": {"seed": seed + index if seed is not None else None},
                }
            )
            emit(("progress", {"fraction": (index + 1) / count, "output_index": index}))
        return {
            "artifacts": artifacts,
            "vram_peak_mb": float(params.get("_mock", {}).get("vram_peak_mb", 0)),
        }


def create_mock_app(
    *, token=None, data_dir=None, stage_delay_ms=None, gpu=None, margin_mb=None
):
    return create_app(
        [descriptor()],
        "engine_mock:MockAdapter",
        token=token,
        data_dir=data_dir,
        gpu=gpu or CpuGpu(),
        margin_mb=margin_mb,
        adapter_options={"stage_delay_ms": stage_delay_ms},
        engine_id="mock",
    )
