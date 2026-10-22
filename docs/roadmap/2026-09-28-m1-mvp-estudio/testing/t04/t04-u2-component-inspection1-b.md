**0 Critical · 1 Important · 1 Minor.** Alcance: T04 U2, inspection1.

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Continuidad del despacho tras retry | **✗ Important — B-01** | [runtime.py:328](../../../../../apps/server/app/queue/runtime.py:328): el retry BF16→offload descarga el residente anterior durante `_preflight`, pero carga offload sin registrar el nuevo `Dispatcher.resident`. Tras el terminal, una petición BF16 queda rechazada en [dispatcher.py:118](../../../../../apps/server/app/queue/dispatcher.py:118), aunque el engine esté idle. El despacho no descarga ese modelo y el bloqueo persiste. La carga de recuperación en `runtime.py:156` tampoco registra el residente. |
| Conservación de la causa original | **✗ Minor — B-02** | [main.py:84](../../../../../apps/server/app/main.py:84): si `runtime.start()` falla y `runtime.close()` también falla durante cleanup, el lifespan propaga la excepción secundaria. La causa de startup queda únicamente en `__context__`, cambiando la excepción que recibe el llamador. |
| Cursor, efectos y terminal atómicos | ✓ Sin defectos adicionales identificados | `events.py:29` |
| Reserva concurrente y presupuesto de retry | ✓ Sin defectos adicionales identificados | `retry.py:97` |
| CancelAck conserva ocupación | ✓ Sin defectos adicionales identificados | `runtime.py:274`, `cancellation.py:56` |

**Pruebas propias:** sondas ejecutadas en memoria con dobles sintéticos sobre código actual. B-01 produjo `preflight offload=True`, residente `None` y siguiente BF16 `False`; el control con el mismo offload pasó. B-02 propagó `SECONDARY_CLOSE` y conservó `ORIGINAL_STARTUP` únicamente como contexto.

Freeze **13/13 exacto**. Cobertura oficial contrastada: ocho módulos completos ≥87,55 %, cero exclusiones; JUnit entregado: **324 PASS, 2 skips**. No reejecuté suites ni modifiqué archivos. No acredita aceptación completa de T04/U3.