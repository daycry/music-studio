"""Matriz completa y entradas propias, no modelos ni audio históricos."""

import pytest


def test_default_matrix_has_160_fresh_jobs_and_alternates_arms(harness_module):
    planner = harness_module("benchmark_plan")
    assert callable(getattr(planner, "matrix_runs", None)), "Falta matriz íntegra"
    runs = planner.matrix_runs()
    assert len(runs) == 160
    assert len({r["job_id"] for r in runs}) == 160
    assert len({r["run_id"] for r in runs}) == 160
    assert len({(r["config_id"], r["duration_s"]) for r in runs}) == 20
    assert {r["duration_s"] for r in runs} == {30, 60, 180, 300}
    for config in {r["config_id"] for r in runs}:
        for duration in (30, 60, 180, 300):
            cell = [
                r
                for r in runs
                if r["config_id"] == config and r["duration_s"] == duration
            ]
            assert sorted(r["repetition"] for r in cell) == [0, 0, 1, 1, 2, 2, 3, 3]
            assert {r["storage"] for r in cell} == {"bind", "container_copy"}
            assert sum(r["phase"] == "process_cold" for r in cell) == 2
    assert not {r["job_id"] for r in planner.matrix_runs()} & {
        r["job_id"] for r in runs
    }


def test_inputs_require_authorship_no_audio_codes_and_all_durations(harness_module):
    planner = harness_module("benchmark_plan")
    assert callable(getattr(planner, "validate_input", None)), "Falta puerta de autoría"
    sample = {
        "task": "music.song",
        "authorship": {"declared": True, "basis": "original"},
        "params": {
            "lyrics": "fixture sintético",
            "style": "pop",
            "language": "es",
            "duration_s": 300,
        },
    }
    assert planner.validate_input(sample, 300)["params"]["duration_s"] == 300
    with pytest.raises(ValueError, match="authorship"):
        planner.validate_input({**sample, "authorship": {"declared": False}}, 300)
    with pytest.raises(ValueError, match="reused"):
        planner.validate_input({**sample, "audio_codes": "old"}, 300)
    with pytest.raises(ValueError, match="duration"):
        planner.validate_input(sample, 60)
