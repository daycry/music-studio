# T-16 — revisión de fix2, intento 1

Fecha: 2026-10-06. Lentes A+B+C+D. El despacho fresco fue rechazado por límite de threads. A reutilizó el contexto anterior de QA T-19 y B el de revisión T-17; ninguno implementó fix2. C y D se ejecutaron secuencialmente en el mismo contexto de B. Esta revisión no acredita cuatro revisores independientes con contexto fresco. El selector activó C por `exec` y D por ruta cache/sleep; esos disparadores eran anteriores al cambio.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| CA1/2 de producto | Conservados | Antecedentes CPU del ledger, sin repetir 430 tests |
| Preflight HTTP real loading/job=null/loaded=null/cap0 | Conforme | test_harness_fix2.py:29; reproducción sin hijo ni job aceptado |
| Exención solo ante campos explícitos null | No conforme | run-comparison.py:55; campos ausentes o falsy también aceptados |
| Medidas GPU inválidas y cap ausente tras carga/job | Conforme en casos probados | test_harness_fix2.py:62,66 |
| Umbral conservador 95 % | Conforme | Delegación legacy y test_harness_fix2.py:71 |
| H1–H4, alcance y constitución | Conservados/conforme | Diff acotado; doce regresiones anteriores incluidas |
| Fuentes, snapshot y RED/GREEN | Conforme | Hashes comprobados independientemente; primer fixture inválido excluido |
| Seguridad introducida/reabierta | Sin hallazgos | Health no alimenta código, comandos ni rutas; exec/whitelist históricos intactos |
| Rendimiento introducido/reabierto | Sin hallazgos | Validación O(1), sin nueva E/S ni bucles |
| CA3/4 GPU y escucha | Pendientes | Cero tomas; unload del intento abortado no confirmado |
| Interop/OpenAPI/cobertura de producción | No aplica | Corrección de arnés privado, sin cambios de producto |

**A-F2-01 — Important:** `run-comparison.py:55` equipara ausencia y valores vacíos con null mediante `not health.get(...)`. Una respuesta loading sin job_id/loaded o con job_id vacío/loaded={} devuelve None y omite el rechazo. La guarda debe exigir presencia y null explícito de ambos campos. B no encontró defectos en sus escenarios; A aporta esta reproducción adicional, verificada por el orquestador.

A ejecutó 20 tests con un aviso de configuración cache_dir al desactivar cacheprovider; B ejecutó 20 con un aviso de permisos al guardar caché. Ambos exit0. No se presentan como ejecuciones sin avisos. C/D solo lectura/diff/AST, sin repetir tests. Ningún revisor ejecutó Docker, GPU, modelos, música ni escribió producto o ledger.

El fix2 queda sustituido por [fix3](harness-fix3-report.md). Los recibos y el snapshot históricos se conservan; revisión del arreglo en intento 2 y QA independientes pendientes. T-16 sigue en-progreso.
