"""Pipeline de inferencia `text2music` de ACE-Step 1.5 turbo, vendorizado.

Este paquete es la mitad que faltaba en `vendor/`: alli esta la **definicion del
modelo** (grafo del DiT, del codificador de condicion, del tokenizador de audio)
y el **decoder del VAE** (`oobleck_decoder.py`); aqui esta lo que hay que hacer
con ellos para que salga una cancion. Procedencia, revisiones fijadas, hashes
SHA-256 y estado de la revision de seguridad, en `README.md` de este directorio.

Orden de uso
------------
1. `conditioning.preparar_condicionamiento_text2music(...)` -> condicionamiento.
2. `diffusion.generar_latentes_text2music(...)` -> latentes `[1, T, 64]`.
3. `decode.decodificar_latentes(...)` -> forma de onda `[1, 2, T*1920]` a 48 kHz.

Este paquete **no instancia nada**: recibe el modelo, el codificador de texto, el
tokenizador y el decoder del VAE ya construidos. Quien los construye desde el
`state_dict` del artefacto es el shim (`ace_step_shim.py`), que es tambien quien
fija `model.config._attn_implementation = "eager"` antes de la primera pasada
(en sm_61 la ruta SDPA cae al kernel mem-efficient y va 12,9x mas lenta, en
silencio).

El decoder del VAE **no se reimplementa aqui**: `decode.py` importa el
`oobleck_decoder.py` del directorio padre, que ya esta verificado en la GPU.

Los imports son **perezosos** (`__getattr__` de modulo, PEP 562): importar el
paquete no arrastra `torch` ni `transformers`, para que el arbol se pueda
inspeccionar en una maquina sin GPU y sin dependencias pesadas.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "CondicionamientoText2Music",
    "DEFAULT_DIT_INSTRUCTION",
    "LATENT_HOP",
    "LATENT_HZ",
    "PASOS_POR_DEFECTO",
    "ResultadoDifusion",
    "SAMPLE_RATE",
    "SFT_GEN_PROMPT",
    "SHIFT_POR_DEFECTO",
    "SHIFT_TIMESTEPS",
    "cargar_decoder",
    "construir_programacion",
    "decodificar_latentes",
    "generar_latentes_text2music",
    "longitud_latente",
    "normalizar_latente_de_silencio",
    "preparar_condicionamiento_text2music",
    "programacion_efectiva",
    "validar_latentes",
]

#: De donde sale cada nombre publico. Se resuelve en el primer acceso.
_ORIGEN = {
    "CondicionamientoText2Music": "conditioning",
    "DEFAULT_DIT_INSTRUCTION": "constants",
    "LATENT_HOP": "constants",
    "LATENT_HZ": "constants",
    "PASOS_POR_DEFECTO": "scheduler",
    "ResultadoDifusion": "diffusion",
    "SAMPLE_RATE": "constants",
    "SFT_GEN_PROMPT": "constants",
    "SHIFT_POR_DEFECTO": "scheduler",
    "SHIFT_TIMESTEPS": "scheduler",
    # Reexportado de `vendor/oobleck_decoder.py`, NO reimplementado aqui.
    "cargar_decoder": "decode",
    "construir_programacion": "scheduler",
    "decodificar_latentes": "decode",
    "generar_latentes_text2music": "diffusion",
    "longitud_latente": "conditioning",
    "normalizar_latente_de_silencio": "conditioning",
    "preparar_condicionamiento_text2music": "conditioning",
    "programacion_efectiva": "scheduler",
    "validar_latentes": "diffusion",
}


def __getattr__(nombre: str) -> Any:
    modulo = _ORIGEN.get(nombre)
    if modulo is None:
        raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")
    from importlib import import_module

    return getattr(import_module(f".{modulo}", __name__), nombre)


def __dir__() -> list[str]:
    return sorted(__all__)
