# Continuar aquí

> Una pantalla como máximo (ADR-0089). El estado vive en los `tasks.md` y esto solo apunta.

**Actualizado:** 2026-10-22, reencauce tras la etapa de Codex.

## Dónde estamos

| Hito | Estado | Ledger |
|---|---|---|
| M0 · Entorno y motor | 13/18 vigentes. Falta: revisar T-08, T-16 y T-20, el benchmark básico (T-09) y **la escucha del propietario (T-13)** | [tasks.md](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) |
| M1 · MVP web (recortado) | 0/15 vigentes. Hay código escrito, pero sin cerrar ni revisar | [tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md) |
| M2 y M3 | **Congelados** y archivados en [`docs/archive/codex-2026-10/`](docs/archive/codex-2026-10/README.md) | — |

## Siguiente paso

1. **M1/T-05: publicación sencilla de takes.**
   - Hoy la publicación usa `renameat2(NOREPLACE)`, que falla sobre el bind de Docker Desktop, así que no hay camino de punta a punta.
   - Implementarla con `/custom-agents:dev-cycle docs/roadmap/2026-09-28-m1-mvp-estudio`, que va directo a implementar.
2. A continuación, cerrar T-01 a T-04 y T-06 (código ya escrito): revisión de dos lentes y su Verificación.
3. En paralelo, cuando el propietario pueda: M0/T-09 básico y la escucha de M0/T-13.

## Reglas que no se olvidan

- Un hito activo a la vez.
- Ledger = estado, criterios y verificación; nada de diario.
- ADR solo para decisiones reales.
- Antes de usar la GPU, libera el Ollama compartido (AGENTS.md §4.8).

## Historial

- Etapa Codex completa: rama `rescue/2026-10-22-codex`, commit `36d4e99`. Es solo local hasta que el propietario la suba.
- Resumen en [`docs/archive/codex-2026-10/README.md`](docs/archive/codex-2026-10/README.md).
