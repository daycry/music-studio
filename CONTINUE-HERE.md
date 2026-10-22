# Continuar aquí

> Una pantalla como máximo (ADR-0089). El estado vive en los `tasks.md` y esto solo apunta.

**Actualizado:** 2026-10-22, reencauce tras la etapa de Codex.

## Dónde estamos

| Hito | Estado | Ledger |
|---|---|---|
| M0 · Entorno y motor | 13/18 vigentes. Falta: revisar T-08, T-16 y T-20, el benchmark básico (T-09) y **la escucha del propietario (T-13)** | [tasks.md](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) |
| M1 · MVP web (recortado) | 0/15 completadas; T-04 y T-05 integradas y en revisión (cierran con T-15). El resto del código está escrito, pero sin revisar | [tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md) |
| M2 y M3 | **Congelados** y archivados en [`docs/archive/codex-2026-10/`](docs/archive/codex-2026-10/README.md) | — |

## Siguiente paso

T-05 y T-04 están **integradas en `main` y en `en-revision`** (2026-10-22). Pasan a `completado` cuando T-15 ejecute sus E2E (T-05: E2E-01 y E2E-09; T-04: E2E-04, E2E-05 y E2E-06).
- T-05: los takes se publican sobre la carpeta de datos de Docker Desktop.
- T-04: un post interrumpido se reanuda solo, los jobs se cancelan sin dejar restos y los GPU dudosos se reintentan ([ADR-0090](docs/decisiones/ADR-0090-reintento-acotado-de-intentos-dudosos.md)).

1. **M1/T-07: H1.** Una generación sin `params.duration_s` se acepta, pero el post-proceso falla, y la web no envía ese campo. Hoy, una generación desde la UI fallaría.
2. **Fuga de temporales (H5 + B5 + N7)**: cada canción deja copias del WAV y JSON en `data/tmp`, y el barrido de cancelados reintenta para siempre los fallos permanentes. Conviene una tarea corta, con `quick-implement`.
3. Cerrar T-01 a T-03 y T-06 (código ya escrito): revisión de dos lentes y su Verificación.
4. En paralelo, cuando el propietario pueda: M0/T-09 básico y la escucha de M0/T-13.

> **No abras `data/db/studio.sqlite` desde Windows con el stack en marcha** (GOT-002).

## Reglas que no se olvidan

- Un hito activo a la vez.
- Ledger = estado, criterios y verificación; nada de diario.
- ADR solo para decisiones reales.
- Antes de usar la GPU, libera el Ollama compartido (AGENTS.md §4.8).

## Historial

- Etapa Codex completa: rama `rescue/2026-10-22-codex`, commit `36d4e99`. Es solo local hasta que el propietario la suba.
- Resumen en [`docs/archive/codex-2026-10/README.md`](docs/archive/codex-2026-10/README.md).
