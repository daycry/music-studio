"""Temporales locales sin ACL privadas incompatibles con el sandbox Windows."""

import os

import pytest

from scripts.test_workspace import ROOT, workspace

# Las pruebas nativas escriben recibos junto al namespace de temporales. El
# fallback interno de ``workspace_base`` basta para crear workspaces, pero las
# pruebas que conservan recibos necesitan la ruta canónica visible en el
# entorno desde el primer módulo recolectado.
os.environ.setdefault("STUDIO_TEST_ROOT", str(ROOT / ".cache" / "pytest-tmp"))


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest):
    with workspace() as path:
        yield path
