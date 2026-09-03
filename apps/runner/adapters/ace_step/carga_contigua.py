"""Carga contigua del artefacto `safetensors` (arregla el defecto de `vram_load`).

POR QUE EXISTE ESTE FICHERO
---------------------------
Hasta el 2026-09-02 el adapter cargaba los pesos con
`safetensors.torch.load_file(ruta, device="cpu")`, que **mapea** el fichero, y el
shim materializaba despues **tensor a tensor** (`clone()` o `.to(cuda)`). Sobre
el bind mount de Docker eso son fallos de pagina de 4 KiB servidos por el
sistema de ficheros del host, y la tasa MEDIDA es de ~11 MiB/s:

    load_file(device='cpu')  (solo mapea)        32,51 s
    POR TENSOR vae.decoder.          161,0 MiB en  13,58 s ->  11,9 MiB/s
    POR TENSOR dit.tokenizer.        200,3 MiB en  18,32 s ->  10,9 MiB/s
    POR TENSOR dit.detokenizer.      200,3 MiB en  17,33 s ->  11,6 MiB/s

Con 7.181 MiB de artefacto eso son los **709,08 s de `vram_load`** que rompian la
promesa de arranque en frio de 2-6 min de `ui-design.md`.

QUE HACE ESTE MODULO, Y POR QUE ASI
-----------------------------------
Los tensores de un `safetensors` estan **uno detras de otro** en el bloque de
datos. Comprobado sobre el artefacto real (1.492 tensores, 7.529.590.739 B): la
cabecera declara **cero huecos** y los componentes salen en tramos contiguos
perfectos (`dit.decoder` 0..3.150.917.760, `dit.detokenizer`, `dit.encoder`,
`dit.tokenizer`, `text_encoder`, `vae.decoder`, `lm`, `aux`). Aun asi el plan
**no lo supone**: se recalcula desde la cabecera en cada arranque y se corta un
tramo nuevo en cuanto `fin_anterior != inicio_actual`.

Asi que se lee el **rango entero de un tramo de una vez** (`readinto` sobre un
buffer propio) y los tensores se construyen como **vistas** de ese buffer, sin
una sola copia adicional. MEDIDO en el mismo contenedor, sobre rangos que nadie
habia tocado (si se mide dos veces el mismo rango, la segunda sale de la cache de
paginas y la comparacion es mentira):

    off=    0 MiB  n=512 MiB  blk= 8 MiB  hilos=1   4,97 s -> 103,1 MiB/s
    off=  512 MiB  n=512 MiB  blk=32 MiB  hilos=1   4,46 s -> 114,7 MiB/s
    off= 2048 MiB  n=512 MiB  blk= 8 MiB  hilos=1   4,30 s -> 119,2 MiB/s

Diez veces la tasa por tensor. El techo es fisico: el mismo rango leido **desde
Windows**, fuera de Docker, da 141-144 MiB/s (D: es un disco mecanico), asi que
el bind mount ya no es el cuello de botella.

RESULTADO EN PRODUCCION (2026-09-02, GTX 1070, artefacto de 7.181 MiB con
planificador, misma orden y misma pista de 25 s):

                         load_file    contigua
    lectura del artefacto  ~610 s      60,4 s   (118,8 MiB/s de media)
    vram_load              642,0 s     72,9 s
    warm-up                 39,1 s     36,8 s
    ARRANQUE EN FRIO       681,1 s    109,7 s
    generacion de 25 s     127,8 s    110,6 s

Lo que NO hay que hacer, tambien medido: paralelizar. Con 4-32 hilos la tasa se
**hunde** a 12-28 MiB/s porque el disco es mecanico y los hilos lo convierten en
acceso aleatorio. Se lee con **un solo hilo, hacia delante**, y los tramos se
recorren en orden fisico creciente para no retroceder nunca.

DOS DESTINOS, DOS FORMAS DE MATERIALIZAR
----------------------------------------
El reparto por componente del shim no cambia: `dit.decoder` residente en VRAM y
el resto en RAM. Lo que cambia es **donde aterrizan los bytes**:

* **tramo a CPU** — un tensor `uint8` del tamano exacto del tramo, `readinto`
  sobre su memoria, y los tensores del artefacto son vistas de el. RAM anonima
  desde el primer byte, que es justo lo que el shim necesitaba conseguir
  clonando: un tensor mapeado se relee del disco pagina a pagina en **cada**
  subida a VRAM (42,91 s frente a 0,43 s, medido en `text_conditioning`).
* **tramo a GPU** — un unico buffer de bytes en VRAM y una escalera
  `disco -> buffer de escala de 32 MiB -> copia H2D`. El pico de RAM del anfitrion
  es el buffer de escala, no los 3.005 MiB del `dit.decoder`, que en un contenedor
  de 7,9 GiB es la diferencia entre cargar y morir por OOM. La copia H2D no es el
  cuello de botella: 2.469 MiB/s pageable medidos, 20 veces la tasa del disco.

CONTRATO CON EL SHIM
--------------------
El diccionario que se devuelve es un `dict` de verdad (el shim comprueba
`isinstance(state_dict, dict)`) con un atributo extra,
`tensores_materializados = True`. Ese atributo le dice al shim que **no clone**:
los tensores ya estan en memoria anonima. Clonarlos seria duplicar cada
componente sin ganar nada y, en el caso de `dit.decoder`, +3.005 MiB de VRAM
inexistentes.

INVARIANTES
-----------
* **Solo `safetensors` (D-14)**. Aqui no hay `pickle` ni `torch.load`: se lee la
  cabecera JSON (8 bytes de longitud + JSON) y bytes crudos. Ni un opcode.
  La puerta de entrada sigue siendo `contracts.assert_safetensors()`, que el
  adapter llama **antes** de invocar a este modulo.
* **Nada de red, nada de `trust_remote_code`.**
* El guardarrail de VRAM se mantiene: antes de asignar un solo byte en la tarjeta
  se comprueba que cabe, y se aborta con un mensaje explicito en vez de dejar que
  el driver lance un OOM (que deja el asignador de PyTorch inservible).
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any

_LOG = logging.getLogger("ace_step.carga")

_MIB = 1048576

#: Tope de un tramo. No es una restriccion de correccion: sirve para no pedirle
#: al asignador un unico bloque de 4 GiB y para que un tensor descartado no
#: mantenga vivo medio artefacto. Un tensor mas grande que el tope forma tramo
#: propio (jamas se parte un tensor).
TOPE_TRAMO_BYTES = 512 * _MIB

#: Tamano de cada `readinto`. Medido: de 1 a 32 MiB la tasa apenas cambia
#: (98 -> 109 MiB/s), asi que se elige el valor que menos memoria de escala
#: necesita para los tramos que van a la GPU.
BLOQUE_BYTES = 32 * _MIB

#: Prefijos que el shim deja residentes en VRAM. El adapter lo lee del **shim**
#: (`ace_step_shim.PREFIJOS_RESIDENTES_GPU`), no de aqui: esta constante es solo
#: el respaldo documental. `tests/test_carga_contigua.py` comprueba que ambas
#: coinciden, que es lo que impide que se separen con el tiempo.
PREFIJOS_RESIDENTES_GPU_ESPERADOS = ("dit.decoder.",)

#: Nombres de dtype de la especificacion de `safetensors` -> dtype de torch.
#: Se resuelven perezosamente porque este modulo tiene que poder importarse en
#: una maquina de desarrollo sin `torch`.
_NOMBRES_DTYPE = {
    "F64": "float64",
    "F32": "float32",
    "F16": "float16",
    "BF16": "bfloat16",
    "I64": "int64",
    "I32": "int32",
    "I16": "int16",
    "I8": "int8",
    "U8": "uint8",
    "BOOL": "bool",
}


class ArtefactoIlegible(RuntimeError):
    """La cabecera del artefacto no es la que este cargador sabe leer."""


class EstadoDelArtefacto(dict):
    """`dict` de tensores con la marca de que **ya estan materializados**.

    Es un `dict` de verdad y no un envoltorio: el shim comprueba
    `isinstance(state_dict, dict)` y consume el diccionario con `pop`. El unico
    anadido es el atributo de clase `tensores_materializados`, que el shim
    consulta con `getattr(..., False)` para saber que no tiene que clonar.
    """

    #: Los tensores viven en RAM/VRAM anonima, no en un mapeo del fichero.
    tensores_materializados = True
    #: SHA-256 hexadecimal del fichero ENTERO, calculado de paso durante la
    #: lectura si se pidio un `digestor`; `None` si no se pidio.
    sha256: str | None = None


@dataclass
class Tramo:
    """Rango contiguo del fichero que se lee de una sola vez, con un destino."""

    destino: str
    ini: int
    fin: int
    claves: list[str] = field(default_factory=list)

    @property
    def bytes(self) -> int:
        return self.fin - self.ini


def leer_cabecera(ruta: str) -> tuple[dict[str, Any], int]:
    """Devuelve `(cabecera, offset_del_bloque_de_datos)`.

    El formato es 8 bytes little-endian con la longitud del JSON, el JSON, y a
    continuacion los datos. **No hay deserializacion de objetos**: `json.loads`
    sobre texto y nada mas (D-14).
    """
    with open(ruta, "rb") as fichero:
        crudo = fichero.read(8)
        if len(crudo) != 8:
            raise ArtefactoIlegible(f"{ruta!r} no tiene ni la longitud de cabecera.")
        n = int.from_bytes(crudo, "little")
        if not 0 < n < 512 * _MIB:
            raise ArtefactoIlegible(
                f"Longitud de cabecera absurda en {ruta!r}: {n} bytes. No es un safetensors."
            )
        texto = fichero.read(n)
        if len(texto) != n:
            raise ArtefactoIlegible(f"Cabecera truncada en {ruta!r}.")
    try:
        cabecera = json.loads(texto.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtefactoIlegible(f"Cabecera ilegible en {ruta!r}: {exc}") from exc
    if not isinstance(cabecera, dict):
        raise ArtefactoIlegible(f"La cabecera de {ruta!r} no es un objeto JSON.")
    return cabecera, 8 + n


def _destino_de(clave: str, destinos: dict[str, str]) -> str:
    """Dispositivo de una clave segun el prefijo mas largo que case."""
    mejor = ""
    elegido = "cpu"
    for prefijo, dispositivo in destinos.items():
        if clave.startswith(prefijo) and len(prefijo) > len(mejor):
            mejor, elegido = prefijo, dispositivo
    return elegido


def planificar(
    cabecera: dict[str, Any],
    base: int,
    destinos: dict[str, str] | None = None,
    tope: int = TOPE_TRAMO_BYTES,
) -> list[Tramo]:
    """Agrupa los tensores en tramos **contiguos de verdad** con el mismo destino.

    No se supone que el fichero venga ordenado por componente: se ordena por
    `data_offsets` y se corta un tramo nuevo en cuanto (a) el destino cambia,
    (b) el rango deja de ser contiguo (`fin_anterior != inicio_actual`, o sea hay
    un hueco o un solape) o (c) el tramo llegaria al tope.

    Returns:
        Tramos en **orden fisico creciente**: recorrerlos en ese orden convierte
        toda la carga en una unica pasada hacia delante sobre el disco.
    """
    destinos = destinos or {}
    entradas = []
    for clave, meta in cabecera.items():
        if clave == "__metadata__":
            continue
        if not isinstance(meta, dict) or "data_offsets" not in meta:
            raise ArtefactoIlegible(f"Entrada de cabecera sin data_offsets: {clave!r}.")
        ini, fin = meta["data_offsets"]
        if not isinstance(ini, int) or not isinstance(fin, int) or fin < ini:
            raise ArtefactoIlegible(f"data_offsets invalidos en {clave!r}: {(ini, fin)!r}.")
        entradas.append((ini, fin, clave))
    if not entradas:
        raise ArtefactoIlegible("La cabecera no declara ni un tensor.")
    entradas.sort()

    tramos: list[Tramo] = []
    for ini, fin, clave in entradas:
        destino = _destino_de(clave, destinos)
        ultimo = tramos[-1] if tramos else None
        if (
            ultimo is not None
            and ultimo.destino == destino
            and ultimo.fin == base + ini            # contiguo de verdad
            and (base + fin) - ultimo.ini <= tope
        ):
            ultimo.fin = base + fin
            ultimo.claves.append(clave)
        else:
            tramos.append(Tramo(destino, base + ini, base + fin, [clave]))
    return tramos


def _numel(forma: list[int]) -> int:
    return math.prod(forma) if forma else 1


def _buffer(nbytes: int, dispositivo: Any, torch: Any) -> Any:
    """Buffer de bytes del tramo, **siempre** un tensor `uint8` de torch.

    Y no un `bytearray`, que seria lo obvio, por la alineacion: `bytearray` sale
    de `malloc`, que en un bloque grande devuelve `pagina + 16`, o sea 16 bytes de
    alineacion. El asignador de CPU de PyTorch alinea a **64**, que es lo que
    quieren los kernels vectorizados que van a ejecutar estos pesos (el
    planificador de 5 Hz corre en CPU: sus 1.264 MiB los recorre oneDNN en cada
    generacion). Sobre los tensores del artefacto real, el 99 % de los offsets
    relativos son multiplos de 64, asi que con una base alineada a 64 salen todos
    alineados a 64; con base+16 no lo estaria ninguno.
    """
    return torch.empty(nbytes, dtype=torch.uint8, device=torch.device(dispositivo))


def _vista_escritura(buf: Any) -> memoryview:
    """`memoryview` escribible sobre el buffer de CPU, para `readinto`."""
    return memoryview(buf.numpy())


def _tensor_desde_buffer(buf: Any, rel: int, meta: dict[str, Any], torch: Any) -> Any:
    """Reinterpreta `buf[rel:rel+tam]` como el tensor que declara la cabecera.

    Sin copiar: es una vista del mismo almacenamiento, tanto en RAM como en VRAM.
    Solo se copia si el offset esta **desalineado** respecto al tamano de
    elemento. En el artefacto real le pasa a UNO de los 1.492 tensores
    (`aux.silence_latent`, F32 de 3,84 MB detras de blobs U8 de longitud impar).
    """
    dtype = getattr(torch, _NOMBRES_DTYPE[meta["dtype"]])
    forma = list(meta["shape"])
    n = _numel(forma)
    tam = meta["data_offsets"][1] - meta["data_offsets"][0]
    if n == 0 or tam == 0:
        return torch.empty(forma, dtype=dtype, device=buf.device)
    elemento = tam // n
    plano = buf.narrow(0, rel, tam)
    if rel % elemento == 0:
        return plano.view(dtype).reshape(forma)
    # `Tensor.view(dtype)` aborta con offset desalineado; se copia a un tensor
    # nuevo, cuyo `storage_offset` es 0 por construccion.
    destino = torch.empty(n, dtype=dtype, device=buf.device)
    destino.view(torch.uint8).copy_(plano)
    return destino.reshape(forma)


def _exigir_vram(torch: Any, dispositivo: Any, necesarios: int) -> None:
    """Aborta ANTES de asignar si el tramo no cabe (mismo criterio que el shim).

    Capturar un `OutOfMemoryError` del driver no es una opcion: deja el asignador
    cacheante de PyTorch en un estado del que no se sale dentro del proceso.
    """
    dev = torch.device(dispositivo)
    if dev.type != "cuda":
        return
    libre, total = torch.cuda.mem_get_info(dev)
    disponible = libre + torch.cuda.memory_reserved(dev) - torch.cuda.memory_allocated(dev)
    if necesarios > disponible:
        raise RuntimeError(
            f"VRAM insuficiente para cargar los pesos residentes en {dev}.\n"
            f"  Necesarios: {necesarios / _MIB:.0f} MiB\n"
            f"  Disponibles: {disponible / _MIB:.0f} MiB (libres del driver "
            f"{libre / _MIB:.0f} MiB de {total / _MIB:.0f} MiB)\n"
            "La carga se aborta antes de asignar: un OOM del driver dejaria el "
            "asignador de PyTorch inservible para el resto del proceso."
        )


def cargar_contiguo(
    ruta: str,
    *,
    destinos: dict[str, str] | None = None,
    tope_tramo: int = TOPE_TRAMO_BYTES,
    bloque: int = BLOQUE_BYTES,
    digestor: Any = None,
) -> EstadoDelArtefacto:
    """Carga el artefacto leyendo cada tramo contiguo de una sola vez.

    Args:
        ruta: fichero `safetensors` ya validado por `contracts.assert_safetensors()`.
        destinos: prefijo -> dispositivo. Lo que no case va a CPU. En produccion
            es `{"dit.decoder.": "cuda:0"}`, que el adapter toma del propio shim.
        tope_tramo: tope de bytes por tramo (ver `TOPE_TRAMO_BYTES`).
        bloque: tamano de cada `readinto`.
        digestor: objeto tipo `hashlib.sha256()`. Si se da, se le pasan TODOS los
            bytes del fichero en orden (cabecera, tramos y cualquier hueco o cola
            que la cabecera no declare) y el resultado queda en `estado.sha256`.
            Es la verificacion de integridad a coste casi cero: recorrer 7,5 GB
            por el bind mount solo para hashearlos costaba 217 s por arranque
            (revision 2026-09-03), y esta lectura ya pasa por cada byte.

    Returns:
        `EstadoDelArtefacto`: un `dict` de tensores **ya materializados**.

    Raises:
        ArtefactoIlegible: la cabecera no es la de un `safetensors`.
        RuntimeError: no cabe en VRAM lo que se pidio residenciar en VRAM, o el
            fichero esta truncado.
    """
    import torch  # noqa: PLC0415  (perezoso: el modulo se importa sin GPU)

    cabecera, base = leer_cabecera(ruta)
    tam_fichero = os.path.getsize(ruta)
    tramos = planificar(cabecera, base, destinos, tope_tramo)
    fin_declarado = max(t.fin for t in tramos)
    if fin_declarado > tam_fichero:
        raise ArtefactoIlegible(
            f"La cabecera de {ruta!r} declara datos hasta el byte {fin_declarado} y el "
            f"fichero tiene {tam_fichero}. Esta truncado."
        )

    total_bytes = sum(t.bytes for t in tramos)
    bytes_gpu = sum(t.bytes for t in tramos if t.destino != "cpu")
    _LOG.info(
        "Carga contigua de %s: %.0f MiB en %d tramos (%d tensores); %.0f MiB directos a "
        "VRAM, %.0f MiB a RAM. Lectura secuencial de un solo hilo en bloques de %d MiB.",
        os.path.basename(ruta),
        total_bytes / _MIB,
        len(tramos),
        sum(len(t.claves) for t in tramos),
        bytes_gpu / _MIB,
        (total_bytes - bytes_gpu) / _MIB,
        bloque // _MIB,
    )
    if bytes_gpu:
        dispositivo_gpu = next(t.destino for t in tramos if t.destino != "cpu")
        _exigir_vram(torch, dispositivo_gpu, bytes_gpu)

    estado = EstadoDelArtefacto()
    escala: Any = None
    inicio = time.perf_counter()
    leidos = 0
    digerido = 0  # bytes del fichero ya pasados al digestor, en orden
    try:
        with open(ruta, "rb", buffering=0) as fichero:
            if digestor is not None:
                # La cabecera (longitud + JSON) tambien forma parte del hash.
                _digerir_rango(fichero, digestor, 0, base, bloque, ruta)
                digerido = base
            for tramo in tramos:
                t0 = time.perf_counter()
                if digestor is not None and tramo.ini > digerido:
                    # Hueco que la cabecera no cubre: no se carga, pero se hashea.
                    _digerir_rango(fichero, digestor, digerido, tramo.ini - digerido, bloque, ruta)
                fichero.seek(tramo.ini)
                buf = _buffer(tramo.bytes, tramo.destino, torch)
                if buf.device.type == "cpu":
                    _leer_en(fichero, _vista_escritura(buf), tramo.bytes, bloque, ruta, digestor)
                else:
                    if escala is None:
                        escala = _buffer(min(bloque, tramo.bytes), "cpu", torch)
                    _leer_a_dispositivo(fichero, buf, tramo.bytes, escala, ruta, digestor)
                if digestor is not None:
                    digerido = tramo.fin
                for clave in tramo.claves:
                    meta = cabecera[clave]
                    rel = base + meta["data_offsets"][0] - tramo.ini
                    estado[clave] = _tensor_desde_buffer(buf, rel, meta, torch)
                del buf
                dt = max(time.perf_counter() - t0, 1e-9)
                leidos += tramo.bytes
                _LOG.info(
                    "  tramo %-4s %10d..%-10d %8.1f MiB en %6.2f s -> %6.1f MiB/s "
                    "(%d tensores, %s)",
                    tramo.destino,
                    tramo.ini,
                    tramo.fin,
                    tramo.bytes / _MIB,
                    dt,
                    tramo.bytes / _MIB / dt,
                    len(tramo.claves),
                    tramo.claves[0],
                )
            if digestor is not None and digerido < tam_fichero:
                # Cola tras el ultimo tensor: tampoco se carga, pero cuenta.
                _digerir_rango(fichero, digestor, digerido, tam_fichero - digerido, bloque, ruta)
                digerido = tam_fichero
    except BaseException:
        # Un fallo a mitad no puede dejar buffers de VRAM huerfanos: el adapter
        # relanza y `_limpiar_carga_fallida()` cuenta con que aqui no queda nada.
        estado.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise

    if digestor is not None:
        estado.sha256 = digestor.hexdigest()
    total = time.perf_counter() - inicio
    _LOG.info(
        "Artefacto cargado: %.0f MiB en %.2f s -> %.1f MiB/s de media, %d tensores.%s",
        leidos / _MIB,
        total,
        leidos / _MIB / max(total, 1e-9),
        len(estado),
        _memoria_del_anfitrion(),
    )
    return estado


def _memoria_del_anfitrion() -> str:
    """Resumen de RAM libre y swap, para poder culpar al swap con datos.

    El planificador de 5 Hz corre **en CPU** y sus 1.264 MiB se recorren en cada
    generacion: si el contenedor empieza a paginar, se nota ahi antes que en
    ningun otro sitio. Sin esta linea, un warm-up lento es un misterio.
    """
    try:
        with open("/proc/meminfo", encoding="ascii") as fichero:
            campos = {}
            for linea in fichero:
                nombre, _, resto = linea.partition(":")
                campos[nombre] = int(resto.strip().split()[0])
    except (OSError, ValueError, IndexError):
        return ""
    usada_swap = campos.get("SwapTotal", 0) - campos.get("SwapFree", 0)
    return (
        f" RAM disponible {campos.get('MemAvailable', 0) / 1024:.0f} MiB, "
        f"cache {campos.get('Cached', 0) / 1024:.0f} MiB, "
        f"swap en uso {usada_swap / 1024:.0f} MiB."
    )


def _digerir_rango(fichero: Any, digestor: Any, ini: int, n: int, bloque: int, ruta: str) -> None:
    """Pasa al digestor los `n` bytes desde `ini`, sin conservarlos."""
    fichero.seek(ini)
    hechos = 0
    while hechos < n:
        trozo = fichero.read(min(bloque, n - hechos))
        if not trozo:
            raise ArtefactoIlegible(
                f"{ruta!r} termino antes de tiempo: faltan {n - hechos} bytes por hashear."
            )
        digestor.update(trozo)
        hechos += len(trozo)


def _leer_en(
    fichero: Any, vista: memoryview, n: int, bloque: int, ruta: str, digestor: Any = None
) -> None:
    """`readinto` secuencial del rango completo sobre un buffer propio."""
    hechos = 0
    while hechos < n:
        trozo = min(bloque, n - hechos)
        k = fichero.readinto(vista[hechos : hechos + trozo])
        if not k:
            raise ArtefactoIlegible(
                f"{ruta!r} termino antes de tiempo: faltan {n - hechos} bytes del tramo."
            )
        if digestor is not None:
            digestor.update(vista[hechos : hechos + k])
        hechos += k


def _leer_a_dispositivo(
    fichero: Any, destino: Any, n: int, escala: Any, ruta: str, digestor: Any = None
) -> None:
    """Escalera disco -> buffer de escala en RAM -> copia H2D, sin picos en RAM.

    El buffer de escala se reutiliza en todas las vueltas: el anfitrion nunca
    tiene mas de `escala.numel()` bytes del componente, aunque el componente ocupe
    3 GiB en la tarjeta. Sin esto, `dit.decoder` daria un pico de 3.005 MiB de RAM
    en un contenedor de 7,9 GiB que ya guarda 4.176 MiB de pesos.
    """
    vista = _vista_escritura(escala)
    hechos = 0
    while hechos < n:
        trozo = min(escala.numel(), n - hechos)
        k = fichero.readinto(vista[:trozo])
        if not k:
            raise ArtefactoIlegible(
                f"{ruta!r} termino antes de tiempo: faltan {n - hechos} bytes del tramo."
            )
        if digestor is not None:
            digestor.update(vista[:k])
        destino.narrow(0, hechos, k).copy_(escala.narrow(0, 0, k))
        hechos += k
