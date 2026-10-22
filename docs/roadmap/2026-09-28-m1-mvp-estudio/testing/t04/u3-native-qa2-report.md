> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA2 independiente U3 actual

SCOPED_CURRENT_NATIVE_QA_PASS

Caso exacto de confinamiento: 1 PASS con fixture original de conftest.py, helper workspace original y STUDIO_TEST_ROOT superficial propio. Target de siete padres observado fuera del repositorio; únicamente validación Settings, sin crear/escribir ese destino.

Baseline nuevo único: 506 PASS, 2 SKIP, 0 FAIL, 0 ERROR. JUnit/argv/UTC/stdout/stderr y datos originales de cobertura propios; ninguna unión histórica.

Cobertura WHOLE por módulo, cero líneas excluidas:

- `apps/server/app/queue/chains.py`: 82/83 = 98.80 %.
- `apps/server/app/queue/references.py`: 120/122 = 98.36 %.
- `apps/server/app/queue/manual_retry.py`: 92/99 = 92.93 %.
- `apps/server/app/queue/admission.py`: 213/226 = 94.25 %.
- `apps/server/app/queue/dispatcher.py`: 147/164 = 89.63 %.

94 fuentes actuales copiadas antes del primer test; cierre ampliado 113 paths. 80 protegidos; 22441 históricos comprobados. Drift fuente/histórico 0/0. Las cinco fuentes de producción conservan los hashes de QA1 repair2. Copias, AST94, prefijos SHA, contenido y directorios inventariados. Seis vecinos originales con AST/assertions/decorators/parameters preservados; test de referencias privado sólo cambia el destino del recibo SQL de STUDIO_TEST_ROOT a STUDIO_QUEUE_TEST_ROOT. Ningún override tmp_path ni cambio global.

Tres baselines QA1 conservados: 506PASS2SKIP con cierre inicial89/94 incompleto; dos505PASS1FAIL2SKIP por ancestro privado dentro del repositorio. No rescate de trace viejo. Inspection2 A/B/D existente revisada readonly; counters y adjudicación reservados a root, sin nueva lente.

SQLite0005/WAL y dos conexiones concurrentes reales; prioridad/FIFO, snapshot400/400/1 finito/detached, winning durable attempt/globaloutputIndex, N/seed/request originales, owner/foreignsong/ACK/fakepost/cancel/ready negativas y revalidación writer sin descriptor confiado de otra TX cubiertos por los casos actuales. Retry tras gen succeeded y gen failed+lastDONE exige fallo post propio autenticado y conserva historial/takes/request.

SELECT nativos realmente ejecutados: 400=11 y64=6; statements originales en native-query-counts.jsonl. 2404/132 son RED históricos revisados, no reejecutados. El caso400 usa tres takes ready compartidos, no400 masters; engine/artifacts/post sintéticos/policy. Sin afirmación de latencia, GPU ni T05 listo.

Finalizers observados 351, pools ['0']; 70 UUID superficiales con stat/marker/token previo, closure antes de teardown y ausencia/registro liberado después. Root superficial propio retenido con marker; DBs y evidencia propia retenidas e inventariadas. Wait/reap directo real; FILETIME/Job/cursor handles UNKNOWN. Sin borrado ajeno.

agents/qa.md y qa-gate leídos: UI/Playwright/gate global n/a por alcance CPU autorizado; no results.json inventado ni modificación del test-plan. TDD n/a QA; RED original revisado readonly. Dos skips por privilegios Windows conservados; su frase histórica sobre Docker Linux no acredita una prueba Linux en esta QA. Dos suplementos HTTP MockTransport U2 históricos no repetidos.

U3 pendiente de aceptación root; T04 ocho CA, T05 real, I01, E2E/M01/Git/calidad física pendientes. Sólo fase QA2 y namespace superficial autorizado escritos; producto/tests/esquema/contratos/locks/docs/históricos readonly. Sin GPU/UI/red/Docker/WSL/Ollama/instalaciones/subagentes/knowledge/meters. Modelo/tokens/EUR/horasIA NULL; meter exclusivo root.

Comprobación posterior independiente: datos originales de coverage normalizados a statements contra las copias previas exactas de los cinco módulos y JSON oficial concordantes. 366 BD retenidas leídas con SQLite nativo mode=ro: todas WAL/0005 y conexión cerrada. Inventario anterior QA1 de 6613 archivos exacto; auditoría root original conservada.

Incidencias privadas de auditoría conservadas: el primer suplemento y el primer audit usaron erróneamente el mapa histórico94 para buscar chains/manual_retry/references. Las ocho fuentes U3 ya estaban en el cierre ampliado113 y sus copias ANTES del test. Reparación sólo del lector privado: audit-fix1 y suplemento-fix1, originales preservados; cero nuevas ejecuciones de tests. No se cambia ni rescata la traza oficial actual.

Contabilidad: preparación/targeted/baseline/inspect/audit/suplementos/publicación/inventario originales en CLI reservado del padre; hijos capturados en actor-command-accounting.json. El primer audit invocado directamente por herramienta terminó exit1 (session42032); PID/UTC nativos no capturados separadamente: UNKNOWN, stdout/stderr originales en CLI del padre. No se reconstruyen nacimientos desde mtime ni se sella CLI activo.
