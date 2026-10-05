import json
from pathlib import Path

import audio_post
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
FFMPEG = (
    ROOT / "tools/ffmpeg/ffmpeg-n9.0.2-10-g51c4a23d74-win64-lgpl-9.0/bin/ffmpeg.exe"
)


def invoke(name, *args, **kwargs):
    return getattr(audio_post, name, lambda *a, **kw: {})(*args, **kwargs)


def signal(sr=48000, seconds=3):
    t = np.arange(sr * seconds) / sr
    return np.column_stack([0.12 * np.sin(2 * np.pi * 440 * t)] * 2)


def test_validation():
    result = invoke("validate_audio", signal(), 48000, 3)
    assert result.get("duration_s") == 3.0
    for samples, sr, duration, code in [
        (signal(), 48000, 6, "AUDIO_DURATION"),
        (np.full((48000, 2), np.nan), 48000, 1, "AUDIO_NONFINITE"),
        (np.full((48000, 2), np.inf), 48000, 1, "AUDIO_NONFINITE"),
        (np.zeros((48000, 2)), 48000, 1, "AUDIO_SILENCE"),
        (np.ones((48000, 2)), 48000, 1, "AUDIO_CLIPPING"),
    ]:
        with pytest.raises(ValueError, match=code):
            invoke("validate_audio", samples, sr, duration)


@pytest.mark.parametrize("sample_rate", [float("nan"), float("inf"), 48000.5, True])
def test_invalid_sample_rate(sample_rate):
    with pytest.raises(ValueError, match="AUDIO_SHAPE"):
        audio_post.validate_audio(signal(), sample_rate, 3)


def test_master_and_listen(tmp_path):
    import subprocess

    source = tmp_path / "raw.wav"
    subprocess.run(
        [
            str(FFMPEG),
            "-v",
            "error",
            "-f",
            "f64le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-i",
            "pipe:0",
            "-c:a",
            "pcm_f32le",
            str(source),
        ],
        input=signal().astype("<f8").tobytes(),
        check=True,
    )
    dest = tmp_path / "take"
    result = invoke("process_audio", source, dest, expected_duration_s=3, ffmpeg=FFMPEG)
    assert (dest / "master.flac").exists()
    import soundfile as sf

    assert sf.info(dest / "master.flac").subtype == "PCM_24"
    master, sr = sf.read(dest / "master.flac", always_2d=True)
    assert sr == 48000
    assert np.max(np.abs(master - signal())) < 2**-22
    assert abs(result["post"]["lufs_out"] + 14) <= 0.5
    assert result["post"]["true_peak_dbtp"] <= -1
    measured = audio_post.measure_audio(dest / "listen.mp3", ffmpeg=FFMPEG)
    assert abs(measured["lufs"] + 14) <= 0.5
    assert measured["true_peak_dbtp"] <= -1
    with pytest.raises(FileExistsError):
        audio_post.process_audio(source, dest, expected_duration_s=3, ffmpeg=FFMPEG)
    # Verify the complete real post-process directory, including peaks.json.
    import importlib.util

    manifest = json.loads(
        (ROOT / "packages/contracts/examples/audio_take.json").read_text()
    )
    manifest["outputs"] = result["outputs"]
    manifest["post"] = result["post"]
    audio_post.write_manifest(dest / "manifest.json", manifest)
    spec = importlib.util.spec_from_file_location(
        "verify_manifest_cli", ROOT / "scripts/verify_manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main([str(dest)]) == 0
    with (dest / "listen.mp3").open("ab") as stream:
        stream.write(b"tampered")
    assert module.main([str(dest)]) == 1


def test_peaks():
    peaks = invoke("make_peaks", signal())
    assert len(peaks.get("data", [])) == 2
    assert len(peaks["data"][0]) == 2000
    assert peaks["data"][0][0][0] == pytest.approx(float(signal()[:72, 0].min()))
    assert peaks["data"][0][0][1] == pytest.approx(float(signal()[:72, 0].max()))


def test_manifest_writer(tmp_path):
    manifest = (
        json.loads((ROOT / "packages/contracts/examples/cli_run.json").read_text())
        if (ROOT / "packages/contracts/examples/cli_run.json").exists()
        else {}
    )
    (tmp_path / "fixture.txt").write_bytes(b"music-studio fixture\n")
    result = invoke("write_manifest", tmp_path / "manifest.json", manifest)
    assert result.get("commercial_use") is True
    assert (tmp_path / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        audio_post.write_manifest(tmp_path / "manifest.json", manifest)
    manifest["tools"][0]["commercial_use"] = False
    result = audio_post.write_manifest(tmp_path / "restricted.json", manifest)
    assert result["commercial_use"] is False


def test_manifest_verification(tmp_path):
    import hashlib

    fixture = ROOT / "packages/contracts/examples/cli_run.json"
    manifest = json.loads(fixture.read_text()) if fixture.exists() else {}
    payload = tmp_path / "output.flac"
    payload.write_bytes(b"content")
    manifest["outputs"] = [
        {
            "role": "master",
            "path": "output.flac",
            "sha256": hashlib.sha256(b"content").hexdigest(),
            "media_type": "audio/flac",
            "meta": {},
        }
    ]
    manifest["future_field"] = {"hello": "world"}
    result = invoke("verify_manifest", manifest, tmp_path)
    assert result.get("valid") is True
    payload.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        audio_post.verify_manifest(manifest, tmp_path)
    manifest["outputs"][0]["path"] = "../escape.flac"
    with pytest.raises(ValueError, match="UNSAFE_PATH|MANIFEST_SCHEMA"):
        audio_post.verify_manifest(manifest, tmp_path)


def test_limiter_and_resampling(tmp_path):
    import soundfile as sf

    sr = 24000
    t = np.arange(sr * 4) / sr
    amplitude = np.where(t % 0.5 < 0.04, 0.8, 0.015)
    samples = amplitude * np.sin(2 * np.pi * 997 * t)
    source = tmp_path / "transients.wav"
    sf.write(source, samples, sr, subtype="FLOAT")
    result = audio_post.process_audio(
        source, tmp_path / "take", expected_duration_s=4, ffmpeg=FFMPEG
    )
    assert result["post"]["limiter"] is True
    assert abs(result["post"]["lufs_out"] + 14) <= 0.5
    assert result["post"]["true_peak_dbtp"] <= -1
    assert sf.info(tmp_path / "take/listen.mp3").samplerate == 48000
    assert sf.info(tmp_path / "take/master.flac").samplerate == 24000


def test_audio_errors(tmp_path, monkeypatch):
    import soundfile as sf
    from audio_post import pipeline

    with pytest.raises(ValueError, match="AUDIO_SHAPE"):
        audio_post.validate_audio(np.empty(0), 48000, 1)
    with pytest.raises(ValueError, match="AUDIO_DURATION"):
        audio_post.validate_audio(signal(), 48000, 0)
    with pytest.raises(ValueError, match="AUDIO_SHAPE"):
        audio_post.make_peaks(np.empty(0))
    assert audio_post.validate_audio(signal()[:, 0], 48000, 3)["channels"] == 1
    assert audio_post.make_peaks(signal()[:10, 0])["channels"] == 1
    source = tmp_path / "raw.wav"
    sf.write(source, signal(), 48000, subtype="FLOAT")
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        audio_post.process_audio(
            source,
            Path("C:/escape") if Path("C:/").exists() else Path("/escape"),
            expected_duration_s=3,
            ffmpeg=FFMPEG,
        )
    monkeypatch.setattr(
        pipeline, "measure_audio", lambda *a, **k: {"lufs": -25, "true_peak_dbtp": 1}
    )
    monkeypatch.setattr(pipeline, "_ffmpeg", lambda *a, **k: None)
    with pytest.raises(ValueError, match="AUDIO_TARGET_UNREACHABLE"):
        audio_post.process_audio(
            source, tmp_path / "unreachable", expected_duration_s=3, ffmpeg=FFMPEG
        )
    assert not (tmp_path / "unreachable").exists()
