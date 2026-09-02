"""Tests de `spikes/medir_ab.py`: los descriptores contra senales de valor conocido.

Estas metricas son la base de la conclusion del A/B del planificador. Un
centroide mal calculado no da un error: da un numero plausible y una conclusion
falsa. Asi que cada descriptor se comprueba contra senales cuyo valor teorico se
conoce de antemano (ruido blanco, senos puros, silencio), no contra otra
implementacion.
"""

from __future__ import annotations

import numpy as np
import pytest

medir_ab = pytest.importorskip("medir_ab", reason="medir_ab necesita numpy y scipy")

SR = 48000


def _senal(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    x = np.ascontiguousarray(x, dtype=np.float64)
    return x, np.stack([x, x], axis=1), SR


@pytest.fixture(scope="module")
def t() -> np.ndarray:
    return np.arange(SR * 4) / SR


# --------------------------------------------------------------------------- #
# Centroide y rolloff contra valores teoricos
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("f0", [1000.0, 5000.0, 10000.0])
def test_centroide_de_un_seno_es_su_frecuencia(t: np.ndarray, f0: float) -> None:
    d = medir_ab.descriptores(*_senal(0.5 * np.sin(2 * np.pi * f0 * t)))
    assert d["centroide_hz"] == pytest.approx(f0, rel=0.02)
    assert d["rolloff95_hz"] == pytest.approx(f0, rel=0.02)


def test_ruido_blanco_da_centroide_en_un_cuarto_de_la_tasa() -> None:
    """Para ruido blanco el centroide teorico es `sr/4` y el rolloff 95 % es
    `0,95 * sr/2`. Es la comprobacion que detecta un eje de frecuencias mal
    construido, que es el fallo silencioso clasico de una STFT casera."""
    rng = np.random.default_rng(0)
    d = medir_ab.descriptores(*_senal(rng.normal(0, 0.1, SR * 4)))
    assert d["centroide_hz"] == pytest.approx(SR / 4, rel=0.05)
    assert d["rolloff95_hz"] == pytest.approx(0.95 * SR / 2, rel=0.05)


def test_energia_sobre_4k_separa_grave_de_agudo(t: np.ndarray) -> None:
    grave = medir_ab.descriptores(*_senal(0.5 * np.sin(2 * np.pi * 200 * t)))
    agudo = medir_ab.descriptores(*_senal(0.5 * np.sin(2 * np.pi * 8000 * t)))
    assert grave["energia_sobre_4k_pct"] < 0.1
    assert agudo["energia_sobre_4k_pct"] > 99.9


# --------------------------------------------------------------------------- #
# Cresta y planitud
# --------------------------------------------------------------------------- #
def test_factor_de_cresta_de_un_seno_son_3_01_db(t: np.ndarray) -> None:
    """Un seno tiene pico/RMS = raiz de 2 = 3,01 dB. Exacto, no aproximado."""
    d = medir_ab.descriptores(*_senal(0.5 * np.sin(2 * np.pi * 440 * t)))
    assert d["factor_cresta_db"] == pytest.approx(20 * np.log10(np.sqrt(2)), abs=0.05)


def test_planitud_separa_ruido_de_tono(t: np.ndarray) -> None:
    """La planitud espectral es ~1 para ruido blanco y ~0 para un tono puro."""
    rng = np.random.default_rng(1)
    ruido = medir_ab.descriptores(*_senal(rng.normal(0, 0.1, SR * 4)))
    tono = medir_ab.descriptores(*_senal(0.5 * np.sin(2 * np.pi * 440 * t)))
    assert ruido["planitud_espectral"] > 0.3
    assert tono["planitud_espectral"] < 1e-6
    assert ruido["planitud_espectral"] > tono["planitud_espectral"] * 1e5


# --------------------------------------------------------------------------- #
# Estructura: es lo que deberia aportar el planificador
# --------------------------------------------------------------------------- #
def test_std_rms_por_segundo_detecta_secciones(t: np.ndarray) -> None:
    """Una senal con tramos fuertes y flojos tiene que dar mas dispersion de
    energia que una de nivel constante. Si no, la metrica no mide estructura."""
    tono = 0.5 * np.sin(2 * np.pi * 440 * t)
    plana = medir_ab.descriptores(*_senal(tono))

    escalonada = tono.copy()
    for i in range(0, 4):                     # un segundo si, un segundo no
        if i % 2:
            escalonada[i * SR : (i + 1) * SR] *= 0.05
    variada = medir_ab.descriptores(*_senal(escalonada))

    assert plana["std_rms_1s_db"] < 0.5
    assert variada["std_rms_1s_db"] > 5.0


def test_autocorrelacion_de_envolvente_encuentra_el_periodo() -> None:
    """Envolvente pulsada cada 2 s: la ACF tiene que picar en 2 s."""
    dur = 20
    x = np.zeros(SR * dur)
    rng = np.random.default_rng(2)
    ruido = rng.normal(0, 0.3, len(x))
    env = (np.sin(2 * np.pi * (1 / 2.0) * np.arange(len(x)) / SR) > 0).astype(float)
    x = ruido * env
    d = medir_ab.descriptores(*_senal(x))
    assert d["acf_env_lag_s"] == pytest.approx(2.0, abs=0.15)
    assert d["acf_env_pico"] > 0.5


# --------------------------------------------------------------------------- #
# Distancias entre pistas
# --------------------------------------------------------------------------- #
def test_distancia_de_una_pista_consigo_misma_es_cero(t: np.ndarray) -> None:
    x = np.ascontiguousarray(0.4 * np.sin(2 * np.pi * 440 * t))
    a = {"mono": x, "tasa": SR}
    r = medir_ab.distancias(a, a)
    assert r["corr_onda"] == pytest.approx(1.0, abs=1e-9)
    assert r["dist_logmel"] == pytest.approx(0.0, abs=1e-9)


def _musical(rng, n, alpha=0.9, sr=SR):
    """Ruido con caida espectral: espectro LLENO, como una mezcla real.

    Importa que sea lleno. La primera version de este ayudante limitaba la banda
    poniendo bins a CERO exacto, y eso creaba un suelo digital que no existe en
    ninguna pista: dos senales asi coinciden perfectamente en las bandas mudas y
    la distancia se vuelve del reves. El fallo era del ayudante, no de la
    metrica, y conviene que quede escrito.
    """
    x = rng.normal(0, 1.0, n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    X *= 1.0 / np.maximum(f, 20.0) ** alpha
    y = np.fft.irfft(X, n)
    return np.ascontiguousarray(0.3 * y / (np.max(np.abs(y)) + 1e-12))


def test_distancia_crece_con_la_diferencia_real() -> None:
    """Ordenacion: identica < parecida < distinta. Sin esto, comparar `d_lm` con
    `d_semilla` no significaria nada.

    Se usa ruido de banda limitada y no senos: dos pistas de musica tienen el
    espectro lleno, y es ahi donde hay que garantizar el orden.
    """
    rng = np.random.default_rng(3)
    n = SR * 4
    base = _musical(rng, n)
    parecida = np.ascontiguousarray(base + rng.normal(0, 0.003, n))
    distinta = _musical(rng, n)                   # otra realizacion: otra "pista"

    a = {"mono": base, "tasa": SR}
    d_id = medir_ab.distancias(a, a)["dist_logmel"]
    d_par = medir_ab.distancias(a, {"mono": parecida, "tasa": SR})["dist_logmel"]
    d_dis = medir_ab.distancias(a, {"mono": distinta, "tasa": SR})["dist_logmel"]
    assert d_id == pytest.approx(0.0, abs=1e-9)
    assert d_id < d_par < d_dis


def test_el_recorte_de_rango_evita_que_manden_las_bandas_mudas() -> None:
    """Regresion de un fallo real de esta metrica, cazado por un test.

    Con suelo absoluto (`log(pot + 1e-10)`) la distancia la decidian las bandas
    casi mudas: anadir ruido inaudible a un seno puntuaba MAS que retransponer
    ese seno de 440 Hz a 3.000 Hz. Con el recorte de `TOP_DB` el orden es el
    correcto. Si alguien quita el recorte, este test se cae.
    """
    t = np.arange(SR * 4) / SR
    base = np.ascontiguousarray(0.4 * np.sin(2 * np.pi * 440 * t))
    rng = np.random.default_rng(4)
    con_ruido = np.ascontiguousarray(base + rng.normal(0, 0.002, len(base)))
    transpuesto = np.ascontiguousarray(0.4 * np.sin(2 * np.pi * 3000 * t))

    a = {"mono": base, "tasa": SR}
    d_ruido = medir_ab.distancias(a, {"mono": con_ruido, "tasa": SR})["dist_logmel"]
    d_transp = medir_ab.distancias(a, {"mono": transpuesto, "tasa": SR})["dist_logmel"]
    assert d_transp > d_ruido, (
        f"mover 440->3000 Hz ({d_transp:.2f}) tiene que puntuar mas que anadir "
        f"ruido inaudible ({d_ruido:.2f})"
    )


def test_lectura_de_wav_rechaza_lo_que_no_sea_pcm16(tmp_path) -> None:
    import wave

    ruta = tmp_path / "malo.wav"
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)          # 8 bits: no es lo que produce el runner
        w.setframerate(SR)
        w.writeframes(b"\x00" * 100)
    with pytest.raises(ValueError, match="16 bits"):
        medir_ab.leer_wav(ruta)
