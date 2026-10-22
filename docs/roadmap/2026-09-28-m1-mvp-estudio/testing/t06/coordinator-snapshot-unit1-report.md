> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

U2c implementada y verificada en scope; lista para revisión fresca de Root, con deriva disjunta declarada.

Final seleccionada: 239/239 PASS; pytest exit 0; líneas y ramas oficiales, UNA traza nueva, cero exclusiones.

| Módulo completo | Líneas | Ramas | Oficial combinado |
|---|---:|---:|---:|

| apps/server/app/event_snapshot.py | 95.238% | 90.909% | 93.750% |

| apps/server/app/publication.py | 91.549% | 81.250% | 89.655% |

| apps/server/app/queue/events.py | 95.595% | 91.250% | 94.463% |

| apps/server/app/sse.py | 96.540% | 92.308% | 95.227% |



Cambios concretos: PublicationCoordinator por instancia con RLock, adquisición <=2s configurable a20ms funcionales; callback síncrono confirma commit y retorna CommitPublication finito construido antes de commit. Orden coordinator→SQLite writer/transacción→bus. PublicationOutcome conserva el retorno durable y fallos de publish/gap; commit incierto propaga el primario, con nota fija si gap también falla. invalidate=True expresa publicación omitida; el caller debe auditar toda mutación visible. No garantiza writers no integrados ni hard realtime.

EventConsumer admite sólo coordinador explícito; default mantiene propagación legacy de publish. Validación y serialización de la entrada preceden la barrera. Sus checks actuales de User local vivo, Song vivo/no soporte, Job/Attempt vivos, owner/engine/ordinal y secuencia siguen siendo la autoridad real del certificado. Los datos del engine no otorgan scope. Una proyección pública inválida conserva el commit y usa el gap legacy. Sin locks privados por consumer.

TrustedFeedScope owner ULID fijo/song ULID opcional sin ID-set creciente; delta/system siempre denegados. CertifiedPublication/fábrica es interfaz confiada del publisher tras checks DB, no autenticación frente a código Python hostil del mismo proceso. Autoridad sellada inmutable separada del dict; deepcopy/replay conservan certificado, y el predicado revalida identidad/tipo canónicos y owner/song. PublicRecord conserva constructor3 args, equality/repr legacy (metadata compare=False/repr=False); encode_frame nunca exporta el certificado. No se admite flag/dict/callable como scope ni permiso. TrustedScope AST exacta/max64; ring256/pending64/subscribers32 y notificaciones coalescidas conservadas.

build_snapshot retorna tuple completa tras validar todos los JobStateDTO cerrados, conflictos y controles existentes. Orden job_id, dedup active+known,1000+64/1064, chunks64/max17, preflight sin salida parcial. H/ts/snapshot_id únicos, sólo end id epoch:H, vacío begin/end. Cota conservadora512bytes/DTO+1024control:64*512+1024=33792<=65536; test llena1064 y máximos actuales incl float23chars/Hmáximo. Ni DTO ni owner de navegador acreditan SQL.

TDD: red-core4FAIL (publicación omitida tras SQLite commit real, snapshot vacío y certificado explícito denegado); red-barrier-faults42FAIL (barrera real de2hilos, fallos de publish/gap, validaciones); red-certified-fallback3FAIL1PASS (forged authority causó AttributeError y etiqueta privada bloqueó commit); red-null-certification1FAIL3PASS (autoridadNone pasó sin gap). Los fallos de API/import/colección no cuentan como RED. Todos los comandos, sources-before, tests/fixtures/runner, JUnit y stdout/stderr originales están archivados. Las ampliaciones que ya pasaban son caracterización/cobertura, no RED inventado.

Historia privada de harness conservada: tres intentos fallidos por alias faltante, shadow de logging y relative import. Hipótesis verificada en tracebacks; fixture final asigna sys.modules a módulos app reales. Este actor no modificó tests antiguos; sus asserts, decorators, parámetros y funciones conservan AST exacta. Hay una deriva de bytes en un fichero disjunto no seleccionado, declarada abajo. Ruff imports/format y notas noqa BLE001 documentan retención de fallos, no exclusiones de cobertura.

Protegidos exactos=True; tests antiguos byte+AST exactos=False; fuente actual vs final antes/después=True; runner/fixture/tests/config exactos durante final=True; lint/format-check0. source-parity.json y coverage-original.json conservan datos originales.

Baseline final seleccionada incluye ficheros enteros nuevos y old test_sse_bus, test_sse_frames, test_dispatcher_events, test_local_sessions, test_event_dtos. No case exclusions ni -k. Sin whole453/801: no necesarios para esta unidad pura/optional consumer; no se amplía runtime/retry/admission para resolver QA2. Su fallo801 histórico permanece pendiente y no se concede waiver ni rendimiento.

Native88 ya terminal0 a 2026-10-09T04:43:13.535692+00:00, antes del primer test de esta unidad. Aquí sólo pytest propio reaped y hilos propios acotados/joins comprobados; ningún caso native88 lanzado. Ausencia de procesos ajenos/transitorios, DLLsOS y cierre universal: UNKNOWN.

Copias físicas previas a los tests: intérprete base gestionado, scripts/.venv y dependencias completas sin __pycache__; 8121 ficheros cotejados después con originales actuales. Primer hash/censo no ocurrió antes de imports: no se retrocertifica. Logs robocopy presentes; argv/UTC/exit completos de aquellos shells sólo parciales en transcript. Antes de cada pytest Popen se copian fuentes, fixtures, tests, runner y configs. TEMP/TMP/UV/pycache/coverage y artifacts privados; sin hostPython/install/red/globalcache. Provider modelo/tokens/EUR/horas null sin originales.

Pendiente explícito: instancia compartida/runtime.py y todos writers (admission/retry/recovery/cancellation/chains/manual_retry/CPU durable), resolver DB autorizado, WAL BEGIN real/read+register+H, replay reauthorization, borrado/transferencia/epoch invalidation, endpoint SSE/session bind/no-store y lifecycle/heartbeat/send timeout, cliente/parser/reducer y E2E. No exponer feed hasta ello. HTTP315 previo no cambia; no HTTP/API/UI/contrato generado nuevo. Root mantiene ADR/ledger/Git/aceptación/meter, revisión fresca y QA independiente. T06 NO completada.

TDD n/a prosa/config/harness privado; no subagentes, goals ni knowledge usados.


Adjudicación de scope: los CINCO ficheros antiguos incluidos en la baseline final son byte+AST exactos desde red-core; todos los protegidos son exactos y todo el código/fixture/tests durante final es exacto. La auditoría inicial detectó deriva de bytes en apps/server/tests/test_worker_native_linux_custody.py, fuera de OWNED y de la selección; AST exacta, autor UNKNOWN. No se revierte ni se acredita como edición propia. Recibo/informe iniciales con esa alarma se conservan en audit-first-original; disjoint-drift-adjudication.json contiene hashes/normalización y comparación. Esto no modifica la traza actual ni reejecuta tests; Root adjudica la deriva ajena.
