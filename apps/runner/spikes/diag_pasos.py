#!/usr/bin/env python3
"""Diagnostico D-PASOS: cuanto de la falta de finura es el precio del turbo.

Hipotesis 1 del diagnostico de calidad: "no suena fino" es el precio de los 8
pasos sin CFG del turbo, no un defecto del pipeline. Se mide, no se opina.

Que hace
--------
Con LA MISMA semilla, prompt, letra y duracion (30 s), genera la misma pista con
distinto numero de pasos de difusion y, aparte, con CFG a varias escalas.
Escribe cada resultado como WAV en /outputs y tabula metricas objetivas.

Por que es legitimo pedirle mas de 8 pasos
------------------------------------------
El DiT se consulta SIEMPRE con `timestep_r == timestep` (tanto en el bucle de
inferencia de upstream como en su propio `forward` de entrenamiento, que llama a
`sample_t_r(..., use_meanflow=False)` y pasa `timestep_r=t`). El embebido de
paso, `time_embed_r(timestep - timestep_r)`, recibe por tanto siempre 0: el
modelo predice la velocidad INSTANTANEA del emparejamiento de flujo, no una
velocidad media sobre un intervalo. Eso significa que los 8 pasos son una
integracion de Euler groserisima de una ODE bien definida, y que anadir pasos es
resolver mejor LA MISMA ODE, no salirse de la distribucion de entrenamiento.

La tabla de 8 pasos de `scheduler.py` es la transformada de desplazamiento
    t' = shift * t / (1 + (shift - 1) * t),  t = 1 - i/N
con N = 8. Este script usa la MISMA formula con N variable; para N = 8 reproduce
la tabla literal de upstream (se comprueba con un assert).

CFG
---
El turbo esta destilado con la guia incorporada y upstream fuerza
`guidance_scale=1.0`. Pero el artefacto SI trae `dit.null_condition_emb` (el
shim la carga), que es exactamente la condicion nula con la que se entreno el
`cfg_ratio=0.15` del modelo base. Asi que la pasada incondicional es
construible: se sustituye `encoder_hidden_states` por esa embebida, con su
propia cache de atencion cruzada, y se combina
    v = v_u + escala * (v_c - v_u).
Puede empeorar. Por eso se mide.

Salidas
-------
/outputs/diag-pasos-NN.wav, /outputs/diag-cfgSS-EE.wav, /outputs/diag-prod-08.wav
/outputs/diag-pasos-informe.json  (todas las metricas, reproducible)

No modifica nada del repositorio ni del artefacto. Usa el codigo de /app.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
import wave
from pathlib import Path

RAIZ = Path(os.environ.get("ACE_STEP_APP_ROOT", "/app"))
for _r in (RAIZ / "spikes", RAIZ / "adapters" / "ace_step", RAIZ):
    sys.path.insert(0, str(_r))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from safetensors.torch import load_file  # noqa: E402
from transformers.cache_utils import DynamicCache, EncoderDecoderCache  # noqa: E402

import ace_step_shim as shim  # noqa: E402
from vendor.pipeline.conditioning import (  # noqa: E402
    longitud_latente,
    preparar_condicionamiento_text2music,
)
from vendor.pipeline.decode import decodificar_latentes  # noqa: E402
from vendor.pipeline.diffusion import generar_latentes_text2music  # noqa: E402
from vendor.pipeline.scheduler import SHIFT_TIMESTEPS  # noqa: E402

SALIDA = Path(os.environ.get("ACE_STEP_OUTPUT_DIR", "/outputs"))
PESOS = Path("/weights/ace_step_1_5.safetensors")
DISPOSITIVO = torch.device("cuda:0")
DTYPE = torch.float16
SR = 48000

# --- Peticion: EXACTAMENTE la de generate_smoke.py por defecto -------------- #
PROMPT = (
    "pop electronico nocturno en castellano, voz femenina calida, sintetizadores "
    "analogicos, guitarra con delay, bajo profundo, bateria suave, 92 BPM, "
    "melancolico, produccion limpia"
)
LETRA = """[verse]
Se apaga la ciudad y enciendo la consola,
la noche me sostiene, la memoria se desborda.
Un cable, dos acordes, la lluvia en el cristal,
y un coro de neones que no sabe terminar.

[chorus]
Canta, que la maquina aprendio a sonar,
canta, que la noche no se va a acabar.
Deja que la onda se condense al respirar,
y guarda cada huella, que la vamos a firmar.

[verse]
No pido una estrella ni un truco de cristal,
me basta con la traza de lo que fue real."""
SEMILLA = 20260902
DURACION = 30.0
SHIFT = 3.0

BARRIDO_PASOS = [8, 12, 16, 24, 30, 40, 50]
PASOS_REFERENCIA = 100           # solucion "convergida" de la ODE, patron de medida
CFG_EN_8 = [1.5, 3.0, 7.0]
CFG_EN_30 = [1.5, 3.0]

informe: dict = {
    "diagnostico": "D-PASOS (hipotesis 1: el techo del turbo)",
    "iniciado_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "peticion": {
        "style_prompt": PROMPT,
        "letra": LETRA,
        "semilla": SEMILLA,
        "duracion_s": DURACION,
        "shift": SHIFT,
        "vocal_language": "es",
    },
    "entorno": {},
    "corridas": {},
    "metricas": {},
    "convergencia": {},
    "errores": [],
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Programacion de pasos generalizada
# --------------------------------------------------------------------------- #

def programacion(n: int, shift: float = SHIFT) -> list[float]:
    """t' = shift*t/(1+(shift-1)*t) con t = 1 - i/n, i = 0..n-1.

    Para n = 8 y shift in {1,2,3} reproduce EXACTAMENTE las tablas de upstream.
    """
    fuera = []
    for i in range(n):
        t = 1.0 - i / n
        fuera.append(shift * t / (1.0 + (shift - 1.0) * t))
    return fuera


def _comprobar_formula() -> dict:
    """La formula tiene que reproducir la tabla literal de upstream a 8 pasos."""
    desvios = {}
    for s, tabla in SHIFT_TIMESTEPS.items():
        calculada = programacion(8, s)
        desvio = max(abs(a - b) for a, b in zip(calculada, tabla))
        desvios[str(s)] = desvio
        assert desvio < 1e-12, f"shift={s}: la formula no reproduce la tabla ({desvio})"
    return {"max_desvio_vs_tabla_upstream": desvios}


# --------------------------------------------------------------------------- #
# Bucle de difusion con N pasos y CFG opcional
# --------------------------------------------------------------------------- #

def bucle(model, cond, *, seed: int, n_pasos: int, shift: float = SHIFT,
          cfg: float | None = None) -> tuple[torch.Tensor, dict]:
    """Replica `vendor/pipeline/diffusion.py` con N pasos y CFG opcional.

    Con `n_pasos=8`, `shift=3.0`, `cfg=None` es bit a bit el camino de produccion
    (se verifica contra la funcion vendorizada en la corrida `prod-08`).
    """
    ctx = cond.context_latents
    dev, dt = ctx.device, ctx.dtype
    t_list = programacion(n_pasos, shift)
    noise = model.prepare_noise(ctx, seed)
    xt = noise
    pkv = EncoderDecoderCache(DynamicCache(), DynamicCache())

    ehs_u = pkv_u = None
    if cfg is not None:
        ehs_u = model.null_condition_emb.to(dtype=dt).expand_as(cond.encoder_hidden_states)
        pkv_u = EncoderDecoderCache(DynamicCache(), DynamicCache())

    t0 = time.perf_counter()
    for i, t in enumerate(t_list):
        tt = t * torch.ones((1,), device=dev, dtype=dt)
        with torch.no_grad():
            salida = model.decoder(
                hidden_states=xt,
                timestep=tt,
                timestep_r=tt,
                attention_mask=cond.attention_mask,
                encoder_hidden_states=cond.encoder_hidden_states,
                encoder_attention_mask=cond.encoder_attention_mask,
                context_latents=ctx,
                use_cache=True,
                past_key_values=pkv,
            )
            vt, pkv = salida[0], salida[1]
            if cfg is not None:
                salida_u = model.decoder(
                    hidden_states=xt,
                    timestep=tt,
                    timestep_r=tt,
                    attention_mask=cond.attention_mask,
                    encoder_hidden_states=ehs_u,
                    encoder_attention_mask=cond.encoder_attention_mask,
                    context_latents=ctx,
                    use_cache=True,
                    past_key_values=pkv_u,
                )
                vu, pkv_u = salida_u[0], salida_u[1]
                vt = vu + cfg * (vt - vu)

        if i == len(t_list) - 1:
            xt = model.get_x0_from_noise(xt, vt, tt)
            break
        t_next = t_list[i + 1]
        xt = xt - vt * (t - t_next)

    torch.cuda.synchronize()
    segundos = time.perf_counter() - t0
    return xt, {
        "pasos": n_pasos,
        "cfg": cfg,
        "t_primero": round(t_list[0], 6),
        "t_ultimo": round(t_list[-1], 6),
        "segundos": round(segundos, 2),
        "s_por_paso": round(segundos / n_pasos, 3),
        "forwards": n_pasos * (2 if cfg is not None else 1),
    }


# --------------------------------------------------------------------------- #
# Metricas objetivas
# --------------------------------------------------------------------------- #

EPS = 1e-20
CENTROS_OCTAVA = [31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0]


def _db(v: float) -> float | None:
    return round(20.0 * float(np.log10(v)), 2) if v > 0 else None


def metricas_audio(x: np.ndarray, sr: int = SR) -> dict:
    """x: [N, C] float64 en [-1, 1]. Devuelve el cuadro de metricas objetivas."""
    n, canales = x.shape
    mono = x.mean(axis=1)

    rms = float(np.sqrt(np.mean(x**2)))
    pico = float(np.abs(x).max())
    saturadas = int(np.sum(np.abs(x) >= 32767.0 / 32768.0))

    # --- Espectro por tramas ------------------------------------------------ #
    n_fft, hop = 2048, 1024
    w = np.hanning(n_fft)
    n_tramas = 1 + (len(mono) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n_tramas)[:, None]
    tramas = mono[idx] * w
    mag = np.abs(np.fft.rfft(tramas, axis=1))
    P = mag**2
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)

    energia = P.sum(axis=1)
    umbral = energia.max() * 1e-6
    vivas = energia > umbral

    centroide = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + EPS)
    planitud = np.exp(np.mean(np.log(P + 1e-18), axis=1)) / (np.mean(P, axis=1) + EPS)

    d = np.diff(mag, axis=0)
    flujo = np.maximum(d, 0.0).sum(axis=1) / (mag[1:].sum(axis=1) + EPS)
    flujo_vivo = flujo[vivas[1:]]

    # --- Espectro promedio de largo plazo (LTAS) ---------------------------- #
    ltas = P.mean(axis=0)
    total = ltas.sum()
    acum = np.cumsum(ltas)
    rolloff95 = float(freqs[int(np.searchsorted(acum, 0.95 * total))])
    rolloff99 = float(freqs[int(np.searchsorted(acum, 0.99 * total))])

    bandas = {}
    for c in CENTROS_OCTAVA:
        lo, hi = c / np.sqrt(2.0), c * np.sqrt(2.0)
        sel = (freqs >= lo) & (freqs < hi)
        e = float(ltas[sel].sum())
        bandas[f"{c:g}"] = round(10.0 * float(np.log10(e / total + 1e-15)), 2)

    # --- Envolvente y nitidez transitoria ----------------------------------- #
    win_e, hop_e = 512, 256
    n_e = 1 + (len(mono) - win_e) // hop_e
    idx_e = np.arange(win_e)[None, :] + hop_e * np.arange(n_e)[:, None]
    env = np.sqrt(np.mean(mono[idx_e] ** 2, axis=1))
    env_db = 20.0 * np.log10(env + 1e-9)
    de = np.diff(env_db)
    subidas = de[de > 0]
    por_s = sr / hop_e

    correlacion = None
    if canales == 2:
        m = np.corrcoef(x[:, 0], x[:, 1])
        if np.isfinite(m[0, 1]):
            correlacion = round(float(m[0, 1]), 4)

    return {
        "rms_dbfs": _db(rms),
        "pico_dbfs": _db(pico),
        "cresta_db": round((_db(pico) or 0.0) - (_db(rms) or 0.0), 2),
        "muestras_saturadas": saturadas,
        "saturadas_pct": round(100.0 * saturadas / (n * canales), 5),
        "correlacion_canales": correlacion,
        "centroide_hz": round(float(np.mean(centroide[vivas])), 1),
        "centroide_hz_pond_energia": round(
            float((centroide * energia).sum() / (energia.sum() + EPS)), 1
        ),
        "planitud_db": round(float(10.0 * np.log10(np.mean(planitud[vivas]) + 1e-15)), 2),
        "planitud_mediana_db": round(
            float(10.0 * np.log10(np.median(planitud[vivas]) + 1e-15)), 2
        ),
        "flujo_espectral": round(float(np.mean(flujo_vivo)), 5),
        "rolloff95_hz": round(rolloff95, 1),
        "rolloff99_hz": round(rolloff99, 1),
        "bandas_octava_db_rel": bandas,
        "envolvente": {
            "subida_media_db_por_trama": round(float(np.mean(subidas)), 4),
            "subida_p95_db": round(float(np.percentile(de, 95)), 4),
            "abs_derivada_media_db": round(float(np.mean(np.abs(de))), 4),
            "ataques_mayores_3db_por_s": round(float(np.sum(de > 3.0) / (n_e / por_s)), 3),
            "rango_dinamico_env_db": round(
                float(np.percentile(env_db, 95) - np.percentile(env_db, 5)), 2
            ),
        },
    }


def leer_wav(ruta: Path) -> np.ndarray:
    with wave.open(str(ruta), "rb") as e:
        canales, ancho, marcos = e.getnchannels(), e.getsampwidth(), e.getnframes()
        crudo = e.readframes(marcos)
    assert ancho == 2
    return np.frombuffer(crudo, dtype="<i2").reshape(-1, canales).astype(np.float64) / 32768.0


def escribir_wav(nombre: str, pcm16: bytes, canales: int) -> Path:
    ruta = SALIDA / nombre
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(canales)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16)
    return ruta


def comparar_latentes(a: torch.Tensor, b: torch.Tensor) -> dict:
    a32, b32 = a.float().flatten(), b.float().flatten()
    d = a32 - b32
    return {
        "l2_relativa_pct": round(float(100.0 * d.norm() / (b32.norm() + 1e-12)), 3),
        "rmse": round(float((d**2).mean().sqrt()), 5),
        "coseno": round(float(torch.nn.functional.cosine_similarity(a32, b32, dim=0)), 5),
        "rms_a": round(float(a32.pow(2).mean().sqrt()), 5),
        "rms_b": round(float(b32.pow(2).mean().sqrt()), 5),
    }


def comparar_audio(a: np.ndarray, b: np.ndarray) -> dict:
    am, bm = a.mean(axis=1), b.mean(axis=1)
    n = min(len(am), len(bm))
    am, bm = am[:n], bm[:n]
    den = float(np.linalg.norm(am) * np.linalg.norm(bm))
    corr = float(np.dot(am, bm) / den) if den > 0 else float("nan")
    return {
        "correlacion_forma_de_onda": round(corr, 4),
        "rmse": round(float(np.sqrt(np.mean((am - bm) ** 2))), 6),
        "l2_relativa_pct": round(
            float(100.0 * np.linalg.norm(am - bm) / (np.linalg.norm(bm) + 1e-12)), 2
        ),
    }


def vram() -> dict:
    libre, total = torch.cuda.mem_get_info(DISPOSITIVO)
    return {
        "libre_mib": round(libre / 2**20),
        "pico_torch_mib": round(torch.cuda.max_memory_allocated(DISPOSITIVO) / 2**20),
    }


# --------------------------------------------------------------------------- #
# Programa
# --------------------------------------------------------------------------- #

def main() -> int:
    if not torch.cuda.is_available():
        print("Sin CUDA: este diagnostico mide sobre la GPU real.")
        return 2

    informe["entorno"] = {
        "torch": torch.__version__,
        "gpu": torch.cuda.get_device_name(0),
        "capacidad": ".".join(map(str, torch.cuda.get_device_capability(0))),
        "artefacto": str(PESOS),
        "vram_inicial": vram(),
        "formula_programacion": _comprobar_formula(),
    }
    log("Formula de programacion verificada contra las tres tablas de upstream.")

    log("Cargando el artefacto a VRAM (bind mount: varios minutos).")
    t0 = time.perf_counter()
    sd = load_file(str(PESOS), device="cuda:0")
    carga_s = time.perf_counter() - t0
    log(f"Artefacto cargado en {carga_s:.1f} s ({len(sd)} tensores).")
    pipe = shim.build_pipeline(state_dict=sd, device="cuda:0", dtype=DTYPE, offload=True)
    del sd
    torch.cuda.empty_cache()
    informe["entorno"]["carga_s"] = round(carga_s, 1)
    informe["entorno"]["vram_tras_construir"] = vram()

    modelo = pipe._modelo
    tramas, dur = longitud_latente(DURACION)
    log(f"Condicionamiento: {tramas} tramas latentes ({dur:.2f} s).")
    with shim._residentes(pipe._text_encoder, pipe._dit_encoder):
        cond = preparar_condicionamiento_text2music(
            model=modelo,
            text_encoder=pipe._text_encoder.modulo,
            text_tokenizer=pipe._tokenizador,
            silence_latent=pipe._silence_latent,
            style_prompt=PROMPT,
            lyrics=LETRA,
            duracion_s=DURACION,
            device=DISPOSITIVO,
            dtype=DTYPE,
            vocal_language="es",
        )
    informe["entorno"]["L_enc"] = int(cond.encoder_hidden_states.shape[1])
    informe["entorno"]["tramas_latentes"] = int(cond.latent_length)
    informe["entorno"]["null_condition_emb"] = {
        "forma": list(modelo.null_condition_emb.shape),
        "dtype": str(modelo.null_condition_emb.dtype),
        "norma": round(float(modelo.null_condition_emb.float().norm()), 4),
        "rms": round(float(modelo.null_condition_emb.float().pow(2).mean().sqrt()), 5),
    }
    torch.cuda.empty_cache()

    # ----------------------------------------------------------- corridas ---- #
    latentes: dict[str, torch.Tensor] = {}
    plan: list[tuple[str, str, dict]] = []

    plan.append(("prod-08", "diag-prod-08.wav", {"produccion": True}))
    for n in BARRIDO_PASOS:
        plan.append((f"pasos-{n:02d}", f"diag-pasos-{n:02d}.wav", {"n": n}))
    plan.append((f"pasos-{PASOS_REFERENCIA}", f"diag-pasos-{PASOS_REFERENCIA}.wav",
                 {"n": PASOS_REFERENCIA}))
    for e in CFG_EN_8:
        plan.append((f"cfg08-{e:g}", f"diag-cfg08-{str(e).replace('.', 'p')}.wav",
                     {"n": 8, "cfg": e}))
    for e in CFG_EN_30:
        plan.append((f"cfg30-{e:g}", f"diag-cfg30-{str(e).replace('.', 'p')}.wav",
                     {"n": 30, "cfg": e}))

    for clave, nombre, cfgd in plan:
        try:
            torch.cuda.reset_peak_memory_stats(DISPOSITIVO)
            if cfgd.get("produccion"):
                log(f"{clave}: camino de PRODUCCION (funcion vendorizada, 8 pasos).")
                t_ini = time.perf_counter()
                res = generar_latentes_text2music(
                    model=modelo, cond=cond, seed=SEMILLA, shift=SHIFT
                )
                torch.cuda.synchronize()
                x = res.target_latents
                meta = {
                    "pasos": 8, "cfg": None, "camino": "vendor/pipeline/diffusion.py",
                    "segundos": round(time.perf_counter() - t_ini, 2),
                    "forwards": 8,
                }
            else:
                log(f"{clave}: {cfgd['n']} pasos, cfg={cfgd.get('cfg')}.")
                x, meta = bucle(
                    modelo, cond, seed=SEMILLA, n_pasos=cfgd["n"], cfg=cfgd.get("cfg")
                )
            meta["vram"] = vram()
            meta["latente"] = {
                "forma": list(x.shape),
                "rms": round(float(x.float().pow(2).mean().sqrt()), 5),
                "max_abs": round(float(x.float().abs().max()), 4),
                "finito": bool(torch.isfinite(x).all()),
            }
            latentes[clave] = x.detach().clone()
            informe["corridas"][clave] = meta
            log(f"  -> {meta['segundos']} s, rms latente {meta['latente']['rms']}")
        except Exception as exc:  # noqa: BLE001
            informe["errores"].append(f"{clave}: {exc!r}")
            informe["corridas"][clave] = {"error": repr(exc)}
            log(f"  !! FALLO {clave}: {exc!r}")
            traceback.print_exc()
        torch.cuda.empty_cache()

    # ------------------------------------------------------------ decodes ---- #
    ondas: dict[str, np.ndarray] = {}
    log("Decodificando todas las corridas con el VAE residente.")
    with shim._residentes(pipe._vae):
        for clave, nombre, _ in plan:
            if clave not in latentes:
                continue
            try:
                t_ini = time.perf_counter()
                onda = decodificar_latentes(
                    decoder=pipe._vae.modulo, target_latents=latentes[clave]
                )
                pcm16, canales, muestras = shim._a_pcm16(onda)
                del onda
                ruta = escribir_wav(nombre, pcm16, canales)
                ondas[clave] = (
                    np.frombuffer(pcm16, dtype="<i2").reshape(-1, canales).astype(np.float64)
                    / 32768.0
                )
                informe["corridas"][clave]["wav"] = {
                    "fichero": nombre,
                    "bytes": ruta.stat().st_size,
                    "duracion_s": round(muestras / SR, 4),
                    "decode_s": round(time.perf_counter() - t_ini, 2),
                }
                log(f"  {nombre} escrito ({muestras / SR:.2f} s).")
            except Exception as exc:  # noqa: BLE001
                informe["errores"].append(f"decode {clave}: {exc!r}")
                log(f"  !! decode {clave}: {exc!r}")
            torch.cuda.empty_cache()

    # ----------------------------------------------------------- metricas ---- #
    log("Midiendo.")
    for clave, onda in ondas.items():
        informe["metricas"][clave] = metricas_audio(onda)

    # Referencia externa: la pista de 30 s ya generada por el camino de produccion.
    for ext in sorted(SALIDA.glob("t03-smoke-30-30s-*.wav")):
        try:
            informe["metricas"][f"externa:{ext.name}"] = metricas_audio(leer_wav(ext))
        except Exception as exc:  # noqa: BLE001
            informe["errores"].append(f"externa {ext.name}: {exc!r}")

    # --------------------------------------------------------- convergencia -- #
    ref = f"pasos-{PASOS_REFERENCIA}"
    if ref in latentes:
        for clave, x in latentes.items():
            if clave == ref:
                continue
            entrada: dict = {"latente_vs_ref": comparar_latentes(x, latentes[ref])}
            if clave in ondas and ref in ondas:
                entrada["audio_vs_ref"] = comparar_audio(ondas[clave], ondas[ref])
            informe["convergencia"][clave] = entrada

    # Fidelidad del arnes: mi bucle a 8 pasos contra la funcion de produccion.
    if "prod-08" in latentes and "pasos-08" in latentes:
        informe["convergencia"]["fidelidad_arnes_prod08_vs_pasos08"] = comparar_latentes(
            latentes["pasos-08"], latentes["prod-08"]
        )
        if "prod-08" in ondas and "pasos-08" in ondas:
            informe["convergencia"]["fidelidad_arnes_audio"] = comparar_audio(
                ondas["pasos-08"], ondas["prod-08"]
            )

    informe["terminado_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ruta_informe = SALIDA / "diag-pasos-informe.json"
    ruta_informe.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Informe en {ruta_informe}")

    # Tabla resumida por stdout para lectura rapida.
    cab = ("corrida", "rms", "pico", "cresta", "centr.", "planit.", "flujo", "roll95",
           "subida", "ataq/s")
    print("\n{:<14}{:>8}{:>8}{:>8}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}".format(*cab), flush=True)
    for clave in list(informe["metricas"]):
        m = informe["metricas"][clave]
        print(
            "{:<14}{:>8}{:>8}{:>8}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}".format(
                clave[:14],
                m["rms_dbfs"], m["pico_dbfs"], m["cresta_db"],
                m["centroide_hz"], m["planitud_db"], m["flujo_espectral"],
                m["rolloff95_hz"],
                m["envolvente"]["subida_media_db_por_trama"],
                m["envolvente"]["ataques_mayores_3db_por_s"],
            ),
            flush=True,
        )

    print("\nConvergencia hacia la solucion de %d pasos:" % PASOS_REFERENCIA, flush=True)
    for clave, v in informe["convergencia"].items():
        if "latente_vs_ref" in v:
            a = v.get("audio_vs_ref", {})
            print(
                f"  {clave:<14} latente L2rel {v['latente_vs_ref']['l2_relativa_pct']:>7}%  "
                f"cos {v['latente_vs_ref']['coseno']:>8}   audio corr "
                f"{a.get('correlacion_forma_de_onda', 'n/d')}",
                flush=True,
            )

    return 0 if not informe["errores"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
