# Límites propuestos, sin estado de tareas

Prerequisito de dispatch: root acepta fix/revisión2/QA de primera unidad; pin nuevo de fuentes aceptadas. Estas seis copias son evidencia de diseño, no permiso para implementar sobre modelos cambiados. Root decide O1/O2/O3 y actualiza rutas documentadas si procede.

## Unidades funcionales recomendadas (O1)

| Unidad | Ownership futuro exacto | Pruebas nuevas exactas | Resultado y aceptación acotada |
|---|---|---|---|
| U1 | `apps/server/app/queue/__init__.py`, `backends/__init__.py`, `backends/protocol.py`, `backends/http.py`, `resolver.py`, `admission.py`, `dispatcher.py`; extensión compatible `app/engine_client.py` | `apps/server/tests/test_queue_backend.py`, `test_queue_resolver.py`, `test_dispatcher_admission.py` | Dos conexiones competidoras: GPU1/CPU2, priorité/FIFO, fechas/deps; ningún HTTP bajo writer; reservar intento congelado y POST/ACK/status reales mediante transporte httpx sintético, sin doble reserva. Selector excluye soporte/ajenos. Resolver negativo y unload mock. U1 no es sólo harness: toma job elegible, congela intento, envía y deja estado reconciliable. |
| U2 | `apps/server/app/queue/events.py`, `recovery.py`, `retry.py`, `cancellation.py`; extensión `dispatcher.py`, integración `app/main.py`; `event_store.py` y extensión schema sólo si root aprueba necesidad | `apps/server/tests/test_dispatcher_events.py`, `test_dispatcher_recovery.py`, `test_dispatcher_retry.py`, `test_dispatcher_lifespan.py` | Eventos/efectos/cursor en TX, fallo commit/replay/SSE, quiet stream, límites3/offload1, restart confirmado, ACKunknown, cancel race, shutdown y reanudación sin regenerar éxito. No cierre CPU post real. |
| U3 | `apps/server/app/queue/chains.py`, `references.py`, `manual_retry.py`; extensión `admission.py`/`dispatcher.py` | `apps/server/tests/test_queue_chains.py`, `test_queue_references.py`, `test_queue_manual_retry.py` | Creación atómica generation→post→beats N, semilla+i, refs exactas al desbloquear, owner/song, dependencias fallidas/canceladas y manual job nuevo sólo takes failed. Boundaries T05 fake explícito, sin fabricar assets ni ready. |

Archivos compartidos se entregan secuencialmente; no ownership paralelo. Ningún subagente toca ledger. O2 sustituye prefijo `app/queue` por `studio_queue`, añade pyproject a U1 y conserva los mismos tests. O3 fusiona U1/U2; mismo ownership, gates más grandes.

Si root aprueba nuevas estructuras: ownership adicional exclusivo en U2 `apps/server/app/models/__init__.py`, nueva migración posterior a head aceptado en `apps/server/app/migrations/versions/`, `app/snapshots.py`, `packages/contracts/song-v1.json`, `apps/server/app/contracts/song-v1.json`, `apps/server/tests/test_queue_runtime_schema.py`. Root fija número/nombre de migración tras custodiar schemafix1; no se presupone 0006 ni se edita 0005. Nueva revisión de invariantes SQL directos/ORM/restore obligatoria, no tocar test ajeno histórico. Este alcance extra puede justificar separar extensión schema como prerequisito explícito; no fingir que ya cabe en primera unidad.

## Cobertura final de las ocho CA T04

| CA (orden tasks:183–190) | Unidad y evidencia requerida |
|---|---|
| 1 GPU1/CPU2, prioridad/FIFO/not_before, CPU beats | U1 concurrencia/admisión; U3 beats; probar no unload de GPU para CPU |
| 2 protocolo nueve métodos HTTP | U1 wire, fallos/control/stream; U2 conexión del consumo |
| 3 cadena N + refs | U3 TX íntegra, rollback, seeds, post completion inyectado; T05 integration posterior |
| 4 resolver verified | U1 descriptor/cache/params/negativas; U3 inputs recién resueltos |
| 5 unload/freeVRAM | U1 mock transición y fallo; live GPU futuro no certificado |
| 6 NDJSON stage/progress/telemetry/bus | U2 replay, atomicidad, bus after commit; endpoint T06 posterior |
| 7 retries2/offload1 | U2 error terminal durable, presupuesto y descriptor |
| 8 recovery/manual/variantes | U2 recovery + U3 manual; I-01 M0 aún abierto |

## Protocolo propuesto (tipos existentes, DTO local sólo cuando falta)

Async `EngineBackend`: `health()->Health`; `models()->list[ModelDescriptor]`; `load(LoadRequest)->LoadedModel`; `unload()->UnloadResult(freed_mb)`; `estimate(JobRequest)->Estimate`; `submit(JobRequest)->Submission(job_id)`; `status(attempt_id)->JobStatus|ConfirmedAbsent`; `events(attempt_id,after)->AsyncIterator[Event]`; `cancel(attempt_id)->CancelAck`. Últimos DTO documentan exactamente body/status nativos antes de implementación: el contrato escrito no especifica todo load/cancel/404; no validar falsamente load como Health o fabricar terminal desde CancelAck. Los nueve métodos son los endpoints de contrato-engines §2, con status incluido por T04 aunque §6 lo omita.

HTTP reutiliza httpx0.28.1 y `engine_contract`. AsyncClient equivalente de engine_client conserva token desde Settings en memoria, destino exacto, trust_env=False, redirects=False. No creds en descriptor/request/options/DB/event/log; no .env extra ni defaults externos. Cierre explícito de clientes; dispatcher no importa implementación HTTP. Rutas fijas y ULID validado, media/content-type/body validados antes de éxito; HTTP error no es evento terminal engine.

Propuesta de deadlines (valores de política a probar, no medición): connect/pool/write10s; controles read10s con deadline total30s; load con deadline acotado configurable según operación; stream read30s de silencio y deadline total del request congelado, ambos con reloj monotónico inyectado. `timeout_s` del engine no prueba que el proceso terminó al vencer localmente. NDJSON incremental, UTF8 y tamaño por línea/buffer limitados (propuesta1MiB), no `response.json()` del stream. EOF sin terminal/quiet timeout: cerrar socket, consultar status y reconectar desde last_seq durable con backoff acotado; no retry de generación. Status transport/malformed/authfailure es Unknown/ProtocolFailure, no ConfirmedAbsent. 404 válido conforme API exacta puede probar absent; 5xx/timeout no. Estado done sin terminal exige recuperar eventos, no inventar artifacts. Stream terminal se valida aunque status diga terminal.

## Resolver y VRAM

Cache de descriptores validada por origen+engine_id+engine_version+image_digest, TTL acotado/invalidation en cambio observado, load mismatch/MODEL_NOT_FOUND o refresh solicitado. Una caída invalida uso para nueva selección; no altera intentos congelados. No implica boot identity. Filtrar local/default comercial, task verified y features usadas verificadas; mock explícitamente sintético. Validar params_schema/limits, roles/media/hashes y mode declarado; opciones load congeladas sin secretos. No corregir silenciosamente parámetros ni elegir nuevo modelo en ACKunknown. Offload requiere modo y capacidad adecuados del descriptor, no sólo substring.

GPU switch mantiene claim global mientras unload→health loaded=None, free_mb suficiente y cap libre−margen. Un aumento aislado de free_mb no demuestra exclusión ajena ni modelo descargado. Consumidor externo puede variar VRAM: no lanzar ante observación insuficiente; backoff/sin intento nuevo. CPU beats no unload/load GPU por defecto. Engine ocupado por job ajeno: BUSY, no cancel/unload ni apropiación. Un engine único puede rechazar CPU mientras busy GPU; el límite CPU2 es global, no promesa de2 jobs por engine.

## Variantes, post y aceptación futura

Documentado: una generación N, toma i seed+i, un post.audio sobre N y N beats. Contrato permite batch o serie por adapter; ninguna fuente revisada elige fallback de producción. Staging conservador: mock N para cadena; generación real deshabilitada hasta verified; propuesta de adapter serie1 a la vez conserva un request N e índices globales. No partir N en job_attempts secuenciales: son retries, máximo3, no variantes. Implementar serie del adapter requeriría ownership separado y decisión root según M0; no pertenece a esta unidad.

CPU `post.audio` utiliza interfaz inyectada `CpuExecutor.execute(job, winning_attempt, cancellation)`; completion durable idempotente por job/take/asset-kind. U3 fake no produce takes ready; fixture explícita de completion permite probar desbloqueo. T05 posee FFmpeg/assets/manifiesto/move/cleanup, T06 endpoint SSE y T07 endpoints dominio. Ningún evento artifact suelto dispara post. T05 debe reconciliar archivos ya movidos/manifiesto existente sin sobrescribir ni duplicar efectos tras crash.

TDD futuro: RED funcional por unidad, GREEN, cobertura ≥80% cambio sin exclusiones, revisión fresca A/B y C/D cuando aplican, QA independiente. Tests actuales no ejecutados en este diseño. Wheel futuro: build con toolchain existente offline, inspección contenido, instalar en venv privado fuera checkout con sin PYTHONPATH, imports normales de app.queue y stdlib queue/httpx/threading; migraciones/contratos incluidos. Docker futuro: mismo wheel/import/runtime con nombres de servicio y restart persistente. Son gates futuros, no resultados estáticos. E2E01/04/05/06/09 y M01 permanecen íntegros; path tmp contractual es attempt_id, texto histórico `<job_id>` no autoriza limpiar job lógico.
