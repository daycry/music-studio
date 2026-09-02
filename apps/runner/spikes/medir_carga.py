"""Medicion de DONDE se va el tiempo al cargar el artefacto (defecto `vram_load`).

No optimiza nada: solo mide, sobre el fichero real y dentro del contenedor, la
velocidad de las dos formas de leer los pesos:

  * **por tensor** — la ruta actual: `load_file(..., device="cpu")` mapea el
    fichero y despues cada tensor se materializa uno a uno (`clone()` o
    `.to(cuda)`). Cada tensor son fallos de pagina sobre el bind mount.
  * **contigua** — la ruta propuesta: un `readinto` del rango completo de un
    componente sobre un buffer propio.

Los grupos que se miden son **disjuntos** a proposito: si se midiera el mismo
rango dos veces, la segunda saldria de la cache de paginas del sistema y la
comparacion seria mentira.

Uso (dentro del contenedor):
    python /work/spikes/medir_carga.py --pesos /weights/ace_step_1_5_lm.safetensors
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

_MIB = 1048576.0

ELEMENTOS = {
    "F64": 8, "F32": 4, "F16": 2, "BF16": 2,
    "I64": 8, "I32": 4, "I16": 2, "I8": 1, "U8": 1, "BOOL": 1,
}


def leer_cabecera(ruta: str) -> tuple[dict[str, Any], int]:
    """8 bytes de longitud + JSON. Sin pickle, sin torch."""
    with open(ruta, "rb") as fichero:
        n = int.from_bytes(fichero.read(8), "little")
        return json.loads(fichero.read(n).decode("utf-8")), 8 + n


def rango(cabecera: dict[str, Any], prefijo: str, base: int) -> tuple[int, int, list[str]]:
    claves = [k for k in cabecera if k != "__metadata__" and k.startswith(prefijo)]
    ini = min(cabecera[k]["data_offsets"][0] for k in claves)
    fin = max(cabecera[k]["data_offsets"][1] for k in claves)
    claves.sort(key=lambda k: cabecera[k]["data_offsets"][0])
    return base + ini, base + fin, claves


def medir_contiguo(ruta: str, ini: int, fin: int, bloque: int, etiqueta: str) -> float:
    n = fin - ini
    buf = bytearray(n)
    vista = memoryview(buf)
    t0 = time.perf_counter()
    with open(ruta, "rb", buffering=0) as fichero:
        fichero.seek(ini)
        leidos = 0
        while leidos < n:
            trozo = min(bloque, n - leidos)
            k = fichero.readinto(vista[leidos : leidos + trozo])
            if not k:
                raise RuntimeError("EOF inesperado")
            leidos += k
    dt = time.perf_counter() - t0
    print(f"  CONTIGUO  {etiqueta:18s} {n/_MIB:8.1f} MiB en {dt:7.2f} s "
          f"-> {n/_MIB/dt:8.1f} MiB/s (bloque {bloque//1024} KiB)")
    del vista, buf
    return dt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pesos", default="/weights/ace_step_1_5_lm.safetensors")
    args = parser.parse_args()
    ruta = args.pesos

    import torch  # noqa: PLC0415
    from safetensors.torch import load_file  # noqa: PLC0415

    cabecera, base = leer_cabecera(ruta)
    print(f"Artefacto: {ruta}")
    print(f"Cabecera: {base} bytes, {len(cabecera)-1 if '__metadata__' in cabecera else len(cabecera)} tensores")
    print()

    # ---- 1) La ruta ACTUAL: load_file(device='cpu') + materializacion por tensor.
    t0 = time.perf_counter()
    sd = load_file(ruta, device="cpu")
    dt_map = time.perf_counter() - t0
    print(f"  load_file(device='cpu')  (solo mapea)      {dt_map:7.2f} s")

    for prefijo in ("vae.decoder.", "dit.tokenizer."):
        claves = sorted(
            (k for k in sd if k.startswith(prefijo)),
            key=lambda k: cabecera[k]["data_offsets"][0],
        )
        n = sum(cabecera[k]["data_offsets"][1] - cabecera[k]["data_offsets"][0] for k in claves)
        t0 = time.perf_counter()
        for clave in claves:
            _ = sd[clave].clone()
            del _
        dt = time.perf_counter() - t0
        print(f"  POR TENSOR {prefijo:17s} {n/_MIB:8.1f} MiB en {dt:7.2f} s "
              f"-> {n/_MIB/dt:8.1f} MiB/s ({len(claves)} tensores)")

    # Un grupo mas grande por la ruta actual, para confirmar que la tasa se sostiene.
    prefijo = "dit.detokenizer."
    claves = sorted(
        (k for k in sd if k.startswith(prefijo)),
        key=lambda k: cabecera[k]["data_offsets"][0],
    )
    n = sum(cabecera[k]["data_offsets"][1] - cabecera[k]["data_offsets"][0] for k in claves)
    t0 = time.perf_counter()
    for clave in claves:
        _ = sd[clave].clone()
        del _
    dt = time.perf_counter() - t0
    print(f"  POR TENSOR {prefijo:17s} {n/_MIB:8.1f} MiB en {dt:7.2f} s "
          f"-> {n/_MIB/dt:8.1f} MiB/s ({len(claves)} tensores)")

    del sd
    import gc  # noqa: PLC0415
    gc.collect()
    print()

    # ---- 2) La ruta PROPUESTA: lectura contigua del rango de un componente.
    for prefijo, bloque in (
        ("vae.decoder.", 8 << 20),          # ya leido arriba: sale de cache, es el techo
        ("text_encoder.", 8 << 20),
        ("dit.encoder.", 64 << 20),
        ("lm.", 1 << 30),
    ):
        ini, fin, _claves = rango(cabecera, prefijo, base)
        medir_contiguo(ruta, ini, fin, bloque, prefijo)
    print()

    # ---- 3) Copia H2D: cuanto cuesta subir un buffer grande a la GPU.
    if torch.cuda.is_available():
        n = 1024 * _MIB
        cpu = torch.empty(int(n), dtype=torch.uint8)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        gpu = cpu.to("cuda:0", non_blocking=False)
        torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        print(f"  H2D pageable  1024,0 MiB en {dt:7.2f} s -> {1024/dt:8.1f} MiB/s")
        del gpu, cpu
        torch.cuda.empty_cache()

        fijado = torch.empty(64 * 1024 * 1024, dtype=torch.uint8, pin_memory=True)
        destino = torch.empty(64 * 1024 * 1024, dtype=torch.uint8, device="cuda:0")
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(16):
            destino.copy_(fijado, non_blocking=False)
        torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        print(f"  H2D fijado    1024,0 MiB en {dt:7.2f} s -> {1024/dt:8.1f} MiB/s")
        del fijado, destino
        torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
