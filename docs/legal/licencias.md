---
documento: licencias
titulo: Registro de licencias de modelos y herramientas
estado: vigente
fecha: 2026-09-28
actualizado: 2026-10-09
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
| Audiobox Aesthetics | P | [CC-BY-4.0](https://github.com/facebookresearch/audiobox-aesthetics/blob/2618e9d451b456e9328b39495b5e6234678aa550/LICENSE) (respetar avisos de componentes) | CC-BY-4.0 (atribución) | — | ✅ con atribución | 2026-10-06 (código fijado) |
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
| PyTorch (`torch`, imagen PyTorch/CUDA fijada) | P (engines, solo Docker) | [BSD-3-Clause](https://github.com/pytorch/pytorch/blob/main/LICENSE); distribución incluye componentes Apache-2.0, LLVM-exception, BSD-2-Clause, BSL-1.0 y MIT con avisos propios | — | — | ✅ conservando avisos de la distribución | 2026-10-06 (fuente oficial y metadatos PyPI; versión runtime se verifica en T-08) |
| NVIDIA CUDA/cuDNN (runtime de la base Docker) | P (engines) | [NVIDIA CUDA EULA](https://docs.nvidia.com/cuda/eula/index.html) / [cuDNN Software License Agreement](https://docs.nvidia.com/deeplearning/cudnn/backend/latest/reference/eula.html); componentes del proveedor con términos propios | — | — | ⚠️ según términos del proveedor y avisos de redistribución | 2026-10-06 (fuentes oficiales; no hereda licencia BSD de PyTorch) |
| Git (build de dependencias fijadas) | Desarrollo (engines Docker) | [GPL-2.0](https://github.com/git/git/blob/master/COPYING) | — | — | ✅ conservando avisos/obligaciones de distribución | 2026-10-06 (licencia oficial) |
| libgomp (runtime OpenMP) | P (engine-analysis) | [GPLv3](https://gcc.gnu.org/onlinedocs/libgomp/Copying.html) con [GCC Runtime Library Exception 3.1](https://www.gnu.org/licenses/gcc-exception-3.1.html) | — | — | ✅ bajo la excepción y avisos correspondientes | 2026-10-06 (fuentes oficiales) |
| torchaudio | P (análisis, solo Docker) | [BSD](https://github.com/pytorch/audio/blob/main/LICENSE) | — | — | ✅ | 2026-10-06 (metadatos oficiales; compatibilidad runtime pendiente) |
| Transformers, Accelerate, safetensors, huggingface-hub | P (loaders locales, sin descarga runtime) | [Apache-2.0](https://github.com/huggingface/transformers/blob/main/LICENSE) ([Accelerate](https://github.com/huggingface/accelerate/blob/main/LICENSE), [safetensors](https://github.com/huggingface/safetensors/blob/main/LICENSE), [hub](https://github.com/huggingface/huggingface_hub/blob/main/LICENSE)) | — | — | ✅ | 2026-10-06 (metadatos oficiales; lock propio del engine) |
| PEFT 0.18.1 | L (dependencia ya instalada en ACE-Step; ruta LoRA de T-10 pendiente de habilitación segura) | [Apache-2.0](https://github.com/huggingface/peft/blob/v0.18.1/LICENSE) | La licencia de cada adaptador se comprueba aparte | — | ✅ para el código, conservando avisos; no acredita derechos de pesos/dataset | 2026-10-06 (licencia oficial de versión y fuente/metadatos de imagen fijada; [inspección](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/peft-loader-inspection-report.md)) |
| qwen-asr (paquete de ASR/alineación) | P (análisis, solo Docker) | [Apache-2.0](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/LICENSE) | Ver Qwen3-ASR/ForcedAligner | — | ✅; sus dependencias conservan licencias propias | 2026-10-06 (commit fijado) |
| qwen-omni-utils | P (dependencia de Qwen) | [Apache-2.0](https://pypi.org/project/qwen-omni-utils/) | — | — | ✅ | 2026-10-06 (metadatos PyPI) |
| einops, rotary-embedding-torch | P (arquitectura beat_this) | [MIT](https://github.com/arogozhnikov/einops/blob/main/LICENSE) ([rotary](https://pypi.org/project/rotary-embedding-torch/)) | — | — | ✅ | 2026-10-06 (metadatos PyPI) |
| tqdm | P (dependencias de análisis) | [MPL-2.0 y MIT](https://github.com/tqdm/tqdm/blob/master/LICENCE) | — | — | ✅ conservando avisos | 2026-10-06 (metadatos PyPI) |
| submitit, rich | P (dependencias de Audiobox) | [MIT](https://github.com/facebookincubator/submitit/blob/main/LICENSE) ([rich](https://github.com/Textualize/rich/blob/master/LICENSE)) | — | — | ✅ | 2026-10-06 (metadatos PyPI) |
| nagisa | P (tokenización japonesa del paquete Qwen) | [MIT](https://pypi.org/project/nagisa/0.2.11/) | — | — | ✅ | 2026-10-06 (metadatos de la versión fijada) |
| soynlp | P (tokenización coreana del paquete Qwen) | [GPLv3](https://github.com/lovit/soynlp/blob/master/LICENSE) | — | — | ✅ uso local; revisar obligaciones de distribución del conjunto | 2026-10-06 (metadatos PyPI, distinta de Apache de Qwen) |
| sox (wrapper Python pysox) | P (dependencia de Qwen) | [BSD-3-Clause](https://github.com/rabitt/pysox/blob/master/LICENSE) | — | — | ✅; no acredita instalación/licencia de un binario SoX | 2026-10-06 (metadatos PyPI) |
| Gradio | Dependencia del paquete Qwen (demos no expuestas) | [Apache-2.0](https://github.com/gradio-app/gradio/blob/main/LICENSE) | — | — | ✅ | 2026-10-06 (metadatos PyPI) |
| Flask, pytz | Dependencias del paquete Qwen | [BSD-3-Clause](https://github.com/pallets/flask/blob/main/LICENSE.txt) / [MIT](https://pypi.org/project/pytz/) | — | — | ✅ | 2026-10-06 (metadatos PyPI) |
| FFmpeg (BtbN `win64-lgpl` en el server, `linux64-lgpl-shared` en engines; con lame, opus, soxr) | P | LGPL 2.1+ | — | — | ✅ (sin `--enable-gpl` ni `--enable-nonfree`) | 2026-09-28 |
| FFmpeg Linux del server: BtbN estático `n9.0.2-17-g2a571b6068`, release `autobuild-2026-09-30-13-08` ([ADR-0054](../decisiones/ADR-0054-ffmpeg-linux-fijado-para-el-server.md)) | P | LGPLv3 según [receta fijada](https://raw.githubusercontent.com/BtbN/FFmpeg-Builds/6c9aec5fc9a72ec3abedd1fa84db141fa18cf52b/variants/defaults-lgpl.sh), con avisos de bibliotecas | — | — | Uso local autorizado; [QA Linux Bookworm/amd64](../roadmap/2026-09-28-m1-mvp-estudio/testing/t05/ffmpeg-linux-native-container-qa1-root-acceptance.json) verifica ejecución y flags version3, sin GPL/nonfree; autodeclaración LGPLv3+. Completitud de avisos de dependencias y redistribución sin certificar. SHA oficial fijado | 2026-10-08 |
| Python 3.12.14 / imagen oficial `python:3.12.14-slim-bookworm` | P (server, mock CPU y helper storage de ADR-0071, base por digest) | [PSF y avisos de Python](https://docs.python.org/3/license.html); componentes Debian con licencias propias en `/usr/share/doc/*/copyright` | — | — | ✅ conservando avisos de la distribución | 2026-10-07 (imagen oficial, revisión `688a0b86bb44289df16a363e9f41d90514c1a5f9`); rol helper ampliado2026-10-09 sin nuevas dependencias |
| QEMU `qemu-utils` Debian `1:7.2+dfsg-7+deb12u18+b3`, sólo `qemu-img` | P (provisión offline de ADR-0069, proceso CPU separado) | GPL-2.0 y licencias compatibles por componente; [aviso upstream 7.2](https://github.com/qemu/qemu/blob/v7.2.0/LICENSE), [copyright Debian exacto](https://metadata.ftp-master.debian.org/changelogs/main/q/qemu/qemu_7.2+dfsg-7+deb12u18_copyright) | — | — | Uso local; conservar avisos. Redistribución del conjunto sin certificar | 2026-10-09 (metadatos firmados y DEB verificado; diagnóstico de versión7.2.22 y formatos raw/VHDX pasa, conversión por FD pendiente) |
| e2fsprogs Debian `1.47.0-2+b2`: mke2fs, e2fsck, debugfs y dumpe2fs | P (provisión y verificación offline, procesos CPU separados) | GPL-2.0 para utilidades; bibliotecas con licencias propias, incluido LGPL-2.0; [copyright Debian exacto](https://metadata.ftp-master.debian.org/changelogs/main/e/e2fsprogs/e2fsprogs_1.47.0-2_copyright) | — | — | Uso local; conservar avisos. Redistribución del conjunto sin certificar | 2026-10-09 (DEBs y avisos verificados; versiones1.47.0 pasan, primer mke2fs por FD falla al leer tamaño; debug pendiente) |
| Bundle transitivo Debian de QEMU/e2fsprogs, 30 paquetes fijados en `tools/storage-linux.lock.json` | P (sysroot privado de provisión, sin instalación global) | Licencias por paquete: GPL/LGPL con sus versiones/excepciones y avisos permisivos; conservar `/usr/share/doc/*/copyright` y textos referidos del bundle real | — | — | Uso local. No atribuir una licencia única ni certificar distribución del bundle | 2026-10-09: Root verificó los30DEBs y30copyrights del sysroot físico. PCRE2 `10.42-1+deb12u2` tiene aviso extraído del DEB exacto, SHA030511be…; cierre declarativo ELF verificado por actor, mapas efectivos y redistribución sin certificar. [Evidencia y límites](../roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-tool-metadata.md) |
| pydantic-settings 2.11.0 / python-dotenv 1.1.1 | P (configuración del server y lectura de `.env`) | [MIT](https://pypi.org/project/pydantic-settings/2.11.0/) / [BSD-3-Clause](https://pypi.org/project/python-dotenv/1.1.1/) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales de las versiones fijadas) |
| SQLAlchemy 2.0.54 / Alembic 1.20.0 | P (esquema y migraciones del server, T-02) | [MIT SQLAlchemy](https://pypi.org/project/SQLAlchemy/2.0.54/) / [MIT Alembic](https://pypi.org/project/alembic/1.20.0/) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales; instalación e integración pendientes) |
| Mako / greenlet | P (dependencias de Alembic/SQLAlchemy, T-02) | [MIT Mako](https://pypi.org/project/Mako/) / [MIT AND PSF-2.0 greenlet](https://pypi.org/project/greenlet/) | — | — | ✅ conservando avisos propios | 2026-10-07 (metadatos oficiales; versiones resueltas se registran en el lock) |
| MarkupSafe 3.0.4 | P (dependencia transitiva de Mako, T-02) | [BSD-3-Clause](https://pypi.org/project/MarkupSafe/3.0.4/) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales de la versión resuelta) |
| FastAPI / Pydantic / JSON Schema (`jsonschema`) | P (contrato y validación) | MIT | — | — | ✅ | 2026-10-05 (metadatos de las distribuciones fijadas en `uv.lock`) |
| Starlette / Uvicorn | P (servidor del engine) | BSD-3-Clause | — | — | ✅ | 2026-10-05 (metadatos locales) |
| nvidia-ml-py (NVML) | P (VRAM sin contexto CUDA) | BSD | — | — | ✅ | 2026-10-05 (licencia de la distribución local) |
| NumPy | P (audio y pesos) | BSD-3-Clause; el wheel incluye 0BSD, MIT, Zlib y CC0-1.0 | — | — | ✅ | 2026-10-05 (metadatos del wheel local) |
| SciPy | P (dependencia de pyloudnorm) | BSD-3-Clause; bibliotecas incluidas con sus avisos y excepción GCC | — | — | ✅ | 2026-10-05 (licencia del wheel local) |
| HTTPX / pytest-cov | Desarrollo (pruebas y cobertura) | BSD-3-Clause / MIT | — | — | ✅ | 2026-10-05 (metadatos locales) |
| PyYAML (catálogo de briefs del CLI) | Desarrollo (M0 CLI) | [MIT](https://github.com/yaml/pyyaml/blob/main/LICENSE) | — | — | ✅ | 2026-10-05 (licencia upstream; parser safe_load) |
| torchao 0.16.0 | P (cuantización DiT explícita del benchmark T-09, implementación pendiente) | [BSD-3-Clause](https://github.com/pytorch/ao/blob/v0.16.0/LICENSE) | — | — | ✅ conservando avisos; compatibilidad CUDA pendiente de prueba | 2026-10-06 (licencia oficial de versión y lock ACE-Step fijado) |
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

| TypeScript 5.9.3 | Desarrollo T03 (compilador y comprobación de parsers) | [Apache-2.0](https://www.npmjs.com/package/typescript/v/5.9.3) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales npm; pin estable verificado) |
| Vitest 5.0.3 / @vitest/coverage-v8 5.0.3 | Desarrollo T03 (pruebas y cobertura web) | [MIT](https://www.npmjs.com/package/vitest/v/5.0.3) / [MIT](https://www.npmjs.com/package/@vitest/coverage-v8/v/5.0.3) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales npm; Node22.23.2 satisface requisito22.12) |
| @types/node 22.19.15 / openapi-typescript 7.13.0 | Desarrollo T03 (tipos y generación de contrato) | [MIT](https://www.npmjs.com/package/@types/node/v/22.19.15) / [MIT](https://www.npmjs.com/package/openapi-typescript/v/7.13.0) | — | — | ✅ conservando avisos | 2026-10-07 (metadatos oficiales npm; generación se implementa después de liberar main) |

## T03-transitive

| Componente | Rol | Código | Pesos | Datos de entrenamiento | Uso comercial | Verificado |
|---|---|---|---|---|---|---|
| Bundle transitivo fijado de TypeScript/Vitest/coverage-v8/@types/node (T03) | Desarrollo, parsers CPU | MIT, Apache-2.0, BSD-3-Clause, ISC y MPL-2.0; conservar avisos propios | — | — | ✅ bajo sus respectivas licencias | 2026-10-07, metadatos oficiales npm por versión; inventario privado T03 y pnpm-lock.yaml |

## Pendientes antes de comercializar

1. Pedir por escrito la licencia de los pesos de SilentCipher, SongEval y los RoFormer de la comunidad (o reentrenar un separador sobre stems con licencia o generados con ACE-Step).
2. No distribuir pesos de Demucs.
3. Confirmar si HeartTranscriptor admite castellano (hoy no se usa).
4. Revisar las dependencias de RVC (ContentVec, RMVPE) si se usa.


## T03 — Dependencias del generador OpenAPI

Las 30 entradas añadidas al lock por openapi-typescript7.13.0 se contrastaron con los metadatos oficiales npm de cada versión y con sus package.json/avisos instalados el2026-10-07. Ningún paquete o snapshot anterior cambia. El inventario exacto permanece en pnpm-lock.yaml; los recibos privados conservan los metadatos y SHA-256. Esta fila complementa el bundle anterior de parsers, no reinterpreta sus licencias.

| Componente | Uso | Licencia | Condición | Fuente |
|---|---|---|---|---|
| @babel/code-frame@7.29.7 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/@babel/code-frame/v/7.29.7) |
| @redocly/ajv@8.11.2 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/@redocly/ajv/v/8.11.2) |
| @redocly/config@0.22.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/@redocly/config/v/0.22.0) |
| @redocly/openapi-core@1.34.20 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/@redocly/openapi-core/v/1.34.20) |
| agent-base@7.1.4 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/agent-base/v/7.1.4) |
| ansi-colors@4.1.3 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/ansi-colors/v/4.1.3) |
| argparse@2.0.1 | Generación de tipos T03, desarrollo | Python-2.0 | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/argparse/v/2.0.1) |
| balanced-match@1.0.2 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/balanced-match/v/1.0.2) |
| brace-expansion@2.1.7 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/brace-expansion/v/2.1.7) |
| change-case@5.4.4 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/change-case/v/5.4.4) |
| colorette@1.4.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/colorette/v/1.4.0) |
| debug@4.4.3 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/debug/v/4.4.3) |
| fast-deep-equal@3.1.3 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/fast-deep-equal/v/3.1.3) |
| https-proxy-agent@7.0.6 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/https-proxy-agent/v/7.0.6) |
| index-to-position@1.2.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/index-to-position/v/1.2.0) |
| js-levenshtein@1.1.6 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/js-levenshtein/v/1.1.6) |
| js-tokens@4.0.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/js-tokens/v/4.0.0) |
| js-yaml@4.3.2 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/js-yaml/v/4.3.2) |
| json-schema-traverse@1.0.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/json-schema-traverse/v/1.0.0) |
| minimatch@5.1.9 | Generación de tipos T03, desarrollo | ISC | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/minimatch/v/5.1.9) |
| ms@2.1.3 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/ms/v/2.1.3) |
| openapi-typescript@7.13.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/openapi-typescript/v/7.13.0) |
| parse-json@8.3.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/parse-json/v/8.3.0) |
| pluralize@8.0.0 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/pluralize/v/8.0.0) |
| require-from-string@2.0.2 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/require-from-string/v/2.0.2) |
| supports-color@10.2.2 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/supports-color/v/10.2.2) |
| type-fest@4.41.0 | Generación de tipos T03, desarrollo | (MIT OR CC0-1.0) | Conservar licencia y avisos propios; para type-fest se elige MIT. | [Metadatos oficiales](https://www.npmjs.com/package/type-fest/v/4.41.0) |
| uri-js-replace@1.0.1 | Generación de tipos T03, desarrollo | MIT | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/uri-js-replace/v/1.0.1) |
| yaml-ast-parser@0.0.43 | Generación de tipos T03, desarrollo | Apache-2.0 | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/yaml-ast-parser/v/0.0.43) |
| yargs-parser@21.1.1 | Generación de tipos T03, desarrollo | ISC | Conservar licencia y avisos propios. | [Metadatos oficiales](https://www.npmjs.com/package/yargs-parser/v/21.1.1) |


## T04 — Herramientas privadas de construcción para QA

Verificación por versión el 2026-10-07: metadatos y licencias de ruedas oficiales PyPI. Alcance exclusivo del prerrequisito de QA; no certifica builds anteriores ni la comercialización del producto. Tomlkit es una rueda candidata privada, sin instalación ni ejecución; su adopción y la reanudación de QA quedan a revisión de raíz.

| Componente | Uso | Licencia | Condición | Fuente y fecha |
|---|---|---|---|---|
| hatchling 1.32.4 | Construcción privada QA T04 | MIT | Conservar licencia y avisos propios. | [PyPI oficial exacto](https://pypi.org/pypi/hatchling/1.32.4/json); 2026-10-07 |
| pathspec 1.1.1 | Construcción privada QA T04 | MPL-2.0 | Componente externo sin modificar; conservar avisos y cumplir las obligaciones MPL-2.0 sobre archivos cubiertos si se modifican y distribuyen. | [PyPI oficial exacto](https://pypi.org/pypi/pathspec/1.1.1/json); 2026-10-07 |
| trove-classifiers 2026.9.21.13 | Construcción privada QA T04 | Apache-2.0 | Conservar licencia Apache-2.0 y avisos aplicables; señalar cambios si se modifica. | [PyPI oficial exacto](https://pypi.org/pypi/trove-classifiers/2026.9.21.13/json); 2026-10-07 |
| packaging 26.3 | Construcción privada QA T04 | Apache-2.0 OR BSD-2-Clause | Licencia dual; para este uso se elige BSD-2-Clause y se conservan sus avisos. | [PyPI oficial exacto](https://pypi.org/pypi/packaging/26.3/json); 2026-10-07 |
| pluggy 1.6.0 | Construcción privada QA T04 | MIT | Conservar licencia y avisos propios. | [PyPI oficial exacto](https://pypi.org/pypi/pluggy/1.6.0/json); 2026-10-07 |
| tomlkit 0.13.3 | Construcción privada QA T04 | MIT | Conservar licencia y avisos propios. | [PyPI oficial exacto](https://pypi.org/pypi/tomlkit/0.13.3/json); 2026-10-07 |


## T08 — Candidatos exactos de primer nivel para la web

Revisión registral de evidencia oficial sellada del 2026-10-07, recontrastada el 2026-10-07 UTC. Alcance: un runtime separado y 24 paquetes candidatos de primer nivel, incluido pnpm 9.12.0, que conserva el packageManager raíz. Las filas históricas T03 y T04 permanecen intactas; las coincidencias se repiten para distinguir esta procedencia candidata.

Este registro no adopta dependencias de producto ni autoriza instalar o ejecutar herramientas. No acredita cierre transitivo, lock pnpm completo, compatibilidad probada ni autorización comercial del conjunto. La licencia del paquete principal no se hereda por sus dependencias ni por componentes compilados o incluidos. La ausencia de LICENSE de eslint-config-next se mantiene explícita: raíz admite la prueba upstream cualificada solo para este candidato, sin equiparar los bytes de fuente y tarball.

Los tarballs oficiales de estas versiones se verificaron por SHA1/SRI/SHA-256 y miembros seguros en el inventario previo, sin ejecución. Las licencias y avisos íntegros se conservan en la evidencia privada. Node conserva íntegro su LICENSE distribuido. Las fuentes candidatas se alojarían localmente; esta revisión no ejecuta Google Fonts remoto. Bootstrap confinado y resolución transitiva completa requieren una unidad posterior independiente; UI y E2E siguen pendientes.

| Componente candidato | Versión exacta | Licencia y alcance | Obligaciones / límite de la evidencia | Fuente oficial de versión y fecha de recontraste |
|---|---|---|---|---|
| Node.js | 22.23.2 | MIT + licencias de terceros distribuidos | Conservar íntegro el LICENSE incluido, con todos sus avisos; SHA-256 del ZIP contrastado, firma PGP sin verificar. | [Distribución oficial exacta](https://nodejs.org/dist/v22.23.2/) · [LICENSE de versión](https://github.com/nodejs/node/blob/v22.23.2/LICENSE); 2026-10-07 UTC |
| pnpm | 9.12.0 | MIT + licencias de componentes incluidos | Conservar los 96 archivos de licencia/avisos incluidos; cada componente conserva su licencia. | [Metadatos oficiales exactos](https://registry.npmjs.org/pnpm/9.12.0) · [Tarball exacto](https://registry.npmjs.org/pnpm/-/pnpm-9.12.0.tgz); 2026-10-07 UTC |
| next | 16.4.0 | MIT + licencias de componentes incluidos | Conservar los 132 archivos de licencia/avisos; componentes compilados o incluidos con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/next/16.4.0) · [Tarball exacto](https://registry.npmjs.org/next/-/next-16.4.0.tgz); 2026-10-07 UTC |
| react | 19.3.0 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/react/19.3.0) · [Tarball exacto](https://registry.npmjs.org/react/-/react-19.3.0.tgz); 2026-10-07 UTC |
| react-dom | 19.3.0 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/react-dom/19.3.0) · [Tarball exacto](https://registry.npmjs.org/react-dom/-/react-dom-19.3.0.tgz); 2026-10-07 UTC |
| next-intl | 4.14.9 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/next-intl/4.14.9) · [Tarball exacto](https://registry.npmjs.org/next-intl/-/next-intl-4.14.9.tgz); 2026-10-07 UTC |
| tailwindcss | 4.3.3 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/tailwindcss/4.3.3) · [Tarball exacto](https://registry.npmjs.org/tailwindcss/-/tailwindcss-4.3.3.tgz); 2026-10-07 UTC |
| @tailwindcss/postcss | 4.3.3 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40tailwindcss%2Fpostcss/4.3.3) · [Tarball exacto](https://registry.npmjs.org/@tailwindcss/postcss/-/postcss-4.3.3.tgz); 2026-10-07 UTC |
| postcss | 8.5.29 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/postcss/8.5.29) · [Tarball exacto](https://registry.npmjs.org/postcss/-/postcss-8.5.29.tgz); 2026-10-07 UTC |
| eslint-config-next | 16.4.0 | MIT declarada; prueba upstream cualificada | Tarball sin LICENSE. Fuente v16.4.0 fijada a e273d5b2e869d0be06c0e86f788e1594f9dd40cf, versión/licencia comprobadas; no prueba identidad de bytes fuente–tarball. Conservar licencia upstream y avisos. | [Metadatos oficiales exactos](https://registry.npmjs.org/eslint-config-next/16.4.0) · [Tarball exacto](https://registry.npmjs.org/eslint-config-next/-/eslint-config-next-16.4.0.tgz) · [Licencia upstream fijada](https://raw.githubusercontent.com/vercel/next.js/e273d5b2e869d0be06c0e86f788e1594f9dd40cf/license.md) · [Fuente de versión](https://github.com/vercel/next.js/blob/e273d5b2e869d0be06c0e86f788e1594f9dd40cf/packages/eslint-config-next/package.json); 2026-10-07 UTC |
| @types/react | 19.3.0 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40types%2Freact/19.3.0) · [Tarball exacto](https://registry.npmjs.org/@types/react/-/react-19.3.0.tgz); 2026-10-07 UTC |
| @types/react-dom | 19.3.0 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40types%2Freact-dom/19.3.0) · [Tarball exacto](https://registry.npmjs.org/@types/react-dom/-/react-dom-19.3.0.tgz); 2026-10-07 UTC |
| @playwright/test | 1.64.0 | Apache-2.0 | Conservar LICENSE Apache-2.0 y NOTICE; navegadores y dependencias se revisan por separado. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40playwright%2Ftest/1.64.0) · [Tarball exacto](https://registry.npmjs.org/@playwright/test/-/test-1.64.0.tgz); 2026-10-07 UTC |
| @fontsource/inter | 5.3.0 | OFL-1.1 | Conservar OFL y atribución; respetar nombres reservados declarados al modificar, redistribuir fuentes modificadas bajo OFL y no vender la fuente por sí sola. Uso local candidato. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40fontsource%2Finter/5.3.0) · [Tarball exacto](https://registry.npmjs.org/@fontsource/inter/-/inter-5.3.0.tgz); 2026-10-07 UTC |
| @fontsource/bricolage-grotesque | 5.3.0 | OFL-1.1 | Conservar OFL y atribución; respetar nombres reservados declarados al modificar, redistribuir fuentes modificadas bajo OFL y no vender la fuente por sí sola. Uso local candidato. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40fontsource%2Fbricolage-grotesque/5.3.0) · [Tarball exacto](https://registry.npmjs.org/@fontsource/bricolage-grotesque/-/bricolage-grotesque-5.3.0.tgz); 2026-10-07 UTC |
| @fontsource/jetbrains-mono | 5.3.0 | OFL-1.1 | Conservar OFL y atribución; respetar nombres reservados declarados al modificar, redistribuir fuentes modificadas bajo OFL y no vender la fuente por sí sola. Uso local candidato. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40fontsource%2Fjetbrains-mono/5.3.0) · [Tarball exacto](https://registry.npmjs.org/@fontsource/jetbrains-mono/-/jetbrains-mono-5.3.0.tgz); 2026-10-07 UTC |
| @testing-library/react | 16.3.3 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40testing-library%2Freact/16.3.3) · [Tarball exacto](https://registry.npmjs.org/@testing-library/react/-/react-16.3.3.tgz); 2026-10-07 UTC |
| jsdom | 30.1.2 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/jsdom/30.1.2) · [Tarball exacto](https://registry.npmjs.org/jsdom/-/jsdom-30.1.2.tgz); 2026-10-07 UTC |
| @testing-library/dom | 10.4.2 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40testing-library%2Fdom/10.4.2) · [Tarball exacto](https://registry.npmjs.org/@testing-library/dom/-/dom-10.4.2.tgz); 2026-10-07 UTC |
| typescript | 5.9.3 | Apache-2.0 | Conservar Apache-2.0 y avisos aplicables; señalar cambios al modificar y distribuir. | [Metadatos oficiales exactos](https://registry.npmjs.org/typescript/5.9.3) · [Tarball exacto](https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz); 2026-10-07 UTC |
| vitest | 5.0.3 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/vitest/5.0.3) · [Tarball exacto](https://registry.npmjs.org/vitest/-/vitest-5.0.3.tgz); 2026-10-07 UTC |
| @vitest/coverage-v8 | 5.0.3 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40vitest%2Fcoverage-v8/5.0.3) · [Tarball exacto](https://registry.npmjs.org/@vitest/coverage-v8/-/coverage-v8-5.0.3.tgz); 2026-10-07 UTC |
| @types/node | 22.19.15 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/%40types%2Fnode/22.19.15) · [Tarball exacto](https://registry.npmjs.org/@types/node/-/node-22.19.15.tgz); 2026-10-07 UTC |
| openapi-typescript | 7.13.0 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/openapi-typescript/7.13.0) · [Tarball exacto](https://registry.npmjs.org/openapi-typescript/-/openapi-typescript-7.13.0.tgz); 2026-10-07 UTC |
| eslint | 9.39.5 | MIT | Conservar licencia y avisos propios; dependencias con licencias independientes. | [Metadatos oficiales exactos](https://registry.npmjs.org/eslint/9.39.5) · [Tarball exacto](https://registry.npmjs.org/eslint/-/eslint-9.39.5.tgz); 2026-10-07 UTC |


## Transitivas web M1 fijadas — uso local autorizado

2026-10-08: [registro de609 versiones](dependencias-web-m1.md) y [SHA/integridades/condiciones](dependencias-web-m1.json), revisados A+B intento2 sin hallazgos. Las23 dependencias de primer nivel mantienen sus pins. Se acepta la declaración nativa cualificada para uso local; licencia completa ausente se conserva como tal. LGPL/MPL/OFL/CC-BY y avisos compilados mantienen condiciones propias; la redistribución de binarios/fuentes/avisos no queda certificada. [ADR0051](../decisiones/ADR-0051-dependencias-web-fijadas-y-uso-local.md) autoriza instalación congelada sin scripts y decide sólo losdos alias byteidénticos fijados porSHA. No adopción de modelos, browsers, bibliotecas deSO/baseLinux ni compatibilidad probada.

## Base web Linux — prueba de ADR-0052

| Componente | Versión fijada candidata | Licencias observadas | Obligaciones y límites de comprobación |
|---|---|---|---|
| Node.js en la imagen Docker de web | 22.23.3, imagen local `sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402` | MIT y licencias de terceros incluidas en el LICENSE completo de la distribución; Dockerfile oficial MIT | Conservar LICENSE y avisos. Sonda CPU comprobó los bytes distribuidos; firma y procedencia remota no verificadas. El [repositorio oficial Docker](https://github.com/nodejs/docker-node/blob/main/LICENSE) confirma la licencia de sus archivos, sin sustituir las licencias de componentes de la imagen. |
| Alpine y bibliotecas de esa base | Alpine 3.24.2, 18 paquetes instalados registrados | Metadatos APK: Apache-2.0; GPL-2.0-only; GPL-2.0-or-later AND LGPL-2.1-or-later; MIT; MIT AND BSD-2-Clause AND GPL-2.0-or-later; MPL-2.0 AND MIT; Zlib | Son expresiones declaradas por paquete; no una licencia única ni una auditoría completa de textos/fuentes de terceros. Mantener avisos y atender las obligaciones aplicables si se redistribuye la imagen. |

La sonda propia fue de sólo lectura, sin red/GPU/puertos/mounts, y terminó con eliminación confirmada del contenedor. El [inventario de metadatos de la base](../roadmap/2026-09-28-m1-mvp-estudio/testing/t08/docker-base-license-metadata.json) conserva paquetes, versiones y expresiones observadas; los originales completos y comandos están en evidencia privada. Esto no acredita build, compatibilidad de bindings ni redistribución aprobada. La instalación web conserva las condiciones de los 609 archivos ya registrados. Véase [ADR-0052](../decisiones/ADR-0052-compilacion-web-linux-fijada.md).
