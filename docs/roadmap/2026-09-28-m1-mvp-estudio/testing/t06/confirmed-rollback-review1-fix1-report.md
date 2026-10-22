> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

B-01 Important, revisión 1: implementación concreta revisable; aceptación exclusiva Root.

RED causal original: prepare-KeyboardInterrupt, SQLite real UPDATE+flush/writer y EventBus/suscriptor reales, primario/traceback retenidos. Exit1: faltaba close (calls=[]); fixture y colección correctas. UTC/argv/PID/exit/stdout/stderr/JUnit y preimágenes en red/. Hypótesis probada: except Exception dejaba salir BaseException sin rollback/close. El finally privado del test libera sus sesiones sólo después de observar el fallo; no demuestra limpieza productiva.

Cambio mínimo: limpieza, begin, prepare y commit capturan BaseException. Ambos pasos de limpieza se intentan; secundarios se adjuntan al mismo primario con atributo privado y notas, sin cambio de tipo/args/cola traceback. Confirmación sólo tras rollback+close exitosos antes de commit; sello privado exacto e inmutable intacto. Constructor fuera del catch de Session: no objeto, no close ficticio. Callback catch amplio preserva incertidumbre: interrupción incierta provoca mark_gap real y rethrow; el resultado confirmado se comprueba fuera del catch. Anotaciones diagnósticas no otorgan autoridad. Publish BaseException provoca gap y rethrow, nunca PublicationOutcome ni éxito. El comportamiento Exception durable B01 permanece.

23 casos nuevos: KeyboardInterrupt, SystemExit y subclase BaseException en prepare/begin/commit/rollback/close/ambos/constructor; real commit persiste 0.9 y después lanza, DB durable+gap; rollback y close reales seguidos por secundarios inyectados, ambos intentados y primario conservado; callback/publish interrupt con gap real y secundario SystemExit. Boundary injection Python explícita, sin CTRL-C, señal OS ni subprocess nativo engine. Preparación real UPDATE+flush adquiere writer; dump SQLite, transacción inactiva, close observado, identity map vacía y feed exacto en confirmado, referencias primario/traceback retenidas. No pesos reales: wrapper Catalog seguro sintético copiado del productor, sólo fixture privada declarada.

GREEN focal 23 PASS. Una única baseline completa final: 294 PASS = 246 originales +25 anteriores +23 nuevos, ocho archivos completos, orden/IDs previos exactos, siete antiguos byteexact y todos los 25 anteriores AST exactos (asserts/decorators/params/functions). WHOLE cuatro módulos, única .coverage RAW fresca + JSON, cero excluidas, todos >=80. Sin union de trazas. Ruff check corriente y format --check exit0 sobre owned3. Primer lint exit1 por cuatro BLE001 preservado; sólo cuatro comentarios noqa añadidos después del baseline: AST incluyendo ubicaciones exacto, sin segunda suite. Error privado de selector ruff-check-final ejecutó realmente format --check, honestamente registrado; runner original conservado y ruff-check-current ejecutó check real.

Fuentes, runner, harness/fixtures y herramientas managed copiadas antes de actual Popen, fuentes después y protegidos scope exactos; no freeze global ni propiedad sobre actores disjuntos. Herramientas copia física una vez antes del primer pytest; fuentes por comando. Bootstrap inicial de runner/stdlib TCB anterior a copia, no inventar custodia before del bootstrap. Tests nativos no autorizados ni ejecutados; sólo subprocess pytest/Ruff con wait directo. OS/DLL/transient/unseen holders UNKNOWN. Entorno UV/TEMP/TMP/pycache/coverage y artefactos privados; .venv gestionada, cero install/download/network/globalcache/hostPython. History RED y baseline productor originales intactas. NULL modelo/tokens/EUR/horas IA originales, sin inferencia. TDD n/a runner/report/config estáticos.

No ledger/docs/ADR/Git/goal/knowledge/subagentes ni fuentes fuera de owned3. No fullT06/generación/seguridad limpia/E2E/GPU/UI/Docker/WSL/PDH/801/fullserver/model/API. Root conserva revisión fresca, QA independiente y focused rescan/aceptación.

Cobertura oficial completa:
apps/server/app/event_snapshot.py: 93.750000% cero excluidas
apps/server/app/publication.py: 96.428571% cero excluidas
apps/server/app/queue/events.py: 95.714286% cero excluidas
apps/server/app/sse.py: 95.226730% cero excluidas
