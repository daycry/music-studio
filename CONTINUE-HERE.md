# Continuar aquí

> Una pantalla como máximo (ADR-0089). El estado vive en los `tasks.md` y esto solo apunta.

**Actualizado:** 2026-10-23, T-08 integrada.

## Dónde estamos

| Hito | Estado | Ledger |
|---|---|---|
| M0 · Entorno y motor | 13/18 vigentes. Falta: revisar T-08, T-16 y T-20, el benchmark básico (T-09) y **la escucha del propietario (T-13)** | [tasks.md](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) |
| M1 · MVP web (recortado) | 1/16 completadas (T-17, fuga de temporales). T-04, T-05, T-07 y T-08 están integradas en `main`, en `en-revision` (cierran con T-15). El resto del código está escrito, pero sin revisar | [tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md) |
| M2 y M3 | **Congelados** y archivados en [`docs/archive/codex-2026-10/`](docs/archive/codex-2026-10/README.md) | — |

## Siguiente paso

**T-08 (base de la web)** está integrada en `main` (2026-10-23) y en `en-revision`.
- **Qué incluye:**
  - el cliente tipado desde `api.d.ts`, con el tope de VRAM real (`cap_mb`);
  - contraste AA en el tema oscuro;
  - estados traducidos;
  - DTO de las respuestas 202 y 200;
  - `build` en verde, con las cachés de SWC en `.cache/swc` y `.cache/la` (MAX_PATH);
  - `PLAYWRIGHT_BROWSERS_PATH` fijado.
- **Deuda aceptada** (ver el ledger):
  - lecturas de `api.ts` sin validar en runtime;
  - hex en `Waveform` y `GenerativeViz`;
  - tareas no-M1 que aparecen como «Desconocido» en Sistema;
  - sin test de las claves `engineState`.

1. **T-09 (Crear)**, después T-10 a T-13: revisar el código heredado y arreglar solo lo roto. Un ejemplo es `rating: 0`, que da 422.
2. **T-15**: E2E con Playwright y el mock. Al pasar, cierra T-04, T-05, T-07 y T-08 y la web.
3. Cerrar T-01 a T-03 y T-06: revisión de dos lentes y su Verificación.
4. Con el propietario y la GPU: M0/T-09 básico, la escucha de M0/T-13 y después M1/T-16.

`pnpm` solo desde PowerShell (`. .\scripts\env.ps1; pnpm --filter ./apps/web <script>`).

> **No abras `data/db/studio.sqlite` desde Windows con el stack en marcha** (GOT-002).

## Reglas que no se olvidan

- Un hito activo a la vez.
- Ledger = estado, criterios y verificación; nada de diario.
- ADR solo para decisiones reales.
- Antes de usar la GPU, libera el Ollama compartido (AGENTS.md §4.8).

## Historial

- Etapa Codex completa: rama `rescue/2026-10-22-codex`, commit `36d4e99`. Es solo local hasta que el propietario la suba.
- Resumen en [`docs/archive/codex-2026-10/README.md`](docs/archive/codex-2026-10/README.md).
