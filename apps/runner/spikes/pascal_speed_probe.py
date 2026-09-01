#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pascal_speed_probe.py -- Microbenchmark de torch PURO (sin modelo) para decidir si
una GPU Pascal sm_61 (GP104, GTX 1070) es viable como runner de ACE-Step 1.5.

PREGUNTA QUE RESPONDE
---------------------
En GP104 el FP16 *nativo* corre a 1/64 del FP32 (solo GP100 tiene FP16 rapido).
La duda: cuando torch/cuBLAS ejecuta un GEMM fp16 en sm_61, se cae en el camino
lento 1/64, o se promociona internamente a FP32 (~6,5 TFLOPS, usable)?

    ratio = TFLOPs(fp16) / TFLOPs(fp32)

      ratio ~ 0.015 (1/64)  -> CAMINO LENTO. El artefacto fp16 residente es
                              inutilizable tal cual; hay que hacer upcast a fp32
                              (y entonces no cabe en 8 GB) o cambiar de plan.
      ratio ~ 1.0          -> cuBLAS promociona a fp32. Pascal USABLE.
      ratio > 1.0          -> ademas gana ancho de banda por leer la mitad de bytes.

QUE MIDE (todo con warmup + torch.cuda.synchronize() alrededor de cada medicion,
>= 5 repeticiones, se reporta MEDIANA):
  1. GEMM cuadrado 4096x4096 fp32 vs fp16 -> TFLOP/s y COCIENTE  [LA RESPUESTA]
     + barrido 1024/2048/4096 por si el ratio depende del tamano.
  2. Lo mismo variando torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction
     (y allow_fp16_accumulation si existe en esta version de torch).
  3. GEMM con las formas REALES del DiT: [1, 2250, hidden] x [hidden, hidden].
  4. Atencion: F.scaled_dot_product_attention [1, heads, 2250, head_dim] fp16,
     por backend explicito, vs. la version eager (matmul + softmax).
  5. Conv1d/ConvTranspose1d representativas del decoder VAE (Oobleck) en fp16 y fp32.
  6. Ancho de banda de memoria efectivo (copia device-to-device).
  7. Identidad del dispositivo: capability, nombre, VRAM total/libre, arch_list.

SALIDA: tabla legible por stdout + bloque JSON final tras '---JSON---'.

NO escribe ningun fichero (el mount /work es de solo lectura). Todo va por stdout.

Uso:
  docker run --rm --gpus all \
    -v "D:\\srv\\ace-step\\weights:/weights:ro" \
    -v "C:\\...\\apps\\runner:/work:ro" \
    --entrypoint python ace-step-runner:t05 /work/spikes/pascal_speed_probe.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time
import traceback

# --------------------------------------------------------------------------------------
# Rutas de config. Si no se montan dentro del contenedor se usan los valores VERIFICADOS
# leidos de los config.json reales el 2026-09-01 (declarados en los FALLBACK_*).
# --------------------------------------------------------------------------------------

DEFAULT_DIT_CONFIG_CANDIDATES = [
    "/upstream/acestep-v15-turbo/config.json",
    "/work/upstream/acestep-v15-turbo/config.json",
    "D:/srv/ace-step/upstream/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/config.json",
]
DEFAULT_VAE_CONFIG_CANDIDATES = [
    "/upstream/vae/config.json",
    "/work/upstream/vae/config.json",
    "D:/srv/ace-step/upstream/19671f406d603126926c1b7e2adc169acbcade22/vae/config.json",
]

FALLBACK_DIT = {
    "hidden_size": 2048,
    "num_attention_heads": 16,
    "num_key_value_heads": 8,
    "head_dim": 128,
    "intermediate_size": 6144,
    "num_hidden_layers": 24,
    "num_audio_decoder_hidden_layers": 24,
    "patch_size": 2,
    "sliding_window": 128,
    "use_sliding_window": True,
    "in_channels": 192,
}
FALLBACK_VAE = {
    "audio_channels": 2,
    "decoder_channels": 128,
    "decoder_input_channels": 64,
    "channel_multiples": [1, 2, 4, 8, 16],
    "downsampling_ratios": [2, 4, 4, 6, 10],
    "sampling_rate": 48000,
}

SEQ_TOKENS_180S = 2250  # 180 s * 25 fps / patch_size 2

RESULTS: dict = {}
ERRORS: list = []


def load_json_first(candidates, fallback, label):
    for p in candidates:
        try:
            if p and os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as fh:
                    return json.load(fh), p
        except Exception as exc:
            ERRORS.append("%s: no se pudo leer %s: %r" % (label, p, exc))
    return dict(fallback), "<fallback-hardcoded-verificado>"


# --------------------------------------------------------------------------------------
# Cronometraje
# --------------------------------------------------------------------------------------

def bench(fn, min_reps=5, label=""):
    """Ejecuta fn() con calentamiento y devuelve estadisticas de tiempo en segundos.

    - Calentamiento: 1 llamada cronometrada para dimensionar + N mas segun coste.
    - Repeticiones: >= min_reps (mas si la op es corta, para amortiguar el jitter).
    - torch.cuda.synchronize() ANTES y DESPUES de cada medicion individual.
    - Devuelve MEDIANA (no media), mas min/max/n.
    """
    import torch

    torch.cuda.synchronize()
    t0 = time.perf_counter()
    fn()
    torch.cuda.synchronize()
    probe = time.perf_counter() - t0

    if probe > 1.0:
        warmup, reps = 1, min_reps
    elif probe > 0.05:
        warmup, reps = 2, max(min_reps, 7)
    elif probe > 0.001:
        warmup, reps = 3, max(min_reps, 15)
    else:
        warmup, reps = 5, max(min_reps, 30)

    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()

    times = []
    for _ in range(reps):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)

    times.sort()
    return {
        "median_s": statistics.median(times),
        "min_s": times[0],
        "max_s": times[-1],
        "mean_s": statistics.fmean(times),
        "n": len(times),
        "warmup_probe_s": probe,
        "label": label,
    }


def tflops(flops, seconds):
    return (flops / seconds) / 1e12 if seconds > 0 else float("nan")


def free_mem():
    import torch
    torch.cuda.synchronize()
    torch.cuda.empty_cache()


def mib(x):
    return x / (1024 ** 2)


def section(title):
    print()
    print("=" * 94)
    print(title)
    print("=" * 94)


# --------------------------------------------------------------------------------------
# 0. Identidad del dispositivo
# --------------------------------------------------------------------------------------

def probe_device():
    import torch

    dev = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(dev)
    cap = torch.cuda.get_device_capability(dev)
    free_b, total_b = torch.cuda.mem_get_info(dev)

    info = {
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "arch_list": torch.cuda.get_arch_list(),
        "device_name": props.name,
        "capability": "sm_%d%d" % (cap[0], cap[1]),
        "capability_tuple": list(cap),
        "multi_processor_count": props.multi_processor_count,
        "total_memory_bytes": props.total_memory,
        "total_memory_mib": round(mib(props.total_memory), 1),
        "free_memory_bytes": free_b,
        "free_memory_mib": round(mib(free_b), 1),
        "mem_get_info_total_bytes": total_b,
        "python": platform.python_version(),
    }
    for attr in ("regs_per_multiprocessor", "warp_size", "L2_cache_size", "max_threads_per_multi_processor"):
        if hasattr(props, attr):
            info[attr] = getattr(props, attr)

    section("0. DISPOSITIVO")
    print("  torch           : %s  (CUDA %s, cuDNN %s)" % (
        info["torch_version"], info["cuda_version"], info["cudnn_version"]))
    print("  arch_list       : %s" % (info["arch_list"],))
    print("  GPU             : %s" % info["device_name"])
    print("  capability      : %s  (get_device_capability -> %s)" % (info["capability"], tuple(cap)))
    print("  SMs             : %s" % info["multi_processor_count"])
    print("  VRAM total      : {:,} B = {:.0f} MiB".format(
        info["total_memory_bytes"], info["total_memory_mib"]))
    print("  VRAM libre      : {:,} B = {:.0f} MiB".format(
        info["free_memory_bytes"], info["free_memory_mib"]))
    print("  nota            : GP104 sm_61 -> fp16 NATIVO documentado a 1/64 del fp32")
    RESULTS["device"] = info
    return info


# --------------------------------------------------------------------------------------
# 1 + 2. GEMM cuadrado fp32 vs fp16, con y sin flags de cuBLAS
# --------------------------------------------------------------------------------------

def gemm_once(n, dtype):
    import torch

    a = torch.randn(n, n, device="cuda", dtype=torch.float32).to(dtype)
    b = torch.randn(n, n, device="cuda", dtype=torch.float32).to(dtype)
    c = torch.empty(n, n, device="cuda", dtype=dtype)
    flops = 2.0 * n * n * n

    def run():
        torch.mm(a, b, out=c)

    st = bench(run, label="gemm_%d_%s" % (n, dtype))
    st["size"] = n
    st["dtype"] = str(dtype)
    st["flops"] = flops
    st["tflops"] = tflops(flops, st["median_s"])
    st["tflops_best"] = tflops(flops, st["min_s"])
    del a, b, c
    free_mem()
    return st


def set_flag(name, value):
    """Fija un flag de torch.backends.cuda.matmul si existe. Devuelve (existia, previo)."""
    import torch
    obj = torch.backends.cuda.matmul
    if not hasattr(obj, name):
        return False, None
    prev = getattr(obj, name)
    try:
        setattr(obj, name, value)
    except Exception as exc:
        ERRORS.append("no se pudo fijar %s=%s: %r" % (name, value, exc))
        return True, prev
    return True, prev


def probe_gemm():
    import torch

    section("1. GEMM CUADRADO -- LA PREGUNTA DECISIVA (fp16 vs fp32 en sm_61)")

    # Pascal no tiene TF32; se deja explicito para que nadie dude del camino fp32.
    try:
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    except Exception as exc:
        ERRORS.append("allow_tf32: %r" % (exc,))

    flags_present = {}
    for fname in ("allow_fp16_reduced_precision_reduction",
                  "allow_bf16_reduced_precision_reduction",
                  "allow_fp16_accumulation",
                  "allow_tf32",
                  "fp32_precision"):
        has = hasattr(torch.backends.cuda.matmul, fname)
        flags_present[fname] = has
        if has:
            try:
                flags_present[fname + "__value"] = getattr(torch.backends.cuda.matmul, fname)
            except Exception as exc:
                flags_present[fname + "__value"] = "<error %r>" % (exc,)
    RESULTS["matmul_flags_available"] = flags_present
    print("  flags de torch.backends.cuda.matmul:")
    for k, v in flags_present.items():
        print("    %-50s = %s" % (k, v))

    # ---- Guardia de correccion numerica --------------------------------------------------
    # Sin esto, un GEMM fp16 sospechosamente rapido podria ser un no-op o un kernel que no
    # calcula nada. Se compara contra la referencia fp32 en CPU-side (misma entrada).
    try:
        n = 512
        a32 = torch.randn(n, n, device="cuda", dtype=torch.float32)
        b32 = torch.randn(n, n, device="cuda", dtype=torch.float32)
        ref = torch.mm(a32, b32)
        got = torch.mm(a32.half(), b32.half()).float()
        err = (got - ref).abs().max().item()
        rel = err / ref.abs().max().item()
        nz = float(got.abs().mean().item())
        check = {"max_abs_err": err, "max_rel_err": rel, "mean_abs_output": nz,
                 "passed": bool(rel < 1e-2 and nz > 0.0)}
        RESULTS["fp16_numerical_check"] = check
        print()
        print("  Guardia numerica (GEMM 512 fp16 vs referencia fp32):")
        print("    max err rel = %.3e   |salida| media = %.4f   -> %s"
              % (rel, nz, "OK, el fp16 CALCULA de verdad" if check["passed"] else "SOSPECHOSO"))
        del a32, b32, ref, got
        free_mem()
    except Exception as exc:
        RESULTS["fp16_numerical_check"] = {"error": repr(exc)}
        ERRORS.append("guardia numerica: %r" % (exc,))

    sizes = [1024, 2048, 4096]
    sweep = {}
    print()
    print("  %6s  %8s  %12s  %10s  %14s  %5s" % ("N", "dtype", "mediana ms", "TFLOP/s", "mejor TFLOP/s", "reps"))
    print("  " + "-" * 74)
    for n in sizes:
        row = {}
        for dtype, dname in ((torch.float32, "fp32"), (torch.float16, "fp16")):
            try:
                st = gemm_once(n, dtype)
                row[dname] = st
                print("  %6d  %8s  %12.3f  %10.4f  %14.4f  %5d" % (
                    n, dname, st["median_s"] * 1e3, st["tflops"], st["tflops_best"], st["n"]))
            except Exception as exc:
                row[dname] = {"error": repr(exc)}
                ERRORS.append("gemm %d %s: %r" % (n, dname, exc))
                print("  %6d  %8s  ERROR: %r" % (n, dname, exc))
                free_mem()
        if all(isinstance(row.get(d), dict) and "tflops" in row[d] for d in ("fp16", "fp32")):
            row["ratio_fp16_over_fp32"] = row["fp16"]["tflops"] / row["fp32"]["tflops"]
            print("  %6d  %8s  %12s  %10.4f   <-- fp16/fp32" % (
                n, "RATIO", "", row["ratio_fp16_over_fp32"]))
        sweep[str(n)] = row
    RESULTS["gemm_square_sweep"] = sweep

    # ---- 2. Mismo GEMM 4096 variando los flags de cuBLAS -------------------------------
    section("2. MISMO GEMM 4096 VARIANDO FLAGS DE cuBLAS (cambia el camino elegido?)")
    flag_matrix = {}
    n = 4096

    combos = []
    if flags_present.get("allow_fp16_reduced_precision_reduction"):
        combos.append(("allow_fp16_reduced_precision_reduction", True))
        combos.append(("allow_fp16_reduced_precision_reduction", False))
    if flags_present.get("allow_fp16_accumulation"):
        combos.append(("allow_fp16_accumulation", True))
        combos.append(("allow_fp16_accumulation", False))

    if not combos:
        print("  (ningun flag relevante disponible en esta version de torch)")
    else:
        print("  %46s  %6s  %6s  %12s  %10s" % ("flag", "valor", "dtype", "mediana ms", "TFLOP/s"))
        print("  " + "-" * 92)

    for fname, fval in combos:
        existed, prev = set_flag(fname, fval)
        if not existed:
            continue
        key = "%s=%s" % (fname, fval)
        try:
            st16 = gemm_once(n, torch.float16)
            st32 = gemm_once(n, torch.float32)
            flag_matrix[key] = {
                "fp16": st16, "fp32": st32,
                "ratio_fp16_over_fp32": st16["tflops"] / st32["tflops"],
            }
            print("  %46s  %6s  %6s  %12.3f  %10.4f" % (fname, fval, "fp16", st16["median_s"] * 1e3, st16["tflops"]))
            print("  %46s  %6s  %6s  %12.3f  %10.4f" % (fname, fval, "fp32", st32["median_s"] * 1e3, st32["tflops"]))
            print("  %46s  %6s  %6s  %12s  %10.4f" % ("", "", "RATIO", "", flag_matrix[key]["ratio_fp16_over_fp32"]))
        except Exception as exc:
            flag_matrix[key] = {"error": repr(exc)}
            ERRORS.append("flag %s=%s: %r" % (fname, fval, exc))
            print("  %s=%s: ERROR %r" % (fname, fval, exc))
            free_mem()
        finally:
            if prev is not None:
                set_flag(fname, prev)

    RESULTS["gemm_flag_matrix"] = flag_matrix


# --------------------------------------------------------------------------------------
# 3. GEMM con las formas REALES del DiT
# --------------------------------------------------------------------------------------

def probe_dit_gemm(dit_cfg):
    import torch

    hidden = int(dit_cfg.get("hidden_size", FALLBACK_DIT["hidden_size"]))
    inter = int(dit_cfg.get("intermediate_size", FALLBACK_DIT["intermediate_size"]))
    heads = int(dit_cfg.get("num_attention_heads", FALLBACK_DIT["num_attention_heads"]))
    layers = int(dit_cfg.get("num_hidden_layers", FALLBACK_DIT["num_hidden_layers"]))
    L = SEQ_TOKENS_180S

    section("3. GEMM CON FORMAS REALES DEL DiT  [1, %d, %d] x [%d, %d]" % (L, hidden, hidden, hidden))
    print("  hidden_size=%d  num_attention_heads=%d  intermediate_size=%d  num_hidden_layers=%d"
          % (hidden, heads, inter, layers))
    print("  L=%d tokens = 180 s de audio (25 fps / patch_size 2)" % L)

    shapes = [
        ("proj_qkv/o  [1,L,H]x[H,H]", (1, L, hidden), (hidden, hidden)),
        ("mlp_up      [1,L,H]x[H,I]", (1, L, hidden), (hidden, inter)),
        ("mlp_down    [1,L,I]x[I,H]", (1, L, inter), (inter, hidden)),
    ]

    out = {}
    print()
    print("  %28s  %6s  %12s  %10s  %5s" % ("operacion", "dtype", "mediana ms", "TFLOP/s", "reps"))
    print("  " + "-" * 76)
    for name, ashape, bshape in shapes:
        entry = {"a_shape": list(ashape), "b_shape": list(bshape)}
        for dtype, dname in ((torch.float32, "fp32"), (torch.float16, "fp16")):
            try:
                a = torch.randn(*ashape, device="cuda", dtype=torch.float32).to(dtype)
                b = torch.randn(*bshape, device="cuda", dtype=torch.float32).to(dtype)
                flops = 2.0 * ashape[0] * ashape[1] * ashape[2] * bshape[1]

                def run():
                    torch.matmul(a, b)

                st = bench(run, label="dit_%s_%s" % (name, dname))
                st["tflops"] = tflops(flops, st["median_s"])
                st["flops"] = flops
                entry[dname] = st
                print("  %28s  %6s  %12.4f  %10.4f  %5d" % (
                    name, dname, st["median_s"] * 1e3, st["tflops"], st["n"]))
                del a, b
                free_mem()
            except Exception as exc:
                entry[dname] = {"error": repr(exc)}
                ERRORS.append("dit gemm %s %s: %r" % (name, dname, exc))
                print("  %28s  %6s  ERROR: %r" % (name, dname, exc))
                free_mem()
        if all(isinstance(entry.get(d), dict) and "tflops" in entry[d] for d in ("fp16", "fp32")):
            entry["ratio_fp16_over_fp32"] = entry["fp16"]["tflops"] / entry["fp32"]["tflops"]
            print("  %28s  %6s  %12s  %10.4f" % (name, "RATIO", "", entry["ratio_fp16_over_fp32"]))
        out[name] = entry

    RESULTS["dit_gemm"] = {
        "hidden_size": hidden, "intermediate_size": inter,
        "num_attention_heads": heads, "num_hidden_layers": layers,
        "seq_len_tokens": L, "shapes": out,
    }


# --------------------------------------------------------------------------------------
# 4. Atencion: SDPA por backend vs eager
# --------------------------------------------------------------------------------------

def probe_attention(dit_cfg):
    import torch
    import torch.nn.functional as F

    hidden = int(dit_cfg.get("hidden_size", FALLBACK_DIT["hidden_size"]))
    heads = int(dit_cfg.get("num_attention_heads", FALLBACK_DIT["num_attention_heads"]))
    head_dim = int(dit_cfg.get("head_dim") or (hidden // heads))
    L = SEQ_TOKENS_180S
    B = 1

    section("4. ATENCION  q,k,v = [%d, %d, %d, %d]  fp16 -- SDPA vs eager" % (B, heads, L, head_dim))
    attn_flops = 4.0 * B * heads * L * L * head_dim  # qk^T + attn@v
    print("  head_dim=%d  FLOPs de las 2 matmuls = %.2f GFLOP" % (head_dim, attn_flops / 1e9))
    print("  (config declara sliding_window=%s use_sliding_window=%s: la atencion full es cota superior)"
          % (dit_cfg.get("sliding_window"), dit_cfg.get("use_sliding_window")))

    res = {"B": B, "heads": heads, "L": L, "head_dim": head_dim, "attn_flops": attn_flops}

    def make_qkv(dtype):
        q = torch.randn(B, heads, L, head_dim, device="cuda", dtype=torch.float32).to(dtype)
        k = torch.randn(B, heads, L, head_dim, device="cuda", dtype=torch.float32).to(dtype)
        v = torch.randn(B, heads, L, head_dim, device="cuda", dtype=torch.float32).to(dtype)
        return q, k, v

    print()
    print("  %34s  %6s  %12s  %10s  %5s" % ("variante", "dtype", "mediana ms", "TFLOP/s", "reps"))
    print("  " + "-" * 82)

    # --- SDPA por defecto (que elija torch) -------------------------------------------
    for dtype, dname in ((torch.float16, "fp16"), (torch.float32, "fp32")):
        try:
            q, k, v = make_qkv(dtype)

            def run():
                F.scaled_dot_product_attention(q, k, v)

            st = bench(run, label="sdpa_default_%s" % dname)
            st["tflops"] = tflops(attn_flops, st["median_s"])
            res["sdpa_default_%s" % dname] = st
            print("  %34s  %6s  %12.4f  %10.4f  %5d" % (
                "sdpa (backend auto)", dname, st["median_s"] * 1e3, st["tflops"], st["n"]))
            del q, k, v
            free_mem()
        except Exception as exc:
            res["sdpa_default_%s" % dname] = {"error": repr(exc)}
            ERRORS.append("sdpa default %s: %r" % (dname, exc))
            print("  %34s  %6s  ERROR: %s: %s" % (
                "sdpa (backend auto)", dname, type(exc).__name__, str(exc)[:100]))
            free_mem()

    # --- SDPA forzando cada backend ---------------------------------------------------
    backends = {}
    try:
        from torch.nn.attention import SDPBackend, sdpa_kernel
        candidates = [("FLASH_ATTENTION", SDPBackend.FLASH_ATTENTION),
                      ("EFFICIENT_ATTENTION", SDPBackend.EFFICIENT_ATTENTION),
                      ("MATH", SDPBackend.MATH)]
        if hasattr(SDPBackend, "CUDNN_ATTENTION"):
            candidates.insert(2, ("CUDNN_ATTENTION", SDPBackend.CUDNN_ATTENTION))

        for bname, backend in candidates:
            try:
                q, k, v = make_qkv(torch.float16)
                with sdpa_kernel(backend):
                    def run():
                        F.scaled_dot_product_attention(q, k, v)
                    st = bench(run, label="sdpa_%s" % bname)
                st["tflops"] = tflops(attn_flops, st["median_s"])
                backends[bname] = st
                print("  %34s  %6s  %12.4f  %10.4f  %5d" % (
                    "sdpa[" + bname + "]", "fp16", st["median_s"] * 1e3, st["tflops"], st["n"]))
                del q, k, v
                free_mem()
            except Exception as exc:
                backends[bname] = {"error": repr(exc)}
                print("  %34s  %6s  NO DISPONIBLE: %s: %s" % (
                    "sdpa[" + bname + "]", "fp16", type(exc).__name__, str(exc)[:110]))
                free_mem()
    except Exception as exc:
        ERRORS.append("torch.nn.attention no disponible: %r" % (exc,))
        print("  (torch.nn.attention no disponible: %r)" % (exc,))
    res["sdpa_backends"] = backends

    # --- eager: matmul + softmax ------------------------------------------------------
    scale = 1.0 / math.sqrt(head_dim)

    def eager_variant(dtype, softmax_fp32):
        q, k, v = make_qkv(dtype)

        def run():
            s = torch.matmul(q, k.transpose(-2, -1)) * scale
            if softmax_fp32:
                p = torch.softmax(s.float(), dim=-1).to(dtype)
            else:
                p = torch.softmax(s, dim=-1)
            return torch.matmul(p, v)

        st = bench(run, min_reps=5, label="eager")
        st["tflops"] = tflops(attn_flops, st["median_s"])
        del q, k, v
        free_mem()
        return st

    for dtype, dname, sm32, tag in (
        (torch.float16, "fp16", False, "eager fp16 (softmax fp16)"),
        (torch.float16, "fp16", True, "eager fp16 (softmax fp32)"),
        (torch.float32, "fp32", False, "eager fp32"),
    ):
        key = tag.replace(" ", "_").replace("(", "").replace(")", "")
        try:
            st = eager_variant(dtype, sm32)
            res[key] = st
            print("  %34s  %6s  %12.4f  %10.4f  %5d" % (
                tag, dname, st["median_s"] * 1e3, st["tflops"], st["n"]))
        except Exception as exc:
            res[key] = {"error": repr(exc)}
            ERRORS.append("eager %s: %r" % (tag, exc))
            print("  %34s  %6s  ERROR: %s: %s" % (tag, dname, type(exc).__name__, str(exc)[:100]))
            free_mem()

    # --- veredicto atencion ------------------------------------------------------------
    cand = {}
    for k_, v_ in list(res.items()):
        if isinstance(v_, dict) and "median_s" in v_ and (
                k_ == "sdpa_default_fp16" or k_.startswith("eager_fp16")):
            cand[k_] = v_["median_s"]
    for bname, v_ in backends.items():
        if isinstance(v_, dict) and "median_s" in v_:
            cand["sdpa[%s]" % bname] = v_["median_s"]
    if cand:
        winner = min(cand, key=cand.get)
        res["fastest_fp16_variant"] = winner
        res["fastest_fp16_median_s"] = cand[winner]
        print()
        print("  GANADOR en fp16 sobre sm_61: %s  (%.3f ms)" % (winner, cand[winner] * 1e3))
        for name_, t_ in sorted(cand.items(), key=lambda kv: kv[1]):
            print("     %34s : %10.3f ms  (x%.2f)" % (name_, t_ * 1e3, t_ / cand[winner]))

    RESULTS["attention"] = res


# --------------------------------------------------------------------------------------
# 5. Conv1d del decoder VAE (Oobleck)
# --------------------------------------------------------------------------------------

def probe_vae_conv(vae_cfg, seconds=15.0):
    import torch

    dec_ch = int(vae_cfg.get("decoder_channels", FALLBACK_VAE["decoder_channels"]))
    dec_in = int(vae_cfg.get("decoder_input_channels", FALLBACK_VAE["decoder_input_channels"]))
    mults = list(vae_cfg.get("channel_multiples", FALLBACK_VAE["channel_multiples"]))
    ratios = list(vae_cfg.get("downsampling_ratios", FALLBACK_VAE["downsampling_ratios"]))
    audio_ch = int(vae_cfg.get("audio_channels", FALLBACK_VAE["audio_channels"]))
    sr = int(vae_cfg.get("sampling_rate", FALLBACK_VAE["sampling_rate"]))

    total_ratio = 1
    for r in ratios:
        total_ratio *= r
    latent_hz = sr / float(total_ratio)
    L_lat = int(round(seconds * latent_hz))

    section("5. Conv1d DEL DECODER VAE (Oobleck)  chunk = %g s" % seconds)
    print("  decoder_input_channels=%d  decoder_channels=%d  channel_multiples=%s"
          % (dec_in, dec_ch, mults))
    print("  downsampling_ratios=%s (producto %d) -> latente a %.1f Hz" % (ratios, total_ratio, latent_hz))
    print("  chunk de %g s -> L_latente=%d frames -> %d muestras a %d Hz"
          % (seconds, L_lat, int(seconds * sr), sr))

    # El decoder recorre los multiplicadores al reves: 16 -> 8 -> 4 -> 2 -> 1
    rev_mults = list(reversed(mults))
    rev_ratios = list(reversed(ratios))

    layers = [("conv_in       k=7", "conv", dec_in, dec_ch * rev_mults[0], 7, 1, L_lat)]
    L = L_lat
    for i, r in enumerate(rev_ratios):
        cin = dec_ch * rev_mults[i]
        cout = dec_ch * (rev_mults[i + 1] if i + 1 < len(rev_mults) else rev_mults[-1])
        layers.append(("upsample%d T k=%d s=%d" % (i + 1, 2 * r, r), "convT", cin, cout, 2 * r, r, L))
        L = L * r
        layers.append(("res%d          k=7 d=1" % (i + 1), "conv", cout, cout, 7, 1, L))
    layers.append(("conv_out      k=7", "conv", dec_ch * rev_mults[-1], audio_ch, 7, 1, L))

    print()
    print("  %26s  %5s %5s %8s  %6s  %12s  %10s  %5s" % (
        "capa", "C_in", "C_out", "L_in", "dtype", "mediana ms", "GFLOP/s", "reps"))
    print("  " + "-" * 104)

    out = {}
    for name, kind, cin, cout, k, stride, Lin in layers:
        entry = {"kind": kind, "c_in": cin, "c_out": cout, "kernel": k, "stride": stride, "L_in": Lin}
        Lout = Lin * stride if kind == "convT" else Lin
        # OJO: en ConvTranspose1d cada posicion de ENTRADA dispersa hacia k salidas, asi que
        # el coste es 2*Cin*Cout*k*L_IN (no L_out). Usar L_out inflaba el throughput por un
        # factor = stride y daba cifras imposibles (>20 TFLOP/s en una GPU de 6,5 TFLOPS).
        flops = 2.0 * cin * cout * k * Lin
        entry["flops"] = flops
        entry["L_out"] = Lout
        for dtype, dname in ((torch.float32, "fp32"), (torch.float16, "fp16")):
            try:
                if kind == "conv":
                    m = torch.nn.Conv1d(cin, cout, k, padding=k // 2).cuda().to(dtype).eval()
                else:
                    m = torch.nn.ConvTranspose1d(cin, cout, k, stride=stride,
                                                 padding=(k - stride) // 2).cuda().to(dtype).eval()
                x = torch.randn(1, cin, Lin, device="cuda", dtype=dtype)

                def run():
                    with torch.no_grad():
                        m(x)

                st = bench(run, label="vae_%s_%s" % (name, dname))
                st["gflops_per_s"] = (flops / st["median_s"]) / 1e9
                entry[dname] = st
                print("  %26s  %5d %5d %8d  %6s  %12.4f  %10.2f  %5d" % (
                    name, cin, cout, Lin, dname, st["median_s"] * 1e3, st["gflops_per_s"], st["n"]))
                del m, x
                free_mem()
            except Exception as exc:
                short = "%s: %s" % (type(exc).__name__, str(exc)[:100])
                entry[dname] = {"error": short}
                ERRORS.append("vae conv %s %s: %s" % (name, dname, short))
                print("  %26s  %5d %5d %8d  %6s  ERROR: %s" % (name, cin, cout, Lin, dname, short))
                free_mem()
        if all(isinstance(entry.get(d), dict) and "median_s" in entry[d] for d in ("fp16", "fp32")):
            entry["speedup_fp16_over_fp32"] = entry["fp32"]["median_s"] / entry["fp16"]["median_s"]
            print("  %26s  %5s %5s %8s  %6s  %12s  %10.3f" % (
                name, "", "", "", "x fp16", "", entry["speedup_fp16_over_fp32"]))
        out[name] = entry

    tot = {"fp16": 0.0, "fp32": 0.0}
    ok = {"fp16": True, "fp32": True}
    for entry in out.values():
        for d in ("fp16", "fp32"):
            e = entry.get(d)
            if isinstance(e, dict) and "median_s" in e:
                tot[d] += e["median_s"]
            else:
                ok[d] = False
    print()
    for d in ("fp32", "fp16"):
        if ok[d]:
            rt = tot[d] / seconds
            print("  SUMA de capas del decoder (%s) por chunk de %g s: %.1f ms "
                  "-> %.4f s de compute por s de audio (x%.1f tiempo real)"
                  % (d, seconds, tot[d] * 1e3, rt, (1.0 / rt) if rt > 0 else float("inf")))
        else:
            print("  SUMA de capas del decoder (%s): incompleta (hubo errores)" % d)

    RESULTS["vae_conv"] = {
        "chunk_seconds": seconds, "latent_hz": latent_hz, "L_latent": L_lat,
        "sampling_rate": sr, "total_ratio": total_ratio,
        "layers": out,
        "sum_median_s": {d: (tot[d] if ok[d] else None) for d in ("fp16", "fp32")},
    }


# --------------------------------------------------------------------------------------
# 6. Ancho de banda de memoria device-to-device
# --------------------------------------------------------------------------------------

def probe_bandwidth():
    import torch

    section("6. ANCHO DE BANDA DE MEMORIA (device-to-device)")
    print("  (GTX 1070 GDDR5 256-bit: pico teorico 256,3 GB/s)")
    res = {}
    print()
    print("  %28s  %8s  %12s  %16s  %5s" % ("test", "MiB", "mediana ms", "GB/s efectivos", "reps"))
    print("  " + "-" * 80)

    for mb in (256, 512):
        nbytes = mb * 1024 * 1024
        try:
            n_el = nbytes // 4
            src = torch.empty(n_el, device="cuda", dtype=torch.float32).fill_(1.0)
            dst = torch.empty_like(src)

            def run():
                dst.copy_(src)

            st = bench(run, label="d2d_copy_%dMiB" % mb)
            st["gb_per_s"] = (2.0 * nbytes / st["median_s"]) / 1e9
            st["bytes_moved"] = 2 * nbytes
            res["copy_%dMiB" % mb] = st
            print("  %28s  %8d  %12.4f  %16.2f  %5d" % (
                "copy_ fp32 (d2d)", mb, st["median_s"] * 1e3, st["gb_per_s"], st["n"]))

            def run2():
                torch.add(src, 1.0, out=dst)

            st2 = bench(run2, label="d2d_add_%dMiB" % mb)
            st2["gb_per_s"] = (2.0 * nbytes / st2["median_s"]) / 1e9
            res["add_%dMiB" % mb] = st2
            print("  %28s  %8d  %12.4f  %16.2f  %5d" % (
                "add out= (1R+1W)", mb, st2["median_s"] * 1e3, st2["gb_per_s"], st2["n"]))

            del src, dst
            free_mem()
        except Exception as exc:
            res["copy_%dMiB" % mb] = {"error": repr(exc)}
            ERRORS.append("bandwidth %dMiB: %r" % (mb, exc))
            print("  copy %d MiB: ERROR %r" % (mb, exc))
            free_mem()

    try:
        nbytes = 256 * 1024 * 1024
        a = torch.empty(nbytes // 2, device="cuda", dtype=torch.float16).fill_(1.0)
        b = torch.empty_like(a)

        def run3():
            b.copy_(a)

        st3 = bench(run3, label="d2d_copy_fp16_256MiB")
        st3["gb_per_s"] = (2.0 * nbytes / st3["median_s"]) / 1e9
        res["copy_fp16_256MiB"] = st3
        print("  %28s  %8d  %12.4f  %16.2f  %5d" % (
            "copy_ fp16 (d2d)", 256, st3["median_s"] * 1e3, st3["gb_per_s"], st3["n"]))
        del a, b
        free_mem()
    except Exception as exc:
        res["copy_fp16_256MiB"] = {"error": repr(exc)}
        ERRORS.append("bandwidth fp16: %r" % (exc,))

    best = max((v["gb_per_s"] for v in res.values() if isinstance(v, dict) and "gb_per_s" in v),
               default=None)
    res["best_gb_per_s"] = best
    if best:
        print()
        print("  Mejor ancho de banda efectivo: %.1f GB/s (%.0f %% del pico teorico 256,3 GB/s)"
              % (best, 100.0 * best / 256.3))
    RESULTS["bandwidth"] = res


# --------------------------------------------------------------------------------------
# Veredicto
# --------------------------------------------------------------------------------------

def verdict():
    section("VEREDICTO -- CAMINO LENTO 1/64 O PROMOCION A FP32?")
    g = RESULTS.get("gemm_square_sweep", {}).get("4096", {})
    ratio = g.get("ratio_fp16_over_fp32")
    v = {"ratio_fp16_over_fp32_4096": ratio}

    if ratio is None:
        print("  No se pudo determinar el cociente (hubo errores). Ver la seccion de errores.")
        v["verdict"] = "indeterminado"
    else:
        f32 = g["fp32"]["tflops"]
        f16 = g["fp16"]["tflops"]
        print("  GEMM 4096^3   fp32 = %8.4f TFLOP/s" % f32)
        print("  GEMM 4096^3   fp16 = %8.4f TFLOP/s" % f16)
        print("  COCIENTE fp16/fp32 = %8.4f   (1/64 = 0.0156)" % ratio)
        print()
        if ratio < 0.05:
            v["verdict"] = "camino_lento_1_64"
            print("  >>> CAMINO LENTO CONFIRMADO. cuBLAS ejecuta fp16 NATIVO en sm_61 (1/64).")
            print("  >>> El artefacto fp16 residente NO es utilizable en fp16 para computo.")
            print("  >>> Hay que hacer upcast a fp32 (y la VRAM pasa a ser el problema) o cambiar de GPU.")
        elif ratio < 0.85:
            v["verdict"] = "degradado_parcial"
            print("  >>> DEGRADACION PARCIAL: fp16 es mas lento que fp32 pero no 1/64.")
            print("  >>> Conviene ejecutar el computo en fp32 y guardar los pesos en fp16.")
        elif ratio <= 1.15:
            v["verdict"] = "promociona_a_fp32"
            print("  >>> cuBLAS PROMOCIONA a fp32. Pascal es USABLE: se paga el precio del fp32")
            print("  >>> (~6,5 TFLOPS pico) pero se conserva la ventaja de memoria del fp16.")
        else:
            v["verdict"] = "fp16_mas_rapido"
            print("  >>> fp16 SUPERA a fp32 (ancho de banda: la mitad de bytes). Pascal usable.")

        v["fp32_tflops"] = f32
        v["fp16_tflops"] = f16
        v["fp32_pct_of_6_5_tflops_peak"] = 100.0 * f32 / 6.5

    # Extrapolacion grosera: solo los GEMM lineales del DiT + atencion. COTA INFERIOR.
    d = RESULTS.get("dit_gemm", {})
    try:
        sh = d["shapes"]
        layers = d["num_hidden_layers"]
        for dname in ("fp16", "fp32"):
            per_layer = 0.0
            okk = True
            e = sh["proj_qkv/o  [1,L,H]x[H,H]"].get(dname)
            if isinstance(e, dict) and "median_s" in e:
                per_layer += 4 * e["median_s"]   # q,k,v,o (cota alta: con GQA k/v son mas baratas)
            else:
                okk = False
            for key in ("mlp_up      [1,L,H]x[H,I]", "mlp_down    [1,L,I]x[I,H]"):
                e = sh[key].get(dname)
                if isinstance(e, dict) and "median_s" in e:
                    per_layer += e["median_s"]
                else:
                    okk = False
            if dname == "fp16":
                att = RESULTS.get("attention", {}).get("fastest_fp16_median_s")
            else:
                att = RESULTS.get("attention", {}).get("sdpa_default_fp32", {}).get("median_s")
            if att:
                per_layer += att
            else:
                okk = False
            if okk:
                per_step = per_layer * layers
                v["dit_step_estimate_s_%s" % dname] = per_step
                print()
                print("  Estimacion GRUESA (%s) de 1 paso de difusion @180 s "
                      "(solo linears+attn, %d capas): %.3f s" % (dname, layers, per_step))
                for steps in (8, 20, 50):
                    print("      %3d pasos -> %8.1f s (%6.2f min)  |  10 pistas -> %7.1f min"
                          % (steps, per_step * steps, per_step * steps / 60.0,
                             per_step * steps * 10 / 60.0))
                v["dit_10_tracks_min_%s" % dname] = {
                    str(s): per_step * s * 10 / 60.0 for s in (8, 20, 50)}
    except Exception as exc:
        ERRORS.append("extrapolacion: %r" % (exc,))

    print()
    print("  AVISO: la extrapolacion anterior IGNORA norms, activaciones, RoPE, el condition")
    print("  encoder, el text encoder y el VAE. Es una COTA INFERIOR del tiempo por paso.")
    RESULTS["verdict"] = v


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="microbenchmark torch puro en sm_61")
    ap.add_argument("--dit-config", default=None, help="ruta a acestep-v15-turbo/config.json")
    ap.add_argument("--vae-config", default=None, help="ruta a vae/config.json")
    ap.add_argument("--vae-chunk-seconds", type=float, default=15.0,
                    help="segundos de audio del chunk del decoder VAE (def 15)")
    ap.add_argument("--skip", default="", help="secciones a saltar, csv: gemm,dit,attn,vae,bw")
    args = ap.parse_args()

    skip = set(s.strip() for s in args.skip.split(",") if s.strip())

    t_start = time.time()
    print("#" * 94)
    print("# pascal_speed_probe.py -- microbenchmark de torch puro (SIN modelo) en sm_61")
    print("# Pregunta: el GEMM fp16 en GP104 usa el camino nativo lento (1/64) o promociona a fp32?")
    print("#" * 94)

    try:
        import torch
    except Exception as exc:
        print("FATAL: no se pudo importar torch: %r" % (exc,))
        traceback.print_exc()
        print("---JSON---")
        print(json.dumps({"fatal": repr(exc)}, indent=2))
        return 2

    if not torch.cuda.is_available():
        msg = "FATAL: torch.cuda.is_available() == False (falta --gpus all?)"
        print(msg)
        print("---JSON---")
        print(json.dumps({"fatal": msg, "torch_version": torch.__version__,
                          "cuda_version": torch.version.cuda}, indent=2))
        return 3

    dit_cands = ([args.dit_config] if args.dit_config else []) + DEFAULT_DIT_CONFIG_CANDIDATES
    vae_cands = ([args.vae_config] if args.vae_config else []) + DEFAULT_VAE_CONFIG_CANDIDATES
    dit_cfg, dit_src = load_json_first(dit_cands, FALLBACK_DIT, "dit_config")
    vae_cfg, vae_src = load_json_first(vae_cands, FALLBACK_VAE, "vae_config")
    RESULTS["config_sources"] = {"dit": dit_src, "vae": vae_src}
    print()
    print("  config DiT desde: %s" % dit_src)
    print("  config VAE desde: %s" % vae_src)

    probe_device()

    steps = [
        ("gemm", lambda: probe_gemm()),
        ("dit", lambda: probe_dit_gemm(dit_cfg)),
        ("attn", lambda: probe_attention(dit_cfg)),
        ("vae", lambda: probe_vae_conv(vae_cfg, args.vae_chunk_seconds)),
        ("bw", lambda: probe_bandwidth()),
    ]
    for name, fn in steps:
        if name in skip:
            print("\n  (seccion '%s' saltada por --skip)" % name)
            continue
        try:
            fn()
        except Exception as exc:
            tb = traceback.format_exc()
            ERRORS.append("SECCION %s abortada: %r" % (name, exc))
            RESULTS["section_%s_traceback" % name] = tb
            print("\n  !!! SECCION '%s' ABORTADA: %r" % (name, exc))
            print(tb)
            try:
                free_mem()
            except Exception:
                pass

    try:
        verdict()
    except Exception as exc:
        ERRORS.append("verdict: %r" % (exc,))
        print("  veredicto no calculable: %r" % (exc,))

    RESULTS["errors"] = ERRORS
    RESULTS["elapsed_s"] = time.time() - t_start

    if ERRORS:
        section("ERRORES / MEDICIONES NO REALIZADAS")
        for e in ERRORS:
            print("  - %s" % e)

    print()
    print("  Tiempo total del probe: %.1f s" % RESULTS["elapsed_s"])
    print()
    print("---JSON---")
    print(json.dumps(RESULTS, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
