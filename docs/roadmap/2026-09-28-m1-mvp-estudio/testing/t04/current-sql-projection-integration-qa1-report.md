> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

QA independiente actual: **FAILED**, una única ejecución completa, sin repetición ni cambios de producto/tests. No aceptación de unidad/tarea/hito.

1055 casos reales: 1051 PASS, 1 FAIL, 0 ERROR, 3 SKIP; wait exit 1, PID 13292, UTC 2026-10-09T03:38:20.867250+00:00 → 2026-10-09T03:45:57.301078+00:00. Resultado original en baseline/stdout-original.txt, stderr-original.txt, junit-original.xml y datos coverage-original/coverage-original.json.

Único fallo: test_persistence_t02.py::test_schema_populated_migration_cycle, CommandError «No 'script_location' key found in configuration». Error del arnés después de colección: qa_prepare omitió apps/server/alembic.ini al cambiar el cwd a inputs privados. La ruta copiada no existía; la configuración actual original sí contiene script_location. No RED causal de producto, ni prueba del ciclo downgrade/upgrade. Se conserva history; harness-repair-post contiene copia POST de la configuración y mínima adaptación estructural para futura autorización, sin tocar baseline sellada y sin rerun.

32 archivos exactamente seleccionados por selected-original32.json. Las 1029 identidades antiguas se conservan: True; 26 casos nuevos, total observado 1055. AST de funciones/clases antiguas, parámetros/decoradores/asserts conservado; test_dispatcher_retry byteexact. HEAD0006 existente intacto, fixtures legacy0005 sin editar.

Original test_global_busy_gpu_negative_once_and_available_cpu_native[801]: [{'classname': 'apps.server.tests.test_dispatcher_retry', 'name': 'test_global_busy_gpu_negative_once_and_available_cpu_native[801]', 'seconds': 8.574, 'status': 'passed', 'message': None, 'detail': None}]. Temporizador original 10s intacto; tiempo JUnit es tiempo del caso, no tiempo CPU submit. Sin observador nuevo. Causa SQL antigua UNKNOWN, ninguna afirmación de mejora medida ni pares controlados.

Cobertura WHOLE oficial de esta única traza fallida; line-only como la receta original, cero exclusiones. Se conservaron todos los targets antiguos y se añadieron admission/resolver. No trace union, extracción, promedio ni gate de ramas inventado.

| Fuente | WHOLE oficial | Excluidas |
|---|---:|---:|
| `apps/server/app/migrations/cpu_publication_invariants.py` | 92.079208% | 0 |
| `apps/server/app/migrations/versions/0006_cpu_publication.py` | 100.000000% | 0 |
| `apps/server/app/models/__init__.py` | 99.523810% | 0 |
| `apps/server/app/queue/admission.py` | 94.893617% | 0 |
| `apps/server/app/queue/resolver.py` | 92.727273% | 0 |
| `apps/server/app/snapshots.py` | 93.580247% | 0 |

Los seis módulos cambiados superan80: True. Todos los otros archivos instrumentados y sus porcentajes (incluidos0001/0002 inferiores80 por no ejecutar downgrade tras error) constan en current-coverage-source-map.json. Esto no da aceptación a la baseline fallida. Comparación legacy4 de instrumentación declarada allí, dos extras debidos al código actual cambiado.

8397 entradas precopiadas; 0 copias divergentes y 0 deltas de fuentes observados. Mapas own observados separados del mapa Root, nunca sobrescrito. Scripts/init_env.py incluido antes de Popen. Fuentes app/tests/contracts/helpers y entorno gestionado archivados. La captura NO es exhaustiva: ini omitido; cierre de imports transitorios/unloaded UNKNOWN. End-loaded gaps físicos observados: 0. 257 aliases del intérprete gestionado (3.12 → 3.12.14) cotejados por ruta física y SHA/bytes con precopia; original lexical comparison preservado. TCB Windows/kernel/cargador DLL/PowerShell/filesystem explícito. Autenticación/main actual sólo queda parcialmente ejercitada por esta baseline; productor307 no aceptado aquí.

Actores previos terminales documentados; observación de procesos previa sin coincidencias activas, no prueba global de todos los descendientes. Custodia OS de descendientes no observados UNKNOWN. Sólo tests CPU con contrato/mock existente, no prueba GPU/música. Tres skips Windows originales preservados, ninguna prueba Linux nueva. Conteos existentes preservados en native-query-counts.jsonl y existing-test-schedule-artifacts.json, sin nuevo workload/observador.

Sólo salida privada; ledger/docs/ADRs/Git/aceptación reservados a Root. TDD n/a verificación independiente. Modelo/tokens/EUR/horasIA NULL. I01/fullworker/SSE/CLI/calidad/E2E y tarea/hito siguen abiertos. Revisión A/B/C/D limpia no sustituye esta QA fallida.
