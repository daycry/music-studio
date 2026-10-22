"""Preparar no publica un informe ni confunde dobles con medición GPU."""

import json


def test_finished_session_replay_checks_seal_without_backend(harness_module, tmp_path):
    cli = harness_module("benchmark")
    evidence = harness_module("benchmark_evidence")
    folder = tmp_path / "session"
    folder.mkdir()
    evidence.exclusive_json(folder / "summary.json", {"complete": True, "rows": 160})
    (folder / "report.md").write_text("real report")
    evidence.exclusive_json(folder / "seal.json", evidence.seal_files(folder))
    assert cli.finished_session(folder) == 0
    (folder / "report.md").write_text("tampered")
    import pytest

    with pytest.raises(ValueError, match="evidence_changed"):
        cli.finished_session(folder)


def test_prepare_only_writes_plan_but_no_public_report(harness_module, tmp_path):
    cli = harness_module("benchmark")
    assert callable(getattr(cli, "main", None)), "Falta CLI canónica"
    planner = harness_module("benchmark_plan")
    models = tmp_path / "models"
    models.mkdir()
    (models / "models.lock.json").write_text('{"models":{}}')
    fixtures = {}
    for duration in (30, 60, 180, 300):
        path = tmp_path / f"fixture-{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "lyrics": "CPU test",
                        "style": "test",
                        "language": "es",
                        "duration_s": duration,
                    },
                }
            )
        )
        fixtures[str(duration)] = {"path": path.name, "sha256": planner.file_hash(path)}
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"fixtures_by_duration": fixtures}))
    assert (
        cli.main(
            [
                "--matrix",
                "default",
                "--prepare-only",
                "--inputs",
                str(inputs),
                "--image",
                "sha256:test",
            ],
            root=tmp_path,
        )
        == 0
    )
    plans = list((tmp_path / ".cache/dev-cycle/t09/runtime").glob("*/plan.json"))
    assert len(plans) == 1 and len(json.loads(plans[0].read_text())["runs"]) == 160
    assert not (tmp_path / "eval/results/benchmark-5070.md").exists()


def test_canonical_missing_inputs_fails_without_fake_report(harness_module, tmp_path):
    cli = harness_module("benchmark")
    assert callable(getattr(cli, "main", None)), "Falta CLI canónica"
    assert cli.main(["--matrix", "default"], root=tmp_path) == 2
    assert not (tmp_path / "eval/results/benchmark-5070.md").exists()
