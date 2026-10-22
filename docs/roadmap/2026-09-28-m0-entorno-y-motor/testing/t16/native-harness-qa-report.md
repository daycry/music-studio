# QA independiente CPU — harness nativo T-16

Estado: **conforme CPU**, 14 pruebas pasan, cero fallos, un aviso de caché de pytest, exit 0. No hubo GPU, Docker, descarga, instalación, build, lectura directa de datos RAW ni impresión de letras/caption/token. No se modificó producto, configuración, Git, ledger, documentos públicos ni evidencia anterior. Despacho fresco, independiente de implementación y revisiones A+B+C+D.

## Alcance y resultados

| Comprobación | Evidencia nueva |
|---|---|
| Propagación real del bloque principal AST | Cuatro casos: CLI no cero, parada conservadora con CLI cero, unload false y éxito completo → exits **1/1/1/0**. Siempre se registra group, se limpia, se para y une monitor, se registran muestras y se cierra cliente antes de salir. quality_approved=false. |
| Preparación completa del candidato intacto | runpy de la fuente real sin --execute, SystemExit0; prepared_not_executed, una toma30s, imagen18d94fd, GPUfalse. Guardas de subprocess.run/Popen/check_output/call/check_call y HTTP sync/async: **0 llamadas**. Padre sin Torch antes/después. Lectura de entradas y entorno solo por el comportamiento original del harness; captura contiene únicamente el resumen sanitizado. |
| Frontera baseline real | Función baseline extraída de dependencia congelada: 1600 admitido y 1601 rechazado por GPU_BASELINE_ABOVE_CEILING. Subprocess doblado; no consulta GPU real ni Ollama. |
| Cleanup real y ownership | Seis casos: propio, owner incorrecto, imagen incorrecta, job ajeno, timeout stop, ausente. Los tres ajenos no generan stop/rm. El propio usa ID64validado; timeout exige rm --force por ese ID. |
| Delta y namespaces actuales | Reversión en memoria de cuatro literales reproduce baseline completo byte lógico exacto; AST3.11. Namespace runtime nativo dentro del workspace, owner/name nuevos, imagen inmutable actual y puerto127.0.0.1:18117. Cinco mounts/tres readonly; diagnóstico RO y salida propia RW. Sin shell=True. |
| Freeze previo/posterior | **44 archivos SHA256 idénticos**: baselinee6fd237e, candidato5a3bfa6f, cinco dependencias congeladas, nueve fuentes productivas, revisión/propuesta/QA históricas y sus evidencias relevantes. Mapas root-relative en freeze-before.json y freeze-after.json. |

Prueba completa única del directorio propio: 14 passed, 1 warning in0.41s. JUnit results.xml confirma14tests/0failures/0errors/0skips. El aviso PytestCacheWarning WinError5 afecta creación de caché propia; pruebas y JUnit terminaron correctamente. No se repitió ni se ocultó el aviso. No hubo errores de fixtures ni RED/TDD atribuido a esta QA.

## Comandos y puertas

Entorno para todos los comandos Python: `. ./scripts/env.ps1`, PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, `uv run --frozen --all-packages --no-sync`.

| Comando posterior al prefijo uv | Exit | Artefacto |
|---|---|---|
| python .cache/dev-cycle/t16/native-harness-qa/freeze.py before | 0 | freeze-before.json |
| pytest .cache/dev-cycle/t16/native-harness-qa/test_harness.py --basetemp=.cache/dev-cycle/t16/native-harness-qa/tmp -o cache_dir=.cache/dev-cycle/t16/native-harness-qa/pytest-cache --junitxml=.cache/dev-cycle/t16/native-harness-qa/results.xml -q | 0 | pytest-output.txt, results.xml, prepare-result.json |
| python <plugin>/agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md | 0 | ledger-output.txt: 0 incoherencias/7 avisos Changelog |
| python <plugin>/agent-kits/qa/coverage-check.py docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md docs/roadmap/2026-09-28-m0-entorno-y-motor/test-plan.md docs/roadmap/2026-09-28-m0-entorno-y-motor/spec.md | 0 | coverage-output.txt |
| python .cache/dev-cycle/t16/native-harness-qa/freeze.py after | 0 | freeze-after.json |

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). coverage-check **applies=false**: puerta no ejecutada, no «cobertura OK». Eximidos/listados: T-00,T-01,T-02,T-03,T-04,T-05,T-06,T-07,T-08,T-09,T-10,T-11,T-12,T-13,T-14,T-15,T-16,T-17,T-18,T-19; eximidos_exigidos=false; gwt_sin_id0, rutas_ui[], rutas_ui_origen{}, rutas_ui_degradado=null, marcador_no_canonico=null. Salida completa conservada. qa-gate/Playwright/E2E/cobertura porcentual del harness: n/a, sin resultados fabricados. PDF pendiente, sin setup ni instalación.

## Límites y siguiente paso

El producto actual conserva QA314 y cobertura64/68 como antecedentes: no se repitieron esas suites ni se atribuyen a esta QA. Tampoco se reprobaron las seis fuentes de imagen ya acreditadas; la configuración fija su digest18d94fd. Esta evidencia nueva acredita el harness en CPU con efectos sintéticos y preparación real bloqueada, no inferencia ni medidas de VRAM/pico/spill/calidad.

Antes de un job real: root debe serializar GPU respecto al trabajo ASR vivo y hacer preflight fresco de Ollama/baseline≤1600/healthidle-unloaded/identidad. Esta QA no ejecuta --execute ni autoriza saltar guardas. CA3 seis tomas90s y CA4 escucha siguen pendientes; T-16/M0 permanecen abiertos. Root conserva publicación y ledger. Sin consultas MCP/conocimiento ni memoria externa.
