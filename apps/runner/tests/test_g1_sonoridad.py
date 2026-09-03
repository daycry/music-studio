# -*- coding: utf-8 -*-
"""Tests de `spikes/g1_sonoridad.py` — medicion EBU R128 y normalizacion de G1.

Por que estos tests y no otros
==============================
Un medidor de sonoridad no se puede validar «a ojo»: o se contrasta contra
verdad conocida o no se ha validado. Aqui la verdad conocida es de tres clases,
y ninguna sale del propio modulo:

1. **La tabla de coeficientes de la Recomendacion ITU-R BS.1770-4** a 48 kHz.
   Esta copiada literal en este fichero, no importada del modulo: si alguien
   toca los coeficientes en `g1_sonoridad.py`, el test lo ve.
2. **La calibracion del propio estandar.** El termino `-0.691` de la formula de
   `L_K` existe para cancelar exactamente la ganancia de la ponderacion K a
   997 Hz. Consecuencia comprobable: un tono estereo a 1 kHz con pico -20 dBFS
   mide -20 LUFS con una desviacion de milesimas (ver el test, que documenta la
   cifra real en vez de forzarla).
3. **Algebra elemental**: aplicar una ganancia constante de +6 dB sube la medida
   6 LU; el pico entre muestras de un seno a fs/4 desfasado 45 grados es
   3,01 dB mayor que el pico de las muestras.

Lo que NO se comprueba aqui: calidad musical. Este modulo iguala el nivel para
que la escucha de `gates/g1-protocolo.md` §5.5 compare mezcla y no sonoridad.
"""

from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

import g1_sonoridad  # noqa: E402


# --------------------------------------------------------------------------- #
# Verdad conocida 1: la tabla de BS.1770-4 a 48 kHz, copiada literal
# --------------------------------------------------------------------------- #

#: Tabla 1 de BS.1770-4 — primera etapa, filtro de estanteria de agudos.
TABLA_SHELF_B = (1.53512485958697, -2.69169618940638, 1.19839281085285)
TABLA_SHELF_A = (1.0, -1.69065929318241, 0.73248077421585)

#: Tabla 2 de BS.1770-4 — segunda etapa, paso alto RLB.
TABLA_PASO_ALTO_B = (1.0, -2.0, 1.0)
TABLA_PASO_ALTO_A = (1.0, -1.99004745483398, 0.99007225036621)


def _ganancia_db(etapas, frecuencia_hz: float, tasa: int) -> float:
    """Ganancia de la cascada de biquads a una frecuencia, en dB."""
    z = np.exp(-1j * 2.0 * math.pi * frecuencia_hz / tasa)
    total = 1.0 + 0j
    for b, a in etapas:
        total *= np.polyval(np.asarray(b)[::-1], z) / np.polyval(np.asarray(a)[::-1], z)
    return float(20.0 * np.log10(abs(total)))


def _seno_estereo(pico: float, frecuencia_hz: float, segundos: float, tasa: int,
                  fase: float = 0.0) -> "np.ndarray":
    n = np.arange(int(round(segundos * tasa)))
    onda = pico * np.sin(2.0 * math.pi * frecuencia_hz * n / tasa + fase)
    return np.column_stack([onda, onda])


# --------------------------------------------------------------------------- #
# Ponderacion K
# --------------------------------------------------------------------------- #

def test_coeficientes_a_48k_son_los_de_la_tabla_del_estandar():
    """A 48 kHz no se deriva nada: se usan los numeros publicados por la ITU."""
    etapas = g1_sonoridad.coeficientes_ponderacion_k(48000)
    assert len(etapas) == 2, "BS.1770 define la ponderacion K en DOS etapas"

    (b_shelf, a_shelf), (b_alto, a_alto) = etapas
    np.testing.assert_allclose(b_shelf, TABLA_SHELF_B, rtol=0, atol=1e-14)
    np.testing.assert_allclose(a_shelf, TABLA_SHELF_A, rtol=0, atol=1e-14)
    np.testing.assert_allclose(b_alto, TABLA_PASO_ALTO_B, rtol=0, atol=1e-14)
    np.testing.assert_allclose(a_alto, TABLA_PASO_ALTO_A, rtol=0, atol=1e-14)


def test_la_ganancia_k_a_997_hz_es_la_que_cancela_el_offset_de_la_formula():
    """El `-0,691` de `L_K` existe para anular la ganancia K a 997 Hz.

    Si esta igualdad se rompe, la escala entera esta desplazada y todas las
    medidas mienten por igual — el error mas dificil de ver a ojo.
    """
    etapas = g1_sonoridad.coeficientes_ponderacion_k(48000)
    assert _ganancia_db(etapas, 997.0, 48000) == pytest.approx(
        -g1_sonoridad.OFFSET_LK_DB, abs=1e-4
    )


@pytest.mark.parametrize("tasa", [44100, 96000, 32000])
def test_a_otras_tasas_la_calibracion_a_997_hz_se_conserva(tasa):
    """La ITU solo tabula 48 kHz; a otras tasas se redisctretiza el prototipo.

    El criterio de que la redisctretizacion es buena es que la calibracion del
    estandar siga en pie: la ganancia a 997 Hz no puede alejarse de 0,691 dB.
    """
    etapas = g1_sonoridad.coeficientes_ponderacion_k(tasa)
    assert _ganancia_db(etapas, 997.0, tasa) == pytest.approx(0.691, abs=0.01)


# --------------------------------------------------------------------------- #
# Sonoridad integrada
# --------------------------------------------------------------------------- #

def test_tono_de_1_khz_a_menos_20_dbfs_mide_menos_20_lufs():
    """Verdad conocida 2, y la desviacion real se documenta en vez de forzarse.

    La ponderacion K vale +0,6910 dB a 997 Hz (offset del estandar) y
    +0,6977 dB a 1000 Hz. La diferencia, +0,0067 dB, es TODA la desviacion
    esperable de esta medida: 1 kHz no es exactamente la frecuencia de
    calibracion. Por eso el margen es 0,05 LU y no 0,5.
    """
    senal = _seno_estereo(pico=0.1, frecuencia_hz=1000.0, segundos=5.0, tasa=48000)
    medido = g1_sonoridad.sonoridad_integrada(senal, 48000)
    assert medido == pytest.approx(-20.0, abs=0.05)
    # La desviacion es positiva y del orden de milesimas: si algun dia sale
    # negativa o pasa de 0,02, la cadena de filtros ha cambiado.
    assert 0.0 < medido + 20.0 < 0.02


def test_el_silencio_da_menos_infinito_y_no_revienta():
    """Ni excepcion, ni `nan`, ni un numero inventado: `-inf` es la respuesta."""
    silencio = np.zeros((48000 * 2, 2))
    assert g1_sonoridad.sonoridad_integrada(silencio, 48000) == -math.inf


def test_una_senal_mas_corta_que_un_bloque_da_menos_infinito():
    """Menos de 400 ms no tiene ni un bloque que medir; se dice, no se estima."""
    corta = _seno_estereo(pico=0.5, frecuencia_hz=1000.0, segundos=0.2, tasa=48000)
    assert g1_sonoridad.sonoridad_integrada(corta, 48000) == -math.inf


def test_aplicar_6_db_sube_la_medida_6_lu():
    """Verdad conocida 3: la medida es equivariante a la ganancia constante.

    Solo lo es lejos de la puerta absoluta de -70 LUFS, que es un umbral fijo y
    no relativo; por eso la senal de prueba esta 50 LU por encima.
    """
    senal = _seno_estereo(pico=0.1, frecuencia_hz=1000.0, segundos=5.0, tasa=48000)
    base = g1_sonoridad.sonoridad_integrada(senal, 48000)
    subida = g1_sonoridad.sonoridad_integrada(senal * (10.0 ** (6.0 / 20.0)), 48000)
    assert subida - base == pytest.approx(6.0, abs=0.01)


def test_la_puerta_relativa_descarta_los_pasajes_flojos():
    """Un pasaje 20 LU por debajo no debe arrastrar la medida hacia abajo.

    Es exactamente lo que hace la puerta relativa de -10 LU: la sonoridad de una
    pista con silencios largos no es su media aritmetica.
    """
    tasa = 48000
    fuerte = _seno_estereo(pico=0.1, frecuencia_hz=1000.0, segundos=5.0, tasa=tasa)
    flojo = _seno_estereo(pico=0.001, frecuencia_hz=1000.0, segundos=5.0, tasa=tasa)
    mezcla = np.concatenate([fuerte, flojo], axis=0)

    solo_fuerte = g1_sonoridad.sonoridad_integrada(fuerte, tasa)
    con_flojo = g1_sonoridad.sonoridad_integrada(mezcla, tasa)
    # Sin puerta relativa la media caeria unos 3 LU; con ella, decimas.
    assert con_flojo == pytest.approx(solo_fuerte, abs=0.3)


# --------------------------------------------------------------------------- #
# Pico real
# --------------------------------------------------------------------------- #

def test_el_pico_real_supera_al_pico_de_muestra():
    """La razon de existir del sobremuestreo, en un caso con solucion exacta.

    Un seno a fs/4 desfasado 45 grados cae siempre en +-sin(45 grados), o sea
    -3,01 dBFS de pico de muestra, mientras que su pico verdadero es 0 dBFS.
    Un medidor que mire solo las muestras se equivoca en 3 dB enteros y deja
    pasar a disco un recorte que si existe.
    """
    tasa = 48000
    senal = _seno_estereo(pico=1.0, frecuencia_hz=tasa / 4.0, segundos=1.0,
                          tasa=tasa, fase=math.pi / 4.0)

    pico_muestra = g1_sonoridad.pico_de_muestra_dbfs(senal)
    pico_real = g1_sonoridad.pico_real_dbtp(senal, tasa)

    assert pico_muestra == pytest.approx(-3.0103, abs=0.001)
    assert pico_real > pico_muestra + 2.5
    # El pico verdadero es 0 dBFS; un sobremuestreo x4 lo estima con decimas de
    # error y por el lado seguro (sobreestimar deja la pista mas baja).
    assert pico_real == pytest.approx(0.0, abs=0.3)


def test_el_pico_real_del_silencio_es_menos_infinito():
    assert g1_sonoridad.pico_real_dbtp(np.zeros((4800, 2)), 48000) == -math.inf


# --------------------------------------------------------------------------- #
# Ganancia hacia el objetivo de la sesion
# --------------------------------------------------------------------------- #

def test_una_senal_ya_en_el_objetivo_no_necesita_ganancia():
    tasa = 48000
    bruta = _seno_estereo(pico=0.1, frecuencia_hz=1000.0, segundos=5.0, tasa=tasa)
    en_objetivo = bruta * (10.0 ** ((-16.0 - g1_sonoridad.sonoridad_integrada(bruta, tasa)) / 20.0))

    ajuste = g1_sonoridad.ganancia_para_objetivo(en_objetivo, tasa)
    assert ajuste.ganancia_db == pytest.approx(0.0, abs=0.01)
    assert ajuste.objetivo_alcanzado is True
    assert ajuste.limitado_por_pico is False


def test_normalizar_deja_la_pista_en_el_objetivo_de_la_sesion():
    tasa = 48000
    senal = _seno_estereo(pico=0.02, frecuencia_hz=440.0, segundos=6.0, tasa=tasa)
    salida, ajuste = g1_sonoridad.normalizar(senal, tasa)

    assert ajuste.objetivo_alcanzado is True
    assert ajuste.lufs_final == pytest.approx(g1_sonoridad.OBJETIVO_LUFS_SESION, abs=0.05)
    assert ajuste.dbtp_final <= g1_sonoridad.TECHO_DBTP_SESION + 1e-6
    assert g1_sonoridad.sonoridad_integrada(salida, tasa) == pytest.approx(-16.0, abs=0.05)


def test_normalizar_solo_aplica_ganancia_no_comprime():
    """El invariante de §5.5, y el motivo de no usar `ffmpeg loudnorm`.

    `loudnorm` puede revertir a modo dinamico y comprimir; comprimir alteraria
    la dimension 2 de la rubrica («calidad de mezcla y ausencia de artefactos»),
    que es una de las cinco que se puntuan. Aqui se comprueba lo unico que hace
    esa promesa verificable: la salida es la entrada multiplicada por UN escalar.
    """
    tasa = 48000
    senal = _seno_estereo(pico=0.3, frecuencia_hz=220.0, segundos=4.0, tasa=tasa)
    # Un transitorio: si hubiera compresion, este pico se aplastaria respecto al resto.
    senal[tasa: tasa + 64] = 0.95

    salida, ajuste = g1_sonoridad.normalizar(senal, tasa)
    esperado = senal * (10.0 ** (ajuste.ganancia_db / 20.0))
    np.testing.assert_array_equal(salida, esperado)


def test_si_el_techo_de_pico_impide_llegar_al_objetivo_se_aplica_la_menor_y_se_dice():
    """El caso que el protocolo prefiere resolver por lo bajo, no recortando.

    Un tren de impulsos a fondo de escala tiene sonoridad muy baja y pico
    maximo: su factor de cresta pasa de los 15 dB que separan el objetivo
    (-16 LUFS) del techo (-1 dBTP). No hay ganancia que cumpla las dos cosas.
    Se aplica la menor, la pista queda por debajo del objetivo, y quien lea el
    acta tiene que poder saberlo.
    """
    tasa = 48000
    impulsos = np.zeros((tasa * 3, 2))
    impulsos[::1000, :] = 1.0

    ajuste = g1_sonoridad.ganancia_para_objetivo(impulsos, tasa)

    # Precondicion de la construccion: el conflicto existe de verdad.
    ganancia_para_lufs = g1_sonoridad.OBJETIVO_LUFS_SESION - ajuste.lufs_medido
    ganancia_para_pico = g1_sonoridad.TECHO_DBTP_SESION - ajuste.dbtp_medido
    assert ganancia_para_lufs > ganancia_para_pico

    assert ajuste.ganancia_db == pytest.approx(ganancia_para_pico, abs=1e-9)
    assert ajuste.limitado_por_pico is True
    assert ajuste.objetivo_alcanzado is False
    assert ajuste.motivo, "un objetivo no alcanzado sin motivo escrito no es auditable"

    salida, aplicado = g1_sonoridad.normalizar(impulsos, tasa)
    assert aplicado.lufs_final < g1_sonoridad.OBJETIVO_LUFS_SESION
    assert aplicado.dbtp_final <= g1_sonoridad.TECHO_DBTP_SESION + 0.01
    assert float(np.max(np.abs(salida))) < 1.0, "nada puede salir recortado"


def test_el_silencio_no_se_amplifica_ni_finge_haber_llegado():
    silencio = np.zeros((48000 * 2, 2))
    ajuste = g1_sonoridad.ganancia_para_objetivo(silencio, 48000)
    assert ajuste.ganancia_db == 0.0
    assert ajuste.objetivo_alcanzado is False
    assert "silencio" in ajuste.motivo.lower() or "puerta" in ajuste.motivo.lower()


# --------------------------------------------------------------------------- #
# Entradas invalidas
# --------------------------------------------------------------------------- #

def test_una_senal_con_valores_no_finitos_se_rechaza():
    """Un `nan` medido en silencio da `-inf` y parece normal: hay que abortar."""
    senal = _seno_estereo(pico=0.1, frecuencia_hz=1000.0, segundos=1.0, tasa=48000)
    senal[100, 0] = np.nan
    with pytest.raises(ValueError):
        g1_sonoridad.sonoridad_integrada(senal, 48000)
