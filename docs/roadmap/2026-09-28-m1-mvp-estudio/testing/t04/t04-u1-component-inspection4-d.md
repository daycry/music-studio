**Sin hallazgos: 0 Critical · 0 Important · 0 Minor.**

Alcance: los tres archivos de `inspection4/scope.diff`, cambios sin commit contra HEAD de la fixture aislada; no existe un rango literal `<base>..HEAD`. Activación: rutas `queue` y `await` en bucles.

| Criterio | Resultado | Evidencia fichero:línea y carga |
|---|---|---|
| N+1 de ocupación GPU | ✓ D3-01 corregido | `dispatcher.py:58,153`: observación compartida entre páginas. Con 200/400/2001 candidatos y GPU ocupada, los perfiles registran **1 SELECT por despacho**, frente a 200/400/2001 anteriores. |
| E/S síncrona introducida en el loop | ✓ | `dispatcher.py:59,194`: consulta de screening y reserva mediante `to_thread`; **0 SELECT de screening en el loop** en las tres cargas. |
| Trabajo evitable repetido | ✓ | `dispatcher.py:169,194`; `admission.py:223,258`: no identifico repetición nueva con degradación acreditada. Se conservan las revalidaciones del seleccionado. |
| Complejidad con volumen | ✓ | `dispatcher.py:155,163`: caché por despacho, compartida entre páginas; el diff no introduce crecimiento superlineal identificado. |

Comprobación propia de lectura: tres fuentes congeladas, 42 archivos del manifiesto final y 26 protegidos coinciden por hash. Contrastados comandos, UTC y JUnit: **206 PASS**; cobertura oficial completa admission **94,58 %**, dispatcher **88,28 %**, cero exclusiones.

Los perfiles son evidencia entregada de SQLite nativo con catálogo sintético; no ejecuté suites ni sondas funcionales. Sus pausas de heartbeat —hasta **0,623 s**— impiden afirmar una garantía de latencia, pero no acreditan una regresión introducida por este diff. T04/U2/U3 y QA independiente permanecen pendientes.