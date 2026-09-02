# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de `acestep/constants.py`.
#
#   Origen          : github.com/ace-step/ACE-Step-1.5, ruta `acestep/constants.py`
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866  (2026-08-29)
#   Bytes origen    : 8333
#   SHA-256 origen  : 7b8d4ce49649c819d1b3be87a434be2d90768308768d4620639328f906209b22
#   blob SHA-1      : 9e6df5323d7e0a2f43237a63910d55ebbf2b39e8  (verificado contra
#                     la atestacion del arbol de la API de GitHub)
#   Copiado el      : 2026-09-02
#   Licencia        : MIT (LICENSE de la raiz del repositorio, blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab, «Copyright (c)
#                     2026 ACEStep»). Copia en
#                     D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt
#
# El fichero origen NO lleva cabecera de copyright propia; se aplica la MIT del
# repositorio. Cada cambio va marcado con "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Constantes del planificador de 5 Hz de ACE-Step 1.5.

Que hay aqui y por que
----------------------
Solo lo que necesita el LM: el vocabulario cerrado de los campos de metadatos
que la decodificacion restringida obliga a respetar (idiomas, tonalidades, BPM,
duracion, compas) y la instruccion de sistema con la que se entreno.

Lo que **no** esta: los tipos de tarea, los modos de la UI, las instrucciones
por tarea y las tablas de niveles de GPU. Nada de eso lo consume el LM.

Relacion con `vendor/pipeline/constants.py`
-------------------------------------------
Los dos ficheros derivan del mismo `acestep/constants.py`, pero **no comparten
ni un solo nombre**: alli estan las constantes del DiT y del VAE
(`SAMPLE_RATE`, `LATENT_HOP`, `DEFAULT_DIT_INSTRUCTION`...), aqui las del LM.
No hay duplicacion; comprobado nombre a nombre.

La cadena de frecuencias, que es donde se pierde todo el mundo
--------------------------------------------------------------
::

    LM  -> 1 codigo cada 0,2 s          (5 Hz,  CODIGOS_POR_SEGUNDO)
    detokenizador: 1 codigo -> 5 fotogramas latentes  (VENTANA_AGRUPACION)
    DiT -> 25 fotogramas latentes por segundo         (25 Hz)
    VAE -> 1 fotograma latente -> 1920 muestras a 48 kHz

O sea: `N` codigos son exactamente `N/5` segundos de audio. Por eso la
decodificacion restringida, forzando `N = int(duracion * 5)`, es lo que cierra
el contrato de duracion; sin ella la longitud la elige el modelo.
"""

from __future__ import annotations

__all__ = [
    "BPM_MAX",
    "BPM_MIN",
    "CAMPOS_COT",
    "CODIGOS_POR_SEGUNDO",
    "DEFAULT_LM_INSTRUCTION",
    "DURATION_MAX",
    "DURATION_MIN",
    "KEYSCALE_ACCIDENTALS",
    "KEYSCALE_MODES",
    "KEYSCALE_NOTES",
    "MARGEN_TOKENS_CODIGOS",
    "MARGEN_TOKENS_COT",
    "MAX_AUDIO_CODE",
    "MAX_TOKENS_CAPTION",
    "TAMANO_LIBRO_CODIGOS",
    "VALID_KEYSCALES",
    "VALID_LANGUAGES",
    "VALID_TIME_SIGNATURES",
    "VENTANA_AGRUPACION",
    "codigos_para_duracion",
    "duracion_de_codigos",
]


# ==============================================================================
# Idiomas
# ==============================================================================

#: Idiomas admitidos para la voz. Lista cerrada: la decodificacion restringida
#: construye con ella el arbol de prefijos del campo `language`, asi que el
#: modelo no puede inventarse un codigo que luego el DiT no sepa condicionar.
VALID_LANGUAGES = [
    'ar', 'az', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 'en',
    'es', 'fa', 'fi', 'fr', 'he', 'hi', 'hr', 'ht', 'hu', 'id',
    'is', 'it', 'ja', 'ko', 'la', 'lt', 'ms', 'ne', 'nl', 'no',
    'pa', 'pl', 'pt', 'ro', 'ru', 'sa', 'sk', 'sr', 'sv', 'sw',
    'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'yue', 'zh',
    'unknown',
]


# ==============================================================================
# Tonalidad
# ==============================================================================

#: Notas en notacion occidental.
KEYSCALE_NOTES = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

#: Alteraciones: natural, sostenido/bemol ASCII y sostenido/bemol Unicode.
KEYSCALE_ACCIDENTALS = ['', '#', 'b', '\u266f', '\u266d']

#: Modos.
KEYSCALE_MODES = ['major', 'minor']

#: Las 70 combinaciones validas (7 notas x 5 alteraciones x 2 modos).
#:
#: MODIFICADO respecto a upstream: upstream lo construye con tres bucles `for`
#: sueltos a nivel de modulo, que dejan `note`, `acc` y `mode` como variables
#: publicas del modulo (`acestep.constants.note` existe y vale 'G'). Aqui se
#: construye con una comprension para no exportar basura; el conjunto resultante
#: es identico, y hay un test de igualdad en la verificacion del README.
VALID_KEYSCALES = {
    f"{nota}{alteracion} {modo}"
    for nota in KEYSCALE_NOTES
    for alteracion in KEYSCALE_ACCIDENTALS
    for modo in KEYSCALE_MODES
}


# ==============================================================================
# Rangos de los campos numericos
# ==============================================================================

#: Pulsos por minuto. 30 = balada muy lenta / ambiental; 300 = electronica
#: rapida o metal extremo.
BPM_MIN = 30
BPM_MAX = 300

#: Duracion en segundos. El tope real de una generacion concreta lo baja
#: `ProcesadorRestringido.fijar_duracion_maxima()` segun lo que quepa en la GPU
#: (en la tarjeta de 6-8 GB upstream declara `max_duration_with_lm = 480`).
DURATION_MIN = 10
DURATION_MAX = 600

#: Compases admitidos: 2/4, 3/4, 4/4 y 6/8.
VALID_TIME_SIGNATURES = [2, 3, 4, 6]


# ==============================================================================
# Instruccion de sistema
# ==============================================================================

#: Instruccion de sistema del LM. Va literal en el mensaje `system` del prompt;
#: cambiarla es cambiar la distribucion que vio el modelo al entrenarse.
DEFAULT_LM_INSTRUCTION = "Generate audio semantic tokens based on the given conditions:"


# ==============================================================================
# Numeros magicos de upstream, aqui con nombre
# ==============================================================================
# MODIFICADO respecto a upstream: los siete valores de abajo viven en upstream
# como literales repartidos entre `constrained_logits_processor.py`,
# `llm_inference.py` y `audio_codes.py` (el `5` de `duration * 5` aparece en tres
# ficheros distintos, el `63999` en dos). Tenerlos con nombre y en un solo sitio
# es lo que permite comprobarlos contra `config.json` del checkpoint del DiT en
# vez de confiar en que las tres copias sigan de acuerdo.

#: Codigos que emite el LM por segundo de audio. Upstream: `duration * 5`.
CODIGOS_POR_SEGUNDO = 5

#: Fotogramas latentes de 25 Hz que produce el detokenizador por cada codigo de
#: 5 Hz. Es `config.pool_window_size` del checkpoint del DiT (`= 5`).
VENTANA_AGRUPACION = 5

#: Entradas del libro de codigos FSQ: 8*8*8*5*5*5 = 64000, que es el producto de
#: `config.fsq_input_levels` del checkpoint del DiT.
TAMANO_LIBRO_CODIGOS = 64000

#: Codigo valido mas alto. **El vocabulario del tokenizador del LM tiene 65.535
#: tokens `<|audio_code_N|>` (N = 0..65534), es decir 1.535 MAS de los que el
#: libro de codigos admite.** Emitir uno de esos 1.535 rompe
#: `quantizer.get_output_from_indices`. Es la segunda razon, despues de la
#: duracion, por la que la lista blanca de la decodificacion restringida no es
#: opcional.
MAX_AUDIO_CODE = TAMANO_LIBRO_CODIGOS - 1

#: Tope de tokens del campo `caption` durante la fase de razonamiento.
MAX_TOKENS_CAPTION = 512

#: Margen de tokens sobre el objetivo en la fase de codigos. Basta con 10:
#: la decodificacion restringida fuerza EOS exactamente en el codigo objetivo,
#: asi que el margen solo evita que una barra de progreso mienta.
MARGEN_TOKENS_CODIGOS = 10

#: Margen de tokens en la fase de razonamiento, para los metadatos.
MARGEN_TOKENS_COT = 500

#: Orden de los campos del razonamiento. Coincide con el orden alfabetico, que
#: es justo lo que produce `yaml.dump(..., sort_keys=True)` al reserializarlo
#: para la fase 2. Que coincidan no es casualidad, pero tampoco esta escrito en
#: ningun sitio de upstream: se comprueba en la verificacion del README.
CAMPOS_COT = ("bpm", "caption", "duration", "keyscale", "language", "timesignature")


def codigos_para_duracion(duracion_s: float) -> int:
    """Numero de codigos de 5 Hz que corresponden a `duracion_s` segundos.

    Upstream: `int(duration * 5)` en `set_target_duration`. El truncado (no
    redondeo) es de upstream y se conserva: cambiarlo desplazaria el punto en el
    que se fuerza el EOS.
    """
    return int(duracion_s * CODIGOS_POR_SEGUNDO)


def duracion_de_codigos(n_codigos: int) -> float:
    """Segundos de audio que representan `n_codigos` codigos de 5 Hz.

    Inversa exacta de :func:`codigos_para_duracion` salvo por el truncado: el
    LM solo puede expresar duraciones multiplo de 0,2 s. Una peticion de 25,5 s
    sale como 25,4 s (127 codigos), un 0,4 % de error — muy dentro del +-5 % que
    exige la spec, pero conviene saberlo antes de perseguir el fantasma.
    """
    return n_codigos / CODIGOS_POR_SEGUNDO
