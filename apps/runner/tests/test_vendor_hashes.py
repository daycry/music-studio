"""Los hashes que prometen los README del vendor tienen que ser los de los ficheros.

Cada `adapters/<adapter>/vendor/` publica, en el README de cada uno de sus
directorios, una tabla «Ficheros ... y hashes» con bytes y SHA-256 de cada
fichero vendorizado. Esa tabla es la unica garantia de inmutabilidad que da el
proyecto sobre codigo de terceros que se EJECUTA (CLAUDE.md: nada de
`trust_remote_code`; el codigo va fijado por hash y revisable en un diff). Los
propios README reconocian que faltaba «un criterio que exija un diff contra los
hashes en cada reconstruccion»: este fichero es ese criterio, y nacio porque la
revision del 2026-09-03 encontro una fila desfasada y un fichero sin fila.

El candado **descubre los adapters**; no los lleva escritos. El dia que se
vendorice un segundo modelo (HeartMuLa, MiniMax...) queda vigilado sin tocar
este fichero, que era el riesgo real: un vendor nuevo ignorado en silencio.
Como un descubrimiento vacio tambien pasaria en verde sin comprobar nada,
`test_el_candado_no_puede_pasar_en_vacio` exige que haya al menos un vendor, un
fichero vendorizado y una fila declarada, y `test_ningun_vendor_se_queda_sin_tabla`
que ningun vendor ni directorio con codigo se quede mudo.

Solo biblioteca estandar: corre en cualquier interprete, con o sin torch.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import NamedTuple

import pytest

ADAPTERS = Path(__file__).resolve().parent.parent / "adapters"

# Encabezado de la seccion que lista los ficheros DE ESE DIRECTORIO. Las tablas
# de procedencia upstream (`acestep/...`, pesos, tokenizer) viven bajo otros
# encabezados y no se comprueban aqui: esos ficheros no estan en el repo.
_ENCABEZADO = re.compile(r"^## Ficheros\b.*\bhashes\b", re.IGNORECASE)
_FILA = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`")
_EXTENSIONES_VENDORIZADAS = {".py", ".json"}


def _etiqueta(ruta: Path, vendor: Path) -> str:
    """`<adapter>/<ruta dentro del vendor>`, con barras normales en cualquier SO."""
    return f"{vendor.parent.name}/{ruta.relative_to(vendor).as_posix()}"


class Declaracion(NamedTuple):
    """Una fila de una tabla de hashes: quien promete que, y sobre que fichero."""

    vendor: Path
    readme: Path
    ruta: Path
    bytes_declarados: int
    sha_declarado: str

    @property
    def etiqueta(self) -> str:
        return _etiqueta(self.ruta, self.vendor)

    @property
    def etiqueta_readme(self) -> str:
        return _etiqueta(self.readme, self.vendor)


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _directorios_vendor(adapters: Path) -> list[Path]:
    """Todos los `adapters/*/vendor/` que existan, ordenados. Aqui esta la generalizacion."""
    return sorted(d for d in adapters.glob("*/vendor") if d.is_dir())


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


def _declaraciones_de(vendor: Path) -> list[Declaracion]:
    return [
        Declaracion(vendor, readme, ruta, tam, sha)
        for readme in sorted(vendor.rglob("README.md"))
        for ruta, tam, sha in _filas(readme)
    ]


def _vendorizados_de(vendor: Path) -> list[Path]:
    return sorted(
        p for p in vendor.rglob("*")
        if p.is_file() and p.suffix in _EXTENSIONES_VENDORIZADAS and "__pycache__" not in p.parts
    )


def _declaraciones(adapters: Path) -> list[Declaracion]:
    return [d for vendor in _directorios_vendor(adapters) for d in _declaraciones_de(vendor)]


def _vendorizados(adapters: Path) -> list[Path]:
    return [p for vendor in _directorios_vendor(adapters) for p in _vendorizados_de(vendor)]


def _motivo_de_desajuste(declaracion: Declaracion) -> str | None:
    """El motivo por el que la fila no cuadra con el fichero, o None si cuadra."""
    ruta = declaracion.ruta
    if not ruta.is_file():
        return f"{declaracion.etiqueta_readme} declara {ruta.name} y no existe"
    tam = ruta.stat().st_size
    if tam != declaracion.bytes_declarados:
        return (
            f"{declaracion.etiqueta}: el README dice {declaracion.bytes_declarados} bytes y el "
            f"fichero tiene {tam}. Si el cambio es intencionado, actualiza la fila."
        )
    real = _sha256(ruta)
    if real != declaracion.sha_declarado:
        return (
            f"{declaracion.etiqueta}: SHA-256 real {real[:16]}... frente al declarado "
            f"{declaracion.sha_declarado[:16]}... Si el cambio es intencionado, actualiza la fila."
        )
    return None


def _sin_declarar(adapters: Path) -> list[str]:
    """Ficheros que se ejecutan y no tienen fila en el README de su directorio."""
    huerfanos: list[str] = []
    for vendor in _directorios_vendor(adapters):
        declaradas = {d.ruta for d in _declaraciones_de(vendor)}
        huerfanos += [
            _etiqueta(p, vendor) for p in _vendorizados_de(vendor) if p not in declaradas
        ]
    return sorted(huerfanos)


def _declarados_varias_veces(adapters: Path) -> list[str]:
    """Ficheros con mas de una fila: dos promesas que pueden contradecirse."""
    repetidos: list[str] = []
    for vendor in _directorios_vendor(adapters):
        rutas = [d.ruta for d in _declaraciones_de(vendor)]
        repetidos += [_etiqueta(p, vendor) for p in set(rutas) if rutas.count(p) > 1]
    return sorted(repetidos)


_VENDORS = _directorios_vendor(ADAPTERS)
_DECLARADAS = _declaraciones(ADAPTERS)


def test_el_candado_no_puede_pasar_en_vacio():
    """Sin recuento fijo de README, «no encontre nada» no puede ser un aprobado.

    `parametrize` con una lista vacia se salta el test sin ruido, asi que la
    unica defensa contra un descubrimiento roto es exigir aqui que encuentre
    algo.
    """
    assert _VENDORS, f"ningun adapters/*/vendor bajo {ADAPTERS}: el candado no vigila nada"
    assert _vendorizados(ADAPTERS), "ningun .py/.json vendorizado: el descubrimiento esta roto"
    assert _DECLARADAS, "ninguna fila declarada: el candado pasaria sin comprobar nada"


def test_ningun_vendor_se_queda_sin_tabla():
    """Un vendor nuevo sin tabla se ignoraria en silencio; aqui hace ruido."""
    mudos = sorted(v.parent.name for v in _VENDORS if not _declaraciones_de(v))
    assert not mudos, f"vendors sin ninguna tabla de hashes: {mudos}"
    con_tabla = {d.readme.parent for d in _DECLARADAS}
    for vendor in _VENDORS:
        sin_tabla = sorted(
            {_etiqueta(p.parent, vendor) for p in _vendorizados_de(vendor)
             if p.parent not in con_tabla}
        )
        assert not sin_tabla, f"directorios con codigo vendorizado y sin tabla propia: {sin_tabla}"


@pytest.mark.parametrize(
    "declaracion",
    _DECLARADAS,
    ids=[d.etiqueta for d in _DECLARADAS],
)
def test_cada_fila_declarada_coincide_con_el_fichero(declaracion: Declaracion):
    motivo = _motivo_de_desajuste(declaracion)
    assert motivo is None, motivo


def test_todo_fichero_vendorizado_esta_declarado_exactamente_una_vez():
    sin_fila = _sin_declarar(ADAPTERS)
    assert not sin_fila, f"ficheros que se ejecutan y nadie fija por hash: {sin_fila}"
    repetidos = _declarados_varias_veces(ADAPTERS)
    assert not repetidos, f"declarados en mas de una tabla: {repetidos}"


# ---------------------------------------------------------------------------
# Que la regla valga para N adapters se prueba sobre un arbol fabricado, no
# sobre el de verdad: hoy solo hay ace_step, y esperar a HeartMuLa para saber
# si el candado generaliza seria enterarse tarde.
# ---------------------------------------------------------------------------

_PLANTILLA_README = """# Vendor fabricado para el test

## Ficheros y hashes

| Fichero | Bytes | SHA-256 |
|---|---|---|
| `{nombre}` | {tam} | `{sha}` |
"""


def _fabricar_adapter(
    tmp_path: Path, *, sha: str | None = None, huerfano: bool = False
) -> tuple[Path, Path]:
    """Crea `<tmp>/adapters/falso/vendor/` con un .py y su README. Devuelve (adapters, modulo)."""
    vendor = tmp_path / "adapters" / "falso" / "vendor"
    vendor.mkdir(parents=True)
    modulo = vendor / "modulo_falso.py"
    modulo.write_bytes(b"CODIGO = 'de mentira'\n")
    if huerfano:
        (vendor / "sin_fila.py").write_bytes(b"CODIGO = 'sin fila'\n")
    (vendor / "README.md").write_text(
        _PLANTILLA_README.format(
            nombre=modulo.name, tam=modulo.stat().st_size, sha=sha or _sha256(modulo)
        ),
        encoding="utf-8",
    )
    return tmp_path / "adapters", modulo


def test_el_descubrimiento_encuentra_y_valida_un_adapter_nuevo(tmp_path: Path):
    adapters, modulo = _fabricar_adapter(tmp_path)
    assert _directorios_vendor(adapters) == [modulo.parent]
    declaradas = _declaraciones(adapters)
    assert [d.ruta for d in declaradas] == [modulo]
    assert declaradas[0].etiqueta == "falso/modulo_falso.py"
    assert _motivo_de_desajuste(declaradas[0]) is None
    assert _vendorizados(adapters) == [modulo]
    assert _sin_declarar(adapters) == []


def test_una_fila_con_hash_incorrecto_hace_fallar_al_adapter_nuevo(tmp_path: Path):
    adapters, _ = _fabricar_adapter(tmp_path, sha="0" * 64)
    (declarada,) = _declaraciones(adapters)
    motivo = _motivo_de_desajuste(declarada)
    assert motivo is not None and "SHA-256" in motivo


def test_un_fichero_sin_fila_del_adapter_nuevo_no_pasa_en_silencio(tmp_path: Path):
    adapters, _ = _fabricar_adapter(tmp_path, huerfano=True)
    assert _sin_declarar(adapters) == ["falso/sin_fila.py"]
