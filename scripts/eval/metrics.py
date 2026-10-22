"""Medidas CPU y staging /v1; sin torch ni aceptación musical automática."""

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

from scripts import input_preparation as preparation

LANGUAGES = {"es": "Spanish", "en": "English"}
NORMALIZATION = "NFC-casefold-punctuation-to-space-preserve-accents-v1"
_FFMPEG_CACHE = {}


def confined(path, root):
    return preparation.safe_path(Path(root).absolute(), Path(path).absolute())


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def exclusive_json(path, value):
    """Publicación completa y exclusiva; nunca JSON parcial ni sobrescritura."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / (".pending-" + os.urandom(16).hex())
    try:
        with temporary.open("xb") as stream:
            stream.write(preparation.encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def words(text, *, reference=False):
    if reference:
        text = re.sub(r"(?m)^\s*(?:\*\*)?\[[^\]\r\n]+\](?:\*\*)?\s*$", "", text)
    text = unicodedata.normalize("NFC", text).casefold()
    return "".join(c if c.isalnum() or c.isspace() else " " for c in text).split()


def wer(reference, transcript, *, language, floor=None):
    if language not in LANGUAGES:
        raise ValueError("LANGUAGE_UNSUPPORTED")
    expected, actual = words(reference, reference=True), words(transcript)
    if not expected:
        raise ValueError("WER_REFERENCE_EMPTY")
    previous = list(range(len(actual) + 1))
    for i, word in enumerate(expected, 1):
        current = [i]
        for j, heard in enumerate(actual, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (word != heard))
            )
        previous = current
    raw = previous[-1] / len(expected)
    if floor is not None and (
        type(floor) not in {int, float} or not math.isfinite(floor) or floor < 0
    ):
        raise ValueError("WER_FLOOR_INVALID")
    return {
        "raw": raw,
        "adjusted": max(0, raw - floor) if floor is not None else None,
        "floor_status": "MEASURED" if floor is not None else "PENDING",
        "floor": floor,
        "edits": previous[-1],
        "reference_words": len(expected),
        "normalization": NORMALIZATION,
        "language": language,
        "acceptance": None,
    }


def audio_record(path, *, expected_duration=None):
    pcm, rate = sf.read(path, dtype="float32", always_2d=True)
    if not pcm.size or rate != 48000 or pcm.shape[1] != 2 or not np.isfinite(pcm).all():
        raise ValueError("PCM_INVALID")
    duration = len(pcm) / rate
    if expected_duration is not None and abs(duration - expected_duration) > 0.05:
        raise ValueError("AUDIO_DURATION_MISMATCH")
    peak = float(np.max(np.abs(pcm)))
    return {
        "sha256": file_hash(path),
        "bytes": Path(path).stat().st_size,
        "frames": len(pcm),
        "sample_rate": rate,
        "channels": 2,
        "duration_s": duration,
        "finite": True,
        "pcm_sha256": hashlib.sha256(pcm.astype("<f4").tobytes()).hexdigest(),
        "peak": peak,
        "over_fullscale": int(np.sum(np.abs(pcm) > 1)),
        "fullscale": int(np.sum(np.abs(pcm) == 1)),
        "silent": peak == 0,
        "blind_ready": False,
    }


def linear_gain(pcm, *, measured_lufs, measured_dbtp, target=-16):
    pcm = np.asarray(pcm, dtype=np.float32)
    if (
        pcm.ndim != 2
        or pcm.shape[1] != 2
        or not pcm.size
        or not np.isfinite(pcm).all()
        or np.max(np.abs(pcm)) > 1
    ):
        raise ValueError("PCM_INVALID")
    if not np.any(pcm) or not all(
        math.isfinite(v) for v in (measured_lufs, measured_dbtp, target)
    ):
        raise ValueError("LOUDNESS_UNMEASURABLE")
    gain = target - measured_lufs
    receipt = {
        "gain_db": gain,
        "gain_factor": 10 ** (gain / 20),
        "target_lufs": target,
        "raw_lufs": measured_lufs,
        "raw_dbtp": measured_dbtp,
        "predicted_dbtp": measured_dbtp + gain,
        "policy": "single_fixed_linear_gain",
    }
    if measured_dbtp + gain > -1:
        return pcm.copy(), dict(receipt, status="PEAK_CONFLICT")
    scaled = pcm * receipt["gain_factor"]
    if not np.isfinite(scaled).all() or np.max(np.abs(scaled)) > 1:
        return pcm.copy(), dict(receipt, status="PEAK_CONFLICT")
    return scaled.astype(np.float32), dict(receipt, status="SCALED_PENDING_MEASUREMENT")


def verified_ffmpeg(root):
    """Sin descarga: contrasta binario con ZIP fijado, SHA y versión."""
    root = Path(root).absolute()
    lock_path = confined(root / "tools/tools.lock.json", root)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))["tools"]["ffmpeg"]
    archive = confined(root / ".cache/fetch" / lock["asset"], root)
    if not archive.is_file() or archive.stat().st_size != lock["bytes"]:
        raise ValueError("FFMPEG_VERIFIED_ARCHIVE_REQUIRED")
    archive_sha256 = file_hash(archive)
    if archive_sha256 != lock["sha256"]:
        raise ValueError("FFMPEG_VERIFIED_ARCHIVE_REQUIRED")
    cache_key = str(root)
    cached = _FFMPEG_CACHE.get(cache_key)
    if (
        cached
        and cached["lock_path"] == lock_path
        and cached["lock"] == lock
        and cached["lock_signature"] == _ffmpeg_stat_signature(lock_path)
        and cached["archive_path"] == archive
        and archive.is_file()
        and cached["archive_signature"] == _ffmpeg_stat_signature(archive)
        and cached["binary_path"].is_file()
        and cached["binary_signature"] == _ffmpeg_stat_signature(cached["binary_path"])
    ):
        if file_hash(cached["binary_path"]) != cached["tool"]["sha256"]:
            raise ValueError("FFMPEG_HASH_MISMATCH")
        return cached["binary_path"], dict(cached["tool"])
    name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    with zipfile.ZipFile(archive) as bundle:
        names = [n for n in bundle.namelist() if n.endswith("/bin/" + name)]
        if len(names) != 1:
            raise ValueError("FFMPEG_BINARY_INVALID")
        binary = confined(root / lock["dest"] / names[0], root)
        expected = hashlib.sha256(bundle.read(names[0])).hexdigest()
    if not binary.is_file() or file_hash(binary) != expected:
        raise ValueError("FFMPEG_HASH_MISMATCH")
    version = subprocess.run(
        [str(binary), "-version"],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    ).stdout
    if (
        "51c4a23d74" not in version
        or "--enable-gpl" in version
        or "--enable-nonfree" in version
    ):
        raise ValueError("FFMPEG_VERSION_MISMATCH")
    tool = {
        "sha256": expected,
        "archive_sha256": lock["sha256"],
        "version": version.splitlines()[0],
    }
    _FFMPEG_CACHE[cache_key] = {
        "lock_path": lock_path,
        "lock": dict(lock),
        "lock_signature": _ffmpeg_stat_signature(lock_path),
        "archive_path": archive,
        "archive_signature": _ffmpeg_stat_signature(archive),
        "binary_path": binary,
        "binary_signature": _ffmpeg_stat_signature(binary),
        "tool": tool,
    }
    return binary, dict(tool)


def _ffmpeg_stat_signature(path):
    """Firma barata para invalidar el caché si cambia la instalación fijada."""
    stat = Path(path).stat()
    return (stat.st_size, stat.st_mtime_ns, getattr(stat, "st_ino", 0))


def loudness(path, binary):
    command = [
        str(binary),
        "-nostdin",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        "ebur128=peak=true",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=300, check=True
    )
    integrated = re.findall(r"I:\s*(-?\d+(?:\.\d+)?) LUFS", result.stderr)
    peaks = re.findall(r"Peak:\s*(-?\d+(?:\.\d+)?) dBFS", result.stderr)
    if not integrated or not peaks:
        raise ValueError("LOUDNESS_MEASUREMENT_INVALID")
    return {
        "lufs": float(integrated[-1]),
        "dbtp": float(peaks[-1]),
        "argv": command,
        "exit_code": result.returncode,
        "stderr": result.stderr,
    }


def normalize_audio(source, destination, *, root):
    source, destination = confined(source, root), confined(destination, root)
    record = audio_record(source)
    if record["silent"] or record["over_fullscale"]:
        raise ValueError("AUDIO_NOT_BLIND_READY")
    binary, tool = verified_ffmpeg(root)
    before = loudness(source, binary)
    pcm, _ = sf.read(source, dtype="float32", always_2d=True)
    scaled, gain = linear_gain(
        pcm, measured_lufs=before["lufs"], measured_dbtp=before["dbtp"]
    )
    receipt = {
        "raw": record,
        "tool": tool,
        "before": before,
        "gain": gain,
        "blind_ready": False,
    }
    if gain["status"] == "PEAK_CONFLICT":
        return receipt
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        sf.write(stream, scaled, 48000, format="WAV", subtype="FLOAT")
    after = loudness(destination, binary)
    receipt.update(after=after, scaled=audio_record(destination))
    receipt["blind_ready"] = (
        abs(after["lufs"] + 16) <= 0.2
        and after["dbtp"] <= -1
        and not receipt["scaled"]["over_fullscale"]
    )
    receipt["gain"]["status"] = (
        "VERIFIED" if receipt["blind_ready"] else "MEASUREMENT_INCOMPATIBLE"
    )
    if file_hash(source) != record["sha256"]:
        raise ValueError("HASH_MISMATCH")
    return receipt


def stage_audio(source, data, job_id, *, root):
    if not re.fullmatch(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", job_id):
        raise ValueError("JOB_ID_INVALID")
    source, data = confined(source, root), confined(data, root)
    target = confined(data / f"tmp/{job_id}/in/audio.wav", root)
    digest = file_hash(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, target.open("xb") as copied:
        shutil.copyfileobj(original, copied)
    if file_hash(target) != digest or file_hash(source) != digest:
        raise ValueError("HASH_MISMATCH")
    return {
        "role": "audio",
        "path": f"tmp/{job_id}/in/audio.wav",
        "sha256": digest,
        "media_type": "audio/wav",
    }


def measure_floor(rows, *, root, model_id, profile):
    if len(rows) not in {2, 3}:
        raise ValueError("REAL_SUNG_GT_REQUIRED")
    measures, bindings = [], []
    for row in rows:
        if (
            row.get("synthetic") is not False
            or row.get("sung") is not True
            or row.get("rights") not in {"own", "public_domain", "licensed"}
            or row.get("gt_declared") is not True
        ):
            raise ValueError("REAL_SUNG_GT_REQUIRED")
        if (
            row.get("model_id") != model_id
            or row.get("profile") != profile
            or row.get("coverage") != "whole_recording"
        ):
            raise ValueError("FLOOR_PROFILE_MISMATCH")
        binding = {}
        for field in ("audio", "ground_truth", "transcript"):
            path = confined(Path(root) / row[field]["path"], root)
            if file_hash(path) != row[field]["sha256"]:
                raise ValueError("HASH_MISMATCH")
            binding[field] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
        audio = audio_record(confined(Path(root) / row["audio"]["path"], root))
        if audio["silent"] or audio["over_fullscale"]:
            raise ValueError("PCM_INVALID")
        binding["audio"].update(audio)
        ref = confined(Path(root) / row["ground_truth"]["path"], root).read_text(
            encoding="utf-8"
        )
        heard = confined(Path(root) / row["transcript"]["path"], root).read_text(
            encoding="utf-8"
        )
        measures.append(wer(ref, heard, language=row["language"])["raw"])
        bindings.append(binding)
    if len({b["audio"]["sha256"] for b in bindings}) != len(rows):
        raise ValueError("FLOOR_RECORDINGS_NOT_DISTINCT")
    return {
        # Bytes and row declarations cannot establish rights, real singing or ASR
        # execution. No controlled real-corpus attestation is implemented yet.
        "status": "PENDING",
        "reason": "CONTROLLED_REAL_CORPUS_EXECUTION_REQUIRED",
        "mean": None,
        "per_recording": measures,
        "model_id": model_id,
        "profile": profile,
        "bindings": bindings,
        "normalization": NORMALIZATION,
    }


def metric_request(task, *, language, style):
    if language not in LANGUAGES:
        raise ValueError("LANGUAGE_UNSUPPORTED")
    if task == "audio.transcribe":
        return {"language": LANGUAGES[language]}
    if task == "audio.clap" and style.strip():
        return {"text": style}
    if task == "audio.aesthetics":
        return {}
    raise ValueError("METRIC_TASK_INVALID")


def native_metric(task, payload, *, reference, language, floor=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("analysis"), dict):
        raise ValueError("METRIC_OUTPUT_INVALID")  # noqa: TRY004 - ValueError preserves the bounded metric validation contract.
    analysis = payload["analysis"]
    if task == "audio.transcribe":
        if not isinstance(analysis.get("text"), str) or not analysis.get("language"):
            raise ValueError("TRANSCRIPT_INVALID")
        return {
            "wer": wer(reference, analysis["text"], language=language, floor=floor),
            "native": payload,
        }
    if task == "audio.clap":
        if (
            type(analysis.get("score")) not in {int, float}
            or not math.isfinite(analysis["score"])
            or analysis.get("text_truncated") is not False
            or analysis.get("audio_window_s") != 10
        ):
            raise ValueError("CLAP_OUTPUT_INVALID")
        return {
            "clap": analysis["score"],
            "native": payload,
            "window_s": 10,
            "window_policy": "rand_trunc",
            "seed_controlled": False,
            "whole_track_score": False,
        }
    if task == "audio.aesthetics":
        axes = {axis: analysis.get(axis) for axis in ("PQ", "PC", "CE", "CU")}
        if not all(type(v) in {int, float} and math.isfinite(v) for v in axes.values()):
            raise ValueError("AESTHETICS_OUTPUT_INVALID")
        return {"audiobox": axes, "native": payload}
    raise ValueError("METRIC_TASK_INVALID")
