# CLAUDE.md — Plataforma de generación musical por IA (proyecto personal, self-hosted)

Guía operativa para Claude (Cowork, Claude Code o cualquier agente) al trabajar en este repositorio. Léela antes de tocar nada.

## Qué es este proyecto

Plataforma web personal/self-hosted para generar canciones con IA: el usuario introduce una letra, un prompt de estilo y opciones de voz, y obtiene una canción descargable (MP3, FLAC; WAV/48 kHz a demanda) con **registro de trazabilidad desde la primera pista**. Equivalente funcional a Suno, self-hosted con modelos open source (ACE-Step 1.5 de referencia, HeartMuLa como segundo adapter; solo licencias con uso comercial permitido).

**Stack**: monorepo Next.js (frontend) + Python/FastAPI (backend) · Postgres (con linaje `parent_id`/`root_id`/`derivation_kind`) · Redis/cola · S3 (FLAC como formato de almacén) · GPU L40S en RunPod (pod caliente en horario laboral Europe/Madrid + efímero de desborde, keep-warm 10 min) · OTel. **Runner GPU ejecutable en cloud RunPod, en local con GPU propia (NVIDIA Container Toolkit, RTX 4090/5090 de referencia, 8 GB suelo con offloading), o mock** (`GPU_PROVIDER=local|runpod|mock`, D-29 — ver §"Estado actual").

## Fuente de verdad y cadena de artefactos

Toda la iniciativa vive en `docs/roadmap/2026-07-27-plataforma-musical-ia/`:

| Artefacto | Fichero | Estado |
|---|---|---|
| Spec (revisión 3) | `spec.md` | `aprobada` (ratificada 2026-08-18) |
| Evaluación y presupuesto | `evaluation.md` | `completado` |
| Brief para dirección | `decision-brief.md` / `.pdf` | ratificado |
| Plan de implementación | `improvement-plan.md` | `en-progreso` |
| **Ledger de tareas** | `tasks.md` | **fuente única de progreso** |
| Plan de pruebas | `test-plan.md` | `borrador` |
| Diseño de UI | `ui-design.md` | `propuesta` |

Índice general: `docs/roadmap/README.md`. Parámetros económicos: `.claude/rates.json` (fuente única: 50 €/h, margen 20 %, supervisión 25 %, tokens Opus 5 verificados 5/25 $/M).

## Regla de ledger canónico (obligatoria)

El progreso de un plan se registra en `docs/roadmap/<fecha>-<slug>/tasks.md`; **cualquier implementador — incluidos orquestadores externos — debe marcar ahí cada tarea** (`pendiente → en-progreso → completado`). Los ledgers propios de otras herramientas son espejo, no fuente. No crear ledgers paralelos. Las tareas se cierran solo cuando sus criterios de aceptación (checkboxes) están verificados.

## Estado actual y qué está autorizado

- **Aprobado y ejecutable**: Fase 0 + Fase 1 — tareas T-01…T-53 + T-85, 656 h base / 39.360 € con margen (ratificado 2026-08-18, incluida la ampliación GPU local D-29). Decisión del mismo día: los spikes de la Fase 0 y la generación de las pistas del gate G1 se ejecutan preferentemente en GPU local, a coste cloud cero salvo la medición de arranque en frío (solo posible en RunPod); T-85 (proveedor local de producción con abstracción completa) sigue en F6.
- **Pre-planificado, NO autorizado**: Fases 2–3 — tareas T-54…T-84 en `bloqueada (gate)`. No implementar sin que su gate se supere.
- **No-go vigente**: Fase 4 (fine-tuning propio y clonación de voz). Sin tareas. No planificar como ejecutable.

### Gates (bloqueos duros, en orden)

1. **G2 legal (T-01)** — bloquea TODO el desarrollo. Dos preguntas por escrito a legal (procedencia del audio + protegibilidad del output), timebox 10 días laborables, matriz de resultados pre-acordada.
2. **T-02 gobernanza** — ✅ **completado en modo solo (2026-09-01)**: evaluador único y usuario piloto = el propietario, construir-vs-comprar documentada (`gates/gobernanza.md`). **El bloqueo de gobernanza está levantado; el bloqueo restante es de entorno GPU** (máquina local, toolkit, pesos — `pre-dev-checklist.md` §A, ítems 5–7).
3. **G1 calidad** (fin de Fase 0) — escucha ciega de ACE-Step con protocolo numérico (7/10 ≥ 4/5, WER ≤ 15 %). **Se ejecuta en modo solo según `gates/gobernanza.md` §2** (el propietario puntúa, umbrales fijados antes de escuchar, sin degradarlos; riesgo de independencia aceptado por escrito).
4. **G1-bis** — mismo protocolo por cada adapter nuevo (HeartMuLa).
5. **Stop-loss** (cierre de C-13) — >60 % del presupuesto con <40 % del alcance → parada y decisión.
6. **G3 adopción** (antes de Fase 3) — **en modo solo según `gates/gobernanza.md` §3**: ≥100 generaciones propias, uso sostenido, ≥1 pista usada en algo real, autoevaluación honesta ≥4/5. Umbrales sin degradar.

**Nunca saltarse un gate ni degradar un umbral para «pasar».**

## Invariantes técnicos innegociables

- **Solo `safetensors`** — jamás `pickle`/`torch.load` sobre checkpoints no confiables (es RCE). `weights_sha256` verifica integridad, no inocuidad.
- **Manifiesto de procedencia en cada generación** desde la primera pista, con `manifest_schema_version` y ledger append-only con cadena de hashes. El esquema del manifiesto lo firma legal antes de implementarse.
- **Declaración de derechos de la letra** (bloqueo duro) en cada generación; gate de titularidad obligatorio en covers.
- **Licencias comerciales verificadas** para toda herramienta del pipeline (modelos, Demucs, watermarker, RVC) ANTES de integrarla. MusicGen está descartado (CC BY-NC). **(pesos de Demucs confirmados CC-BY-NC el 2026-08-18: buscar alternativa con pesos MIT o licenciar)**.
- El runner GPU corre **sin credenciales persistentes**; aislamiento entre trabajos.
- **Tope de gasto GPU mensual agregado + kill switch** — hay `max_gpu_seconds` por trabajo Y límite global.
- FLAC como almacenamiento; WAV/48 kHz solo exportación a demanda. Loudness EBU R128 por destino.
- i18n castellano (`next-intl`) desde el día 1. Componentes accesibles por defecto (shadcn/ui / Radix).
- Los E2E validan **contratos observables** (estados, formatos, manifiesto, duración ±5 %, loudness), nunca la calidad musical — eso es escucha humana (G1).

## Diseño de UI

Seguir `ui-design.md` estrictamente: concepto «estudio nocturno» (oscuro cálido en 4 capas, acento verde traza `#34D399`, Inter + Bricolage Grotesque), firma visual de «condensación de onda» ligada al progreso real por SSE, mensajes de espera honestos (cold start 2–6 min: cronómetro, nunca barra falsa). La UX de Suno es referencia **funcional**; la identidad visual es propia — prohibido clonarla. Contraste AA en todo par texto/fondo (requisito de color desde la Fase 1; la conformidad WCAG AA completa no es objetivo de Fase 1 — D-25).

## Flujo de trabajo con agentes (plugin custom-agents)

- Ciclo de desarrollo: `/dev-cycle` sobre la carpeta de la iniciativa (cadena nativa por defecto). El plan ya existe: arranca en implementación tras las puertas.
- Cambios pequeños fuera del plan: vía rápida de `/dev-cycle` o skill `quick-implement` (mantiene revisión de dos lentes + qa-gate).
- QA: agente `qa` ejecuta `test-plan.md` (bloques E2E-xx con Playwright, `MOCK_GPU=1` por defecto; suite GPU real solo nocturna y acotada).
- Retro al cerrar fases: `/retro` (alimenta la calibración del evaluator — este proyecto ya corrigió su estimación un 44 %, hay que construir histórico).
- Confluence/Jira: **opt-in no activado** (`.claude/confluence.json` y `.claude/jira.json` no existen). No publicar ni crear issues sin activarlo con `/setup`.

## Convenciones de código (cuando exista código)

- Ramas: `feature/<slug>` por iniciativa; commits `T-XX: descripción`.
- Sin restos de instrumentación de debug en los diffs.
- Tests junto al código; los criterios de aceptación con test exigen el test.
- Flujo solo (decidido 2026-09-01): ramas `feature/<slug>` y merge directo a `main` sin PR; commits `T-XX`.

## Contacto

Propietario de la iniciativa: Daycry (proyecto personal; posible comercialización futura — ver gate GC-01 en `gates/gobernanza.md`). Todas las decisiones son suyas.
