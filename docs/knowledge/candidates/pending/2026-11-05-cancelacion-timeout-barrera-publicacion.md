---
category: GOTCHA
evidencia: validated_case
fecha: 2026-11-05
fuentes:
  - apps/server/app/publication.py
  - apps/server/app/domain_routes.py
  - apps/server/app/queue/cancellation.py
  - apps/server/tests/test_queue_cancel_publication.py
  - .cache/dev-cycle/20261105-m1-docker/review1-fix/root-cause.txt
  - .cache/dev-cycle/20261105-m1-docker/review1-fix/receipt.json
tags:
  - "area:api"
  - "componente:cancelacion"
  - "garantia:publicacion-coherente"
  - "error:PublicationTimeout"
---

# El timeout de la barrera de publicación debe conservar el estado de cancelación

Propuesta de conocimiento para curación. La categoría y el nivel de evidencia propuestos siguen la taxonomía local; no constituyen aprobación.

## Síntoma

Cancelar un job mientras otro hilo retenía la barrera de publicación devolvía `500 INTERNAL`. La operación no había alcanzado el callback que modifica el job.

## Causa raíz

`PublicationCoordinator` lanza `PublicationTimeout` si no adquiere la barrera dentro del plazo. La excepción escapaba del manejador HTTP de cancelación, que carecía de una traducción específica para esa contención temporal.

## Qué hacer en su lugar

Captura exactamente `PublicationTimeout` en `_cancel_job` y devuelve el problema existente `503 SERVICE_UNAVAILABLE`. No confirmes una cancelación ni publiques invalidaciones si no adquiriste la barrera y no hubo mutación.

Conserva estados de Job/Take, `cancel_requested_at` y epoch/cursor del EventBus. Esta regla distingue falta de adquisición de un fallo posterior al commit; no convierte toda excepción de publicación en ausencia de cambios.

## Evidencia

`test_cancel_barrier_timeout_returns_503_without_rows_or_feed_changes`, en `apps/server/tests/test_queue_cancel_publication.py`, retiene una barrera real desde otro hilo con plazo de adquisición de 0,01 segundos.

La prueba usa ASGI y SQLite reales. Comprueba el 503, el código `SERVICE_UNAVAILABLE`, estados sin modificar, ausencia de marca de cancelación y ningún evento nuevo para el suscriptor.

El mismo archivo diferencia rollback previo al commit (`test_precommit_failure_rolls_back_real_rows_and_preserves_feed`) de incertidumbre posterior (`test_commit_uncertainty_preserves_durable_terminal_and_invalidates`). En el segundo caso conserva el terminal durable y sí invalida el feed.

Los recibos privados auxiliares registran el RED y el GREEN de B2. La excepción, su captura y las regresiones también están en las fuentes públicas citadas. Esta propuesta no vuelve a ejecutar pruebas ni amplía la aceptación de M1.
