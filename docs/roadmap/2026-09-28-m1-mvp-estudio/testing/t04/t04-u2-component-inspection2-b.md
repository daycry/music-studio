**0 Critical · 2 Important · 0 Minor.** Alcance: T04/U2, inspección de componente 2.

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Cierre del lector al cancelar | **✗ Important — B-01** | [runtime.py:308](../../../../../apps/server/app/queue/runtime.py:308): cancelar mientras `next(pages)` sigue ejecutándose en un worker provoca que otro worker llame simultáneamente a `pages.close()`. Lanza `ValueError: generator already executing`, sustituye la cancelación y deja sin ejecutar el cierre del iterador. |
| Prioridad entre retries y jobs nuevos | **✗ Important — B-02** | [runtime.py:431](../../../../../apps/server/app/queue/runtime.py:431): con GPU libre, un fallo `batch` reintentable y un job `interactive` en cola, `_retry()` reserva y envía primero el batch. El despacho posterior encuentra el carril ocupado y bloquea el interactive. El orden por prioridad del selector de retries no compara ambas poblaciones. |
| Residencia tras carga confirmada | ✓ Sin defectos adicionales identificados | `runtime.py:244` |
| Validación positiva fresca y reserva durable | ✓ Sin defectos adicionales identificados | `runtime.py:349`, `retry.py:140` |
| Conservación de la causa de startup | ✓ Sin defectos adicionales identificados | `main.py:89` |

**B-01 reproducido en memoria:** métodos actuales `_retry`/`dbcall`, executor real y generador bloqueado sintético. Resultado: `ValueError`, cierre no ejecutado e iterador todavía abierto. No acredita una fuga SQLite nativa. **B-02 es evidencia estática**, sin prueba funcional ejecutada.

Freeze de cinco fuentes y snapshots de entrega **87/87 exactos**. Cobertura recalculada desde la traza oficial: main **96,12 %**, retry **94,12 %**, runtime **89,35 %**, cero exclusiones. JUnit entregado: **386 PASS, 2 skips**; sin reejecutar suites ni modificar archivos. No concede aceptación completa de T04/U3.