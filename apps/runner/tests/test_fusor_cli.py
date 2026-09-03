"""Autodeteccion del fusor: que espera encontrar en el artefacto antes de abrirlo.

`_artefacto_declara_lm()` y `_dit_root_declarado()` leen SOLO la cabecera del
`safetensors` —los 8 primeros bytes son la longitud del JSON, y ahi ya estan los
nombres de todos los tensores— para elegir una expectativa sin abrir los 7,5 GB.

Por que tienen test propio ahora: `_artefacto_declara_lm` tuvo **dos bugs
consecutivos** durante su desarrollo (la bandera se fijaba despues de construir
las rutas, dejando la del planificador en `None`; y una edicion con expresiones
regulares dejo el fichero sin compilar) y no se probaba en ningun sitio, ni en
pytest ni en el `--selftest` del propio fusor, donde si esta cubierta su hermana
`_dit_root_declarado`.

Las dos comparten un contrato deliberado: **ante cualquier problema de lectura
devuelven el valor negativo en vez de reventar**, porque solo eligen una
expectativa. Quien valida de verdad es `verificar_artefacto`, que compara el
contenido y falla con su mensaje propio. Estos tests fijan ese contrato para que
nadie lo endurezca sin darse cuenta de que romperia la linea de comandos.
"""

from __future__ import annotations

import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

_FUSOR = Path(__file__).resolve().parent.parent / "tools" / "build_artifact.py"


def _cargar_fusor():
    spec = importlib.util.spec_from_file_location("_fusor_cli_bajo_test", _FUSOR)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


fusor = _cargar_fusor()


def _artefacto(destino: Path, claves: dict, *, metadatos: dict | None = None) -> Path:
    """Escribe un safetensors con SOLO cabecera: los nombres son lo que se lee."""
    cabecera = dict(claves)
    if metadatos is not None:
        cabecera["__metadata__"] = metadatos
    cuerpo = json.dumps(cabecera).encode("utf-8")
    destino.write_bytes(struct.pack("<Q", len(cuerpo)) + cuerpo)
    return destino


def _tensor(ini: int = 0, fin: int = 4) -> dict:
    return {"dtype": "U8", "shape": [fin - ini], "data_offsets": [ini, fin]}


class TestDeclaraLm:
    def test_un_artefacto_con_claves_lm_lo_declara(self, tmp_path):
        ruta = _artefacto(tmp_path / "con.safetensors", {
            "dit.decoder.w": _tensor(),
            "lm.model.embed_tokens.weight": _tensor(4, 8),
        })
        assert fusor._artefacto_declara_lm(ruta) is True

    def test_un_artefacto_sin_claves_lm_no_lo_declara(self, tmp_path):
        ruta = _artefacto(tmp_path / "sin.safetensors", {
            "dit.decoder.w": _tensor(),
            "vae.decoder.w": _tensor(4, 8),
        })
        assert fusor._artefacto_declara_lm(ruta) is False

    def test_una_clave_que_solo_contiene_lm_no_cuenta(self, tmp_path):
        # El prefijo es `lm.`, no la subcadena: `text_encoder.lm_head` no es el
        # planificador, y confundirlos elegiria la expectativa equivocada.
        ruta = _artefacto(tmp_path / "casi.safetensors", {
            "text_encoder.lm_head.weight": _tensor(),
            "dit.decoder.alm": _tensor(4, 8),
        })
        assert fusor._artefacto_declara_lm(ruta) is False

    def test_un_fichero_que_no_existe_devuelve_false_sin_reventar(self, tmp_path):
        assert fusor._artefacto_declara_lm(tmp_path / "no_existe.safetensors") is False

    def test_un_fichero_que_no_es_safetensors_devuelve_false(self, tmp_path):
        basura = tmp_path / "basura.safetensors"
        basura.write_bytes(b"\xff" * 512)
        assert fusor._artefacto_declara_lm(basura) is False

    def test_un_fichero_vacio_devuelve_false(self, tmp_path):
        vacio = tmp_path / "vacio.safetensors"
        vacio.write_bytes(b"")
        assert fusor._artefacto_declara_lm(vacio) is False

    def test_una_cabecera_truncada_devuelve_false(self, tmp_path):
        # Declara mas bytes de JSON de los que hay: `json.loads` fallara y el
        # contrato dice que eso es False, no una excepcion.
        truncado = tmp_path / "truncado.safetensors"
        truncado.write_bytes(struct.pack("<Q", 4096) + b'{"lm.w":')
        assert fusor._artefacto_declara_lm(truncado) is False

    def test_una_longitud_de_cabecera_absurda_devuelve_false(self, tmp_path):
        absurdo = tmp_path / "absurdo.safetensors"
        absurdo.write_bytes(struct.pack("<Q", 1 << 40) + b"{}")
        assert fusor._artefacto_declara_lm(absurdo) is False

    def test_no_lee_el_bloque_de_datos(self, tmp_path):
        # La razon de ser de la funcion: elegir la expectativa sin abrir los
        # gigabytes. Se comprueba con una cabecera pequena seguida de un bloque
        # de datos que, si se leyera entero, se notaria.
        ruta = tmp_path / "gordo.safetensors"
        cuerpo = json.dumps({"lm.w": _tensor()}).encode("utf-8")
        ruta.write_bytes(struct.pack("<Q", len(cuerpo)) + cuerpo + b"\x00" * (4 * 1024 * 1024))
        assert fusor._artefacto_declara_lm(ruta) is True


class TestDitRootDeclarado:
    """La hermana, que si estaba cubierta en el selftest: mismo contrato."""

    def test_devuelve_none_cuando_no_hay_nada_que_decir(self, tmp_path):
        ruta = _artefacto(tmp_path / "pelado.safetensors", {"dit.decoder.w": _tensor()})
        assert fusor._dit_root_declarado(ruta) is None

    def test_un_fichero_inexistente_devuelve_none_sin_reventar(self, tmp_path):
        assert fusor._dit_root_declarado(tmp_path / "no_existe.safetensors") is None


def test_las_dos_comparten_el_contrato_de_no_reventar(tmp_path):
    """Guardarrail del contrato: si alguien las endurece, la CLI deja de arrancar.

    Las dos se llaman en `main()` para ELEGIR expectativas antes de validar. Si
    empezaran a lanzar, el fusor fallaria al resolver sus argumentos en vez de en
    la verificacion, que es donde estan los mensajes utiles.
    """
    basura = tmp_path / "basura.safetensors"
    basura.write_bytes(b"no soy un safetensors")
    assert fusor._artefacto_declara_lm(basura) is False
    assert fusor._dit_root_declarado(basura) is None
