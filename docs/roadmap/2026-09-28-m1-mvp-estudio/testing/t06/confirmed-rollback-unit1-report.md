> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# VULN-001 — implementación acotada de rollback confirmado

Estado: código concreto y baseline funcional verde; revisión fresca, QA independiente y aceptación exclusivas de Root. ADR0061 O1 adoptado y handoff explícito. OWNED exactos: publication.py, queue/events.py y test_publication_confirmed_rollback.py. No escrituras fuera de OWNED y este paquete privado.

La integración emite _ConfirmedRollback frozen/slots y sello privado únicamente después de preparación fallida, rollback real y Session.close completados, antes de cualquier intento de commit. El coordinador comprueba tipo exacto y sello fuera del catch genérico, y relanza el MISMO primario con su traceback original como cola y from None. No retorno de éxito ni Outcome en el rechazo. Begin fallido, rollback/close fallidos, callback genérico y commit incierto mantienen gap. Commit SQLite real que persiste y después lanza conserva DB durable y gap aunque el rollback posterior falle. Secundarios rollback/close se conservan en atributo privado y notas; no sustituyen identidad, clase ni args del primario.

_prepare_batch contiene el mismo cuerpo AST de validación/modificaciones/batch original. _commit legacy conserva Session + session.begin y propagación original. No se debilitan propiedad, ordinal, secuencias, replay, CAS o fuente; B01, None legacy, ack/count/vacíos/invalidate se ejercitan en los antiguos siete ficheros byteexact.

## RED y límites honestos

red y red-causal fallaron en bootstrap de fixture: Catalog tenía digest synthetic inválido y weights vacío para la nueva procedencia. Se preservaron íntegros; no son RED causal. Reparación privada declarada: wrapper autouse sobre el Catalog sintético ajeno, health digest unknown y metadata de peso fixture/model.safetensors con SHA sintético de 64 a, 1 byte, safetensors. No archivo de pesos real ni bypass de validadores. SQLite, EventConsumer, EventBus, ring y suscriptores son reales.

red-causal-complete tiene CUATRO RED causales (identity/sequence/owner/ordinal): contrato válido, ValueError esperado observado; dump SQLite independiente permanece exacto y a continuación falla igualdad feed/epoch, con ring/replay/pending reales destruidos y lectores cerrados por gap. Fuentes, test, runner, dependencias y fixtures capturados físicamente antes de Popen. Otros dos casos terminal/replay fallaron por enum SYNTHETIC inválido en el test nuevo; se corrigió a INTERNAL antes de GREEN, sin atribuirles RED causal independiente. RED-receipt.json conserva esa distinción. No reejecución retrospectiva del RED ni waiver por QA246 histórica.

## Única baseline final actual

271 PASS = mismos 246 antiguos + 25 nuevos, 0 fail/error/skip. Ocho ficheros completos; sin -k, exclusión, selección parcial ni retry funcional. Los casos nuevos cubren identidad/secuencia/owner/ordinal/terminal/replay, otros jobs y lectores, identidad real del error y nodo de cola del traceback con observador passthrough, begin/commit/rollback/close inciertos, commit que REALMENTE persiste antes de lanzar, rollback real que después lanza, close antes/después, commit durable seguido de close fallido, seal/tipo/JSON/bool/ValueError inválidos, callback ValueError genérico, inmutabilidad y error legacy.

WHOLE actual oficial líneas+ramas en una única .coverage fresca, cero excluidas:

- apps/server/app/publication.py: 96.226415% (summary completo en whole-current-coverage.json).
- apps/server/app/event_snapshot.py: 93.750000% (summary completo en whole-current-coverage.json).
- apps/server/app/sse.py: 95.226730% (summary completo en whole-current-coverage.json).
- apps/server/app/queue/events.py: 95.714286% (summary completo en whole-current-coverage.json).

Ruff check y format --check --no-cache actuales sobre OWNED: exit0 ambos. Historial estático conserva primera tentativa de format exit2 (reemplazo textual privado convirtió accidentalmente 0.9 en None.9; corregido antes de ejecutar tests), y lint inicial con cuatro avisos de imports/noqa corregidos; no se borró historia ni se llamó RED al parsing.

## Custodia y entrega

actor-command-accounting.json y cada command-original.json registran argv reales, PID de runner/child, UTC, environment privado, exit y wait directo; stdout/stderr originales, JUnit y coverage RAW/JSON permanecen. Intérprete .venv gestionado con base privada CPython 3.12.14; env cargado por scripts/env.ps1 y TEMP/TMP/UV/pycache privados antes de ejecución/imports. Bootstrap runners/stdlib declarados TCB; intérprete/runner inicial hash por PowerShell antes del runner. Captura física de tools y source/fixtures antes de pytest; cargados comparados con bytes previos, herramientas sin drift. Imports transitorios y kernel/DLL desconocidos, no pretensión de prueba OS. Ningún hijo engine/worker nativo propio; Popen pytest/Ruff esperados directamente, hilos de los tests originales bajo sus verificaciones existentes. No censo universal de procesos. Source/protected before/after exactos, viejos siete ficheros iguales también a QA246 y AST completos intactos. Inventario NONCLI completo excluye sólo cuatro nombres de Root reservados al nivel superior y el propio inventario.

Proveedor/modelo/tokens/EUR/horas IA/horas NULL por falta de originales; sin estimación disfrazada de uso real. TDD sólo declara cuatro RED causales; casos adicionales son verificaciones escritas antes del fix, no se fabrican rojos. TDD n/a para el runner/report estáticos. No ledger/docs/ADR/Git/goal/knowledge/subagentes, red/instalación, GPU/Docker/WSL/Ollama/PDH/UI ni suites 801/nativas/heavy. El antiguo SAST U2c6 y QA246 quedan históricos; no score limpio inventado ni dispensa del hallazgo. La revisión lógica actual y QA independiente corresponden a Root; no aceptación de T06 completo, exposición HTTP/SSE integral, allwriters, WAL, cliente/E2E ni calidad musical.
Observación adicional de cierre: la primera ejecución del finalizador de evidencia tuvo SyntaxError por escaping de una barra en su comparación de rutas; no importó producto, no ejecutó tests y no generó receipt. Fuente conservada en finalize-before-escape-repair.py y salida original en el registro de herramientas de la sesión (UTC/PID exactos de esa tentativa UNKNOWN, sin inventarlos). La ejecución corregida tiene finalize-command-original.json, stdout/stderr originales y wait directo. No hubo segundo baseline funcional. El inventario se refrescó después del cierre del finalizador para incluir sus salidas/metadatos ya terminales.
Límite del wrapper PowerShell del finalizador: WaitForExit terminó y hay salida terminal/receipt completo, pero Start-Process devolvió ExitCode NULL; se conserva NULL en finalize-command-original.json y actor-command-accounting.json, sin inferir exit0. Esto no afecta a los exits directos originales de pytest y Ruff, capturados por subprocess.Popen.wait.
