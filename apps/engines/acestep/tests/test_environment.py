"""Comprobaciones del entorno real, sin cargar checkpoints ni inicializar CUDA."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("STUDIO_ENGINE_CONTAINER") != "1",
    reason="El entorno GPU se verifica exclusivamente dentro de engine-acestep.",
)


def test_startup_log():
    entrypoint = Path(__file__).resolve().parents[1] / "entrypoint.sh"
    result = subprocess.run(
        ["sh", str(entrypoint), "python", "-c", "print('command-executed')"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "attention=SDPA torch=2.10.0+cu128" in result.stdout
    assert result.stdout.rstrip().endswith("command-executed")


def test_runtime_dependencies():
    import engine_common
    import engine_contract
    import torch

    assert sys.version_info[:2] == (3, 11)
    assert torch.__version__ == "2.10.0+cu128"
    assert engine_common.create_app
    assert engine_contract.JobRequest
    assert importlib.util.find_spec("acestep")
    assert not importlib.util.find_spec("xformers")
    assert not importlib.util.find_spec("flash_attn")


def test_ffmpeg_shared_lgpl():
    result = subprocess.run(
        ["ffmpeg", "-buildconf"], capture_output=True, text=True, check=True
    )
    config = result.stdout + result.stderr
    for flag in (
        "--enable-libmp3lame",
        "--enable-libsoxr",
        "--enable-libopus",
        "--enable-shared",
    ):
        assert flag in config
    assert "--enable-gpl" not in config
    assert "--enable-nonfree" not in config
    subprocess.run(["python", "-c", "import torchcodec"], check=True)


def test_runtime_configuration():
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
    assert os.environ["ACESTEP_LM_BACKEND"] == "pt"
    assert os.environ["ACESTEP_CHECKPOINTS_DIR"].startswith("/models/")
    assert os.environ["PYTORCH_CUDA_ALLOC_CONF"] == "expandable_segments:True"
    assert os.environ["STUDIO_ENGINE_TOKEN"]
    assert Path("/models/models.lock.json").is_file()
    for directory in ("/models", "/data"):
        readonly_probe = Path(directory, ".t05-readonly-probe")
        try:
            with pytest.raises(OSError):
                readonly_probe.write_text("readonly")
        finally:
            if readonly_probe.exists():
                readonly_probe.unlink()
    probe = Path("/data/tmp/.t05-write-probe")
    try:
        probe.write_text("writable")
        assert probe.read_text() == "writable"
    finally:
        probe.unlink(missing_ok=True)
