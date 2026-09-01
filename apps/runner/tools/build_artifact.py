#!/usr/bin/env python3
"""Fusor OFFLINE del artefacto `ace_step_1_5.safetensors` — `T-03`/`T-05` (Fase 0).

Que es esto
-----------
El **unico productor** del fichero de pesos que espera el adapter
(`adapters/ace_step/adapter.py`, `DEFAULT_WEIGHTS_FILE = "ace_step_1_5.safetensors"`).
Ese fichero **no existe en ningun repo publico**: hay que fabricarlo fusionando
cuatro componentes que upstream publica por separado, y hacerlo de forma que el
resultado siga cumpliendo los invariantes del proyecto.

    dit.<clave>            677 tensores   4.565,9 MiB   acestep-v15-turbo/model.safetensors
    text_encoder.<clave>   310 tensores   1.136,4 MiB   Qwen3-Embedding-0.6B/model.safetensors
    vae.decoder.<clave>    182 tensores     161,0 MiB   vae/diffusion_pytorch_model.safetensors
    aux.*                    8 tensores      14,6 MiB   configs + tokenizer + latente de silencio
                          ----------------------------
                          1.177 tensores

Por que un solo fichero, y por que los configs van como tensores U8
-------------------------------------------------------------------
El adapter llama a `load_file(ruta, device=ctx.device)` y le pasa a la factoria
del shim **solo** `state_dict`, `device`, `dtype` y `offload`. La factoria no
recibe ni el `RunnerContext` ni el `weights_dir`, y `load_file()` **descarta**
`__metadata__` (solo lo ve `safe_open().metadata()`, que exige una ruta que la
factoria no tiene). Conclusion verificada en el host: **el `state_dict` es el
unico canal que llega al shim**. De ahi que `config.json`, `tokenizer.json`,
`tokenizer_config.json`, `special_tokens_map.json` y el latente de silencio
viajen como **tensores** (`U8` los blobs de texto, `F32` el latente) y no como
metadatos ni como ficheros hermanos.

Eso no relaja el invariante "solo safetensors": lo **refuerza**. Un tensor `U8`
es dato inerte —se parsea con `json` o con `tokenizers` (Rust), jamas con
`pickle`— y un unico SHA-256 (`ACE_STEP_WEIGHTS_SHA256`) pasa a sellar pesos,
configs, tokenizer y latente a la vez.

    AVISO GRANDE Y DELIBERADO — NO SUSTITUIR tokenizer.json POR vocab.json+merges.txt.
    Se empotra `tokenizer.json` ENTERO (11.423.705 B). La "optimizacion" de
    embarcar `vocab.json` + `merges.txt` (4,4 MB en vez de 11,4 MB) produce un
    tokenizer que PARECE funcionar y NO lo hace: se pierde el `post_processor`,
    que es quien anade `<|endoftext|>` (id 151643) al final de cada secuencia.
    Verificado hoy en el host: `encode("hola mundo").ids == [71, 7924, 28352, 151643]`.
    Sin ese ultimo id el condicionamiento del texto cambia, el audio sale distinto
    y **nada lanza un error**. Es un fallo silencioso. No se toca.

Por que la conversion BF16 -> FP16 se hace AQUI y no en la carga
---------------------------------------------------------------
`load_file()` ocurre **antes** de que la factoria del shim pueda opinar
(`adapter.py`, la factoria se resuelve en la linea anterior pero recibe el
`state_dict` ya materializado), asi que lo que haya en el fichero aterriza en
VRAM tal cual. En la GTX 1070 de referencia (Pascal `sm_61`, sin BF16, sin
tensor cores) hay ~6.988 MiB libres con el escritorio arrancado:

* artefacto en **FP16** = 5.878 MiB + contexto CUDA ~300 MiB = 6.178 MiB -> cabe,
  con 810 MiB de holgura;
* artefacto en **BF16** = mismo tamano pero de un dtype que `sm_61` no ejecuta, y
  convertirlo despues exige una copia entera mas -> OOM garantizado;
* artefacto en **FP32** = 9.132 MiB solo la ACE-Step -> imposible por aritmetica.

La conversion de los **pesos** es inocua y esta medida: `max|w|` global 5,03
frente al techo 65.504 de fp16, cero desbordamientos, y bf16 -> fp16 es *exacto*
en rango normal (fp16 tiene 10 bits de mantisa frente a los 7 de bf16). El riesgo
de fp16 en Pascal esta en las **activaciones**, no en los pesos, y eso es trabajo
del shim (`T-03`), no de este fichero.

Este fusor **declara** la conversion en `__metadata__` y en `aux.manifest_json`
(`source_dtype=bfloat16`, `stored_dtype=float16`) y **no reinterpreta ningun
otro byte**: los blobs `U8` se copian tal cual del fichero fuente (sin
reformatear el JSON, o el SHA-256 dejaria de cuadrar y el manifiesto mentiria) y
el latente `F32` se copia crudo del almacen del `.pt`.

Streaming, no `save_file()`
---------------------------
`safetensors.torch.save_file()` exige el `state_dict` COMPLETO en RAM: 6,16 GB
sobre 7,5 GiB libres, con un segfault ya reproducido al castear el diccionario
entero. Aqui se escribe **por streaming**, tensor a tensor:

    pasada 1  leer solo las CABECERAS de los tres safetensors upstream (8 bytes de
              longitud + JSON), calcular shapes, dtypes y offsets de salida, y
              serializar la cabecera completa del artefacto;
    pasada 2  escribir la cabecera y despues, en orden, cada tensor:
              `safe_open().get_tensor(k)` -> `.to(float16)` -> `f.write(buffer)` -> liberar.

El transitorio maximo es el tensor mas grande (`embed_tokens.weight`,
[151669, 1024] = 310 MiB) por dos (origen bf16 + destino fp16) mas las mascaras
de las guardias numericas: del orden de 1 GiB, no de 6.

Formato de salida (verificado en el host contra `load_file` y `safe_open`)
--------------------------------------------------------------------------
    [8 bytes u64 little-endian = longitud del header JSON]
    [header JSON UTF-8 rellenado con espacios ASCII hasta que (8+len) % 8 == 0]
    [bloque de datos]

Cada entrada del header es `{"dtype": ..., "shape": [...], "data_offsets": [ini, fin]}`
con offsets **relativos al inicio del bloque de datos**, contiguos y ascendentes
en el mismo orden en que se escriben: el validador de Rust exige
`start == last_stop` y un hueco rompe el fichero. `__metadata__` es una entrada
mas del header, `str -> str`.

El pickle en cuarentena
-----------------------
`D:\\srv\\ace-step\\quarantine\\silence_latent.pt` es **obligatorio** para
text2music segun el codigo upstream y es un **pickle**. Aqui se convierte a
`aux.silence_latent` **sin ejecutarlo**: se abre como ZIP, se desensambla el
pickle con `pickletools.genops` (parser puro, no ejecuta nada) y se rechaza por
lista blanca de opcodes. Ver la seccion 3 y, sobre todo, la nota larga de
`_OPCODES_LETALES`: una lista blanca que solo vigile `GLOBAL`/`STACK_GLOBAL`
**no sirve**, porque `INST`, `OBJ`, `NEWOBJ`, `NEWOBJ_EX`, `EXT1`, `EXT2` y
`EXT4` referencian callables sin emitir un solo `GLOBAL`.

Lo que este fichero NO hace, y quien lo hace
--------------------------------------------
* **No es el shim.** El despacho por componente (text_encoder a CPU/fp32,
  `dit.encoder`/`tokenizer`/`detokenizer` a CPU tras `prepare_condition`, VAE a
  fp32, decode troceado con solape de 16 frames), el centinela de mascara fp16,
  la reconstruccion de `rotary_emb.inv_freq` y la construccion en meta-device son
  **T-03**. Aqui no hay ni un import de `transformers` ni de `diffusers`: este
  fusor solo lee cabeceras y bytes, y por eso se puede ejecutar HOY en el host
  sin GPU, antes de que el shim exista.
* **No transpone el latente.** En disco es `[1, 64, 15000]` = `[B, C, T]` (el
  layout del VAE), pero `generate_audio` lo indexa como `[:, :T, :]` (dim 1 =
  tiempo). El shim **debe** transponer a `[1, 15000, 64]` con un assert: una
  transposicion olvidada no da error de forma, da audio basura. El fusor lo deja
  como esta y lo documenta en el manifiesto (`layout: "B,C,T"`).
* **No incluye el encoder del VAE** (183 tensores, 161 MiB). No hace falta para
  text2music y ahorra 161 MiB del pico mas estrecho del diseno. Se puede incluir
  con `--include-vae-encoder` para cuando las Fases 2-3 salgan de su gate.
* **No emite el manifiesto de procedencia v1 de la plataforma.** El esquema lo
  firma legal (D-20) y lo implementa `T-27` en la Fase 5. Lo que se empotra aqui
  es un manifiesto **del artefacto** marcado `manifest_schema_version="0-draft"`:
  reconstruir el artefacto cuando legal firme cuesta minutos.

Aviso de alcance de gate
------------------------
CLAUDE.md dice que **G2 legal bloquea TODO el desarrollo**. Este fichero produce
un artefacto de pesos **derivado** de tres modelos de terceros. Ejecutarlo es una
decision del propietario, no de la herramienta: el codigo esta escrito, revisado
y es reproducible, pero *correrlo* sobre los pesos reales queda a su criterio.

Uso
---
    python tools/build_artifact.py --dry-run     # plan, recuentos y tamano exacto
    python tools/build_artifact.py --selftest    # ciclo build+verify sobre un arbol sintetico
    python tools/build_artifact.py               # build real (minutos, ~6,2 GB)
    python tools/build_artifact.py --verify      # reabre y valida el artefacto ya escrito

Dependencias: `torch` (CPU basta), `safetensors>=0.8.0`, `numpy`. `tokenizers`
solo para `--verify` y `--selftest`. Sin red, sin CUDA, sin `transformers`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickletools
import shutil
import struct
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

TASK = "T-03"
TOOL = "build_artifact"

#: Version del fusor. Entra en el manifiesto: si cambia la logica de fusion,
#: sube. Dos artefactos con distinta `builder_version` no son comparables byte a
#: byte aunque las entradas sean identicas.
BUILDER_VERSION = "1.0.0"

#: Version del layout del artefacto (prefijos, nombres de las claves `aux.*`,
#: dtypes). El shim la lee de `aux.manifest_json` y debe rechazar lo que no
#: entienda: mejor un fallo de arranque legible que audio basura.
ARTIFACT_SCHEMA_VERSION = 1

#: BORRADOR a proposito. El esquema del manifiesto de procedencia **lo firma
#: legal antes de implementarse** (D-20, CLAUDE.md). Marcarlo asi deja constancia
#: de que este manifiesto es del ARTEFACTO (auditoria de la fusion) y no el
#: manifiesto de GENERACION de T-27, que es el que legal firma.
MANIFEST_SCHEMA_VERSION = "0-draft"

#: Revision upstream fijada. Jamas `refs/main`: no es reproducible.
UPSTREAM_REVISION = "19671f406d603126926c1b7e2adc169acbcade22"

DEFAULT_UPSTREAM_ROOT = rf"D:\srv\ace-step\upstream\{UPSTREAM_REVISION}"
DEFAULT_QUARANTINE_PT = r"D:\srv\ace-step\quarantine\silence_latent.pt"

#: Destino del artefacto. El **nombre** es innegociable: coincide con
#: `DEFAULT_WEIGHTS_FILE` del adapter, asi no hay que configurar
#: `ACE_STEP_WEIGHTS_FILE` en ningun sitio. El **directorio** es el que se monta
#: como `/weights:ro` en el contenedor, asi que da igual como se llame en el
#: host mientras este en D: (C: no tiene sitio).
DEFAULT_OUT = r"D:\srv\ace-step\weights\ace_step_1_5.safetensors"

#: Fichas de licencia locales. El invariante de CLAUDE.md exige licencias
#: verificadas ANTES de integrar; aqui se hashean para que el manifiesto las
#: referencie. Si falta alguna se avisa (WARNING visible), no se aborta: el
#: bloqueo es una decision del propietario, no de la herramienta.
DEFAULT_LICENSES_DIR = r"D:\srv\ace-step\provenance"

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_VERIFY = 3
EXIT_GUARD = 4

# --------------------------------------------------------------------------- #
# Constantes de formato y topes
# --------------------------------------------------------------------------- #

#: Tope del header JSON de un safetensors de entrada. El validador de Rust usa
#: 100 MB; aqui basta con muy poco (el mayor upstream son 80.560 B) y un tope
#: bajo evita que un fichero corrupto nos haga reservar memoria a lo tonto.
MAX_HEADER_BYTES = 16 * 1024 * 1024

#: Tamano FIJO reservado para `aux.manifest_json`. Es fijo a proposito: el
#: manifiesto lleva las guardias numericas, que solo se conocen DESPUES de
#: convertir los 6 GB, y no se puede reescribir la cabecera si cambia de
#: longitud (moveria todos los `data_offsets`). Con longitud fija, al terminar
#: se hace `seek` y se sobreescriben cabecera y manifiesto en su sitio.
#:
#: CUADRE DE TAMANOS con la cifra de aceptacion del analisis (6.163.403.698 B).
#: Esa cifra suponia un manifiesto de ~4.000 B y contaba SOLO el bloque de
#: datos. Medido con `--dry-run` sobre el arbol real:
#:     bloque de datos  6.163.407.890 B   (+4.192 B = 8.192 reservados - 4.000 estimados)
#:     cabecera + 8 B      143.560 B
#:     FICHERO TOTAL   6.163.551.450 B
#: El bloque de datos queda dentro del +-16 KiB de la aceptacion; la diferencia
#: del total es la cabecera, que aquella cifra no incluia. `--dry-run` imprime
#: los dos numeros para que no haya que reconstruir la resta.
AUX_MANIFEST_BYTES = 8192

#: Espacio libre minimo exigido en el destino antes de abrir el fichero.
MIN_FREE_BYTES = 8 * 1024 ** 3

#: Menor normal de fp16 (2**-14). Por debajo (y != 0) el valor es subnormal:
#: representable, pero con mantisa degradada.
FP16_MIN_NORMAL = 6.103515625e-05

#: Cotas duras del `.pt` en cuarentena. Un fichero que las supere se rechaza sin
#: mirarlo: no hay ningun motivo legitimo para que un latente de silencio de
#: 3,84 MB crezca, y una cota es mas barata que una auditoria.
MAX_PT_BYTES = 64 * 1024 * 1024
MAX_PT_MIEMBROS = 32
MAX_PICKLE_BYTES = 64 * 1024
MAX_OPCODES = 4096
MAX_PILA_PICKLE = 256

#: Recuentos canonicos de la revision fijada. Un desvio significa que se ha
#: cambiado de revision upstream (o que la descarga esta incompleta) y el
#: artefacto NO debe construirse a ciegas.
CANON_TENSORES_DIT = 677
CANON_TENSORES_TEXT_ENCODER = 310
CANON_TENSORES_VAE_DECODER = 182
CANON_TENSORES_VAE_ENCODER = 183
CANON_TENSORES_AUX = 8

#: Latente de silencio, medido hoy sobre el fichero en cuarentena.
CANON_LATENTE_SHAPE = (1, 64, 15000)
CANON_LATENTE_STORAGE_BYTES = 3_840_000
CANON_LATENTE_STORAGE_SHA256 = (
    "1491511c30d62238eb9b55ef0a01e220a3a664c2679444c44b3cdabd8cbbd29f"
)

#: Rutas relativas dentro del arbol upstream. Se centralizan aqui para que el
#: selftest pueda montar un arbol sintetico con la misma forma.
REL_ACESTEP_WEIGHTS = ("acestep-v15-turbo", "model.safetensors")
REL_ACESTEP_CONFIG = ("acestep-v15-turbo", "config.json")
REL_QWEN3_WEIGHTS = ("Qwen3-Embedding-0.6B", "model.safetensors")
REL_QWEN3_CONFIG = ("Qwen3-Embedding-0.6B", "config.json")
REL_QWEN3_TOKENIZER = ("Qwen3-Embedding-0.6B", "tokenizer.json")
REL_QWEN3_TOKENIZER_CONFIG = ("Qwen3-Embedding-0.6B", "tokenizer_config.json")
REL_QWEN3_SPECIAL_TOKENS = ("Qwen3-Embedding-0.6B", "special_tokens_map.json")
REL_VAE_WEIGHTS = ("vae", "diffusion_pytorch_model.safetensors")
REL_VAE_CONFIG = ("vae", "config.json")

#: Los cuatro prefijos del artefacto. REGLA DURA para el shim: toda clave que no
#: empiece por uno de estos es error fatal.
PREFIJO_DIT = "dit."
PREFIJO_TEXT_ENCODER = "text_encoder."
PREFIJO_VAE = "vae."
PREFIJO_AUX = "aux."

#: Fichas de licencia esperadas en `--licenses-dir`.
FICHAS_LICENCIA = (
    ("acestep", "MIT", "LICENSE.acestep.mit.txt"),
    ("qwen3_embedding", "Apache-2.0", "LICENSE.qwen3-embedding.apache-2.0.txt"),
)


# --------------------------------------------------------------------------- #
# Excepciones
# --------------------------------------------------------------------------- #

class BuildError(Exception):
    """Fallo de configuracion, de entrada o de invariante durante la fusion."""


class PickleRechazado(BuildError):
    """El `.pt` en cuarentena no supera la auditoria de opcodes.

    Se levanta ANTES de tocar un solo byte de datos. Nunca se degrada a aviso:
    aceptar un pickle que no encaja exactamente en la forma esperada equivale a
    ejecutar codigo desconocido (D-14), y `weights_sha256` verifica integridad,
    no inocuidad.
    """


class VerificacionFallida(BuildError):
    """`--verify` encontro una discrepancia en el artefacto ya escrito."""


# --------------------------------------------------------------------------- #
# Seccion 0 — utilidades: imports perezosos, hashes, disco, formato
# --------------------------------------------------------------------------- #

def _importar_torch() -> Any:
    """Importa `torch` con un mensaje util si no esta.

    Perezoso como en el resto de los spikes: `--help` y los errores de
    configuracion tienen que funcionar en un Python limpio.
    """
    try:
        import torch  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise BuildError(
            "Falta 'torch'. El fusor solo necesita la rueda CPU: la conversion "
            "bfloat16 -> float16 se hace en el host, sin CUDA."
        ) from exc
    return torch


def _importar_numpy() -> Any:
    try:
        import numpy  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise BuildError("Falta 'numpy' (se usa para el latente y para escribir buffers).") from exc
    return numpy


def _importar_safe_open() -> Any:
    try:
        from safetensors import safe_open  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise BuildError("Falta 'safetensors' (>=0.8.0).") from exc
    return safe_open


def sha256_fichero(ruta: Path, bloque: int = 8 * 1024 * 1024) -> str:
    """SHA-256 de un fichero por streaming. No carga el fichero en RAM."""
    if not ruta.is_file():
        raise BuildError(f"No existe el fichero a hashear: {ruta}")
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while True:
            trozo = f.read(bloque)
            if not trozo:
                break
            h.update(trozo)
    return h.hexdigest()


def _leer_bytes(ruta: Path, tope: int | None = None) -> bytes:
    """Lee un fichero entero como bytes, con tope opcional.

    Los blobs `U8` se copian TAL CUAL: nada de `json.load` + `json.dumps`. Si se
    reformatea el JSON, su SHA-256 deja de cuadrar con el fichero fuente y el
    manifiesto pasa a mentir sobre lo que contiene el artefacto.
    """
    if not ruta.is_file():
        raise BuildError(f"No existe el fichero de entrada: {ruta}")
    tam = ruta.stat().st_size
    if tope is not None and tam > tope:
        raise BuildError(f"Fichero demasiado grande ({tam} B > {tope} B): {ruta}")
    return ruta.read_bytes()


def _fmt_contador(n: int) -> str:
    """Contador como cadena de ANCHO FIJO (20 digitos).

    Ancho fijo porque estos valores se escriben dos veces —placeholder al abrir
    el fichero, valor real al cerrarlo— y la cabecera se sobreescribe en su
    sitio: si cambiase de longitud, moveria todos los `data_offsets`.
    """
    if n < 0 or n >= 10 ** 20:
        raise BuildError(f"Contador fuera de rango para el manifiesto: {n}")
    return f"{n:020d}"


def _fmt_real(x: float) -> str:
    """Real como cadena de ANCHO FIJO (12 caracteres, notacion cientifica)."""
    texto = f"{x:.6e}"
    if len(texto) != 12:
        raise BuildError(
            f"Valor no representable en ancho fijo para el manifiesto: {x!r} -> {texto!r}"
        )
    return texto


def _ahora_utc() -> str:
    """Marca de tiempo UTC de ancho fijo (20 caracteres)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validar_marca_tiempo(texto: str) -> str:
    """Valida `--built-at`.

    Existe para que dos ejecuciones con las mismas entradas Y la misma marca den
    ficheros byte-identicos: el reloj es la unica fuente de no-determinismo del
    fusor. Sin `--built-at`, el artefacto cambia de hash cada vez aunque los
    pesos sean los mismos.
    """
    try:
        datetime.strptime(texto, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise BuildError(
            f"--built-at debe ser 'AAAA-MM-DDTHH:MM:SSZ' en UTC; se recibio {texto!r}."
        ) from exc
    return texto


def _comprobar_destino(destino: Path, bytes_necesarios: int, permitir_disco_sistema: bool) -> None:
    """Puertas de disco antes de abrir el fichero de salida.

    Dos reglas, ambas aprendidas por las malas:
    1. **Nunca en el disco de sistema.** En esta maquina C: es el disco de
       Windows y de Docker Desktop; llenarlo a mitad de un build de 6 GB deja la
       maquina inutilizable, no solo el build.
    2. **Espacio libre suficiente**: `MIN_FREE_BYTES` o el tamano previsto con
       margen, lo que sea mayor.
    """
    carpeta = destino.parent

    # La comprobacion de unidad va ANTES del mkdir: rechazar el destino no debe
    # dejar creado un directorio en el disco que se acaba de rechazar.
    if os.name == "nt" and not permitir_disco_sistema:
        # `Path.drive` devuelve 'D:' en Windows y '' en POSIX; en POSIX esta
        # regla no aplica y se salta a proposito.
        unidad = os.path.splitdrive(str(destino.resolve()))[0].upper()
        sistema = os.path.splitdrive(os.environ.get("SystemDrive", "C:"))[0].upper() or "C:"
        if unidad == sistema:
            raise BuildError(
                f"Destino en el disco de sistema ({unidad}): {destino}. El artefacto son "
                f"~6,2 GB y C: es tambien el disco de Docker Desktop. Escribe en D: "
                f"(por defecto {DEFAULT_OUT}) o pasa --allow-system-drive si sabes lo "
                f"que haces."
            )

    carpeta.mkdir(parents=True, exist_ok=True)
    exigido = max(MIN_FREE_BYTES, int(bytes_necesarios * 1.05))
    libre = shutil.disk_usage(carpeta).free
    if libre < exigido:
        raise BuildError(
            f"Espacio insuficiente en {carpeta}: {libre / 2**30:.1f} GiB libres frente a "
            f"{exigido / 2**30:.1f} GiB exigidos (artefacto {bytes_necesarios / 2**30:.2f} GiB "
            f"+ margen). Un build interrumpido por disco lleno deja un .tmp de varios GB."
        )


def _log(mensaje: str, *, silencioso: bool = False) -> None:
    """Traza operativa a stderr.

    No es instrumentacion de depuracion: un build de 6,2 GB tarda minutos y un
    proceso mudo es indistinguible de uno colgado. Se silencia con `--quiet`.
    """
    if not silencioso:
        print(f"[{TASK}/{TOOL}] {mensaje}", file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Seccion 1 — cabeceras safetensors: lectura manual y serializacion
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class TensorUpstream:
    """Una entrada de la cabecera de un safetensors de entrada."""

    clave: str
    dtype: str
    shape: tuple[int, ...]
    nbytes: int


def leer_cabecera_safetensors(ruta: Path) -> tuple[dict[str, TensorUpstream], dict[str, str], int]:
    """Lee SOLO la cabecera de un safetensors: 8 bytes de longitud + JSON.

    No abre el bloque de datos ni mapea nada: es lo que permite planificar la
    fusion de 6,2 GB leyendo apenas 155 KB. Devuelve
    `(tensores_en_orden_de_cabecera, metadatos, offset_inicio_datos)`.

    Se valida que los `data_offsets` sean contiguos y ascendentes en el orden de
    la cabecera: es lo que exige el validador de Rust, y comprobarlo aqui detecta
    un fichero corrupto antes de gastar minutos.
    """
    if not ruta.is_file():
        raise BuildError(f"No existe el safetensors de entrada: {ruta}")

    with open(ruta, "rb") as f:
        crudo = f.read(8)
        if len(crudo) != 8:
            raise BuildError(f"Fichero truncado (menos de 8 bytes de cabecera): {ruta}")
        longitud = struct.unpack("<Q", crudo)[0]
        if longitud == 0 or longitud > MAX_HEADER_BYTES:
            raise BuildError(
                f"Longitud de cabecera absurda en {ruta}: {longitud} B "
                f"(tope {MAX_HEADER_BYTES} B). El fichero no es un safetensors valido."
            )
        cabecera_bytes = f.read(longitud)
    if len(cabecera_bytes) != longitud:
        raise BuildError(f"Cabecera truncada en {ruta}.")

    try:
        cabecera = json.loads(cabecera_bytes)
    except json.JSONDecodeError as exc:
        raise BuildError(f"Cabecera JSON invalida en {ruta}: {exc}") from exc
    if not isinstance(cabecera, dict):
        raise BuildError(f"Cabecera de {ruta} no es un objeto JSON.")

    metadatos_crudos = cabecera.pop("__metadata__", {}) or {}
    metadatos = {str(k): str(v) for k, v in metadatos_crudos.items()}

    tensores: dict[str, TensorUpstream] = {}
    ultimo_fin = 0
    for clave, info in cabecera.items():
        if not isinstance(info, dict):
            raise BuildError(f"Entrada de cabecera invalida en {ruta}: {clave!r}")
        try:
            dtype = str(info["dtype"])
            shape = tuple(int(d) for d in info["shape"])
            ini, fin = (int(v) for v in info["data_offsets"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BuildError(f"Entrada de cabecera incompleta en {ruta}: {clave!r}") from exc
        if ini != ultimo_fin:
            raise BuildError(
                f"Hueco en los data_offsets de {ruta} en {clave!r}: empieza en {ini} y el "
                f"tensor anterior acababa en {ultimo_fin}."
            )
        if fin < ini:
            raise BuildError(f"data_offsets invertidos en {ruta}: {clave!r}")
        ultimo_fin = fin
        tensores[clave] = TensorUpstream(clave=clave, dtype=dtype, shape=shape, nbytes=fin - ini)

    return tensores, metadatos, 8 + longitud


@dataclass(frozen=True, slots=True)
class EntradaPlan:
    """Una entrada del artefacto de salida, ya resuelta.

    `origen` distingue las dos vias de datos:
    * `"tensor"`  -> se lee de `fuente` con `safe_open().get_tensor(clave_fuente)`
                     y se convierte de `dtype_fuente` a `dtype_salida`;
    * `"bytes"`   -> los datos ya estan en `datos` (blobs `U8` y latente `F32`).
    """

    clave: str
    dtype_salida: str
    shape: tuple[int, ...]
    nbytes: int
    origen: str
    fuente: Path | None = None
    clave_fuente: str | None = None
    dtype_fuente: str | None = None
    datos: bytes | None = None


def serializar_cabecera(entradas: Sequence[EntradaPlan], metadatos: dict[str, str]) -> bytes:
    """Serializa la cabecera del artefacto, ya rellenada a multiplo de 8.

    Determinismo: separadores compactos fijos, `ensure_ascii=True`, orden de
    insercion fijo (nunca `sort_keys`, que reordenaria los tensores y romperia la
    contiguidad de los offsets). Dos ejecuciones con las mismas entradas y la
    misma `--built-at` producen exactamente estos mismos bytes.
    """
    cabecera: dict[str, Any] = {"__metadata__": dict(metadatos)}
    inicio = 0
    for entrada in entradas:
        cabecera[entrada.clave] = {
            "dtype": entrada.dtype_salida,
            "shape": list(entrada.shape),
            "data_offsets": [inicio, inicio + entrada.nbytes],
        }
        inicio += entrada.nbytes

    crudo = json.dumps(cabecera, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    # El bloque de datos tiene que empezar en un offset multiplo de 8: se rellena
    # el JSON con espacios ASCII, que `serde_json` acepta como espacio en blanco
    # final. Verificado contra `load_file` y `safe_open` en el host.
    relleno = (-(8 + len(crudo))) % 8
    return crudo + b" " * relleno


def offsets_absolutos(entradas: Sequence[EntradaPlan], inicio_datos: int) -> dict[str, int]:
    """Offset absoluto (desde el principio del fichero) de cada entrada."""
    offsets: dict[str, int] = {}
    cursor = inicio_datos
    for entrada in entradas:
        offsets[entrada.clave] = cursor
        cursor += entrada.nbytes
    return offsets


# --------------------------------------------------------------------------- #
# Seccion 2 — conversion segura del pickle en cuarentena
# --------------------------------------------------------------------------- #
#
# Aqui no se llama NUNCA a `pickle.load`, `torch.load`, `joblib`, `dill` ni
# `np.load(allow_pickle=True)`. Se desensambla el flujo con `pickletools.genops`,
# que es un PARSER: recorre los opcodes y devuelve sus argumentos literales sin
# ejecutar ninguno. Sobre ese flujo se aplican cuatro capas:
#
#   capa 1  lista blanca de opcodes INERTES + denegacion explicita y por nombre
#           de los opcodes letales (ver `_OPCODES_LETALES`);
#   capa 2  cotas de recuento para los tres opcodes que pueden referenciar un
#           callable (`GLOBAL`/`STACK_GLOBAL`, `BINPERSID`, `REDUCE`);
#   capa 3  un mini-interprete INERTE que reconstruye la pila con valores
#           basicos (int, str, bool, None, tuple) y MARCADORES —nunca objetos
#           reales, nunca una llamada—, y que en `REDUCE` hace *pattern matching*
#           contra las dos unicas formas admitidas en vez de invocar nada;
#   capa 4  validacion semantica del tensor resultante (shape, strides, offset,
#           requires_grad, numel) y SHA-256 del almacen contra una constante.
#
# Ninguna capa sobra. La capa 3 es la que convierte una "lista blanca de
# opcodes" en una garantia real: sin ella, una secuencia de opcodes todos
# inertes puede seguir describiendo un objeto que no es el que esperamos.

#: Opcodes inertes: mueven datos por la pila y el memo, y construyen valores
#: basicos. Ninguno puede referenciar, construir ni mutar un objeto de usuario.
_OPCODES_INERTES = frozenset({
    "PROTO", "FRAME", "STOP", "MARK",
    "PUT", "BINPUT", "LONG_BINPUT", "MEMOIZE",
    "GET", "BINGET", "LONG_BINGET",
    "BINUNICODE", "SHORT_BINUNICODE", "BINUNICODE8",
    "BININT", "BININT1", "BININT2", "LONG1", "LONG4",
    "NEWTRUE", "NEWFALSE", "NONE",
    "EMPTY_TUPLE", "TUPLE", "TUPLE1", "TUPLE2", "TUPLE3",
})

#: Opcodes CONTROLADOS: los tres unicos que pueden acabar referenciando un
#: callable o un objeto externo. Se permiten con cota de recuento y con
#: validacion semantica obligatoria; nunca se ejecutan.
_OPCODES_CONTROLADOS = frozenset({"GLOBAL", "STACK_GLOBAL", "BINPERSID", "REDUCE"})

#: LOS LETALES. Esta tabla es el corazon de la auditoria y el motivo de que una
#: lista blanca ingenua NO SIRVA.
#:
#: El error clasico es escribir un validador que solo mire `GLOBAL` y
#: `STACK_GLOBAL` ("si los nombres importados son benignos, el pickle es
#: benigno"). Es falso, y esta demostrado: los siete opcodes de abajo
#: referencian o construyen objetos SIN emitir un solo `GLOBAL`.
#:
#:   INST        lee modulo y clase como texto plano en el propio opcode y los
#:               instancia. No hay GLOBAL en ninguna parte del flujo.
#:   OBJ         igual, tomando la clase de la pila.
#:   NEWOBJ      llama a `cls.__new__(cls, *args)`.
#:   NEWOBJ_EX   igual con kwargs.
#:   EXT1/2/4    resuelven un callable por CODIGO NUMERICO contra la tabla de
#:               extension del `copyreg`; el nombre no aparece en el fichero, asi
#:               que ningun filtro por cadena lo ve pasar.
#:   BUILD       invoca `__setstate__`/actualiza `__dict__` sobre el objeto que
#:               haya en la pila: es mutacion arbitraria de estado.
#:   PERSID      variante textual de `BINPERSID`: lee el id persistente como
#:               linea de texto. No aparece en nada que escriba torch; si
#:               aparece, el fichero no lo ha generado torch.
#:
#: Se rechazan por NOMBRE, antes de cualquier otro analisis, aunque el resto del
#: flujo pareciese impecable.
_OPCODES_LETALES: dict[str, str] = {
    "INST": "instancia una clase leida como texto plano, sin emitir GLOBAL",
    "OBJ": "instancia la clase que haya en la pila, sin emitir GLOBAL",
    "NEWOBJ": "llama a cls.__new__(cls, *args)",
    "NEWOBJ_EX": "llama a cls.__new__(cls, *args, **kwargs)",
    "EXT1": "resuelve un callable por codigo numerico de la tabla de extension (invisible a un filtro por nombre)",
    "EXT2": "resuelve un callable por codigo numerico de la tabla de extension (invisible a un filtro por nombre)",
    "EXT4": "resuelve un callable por codigo numerico de la tabla de extension (invisible a un filtro por nombre)",
    "BUILD": "invoca __setstate__ / muta __dict__ del objeto en la pila",
    "PERSID": "id persistente en texto plano; torch nunca lo emite",
}

#: Los TRES unicos callables que puede nombrar el pickle. Cualquier otro nombre
#: —incluido cualquier cosa de `os`, `builtins`, `posix`, `subprocess`,
#: `torch.serialization` o `numpy.core.multiarray`— aborta.
_CALLABLES_PERMITIDOS = frozenset({
    ("torch._utils", "_rebuild_tensor_v2"),
    ("torch", "FloatStorage"),
    ("collections", "OrderedDict"),
})

#: Cotas de recuento, ajustadas a la forma canonica EXACTA que emite
#: `torch.save` para un tensor pelado (verificada hoy sobre el fichero real y
#: sobre uno recien generado con torch 2.13):
#:   3 GLOBAL (rebuild, FloatStorage, OrderedDict), 1 BINPERSID, 2 REDUCE.
_MAX_GLOBAL = 3
_MAX_BINPERSID = 1
_MAX_REDUCE = 2


@dataclass(frozen=True, slots=True)
class _Callable:
    """Marcador INERTE de un callable nombrado por GLOBAL/STACK_GLOBAL.

    Deliberadamente NO resuelve el import: guarda las dos cadenas y nada mas.
    Resolver el nombre ya seria dar un paso hacia ejecutar el pickle.
    """

    modulo: str
    nombre: str


class _MarcaDictVacio:
    """Marcador inerte del `OrderedDict()` vacio de `backward_hooks`."""

    __slots__ = ()


_DICT_VACIO = _MarcaDictVacio()


@dataclass(frozen=True, slots=True)
class _RefAlmacen:
    """Referencia a un almacen (resultado inerte de BINPERSID)."""

    tipo: _Callable
    clave: str
    ubicacion: str
    numel: int


@dataclass(frozen=True, slots=True)
class _EspecTensor:
    """Descripcion inerte del tensor: lo que `_rebuild_tensor_v2` habria construido."""

    almacen: _RefAlmacen
    offset: int
    shape: tuple[int, ...]
    strides: tuple[int, ...]
    requires_grad: bool


@dataclass(slots=True)
class AuditoriaPickle:
    """Resultado de la auditoria, para el manifiesto."""

    opcodes: int = 0
    globals_vistos: tuple[str, ...] = ()
    reduce: int = 0
    binpersid: int = 0
    protocolo: int = 0


def _strides_contiguos(shape: Sequence[int]) -> tuple[int, ...]:
    """Strides de un tensor C-contiguo con esa forma."""
    strides: list[int] = []
    acumulado = 1
    for dim in reversed(shape):
        strides.append(acumulado)
        acumulado *= int(dim)
    return tuple(reversed(strides))


def _resolver_callable(modulo: str, nombre: str, pos: int) -> _Callable:
    if (modulo, nombre) not in _CALLABLES_PERMITIDOS:
        raise PickleRechazado(
            f"Callable no permitido en el pickle (offset {pos}): {modulo}.{nombre}. "
            f"Solo se admiten: "
            + ", ".join(sorted(f"{m}.{n}" for m, n in _CALLABLES_PERMITIDOS))
            + ". Cualquier otro nombre convierte la carga en ejecucion de codigo (D-14)."
        )
    return _Callable(modulo=modulo, nombre=nombre)


def _interpretar_pickle_inerte(datos: bytes) -> tuple[_EspecTensor, AuditoriaPickle]:
    """Mini-interprete INERTE del pickle. No ejecuta ni un solo opcode.

    Reconstruye la pila con `int`, `str`, `bool`, `None`, `tuple` y los tres
    marcadores (`_Callable`, `_RefAlmacen`, `_MarcaDictVacio`). Donde un
    `pickle.Unpickler` llamaria a una funcion, aqui se hace *pattern matching*
    contra las dos unicas formas admitidas:

        REDUCE(collections.OrderedDict, ())            -> marcador de dict vacio
        REDUCE(torch._utils._rebuild_tensor_v2, args)  -> _EspecTensor validado

    Cualquier otra combinacion aborta. El objeto de nivel superior tiene que ser
    un tensor pelado: un `.pt` que contenga un diccionario, una lista o
    cualquier otra estructura se rechaza a proposito (menos superficie, y no hay
    ningun motivo para que el latente de silencio cambie de forma).
    """
    if len(datos) > MAX_PICKLE_BYTES:
        raise PickleRechazado(
            f"data.pkl de {len(datos)} B supera el tope de {MAX_PICKLE_BYTES} B. "
            "El pickle canonico de un tensor pelado ocupa 166 B."
        )

    pila: list[Any] = []
    marcas: list[int] = []
    memo: dict[int, Any] = {}
    auditoria = AuditoriaPickle()
    globals_vistos: list[str] = []
    pos_stop = -1

    def sacar(n: int, opcode: str, pos: int) -> list[Any]:
        if len(pila) < n:
            raise PickleRechazado(
                f"Pila insuficiente para {opcode} en el offset {pos} "
                f"({len(pila)} elementos, se necesitan {n}). Pickle malformado."
            )
        valores = pila[-n:]
        del pila[-n:]
        return valores

    try:
        flujo: Iterator[tuple[Any, Any, int]] = pickletools.genops(datos)
        for opcode, arg, pos in flujo:
            nombre = opcode.name
            auditoria.opcodes += 1
            if auditoria.opcodes > MAX_OPCODES:
                raise PickleRechazado(
                    f"El pickle supera los {MAX_OPCODES} opcodes. El canonico tiene 39 "
                    "(medido sobre el fichero en cuarentena)."
                )
            if len(pila) > MAX_PILA_PICKLE:
                raise PickleRechazado(f"Pila del pickle desbordada (> {MAX_PILA_PICKLE}).")

            # --- capa 1: denegacion explicita, antes de nada mas -------------
            if nombre in _OPCODES_LETALES:
                raise PickleRechazado(
                    f"Opcode PROHIBIDO {nombre} en el offset {pos}: "
                    f"{_OPCODES_LETALES[nombre]}. Un filtro que solo vigile "
                    f"GLOBAL/STACK_GLOBAL no lo veria pasar; por eso se rechaza por nombre."
                )
            if nombre not in _OPCODES_INERTES and nombre not in _OPCODES_CONTROLADOS:
                raise PickleRechazado(
                    f"Opcode fuera de la lista blanca: {nombre} (offset {pos}). "
                    "La lista blanca es cerrada a proposito: lo que no se ha analizado, "
                    "no se acepta."
                )

            # --- capa 3: interprete inerte ------------------------------------
            if nombre == "PROTO":
                protocolo = int(arg)
                if not 2 <= protocolo <= 5:
                    raise PickleRechazado(
                        f"Protocolo de pickle {protocolo} no admitido (se exige 2..5; "
                        "torch escribe 2). Los protocolos de texto (0 y 1) permiten "
                        "opcodes que este parser no audita."
                    )
                auditoria.protocolo = protocolo
            elif nombre == "FRAME":
                # Solo declara la longitud del siguiente marco. Inerte.
                pass
            elif nombre == "STOP":
                pos_stop = pos
                break
            elif nombre == "MARK":
                marcas.append(len(pila))
            elif nombre in ("PUT", "BINPUT", "LONG_BINPUT"):
                if not pila:
                    raise PickleRechazado(f"{nombre} con la pila vacia (offset {pos}).")
                memo[int(arg)] = pila[-1]
            elif nombre == "MEMOIZE":
                if not pila:
                    raise PickleRechazado(f"MEMOIZE con la pila vacia (offset {pos}).")
                memo[len(memo)] = pila[-1]
            elif nombre in ("GET", "BINGET", "LONG_BINGET"):
                clave_memo = int(arg)
                if clave_memo not in memo:
                    raise PickleRechazado(f"Referencia a memo inexistente {clave_memo} (offset {pos}).")
                pila.append(memo[clave_memo])
            elif nombre in ("BINUNICODE", "SHORT_BINUNICODE", "BINUNICODE8"):
                pila.append(str(arg))
            elif nombre in ("BININT", "BININT1", "BININT2", "LONG1", "LONG4"):
                pila.append(int(arg))
            elif nombre == "NEWTRUE":
                pila.append(True)
            elif nombre == "NEWFALSE":
                pila.append(False)
            elif nombre == "NONE":
                pila.append(None)
            elif nombre == "EMPTY_TUPLE":
                pila.append(())
            elif nombre == "TUPLE":
                if not marcas:
                    raise PickleRechazado(f"TUPLE sin MARK (offset {pos}).")
                indice = marcas.pop()
                if indice > len(pila):
                    raise PickleRechazado(f"MARK incoherente en TUPLE (offset {pos}).")
                valores = tuple(pila[indice:])
                del pila[indice:]
                pila.append(valores)
            elif nombre in ("TUPLE1", "TUPLE2", "TUPLE3"):
                n = int(nombre[-1])
                pila.append(tuple(sacar(n, nombre, pos)))

            # --- capa 2 + 3: los tres opcodes controlados ---------------------
            elif nombre == "GLOBAL":
                partes = str(arg).split(" ")
                if len(partes) != 2:
                    raise PickleRechazado(f"GLOBAL malformado en el offset {pos}: {arg!r}")
                if len(globals_vistos) >= _MAX_GLOBAL:
                    raise PickleRechazado(
                        f"Mas de {_MAX_GLOBAL} imports en el pickle (offset {pos}). "
                        "El canonico tiene exactamente tres."
                    )
                marcador = _resolver_callable(partes[0], partes[1], pos)
                globals_vistos.append(f"{marcador.modulo}.{marcador.nombre}")
                pila.append(marcador)
            elif nombre == "STACK_GLOBAL":
                # Se soporta EXPLICITAMENTE (aunque torch no lo emita en
                # protocolo 2) para que no pueda colarse por la puerta de atras
                # como "opcode desconocido" en un fichero de protocolo 4.
                atributo, modulo = sacar(2, nombre, pos)[::-1]
                if not isinstance(modulo, str) or not isinstance(atributo, str):
                    raise PickleRechazado(f"STACK_GLOBAL con operandos no textuales (offset {pos}).")
                if len(globals_vistos) >= _MAX_GLOBAL:
                    raise PickleRechazado(f"Mas de {_MAX_GLOBAL} imports en el pickle (offset {pos}).")
                marcador = _resolver_callable(modulo, atributo, pos)
                globals_vistos.append(f"{marcador.modulo}.{marcador.nombre}")
                pila.append(marcador)
            elif nombre == "BINPERSID":
                auditoria.binpersid += 1
                if auditoria.binpersid > _MAX_BINPERSID:
                    raise PickleRechazado(
                        f"Mas de {_MAX_BINPERSID} id persistente (offset {pos}): el latente "
                        "es un tensor con un unico almacen."
                    )
                (identificador,) = sacar(1, nombre, pos)
                pila.append(_construir_ref_almacen(identificador, pos))
            elif nombre == "REDUCE":
                auditoria.reduce += 1
                if auditoria.reduce > _MAX_REDUCE:
                    raise PickleRechazado(
                        f"Mas de {_MAX_REDUCE} REDUCE (offset {pos}). El pickle canonico de "
                        "un tensor pelado tiene exactamente dos: el OrderedDict vacio de "
                        "backward_hooks y el propio _rebuild_tensor_v2."
                    )
                argumentos, funcion = sacar(2, nombre, pos)[::-1]
                pila.append(_reducir_inerte(funcion, argumentos, pos))
            else:  # pragma: no cover - la lista blanca ya lo cubre
                raise PickleRechazado(f"Opcode no manejado: {nombre} (offset {pos}).")
    except (ValueError, IndexError, struct.error) as exc:
        # `genops` levanta ValueError sobre un flujo corrupto. No se degrada a
        # aviso: un pickle que no se puede parsear no se puede auditar.
        raise PickleRechazado(f"El pickle no se puede desensamblar: {exc}") from exc

    if pos_stop < 0:
        raise PickleRechazado("El pickle no tiene opcode STOP.")
    if pos_stop + 1 != len(datos):
        raise PickleRechazado(
            f"Hay {len(datos) - pos_stop - 1} bytes DESPUES del STOP (offset {pos_stop}). "
            "Un flujo con cola es un flujo que no se ha auditado entero."
        )
    if len(pila) != 1:
        raise PickleRechazado(f"La pila final tiene {len(pila)} elementos; se esperaba 1.")
    if marcas:
        raise PickleRechazado("Quedan MARK sin cerrar al llegar al STOP.")

    resultado = pila[0]
    if not isinstance(resultado, _EspecTensor):
        raise PickleRechazado(
            f"El objeto de nivel superior no es un tensor: {type(resultado).__name__}. "
            "Se espera un tensor pelado guardado con torch.save(tensor, ruta); un "
            "diccionario o una lista se rechazan a proposito."
        )

    auditoria.globals_vistos = tuple(globals_vistos)
    return resultado, auditoria


def _construir_ref_almacen(identificador: Any, pos: int) -> _RefAlmacen:
    """Valida la tupla de id persistente y devuelve un marcador inerte.

    Forma canonica: `("storage", <FloatStorage>, "0", "cpu", numel)`.
    """
    if not isinstance(identificador, tuple) or len(identificador) != 5:
        raise PickleRechazado(
            f"Id persistente con forma inesperada en el offset {pos}: se espera una tupla "
            f"de 5 elementos ('storage', tipo, clave, ubicacion, numel)."
        )
    etiqueta, tipo, clave, ubicacion, numel = identificador
    if etiqueta != "storage":
        raise PickleRechazado(f"Id persistente que no es 'storage': {etiqueta!r} (offset {pos}).")
    if not isinstance(tipo, _Callable):
        raise PickleRechazado(f"Tipo de almacen no resuelto por GLOBAL (offset {pos}).")
    if (tipo.modulo, tipo.nombre) != ("torch", "FloatStorage"):
        raise PickleRechazado(
            f"Tipo de almacen {tipo.modulo}.{tipo.nombre}: solo se acepta torch.FloatStorage "
            "(el latente es float32; cualquier otro tipo cambiaria la reinterpretacion de "
            "los bytes, y este fusor no reinterpreta nada)."
        )
    if not isinstance(clave, str) or not clave.isdigit():
        raise PickleRechazado(f"Clave de almacen no numerica: {clave!r} (offset {pos}).")
    if ubicacion != "cpu":
        raise PickleRechazado(
            f"Almacen ubicado en {ubicacion!r}: solo se acepta 'cpu'. Un tensor guardado "
            "desde GPU exige un remapeo que este conversor no hace."
        )
    if not isinstance(numel, int) or numel <= 0:
        raise PickleRechazado(f"numel de almacen invalido: {numel!r} (offset {pos}).")
    return _RefAlmacen(tipo=tipo, clave=clave, ubicacion=ubicacion, numel=numel)


def _reducir_inerte(funcion: Any, argumentos: Any, pos: int) -> Any:
    """`REDUCE` sin llamar a nada: pattern matching contra las dos formas validas."""
    if not isinstance(funcion, _Callable):
        raise PickleRechazado(
            f"REDUCE sobre algo que no es un callable nombrado por GLOBAL (offset {pos})."
        )
    if not isinstance(argumentos, tuple):
        raise PickleRechazado(f"REDUCE con argumentos que no son una tupla (offset {pos}).")

    if (funcion.modulo, funcion.nombre) == ("collections", "OrderedDict"):
        if argumentos != ():
            raise PickleRechazado(
                f"OrderedDict con argumentos en el offset {pos}: solo se acepta el "
                "OrderedDict() vacio de backward_hooks."
            )
        return _DICT_VACIO

    if (funcion.modulo, funcion.nombre) != ("torch._utils", "_rebuild_tensor_v2"):
        raise PickleRechazado(
            f"REDUCE sobre {funcion.modulo}.{funcion.nombre} (offset {pos}): no admitido."
        )

    # Firma real: (storage, storage_offset, size, stride, requires_grad,
    #              backward_hooks[, metadata]).
    if len(argumentos) not in (6, 7):
        raise PickleRechazado(
            f"_rebuild_tensor_v2 con {len(argumentos)} argumentos (offset {pos}); se "
            "esperan 6 o 7."
        )
    almacen, offset, shape, strides, requires_grad, hooks = argumentos[:6]
    if len(argumentos) == 7 and argumentos[6] is not None:
        raise PickleRechazado(
            f"_rebuild_tensor_v2 con 'metadata' no nulo (offset {pos}): no se audita."
        )
    if not isinstance(almacen, _RefAlmacen):
        raise PickleRechazado(f"_rebuild_tensor_v2 sin referencia de almacen (offset {pos}).")
    if not isinstance(offset, int) or offset != 0:
        raise PickleRechazado(
            f"storage_offset={offset!r} (offset {pos}): solo se acepta 0. Un offset no nulo "
            "implica una vista sobre un almacen compartido, y aqui se copian bytes crudos."
        )
    if not isinstance(shape, tuple) or not shape or not all(isinstance(d, int) and d > 0 for d in shape):
        raise PickleRechazado(f"Forma del tensor invalida: {shape!r} (offset {pos}).")
    if not isinstance(strides, tuple) or len(strides) != len(shape):
        raise PickleRechazado(f"Strides invalidos: {strides!r} (offset {pos}).")
    if not isinstance(requires_grad, bool):
        raise PickleRechazado(f"requires_grad no booleano: {requires_grad!r} (offset {pos}).")
    if requires_grad:
        raise PickleRechazado(
            "requires_grad=True en el latente de silencio: un tensor con grafo no pinta "
            "nada en un artefacto de pesos."
        )
    if not isinstance(hooks, _MarcaDictVacio):
        raise PickleRechazado(
            f"backward_hooks no es un OrderedDict vacio (offset {pos}): "
            "cualquier hook seria codigo colgado del tensor."
        )
    return _EspecTensor(
        almacen=almacen,
        offset=offset,
        shape=tuple(int(d) for d in shape),
        strides=tuple(int(s) for s in strides),
        requires_grad=False,
    )


@dataclass(frozen=True, slots=True)
class LatenteConvertido:
    """Latente de silencio ya extraido del `.pt`, listo para escribirse."""

    datos: bytes
    shape: tuple[int, ...]
    strides: tuple[int, ...]
    sha256_almacen: str
    sha256_fichero: str
    auditoria: AuditoriaPickle


def convertir_latente_en_cuarentena(
    ruta: Path,
    *,
    shape_esperada: tuple[int, ...],
    sha256_esperado: str | None,
) -> LatenteConvertido:
    """Convierte `silence_latent.pt` a bytes `F32` sin ejecutar el pickle.

    Pasos, en este orden y sin atajos:
      1. tope de tamano y magic `PK\\x03\\x04`;
      2. apertura como ZIP; **todo** miembro debe estar `ZIP_STORED` (un miembro
         comprimido puede expandirse a lo que quiera: bomba de descompresion) y
         con nombre sin travesia de directorios;
      3. `byteorder` == `b"little"` (escribimos el buffer crudo tal cual);
      4. auditoria del `data.pkl` con la maquinaria de arriba;
      5. lectura del almacen crudo, comprobacion de tamano y SHA-256 contra la
         constante fijada;
      6. comprobacion de finitud sobre el buffer ya reinterpretado como `<f4`.

    Devuelve los **bytes crudos**: el almacen ya es float32 little-endian
    C-contiguo, que es exactamente lo que safetensors espera para un `F32`. No
    se reinterpreta ni un byte.
    """
    numpy = _importar_numpy()

    if sys.byteorder != "little":  # pragma: no cover - x86/arm64 son little
        raise BuildError(
            "Este fusor escribe buffers crudos y safetensors es little-endian; "
            f"esta maquina es {sys.byteorder}-endian."
        )
    if not ruta.is_file():
        raise BuildError(f"No existe el latente en cuarentena: {ruta}")

    tam = ruta.stat().st_size
    if tam > MAX_PT_BYTES:
        raise PickleRechazado(
            f"El .pt en cuarentena ocupa {tam} B (tope {MAX_PT_BYTES} B). El canonico son "
            "3.841.215 B; un fichero mayor no es el latente de silencio."
        )
    with open(ruta, "rb") as f:
        magic = f.read(4)
    if magic != b"PK\x03\x04":
        raise PickleRechazado(
            f"El .pt no empieza por el magic de ZIP: {magic!r}. Los .pt del formato antiguo "
            "(tar / pickle plano) no se auditan aqui y se rechazan."
        )

    sha_fichero = sha256_fichero(ruta)

    with zipfile.ZipFile(ruta) as zf:
        miembros = zf.infolist()
        if len(miembros) > MAX_PT_MIEMBROS:
            raise PickleRechazado(
                f"El ZIP tiene {len(miembros)} miembros (tope {MAX_PT_MIEMBROS})."
            )
        total_declarado = 0
        for info in miembros:
            if info.compress_type != zipfile.ZIP_STORED:
                raise PickleRechazado(
                    f"Miembro comprimido en el .pt: {info.filename!r} "
                    f"(compress_type={info.compress_type}). torch escribe siempre "
                    "ZIP_STORED; un miembro comprimido puede expandirse sin cota "
                    "(bomba de descompresion) y ademas oculta su contenido real."
                )
            if info.compress_size != info.file_size:
                raise PickleRechazado(
                    f"Miembro {info.filename!r} declara ZIP_STORED pero comprimido "
                    f"({info.compress_size}) y original ({info.file_size}) no coinciden."
                )
            nombre = info.filename.replace("\\", "/")
            if nombre.startswith("/") or ".." in nombre.split("/") or os.path.splitdrive(nombre)[0]:
                raise PickleRechazado(f"Nombre de miembro con travesia de directorios: {nombre!r}")
            total_declarado += info.file_size
            if total_declarado > MAX_PT_BYTES:
                raise PickleRechazado(
                    f"El contenido del ZIP supera {MAX_PT_BYTES} B sin descomprimir."
                )

        nombres = [i.filename.replace("\\", "/") for i in miembros]
        pkls = [n for n in nombres if n.endswith("/data.pkl")]
        if len(pkls) != 1:
            raise PickleRechazado(
                f"Se esperaba exactamente un 'data.pkl' en el ZIP; hay {len(pkls)}."
            )
        prefijo = pkls[0].rsplit("/", 1)[0]

        ruta_byteorder = f"{prefijo}/byteorder"
        if ruta_byteorder not in nombres:
            raise PickleRechazado(
                "El ZIP no declara 'byteorder'. Sin esa declaracion no se puede afirmar que "
                "los bytes del almacen sean little-endian, y este conversor los copia crudos."
            )
        byteorder = zf.read(ruta_byteorder).strip()
        if byteorder != b"little":
            raise PickleRechazado(f"byteorder={byteorder!r}: solo se acepta b'little'.")

        espec, auditoria = _interpretar_pickle_inerte(zf.read(pkls[0]))

        # --- capa 4: validacion semantica ---------------------------------
        if espec.shape != tuple(shape_esperada):
            raise PickleRechazado(
                f"Forma del latente {espec.shape}, se esperaba {tuple(shape_esperada)}. "
                "Un latente con otra forma no es el que consume generate_audio."
            )
        contiguos = _strides_contiguos(espec.shape)
        if espec.strides != contiguos:
            raise PickleRechazado(
                f"Strides {espec.strides} no son los C-contiguos {contiguos}. Este conversor "
                "copia el almacen crudo: un tensor no contiguo se reordenaria mal y el "
                "resultado seria audio basura sin ningun error de forma."
            )
        numel = math.prod(espec.shape)
        if espec.almacen.numel != numel:
            raise PickleRechazado(
                f"El almacen declara {espec.almacen.numel} elementos y la forma exige {numel}."
            )

        ruta_almacen = f"{prefijo}/data/{espec.almacen.clave}"
        if ruta_almacen not in nombres:
            raise PickleRechazado(f"No existe el miembro del almacen: {ruta_almacen!r}")
        info_almacen = next(i for i in miembros if i.filename.replace("\\", "/") == ruta_almacen)
        bytes_esperados = numel * 4  # float32
        if info_almacen.file_size != bytes_esperados:
            raise PickleRechazado(
                f"El almacen ocupa {info_almacen.file_size} B y la forma exige "
                f"{bytes_esperados} B."
            )
        crudo = zf.read(ruta_almacen)

    if len(crudo) != bytes_esperados:
        raise PickleRechazado(f"Lectura corta del almacen: {len(crudo)} de {bytes_esperados} B.")

    sha_almacen = hashlib.sha256(crudo).hexdigest()
    if sha256_esperado is not None and sha_almacen != sha256_esperado:
        raise PickleRechazado(
            f"SHA-256 del almacen {sha_almacen} != esperado {sha256_esperado}. El latente en "
            "cuarentena NO es el auditado; no se construye nada."
        )

    vista = numpy.frombuffer(crudo, dtype="<f4")
    if not bool(numpy.isfinite(vista).all()):
        raise PickleRechazado(
            "El latente de silencio contiene inf/NaN. No se empotra: un NaN en el "
            "condicionamiento se propaga a toda la difusion."
        )

    return LatenteConvertido(
        datos=crudo,
        shape=espec.shape,
        strides=espec.strides,
        sha256_almacen=sha_almacen,
        sha256_fichero=sha_fichero,
        auditoria=auditoria,
    )


# --------------------------------------------------------------------------- #
# Seccion 3 — guardias numericas de la conversion bfloat16 -> float16
# --------------------------------------------------------------------------- #

@dataclass(slots=True)
class GuardiasNumericas:
    """Estadisticas acumuladas de la conversion, con abortos duros.

    Valores de referencia medidos sobre la ACE-Step (2.393.872.518 parametros):
    `max_abs_weight` 5,03125, `overflow_count` 0, `subnormal_count` 3.319.119,
    `flush_to_zero_count` 3.263. Los recuentos del artefacto COMPLETO son
    mayores (incluyen Qwen3 y el decoder del VAE) y no se comparan contra una
    constante: se **registran** en el manifiesto para poder auditarlos entre
    builds. Lo que si es fallo duro es `overflow_count > 0` o
    `max_abs_weight > 1000`.
    """

    max_abs_weight: float = 0.0
    max_abs_clave: str = ""
    overflow_count: int = 0
    subnormal_count: int = 0
    flush_to_zero_count: int = 0
    elementos: int = 0
    tensores: int = 0

    def registrar(self, clave: str, origen: Any, destino: Any) -> None:
        """Mide un tensor recien convertido y aborta si algo se sale.

        Cada comprobacion se hace sobre el tensor concreto y el mensaje **nombra
        la clave**: con 1.177 tensores, un "hay un inf" sin nombre no sirve de
        nada.
        """
        torch = _importar_torch()

        no_finitos_origen = int((~torch.isfinite(origen)).sum())
        if no_finitos_origen:
            raise BuildError(
                f"El tensor de ORIGEN {clave!r} ya contiene {no_finitos_origen} valores no "
                "finitos. El checkpoint upstream esta corrupto o la revision no es la fijada."
            )

        no_finitos_destino = int((~torch.isfinite(destino)).sum())
        if no_finitos_destino:
            self.overflow_count += no_finitos_destino
            raise BuildError(
                f"Desbordamiento al convertir {clave!r} a float16: {no_finitos_destino} "
                "valores pasan a inf. El techo de fp16 es 65.504. Con este tensor el "
                "artefacto NO es utilizable; el build se aborta."
            )

        absolutos = destino.abs()
        maximo = float(absolutos.max())
        if maximo > self.max_abs_weight:
            self.max_abs_weight = maximo
            self.max_abs_clave = clave

        # Subnormal en fp16: representable pero con mantisa degradada.
        self.subnormal_count += int(((absolutos > 0) & (absolutos < FP16_MIN_NORMAL)).sum())
        # Flush-to-zero: el origen no era cero y el destino si lo es.
        self.flush_to_zero_count += int(((origen != 0) & (destino == 0)).sum())

        self.elementos += int(destino.numel())
        self.tensores += 1

    def cerrar(self) -> None:
        """Comprobaciones finales. Un fallo aqui invalida el artefacto entero."""
        if self.overflow_count > 0:
            raise BuildError(f"overflow_count={self.overflow_count}; se exige 0.")
        if self.max_abs_weight > 1000.0:
            raise BuildError(
                f"max_abs_weight={self.max_abs_weight} en {self.max_abs_clave!r}: por encima "
                "de 1000 la conversion a fp16 deja de ser defendible (las activaciones "
                "amplifican los pesos y el techo de fp16 es 65.504)."
            )

    def como_metadatos(self) -> dict[str, str]:
        """Vista de ancho fijo para la cabecera y el manifiesto."""
        return {
            "guard_max_abs_weight": _fmt_real(self.max_abs_weight),
            "guard_overflow_count": _fmt_contador(self.overflow_count),
            "guard_subnormal_count": _fmt_contador(self.subnormal_count),
            "guard_flush_to_zero_count": _fmt_contador(self.flush_to_zero_count),
            "guard_elements": _fmt_contador(self.elementos),
            "guard_tensors_converted": _fmt_contador(self.tensores),
        }


# --------------------------------------------------------------------------- #
# Seccion 4 — plan de fusion
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class Expectativas:
    """Recuentos y hashes que el fusor exige a la entrada.

    En produccion son los de la revision fijada; `--selftest` construye los
    suyos sobre el arbol sintetico. Tenerlos como dato (y no como constantes
    dispersas por el codigo) es lo que hace el selftest posible sin mover 6 GB.
    """

    tensores_dit: int = CANON_TENSORES_DIT
    tensores_text_encoder: int = CANON_TENSORES_TEXT_ENCODER
    tensores_vae_decoder: int = CANON_TENSORES_VAE_DECODER
    tensores_vae_encoder: int = CANON_TENSORES_VAE_ENCODER
    latente_shape: tuple[int, ...] = CANON_LATENTE_SHAPE
    latente_sha256: str | None = CANON_LATENTE_STORAGE_SHA256


@dataclass(frozen=True, slots=True)
class Rutas:
    """Rutas de entrada resueltas."""

    upstream_root: Path
    quarantine_pt: Path
    licenses_dir: Path

    def acestep_weights(self) -> Path:
        return self.upstream_root.joinpath(*REL_ACESTEP_WEIGHTS)

    def qwen3_weights(self) -> Path:
        return self.upstream_root.joinpath(*REL_QWEN3_WEIGHTS)

    def vae_weights(self) -> Path:
        return self.upstream_root.joinpath(*REL_VAE_WEIGHTS)


@dataclass(slots=True)
class PlanFusion:
    """Plan completo: entradas ordenadas, hashes de fuente y recuentos."""

    entradas: list[EntradaPlan]
    recuentos: dict[str, int]
    hashes: dict[str, dict[str, Any]]
    latente: LatenteConvertido
    incluir_vae_encoder: bool
    avisos: list[str] = field(default_factory=list)

    @property
    def bytes_datos(self) -> int:
        return sum(e.nbytes for e in self.entradas)

    @property
    def indice_manifiesto(self) -> int:
        for i, e in enumerate(self.entradas):
            if e.clave == "aux.manifest_json":
                return i
        raise BuildError("El plan no incluye aux.manifest_json.")


def _entradas_desde_safetensors(
    ruta: Path,
    prefijo: str,
    *,
    filtro_clave: Any = None,
) -> tuple[list[EntradaPlan], dict[str, TensorUpstream]]:
    """Convierte la cabecera de un safetensors upstream en entradas del plan.

    Se exige BF16 en el origen y se emite F16. Un dtype distinto aborta: un
    checkpoint mixto significa que la revision upstream ha cambiado y el analisis
    de VRAM (que asume 2 bytes por parametro) deja de valer.
    """
    tensores, _meta, _inicio = leer_cabecera_safetensors(ruta)
    entradas: list[EntradaPlan] = []
    for clave, info in tensores.items():
        if filtro_clave is not None and not filtro_clave(clave):
            continue
        if info.dtype != "BF16":
            raise BuildError(
                f"{ruta.name}:{clave} tiene dtype {info.dtype}; se esperaba BF16. La "
                "aritmetica de VRAM y la conversion declarada (bfloat16 -> float16) "
                "asumen un checkpoint homogeneo en BF16."
            )
        elementos = math.prod(info.shape) if info.shape else 1
        entradas.append(
            EntradaPlan(
                clave=f"{prefijo}{clave}",
                dtype_salida="F16",
                shape=info.shape,
                nbytes=elementos * 2,
                origen="tensor",
                fuente=ruta,
                clave_fuente=clave,
                dtype_fuente="BF16",
            )
        )
    return entradas, tensores


def construir_plan(
    rutas: Rutas,
    *,
    incluir_vae_encoder: bool,
    expectativas: Expectativas,
) -> PlanFusion:
    """Pasada 1: solo cabeceras y blobs pequenos. No toca los 6 GB de datos."""
    avisos: list[str] = []
    entradas: list[EntradaPlan] = []
    hashes: dict[str, dict[str, Any]] = {}

    def registrar_hash(etiqueta: str, ruta: Path) -> str:
        digest = sha256_fichero(ruta)
        hashes[etiqueta] = {
            "path": str(ruta),
            "sha256": digest,
            "bytes": ruta.stat().st_size,
        }
        return digest

    # --- dit.* -----------------------------------------------------------
    ruta_acestep = rutas.acestep_weights()
    registrar_hash("acestep_model_safetensors", ruta_acestep)
    ent_dit, _ = _entradas_desde_safetensors(ruta_acestep, PREFIJO_DIT)
    if len(ent_dit) != expectativas.tensores_dit:
        raise BuildError(
            f"{ruta_acestep.name}: {len(ent_dit)} tensores, se esperaban "
            f"{expectativas.tensores_dit}. Revision upstream distinta o descarga incompleta."
        )
    entradas.extend(ent_dit)

    # --- text_encoder.* --------------------------------------------------
    ruta_qwen3 = rutas.qwen3_weights()
    registrar_hash("qwen3_model_safetensors", ruta_qwen3)
    ent_te, _ = _entradas_desde_safetensors(ruta_qwen3, PREFIJO_TEXT_ENCODER)
    if len(ent_te) != expectativas.tensores_text_encoder:
        raise BuildError(
            f"{ruta_qwen3.name}: {len(ent_te)} tensores, se esperaban "
            f"{expectativas.tensores_text_encoder}."
        )
    entradas.extend(ent_te)

    # --- vae.decoder.* (y opcionalmente vae.encoder.*) -------------------
    # Se conserva el 'decoder.' upstream DENTRO del namespace 'vae.' para que
    # las Fases 2-3 puedan anadir 'vae.encoder.*' sin renombrar nada.
    ruta_vae = rutas.vae_weights()
    registrar_hash("vae_model_safetensors", ruta_vae)
    if incluir_vae_encoder:
        ent_vae, _ = _entradas_desde_safetensors(ruta_vae, PREFIJO_VAE)
        n_dec = sum(1 for e in ent_vae if e.clave.startswith("vae.decoder."))
        n_enc = sum(1 for e in ent_vae if e.clave.startswith("vae.encoder."))
    else:
        ent_vae, _ = _entradas_desde_safetensors(
            ruta_vae, PREFIJO_VAE, filtro_clave=lambda k: k.startswith("decoder.")
        )
        n_dec, n_enc = len(ent_vae), 0
    if n_dec != expectativas.tensores_vae_decoder:
        raise BuildError(
            f"{ruta_vae.name}: {n_dec} tensores 'decoder.*', se esperaban "
            f"{expectativas.tensores_vae_decoder}."
        )
    if incluir_vae_encoder and n_enc != expectativas.tensores_vae_encoder:
        raise BuildError(
            f"{ruta_vae.name}: {n_enc} tensores 'encoder.*', se esperaban "
            f"{expectativas.tensores_vae_encoder}."
        )
    entradas.extend(ent_vae)

    # --- aux.* -----------------------------------------------------------
    # Los blobs se copian TAL CUAL (ver `_leer_bytes`). El orden es fijo y
    # deliberado; `aux.manifest_json` va SIEMPRE el ultimo porque es el unico
    # que se reescribe al cerrar el fichero.
    blobs: list[tuple[str, Path]] = [
        ("aux.config.acestep_json", rutas.upstream_root.joinpath(*REL_ACESTEP_CONFIG)),
        ("aux.config.qwen3_json", rutas.upstream_root.joinpath(*REL_QWEN3_CONFIG)),
        ("aux.config.vae_json", rutas.upstream_root.joinpath(*REL_VAE_CONFIG)),
        # tokenizer.json ENTERO. Ver el aviso del docstring del modulo: sustituirlo
        # por vocab.json+merges.txt pierde el post_processor y es un fallo SILENCIOSO.
        ("aux.text_tokenizer.tokenizer_json", rutas.upstream_root.joinpath(*REL_QWEN3_TOKENIZER)),
        (
            "aux.text_tokenizer.tokenizer_config_json",
            rutas.upstream_root.joinpath(*REL_QWEN3_TOKENIZER_CONFIG),
        ),
        (
            "aux.text_tokenizer.special_tokens_map_json",
            rutas.upstream_root.joinpath(*REL_QWEN3_SPECIAL_TOKENS),
        ),
    ]
    etiquetas_hash = {
        "aux.config.acestep_json": "acestep_config_json",
        "aux.config.qwen3_json": "qwen3_config_json",
        "aux.config.vae_json": "vae_config_json",
        "aux.text_tokenizer.tokenizer_json": "qwen3_tokenizer_json",
        "aux.text_tokenizer.tokenizer_config_json": "qwen3_tokenizer_config_json",
        "aux.text_tokenizer.special_tokens_map_json": "qwen3_special_tokens_map_json",
    }
    for clave, ruta_blob in blobs:
        datos = _leer_bytes(ruta_blob, tope=64 * 1024 * 1024)
        registrar_hash(etiquetas_hash[clave], ruta_blob)
        entradas.append(
            EntradaPlan(
                clave=clave,
                dtype_salida="U8",
                shape=(len(datos),),
                nbytes=len(datos),
                origen="bytes",
                datos=datos,
            )
        )

    latente = convertir_latente_en_cuarentena(
        rutas.quarantine_pt,
        shape_esperada=expectativas.latente_shape,
        sha256_esperado=expectativas.latente_sha256,
    )
    hashes["silence_latent_pt"] = {
        "path": str(rutas.quarantine_pt),
        "sha256": latente.sha256_fichero,
        "bytes": rutas.quarantine_pt.stat().st_size,
    }
    hashes["silence_latent_storage"] = {
        "path": f"{rutas.quarantine_pt}::data/0",
        "sha256": latente.sha256_almacen,
        "bytes": len(latente.datos),
    }
    entradas.append(
        EntradaPlan(
            clave="aux.silence_latent",
            dtype_salida="F32",
            shape=latente.shape,
            nbytes=len(latente.datos),
            origen="bytes",
            datos=latente.datos,
        )
    )

    entradas.append(
        EntradaPlan(
            clave="aux.manifest_json",
            dtype_salida="U8",
            shape=(AUX_MANIFEST_BYTES,),
            nbytes=AUX_MANIFEST_BYTES,
            origen="bytes",
            datos=b" " * AUX_MANIFEST_BYTES,  # placeholder; se reescribe al cerrar
        )
    )

    # --- licencias -------------------------------------------------------
    for componente, spdx, nombre in FICHAS_LICENCIA:
        ruta_lic = rutas.licenses_dir / nombre
        if ruta_lic.is_file():
            hashes[f"license_{componente}"] = {
                "path": str(ruta_lic),
                "sha256": sha256_fichero(ruta_lic),
                "bytes": ruta_lic.stat().st_size,
                "spdx": spdx,
                "present": True,
            }
        else:
            hashes[f"license_{componente}"] = {
                "path": str(ruta_lic),
                "sha256": None,
                "bytes": 0,
                "spdx": spdx,
                "present": False,
            }
            avisos.append(
                f"FICHA DE LICENCIA AUSENTE: {componente} ({spdx}) - no existe {ruta_lic}. "
                "El invariante de CLAUDE.md exige licencias verificadas ANTES de integrar. "
                "El artefacto se construye, pero la deuda queda abierta y registrada en el "
                "manifiesto (license_file_present=false)."
            )

    n_aux = sum(1 for e in entradas if e.clave.startswith(PREFIJO_AUX))
    if n_aux != CANON_TENSORES_AUX:
        raise BuildError(f"Se han planificado {n_aux} tensores 'aux.*'; se esperaban {CANON_TENSORES_AUX}.")

    recuentos = {
        "dit": len(ent_dit),
        "text_encoder": len(ent_te),
        "vae_decoder": n_dec,
        "vae_encoder": n_enc,
        "aux": n_aux,
        "total": len(entradas),
    }

    # Assert de recuento del formato: 677 + 310 + 182 + 8 = 1177.
    esperado_total = (
        expectativas.tensores_dit
        + expectativas.tensores_text_encoder
        + expectativas.tensores_vae_decoder
        + (expectativas.tensores_vae_encoder if incluir_vae_encoder else 0)
        + CANON_TENSORES_AUX
    )
    if recuentos["total"] != esperado_total:
        raise BuildError(
            f"El plan tiene {recuentos['total']} tensores y el formato exige {esperado_total}."
        )

    claves = [e.clave for e in entradas]
    if len(set(claves)) != len(claves):
        raise BuildError("Hay claves duplicadas en el plan de fusion.")
    for clave in claves:
        if not clave.startswith((PREFIJO_DIT, PREFIJO_TEXT_ENCODER, PREFIJO_VAE, PREFIJO_AUX)):
            raise BuildError(f"Clave sin prefijo valido en el plan: {clave!r}")

    return PlanFusion(
        entradas=entradas,
        recuentos=recuentos,
        hashes=hashes,
        latente=latente,
        incluir_vae_encoder=incluir_vae_encoder,
        avisos=avisos,
    )


# --------------------------------------------------------------------------- #
# Seccion 5 — manifiesto de procedencia
# --------------------------------------------------------------------------- #

def construir_manifiesto(
    plan: PlanFusion,
    *,
    built_at: str,
    guardias: GuardiasNumericas,
) -> dict[str, Any]:
    """Manifiesto del ARTEFACTO. Se duplica en `__metadata__` y en `aux.manifest_json`.

    `__metadata__` es un **espejo documental**: lo ven las herramientas de
    auditoria y `safe_open().metadata()`, pero **nada funcional puede depender de
    el**, porque `load_file()` lo descarta y el shim no lo recibe. Por eso el
    manifiesto viaja tambien como tensor `U8`.
    """
    def hash_de(etiqueta: str) -> str | None:
        entrada = plan.hashes.get(etiqueta)
        return None if entrada is None else entrada.get("sha256")

    licencias = []
    for componente, spdx, _nombre in FICHAS_LICENCIA:
        info = plan.hashes[f"license_{componente}"]
        licencias.append({
            "component": componente,
            "spdx": spdx,
            "license_file_present": bool(info["present"]),
            "license_file_sha256": info["sha256"],
            "license_file_path": info["path"],
        })

    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_schema_note": (
            "BORRADOR. El esquema del manifiesto de procedencia de GENERACION lo firma "
            "legal (D-20) y lo implementa T-27 en la Fase 5. Este manifiesto describe la "
            "FUSION del artefacto, no una generacion: reconstruirlo cuando legal firme "
            "cuesta minutos."
        ),
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "format": "pt",
        "builder": {"tool": f"{TOOL}.py", "version": BUILDER_VERSION, "task": TASK},
        "built_at_utc": built_at,
        "upstream_revision": UPSTREAM_REVISION,
        "source_dtype": "bfloat16",
        "stored_dtype": "float16",
        "dtype_conversion": (
            "Los tensores de dit.*, text_encoder.* y vae.* se convierten de bfloat16 a "
            "float16 EN EL FUSOR, tensor a tensor y offline. Es la unica reinterpretacion "
            "de bytes del artefacto y esta declarada aqui a proposito. Motivo: load_file() "
            "deposita el fichero en VRAM ANTES de que la factoria del shim pueda opinar, y "
            "Pascal (sm_61) no ejecuta bfloat16. Los blobs aux.* NO se convierten."
        ),
        "sources": plan.hashes,
        "components": plan.recuentos,
        "vae_encoder_included": plan.incluir_vae_encoder,
        "prefix_contract": {
            "dit.": (
                "Namespace del AceStepConditionGenerationModel COMPLETO, no solo del DiT. "
                "Quitar 'dit.' devuelve las claves upstream exactas -> "
                "load_state_dict(strict=True) sin remapeo. OJO: 'dit.tokenizer.*' es el "
                "tokenizer de AUDIO (ResidualFSQ) y no tiene NADA que ver con el tokenizer "
                "de texto, que vive en 'aux.text_tokenizer.*'."
            ),
            "text_encoder.": (
                "Qwen3-Embedding-0.6B desnudo (embed_tokens/layers/norm, sin 'model.' ni "
                "lm_head). Quitar el prefijo -> Qwen3Model.load_state_dict(strict=True)."
            ),
            "vae.": (
                "Se conserva el 'decoder.' upstream DENTRO del namespace para que las "
                "Fases 2-3 puedan anadir 'vae.encoder.*' sin renombrar nada."
            ),
            "aux.": "Dato inerte: U8 (JSON/tokenizer) y F32 (latente). Nunca se castea.",
            "regla_dura": (
                "Toda clave que no empiece por uno de los cuatro prefijos es error fatal "
                "en el shim."
            ),
        },
        "silence_latent": {
            "source_pt_sha256": hash_de("silence_latent_pt"),
            "storage_sha256": hash_de("silence_latent_storage"),
            "shape": list(plan.latente.shape),
            "strides": list(plan.latente.strides),
            "layout": "B,C,T",
            "layout_warning": (
                "En disco es [1,64,15000] = [B,C,T] (layout del VAE), pero generate_audio "
                "lo indexa como [:, :T, :] (dim 1 = tiempo). EL SHIM DEBE TRANSPONER a "
                "[1,15000,64] con un assert: una transposicion olvidada no da error de "
                "forma, da audio basura."
            ),
            "conversion": (
                "Extraido del .pt en cuarentena SIN pickle.load ni torch.load: ZIP abierto "
                "con zipfile, data.pkl desensamblado con pickletools.genops y aceptado por "
                "lista blanca de opcodes; el almacen se copia crudo."
            ),
            "pickle_audit": {
                "opcodes": plan.latente.auditoria.opcodes,
                "protocol": plan.latente.auditoria.protocolo,
                "globals": list(plan.latente.auditoria.globals_vistos),
                "reduce_count": plan.latente.auditoria.reduce,
                "binpersid_count": plan.latente.auditoria.binpersid,
            },
        },
        "conversion_guards": guardias.como_metadatos(),
        "licenses": licencias,
        "license_notes": [
            "Los pesos del VAE proceden del repo de ACE-Step (MIT). El decoder Oobleck "
            "VENDORIZADO es CODIGO, obra derivada de diffusers (Apache-2.0): su aviso de "
            "copyright y su nota de modificacion van en la imagen, no en este artefacto.",
            "Apache-2.0 (Qwen3-Embedding) exige NOTICE/atribucion que MIT no. El artefacto "
            "redistribuye DOS licencias.",
        ],
        "notes": [
            "Este artefacto NO incluye el encoder del VAE (183 tensores, 161 MiB): no hace "
            "falta para text2music y las Fases 2-3 estan bloqueadas por gate.",
            "El .py vendorizado y sus parches (centinela de mascara fp16, reconstruccion de "
            "rotary_emb.inv_freq, construccion en meta-device) NO van aqui: son codigo, van "
            "en la imagen, y son trabajo de T-03.",
            "__metadata__ es un espejo DOCUMENTAL. load_file() lo descarta y la factoria del "
            "shim no lo recibe: nada funcional puede depender de el.",
            "sources[].path registra la ruta ABSOLUTA del host. Dos builds desde arboles "
            "colocados en rutas distintas producen manifiestos distintos y, por tanto, "
            "SHA-256 distintos, aunque los pesos sean identicos: el criterio de identidad "
            "real son los sha256 de las fuentes, no el del artefacto. Para un build "
            "reproducible byte a byte hacen falta la misma ruta y la misma --built-at.",
        ],
    }


def _manifiesto_plano(manifiesto: dict[str, Any], plan: PlanFusion) -> dict[str, str]:
    """Vista `str -> str` del manifiesto para `__metadata__`.

    Todos los valores tienen longitud determinada por las entradas (los hashes
    son 64 caracteres, la marca de tiempo 20, y las guardias van en ancho fijo),
    asi que la cabecera se puede reescribir en su sitio al cerrar el fichero.
    """
    def hash_de(etiqueta: str) -> str:
        entrada = plan.hashes.get(etiqueta) or {}
        return str(entrada.get("sha256") or "")

    plano: dict[str, str] = {
        "format": "pt",
        "artifact_schema_version": str(ARTIFACT_SCHEMA_VERSION),
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "builder_version": BUILDER_VERSION,
        "built_at_utc": str(manifiesto["built_at_utc"]),
        "upstream_revision": UPSTREAM_REVISION,
        "source_dtype": "bfloat16",
        "stored_dtype": "float16",
        "source_sha256_acestep": hash_de("acestep_model_safetensors"),
        "source_sha256_qwen3": hash_de("qwen3_model_safetensors"),
        "source_sha256_vae": hash_de("vae_model_safetensors"),
        "source_sha256_tokenizer_json": hash_de("qwen3_tokenizer_json"),
        "source_sha256_silence_latent_storage": hash_de("silence_latent_storage"),
        "components": json.dumps(plan.recuentos, separators=(",", ":"), sort_keys=True),
        "vae_encoder_included": "true" if plan.incluir_vae_encoder else "false",
        "licenses": json.dumps(
            [
                {
                    "component": lic["component"],
                    "spdx": lic["spdx"],
                    "license_file_present": lic["license_file_present"],
                }
                for lic in manifiesto["licenses"]
            ],
            separators=(",", ":"),
        ),
        "silence_latent_layout": "B,C,T",
        "metadata_is_documentary_only": (
            "load_file() descarta __metadata__; el canal funcional es aux.manifest_json"
        ),
    }
    plano.update({k: str(v) for k, v in manifiesto["conversion_guards"].items()})
    return plano


def _serializar_manifiesto_fijo(manifiesto: dict[str, Any]) -> bytes:
    """Serializa el manifiesto y lo rellena a `AUX_MANIFEST_BYTES`.

    El relleno son espacios: `json.loads` los tolera al final, asi que el shim
    puede hacer `json.loads(bytes(tensor))` sin ceremonias.
    """
    crudo = json.dumps(manifiesto, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if len(crudo) > AUX_MANIFEST_BYTES:
        raise BuildError(
            f"El manifiesto ocupa {len(crudo)} B y solo hay {AUX_MANIFEST_BYTES} B "
            f"reservados en aux.manifest_json. Sube AUX_MANIFEST_BYTES (y con el cambia "
            f"el tamano del artefacto) o acorta el manifiesto."
        )
    return crudo + b" " * (AUX_MANIFEST_BYTES - len(crudo))


# --------------------------------------------------------------------------- #
# Seccion 6 — escritura del artefacto
# --------------------------------------------------------------------------- #

def _escribir_bloque_datos(
    destino: Any,
    plan: PlanFusion,
    guardias: GuardiasNumericas,
    *,
    silencioso: bool,
) -> None:
    """Pasada 2: escribe los datos, un tensor cada vez.

    Se abre **un** `safe_open` por fichero fuente y se mantiene mientras las
    entradas consecutivas del plan vengan de ese fichero (el plan esta agrupado
    por origen a proposito). Cada tensor se convierte, se mide, se escribe y se
    libera antes de tocar el siguiente: el transitorio maximo es el tensor mas
    grande, no el artefacto.
    """
    torch = _importar_torch()
    safe_open = _importar_safe_open()

    # `safe_open` es un gestor de contexto; aqui la vida del handle no encaja en
    # un `with` porque abarca un tramo variable del plan, asi que se maneja a
    # mano con `try/finally`. Se guardan las dos referencias (contexto y handle)
    # en vez de asumir que `__enter__` devuelve `self`.
    contexto = None
    manejador = None
    fuente_abierta: Path | None = None
    escritos = 0
    bytes_escritos = 0
    total = len(plan.entradas)

    try:
        for entrada in plan.entradas:
            if entrada.origen == "bytes":
                if contexto is not None:
                    contexto.__exit__(None, None, None)
                    contexto, manejador, fuente_abierta = None, None, None
                datos = entrada.datos
                if datos is None or len(datos) != entrada.nbytes:
                    raise BuildError(f"Blob incoherente para {entrada.clave!r}.")
                destino.write(datos)
            else:
                if entrada.fuente != fuente_abierta:
                    if contexto is not None:
                        contexto.__exit__(None, None, None)
                    contexto = safe_open(str(entrada.fuente), framework="pt", device="cpu")
                    manejador = contexto.__enter__()
                    fuente_abierta = entrada.fuente
                    _log(f"leyendo {entrada.fuente.name}", silencioso=silencioso)

                assert manejador is not None and entrada.clave_fuente is not None
                origen = manejador.get_tensor(entrada.clave_fuente)
                if tuple(origen.shape) != entrada.shape:
                    raise BuildError(
                        f"{entrada.clave!r}: la cabecera declaraba {entrada.shape} y el "
                        f"tensor es {tuple(origen.shape)}."
                    )
                if origen.dtype is not torch.bfloat16:
                    raise BuildError(
                        f"{entrada.clave!r}: dtype {origen.dtype}, se esperaba bfloat16."
                    )
                convertido = origen.to(torch.float16).contiguous()
                guardias.registrar(entrada.clave, origen, convertido)

                bloque = convertido.numpy()
                vista = memoryview(bloque)
                if not vista.c_contiguous:  # pragma: no cover - .contiguous() lo garantiza
                    raise BuildError(f"{entrada.clave!r}: buffer no contiguo tras la conversion.")
                crudo = vista.cast("B")
                if len(crudo) != entrada.nbytes:
                    raise BuildError(
                        f"{entrada.clave!r}: {len(crudo)} B convertidos frente a "
                        f"{entrada.nbytes} B planificados."
                    )
                destino.write(crudo)
                # Liberar explicitamente antes del siguiente tensor: con
                # embed_tokens (310 MiB) el transitorio importa.
                del crudo, vista, bloque, convertido, origen

            escritos += 1
            bytes_escritos += entrada.nbytes
            if escritos % 100 == 0 or escritos == total:
                _log(
                    f"{escritos}/{total} tensores, {bytes_escritos / 2**30:.2f} GiB escritos",
                    silencioso=silencioso,
                )
    finally:
        if contexto is not None:
            contexto.__exit__(None, None, None)


def construir_artefacto(
    rutas: Rutas,
    destino: Path,
    *,
    incluir_vae_encoder: bool,
    expectativas: Expectativas,
    built_at: str,
    permitir_disco_sistema: bool,
    silencioso: bool = False,
) -> dict[str, Any]:
    """Construye el artefacto completo y devuelve el registro de procedencia.

    Se escribe a `<destino>.tmp` y se renombra al final: un build interrumpido no
    debe dejar un fichero a medias con el nombre bueno, porque el adapter lo
    cargaria tan contento (el SHA-256 lo salvaria, pero solo si esta configurado).
    """
    plan = construir_plan(
        rutas, incluir_vae_encoder=incluir_vae_encoder, expectativas=expectativas
    )
    for aviso in plan.avisos:
        _log(f"AVISO: {aviso}", silencioso=False)

    guardias = GuardiasNumericas()
    manifiesto = construir_manifiesto(plan, built_at=built_at, guardias=guardias)
    metadatos = _manifiesto_plano(manifiesto, plan)
    cabecera = serializar_cabecera(plan.entradas, metadatos)
    tamano_total = 8 + len(cabecera) + plan.bytes_datos

    _comprobar_destino(destino, tamano_total, permitir_disco_sistema)

    temporal = destino.with_name(destino.name + ".tmp")
    if temporal.exists():
        temporal.unlink()

    offsets = offsets_absolutos(plan.entradas, 8 + len(cabecera))
    offset_manifiesto = offsets["aux.manifest_json"]

    _log(
        f"escribiendo {tamano_total} B ({tamano_total / 2**30:.2f} GiB) en {temporal}",
        silencioso=silencioso,
    )
    try:
        with open(temporal, "wb") as f:
            f.write(struct.pack("<Q", len(cabecera)))
            f.write(cabecera)
            _escribir_bloque_datos(f, plan, guardias, silencioso=silencioso)

            guardias.cerrar()

            # Reescritura en su sitio de cabecera y manifiesto con las guardias
            # ya medidas. Las longitudes son fijas por construccion (ancho fijo
            # en los contadores, relleno fijo en el manifiesto); si aun asi
            # cambiasen, se aborta antes de corromper el fichero.
            manifiesto_final = construir_manifiesto(plan, built_at=built_at, guardias=guardias)
            metadatos_finales = _manifiesto_plano(manifiesto_final, plan)
            cabecera_final = serializar_cabecera(plan.entradas, metadatos_finales)
            if len(cabecera_final) != len(cabecera):
                raise BuildError(
                    f"La cabecera cambio de longitud al rellenar las guardias "
                    f"({len(cabecera)} -> {len(cabecera_final)}). No se puede reescribir en "
                    "su sitio sin mover todos los data_offsets."
                )
            bytes_manifiesto = _serializar_manifiesto_fijo(manifiesto_final)

            f.flush()
            f.seek(8)
            f.write(cabecera_final)
            f.seek(offset_manifiesto)
            f.write(bytes_manifiesto)
            f.flush()
            os.fsync(f.fileno())

        tamano_real = temporal.stat().st_size
        if tamano_real != tamano_total:
            raise BuildError(
                f"El fichero escrito ocupa {tamano_real} B y el plan preveia {tamano_total} B."
            )

        _log("calculando SHA-256 del artefacto", silencioso=silencioso)
        digest = sha256_fichero(temporal)
        os.replace(temporal, destino)
    except BaseException:
        # Sin artefactos a medias con nombre bueno. Se limpia el .tmp y se
        # propaga: un build que falla tiene que fallar de forma visible.
        if temporal.exists():
            try:
                temporal.unlink()
            except OSError:  # pragma: no cover - carrera con antivirus/indexador
                pass
        raise

    return {
        "artifact": {
            "path": str(destino),
            "bytes": tamano_total,
            "sha256": digest,
            "header_bytes": len(cabecera),
            "data_bytes": plan.bytes_datos,
            "tensors": plan.recuentos["total"],
        },
        "manifest": manifiesto_final,
        "warnings": plan.avisos,
    }


def escribir_procedencia(registro: dict[str, Any], destino_json: Path) -> None:
    """Escribe el JSON de procedencia hermano del artefacto.

    Duplica lo que ya va empotrado en `aux.manifest_json`: el fichero suelto es
    para el operador y para la auditoria (se lee sin abrir 6 GB), el empotrado es
    el que viaja con los pesos y entra en `ACE_STEP_WEIGHTS_SHA256`.
    """
    destino_json.parent.mkdir(parents=True, exist_ok=True)
    destino_json.write_text(
        json.dumps(registro, indent=2, ensure_ascii=True, sort_keys=False) + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# Seccion 7 — verificacion del artefacto ya escrito
# --------------------------------------------------------------------------- #

#: Casos de paridad del tokenizer. En escapes `\\uXXXX` a proposito: la consola
#: de Windows es cp1252 y un emoji literal en el fuente reventaria al imprimirlo.
CASOS_TOKENIZER: tuple[tuple[str, str], ...] = (
    ("ascii-simple", "the quick brown fox"),
    ("castellano-acentos", "canci\u00f3n de oto\u00f1o en Madrid, \u00a1vamos!"),
    ("emoji", "\U0001f3b5\U0001f3b6 lo-fi beats \U0001f3a7"),
    ("cjk", "\u6f22\u5b57\u30c6\u30b9\u30c8 \ud55c\uae00"),
    ("tabs-y-saltos", "a\tb\nc\r\n   d"),
    ("tokens-especiales-literales", "<|endoftext|> literal <|im_start|> mas texto"),
    ("mixto-largo", "verse 1: 90 bpm, C minor \u2014 \u00e7\u00e5\u00f8 \u2603 fin"),
)


def verificar_artefacto(
    artefacto: Path,
    rutas: Rutas,
    *,
    incluir_vae_encoder: bool,
    expectativas: Expectativas,
    silencioso: bool = False,
) -> dict[str, Any]:
    """Reabre el artefacto y comprueba que es lo que dice ser.

    Comprueba: recuento y prefijos de claves, dtypes, finitud de TODOS los
    tensores, round-trip byte a byte de los blobs `U8` contra los ficheros
    fuente, forma y hash del latente, presencia y coherencia de `__metadata__` y
    `aux.manifest_json`, y reconstruccion del tokenizer con
    `tokenizers.Tokenizer.from_str` con paridad de ids en los siete casos de
    arriba mas un lote con relleno.

    Lee los 6,2 GB: tarda. Es la unica forma de afirmar que el artefacto sirve.
    """
    torch = _importar_torch()
    safe_open = _importar_safe_open()

    if not artefacto.is_file():
        raise VerificacionFallida(f"No existe el artefacto: {artefacto}")

    problemas: list[str] = []
    resumen: dict[str, Any] = {"path": str(artefacto), "bytes": artefacto.stat().st_size}

    with safe_open(str(artefacto), framework="pt", device="cpu") as h:
        claves = list(h.keys())
        metadatos = h.metadata() or {}

        esperado_total = (
            expectativas.tensores_dit
            + expectativas.tensores_text_encoder
            + expectativas.tensores_vae_decoder
            + (expectativas.tensores_vae_encoder if incluir_vae_encoder else 0)
            + CANON_TENSORES_AUX
        )
        if len(claves) != esperado_total:
            problemas.append(f"{len(claves)} claves, se esperaban {esperado_total}.")

        por_prefijo = {
            "dit": sum(1 for k in claves if k.startswith(PREFIJO_DIT)),
            "text_encoder": sum(1 for k in claves if k.startswith(PREFIJO_TEXT_ENCODER)),
            "vae_decoder": sum(1 for k in claves if k.startswith("vae.decoder.")),
            "vae_encoder": sum(1 for k in claves if k.startswith("vae.encoder.")),
            "aux": sum(1 for k in claves if k.startswith(PREFIJO_AUX)),
        }
        resumen["counts"] = por_prefijo
        if por_prefijo["dit"] != expectativas.tensores_dit:
            problemas.append(f"dit.*: {por_prefijo['dit']} != {expectativas.tensores_dit}")
        if por_prefijo["text_encoder"] != expectativas.tensores_text_encoder:
            problemas.append(
                f"text_encoder.*: {por_prefijo['text_encoder']} != "
                f"{expectativas.tensores_text_encoder}"
            )
        if por_prefijo["vae_decoder"] != expectativas.tensores_vae_decoder:
            problemas.append(
                f"vae.decoder.*: {por_prefijo['vae_decoder']} != {expectativas.tensores_vae_decoder}"
            )
        if not incluir_vae_encoder and por_prefijo["vae_encoder"]:
            problemas.append("hay tensores vae.encoder.* y no se pidieron.")
        if por_prefijo["aux"] != CANON_TENSORES_AUX:
            problemas.append(f"aux.*: {por_prefijo['aux']} != {CANON_TENSORES_AUX}")

        sueltas = [k for k in claves if not k.startswith(
            (PREFIJO_DIT, PREFIJO_TEXT_ENCODER, PREFIJO_VAE, PREFIJO_AUX))]
        if sueltas:
            problemas.append(f"claves sin prefijo valido: {sueltas[:5]}")

        # --- dtypes y finitud, tensor a tensor ---------------------------
        _log(f"verificando {len(claves)} tensores", silencioso=silencioso)
        revisados = 0
        for clave in claves:
            tensor = h.get_tensor(clave)
            if clave.startswith(PREFIJO_AUX):
                if clave == "aux.silence_latent":
                    esperado = torch.float32
                else:
                    esperado = torch.uint8
            else:
                esperado = torch.float16
            if tensor.dtype is not esperado:
                problemas.append(f"{clave}: dtype {tensor.dtype}, se esperaba {esperado}")
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                problemas.append(f"{clave}: contiene inf/NaN")
            del tensor
            revisados += 1
            if revisados % 200 == 0:
                _log(f"  {revisados}/{len(claves)}", silencioso=silencioso)

        # --- round-trip byte a byte de los blobs U8 ----------------------
        pares = [
            ("aux.config.acestep_json", rutas.upstream_root.joinpath(*REL_ACESTEP_CONFIG)),
            ("aux.config.qwen3_json", rutas.upstream_root.joinpath(*REL_QWEN3_CONFIG)),
            ("aux.config.vae_json", rutas.upstream_root.joinpath(*REL_VAE_CONFIG)),
            ("aux.text_tokenizer.tokenizer_json", rutas.upstream_root.joinpath(*REL_QWEN3_TOKENIZER)),
            (
                "aux.text_tokenizer.tokenizer_config_json",
                rutas.upstream_root.joinpath(*REL_QWEN3_TOKENIZER_CONFIG),
            ),
            (
                "aux.text_tokenizer.special_tokens_map_json",
                rutas.upstream_root.joinpath(*REL_QWEN3_SPECIAL_TOKENS),
            ),
        ]
        tokenizer_empotrado: str | None = None
        for clave, ruta_fuente in pares:
            if clave not in claves:
                problemas.append(f"falta el blob {clave}")
                continue
            empotrado = bytes(h.get_tensor(clave).numpy().tobytes())
            original = ruta_fuente.read_bytes()
            if empotrado != original:
                problemas.append(
                    f"{clave}: NO es byte-identico a {ruta_fuente.name} "
                    f"({len(empotrado)} B frente a {len(original)} B). Los blobs se copian "
                    "tal cual: si difieren, alguien ha reformateado el JSON y el manifiesto "
                    "miente."
                )
            elif clave == "aux.text_tokenizer.tokenizer_json":
                tokenizer_empotrado = empotrado.decode("utf-8")

        # --- latente ------------------------------------------------------
        if "aux.silence_latent" in claves:
            latente = h.get_tensor("aux.silence_latent")
            if tuple(latente.shape) != tuple(expectativas.latente_shape):
                problemas.append(
                    f"aux.silence_latent: forma {tuple(latente.shape)}, se esperaba "
                    f"{tuple(expectativas.latente_shape)}"
                )
            digest = hashlib.sha256(latente.numpy().tobytes()).hexdigest()
            resumen["silence_latent_sha256"] = digest
            if expectativas.latente_sha256 and digest != expectativas.latente_sha256:
                problemas.append(
                    f"aux.silence_latent: sha256 {digest} != {expectativas.latente_sha256}"
                )
            del latente
        else:
            problemas.append("falta aux.silence_latent")

        # --- manifiesto ---------------------------------------------------
        if "aux.manifest_json" in claves:
            crudo = bytes(h.get_tensor("aux.manifest_json").numpy().tobytes())
            try:
                manifiesto = json.loads(crudo.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                problemas.append(f"aux.manifest_json no parsea: {exc}")
                manifiesto = {}
            resumen["manifest_schema_version"] = manifiesto.get("manifest_schema_version")
            for campo in ("upstream_revision", "source_dtype", "stored_dtype", "components"):
                if campo not in manifiesto:
                    problemas.append(f"aux.manifest_json sin campo {campo!r}")
            if manifiesto.get("stored_dtype") != "float16":
                problemas.append("aux.manifest_json: stored_dtype != float16")
            if metadatos.get("upstream_revision") != manifiesto.get("upstream_revision"):
                problemas.append("__metadata__ y aux.manifest_json discrepan en upstream_revision")
        else:
            problemas.append("falta aux.manifest_json")

        if not metadatos:
            problemas.append("__metadata__ vacio o ausente")
        resumen["metadata_keys"] = sorted(metadatos)

    # --- tokenizer: reconstruccion y paridad de ids -----------------------
    if tokenizer_empotrado is None:
        problemas.append("no se pudo extraer el tokenizer empotrado para la paridad de ids")
    else:
        problemas.extend(
            _verificar_tokenizer(
                tokenizer_empotrado, rutas.upstream_root.joinpath(*REL_QWEN3_TOKENIZER)
            )
        )

    resumen["problems"] = problemas
    resumen["ok"] = not problemas
    if problemas:
        raise VerificacionFallida(
            "El artefacto NO pasa la verificacion:\n  - " + "\n  - ".join(problemas)
        )
    return resumen


def _verificar_tokenizer(empotrado: str, ruta_fuente: Path) -> list[str]:
    """Reconstruye el tokenizer desde el blob empotrado y compara ids.

    Comprueba lo que un `vocab.json + merges.txt` perderia en silencio: que el
    `post_processor` sigue ahi. Se hace por doble via —paridad frente al fichero
    fuente y comprobacion explicita de que las secuencias no quedan truncadas—
    porque el fallo que se persigue es *silencioso*.
    """
    try:
        from tokenizers import Tokenizer  # noqa: PLC0415
    except ImportError:
        return [
            "no se pudo importar 'tokenizers': la paridad de ids del tokenizer NO se ha "
            "verificado (instala tokenizers==0.23.1 y repite --verify)."
        ]

    problemas: list[str] = []
    try:
        desde_str = Tokenizer.from_str(empotrado)
    except Exception as exc:  # noqa: BLE001 - la excepcion viene de Rust
        return [f"Tokenizer.from_str() falla sobre el blob empotrado: {exc}"]
    desde_fichero = Tokenizer.from_file(str(ruta_fuente))

    for nombre, texto in CASOS_TOKENIZER:
        ids_a = desde_str.encode(texto).ids
        ids_b = desde_fichero.encode(texto).ids
        if ids_a != ids_b:
            problemas.append(f"paridad de ids rota en el caso {nombre!r}")
        if not ids_a:
            problemas.append(f"el caso {nombre!r} produce cero tokens")

    # CANARIO DEL post_processor. En Qwen3-Embedding cada secuencia termina en
    # <|endoftext|> (id 151643). Si ese id desaparece, el tokenizer sigue
    # "funcionando", el condicionamiento del texto cambia y NADA avisa: es
    # exactamente el fallo silencioso que provoca sustituir tokenizer.json por
    # vocab.json + merges.txt.
    #
    # La comprobacion se hace en dos niveles para que valga tanto en produccion
    # como sobre el tokenizer en miniatura del --selftest, que legitimamente no
    # tiene post_processor:
    #   (a) PARIDAD: si el tokenizer FUENTE anade el sufijo y el empotrado no,
    #       es un fallo duro (se ha perdido algo al empotrarlo);
    #   (b) CANARIO DE QWEN3: si el vocabulario es el de Qwen3-Embedding
    #       (<|endoftext|> == 151643) y NO hay sufijo, es un fallo duro aunque
    #       la paridad cuadre: significa que el blob no es el tokenizer.json
    #       completo.
    eos = desde_str.token_to_id("<|endoftext|>")
    if eos is not None:
        ids_empotrado = desde_str.encode("hola mundo").ids
        ids_fuente = desde_fichero.encode("hola mundo").ids
        sufijo_empotrado = bool(ids_empotrado) and ids_empotrado[-1] == eos
        sufijo_fuente = bool(ids_fuente) and ids_fuente[-1] == eos
        if sufijo_fuente and not sufijo_empotrado:
            problemas.append(
                f"el tokenizer EMPOTRADO no anade <|endoftext|> ({eos}) y el fuente si: "
                "se ha perdido el post_processor al empotrarlo."
            )
        elif not sufijo_fuente and eos == 151643:
            problemas.append(
                "el blob del tokenizer tiene el vocabulario de Qwen3-Embedding "
                "(<|endoftext|> == 151643) pero NO anade el sufijo: no es el tokenizer.json "
                "completo. Ver el aviso del docstring: vocab.json+merges.txt pierde el "
                "post_processor y es un fallo SILENCIOSO."
            )

    # Lote con relleno: ejercita el padding, que es camino distinto al de
    # `encode()` suelto.
    try:
        pad_id = eos if eos is not None else 0
        for tok in (desde_str, desde_fichero):
            tok.enable_padding(pad_id=pad_id, pad_token="<|endoftext|>")
        lote = [texto for _nombre, texto in CASOS_TOKENIZER[:3]]
        lote_a = [e.ids for e in desde_str.encode_batch(lote)]
        lote_b = [e.ids for e in desde_fichero.encode_batch(lote)]
        if lote_a != lote_b:
            problemas.append("paridad de ids rota en el lote con relleno")
        if len({len(x) for x in lote_a}) != 1:
            problemas.append("el relleno del lote no iguala longitudes")
    except Exception as exc:  # noqa: BLE001 - la excepcion viene de Rust
        problemas.append(f"fallo al ejercitar el lote con relleno: {exc}")

    return problemas


# --------------------------------------------------------------------------- #
# Seccion 8 — selftest sobre un arbol upstream sintetico
# --------------------------------------------------------------------------- #

def ejecutar_selftest(*, silencioso: bool = False) -> dict[str, Any]:
    """Ciclo completo build + verify sobre un arbol en miniatura.

    Es la prueba automatizable sin mover 6 GB: monta en un directorio temporal
    un arbol con la misma FORMA que el real (tres safetensors BF16 con los
    prefijos correctos, tres config.json, el tokenizer y un `.pt` generado por el
    propio test con `torch.save`) y lo pasa por el fusor entero.

    El `.pt` se genera aqui con `torch.save` a proposito: escribir un pickle es
    seguro, lo peligroso es *leerlo*. Y leerlo es justamente lo que se quiere
    ejercitar, por el camino auditado.
    """
    torch = _importar_torch()
    from safetensors.torch import save_file  # noqa: PLC0415

    with tempfile.TemporaryDirectory(prefix="build_artifact_selftest_") as tmp:
        raiz = Path(tmp)
        upstream = raiz / "upstream"
        (upstream / REL_ACESTEP_WEIGHTS[0]).mkdir(parents=True)
        (upstream / REL_QWEN3_WEIGHTS[0]).mkdir(parents=True)
        (upstream / REL_VAE_WEIGHTS[0]).mkdir(parents=True)

        def bf16(*forma: int) -> Any:
            # Valores deterministas y de magnitud realista (max|w| ~ 5) para que
            # las guardias numericas hagan un recorrido con sentido: incluye un
            # subnormal de fp16 y un valor que hace flush-to-zero.
            n = math.prod(forma)
            plano = torch.linspace(-5.0, 5.0, steps=n, dtype=torch.float32)
            plano[0] = 1e-6      # subnormal en fp16
            plano[-1] = 1e-12    # flush-to-zero en fp16
            return plano.reshape(*forma).to(torch.bfloat16)

        pesos_dit = {
            "decoder.layers.0.weight": bf16(8, 16),
            "decoder.layers.0.bias": bf16(8),
            "encoder.proj.weight": bf16(4, 8),
            "tokenizer.codebook": bf16(4, 4),
            "detokenizer.proj.weight": bf16(4, 4),
            "null_condition_emb": bf16(2, 4),
        }
        pesos_te = {
            "embed_tokens.weight": bf16(32, 8),
            "layers.0.input_layernorm.weight": bf16(8),
            "norm.weight": bf16(8),
        }
        pesos_vae = {
            "decoder.block.0.conv.weight": bf16(4, 4, 3),
            "decoder.block.0.conv.bias": bf16(4),
            "encoder.block.0.conv.weight": bf16(4, 4, 3),
        }
        save_file(pesos_dit, str(upstream.joinpath(*REL_ACESTEP_WEIGHTS)), metadata={"format": "pt"})
        save_file(pesos_te, str(upstream.joinpath(*REL_QWEN3_WEIGHTS)), metadata={"format": "pt"})
        save_file(pesos_vae, str(upstream.joinpath(*REL_VAE_WEIGHTS)), metadata={"format": "pt"})

        # Configs: bytes arbitrarios pero JSON valido, y con un espaciado raro a
        # proposito para que el round-trip byte a byte de --verify sea
        # significativo (si alguien reformatease, saltaria).
        upstream.joinpath(*REL_ACESTEP_CONFIG).write_bytes(b'{\n  "model_type" :  "acestep_v15"\n}\n')
        upstream.joinpath(*REL_QWEN3_CONFIG).write_bytes(b'{\n  "model_type" :  "qwen3"\n}\n')
        upstream.joinpath(*REL_VAE_CONFIG).write_bytes(b'{\n  "sampling_rate" :  48000\n}\n')
        upstream.joinpath(*REL_QWEN3_TOKENIZER_CONFIG).write_bytes(b'{"tokenizer_class":"Qwen2Tokenizer"}')
        upstream.joinpath(*REL_QWEN3_SPECIAL_TOKENS).write_bytes(b'{"eos_token":"<|endoftext|>"}')

        # Tokenizer real en miniatura: se serializa con la propia biblioteca para
        # que `Tokenizer.from_str` del --verify tenga algo valido que reconstruir.
        try:
            from tokenizers import Tokenizer, models, pre_tokenizers  # noqa: PLC0415

            vocabulario = {"<|endoftext|>": 0, "<unk>": 1}
            for i, palabra in enumerate(
                ["the", "quick", "brown", "fox", "a", "b", "c", "d", "mas", "texto",
                 "literal", "fin", "lo-fi", "beats", "verse", "90", "bpm", "minor"],
                start=2,
            ):
                vocabulario[palabra] = i
            tok = Tokenizer(models.WordLevel(vocab=vocabulario, unk_token="<unk>"))
            tok.pre_tokenizer = pre_tokenizers.Whitespace()
            upstream.joinpath(*REL_QWEN3_TOKENIZER).write_bytes(tok.to_str().encode("utf-8"))
            tokenizer_disponible = True
        except ImportError:
            upstream.joinpath(*REL_QWEN3_TOKENIZER).write_bytes(b'{"version":"1.0"}')
            tokenizer_disponible = False

        # `.pt` en cuarentena sintetico, generado con torch.save para ejercitar el
        # conversor por el camino auditado.
        cuarentena = raiz / "quarantine"
        cuarentena.mkdir()
        ruta_pt = cuarentena / "silence_latent.pt"
        forma_latente = (1, 4, 8)
        latente = torch.arange(math.prod(forma_latente), dtype=torch.float32).reshape(*forma_latente)
        torch.save(latente, str(ruta_pt))

        rutas = Rutas(
            upstream_root=upstream,
            quarantine_pt=ruta_pt,
            licenses_dir=raiz / "provenance",  # ausente a proposito: ejercita el aviso
        )
        expectativas = Expectativas(
            tensores_dit=len(pesos_dit),
            tensores_text_encoder=len(pesos_te),
            tensores_vae_decoder=sum(1 for k in pesos_vae if k.startswith("decoder.")),
            tensores_vae_encoder=sum(1 for k in pesos_vae if k.startswith("encoder.")),
            latente_shape=forma_latente,
            latente_sha256=None,  # se calcula sobre el fichero sintetico
        )

        salida = raiz / "out" / "ace_step_1_5.safetensors"
        registro = construir_artefacto(
            rutas,
            salida,
            incluir_vae_encoder=False,
            expectativas=expectativas,
            built_at="2026-01-01T00:00:00Z",
            permitir_disco_sistema=True,  # el tmpdir vive en C:; son unos KB
            silencioso=silencioso,
        )

        resumen = verificar_artefacto(
            salida,
            rutas,
            incluir_vae_encoder=False,
            expectativas=Expectativas(
                tensores_dit=expectativas.tensores_dit,
                tensores_text_encoder=expectativas.tensores_text_encoder,
                tensores_vae_decoder=expectativas.tensores_vae_decoder,
                tensores_vae_encoder=expectativas.tensores_vae_encoder,
                latente_shape=forma_latente,
                latente_sha256=registro["manifest"]["silence_latent"]["storage_sha256"],
            ),
            silencioso=silencioso,
        )

        # Determinismo: mismas entradas + misma --built-at -> mismos bytes.
        salida2 = raiz / "out2" / "ace_step_1_5.safetensors"
        registro2 = construir_artefacto(
            rutas,
            salida2,
            incluir_vae_encoder=False,
            expectativas=expectativas,
            built_at="2026-01-01T00:00:00Z",
            permitir_disco_sistema=True,
            silencioso=True,
        )
        if registro2["artifact"]["sha256"] != registro["artifact"]["sha256"]:
            raise BuildError(
                "Dos builds con las mismas entradas y la misma --built-at han dado hashes "
                "distintos: el fusor ha dejado de ser determinista."
            )

        # El pickle sintetico manipulado tiene que ser RECHAZADO. Se comprueba el
        # camino de error, no solo el feliz: una lista blanca que nunca ha
        # rechazado nada no esta verificada.
        rechazos = _selftest_rechazos(ruta_pt, raiz)

        return {
            "artifact_sha256": registro["artifact"]["sha256"],
            "artifact_bytes": registro["artifact"]["bytes"],
            "tensors": registro["artifact"]["tensors"],
            "verify": resumen,
            "deterministic": True,
            "tokenizer_checked": tokenizer_disponible,
            "pickle_rejections": rechazos,
            "warnings": registro["warnings"],
        }


def _selftest_rechazos(ruta_pt: Path, raiz: Path) -> dict[str, str]:
    """Comprueba que el auditor de pickles RECHAZA lo que tiene que rechazar.

    Tres casos, cada uno atacando una capa distinta:
      * `opcode_letal`   -> un `data.pkl` con `GLOBAL os system` + `REDUCE`
                            (la capa de callables permitidos);
      * `miembro_deflate`-> el mismo ZIP con un miembro comprimido
                            (la capa de estructura del contenedor);
      * `sha_distinto`   -> el fichero legitimo contra un SHA-256 que no cuadra
                            (la capa de integridad).
    """
    resultados: dict[str, str] = {}
    with zipfile.ZipFile(ruta_pt) as zf:
        contenido = {n: zf.read(n) for n in zf.namelist()}
    nombre_pkl = next(n for n in contenido if n.endswith("data.pkl"))

    # (1) pickle hostil: importa os.system y lo reduce. Nunca se ejecuta; lo que
    # se comprueba es que el auditor lo para en seco.
    hostil = raiz / "hostil.pt"
    malicioso = b"\x80\x02cos\nsystem\nq\x00X\x03\x00\x00\x00dirq\x01\x85q\x02Rq\x03."
    with zipfile.ZipFile(hostil, "w", zipfile.ZIP_STORED) as zf:
        for nombre, datos in contenido.items():
            zf.writestr(nombre, malicioso if nombre == nombre_pkl else datos)
    try:
        convertir_latente_en_cuarentena(hostil, shape_esperada=(1, 4, 8), sha256_esperado=None)
        raise BuildError("El auditor ACEPTO un pickle que invoca os.system. Esto es un fallo grave.")
    except PickleRechazado as exc:
        resultados["opcode_letal"] = str(exc).splitlines()[0]

    # (2) miembro comprimido.
    comprimido = raiz / "comprimido.pt"
    with zipfile.ZipFile(comprimido, "w") as zf:
        for nombre, datos in contenido.items():
            zf.writestr(
                nombre,
                datos,
                compress_type=zipfile.ZIP_DEFLATED if nombre.endswith("/data/0") else zipfile.ZIP_STORED,
            )
    try:
        convertir_latente_en_cuarentena(comprimido, shape_esperada=(1, 4, 8), sha256_esperado=None)
        raise BuildError("El auditor ACEPTO un ZIP con miembros comprimidos.")
    except PickleRechazado as exc:
        resultados["miembro_deflate"] = str(exc).splitlines()[0]

    # (3) hash del almacen que no cuadra.
    try:
        convertir_latente_en_cuarentena(ruta_pt, shape_esperada=(1, 4, 8), sha256_esperado="00" * 32)
        raise BuildError("El auditor ACEPTO un almacen con SHA-256 distinto del esperado.")
    except PickleRechazado as exc:
        resultados["sha_distinto"] = str(exc).splitlines()[0]

    return resultados


# --------------------------------------------------------------------------- #
# Seccion 9 — informe por consola
# --------------------------------------------------------------------------- #

def imprimir_plan(plan: PlanFusion, cabecera_bytes: int) -> None:
    """Informe de `--dry-run`: recuentos y tamano EXACTO, sin escribir nada.

    El tamano es exacto —no aproximado— porque el manifiesto tiene longitud fija
    y las guardias numericas van en ancho fijo: la cabecera del dry-run mide
    exactamente lo mismo que la del build real.
    """
    total = 8 + cabecera_bytes + plan.bytes_datos
    print(f"[{TASK}/{TOOL}] PLAN DE FUSION (dry-run: no se escribe nada)")
    print()
    print("## Recuentos por prefijo")
    print()
    for etiqueta, clave in (
        ("dit.*", "dit"),
        ("text_encoder.*", "text_encoder"),
        ("vae.decoder.*", "vae_decoder"),
        ("vae.encoder.*", "vae_encoder"),
        ("aux.*", "aux"),
    ):
        bytes_prefijo = sum(
            e.nbytes for e in plan.entradas
            if e.clave.startswith(
                {"dit": PREFIJO_DIT, "text_encoder": PREFIJO_TEXT_ENCODER,
                 "vae_decoder": "vae.decoder.", "vae_encoder": "vae.encoder.",
                 "aux": PREFIJO_AUX}[clave]
            )
        )
        print(f"  {etiqueta:<20} {plan.recuentos[clave]:>5} tensores  {bytes_prefijo / 2**20:>10.1f} MiB")
    print(f"  {'TOTAL':<20} {plan.recuentos['total']:>5} tensores")
    print()
    print("## Tamano")
    print()
    print(f"  cabecera JSON + 8 B de longitud : {8 + cabecera_bytes:>15} B")
    print(f"  bloque de datos                 : {plan.bytes_datos:>15} B")
    print(f"  FICHERO TOTAL                   : {total:>15} B  ({total / 2**30:.3f} GiB)")
    print()
    print("## Blobs auxiliares")
    print()
    for entrada in plan.entradas:
        if entrada.clave.startswith(PREFIJO_AUX):
            print(f"  {entrada.clave:<44} {entrada.dtype_salida:<4} {list(entrada.shape)}")
    print()
    print("## Latente de silencio (auditoria del pickle)")
    print()
    aud = plan.latente.auditoria
    print(f"  protocolo         : {aud.protocolo}")
    print(f"  opcodes           : {aud.opcodes}")
    print(f"  imports (GLOBAL)  : {', '.join(aud.globals_vistos)}")
    print(f"  REDUCE / BINPERSID: {aud.reduce} / {aud.binpersid}")
    print(f"  sha256 del almacen: {plan.latente.sha256_almacen}")
    print(f"  forma / strides   : {list(plan.latente.shape)} / {list(plan.latente.strides)}")
    print()
    if plan.avisos:
        print("## Avisos")
        print()
        for aviso in plan.avisos:
            print(f"  - {aviso}")
        print()


# --------------------------------------------------------------------------- #
# Seccion 10 — CLI
# --------------------------------------------------------------------------- #

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_artifact.py",
        description=(
            "Fusor offline del artefacto ace_step_1_5.safetensors (T-03/T-05). Lee las "
            "cabeceras de los tres safetensors upstream, convierte bfloat16 -> float16 por "
            "streaming, empotra configs y tokenizer como tensores U8 y convierte el latente "
            "en cuarentena sin ejecutar su pickle."
        ),
        epilog=(
            "AVISO DE GATE: CLAUDE.md establece que G2 legal bloquea TODO el desarrollo. "
            "Este script produce un artefacto de pesos DERIVADO de tres modelos de terceros; "
            "ejecutarlo sobre los pesos reales es una decision del propietario."
        ),
    )
    parser.add_argument("--upstream-root", default=DEFAULT_UPSTREAM_ROOT,
                        help=f"Arbol upstream de la revision fijada. Defecto: {DEFAULT_UPSTREAM_ROOT}")
    parser.add_argument("--quarantine-pt", default=DEFAULT_QUARANTINE_PT,
                        help=f"Latente de silencio en cuarentena. Defecto: {DEFAULT_QUARANTINE_PT}")
    parser.add_argument("--licenses-dir", default=DEFAULT_LICENSES_DIR,
                        help=f"Fichas de licencia locales. Defecto: {DEFAULT_LICENSES_DIR}")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help=f"Artefacto de salida. Defecto: {DEFAULT_OUT}")
    parser.add_argument("--provenance-out", default=None,
                        help="JSON de procedencia. Defecto: <out sin extension>.provenance.json")
    parser.add_argument("--include-vae-encoder", action="store_true",
                        help="Incluye vae.encoder.* (183 tensores, +161 MiB). Por defecto NO: "
                             "no hace falta para text2music y engorda el pico de carga.")
    parser.add_argument("--built-at", default=None,
                        help="Marca UTC 'AAAA-MM-DDTHH:MM:SSZ'. Fijarla hace el build "
                             "reproducible byte a byte; por defecto se usa el reloj.")
    parser.add_argument("--allow-system-drive", action="store_true",
                        help="Permite escribir en el disco de sistema. Por defecto se aborta.")
    parser.add_argument("--quiet", action="store_true", help="Silencia la traza de progreso.")

    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true",
                      help="Imprime el plan, los recuentos y el tamano exacto sin escribir.")
    modo.add_argument("--verify", action="store_true",
                      help="Reabre el artefacto de --out y lo valida contra las fuentes.")
    modo.add_argument("--selftest", action="store_true",
                      help="Ciclo build+verify sobre un arbol upstream sintetico en miniatura.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.selftest:
            resultado = ejecutar_selftest(silencioso=args.quiet)
            print(f"[{TASK}/{TOOL}] SELFTEST OK")
            print(f"  tensores            : {resultado['tensors']}")
            print(f"  bytes               : {resultado['artifact_bytes']}")
            print(f"  sha256              : {resultado['artifact_sha256']}")
            print(f"  determinista        : {resultado['deterministic']}")
            print(f"  tokenizer verificado: {resultado['tokenizer_checked']}")
            print("  rechazos del auditor de pickles:")
            for caso, motivo in resultado["pickle_rejections"].items():
                print(f"    - {caso}: {motivo[:120]}")
            return EXIT_OK

        rutas = Rutas(
            upstream_root=Path(args.upstream_root),
            quarantine_pt=Path(args.quarantine_pt),
            licenses_dir=Path(args.licenses_dir),
        )
        salida = Path(args.out)
        expectativas = Expectativas()

        if args.verify:
            resumen = verificar_artefacto(
                salida,
                rutas,
                incluir_vae_encoder=args.include_vae_encoder,
                expectativas=expectativas,
                silencioso=args.quiet,
            )
            print(f"[{TASK}/{TOOL}] VERIFICACION OK: {salida}")
            print(f"  bytes    : {resumen['bytes']}")
            print(f"  recuentos: {resumen['counts']}")
            print(f"  manifiesto schema: {resumen.get('manifest_schema_version')}")
            return EXIT_OK

        if args.dry_run:
            plan = construir_plan(
                rutas,
                incluir_vae_encoder=args.include_vae_encoder,
                expectativas=expectativas,
            )
            guardias = GuardiasNumericas()
            built_at = _validar_marca_tiempo(args.built_at) if args.built_at else _ahora_utc()
            manifiesto = construir_manifiesto(plan, built_at=built_at, guardias=guardias)
            cabecera = serializar_cabecera(plan.entradas, _manifiesto_plano(manifiesto, plan))
            imprimir_plan(plan, len(cabecera))
            return EXIT_OK

        built_at = _validar_marca_tiempo(args.built_at) if args.built_at else _ahora_utc()
        if args.built_at is None:
            _log(
                "sin --built-at: el artefacto llevara el reloj actual y su SHA-256 cambiara "
                "en cada build aunque las entradas sean identicas.",
                silencioso=args.quiet,
            )

        registro = construir_artefacto(
            rutas,
            salida,
            incluir_vae_encoder=args.include_vae_encoder,
            expectativas=expectativas,
            built_at=built_at,
            permitir_disco_sistema=args.allow_system_drive,
            silencioso=args.quiet,
        )

        destino_json = (
            Path(args.provenance_out)
            if args.provenance_out
            else salida.with_name(salida.stem + ".provenance.json")
        )
        escribir_procedencia(registro, destino_json)

        guardias = registro["manifest"]["conversion_guards"]
        print()
        print(f"[{TASK}/{TOOL}] ARTEFACTO CONSTRUIDO")
        print(f"  fichero    : {salida}")
        print(f"  tensores   : {registro['artifact']['tensors']}")
        print(f"  bytes      : {registro['artifact']['bytes']}")
        print(f"  procedencia: {destino_json}")
        print()
        print("  Guardias numericas de la conversion bfloat16 -> float16:")
        print(f"    max_abs_weight      : {float(guardias['guard_max_abs_weight']):.5f}")
        print(f"    overflow_count      : {int(guardias['guard_overflow_count'])}")
        print(f"    subnormal_count     : {int(guardias['guard_subnormal_count'])}")
        print(f"    flush_to_zero_count : {int(guardias['guard_flush_to_zero_count'])}")
        print(f"    elementos convertidos: {int(guardias['guard_elements'])}")
        print()
        print("  SHA-256 del artefacto (exportar como ACE_STEP_WEIGHTS_SHA256):")
        print(f"    {registro['artifact']['sha256']}")
        print()
        for aviso in registro["warnings"]:
            print(f"  AVISO: {aviso}")
        print(f"  Siguiente paso: python {TOOL}.py --verify --out {salida}")
        return EXIT_OK

    except VerificacionFallida as exc:
        print(f"\n[{TASK}/{TOOL}] ERROR DE VERIFICACION: {exc}", file=sys.stderr)
        return EXIT_VERIFY
    except PickleRechazado as exc:
        print(f"\n[{TASK}/{TOOL}] PICKLE RECHAZADO (D-14): {exc}", file=sys.stderr)
        return EXIT_GUARD
    except BuildError as exc:
        print(f"\n[{TASK}/{TOOL}] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except OSError as exc:
        # Red de seguridad para fallos de sistema de ficheros que no han pasado
        # por las puertas de arriba (permisos, unidad desconectada, disco lleno
        # a mitad de escritura). Se reporta como error de configuracion, no como
        # traza sin manejar.
        print(f"\n[{TASK}/{TOOL}] ERROR DE E/S: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except KeyboardInterrupt:  # pragma: no cover - interactivo
        print(f"\n[{TASK}/{TOOL}] Interrumpido por el usuario.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
