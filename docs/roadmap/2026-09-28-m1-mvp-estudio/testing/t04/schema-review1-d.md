**Lente D: sin hallazgos de rendimiento** en el diff de las ocho fuentes de la unidad parcial T04.

Activación: rutas `migrations` y heurísticas `n-plus-one` y `concat-en-bucle` en `job_attempt_invariants.py:266`.

| Criterio D | Resultado | Evidencia y escenario |
|---|---|---|
| N+1 introducido | ✓ | `job_attempt_invariants.py:266`: dos operaciones y tres contratos fijos; no itera por datos del usuario. El test `test_job_attempt_schema.py:719` exige 29/29/32 SELECT para 20/200/405 intentos, con lecturas de colisiones por lotes de 400. |
| Bloqueos síncronos evitables | ✓ | No se añaden esperas, llamadas de red ni ejecución síncrona dentro de una función async. La publicación y restauración síncronas ya existían. |
| Trabajo repetido con impacto por volumen | ✓ | `job_attempt_invariants.py:244–278`: compilación y concatenación durante instalación, con cardinalidad fija. La validación contractual por fila recorre su payload; no aparece un crecimiento multiplicativo por número de intentos. |
| Complejidad respecto al volumen del dominio | ✓ | La relación incorpora índice por `job_id` (`0005_job_attempt.py:15`); los selectores de invalidación usan identidades y membresías indexadas (`job_attempt_invariants.py:333`). No se introduce una proyección de toda la biblioteca por cada intento. |

**Gaps:** Critical: 0 · Important: 0 · Minor: 0.

Revisión exclusivamente estática del paquete inline; no ejecuté tests ni comprobé planes o latencias. Los resultados incluidos son evidencia aportada. La tabla corresponde a D; no emito conformidad A ni aceptación técnica. T04 conserva sus ocho CA abiertos y wheel/Docker/QA siguen pendientes.