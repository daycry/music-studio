# Continuar aquí

> Una pantalla como máximo (ADR-0089). El estado vive en los `tasks.md` y esto solo apunta.

**Actualizado:** 2026-10-22, reencauce tras la etapa de Codex.

## Dónde estamos

| Hito | Estado | Ledger |
|---|---|---|
| M0 · Entorno y motor | 13/18 vigentes. Falta: revisar T-08, T-16 y T-20, el benchmark básico (T-09) y **la escucha del propietario (T-13)** | [tasks.md](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) |
| M1 · MVP web (recortado) | 1/16 completadas (T-17, fuga de temporales); T-04, T-05 y T-07 integradas y en revisión (cierran con T-15). El resto del código está escrito, pero sin revisar | [tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md) |
| M2 y M3 | **Congelados** y archivados en [`docs/archive/codex-2026-10/`](docs/archive/codex-2026-10/README.md) | — |

## Siguiente paso

T-04, T-05 y T-07 están **integradas en `main` y en `en-revision`** (2026-10-22). Pasan a `completado` cuando T-15 ejecute sus E2E.
- La API mínima está completa:
  - si no se indica duración, se usan 30 s;
  - descargas MP3/FLAC como fichero;
  - contrato tipado.
- El código de M2 se retiró del server.
- T-17 (`completado`): `data/tmp` ya no acumula temporales tras cada canción.

1. **Web (T-08 a T-13)**: empezar por T-08. Incluye corregir `SystemInfo.gpu.limit_mb` → `cap_mb` y usar los tipos generados.
2. Cerrar T-01 a T-03 y T-06 (código ya escrito): revisión de dos lentes y su Verificación.
3. En paralelo, cuando el propietario pueda: M0/T-09 básico y la escucha de M0/T-13.

> **No abras `data/db/studio.sqlite` desde Windows con el stack en marcha** (GOT-002).

## Reglas que no se olvidan

- Un hito activo a la vez.
- Ledger = estado, criterios y verificación; nada de diario.
- ADR solo para decisiones reales.
- Antes de usar la GPU, libera el Ollama compartido (AGENTS.md §4.8).

## Historial

- Etapa Codex completa: rama `rescue/2026-10-22-codex`, commit `36d4e99`. Es solo local hasta que el propietario la suba.
- Resumen en [`docs/archive/codex-2026-10/README.md`](docs/archive/codex-2026-10/README.md).
