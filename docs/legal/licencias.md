---
documento: licencias
titulo: Registro de licencias de modelos y herramientas
estado: vigente
fecha: 2026-09-28
actualizado: 2026-10-05
---

# Registro de licencias

**Regla:** ningún modelo, peso ni herramienta entra en el código sin una fila aquí. Se distinguen la licencia del **código**, la de los **pesos** y la de los **datos de entrenamiento**, porque no suelen coincidir. Este registro no es asesoramiento legal.

**Uso comercial:** ✅ permitido · ⚠️ ambiguo o con condiciones · ❌ no permitido. **Rol:** P = pipeline por defecto · L = laboratorio (solo evaluación) · F = futuro.

| Componente | Rol | Código | Pesos | Datos de entrenamiento | Uso comercial | Verificado |
|---|---|---|---|---|---|---|
| ACE-Step 1.5 (2B turbo/sft/base, LM 0.6B/1.7B, XL) | P | MIT | **MIT** (todos los repos HF; `silence_latent.pt` pickle → convertir; `.py` remotos fijados) | Declarados «licensed, royalty-free/PD, synthetic» ([model card fijada](https://huggingface.co/ACE-Step/Ace-Step1.5/blob/19671f406d603126926c1b7e2adc169acbcade22/README.md), sin auditoría) | ✅ pesos · ⚠️ datos | 2026-10-05 (declaración del proveedor contrastada) |
| Qwen3-Embedding-0.6B (codificador de texto de ACE-Step) | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09 |
| HeartMuLa-oss-3B + HeartCodec | L→F | Apache 2.0 | Apache 2.0 | No declarados | ✅ pesos · ⚠️ datos | 2026-09-28 |
| MiniMax-Music3 | L | — | Community License (marca en la UI, umbral de 20 M$, AUP) | No declarados | ⚠️ | 2026-09-28 |
| YuE2-3B | L | — | CC-BY-NC 4.0 | — | ❌ | 2026-09-28 |
| LeVo 2 / SongGeneration | — | — | Solo uso académico | — | ❌ | 2026-09-28 |
| Qwen3-ASR-1.7B | P | Apache 2.0 | Apache 2.0 (safetensors) | — | ✅ | 2026-09-28 |
| Qwen3-ForcedAligner-0.6B | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09-28 |
| Whisper large-v3-turbo | P | MIT | MIT | — | ✅ | 2026-09-28 |
| LAION larger_clap_music | P | CC0/Apache | Apache 2.0 (solo `pytorch_model.bin` → convertir) | Con restricciones de copyright (no redistribuibles) | ✅ pesos | 2026-09-28 |
| Audiobox Aesthetics | P | — | CC-BY-4.0 (atribución) | — | ✅ | 2026-09-28 |
| SongEval | L | Ambigua (LICENSE Apache, README CC BY-NC-SA) | — | CC-BY-NC-SA | ⚠️ | 2026-09-28 |
| MuQ-MuLan | L | — | CC-BY-NC 4.0 | — | ❌ | 2026-09-28 |
| Mel-Band RoFormer (Kimberley) / BS-RoFormer / SCNet vía MSST | P (personal) | MIT | «mit» sin tarjeta / sin declarar | MUSDB18 u otros no comerciales | ⚠️ | 2026-09-28 |
| Demucs htdemucs | — | MIT | Solo investigación | MUSDB + internas | ❌ | 2026-09-28 [NV] |
| RVC v2 | F | MIT | MIT | VCTK (CC BY 4.0) | ✅ (revisar ContentVec y RMVPE) | 2026-09-28 |
| audiowmark | F | GPLv3+ | — | — | ✅ como proceso aparte, sin distribuirlo | 2026-09-28 |
| AudioSeal | F | MIT | MIT | — | ✅ (poco robusto en música) | 2026-09-28 |
| Gemma 4 12B-it (`gemma-4-12B-it-qat-q4_0-gguf`) | P (letras, por defecto) | — | Apache 2.0 (GGUF, sin gate) | — | ✅ | 2026-09-28 |
| Qwen3.5-9B | Alternativa (letras) | — | Apache 2.0 | — | ✅ | 2026-09-28 |
| llama.cpp | P (engine-llm) | MIT | — | — | ✅ | 2026-09-28 |
| Claude API | Opcional (letras) | — | Servicio de pago | — | ✅ según los términos comerciales de Anthropic | 2026-09-28 |
| **Vídeo e imagen** | | | | | | |
| Wan 2.2 TI2V-5B / A14B, Wan 2.1 FLF2V/VACE | P | Apache 2.0 | Apache 2.0 | No declarados | ✅ pesos · ⚠️ datos | 2026-09-28 |
| InfiniteTalk / MultiTalk | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09-28 |
| LatentSync 1.6 | P | — | OpenRAIL++ (restricciones de uso) | — | ⚠️ | 2026-09-28 |
| Z-Image / Z-Image-Turbo | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09-28 |
| Qwen-Image-2512 / Qwen-Image-Edit-2509/2511 | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09-28 |
| FLUX.2 [klein] 4B | P | Apache 2.0 | Apache 2.0 | — | ✅ | 2026-09-28 |
| FLUX.1/2-dev, Kontext-dev, klein 9B | — | — | No comercial (pesos) | — | ❌ | 2026-09-28 |
| Qwen-Image-2.1 | — | — | Qwen Research License | — | ❌ | 2026-09-28 |
| Depth Anything V2 Small | P | Apache 2.0 | Apache 2.0 (Base/Large: CC-BY-NC ❌) | — | ✅ | 2026-09-28 |
| LTX-2.5 | L | — | LTX-2.x Community (<10 M$; cláusula de no competencia con Lightricks; etiquetado obligatorio) | — | ⚠️ | 2026-09-28 |
| SkyReels V3 | L | — | Skywork Community (registro para servicios online) | — | ⚠️ | 2026-09-28 |
| Kandinsky 5 Video Lite | L | — | MIT | — | ✅ | 2026-09-28 |
| HunyuanVideo 1.5 / Avatar / HunyuanImage 3 | — | — | Tencent Community — **excluye la UE** | — | ❌ | 2026-09-28 |
| Sonic | — | — | CC BY-NC-SA | — | ❌ | 2026-09-28 |
| beat_this | P | MIT | MIT (`.ckpt` Lightning → convertir) | ⚠️ README avisa de datos con copyright | ✅ pesos · ⚠️ datos | 2026-09-28 |
| allin1 | L | MIT | MIT (`.pth`) | — | ⚠️ depende de Demucs (pesos solo investigación) y madmom | 2026-09-28 |
| madmom (modelos) | — | BSD | CC BY-NC-SA | — | ❌ | 2026-09-28 |
| ComfyUI | P (motor) | **GPL-3.0** | — | — | ✅ uso personal como proceso aparte · ⚠️ revisar antes de comercializar | 2026-09-28 |
| Pydantic, FastAPI, jsonschema | P (contrato y servidor engine) | MIT | — | — | ✅ | 2026-10-05 (metadatos instalados) |
| Uvicorn, HTTPX | P (servidor y pruebas engine) | BSD-3-Clause | — | — | ✅ | 2026-10-05 (metadatos instalados) |
| nvidia-ml-py | P (lectura NVML sin CUDA) | BSD | — | — | ✅ | 2026-10-05 (metadatos instalados) |
| pytest-cov | P (verificación de cobertura) | MIT | — | — | ✅ | 2026-10-05 (metadatos instalados) |
| **Audio y utilidades** | | | | | | |
| FFmpeg (BtbN `win64-lgpl` en el server, `linux64-lgpl-shared` en engines; con lame, opus, soxr) | P | LGPL 2.1+ | — | — | ✅ (sin `--enable-gpl` ni `--enable-nonfree`) | 2026-09-28 |
| FastAPI / Pydantic / JSON Schema (`jsonschema`) | P (contrato y validación) | MIT | — | — | ✅ | 2026-10-05 (metadatos de las distribuciones fijadas en `uv.lock`) |
| Starlette / Uvicorn | P (servidor del engine) | BSD-3-Clause | — | — | ✅ | 2026-10-05 (metadatos locales) |
| nvidia-ml-py (NVML) | P (VRAM sin contexto CUDA) | BSD | — | — | ✅ | 2026-10-05 (licencia de la distribución local) |
| NumPy | P (audio y pesos) | BSD-3-Clause; el wheel incluye 0BSD, MIT, Zlib y CC0-1.0 | — | — | ✅ | 2026-10-05 (metadatos del wheel local) |
| SciPy | P (dependencia de pyloudnorm) | BSD-3-Clause; bibliotecas incluidas con sus avisos y excepción GCC | — | — | ✅ | 2026-10-05 (licencia del wheel local) |
| HTTPX / pytest-cov | Desarrollo (pruebas y cobertura) | BSD-3-Clause / MIT | — | — | ✅ | 2026-10-05 (metadatos locales) |
| pyloudnorm | P | MIT | — | — | ✅ | 2026-09-28 |
| soxr / python-soxr | P | LGPL 2.1+ | — | — | ✅ | 2026-09-28 |
| librosa | P | ISC | — | — | ✅ | — |
| soundfile / libsndfile | P | BSD-3 / LGPL-2.1 | — | — | ✅ | — |
| NATTEN | L (allin1) | MIT | — | — | ✅ | — |
| next-intl | P | MIT | — | — | ✅ | — |
| simplex-noise | P | MIT | — | — | ✅ | — |
| Inter, Bricolage Grotesque, JetBrains Mono | P | SIL OFL 1.1 | — | — | ✅ | — |
| wavesurfer.js | P | BSD-3 | — | — | ✅ | — |
| shadcn/ui, Radix | P | MIT | — | — | ✅ | — |

## Pendientes antes de comercializar

1. Pedir por escrito la licencia de los pesos de SilentCipher, SongEval y los RoFormer de la comunidad (o reentrenar un separador sobre stems con licencia o generados con ACE-Step).
2. No distribuir pesos de Demucs.
3. Confirmar si HeartTranscriptor admite castellano (hoy no se usa).
4. Revisar las dependencias de RVC (ContentVec, RMVPE) si se usa.
