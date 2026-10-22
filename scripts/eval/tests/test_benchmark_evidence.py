"""Recibos y recomendaciones limitadas a observación real válida."""

import pytest


def test_event_sequence_and_single_terminal(harness_module):
    evidence = harness_module("benchmark_evidence")
    assert callable(getattr(evidence, "validate_events", None)), (
        "Falta puerta de eventos"
    )
    events = [
        {"seq": 1, "type": "stage", "job_id": "job"},
        {"seq": 2, "type": "done", "job_id": "job"},
    ]
    assert evidence.validate_events(events, "job")["type"] == "done"
    for broken in (
        [events[1]],
        events + [{"seq": 3, "type": "error", "job_id": "job"}],
        [{**events[0], "job_id": "other"}, events[1]],
    ):
        with pytest.raises(ValueError):
            evidence.validate_events(broken, "job")


def test_reference_uses_exact_three_valid_warm_same_cell(harness_module):
    evidence = harness_module("benchmark_evidence")
    assert callable(getattr(evidence, "reference_rtf", None)), (
        "Falta referencia elegible"
    )
    rows = [
        {
            "run_id": str(i),
            "phase": "warm",
            "config_id": "base",
            "duration_s": 300,
            "storage": "bind",
            "fixture_sha256": "a",
            "mode": "bf16",
            "rtf": rtf,
            "valid": True,
            "shared_gpu_observed": False,
        }
        for i, rtf in enumerate((0.2, 0.3, 0.4))
    ]
    assert evidence.reference_rtf(rows, rows[0]) == (0.3, ["0", "1", "2"])
    assert evidence.reference_rtf(rows[:-1], rows[0]) == (None, [])
    rows[2]["storage"] = "container_copy"
    assert evidence.reference_rtf(rows, rows[0]) == (None, [])


def test_report_redacts_private_fields_and_preserves_missing_rows(harness_module):
    evidence = harness_module("benchmark_evidence")
    assert callable(getattr(evidence, "render_report", None)), "Falta reporte honesto"
    plan = {
        "session_id": "session",
        "runs": [
            {
                "run_id": "r",
                "config_id": "base",
                "duration_s": 300,
                "storage": "bind",
                "phase": "process_cold",
                "repetition": 0,
            }
        ],
        "baseline": {"used_mb": 1300},
    }
    report = evidence.render_report(
        plan,
        [
            {
                "run_id": "r",
                "lyrics": "SECRET_LYRICS",
                "token": "SECRET_TOKEN",
                "personal_path": "C:/Users/private",
                "status": "missing_weights",
                "valid": False,
            }
        ],
    )
    assert "SECRET" not in report and "C:/" not in report
    assert "missing_weights" in report and "300" in report
    assert "null" in report and "pendiente" in report


def test_report_publishes_baseline_without_private_fields(harness_module):
    evidence = harness_module("benchmark_evidence")
    plan = {
        "session_id": "CPU",
        "runs": [],
        "baseline": {"used_mb": 1497.123, "free_mb": 10700.25, "secret": "SECRET"},
        "configs": [],
    }
    report = evidence.render_report(plan, [])
    assert "1497.1230" in report and "10700.2500" in report
    assert "SECRET" not in report
    assert "VRAM en reposo" in report
    missing = evidence.render_report(
        {"session_id": "CPU", "runs": [], "configs": []}, []
    )
    assert "VRAM en reposo" in missing and "null" in missing


def test_report_copy_amortization_and_warm_dispersion(harness_module):
    evidence = harness_module("benchmark_evidence")
    plan = {
        "session_id": "CPU",
        "runs": [],
        "configs": [{"config_id": "base"}],
        "durations_s": [30],
    }
    rows = []
    for arm in ("bind", "container_copy"):
        for i in range(4):
            row = {
                "run_id": f"{arm}-{i}",
                "config_id": "base",
                "storage": arm,
                "duration_s": 30,
                "phase": "process_cold" if i == 0 else "warm",
                "valid": True,
                "load_s": 41 if arm == "bind" else 11,
                "copy_s": 90 if arm == "container_copy" else 0,
                "vram_peak_mb": 7000,
                "inference_s": 10.0 + i,
                "rtf": (10 + i) / 30,
                "fixture_sha256": "F",
                "mode": "bf16",
                "shared_gpu_observed": False,
            }
            rows.append(row)
            plan["runs"].append(row)
    report = evidence.render_report(plan, rows)
    assert "copy_s" in report and "90" in report
    assert "break_even_cold_loads" in report and "3.0000" in report
    assert "warm_inference_stdev_s" in report and "1.0000" in report
    assert "warm_inference_min_s" in report and "11.0000" in report
    partial = evidence.render_report(plan, rows[:2])
    assert "warm_inference_stdev_s" in partial and "null" in partial


def test_recommendation_load_uses_cold_only(harness_module):
    evidence = harness_module("benchmark_evidence")
    runs = [
        {
            "run_id": str(i),
            "config_id": "base",
            "phase": "process_cold" if i % 4 == 0 else "warm",
        }
        for i in range(32)
    ]
    plan = {"configs": [{"config_id": "base"}], "runs": runs}
    rows = [
        {
            **r,
            "valid": True,
            "rtf": 0.2,
            "shared_gpu_observed": False,
            "spill_assessment": "not_detected",
            "load_s": 31 if r["phase"] == "process_cold" else 0,
            "vram_peak_mb": 7000,
        }
        for r in runs
    ]
    report = evidence.recommendations(plan, rows)
    assert "carga cold mediana 31.000 s" in report
    assert "carga warm mediana 0.000 s" in report
