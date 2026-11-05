---
category: GOTCHA
evidencia: validated_case
fecha: 2026-11-05
fuentes:
  - apps/server/app/queue/runtime.py
  - apps/server/app/queue/retry.py
  - apps/server/app/queue/terminal_takes.py
  - apps/server/tests/test_queue_terminal_takes.py
  - apps/server/tests/test_dispatcher_retry.py
  - .cache/dev-cycle/20261105-m1-docker/review1-fix/root-cause.txt
  - .cache/dev-cycle/20261105-m1-docker/review1-fix/receipt.json
tags:
  - "area:cola"
  - "componente:retry"
  - "garantia:historia-inmutable"
  - "error:VRAM_EXCEEDED"
---

# Un error retryable puede carecer de un reintento operativo posible

Propuesta de conocimiento para curación. La categoría y el nivel de evidencia propuestos siguen la taxonomía local; no constituyen aprobación.

## Síntoma

Un terminal `VRAM_EXCEEDED` marcado `retryable` podía mantener el postproceso bloqueado indefinidamente. Admission conservaba la posibilidad de reintento; Runtime descartaba cada ciclo porque faltaba `offload` o el intento ya lo había usado.

## Causa raíz

El flag del engine describe el error original. No demuestra que el catálogo y el presupuesto actuales permitan reservar otro intento. Tratar ambas condiciones como equivalentes impedía cerrar los placeholders sin inventar intentos ejecutados.

Tampoco basta con que el descriptor capturado carezca de `offload`: el catálogo fresco puede incorporarlo. La ausencia del modelo, un cambio de identidad o una observación transitoria no prueban imposibilidad estructural.

## Qué hacer en su lugar

Comparte la política de cambio de modo. Ante un intento ya en `offload`, o identidad fresca estable con el modelo presente pero sin ese modo, cierra el presupuesto operativo.

`Retry.close_impossible_vram` reduce `max_attempts` al ordinal realmente ejecutado. Su transacción comprueba por CAS ámbito local, estado, presupuesto, ordinal, modelo/engine, petición y terminal previo. Sólo terminaliza placeholders coincidentes aún sin publicar.

Conserva `JobAttempt`, el terminal `retryable`, la petición y opciones congeladas, procedencia, semillas e índices de salida. No aumentes `attempt` para simular agotamiento. El reintento manual crea otro job con presupuesto de tres intentos.

Mantén la posibilidad de retry ante modelo ausente, identidad cambiada, engine ocupado, VRAM libre insuficiente o backoff. Son condiciones distintas de la imposibilidad estructural comprobada.

## Evidencia

La matriz `test_runtime_and_admission_finish_impossible_vram_retry` de `apps/server/tests/test_queue_terminal_takes.py` cubre catálogo sin offload, intento ya offload, offload disponible y situaciones transitorias. Incluye procedencia capturada y legado. Contrasta estados, presupuesto, historia y reintento manual.

En el mismo archivo, `test_impossible_vram_close_cas_preserves_changed_authority` y `test_impossible_vram_close_rollback_preserves_budget_placeholders_and_feed` comprueban carreras y rollback. `test_retry_budget_three_and_offload_once_verified_only`, en `test_dispatcher_retry.py`, conserva el vecino donde el catálogo fresco permite offload.

Los recibos privados auxiliares registran reproducciones RED y regresiones GREEN del arreglo B1. No son la única fuente: la política y las regresiones permanecen en los archivos públicos citados. Esta propuesta no vuelve a ejecutar pruebas ni acredita inferencia GPU o aceptación musical.
