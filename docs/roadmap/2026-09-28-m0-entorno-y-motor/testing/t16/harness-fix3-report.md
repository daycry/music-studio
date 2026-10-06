# T-16 — exigir null explícito durante preflight

Fecha: 2026-10-06. Corrección privada de A-F2-01 detectado en la [revisión de fix2](harness-fix2-review-1.md). No cambia producto, imagen, entradas ni guardas históricas T-15.

El wrapper anterior aceptaba campos ausentes, job_id vacío y loaded vacío/false. Ahora exige que job_id y loaded existan y sean exactamente None antes de dispensar cap0 durante loading. Los restantes estados pasan por la guarda anterior. No se inventa un cap ni se modifica el margen o umbral del 95 %.

**RED:** `test_harness_fix3.py::test_preflight_requires_explicit_null_job_and_model` reprodujo seis casos, todos `DID NOT RAISE ValueError`, exit1 antes de cambiar el runner. Un aviso de configuración cache_dir al desactivar cacheprovider queda declarado; no interviene en los fallos.

**GREEN:** suite privada fix1+fix2+fix3, **26 passed**, sin avisos, exit0 en 0,80 s. Incluye el preflight HTTP real válido y el rechazo de las seis respuestas incompletas o con valores falsy. Snapshot anterior conservado con SHA `30f56aaf56cb0a9ff9831b92b4caa2a7025fa00fb3babb35f6c102867e66ec54`; [recibo nuevo](harness-fix3-receipt.json) congela nueve fuentes sin sobrescribir los anteriores.

Revisión intento 2 y QA pendientes. La limitación de threads obliga a declarar reutilización de contextos; no se afirma revisión fresca. No se ha vuelto a generar audio ni a cargar un modelo después del intento abortado. Los criterios GPU y escucha siguen abiertos, con calidad no aprobada. Medición estimada, consumo real desconocido; las ventanas concurrentes no se suman como horas IA.
