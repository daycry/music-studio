"""Los hashes que prometen los README del vendor tienen que ser los de los ficheros.

Los cuatro README de `adapters/ace_step/vendor/` publican una tabla
«Ficheros ... y hashes» con bytes y SHA-256 de cada fichero vendorizado. Esa tabla
es la unica garantia de inmutabilidad que da el proyecto sobre codigo de
terceros que se EJECUTA (CLAUDE.md: nada de `trust_remote_code`; el codigo va
fijado por hash y revisable en un diff). Los propios README reconocian que
faltaba «un criterio que exija un diff contra los hashes en cada
reconstruccion»: este fichero es ese criterio, y nacio porque la revision del
2026-09-03 encontro una fila desfasada y un fichero sin fila.

Solo biblioteca estandar: corre en cualquier interprete, con o sin torch.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

VENDOR = Path(__file__).resolve().parent.parent / "adapters" / "ace_step" / "vendor"
READMES = sorted(VENDOR.rglob("README.md"))

# Encabezado de la seccion que lista los ficheros DE ESE DIRECTORIO. Las tablas
# de procedencia upstream (`acestep/...`, pesos, tokenizer) viven bajo otros
# encabezados y no se comprueban aqui: esos ficheros no estan en el repo.
_ENCABEZADO = re.compile(r"^## Ficheros\b.*\bhashes\b", re.IGNORECASE)
_FILA = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`")
_EXTENSIONES_VENDORIZADAS = {".py", ".json"}


def _filas(readme: Path) -> list[tuple[Path, int, str]]:
    """(ruta, bytes declarados, sha256 declarado) de la tabla de ficheros propios."""
    dentro = False
    filas: list[tuple[Path, int, str]] = []
    for linea in readme.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            dentro = bool(_ENCABEZADO.match(linea))
            continue
        if not dentro:
            continue
        coincide = _FILA.match(linea)
        if coincide:
            filas.append((readme.parent / coincide.group(1), int(coincide.group(2)),
                          coincide.group(3)))
    return filas


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


_DECLARADOS = [(readme, fila) for readme in READMES for fila in _filas(readme)]
_VENDORIZADOS = sorted(
    p for p in VENDOR.rglob("*")
    if p.is_file() and p.suffix in _EXTENSIONES_VENDORIZADAS and "__pycache__" not in p.parts
)


def test_hay_cuatro_readmes_y_todos_tienen_tabla_de_hashes():
    assert len(READMES) == 4, READMES
    for readme in READMES:
        assert _filas(readme), f"{readme.relative_to(VENDOR)} no tiene tabla de hashes propia"


@pytest.mark.parametrize(
    "readme,fila",
    _DECLARADOS,
    ids=[str(fila[0].relative_to(VENDOR)) for _, fila in _DECLARADOS],
)
def test_cada_fila_declarada_coincide_con_el_fichero(readme: Path, fila):
    ruta, bytes_declarados, sha_declarado = fila
    assert ruta.is_file(), f"{readme.relative_to(VENDOR)} declara {ruta.name} y no existe"
    assert ruta.stat().st_size == bytes_declarados, (
        f"{ruta.relative_to(VENDOR)}: el README dice {bytes_declarados} bytes y el fichero "
        f"tiene {ruta.stat().st_size}. Si el cambio es intencionado, actualiza la fila."
    )
    assert _sha256(ruta) == sha_declarado, (
        f"{ruta.relative_to(VENDOR)}: SHA-256 real {_sha256(ruta)[:16]}... frente al "
        f"declarado {sha_declarado[:16]}... Si el cambio es intencionado, actualiza la fila."
    )


def test_todo_fichero_vendorizado_esta_declarado_exactamente_una_vez():
    declarados = [fila[0] for _, fila in _DECLARADOS]
    sin_fila = [p.relative_to(VENDOR) for p in _VENDORIZADOS if p not in declarados]
    assert not sin_fila, f"ficheros que se ejecutan y nadie fija por hash: {sin_fila}"
    repetidos = sorted({p.relative_to(VENDOR) for p in declarados if declarados.count(p) > 1})
    assert not repetidos, f"declarados en mas de una tabla: {repetidos}"
