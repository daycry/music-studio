"""Tests del limitador de picos del shim (`_limitar_picos` y `_a_pcm16`), sin GPU.

Regresion del defecto que destapo la revision del 2026-09-03: `_a_pcm16` quita el
eje de lote (`onda[0]`) y entrega `[C, N]`, pero el limitador reducia DOS ejes
como si recibiera `[1, C, N]`. La envolvente se colapsaba a un escalar y la
"limitacion" era una ganancia constante sobre toda la pista. El pico de salida
daba exactamente -1 dBFS, asi que ninguna verificacion por pico lo veia.

Por eso estos tests no miran el pico: miran lo que un pico no cuenta. Que la
senal lejos del transitorio salga **identica** a la entrada, que no haya fundido
en los bordes, que la ganancia sea la misma en los dos canales y que el informe
diga la verdad sobre cuantas muestras se tocaron.

La suite se salta sin torch (ver `conftest.py`): el shim lo necesita para importar.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

torch = pytest.importorskip("torch", reason="el shim necesita torch")

import ace_step_shim as shim  # noqa: E402

SR = 48000
TECHO = 10.0 ** (shim.TECHO_LIMITADOR_DB / 20.0)


def _base(segundos: float = 3.0, nivel: float = 0.25, canales: int = 2) -> torch.Tensor:
    """Seno grave a `nivel`, bien por debajo del techo, en todos los canales."""
    t = torch.arange(int(segundos * SR), dtype=torch.float32) / SR
    seno = nivel * torch.sin(2.0 * math.pi * 110.0 * t)
    return seno.unsqueeze(0).repeat(canales, 1)


def _con_transitorio(onda: torch.Tensor, *, en_s: float = 1.0, valor: float = 1.4,
                     canales: tuple[int, ...] | None = None) -> tuple[torch.Tensor, int]:
    """Copia de `onda` con una sola muestra a +3 dBFS en `en_s`."""
    onda = onda.clone()
    i = int(en_s * SR)
    for c in (range(onda.shape[0]) if canales is None else canales):
        onda[c, i] = valor
    return onda, i


def _lejos(i: int, n: int) -> slice:
    """Tramo a mas de un segundo del transitorio: ahi la ganancia debe ser 1."""
    return slice(i + SR, n)


class TestLimitarPicos:
    def test_lejos_del_transitorio_la_senal_sale_identica(self):
        onda, i = _con_transitorio(_base())
        salida, informe = shim._limitar_picos(onda)
        lejos = _lejos(i, onda.shape[1])
        assert torch.equal(salida[:, lejos], onda[:, lejos]), (
            "un transitorio de una muestra ha cambiado la senal a un segundo de "
            "distancia: la ganancia no es local"
        )
        assert informe["porcentaje_tocado"] < 10.0, informe

    def test_no_hay_fundido_en_los_bordes(self):
        onda, _ = _con_transitorio(_base())
        salida, _ = shim._limitar_picos(onda)
        assert torch.equal(salida[:, :100], onda[:, :100])
        assert torch.equal(salida[:, -100:], onda[:, -100:])

    def test_el_pico_de_salida_respeta_el_techo(self):
        onda, _ = _con_transitorio(_base())
        salida, informe = shim._limitar_picos(onda)
        assert float(salida.abs().max()) <= TECHO + 1e-6
        assert informe["reduccion_db"] > 0.0

    def test_la_ganancia_es_la_misma_en_los_dos_canales(self):
        # Solo el canal izquierdo se pasa. Si la ganancia fuera por canal, la
        # imagen estereo se movería al limitar; tiene que ser comun.
        onda, i = _con_transitorio(_base(), canales=(0,))
        onda[1, i] = 0.25
        salida, _ = shim._limitar_picos(onda)
        g_izq = float(salida[0, i] / onda[0, i])
        g_der = float(salida[1, i] / onda[1, i])
        assert g_der < 1.0, "el canal sin pico no se ha atenuado a la vez que el otro"
        assert g_der == pytest.approx(g_izq, rel=1e-5)

    def test_funciona_en_mono(self):
        onda, i = _con_transitorio(_base(canales=1))
        salida, _ = shim._limitar_picos(onda)
        lejos = _lejos(i, onda.shape[1])
        assert salida.shape == onda.shape
        assert torch.equal(salida[:, lejos], onda[:, lejos])

    def test_onda_bajo_el_techo_sale_intacta(self):
        onda = _base()
        salida, informe = shim._limitar_picos(onda)
        assert torch.equal(salida, onda)
        assert informe["reduccion_db"] == 0.0
        assert informe["porcentaje_tocado"] == 0.0

    def test_silencio_total_no_revienta(self):
        onda = torch.zeros(2, SR)
        salida, informe = shim._limitar_picos(onda)
        assert torch.equal(salida, onda)
        assert informe["pico_entrada_db"] == float("-inf")

    def test_rechaza_una_onda_con_eje_de_lote(self):
        # El contrato es [C, N]. Aceptar [1, C, N] en silencio es exactamente
        # como nacio el defecto.
        with pytest.raises(RuntimeError, match=r"\[C, N\]"):
            shim._limitar_picos(torch.zeros(1, 2, SR))


class TestAPcm16:
    """El punto de llamada real: `[1, C, N]` -> PCM16. Aqui es donde fallaba."""

    @staticmethod
    def _decodificar(datos: bytes, canales: int, muestras: int) -> np.ndarray:
        return np.frombuffer(datos, dtype="<i2").reshape(muestras, canales)

    def test_un_transitorio_no_atenua_la_pista_entera(self):
        n = 3 * SR
        onda = torch.full((1, 2, n), 0.25)
        i = SR
        onda[0, :, i] = 1.4
        datos, canales, muestras = shim._a_pcm16(onda)
        pcm = self._decodificar(datos, canales, muestras)
        esperado = round(0.25 * 32767.0)
        lejos = pcm[_lejos(i, n), :]
        assert (lejos == esperado).all(), (
            f"lejos del transitorio deberia haber {esperado} y hay "
            f"{np.unique(lejos)[:5]}: la pista entera se ha atenuado"
        )
        assert abs(int(pcm[i, 0])) <= round(TECHO * 32767.0) + 1

    def test_sin_transitorio_el_pcm_es_la_cuantizacion_directa(self):
        onda = torch.full((1, 2, SR), 0.25)
        datos, canales, muestras = shim._a_pcm16(onda)
        pcm = self._decodificar(datos, canales, muestras)
        assert (pcm == round(0.25 * 32767.0)).all()


class TestFormaYCoste:
    """Lo que destapo la segunda revision (2026-09-03): al corregir el eje, el
    limitador paso de operar sobre un escalar a convoluciones O(N*K) sobre la
    pista entera (205 s de CPU para 180 s de audio, contados como gpu_seconds), y
    el `minimum` con la ganancia cruda reinstauraba un escalon de ~3 dB en una
    sola muestra a +-10 ms del pico: un clic que G1 atribuiria al modelo.
    """

    def test_la_ganancia_no_da_saltos(self):
        # La pendiente de la ganancia esta acotada por la rampa de ataque: la
        # reduccion completa se reparte, como minimo, en _ANTICIPACION_MUESTRAS.
        # Base constante: sin cruces por cero, `salida / onda` ES la ganancia.
        onda, i = _con_transitorio(torch.full((2, 3 * SR), 0.25), valor=1.4)
        salida, _ = shim._limitar_picos(onda)
        ganancia = salida[0] / onda[0]
        salto = (ganancia[1:] - ganancia[:-1]).abs()
        techo_salto = (1.0 - TECHO / 1.4) / shim._ANTICIPACION_MUESTRAS * 1.05
        assert float(salto.max()) <= techo_salto, (
            f"salto maximo {float(salto.max()):.4f} por muestra; el maximo admisible "
            f"para una rampa de {shim._ANTICIPACION_MUESTRAS} muestras es {techo_salto:.4f}"
        )

    def test_el_coste_es_lineal_y_pequeno(self):
        import time

        onda, _ = _con_transitorio(_base(segundos=60.0), en_s=30.0)
        inicio = time.perf_counter()
        shim._limitar_picos(onda)
        coste = time.perf_counter() - inicio
        assert coste < 3.0, (
            f"{coste:.1f} s para limitar 60 s de audio en CPU: esto se contabiliza como "
            "gpu_seconds y contamina D-17 y T-03"
        )
