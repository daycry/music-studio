**Lente D: sin hallazgos de rendimiento** introducidos o reabiertos en las nueve fuentes del diff INLINE.

Activación: `lente_d: true`; rutas `migrations` y patrones `n-plus-one` / `concat-en-bucle` en `job_attempt_invariants.py:278`.

| Criterio D | ✓/✗ | Evidencia y escenario de carga |
|---|---|---|
| N+1 | ✓ | `job_attempt_invariants.py:278` recorre dos operaciones y tres contratos fijos durante instalación. Para 20/200/405 intentos, el test aportado (`test_job_attempt_schema.py:719`) exige 29/29/32 SELECT y 2/2/3 lecturas de `job_attempt`; consultas por lotes de 400. |
| Bloqueos síncronos evitables | ✓ | El diff no incorpora `sleep`, red ni E/S síncrona en funciones async. Publicación y restauración síncronas son anteriores. |
| Trabajo evitable repetido con impacto real | ✓ | La compilación SQL y concatenación (`job_attempt_invariants.py:253`, `:278`) tienen cardinalidad fija durante la migración. La corrección de `ts` añade comprobaciones constantes; no introduce trabajo multiplicativo por volumen. |
| Complejidad con datos del dominio | ✓ | Índice por `job_id` en `0005_job_attempt.py:15`; invalidación por identidad y membresía en `job_attempt_invariants.py:345`. No identifico un escaneo nuevo de toda la biblioteca por intento. |

**Gaps:** Critical: 0 · Important: 0 · Minor: 0.

Revisión exclusivamente estática del paquete INLINE completo, sin herramientas ni ejecución propia; los conteos son evidencia aportada. La tabla corresponde a D, sin emitir conformidad A. T04 mantiene sus ocho CA abiertos; wheel/Docker y QA independiente siguen pendientes.