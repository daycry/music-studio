import importlib
import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest


def test_direct_script_entrypoint_bootstraps_repository_imports():
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "scripts/eval/capabilities.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Matriz T-10 local" in result.stdout


def test_canonical_cli_subprocess_plan_and_report_original_bundle():
    root = Path(__file__).resolve().parents[3]
    session = "t10-fix1-cpu-command-test-" + uuid.uuid4().hex
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.eval.capabilities",
            "plan",
            "--session",
            session,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    folder = root / "eval/capabilities" / session
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    from scripts.eval.capabilities_evidence import file_record

    assert set(plan["source_seal"]) == {
        p.relative_to(root).as_posix()
        for p in (root / "scripts/eval").glob("capabilities*.py")
    }
    for key, seal in plan["source_seal"].items():
        assert PurePosixPath(key).parts[:2] == ("scripts", "eval")
        assert file_record(root.joinpath(*PurePosixPath(key).parts)) == seal
    assert len({row["case"] for row in plan["rows"]}) == 13
    assert {row["surface"] for row in plan["rows"]} == {"v1", "native_lab"}
    assert not any(row["verified"] for row in plan["rows"])
    report = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.eval.capabilities",
            "report",
            "--session",
            session,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert report.returncode == 0, report.stderr
    assert "pendiente" in (folder / "report.md").read_text(encoding="utf-8")


def test_plan_cli_writes_complete_immutable_plan(tmp_path):
    name = "scripts.eval.capabilities"
    main = (
        importlib.import_module(name).main
        if importlib.util.find_spec(name)
        else lambda *a, **k: 1
    )
    bundle = tmp_path / "text"
    bundle.mkdir()
    from scripts.eval.capabilities_evidence import file_record

    for name in ("lyrics.txt", "song-caption.txt", "instrumental-caption.txt"):
        (bundle / name).write_text("Original test content", encoding="utf-8")
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "lyrics_declaration": "assistant",
                "files": {p.name: file_record(p) for p in bundle.iterdir()},
            }
        )
    )
    assert (
        main(["plan", "--session", "session", "--text-bundle", "text"], root=tmp_path)
        == 0
    )
    plan = json.loads((tmp_path / "eval/capabilities/session/plan.json").read_text())
    assert len({r["case"] for r in plan["rows"]}) == 13
    assert (
        main(["plan", "--session", "session", "--text-bundle", "text"], root=tmp_path)
        == 2
    )


def test_windows_source_seal_resolves_as_posix_paths(tmp_path, monkeypatch):
    from scripts.eval.capabilities import main
    from scripts.eval.capabilities_evidence import file_record

    bundle = tmp_path / "text"
    bundle.mkdir()
    for name in ("lyrics.txt", "song-caption.txt", "instrumental-caption.txt"):
        (bundle / name).write_text("Original regression content", encoding="utf-8")
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "lyrics_declaration": "assistant",
                "files": {p.name: file_record(p) for p in bundle.iterdir()},
            }
        ),
        encoding="utf-8",
    )
    source_folder = tmp_path / "scripts/eval"
    source_folder.mkdir(parents=True)
    names = ("capabilities.py", "capabilities_native.py")
    for name in names:
        (source_folder / name).write_text(f"# Source {name}\n", encoding="utf-8")

    relative_to = Path.relative_to

    def windows_source_relative_to(path, *args, **kwargs):
        relative = relative_to(path, *args, **kwargs)
        if path.parent == source_folder:
            return PureWindowsPath(*relative.parts)
        return relative

    # Exercise Windows serialization on every host, with real source files and CLI plan.
    monkeypatch.setattr(Path, "relative_to", windows_source_relative_to)
    assert (
        main(
            ["plan", "--session", "posix-seal", "--text-bundle", "text"], root=tmp_path
        )
        == 0
    )
    plan = json.loads(
        (tmp_path / "eval/capabilities/posix-seal/plan.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(plan["source_seal"]) == {f"scripts/eval/{name}" for name in names}
    for key, seal in plan["source_seal"].items():
        posix = PurePosixPath(key)
        assert posix.parts == ("scripts", "eval", posix.name)
        assert (PurePosixPath("/studio") / posix).parent == PurePosixPath(
            "/studio/scripts/eval"
        )
        assert file_record(tmp_path.joinpath(*posix.parts)) == seal
        # A Linux consumer treats the original Windows string as one literal filename.
        literal_windows = PurePosixPath(str(PureWindowsPath(key)))
        assert literal_windows.parts == (str(PureWindowsPath(key)),)
        assert literal_windows != posix


@pytest.fixture
def sealed_cli_plan(tmp_path):
    from scripts.eval.capabilities import main
    from scripts.eval.capabilities_evidence import file_record

    bundle = tmp_path / "text"
    bundle.mkdir()
    for name in ("lyrics.txt", "song-caption.txt", "instrumental-caption.txt"):
        (bundle / name).write_text("Original custody content", encoding="utf-8")
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "lyrics_declaration": "assistant",
                "files": {p.name: file_record(p) for p in bundle.iterdir()},
            }
        ),
        encoding="utf-8",
    )
    source = tmp_path / "scripts/eval/capabilities.py"
    source.parent.mkdir(parents=True)
    source.write_text("# Original harness\n", encoding="utf-8")
    assert (
        main(["plan", "--session", "custody", "--text-bundle", "text"], root=tmp_path)
        == 0
    )
    return tmp_path, bundle, source, tmp_path / "eval/capabilities/custody"


@pytest.mark.parametrize(
    ("changed", "error"),
    [
        ("plan", "plan_changed"),
        ("harness", "harness_changed_since_plan"),
        ("text", "original_inputs_changed"),
        ("rights", "lyrics_rights_required"),
    ],
)
def test_posix_plan_keeps_custody_checks(sealed_cli_plan, changed, error, capsys):
    from scripts.eval.capabilities import main
    from scripts.eval.capabilities_evidence import file_record

    root, bundle, source, folder = sealed_cli_plan
    plan_before = (folder / "plan.json").read_bytes()
    if changed == "plan":
        with (folder / "plan.json").open("a", encoding="utf-8") as stream:
            stream.write("\n")
    elif changed == "harness":
        source.write_text("# Changed harness\n", encoding="utf-8")
    else:
        manifest = json.loads((bundle / "manifest.json").read_text())
        if changed == "rights":
            manifest["lyrics_declaration"] = "undeclared"
        else:
            caption = bundle / "song-caption.txt"
            caption.write_text("Changed caption", encoding="utf-8")
            manifest["files"][caption.name] = file_record(caption)
        (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    seal_before = (folder / "plan-seal.json").read_bytes()
    assert main(["report", "--session", "custody"], root=root) == 2
    assert error in capsys.readouterr().out
    assert not (folder / "report.md").exists()
    assert (folder / "plan-seal.json").read_bytes() == seal_before
    if changed != "plan":
        assert (folder / "plan.json").read_bytes() == plan_before


def test_cli_rejects_changed_resource_seal_before_execution(sealed_cli_plan, capsys):
    from scripts.eval.capabilities import main
    from scripts.eval.capabilities_evidence import file_record

    root, _, _, folder = sealed_cli_plan
    resource_input = root / "resource.txt"
    resource_input.write_text("Authorized original", encoding="utf-8")
    seal = file_record(resource_input)
    resource_input.write_text("Changed input", encoding="utf-8")
    (root / "resources.json").write_text(
        json.dumps({"input_seals": {"resource.txt": seal}}), encoding="utf-8"
    )
    plan = json.loads((folder / "plan.json").read_text())
    row = plan["rows"][0]
    assert (
        main(
            [
                "execute",
                "--session",
                "custody",
                "--case-id",
                row["job_id"],
                "--resources",
                "resources.json",
            ],
            root=root,
        )
        == 2
    )
    assert "audio_input_changed" in capsys.readouterr().out
    assert not (folder / row["job_id"] / "resources-receipt.json").exists()
    assert not (folder / row["job_id"] / "result.json").exists()


@pytest.mark.parametrize(
    ("case", "missing"),
    [
        ("music.retake", "authorized_source_audio"),
        ("timbre_ref", "authorized_reference_audio"),
    ],
)
def test_posix_cli_plan_preserves_missing_input_status(sealed_cli_plan, case, missing):
    from scripts.eval.capabilities import main

    root, _, _, folder = sealed_cli_plan
    plan = json.loads((folder / "plan.json").read_text())
    row = next(
        row
        for row in plan["rows"]
        if row["surface"] == "native_lab"
        and row["case"] == case
        and (case != "timbre_ref" or row["control"]["reference"])
    )
    assert (
        main(["execute", "--session", "custody", "--case-id", row["job_id"]], root=root)
        == 0
    )
    result = json.loads((folder / row["job_id"] / "result.json").read_text())
    assert result["execution_status"] == "pending_prerequisite"
    assert missing in result["missing_prerequisites"]
    assert result["verdict"] is None


def test_native_cli_requires_container_before_loading_runtime(
    sealed_cli_plan, monkeypatch, capsys
):
    from scripts.eval.capabilities import main

    root, _, _, folder = sealed_cli_plan
    plan = json.loads((folder / "plan.json").read_text())
    row = next(
        row
        for row in plan["rows"]
        if row["surface"] == "native_lab" and row["case"] == "music.instrumental"
    )
    exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda path: False if path == Path("/.dockerenv") else exists(path),
    )
    assert (
        main(["execute", "--session", "custody", "--case-id", row["job_id"]], root=root)
        == 2
    )
    assert "native_container_required" in capsys.readouterr().out
    assert not (folder / row["job_id"] / "result.json").exists()
