"""Temporales de prueba locales y escribibles en el sandbox de Windows."""

from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Path:
    """Aísla cada test sin el mkdir(0700) que el sandbox de Windows rechaza."""
    path = Path(__file__).parent / ".cache" / "pytest-tmp" / uuid4().hex
    path.mkdir(parents=True)
    return path
