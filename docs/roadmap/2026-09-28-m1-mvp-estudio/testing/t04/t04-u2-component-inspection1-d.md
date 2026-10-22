**Dos hallazgos Important** en el diff congelado de U2. Evidencia estática; sin benchmark ni ejecución de carga del revisor.

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| N+1 | ✗ **D-01 Important** | [retry.py:55](../../../../../apps/server/app/queue/retry.py:55): con **200 jobs fallidos**, ejecuta **201 SELECT por ciclo**, aunque todos sean no reintentables o hayan agotado el presupuesto. Consulta el intento individual antes de comprobar `eligible`. |
| Trabajo repetido en bucle | ✗ **D-02 Important** | [runtime.py:285](../../../../../apps/server/app/queue/runtime.py:285): con **200 retries elegibles para un único engine ocupado**, cada candidato vuelve a observar el backend, invalida su catálogo y crea otro resolver. Ejecuta al menos **600 GET health y 400 GET models por ciclo**, aunque todos se descarten por la misma ocupación. |
| Bloqueos síncronos | ✓ Sin hallazgo adicional | [dispatcher.py:28](../../../../../apps/server/app/queue/dispatcher.py:28): las operaciones SQLite modificadas pasan a ejecución fuera del event loop. |
| Crecimiento con el volumen | ✗ **D-01 / D-02** | [runtime.py:355](../../../../../apps/server/app/queue/runtime.py:355): el despacho normal espera a que termine `_retry()`. El coste crece con los fallos históricos y los retries pendientes, incluso cuando no puede admitirse ninguno. |

**D-01:** el histórico de fallos permanece dentro de la búsqueda en cada ciclo —espera nominal de 100 ms—. Conviene seleccionar jobs e intentos mediante una consulta conjunta y aplicar antes los filtros de presupuesto, fecha y elegibilidad.

**D-02:** en el escenario indicado, con **10 ms por respuesta HTTP**, las 1.000 peticiones secuenciales añaden aproximadamente **10 segundos antes del despacho normal**, incluidos jobs CPU de otro engine disponible. Esa duración es una estimación para la latencia indicada, no una medición. Conviene reutilizar observaciones de descarte por ciclo y conservar la validación fresca al admitir un candidato.

Selector comprobado: activación por rutas `queue` y `await-en-bucle`. Fuentes actuales coinciden con el freeze; cobertura oficial por módulo **87,55–96,59 %**, cero exclusiones. La traza entregada registra **324 PASS y 2 skips**; no se repitió la suite. Alcance limitado a U2, sin aceptación global de T04.