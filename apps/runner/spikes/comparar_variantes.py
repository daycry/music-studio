#!/usr/bin/env python3
"""Compara dos pistas del A/B de variante de pesos (turbo destilado vs sft).

Responde a UNA pregunta: la destilacion a 8 pasos del turbo, ¿se dejo por el
camino el encaje ritmico de la voz con la base? Se generan las dos ramas con la
MISMA letra, prompt, semilla, metadatos y duracion, y aqui se mide si hay o no
una diferencia MEDIBLE.

Que se mide y por que
---------------------
* Nivel y espectro (`rms`, `pico`, `centroide`, `rolloff95`, `energia>4k`): no
  responden a la pregunta, pero acotan el terreno. Si las dos ramas difieren
  mucho en brillo o nivel, cualquier impresion de «encaja mejor» puede ser eso y
  no ritmo.
* **Ritmo** (`bpm_acf`, `pulso_fuerza` y el bloque voz-base): es el par que
  importa. `pulso_fuerza` es la altura del pico de la autocorrelacion de la
  envolvente de ATAQUES: distingue un pulso marcado de uno emborronado.
* `coherencia_voz_beat` y `desfase_voz_beat_ms`: proxy directo de la queja. Se
  comparan los ataques de la banda de voz (300-3400 Hz) con los del grave
  (30-200 Hz).

Limites, escritos aqui para que no se lean estos numeros por mas de lo que son:

1. Todo esto mide la MEZCLA, no la voz aislada. Un golpe seco es de banda ancha y
   deja rastro en la banda de voz (hay un test que lo fija). Por eso las cifras
   valen para comparar dos pistas de la misma instrumentacion entre si, y NO como
   veredicto absoluto de encaje.
2. Dos pistas es n=1 por rama. Una diferencia pequena puede ser la semilla.
3. Nada de esto es calidad musical. Eso es escucha humana (G1).

Uso::

    python comparar_variantes.py \\
        --pista turbo=/outputs/turbo-120-....wav \\
        --pista sft=/outputs/sft-120-....wav \\
        --bpm-objetivo 94 --salida /outputs/ab-variantes.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import medir_ab  # noqa: E402

#: Metricas que se tabulan, en orden de lectura, con su formato y unidad.
#: El bloque de ritmo va al final a proposito: es la conclusion, no el preambulo.
FILAS: list[tuple[str, str, str]] = [
    ("rms_dbfs", "RMS", "dBFS"),
    ("pico_dbfs", "Pico", "dBFS"),
    ("factor_cresta_db", "Factor de cresta", "dB"),
    ("centroide_hz", "Centroide espectral", "Hz"),
    ("rolloff95_hz", "Rolloff 95 %", "Hz"),
    ("energia_sobre_4k_pct", "Energia sobre 4 kHz", "%"),
    ("planitud_espectral", "Planitud espectral", ""),
    ("flujo_espectral", "Flujo espectral", ""),
    ("std_rms_1s_db", "Variacion de nivel (1 s)", "dB"),
    ("rango_rms_1s_db", "Rango de nivel (1 s)", "dB"),
    ("cambios_seccion", "Cambios de seccion", ""),
    ("bpm_acf_plegado", "BPM (mezcla)", "BPM"),
    ("pulso_fuerza", "FUERZA DEL PULSO (mezcla)", ""),
    ("bpm_grave_plegado", "BPM (grave)", "BPM"),
    ("pulso_fuerza_grave", "FUERZA DEL PULSO (grave)", ""),
    ("bpm_voz_plegado", "BPM (banda de voz)", "BPM"),
    ("pulso_fuerza_voz", "FUERZA DEL PULSO (voz)", ""),
    ("desfase_voz_beat_ms", "Desfase voz-base", "ms"),
    ("coherencia_voz_beat", "Coherencia voz-base", ""),
]


def _fmt(valor: Any) -> str:
    if valor is None or (isinstance(valor, float) and not math.isfinite(valor)):
        return "n/d"
    if isinstance(valor, float):
        # Sin separador de millares: junto a un "949.78" de la columna de al lado,
        # un "2.410" se lee como dos coma cuatro y no como dos mil cuatrocientos.
        if abs(valor) >= 1000:
            return f"{valor:.0f}"
        if abs(valor) >= 10:
            return f"{valor:.2f}"
        return f"{valor:.4f}"
    return str(valor)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--pista",
        action="append",
        required=True,
        metavar="ETIQUETA=RUTA",
        help="Pista a medir. Se admite dos veces (la segunda es la comparada).",
    )
    p.add_argument("--bpm-objetivo", type=float, default=94.0, dest="bpm_objetivo")
    p.add_argument("--salida", default=None, help="JSON con todas las metricas.")
    args = p.parse_args()

    pistas: dict[str, dict[str, Any]] = {}
    for spec in args.pista:
        if "=" not in spec:
            raise SystemExit(f"--pista espera ETIQUETA=RUTA, no {spec!r}")
        etiqueta, ruta_txt = spec.split("=", 1)
        ruta = Path(ruta_txt)
        if not ruta.is_file():
            raise SystemExit(f"No existe la pista {ruta}")
        mono, estereo, tasa = medir_ab.leer_wav(ruta)
        d = medir_ab.descriptores(mono, estereo, tasa)
        d["fichero"] = ruta.name
        d["duracion_s"] = round(len(mono) / tasa, 3)
        pistas[etiqueta] = {**d, "mono": mono, "tasa": tasa}
        print(f"[medido] {etiqueta:10s} {ruta.name}  {d['duracion_s']} s")

    etiquetas = list(pistas)
    ancho = max(14, max(len(e) for e in etiquetas) + 2)

    print()
    print("=" * (34 + ancho * len(etiquetas) + 12))
    print("A/B DE VARIANTE DE PESOS — misma letra, prompt, semilla, metadatos y duracion")
    print("=" * (34 + ancho * len(etiquetas) + 12))
    cabecera = f"{'Metrica':<28}{'Unidad':<8}" + "".join(f"{e:>{ancho}}" for e in etiquetas)
    if len(etiquetas) == 2:
        cabecera += f"{'delta':>14}"
    print(cabecera)
    print("-" * len(cabecera))

    for clave, titulo, unidad in FILAS:
        valores = [pistas[e].get(clave) for e in etiquetas]
        linea = f"{titulo:<28}{unidad:<8}" + "".join(f"{_fmt(v):>{ancho}}" for v in valores)
        if len(etiquetas) == 2:
            a, b = valores
            if all(isinstance(v, (int, float)) and math.isfinite(v) for v in (a, b)):
                linea += f"{b - a:>+14.4f}"
            else:
                linea += f"{'n/d':>14}"
        print(linea)

    informe: dict[str, Any] = {
        "bpm_objetivo": args.bpm_objetivo,
        "pistas": {
            e: {k: v for k, v in d.items() if k not in ("mono",)}
            for e, d in pistas.items()
        },
    }
    if len(etiquetas) == 2:
        a, b = etiquetas
        informe["distancias_audio"] = medir_ab.distancias(pistas[a], pistas[b])
        print()
        for k, v in informe["distancias_audio"].items():
            print(f"{k:<28}{_fmt(v)}")

    if args.salida:
        def _limpiar(o: Any) -> Any:
            if isinstance(o, dict):
                return {k: _limpiar(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_limpiar(v) for v in o]
            # Los escalares de numpy tienen `.tolist()` igual que los arrays: hay
            # que distinguirlos por `ndim`, o se anulan numeros perfectamente
            # validos y el JSON sale lleno de `null`.
            if hasattr(o, "ndim"):
                if o.ndim > 0:
                    return None
                o = o.item()
            if isinstance(o, float) and not math.isfinite(o):
                return None
            return o

        Path(args.salida).write_text(
            json.dumps(_limpiar(informe), indent=2, ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )
        print(f"\n[informe] {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
