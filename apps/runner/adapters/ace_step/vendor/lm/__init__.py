"""Planificador de 5 Hz de ACE-Step 1.5 (`acestep-5Hz-lm-0.6B`), vendorizado.

Que es esto
-----------
El tercer bloque de `vendor/`. En el directorio padre esta la **definicion del
modelo** de difusion y el decoder del VAE; en `vendor/pipeline/` esta el
**pipeline de inferencia** `text2music`; aqui esta el **planificador**: un Qwen3
de 0,6 B que, a partir del estilo y la letra, escribe los metadatos de la pieza
y despues emite una secuencia de codigos de audio a 5 Hz.

Esos codigos son lo que el DiT usa como latente de origen. Sin ellos, el latente
de origen es el latente de SILENCIO y el modelo compone a ciegas. Con ellos,
compone sobre un boceto. La diferencia entre las dos cosas es lo que este
paquete existe para poder medir.

Orden de uso
------------
1. `PlanificadorLM.cargar(ruta)` -> carga el checkpoint (local, safetensors).
2. `planificador.planificar(estilo, letra, duracion_s=30)` -> `PlanDeAudio`.
3. `hints_25Hz(model, plan.codigos)` -> `[1, N*5, 64]` para el DiT.

Y despues, en el shim, la parte que NO esta aqui y sin la cual todo lo anterior
no cambia nada: pasar esos hints con **`is_covers = True`**. Ver el docstring de
`planificador.py` y el README de este directorio.

La restriccion de longitud NO es opcional
-----------------------------------------
`decodificacion_restringida.py` es lo que hace que el numero de codigos sea
exactamente `int(duracion * 5)`. Sin el, la longitud la elige el modelo y el
contrato de duracion +-5 % de la spec deja de existir.

Procedencia, revisiones fijadas, hashes SHA-256 y estado de la revision de
seguridad: `README.md` de este directorio.

Los imports son **perezosos** (`__getattr__` de modulo, PEP 562): importar el
paquete no arrastra `torch` ni `transformers`, para que el arbol se pueda
inspeccionar en una maquina sin GPU y sin dependencias pesadas.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "CAMPOS",
    "CAMPOS_COT",
    "CAMPOS_SUFICIENTES",
    "CODIGOS_POR_SEGUNDO",
    "DEFAULT_LM_INSTRUCTION",
    "DURATION_MAX",
    "DURATION_MIN",
    "EstadoFSM",
    "MAX_AUDIO_CODE",
    "PlanDeAudio",
    "PlanificadorLM",
    "ProcesadorRestringido",
    "SIN_ENTRADA_USUARIO",
    "TAMANO_LIBRO_CODIGOS",
    "VALID_KEYSCALES",
    "VALID_LANGUAGES",
    "VALID_TIME_SIGNATURES",
    "VENTANA_AGRUPACION",
    "calcular_max_tokens_nuevos",
    "codigos_de_texto",
    "codigos_para_duracion",
    "duracion_de_codigos",
    "generar",
    "generar_con_cfg",
    "hints_25Hz",
    "indices_de_codigos",
    "limpiar_caption",
    "metadatos_a_cot",
    "parsear_salida",
    "prompt_codigos",
    "prompt_codigos_uncond",
    "prompt_cot",
    "prompt_cot_uncond",
    "resumen_rango_dinamico",
]

#: De donde sale cada nombre publico. Se resuelve en el primer acceso.
_ORIGEN = {
    "CAMPOS": "decodificacion_restringida",
    "CAMPOS_COT": "constants",
    "CAMPOS_SUFICIENTES": "planificador",
    "CODIGOS_POR_SEGUNDO": "constants",
    "DEFAULT_LM_INSTRUCTION": "constants",
    "DURATION_MAX": "constants",
    "DURATION_MIN": "constants",
    "EstadoFSM": "decodificacion_restringida",
    "MAX_AUDIO_CODE": "constants",
    "PlanDeAudio": "planificador",
    "PlanificadorLM": "planificador",
    "ProcesadorRestringido": "decodificacion_restringida",
    "SIN_ENTRADA_USUARIO": "prompt",
    "TAMANO_LIBRO_CODIGOS": "constants",
    "VALID_KEYSCALES": "constants",
    "VALID_LANGUAGES": "constants",
    "VALID_TIME_SIGNATURES": "constants",
    "VENTANA_AGRUPACION": "constants",
    "calcular_max_tokens_nuevos": "generacion",
    "codigos_de_texto": "planificador",
    "codigos_para_duracion": "constants",
    "duracion_de_codigos": "constants",
    "generar": "generacion",
    "generar_con_cfg": "generacion",
    "hints_25Hz": "planificador",
    "indices_de_codigos": "planificador",
    "limpiar_caption": "decodificacion_restringida",
    "metadatos_a_cot": "prompt",
    "parsear_salida": "prompt",
    "prompt_codigos": "prompt",
    "prompt_codigos_uncond": "prompt",
    "prompt_cot": "prompt",
    "prompt_cot_uncond": "prompt",
    "resumen_rango_dinamico": "planificador",
}


def __getattr__(nombre: str) -> Any:
    modulo = _ORIGEN.get(nombre)
    if modulo is None:
        raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")
    from importlib import import_module

    return getattr(import_module(f".{modulo}", __name__), nombre)


def __dir__() -> list[str]:
    return sorted(__all__)
