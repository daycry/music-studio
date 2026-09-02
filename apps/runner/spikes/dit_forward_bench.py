#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dit_forward_bench.py -- Cronometra UN forward del DiT real de ACE-Step 1.5 turbo
sobre el artefacto de pesos de produccion, con las formas reales de inferencia.

Objetivo: convertir el microbenchmark sintetico de pascal_speed_probe.py (GEMMs
sueltos) en una MEDIDA DEL MODELO REAL, para extrapolar cuanto tarda una pista y
cuanto tardan las 10 pistas del gate G1.

El modelo turbo hace 8 pasos de difusion SIN CFG -> 1 forward del DiT por paso.

Que hace, en orden:
  1. Lee el config del propio artefacto (aux.config.acestep_json, tensor U8).
  2. Instancia AceStepConditionGenerationModel en meta (coste 0 de RAM).
  3. Carga por STREAMING solo las claves dit.* del safetensors (nunca los 6 GB):
     - dit.decoder.* (el DiT) empaquetadas en UN buffer contiguo -> UNA copia H2D.
     - el resto de dit.* a CPU (para que load_state_dict(strict=True) valide de
       verdad las 677 claves).
     Se quita el prefijo 'dit.' y se hace load_state_dict(strict=True, assign=True).
  4. Reporta VRAM (memory_allocated / max_memory_allocated / mem_get_info).
  5. Cronometra N forwards por cada longitud L (tokens del DiT tras el patchify),
     con torch.cuda.synchronize() antes y despues de cada repeticion. MEDIANA.
  6. Comprueba que la salida es finita (sin NaN/inf): el margen fp16 es real.
  7. Si algo desborda la VRAM, CAPTURA el OOM y reporta a que L ocurre.
  8. Imprime tabla + bloque JSON tras '---JSON---'.

USO (dentro del contenedor; /work es SOLO LECTURA, no escribimos nada):

  docker run --rm --gpus all
    -v "D:\\srv\\ace-step\\weights:/weights:ro"
    -v "D:\\srv\\ace-step\\upstream\\<rev>\\acestep-v15-turbo:/upstream:ro"
    -v "C:\\Users\\daycry\\...\\apps\\runner:/work:ro"
    --entrypoint python ace-step-runner:t05 /work/spikes/dit_forward_bench.py

Flags: --reps N  --lengths 375,2250  --attn eager|sdpa  --enc-len 210
       --weights PATH  --code-dir PATH  --skip-full-vram

INVARIANTES DEL PROYECTO respetados:
  - Solo safetensors. Nunca torch.load / pickle.
  - Nunca AutoModel + trust_remote_code: se importa la CLASE directamente desde el
    codigo upstream montado read-only (que sera vendorizado y revisado en T-03).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import types

# ---------------------------------------------------------------------------
# 0. Argumentos
# ---------------------------------------------------------------------------
P = argparse.ArgumentParser()
P.add_argument("--weights", default="/weights/ace_step_1_5.safetensors")
P.add_argument("--code-dir", default=None,
               help="Dir con modeling_acestep_v15_turbo.py y configuration_acestep_v15.py. "
                    "Por defecto se autodetecta: primero el codigo VENDORIZADO que viaja en la "
                    "imagen, y solo si no esta, /upstream montado a mano.")
P.add_argument("--reps", type=int, default=5)
P.add_argument("--warmup", type=int, default=2)
P.add_argument("--lengths", default="375,750,1125,1500,2250,3000,3750",
               help="Longitudes L en TOKENS DEL DiT (L = segundos*25/patch_size)")
P.add_argument("--enc-len", type=int, default=210,
               help="L_enc del encoder_hidden_states (cross-attention)")
P.add_argument("--bsz", type=int, default=1,
               help="Tamano de lote del forward. 1 = turbo (sin guia) y tambien la "
                    "pasada gemela SECUENCIAL del sft. 2 = la pasada gemela POR LOTE "
                    "de upstream (cond + incond en una sola llamada), que es lo que "
                    "hay que medir para saber si cabe en 8 GB.")
P.add_argument("--attn", default="eager", choices=["eager", "sdpa"])
P.add_argument("--steps", type=int, default=8, help="Pasos de difusion del turbo (sin CFG)")
P.add_argument("--tracks", type=int, default=10, help="Pistas del gate G1")
P.add_argument("--loop-check", default="2250",
               help="Longitudes L en las que ejecutar ADEMAS el bucle real de 8 pasos "
                    "(schedule shift=3.0 hardcodeado upstream, Euler ODE, cache de "
                    "cross-attn compartida). '' para desactivar.")
P.add_argument("--skip-full-vram", action="store_true",
               help="No medir la VRAM del dit.* completo residente al final")
P.add_argument("--load-mode", default="bulk", choices=["bulk", "pertensor"],
               help="bulk: UNA lectura secuencial del rango contiguo dit.decoder.* "
                    "(mide 12x mas rapido que el mmap de safe_open sobre bind mount). "
                    "pertensor: safe_open.get_tensor() clave a clave.")
ARGS = P.parse_args()

RESULT = {
    "script": "dit_forward_bench.py",
    "ok": False,
    "errors": [],
    "warnings": [],
}


def log(*a):
    print(*a, flush=True)


def hdr(t):
    log("")
    log("=" * 78)
    log(t)
    log("=" * 78)


t_script0 = time.time()

# ---------------------------------------------------------------------------
# 1. Imports pesados + stub de ResidualFSQ (necesario para instanciar en meta)
# ---------------------------------------------------------------------------
import torch                       # noqa: E402
import torch.nn as nn              # noqa: E402
from safetensors import safe_open  # noqa: E402


# ---- STUB de vector_quantize_pytorch.ResidualFSQ ----------------------------
# El ResidualFSQ real llama a .item() sobre tensores en __init__
# (finite_scalar_quantization.py:125  self._levels.prod().item()  y
#  residual_fsq.py:84  assert (levels_tensor > 1).all()), lo que REVIENTA bajo
# torch.device('meta'):  RuntimeError: Tensor.item() cannot be called on meta tensors
# El quantizer solo aporta 4 tensores al checkpoint (project_in/project_out); los
# sub-FSQ registran buffers NO persistentes que no aparecen en el state_dict.
# Este banco solo ejecuta el DiT (model.decoder), asi que un stub con la misma
# superficie de state_dict basta y mantiene load_state_dict(strict=True) honesto.
class _ResidualFSQStub(nn.Module):
    def __init__(self, dim, levels, num_quantizers=1, **kw):
        super().__init__()
        n = len(levels) * num_quantizers
        self.project_in = nn.Linear(dim, n)
        self.project_out = nn.Linear(n, dim)

    def forward(self, x):  # nunca se llama en este banco
        raise NotImplementedError("ResidualFSQ stub: solo para instanciar el grafo")


_vq = types.ModuleType("vector_quantize_pytorch")
_vq.ResidualFSQ = _ResidualFSQStub
sys.modules["vector_quantize_pytorch"] = _vq

# Resolucion del codigo del modelo. El orden importa: primero el VENDORIZADO,
# que viaja dentro de la imagen fijado por hash (CLAUDE.md prohibe
# `trust_remote_code`, asi que el codigo de terceros que se ejecuta tiene que
# estar en el repo y ser revisable en un diff). El montaje manual de /upstream
# queda solo como respaldo para ejecutar fuera del contenedor.
_CANDIDATOS = [ARGS.code_dir] if ARGS.code_dir else [
    "/app/adapters/ace_step/vendor",                                   # imagen
    os.path.join(os.path.dirname(os.path.abspath(__file__)),           # arbol local
                 "..", "adapters", "ace_step", "vendor"),
    "/upstream",                                                       # respaldo
]
_CODE_DIR = None
for _c in _CANDIDATOS:
    if _c and os.path.isfile(os.path.join(_c, "modeling_acestep_v15_turbo.py")):
        _CODE_DIR = os.path.abspath(_c)
        break
if _CODE_DIR is None:
    raise SystemExit(
        "No encuentro el codigo del modelo. Buscado en: "
        + ", ".join(repr(c) for c in _CANDIDATOS if c)
        + ". Opciones: (a) usar la imagen del runner, que ya lo lleva vendorizado en "
          "/app/adapters/ace_step/vendor; (b) pasar --code-dir; (c) montar el upstream "
          "en /upstream."
    )
print("[bench] codigo del modelo desde: %s" % _CODE_DIR)
sys.path.insert(0, _CODE_DIR)
import configuration_acestep_v15 as cfgmod     # noqa: E402
import modeling_acestep_v15_turbo as mod       # noqa: E402

hdr("0. ENTORNO")
dev = torch.device("cuda")
assert torch.cuda.is_available(), "No hay CUDA en el contenedor"
props = torch.cuda.get_device_properties(0)
cap = torch.cuda.get_device_capability(0)
free0, total0 = torch.cuda.mem_get_info()
env = {
    "torch": torch.__version__,
    "gpu": props.name,
    "capability": "sm_%d%d" % cap,
    "sm_count": props.multi_processor_count,
    "vram_total_MiB": round(total0 / 2 ** 20, 1),
    "vram_free_before_MiB": round(free0 / 2 ** 20, 1),
    "attn_impl_requested": ARGS.attn,
}
for k, v in env.items():
    log("  %-26s %s" % (k, v))
RESULT["env"] = env

# ---------------------------------------------------------------------------
# 2. Config desde el propio artefacto (aux.config.acestep_json)
# ---------------------------------------------------------------------------
hdr("1. CONFIG DESDE EL ARTEFACTO (aux.config.acestep_json)")
f = safe_open(ARGS.weights, framework="pt", device="cpu")
all_keys = list(f.keys())
cfg_bytes = f.get_tensor("aux.config.acestep_json").numpy().tobytes()
cfg_dict = json.loads(cfg_bytes.decode("utf-8"))
log("  artefacto: %s" % ARGS.weights)
log("  tensores totales: %d" % len(all_keys))
log("  config: %d bytes, %d claves" % (len(cfg_bytes), len(cfg_dict)))
log("  hidden=%s layers=%s heads=%s/%s head_dim=%s ffn=%s in_ch=%s patch=%s sliding=%s" % (
    cfg_dict["hidden_size"], cfg_dict["num_hidden_layers"], cfg_dict["num_attention_heads"],
    cfg_dict["num_key_value_heads"], cfg_dict["head_dim"], cfg_dict["intermediate_size"],
    cfg_dict["in_channels"], cfg_dict["patch_size"], cfg_dict["sliding_window"]))

config = cfgmod.AceStepConfig(**cfg_dict)
RESULT["config"] = dict((k, cfg_dict[k]) for k in (
    "hidden_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads",
    "head_dim", "intermediate_size", "in_channels", "patch_size",
    "audio_acoustic_hidden_dim", "sliding_window", "use_sliding_window", "rope_theta"))

# ---------------------------------------------------------------------------
# 3. Instanciar en meta
# ---------------------------------------------------------------------------
hdr("2. INSTANCIACION EN META")
t0 = time.time()
mod.AceStepPreTrainedModel._init_weights = lambda self, module: None   # no-init
torch.set_default_dtype(torch.float16)
with torch.device("meta"):
    model = mod.AceStepConditionGenerationModel(config)
torch.set_default_dtype(torch.float32)
t_meta = time.time() - t0
model.eval()

# El selector de atencion (modeling L348-352) hace ALL_ATTENTION_FUNCTIONS[impl]
# si impl != 'eager'. set_attn_implementation('eager') NO es fiable: hay que
# asignar directamente. Degradacion SILENCIOSA de ~3,7x si se queda en 'sdpa'.
attn_before = getattr(model.config, "_attn_implementation", None)
model.config._attn_implementation = ARGS.attn
assert model.decoder.config._attn_implementation == ARGS.attn, "el config no se propago"
assert model.decoder.layers[0].self_attn.config._attn_implementation == ARGS.attn
log("  instanciado en meta en %.2fs" % t_meta)
log("  _attn_implementation: %r -> %r   (ASSERT ok)" % (attn_before, model.config._attn_implementation))
log("  layer_types[:6] = %s" % (config.layer_types[:6],))
RESULT["meta_instantiation_s"] = round(t_meta, 3)
RESULT["attn_impl_before"] = attn_before

# ---------------------------------------------------------------------------
# 4. Carga por streaming de dit.*
# ---------------------------------------------------------------------------
hdr("3. CARGA POR STREAMING DE dit.*  (sin materializar los 6 GB)")

_DT = {"F16": torch.float16, "F32": torch.float32, "BF16": torch.bfloat16,
       "F64": torch.float64, "I64": torch.int64, "I32": torch.int32,
       "I16": torch.int16, "I8": torch.int8, "U8": torch.uint8, "BOOL": torch.bool}

def read_st_header(path):
    """Cabecera JSON del safetensors (8 B de longitud + JSON). Sin pickle.

    Devuelve (header_dict, data_section_start_offset).
    """
    with open(path, "rb") as fh:
        n = int.from_bytes(fh.read(8), "little")
        return json.loads(fh.read(n).decode("utf-8")), 8 + n


# ORDEN DE LECTURA POR OFFSET EN EL FICHERO, no alfabetico.
# MEDIDO: leyendo las 476 claves dit.decoder.* en orden alfabetico el empaquetado
# tardo 382,3 s (8,2 MiB/s) porque el artefacto vive en un HDD 5400 rpm y el orden
# alfabetico ('layers.0','layers.1','layers.10',...) provoca seek aleatorio sobre
# 4,5 GB. Ordenando por data_offsets el acceso es secuencial.
_hdr, DATA_START = read_st_header(ARGS.weights)
_off = dict((k, tuple(v["data_offsets"])) for k, v in _hdr.items() if k != "__metadata__")
_off0 = dict((k, v[0]) for k, v in _off.items())

dit_keys = sorted((k for k in all_keys if k.startswith("dit.")), key=lambda k: _off0[k])
dec_keys = [k for k in dit_keys if k.startswith("dit.decoder.")]
oth_keys = [k for k in dit_keys if not k.startswith("dit.decoder.")]
log("  claves dit.*                                      : %d" % len(dit_keys))
log("  de las cuales dit.decoder.* (el DiT)              : %d" % len(dec_keys))
log("  resto (encoder/tokenizer/detokenizer/null_cond)   : %d" % len(oth_keys))


def meta_of(keys):
    """Metadatos (shape/dtype/bytes) sin materializar nada."""
    out = []
    for k in keys:
        sl = f.get_slice(k)
        shape = tuple(int(x) for x in sl.get_shape())
        dt = _DT[sl.get_dtype()]
        n = 1
        for s in shape:
            n *= s
        out.append((k, shape, dt, n * dt.itemsize))
    return out


dec_meta = meta_of(dec_keys)
oth_meta = meta_of(oth_keys)
dec_bytes = sum(m[3] for m in dec_meta)
oth_bytes = sum(m[3] for m in oth_meta)
log("  bytes dit.decoder.* : %d = %.1f MiB" % (dec_bytes, dec_bytes / 2 ** 20))
log("  bytes resto dit.*   : %d = %.1f MiB" % (oth_bytes, oth_bytes / 2 ** 20))
log("  bytes dit.* total   : %.1f MiB" % ((dec_bytes + oth_bytes) / 2 ** 20))

# --- empaquetado contiguo + UNA copia H2D -----------------------------------
# Medido en spikes previos: 476 copias H2D pequenas bajo WDDM = 110-123 s
# (~27 MiB/s efectivos, ~230 ms de sobrecarga por copia). Una copia unica de
# 3005 MiB tarda ~0,83 s. No es un truco del banco: es la mitigacion que el
# runner de produccion tendra que aplicar al arranque en frio.
# dit.decoder.* es CONTIGUO en el fichero (bytes 0..3.150.917.760 de la seccion de
# datos) y en orden. Eso permite UNA lectura secuencial con read()/readinto() en vez
# de 476 get_tensor() sobre el mmap.
# MEDIDO: el mmap de safe_open sobre el bind mount de Docker Desktop da ~10 MiB/s
# (fallos de pagina de 4 KiB a traves de la capa de virtualizacion del sistema de
# ficheros); un read() secuencial del MISMO rango da ~120 MiB/s. 12x en el arranque
# en frio del runner.
dec_start = min(_off[k][0] for k in dec_keys)
dec_end = max(_off[k][1] for k in dec_keys)
contiguous = (dec_end - dec_start) == dec_bytes
aligned = all((_off[k][0] - dec_start) % 16 == 0 or
              (_off[k][0] - dec_start) % _DT[f.get_slice(k).get_dtype()].itemsize == 0
              for k in dec_keys)
use_bulk = (ARGS.load_mode == "bulk") and contiguous and aligned
log("  rango dit.decoder.* en el fichero: [%d, %d) contiguo=%s alineado=%s -> modo %s" % (
    dec_start, dec_end, contiguous, aligned, "BULK read()" if use_bulk else "get_tensor()"))

dec_lut = dict((m[0], m) for m in dec_meta)
cpu_side = {}
t_oth = 0.0

if use_bulk:
    total_bytes = dec_bytes
    buf_off = dict((k, _off[k][0] - dec_start) for k in dec_keys)
    cpu_buf = torch.empty(total_bytes, dtype=torch.uint8)
    mv = memoryview(cpu_buf.numpy())
    t0 = time.time()
    with open(ARGS.weights, "rb", buffering=0) as fh:
        fh.seek(DATA_START + dec_start)
        got, CH = 0, 8 << 20
        while got < total_bytes:
            n = fh.readinto(mv[got:got + min(CH, total_bytes - got)])
            if not n:
                raise IOError("lectura corta del artefacto en %d" % got)
            got += n
    t_pack = time.time() - t0
    t1 = time.time()
    for k in oth_keys:
        cpu_side[k] = f.get_tensor(k)        # a CPU: valida strict=True de verdad
    t_oth = time.time() - t1
else:
    offs, off = [], 0
    for k, shape, dt, nb in dec_meta:
        off = (off + 15) // 16 * 16      # alineacion a 16 B para permitir .view(dtype)
        offs.append(off)
        off += nb
    total_bytes = off
    buf_off = dict(zip((m[0] for m in dec_meta), offs))
    cpu_buf = torch.empty(total_bytes, dtype=torch.uint8)
    t0 = time.time()
    for k in dit_keys:                       # una pasada en orden de fichero
        if k in dec_lut:
            _, shape, dt, nb = dec_lut[k]
            if nb:
                o = buf_off[k]
                cpu_buf[o:o + nb].view(dt).view(shape).copy_(f.get_tensor(k))
        else:
            t1 = time.time()
            cpu_side[k] = f.get_tensor(k)
            t_oth += time.time() - t1
    t_pack = time.time() - t0 - t_oth

torch.cuda.synchronize()
t0 = time.time()
gpu_buf = torch.empty(total_bytes, dtype=torch.uint8, device=dev)
gpu_buf.copy_(cpu_buf)
torch.cuda.synchronize()
t_h2d = time.time() - t0
del cpu_buf

sd = {}
for k, shape, dt, nb in dec_meta:
    o = buf_off[k]
    sd[k[len("dit."):]] = gpu_buf[o:o + nb].view(dt).view(shape)
for k, v in cpu_side.items():
    sd[k[len("dit."):]] = v

log("  lectura dit.decoder.* -> buffer CPU (%s) : %.2fs (%.1f MiB/s)" % (
    "bulk" if use_bulk else "get_tensor", t_pack,
    dec_bytes / 2 ** 20 / max(t_pack, 1e-9)))
log("  UNA copia H2D de %.1f MiB                : %.3fs (%.0f MiB/s)" % (
    total_bytes / 2 ** 20, t_h2d, total_bytes / 2 ** 20 / max(t_h2d, 1e-9)))
log("  resto dit.* (%d claves) leido a CPU        : %.2fs" % (len(oth_keys), t_oth))

# --- load_state_dict(strict=True) -------------------------------------------
t0 = time.time()
missing, unexpected = model.load_state_dict(sd, strict=True, assign=True)
t_lsd = time.time() - t0
log("  load_state_dict(strict=True, assign=True)  : %.2fs  missing=%s unexpected=%s" % (
    t_lsd, list(missing), list(unexpected)))
assert not missing and not unexpected

dit = model.decoder

# --- buffers NO persistentes que quedan en meta tras el assign --------------
# rotary_emb.inv_freq / original_inv_freq NO estan en el state_dict; si se dejan
# en meta el fallo NO aparece al cargar sino en el PRIMER FORWARD:
#   NotImplementedError: Cannot copy out of meta tensor; no data!
meta_bufs_before = [n for n, b in dit.named_buffers() if b.is_meta]
from transformers.models.qwen3.modeling_qwen3 import Qwen3RotaryEmbedding   # noqa: E402
dit.rotary_emb = Qwen3RotaryEmbedding(config).to(dev)
meta_bufs_after = [n for n, b in dit.named_buffers() if b.is_meta]
meta_params_after = [n for n, p in dit.named_parameters() if p.is_meta]
log("  buffers en meta antes del fix : %s" % meta_bufs_before)
log("  buffers en meta despues       : %s" % meta_bufs_after)
log("  parametros en meta            : %s" % meta_params_after)
assert not meta_bufs_after and not meta_params_after, "quedan tensores en meta"

n_par = sum(p.numel() for p in dit.parameters())
dtypes = sorted(set(str(p.dtype) for p in dit.parameters()))
devs = sorted(set(str(p.device) for p in dit.parameters()))
log("  DiT: %s parametros  dtypes=%s devices=%s" % ("{:,}".format(n_par), dtypes, devs))

RESULT["load"] = {
    "keys_dit": len(dit_keys), "keys_dit_decoder": len(dec_keys),
    "keys_dit_other": len(oth_keys),
    "bytes_dit_decoder": dec_bytes, "bytes_dit_other": oth_bytes,
    "load_mode": "bulk" if use_bulk else "get_tensor",
    "dit_decoder_contiguous_in_file": contiguous,
    "read_dit_decoder_s": round(t_pack, 3),
    "read_dit_decoder_MiB_per_s": round(dec_bytes / 2 ** 20 / max(t_pack, 1e-9), 1),
    "pack_cpu_s": round(t_pack, 3), "h2d_single_copy_s": round(t_h2d, 3),
    "h2d_MiB_per_s": round(total_bytes / 2 ** 20 / max(t_h2d, 1e-9), 1),
    "read_other_cpu_s": round(t_oth, 3),
    "load_state_dict_s": round(t_lsd, 3),
    "strict_missing": list(missing), "strict_unexpected": list(unexpected),
    "dit_params": n_par, "dit_param_dtypes": dtypes,
    "meta_buffers_fixed": meta_bufs_before,
}

# ---------------------------------------------------------------------------
# 5. VRAM tras cargar
# ---------------------------------------------------------------------------
hdr("4. VRAM TRAS CARGAR EL DiT")
torch.cuda.synchronize()
alloc = torch.cuda.memory_allocated()
maxalloc = torch.cuda.max_memory_allocated()
reserved = torch.cuda.memory_reserved()
free1, total1 = torch.cuda.mem_get_info()
vram_load = {
    "memory_allocated_MiB": round(alloc / 2 ** 20, 1),
    "max_memory_allocated_MiB": round(maxalloc / 2 ** 20, 1),
    "memory_reserved_MiB": round(reserved / 2 ** 20, 1),
    "mem_get_info_free_MiB": round(free1 / 2 ** 20, 1),
    "cuda_ctx_plus_overhead_MiB": round((total1 - free1 - alloc) / 2 ** 20, 1),
}
for k, v in vram_load.items():
    log("  %-34s %s" % (k, v))
log("  NOTA: en GPU solo esta dit.decoder.* (el DiT). El resto de dit.* "
    "(%.0f MiB) esta en CPU a proposito." % (oth_bytes / 2 ** 20))
RESULT["vram_after_load"] = vram_load

# ---------------------------------------------------------------------------
# 6. Entradas sinteticas con las formas REALES
# ---------------------------------------------------------------------------
hdr("5. ENTRADAS")
FPS = 25.0
PATCH = int(config.patch_size)
AC = int(config.audio_acoustic_hidden_dim)     # 64
HID = int(config.hidden_size)                  # 2048

# aux.silence_latent: F32 [1, 64, 15000] (channels-first). El modelo lo consume
# como [B, T, 64] -> hay que TRASPONER (upstream lo hace al cargar). Usar el
# latente real hace que la comprobacion de NaN/inf sea significativa.
sil = f.get_tensor("aux.silence_latent")
log("  aux.silence_latent en el artefacto: %s %s (channels-first)" % (tuple(sil.shape), sil.dtype))
sil = sil.transpose(1, 2).contiguous().to(torch.float16)
log("  tras transpose(1,2) -> %s  (frames: %d = %.0f s)" % (
    tuple(sil.shape), sil.shape[1], sil.shape[1] / FPS))
assert sil.shape[-1] == AC, "silence_latent mal orientado"


def make_inputs(L, enc_len, gen, bsz=1):
    """L = tokens del DiT (tras patchify). T = PATCH*L frames latentes @25 Hz.

    `bsz` replica las entradas igual que hace la guia POR LOTE de upstream
    (`torch.cat([xt, xt])` y el condicionamiento concatenado con el nulo): lo que
    se mide con bsz=2 es EXACTAMENTE el coste de esa pasada gemela en un solo
    forward, frente a bsz=1, que es el de la secuencial.
    """
    T = L * PATCH
    if T > sil.shape[1]:
        reps = int(math.ceil(T / float(sil.shape[1])))
        src = sil.repeat(1, reps, 1)[:, :T, :].to(dev)
    else:
        src = sil[:, :T, :].to(dev)
    mask = torch.ones(1, T, AC, dtype=torch.float16, device=dev)      # chunk_masks
    ctx = torch.cat([src, mask], dim=-1)                              # [1,T,128]
    x = torch.randn(1, T, AC, generator=gen, device=dev, dtype=torch.float16)
    enc = torch.randn(1, enc_len, HID, generator=gen, device=dev, dtype=torch.float16) * 0.02
    ts = torch.full((1,), 1.0, dtype=torch.float16, device=dev)       # t=1.0, primer paso turbo
    if bsz > 1:
        x = x.repeat(bsz, 1, 1)
        ctx = ctx.repeat(bsz, 1, 1)
        enc = enc.repeat(bsz, 1, 1)
        ts = ts.repeat(bsz)
    return x, ctx, enc, ts, T


gen = torch.Generator(device=dev)
gen.manual_seed(1234)
log("  hidden_states [1,T,%d] ~N(0,1) | context_latents [1,T,128] = "
    "cat(silence_latent, ones) | encoder_hidden_states [1,%d,%d]*0.02" % (AC, ARGS.enc_len, HID))
log("  timestep = timestep_r = 1.0 (fp16) -> time_embed_r recibe 0 (turbo, sin CFG)")
log("  use_cache=False y past_key_values=None en TODAS las reps: cada forward "
    "recomputa la K/V de cross-attn (cota SUPERIOR; el bucle real la cachea).")

# ---------------------------------------------------------------------------
# 7. Benchmark
# ---------------------------------------------------------------------------
hdr("6. BENCHMARK: %d forwards por longitud (warmup %d), attn=%s, bsz=%d" % (
    ARGS.reps, ARGS.warmup, ARGS.attn, ARGS.bsz))

lengths = [int(x) for x in ARGS.lengths.split(",") if x.strip()]
rows = []
oom_at = None


def one_forward(x, ctx, enc, ts):
    with torch.no_grad():
        out = dit(
            hidden_states=x,
            timestep=ts,
            timestep_r=ts,
            attention_mask=None,
            encoder_hidden_states=enc,
            encoder_attention_mask=None,
            context_latents=ctx,
            use_cache=False,
            past_key_values=None,
        )
    return out[0]


for L in lengths:
    T = L * PATCH
    secs = T / FPS
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    entry = {"L_tokens": L, "T_frames": T, "audio_s": round(secs, 1), "bsz": ARGS.bsz}
    x = ctx = enc = y = yf = None
    try:
        x, ctx, enc, ts, T = make_inputs(L, ARGS.enc_len, gen, ARGS.bsz)
        for _ in range(ARGS.warmup):
            y = one_forward(x, ctx, enc, ts)
        torch.cuda.synchronize()

        times = []
        for _ in range(ARGS.reps):
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            y = one_forward(x, ctx, enc, ts)
            torch.cuda.synchronize()
            times.append(time.perf_counter() - t0)

        yf = y.float()
        n_nan = int(torch.isnan(yf).sum().item())
        n_inf = int(torch.isinf(yf).sum().item())
        finite = bool(torch.isfinite(yf).all().item())
        med = statistics.median(times)
        entry.update({
            "ok": True,
            "median_ms": round(med * 1e3, 2),
            "min_ms": round(min(times) * 1e3, 2),
            "max_ms": round(max(times) * 1e3, 2),
            "spread_pct": round((max(times) - min(times)) / med * 100, 1),
            "out_shape": list(y.shape),
            "finite": finite, "n_nan": n_nan, "n_inf": n_inf,
            "out_absmax": round(float(yf.abs().max().item()), 4),
            "out_std": round(float(yf.std().item()), 4),
            "peak_vram_MiB": round(torch.cuda.max_memory_allocated() / 2 ** 20, 1),
            "activations_MiB": round((torch.cuda.max_memory_allocated() - alloc) / 2 ** 20, 1),
        })
        assert list(y.shape) == [ARGS.bsz, T, AC], "shape inesperada %s" % (y.shape,)
        log("  L=%5d T=%5d (%5.0fs)  mediana %9.2f ms  [%.1f-%.1f]  pico %7.1f MiB  "
            "finito=%s |max|=%.3f std=%.3f" % (
                L, T, secs, entry["median_ms"], entry["min_ms"], entry["max_ms"],
                entry["peak_vram_MiB"], finite, entry["out_absmax"], entry["out_std"]))
        if not finite:
            RESULT["errors"].append("L=%d: salida NO finita (nan=%d inf=%d)" % (L, n_nan, n_inf))
    except RuntimeError as e:
        msg = str(e)
        is_oom = ("out of memory" in msg.lower()) or ("CUDA_ERROR_OUT_OF_MEMORY" in msg)
        post_oom = oom_at is not None
        entry.update({"ok": False, "oom": is_oom, "post_oom": post_oom,
                      "error": msg.splitlines()[0][:300]})
        if oom_at is None and is_oom:
            oom_at = L
        log("  L=%5d T=%5d (%5.0fs)  *** %s ***" % (
            L, T, secs, "OOM" if is_oom else ("ERROR (post-OOM)" if post_oom else "ERROR")))
        log("        %s" % msg.splitlines()[0][:200])
        if is_oom:
            # MEDIDO: un OOM a nivel de DRIVER ("CUDA driver error: out of memory")
            # deja el caching allocator de PyTorch en estado inconsistente; la
            # siguiente asignacion revienta con
            #   !handles_.at(i) INTERNAL ASSERT FAILED ... CUDACachingAllocator.cpp:467
            # No es recuperable en proceso: el runner debe comprobar mem_get_info
            # ANTES de asignar y, si falla igualmente, morir y reiniciar.
            RESULT["warnings"].append(
                "OOM en L=%d: a partir de aqui el CUDA caching allocator queda en "
                "estado inconsistente; las medidas posteriores del MISMO proceso no "
                "son fiables." % L)
        elif post_oom:
            RESULT["warnings"].append(
                "L=%d: fallo en cascada tras el OOM de L=%s (allocator corrupto), "
                "no es un fallo independiente: %s" % (L, oom_at, msg.splitlines()[0][:160]))
        else:
            RESULT["errors"].append("L=%d: %s" % (L, msg.splitlines()[0][:200]))
    finally:
        del x, ctx, enc, y, yf
        torch.cuda.empty_cache()
    rows.append(entry)

RESULT["forwards"] = rows
RESULT["oom_first_L"] = oom_at

# ---------------------------------------------------------------------------
# 8. Extrapolacion
# ---------------------------------------------------------------------------
hdr("7. EXTRAPOLACION  (%d pasos de difusion, sin CFG -> 1 forward/paso)" % ARGS.steps)
log("  %6s %7s %11s %9s %13s %12s %10s" % (
    "L", "audio", "ms/forward", "s/pista", "x t.real", "%d pistas" % ARGS.tracks, "pico VRAM"))
log("  " + "-" * 76)
extrap = []
for r in rows:
    if not r.get("ok"):
        log("  %6d %6.0fs   ---  %s" % (r["L_tokens"], r["audio_s"],
                                        "OOM" if r.get("oom") else "ERROR"))
        continue
    per_track = r["median_ms"] / 1e3 * ARGS.steps
    g1 = per_track * ARGS.tracks
    e = {
        "L_tokens": r["L_tokens"], "audio_s": r["audio_s"],
        "median_ms_per_forward": r["median_ms"],
        "s_per_track_diffusion": round(per_track, 2),
        "realtime_factor": round(r["audio_s"] / per_track, 2),
        "g1_tracks_s": round(g1, 1),
        "g1_tracks_min": round(g1 / 60.0, 2),
        "peak_vram_MiB": r["peak_vram_MiB"],
    }
    extrap.append(e)
    log("  %6d %6.0fs %11.2f %9.2f %12.2fx %10.2f min %9.1f" % (
        r["L_tokens"], r["audio_s"], r["median_ms"], per_track,
        e["realtime_factor"], g1 / 60.0, r["peak_vram_MiB"]))
RESULT["extrapolation"] = extrap
RESULT["diffusion_steps"] = ARGS.steps
RESULT["g1_tracks"] = ARGS.tracks

main = None
for e in extrap:
    if e["L_tokens"] == 2250:
        main = e
if main:
    log("")
    log("  OBJETIVO 180 s (L=2250): %.1f ms/forward -> %.1f s de difusion por pista "
        "-> %d pistas = %.2f min" % (
            main["median_ms_per_forward"], main["s_per_track_diffusion"],
            ARGS.tracks, main["g1_tracks_min"]))
    RESULT["headline_180s"] = main
log("")
log("  AVISO: esto es SOLO el DiT. No incluye text encoder Qwen3, condition")
log("  encoder, decode del VAE por trozos, ni la escritura de audio.")

# ---------------------------------------------------------------------------
# 7-bis. BUCLE REAL DE 8 PASOS (deja de ser extrapolacion y pasa a ser medida)
# ---------------------------------------------------------------------------
# Schedule literal de generate_audio (L1817-1821), shift=3.0, fix_nfe=8.
SHIFT3 = [1.0, 0.9545454545454546, 0.9, 0.8333333333333334,
          0.75, 0.6428571428571429, 0.5, 0.3]
from transformers.cache_utils import DynamicCache, EncoderDecoderCache   # noqa: E402

loop_rows = []
loop_lengths = [int(x) for x in ARGS.loop_check.split(",") if x.strip()]
if loop_lengths:
    hdr("7-bis. BUCLE REAL DE %d PASOS (Euler ODE, cache de cross-attn compartida)" % len(SHIFT3))
    log("  t_schedule (shift=3.0, literal upstream): %s" % [round(t, 4) for t in SHIFT3])
    for L in loop_lengths:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        try:
            x, ctx, enc, _ts, T = make_inputs(L, ARGS.enc_len, gen)
            per_step = []
            with torch.no_grad():
                pkv = EncoderDecoderCache(DynamicCache(), DynamicCache())
                xt = x
                torch.cuda.synchronize()
                t_loop0 = time.perf_counter()
                for i, tcur in enumerate(SHIFT3):
                    tt = torch.full((1,), tcur, device=dev, dtype=torch.float16)
                    t0 = time.perf_counter()
                    out = dit(hidden_states=xt, timestep=tt, timestep_r=tt,
                              attention_mask=None, encoder_hidden_states=enc,
                              encoder_attention_mask=None, context_latents=ctx,
                              use_cache=True, past_key_values=pkv)
                    vt = out[0]
                    pkv = out[1]
                    if i == len(SHIFT3) - 1:
                        xt = xt - vt * tt.unsqueeze(-1).unsqueeze(-1)   # get_x0_from_noise
                    else:
                        dt = tcur - SHIFT3[i + 1]                      # Euler ODE
                        xt = xt - vt * dt
                    torch.cuda.synchronize()
                    per_step.append(time.perf_counter() - t0)
                torch.cuda.synchronize()
                t_loop = time.perf_counter() - t_loop0
            xf = xt.float()
            r = {
                "L_tokens": L, "T_frames": T, "audio_s": round(T / FPS, 1),
                "ok": True,
                "loop_total_s": round(t_loop, 3),
                "step_ms": [round(s * 1e3, 1) for s in per_step],
                "step1_ms": round(per_step[0] * 1e3, 1),
                "steps2plus_median_ms": round(statistics.median(per_step[1:]) * 1e3, 2),
                "realtime_factor": round((T / FPS) / t_loop, 2),
                "peak_vram_MiB": round(torch.cuda.max_memory_allocated() / 2 ** 20, 1),
                "finite": bool(torch.isfinite(xf).all().item()),
                "n_nan": int(torch.isnan(xf).sum().item()),
                "n_inf": int(torch.isinf(xf).sum().item()),
                "x0_absmax": round(float(xf.abs().max().item()), 4),
                "x0_std": round(float(xf.std().item()), 4),
                "g1_tracks_min": round(t_loop * ARGS.tracks / 60.0, 2),
            }
            log("  L=%5d (%3.0fs): 8 pasos en %.2f s  (paso1 %.0f ms con K/V de cross, "
                "pasos 2-8 mediana %.0f ms)" % (
                    L, T / FPS, t_loop, r["step1_ms"], r["steps2plus_median_ms"]))
            log("           x0 finito=%s |max|=%.3f std=%.3f  pico %0.1f MiB  "
                "-> %d pistas = %.2f min" % (
                    r["finite"], r["x0_absmax"], r["x0_std"], r["peak_vram_MiB"],
                    ARGS.tracks, r["g1_tracks_min"]))
            if not r["finite"]:
                RESULT["errors"].append("bucle L=%d: x0 NO finito" % L)
            loop_rows.append(r)
            del x, ctx, enc, xt, vt, out, pkv, xf
        except RuntimeError as e:
            msg = str(e)
            is_oom = "out of memory" in msg.lower()
            log("  L=%5d: *** %s *** %s" % (L, "OOM" if is_oom else "ERROR",
                                            msg.splitlines()[0][:180]))
            loop_rows.append({"L_tokens": L, "ok": False, "oom": is_oom,
                              "error": msg.splitlines()[0][:300]})
            if not is_oom:
                RESULT["errors"].append("bucle L=%d: %s" % (L, msg.splitlines()[0][:180]))
        torch.cuda.empty_cache()
RESULT["real_8step_loop"] = loop_rows

# ---------------------------------------------------------------------------
# 9. VRAM del dit.* completo residente (bonus: el instante mas estrecho)
# ---------------------------------------------------------------------------
if not ARGS.skip_full_vram:
    hdr("8. BONUS: VRAM con TODO dit.* residente en GPU")
    try:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        # OJO: .to(dev) sobre estos submodulos FALLA con
        #   "Cannot copy out of meta tensor; no data!"
        # porque conservan buffers NO persistentes en meta (rotary_emb.inv_freq del
        # lyric_encoder, etc.) que nunca estuvieron en el state_dict. Movemos solo
        # los tensores con datos reales.
        n_meta_skipped = 0
        for sub in (model.encoder, model.tokenizer, model.detokenizer):
            for _, p in sub.named_parameters():
                if p.is_meta:
                    n_meta_skipped += 1
                else:
                    p.data = p.data.to(dev)
            for _, b in sub.named_buffers():
                if b.is_meta:
                    n_meta_skipped += 1
                else:
                    b.data = b.data.to(dev)
        model.null_condition_emb.data = model.null_condition_emb.data.to(dev)
        log("  tensores en meta omitidos (buffers no persistentes): %d" % n_meta_skipped)
        torch.cuda.synchronize()
        a2 = torch.cuda.memory_allocated()
        fr2, tt2 = torch.cuda.mem_get_info()
        b = {
            "dit_all_allocated_MiB": round(a2 / 2 ** 20, 1),
            "mem_get_info_free_MiB": round(fr2 / 2 ** 20, 1),
            "delta_vs_dit_only_MiB": round((a2 - alloc) / 2 ** 20, 1),
        }
        for k, v in b.items():
            log("  %-32s %s" % (k, v))
        RESULT["vram_all_dit_on_gpu"] = b
    except RuntimeError as e:
        log("  OOM/ERROR al residenciar todo dit.*: %s" % str(e).splitlines()[0][:200])
        RESULT["vram_all_dit_on_gpu"] = {"error": str(e).splitlines()[0][:200]}
        torch.cuda.empty_cache()

# ---------------------------------------------------------------------------
RESULT["ok"] = len(RESULT["errors"]) == 0
RESULT["total_wall_s"] = round(time.time() - t_script0, 1)
RESULT["cli"] = vars(ARGS)
hdr("FIN")
log("  wall total: %s s   errores: %s" % (RESULT["total_wall_s"], RESULT["errors"]))
print("---JSON---", flush=True)
print(json.dumps(RESULT, indent=2, ensure_ascii=False), flush=True)
