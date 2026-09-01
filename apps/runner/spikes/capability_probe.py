#!/usr/bin/env python3
"""Sonda empirica de capacidades - `T-07`, matriz de capacidades verificadas.

Que decide esta tarea
---------------------
`T-07` responde a una sola pregunta, con evidencia y no de oidas: **soporta
ACE-Step 1.5 las capacidades `SECTION_INPAINT`, `AUDIO_TO_AUDIO`,
`VOICE_CONDITIONING` y `CONTINUATION`?** De esa respuesta dependen C-07 y C-08
(276 h de una futura **Fase 3**, hoy **fuera de alcance y bloqueada por el gate
G3**). Esta tarea **solo deja el dato**: no planifica, no implementa la
capacidad, no mueve una hora de presupuesto. Si la matriz sale vacia, C-07/C-08
se replantean **antes** de ejecutarse - es exactamente la informacion que estas
12 h se pagaron para tener con antelacion (`evaluation.md` seccion 10.3).

La regla de honestidad (el valor entero de la tarea)
---------------------------------------------------
Hay tres veredictos, y la diferencia entre dos de ellos es todo el sentido de
este script:

* **SI** - la capacidad se invoco y el audio producido presenta el **efecto
  estructural esperado** (medido, no supuesto).
* **NO** - el **modelo** rechaza la capacidad: la pila del modelo (biblioteca de
  terceros) levanta un error que dice explicitamente que esa tarea o punto de
  entrada no existe. La traza queda guardada como evidencia y **exige lectura
  humana** antes de darla por buena.
* **NO_CONCLUYENTE** - no se pudo saber. En particular, y esto es lo importante:
  **cuando la capacidad no se puede invocar porque el adapter minimo de la Fase 0
  no expone el parametro, el veredicto es NO_CONCLUYENTE, nunca NO.**

`GenerationRequest` de la Fase 0 **no tiene** `section_edit`, ni `source_audio`,
ni `voice`: son campos diferidos a las Fases 2-4 (ver el docstring de
`contracts.py`). Por tanto la sonda intenta la invocacion por la unica via que
existe hoy, el diccionario libre `model_params`, y puede pasar que el adapter la
**acepte y la ignore en silencio**. Confundir 'el modelo no lo soporta' con
'nuestro adapter minimo aun no lo cablea' convertiria esta tarea en una fuente de
decisiones falsas: seria peor que no ejecutarla, porque C-07/C-08 se caerian (o
se aprobarian) sobre un dato inventado. De ahi que un parametro sin efecto
observable **siempre** sea NO_CONCLUYENTE, con el motivo escrito.

Metodo empirico (y sus limites, declarados)
-------------------------------------------
No se puede preguntar al modelo si soporta algo; hay que intentarlo y **medir si
la salida cambio como se esperaba**. El problema es que dos generaciones nunca
son identicas: la semilla se registra por trazabilidad pero **no** garantiza
salida identica (driver, cuDNN, kernels de atencion, orden de reduccion en coma
flotante). Ninguna comparacion de este script es bit a bit; seria intrinsecamente
inestable. En su lugar:

1. Se generan **dos controles** con la misma peticion base y sin parametro de
   capacidad. La distancia entre ambos es la **variabilidad natural** de ejecucion
   a ejecucion de este modelo en esta maquina.
2. Se genera la **sonda** con el parametro de capacidad puesto.
3. Solo si la distancia sonda-control supera la variabilidad por un factor
   (`FACTOR_EFECTO`, con un piso absoluto `PISO_EFECTO`) se concluye que el
   parametro **hizo algo**. Si no lo supera, se ignoro: NO_CONCLUYENTE.
4. Si hizo algo, se comprueba la **forma** del efecto, que es distinta por
   capacidad (prefijo preservado y duracion extendida en `CONTINUATION`; tramo
   interior regenerado y exterior preservado en `SECTION_INPAINT`; dependencia de
   la pista fuente en `AUDIO_TO_AUDIO`). Efecto sin la forma esperada tampoco es
   NO: es NO_CONCLUYENTE, porque puede ser nuestro cableado.

La metrica es un **perfil de RMS por ventana** leido del WAV con la biblioteca
estandar (`wave` + `array`; `audioop` desaparecio en Python 3.13). Es
deliberadamente tosca: sirve para detectar *presencia y localizacion* de cambio
estructural, no para juzgar musica. **La calidad musical no se decide aqui**: eso
es escucha humana y se llama G1 (`T-08`/`T-09`).

Techo de lo que el codigo puede decidir
---------------------------------------
`VOICE_CONDITIONING` **no puede** salir SI de forma automatica, y el script lo
impone. Verificar que el timbre se parece al de la referencia exige o escucha
humana ciega o un modelo de similitud de locutor, y ninguna de las dos cosas es
alcance de la Fase 0. Lo maximo que la sonda automatica puede afirmar es 'el
parametro cambio la salida'; el veredicto se queda en NO_CONCLUYENTE con
`requiere_confirmacion_humana` a `true` y la evidencia guardada para escucharla.

En modo `--mock` **ningun veredicto puede ser SI ni NO**. El mock es una
simulacion determinista: su audio es silencio y sus tiempos son inventados. El
script calcula igualmente todas las metricas -para que el recorrido quede
verificado- y luego aplica un tope explicito, dejando en el informe el veredicto
bruto y la marca `clamp_mock_aplicado`. Una simulacion no puede responder a
`T-07`; el criterio de aceptacion exige el contenedor de `T-05` sobre GPU real.

Politica de las pistas (S-11)
-----------------------------
Toda la evidencia de audio cae en una **carpeta segregada de evaluacion**, con
**retencion de 12 meses**, y **no entra en la biblioteca de trabajo ni en ninguna
produccion**. El script lo avisa por consola en cada ejecucion y lo escribe en el
informe. Las pistas fuente de las sondas son **generadas por el propio modelo**:
la sonda de `AUDIO_TO_AUDIO` nunca parte de material de terceros (habria gate de
titularidad) y la de `VOICE_CONDITIONING` nunca usa la voz de una persona real
(la clonacion de voz es **no-go vigente**, y grabar a alguien para un spike
exigiria consentimiento y base legal que esta fase no tiene).

Procedencia
-----------
Este script **no emite manifiesto de procedencia**, igual que el resto de la
Fase 0. El manifiesto v1 (`manifest_schema_version`, `lyrics_declaration`,
`source_generation`, encadenado al ledger append-only) lo aporta **T-27 en la
Fase 5 (C-10a)**, sobre el esquema **firmado por legal** (D-20). Las ~20 pistas
propias de spikes y G1 se cubren con manifiesto retroactivo simplificado (S-11).

Dependencias e imports
----------------------
El camino `--mock` funciona con **solo la biblioteca estandar**: en la maquina
donde se escribio esto no hay GPU, `nvidia-smi` no existe y `torch` no esta
instalado. Todo import de acelerador o de audio no estandar es **perezoso**
(dentro de la funcion que lo necesita) y su ausencia degrada la medicion con un
motivo escrito, nunca revienta el script.

Codigos de salida
-----------------
* `0` - informe completo escrito. **Un veredicto NO_CONCLUYENTE no es un fallo**:
  es un resultado, y de los caros de conseguir.
* `1` - informe escrito pero **incompleto** (por ejemplo, el presupuesto agregado
  de GPU de D-17 se agoto a mitad de la matriz).
* `2` - fallo operativo: no hay adapter que sondar, la VRAM no da, `health()` no
  esta listo. No se escribe matriz.

Uso
---
    python apps/runner/spikes/capability_probe.py --mock
    python apps/runner/spikes/capability_probe.py --capability continuation --keep-audio
    python apps/runner/spikes/capability_probe.py --out ruta/evidencias --duration 30
"""

from __future__ import annotations

import argparse
import array
import asyncio
import importlib.util
import platform
import shutil
import sys
import traceback
import wave
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Sequence

# --------------------------------------------------------------------------- #
# Arranque de sys.path
# --------------------------------------------------------------------------- #
# Los spikes se ejecutan como scripts sueltos: no hay paquete instalable ni
# __init__.py, porque el empaquetado del monorepo es T-10 y esta detras del gate
# G1. Se anade `apps/runner/` (para `contracts`) y el propio directorio de
# spikes (para `_timing` y `_mock`), de forma robusta al directorio de trabajo.
_AQUI = Path(__file__).resolve()
_SPIKES_DIR = _AQUI.parent                      # apps/runner/spikes
_RUNNER_ROOT = _AQUI.parents[1]                 # apps/runner
_RAIZ_PROYECTO = _AQUI.parents[3]               # raiz del arbol de trabajo
for _ruta in (str(_RUNNER_ROOT), str(_SPIKES_DIR)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import _timing  # noqa: E402  (tras el arranque de sys.path)
from _mock import MockMusicModelAdapter, make_request  # noqa: E402
from contracts import (  # noqa: E402
    AudioArtifact,
    GenerationRequest,
    GenerationResult,
    GpuBudgetExceeded,
    ModelCapability,
    MusicModelAdapter,
    RunnerContext,
    assert_within_gpu_budget,
)

# --------------------------------------------------------------------------- #
# Constantes de metodo
# --------------------------------------------------------------------------- #

#: Ventana del perfil de RMS, en segundos. 0,5 s localiza un tramo de inpaint con
#: suficiente resolucion sin convertir el perfil en una serie inmanejable.
VENTANA_S = 0.5

#: Un efecto se acepta como real si la distancia sonda-control supera la
#: variabilidad control-control por este factor. Con solo dos controles la
#: estimacion de variabilidad es debil: el factor es holgado a proposito, y el
#: informe lo declara como limite del metodo.
FACTOR_EFECTO = 3.0

#: Piso absoluto de distancia relativa (2 %) para no llamar 'efecto' al ruido
#: numerico cuando los dos controles salen casi identicos.
PISO_EFECTO = 0.02

#: Margen exigido en `AUDIO_TO_AUDIO`: la salida debe parecerse a la pista fuente
#: bastante mas que una generacion independiente, no un poco mas.
MARGEN_DEPENDENCIA_FUENTE = 0.6

#: Tolerancia de duracion, la misma de C-01 (+/-5 %).
TOLERANCIA_DURACION = 0.05

#: Segundos que se piden de extension en la sonda de `CONTINUATION`.
EXTENSION_S = 15

#: Duracion por defecto de las pistas de sonda. Cortas a proposito: `T-07`
#: verifica capacidad, no calidad de cancion completa (eso es G1), y cada WAV de
#: 44,1 kHz estereo de 16 bit pesa ~10,6 MB por minuto.
DURACION_POR_DEFECTO_S = 30

#: Modulos 'propios': una excepcion nacida aqui habla de NUESTRO cableado, no del
#: modelo, y por tanto nunca puede sostener un veredicto NO.
_MODULOS_PROPIOS = frozenset(
    {"contracts", "_mock", "_timing", "capability_probe", "__main__", "builtins", "asyncio"}
)

#: Marcadores de mensaje con los que la pila del modelo declara que una tarea o
#: punto de entrada no existe. Solo se usan sobre excepciones de terceros, y solo
#: como indicio: el veredicto NO siempre queda marcado para confirmacion humana.
_MARCADORES_NO_SOPORTADO = (
    "not supported",
    "unsupported",
    "not implemented",
    "notimplemented",
    "unknown task",
    "invalid task",
    "no such task",
    "unrecognized",
    "unexpected keyword",
    "has no attribute",
)

POLITICA_S11 = (
    "S-11: las pistas de spikes y del gate G1 viven en una CARPETA SEGREGADA DE "
    "EVALUACION, con RETENCION DE 12 MESES. No entran en la biblioteca de trabajo "
    "ni en ninguna produccion. Las propias llevan manifiesto retroactivo "
    "simplificado; el manifiesto v1 completo lo aporta T-27 en la Fase 5 sobre el "
    "esquema firmado por legal (D-20)."
)


class Veredicto(StrEnum):
    """Los tres unicos veredictos posibles de la matriz de `T-07`."""

    SI = "SI"
    NO = "NO"
    NO_CONCLUYENTE = "NO_CONCLUYENTE"


# --------------------------------------------------------------------------- #
# Definicion de las cuatro sondas
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True, kw_only=True)
class Sonda:
    """Descripcion declarativa de una sonda de capacidad.

    Args:
        capability: capacidad del vocabulario de `ModelCapability` que se prueba.
        titulo: nombre legible para la tabla del documento de `T-07`.
        pregunta: que se quiere saber, en una frase.
        invocacion: como se intenta invocar, incluido el punto de entrada que se
            usaria si el campo canonico existiera.
        campo_canonico: campo de `GenerationRequest` que transportaria esta
            capacidad en el contrato definitivo. En la Fase 0 no existe: se
            comprueba en tiempo de ejecucion y se documenta en el informe.
        fase_destino: quien consume el dato (tarea y caracteristica).
        tope_automatico: veredicto maximo que la sonda automatica puede emitir.
            `NO_CONCLUYENTE` para lo que solo se puede juzgar escuchando.
        forma_esperada: descripcion del efecto estructural que se busca medir.
    """

    capability: ModelCapability
    titulo: str
    pregunta: str
    invocacion: str
    campo_canonico: str
    fase_destino: str
    tope_automatico: Veredicto
    forma_esperada: str


SONDAS: tuple[Sonda, ...] = (
    Sonda(
        capability=ModelCapability.SECTION_INPAINT,
        titulo="Regeneracion de un tramo (inpaint de seccion)",
        pregunta=(
            "Puede ACE-Step regenerar solo el tramo [t0, t1] de una pista "
            "existente, conservando el resto?"
        ),
        invocacion=(
            "model_params['section_edit'] = {source_audio, start_s, end_s, prompt, "
            "mode='inpaint'} sobre la pista base generada por el propio modelo. En "
            "el contrato definitivo esto viajaria en GenerationRequest.section_edit."
        ),
        campo_canonico="section_edit",
        fase_destino="C-07 (Fase 3, bloqueada por G3) - T-70/T-71",
        tope_automatico=Veredicto.SI,
        forma_esperada=(
            "El perfil de RMS fuera de la ventana [t0, t1] se conserva respecto a la "
            "pista base y dentro de la ventana cambia de forma material."
        ),
    ),
    Sonda(
        capability=ModelCapability.AUDIO_TO_AUDIO,
        titulo="Cover / remezcla sobre audio de entrada",
        pregunta=(
            "Puede ACE-Step tomar una pista como entrada y producir una version "
            "condicionada por ella, en vez de generar desde cero?"
        ),
        invocacion=(
            "model_params['source_audio'] = {path, duration_s} con task='audio_to_audio' "
            "y strength. En el contrato definitivo viajaria en "
            "GenerationRequest.source_audio (AudioRef)."
        ),
        campo_canonico="source_audio",
        fase_destino="C-08 (Fase 3, bloqueada por G3) - T-77",
        tope_automatico=Veredicto.SI,
        forma_esperada=(
            "La salida se parece a la pista fuente bastante mas que una generacion "
            "independiente con el mismo prompt, y respeta su duracion."
        ),
    ),
    Sonda(
        capability=ModelCapability.VOICE_CONDITIONING,
        titulo="Condicionamiento de timbre vocal",
        pregunta=(
            "Puede ACE-Step condicionar el timbre o registro vocal a partir de una "
            "referencia sintetica y de etiquetas?"
        ),
        invocacion=(
            "model_params['voice'] = {reference_audio (SINTETICA, generada por el "
            "propio modelo), kind='synthetic_reference', tags}. En el contrato "
            "definitivo viajaria en GenerationRequest.voice (VoiceSpec)."
        ),
        campo_canonico="voice",
        fase_destino=(
            "C-03 (presets de voz por etiquetas / audio sintetico). La clonacion de "
            "voz de la Fase 4 es NO-GO vigente y esta sonda no la prueba."
        ),
        tope_automatico=Veredicto.NO_CONCLUYENTE,
        forma_esperada=(
            "El parametro cambia la salida. La semejanza de TIMBRE no es verificable "
            "por codigo en la Fase 0: exige escucha humana ciega (protocolo de G1) o "
            "un modelo de similitud de locutor, ninguno de los dos en alcance."
        ),
    ),
    Sonda(
        capability=ModelCapability.CONTINUATION,
        titulo="Continuacion / extension de una pista",
        pregunta=(
            "Puede ACE-Step extender una pista existente por su final, conservando "
            "lo ya generado?"
        ),
        invocacion=(
            "model_params['source_audio'] + task='continuation' + extend_s, con "
            "duration_s = duracion de la base + extend_s. En el contrato definitivo "
            "viajaria en GenerationRequest.source_audio con derivation_kind de "
            "continuacion (D-22)."
        ),
        campo_canonico="source_audio",
        fase_destino="C-07 (Fase 3, bloqueada por G3) - T-71",
        tope_automatico=Veredicto.SI,
        forma_esperada=(
            f"La duracion crece ~{EXTENSION_S} s (tolerancia +/-"
            f"{int(TOLERANCIA_DURACION * 100)} %) y el prefijo correspondiente a la "
            "pista base se conserva."
        ),
    ),
)

SONDAS_POR_CLAVE: dict[str, Sonda] = {str(s.capability): s for s in SONDAS}


# --------------------------------------------------------------------------- #
# Medicion de audio (biblioteca estandar; `soundfile` opcional y perezoso)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True, kw_only=True)
class Medida:
    """Medida de un artefacto de audio: duracion real y perfil de energia."""

    etiqueta: str
    ruta: str | None
    formato: str
    duracion_declarada_s: float
    duracion_medida_s: float | None
    perfil: tuple[float, ...] | None
    motivo_perfil: str
    silencioso: bool

    def as_dict(self) -> dict[str, Any]:
        """Version serializable. El perfil completo NO se vuelca al informe.

        Un perfil de 0,5 s sobre una pista de 3 min son 360 numeros por pista y
        siete pistas por ejecucion: llenaria el informe de ruido sin aportar nada
        que la distancia agregada no diga ya. Se vuelca su tamano y su nivel medio.
        """
        return {
            "etiqueta": self.etiqueta,
            "ruta": self.ruta,
            "formato": self.formato,
            "duracion_declarada_s": round(self.duracion_declarada_s, 3),
            "duracion_medida_s": (
                None if self.duracion_medida_s is None else round(self.duracion_medida_s, 3)
            ),
            "ventanas_perfil": None if self.perfil is None else len(self.perfil),
            "nivel_medio_rms": (
                None
                if not self.perfil
                else round(sum(self.perfil) / len(self.perfil), 6)
            ),
            "perfil_silencioso": self.silencioso,
            "motivo_perfil": self.motivo_perfil,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class Comparacion:
    """Distancia relativa entre dos perfiles de energia.

    `informativa` es `False` cuando la distancia existe pero no dice nada (por
    ejemplo, dos perfiles de silencio dan 0,0 y eso no significa 'iguales por
    decision del modelo'). Distinguirlo es lo que evita leer el modo mock como
    una medicion.
    """

    valor: float | None
    nota: str
    informativa: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "valor": None if self.valor is None else round(self.valor, 6),
            "informativa": self.informativa,
            "nota": self.nota,
        }


def _perfil_rms_wav(ruta: Path, ventana_s: float) -> tuple[tuple[float, ...], str]:
    """Perfil de RMS por ventana de un WAV PCM de 16 bit, con `wave` + `array`.

    Se lee por bloques para no cargar en memoria una pista entera. `audioop`
    desaparecio en Python 3.13 (PEP 594), asi que el RMS se calcula a mano sobre
    un `array('h')`, con `byteswap()` si la maquina no es little-endian (el WAV
    siempre lo es).

    Devuelve `(perfil, motivo)`. El perfil puede ser vacio si el fichero no tiene
    marcos.
    """
    with wave.open(str(ruta), "rb") as wav:
        canales = wav.getnchannels()
        ancho = wav.getsampwidth()
        tasa = wav.getframerate()
        marcos_totales = wav.getnframes()
        if ancho != 2:
            return ((), f"WAV de {ancho * 8} bit: el lector estandar de este spike solo trata PCM de 16 bit.")
        if tasa <= 0 or canales <= 0:
            return ((), "Cabecera WAV incoherente (tasa o canales no positivos).")

        marcos_por_ventana = max(int(tasa * ventana_s), 1)
        perfil: list[float] = []
        leidos = 0
        while leidos < marcos_totales:
            pedir = min(marcos_por_ventana, marcos_totales - leidos)
            crudo = wav.readframes(pedir)
            if not crudo:
                break
            muestras = array.array("h")
            # frombytes exige multiplo del tamano de item: se recorta cualquier
            # cola incompleta en lugar de reventar.
            utiles = len(crudo) - (len(crudo) % muestras.itemsize)
            muestras.frombytes(crudo[:utiles])
            if sys.byteorder != "little":
                muestras.byteswap()
            if muestras:
                suma = 0.0
                for m in muestras:
                    suma += float(m) * float(m)
                perfil.append((suma / len(muestras)) ** 0.5 / 32768.0)
            leidos += pedir
        return (tuple(perfil), f"Perfil de RMS por ventanas de {ventana_s} s leido con 'wave' (estandar).")


def _perfil_rms_soundfile(ruta: Path, ventana_s: float) -> tuple[tuple[float, ...], str] | None:
    """Intento **opcional y perezoso** de leer FLAC/MP3 con `soundfile`.

    El adapter real de la Fase 1 entrega FLAC + MP3 320 (D-09), formatos que la
    biblioteca estandar no decodifica. Si `soundfile` esta instalado (ver
    `requirements.txt`), se usa; si no, se devuelve `None` y el informe declara la
    limitacion en lugar de fingir una medida. El import va **dentro** de la
    funcion: en la maquina de desarrollo no hay ni torch ni soundfile.
    """
    try:
        import soundfile  # noqa: PLC0415  (perezoso a proposito)
    except Exception:
        return None
    try:
        with soundfile.SoundFile(str(ruta)) as f:
            tasa = int(f.samplerate)
            marcos_por_ventana = max(int(tasa * ventana_s), 1)
            perfil: list[float] = []
            while True:
                bloque = f.read(frames=marcos_por_ventana, dtype="float32", always_2d=True)
                if len(bloque) == 0:
                    break
                suma = 0.0
                n = 0
                for marco in bloque:
                    for muestra in marco:
                        suma += float(muestra) * float(muestra)
                        n += 1
                if n:
                    perfil.append((suma / n) ** 0.5)
        return (tuple(perfil), f"Perfil de RMS por ventanas de {ventana_s} s leido con 'soundfile'.")
    except Exception as exc:  # pragma: no cover - depende de la instalacion real
        return ((), f"'soundfile' presente pero fallo al leer {ruta.name}: {exc!r}.")


def medir_artefacto(art: AudioArtifact, etiqueta: str, ventana_s: float) -> Medida:
    """Mide duracion real y perfil de energia de un artefacto ya materializado.

    Nunca lanza: un fichero ilegible es una limitacion documentada del informe,
    no un fallo del spike. La duracion **medida** puede diferir de la
    **declarada**; verlo es util (la tolerancia de C-01 es +/-5 %).
    """
    if art.path is None:
        return Medida(
            etiqueta=etiqueta,
            ruta=None,
            formato=art.format,
            duracion_declarada_s=art.duration_s,
            duracion_medida_s=None,
            perfil=None,
            motivo_perfil=(
                "El artefacto viaja como bytes en memoria, sin ruta: no hay fichero "
                "que medir ni evidencia que archivar (S-11 exige fichero)."
            ),
            silencioso=False,
        )

    ruta = Path(art.path)
    if not ruta.is_file():
        return Medida(
            etiqueta=etiqueta,
            ruta=str(ruta),
            formato=art.format,
            duracion_declarada_s=art.duration_s,
            duracion_medida_s=None,
            perfil=None,
            motivo_perfil=f"La ruta declarada no existe en disco: {ruta}.",
            silencioso=False,
        )

    perfil: tuple[float, ...] | None = None
    motivo = ""
    duracion_medida: float | None = None

    if art.format == "wav":
        try:
            with wave.open(str(ruta), "rb") as wav:
                tasa = wav.getframerate()
                duracion_medida = wav.getnframes() / tasa if tasa else None
            perfil, motivo = _perfil_rms_wav(ruta, ventana_s)
        except Exception as exc:
            perfil, motivo = None, f"WAV ilegible ({exc!r}): sin perfil de energia."
    else:
        resultado = _perfil_rms_soundfile(ruta, ventana_s)
        if resultado is None:
            motivo = (
                f"Artefacto '{art.format}': la biblioteca estandar no lo decodifica y "
                "'soundfile' no esta instalado. Sin perfil de energia: el veredicto se "
                "apoyara solo en duracion, excepciones y escucha humana. Instala "
                "'soundfile' (ver requirements.txt) para habilitar la comparacion."
            )
        else:
            perfil, motivo = resultado
            try:
                import soundfile  # noqa: PLC0415  (perezoso; solo para la duracion)

                with soundfile.SoundFile(str(ruta)) as f:
                    duracion_medida = len(f) / float(f.samplerate) if f.samplerate else None
            except Exception:
                duracion_medida = None

    silencioso = bool(perfil) and max(perfil) <= 1e-9
    if silencioso:
        motivo = (
            f"{motivo} PERFIL EN SILENCIO ABSOLUTO: cualquier comparacion sobre el es "
            "no informativa (caso normal del adapter mock, que escribe silencio)."
        )
    if perfil is not None and not perfil:
        perfil = None
        motivo = f"{motivo} Perfil vacio: no se pudo derivar energia del fichero."

    return Medida(
        etiqueta=etiqueta,
        ruta=str(ruta),
        formato=art.format,
        duracion_declarada_s=art.duration_s,
        duracion_medida_s=duracion_medida,
        perfil=perfil,
        motivo_perfil=motivo.strip(),
        silencioso=silencioso,
    )


def _rebanada(
    perfil: Sequence[float], desde_s: float, hasta_s: float, ventana_s: float
) -> tuple[float, ...]:
    """Tramo del perfil correspondiente al intervalo `[desde_s, hasta_s)`."""
    i0 = max(int(desde_s / ventana_s), 0)
    i1 = min(int(hasta_s / ventana_s), len(perfil))
    return tuple(perfil[i0:i1])


def comparar(
    a: Sequence[float] | None,
    b: Sequence[float] | None,
    *,
    contexto: str = "",
) -> Comparacion:
    """Distancia relativa media entre dos perfiles de energia.

    Se alinean al minimo de longitudes (dos generaciones de distinta duracion son
    comparables en su parte comun) y se normaliza por el nivel medio de ambos,
    para que la cifra no dependa de la ganancia absoluta.

    **Nunca compara bit a bit**: la difusion en GPU no garantiza salida identica
    ni con la misma semilla, asi que un `assert` de igualdad exacta seria inestable
    por construccion.
    """
    if a is None or b is None:
        return Comparacion(
            valor=None,
            nota=f"Sin perfil en uno de los dos lados{f' ({contexto})' if contexto else ''}.",
            informativa=False,
        )
    n = min(len(a), len(b))
    if n == 0:
        return Comparacion(valor=None, nota="Perfiles vacios.", informativa=False)
    diferencia = sum(abs(float(a[i]) - float(b[i])) for i in range(n)) / n
    nivel = (sum(float(x) for x in a[:n]) + sum(float(x) for x in b[:n])) / (2 * n)
    if nivel <= 1e-9:
        return Comparacion(
            valor=0.0,
            nota=(
                "Ambos perfiles estan en silencio: la distancia sale 0,0 pero NO "
                "significa que el modelo haya decidido nada. Metrica no informativa."
            ),
            informativa=False,
        )
    return Comparacion(
        valor=diferencia / nivel,
        nota=f"Distancia relativa media sobre {n} ventanas de {VENTANA_S} s.",
        informativa=True,
    )


# --------------------------------------------------------------------------- #
# Construccion del adapter (mock o real, con import perezoso)
# --------------------------------------------------------------------------- #

def _ruta_adapter_real(personalizada: str | None) -> Path:
    """Ruta del adapter real de `T-05`."""
    if personalizada:
        return Path(personalizada).expanduser().resolve()
    return _RUNNER_ROOT / "adapters" / "ace_step" / "adapter.py"


def _instanciar(constructor: Any, dir_audio: Path) -> tuple[Any, str]:
    """Instancia el adapter pasandole `output_dir` si lo acepta.

    Se intenta primero con `output_dir=<carpeta segregada>` para que el audio de
    evidencia se escriba directamente donde manda S-11, en lugar de viajar en
    memoria y tener que volcarlo despues. Si el constructor no acepta ese
    argumento, se cae a la llamada sin argumentos: `T-07` no impone la firma de
    `T-05`, solo la aprovecha si esta.
    """
    try:
        return constructor(output_dir=dir_audio), "con output_dir"
    except TypeError:
        return constructor(), "sin argumentos"


def cargar_adapter_real(ruta: Path, dir_audio: Path) -> tuple[Any, dict[str, Any]]:
    """Carga el adapter de ACE-Step de `T-05` por ruta de fichero, sin paquete.

    Se usa `importlib` sobre la ruta porque en la Fase 0 no hay paquete instalable
    (eso es `T-10`, detras de G1) y porque asi el import de `torch` que el adapter
    haga ocurre **dentro** de esta funcion: el modo `--mock` nunca lo toca.

    El modulo se **registra en `sys.modules` antes de ejecutarlo**. No es
    cosmetico: `@dataclass(slots=True)` resuelve las anotaciones de su propia clase
    a traves de `sys.modules[cls.__module__].__dict__`, asi que un modulo cargado
    por ruta y no registrado revienta con `AttributeError: 'NoneType' object has no
    attribute '__dict__'` en cuanto define un dataclass con `slots`. El adapter de
    `T-05` los usa, de modo que sin este registro `T-07` no podria cargarlo. Si la
    ejecucion falla, la entrada se retira para no dejar un modulo a medias.

    El adapter debe ofrecer, por este orden, una de estas dos cosas: una fabrica
    `build_adapter()` / `crear_adapter()`, o una clase que implemente
    `contracts.MusicModelAdapter` (se prueban primero los nombres `AceStepAdapter`
    y `Adapter`). Si no ofrece ninguna, se aborta diciendo exactamente que se
    busco: `T-07` no puede sondar lo que no puede instanciar.

    Levanta:
        FileNotFoundError: si `T-05` aun no ha entregado el adapter.
        RuntimeError: si el modulo carga pero no expone un adapter utilizable.
    """
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No existe el adapter de ACE-Step en {ruta}. T-07 depende de T-05 "
            "(contenerizacion minima de ACE-Step 1.5): sin ese contenedor no hay "
            "modelo que sondar. Ejecuta con --mock para verificar el recorrido del "
            "script, sabiendo que un mock NO puede responder a T-07."
        )

    nombre_modulo = "ace_step_adapter_t05"
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo preparar el import de {ruta}.")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre_modulo] = modulo
    try:
        spec.loader.exec_module(modulo)
    except Exception:
        sys.modules.pop(nombre_modulo, None)
        raise

    for nombre in ("build_adapter", "crear_adapter"):
        fabrica = getattr(modulo, nombre, None)
        if callable(fabrica):
            adapter, como = _instanciar(fabrica, dir_audio)
            return adapter, {
                "fuente": "gpu",
                "origen": str(ruta),
                "punto_de_entrada": f"{nombre}() {como}",
            }

    candidatos = ["AceStepAdapter", "Adapter"]
    for nombre in candidatos:
        clase = getattr(modulo, nombre, None)
        if isinstance(clase, type):
            adapter, como = _instanciar(clase, dir_audio)
            return adapter, {
                "fuente": "gpu",
                "origen": str(ruta),
                "punto_de_entrada": f"{nombre} {como}",
            }

    for nombre, obj in vars(modulo).items():
        if nombre.startswith("_") or not isinstance(obj, type):
            continue
        try:
            if issubclass(obj, MusicModelAdapter):
                adapter, como = _instanciar(obj, dir_audio)
                return adapter, {
                    "fuente": "gpu",
                    "origen": str(ruta),
                    "punto_de_entrada": f"{nombre} {como} (detectado por Protocol)",
                }
        except TypeError:
            continue

    raise RuntimeError(
        f"{ruta} carga, pero no expone adapter utilizable. Se busco: build_adapter(), "
        f"crear_adapter(), las clases {candidatos}, y cualquier clase que implemente "
        "contracts.MusicModelAdapter. Anade una de las dos fabricas en T-05."
    )


def metadatos_adapter(adapter: Any, extra: dict[str, Any]) -> dict[str, Any]:
    """Cabecera del informe con la identidad del adapter sondado.

    Se acepta `describe()` (lo trae el adapter de `T-05`) o `report_metadata()` (lo
    trae el mock de spikes). Los dos devuelven una cabecera con la clave `source`
    (`"gpu"` o `"mock"`), y esa marca es precisamente lo que impide leer una
    simulacion como medicion de `T-07`. Si el adapter ofrece `probe()`, se recoge
    tambien: es diagnostico de hardware sin cargar pesos.
    """
    base: dict[str, Any] = {}
    for nombre in ("describe", "report_metadata"):
        metodo = getattr(adapter, nombre, None)
        if callable(metodo):
            try:
                base.update(dict(metodo()))
            except Exception as exc:  # pragma: no cover - adapter de terceros
                base[f"{nombre}_error"] = repr(exc)
            break
    diagnostico = getattr(adapter, "probe", None)
    if callable(diagnostico):
        try:
            base["probe"] = dict(diagnostico())
        except Exception as exc:  # pragma: no cover - adapter de terceros
            base["probe_error"] = repr(exc)
    if getattr(adapter, "backend", None) is not None:
        base["backend"] = str(adapter.backend)
        base["backend_reason"] = str(getattr(adapter, "backend_reason", ""))
    base.setdefault("model_id", str(getattr(adapter, "MODEL_ID", type(adapter).__name__)))
    base.setdefault("model_version", str(getattr(adapter, "MODEL_VERSION", "desconocida")))
    declaradas = getattr(adapter, "CAPABILITIES", None)
    base["capacidades_declaradas"] = (
        sorted(str(c) for c in declaradas) if declaradas is not None else None
    )
    base["implementa_protocolo_MusicModelAdapter"] = isinstance(adapter, MusicModelAdapter)
    base.update(extra)
    return base


# --------------------------------------------------------------------------- #
# Materializacion de evidencia
# --------------------------------------------------------------------------- #

def materializar(art: AudioArtifact, dir_audio: Path, etiqueta: str) -> AudioArtifact:
    """Deja el artefacto como fichero **dentro** de la carpeta de evidencias.

    Tres casos: ya esta dentro (no se toca), esta fuera (se copia, porque S-11
    exige que la evidencia viva junta en la carpeta segregada) o viaja en memoria
    (se escribe). Devuelve un artefacto equivalente con la ruta final.
    """
    dir_audio.mkdir(parents=True, exist_ok=True)

    if art.path is not None:
        origen = Path(art.path)
        try:
            dentro = origen.resolve().is_relative_to(dir_audio.resolve())
        except OSError:  # pragma: no cover - rutas raras del sistema
            dentro = False
        if dentro or not origen.is_file():
            return art
        destino = dir_audio / f"{etiqueta}{origen.suffix}"
        shutil.copy2(origen, destino)
        return AudioArtifact(
            format=art.format,
            sample_rate=art.sample_rate,
            channels=art.channels,
            duration_s=art.duration_s,
            size_bytes=destino.stat().st_size,
            path=str(destino),
        )

    destino = dir_audio / f"{etiqueta}.{art.format}"
    destino.write_bytes(art.data or b"")
    return AudioArtifact(
        format=art.format,
        sample_rate=art.sample_rate,
        channels=art.channels,
        duration_s=art.duration_s,
        size_bytes=destino.stat().st_size,
        path=str(destino),
    )


# --------------------------------------------------------------------------- #
# Ejecucion de generaciones con presupuesto agregado (D-17)
# --------------------------------------------------------------------------- #

@dataclass(slots=True)
class Presupuesto:
    """Contador agregado de segundos de GPU de toda la ejecucion (D-17).

    El adapter ya aplica `max_gpu_seconds` **por trabajo**; esto es el tope
    **global** de la sonda: seis o siete generaciones seguidas pueden salir caras
    aunque ninguna se pase por si sola. Al agotarse, las sondas restantes se
    marcan como no ejecutadas y el informe se escribe igualmente: un resultado
    parcial honesto vale mas que ninguno.

    Contrato M-3: `RunTelemetry.gpu_seconds` de cada generacion ya NO incluye el
    coste del arranque, asi que este contador lo suma **una sola vez** via
    `registrar_carga()` (leido del `load_gpu_seconds` que reporta el adapter),
    en lugar de arrastrarlo repetido en cada `registrar()`.
    """

    total_max_s: int
    consumido_s: float = 0.0
    carga_s: float | None = None

    def registrar_carga(self, load_gpu_seconds: float) -> None:
        """Suma el coste de GPU del ARRANQUE (vram_load + warmup) una sola vez.

        Idempotente: una segunda llamada se ignora, que es justo lo que evita la
        doble contabilidad que corrige M-3.
        """
        if self.carga_s is not None:
            return
        self.carga_s = float(load_gpu_seconds)
        self.consumido_s += self.carga_s
        assert_within_gpu_budget(
            self.consumido_s,
            self.total_max_s,
            detail=(
                "Presupuesto AGREGADO de la sonda de capacidades (T-07) agotado ya "
                "con el coste del arranque. Se aborta la matriz y se escribe "
                "informe parcial."
            ),
        )

    def registrar(self, gpu_seconds: float) -> None:
        """Suma los `gpu_seconds` de UNA generacion (solo su inferencia, M-3)."""
        self.consumido_s += float(gpu_seconds)
        assert_within_gpu_budget(
            self.consumido_s,
            self.total_max_s,
            detail=(
                "Presupuesto AGREGADO de la sonda de capacidades (T-07), no de un "
                "trabajo suelto. Se aborta la matriz y se escribe informe parcial."
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_gpu_seconds_agregado": self.total_max_s,
            "gpu_seconds_consumidos": round(self.consumido_s, 3),
            # Coste del arranque, registrado UNA vez (M-3); None si no llego a
            # registrarse (fallo antes de cargar).
            "load_gpu_seconds": None if self.carga_s is None else round(self.carga_s, 3),
        }


@dataclass(slots=True)
class Generacion:
    """Una generacion ejecutada: peticion, artefacto medido y telemetria."""

    etiqueta: str
    request: GenerationRequest
    medida: Medida | None
    telemetria: dict[str, Any]
    excepcion: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return self.excepcion is None and self.medida is not None


def _resumen_request(req: GenerationRequest) -> dict[str, Any]:
    """Peticion en forma serializable, con `model_params` incluido.

    `model_params` es la via por la que se cuelan los parametros de capacidad, asi
    que verlo en el informe es lo que permite reproducir la sonda.
    """
    return {
        "style_prompt": req.style_prompt,
        "duration_s": req.duration_s,
        "max_gpu_seconds": req.max_gpu_seconds,
        "idempotency_key": req.idempotency_key,
        "tiene_lyrics": req.lyrics is not None,
        "instrumental": req.instrumental,
        "seed": req.seed,
        "model_params": req.model_params,
    }


def _clasificar_excepcion(exc: BaseException) -> dict[str, Any]:
    """Decide si una excepcion habla del **modelo** o de **nuestro cableado**.

    Es la pieza que separa un NO legitimo de un NO_CONCLUYENTE:

    * excepcion de un modulo propio (`contracts`, `_mock`, este script) -> jamas
      sostiene un NO: es nuestra validacion, no el modelo;
    * excepcion de una biblioteca de terceros cuyo mensaje declara que la tarea o
      el argumento no existen -> indicio de NO, **marcado para confirmacion
      humana** (hay que leer la traza antes de tumbar 276 h de Fase 3);
    * cualquier otra -> NO_CONCLUYENTE (fallo de entorno, OOM, timeout...).
    """
    modulo = type(exc).__module__.split(".")[0]
    propia = modulo in _MODULOS_PROPIOS
    mensaje = str(exc).lower()
    marcadores = [m for m in _MARCADORES_NO_SOPORTADO if m in mensaje]
    return {
        "tipo": type(exc).__name__,
        "modulo": type(exc).__module__,
        "origen": "propio" if propia else "terceros",
        "mensaje": str(exc)[:600],
        "marcadores_de_no_soportado": marcadores,
        "sostiene_veredicto_no": bool(marcadores) and not propia,
        "traza": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
    }


async def generar(
    adapter: Any,
    req: GenerationRequest,
    *,
    etiqueta: str,
    dir_audio: Path,
    ventana_s: float,
    presupuesto: Presupuesto,
    registro: list[Generacion] | None = None,
) -> Generacion:
    """Ejecuta una generacion, materializa la evidencia y la mide.

    Captura cualquier excepcion del adapter y la clasifica: en esta sonda un fallo
    **es** un dato (puede ser la respuesta 'el modelo no soporta esto'), no un
    motivo para abortar. La unica excepcion que se propaga es
    `GpuBudgetExceeded` del presupuesto **agregado**, que si detiene la matriz.

    Toda generacion se anade a `registro` **antes** de comprobar el presupuesto
    agregado, para que el informe liste las seis o siete ejecuciones que de verdad
    consumieron GPU. Si solo se registraran las que terminan bien, el apartado
    `generaciones` del informe contradiria a `presupuesto_gpu` y el rastro de
    auditoria dejaria de cuadrar.
    """
    def _cerrar(gen: Generacion) -> Generacion:
        if registro is not None:
            registro.append(gen)
        return gen

    try:
        resultado: GenerationResult = await adapter.generate(req)
    except GpuBudgetExceeded as exc:
        # D-17 por trabajo: es un dato de la sonda, no una parada global.
        return _cerrar(
            Generacion(
                etiqueta=etiqueta,
                request=req,
                medida=None,
                telemetria={},
                excepcion=_clasificar_excepcion(exc),
            )
        )
    except Exception as exc:
        return _cerrar(
            Generacion(
                etiqueta=etiqueta,
                request=req,
                medida=None,
                telemetria={},
                excepcion=_clasificar_excepcion(exc),
            )
        )

    telemetria = {
        "gpu_seconds": resultado.telemetry.gpu_seconds,
        "vram_peak_mb": resultado.telemetry.vram_peak_mb,
        "offloading_enabled": resultado.telemetry.offloading_enabled,
        "retries": resultado.telemetry.retries,
        "stage_timings_s": dict(resultado.telemetry.stage_timings),
    }
    if not resultado.artifacts:
        return _cerrar(
            Generacion(
                etiqueta=etiqueta,
                request=req,
                medida=None,
                telemetria=telemetria,
                excepcion={
                    "tipo": "SinArtefacto",
                    "modulo": "capability_probe",
                    "origen": "propio",
                    "mensaje": "El adapter devolvio GenerationResult sin artefactos.",
                    "marcadores_de_no_soportado": [],
                    "sostiene_veredicto_no": False,
                    "traza": "",
                },
            )
        )

    art = materializar(resultado.artifacts[0], dir_audio, etiqueta)
    medida = medir_artefacto(art, etiqueta, ventana_s)
    gen = _cerrar(
        Generacion(
            etiqueta=etiqueta,
            request=req,
            medida=medida,
            telemetria=telemetria,
            excepcion=None,
        )
    )
    # El presupuesto agregado se comprueba DESPUES de tener la evidencia en disco y
    # la generacion en el registro: si salta aqui, la pista ya esta archivada y el
    # informe parcial la lista.
    presupuesto.registrar(resultado.telemetry.gpu_seconds)
    return gen


# --------------------------------------------------------------------------- #
# Parametros de capacidad y comprobacion estructural
# --------------------------------------------------------------------------- #

def params_de_sonda(sonda: Sonda, fuente: Medida, duracion_base_s: float) -> dict[str, Any]:
    """Construye el `model_params` con el que se intenta invocar la capacidad.

    Los nombres de clave imitan los campos del contrato definitivo
    (`section_edit`, `source_audio`, `voice`) para que, cuando esos campos existan
    de verdad (Fases 2-3), la sonda se traduzca de forma obvia. Hoy viajan por
    `model_params` porque es el **unico** canal libre de la peticion de Fase 0.
    """
    ref_fuente = {"path": fuente.ruta, "duration_s": round(duracion_base_s, 3)}

    if sonda.capability is ModelCapability.SECTION_INPAINT:
        t0 = round(duracion_base_s / 3.0, 3)
        t1 = round(2.0 * duracion_base_s / 3.0, 3)
        return {
            "task": "inpaint",
            "section_edit": {
                "source_audio": ref_fuente,
                "start_s": t0,
                "end_s": t1,
                "prompt": "solo instrumental de guitarra en el tramo seleccionado",
                "mode": "inpaint",
            },
        }

    if sonda.capability is ModelCapability.AUDIO_TO_AUDIO:
        return {
            "task": "audio_to_audio",
            "source_audio": ref_fuente,
            "strength": 0.6,
            # La fuente es una pista generada por el propio modelo: nunca material
            # de terceros. Un cover sobre obra ajena exige gate de titularidad, y
            # ese gate no es alcance de un spike.
            "source_is_own_generation": True,
        }

    if sonda.capability is ModelCapability.VOICE_CONDITIONING:
        return {
            "task": "voice_conditioning",
            "voice": {
                # Referencia SINTETICA generada por el propio modelo. Nunca la voz
                # de una persona real: la clonacion de voz es no-go vigente y
                # grabar a alguien para un spike exigiria consentimiento y base
                # legal que esta fase no tiene.
                "reference_audio": ref_fuente,
                "kind": "synthetic_reference",
                "tags": ["voz femenina", "registro medio", "timbre calido"],
            },
        }

    if sonda.capability is ModelCapability.CONTINUATION:
        return {
            "task": "continuation",
            "source_audio": ref_fuente,
            "continue_from_s": round(duracion_base_s, 3),
            "extend_s": EXTENSION_S,
        }

    raise ValueError(f"Sonda sin parametros definidos: {sonda.capability}.")  # pragma: no cover


def _duracion_pedida(sonda: Sonda, duracion_base_s: float) -> int:
    """Duracion que se pide en la sonda. Solo `CONTINUATION` cambia la duracion."""
    if sonda.capability is ModelCapability.CONTINUATION:
        return int(round(duracion_base_s + EXTENSION_S))
    return int(round(duracion_base_s))


def _dentro_de_tolerancia(valor: float, esperado: float, tolerancia: float) -> bool:
    """`True` si `valor` esta dentro de `esperado` +/- `tolerancia` relativa."""
    if esperado <= 0:
        return False
    return abs(valor - esperado) / esperado <= tolerancia


def comprobar_forma(
    sonda: Sonda,
    *,
    sonda_medida: Medida,
    fuente: Medida,
    control: Medida | None,
    umbral: float,
    duracion_base_s: float,
    ventana_s: float,
) -> tuple[bool | None, str, dict[str, Any]]:
    """Comprueba si el efecto observado tiene la **forma** que la capacidad exige.

    Devuelve `(cumple, motivo, metricas)`. `cumple=None` significa 'no se pudo
    comprobar' (por ejemplo, sin perfiles): eso lleva a NO_CONCLUYENTE, nunca a
    NO. Ninguna comprobacion compara audio bit a bit.

    `control` puede ser `None` (el control B fallo): las comprobaciones que lo
    necesitan (AUDIO_TO_AUDIO) se marcan como no aplicables en vez de comparar
    la sonda consigo misma, que seria un autocotejo sin valor.
    """
    metricas: dict[str, Any] = {}

    if sonda.capability is ModelCapability.CONTINUATION:
        esperada = duracion_base_s + EXTENSION_S
        medida = sonda_medida.duracion_medida_s
        metricas["duracion_esperada_s"] = round(esperada, 3)
        metricas["duracion_medida_s"] = None if medida is None else round(medida, 3)
        if medida is None:
            return (None, "Sin duracion medible en la salida: no se puede verificar la extension.", metricas)
        if not _dentro_de_tolerancia(medida, esperada, TOLERANCIA_DURACION):
            return (
                False,
                (
                    f"La salida dura {medida:.1f} s y una continuacion de la base "
                    f"({duracion_base_s:.1f} s) + {EXTENSION_S} s deberia durar "
                    f"~{esperada:.1f} s (+/-{int(TOLERANCIA_DURACION * 100)} %). El "
                    "parametro cambio algo, pero no extendio la pista."
                ),
                metricas,
            )
        if sonda_medida.perfil is None or fuente.perfil is None:
            return (None, "Sin perfiles de energia: no se puede verificar si el prefijo se conserva.", metricas)
        prefijo_sonda = _rebanada(sonda_medida.perfil, 0.0, duracion_base_s, ventana_s)
        cmp_prefijo = comparar(prefijo_sonda, fuente.perfil, contexto="prefijo vs pista base")
        metricas["distancia_prefijo_vs_base"] = cmp_prefijo.as_dict()
        metricas["umbral_efecto"] = round(umbral, 6)
        if not cmp_prefijo.informativa or cmp_prefijo.valor is None:
            return (None, f"Comparacion del prefijo no informativa: {cmp_prefijo.nota}", metricas)
        if cmp_prefijo.valor <= umbral:
            return (
                True,
                (
                    f"Duracion extendida a {medida:.1f} s y prefijo conservado "
                    f"(distancia {cmp_prefijo.valor:.3f} <= umbral {umbral:.3f}): la "
                    "salida continua la pista base en lugar de regenerarla."
                ),
                metricas,
            )
        return (
            False,
            (
                f"Duracion correcta pero el prefijo NO se conserva (distancia "
                f"{cmp_prefijo.valor:.3f} > umbral {umbral:.3f}): parece una "
                "generacion nueva mas larga, no una continuacion."
            ),
            metricas,
        )

    if sonda.capability is ModelCapability.SECTION_INPAINT:
        if sonda_medida.perfil is None or fuente.perfil is None:
            return (None, "Sin perfiles de energia: no se puede localizar el tramo regenerado.", metricas)
        t0 = duracion_base_s / 3.0
        t1 = 2.0 * duracion_base_s / 3.0
        dentro = comparar(
            _rebanada(sonda_medida.perfil, t0, t1, ventana_s),
            _rebanada(fuente.perfil, t0, t1, ventana_s),
            contexto="tramo interior",
        )
        antes = comparar(
            _rebanada(sonda_medida.perfil, 0.0, t0, ventana_s),
            _rebanada(fuente.perfil, 0.0, t0, ventana_s),
            contexto="tramo previo",
        )
        despues = comparar(
            _rebanada(sonda_medida.perfil, t1, duracion_base_s, ventana_s),
            _rebanada(fuente.perfil, t1, duracion_base_s, ventana_s),
            contexto="tramo posterior",
        )
        metricas.update(
            {
                "ventana_editada_s": [round(t0, 3), round(t1, 3)],
                "distancia_dentro_de_ventana": dentro.as_dict(),
                "distancia_antes_de_ventana": antes.as_dict(),
                "distancia_despues_de_ventana": despues.as_dict(),
                "umbral_efecto": round(umbral, 6),
            }
        )
        if not (dentro.informativa and antes.informativa and despues.informativa):
            return (None, "Alguna comparacion por tramos no es informativa: sin veredicto de forma.", metricas)
        fuera_conservado = max(antes.valor or 0.0, despues.valor or 0.0) <= umbral
        dentro_cambiado = (dentro.valor or 0.0) > umbral
        if fuera_conservado and dentro_cambiado:
            return (
                True,
                (
                    f"El tramo [{t0:.1f}, {t1:.1f}] s cambia (distancia "
                    f"{dentro.valor:.3f} > {umbral:.3f}) y el resto se conserva: "
                    "edicion localizada, que es lo que exige SECTION_INPAINT."
                ),
                metricas,
            )
        if dentro_cambiado and not fuera_conservado:
            return (
                False,
                (
                    "Cambia el tramo pedido, pero tambien el resto de la pista: el "
                    "adapter regenero la cancion completa en vez de editar una "
                    "seccion. No es inpaint."
                ),
                metricas,
            )
        return (
            False,
            (
                f"El tramo pedido no cambia mas que el resto (dentro "
                f"{dentro.valor:.3f} frente a umbral {umbral:.3f}): el parametro tuvo "
                "efecto, pero no localizado en la ventana."
            ),
            metricas,
        )

    if sonda.capability is ModelCapability.AUDIO_TO_AUDIO:
        if control is None:
            # Sin control independiente, la unica comparacion posible seria la
            # sonda contra si misma: distancia 0,0 garantizada y "dependencia de
            # la fuente" inventada. Se marca no aplicable y el veredicto queda
            # NO_CONCLUYENTE (cumple=None), nunca un SI/NO fabricado.
            metricas["distancia_control_vs_fuente"] = Comparacion(
                valor=None,
                nota=(
                    "Sin pista de control utilizable: la comparacion control-fuente "
                    "no es aplicable y no se sustituye por un autocotejo de la sonda."
                ),
                informativa=False,
            ).as_dict()
            return (
                None,
                "Sin control independiente no se puede medir la dependencia de la fuente.",
                metricas,
            )
        if sonda_medida.perfil is None or fuente.perfil is None or control.perfil is None:
            return (None, "Sin perfiles de energia: no se puede medir dependencia de la fuente.", metricas)
        d_sonda = comparar(sonda_medida.perfil, fuente.perfil, contexto="sonda vs fuente")
        d_control = comparar(control.perfil, fuente.perfil, contexto="control vs fuente")
        metricas["distancia_sonda_vs_fuente"] = d_sonda.as_dict()
        metricas["distancia_control_vs_fuente"] = d_control.as_dict()
        metricas["margen_exigido"] = MARGEN_DEPENDENCIA_FUENTE
        duracion = sonda_medida.duracion_medida_s
        metricas["duracion_medida_s"] = None if duracion is None else round(duracion, 3)
        if not (d_sonda.informativa and d_control.informativa):
            return (None, "Comparaciones con la fuente no informativas: sin veredicto de forma.", metricas)
        if duracion is not None and not _dentro_de_tolerancia(
            duracion, duracion_base_s, TOLERANCIA_DURACION
        ):
            return (
                False,
                (
                    f"La salida dura {duracion:.1f} s frente a los {duracion_base_s:.1f} s "
                    "de la fuente: no respeta la pista de entrada."
                ),
                metricas,
            )
        if (d_sonda.valor or 0.0) < (d_control.valor or 0.0) * MARGEN_DEPENDENCIA_FUENTE:
            return (
                True,
                (
                    f"La salida se parece a la fuente mucho mas que una generacion "
                    f"independiente ({d_sonda.valor:.3f} frente a {d_control.valor:.3f}): "
                    "esta condicionada por el audio de entrada."
                ),
                metricas,
            )
        return (
            False,
            (
                f"La salida no se parece a la fuente mas que el control "
                f"({d_sonda.valor:.3f} frente a {d_control.valor:.3f}): el parametro "
                "cambio algo, pero no condiciono la generacion con la pista de entrada."
            ),
            metricas,
        )

    if sonda.capability is ModelCapability.VOICE_CONDITIONING:
        # Tope automatico: aqui no hay forma estructural que medir. El timbre es
        # perceptual y su verificacion es humana (protocolo de G1) o exige un
        # modelo de similitud de locutor, fuera de alcance de la Fase 0.
        return (
            None,
            (
                "El parametro tuvo efecto observable, pero la semejanza de TIMBRE no "
                "es verificable por codigo en la Fase 0. Queda evidencia de audio para "
                "escucha humana ciega; el veredicto automatico no puede pasar de "
                "NO_CONCLUYENTE."
            ),
            metricas,
        )

    return (None, "Capacidad sin comprobacion de forma definida.", metricas)  # pragma: no cover


# --------------------------------------------------------------------------- #
# Ejecucion de una sonda
# --------------------------------------------------------------------------- #

@dataclass(slots=True)
class ResultadoSonda:
    """Fila de la matriz de `T-07`."""

    sonda: Sonda
    veredicto: Veredicto
    veredicto_bruto: Veredicto
    motivo: str
    motivos_extra: list[str]
    efecto: bool | None
    metricas: dict[str, Any]
    evidencia: list[str]
    excepcion: dict[str, Any] | None
    declarada_por_el_adapter: bool | None
    canal: str
    campo_canonico_presente: bool
    requiere_confirmacion_humana: bool
    clamp_mock_aplicado: bool
    request: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "capacidad": str(self.sonda.capability),
            "titulo": self.sonda.titulo,
            "pregunta": self.sonda.pregunta,
            "veredicto": str(self.veredicto),
            "veredicto_bruto": str(self.veredicto_bruto),
            "clamp_mock_aplicado": self.clamp_mock_aplicado,
            "motivo": self.motivo,
            "motivos_extra": self.motivos_extra,
            "efecto_observado": self.efecto,
            "invocacion_intentada": self.sonda.invocacion,
            "canal_de_invocacion": self.canal,
            "campo_canonico": self.sonda.campo_canonico,
            "campo_canonico_presente_en_GenerationRequest": self.campo_canonico_presente,
            "forma_esperada": self.sonda.forma_esperada,
            "capacidad_declarada_por_el_adapter": self.declarada_por_el_adapter,
            "requiere_confirmacion_humana": self.requiere_confirmacion_humana,
            "consume_este_dato": self.sonda.fase_destino,
            "veredicto_automatico_maximo": str(self.sonda.tope_automatico),
            "metricas": self.metricas,
            "evidencia_audio": self.evidencia,
            "excepcion": self.excepcion,
            "peticion": self.request,
        }


async def ejecutar_sonda(
    adapter: Any,
    sonda: Sonda,
    *,
    fuente: Generacion,
    control: Generacion,
    variabilidad: Comparacion,
    cfg: argparse.Namespace,
    dir_audio: Path,
    presupuesto: Presupuesto,
    modo: str,
    declaradas: Sequence[str] | None,
    registro: list[Generacion],
) -> ResultadoSonda:
    """Intenta invocar una capacidad y emite su veredicto con el motivo escrito.

    El orden de decision es deliberado y no se puede reordenar sin romper la regla
    de honestidad:

    1. **Excepcion** -> se clasifica. Solo una excepcion de terceros que declare
       que la tarea no existe sostiene NO; el resto es NO_CONCLUYENTE.
    2. **Sin efecto observable** -> NO_CONCLUYENTE: el parametro se acepto y se
       ignoro, y no se puede distinguir 'el modelo no lo soporta' de 'el adapter
       minimo de Fase 0 no lo cablea'.
    3. **Con efecto** -> se comprueba la forma. Forma correcta -> SI; forma
       distinta o no comprobable -> NO_CONCLUYENTE.
    4. **Topes**: `VOICE_CONDITIONING` nunca llega a SI automaticamente, y en modo
       mock ningun veredicto puede ser SI ni NO.
    """
    motivos_extra: list[str] = []
    campos_request = {f.name for f in fields(GenerationRequest)}
    campo_presente = sonda.campo_canonico in campos_request
    canal = (
        f"GenerationRequest.{sonda.campo_canonico}"
        if campo_presente
        else "model_params (via de escape: el campo canonico no existe en la Fase 0)"
    )
    if not campo_presente:
        motivos_extra.append(
            f"GenerationRequest de la Fase 0 no tiene el campo '{sonda.campo_canonico}' "
            f"(diferido: {sonda.fase_destino}). La invocacion se intenta por "
            "model_params, que el adapter puede ignorar en silencio."
        )

    declarada = None if declaradas is None else str(sonda.capability) in declaradas
    if declarada is False:
        motivos_extra.append(
            "El adapter no declara esta capacidad. Es informativo, NO el veredicto: "
            "T-07 existe precisamente para no fiarse de la declaracion."
        )

    duracion_base_s = float(cfg.duration)
    if fuente.medida is None:
        return ResultadoSonda(
            sonda=sonda,
            veredicto=Veredicto.NO_CONCLUYENTE,
            veredicto_bruto=Veredicto.NO_CONCLUYENTE,
            motivo=(
                "No hay pista fuente utilizable: sin ella no se puede intentar la "
                "invocacion. Fallo de entorno, no respuesta del modelo."
            ),
            motivos_extra=motivos_extra,
            efecto=None,
            metricas={},
            evidencia=[],
            excepcion=fuente.excepcion,
            declarada_por_el_adapter=declarada,
            canal=canal,
            campo_canonico_presente=campo_presente,
            requiere_confirmacion_humana=True,
            clamp_mock_aplicado=False,
            request=None,
        )

    params = params_de_sonda(sonda, fuente.medida, duracion_base_s)
    etiqueta = f"sonda-{str(sonda.capability).replace('_', '-')}"
    req = make_request(
        style_prompt=cfg.style_prompt,
        duration_s=_duracion_pedida(sonda, duracion_base_s),
        max_gpu_seconds=cfg.max_gpu_seconds,
        idempotency_key=f"t07-{etiqueta}",
        lyrics=None,
        instrumental=True,
        seed=cfg.seed,
        model_params=params,
    )

    gen = await generar(
        adapter,
        req,
        etiqueta=etiqueta,
        dir_audio=dir_audio,
        ventana_s=cfg.ventana,
        presupuesto=presupuesto,
        registro=registro,
    )

    evidencia = [m.ruta for m in (fuente.medida, gen.medida) if m is not None and m.ruta]
    metricas: dict[str, Any] = {"variabilidad_control": variabilidad.as_dict()}

    # --- 1. La invocacion fallo ------------------------------------------- #
    if gen.excepcion is not None:
        exc = gen.excepcion
        if exc["sostiene_veredicto_no"]:
            veredicto = Veredicto.NO
            motivo = (
                f"La pila del modelo ({exc['modulo']}) rechaza la invocacion: "
                f"{exc['tipo']}: {exc['mensaje']}. El mensaje declara que la tarea o "
                f"el argumento no existen (marcadores: {', '.join(exc['marcadores_de_no_soportado'])}). "
                "LEER LA TRAZA antes de dar el NO por definitivo."
            )
        else:
            veredicto = Veredicto.NO_CONCLUYENTE
            origen = (
                "nuestro propio codigo (validacion del adapter minimo o del contrato)"
                if exc["origen"] == "propio"
                else "una biblioteca de terceros, pero sin declarar que la capacidad no exista"
            )
            motivo = (
                f"La invocacion fallo con {exc['tipo']}: {exc['mensaje']}. La excepcion "
                f"viene de {origen}, asi que NO puede leerse como 'el modelo no lo "
                "soporta': no se distingue de 'nuestro adapter minimo aun no lo expone'."
            )
        return _con_topes(
            sonda=sonda,
            veredicto=veredicto,
            motivo=motivo,
            motivos_extra=motivos_extra,
            efecto=None,
            metricas=metricas,
            evidencia=evidencia,
            excepcion=exc,
            declarada=declarada,
            canal=canal,
            campo_presente=campo_presente,
            modo=modo,
            request=_resumen_request(req),
            requiere_humano=True,
        )

    if gen.medida is None:
        # No deberia ocurrir (sin excepcion, `generar` siempre devuelve medida),
        # pero un `assert` en su lugar desapareceria con python -O y dejaria la
        # rama silenciosa. Un fallo de medicion es NO_CONCLUYENTE, nunca NO.
        return _con_topes(
            sonda=sonda,
            veredicto=Veredicto.NO_CONCLUYENTE,
            motivo=(
                "La generacion de la sonda no dejo artefacto medible pese a no lanzar "
                "excepcion: fallo de entorno, no respuesta del modelo."
            ),
            motivos_extra=motivos_extra,
            efecto=None,
            metricas=metricas,
            evidencia=evidencia,
            excepcion=None,
            declarada=declarada,
            canal=canal,
            campo_presente=campo_presente,
            modo=modo,
            request=_resumen_request(req),
            requiere_humano=True,
        )

    control_medida = control.medida
    cmp_sonda_control = comparar(
        gen.medida.perfil,
        control_medida.perfil if control_medida else None,
        contexto="sonda vs control",
    )
    umbral = max((variabilidad.valor or 0.0) * FACTOR_EFECTO, PISO_EFECTO)
    metricas.update(
        {
            "distancia_sonda_vs_control": cmp_sonda_control.as_dict(),
            "umbral_efecto": round(umbral, 6),
            "factor_efecto": FACTOR_EFECTO,
            "piso_efecto": PISO_EFECTO,
            "artefacto_sonda": gen.medida.as_dict(),
            "telemetria": gen.telemetria,
        }
    )

    # --- 2. El parametro no hizo nada observable -------------------------- #
    if not cmp_sonda_control.informativa or cmp_sonda_control.valor is None:
        return _con_topes(
            sonda=sonda,
            veredicto=Veredicto.NO_CONCLUYENTE,
            motivo=(
                "No se pudo medir si el parametro tuvo efecto: "
                f"{cmp_sonda_control.nota} Sin medida no hay veredicto, y desde luego "
                "no un NO."
            ),
            motivos_extra=motivos_extra,
            efecto=None,
            metricas=metricas,
            evidencia=evidencia,
            excepcion=None,
            declarada=declarada,
            canal=canal,
            campo_presente=campo_presente,
            modo=modo,
            request=_resumen_request(req),
            requiere_humano=True,
        )

    if cmp_sonda_control.valor <= umbral:
        return _con_topes(
            sonda=sonda,
            veredicto=Veredicto.NO_CONCLUYENTE,
            motivo=(
                f"El adapter ACEPTO el parametro y lo IGNORO: la salida se aparta del "
                f"control {cmp_sonda_control.valor:.3f}, dentro de la variabilidad "
                f"natural entre dos ejecuciones (umbral {umbral:.3f}). Esto NO es un "
                "NO: no se puede distinguir 'el modelo no soporta la capacidad' de "
                "'nuestro adapter minimo de Fase 0 no cablea el parametro al "
                "pipeline'. Para concluir, T-05 debe reenviar model_params al modelo "
                "o exponer su punto de entrada de tareas, y repetir esta sonda."
            ),
            motivos_extra=motivos_extra,
            efecto=False,
            metricas=metricas,
            evidencia=evidencia,
            excepcion=None,
            declarada=declarada,
            canal=canal,
            campo_presente=campo_presente,
            modo=modo,
            request=_resumen_request(req),
            requiere_humano=False,
        )

    # --- 3. Hubo efecto: se comprueba la forma ---------------------------- #
    cumple, motivo_forma, metricas_forma = comprobar_forma(
        sonda,
        sonda_medida=gen.medida,
        fuente=fuente.medida,
        # Sin control B utilizable se pasa None: comprobar_forma marca la
        # comparacion como no aplicable en vez de autocotejar la sonda (menor 8).
        control=control_medida,
        umbral=umbral,
        duracion_base_s=duracion_base_s,
        ventana_s=cfg.ventana,
    )
    metricas["forma"] = metricas_forma

    if cumple is True:
        veredicto = Veredicto.SI
        motivo = (
            f"Invocada por {canal} con efecto medible (distancia "
            f"{cmp_sonda_control.valor:.3f} > umbral {umbral:.3f}) y con la forma "
            f"esperada. {motivo_forma}"
        )
        requiere_humano = False
    elif cumple is False:
        veredicto = Veredicto.NO_CONCLUYENTE
        motivo = (
            f"El parametro SI tuvo efecto (distancia {cmp_sonda_control.valor:.3f} > "
            f"umbral {umbral:.3f}), pero no con la forma que la capacidad exige. "
            f"{motivo_forma} Puede ser del modelo o de nuestro cableado: no se emite "
            "NO sin poder separar las dos cosas."
        )
        requiere_humano = True
    else:
        veredicto = Veredicto.NO_CONCLUYENTE
        motivo = (
            f"El parametro tuvo efecto (distancia {cmp_sonda_control.valor:.3f} > "
            f"umbral {umbral:.3f}), pero la forma no se pudo comprobar. {motivo_forma}"
        )
        requiere_humano = True

    return _con_topes(
        sonda=sonda,
        veredicto=veredicto,
        motivo=motivo,
        motivos_extra=motivos_extra,
        efecto=True,
        metricas=metricas,
        evidencia=evidencia,
        excepcion=None,
        declarada=declarada,
        canal=canal,
        campo_presente=campo_presente,
        modo=modo,
        request=_resumen_request(req),
        requiere_humano=requiere_humano,
    )


def _con_topes(
    *,
    sonda: Sonda,
    veredicto: Veredicto,
    motivo: str,
    motivos_extra: list[str],
    efecto: bool | None,
    metricas: dict[str, Any],
    evidencia: list[str],
    excepcion: dict[str, Any] | None,
    declarada: bool | None,
    canal: str,
    campo_presente: bool,
    modo: str,
    request: dict[str, Any] | None,
    requiere_humano: bool,
) -> ResultadoSonda:
    """Aplica los dos topes de honestidad y construye la fila de la matriz.

    * **Tope por capacidad**: lo que solo se puede juzgar escuchando no llega a SI
      (`Sonda.tope_automatico`).
    * **Tope de mock**: una simulacion no responde a `T-07`, asi que ni SI ni NO.

    El veredicto **bruto** se conserva en el informe: asi se ve que la maquinaria
    de medida se ejecuto de verdad y que lo unico que la frena es una regla
    declarada, no un fallo silencioso.
    """
    bruto = veredicto
    extra = list(motivos_extra)
    clamp_mock = False

    if veredicto is Veredicto.SI and sonda.tope_automatico is not Veredicto.SI:
        veredicto = Veredicto.NO_CONCLUYENTE
        requiere_humano = True
        extra.append(
            "TOPE DE LA SONDA: esta capacidad no admite veredicto SI automatico. "
            "Verificarla exige escucha humana ciega (protocolo de G1) o un modelo de "
            "similitud, fuera del alcance de la Fase 0."
        )

    if modo == "mock" and veredicto in (Veredicto.SI, Veredicto.NO):
        veredicto = Veredicto.NO_CONCLUYENTE
        clamp_mock = True
        requiere_humano = True
        extra.append(
            "TOPE DE MOCK: en modo --mock ningun veredicto puede ser SI ni NO. El mock "
            "es una simulacion determinista que escribe silencio; el criterio de "
            "aceptacion de T-07 exige el contenedor de T-05 sobre GPU real. Se "
            f"conserva el veredicto bruto ({bruto}) para ver que la medida se ejecuto."
        )

    return ResultadoSonda(
        sonda=sonda,
        veredicto=veredicto,
        veredicto_bruto=bruto,
        motivo=motivo,
        motivos_extra=extra,
        efecto=efecto,
        metricas=metricas,
        evidencia=evidencia,
        excepcion=excepcion,
        declarada_por_el_adapter=declarada,
        canal=canal,
        campo_canonico_presente=campo_presente,
        requiere_confirmacion_humana=requiere_humano,
        clamp_mock_aplicado=clamp_mock,
        request=request,
    )


def sonda_no_ejecutada(sonda: Sonda, motivo: str) -> ResultadoSonda:
    """Fila para una capacidad que no se llego a probar (presupuesto agotado)."""
    return ResultadoSonda(
        sonda=sonda,
        veredicto=Veredicto.NO_CONCLUYENTE,
        veredicto_bruto=Veredicto.NO_CONCLUYENTE,
        motivo=motivo,
        motivos_extra=["Sonda no ejecutada: la matriz esta incompleta."],
        efecto=None,
        metricas={},
        evidencia=[],
        excepcion=None,
        declarada_por_el_adapter=None,
        canal="no intentado",
        campo_canonico_presente=sonda.campo_canonico in {f.name for f in fields(GenerationRequest)},
        requiere_confirmacion_humana=True,
        clamp_mock_aplicado=False,
        request=None,
    )


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #

def _recorta(texto: str, ancho: int = 150) -> str:
    """Recorta un motivo para la tabla de consola; el completo va en el JSON."""
    limpio = " ".join(texto.split())
    return limpio if len(limpio) <= ancho else limpio[: ancho - 3].rstrip() + "..."


def tabla_markdown(resultados: Sequence[ResultadoSonda]) -> str:
    """Tabla en castellano lista para copiar al documento de `T-07`.

    Sale en Markdown porque su destino es
    `docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/matriz-capacidades.md`,
    que es donde `T-07` deja el dato para una futura Fase 3.
    """
    lineas = [
        "| Capacidad | Veredicto | Canal intentado | Efecto observado | Motivo | Evidencia |",
        "|---|---|---|---|---|---|",
    ]
    for r in resultados:
        efecto = {True: "si", False: "no (parametro ignorado)", None: "no medible"}[r.efecto]
        canal = "campo canonico" if r.campo_canonico_presente else "model_params (via de escape)"
        evidencia = ", ".join(Path(p).name for p in r.evidencia) or "-"
        marca = " (requiere confirmacion humana)" if r.requiere_confirmacion_humana else ""
        lineas.append(
            f"| `{r.sonda.capability}` | **{r.veredicto}**{marca} | {canal} | {efecto} "
            f"| {_recorta(r.motivo)} | {evidencia} |"
        )
    return "\n".join(lineas)


def construir_informe(
    *,
    cfg: argparse.Namespace,
    modo: str,
    meta_adapter: dict[str, Any],
    entorno: dict[str, Any],
    generaciones: Sequence[Generacion],
    variabilidad: Comparacion,
    resultados: Sequence[ResultadoSonda],
    presupuesto: Presupuesto,
    completa: bool,
    audio_conservado: bool,
    motivo_audio: str,
) -> dict[str, Any]:
    """Payload JSON de la matriz de capacidades."""
    return {
        "tarea": "T-07",
        "titulo": "Matriz de capacidades verificadas (ACE-Step 1.5)",
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modo": modo,
        "matriz_completa": completa,
        "aviso_principal": (
            "MODO MOCK: simulacion determinista, NO una medicion. Ningun veredicto "
            "puede ser SI ni NO; el criterio de aceptacion de T-07 exige el contenedor "
            "de T-05 sobre GPU real."
            if modo == "mock"
            else "Medicion contra el adapter real de T-05. Los veredictos NO exigen "
            "lectura humana de la traza antes de darse por definitivos."
        ),
        "que_decide_este_dato": (
            "C-07 y C-08 (276 h de una futura Fase 3, hoy fuera de alcance y bloqueada "
            "por el gate G3). T-07 solo deja el dato: no planifica ni implementa nada. "
            "T-70/T-71 y T-77 comprueban esta matriz VERIFICADA, no el descriptor "
            "declarado del modelo."
        ),
        "adapter": meta_adapter,
        "entorno": entorno,
        "metodo": {
            "descripcion": (
                "Se generan dos controles con la misma peticion y sin parametro de "
                "capacidad; su distancia es la variabilidad natural de ejecucion a "
                "ejecucion. Un parametro se considera efectivo solo si su salida se "
                "aparta del control mas de FACTOR_EFECTO veces esa variabilidad (con "
                "piso PISO_EFECTO). Despues se comprueba la FORMA del efecto, distinta "
                "por capacidad."
            ),
            "metrica": (
                f"Perfil de RMS por ventanas de {cfg.ventana} s leido con la biblioteca "
                "estandar. Tosca a proposito: detecta presencia y localizacion de "
                "cambio estructural, no juzga musica."
            ),
            "factor_efecto": FACTOR_EFECTO,
            "piso_efecto": PISO_EFECTO,
            "tolerancia_duracion": TOLERANCIA_DURACION,
            "margen_dependencia_fuente": MARGEN_DEPENDENCIA_FUENTE,
            "variabilidad_control": variabilidad.as_dict(),
            "nunca_bit_a_bit": (
                "Ninguna comparacion es bit a bit: la semilla se registra por "
                "trazabilidad y NO garantiza salida identica (driver, cuDNN, kernels de "
                "atencion, orden de reduccion en coma flotante). Un assert de igualdad "
                "exacta seria inestable por construccion."
            ),
        },
        "limites_del_metodo": [
            "La variabilidad se estima con solo 2 controles: es una cota debil. Con "
            "presupuesto de GPU para mas controles, la discriminacion mejora.",
            "El perfil de RMS no distingue timbre, armonia ni letra: puede haber "
            "capacidades soportadas cuyo efecto no aparezca en la envolvente de "
            "energia. Un NO_CONCLUYENTE nunca debe leerse como NO.",
            "VOICE_CONDITIONING no admite veredicto SI automatico: exige escucha humana "
            "ciega o un modelo de similitud de locutor, fuera de alcance de la Fase 0.",
            "La calidad musical no se evalua aqui en absoluto: eso es G1 (T-08/T-09), "
            "escucha humana con protocolo numerico.",
        ],
        "presupuesto_gpu": presupuesto.as_dict(),
        "generaciones": [
            {
                "etiqueta": g.etiqueta,
                "peticion": _resumen_request(g.request),
                "artefacto": None if g.medida is None else g.medida.as_dict(),
                "telemetria": g.telemetria,
                "excepcion": g.excepcion,
            }
            for g in generaciones
        ],
        "matriz": [r.as_dict() for r in resultados],
        "tabla_markdown": tabla_markdown(resultados),
        "recomendaciones": _recomendaciones(resultados, modo),
        "politica_de_pistas_S11": POLITICA_S11,
        "evidencia": {
            "carpeta": str(Path(cfg.out).resolve()),
            "audio_conservado": audio_conservado,
            "motivo": motivo_audio,
            "retencion_meses": 12,
        },
        "procedencia": (
            "Este informe NO es un manifiesto de procedencia. El manifiesto v1 "
            "(manifest_schema_version, lyrics_declaration, source_generation, "
            "encadenado al ledger append-only) lo aporta T-27 en la Fase 5 (C-10a), "
            "sobre el esquema firmado por legal (D-20). Las pistas propias de spikes y "
            "G1 se cubren con manifiesto retroactivo simplificado (S-11)."
        ),
        "cobertura_de_criterios_de_T-07": {
            "cada_capacidad_probada_con_evidencia": (
                "Lo cubre este script: una sonda por capacidad, con fichero de audio "
                "archivado y motivo escrito. En modo mock la evidencia es silencio y no "
                "vale como prueba."
            ),
            "matriz_documentada_y_enlazada": (
                "Lo cubre la persona en "
                "docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/matriz-capacidades.md, "
                "pegando 'tabla_markdown' y enlazando este JSON."
            ),
        },
    }


def _recomendaciones(resultados: Sequence[ResultadoSonda], modo: str) -> list[str]:
    """Acciones concretas que se derivan de la matriz, sin planificar nada."""
    recomendaciones: list[str] = []
    if modo == "mock":
        recomendaciones.append(
            "Repetir esta ejecucion contra el contenedor de T-05 en GPU real: en modo "
            "mock la matriz no cierra ningun criterio de aceptacion de T-07."
        )
    ignorados = [r for r in resultados if r.efecto is False]
    if ignorados:
        recomendaciones.append(
            "El adapter acepto y descarto los parametros de "
            + ", ".join(str(r.sonda.capability) for r in ignorados)
            + ". Para obtener un veredicto concluyente, el adapter de T-05 debe "
            "reenviar model_params al pipeline (passthrough) o exponer su punto de "
            "entrada de tareas, y repetir la sonda. Mientras eso no ocurra, la "
            "respuesta correcta es NO_CONCLUYENTE, no NO."
        )
    negativos = [r for r in resultados if r.veredicto is Veredicto.NO]
    if negativos:
        recomendaciones.append(
            "Antes de dar por cerrado un NO ("
            + ", ".join(str(r.sonda.capability) for r in negativos)
            + "), leer la traza guardada en el campo 'excepcion': un NO de esta matriz "
            "puede tumbar caracteristicas de la Fase 3 (C-07/C-08, 276 h), y esa "
            "decision no se delega en una heuristica de mensajes de error."
        )
    afirmativos = [r for r in resultados if r.veredicto is Veredicto.SI]
    if afirmativos:
        recomendaciones.append(
            "Escuchar la evidencia de "
            + ", ".join(str(r.sonda.capability) for r in afirmativos)
            + " antes de anotar el SI en el documento: el efecto estructural esta "
            "medido, pero que el resultado sea musicalmente utilizable es juicio "
            "humano (mismo criterio que G1)."
        )
    recomendaciones.append(
        "Enlazar este JSON desde spikes/matriz-capacidades.md y dejarlo como entrada de "
        "decision de C-07/C-08. No planificar Fase 3 desde aqui: sigue bloqueada por G3."
    )
    return recomendaciones


def imprimir_informe(payload: dict[str, Any], ruta_json: Path, resultados: Sequence[ResultadoSonda]) -> None:
    """Salida de consola en castellano, con la tabla lista para copiar."""
    print()
    print("=" * 78)
    print("T-07 - MATRIZ DE CAPACIDADES VERIFICADAS - ACE-Step 1.5")
    print("=" * 78)
    print(f"Modo             : {payload['modo']}")
    print(f"Adapter          : {payload['adapter'].get('model_id')}@{payload['adapter'].get('model_version')}")
    print(f"Fecha (UTC)      : {payload['fecha_utc']}")
    print(f"GPU detectada    : {payload['entorno'].get('gpu') or 'ninguna (sin torch/CUDA)'}")
    print(f"Offloading       : {payload['entorno'].get('offload')} - {payload['entorno'].get('motivo_offload')}")
    print(f"Matriz completa  : {'si' if payload['matriz_completa'] else 'NO (parcial)'}")
    print()
    print("AVISO: " + payload["aviso_principal"])
    print()
    print("Variabilidad natural entre dos controles: "
          f"{payload['metodo']['variabilidad_control']['valor']} "
          f"(informativa={payload['metodo']['variabilidad_control']['informativa']})")
    print(f"  {payload['metodo']['variabilidad_control']['nota']}")
    print()
    print("-" * 78)
    print("TABLA PARA EL DOCUMENTO DE T-07 (spikes/matriz-capacidades.md)")
    print("-" * 78)
    print(payload["tabla_markdown"])
    print()
    print("Leyenda de veredictos:")
    print("  SI             - capacidad invocada y efecto estructural esperado, medido.")
    print("  NO             - la pila del modelo declara que la tarea no existe (leer la traza).")
    print("  NO_CONCLUYENTE - no se pudo saber. Incluye el caso clave: el adapter minimo de")
    print("                   la Fase 0 no expone el parametro, asi que NO se distingue")
    print("                   'el modelo no lo soporta' de 'aun no lo hemos cableado'.")
    print()
    print("-" * 78)
    print("MOTIVO COMPLETO POR CAPACIDAD")
    print("-" * 78)
    for r in resultados:
        print(f"* {r.sonda.capability} -> {r.veredicto}"
              f"{f' (bruto: {r.veredicto_bruto})' if r.veredicto_bruto != r.veredicto else ''}")
        print(f"  {r.motivo}")
        for extra in r.motivos_extra:
            print(f"  - {extra}")
        if r.evidencia:
            for ruta in r.evidencia:
                print(f"  evidencia: {ruta}")
        print()
    print("-" * 78)
    print("RECOMENDACIONES")
    print("-" * 78)
    for rec in payload["recomendaciones"]:
        print(f"* {rec}")
    print()
    print("!" * 78)
    print("POLITICA DE PISTAS DE EVALUACION (S-11)")
    print("!" * 78)
    print(POLITICA_S11)
    print(f"Carpeta segregada : {payload['evidencia']['carpeta']}")
    print(f"Audio conservado  : {'si' if payload['evidencia']['audio_conservado'] else 'no'} "
          f"- {payload['evidencia']['motivo']}")
    print("!" * 78)
    print()
    print(f"Informe JSON: {ruta_json}")
    print()


# --------------------------------------------------------------------------- #
# Politica de conservacion del audio
# --------------------------------------------------------------------------- #

def decidir_audio(modo: str, keep_audio: bool) -> tuple[bool, str]:
    """Decide si la evidencia de audio se conserva, y lo explica.

    * En **GPU real** se conserva siempre: el criterio de aceptacion de `T-07`
      exige evidencia de audio por capacidad, y borrarla dejaria la tarea sin
      cerrar. `--keep-audio` ahi es redundante y se dice.
    * En **mock** se borra salvo `--keep-audio`: son WAV de silencio, sin valor
      probatorio, y ocupan ~10,6 MB por minuto de pista.
    """
    if modo != "mock":
        return (
            True,
            "Modo GPU real: la evidencia de audio se conserva SIEMPRE (el criterio de "
            "aceptacion de T-07 la exige). Carpeta segregada, retencion 12 meses (S-11)."
            + ("" if keep_audio else " --keep-audio no era necesario."),
        )
    if keep_audio:
        return (
            True,
            "Modo mock con --keep-audio: se conservan WAV de SILENCIO. No son evidencia "
            "de nada; solo sirven para inspeccionar el recorrido del script.",
        )
    return (
        False,
        "Modo mock sin --keep-audio: el audio simulado (silencio) se borra al terminar. "
        "El informe JSON se conserva como prueba de que el recorrido se ejecuto.",
    )


# --------------------------------------------------------------------------- #
# Flujo principal
# --------------------------------------------------------------------------- #

async def ejecutar(cfg: argparse.Namespace) -> tuple[dict[str, Any], Path, list[ResultadoSonda], int]:
    """Prepara el adapter, genera controles, corre las sondas y arma el informe."""
    dir_salida = Path(cfg.out).expanduser().resolve()
    dir_audio = dir_salida / "audio"

    # --- entorno y decision de offloading (D-06 / D-29) ------------------- #
    info_gpu = _timing.gpu_info()
    vram_total = info_gpu["vram_total_mb"] if info_gpu else None
    offload_auto, motivo_offload = _timing.decide_offloading(vram_total)
    if motivo_offload.startswith(_timing.NOT_VIABLE_PREFIX):
        raise SystemExit(
            f"[T-07] Abortado. {motivo_offload}\n"
            f"VRAM detectada: {vram_total} MB. Minimo exigido: {_timing.VRAM_FLOOR_MB} MB."
        )
    if info_gpu is None and not cfg.mock:
        raise SystemExit(
            "[T-07] Abortado: no hay GPU detectada (sin torch o sin CUDA) y no se pidio "
            "--mock. La matriz de capacidades exige el contenedor de T-05 sobre GPU "
            "real; una simulacion no responde a T-07.\n"
            "  - Para verificar el recorrido del script: anade --mock.\n"
            "  - Para medir de verdad: ejecuta dentro del contenedor de T-05 "
            "(docker run --gpus all), ver apps/runner/spikes/README.md."
        )
    offload = offload_auto if cfg.offload == "auto" else (cfg.offload == "on")

    # --- adapter ---------------------------------------------------------- #
    if cfg.mock:
        adapter: Any = MockMusicModelAdapter(
            output_dir=dir_audio,
            image_cached=True,
            weights_cached=True,
            time_scale=0.0,
        )
        extra_meta: dict[str, Any] = {"fuente": "mock", "origen": "spikes/_mock.py"}
        modo = "mock"
    else:
        ruta = _ruta_adapter_real(cfg.adapter_path)
        try:
            adapter, extra_meta = cargar_adapter_real(ruta, dir_audio)
        except (FileNotFoundError, RuntimeError) as exc:
            raise SystemExit(f"[T-07] Abortado: {exc}") from exc
        modo = "gpu"

    ctx = RunnerContext(
        device=cfg.device,
        dtype=cfg.dtype,
        offload=offload,
        weights_dir=cfg.weights_dir,
        max_gpu_seconds=cfg.max_gpu_seconds,
    )
    # M-6: un fallo de carga distinto de "sin CUDA" (pesos ausentes, hash
    # incorrecto, VRAM insuficiente...) es un fallo OPERATIVO del contrato de
    # salida: mensaje claro por stderr y exit 2, nunca un traceback crudo con
    # exit 1 (1 significa "informe parcial"). Antes de abortar se descarga en
    # best-effort: un load() parcialmente fallido puede haber reservado VRAM.
    try:
        await adapter.load(ctx)
    except Exception as exc:
        try:
            await adapter.unload()
        except Exception:  # noqa: BLE001, S110  (limpieza best-effort)
            pass
        raise SystemExit(
            f"[T-07] Abortado: load() del adapter fallo ({type(exc).__name__}: {exc}). "
            "No hay modelo que sondar; corrige la causa (pesos, VRAM, shim) y "
            "repite. No se escribe matriz."
        ) from exc
    salud = await adapter.health()
    if not salud.ready:
        try:
            await adapter.unload()
        except Exception:  # noqa: BLE001, S110  (limpieza best-effort)
            pass
        raise SystemExit(f"[T-07] Abortado: el adapter no esta listo tras load(). {salud.detail}")

    meta_adapter = metadatos_adapter(adapter, extra_meta)

    # El adapter de T-05 cae al mock cuando no ve CUDA o cuando ACE_STEP_MOCK esta
    # puesto. Si eso pasa sin que nosotros hayamos pedido --mock, el informe se
    # etiquetaria como "gpu" llevando dentro audio simulado: exactamente el dato
    # falso que T-07 no puede permitirse. Se degrada el modo (con lo que entran en
    # vigor los topes de honestidad) y se avisa a gritos.
    aviso_degradado = ""
    if modo == "gpu":
        backend = str(meta_adapter.get("backend", "") or "")
        fuente = str(meta_adapter.get("source", "") or "")
        if backend in ("mock", "unavailable") or fuente == "mock":
            modo = "mock"
            aviso_degradado = (
                "El adapter de T-05 NO esta corriendo sobre GPU real (backend="
                f"{backend!r}, source={fuente!r}): "
                f"{meta_adapter.get('backend_reason', '')} El modo se degrada a 'mock' "
                "y ningun veredicto podra ser SI ni NO. Para una medicion valida de "
                "T-07: GPU visible en el contenedor (docker run --gpus all), "
                "ACE_STEP_MOCK sin poner y ACE_STEP_REQUIRE_GPU=1."
            )
            print(f"[T-07] AVISO GRAVE: {aviso_degradado}", file=sys.stderr)

    declaradas = meta_adapter.get("capacidades_declaradas")
    entorno = {
        "gpu": info_gpu,
        "vram_total_mb": vram_total,
        "offload": offload,
        "modo_offload_pedido": cfg.offload,
        "motivo_offload": motivo_offload,
        "degradado_a_mock": aviso_degradado or None,
        "salud": {"ready": salud.ready, "detail": salud.detail,
                  "vram_total_mb": salud.vram_total_mb, "vram_free_mb": salud.vram_free_mb},
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "device": ctx.device,
        "dtype": ctx.dtype,
        "weights_dir": ctx.weights_dir,
    }

    presupuesto = Presupuesto(total_max_s=cfg.max_gpu_seconds_total)
    generaciones: list[Generacion] = []
    resultados: list[ResultadoSonda] = []
    completa = True
    # Inicializada ANTES del try: si el presupuesto salta antes de medirla, el
    # informe la reporta como no medida en vez de rescatarla de locals().
    variabilidad = Comparacion(
        valor=None, nota="No se llego a medir la variabilidad.", informativa=False
    )

    peticion_control = dict(
        style_prompt=cfg.style_prompt,
        duration_s=int(cfg.duration),
        max_gpu_seconds=cfg.max_gpu_seconds,
        lyrics=None,
        instrumental=True,  # sin letra: la sonda mide estructura, no interpretacion
        seed=cfg.seed,
    )

    try:
        # M-3: el coste de GPU del arranque (vram_load + warmup) se paga UNA vez
        # y el adapter lo reporta aparte; las telemetrias de cada generacion ya
        # no lo incluyen, asi que se registra aqui una sola vez.
        presupuesto.registrar_carga(float(meta_adapter.get("load_gpu_seconds") or 0.0))

        # Control A: es tambien la PISTA FUENTE de las sondas. Se genera con el
        # propio modelo a proposito (S-11 + gate de titularidad: nada de material
        # de terceros ni voz de personas reales en un spike).
        print("[T-07] Generando control A (pista fuente de las sondas)...")
        fuente = await generar(
            adapter,
            make_request(idempotency_key="t07-control-a-fuente", **peticion_control),
            etiqueta="control-a-fuente",
            dir_audio=dir_audio,
            ventana_s=cfg.ventana,
            presupuesto=presupuesto,
            registro=generaciones,
        )

        print("[T-07] Generando control B (variabilidad de ejecucion a ejecucion)...")
        control_b = await generar(
            adapter,
            make_request(idempotency_key="t07-control-b", **peticion_control),
            etiqueta="control-b",
            dir_audio=dir_audio,
            ventana_s=cfg.ventana,
            presupuesto=presupuesto,
            registro=generaciones,
        )

        variabilidad = comparar(
            fuente.medida.perfil if fuente.medida else None,
            control_b.medida.perfil if control_b.medida else None,
            contexto="control A vs control B",
        )
        print(f"[T-07] Variabilidad control-control: {variabilidad.valor} "
              f"(informativa={variabilidad.informativa})")

        for sonda in cfg.sondas:
            print(f"[T-07] Sondando {sonda.capability}...")
            resultado = await ejecutar_sonda(
                adapter,
                sonda,
                fuente=fuente,
                control=control_b,
                variabilidad=variabilidad,
                cfg=cfg,
                dir_audio=dir_audio,
                presupuesto=presupuesto,
                modo=modo,
                declaradas=declaradas,
                registro=generaciones,
            )
            resultados.append(resultado)
            print(f"        -> {resultado.veredicto}")

    except GpuBudgetExceeded as exc:
        # D-17 agregado: se detiene la matriz, pero el informe se escribe con lo
        # que haya. Un resultado parcial documentado es util; un fallo mudo no.
        completa = False
        print(f"[T-07] PRESUPUESTO AGREGADO DE GPU AGOTADO (D-17): {exc}")
        probadas = {r.sonda.capability for r in resultados}
        for sonda in cfg.sondas:
            if sonda.capability not in probadas:
                resultados.append(
                    sonda_no_ejecutada(
                        sonda,
                        (
                            "No ejecutada: el presupuesto agregado de GPU de la sonda se "
                            f"agoto ({exc}). Ampliar --max-gpu-seconds-total y repetir."
                        ),
                    )
                )
    finally:
        await adapter.unload()

    audio_conservado, motivo_audio = decidir_audio(modo, cfg.keep_audio)
    payload = construir_informe(
        cfg=cfg,
        modo=modo,
        meta_adapter=meta_adapter,
        entorno=entorno,
        generaciones=generaciones,
        variabilidad=variabilidad,
        resultados=resultados,
        presupuesto=presupuesto,
        completa=completa,
        audio_conservado=audio_conservado,
        motivo_audio=motivo_audio,
    )

    ruta_json = _timing.write_json_report(dir_salida / "matriz-capacidades-t07.json", payload)

    if not audio_conservado and dir_audio.is_dir():
        shutil.rmtree(dir_audio, ignore_errors=True)

    return payload, ruta_json, resultados, (0 if completa else 1)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def construir_parser() -> argparse.ArgumentParser:
    """Parser de la linea de comandos, con la ayuda en castellano."""
    por_defecto_out = _RAIZ_PROYECTO / "evaluacion-segregada" / "T-07-matriz-capacidades"
    parser = argparse.ArgumentParser(
        prog="capability_probe.py",
        description=(
            "T-07 - sonda empirica de capacidades de ACE-Step 1.5 (SECTION_INPAINT, "
            "AUDIO_TO_AUDIO, VOICE_CONDITIONING, CONTINUATION). Prueba invocando, no "
            "leyendo el README del modelo, y distingue 'el modelo no lo soporta' (NO) "
            "de 'nuestro adapter minimo de Fase 0 no lo expone' (NO_CONCLUYENTE)."
        ),
        epilog=(
            "Un veredicto NO_CONCLUYENTE no es un fallo del script: es el resultado "
            "honesto cuando la capacidad no se puede invocar todavia. " + POLITICA_S11
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Usa el adapter mock de spikes/_mock.py (solo biblioteca estandar). "
            "Obligatorio en maquinas sin GPU. En este modo NINGUN veredicto puede ser "
            "SI ni NO: una simulacion no responde a T-07."
        ),
    )
    parser.add_argument(
        "--capability",
        action="append",
        choices=sorted(SONDAS_POR_CLAVE),
        metavar="CAPACIDAD",
        help=(
            "Prueba solo esta capacidad (repetible). Por defecto, las cuatro. "
            f"Opciones: {', '.join(sorted(SONDAS_POR_CLAVE))}."
        ),
    )
    parser.add_argument(
        "--out",
        default=str(por_defecto_out),
        help=(
            "Carpeta SEGREGADA de evaluacion donde caen el informe JSON y las "
            f"evidencias de audio (subcarpeta 'audio/'). Por defecto: {por_defecto_out}. "
            "Retencion 12 meses; no es biblioteca de trabajo (S-11)."
        ),
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help=(
            "Conserva la evidencia de audio en modo mock (silencio, ~10,6 MB por minuto "
            "y por pista). En GPU real la evidencia se conserva siempre, porque el "
            "criterio de aceptacion de T-07 la exige."
        ),
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DURACION_POR_DEFECTO_S,
        help=(
            f"Duracion en segundos de las pistas de sonda (por defecto {DURACION_POR_DEFECTO_S}). "
            "Cortas a proposito: T-07 verifica capacidad, no calidad de cancion completa."
        ),
    )
    parser.add_argument("--seed", type=int, default=1234,
                        help="Semilla, registrada por trazabilidad. NO garantiza salida identica.")
    parser.add_argument(
        "--style-prompt",
        default="pop electronico melancolico, tempo medio, instrumental",
        help="Prompt de estilo de la peticion base.",
    )
    parser.add_argument("--device", default="cuda:0",
                        help="Dispositivo del RunnerContext (por defecto cuda:0; en mock es nominal).")
    parser.add_argument("--dtype", default="bfloat16", help="Precision de computo del RunnerContext.")
    parser.add_argument(
        "--offload",
        choices=("auto", "on", "off"),
        default="auto",
        help=(
            "Offloading de pesos. 'auto' (por defecto) lo decide la VRAM detectada con "
            "los umbrales de D-06: suelo 8 GB, confort 24 GB."
        ),
    )
    parser.add_argument("--weights-dir", default="/weights",
                        help="Directorio de la cache de pesos safetensors dentro del contenedor (D-14).")
    parser.add_argument(
        "--max-gpu-seconds",
        type=int,
        default=600,
        help="Presupuesto de GPU POR TRABAJO (D-17). Por defecto 600 s.",
    )
    parser.add_argument(
        "--max-gpu-seconds-total",
        type=int,
        default=3600,
        help=(
            "Presupuesto AGREGADO de GPU de toda la sonda (D-17). Por defecto 3600 s. "
            "Al agotarse, la matriz queda parcial y el informe lo dice."
        ),
    )
    parser.add_argument("--ventana", type=float, default=VENTANA_S,
                        help=f"Ventana del perfil de RMS en segundos (por defecto {VENTANA_S}).")
    parser.add_argument(
        "--adapter-path",
        default=None,
        help=(
            "Ruta al adapter real de T-05 (por defecto "
            "apps/runner/adapters/ace_step/adapter.py). Solo se usa sin --mock."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada. Devuelve el codigo de salida (0 ok, 1 parcial, 2 operativo).

    Todo el texto que se imprime es ASCII a proposito: este script se ejecuta
    dentro del contenedor de `T-05`, donde la configuracion regional puede ser `C`
    y un `print` con acentos abortaria la sonda por `UnicodeEncodeError` justo
    despues de haber gastado la GPU. El `reconfigure(errors="replace")` es el
    cinturon de seguridad por si alguien anade texto acentuado mas adelante: es
    preferible una letra sustituida a perder la matriz entera.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass

    parser = construir_parser()
    cfg = parser.parse_args(argv)

    if cfg.duration <= 0:
        parser.error("--duration debe ser > 0.")
    if cfg.ventana <= 0:
        parser.error("--ventana debe ser > 0.")
    if cfg.duration < cfg.ventana * 6:
        parser.error(
            f"--duration {cfg.duration} s es demasiado corta para una ventana de "
            f"{cfg.ventana} s: hacen falta al menos 6 ventanas para localizar un tramo "
            "de inpaint. Sube la duracion o baja la ventana."
        )

    claves = cfg.capability or sorted(SONDAS_POR_CLAVE)
    # Se respeta el orden canonico de SONDAS, no el de la linea de comandos, para
    # que dos ejecuciones den matrices comparables.
    cfg.sondas = [s for s in SONDAS if str(s.capability) in set(claves)]

    try:
        payload, ruta_json, resultados, codigo = asyncio.run(ejecutar(cfg))
    except SystemExit as exc:
        # Fallo operativo: no hay matriz que escribir.
        print(str(exc.code) if exc.code is not None else "[T-07] Abortado.", file=sys.stderr)
        return 2

    imprimir_informe(payload, ruta_json, resultados)
    if codigo != 0:
        print("[T-07] ATENCION: la matriz esta INCOMPLETA (ver 'matriz_completa' en el JSON).",
              file=sys.stderr)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
