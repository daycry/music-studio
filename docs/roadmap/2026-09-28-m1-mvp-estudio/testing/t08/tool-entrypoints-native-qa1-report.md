> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA independiente de entrypoints T08

**SCOPED_CURRENT_NATIVE_QA_PASS**. Una única línea base actual: 65 PASS, 0 fallos, 0 errores, 0 skips. Archivo canónico de entrypoints más los cuatro helpers exactos del comando final-current2; sin copias ni alteraciones de tests. Cobertura oficial de TODO `scripts/pnpm.py`: 159/165 = 96.363636 %, 0 exclusiones, una sola traza fresca `.coverage-current` y JSON original. No unión histórica, media ni cobertura de ramas.

Fuentes actuales producción750bd7/tests06836c, freeze privado antes del lanzamiento; mapas protegidos antes/después exactos (27 rutas) y tools oficiales exactos (2935 archivos) verificados independientemente dos veces. 27 funciones anteriores con AST completo, asserts/decoradores/parámetros exactos. Fuentes originales y wrappers archivados en `sources-before/`; helpers/runner incluidos. Pruebas canónicas directas, sin profile/site injection ni parche QA de producción. La instrumentación binaria es el fixture original vigente.

Windows nativo: publicación simultánea y escritor parcial controlados mediante barreras de tests sobre filesystem real; ambos inicializadores éxito. Ganador válido y rechazos de bytes ajenos/parciales/hardlink/directorio/junction; temporal sustituido preservado. Integración con tools oficiales, argumentos literales y exit37. Recibos originales `native-byte-receipts/`, `native-receipts/`, `race-receipts/` y recibos de nested según fixture conservan fuente/argv anteriores y stdout/stderr. Controles sintéticos/policy/mocked del CLI se distinguen de procesos Windows y no acreditan ejecución real de todas las políticas. PID/UTC/UUID sólo cuando observados; FILETIME/Job y metadata no capturada UNKNOWN. No reconstrucción por mtime ni afirmación de DEVNULL conocido.

Herramientas Node22.23.2/pnpm9.12.0 existentes y verificadas; ningún install/CFS/resolución/red/deps/globalcache. `.cache/web-runtime` mutable sólo en proyectos fixture propios; store vacío no acredita bootstrap offline limpio. Teardown usa helper canónico con marcador y registro de propiedad, identidad y padres; namespace propio vacío (`cleanup.json`), sin borrar namespace ajeno.

Custodia del último actor comparada una vez con su inventario NONCLI (`predecessor-custody.json`), sin rehash masivo de81081 archivos históricos. Parity installed-terminal leído:482artefactos/27919payloads sin diferencias, evidencia histórica, no una nueva certificación CFS. Predecesor legal609/23pins y portableQA106PASS5Windows skips preservados, sin rerun. Linux/Bash unsupported negativos y anteriores pruebas Docker cualificados históricos, no prueba Linux nueva.

Root canonical gen real ya acreditado en `t08-canonical-gen-root1/receipt.json`: source12/TypeScript byteexact, sólo leído; esta QA no escribe el archivo generado ni repite gen canónico. Los positivos gen aquí son fixtures/sentinels con tools oficiales. Revisión3 A/B y adjudicación0gaps leídas, sin reejecutar reviewers.

Historia cualificada: primer unit parent1/CHILDexitUNKNOWN por metadata collision; expectativa previa stderr UTF corregida; error de binding PowerShell previo a Python NO RED; provisional BLE001 freeze no corresponde a current-final2. RED race/partial anterior sólo leído, no ejecutado. QA forward no certifica historia TDD perfecta.

Ruff check y format --check dirigidos y ledger-lint readonly se conservan con salida original. Global test-plan existente de UI futura; E2E/qa-gate/browser/URL real n/a para este componente CPU, no hay prueba de navegador. Resultado de coverage-check global:

```text
⚠️  T-00: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)

{"applies": true, "defined": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "referenced": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "broken_refs": 0, "tasks_sin_cobertura": ["T-00"], "tests_sin_referencia": [], "gwt_cubiertos": [], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}


```

No aceptación T08/M1/calidad/UX/build/Docker/LinuxNode/Playwright/GPU. Criterios UI y checklist manual M-02 continúan pendientes en el plan. TDD n/a: QA independiente sólo lectura. Root exclusivo ledger/Git/docs/decisiones/meter. Actores dinámicos T09/queue disjuntos fuera de la afirmación de custodia.

Comandos reales (stdout/stderr binarios, argv/UTC/PID/exit en accounting y recibos):

- `['/.venv\\Scripts\\python.exe', '-B', '-m', 'coverage', 'run', '--rcfile=/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\coverage.ini', '-m', 'pytest', 'tests/test_web_tool_entrypoints.py', 'tests/test_fetch_web_tools.py::test_private_environment', 'tests/test_fetch_web_tools.py::test_environment_foreign_config_preserved', 'tests/test_fetch_web_tools.py::test_package_manager_mismatch', 'tests/test_fetch_web_tools.py::test_prepared_check_only_offline', '-q', '-o', 'cache_dir=/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\pytest-cache', '--basetemp=/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\pytest-base', '--junitxml=/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\baseline.xml']`: exit 0; 2026-10-08T03:39:21.489950+00:00 → 2026-10-08T03:45:09.493168+00:00.
- `['/.venv\\Scripts\\python.exe', '-B', '-m', 'coverage', 'json', '--rcfile=/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\coverage.ini', '-o', '/.cache\\dev-cycle\\m1\\t08-tool-entrypoints-native-qa1\\coverage-current.json']`: exit 0; 2026-10-08T03:45:09.496176+00:00 → 2026-10-08T03:45:09.869845+00:00.
- `['/.venv\\Scripts\\python.exe', '-B', '-m', 'ruff', 'check', 'scripts/pnpm.py', 'tests/test_web_tool_entrypoints.py']`: exit 0; 2026-10-08T03:45:09.870853+00:00 → 2026-10-08T03:45:10.013271+00:00.
- `['/.venv\\Scripts\\python.exe', '-B', '-m', 'ruff', 'format', '--check', 'scripts/pnpm.py', 'tests/test_web_tool_entrypoints.py']`: exit 0; 2026-10-08T03:45:10.014273+00:00 → 2026-10-08T03:45:10.146936+00:00.
- `['/.venv\\Scripts\\python.exe', '-B', '<plugin>/agent-kits\\shared\\ledger-lint.py', 'docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md']`: exit 0; 2026-10-08T03:45:10.148935+00:00 → 2026-10-08T03:45:10.261555+00:00.
- `['/.venv\\Scripts\\python.exe', '-B', '<plugin>/agent-kits\\qa\\coverage-check.py', 'docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md', 'docs/roadmap/2026-09-28-m1-mvp-estudio/test-plan.md', 'docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md']`: exit 0; 2026-10-08T03:45:10.262486+00:00 → 2026-10-08T03:45:10.357404+00:00.

Modelo/tokens/EUR/horasIA reales NULL; peso estimado1,5. Inventario NONCLI final excluye únicamente los cuatro nombres top-level reservados y su propio inventario; no se sella un CLI activo.
