"""Tests de la puerta de compatibilidad de esquema del artefacto.

Por que existe: el fusor escribe `artifact_schema_version` en `aux.manifest_json`
desde el primer artefacto, pero el shim NO lo leia en ningun sitio (cero
apariciones, verificado). Un artefacto de esquema 2 —con los tensores en otra
disposicion— cargado por este shim no habria dado un error claro: habria dado un
fallo raro mucho mas adelante, o audio incorrecto. La puerta convierte ese modo
de fallo en un aborto legible al arrancar.

Lo que se congela aqui:

1. que la version soportada por el shim es la que escribe el fusor (si alguien
   sube una y no la otra, protesta este test y no un artefacto en produccion);
2. las tres ramas de la puerta: igual sigue, mayor aborta con un mensaje que
   dice las dos versiones y que hacer, ausente avisa y sigue;
3. que `build_pipeline` la llama de verdad — una puerta que nadie invoca es peor
   que no tenerla, porque da sensacion de red;
4. que los artefactos reales que hay en disco siguen pasando.

Nada de esto necesita los 7,5 GB de pesos: la funcion solo mira un blob U8 con
JSON dentro, y de los artefactos de disco se leen la cabecera y los bytes del
manifiesto, no el bloque de datos.
"""

from __future__ import annotations

import json
import logging
import re
import struct
from pathlib import Path

import pytest

torch = pytest.importorskip("torch", reason="el shim necesita torch")

import ace_step_shim as shim  # noqa: E402

#: Reserva real de `aux.manifest_json` en el artefacto: el fusor rellena con
#: espacios hasta un ancho fijo. Los tests lo imitan porque el relleno es
#: precisamente lo que `json.loads` tiene que tolerar.
RELLENO = 64

#: Los artefactos fusionados de la maquina de referencia. Si no estan (otra
#: maquina, CI), los tests que los usan se saltan; los demas no dependen de ellos.
DIR_ARTEFACTOS = Path(r"D:\srv\ace-step\weights")


def _blob(texto: str) -> torch.Tensor:
    """El mismo envoltorio que usa el fusor: tensor U8 de una dimension."""
    return torch.tensor(list(texto.encode("utf-8")), dtype=torch.uint8)


def _manifiesto(version: object | None, *, relleno: int = 0) -> dict[str, torch.Tensor]:
    """`state_dict` minimo con el blob del manifiesto y nada mas.

    `version=None` produce un manifiesto SIN la clave: es el artefacto anterior a
    la puerta, que tiene que seguir cargando.
    """
    cuerpo: dict[str, object] = {"manifest_schema_version": "0-draft", "format": "pt"}
    if version is not None:
        cuerpo["artifact_schema_version"] = version
    texto = json.dumps(cuerpo, separators=(",", ":")) + " " * relleno
    return {shim.CLAVE_MANIFIESTO: _blob(texto)}


def _manifiesto_de_artefacto(ruta: Path) -> dict[str, torch.Tensor]:
    """Extrae SOLO `aux.manifest_json` de un `.safetensors` real.

    Lee la cabecera y el tramo del manifiesto: unas decenas de KB de un fichero
    de 7,5 GB. El bloque de pesos no se toca.
    """
    with ruta.open("rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        cabecera = json.loads(f.read(n))
        entrada = cabecera.get(shim.CLAVE_MANIFIESTO)
        if entrada is None:
            return {}
        inicio, fin = entrada["data_offsets"]
        f.seek(8 + n + inicio)
        crudo = f.read(fin - inicio)
    return {shim.CLAVE_MANIFIESTO: torch.frombuffer(bytearray(crudo), dtype=torch.uint8)}


# --------------------------------------------------------------------------- #
# La constante y quien la escribe
# --------------------------------------------------------------------------- #

class TestVersionSoportada:
    def test_coincide_con_la_que_escribe_el_fusor(self):
        """El shim y `build_artifact.py` tienen que hablar del mismo esquema.

        Se lee del fuente del fusor con una expresion regular, no importandolo:
        el fusor es un script de herramientas y no esta en el `sys.path` de la
        suite. Si alguien sube `ARTIFACT_SCHEMA_VERSION` sin adaptar el shim,
        falla aqui, que es barato, y no en la carga de un artefacto de 7,5 GB.
        """
        fusor = Path(shim.__file__).resolve().parents[2] / "tools" / "build_artifact.py"
        assert fusor.is_file(), f"no esta el fusor en {fusor}"
        m = re.search(
            r"^ARTIFACT_SCHEMA_VERSION\s*=\s*(\d+)\s*$",
            fusor.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        assert m is not None, "el fusor ya no declara ARTIFACT_SCHEMA_VERSION"
        assert shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA == int(m.group(1))

    def test_es_un_entero_positivo(self):
        assert isinstance(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA, int)
        assert shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA >= 1


# --------------------------------------------------------------------------- #
# Las tres ramas de la puerta
# --------------------------------------------------------------------------- #

class TestPuertaDeEsquema:
    def test_la_version_igual_pasa(self):
        sd = _manifiesto(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA)
        assert shim._exigir_esquema_compatible(sd) == shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA

    def test_tolera_el_relleno_de_espacios_del_fusor(self):
        """El manifiesto real viene rellenado a ancho fijo; no es JSON exacto."""
        sd = _manifiesto(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA, relleno=RELLENO)
        assert shim._exigir_esquema_compatible(sd) == shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA

    def test_la_version_mayor_aborta(self):
        futura = shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA + 1
        with pytest.raises(RuntimeError) as exc:
            shim._exigir_esquema_compatible(_manifiesto(futura))
        mensaje = str(exc.value)
        assert str(futura) in mensaje, "el mensaje no dice la version encontrada"
        assert str(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA) in mensaje, (
            "el mensaje no dice la version soportada"
        )
        assert "shim" in mensaje.lower()
        assert "regenera" in mensaje.lower(), "el mensaje no dice que se puede hacer"

    def test_la_version_ausente_avisa_y_sigue(self, caplog):
        """Artefacto anterior a la puerta: se avisa, pero se carga."""
        caplog.set_level(logging.WARNING, logger="ace_step.shim")
        assert shim._exigir_esquema_compatible(_manifiesto(None)) is None
        assert any(r.levelno == logging.WARNING for r in caplog.records), "no ha avisado"
        assert "artifact_schema_version" in caplog.text

    def test_sin_blob_de_manifiesto_avisa_y_sigue(self, caplog):
        caplog.set_level(logging.WARNING, logger="ace_step.shim")
        assert shim._exigir_esquema_compatible({}) is None
        assert any(r.levelno == logging.WARNING for r in caplog.records), "no ha avisado"

    def test_un_manifiesto_ilegible_avisa_y_sigue(self, caplog):
        """No se puede saber la version, que es el mismo caso que no declararla."""
        caplog.set_level(logging.WARNING, logger="ace_step.shim")
        sd = {shim.CLAVE_MANIFIESTO: _blob("esto no es json")}
        assert shim._exigir_esquema_compatible(sd) is None
        assert any(r.levelno == logging.WARNING for r in caplog.records), "no ha avisado"

    def test_una_version_declarada_como_texto_se_entiende(self):
        """`__metadata__` la guarda como cadena; que la puerta no se despiste."""
        sd = _manifiesto(str(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA))
        assert shim._exigir_esquema_compatible(sd) == shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA

    def test_una_version_que_no_es_un_entero_aborta(self):
        """Declara algo, y este shim no lo entiende: no se carga a ciegas."""
        with pytest.raises(RuntimeError, match="2.0"):
            shim._exigir_esquema_compatible(_manifiesto("2.0"))

    def test_una_version_anterior_avisa_pero_sigue(self, caplog):
        caplog.set_level(logging.WARNING, logger="ace_step.shim")
        anterior = shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA - 1
        assert shim._exigir_esquema_compatible(_manifiesto(anterior)) == anterior
        assert any(r.levelno == logging.WARNING for r in caplog.records), "no ha avisado"


# --------------------------------------------------------------------------- #
# La puerta esta CONECTADA (lo que fallaba antes no era la logica, era el cable)
# --------------------------------------------------------------------------- #

class TestBuildPipelineLlamaALaPuerta:
    def test_build_pipeline_aborta_con_un_esquema_mas_nuevo(self):
        """Y aborta por el esquema, no por lo que falte despues.

        El `state_dict` esta casi vacio a proposito: si la puerta no estuviera
        conectada, la excepcion hablaria de `dit.decoder...` y no del esquema.
        """
        futura = shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA + 1
        with pytest.raises(RuntimeError) as exc:
            shim.build_pipeline(
                state_dict=_manifiesto(futura), device="cpu", dtype=None, offload=True
            )
        assert "artifact_schema_version" in str(exc.value)

    def test_build_pipeline_no_se_queja_del_esquema_actual(self):
        """Control: con la version buena, la puerta deja pasar y falla lo de siempre."""
        sd = _manifiesto(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA)
        with pytest.raises(RuntimeError) as exc:
            shim.build_pipeline(state_dict=sd, device="cpu", dtype=None, offload=True)
        assert "artifact_schema_version" not in str(exc.value)
        assert "dit.decoder" in str(exc.value)


# --------------------------------------------------------------------------- #
# Los artefactos que ya existen tienen que seguir cargando
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    not DIR_ARTEFACTOS.is_dir(),
    reason=f"no hay artefactos fusionados en {DIR_ARTEFACTOS}",
)
class TestArtefactosEnDisco:
    def test_todos_pasan_la_puerta_declarando_el_esquema(self):
        # Antes se aceptaba `declarada in (None, SOPORTADA)`, y con eso el test
        # no distinguia «el artefacto declara 1» de «no he extraido nada»: habria
        # pasado igual con el manifiesto vacio y la puerta sin cablear. Los tres
        # artefactos fusionados SI declaran la version (comprobado: entero 1 en
        # `aux.manifest_json`), asi que se exige el valor, no la ausencia.
        artefactos = sorted(DIR_ARTEFACTOS.glob("*.safetensors"))
        if not artefactos:
            pytest.skip(f"{DIR_ARTEFACTOS} no tiene artefactos")
        for ruta in artefactos:
            sd = _manifiesto_de_artefacto(ruta)
            assert sd, f"{ruta.name}: no se extrajo {shim.CLAVE_MANIFIESTO}, el test no probaria nada"
            declarada = shim._exigir_esquema_compatible(sd)
            assert declarada == shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA, (
                f"{ruta.name} declara el esquema {declarada!r} y este shim soporta "
                f"{shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA}"
            )


# --------------------------------------------------------------------------- #
# El aborto por esquema tambien tiene que limpiar (revision 2026-09-03)
# --------------------------------------------------------------------------- #

def test_el_aborto_por_esquema_deja_el_dict_del_llamante_vacio():
    """`build_pipeline` promete en su docstring dejar el dict vacio al volver.

    Lo cumplia con un `state_dict.clear()` dentro del `try/except`, pero la puerta
    de esquema se llamaba ANTES del try: era la unica via de fallo que se escapaba
    del bloque de limpieza, y dejaba los tensores del artefacto en el diccionario
    del adapter, que cuenta con lo contrario.
    """
    sd = {
        **_manifiesto(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA + 1),
        "dit.decoder.layers.0.mlp.up_proj.weight": torch.zeros(2, 2),
    }
    with pytest.raises(RuntimeError, match="esquema"):
        shim.build_pipeline(state_dict=sd, device="cpu", dtype="float32", offload=False)
    assert sd == {}, (
        "el aborto por esquema no limpio el dict del llamante: build_pipeline "
        "promete lo contrario en su docstring"
    )


def test_la_puerta_sigue_siendo_lo_primero_que_se_comprueba():
    """Mover la puerta dentro del try no puede colarla DESPUES de tocar tensores.

    Con un esquema incompatible, el mensaje tiene que ser el del esquema y no el
    de «no es el checkpoint que este shim sabe cargar»: si sale el segundo,
    alguien miro los tensores antes de comprobar la version.
    """
    sd = _manifiesto(shim.ARTIFACT_SCHEMA_VERSION_SOPORTADA + 1)  # sin ningun tensor
    with pytest.raises(RuntimeError) as info:
        shim.build_pipeline(state_dict=sd, device="cpu", dtype="float32", offload=False)
    assert "esquema" in str(info.value)
    assert "no trae" not in str(info.value)
