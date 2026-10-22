**1 Important · 0 Critical · 0 Minor.**

Alcance: `scope.diff` de inspection3, cuatro ficheros; seis fuentes cotejadas con el freeze, todas exactas. El alcance capturado contiene cambios sin commit, no un rango literal `<base>..HEAD`. Lente activada por rutas `queue` y `await` en bucles.

| Criterio | Resultado | Evidencia y escenario de carga |
|---|---|---|
| Consultas repetidas y bloqueo síncrono | **✗ Important D3-01** | [dispatcher.py:55](../../../../../apps/server/app/queue/dispatcher.py:55) llama directamente a [admission.py:378](../../../../../apps/server/app/queue/admission.py:378) por cada candidato GPU. Con **un job GPU activo en BD y 400 candidatos dirigidos a otro engine observado libre**, ejecuta **400 SELECT de la misma ocupación**, en vez de una observación compartida para descartar durante ese despacho. |
| N+1 de dependencias | ✓ | `admission.py:197`: mapa agrupado por página de hasta 400 IDs. Sin hallazgo adicional. |
| Hash y salud por candidato ocupado | ✓ | `dispatcher.py:163`, `resolver.py:153`: screening previo al hash y observaciones compartidas. D2-03 corregido según evidencia de entrega. |
| Complejidad y trabajo repetido restantes | ✓ | Sin otro hallazgo independiente acreditado con carga concreta. |

**Prueba propia de D3-01:** ejecuté `_dispatch_page`, `_screen` y `Admission.gpu_active` actuales sobre SQLite real **en memoria**, con rutas, salud y candidatos inyectados:

| Candidatos | SELECT reales | Tiempo sin ceder al event loop | Heartbeats durante el recorrido |
|---:|---:|---:|---:|
| 200 | 200 | 33 ms | 0 |
| 400 | 400 | 65 ms | 0 |
| 2001 | 2001 | 296 ms | 0 |

Los tiempos corresponden a esta sonda, sin HTTP, GPU ni integración completa. Conviene compartir la observación negativa de ocupación durante el despacho y mantener la revalidación vigente antes de reservar.

Evidencia documental contrastada, sin reejecutar suites: **189 PASS** en JUnit; cobertura completa admission **93,37 %**, dispatcher **86,03 %**, resolver **92,64 %**, todas con **cero exclusiones**. Esta revisión no acredita aceptación íntegra de T04.