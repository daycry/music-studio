"""Pruebas de la configuracion por nivel de GPU (D-29, T-85).

Corren sin GPU y sin torch: `gpu_tiers` recibe la VRAM y la capacidad de computo
como argumentos justamente para poder probarse en cualquier maquina.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "adapters" / "ace_step"))

import gpu_tiers  # noqa: E402


PASCAL = (6, 1)
AMPERE = (8, 6)


# --------------------------------------------------------------------------- #
# Deteccion del nivel
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "vram_mb, esperado",
    [
        (0, "tier1"),          # modo CPU
        (4096, "tier1"),
        (6144, "tier2"),
        (8191, "tier3"),       # <- la GTX 1070 real: CUDA informa 8191, no 8192
        (8192, "tier3"),
        (12287, "tier4"),      # 12 GB entra en tier4: upstream cierra con "<= 12"
        (14336, "tier5"),      # 14 GB si es tier5 (12 < x < 16)
        (16384, "tier6a"),     # 16 GB NO es tier5: tier5 cierra con "< 16"
        (24576, "tier6b"),     # <- RTX 4090, referencia de la spec
        (49140, "unlimited"),  # <- L40S de 48 GB
    ],
)
def test_deteccion_de_nivel(vram_mb, esperado):
    assert gpu_tiers.detectar_nivel(vram_mb) == esperado


def test_la_1070_no_cae_un_nivel_por_los_132_mib_del_driver():
    """CS-51 otra vez: comparar contra el dato crudo degradaria el nivel."""
    assert gpu_tiers.detectar_nivel(8191) == gpu_tiers.detectar_nivel(8192)


# --------------------------------------------------------------------------- #
# Correcciones sobre la tabla de upstream
# --------------------------------------------------------------------------- #

def test_pascal_no_cuantiza_aunque_la_tabla_lo_pida():
    cfg = gpu_tiers.resolver_configuracion(8191, PASCAL)
    assert gpu_tiers._TABLA["tier3"]["cuantizar"] is True, "premisa del test"
    assert cfg.cuantizar is False
    assert any("INT8" in a for a in cfg.avisos)


def test_pascal_usa_fp16_y_atencion_eager():
    cfg = gpu_tiers.resolver_configuracion(8191, PASCAL)
    assert cfg.dtype == "float16"
    assert cfg.atencion == "eager"
    assert any("12,9x" in a for a in cfg.avisos)


def test_ampere_de_24gb_usa_bf16_sdpa_y_no_offloadea_el_dit():
    cfg = gpu_tiers.resolver_configuracion(24576, AMPERE)
    assert cfg.nivel == "tier6b"
    assert cfg.dtype == "bfloat16"
    assert cfg.atencion == "sdpa"
    assert cfg.offload_dit is False
    assert cfg.cuantizar is False
    assert cfg.decode_vae_por_trozos is False


def test_una_tarjeta_de_16gb_no_se_queda_en_tier5():
    """El corte de tier5 es estricto (`< 16`), asi que 16 GB sube a tier6a."""
    assert gpu_tiers.detectar_nivel(16384) == "tier6a"
    assert gpu_tiers.detectar_nivel(15360) == "tier5"


def test_el_planificador_escala_con_el_nivel():
    bajo = gpu_tiers.resolver_configuracion(4096, PASCAL)
    medio = gpu_tiers.resolver_configuracion(8191, PASCAL)
    alto = gpu_tiers.resolver_configuracion(24576, AMPERE)
    assert bajo.planificador is False and bajo.lm_recomendado is None
    assert medio.lm_recomendado == "acestep-5Hz-lm-0.6B"
    assert alto.lm_recomendado == "acestep-5Hz-lm-1.7B"
    assert bajo.lote_max < medio.lote_max < alto.lote_max


def test_pedir_planificador_donde_no_cabe_no_revienta_pero_avisa():
    cfg = gpu_tiers.resolver_configuracion(4096, PASCAL, usar_planificador=True)
    assert cfg.planificador is False
    assert any("no tiene ningun modelo LM" in a for a in cfg.avisos)


# --------------------------------------------------------------------------- #
# Guardarrail para G1: el nivel bajo tiene que avisar de que lo es
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("vram_mb", [4096, 6144, 8191])
def test_los_niveles_bajos_avisan_de_que_juzgan_el_suelo(vram_mb):
    cfg = gpu_tiers.resolver_configuracion(vram_mb, PASCAL)
    assert any("G1" in a for a in cfg.avisos), (
        "un juicio de calidad emitido en un nivel bajo tiene que llevar el aviso "
        "encima, o G1 condenaria al modelo por el hardware"
    )


def test_el_nivel_de_referencia_no_lleva_ese_aviso():
    cfg = gpu_tiers.resolver_configuracion(24576, AMPERE)
    assert not any("G1" in a for a in cfg.avisos)


# --------------------------------------------------------------------------- #
# Sobreescrituras
# --------------------------------------------------------------------------- #

def test_forzar_nivel_avisa_de_que_el_informe_no_es_de_esta_maquina():
    cfg = gpu_tiers.resolver_configuracion(8191, PASCAL, forzar_nivel="tier6b")
    assert cfg.nivel == "tier6b"
    assert any("FORZADO" in a for a in cfg.avisos)


def test_forzar_un_nivel_inexistente_falla_pronto_y_claro():
    with pytest.raises(ValueError, match="desconocido"):
        gpu_tiers.resolver_configuracion(8191, PASCAL, forzar_nivel="tier99")


def test_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("ACE_STEP_TIER", "tier5")
    monkeypatch.setenv("ACE_STEP_USE_LM", "0")
    cfg = gpu_tiers.resolver_configuracion(8191, PASCAL)
    assert cfg.nivel == "tier5"
    assert cfg.planificador is False
    assert cfg.duracion_max_s == 600, "sin planificador se admite mas duracion"


def test_el_argumento_explicito_gana_a_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("ACE_STEP_USE_LM", "1")
    cfg = gpu_tiers.resolver_configuracion(8191, PASCAL, usar_planificador=False)
    assert cfg.planificador is False


def test_sin_capacidad_conocida_no_asume_pascal():
    cfg = gpu_tiers.resolver_configuracion(24576, None)
    assert cfg.atencion == "sdpa"
    assert cfg.cuantizar is False, "tier6b no cuantiza de todos modos"


# --------------------------------------------------------------------------- #
# Fidelidad a upstream en los bordes (revision 2026-09-03)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "vram_mb, esperado, porque",
    [
        # Cadena de upstream sobre GB CRUDOS (gpu_config.py, get_gpu_tier):
        #   <= 4 t1 | <= 6 t2 | <= 8 t3 | <= 12 t4 | < 15,5 t5 | < 20 t6a
        #   | <= 24 t6b | resto unlimited
        # con VRAM_16GB_MIN_GB = 16,0 - 0,5 y VRAM_AUTO_OFFLOAD_THRESHOLD_GB = 20,0.
        (8191, "tier3", "7,999 GB entra en '<= 8' sin necesidad de redondear nada"),
        (12287, "tier4", "11,999 GB entra en '<= 12': upstream tambien da tier4 aqui"),
        (15770, "tier5", "15,4 GB queda por debajo de la tolerancia de 15,5"),
        (15974, "tier6a", "15,6 GB alcanza la tolerancia: clase de 16 GB, con offload"),
        (19968, "tier6a", "19,5 GB: 20 GB nominales reportan menos, y siguen bajo el umbral"),
        (20378, "tier6a", "19,9 GB: el caso que el redondeo mandaba a tier6b y revienta"),
        (20480, "tier6b", "20,0 GB exactos ya NO estan por debajo del umbral"),
        (24564, "tier6b", "23,99 GB de una tarjeta de 24 GB entran en '<= 24'"),
        (32768, "unlimited", "32 GB pasa de 24"),
    ],
)
def test_los_bordes_coinciden_con_la_cadena_de_upstream(vram_mb, esperado, porque):
    assert gpu_tiers.detectar_nivel(vram_mb) == esperado, porque


def test_una_tarjeta_de_20gb_nominales_no_se_promociona_de_nivel():
    """El defecto concreto: 20 GB nominales acababan en tier6b y darian OOM.

    Una RTX 4000 Ada o una A4500 de 20 GB informa ~19,5-19,9 GB. Redondeando al
    GB, eso daba 20, el corte 'menor que 20' era falso y la tarjeta caia en
    tier6b: sin offload, sin cuantizar, lote 8 y planificador de 4B. Upstream la
    pone en tier6a, que es la configuracion que si le cabe.
    """
    for vram_mb in (19968, 20070, 20275, 20378):
        nivel = gpu_tiers.detectar_nivel(vram_mb)
        assert nivel == "tier6a", f"{vram_mb} MiB dio {nivel}"
        cfg = gpu_tiers._TABLA[nivel]
        assert cfg["offload_todo"] or cfg["offload_dit"], (
            "tier6a tiene que descargar algo: es la razon de que exista"
        )


def test_el_docstring_no_promete_una_fidelidad_que_no_tiene():
    """Guardarrail de honestidad, no de comportamiento.

    El docstring afirmaba ser la 'cadena identica a upstream' mientras redondeaba
    antes de comparar, y justificaba el redondeo con un ejemplo falso (decia que
    12287 MiB caeria a tier4 'en vez de tier5', cuando upstream tambien da tier4).
    Si vuelve a aparecer un redondeo, que no venga acompanado de esa promesa.
    """
    import inspect

    fuente = inspect.getsource(gpu_tiers.detectar_nivel)
    assert "round(" not in fuente, (
        "si se reintroduce el redondeo, hay que revisar el tramo de 19,5-19,9 GB "
        "y quitar la promesa de fidelidad del docstring"
    )
