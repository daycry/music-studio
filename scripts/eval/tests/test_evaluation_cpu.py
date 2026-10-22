"""Entradas, audio y GT sintéticos; no acreditan inferencia ni escucha musical."""

import importlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest
import soundfile as sf
import yaml

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def tmp_path():
    path = (
        ROOT / ".cache/dev-cycle/t11/cpu-implementation/worker-fixtures" / uuid4().hex
    )
    path.mkdir(parents=True)
    return path


def api(name):
    path = ROOT / f"scripts/eval/{name}.py"
    assert path.is_file(), f"Unidad CPU {name} ausente"
    return importlib.import_module(f"scripts.eval.{name}")


def catalog(root, complete=True):
    folder = root / "eval/briefs"
    folder.mkdir(parents=True)
    entries = {}
    durations = [45, 180, 30, 120, 150, 30, 150, 40, 165, 90]
    bpms = [112, 84, 96, 92, 68, 124, 140, 100, 76, 110]
    for index in range(10) if complete else [1]:
        code = f"B-{index + 1:02}"
        entries[code] = {
            "task": "music.song",
            "style": f"ESTILO SINTÉTICO **[voz {index}]**",
            "duration_s": durations[index],
            "bpm": bpms[index],
            "language": "en" if index in {3, 6, 8, 9} else "es",
            "lyrics_declaration": "own" if complete else None,
        }
        if complete:
            (folder / f"{code}.txt").write_text(
                "**[Verse: female, intimate]**\nPalabras sintéticas de prueba\n[Chorus]\nLuz azul",
                encoding="utf-8",
            )
    (folder / "briefs.yaml").write_text(
        yaml.safe_dump({"version": 1, "briefs": entries}), encoding="utf-8"
    )
    return entries


def test_plan_has_thirty_fixed_slots_and_literal_inputs(tmp_path):
    entries = catalog(tmp_path)
    plan = api("run").build_plan("ace-step-1.5-turbo", root=tmp_path)
    assert len(plan["rows"]) == 30
    assert [(r["brief_id"], r["seed"]) for r in plan["rows"]] == [
        (f"B-{i:02}", seed) for i in range(1, 11) for seed in (101, 202, 303)
    ]
    for row in plan["rows"]:
        assert row["request"]["params"]["style"] == entries[row["brief_id"]]["style"]
        assert "**[Verse: female, intimate]**" in row["request"]["params"]["lyrics"]
        assert row["preparation"]["transformations"] == []
    assert (
        plan["hash"]
        == api("run").build_plan("ace-step-1.5-turbo", root=tmp_path)["hash"]
    )


def test_missing_prerequisites_fail_before_any_transport(tmp_path):
    catalog(tmp_path, complete=False)
    run = api("run")
    plan = run.build_plan("ace-step-1.5-turbo", root=tmp_path)
    assert len(plan["rows"]) == 30
    assert "MISSING_DECLARATION" in plan["rows"][3]["diagnostics"]
    calls = []
    with pytest.raises(ValueError, match="PREREQUISITES_PENDING"):
        run.execute(plan, root=tmp_path, transport=lambda *a: calls.append(a))
    assert calls == []


def test_wer_preserves_sung_tags_and_pending_floor():
    metrics = api("metrics")
    result = metrics.wer(
        "**[Verse: female]**\nHola, corazón azul",
        "hola corazón azul verse female",
        language="es",
    )
    assert result["edits"] == 2 and result["reference_words"] == 3
    assert result["raw"] == pytest.approx(2 / 3)
    assert result["adjusted"] is None and result["floor_status"] == "PENDING"


def test_fixed_gain_is_proportional_and_conflict_keeps_raw(tmp_path):
    metrics = api("metrics")
    pcm = np.array([[0.01, -0.02], [0.03, 0.015], [-0.01, 0.005]], dtype=np.float32)
    output, receipt = metrics.linear_gain(pcm, measured_lufs=-20, measured_dbtp=-20)
    assert output == pytest.approx(pcm * 10 ** (4 / 20))
    assert receipt["gain_db"] == 4
    conflict, receipt = metrics.linear_gain(pcm, measured_lufs=-30, measured_dbtp=-5)
    assert np.array_equal(conflict, pcm) and receipt["status"] == "PEAK_CONFLICT"
    raw = tmp_path / "synthetic.wav"
    sf.write(raw, pcm, 48000, subtype="FLOAT")
    assert metrics.audio_record(raw)["frames"] == 3


def test_blind_collection_exclusive_stable_private_map(tmp_path):
    run = api("run")
    raw = tmp_path / "synthetic-source.wav"
    sf.write(
        raw,
        np.array([[0.1, -0.1], [0.2, -0.2]], dtype=np.float32),
        48000,
        subtype="FLOAT",
    )
    take = {
        "identity": "synthetic-B01-model-seed",
        "source": str(raw),
        "sha256": run.file_hash(raw),
    }
    folder = tmp_path / "collection"
    first = run.anonymize([take], folder, root=tmp_path)
    assert run.anonymize([take], folder, root=tmp_path) == first
    listing = (folder / "blind/sheet.md").read_text(encoding="utf-8")
    assert "synthetic-B01-model-seed" not in listing and str(raw) not in listing
    assert "D1" in listing and "D5" in listing and "naturalidad" in listing
    assert (folder / "private.map.json").is_file()
    raw.write_bytes(b"changed")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        run.anonymize([take], folder, root=tmp_path)


def test_analysis_stages_under_job_in_with_exact_hash(tmp_path):
    metrics = api("metrics")
    raw = tmp_path / "synthetic.wav"
    sf.write(raw, np.zeros((30, 2), dtype=np.float32), 48000, subtype="FLOAT")
    binding = metrics.stage_audio(
        raw, tmp_path / "data", "01M49HZQ7K5WFE9PA1N3WDN92K", root=tmp_path
    )
    assert binding["path"] == "tmp/01M49HZQ7K5WFE9PA1N3WDN92K/in/audio.wav"
    assert (tmp_path / "data" / binding["path"]).read_bytes() == raw.read_bytes()
    with pytest.raises(FileExistsError):
        metrics.stage_audio(
            raw, tmp_path / "data", "01M49HZQ7K5WFE9PA1N3WDN92K", root=tmp_path
        )


def test_floor_requires_real_declared_whole_content_matched_profile(tmp_path):
    metrics = api("metrics")
    rows = [{"synthetic": True}, {"synthetic": True}]
    with pytest.raises(ValueError, match="REAL_SUNG_GT_REQUIRED"):
        metrics.measure_floor(rows, root=tmp_path, model_id="asr", profile="whole-v1")


def test_descriptor_resolution_exact_verified_no_profile_inheritance():
    from engine_mock import descriptor

    run = api("run")
    model = descriptor().model_dump(mode="json")
    assert run.resolve_descriptor([model], "mock", "music.song")["id"] == "mock"
    with pytest.raises(ValueError, match="CANDIDATE_UNAVAILABLE"):
        run.resolve_descriptor([model], "heartmula", "music.song")
    model["tasks"]["music.song"]["verified"] = False
    with pytest.raises(ValueError, match="CAPABILITY_UNVERIFIED"):
        run.resolve_descriptor([model], "mock", "music.song")


def test_synthetic_complete_workflow_thirty_unique_jobs(tmp_path):
    run = api("run")
    catalog(tmp_path)
    plan = run.build_plan("mock", root=tmp_path, known_candidates={"mock"})
    # Explicit test-only effective catalog: short audio avoids claiming canonical 30 takes.
    for row in plan["rows"]:
        row["request"]["params"]["duration_s"] = 0.01
        from scripts import input_preparation

        row["preparation"] = input_preparation.prepare(row["request"])
    plan = run.seal_plan(plan)
    jobs = []

    def transport(request, *, job_id, **kwargs):
        jobs.append(job_id)
        output = tmp_path / "data/tmp" / job_id / "synthetic.wav"
        output.parent.mkdir(parents=True)
        sf.write(
            output, np.full((480, 2), 0.01, dtype=np.float32), 48000, subtype="FLOAT"
        )
        return {
            "source": str(output),
            "sha256": run.file_hash(output),
            "synthetic": True,
            "model_id": "mock",
            "job_id": job_id,
            "captured_receipts": [],
            "run_s": 0.01,
        }

    result = run.execute(plan, root=tmp_path, transport=transport, allow_synthetic=True)
    assert len(result["takes"]) == 30 and len(set(jobs)) == 30
    assert all(
        t["status"] == "RAW_ONLY_PENDING_LOUDNESS_METRICS" for t in result["takes"]
    )
    assert all(t["synthetic"] for t in result["takes"])
    assert result["acceptance"] is None
    with pytest.raises(ValueError, match="PLAN_HASH_MISMATCH"):
        altered = json.loads(json.dumps(plan))
        altered["rows"][0]["seed"] = 999
        run.execute(altered, root=tmp_path, transport=transport, allow_synthetic=True)


def test_v1_http_mock_auth_explicit_model_events_cleanup(tmp_path):
    from engine_mock import create_mock_app, descriptor
    from fastapi.testclient import TestClient

    run = api("run")
    assert hasattr(run, "V1Transport"), "Transporte /v1 de evaluación ausente"
    data = tmp_path / "data"
    data.mkdir()
    app = create_mock_app(token="synthetic-test-token", data_dir=data, stage_delay_ms=0)
    with TestClient(app) as client:
        transport = run.V1Transport(
            root=tmp_path,
            config={"STUDIO_ENGINE_TOKEN": "synthetic-test-token"},
            url="http://127.0.0.1",
            client=client,
        )
        request = {
            "task": "music.song",
            "params": {
                "duration_s": 0.01,
                "style": "synthetic",
                "lyrics": "synthetic words",
            },
            "seed": 101,
        }
        result = transport(
            request,
            job_id="01M49HZQ7K5WFE9PA1N3WDN92K",
            descriptor=descriptor().model_dump(mode="json"),
        )
        assert result["sha256"] == run.file_hash(Path(result["source"]))
        assert result["model_id"] == "mock"
        health = client.get(
            "/v1/health", headers={"X-Studio-Engine-Token": "synthetic-test-token"}
        ).json()
        assert health["loaded"] is None and health["job_id"] is None


def test_metrics_harness_exact_bindings_staging_native_axes(tmp_path):
    from engine_mock import descriptor

    run = api("run")
    assert hasattr(run, "measure_take"), "Harness de métricas ausente"
    source = tmp_path / "synthetic.wav"
    sf.write(source, np.full((480, 2), 0.01, dtype=np.float32), 48000, subtype="FLOAT")
    model = descriptor().model_dump(mode="json")
    bindings = {
        task: "mock" for task in ("audio.transcribe", "audio.clap", "audio.aesthetics")
    }
    calls = []

    def fake(request, *, job_id, descriptor, inputs):
        calls.append(request)
        assert inputs[0]["path"] == f"tmp/{job_id}/in/audio.wav"
        assert (
            tmp_path / "data" / inputs[0]["path"]
        ).read_bytes() == source.read_bytes()
        task = request["task"]
        native = {
            "audio.transcribe": {"text": "hola azul", "language": "Spanish"},
            "audio.clap": {
                "score": 0.42,
                "text_truncated": False,
                "audio_window_s": 10,
            },
            "audio.aesthetics": {"PQ": 1.1, "PC": 2.2, "CE": 3.3, "CU": 4.4},
        }[task]
        path = tmp_path / f"data/tmp/{job_id}/analysis.json"
        path.write_text(
            json.dumps(
                {
                    "task": task,
                    "analysis": native,
                    "stages": [
                        {"task": task, "model_id": "mock", "revision": "synthetic-v1"}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return {
            "source": str(path),
            "sha256": run.file_hash(path),
            "job_id": job_id,
            "model_id": "mock",
            "synthetic": True,
        }

    request = {
        "params": {
            "lyrics": "[Verse]\nhola azul",
            "language": "es",
            "style": "ESTILO **[literal]**",
        }
    }
    result = run.measure_take(
        source,
        request,
        root=tmp_path,
        transport=fake,
        descriptors=[model],
        bindings=bindings,
    )
    assert calls[0]["params"] == {"language": "Spanish"}
    assert calls[1]["params"] == {"text": "ESTILO **[literal]**"}
    assert result["audio.transcribe"]["value"]["wer"]["adjusted"] is None
    assert result["audio.clap"]["value"]["seed_controlled"] is False
    assert result["audio.aesthetics"]["value"]["audiobox"] == {
        "PQ": 1.1,
        "PC": 2.2,
        "CE": 3.3,
        "CU": 4.4,
    }


def test_synthetic_thirty_takes_ninety_metric_jobs_and_blind_sheet(tmp_path):
    """Toda la orquestación con datos sintéticos; loudness/métricas reales pendientes."""
    from engine_mock import descriptor

    from scripts import input_preparation

    run = api("run")
    catalog(tmp_path)
    model = descriptor().model_dump(mode="json")
    plan = run.build_plan("mock", root=tmp_path, descriptors=[model])
    plan["fixture_label"] = "SYNTHETIC_CPU_NOT_CANONICAL_GENERATIONS"
    for row in plan["rows"]:
        row["request"]["params"]["duration_s"] = 0.01
        row["preparation"] = input_preparation.prepare(row["request"])
    plan = run.seal_plan(plan)
    calls = []

    def fake(request, *, job_id, inputs=None, **kwargs):
        task = request["task"]
        calls.append((task, job_id))
        directory = tmp_path / f"data/tmp/{job_id}"
        directory.mkdir(parents=True, exist_ok=True)
        if task == "music.song":
            output = directory / "synthetic.wav"
            sf.write(
                output,
                np.full((480, 2), 0.01, dtype=np.float32),
                48000,
                subtype="FLOAT",
            )
        else:
            assert inputs and inputs[0]["path"] == f"tmp/{job_id}/in/audio.wav"
            native = {
                "audio.transcribe": {
                    "text": "Palabras sintéticas de prueba Luz azul",
                    "language": "Spanish",
                },
                "audio.clap": {
                    "score": 0.42,
                    "text_truncated": False,
                    "audio_window_s": 10,
                },
                "audio.aesthetics": {"PQ": 1.1, "PC": 2.2, "CE": 3.3, "CU": 4.4},
            }[task]
            output = directory / "analysis.json"
            output.write_text(
                json.dumps(
                    {
                        "task": task,
                        "analysis": native,
                        "fixture_label": "SYNTHETIC_NATIVE_OUTPUT",
                        "stages": [
                            {
                                "task": task,
                                "model_id": "mock",
                                "revision": "synthetic-v1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
        return {
            "job_id": job_id,
            "model_id": "mock",
            "source": str(output),
            "sha256": run.file_hash(output),
            "synthetic": True,
        }

    def measure(source, request, *, root):
        return run.measure_take(
            source,
            request,
            root=root,
            transport=fake,
            descriptors=[model],
            bindings={
                t: "mock"
                for t in ("audio.transcribe", "audio.clap", "audio.aesthetics")
            },
        )

    result = run.execute(
        plan, root=tmp_path, transport=fake, allow_synthetic=True, metric_runner=measure
    )
    assert len(calls) == 120 and len({job for task, job in calls}) == 120
    assert len(result["takes"]) == 30 and all(t["synthetic"] for t in result["takes"])
    assert all(
        t["metrics"]["audio.transcribe"]["value"]["wer"]["adjusted"] is None
        for t in result["takes"]
    )
    assert all(
        t["metrics"]["audio.aesthetics"]["status"] == "MEASURED"
        for t in result["takes"]
    )
    folder = tmp_path / "synthetic-blind-collection"
    mapping = run.anonymize(result["takes"], folder, root=tmp_path)
    assert len(mapping) == 30 and len({m["code"] for m in mapping}) == 30
    sheet = (folder / "blind/sheet.md").read_text(encoding="utf-8")
    assert "0.4200" in sheet and "PENDING" in sheet and "1.1000" in sheet
    assert "B-01" not in sheet and "mock" not in sheet and "seed" not in sheet
    assert result["acceptance"] is None and not any(
        t["blind_ready"] for t in result["takes"]
    )


def test_plan_hash_pins_descriptor_and_source_catalog(tmp_path):
    from engine_mock import descriptor

    entries = catalog(tmp_path)
    run = api("run")
    model = descriptor().model_dump(mode="json")
    first = run.build_plan("mock", root=tmp_path, descriptors=[model])
    model["revision"] = "synthetic-v2"
    assert (
        run.build_plan("mock", root=tmp_path, descriptors=[model])["hash"]
        != first["hash"]
    )
    entries["B-02"]["style"] += " nunca truncar"
    (tmp_path / "eval/briefs/briefs.yaml").write_text(
        yaml.safe_dump({"version": 1, "briefs": entries}), encoding="utf-8"
    )
    assert (
        run.build_plan("mock", root=tmp_path, descriptors=[model])["hash"]
        != first["hash"]
    )


@pytest.mark.parametrize(
    "language,reference,heard,edits",
    [
        ("en", "[Verse]\nWe're BLUE", "we re blue", 0),
        ("es", "[Estribillo]\nEl árbol canta", "el arbol canta", 1),
        ("es", "[Verse]\nuno dos tres", "uno tres", 1),
        ("en", "[Verse]\none two", "one red two", 1),
    ],
)
def test_wer_plain_edit_distance(language, reference, heard, edits):
    value = api("metrics").wer(reference, heard, language=language, floor=0.1)
    assert value["edits"] == edits
    assert value["adjusted"] == max(0, value["raw"] - 0.1)


@pytest.mark.parametrize("case", ["silence", "nonfinite", "clipped", "mono", "empty"])
def test_linear_gain_rejects_invalid_pcm(case):
    pcm = np.array([[0.1, -0.1]], dtype=np.float32)
    if case == "silence":
        pcm *= 0
    if case == "nonfinite":
        pcm[0, 0] = np.nan
    if case == "clipped":
        pcm[0, 0] = 1.01
    if case == "mono":
        pcm = pcm[:, :1]
    if case == "empty":
        pcm = pcm[:0]
    with pytest.raises(ValueError):
        api("metrics").linear_gain(pcm, measured_lufs=-20, measured_dbtp=-10)


def test_fullscale_one_sample_is_counted_not_rejected(tmp_path):
    raw = tmp_path / "synthetic-one-fullscale.wav"
    sf.write(
        raw,
        np.array([[1.0, 0.1], [0.2, -0.1]], dtype=np.float32),
        48000,
        subtype="FLOAT",
    )
    result = api("metrics").audio_record(raw)
    assert result["fullscale"] == 1 and result["over_fullscale"] == 0


def test_pinned_ffmpeg_real_measurement_only_if_archive_verified(tmp_path):
    metrics = api("metrics")
    try:
        binary, tool = metrics.verified_ffmpeg(ROOT)
    except ValueError as error:
        pytest.skip(f"No se ejecuta FFmpeg no verificado: {error}")
    pcm = np.sin(np.arange(48000 * 3) * 2 * np.pi * 997 / 48000).astype(np.float32)
    raw = tmp_path / "synthetic-tone.wav"
    scaled = tmp_path / "synthetic-scaled.wav"
    sf.write(raw, np.column_stack((pcm * 0.07, pcm * 0.035)), 48000, subtype="FLOAT")
    before = metrics.loudness(raw, binary)
    adjusted, gain = metrics.linear_gain(
        np.column_stack((pcm * 0.07, pcm * 0.035)),
        measured_lufs=before["lufs"],
        measured_dbtp=before["dbtp"],
    )
    sf.write(scaled, adjusted, 48000, subtype="FLOAT")
    after = metrics.loudness(scaled, binary)
    assert tool["sha256"] and abs(after["lufs"] + 16) <= 0.2 and after["dbtp"] <= -1
    assert sf.read(scaled, dtype="float32")[0] == pytest.approx(
        sf.read(raw, dtype="float32")[0] * gain["gain_factor"], abs=1e-7
    )
    normalized = tmp_path / "synthetic-normalized.wav"
    receipt = metrics.normalize_audio(raw, normalized, root=ROOT)
    assert receipt["blind_ready"] and receipt["gain"]["status"] == "VERIFIED"
    assert sf.read(normalized, dtype="float32")[0] == pytest.approx(
        sf.read(raw, dtype="float32")[0] * receipt["gain"]["gain_factor"], abs=1e-7
    )
    # Alto factor de cresta: la ganancia exacta a -16 entra en conflicto con -1 dBTP.
    conflict = tmp_path / "synthetic-peak-conflict.wav"
    impulse = np.column_stack((pcm * 0.001, pcm * 0.001))
    impulse[len(impulse) // 2] = 0.8
    sf.write(conflict, impulse, 48000, subtype="FLOAT")
    conflict_hash = metrics.file_hash(conflict)
    rejected = metrics.normalize_audio(
        conflict, tmp_path / "not-published.wav", root=ROOT
    )
    assert rejected["gain"]["status"] == "PEAK_CONFLICT" and not rejected["blind_ready"]
    assert (
        metrics.file_hash(conflict) == conflict_hash
        and not (tmp_path / "not-published.wav").exists()
    )
    metrics.exclusive_json(
        tmp_path / "native-ffmpeg-synthetic-receipt.json",
        {
            "synthetic": True,
            "purpose": "CPU_FIXED_GAIN_NOT_MUSIC_ACCEPTANCE",
            "tool": tool,
            "before": before,
            "after": after,
            "normalized": receipt,
            "peak_conflict": rejected,
        },
    )
