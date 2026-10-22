"""Herramientas reales fijadas para las pruebas de audio en cada plataforma."""

import hashlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def ffmpeg_path():
    if sys.platform == "win32":
        binary = (
            ROOT
            / "tools/ffmpeg/ffmpeg-n9.0.2-10-g51c4a23d74-win64-lgpl-9.0/bin/ffmpeg.exe"
        )
    else:
        configured = os.environ.get("STUDIO_ACTUAL_FFMPEG")
        assert configured, "STUDIO_ACTUAL_FFMPEG must select the pinned Linux binary"
        binary = Path(configured)
        expected = "953632dece404bb1461a4a2285f0191a6105d72c81f9da577eb54326a7fad49a"
        assert hashlib.sha256(binary.read_bytes()).hexdigest() == expected
    assert binary.is_file(), f"managed FFmpeg unavailable: {binary}"
    return binary
