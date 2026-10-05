import copy
import json
import subprocess
from pathlib import Path

import pytest
from audio_post import verify_manifest, write_manifest
from audio_post.manifest import safe_path

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def manifest(tmp_path):
    (tmp_path / "fixture.txt").write_bytes(b"music-studio fixture\n")
    return json.loads((ROOT / "packages/contracts/examples/cli_run.json").read_text())


@pytest.mark.parametrize("group", ["models", "tools", "inputs"])
def test_commercial_and_and_missing_permission(manifest, tmp_path, group):
    if group == "inputs":
        manifest[group] = [
            {
                "role": "reference",
                "ref": manifest["subject"],
                "sha256": "a" * 64,
                "rights": "licensed",
                "consent": "n_a",
                "commercial_use": False,
            }
        ]
    else:
        manifest[group][0]["commercial_use"] = False
    assert (
        write_manifest(tmp_path / "restricted.json", manifest)["commercial_use"]
        is False
    )
    del manifest[group][0]["commercial_use"]
    assert (
        write_manifest(tmp_path / "unknown.json", manifest)["commercial_use"] is False
    )


@pytest.mark.parametrize("private", ["lyrics", "lyrics_text", "photos", "photo_path"])
def test_private_content_rejected(manifest, tmp_path, private):
    manifest["request"]["params"][private] = "private-content"
    with pytest.raises(ValueError, match="MANIFEST_PRIVATE_CONTENT"):
        write_manifest(tmp_path / "manifest.json", manifest)
    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "C:/secret",
        "C:secret",
        "//server/share",
        "\\\\server\\share",
        "../secret",
        "a/../../secret",
        "a\\..\\secret",
        "a//b",
        "a/./b",
        "file:stream",
    ],
)
def test_unsafe_paths(tmp_path, path):
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        safe_path(tmp_path, path)


def test_symlink_rejected(tmp_path, monkeypatch):
    actual = tmp_path / "real.txt"
    actual.write_text("content")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(actual)
    except OSError:
        # Windows needs an unavailable privilege for creation in this sandbox;
        # still exercise rejection rather than skipping the security guard.
        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda p: p == link or original(p))
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        safe_path(tmp_path, "link.txt")


def test_windows_special_names(tmp_path):
    for name in ["NUL", "CON.txt", "aux.mp3", "dir/file.", "dir/file ", "dir/a\x00b"]:
        with pytest.raises(ValueError, match="UNSAFE_PATH"):
            safe_path(tmp_path, name)


def test_bad_json_does_not_leave_manifest(manifest, tmp_path):
    manifest["future_field"] = float("nan")
    with pytest.raises(ValueError):
        write_manifest(tmp_path / "manifest.json", manifest)
    assert not (tmp_path / "manifest.json").exists()


def test_photo_input_only_reference(manifest, tmp_path):
    manifest["inputs"] = [
        {
            "role": "reference",
            "ref": manifest["subject"],
            "sha256": "a" * 64,
            "rights": "consented",
            "consent": "self",
            "commercial_use": True,
            "path": "uploads/private-photo.png",
        }
    ]
    with pytest.raises(ValueError, match="MANIFEST_PRIVATE_CONTENT"):
        write_manifest(tmp_path / "manifest.json", manifest)


def test_schema_missing_field_and_size(manifest, tmp_path):
    bad = copy.deepcopy(manifest)
    del bad["pipeline"]
    with pytest.raises(ValueError, match="MANIFEST_SCHEMA"):
        verify_manifest(bad, tmp_path)
    manifest["outputs"][0]["bytes"] = 1
    with pytest.raises(ValueError, match="SIZE_MISMATCH"):
        verify_manifest(manifest, tmp_path)
    manifest["outputs"][0]["path"] = "missing.flac"
    with pytest.raises(ValueError, match="OUTPUT_MISSING"):
        verify_manifest(manifest, tmp_path)


def test_cli_empty_and_invalid(tmp_path, manifest):
    import sys

    command = [sys.executable, str(ROOT / "scripts/verify_manifest.py"), str(tmp_path)]
    empty = subprocess.run(command, capture_output=True, text=True, check=False)
    assert empty.returncode == 1 and "MANIFEST_MISSING" in empty.stderr
    (tmp_path / "bad.json").write_text(json.dumps({"manifest_version": 99}))
    bad = subprocess.run(command, capture_output=True, text=True, check=False)
    assert bad.returncode == 1 and "MANIFEST_SCHEMA" in bad.stderr


def test_cli_main_valid_missing_invalid(tmp_path, manifest, capsys):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verify_manifest_cli", ROOT / "scripts/verify_manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main([str(tmp_path / "missing.json")]) == 1
    assert "MANIFEST_MISSING" in capsys.readouterr().err
    write_manifest(tmp_path / "manifest.json", manifest)
    assert module.main([str(tmp_path)]) == 0
    assert "all valid (1 manifests)" in capsys.readouterr().out
    (tmp_path / "fixture.txt").write_bytes(b"tampered")
    assert module.main([str(tmp_path / "manifest.json")]) == 1
    assert "HASH_MISMATCH" in capsys.readouterr().err


@pytest.mark.parametrize("inputs", [None, 42])
def test_malformed_inputs_schema_error(manifest, tmp_path, inputs):
    manifest["inputs"] = inputs
    with pytest.raises(ValueError, match="MANIFEST_SCHEMA"):
        verify_manifest(manifest, tmp_path)


@pytest.mark.parametrize("subject_type", ["take", "character"])
def test_audio_take_requires_song(manifest, tmp_path, subject_type):
    manifest["kind"] = "audio_take"
    manifest["subject"]["type"] = subject_type
    manifest["song_id"] = None
    with pytest.raises(ValueError, match="MANIFEST_SCHEMA"):
        verify_manifest(manifest, tmp_path)


def test_cli_and_character_without_song(manifest, tmp_path):
    assert verify_manifest(manifest, tmp_path)["valid"]
    manifest["kind"] = "image"
    manifest["subject"]["type"] = "character"
    manifest["song_id"] = None
    assert verify_manifest(manifest, tmp_path)["valid"]


@pytest.mark.parametrize("group", ["models", "tools", "inputs"])
def test_verifier_rejects_commercial_permission_tampering(manifest, tmp_path, group):
    if group == "inputs":
        manifest[group] = [
            {
                "role": "reference",
                "ref": manifest["subject"],
                "sha256": "a" * 64,
                "rights": "licensed",
                "consent": "n_a",
                "commercial_use": False,
            }
        ]
    else:
        manifest[group][0]["commercial_use"] = False
    with pytest.raises(ValueError, match="COMMERCIAL_USE_MISMATCH"):
        verify_manifest(manifest, tmp_path)


def test_verifier_rejects_false_aggregate(manifest, tmp_path):
    manifest["commercial_use"] = False
    with pytest.raises(ValueError, match="COMMERCIAL_USE_MISMATCH"):
        verify_manifest(manifest, tmp_path)


def test_legacy_optional_commercial_permission(manifest, tmp_path):
    del manifest["models"][0]["commercial_use"]
    assert verify_manifest(manifest, tmp_path)["valid"]


def verifier_cli():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verify_manifest_cli", ROOT / "scripts/verify_manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_directory_ignores_non_manifest_json(tmp_path, manifest, capsys):
    write_manifest(tmp_path / "manifest.json", manifest)
    for name in ("peaks.json", "timeline.json", "song.json"):
        (tmp_path / name).write_text(json.dumps({"version": 1, "data": []}))
    assert verifier_cli().main([str(tmp_path)]) == 0
    assert "all valid (1 manifests)" in capsys.readouterr().out


@pytest.mark.parametrize(
    "name,payload",
    [
        ("manifest.json", "{"),
        ("manifest.json", "{}"),
        ("manifest-v2.json", "{}"),
        ("bad.json", '{"manifest_version": 99}'),
        ("bad.json", "{"),
    ],
)
def test_cli_directory_does_not_hide_invalid_manifest(
    tmp_path, manifest, name, payload, capsys
):
    write_manifest(tmp_path / "valid.json", manifest)
    (tmp_path / name).write_text(payload)
    assert verifier_cli().main([str(tmp_path)]) == 1
    assert capsys.readouterr().err


def test_cli_directory_only_non_manifests(tmp_path, capsys):
    (tmp_path / "song.json").write_text('{"title": "song"}')
    assert verifier_cli().main([str(tmp_path)]) == 1
    assert "MANIFEST_MISSING" in capsys.readouterr().err
