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


def test_preparation_reference_missing_rejected(manifest, tmp_path):
    manifest["preparation"] = {"sha256": "a" * 64}
    with pytest.raises(ValueError, match="PREPARATION_MISSING"):
        verify_manifest(manifest, tmp_path)


def _cli():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verify_manifest_cli_root", ROOT / "scripts/verify_manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _server_style(tmp_path, manifest):
    """Manifiesto del server: rutas `data/...` relativas a la raíz que contiene data/."""
    take = tmp_path / "root" / "data" / "songs" / "S" / "takes" / "T"
    take.mkdir(parents=True)
    (take / "fixture.txt").write_bytes(b"music-studio fixture\n")
    manifest["outputs"][0]["path"] = "data/songs/S/takes/T/fixture.txt"
    (take / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path / "root", take


def test_cli_validates_server_manifests_with_data_relative_paths(
    tmp_path, manifest, capsys
):
    root, take = _server_style(tmp_path, manifest)
    module = _cli()
    assert module.main([str(take / "manifest.json")]) == 0
    assert module.main([str(root / "data" / "songs")]) == 0
    assert "all valid (1 manifests)" in capsys.readouterr().out
    (take / "fixture.txt").write_bytes(b"tampered")
    assert module.main([str(take / "manifest.json")]) == 1
    assert "HASH_MISMATCH" in capsys.readouterr().err


def test_cli_data_dir_is_the_data_directory_itself(tmp_path, manifest, capsys):
    """STUDIO_DATA_ROOT aislado: el directorio de datos no se llama `data` ni tiene hijo `data/`."""
    data_dir = tmp_path / "e2e-data"
    take = data_dir / "songs" / "S" / "takes" / "T"
    take.mkdir(parents=True)
    (take / "fixture.txt").write_bytes(b"music-studio fixture\n")
    manifest["outputs"][0]["path"] = "data/songs/S/takes/T/fixture.txt"
    (take / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    module = _cli()
    assert module.main([str(data_dir / "songs")]) == 0  # raíz derivada del manifiesto
    capsys.readouterr()
    assert module.main([str(data_dir / "songs"), "--data-dir", str(data_dir)]) == 0
    assert "all valid" in capsys.readouterr().out
    assert (take / "manifest.json").read_text().count('"path": "data/') == 1
    (take / "fixture.txt").write_bytes(b"tampered")
    assert module.main([str(take / "manifest.json"), "--data-dir", str(data_dir)]) == 1
    assert "HASH_MISMATCH" in capsys.readouterr().err


def _put(take_dir, payload, rel, base):
    take_dir.mkdir(parents=True, exist_ok=True)
    (take_dir / "fixture.txt").write_bytes(payload)
    value = json.loads(json.dumps(base))
    value["outputs"][0]["path"] = rel
    (take_dir / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
    return value


GOOD = b"music-studio fixture" + bytes([10])
TAKE_REL = "data/songs/S/takes/T/fixture.txt"


def test_cli_s1_corrupted_copy_is_not_validated_against_another_data(
    tmp_path, manifest
):
    live = tmp_path / "root" / "data" / "songs" / "S" / "takes" / "T"
    snap = tmp_path / "root" / "snapshot" / "songs" / "S" / "takes" / "T"
    _put(live, GOOD, TAKE_REL, manifest)
    _put(snap, b"CORRUPTED", TAKE_REL, manifest)
    module = _cli()
    assert module.main([str(live / "manifest.json")]) == 0
    assert module.main([str(snap / "manifest.json")]) == 1  # snapshot/ != data/


def test_cli_derives_data_root_from_manifest_without_option(tmp_path, manifest):
    module = _cli()
    for name in ("x/data", "e2e-data"):
        take = tmp_path / name / "songs" / "S" / "takes" / "T"
        _put(take, GOOD, TAKE_REL, manifest)
        assert module.main([str(take / "manifest.json")]) == 0
        assert (
            module.main(
                [str(take / "manifest.json"), "--data-dir", str(tmp_path / name)]
            )
            == 0
        )
        (take / "fixture.txt").write_bytes(b"tampered")
        assert module.main([str(take / "manifest.json")]) == 1


def test_cli_data_dir_must_contain_the_manifest_folder(tmp_path, manifest, capsys):
    dd = tmp_path / "dd"
    take = dd / "songs" / "S" / "takes" / "T"
    _put(take, GOOD, TAKE_REL, manifest)
    module = _cli()
    assert (
        module.main([str(take / "manifest.json"), "--data-dir", str(tmp_path / "otro")])
        == 1
    )
    assert "OUTPUT_OUTSIDE_TAKE" in capsys.readouterr().err


def test_cli_rejects_mixed_data_and_relative_outputs(tmp_path, manifest, capsys):
    dd = tmp_path / "dd"
    take = dd / "songs" / "S" / "takes" / "T"
    value = _put(take, GOOD, TAKE_REL, manifest)
    second = dict(value["outputs"][0])
    second["path"] = "fixture.txt"
    value["outputs"].append(second)
    (take / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
    module = _cli()
    for extra in ([], ["--data-dir", str(dd)]):
        assert module.main([str(take / "manifest.json"), *extra]) == 1  # S2
    (dd / "fixture.txt").write_bytes(GOOD)
    assert module.main([str(take / "manifest.json"), "--data-dir", str(dd)]) == 1  # S2b
    assert "OUTPUT_MIXED_PATHS" in capsys.readouterr().err


def test_cli_rejects_manifest_pointing_to_another_take(tmp_path, manifest, capsys):
    dd = tmp_path / "dd"
    _put(dd / "songs" / "S" / "takes" / "T", GOOD, TAKE_REL, manifest)
    other = dd / "songs" / "S" / "takes" / "T1"
    other.mkdir(parents=True)
    (other / "manifest.json").write_text(
        json.dumps(
            {
                **manifest,
                "outputs": [{**manifest["outputs"][0], "path": TAKE_REL}],
            }
        ),
        encoding="utf-8",
    )
    module = _cli()
    assert module.main([str(other / "manifest.json"), "--data-dir", str(dd)]) == 1  # S3
    assert "OUTPUT_OUTSIDE_TAKE" in capsys.readouterr().err


def test_cli_m0_relative_manifests_unchanged(tmp_path, manifest):
    run = tmp_path / "m0" / "run"
    _put(run, GOOD, "fixture.txt", manifest)
    module = _cli()
    assert module.main([str(run / "manifest.json")]) == 0  # S4
    (run / "fixture.txt").write_bytes(b"x")
    assert module.main([str(run / "manifest.json")]) == 1  # S4b


@pytest.mark.parametrize(
    "rel",
    [
        "data/songs/S/./takes/T/fixture.txt",
        "data/songs//S/takes/T/fixture.txt",
        "data/songs/S/takes/T/fixture.txt/",
        "data//songs/S/takes/T/fixture.txt",
        "data/songs/S/takes/../takes/T/fixture.txt",
        "data/fixture.txt",
    ],
)
def test_cli_rejects_non_canonical_data_paths(tmp_path, manifest, rel):
    take = tmp_path / "a" / "songs" / "S" / "takes" / "T"
    _put(take, GOOD, rel, manifest)
    module = _cli()
    assert module.main([str(take / "manifest.json")]) == 1
    assert (
        module.main([str(take / "manifest.json"), "--data-dir", str(tmp_path / "a")])
        == 1
    )


@pytest.mark.parametrize("bad", ["x", {"role": "master"}, {"path": 5}])
def test_cli_malformed_outputs_are_a_clean_error(tmp_path, manifest, bad, capsys):
    take = tmp_path / "a" / "songs" / "S" / "takes" / "T"
    value = _put(take, GOOD, TAKE_REL, manifest)
    value["outputs"].append(bad)
    (take / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
    assert _cli().main([str(take / "manifest.json")]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_cli_data_dir_comparison_ignores_case_on_windows(tmp_path, manifest):
    import sys

    if sys.platform != "win32":
        pytest.skip("la comparación insensible a mayúsculas es de Windows")
    take = tmp_path / "a" / "songs" / "S" / "takes" / "T"
    _put(take, GOOD, TAKE_REL, manifest)
    module = _cli()
    assert (
        module.main(
            [str(take / "manifest.json"), "--data-dir", str(tmp_path / "a").upper()]
        )
        == 0
    )
    assert (
        module.main([str(Path(str(take).replace("songs", "SONGS")) / "manifest.json")])
        == 0
    )
