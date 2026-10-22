> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Clasificación estática acotada — ADR-0060 / compatibilidad mock

OWNED `[]`. Ningún cambio de producción, fixture, test, docs, ADR o ledger; ninguna ejecución/importación Python ni test. TDD n/a: análisis estático. La baseline original sigue **288 = 213 PASS + 75 FAIL; nuevos 54 PASS; gate WHOLE seis FALSE**. No se rehízo. Tabla completa al final; detalle individual sin trazas en `failure-classification.json`.

**Recomendación:** Root debe decidir una variante explícita de evidencia sintética con binding confiado del server. No añadir pesos ficticios al mock, aceptar SHA inválidos ni dar confianza por `family`. Después, preparar fixtures válidas sin tocar sus assertions. La incompatibilidad de contratos está identificada estáticamente; su causalidad en el producto aún NO está probada por ejecución.

## 1. Dos bloqueos distintos, no 75 bugs demostrados

Los **67 `Invalid immutable engine request`** llegan a `resolver.py:314–322`: `SelectedProvenance.select` → `CapturedDescriptor` (`worker/contracts.py:158`) exige pesos; `provenance.py:74` además rechaza el digest `synthetic`. El primer rechazo impide observar el segundo. Los builders compartidos son `test_queue_resolver.py:13 descriptor`, `:48 Catalog` / `:57 health`; HTTP usa `test_queue_backend.py:111 health`. Las cadenas pasan por `test_queue_chains.py:20 services` / `:47 create`; admisión/recovery por `test_dispatcher_admission.py:252 resolve`. No son 67 motores reales ni 67 verificaciones de pesos fallidas.

Los **otros 8** son seis assertions de dispatch (busy_cpu, cuatro ACK, gpu-False-False), una expectativa de lifespan consumido y una assertion de shutdown. Sus fixtures también usan descriptor sin pesos/digest synthetic. `Dispatcher` puede convertir el rechazo de resolución en `None`; eso explica una hipótesis concreta para las assertions, no demuestra todos sus caminos. Tras desbloquear selección, los handlers positivos todavía devuelven `loaded=None` después de un ACK de load: el Health fresco exige residente coincidente en GPU (`provenance.py:88`). `RecordedBackend.load` devuelve un ACK pero no registra residencia. Mantener busy/foreign/unload_lie como estados realmente observados; una bandera de éxito no basta.

**Bug de compatibilidad candidato real:** `engine_mock/__init__.py:77 descriptor` declara id/family mock, revision synthetic-v1, weights [], training_data sintético, modo CPU y tareas CPU. `engine_common/server.py:406` declara digest `unknown` por defecto. Contrato público `ModelDescriptor.weights` permite lista vacía (`engine_contract/__init__.py:227`); ADR-0037 y contrato-engines §7 requieren ese pipeline. El mock real tropieza con la exigencia privada de pesos, no necesita un digest `synthetic` permitido. Ningún bug adicional de cola ha quedado probado; conservar prioridad/FIFO/capacidad/cache/CAS/request/rights/índices.

## 2. Decisión precisa que Root puede adoptar

Propuesta de adición a ADR-0060, sin modificarlo aquí: «La procedencia aprendida mantiene descriptor con identidades de pesos seguros fijados y hashes válidos. La procedencia sintética se distingue explícitamente, declara ausencia de entrenamiento/pesos y nunca acredita ejecución aprendida ni controles efectivos. Solo el server puede admitirla mediante binding confiado a backend configurado, origen, identidad contractual y fingerprint exacto del descriptor/implementación sintética registrados antes de leer el catálogo. La identidad recibida no otorga autoridad. La captura conserva esa clasificación y binding en su SHA y publicación. Digest de imagen desconocido continúa null; conocido inválido/discrepante se rechaza también para mock. Recovery no reconstruye evidencia legacy NULL».

Preferir variante privada tipada **dentro de `CapturedProvenance`**, con rama aprendida por defecto compatible con JSON histórico y rama explícita `evidence_kind=synthetic`, descriptor sintético separado y referencia al binding. `CapturedDescriptor` aprendido conserva su requisito de pesos. No cambiar `/v1`, DDL ni `WorkerJSON(CapturedProvenance)` (`models/__init__.py:483`). No usar un union que acepte sin más el descriptor más permisivo: selección explícita, rama validada y revalidación de autoridad son obligatorias. Un fingerprint en JSON es dato, no permiso; debe cotejarse con registro inmutable propiedad del server al seleccionar, capturar y reenviar. No confiar en class name, URL parecida, string family, hash recibido o proveedor externo.

Binding de producto: backend local configurado para engine-mock, origen exacto y engine_id/version/contract, descriptor canónico de **la función real `engine_mock.descriptor()`**, implementación fijada desde fuente/build de confianza. CPU, pesos vacíos y declaración sintética exactos. Fuente/build declarados no prueban qué código ejecutó un contenedor ni son image_digest. Si no existe autoridad de imagen configurada, expected_digest=null. No ampliar aceptación de SHA conocidos malos.

Las fixtures GPU antiguas son un catálogo sintético de pruebas, **no** el descriptor CPU del producto. Preservar bf16/offload, VRAM, schemas y request originales. Registrar explícitamente cada variante declarada mediante composición de test, fingerprint previo a las mutaciones y ámbito de prueba; nunca autogenerar binding desde el catálogo mutable ni exportarlo a configuración de producto. Los negativos que cambian descriptor/identidad deben seguir llegando a su guarda prevista. Si el binding añade rechazo anticipado, construir una variante declarada válida antes de la mutación de la condición objetivo; conservar la mutation negativa y documentar qué guarda se alcanzó. No fingir pesos ejecutados.

**Ownership propuesto, pendiente de Root:** unidad de compatibilidad máximo seis ficheros: `app/worker/contracts.py` (rama privada), `app/queue/provenance.py` (registro/binding/captura), `resolver.py` (selección explícita), `admission.py` (binding vigente al CAS), `runtime.py` (recovery con autoridad registrada), `retry.py` (propagación al nuevo intento). `dispatcher.py` consume los helpers actuales sin necesitar un nuevo bypass. Engine mock, modelos/DDL, contrato público, SSE y métricas quedan fuera. Si el camino exige tocar dispatcher, Root sustituye una responsabilidad o abre otra unidad; no ampliar silenciosamente seis. Cualquier adaptación del manifiesto va en unidad posterior con schema y consumidor acreditados; no afirmar que esta unidad ya publica.

## 3. Handoff exacto de fixtures y assertions

F en tabla = bloqueo de builders compartidos. C = captura previa auténtica. H = Health/residencia. R = identidad del Resident de prueba. Cada fila representa todas sus parametrizaciones fallidas exactas; JSON enumera **75/75** con línea de definición y ubicaciones de la traza. No se incluyeron trazas completas.

1. `descriptor():13`: mantener weights [], entrenamiento sintético, task/params/features/modes/version/revision/rights. Añadir binding explícito por fixture declarada; no inventar identidades de pesos. `Catalog.health():57` y HTTP `health():111`: sustituir digest marcador synthetic por **unknown** porque no existe digest de imagen observado; dejar engine/version/contract/VRAM/busy/job intactos. Actualizar coherentemente literal identity de `Resident` en admission:561; tampoco es un digest acreditado. `services():20` conserva los cambios declarados a CPU/inputs antes de registrar su variante y congelarla.
2. Handlers admission:113, :315, :441 y lifespan:25: mantener `resident=None` inicial; load valida request model/mode, registra `LoadedModel` exacto y retorna ese mismo ACK; health devuelve el residente registrado. No cambiar las ramas foreign/busy. `Fake.load():537` ya hace esto; conservarlo. `RecordedBackend:34` necesita la misma transición y Health. Submit/events/status continúan con sus registros y errores originales. No cargar en CPU por comodidad; CPU unloaded queda observed_model=null.
3. `prepared():64`: resolver → reserve → load del backend declarado de setup → **Health fresco** → `capture_before_send(claim.selected_provenance, claim.request, claim.load_options, health, require_loaded=True)` → `capture_provenance(claim, value, canonical_sha256(value))`; comprobar may_send antes del envío perdido simulado. Retornar el mismo claim bound, ID, request y options. No usar SQL para inventar captura, ni cargar datos actuales durante recovery. El backend de recovery debe compartir la variante registrada y reportar honestamente su estado; las mutaciones cursor/partial/foreign/unverified/etc. vienen después de la preparación válida.
4. `accepted():18` en referencias: añadir esa preparación si representa generación previamente enviada, antes de inyectar el terminal; no alterar los bytes sintéticos, índices, paths, edges, seed ni artifact_mutator. La actual reserva sola no prueba envío. Los casos reserve-only (prioridad, capacidad, CAS) **no** necesitan capturar para reservar y no deben exigir may_send como sustituto de su assertion. Guards de inputs/referencias/rollback mantienen sus negativos después de un setup válido.

**Assertions a cambiar: ninguna recomendada para estos 75.** `test_absent_zero_cursor_resubmits_same_frozen_id` sí presupone antes un éxito sin evidencia porque prepared guardaba NULL; preparar captura previa restaura su intención de lost-ACK sin alterar `len(posts)==1` ni identidad congelada. El caso alias done tiene registro terminal existente y no requiere reenvío/backfill. Los nueve uncertain necesitan preparación válida para no pasar por un NULL que enmascare cursor/VRAM/etc.

Si Root decide mantener **ese mismo caso** como legacy NULL, la única modificación semántica propuesta requiere autorización específica: en recovery:98 cambiar la expectativa de un POST por cero, conservar ID/request/ordinal/cursor y exigir estado interrupted/capacidad retenida/pareja NULL. Base primaria ADR-0060 «no completa retrospectivamente» y runtime:268–291 rechaza NULL en resend. Crear además un caso positivo capturado con la assertion original. Preferencia: conservar el original positivo y cubrir legacy en un caso separado; no alias privado que oculte el cambio.

No hay llamada directa antigua `Admission.may_send` entre las fuentes de los 75. Búsqueda acotada queue/dispatcher encuentra la positiva nueva capture:54 (precedida de captura) y negativas :79/:215. Retry:137 sustituye may_send por bool según número de llamadas: ese bool no acredita evidencia/residente; mantener intención de negar efectos con setup auténtico y delegación a la guarda real para caminos permitidos. Ese fichero no figura entre los 75 y no se propone cambiar sus assertions ni declarar probado su comportamiento.

## 4. Próxima prueba causal y límites de aceptación

Antes de implementar, Root autoriza **una regresión de producto**: descriptor real `engine_mock.descriptor()` sin alterar; backend de transporte explícito/adaptador real, SQLite real migrado, petición CPU musical con seed/n_outputs/params intactos. Resolver/Admission/Dispatcher deben llegar a submit con procedencia sintética bound persistida y SHA exacto; hoy la hipótesis predice rechazo por weights[]. Assert de comportamiento/durabilidad, no ausencia de API/import/classname. Archivar fuentes/fixture/runner antes y registrar argv/UTC/exit/stdout/stderr/JUnit. Este informe no ejecuta ese RED ni lo llama demostrado.

Después, casos de suplantación (family mock externo/no binding, descriptor/build/origin cambiado), learned weights[]/SHA inválido, imagen knownbad, write-once distinto, CPU unknown y retry/resend bound. Preservar los **74 contratos históricos**: worker_contracts:129 válido/inmutable; :184 mismatches/unverified/extra/secrets/version; :191 unknown separado/detached; :342 weights[] aprendido rechazado; :362 límites; :387 null load/observed y roundtrip. Public test_contract:8 admite descriptor vacío y preserva remote_code con rechazos; no fusionar eso con evidencia aprendida. No se ejecutaron ni recuentan 74 aquí.

Prueba real SQLite/request/**manifest** posterior: generar WAV con adapter mock real, consumir terminal auténtico, preparar/publicar con pipeline actual y verificar manifest real/JSON Schema/índices/semilla/linaje/etiqueta sintética. Si la publicación aún no está implementada, gate pendiente: no suplirla con dict fake ni asegurar GREEN. Captura solicitada/observada no permite añadir LM/DiT efectivos inventados. No simular verificación de pesos ejecutados; los hashes de ejemplos de contratos son datos declarados sintéticos.

Tras cambios nuevos, baseline apropiada una vez cuando Root libere; los 54 verdes se conservan, no se redescubren. WHOLE actual seis proviene de baseline fallida, sin aceptación: admission 84.126984, dispatcher 69.731801, provenance 96, resolver 86.580087, retry 77.372263, runtime 76.551724%, cero exclusiones. Gate FALSE. La unidad nueva necesita cada runtime cambiado >=80 en trace fresco único; no promedios ni exclusiones. U1 nativo fallido/H1 UNKNOWN no justifica debilitar cola ni omitir original801; los permisos de ejecución siguen reservados a Root.

## 5. Custodia y contabilidad

41 entradas acotadas copiadas/hashadas, 0 drift durante snapshot before/after; el inventario no pretende incluir dependencias irrelevantes ni TCB ejecutado. Primeras lecturas precedieron copias. **Error de límite inicial:** First180 de CONTINUE cruzó Historial (línea128); se conservó solo extracto vigente después. Algunos outputs iniciales truncados y errores de rutas/sintaxis están declarados en accounting, no son RED de producto. No hay garantía before-first-read ni freeze global frente a actores ajenos. Hashes de fuentes exactas y diez guards de Root se verifican separadamente; SSE/métricas no se tocaron, no se inventa auditoría de su árbol.

Solo outputs privados en esta carpeta. Archivos CLI reservados intactos; modelo/tokens/EUR/horas IA NULL sin originales. Ningún proceso nativo propio: cleanup no aplica. No aceptación T-05/fulltask/GPU/UI/E2E ni decisión de ADR/ledger. Root conserva decisiones, review fresca y QA.

## Tabla compacta de los 75 fallos

| Casos originales (nombre exacto; parÃ¡metros originales) | n | Fuente: lÃ­nea | Clase / preparaciÃ³n |
|---|---:|---|---|
| `test_queue_resolver_frozen_request_exact_text_cpu_lane` | 1 | test_queue_resolver.py:105 | F |
| `test_queue_resolver_cache_ttl_identity_down` | 1 | test_queue_resolver.py:192 | F |
| `test_queue_resolver_null_seed_freezes_concrete_seed` | 1 | test_queue_resolver.py:245 | F |
| `test_queue_resolver_explicit_healthy_after_unavailable` | 1 | test_queue_resolver.py:257 | F |
| `test_queue_chain_atomic_variants_and_real_edges` | 1 | test_queue_chains.py:61 | F |
| `test_queue_chain_midinsert_rollback` | 1 | test_queue_chains.py:148 | F |
| `test_queue_chain_declared_lyrics_version_exact_owned_text` | 1 | test_queue_chains.py:166 | F |
| `test_queue_admission_unblocks_only_available_dependencies` | 1 | test_queue_references.py:57 | F |
| `test_queue_references_winning_attempt_delegate_bytes` | 1 | test_queue_references.py:70 | F |
| `test_queue_references_reject_before_reserve [changed_bytes, missing, duplicate_index, wrong_index, wrong_path, missing_edge, wrong_song, unknown_attempt, hardlink]` | 9 | test_queue_references.py:98 | F |
| `test_queue_t05_completion_injection_beats_cpu_no_gpu_unload` | 1 | test_queue_references.py:141 | F |
| `test_queue_failed_parent_propagates_chain [failed, cancelled]` | 2 | test_queue_references.py:195 | F |
| `test_queue_references_400_ready_beats_native_query_bound` | 1 | test_queue_references.py:303 | F |
| `test_queue_references_shared_64_post_inputs_native_query_bound` | 1 | test_queue_references.py:323 | F |
| `test_queue_references_finite_801_ready_beats_detached` | 1 | test_queue_references.py:351 | F |
| `test_queue_references_preloaded_native_identities_remain_authoritative [asset_ref, duplicate_asset, deleted_take, deleted_asset, wrong_role, duplicate_ref, bad_item, bad_identity, bad_type, unknown_kind, missing_post_binding]` | 11 | test_queue_references.py:399 | F |
| `test_queue_references_window_never_trusted_across_transactions_or_polls` | 1 | test_queue_references.py:464 | F |
| `test_dispatcher_available_lanes_native_http [busy_cpu, gpu_head]` | 2 | test_dispatcher_admission.py:89 | F+H |
| `test_dispatcher_admission_priority_dates_support_and_dependencies` | 1 | test_dispatcher_admission.py:262 | F |
| `test_dispatcher_admission_two_native_connections_capacity [gpu-1]` | 1 | test_dispatcher_admission.py:280 | F |
| `test_dispatcher_first_http_post_durable_and_writer_released [valid, unknown, timeout, cancel]` | 4 | test_dispatcher_admission.py:311 | F+H |
| `test_dispatcher_uncertain_support_running_counts_global` | 1 | test_dispatcher_admission.py:412 | F |
| `test_dispatcher_never_unloads_unknown_model_or_cpu [gpu-False-False]` | 1 | test_dispatcher_admission.py:430 | F+H |
| `test_dispatcher_gpu_switch_residence_proof [foreign_loaded, foreign_busy, owned, unload_lie, free_insufficient, identity_changed, cpu_active]` | 7 | test_dispatcher_admission.py:504 | F+R |
| `test_dispatcher_selection_and_cas_changes [cancel, deleted, request, owner, remote, not_before, nightly, budget, pending]` | 9 | test_dispatcher_admission.py:758 | F |
| `test_absent_zero_cursor_resubmits_same_frozen_id` | 1 | test_dispatcher_recovery.py:90 | F+C |
| `test_configured_family_alias_reconnects_only_matching_engine` | 1 | test_dispatcher_recovery.py:110 | F+C |
| `test_uncertain_recovery_retains_capacity_and_cursor [cursor, rollback, partial, status_failure, foreign, wrong_identity, unverified, noncommercial, vram]` | 9 | test_dispatcher_recovery.py:155 | F+C |
| `test_configured_lifespan_consumes_real_terminal` | 1 | test_dispatcher_lifespan.py:21 | F/H |
| `test_shutdown_awaits_native_writer_and_cancels_slow_stream` | 1 | test_dispatcher_lifespan.py:351 | F/H |
