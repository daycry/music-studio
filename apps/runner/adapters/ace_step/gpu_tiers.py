"""Configuracion del runner por **nivel de GPU**, detectada en arranque (D-29, T-85).

Por que existe este modulo
--------------------------
Durante el desarrollo de la Fase 0 se fueron clavando a mano decisiones que en
realidad **dependen de la maquina**: si se usa el planificador de 5 Hz y cual, si
hay que descargar componentes a CPU, la duracion maxima, el tamano de lote. Se
clavaron a los valores de la maquina de desarrollo —una GTX 1070 de 8 GB—, que
resulta ser el **segundo nivel mas bajo de seis**.

Eso contradice `spec.md` D-29, que exige «deteccion de GPU/VRAM al arrancar,
offloading automatico si < 24 GB», y ademas falsea cualquier juicio sobre la
calidad del modelo: el hardware de referencia de la spec es una RTX 4090/5090 de
24 GB, que corre en **bf16 sin cuantizar, sin offloading, con el planificador de
1.7B y lote 8**. Nada que ver.

Upstream ya resuelve esto por niveles, asi que aqui **no se inventa nada**: se
adopta su tabla, se le anaden los guardarrailes propios del proyecto y se deja
todo sobreescribible por entorno para poder forzar un nivel en pruebas.

Procedencia de la tabla
-----------------------
Vendorizada de `github.com/ace-step/ACE-Step-1.5` (MIT), ficheros
`acestep/constants.py` (`GPU_TIER_THRESHOLDS`) y `acestep/gpu_config.py`
(`get_gpu_tier`, tabla de configuracion por nivel). Copia local de trabajo en
`D:\\srv\\ace-step\\out\\hyp4\\acestep\\`.

MODIFICADO respecto a upstream, y el motivo de cada cambio, porque su tabla
presupone GPUs modernas y la nuestra no lo es:

1. **INT8 no existe en Pascal.** Upstream pone `quantization_default: True` de
   tier1 a tier6a. `sm_61` no tiene los tensor cores de INT8, asi que en Pascal
   se fuerza a `False` y se avisa. Pedir cuantizacion donde no la hay solo
   produce una degradacion silenciosa o un fallo tardio.
2. **BF16 tampoco existe en Pascal.** El nivel tier6b usa bf16; aqui el dtype se
   decide por capacidad de computo, no por nivel.
3. **Atencion eager obligatoria en `sm_61`.** Medido: SDPA cae al kernel
   *mem-efficient* y tarda 282,20 ms frente a 21,87 ms de eager con softmax en
   fp32, a las formas reales del DiT. Son **12,9x**, y es silencioso.
4. **Suelo de VRAM con tolerancia** (CS-51): la VRAM que reporta CUDA nunca
   llega al nominal — una tarjeta de 8 GB informa 8191 MiB — asi que el nivel se
   calcula sobre el nominal redondeado, no sobre el dato crudo, o toda tarjeta
   caeria un nivel por debajo del suyo.

Este modulo **no toca la GPU**: recibe la VRAM y la capacidad de computo como
argumentos, de modo que se puede probar entero sin tarjeta.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

_LOG = logging.getLogger("ace_step.gpu_tiers")

__all__ = [
    "TIER_THRESHOLDS_GB",
    "ConfiguracionNivel",
    "detectar_nivel",
    "resolver_configuracion",
]

#: Umbrales en GB, verbatim de `constants.py::GPU_TIER_THRESHOLDS` mas los dos
#: cortes que `get_gpu_tier` aplica dentro del antiguo "tier6".
TIER_THRESHOLDS_GB: dict[str, float] = {
    "tier1": 4.0,     # <= 4 GB
    "tier2": 6.0,     # 4-6 GB
    "tier3": 8.0,     # 6-8 GB   <- GTX 1070, maquina de desarrollo
    "tier4": 12.0,    # 8-12 GB
    "tier5": 16.0,    # 12-16 GB
    "tier6a": 20.0,   # 16-20 GB
    "tier6b": 24.0,   # 20-24 GB <- RTX 3090 / 4090, referencia de la spec
    # por encima de 24 GB: "unlimited" (p. ej. L40S de 48 GB)
}

#: Tabla por nivel, adoptada de `gpu_config.py`. Solo se recogen las claves que
#: este runner usa; el resto de la tabla de upstream (backends de vLLM,
#: `compile_model_default`) queda fuera a proposito hasta que haga falta.
_TABLA: dict[str, dict] = {
    "tier1": dict(planificador=False, modelos_lm=[], lm_recomendado=None,
                  duracion_max_con_lm=240, duracion_max_sin_lm=360,
                  lote_max=1, offload_todo=True, offload_dit=True, cuantizar=True),
    "tier2": dict(planificador=False, modelos_lm=[], lm_recomendado=None,
                  duracion_max_con_lm=480, duracion_max_sin_lm=600,
                  lote_max=1, offload_todo=True, offload_dit=True, cuantizar=True),
    "tier3": dict(planificador=True, modelos_lm=["acestep-5Hz-lm-0.6B"],
                  lm_recomendado="acestep-5Hz-lm-0.6B",
                  duracion_max_con_lm=480, duracion_max_sin_lm=600,
                  lote_max=2, offload_todo=True, offload_dit=True, cuantizar=True),
    "tier4": dict(planificador=True, modelos_lm=["acestep-5Hz-lm-0.6B"],
                  lm_recomendado="acestep-5Hz-lm-0.6B",
                  duracion_max_con_lm=480, duracion_max_sin_lm=600,
                  lote_max=2, offload_todo=True, offload_dit=True, cuantizar=True),
    "tier5": dict(planificador=True,
                  modelos_lm=["acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B"],
                  lm_recomendado="acestep-5Hz-lm-1.7B",
                  duracion_max_con_lm=480, duracion_max_sin_lm=600,
                  lote_max=4, offload_todo=True, offload_dit=False, cuantizar=True),
    "tier6a": dict(planificador=True,
                   modelos_lm=["acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B"],
                   lm_recomendado="acestep-5Hz-lm-1.7B",
                   duracion_max_con_lm=480, duracion_max_sin_lm=600,
                   lote_max=4, offload_todo=True, offload_dit=False, cuantizar=True),
    "tier6b": dict(planificador=True,
                   modelos_lm=["acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B",
                               "acestep-5Hz-lm-4B"],
                   lm_recomendado="acestep-5Hz-lm-1.7B",
                   duracion_max_con_lm=480, duracion_max_sin_lm=480,
                   lote_max=8, offload_todo=False, offload_dit=False, cuantizar=False),
    "unlimited": dict(planificador=True,
                      modelos_lm=["acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B",
                                  "acestep-5Hz-lm-4B"],
                      lm_recomendado="acestep-5Hz-lm-4B",
                      duracion_max_con_lm=600, duracion_max_sin_lm=600,
                      lote_max=8, offload_todo=False, offload_dit=False, cuantizar=False),
}


def detectar_nivel(vram_mb: int) -> str:
    """Devuelve el nivel para una VRAM dada, en MiB tal y como la reporta CUDA.

    Se redondea al GB nominal **hacia arriba** antes de comparar. Sin eso, toda
    tarjeta caeria un nivel por debajo del suyo: CUDA informa 8191 MiB en una de
    8 GB (el driver se reserva ~132 MiB), y 8191/1024 = 7,999 GB entraria en
    "6-8 GB" por los pelos pero una de 12 GB reportando 12287 MiB caeria a
    tier4 en vez de tier5. Es el mismo problema que CS-51 y se resuelve igual:
    comparando contra el envase, no contra el dato crudo.
    """
    if vram_mb <= 0:
        return "tier1"  # modo CPU: se usan los limites mas conservadores
    # Redondeo al GB de envase. Las tarjetas se venden en GB enteros y CUDA
    # informa algo menos (una de 8 GB dice 8191 MiB), asi que redondear al entero
    # mas cercano recupera la cifra comercial sin inventarse memoria.
    gb = round(vram_mb / 1024.0)
    # Cadena identica a `get_gpu_tier` de upstream. Se escribe explicita, y no
    # como bucle sobre la tabla, porque sus cortes NO son homogeneos: tier4 se
    # cierra con `<= 12` pero tier5 con `< 16`, de modo que una tarjeta de 16 GB
    # cae en tier6a y no en tier5. Un bucle con `<=` se equivocaria justo ahi.
    if gb <= 4:
        return "tier1"
    if gb <= 6:
        return "tier2"
    if gb <= 8:
        return "tier3"
    if gb <= 12:
        return "tier4"
    if gb < 16:
        return "tier5"
    if gb < 20:
        return "tier6a"
    if gb <= 24:
        return "tier6b"
    return "unlimited"


@dataclass(frozen=True)
class ConfiguracionNivel:
    """Configuracion efectiva del runner para una maquina concreta."""

    nivel: str
    vram_mb: int
    capacidad: tuple[int, int] | None
    planificador: bool
    modelos_lm: list[str]
    lm_recomendado: str | None
    duracion_max_s: int
    lote_max: int
    offload_todo: bool
    offload_dit: bool
    cuantizar: bool
    dtype: str
    atencion: str
    decode_vae_por_trozos: bool
    avisos: list[str] = field(default_factory=list)

    def resumen(self) -> str:
        lm = self.lm_recomendado or "ninguno"
        return (
            f"nivel={self.nivel} vram={self.vram_mb} MiB dtype={self.dtype} "
            f"atencion={self.atencion} planificador={lm} lote<={self.lote_max} "
            f"duracion<={self.duracion_max_s}s offload_dit={self.offload_dit} "
            f"cuantizar={self.cuantizar}"
        )


def resolver_configuracion(
    vram_mb: int,
    capacidad: tuple[int, int] | None = None,
    *,
    forzar_nivel: str | None = None,
    usar_planificador: bool | None = None,
) -> ConfiguracionNivel:
    """Resuelve la configuracion efectiva y explica cada desviacion.

    `capacidad` es la *compute capability* como `(major, minor)`; `(6, 1)` es
    Pascal. Se pasa como argumento en vez de consultarse aqui para que este
    modulo sea probable sin GPU.

    Sobreescrituras por entorno, pensadas para pruebas y para el gate G1:
      * `ACE_STEP_TIER` fuerza el nivel (util para reproducir el
        comportamiento de otra maquina).
      * `ACE_STEP_USE_LM` a 0/1 fuerza el planificador.
    """
    nivel = (forzar_nivel or os.environ.get("ACE_STEP_TIER") or "").strip()
    avisos: list[str] = []
    if nivel:
        if nivel not in _TABLA:
            raise ValueError(
                f"Nivel {nivel!r} desconocido. Validos: {', '.join(_TABLA)}."
            )
        avisos.append(
            f"Nivel FORZADO a {nivel} (la deteccion habria dicho "
            f"{detectar_nivel(vram_mb)}). El informe no representa a esta maquina."
        )
    else:
        nivel = detectar_nivel(vram_mb)

    base = dict(_TABLA[nivel])

    es_pascal = capacidad is not None and capacidad < (7, 0)

    # (1) INT8: no existe en Pascal. Pedirla donde no la hay degrada en silencio.
    cuantizar = bool(base["cuantizar"])
    if cuantizar and es_pascal:
        cuantizar = False
        avisos.append(
            f"Cuantizacion desactivada: la tabla de {nivel} la pide, pero "
            f"sm_{capacidad[0]}{capacidad[1]} no tiene INT8. Se pierde el ahorro "
            "de VRAM que ese nivel presupone."
        )

    # (2) dtype: lo decide la capacidad de computo, no el nivel.
    if es_pascal:
        dtype = "float16"
    elif capacidad is not None and capacidad >= (8, 0):
        dtype = "bfloat16"
    else:
        dtype = "float16"

    # (3) Atencion: en Pascal, eager o se pierde un 12,9x sin enterarse.
    if es_pascal:
        atencion = "eager"
        avisos.append(
            "Atencion forzada a eager: en sm_61 no hay FlashAttention ni cuDNN "
            "MHA y SDPA cae al kernel mem-efficient, 12,9x mas lento (282,20 ms "
            "frente a 21,87 ms, medido). La degradacion es silenciosa."
        )
    else:
        atencion = "sdpa"

    # (4) Planificador: la tabla manda, salvo orden expresa.
    planificador = bool(base["planificador"])
    forzado_lm = os.environ.get("ACE_STEP_USE_LM")
    if usar_planificador is not None:
        planificador = usar_planificador
    elif forzado_lm is not None:
        planificador = forzado_lm.strip() not in ("0", "", "false", "no")
    if planificador and not base["modelos_lm"]:
        planificador = False
        avisos.append(
            f"Planificador pedido pero {nivel} no tiene ningun modelo LM que "
            "quepa. Se genera sin plan semantico."
        )

    duracion = int(
        base["duracion_max_con_lm"] if planificador else base["duracion_max_sin_lm"]
    )

    # (5) Decode del VAE por trozos: monolitico solo cabe con VRAM de sobra.
    por_trozos = nivel not in ("tier6b", "unlimited")

    if nivel in ("tier1", "tier2", "tier3"):
        avisos.append(
            f"{nivel} es un nivel BAJO de los ocho. La referencia de la spec "
            "(RTX 4090/5090) es tier6b, que corre sin offloading, sin cuantizar "
            "y con el planificador de 1.7B. Cualquier juicio de calidad emitido "
            "aqui describe el suelo del producto, no su objetivo — relevante "
            "para el gate G1."
        )

    cfg = ConfiguracionNivel(
        nivel=nivel,
        vram_mb=vram_mb,
        capacidad=capacidad,
        planificador=planificador,
        modelos_lm=list(base["modelos_lm"]),
        lm_recomendado=(base["lm_recomendado"] if planificador else None),
        duracion_max_s=duracion,
        lote_max=int(base["lote_max"]),
        offload_todo=bool(base["offload_todo"]),
        offload_dit=bool(base["offload_dit"]),
        cuantizar=cuantizar,
        dtype=dtype,
        atencion=atencion,
        decode_vae_por_trozos=por_trozos,
        avisos=avisos,
    )
    _LOG.info("Configuracion por nivel: %s", cfg.resumen())
    for aviso in avisos:
        _LOG.warning("%s", aviso)
    return cfg
