"""Tests del suelo de VRAM de `decide_offloading()` — regresion de **CS-51**.

Por que este fichero existe aparte de `test_timing.py`
------------------------------------------------------
`test_timing.py` cubre `_timing.py` en general (estadisticas, informes, la
decision de offloading en sus tres tramos). Este fichero cubre **una sola cosa**:
que el suelo de 8 GB de D-06 / `spec.md` §11.1 admite de verdad una tarjeta de
8 GB. Va suelto para que sea localizable por nombre y para que nadie lo borre
por parecer redundante con los tests de tramo.

El bug que blinda (verificado en la maquina local, no teorico)
--------------------------------------------------------------
`VRAM_FLOOR_MB = 8 * 1024 = 8192` se comparaba con
`int(props.total_memory) // (1024 * 1024)`, que **no** es la VRAM nominal de la
tarjeta sino la utilizable tras la reserva del driver, truncada a MB. En la GTX
1070 de la maquina de desarrollo:

* `cuDeviceTotalMem_v2` = 8.589.672.448 B = 8191,75 MiB -> se lee **8191**.
* `nvidia-smi`: `Total` 8192 MiB, `Reserved` **132 MiB**.

Con el `<` estricto contra 8192, **cualquier** tarjeta de 8 GB daba `NO VIABLE` y
`adapter._load_sync()` abortaba antes de tocar los pesos: el suelo de 8 GB era
inalcanzable por construccion. El arreglo es la banda `VRAM_FLOOR_TOLERANCE_MB`,
que convierte la comparacion en una de VRAM *reportada* frente a VRAM *nominal*.

AVISO: el suelo **efectivo** resultante (8128 MB) es un umbral de spec y necesita
ratificacion del propietario — ver la nota de `VRAM_FLOOR_TOLERANCE_MB` en
`spikes/_timing.py` y el item 7-ter (CS-51) de `pre-dev-checklist.md`. Estos
tests fijan el comportamiento acordado; si el propietario ratifica otra cifra,
se cambian aqui **a la vez** que la constante, nunca solo la constante.

Todo corre sin torch y sin GPU: `decide_offloading()` recibe un entero.
"""

from __future__ import annotations

import _timing

#: Suelo efectivo, derivado — nunca escrito a mano en las aserciones salvo en el
#: test que comprueba a proposito que la cifra publicada es 8128.
SUELO_EFECTIVO_MB = _timing.VRAM_FLOOR_MB - _timing.VRAM_FLOOR_TOLERANCE_MB

#: Lo que reporta `torch.cuda.get_device_properties(0).total_memory // 1024**2` en
#: la GTX 1070 de la maquina local. Es el caso frontera real, medido.
GTX_1070_REPORTA_MB = 8191


# --------------------------------------------------------------------------- #
# La regresion: una 8 GB de verdad debe pasar
# --------------------------------------------------------------------------- #

class TestSueloDeVramCS51:
    def test_gtx1070_8191_mib_es_viable(self):
        """LA REGRESION DE CS-51. No borrar por "numero magico": 8191 es la cifra
        que reporta CUDA en una GTX 1070 de 8 GB, y con el suelo estricto de 8192
        el propio codigo declaraba no ejecutable la unica GPU del proyecto.
        """
        offload, motivo = _timing.decide_offloading(GTX_1070_REPORTA_MB)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX), (
            "Regresion de CS-51: una GTX 1070 de 8 GB (reporta 8191 MB) ha vuelto "
            f"a declararse no viable. Motivo devuelto: {motivo}"
        )
        # Cae en el tramo intermedio: viable, pero con el aviso de D-29.
        assert "DEGRADADOS" in motivo

    def test_suelo_menos_tolerancia_exacto_es_viable(self):
        """El borde inferior de la banda es inclusivo: 8128 pasa."""
        offload, motivo = _timing.decide_offloading(SUELO_EFECTIVO_MB)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_un_mib_por_debajo_de_la_tolerancia_no_es_viable(self):
        """Y 8127 no. La banda tiene un borde definido, no un degradado."""
        offload, motivo = _timing.decide_offloading(SUELO_EFECTIVO_MB - 1)
        assert offload is True  # valor conservador; no significa "se puede ejecutar"
        assert motivo.startswith(_timing.NOT_VIABLE_PREFIX)


# --------------------------------------------------------------------------- #
# La tolerancia no puede convertirse en una rampa
# --------------------------------------------------------------------------- #

class TestLaToleranciaNoEsUnaRampa:
    def test_tarjeta_de_6gb_sigue_siendo_no_viable(self):
        """El aborto real se conserva para tarjetas por debajo de 8 GB de verdad.

        6144 + 64 = 6208, muy por debajo de 8192: el siguiente escalon comercial
        no se cuela por la banda. Si este test se pone en rojo es que alguien ha
        ampliado la tolerancia hasta hacerla otra cosa.
        """
        offload, motivo = _timing.decide_offloading(6 * 1024)
        assert offload is True
        assert motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_tarjetas_claramente_insuficientes_abortan(self):
        for vram_mb in (2 * 1024, 4 * 1024, 6 * 1024, 7 * 1024):
            offload, motivo = _timing.decide_offloading(vram_mb)
            assert offload is True
            assert motivo.startswith(_timing.NOT_VIABLE_PREFIX), (
                f"{vram_mb} MB deberia seguir siendo NO VIABLE; motivo: {motivo}"
            )

    def test_la_tolerancia_es_pequena_frente_al_suelo(self):
        """Guardarrail de magnitud: la banda corrige una unidad de medida (< 1 %
        del suelo), no relaja el requisito de hardware.
        """
        assert 0 < _timing.VRAM_FLOOR_TOLERANCE_MB <= _timing.VRAM_FLOOR_MB // 64


# --------------------------------------------------------------------------- #
# Contrato publico: valores y mensaje
# --------------------------------------------------------------------------- #

class TestContratoDelSuelo:
    def test_el_suelo_nominal_no_cambia(self):
        """`VRAM_FLOOR_MB` sigue valiendo 8192 a proposito.

        `vram_profile.py` lo usa como techo de PICO (`fits_floor_8gb`) y
        `_mock.py` como VRAM total simulada: tocar el numero les cambiaria el
        significado por debajo. El arreglo de CS-51 va en la tolerancia.
        """
        assert _timing.VRAM_FLOOR_MB == 8 * 1024

    def test_la_tolerancia_esta_exportada(self):
        """Es API publica del modulo: los spikes y el adapter la citan."""
        assert "VRAM_FLOOR_TOLERANCE_MB" in _timing.__all__

    def test_mensaje_no_viable_cita_el_suelo_efectivo(self):
        """El operador tiene que poder comparar su VRAM con el minimo real.

        Un mensaje que solo cite 8192 manda a la gente a buscar una tarjeta que
        no necesita: el minimo aplicado es 8128.
        """
        _, motivo = _timing.decide_offloading(6 * 1024)
        assert "8128" in motivo
        assert str(_timing.VRAM_FLOOR_MB) in motivo  # el nominal tambien aparece
        assert "6144" in motivo                      # y la VRAM detectada

    def test_mensaje_no_viable_no_repite_la_afirmacion_falsa_del_3_5b(self):
        """Dos afirmaciones del mensaje anterior eran falsas y no deben volver:
        el recuento de "3,5B" (son 2,394 G del checkpoint ACE-Step, 3,158 G con
        text encoder y VAE) y el "no arranca ni con offloading" (el offloading lo
        decide la factoria del pipeline, que se ejecuta DESPUES de que
        `load_file()` haya depositado el artefacto entero en VRAM).
        """
        _, motivo = _timing.decide_offloading(4 * 1024)
        assert "3,5B" not in motivo
        assert "no arranca ni con offloading" not in motivo
        assert "2,394 G" in motivo  # el recuento que si sale del checkpoint


# --------------------------------------------------------------------------- #
# Los tramos de arriba no se han movido
# --------------------------------------------------------------------------- #

class TestTramosSuperioresIntactos:
    def test_suelo_nominal_exacto_sigue_siendo_viable_con_offloading(self):
        offload, motivo = _timing.decide_offloading(_timing.VRAM_FLOOR_MB)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_confort_exacto_sigue_sin_offloading(self):
        offload, motivo = _timing.decide_offloading(_timing.VRAM_COMFORT_MB)
        assert offload is False
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_vram_desconocida_sigue_siendo_conservadora(self):
        """La tolerancia no debe haber tocado la rama de `None` (maquina sin
        CUDA): ahi no hay aritmetica que hacer y sumar sobre `None` reventaria.
        """
        offload, motivo = _timing.decide_offloading(None)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)
