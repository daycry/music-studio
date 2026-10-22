"""Regresiones de la verificación compartida de FFmpeg en T-11."""

import os
import subprocess
from types import SimpleNamespace

import pytest
from test_evaluation_guards import fake_bundle

from scripts.eval import metrics


def test_verified_ffmpeg_reuses_stable_process_cache(tmp_path, monkeypatch):
    """Una instalación estable se verifica una vez por proceso y raíz."""
    binary, _ = fake_bundle(tmp_path)
    original_hash = metrics.file_hash
    hashes = []
    versions = []

    def tracked_hash(path):
        hashes.append(path)
        return original_hash(path)

    def fake_run(*args, **kwargs):
        versions.append((args, kwargs))
        return SimpleNamespace(stdout="ffmpeg 51c4a23d74 SYNTHETIC_SIMULATION\n")

    monkeypatch.setattr(metrics, "file_hash", tracked_hash)
    monkeypatch.setattr(subprocess, "run", fake_run)

    first = metrics.verified_ffmpeg(tmp_path)
    second = metrics.verified_ffmpeg(tmp_path)

    assert first == second
    assert first[0] == binary
    assert len(hashes) == 4
    assert len(versions) == 1


def test_verified_ffmpeg_rehashes_binary_after_same_stat_replacement(
    tmp_path, monkeypatch
):
    """Un reemplazo in-place no puede conservar la verificación del caché."""
    binary, _ = fake_bundle(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="ffmpeg 51c4a23d74 SYNTHETIC_SIMULATION\n"
        ),
    )

    metrics.verified_ffmpeg(tmp_path)
    original_stat = binary.stat()
    binary.write_bytes(b"X" * original_stat.st_size)
    os.utime(binary, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    with pytest.raises(ValueError, match="FFMPEG_HASH_MISMATCH"):
        metrics.verified_ffmpeg(tmp_path)
