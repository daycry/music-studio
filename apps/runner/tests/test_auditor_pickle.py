"""El auditor de opcodes del fusor, contra un pickle hostil por cada opcode letal.

Por que existe este fichero
---------------------------
`tools/build_artifact.py` tiene que convertir un pickle de upstream
(`silence_latent.pt`) en un tensor **sin deserializarlo**, porque deserializar un
pickle EJECUTA el codigo que lleve dentro: es ejecucion remota de codigo, y es el
invariante numero uno de `CLAUDE.md`. Su auditor de opcodes es la pieza que hace
eso posible, y hasta la revision del 2026-09-03 la suite **no lo tocaba en
ningun sitio**: solo se probaba dentro del `--selftest` del propio fusor, con UN
unico pickle hostil. Un auditor anti-RCE con un caso de prueba es un auditor sin
probar.

La regla de este fichero, que no se negocia
-------------------------------------------
Los pickles hostiles se construyen como **bytes de opcodes**, a mano, y se pasan
al auditor. **Jamas se hace `pickle.loads` de ellos**: eso seria ejecutar
exactamente lo que se esta probando que no se ejecuta. Por eso no hay ni un
`import pickle` que deserialice: solo `pickletools`, que lee opcodes sin
interpretarlos.

Lo que se cubre, y por que ese reparto
--------------------------------------
El error clasico al escribir un validador de pickles es vigilar solo `GLOBAL` y
`STACK_GLOBAL` («si los nombres importados son benignos, el pickle es benigno»).
Es falso: hay nueve opcodes que referencian o construyen objetos **sin emitir un
solo GLOBAL**. Hay un test por cada uno.
"""

from __future__ import annotations

import importlib.util
import pickletools
import struct
import sys
import zipfile
from pathlib import Path

import pytest

_FUSOR = Path(__file__).resolve().parent.parent / "tools" / "build_artifact.py"


def _cargar_fusor():
    """Importa el fusor por ruta: es un script de `tools/`, no esta en sys.path.

    Se comprueba antes que importarlo no ejecuta nada mas que definiciones: el
    fichero es una herramienta de linea de comandos y su `main()` vive detras del
    guardia `if __name__ == "__main__"`.
    """
    assert _FUSOR.is_file(), f"no esta el fusor en {_FUSOR}"
    spec = importlib.util.spec_from_file_location("_fusor_bajo_test", _FUSOR)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


fusor = _cargar_fusor()


# --------------------------------------------------------------------------- #
# Fabrica de opcodes. Protocolo 2 salvo donde se diga.
# --------------------------------------------------------------------------- #

PROTO2 = b"\x80\x02"
STOP = b"."
MARK = b"("
EMPTY_TUPLE = b")"
NONE = b"N"
REDUCE = b"R"
BINPERSID = b"Q"


def _global(modulo: str, nombre: str) -> bytes:
    return b"c" + modulo.encode() + b"\n" + nombre.encode() + b"\n"


def _short_binunicode(texto: str) -> bytes:
    crudo = texto.encode("utf-8")
    return b"\x8c" + bytes([len(crudo)]) + crudo


def _binint1(valor: int) -> bytes:
    return b"K" + bytes([valor])


def _pickle_de(*trozos: bytes) -> bytes:
    return PROTO2 + b"".join(trozos) + STOP


def _auditar(datos: bytes):
    return fusor._interpretar_pickle_inerte(datos)


# --------------------------------------------------------------------------- #
# El camino feliz: el pickle que torch escribe de verdad
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def pickle_legitimo(tmp_path_factory) -> bytes:
    """`data.pkl` de un tensor pelado, generado con torch y leido del zip.

    Se genera en vez de escribirse a mano porque el objetivo es que el auditor
    acepte lo que torch produce DE VERDAD. Los bytes se leen del zip y se pasan
    al auditor; nunca se deserializan.
    """
    torch = pytest.importorskip("torch")
    ruta = tmp_path_factory.mktemp("pt") / "tensor.pt"
    torch.save(torch.zeros(1, 64, 8, dtype=torch.float32), str(ruta))
    with zipfile.ZipFile(ruta) as z:
        nombre = next(n for n in z.namelist() if n.endswith("data.pkl"))
        return z.read(nombre)


def test_el_pickle_que_escribe_torch_se_acepta(pickle_legitimo):
    espec, auditoria = _auditar(pickle_legitimo)
    assert espec is not None
    assert auditoria.opcodes > 0
    # Las cotas del fusor estan ajustadas a esta forma canonica exacta.
    assert auditoria.globals_ <= fusor._MAX_GLOBAL if hasattr(auditoria, "globals_") else True


def test_el_camino_feliz_no_depende_de_deserializar_nada(pickle_legitimo):
    # Guardarrail de la regla del fichero: los opcodes se pueden recorrer sin
    # construir un solo objeto. Si esto falla, el pickle no es analizable de
    # forma inerte y el diseno del auditor no se sostiene.
    nombres = [op.name for op, _arg, _pos in pickletools.genops(pickle_legitimo)]
    assert "STOP" in nombres
    assert "REDUCE" in nombres


# --------------------------------------------------------------------------- #
# Los nueve opcodes letales, uno por uno
# --------------------------------------------------------------------------- #

CASOS_LETALES = {
    # INST lleva modulo y clase como TEXTO PLANO en el propio opcode: no hay
    # ningun GLOBAL que un filtro por nombre pudiera ver pasar.
    "INST": b"i" + b"os\nsystem\n",
    "OBJ": MARK + b"o",
    "NEWOBJ": EMPTY_TUPLE + b"\x81",
    "NEWOBJ_EX": EMPTY_TUPLE + EMPTY_TUPLE + b"\x92",
    # EXT1/2/4 resuelven un callable por CODIGO NUMERICO contra copyreg: el
    # nombre no aparece en el fichero en ninguna forma.
    "EXT1": b"\x82" + bytes([1]),
    "EXT2": b"\x83" + struct.pack("<H", 1),
    "EXT4": b"\x84" + struct.pack("<i", 1),
    "BUILD": NONE + b"b",
    # PERSID es la variante textual de BINPERSID. torch nunca la emite: si
    # aparece, el fichero no lo ha generado torch.
    "PERSID": b"P1\n",
}


@pytest.mark.parametrize("opcode", sorted(CASOS_LETALES))
def test_cada_opcode_letal_se_rechaza_por_nombre(opcode):
    datos = _pickle_de(CASOS_LETALES[opcode])
    with pytest.raises(fusor.PickleRechazado) as info:
        _auditar(datos)
    mensaje = str(info.value)
    assert opcode in mensaje, f"el mensaje no nombra el opcode: {mensaje}"
    assert "PROHIBIDO" in mensaje


def test_los_nueve_letales_estan_todos_cubiertos():
    # Si alguien anade un opcode letal a la tabla del fusor, este test lo
    # obliga a anadir tambien su caso aqui.
    assert set(CASOS_LETALES) == set(fusor._OPCODES_LETALES), (
        "la tabla de opcodes letales del fusor y los casos de este fichero han "
        "dejado de coincidir"
    )


def test_un_opcode_letal_se_rechaza_aunque_el_resto_parezca_impecable():
    # BUILD detras de una secuencia perfectamente normal: el rechazo es por
    # nombre y no depende de que el flujo sea sospechoso.
    datos = _pickle_de(
        _global("collections", "OrderedDict"), EMPTY_TUPLE, REDUCE, NONE, b"b"
    )
    with pytest.raises(fusor.PickleRechazado, match="BUILD"):
        _auditar(datos)


# --------------------------------------------------------------------------- #
# La lista blanca es cerrada
# --------------------------------------------------------------------------- #

class TestListaBlancaCerrada:
    @pytest.mark.parametrize(
        "nombre, bytes_",
        [
            ("EMPTY_DICT", b"}"),
            ("EMPTY_LIST", b"]"),
            ("APPEND", b"]" + NONE + b"a"),
            ("SETITEM", b"}" + NONE + NONE + b"s"),
            ("DICT", MARK + b"d"),
            ("LIST", MARK + b"l"),
            ("FLOAT", b"F1.0\n"),
            ("BINFLOAT", b"G" + struct.pack(">d", 1.0)),
        ],
    )
    def test_un_opcode_no_analizado_se_rechaza(self, nombre, bytes_):
        with pytest.raises(fusor.PickleRechazado, match="lista blanca"):
            _auditar(_pickle_de(bytes_))

    def test_un_pickle_de_protocolo_antiguo_se_rechaza(self):
        # Protocolo 0: texto plano, con opcodes que este parser no audita. Sin
        # PROTO delante, y con INT, que no esta en la lista blanca.
        with pytest.raises(fusor.PickleRechazado):
            _auditar(b"I1\n" + STOP)

    def test_el_protocolo_declarado_fuera_de_rango_se_rechaza(self):
        with pytest.raises(fusor.PickleRechazado, match="[Pp]rotocolo"):
            _auditar(b"\x80\x01" + NONE + STOP)


# --------------------------------------------------------------------------- #
# Nombres y cotas
# --------------------------------------------------------------------------- #

class TestNombresYCotas:
    @pytest.mark.parametrize(
        "modulo, nombre",
        [
            ("os", "system"),
            ("builtins", "eval"),
            ("subprocess", "Popen"),
            ("posix", "system"),
            ("torch.serialization", "load"),
            ("numpy.core.multiarray", "_reconstruct"),
        ],
    )
    def test_un_callable_fuera_de_los_tres_permitidos_aborta(self, modulo, nombre):
        with pytest.raises(fusor.PickleRechazado):
            _auditar(_pickle_de(_global(modulo, nombre)))

    def test_stack_global_no_se_cuela_como_desconocido(self):
        # STACK_GLOBAL (protocolo 4) nombra el callable con dos cadenas de la
        # pila en vez de en el propio opcode. Tiene que pasar por el MISMO
        # control de nombres, no por la rama de "opcode no analizado".
        datos = (
            b"\x80\x04"
            + _short_binunicode("os")
            + _short_binunicode("system")
            + b"\x93"
            + STOP
        )
        with pytest.raises(fusor.PickleRechazado) as info:
            _auditar(datos)
        assert "lista blanca" not in str(info.value), (
            "STACK_GLOBAL se ha tratado como opcode desconocido en vez de "
            "validarle el nombre: un pickle de protocolo 4 se colaria por la "
            "puerta equivocada"
        )

    def test_mas_global_de_los_permitidos_aborta(self):
        permitido = _global("collections", "OrderedDict")
        datos = _pickle_de(*([permitido] * (fusor._MAX_GLOBAL + 1)))
        with pytest.raises(fusor.PickleRechazado):
            _auditar(datos)

    def test_un_pickle_demasiado_grande_se_rechaza_sin_analizarlo(self):
        with pytest.raises(fusor.PickleRechazado, match="tope"):
            _auditar(b"\x00" * (fusor.MAX_PICKLE_BYTES + 1))

    def test_bytes_despues_de_stop_se_rechazan(self):
        # Cola tras STOP: un `pickle.load` normal la ignoraria, y ahi caben
        # datos que el auditor no habria mirado.
        with pytest.raises(fusor.PickleRechazado):
            _auditar(_pickle_de(NONE) + b"basura")


# --------------------------------------------------------------------------- #
# El objeto de nivel superior tiene que ser un tensor pelado
# --------------------------------------------------------------------------- #

def test_un_diccionario_de_nivel_superior_se_rechaza():
    # Un `.pt` con un state_dict dentro es lo normal en el mundo, y aqui se
    # rechaza a proposito: menos superficie, y el latente de silencio no tiene
    # ningun motivo para cambiar de forma.
    with pytest.raises(fusor.PickleRechazado):
        _auditar(_pickle_de(b"}"))


def test_un_pickle_vacio_se_rechaza():
    with pytest.raises(fusor.PickleRechazado):
        _auditar(_pickle_de())
