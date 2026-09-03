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

Que NO vigila este candado, y hay que saberlo
---------------------------------------------
Un candado que se lee como si cubriera todo es peor que uno con los limites
escritos. Los de este:

* **Solo `adapters/<x>/vendor`, exactamente a ese nivel.** Un `vendor/`
  compartido en otro sitio del arbol, o uno anidado mas profundo
  (`adapters/<familia>/<x>/vendor`), queda **invisible**.
* **Solo `.py` y `.json`.** Un `.pyx`, un `.so`, un `.yaml` o un `.txt` no se
  exigen ni se comprueban. Para `LICENSES/*.txt` eso es lo correcto; para un
  binario compilado que se cargue con `dlopen` seria un agujero.
* **Solo la tabla bajo `## Ficheros ... hashes`.** Las tablas de procedencia
  upstream (`acestep/...`, pesos, tokenizer) viven bajo otros encabezados y se
  ignoran a proposito: esos ficheros no estan en el repositorio.
* **Integridad, no inocuidad.** Que un fichero coincida con su hash no dice nada
  de lo que hace. La revision de seguridad linea a linea del codigo vendorizado
  sigue pendiente y es criterio de `T-03`.

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


def _etiqueta_de_directorio(ruta: Path, vendor: Path) -> str:
    """Como `_etiqueta`, pero legible cuando el directorio ES la raiz del vendor.

    `relative_to` devuelve "." para la raiz, asi que el mensaje salia como
    `hm/.` y no decia nada a quien lo leyera, que es precisamente quien acaba de
    vendorizar un modelo nuevo y no sabe que le falta.
    """
    relativa = ruta.relative_to(vendor).as_posix()
    if relativa == ".":
        return f"{vendor.parent.name}/vendor (la raiz del vendor)"
    return f"{vendor.parent.name}/{relativa}"


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


def problemas_de_descubrimiento(adapters: Path) -> list[str]:
    """Motivos por los que el candado no estaria vigilando nada. Vacio = bien.

    Recibe el directorio en vez de leer los globales para que las propias
    guardias tengan test de regresion sobre un arbol fabricado: son las reglas
    que protegen del fallo peor —un descubrimiento roto que pasa en verde— y
    hasta la revision del 2026-09-03 eran las unicas sin cubrir.
    """
    motivos = []
    if not _directorios_vendor(adapters):
        motivos.append(f"ningun adapters/*/vendor bajo {adapters}: el candado no vigila nada")
    if not _vendorizados(adapters):
        motivos.append("ningun .py/.json vendorizado: el descubrimiento esta roto")
    if not _declaraciones(adapters):
        motivos.append("ninguna fila declarada: el candado pasaria sin comprobar nada")
    return motivos


def problemas_de_cobertura(adapters: Path) -> list[str]:
    """Vendors o directorios con codigo que nadie declara. Vacio = bien.

    Recoge TODOS los problemas antes de devolver. Antes el assert vivia dentro
    del bucle sobre vendors, asi que con dos adapters mal solo se veia uno y se
    arreglaba a ciegas en dos vueltas: molesto justo el dia en que el fichero
    tenga que demostrar que generaliza.
    """
    motivos = []
    con_tabla = {d.readme.parent for d in _declaraciones(adapters)}
    for vendor in _directorios_vendor(adapters):
        if not _declaraciones_de(vendor):
            motivos.append(f"{vendor.parent.name}: vendor sin ninguna tabla de hashes")
            continue
        sin_tabla = sorted(
            {_etiqueta_de_directorio(p.parent, vendor) for p in _vendorizados_de(vendor)
             if p.parent not in con_tabla}
        )
        motivos += [f"{d}: hay codigo vendorizado y ningun README con su tabla" for d in sin_tabla]
    return motivos


def test_el_candado_no_puede_pasar_en_vacio():
    """Sin recuento fijo de README, «no encontre nada» no puede ser un aprobado.

    `parametrize` con una lista vacia se salta el test sin ruido, asi que la
    unica defensa contra un descubrimiento roto es exigir aqui que encuentre
    algo.
    """
    assert problemas_de_descubrimiento(ADAPTERS) == []


def test_ningun_vendor_se_queda_sin_tabla():
    """Un vendor nuevo sin tabla se ignoraria en silencio; aqui hace ruido."""
    assert problemas_de_cobertura(ADAPTERS) == []


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


# --------------------------------------------------------------------------- #
# Las guardias, sobre arboles fabricados (revision 2026-09-03)
# --------------------------------------------------------------------------- #

def _fabricar(raiz: Path, adapter: str, ficheros: dict[str, str], *,
              tabla: dict[str, str] | None = None, subdir: str = "") -> Path:
    """Monta `raiz/<adapter>/vendor/[subdir]/` con ficheros y su README.

    `tabla` mapea nombre -> sha256 declarado; si es None se declaran los hashes
    de verdad. Devuelve el directorio del vendor.
    """
    vendor = raiz / adapter / "vendor"
    destino = vendor / subdir if subdir else vendor
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for nombre, contenido in ficheros.items():
        (destino / nombre).write_text(contenido, encoding="utf-8")
        tam = len((destino / nombre).read_bytes())
        sha = (tabla or {}).get(nombre) or _sha256(destino / nombre)
        filas.append(f"| `{nombre}` | {tam} | `{sha}` |")
    if tabla is not None or ficheros:
        (destino / "README.md").write_text(
            "# vendor falso\n\n## Ficheros y hashes\n\n| Fichero | Bytes | SHA-256 |\n"
            "|---|---|---|\n" + "\n".join(filas) + "\n",
            encoding="utf-8",
        )
    return vendor


class TestGuardiaDeDescubrimiento:
    def test_un_arbol_sin_vendors_no_pasa_en_verde(self, tmp_path):
        (tmp_path / "ace_step").mkdir()
        motivos = problemas_de_descubrimiento(tmp_path)
        assert motivos, "un descubrimiento vacio tiene que hacer ruido, no pasar"
        assert any("no vigila nada" in m for m in motivos)

    def test_un_vendor_con_codigo_y_su_tabla_pasa(self, tmp_path):
        _fabricar(tmp_path, "ace_step", {"a.py": "x = 1\n"})
        assert problemas_de_descubrimiento(tmp_path) == []
        assert problemas_de_cobertura(tmp_path) == []

    def test_un_vendor_con_codigo_y_sin_tabla_ninguna_hace_ruido(self, tmp_path):
        vendor = tmp_path / "minimax" / "vendor"
        vendor.mkdir(parents=True)
        (vendor / "a.py").write_text("x = 1\n", encoding="utf-8")
        motivos = problemas_de_cobertura(tmp_path)
        assert any("sin ninguna tabla" in m for m in motivos), motivos


class TestGuardiaDeCobertura:
    def test_recoge_los_problemas_de_TODOS_los_adapters_no_solo_del_primero(self, tmp_path):
        # Dos vendors mal a la vez: antes se veia uno y se arreglaba a ciegas.
        for adapter in ("aaa_primero", "zzz_segundo"):
            vendor = tmp_path / adapter / "vendor"
            vendor.mkdir(parents=True)
            (vendor / "codigo.py").write_text("x = 1\n", encoding="utf-8")
        motivos = problemas_de_cobertura(tmp_path)
        assert any("aaa_primero" in m for m in motivos)
        assert any("zzz_segundo" in m for m in motivos), (
            f"solo se ve el primero: {motivos}"
        )

    def test_el_mensaje_de_la_raiz_del_vendor_dice_algo_util(self, tmp_path):
        # El caso del `hm/.`: hay tabla en un subdirectorio, pero la raiz tiene
        # codigo sin declarar.
        vendor = _fabricar(tmp_path, "hm", {"dentro.py": "y = 2\n"}, subdir="pipeline")
        (vendor / "suelto.py").write_text("z = 3\n", encoding="utf-8")
        motivos = problemas_de_cobertura(tmp_path)
        assert motivos, "la raiz con codigo sin tabla tiene que salir"
        assert not any(m.startswith("hm/.") or "/." in m for m in motivos), motivos
        assert any("raiz del vendor" in m for m in motivos), motivos


class TestGeneralizacionAVariosAdapters:
    def test_una_fila_desfasada_de_un_adapter_nuevo_se_detecta_y_lo_nombra(self, tmp_path):
        _fabricar(tmp_path, "heartmula", {"c.py": "w = 4\n"}, tabla={"c.py": "0" * 64})
        [decl] = _declaraciones(tmp_path)
        motivo = _motivo_de_desajuste(decl)
        assert motivo is not None
        assert "heartmula/c.py" in motivo, motivo

    def test_un_fichero_nuevo_sin_fila_se_detecta(self, tmp_path):
        vendor = _fabricar(tmp_path, "heartmula", {"c.py": "w = 4\n"})
        (vendor / "oculto.py").write_text("secreto = 1\n", encoding="utf-8")
        assert _sin_declarar(tmp_path) == ["heartmula/oculto.py"]

    def test_dos_adapters_correctos_conviven(self, tmp_path):
        _fabricar(tmp_path, "ace_step", {"a.py": "x = 1\n"})
        _fabricar(tmp_path, "heartmula", {"b.py": "y = 2\n"})
        assert problemas_de_descubrimiento(tmp_path) == []
        assert problemas_de_cobertura(tmp_path) == []
        assert _sin_declarar(tmp_path) == []
        etiquetas = sorted(d.etiqueta for d in _declaraciones(tmp_path))
        assert etiquetas == ["ace_step/a.py", "heartmula/b.py"]

    def test_un_directorio_de_solo_texto_no_exige_tabla(self, tmp_path):
        # Es el caso de `vendor/LICENSES/`: textos de licencia, sin codigo. El
        # candado solo vigila .py y .json, asi que no debe pedirle tabla.
        vendor = _fabricar(tmp_path, "ace_step", {"a.py": "x = 1\n"})
        licencias = vendor / "LICENSES"
        licencias.mkdir()
        (licencias / "MIT.txt").write_text("MIT License\n", encoding="utf-8")
        assert problemas_de_cobertura(tmp_path) == []
