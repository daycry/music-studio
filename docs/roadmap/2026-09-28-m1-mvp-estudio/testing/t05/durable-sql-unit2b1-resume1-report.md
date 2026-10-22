> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

U2b1 resume1: NEEDS_ROOT_DIAGNOSIS; entrega para revisión raíz A/B/C/D y QA independiente. Sin aceptación de unidad, T05 ni M1.

Baseline fresca única: {'cases': 1029, 'passed': 1025, 'failed': 1, 'errors': 0, 'skipped': 3}; exit 1. Mismos32 ficheros y1029 identidades: True. Sin excluir casos801 ni historia de migraciones.

Único cambio: cuatro expectativas exactas de HEAD0005→0006 autorizadas en tres tests. AST completo normalizado y bytes cualificados exactos; todos los demás asserts, funciones, parámetros y decoradores intactos. Los nueve archivos originales coinciden con la entrega anterior; los tres ajustes job_attempt anteriores siguen exactos. TDD n/a: actualización intencional de expectativas de esquema y harness/config privado.

Copias antes de ejecución exactas: True; scripts/init_env.py, scripts Python transitivos y fixtures archivados antes del primer test. Delta protegido original: []; delta guardias current: []. Otros deltas de entradas: ['apps/server/app/worker/custody_linux.py', 'apps/server/app/worker/custody_linux_supervisor.py', 'apps/server/tests/fixtures/worker_custody_linux_child.py', 'apps/server/tests/test_worker_native_linux_custody.py'].

La baseline histórica permanece804PASS8FAIL214ERROR3SKIP, exit1; los220 mismatches HEAD, el timeout801 UNKNOWN y el fallo del script privado conservan su clasificación. Repair aislado1PASS y51PASS propios anteriores no son baseline ni aceptación. Coberturas anteriores92/100/99/93 no se reutilizan. No union/extracción/promedio/exclusión de líneas.

Caso801 actual: [{'name': 'test_global_busy_gpu_negative_once_and_available_cpu_native[801]', 'JUnit_testcase_wall_seconds': '12.665', 'passed': False}]. El tiempo JUnit es duración del testcase completo, no medición del deadline de submitCPU. Un PASS actual no explica ni convierte en verde el timeout histórico; causa UNKNOWN.

Cobertura oficial Coverage.py de esta ejecución única, módulo WHOLE completo incluyendo la migración dinámica:

apps/server/app/migrations/cpu_publication_invariants.py: 279/303 = 92.07920792%; excluidas 0.

apps/server/app/migrations/versions/0006_cpu_publication.py: 27/27 = 100.00000000%; excluidas 0.

apps/server/app/models/__init__.py: 418/420 = 99.52380952%; excluidas 0.

apps/server/app/snapshots.py: 379/405 = 93.58024691%; excluidas 0.

SQLite/ORM/backup/procedencia/esquema reales. Descriptores, estados de engine y fixtures sintéticos declarados; no acreditan engines reales. Migraciones0001–0005 intactas; los ciclos head y hashDDL0004 permanecen en los tests originales de esta baseline. Sin nuevos cambios semánticos de modelos/invariantes/snapshots.

Historia TDD original y limitaciones de primer custody archivado incompleto (initial_relations JSON), incidentes de pytestcache compartido y repair previo intactas; no se fabrican capturas anteriores. La nueva corrida desactiva cacheprovider y usa rutas privadas desde antes de importar. Runtime actual del checkout, tests copiados actuales, no prototipo privado presentado como implementación.

Los deltas de custody_linux/supervisor/fixtureLinux/testLinux pertenecen al actor Linux activo autorizado; están clasificados en disjoint-input-delta-classification.json. Sus copias previas quedan preservadas, sin revertir ni congelar esa unidad ni atribuirle causalidad SQL.

Custodia nativa/cleanup UNKNOWN. Sin CPU2, filesystem publicación, FFmpeg, medios, beats, análisisImport, GPU, Docker, WSL, UI, E2E ni aceptación fullT05/M1. Ningún archivo de docs/ledger/ADR/Git/knowledge ni CLI reservado se ha escrito. Tokens/modelo/EUR/horasIA NULL.

Referencias completas: receipt.json; qualifier-ast-final.json; owned-sources-before-after.json; sourcecurrent12/; current-source-guards.json; copied-inputs-before-after.json; case-inventory-comparison.json; history-references.json; final-current/command.json/stdout-original.txt/stderr-original.txt/junit-original.xml/coverage-original.json y rawtrace. Inventario de todos los NONCLI excluye sólo cuatro reservados exactos de raíz y su propio inventario.

Fallos actuales preservados en baseline-failures-original.json; no rerun ciego ni ampliación de timeout. Diagnóstico/coordinación raíz siguiente, sin fix de código ajeno.
