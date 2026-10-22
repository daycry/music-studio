> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Componente de proyecciÃ³n conservadora del lector

Entrega acotada para revisiÃ³n fresca y QA de Root; no aceptaciÃ³n de T-04 ni del hito.

El lector limpio proyecta las 25 columnas Job mediante atributos mapeados y with_only_columns(maintain_column_froms=True) sobre _query original. El materializado completo de filas mantiene todos los procesadores, incluido telemetry JSON. Cursor con etiquetas exclusivas y posiciones separadas; snapshot_values usa los mismos 17 campos canÃ³nicos compartidos en resolver. No Job ficticio, SQL de lectura crudo, cache, tabla, migraciÃ³n ni API nueva.

La limpieza se comprueba en cada pÃ¡gina: identity_map/new/dirty/deleted activan exactamente el camino ORM y expunge previo. Se conservan WAL/transacciÃ³n, joins/filtros, UTC fraccional/keyset, FIFO/prioridad y lÃ­mite 400. Writer/revalidaciÃ³n/dependencias/referencias/reserva/CPU2/GPU1 siguen iguales. scope-audit.json verifica AST del bloque writer y todos los demÃ¡s mÃ©todos Admission, nodos resolver ajenos a snapshot, cuatro protegidos por SHA y las 21 funciones scanning originales con decoradores/aserciones/parametrizaciones intactos.

RED: apps/server/tests/test_dispatcher_scanning.py::test_clean_snapshot_reader_avoids_job_entities fallÃ³ con lector=[Job.id] frente a []; writer=[Job.id] ya cumplido Â· 2026-10-09T02:22:51.015560+00:00. Originales en red/before, red/stdout.txt, red/stderr.txt, red/birth.json, red/command.json y red/junit.xml. GREEN aislado: 1 PASS. La optimizaciÃ³n solo se escribiÃ³ despuÃ©s de este RED. Los invariantes preservados tuvieron pruebas escritas antes del cambio y 8 PASS previos tras reparar las nuevas fixtures; no se presentan como nuevos RED funcionales.

VerificaciÃ³n actual: 271 PASS / 0 FAIL / 0 ERROR / 0 SKIP, exit 0, en selected-custody-complete. Nueve ficheros explÃ­citos de admisiÃ³n/scanning/resolver/inputs/references/chains/manual_retry/cancellation/recovery, completos sin -k ni exclusiones. dispatcher_retry.py no forma parte de esta selecciÃ³n por fichero; no se omitiÃ³ ni debilitÃ³ su 801. Comando exacto/UTC/PID/stdout/stderr/JUnit en esa carpeta y actor-command-accounting.json. Ruff check y format --check de los tres ficheros: exit 0.

Cobertura WHOLE de cada producciÃ³n cambiada, lÃ­neas+ramas, cero exclusiones, una sola traza actual sin append/union: admission 93.33333333 %; resolver 89.08296943 %. JSON conserva tambiÃ©n las mÃ©tricas separadas; resolver ramas=79,6875 % no se redondea como un gate separado cumplido. Datos crudos .coverage y JSON copiados de la ejecuciÃ³n actual; no se usan trazas histÃ³ricas para el gate.

Nuevas pruebas: conteo reader=0/writer>0 y output Job real; mapa stale, dirty/new/deleted y autoflush original (incluido database-is-locked original), recheck entre pÃ¡ginas; deserializadores telemetry/request fallan antes del writer; tipos request/telemetry, 17 claves/valores canÃ³nicos/acento/orden JSON; cambios concurrentes de los 17 campos con updated_at fijo salvo su propio caso. Tests originales conservan inserciones backdated/WAL/orden/cancelaciÃ³n/referencias/reserva.

Fallo privado explÃ­cito de fixture: owner_id requiere un segundo usuario sintÃ©tico self-owned; solo su creaciÃ³n suspende/restaura checks de nombre, antes de leer Job. id/owner_id normalmente inmutables se ensayan suspendiendo/reponiendo identity_job dentro de la transacciÃ³n de la mutaciÃ³n antes del commit. owner_id cambia tambiÃ©n song_id para respetar el dominio del nuevo propietario. No se retiran controles en producciÃ³n ni se relajan datos rechazados por ella.

Historia conservada: semantics-before 5 FAIL/3 PASS (expectativa de autoflush y cache del deserializador de las nuevas fixtures), reparado 8 PASS antes de producciÃ³n; selected-current 19 FAIL/252 PASS (nueva fixture User y STUDIO_TEST_ROOT faltante); concurrent-repaired 2 FAIL/15 PASS (identidad inmutable); selected-final 1 FAIL/270 PASS (owner/song); concurrent-isolated-fields 1 FAIL/16 PASS (User.owner_id); concurrent-self-owned-fixture 17 PASS. Ninguno se cuenta como RED de producto ni se oculta. selected-current-final 271 PASS tenÃ­a cuatro fuentes transitivas faltantes en captura previa; la repeticiÃ³n final responde a ese hueco material de custodia y no a mejorar timings.

Custodia final: 8409 copias fÃ­sicas con SHA-256, 297534275 bytes antes de Popen; .venv, intÃ©rprete gestionado, apps/server, packages, scripts/configs, engines common/mock y bytecodes privados. 1007 mÃ³dulos con fichero observados, 0 huecos frente a before, 56 builtin/frozen/namespace separados. Las copias de contexto son posteriores a su primera lectura; no se certifica retrospectivamente first-read. Caches UV/TEMP/TMP/pycache/pytest/coverage/Ruff bajo esta carpeta; uv/instalaciones/red/GPU/WSL/Ollama/Docker/UI/PDH no ejecutados. Los procesos del runner tienen birth/exit y fueron esperados por run.py; el inventario separado tiene inventory-command.json e inventory-terminal.json con exit 0 observado del exec; enumeraciÃ³n OS de descendientes UNKNOWN, sin terminar procesos ajenos. No se afirma ausencia universal de hooks ni ejecuciÃ³n nativa a partir de hashes.

Gates sin ejecutar por esta unidad: original 801 cubierto con timeout 10 s intacto, suite completa 32 ficheros/1029, revisiÃ³n independiente y QA de Root. Antecedente 1025 PASS / 1 FAIL / 3 SKIP sigue abierto. Cero afirmaciÃ³n de speedup medido o causa histÃ³rica corregida.

Solo tres ficheros autorizados y outputs privados; ledger/docs/ADRs/Git/aceptaciÃ³n/meter no editados. Uso real modelo/tokens/EUR/horas IA=NULL; originales CLI reservados de Root intactos. non-cli-inventory.json excluye solo cuatro nombres reservados exactos en raÃ­z y su propio fichero.

DONE_WITH_CONCERNS: gates de integraciÃ³n/801/revisiÃ³n/QA pendientes de Root; custodia histÃ³rica limitada declarada y enumeraciÃ³n OS de descendientes UNKNOWN.

TDD n/a: helpers privados de custodia/inventario y prosa del recibo; sin cambio adicional de producción.

