"""Temporales de prueba locales y escribibles en el sandbox de Windows."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.test_workspace import workspace


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Iterator[Path]:
    """Aísla cada test sin el mkdir(0700) que el sandbox de Windows rechaza."""
    with workspace() as path:
        yield path
