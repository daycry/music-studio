---
documento: modelos
titulo: Selección de modelos (septiembre 2026)
estado: vigente — pendiente de confirmar con la medición y la escucha de M0
fecha: 2026-09-28
actualizado: 2026-10-05
fuentes-consultadas: 2026-09-28
---

# Selección de modelos

Revisión del catálogo abierto a **2026-09-28** para una **RTX 5070 de 12 GB**. Marcas: **[V]** verificado en fuente primaria (URL en §7) · **[P]** fuente secundaria · **[NV]** sin verificar · **[M0]** se mide en el hito M0. Nada de esta tabla está medido todavía en la 5070.

**Política de licencias** ([ADR-0011](../decisiones/ADR-0011-seleccion-de-modelos.md)): el pipeline por defecto solo usa modelos cuyos **pesos** permiten uso comercial. Los modelos no comerciales pueden entrar como **laboratorio** (comparar y evaluar), nunca como motor por defecto, y sus pistas llevan `commercial_use: false` en el manifiesto.

## 1. Generador de canciones

### 1.1 Candidatos que se evalúan en M0

| | **A · ACE-Step 1.5** (principal) | **B · HeartMuLa-oss-3B** (alternativa) | **C · MiniMax-Music3** (laboratorio) |
|---|---|---|---|
| Versión | 2B turbo/sft/base (ene-2026); **XL** DiT 4B (abr-2026); última release v0.1.8 (may-2026) [V:S1,S2] | oss-3B «happy-new-year» (feb-2026) + codec 20260123 [V:S4] | ago-2026: LLM 8B + 0,6B + flow matching 2,4B [V:S10] |
| Licencia de los pesos | **MIT** [V:S3] | **Apache 2.0** [V:S4] | **Community License propia**: uso comercial permitido, pero exige mostrar «MiniMax-Music3» en la UI, pedir permiso por encima de 20 M$/año y salvaguardas si se sirve a terceros [V:S11] |
| Datos de entrenamiento (declarados) | «licensed, royalty-free/PD, synthetic» [V:S3] | 100k h «internas», origen no declarado [V:S5] | No declarados [V:S10] |
| Idiomas | 50+ declarados, español incluido; sin evaluación seria del español [V:S1][NV] | Evaluado en EN/ZH/JA/KO/**ES**: en español PER 0,13 y SongEval 4,34, frente a 0,15 y 4,46 de Suno v5, según su propio paper [V:S5] | EN/ZH en las demos; español sin evidencia [NV] |
| Duración y audio | 10 s–10 min [V:S1]; salida a 48 kHz medida en el spike anterior | Hasta 6 min (4 por defecto); codec 48 kHz estéreo [V:S4,S5] | Hasta 5 min; 32 kHz estéreo [V:S10] |
| ¿Cabe en 12 GB? | **Sí.** La 5070 (11,94 GiB) es **tier 4** en `gpu_config.py`: 2B turbo/sft + **LM 0.6B**. El LM 1.7B es del tier 5 (12–16 GB) y XL pide ≥ 12 GB con offload + INT8 → experimentos de M0 T-09 [V:S1, GPU_COMPATIBILITY.md] | Sin benchmark local: cuantización4bits según [P:S7]; upstream también propone lazy_load. No se confirma encaje BF16 en12GB | **Justo**: cabe en 8 GB con offload por capas, pero lento [V:S10] |
| Velocidad | Rápido (turbo, pocos pasos); se mide [M0] | RTF ≈ 1 [V:S4] | Lento con offload [V:S10] |
| Capacidades | text2music, **repaint**, **cover**, retake, vocal2BGM, flow-edit, **LoRA**; extract/lego/complete solo en el checkpoint base [V:S1,S2] | Letra + tags; referencia de audio pendiente; sin LoRA oficial [V:S4] | Letra con secciones y captions estructurados; sin cover, edición ni extend [V:S10] |
| Calidad frente a Suno | Según el equipo, «entre Suno v4.5 y v5» [V:S1]. Arena de Khala: 1471 frente a 1644 de Suno v5 [V:S13]. «Brillo metálico» en las voces [P:S14] | Arena de Khala: 1422 [V:S13]; «todo suena a pop genérico» [P:S14] | **El único abierto en la arena vocal independiente de Artificial Analysis**: Elo 1000 frente a 1134 de Suno v6 [V:S12] |
| Dependencias en sm_120 | Python 3.11, `torch 2.10+cu128`; flash-attn opcional (SDPA); backend `pt` para el LM (el de vLLM da segfault) [V] | `torch<2.11`, `bitsandbytes==0.49`, `transformers==4.57` [V] | diffusers / ComfyUI [V:S25] |

### 1.2 Por qué ACE-Step sigue siendo el principal

Es el único candidato que reúne todo esto a la vez:

- **pesos MIT** y datos declarados como licenciados o sintéticos;
- **soporte oficial para 12 GB**;
- **las operaciones de edición que hacen falta para parecerse a Suno**: repaint, cover, extend (con máscara de repaint) y stems (extract, en el checkpoint base);
- **LoRA** para estilos propios.

La 5070 permite además activar el **planificador LM**, que controla el idioma, la estructura y los metadatos (BPM, tonalidad), y probar **XL** como modo de alta calidad.

**Configuración inicial:** DiT 2B **turbo** + LM **0.6B**, en BF16, sin offload, sin cuantización y sin `torch.compile` (modos forzados, no los automáticos del tier 4). **Experimentos de M0 T-09:** LM 1.7B, checkpoints sft/base, XL-turbo (≈ 20 GB en disco, fp32) con offload + INT8. **Modo alta calidad (F-18):** el que gane en T-09, si cabe con margen.

**Repos en Hugging Face (todos MIT):** el bundle `ACE-Step/Ace-Step1.5` trae turbo + LM 1.7B + VAE (encoder y decoder) + Qwen3-Embedding (~10 GB); **sft, base, LM 0.6B y XL son repos separados**, cada uno con su revisión en el lock. Cada DiT trae `silence_latent.pt` (pickle, tensor [1,64,15000]) → convertido por el auditor ([ADR-0006](../decisiones/ADR-0006-seguridad-de-pesos.md)); y `.py` de `trust_remote_code` → fijados con SHA-256. Idioma del canto: parámetro `vocal_language` (por defecto `"en"`: pasar `"es"` en castellano). Integración: el adapter envuelve la **API Python** (handler), no la REST (`/release_task` + sondeo), que no da progreso ni permite descargar el modelo.

### 1.3 Descartados (a 2026-09-28)

| Modelo | Motivo |
|---|---|
| YuE2-3B (sep-2026) | Pesos **CC-BY-NC 4.0**; solo Linux y FlashAttention. Candidato de **laboratorio** si se quiere comparar [V:S8] |
| LeVo 2 / SongGeneration v2 (mar-2026) | **Solo uso académico** [V:S15]. Según un análisis de terceros, la mejor calidad abierta [P:S14]. Laboratorio como mucho |
| Khala 1.0 | CC-BY-NC y 24 GB [P] |
| MuLaCover, JAM-0.5, MusicGen, Open-Unmix | No comerciales [V/P] |
| Muse (Fudan) | Entrenado con salidas de Suno v5: riesgo legal [P:S14] |
| Qwen-Music, StepAudio 3 Music | Sin pesos oficiales [NV] |
| Stable Audio 3 Medium, Magenta RealTime 2, InspireMusic | No cantan (solo instrumental). Stable Audio 3 queda como opción para **instrumentales** con datos licenciados (Stability Community License: licencia enterprise por encima de 1 M$) [P:S17] |
| YuE v1, SongGen, SongBloom, DiffRhythm 2 | Peor calidad o limitaciones (SongBloom: 2:30 y necesita un prompt de audio). DiffRhythm 2 (Apache) queda en reserva |
| «Ace-Step2.0» en HF | Subida de terceros, no oficial |

## 1-bis. Imagen y vídeo

Ver [`video.md`](./video.md) §4: Wan 2.2/2.1 (Apache 2.0), InfiniteTalk (Apache 2.0), Z-Image-Turbo, Qwen-Image-2512/Edit-2511, FLUX.2 klein 4B (Apache 2.0), Depth Anything V2 Small, beat_this, allin1; ejecutados en `engine-comfy` ([ADR-0016](../decisiones/ADR-0016-comfyui-como-motor-de-imagen-y-video.md)). El LLM local del §2 también escribe el guion de planos.

## 2. Asistente de letras (LLM)

| Opción | Licencia | VRAM | Uso |
|---|---|---|---|
| **Gemma 4 12B-it (QAT Q4 GGUF)** | Apache 2.0 [V] | ~7–8 GB en Q4 [NV] | **Por defecto** ([ADR-0012](../decisiones/ADR-0012-llm-de-letras.md)): local, sin conexión; se turna con el generador en la GPU |
| Qwen3.5-9B | Apache 2.0 [V] | Q4–Q8 [NV] | Alternativa local si Gemma rinde peor en castellano (prueba en M2) |
| Claude API (Sonnet 5 / Haiku 4.5) | Servicio de pago por uso; por defecto la API no entrena con los datos [V] | 0 | **Opcional**, desactivada de fábrica ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)): comparar calidad o usar con la GPU ocupada |

La salida del LLM siempre se valida con el parser de etiquetas antes de ofrecerse como letra. El prompt de sistema prohíbe reproducir letras existentes.

## 3. Evaluación automática (M0 y regresiones)

| Uso | Elegido | Licencia | Alternativa |
|---|---|---|---|
| **WER de la letra cantada** | **Qwen3-ASR-1.7B** (safetensors): WER 5,98 en M4Singer frente a 13,58 de Whisper-v3; admite canto con acompañamiento [V] | Apache 2.0 [V] | Whisper large-v3-turbo (MIT) como segunda opinión |
| **Tiempos por palabra (LRC, vídeo)** | **Qwen3-ForcedAligner-0.6B** sobre la voz, con la letra conocida | Apache 2.0 [V] | Whisper con timestamps |
| **Similitud audio-texto** | LAION `larger_clap_music` — solo publica `pytorch_model.bin` (pickle) → **convertido** por el auditor | Apache 2.0 (pesos) [V] | MuQ-MuLan (**NC**, solo referencia interna) |
| **Estética** | Audiobox Aesthetics (CE/CU/PC/PQ) — usar `model.safetensors` (el repo trae también `checkpoint.pt`) | CC-BY-4.0 [V] | SongEval (licencia ambigua: solo uso interno) |

Todos corren en `engine-analysis` ([contrato-engines.md](./contrato-engines.md) §6).

## 4. Herramientas de producción

| Uso | Elegido | Licencia | Nota |
|---|---|---|---|
| **Stems** | 1.º **extract de ACE-Step** (checkpoint base) | MIT [V] | Licencia limpia; calidad por medir [M3] |
| | 2.º Mel-Band RoFormer (voces) + BS-RoFormer/SCNet (4 stems) vía MSST | Código MIT; licencia de pesos **ambigua** o sin declarar [V] | Válido en uso personal; ⚠️ antes de comercializar |
| | ✗ Demucs | Pesos solo para investigación [NV] | Descartado |
| **Letra sincronizada (LRC)** | Qwen3-ForcedAligner-0.6B (+ Qwen3-ASR para verificar) | Apache 2.0 | F-34 |
| **Conversión de voz** (futuro) | RVC v2 | Código y pesos MIT; base VCTK CC BY 4.0 [V] | Solo con voces propias; revisar ContentVec y RMVPE |
| **Marca de agua** (solo si se comercializa) | audiowmark (proceso aparte) + AudioSeal | GPLv3+ / MIT [V] | Fuera del alcance personal ([ADR-0008](../decisiones/ADR-0008-procedencia-y-linaje.md)) |
| **Loudness y transcodificación** | FFmpeg LGPL (lame, opus), pyloudnorm, soxr | LGPL / MIT / LGPL [V] | [pipeline-audio.md](./pipeline-audio.md) |
| **Beats y BPM** | **beat_this** (checkpoint Lightning `.ckpt` → convertido) | MIT código y pesos [V]; ⚠️ el README avisa de datos de entrenamiento con copyright | F-33 |
| **Tonalidad y energía** | librosa | ISC | F-33; evitar essentia (AGPL) |
| **Secciones** | Estructura de la letra (`[verse]`, `[chorus]`…) alineada con el audio; allin1 solo en laboratorio (arrastra Demucs, madmom y NATTEN) | — | F-33, F-43 |

## 5. Presupuesto de VRAM (orden secuencial, un modelo cada vez)

| Fase del trabajo | Modelo residente | VRAM estimada |
|---|---|---|
| Generar | ACE-Step 2B turbo + LM 0.6B (BF16) | ~8–10 GB [M0] |
| Generar (alta calidad) | ACE-Step XL-turbo + offload + INT8 | ≤ 11 GB con offload [M0] |
| Stems | ACE-Step base (extract) o RoFormer | ~4–8 GB [M3] |
| Evaluar | Qwen3-ASR-1.7B → CLAP → Audiobox | ~4 / 2 / 2 GB [NV] |
| Letras (por defecto) | Gemma 4 12B Q4 | ~7–8 GB [NV] |

## 6. Qué se decide en M0

1. VRAM pico y tiempo por pista de 3 min de 2B turbo + LM 0.6B (configuración inicial) y si el LM 1.7B cabe con margen en ~10,7 GB libres sin desbordar.
2. turbo, sft o base, y LM 0.6B o 1.7B: calidad frente a velocidad en la escucha.
3. Si XL-turbo aporta lo suficiente para justificar el modo de alta calidad.
4. Si HeartMuLa en 4 bits supera a ACE-Step en castellano; si es así, entra como segundo motor en M5 (F-74).
5. MiniMax-Music3: solo si sobra tiempo, como referencia de calidad.

## 7. Fuentes

- S1 https://github.com/ace-step/ACE-Step-1.5 · S2 …/releases · S3 https://huggingface.co/ACE-Step/acestep-v15-xl-turbo
- S4 https://github.com/HeartMuLa/heartlib · S5 https://arxiv.org/html/2601.10547v2 · S6 https://huggingface.co/HeartMuLa/HeartMuLa-oss-3B · S7 https://github.com/benjiyaya/HeartMuLa_ComfyUI/blob/main/README_FP4.md
- S8 https://huggingface.co/m-a-p/YuE2-3B · S10 https://huggingface.co/MiniMaxAI/MiniMax-Music3 · S11 …/blob/main/LICENSE · S12 https://artificialanalysis.ai/music/leaderboard/vocals
- S13 https://arxiv.org/html/2605.01790v1 · S14 https://www.it-jim.com/blog/best-open-source-ai-music-generator/ · S15 https://huggingface.co/spaces/tencent/SongGeneration/blame/main/LICENSE · S17 https://huggingface.co/stabilityai/stable-audio-3-medium · S25 https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3
- Auxiliares: https://huggingface.co/Qwen/Qwen3-ASR-1.7B · https://arxiv.org/pdf/2601.21337 · https://huggingface.co/laion/larger_clap_music · https://huggingface.co/facebook/audiobox-aesthetics · https://github.com/ZFTurbo/Music-Source-Separation-Training · https://github.com/swesterfeld/audiowmark · https://github.com/facebookresearch/audioseal · https://huggingface.co/lj1995/VoiceConversionWebUI · https://huggingface.co/google/gemma-4-12B-it · https://ffmpeg.org/legal.html
- Blackwell y WSL2: ver [entorno.md](./entorno.md).

**Imagen Docker oficial:** existe `ghcr.io/ace-step/ace-step-1.5` (`latest` = `0.1.8`, linux/amd64) y el repo trae `Dockerfile` y `docker-compose.yml` [V]. **No se usa tal cual**: carga el LM 4B por defecto (OOM en 12 GB) e instala el ffmpeg GPL de apt. Sirve de referencia para el Dockerfile propio ([entorno.md](./entorno.md) §2).


## Revisión de naturalidad — 2026-10-05

[Revisión de candidatos T-15](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t15/model-review.md): fuentes primarias actualizadas, límites de memoria y licencias, y evidencia local separada de declaraciones de autores. SFT2B y HeartMuLa3B son prioridades para probar; no hay cambio de motor por defecto ni superioridad musical acreditada. T-14 no mostró ganador consistente de shift y el propietario sigue percibiendo falta de naturalidad. La comparación de prompts T-15 mantiene la configuración actual fija.
