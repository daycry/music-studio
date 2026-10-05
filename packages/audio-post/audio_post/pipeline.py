"""Master sin normalizar y escucha medida después de codificar."""

import hashlib
import json
import math
import re
import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path

import pyloudnorm as pyln
import soundfile as sf

from . import make_peaks, validate_audio
from .manifest import safe_path


@contextmanager
def _staging_directory(destination):
    # Inherit the destination ACL on Windows, including restricted local runtimes.
    staging = destination / (".post-" + uuid.uuid4().hex)
    staging.mkdir()
    try:
        yield staging
    finally:
        for filename in ("master.flac", "listen.mp3", "peaks.json"):
            (staging / filename).unlink(missing_ok=True)
        staging.rmdir()


def _ffmpeg(binary, args):
    result = subprocess.run(
        [str(binary), "-nostdin", "-hide_banner", *args],
        capture_output=True,
        timeout=300,
        check=False,
    )
    if result.returncode:
        raise ValueError("AUDIO_TRANSCODE_FAILED")
    return result


def measure_audio(path, *, ffmpeg):
    samples, sr = sf.read(path, dtype="float64", always_2d=True)
    loudness = float(pyln.Meter(sr).integrated_loudness(samples))
    result = _ffmpeg(
        ffmpeg, ["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]
    )
    matches = re.findall(
        r"Peak:\s+(-?\d+(?:\.\d+)?) dBFS",
        result.stderr.decode("utf-8", errors="replace"),
    )
    if not matches or not math.isfinite(loudness):
        raise ValueError("AUDIO_MEASUREMENT_FAILED")
    return {"lufs": loudness, "true_peak_dbtp": float(matches[-1])}


def process_audio(source, destination, *, expected_duration_s, ffmpeg):
    source, destination = Path(source), Path(destination)
    root = Path(__file__).resolve().parents[3]
    if not source.absolute().is_relative_to(
        root
    ) or not destination.absolute().is_relative_to(root):
        raise ValueError("UNSAFE_PATH")
    source = safe_path(root, source.absolute().relative_to(root).as_posix())
    destination = safe_path(root, destination.absolute().relative_to(root).as_posix())
    samples, sr = sf.read(source, dtype="float64", always_2d=True)
    meta = validate_audio(samples, sr, expected_duration_s)
    if sr not in (32000, 44100, 48000):
        listen_sr = 48000
    else:
        listen_sr = sr
    loudness = float(pyln.Meter(sr).integrated_loudness(samples))
    if not math.isfinite(loudness):
        raise ValueError("AUDIO_MEASUREMENT_FAILED")
    gain_db = -14 - loudness
    limiter = False
    ceiling_db = -1.5
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with _staging_directory(destination) as staging:
            staging = Path(staging)
            master = staging / "master.flac"
            listen = staging / "listen.mp3"
            sf.write(master, samples, sr, format="FLAC", subtype="PCM_24")
            for _ in range(16):
                filters = [f"volume={gain_db:.8f}dB"]
                if limiter:
                    filters.append(
                        f"alimiter=limit={10 ** (ceiling_db / 20):.8f}:level=false:latency=true"
                    )
                if listen_sr != sr:
                    filters.append("aresample=resampler=soxr")
                _ffmpeg(
                    ffmpeg,
                    [
                        "-v",
                        "error",
                        "-y",
                        "-i",
                        str(master),
                        "-af",
                        ",".join(filters),
                        "-ar",
                        str(listen_sr),
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "320k",
                        str(listen),
                    ],
                )
                measured = measure_audio(listen, ffmpeg=ffmpeg)
                delta = -14 - measured["lufs"]
                if abs(delta) <= 0.5 and measured["true_peak_dbtp"] <= -1.0:
                    break
                if measured["true_peak_dbtp"] > -1.0:
                    if limiter:
                        ceiling_db -= max(0.3, measured["true_peak_dbtp"] + 1.1)
                    limiter = True
                gain_db += delta
            else:
                raise ValueError("AUDIO_TARGET_UNREACHABLE")
            peaks = staging / "peaks.json"
            peaks.write_text(
                json.dumps(make_peaks(samples), allow_nan=False) + "\n",
                encoding="utf-8",
            )
            outputs = []
            for filename, media_type, role in [
                ("master.flac", "audio/flac", "master"),
                ("listen.mp3", "audio/mpeg", "listen"),
                ("peaks.json", "application/json", "peaks"),
            ]:
                path = staging / filename
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                asset_meta = dict(meta) if role != "peaks" else {}
                if role == "listen":
                    asset_meta.update(
                        sample_rate=listen_sr,
                        lufs=measured["lufs"],
                        true_peak=measured["true_peak_dbtp"],
                    )
                outputs.append(
                    {
                        "role": role,
                        "path": filename,
                        "media_type": media_type,
                        "sha256": digest,
                        "bytes": path.stat().st_size,
                        "meta": asset_meta,
                    }
                )
            for output in outputs:
                (staging / output["path"]).rename(destination / output["path"])
        return {
            "outputs": outputs,
            "post": {
                "lufs_in": loudness,
                "lufs_out": measured["lufs"],
                "gain_db": gain_db,
                "limiter": limiter,
                "true_peak_dbtp": measured["true_peak_dbtp"],
            },
        }
    except BaseException:
        for name in ("master.flac", "listen.mp3", "peaks.json"):
            (destination / name).unlink(missing_ok=True)
        destination.rmdir()
        raise
