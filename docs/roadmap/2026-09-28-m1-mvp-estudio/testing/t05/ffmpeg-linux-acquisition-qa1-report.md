> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA independiente: adquisición FFmpeg Linux

**SCOPED_PASS** acotado. Baseline fresca única: 58 PASS, 0 fallos; exit 0. Módulo productivo completo actual: 334/379 = 88.12664908 %, 0 exclusiones. Datos originales en `.coverage`, `coverage.json`, `junit.xml` y comandos/stdout/stderr por ejecución. Sin unión ni media de trazas.

`--check` real con lock oficial actual: exit 0; 70 archivos del payload y caché SHA/tamaño idénticos antes/después. Archivo fijado 137863452 bytes, SHA-256 2d41cbea0ca1a15029b638330740f78d6f5aeb062355bf425433fc938705350a. No descarga ni ejecución de los binarios.

10 fuentes/config/helpers acotados congelados antes y cotejados después: estables=True. Producto y tests actuales coinciden con las copias finales de implementación: {'scripts/fetch_ffmpeg_linux.py': True, 'tests/test_fetch_ffmpeg_linux.py': True}. AST contra preimágenes en `implementation-custody.json`; tests originales, decoradores y parámetros incluidos. Fixtures definidas por los tests congelados antes de ejecutar; tar/pin TESTDOUBLE generados archivados por el mecanismo existente bajo `fixtures/`. No nuevos tests ni cambios de producto.

B01: fallos inyectados de escritura de `.owner` OSError/KeyboardInterrupt sobre filesystem nativo Windows verifican ausencia del lock vacío propio y conservación de fuente; entradas/marcador/identidad/custodia desconocida preservados. B02: negativos de ambos binarios y positivos plataforma/modo son stat/plataforma TESTDOUBLE; no equivalen a Linux nativo. Transporte y mutaciones de identidad también TESTDOUBLE. JUnit original conserva los 58 casos.

TDD n/a: QA READONLY de implementación existente. RED históricos no repetidos. Copias independientes por RED de helper ausentes: limitación de custodia de implementación conservada, sin reconstrucción retrospectiva.

Sólo mapa asignado comparado: no afirmación de estabilidad global de apps/scripts/tests ni de cambios autorizados U2a/T08/docs root. Ownership producto/tests/docs/Git/locks = []. Escrituras únicamente privadas de esta fase. Hijos directos medidos con PID/wait/exit; descendientes no medidos UNKNOWN. Modelo/tokens/EUR/horasIA NULL.

Linux nativo, ABI, licencia binaria, Docker, integración audio, E2E/media, T05/M1 y aceptación final siguen pendientes de root. Sin UI/GPU/PDH/WSL/Ollama/red/instalación/subagentes/knowledge. Informe y recibo son originales de QA; ledger/docs/Git/meter/aceptación quedan exclusivamente en root.

Preservación confirmada: las 25 funciones originales de tests tienen AST íntegro idéntico (incluye cuerpos anidados, assertions/decoradores/parámetros); los 45 casos anteriores están presentes en el JUnit actual y pasan. `old-tests-preservation.json` evita colisiones de nombres anidados del índice AST plano exploratorio de `implementation-custody.json`; ese índice plano no permite atribuir cambios al helper `fail`.

Custodia auxiliar: finalizador PID27508 esperado con WaitForExit, pero ExitCode retornó NULL (UNKNOWN), conservado en finalize-command.json; no se infiere exit0 del stdout ni del shell. Baseline/export/check conservan exit0 medido con Popen.wait. Workspace privado de tests vacío al terminar; fixtures originales archivadas conservadas. No rerun. Inventario cotejado antes de este añadido: 211 archivos, cero diferencias; regenerado para incluir cierre.
