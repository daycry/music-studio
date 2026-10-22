"""Rechazos CPU con WAV sintéticos y dobles explícitos; no medidas reales de FFmpeg."""

import hashlib
import json
import os
import subprocess
import zipfile
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest
import soundfile as sf

from scripts.eval import metrics, run


@pytest.fixture
def tmp_path():
    path = (
        run.ROOT
        / ".cache/dev-cycle/t11/cpu-implementation/worker-fixtures"
        / uuid4().hex
    )
    path.mkdir(parents=True)
    return path


def test_cli_canonical_dry_and_fail_closed(capsys):
    assert run.main(["--candidate", "ace-step-1.5-turbo", "--dry-run"]) == 0
    text = capsys.readouterr().out
    assert sum(line.startswith("B-") for line in text.splitlines()) == 30
    assert "MISSING_DECLARATION" in text and "MISSING_INPUT" in text
    assert run.main(["--candidate", "ace-step-1.5-turbo"]) == 2
    assert "PREREQUISITES_PENDING" in capsys.readouterr().err
    assert run.main(["--candidate", "unknown-candidate", "--dry-run"]) == 2
    assert "UNKNOWN_CANDIDATE" in capsys.readouterr().err


def test_local_auth_and_descriptor_guards(tmp_path):
    with pytest.raises(ValueError, match="LOCAL_ENGINE_REQUIRED"):
        run.V1Transport(
            root=tmp_path, config={}, url="http://example.invalid", client=None
        )
    with pytest.raises(ValueError, match="ENGINE_TOKEN_REQUIRED"):
        run.V1Transport(root=tmp_path, config={}, url="http://127.0.0.1", client=None)
    from engine_mock import descriptor

    model = descriptor().model_dump(mode="json")
    model["modes"] = []
    with pytest.raises(ValueError, match="MODE_UNAVAILABLE"):
        run.resolve_descriptor([model], "mock", "music.song")
    model["modes"] = [{"id": "cpu", "notes": "synthetic"}]
    model["tasks"]["music.song"]["device"] = "gpu"
    transport = run.V1Transport(
        root=tmp_path,
        config={"STUDIO_ENGINE_TOKEN": "synthetic"},
        url="http://127.0.0.1",
        client=None,
    )
    with pytest.raises(ValueError, match="REAL_GPU_PREFLIGHT_DEFERRED"):
        transport(
            {"task": "music.song", "params": {}, "seed": 101},
            job_id="01M49HZQ7K5WFE9PA1N3WDN92K",
            descriptor=model,
        )


@pytest.mark.parametrize("case", ["rate", "channels", "nonfinite", "duration"])
def test_audio_record_gates(tmp_path, case):
    pcm = np.ones((480, 2), dtype=np.float32) * 0.1
    if case == "channels":
        pcm = pcm[:, :1]
    if case == "nonfinite":
        pcm[0, 0] = np.inf
    path = tmp_path / "synthetic.wav"
    sf.write(path, pcm, 44100 if case == "rate" else 48000, subtype="FLOAT")
    with pytest.raises(ValueError):
        metrics.audio_record(path, expected_duration=20 if case == "duration" else None)


def test_wer_language_empty_and_floor_gates():
    for kwargs in (
        {"language": "fr"},
        {"language": "es", "floor": float("nan")},
        {"language": "es", "floor": -1},
    ):
        with pytest.raises(ValueError):
            metrics.wer("uno", "uno", **kwargs)
    with pytest.raises(ValueError, match="WER_REFERENCE_EMPTY"):
        metrics.wer("[Verse]", "verse", language="es")
    with pytest.raises(ValueError):
        metrics.metric_request("audio.transcribe", language="fr", style="x")
    with pytest.raises(ValueError):
        metrics.metric_request("audio.clap", language="es", style="")
    with pytest.raises(ValueError):
        metrics.metric_request("wrong", language="es", style="x")
    with pytest.raises(ValueError):
        metrics.native_metric("wrong", {"analysis": {}}, reference="x", language="es")
    with pytest.raises(ValueError):
        metrics.native_metric(
            "audio.transcribe", {"analysis": {}}, reference="x", language="es"
        )
    with pytest.raises(ValueError):
        metrics.native_metric(
            "audio.clap",
            {"analysis": {"score": float("nan")}},
            reference="x",
            language="es",
        )
    with pytest.raises(ValueError):
        metrics.native_metric(
            "audio.aesthetics",
            {"analysis": {"PQ": 1, "PC": 2, "CE": 3, "CU": float("inf")}},
            reference="x",
            language="es",
        )


def test_floor_rejects_cardinality_and_synthetic_even_with_claimed_profile(tmp_path):
    with pytest.raises(ValueError):
        metrics.measure_floor([], root=tmp_path, model_id="x", profile="x")
    rows = [
        {
            "synthetic": True,
            "sung": True,
            "fixture_label": "SYNTHETIC_GT_NO_CALIBRATION",
        }
    ] * 2
    with pytest.raises(ValueError, match="REAL_SUNG_GT_REQUIRED"):
        metrics.measure_floor(rows, root=tmp_path, model_id="x", profile="x")


def test_fixed_gain_underflow_and_prediction_conflict():
    pcm = np.array([[1.0, -1.0]], dtype=np.float32)
    scaled, result = metrics.linear_gain(pcm, measured_lufs=-16, measured_dbtp=-2)
    assert result["gain_db"] == 0 and np.array_equal(pcm, scaled)
    scaled, result = metrics.linear_gain(pcm, measured_lufs=-20, measured_dbtp=-20)
    assert result["status"] == "PEAK_CONFLICT" and np.array_equal(pcm, scaled)
    with pytest.raises(ValueError):
        metrics.linear_gain(pcm, measured_lufs=float("nan"), measured_dbtp=-2)


def test_staging_confinement_invalid_identity_and_hash_mutation(tmp_path, monkeypatch):
    source = tmp_path / "synthetic.wav"
    source.write_bytes(b"SYNTHETIC_NOT_AUDIO")
    with pytest.raises(ValueError, match="JOB_ID_INVALID"):
        metrics.stage_audio(source, tmp_path / "data", "../bad", root=tmp_path)
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        metrics.confined(tmp_path.parent / "foreign.wav", tmp_path)
    actual = metrics.file_hash
    calls = []

    def changing(path):
        calls.append(path)
        return actual(path) if len(calls) == 1 else "0" * 64

    monkeypatch.setattr(metrics, "file_hash", changing)
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        metrics.stage_audio(
            source, tmp_path / "data", "01M49HZQ7K5WFE9PA1N3WDN92K", root=tmp_path
        )


def fake_bundle(root):
    """ZIP y ejecutable de prueba, jamás se ejecuta como FFmpeg."""
    name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    member = f"synthetic/bin/{name}"
    archive = root / ".cache/fetch/synthetic.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(member, b"SYNTHETIC_EXECUTABLE_STUB_DO_NOT_RUN")
    binary = root / "tools/ffmpeg" / member
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"SYNTHETIC_EXECUTABLE_STUB_DO_NOT_RUN")
    lock = {
        "tools": {
            "ffmpeg": {
                "asset": "synthetic.zip",
                "bytes": archive.stat().st_size,
                "sha256": metrics.file_hash(archive),
                "dest": "tools/ffmpeg",
            }
        }
    }
    (root / "tools/tools.lock.json").write_text(json.dumps(lock), encoding="utf-8")
    return binary, archive


def test_ffmpeg_archive_binary_version_guards_simulated_only(tmp_path, monkeypatch):
    binary, archive = fake_bundle(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            stdout="ffmpeg 51c4a23d74 SYNTHETIC_SIMULATION\n"
        ),
    )
    result, receipt = metrics.verified_ffmpeg(tmp_path)
    assert (
        result == binary
        and receipt["sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
    )
    binary.write_bytes(b"changed synthetic")
    with pytest.raises(ValueError, match="FFMPEG_HASH_MISMATCH"):
        metrics.verified_ffmpeg(tmp_path)
    binary.write_bytes(b"SYNTHETIC_EXECUTABLE_STUB_DO_NOT_RUN")
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="untrusted version")
    )
    with pytest.raises(ValueError, match="FFMPEG_VERSION_MISMATCH"):
        metrics.verified_ffmpeg(tmp_path)
    archive.write_bytes(b"invalid")
    with pytest.raises(ValueError, match="FFMPEG_VERIFIED_ARCHIVE_REQUIRED"):
        metrics.verified_ffmpeg(tmp_path)


def test_loudness_parser_is_unit_simulation_not_measurement(tmp_path, monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stderr="I: -30.0 LUFS\nPeak: -20.0 dBFS\nI: -16.0 LUFS\nPeak: -1.2 dBFS\n",
        ),
    )
    result = metrics.loudness(tmp_path / "synthetic.wav", tmp_path / "not-executed")
    assert result["lufs"] == -16 and result["dbtp"] == -1.2
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stderr="no measurement"),
    )
    with pytest.raises(ValueError, match="LOUDNESS_MEASUREMENT_INVALID"):
        metrics.loudness(tmp_path / "synthetic.wav", tmp_path / "not-executed")


@pytest.mark.parametrize(
    "case", ["pass", "peak-conflict", "post-conflict", "silence", "clipped"]
)
def test_normalization_controller_simulated_measurement_native_wav(
    tmp_path, monkeypatch, case
):
    pcm = np.array([[0.1, -0.05], [0.05, 0.01]], dtype=np.float32)
    if case == "silence":
        pcm *= 0
    if case == "clipped":
        pcm[0, 0] = 1.1
    source, destination = tmp_path / "synthetic.wav", tmp_path / "scaled-synthetic.wav"
    sf.write(source, pcm, 48000, subtype="FLOAT")
    original_hash = metrics.file_hash(source)
    monkeypatch.setattr(
        metrics,
        "verified_ffmpeg",
        lambda root: (tmp_path / "not-executed", {"synthetic_unit_double": True}),
    )
    calls = []

    def simulated(path, binary):
        calls.append(path)
        if len(calls) == 1:
            return {
                "lufs": -20.0,
                "dbtp": -3.0 if case == "peak-conflict" else -20.0,
                "synthetic_unit_double": True,
            }
        return {
            "lufs": -16.0,
            "dbtp": -0.5 if case == "post-conflict" else -16.0,
            "synthetic_unit_double": True,
        }

    monkeypatch.setattr(metrics, "loudness", simulated)
    if case in {"silence", "clipped"}:
        with pytest.raises(ValueError, match="AUDIO_NOT_BLIND_READY"):
            metrics.normalize_audio(source, destination, root=tmp_path)
    else:
        result = metrics.normalize_audio(source, destination, root=tmp_path)
        assert result["blind_ready"] is (case == "pass")
        if case == "peak-conflict":
            assert not destination.exists()
        else:
            assert sf.info(destination).subtype == "FLOAT"
            assert sf.read(destination, dtype="float32")[0] == pytest.approx(
                pcm * 10 ** (4 / 20)
            )
    assert metrics.file_hash(source) == original_hash


def test_metrics_failures_observable_without_zero_scores(tmp_path):
    from engine_mock import descriptor

    source = tmp_path / "synthetic.wav"
    sf.write(source, np.full((480, 2), 0.01, dtype=np.float32), 48000, subtype="FLOAT")
    tasks = ("audio.transcribe", "audio.clap", "audio.aesthetics")
    request = {
        "params": {"language": "es", "style": "synthetic", "lyrics": "synthetic"}
    }
    with pytest.raises(ValueError, match="METRIC_BINDINGS_REQUIRED"):
        run.measure_take(
            source, request, root=tmp_path, transport=None, descriptors=[], bindings={}
        )

    def broken(*a, **k):
        raise ValueError("SYNTHETIC_METRIC_FAILURE")

    result = run.measure_take(
        source,
        request,
        root=tmp_path,
        transport=broken,
        descriptors=[descriptor().model_dump(mode="json")],
        bindings={t: "mock" for t in tasks},
    )
    assert all(
        row["status"] == "ERROR" and "value" not in row for row in result.values()
    )


def test_unknown_submit_ack_retains_identity_never_retries_and_sanitizes(tmp_path):
    import httpx
    from engine_mock import descriptor

    model = descriptor().model_dump(mode="json")
    calls = []
    secret = "synthetic-secret-never-in-artifacts"

    def handler(request):
        calls.append((request.method, request.url.path))
        assert request.headers["X-Studio-Engine-Token"] == secret
        if request.url.path == "/v1/health":
            return httpx.Response(
                200,
                json={
                    "engine_id": "mock",
                    "engine_version": "1",
                    "image_digest": "synthetic",
                    "state": "idle",
                    "loaded": None,
                    "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
                },
            )
        if request.url.path == "/v1/models":
            return httpx.Response(200, json=[model])
        if request.url.path == "/v1/estimate":
            return httpx.Response(200, json={"eta_s": 0.01, "vram_mb": 0})
        if request.url.path == "/v1/jobs":
            raise httpx.ReadTimeout(secret)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        transport = run.V1Transport(
            root=tmp_path,
            config={"STUDIO_ENGINE_TOKEN": secret},
            url="http://127.0.0.1",
            client=client,
        )
        with pytest.raises(ValueError, match="SUBMIT_ACK_UNKNOWN"):
            transport(
                {"task": "music.song", "params": {"duration_s": 0.01}, "seed": 101},
                job_id="01M49HZQ7K5WFE9PA1N3WDN92K",
                descriptor=model,
            )
    assert calls.count(("POST", "/v1/jobs")) == 1
    artifacts = list((tmp_path / "data/tmp").rglob("*.json"))
    assert any("SUBMIT_ACK_UNKNOWN" in p.read_text(encoding="utf-8") for p in artifacts)
    assert all(secret not in p.read_text(encoding="utf-8") for p in artifacts)


def test_sealed_plan_rejects_catalog_replacement_before_transport(tmp_path):
    from test_evaluation_cpu import catalog

    catalog(tmp_path)
    plan = run.build_plan("mock", root=tmp_path, known_candidates={"mock"})
    (tmp_path / "eval/briefs/briefs.yaml").write_text(
        "version: 1\nbriefs: {}", encoding="utf-8"
    )
    calls = []
    with pytest.raises(ValueError, match="SOURCE_CATALOG_MISMATCH"):
        run.execute(
            plan,
            root=tmp_path,
            transport=lambda *a, **k: calls.append(a),
            allow_synthetic=True,
        )
    assert not calls


def test_blind_resume_recovers_missing_copy_keeps_same_map(tmp_path):
    source = tmp_path / "synthetic.wav"
    sf.write(source, np.full((480, 2), 0.1, dtype=np.float32), 48000, subtype="FLOAT")
    takes = [
        {
            "source": str(source),
            "sha256": metrics.file_hash(source),
            "identity": "synthetic-identity",
        }
    ]
    folder = tmp_path / "collection"
    first = run.anonymize(takes, folder, root=tmp_path)
    original_map = (folder / "private.map.json").read_bytes()
    (folder / "blind" / (first[0]["code"] + ".wav")).unlink()
    assert run.anonymize(takes, folder, root=tmp_path) == first
    assert (folder / "private.map.json").read_bytes() == original_map


def test_unknown_plan_schema_fails_closed(tmp_path):
    from test_evaluation_cpu import catalog

    catalog(tmp_path)
    plan = run.build_plan("mock", root=tmp_path, known_candidates={"mock"})
    plan["version"] = "unknown-schema"
    plan = run.seal_plan(plan)
    with pytest.raises(ValueError, match="PLAN_SCHEMA_INVALID"):
        run.execute(plan, root=tmp_path, transport=None, allow_synthetic=True)


def test_floor_profile_mismatch_never_adjusts_raw_wer(tmp_path):
    from engine_mock import descriptor

    source = tmp_path / "synthetic.wav"
    sf.write(source, np.full((480, 2), 0.1, dtype=np.float32), 48000, subtype="FLOAT")
    model = descriptor().model_dump(mode="json")

    def fake(request, *, job_id, **kwargs):
        output = tmp_path / f"data/tmp/{job_id}/analysis.json"
        native = {
            "task": request["task"],
            "analysis": {"text": "uno", "language": "Spanish"},
            "stages": [
                {
                    "task": request["task"],
                    "model_id": "mock",
                    "revision": "synthetic-v1",
                }
            ],
        }
        output.write_text(json.dumps(native), encoding="utf-8")
        return {
            "job_id": job_id,
            "model_id": "mock",
            "source": str(output),
            "sha256": metrics.file_hash(output),
            "synthetic": True,
        }

    floor = {
        "model_id": "mock",
        "status": "MEASURED",
        "normalization": metrics.NORMALIZATION,
        "bindings": [{"synthetic_fixture": True}],
        "profile": "wrong-profile",
        "mean": 0.9,
    }
    result = run.measure_take(
        source,
        {"params": {"lyrics": "uno dos", "language": "es", "style": "synthetic"}},
        root=tmp_path,
        transport=fake,
        descriptors=[model],
        bindings={
            t: "mock" for t in ("audio.transcribe", "audio.clap", "audio.aesthetics")
        },
        floor=floor,
    )
    assert result["audio.transcribe"]["status"] == "ERROR"
    assert result["audio.transcribe"]["error"] == "FLOOR_PROFILE_MISMATCH"


def test_public_blind_order_does_not_disclose_plan_slot_order(tmp_path, monkeypatch):
    import random

    source = tmp_path / "synthetic.wav"
    sf.write(source, np.full((480, 2), 0.1, dtype=np.float32), 48000, subtype="FLOAT")
    takes = [
        {
            "source": str(source),
            "sha256": metrics.file_hash(source),
            "identity": f"synthetic-{i}",
        }
        for i in range(3)
    ]
    monkeypatch.setattr(
        random.SystemRandom, "shuffle", lambda self, rows: rows.reverse()
    )
    folder = tmp_path / "collection"
    mapping = run.anonymize(takes, folder, root=tmp_path)
    sheet = (folder / "blind/sheet.md").read_text(encoding="utf-8")
    lines = [
        line.split("|")[1].strip() for line in sheet.splitlines() if ".wav](" in line
    ]
    assert lines == [row["code"] for row in reversed(mapping)]
