"""Configuracion comun de la suite de tests del runner (Fase 0).

Los modulos del cimiento (`contracts.py`, `spikes/_timing.py`, `spikes/_mock.py`,
`adapters/ace_step/adapter.py`) son scripts sueltos sin paquete instalable (el
empaquetado del monorepo es T-10, detras del gate G1), asi que se anaden sus
directorios a `sys.path` a mano, igual que hacen los propios scripts.

Toda la suite corre **sin GPU y sin torch**: solo biblioteca estandar + pytest.
Cualquier dependencia de acelerador debe ser perezosa en el codigo probado; un
test que la necesitara de verdad tendria que llevar su `skipif` explicito.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_RUNNER_ROOT = _TESTS_DIR.parent                       # apps/runner
_SPIKES_DIR = _RUNNER_ROOT / "spikes"
_ADAPTER_DIR = _RUNNER_ROOT / "adapters" / "ace_step"

for _ruta in (str(_RUNNER_ROOT), str(_SPIKES_DIR), str(_ADAPTER_DIR)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
