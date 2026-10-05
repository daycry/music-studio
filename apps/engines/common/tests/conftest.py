"""Temporales locales sin ACL privadas incompatibles con el sandbox Windows."""

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    path = (
        Path(__file__).resolve().parents[4] / ".cache/dev-cycle/t03" / uuid.uuid4().hex
    )
    path.mkdir(parents=True)
    yield path
    shutil.rmtree(path)
