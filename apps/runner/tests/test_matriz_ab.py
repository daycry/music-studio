"""Tests de la matriz A/B de `spikes/generate_smoke.py` (sin GPU y sin pesos).

Lo que se prueba aqui es el unico trozo del A/B que puede fallar en silencio y
arruinar la conclusion: **que cada pista se genere con la rama y la semilla que
dice su etiqueta**. Si `--matriz` mezclara los ejes, el informe seguiria saliendo
verde y las medidas no significarian nada.

La generacion en si necesita GPU y 7,5 GB de pesos: no se simula aqui.
"""

from __future__ import annotations

import pytest

import generate_smoke as gs


class _Args:
    """Lo minimo que mira `_construir_model_params`."""

    def __init__(self, sin_lm: bool = False) -> None:
        self.idioma_voz = "es"
        self.bpm = 92
        self.tonalidad = "A minor"
        self.compas = "4/4"
        self.sin_lm = sin_lm
        self.lm_cfg = 2.0
        self.lm_temperatura = 0.85


# --------------------------------------------------------------------------- #
# Parseo de la matriz
# --------------------------------------------------------------------------- #
def test_matriz_parsea_los_tres_ejes() -> None:
    casos = gs._parsear_matriz("lm-si-s1:25:20260902:si,lm-no-s2:60:771013:no")
    assert [c.etiqueta for c in casos] == ["lm-si-s1", "lm-no-s2"]
    assert [c.duracion_s for c in casos] == [25, 60]
    assert [c.semilla for c in casos] == [20260902, 771013]
    assert [c.usar_lm for c in casos] == [True, False]


def test_matriz_tolera_espacios_y_celdas_vacias() -> None:
    casos = gs._parsear_matriz("  a:25:1:si , , b:25:1:no ,")
    assert len(casos) == 2
    assert casos[0].usar_lm is True
    assert casos[1].usar_lm is False


@pytest.mark.parametrize(
    "texto",
    ["a:25:1", "a:25:1:si:extra", "a:25:1:quizas", "a:25:1:SI", ""],
)
def test_matriz_rechaza_celdas_invalidas(texto: str) -> None:
    """Nada de adivinar: una celda mal escrita aborta en vez de generar otra cosa."""
    with pytest.raises(SystemExit):
        gs._parsear_matriz(texto)


# --------------------------------------------------------------------------- #
# La perilla del A/B llega intacta a `model_params`
# --------------------------------------------------------------------------- #
def test_override_de_usar_lm_gana_sobre_sin_lm() -> None:
    """La celda manda: es lo que permite las dos ramas en un solo proceso."""
    assert gs._construir_model_params(_Args(sin_lm=True), usar_lm=True)["usar_lm"] is True
    assert gs._construir_model_params(_Args(sin_lm=False), usar_lm=False)["usar_lm"] is False


def test_sin_override_manda_la_bandera_global() -> None:
    """Sin matriz, el comportamiento anterior no cambia."""
    assert gs._construir_model_params(_Args(sin_lm=False))["usar_lm"] is True
    assert gs._construir_model_params(_Args(sin_lm=True))["usar_lm"] is False


def test_la_rama_no_arrastra_el_resto_de_metadatos() -> None:
    """Cambiar `usar_lm` no puede cambiar nada mas, o el A/B no compara una sola cosa."""
    con = gs._construir_model_params(_Args(), usar_lm=True)
    sin = gs._construir_model_params(_Args(), usar_lm=False)
    assert {k: v for k, v in con.items() if k != "usar_lm"} == {
        k: v for k, v in sin.items() if k != "usar_lm"
    }
    assert con["bpm"] == sin["bpm"] == 92
    assert con["keyscale"] == sin["keyscale"] == "A minor"
    assert con["timesignature"] == sin["timesignature"] == "4/4"


# --------------------------------------------------------------------------- #
# El parser acepta la matriz de esta corrida
# --------------------------------------------------------------------------- #
def test_parser_acepta_la_matriz_real() -> None:
    matriz = (
        "lm-si-s1:25:20260902:si,lm-no-s1:25:20260902:no,"
        "lm-si-s2:25:771013:si,lm-no-s2:25:771013:no,"
        "lm-si-60:60:20260902:si,lm-no-60:60:20260902:no"
    )
    args = gs.construir_parser().parse_args(
        ["--matriz", matriz, "--seguir-tras-fallo", "--max-gpu-seconds", "2400"]
    )
    casos = gs._parsear_matriz(args.matriz)
    assert len(casos) == 6
    assert args.seguir_tras_fallo is True

    # Los dos ejes estan cruzados de verdad: cada rama aparece con las dos
    # semillas a 25 s. Sin este cruce no hay vara de medir.
    de_25 = [c for c in casos if c.duracion_s == 25]
    assert {(c.usar_lm, c.semilla) for c in de_25} == {
        (True, 20260902), (False, 20260902), (True, 771013), (False, 771013)
    }

    # Y cada par comparte semilla, que es lo que garantiza el mismo ruido inicial.
    for semilla in (20260902, 771013):
        par = [c for c in de_25 if c.semilla == semilla]
        assert len(par) == 2
        assert {c.usar_lm for c in par} == {True, False}
