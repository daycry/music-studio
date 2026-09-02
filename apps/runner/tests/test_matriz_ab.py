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

    def __init__(self, sin_lm: bool = False, variante: str = "turbo") -> None:
        self.idioma_voz = "es"
        self.bpm = 92
        self.tonalidad = "A minor"
        self.compas = "4/4"
        self.sin_lm = sin_lm
        self.lm_cfg = 2.0
        self.lm_temperatura = 0.85
        self.variante = variante
        self.pasos = None
        self.guidance = None


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


# --------------------------------------------------------------------------- #
# La perilla de variante
# --------------------------------------------------------------------------- #
def test_la_variante_viaja_siempre_en_model_params() -> None:
    """Aunque sea la de por defecto: el informe guarda `model_params` entero y una
    comparacion turbo-vs-sft en la que haya que adivinar cual era cual no vale."""
    assert gs._construir_model_params(_Args())["variante"] == "turbo"
    assert gs._construir_model_params(_Args(variante="sft"))["variante"] == "sft"


def test_pasos_y_guidance_solo_viajan_si_se_piden() -> None:
    """`None` significa 'el defecto de la variante', que NO es el mismo numero
    para las dos (8/3,0 en turbo, 50/1,0 en sft). Mandar un numero fijo desde
    aqui le colaria al sft la programacion del turbo."""
    params = gs._construir_model_params(_Args(variante="sft"))
    assert "pasos" not in params
    assert "guidance_scale" not in params

    args = _Args(variante="sft")
    args.pasos, args.guidance = 30, 5.0
    params = gs._construir_model_params(args)
    assert params["pasos"] == 30
    assert params["guidance_scale"] == 5.0


def test_guidance_uno_no_se_pierde() -> None:
    """1,0 desactiva la guia y es un valor con significado: `if args.guidance`
    lo habria tirado por falsy. Se comprueba porque ya paso una vez con --bpm 0."""
    args = _Args(variante="sft")
    args.guidance = 1.0
    assert gs._construir_model_params(args)["guidance_scale"] == 1.0
