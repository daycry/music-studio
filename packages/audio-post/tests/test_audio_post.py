import json
from pathlib import Path

import audio_post
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]


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


def test_master_and_listen(tmp_path, ffmpeg_path):
    import subprocess

    source = tmp_path / "raw.wav"
    subprocess.run(
        [
            str(ffmpeg_path),
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
    result = invoke(
        "process_audio", source, dest, expected_duration_s=3, ffmpeg=ffmpeg_path
    )
    assert (dest / "master.flac").exists()
    import soundfile as sf

    assert sf.info(dest / "master.flac").subtype == "PCM_24"
    master, sr = sf.read(dest / "master.flac", always_2d=True)
    assert sr == 48000
    assert np.max(np.abs(master - signal())) < 2**-22
    assert abs(result["post"]["lufs_out"] + 14) <= 0.5
    assert result["post"]["true_peak_dbtp"] <= -1
    measured = audio_post.measure_audio(dest / "listen.mp3", ffmpeg=ffmpeg_path)
    assert abs(measured["lufs"] + 14) <= 0.5
    assert measured["true_peak_dbtp"] <= -1
    with pytest.raises(FileExistsError):
        audio_post.process_audio(
            source, dest, expected_duration_s=3, ffmpeg=ffmpeg_path
        )
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


def test_limiter_and_resampling(tmp_path, ffmpeg_path):
    import soundfile as sf

    sr = 24000
    t = np.arange(sr * 4) / sr
    amplitude = np.where(t % 0.5 < 0.04, 0.8, 0.015)
    samples = amplitude * np.sin(2 * np.pi * 997 * t)
    source = tmp_path / "transients.wav"
    sf.write(source, samples, sr, subtype="FLOAT")
    result = audio_post.process_audio(
        source, tmp_path / "take", expected_duration_s=4, ffmpeg=ffmpeg_path
    )
    assert result["post"]["limiter"] is True
    assert abs(result["post"]["lufs_out"] + 14) <= 0.5
    assert result["post"]["true_peak_dbtp"] <= -1
    assert sf.info(tmp_path / "take/listen.mp3").samplerate == 48000
    assert sf.info(tmp_path / "take/master.flac").samplerate == 24000


def test_audio_errors(tmp_path, monkeypatch, ffmpeg_path):
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
            ffmpeg=ffmpeg_path,
        )
    monkeypatch.setattr(
        pipeline, "measure_audio", lambda *a, **k: {"lufs": -25, "true_peak_dbtp": 1}
    )
    monkeypatch.setattr(pipeline, "_ffmpeg", lambda *a, **k: None)
    with pytest.raises(ValueError, match="AUDIO_TARGET_UNREACHABLE"):
        audio_post.process_audio(
            source, tmp_path / "unreachable", expected_duration_s=3, ffmpeg=ffmpeg_path
        )
    assert not (tmp_path / "unreachable").exists()


@pytest.mark.parametrize("task", ["text2music", "cover"])
@pytest.mark.parametrize(
    "mutation",
    [
        "boolean",
        "instruction",
        "task",
        "tokens",
        "candidate_budget",
        "missing",
        "version",
        "alias",
        "output",
        "seed",
        "profile",
        "source",
    ],
)
def test_native_v2_resolution_rejects_rehashed_contradictions(
    monkeypatch, task, mutation
):
    monkeypatch.syspath_prepend(str(ROOT / "tests"))
    from audio_post.manifest import validate_input_receipt
    from test_generate_preparation import (
        _native_v2_receipt_fixture,
        _rehash_native_receipt,
    )

    receipt, request = _native_v2_receipt_fixture(task)
    planned, captured = receipt["planned"], receipt["captured"]
    assert validate_input_receipt(json.dumps(receipt), request, 0) == receipt
    resolution = captured["boundaries"][3]
    if mutation == "boolean":
        resolution["has_audio_codes"] = int(resolution["has_audio_codes"])
    elif mutation == "instruction":
        resolution["instruction_sha256"] = planned["dit"]["candidates"][task][
            "instruction_sha256"
        ] = "0" * 64
    elif mutation == "task":
        resolution["resolved_task"] = "unknown"
    elif mutation == "tokens":
        captured["boundaries"][4]["text"]["tokens_sha256"] = "0" * 64
    elif mutation == "candidate_budget":
        planned["dit"]["candidates"]["cover" if task == "text2music" else "text2music"][
            "text"
        ]["count"] = 257
    elif mutation == "missing":
        captured["boundaries"].pop(3)
    elif mutation == "version":
        captured["receipt_version"] = 1
    elif mutation == "alias":
        planned["dit"]["text"]["tokens_sha256"] = "0" * 64
    elif mutation == "output":
        captured["output_index"] = 1
    elif mutation == "profile":
        planned["profile_revision"] = "unknown"
    elif mutation == "source":
        planned["source_hashes"][
            "core/generation/handler/generate_music_request.py"
        ] = "0" * 64
    else:
        request = {**request, "seed": 2}
    _rehash_native_receipt(receipt)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0)


@pytest.fixture
def prepared_manifest(tmp_path):
    """Recibo real del productor CLI; el manifiesto conserva sólo datos públicos."""
    import hashlib

    from scripts import input_preparation

    lyrics = "**[Verse]**\nTexto privado de prueba\n"
    original_bytes = b"\xef\xbb\xbf" + lyrics.encode("utf-8")
    request = {
        "task": "music.song",
        "params": {
            "lyrics": lyrics,
            "style": "estilo explícito",
            "duration_s": 3,
            "vocal_language": "es",
        },
        "lyrics_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "lyrics_declaration": "own",
        "seed": 42,
        "n_outputs": 2,
    }
    receipt = input_preparation.prepare(
        request,
        sources={"lyrics": original_bytes, "style": b"estilo original"},
        strip_tag_markdown=True,
    )
    receipt = input_preparation.bind_execution(receipt, seed=42, n_outputs=2)
    manifest = json.loads(
        (ROOT / "packages/contracts/examples/cli_run.json").read_text()
    )
    manifest["request"] = {
        "task": request["task"],
        "params": {
            key: value
            for key, value in request["params"].items()
            if key not in {"lyrics", "style"}
        },
        "seed": 43,
        "variant_index": 1,
        "lyrics_sha256": request["lyrics_sha256"],
        "lyrics_declaration": "own",
    }
    (tmp_path / "fixture.txt").write_bytes(b"music-studio fixture\n")
    directory = tmp_path / "preparations"
    directory.mkdir()

    def bind(value):
        payload = input_preparation.encode(value)
        digest = hashlib.sha256(payload).hexdigest()
        (directory / (digest + ".json")).write_bytes(payload)
        manifest["preparation"] = {"sha256": digest}
        return directory / (digest + ".json")

    bind(receipt)
    return manifest, receipt, bind


def test_manifest_verifies_private_preparation_and_variant(prepared_manifest, tmp_path):
    manifest, _, _ = prepared_manifest
    assert audio_post.verify_manifest(manifest, tmp_path) == {
        "valid": True,
        "outputs": 1,
    }
    assert "Texto privado" not in json.dumps(manifest)
    manifest["request"]["seed"] = 42
    with pytest.raises(ValueError, match="PREPARATION_REQUEST_MISMATCH"):
        audio_post.verify_manifest(manifest, tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "version",
        "budget",
        "digest",
        "base64",
        "bytes_hash",
        "effective_hash",
        "diff",
        "fields",
        "transformation",
        "source_hash",
    ],
)
def test_manifest_rejects_rehashed_preparation_forgery(
    prepared_manifest, tmp_path, mutation
):
    manifest, receipt, bind = prepared_manifest
    assert audio_post.verify_manifest(manifest, tmp_path)["valid"]
    if mutation == "version":
        receipt["version"] = 2
    elif mutation == "budget":
        receipt["engine_budget"] = "accepted"
    elif mutation == "digest":
        receipt["effective_request_sha256"] = "0" * 64
    elif mutation == "base64":
        receipt["fields"]["lyrics"]["original_bytes_base64"] = "!invalid!"
    elif mutation == "bytes_hash":
        receipt["fields"]["lyrics"]["original_bytes_sha256"] = "0" * 64
    elif mutation == "effective_hash":
        receipt["fields"]["lyrics"]["effective_sha256"] = "0" * 64
    elif mutation == "diff":
        receipt["fields"]["style"]["diff"] = ""
    elif mutation == "fields":
        del receipt["fields"]["lyrics"]
    elif mutation == "transformation":
        receipt["transformations"] = ["strip_tag_markdown"]
    else:
        receipt["original"]["lyrics_sha256"] = "0" * 64
        receipt["effective"]["lyrics_sha256"] = "0" * 64
        from scripts import input_preparation

        receipt["effective_request_sha256"] = input_preparation.digest(
            input_preparation.encode(receipt["effective"])
        )
    bind(receipt)
    with pytest.raises(ValueError, match="PREPARATION_INVALID"):
        audio_post.verify_manifest(manifest, tmp_path)


@pytest.mark.parametrize("mutation", ["missing", "hash", "seed", "duration"])
def test_manifest_rejects_missing_or_unbound_preparation(
    prepared_manifest, tmp_path, mutation
):
    manifest, receipt, bind = prepared_manifest
    assert audio_post.verify_manifest(manifest, tmp_path)["valid"]
    if mutation == "missing":
        bind(receipt).unlink()
        code = "PREPARATION_MISSING"
    elif mutation == "hash":
        bind(receipt).write_bytes(b"{}")
        code = "PREPARATION_HASH_MISMATCH"
    elif mutation == "seed":
        receipt["execution"]["seed"] = True
        bind(receipt)
        code = "PREPARATION_REQUEST_MISMATCH"
    else:
        manifest["request"]["params"]["duration_s"] = 4
        code = "PREPARATION_REQUEST_MISMATCH"
    with pytest.raises(ValueError, match=code):
        audio_post.verify_manifest(manifest, tmp_path)
