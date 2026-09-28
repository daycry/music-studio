# ADR-0018 · Cola de jobs: carriles, prioridades, dependencias y recuperación

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Concreta [ADR-0004](ADR-0004-sqlite-y-cola-propia.md)

## Decisión

- **Tablas.** `job` y `job_dependency`, definidas en [`../arquitectura/datos.md`](../arquitectura/datos.md). Cada entidad producida guarda su `job_id`.
- **Carriles.**

  | Carril | Concurrencia | Qué ejecuta |
  |---|---|---|
  | `gpu` | 1 | Cualquier engine local |
  | `cpu` | 2 | Post-proceso, manifiesto, render, exportación y backup |
  | `remote` | 1 por proveedor | Proveedores externos opcionales |

- **Prioridades.** `interactive` (LLM, previsualizaciones, análisis ligero) > `normal` (generaciones) > `batch` > `nightly`. Un job `nightly` solo se lanza dentro de `STUDIO_NIGHTLY_WINDOW` (`not_before`).
- **Orden dentro de una misma prioridad.** FIFO. Además, se agrupan los jobs que usan **el mismo modelo** antes de cambiar de modelo, sin retrasar ninguno más de `STUDIO_MAX_REORDER_S` (120 s por defecto).
- **Sin expropiación.** Un job en curso no se interrumpe. Por eso los trabajos largos se trocean: el vídeo se genera **plano a plano**, un job por plano.
- **Dependencias.** Un job con dependencias pendientes queda en `blocked`. Si un padre falla, sus hijos pasan a `failed` con `error_code=DEPENDENCY_FAILED`.
- **Reintentos.** Automáticos solo si el engine marca el error como `retryable`, hasta `max_attempts` (2 por defecto). `VRAM_EXCEEDED` se reintenta una vez en modo `offload` si el descriptor lo tiene.
- **Recuperación.** Al arrancar:
  - `queued` y `blocked` se conservan;
  - `running` pasa a `interrupted` y se reencola si la petición es idempotente (lleva semilla fija);
  - se limpian los temporales huérfanos.
- **Cancelación.** El server marca `cancel_requested_at` y la propaga al engine (`DELETE /v1/jobs/{id}`).
- **Cambio de modelo.** Antes de despachar a un engine distinto del que tiene la VRAM, el dispatcher llama a `POST /v1/unload` y espera a que `/v1/health` muestre la VRAM liberada. Las tareas que el descriptor marca como `device: cpu` (p. ej. `audio.beats`) van por el carril `cpu` y no descargan la GPU: así no se recarga ACE-Step después de cada análisis.
- **Una petición = una cadena de jobs.** Primero el job de generación, con N salidas, `seed + i` y los takes compartiendo `job_id`. Después `post.audio` en el carril `cpu`. Por último un `audio.beats` por take. Todos se crean en la misma transacción; los dependientes quedan en `blocked`. El detalle, junto con el reintento manual y la recuperación, está en [`../arquitectura/sistema.md`](../arquitectura/sistema.md) §3.

## Consecuencias

- M1 implementa los carriles `gpu` y `cpu`, la prioridad, las dependencias (take → análisis), los reintentos y la recuperación.
- `remote`, `nightly` y el agrupado por modelo empiezan a tener efecto en M2–M4, pero sus columnas y su lógica base existen desde M1.
