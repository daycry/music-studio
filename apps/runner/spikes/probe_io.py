"""Sonda de E/S: que estrategia de lectura saca mas MiB/s del bind mount.

Cada caso lee un rango DISTINTO del fichero para que ninguno se beneficie de la
cache de paginas del anterior. No toca torch: solo `open`/`readinto`.
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor

MIB = 1048576


def leer_rango(ruta: str, ini: int, n: int, blk: int, destino: memoryview) -> int:
    with open(ruta, "rb", buffering=0) as f:
        f.seek(ini)
        got = 0
        while got < n:
            k = f.readinto(destino[got : got + min(blk, n - got)])
            if not k:
                break
            got += k
    return got


def caso(ruta: str, off_mib: int, n_mib: int, blk_mib: int, hilos: int) -> None:
    n = n_mib * MIB
    blk = blk_mib * MIB
    buf = bytearray(n)
    mv = memoryview(buf)
    t0 = time.perf_counter()
    if hilos <= 1:
        leer_rango(ruta, off_mib * MIB, n, blk, mv)
    else:
        trozo = n // hilos
        with ThreadPoolExecutor(max_workers=hilos) as pool:
            futuros = [
                pool.submit(
                    leer_rango,
                    ruta,
                    off_mib * MIB + i * trozo,
                    trozo if i < hilos - 1 else n - trozo * (hilos - 1),
                    blk,
                    mv[i * trozo : (i * trozo + trozo) if i < hilos - 1 else n],
                )
                for i in range(hilos)
            ]
            for f in futuros:
                f.result()
    dt = time.perf_counter() - t0
    print(f"  off={off_mib:>5} MiB  n={n_mib:>4} MiB  blk={blk_mib:>3} MiB  hilos={hilos:>2}  "
          f"{dt:6.2f} s -> {n_mib/dt:8.1f} MiB/s")
    del mv, buf


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fichero", default="/weights/ace_step_1_5.safetensors")
    p.add_argument("--casos", default="")
    args = p.parse_args()
    print(f"Fichero: {args.fichero}  ({os.path.getsize(args.fichero)/MIB:.0f} MiB)")
    if args.casos:
        casos = []
        for c in args.casos.split(","):
            o, n, b, h = c.split(":")
            casos.append((int(o), int(n), int(b), int(h)))
    else:
        casos = [
            (0, 512, 1, 1),
            (512, 512, 8, 1),
            (1024, 512, 32, 1),
            (1536, 512, 8, 4),
            (2048, 512, 8, 8),
            (2560, 512, 4, 16),
            (3072, 512, 2, 32),
            (3584, 512, 16, 8),
        ]
    for o, n, b, h in casos:
        caso(args.fichero, o, n, b, h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
