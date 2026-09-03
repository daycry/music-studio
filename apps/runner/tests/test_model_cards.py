"""Tests del inventario de fichas de modelo (`model_cards.py`), sin torch ni GPU.

Lo que se prueba aqui es la regla que sostiene todo el diseno: **la ficha es
evidencia, nunca autoridad**. Una ficha describe unos pesos que ya estan en
disco; no decide que codigo se importa ni puede apagar una salvaguarda. Si eso
se rompe, el mecanismo pasa de inventario a superficie de ejecucion, que es
exactamente lo que `CLAUDE.md` prohibe al vetar `trust_remote_code`.

El problema concreto que resuelve, hoy y sin servidor: en el disco de la maquina
hay tres `.safetensors` que son el MISMO modelo, y dos de ellos (turbo y sft) son
indistinguibles mirando el artefacto —mismas claves, mismas formas—, pero suenan
distinto. Elegir mal no da error.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import model_cards as mc


# --------------------------------------------------------------------------- #
# Utilidades: un directorio de pesos de juguete
# --------------------------------------------------------------------------- #

def _ficha(**cambios):
    base = {
        "schema": mc.SCHEMA_SOPORTADO,
        "id": "ace-step",
        "version": "1.5-turbo-lm",
        "adapter": "ace_step",
        "pesos": "modelo.safetensors",
        "estado": "activo",
        "hardware": {"min_vram_mb": 8192},
        "licencias": [{"componente": "dit", "spdx": "MIT"}],
        "env": {"ACE_STEP_VARIANTE": "turbo"},
    }
    base.update(cambios)
    return base


def _pesos(dirp: Path, nombre: str = "modelo.safetensors", *, provenance: bool = True,
           ficha: dict | None = None) -> Path:
    ruta = dirp / nombre
    ruta.write_bytes(b"\x08\x00\x00\x00\x00\x00\x00\x00{}      ")
    if provenance:
        ruta.with_suffix(".provenance.json").write_text(
            json.dumps({"artifact": {"sha256": "0" * 64}}), encoding="utf-8"
        )
    if ficha is not None:
        ruta.with_suffix(".model.json").write_text(
            json.dumps(ficha), encoding="utf-8"
        )
    return ruta


@pytest.fixture
def pesos(tmp_path: Path) -> Path:
    return tmp_path


# --------------------------------------------------------------------------- #
# La ficha no manda sobre el codigo
# --------------------------------------------------------------------------- #

class TestLaFichaNoEsAutoridad:
    def test_un_adapter_desconocido_se_rechaza_no_se_importa(self, pesos):
        # Este es EL test del diseno: la ficha nombra el adapter, no lo resuelve.
        _pesos(pesos, ficha=_ficha(adapter="os:system"))
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert "adapter" in f.motivo.lower()

    def test_los_adapters_conocidos_son_una_lista_cerrada_del_repo(self):
        assert isinstance(mc.ADAPTERS_CONOCIDOS, frozenset)
        assert "ace_step" in mc.ADAPTERS_CONOCIDOS

    def test_el_modulo_no_importa_nada_por_nombre(self):
        # Sin importlib, __import__, eval, exec ni pickle no hay forma de que un
        # dato del disco acabe siendo codigo. Se comprueba sobre el ARBOL
        # SINTACTICO y no por texto: un grep tambien casa con la prosa del
        # docstring que explica por que no se usa, y prohibir explicarlo seria
        # castigar la documentacion en vez del riesgo.
        import ast

        arbol = ast.parse(Path(mc.__file__).read_text(encoding="utf-8"))
        prohibidos = {"importlib", "pickle", "subprocess"}
        llamadas_prohibidas = {"__import__", "eval", "exec", "compile", "getattr"}
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    assert alias.name.split(".")[0] not in prohibidos, alias.name
            elif isinstance(nodo, ast.ImportFrom):
                assert (nodo.module or "").split(".")[0] not in prohibidos, nodo.module
            elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                assert nodo.func.id not in llamadas_prohibidas, nodo.func.id

    @pytest.mark.parametrize("variable", ["ACE_STEP_SKIP_INTEGRITY", "ACE_STEP_MOCK"])
    def test_una_ficha_no_puede_apagar_una_salvaguarda(self, pesos, variable):
        # Una ficha configura; jamas desactiva la verificacion de integridad ni
        # convierte una generacion real en simulada.
        _pesos(pesos, ficha=_ficha(env={variable: "1"}))
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert variable in f.motivo

    def test_una_variable_de_entorno_fuera_de_la_lista_blanca_se_rechaza(self, pesos):
        _pesos(pesos, ficha=_ficha(env={"LD_PRELOAD": "/tmp/x.so"}))
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert "LD_PRELOAD" in f.motivo


# --------------------------------------------------------------------------- #
# Estados del inventario
# --------------------------------------------------------------------------- #

class TestEstados:
    def test_una_ficha_valida_con_pesos_y_procedencia_esta_disponible(self, pesos):
        _pesos(pesos, ficha=_ficha())
        [f] = mc.inventariar(pesos, vram_mb=8192)
        assert f.estado == mc.DISPONIBLE, f.motivo
        assert f.ref == "ace-step@1.5-turbo-lm"

    def test_unos_pesos_sin_ficha_se_listan_como_tales_y_no_se_ocultan(self, pesos):
        # Es el caso de hoy: tres artefactos y ninguna ficha. Ocultarlos seria
        # peor que listarlos, porque estan ahi y alguien los usara.
        _pesos(pesos, ficha=None)
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.SIN_FICHA
        assert f.ruta_pesos.name == "modelo.safetensors"

    def test_un_modelo_deprecado_no_es_seleccionable_pero_sigue_visible(self, pesos):
        # El sft descartado en T-06 tiene que verse Y no poder elegirse por
        # descuido. Marcarlo "disponible" seria volver al problema.
        _pesos(pesos, ficha=_ficha(estado="deprecado"))
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.NO_SELECCIONABLE
        assert "deprecado" in f.motivo.lower()

    def test_sin_provenance_hermano_se_rechaza(self, pesos):
        # Una sola regla de hash: la procedencia la escribe el fusor. Sin ella no
        # hay nada que contrastar y la ficha seria una promesa sin respaldo.
        _pesos(pesos, provenance=False, ficha=_ficha())
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert "provenance" in f.motivo.lower()

    def test_una_ficha_que_apunta_a_unos_pesos_que_no_existen_se_rechaza(self, pesos):
        (pesos / "huerfana.model.json").write_text(
            json.dumps(_ficha(pesos="no_existe.safetensors")), encoding="utf-8"
        )
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert "no existe" in f.motivo.lower()

    def test_una_ficha_ilegible_no_se_confunde_con_ausente(self, pesos):
        ruta = _pesos(pesos)
        ruta.with_suffix(".model.json").write_text("{roto", encoding="utf-8")
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA

    def test_un_esquema_de_ficha_futuro_se_rechaza_en_vez_de_adivinarse(self, pesos):
        _pesos(pesos, ficha=_ficha(schema=mc.SCHEMA_SOPORTADO + 1))
        [f] = mc.inventariar(pesos)
        assert f.estado == mc.RECHAZADA
        assert "schema" in f.motivo.lower()


# --------------------------------------------------------------------------- #
# VRAM: responde "cabe", no "sirve"
# --------------------------------------------------------------------------- #

class TestVram:
    def test_lo_que_no_cabe_no_es_seleccionable_y_dice_cuanto_falta(self, pesos):
        _pesos(pesos, ficha=_ficha(hardware={"min_vram_mb": 16384}))
        [f] = mc.inventariar(pesos, vram_mb=8192)
        assert f.estado == mc.NO_SELECCIONABLE
        assert "16384" in f.motivo and "8192" in f.motivo

    def test_sin_vram_conocida_no_se_inventa_un_veredicto(self, pesos):
        # El modulo no importa torch a proposito: la VRAM se inyecta. Si nadie la
        # da, no puede decidir, y decir "disponible" seria mentir.
        _pesos(pesos, ficha=_ficha(hardware={"min_vram_mb": 16384}))
        [f] = mc.inventariar(pesos, vram_mb=None)
        assert f.estado == mc.DISPONIBLE
        assert "sin comprobar" in f.motivo.lower()

    def test_el_modulo_no_importa_torch(self):
        fuente = Path(mc.__file__).read_text(encoding="utf-8")
        assert "import torch" not in fuente


# --------------------------------------------------------------------------- #
# El caso real que motiva todo esto
# --------------------------------------------------------------------------- #

def test_tres_artefactos_del_mismo_modelo_quedan_distinguidos(pesos):
    """Reproduce el disco de hoy: mismo modelo, tres ficheros, uno descartado."""
    for nombre, version, estado in (
        ("ace_step_1_5.safetensors", "1.5-turbo", "activo"),
        ("ace_step_1_5_lm.safetensors", "1.5-turbo-lm", "activo"),
        ("ace_step_1_5_sft_lm.safetensors", "1.5-sft-lm", "deprecado"),
    ):
        _pesos(pesos, nombre, ficha=_ficha(version=version, estado=estado, pesos=nombre))

    fichas = {f.ref: f for f in mc.inventariar(pesos, vram_mb=8192)}
    assert len(fichas) == 3
    assert fichas["ace-step@1.5-turbo-lm"].estado == mc.DISPONIBLE
    assert fichas["ace-step@1.5-sft-lm"].estado == mc.NO_SELECCIONABLE
    seleccionables = [f.ref for f in fichas.values() if f.estado == mc.DISPONIBLE]
    assert "ace-step@1.5-sft-lm" not in seleccionables
