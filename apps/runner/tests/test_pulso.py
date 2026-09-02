"""Tests del bloque de RITMO de `spikes/medir_ab.py` contra senales construidas.

Este bloque es el que responde a la queja del propietario («las voces no siguen
el ritmo de la base»), asi que es el que menos margen tiene para dar un numero
plausible y falso. Cada metrica se comprueba contra una senal cuyo tempo, cuya
periodicidad y cuyo desfase se conocen porque los ponemos nosotros, nunca contra
otra implementacion.

Lo que NO se prueba aqui, y conviene tenerlo claro al leer el informe: que estas
metricas midan CALIDAD musical. Miden periodicidad de los ataques. Un pulso
fuerte no es una buena cancion, y el encaje real lo juzga el oido (G1).
"""

from __future__ import annotations

import numpy as np
import pytest

medir_ab = pytest.importorskip("medir_ab", reason="medir_ab necesita numpy y scipy")

SR = 48000
BPM_OBJETIVO = 94.0
DURACION_S = 12.0


def _tren(
    bpm: float,
    *,
    frecuencia: float,
    duracion_s: float = DURACION_S,
    retraso_s: float = 0.0,
    ancho_s: float = 0.03,
    amplitud: float = 0.5,
    tasa: int = SR,
    jitter_s: float = 0.0,
    semilla: int = 20260902,
) -> np.ndarray:
    """Tren de golpes tonales: `frecuencia` marca en que banda cae cada golpe."""
    n = int(duracion_s * tasa)
    x = np.zeros(n)
    periodo = 60.0 / bpm
    rng = np.random.default_rng(semilla)
    t_golpe = retraso_s
    while t_golpe < duracion_s:
        desvio = rng.normal(0.0, jitter_s) if jitter_s > 0 else 0.0
        inicio = int((t_golpe + desvio) * tasa)
        largo = int(ancho_s * tasa)
        if 0 <= inicio < n - largo:
            tt = np.arange(largo) / tasa
            # Ataque instantaneo y caida exponencial: es lo que ve el flujo espectral.
            golpe = np.sin(2 * np.pi * frecuencia * tt) * np.exp(-tt / (ancho_s / 3.0))
            x[inicio : inicio + largo] += amplitud * golpe
        t_golpe += periodo
    return x


def _mag(x: np.ndarray) -> np.ndarray:
    return medir_ab.stft_magnitud(np.ascontiguousarray(x, dtype=np.float64))


# --------------------------------------------------------------------------- #
# Tempo
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bpm", [80.0, 94.0, 120.0])
def test_el_tempo_estimado_es_el_del_tren_de_golpes(bpm: float) -> None:
    d = medir_ab.pulso(_mag(_tren(bpm, frecuencia=80.0)), SR)
    assert d["bpm_acf_plegado"] == pytest.approx(bpm, abs=1.0)


def test_el_tempo_sobrevive_a_una_mezcla_de_grave_y_voz() -> None:
    """Con dos bandas a la vez el pulso sigue siendo el mismo."""
    x = _tren(BPM_OBJETIVO, frecuencia=60.0) + _tren(BPM_OBJETIVO, frecuencia=900.0)
    d = medir_ab.pulso(_mag(x), SR)
    assert d["bpm_acf_plegado"] == pytest.approx(BPM_OBJETIVO, abs=1.5)
    assert d["bpm_grave_plegado"] == pytest.approx(BPM_OBJETIVO, abs=1.5)
    assert d["bpm_voz_plegado"] == pytest.approx(BPM_OBJETIVO, abs=1.5)


def test_el_plegado_lleva_las_octavas_al_mismo_sitio() -> None:
    assert medir_ab._plegar_bpm(47.0) == pytest.approx(94.0)
    assert medir_ab._plegar_bpm(188.0) == pytest.approx(94.0)
    assert medir_ab._plegar_bpm(94.0) == pytest.approx(94.0)


# --------------------------------------------------------------------------- #
# Fuerza del pulso: la metrica que mas pesa en la comparacion
# --------------------------------------------------------------------------- #
def test_un_pulso_regular_da_mas_fuerza_que_uno_desencajado() -> None:
    """Mismo tempo, misma energia: solo cambia si los golpes caen en la rejilla."""
    regular = medir_ab.pulso(_mag(_tren(BPM_OBJETIVO, frecuencia=80.0)), SR)
    desencajado = medir_ab.pulso(
        _mag(_tren(BPM_OBJETIVO, frecuencia=80.0, jitter_s=0.12)), SR
    )
    assert regular["pulso_fuerza"] > desencajado["pulso_fuerza"], (
        f"regular {regular['pulso_fuerza']:.3f} vs desencajado "
        f"{desencajado['pulso_fuerza']:.3f}"
    )


def test_el_ruido_sin_pulso_da_fuerza_baja() -> None:
    rng = np.random.default_rng(20260902)
    ruido = medir_ab.pulso(_mag(rng.normal(0, 0.1, int(DURACION_S * SR))), SR)
    tren = medir_ab.pulso(_mag(_tren(BPM_OBJETIVO, frecuencia=80.0)), SR)
    assert ruido["pulso_fuerza"] < 0.25
    assert tren["pulso_fuerza"] > 3 * max(ruido["pulso_fuerza"], 1e-3)


def test_el_silencio_no_revienta_y_devuelve_nan() -> None:
    d = medir_ab.pulso(_mag(np.zeros(int(4 * SR))), SR)
    assert np.isnan(d["bpm_acf"])
    assert np.isnan(d["pulso_fuerza"])


# --------------------------------------------------------------------------- #
# Encaje voz-base: signo, magnitud y coherencia
# --------------------------------------------------------------------------- #
def test_sin_retraso_el_desfase_es_cero_y_la_coherencia_alta() -> None:
    x = _tren(BPM_OBJETIVO, frecuencia=60.0) + _tren(BPM_OBJETIVO, frecuencia=900.0)
    d = medir_ab.pulso(_mag(x), SR)
    assert abs(d["desfase_voz_beat_ms"]) <= 15.0
    assert d["coherencia_voz_beat"] > 0.5


@pytest.mark.parametrize("retraso_ms", [60.0, 120.0])
def test_una_voz_atrasada_da_desfase_positivo(retraso_ms: float) -> None:
    """El signo importa: positivo tiene que significar «la voz llega tarde»."""
    x = _tren(BPM_OBJETIVO, frecuencia=60.0) + _tren(
        BPM_OBJETIVO, frecuencia=900.0, retraso_s=retraso_ms / 1000.0
    )
    d = medir_ab.pulso(_mag(x), SR)
    assert d["desfase_voz_beat_ms"] == pytest.approx(retraso_ms, abs=20.0)


def test_una_voz_adelantada_da_desfase_negativo() -> None:
    # El grave se retrasa 80 ms: relativo a el, la voz va adelantada.
    x = _tren(BPM_OBJETIVO, frecuencia=60.0, retraso_s=0.08) + _tren(
        BPM_OBJETIVO, frecuencia=900.0
    )
    d = medir_ab.pulso(_mag(x), SR)
    assert d["desfase_voz_beat_ms"] < -20.0


def test_una_voz_que_no_sigue_la_rejilla_baja_la_coherencia() -> None:
    """Lo que de verdad describe la queja: no es ir tarde, es no ir a compas."""
    base = _tren(BPM_OBJETIVO, frecuencia=60.0)
    encajada = medir_ab.pulso(_mag(base + _tren(BPM_OBJETIVO, frecuencia=900.0)), SR)
    suelta = medir_ab.pulso(
        _mag(base + _tren(BPM_OBJETIVO, frecuencia=900.0, jitter_s=0.15, semilla=7)), SR
    )
    assert suelta["coherencia_voz_beat"] < encajada["coherencia_voz_beat"]


def test_las_bandas_separan_grave_de_voz() -> None:
    """Si las bandas no separasen, comparar voz con grave no diria nada."""
    solo_grave = _mag(_tren(BPM_OBJETIVO, frecuencia=60.0))
    e_grave = medir_ab.envolvente_ataques(solo_grave, SR, medir_ab.BANDA_GRAVE_HZ)
    e_voz = medir_ab.envolvente_ataques(solo_grave, SR, medir_ab.BANDA_VOZ_HZ)
    assert e_grave.max() > 5.0 * max(e_voz.max(), 1e-6)


# --------------------------------------------------------------------------- #
# Integracion con el resto de descriptores
# --------------------------------------------------------------------------- #
def test_los_descriptores_incluyen_el_bloque_de_ritmo() -> None:
    x = _tren(BPM_OBJETIVO, frecuencia=80.0)
    d = medir_ab.descriptores(x, np.stack([x, x], axis=1), SR)
    for clave in (
        "bpm_acf",
        "pulso_fuerza",
        "bpm_grave",
        "bpm_voz",
        "desfase_voz_beat_ms",
        "coherencia_voz_beat",
    ):
        assert clave in d, clave
    assert d["bpm_acf_plegado"] == pytest.approx(BPM_OBJETIVO, abs=1.5)


def test_la_referencia_por_banda_seria_un_espejismo() -> None:
    """Regresion del fallo que costo dos tests de este fichero.

    Normalizar cada banda contra SU propio maximo sube el suelo de la banda vacia
    hasta la escala completa y convierte la fuga del transitorio del bombo en un
    ataque de libro. Con eso, la coherencia voz-base salia alta por construccion y
    la metrica habria dicho «encajan» pasara lo que pasara.
    """
    m = _mag(_tren(BPM_OBJETIVO, frecuencia=60.0))
    frecs = np.fft.rfftfreq(medir_ab.N_FFT, d=1.0 / SR)
    sel = (frecs >= medir_ab.BANDA_VOZ_HZ[0]) & (frecs < medir_ab.BANDA_VOZ_HZ[1])

    con_comun = medir_ab.envolvente_ataques(m, SR, medir_ab.BANDA_VOZ_HZ, float(np.max(m**2)))
    con_propia = medir_ab.envolvente_ataques(
        m, SR, medir_ab.BANDA_VOZ_HZ, float(np.max(m[sel] ** 2))
    )
    assert con_propia.max() > 5.0 * con_comun.max(), (
        f"comun {con_comun.max():.3f} vs propia {con_propia.max():.3f}: la referencia "
        "por banda ya no infla la banda vacia, revisa si el remedio sigue haciendo falta"
    )


def test_limitacion_conocida_un_transitorio_ancho_deja_rastro_en_las_dos_bandas() -> None:
    """Queda ESCRITO lo que la metrica no puede: un golpe seco es de banda ancha.

    Un bombo con clic marca la banda de voz aunque no haya voz. Por eso
    `coherencia_voz_beat` es un proxy que solo vale para comparar dos pistas de la
    MISMA instrumentacion entre si, y nunca como veredicto absoluto de encaje.
    """
    m = _mag(_tren(BPM_OBJETIVO, frecuencia=60.0))
    ref = float(np.max(m**2))
    e_voz = medir_ab.envolvente_ataques(m, SR, medir_ab.BANDA_VOZ_HZ, ref)
    assert e_voz.max() > 0.0, "sin nada de fuga, este test no describe la realidad"
