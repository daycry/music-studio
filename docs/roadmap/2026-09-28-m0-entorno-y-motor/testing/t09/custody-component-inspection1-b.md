**Lente B: 0 Critical · 1 Important · 0 Minor.**

| Criterio de corrección | Resultado | Fichero:línea |
|---|---|---|
| Límites, índice cerrado y bytes exactos | ✓ Sin defecto encontrado | `benchmark_custody.py:483` |
| Referencias ajenas y rangos inválidos | ✓ Sin defecto encontrado | `benchmark_custody.py:524` |
| Deadline único y rechazo de resultados tardíos | ✓ Sin defecto encontrado | `benchmark_custody.py:450` |
| Revocación tras pérdida de identidad | ✓ Detecta la pérdida | `benchmark_custody.py:255` |
| Cierre exclusivamente de recursos propios | ✗ B-01 | `benchmark_custody.py:315` |
| Fixture confinada y limpieza de UUID propio | ✓ Sin defecto encontrado | `test_benchmark_custody.py:35` |

**B-01 — Important: `close()` cierra un handle ajeno si Windows reutiliza el slot de `_guard`.**  
En [benchmark_custody.py:315](../../../../../scripts/eval/benchmark_custody.py:315), el duplicado `_guard` se libera sin comprobar su identidad. Escenario: se pierde ese handle y Windows reutiliza su valor para abrir otro archivo. `verify()` detecta correctamente la discrepancia, pero el posterior `close()` cierra el handle ajeno. Además, omite cerrar el principal propio porque `CompareObjectHandles` devuelve falso y después descarta su valor.

**Reproducción propia nativa, sólo lectura, exit 0:** reutilización real del slot; handle ajeno válido antes de `close()` e inválido después; principal propio todavía abierto. Cero archivos creados o escritos; todos los handles de la sonda liberados al terminar.

Diff completo y sellos actuales cotejados. Los 59 PASS/1 skip y la cobertura recibida son evidencia previa; no reejecuté la suite. El hallazgo pertenece al componente individual y no altera el estado de T09/T13 ni la revisión formal pendiente.