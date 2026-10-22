# B01 — congelación de identidad antes de I/O

Corrección concreta lista para revisión fresca y QA independiente; no aceptación del componente, tarea o calidad.

`fold_originals` copia por separado intentos y anclas del llamador antes de comparación y cualquier I/O. `transition` copia sólo intento, contexto y record del delta antes de validar. No copia ni recorre `head/history`; mantiene los enlaces inmutables y O(delta). El fold offline permite la copia del historial completo. Cambio limitado a los dos ficheros asignados.

Hipótesis probada: el recibo mutable conserva un alias después de verificar identidad y se congela sólo al terminar; mutar el PID al leer request.json publica otra identidad. La regresión adquiere una publicación aceptada real, calcula un baseline con el fold público y cambia exclusivamente el intento/ancla del llamador al leer ese request, sin alterar originales, proveedor, reloj ni validación. Se descartan causa de fixture no aceptada/import/API ausente: el baseline pasa y el RED muestra pid=0 frente al PID nativo original.

Tres RED genuinos individuales, con runner/test/fuentes archivados antes, argv/UTC/exits/stdout/stderr y JUnit únicos:

- RED: `test_caller_identity_is_frozen_before_request_io[attempt]` falló por aceptar pid=0 · 2026-10-08T00:17:02.626986+00:00 · `runs/red-attempt/`.

- RED: `test_caller_identity_is_frozen_before_request_io[both]` falló por aceptar pid=0 · 2026-10-08T00:17:07.948471+00:00 · `runs/baseline-both/`.

- RED: `test_caller_identity_is_frozen_before_request_io[transition]` falló por aceptar pid=0 · 2026-10-08T00:17:08.702251+00:00 · `runs/baseline-transition/`.

El control ancla sola ya pasaba: no se cuenta como RED. GREEN dirigido4 PASS. Los controles extra de retorno directo rejected/interrupted auditan alias de entradas y exports, sin cambiar diseño ni contarse como RED nuevos. El caso accepted/transition conserva recibo, historial y samples exactos pese a mutaciones durante I/O y después del retorno.

Verificación final única: **94 passed in 55.53s** =88 predecesores +6 casos nuevos; cero fallos/skips. Se conserva AST exacto de todas las funciones/tests/helpers anteriores, decoradores y asserts. Los25 vecinos nativos usan clon propio con sólo PHASE cambiado; funciones y fixture mantienen AST exacto. Los34 RED funcionales anteriores y sus88 PASS permanecen predecesores intactos, no recertificación histórica. Validador semántico y demás funciones protegidas exactos salvo fold/transition; `benchmark_episode.py`, incluidos Provider/Acquirer, byte-exacto. 62 protegidos exactos.

Cobertura oficial actual completa de `benchmark_canonical.py`: **87.242798%**, 323/356 líneas, 101/130 ramas; **0 excluidas**. Datos originales `runs/final-current/.coverage` y JSON oficial `coverage.json`; fuentes congeladas idénticas antes/después/actuales. No union de pasadas, changed-lines ni promedio. `benchmark_episode.py` **81,316348% sólo predecesor** con bytes unchanged; no childcoverage costoso nuevo. Ruff check y format --check exit0.

94 nacimientos propios UUID/PID/creation FILETIME/Job ligados a 94 cierres reales: Job vacío, reader joined, exit registrado, cero errores. Logging pasante original init/close incluye autoclose; sin sustitución de provider/acquirer. Recibos y prueba agregada en `native-ownership-cleanup-proof.json`. En los RED tempranos constan identidad/FILETIME/intentos/cleanup propios, sin logging UUID de startup. stdout hijo es RPC; stderr original DEVNULL no se certifica vacío. Valores de sensor CPU sintéticos; procesos y relojes Windows reales. Sin afirmaciones de GPU/cadencia/calibración.

Se esperó el CLI terminal t08-fixture-owner-fix3 (exit0, 2026-10-08T00:18:29.453267+00:00) antes de la corrida final (2026-10-08T00:18:59.955934+00:00). Helper final `scripts/test_workspace.py` SHA da1fb4f6b0fdd6cad46f801e495bd86c4fb6d8d140971ed4bb4b936b9eaa525a permanece exacto durante/tras tests. Limitación histórica explícita: el runner inicial no archivó ese helper global en RED; sus bytes cargados son UNKNOWN y no se afirma equivalencia con el helper actual. La fuente/test/runner del RED sí están archivados. Ningún restore de otro actor.

Original freeze3 incluye episode unchanged; mapas sources-before3/sources-after3, frozen-current, protected-before/after, diff, compatibilidad AST y loaded-bytes acompañan el recibo. Inventario NONCLI completo con SHA/tamaño, excluyendo exclusivamente los cinco nombres top enumerados; conserva todos los artefactos/cachés/fixtures/receipts privados. No se ejecutaron runners privados anteriores ni se modificaron fases cerradas.

Incidente de finalización: la primera lectura del JSON oficial comparó un path Windows con un literal de barras y falló el assert de reporting. Se corrigió normalizando separadores sólo en el lector; no se tocó el JSON/data oficial, fuente ni tests, y no hubo rerun de pruebas. `finalization-incident.json` conserva la limitación de captura (tool transcript, sin wrapper argv/UTC/stdout/stderr); no es RED funcional.

Root conserva ledger/docs/Git/decisiones/aceptación. No memoria/gotcha en docs por ownership explícito; causa y evidencia quedan aquí para root. No goals/delegación/GPU/UI/WSL/Ollama/red/install/hostPython. Sin integración runtime/coordinador/rowreader/FINAL packs, sin matriz T09 ni cierre de tarea. Actual model/tokens/EUR/AIhours NULL; sin estimación numérica inventada.

DONE_WITH_CONCERNS: revisión fresca y QA independiente pendientes; bytes del helper global en los RED tempranos UNKNOWN, verificación final same-current exacta.
