import os
from pathlib import Path
from uuid import uuid4

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("STUDIO_TEST_ROOT", str(PROJECT_ROOT / ".cache" / "pytest-tmp"))
os.environ.setdefault(
    "STUDIO_QUEUE_TEST_ROOT",
    str(PROJECT_ROOT / ".cache" / "dev-cycle" / "m1" / "t04-queue-tests"),
)
os.environ.setdefault(
    "STUDIO_PROVENANCE_TEST_ROOT",
    str(PROJECT_ROOT / ".cache" / "dev-cycle" / "m1" / "t05-provenance-capture-unit1"),
)


class ProjectTempPathFactory:
    """Sustituto mínimo del factory de pytest confinado al repositorio."""

    def __init__(self):
        self.base = PROJECT_ROOT / ".cache" / "pytest-tmp" / "server"
        self.base.mkdir(parents=True, exist_ok=True)

    def mktemp(self, basename, numbered=True):
        suffix = uuid4().hex if numbered else "0"
        path = self.base / f"{basename}{suffix}"
        path.mkdir(parents=True, exist_ok=False)
        return path


@pytest.fixture
def tmp_path_factory():
    return ProjectTempPathFactory()


@pytest.fixture
def tmp_path():
    path = Path.cwd() / ".cache/dev-cycle/m1/t01-implementation/fixtures" / uuid4().hex
    path.mkdir(parents=True)
    return path


_LINUX_FIXTURES = {"actual", "song_actual"}


def pytest_collection_modifyitems(config, items):
    """Marca y salta con motivo los tests que no aplican en este entorno (M1/T-05)."""
    import sys

    for item in items:
        if _LINUX_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.linux_real)
        if item.get_closest_marker("linux_real") and sys.platform != "linux":
            item.add_marker(
                pytest.mark.skip(reason="requiere Linux real (se ejecuta en Docker)")
            )
        if item.get_closest_marker("custody_harness") and not os.environ.get(
            "CUSTODY_SOURCE_SHA256"
        ):
            item.add_marker(
                pytest.mark.skip(
                    reason="requiere el arnés de custodia Windows (CUSTODY_SOURCE_SHA256)"
                )
            )
