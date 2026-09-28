---
spec: m0-entorno-y-motor
descripcion: Entorno reproducible, primera canción por CLI en la RTX 5070, números reales y elección de modelo por escucha
estado: aprobada          # borrador | aprobada | implementada | obsoleta
aprobada: 2026-09-28
creado: 2026-09-28
actualizado: 2026-09-28
evaluacion: n/a (proyecto personal — ADR-0001; esfuerzo orientativo en tasks.md)
design: n/a (la arquitectura está en docs/arquitectura/ y docs/decisiones/)
plan: improvement-plan.md
---

# Spec · M0 — Entorno, motor por CLI y elección de modelo

## 1. Objetivo

Salir de M0 con tres cosas:

1. **Una canción generada en la RTX 5070 desde la línea de comandos**, con post-proceso y manifiesto v1.
2. **Números reales** de la 5070: VRAM pico, tiempos de carga y de inferencia, y qué modos caben.
3. **La elección de modelo confirmada por escucha.**

Los cimientos de M0 (`engine-contract`, `engines/common`, `audio-post`, `weights`, el escritor del manifiesto y `engine-analysis`) son los mismos que usará M1. **No se escribe nada que haya que tirar después.**

## 2. Alcance

**Dentro:**

- **T-00 · Prerrequisitos manuales:** Synology, `.wslconfig`, prueba de la GPU en Docker y herramientas.
- **Esqueleto del repositorio** y `.gitignore` según [ADR-0005](../../decisiones/ADR-0005-todo-en-la-carpeta.md).
- **`packages/weights`:**
  - `models.lock.json` y `tools.lock.json`;
  - descarga fijada por revisión;
  - SHA-256 y sello;
  - auditor y conversor de pickle;
  - fijación del código remoto.
- **Contrato y engines base:**
  - `packages/engine-contract`: modelos Pydantic del contrato `/v1`;
  - `apps/engines/common`: servidor `/v1`, proceso hijo, VramGuard y cancelación;
  - `engine-mock` con tareas de audio, texto e imagen.
- **`packages/audio-post`** y el escritor y el verificador del **manifiesto v1**.
- **`engine-acestep`** (imagen y adapter) con las tareas `music.song` y `music.instrumental`.
- **CLI `scripts/generate.py`**, que hace de server.
- **`engine-analysis`** con las tareas `audio.transcribe`, `audio.clap`, `audio.aesthetics` y `audio.beats`.
- **Medición y evaluación:** benchmark de la 5070, matriz de capacidades verificadas, batería de evaluación y sesión de escucha.
- *(Opcional)* `engine-heartmula` en 4 bits.

**Fuera:** server, BD y web (M1); operaciones de edición expuestas al usuario (M2), aunque en M0 se verifica que funcionan.

## 3. Criterios de aceptación

| # | Criterio |
|---|---|
| CA-01 | **Pesos:** `scripts/fetch_models.py --model ace-step-1.5` deja en `models/` los ficheros del lock, verificados por SHA-256, con la revisión fijada.<br>• Un fichero alterado hace fallar la verificación.<br>• Un pickle (`silence_latent.pt`) se convierte a safetensors mediante el auditor, sin ejecutarlo.<br>• Un pickle malicioso de prueba se rechaza.<br>• Los `.py` de `trust_remote_code` quedan fijados con su SHA-256. |
| CA-02 | **Imagen:** `engine-acestep` se construye en local. Dentro del contenedor:<br>• `sm_120 ∈ torch.cuda.get_arch_list()`;<br>• una matmul BF16 da el resultado correcto;<br>• `ffmpeg -buildconf` incluye lame, soxr y opus, y no incluye `--enable-gpl` ni `--enable-nonfree`. |
| CA-03 | **Contrato:** `engine-acestep` y `engine-mock` implementan el contrato `/v1` de [contrato-engines.md](../../arquitectura/contrato-engines.md):<br>• health, models, load, unload, jobs, eventos NDJSON con `seq` y reenganche, y cancel;<br>• su descriptor valida contra `engine-v1.json`;<br>• `engine-mock` sirve una tarea de audio, otra de texto en streaming y otra de imagen, lo que demuestra que el contrato es genérico. |
| CA-04 | **Primera canción:** `scripts/generate.py --brief B-02` (o la forma explícita `--lyrics … --style "…" --duration 180 --language es`) produce en `data/cli/<fecha>/<run_id>/`:<br>• `master.flac` (48 kHz, sin normalizar);<br>• `listen.mp3` (−14 LUFS ±0,5 y true peak ≤ −1 dBTP, medido con ffmpeg);<br>• `peaks.json`;<br>• `manifest.json`, válido contra `manifest-v1.schema.json` (`kind: cli_run`) y que pasa `verify_manifest.py`. |
| CA-05 | **VRAM:**<br>• El tope se calcula a partir de la VRAM libre menos 512 MB y queda registrado en la telemetría junto con el pico.<br>• Una petición que lo excede termina con `VRAM_EXCEEDED` en vez de desbordar a RAM.<br>• `unload` libera la VRAM de verdad: `/v1/health` muestra que `free_mb` vuelve a ±300 MB del valor que tenía antes de cargar. |
| CA-06 | **Benchmark:** `eval/results/benchmark-5070.md` recoge la VRAM pico, los tiempos de carga (bind mount frente a copia local), los tiempos de inferencia y el RTF a 30, 60, 180 y 300 s, e indica si hubo desbordamiento. Configuraciones medidas:<br>• 2B turbo + LM 0.6B (la inicial);<br>• turbo + LM 1.7B;<br>• sft;<br>• base;<br>• XL-turbo con offload + INT8, si cabe. |
| CA-07 | **Capacidades:** `eval/results/capacidades-acestep.md` marca, con audio de evidencia y el comando usado, qué funciona y con qué checkpoint: **`music.song`**, `music.instrumental`, `retake`, `extend`, `repaint` (¿queda intacto fuera de la región?), `cover`, `complete`, `audio.stems` (extract), y las features de `music.song` (`negative_prompt`, `bpm`, `key`, `timbre_ref`, `lora`). El descriptor solo pone `verified: true` en lo que funciona; `music.song` y `music.instrumental` verificadas son requisito para empezar M1. |
| CA-08 | **Batería de evaluación:** `scripts/eval/run.py --candidate <id>`:<br>• genera los 10 briefs × 3 tomas;<br>• iguala el loudness con ganancia lineal y anonimiza las tomas;<br>• calcula WER (Qwen3-ASR), CLAP y Audiobox mediante `engine-analysis`, midiendo antes el suelo de WER del transcriptor. |
| CA-09 | **Escucha y decisión:** la sesión de escucha se hace según [evaluacion-escucha.md](../../calidad/evaluacion-escucha.md) y su informe queda en `eval/results/escucha-m0.md`, con el veredicto. [ADR-0011](../../decisiones/ADR-0011-seleccion-de-modelos.md) y [modelos.md](../../arquitectura/modelos.md) quedan actualizados con la configuración elegida y sus números. |
| CA-10 | **Tests:** `uv run pytest -m "not gpu"` en verde, cubriendo:<br>• auditor y conversor de pickle, SHA-256 y sello;<br>• cálculo del tope, supervisor de proceso hijo y cancelación;<br>• contrato (el JSON Schema generado coincide con el versionado);<br>• audio-post (loudness, true peak, validación);<br>• manifiesto y verificador;<br>• la regla «ni `torch.load` ni `pickle.load`» en `apps/` y `packages/`. |

## 4. Restricciones

- [CONSTITUTION](../../CONSTITUTION.md) completa.
- Versiones de [entorno.md](../../arquitectura/entorno.md) §2: ACE-Step con Python 3.11, `torch 2.10+cu128`, `uv sync --frozen`, backend `pt`, compile desactivado y ffmpeg `lgpl-shared`.
- La 5070 es el **tier 4** de ACE-Step: el adapter fuerza los modos de forma explícita ([ADR-0007](../../decisiones/ADR-0007-gpu-local-12gb.md)).

## 5. Incógnitas

| # | Incógnita | Se resuelve en |
|---|---|---|
| I-01 | ¿Cuánto ocupa 2B turbo + LM 0.6B en BF16 sin offload? ¿Cabe el LM 1.7B con margen en ~10,7 GB libres? | T-09 |
| I-02 | ¿Cuánto tarda la carga de pesos desde el bind mount de Windows? | T-09 |
| I-03 | ¿Qué puntos de enganche ofrece la API Python de ACE-Step para progreso por pasos y cancelación entre pasos? | T-06 |
| I-04 | ¿Hay otros `torch.load` en el camino de carga de upstream, además del de `silence_latent.pt`? | T-06 |
| I-05 | ¿Cómo suena ACE-Step en castellano frente a HeartMuLa? | T-11, T-12, T-13 |
