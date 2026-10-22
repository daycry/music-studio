"""Verificación CPU con doubles explícitos: nunca evidencia de capacidad musical."""

import json
import sys
import types
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pytest

from scripts.eval import capabilities as cli
from scripts.eval import capabilities_native as native
from scripts.eval import capabilities_runtime as runtime
from scripts.eval.capabilities_evidence import (
    compare_pcm,
    eligible,
    file_record,
    pcm_record,
    render_report,
)
from scripts.eval.capabilities_plan import matrix, request_for


@pytest.mark.parametrize(
    "case",
    [
        "music.instrumental",
        "music.extend",
        "music.repaint",
        "music.cover",
        "music.complete",
        "audio.stems",
        "negative_prompt",
        "bpm",
        "key",
        "timbre_ref",
        "lora",
    ],
)
def test_native_parameter_mapping_all_cases(case):
    row = next(
        r for r in matrix() if r["case"] == case and r["surface"] == "native_lab"
    )
    fixture = {
        "style": "original",
        "instrumental_style": "Instrumental pop. No vocals, speech or humming.",
        "lyrics": "[Verse]\noriginal",
        "source": "source.wav",
        "padded_source": "pad.wav",
        "vocals": "vocals.wav",
        "references": {"A": {"path": "a.wav"}, "B": {"path": "b.wav"}},
    }
    request = request_for(row, fixture)
    values = native.native_values(row, request, fixture)
    assert values["duration"] == row["duration_s"]
    assert values["seed"] == row["seed"]
    assert values["thinking"] is (case != "music.complete")
    assert not values["enable_normalization"]
    assert not any(
        values[k] for k in ("use_cot_caption", "use_cot_language", "use_cot_metas")
    )
    if case == "music.extend":
        assert values["task_type"] == "repaint" and values["src_audio"] == "pad.wav"
    if case == "music.complete":
        assert values["task_type"] == "complete" and values["src_audio"] == "vocals.wav"
    if case == "audio.stems":
        assert values["task_type"] == "extract"


def test_pcm_errors_and_report():
    with pytest.raises(ValueError):
        pcm_record(np.ones((2, 5), dtype=np.float64))
    value = np.zeros((2, 5), dtype=np.float32)
    with pytest.raises(ValueError):
        compare_pcm(value, value[:, :4], 1, 2)
    result = compare_pcm(value, value, 0, 5)
    assert result["prefix"]["max_abs_error"] == [0, 0]
    row = matrix()[0]
    assert "pendiente" in render_report([row])
    row.update(
        execution_status="executed",
        verdict="funciona",
        audio_output="own.wav",
        output_seal={"sha256": "a"},
        technical_acceptance=True,
        musical_acceptance={
            "accepted": True,
            "evaluator": "owner",
            "observed_at": "2026-10-06",
            "evidence_sha256": "x",
        },
    )
    assert eligible(row)
    assert "sí" in render_report([row])
    row["test_double"] = True
    assert not eligible(row)


@pytest.mark.parametrize("terminal", ["done", "error", "cancelled", "invalid"])
def test_v1_terminal_evidence_and_raw_copy(tmp_path, terminal):
    row = matrix()[0]
    raw = tmp_path / "data/tmp" / row["job_id"]
    raw.mkdir(parents=True)
    (raw / "output.wav").write_bytes(b"CPU double, not audio")

    class API:
        def request(self, *a, **k):
            return {"ok": True}

        def events(self, job, **k):
            return [
                {
                    "job_id": job,
                    "seq": 9 if terminal == "invalid" else 1,
                    "type": "done" if terminal == "invalid" else terminal,
                    "data": {
                        "artifacts": [
                            {
                                "path": str(
                                    (raw / "output.wav").relative_to(tmp_path / "data")
                                ),
                                "sha256": file_record(raw / "output.wav")["sha256"],
                            }
                        ],
                        "code": "INTERNAL",
                    },
                }
            ]

    result = runtime.execute_v1(
        row,
        {"style": "original", "lyrics": "original"},
        API(),
        tmp_path,
        tmp_path / "evaluation",
        test_double=True,
    )
    assert result["execution_status"] == (
        "executed" if terminal == "done" else "failed"
    )
    assert not result["verified"] and result["verdict"] is None


def test_output_traversal_hash_and_missing_rejected(tmp_path):
    row = matrix()[0]
    with pytest.raises(ValueError, match="missing_audio"):
        runtime.copy_outputs(row, [], tmp_path, tmp_path)
    with pytest.raises(ValueError, match="outside_project"):
        native.contained(tmp_path, "../outside")
    source = tmp_path / "data/tmp" / row["job_id"] / "audio.wav"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"CPU")
    with pytest.raises(ValueError, match="output_hash_changed"):
        runtime.copy_outputs(
            row,
            [{"path": str(source.relative_to(tmp_path / "data")), "sha256": "wrong"}],
            tmp_path,
            tmp_path,
        )


def test_native_result_copy_and_pending(tmp_path):
    row = next(
        r
        for r in matrix()
        if r["surface"] == "native_lab" and r["case"] == "music.song"
    )

    class GPU:
        def snapshot(self):
            return (12000, 10000)

    class Supervisor:
        alive = False

        def load(self, *a, **k):
            pass

        def send(self, message):
            raw = Path(message["output_dir"])
            (raw / "output.wav").write_bytes(b"CPU not music")
            (raw / "receipt.json").write_text("{}")

        def receive(self, timeout):
            return {
                "kind": "result",
                "vram_peak_mb": 7000,
                "artifacts": [{"filename": "output.wav"}],
                "result": {"test_double": True},
            }

        def unload(self):
            pass

    result = runtime.execute_native(
        row,
        {"style": "own", "lyrics": "own"},
        Supervisor(),
        GPU(),
        tmp_path,
        tmp_path / "evidence",
        test_double=True,
    )
    assert result["execution_status"] == "executed" and not result["verified"]
    pending = next(
        r for r in matrix() if r["surface"] == "native_lab" and r["case"] == "lora"
    )
    result = runtime.execute_native(
        pending, {}, None, None, tmp_path, tmp_path / "pending", test_double=True
    )
    assert result["execution_status"] == "pending_prerequisite"
    assert runtime.pending(
        pending,
        {"prerequisites": {p: True for p in pending["prerequisites"]}},
        tmp_path,
    ) == ["lora_prerequisite"]


def text_bundle(root):
    folder = root / "text"
    folder.mkdir()
    for name in ("lyrics.txt", "song-caption.txt", "instrumental-caption.txt"):
        (folder / name).write_text("[Verse]\noriginal", encoding="utf-8")
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "lyrics_declaration": "assistant",
                "files": {p.name: file_record(p) for p in folder.iterdir()},
            }
        )
    )
    return folder


def test_cli_report_execution_pending_unknown_and_changed(tmp_path):
    text_bundle(tmp_path)
    assert (
        cli.main(["plan", "--session", "a", "--text-bundle", "text"], root=tmp_path)
        == 0
    )
    plan = json.loads((tmp_path / "eval/capabilities/a/plan.json").read_text())
    lora = next(
        r for r in plan["rows"] if r["case"] == "lora" and r["surface"] == "native_lab"
    )
    assert (
        cli.main(
            ["execute", "--session", "a", "--case-id", lora["job_id"]], root=tmp_path
        )
        == 0
    )
    assert (
        cli.main(["execute", "--session", "a", "--case-id", "unknown"], root=tmp_path)
        == 2
    )
    assert cli.main(["report", "--session", "a"], root=tmp_path) == 0
    (tmp_path / "text/lyrics.txt").write_text("changed")
    assert (
        cli.main(
            ["execute", "--session", "a", "--case-id", plan["rows"][0]["job_id"]],
            root=tmp_path,
        )
        == 2
    )


def test_capture_splice_source_reference_rng_restored(tmp_path, monkeypatch):
    import random

    name = "acestep.core.generation.handler.generate_music"
    fake = types.ModuleType(name)
    fake.apply_repaint_waveform_splice = lambda **k: k["pred_wavs"]
    monkeypatch.setitem(sys.modules, name, fake)
    source = np.zeros((2, 1440000), dtype=np.float32)

    class DIT:
        def _decode_generate_music_pred_latents(self, **kwargs):
            return (source, None, {})

        def process_src_audio(self, *a):
            return source

        def process_reference_audio(self, *a):
            for _ in range(3):
                random.randint(0, 10)
            return source

        def generate_music(self, **kwargs):
            return kwargs

    lm = types.SimpleNamespace(
        generate_with_stop_condition=lambda **k: k,
        generate_from_formatted_prompt=lambda *a, **k: None,
    )
    state = random.getstate()
    dit = DIT()
    old = dit.process_src_audio
    with native.capture_boundaries(
        types.SimpleNamespace(dit=dit, lm=lm), tmp_path, {}, 501
    ) as receipt:
        dit.process_src_audio("own")
        dit.process_reference_audio("own")
        dit._decode_generate_music_pred_latents()
        fake.apply_repaint_waveform_splice(
            pred_wavs=source, src_wavs=source, crossfade_duration=0.025
        )
    assert receipt["crossfade_duration_effective"] == 0.025
    assert len(receipt["reference_segment_sha256"]) == 3
    assert len(receipt["reference_offsets"]) == 3
    assert dit.process_src_audio == old and random.getstate() == state


@pytest.mark.parametrize("case", ["music.repaint", "music.complete"])
def test_native_generate_cpu_double_emits_real_api_receipt(tmp_path, monkeypatch, case):
    import soundfile as sf

    row = next(
        r for r in matrix() if r["case"] == case and r["surface"] == "native_lab"
    )
    source = np.zeros((2, 60 * 48000), dtype=np.float32)
    sf.write(tmp_path / "source.wav", source.T, 48000, subtype="FLOAT")
    fake = types.ModuleType("acestep.core.generation.handler.generate_music")
    fake.apply_repaint_waveform_splice = lambda **k: k["pred_wavs"]
    monkeypatch.setitem(sys.modules, fake.__name__, fake)

    class DIT:
        def generate_instruction(self, task_type, **kwargs):
            return "CPU double instruction: " + task_type

        def _decode_generate_music_pred_latents(self, **k):
            return (source, None, {})

        def process_src_audio(self, *a):
            return source

        def process_reference_audio(self, *a):
            return None

        def generate_music(self, **k):
            return k

    dit = DIT()

    def generate(dit, lm, params, config, **kwargs):
        dit.process_src_audio(params.src_audio)
        dit._decode_generate_music_pred_latents()
        fake.apply_repaint_waveform_splice(
            pred_wavs=source, src_wavs=source, crossfade_duration=0.025
        )
        kwargs["progress"](0.8)
        return types.SimpleNamespace(
            success=True,
            audios=[{"tensor": source, "sample_rate": 48000, "params": {"seed": 101}}],
        )

    model = types.SimpleNamespace(
        dit=dit,
        lm=types.SimpleNamespace(
            generate_with_stop_condition=lambda **k: k,
            generate_from_formatted_prompt=lambda *a, **k: None,
        ),
        GenerationParams=lambda **k: types.SimpleNamespace(**k),
        GenerationConfig=lambda **k: types.SimpleNamespace(**k),
        generate_music=generate,
        torch=types.SimpleNamespace(
            cuda=types.SimpleNamespace(max_memory_allocated=lambda: 5000)
        ),
    )
    adapter = types.ModuleType("adapter")
    adapter.AceStepAdapter = lambda **k: types.SimpleNamespace(
        runtime=model, effective={"test_double": True}
    )
    adapter.private_upstream_output = nullcontext
    adapter.step_hooks = lambda *a: nullcontext()
    adapter.timed_generation = lambda rt, operation: (
        operation(),
        {"test_double": True},
    )
    adapter.upstream_call = lambda phase, function, *a, **k: function(*a, **k)
    adapter.write_wav = lambda path, samples, rate: sf.write(
        path, samples.T, rate, subtype="FLOAT"
    )
    monkeypatch.setitem(sys.modules, "adapter", adapter)
    lab = native.NativeLabAdapter(row["checkpoint"], row["lm"], "models", tmp_path, {})
    request = request_for(row, {"style": "own", "lyrics": "own"})
    request.update(
        capability_row=row,
        fixture={
            "source": "source.wav",
            "vocals": "source.wav",
            "input_seals": {"source.wav": file_record(tmp_path / "source.wav")},
            "rights": {"source.wav": {"authorized": True, "provenance": "CPU double"}},
        },
    )
    folder = tmp_path / "data/tmp" / row["job_id"]
    folder.mkdir(parents=True)
    events = []
    result = lab.generate(
        request, folder, events.append, types.SimpleNamespace(check=lambda: None)
    )
    if case == "music.repaint":
        assert result["result"]["comparisons"]["original_source:post_splice"][
            "outside_bitexact"
        ]
    else:
        assert result["result"]["params_effective"]["thinking"] is False
        assert result["result"]["captured"]["states"]["processed_source"]
        assert (
            result["result"]["lm_policy"]["reason"]
            == "complete_consumes_vocals_without_lm_codes"
        )
    assert result["artifacts"][0]["filename"] == "output-0.wav"
    assert events and not result["result"]["verified"]
    with pytest.raises(ValueError, match="raw_output_only"):
        lab.generate(
            request, tmp_path, events.append, types.SimpleNamespace(check=lambda: None)
        )
