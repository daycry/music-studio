**Lente D: sin hallazgos de rendimiento introducidos o reabiertos** en las diez fuentes del diff INLINE de esta unidad parcial T04.

Activación: `lente_d: true`; rutas `migrations` y patrones `n-plus-one`, `concat-en-bucle` y `bucle-anidado-con-llamada`.

| Criterio D | ✓/✗ | Evidencia y escenario de carga |
|---|---|---|
| N+1 | ✓ | `job_attempt_invariants.py:300` recorre dos operaciones y conjuntos fijos de tres fechas y tres contratos durante instalación. El test `test_job_attempt_schema.py:719` exige **29/29/32 SELECT para 20/200/405 intentos**, con colisiones por lotes de 400. |
| Bloqueos síncronos evitables | ✓ | No se incorporan esperas, red ni E/S síncrona dentro de funciones async. Publicación y restauración síncronas son anteriores al diff. |
| Trabajo repetido con impacto real | ✓ | Compilación y concatenación en `job_attempt_invariants.py:275` y `:300` tienen cardinalidad fija durante la migración. Las nuevas guardas de calendario (`:162`) añaden comprobaciones por fecha; no introducen crecimiento multiplicativo por número de intentos. |
| Complejidad con volumen del dominio | ✓ | Índice por `job_id` en `0005_job_attempt.py:15`; invalidación por identidades y membresías indexadas en `job_attempt_invariants.py:370`. No identifico un escaneo nuevo de toda la biblioteca por intento. |

**Gaps: Critical: 0 · Important: 0 · Minor: 0.** No aparece evidencia nueva que justifique reabrir los veredictos D anteriores.

Revisión exclusivamente estática del paquete INLINE completo, sin herramientas ni ejecución propia. Los conteos son evidencia aportada; no comprobé planes ni latencias. La tabla corresponde a **D** y no emite conformidad A. T04 mantiene sus ocho CA abiertos; aceptación técnica, wheel/Docker y QA independiente siguen pendientes.