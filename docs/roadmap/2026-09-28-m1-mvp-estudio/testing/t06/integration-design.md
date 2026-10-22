---
title: Integración completa T06 — escritores, WAL, autorización, HTTP y navegador
estado: aprobado
opcion_recomendada: O1
opcion_elegida: O1
fecha: 2026-10-09
contexto: reutilizado de arquitectura T05 ajena; no contexto vacío
tdd: 'n/a: lectura y diseño'
generacion:
  modelo: null
  tokens: null
  coste_eur: null
  horas_ia: null
---

> **Decisión del orquestador:** O1 elegida bajo la delegación del propietario.
> Se libera primero el cliente fetch, independiente de la cola en edición.
> ADR-0065 adopta M1 para controles finales de metadata sobre entradas
> autorizadas y staging propio; preserva las comprobaciones actuales y
> prohíbe bytes/red/awaits bajo la barrera. El diseño no acredita
> implementación, QA ni cierre de T-06. Fuente privada verificada: 63 archivos
> y recibo del arquitecto, con contexto anterior ajeno declarado.

El [contrato del cliente](client-contract.md) precisa las correcciones de su
primera revisión y prevalece sobre la firma opcional de snapshot descrita
en la propuesta inicial. La integración de escritores adopta
[ADR-0065](../../../../decisiones/ADR-0065-comprobaciones-finales-de-metadata-bajo-barrera.md);
las opciones y preguntas iniciales de abajo conservan su contexto de diseño.

# 1. Contexto, contrato y alcance

Primero se leyó CONTINUE-HERE vigente, después AGENTS.md/CONSTITUTION. Se inspeccionaron ADR0056/58/61, preparación pública `testing/t06/integration-readiness.md`, propuesta `events-openapi.proposed.json`, brief oficial completo y fuentes listadas en el inventario. Se reutiliza contexto anterior de arquitectura CPU; no productor ni revisor del target T05. Sólo writes en este directorio privado. Sin tests, cargas temporales nativas, servicios, GPU, red, instalación, nuevos agentes, Git, docs/ledger compartidos ni goals.

Brief generado por plugin actual 1.22.0 con Python gestionado uv `--no-sync --offline`, stdout/stderr conservados como bytes. Exit0;17143bytes/16726caracteres. Aviso preexistente de exceso10000 preservado íntegro, sin recortar criterios. Verificación canónica T06: `uv run pytest apps/server -k sse -q`, reconexión con Last-Event-ID sin pérdida; CA sobre público/keep-alive15s/replay/reset. Esta entrega no ejecuta la verificación ni cierra CA.

ADR0056 fija ring256, epoch:seq global seguroJS, snapshots begin/chunk/end, CPU sin infra nueva; ADR0058 sesión pública dedicada, header/no URL, fetch; ADR0061 rollback confirmado previo a commit conserva feed/error. Recomendación se mantiene dentro de estas decisiones. Root decide cualquier precisión nueva, especialmente metadata bajo barrera y código de exceso; sin aprobación implícita en este borrador.

# 2. Interfaces actuales y gaps verificables

| Fuente/interfaz real | Estado leído y conexión pendiente |
|---|---|
| `publication.py`: PublicationCoordinator.barrier/commit_and_publish, CommitPublication, PublicationOutcome | RLock nativo acquire≤2s; orden coordinator→writer/SQLite→bus; callbacks síncronos. `_ConfirmedRollback` exacto con sello interno conserva primera causa. Batch≤1064. No coordina writers que no reciben misma instancia |
| `queue/events.py`: EventBus.subscribe(scope,cursor), cursor, publish_confirmed, mark_gap, shutdown | subscribe exige `get_running_loop`; ring replay+alta bajo lock bus; readers32/pending64; overflow cierra y despierta. Falta alta prebound para hilo del bootstrap WAL |
| `Subscription.next/close` | `next` cancelado cierra el lector. wait_for(next,15) como heartbeat sería incorrecto: cerraría lectores. Necesita next task persistente, timeout de espera sin cancelar |
| `EventConsumer(...,coordinator=None).accept` | Rama coordinada existe; `QueueRuntime.start` sigue construyéndolo sin coordinador. `_prepare_batch` publica notification también para artifact/log; `job.artifact/job.log` no están en PUBLIC_TYPES y provocan gap. Separar cambios públicos de eventos privados manteniendo legacy |
| `sse.py`: TrustedFeedScope, certify_publication, public_event, encode_frame, heartbeat, parse_cursor | Certificado interno acredita publicación en commit, no pertenencia vigente en replay. Feed dinámico sin conjuntos crecientes. Cursor no contiene identidad de filtro; TrustedScope documenta que web debe borrarlo al cambiar filtro |
| `event_snapshot.py`: build_snapshot(active,known,epoch,high_water,ts,snapshot_id,reason) | Sólo DTOs autorizados/presentes; todos frames preflight. No consulta DB ni reautoriza. Activos1000/conocidos64/chunks64≤17/frame64KiB. Duplicate activo+conocido exige igualdad |
| `event_dtos.py`: JobStateDTO/SnapshotControlDTO | DTO cerrado, job/song ULID, attempt nullable, labels ASCII64, progress nullable, end.id igual seq de end.cursor. No request, terminal, lyrics ni paths |
| `local_sessions.py`: validate/revalidate/revoke/close, SessionBinding | Registry32, token mémoire8h monotonic. revalidate devuelve deadline absoluto; no wake callback para feed al revocar. No adquirir registry lock en loop porque puede esperar2s |
| `event_routes.py`: local_owner/_credential/_empty_request/register_session_routes | POST bootstrap y DELETE session implementados; GET events aún ausente. Header único, body/query vacío para sesión. Owner siempre resuelto por DB, no por cliente |
| `security.py`: LocalSecurity/SESSION_PREFLIGHT | Token permitido preflight sólo bootstrap y DELETE; events necesita GET+token+Last-Event-ID opcional, origen exacto y loopback dedicado. Middleware controla Host/Origin antes routing |
| `main.py`: lifespan y register_session_routes | Sesión/cola/DB construidos; compartir un único coordinador y lifecycle feed. Shutdown debe parar publicaciones, bus/readers, registry y DB ordenadamente |
| `apps/web/lib/events.ts` | EventSource sin header sesión. Incompatible ADR0058. No parser fetch, cursor epoch:seq ni reducer snapshot. `events.test.ts` prueba doble EventSource y usa `/events`; no prueba `/api/events` ni transporte real |

No hay runtime integrado de publicación de takes/Analysis en app/worker leído: contratos, ejecución, IPC/custodia son componentes presentes; su futura mutación DB deberá entrar al mismo mecanismo. No afirmar cobertura de writer futuro inexistente. `queue/provenance.py` selecciona/captura DTO, sin escritura DB directa; escritura ocurre Admission.capture_provenance.

# 3. Opciones reales y recomendación

Las tres cubren endpoint y navegador completos; ninguna declara que el bus aislado cumple T06.

| Opción | Diseño concreto | Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|---|---|
| O1 recomendada | Una instancia PublicationCoordinator por QueueRuntime/app; cada transacción participante retorna batch/invalidate tras commit; bootstrap WAL y attach prebound bajo misma barrera; route/ASGI finito+fetch reducer | Media-alta | Medio: inventario completo/locks/ventanas de fallo requieren pruebas | M | Alta: conserva APIs legacy y ring |
| O2 | Actor nativo único con cola acotada de comandos para TODOS escritores y bootstrap, tickets creados en loop; SQL se ejecuta en actor y publicación inline; route/fetch iguales | Alta | Medio-alto: cambia ejecutores, orden/FIFO y shutdown; migrar cada call path, no bastaría mover sólo EventConsumer | L | Media: callers pasan por actor |
| O3 | Outbox SQLite durable insertado en cada tx + lector/stream; feed auth/reducer igual; cursor durable y epoch/reset definidos | Alta | Alto: reabre ADR0056, necesita migración y snapshots/backups/export; still auth y atomic reset | L | Media-baja: nuevo contrato durable |

Recomiendo O1 para el runtime único fijado; O2 no elimina el trabajo de integrar writers ni el gate de filesystem y desplaza mucho código de T04/T05. O3 sólo si cambia requisito a replay histórico durable/múltiples procesos; no se elige ahora sin ADR nuevo. O1 aún requiere Rootdecisión y release de ownership T05.

**Finalchecks de ficheros:** root pidió comparar dos soluciones sin debilitar seguridad actual.

| Variante | Garantía y coste real | Recomendación |
|---|---|---|
| M1 — excepción explícita sólo metadata final de staging propio/read-only | Conservar `resolve_references(...verify=False)`, `staged.check`, `proof.check` finales actuales. Permitir exclusivamente path/stat/link/junction/identity checks de entradas acreditadas bajo coordinator→SQLite, siempre hilo nativo; nunca byteIO/hash/copia/cleanup/red/modelo/await. Syscalls no tienen hardRT garantizado; acquire2s no limita duración de callback | Más simple, conserva comprobación filesystem actual. Requiere precisión ADR0056+docs publication/readiness por Root antes source edits; no política vigente aún |
| M2 — lease/custodia pura lifecycle servidor | Ownership lease impide que mutadores/cleanup propios cambien staging durante claim; bajo tx se compara token/version sin FS. No prueba filesystem externo congelado ni reemplaza stat frente a alteración externa. Para conservar garantía actual exige custodia real de bytes/handles/ACL o checks complementarios | Mayor superficie y depende T05; no aprobar como sustitución silenciosa de finalchecks ni inferir congelación externa |

M1 recomendada como precisión honesta si Root la valida. No envolver reserve actual alegando cero fileIO ni mover checks fuera para pasar gate. Captura/validación/SHA/staging ocurren antes; cleanup y pruebas de commit incierto ocurren después de liberar locks. Los fallos metadata precommit usan rollback confirmado; no dispensar vigencia por evidencia vieja.

# 4. Coordinación completa, WAL y autorización

**API interna propuesta:** `QueueRuntime.publications` único se entrega por constructor a Admission, GenerationChains, Cancellation, Recovery, Retry, ManualRetry, EventConsumer y futuros writers CPU. Constructores mantienen `coordinator=None` para consumidores legacy existentes; la app productiva no usa esa excepción. Main expone `application.state.event_feed` con registry/engine/bus/coordinator, no otro bus/coordinator. Helpers subtransaccionales `add_dependents`, `_dependencies` y writer(session) no adquieren otra barrera ni publican antes commit.

| Participante actual | Transacciones a integrar y batch público |
|---|---|
| Admission.candidates/candidate_batches | Mutan blocked→queued/DEPENDENCY_FAILED. Un batch por writer-page≤400, no mantener barrera durante generator/yield ni outer WAL reader. Comparar campos públicos before/after sólo de filas elegibles; failed real o state refresh certificado |
| Admission.reserve | running+attempt nuevo; claim public job.stage/state acorde a estado real. Staging prebarrier y cleanup postbarrier; M1 metadata gate |
| Admission.capture_provenance | Write-once privado; batch vacío pero misma disciplina coordinator→writer. DTO/SHA fuera; no exportar metadata del modelo ni emitir progreso ficticio |
| Admission.acknowledge | Submitted privado, batch vacío si estado público igual; autoridad vigente intacta |
| GenerationChains._create/add_dependents | Publicar job.created para generación, post y beats realmente insertados y entity.updated take cuando corresponda, todos certificados DB; transacción completa sin eventos parciales |
| Cancellation.request/pending | Intención durable real, cancelled si terminal local confirmado; nunca job.cancelled por sólo cancel_requested de engine running. Batch state refresh para estado sin tipo nuevo, o invalidación explícita si proyección no representable |
| Recovery.startup/uncertain | interrupted durable; state refresh certificado/invalidación. Startup sucede con bus disponible pero antes exposición endpoint; nunca reconstruye éxito de carpeta |
| Retry.reserve | Nuevo intento ordinal y running dentro única tx; registrar notificación con nuevo attempt real. Inputs check gateM1; no volver a POST si publish falló |
| ManualRetry._claim/add_dependents | Nuevo job lógico+rebind takes seleccionados+post/beats dependientes; certificar todas nuevas filas afterflush beforecommit, publicar después. No reenviar chain si notificación falla |
| EventConsumer.accept | stage/progress/terminal reales y cursor engine atómicos. Replay duplicate devuelve batch vacío. Log/artifact/private cursor updates no hacen nuevo evento público inválido; delta continúa política existente sin autorizar texto en feed dinámico |
| Futuros dominio/CPU publication/analysis | take ready, assets, analysis/entity mutations entran misma instancia. FS publishing fuera barrera salvo metadataM1 explícita; writer más CAS pure dentro. Deben registrarse antes de exponer funcionalidad que los usa |

Un método con múltiples commits no puede emitir `_ConfirmedRollback` de la operación entera si hubo un commit previo: callbacks individuales por transacción/página, cada uno conserva primera causa. Batch vacío sólo cuando no cambia proyección pública; no usarlo como bypass para cambios visibles. Lo que no sea representable con tipos existentes puede `invalidate=True`, pero invalidar deliberadamente cada progreso no cumple experiencia/replay ni sirve de atajo. Un publicador fallido conserva retorno durable y mark_gap independiente; nunca rollback/resubmit/terminal fake.

**Bootstrap O1, sin await bajo RLock:** en loop crear ticket/subscriber con asyncio.Event y loop real, antes de DBtask. Añadir API interna bus `prepare_subscription(...)` en loop y `attach_prepared(ticket,scope,cursor)` síncrona bajo coordinator en native thread; ticket exacto/sellado/single-use y perteneciente a ese bus/loop. `subscribe` legacy conserva firma/semántica/get_running_loop mediante wrappers. No `call_soon_threadsafe` ilimitado ni thread rendezvous esperando loop bajo barrera. No llamar get_running_loop en hilo ni adquirir RLock síncrono desde endpoint.

Callback nativo toma coordinator, revalida registry binding y owner/song/known IDs, abre BEGIN de lectura WAL y realiza SELECT inicial que fija snapshot (BEGIN por sí solo no basta), captura DTOs públicos y H del bus, decide replay/reset y hace attach prebound antes liberar coordinator. Lectura sólo columnas JobStateDTO con outerjoin al intento vigente `(job_id,ordinal=Job.attempt)` si existe; no hidratar requests/provenance JSON/pesos/modelo. Queries acotadas a1001 activos y≤64 known, joins User local live/Song sameowner live no dependencyonly/Job sameowner live; índices reales y query count se prueban. Si1001 activo: error explícito, cerrar ticket sin stream. DTO rows copiadas y tx cerrada antes encoding/envío.

All writers coordinados quedan completamente antes del WAL/H o después de H con publicación: ningún commit cae fuera de snapshot y feed. Si replay utilizable no obliga reset, pero snapshot bounds no se validan sólo tras enviar200. Construir/preflight todos frames snapshot antes http.response.start (build_snapshot reutilizado fuera barrera sobre DTOs frozen). Future buffer overflow durante preflight invalida suscriptor; cerrar y repetir bootstrap acotadamente o devolver503 antes200, nunca continuar con snapshot viejo seguido de gap oculto.

Auth antes replay y antes cada frame/página snapshot enviada, también tras espera/heartbeat: registry.revalidate y DBowner/live song. Para records replay/batch live comprobar identidad actual de job/entidad y canción; certificado sólo selecciona candidato. Entidades resuelven parent membership por tablas explícitas, no owner_id wire. No guardar permisos en sets crecientes ni escanear toda biblioteca. Si no existe/borrado/movido fuera scope, no entregar record; si desaparece owner/filter root, cerrar. Al saltar records no avanzar cursor sobre otros eventos que el cliente no ha aplicado de manera que encubra datos autorizados posteriores; global secuencia puede saltar naturalmente por filtro. Filtro nunca es owner authority.

Registro/revoke no adquiere coordinator mientras registry lock retenido. Lock order nativo global coordinator→registry(bounded/release)→SQLite→bus; no send/await con ninguno. Revocación marca binding, después wake/cierra lectores genuinos de ese binding desde lifecycle acotado32, fuera registry lock; cierre registry despierta todos. SessionExpiry wait deadline tiene base monotónica compatible registry. Autorización corresponde al checkpoint antes send; no prometer revocar bytes ya preparados/en tránsito ni retener SQLite/barrera durante red.

# 5. Query, cursor, HTTP y cliente: decisiones propuestas

Recomiendo fijar `song_id` opcional SINGLETON ULID; `known_job_id` repetido0..64 ULID distintos (`form/explode=true`), todos pertenecientes a binding/filter actual. Rechazar duplicado song_id/known repetidos, owner/token/cursor en query, parámetros ajenos/UTF8 inválido/escape inválido y exceso de query antes materializar colección ilimitada. Header X-Studio-Session-Token exactamente1, Last-Event-ID≤1 ASCII96 validado parse_cursor; body vacío y headers≤128 como endpoints públicos actuales. Límites byte query/header definitivos los fija Root y contract tests; derivarlos del máximo64 IDs sin inventar un nuevo permiso.

**Cambio de filtro:** cliente cancela conexión anterior, descarta snapshot parcial, cursor y cards del scope anterior; abre nuevo scope sin Last-Event-ID y exige bootstrap. Semántica ya documentada en TrustedScope/ADR/propuesta. El servidor autentica filtro nuevo; epoch:seq solo NO identifica filtro ni detecta que caller malicioso lo reutilizó. No afirmar detección server. Si Root quiere enforcement server añadir identidad de stream/scope vinculada a sesión mediante contrato aparte acotado; no meterlo de forma opaca en cursor ni cambiar gramática actual. Known IDs son hints de reconciliación terminal, no permisos, ni filtro de feed limitado64.

**Errores:** malformed cursor/query/>64known422 INVALID_PARAMS; session401 SESSION_REQUIRED; scope no autorizado/absent/foreign/deleted403 FORBIDDEN_SCOPE homogéneo sin echo; unavailable owner/barrier/backend503 SERVICE_UNAVAILABLE; subscribers llenos503 explícito. Snapshot servidor>1000 activos recomiendo nuevo503 SNAPSHOT_LIMIT, en ProblemDTO/PROBLEMS y OpenAPI code-first como ampliación compatible; root decide antes implementación. No truncar, no confundir sobrecarga de estado servidor con input inválido. Tras200 no se puede enviar ProblemJSON: close con reconexión y endpoint nuevo devuelve fallo finito. Nunca volver al token engine.

**Contrato:** propuesta actual tiene GET operationId stream_local_events, query señalada y401/403/422/503, controles DTO y text/event-stream. Canónico aún sin GET; no editar JSON a mano y asumir registrado. FastAPI code-first registra GET/schema de header/query/errors exactos, gen contratos y api.d.ts mismo diff; añadir enum SNAPSHOT_LIMIT sólo si aprobado. Preservar sesiones/health/operaciones existentes; api-contract lint+diff, export parity, types-client tests son gates futuros. Propuesta no demuestra autenticación ni SQL ni transporte.

**HTTP/ASGI completo:** nuevo stream handler en `event_routes.py` o `event_stream.py` con response ASGI propia si StreamingResponse no permite imponer30s deadline real de send. Ejecutar preflight autorización/query/ticket/snapshot antes status200. CORS events GET sólo header token y Last-Event-ID opcional, origen exacto/loopback/no proxytrust; Cache-Control:no-store y text/event-stream, nada de credencial en URL/cookie/storage. Heartbeat comentario15s sin ID usando deadline absoluto; await/send/close30s acotados, receive watcher disconnect único, cleanup finally idempotente. Mantener nexttask persistente con `asyncio.wait` para heartbeat; no wait_for next ni callbacks ilimitados. Session revoke/shutdown y overflow wake readers; no cancelar jobs por lector cerrado. Gestionar carrera cancel/disconnect mientras DBtask attach sigue vivo: aguardar retorno nativo real y cerrar ticket/result aunque request ya cancelado, sin callback tardío huérfano.

**Navegador:** reemplazar EventSource por fetch(credentials:'omit')+ReadableStream+TextDecoder streaming, AbortController y cancelación idempotente. Bootstrap automático header1 sólo API_ORIGIN exacto antes GET; credencial sólo memoria, reinicio/401→bootstrap acotado; no tratar401/403/422/SNAPSHOT_LIMIT como retry loop infinito. Retry transitorio backoff acotado+una sola conexión, cancelar sleeps/readers al stop/scope change, idle deadline acorde heartbeat. Sólo enviar Last-Event-ID de cursor confirmado en scope actual. Validar URL exacta `/api/events` y allowlist de query; old test `/events` no es una ruta productiva compatible por accidente.

Parser limitado64KiB UTF8/frame, filas/buffer residual acotadas, límites antes concat; CRLF/LF y UTF8 fragmentado, comentarios heartbeat, event/data/id; rechazar ID que contradice JSON id o type nombrado. Frame normal id epoch:seq concordante seq body.id; no exigir consecutividad porque filtro salta seq. Invalid frame closes/discards/reconnect desde último cursor confirmado, no silentignore avanzando. begin/chunk/end puede repetir H; begin/chunk sin id y sólo end confirma. Reducer staging≤1064 jobs, snapshot_id/indices/counts/cursor/epoch/H coinciden, únicoid; end válido reemplaza mapa del scope en UNA actualización y confirma cursor. Interrupción descarta staging y conserva cursor anterior; eventos posteriores se aplican después end, no mezclar mapa antiguo/parcial. KnownIDs mantener≤64 elegibles de cards que necesitan terminal: no descartar indefinidamente una tarjeta running por tener65; reconsulta/paginación UI requiere diseñoT07/T10 si supera ventana, no inventar terminal. `subscribeEvents` puede conservar wrapper cleanup/callback para eventos normales, pero snapshot requiere callback/estado atómico nuevo explícito; no fingir atomicidad emitiendo64 callbacks por chunk. Consumidores productivos no encontrados, sólo tests del helper; introducción cliente acotada está dentro T06.

# 6. Ownership e integración verificable completa

Root debe ampliar ownership T06 con writers después de entrega T05 revisada/QA y generar brief nuevo. No editar runtime/admission/resolver/provenance/contracts/retry mientras actor T05 los posee. No heredar SHA de esta inspección como versión aceptada: consultar drift.json y baseline actual al despacho. Se pueden preparar contratos/tests de nuevas rutas/parser en ficheros propios sin tocar cola; endpoint se habilita sólo con barrera allwriters conectada.

| Frontera | Ownership propuesto exclusivo | Evidencia requerida antes aceptación |
|---|---|---|
| Writers compartidos | `publication.py`, `queue/admission.py`, `chains.py`, `cancellation.py`, `recovery.py`, `retry.py`, `manual_retry.py`, `events.py`, `runtime.py`; nuevo helper transaccional si evita duplicar rollback | RED SQLiteWAL concurrente escritor/boot, callback no ejecutado timeout, each writer/public-private/commitunknown/rollback/close/publish failure; invariantes T04/T05 y original80110s/counters intactos |
| Bootstrap/bus/auth | `queue/events.py`, `sse.py`, nuevo `event_feed.py`, `event_snapshot.py` sólo si API necesita; `local_sessions.py` si wake API | Ticket en loop + attach hilo/ownership; WAL pin/H/replay/bufferexpiry; reauth deleted/moved/revoke/expiry;1000/1001,64/65,frame bytes; no loops/sets/callbacks ilimitados |
| Route/contrato | `event_routes.py` y/o nuevo `event_stream.py`, `main.py`, `security.py`, `errors.py`, `api_models.py`, contracts/openapi/generated client, tests session+sse nuevos | Compatcodefirst, Origin/headerduplicate/simplepreflight/GET auth; real ASGI send30/disconnect15keepalive/slowreader/shutdown; no route200 anteserror |
| Browser | `apps/web/lib/events.ts`, tests actuales preservados/actualizados con semántica fetch; nuevos parser/reducer/session módulos y tests si facilita claridad | UTF8/CRLF fragmentación,malformedID/frame cap,401/errors/backoff,Abort,filterreset,atomicbegin/end,knownterminal,tokenmemory; no tests que sólo espejen función |
| Aceptación end-to-end | Root ledger/testing docs; QA independiente ejecuta app HTTP y navegador Docker | E2E01 generación-real-mock etapas/terminal/take+waves y E2E06 disconnect/restart/expiredcursor; pruebas allwriters con snapshothandoff; no GPU/M01 musical por mock |

Estas fronteras tienen solapamientos `events.py`/main/contracts: ownership secuencial o único integrador, no workers paralelos sobre mismos archivos. No justificar cierre por cada componente aislado. Tests que cubren sólo helper no demuestran endpoint/allwriters/cliente. Fixtures T05 delivery actual y antiguos RED/learnedSHA/deadlines conservados; fuente entera WHOLE≥80 sin exclusiones para cada archivo producción modificado, revisión A/B/Cseguridad/Dperformance y QA independientes antes Docker/E2E.

# 7. Riesgos, dependencia y evidencia acotada

GateRoot: elegir O1/M1 metadata o alternativa, SNAPSHOT_LIMIT/códigos y política scope-change enforce sólo cliente vs nueva serverbinding. No se implementa política nueva por inferencia. GateT05: ownership liberado y fuentes actuales aceptadas; diseño allwriters actualizado tras cambio actual de candidate projection/resolver authority, sin revertir. GatefuturoCPU: registrar mutadores reales cuando existan antes de exponerlos. GateE2E: cliente fetch y producto Docker; ninguna ejecución acreditada aquí.

Riesgos concretos: RLock en eventloop/await retenido, DBwriter antes coordinator, thread subscribe sinloop, heartbeat cancelnext, leak tras cancel attach, readBEGIN sinSELECT pin, snapshot truncado, stalecert replay, publicationfailure resubmission, oldfiltercursor, EventSource sin token, transport tests sólo in-process buffering, filesystemfinalchecks movidos/ignorados, todo método candidates con batch>1064, error stage fuera label que no debe convertirse en progreso inventado.

Primera ventana before/after:63fuentes, cambios sólo `tasks.md` y `integration-readiness.md`; ninguna fuente producto del inventario cambió en esa ventana. Se releyó readiness actualizado: incorporó explícitamente incompatibilidad EventSource/header y fetch/atomic reset, congruente con este diseño. No se reinterpreta el ledger nuevo como aceptación. Receipt final conserva cualquier drift posterior, sin convertir una baseline T05 vieja en current.

**Despacho frontend independiente disponible ahora:** ownership `apps/web/lib/events.ts`, `events.test.ts` y nuevos `event-parser.ts`, `event-parser.test.ts`, `event-reducer.ts`, `event-reducer.test.ts`, `event-session.ts`, `event-session.test.ts` si el implementer necesita dividir responsabilidades; fuera de ownership `api.ts`, `api.d.ts` generado, package/locks, server/cola y docs. Usar tipos explícitos de propuesta actual/DTO, no generar canónico antes handler ni confiar en JSONsinvalidar. PrimerRED fetchmock con header y lectura real de chunks UTF8, reducer snapshot interrumpido sin cursor; continuar parser/framebounds/abort/filterreconnect/retry/status/privacy. Actualizar pruebas EventSource a transporte aprobado, conservar comportamiento de privacidad/fecha/ID/cierre y documentar cambio de `/events` a `/api/events`; no dejar pruebas viejas skip ni assertions debilitadas para alegar backwardcompatibility ficticia. Esta unidad será componente cliente, no integración app/HTTP/E2E ni cierreT06; Root puede despacharla mientras T05 mantiene cola.

Inventario SHA/tamaño before/after en sources-before.json/sources-after.json; drift.json identifica cambios concurrentes sin aceptarlos. Brief exit0 real y aviso intacto; inspección de fuentes/propuesta solamente. DoD prosa: siete secciones, sin placeholders guía; elección/ADR pendienteRoot, no diseño aprobado. Tokens/modelo/EUR/horasIA null. Handoff integración completa con ownership separado y tests anteriores por ejecutar, no cierreT06.
