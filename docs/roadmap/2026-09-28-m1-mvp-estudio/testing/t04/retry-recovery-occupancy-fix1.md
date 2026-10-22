# T-04 ? ocupaci?n durable de retry y recovery

Fecha: 2026-10-10

## Alcance

La revisi?n fresca de T-04 detect? que `Retry.reserve` y `Recovery.other_active` contaban cualquier fila `running`/`interrupted`, mientras que `Admission.reserve` y `QueueRuntime._retry_occupancy` aplicaban la sem?ntica durable de ocupaci?n. Eso pod?a bloquear un retry por un job CPU interrumpido sin `JobAttempt` abierto o por una fila borrada.

## TDD

- **RED:** `test_other_active_ignores_orphan_or_deleted_interrupted_jobs` fall? porque `Recovery.other_active(...)` devolv?a `True` para las dos filas que deb?an ignorarse.
- **RED:** la primera preparaci?n de la prueba de retry fall? en el fixture sint?tico (`selected_provenance=None`); se corrigi? el fixture para reutilizar `failed_attempts`, que acredita un intento retryable real.
- **GREEN:** los dos casos focales pasan: `2 passed in 1.19s`.

## Cambio

Se extrajo `occupancy_filters(owner_id)` en `apps/server/app/queue/admission.py`. El predicado com?n exige propietario y fila no borrada, cuenta jobs `running`, intentos activos durables, jobs de soporte y jobs GPU `interrupted`, y excluye hu?rfanos CPU `interrupted`. Lo reutilizan admisi?n, runtime, retry y recovery.

## Regresi?n

- `test_dispatcher_retry.py` + `test_dispatcher_recovery.py`: **122 passed in 80.25s**.
- `test_dispatcher_admission.py` + `test_dispatcher_scanning.py`: **156 passed in 109.88s**.
- Ruff sobre los seis ficheros tocados: **All checks passed**.

T-04 sigue abierto: todav?a faltan la evidencia del engine GPU real, almacenamiento/recovery persistente y los gates formales de revisi?n/QA.
