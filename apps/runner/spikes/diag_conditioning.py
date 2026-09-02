#!/usr/bin/env python
"""Diagnostico H3: el condicionamiento de texto que ve el DiT de ACE-Step 1.5.

Dos fases independientes:

  --fase texto  Audita el TEXTO exacto y los IDS exactos que llegan al text
                encoder y al codificador de letra: plantilla SFT, bloque de
                metadatos, cabecera de idioma, tokens especiales, longitudes y
                composicion de L_enc. No genera audio (segundos).

  --fase audio  Prueba de ADHERENCIA empirica. Genera pistas cortas con
                condiciones deliberadamente opuestas y mide si el audio se
                diferencia de verdad, contra un control de la MISMA condicion
                con otra semilla. Si dos prompts opuestos se parecen tanto
                entre si como dos semillas del mismo prompt, el
                condicionamiento no esta llegando.

Escribe WAV en `--salida` (por defecto /outputs) con prefijo `diag-cond-` y un
informe JSON con todas las metricas.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np
import torch

RAIZ_APP = Path(os.environ.get("ACE_STEP_APP_ROOT", "/app"))
if not (RAIZ_APP / "adapters").is_dir():
    RAIZ_APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_APP))
sys.path.insert(0, str(RAIZ_APP / "adapters" / "ace_step"))

SR = 48000


# --------------------------------------------------------------------------- #
# Utilidades de carga parcial del artefacto
# --------------------------------------------------------------------------- #

def cargar_prefijos(ruta: str, prefijos: tuple[str, ...]) -> dict[str, torch.Tensor]:
    from safetensors import safe_open

    with open(ruta, "rb") as fichero:
        n = int.from_bytes(fichero.read(8), "little")
        cabecera = json.loads(fichero.read(n).decode("utf-8"))
    quiero = [
        clave
        for clave in cabecera
        if clave != "__metadata__" and any(clave.startswith(p) for p in prefijos)
    ]
    quiero.sort(key=lambda c: cabecera[c]["data_offsets"][0])
    salida: dict[str, torch.Tensor] = {}
    with safe_open(ruta, framework="pt", device="cpu") as fichero:
        for clave in quiero:
            salida[clave] = fichero.get_tensor(clave)
    return salida


# --------------------------------------------------------------------------- #
# FASE 1 — auditoria del texto y de los ids
# --------------------------------------------------------------------------- #

def fase_texto(args: argparse.Namespace) -> int:
    import text_conditioning
    from vendor.pipeline import conditioning as vcond
    from vendor.pipeline import constants as vconst

    print("=" * 78)
    print("FASE 1 — TEXTO E IDS EXACTOS QUE VE EL MODELO")
    print("=" * 78)

    parcial = cargar_prefijos(args.pesos, ("aux.",))
    tok = text_conditioning.construir_tokenizer(parcial)
    interno = tok.tokenizer

    print(f"\n[tokenizer] vocab={tok.n_vocab} eos_id={tok.id_eos} "
          f"post={type(interno.post_processor).__name__} norm={type(interno.normalizer).__name__}")

    # --- 1. Plantilla verbatim -------------------------------------------- #
    print("\n[1] PLANTILLAS (contrato con los pesos)")
    print(f"    SFT_GEN_PROMPT          = {vconst.SFT_GEN_PROMPT!r}")
    print(f"    DEFAULT_DIT_INSTRUCTION = {vconst.DEFAULT_DIT_INSTRUCTION!r}")
    print(f"    formatear_letra('L','es')= {vconst.formatear_letra('L', 'es')!r}")

    casos = [
        ("por-defecto-es", args.prompt, args.letra, "es", None, None, None, 30.0),
        ("instrumental", args.prompt, "", "es", None, None, None, 30.0),
        ("bpm-60", "musica electronica instrumental", "", "es", 60, None, None, 30.0),
        ("bpm-180", "musica electronica instrumental", "", "es", 180, None, None, 30.0),
        ("meta-completo", args.prompt, args.letra, "es", 92, "A minor", "4/4", 180.0),
    ]

    resumen = []
    for nombre, prompt, letra, idioma, bpm, keyscale, ts, dur in casos:
        texto_prompt = vcond._construir_prompt(
            style_prompt=prompt,
            duracion_s=dur,
            bpm=bpm,
            keyscale=keyscale,
            timesignature=ts,
            instruccion=vconst.DEFAULT_DIT_INSTRUCTION,
        )
        texto_letra = vconst.formatear_letra(letra, idioma)
        ids_p = tok.codificar(texto_prompt)
        ids_l = tok.codificar(texto_letra)
        sin_p = interno.encode(texto_prompt, add_special_tokens=False).ids
        sin_l = interno.encode(texto_letra, add_special_tokens=False).ids
        l_enc = len(ids_l) + 1 + len(ids_p)
        print(f"\n[2] caso {nombre!r}")
        print(f"    PROMPT (texto literal, repr):\n        {texto_prompt!r}")
        print(f"    LETRA  (texto literal, repr, 200 primeros):\n        {texto_letra[:200]!r}")
        print(f"    ids prompt: {len(ids_p)} (sin especiales {len(sin_p)})  cola={ids_p[-6:]}")
        print(f"    ids letra : {len(ids_l)} (sin especiales {len(sin_l)})  cola={ids_l[-6:]}")
        print(f"    cabeza prompt={ids_p[:4]} letra={ids_l[:4]}")
        print(f"    decode cola prompt: {interno.decode(ids_p[-4:], skip_special_tokens=False)!r}")
        print(f"    decode cola letra : {interno.decode(ids_l[-4:], skip_special_tokens=False)!r}")
        print(f"    L_enc = L_lyric({len(ids_l)}) + timbre(1) + L_text({len(ids_p)}) = {l_enc}")
        print(f"    truncado upstream? prompt>{vconst.MAX_TEXT_TOKENS}: "
              f"{len(ids_p) > vconst.MAX_TEXT_TOKENS} · letra>{vconst.MAX_LYRIC_TOKENS}: "
              f"{len(ids_l) > vconst.MAX_LYRIC_TOKENS}")
        resumen.append(
            {
                "caso": nombre,
                "prompt_texto": texto_prompt,
                "letra_texto": texto_letra,
                "n_ids_prompt": len(ids_p),
                "n_ids_letra": len(ids_l),
                "eos_dobles_prompt": ids_p[-2:] == [tok.id_eos, tok.id_eos],
                "l_enc": l_enc,
            }
        )

    # --- 3. Sensibilidad del texto: dos prompts opuestos comparten ids? ---- #
    a = tok.codificar(vcond._construir_prompt(
        style_prompt="piano solo clasico lento, sin percusion",
        duracion_s=30.0, bpm=None, keyscale=None, timesignature=None,
        instruccion=vconst.DEFAULT_DIT_INSTRUCTION))
    b = tok.codificar(vcond._construir_prompt(
        style_prompt="death metal rapido con blast beats",
        duracion_s=30.0, bpm=None, keyscale=None, timesignature=None,
        instruccion=vconst.DEFAULT_DIT_INSTRUCTION))
    comun = sum(1 for x, y in zip(a, b) if x == y)
    print(f"\n[3] prompts opuestos: {len(a)} vs {len(b)} ids, "
          f"{comun} posiciones coincidentes (la plantilla es {comun} de prefijo/sufijo fijo)")

    salida = Path(args.salida) / "diag-cond-texto.json"
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nInforme: {salida}")
    return 0


# --------------------------------------------------------------------------- #
# Metricas de audio (numpy puro: la imagen no trae scipy ni librosa)
# --------------------------------------------------------------------------- #

def _stft_mag(x: np.ndarray, n_fft: int = 2048, hop: int = 512) -> np.ndarray:
    t = torch.from_numpy(x.astype(np.float32))
    ventana = torch.hann_window(n_fft)
    espectro = torch.stft(t, n_fft=n_fft, hop_length=hop, window=ventana,
                          center=True, return_complex=True)
    return espectro.abs().numpy()  # [bins, frames]


def _mediana_deslizante(m: np.ndarray, k: int, eje: int) -> np.ndarray:
    """Filtro de mediana con kernel impar `k` a lo largo de `eje`, con borde replicado."""
    r = k // 2
    pad = [(0, 0), (0, 0)]
    pad[eje] = (r, r)
    mp = np.pad(m, pad, mode="edge")
    vistas = np.lib.stride_tricks.sliding_window_view(mp, k, axis=eje)
    return np.median(vistas, axis=-1).astype(np.float32)


def metricas_audio(pcm: np.ndarray, sr: int = SR) -> dict[str, float]:
    """`pcm` es float32 [N, C] en [-1, 1]."""
    mono = pcm.mean(axis=1)
    n = mono.size
    rms = float(np.sqrt(np.mean(mono**2)))
    pico = float(np.max(np.abs(mono)))
    mag = _stft_mag(mono)                       # [1025, F]
    frec = np.linspace(0, sr / 2, mag.shape[0]).astype(np.float32)
    energia = mag.sum(axis=0) + 1e-12
    centroide = float(np.mean((frec[:, None] * mag).sum(axis=0) / energia))
    # Rolloff 85 %
    acum = np.cumsum(mag, axis=0) / (mag.sum(axis=0, keepdims=True) + 1e-12)
    idx = (acum >= 0.85).argmax(axis=0)
    rolloff = float(np.mean(frec[idx]))
    # Planitud espectral (media geometrica / aritmetica) en dB
    logm = np.log(mag + 1e-10)
    planitud = float(np.mean(np.exp(logm.mean(axis=0)) / (mag.mean(axis=0) + 1e-12)))
    # Bandas
    bandas = {}
    total = float((mag**2).sum()) + 1e-12
    for etiqueta, lo, hi in (("b_0_200", 0, 200), ("b_200_2k", 200, 2000),
                             ("b_2k_8k", 2000, 8000), ("b_8k_20k", 8000, 20000)):
        sel = (frec >= lo) & (frec < hi)
        bandas[etiqueta] = float(10 * math.log10(float((mag[sel] ** 2).sum()) / total + 1e-12))
    # HPSS suave (mascara de Wiener) -> energia percusiva
    h = _mediana_deslizante(mag, 31, eje=1)     # suaviza en tiempo -> armonico
    p = _mediana_deslizante(mag, 31, eje=0)     # suaviza en frecuencia -> percusivo
    mask_p = (p**2) / (p**2 + h**2 + 1e-12)
    ratio_perc = float((mag * mask_p).sum() / (mag.sum() + 1e-12))
    # Envolvente de inicios (flujo espectral rectificado) y tempo
    logmag = np.log1p(mag * 100.0)
    flujo = np.maximum(np.diff(logmag, axis=1), 0).sum(axis=0)
    flujo = flujo - flujo.mean()
    fps = sr / 512.0
    if flujo.std() > 1e-9:
        flujo_n = flujo / flujo.std()
    else:
        flujo_n = flujo
    ac = np.correlate(flujo_n, flujo_n, mode="full")[flujo_n.size - 1:]
    ac = ac / (ac[0] + 1e-12)
    lag_min = int(fps * 60.0 / 200.0)           # 200 BPM
    lag_max = int(fps * 60.0 / 45.0)            # 45 BPM
    lag_max = min(lag_max, ac.size - 1)
    if lag_max > lag_min + 1:
        mejor = int(np.argmax(ac[lag_min:lag_max])) + lag_min
        tempo = 60.0 * fps / mejor
        fuerza_tempo = float(ac[mejor])
    else:
        tempo, fuerza_tempo = 0.0, 0.0
    # Tasa de inicios: picos por encima de 1,5 sigma con 100 ms de refractario
    umbral = flujo_n.mean() + 1.5 * flujo_n.std()
    picos, ultimo = 0, -10**9
    for i in range(1, flujo_n.size - 1):
        if flujo_n[i] > umbral and flujo_n[i] >= flujo_n[i - 1] and flujo_n[i] > flujo_n[i + 1]:
            if i - ultimo > fps * 0.10:
                picos += 1
                ultimo = i
    tasa_inicios = picos / (n / sr)
    # Cruces por cero
    zcr = float(np.mean(np.abs(np.diff(np.sign(mono))) > 0))
    return {
        "rms_dbfs": round(20 * math.log10(rms + 1e-12), 2),
        "pico_dbfs": round(20 * math.log10(pico + 1e-12), 2),
        "cresta_db": round(20 * math.log10((pico + 1e-12) / (rms + 1e-12)), 2),
        "centroide_hz": round(centroide, 1),
        "rolloff85_hz": round(rolloff, 1),
        "planitud": round(planitud, 5),
        **{k: round(v, 2) for k, v in bandas.items()},
        "ratio_percusivo": round(ratio_perc, 4),
        "tempo_bpm": round(tempo, 1),
        "fuerza_tempo": round(fuerza_tempo, 4),
        "inicios_por_s": round(tasa_inicios, 3),
        "zcr": round(zcr, 5),
    }


CLAVES_VECTOR = (
    "centroide_hz", "rolloff85_hz", "ratio_percusivo", "inicios_por_s",
    "b_0_200", "b_200_2k", "b_2k_8k", "b_8k_20k", "zcr", "cresta_db",
)


def distancia(a: dict[str, float], b: dict[str, float], escalas: dict[str, float]) -> float:
    """Distancia euclidea normalizada por la dispersion entre todas las pistas."""
    total = 0.0
    for k in CLAVES_VECTOR:
        s = escalas.get(k, 1.0) or 1.0
        total += ((a[k] - b[k]) / s) ** 2
    return math.sqrt(total / len(CLAVES_VECTOR))


# --------------------------------------------------------------------------- #
# FASE 2 — adherencia empirica
# --------------------------------------------------------------------------- #

def escribir_wav(ruta: Path, pcm16: bytes, canales: int, sr: int = SR) -> None:
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(canales)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm16)


def pcm16_a_float(pcm16: bytes, canales: int) -> np.ndarray:
    bruto = np.frombuffer(pcm16, dtype="<i2").astype(np.float32) / 32768.0
    return bruto.reshape(-1, canales)


LETRA = """[verse]
Se apaga la ciudad y enciendo la consola,
la noche me sostiene, la memoria se desborda.
Un cable, dos acordes, la lluvia en el cristal,
y un coro de neones que no sabe terminar.

[chorus]
Canta, que la maquina aprendio a sonar,
canta, que la noche no se va a acabar."""


def fase_audio(args: argparse.Namespace) -> int:
    from ace_step_shim import build_pipeline
    from safetensors.torch import load_file

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("FASE 2 — PRUEBA DE ADHERENCIA")
    print("=" * 78)

    t0 = time.perf_counter()
    state = load_file(args.pesos, device=args.dispositivo)
    pipeline = build_pipeline(state_dict=state, device=args.dispositivo,
                              dtype="float16", offload=True)
    print(f"[carga] pipeline listo en {time.perf_counter() - t0:.1f} s")

    P_PIANO = "piano solo clasico lento, sin percusion, sala de conciertos, melancolico"
    P_METAL = "death metal rapido con blast beats, guitarras distorsionadas, doble bombo, voz gutural"
    P_POP = ("pop electronico nocturno en castellano, voz femenina calida, sintetizadores "
             "analogicos, bateria suave, 92 BPM")
    P_NEUTRO = "musica electronica instrumental"

    # (id, prompt, letra, instrumental, semilla, params extra)
    casos: list[tuple[str, str, str | None, bool, int, dict[str, Any]]] = [
        # A. prompts opuestos, misma semilla + control de semilla
        ("A1-piano-s1", P_PIANO, None, True, 1001, {}),
        ("A2-metal-s1", P_METAL, None, True, 1001, {}),
        ("A3-piano-s2", P_PIANO, None, True, 2002, {}),
        ("A4-metal-s2", P_METAL, None, True, 2002, {}),
        # B. letra vacia vs letra larga, mismo prompt y semilla
        ("B1-pop-conletra-s1", P_POP, LETRA, False, 1001, {"vocal_language": "es"}),
        ("B2-pop-instrumental-s1", P_POP, None, True, 1001, {"vocal_language": "es"}),
        ("B3-pop-conletra-s2", P_POP, LETRA, False, 2002, {"vocal_language": "es"}),
        # C. BPM en el bloque de metadatos, mismo prompt y semilla
        ("C1-bpm60-s1", P_NEUTRO, None, True, 1001, {"bpm": 60}),
        ("C2-bpm180-s1", P_NEUTRO, None, True, 1001, {"bpm": 180}),
        ("C3-bpm-na-s1", P_NEUTRO, None, True, 1001, {}),
    ]
    if args.solo:
        pedidos = set(args.solo.split(","))
        casos = [c for c in casos if c[0].split("-")[0] in pedidos or c[0] in pedidos]

    resultados: list[dict[str, Any]] = []
    for ident, prompt, letra, instrumental, semilla, extra in casos:
        print(f"\n[gen] {ident}  semilla={semilla} instrumental={instrumental} extra={extra}")
        t = time.perf_counter()
        render = pipeline.render(
            style_prompt=prompt,
            lyrics=letra,
            duration_s=args.duracion,
            instrumental=instrumental,
            seed=semilla,
            params=extra,
            on_step=lambda a, b: None,
        )
        dt = time.perf_counter() - t
        ruta = salida / f"diag-cond-{ident}.wav"
        escribir_wav(ruta, render.pcm16, render.channels)
        pcm = pcm16_a_float(render.pcm16, render.channels)
        met = metricas_audio(pcm)
        met["_segundos"] = round(dt, 2)
        print(f"      {dt:.1f} s -> {ruta.name}  centroide={met['centroide_hz']:.0f} Hz "
              f"perc={met['ratio_percusivo']:.3f} tempo={met['tempo_bpm']:.0f} "
              f"rms={met['rms_dbfs']:.1f} dBFS")
        resultados.append({"id": ident, "prompt": prompt, "letra": bool(letra),
                           "instrumental": instrumental, "semilla": semilla,
                           "params": extra, "wav": str(ruta), "metricas": met})

    # --- Escalas de normalizacion: dispersion observada entre TODAS las pistas #
    escalas = {}
    for k in CLAVES_VECTOR:
        vals = [r["metricas"][k] for r in resultados]
        escalas[k] = float(np.std(vals)) or 1.0

    idx = {r["id"]: r["metricas"] for r in resultados}

    def d(a: str, b: str) -> float | None:
        if a in idx and b in idx:
            return round(distancia(idx[a], idx[b], escalas), 4)
        return None

    comparaciones = {
        "A_prompts_opuestos_s1": d("A1-piano-s1", "A2-metal-s1"),
        "A_prompts_opuestos_s2": d("A3-piano-s2", "A4-metal-s2"),
        "A_control_piano_2_semillas": d("A1-piano-s1", "A3-piano-s2"),
        "A_control_metal_2_semillas": d("A2-metal-s1", "A4-metal-s2"),
        "B_letra_vs_instrumental": d("B1-pop-conletra-s1", "B2-pop-instrumental-s1"),
        "B_control_letra_2_semillas": d("B1-pop-conletra-s1", "B3-pop-conletra-s2"),
        "C_bpm60_vs_bpm180": d("C1-bpm60-s1", "C2-bpm180-s1"),
        "C_bpm60_vs_na": d("C1-bpm60-s1", "C3-bpm-na-s1"),
    }

    print("\n" + "=" * 78)
    print("TABLA DE METRICAS")
    print("=" * 78)
    cabecera = ["id", "centroide", "rolloff85", "perc", "inicios/s", "tempo", "b_0_200",
                "b_2k_8k", "rms", "cresta"]
    print(("{:<24}" + "{:>11}" * (len(cabecera) - 1)).format(*cabecera))
    for r in resultados:
        m = r["metricas"]
        print(("{:<24}" + "{:>11}" * 9).format(
            r["id"], m["centroide_hz"], m["rolloff85_hz"], m["ratio_percusivo"],
            m["inicios_por_s"], m["tempo_bpm"], m["b_0_200"], m["b_2k_8k"],
            m["rms_dbfs"], m["cresta_db"]))

    print("\n" + "=" * 78)
    print("DISTANCIAS (normalizadas por la dispersion del conjunto)")
    print("=" * 78)
    for k, v in comparaciones.items():
        print(f"  {k:<32} {v}")

    informe = {
        "duracion_s": args.duracion,
        "escalas": {k: round(v, 4) for k, v in escalas.items()},
        "resultados": resultados,
        "comparaciones": comparaciones,
    }
    ruta_json = salida / "diag-cond-audio.json"
    ruta_json.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nInforme: {ruta_json}")
    pipeline.release()
    return 0


# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fase", choices=("texto", "audio"), required=True)
    p.add_argument("--pesos", default="/weights/ace_step_1_5.safetensors")
    p.add_argument("--salida", default=os.environ.get("ACE_STEP_OUTPUT_DIR", "/outputs"))
    p.add_argument("--dispositivo", default="cuda:0")
    p.add_argument("--duracion", type=int, default=30)
    p.add_argument("--solo", default=None, help="Grupos o ids a generar (coma).")
    p.add_argument("--prompt", default=(
        "pop electronico nocturno en castellano, voz femenina calida, sintetizadores "
        "analogicos, guitarra con delay, bajo profundo, bateria suave, 92 BPM, "
        "melancolico, produccion limpia"))
    p.add_argument("--letra", default=LETRA)
    args = p.parse_args(argv)
    Path(args.salida).mkdir(parents=True, exist_ok=True)
    return fase_texto(args) if args.fase == "texto" else fase_audio(args)


if __name__ == "__main__":
    raise SystemExit(main())
