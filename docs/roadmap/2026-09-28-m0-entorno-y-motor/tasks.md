---
generacion:
  fuente: estimado
verificacion: obligatoria
---

# Checklist de Tareas — M0 · Entorno, motor por CLI y elección de modelo

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-28 · reencauzado 2026-10-22 ([ADR-0089](../../decisiones/ADR-0089-reencauce-tras-codex.md)) |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Historial** | [`../../archive/codex-2026-10/m0-tasks.md`](../../archive/codex-2026-10/m0-tasks.md): ledger completo con revisiones e intentos hasta 2026-10-12. Las evidencias crudas están en el commit `36d4e99` |

> **Ledger canónico.** Aquí solo va el estado, los criterios y la salida resumida de la Verificación. El diario de intentos y los recibos de revisión no entran (ADR-0089). Solo el orquestador actualiza este fichero.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Canceladas |
|------|------------|-------|----------|-----------|
| Fase 1 — Preparación | 2 | 2 | 100% | 0 |
| Fase 2 — Cimientos compartidos | 3 | 3 | 100% | 0 |
| Fase 3 — Motor musical | 3 | 3 | 100% | 0 |
| Fase 4 — Medición y elección | 5 | 13 | 38% (5 de 10 vigentes) | 3 |
| **TOTAL** | **13** | **21** | **72% de lo vigente (13/18)** | **3** |

**Para cerrar M0 falta:**

1. Cerrar la revisión de T-08, T-16 y T-20.
2. Hacer el benchmark básico de T-09.
3. La escucha y la decisión del propietario (T-13).

---

## Fase 1 — Preparación

### T-00 — Prerrequisitos manuales de la máquina
- **Descripción**: Máquina lista: GPU visible en Docker, WSL con 24 GB, Python aislado con uv y herramientas instaladas.
- **Estado**: completado
- **Dependencias**: ninguna
- **Verificación** (ejecutada 2026-09-28): `docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi` → `NVIDIA GeForce RTX 5070, 12227MiB` · `wsl -e free -g` → 23 · Node 22.23.2 / pnpm 9.12.0 / uv 0.12.19 / git 2.47.1.
- **Changelog**: Máquina preparada: GPU visible en Docker, WSL con 24 GB, herramientas instaladas y carpetas pesadas fuera de la sincronización.

### T-01 — Esqueleto del repositorio
- **Descripción**: Estructura del monorepo, tooling Python/Node y script de bootstrap desde los locks.
- **Estado**: completado
- **Dependencias**: T-00
- **Verificación**: `.\scripts\bootstrap.ps1` reconstruye `.venv` y `node_modules` · `uv run ruff check .` limpio (ejecutada al cerrar; detalle en el historial).
- **Changelog**: Repositorio inicializado con el esqueleto del monorepo y un script que reconstruye el entorno de desarrollo desde los ficheros de bloqueo.

## Fase 2 — Cimientos compartidos

### T-02 — `packages/weights`: lock, descarga verificada, auditor de pickle y herramientas
- **Descripción**: Descarga reproducible y segura de modelos y herramientas (ADR-0006).
- **Estado**: completado
- **Dependencias**: T-01
- **Verificación**: `uv run scripts/fetch_models.py --check` y `uv run scripts/fetch_tools.py --check` → todo verificado por SHA-256 (detalle en el historial).
- **Changelog**: Descarga reproducible y verificada (SHA-256, revisión fijada) de los modelos de ACE-Step y de evaluación, con conversión segura de pickle a safetensors y ffmpeg LGPL.

### T-03 — `packages/engine-contract` + `apps/engines/common` + `engine-mock`
- **Descripción**: El contrato `/v1` como código, con el servidor común de engines y un engine simulado.
- **Estado**: completado
- **Dependencias**: T-02
- **Verificación**: `uv run pytest packages/engine-contract apps/engines/common apps/engines/mock -m "not gpu"` en verde; revisión de dos lentes intento 3 sin gaps (historial).
- **Changelog**: Contrato /v1 de engines como código, con servidor común, control de VRAM y engine simulado para pruebas sin GPU.

### T-04 — `packages/audio-post` + manifiesto v1 + verificador
- **Descripción**: Post-proceso CPU (FLAC 24, MP3, forma de onda) y manifiesto verificable.
- **Estado**: completado
- **Dependencias**: T-02
- **Verificación**: `uv run pytest packages/audio-post -m "not gpu"` en verde; QA de la Fase 2, 2026-10-05 (historial).
- **Changelog**: Post-proceso de audio en CPU con FLAC de 24 bits, MP3, forma de onda y manifiesto verificable.

## Fase 3 — Motor musical

### T-05 — Imagen `engine-acestep` para sm_120
- **Descripción**: Imagen Docker de ACE-Step con CUDA para la RTX 5070.
- **Estado**: completado
- **Dependencias**: T-03
- **Verificación**: build de la imagen y prueba GPU en la 5070 (historial, revisión de la Fase 3).
- **Changelog**: Imagen de ACE-Step con CUDA, Python 3.11, FFmpeg LGPL y BF16 comprobada en la RTX 5070.

### T-06 — Adapter ACE-Step (`music.song`, `music.instrumental`)
- **Descripción**: La API Python de ACE-Step detrás de `/v1`, con los modos del tier 4 forzados.
- **Estado**: completado
- **Dependencias**: T-05
- **Verificación**: `docker compose run --rm engine-acestep uv run pytest -m gpu` en verde (historial).
- **Changelog**: ACE-Step genera canciones e instrumentales locales mediante /v1, con pesos verificados, semillas exactas, control de memoria y salida WAV estéreo a 48 kHz.

### T-07 — CLI `scripts/generate.py`: primera canción 🎯
- **Descripción**: CLI que llama al engine, ejecuta audio-post y escribe el manifiesto.
- **Estado**: completado
- **Dependencias**: T-04, T-06
- **Verificación**: primera canción completa generada por CLI y escuchada por el propietario (historial).
- **Changelog**: Generación local por CLI desde letra y estilo o catálogo de briefs, con progreso, cancelación y exportaciones inmutables de master, MP3, forma de onda y manifiesto; primera canción completa generada y escuchada.

## Fase 4 — Medición y elección

### T-08 — `engine-analysis` (transcripción, CLAP, estética y beats)
- **Descripción**: Contenedor de análisis que usan M0 (evaluación) y M1 (beats).
- **Estado**: en-revision
- **Dependencias**: T-03, T-02, T-19
- **Verificación**: `uv run pytest apps/engines/analysis -m "not gpu"` en verde **y** `docker compose run --rm engine-analysis uv run pytest -m gpu` en verde. Pendiente de ejecutar después del reencauce.
- **Changelog**: Motor local de análisis con transcripción y alineación secuenciales, similitud CLAP, estética y beats en CPU; pesos verificados, caché segura y descarga del proceso hijo.

### T-09 — Benchmark básico en la 5070
- **Descripción**: **Recortado (ADR-0089).** Medir tiempo por canción, VRAM de pico y si hay desbordamiento a RAM con el modo por defecto de ACE-Step en la 5070. La auditoría canónica y el presupuesto absoluto quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-07, T-19
- **Verificación**: una tabla en este ledger con 3 generaciones (≈2 min de canción): duración, VRAM de pico (`nvidia-smi`) y `spilled=false`.
- **Changelog**: Benchmark básico de ACE-Step en la RTX 5070: tiempo por canción y VRAM de pico.

### T-10 — Matriz de capacidades verificadas
- **Descripción**: Aplazada al backlog (ADR-0089): no bloquea el MVP.
- **Estado**: cancelado
- **Dependencias**: T-07, T-19
- **Verificación**: n/a (cancelada; el trabajo parcial sigue en el historial y en `scripts/eval`).

### T-11 — Batería de evaluación automatizada (F-84)
- **Descripción**: Aplazada al backlog (ADR-0089). El código parcial sigue en `scripts/eval`.
- **Estado**: cancelado
- **Dependencias**: T-07, T-08, T-19
- **Verificación**: n/a (cancelada).

### T-12 — *(Opcional)* `engine-heartmula` en 4 bits
- **Descripción**: Opcional; aplazada al backlog (ADR-0089).
- **Estado**: cancelado
- **Dependencias**: T-03, T-11, T-19
- **Verificación**: n/a (cancelada).

### T-13 — Escucha y decisión de modelo
- **Descripción**: Escucha a ciegas del propietario (T-14, T-15, T-16 y T-09) y decisión de modelo y modo por defecto registrada en un ADR.
- **Estado**: borrador
- **Dependencias**: T-09
- **Verificación**: ADR con el modelo y el modo por defecto elegidos por el propietario y `models/models.lock.json` coherente.

### T-14 — Comparación privada de «Libre»: shift 1 frente a 3
- **Descripción**: Tomas privadas comparables con hoja de escucha a ciegas.
- **Estado**: completado
- **Dependencias**: T-06, T-07
- **Verificación**: seis tomas y hoja de escucha generadas (historial).
- **Changelog**: Añade un shift opcional validado en la CLI y en ACE-Step, y prepara seis tomas privadas de Libre con hoja de escucha a ciegas.

### T-15 — Calidad de Libre: revisión de candidatos y comparación de prompts
- **Descripción**: Revisión de modelos locales alternativos y prueba de prompts.
- **Estado**: completado
- **Dependencias**: T-14
- **Verificación**: candidatos y licencias documentados; seis tomas privadas (historial).
- **Changelog**: Revisa candidatos locales y sus licencias, y prepara seis tomas privadas para comparar prompts con escucha a ciegas.

### T-16 — Controles de inferencia y comparación privada SFT frente a Turbo
- **Descripción**: Controles de inferencia (pasos, CFG, SFT/Turbo) en la CLI y el adapter, con tomas comparables.
- **Estado**: en-revision
- **Dependencias**: T-06, T-07, T-15, T-19
- **Verificación**: `uv run pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py` en verde y las tomas SFT/Turbo preparadas para T-13.
- **Changelog**: Controles de inferencia SFT/Turbo en la CLI y en ACE-Step, con tomas privadas comparables.

### T-17 — Auditoría de fidelidad de prompts hasta LM y DiT
- **Descripción**: Auditoría del transporte de prompts y metadata hasta LM/DiT.
- **Estado**: completado
- **Dependencias**: T-06, T-07, T-15
- **Verificación**: informe de auditoría con evidencia en CPU (historial).
- **Changelog**: Audita el transporte de prompts, tags y metadata hasta LM/DiT con evidencia en CPU.

### T-18 — Preparación fiel y procedencia privada de instrucciones
- **Descripción**: Original y entrada efectiva separados, preparación offline y procedencia privada.
- **Estado**: completado
- **Dependencias**: T-07, T-17
- **Verificación**: `uv run pytest tests/test_generate_preparation.py tests/test_input_preparation.py` en verde (historial).
- **Changelog**: El CLI conserva la letra y el estilo originales, permite preparar entradas offline y registra la procedencia sin perder los tags.

### T-19 — Preflight nativo de tokens y captura de entradas efectivas
- **Descripción**: Presupuesto real de tokens antes de aceptar letra y estilo, sin truncar en silencio.
- **Estado**: completado
- **Dependencias**: T-06, T-18
- **Verificación**: `uv run pytest apps/engines/acestep/tests/test_preflight.py` en verde (historial).
- **Changelog**: La generación comprueba el presupuesto real antes de aceptar letra y estilo y registra entradas efectivas verificables.

### T-20 — Arquitectura de despliegue Docker y Ollama compartido
- **Descripción**: Registrar la arquitectura de despliegue (producto en Docker sobre WSL2, Ollama compartido) en `docs/arquitectura/`.
- **Estado**: en-revision
- **Dependencias**: T-00
- **Verificación**: ADR-0035 y `docs/arquitectura/entorno.md` coherentes con `docker-compose.yml`; `docker compose config -q` sin errores.
- **Changelog**: Documenta el despliegue en Docker sobre WSL2 y el uso compartido de la GPU con Ollama.
