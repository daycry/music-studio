import hashlib
import sys
from pathlib import Path

import audio_post
import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]


def test_explicit_root_real_audio(tmp_path, ffmpeg_path):
    t = np.arange(48000) / 48000
    samples = np.column_stack([0.12 * np.sin(2 * np.pi * 440 * t)] * 2)
    source = tmp_path / "raw.wav"
    sf.write(source, samples, 48000, subtype="FLOAT")
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    result = audio_post.process_audio(
        source,
        tmp_path / "take",
        root=tmp_path,
        expected_duration_s=1,
        ffmpeg=ffmpeg_path,
    )
    assert {o["role"] for o in result["outputs"]} == {"master", "listen", "peaks"}
    assert abs(result["post"]["lufs_out"] + 14) <= 0.5
    assert result["post"]["true_peak_dbtp"] <= -1
    master, sr = sf.read(tmp_path / "take/master.flac", always_2d=True)
    assert sr == 48000
    assert np.max(np.abs(master - samples)) < 2**-22
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_existing_destination_before_read(tmp_path, monkeypatch, ffmpeg_path):
    from audio_post import pipeline

    destination = tmp_path / "take"
    destination.mkdir()
    (destination / "unknown").write_bytes(b"keep")
    monkeypatch.setattr(
        pipeline.sf, "read", lambda *a, **k: pytest.fail("read before validation")
    )
    with pytest.raises(FileExistsError):
        audio_post.process_audio(
            tmp_path / "raw.wav", destination, expected_duration_s=1, ffmpeg=ffmpeg_path
        )
    assert (destination / "unknown").read_bytes() == b"keep"


@pytest.mark.parametrize(
    "case",
    [
        "source_outside",
        "dest_outside",
        "traversal",
        "missing_root",
        "root_alias",
        "dest_alias",
    ],
)
def test_unsafe_before_effects(tmp_path, monkeypatch, case, ffmpeg_path):
    from audio_post import pipeline

    root = tmp_path / "data"
    root.mkdir()
    source, destination = root / "raw.wav", root / "take"
    if case == "source_outside":
        source = tmp_path / "raw.wav"
    elif case == "dest_outside":
        destination = tmp_path / "take"
    elif case == "traversal":
        source = root / ".." / "raw.wav"
    elif case == "missing_root":
        root = root / "absent"
    elif case == "root_alias":
        root = root / ".." / "data"
    else:
        destination = root / ".." / "data" / "take"
    monkeypatch.setattr(
        pipeline.sf, "read", lambda *a, **k: pytest.fail("unexpected read")
    )
    monkeypatch.setattr(
        pipeline, "_ffmpeg", lambda *a, **k: pytest.fail("unexpected ffmpeg")
    )
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        audio_post.process_audio(
            source, destination, root=root, expected_duration_s=1, ffmpeg=ffmpeg_path
        )
    assert list((tmp_path / "data").iterdir()) == []


@pytest.mark.parametrize("where", ["root", "ancestor", "source", "destination"])
@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(
            "junction",
            marks=pytest.mark.skipif(
                sys.platform != "win32", reason="Windows directory junctions only"
            ),
        ),
        "symlink",
    ],
)
def test_real_link_rejected(tmp_path, monkeypatch, where, kind, ffmpeg_path):
    import os
    import subprocess

    from audio_post import pipeline

    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    if kind == "junction":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(real)],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
    else:
        try:
            os.symlink(real, link, target_is_directory=True)
        except OSError as error:
            pytest.skip(f"native symlink privilege unavailable: {error}")
    try:
        root, source, destination = tmp_path, tmp_path / "raw.wav", tmp_path / "take"
        if where == "root":
            root, source, destination = link, link / "raw.wav", link / "take"
        elif where == "ancestor":
            (real / "data").mkdir()
            root, source, destination = (
                link / "data",
                link / "data/raw.wav",
                link / "data/take",
            )
        elif where == "source":
            source = link / "raw.wav"
        else:
            destination = link / "take"
        monkeypatch.setattr(
            pipeline.sf, "read", lambda *a, **k: pytest.fail("unexpected read")
        )
        with pytest.raises(ValueError, match="UNSAFE_PATH"):
            audio_post.process_audio(
                source,
                destination,
                root=root,
                expected_duration_s=1,
                ffmpeg=ffmpeg_path,
            )
        assert not (real / "take").exists()
    finally:
        if kind == "symlink":
            link.unlink()
        else:
            link.rmdir()


@pytest.mark.parametrize("failure", ["transcode", "nonfinite", "duration", "silence"])
def test_failure_preserves_source_and_cleans_own_output(tmp_path, failure, ffmpeg_path):
    t = np.arange(48000) / 48000
    samples = 0.12 * np.sin(2 * np.pi * 440 * t)
    if failure == "nonfinite":
        samples[20] = np.nan
    elif failure == "silence":
        samples[:] = 0
    source = tmp_path / "raw.wav"
    sf.write(source, samples, 48000, subtype="FLOAT")
    before = source.read_bytes()
    codes = {
        "transcode": "AUDIO_TRANSCODE_FAILED",
        "nonfinite": "AUDIO_NONFINITE",
        "duration": "AUDIO_DURATION",
        "silence": "AUDIO_SILENCE",
    }
    with pytest.raises(ValueError, match=codes[failure]):
        audio_post.process_audio(
            source,
            tmp_path / "take",
            root=tmp_path,
            expected_duration_s=3 if failure == "duration" else 1,
            ffmpeg=(
                ROOT / "tools/node/22.23.2/win-x64/node.exe"
                if sys.platform == "win32"
                else Path(sys.executable)
            )
            if failure == "transcode"
            else ffmpeg_path,
        )
    assert source.read_bytes() == before
    assert not (tmp_path / "take").exists()


@pytest.mark.parametrize("replace_at", ["read", "transcode"])
def test_replaced_owned_directory_is_preserved(
    tmp_path, monkeypatch, replace_at, ffmpeg_path
):
    from audio_post import pipeline

    root = tmp_path / "data"
    root.mkdir()
    t = np.arange(48000) / 48000
    source = root / "raw.wav"
    sf.write(source, 0.12 * np.sin(2 * np.pi * 440 * t), 48000, subtype="FLOAT")
    original_read, original_ffmpeg = pipeline.sf.read, pipeline._ffmpeg
    replacement = root if replace_at == "read" else root / "take"
    moved = tmp_path / "moved"
    sentinel = replacement / "master.flac"

    def swap():
        if moved.exists():
            return
        replacement.rename(moved)
        replacement.mkdir()
        sentinel.write_bytes(b"foreign master must survive")

    def read(*args, **kwargs):
        result = original_read(*args, **kwargs)
        swap()
        return result

    def transcode(*args, **kwargs):
        result = original_ffmpeg(*args, **kwargs)
        swap()
        return result

    if replace_at == "read":
        monkeypatch.setattr(pipeline.sf, "read", read)
    else:
        monkeypatch.setattr(pipeline, "_ffmpeg", transcode)
    error = None
    try:
        audio_post.process_audio(
            source, root / "take", root=root, expected_duration_s=1, ffmpeg=ffmpeg_path
        )
    except Exception as caught:  # noqa: BLE001 - Captura el fallo legado y verifica que no borra ajenos.
        error = caught
    assert sentinel.exists(), "cleanup removed a foreign file"
    assert sentinel.read_bytes() == b"foreign master must survive"
    assert isinstance(error, ValueError) and str(error) == "UNSAFE_PATH"
    assert moved.is_dir()
