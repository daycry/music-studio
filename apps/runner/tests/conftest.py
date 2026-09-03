"""Configuracion comun de la suite de tests del runner (Fase 0).

Los modulos del cimiento (`contracts.py`, `spikes/_timing.py`, `spikes/_mock.py`,
`adapters/ace_step/adapter.py`, el shim) son scripts sueltos sin paquete
instalable (el empaquetado del monorepo es T-10, detras del gate G1), asi que se
anaden sus directorios a `sys.path` a mano, igual que hacen los propios scripts.

Dependencias, dicho sin adornos (revision 2026-09-03)
----------------------------------------------------
**La suite NO corre entera sin torch.** Unos 260 tests son biblioteca estandar
pura (contratos, D-14, D-17, `_timing`, hashes del vendor); los otros ~350
necesitan `torch`, `numpy` y `scipy` (limitador, carga contigua, planificador,
difusion, metricas del A/B, pulso) y se saltan con `importorskip` si faltan.

Un `-q` sin `-rs` esconderia esos saltos, y «614 en verde» con la mitad saltada
seria una mentira. Por eso, si faltan las dependencias numericas, **la sesion
aborta** con un mensaje claro, salvo que se pida explicitamente
`--permitir-saltos` (util en una maquina sin torch para correr solo la parte
pura). Ninguna dependencia de GPU es necesaria: todo corre en CPU.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_RUNNER_ROOT = _TESTS_DIR.parent                       # apps/runner
_SPIKES_DIR = _RUNNER_ROOT / "spikes"
_ADAPTER_DIR = _RUNNER_ROOT / "adapters" / "ace_step"

for _ruta in (str(_RUNNER_ROOT), str(_SPIKES_DIR), str(_ADAPTER_DIR)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

_DEPENDENCIAS_NUMERICAS = ("torch", "numpy", "scipy")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--permitir-saltos",
        action="store_true",
        default=False,
        help=(
            "Permite correr sin torch/numpy/scipy saltando los tests que los "
            "necesitan. Por defecto la sesion aborta, para que un recuento en verde "
            "no esconda medio suite saltada."
        ),
    )


def _disponible(modulo: str) -> bool:
    try:
        return importlib.util.find_spec(modulo) is not None
    except ValueError:  # `sys.modules[modulo] = None`: la forma de simular su ausencia
        return False


def pytest_sessionstart(session: pytest.Session) -> None:
    if session.config.getoption("--permitir-saltos"):
        return
    faltan = [m for m in _DEPENDENCIAS_NUMERICAS if not _disponible(m)]
    if faltan:
        pytest.exit(
            f"Faltan {', '.join(faltan)}: sin ellas se saltarian ~350 de los tests en "
            "silencio. Instala las dependencias numericas (torch en CPU basta) o pasa "
            "--permitir-saltos a proposito.",
            returncode=3,
        )
