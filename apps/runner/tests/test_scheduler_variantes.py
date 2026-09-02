"""Tests de la programacion de pasos de `vendor/pipeline/scheduler.py`.

Existen por una razon concreta: desde el 2026-09-02 el modulo sirve a DOS
variantes de pesos con programaciones incompatibles (8 pasos discretos el turbo,
N continuos el sft), y el modo de fallar de eso no es una excepcion sino audio
peor sin que salte nada. Asi que lo que se congela aqui es:

1. que la tabla del turbo sigue dando **exactamente** los mismos ocho valores;
2. que la formula continua reproduce esa tabla cuando se la evalua en sus mismos
   puntos, que es lo que respalda usar un unico bucle para las dos;
3. que los valores invalidos se rechazan en vez de corregirse solos.

El modulo no importa `torch` a proposito, asi que estos tests corren en la suite
base sin dependencias de acelerador.
"""

from __future__ import annotations

import pytest

from vendor.pipeline import scheduler as sch


# --------------------------------------------------------------------------- #
# El turbo no se ha movido
# --------------------------------------------------------------------------- #

class TestTurboIntacto:
    #: Los ocho valores de `SHIFT_TIMESTEPS[3.0]`, escritos a mano. Si alguien
    #: toca la tabla, este literal es el que protesta.
    OCHO = [
        1.0,
        0.9545454545454546,
        0.9,
        0.8333333333333334,
        0.75,
        0.6428571428571429,
        0.5,
        0.3,
    ]

    def test_la_tabla_sigue_teniendo_ocho_entradas(self):
        for shift, tabla in sch.SHIFT_TIMESTEPS.items():
            assert len(tabla) == 8, f"shift={shift} ya no tiene 8 pasos"
        assert sch.PASOS_POR_DEFECTO == 8
        assert sch.SHIFT_POR_DEFECTO == 3.0

    def test_construir_programacion_no_ha_cambiado(self):
        assert sch.construir_programacion(3.0) == self.OCHO
        assert sch.programacion_efectiva(3.0) == (3.0, self.OCHO)

    def test_la_variante_turbo_devuelve_la_tabla_mas_el_cero(self):
        variante, shift, pasos, tiempos = sch.programacion_de_variante("turbo")
        assert (variante, shift, pasos) == ("turbo", 3.0, 8)
        assert tiempos == [*self.OCHO, 0.0]

    def test_el_cero_final_es_el_salto_a_x0_que_el_turbo_ya_hacia(self):
        """`dt` del ultimo paso == `t` del ultimo paso: es `x0 = x - v*t`."""
        _, _, _, tiempos = sch.programacion_de_variante("turbo")
        assert tiempos[-1] == 0.0
        assert tiempos[-2] - tiempos[-1] == tiempos[-2] == 0.3

    def test_al_turbo_no_se_le_pueden_pedir_otros_pasos(self):
        with pytest.raises(ValueError, match="turbo"):
            sch.programacion_de_variante("turbo", pasos=50)
        # 8 explicito si vale: es el unico que la destilacion vio.
        assert sch.programacion_de_variante("turbo", pasos=8)[2] == 8

    @pytest.mark.parametrize("pedido,esperado", [(2.4, 2.0), (2.6, 3.0), (0.9, 1.0)])
    def test_el_redondeo_de_shift_del_turbo_sigue_vivo(self, pedido, esperado):
        assert sch.programacion_de_variante("turbo", shift=pedido)[1] == esperado


# --------------------------------------------------------------------------- #
# La programacion continua del sft
# --------------------------------------------------------------------------- #

class TestProgramacionContinua:
    def test_la_formula_reproduce_la_tabla_del_turbo(self):
        """La prueba de que las dos programaciones son la MISMA forma cerrada.

        Evaluada en 8 pasos con shift 3,0, la formula continua da los ocho
        valores literales de la tabla destilada, hasta el ultimo bit del doble.
        Es lo que justifica que el bucle sea uno solo.
        """
        continua = sch.construir_programacion_continua(8, 3.0)
        assert continua == [*TestTurboIntacto.OCHO, 0.0]

    def test_defectos_del_sft(self):
        variante, shift, pasos, tiempos = sch.programacion_de_variante("sft")
        assert (variante, shift, pasos) == ("sft", 1.0, 50)
        assert len(tiempos) == 51
        assert tiempos[0] == 1.0 and tiempos[-1] == 0.0
        assert sch.PASOS_SFT_POR_DEFECTO == 50
        assert sch.SHIFT_SFT_POR_DEFECTO == 1.0
        assert sch.GUIA_SFT_POR_DEFECTO == 7.0

    def test_sin_shift_es_lineal(self):
        t = sch.construir_programacion_continua(50, 1.0)
        assert t == pytest.approx([1.0 - i / 50 for i in range(51)])

    @pytest.mark.parametrize("pasos", [1, 8, 30, 50, 100])
    @pytest.mark.parametrize("shift", [0.5, 1.0, 2.0, 3.0])
    def test_siempre_decreciente_de_uno_a_cero(self, pasos, shift):
        t = sch.construir_programacion_continua(pasos, shift)
        assert len(t) == pasos + 1
        assert t[0] == 1.0
        assert t[-1] == 0.0
        assert all(a > b for a, b in zip(t, t[1:])), "la programacion no decrece"

    def test_el_shift_del_sft_no_se_redondea(self):
        """A diferencia del turbo: el modelo base no esta destilado sobre tablas."""
        _, shift, _, t = sch.programacion_de_variante("sft", shift=2.5, pasos=8)
        assert shift == 2.5
        # 2,5 no es ninguno de los VALID_SHIFTS y aun asi se aplica tal cual.
        assert t != sch.construir_programacion_continua(8, 3.0)
        assert t[1] == pytest.approx(2.5 * 0.875 / (1 + 1.5 * 0.875))

    @pytest.mark.parametrize("malos", [0, -1, 101, 8.0, True, "8"])
    def test_pasos_invalidos_se_rechazan(self, malos):
        with pytest.raises(ValueError):
            sch.construir_programacion_continua(malos, 1.0)

    @pytest.mark.parametrize("malos", [0.0, -1.0, float("nan"), float("inf")])
    def test_shift_invalido_se_rechaza_en_vez_de_corregirse(self, malos):
        """Upstream clampa shift<=0 a 1,0 en silencio; aqui se aborta."""
        with pytest.raises(ValueError):
            sch.construir_programacion_continua(50, malos)


# --------------------------------------------------------------------------- #
# Variantes
# --------------------------------------------------------------------------- #

class TestVariantes:
    def test_la_lista_y_el_defecto(self):
        assert sch.VARIANTES == ("turbo", "sft")
        assert sch.VARIANTE_POR_DEFECTO == "turbo"

    @pytest.mark.parametrize("entrada,salida", [("TURBO", "turbo"), (" sft ", "sft")])
    def test_normaliza_mayusculas_y_espacios(self, entrada, salida):
        assert sch.normalizar_variante(entrada) == salida

    @pytest.mark.parametrize("mala", ["base", "", "turbo2", None, 3])
    def test_variante_desconocida_se_rechaza(self, mala):
        with pytest.raises(ValueError):
            sch.normalizar_variante(mala)

    def test_el_turbo_no_lleva_guia_y_el_sft_si(self):
        """La diferencia que da sentido a todo el cambio."""
        assert sch.defectos_de_variante("turbo")["guidance_scale"] == 1.0
        assert sch.defectos_de_variante("sft")["guidance_scale"] == 7.0
