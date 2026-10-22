---
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — M1 · MVP del estudio web

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-28 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | [design.md](design.md) · [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.
>
> **Apertura técnica:** ADR-0037 con revisión y QA documental conformes permite construir contra mock. **Aceptación final de M1:** M0/T-13 cerrado y todos los criterios reales/manuales cumplidos. Una tarea con criterio propio pendiente no se cierra. M1 reutiliza tal cual `packages/engine-contract`, `packages/audio-post`, `packages/weights`, el escritor del manifiesto, `engine-mock`, `engine-acestep` y `engine-analysis`.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 0 — Secuenciación | 0 | 1 | 0% | — | — | — | — |
| Fase 1 — Server base | 0 | 3 | 0% | 0 / 20h | 0 / 10h | 0 / 2.5h | 0 / — |
| Fase 2 — Cola y post-proceso | 0 | 3 | 0% | 0 / 26h | 0 / 13h | 0 / 3.3h | 0 / — |
| Fase 3 — API de dominio | 0 | 1 | 0% | 0 / 12h | 0 / 6h | 0 / 1.5h | 0 / — |
| Fase 4 — Web | 0 | 7 | 0% | 0 / 86h | 0 / 43h | 0 / 10.8h | 0 / — |
| Fase 5 — Pruebas y cierre | 0 | 2 | 0% | 0 / 9h | 0 / 4.5h | 0 / 1.1h | 0 / — |
| **TOTAL** | **0** | **17** | **0%** | **0 / 153h** | **0 / 76.5h** | **0 / 19.2h** | **0 / —** |

---

## Fase 0 — Secuenciación

**Estado**: en-progreso · **Estimado**: — · **Real**: —

### T-00 — Apertura técnica condicionada y aceptación real preservada

- **Descripción**: Registrar la decisión de secuenciación tomada por el orquestador bajo delegación del propietario y armonizar gates sin sustituir escucha, GPU ni verificación de capacidades.
- **Estado**: en-revision
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: spec M1 aprobada; delegación vigente del propietario
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-09-28-m1-mvp-estudio/*.md`, `docs/roadmap/README.md`, `docs/decisiones/ADR-0037-avance-tecnico-condicionado.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md`; evidencia `.cache/dev-cycle/m1/technical-sequencing-design/` y `testing/t00/`
- **Verificación**: `uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/m1/verify-sequencing-docs-root.py` → enlaces/coherencia y ledgers conformes; revisión independiente A/B sin gaps pendientes.
- **Cubre (tests)**: DOC-00

**Criterios de aceptación**
- [x] ADR/diseño/gates distinguen construcción técnica y aceptación real, sin atribuir O2 específicamente al propietario.
- [x] M0/T-13, capacidades reales, I-01, M-01/02/03 y umbrales de uso real se conservan como evidencia pendiente; no se inventa calidad ni cierre.
- [x] Revisión A/B y QA documental conformes; fuentes28 de GPU160 intactas y estados solo en ledgers.

**TDD n/a: prosa y secuenciación.** No horas/coste retrospectivos inventados. Estado en progreso; Git e implementación de M1 pendientes.

---

**Verificación ejecutada — 2026-10-07:** helper declarado exit0, 9 documentos/482 enlaces/0 errores, fuentes28 intactas. Ledgers M0 0/7 avisos futuros y M1 0/0; A+B sin gaps. [QA](testing/t00/qa-report.md). Criterios documentales conformes; integración Git pendiente, no tarea completada.

## Fase 1 — Server base

**Estado**: en-progreso · **Estimado**: 20h · **Real**: —

### T-01 — Esqueleto del server: configuración, seguridad local y logs

- **Descripción**: App FastAPI con la configuración `STUDIO_*`, validación de `Host` y `Origin`, CORS con lista cerrada, errores `problem+json` y logs JSON.
- **Estado**: en-revision
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: contratos `/v1` y engine-mock disponibles; secuenciación ADR-0037 revisada y QA documental conforme. M0 cerrado se conserva para aceptación final de M1/T-16.
- **Tipo**: backend
- **Archivos**: `apps/server/` (`main.py`, `settings.py`, `errors.py`, `security.py`, `logging.py`, `Dockerfile`), `docker-compose.yml`, `uv.lock`, `docs/legal/licencias.md`, tests
- **Cubre (tests)**: API-01
- **Verificación**:
  - `uv run pytest apps/server -k "security or errors or settings" -q` → verde
  - `curl -s -o /dev/null -w "%{http_code}" -X POST -H "Origin: http://evil.test" http://127.0.0.1:8000/api/songs` → `403`

**Criterios de aceptación**
- [x] `pydantic-settings` con las variables de [convenciones.md](../../arquitectura/convenciones.md) §4. `STUDIO_ENGINES` se interpreta como un mapa familia→URL.
- [x] `STUDIO_ALLOWED_HOSTS` con lista cerrada; Host único bien formado ajeno403 `INVALID_HOST`. Mensajes mal formados rechazados por el parser reciben400 según [ADR-0040](../../decisiones/ADR-0040-frontera-parser-http-y-aplicacion.md). Todo Origin presente debe ser el único `STUDIO_WEB_ORIGIN`; ajeno o duplicado403 `FORBIDDEN_ORIGIN` incluso en GET/HEAD. GET/HEAD ordinarios pueden omitirlo; SSE y los demás métodos lo exigen. CORS cerrado y sin exposición LAN ([ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md), [ADR-0038](../../decisiones/ADR-0038-rechazo-explicito-host-origin.md)).
- [x] Errores RFC 9457 con `code` estable. Logs JSON en `data/logs/server.log` con rotación.
- [x] Token de engines generado en `.env` la primera vez y enviado en `X-Studio-Engine-Token`.
- [x] Imagen del server sin torch y servicio Compose, rutas de datos persistentes dentro del proyecto y URLs internas de engines; arranque y configuración validables antes de T-08.

**Entrega técnica — 2026-10-07:** implementer fresco, 65pass/2skip Windows por permisos symlink; dos RED/GREEN reales en Linux. Cobertura oficial siete módulos completos196/197=99,49%, sin exclusiones; contrato15pass y Verificación59pass/8deselected, POST Origin ajeno403. Imagen final sin torch/paridad7fuentes; Compose propio server/mock, HTTP/token y cleanup conformes. 28fuentesT09/63versionespreviaslock intactas. RED de configuración, HTTP, logs, cliente y escapes documentados con argv/UTC/exits originales en recibo privado. No QA independiente ni tarea cerrada; revisión A/B/C/Nemesis pendiente.

**Fix1 — 2026-10-07:** RED individuales contra producción anterior: Host400≠403, GET Origin ajeno200≠403, Origin duplicado200≠403, Allow405 y WWW-Authenticate401 ausentes. GREEN86pass/2skip; cobertura siete módulos201/202=99,50%, cero exclusiones. Primeros RED añadieron fixtures privadas al directorio de implementación anterior por conftest; no sobrescribieron originales y runner posterior los confinó. Ruff salidas/exits0 sin UTC individual registrada. Raíz finaliza sellos del streamCLI tras terminar; sello previo no se atribuye al streamfinal. Docker corregido/QA independiente pendientes.

**QA1 independiente — 2026-10-07:** CPU86pass/2skip/cobertura201of202/gates0; reconstrucción Docker sin red no pudo descargar una dependencia fijada, original preservado y construcción con red para lock autorizada después. Runtime21criterios:19conformes/2gaps por Host duplicado400 antes deASGI frente a403 exigido inicialmente. Imagen corregida c51aaf/paridad7, torch ausente, mock200/401, curl403, dos sondas symlinkLinux, recursos/montajes/persistencia y cleanup acreditados. Probe inicial comparaba str con SecretStr y se corrigió sólo en privado; originales preservados. [ADR-0040](../../decisiones/ADR-0040-frontera-parser-http-y-aplicacion.md) corrige la ampliación del requisito: RFC9112 requiere400 para Host duplicado. Rebate/revisión fresca y suplementoQA pendientes; original QA con gaps no se reescribe.

**Aceptación técnica — 2026-10-07:** [QA independiente](testing/t01/qa-report.md) y revisión A/B/C conformes; rebate del parser A/B conforme, QA suplemento444comprobaciones/105enlaces. Verificación80pass/8deselected y curl403, Docker real/paridad7/sin torch/montajes/persistencia/cleanup propios. Todos los criterios técnicos acreditados; T-01 en-revisión por integración Git pendiente. ADR-0037 permite usar esta dependencia técnica para T-02/T-03 conservando la aceptación final de M1.

### T-02 — Esquema completo, migración inicial, FTS y backup

- **Descripción**: La primera migración Alembic con **todas** las tablas de [datos.md](../../arquitectura/datos.md) §1, triggers FTS5 y la tarea de backup diario.
- **Estado**: en-revision
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 5h · real —
- **Supervisión**: est. 1.3h (≈25 % IA) · real —
- **Dependencias**: T-01 con revisión/QA técnicas conformes; integración Git de ambos pendiente y aceptación final M1 conservada por ADR-0037. Diseño ADR-0041 elegido bajo delegación.
- **Tipo**: db
- **Archivos**: `apps/server/app/models/`, `apps/server/app/db.py`, `apps/server/app/snapshots.py`, `apps/server/app/backup.py`, `apps/server/app/migrations/`, `apps/server/alembic.ini`, `apps/server/README.md`, integración en `apps/server/app/main.py`, `apps/server/pyproject.toml`, `uv.lock`, `docs/legal/licencias.md`, `packages/contracts/song-v1.schema.json`, `packages/contracts/timeline-v1.schema.json`, tests
- **Cubre (tests)**: M-03
- **Verificación**:
  - `uv run alembic -c apps/server/alembic.ini upgrade head`, `downgrade base` y `upgrade head` con la misma configuración y una BD temporal privada → sin errores, tanto vacía como poblada
  - `uv run pytest apps/server -k "schema or lineage or fts or backup" -q` → verde

**Criterios de aceptación**
- [x] Tablas: `user` (fila `local`), `collection`, `song`, `lyrics_version`, `take`, `lineage_edge`, `asset`, `upload`, `analysis`, `artwork`, `character`, `character_ref`, `preset`, `video_project`, `video_character`, `shot`, `shot_version`, `render`, `export`, `job`, `job_dependency`, `setting` y `provider`. Todas con ULID, `owner_id`, `created_at`, `updated_at` y `deleted_at`.
- [x] SQLite en modo WAL con `foreign_keys=ON`. Tabla virtual FTS5 `song_fts`, mantenida por triggers.
- [x] `song.json` (esquema `song-v1`) se regenera al cambiar la canción y permite reconstruir sus filas.
- [x] Backup diario con la API nativa `sqlite3.Connection.backup()` en `data/backups/`, rotación propia de 14 días y restauración real de datos WAL/FTS; conserva la última copia válida si falla (ADR-0041).
- [x] Tests:
  - un take derivado tiene una arista en `lineage_edge` y un `root_id` correcto;
  - varios padres (crossfade);
  - papelera sin romper a los hijos;
  - FTS por letra.

**Preparación y contexto — 2026-10-07:** dependencias resueltas/sincronizadas en el entorno gestionado, ninguna versión anterior modificada. MarkupSafe3.0.4 quedó pendiente de fila legal y se registró antes del uso. Primer redispatch conserva RED real de esquema: test_schema_complete falló por23tablas ausentes,1failed0,32s; faltan UTC nativos individuales en ese original. No código de producción todavía. Segundo retorno NEEDS_CONTEXT por timeline-v1 inexistente; se autoriza crear el contrato ya previsto en datos.md/ADR-0019 dentro de T02 y se añade a Archivos. Límite de un redispatch del modo brief-only agotado: pasa al flujo normal implementer supervisado por raíz, no más redispatches ciegos. Se conservan ambos originales y se recaptura RED con argv/UTC/exits antes del código. RutaBD canónica data/db/studio.sqlite.

**Entrega para revisión — 2026-10-07:** [Implementación](testing/t02/implementation-report.md):23tablas; Alembic vacío/poblado0/0/0; Verificación27pass/206deselect, propia34pass/1skipLinuxcubierto, cobertura793/838sinexclusiones. Root22fuentes/71protegidos/4preimágenes/originales y CLIterminal conformes; Dockerwheel21SHA/torchausente/cleanup. Preocupación de escaneo/reconcile total porcommit a lente D. Helpers y SQL migración/README declarados en Archivos por empaquetado necesario. Revisión/QA/Git/M03 reales pendientes; T02en-progreso.

RED: apps/server/tests/test_schema_t02.py::test_schema_complete falló con 23 tablas ausentes · 2026-10-07
RED: apps/server/tests/test_persistence_t02.py::test_fts_current_lyrics_and_trash falló con no such table: song_fts · 2026-10-07
RED: apps/server/tests/test_persistence_t02.py::test_snapshot_roundtrip falló con Falta snapshot restaurable · 2026-10-07
RED: apps/server/tests/test_persistence_t02.py::test_backup_restores_wal_and_fts falló con Falta backup nativo · 2026-10-07
RED: apps/server/tests/test_persistence_t02.py::test_lineage_multiparent_root_and_trash falló con root_id distinto de la menor raíz de sus padres · 2026-10-07


**Aceptación técnica T02 — 2026-10-07:** [QA4 independiente](testing/t02/qa4-report.md).327pass/3skipsWindows, mismos3Linuxpass,30selecciónincluida, cobertura3módulos365/39492,64%0exclusiones/Ruff0. Root32fuentes/inventario/CLIterminal/5criteriosoriginales íntegros verificados. Wheel28/paridad/18CLIvacíaspobladas/reinicioDockerCPU/persistencia/FTS/backup/cleanuppropio conforme. Revisión4A/B/C/D0gaps. Unitqa-gate0; M1globalqa-gate1sinE2E, M03real/Git/T02cierrependientes. ADR0037permite usar dependencia técnica: main/settings/errors se transfieren a T03API sobrebaselinecongelado aceptado; modelos/migraciones/snapshots quedan intactos hasta propia siguienteunidad.
### T-03 — Contratos exportados y parser de letras compartido

- **Descripción**: `openapi.json` code-first versionado, generación de tipos TypeScript y parser de etiquetas en Python y TS sobre los mismos casos.
- **Estado**: en-revision
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `scripts/export_contracts.py`, `packages/contracts/openapi.json`, `packages/contracts/lyrics-cases.json`, `apps/server/app/lyrics.py`, integración coordinada en `apps/server/app/main.py`, `apps/server/app/settings.py`, `apps/server/app/errors.py`, `apps/web/lib/lyrics.ts`, `apps/web/lib/generated/api.d.ts`, tooling `apps/web/package.json`/TS/Vitest, `package.json`, `pnpm-lock.yaml`, `docs/legal/licencias.md`, `apps/server/app/api_models.py`, `apps/server/tests/test_openapi_t03.py`, `apps/server/tests/test_lyrics.py`, `apps/web/lib/lyrics.test.ts`, `apps/web/tsconfig.json`, `apps/web/vitest.config.ts`, tests
- **Cubre (tests)**: E2E-03, API-02
- **Verificación**:
  - `uv run scripts/export_contracts.py --check` → `openapi.json up to date · engine-v1.json up to date`
  - `uv run pytest apps/server -k lyrics -q` → verde · `pnpm --filter web test lyrics` → verde

**Criterios de aceptación**
- [x] `export_contracts.py` genera `openapi.json` desde FastAPI; un test falla si el fichero versionado difiere del generado.
- [x] `pnpm gen` genera los tipos de la web (`openapi-typescript`).
- [x] `lyrics-cases.json` cubre etiquetas válidas e inválidas, secciones vacías, mayúsculas y alias en castellano (`[estribillo]` → `[chorus]`). Los dos parsers pasan exactamente los mismos casos.


**Inicio parcial — 2026-10-07:** implementer fresco recibe sólo parsers nuevos Python/TS, fixtures comunes y tooling web. T02 conserva main.py/pyproject/uv.lock; exportador e integración quedan para la siguiente unidad. Resultados esperados escritos antes e independientemente de ambos parsers; original/rangos UTF16/tag Markdown/direcciones se preservan. Sin aceptación T03/UI/modelo. Medición agregada proporcional estimada, suplemento T03parser2; raíz conserva ledger/Git/documentación.

---

## Fase 2 — Cola y post-proceso

**Estado**: borrador · **Estimado**: 26h · **Real**: —


**Aceptación técnica T03 — 2026-10-07:** [QA1](testing/t03/qa1-report.md).348canónicaspass3Windows skips/112genéricasporlenguaje/56fixtures,117selecciónlyrics incluye5vecinos; conteo anterior351pass incluía5privadas, reconciliación íntegra.6módulosPythonwhole≥96,43%/TS53/53ramas57/62/0exclusiones. Exportcheck/pnpmgenx2determinista/typecheck/OpenAPIlint0/2sondas403.18fuentes/651noCLI/rootterminal0 verificados. Revisión2A/B/D0gapsnuevos/R03-01corregido. Unitgate0/M1globalgate1sinE2E. Incidente operativo pnpm: intento de descarga automática/cachefuera del proyecto preservado; recuperaciónNode/Vitestexistente, sources/tests/locks exactos pero dependenciasinstaladas no certificadasinmutables. Root acepta dependencia funcional bajoADR0037 sin convertir esa restricción en verde. Tres criterios técnicos marcadosx; Git/T03cierre/M1/API-02/E2E-03/UIpendientes.

### T-04 — Dispatcher: carriles, prioridades, dependencias, reintentos y recuperación

- **Descripción**: La cola de [ADR-0018](../../decisiones/ADR-0018-cola-de-jobs.md) sobre la tabla `job`, con el cliente del contrato `/v1`.
- **Estado**: en-progreso
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 7h · real —
- **Supervisión**: est. 1.8h (≈25 % IA) · real —
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `apps/server/app/queue/` (ADR-0047: dispatcher, `backends/` con el protocolo `EngineBackend` y `HttpEngineBackend`, `resolver`), `apps/server/app/models/`, nueva migración aditiva `apps/server/app/migrations/versions/`, `apps/server/app/snapshots.py`, contratos song-v1 de `packages/contracts/` y recurso empaquetado, tests, `docs/legal/licencias.md` (toolchain fijado de QA); `docs/decisiones/ADR-0049-entradas-estables-fuera-del-writer.md`, índice y arquitectura sistema/datos (entradas estables fuera del writer); `apps/server/tests/test_dispatcher_scanning.py` (ventanas, candidaturas inválidas y coste de inputs)
- **Cubre (tests)**: E2E-01, E2E-04, E2E-05, E2E-06, E2E-09, M-01
- **Verificación**:
  - `uv run pytest apps/server -k "dispatcher or queue" -q` → verde con `engine-mock`: éxito, error `retryable` reintentado, error no reintentable, cancelación, reinicio a mitad (`interrupted` → reencolado), dependencia `blocked`→`succeeded` y dependencia fallida → `DEPENDENCY_FAILED`

**Criterios de aceptación**
- [ ] Carriles `gpu` (1) y `cpu` (2). La columna `lane=remote` existe, pero sin adapters todavía. Prioridad y después FIFO. `not_before` se respeta. Las tareas con `device: cpu` en el descriptor (`audio.beats`) van por el carril `cpu` y no descargan la GPU.
- [ ] El dispatcher solo habla con el protocolo **`EngineBackend`** (`health`, `models`, `load`, `unload`, `estimate`, `submit`, `status`, `events`, `cancel`). `HttpEngineBackend` implementa `/v1`, y en M2 los adapters externos entrarán sin tocar el dispatcher.
- [ ] **Cadena de jobs por petición** ([sistema.md](../../arquitectura/sistema.md) §3): generación (N salidas, `seed + i`) → `post.audio` (cpu) → un `audio.beats` por take, creados en `blocked` y con sus `inputs` como referencias que se resuelven al desbloquear.
- [ ] El resolver elige engine y modelo por **tarea verificada** en los descriptores (`GET /v1/models` en caché).
- [ ] Antes de despachar a otro engine: `POST /v1/unload` al que tiene el modelo cargado y comprobación de `free_mb` en `/v1/health`.
- [ ] Consume el NDJSON con reenganche por `seq`. Actualiza `stage`, `progress` y `telemetry`, y publica los eventos en el bus interno del SSE.
- [ ] Reintentos solo si el error es `retryable`, con un máximo de 2. `VRAM_EXCEEDED` se reintenta una vez en modo `offload` si existe.
- [ ] Recuperación según ADR-0018 y [ADR-0043](../../decisiones/ADR-0043-identidad-durable-de-intentos.md): mismo ID y payload del intento vigente, cursor/efecto transaccionales, sin consumir retries por acuse perdido. Sólo un error durable reintentable reserva otro ID, hasta tres intentos totales. Registro ausente/temporales requieren reconciliación; done durable continúa CPU. Reintento manual: job lógico nuevo y sólo takes failed del mismo usuario/canción. Variantes en batch o en serie según I-01 (benchmark M0).


**Inicio técnico parcial — 2026-10-07:** dependencia T02 aceptada y T03 técnica conforme; implementer fresco recibe sólo relación job_attempt/migración0005/snapshots/contratos, segúnADR0043. RED antes de producción, baseline0001–4 e invariantes anteriores congelados. Dispatcher/backends/resolver/chains siguen para próxima unidad; ninguna CA completa marcada, revisión/QA/Git/T04/M1pendientes.

**Verificacion adicional T-04 - 2026-10-10:** TDD de capacidad de cola: el caso RED de una reserva `interrupted` de soporte sin `JobAttempt` se corrigio preservando la proteccion GPU, excluyendo huerfanos CPU interrumpidos y manteniendo la ocupacion de filas `running`. Suites: `test_dispatcher_admission.py` 65 passed; `test_dispatcher_retry.py` 108 passed; subconjunto `dispatcher or queue or worker_recovery` 565 passed, 1254 deselected, 1 warning. El contrato del backend mock de los nueve metodos y la resolucion CPU `audio.beats` con entrada `master` tambien quedan verificados; el test de politica CPU se ajusto para aislar la seleccion de carril del requisito de entrada. T-04 sigue en-progreso hasta revision adversarial, QA y los criterios de almacenamiento/recovery.

**Verificacion declarada actualizada - 2026-10-10:** `python -m pytest apps/server/tests -k "dispatcher or queue" -q` termina con **562 passed, 1 skipped, 1257 deselected, 1 warning** en 250,30 s. [Recibo](testing/t04/dispatcher-verification-current.md). La diferencia de conteo respecto al recibo anterior refleja la selección actual del árbol de pruebas; no se relaja ningún criterio. La revisión adversarial final, el almacenamiento/recovery y el gate QA siguen abiertos.

### T-05 — Worker CPU: post-proceso, manifiesto, traslado y análisis dependiente

- **Descripción**: El carril `cpu` que convierte la salida cruda en takes `ready` ([ADR-0017](../../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)).
- **Estado**: en-progreso
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `apps/server/app/worker/`, `apps/server/app/models/__init__.py`, `apps/server/app/models/song-v1.schema.json`, `apps/server/app/snapshots.py`, `apps/server/app/migrations/cpu_publication_invariants.py`, `apps/server/app/migrations/versions/0006_cpu_publication.py`, `packages/contracts/song-v1.schema.json`, `apps/server/tests/test_worker_contracts.py`, `apps/server/tests/test_worker_publication_invariants.py`, `apps/server/tests/test_worker_snapshots.py`, `packages/audio-post/audio_post/pipeline.py`, `packages/audio-post/audio_post/manifest.py`, `packages/audio-post/audio_post/manifest-v1.schema.json`, `packages/audio-post/pyproject.toml`, `packages/audio-post/tests/test_portable_audio_post.py`, `packages/audio-post/tests/test_wheel_resources.py`, `tools/ffmpeg-linux.lock.json`, `.gitignore`, `docs/legal/licencias.md`, `scripts/fetch_ffmpeg_linux.py`, `tests/test_fetch_ffmpeg_linux.py`, `docs/decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md`, `docs/decisiones/README.md`, `docs/arquitectura/datos.md`, `docs/arquitectura/pipeline-audio.md`, tests, `apps/server/app/queue/resolver.py`, `apps/server/app/queue/dispatcher.py`, `apps/server/tests/test_dispatcher_scanning.py`, `apps/server/tests/test_queue_manual_retry.py`, `apps/server/tests/test_dispatcher_identity_drift.py`, `docs/decisiones/ADR-0068-descarte-de-identidad-obsoleta-antes-de-procedencia.md`, `docs/arquitectura/sistema.md`, `apps/server/pyproject.toml`, `apps/server/Dockerfile`, `apps/server/Dockerfile.dockerignore`, `uv.lock`, `apps/server/tests/test_snapshot_synthetic_provenance.py`, `scripts/storage.py`, `scripts/storage.ps1`, `scripts/storage.sh`, `docker-compose.storage.yml`, `tests/test_storage_preflight.py`, `docs/decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md`, `packages/audio-post/audio_post/private_context.py`, `packages/audio-post/tests/test_private_request_context.py`, `packages/contracts/manifest-v1.schema.json`, `docs/decisiones/ADR-0070-contexto-privado-de-request-y-linaje-en-publicacion-audio.md`, `packages/storage-guard/pyproject.toml`, `packages/storage-guard/studio_storage_guard/preflight.py`, `packages/storage-guard/studio_storage_guard/__init__.py`, `packages/storage-guard/tests/test_native_probe.py`, `packages/storage-guard/tests/test_preflight.py`, `apps/server/app/worker/audio_child.py`, `apps/server/app/worker/execution.py`, `apps/server/app/worker/packages.py`, `apps/server/app/worker/publications.py`, `apps/server/app/worker/custody.py`, `apps/server/app/worker/custody_linux.py`, `apps/server/app/worker/custody_linux_supervisor.py`, `apps/server/tests/test_worker_actual_execution.py`, `apps/server/tests/test_worker_private_context_integration.py`, `scripts/storage_attach.py`, `tests/test_storage_attach.py`, `packages/storage-guard/studio_storage_guard/provision.py`, `packages/storage-guard/tests/test_provision.py`, `apps/storage-guard/Dockerfile`, `tests/test_storage_guard_deployment.py`, `apps/engines/acestep/entrypoint.sh`, `tests/test_acestep_startup.py`, `scripts/storage_operator.py`, `tests/test_storage_operator_binding.py`, `scripts/storage_receipt_store.py`, `tests/test_storage_receipt_store.py`, `packages/storage-guard/studio_storage_guard/helper.py`; `packages/storage-guard/tests/test_helper.py` (formato del test existente del helper IPC, sin cambio semantico) , `packages/audio-post/tests/conftest.py`, `packages/audio-post/tests/test_audio_post.py`, `apps/server/tests/test_worker_native_linux_custody.py` , `scripts/test_workspace.py`, `tests/test_fixture_confinement.py`, `packages/audio-post/tests/test_directory_attributes.py` , `docs/decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md`, `apps/server/tests/fixtures/native_custody_fault_bootstrap.py`, `scripts/storage_journal.py`, `tests/test_storage_journal.py`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md`, `docs/decisiones/ADR-0076-politica-estricta-de-confianza-del-journal-windows.md`, `scripts/storage_journal_windows.py`, `tests/test_storage_journal_windows.py`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md`, `docs/decisiones/ADR-0078-geometria-nt-readonly-del-journal.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md`, `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md`, `scripts/storage_journal_windows_io.py`, `scripts/storage_journal_windows_abi.py`, `tests/test_storage_journal_windows_io.py`, `tests/test_storage_journal_windows_abi.py`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-principal-design.md`, `scripts/storage_journal_windows_identity.py`, `tests/test_storage_journal_windows_identity.py`, `docs/decisiones/ADR-0084-frontera-nativa-y-admision-del-principal-windows.md`, `docs/decisiones/README.md`, `scripts/storage_journal_windows_acquisition.py`, `tests/test_storage_journal_windows_acquisition.py`, `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-observation-design.md`, `docs/decisiones/ADR-0089-observacion-nominal-del-mismo-handle-windows.md`, `scripts/storage_journal_windows_observation.py`, `tests/test_storage_journal_windows_observation.py`
- **Cubre (tests)**: E2E-01, E2E-09, M-01
- **Verificación**:
  - `uv run pytest apps/server -k worker -q` → verde
  - `uv run scripts/verify_manifest.py data/songs/` → `all valid` (tras un E2E)

**Criterios de aceptación**
- [ ] Ejecuta `audio-post` dentro del contenedor server con FFmpeg LGPL Linux fijado y verificado. Mueve el resultado de forma atómica a `data/songs/<song>/takes/<take>/`. Registra los `asset` y escribe el manifiesto v1 `audio_take`.
- [ ] Marca el take `ready`, regenera `song.json` y desbloquea el job `audio.beats` dependiente, cuyo resultado se guarda como fila `analysis(kind=beats)`.
- [ ] Limpia sólo la salida propia acreditada `data/tmp/<attempt_id>/` del intento aceptado (ID contractual del engine, ADR-0043). Si el post-proceso falla (validación), el take queda `failed` con su `code`.

### T-06 — SSE de eventos

- **Descripción**: `GET /api/events` según [convenciones.md](../../arquitectura/convenciones.md) §3.
- **Estado**: en-progreso
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: apps/server/app/local_sessions.py, apps/server/app/event_dtos.py, apps/server/tests/test_local_sessions.py, apps/server/tests/test_event_dtos.py, docs/decisiones/ADR-0058-sesion-publica-local-para-eventos.md, `apps/server/app/publication.py`, `apps/server/app/event_snapshot.py`, `apps/server/tests/test_publication_coordinator.py`, `apps/server/tests/test_event_snapshot.py`, `apps/server/app/queue/events.py`, `apps/server/app/sse.py`, `apps/server/tests/test_sse_bus.py`, `apps/server/tests/test_sse_frames.py`, `apps/server/app/event_routes.py`, `apps/server/app/api_models.py`, `apps/server/app/errors.py`, `apps/server/tests/test_session_http.py`, `apps/server/app/main.py`, `apps/server/app/settings.py`, `apps/server/app/security.py`, `packages/contracts/openapi.json`, `apps/web/lib/events.ts`, `apps/web/lib/events.test.ts`, `apps/web/lib/event-parser.ts`, `apps/web/lib/event-parser.test.ts`, `apps/web/lib/event-reducer.ts`, `apps/web/lib/event-reducer.test.ts`, `apps/web/lib/event-session.ts`, `apps/web/lib/event-session.test.ts`, `apps/web/lib/generated/api.d.ts`, `docs/decisiones/ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md`, `docs/decisiones/README.md`, `docs/arquitectura/convenciones.md`, tests
- **Cubre (tests)**: E2E-01, E2E-06
- **Verificación**:
  - `uv run pytest apps/server -k sse -q` → verde (reconexión con `Last-Event-ID` sin perder eventos)

**Criterios de aceptación**
- [ ] Sobre de evento `{id: seq, type, ts, data}` con los tipos `job.*`, `entity.updated` y `system.status`. Keep-alive cada 15 s.
- [ ] `Last-Event-ID` reenvía los eventos perdidos desde un buffer. Si el buffer se agotó, envía el estado actual de los jobs activos.

---

## Fase 3 — API de dominio

**Estado**: borrador · **Estimado**: 12h · **Real**: —

**Verificacion adicional T-06 - 2026-10-10:** la frontera CORS rechaza preflight de barras y subrutas desconocidas bajo `/api/session/`, evitando que hereden la politica global; los dos endpoints exactos mantienen su contrato. `apps/server/tests/test_session_http.py` pasa 82/82 y Ruff de `security.py` queda limpio. T-06 sigue en-progreso hasta revision y QA formal.

**Verificacion SSE actualizada - 2026-10-10:** la bateria conjunta de `test_sse_http.py`, `test_session_http.py`, `test_sse_bus.py`, `test_sse_frames.py`, `test_event_snapshot.py` y `test_event_dtos.py` termina con **233 passed en 49,36 s**. [Recibo](testing/t06/sse-verification-current.md). La revisión adversarial, QA de integración y E2E navegador siguen abiertos.

### T-07 — API: canciones, letras, generaciones, takes, colecciones, modelos y sistema

- **Descripción**: Los endpoints de M1 de [sistema.md](../../arquitectura/sistema.md) §5.
- **Estado**: en-progreso
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-04, T-05
- **Tipo**: backend
- **Archivos**: `apps/server/api/` (`songs`, `lyrics`, `generations`, `takes`, `collections`, `jobs`, `models`, `system`), tests, `apps/server/tests/test_domain_routes.py`
- **Cubre (tests)**: E2E-01, E2E-02, E2E-07, E2E-08, E2E-10, E2E-11
- **Verificación**:
  - `uv run pytest apps/server -k api -q` → verde
  - `uv run scripts/export_contracts.py --check` → up to date

**Criterios de aceptación**
- [ ] `POST /api/generations` (`song_id?`):
  - valida contra el `params_schema` de la tarea;
  - exige `lyrics_declaration` cuando hay letra (`422 LYRICS_DECLARATION_REQUIRED`); `music.instrumental` no la pide;
  - crea la canción borrador si no se indica una, la versión de letra si cambió, N takes `queued` con semillas distintas y el job.
- [ ] Canciones:
  - CRUD de canciones con paginación por cursor y búsqueda FTS;
  - `POST /api/songs/{id}/master`;
  - versiones de letra.
- [ ] Takes:
  - detalle, manifiesto y linaje;
  - PATCH de favorito, valoración y etiqueta;
  - papelera con restauración.
- [ ] `GET /api/takes/{id}/audio` con `Range`, más `/peaks` y `/analysis`. Nombres de descarga legibles.
- [ ] `GET /api/models` agrega los descriptores (tareas y features verificadas). `GET /api/system` devuelve GPU, VRAM, RAM, engines, cola y disco.
- [ ] `POST /api/generations/estimate` (proxy a `/v1/estimate`), `POST /api/system/unload` y `POST /api/jobs/{id}/retry` (reutiliza los takes `failed`).

---

## Fase 4 — Web

**Estado**: en-progreso · **Estimado**: 86h · **Real**: —


**Verificacion de API T-07 - 2026-10-10:** `apps/server/tests/test_domain_routes.py` pasa 18/18 y `uv run scripts/export_contracts.py --check` confirma `openapi.json` y `engine-v1.json` actualizados. T-07 pasa a en-progreso; quedan revision adversarial, QA y la cobertura E2E de todos los criterios.

**Verificacion actual T-07 - 2026-10-10:** se repite la bateria con `test_domain_routes.py`: **18 passed en 6,34 s**; `scripts/export_contracts.py --check` devuelve `engine-v1.json up to date` y `openapi.json up to date`. [Recibo](testing/t07/domain-api-verification-current.md).
### T-08 — Web: esqueleto, tokens, temas, i18n, layout y cliente de API

- **Descripción**: Base de `apps/web` según [ux.md](../../producto/ux.md) §2–§3.
- **Estado**: en-progreso
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 7h · real —
- **Supervisión**: est. 1.8h (≈25 % IA) · real —
- **Dependencias**: T-03
- **Tipo**: frontend
- **Archivos**: `apps/web/` (App Router, Tailwind, shadcn/ui, next-intl, `styles/tokens.css`, `lib/api.ts`, `lib/events.ts`), `apps/web/messages/es.json`, `apps/web/playwright.config.ts`, `apps/web/e2e/fixtures/`, `scripts/e2e_stack.py` (levanta server en modo prueba + engine-mock + seed), `apps/server/scripts/seed_e2e.py`, `docs/legal/licencias.md` (prerrequisitos exactos), `tools/node/`, `tools/pnpm/` (herramientas portátiles verificadas), `tools/tools.lock.json`, `scripts/fetch_web_tools.py`, `tests/test_fetch_web_tools.py` (bootstrap portable confinado); `scripts/test_workspace.py`, `tests/test_fixture_confinement.py`, `tests/conftest.py`, `conftest.py` (temporales propios, sin namespace de entregas históricas); entrypoints del toolchain propio (ADR-0048/0051): `scripts/env.ps1`, `scripts/env.sh`, `scripts/bootstrap.ps1`, `scripts/bootstrap.sh`, `scripts/pnpm.py`, `scripts/pnpm.ps1`, `scripts/pnpm.sh`, `tests/test_web_tool_entrypoints.py`; ADR-0052 entradas Docker: `tools/web-linux.lock.json`, `tools/web-dependencies.lock.json`, `.gitignore`; `scripts/fetch_web_dependencies.py`, `tests/test_fetch_web_dependencies.py`, `scripts/web_build_inputs.py`, `tests/test_web_build_inputs.py` (adquisición local sellada y contexto selectivo, sin red implícita)
- **Cubre (tests)**: M-02
- **Verificación**:
  - `pnpm --filter web lint && pnpm --filter web test` → verde (incluye la regla contra literales en JSX)
  - `pnpm --filter web build` → OK
  - `pnpm test:e2e -g smoke` → verde (la app abre contra engine-mock)

**Criterios de aceptación**
- [ ] Tokens de [ux.md](../../producto/ux.md) §2, temas oscuro y claro, `prefers-color-scheme` y `prefers-reduced-motion`. Tipografías Inter, Bricolage Grotesque y JetBrains Mono (OFL).
- [ ] Navegación: Crear · Canciones · Sistema. El reproductor persistente vive fuera del árbol de páginas.
- [ ] Cliente tipado a partir de `openapi.json`. Cliente SSE con reconexión y `Last-Event-ID`. La web habla directamente con `127.0.0.1:8000`, sin el proxy de Next.
- [ ] Todo el texto sale de `messages/es.json`.
- [ ] **Infraestructura E2E lista desde aquí**: Playwright configurado, `scripts/e2e_stack.py` arranca el server en modo prueba (BD temporal en `data/tmp/e2e/`), `engine-mock` y la web, y ejecuta el seed. `pnpm test:e2e` funciona con un spec de humo. Cada tarea web posterior añade **su propio** spec E2E.
- [ ] `apps/web/Dockerfile` y Compose para web/server/mock listos desde T-08; `scripts/e2e_stack.py` arranca los servicios en Docker y ejecuta el seed dentro del server. Verificar URLs del navegador, resolución interna y SSE. El cierre T-16 documenta este despliegue; no lo introduce después de los E2E.

**Evidencia T-08 - 2026-10-10:** la bateria de infraestructura del server pasa 454 tests, 5 omitidos y 1 caso ambiental aislado (SWC nativo requiere ACL Windows de no-reemplazo que el host actual no acredita); el test especifico de dependencias web pasa 49/49 y el lock mantiene las 609 integridades. Se corrigieron el namespace STUDIO_TEST_ROOT del arnes y la lectura UTF-8 de rutas Unicode. T-08 permanece en-progreso hasta revisar la capacidad ACL o declarar el prerrequisito de host.
**Regresion web actual - 2026-10-10:** `pnpm --filter web test` termina con **248 passed en 23 ficheros**; `pnpm --filter web lint`, `pnpm --filter web typecheck` y `pnpm --filter web build` terminan con exit 0. [Recibo](testing/t08/web-regression-current.md). Docker/Playwright, revisión y QA de cierre siguen abiertos.
### T-09 — Crear: editor de letra, estilo, autoría, avanzado y variantes

- **Descripción**: El panel de creación de [ux.md](../../producto/ux.md) §4.1 (modo personalizado).
- **Estado**: en-progreso
- **Tiempo humano**: est. 16h · real —
- **Tiempo IA (ejec.)**: est. 8h · real —
- **Supervisión**: est. 2h (≈25 % IA) · real —
- **Dependencias**: T-08, T-07
- **Tipo**: frontend
- **Archivos**: `apps/web/app/create/`, `apps/web/components/LyricsEditor/`, tests
- **Cubre (tests)**: E2E-01, E2E-02, E2E-03, E2E-11
- **Verificación**:
  - `pnpm --filter web test create` → verde
  - `pnpm --filter web test:e2e -g "E2E-02|E2E-03|E2E-11"` → verde

**Criterios de aceptación**
- [ ] `LyricsEditor`: textarea con capa espejo que resalta las etiquetas, inserción de secciones, validación en vivo con el parser compartido y contador de líneas y sílabas por sección.
- [ ] Estilo libre con chips y estilos a excluir. **Autoría obligatoria** (grupo de radios siempre visible). Idioma.
- [ ] Opciones avanzadas escritas a mano con los campos que declara el `params_schema` de la tarea.
- [ ] Toggle de instrumental que pliega la letra sin borrarla. Selector de 1 a 4 variantes.
- [ ] El botón Crear muestra la estimación (`POST /v1/estimate` vía server), la cola y el estado de la GPU. `Ctrl+Enter` también crea.

**Evidencia T-09 - 2026-10-10:** el compositor actualiza cola/GPU al abrir y cada 5 s, cancela la peticion anterior al refrescar y limpia el intervalo al desmontar. Selecciona el primer modelo verificado publicado por `/api/system` para alinear estimacion y generacion; conserva fallback de ACE-Step si el catalogo aun no llega. El valor inicial de variantes es 2. TDD/regresion: `pnpm --filter web test` **236 passed**, `pnpm --filter web lint` exit 0, `pnpm --filter web typecheck` exit 0; Playwright contra Compose aislado **14 passed, 1 skipped**. T-09 sigue en-progreso: falta la revision/QA formal y la verificacion del modelo ACE-Step real.
**Verificacion adicional T-09 - 2026-10-10:** regresion web completa `pnpm --filter web test` pasa **247/247** en 23 ficheros, incluyendo editor de etiquetas, insercion de secciones, parametros dinamicos, instrumental y E2E-11. Se conserva el estado en-progreso por revision adversarial, QA Playwright y validacion ACE-Step real.

### T-10 — Tarjeta de generación y feed A/B

- **Descripción**: La firma visual de [ux.md](../../producto/ux.md) §4.2.
- **Estado**: en-progreso
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-09, T-06
- **Tipo**: frontend
- **Archivos**: `apps/web/components/GenerativeViz/`, `apps/web/components/GenerationCard/`, tests
- **Cubre (tests)**: E2E-01, E2E-04, E2E-05
- **Verificación**:
  - `pnpm --filter web test:e2e -g "E2E-01|E2E-04|E2E-05"` → verde

**Criterios de aceptación**
- [x] `GenerativeViz` en canvas de 96 columnas, movida **solo** por el progreso real. Al terminar se transforma en los picos reales. Un único rAF, 30 fps como máximo, en pausa fuera del viewport.
- [x] Stepper con las etapas que envía el engine. La etapa «Modelo» solo aparece si hay que cargar el modelo.
- [x] Feed con las variantes agrupadas. Error en la tarjeta con `code`, `job_id` y botón de reintentar. Cancelar desde la tarjeta.


**Evidencia T-10 - 2026-10-10:** GenerativeViz usa canvas de 96 columnas, progreso del evento real, un unico rAF limitado a 30 fps y pausa fuera del viewport; al completar adopta peaks. GenerationCard muestra stepper, carga de modelo condicional, agrupacion A/B, errores con code/job_id y acciones de cancelar/reintentar. Tests focales Vitest 5/5; Playwright Compose E2E-01/E2E-04/E2E-05 3/3; lint y TypeScript verdes. T-10 queda en-progreso hasta revision adversarial y QA de cierre.
### T-11 — Biblioteca de canciones

- **Descripción**: [ux.md](../../producto/ux.md) §4.3.
- **Estado**: en-progreso
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 5h · real —
- **Supervisión**: est. 1.3h (≈25 % IA) · real —
- **Dependencias**: T-08, T-07
- **Tipo**: frontend
- **Archivos**: `apps/web/app/songs/`, tests
- **Cubre (tests)**: E2E-08
- **Verificación**:
  - `pnpm --filter web test:e2e -g "E2E-08"` → verde

**Criterios de aceptación**
- [x] Vistas en grid y en lista, búsqueda, filtros, scroll infinito con skeletons y estado vacío con llamada a la acción.
- [x] Preescucha del maestro (400 ms de espera, 10 s, se puede desactivar). Miniatura de la visualización en las canciones que están generando.
- [x] Papelera con restaurar y purgar.



**Implementacion de papelera - 2026-10-10:** se anaden GET /api/songs/trash, POST /api/songs/{id}/restore y POST /api/songs/{id}/purge. La papelera conserva deleted_at y purge_after; restaurar mantiene las tomas y reactiva FTS. La purga exige 30 dias y rechaza proyectos con historial durable (PURGE_PROTECTED) para respetar los disparadores de inmutabilidad. La UI incorpora el modo papelera y acciones Restaurar/Purgar. RED inicial: 2 fallos por rutas inexistentes; GREEN: server 16 passed, web 238 passed, Playwright completo 15 passed, 1 skipped, lint, TypeScript, Ruff y export_contracts.py --check verdes. La tarea sigue en-progreso por preescucha del maestro y miniaturas de generaciones pendientes.


**T-11 preescucha y miniatura - 2026-10-10:** MasterPreview carga el take maestro autenticado tras 400 ms de hover/focus, limita la reproduccion a 10 s, libera el Blob URL y permite desactivar la funcion. Las canciones in_progress muestran GenerativeViz como miniatura de generacion. RED/GREEN del componente: 1 test; focal pages + componente 16 passed; suite web 240 passed; Playwright Compose 15 passed, 1 skipped; lint/typecheck/build verdes. T-11 permanece en-progreso hasta revision adversarial y QA de cierre.
### T-12 — Vista de canción (Audio y Letra)

- **Descripción**: [ux.md](../../producto/ux.md) §4.4, pestañas Audio y Letra. Las demás pestañas aparecen deshabilitadas con su hito.
- **Estado**: en-progreso
- **Tiempo humano**: est. 16h · real —
- **Tiempo IA (ejec.)**: est. 8h · real —
- **Supervisión**: est. 2h (≈25 % IA) · real —
- **Dependencias**: T-08, T-07
- **Tipo**: frontend
- **Archivos**: `apps/web/app/songs/[id]/`, `apps/web/components/Waveform/`, `apps/web/components/ProvenancePanel/`, tests
- **Cubre (tests)**: E2E-07, E2E-09
- **Verificación**:
  - `pnpm --filter web test:e2e -g "E2E-07|E2E-09"` → verde

**Criterios de aceptación**
- [x] Lista de takes con valoración, etiqueta y **marcar maestro**. Cabecera con título, artista, estado, BPM y maestro.
- [x] `Waveform` sobre wavesurfer.js alimentado con `peaks.json`: seek, zoom, marcas de beat y el plugin Regions ya cargado para M2.
- [x] Pestaña Letra: versiones, diferencias y qué takes cantaron cada una.
- [x] `ProvenancePanel` siempre visible, con los hashes copiables y exportación a JSON. Descarga en MP3 y FLAC.



**T-12 audio autenticado - 2026-10-10:** el server expone el asset master FLAC autenticado y la vista ofrece descarga MP3/FLAC por toma. RED/GREEN: endpoint focal y suite de dominio verdes; E2E-07 pasa en Compose; export_contracts.py --check, lint y TypeScript verdes. Quedan abiertas waveform, letra/versiones y panel de procedencia antes del cierre.


**T-12 waveform, letra y procedencia - 2026-10-10:** Waveform usa wavesurfer.js con peaks, seek accesible, zoom, regiones cargadas y contador de beats; la pestana Letra muestra versiones, diff y takes asociados; ProvenancePanel mantiene hashes copiables y exportacion JSON. La vista ofrece valoracion, favorito, seleccion de maestro y descargas MP3/FLAC. RED/GREEN focal: Waveform y ProvenancePanel 2/2; suite web 243/243; lint, TypeScript y build verdes; server focal 17/17; Playwright Docker 15 passed, 1 skipped.
### T-13 — Reproductor persistente, cola y atajos

- **Descripción**: [ux.md](../../producto/ux.md) §4.10 y §5.
- **Estado**: en-progreso
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-08, T-07
- **Tipo**: frontend
- **Archivos**: `apps/web/components/PersistentPlayer/`, tests
- **Cubre (tests)**: E2E-01, M-02
- **Verificación**:
  - `pnpm --filter web test player` → verde
  - lectura: M-02 (reproductor usable solo con teclado)

**Criterios de aceptación**
- [x] El reproductor persiste al navegar. Cola reordenable. `⏭` sobre una variante salta a su pareja.
- [x] Atajos de §5 y hoja de ayuda con `?`. Onda con `role="slider"` operable con el teclado.



**T-13 reproductor y variantes - 2026-10-10:** StudioShell mantiene PlayerProvider y PlayerDock al navegar; la cola se persiste en localStorage, permite reordenar/quitar y conserva la toma. Se implementan atajos de espacio/flechas/?, onda accesible y salto a la variante hermana por batch_id/variant_index. RED/GREEN: PlayerContext/PlayerDock 4/4 y take-pairs 2/2; E2E-01 y E2E-07 cubren navegaci?n y pareja; lint/typecheck/build verdes.
### T-14 — Colecciones y página Sistema

- **Descripción**: CRUD de colecciones en la UI y [ux.md](../../producto/ux.md) §4.9.
- **Estado**: en-progreso
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-11, T-07
- **Tipo**: frontend
- **Archivos**: `apps/web/app/system/`, `apps/web/components/Collections/`, tests
- **Cubre (tests)**: E2E-08, E2E-10
- **Verificación**:
  - `pnpm --filter web test:e2e -g "E2E-10"` → verde

**Criterios de aceptación**
- [x] Colecciones: crear, renombrar y mover canciones, individualmente o en lote. Filtro por colección.
- [x] Sistema: GPU, VRAM (total, libre y tope), RAM, engines, modelos con sus tareas verificadas, licencia y hash ✓, cola y disco. Botón para descargar el modelo.

---



**T-14 colecciones y sistema - 2026-10-10:** la UI permite crear/renombrar colecciones, filtrar, mover una cancion y mover varias seleccionadas mediante la misma API. Sistema muestra GPU libre/total/tope, RAM, engines, cola, disco, licencias, tareas verificadas y SHA-256 de pesos; mantiene la descarga del modelo de VRAM. E2E-10 y regresion web cubren la ruta; queda la lectura manual de hardware real para el cierre.
## Fase 5 — Pruebas y cierre

**Estado**: borrador · **Estimado**: 9h · **Real**: —

### T-15 — Suite E2E (Playwright + engine-mock)

- **Descripción**: Completar y estabilizar la suite: los E2E que no haya escrito ya su tarea web (E2E-06 recuperación, API-01/02), eliminar la inestabilidad y dejar la suite en verde.
- **Estado**: en-progreso
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-10, T-11, T-12, T-13, T-14
- **Tipo**: test
- **Archivos**: `apps/web/e2e/*.spec.ts`, `apps/server/scripts/seed_e2e.py`
- **Cubre (tests)**: E2E-01…E2E-11, API-01, API-02
- **Verificación**:
  - `pnpm test:e2e` → 11/11 E2E en verde contra `engine-mock` (3 ejecuciones seguidas sin fallos intermitentes)

**Criterios de aceptación**
- [x] Un spec por bloque E2E-xx con sus aserciones, y seed reproducible.
- [x] Tres ejecuciones seguidas en verde.



**T-15 ejecuciones recientes - 2026-10-10:** tres ejecuciones ordinarias consecutivas de Playwright pasan 15 pruebas activas con E2E-06 omitido. El modo recovery pasa los 15 specs no destructivos por separado, pero el escenario E2E-06 sigue fallando en la publicacion sobre bind Windows 9p/DrvFS con `renameat2` EINVAL, conforme a ADR-0069; no se marca el criterio de cierre hasta ejecutar sobre almacenamiento ext4/VHDX propio.
### T-16 — README de puesta en marcha y cierre del hito

- **Descripción**: Dejar el producto arrancable desde cero mediante Docker Compose (web, server con worker CPU y engines), y cerrar M1 con evidencias. Ollama permanece compartido en WSL2 y su adaptador corresponde a M2 ([ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)).
- **Estado**: en-progreso
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Supervisión**: est. 0.4h (≈25 % IA) · real —
- **Dependencias**: T-15
- **Tipo**: devops
- **Archivos**: `README.md`, `docker-compose.yml`, `apps/server/Dockerfile`, `apps/web/Dockerfile`, `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md`
- **Cubre (tests)**: M-01, M-03
- **Verificación**:
  - lectura: seguir el README desde un clon limpio lleva a la app funcionando
  - lectura: M-01 (generación real con GPU) y M-03 (backup y restauración) hechos y anotados

**Criterios de aceptación**
- [ ] README de puesta en marcha según [entorno.md](../../arquitectura/entorno.md) §5.
- [ ] Docker Compose arranca web/server/engines; migraciones dentro del server, SQLite WAL y assets persistentes, FFmpeg LGPL Linux fijado, nombres internos y Host/Origin cerrados. Pruebas sin GPU con mock y prueba real M-01, sin exigir Ollama en M1.
- [ ] Todos los CA de la spec verificados con evidencia; spec en `implementada` tras la retro del plugin.

**Notas**: [ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md) sustituye la exclusión inicial del despliegue Docker: M1 debe resolver FFmpeg Linux en el server, `STUDIO_ENGINES` con nombres de servicio y `STUDIO_ALLOWED_HOSTS` configurable. La decisión está aceptada; su implementación y validación siguen pendientes, sin modificar estados de tareas ni ampliar acceso a LAN.

**Decisión del propietario · 2026-10-06:** web/server/engines en Docker Compose; Ollama compartido en Ubuntu WSL2 y `engine-llm` adaptador `/v1` sin inferencia propia (M2). Cola SQLite `job`/`job_dependency`, GPU1/CPU2 y remote opcional apagado conservados. CA-01 y pruebas de despliegue alineadas. TDD n/a: prosa; no cierre de tareas ni evidencia runtime por esta actualización. Architect fresh entregó decisión y ajustes, aplicados por el orquestador. Verificación: 12 documentos UTF8, 155 enlaces relativos existentes, bloques de código cerrados y 59 fuentes de código intactas; recibo privado `.cache/dev-cycle/architecture-docker/verification.json`. `ledger-lint.py` M1: 0 incoherencias y 0 avisos; M0: 0 incoherencias y 6 avisos Changelog previos. Empaquetado server desde T-01 y web/mock/E2E Compose desde T-08, antes del cierre T-16. Estimaciones heredadas no recalculadas por esta actualización documental.


## Evidencia y gates de aceptación — ADR-0037

T-04 conserva I-01 y no se cierra mientras esa incógnita siga pendiente. M-01 se ejecuta para aceptación final en T-16 y conserva cobertura compartida de T-04/T-05; CPU/mock no la acreditan. M-02/M-03 mantienen sus requisitos existentes. T-16 conserva M0/T-13, descriptores reales y todos los CA de la spec. Las tareas técnicas solo se cierran con sus propios CA y verificaciones cumplidos; ninguna se cierra en este cambio documental.


## Revisión de dos lentes — intento 1: M1/T-00, secuenciación condicionada

A+B sin gaps; C/Dfalse por prosa. Scope0 en fixture Git privado de nueve archivos exactos y configuración vigente, sin excluir producción por globs; checkout compartido sin Gitwrites. Lectura estática en contextos frescos, no tests ni hasheslive por revisores. Root custodia9docs. [Informe](testing/t00/review1-report.md). QA documental pendiente; ninguna tarea de implementación cerrada.

## Revisión de dos lentes — intento 1: M1/T-01 — corrección pendiente

A/B/C, D no seleccionada. A-01 Important: Host400 y GET/HEAD con Origin ajeno200 contradicen CA14; B-01 Minor: se pierde Allow405. Auditoría enfocada de autorización1/8: cero vulnerabilidades adicionales demostradas, estática. [Informe](testing/t01/review1-report.md). T-01 permanece en-progreso; QA y Git pendientes. Corregir con RED frente al comportamiento actual, conservar criterios y repetir revisión sobre el diff completo.

## Revisión de dos lentes — intento 2: M1/T-01 — conforme

A/B/C sin gaps sobre diff completo; D no seleccionada. A-01 y B-01 corregidos con TDD, revisores frescos estáticos. [Informe](testing/t01/review2-report.md). T01 permanece en-progreso: QA independiente e imagen corregida/Git pendientes.


**T03 integración preparada, aún sin sourcefix — 2026-10-07:** RED: test_factory_and_openapi_are_free_of_runtime_writes falló porque la factoría configura logging de fichero antes de lifespan; RED: test_health_contract_declares_response_and_real_errors falló porque schema200 es vacío; RED: test_export_check_checks_server_contract_too falló porque --check sólo inspecciona engine-v1. Tres ejecuciones individuales reales/UTC/exits1 conservadas privadas, tras reproducción conjunta3fail. Fuente main sigue ownershipT02; se implementará al liberar esa unidad. Configuración explícita neutral y sin datos reales; ningún cambio de producto por este RED.


**T03 parsers entregados — 2026-10-07:** [Unidad y custodia](testing/t03/parser-unit-report.md):55fixtures/110Python/110TS/8vecinos, cobertura66/66y53/53sinexclusiones, strict/Ruff conformes. RED sección ausente Python y TS con argv/UTC/exits originales; esperados escritos antes de ambos parsers. Rootcustodiafuentes/originales/cinco protegidos; main cambiaT02/noidentityclaim. Incidentes declarados. IntegraciónOpenAPI/gen/factoría y revisión/QA pendientes; T03en-progreso. No promesa de obediencia a indicaciones musicales.


## Revisión de dos lentes — intento 1: M1/T02

[Informe](testing/t02/review1-report.md): A/B/C/Dfrescas; scope0/exclusiones0, root22fuentes intactas.0Critical/8Important/1Minor, pendientesreproducirantesfix; sinrebates/reset, siguienteintento2/3.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R02-01 | Important | Raíz canónica modificable fuera de cambios de aristas | T-02 | fix1, pendiente revisión2 | A-G1/B01 initial_invariants.py:139 |
| R02-02 | Important | Mover sujeto deja linaje cruzado entre canciones | T-02 | fix1, pendiente revisión2 | A-G2/B02 initial_invariants.py:117 |
| R02-03 | Important | Referencias globales a artwork de otra canción rompen snapshot | T-02 | fix1, pendiente revisión2 | A-G3/B03 snapshots.py:210 |
| R02-04 | Important | Una proyección fallida aborta reconciliación y arranque | T-02 | fix1, pendiente revisión2 | B04 snapshots.py:295 |
| R02-05 | Important | due acepta backup no restaurable y aplaza copia válida | T-02 | fix1, pendiente revisión2 | B05 backup.py:85 |
| R02-06 | Minor | Eventos de errores no llegan identificables al logger configurado | T-02 | fix1, pendiente revisión2 | B06 db.py:58 / backup.py:156 |
| R02-07 | Important | Cada commit escanea y publica toda la biblioteca | T-02 | fix1, pendiente revisión2 | D01 db.py:55 / snapshots.py:175 |
| R02-08 | Important | Cada arista recalcula todos los takes incluso ajenos | T-02 | fix1, pendiente revisión2 | D02 initial_invariants.py:139 |
| R02-09 | Important | Borrado FTS por columna UNINDEXED escanea biblioteca | T-02 | fix1, pendiente revisión2 | D03 0001_initial.py:44 |


**Diseño focalizado T04 elegido — 2026-10-07:** ADR-0043 selecciona O2, tabla job_attempt tipada mediante migración posterior a baseline23. Campos comunes owner/UTC/deleted obligatorios; request contractual congelada, cursor/terminal durables. Reintento confirmado crea identidad nueva; recovery/ACK perdido conserva la vigente. Tres intentos totales y offload único. Engine/wire/pesos sin cambios. TDD n/a: prosa/config; pruebas de reserva/replay/recovery/cancel/restore/propiedad quedan para implementerfresh tras T02. T04 continúa borrador, sin afirmar código/migración implementados.


**T02 selección focalizada — 2026-10-07:** arquitectofresh compara3opciones; raíz eligeO1 bajo delegación, ADR-0044. Snapshot una raíz completa y dependencias dirigidas, soporte durable y metadatosdirty/generación mediante migración aditiva. Sin remapIDs/prohibirrefslegales/arrastrar proyectos completos. Próximo implementerfresh fix1 reproduce R02-01…09 primero, corrige o rebateconprueba. TDD n/a: prosa/config de esta selección; nuevo código exigeRED funcional. Mediciónsuplementoestimado6 declarado antesdespacho, sinprecio/tokens/horasIAinferidos. T02en-progreso y review2/3+QA pendientes.


**T02 fix1 entregado para revisión2 — 2026-10-07:** [Informe](testing/t02/fix1-report.md):152pass/3skipWindows(Linuxcubierto), Verificación29pass/236deselect, ocho módulos completos978/1020=95,88%sinexclusiones. Root25fuentes/copia/490protegidos/279originales/preimágenes/0001baseline conformes. Wheel23recursos/torchNone/probeLinux0002/cleanup2contendores. NueveIDs implementados pendientesreview2/3 yQA; no rebates/reset ni M03real/Git.
RED: red-01 confirmó R02-01 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-02-corrected confirmó R02-02 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-03-corrected (collection); frozen baseline character reproduction is supplemental confirmó R02-03 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-04 confirmó R02-04 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-05 confirmó R02-05 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-06-corrected confirmó R02-06 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-07-corrected confirmó R02-07 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-08-corrected confirmó R02-08 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).
RED: red-09 confirmó R02-09 antes de la corrección · 2026-10-07 (originales en fix1; reproducciones suplementarias posteriores separadas).


## Revisión de dos lentes — intento 2: T02, corrección pendiente

[Informe](testing/t02/review2-report.md). A/B/C/D frescos mediante fallbackCLI;0Critical/8Important/0Minor, lectura estática. Cuatro terminales exit0; raíz25fuentes/paquetes/originales conformes. R02-07 sigue parcialmente abierto; nueveIDs anteriores preservados. No reset ni QA/cierre.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R02-10 | Important | Pertenencia ordinaria transitiva | T-02 | fix2, pendiente revisión3 | B2-01, `fix1_invariants.py:116`; review2-report.md |
| R02-11 | Important | Selección de versión de otro plano | T-02 | fix2, pendiente revisión3 | A-G3/B2-02, `snapshots.py:304`; review2-report.md |
| R02-12 | Important | Contenido de soporte editable | T-02 | fix2, pendiente revisión3 | A-G2/B2-03, `fix1_invariants.py:31`; review2-report.md |
| R02-13 | Important | Dependencia nueva no invalida consumidor | T-02 | fix2, pendiente revisión3 | A-G1/B2-04, `snapshots.py:415`; review2-report.md |
| R02-14 | Important | Cancelación omitida al comprobar backups | T-02 | fix2, pendiente revisión3 | B2-05/D2-03 parcialmente, `backup.py:91`; review2-report.md |
| R02-15 | Important | Consultas por cada fila del cierre | T-02 | fix2, pendiente revisión3 | D2-01, `snapshots.py:80,100,364,373`; review2-report.md |
| R02-16 | Important | Validación cuadrática en memoria | T-02 | fix2, pendiente revisión3 | D2-02, `snapshots.py:319,326,333`; review2-report.md |
| R02-17 | Important | Comprobación de toda la retención | T-02 | fix2, pendiente revisión3 | D2-03, `backup.py:81,85,91,92`; review2-report.md |


**T02 fix2 entregado — 2026-10-07:** [Informe](testing/t02/fix2-report.md):305pass/3skipLinuxsuplementado,30verificaciónselectiva,631/667=94,60%cinco módulos completos sinexclusiones. Root29fuentes/25preimages/509protected/553prior/273closed verificados.43regresiones;0003/wheel26/DockerCPU sinTorch/cleanup2. Todos los hallazgos siguen pendientes de review3 final3/3 y QA; no reset/rebate/aceptaciónM03/Git.
RED: red-10-corrected confirmó R02-10 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-2 confirmó R02-11 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-4 confirmó R02-12 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-5 confirmó R02-13 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-6 confirmó R02-14 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-15 confirmó R02-15 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-16 confirmó R02-16 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).
RED: red-7 confirmó R02-17 antes de su producción · 2026-10-07 (argv/UTC/exit1/JUnit originales en fix2).


## Revisión de dos lentes — intento 3: T02 — dos Important pendientes

[Informe](testing/t02/review3-report.md). Cuatrocontextosfrescos A/B/C/D,root29fuentes/originales verificados,0Critical2Important0Minor.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R02-12 | Important | Promoción por SQL ordinario elude protección | T-02 | pendiente reproducción | apps/server/app/migrations/fix2_invariants.py:84; review3-report.md |
| R02-18 | Important | Restore duplica SELECT por fila | T-02 | pendiente reproducción | apps/server/app/snapshots.py:564,588; review3-report.md |

**Decisión del orquestador tras3/3:** continuar fix3concreto y revisión4 bajo delegación vigente del propietario, sin reset/nueva autorización puntual/deuda silenciosa. Se conserva todo el historial; QA/cierreT02/M03/Git pendientes.


**T02fix3 custodiado — 2026-10-07:** [Informe](testing/t02/fix3-report.md),327pass3skip/30selección,365/394=92,64%tresmóduloscompletos0exclusiones.32fuentes/29preimágenes/850originales/282cerrados/18auditoríasprivadas/wheel28/probesnativecerradosverificados. R02-12yR02-18candidatos corregidos, nuevosREDoriginales antesproducción, revisión4/QApendientes sinreset/Git/M03cierre. CLIoriginalexitcleanupUNKNOWN; nuevofinisher0noatribuyepasado.
RED: red-promotion reprodujoSQLpromociónantes0004 · 2026-10-07 (UTCargvexit1original).
RED: red-queries-exact reprodujo4500SELECT para405antescache/lotes · 2026-10-07 (UTCargvexit1original).


## Revisión de dos lentes — intento 4: T02 — sin gaps nuevos

[Informe](testing/t02/review4-report.md). A/B/C/Dfrescos0Critical0Important0Minor;32fuentes/paquetes originales verificados. R02-12/18corregidosestáticamente; historial íntegro/contador4sinreset. QAindependiente siguiente, T02/Git/M1pendientes.


**T03 API y parsers custodiados — 2026-10-07:** [API](testing/t03/api-unit-report.md) y [parser](testing/t03/parser-unit-report.md).18fuentes/351Pythonpass3skip/110TS,APIwhole5≥98,73%0excl/OpenAPIlint0,engineexacto,genpinned7.13.0.30licenciasgeneradorreconciliadas;18sourceunion incluye parser+tooling necesarios declaradosenArchivos,ningún baselineT02db/model/migraciones/snapshots alterado. NEWREDdotenvread yCRLFpreservacióncorregidos;inventariosCLIprematurosinvalidospreservados/rootterminalhashnuevo. Revisión1/QA/Git/T03/M1pendientes.


## Revisión de dos lentes — intento 1: T03 — un Minor de paridad

[Informe](testing/t03/review1-report.md). A/B/Dfrescos0Critical0Important1MinorR03-01(UnicodeⅣ,UNKNOWN_TAGvsMALFORMED_TAG). Root18fuentes/paquetes verificados. CorregirparidadliteralantesQA bajo delegación/prioridadtags,no deuda silenciosa; siguiente revisión2sinreset. T03/M1/Gitpendientes.


## Revisión de dos lentes — intento 2: T03 — sin gaps nuevos

[Informe](testing/t03/review2-report.md). A/B/Dfrescos0Critical0Important0Minor nuevos, R03-01 corregido estáticamente.18fuentes/paquetes verificados;56fixtures/112porlenguaje sólo evidencia de implementación actual. QA fresca siguiente; T03/Git/M1/UIpendientes.


**Documentación técnica — 2026-10-07:** [Revisión y QA](testing/technical-documentation/report.md).5docs/106enlaces/2anclas/0incidencias, A/Bfrescos sin defectos concretos; A no verifica cierres sin ledger/plan/rango en su paquete. Prosa TDDn/a, guía server-y-contratos nueva. Docker/Ollama/SQLitepreservados; no hito cerrado ni nueva arquitectura.


**T04 primera unidad custodiada — 2026-10-07:** [Relación durable](testing/t04/attempt-schema-unit-report.md), siete fuentes y89 pruebas nuevas. BD212pass/1skip/8RED históricos de head. Root exige ciclo0004 explícito y ciclo actual0005, sin monkeypatch del head ni exclusiones. Revisión/QA pendientes; ocho criterios abiertos, dispatcher/backends no implementados.


## Revisión de dos lentes — intento 1: T04 relación durable — un Important

Lentes A+B+C+D frescas estáticas, ocho fuentes/scope0. T04 sigue en-progreso y sus ocho criterios abiertos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R04-S01 | Important | Terminal SQL sin ts obtiene fecha nueva en cada lectura | T-04 | pendiente RED y timestamp durable obligatorio sin cambiar wire | [Revisión1](testing/t04/schema-review1-report.md), helper:220/278 y Event:145 |


**Ubicación y entregas T04 elegidas — 2026-10-07:**[ADR0047](../../decisiones/ADR-0047-cola-empaquetada-en-app.md) elige app.queue para evitar colisión stdlib y mantener empaquetado app. Tres unidades funcionales secuenciales después de aceptación de esquema. No se aprueban tablas extra/bootID/multiproceso ni se resuelve I-01. Ocho criterios y verificación originales conservados; T04en-progreso.


**Corrección1 de esquema custodiada — 2026-10-07:** [R04-S01](testing/t04/schema-fix1-report.md),14newPASS/234DBpass1skip/helper179of19193,72%0exclusiones.65fuentes son freeze contextual, cuatro paths modificados propios; familia de revisión2 son nueve fuentes, no65cambios. Primer Ruffcache compartido incidente explícito; finalno-cache. Revisión2-dispatch1 A/Bactivas, C/D siguientes. Primerprepare2fallóantesdispatch por mezclar contexto/ownership, artefactos incompletos conservados; contador2sinreset.


## Revisión de dos lentes — intento 2: T04 relación durable — calendario SQL

A+B+C+D frescas estáticas,9fuentes/scope0. R04-S01 corregido;0Critical1Important0Minor nuevo.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R04-S01 | Important | Terminal durable sin fecha | T-04 | corregido por fecha UTC explícita | revisión2 A/B/C y14casos nuevos |
| R04-B02 | Important | Fecha imposible SQL produce fila ilegible ORM | T-04 | pendiente RED y calendario SQL estricto | [Revisión2](testing/t04/schema-review2-report.md), helper:220 |


## Revisión de dos lentes — intento 3: T04 relación durable — sin gaps pendientes tras rebate

A+B+C+D frescas,10fuentes/scope0. S01/B02corregidos; B03rebatido con ejecución exacta privada, date-time checker opcionalausente. No strictRFC externo certificado.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R04-S01 | Important | Timestamp durable ausente | T-04 | corregido | revisión3 A/B/C |
| R04-B02 | Important | Calendario imposible SQL | T-04 | corregido |71newPASS/helper184of196 |
| R04-B03 | Important | Supuesto rechazo de UTCspace por snapshot | T-04 | descartado (rebatido): caseexactoSQL/project/validatePASS, checker no registrado | [Revisión3](testing/t04/schema-review3-report.md) |

QAunidad pendiente, T04en-progreso/ochoCAabiertas; no dispatcher/Git/hito.


## Continuación autónoma — 2026-10-07T21:28:09.340481+00:00

T04 QA1 terminal0:522PASS/3skips Windows,174 nuevos+8históricos,10fuentes protegidas intactas. NO aceptación: cobertura dinámica0005 sin captura0/18 y toolchain de build sin filas/pin. TDD n/a: inventario y registro de licencias del prerrequisito. Root resuelve con verificación oficial/lock privado de QA y continuación independiente wheel/Docker/UTCspace/cobertura, sin instalar en Python máquina ni repetir producción. OchoCA abiertas.


## Revisión de dos lentes — intento 1: prerrequisito privado de construcción T04

A+B0Critical/0Important/0Minor; seis ruedas oficiales y179miembros contrastados. Primer despacho no evaluó nada por política Windows de lectura; conservado y sustituido por contexto fresco con lecturas autorizadas, sin cambiar contador. Root autoriza seis versiones exactas, incluido tomlkit0.13.3, sólo en venv privado de QA2/interprete gestionado. Ni Python máquina ni pyproject/lock general cambian. QA2 continúa cobertura0005/wheel/Docker/UTCspace;522PASS/3skips de QA1 intactos. No aceptación T04 ni conformidad histórica implícita.


## Dependencia técnica T04 aceptada — identidad durable, no tarea completa

Revisión3A/B/C/D0pending después de rebate nativo. QA1 522PASS3Win-skips; QA2 2ciclos nativos+5Linux (3symlinks reales),18/18migración0005 y tres otroswhole336/338,360/385,184/196,0exclusiones/samefrozenbytes. Wheel limpia/UTCspace/restore/backup/registry/calendario/traces29/29/32/restartDocker/NoTorch PASS,10fuentes/inventario cerrado verificados. Root acepta dependencia funcional bajoADR0037; ochoCA T04 siguen abiertas/Git/M1 pendientes. ControlCPUroot real sobrevivecleanup posterior (primerpreflight0 conservado; agregadoQAomitelasegundaprueba). No strictRFCexterno/futurebuildpin/operationalhistórico/GPU/quality certificado. PróximaunidadU1 backend/resolver/admision. [Aceptación](testing/t04/schema-qa2-root-acceptance.json).


## Continuación autónoma — 2026-10-07T22:21:32.394161+00:00

T04 U1 primer actor NEEDS_CONTEXT antes de RED/escrituras; root corrigió contexto exacto: env-B=.venv gestionada, CurrentJob=app.models.Job, registro activo=raíz DB Song viva owner/is_dependency_only false+dispatchable_job, sin tabla inventada. Único re-despacho contexto1 en ejecución. T08 inventario oficial24 candidatos custodiado, fuentes41 con drift sólo ledger root; sin instalación ni cierre transitivo/lock producto. Registro legal y bootstrap local pendientes; TDD n/a inventario. OchoCA T04 abiertas.


## Revisión de dos lentes — intento 1: T08 prerrequisito legal de primer nivel

A+B frescas0Critical/0Important/0Minor: Node separado+24paquetes exactos, prefijo histórico24181byteexacto/seisT04filas preservadas. Root acepta registro candidato cualificado y autoriza únicamente instalación portable de Node22.23.2/pnpm9.12.0 oficiales hash-verificados y probes propios --version/check, sin instalar dependencias de producto ni ejecutar wrapper perfil/Corepack. Avisos compilados/bundled independientes, ESLintconfig licencia upstream cualificada, sin auditoría comercial global ni cierre transitivo. TDD n/a docs; siguiente unidad fetch seguro con TDD. T08 CA abiertas.


## Continuación autónoma — 2026-10-07T22:36:13.777045+00:00

T08 registro legal de primer nivel aceptado por root tras AB limpias, ADR0048 fija herramientas portátiles; ejecución parcial fetch seguro/script+tests+toolslock en progreso. Sin dependencias/frontend/lock transitivo adoptados ni env/bootstrap migrados. T04 U1 avanza TDD SQLite/engine-mock real, cobertura individual pendiente antes de entrega; ningún CA cerrado.


## Inspección de componente U1 — intento 1: seis Important

Lentes frescas A+B+D según selector real (Cfalse):98propios/25vecinos/wholemín83,76%0excluded, pero seisImportant confirmados. A: REDpresence find_spec no acredita RED por comportamiento; clasificación previa corregida, preservando originales sin retrocertificación. B: busyCPUbloqueaGPU, backendcaído anterior bloquea solicitado y cabezaGPUocupada dejaCPUsin ejecutar. D:200jobs202SELECT/201dependencias bajo writer, yhasharchivo íntegro síncrono/eventloop+bajo writer. Corrección/reconstrucción TDD y nueva inspección2 pendientes; noU1aceptado/noT04CAcerrado, formalconjunta4 tras U2U3 conservada. Bytesrawprompts/letra/schema/identidad y límitesGPU1CPU2 siguen obligatorios.


## Inspección de componente T08 herramientas portátiles — intento 1

2026-10-07T23:07:09.750803+00:00: lentes frescas A+B declararon 0Critical/0Important/0Minor de corrección; selector oficial C/Dfalse. Root confirma alcance parcial y conservación de FFmpeg, pero adjudica **WEBTOOLS-TDD01 Important**: 49 casos iniciales se detuvieron en find_spec/assert de disponibilidad antes de alcanzar efectos de comportamiento. La autorización inicial de root para ese guard no reemplaza la ley dura de custom-agents:tdd. Originales y GREEN posteriores preservados; no certificación retrospectiva. QA nativa independiente sobre los bytes actuales sigue útil, sin aceptar TDD ni cerrar T08. Próximo implementer normal reconstruye tras RED genuino y corrige fixtures confinadas; próxima inspección de componente2. CA web/lock transitivo/env/bootstrap/Linux/Docker/E2E pendientes. TDD n/a: esta adjudicación y prosa/config del ledger.


## QA independiente forward T08 herramientas, no aceptación TDD

2026-10-07T23:09:48.230943+00:00: módulo exacto67casos,66PASS/1Windows symlinkprivilegeskip;74PASS previo incluía8vecinos weights. Whole actual290/315=92,06%zeroexcluded. Sondas nativas aisladas Node22.23.2/pnpm9.12.0,2933payload hashes intactos, junction Windows real rechazado/marker propio intacto, cleanup sólo propio. Clon privado de fixture histórica fija, AST del resto exacto; no ejecución canónica ni certificación histórica. Root verificó inventario completo y fuentes. WEBTOOLS-TDD01 sigue abierto; siguiente implementer normal reconstruye tras RED genuino y confina temporales, revisión2+QA posterior. No cierre T08/CA/frontend/envbootstrap/transitive/Linux/Docker/GPU.


## Decisión de entradas estables T04 — ADR0049

2026-10-07T23:12:59.250295+00:00: root elige copias propias verificadas antes del writer, payload contractual congelado y conservación ante commit/envío desconocidos. Nuevos tests del implementer reprodujeron fallo de limpieza tras commit ya durable; no se acepta la primera corrida cuya fuente cambió durante ejecución. Implementación/revisión/QA actuales y lifecycle U2 pendientes. TDD n/a: ADR/documentación, decisión bajo autorización autónoma vigente; no modificación de constitución/schema/contrato.


## Inspección de componente U1 — intento2: tres Important nuevos

2026-10-07T23:35:49.636056+00:00: A0gaps y confirma reconstrucción TDD válida; B2Important+D1Important, consolidado0Critical/3Important/0Minor. Seis anteriores corregidos dentro U1, sin aceptación global. U1-B2-01: ResolutionError de cabeza corta exploración; U1-B2-02: LIMIT400 previo a elegibilidad oculta401ejecutable tras400aplazados/dependencias; U1-D2-03: resolver antesocupación repite401health/201inputs en200GPUocupados+CPU. Conteos ejecutados con dependencias sintéticas;13,8GB cálculo estático no benchmark. Corrección normalfresh con regresiones nativas previas y revalidación selected, preserva sourcefrozen/history,contador final real150=125U1+25vecinos. Próxima inspección3/formal integrada4, QA pendiente; ocho CA abiertas. RootADR0049 ya registra staging, sin schema/protocolo/event/recovery extra.


## Inspección de componente T08 herramientas/fixtures — intento2

2026-10-07T23:45:13.053222+00:00: A0gaps acredita reconstrucción funcional de WEBTOOLS-TDD01 (no custodia histórica perfecta); B1Important FIXTURE-LINK01: fixtures globales rechazan childsymlinks legítimos de negativos existentes, teardown falla donde creación permitida. Evidencia estática, skip Windows lo oculta. Root elige eliminar sólo el enlace propio dentroUUID sin recorrer destino, conserva rechazo de namespace/raíz/marcador/ancestros reparse y pertenencia. Childhardlinks puedenunlink propio sinchmod ni alterarcontenido extranjero; markerhardlink siemprefailclosed. Implementer normal2fuentes reproduceRED nativo antesfix, pruebas existentes no se debilitan.93PASS1skip/whole4>=93%zeroexcluded previo forward supersedido por nuevafunción despuésfix; próximo componente3/QA2, T08CA pendientes.


## Revisión de componente T-08 — t08-portable-component-inspection3

2026-10-08T00:15:45.834846+00:00: A limpia; B FIXTURE-OWNER01 Important probado sólo con filesystem simulado, no nativo. Orquestador continúa bajo autorización autónoma después de3 intentos, sin deuda/reset: componente4 siguiente. RED nativo debe demostrar cero borrados ante token alterado durante collect. Childlink own unlink/open-directory recovery permanecen contratos. No T08CA aceptada. TDD n/a: adjudicación/prosa.


## Revisión de componente T-04 — t04-u1-component-inspection3

2026-10-08T00:15:45.834846+00:00: A limpia; B3-01 y D3-01 Important distintos. Reproducción B simulada; D SQLite real in-memory 200/400/2001SELECT y33/65/296ms, sin HTTP/GPU. Orquestador decide seguir bajo delegación autónoma después de3 intentos, sin deuda/reset: componente4 siguiente. RED nativo antesfix, unknown commit conservado; ochoCA/U2/U3 abiertas. TDD n/a: adjudicación/prosa.


## Entrega técnica fixture-owner-fix3 para revisión independiente

2026-10-08T00:19:49.387274+00:00: 106PASS5Windows skips; tres RED nativos de retencion payload antesfix; whole119/126=94,44%zeroexcluded con bytes actuales. 19 funciones fixture previas AST exacto/original67 portable byte exacto y2933 payloads+origenes protegidos. Inspeccion4 A en curso/B pendiente y QA2 posterior; limite TOCTOU declarado, prueba Linux anterior solo anterior fuente; no T08CA/quality/aceptacion global.

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[entry] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:44.545715+00:00

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[collected] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:45.495298+00:00

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[between] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:46.471775+00:00



## Revisión de dos lentes — intento 4: T08 componente conforme

2026-10-08T00:23:57.189877+00:00: A+B0Critical/0Important/0Minor, FIXTURE-OWNER01 corregido con3RED funcionales y106PASS5skip/whole94,44%zeroexcluded. Revisión propia estática/lectura; evidencia nativa del implementer, no rerun del revisor. Sigue QA2 independiente de herramientas/fixtures actuales; seisCA web pendientes, no aceptación de tarea ni historial perfecto. TDD n/a: adjudicación/prosa.


## Entrega técnica dispatcher-u1-fix3 para revisión independiente

2026-10-08T00:27:22.706683+00:00: B3-01/D3-01 corregidos:206PASS189previos+17nuevos y6RED funcionales; wholeadmission94,58/dispatcher88,28%zeroexcluded actual.26protegidos exactos/39scanningcasesAST. NativeSQLite200/400/2001 candidatos 1SELECTpor despacho/0enloop; preflight/reservefresh y6controlespostcommitfailclosed retienenstaging. Inspeccion4 yQA pendientes, ochoCA/U2/U3 abiertas, no GPU/quality/globalacceptance.

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-upload_deleted] falló con app.queue.inputs.ResolutionError: Input not owned · 2026-10-08T00:18:33.577016+00:00

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-file_deleted] falló con app.queue.inputs.ResolutionError: Input file absent or outside data · 2026-10-08T00:18:41.891649+00:00

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_input_race_between_resolve_and_reserve[False-file_changed] falló con app.queue.inputs.ResolutionError: Input changed during staging · 2026-10-08T00:18:44.934553+00:00

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[200] falló con AssertionError: {'candidates': 200, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [200, 200], ...}

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[400] falló con AssertionError: {'candidates': 400, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [400, 400], ...}

RED: apps/server/tests/test_dispatcher_scanning.py::test_native_durable_gpu_screen_once_per_dispatch_snapshot[2001] falló con AssertionError: {'candidates': 2001, 'database': 'native file SQLite head0005', 'adapter': 'synthetic Catalog', 'occupancy_selects': [2001, 2001], ...}



## Entrega técnica portable-native-qa2 para revisión independiente

2026-10-08T00:31:58.447308+00:00: Dependencia tecnica portable/fixtures aceptada por root:6fuentesactuales,106PASS5skip y4modulos completos >=80%zeroexcluded. Node22.23.2/pnpm9.12.0 nativos aislados/2933payloads+2originmeta protegidos;LinuxCPU helperactual links ytokenrechazoantesborrado pasan/owncontainereliminado. Limitaciones historicas/TOCTOU/incidente reporteLinux conservados; root corrigio solo cabecera de revision, ledgerlint actual0/0, originalQA lint0/1 preservado. SeisCA web/transitivo/envbootstrap/DockerNode/E2E/T08 pendientes.



## Revisión de componente T-04 — t04-u1-component-inspection4

2026-10-08T00:34:34.049753+00:00: A+D limpias; B4-01 Important de source.open tras validación de ruta. Sonda revisor AST/intercalación FS simulada. Root elige normalización en punto de lectura dentro inputs, conservando PreclaimResolutionError y propagación de destino/commit. RED con FS y SQLite nativos antesfix; siguiente componente5 sin reset/deuda, QA U1 pendiente,206PASS anterior cualificado. TDD n/a: adjudicación/prosa.


## Entrega técnica dispatcher-input-open-fix4 para revisión independiente

2026-10-08T00:45:50.858316+00:00: B4-01 corregido solo inputs+test:215PASS206previos+9nuevos,2RED filesystem/SQLite nativos previos. Wholeinputs116/13486,57%zeroexcluded/sourcecurrent;26protegidos y39+17ASTprevio exactos. Catchsolo sourceopenFileNotFound;causatypechainconservada/destino/lectura/fsync/mkdir/cleanup propaganfailclosed con7controlesbaselinePASS. Inspeccion componente5/QA U1 pendientes, ochoCA/U2/U3/GPU/quality abiertos.

RED: test_native_source_disappears_after_staging_confinement[False] falló con FileNotFoundError · 2026-10-08T00:35:33.180210+00:00.

RED: test_native_source_disappears_after_staging_confinement[True] falló con FileNotFoundError · 2026-10-08T00:35:39.144392+00:00.



## Revisión de dos lentes — intento 5: T04 U1 componente conforme

2026-10-08T01:01:45.854807+00:00: A+B+D0Critical/0Important/0Minor. B4-01 corregido;215PASS/inputs86,57%wholezeroexcluded; lectura propia sin rerun funcional. QA U1 actual independiente siguiente; U2/U3 y ocho criterios generales abiertos. No aceptación por revisión. TDD n/a: arbitraje/prosa.


## Entrega técnica dispatcher-u1-native-qa1 para revisión independiente

2026-10-08T01:10:11.396286+00:00: Root acepta sólo dependencia técnica U1:215PASS190U1+25vecinos,6móduloswholecadauno>=86,57%zeroexcluded,72fuentes62protegidos/inventario/136SQLite0005 verificados; wheelactual75369bytes/import realextracciónpropia sin torch. No Docker/Linuxcleaninstall ni GPU/realtime/fullT04/U2/U3/8CA/Git/M1. Próximo U2 eventosretryrecoverycancelLifespan. TDD n/a QA independiente; errores privados de finalizador preservados sin rerun tests. Incidente root publicación BOM corregido en lector privado; informe parcial se compara exacto y no se sobrescribe.



## Continuación autónoma — T04 U2 ciclo de vida

2026-10-08T01:11:43.427578+00:00: U1 técnico aceptado215PASS/6whole/source72/protected62/nativeSQLite136/currentwheel; implementador fresco recibe events/retry/recovery/cancellation/runtime, admission/dispatcher/main y5tests nuevos. Sin tablas/schema/health/infra nueva, busmemoriaacotado aftercommit. Conserva ausencia vsunknown, cursor/terminalatómicos, IDmisma recuperación y3totales/offloadúnico, cancelnoquitaocupación poracuse. Redfuncional/TDD/wholeEACH80zeroexcluded/revisión/QA obligatorios. T05/T06endpoint/U3/cadenas/Git/M1abiertos. Peso4estimado/realNULL.


## Revisión de dos lentes — intento 1: T08 transitivas, precisión documental

2026-10-08T01:20:09.456495+00:00: A+B1Importantfusionado(A01/B01) y1Minor(A02);609paquetes nativos/75casos/2aliasbyteidénticos ymapas íntegros verificados porlectura propia. El auditor DATA rechazó duplicados, no pnpm productivo; helpers historial tiene1exit1conservado yfinalexit0. Rootcorrige sóloprosa en candidato nuevo, noorigen/archivevalidator/fuentes ni pnpm ejecución. Revisión2 fresca antesadoptar, permisosprácticosprivados/redistribución diferenciados. TDD n/a prosa, no tests/coverage requeridos.


## Revisión de dos lentes — intento 2: T08 transitivas conformes y uso local autorizado

2026-10-08T01:26:28.019450+00:00: A+B0Critical/0Important/0Minor; A01/B01 yA02corregidos sin cambiar609filas/manifiesto/predecesor. Rootacepta cualificación e incorpora registro609/SHAcondiciones/ADR0051, permite23pins+lockcongelado+pnpmverificado ignore-scripts ydosTAR exactos con1colisiónbyteidéntica12miembrosregularescadauno. No permiso general deextractor ni cambiofetch_web_tools. Canonicalpackage/lock/instalación/compatibilidad/UI/Docker/E2E/redistribución siguenpendientes; no T08CA/Git/M1cerrados. TDD n/a prosa/config; próximoimplementador env/bootstrap ymanifiestos bajoTDD para códigoygatesfresh.


## Continuación autónoma — T08 entradas de herramientas y manifiestos

2026-10-08T01:33:39.535726+00:00: traslegal2ABsin gaps/ADR0051, implementadorfresco recibe env/bootstrap/wrapperspnpm/testsentrypoint yappswebpackage+lock, diezpaths exclusivos. UsaNode22.23.2/pnpm9.12.0 exactosmanageraceptado6fuentes/2935payloadsprotegidos, noambient/profile/Corepack, frozen ignore-scripts yconfigconfinada. JSON/YAMLTDDn/a; shell/Python REDfuncionalantescódigo/coberturaPythonwhole80zeroexcluded ypruebasnativasPS/Linuxnegativoapropiadas. Instalar23pins/609fijoslocal autorizado, noresoluciónnueva niUI/DockerLinux/basebrowser/redistribución/T08aceptados. Peso3estimado realNULL.


## Revisión de componente T-04 — t04-u2-component-inspection1

2026-10-08T02:02:37.696891+00:00: U2 inspection1 A+B+D terminal: 0Critical/3Important/1Minor after deduplicating A/B. Residency and original-cause probes executed in memory with synthetic backends; SQL/HTTP cost static estimates, no benchmark by reviewer. Current324PASS2skip plus2HTTP supplemental qualified. Fresh correction owns runtime/retry/main and retry/lifespan tests, five existingfiles; whole threeprod80zeroexcluded/nativeSQL count regressions beforefix. U1accepted215 retained, U3/T05/T06/T07/eightCA remain pending. Next U2inspection2/independentQA withoutreset. TDD n/a: adjudicación/prosa.


## Declaración de alcance T08 ? entrypoints ya autorizados

2026-10-08T02:10:46.512119+00:00: root a?ade ocho rutas exactas de env/bootstrap/wrappers/tests al campo Archivos de T08. La delegación original ya las enumeraba; scope-check previo detect? su ausencia literal (ocho fuera, dos dentro), antes de lanzar ning?n revisor. Fallo y fixture previos preservados; ninguna implementación, permiso nuevo, test o aceptación se cambia. TDD n/a: prosa. Revisión componente1 sigue siendo1.


## Revisión de componente T-08 — t08-tool-entrypoints-inspection1

2026-10-08T02:22:21.273507+00:00: EntryPoints inspection1 A clean B1Important: nestedpnpm rootgen command cannot find manager because PATH onlyNode. Staticreview not actualwrapperexecution. Rootnext freshfix owns pnpm.py+entrypointtests only, retains prior43/whole96,70 and23pins/609licensedlock/install482 qualifiers. ActualparentCLI priorunit1exit1 metadata collision / CHILDexitUNKNOWN preserved, no0invented; sourceinventory81081+1500links exact. Rootscope8declarations and790CRtransport incident correctedprosa beforeanyreview, scope/taskbrief/ledger0, sources unchanged. Fix2inspectionnext (componentcounter2), no T08/UI/build/Docker/E2E accepted. TDD n/a: adjudicación/prosa.


## Revisión de componente T-04 — t04-u2-component-inspection2

2026-10-08T02:58:51.100425+00:00: U2inspection2 A1Important/B2Important/Dclean, dedup=>2Important0Critical0Minor. Globalprioritybetweenretryandqueued (static+inmemoryAproof), readercancelrace executorreal/generatorblockedsynthetic (notnativeconnectionleakproof). Rootselects oneglobalorderedarbitration, nativeSQLreaderpendingcleanup causal tests beforecode, up toseven existingfiles permitted runtime/retry/dispatcher/admission +testsretry/scanning/admission; minimizeactualchanges. Prior386PASS2skip+2HTTP preserved/currentwhole3 zeroexcluded67protected; originalrootallocation3 notactorprosa4. NextU2inspection3 no reset, U1five/QA remain qualified; U3/T05/T06/T07/eightCA/fullDockerGitintegration pending. TDD n/a: adjudicación/prosa.


## Revisión de componente T-08 — t08-tool-entrypoints-inspection2

2026-10-08T03:07:22.496648+00:00: EntryPoints inspection2 A clean B0Critical0Important1Minor concurrent shim initialization. In-memory reviewer proof, fresh NativeWindowsFS causal RED before minimal fix. Two owned existing files, prior55PASS/whole97,41zeroexcluded preserved. Official2935/six helpers/locks/currentapps/prior proofs unchanged. Nextinspection3/QA; no T08/UI/Docker/E2E/quality acceptance. Rootweight1 actualNULL. TDD n/a: adjudicación/prosa.


## Revisión de componente T-04 — t04-u2-component-inspection3

2026-10-08T03:25:10.316836+00:00: U2inspection3 A1Important, B/Dclean. Actualsharedexpunge_all/streaming ORM mechanism valid: reviewer executed in-memory SQLite801 partitions, notfullruntime nativefile. Rootchoose freshminimal fix3 owning admission+testretry+testscanning only, runtime/retry/dispatcher allprotected. Genuine nativefileSQLite0005 interleaved >400 both populations RED beforecode required, preserve426PASS2Windows skips/+2HTTP separate/currentwhole. Rootautonomous continuation beyondregular3, next4 no reset/debt, U1five/QA preserved, U3/fullT04/eightCA remainopen; estimate1,5 realNULL. TDD n/a: adjudicación/prosa.


## Revisión de dos lentes — intento 3: T08 entrypoints, componente aislado

2026-10-08T03:37:59.906546+00:00: A/B0Critical0Important0Minor;65PASS/currentwholepnpm96,36zeroexcluded reviewed. Nativeconcurrentcompletepublication/foreignbytes preservation and nestedargs exit37 retainoldasserts. RootactualcanonicalpnpmgenPASS/TypeScript12sources byteexact, no sentinelonlyclaim. QA independentcurrent65 baseline next; sixfrontendCA/build/UI/DockerLinux/E2E and taskGit remainopen. Counters preserved, QAestimate1,5 actualNULL. TDD n/a: adjudicación/QA.


## Revisión de dos lentes — intento 4: T04 U2, componente aislado conforme

2026-10-08T03:44:51.598601+00:00: A/B/D0Critical0Important0Minor; A3-01 corregido con detachporfila de paginaqueued, conserva sharedWAL ycursorretry.428PASS2Windows skips/2HTTPseparadas/currentwholeadmission94,66zeroexcluded contrastadossololectura. QA U2 independiente actual8modulos/base428 siguiente, rootpreserva counters4/U1cinco yautonomia masalla3 sin aceptar deuda. U3/T05/T06/T07/eightCA/fulltask/Git/quality abiertos. PesoQA2estimado/realesNULL. TDD n/a: adjudicación/QA.


## Entrega técnica tool-entrypoints-native-qa1 para revisión independiente

2026-10-08T03:50:52.689093+00:00: Root acepta solo entrypoints tecnicos:65PASS (canonicas+4helpers)/pnpm159de165=96,36wholezeroexcluded/fuentes27/tools2935 exactos/namespacepropio vacio/inventario verificado. Rootcanonicalgen realPASS TypeScript12sourcebyteexact. PID/UTC/argv/exit/bytes dondeobservados; FILETIMEJob/desconocidos UNKNOWN. GlobalplanCoverage advierteT00sinmapping, no E2Egreen/UI/T08/M1 aceptados. Storemutablevacio nocleanofflinebootstrap. Nuevabaseweb aprobada siguientecon23pins609licencias exactas sin nuevasdeps noauditas. HistorialCLIexitUNKNOWN/erroresfixture/prosacontadores preservado, actualmodeloTokensEURIAhoursNULL. TDD n/a QA independiente.



## T04 U2: QA2 independiente tras incidencia de confinamiento

2026-10-08T04:09:01.254947+00:00: QA1 funcional428PASS2skip y2HTTP, primera corrida creo artefacto nuevo en fase historica por literal copiado. Originales historicos verificados sin modificar ni borrar; no aceptacion. QA2 justificada con fuentes e inspeccion4 iguales; arranque archivado antes de ejecutar, rutas privadas corregidas antes de primera prueba. RealesNULL/peso2 estimado; T04 abierto.


## T08: implementacion bounded de la interfaz base

2026-10-08T04:09:01.527331+00:00: Toolchain aceptada65PASS/whole96,36 y gen real0. Base AppRouter/tema/tokens/i18n/nav/player persistente/clienteAPI y eventos con23pins licenciados existentes sin nuevas dependencias. T08/E2E/Docker/flujo musical abiertos. Config Vitest migra caches fuera de fase historica antes de ejecutar. TDD causal wholecada runtime>=80zeroexcluded; peso5estimado/realesNULL.


## T08: cualificación documental del aviso DOC-00

T00 sí tiene Cubre(tests): DOC-00 y bloque DOC-00 en test-plan. El aviso del checker no reconoce ese prefijo: limitación del parser, no falta de mapping. Se conserva decision/log original y se publica suplemento; no se altera plugin ni se asigna M03 ajeno. Gate UI global sigue pendiente. TDD n/a: prosa.


## T04 U2: aceptación técnica acotada de QA2

2026-10-08T04:18:00.529687+00:00: 428PASS2Windows skips y2MockTransport separados; ocho módulos completos90–96,30%ceroexclusiones, una baseline fresca sin unión histórica. Root verificó94fuentes,27739artefactos históricos e inventario privado. Incidencias de auditor privado preservadas y corregidas sin rerunpytest. Inspección4A/B/D limpia y contadores sin reset; U1cinco. FILETIME/Job/UTCbootstrap no observados UNKNOWN, ninguna GPU/E2E/socketHTTP. U3 siguiente; ochoCA/fullT04/Git abiertos. [Aceptación](testing/t04/dispatcher-u2-native-qa2-root-acceptance.json). TDD n/a: QA/adjudicación.


## Entrega técnica dispatcher-u2-native-qa2 para revisión independiente

2026-10-08T04:18:08.951251+00:00: QA2 independiente U2 aceptada dentro de su alcance; sin cierre T04/Git/E2E/GPU.



## T04 U3: cadenas, referencias y reintento manual

2026-10-08T04:18:09.594013+00:00: Tras aceptacionU2 actual se ejecuta U3 aprobada por diseñoO1/ADR0047: chain atomicaN->post.audio->Nbeats, inputsreferencias, failed dependency/manualretry nuevojob ysolo takesfailed. Server CPUpostreal/T05 e I01 batchserie permanecenpendientes; sin inventarassetsready/modelodescriptor verified. Wholecadachangedruntime>=80zeroexcluded/TDDcausal; peso4estimado/realesNULL.


## Revisión de dos lentes — intento 1: T08 basefrontend, correcciones autorizadas

2026-10-08T04:43:00.356651+00:00: A/B/C terminal; root0Critical3Important1Minor: SSEsobreengine incompatibleglobal,404English,canonicalbuildSWCcachefail ylayout144/120vs64/72. C limpia. Rootautoriza fixboundedeightpaths incluyendo nuevosnot-found/test y pnpm.py/testentrypoints ya ArchivosT08; no waiver. Originales/probe realbuildexit1 y.nextprevio conservados. FixtureSSE equivocada se corrige con autorización explícita preservando escenarios/asserts de intención y añadiendo regresiónantecódigo; old112lyrics/65tooling intactos. Countersbase1 ytooling3 distintos; T08 abierto/peso3estimado/realesNULL.


## Entrega técnica frontend-base-unit1 para revisión independiente

2026-10-08T04:44:30.566813+00:00: Entrega provisional133PASS y12whole100%; inspeccion1 marca3Important1Minor y buildcanonicoSWCcacheexit1. Fix1 autorizado; no aceptacion T08/UIE2E/Docker.



## Revisión de componente T-04 — t04-u3-component-inspection1

2026-10-08T05:05:44.476926+00:00: A/B/D terminales: 0 Critical, 2 Important deduplicados, 0 Minor. Reintento tras post fallido y consultas N+1 requieren RED SQLite real y corrección acotada; no se cierra T-04. TDD n/a: adjudicación/prosa.


## T-08 — diagnóstico acotado de compilación SWC

2026-10-08T05:06:24.920098+00:00: Frontend fix1 terminal con 137 tests web verdes y build nativo bloqueado por confianza ACL de ancestros. Se delega diagnóstico privado de alternativas soportadas frente a Docker, sin tocar permisos, dependencias ni producto; T-08 sigue abierta.


## Entrega técnica frontend-review1-fix1 para revisión independiente

2026-10-08T05:09:25.617448+00:00: Entrega parcial: 137 web PASS y 68 Python PASS/1 FAIL; build nativo y transform SWC siguen exit1. Root verificó inventario1904 archivos/604directorios y fuentes actuales; no aceptación. Diagnóstico privado de ruta segura Docker/nativa en curso, sin modificar ACL compartidas.



## T-08 — prueba privada de build Linux offline

2026-10-08T05:14:09.428523+00:00: Root elige ruta Docker ya aprobada, tras diagnóstico SWC y sonda CPU de imagen Node22.23.3/Alpine3.24.2/licencias presentes, contenedor propio eliminado. Sólo prueba privada offline, sin tocar producto/ACL/servicios; hostbuild sigue rojo. Ensamblado, ABI y build reales requieren evidencia.


## Entrega técnica u3-review1-fix1 para revisión independiente

2026-10-08T05:28:03.135922+00:00: Corrección entregada:506PASS2skip/cinco WHOLE89,63–98,80sinexclusiones;SELECT nativos400beats2404→11 y64post132→6. Retry exige fallo post propio con gen succeeded o lógico failed trasdone. Custodia actual verificada para inspection2A/B/D, Aen curso; sin cierre T04 ni aceptación QA. Publicador bloqueó ruta personal del CLI histórico en receipt; original preservado y anonimización corregida, incluyendo incidente de indentación privado, sin repetir tests.

RED: apps/server/tests/test_queue_manual_retry.py::test_queue_manual_retry_succeeded_generation_own_post_failure_native falló con Owned failed generation required · 2026-10-08T05:07:45.141707+00:00

RED: apps/server/tests/test_queue_references.py::test_queue_references_400_ready_beats_native_query_bound falló con AssertionError: 2404 SELECT >16 · 2026-10-08T05:08:48.042833+00:00

RED: apps/server/tests/test_queue_references.py::test_queue_references_shared_64_post_inputs_native_query_bound falló con AssertionError: 132 SELECT >8 · 2026-10-08T05:08:57.725625+00:00

RED: apps/server/tests/test_queue_manual_retry.py::test_queue_manual_retry_failed_logical_done_cannot_skip_post_authentication falló con DID NOT RAISE ValueError · 2026-10-08T05:18:39.455632+00:00



## T-08 — handoff de la prueba Linux al producto

2026-10-08T05:33:25.488938+00:00: Prueba Linux terminal0:493paquetes27710files/SWC+Next musl+build0/638licencias. BaseNode22.23.3Alpine3.24.2; AUTHresolverincidente y warningHOME trazas conservados. Root solicita handoff privado de implementación Docker y verificación canónica, sin cambiar producto/tests ni dispensar hostbuild.


## T04 U3: QA1 nativa independiente tras inspección2

2026-10-08T05:36:17.390101+00:00: Fuentes actuales y revisiones2 A/B/D se cotejan antes de despacho; QA dirigida actual506casos2skips concinco WHOLE, SQLite real y límites sintéticos conservados. U1/U2contadores intactos, noT05/I01/fullT04.


## T-08 — entradas estables y contexto selectivo de Docker

2026-10-08T05:46:02.663168+00:00: Root adopta handoffA, fusiona U1importación/U2contexto en cuatro ficheros nuevos. Nuevos locks Linux/base+609archives cotejados SHA512/SHA256/bytes, sin alterar pinWindows ni pnpm-lock. ActualFULLLinuxbuild0 es dependencia limitada; hostSWCpositivo permanece rojo. TDD/WHOLEcada2/review/QA antesaceptación.


## T04 U3: QA2 tras causa de bootstrap privado

2026-10-08T05:58:41.119680+00:00: QA1 final505PASS1FAIL2skip conservado,80protegidos/6613artefactosrootexactos; raízconftest usa STUDIO_TEST_ROOT anidado y siete padres quedan dentro repo. Nuevo namespace propio somero explícito, source/assertsinvariantes y94copiasantesprimercaso, diagnóstico puntual primero ybaselinefreshuna. Inspección2A/B/Dmisma/countersconservados; T04sinaceptación.


## Entrega técnica u3-native-qa1 para revisión independiente

2026-10-08T05:59:37.272074+00:00: QA1 CONCRETE_CONCERN: tercera corrida actual505PASS1FAIL2skip, mismos cinco módulos89,63–98,80; fallo privado siete padres/tmp_path yprecedencia rootconftest, sin defecto U3 probado ni cambio de assertions. Tresoriginales conservados/6613artefactos80protegidosrootexactos. QA2 autorizada con namespacepropiosomero ydiagnósticoexactoprimero; inspección2misma, countersnoreset.



## Entrega técnica linux-offline-build-proof1 para revisión independiente

2026-10-08T05:59:37.662118+00:00: Prueba privada limitada:493paquetes27710files/609SHA-SRI/SWC+Nextmusl ybuild0/638licencias. Rootcustody2893files535dirs91sources actuales8rootprotegidos exactos; único drift histórico docslegal escrito por root se cualifica, no rollback. AUTHresolverincidente/tracingHOMEwarning/hostWindowsred conservados; sin aceptación de despliegue/T08. HandoffAfullclosure adoptado y unidadentradasestablesen curso.



## Entrega técnica u3-native-qa2 para revisión independiente

2026-10-08T06:15:44.810143+00:00: QA2 terminal exit0, 506 PASS/2 SKIP, cinco módulos actuales WHOLE 89,63-98,80 sin exclusiones. Auditoría root cotejó 3070 archivos originales y 80 protegidos; cierre ampliado actual de 113 fuentes exacto. Sin cerrar T04 ni T05/E2E/Git; aceptación final acotada pendiente al retomar por petición de parada del propietario.



## Parada solicitada para apagar el ordenador

2026-10-08T06:27:22.369342+00:00: Parada expresa para apagar. U3 QA2 terminal0 506PASS2SKIP publicada, aceptación final acotada pendiente. T08 baseline-current48PASS1FAIL; baseline-final y CLI propios interrumpidos por parada, exit4294967295, fuentes actuales preservadas/difieren de primera baseline; sin entrega o cobertura actual aceptada. Revisión/QA pendientes al reanudar. Ninguna tarea cerrada.


## T04 U3: aceptación técnica acotada de QA2 tras reanudar

2026-10-08T18:14:22.463510+00:00: 506PASS2SKIP Windows, cinco módulos completos89,63–98,80%sinexclusiones. Root coteja113fuentes actuales/80protegidos/3070originales/JUnit/JSON contra datos oficiales. Inspection2 limpia y counters U1cinco/U2cuatro/U3dos conservados. T05 real/I01/E2E/M01/ochoCA/Git pendientes, T04 abierta. [Aceptación](testing/t04/u3-native-qa2-root-acceptance.json). TDD n/a: adjudicación de QA.


## T05: primera unidad de portabilidad y decisión de ejecución CPU

2026-10-08T18:22:31.951276+00:00: ADR0053 elige hijo propio sin BD y publicación por padre; sólo primera unidad root/schema autorizada ahora. Namespace app.worker corresponde al wheel actual, reemplaza la ruta planificada apps/server/worker; sin código worker aún. TDD n/a: decisión/prosa. Ownership inicial dos módulos audio-post, recurso schema derivado byte exacto, pyproject sólo si empaquetado requiere y dos tests nuevos; contracts/locks/cola/server intactos. Resto de procedencia, migración, beats y FFmpegLinux pendiente. T05 en-progreso, ningún CA cerrado por diseño.


## Revisión de dos lentes — intento 1: portabilidad T05 U1 y entradas T08 U1/U2

2026-10-08T18:40:38.152444+00:00: baselines actuales228PASS4SKIP y59PASS0SKIP, cuatro módulos WHOLE90,91–96,24%sinexclusiones (cada baseline por unidad, sin unión). Root verifica4276+462originales/nuevefuentes yprotectedscope; CONTINUE cambió por root, declarado. Scopecheck0 sin avisos sobre fixtureaislado; sharedWIP no descartado/revertido. A/B y suplementarias C/D por autoridadFS/coste609archivos. Lentes frescas pendientes, ninguna aceptación aún. Countersfrontendhistóricos conservados. TDD REDhistorias originales enentregas; líneas concretas se incorporan al validar reviews.


## T05: adquisición FFmpeg Linux por implementador fresco

2026-10-08T18:50:59.892427+00:00: ADR0054 y fila legal LGPLv3 registrada antes de código. Sólo dos archivos nuevos de adquisición/tests y pinLinux independiente. Agent nativo rechazado por límite de threads: fallbackCLIephemeral con mismo brief/TDD/gates. Descarga137863452bytes explícitamente autorizada. RuntimeLinux/Docker/audio/cancelación posteriores, no cierreT05.


## Adjudicación portabilidad: intento 1

2026-10-08T18:55:25.873216+00:00: A/C/D cero hallazgos; B1-01 Minor integrity null/int produce AttributeError en vez INVALID_LOCK/CLI2 antes publicación, corregir. ROOT1-02 Important: fixtures permanentes de T08 hardcodean PHASE/COPIES/ARCHIVES de historial privado; ambas FileNotFoundError con source-copies ausente en probe propio sin borrar historia. Fix autorizado sólo helperfetch y dos testsweb, revisión2 después. Audio T05 U1 actual sin defectosrevisión, QA independiente pendiente; ningún fullCA/T05/T08/M1 aceptado. Predossier7fuera scope/backticks+baselineweb tomado deT05preimage preservado y reparado antesdespacho; scopeactual9/0. Fuente1885 cambiolegal exclusivo root posterior registrado. TDD n/a adjudicación; actorfix requiere causalRED nuevo.


## T05: QA independiente de portabilidad U1

2026-10-08T18:57:57.913612+00:00: A/B/C/D sobre audio U1 sin hallazgos; rootfinding fixtures/BMinor afectan sólo web T08, no modifican audio. QA fresca readonly CPU/audio real/instalación privada autorizada contra fuentes actuales, no Docker/GPU/E2E/fullT05. Fallback CLI por límite lifetime Agent; no metadata nativa inventada.


## T08: fix de revisión1, fixtures actuales y error tipado

2026-10-08T19:03:45.045217+00:00: ROOT1-02 Important y B1-01 Minor confirmados. Ownership helperfetch y dos testsweb, runtimecontext sin cambios. Preparación/tools canónicos locales autorizada sin red; datos históricos privados intactos. Revisión2 y QA después, sin cierreT08.


## T05 U1: aceptación técnica de portabilidad tras QA independiente

2026-10-08T19:05:03.684612+00:00:228PASS4Windows symlinkSKIP, WHOLEpipeline96,24/manifest92,40ceroexclusiones,56fuentes y143originales cotejados. Esquema canónico byteexact; wheel/sdist/instalación actuales19artefactos retenidos, cuatrojunctionnativePASS. Root conservaTOCTOU/PIDnietosUNKNOWN y Linux/Docker sin probar. A/B/C/D audio sin gaps; hallazgosweb se corrigen aparte. T05/fullM1 siguenabiertos; siguiente workerlocalcontract/FFmpegLinux. [Aceptación](testing/t05/portable-audio-post-qa1-root-acceptance.json). TDD n/a adjudicaciónQA.


## Entrega técnica portable-audio-post-qa1 para revisión independiente

2026-10-08T19:05:38.912681+00:00: QA independiente U1 publicada y aceptación técnica acotada root guardada: 228PASS4SKIP, dos módulos WHOLE actuales96,24/92,40. FullT05/DockerLinux/worker/manifest takes reales siguen pendientes.



## T05 adquisición FFmpeg: fix de revisión1

2026-10-08T19:23:47.200084+00:00: A/C limpias; B dos Important confirmados: lock huérfano al fallar .owner antes finally, y --check no detecta falta de bits ejecutables Linux. B01 rootreproducido controlado sin red. Implementerfresh CLI fallback corrige dos archivos sin cambiar pin ni carga oficial. Revisión2/QA después; no fullT05.


## Revisión de dos lentes — intento 1: adquisición FFmpeg Linux

2026-10-08T19:24:54.525601+00:00: A/C0hallazgos, BdosImportant (B01ownlockantesfinally orphanconfirmedroot; B02Linuxxmode checkmissing estático, REDactual requerido). CLIreviewers0, scope2/0, fuenteactualwhole87,32/45PASSnoaceptación. Fix1frescoencurso exec11656 sólohelperytests, flags/licenciaABI/Linuxruntime pendientes. [Revisión](testing/t05/ffmpeg-linux-review1.md). TDD n/a adjudicación, siguienteactorRED+GREEN yreview2.


## T05: contrato durable de worker y publicación

2026-10-08T19:32:10.745357+00:00: Diseño acotado readonly tras U1portable aceptada y ADR0053 O2. Aclara esquema local CPU, intent FS/SQLite, procedencia ganadora, variantes parciales y beats; sólo artefactos privados, root decide/ADR antes código. No fakeengine ni cierreT05.


## Entrega técnica ffmpeg-linux-review1-fix1 para revisión independiente

2026-10-08T19:57:32.108497+00:00: Entrega fix1 terminal CLI0: 58PASS, módulo WHOLE88,12665% sin exclusiones; root cotejó315originales y2fuentes actuales exactos. Review2/QA y runtimeLinux pendientes, sin aceptación T05. Petición de parada: no iniciar nueva fase.



## Entrega técnica durable-publication-contract-design1 para revisión independiente

2026-10-08T19:57:32.188103+00:00: Diseño readonly terminal CLI0 guardado; root cotejó55originales y43fuentes exactas. source_count array en receipt no es entero válido;43 se deriva del mapa. P1 propuesto, adopción ADR/schema e implementación pendientes. No tests/aceptación; parada tras suiteweb vigente.



## Revisión de dos lentes — intento 2: adquisición FFmpeg Linux

Revisión2 iniciada A/B frescas y C suplementaria por custodia filesystem, alcance dos archivos/0 fuera/sin avisos. Baselinefix1 actual58PASS/334de379=88,12665%whole cero exclusiones. Counter1 y sus dos Important conservados; no aceptación antes de veredictos y QA. Actores CLI genéricos por cuota nativa agotada, metadata real al terminar.

## T05: adopción del contrato durable por toma

ADR0055 adopta P1 bajo delegación autónoma. Migración siguiente disponible0006 comprobada; U2a limitada a contrato, tablas/invariantes y snapshots con contenido causal y privacidad. Identidad raíz estable y revisiones inmutables por intento; no UNIQUE global del ganador/índice que impida retry de la misma salida. Procedencia histórica opcional, nueva publicación exige evidencia. Capacidad CPU2/runtime y AnalysisImport se integran en unidades posteriores, no simuladas por tablas. Archivos de T05 ampliados explícitamente por contrato/migración empaquetada y tests necesarios. T05 sigue en-progreso, ningún CA cerrado. TDD n/a: decisión/prosa.

## Continuación autónoma confirmada por el propietario

El propietario revoca la parada con «no dejes el objetivo pausado hasta que no esté todo implementado». Objetivo completo activo; no pausar al acabar la suite actual. Toda aceptación sigue requiriendo sus gates reales.


## T05 U2a: implementación del contrato local durable

2026-10-08T20:05:41.202785+00:00: ADR0055P1 adoptada,0006 disponible, primeraunidad sólo contratos/modelos/invariantes/migración/snapshots. Hijo/runtime/publicaciónfilesystem/provenancecapture/beats/CPU2race reales posteriores. FreshCLIfallback cuotaAgent, TDD ywholecada módulo80ceroexclusiones; sin tocarqueue/audio/helpers activos. FullT05 pendiente.


## Adjudicación FFmpeg Linux: intento 2

2026-10-08T20:07:31.784749+00:00: A/B/C terminalesCLI0 y0hallazgos nuevos; B01/B02 corregidos causalmente. Dosfuentes actuales exactas; baseline58PASS/WHOLE88,12665%ceroexclusiones. QA independiente siguiente, sin aceptación T05/Linuxnativo. [Revisión2](testing/t05/ffmpeg-linux-review2.md). Historial1 preservado; TDD n/a adjudicación.


## T05: QA independiente de adquisición FFmpeg Linux

2026-10-08T20:08:14.541410+00:00: Review2 A/B/C0gaps tras fixB01/B02. QA fresca readonly unit adquisición, fuente actual2files y fijación global payload; Linuxnativo/Docker/ABI/binlicense/fullT05 pendientes. CLI genérico rol QA por prompt, launcher tierdefault implementer no override fingido.


## T05 U2a: entrega incompleta y división de alcance

2026-10-08T20:10:37.548604+00:00: CLI0 no implica implementación: no cambios/tests/RED/cobertura,11owned intactos. Sin bloqueo técnico demostrado; root divide contratos U2a1, migración/invariantes U2a2 y snapshots U2a3 con gates propios. Riesgo de schema compartido con freezeweb descubierto tras lanzamiento, resuelto al comprobar ningún cambio; próxima unidad schema espera suiteweb terminal. Historia incompleta conservada, no replay. T05 abierta, objetivo activo.


## T05 U2a1: contrato privado verificable antes de migración

2026-10-08T20:11:36.924088+00:00: La unidad amplia anterior terminó incompleta sin código y11owned exactos. Se divide: ahora3archivos contratos/test, sin models/schema/snapshots ni overlapweb. RootprevioADR0055 vigente; TDDcausal ywholemodule>=80ceroexcl, reviewQA luego.


## T05: adquisición FFmpeg aceptada técnicamente tras QA independiente

2026-10-08T20:16:33.380417+00:00: review2A/B/C0gaps, QA58PASS0fallos/whole334de379=88,12665%ceroexclusiones. Root coteja211originales/10fuentes/70payload SHA exactos. Sólo adquisición Windows; Linuxnativo/ABI/flags-binlicense/Docker/worker/E2E/fullT05 pendientes. FinalizadorQA ExitCodeNULL UNKNOWN conserva, baseline/check/export0 Popen reales. [Aceptación](testing/t05/ffmpeg-linux-acquisition-qa1-root-acceptance.json). Ningún CA ni tarea cerrado; TDD n/a adjudicaciónQA.


## Entrega técnica ffmpeg-linux-acquisition-qa1 para revisión independiente

2026-10-08T20:16:33.461041+00:00: QA independiente adquisición Windows técnicamente aceptada por root:58PASS/WHOLE88,12665%sinexcluidos,211originales yfuentes/payload actuales verificados; límites nativoLinux/fullT05 yfinalizadorNULL explícitos enaceptación. No repetir suite.



## T05: verificación nativa Linux de FFmpeg adquirido

2026-10-08T20:18:20.261097+00:00: AdquisiciónWindows accepted58PASS/review2QA. PruebaLinuxCPU Docker aislada autorizada por objetivo/despliegueDocker, imagenPythonbase existente fijada, sinred/GPU/servicios ajenos. Checkreal/ABIflags/modosLinux/noreplace/smokeCodec ennamespaceprivado, no workerfullT05.


## Entrega técnica durable-contract-unit2a1 para revisión independiente

2026-10-08T20:25:16.428282+00:00: Unidad3archivos implementada74PASS/finalofficialsingleWHOLE97,81022%sinexclusiones, entregada parareview1 A/B/C/D yQA. NO DB/migración/snapshots/runtime/SQL/CAS/FS probado, ningunfullCA/T05/M1 aceptado.



## T05: aceptación técnica Linux de FFmpeg y primitiva no-clobber

2026-10-08T20:30:51.781432+00:00: Bookwormamd64 basePythonfijada:check/ABIversion/flags/sintéticosWAV-FLAC-MP3/modosX reales/renameat2EEXIST testigos preservados.14fuentes/242originales/69payload exactos; doscontenedores propios eliminados, fallo inicial de fixture permisos conservado. Conteo anterior70=69payload+1cachearchivo, no artefacto perdido. SelfreportLGPLv3+/version3sinGPLnonfree; avisos completos/redistribuciónUNKNOWN. No acquireLinuxcompleto/worker/imagenserverfull/E2E/T05/M1aceptados. [Aceptación](testing/t05/ffmpeg-linux-native-container-qa1-root-acceptance.json). TDD n/a adjudicaciónQA.


## T08: corrección causal del bootstrap586 por versión exacta

2026-10-08T20:34:57.059050+00:00: Baseline actualnative terminal64PASS1FAIL: test_original586_missing23 omite24por name-onlypostcss8.5.23y8.5.29, directoactual8.5.29. Metadatos name+version reproducen23, no cambia producto/pins. Fixturetest only, originalassertfaltan23 ydestnoeffect intactos. Unidadescontracts/modelsschemas siguientes ya pueden avanzar traswebterminal; ahorafreshCLI fix2testonly, countersreview1 preservados.


## Revisión de dos lentes — intento 1: contratos locales T05 U2a1

2026-10-08T20:36:53.173820+00:00: A/B/C/D cuatrocontextosfrescosCLI0/0gaps. Scope3/0, fuentes3actuales exactas. Csuplementariaprivacidad/rutas, Dautoworker. Baseline74PASS/whole268de27497,81022%sinexclusiones inspeccionada, no repetida porreviewers. QA independiente siguiente. No SQL/CAS/migración/runtime/FS/fullT05 acreditados. [Revisión](testing/t05/durable-contract-unit2a1-review1.md). TDDn/a adjudicación.


## Entrega técnica ffmpeg-linux-native-container-qa1 para revisión independiente

2026-10-08T20:36:53.253787+00:00: QA Linuxnativa accepted scopehelper/ABIbookworm/codecs/modosX/noreplace. Root242originales14fuentes69payload verificados; doscontainerspropiosgone. Diferencia70anterior=69payload+1cache archivo, adjudicada. No fullT05/M1/worker/adquisiciónLinuxcompleta/redistribución.



## T05 U2a1: QA independiente tras revisión1 limpia

2026-10-08T20:37:28.222545+00:00: A/B/C/D0gaps, scope3current exact. Freshreadonly QA74tests tipo-provenance-authority-path-outcomes, WHOLE contracts80mínimo0excl singletrace. Sin SQL/migración/snapshots/custodia/runtime/FS/fullT05. GenericQA prompt no modelooverridefingido.


## T06: diseño de replay SSE y contratos existentes

2026-10-08T20:39:08.781628+00:00: Análisisreadonly privado del siguiente componente independiente: EventBus/cola/auth yCA/T06, alternativa de replay/recovery sinKafkaRedis. No implementar/migrar/publicAPI/schema ni declararT04cerrada. RooteligeADRyownership antescódigo; CLIgenérico arquitectoporprompt.


## T05 U2a1: contratos tipados aceptados tras QA independiente

2026-10-08T20:44:31.818325+00:00: A/B/C/Dreview1limpia, QA74PASS0SKIP/WHOLE268de27497,81022%ceroexclusiones. Root175originales/145inputs congelados actuales cotejados. Tresfuentes aceptadas solamente; aún sin SQL/CAS/migración/snapshots/custodia/runtime/publicación/T05full. [Aceptación](testing/t05/durable-contract-unit2a1-qa1-root-acceptance.json). TDDn/a adjudicaciónQA.


## T05: diseño de custodia del grupo propio antes de runtime

2026-10-08T20:45:32.590027+00:00: Contratos U2a1 accepted74PASS trasreviewQA; schema/migración diferidos mientrasfixturewebfinal fija JSON compartidos. Análisisreadonly de grupoCPU/FFmpeg yEOFparent segúnADR0053/55, sin código ni fakecleanup. Opcionesreuso seguro vsstdlibgrupo actual, rootadoptaownership antesimplementar.


## T08: baseline reanudada roja y causa de fixture acotada

2026-10-08T20:46:43.628415+00:00:65casos64PASS1FAIL0SKIP exit1,2329,58s.470originales yparidad968antes/después delactor confirmados; ya no afirmar968currentexact trasfix autorizado. No llegó a copiar586: name-only direct23selecciona24 porpostcss8.5.23transitivo+8.5.29directo. Nombre+versión exacta selecciona23metadata, hipótesisconfirmada sinmodelo/runtimebug. Freshfix2fixture exec98057 en curso, originalassert faltan23+destnoeffects intacta. Bootstrap/parityhistórico no prueba físico586, conservado/cualificado. Native reusadoNOQA independiente, CLIanteriorNULL. [Fallo](testing/t08/stable-inputs-review1-fix-resume1-report.md). Objetivo activo; no cierreT08/M1.


## Entrega técnica durable-contract-unit2a1-qa1 para revisión independiente

2026-10-08T20:46:43.715577+00:00: ContratoU2a1 aceptadotécnico trasQA74PASS/97,81022%whole. Root175originales/145inputs cotejados,3fuentes actuales. No SQL/CAS/migración/snapshots/media/custodia/runtime/FS/fullT05.



## T06: decisión SSE O1 con recuperación de estado

2026-10-08T21:00:15.010679+00:00: ADR0056 adopta busbuffer256+epoch/replay/snapshot con límites, sinoutbox/KafkaRedis. Primerownership4archivos bus/framing/tests, semántica interna protegida; routing/security/tokenAPI/SQLitebarrier/snapshot/client/OpenAPI/E2E posteriores. No tokenengine navegador ni tokenURL. Client debe descartarcursor al cambiarfiltro; serverautoriza scope antesdata sin inventar detección statelessdel filtro a partir de epoch:seq. Archivos actualizados de namespace planificado a app empaquetada. TDDn/a decisión/prosa, no CA cerrado.


## T06 U1: implementación del bus y framing acotados

2026-10-08T21:01:23.869741+00:00: ADR0056O1 adoptada. Ownership4bus/SSEmodule/tests, NO route/auth/token/DBbarrier/snapshots/publiccontract/client. CapturaTDDconductual yWHOLEchangedruntime80ceroexcl; oldqueuebus API/buffer/terminaltests intactos. NoCAclosed ni fullT06/M1.


## T05: custodia O2 y protocolo antes del runtime

2026-10-08T21:09:04.107841+00:00: ADR0057adoptahelperstdlibserver4módulosnuevos, sin importbenchmark/enginecommon/torch/depsnuevas. Primeraunidad sólopipe_protocol ytests; grupoWin/Linux despuésconpruebasreales. Rootajusta propuesta68frames a132+take_result64 paraentregasparcialesADR0055, mantienetotal4MiB/frame256KiB. PrimaryWin32 APIs consultadasantescódigo, binding/layout/behaviornativoUNTESTED. Jobherenciahandleswhitelist/compareobjecthandle escrow; Linuxsubreaper+liveness noPIDkills. NadaCPU2/cleanup/liberado sólo por decoder. TDDn/a decisión/prosa, fullT05abierta.


## T05: implementación del protocolo privado puro

2026-10-08T21:09:04.714239+00:00: ADR0057 O2 seleccionada, primerunit2archivos encode/decode/sessionbudget JSON estricto. No procesos/custodia/DB/CPU2/nativeclaims. Per-takeresult64+132frames4MiB mantiene parcialidadADR0055. TDDcausal ywhole80ceroexcl; contratos3accepted readonly, schema JSON congeladaweb.


## Revisión de dos lentes — intento 1: bus SSE T06 U1

2026-10-08T21:33:00.016405+00:00: A/B/C/DCLI0;0Critical1Important0Minor. A01rootconfirmado: entity.updated pierdetype/id documentados yusaentity_type/revision sinADR. Corregiradaptador/testnuevo2files, no cambiarcontrato. B/C/Dnogaps nuevos. OldEventConsumerAST intacta, baseline428PASS/WHOLE96,06/97,13noaceptación. Scope4/0; preflightroot sourceSHA-list/map falló ylanesnoarrancaron, corrección verificada antesdispatchactual. [Revisión](testing/t06/sse-bus-unit1-review1.md). T06enprogreso, próximo review2+QA.


## T06 U1: fix causal de forma pública entity.updated

2026-10-08T21:34:00.149993+00:00: Review1A/B/C/Dterminal: A01Important confirmadofieldtype/id descartados vsconvenciones34. Freshfix2files adaptor/newtest sólo, sin cambiar docscontrato ni buffer interno/EventConsumer. REDactual expectedtype/id beforefix, baselinebroadsame428+regression, review2+QA next.


## T06: aislamiento del timeout scheduler801 sin cambiar tests

2026-10-08T21:42:30.492653+00:00: FixA01targeted28green pero baseline452PASS1FAIL timeout Event10s nodeglobalbusyGPUnegativeCPU801. Autoriza debugrootcause fases1–3readonly: reproducciónnodeexact+datoscausales, sin extenderplazo/weakening ni arreglosajenos. No atribuir carga/flakiness sin prueba, no whole rerun porimpaciencia.


## Revisión de dos lentes — intento 1: protocolo privado CPU T05

2026-10-08T21:43:37.355595+00:00: A/B/C/DCLI0nogaps, scope2/0/current2fuentesexactas. B228fragmentationfronterasinmemory reales; sin reruns de110baseline. Producerwhole238de24099,16667%0excl. Csuplementaria JSONtrustbound,Dautoworker. QAindependiente siguiente; sinpipes/custodia/slots/SQL/FS/fullT05. [Revisión](testing/t05/pipe-protocol-unit1-review1.md). TDDn/a adjudicación.


## T05 protocolo puro: QA independiente tras review1

2026-10-08T21:43:37.963980+00:00: A/B/C/Dreview1limpia, 110caseproducer99,1667%whole. FreshreadonlyQA current110 yrawsingletrace/bytesbudgets; no pipelines nativas/model/media/SQL/CPU2/FSclaims. Rootsoleacceptance.


## Revisión de dos lentes — intento 2: entradas web actuales T08

2026-10-08T21:45:38.672280+00:00: A/B/C0gaps CLI0; Source4currentexact,scope3/0. B1-01INVALID_LOCKCLI2/ROOT1-02historiafixtures/fallo586nameonly corregidoscon66PASS actualfísico586 y23missing. Wholefetch93,6963/webinputs90,9091ceroexclusiones. ROOTproxy de324originales noentregaimplementer; actualCLI0fix2 solamente, oldCLI96670UNKNOWN ylímitesREDcopiasprevias preservados. [Review2](testing/t08/stable-inputs-review2.md). QA independiente siguiente; T08full/WindowsSWC/DockerE2E/M1abiertos.


## T08: QA independiente entradas actuales tras review2

2026-10-08T21:45:39.295854+00:00: A/B/C review2 limpia, ROOTproxy qualifiersCLIoldUNKNOWN preserved. FreshreadonlyQA66cases real58623missing/609archives901pnpm+whole2 >=80zeroexcl. Fuenteappsweb/contractsJSON congelarcurrentdurantesuite sinmodelschemachanges; no WindowsSWC/Compose/E2E/fullT08 por esto.


## T05: protocolo JSON puro aceptado tras QA independiente

2026-10-08T21:47:26.685365+00:00: review1A/B/C/D0gaps+QA110PASS/whole238de24099,16667%0excl. Root57originales/35inputsactuales cotejados,2owned accepted. Cota262148lógica noRSS; epochnonauth/stopcontextnoOSproof. Custodianativa/slots/SQL/publicación/DB/workerfull pendientes. [Aceptación](testing/t05/pipe-protocol-unit1-qa1-root-acceptance.json). TDDn/a adjudicaciónQA.


## T06: diagnóstico parcial del timeout scheduler801

2026-10-08T21:51:26.885832+00:00: baselineA01fix453cases452PASS1FAIL Event10s protegida. Diagnóstico3runs: originalnodePASS2,556s; fullprofilerFAIL13,383sperturba; coverage+lightobserverPASS12,285s/submit9,96565deadlineStart. Sin causaloriginalprobada, entityupdatedbranchnoejecutada;213protectedexact. No timeoutextend/weakening/códigoajeno ni atribucióncarga/flaky. Rootnext causalbarato/refinamientohypothesis acotado; Review2+QA/fullT06pending. Objetivoactivo, no pause.


## T05: primera implementación de custodia Windows real

2026-10-08T21:53:44.115358+00:00: ADR0057O2/contratos+protoaccepted.4newfiles fachada/custodiaWin/test/fixture, birth suspendidoassign-before-resume/killonclose/deadline/foreignwitness/pipefinish. Linuxsupervisor unidad siguiente no placeholderaccepted. NativeWindowsWHOLEcada módulo≥80zeroexcl conchildren tracer actualsame-run; NO CPU2/DB/FS/bodyaudio scope.


## T06: prueba de una variable para deadline801

2026-10-08T21:55:28.979390+00:00: Diagnóstico1parcial2hypothesespreservado; caso originalPASS2,556s ecoverage+observer9,96565scerca10s no causaloriginal. Ahora pairedoriginal801 mismoSRI/config/fixtures, única variable cobertura de2fuentes exacta a final453, no nuevoobserver/profiler. Sinfix/timeoutextend/testweakening, no whole rerun hasta evidencia.


## Entrega técnica pipe-protocol-unit1-qa1 para revisión independiente

2026-10-08T21:56:08.288677+00:00: QAprotocolo puro accepted110PASS/99,16667%whole0excl; root57originales35inputs actuales verificados. Sólo transporte JSON no OS/pipes/slots/SQL/publicación/fullT05.



## T06: diagnóstico parcial y despacho de revisión 2

2026-10-08T22:04:24.149495+00:00: pareja controlada del nodo801 PASS3,251s sin cobertura y PASS6,077s con cobertura; causa del timeout original UNKNOWN. Se conservan 452PASS/1FAIL y deadline10. Paquete raíz actual de cuatro fuentes para revisión2/3, nunca aceptación por CLI0. QA independiente posterior conserva la verificación completa. No cambios de producto/test en el diagnóstico. Objetivo activo M0–M5.


## Entrega técnica coverage-deadline-comparison1 para revisión independiente

2026-10-08T22:04:41.443713+00:00: Diagnóstico readonly: pareja original801 sin/cobertura pasa; coste asociado instrumentación observado, causa timeout original UNKNOWN. Sin cambio de deadline/test/producto ni aceptación de T06.



## T06: Revisión de dos lentes — intento 2

2026-10-08T22:11:18.133996+00:00: A/B/C/D frescas CLI0, scope0, 0Critical/0Important/0Minor. A01 corregido, cuatro fuentes exactas; [informe](testing/t06/sse-bus-review2.md). Cobertura WHOLE de la suite453 fallida sólo medición; timeout801 UNKNOWN. QA independiente actual pendiente, no cierre T06/M1.


## T06: QA independiente después de revisión2

2026-10-08T22:11:31.037918+00:00: Bus+adaptador puro; root exige A/B/C/D revisión2 fusionada sin pendientes antes de dispatch. Actual baseline453 original intacta, deadline10 sin cambios, WHOLEevents+sse current80zeroexcl; ningún cierre por CLI0. QA única actual independiente sin edición de fuente/tests, no snapshot/auth/API/E2E/fullT06.


## T06: aceptación técnica del bus y framing tras QA independiente

2026-10-08T22:18:50.352577+00:00: revisión2A/B/C/D limpia y QA única actual453PASS/0FAIL/0SKIP exit0; WHOLEevents195/20396,0591% y sse202/20897,11538%, cero exclusiones. Root cotejó 2184 originales y 90 copias de entrada; cuatro fuentes actuales y 15 tests/helpers seleccionados exactos. Cambios archivales disjuntos de custodia documentados. Baseline anterior452PASS1FAIL permanece fallida, causaUNKNOWN sin flake/plazo cambiado. [Aceptación](testing/t06/sse-bus-qa1-acceptance.json). T06/M1 siguen abiertos por endpoint/snapshot/auth/cliente/E2E.


## Entrega técnica sse-bus-qa1 para revisión independiente

2026-10-08T22:19:25.555180+00:00: QA independiente del componente aceptada por root:453PASS, cada módulo WHOLE>=96%zeroexcl, originales y fuentes cotejados. HTTP/snapshot/auth/cliente/E2E y T06 completo abiertos; timeout original UNKNOWN permanece registrado.



## T06: diseño de contrato HTTP y sesión local posterior al bus

2026-10-08T22:20:30.216857+00:00: U1bus/framing accepted453PASS, review2A/B/C/D0. Fresharchitect genericCLI readonly ownership[], diseña obligatoria sesión pública dedicada/API+snapshotwriterhandoff ADR0056 sin tocarpackagesJSON duranteQAweb. Rootelige/revisapropuesta antes código. No cambio producto/endpoint/auth/E2E/CPU2 acreditado.


## Entrega técnica native-windows-custody-unit1 para revisión independiente

2026-10-08T22:25:05.296486+00:00: Entrega actual final04:31PASS, WHOLEcustody87,9227%/windows91,4365%zeroexcl singlecurrentUUID/two traces. Fuentes e inventario cotejados antes review1. Custodia kernel y transporte benigno nativos; SQL/CPU2/audio/FS/Linux/integración y T05 no aceptados. ReviewA/B/C/D y QA independientes pendientes.



## T05 custodia Windows: Revisión de dos lentes — intento 1

2026-10-08T22:31:39.819415+00:00: A/B/C/D frescas CLI0/scope0; 0Critical/3Important/0Minor. B01finalizador sin done/recibo, B02race done→join0, B03handle perdido antesregistro confirmados. [Informe](testing/t05/native-windows-custody-review1.md). T05 en-progreso; freshfix1 con TDD y31nativebaseline antesreview2/QA.


## T05 custodia Windows: corrección1 posterior a revisión1

2026-10-08T22:32:57.145488+00:00: Revisión1A/B/C/D0Critical3Important0Minor fusionada, B01B02B03 confirmados. Freshfix3files sólo finalizadorfinito/racewait/retenciónOpenProcess; old31nativecases/fixture byte-semánticas conservadas. Actualnativepositive vs inyección fault separados; causalREDbeforefix, singlecurrenteachWHOLE80zeroexcl, review2/QAposteriores. Ningún fullT05/CPU2/SQL/audio/FS/Linuxclaim.


## T08: aceptación de entradas actuales tras QA independiente

2026-10-08T22:36:33.400390+00:00: review2A/B/C limpia y66PASS/0FAIL/0SKIP, exit0; WHOLEfetch93,6963%/webinputs90,9091%, zeroexcl singlecurrenttrace. Root1622 originales/1573frozeninputs/1562context/10contracts/physical586-vs609 cotejados. PostCSS8.5.23retain/8.5.29omit, 23faltan real. JSONfreeze liberada tras terminalCLI0 (no duranteobservación), actualpid1064 waited/observerjoined/workspaces0; nestedchildrenUNKNOWN. OldCLI96670UNKNOWN preservado. [Aceptación](testing/t08/stable-inputs-qa1-acceptance.json). WindowsSWC/Docker/E2E/fullT08 siguen pendientes.


## Entrega técnica stable-inputs-qa1 para revisión independiente

2026-10-08T22:36:33.492108+00:00: QA independiente aceptada por root:66PASS, wholeeach90,9–93,7%zeroexcl, 1573inputs yphysical586 vs609 actual. JSONfreeze liberada despuésCLIterminal yfuentescotejadas. WindowsSWC/Docker/E2E yT08/M1 completos pendientes.



## T05 U2b1: migración0006 e historial durable

2026-10-08T22:37:43.957725+00:00: ADR0055; contratosU2a1accepted readonly. Nueve archivos acotados SQL/models/snapshots/schema+tests, old expectedhead/tableextension assertions updated exactly perrootdecision, no weakening/historical rewrite. Dispatch requires currentwebQA terminal and no SSE baseline concurrently changinghead. Wholeeachmodule80zeroexcl, realSQLite/TDD, no runtime/publicaciónfilesystem/CPU2 claim.


## T06: decisión de sesión local y siguiente unidad pura

2026-10-08T22:39:09.617289+00:00: root adoptaA conformeADR0058 tras29observaciones/copies exactas y46 originales cotejados. Custodia previa a primera lectura no demostrada, errores de helpers retenidos. Registro/DTOs nuevos primero, sin HTTP/CORS/SQL/main niJSON. Bootstrap automático sinloginUI/tokenengine/URL, contrato ybrowser tests posteriores. No cierreT06.


## T06: implementación del registro local y DTOs de snapshot

2026-10-08T22:40:56.840238+00:00: ADR0058A adoptada porroot, primeraunidad pura4newfiles, registro32/8h/ownerinterno/randomness+DTOs closed/null/bounds. Ningún HTTP/CORS/main/SQL/JSON/cliente, APIcontractstage posterior. FreshTDD/cadawhole80zeroexcl/reviewseguridad yQAindependiente. Nativefix3 ySQL0006/model/snapshot disjuntos; sólo mapcausalpropio no freezeappglobal.


## Entrega técnica native-windows-custody-fix1 para revisión independiente

2026-10-08T22:47:23.061708+00:00: Corrección1 entregada:36PASS, original31AST intacta+5regresiones, WHOLEcustody90,0943%/windows92,1875%0excl actualsingleUUID. B01/B02/B03 producerclaimsfix; review2 yQA actuales obligatorias, ningún cierreT05/M1.

RED: `test_fix1_repeated_containment_failure_has_finite_unknown_receipt[containment]` falló por done ausente tras **dos** intentos de contención comprobados · 2026-10-08. `red-b01-strengthened`, exit1. La variante disposition también falló por done ausente después de RuntimeError real controlado; GREEN2 en `green-b01-strengthened`. `red-b01` inicial queda preservado; se reforzó causalmente la fixture y se reexpuso únicamente custody.py original owned a la prueba, luego se restauró la propuesta propia. No source histórica se presentó como actual: cada comando guarda su SHA real.

RED: `test_fix1_done_barrier_waits_actual_thread_exit_without_spurious_timeout` falló con TimeoutError de join(0) sobre un hilo real después de done · 2026-10-08. `red-b02` exit1 → `green-b02` PASS.

RED: `test_fix1_actual_openprocess_retained_before_identity_fault[get_times/mismatch_close]` falló con grupo sin referencia al OpenProcess real · 2026-10-08. `red-b03` exit1/2FAIL → `green-b03`2PASS. Cleanup RED usó exclusivamente Guard/anclaje kernel del objeto capturado. Witness sobrevivió ambos comportamientos; `injection.json` etiqueta expresamente la inyección finita, NO fallo espontáneo de WinAPI.



## Entrega técnica local-session-dtos-unit1 para revisión independiente

2026-10-08T22:56:09.197735+00:00: Entrega pura4newfiles:125PASS, WHOLEdto98,7342%/registry99,3902%zeroexcl freshsingletrace. Thread32capacity/40barrier/worstframe21597bytes probados, noHTTP/SQL/authtransport/browser/fullT06. Incidentesbootstrap/cachecompartida preservados/lastmutationsUNKNOWN sin borrarcache. Review1A/B/C yQApendientes.

RED: `apps/server/tests/test_local_sessions.py::test_real_defaults_and_fixed_owner` · exit1 · 2026-10-08T22:43:45.091637+00:00 · originales `red-registry-causal/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_private_extra_fields_rejected[engine_token]` · exit1 · 2026-10-08T22:43:47.141740+00:00 · originales `red-dto-privacy-causal/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_strict_job_bounds[progress-True]` · exit1 · 2026-10-08T22:43:49.142692+00:00 · originales `red-dto-finite-causal/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_controls_frame_phase_and_wire_commit[end]` · exit1 · 2026-10-08T22:43:51.143404+00:00 · originales `red-frame-causal/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_credential_exact_schema` · exit1 · 2026-10-08T22:44:00.166139+00:00 · originales `red-credential/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_control_data_bounds[begin-active_count-1001]` · exit1 · 2026-10-08T22:44:02.200866+00:00 · originales `red-control-shape/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_control_data_bounds[end-cursor-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:2]` · exit1 · 2026-10-08T22:44:04.215403+00:00 · originales `red-control-cursor/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_control_envelope_bounds[id-True]` · exit1 · 2026-10-08T22:44:06.230864+00:00 · originales `red-envelope/stdout.txt` y JUnit.

RED: `apps/server/tests/test_event_dtos.py::test_control_closed_discriminator_and_schema` · exit1 · 2026-10-08T22:44:08.235244+00:00 · originales `red-discriminator/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_expiry_idle_deadline_and_no_sliding` · exit1 · 2026-10-08T22:45:26.480213+00:00 · originales `red-expiry/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_absolute_expiry_and_purge_without_eviction` · exit1 · 2026-10-08T22:45:28.518538+00:00 · originales `red-capacity/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_revoke_close_restart_and_foreign_binding` · exit1 · 2026-10-08T22:45:30.545386+00:00 · originales `red-binding/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_duplicate_rng_finite_no_overwrite` · exit1 · 2026-10-08T22:45:32.596501+00:00 · originales `red-collision/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_invalid_clock[True]` · exit1 · 2026-10-08T22:45:34.665601+00:00 · originales `red-clock/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_invalid_controls[controls0]` · exit1 · 2026-10-08T22:45:36.731672+00:00 · originales `red-controls/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_constant_time_bounded_scan` · exit1 · 2026-10-08T22:45:38.784763+00:00 · originales `red-scan/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_thread_capacity_and_revoke_race` · exit1 · 2026-10-08T22:45:40.863278+00:00 · originales `red-threads/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_wrong_owner_cannot_issue` · exit1 · 2026-10-08T22:46:01.673581+00:00 · originales `red-owner-causal/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_revocation_invalidates_and_is_idempotent` · exit1 · 2026-10-08T22:46:03.692263+00:00 · originales `red-revoke/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_close_invalidates_all` · exit1 · 2026-10-08T22:46:05.717552+00:00 · originales `red-close/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_rng_retry_and_private_exception` · exit1 · 2026-10-08T22:46:07.795456+00:00 · originales `red-rng-private/stdout.txt` y JUnit.

RED: `apps/server/tests/test_local_sessions.py::test_invalid_clock` · exit1 · 2026-10-08T22:47:39.763499+00:00 · originales `red-huge-clock-causal/stdout.txt` y JUnit.



## T05 custodia Windows: Revisión de dos lentes — intento 2

2026-10-08T22:58:44.683276+00:00: A/B/C/Dfresh CLI0/scope0, 0Critical/Important/Minor. B01B02B03 corregidos segúnfuente/RED/36casos nativos yregresiones; tres fuentes+fixture exactas. [Informe](testing/t05/native-windows-custody-review2.md). QA independiente36actual yWHOLEcada módulo pendiente, T05 sigue en-progreso.


## T05: QA nativa independiente después de revisión2

2026-10-08T22:59:04.836366+00:00: Gateantesdispatch exige review2A/B/C/D0pending ycurrent3+fixture SHAexact. Windowskernel/stdio/trustedfixture sólo, nuevaúnicabaseline36casos conWHOLEcada runtime>=80zeroexcl yactualtrace2sameUUID. Inyecciones etiquetadas, no CPU2/audio/SQL/Linux/fullT05claim. SQL/puresession disjuntas nofreezeglobal.


## T05: aceptación técnica de custodia Windows actual

2026-10-08T23:05:54.101605+00:00: revisión2A/B/C/D limpia y QA independiente36PASS/0FAIL/0SKIP exit0; WHOLEcustody90,0943%/windows92,1875%0excl, dos trazas actualUUID sin unioneshistóricas. Root1642 originales/36recibos nativos/4fuentes+guards exactos cotejados. DirectPopen/nativepytest/nativeparent distinguidos; parentterminationexit1 intencional noFAILpytest. B01B02B03 cerrados conregresión actual; unknown retiene refs noCPU2claim. Ruffunit cuatroactuales proyecto/defaultisolated exit0, nogloballintclaim. [Aceptación](testing/t05/native-windows-custody-qa1-acceptance.json). Linux/audio/FFmpeg/SQL/FS/CPU2/E2E yfullT05 pendientes.


## Entrega técnica native-windows-custody-qa1 para revisión independiente

2026-10-08T23:05:54.203338+00:00: QA nativa36actual aprobada técnicamente porroot, cadaWHOLE90/92zeroexcl, originalrecords/same-runtrace/sourceguards verificados. UNKNOWNrefsretained y parentexit1 esperado distinguidos dePytestexit0. Linux/audio/CPU2/SQL/FS/E2E/fullT05 pendientes.



## T06 registro/DTOs: Revisión de dos lentes — intento 1

2026-10-08T23:07:12.058942+00:00: A/B/Cfresh CLI0/scope0,0Critical/Important/Minor; DautoFalse. Current4source exact,125producerPASS yWHOLE98/99zeroexcl, incidenciaruffcachepreservada no fakeglobalfreeze. [Informe](testing/t06/local-session-dtos-review1.md). QA125 independiente pendiente; HTTP/CORS/UserDB/SQL/feed/browser/E2E/fullT06 quedan abiertos.


## T06: QA independiente del registro y DTOs

2026-10-08T23:07:12.418387+00:00: Preconditionreview1A/B/C cleanrootadjudication antesdispatch;125currentnewtests, eachWHOLE80zeroexcl singletrace. Registry/DTOs sólo; noHTTP/auth/CORS/SQL/feed/builder/E2E/fullT06. Privatesource/config/runner copies	beforePopen ysourceguards precisos, no appglobal/native/SQLdrift claims.


## T05: backend Linux y supervisor de grupo CPU

2026-10-08T23:12:54.848657+00:00: Windowscoreaccepted36native/review2A/B/C/D+QA90/92wholezeroexcl. ADR0057Linuxsupervisor outsideworkgroup/subreaper/pipe liveness; newLinuxbackend2+fixture/test yfacadaowned para scope/backendintegration. DockerCPU imagefijo nonroot/nored/nogpu/newdeps0. CausalnativeTDD antescode/wholecada runtime80zeroexcl SINGLEdeclareddualOS sourceUUID (Win36 actual+Linuxnew) sin unionhistórica. FullCPU2/audio/SQL/publicación aún posteriores.


## T06: aceptación técnica del registro local y DTOs

2026-10-08T23:15:58.725672+00:00: review1A/B/C0gaps yQA independiente125PASS/0FAIL/0ERROR/0SKIP exit0; WHOLEdto98,7342%/registry99,3902%, zeroexcl/currentonly. Root2142 originales/current4+guards/AST/runcmdUTC/PIDs/traza/frame21597bytes cotejados. Threadsdepruebasjoined, descendantsOSUNKNOWN; parentfinalizerUNKNOWNno0inventado. Owner DB/authHTTP/CORS/API/WAL/feed/builder/browser/E2E no acreditados. [Aceptación](testing/t06/local-session-dtos-qa1-acceptance.json). T06/M1 continúan abiertos.


## Entrega técnica local-session-dtos-qa1 para revisión independiente

2026-10-08T23:15:58.805104+00:00: QA independiente125actual aceptada técnicamente porroot, WHOLEcada98/99zeroexcl, actualargvUTC/PIDs/sourcehash/AST/frame21597 comprobados. Pure registry/DTOs sólo, realUserDB/HTTP/CORS/SQL/feed/builder/browser/fullT06 abiertos. Sharedcache/firstread/parentfinalizerUNKNOWN preservados.



## Entrega técnica durable-sql-unit2b1 para revisión independiente

2026-10-08T23:18:43.905272+00:00: EntregaNEEDS_CONTEXT sinaceptación:51ownPASS pero1029baseline804PASS8FAIL214ERROR3SKIP exit1. Root220HEADexpectationsold+1harnessinitEnv+1timeout801UNKNOWN identificado. Runtime4WHOLE92–100zeroexcl sólo mediciónfallida. Scope12resume1 exact4headactual updates autorizado, no timerbypass/historyrewrite/fullT05.

RED: test_sql_cas_stale_illegal_and_immutable falló con AssertionError: assert 1 == 2

RED: test_committed_requires_exact_assets falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:56:37.979396+00:00 · red-committed-assets/junit-original.xml

RED: test_cpu_rejects_engine_lane_sql falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:42:00.413823+00:00 · red-cpu-authority/junit-original.xml

RED: test_cpu_unknown_custody_cannot_finish_or_resume falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:24.554414+00:00 · red-custody-state/junit-original.xml

RED: test_orm_plan_rechecks_real_winner_terminal_digest falló con Failed: DID NOT RAISE any of (ValueError, StatementError, IntegrityError) · 2026-10-08T22:59:40.663824+00:00 · red-orm-winner-sha/junit-original.xml

RED: test_sql_outcome_is_closed_and_finite falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:54:29.427864+00:00 · red-outcome/junit-original.xml

RED: test_prepared_package_sql_rejects_contradictions[foreign_seed] falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:30.247454+00:00 · red-package-authority/junit-original.xml

RED: test_cpu_orm_contract_invalid[digest] falló con Failed: DID NOT RAISE any of (ValueError, StatementError, IntegrityError) · 2026-10-08T22:42:15.911575+00:00 · red-plan-digest/junit-original.xml

RED: test_ready_assets_history_and_terminal_outcome_are_preserved falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:56:41.008635+00:00 · red-ready-immutable/junit-original.xml

RED: test_legacy_ready_take_cannot_acquire_new_intent falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:27.463579+00:00 · red-ready-preservation/junit-original.xml

RED: test_revision_crossrow_fraud_sql[output_index-1] falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:42:13.098288+00:00 · red-revision-authority/junit-original.xml

RED: test_snapshot_causal_closure_private_roundtrip falló con AssertionError: assert [] == ['01K70000000000000000000006']

RED: test_portable_row_drops_operational_identity falló con AssertionError: assert {'cleanup_sta...shed_at', ...} == {'contract_ve...handler', ...}



## T05 SQL: contexto necesario resuelto y único re-despacho1

2026-10-08T23:19:19.682100+00:00: Rootcotejóoriginales1029baselinefallida y220asserts/setup HEAD0005 obsoletos+1harnessinit_env+1timeout801UNKNOWN. Sólo4literalesHEAD0005→0006 en3nuevosownedtests; no downgrade/historicalDDL cambio ni performanceweaken. Original9+3=12owned ycurrentcov>=92 sóloMEDICIÓNsuitefallida. Redispatch1único, harnesssourcebeforefix/freshbaseline32files1029 conwhole4runtime80zeroexcl; review+QA después, no aceptaciónactual.


## T05: diagnóstico causal del único fallo restante de SQL

2026-10-08T23:32:35.539042+00:00: SQLresume1 fresh1029=1025PASS1FAIL3SKIP, sólo original80110s, HEAD yprivateharness resueltos. Readonlydebug-root-cause1–3 current4coveragefactor ycoarsecost hypothesesMAX2, no casoexclusion/timeoutextend/flake/barefullrerun. HistoriasSSEdiag1/2 preserved noreset. NoQueue/ORM/product changes niQAacceptance.


## Entrega técnica durable-sql-unit2b1-resume1 para revisión independiente

2026-10-08T23:32:48.110437+00:00: Resume1actual1029=1025PASS1FAIL3SKIP, HEAD4 yprivateinitEnv reparados, actual80110s timeoutUNKNOWN único restante. Source9prod exactsinsemantics+4literalHEAD cambios3tests cualificados, WHOLE4>=92zeroexcl MEDICIÓNbaselinefallida. Rootdiagnóstico actual iniciado; ninguna aceptación/waiver/flakelabel/timeoutchange.



## Entrega técnica native-linux-custody-unit1 para revisión independiente

2026-10-08T23:42:33.539094+00:00: CurrentFINAL06 Linux23+Windows36=59PASS/0SKIP; WHOLEcustody90,4977/Linux90,1709/supervisor85,6436%zeroexcl samecurrentUUID. Root7733originals/5owned+8contextSHA/21exactownCIDgoneverified. FourcausalRED+injection/birthmetadata limits retained. Review1A/B/C/D yfreshDualQA beforeaccept; noCPU2/audio/SQL/FS/fullT05.



## T05 Linux: Revisión de dos lentes — intento 1

2026-10-08T23:50:14.565978+00:00: A/C/D sin gaps; B acredita dos Important (EMFILE posterior a Popen, journal ENOSPC/EIO sin finally de contención). [Informe](testing/t05/native-linux-custody-review1.md). Corrección nativa autorizada, revisión2/QA pendientes, T05 en-progreso.


## T05 Linux: corrección de revisión 1

2026-10-08T23:50:19.431088+00:00: Fresh implementer para B-01/B-02 Important; cuatro fuentes propias, fachada/Windows/protocolo/contratos protegidos. Regresiones Linux reales antes del fix, dual OS actual y cobertura WHOLE individual sin mezclar trazas históricas. Revisión 2 y QA independiente pendientes. T05 abierto.


## Entrega técnica current-801-latency-diagnosis1 para revisión independiente

2026-10-08T23:53:23.464548+00:00: Diagnóstico parcial readonly: pareja actual nocovPASS2,725s/covFAIL12,384s; factor temporal observado, coste CPUsubmit y causa baseline UNKNOWN. Dos imports capturados sólo POST, límite conservado. Historia intacta, sinfix/waiver/QA; rootautoriza una medición agregada nueva con captura completa previa.



## Entrega técnica native-linux-custody-fix1 para revisión independiente

2026-10-09T00:08:43.376945+00:00: Rootverifica FINAL02 Linux26+Win36=62PASS ceroerrores/skips; WHOLE oficial líneas+ramas88,0546/85,5856/80,18868 cada80+0excl mismoUUID. TresREDrealescontrolados EMFILE/ENOSPC/EIO, sieteCIDs propios gone porinspect; fuentes4+protegidas exactas/originales cotejados. Review2B iniciado A/C/Dpendientes; QAindependiente aúnpendiente. RecursosparcialesUNKNOWN retenidos, metadataindividualtempranaUNKNOWN conservada; noT05/SQL/audio/CPU2/E2E/GPUaceptación.

RED: test_construction_emfile_after_native_popen_contains_tree falló con supervisor/líder/nieto reales vivos después de EMFILE · 2026-10-09; runs/red-b01.

RED: test_journal_fault_after_native_registration_still_reaps[ENOSPC] falló con nieto real vivo tras salida del supervisor · 2026-10-09; runs/red-b02.

RED: test_journal_fault_after_native_registration_still_reaps[EIO] falló con descendientes reales vivos · 2026-10-09; runs/red-b02-eio.



## T05 Linux: Revisión de dos lentes — intento2

2026-10-09T00:29:00.254311+00:00: A/C/D sin nuevosgaps; B01/B02 corregidos y B03Important nuevo(selectorENFILE despuésTERM omiteKILL/waits). [Informe](testing/t05/native-linux-custody-review2.md). FixnativoTDD owned3autorizado, nextreview3/QA sinreset. T05 sigueen-progreso.


## T05 Linux: corrección B03 de revisión2

2026-10-09T00:29:03.947885+00:00: Fresh implementer para OSErrorENFILE al crear selector despuésTERM. REDnativo real controlado antesminimumGREEN; proteger facade/Linuxbackend/Win36/oldLinux26. SIGKILL y waits no dependen de éxito del selectorgracia. FreshdualOS actual/cadaWHOLE80zeroexcl/mismoUUID, revisión3 yQA pendientes; noreset/noT05cierre.


## T05: localizar procedencia observada antes de captura U3

2026-10-09T00:35:38.755045+00:00: Explorer-role freshreadonly específico: mapping campos actualJobAttempt/terminal/catalog vs contratoCapture/manifest, únicamente gaps de observación necesarios para siguienteunidad. Reutiliza diseñosCPU/publicación existentes y0006actual; no repetirdiseño general ni impl/test/native/GPU. Rootelige nextownership con evidencia, sinprovenance inventada.


## Entrega técnica provenance-current-fields-exploration1 para revisión independiente

2026-10-09T00:54:04.056816+00:00: Mapaestático deprocedencia; rootinventario/protectedparent7/copies cotejados. Hashmismatchpropuesto NOdemostrado: digest(str)=UTF8 yJSONsingleline(actualsamehash pureprobe), [adjudicación](testing/t05/provenance-current-fields-root-adjudication.md) corrigeinforme. PublicationIntentRevision esmodeloactual noAssetRevision. Descriptor/Healthpre_sendcaptura yroles nextpending801/decisión; codesLM/DiTactual requierenotraunidad. SinDB/data/generaciónreal/aceptaciónniimpl; limitInicialRead/rawcommandUTCUNKNOWN conservados.



## T05: medición causal agregada del plazo801

2026-10-09T00:57:56.829356+00:00: Readonly una llamada original801 cubierta actual, pre-Popen transitive capture completa y spans agregados. HistoriaH1/H2 y limitacióncapturaPOST conservadas. Ningúnfix/plazo ampliado/caso excluido, SQL/T05 abiertos. Preparaciónroot y ejecucióndespués de terminar medicionespesadas en otrasunidades.


## Entrega técnica native-linux-custody-fix2 para revisión independiente

2026-10-09T01:04:42.845198+00:00: RootcurrentFINAL05 Linux32+Win36=68PASS(26+4selector+2aux), WHOLEoficial88,0546/83,7838/80,7339% each0excl/currentUUID/rawsame source/copies/16ownCIDs gone verificados. Produceraritmética32(26+4)secompleta con2aux notremoved. Historialcov77,7778/79,7546FAIL yfinal04format1 intactos, currentfinal05newSHA/UUID/runsno union. Review3A/B iniciado,C/D/QA pendientes; B03selectorcontención/sourcequery/no-final UNKNOWN no fakefree. SinT05/audio/CPU2/SQLite/fs/GPU/E2Eaceptación.

RED: test_grace_selector_enfile_after_actual_term_contains_owned_tree[create] fallÃ³ con ambos descendientes reales vivos tras TERM real + ENFILE controlado Â· 2026-10-09; runs/red-b03-create.

RED: variantes register/select/close fallaron por la misma assertion conductual Â· 2026-10-09; runs/red-b03-other. Supervisor original exacto; fuente/test/fixture/runner/toolchain precopiados antes de ejecuciÃ³n, argv/PID/UTC/exits/stdout/stderr/JUnit originales. Rescate pidfd propio sÃ³lo DESPUÃ‰S de assertions; testigo ajeno vivo antes del rescate.



## T05 Linux: Revisión de dos lentes — intento3 limpia

2026-10-09T01:11:02.409442+00:00: A/B/C/D0CriticalImportantMinor; B03correctedmantienehistoria1/2. [Informe](testing/t05/native-linux-custody-review3.md). FreshQA68dualOS/currentWHOLE3configreadyNOTlaunched until801measurementcompleted. T05 sigueen-progreso/noaceptaciónporrevisión.


## T05 Linux: QA independiente tras revisión3 limpia

2026-10-09T01:11:20.078126+00:00: FreshQA owned[] current32Linux+36Windows yWHOLE3oficial>=80zeroexcl/samefreshUUID antesaceptaciónRoot. Source/tests/fixturesreadonly exactos; productorfinal05/reference67RAW no reuse. Docker ownCPU pinnedimage/privatebytecopies/networkGPUoff noinstalls. Reservarhasta801measurementterminal antesfuncionalnative. T05/CPU2/audio/SQL/fs/E2E/GPU pendientes.


## T05 801: medición coarse adjudicada

2026-10-09T01:16:27.940613+00:00: Oneoriginal801coveredPASS/submit7,024s10s, no waiver previousFAIL. JSON70msnohotspotcarodemostrado; queued3,97s necesitaaislarSQL/writer/flushcommit.59missingmanagedBEFOREcapture/hostBlenderCPUlimitconservados. NextONEqueuedspansconfigreadyNOTlauncheduntilownheavyfinish. No productfix/SQLacceptance.


## Entrega técnica current-801-coarse-spans1 para revisión independiente

2026-10-09T01:17:46.133875+00:00: RootoriginalauditONEcovered801PASS9,458s/cpu_submit7,024s10s. ContractJSON70ms/queued3,97sdominantobservedwallnoCPUexclusive/avoidablecauseproof. Capturegap59managedbeforefilesmaterialconservado, Blender19CPUwindow noexactattribution. NoSQLwaiver/coveragegate/codefix; NEXTonequeuedquerywriterflushspansconfigpreparedNOTlaunch untilQA68/FC01nativefinish. Currenthead0006/globalpriority/FIFO/cachednegative/CPU2/snapshotauthority unchanged.



## T05: QA1 nativa fallida — diagnóstico causal autorizado

2026-10-09T01:24:42.686724+00:00: 67PASS1FAIL truncatedUNKNOWNexpectedvsCLOSEDobserved; ordenwire/cancelnoobservado causeUNKNOWN. OwnCIDgone/sourceinputs exact/noacceptance. Protectedcontractsformat1 preservedoutsidecorenativecurrent scope. DebugMAX2hypotheses realnativeordering/TDDbeforeminimaldrainfix owned3; old68+new/rawcurrentfreshwhole80zeroexcl/newreviewQA2required. No flaky/waiver/timerweakening.


## T05 Linux: debug causal de QA1 fallida

2026-10-09T01:25:19.290460+00:00: Freshdebug/TDD Ownerdrain trasQA67PASS1FAIL exacttruncated wronglyCLOSED. CauseUNKNOWN, MAX2hypotheses nativecontrolledordering beforefix, no flaky/plazo/assertweakening. Ownedfacade+LinuxWin tests3, backends/supervisor/fixtures/contractsreadonly. Existing68+newdualOS/currentWHOLE3each80zeroexcl/rawsameUUID freshreviewafterfix, QA2pending. Rootacceptancefalse.


## Entrega técnica native-linux-custody-qa1 para revisión independiente

2026-10-09T01:25:29.249471+00:00: FAILED independentQA67PASS1FAIL exacttruncatedUNKNOWNvsCLOSED; currentWHOLE3each80+0excl/67RAW source/copies/ownCIDgone noacceptance. Sourcecontractsunchanged broadformat1preserveddebtnotnativecorenewdefect. CauseUNKNOWNdrainFalse hypothesis needsnativeordering; rootfreshdebugmax2 causalREDbeforeminimumfix ownedfacadeLinuxWin tests3. No flake/timer/assertweakening/Task05done. QaBootstrapprivatefirstWin27FAIL/Lbeforecreate retained actualcurrentnewUUID only.



## T05: aislar coste801 de queued

2026-10-09T01:33:53.880321+00:00: RootcoarseONEPASS submit7,024s/10; ContractJSON70msnohotspotdemostrado, queued3,97ssinseparar. NOwaiver originalSQLFAIL/causaUNKNOWN. NextONEcall queuedquery/writer/preload/flush/transaction afterownheavyterminal; fullmanagedbeforecaptureincl59missing. Ownership[]nofix/timerweakening.


## T05 drain: diagnóstico1 parcial, sin código

2026-10-09T01:46:28.787688+00:00: Sourceowned3restoredexact/inventoryverified. NativeactualUNKNOWNcancelled, expectedunsafeCLOSEDnotreproduced; causeQA1unknown/prod0/noTDDGREEN. NextONEauthority-observationH1continuationconfigpreparedNOTlauncheduntilqueued801finish; no forcedkernelTrue/testtimerweakening. QA67/1failedstatusintact.


## Entrega técnica native-drain-race-debug1 para revisión independiente

2026-10-09T01:47:08.771098+00:00: PartialH1realwirehelduntildrainobserved UNKNOWNcancelled causeunsafeCLOSEDnotreproduced. NOcausalRED/GREEN/prodchange/QAacceptance, original3testsrestoredmatchespreimages+QA1. root-owned-before.json currently{} despitedeclaredowned3, originalmapprovenanceUNKNOWN; rootnewqualificationfromimmutablepreimages/QA1 notretroreceipt. Onefutureauthority-observationH1continuationconfigpreparedNOTlaunched untilqueued801finish. No kernelbooloverride/testtimerweakening/repeatuntilpass. QA67/1remainsfailed.



## T05 801: ejecutar preparación corregida sin aprobación adicional

2026-10-09T01:51:07.707498+00:00: PREPonly prioractor0nativecalls, Rootautorization alreadyONEmeasurement. Freshrunactor completesmonitorboundedlabels/counts thenONEoriginal801 currentcov4/10s withfullbeforecapture incl59. Priorheavynative actorsallterminalverified, no newgate/userquestion; SQL1025PASS1FAIL3SKIPno waiver, prod/testsreadonly.


## Entrega técnica current-801-queued-spans1-preparation para revisión independiente

2026-10-09T01:51:17.622214+00:00: PREPARATION_ONLY0Python0pytestcalls/sourcecopy5590files215MB including59priorgaps; observerboundedthreadsnotcomplete andno performance result. RootpriorlaunchalreadyONEexecutionauthorized, interpretedprep-only notmissinguserpermission; explicitRootgate recorded run1launched actualonceafterbounds/fullnewcapture. SQL1025PASS1FAIL3SKIPnotwaived/no codefix/QAacceptance.



## T05 801: medición queued ejecutada y adjudicada

2026-10-09T02:14:21.264105+00:00: ONEoriginal801PASS11,826s/submit9,3986s10s, materializationreader2,0977/writer2,8725dominantwall; nooldfailurewaiver/causeUNKNOWN. Endmanagedloadedgaps0/prior59missing0 buttransientunloadedclosureUNPROVENexplicitlimit. Arquitecto acotado static equivalence typed17fieldreaderprojection needed beforeoptimization; configready no codechange/nativeprobe.


## T05: completar diagnóstico drain sin parche ciego

2026-10-09T02:15:05.802342+00:00: H1 nativeUNKNOWN(cancelled), stateassertpassed/reasonfailed NOTrequiredunsafeCLOSEDRED; restoredowned3exact/prod0. Oneboundedcontinuation observegroup.terminate realreturn/errors/refs/controltimeline; no kernelbool override/oldtestweakening/newfix. Despuésqueued801finished only. QA67/1stillFAIL.


## T04: comprobar evitabilidad de hidratación del reader

2026-10-09T02:15:15.970474+00:00: Staticarchitecture-only mapping: current801observedORMmaterialization2,10+2,87s, firstsnapshotreader usesonly17canonicalfields thenexpungesJob. Prove/reject typedCoreprojection withsameWAL/currentwriterORMrevalidation/orderfilters/validation. No change/perf/waiver/queuefix authorized; Rootselectafterconcreteevidence.


## T04: decisión sobre proyección del lector

2026-10-09T02:21:19.899220+00:00: Dictamen estático e inventario verificados. EXACT17 rechazado por conversión telemetry e identity map. Variante conservadora autorizada: todas las columnas tipadas, fallback ORM para lector con estado, writer/WAL/filtros/cursor intactos. Sin mejora temporal demostrada ni aceptación de SQL. No contradice un contrato documentado: optimización interna preservando comportamiento.


## T04: implementación del lector sin entidades innecesarias

2026-10-09T02:21:24.612671+00:00: Root rechaza EXACT17 porque omitiría conversiones de telemetry. Autoriza proyección tipada de TODAS las columnas Job para lector limpio y fallback ORM para mapa/estado existente, manteniendo filtros/WAL/cursor/autoridad writer. TDD real; mejora temporal aún no medida; SQL 1025/1/3 permanece fallida.


## Entrega técnica current-801-queued-spans1-run1 para revisión independiente

2026-10-09T02:21:43.791264+00:00: Una ejecución original801 pasó con envío CPU a 9,3986 s y plazo intacto de 10 s; causa del fallo previo desconocida. Inventario de cierre sin huecos, módulos transitorios descargados no acreditados. No aceptación, waiver ni mejora temporal probada.



## Entrega técnica snapshot-row-projection-design1 para revisión independiente

2026-10-09T02:23:39.298602+00:00: Análisis estático auditado: EXACT17 no acredita equivalencia por telemetry e identity map. Root eligió todas las columnas tipadas y fallback ORM con sesión existente; implementación separada en curso. Cero tests ejecutados en diseño, custodia parcial declarada, sin aceptación ni mejora temporal acreditada.



## T05: validar mensajes reales durante cancelación

2026-10-09T02:29:07.823815+00:00: H1 reprodujo CLOSED_CONFIRMED/cancelled con bytes reales truncados durante DRAINING y terminate/close reales True. Observador EBADF posterior no es RED. Root autoriza prueba conductual genuina previa al código y fix mínimo de framing sin efectos tardíos; QA67/1 y causa del terminateFalse antiguo siguen abiertos.


## Entrega técnica native-drain-authority-diagnosis2 para revisión independiente

2026-10-09T02:29:43.023624+00:00: Una observación H1 reproduce cierre inseguro con bytes truncados reales durante drain y autoridades terminate/close True. EBADF posterior del observador no constituye RED; se conservan UNKNOWN previos y QA67/1. Root verificó inventario/fuentes/copia de herramientas/CID propio eliminado y autorizó TDD separado. Sin aceptación ni cambio de producto en diagnóstico.



## T06: contrato y alcance HTTP preparados

2026-10-09T02:41:55.922986+00:00: ADR0058 registro125QA aceptado. Siguienteunidad bootstrap/revoke+CORS y contratosaditivos sólo User readonly, SSE/fullserver abierto. Config lista para slot real, no lanzada todavía; ninguna aceptación HTTP.


## T06: integración HTTP de la sesión pública local

2026-10-09T02:48:18.730818+00:00: Registro/DTOs125QA aceptados y JSONfreeze liberado. Root autoriza ADR0058 bootstrap/revoke+CORS específico+contratos aditivos. Sólo User readonly, ningún job/model/queue. Transporte SSE/barrera/feed/client y fullserver pendientes. TDD/revisión/QA requeridos.


## T05 drain: entrega fallida conserva gate abierto

2026-10-09T02:52:59.913368+00:00: Linux40PASS/1FAIL(backpressure)+Windows46PASS, 19regresiones nuevas, WHOLEfacade87,84%0excl/85RAW actuales. Rootfuentes/JUnit/RAW/inventario/CIDgone revisados. REDoriginalcommandmetadata PARCIAL, no reconstrucción. Diagnóstico BP01 ONEcase preparado, sólo trasQA pesada terminal, sin fixciego ni waiver.


## Entrega técnica native-drain-framing-fix1 para revisión independiente

2026-10-09T02:53:59.431698+00:00: Entrega FALLIDA para integración: 86 PASS/1 FAIL original Linux backpressure. 19 regresiones nuevas pasan y framing de drain se valida sin efectos; WHOLEfacade87,84%0excl/85RAW actuales. Root fuentes/inventario/JUnit/RAW/CIDgone comprobados. Metadata de comandos RED parcial por sobrescritura focalGREEN declarada, no reconstruida. Diagnóstico acotado preparado; ninguna aceptación ni waiver.

RED: test_real_wire_held_until_draining_retains_owner[truncated] falló con CLOSED_CONFIRMED/cancelled y release_gate=True frente a UNKNOWN_QUARANTINED · 2026-10-09. Bytes reales 000000107b retenidos por una lectura física, entregados durante DRAINING. Terminate y close reales True, sin sustituciones de autoridad. Prueba escrita antes de producto; fuente archivada antes del run; JUnit assertion genuina, sin EBADF. Testigo vivo antes de assertion/rescate y waitpid real posterior [9,0]. Focal GREEN Linux2 PASS. Antecedente EBADF diagnóstico no es RED; calendario QA anterior y terminateFalse histórico siguen UNKNOWN.



## T05: investigar backpressure antes de aceptar drain

2026-10-09T02:55:43.205579+00:00: Drainfix86PASS/1FAIL: originalLinux backpressure CLOSED_CONFIRMED, 19newcasespass/WHOLEfacade87,84%/85RAW actuales. Root inventario/source/dualOSJunit/RAW/CIDgone comprobados; NOaceptación. Onebounded originalcase instrumented ONLYafter heavyQAfinished, no timer/assert weak/oldfailure waiver.


## T05 BP01: adjudicación del estímulo de saturación

2026-10-09T03:15:42.182521+00:00: Capacidadreal4 (promptprevio8 era erróneo), plazo venció con3/4 yFull0, no saturación actual. No cambiar policy de cierre válido. Rootautoriza fixtureLinuxcompacta/count20/handshake igual y pruebaFullnatural conplazo/asserts0.25/10 intactos; historia temporalUNKNOWN, ninguna aceptación/waiver.


## T05: acreditar saturación real sin modificar plazos

2026-10-09T03:16:17.845908+00:00: BP01 ONEcase evidencia deadline concola3/4/Full0; Rootcorrige prompt8→capacidadreal4. No es transportmalformed constatado. Autoriza fortalecer fixtureLinux progress compactos/count20/handshake intacto y nueva prueba naturalFull; productor/runtime unchanged, asserts0.25/10 se preservan, no waiver/false prodRED.


## T04 lector: revisión de componente — intento1

2026-10-09T03:33:53.220548+00:00: A/B/C/D0gaps [Informe](testing/t04/snapshot-reader-projection-inspection1-report.md). QAfullSQL32 originales+scanningnuevo/current6WHOLE/original80110 preparada, no aceptación/waiver1025/1/3. El lanzamiento espera fuentesestables yfin de pruebasnativas pesadas.


## T04: revisión lector limpia y QA fullSQL pendiente

2026-10-09T03:34:10.732932+00:00: Readercomponent A/B/C/D limpio,271producer+WHOLE2 válidos. SiguienteQA independiente32ficheros originales SQL con currentHEAD0006 y nuevas pruebas de scanning, original80110s cubierto intacto, cuatro módulosSQL+dosqueue WHOLE actuales. No waiver de1025/1/3 ni speedup. Sólo tras terminar todas las pruebas nativas pesadas.


## Entrega técnica snapshot-reader-projection-unit1 para revisión independiente

2026-10-09T03:34:20.361546+00:00: 271PASS/WHOLEadmission93,33%/resolver89,08%/0excl, 8409copias verificadas y ASTwriter+21funcionesoldtest intactos. RevisiónA/B/C/D limpia, QAfullSQL/original80110s lanzada aparte. Sin mejora temporal medida ni aceptación/waiver1025/1/3. Reportoriginalcodificación mixta preservada; evidencia privada intacta.

RED: apps/server/tests/test_dispatcher_scanning.py::test_clean_snapshot_reader_avoids_job_entities fallÃ³ con lector=[Job.id] frente a []; writer=[Job.id] ya cumplido Â· 2026-10-09T02:22:51.015560+00:00. Originales en red/before, red/stdout.txt, red/stderr.txt, red/birth.json, red/command.json y red/junit.xml. GREEN aislado: 1 PASS. La optimizaciÃ³n solo se escribiÃ³ despuÃ©s de este RED. Los invariantes preservados tuvieron pruebas escritas antes del cambio y 8 PASS previos tras reparar las nuevas fixtures; no se presentan como nuevos RED funcionales.



## Entrega técnica session-http-unit1 para revisión independiente

2026-10-09T03:42:13.104353+00:00: 307PASS/WHOLE5 96,97–100%0excl/currenttrace, Root5735inventory/current8/protected17/JUnit/cov comprobados. PropuestaOpenAPI equivalente JSON, bytes CRLF vsLF distintos cualificados porRoot; export/lint/diff/types actuales verdes. No aceptación: revisiónA/C iniciada, B/D/Nemesis/QA/socketDocker/E2E pendientes, límitesTDD/custodia declarados.

RED: test_issue_validate_revoke falló en emisión real registrada:503 en vez de200 · 2026-10-09. runs/red-issue.

RED: rechazo de body/query/credenciales ajenas y permiso de preflight:503 en vez de422,400 en vez de200; no-store ausente en rechazos existentes · 2026-10-09. runs/red-request-boundary. Los12 casos ya verdes no cuentan como RED.

RED: test_preflight_invalid_syntax:200 en vez de400 para controles y NBSP · 2026-10-09. runs/red-preflight-syntax.

RED: test_bootstrap_before_lifespan_is_unavailable:500 en vez de503 · 2026-10-09. runs/red-unstarted.



## T06 HTTP: auditoría estática cybersecurity preparada

2026-10-09T03:49:36.396791+00:00: Diff8files/transitive15/STRIDE ycopiasRoot before. Ochoespecialistas requeridos enwavesporlímite3+Root/quota, sólolectura SAST; noDAST/toolinstalls/CVEonlineclaim. Código/testcontratos congeladosporSQLQA39120. No auditoría aceptada ni score todavía.


## T06 HTTP: revisión de componente — intento1

2026-10-09T03:52:15.471432+00:00: A/C/D0gaps, BMinorB-01DELETEprelifespan500sinno-store. [Informe](testing/t06/session-http-inspection1-report.md). Fix2files preparado trasSQLQA39120freeze, aúnNOlanzado. Fuente actual8 siguebaseline deauditoría SAST; ningún cierre.


## T04 fullSQL QA1: fallo material del arnés y nueva ejecución condicionada

2026-10-09T03:55:26.357197+00:00: 1051PASS/1FAIL privateiniomitido/3SKIP, original801PASS8,574s10intacto. Rootinventario/8397copies/current6/JUnitverificados. FreezeQA1liberado paraB01; QA2preparadaONLYafterB01terminal yfreshprecopiaini+absoluteconfig beforetests. No aceptación/waiver/causatemporalvieja niREDproducto.


## T06: corregir Minor B-01 después del freeze SQL

2026-10-09T03:56:39.549111+00:00: Review1 A/C/Dclean B1Minor DELETEprelifespan500sinno-store. Config2filespreparedONLYafterSQLQA39120terminal/sourcefreeze release. Nativeprecode behaviorRED missingregistry->finite503,no-store, no authbypass. Full307+new/currentWHOLEmodifiedmodule>=80/headers/speclock protected; revisión2/QA pendientes.


## Entrega técnica current-sql-projection-integration-qa1 para revisión independiente

2026-10-09T03:56:49.469439+00:00: QA1 FALLIDA 1051PASS/1FAIL arnésiniomitido/3SKIP; original801PASS8,574s10intacto. Root fullinventario/8397copies/JUnit/current6 cov≥80 noexcl cotejados, datosdebaselineFAILED noaceptación. FreezeSQL1 liberado paraB01fix; QA2freshprecopiaini preparada trasfixterminal, ninguna causa temporal histórica/waiver/speedup.



## T05 estímulo de backpressure: prueba positiva y ajuste de configuración

2026-10-09T04:00:23.034402+00:00: NuevoFull-witness PASSactual3Full/cola4/4/UNKNOWN conoldfixture; noRED. RootverificaoldAST/protected/inventory yretieneamboscalendarios. AutorizaONLYvalor payloadLinuxcompacto20progress paraseparar coste8KiBdequeuepressure, TDDn/a fixturedata, no cambios runtime/asserts/timers ni waiver. Full88+review/QA pendientes.


## T05: configuración de payload para saturación real

2026-10-09T04:00:33.160199+00:00: InitialFullregressionPASS noRED/fix fixture antiguo; Root mantieneprueba yautorizaONLYpayloadLinuxcompacto20progress/handshake/0.25/10/asserts iguales. TDDn/a fixturedata/config, no runtimecode/retornoskernel/capacidadcambiados. FullLinux42+Win46 actual una vez, sin rerunverdehastaocultarfallo.


## Entrega técnica session-http-b01-fix1 para revisión independiente

2026-10-09T04:04:11.591606+00:00: B01 RED500→503no-store,315PASS/currentWHOLEevent_routes98,11%0excl/protected23byteexact verificadosRoot. Incident8newfixtureUUIDdirs enoldproducerbeforeUNITrepair nooverwrite declarado, no retroseal. Review2+QA315/SASTcurrentsource/socketDocker pendientes, no aceptación.

RED: apps/server/tests/test_session_http.py::test_delete_unavailable_registry_before_lifespan[wrong-missing] y [wrong-none] fallaron con assert 500 == 503 · 2026-10-09T03:59:00 UTC. runs/red2 contiene fuente, runner, fixtures, argv, PID, UTC, stdout/stderr, exit1 y JUnit. runs/red inicial fue NO causal: httpx body continuación devolvió422, preservado. Test corregido a ASGI real con body vacío completo; sin lifespan ni doble de producción.



## Entrega técnica native-backpressure-diagnosis1 para revisión independiente

2026-10-09T04:04:53.805825+00:00: ONEoriginalcase H1deadlinecola3/4Full0observed, capacidadreal4 corrigeRootprompt8. Closed/kernelTrue fue deadlineválido sinFull; timinghistóricoUNPROVEN/H2notseen/observeroverheadUnknown. Rootsource20/inventory/CIDgone checked, no codefix/red/acceptance niwaiverold86/1.



## Entrega técnica native-backpressure-full-witness1 para revisión independiente

2026-10-09T04:04:54.143042+00:00: InitialtestPASS con3Fullreales/cola4/4/UNKNOWN, no causalRED/fixturepatch/full88 run. Rootinventory/oldAST/protected yCIDgone check. Se retieneprueba y se autoriza fixtureDATAcompacta en siguienteunit1constant, TDDn/a config no runtimepolicy/timer/assertchanges. No aceptación ni repeateduntilfail.



## T04: QA2 independiente con configuración completa

2026-10-09T04:05:27.478197+00:00: QA1 1051PASS/1harnessFAIL/3SKIP y801PASS8,574s; faltaalembic.ini enprivateCWD. Rootaudita fullinventario8397copies ysource/current6, preserveFAILEDhistory. Nuevofull baseline justificadofallomaterial delarness, ONLYafterB01fixsource terminal, original1055/currentnewcases y10s/cov6 intactos.


## Entrega técnica native-backpressure-fixture-data1 para revisión independiente

2026-10-09T04:09:39.706636+00:00: FixtureLinuxonly8192→xconfig,constante1 concount20/request/timers/asserts iguales. 88PASS Linux42+Win46/Full4actual, Rootinventory/Source/protected/RAWsameUUID/CIDgone/diff1line verificados. No runtimefix/TDDRED niwaiver86/1. HostinterpdepsprephysicalUNKNOWN declarado. Compositefreshreview4files yQAdualOS completos pendientes.



## T06 HTTP: auditoría estática cybersecurity preparada

2026-10-09T04:11:18.608878+00:00: Diff8files/transitive15/STRIDE ycopiasRoot before. Ochoespecialistas requeridos enwavesporlímite3+Root/quota, sólolectura SAST; noDAST/toolinstalls/CVEonlineclaim. Código/testcontratos congeladosporSQLQA23898. No auditoría aceptada ni score todavía.


## T06 HTTP: revisión de componente — intento2 conforme

2026-10-09T04:12:52.692146+00:00: A/B/C0gaps, Dselectorfalse. B01finite503/no-storecorrected; current315producer noindependentQA yet. [Informe](testing/t06/session-http-inspection2-report.md). SASTversion2 sourceactual ochoespecialistas enwaves/static yQA315 pendientes, noSSE/taskclose.


## T04 QA2: configuración corregida, fallo temporal persiste

2026-10-09T04:25:03.348303+00:00: 1051PASS1FAIL80112,348s/10intacto3SKIP; populatedmigrationPASS. RootcurrentSource/JUnit/current6WHOLE/inventory cotejados; no acceptance. DiagnósticoONE residualphase current6coverage preparado trasproyecciónreal, nofullsuite retry/waiver/priority/timercambio. Historias de causasUNKNOWN/hypótesis originales preservadas.


## T04: QA2 fallo temporal real y diagnóstico residual acotado

2026-10-09T04:25:23.626050+00:00: QA2 1051PASS1FAIL80112,348s3SKIP, populatedmigrationPASS, current6WHOLEgreen desdeFAILEDtrace NOacceptance. Projectionreader eliminatesentities buttimecase stillfails. ONEactualoriginal801currentcoverage6 boundedaggregate phases to locate remainingcost; no codefix/full1055retry/priority/timer changes. Priorcauses/hypotheses notreset.


## Entrega técnica current-sql-projection-integration-qa2 para revisión independiente

2026-10-09T04:25:33.549651+00:00: QA2FAILED1051PASS1FAILoriginal801Timeout10s/12,348scase3SKIP; populatedmigrationPASS. Rootsources/current6WHOLE/inventory/oldidentities/JUnitchecked, failedtracesnoacceptance. ONEresidualphase measurement aftercurrentprojection readylaunched, no allsuiteiters/waiver/oldcauseproof/speedup claimed.



## T06 HTTP: cybersecurity SAST diff actual completado

2026-10-09T04:28:19.562142+00:00:8/8especialistas actualguard,0findings/score100A limitadoaldiffSAST. [Informeprivado](../../security-scan/2026-10-09_0428/index.html) ySTATE/auditindex actualizados. SinCVEonline/DAST/socketDocker/repo completo ni aceptaciónT06. QA315pendiente; security1partialno reused.


## T06: QA315 independiente preparada para fuentes actuales

2026-10-09T04:35:51.588010+00:00: B01review2A/B/Cclean y315producer; SASTcurrent2 requerido. QA315readonlyconfigready, launchONLYafterSQLQA2timingterminal/SASTactualcomplete/slotfree; no sourcewrite/taskacceptance.


## T05: revisión del drenaje y QA pendiente

2026-10-09T04:36:34.045703+00:00: A/B/C/D sin defectos nuevos. [Informe](testing/t05/drain-combined-inspection1-report.md). QA independiente de Linux42 y Windows46 preparada; cobertura actual de cuatro módulos pendiente de verificar. T-05 permanece en-progreso.


## T05: QA independiente del drenaje tras revisión limpia

2026-10-09T04:36:34.631651+00:00: Revisión A/B/C/D sin defectos nuevos. QA independiente de 88 casos y cuatro módulos completos, con cobertura oficial >=80 % y cero exclusiones. Las fuentes y fixtures permanecen intactas; T-05 sigue abierta.


## T04: diagnóstico residual recogido y diseño equivalente pendiente

2026-10-09T04:38:57.342813+00:00: Caso original801 pasó una vez con submit CPU a 9,141 s y timeout10 intacto. Validación contractual retry: 0,045455 s; lectura/materialización concentra coste inclusivo. No prueba causa histórica, overhead exclusivo ni speedup. QA2 sigue fallida. Diseño estático acotado sin nuevos benchmarks ni modificación de producto.


## Entrega técnica postprojection-residual-spans1 para revisión independiente

2026-10-09T04:39:29.060073+00:00: Una ejecución original801 PASS; CPU submit9,141 s con timeout10 intacto. Agregados inclusivos de lectura/materialización, validaciones retry0,045455 s. Sin causa histórica probada ni waiver de QA2; diseño equivalente pendiente.



## T06: aceptación técnica de sesiones HTTP

2026-10-09T04:41:58.180285+00:00: QA independiente 315 PASS, sin fallos ni skips; cinco módulos completos entre 96,97 % y 100 %, cero exclusiones. Revisión actual A/B/C y ocho lentes estáticas conformes. Fuentes y copias previas cotejadas. [Aceptación del componente](testing/t06/session-http-independent-qa1-acceptance.json). Transporte real, endpoint SSE, snapshot transaccional, cliente y E2E siguen pendientes; T-06 permanece abierta.


## T06: siguiente unidad SSE tras aceptar sesiones HTTP

2026-10-09T04:43:53.522811+00:00: QA independiente HTTP315 aceptada. Comienza U2c del diseño adoptado: coordinator síncrono, feed con autoridad interna y construcción pura del snapshot. No se expone GET SSE hasta conectar todos los escritores y validar snapshot WAL real. TDD/revisión/QA actuales obligatorios.


## Entrega técnica session-http-independent-qa1 para revisión independiente

2026-10-09T04:44:15.410711+00:00: QA independiente315 PASS, cinco módulos WHOLE >=96,97 % y cero exclusiones; Root acepta únicamente el componente HTTP. Fuente y copias actuales cotejadas. SSE/worker/Git/E2E y T06 completos siguen pendientes.



## T05: 88 pruebas conformes; formato QA01 pendiente

2026-10-09T04:46:52.745745+00:00: QA independiente Linux42/Windows46 PASS y cuatro módulos actuales >=80 %, cero exclusiones. Único gap: Ruff format del nuevo witness Linux. Se autoriza sólo formato de ese test, AST completo idéntico, sin cambios de runtime, fixtures, assertions ni parámetros. Después, revisión fresca y suplemento QA de formato/AST; el fallo inicial se conserva.


## Entrega técnica residual-materialization-design1 para revisión independiente

2026-10-09T04:48:12.122776+00:00: Root conserva el runtime: las alternativas pierden identidad/estado entre particiones, autoridad de escritura o carecen de equivalencia probada. Diseño estático30copias verificado; no tests nuevos ni speedup. QA2 sigue fallida. Continúa SSE y publicación CPU.



## Entrega técnica drain-combined-independent-qa1 para revisión independiente

2026-10-09T04:48:12.218920+00:00: QA88 funcional PASS, cuatro módulos actuales WHOLE >=80 % sin exclusiones y CID propio gone cotejado. GATE FAILED por único QA01: formato de test Linux. Fix sólo layout delegado, AST íntegro y runtime byteexact; no aceptación hasta revisión y suplemento QA.



## T05: revisión del formato limpia; suplemento QA independiente

2026-10-09T04:56:25.522590+00:00: A/B/D sin defectos nuevos; selector C false. QA independiente de Ruff check/format y AST completo sobre el único test formateado. Producción sigue byteexact respecto a las 88 pruebas; no se inventa otra ejecución ni se repite nativo sin motivo. T05 abierta.


## T05: aceptación técnica de custodia y drenaje

2026-10-09T05:02:15.903916+00:00: Linux42/Windows46 PASS, cuatro módulos actuales completos >=80 % sin exclusiones; RAW87 y copias previas cotejadas. QA01 de formato corregido con AST completo idéntico, revisión limpia y suplemento independiente Ruff0/format0. [Aceptación del componente](testing/t05/drain-native88-acceptance.json). Se conserva el fallo inicial y no se inventa otro run88 ni cierre universal. Publicación CPU, assets/manifiesto, reconciliación, análisis y T-05 completos pendientes.


## Entrega técnica drain-format-qa01-fix1 para revisión independiente

2026-10-09T05:03:20.743178+00:00: QA01 corregido sólo por Ruff layout, AST/comentarios completos idénticos y runtime byteexact. Revisión A/B/D limpia y suplemento independiente conforme; fallo QA01 original preservado.



## Entrega técnica drain-format-independent-supplement1 para revisión independiente

2026-10-09T05:03:20.819004+00:00: Ruff check/format0 independientes, AST contra preimagen y copiaQA88 idéntico, siete fuentes byteexact, RAW87 y copias cotejadas. Root acepta componente custodia/drain de QA88 original; no nuevo nativo ni T05 completo.



## Entrega técnica coordinator-snapshot-unit1 para revisión independiente

2026-10-09T05:07:48.527343+00:00: Productor239 PASS, cuatro módulos actuales WHOLE >89 % sin exclusiones, fuentes/protected/RED auditados. CONCERNS de drift global corresponde sólo al test Linux formateado por Root fuera de esta selección; todo AST y old selected byteexact. No QA independiente, shared writers/WAL/HTTP aún pendientes; QA2 sin waiver.



## T06: revisión intento1 detecta B01; corrección TDD

2026-10-09T05:15:08.421333+00:00: A/C/D limpios; B detecta Important B01: published=True cuando bus rechaza silenciosamente o está shutdown. Se autoriza regresión con EventBus real y acuse explícito; resultado durable y gap conservados. Historial239/4WHOLE preservado; nueva revisión y QA pendientes.


## T05: preparar captura de procedencia para publicación CPU

2026-10-09T05:19:07.086387+00:00: Custodia/drain88 aceptados y contratos de publicación existentes. Diseño estático acotado del constructor real de JobAttempt.provenance+SHA y observación efectiva; reutiliza mapa de exploración existente, no inventa campos ni procedencia ni toca modelos/cola mientras SSE se corrige.


## T05: decisión de captura de procedencia

2026-10-09T05:27:06.163984+00:00: Root elige O2 por delegación, [ADR-0060](../../decisiones/ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md). Diseño estático27copias verificado; ninguna prueba ni generación ejecutada. Captura real write-once y sus seis módulos pendientes; coordinación de fuentes con QA SSE antes de implementar. T-05 sigue abierta.


## Entrega técnica provenance-capture-design1 para revisión independiente

2026-10-09T05:27:36.241117+00:00: Root adopta O2 en ADR0060: captura real write-once tras load/Health fresco y antes de submit, sin backfill. Diseño estático27copias, fuentes7 intactas; no tests ni generación. Implementación6módulos pendiente de coordinación con QA SSE.



## T06: revisión del componente — intento2 limpia

2026-10-09T05:29:35.958570+00:00: A/B/C/D sin defectos nuevos; B01 corregido con confirmación efectiva, count y retorno legacy conservados. [Informe](testing/t06/coordinator-snapshot-inspection2-report.md). QA246 independiente preparada; cuatro runtime y seis fuentes U2c se congelan hasta resultado. No aceptación de T06 ni waiver SQL QA2.


## Entrega técnica coordinator-b01-fix1 para revisión independiente

2026-10-09T05:29:36.038277+00:00: B01 corregido con RED real3fallos/1válido y246PASS, cuatroWHOLE>=80 sin exclusiones. publishNonelegacy conservado, acuse explícito/count; revisión2A/B/C/Dlimpia. QA independiente pendiente; prototipos de publishers no acreditan comportamiento real, QA2sinwaiver.



## T06: QA246 independiente preparada tras revisión2

2026-10-09T05:29:36.592222+00:00: Lanzar sólo con A/B/C/D de revisión2 terminales y limpios. Baseline246 exacta y cuatro runtime WHOLE actuales >=80 % cero exclusiones, nueva traza independiente. No full453/801 ni worker native, QA2 intacta; freeze scoped seis fuentes U2c hasta resultado.


## T06: auditoría estática del feed certificado actual

2026-10-09T05:36:13.901837+00:00: Scope cumulative U2c6 actual después B01, copiasRoot y STRIDE preparados. Ocho lentes cybersecurity en waves por máximo3+Root; SAST sin DAST/installs/currentCVE claim. QA246 actual activa, fuentes congeladas. No resultado ni aceptación de seguridad todavía.


## T06: aceptación técnica de coordinación y snapshot

2026-10-09T05:39:11.270308+00:00: QA independiente246 PASS, sin fallos ni skips, cuatro módulos completos >=90,32 % salvo snapshot93,75 % y cero exclusiones; revisión2A/B/C/D limpia. Fuentes/artefactos actuales cotejados y freeze de cola liberado para procedencia. [Aceptación del componente](testing/t06/coordinator-snapshot-independent-qa1-acceptance.json). Auditoría estática acumulada sigue en curso; endpoint, todos los escritores, WAL/replay, cliente y T-06 completos permanecen pendientes.


## Entrega técnica coordinator-snapshot-independent-qa1 para revisión independiente

2026-10-09T05:40:12.051702+00:00: QA246PASS y cuatroWHOLE90.32/93.75/95.23/94.52zeroexcl, nueva traza/sources actuales cotejados; Rootacepta sólo coordinador/feedinterno/snapshotpuro. Freeze cola liberado; SASTnuevo6 sigueen curso, exposiciónSSE/WAL/writers/cliente/T06 pendientes.



## T05: implementar captura write-once tras liberar QA SSE

2026-10-09T05:41:37.022916+00:00: ADR0060 O2 adoptada, QA246 interna aceptada y freeze de cola liberado. Se transfiere ownership de seis módulos de cola para captura real después de load/Health fresco y antes submit, con SQLite/engine declarado y TDD. Modelo/custodia/SSE/contratos protegidos; original80110 integración sólo sin otra carga nativa, no waiverQA2.


## T06: SAST del feed certificado completo con VULN-001

2026-10-09T05:59:12.474955+00:00: Ocho especialistas completados,98.5/A limitado al diff U2c6;1Medium VULN-001 rechazo precommit provoca gap global. [Informe privado](../../security-scan/2026-10-09_0559-sse/index.html). Securitygate pendiente de fixTDD; QA246 histórica no acredita ausencia del defecto. Fuentes/copias cotejadas; sin DAST/CVEonline/repo completo ni aceptación de exposición SSE/T06.


## T06: VULN-001, definir rollback confirmado sin romper primera causa

2026-10-09T06:00:50.339555+00:00: SAST8 identifica Medium VULN-001: rechazo precommit invalida feed compartido. Diseñar sólo discriminación de rollback confirmado vs commit incierto, preservando primer error/legacy/default consumidor. Readonly mientras provenanceunit protege archivos; no fix/exposición/aceptación falsa.


## T05: regresión de procedencia fallida, clasificación sin cambiar tests

2026-10-09T06:06:55.057980+00:00: Productor288=213PASS75FAIL,54newPASS, current6WHOLEgatefalse. Rootadjudica sinaceptar. Clasificar67descriptor/digest y8others; engine_mockreal weights[] legítimo exige soporte explícito sininventarpesos ni etiquetarsynthetic comoSHAreal. Sólolectura, no asserts/timers/captures weakening, fixture data propuesta concreta.


## T06: ADR0061 y TDD de VULN001 después del handoff

2026-10-09T06:10:36.350673+00:00: RootadoptaO1 rollbackoutcome privado, ADR0061; provenance productor terminal libera pub/events. Nuevo RED realSQLite/bus/lector contra gap-global, luego mínima corrección de dosruntime. QA246 histórica y SAST98.5/Medium preservados, no aceptaciónhasta freshreview/QA/focusedrescan.


## Entrega técnica provenance-capture-unit1 para revisión independiente

2026-10-09T06:11:59.222801+00:00: Código6runtime/2tests actual,54newPASS pero288=213PASS75FAIL/current6WHOLEgatefalse; noaceptación. Descriptor/digestfixtures +legacycapture/mocks debenclasificarse, engine_mockrealweightless debe conservarsoportehonesto. No asserttimerweakening, full801pending, sourcepub/eventshandoff liberado.



## Entrega técnica confirmed-rollback-design1 para revisión independiente

2026-10-09T06:11:59.292454+00:00: RooteligeO1 enADR0061, outcomesellado sólo tras rollback real/cierrecompleto yningúncommitintentado. Preservaprimario/feed, genérico/inciertogap. Diseñoestáticonotested, sourcepub/eventshandoff confirmado; fix98748actualenprogreso, VULN001 sigueabierta.



## T05: compatibilidad sintética explícita, ADR0062

2026-10-09T06:22:20.508061+00:00: Root adopta variante privada tipada con binding confiado, [ADR-0062](../../decisiones/ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md). Clasificación estática75fail sin ejecutar; no pesos/digests ficticios ni assertions/timers cambiados. Se autoriza preparar fixtures válidas y producto mock real sin rebajar la rama aprendida; implementación y QA pendientes, no aceptación.


## Entrega técnica provenance-regression-analysis1 para revisión independiente

2026-10-09T06:22:20.847300+00:00: RootadoptaADR0062: evidencia sintética tipada conbindingserver, realmockweightless legítimo, learnedweights safeguards kept. Clasificación75static/41copies no runtimeverification; oldassertsparams unchanged, fixturevalidcapture/setup propuesta. Código/QA/publicación real pendientes.



## T-05 · Composición confiada de evidencia sintética — diseño acotado

2026-10-09T06:30:56.386366+00:00: ADR0062 adoptado; análisis de los75 fallos terminal, sin aceptación. Diseño readonly de composición y API exacta antes de la siguiente unidad TDD. Dos revisores de rollback disjuntos; no mutar fuentes protegidas. Modelo/uso real desconocidos.


## Entrega técnica confirmed-rollback-unit1 para revisión independiente

2026-10-09T06:33:14.710033+00:00: ADR0061 O1 implementado: productor271PASS, cuatro módulos WHOLE>=93% cero excluidas, cuatro RED causales, originales246 conservados. Entrega revisable, no aceptación; revisión A/B/C/D y QA independiente pendientes. Histórico VULN001 Medium sigue abierto hasta contraste actual. T-06 continúa en-progreso.



## Revisión de dos lentes — intento 1: rollback ADR0061

2026-10-09T06:35:44.842028+00:00: scope0 sin avisos/exclusiones; A/B/C/D de contexto fresco terminal0. A/C/D sin gaps; B-01 Important aceptado: KeyboardInterrupt tras adquirir writer abandona transacción/sesión; prueba SQLite en memoria del revisor contrasta legacy. T-06 en-progreso. Fuentes actuales congeladas verificadas y handoff liberado para fix1 TDD; nueva revisión será intento2. Productor271PASS no sustituye QA independiente. Histórico VULN001 no cerrado. [Informe](testing/t06/confirmed-rollback-review1.md).


## T-06 · Revisión rollback intento1 — B01 interrupciones requieren cierre

2026-10-09T06:35:52.218778+00:00: B01 Important aceptado: camino manual no garantiza rollback/close ante KeyboardInterrupt tras adquirir writer; prueba SQLite en memoria del reviewer comparó session activa con legacy cerrada. Corregir con RED conductual real y preservar mismos271 casos, identidad/traceback/gaps. Revisión1 historial retenido; nuevo diff va a revisión2, QA independiente pendiente. No cerrar T-06.


## Entrega técnica synthetic-composition-design1 para revisión independiente

2026-10-09T06:37:36.622494+00:00: ADR0062 composición adoptada: receta CPU empaquetada sin imports de engine, registry inmutable/backend exacto antes del catálogo, rebind contra autoridad recompuesta y serialización learned SHA histórica exacta. Seis módulos runtime propuestos. Diseño estático, cero tests/código; handoff del contrato espera fix rollback85243 terminal. No aceptación T-05.



## Entrega técnica confirmed-rollback-review1-fix1 para revisión independiente

2026-10-09T06:47:38.973401+00:00: B01 interrupciones corregido con RED real SQLite prepare-KeyboardInterrupt. Productor294PASS (246+25+23), cuatro WHOLE>=93% cero excluidas, antiguos246 bytes y25 funciones/assertions AST conservados. Cambios después de baseline sólo comentarios noqa/AST con ubicaciones exactas; lint/check actuales0. Entrega revisable, revisión2 A/B/C/D y QA independiente/focused logic pendientes, no aceptación T-06 ni cierre histórico Medium.



## Revisión de dos lentes — intento 2: rollback confirmado ADR0061

2026-10-09T06:53:47.262453+00:00: scope0 sin avisos/exclusiones; A/B/C/D contexto fresco terminal0, cero gaps. B01 corregido técnicamente con RED real, productor294PASS e independiente reviewerB SQLite/in-memory; no señal OS. WHOLE4 actuales>=93% cero exclusiones y paridad AST con ubicaciones tras comentarios. QA294 independiente y focusedlogic pendientes; históricoMedium no cerrado. T-06 en-progreso. [Informe](testing/t06/confirmed-rollback-review2.md).


## T-06 · Seguimiento focal de seguridad VULN001

2026-10-09T06:55:26.932728+00:00: Revisión2 A/B/C/D limpia; followup readonly categoría logic para VULN001 sobre código actual. No repetir ocho categorías ni inventar fullscore100; Medium histórico hasta contraste actual y QA independiente. No DAST/CVE/red/tests/native.


## Entrega técnica rollback-followup para revisión independiente

2026-10-09T07:03:32.645792+00:00: Seguimiento focal actual de VULN-001 aceptado: causa corregida en código; BUSINESSLOGIC100 sólo en este ámbito, cero hallazgos nuevos. Inventario48 y nueve fuentes actuales exactos verificados; originales de auditoría98.5/Medium preservados. QA294 independiente y aceptación técnica pendientes, sin nueva auditoría completa ni DAST/CVE ni cierre T-06.



## T-06 · QA294 independiente con agente disponible

2026-10-09T08:12:47.148775+00:00: CLI auxiliar detenido por límite de uso; nativeactor27982 terminal1 y nativefinal02 incompleto, no aceptado. Se reutiliza agente existente de trabajo UI ajeno para rol QA sólo lectura sobre rollback, no productor y sin atribuir contexto vacío/modeloSonnet. Fuentes de review2 actuales exactas, release de competencia temporal acotado: PIDs6576/25840 y procesos fase no observados. ONE QA294/WHOLE4 fresco, no native/801 concurrente; no falsa prueba de cierre universal. Root sólo ledger/aceptación.


## Entrega nativa confirmed-rollback-independent-qa1 para adjudicación

2026-10-09T08:36:36.827985+00:00: QA294 independiente técnica aceptada por Root:294PASS0fail/error/skip, WHOLE4>=93% cero exclusiones,9.632originales/244fuentes/33protegidos/8.126tools exactos verificados. Contexto nativo UI ajeno reutilizado declarado, no productor ni CLI0 ficticio. Alias-target-before/TCB/DLL/kernel/nestedOSUNKNOWN conservados; fixturemetadata no pesos reales. Sólo rollback/interrupciones: T-06/app/allwriters/WAL/cliente siguen pendientes.


## T-05 · ADR0062 implementación nativa tras handoff

2026-10-09T08:39:50.091912+00:00: QA294 rollback aceptada; worker/contracts y fixtures liberados explícitamente. Se reutiliza agente nativo de QA ajena para implementación con nuevo brief, contexto no vacío declarado y uso/modeloNULL. Quince archivos exactos:seisruntime,helper+testnuevo y setup-onlysieteantiguos, asserts/params/timers/querybounds preservados. Prueba801 una baseline autorizada tras cambios concretos, sin native concorrente; final02 incompleto no acreditado. No CLI por cuota agotada, no nuevasdependencias/modelos/red/GPU/Docker/WSL/UI. FreshRED conductual real descriptor()mock+SQLite beforecode y WHOLEcada6+dispatcher/retry>=80zeroexcl, revisión/QA posterior. T-05 en-progreso.


## T-06 ? Preparaci?n de integraci?n WAL y HTTP

2026-10-09T08:55:46.738178+00:00: Inspecci?n de fuentes y enlaces completada; [preparaci?n de integraci?n](testing/t06/integration-readiness.md) conectada al plan. Identificados writers de admisi?n, cadenas, cancelaci?n, recuperaci?n, retries y eventos; TrustedFeedScope ya existente evita conjuntos crecientes. Runtime todav?a crea EventConsumer sin coordinador y no hay GET /api/events. Pr?xima unidad conserva sesi?n dedicada, reautorizaci?n, l?mites y pruebas WAL/reconexi?n; no se modifica producci?n ni se acepta T-06. Ownership de unidad sint?tica respetado. TDD n/a: prosa/inspecci?n.


## T-06 ? Propuesta de contrato del stream validada

2026-10-09T09:02:46.402781+00:00: [Propuesta OpenAPI](testing/t06/events-openapi.proposed.json) generada antes del handler, con controles derivados de DTOs actuales y todas las operaciones/componentes anteriores conservados. api-contract lint exit0 sin errores/avisos; diff exit0, cero rompedores y un path nuevo /api/events. Nombres de query, cambio de filtro y error por exceso requieren adjudicacion antes de integrar. Contrato canonico/router/cliente sin cambios; no es prueba de HTTP, autorizacion o WAL ni cierre T-06. TDD n/a: especificacion/configuracion.


## T-05 ? Focales causales de procedencia sintetica observados

RED: test_real_cpu_mock_owned_runtime_captures_before_fixture_submit fallo con AssertionError: Configured real CPU mock never reached durable submit assert 0 == 1  +  where 0 = len([]) ? 2026-10-09T08:52:18.048263+00:00; comando original exit1/direct_wait y JUnit1failure0error.

RED: test_registry_issues_only_exact_bound_identity_lease fallo con AssertionError: Trusted recipe did not issue an authority lease assert None is not None ? 2026-10-09T08:54:11.435717+00:00; comando original exit1/direct_wait y JUnit1failure0error.

Primer GREEN funcional green-sql-compatible:2PASS0failure0error, PID24936/exit0/direct_wait. green-initial exit1 por compilacion SQL del pattern conserva su error; implementer corrigio dentro contracts sin modificar migraciones. Root lee originales, no acepta unidad por estos focales: baseline completa, WHOLE, revision y QA pendientes. Fuentes siguen bajo ownership del implementer.


## T-05 ? Ampliacion explicita de setup retry

2026-10-09T09:10:37.696263+00:00: Root autoriza test_dispatcher_retry.py como OWNED16 setup-only, con archivo y forma original capturados antes; quedan36protegidos y se conserva el manifiesto37 historico. Se declara composicion de fixtures en constructores/import explicitos, sin remap privado del target QueueRuntime ni confianza runtime por clase/atributo. Todos los asserts/params/decorators/IDs/plazos originales80110s se conservan. Revisar este diff ampliado y QA correspondiente; unidad/T-05 no aceptados.


## T-05 ? Preparacion de revision nativa independiente

2026-10-09T09:25:02.629362+00:00: Disponibilidad real de audit_t17 y audit_t10_container_runtime confirmada por collaboration FINAL_ANSWER; trabajos anteriores ajenos, ambos declaran no haber implementado/revisado la unidad sintetica. Contexto reutilizado declarado, no vacio. Nuevo preparador nativo requiere terminal real y SHA del recibo, inventario/custodia/freeze/alcance/lentes; no fabrica CLIexit0. Sintaxis comprobada, aun no ejecuta revision: productor tiene baseline en marcha y posible fix pendiente. No cambia criterios ni acepta unidad/T-05.


## T-05 ? Baseline interrumpida por fixture incompatible

2026-10-09T09:38:03.822767+00:00: Baseline15suites/598casos segun AST del productor se detuvo en caso396;395indicadores y3F son parciales. Backend+offload no coincidia con receta capturada por prepared; rebind rechazaba correctamente y _consume directo esperaba stop. Tras verificar identidad/argv/ancestros/CreationDate se termino solo pytest19044; sesion95715 terminal real1, redirector4294967295/direct_wait. Sin JUnit/cobertura final, no se acepta la unidad ni se inventa cierre. Fs142/372/373 se diagnostican con focales originales; setup de receta y ambas fronteras de envio preserva asserts/plazos. Nueva baseline completa espera liberacion temporal T09.


## T-05 ? Baseline599 completa roja y ajuste de medicion

2026-10-09T09:59:10.250954+00:00: Baseline actual599=597PASS2FAIL0error/skip, waitreal1. WHOLE8 cada>=80/ceroexcl, pero fracaso80110s y nueva espera0.3s impiden aceptar unidad. Se conserva original all-app trace/config/testbefore. Root autoriza instrumentacion de ocho modulos completos (source_pkgs, branchTrue, ceroexcl) y focal comparador801 con plazo10 intacto; no permite ampliar deadlines historicos ni cambiar producto sin causa probada. Nuevo test usa evento del POST despues de asserts SQL/body y wait_for finito control_s; no se atribuye0.3s a SLA de producto. Comparadores y Root autorizacion pendientes antes de fullbaseline.


## T-05 ? Aislamiento temporal del recorrido801

2026-10-09T10:06:59.843217+00:00: Focal observacional80110s termina rojo con memoria limitada/overflow0; await de paginas next2.0808s y1.3337s, huecos fuera de dbcall3.7544s y4.0427s. No son medidas native-direct-return. Hipotesis all-app exclusiva descartada por comparator source_pkgs8; evento POST pasa. Root solicita lectura independiente route/schema y una hipotesis falsable, sin escribir producto ni correr otra suite completa. Causa y fix801 pendientes.


## T-05 ? Causa medida y decision de resolucion posterior al filtro

2026-10-09T10:13:42.476331+00:00: Diagnostico valido/overflow0:800select=6.989347s dentro de799route completados=8.441079s (no sumar tiempos anidados). Lectura independiente confirma construccion repetida antes de _screen. [ADR-0063](../../decisiones/ADR-0063-procedencia-en-resolucion-completa-tras-routing.md) elige seleccion/lease en resolve completo; route conserva elegibilidad/carril y preflight/CAS/health positivos. RED conductual antes del fix,80110s/counters/SQL intactos y binding/snapshot/focales requieren verificacion. No se acepta rendimiento por la medicion previa; revision/QA siguen pendientes.


## T-05 ? Seleccion fuera de routing, controles focales verdes

2026-10-09T10:17:43.149770+00:00: RED conductual genuino de route que emitia seleccion (red-routing-selection-authority exit1) antes de fix minimo resolver. Focal posterior96=95PASS1FAIL: nueva separacion, CPUEvent, old54 y binding/snapshot/SQL verdes;80110s aunTimeout. No se afirma plazo resuelto ni acepta unidad. Se autoriza una nueva observacion pasante en codigo corregido para distinguir route restante/next, con nuevas fuentes/traza y deadline/counters/SQL originales. Sin fullbaseline ni fix ciego.


## T-05 ? Original801 verde despues del fix causal

2026-10-09T10:21:13.583553+00:00: diagnostic-route-select-after-fix-801 real1PASS/exit0/direct_wait con80110s/counters/SQL originales. Perfil valido0overflow:select1/0.006143s,route802/1.0063s frente seleccion800/6.9893s antes. Tiempos anidados no se suman; next8.0045s incluyeespera/materializacion. El tiempo total del caso incluye setup/cierre y no se confunde con wait10s. Root autoriza UNA baseline completa actual sin wrappers diagnosticos, fuente8/ceroexcl y traza nueva, tras paridad/lint/protected. No aceptar unidad por focal; delivery/freeze/revision/QA pendientes.


## T-05 ? Completa600 roja: plazo original requiere margen consistente

2026-10-09T10:26:56.439903+00:00: baseline-authoritative-600 REAL600=599PASS1FAIL80110s, exit1/direct_wait, WHOLE8 cada>=80/ceroexcl. Focal previo801verde no acredita comportamiento consistente; no se acepta unidad ni se repite fullsuite sin causa nueva. Perfil post-fix next8.0045s frenteroute1.0063s/select0.00614s orienta siguiente aislamiento hacia lectura/materializacion/JSON. Se solicita lectura independiente de proyecciones y propuesta de perfil nativo en memoria, sin relajar guards, querybounds, snapshot o deadlines.

## T-05 — Validación JSON descartada como cuello principal

Observación `diagnostic-native-thread-json-801`: terminal real exit1/direct_wait,
un caso fallido por el plazo original de 10 s, sin skips. Root verificó las
ventanas por identidad de hilo, los contadores originales, overflow cero,
fuentes sin cambios y las 36 protegidas exactas; recibo privado
`.cache/dev-cycle/m1/t05-synthetic-compatibility-unit1/root-thread-observation-adjudication.json`.
Se ejecutaron 801 validaciones de cada tipo: request 0,0204 s, load 0,0061 s,
event 0,0793 s y procedencia 0,0041 s. Son intervalos anidados; no se suman
al tiempo de `next`. El mayor callback `next` tardó 5,913 s de pared y
1,188 s de CPU de su hilo. La validación tipada no explica el cuello medido;
SQL, ORM y competencia con otros hilos aún no están aislados.
El perfil cProfile anterior contiene callbacks del event loop y no acredita
atribución exclusiva al hilo nativo. Se conserva con esa limitación.
Autorizada una observación original801 con SQL/ORM filtrados por hilo y CPU
del proceso, sin cambiar producto, plazos, límites o validaciones y sin otra
suite completa hasta probar una causa nueva. La unidad sigue sin aceptación.

Observación posterior `diagnostic-native-sql-orm-801`: terminal exit0/direct_wait,
original801 PASS. Root recalculó contadores y verificó JUnit, ventanas por hilo,
fuentes exactas y 36 protegidas en `root-sql-orm-observation-adjudication.json`.
Los 17 cursor_execute consumieron 0,1014 s y los 2.404 processors ORM 0,0135 s;
no explican las ventanas next de 5,3625/2,5526 s. Estas tuvieron 0,875/0,2969 s
de CPU propio frente a 6,0313/2,8281 s del proceso. Hay actividad de otros hilos,
pero no se prueba una causa exclusiva de GIL ni se descarta fetch/procesamiento
restante. La condición del test incluye un heartbeat con sleep(0), preservado.
La baseline completa roja sigue vigente; no se acepta rendimiento por este
focal ni se repite la fullsuite sin cambio causal demostrado.

## T-06 — Diseño integral elegido y cliente fetch despachado

Root verificó físicamente las 63 fuentes del diseño privado del arquitecto;
selecciona O1, coherente con ADR-0056/0058: coordinador compartido, todos los
escritores, bootstrap WAL, autorización, HTTP y navegador. Diseño público:
[Integración completa](testing/t06/integration-design.md). La excepción de
metadata necesita precisión y ADR antes del cambio de escritores; no se
mueve ni debilita ninguna comprobación actual.

Cliente despachado con ocho archivos exclusivos, dos preimágenes y 42
fuentes protegidas en `.cache/dev-cycle/m1/t06-fetch-client-unit1`.
Actor nativo `debug_t09_estimate_continuity`: contexto anterior de diagnóstico
T05 ajeno declarado; implementer del cliente, no su QA/reviewer. TDD causal,
fetch con credencial sólo en memoria, parser acotado, snapshot atómico,
reconexión/cursor y cancelación. Archivos añadidos al alcance de T-06:
`apps/web/lib/event-parser.ts`, `apps/web/lib/event-parser.test.ts`,
`apps/web/lib/event-reducer.ts`, `apps/web/lib/event-reducer.test.ts`,
`apps/web/lib/event-session.ts`, `apps/web/lib/event-session.test.ts`, además
de los dos archivos events existentes. Fuera de alcance server, cola,
contratos canónicos, generados y dependencias. Las ventanas de carga temporal
se coordinan por handles reales; sin reiniciar ni detener procesos ajenos.
La unidad cliente no acredita integración HTTP/Docker/E2E ni cierra T-06.

## T-05 — Verificación separada calibrada y ejecuciones nuevas verdes

[ADR-0064](../../decisiones/ADR-0064-verificacion-funcional-y-cobertura-con-coste-de-instrumentacion.md)
adopta la recomendación metodológica independiente O2; Root verificó 19 fuentes
del informe. La nueva colección real contiene 600 IDs únicos para funcional
y 599 para cobertura, con omisión explícita únicamente del parámetro801 en
la instrumentación. Las pruebas funcionales siguen incluyendo ese caso y
su plazo de 10 s; parámetros200/400 y aserciones originales se conservan.

Productor reporta terminales reales exit0/direct_wait: funcional600 sin traza
600PASS, UTC11:09:42–11:12:21; cobertura599 con source8, 599PASS y una deselection
instrumental declarada, UTC11:12:37–11:16:27. Los dos conjuntos son distintos:
no se suman para inventar una suite ni se unen coberturas históricas.
La baseline antigua599PASS/1FAIL sigue roja y preservada. Paquete nuevo
READY_FOR_REVIEW: Root todavía debe verificar inventario, fuentes, JUnit y
cobertura antes de despachar revisión y QA. Ninguna aceptación de T-05.

## Revisión de dos lentes — intento 1: T-06, cliente fetch

Root verificó la entrega real: 106 archivos originales, ocho fuentes finales
idénticas a la ejecución completa de 207 casos/13 suites sin fallos ni skips,
42 protegidas y dos preimágenes. Lint y TypeScript exit0. LCOV oficial completo
de los cuatro módulos: porcentajes combinados por archivo96,18–97,89 %;
configuración include explícita y exclude vacía. Los títulos de algunos
parameterized cases se repiten; se cuentan los elementos reales del JUnit,
sin fingir que el título identifica los parámetros. Recibo Root privado
`t06-fetch-client-unit1/root-delivery-verification.json`.

Scope-check exit0 sin avisos ni exclusiones; selector activa A/B/C/D. Actores
nativos genéricos reutilizados de trabajos ajenos, independientes del productor:
A `audit_t17`, B `audit_t10_container_runtime`, C `debug_t09_native_clock_precision`,
D `design_t09_autonomous_observability`. Prompts literales del plugin1.22.0 y
persona backend antepuesta en B; modelo/tokens/coste reales desconocidos.

A y B terminales con hallazgos estáticos: CLIENT-01 cursor viejo restaurado
por reentrada de callback al cambiar scope (ambas lentes); CLIENT-02 espera
sin límite de cancelación subyacente (A); CLIENT-03 snapshot ignorado por
callback opcional vacío, aunque se confirma el cursor (B). Los tres son
Important pendientes de verificación causal y corrección; no son repros
ejecutadas por los revisores. Fusión preliminar privada:
`t06-fetch-client-review1/root-preliminary-a-b-fusion.json`.
C y D están en curso; no se modifica la fuente congelada antes de recibir
sus resultados. La tarea continúa abierta y no hay QA independiente nueva.

C y D ya devolvieron sus FINAL reales sin hallazgos de seguridad/rendimiento
introducidos; cotejaron las ocho fuentes y explicitan que no hicieron probes.
Sus veredictos no rebaten los tres defectos de corrección de A/B.
Root verificó además CLIENT-04: cada cambio de scope construye otra sesión,
pero el cierre elimina el token sin revocarla; el registro real conserva
32 records hasta ocho horas. La navegación repetida puede agotar sesiones.
Se añade como Important de disponibilidad con RED causal pendiente.

Root fija el [contrato del cliente](testing/t06/client-contract.md): snapshot
consumer obligatorio, confirmación sólo en scope vigente, credencial por
suscripción y revocación de cierre finita. El cleanup incierto se conserva
como desconocido y se informa de forma acotada, sin declarar cierre falso.
Fix1 liberado al productor original dentro de los mismos ocho archivos,
con ocho preimágenes nuevas y 42 protegidas actuales capturadas en
`.cache/dev-cycle/m1/t06-fetch-client-review1-fix1`. Tests causales primero;
full web/V8/lint/TypeScript después. Segunda revisión conserva esta tabla
de defectos y no reinicia el contador. Ninguna aceptación ni cierre T-06.

## T-06 — Decisión de integración de escritores sin quitar controles finales

[ADR-0065](../../decisiones/ADR-0065-comprobaciones-finales-de-metadata-bajo-barrera.md)
adopta M1 del diseño: conservar bajo coordinador→SQLite los controles finales
de metadata de referencias autorizadas y staging propio. No se leen bytes,
calculan hashes, copian/limpian archivos ni hacen red/awaits bajo esa barrera.
La inspección de `resolve_references(verify=False)` confirmó que la excepción
incluye originales autorizados, además del staging. No se ha cambiado código
congelado de T-05; integración/runtime y sus pruebas todavía pendientes.

Fix1 cliente: productor reporta nuevos RED conductuales de los cuatro gaps
y GREEN focal87 casos. Primera verificación nueva completa219PASS/13 suites,
V8 cuatro módulos completos y TypeScript0; lint detectó sólo una declaración
`let` de fixture que debía ser `const`. Resultado conservado como lint rojo,
no como RED de producto. Autorizada una nueva verificación completa sobre
los bytes finales tras esa corrección de test. La entrega/freeze/revisión2
y QA siguen pendientes; no se acepta el componente por el primer219PASS.

## Revisión de dos lentes — intento 1: T-05, compatibilidad sintética

Root cotejó 17.115 archivos originales, 16 fuentes actuales, 36 protegidas y
116 fuentes idénticas entre las ejecuciones. JUnits/IDs/orden exactos:600
funcionales y599 instrumentados según ADR-0064. `scope-check`0 sin avisos;
lentesA/B/D automáticas y C explícita por autoridad del registro sintético.
Actores independientes del productor, con contexto previo ajeno declarado:
A `audit_t17`, B `audit_t10_container_runtime`, C `debug_t09_native_clock_precision`,
D `design_t09_autonomous_observability`. Prompts literales y B con persona
backend; no se afirma modelo real por la metadata de tier.

A/B/C ya devolvieron FINAL sin defectos de sus lentes. Cotejaron las16 fuentes
y los conjuntos nuevos600/599, distinguiendo learned real, fixtures y pins
declarados de una imagen ejecutada. No ejecutaron pruebas ni probes. D sigue
activa; no hay fusión final ni aceptación. QA técnica independiente preparada,
sin ejecutar, con dos conjuntos actuales y fuentes congeladas. No se fabricará
un resultado Playwright a partir de JUnit; E2E/Docker y T-05 completa pendientes.

D ya devolvió FINAL sin hallazgos de rendimiento introducidos; cotejó16/16
fuentes y los conjuntos600/599. Root volvió a comprobar las16 fuentes y
fusionó las cuatro lentes: cero Critical/Important/Minor, en
`t05-synthetic-compatibility-review1/root-adjudication.json`. Aún no hay
aceptación: QA independiente `design_t09_benchmark`, sin participación en
producir o revisar el código, reutiliza contexto de metodología declarado.
Ownership de producto vacío; nuevo namespace técnico. Ventana liberada tras
terminales reales del cliente para colección y dos ejecuciones nuevas exactas
funcional600/cobertura599. No sustituye E2E ni cierra la tarea completa.

Fix1 cliente: productor confirma nueva verificación final219PASS/13 suites,
sin skips/unhandled, lint-final0 y TypeScript-final0. El resultado anterior
con lint de fixture rojo sigue separado. Las regresiones cubren cuatro gaps,
y distinguen revocación204 de credencial ya inválida401. No usa la respuesta
401 como confirmación de DELETE ejecutado. Los procesos ya son terminales;
entrega sellada y revisión2 pendientes de verificación Root.

Root verificó fix1 físico:119 archivos originales, ocho fuentes actuales
idénticas a los bytes anteriores de la última ejecución219PASS/13 suites,
42 protegidos y ocho preimágenes. Lint-final y TypeScript-final terminal0.
LCOV oficial de cuatro módulos completos94,06–97,75 % combinado, exclusiones
vacías. Los resultados219previos y el lint de fixture rojo permanecen separados.
Revisión2 preparada con diff completo original→final, scope0sin avisos,
tabla anterior y cuatro gaps conservados. A/B se han despachado al mismo
revisor de cada lente; C/D esperan slots. No se reinicia el contador ni se
declara el componente aceptado antes de la nueva revisión y QA.

QA independiente T05 funcional600 sin traza: actor confirmó terminal real0,
UTC11:53:10–11:55:47,600PASS/0failure/error/skip, orden/casos exactos y fuentes
16/116/protegidas36/herramientas8126 sin drift. Cobertura599 independiente
todavía pendiente. Root debe verificar el paquete completo; no hay QAverde
global ni aceptación por esta primera fase.

QA T05 cobertura599 terminó REALexit1/direct_wait, UTC11:56:04–12:00:41:
598PASS/1FAIL/0error/skip, una deselection declarada801. Falló
`test_dispatcher_recovery.py::test_absent_zero_cursor_resubmits_same_frozen_id`:
tras `asyncio.sleep(0.35)` falló `len(backend.posts) == 1`; el contador exacto
no figura en la aserción plain. Se conserva QA_RED
aunque los ocho porcentajes completos superen80. No retake ni etiqueta flaky.
El productor abre diagnóstico readonly separado para distinguir comportamiento
de recuperación y scheduling/tracing, sin cambiar0,35s/aserciones ni ejecutar
otra suite. Root debe esperar el paqueteQA rojo y aprobar la observación causal.

## Revisión de dos lentes — intento 2: T-06, cliente fetch

Cuatro FINAL reales; CLIENT01–04 corregidos por lectura/evidenciaactual219.
A/C sin gaps nuevos. B aporta CLIENT-05 Important: primera401 en quinto
intento sale por `continue` sin halt/cierre, dejando connecting. D aporta
CLIENT-06 Important: una promesa de interrupción pendiente reutilizada por
chunk acumula reacciones O(chunks);64KiB fragmentados byte a byte implican
65.536 registros. No se midieron heap/GC/latencia; Root corrobora el recorrido,
pero exige RED causal antes del fix. Fusión en
`t06-fetch-client-review2/root-adjudication.json`, no limpia/aceptada.

Fix2overall liberado dentro mismos8owned, con ocho preimágenes y42protegidas
nuevas en `t06-fetch-client-review2-fix1`. Conserva los cuatro fixesprevios,
máximo5intentos/renovación acotada y garantías de timeout/cleanupUNKNOWN.
FocalesTDD permitidos tras terminalQA; fullweb/V8/lint/tsc necesita nueva
ventanaRoot trascausalGREEN. Próxima revisión será intento3, no reiniciar
contador. Endpoint, allwriters, Docker, navegador y cierre T-06 pendientes.

Fix2overall productor reporta RED05 con dos secuencias de401 final que dejaban
connecting, y RED06 determinista: un frame64KiB válido fragmentado byte a
byte registró65.537 `.then` en la misma promesa pendiente (esperado máximo1).
Se observa registro de reacciones, no heap/GC. GREEN05/06 posterior3PASS y
los cuatro archivos focales91PASS/0skip/unhandled, manteniendoCLIENT01–04.
Guard de último intento precede renovación; espera de abort por lectura con
listener retirado enfinally. Fullweb esperado222 todavía no ejecutado.

Root verificó el reciboQA rojo y los JUnits:600 funcionales correctos y598/599
instrumentados con una failure. Fuente116 antes/después/current coincide,
protegidas36 y mapa de herramientas8126 exactos; sus timestamps de metadata
son distintos y no se comparan como si fueran bytes de herramientas. No se
rehashó el inventario completo para declarar aceptación, que sigue denegada.
El assert plain sólo prueba `len(posts)!=1`; se retira cualquier inferencia
de contador0. Una observación causal pasante del caso exacto fue autorizada
tras liberar focalesNode:2048registros acotados, mismos0,35s/aserciones,
timestamps de etapas/caller/nativo y contador enclose-entry con desfase
declarado frente al assert. No producto/parche/fullsuite ni QAverde porfocal.

Observación ACK autorizada REALterminal0/direct_wait PID10140,
UTC12:11:30–12:11:37:un casoPASS,171registros/overflow0/restored. Productor
reporta relativo al retorno de start:ConfirmedAbsent0,0829s,safe_absenttrue
0,0835s,preflightResolved0,1024s,capturatrue0,1249s,POST0,1297s;close-entry
0,3729s registróposts1/native0. Los intervalos son anidados y no se suman;
CPUWindows cuantizado no acredita duración exclusiva de cada etapa.
Ese focal no reprodujo el fallo histórico ni prueba que lo causara tracing.
QA_RED sigue vigente; se exige hipótesis de contexto y reproducción mínima
antes de cambiar producto/timers o repetir suite completa.

Tras ese terminal, Root libera una verificación cliente completa222 casos
(219previos+2variantes05+1contador06), V8 cuatro módulos completos, lint y
TypeScript sobre bytes finales. No se ejecuta otro diagnóstico temporal
backend mientras esa ventana. Revisión3 todavía pendiente y no hay cierre.

## T-06 — Verificación final del segundo ajuste del cliente

2026-10-09: productor terminó una ejecución completa de222 casos,13 suites,
cero failures/errors/skips; lint y TypeScript gestionado exit0. Root comprobó
el recibo contra el FINAL real de collaboration,63 archivos del inventario,
ocho fuentes actuales idénticas a las anteriores al run,42 protegidos y ocho
preimágenes. LCOV oficial completo y sin exclusiones: parser97,53%,
reducer97,75%, session94,09% y events94,63% combinando líneas y ramas por
archivo. No se suman focales ni porcentajes de ejecuciones anteriores.

Revisión3 de3 preparada con diff completo original→final de ocho archivos,
scope0 sin avisos y lentes A/B/C/D. A/B despachadas; C/D esperan slots.
CLIENT01–04 y los veredictos anteriores se conservan; se reevalúan CLIENT05/06
sin reiniciar contador. [Comprobación Root](../../../.cache/dev-cycle/m1/t06-fetch-client-review2-fix1/root-delivery-verification.json).
QA independiente, HTTP, todos los escritores, Docker y navegador pendientes;
esta ejecución no cierra T-06 ni M1.

T-05: liberada una observación contextual de11 casos, últimos diez anteriores
del orden de QA más el caso de recuperación, instrumentando sólo este último.
Conserva0,35s/aserciones y GC pasivo sin cambiar su política. Inicio real
12:20:05UTC,handle23425/PID30024; no es resultado terminal ni retake completo.
El focal previoPASS no explica el fallo de QA, que sigue abierto.

## Revisión de dos lentes — intento 3: T-06, cliente fetch

A/B/C/D nativas terminaron sin gaps nuevos ni pendientes; lectura estática
y cotejo propio, no QA ejecutada por revisores. Contextos existentes reutilizados
e independientes del productor, no se afirma contexto vacío literal.

| # | Grado original | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| CLIENT-01 | Important | Cursor antiguo tras callback reentrante | T-06 | Corregido, disposición conservada | Revision guard tras callback en reducer. |
| CLIENT-02 | Important | Cleanup bloqueante | T-06 | Corregido bajo UNKNOWN/halt | Espera2s, retención del recurso y primera causa, no reapertura automática. |
| CLIENT-03 | Important | Snapshot confirmado sin consumidor | T-06 | Corregido | Consumidor obligatorio antes de I/O. |
| CLIENT-04 | Important | Navegación agota sesiones | T-06 | Corregido | Un owner, DELETE acotado con204/401/unknown distintos. |
| CLIENT-05 | Important | Último401 deja connecting | T-06 | Corregido | Halt antes de renew; RED dos variantes y GREEN actuales. |
| CLIENT-06 | Important | Reacciones O(chunks) | T-06 | Corregido | Waiter por lectura; RED65.537/GREEN≤1 por waiter, sin claim heap/GC. |

[Informe](testing/t06/client-review3.md). Diff original→final8, scope0sin
avisos y selectorC/Dautomático. RawFINAL4 y fusión preservados. Root libera
QA técnica independiente222V8/lint/tsc en namespace nuevo; no instalación,
GPU ni servicios. Cache del wrapper aislada sólo en instancia privada verificada,
sin editar producto. T-06 no cerrada, HTTP/Docker/E2E pendientes. Jira desactivado.

T-05 contextual11 terminó exit0/direct_wait12:20:14UTC,11PASS,190eventos
overflow0/restored. Root verificóJUnit/colecciónexacta/fuente116/protegidas36
actuales. No reprodujo QAroja ni descarta214casos anteriores/carga histórica.
POST0,0893s en este contexto; GCpasivo acotado sin política modificada.
Hashes de descriptorraw y bindingvalidado son dominios distintos; su desigualdad
no acredita drift. QA_RED se conserva; diagnóstico siguiente sólo preparación
readonly mientras QAcliente ejecuta.

## T-06 — Cliente fetch aceptado técnicamente tras QA independiente

2026-10-09: QA nativa independiente REALterminal0, fullV8/lint/tsc exit0;
222PASS/13suites sin failures/errors/skips. Root verificó FINAL/recibo e
inventario2428 completo, fuentes8/protegidas42 incl9tests ajenos/tools2935/
configs15/originales133 exactos. LCOV oficial completo por archivo97,53 /
97,75 /94,09 /94,63%, exclusiones vacías, sin unión histórica.

[Informe y aceptación](testing/t06/client-independent-qa1.md). Componente
fetch/parser/reducer/session aceptado, revisión3 A/B/C/D limpia; contextoQA
arquitectónico reutilizado independiente del productor/lentes declarado.
No gatePlaywright fabricado ni rutaHTTP/WAL/allwriters/browser/Docker
acreditados. T-06 sigue en-progreso y conserva sus CA/Verificación completas.

VentanaQA terminada y liberada para UNA observación diagnóstica T05 con
prefijo225, tras colección599/import15files, misma traza8 y0,35s. Preflight
sentinelPEP669 localLINE terminal0 conserva identidad del tracer y restaura
slot; no pruebaproducto. Contadorbeforeassert bounded, sin locals ni cambiar
sleep/asserts. Inicio real12:32:08UTC,handle65446/PID22468; esperar terminal.
No nueva suite completa ni fix justificado todavía.

T05 prefijo225 diagnóstico REALterminal0/direct_wait12:33:20UTC,
225PASS/375deselect diagnósticas (374 posteriores+801), colección599/import15
antes de selección exacta. Root cotejóJUnit225/selecciónactual/fuente116/
protegidas36 y179registros overflow0/restored, slotmonitorlibre trasfinal.
Contadorbeforeassert real:posts1/native0 a0,3628s desde start-return;
POST0,0786s. No reproduceQAroja ni prueba causa histórica; no suite completa,
fix o relajación de deadline acreditados. Lectura independiente del contrato
evalúa si0,35s es requisito o una espera fija del fixture; producto intacto.

Auditoría documental independiente confirmó que specCA09/ADR0018/0043 no
garantizan POST antes de350ms. `poll_s=0.1` no es latencia máxima;
`control_s=30` limita cada operación, no la recuperación global. Root autoriza
UNA reproducción privada controlada con status legítimo pendiente más de0,35s
y menos del presupuesto operativo, checkpoint temprano y posterior submit
real observado, manteniendo request/ordinal/JobAttempt/cierre. Demostrará, si
pasa, el mismatch entre espera fija y comportamiento; no la causa histórica.
No modificación del test ni retake completo antes de prueba y decisión.

## T-05 — Corrección acotada de sincronización de la fixture

La pareja causal privada terminó REALexit1/direct_wait: una failure esperada
de la copia original y un PASS del candidato. Ambas observaron posts0/status
pendiente en el checkpoint temprano con demora legítima0,45s; el candidato
esperó el submit real y conservó las cuatro aserciones/SQL, cerrando native0.
Root comprobóJUnit/counters/fuentes116/protegidas36. Se prueba el mismatch
controlado de la espera fija; la causa histórica de QA599 sigue desconocida.

[ADR-0066](../../decisiones/ADR-0066-sincronizacion-con-el-submit-real-en-prueba-de-recuperacion.md)
adopta observar el submit real con timeout finito de prueba; actualiza sólo
esa excepción en ADR0062. Root preparó unidad privada nueva con16preimágenes,
51protegidos y formas de los tres tests originales. OWNED exclusivamente
`apps/server/tests/test_dispatcher_recovery.py`: sincronización del caso
original y UNA regresión de status retrasado. No cambios de runtime/SQL ni
de las cuatro aserciones, firmas, decoradores u otros timers. RegresiónRED
contra el test canónico antes del fix, GREEN y vecinos después; fullsuite
todavía no liberada. Conjuntos esperados601 funcionales/600 instrumentados,
sin nuevo skip/xfail/exclusión; parámetro801 conserva10s y políticaADR0064.

Readiness de ejecuciónCPU real recibida/verificada:55fuentes actuales y59
artefactos exactos, sin drift ni tests. Scope propuesto child/FFmpeg/paquetes/
publicación por toma, después runtimeCPU2/beats/Analysis/Docker. No implementación
liberada por este informe. AuditoríaSQL confirma que QA2 posterior también
fue FAILED por801 y que no hay defectoDDL demostrado que justifique reescribir
tablas; se requiere verificación actual completa antes de aceptar ese scope.

RED: `test_absent_zero_cursor_waits_for_real_submit_with_delayed_status`
falló con `AssertionError: Lost ACK did not reconcile frozen attempt` al
invocar el caso canónico aún con sleep0,35s · 2026-10-09. PID23836/direct_wait
exit1, JUnit1failure/0error, UTC12:51:40–12:51:47. Root cotejó que la función
original completa era AST-idéntica a la preimagen en el RED. No error de
import/colección usado como RED; warning inicial de tempdir separado. El
productor aplica después la sincronización mínima; GREEN todavía pendiente.

GREEN posterior REALexit0: nueva regresión1PASS y módulo de recuperación
completo12PASS/0failure/error. Root cotejó cuatro aserciones, firmas y
decoradores originales exactos; los otros dos tests completos conservan AST.
Sólo el archivo de fixture cambia. Ruffcheck/formatcheck finales0; el primer
formatcheck1 de firma nueva se conserva como formato, no RED de producto.

Root libera UNA suite601 funcional sin tracing y600 con cobertura oficial8,
tras congelar fuentes y comprobar colección/orden. Exclusión instrumentada
únicamente80110s/ADR64; sin excluir código/añadir skips ni combinar resultados.
Revisión2 del componente sintético más fixture y QA independiente siguen
pendientes; fullsuite no se da por verde al despacharla.

Colecciones actuales601/600 terminaron exit0: al retirar la regresión nueva
se restauran IDs y orden de los conjuntos históricos600/599. Sólo801 se
omite de instrumentación. Funcional601NONE inició REAL12:58:02UTC,
handle53848/PID32728, fuentes16/source116/protected51/tools8126 verificadas
antes de Popen. Cobertura600 todavía no iniciada; esperar el mismo handle
sin reiniciar por timeout de observación. No otro runner durante la ventana.

Funcional601NONE REALterminal0/direct_wait13:00:38UTC,601PASS. Cobertura600
REALterminal0/direct_wait13:06:39UTC,600PASS; ambas únicas ejecuciones nuevas.
Root verificó2677raw/16fuentes/116freeze/51protegidas/16preimágenes/8126tools,
JUnit/colección/omisiónexact801. WHOLE8 combinado83,52–97,26% y cero código
excluido. Un KeyError del verificador Root al asumir collection.actual se
corrigió leyendo el campo real selected_nodeids; no fue fallo de producto
ni retake de tests. [Comprobación](../../../.cache/dev-cycle/m1/t05-recovery-submit-sync-fix1/root-delivery-verification.json).

Revisión2 preparada con diff completo16original→final y scope0sinavisos,
selectorA/B/C/D y personaB real. A/B despachadas, contextos existentes
independientes del productor declarados; no aprobación porverde ni cierre.
QA independiente posterior y alcanceSQL/Docker/publicaciónreal pendientes.

[ADR-0067](../../decisiones/ADR-0067-verificacion-vigente-del-esquema-sql-con-suite-completa.md)
adopta la nueva verificaciónSQL completa32suites1056funcional/1055instrumentada
con la misma única omisión801 y sus controles funcionales íntegros. No afirma
calibración causal específica sourceSQL4 ni aceptación por SHA. Plan/artefactos
verificados con1055IDs originales en orden y cuatro fuentesSQLactuales; se
preparaQA en namespace nuevo, sin runners liberados. Tres skips originales
requieren sus mismos casos Linux actuales; QA antigua no los acredita por sí sola.

## Revisión de dos lentes — intento 2: T-05, compatibilidad sintética y fixture

A/B/C/D FINAL reales: cero Critical/Important/Minor nuevos o pendientes.
Quince archivos conservan su SHA de revisión1, incluidos los seis runtime;
se reevalúa sólo el fixture de recuperación y su nueva regresión. A1/B1/C1/D1
aprobados se conservan; B1 tabla literal ausente se declara, no se reconstruye.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A/B/C/D | — | Ninguno nuevo | T-05 | Sin correcciones pendientes de revisión | 16SHA/freeze, lectura completa del diff y RAWFINAL4. |

[Informe](testing/t05/synthetic-compatibility-review2.md). Scope0sinavisos,
selectorC/Dauto, personaB real, fuente congelada. Reutilización independiente
de contextos nativos declarada; no tests ejecutados por revisores. No cierre
T-05 ni aceptación del componente antes de QA. Jira desactivado.

QA2 nativa independiente prepara y verifica nuevas colecciones601/600 exactas,
ambas terminal0, una omisióninstrumentada801. Fuentes16/116/protected51/
tools8126 coinciden antes/después. Funcional601NONE inició REAL13:23:09UTC,
handle84612/PID19324; esperar ese mismo proceso, sin reiniciar por observación
expirada. Cobertura600 sigue pendiente. SQLQA3 permanece preparada sinrunners;
no carga temporal adicional durante la ventanaQA2.

QA2 funcional601NONE REALterminal0/direct_wait13:26:05UTC:601PASS, cero
failures/errors/skips y fases setup/call/teardown correctas. Fuentes16/116,
51protegidas y8126tools antes/después exactas; no repetición de esa suite.
Coverage600 oficial inició REAL13:26:22UTC, handle9458/PID33164, en ventana
exclusiva. Esperar ese mismo handle; porcentaje o tiempo no prueban terminal.

PreparaciónSQL: Root detectó que los comandos previstos no fijaban rootdir
ni ini de colección. El pytest instalado encuentra pyproject.toml del repo
por ancestros, por lo que CWDinputs no acredita IDs relativos esperados.
ActorQA3 revisa ese arnés privado antes de ejecutar; preserva originales
sellados y no cambia fuentes/tests ni sus expectativas. No colección/run
SQL todavía, ni inferencia de fallo del producto por esta preparación.

## T-05 — Compatibilidad sintética aceptada técnicamente tras QA2

QA2 cobertura600 REALterminal0/direct_wait13:30:10UTC,600PASS y omisiónexact801;
funcional601 previa igualmenteverde. Root cotejó1870raw/16current/116freeze/
51protected/8126tools y ocho módulos completos83,52–97,26% combinado,
sin código excluido. [Informe y aceptación](testing/t05/synthetic-compatibility-independent-qa2.md).
Revisión2 A/B/C/D limpia y QA independiente; componente técnico aceptado.
QA1 roja/historiacausaUNKNOWN preservadas. T-05 sigue en-progreso; no WAV,
Docker/E2E, SQLintegral ni cierre universalOS acreditados por este componente.

QA3SQL preflightSourceGuard/Ini terminal0 y colecciones1056/1055 exactas tras
amendment2 privado. Primer intento de colección falló antes de importpytest
por un argv rootdir/-c/ini serializado como un token; se preservó y corrigió
la lista de tres tokens, sin relajar guardas ni reescribir IDs o expectativas.
Handle70024 TERMINAL0 recogido, casos ejecutados0 en colección; no gate de
cobertura por collect-only. Root libera UNAfuncional1056NONE seguida sólo si
verde por UNAcoverage1055sourceSQL4 bajoADR67. Tres skips Windows originales
requieren el suplementoLinux posterior. No Docker/GPU ni otro runner durante
esta ventana; no aceptaciónSQL anticipada.

QA3 funcional1056NONE inició proceso REALhandle90240/PID7196,
`full-functional1056-none/active.json`; Root observó ese PID Python vivo.
Argumentos rootdir/-c/ini ya separados y efectivos, sin pytest_cov ni
deselect; guardas116/SQL4/134mirrors/protected51/tools8126 exactas antes.
Esperar ese mismo handle; cobertura y suplementoLinux no iniciados. No
resultadofuncional por intención ni aceptaciónSQL antes de sus verificaciones.

QA3 funcional1056 REALterminalexit1/direct_waithandle90240:1026PASS27FAIL,
0ERROR y3SKIP exactos. Treinta y dos suites/IDs/orden sin deselect yguardas
116/SQL4/134mirrors/protected51/tools8126 beforeafter coinciden. Cobertura y
Linux no iniciados. Se conserva el resultado rojo completo y no se suman
verdes anteriores para aceptarSQL.

Fallos:25 en dispatcher_scanning, uno en
`test_queue_manual_retry_never_replaces_uncertain_prepared_attempt` y otro en
`test_existing_init_env_generates_once`. Original801 y regresión de estado
retrasado no están en la lista fallida. QA realiza clasificaciónreadonly;
dos revisores independientes examinan scanning y los otros dos casos.
Ningún fix de runtime, fixture, recurso o expectativa autorizado todavía:
hipótesis y evidencia exactas antes de ampliar ownership o repetir suites.

## T-05 — Diagnóstico causal focal tras SQL QA3

2026-10-09: las dos revisiones independientes readonly entregaron sus informes
en `.cache/dev-cycle/m1/t05-scanning-qa3-failure-review1/report.md` y
`.cache/dev-cycle/m1/t05-other-qa3-failure-review1/report.md`. No probaron aún
causalidad experimental: el registro sintético compartido, ACK/residencia del
doble y el recurso `scripts/init_env.py` ausente son hipótesis contrastables.
El caso de identidad cambiada conserva su rechazo y exige decisión contractual;
no se autoriza la identidad `changed` ni se mueve la inyección negativa.

Root libera exclusivamente probes CPU focales privados en
`.cache/dev-cycle/m1/t05-qa3-causal-probes1`, a cargo de
`design_t05_actual_cpu_worker`, ahora diagnóstico y no QA independiente de su
futura corrección. Reproducción original antes de prototipo, comandos/JUnit y
fuentes antes/después; copia nueva, QA3 intacta, ningún cambio canónico todavía.
`audit_t17` examina sólo el contrato de drift en otra carpeta privada readonly.
Contextos reutilizados declarados; datos efectivos de modelo/tokens/coste/horas
desconocidos. Sin fullsuite/cobertura/GPU/Docker/servicios ni cambio de estado
de la tarea. TDD n/a: adjudicación y prototipos diagnósticos; no se afirma un
RED funcional por el FileNotFoundError de preparación.

Root verificó los cuatro primeros focales en
`t05-qa3-causal-probes1/root-first-four-probes-verification.json`: manual RED
exit1 `Selected provenance mismatch` y prototipo GREEN1 exit0 con sólo el
keyword del registro; token RED exit1 por recurso ausente y GREEN1 exit0 con
script exacto SHA21a3 y test intacto. Cada JUnit contiene un caso;116 fuentes
antes/después iguales. Las dos hipótesis concretas quedan confirmadas, sin
aceptación del conjunto ni cambio canónico mientras continúa el aislamiento
scanning/identity. El token RED acredita preparación, no RED funcional TDD.

## T-05 — Fix canónico tras causa probada; ADR-0068

Los focales scanning válidos confirman: registro compartido supera selección
y alcanza ACK ausente; ACK/residente coherentes pasan el assert original.
El caso identity conserva el fallo con exactamente dos Health1→changed,
sin intento. Root verifica nueve focales y34 firmas/decoradores/aserciones
originales; el primer prototipo A mal cableado se excluye de causalidad.
Recibo diagnóstico SHA08dc3dd602f6888ba712a4835cfde1d4a80b74fa03bb2dc8998bddbe61049ca0.

Root adopta [ADR-0068](../../decisiones/ADR-0068-descarte-de-identidad-obsoleta-antes-de-procedencia.md):
comparar la misma identidad fresca antes de construir procedencia, descartar
sólo drift acreditado sin autoridad y conservar errores explícitos de inputs.
Actor nuevo `implement_t05_qa3_fix1`, contexto sin historial, recibe brief
oficial completo (aviso de exceso preexistente conservado) y ownership de
resolver/dispatcher, dos fixtures y test nuevo específico. Preimágenes4,
freeze116 y112protegidas en `t05-qa3-fix1/root-handoff-release.json`.
Archivos adicionales necesarios: ADR0068, índice de decisiones y
`docs/arquitectura/sistema.md`; nuevo test
`apps/server/tests/test_dispatcher_identity_drift.py`.

RED funcional antes de runtime, focales y diff mínimo; ningún nuevo
full1056/cobertura/full91 antes del release posterior. No cambio SQL,
synthetic_registry, helpers ajenos, asserts/plazos/querybounds ni confianza
por catálogo. Revisión y QA independiente pendientes; estados T05/M1 y
objetivo íntegro M0–M5 conservados. Tokens/modelo/coste/horas reales desconocidos.

RED: `apps/server/tests/test_dispatcher_identity_drift.py::test_identity_drift_before_selected_provenance[True]`
falló con `ResolutionError: Invalid immutable engine request`, resolver344,
exit1 ·2026-10-09T14:11:36–14:11:38UTC. Root leyó comando, salida y test nuevo
con composición declarada y prohibición de lease/reserve/load/submit.
Originales en `t05-qa3-fix1/identity-red/`. No se atribuye SourceGuard al
runner de este RED; no es la QA definitiva ni se acepta sólo por este fallo.

[Informe del diagnóstico causal](testing/t05/qa3-causal-diagnosis.md) publicado,
dos enlaces relativos comprobados. La corrección canónica continúa en los
cinco archivos asignados; Root conserva estados y gates pendientes.

Productor reporta drift explícito/automático2PASS y focales originales12PASS;
controles posteriores16PASS y otras carreras32PASS se solapan, no se suman
como suite conjunta. Nueva prueba también detectó referencias de backend/origen
mutables: RED previo a capturar contexto de ruta inmutable, dentro de los
mismos archivos. Root conserva evidencia en `binding-red/` y debe adjudicarla
con la entrega final. Productor declara112protegidas y34shapes intactas yRuff0.

Root libera UNA verificación vecina funcional de scanning91, reintento manual
y test nuevo completo después de controles verdes. Observó procesosPython
reales33188/25336 con pytest y padres28712/33024 del runner en
`t05-qa3-fix1/neighbors-once/`; no resultado anticipado ni retake por timeout.
Preparador independiente `design_t09_autonomous_observability` sólo redacta
adaptación QA4 en carpeta privada:33suites preservando1056IDs y sumando las
regresiones nuevas, recurso init_env y cobertura WHOLE6(SQL4+runtime2).
No ejecuta collect/tests ni congela código en edición. QA4 completa espera
entrega y revisión; Linux tres casos después, nunca aceptación por receta.

Vecinos terminal exit0:132PASS0FAIL0SKIP,78.30s, scanning91/manual33/nuevo8.
Root verificó JUnit/comando, cinco fuentes actuales,112protegidas y34shapes
intactas en `t05-qa3-fix1/root-focal-delivery-verification.json`. FINAL nativo
real preservado; recibo SHA0d7c5ebad4b1b8c0c066d87484c562b19cda121b1f07ab1f8b211dd6f54893b1.
Inventario1601 pendiente de cotejo profundo fuera de ventanas temporales;
no se afirma aceptación de componente ni SourceGuard antes del primer RED.

Root libera suplemento de cobertura prerevisión, sólo privado y sin nuevas
ediciones canónicas: UNA medición oficial de resolver/dispatcher completos,
33suites actuales y sólo801 excluido de instrumentación bajoADR64/67.
Los ocho casos nuevos permanecen incluidos. No fullNONE nuevo ni retake;
WHOLEcada2 debe alcanzar80% combinado sin excluir código. Artefactos originales
del fix se conservan, suplemento en `coverage-supplement1/`. Esta medición del
productor no sustituye la posterior QA independiente33suites/WHOLE6/Linux3.
QA4 plan propuesto entregado sin ejecución en
`t05-current-sql-independent-qa4-preparation/plan.md`; revisar sólo tras
freeze/entrega/revisión. Objetivo completo activo, sin cierre T05/M1.

Suplemento1 cobertura terminó PID31784 exit3 **antes de ejecutar tests**:
assert de colección; `-c` privado sin rootdir explícito. La traza sólo de
imports no mide el gate. Originales íntegros. Root autoriza nuevo suplemento2
con rootdir checkout y config separada: collect-only guarda IDs/config antes
del assert y verifica1056originales en orden más8nuevos, excluyendo sólo801
instrumental. Únicamente después del preflight exacto permite UNA medición
real con mismas fuentes. Sin normalizar IDs, retake de tests verdes ni
arreglo de runtime por un fallo del arnés. Causa de prefijos exige datos;
si preflight vuelve rojo, no ejecutar tests y devolver diferencias.

Suplemento2 preflight collect-only PID31264 exit0: rootdir checkout e
inipath privado explícitos;1064IDs originales1056+nuevos8 en orden, sólo
801deselect→1063seleccionados. Actor inicia medición única PID33604,
session81991; Root observa ese PID Python real con `coverage run` a14:24UTC.
Mismas5fuentes/112protegidas pre-run. Esperar el mismo proceso/handle,
sin otra carga pesada ni retake por observación expirada. Cero resultado
de cobertura anticipado; suplemento1 fallido no se usa como gate.

Medición suplemento2 REALterminal1 PID33604/session81991:1056PASS4FAIL3SKIP,
1exact801deselect,476.14s. WHOLE oficial completo:dispatcher86,8421%,
resolver89,6947%, cero exclusiones. La cobertura numérica no acepta el gate
rojo ni fuentes posteriores. Dos FAIL son regresiones del filtro de backend
antes de `_catalog`: observaciones busy1 en vez de2, no timeout.
Settings falla por fixture demasiado profunda (siete padres coinciden con
ROOT, ruta permitida); el cuarto fallo snapshot artwork258 sigue pendiente
de contraste independiente. No se amplían excepciones temporales.

Root libera fix2 exclusivamente resolver, preimagen actual+116protegidas en
`t05-qa3-positive-observation-fix2`. Contexto restringe selección, preserva
las observaciones frescas previas de otros backends, ADR0068 aclarado. Actor
diagnóstico nuevo `diagnose_t05_snapshot_reconcile` sólo privado ejecutó un
focal original artwork SINTRACING:1FAIL, mismo assert258; lectura de DB/JSON
posterior, ninguna edición snapshot/schema y ningún rerun sin autorización.

RED: original `test_global_busy_gpu_negative_once_and_available_cpu_native[200]`
falló assert1520 positivo/contadores, SINTRACING, PID28028 exit1,1,53s,
deadline10s intacto; resolver aún0682e2f antes del fix. Originales en
`t05-qa3-positive-observation-fix2/original200-functional-red/`.
Intento previo33696 falló preparación parentqueue inexistente; preservado,
no cuenta como TDD. Root espera diff/focales verdes, no fullsuite ni cobertura
nueva liberados todavía. Revisión/QA4/Linux/T05 pendientes.

Fix2 terminal: delta sólo resolver, filtro de selección después de catálogo
fresco. GREEN12PASS0FAIL0SKIP,6,41s(originales200/400,identidad8,ASGIbusyCPU2),
Ruff/formato0 y116protegidas exactas. Resolver actual SHA867fbae20206eb95a402ee461a1b6271f0a4108f37468287f421271c112e8622.
Inventario648 y recibo en `t05-qa3-positive-observation-fix2`; pendiente cotejo
profundo Root. Los132PASS del fix anterior y la cobertura2 anterior son
históricos respecto de este nuevo resolver; no se mezclan para aceptar.

Diagnóstico independiente artwork phase3 confirmado: el MISMO JSON leído
UTF8 coincide con `project` completo; lectura cp1252 difiere en nombres
acentuados. DB/JSON originales/focal sin cambios. QA3 fijaba PYTHONUTF8=1,
suplemento2 omitió ese override; valor heredado histórico UNKNOWN. No hay
evidencia de defecto de snapshots: no cambiar writer ni aserciones.
Root libera confirmación barata en nueva `t05-qa3-prep-corrections-proof1`:
una ejecución de artwork/settings intactos, PYTHONUTF8=1 antes del proceso
y tmpfixture a profundidad equivalente QA3, cuyo séptimo padre está fuera
deROOT. Prosa/config sin TDD funcional; no fullsuite/cov ni snapshotscodefix.
Entrega/gate global aún pendientes, sin declaración de fase4 completa.

Confirmación preparación terminal PID10520 exit0:2PASS,1,43s, dos tests
originales sin edits ni retakes. UTF8mode1 antespytest yséptimo padre fuera
deROOT;117fuentes actuales antes/después iguales. Root cotejó ambos JUnits
(fix12/prep2) y los5SHA actuales; ningún snapshots/settingscodefix.

Root libera nueva medición prerevisión con materialfix probado, sin cambios
canónicos, en `t05-qa3-fixed-coverage3/root-release.json`: mismas33suites y
1064originales+nuevos, sólo801instrumentalomitido, branchWHOLE2 actual sin
excluir código. CollectPID32176 exit0 exactorder1064/1063selected/new8;
UTF8mode1/tmpRootQ3-depth preflight verdadero. Medición session48979/PID13012
iniciada una vez yobservada viva por Root14:46UTC. No resultado anticipado,
no heavy/timed paralelo ni nuevofullNONE; esperar ese mismo handle. Config
revisión1 preparada apuntando actualdelivery5 conpreimages originales, aún
NOejecutada. QA4indep/WHOLE6/Linux3/T05/M0–M5 siguen pendientes/activos.

Medición corregida session48979/PID13012 REALterminal0:1060PASS0FAIL0ERROR,
3WindowsSKIP exactos y1exact801deselect,455,93s. Root cotejó JUnit/colección,
cinco SHA actuales ybeforeafterprotegidas; WHOLE2actual completo
dispatcher86,8421%/resolver89,6947%, cero código excluido. Evidencia en
`t05-qa3-fixed-coverage3/root-measurement-verification.json` yFINAL nativo
real preservado; recibo SHA7ffdc55291d4cb17fed88c7139edb08f6baf4926e9ad675978f892b9a1c48cdd.

PreparadorRoot verificó inventario2567/fuentes5/preimágenes originales y
scope0sinavisos en `t05-qa3-fix1-review1`. SelectorDtrue/Cfalse; Root añade
C por cambio del orden de autoridad/identidad, sin alterar configuración.
Revisión adversarial intento1 de este delta nuevo: actores nuevos sinhistorial
`review_t05_identity_a1`, `review_t05_identity_b1`, `review_t05_identity_c1`
despachados con prompts literalesreadonlystatic. D espera plaza disponible
(máximo tres revisores simultáneos). Modelo efectivo/tokens/coste/horas UNKNOWN;
tiers configurados no se presentan como ejecución real. Ningún writer de
producto durante revisión. No aceptaciónT05/SQL6/fullNONE801/Linux anticipada.

## Revisión de dos lentes — intento 1: identidad tras routing

Cuatro FINAL nativos nuevos preservados en `t05-qa3-fix1-review1/final-{a,b,c,d}.md`.
A/C/D0hallazgos; B1Important: membership de backend sólo se coteja antes de
await_catalog de otro backend. Sustitución del seleccionado conservando
tamaño puede omitir al reemplazo y terminar en ResolutionError en lugar de
StaleRoute/invalidation; el modo automático también omite invalidación.
Precondición declarada por prueba existente de rebind, sin writer productivo
identificado ni ejecución del escenario por reviewer. Root confirma flujo
estático y exige reproducción funcional, no parche a ciegas. El criterio
nominal A no anula este caso concreto. Fusión0Critical/1Important/0Minor;
`root-adjudication.json` conserva aprobaciones y bloquea aceptación.

| Lente | Veredicto del delta | Evidencia |
|---|---|---|
| A | ✓ conformidad acotada; tarea completa pendiente | `final-a.md` |
| B | ✗ B1 Important | `final-b.md`, resolver219/242/246/399 ydispatcher213 |
| C | ✓ sin hallazgos de seguridad | `final-c.md` |
| D | ✓ sin degradación demostrada;801 pendiente de QA | `final-d.md` |

| Gap | Grado | Tarea | Fichero:línea | Escenario y disposición |
|---|---|---|---|---|
| B1 | Important | T-05 | `apps/server/app/queue/resolver.py:246` | Sustituir seleccionado durante await de catálogo anterior omite invalidación y clasifica error genérico; confirmado estático, reproducción funcional antes de fix, no aceptación ni deuda. |

Root libera fix B1 en `t05-qa3-review-b1-fix3`: ownership resolver y testnuevo,
115protegidas/preimágenes actuales. Actor implementer reutilizado sólo código,
no QA independiente; agrega casos explícito/auto con RED antes runtime,
preserva los ocho previos y TODOS originales. Sin retargeting/autoridad/catch
universal ni nuevas lecturas, plazos o queries. Freshobservations200/400
conservadas. No fullsuite/cobertura nueva hasta Rootrelease. El próximo
intento de revisión será2de3, sin reset ni deuda aceptada. T05 sigueenprogreso,
QA4/SQL6/Linux3/CPUreal/M0–M5 pendientes; coste efectivo UNKNOWN.

RED: nuevo `test_selected_backend_replaced_during_prior_catalog[True/False]`
PID33520 exit1/2FAIL,1,21s ·2026-10-09T15:07UTC. Explícito propaga
ResolutionError yautomático conserva caché; callback sustituye seleccionado
durante segundo Health deotro backend. Root leyó salida ycomando; resolver
SHA867fba previo,115protegidas. Fix B1 confirmado con14PASS0FAIL0SKIP,6,59s;
captura key una vez, cotejo post_catalog normalO1/fallback sólo keycambiada.
Originales yorden intactos; Ruff/formato0. Resolver actual8278f3/15737bytes,
testidentity87975a/8792bytes, dos casos nuevos; cobertura anterior histórica.

Root libera medición apropiada de WHOLE2 actual en
`t05-qa3-b1-current-coverage4`: todas13 suites queue/dispatcher(446originales)
módulo completo identidad(10 actuales), sólo801instrumental omitido.
No sustituye QA4 completa33suites(original1056+10)/WHOLE6/Linux3. Artefactos
actuales5frozen/protected115; ninguna nueva edicióncanónica ni fullNONE.
Primer collectPID32212 exit3/0tests por helper que asumía censusobjeto cuando
era lista de filasnodeid. Root confirmó estructura, autorizaamendment1
preservandohelper/collectfallido y nuevo collect-corrected1 antes deUNA
mediciónreal. No falso TDD/coveragegate por preparación ni normalizaciónIDs.
Revisión siguiente2de3 después de coberturaactual; aprobacionesA/C/D1 se
conservan salvo evidencia nueva, B1 se reevalúa con prueba ejecutada.

C4collect-corrected1 PID27492 terminal0:456IDs, proyección446originalesexacta
y10identity actuales, únicos/old8preserved; sólo801deselect→455. UTF8mode1,
rootdircheckout/iniprivada ytmpoutside preflight0. ÚNICA mediciónreal
session38056/PID33568 iniciada; Rootobserva ese mismo PID Python `coverage run`.
No heavy/timed paralelo ni retakes ni resultado anticipado. Oldcollect
fallido/helpers/code no se sobrescriben; amendment-preflight1 sellada.

C4REALterminal0 session38056/PID33568:455PASS0FAIL0ERROR0SKIP,238,84s,
1exact801instrumentaldeselect. Root coteja JUnit/colección/proyección446,
old8exactorder+dosnuevos/10totales, current5physicalSHA yproteccionesbeforeafter.
WHOLE2actual dispatcher86,8421%/resolver90,0735%, excl0. FINAL nativo actual
preservado enC4, recibo SHAad153f50790f1f3741d0e4d3f9591e887d6bfd21f8fe8fd1dccedc21e80daf55.
Inventario2101/current5/preimágenes originales verificados por preparadorRoot;
scope0sinavisos, selecciónDtrue yC adicional motivadaautoridad en
`t05-qa3-identity-review2`. No uso de cobertura histórica ni aceptaciónT05.

## Revisión de dos lentes — intento 2: pertenencia tras catálogo esperado

Actores nuevos `review_t05_identity_a2`, `review_t05_identity_b2`,
`review_t05_identity_c2` despachados con prompts literales ytraspaso exacto
de final-a/b/c/d1 yroot-adjudication1. Reevalúan B1/resolver/identity nuevos;
aprobacionesA/C/D anteriores se conservan salvo evidencia nueva. D2 espera
plaza (máximo3simultáneos). Source5frozen yningún writer/código mientrasrevisión.
No resultados adelantados ni contadorreiniciado; efectivaidentidadmodelo/
proveedor/tokens/coste/horas UNKNOWN. FullQA4original1056+10/WHOLE6/NONE801/
Linux3 siguenobligatorios, testsubset14 no los sustituye. No cierreT05/goal.

Loscuatro FINAL2 reales guardados en `t05-qa3-identity-review2/final-a/b/c/d.md`.
Root vuelve a cotejarSHA5 actual: A/B/C/D0Critical0Important0Minor,
B1→corregido confirmado porB yA conRED2/GREEN14 yguardpost_catalog;
aprobacionesanterioresconservadas. Rootadjudication2 limpio sin aceptarT05.
C atribuye scope0 a preparadorRoot/assertsubprocess/rawscope.json, recibo
separadodelsubprocess inexistente declarado, no ejecutado/fabricado porreviewer.

ActorQA nuevo independiente `qa_t05_current_sql4`(sin historial/productor/
reviewtarget previo) recibe preparación+preeflight sólo en
`t05-current-sql-independent-qa4/root-release-preparation.json`.
ReutilizaQ3minimal/sourceguardantespytest/producto,actual117+scriptinit_env,
mirror136,SQL4+runtime2 cada80% sinexcluircódigo,33suites originales1056
enorden+identity10 derivadoColección, fullNONEincluyendo801 ycoverage sólo801
omitido. UTF8 explícito child ytmpRootQ3-depth; originales/código intactos.
Fullfuncional/cobertura/Docker/Linux NOliberados aún hasta Rootcotejo de
preparación/preflight real. NoexecUI/E2EfullM1 porestecomponenteserver ni
estadosCAcerrados. ObjetivoM0–M5activo, límitesTCB/primerREDguard/usageUNKNOWN.

**QA4 funcional liberada — 2026-10-09:** Root verificó preparación,
colecciones y sellos actuales; `root-release-full.json` autoriza una pareja
de pruebas. El actor independiente mantiene sesión 7354 y PID 21064 activo.
Último checkpoint: aproximadamente 33 %, sin fallos visibles, sin resultado
final. Funcional: 1.066 casos, incluido 801 sin instrumentación. Sólo tras
resultado limpio comienza cobertura: 1.065 casos, seis módulos completos,
única omisión instrumental 801, cero exclusiones de código. Linux/Docker
siguen sin liberar. Ninguna aceptación anticipada ni cierre de T-05.

**QA4 funcional terminal — 2026-10-09T16:02 UTC:** comando PID 21064 exit 0
mediante wait real, 1.063 PASS/3 SKIP/0 FAIL/0 ERROR, 368,24 s. Root cotejó
JUnit 1.066 casos y original 801 PASS en 2,821 s sin instrumentación.
Resultado del runner: fuentes/copia/config/tools intactos y colección,
rootdir, skips y deselection exactos. Cobertura actual inició PID 28716
a las 16:02:13 UTC, misma sesión 7354; aún sin resultado final. Mantener
exclusividad. Linux y aceptación de SQL/T-05 permanecen pendientes.

**Preparación siguiente unidad real — 2026-10-09:** implementer nuevo
`implement_t05_actual_execution1`, contexto fresco, sólo lectura acotada y
nota privada en `t05-actual-execution-implementation1`. Recibe brief
determinista completo, aviso real de longitud y alcance A/B de ejecución/
publicación WAV/FFmpeg con TDD. Producto, tests, imports, probes y servicios
no liberados mientras QA4 permanece activa. Contratos/modelos/0006/snapshots/
cola/coordinador/locks readonly; Root decide cualquier ampliación exacta.
No sustituye CA Docker/beats/cleanup ni cierra T-05 por preparar la unidad.

**QA4 pareja Windows terminal verificada — 2026-10-09:** funcional 1.063
PASS/3 SKIP y cobertura 1.062 PASS/3 SKIP/único 801 deselectado; exit 0
real en ambas fases, sesión 7354 terminada. Root recalculó JUnit/colecciones/
WHOLE6 y cotejó físicamente Source117/protected112/tools8126/mirror136,
configuraciones y recursos. Por módulo: models 99,1525 %, snapshots
91,4463 %, invariantes CPU 89,7603 %, migración 0006 100 %, dispatcher
86,8421 %, resolver 90,0735 %. Cero exclusiones de código. Extras Alembic
declarados en el resultado oficial. `root-windows-pair-verification.json`.
Root libera sólo preflight Linux en `root-release-linux-preparation.json`;
no pruebas Linux todavía, sin pull/build/install/GPU/red ni servicios.
Preparar imagen existente, imports Linux y comando exacto de tres casos.
Aceptación SQL y T-05 siguen pendientes de los scopes correspondientes.

Informe público de esta pareja y sus límites:
[QA4 Windows actual](testing/t05/qa4-windows-sql-current.md).
TDD n/a: actualización de prosa y recibos de verificación; producto intacto.

Entrega Windows cerrada adicionalmente: Root verificó 5.680 artefactos del
inventario final y recibo SHA
`da8a36d7561d9eb67130645272aaa0369128f4b3a36515288faa780e04032279`.
SourceGuard declara 279 metadatos exactos en ambas fases y carga actual de
0006 con ubicaciones originales; cierre exhaustivo TCB/nativo/transitorio
sigue UNKNOWN. Actor QA prepara Linux bajo release específico, sin tests.
Readiness del implementer encontró handshake de custodia fixture limitado
a dos miembros: se adopta en principio extender `custody.py` y regresiones
acotadas para FFmpeg real, preservando fixtures y límites de pipe existentes.
IPC privado máximo 16 MiB con rechazo antes spawn, sin truncar. Producto
todavía no liberado; implementación real y aceptación T-05 pendientes.

**QA4 Linux preflight verificado y tests liberados — 2026-10-09:** Root
cotejó inventario 655, fuentes actuales 117, espejo 136, purePython 463,
imagen exacta y probe Linux terminal 0 sin imports de app/pytest ni tests.
Dependencias pinneadas correctas, ningún paquete ausente; contenedor probe
propio retirado tras verificar owner/imagen. Plan SHA
`6e6b74c2a8a152da4b54d20c00225a0193bb4bcded504c6c93bd1cc8a991e9ba`,
CWD `/proof/inputs`, tres nodeids exactos, 18 mounts (17 readonly), sólo
namespace privado RW. `linux/root-release-tests.json` autoriza una corrida
del owner `7023d6612adc44c48adede22df40c431`. No resultados anticipados;
recibos Windows inmutables, sin pull/build/install/GPU/red ni servicios.
SQL y T-05 abiertos hasta evidencia final de sus respectivos alcances.

**Aceptación técnica SQL/identidad QA4 — 2026-10-09:** Root aceptó el
alcance del código actual tras la pareja Windows y suplemento Linux real
3 PASS/0 FAIL/0 ERROR/0 SKIP. Cotejo adicional: 39 cargas guardadas, 139
metadatos, source117/mirror136/libs463 intactos, cleanup propio, recibos
Windows preservados e inventario Linux705. Tres enlaces fixture sólo
metadata; Win1920/readlink error conservados, sin repetir tests. Terminal
Linux se acredita por inspect ExitCode0 y start-attach0; no recibo docker
wait fabricado. FINAL nativo QA completo guardado; recibo Linux SHA
`731666f562cd7e6b5cc46a72727913e74e879cc3ee5bbbb8d67661d46ce55b15`.
`t05-current-sql-independent-qa4/root-acceptance.json`; aceptación de
componente, no cierre T-05/M1/Git/E2E ni objetivo global.

**Implementación real A/B liberada:** actor `implement_t05_actual_execution1`
reanudado bajo `t05-actual-execution-implementation1/root-release-implementation.json`.
Ownership worker/audio_child, execution, packages, publications nuevos;
custody.py/LinuxGroup/supervisor/seam pipeline y tests acotados. Añadido
scope mínimo de `apps/server/pyproject.toml`, `apps/server/Dockerfile`,
`apps/server/Dockerfile.dockerignore`, `uv.lock` exclusivo para incluir
audio-post y payload FFmpeg Linux fijado en el runner/server real. Conservar
versiones/pins existentes y Python gestionado; sin GPU/Ollama/services.
Primer checkpoint preimágenes/runner/RED conductual real antes del compute.
IPC 16 MiB con rechazo antes spawn; fixturecustody/protocolo conservados,
reap secuencial confirmado por autoridad nativa. Contratos/modelos/0006/
snapshots/cola/coordinador/pins readonly. TDD/revisión/QA actuales obligatorios.
CA completos T-05, runtimeCPU2, beats/Analysis, Docker/E2E/Git siguen abiertos.

**Prerrequisitos de integración real en marcha:** implementer verificó
source117 y preservó ocho preimágenes owned; cuatro módulos nuevos aún
ausentes antes de implementación. Config server añade audio-post workspace
y Docker copia código/schema con payload FFmpeg cuyo archivo se verifica
contra SHA del pin existente. Build propio CPU en sesión 46045 comunicado
activo por actor, pendiente resultado real. Root cotejó uv.lock antes/después:
70 paquetes/versiones preservados; único record distinto server0.1.0,
añadiendo audio-post. `root-lock-parity-verification.json` privado.
El uv run de este cotejo sincronizó únicamente el editable server gestionado;
actor informado, siguientes verificaciones Root usarán --no-sync y nuevo
freeze de entorno antes de pruebas. TDD n/a: prerrequisitos de configuración;
todavía no se acredita RED de comportamiento ni cómputo/publicación real.

**RED real A/B — 2026-10-09T16:30:56 UTC:**
RED: `apps/server/tests/test_worker_actual_execution.py::test_real_wav_is_transcoded_and_published_once`
falló con `AssertionError: El WAV autorizado debe producir los cuatro assets durables`
(`set()` frente a master/listen/peaks/manifest), un caso fallido, 6,98 s.
Root cotejó JUnit, stdout y terminal: attach/container exit 1, Running false,
cleanup propio. Fixtures completaron WAV físico 384.044 bytes/2 s/48 kHz,
SQLite migrada, ganador succeeded/procedencia sintética explícita y FFmpeg
Linux real; no fallo de import/dependencia ni assert de mera existencia.
Stub pre-RED preservado privado y eliminado antes del test; service None
representa comportamiento actual sin publicación. Red1 fue preparación
OCI mount ausente, cero tests; error conservado, no contado como TDD RED.
Imagen real RED2 según inspect:
`sha256:ec34e3de06a299f8a36942e7b7606befa7824b1045e8f1aedd57fd2f942823e7`.
Hash preimport sobre 123 entradas copiadas readonly; esto no certifica
SourceFileLoader/TCB exhaustivo. Actor comienza implementación tras rojo,
pipe_protocol intacto; presupuesto 131 frames para 64 results/progress y
ready/result/closed. Nuevo freeze de entorno comunicado 9.719 archivos,
sin atribuir el freeze histórico8.126 a bytes nuevos. GREEN/revisión/QA
actuales y todos los CA T-05 permanecen pendientes.

**Primer intento GREEN real terminal rojo — 2026-10-09T16:41:17 UTC:**
sesión 17083, `green1`, mismo test original, 1 FAIL/13,24 s; attach/container
exit 1, Running false y cleanup propio. Root cotejó terminal/stdout: falla
en `publications.py:42`, renameat2(RENAME_NOREPLACE), errno 22 EINVAL hacia
destino bajo bind Windows. Imagen exacta de esa corrida
`sha256:51d5cc4a034c2a55faa849c4cac440eacc8ec1a08f0e8835c0f0a1b1e8c4a7e1`.
Actor reporta paquete preparado de cuatro archivos y journal supervisor
confirmed/reaped; no equivale a assets registrados ni take ready, pendientes.
Root autoriza diagnóstico mínimo causal bind vs tmpfs con st_dev/testigos
ajenos y salida real, sin tocar producto ni fallback de sobrescritura.
Tmpfs no sustituye ni acredita despliegue con data bindWindows; conservar
objetivo todoDocker/datos dentro proyecto. Próximo checkpoint causa probada
y alternativas concretas compatibles. No repetición por timeout, no cierre.

**Diagnóstico FS cerrado y ADR-0069:** probes propios confirmaron bind
9p/DrvFS EINVAL al rename NOREPLACE con destino ausente/same st_dev y
éxito nativo. Plain rename reemplaza directorio ajeno vacío: no fallback.
Arquitecto fresh comparó SMB, ext4/VHDX y reserva/CAS; Root elige ext4 en
VHDX físicamente dentro del proyecto, preservando traslado atómico y los
CA originales. [ADR-0069](../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md)
aceptada bajo delegación; constitución/arquitectura/spec/plan/test-plan
actualizados. Montaje virtual como vista del archivo propio, sin volumen
externo, nuevo servicio anfitrión o privilegios de montaje en server.
Token administrador de sesión actual false: aún no creación/attach/mount
ni acreditación persistente. Preparación revisable sí liberada.

**Diagnóstico nativo adicional:** UNA ejecución del test original sobre
tmpfs, `native-fs-diagnostic1` sesión 73999 terminal 1/1 FAIL/11,68 s.
Según rawactual alcanzó rename+assets4/takeReady/intentionCommitted;
falló después snapshots.publish porque song-v1 no admite procedencia
sintética actual. Export propio antes de terminar proceso acreditado;
no éxito de despliegueWindows ni aceptación A/B. Actor original frozen13
owned, restantes114 de source117 intactos. Contexto exacto params/lineage
parent-owned sealed decidido, pendiente implementar; nada de params{}
u original inventados para operaciones derivadas.

**Fix schema asignado:** implementer fresh
`implement_t05_snapshot_synthetic_schema1` sólo dos song-v1 espejos y nuevo
test_snapshot_synthetic_provenance; DTO/runtime readonly. RED real
snapshots.publish anyOf provenance; primeras regresiones green27 y Ruff0.
Compatibilidad215PASS/3FAIL por COVERAGE_FILE ausente tras asserts de
querybounds, preservar diagnóstico y corregir sólo entorno; no aceptación
todavía. Nuevos cierres sintéticos requieren RED propio; legacy preservado.

**Provisión asignada:** actor fresh `implement_t05_project_storage1`, sólo
nuevos scripts/storage.py/.ps1/.sh, docker-compose.storage.yml y pruebas
propias. TDD/dryrun/preflight de política; sin creación/montaje/formato/WSL
o datos reales. Asociación segura VHDX↔dispositivo no inventada: plan-only
hasta evidencia nativa. Main/settings/Compose original/runtime readonly;
startup wiring y QA persistente aún pendientes. Root sole ledger/Git/docs.

**Entrega fix schema:** 35 PASS finales, Ruff/check-format 0; byteparidad
dos JSON SHA `c84b8c4baa8698931ce4590bf81b6cef1fb20ecbdcf1e1447ec94860bae5a2f1`.
Aprendida proyectada exactamente al esquema original, sin min/max nuevos;
NULL intacto. Compatibilidad original183PASS más3 errores de preparación
COVERAGE_FILE, luego esos3PASS con entorno privado corregido. Nuevo test
RED real de snapshot y RED de cierre sintético conservados. Root verificó
actuales3 fuentes, restantes126 de manifiesto nativo y frozen13 registrados
antes/después; evidencia32logs/helpers/preimágenes, fuera fixtures/cache
declarados. No aceptación todavía, sin código Python productivo cambiado.

## Revisión de dos lentes — intento 1: T-05, schema de procedencia sintética

Preparador Root terminal0, scope0 sin avisos/exclusiones, tres archivos en
fixtureGit aislado; checkout compartido sin cambios Git. Selector C/D false;
C añadida explícitamente por aceptación estructural de procedencia pública.
Actores reviewer nuevos A/B/C (`review_t05_snapshot_schema_a1/b1/c1`),
prompts literales primero, sólo lectura y sin tests concurrentes. Revisión,
QA independiente y vuelta a integración real todavía pendientes.

**Entrega preparación storage:** cinco archivos nuevos, 18 tests de política
PASS/Ruff0, YAML/PowerShell parse conforme según productor. Dryruns
NEEDS_ADMIN/NEEDS_CONTEXT exit2, cero comandos ejecutables de discos.
Es preparación de política/planes únicamente: executor nativo, custodia
de asociación VHDX/dispositivo, preflight kernel y startup no implementados.
No aceptar almacenamiento desplegable ni garantías kernel con simulaciones.
Revisión/QA de ese alcance y ejecución persistente real siguen pendientes.

**Schema review1 cerrado y QA aceptada:** FINAL A/B/C originales guardados,
0 Critical/Important/Minor. Root adjudicación limpia actualSHA3; ningún
runtime Python cambió. Handoff adicional de productor guarda comandos
literales RED/RED-closed/GREENfinal y orden observado del historial; no
recibos CLI separados/UTC de invocación inventados. JUnit RED indica
2026-10-09T18:55:47.742824+02:00, rechazo provenance; RED-closed indica
19:00:18.181722+02:00, provider_extra no rechazado antes del fix.
RED: `apps/server/tests/test_snapshot_synthetic_provenance.py::test_packaged_synthetic_snapshot_publish_and_roundtrip`
falló `jsonschema.ValidationError: anyOf rows.job_attempt[0].provenance`
antes de editar esquemas, 2026-10-09.

QA fresca `qa_t05_snapshot_synthetic_schema1`: sesión22835/PID27460 TERMINAL0,
221 PASS/0 FAIL/ERROR/SKIP (35 nuevos+186 originales), 67,16 s, NONE tracing.
Root cotejó JUnit/rawterminal, actuales3SHA, originales IDs/cases y 263
artefactos del inventario; protected126/frozen13/tool9719 pre/post exactos.
`t05-snapshot-synthetic-schema-independent-qa1/root-acceptance.json` acepta
sólo compatibilidad estructural de snapshot sintético, no audio/FS/T-05.

**A/B contexto liberado:** actor original reanudado tras aceptación schema.
Primero TDD de pérdida de params request ganador/lineage derivada, luego
contexto parent-owned sealed/budget16MiB y comprobación independiente CAS.
DTO/model/SQL/cola readonly; gap durable exacto antes ampliar contrato.
Una diagnostic original nativa2 autorizada posteriormente para snapshot/
replay, sin atribuir éxito a desplieguebindWindows ni FS persistente.

**Storage puerta de preparación:** coverage1 68,69 % declaraciones y
coverage2 94,949 % líneas no satisfacían gate combinado. Medición corregida
privada con ramas: storage.py 94/99 líneas+49/56 ramas=143/155=92,2581 %,
28 PASS, cero exclusiones, según evidencia oficial del productor. Se
preservan resultados anteriores y .coverage root no se borra/adopta;
QA schema usó su archivo privado y sin instrumentación. Storage sigue
PLAN-ONLY, pendiente revisión/QA, executor y prueba persistente nativa.

## Revisión de dos lentes — intento 1: T-05, preparación de almacenamiento

Root verificó actuales5, informe oficial WHOLE143/155=92,2581 % y evidencia
35 artefactos logs/coverage, excluyendo fixtures/caches expresamente. Scope0,
C seleccionada por Docker/D false; A/B/C reviewers nuevos readonly. B/C sin
gaps. A-01 Important confirmado: los RED iniciales sólo comprobaban presencia
de storage.py y no alcanzaban assertions de política. No rebata con verdes
posteriores; alcance PLAN-ONLY preservado, ningún otro gap conforme.

| ID | Grado | Hallazgo | Estado |
|---|---|---|---|
| storage-A01 | Important | RED de presencia de módulo no acredita comportamiento TDD | fix1 pendiente revisión2/QA |

Root liberó FIX1 con archivo previo/histórico preservado, implementación
retirada y baseline temporal callable puro, entrypoint bloqueado exit2.
Nuevos RED reales individuales: administración UNIMPLEMENTED!=NEEDS_ADMIN,
conflicto UNIMPLEMENTED!=CONFLICT, alias DID NOT RAISE, parser
UNIMPLEMENTED!=ext4, identidad DID NOT RAISE y CLI None!=2. Después se retiró
baseline y se reescribió código desde contratos/tests, sin restaurar original.
Entrega fix1:28PASS, whole152/163=93,2515 % combinado/excl0; otros4/test
originales byteidénticos y814 fuentes ajenas intactas según productor.
Review2de3/QA aún pendientes, almacenamiento ejecutable/nativo no acreditado.

**Contexto A/B:** RED real compara params{} y linaje original inventado con
request ganador/Take variant real. Fixture requestduration30/WAV2 histórica
preservada; corregida a2/2 para fidelidad, assertions contraSQLite intactas.
ContextGREEN1 focal1PASS10,78s y privacyRED→GREEN1PASS10,41s fallando cerrado
en stylesinreceipt. Original diagnosticnativa2 session59027 TERMINAL0:
1PASS11,08s, WAV→hijo/2FFmpeg→paquete4→assets4/ready/committed→song.json→
replay sin sobrescritura. Tmpfs únicamente, no aceptaciónpersistente A/B/T05.

**ADR-0070 y helper asignado:** exact request/linaje quedan en recibo privado
sellado, opcionalpublic private_context:{sha256}; nunca letra/estilo públicos
ni ACEpreparation inventada. Recibo fullnormalizedJobRequest+SHA/song/takes
conoutput_index yoptional lyrics proof deDB LyricsVersion real
(id/hash/declaration); no autoría inferida deparams. DefaultDATAroot sólo
layoutcanónico song/take, otros/stagedrequierenrootexplícito. Actor fresh
`implement_t05_private_context_receipt1` sólo helpermanifest/schema/newmodule/
tests; workeractor no tocahelper hasta revisión/QA. RED causal inicial
existingverify_manifest no rechazó contexto ausente (DID NOT RAISE), antes
código; implementación ahora autorizada. FuenteSchemas/DTO/DB readonly.
WholePython>=80combinedsinexcl y regresionesM0 originales obligatorias.

## Revisión de dos lentes — intento 2: T-05, política de almacenamiento

En curso; no aceptación de tarea ni de despliegue. Root cotejó cinco fuentes
actuales, siete recibos RED con argv/UTC/exit1 anteriores al GREEN y el JSON de
cobertura oficial: 104/109 líneas + 48/54 ramas = 152/163 (93,2515 %), sin
exclusiones. Funcional productor: 28 PASS. Puerta de alcance del preparador
exit0 sin avisos; A/B despachadas frescas y C seleccionada, pendiente de slot.

| ID heredado | Grado | Hallazgo | Estado |
|---|---|---|---|
| storage-A01 | Important | RED anterior comprobaba presencia, no comportamiento | fix1 entregado; pendiente adjudicación de revisión 2 y QA |

Se preservan las aprobaciones restantes de A y los veredictos sin gaps de B/C
del intento 1; sólo se reabren con evidencia nueva. Entrega e inventario acotado
en `.cache/dev-cycle/m1/t05-project-storage-preparation-fix1`; revisión en
`.cache/dev-cycle/m1/t05-project-storage-preparation-review2`. El inventario
de evidencia cubre 30 archivos superiores, no fixtures/caches. El productor
guardó un resumen de protección posterior, no un inventario completo posterior;
Root comparó ahora las 814 huellas anteriores y encontró cuatro cambios
autorizados del helper paralelo, ajenos al almacenamiento. No atribuir a storage
esos cambios ni afirmar una comparación histórica independiente inexistente.

**Ampliación acotada del helper ADR-0070:** `private_context.py`, su nuevo test,
`packages/contracts/manifest-v1.schema.json` y su copia audio-post pertenecen a
T-05; la sincronización contractual es necesaria para la prueba del wheel.
Letra requerida nullable y declaración desde LyricsVersion autoritativa.
Los dos suites originales de preparación se añaden readonly a la puerta WHOLE.
Se preserva el fallo de fixture del benchmark
`test_session_runner_submits_once_after_estimate_and_resume_uses_receipt`:
Sensors carece de observation_method y se rechaza como legacy antes de las
assertions de idempotencia. Omitir sólo ese caso permite medir el helper; la
regresión del benchmark completa sigue pendiente de reparación independiente.

**Resultado de la revisión 2 de almacenamiento:** A/B/C FINAL recibidos y
preservados completos. A confirma storage-A01 corregido; B/C sin defectos;
0 Critical/Important/Minor pendientes. Root adjudica cierre limpio de este
bucle acotado, sin cierre de tarea. QA independiente ejecutó una sola batería:
28/28 PASS, terminal real exit0, WHOLE152/163=93,2515 %, cero exclusiones.
Ruff/formato/parserPowerShell/YAML conformes; Bash/Compose no ejecutados.
Root cotejó inventario26, JUnit28, terminal y cinco fuentes antes/después.
Componente PLAN-ONLY aceptado; executor/kernel/mount/startup/E2E pendientes.
Informe: [storage-policy-qa2.md](testing/t05/storage-policy-qa2.md).

## Revisión de dos lentes — intento 1: T-05, helper privado ADR-0070

En curso A/B/C frescas, alcance seis archivos y scope0 sin avisos. Root verificó
41 artefactos inventariados, seis fuentes actuales, JUnits funcional/cobertura
242 PASS/4 SKIP/1 caso omitido autorizado y wheel3PASS. WHOLE manifest.py
378/415=91,0843 %, private_context.py265/302=87,7483 %, sin exclusiones.
Los cuatro SKIP son symlinks nativos Windows rechazados por WinError1314;
no son PASS ni acreditan los cuatro casos en Linux.

Root recuperó los cuatro originales físicos de capturas históricas y los
cotejó con huellas anteriores; no son preimágenes personales tomadas por el
productor. RED del verificador existente: DID NOT RAISE, 2026-10-09,
toolchunk362238; nuevos RED causales ctime (9667cd) y tipos JSON (1714bc).
Los argv/exits/chunks están en tool-evidence.json; UTC exacta de invocación y
stdout original de esos RED no fueron capturados: no se inventan recibos.
Primera batería roja y error inicial de colección de cobertura preservados.
La integración del worker sigue bloqueada hasta revisión/QA del helper.

**Reparación independiente del fixture M0/T-09:** una única declaración
Sensors.observation_method="task_manager_v1" en el test original produjo
RED original exit1, GREEN focal1PASS y suite del fichero16PASS, según entrega
del productor. No cambia política ni código del benchmark; revisión/QA
independientes pendientes, por lo que aún no se acepta el arreglo ni M0/T-09.

**Resultado review1 del helper ADR-0070:** A sin gaps de conformidad; B y C
aportan dos Important confirmados por Root. Los FINAL completos y la
adjudicación están en `t05-private-context-receipt-review1`; no se acepta aún.

| ID | Grado | Hallazgo | Corrección / evidencia |
|---|---|---|---|
| B-PC-01 | Important | API directa acepta commercial_use 1/1.0 frente true por igualdad Python | fix1 TDD autorizado; el schema protege el wrapper, no repara la API directa |
| C01 | Important | Sustitución de archivo por FIFO Linux puede bloquear open antes de fstat | fix1 TDD autorizado; análisis estático/probe inyectado, regresión nativa aún pendiente |

Root mantiene las demás aprobaciones y no convierte `root_take_id` provisional
del worker en nuevo campo contractual. El identificador intermedio erróneo de
probe comunicado por B fue retirado; no se usa como recibo. FIX1 sólo puede
modificar `private_context.py` y su test, con las otras cuatro fuentes intactas.
Actor capturó preimágenes físicas y sellos de los seis archivos antes de tocar
producto. Se autorizó únicamente diagnóstico Linux CPU en la imagen existente
51d5cc4a… y un hijo/FIFO propios con deadline de prueba y cleanup por propiedad;
sin red, GPU, pesos, privilegios ni operaciones de servicios globales.
Después: regresiones originales sin deselect, cobertura WHOLE, review2 y QA.

**FIX1 RED/GREEN causal observado por Root:** seis preimágenes físicas
verificadas. 2026-10-09T18:12:05Z, RED comercial6 casos: 4 FAIL DID NOT RAISE
y2PASS; simulación Windows1FAIL con assertion de bloqueo. RED Linux real
en snapshot con helper anterior intacto: hijo propio22 intercambió archivo
por FIFO, bloqueó3,007 s, fue terminado/reapado después del deadline3 s;
test1FAIL, contenedor propio exited1 y cleanup0. Root cotejó ocho inputs,
terminal/propiedad/image/childreceipt y pruebas originales. Tras fix focal:
comercial6PASS, simulación1PASS. FIFO Linux GREEN1PASS, rechazo0,665 s,
hijo exit0/reapado y cleanup0. No se acepta todavía helper completo:
regresión/cobertura actual, review2 y QA pendientes.

## Revisión de dos lentes — intento 2: T-05, correcciones del helper privado

En curso A/B/C frescas, scope0 sin avisos. FIX1 entregado y congelado:
dos fuentes cambiadas (helper y test), otras cuatro byteidénticas, 11
protegidos conservados. Root verificó 164 artefactos con SHA/tamaños, fuentes
actuales6 y preimágenes6; delta físico en fix-delta.diff. Funcional y cobertura
actuales: 250PASS/5SKIP/0deselect, terminales66444/27429 exit0; no repetir.
WHOLEmanifest378/415=91,0843 %, helper267/302=88,4106 %, sin exclusiones.
Cuatro skips son symlinks originales Windows; el quinto es FIFO Linux en
Windows. Ese nuevo caso sí se ejecutó por separado nativamente en Linux.

| ID heredado | Grado | Hallazgo | Estado |
|---|---|---|---|
| B-PC-01 | Important | Uso comercial con tipos JSON distintos aceptado en API directa | fix1 GREEN causal; pendiente adjudicación review2/QA |
| C01 | Important | Apertura bloqueante de FIFO sustituido | fix1 GREEN nativo y simulado; pendiente adjudicación review2/QA |

Las demás aprobaciones de A/B/C del intento1 se conservan y sólo se reabren
con evidencia nueva. La última separación de imports en el test nuevo ocurrió
después de la pareja funcional/cobertura: AST sin posiciones idéntica, código
runtime y posiciones de la función FIFO nativa intactos; se declara esa
normalización, no se finge una pareja ejecutada después. Fuentes congeladas
actuales serán las de la QA independiente. Entrega en
`t05-private-context-receipt-fix1`; revisión en `t05-private-context-receipt-review2`.
No aceptación de helper completo, worker, despliegue persistente ni T-05 todavía.

**Resultado review2 del helper:** A/B/C FINAL completos recibidos y preservados,
0 Critical/Important/Minor; B-PC-01 y C01 corregidos y demás aprobaciones
conservadas. Root adjudica revisión limpia, no aceptación de QA ni tarea.

**QA2 independiente — NO VERDE:** Windows funcional y cobertura250PASS/5SKIP/
0deselect, terminales65773/61750 exit0; WHOLE91,0843/88,4106 % sin exclusiones.
Linux original1PASS/4FAIL/0SKIP, exit1. FIFO real rechazado0,696859 s con hijo
reapado; cuatro casos symlink fallan en finally link.rmdir() POSIX (ENOTDIR),
no se contabilizan como PASS aunque las assertions precedieran a la limpieza.
Contenedor propio exited1 verificado y cleanup0; todas sesiones terminales.
Root verificó90artefactos y conserva fallo en
`t05-private-context-receipt-independent-qa2`. No cambiar ni reetiquetar esa fase.

## Revisión de dos lentes — intento 1: T-05, limpieza portable del fixture

Reparación separada exclusivamente en test_portable_audio_post.py: symlink
se elimina con unlink y junction con rmdir. Todos los asserts originales y
AST restante exactos; 51 archivos protegidos sin cambios, incluidas fuentes
del helper. TDD/cobertura de producto n/a: limpieza de test, sin producto nuevo.
RED original cuatro ENOTDIR se conserva; productor Windows18PASS/4SKIP
(junction4PASS), Linux originales4PASS exit0, contenedor propio limpiado.
Fallos de preparación CRLF/referencia Docker inválida preservados; no son
REDs de producto ni se afirman contenedores creados en esa preparación fallida.
Root verificó121artefactos, fuente/preimagen, assertions/AST y reporte native.
Scope0 sin avisos, A/B frescas en curso; C/D no seleccionadas.
Luego: QA3 del helper con test actualizado, sin aceptación todavía.

**Readiness worker:** entregado sólo nuevo context-integration-readiness1.md,
sin cambios de producto ni tests. Detalla captura SQL autoritativa de
LyricsVersion/Take, presupuesto conjunto16MiB, staging explícito, retiro de
provisionales y primer RED real music.song. Se verifica el alcance real de los
writers de letra/enlace tras committed antes de ampliar invariantes SQL;
ningún writer futuro se cuenta como código actual.

**Fixture cleanup review1 cerrada:** A/B sin gaps; 0 Critical/Important/Minor.
Veredictos completos preservados; Root mantiene helperreview2 independiente.
QA3 fresh en curso en `t05-private-context-receipt-independent-qa3`: selección
Windows completa y los cinco nodeids originales Linux, séptima fuente portable
actualSHA4945c2… y fuentes6helper intactas; no adaptar tests para fabricar verde.

**Resolución de alcance SQL del contexto:** explorador readonly confirmó
chains.py:176/187–205 sólo crea takes; manual_retry.py:135–140 selecciona failed
y sólo cambia status/job_id; publications.py:371–379 publica campos de estado;
snapshots.py:671–674/698–709 rechaza colisión distinta y no modifica letra/enlace
de filas existentes. No hay CRUD de letras/takes vigente que cambie esos campos
después de committed. SQL/ORM directos sí pueden cambiarlos: guardas actuales
no incluyen binding ni contenido de LyricsVersion; no se afirma lo contrario.

ADR-0070 exige captura y cotejo antes de preparar/publicar/reconciliar, no
freeze global de todas las versiones. La integración debe detectar divergencia
con el recibo histórico durable anclado al manifiesto, incluso replay, sin
recapturar/adoptar otro SHA como autorización. No se amplían migraciones/DTO
en este release de worker. Las futuras rutas T-07 deben crear versiones nuevas,
conservar procedencia readonly y aplicar las invariantes canónicas; no se
considera su implementación ni sus writers como evidencia actual.

**QA3 y aceptación técnica del helper:** Windows funcional/cobertura250PASS/
5SKIP/0deselect, 255 nodeids conservados; Linux originales5PASS0FAIL/ERROR/SKIP.
FIFO rechazado0,669224s con hijo reapado; contenedor propio exited0 y cleanup0.
WHOLEmanifest378/41591,0843 %, helper267/30288,4106 %, cero exclusiones.
Root verificó85artefactos, fuentes7, protegidos10, inputsLinux9 y
owner/image/id/terminal/noPrivileged/networkNone/noGPU. Helper y fixturecleanup
aceptados como componentes; QA2 NO VERDE conserva todos sus resultados.
Informe [private-context-qa3.md](testing/t05/private-context-qa3.md).

**Integración del worker liberada:** release nuevo
`t05-actual-execution-implementation1/root-release-context-integration1.json`.
Ownership cuatro módulos worker principales, seams existentes sólo necesarios,
tests originales conservados/nuevos de autoridad y replay. Helper/contracts/
models/migrations/queue/snapshots/coordinator/pins readonly. Primer checkpoint
preimágenes actuales + buildCPUconhelperaceptado + RED real music.song conWAV2s
y LyricsVersionSQL propia antes del código. Recibo write-once porhash,
proyección compartida, stagedDATA explícito, retiro de provisionales,
presupuesto TOTAL16MiB y drift/replay contra referencia histórica son obligatorios.
No dependencias nuevas/uv.lock edits; DockerCPUpropio con inputs existentes.
FullWorker/CPU2/Analysis/persistencia/E2E/review/QA y cierreT05 siguen pendientes.

**Diseño ejecutor VHDX O2:** arquitecto trabaja sólo informe privado en
`t05-vhdx-native-executor-design1`, compara creación/formatdevicepropio vsimagen
ext4 offline/convertVHDX segura y preflight kernel UUID sin privilegios del server.
ADR0069/atomicidad/datosproyecto se conservan; no se instala/provisiona/monta,
ni se usa disco por posición, loopprivilegiado9p o shutdown global.

**Elección del executor VHDX:** Root elige B bajo delegación, ext4 offline en
archivos propios→VHDX→montaje por ruta exacta. ConservaADR0069 y atomicidad;
no formatea `/dev` elegido por enumeración. Custodia Windows/FD Linux y
qemu-img create/convert deben probarse con herramientas fijadas; no se afirman
validadas porque sólo se leyó código upstream. QEMU ausente, licencias/lock
pendientes antes de incorporar herramientas. Preparación offline sinadmin;
attach/detach y QA persistente requierenprivilegio actualmenteausente.
Diseño [storage-execution-design.md](storage-execution-design.md).

**Checkpoint worker actual:** primera observación REDsong1 session43589
terminal1, Take.failed/PROVENANCE_MISSING vsReady despuésWAV/FFmpeg. Root
cotejó preimágenes9, inputs79/130, lock70 y38paquetes. Sin embargo GREENsong1
64731 terminal1 CPU_CUSTODY_UNKNOWN antesReady/0FFmpeg reveló un fallo de
arnés: Path app/. normalizó el punto y docker cp creó app/app y
audio_post/audio_post. Imagen80064… no tenía helper en el path real del hijo;
el censo de inputs/versiones no probaba contenido runtime. Se retira esa
atribución de imagen integrada actual; ambas observaciones quedan preservadas.

Root exige corregir sólo COPY literal y hashguard de todos paths runtime antes
commit. Para reacreditar TDD con runtime fiel, preservar fix4actual/logs,
retirarlo y devolver únicamente4owned a preimágenes exactas; correr nuevo RED
contra imagen baseline corregida; después reescribir desde contrato/tests,
sin restaurar/copiar el fix previo. No Git reset ni cambios ajenos; otras5owned
intactas, originales/asserts conservados. No nuevoGREEN hasta ese checkpoint.
Esto repara preparación/TDD, no es aceptación de runtime, persistencia ni T05.

**Reacreditación de RED con runtime correcto:** fix4 previo se preservó en
INVALID-before-correct-red; Root cotejó canonical9 exactas a preimágenes y
snapshot130. Imagen baseline0dd66c… COPYliteral,73 hashes de paths reales
verificados antescommit;38 paquetes/lock70 iguales. Guard stdlib diagnóstico
sitecustomize sóloimagenpropia verifica esos73 y el entrypoint antes de ejecutar:
supervisor22 SHAaae89… y audiochild23 SHA075045… conformes.
CorrectREDsong1 session77457 TERMINAL1: mismoassertTakeReady→failed,
1FAIL10,31s, sinimport/helperMissing y con2FFmpeg. Root verificó JUnit,
terminal/cleanup,9preimages/runtimeguards y emitió
`t05-actual-context-integration1/root-corrected-red-verification.json`.
REWRITE autorizado ahora desdeABI/contratos/tests, sin leer/copiar fix inválido;
fuentes compartidas readonly y originales conservados. NuevoGREEN/coverage/
review/QA pendientes, ninguna aceptación del worker todavía.

**Prerrequisitos de provisión B:** investigación sólometadata primaria de
QEMU/e2fsprogs Linuxamd64/Bookworm, versiones/hash/dependencias/licencias en
`t05-storage-tool-candidates1`. No binarios/install/código/locks ni incorporaciones
antes fila legal y pin verificable. La versión upstream leída no sustituye la
prueba de la versión finalmente fijada sobre FD propio.

## T-05 · GREEN de canción y adquisición fijada de storage

2026-10-09. Root leyó JUnit original y terminal de
`t05-actual-context-integration1/green-song-rewrite2`: exit0, un caso PASS;
la llamada de verificación usa raíz de proyecto y DATA explícito. Actor informa
Ready, cuatro assets, recibo privado exacto, autoría SQL y replay sin duplicados.
Root también leyó terminal0 del instrumental original. Negativos2 informa10PASS;
cobertura focal2 seguía en sesión96450. La entrega de fuentes congeladas,
revisión y QA siguen pendientes. Estos tests usan tmpfs, no despliegue persistente.

**TDD n/a: registro declarativo de pins/licencias.** Root verificó90artefactos,
seis hashes/tamaños de índices contra InRelease,30paquetes contra sus estrofas
originales y los tres logs gpgv terminal0;68restricciones declarativas concuerdan.
Comando `uv run --no-sync python -B .cache/dev-cycle/verify-storage-tool-candidate-root.py`
→ sesión6703 terminal0; recibo `t05-storage-tool-root1/root-metadata-verification.json`.
Nuevo `tools/storage-linux.lock.json`, SHA
`96871d907f50d78583287a1f1f7464bc46a604418d8f48929b85704450e8d4f5`;
filas legales QEMU/e2fsprogs/bundle añadidas. El candidato cp1252 se corrigió a
UTF8 con igualdad JSON y original preservado. Copyright PCRE2 security exacto
se extraerá del DEB fijado antes de ejecutar; predecessor no es equivalente.

Actor research autorizado a adquirir30DEBs verificados en tools/storage-linux
y probar herramientas/FDs en fixture privado CPU, sin instalar globalmente,
sin disco final ni attach. Implementer fresco autorizado sólo nuevo
`packages/storage-guard/` y pruebas: FD/UUID/mountinfo/NOREPLACE y RootLease,
sin wiring ni cambios de locks. Producto todavía no tiene ese startup gate
conectado. No aceptación de persistencia, worker completo ni cierre T-05.

**RED:** `packages/storage-guard/tests/test_preflight.py::test_valid_server_retains_fd_until_close`
falló con `NotImplementedError: storage preflight not implemented` ·2026-10-09.
Root leyó raw stdout/JUnit/terminal1 de
`t05-storage-preflight-implementation1/red1`; un fallo, sin fallo de import.
Scaffold explícito sin comportamiento; prueba mediante backend simulado
declara la retención/cierre del FD. No es prueba nativa ext4 ni de startup.
Implementer continúa GREEN y criterios posteriores dentro de su ownership.

Informe público de metadatos/pins/límites:
[storage-tool-metadata.md](testing/t05/storage-tool-metadata.md).

## T-05 · Evidencia actual de runtime y fallo causal pendiente

Root ejecutó `verify-storage-acquisition-root.py`→exit0:30DEBs,
11.136.896bytes, hashes oficiales y copyright PCRE2 obtenido del archivo
exacto verificados. Después `verify-storage-runtime1-root.py`→exit0:
139artefactos,579sellos TAR y30copyrights; siete comandos reapados,8asserts
PASS/1FAIL. Cinco versiones y ayuda QEMU pasan; mke2fs por FD termina1
DeviceSizeZero. Contenedor553fc5…terminado1/eliminado; exportstatic propio
sin arrancar/eliminado. Los recibos Root aceptan la evidencia del fallo,
no formato ext4 ni VHDX. Informe y filas legales actualizados.

`custom-agents:debug-root-cause` aplicado a demanda: namespace nuevo
`t05-storage-tool-fd-debug1`, runtime1 congelado. Primer mínimo termina1
en fstatFD trasrename→ENOENT antes de mke2fs; controles filesystem/FD en
aislamiento. No causa establecida ni fallback autorizado a nombres mutables.

Worker coverage96450 terminó0,13PASS; whole audio_child70% y
publications74,05% **no cumplen**80%. La ampliación conserva exclusiones0.
**RED:** `test_actual_ffmpeg_failure_is_durable_and_has_no_assets`
falló CPU_CUSTODY_UNKNOWN; traceback real muestra LibsndfileError de sf.read
·2026-10-09. Root leyó raw childstderr de audio-invalid-red2 y JUnit/terminal
de audio-invalid-green1: unPASS, exit0 tras captura explícita SoundFileError
→AUDIO_INVALID, sin ocultar crashes generales. Nueva imagen93a6…actual.
Focalcurrent1 tuvo20PASS/1fallo fixture sparse(seed17 debía20), con exportFIFO
fallido posterior; actor conserva bruto y corrige sólo fixture/export propios.
Focalcurrent2 sesión62253 estaba activa al checkpoint. Entrega/review/QA
actuales pendientes, sin aceptar cobertura anterior al fix ni persistencia.

Storage-guard informa27Linux/22Windows y coberturaWHOLE92,28%exclusiones0;
es un componente nuevo todavía sin wiring ni revisión/QA. Los primeros RED
nativos tienen evidencia/preimágenes limitadas declaradas por el implementer,
no se inventan snapshots retrospectivos. Root examinará entrega congelada.

## Revisión de dos lentes — intento 1: T-05, componente storage-guard

Entrega original congelada del implementer: cinco fuentes nuevas,28LinuxPASS,
23WindowsPASS/5SKIP;223/236líneas y69/80ramas, WHOLE292/316=92,4051%,
exclusiones0. Root verificó1864artefactos,522inputs nativos y sus guards,
JUnit/terminales y13contenedores propios terminales/eliminados. Se declararon
cinco fuentes en Archivos de T-05; no startup/wiring ni locks de dependencias.
Preparador Root `prepare-storage-preflight-review-root.py`→exit0 tras corregir
su expectativa de label a la real `studio.owner`, sin cambiar producto.
Scope-check0sinavisos/info; selectorC/Dfalse. Root añade C por custodia y
limpieza de archivos propias; tierreviewer frontmatter. Fase
`t05-storage-preflight-review1`, lentes A/B/C previstas; A fresca despachada,
B/C pendientes de slot. No aceptación por revisión ni QA aún.

**Causa storage probada (fase3, fix no aplicado):** Root verificó142artefactos
FD-debug y seis controles: bindWindows9p sinrename64MiB; rename-only produce
ENOENT; rename+testigo45bytes da tamaño45/getsize0/mkeFAIL. Tmpfs mantiene
64MiB y mkePASS con el mismo binario. No atribuir éste último a persistencia.
Recibo `root-fd-cause-verification.json` y diseño actualizado. Probe privado
nuevo `t05-storage-windows-custody-probe1` autorizado para acreditar guardianes
Windows sin FILE_SHARE_DELETE antes de herramientas por FD. No bloques
explícitos para ocultar fallo, ni fallback a rutas, ni VHDX final/attach.

Worker focalcurrent2 informa21PASS69,16s y cleanup/export completos; nueva
cobertura actual80702 estaba activa en imagen93a6… con traza real antesexec.
No fuente de cobertura anterior al SoundFileError-fix sustituye este gate.

**Revisión1 de storage-guard cerrada con gaps:** A limpia; B1Critical/2Important;
C2Critical. Fullfinales persistidos `t05-storage-preflight-review1/final-a.md`,
`final-b.md`, `final-c.md`; Rootfusión `root-adjudication.json`:2Critical y
2Important tras deduplicar B01=C01. B01/C01stat→borrado permite borrar
objeto ajeno; C02sello posterior al cierre puede adoptar bytes modificados;
B02pierde binding raíz original al mover montaje; B03entrega par library/raw
con biblioteca yaRW. Root reprodujo B03 en memoria (chunke06393), sin writes.
Sin QA ni aceptación del componente. Contador permanece1; siguiente2trasfix.
Limitación de preimágenes RED9/12 declarada y evaluada por A no demuestra
code-before-test; no se fabrica evidencia ni se borra historia por ella.

Architect confirmó que Linuxunlinkat carece de CASinode y que másstat o
quarantine no cierran la carrera. Root eligió **O1, dominio de probes realmente
aislado**, para mantener limpieza inmediata y preservación de datos ajenos.
Refinamiento de ABI/helperCPU/DockerUID/capabilities y ADR nuevo en curso;
ningún booleano del caller ni recibo antiguo activará el gate.

**Diagnóstico Windows fase4 verificado por Root:**43artefactos/27PASS,
14rename/delete bloqueados, nueve comandos reapados exit0 sobre mismosFD3/4
con10guardianesWindows; ext4→VHDX compare0, hashes Windows/Linux iguales.
Contenedor propio eliminado, handles cerrados y tres fixtures propias limpiadas.
Root `verify-storage-windows-guardian-root.py`→exit0 tras corregir dos
expectativas de su parser (nombre de stdout/formaJSON), sin modificar evidencias.
Recibo `t05-storage-tool-root1/root-guardian-verification.json` acepta sólo
el diagnóstico privado: no executor, promoción, crash, montaje ni persistencia.
Gotcha propuesta GOT-001 indexada; no conocimiento aprobado ni cierreT05.

Worker entregaactual congelada `t05-actual-context-integration1/delivery.md`:
21integraciónPASS,9focalesPASS,42custodyLinuxPASS (actualhook privado separado).
WHOLEcombineoficial de mismoSource4:82,684/85,714/84,444/80,466%,exclusiones0.
Fuentes10físicas, helper7/protected10/image73 verificados por actor. Root
todavía debe verificar entrega y lanzar review/QA actuales; no aceptación aún.
## T-05 — replay parcial y contexto preparado (fix local)

2026-10-09. El ciclo TDD del worker conserva el bloqueo B1-01 de la revisión
adversarial: `apps/server/tests/test_worker_recovery_regression.py::test_replay_rejects_partial_reserved_history_before_returning_receipt`
falló en RED con `DID NOT RAISE` porque un sibling `committed` ocultaba otra
toma `reserved` sin paquete. El caso es una regresión funcional aislada, sin
fallo de import ni fixture.

El GREEN añade rechazo explícito `CPU_EXECUTION_REQUIRES_RECOVERY` cuando el
replay encuentra una intención `reserved`, `prepared` o `renamed` sin paquete;
las intenciones históricas `failed`/`cancelled` siguen pudiendo conservar el
resultado mixto. La misma unidad incorpora `PreparedContext` para reutilizar
una representación canónica validada por ejecución y evita reserializarla por
toma, manteniendo la revalidación de fichero privado en cada verificación.
Focales verdes: regresiones 2 PASS, contexto privado 62 PASS/1 SKIP,
invariantes de publicación 39 PASS y Ruff 0. Cobertura oficial, revisión
adversarial de seguimiento y QA Linux/Docker siguen pendientes; T-05 no se
cierra con esta evidencia.

## T-05 — QA Docker de la corrección actual

2026-10-09. La imagen reproducible `music-studio-t05-current:cpu` se construyó
con el árbol actual. La prueba focal en contenedor, con `.cache` temporal
escribible, pasó **41/41** (`test_worker_recovery_regression.py` +
`test_worker_publication_invariants.py`) en 19,69 s. La suite Linux con
FFmpeg fijado por SHA-256 y volumen cross-device temporal `/proof` pasó
**26/26** en 74,93 s (`test_worker_actual_execution.py` +
`test_worker_private_context_integration.py`). La primera ejecución Linux
falló sólo porque el arnés no había montado `/proof`; se repitió con el
volumen previsto y quedó verde.

Esta evidencia valida el delta en Docker/FFmpeg real, pero no cierra T-05:
la revisión adversarial fresca, la cobertura oficial de los módulos completos,
el almacenamiento persistente y la QA de los criterios restantes siguen
pendientes.

## T-05 — Revisión fresca y recuperación de resultados fallidos

2026-10-09. La lente fresca A/B/D detectó B-01 (Important): `_stored_results`
reconstruía sólo estados `committed` y perdía tomas históricas `failed` o
`cancelled` en una ejecución mixta. El caso TDD falló en RED con una tupla
vacía frente a dos `TakeFailure` esperados. El GREEN conserva el orden del
plan, recupera `intent.error_code`/`revision.error_code` y rechaza con
`CPU_EXECUTION_REQUIRES_RECOVERY` un código ausente o inválido. Regresión,
Ruff y formato: **3 PASS**.

La imagen Docker reconstruida con este cambio pasó **42/42** pruebas focales.
La suite Linux/FFmpeg ejecutada en lote presentó fallos intermitentes de
custodia (`CPU_CUSTODY_UNKNOWN`) en casos distintos entre ejecuciones; cada
caso fallido pasó al repetirlo de forma aislada y la corrida anterior completa
había pasado 26/26. Se conserva como evidencia de inestabilidad del arnés,
no como aceptación de QA Linux: el gate de QA y la cobertura oficial completa
siguen pendientes.

## T-05 — Finalización post-audio y análisis de beats

2026-10-09. El ciclo TDD cerró dos huecos de integración detectados en la revisión fresca. `Publisher._complete_post` marca el `post.audio` como publicado y deja en `failed` los jobs `audio.beats` cuyos takes tienen `TakeFailure`; los beats de takes válidos permanecen bloqueados para la admisión posterior. `EventConsumer` persiste el análisis terminal de `audio.beats` como `analysis(kind=beats)` después de avanzar el cursor, evitando autoflush contra invariantes de terminal.

RED/GREEN funcional: `test_post_completion_marks_job_and_failed_beat_durable` falló con `AttributeError` antes de implementar el cierre y pasó después; `test_audio_beats_terminal_persists_analysis_for_ready_take` falló porque no existía la fila y pasó después. Verificación local: worker/replay **43 PASS**, eventos **17 PASS**, cadenas **16 PASS**, referencias **29 PASS** y Ruff check/format **0 errores**.

La imagen `music-studio-t05-current:cpu` se reconstruyó. QA focal en contenedor, con los tests montados en la raíz confinada `/studio` y las variables de fixtures declaradas, pasó **60/60**. Una ejecución anterior del arnés fuera de `/studio` se conserva como fallo de entorno (`Path must remain inside the studio`/`STUDIO_QUEUE_TEST_ROOT`), no como fallo de producto.

T-05 sigue `en-progreso`: falta conectar el `CpuAudioService` al ciclo de `QueueRuntime`/planificación real del job `post.audio`, completar la cobertura oficial de los módulos y resolver el almacenamiento persistente VHDX/montaje. No se marca ningún criterio de aceptación todavía.

## T-05 — Integración del worker CPU en QueueRuntime

2026-10-09. Se añadió `apps/server/app/worker/planning.py` para componer `PostPlan` exclusivamente desde el job `post.audio`, su dependencia de generación, el intento ganador, los artefactos terminales y los `Take` persistidos. Verifica propiedad, estados, índices, SHA del fichero, duración y procedencia antes de permitir la ejecución. `CpuAudioService` reclama el job con una transacción atómica y respeta el máximo global de dos trabajos CPU; los fallos de composición se materializan como job/takes `failed`.

`QueueRuntime` crea el servicio sólo cuando encuentra la build FFmpeg fijada en el proyecto, despacha únicamente `post.audio`, conserva `audio.beats` para el carril CPU normal y persiste un fallo del worker si la ejecución termina sin resultado. Nuevas regresiones: composición de plan **2 PASS**, despacho runtime **1 PASS**, límite de slots CPU **1 PASS**.

Verificación local de la unidad ampliada: **21 PASS** (runtime, planning, replay, worker y cadenas seleccionadas), Ruff sin errores. Imagen server reconstruida y QA focal Docker **64/64**; QA Docker con FFmpeg Linux real y volumen `/proof` **26/26**.

T-05 continúa `en-progreso`: faltan la recuperación/cancelación completa del worker CPU, la cobertura oficial de los módulos completos y el almacenamiento persistente VHDX/montaje. La ruta automática ya está conectada en el server Docker.

## T-05 — Custodia desconocida conserva el fallo de ejecución

2026-10-09. El runtime ya no convierte una excepción posterior a la creación de `CpuExecution` en un `failed` ficticio: `fail_plan` detecta una ejecución no terminal y deja el job `interrupted` con `CPU_CUSTODY_UNKNOWN`. Sólo los errores de composición anteriores a crear custodia marcan job y takes como `failed`. Esta frontera conserva la autoridad de reconciliación para el siguiente arranque.

Tras el ajuste, Ruff permanece verde y el foco Docker actualizado vuelve a pasar **64/64**.

## T-05 — Verificación Docker del runtime CPU tras recuperación/cancelación

2026-10-09. Tras los cambios de custodia y cancelación, Ruff check/format quedó a cero y la suite local del runtime, planificación, replay, publicaciones y eventos pasó **64/64**. La misma imagen reproducible `music-studio-t05-current:cpu` pasó **64/64** en Docker con los tests montados dentro de `/studio`. La verificación Linux con FFmpeg fijado por SHA-256, WAV físico y volumen `/proof` pasó **26/26** en 54,22 s; la primera invocación sin `STUDIO_ACTUAL_FFMPEG` se clasifica como fallo de arnés y no de producto.

La integración automática del worker CPU queda verificada en el contenedor y con FFmpeg real. T-05 sigue `en-progreso`: la cobertura oficial completa, la reconciliación/cancelación con fixtures de ejecución activa, la revisión/QA del delta y el almacenamiento persistente VHDX/montaje siguen abiertos.

## T-05 — Evidencia de reconciliación de custodia activa

2026-10-09. Se añadió una regresión con `CpuExecution` no terminal persistido y un `post.audio` en ejecución. `CpuAudioService.reconcile_startup()` pasa **1/1** y deja ambos registros en `interrupted` con `CPU_CUSTODY_UNKNOWN` y `cleanup_state=unknown`; la suite local del worker/runtime queda en **65/65**. Ruff check/format también queda verde. Esta evidencia cubre el caso de reinicio con custodia activa; no sustituye la prueba de cancelación durante un proceso real ni el almacenamiento persistente.

Corrección de verificación — 2026-10-09: el primer chequeo Ruff de la regresión detectó un import de fixture sin uso; se eliminó. La repetición de Ruff check/format termina sin errores.

## T-06 — Verificación del núcleo SSE U1

2026-10-09. La verificación aislada del bus, framing, DTOs y snapshots SSE pasa **147/147** en Windows; la suite de sesiones locales pasa **55/55** con el adaptador de importación del paquete. La prueba amplia de `apps/server -k sse` no se usa como gate porque mezcla módulos Linux-only y fixtures que exigen variables de entorno específicas. T-06 permanece `en-progreso`: todavía falta conectar el endpoint HTTP `/api/events`, la credencial de sesión al stream y el E2E de reconexión.

## T-06 — Endpoint HTTP SSE autenticado y replay

2026-10-10. Se conectó `GET /api/events` al `EventBus` del runtime. El endpoint valida la sesión local, comprueba pertenencia de `song_id`, filtra por owner, acepta `Last-Event-ID` y `X-Studio-Known-Jobs`, emite snapshots acotados cuando el cursor no se puede reproducir y mantiene heartbeat cada 15 segundos. El framing público continúa ocultando terminales, rutas y payloads privados. La preflight CORS se limita a GET y a los headers SSE propios.

TDD: los tests HTTP empezaron en RED con 404. GREEN local: **85/85** (`test_sse_http.py` + `test_session_http.py`), núcleo SSE **147/147**. Docker sobre `music-studio-t06-current:cpu`: endpoint SSE **3/3** y regresión worker/runtime **65/65**. Ruff check/format y `ledger-lint` quedan verdes. T-06 sigue `en-progreso`: falta el E2E navegador y verificar la integración con todos los escritores transaccionales antes de cerrar la tarea.

## T-06 — Contrato generado y cliente web compatible

2026-10-10. El handler code-first se exporta con `scripts/export_contracts.py --check` y `pnpm --filter web gen`; el tipo generado incluye `/api/events`. La suite web termina **222/222** y TypeScript typecheck pasa. El OpenAPI canónico y sus pruebas server pasan **19/19**. Se conserva el transporte fetch/ReadableStream del cliente con cursor `epoch:seq`, bootstrap de sesión en memoria y query `known_job_id` alineada con el contrato HTTP.

## T-07 — API de dominio inicial y acceso seguro a takes

2026-10-10. Se implementaron las rutas iniciales de dominio en `apps/server/app/domain_routes.py`: CRUD básico de canciones, versiones de letra, creación de cadenas de generación, detalle y edición de takes, papelera/restauración, selección de master, cancelación y reintento de jobs, audio con `Range`, peaks, análisis, modelos, sistema, estimación y descarga de modelos.

TDD: la regresión de dominio pasó de RED por rutas ausentes a GREEN con **7/7** (`test_domain_routes.py`). La prueba cubre propiedad local, `Range` 206 con `Content-Range`, límites de assets, master, cancelación durable, descriptores, estimate y unload. La regresión conjunta de contrato, sesiones, SSE y dominio pasa **111/111**; `export_contracts.py --check` y `pnpm --filter web gen` quedan verdes.

T-07 sigue abierto: quedan paginación/FTS completa, colecciones, integración de reintento contra jobs reales, cobertura oficial del módulo, E2E y revisión adversarial. No se marca ningún criterio completo todavía.

## T-07 — búsqueda, cursor y colecciones

2026-10-10. Se añadió búsqueda FTS5 sobre título/estilo/letra, paginación por cursor estable `(updated_at,id)`, filtro por colección y endpoints de colecciones para crear, listar y renombrar. La colección se valida por propietario al crear o mover una canción.

La regresión TDD de cursor/FTS/colección pasó **1/1** tras el RED inicial 404; la unidad completa de dominio queda en **8/8**, Ruff 0, y el contrato se volvió a exportar y comprobar con `openapi.json up to date`.

## T-08 — Docker web y smoke E2E

2026-10-10. Se añadió `apps/web/Dockerfile` reproducible con Next.js 16 sobre Node 22, el servicio `web` de Compose en `127.0.0.1:3000`, `scripts/e2e_stack.py` y la configuración/especificación Playwright de humo. Vitest quedó acotado a las pruebas unitarias propias y ya no intenta cargar tests de dependencias ni los specs E2E.

Verificación: `pnpm --filter web lint` verde, **222/222** tests Vitest, TypeScript verde; la imagen web compila dentro de Docker y el contenedor responde `200` en `/create`. La build local nativa sigue condicionada por el binario SWC de Windows, pero la build Linux del contenedor es la ruta de despliegue canónica.

T-08 continúa `en-progreso`: falta ejecutar el stack Compose completo con server/mock y el smoke de Playwright en el entorno de QA, además de revisión adversarial y cobertura oficial del delta.

## T-08 — Stack Compose integrado

2026-10-10. `scripts/e2e_stack.py up` construyó y arrancó `web`, `server` y `engine-mock` en Compose con los puertos locales cerrados a loopback. La imagen Linux del server incorporó las rutas T-07; el mock quedó accesible por su nombre interno.

Smoke de integración: `/health` del server respondió **200** y `/create` de la web respondió **200** mientras los tres contenedores estaban activos. Los contenedores de esta prueba se detuvieron explícitamente al terminar; no se tocó el engine ACE-Step que ya estaba ejecutándose.

La aceptación funcional E2E completa aún queda abierta: falta el flujo Playwright con sesión, generación y persistencia real, además de QA/revisión.

## T-08 — Smoke Playwright confirmado

2026-10-10. Tras instalar el navegador Playwright fijado localmente, el spec de humo contra el contenedor web pasó **1/1**: abre `/create`, comprueba el encabezado y navega a `/system`. El contenedor se detuvo después de la prueba.

## T-09 — Compositor web inicial y contrato de generación

2026-10-10. Se conectó `apps/web/app/create/page.tsx` con el parser compartido y el cliente de generación: editor de letra con resaltado de etiquetas, validación en vivo, contador aproximado de líneas/sílabas por sección, declaración de autoría siempre visible, toggle instrumental que conserva la letra, variantes 1–4, controles avanzados declarados por el perfil ACE-Step y atajo Ctrl+Enter. La petición conserva los parámetros en `params` y el server reenvía `style_prompt` como `params.style`; cuando no se indica semilla usa `0` para cumplir el contrato de variantes.

TDD: la regresión web pasó **224/224**, incluyendo envío de letra/declaración/variantes y el flujo instrumental (la letra queda visible pero se omite del payload). `pnpm --filter web lint` y `pnpm --filter web typecheck` pasan. La regresión focal de dominio pasa **9/9** y verifica que estilo y semilla llegan al job persistido. Se corrigió además la respuesta de reintento para devolver los campos de `Chain` reales (`generation_job_id`, `post_job_id`, `take_ids`, `beat_job_ids`).

T-09 sigue abierto: faltan E2E-02/E2E-03/E2E-11 contra Compose, integración visual completa con estimación/telemetría real, revisión adversarial y gate de cobertura. No se marca ningún criterio completo todavía.

## T-09 — E2E del compositor

2026-10-10. Se añadieron `apps/web/e2e/composer.spec.ts` con E2E-02 (payload de canción con letra, declaración y variantes) y E2E-03 (instrumental conserva la letra visible). Playwright pasó **2/2** contra la web en Docker; E2E-02 intercepta el backend para verificar el contrato del navegador porque `engine-mock` es CPU y el contrato de generación exige una tarea GPU. El stack `web/server/engine-mock` se detuvo después de la prueba; el engine ACE-Step preexistente no se tocó.

La generación real contra un engine GPU queda explícitamente pendiente para la aceptación de integración, junto con E2E-11, cobertura oficial y revisión adversarial.

## T-09 — Build Linux y E2E tras el editor completo

2026-10-10. La imagen `music-studio-web-t09:local` compila con Next.js/TypeScript dentro de Docker Linux. El contenedor aislado responde en `/create` y Playwright vuelve a pasar **2/2** sobre esa imagen, con la captura de contrato E2E-02 y la conservación de letra E2E-03. Vitest **224/224**, ESLint y `tsc --noEmit` siguen verdes después de añadir chips de estilo.

## T-09 - Estimacion, validacion compartida y E2E instrumental

2026-10-10. La estimacion de canciones reenvia ahora `lyrics` y `language` junto con el estilo y la duracion, tal como exige el `params_schema` de ACE-Step. El endpoint de generacion valida el parser compartido antes de crear la cancion o encolar el job, por lo que una etiqueta desconocida no deja datos durables ni llega al resolver. El editor distingue visualmente etiquetas reconocidas y desconocidas e inserta secciones `[Verse]`, `[Chorus]`, `[Bridge]`, `[Intro]` y `[Outro]` en la posicion del cursor.

TDD: la regresion de dominio pasa **11/11**, incluyendo captura de parametros de estimate y rechazo de `[chrous]`; la web pasa **224/224**, ESLint y TypeScript. `E2E-02`, `E2E-03` y `E2E-11` pasan **3/3** contra la imagen Linux aislada `music-studio-web-t09:local`. La pagina consulta `/api/system/info` y muestra la cola y si existe telemetria GPU; no afirma que la GPU este lista cuando el servidor no entrega mediciones.

T-09 continua `en-progreso`: sigue pendiente la ejecucion contra un engine GPU real, la cobertura oficial del delta y la revision/QA de cierre. El mock CPU no se usa como sustituto de esa aceptacion.

La comprobacion ampliada de contrato/sesiones/SSE/dominio queda en **116 passed, 1 warning** y `export_contracts.py --check` informa `engine-v1.json up to date` y `openapi.json up to date`. La cobertura oficial focal del modulo `domain_routes.py` es **69%** (579 sentencias, 180 sin cubrir) con esa seleccion; por eso el gate de cobertura del delta permanece abierto y no se marca T-09 como completado.

## T-10 - Feed de generaciones, visualizacion y acciones de job

2026-10-10. Se añadieron `apps/web/components/GenerativeViz.tsx`, `GenerationCard.tsx` y `GenerationFeed.tsx`. `GenerativeViz` dibuja 96 columnas, avanza únicamente hacia el progreso recibido, limita el `requestAnimationFrame` a 30 fps, pausa fuera del viewport y sustituye las barras por `peaks` al terminar. `GenerationCard` muestra las etapas reales, incorpora la etapa Modelo sólo cuando se solicita, conserva `code` y `job_id` en errores y ofrece reintento/cancelación. `GenerationFeed` agrupa jobs por canción/lote y ordena las variantes A/B.

La página Crear conecta el feed con el resultado de la generación, las acciones `/api/jobs/{id}/cancel|retry` y el cliente SSE existente para actualizar estado, etapa, progreso y errores sin inventar avance. Nuevos E2E-04/E2E-05 cubren visualización de 96 columnas y cancelación; junto con T-09 pasan **5/5** en la imagen Docker Linux. La unidad web pasa **229/229**, ESLint y TypeScript.

T-10 continúa `en-progreso`: faltan validar reconexión SSE en navegador contra Compose, tarjetas con resultados durables y cobertura oficial del delta. La evidencia actual usa respuestas interceptadas para aislar la UI y no acredita generación GPU ni audio real.

## T-11 - Biblioteca web inicial

2026-10-10. `apps/web/app/songs/page.tsx` deja de ser un estado vacío fijo y consulta la API tipada con búsqueda, cursor, skeletons, error recuperable, cuadrícula/lista y enlaces a la canción. `listSongs` y `deleteSong` comparten la sesión local; el layout conserva el estado vacío cuando la API responde sin canciones y permite enviar una canción a la papelera.

La suite web queda en **230/230** y el E2E-08 contra la imagen Docker Linux verifica carga, búsqueda y cambio de vista. El grupo E2E de T-09/T-10/T-11 pasa **6/6**. La preescucha autenticada y la vista de papelera/restauración completa siguen abiertas porque necesitan los endpoints/flujo de assets de T-12/T-14.

T-11 continúa `en-progreso`; no se marca completo hasta cubrir preescucha, miniaturas de generación y ciclo de restauración/purgado.

## T-14 - Estado del sistema visible en la web

2026-10-10. `apps/web/app/system/page.tsx` consume `/api/system/info` después de confirmar la salud del server y muestra cola, engines y disponibilidad de telemetría GPU, conservando un estado explícito cuando la respuesta no tiene forma válida o no hay mediciones. La consulta usa la misma sesión local y aborta al desmontar.

La unidad web mantiene **230/230**, ESLint y TypeScript. Esta capa deja de afirmar disponibilidad de GPU sin evidencia; los campos detallados de VRAM/RAM/disco, modelos verificados y descarga siguen pendientes de ampliar el DTO/endpoint de sistema.

T-14 continúa `en-progreso`.

## T-12 - Vista de canción y procedencia

2026-10-10. Se añadió `GET /api/songs/{song_id}/takes` con aislamiento por propietario y la página `/songs/[id]` con pestañas Audio/Letra, selección de toma, forma de onda accesible, versiones de letra y panel de procedencia exportable. El cliente tipado comparte la sesión local y valida la forma de las respuestas; el backend se exportó de nuevo y `openapi.json` quedó actualizado.

Verificación: la regresión focal de dominio pasa **12/12**, `export_contracts.py --check` informa los contratos al día, la build Linux de Next compila dentro de Docker y Playwright pasa **8/8** (incluido E2E-07) contra el stack Compose. La unidad web se mantiene en **230/230**, con ESLint y TypeScript verdes.

T-12 continúa `en-progreso`: falta la reproducción de audio autenticada, acciones completas de toma (master/valoración/linaje) y E2E-09 con datos persistidos; la cobertura oficial y la revisión/QA de cierre siguen abiertas.

## T-13 - Estado persistente del reproductor

2026-10-10. Se introdujo `PlayerProvider` en el shell global con cola persistida en `localStorage`, selección de toma, navegación anterior/siguiente, reordenación y eliminación. `PlayerDock` dejó el estado puramente deshabilitado: muestra la toma seleccionada, audio, seek accesible, ayuda de atajos (`?`, espacio y flechas) y panel de cola. La vista de canción conecta cada toma con la selección global del reproductor.

TDD: el test de persistencia empezó en RED por el módulo ausente y quedó GREEN; la suite web pasa **231/231**, ESLint y TypeScript pasan.

T-13 continúa `en-progreso`: faltan E2E-01/M-02 con navegación real y teclado, reproducción autenticada con assets reales y validación de la cola frente a takes hermanos.

Corrección de verificación T-13 — 2026-10-10: Playwright E2E-01 pasa **1/1** contra Compose tras corregir el selector del take; la toma seleccionada permanece visible al navegar de detalle a biblioteca y `?` abre la ayuda. La primera ejecución de la prueba falló por seleccionar la pestaña Audio con un selector ambiguo; no fue un fallo de producto. La suite completa actual queda en **9/9** al repetirla con el spec corregido.

## T-14 - Telemetría ampliada y contrato de sistema

2026-10-10. Se corrigió el cliente para consumir la ruta canónica `GET /api/system` (el cliente apuntaba a `/api/system/info`) y el DTO ahora expone GPU desde la salud del engine, RAM Linux, disco y modelos publicados con licencia, revisión, pesos y tareas verificadas. La página Sistema muestra estas mediciones sin inventar valores cuando faltan.

Verificación: server focal **12/12**, web **231/231**, ESLint y TypeScript verdes. T-14 sigue `en-progreso`: falta el CRUD/filtro de colecciones en la UI, descarga de modelos y E2E-10.

Corrección de verificación T-14 — 2026-10-10: `CollectionsPanel` permite listar, filtrar, crear y renombrar colecciones; la biblioteca permite mover cada canción y conserva el filtro por cursor. Playwright E2E-10 pasa **1/1** y la suite existente pasa **10/10** contra el stack Docker reconstruido. La regresión web queda en **232/232**, ESLint y TypeScript verdes.

T-14 continúa `en-progreso`: falta la descarga controlada de modelos desde Sistema y completar la lectura manual de VRAM/tope/licencias/hash sobre el hardware real.

## T-15 - Suite E2E parcial estabilizada

2026-10-10. Se añadió cobertura Playwright para E2E-01 (reproductor persistente/atajos) y E2E-10 (colecciones). La ejecución completa disponible de los specs actuales termina **10/10** en Docker Compose, tras corregir selectores ambiguos y el formulario anidado de la barra de biblioteca.

T-15 continúa `en-progreso`: todavía faltan los specs E2E-06/E2E-09 y API-01/API-02, tres ejecuciones consecutivas y el flujo real de generación/descarga con persistencia.

## T-12 - Análisis de beats en la vista de canción

2026-10-10. La vista de canción consulta `/api/takes/{take_id}/analysis` además de peaks; cuando existe `audio.beats`, dibuja marcas de beat en la forma de onda y muestra el BPM. El dato queda acotado a la toma autenticada y no se inventa si el análisis falta.

Verificación: contratos `engine-v1.json` y `openapi.json` al día, server focal **12/12**, web **232/232**. Se añadió E2E-09 para BPM/slider; requiere repetirlo contra la imagen Docker reconstruida junto con la suite completa.

Corrección de verificación T-15 — 2026-10-10: la suite Playwright actualizada pasa **13/13** en Docker Compose, incluyendo E2E-09 (BPM/beats), API-01 (Origin rechazado) y API-02 (OpenAPI). El stack se detuvo al finalizar.

T-15 continúa `en-progreso`: no se han ejecutado todavía tres repeticiones consecutivas ni E2E-06 de reinicio/reconexión; E2E-01 sigue usando fixtures de UI y no acredita generación GPU real.

Cierre de verificación repetible T-15 — 2026-10-10: tres ejecuciones consecutivas de la suite Playwright en el mismo stack Docker pasan **13/13**, **13/13** y **13/13**. No hubo fallos intermitentes; los contenedores se detuvieron después.

T-15 continúa `en-progreso` únicamente por E2E-06 de reinicio/reconexión y por la falta de una generación real con persistencia en E2E-01; los smoke API-01/API-02 ya están cubiertos.

## T-16 - Arranque Docker documentado

2026-10-10. `README.md` documenta el arranque reproducible del MVP con `scripts/e2e_stack.py`, la URL local, la parada del stack y el reinicio aislado del server. También deja explícito que Ollama sigue compartido en WSL2 y que ACE-Step real requiere sus pesos y el gate de VRAM.

T-16 continúa `en-progreso`: falta el recorrido desde clon limpio, el cierre de M0/T-13, la prueba M-01 con GPU real y M-03 de backup/restauración.

Corrección de sistema — 2026-10-10: `_system_info` ahora serializa descriptores mediante `model_dump`, por lo que también funciona con backends sintéticos que no exponen atributos de Pydantic directamente. La regresión focal vuelve a **12/12** y Ruff queda limpio.

Correcci�n de verificaci�n T-12/T-13 � 2026-10-10: la reproducci�n del reproductor resuelve el audio mediante `getTakeAudioBlob` con la sesi�n local y revoca las URLs Blob al cambiar de toma. La vista de canci�n a�ade acciones de valoraci�n, favorito y selecci�n de maestro, conectadas a los endpoints tipados. `pnpm --filter web lint`, `tsc --noEmit` y Vitest pasan **232/232**; la regresi�n server focal pasa **12/12** y Ruff queda limpio. La verificaci�n Docker de estos cambios queda pendiente de repetir.

Verificaci�n Docker de T-12/T-13 � 2026-10-10: se reconstruyeron las im�genes web/server/engine-mock despu�s de a�adir audio autenticado y acciones de take. Playwright pasa **13/13**, incluidos E2E-01, E2E-07, E2E-09 y API-01/API-02; los contenedores se detuvieron al terminar. La ejecuci�n cubre el contrato y la UI mock; a�n no sustituye la prueba con assets reales ni el engine GPU.

Avance de recuperaci�n M1 � 2026-10-10: el descriptor sint�tico del engine-mock acepta los par�metros que env�a el compositor (`style`, `lyrics`, `language`, controles de tempo/tono y pasos). `GenerationChains` admite el carril CPU s�lo cuando `engine_id == "mock"`; los engines reales siguen obligados al carril GPU. El feed de `/create` se hidrata desde `localStorage`, de modo que puede reconstruirse tras una recarga y volver a suscribirse al SSE.

Verificaci�n: `test_queue_chains.py` + `test_domain_routes.py` **28 passed**, Vitest **232/232**, ESLint, TypeScript y Ruff verdes. Playwright normal pasa **13/13** con E2E-06 omitido por requerir el arranque especial de recuperaci�n. La prueba dedicada de reinicio a�n no se cierra: el control automatizado del proceso Docker queda pendiente y no se registra como verde.

Avance de T-14 y seguridad de sesi�n � 2026-10-10: el panel Sistema incorpora �Descargar modelo de la VRAM�, conectado a `POST /api/system/unload`, muestra los MiB liberados y refresca las mediciones. El middleware CORS permite ahora `x-studio-session-token` en los preflight de la API; sin esa cabecera el navegador bloqueaba la acci�n aunque el endpoint respondiera correctamente.

Verificaci�n: prueba TDD nueva en rojo (400 antes del cambio) y verde despu�s; `test_security_cors_preflight_allows_session_token_for_api` **1 passed**; regresi�n web **233/233**, ESLint, TypeScript y Ruff verdes; build Docker Linux de web/server completada; Playwright contra Compose **13 passed, 1 skipped** (E2E-06 sigue condicionado a la prueba de reinicio); smoke de Sistema **1/1**, incluyendo descarga de VRAM. El fallo hist�rico `test_security_sse_allowed_origin_without_fake_endpoint` (401 frente a expectativa 404) queda fuera de este delta y no se atribuye al cambio.

T-14 sigue `en-progreso`: queda pendiente la comprobaci�n manual de VRAM/tope/licencias/hash sobre hardware real. T-15 sigue `en-progreso` por E2E-06 y generaci�n real con persistencia.

Correcci�n de E2E-06 y feed SSE � 2026-10-10: el feed de `/create` ya no sustituye las tarjetas de generaci�n por los jobs dependientes `post.audio` y `audio.beats` que llegan en el snapshot. Conserva los jobs que el navegador conoce y env�a sus `known_job_id` al endpoint SSE, por lo que una recarga puede recuperar tambi�n un job terminal. El escenario E2E-06 usa una ra�z de repositorio estable para reiniciar Compose desde Playwright y espera a que la cadena persistida termine antes de la recarga final.

Verificaci�n: `pnpm --filter web test` **233/233**, ESLint y TypeScript verdes; focal server de cola/dominio **28 passed** y preflight de sesi�n verde; Playwright normal **13 passed, 1 skipped**; Playwright dedicado con `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000` **1 passed (18,5 s)**. Esta evidencia prueba la recuperaci�n duradera y el snapshot tras reinicio; la transici�n visual en vivo sin una segunda lectura del snapshot queda como comprobaci�n manual pendiente.
Corrección T-05 de worker CPU y arbitraje — 2026-10-10: el runtime resolvía la raíz equivocada dentro del contenedor y no encontraba el FFmpeg fijado; además lanzaba dos `post.audio` antes de arbitrar una generación, agotando los slots CPU del engine-mock. `_default_cpu_service` ahora separa la raíz del checkout de la raíz del volumen `data_dir`, y `_run` arbitra engines antes de ocupar los slots de postproceso. Se añadieron regresiones TDD para ambas rutas y para el orden del ciclo.

Verificación: `tests/test_dispatcher_cpu_worker.py` **6 passed**; `ruff check app/queue/runtime.py tests/test_dispatcher_cpu_worker.py` limpio; `test_queue_chains.py` + `test_domain_routes.py` **28 passed**. En Compose, con SQLite limpia, E2E-06 pasa **1/1 (18,5 s)**; la generación mock termina y el worker crea el plan bajo `data/tmp/_server_cpu`. La prueba de publicación completa queda abierta porque el reinicio deliberado durante la custodia deja el `post.audio` en `CPU_CUSTODY_UNKNOWN`, como exige el protocolo, y no se cuenta como publicación verde.

La SQLite persistente del proyecto se restauró tras la prueba aislada y los contenedores de verificación quedaron detenidos. T-05, T-15 y el cierre M1 siguen `en-progreso`.


**Diagnostico adicional T-05 - 2026-10-10:** la primera cadena Compose de prueba uso `duration_s=0.1`; `audio-post` rechaza correctamente duraciones menores que su bloque LUFS (`ValueError: Audio must have length greater than the block size`), por lo que el hijo termina antes de lanzar FFmpeg (`registered_count=0`) y publica `AUDIO_INVALID`. No es un fallo de custodia. Una segunda repeticion con el stack activo encontro un descriptor SQLite obsoleto despues de intercambiar el fichero montado; se paro y recreo `server`/`engine-mock` y se restauro la base persistente desde `.cache/studio.sqlite.before-full-chain` (27 canciones, 42 jobs, 14 takes). La publicacion E2E con una duracion valida queda pendiente de una nueva ejecucion limpia; T-05 continua `en-progreso`.


**Verificacion nativa T-05 actualizada - 2026-10-10:** imagen `music-studio/server:m1-t01` reconstruida desde el checkout vigente. En contenedor aislado Linux, con FFmpeg fijado por SHA, `test_worker_actual_execution.py` pasa 3/3 y `test_worker_private_context_integration.py` pasa 23/23 (incluido el probe cross-device con `/proof` en tmpfs). En Windows, `test_queue_synthetic_composition.py` pasa 41/41 y `test_dispatcher_cpu_worker.py` 6/6. La prueba Compose de cadena completa no se acredita todavia: leer la SQLite WAL desde Windows mientras el contenedor escribe provoca `disk I/O error`; debe repetirse con el sondeo dentro del contenedor. T-05 continua `en-progreso`.

**Evidencia adicional T-05 - 2026-10-10:** en un volumen Docker ext4 y sin abrir lectores SQLite mientras el server escribe, la cadena API -> engine-mock -> `post.audio` completa `cpu_execution=finished`, `cleanup_state=confirmed`, intención de publicación `committed`, take `ready` y los cuatro assets (`master`, `listen`, `peaks`, `manifest`) quedan persistidos. Las lecturas SQLite concurrentes durante la transición `prepared` -> `running` pueden provocar un bloqueo transitorio y dejar el intento en `CPU_CUSTODY_UNKNOWN`; no se usa ese patrón como verificación. `audio.beats` se crea y queda `queued` para su despacho posterior. T-05 continúa `en-progreso` hasta acreditar también el análisis dependiente y una ejecución E2E sin sondeo concurrente.

**Diagnóstico de bloqueo T-05 - 2026-10-10:** la ejecución Docker del worker reveló `sqlite3.OperationalError: database is locked` al CAS `cpu_execution prepared -> running`, que se convertía en `CPU_CUSTODY_UNKNOWN` sin dejar visible la excepción. El runtime ahora comparte `PublicationCoordinator` entre `EventConsumer` y `CpuAudioService`, y conserva el traceback de cualquier worker CPU fallido. Regresión focal: `test_dispatcher_cpu_worker.py` + `test_queue_chains.py` **22 passed** y Ruff limpio. La publicación nativa aislada sigue verde; la cadena completa Compose permanece abierta hasta resolver la contención SQLite del runtime.

**Cierre técnico de la cadena CPU sintética — 2026-10-10:** la receta empaquetada del server se alineó con la entrada `master` de `audio.beats` y el engine-mock ahora devuelve el resultado estructurado (`analysis` + `stages`) que exige la persistencia de beats. TDD: el contrato de receta falló en RED antes de añadir la entrada y el test de resultado falló por ausencia de `result`; ambos quedaron GREEN después. Regresión server (composición sintética, persistencia de snapshots, cadenas, dominio y worker CPU): **76 passed**; engine-mock: **3 passed**; Ruff limpio.

Verificación Docker con volumen ext4 aislado y salida compartida: una generación nueva completó `music.song=succeeded`, `post.audio=succeeded`, `audio.beats=succeeded`; el take quedó `ready`, `cpu_execution=finished/confirmed`, la intención de publicación quedó comprometida, se conservaron los cuatro assets (`master`, `listen`, `peaks`, `manifest`) y se persistió `analysis(kind=beats, analyzer=mock, revision=synthetic-v1, bpm=120)`. T-05 sigue `en-progreso`: falta repetir la ejecución oficial del plan sin helpers temporales, pasar las puertas de revisión/QA y cerrar el resto de tareas M1.
**Avance T-09 — parámetros avanzados del compositor — 2026-10-10:** el formulario web ahora expone `vocal_language`, `shift` y `guidance_scale` para canciones ACE-Step y los incluye en `params` tanto en `POST /api/generations/estimate` como en la creación. La letra y el idioma también quedan explícitos dentro de los parámetros efectivos enviados al motor. TDD: la prueba de página falló al no existir los controles y quedó GREEN tras la implementación. Verificación: página focal **11/11**, suite web **234/234**, ESLint y TypeScript verdes. T-09 permanece abierto: faltan validación E2E completa, estado dinámico de cola/GPU y cierre de revisión/QA.
**Corrección T-09 de atomicidad de creación — 2026-10-10:** si la resolución del engine falla después de crear una canción o versión de letra para una petición nueva, el server ahora compensa esas filas dentro de una transacción y restaura la versión anterior cuando la canción ya existía. TDD: el test nuevo reproducía un borrador y una letra huérfanos en RED; quedó GREEN tras la compensación. Verificación: `test_domain_routes.py` **13 passed** y Ruff limpio.
- Evidencia E2E T-09 — 2026-10-10: stack Docker temporal web/server/engine-mock; pnpm --filter web exec playwright test apps/web/e2e/composer.spec.ts → 3 passed (E2E-02, E2E-03, E2E-11); python scripts/e2e_stack.py down ejecutado; ACE-Step persistente no se detuvo. T-09 continúa en-progreso hasta completar sus gates de revisión/QA.

- Evidencia E2E M1 — 2026-10-10: Compose web/server/engine-mock; pnpm --filter web exec playwright test → 13 passed, 1 skipped (14 tests). Verificados API-01/02, E2E-01/02/03/04/05/07/08/09/10/11 y smoke; E2E-06 queda omitido por su naturaleza de reinicio controlado. Stack detenido después, ACE-Step persistente intacto.

- Corrección T-05/T-15 de recuperación y arnés E2E — 2026-10-10: _retry_occupancy y Admission.reserve ya no cuentan jobs
unning/interrupted huérfanos sin JobAttempt durable; regresión TDD en 	est_queue_provenance_send.py RED/GREEN, suite de procedencia 35 passed. Compose parametriza STUDIO_DATA_ROOT; scripts/e2e_stack.py aísla E2E_RECOVERY en .cache/e2e-data para no contaminar data/. E2E-06 en stack aislado: 1 passed en 18.6s; ACE-Step persistente intacto.

- Estabilidad T-15 — 2026-10-10: tres ejecuciones independientes de pnpm --filter web exec playwright test con E2E_RECOVERY=1, MOCK_STAGE_DELAY_MS=5000 y .cache/e2e-data: cada ejecución 14/14 passed (API-01/02, E2E-01…E2E-11); tiempos 19.8s, 20.1s y 19.9s. Los stacks se detuvieron después de cada ejecución y no se tocó data/.

- Ajuste de verificación T-09 — 2026-10-10: se añadió pps/web/app/create/page.test.tsx para que el comando canónico pnpm --filter web test create encuentre una prueba real (1 passed). Regresión web completa posterior: 19 archivos, 235 tests passed; ESLint y TypeScript verdes.

**T-05 - limpieza de salida cruda y cadena Compose - 2026-10-10:** TDD RED reprodujo que el directorio `data/tmp/<attempt_id>/` del intento ganador permanecia tras una publicacion correcta. `CpuAudioService` ahora elimina unicamente los directorios cuyo `winning_attempt_id` esta acreditado en el plan y valida el prefijo antes de borrar. El foco Linux en Docker paso **26/26** (`test_worker_private_context_integration.py` + `test_worker_actual_execution.py`), incluido el caso cross-device con `/proof`; el intento previo sin `/proof` queda clasificado como fallo de arnes. La comprobacion Ruff aislada solo conserva tres avisos UP017 preexistentes en `execution.py`.

**T-05 - aceptacion de recorrido ext4 aislado - 2026-10-10:** con la imagen `music-studio/server:m1-t01` reconstruida y un volumen Docker ext4 limpio, la cadena API -> engine-mock -> `post.audio` -> `audio.beats` termino con los tres jobs `succeeded`, `cpu_execution=finished/confirmed`, take `ready`, cuatro assets publicados y `analysis(kind=beats, analyzer=mock, revision=synthetic-v1, bpm=120)` persistido. `verify_manifest` devolvio `valid=True`; el directorio del intento de generacion aceptado ya no existe. Esta evidencia usa el sondeo SQLite dentro del contenedor, sin lectores concurrentes desde Windows. T-05 continua `en-progreso` hasta la ejecucion oficial sin helpers temporales, revision/QA y almacenamiento persistente VHDX.
**T-06 server import boundary — 2026-10-10:** la suite directa de `apps/server` reproducía un fallo de colección en `test_local_sessions.py`: `local_sessions` importado como módulo superior no podía resolver `.event_dtos`. Se añadió una ruta explícita para ese modo de ejecución, conservando el import relativo del paquete. GREEN focalizado **55 passed**; bloque server dirigido (queue/domain/dispatcher/event DTO/session) **160 passed**; Ruff y formato del fichero conformes. No se declara cerrado T-06: faltan la verificación SSE completa, revisión y QA del hito.
**T-06 SSE CPU — 2026-10-10:** suite de `test_sse*.py` ejecutada con el intérprete gestionado y módulos server cargados en su frontera de paquete: **38 passed** en 31,74 s. La prueba cubre reenganche, buffer y frames; no sustituye el QA de integración Docker/E2E del hito.
**T-08 web integración CPU — 2026-10-10:** `pnpm --filter web test` **235 passed**, `pnpm --filter web lint` exit 0 y `pnpm --filter web build` exit 0 con Next 16.4/webpack; rutas `/`, `/create`, `/songs`, `/songs/[id]` y `/system` compilan. T-08 sigue en-progreso hasta QA/E2E y cierre Git.


**Verificaci?n E2E aislada reproducible ? 2026-10-10:** `E2E_ISOLATED=1 .venv\Scripts\python.exe scripts/e2e_stack.py up` reconstruy? web/server/engine-mock desde las im?genes actuales sin tocar `data/`. `pnpm --filter web exec playwright test` termin? **13 passed, 1 skipped** (E2E-06 requiere el modo recovery). Despu?s, con `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000`, la prueba dedicada `apps/web/e2e/recovery.spec.ts` termin? **1 passed en 18,5 s**. `scripts/e2e_stack.py down` retir? los contenedores. Esta evidencia cierra la repetibilidad del despliegue E2E mock y la recuperaci?n tras reinicio; no sustituye M-01 GPU real, M-02 visual ni M-03 backup/restauraci?n. T-15/T-16 siguen en-progreso por esos criterios y por la integraci?n Git.


**Diagn?stico de suite de cola CPU ? 2026-10-10:** el bloque dirigido de dispatcher/queue termin? **424 passed, 15 failed** en 179,85 s. Los fallos se separan as?: 12 casos de control nativo SQLite/WinEvent y una prueba ASGI con `tmp_path` externo (la pol?tica de confinamiento los rechaza), m?s dos fixtures de ocupaci?n que representan jobs hu?rfanos sin `JobAttempt` durable y una fixture de `audio.beats` sin su entrada requerida. La implementaci?n vigente rechaza deliberadamente esos estados hu?rfanos y exige entradas declaradas; no se relaja el protocolo para hacerlos verdes. T-04/T-05 no se cierran con esta suite; queda pendiente reparar fixtures/arn?s o ejecutar el bloque dentro del entorno Linux/Compose que acredita cada control nativo.


**Integraci?n del paquete storage-guard ? 2026-10-10:** la suite del paquete no se pod?a coleccionar desde el workspace ra?z porque `packages/storage-guard` no estaba declarado en `pyproject.toml`; el fallo era `ModuleNotFoundError: studio_storage_guard`. Se a?adi? como miembro local y se regener? `uv.lock` sin dependencias externas nuevas. Verificaci?n can?nica: `uv run --frozen --package studio-storage-guard pytest packages/storage-guard/tests -q` ? **90 passed, 42 skipped** en Windows (los skips son probes Linux-only). La pol?tica `scripts/storage.py` conserva su modo PLAN-ONLY y su suite pasa **42/42**; no se aprovision? ni mont? VHDX. T-05 contin?a abierto por el executor/mount/QA persistente.


**Gate de almacenamiento en el arranque del server ? 2026-10-10:** `STUDIO_STORAGE_UUID` es opcional y tipado; cuando se declara, el lifespan verifica `studio_storage_guard.verify_root(..., "server")` antes de configurar logs o migrar SQLite, conserva la lease durante el proceso y la cierra al detenerse. TDD: la regresi?n comprueba que un montaje no acreditado corta el arranque antes de ambos efectos. Verificaci?n focal **2 passed**, regresi?n server de settings/OpenAPI/lifespan **40 passed, 3 warnings**, Ruff y formato verdes. El modo por defecto sin UUID permanece compatible con E2E; no se ha creado ni montado VHDX.


**Imagen server con storage-guard ? 2026-10-10:** el primer build mostr? que declarar el paquete en `server/pyproject.toml` no bastaba: el Dockerfile no copiaba sus fuentes y la imagen no lo instalaba. Se a?adi? la copia del workspace y se reconstruy? `music-studio/server:m1-t01`; `uv sync --frozen` instal? `studio-storage-guard==0.1.0` desde el workspace y el build termin? correctamente.


**Regresi?n E2E tras gate de storage ? 2026-10-10:** con `E2E_ISOLATED=1` se reconstruyeron las im?genes actuales (incluido `studio-storage-guard`), se ejecut? Playwright y termin? **13 passed, 1 skipped**; el skip es E2E-06 por requerir `E2E_RECOVERY=1`. El stack se detuvo y el ?rbol aislado se elimin?.


`uv lock --check --offline` y la importaci??n desde `uv run --frozen --all-packages` quedan verdes tras la integraci??n de `studio-storage-guard`.


**Integración del guardarraíl de almacenamiento en engines — 2026-10-10:** engine-common verifica STUDIO_STORAGE_UUID con erify_engine_roots antes de ceder el lifespan a FastAPI y mantiene los descriptores abiertos hasta el apagado. La lease se cierra incluso si el cleanup del engine falla. El paquete admite Python 3.11-3.12; se añadió a los locks de root y ACE-Step y los Dockerfiles de ACE-Step/analysis copian la fuente al contexto. TDD: la prueba de arranque falló en RED antes del gate y quedó GREEN después. Verificación: pps/engines/common/tests **27 passed**, Ruff limpio y uv lock --check --offline conforme. El lock de analysis necesita regeneración online por sus dependencias Git fijadas; no se declara imagen analysis reconstruida.


**Verificación de imágenes tras integrar storage-guard — 2026-10-10:** docker compose --profile studio build server engine-mock terminó correctamente e instaló studio-storage-guard==0.1.0 en ambos entornos. docker build -f apps/engines/analysis/Dockerfile y docker build -f apps/engines/acestep/Dockerfile también terminaron correctamente; ambos locks incluyen el paquete y sus contenedores importan el engine sin inicializar CUDA. Contratos: export_contracts.py --check conforme. Regresiones repetidas: storage-guard **90 passed, 42 skipped**, server storage/OpenAPI **40 passed, 3 warnings**, engine-common CPU **27 passed**. ledger-lint mantiene **0 incoherencias** y un aviso histórico de codificación no UTF-8 limpia en 	asks.md.


**E2E posterior a las imágenes nuevas — 2026-10-10:** E2E_ISOLATED=1 ... scripts/e2e_stack.py up reconstruyó web/server/engine-mock con storage-guard instalado y la suite Playwright terminó **13 passed, 1 skipped** en 2,8 s. El stack se detuvo en el bloque inally; la red Docker residual en uso no dejó contenedores del escenario activos y la raíz aislada no escribió en data/.


**E2E-03 actualizado - 2026-10-10:** el escenario de compositor ahora cubre tambien una etiqueta desconocida ([chrous]): el editor la resalta como invalida y el boton Generar queda deshabilitado. Con las imagenes Docker reconstruidas, ambos casos de E2E-03 pasan **2/2** en 1,2 s; el stack aislado se detuvo y no se escribio en data/.

**T-09 contrato efectivo del modelo - 2026-10-10:** `/api/system` publica `params_schema` y `features` por tarea; el formulario selecciona el modelo verificado y filtra/inhabilita controles que el esquema o la verificación no permiten. El idioma principal pasa a ser editable y el `model_id` de fallback ACE-Step se usa tanto en estimacion como en creacion. TDD/regresion: pages focal **13 passed**, web completa **237 passed**, server dominio **13 passed**, lint/typecheck verdes. T-09 permanece en-progreso por QA/revision formal y validacion GPU ACE-Step.

**T-09 integracion Docker tras esquema dinamico - 2026-10-10:** las imagenes web/server/engine-mock se reconstruyeron con el contrato de capacidades. Playwright aislado: primera ejecucion sufrio dos `ECONNRESET` durante el arranque concurrente; se repitio sin reiniciar el stack y la suite estabilizada termino **14 passed, 1 skipped** (incluido API-01/API-02). El contenedor persistente ACE-Step no se detuvo.

**T-09 fallback ACE-Step cerrado - 2026-10-10:** cuando el catalogo no responde, el formulario aplica las capacidades conocidas de `ace-step-1.5-turbo` y deshabilita `guidance_scale`, BPM, tonalidad y negative prompt no verificados; no los envia al resolver. Los parametros compatibles (idioma vocal, shift, compas y pasos) siguen disponibles. La prueba focal queda en **13 passed**.

**T-09 validacion final del fallback - 2026-10-10:** con las imagenes reconstruidas desde el estado final, Playwright tras esperar el healthcheck termino **14 passed, 1 skipped**; los dos `ECONNRESET` de la primera ejecucion quedaron clasificados como carrera de arranque y no reaparecieron. Stack temporal eliminado y ACE-Step persistente intacto.

**T-09 revision 3 cerrada - 2026-10-10:** el catalogo solo selecciona tareas verificadas de modelos locales, comerciales y con licencia; el cliente aplica limites/minimum/maximum/pattern del esquema y bloquea el envio con mensaje visible si un valor avanzado no es valido. Test focal **13 passed**; la revalidacion RO no encontro gaps B-02/B-03, quedaban estos dos ajustes de robustez.

**T-09 verificacion de robustez - 2026-10-10:** seleccion de modelos restringida a proveedor local, uso comercial y licencia presente; validacion de limites/patrones en cliente con mensaje y boton bloqueado. Con imagenes reconstruidas desde este estado: Playwright **14 passed, 1 skipped**, stack detenido; el ACE-Step persistente permanece intacto.


**T-11 filtros y scroll infinito - 2026-10-10:** la biblioteca incorpora filtros de estado, modelo, favoritas, etiqueta y rango de fechas; el server valida y aplica los filtros con parametros OpenAPI tipados. Se anade sentinel IntersectionObserver con guardia contra cargas duplicadas y boton de respaldo. RED/GREEN server: 17 passed; web: 240 passed; lint, TypeScript y Ruff verdes.

**T-11 correcciones de revision - 2026-10-10:** se tipan tambien cursor/limit de la papelera en OpenAPI; la portada solo es enlace en biblioteca activa y no abre canciones borradas; las cargas de biblioteca llevan identificador de solicitud para descartar respuestas obsoletas. La preescucha invalida peticiones al salir y detiene el audio al terminar. Focal web 16/16 y suite completa 240/240; server 17/17.


**T-11 regresion de accesibilidad - 2026-10-10:** se elimino la etiqueta redundante de la portada para que el enlace del titulo tenga un nombre accesible unico. Tras reconstruir Docker, Playwright pasa 15/15 pruebas activas y 1 queda omitida por E2E-06 condicionado a recovery.


**Correccion de trazabilidad T-04/T-05 - 2026-10-10:** la nota historica que afirmaba que todos los `running/interrupted` huerfanos quedaban excluidos es demasiado amplia. La implementacion vigente cuenta reservas `running`, reservas GPU `interrupted` y trabajos de soporte como ocupacion segura; solo excluye huerfanos CPU `interrupted` sin intento durable. La semantica actual queda demostrada por 4 casos focales y por las suites 173/565 reportadas arriba.


**E2E-06 oficial de recovery - 2026-10-10:** se reconstruyo y levanto el stack aislado con `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000`; el spec oficial `apps/web/e2e/recovery.spec.ts` paso **1/1 en 22,0 s**, incluyendo reinicio real del server y recuperacion del job hasta `Lista`. `scripts/e2e_stack.py down` retiro web/server/engine-mock; el ACE-Step persistente permanecio activo. T-05/T-15 siguen en-progreso por revision/QA formal, storage VHDX y el resto de criterios M1.


**Correccion y cierre E2E T-15 - 2026-10-10:** la prueba completa se ejecuto tres veces consecutivas con `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000`; cada corrida termino **16/16 passed** (API-01/02, E2E-01..E2E-11 y recovery). La primera corrida encontro una ambiguedad real del locator de coleccion (`.song-card select` con dos canciones); se corrigio el spec para seleccionar la primera tarjeta y las tres corridas posteriores pasaron. La nota anterior que describia E2E-06 como fallido queda superada por esta evidencia. El stack se detuvo tras la tercera corrida y ACE-Step persistente quedo intacto. T-15 mantiene `en-progreso` hasta revision adversarial/QA formal y cierre Git.


**Entry point E2E T-15 - 2026-10-10:** el launcher seguro de pnpm acepta ahora `pnpm --filter web exec playwright ...` junto a `tsc` y `vitest`; conserva la validacion de opciones/raiz y pasa su prueba RED/GREEN (`test_preserves_allowed_argv` 10/10, Ruff limpio). El comando documentado en README ya es ejecutable desde el toolchain gestionado.


Evidencia adicional T-15 - 2026-10-10
- La ruta can??nica del wrapper local queda verificada con `pnpm --filter ./apps/web exec playwright -- test`: 15 pruebas pasaron y 1 qued?? omitida por dise??o (E2E-06 reinicia el servidor dentro del caso).
- La cach?? de Playwright se instal?? bajo `.cache/web-runtime/local-appdata` y no se us?? el perfil del usuario.
- El stack temporal se detuvo al terminar; el contenedor persistente `music-studio-engine-acestep-1` permaneci?? activo.


Correccion de exportacion de contratos - 2026-10-10
- `scripts/export_contracts.py` resuelve el directorio por defecto desde su `__file__` al ejecutar, de modo que `--check` y la regeneracion funcionan tambien en un checkout aislado y no quedan atados a la raiz importada.
- RED reproducido en `packages/engine-contract/tests/test_contract.py::test_export_cli_generates_and_detects_stale_contract`: devolvia 0 sobre una salida temporal. GREEN: **15 passed** en el fichero completo; Ruff y `uv run scripts/export_contracts.py --check` limpios.


Verificacion SSE y namespace de tests - 2026-10-10
- El bloque de eventos (`test_sse_bus.py`, `test_sse_frames.py`, `test_sse_http.py`, `test_event_dtos.py`, `test_event_snapshot.py`, `test_dispatcher_events.py`) pasa **168 tests** desde el proyecto server.
- `test_event_dtos.py` usaba el import legado `event_dtos`; se alinea con `app.event_dtos` para que la suite sea reproducible bajo el empaquetado actual. Ruff del test limpio; el server completo conserva avisos historicos de estilo fuera de esta unidad.


Regresion CPU T-05 reproducible - 2026-10-10
- El bloque portable `test_dispatcher_cpu_worker.py`, `test_queue_chains.py` y `test_worker_recovery_regression.py` pasa **25/25** en Windows.
- La ejecucion conjunta que incluye `test_worker_actual_execution.py` y la integracion privada deja **25 pasadas**, pero mantiene 22 errores/4 fallos porque esos casos exigen Linux real, libc `renameat2` y `/proof`; no se reclasifican como fallo de producto ni se relaja el gate.


Correccion de receta T-16 - 2026-10-10
- README y `scripts/e2e_stack.py smoke` usan ahora el entorno gestionado y la sintaxis verificada `pnpm --filter ./apps/web exec playwright -- test`; se elimina la receta que fallaba por no separar los argumentos de Playwright.
- `scripts/e2e_stack.py --help` responde correctamente y el stack persistente de ACE-Step no se toca.


2026-10-10. T-15: el launcher canonico ya conserva solo E2E_RECOVERY, E2E_ISOLATED y MOCK_STAGE_DELAY_MS. RED reprodujo el skip del recovery por perdida de entorno; GREEN focal 1 passed. E2E-06 canonico con pnpm: 1 passed en 19.8s. El stack temporal se detuvo y solo ACE-Step persistente quedo activo. T-15 sigue en-progreso: falta ejecutar la publicacion sobre ext4/VHDX y la QA/revision de cierre.



2026-10-10. T-05: se implementaron scripts/fetch_storage_linux.py y tests/test_fetch_storage_linux.py. TDD 6 passed; ruff limpio. Importacion real de los 30 DEB desde el bundle existente a root aislado t05-storage-acq5 y --check pasan. En contenedor Bookworm fijado, qemu-img 7.2.22 y mke2fs 1.47.0 ejecutan sin red; raw ext4 64 MiB + e2fsck + conversion VHDX + qemu-img info pasan. Evidencia: testing/t05/storage-acquisition-runtime1.md. No se reemplaza el destino oficial existente ni se cierra T-05: siguen pendientes FD/handle Windows, attach/mount persistente y QA.


2026-10-10. Barrera adicional en fetch_storage_linux.py: cada paquete debe aportar usr/share/doc/<package>/copyright y se valida su hash durante --check. Importacion final t05-storage-acq6 y --check pasan; runtime Docker vuelve a probar qemu-img/mke2fs, ext4, e2fsck y VHDX con dirty-flag=false.


**Verificación T-07 OpenAPI — 2026-10-10:** se corrigieron los esquemas de las respuestas de colecciones, restauración de canciones/takes y versiones de letra en `apps/server/app/domain_routes.py`; se regeneró `packages/contracts/openapi.json` y `apps/web/lib/generated/api.d.ts`. TDD: RED `test_openapi_audio_and_take_shapes` falló con `KeyError: properties` al recibir `{}`; GREEN focal 1/1. Verificación adicional: `test_domain_routes.py` 18/18, `scripts/export_contracts.py --check` conforme, `pnpm --filter ./apps/web run gen`, TypeScript sin errores y Vitest 247/247. T-07 sigue en-progreso hasta revisión adversarial, QA y E2E completo.

**E2E T-07/T-08 — 2026-10-10:** stack Compose aislado (`E2E_ISOLATED=1`) reconstruido y Playwright ejecutado contra web/server/engine-mock: **15 passed, 1 skipped**. E2E-01/02/03/04/05/07/08/09/10/11 y API-01/02 verdes; E2E-06 queda omitido por la limitacion conocida de publicacion atomica sobre bind Windows 9p/DrvFS (`renameat2 EINVAL`) y requiere el almacenamiento ext4/VHDX del diseño ADR-0069. El build Docker de web/server/mock tambien termino correctamente. No se cierra T-07 ni T-15 mientras falte E2E-06 y la QA/revision formal.

**T-07 contrato completo — 2026-10-10:** la revisión fresca detectó tres desajustes de OpenAPI y se corrigieron con TDD. RED ampliado: `list_song_takes` anunciaba `next` inexistente; Song omitía `negative_prompt`, `language`, `tags`, `notes` y `current_lyrics_version_id`; Take/Asset omitían timestamps, `role` y `bytes`; la creación de colección publicaba un 200 implícito. GREEN: `test_openapi_audio_and_take_shapes` 1/1, dominio 18/18, Ruff limpio, exportación y generación tipada conformes; web TypeScript, lint y Vitest 247/247 verdes. Revisión fresca final pendiente; T-07 sigue en-progreso.

**Revisión fresca T-07 — intento 2 — 2026-10-10:** Lente A sin gaps en el contrato OpenAPI tras el arreglo. Colecciones solo 201, restauración Song/Take completa, lista de takes `{items}`, Song/Take/Asset coinciden con las respuestas reales y audio 200/206 binario correcto. Evidencia del revisor: dominio 18/18, focal OpenAPI 1/1, exportación conforme y páginas web 15/15. QA E2E posterior en Compose aislado: API-01/API-02 y E2E-07 3/3. T-07 conserva estado en-progreso hasta QA formal de la tarea y cierre del hito.

**Recovery E2E posterior a T-07 — 2026-10-10:** con `E2E_RECOVERY=1`, `E2E_ISOLATED=1` y `MOCK_STAGE_DELAY_MS=5000`, se reconstruyeron las imágenes actuales y `recovery.spec.ts` pasó **1/1 en 19,3 s**. API-01/API-02 y E2E-07 ya habían pasado 3/3 en la misma imagen. El stack se retiró y solo ACE-Step persistente quedó activo. Esta ejecución confirma la recuperación mock; T-15 aún conserva la revisión/QA formal y la publicación CPU sobre storage persistente como criterios de cierre.

**Verificación actual T-06 — 2026-10-10:** el bloque dirigido de eventos y sesión HTTP (`test_dispatcher_events.py`, `test_event_dtos.py`, `test_event_snapshot.py`, `test_session_http.py`, `test_sse_bus.py`, `test_sse_frames.py`, `test_sse_http.py`) terminó **250 passed en 52,49 s**, sin fallos ni skips, con el intérprete gestionado y `--basetemp=.cache/pytest/t06-current`. La evidencia cubre bus, sobres, snapshots, sesión HTTP, frames, endpoint SSE y dispatcher desde el árbol actual; T-06 sigue `en-progreso` hasta revisión adversarial y QA de integración Docker/E2E.

**T-12 — marcadores de beat — 2026-10-10:** `Waveform` ahora convierte cada tiempo válido de `audio.beats` en una región estrecha, coloreada y no editable mediante `RegionsPlugin`; descarta tiempos negativos, NaN y fuera de duración, y reacciona a cambios de beats. RED: el test nuevo obtenía 0 regiones; GREEN focal **2/2**. Suite web **248/248**, TypeScript y ESLint verdes. Evidencia: `testing/t12/waveform-beat-regions.md`. T-12 sigue `en-progreso` hasta QA visual y revisión formal.

**T-05 — executor offline ext4/VHDX — 2026-10-10:** se implementaron `scripts/storage_offline.py` y `studio_storage_guard.receipt.StorageReceipt`. El executor reserva sólo `.cache/dev-cycle/storage-<operation_id>`, rechaza reservas/finales existentes, ejecuta las cinco herramientas fijadas en Docker y deja recibo monotónico hasta `vhdx_verified`. TDD: RED por módulo ausente; GREEN **8 tests** de plan/ejecucion y **3** del recibo; paquete storage-guard **93 passed, 42 skipped**, Ruff limpio. Ejecución real de 64 MiB con la imagen privada fijada: mke2fs, e2fsck, qemu-img convert -n e info exit 0; raw 67108864 B y VHDX 75497472 B con hashes en `.cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV/receipt.json`. El VHDX final no existe: promoción, attach/mount, preflight y E2E persistente siguen pendientes.




**T-05 ? publicaci?n custodiada ? 2026-10-10:** `scripts/storage_publish.py` copia ?nicamente el VHDX respaldado por un recibo `vhdx_verified` a un archivo creado bajo `WindowsCustody`; sella SHA-256 y usa promoci?n nativa sin reemplazo. RED por m?dulo ausente; GREEN **3/3**; junto con custodia Windows **17/17** y Ruff limpio. Ejecuci?n real public? `data/_storage/studio-data.vhdx` y avanz? el recibo a `published`; `qemu-img info` del destino devuelve VHDX v?lido y `dirty-flag=false`. Attach/mount WSL, preflight ext4 y E2E persistente siguen pendientes.


**T-05 ? operador WSL attach/mount ? 2026-10-10:** `scripts/storage_attach.py` implementa la secuencia fail-closed sobre el VHDX publicado: `wsl --mount --vhd --bare`, comparaci?n `lsblk` antes/despu?s, selecci?n ?nica por UUID ext4, `mount`, `findmnt`, `blkid` y rollback privado (`umount` + `wsl --unmount`) ante error. RED por m?dulo ausente; GREEN **5/5**; publicaci?n + attach + custodia **23/23** y Ruff limpios. En la sesi?n no elevada, `--execute` devuelve `NEEDS_ADMIN` sin tocar WSL; el montaje real y el recibo `attached/validated` quedan condicionados al privilegio de plataforma.


**T-05 ? gate UUID en Compose ? 2026-10-10:** `docker-compose.storage.yml` exige `STUDIO_STORAGE_UUID` en los cuatro consumidores persistentes y conserva `create_host_path: false`. RED por ausencia del contrato; GREEN **1/1** y `docker compose ... config -q` exit 0 con ra?z/UUID de prueba. El override sigue sin arrancar hasta que el operador WSL acredite el mount ext4.


## 2026-10-10 - T-16 README reproducible

Se reemplazo el remoto generico por `https://github.com/daycry/music-studio.git` y se documentaron bootstrap, stack mock, VHDX ext4, attach WSL2 elevado, override `docker-compose.storage.yml`, UUID y Ollama fuera de Docker. RED/GREEN de `tests/test_readme_startup.py`: 1/1; `git diff --check` limpio. Evidencia en `testing/t16/readme-startup.md`. T-16 sigue en-progreso por M-01 GPU real, M-03 backup/restauracion y cierre formal.


**Verificacion de cadena y contratos T-04 - 2026-10-10:** `test_queue_chains.py`, `test_queue_backend.py`, `test_queue_inputs.py`, `test_queue_resolver.py`, `test_queue_references.py` y `test_dispatcher_events.py` pasan **122/122 en 23,34 s** (un warning de serializacion Pydantic en el mock). Cubre cadena atomica de variantes, referencias estables, catalogo/verificacion, contrato EngineBackend/HTTP y eventos; no sustituye la QA completa, el almacenamiento persistente ni M-01 GPU.


**Regresion worker CPU con entorno de cobertura - 2026-10-10:** con `COVERAGE_FILE` dentro de `.cache`, `test_dispatcher_cpu_worker.py`, `test_worker_contracts.py`, `test_worker_snapshots.py`, `test_worker_publication_invariants.py` y `test_worker_planning.py` terminan **134 passed en 37,14 s**. El primer intento sin `COVERAGE_FILE` fallo solo por la variable ambiental requerida por la prueba de consultas; se conserva como diagn?stico, no como fallo de producto. Esta ejecuci?n no sustituye la integraci?n persistente E2E ni M-01.


**Fix del arnes T-05 - 2026-10-10:** `test_worker_snapshots.py` ya no exige `COVERAGE_FILE` del entorno; cuando falta, escribe los artefactos de proposito SQL bajo `.cache/pytest/sql-purpose`. RED reproducida con `KeyError: COVERAGE_FILE`; GREEN focal sin variable **12/12** y regresion worker completa sin variable **134/134 en 37,27 s**. El cambio queda limitado al arnes de pruebas y no modifica el contrato del producto.


**Regresion T-02 de snapshots/backup - 2026-10-10:** `test_persistence_t02.py -k "backup or snapshot"` pasa **14 passed, 1 skipped, 20 deselected en 6,29 s**. Cubre roundtrip de snapshot, WAL/FTS y restauracion valida; no sustituye M-03 manual sobre la biblioteca real, que sigue pendiente.


**Gate de startup persistente - 2026-10-10:** `test_storage_startup.py`, `test_storage_preflight.py` y `test_storage_compose.py` pasan **31/31 en 0,88 s**. El arranque rechaza ausencia de mount/UUID y no crea rutas vacias; sigue pendiente ejecutar el attach nativo y el E2E sobre el volumen real.


**Correccion de namespace de sesiones - 2026-10-10:** la coleccion completa de `apps/server/tests` fallaba antes con `ModuleNotFoundError: local_sessions`. `test_local_sessions.py` ahora importa el paquete instalado `app.local_sessions`; focal **55/55** y Ruff verde. La coleccion completa queda en **1819 tests collected** sin errores.


**T-04 ? correcci?n de ocupaci?n durable en retry/recovery (2026-10-10):** la revisi?n fresca encontr? que `Retry.reserve` y `Recovery.other_active` no compart?an el predicado de ocupaci?n del runtime. TDD RED reprodujo el bloqueo por job CPU `interrupted` hu?rfano y por fila borrada; GREEN extrajo `occupancy_filters(owner_id)` y lo reutiliz? en admisi?n, runtime, retry y recovery. Focales: **2 passed**; regresiones retry+recovery **122 passed en 80,25 s** y admission+scanning **156 passed en 109,88 s**; Ruff limpio. T-04 contin?a `en-progreso`: quedan GPU/ACE real, storage/recovery persistente y revisi?n/QA formal. Evidencia: [`testing/t04/retry-recovery-occupancy-fix1.md`](testing/t04/retry-recovery-occupancy-fix1.md).

**T-04 reintento manual actual - 2026-10-10:** `uv run --package server pytest apps/server/tests/test_queue_manual_retry.py -q` termina **33 passed en 10,65 s**. Confirma la selección de takes fallidos, autenticación del fallo `post.audio`, revalidación bajo writer, reclamación concurrente y rollback; no cierra los criterios de GPU, almacenamiento persistente ni QA formal.


**E2E-06 aislado actualizado ? 2026-10-10:** con `E2E_ISOLATED=1`, `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000`, el spec dedicado `apps/web/e2e/recovery.spec.ts` ejecutado con un worker pasa **1/1 en 18,5 s**; el stack se retir?. La recuperaci?n mock queda verificada. El criterio persistente sobre VHDX/ext4 sigue abierto y no se sustituye por bind Windows.


## Avance de correcciones web tras revisi?n fresca ? 2026-10-10

- **T-08/T-09:** `GenerativeViz` respeta `prefers-reduced-motion` tambi?n para su `requestAnimationFrame`; el compositor oculta controles avanzados que el descriptor del modelo no declara. `pnpm --filter web lint` y `typecheck` pasan.
- **T-10:** `createFeedJobs` expande `take_ids` a una tarjeta por variante, mantiene el job padre para SSE/acciones, recupera peaks publicados y muestra la etapa de modelo. Focales T-10 verdes; la regresi?n web completa queda en **255/255**.
- **T-12/T-13:** cabecera de canci?n con estado/BPM, Waveform estable durante seek, atajos V/L/C/B y Shift+flechas, protecci?n de campos editables y salto directo entre tomas hermanas A/B. Focales **7/7**; typecheck y lint verdes.
- **T-14:** Sistema muestra engines con estado y pesos con SHA-256/tama?o; la descarga controlada de modelos y la comprobaci?n manual de hardware siguen abiertas.

Estas correcciones no cierran las tareas: siguen pendientes el seed reproducible de E2E, descarga de modelos, M-01 GPU real, M-03 backup/restauraci?n, montaje VHDX/ext4 elevado y revisi?n/QA formal.


**Verificaci?n de integraci?n web posterior ? 2026-10-10:** `pnpm --filter web test` **255/255**, `pnpm --filter web lint` exit 0, `pnpm --filter web typecheck` exit 0 y `pnpm --filter web build` exit 0 (Next.js webpack, rutas `/`, `/create`, `/songs`, `/songs/[id]`, `/system`).


## T-08/T-15 ? seed E2E reproducible y suite completa ? 2026-10-10

Se a?adi? `apps/server/scripts/seed_e2e.py`, un seed idempotente que usa exclusivamente la API autenticada del server y el origen web permitido; crea o reutiliza la colecci?n y canci?n `E2E` sin abrir ni escribir SQLite desde el host. `scripts/e2e_stack.py up` lo ejecuta autom?ticamente s?lo cuando `E2E_ISOLATED=1` o `E2E_RECOVERY=1`, sobre `.cache/e2e-data`.

TDD del seed: **3 passed**, Ruff limpio. Verificaci?n integrada: Compose aislado reconstruido, seed ejecutado dos veces con los mismos IDs, y Playwright completo con `E2E_RECOVERY=1`/`MOCK_STAGE_DELAY_MS=5000`: **16/16 passed en 23,4 s** (E2E-01..E2E-11, API-01/API-02 y recovery). El stack temporal se detuvo y `music-studio-engine-acestep-1` no se detuvo.

T-08/T-15 permanecen `en-progreso`: a?n faltan revisi?n/QA formal, generaci?n ACE-Step real con persistencia y el gate VHDX/ext4.


**T-15 cierre de repetibilidad ? 2026-10-10:** con el seed integrado y `E2E_RECOVERY=1`, `MOCK_STAGE_DELAY_MS=5000`, tres ejecuciones consecutivas de la suite completa terminaron **16/16**, **16/16** y **16/16** (23,7 s; 23,0 s; 23,4 s). Incluyen E2E-06 recovery, E2E-01?E2E-11 y API-01/API-02. Los contenedores se retiraron tras la tercera ejecuci?n. El estado de T-15 permanece `en-progreso` hasta revisi?n/QA formal y la prueba persistente VHDX/ext4.

**M-01 / ACE-Step real - 2026-10-10:** se reconstruyo `engine-acestep` desde el checkout actual (la imagen previa era `m0-t19-preflight`) y se ejecuto `tests/test_gpu.py -m gpu` dentro de Docker con Ollama vacio y 1.163/12.227 MiB de VRAM usados antes de la carga. Resultado: **1 passed en 157,02 s**. La toma produjo WAV FLOAT estereo 48 kHz de 30,0 s (1.440.000 muestras, RMS 0,1565); telemetria `bf16`, revision `19671f406d603126926c1b7e2adc169acbcade22`, tope 10.268,31 MiB, pico 7.806,80 MiB y `spilled=false`; `unload` termino el proceso hijo y la salud posterior informo `loaded=null`. Evidencia detallada: [testing/m01-gpu-real-2026-10-10.md](testing/m01-gpu-real-2026-10-10.md). La escucha humana de la toma queda pendiente, por lo que no se marca M-01 completo ni se cierran T-04/T-05/T-16.

**M-03 backup tecnico - 2026-10-10:** en una raiz privada nueva, sin borrar la base viva, `backup()` y `restore_backup()` completaron el roundtrip de `data/db/studio.sqlite`. La restauracion nueva paso `PRAGMA integrity_check` (`ok`), `foreign_key_check` (0 errores) y contuvo 39 tablas; backup de 2.228.224 bytes con SHA-256 `bbab547954b1bb22468941693ce769032e30e97a0181549a35a8a7b7e474e6a0`. Evidencia: [testing/m03-backup-current-2026-10-10.md](testing/m03-backup-current-2026-10-10.md). M-03 manual sobre biblioteca persistente y manifiestos reales sigue pendiente.

**M-03 saneamiento de staging - 2026-10-10:** `scripts/verify_manifest.py data/songs/` detecto dos manifiestos bajo tres directorios `.pending-*` huerfanos (`PRIVATE_CONTEXT_INVALID`). Se comprobo que no habia server/worker activo ni referencias de esos IDs en `data/db/studio.sqlite`; los tres directorios se movieron, sin borrarlos, a `.cache/dev-cycle/m03/pending-quarantine-20261010/` con hashes y rutas en `receipt.json`. La misma verificacion posterior devuelve `MANIFEST_MISSING` porque la biblioteca actual solo contiene `song.json` de snapshots y no manifiestos `audio_take`; por tanto M-03 sigue abierto y no se atribuye un verde que no existe. Evidencia: [testing/m03-pending-quarantine-2026-10-10.md](testing/m03-pending-quarantine-2026-10-10.md).

**Correcciones T-10/T-13 tras revisi�n adversarial � 2026-10-10:** TDD RED reprodujo que el feed SSE s�lo suscrib�a la primera canci�n y que `?` reproduc�a la pista intermedia en vez de la variante hermana. GREEN: `Crear suscribe el feed de cada canci�n` y `el siguiente salta a la variante hermana aunque haya otra pista entre medias`; regresi�n web **257/257**, `pnpm --filter web run typecheck` y `pnpm --filter web run lint` exit 0. T-10/T-13 siguen `en-progreso` hasta revisi�n final y QA Docker/E2E.

**T-09 matriz GPU � 2026-10-10:** la sesi�n controlada `01M4K1RSS80XDD4CPMAAKSC9C2` complet� 8 ejecuciones/1.353 recibos aceptados sin desbordamiento observado, pero termin� con `worker_pipe_eof`/`worker_deadline` al abrir la siguiente operaci�n; no se acredita como verde y queda para depuraci�n/repetici�n.

**Correcci�n final de reproductor � 2026-10-10:** la revisi�n detect� que usar el mismo salto sim�trico en `audio.onEnded` creaba el ciclo A?B?A. TDD RED reprodujo que la reproducci�n autom�tica nunca alcanzaba C; GREEN separ� el avance manual A?B (`advance`) del avance autom�tico (`finish`), que pasa de B a la siguiente pista. Suite web actual: **260/260**, typecheck y lint exit 0.

**QA E2E posterior � 2026-10-10:** la reconstrucci�n Docker y la suite Playwright ejecutaron 15/16; API, compositor, feed, biblioteca, canci�n, reproductor y colecciones pasaron. El recovery E2E-06 qued� en `interrupted` tras el reinicio en esta repetici�n; existe una ejecuci�n anterior documentada de **16/16**, pero se repite para confirmar estabilidad antes del cierre.

**Última verificación de recuperación E2E — 2026-10-10:** se ajustó `playwright.config.ts` para serializar el modo `E2E_RECOVERY` porque E2E-06 reinicia el server compartido. La suite completa con `E2E_ISOLATED=1 E2E_RECOVERY=1 MOCK_STAGE_DELAY_MS=5000` terminó **16/16 en 25,4 s**, incluido recovery; el stack temporal se retiró después. Esto corrige la interferencia entre workers, pero T-15 permanece abierto hasta revisión/QA formal y persistencia VHDX/ext4.

**T-11 fix2 — 2026-10-10:** la verificación FFmpeg conserva las comprobaciones SHA/ZIP/version en la primera llamada y reutiliza el resultado sólo mientras la firma de lock, ZIP y binario permanece estable. RED esperado (`4 hashes` frente a `2`) y GREEN `1/1`; vecinos `25/25`, stream-silence `4/4`, bloque CPU `101/101`, Ruff/formato limpios. T-11 sigue abierto por GPU, WER/escucha y revisión/QA formal.

## T-05 - Auditoria de operadores y RED/GREEN del protocolo lsblk - 2026-10-10

Auditoria fresca de solo lectura confirma trabajo de codigo pendiente ademas de elevacion: wrappers solo plan offline, preflight RW IPC sin wiring, dominio/helper Compose y credenciales sin provision completa, y lifecycle attach/detach/validacion pendiente. El VHDX offline publicado existe y coincide con receipt; no acredita biblioteca montada. Se preservan todos los gates reales.

Primer delta focal: scripts/storage_attach.py y tests/test_storage_attach.py usan ahora JSON real de lsblk, campos null/swap/children, rechazo de estructura/devices duplicados y UUID ambiguo; comparacion antes/despues y NEEDS_ADMIN permanecen. RED: test_parse_real_lsblk_json_with_null_and_swap fallo con AttachError lsblk no canonico a 2026-10-10T18:13:44.8467109Z. RED: test_plan_contains_vhd_bare_and_uuid_probe fallo con AssertionError --json/--paths a 2026-10-10T18:14:10.9240449Z. GREEN focal 53/53 a 18:16:34.9677000Z; cobertura WHOLE 191/210=90,95%, 0 exclusiones, Ruff/formato limpios. Artefactos .cache/dev-cycle/m1/storage-attach-parser-20261010/worker/. Archivos anadidos al alcance T-05 por la correccion necesaria del operador; revision y QA independientes pendientes. No attach/mount/GPU real, no cierre T-05.

## T-05 - Wiring default del preflight IPC - 2026-10-10

Delta limitado a packages/storage-guard/studio_storage_guard/preflight.py y tests/test_preflight.py: el backend Linux real conecta Client.perform y anonymous_rw_probe con FD original, rol/UUID y lease revalidada antes/entre/despues; library RO no hace IPC ni escritura. verify_engine_roots conserva la raiz original de library como control del raw y cierra ambas leases ante fallo. LinuxBackend().probe sin contexto sigue rechazando STORAGE_ROOT_INVALID sin escritura.

RED: test_default_server_wires_fresh_ipc_and_anonymous_probe fallo con STORAGE_ROOT_INVALID antes del wiring a 2026-10-10T18:16:24.8611799Z; GREEN funcional1/1 y final109 passed/42 skipped, Ruff/formato exit0. WHOLE preflight.py180/195=92,307692%, exclusiones0; paquete completo504/803=62,764633%, exclusiones0, no se declara gate integral. Evidencia .cache/dev-cycle/m1/storage-preflight-wiring-20261010/worker/: report.txt, source.diff, source-sha.json, RED/GREEN/JUnit/cobertura. Windows usa seams de syscall/IPC explicitos; faltan Linux/SCM_RIGHTS efectivo, Docker y VHDX. Revision/QA independientes pendientes; T-05 permanece en-progreso.

## Revisión de dos lentes — intento 1: T-05 — protocolo JSON de lsblk

A/B frescas, 0 Critical/Important/Minor; selector auto no requiere C/D. QA independiente funcional53/53 y cobertura53/53, exit0 ambos; WHOLE scripts/storage_attach.py191/210=90,95%, 0exclusiones. Scope oficial del componente exit0/2dentro/0fuera/0excluidos/0avisos; no atribuye gate global al checkout compartido. Root verifica27artefactos del inventario y7hashes de fuentes/preimagenes/evidencia con exit0. [Informe](testing/t05/storage-attach-parser-qa-2026-10-10.md). Componente CPU aceptado; sin attach/provision/WSL/Docker/GPU/E2E persistente ni cierre T-05/M1.

## Revisión de dos lentes — intento 1: T-05 — wiring default del preflight IPC

A/B frescas sin gaps Critical/Important/Minor. A reproduce16tests default; B42tests preflightCPU. Ambas cotejan SHA y preservacion de libraryRO, FD original, control raw/library, IPC/probe nuevos, revalidacion y cierre ante error. Scope oficial2dentro0fuera exit0; coverageWHOLE180/195=92,3077%sinexclusiones. El paquete completo mantiene62,7646%, no se atribuye >=80 a todo el paquete. QA independiente CPU en curso; nativoLinux/SCM_RIGHTS/UIDNamespace/ext4 y gate persistente pendientes. T-05 en-progreso.

## T-05 - QA independiente del wiring IPC - 2026-10-10

QA componente CPU aceptada: funcional109PASS42LinuxSKIP, cobertura109PASS42SKIP, moduloWHOLE180/195=92,3077%excl0 (gate80pasa), paquete504/803=62,7646%informativo. Ruff/formatoexit0; ledgerlint0incoherencias1UTF8aviso. Root coteja23artefactos y2fuentesSHAintactas conexit0. [Informe](testing/t05/storage-preflight-wiring-qa-2026-10-10.md). Incidenteswrapper/parser posteriores preservados, sin repetirtestsni ocultar. NativoLinux/SCM_RIGHTS/UID/ext4/Docker pendientes; no cierreT05/M1. Se liberan unidadesindependientes ADR0071 provision.py/test_provision.py y Dockerfilehelper/override/test_deployment con ownership separado y briefs deterministas; protocolo real y runtime integral siguen por verificar.

## T-05 - Entrega de dominios y despliegue aislado - 2026-10-10

Unidad ADR0071 provision_domains: archivos provision.py/test_provision.py nuevos, controladorrootLinux sin backend/FD/booleanas de caller, UUID/mount exacto nativo/árbolvirgen, ancestrosretenidos, root0700 antescreación y root1770 último, creaciónexclusiva/fsync yrevalidación; noadopción/residuosajenos ni avance receipt. RED: 27casos conductuales fallaron DIDNOTRAISE/resultado{} a2026-10-10T18:36:18.2456278Z; singletonhappy AssertionError a18:37:04.6082769Z; singletonancestor DIDNOTRAISE a18:37:38.4044300Z, anteriorescódigo. GREEN59/59, paquete168PASS42LinuxSKIP, WHOLE162/171=94,7368%excl0, Ruff/formato0. SHAcode3aff44174110c48e12c769127ff39fd7ef7943cd9c9793f88c9afe521d4e889a; SHA test33a4ca0029f66abfad08c618a1ecc2667ea7f42dc03ca9ac63c82f99f97b2467. Evidencia .cache/dev-cycle/m1/storage-provision-domains-20261010/worker/. La pruebaWindowsmodelada no acredita Linux/VHDX ni vinculación attached/disco que haráelcontrolador.

Unidaddespliegue: DockerfilehelperCPU pinyaexistente/stdlib UID19000:10001, overridepersistent5serviciossinprivilegios yconsumidores10001:10001, dependenciasbase/mountROlibrary+RWrawconservados. SieteREDaislados exit1 previos imagen/helperausentes yconsumidores sinUID; GREEN8/8 convecinoCompose, Ruff0. Fuentehelper/client/custody/serverDockerfileintactas. Evidencia .cache/dev-cycle/m1/storage-helper-deployment-20261010/worker/. TDD n/a configuración; testsdecontratosyaml precedencambios. NoDockerinvocación, configreal/build/credenciales/startup aúnpendientes.

Paquete de revisión1 limitado a5paths anteriores: preimagenoverride35058ff... recuperada y verificada porSHA exacto, cuatro archivosantesausentes. ScopeCLI oficialen snapshotprivado5dentro0fueraexit0 sinexclusiones/avisos; copiedledgerescontexto, noautoridadestado. SelectorautoC=true porDockerfile/Compose, D=false. .cache/dev-cycle/m1/storage-domain-deployment-review1-20261010/. A/B/C frescas yQA pendientes, T05en-progreso; ningúncierreintegral.


## Revisión de dos lentes — intento 1: T-05 — dominios y despliegue

Lentes A/B/C de contexto fresco, diff completo de cinco archivos: 0 Critical, 0 Important, 0 Minor. C aplica por Docker/IaC; D no aplica según selección oficial. Scope del componente exit 0, cinco dentro, cero fuera/excluidos/avisos; no acredita el checkout compartido completo. QA independiente: 176 PASS/42 Linux SKIP, cero fallos/errores, funcional y cobertura; WHOLE provision.py 162/171 = 94,74 %, exclusiones cero. Paquete total 68,38 % informativo, no gate general. Ruff/formato exit 0; ledger-lint cero incoherencias y aviso UTF-8 preexistente. Root coteja 20 artefactos, cinco fuentes, siete terminales y dos JUnit, exit 0.

Docker Compose config real resuelve el helper y cuatro consumidores con UUID/root de ejemplo. Build real de la imagen fijada termina exit 0; prueba por ID verifica UID reales/salvadas/efectivas 19000:GID 10001, único grupo 10001, CapEff/CapBnd cero y NoNewPrivs=1. Arranque sin UUID y UUID inválido rechaza exit 1. Tres contenedores propios ausentes después; ningún modelo GPU cargado. El build resolvió metadatos del registro, por lo que no se declara totalmente offline. Informe: [dominios y despliegue](testing/t05/storage-domains-deployment-qa-2026-10-10.md); recibos `.cache/dev-cycle/m1/storage-domain-deployment-review1-20261010/qa/`, `root-verification.json` y `runtime/receipt.json`.

Componente CPU y credenciales Docker aceptados. T-05 sigue en-progreso: pendiente IPC positivo/permisos sobre ext4/VHDX, binding/custodia del controlador, validación/desmontaje y manuales. No se cierran T-05 ni M1.


## T-05 — Arranque ACE-Step sin importar torch antes del gate — 2026-10-10

El entrypoint actual importa torch antes de ejecutar la factoría HTTP y su preflight storage. Se autoriza una corrección acotada de entrypoint.sh y prueba conductual propia, sin alterar imagen/recibos congelados de T-09, adaptador, pesos ni descriptores. La imagen actual no se reemplaza durante el diagnóstico; el despliegue posterior requiere imagen nueva y verificación. Test RED antes de código; root conserva ledger y revisión/QA. No se está solo y no se revierten fuentes ajenas.


## T-05 — RED/GREEN del arranque ACE sin torch — 2026-10-10

RED: test_pre_gate_startup_delegates_without_python_import falló AssertionError «entrypoint ejecutó Python antes de delegar al preflight» · 2026-10-10T18:56:56Z · exit 1, fuente anterior retenida. GREEN Linux real 3/3, exit 0: sin import previo, argumentos exactos, exit 23/PID exec y SIGTERM→42. Windows 3 SKIP explícitos. red1.xml conserva incidente de wrapper PowerShell previo; recibo causal principal red2 tiene UTC/argv/hash completo. Fuente elimina solo import/banner de torch y conserva exec. Evidencia `.cache/dev-cycle/m1/acestep-startup-20261010/worker/`, tres contenedores propios ausentes. Sin rebuild de ACE ni cambios en imagen/calibración/recibos de T-09. Revisión y QA independientes pendientes; no cierre T-05.

## Revisión de dos lentes — intento 1: T-05 arranque ACE sin torch — QA conforme

A y B frescas sin gaps pendientes. QA independiente PASS_COMPONENT: 3/3 Linux reales, 0 fallos y 0 skips Linux; Windows 3 SKIP. Ruff/formato, ledger-lint, coverage-check y qa-gate terminales exit 0. Cobertura porcentual n/a para producción shell, sin módulo Python producto modificado. Root verificó 56 artefactos, dos hashes de fuentes y ocho terminales, con limpieza confirmada. Se conservan los incidentes del wrapper y del recibo inicial de ausencia, corregidos con evidencia original. Informe `testing/t05/acestep-startup-qa-2026-10-10.md`; recibos `.cache/dev-cycle/m1/acestep-startup-20261010/`. Se acepta esta unidad de código; no se reconstruye la imagen ACE ni se acredita montaje ext4/VHDX, GPU, readiness integrado o E2E. T-05 permanece en-progreso.


## Validación actual de M1 — 2026-10-10: primer corte y corrección de lint

Prioridad explícita del propietario: validar M1 antes de continuar M2/T-02. [Informe vigente](testing/current-validation-2026-10-10.md). Estados de tareas preservados; no cierre de M1 con fixtures ni traslado de gates a M2.

QA independiente E2E: builds oficiales server/web/mock exit0; fixtures Playwright15/15, web260/260, lint0/typecheck0. Recorrido real con mock y FFmpeg: publicación falla OSError22/rename_noreplace sobre bindWindows; assertionreal0/1 y qa-gateNO-VERDE. Falta ext4/VHDX autorizado, persistencia/recovery/Range real y M-01/M-02/M-03. SOURCE_SEAL_FINISHED19:40:43UTC; raíz133artefactos/1748sellos/bothJUnit/8terminales comprobados19:41:56UTC. Tools excluidos del sellado original; único driftCONTINUErouting esperado. Tres contenedores/red/token propios retirados, ACE intacto.

Suite backend actual Linux terminó command3exit1/JUnit2109PASS88FAIL11SKIP1ERROR en597,63s. El wrapper de contenedor termina0 sin propagar ese exit: no acredita verde. QA agrupa dependencias/fixtures ausentes y defectos reales, conservando originales. SOURCE_SEAL_FINISHED:380fuentes actuales sin mismatch antes de corregirlas. No convertir88fallos en88defectos de producto por inferencia; informe/focales causales en curso.

RED de lint real: I001 en test_dispatcher_cpu_worker.py y13archivos sin formato, originales nativeRuff de QA. TDD n/a para esta unidad: formato y reordenación de imports, sin nueva lógica. Implementer fresco preparó13archivos privados; 12AST idénticos y testCPUAST idéntico normalizando únicamente11imports iniciales. Raíz integró output exacto tras CAS de13SHA y comprobación AST a19:44:09UTC. GREEN nativo: `uv run --frozen --no-sync --all-packages ruff check apps/server packages/engine-contract packages/audio-post packages/storage-guard` exit0; `ruff format --check` mismo alcance exit0,154yaformateados. Recibo `.cache/dev-cycle/m1/validation-20261010/apply_lint_root.receipt.json`. Revisión/QA posterior pendientes; no tarea completada.

CandidatoT-07 idioma confirmado: DTO admite omitido/null pero params.language:null viola schema string delmock,422INVALID_PARAMS; control es202. Implementer fresco conserva REDcausal2/2 y baseline4FAIL6PASS, preparaciónGREEN10/10. Aplicación semántica/revisión/QA en curso. T-02 bloqueo SQLite concurrente en diagnóstico causal independiente; entrada SQLInfinity y FIFO de test pendientes de corrección verificable. La Verificación históricaT-00 falla hoy al decodificar ledger noUTF8; no reutilizar sufreeze anterior como actualidad.


**Alcance de validación M1 — 2026-10-10:** el precheck de la revisión detectó `packages/storage-guard/tests/test_helper.py` fuera del campo Archivos. Se declara en T-05 porque la corrección de lint formatea ese test existente del helper IPC; AST idéntico y sin lógica nueva. No exclusión de usuario ni cierre de tarea.


## Revisión de dos lentes — intento 1: Validación actual M1 (T-02, T-05, T-07, T-15) — correcciones CPU/API

Unidad posterior al sellado original de QA. Diff privado17archivos,16fuentes de producto; no incluye el candidato JSON0007 ni la fixture FIFO. Scope-check exit0, fuera[], exclusiones de usuario[]; helper test incorporado al campo Archivos de T-05 tras el precheck. LenteCauto=false; lenteDauto=true por rutas queue/worker/sql.

| Lente | Veredicto | Evidencia y ejecución |
|---|---|---|
| A conformidad | Sin defectos | Diff completo,16SHA, criteriosT02/07 acotados, constitución y contratos; Ruff0/format0/export0 |
| B corrección | Sin defectos introducidos |42PASS API/FTS;42PASS+1SKIP persistencia/dispatcher/esquema;AST13/13 |
| D rendimiento | Sin hallazgos | FTS107pasosSQLite para0/100/10000canciones,0filas/sintransacción;AST11conformes |

Critical0,Important0,Minor0; sin gaps pendientes **en esta unidad**. QA independiente posterior en curso. No cerrar tareas ni M1: permanecen los criterios integrales de generación/publicación, ext4, recovery, escucha y backup, además de integración Git.

- **RED T-07**: petición de generación con idioma omitido/null falló con422 INVALID_PARAMS en vez202 antes de corregir; dos fallos causales originales conservados ·2026-10-10.
- **GREEN T-07**: regresión final API203PASS,exit0; cobertura whole domain_routes.py654/755=86,62%,exclusiones0. El29/29 inicial y la cobertura73,77% quedan como intentos anteriores, no sustituyen este sello.
- **RED T-02**: test final de commits FTS concurrentes sobre db anterior falló con SQLite517/SQLITE_BUSY_SNAPSHOT, segunda fila no persistida ·2026-10-10.
- **GREEN T-02**: reparación aplicada autocommitFTS; Windows37PASS/1SKIP y Linux38PASS,exit0; whole db.py60/64=93,75%,exclusiones0. Barreras,BEGIN ytimeoutes permanecen.
- **TDD n/a**: formato/imports y ampliación de validación de comportamiento existente; no lógica nueva en la ampliación de cobertura.
- Raíz verificó79artefactos de concurrencia,16SHA de revisión,203casosJUnit y ambas coberturas originales a20:02:34UTC. Fuentes current no cambian durante revisión. Consultas de conocimiento0aciertos; sin imputar tokens/horas estimados como mediciones reales.
- Evidencia privada: .cache/dev-cycle/m1/validation-20261010/review/lens-a.md, lens-b.md, lens-d.md y source.diff; verify_fixes_root.receipt.json; concurrency-fix/APPLIED_REPORT.md; language-fix/coverage-extension/handoff.json.
- Nuevo candidato separado T-04: generación sin model_id explícito devuelve202, guarda Job.model_id=null y Take.model_id=mock; retry posterior409. Repro en language-fix/coverage-extension/issue-retry-model-implicit.json; no se oculta corrigiendo el test ni entra en este diff.

Los estados y checkboxes de las tareas se conservan; el informe actual vigente es testing/current-validation-2026-10-10.md.


## QA independiente de validación M1 — 2026-10-10: unidad CPU/API aceptada

Después de revisión A/B/D sin gaps, QA fresca termina Windows **349 PASS,1 SKIP,0 FAIL,0 ERROR**; Linux nativo **38/38 PASS**; Playwright HTTP nuevo sobre Docker real **6/6 PASS**, sin retries. `qa-gate.py` ejecutado por QA y por raíz: **exit0 VERDE**, passed6/failed0/flaky0/skipped0/interrupted0. El verde se limita a CPU/API; **M1 integral NO-VERDE**.

Whole domain_routes.py654/755=86,62%, db.py60/64=93,75%, ninguna exclusión. Fuente16/16 intacta hasta SOURCE_SEAL_FINISHED20:12:11UTC. Raíz verificó3275artefactos por tamaño/SHA a20:13:38UTC; dos entradas de fixtures nativas no legibles en Windows quedan explícitamente sin verificación de contenido. JUnit350/38/6 y terminales0 verificados. Intentos de harness originales conservados; ningún fallo ocultado como flaky. Reporte testing/current-fixes-qa-2026-10-10.md corregido exclusivamente de codificación en56segmentos, con recibo separado y originales intactos. Contenedores/red/tag propios retirados; ACE intacto. Sin GPU ni Ollama. PDF omitido por dependencia gestionada ausente.

No cierre T-02/04/05/07/15 ni M1: faltan almacenamiento ext4, publicación/recovery, Range y backup de biblioteca, GPU/escucha, revisión manual e integración Git. La raíz acepta sólo el componente verificado, según verify_fixes_qa_root.receipt.json.

## Correcciones siguientes de validación M1 — 2026-10-10: integradas para revisión, no aceptadas

Tras terminar el sellado QA anterior, la raíz integró por CAS8archivos de tres implementadores frescos. Preimágenes exactas; no cambios de Git compartido, ni a0001–0006. Snapshot/diff privados en .cache/dev-cycle/m1/validation-20261010/next-fixes-review, base d5efbb18a4e31340160c8a690c33b75818ff1bc7. Verificados837artefactos JSONrevision2,843 originales retry y195 nuevos de prosa;65regulares FIFO y1entrada especial no abierta. Scope-checkexit0,8fuentes,fuera[],exclusiones[]. Lentes Cauto=true(sql-fstring)/Dauto=true(migrations/queue/n-plus-one); revisiónA/B/C fresca activa yD pendiente de despacho al liberarse slot. QA posterior aún no ejecutada para estas8fuentes.

- **RED T-04 JSON**:27casos INSERT/UPDATE/REPLACE de sintaxis inválida produjeron OperationalError/malformedJSON en vez IntegrityError sobreSQLite3.40.1 ·2026-10-10. Prefijo json_valid/RAISEABORT dentro de los dos triggers actuales; migración incremental0007, sin reescribir filas/IDs/FK/snapshots. Downgrade restaura DDL legado exacto, rollback del segundoCREATE verificado.
- **GREEN candidato JSON**:124PASS Linux yWindows, wholehelper189/202=93,56%,0007=15/15=100%,exclusiones0. Dos tests existentes actualizan exclusivamente head0006→0007; REDdel segundo consumidor4/4conheadanterior conservado. Prueba nueva usa tmp_path/monkeypatch, sin mutar PHASE global al importar. Final5archivos entregados en json-guard-fix/revision2;120previos/inventario1009preservados.
- **RED T-04 modelo implícito**:API real devolvió409al retry esperado202; caso default cambiado también reproduce409 ·2026-10-10. Chain guarda modelo/engine efectivos antes_create; CPUdependents legítimosnull preservados, no reelegirdefault al retry ni reparar legacyinplace.
- **GREEN candidato retry**:81PASS,wholechains84/86=97,67%,exclusiones0. Dos textos posteriores corregidos con ASTequivalente y10focales actualesPASS;81/coverage corresponden explícitamente a la fuente anterior sólo en prosa. Dos archivos exactos integrados; nuevos SHA en implicit-retry-fix/revision2/sources.json. Inconsistencias legacy quedan failclosed.
- **RED T-05 FIFO**:testoriginal1PASS+1ERRORteardown por Entradaespecial del propio FIFO ·2026-10-10. Fix únicamente de fixture: identidad emitida por hijo, cleanup trasreap con directorioFD/NOFOLLOW, sin borrar entrada sustituida. No cambios a scripts/test_workspace.py ni a19funciones/asserts originales.
- **GREEN candidato FIFO**:focal1PASS yregresión66PASS/1SKIP Linux; cuatro casos de custodia de owned/identity/regular/symlink. Ocho containers propios terminalPID0 retirados. Sólo testfixture, sin atribuir cobertura runtime nueva.

Integración20:14:33UTC no acredita aceptación de esta unidad. Tareas/checkboxes permanecen abiertos. Informe vigente testing/current-validation-2026-10-10.md; recibos originales y posteriores separados.


## Revisión de dos lentes — intento 1: Correcciones siguientes M1 (T-04, T-05, T-07) — JSON, modelo y fixture

Diff congelado de ocho archivos y 719 líneas, base privada d5efbb18a4e31340160c8a690c33b75818ff1bc7. Scope-check exit0, fuera[], exclusiones[]. Todos los revisores verificaron SHA8/8 antes y después; fuentes y snapshot idénticos al recibo de integración. C activada por SQL interpolado; D por migrations/queue y heurística n-plus-one. Sólo componentes correctivos, no aceptación integral M1.

| Lente | Veredicto | Evidencia independiente |
|---|---|---|
| A conformidad | Sin defectos | JSON atómico, migración/custodia, modelo efectivo, FIFOfixture y constitución; focal42PASS/4SKIP |
| B corrección | Sin defectos | JSON+retry41PASS; privatecontext+head64PASS/5SKIP, ambos exit0 |
| C seguridad | Sin hallazgos | Identificadores SQL constantes,2/2cuerpos legados iguales al retirar prefijo;18/18SQLmalformados rechazados atómicamente en memoria |
| D rendimiento | Sin hallazgos | DosDDLdrop/create sin recorrer filas; chainO(1)sinquerynueva;1000UPDATE×4muestras con416/8608/65952Bsinregresiónobservada |

Critical0, Important0, Minor0: **sin gaps pendientes en esta unidad**. Los skips de los revisores Windows requieren POSIX; la QA posterior debe ejecutar FIFO nativo. Las diferencias de tiempo de D no acreditan una mejora por ruido. Consultas de conocimiento ADR sin aciertos. Evidencias privadas next-fixes-review/lens-a.md,lens-b.md,lens-c.md,lens-d.md ysource.diff.

QA fresca /root/qa_m1_next_fixes activa, ownership next-fixes-qa y testing/current-next-fixes-qa-2026-10-10.md. El verde previo349/38/6 se conserva como unidad anterior y no se reutiliza para estas ocho fuentes. Medición QA inició a20:19:59Z con usage-meter y estado privado next-fixes-review/usage-state.json; cero transcripciones API disponibles, por lo que tokens/coste deben quedar estimados o desconocidos, nunca reales. La revisión anterior no tenía marcador medido; no se inventa retroactivamente una medición.

Tareas y checkboxes conservados abiertos. M1 continúa NO-VERDE por ext4/publicación/recovery/Range/backup/GPU/escucha/manual/Git. No handoff de cierre ni cambios al objetivo global activo.


## QA independiente — segunda unidad M1: NO-VERDE · 2026-10-10

Revisión intento 1 A/B/C/D: sin hallazgos. La QA posterior sí detecta dos gaps Important: dispatcher_retry.py:1824 espera head0006 frente a0007 (dos FAIL); fixture compartida dispatcher_admission.py:217 espera0006 (49ERROR en Windows y otros49 en Linux). No son fallos de generación ni se omiten de la regresión. Barrido del implementador encuentra un tercer consumidor test_queue_manual_retry.py:272, antes oculto por setup; corrección privada autorizada únicamente para tres literales HEAD.

Resultados actuales sellados20:27:56UTC: JSON124/124 Windows y124/124 Linux; selección ampliada227PASS/2FAIL; chains32PASS/49ERROR por plataforma; FIFO66PASS/1SKIP POSIX; HTTP real6/6, qa-gate0. Cobertura whole usada por selección: helper189/202=93,56%, migración15/15=100%, chains79/86=91,86%, sin exclusiones. Coberturas incidentales de módulos ajenos a cada selección no se sustituyen por estos porcentajes. El componente sigue NO-VERDE aunque HTTP/cobertura pasen.

Raíz verifica2995artefactos por SHA/tamaño, ocho fuentes idénticas hasta el sello, siete JUnit/terminales incluyendo exit1, informe y gate HTTP real. Recibo verify_next_qa_root.receipt.json; informe testing/current-next-fixes-qa-2026-10-10.md. Contenedores/red/tag propios retirados; mock/ACE conservados. Sin GPU/Ollama/datos canónicos. PDF omitido por dependencias gestionadas ausentes. Usage-meter QA cerrado20:28:45Z, fuente estimado, tokens/coste reales null; no se inventa medición real.

Fix revisión3 privado a cargo del implementador original; deberá integrarse por CAS, pasar revisión intento2 y QA de regresión actual. Originales y pruebas fallidas se conservan. Estados/checklists permanecen abiertos. M1 integral NO-VERDE por publicación ext4, recovery/Range/backup, GPU/escucha/manuales e integración Git; M2T02 no iniciado. Objetivo global activo.


## T-05 — binding nativo del disco publicado: integrado para revisión · 2026-10-10

Nueva custodia de consulta PublishedDiskBinding, únicamente scripts/storage_operator.py y tests/test_storage_operator_binding.py. Alcance T-05 ampliado a ambos por requisito de controlar identidad publicada durante attach; storage_windows.py intacto. API open(project_root,StorageReceipt)/revalidate/close; FILE_ID_INFO y ruta/ancestros reales retenidos. Sin autoridad de creación, borrado o adopción, ni checksum inicial como identidad mutable. No integración attach/validated/detach en este incremento.

RED: ocho capacidades ausentes fallaron aisladamente con AssertionError, no ImportError. Probe real: READ_ATTRIBUTES(0x80) y +SYNCHRONIZE(0x100080) no bloqueaban rename, primer17PASS/1FAIL guardado. Adaptación explícita autorizada por raíz READ_ATTRIBUTES|SYNCHRONIZE|FILE_EXECUTE/TRAVERSE(0x1000A0) activa sharing denyDELETE; API carece de operación execute/readbytes/write/delete. GREEN candidato Windows18/18, whole113/118=95,76%, sin exclusiones, Ruff0. Rename/delete propios WinError32 mientras lease, permitidos tras close; handles liberados exactamente. Identidades/recibos cambiantes, reparse/junction/hardlink rechazados; foreign intacto. Este derecho se evaluará en revisión de seguridad si aplica, no se oculta como query-only acceso numérico.

Raíz verifica185artefactos por SHA/tamaño y ambas preimágenes ausentes; aplica exactamente los dos archivos nuevos. Diff/snapshot privados storage-binding-20261010/review, candidato/inventario originales intactos. Revisión/QA actuales pendientes. Sin admin/mount/VHDX real/ext4/GPU/Ollama/servicios. El disco smoke existente permanece intacto; no cierra T-05/M1 ni autoriza validated con booleanos.


## Revisión de dos lentes — intento 1: T-05 binding publicado · 2026-10-10

Scope dos fuentes exit0, fuera/exclusiones/avisos[], selectorauto Cfalse/Dfalse. A/B frescas y fuentes intactas antes/después. A conformidad sin gaps con18PASS nativos propios; B corrección18PASS propios, pero reproducción adicional confirma **B01 Important**: storage_operator.py:231 falla revalidate en __enter__, Python omite __exit__,19handles abiertos retienen disco/ancestros. Mutación de recibo tras último revalidate exitoso de open y antes de entrar:180→199handles, rename WinError32; cleanup explícito→180bytesintactos. Salida real del revisor persistida lens-b.md; reproducción efímera, no se inventa terminal en archivo.

Tabla completa intento1: identidad/ruta/fase/hashmutable ✓; reparse/hardlink/ajenos ✓; denyDELETE y close normal ✓; TDD/cobertura/constitución/alcance/no cierre ✓; entrada al contexto libera recursos ✗ B01Important; interop/OpenAPI no aplica; integral T05 no acreditado. Critical0 Important1 Minor0, ninguno descartado. Root acepta B01trascontrastarlo con semántica de context manager y autoriza fix privado mínimo con testREDcausal; originales185artefactos y fuentes integradas intactas. Implementador prepara revisión2 sin editar compartido.

Revisión intento2 deberá reevaluar únicamente B01/cambios nuevos conservando tabla anterior salvo evidencia nueva; QA independiente sólo después. Componente no aceptado; T05 y M1 abiertos, sin attach/ext4/admin/GPU.


## Revisión de dos lentes — intento 2: correcciones siguientes M1, tres expectativas HEAD · 2026-10-10

Tabla anterior A/B/C/Dsin gaps preservada; la QA posterior detectó dos referencias0006 obsoletas y el barrido causal encontró una tercera antes oculta. Todos Important corregidos, ninguno descartado. Rootverificó1552artefactos/revisión3preimagesexactos yCAS20:37:16, sólo tres bytes0006→0007. Originales1009+837yrojosconservados. GREENcandidato190PASSWindows/180PASS10SKIPLinux, manualfinalLF33PASSambos (ASTigualalfullanterior). Fuente runtimeJSON/model/FIFO sin otro cambio;0001–0006intactos ycuatro0006históricosdowngrade/rollback preservados.

Scope3exit0fuera[]excl[],Cauto=false,Dauto=true rutaqueue. FrescasA/B/D: Aconformidad4PASS, Bcorrección4PASS, Drendimiento reversebyteproof3/3 sin nuevaoperación; Critical0Important0Minor0. SHA3antes/despuéscoinciden. Los casos focales mantienen todas sus aserciones. Evidencias head-fix-review/lens-a.md,b.md,d.md. No reapertura de lo previamente aprobado sin evidencia nueva.

QA fresca activada en head-fix-qa ytesting/current-head-fix-qa-2026-10-10.md. Combina JSON/retry/chains sobre fuentes actuales; candidatos no sustituyenQA. FIFO/HTTP previos sólo pueden citarse como históricos del mismo runtimeSHA, sin fingir ejecuciones nuevas ni statsPlaywrightfabricados. Medidor start20:40:03Z clave m1/validation-head-fix/qa, cero transcripciones disponibles, tokens/costes reales desconocidos. M1 integralNO-VERDE, tasks abiertos.

T05B01: segunda corrección integrada porCAS20:38:29 tras verificar185originales+80nuevosartefactos; fuenteoperator/test47f20b.../ccb424..., storage_windowsintacto. REDnativo214vs196/rename32; GREENcandidato19PASS/whole118/12594.4%sinexcl. Cambiosúnicos__enter__+nuevo test, APIrightsinalterados. Revisión2A/Bactiva; todavía no aceptado niQA. Sin attach/ext4/validated/detach/admin/GPU/servicios reales.


## Revisión de dos lentes — intento 2: T-05 binding publicado · 2026-10-10

Tabla intento1 completa transferida a revisores frescos: todos los criterios aprobados conservados, B01Important entrada alcontexto pendiente. A/Brevisanúnicamente fix/nuevotest: ambos **B01corregido**,0Critical0Important0Minor. A19PASSnativos, handles207→207/renamepermitido; B1PASSnativo handles202→202+probeserrororiginal/cleanupcause/KeyboardInterrupt. SHA2antes/despuésiguales a integración/snapshot. AutoC/Dfalse,scope2exit0fuera[]excl[]. No reabrirvalidacionespreviasni atribuirrealattach/ext4.

Raíz conservó185originales yverificó80nuevosantesCAS20:38:29; scripts/storage_operator.py__enter__cierraownleaseantespropagarerror, noAPInuevani rightsadicionales. Nueva prueba causalreproducecambiode receiptDESPUÉSopenexitoso yantesenter. RED214vs196/rename32;GREENcandidato19PASSwhole94.4%sobre125sinexclusiones;intervencióndel código limitada__enter__ ytest.

QAindependiente /root/qa_m1_storage_binding activa en storage-binding-20261010/qa y testing/t05/storage-binding-qa-2026-10-10.md. Windowsnativosreales, whole>=80/0excl,sellos2sources+dependency; sinfakePlaywrightJSONpor módulo nativo. Usage-markerstart20:41:11Z m1/storage-binding/qa,cero transcripcionesAPI,realcost/tokensdesconocidos. Rootprobe20:42:06Zcontinúa elevated=false; noefectosadmin/GPU/WSL/VHDXreal. Componenteaúnno aceptadohastaQA, T05/M1abiertos.


## QA independiente y aceptación limitada — T-05 binding publicado · 2026-10-10

Tras revisión2A/B sin gaps, QA Windows nativa actual pasa19/19 funcionales,19/19 con cobertura,17/17 de regresión. Whole/módulo118/125=94,4%, exclusiones0. Reproducción independiente entrada fallida235→254→235handles, cuerpo no ejecutado, foreignSHA idéntico, rename permitido después. Lease normal devuelve handles al baseline; delete durante lease WinError32. Regresión publicación contiene3tests FakeCustody: no se presenta como VHDX/ext4 real. Primer harness de regresión14ERRORsetup/3PASS se conserva; sólo se creó padre privado requerido y los mismos17tests pasan. Finalize inicial de encoding y terminales también conservados.

Raíz verifica153artefactos por tamaño/SHA, ocho fuentes/dependencias intactas, JUnit19/19/17 y terminales0, reproducciones y cobertura oficial. Recibo storage-binding-20261010/verify-qa-root.receipt.json. Informe testing/t05/storage-binding-qa-2026-10-10.md: rutas personales sustituidas sólo por enlaces relativos, original privado/inventario153/sello intactos y delta documental separateSHA. No pruebas repetidas por enlaces. qa-gatePlaywright no aplica al módulo nativo; no stats sintéticas. PDF no renderer gestionado disponible. Medidor cerrado20:45:04Z fuente estimado, tokens/coste reales null.

**Aceptado únicamente PublishedDiskBinding nativo**, no T05 ni M1. Fuentehelper47f20bc.../testccb424... permanece congelada hasta fin QA. Sin attach, ext4, validated, detach, consumidores, publicación persistente ni servicios/admin/GPU reales. M1 permanece NO-VERDE y sus estados/checklists abiertos.

Siguiente delta privado /root/implement_m1_attach_binding: retener binding en execute antes/durante efectos y rollback, con tests CPU explícitos y revisión/QA posteriores. Own scripts/storage_attach.py+tests/test_storage_attach.py, sin alterar compartido. Se conserva límite de recibo: bytescheck+write por ruta no acredita CAS ni durabilidad; pérdida después del commit debe indicar efecto/incertidumbre, no fingir ausencia de avance ni revertir por ruta. Controller completo/receiptcommit durable siguen pendientes, no se aceptan con mocks. Objetivo global activo, no cierre ni pausa.


## QA independiente y aceptación limitada — segunda unidad M1 corregida · 2026-10-10

Después de revisión2A/B/D sin gaps, regresión combinada actual: **Windows310PASS; Linux300PASS/10SKIP**, cero fallos/errores y terminales0. Los diez skips son controles WinEvent propios que sí pasan en Windows, sin exclusiones nuevas. Whole en ambas plataformas: helper189/202=93,56%; migración0007 15/15=100%; chains84/86=97,67%; exclusiones0. Ninguna tarea cerrada por este verde parcial.

Raíz verifica3053artefactos por tamaño/SHA (sin entradas sin verificar), diez fuentes iguales antes/después hasta sello20:49:30UTC, JUnit/terminales y tres coberturas oficiales. Recibo verify_head_qa_root.receipt.json e informe testing/current-head-fix-qa-2026-10-10.md. HTTP6/6 yFIFO66PASS/1SKIP **históricos**, no repetidos: runtime71fuentes idénticas yFIFO SHAigual; gate HTTP vuelve a ejecutarse sobre JSON Playwright real anterior y pasa0. Esta QA genera0testsHTTP nuevos, no resultados sintéticos. Contenedor propio terminadoPID0 yretirado; restantespropios[]. No GPU/datoscanónicos/Ollama. Usage cerrado20:50:43Z, fuente estimado, tokens/coste reales null. PDFomitido sinrenderer gestionado.

**Aceptada únicamente la unidad CPU/API correctiva**: JSONmalformado incremental, modelo efectivo/retry yexpectativasHEAD actualizadas; FIFO conserva aceptación POSIX previa. Primeros rojos227PASS/2FAIL y32PASS/49ERROR por plataforma permanecen en next-fixes-qa. Todas las preimágenes, revisiones y artefactos anteriores intactos. No reinterpretar verdes de candidatos como QA actual.

T05 binding nativo también aceptado separadamente19/19+17/17,whole94,4%; incremento attach aún PRIVADO/NO aplicado: candidato71PASS/whole251/27292,28%,63artefactos verificados yscope2exit0, base privada8d7361ef...; /root/review_m1_attach_binding_a y_b activos, autoC/Dfalse. Mantiene límite commitreceipt por ruta sinCAS/durabilidad, no attach/ext4/validated/detach nativos. Lectura del candidato no acredita implementación compartida ni aceptación.

M1 integral sigue **NO-VERDE**: publicación EINVAL sobre bindWindows, montaje ext4/persistencia, recovery/Range/backup, GPU/escucha/manuales e integración Git pendientes. Windows tokenadminfalse20:42:06UTC. M2T02 no iniciado, objetivo global activo yestados/checklists sin cambios.


## Revisión de dos lentes — intento 1: T-05 attach con binding, candidato privado · 2026-10-10

Base privada8d7361ef...; scope2exit0fuera[]excl[],autoC/Dfalse. Root63artefactos verificados; producto NO aplicado, preimages601e1c.../8896ed...intactas. A yB frescas ejecutan71PASScada sobrecandidate; SHA2preimage/2candidate/3dependenciesantes/despuésexactos. A no encuentra defectos introducidos; B encuentra **B01Important**, código snapshot storage_attach.py:381/444: si haycausaprimaria, rollbackcorrecto yclosefalla, cleanup_errors/notes conservanfallo pero CLI imprime sólostr, oculta cierre/incertidumbre. ReproducciónCPU mainexit2/close1/recibointacto,JSON NOT_READYsólocausaprimaria. Rootcontrasta yacepta gap, no descarta por71PASS.

Tabla completa: autoridad/admin/binding✓; fronterasrevalidate✓; efectosregistrados/identityloss✓; rollbackmountpoint/deviceUUID✓; recibocambiadoobservado/snapshotseparado✓; postcommituncertainty✓; cierreúnico✓ pero diagnósticocloseconprimaria✗B01Important. ReciboCAS/durability/fullT05/ext4/validated/detach no verificables ypreexistentes; no aprobados como resueltos. Interop/OpenAPInoaplica; no tareas cerradas. Critical0Important1Minor0; ninguno descartado.

Fixprivado2 a cargo implementadorfreshoriginal; namespace implementation-review2, original63intacto. REDCLI causal exige cierre/incertidumbre sinfiltrar paths, luego fixmínimo manteniendo primaria/status/exit; revisión intento2yQA posteriores. RootnoCASproducto hastaresolvergap. EstadosM1abiertos/NO-VERDEglobal; unidadCPU/API310Win/300Linux+10skip ybindingnativo19+17conservaraceptación limitada. Sin plataforma/GPU/servicios/datos reales.


## Revisión de dos lentes — intento 2: T-05 attach con binding · 2026-10-10

Lentes A/B frescas, scope 2 archivos exit 0, fuera de alcance y exclusiones vacíos; C/D automáticas no aplican. A ejecutó seis casos focales (66 no seleccionados); B ejecutó los 72 y un probe independiente. Terminales 0 y hashes protegidos iguales antes/después. Ambos dictámenes: cero Critical, Important o Minor. Ninguno descartado. B01 queda corregido: la salida CLI conserva la causa primaria y comunica cierre fallido, incertidumbre, efectos observados y posible retención de handles; no expone el detalle privado de close. Ver review2/lens-a.md y lens-b.md.

La raíz verificó los 88 artefactos de candidatos y las preimágenes/dependencias, y aplicó exclusivamente dos archivos a las 21:00:56 UTC, sin cambiar Git. Recibo review2/integration-receipt.json. Los originales anteriores permanecen intactos. La QA independiente de las fuentes compartidas comienza con /root/qa_attach_binding_current. Aún no hay aceptación del componente por QA.

Los límites preexistentes de actualización del recibo por ruta, CAS/durabilidad y validación/attach/detach físicos siguen abiertos. Ninguna tarea cerrada; M1 integral NO-VERDE.

## Siguiente incremento acotado T-05: lease del recibo existente · 2026-10-10

La auditoría de sólo lectura identifica ausencia de store/exclusión del recibo y commit durable. El diseño aprobado exige fases durables y recuperación cerrada (storage-execution-design.md:55–60). Se declara en Archivos el incremento scripts/storage_receipt_store.py y tests/test_storage_receipt_store.py: lease Windows por handles del recibo y ancestros, snapshot tipado coherente y exclusión real de escritura/reemplazo rival. Sin crear/adoptar recibos, sin commit ni cambio de fases, sin extender PublishedDiskBinding ni el candidato attach aceptado por revisión. Es una concreción del diseño; no cambia el formato ni la fuente de verdad. Commit durable y lifecycle posterior requieren su propia unidad y evidencia. El implementador fresco trabaja en espejo privado, TDD nativo, y espera CAS raíz antes de aplicar. Esta declaración no cierra T-05 ni ninguna puerta física.


## QA independiente y aceptación limitada — T-05 attach con binding · 2026-10-10

Tras revisión 2 A/B sin gaps, QA de las fuentes aplicadas: 72 pruebas attach funcionales, 72 de cobertura, 19 binding Windows nativas y 14 custodia Windows nativas; cero fallos/errores/skips y terminales 0. Cobertura oficial del módulo completo storage_attach: 252/273 = 92,31 %, sin exclusiones, gate fail-under 80 exit 0. Probe B01 independiente API/CLI conserva primaria, cleanup_errors y notes, muestra incertidumbre con CLI exit 2 esperado, close una vez y bytes del recibo intactos. Los comandos attach/mount/rollback del probe son dobles CPU, no WSL real.

La raíz verificó a las 21:05:08 UTC los 314 artefactos por tamaño/SHA, 16 fuentes/dependencias actuales y snapshots, cuatro JUnit, terminales oficiales y 41 enlaces relativos del informe testing/t05/storage-attach-binding-qa-2026-10-10.md. Recibo .cache/dev-cycle/m1/storage-attach-binding-20261010/verify-qa-root.receipt.json. Un primer verificador raíz usó la clave exit en vez de exit_code; falló antes de emitir aceptación y se conservó como verify_qa_root_attempt1.py. La corrección sólo afecta al arnés raíz; ninguna fuente ni evidencia QA cambiada. Los intentos de medición/probe fallidos propios de QA siguen íntegros.

**Se acepta sólo el incremento técnico CPU/nativo attach-binding.** Sin UI en el delta: cero E2E nuevos, qa-gate Playwright no aplicable, PDF omitido sin renderer gestionado. Sin GPU/Ollama/WSL/admin/servicios ajenos/datos reales. ReceiptLease sigue en espejo privado; commit durable/CAS, validated/detach, montaje ext4 y compatibilidad WSL del binding pendientes. M1 integral NO-VERDE y estados/checkboxes intactos.

Validación completa actual adicional: /root/qa_m1_backend_current_full prepara backend-current/ con fuentes/auxiliares completos. Suite principal UID10001/cap-dropALL; credenciales nativas que requieran UID0 se verifican separadamente, sin sustituir runtime. No se ocultan fallos/hooks ausentes ni se crean alias FFmpeg.exe. La suite histórica original conserva 2109 PASS/88 FAIL/11 SKIP/1 ERROR. Uso del trabajo paralelo gestionado por una clave de lote; fuente estimado y tokens/coste reales null, sin suma individual.


## Defecto reproducible en validación actual — T-05 helper close · 2026-10-10

QA actual del IPC nativo: 84 PASS y un FAIL; focal separado reproduce un FAIL (84 no seleccionados), con fixtures reales del helper UID19000 y rival/consumer10001. test_native_second_instance_and_idempotent_close abre un descriptor retained entre dos cierres. Server.close en helper.py:160–178 deja self.lock/self.control con enteros cerrados: el segundo close ejecuta stat/close sobre descriptores obsoletos y produce EBADF, con riesgo de cerrar un FD ajeno si se reutiliza el número. Root contrasta y acepta la causa; no atribuye los otros fallos históricos de arnés al producto.

Se declara helper.py en Archivos y se autoriza corrección mínima privada con tests/test_helper.py ya existente (packages/storage-guard/tests/test_helper.py): cierre idempotente, sólo descriptores propios, causa y limpieza preservadas. Mantener todas las aserciones nativas actuales. Fresh implementer, TDD RED existente y nuevas regresiones causales si cambian ramas, >=80 % del módulo completo, revisión A/B/condicionales y QA independientes. Espejo storage-helper-close-20261010/; WAIT_ROOT_BEFORE_APPLY hasta terminar sellado de suite actual y revisión, sin mutación de producto durante QA. No se cierra T-05/M1. La selección de archivos del incremento anterior del test era formato; esta unidad sí corrige conducta y queda declarada por separado.


## Revisión de dos lentes — intento 1: T-05 cierre idempotente del helper · 2026-10-10

Candidato privado helper.py/test_helper.py, base8e9d01cb..., scope2exit0, fuera de alcance/exclusiones vacíos; C/Dauto false. A/B frescas leen diff entero y dan cero gaps Critical/Important/Minor. A ejecuta focal7 y autenticación nativa1; B focalLinux7, Windows5 ydosprobes adicionales, todosPASS con terminales0. Root conserva inspect de tres contenedores terminadosPID0/exit0; dosfallosmounts de A anteriores a pytest siguen históricos, no defectos producto.

Tabla conforme: cierre idempotente; FDreutilizado conservado; socket extranjero no borrado; ambosFDs intentados antefallo yprimaria preservada; reentrada no duplicaoperaciones; contratos/constitución intactos. ProbeB causa EINTR después de closeREAL delFD4, abreFDextranjero4 y demuestra que segundo close lo conserva, controlFD3liberado ybaseline4/final4. Son syscalls/credenciales reales sobretestigos propios; tmpfs/UUIDdoblado e inyección de errores no acreditan persistencia ext4/VHDX.

TDD privadoRED6FAIL yGREEN90PASS; whole combinado145líneas+40ramas de197=93,91%, statements145/15196,03%,sinexcl. Precisión de AST: 15 funciones top-level preservadas, de ellas12test_* y3helpers; no15tests. Se conserva candidate.receipt original con su nombre de métrica ambiguo yesta anotación explícita. Rootverifica17SHA de fuentesproporcionadosporworker ycongela227artefactosraw por su cuenta (root-frozen-artifact-inventory.json); no existe inventario independiente de worker que se pueda atribuir.

**NO aplicado todavía**: fullbackendQAactual sigue con snapshot/producto sellados; esperar SOURCE_SEAL_FINISHED antes de CAS2files yQA actual independiente. M1T05 e hitoabiertos; revisión no sustituyeQA. Rawreview/verdicts en storage-helper-close-20261010/review/. ReceiptLease privado34PASS aún revisiónA/B /root/review_receipt_lease_a y_b, no aplicado. Uso paralelo en única clave de lote, estimado/nulltokenscost; no suma individual.


## Revisión de dos lentes — intento 1: T-05 lease del recibo existente · 2026-10-10

Candidato PRIVADO; fuente/test aún ausentes en producto. Base1233049f..., scope2exit0fuera[]excl[], C/Dauto false. A conformidad conforme: focalnativo15PASS/19deselected exit0, hashes exactos y215/215inventario verificado. B lee diff completo y reproduce dos Important en syscallsWindows reales confallos/schedulesinyectados. Root verifica contra código y acepta ambos; ninguno descartado. Los34PASS/whole97,64% delcandidato no tapan defectos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important | Cierre incierto retiene número de handle y retry puede cerrar extranjero reutilizado (storage_receipt_store.py:173). | T-05 | Pendiente privado2: invalidar autoridad antesclose y no repetir un cierre incierto; mantenerdiagnóstico. | CloseHandleREAL success, KeyboardInterrupt posterior inyectada, HANDLE564 reutilizado tras14openspropios; segundo close causaWinError6 al inspeccionar extranjero. Controlordinario lo conserva. |
| B02 | Important | Snapshots concurrentes comparten puntero seek/read (storage_receipt_store.py:65). | T-05 | Pendiente privado2: serializar snapshot/estado o equivalente fiable. | Reader1 seekREAL0 ypausa; reader2 devuelvepayloadexacto; reader1 consumeEOFreal/CustodyError pese bytesintactos. |

La salida original está en el tool del revisor B; no hay un script/terminalfile de ese probe guardado. Root guarda transcripción/dictamen en review/lens-b.md yverdict-b.json, sin inventar archivooriginal. Imports4snapshot yhashes2sources+4deps exactos antes/después. A: todoscriterios límiteactual✓; B: lecturaindividual/exclusión/entrada/cierreORDINARIO✓, cierreincierto/concurrencia✗. FullCAS/durabilidad/lifecycle no verificable, ninguno aceptado como resuelto. Grados Critical0/Important2/Minor0.

/ root implement_receipt_lease continúa fix privado2 en implementation-review2/, preserva215artefactosoriginales ynamespace previo. REDcausalnativo antesfix, no retryhandleincierto, RLock mínimo o equivalente para puntero y close, deadlines de pruebas; pruebas antiguas de retry inseguro sólo pueden cambiar con justificaciónB01 explícita. Whole80sinexcl/revisión2/QA pendientes. No fuentes compartidas ni otras dependencias modificadas; globalM1NO-VERDE. Helperclose revisiónA/B conforme está preparado pero no aplicado hasta cerrar sello fullbackendQA; uso único de lote estimado/nullreal.


## Validación M1 — terminal de suite actual, adjudicación pendiente

Raíz comprueba JUnit2277casos: 2185PASS/81FAIL/11SKIP/0ERROR ypytestterminal1 (21:23:50UTC), UID10001/CapEff0/NNP1 reales. La suite sigue NO-VERDE. Focales de arnés, desglose y sello final siguen en curso; no se adjudican 81bugs. No cambian estados de tareas. Helper cierre: revisión1A/B sin gaps, candidato90PASS/whole93,91%, integración/QAactual pendientes. ReceiptLease: B01/B02 confirmados; candidato2REDcausal1+1/GREEN38/whole97,99%, revisión2A/B en curso, no aplicado. Originales preservados.


## Revisión de dos lentes — intento 2: T-05 lease del recibo existente

Lentes A+B frescas; scope0/fuera[]/exclusuario{}, C/Dfalse. Candidato privado yscopeT05; sinaplicación niaceptación. Tabla completa del intento1 transferida, ninguno descartado.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important | Retryclose incierto sobre HANDLE reutilizado | T-05 | Corregido: invalidar autoridad antes CloseHandle; incertidumbre persistente sinretry | B nativo reuse940/42opens, extranjero intacto; A aislado reuse856/50opens |
| B02 | Important | Lecturas concurrentes sobre mismo cursor | T-05 | Corregido: RLock en operaciones cortas; contextbody sinlock | B02GREEN nativo; dos snapshots exactos |
| B03 | Important | Test exige reuse dentro512opens no garantizado | T-05 | Pendiente: robusteztest; no cambiar producto correcto sin razón | A focal6PASS1FAIL target692/last2960, previosecondclose; B7PASS no rebate rojo |

Root verifica215originales/119candidato ySHA2fuentes/4deps. A0gaps; B1Important. JUnitAprimero1FAIL yaislado1PASS íntegros. GREEN38/whole97,99% es candidato yno QAactual. T05/M1 abiertos; no estados cambiados. Siguiente sólofixturetest enprivado yreview3de3.


T-07 ampliación de Archivos para corregir dos stubs de resolver en test_domain_routes.py193/296: el contrato actual ResolvedEngine exige engine_id al registrar el modelo efectivo. QA actual reproduce dos AttributeError; el alcance inicial es sólo fixtures privadas, sin modificar runtime ni rebajar aserciones. TDD, revisión A/B y QA actual antes de integración; T07/M1 continúan abiertos.


## Validación M1 — sello backend actual e integración posterior del helper

Root verifica9821artefactos/1767fuentesbeforeafter/JUnit/terminales a21:32:04UTC: fuenteproducto sin deriva hastaseal5b5e3fdc.... Ledgerdocposteriorreview2yaddedreportpre-generación declaradosen rootrecibo, no fingirSHAidénticos. Principal2185/81/11/0pytest1; FFmpegfocal19/19 ycredenciales21/21; IPC84/85 y1FAILfocal. Coveragewholemanifest66,27/pipeline75,19%0excl: gateabierto. Trescustodia(normal/EOF/backpressure)noadjudicados. HelperCAS2files21:32:34 despuésseal yreview1clean, QAactualpendiente; noaceptaciónaún. ReceiptLeaseB03 sólotestprivate3pendiente. Domainresolver2fixtures sóloprivateT07. No cambios de estados ni cierres.


## QA aceptada de componente T-05 — cierre idempotente del helper

Después de review1A/Bclean yCAS2files21:32:34UTC trasbackendseal, QAactual independienteLinux91PASS/Windows5PASS0FAIL/ERROR/SKIP, Ruffformat0. Wholehelper145/151statements+40/46branches=185/19793,9086%,sinexcl. Root102artefactos/17fuentes/JUnit/terminalPID0image7c65 y26links verified. Primerarnés/out755fallido propioexit137 preservado, segunda/out1777correctaexit0. CredencialeshijosEff/Prm/Inh/Amb0NNP1; Bnd5capssetup explícito(noafirmarCap*=0). NativeforeignFDreused conservado trasCloseHandleEINTRpostsuccess. Sólo componenteaccepted; T05/M1sinverde niestado cambiado. Informe testing/t05/storage-helper-close-qa-2026-10-10.md.


## Revisión de dos lentes — intento 3: T-05 lease del recibo existente

A+Bcontextofresco, scope0/fuera[]/exclusuario{},C/Dfalse. Tabla completa intento2 transferida,ninguno descartado. A0/B0gaps nuevos; B01/B02corregidos conservados, B03corregido testnativecalls sinprecondiciónallocator. A6PASS; B1PASS ycontraprueba1FAILexpected calls1→2. ROOT215/119/78artifacts yabsent2+4deps verified. Candidatowhole146/14997,99%0excl/38PASS, noQAactual.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important | Retryclose inciertoscalar | T-05 | Corregido, conservado2 | Producto2d0944SHAidéntico, nativecalls1→1 |
| B02 | Important | Sharedcursor concurrency | T-05 | Corregido, conservado2 | RLocknative2exactsnapshots, sin contextbodylock |
| B03 | Important | Testallocatorreuse<=512 | T-05 | Corregido sólofixturetest | A6PASS/B1PASS+REDnativecalls1→2, reuseFalseambos válidos |

Revisión aceptadaenalcance. ROOT aplica solamente newfiles2porpreimagesausentes despuésbackendseal. QAactualindependientependiente; noT05/M1completion.


## Revisión de dos lentes — intento 1: T-07 fixtures resolver con engine efectivo

A+Bfrescas0gaps, scope1exit0fuera[]exclusuario{},C/Dfalse. Sólo2fixtureSimpleNamespacereturnsengine_idmock alineadosconResolvedEngineactual; runtime/assertsrestoASTsinchange. RED2AttributeErrorengine_idexit1→GREEN18dominio+2focal+11idioma candidatoexit0, Ruffformat0. Root352artefactos/182fuentespreimagesverified. Cobertura runtimechanged n/a test-only, no80fingido. ROOTCAS1testposteriorsealbackend/reviewclean; QAactualindependientependiente. NingunestadoT07/M1cerrado.


## QA aceptada de componente T-05 — lease del recibo existente

Despuésreview3A/Bclean ynewfileCAS21:40:11UTC, QAactualnativeWindows38PASS0FAIL/ERROR/SKIP ywhole146/14997,986577%0excl; coveragefail-under80/Ruff/format0. Root91artefactos/6fuentesbeforeafter/pin+JUnit/8terminalcommandsverified. Probeown25cicloshandles136→149→136trasobjectdestroy, B03calls1→1eightforeignident/payloadintactos,reuseFalseobservaciónsinprecondición. Primerfinalizadorcp1252fallido propio conservadosinreinterpretarpytestverde como falloprod; reportUTF8sealed. Sólo componentaccepted; nocreate/adopt/write/commitdurable/lifecycle/WSL/validated/detach. T05/M1estadosnochanged. Informe testing/t05/storage-receipt-lease-qa-2026-10-10.md; PDFomitidodepsausentes yqa-gate n/a technical sinJSONfabricado.


## QA aceptada de componente T-07 — fixtures del resolver

Root verifica 400 artefactos y 182 fuentes actuales antes/después; Windows18/18 y Docker Linux18/18 oficiales, 58 imports privados por plataforma. pytest/uv/docker y Ruff/format0; contenedor propio detenido PID0 imagen fijada7c65, UID10001/capdropALL/NNP/rednone. Se conserva el primer fallo de captura temporal sobre bind Windows y su corrección exclusiva TMPDIR Linux. Cambio test-only: solo dos engine_id="mock", aserciones/runtime intactos, cobertura runtime cambiado n/a. Informe testing/t07/domain-resolver-fixtures-qa-2026-10-10.md. Componente aceptado, T07/M1 abiertos; sin aceptación UI/GPU/ext4/manual ni cambios de estados.


## Diagnóstico causal Linux y siguiente corrección privada T-05

Root verifica 867 artefactos, 813 exportaciones y 32 comparaciones snapshot/producto sin discrepancias. normal: ECONNRESET en canal terminal tras salida leader, sin alcanzar close, probado con control nativo. EOF/backpressure: deadlines anteriores al estímulo, probados con precedencia temporal y controles nativos, no defectos de sus gates. Se autoriza Fase4 privada con RED causal antes del fix mínimo y barreras reales de estímulo; sin rebajar UNKNOWN, sin cambiar plazo productivo ni simular hooks. Ocho fault hooks ausentes siguen pendientes. Archivos añade explícitamente los tres tests/helper de fixtures por reparación portátil y diagnóstico causal; runtime audio intacto. Revisión fresca y QA obligatorias antes de CAS root; T05/M1 abiertos. Diagnóstico .cache/dev-cycle/m1/linux-custody-current-debug-20261010/DIAGNOSTICO.md.


## Diagnóstico Windows de identidad de carpeta — T-05

Root verifica inventario/sello, tres cambios nativos exclusivamente0x10000000 con dev/ino/mode/tag y FileId128/volumen estables. process_audio real falla UNSAFE_PATH antesFFmpeg, cleanup carpeta vacía falla por enumeración; junction real rechazado y sustitución nativeinode distinta detectada. Bit semántica desconocida, NO RECALL_ON_OPEN ni cloud/provider afirmado. Fase4 privada autorizada: normalizar SOLO ese bit incidental conservando todas las otras señales de identidad/atributos y política reparse/marker/ownership. RED previo+regresión real+negativos obligatorios, revisión fresca yQA antesCAS. Ampliación de Archivos exactos por causa shared pipeline/cleanup, sin cambiar runtime de música ni doctrina de custodia. T05/M1 abiertos. Diagnóstico .cache/dev-cycle/m1/windows-directory-attributes-debug-20261010/diagnosis.md.


## Revisión de dos lentes — intento 1: T-05 — pruebas portátiles de audio

Lentes A/B limpias, C/Dfalse por selector determinista. Scope4 dentro/0fuera/usuarioexcluidos{} exit0; root2269artefactos/6fuentes verificadas. A conformidad alcance/constitución/aserciones/runtime intacto, CA1/2/3integrales no verificables y pendientes. B55/55 asercionesAST preservadas, no defects introduced. RED causal arnésLinux10FAIL50PASS; candidato180PASS5legitWindowsSKIP, wholemanifest84,31/pipeline96,24%0excl. Nuevos tests de contratos validan comportamiento existente (TDD n/a para ampliación, sin rojo fingido). Windows169PASS9SKIP7FAIL16errors conservados, fixruntime separado en curso. CAS root4testfiles integrado con exactpreimages/newconftestabsent; QA actual posterior pendiente, componente aún NOaceptado. No T05/M1cierre ni estados cambiados. Uso loteROOTnull/estimado, no sumar ventanas. Evidencia .cache/dev-cycle/m1/audio-post-portability-20261010/review/.


## QA aceptada de alcance Linux — T-05, pruebas portátiles de audio

DespuésCAS4tests22:01:07UTC/review1A/Bclean, QA independiente actualLinux180PASS5legitWindowsSKIP0FAIL0ERROR, wholemanifest215/25584,31% ypipeline128/13396,24%0excl yreportfail-under80cada0. Root307artefactos/237fuentes/19importsprivados/14enlaces+JUnit/terminales/imagePID0verificados. Primerinfra156PASS5SKIP24ModuleNotFoundError engine_mock se conserva; snapshot2 incorpora paquete transitivo actualsin cambiodefixtures/source. Runtimepipeline11f72... yhelperda1fb... baselinevigente; fixWindows en privado, no atribuir estos SHAs a futura fuente nueva. Solo alcanceLinux aceptado; Windows permanece rojo sinrerun redundante, no aceptaciónmultiplataforma/T05/M1. Informe testing/t05/audio-portability-linux-qa-2026-10-10.md. qa-gatePlaywright n/a técnico, PDFomitido depsausentes. Estados sin cambios.


## Revisión de dos lentes — intento 1: T-05 — atributos incidentales de directorio

A/B sin gapsintroducidos, C/Dfalse porselector; scope4dentro/0afuera/exclusuario{}exit0. Root2357artefactos/4candidatos/3preimages+4overlayfixtures+5dependenciasverificados. RED: test_native_child_creation_preserves_directory_identity falló por atributo incidental con identidadFileId128 estable; test_native_empty_directory_cleanup falló Entrada cambiada durante limpieza, ambos nativosWindows pytest1 antesfix, receiptsUTC propios. Máscara SOLO0x10000000directorios, otrasattrs/devino/modetag/políticareparsemarker/registryforeignpreservation intactos; primaryerrorbaseline no cambia. Linux3causalesNT-only fallos preservados/guards exactos, Windowslos ejecuta. CandidatoWin213PASS13SKIP/Linux207PASS19SKIP, wholepipeline96,32/helper94,44Win88,89Linux0excl/gatescada0. FreshB18nativefocalPASSexit0en runnerenmemoria segúnretorno, no inventararchivo/JUnit. CASroot4files aplicado, QAactualpendiente; estadosT05/M1siguenabiertos ynoaceptarcomponentehastaQA. OriginalinfraHatchling2errors yexportprematuro preservados. Evidencia .cache/dev-cycle/m1/windows-directory-attributes-fix-20261010/review/.


## Evidencia RED exacta — T-05, identidad de directorios

La nota anterior abrevia erróneamente el segundo test como test_native_empty_directory_cleanup; el nodo oficial ejecutado es el siguiente. Se conserva la nota histórica y se corrige la referencia con JUnit/argv/UTC reales, sin nueva ejecución.

RED: `packages/audio-post/tests/test_directory_attributes.py::test_native_child_creation_preserves_directory_identity` falló con `assert (154211489804...6895, 1572880) == (154211489804...95, 270008336)
  
  At index 3 diff: 1572880 != 270008336
  Use -v to get more diff` · 2026-10-10T22:01:46.241049+00:00 · pytest exit1.

RED: `tests/test_fixture_confinement.py::test_cleanup_native_empty_directory_without_identity_change` falló con `ValueError: Entrada cambiada durante limpieza` · 2026-10-10T22:01:50.842054+00:00 · pytest exit1.



## QA actual aceptada por ROOT — T-05, identidad de directorios Windows/Linux

Tras revisión A/B sin hallazgos y CAS de cuatro ficheros a las 22:12:39 UTC, la QA independiente de las fuentes actuales pasa **Windows: 213 PASS / 13 SKIP; Linux: 207 PASS / 19 SKIP**, sin fallos ni errores. Cada selección tiene 226 casos. Cobertura oficial de cada módulo completo: pipeline 131/136 (96,32 %) en ambos; scripts/test_workspace.py 119/126 (94,44 %) Windows y 112/126 (88,89 %) Linux. Cuatro gates --fail-under=80 exit 0, sin líneas excluidas. Ruff check/format exit 0.

ROOT rehasha los 1.050 artefactos, contrasta 379 fuentes/herramientas privadas con el checkout actual y verifica 21 imports del proyecto por plataforma, JUnit, terminales y 26 enlaces. Docker propio: UID10001, cap-drop ALL, no-new-privileges, red none, export anterior al apagado, PID0 y exit0. Los dos intentos Windows con herramientas omitidas por QA se conservan (FFmpeg y después Node); la selección final usa herramientas gestionadas reales sin modificar fuentes. Informe: testing/t05/directory-attributes-current-qa-2026-10-10.md; recibo privado verify-qa-current-root.receipt.json.

Aceptación limitada al componente. T-05 y M1 permanecen abiertos: no acredita publicación persistente, recovery/Range, GPU ni escucha/manuales. qa-gate Playwright n/a en esta selección técnica; sin resultado E2E fabricado. Estados y checkboxes sin cambios.

El candidato de custodia Linux permanece privado: padre 88,32 %, supervisor 75,46 % (gate rojo). Sus 40 pases nativos y 24 focales de carga no sustituyen ocho negativos pendientes por hooks ausentes; las pruebas de audio congeladas 7+2 pasaron, pero el último bootstrap instrumentado dio 1 PASS / 1 FAIL AUDIO_TRANSCODE_FAILED sin causa aislada. No se aplica ni se acepta ese candidato. El contenedor propio se detuvo/eliminó con PID0, stop/remove exit0, **State.ExitCode137**; no se declara exit0 del contenedor. Mantiene las exportaciones y los 18 zombies adoptados observados antes del stop, sin workloads vivos.


## T-05 — diagnóstico acotado del positivo audio instrumentado

El análisis del gap confirma que terminal_ack ya tiene todas sus líneas medidas (no cobertura de ramas); añadir esos casos no resuelve el déficit del supervisor. Se despacha contexto fresco con brief determinista T-05 y skill debug-root-cause, fases 1–3, sobre el rojo AUDIO_TRANSCODE_FAILED del último bootstrap. Máximo una pareja causal control/instrumentado del mismo positivo y fuentes congeladas; stderr real, sin nuevos hooks, fixes de producto ni integración. Los ocho hooks originales y el gate whole siguen pendientes. Ownership privado linux-audio-instrumentation-debug-20261010; ROOT acepta y mantiene este ledger.

El lote paralelo anterior cierra a las 22:23:09 UTC: reloj 1h21m, **fuente estimado, tokens/eur/horas-IA null**; no se presenta como coste real ni se suman ventanas solapadas. Nueva ventana secuencial m1/T-05-debug-audio-instrumentation. Estados sin cambios, objetivo activo sin pausa; M1 NO-VERDE y M2/T-02 no iniciado.


## T-05 — diagnóstico causal aceptado del arnés execve

ROOT verifica 68 entradas del inventario, 1.984 entradas históricas intactas, JUnit, snapshots antes/después, stderr real de FFmpeg y el journal nativo. Pareja única: control con el mismo wrapper/save desactivado e instrumentado dan 1 FAIL cada uno. El traceback demuestra TypeError al serializar path=PosixPath en JSON antes de original_execve; el hijo termina126, take failed/AUDIO_TRANSCODE_FAILED y assets0, con cleanup nativo confirmado. Save no es necesario para ese fallo; no se atribuye a codecs ni a la canción.

La fase4 propuesta normaliza exclusivamente la copia de metadata para JSON, conservando exactamente los argumentos originales de execve. No se modifica producto por este hallazgo. Docker propio --init, export anterior al stop, PID0/State.ExitCode143; stop/remove y wrapper0 no equivalen a pytest1. Supervisor whole75,46% sigue rojo. Estados intactos; no cierre M1/T05. Evidencia privada linux-audio-instrumentation-debug-20261010/DIAGNOSTICO.md y verify-diagnosis-root.receipt.json.


## T-05 — reparación del arnés y diseño del controller durable en curso

Tres actores frescos con ownership privado separado y briefs deterministas: metadata execve (fase4 del diagnóstico aceptado), arnés de los ocho negativos configurados sin bootstrap y opciones del controller durable de almacenamiento. El arnés de negativos debe inyectar fallos explícitamente en testfixtures, conservar todos los procesos/pidfds/signals/waits reales y preservar assertions; no añadir envhooks a producto ni fabricar journal/final/reap. El diseño debe resolver commit/CAS/crash recovery/validated/detach, preservar ReceiptLease y PublishedDiskBinding aceptados, sin adoptar el SMOKE ni prometer power-loss. ROOT decide la alternativa bajo la autorización del usuario de tomar las mejores decisiones y publica ADR tras revisión.

Único lote m1/lote-execve-harness-storage-design; el marcador diagnóstico anterior se cerró22:29:11UTC (ventana22:23:30–22:29:11), fuente estimado/tokens/eur/horasnull. No sumar ventanas solapadas. Estados sin cambios; M1 no aceptado/M2T02 no iniciado.


## T-05 — fix de metadata del arnés aceptado en alcance privado

ROOT verifica 219 entradas/200 artefactos regulares del inventario, hashes del wrapper y reporte, cinco JUnit y terminales/StateExit143 exactos. RED test_execve_metadata.py::test_execve_metadata_accepts_pathlike_and_bytes_without_mutation falló con TypeError PosixPath JSON · 2026-10-10 UTC; GREEN mismo nodo1PASS, printf nativo y argumentos originales intactos. El positivo FFmpeg real1PASS18,01s y journal2registered/2reaped confirmado demuestra la corrección del arnés en las fuentes congeladas. Fallo BOM posterior del exporter queda preservado y se recupera offline sin repetir el positivo.

Focales terminales1PASS2,95s y1PASS3,15s tras reparar el defaultsave del harness. La captura pública tiene collector/save reales pero ninguna línea de la copia de supervisor; se detecta filtro source que no incluye /tmp/native/.../source/ donde se ejecuta el focal. No se atribuye a un bug de coverage ni se declara gateverde. Combinación oficial COPIAS/SHA idénticos mantiene88,32/75,46. Los históricos1.984 intactos. No se aplica ningún runtime canónico por este fix privado.

El arnés de negativos aporta nuevo RED auténtico del candidato: notify(final) falla con ValueError inyectado, todos los hijos propios waited y testigoajeno vivo, pero espera ACK no entregable y termina120. ROOT autoriza recheck de incertidumbre después de notify y antes de ACK, sólo en candidato privado; ocho casos pasan después. Fullnative/whole/review/QA/CAS pendientes. No debilitar assertions ni publicar final inventado. Estados sin cambios.


## Revisión de dos lentes — intento 1: T-05 diseño durable — correcciones documentales privadas

Lentes A+B; selector C/D false. Scope inicial falló por CR mal posicionado en Archivos: corregido sin cambiar estados; scope posterior8archivos/0fuera. No código ni QA física; TDD n/a prosa. O2 elegida bajo delegación del propietario.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | ADR0075:48 remite a design.md sin apartados4.2–4.6 | T-05 | Enlace al storage-durable-design.md correcto, candidato privado; recheck2 pendiente | A criterio6/docs-style5; attempt1-source.diff y prepare-receipt preservados |
| A02 | Minor | storage-durable-design:192 enumera C0–C7 en frase larga | T-05 | Tabla de cortes con momentos y reglas idénticos, privada; recheck2 pendiente | A docs-style1/4; fix_documentation_root.py |
| B01 | — | Sin defectos concretos de corrección | T-05 | Sin cambios semánticos requeridos | Lente B: autoridad/CAS/recovery/compatibilidad/flush/detach conformes documentales |

Tabla A completa: cierres/CA1/CA2/CA3 NA; alcance✓; tests-coberturaNA; constitución✓; verificación cerradasNA; trazabilidad✗A01; docs-style✗A01/A02; elección O2/gate conservado✓. B completa: autoridad/CAS, recovery, compatv1, validated/detach, límitesflush✓ documentales; funcionamientocontroller no verificable. No se cierran tareas.

**T-05 — candidato de custodia Linux comprobado por ROOT, revisión/QA/CAS pendientes:** verify-candidate-root.receipt.json UTC22:50:06 verifica2272entradas/1783artefactos, tar1063miembros/798regulares,96fuenteshistóricas y106dependenciasactuales. JUnit causalesRED1/RED1, GREEN8/49/7 y3caracterización; no atribuir una invocación52. Wholeparent88,32%/supervisor80,78%, ceroexclusiones,gate0; AST190asserts originales intactos. Supervisor557e3c, parent0d021, arnesef025 privados. Ambos fixes privados desde baseline canónico78c1/aae8 necesitan revisiónA+B+D (selector Dworker true,Cfalse); scope4/0fuera. Exportfinal verificado antesstop/remove0,Pid0/exit143delsleeper, sinworkloads; .cache/dev-cycle/m1/native-fault-harness-20261010/REPORT.md. Primer export tmpfs perdido y recuperación justificadaconservados. Sin GPU/admin/Ollama/incumbente.

**T-03 — check contractual vigente:** ejecución ROOT `uv run --frozen --no-sync --all-packages python scripts/export_contracts.py --check` exit0: `engine-v1.json up to date` y `openapi.json up to date`. Captura tool chunk07001b; check readonly, no atribuir suite completa ni cierreM1.


## Revisión de dos lentes — intento 2: T-05 diseño durable — A/B conforme

| # | Grado original | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Referencia al diseño erróneo | T-05 | Corregido: enlace y apartados4.2–4.6 exactos | A2/B2 conformes, candidatos7/7SHA |
| A02 | Minor | Cutpoints en enumeración larga | T-05 | Corregido: tablaC0–C7, mismas reglas | A2/B2 semántica intacta |
| B01 | — | Sin defectos | T-05 | Veredicto conservado | Autoridad/CAS/recovery/compatv1/detach/powerloss documentales conformes |

Tabla completa A2: cierres/CA1/CA2/CA3 NA; alcance✓; test-coberturaNA; constitución✓; verificaciones cerradasNA; trazabilidad✓; docs-style✓; elección acotada✓. B2: A01/A02✓, cinco invariantes/grupos documentales✓ conservados; funcionamiento runtime no verificable. C/D no seleccionadas; cero gaps pendientes documentales.

**QA/adopción documental:** ROOTCAS7docs22:55:20, actualización administrativa de publicación separada del contenido revisado. QA205/205+140enlaces encontróDOC01/DOC02Minor de estado actual; ROOTcorrigiósólo2paragraphs22:58:45; QA recheck42/42exit0/sin gaps. ROOTverifica18artefactos de sellos+7fuentes antes liberarcodec23:01:33. [Informe](testing/t05/storage-durable-design-qa-2026-10-10.md). ADR0075 aceptada bajo delegación, O2 diseño aprobado; no runtime/gateM1 atribuidos. Historial y originales preservados.

## Revisión de dos lentes — intento 1: T-05 custodia Linux — A+B+D sin gaps

| Lente | Criterios completos | Gaps | Evidencia |
|---|---|---|---|
| A | Objetivo/alcance/tests/constitución/TDD/descripciones✓; CA1/CA2/CA3 integrales pendientes | 0 | Diff4sources yAST190 intactos; baseline153 con1BPassert másfuerte; JUnit8/49/7/3separados; whole88,32/80,78%sinexcl |
| B | ACK/notify/EOF-backpressure/cancelbeforebirth/aislamiento/testigos/audio✓ | 0 | Artefactos nativos con waits/reap/foreignwitness; bootstrap8configs auditado, sin hooks producto |
| D | ACKsin espera fija, drainacotado, arnesecosto acotado✓ | 0 | Sonda Windowshelper20ACKmediana0,021ms, noLinuxattribución; JUnitLinux terminal/audioleídos |

SelectorCfalse/Dtrueworker, scope4/0fuera. ROOTCAS4sources22:57:58: parent0d021/supervisor557e3c/teste5d9/arnesef025, preimágenes78c1/aae8/be8 intactas. QA independiente actual52+7/whole80 en curso; primer bindocultóvenv exit127sinPython, luego snapshot omitiófixturechild causando32FAIL20PASS; ambos errores de preparaciónQA preservados, no defectos producto demostrados. Actor audita14referencias/18files antes agregarfixturechild6635cff y ejecutar nueva suite actual. No se aceptan resultados anteriores como QA verde.

**T-05/U1 formato liberado:** W1–W6 ratificados por ROOT23:01:33, brief06aeaa/planac7522 privados; 96header/152PREPARE/176COMMIT bytes LE,64slots/maxpayload1MiB/B512–65536. Comparación bytes/replay lógico no capacidad nativa. Rootclarifica parent_chain drive→journalparent/childsteps/projectonce/noalias/crossvolume. Preservarparserv1 y usar validación portableWindows; no adoptar ni normalizar seed. Accionesrequests adicionales y resolucióncausal no habilitadas hasta contratos futuros. Actor implement_storage_journal_codec posee sólo2sources nuevas privadas, conTDD/whole80/review/QA pendientes; no código canónico aún.

**Usage:** loteexecve-harness-storage-design cerrado22:56:49 (27mreloj; fuenteestimado/tokens/eur/horasIA realesnull). Nuevo único marcador m1/lote-custody-review-qa-codec abierto22:56:53; sin markers por actor ni sumar solapes. Estados/checks formales permanecen sin cambio.


## T-05 — QA independiente actual de custodia Linux aceptada

ROOT verifica el recibo `custody-current-qa-root.receipt.json`: 2.312 artefactos, 109 fuentes actuales y 62 imports por SHA; tar final 1.190 miembros/908 regulares, tamaño y SHA cotejados antes de stop; ambos raw SQLite íntegros. JUnit válido 52/52 nativos y 7/7 CPU/SQLite/audio/FFmpeg, cero fail/error/skip; pytest/dockerexec 0. Whole oficial individual 88,3212 % (242/274) y 80,7780 % (353/437), exclusiones 0 y gate 0. La variante scheduling con SHA distinto no se mezcla. Contenedores propios retirados con stop/rm 0 y Pid 0; Exit143 del sleeper no es el resultado de pytest. Se aceptan únicamente este componente y las cuatro fuentes CAS del 22:57:58 tras revisión A/B/D sin gaps.

Se mantienen los cinco diagnósticos de preparación, incluidos preflight EPERM y autenticidad integral de herramientas comprobada concurrentemente durante la suite final. No se simula un preflight anterior ni se repite la suite nativa verde. QA Playwright/PDF N/A en este alcance. [Informe](testing/t05/linux-custody-current-qa-2026-10-10.md). T-05/M1 abiertos; persistencia/E2E/manuales/Git no acreditados por este componente.

**U1/W6 aclaración ratificada por ROOT:** `record.arguments.phase` y `receipt_sha256` deben coincidir exactamente con el recibo actual del envelope y el SHA de sus bytes completos con LF. `reserve.size_bytes/project_path` coinciden exactamente con los campos del recibo actual. El actor debe probar cada frontera con control válido y mutación aislada RED antes de implementar; no se amplían acciones ni efectos. Implementación solo privada en sus dos fuentes; revisión/QA/CAS pendientes.


# Revisión de dos lentes — intento 1: T-05/U1 codec puro — tres Important

Lentes A+B frescas, sin C/D (selector auto false/false). Diff privado de tres archivos; scope exit0, cero fuera/avisos/exclusiones de usuario. Ninguna tarea se cierra; U1/T-05/M1 no aceptados. ROOT conserva la entrega171artefactos, fuentes4e8d5c/732696, 200Windows+200Linux/whole94,636678%sinexcl. Los revisores leyeron los tres diff completos. ROOT corroboró los tres escenarios con controles válidos; no rebatidos ni deuda aceptada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Status público retiene lista mutable con igualdad personalizada; misma inspección cambia JOURNAL_BLOCKED→append al mutar caller | T-05/U1 | Pendiente: escalares estrictos en JournalInspection/RequestDecision | storage_journal.py:777/:910; brief:23; repro A y ROOT |
| B01 | Important | History/published prefix usa igualdad Python y permite sustituir evidence true por1 aunque cambian bytes | T-05/U1 | Pendiente: continuidad exacta de tipos/bytes | storage_journal.py:823/:623; control clean y mutante clean head2; ROOT lo reprodujo con request record y recibo raw_verified |
| B02 | Important | JSON entero5000dígitos deja escapar ValueError del intérprete; no JournalError ni clasificación corrupt de inspect | T-05/U1 | Pendiente: rechazo tipado y clasificación fail-closed sin ampliar límite global | storage_journal.py:347/:352/:890; control válido, payload<1MiB y frames correctamente resellados; A/B/ROOT |

## Tabla completa de la lente A

| Criterio T-05/U1 | Veredicto | Evidencia |
|---|---|---|
| Alcance codec/tests/contrato | ✓ | tasks.md:208; scope3/0outside/0avisos, diff2079líneas |
| W1 LE/versión/geometría/digest/padding | ✓ | source:94/:155/:178; tests:770/:1001/:1025/:1041 |
| W2 slots64/capacidad/límite envelope | ✓ | source:98/:107/:837; tests:782/:1041, B4096 EOF67637248 |
| W3 PREPARE/COMMIT/hashes compartidos | ✓ | source:691/:717/:795; tests:314/:339/:361/:953; golden focalPASS |
| W4 JSON/budgets/schema | ✓ fronteras comprobadas; B02 pendiente | source:302/:315/:343/:512; tests:180/:204/:738/:848/:993 |
| W4 IDs/paths/identidades/parents | ✓ | source:115/:245/:253/:404/:525; tests:240/:693/:859/:977/:983 |
| API dataclasses sólo bytes/tuplas/scalars estrictos | ✗ A01 | source:777/:910; brief:23 |
| Snapshot bytes/proyección fresca/mutación | ✓ | source:204; tests:111 focalPASS |
| v1 portable/parser readonly | ✓ | source:413; tests:658; seisphasegoldenWin/receipt3+3, SHA811a5782 |
| Published exacto/preservación | ✓ casos comprobados; B01 pendiente | source:615/:807; tests:604/:625; RED08→GREEN08 |
| W5 scan64/gap/fork/predecessor/daño/EOF | ✓ estructura comprobada | source:830/:849/:892; tests:401/:434/:496/:953 |
| W5 incomplete sin head/continuación/replay | ✓ | source:894/:932; tests:410/:526 |
| W6 replay/conflict/stale/full | ✓ | source:925; tests:507/:530/:839; full64 exactretry |
| W6 reserve/record actualreceipt | ✓ | ledger:4574; source:631; tests:883; RED10→GREEN10 |
| Win/Linux/imports/pureza | ✓ | JUnit200+200 conimports/SHA; source:8; guardtests:793 focalPASS |
| TDD controles causales | ✓ entregado | RED01–RED12-no-mocks; RED07 fixtureinválida yRED12spy sincrédito |
| Whole80sinexcl/Ruff/receipt | ✓ | 547/57894,636678%; Ruff0, regression3+3 |
| Review/QA antesCAS | No verificable aún | Puertas pendientes; candidato privado no adoptado |
| Constitución/tareas abiertas | ✓ | Constitution:32/:43/:63/:65/:73; T05:202 en-progreso, verificación:210 pendiente |
| Generados/interoperabilidad | NA | Sincommands/agents/hooks; docwire/API actualizada:410/:459/:462 |

## Tabla completa de la lente B

| Criterio T-05/U1 | Veredicto | Evidencia |
|---|---|---|
| W1–W3 layout/frames/padding/hashes/EOF | ✓ | source:94/:178/:691/:795 ygoldens completos |
| W4 JSON acotado/errores tipados | ✗ B02 | Repro5000digits |
| W4/W5 history/published exactos | ✗ B01 | Reprobool/int |
| W5 scan64/gap/fork/incomplete | ✓ | source:849; tests:401/:434/:953 |
| W6 replay/conflict/stale/full/receipt | ✓ | source:633/:925; tests:507/:530/:883 |
| Bytes/proyección/pure codec sin effects | ✓ | source:204; tests:111/:782/:793 |

A verificó171artefactos y focales golden/proyección/pureguard sin repetir suites. B leyó959líneas source/1048tests y reprodujo ambos defectos por stdin -B. Sus consultas nativas sobre CON .txt no demostraron alias (tampoco su control CON.txt), por lo que no se graduaron como gap. Ambas consultas knowledge-find ADR/backend dieron0aciertos.

ROOT verificó171artefactos, tar170regulares, rawSQLite, JUnit200+200 y fuentes exactas, y retiró el contenedor ya detenido97e63...tras exportverificado/Pid0/rm0. La primera prueba propia B01 empleó un control incorrecto y falló antes del escenario: root-failed-b01-control.py se conserva como diagnóstico sin crédito. El recibo root-reproductions.json corresponde a la reproducción corregida con control válido y confirma A01/B01/B02. NT/mount/E2E/cierreglobal no se evalúan.

Traspaso al intento2: conservar TODOS los criterios aprobados y NA, los tres gaps y estos diagnósticos. Reevaluar sólo lo corregido; no reabrir aprobados salvo evidencia nueva. Fix1 privado exige RED causal previo, GREEN, fuentes frozen, whole80sinexcl, Ruff y plataformas afectadas; entrega original intacta. QA independiente continúa pendiente después de reviewconforme.


## Revisión de dos lentes — intento 2: T-05/U1 codec puro — sin gaps pendientes

Lentes frescas A+B sobre el diff canonical privado be7af4ecee4498a146ce058f21a9a9d40c460940, tres archivos/2244 líneas completas. Scope0,0fuera/avisos/exclusiones de usuario; C/D auto false. Conservados todos los20criterios A y6B del intento1; sólo A01/B01/B02 reevaluados. No deuda aceptada ni gaps rebatidos. Candidato privado, sin QA independiente/CAS todavía; T05/M1 abiertos.

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Status mutable retenido | T-05/U1 | Corregido: type(status) is str antes del enum | scripts/storage_journal.py:780/:913; ambas lentes2/2 focales; controlbloqueado/mutable rechazado |
| B01 | Important | History/published true==1 aunque bytesdistintos | T-05/U1 | Corregido: comparación de serialización canónica | source:625/:826; ambas lentes2/2; B2 además false→0/anidado corrupt sinhead |
| B02 | Important | JSON5000digits escapaba ValueError | T-05/U1 | Corregido: parser traduce ValueError a JournalError sin ampliar límite | source:354/:893; ambas lentes4/4; generation/epoch yframes independently resellados, límite4300 intacto |

Gaps pendientes: **0Critical/0Important/0Minor**.

### Tabla completa de la lente A — intento 2

| Criterio T-05/U1 | Veredicto | Evidencia relativa al snapshot |
|---|---|---|
| Alcance codec/tests/contrato | ✓ conservado | tasks:208; scope3dentro/0fuera/0avisos |
| W1 LE/versión/geometría/digest/padding | ✓ conservado | source:94/:155/:178; tests:770/:1167/:1183 |
| W2 slots64/capacidad/límite envelope | ✓ conservado | source:98/:107/:837; tests:782/:1183 |
| W3 PREPARE/COMMIT/hashes compartidos | ✓ conservado | source:694/:720/:798; tests:314/:339/:361/:953 |
| W4 JSON/budgets/schema | ✓ B02 corregido | source:352/:354/:893; tests:1097/:1108; focal4PASS |
| W4 IDs/paths/identidades/parents | ✓ conservado | source:115/:245/:253/:406/:527; tests:240/:693/:859/:977/:983 |
| API dataclasses bytes/tuplas/scalars estrictos | ✓ A01 corregido | source:780/:913; brief:23; tests:1018; focal2PASS |
| Snapshot bytes/proyección fresca/mutación | ✓ conservado | source:204; tests:111; focalintento1 conservado |
| v1 portable/parser readonly | ✓ conservado | source:415; tests:658; acceptedSHA811a5782 intacto,regresión3+3 |
| Published exacto/preservación | ✓ B01 corregido | source:625/:826; tests:1049/:1070; controlesválidos/focal2PASS |
| W5 scan64/gap/fork/predecessor/daño/EOF | ✓ conservado | source:833/:852/:895; tests:401/:434/:496/:953 |
| W5 incomplete sin head/continuación/replay | ✓ conservado | source:897/:935; tests:410/:526 |
| W6 replay/conflict/stale/full | ✓ conservado | source:928; tests:507/:530/:839; full64/exactretry |
| W6 reserve/record actualreceipt | ✓ conservado | tasks:4574; source:634; tests:883; RED10→GREEN10 |
| Win/Linux/imports/pureza | ✓ conservado | source:8; tests:793/:970; JUnit208+208 SHA5db83df2 |
| TDD controles causales | ✓ | históricosconservados; FIX1redA01/B01/B02=8causalesruntime4e8d,green8 |
| Whole80sinexcl/Ruff/receipt | ✓ | 551/58095%; excluded_lines=[];Ruff0/receipt3+3 |
| Review/QA antesCAS | No verificable aún, conservado | QAindependiente/CAS pendientes; este pase no los sustituye |
| Constitución/tareas abiertas | ✓ conservado | Constitution:32/:43/:63/:65/:73; tasks:202/:210 en-progreso/verificaciónpendiente |
| Generados/interoperabilidad | NA conservado | Sincommands/agents/hooks; docwire/API:406/:452/:462 |

### Tabla completa de la lente B — intento 2

| Criterio T-05/U1 | Veredicto | Evidencia |
|---|---|---|
| W1–W3 layout/frames/padding/hashes/EOF | ✓ conservado | review1tablaB, sin delta de fronteras |
| W4 JSON acotado/errores tipados | ✓ B02 corregido | source:353; focal4/4,JSON_INVALID/bloqueante/límite4300 |
| W4/W5 history/published exactos | ✓ B01 corregido | source:625/:826; focal2/2,true→1,false→0,anidado |
| W5 scan64/gap/fork/incomplete | ✓ conservado | review1tablaB, scan yclasificaciónpreservados |
| W6 replay/conflict/stale/full/receipt | ✓ conservado | review1tablaB,decisiónpreservada |
| Bytes/proyección/pure codec sin efectos | ✓ conservado; A01 corroborado | source:780/:913; focal2/2,mutables/subclassesstrrechazados |

Ambas lentes usaron env.ps1/.venv python -B por stdin/stdout, verificaron8focales, los171artefactosoriginales y80FIX1, fuentes/SHA/imports, JUnit208Win+208Linux/whole95sinexcl, sin repetir suites completas. Knowledge-find ADR/backend0aciertos. A/B no escribieron canon/ledger ni namespace frozen. NT/mount/controller/E2E/cierreT05/M1 fuera del alcance U1.

ROOT verificó80FIX1+171originales,74tarregulares,8REDcausales/8GREEN,preimágenescompletas,ASTruntimepreformatoequivalentefinal,JUnit208+208/rawSQLite/whole95sinexcl,Ruff/receipt3+3/6goldenWin/readonlySHA y exportantesstop/ID/Pid0/rm0. Tres symlinkspytestcurrent ephemeral inspeccionados y noextraídos. Dos errores de supuesto del verificador ROOT (GREENpreformatoSHA ytarconpytestlinks) corregidos, preservados como diagnósticos; no son bugsproducto ni REDTDD. Recibo fix1-delivery-root.receipt.json. Original FIX1 privadoinmutable.

QAindependiente siguiente, no CAS hasta verde técnico validado. Jira desactivado; sin publicación ni promoción conocimiento. Métricas realesnull, únicoloteROOT vigente.


## T-05 — codec U1 aceptado tras revisión 2 y QA independiente

- RED: `test_a01_public_status_rejects_mutable_scalar[JournalInspection-JOURNAL_CORRUPT]` falló con `Failed: DID NOT RAISE JournalError` · 2026-10-10T23:28:09.401500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_a01_public_status_rejects_mutable_scalar[RequestDecision-append]` falló con `Failed: DID NOT RAISE JournalError` · 2026-10-10T23:28:09.401500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b01_chain_history_bool_to_int_changes_exact_bytes` falló con `AssertionError: assert ('clean' == 'JOURNAL_CORRUPT'      - JOURNAL_CORRUPT   + clean)` · 2026-10-10T23:28:10.181895+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b01_published_prefix_bool_to_int_changes_exact_bytes` falló con `Failed: DID NOT RAISE JournalError` · 2026-10-10T23:28:10.181895+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b02_large_integer_has_typed_error_without_global_limit_change[generation]` falló con `ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit` · 2026-10-10T23:28:11.124500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b02_large_integer_has_typed_error_without_global_limit_change[epoch]` falló con `ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit` · 2026-10-10T23:28:11.124500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b02_large_integer_correctly_hashed_wire_is_closed[generation]` falló con `ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit` · 2026-10-10T23:28:11.124500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.
- RED: `test_b02_large_integer_correctly_hashed_wire_is_closed[epoch]` falló con `ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit` · 2026-10-10T23:28:11.124500+00:00; runtime previo4e8d5c, preimagen/JUnit conservados; GREEN posterior y suite actual208+208.

ROOT adopta tres archivos SHA idénticos al snapshot revisado: runtime5db83df2/test6d40fafd/doc673cda4f. A/B intento2:0Critical/0Important/0Minor, veinte criteriosA yseisB conservados; A01/B01/B02 corregidos, sin deuda ni rebates. QA independiente208Windows+208Linux yreceipt3+3, whole551/58095%0excl/omit, Ruff0, gate técnico0. ROOT74artefactos/13fuentes/14tarregulares/rawSQLite/imports ycleanupPid0/rm0 comprobados. El actor escribió reporte/sello antes de fallar su chat final por uso; entrega física completa verificada, sin fingir final del actor. Preimágenes/frozenoriginal171+80 intactas; no repetir suites después de CAS byteidéntico. [Informe](testing/t05/storage-journal-codec-current-qa-2026-10-11.md).

G0 freezeU1 ratificado por reciboROOT; NTU2 aún sin código. G2permissions preparaciónname-only detecta2SIDsnorresueltosMODIFY; sin acreditartrust ni cambiarACL, diseño acotado privado pendiente. T05/M1 siguen abiertos, Verificaciónglobal worker/manifest/E2E/persistencia/manuales/Git no cerrada. Medidor lote-custody-review-qa-codec cerrado oficialmente2026-10-11T06:58:41Z:fuenteestimado,tokens/eur/horasIAnull; ventana8h2m incluyeinactividad/interrupción, no es tiempo de trabajo medido.


## T-05 — preparación NT experimental y decisión G2 de ROOT

ROOT verifica el inventario sellado de 14 archivos del probe G1/G3, sus 15 entradas de custodia y fuentes U1 intactas. Control02 nativo exit0: aperturas relativas, creación exclusiva y sharing bilateral; handles192→203→192, cierres únicos con revocación previa y procesos propios restantes0. Intento01 exit1 y delta+1 se conservan: no se atribuye baseline limpio. Son instrumentos experimentales sin imports de producto ni crédito TDD. G3 permanece cerrado en esta entrega: Flags15 no completamente documentados por FileStorageInfo, cero escritura/flush/relectura. No se acredita durabilidad ni aceptación de U2/T05/M1. Namespace congelado storage-nt-abi-preparation-20261011.

Diseño G2 privado f85559c6 presenta S1/S2/S3 y contraejemplo de replay tras restart. ROOT elige S1 para producción, con excepción exacta TrustedInstaller sólo en el ancla de sistema por acreditar; S2 únicamente evidencia limitada de lease. S3 se aplaza hasta resolver bootstrap, asociación activa independiente y custodia de código. La política estricta rechaza grants peligrosos de outsiders sin cambiar ACL existentes ni adoptar SMOKE. Candidato documental privado en preparación, aún sin ratificación canónica ni liberación de implementación U2. Una lectura por nombre no acredita descriptor por handle. Se libera sólo un nuevo experimento G3 mediante NtQueryVolumeInformationFile, sin reinterpretar bits de FileStorageInfo; resultado pendiente.

Medidor ROOT m1/lote-nt-security-abi-preparation activo desde07:02:28Z; sin marcadores de actores ni cifras reales inventadas. T05 y M1 siguen abiertos; persistencia, lifecycle, Range/recovery/backup, E2E y manuales pendientes.


T-05 ROOT 20261011T071520Z: nuevo experimento G3 verificado8artefactos/14previosintactos; consulta NT independiente clase11/status0/info28, E/S sin caché alineada131072 bytes→Flush→relecturaexacta/samehandle/reopen, identidad intacta/handles192→203→192/PID0. No reinterpretar FileStorageInfo ni afirmar durabilidad/64slots/crash. [Informe](testing/t05/storage-nt-preparation-2026-10-11.md). Archivos declara política S1 y ADR0076 por decisión de ROOT, candidatos aún sin aceptar. U2/T05/M1 abiertos; no modificaciones ACL existentes.


## T-05 ROOT: política NT S1 incorporada y preparación nativa verificada — 20261011T074038Z

**Revisión de dos lentes — intento 1** documental: A29/B6 criterios,0Critical/0Important/0Minor; C/D no seleccionadas para prosa. [Tablas completas](testing/t05/storage-nt-security-s1-review-2026-10-11.md). [QA fresca](testing/t05/storage-nt-security-s1-qa-2026-10-11.md):64/64exit0,91entradaspre/post,8artefactos sellados; ROOT verifica antes del CAS07:34:48UTC. Cuatro documentos adoptados; cinco reemplazos exclusivamente de metadatos acreditados, originales distintos de SHA finales. TDD n/a:prosa. No cambia wire/runtime/estados.

G2 experimental:27artefactos/6PIDs propios restantes0; descriptor por handle confirma dos outsiders MODIFY en padres, por lo que admisión completa S1 permanece cerrada. Fixture nuevo protegido al crear demuestra sólo leaf/lease. Cold GetSecurityInfo+8 y ConvertStringSD+7 handles, repeticiones0; controls tras calentamiento170→179→170, no se afirma identificación de handles OS. Symlink privado rechaza1314; negativo reparse real pendiente, sin privilegios/remediación ACL.

G4 experimental:25artefactos/5PIDs restantes0;73writes exactas contiguas sobre75563008B de ceros→Flush→73reads exactas completas, SHAa09d7ea396297c226ba6b6b3f9a6b81a450d91bb4c8265bf73e88f0b55dcdefe. EOF75563008/Allocation82837504 (no cuota exacta), un stream::$DATA, sin sparse/compression, ID/SD intactos. Tres fixtures conservadas. Diagnósticos de streaming hash preservados; liberar dos objetos hash propios devuelve baseline173→184→173, no cierre de handles opacos. ROOT verificó25artefactos y225MB de fixtures antes del CAS. [Informe nativo](testing/t05/storage-nt-preparation-2026-10-11.md).

Sin journal de producción, commit, crash, ACK, durabilidad eléctrica, ext4/WSL/admin ni aceptación T05/M1. Próxima unidad U2a: lector/parser/política local readonly con TDD, sin store completo; release explícita posterior de ROOT, no derivada de estos experimentos. G1reparse/G2cadena/lifecycle/controller/E2E siguen pendientes.


T-05/U2a ROOT release2026-10-11: implementación fresca privada de lector de SD por handle, principal independiente, parser y política S1 local readonly liberada en storage-nt-security-u2a-20261011. Ownership dos nuevos scripts/storage_journal_windows.py y tests/test_storage_journal_windows.py ya declarados en Archivos;18entradas readonly y Gitbase privada27c201e2…; brief oficial intacto21392caracteres con aviso límite10000preexistente (no truncado). Actor fresco implement_nt_security_u2a, TDD causal obligatorio, nativefixtures propios protegidos de entrada/hostnegativo readonly/cobertura whole>=80%0exclusiones; sin writer/commit/crear journal ni cadena productiva. TrustedInstallerroot excepción pendiente bootstrap: U2a nunca la autoacredita desde boolean/path. No cambiar ACL existentes ni tocar datos/admin/WSL/GPU/servicios.

UsageROOT: lote-nt-security-abi-preparation cerrado07:42:21Z, ventana40m de reloj, fuenteestimado/sin transcripts/tokensreales/eur/horasIAnull; no trabajo/coste medido. Marker secuencial T05-U2a-security-readonly abierto después, sóloROOT. Producto U2a aún no aceptado: pendientes TDD/verificación/review A/B/C(+Dsegúnselector)/QA fresca/CAS. T05/M1 abiertos, ninguna checkbox cambiada. El release-root.receipt.json conserva hashes previos; esta actualización sólo ledger/CONTINUE es autorizada por ROOT.


## T-05 ROOT: U2a en revisión y nueva validación backend — 20261011T081114Z

Candidato U2a congelado, aún ausente canónicamente: sólo `scripts/storage_journal_windows.py` y `tests/test_storage_journal_windows.py`. ROOT verifica368 artefactos,48 registros de etapas RED/GREEN (no48 rojos válidos),18 inputs de revisión, scope2/0fuera/0warnings. Actor Windows66PASS y whole97,0027% (247/253 statements,109/114 branches,excluded0); Linux manual real UID10001/rednone/readonly/NNP con dos PLATFORM_UNSUPPORTED y cero DLL, sin pytest/JUnit inventados. **Evidencia de actor; QA fresca y aceptación pendientes.** SHA candidato805b4abfee03d20da2afa8422f4c425f542998f356eb9894fd49c1355fb6f8dd / test6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5.

Revisión A/B fresca en curso; C de seguridad exigida explícitamente por release, aunque selector automático no detecta este módulo WinACL. Overlay privado de revisión selecciona C=true y D=false; no cambia dev.json canónico. TDD original preservado: máscara unknown-standard mal elegida no cuenta RED; etapa12 coverage existente sin RED nuevo. Revisión verifica ley TDD sobre implementación/errorpaths, sin otorgar conformidad adelantada. ROOT restauró un helper propio de inspección al SHA exacto congelado; preimagen posterior y recibo repair se conservan, sin alterar los dos archivos de producto/test.

G1 experimental con junction real: ROOT16artefactos/74previos/8sources/PIDs0 verificados. NtCreateFile abre alias mismo; tagreparse/ID distinto exige rechazo por metadata. Sin traversal, sentinel60B intacto. Exit1 original contador170→171 conservado; mínimo independiente UUID145→146 y control separado146→146. No corrección retrospectiva/handleopaco/repetición artificial. [Informe](testing/t05/storage-nt-reparse-experiment-2026-10-11.md). NoG1full/G2/producción.

Backend fresco en curso en imagen CPU existente pinned. Native52/52,IPC90/90,custody21/21 tienen ejecuciones reales exit0 y exportaciones verificadas por el actor; aceptación ROOT pendiente del sello/selección/imports/coverage/cleanup. Principal2153nodos sigue ejecutándose tras readiness real de tres raíces temporales, tmp_path_factory, FFmpeg y credenciales. Diagnósticos previos de arnés conservados: rutas fuera de .cache y fuentes audio omitidas impiden atribuir esas ejecuciones a QA completa. Corrección exclusivamente de preparación, no relaxmarks ni tests producto. Cruce offline de81fallos históricos con testigos focales sólo es índice candidato, no verde global actual ni81bugs resueltos.

Marker ROOT activo `m1/lote-u2a-review-backend-qa`; anteriores cerrados sin solapamiento. Tokens/eur/horasIA realesnull; no asignaciones inventadas. T05/M1/estados sin cambios; contrato S1 mantiene admisión completa cerrada ante MODIFY outsiders, U2a sólo diagnóstico readonly. Ext4 persistente/lifecycle/recovery/backup/Range/E2E/escucha/Git siguen pendientes.


## Revisión de dos lentes — intento 1: T-05/U2a — 20261011T081819Z

**A/B/C frescas:0Critical/1Important/0Minor. A01 confirmado y abierto; no adopción.** [Tabla completa y evidencia](testing/t05/storage-nt-security-u2a-review1-2026-10-11.md). A61PASS/5deselected; B62PASS/4deselected; C61PASS/5deselected+5controlesnative readonly; se solapan y no se agregan como suite. Native/rawSD/hash368/48registros preservados, dos targets exactos. Scope2/0/0. Selector auto Cfalse/Dfalse; C mandatoria por release. Entrada suplementaria absoluta produjo D por .cache de evidencia; raw conservado, corregido a paths relativos y fuentesexactas: Ctrue/Dfalse/0warnings, sin config canónica editada.

| ID | Grado | Tarea | fichero:línea | Escenario | Veredicto |
|---|---|---|---|---|---|
|A01|Important|T-05/U2a CA3|scripts/storage_journal_windows.py:305;tests/test_storage_journal_windows.py:473,598,616|09green contiene errores/cleanup ya implementados;25tests de12-existing-behavior posteriores pasan contra esa preimagen|Confirmado,pendingFIX1|

ROOTrelease FIX1 sólo dos archivos en snapshot nuevo, actor fresco implement_u2a_fix1. Ley tdd: borrar código anterior altest y reescribir después de RED auténtico, no cobertura retrospectiva. Implementer comunica42nodes aislados causalesrojos después de borrar segmento y antes de reescritura; primerharness42exit4porargv inválido conservado sin créditoTDD. Esto aún es evidencia de actor, recibos/rootverificación/handoff/review2 y QA independiente pendientes. Originalfreeze805b4a/6671db intacto; no transferir su Linuxmanual al SHA nuevo. T05/M1/checkboxes sin cambios.

UsageROOTreviewbatch cerrado08:15:27Z/reloj12m/estimado, realesnull; markeractivo m1/lote-u2a-fix1-backend, sin solapamiento ni costes individuales inventados. Backendprincipal continúa tras readiness válida; grupos52/90/21 no se repiten. Provenance main/native sys.modules exactos; credential90/21 sólo guard-before-import seals+coveragefilenames, no sys.modules retrospectivo. No declarar verdeglobal antes de rawfinal/seal/cobertura/partición/cleanup.


## Revisión de dos lentes — intento 2: T-05/U2a FIX1 — 20261011T082913Z

**A01 corregido; A/B/Cfresh0Critical/0Important/0Minor.** [Tablas completas](testing/t05/storage-nt-security-u2a-review2-2026-10-11.md). ROOT1419artefactos+142inputs+42pairs/84JUnitindividuales/actor66PASS/whole97,1279370excluded/scope2/0/0verificados. Prefix/parser/policy/ABI/tests byteexactos; runtime91e279nuevo, original805b4a intacto. Los25tests posteriores ahora preceden reescrituraauténtica después deRED. Los42exit4previos no cuentan. Originalfreeze368 sigueexacto. Ctrue/Dfalse conoverlayonlyreviewconfig y pathsrelativos; dev.jsoncanónico intacto. ReviewerA/B62PASS4deselected yC61PASS5deselected+nativecontrolsreadonly, conjuntos solapados/no sumar.

| ID | Grado original | Veredicto | Evidencia |
|---|---|---|---|
|A01|Important|Corregido|delete/stubs42RED→reescritura08:16:43→42GREEN;84JUnit/pinsraw verificados|

Evidencia TDD actual por criterio, copiada por ROOT tras verificación del handoff (fase local, no cierreT05):

RED: tests/test_storage_journal_windows.py::test_portable_platform_rejects_without_loading_dll falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_principal_matches_independent_token_user falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_closed_descriptor_read_borrowed_handle falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_outsider_effective_grant_rejected[write-data] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_outsider_effective_grant_rejected[write-dac] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_existing_host_parent_rejects_without_mutation falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[status] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[missing] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[invalid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[oversize] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[control] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[inconsistent] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[cleanup] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_baseexception_and_cleanup_primary_preserved falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[impersonation] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[thread-denied] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[process-missing] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[process-failed] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-large] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-error] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-success] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[query-failed] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[query-size] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[pointer-outside] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[pointer-prefix] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[truncated] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[invalid-sid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[native-invalid-sid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[native-length] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[cleanup] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_cleanup_invalidates_owned_pointer_before_callback falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_principal_rejects_pseudo_handle_without_closing_it falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[None] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[True] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[0] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[-1] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[18446744073709551615] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[18446744073709551616] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[handle6] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_principal_baseexception_primary_and_cleanup_separated falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_load_error_is_typed falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_cleanup_without_primary_exception_is_typed falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.

QA independiente preparada conrelease privada storage-nt-security-u2a-qa-20261011, sólo lector/políticafreshWindows y LinuxrealnuevoSHA; noadopciónantesQA. Backendfuncionalactual actor2298PASS18SKIP/0FAIL/0ERROR en4gruposdisjuntos, selloROOTacceptancependiente. No80cadaarchivoglobal niM1green. MarkerROOT m1/lote-u2a-review2-backend; métricas realesnull. No checkbox/estado modificado.


## Validación actual CPU y adopción T-05/U2a — 2026-10-11T08:42:29.270073+00:00

ROOT acepta el backend CPU actual en cuatro grupos disjuntos:2298PASS18SKIP0FAIL0ERROR/2316JUnit/0duplicados. Verificación independiente53132archivos/3332196132bytes/1770fuentesactuales/4TARcausales; propiosPID0. [Informe backend](testing/current-backend-post-components-qa-2026-10-11.md). Los81nodos históricos exactos se cotejan:77PASS4SKIP0ausentes; originales rojos intactos. Whole80archivos/8por debajo80; afectadosmedidos>=80conIPCbranch separado, no verdeglobal de cobertura. ImagenCPU/persistenciatmpfs no acreditaext4producto. Procedenciagruposcredencialeslimitada explícita.

U2aFIX1 aceptada en alcance lector/política tras review2A/B/C0gaps y QA fresca66PASSWindows/43PASS23SKIPLinux, exit0ambos. Wholeoficialcombinada259/265lines+113/118branches=97,127937%,0exclusiones/gate0; Linuxindividual76,501305%honesto. ROOT173payload+78snapshot(20fuentes/58Gitprivado)+9suplementobufferingverificados; JUnit/coverage/imports/TARexactos y recursospropiosreaped. Windowsstdoutfinal1574B autenticadofreeze,noPOSTprevio; sueltabúfer posterior, norepetirtests. Contadorinitialfixture+8conservado,100consultasplateau/cierrepropio−1; noocultarbaselinefailed.

ROOTCAS dosfiles nuevos ausentes 2026-10-11T08:42:29.270073+00:00: scripts/storage_journal_windows.pySHA91e279775c20561b14679845066f334f3af6d30fdc0a41a92ce5d0ee24af4b70 y tests/test_storage_journal_windows.pySHA6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5, bytesQAexactos. [QA actual](testing/t05/storage-nt-security-u2a-current-qa-2026-10-11.md). Freezeacceptedprivado en storage-nt-security-u2a-root-20261011/adoption-root.receipt.json.

Diagnóstico local no capacidad; G2cadena sigue rechazado, bootstrapTI/store/writer/ACK/ext4/lifecycle/E2E/manuales pendientes. T05/T15/M1 siguen abiertos, sin checkbox/estado/Git/ACL/datos alterados. Próximaunidad U2baperturarelativaexistentes/metadata/geometríareadonly aún sinrelease; no creanobjetos ni autoridad. MarkerROOT m1/lote-u2a-qa-backend-accept, tokens/eur/horasIA realesnull.


## T-05: release de apertura relativa y metadata — 2026-10-11T08:48:25.614820+00:00

U2a aceptada y congelada por ROOT tras revisión2 A/B/C y QA independiente. Se libera U2b1 al actor fresco implement_nt_observation_u2b1 en snapshot privado storage-nt-observation-u2b1-20261011: sólo FILE_OPEN de hijos existentes, metadata por el mismo handle y cierre local. Geometría se reserva para U2b2. Es división de la implementación O2/S1 ya aprobada, no un nuevo plan ni una ampliación de autoridad.

Base privada612dbb9388c86cdcca4e99e4bb70a2695bff2f2d;22fuentes/inventario actual, runtimebase91e279/testbase6671db. Release y recibo privados conservan el brief del plugin íntegro; preimágenes aceptadas y cuerpos/tests U2a no se refactorizan. Política de sincronía ratificada: NTretorno distinto dePENDING gobierna; pending/entered sinretorno no concede salida ni close, arenas y owner vivos hasta reap, contexto revocado. Retener un scalar no acredita custodia del prestado. Caller confiable debe conservar adquisición; los tests de contingencia se ejecutan en hijo propio y no prueban pendingnativo.

TDD causal obligatorio antes de cada cuerpo inclerrores/cleanup; revisión fresca A/B/C y QA independiente antes de CAS. Sin geometry/create/store/writer/ACK/bootstrapTI/fullchain/CLI/admin/WSL/ACL existentes/datos. TDD n/a del release documental. No estados/checks alterados. Marker anterior m1/lote-u2a-qa-backend-accept cerrado08:42:57Z (13m reloj, no horasIA); activo m1/T05-U2b-observacion-NT. Tokens/eur/horasIA realesnull.


## T-05/U2b1 candidato y revisión en curso — 2026-10-11T09:14:54.896636+00:00

Candidato privado congelado, no adoptado: apertura relativa FILE_OPEN existente, metadata Win32 y close/context. Runtime1556847e29c4e5ba08486765ededaf80110b7851a715ad83bfd415dd76dc5c29; tests11e598146a73ded9bb144c113baa0e75a379379c8473b2d408204c390e662093. ROOT verifica1242payload/5reparse stat-only sin traversal,22inputs,18defsU2a/31defs-tests exactas,100runs individuales54RED46GREEN y112PASS (66U2a+46nuevos). Ocho REDcleanup con adquisición válida superseden bootstrap sin adquisición; originales inválidos conservados y no acreditados como causal. Whole485/520líneas93,2692%,159/178ramas89,3258%,combinado92,2636%,exclusiones0/omitvacío/pragmas0; Ruff0. Nativecold151/importwarm170/fixturewarm171/open172/close171 (12iteraciones)/ownerclose170: +19inicialhonesto,sin allocatorreuse. PENDING/unknown son dobles propios con8childreaps, no pendingnativo ni durabilidad.

Revisión fresca intento1A/B/C activa en storage-nt-observation-u2b1-review1-20261011, baseprivada901701760860b52488cd166556652c6f3cd6a518. Scope2filesexit0,0avisos/0exclusuario. AutoCfalseDfalse; overlay sólo revisión Csiempre produceCtrueDfalse sin alterar dev.json. B informaB01Important pendiente: interrupción tras retornoSTATUS_PENDING/pre reconocimiento puede liberararena y permitir siguienteoperación; reproducción/fullfusion pendientes. No se acepta candidato con gap abierto. QA independiente preparada, aún no ejecutada ni autorizada antes reviewlimpia; CASposterior. Fuente U2a canónica91e279/6671db intacta. GeometríaU2b2/bootstrap/store/writer/ACK/fullchain/ext4/lifecycle/E2E/manuales/Git pendientes; T05/M1abiertos y cero checkbox/estado modificado. Meterimplementación cerrado,revisión m1/T05-U2b1-review1 activo; tokens/eur/horasIA realesnull.


### RED originales U2b1 (bootstrap cleanup supersedido, no contar como causal)

RED: tests/test_storage_journal_windows.py::test_observation_component_closed_validation falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:48:42.861961+00:00
RED: tests/test_storage_journal_windows.py::test_observation_abi_and_profiles falló con AssertionError: ABI aún no implementada · 2026-10-11T08:51:53.912970+00:00
RED: tests/test_storage_journal_windows.py::test_observation_rejects_inputs_before_open[scalar] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:54.523553+00:00
RED: tests/test_storage_journal_windows.py::test_observation_rejects_inputs_before_open[closed] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:55.141881+00:00
RED: tests/test_storage_journal_windows.py::test_observation_rejects_inputs_before_open[kind] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:55.791635+00:00
RED: tests/test_storage_journal_windows.py::test_observation_rejects_inputs_before_open[name] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:56.430194+00:00
RED: tests/test_storage_journal_windows.py::test_observation_rejects_inputs_before_open[parent-type] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:57.046326+00:00
RED: tests/test_storage_journal_windows.py::test_observation_status_error_never_closes_outslot falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:57.668152+00:00
RED: tests/test_storage_journal_windows.py::test_observation_return_governs_not_iosb falló con AssertionError: assert False · 2026-10-11T08:51:58.272044+00:00
RED: tests/test_storage_journal_windows.py::test_observation_wrong_information_closes_acquisition_once falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:51:58.879164+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_frozen_copy falló con AssertionError: Falta apertura propia · 2026-10-11T08:51:59.499177+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[attributes-1056] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:00.099183+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[tag-2684354563] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:00.738345+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[links-0] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:01.420257+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[links-2] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:02.074244+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[delete_pending-1] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:02.777931+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[directory-1] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:03.454588+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[file_type-3] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:04.071392+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[eof--1] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:04.694207+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[allocation--1] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:05.311749+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[allocation-1] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:05.955741+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[path-\\\\?\\UNC\\host\\share\\f] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:06.567953+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[path-C:\\x] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:07.187109+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[path-\\\\?\\C:\\a\\..\\b] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:07.811804+00:00
RED: tests/test_storage_journal_windows.py::test_observation_metadata_fail_closed[path-\\\\?\\C:\\a:stream] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:08.426516+00:00
RED: tests/test_storage_journal_windows.py::test_observation_false_query_never_parses_plausible_buffer falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:09.043932+00:00
RED: tests/test_storage_journal_windows.py::test_observation_close_revokes_once falló con AssertionError: Falta adquisición propia · 2026-10-11T08:52:09.675684+00:00
RED: tests/test_storage_journal_windows.py::test_observation_context_preserves_baseexception_and_cleanup falló con AssertionError: Falta adquisición propia · 2026-10-11T08:52:10.280077+00:00
RED: tests/test_storage_journal_windows.py::test_observation_nonwindows_without_dll falló con Failed: DID NOT RAISE PlatformUnsupportedError · 2026-10-11T08:52:11.010647+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unresolved_retains_and_poison_child[pending-open] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:11.642349+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unresolved_retains_and_poison_child[entered-exception] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:12.486303+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unresolved_retains_and_poison_child[pending-query] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:13.370268+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[false] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:14.200955+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[exception] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:15.004690+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[cleanup-primary] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:52:15.817214+00:00
RED: tests/test_storage_journal_windows.py::test_observation_concurrent_query_close_serialized falló con AssertionError: Falta adquisición propia · 2026-10-11T08:52:16.612395+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_ordinary_missing_and_borrow falló con AssertionError: FILE_OPEN aún no implementado · 2026-10-11T08:52:17.230734+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_sharing_bilateral[2] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:17.858679+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_sharing_bilateral[65536] falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:18.484570+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_directory_denies_delete falló con AssertionError: FILE_OPEN directorio aún no implementado · 2026-10-11T08:52:19.109631+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_hardlink_and_wrong_kind falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:19.724612+00:00
RED: tests/test_storage_journal_windows.py::test_observation_native_new_junction_no_traversal falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:52:20.334412+00:00
RED: tests/test_storage_journal_windows.py::test_observation_poison_retains_other_live_acquisitions_child falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:55:47.315905+00:00
RED: tests/test_storage_journal_windows.py::test_observation_independent_contexts_serialize_native_calls falló con AssertionError: Segundo contexto no debe entrar en vuelo simultáneo · 2026-10-11T08:55:48.171862+00:00
RED: tests/test_storage_journal_windows.py::test_observation_kind_requires_exact_closed_string falló con Failed: DID NOT RAISE NativeObservationError · 2026-10-11T08:58:48.283413+00:00
RED: tests/test_storage_journal_windows.py::test_observation_close_beforecall_fault_is_unknown_child falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:59:32.001414+00:00
RED: tests/test_storage_journal_windows.py::test_observation_wrong_information_closes_acquisition_once falló con assert [] == [202] · 2026-10-11T08:54:03.515689+00:00
RED: tests/test_storage_journal_windows.py::test_observation_false_query_never_parses_plausible_buffer falló con assert [] == [202] · 2026-10-11T08:54:04.164319+00:00
RED: tests/test_storage_journal_windows.py::test_observation_close_revokes_once falló con AttributeError: 'NoneType' object has no attribute 'state' · 2026-10-11T08:54:04.799868+00:00
RED: tests/test_storage_journal_windows.py::test_observation_context_preserves_baseexception_and_cleanup falló con AssertionError: assert ('primary' == 'primary' · 2026-10-11T08:54:05.468117+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[false] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:54:06.120590+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[exception] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:54:06.961695+00:00
RED: tests/test_storage_journal_windows.py::test_observation_unknown_close_retains_without_retry_child[cleanup-primary] falló con AssertionError: Traceback (most recent call last): · 2026-10-11T08:54:07.825633+00:00
RED: tests/test_storage_journal_windows.py::test_observation_concurrent_query_close_serialized falló con assert not True · 2026-10-11T08:54:08.663786+00:00


## Revisión de dos lentes — intento 1: T-05/U2b1 — cuatro Important pendientes

A+B+C frescos, Dfalseporselector. ROOT2026-10-11T09:20:39.783534+00:00fusiona0Critical4Important0Minor,sinrebates. Csinseguridadnueva; A01TDDyB01-B03corrección bloqueanCAS/QA. [Informe completo](testing/t05/storage-nt-observation-u2b1-review1-2026-10-11.md).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria implementado sin RED/test; runtime:558 | T05/U2b1 | pendiente FIX1: borrar sólo __exit__nuevo a stub→RED válido→reescribir; no restaurar cuerpo anterior | LenteA100runs/coverage558missing/probepropioexit0; defecto disciplina,no bug funcional |
| B01 | Important | KeyboardInterrupt posPENDING/pre reconocer libera arena, no poison; runtime:486 | T05/U2b1 | pendiente FIX1: ampliar custodia/cobertura transición, REDregresión previo | Bdouble5hijos;ROOTsinglefault/control6hijosreaped:arenadead/nextoptrue vscontrolalive/false |
| B02 | Important | KeyboardInterrupt posCloseHandle/pre publish permite retry con None; runtime:534 | T05/U2b1 | pendiente FIX1: estado idempotente reservado antes, REDregresión previo | ROOT[202,None] vscontrol[202],actualfakeNonefalse/retention |
| B03 | Important | KeyboardInterrupt posSUCCESS/pre registrar pierde adquisición; runtime:621 | T05/U2b1 | pendiente FIX1: arena/owner durante transfer, REDregresión previo | ROOTopen1/closed[]/owner0/retainedfalse vscontrolclose202 |

T05/M1abiertos. FIX1fresco requiereREDcausalantesdecódigo;A01borrar/rewrite__exit__sintest,UAaceptadaintacta.Geometría/bootstrap/store/ACK/ext4pendientes. LedgerúnicoROOT,sincheckbox/estadosalterados.


## T-05/U2b1 FIX1 autorizado — 2026-10-11T09:24:56.242765+00:00

ROOT delega cuatro Important a actor fresco implement_u2b1_fix1 en storage-nt-observation-u2b1-fix1-20261011/snapshot. Release dbc9799b2f70d54ea86b1095cf16cdf61a81821074b63aafbeb466cc206943f2,23 fuentes/base privada431ae3357a35177b59081364d93434fe77abfb42. Ownership sólo dosfuentes/evidencia; preservación U2a/112nodosprevios; A01stub→RED→reescritura y B01-B03regresionesREDprevio. Revisión1completa y ROOT6hijosdobles corroboran bloqueo. ReviewerB yCJUnit47cadauno son exactamente47nodos iguales tras normalizar sólo prefijo cápsula; no94. ROOTverifica28payload por cápsula/8reapreceipts cada una sintraversal; importpathactualnoinstrumentado,noatribuirsys.modulescaptura. Jiraenabledfalse,nooperacionesexternas. Meterreview1cerrado09:22:58Z/ventana12mrelojnoIAmedida; activo m1/T05-U2b1-fix1. QA preparada bloqueada hasta review2limpia; cero adopción/checkbox/estado. T05/M1abiertos; geometryU2b2 y ext4/integración amplio pendientes. Tokens/eur/horasIA realesnull.


## Revisión de dos lentes — intento 2: T-05/U2b1 — A/B/C sin gaps pendientes

ROOT 2026-10-11T09:46:46.890459+00:00:0Critical/Important/Minor; cuatro Important intento1 corregidos,sinrebates,deudanula. Dfalse selectorauto/overlay,canondevauto intacto. [Tablas e informe](testing/t05/storage-nt-observation-u2b1-review2-2026-10-11.md).

| # | Grado inicial | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito sin RED | T05/U2b1 | corregido: __exit__ borrado a pass, RED causal válido, reescritura distinta anterior | A2 verifica source-before/UTC/hash/JUnit; escenario propio PASS |
| B01 | Important | PosPENDING liberaba arena y dejaba operar | T05/U2b1 | corregido: custodia y poison cubren transición posretorno | B2/C2/A2 fault/control, arena/owner vivos, cero close/segunda operación |
| B02 | Important | Posclose permitía retry CloseHandle(None) | T05/U2b1 | corregido: reserva idempotencia/revocación/retención de unknown | Fault/control [202] una vez, sin None; 8close transiciones adicionales |
| B03 | Important | SUCCESS antes de registro perdía adquisición | T05/U2b1 | corregido: arena/owner durante transferencia y constructor | Fault/control custodia/no nueva operación;11open transiciones adicionales |

ROOT588payload/23snapshot/6pares/139actorPASS/74reviewernodosúnicos verificados; wholelíneas95,514%/ramas91,758%0excl. QAactualWin/Linux y CAS posteriores; nadaadoptado, T05/M1abiertos. No pendingnativo/nofugasglobal/cadena/store/ACK. Marker m1/T05-U2b1-review2 activo hasta releaseQA; tokens/eur/horasIA null.


### RED causales U2b1 FIX1

RED: test_fix1_context_without_primary_unknown_close_is_typed falló con Cleanup no acreditado sin primaria debe generar error tipado · 2026-10-11 · a01-red
RED: test_fix1_postpending_retains_arena_owner_global_poison[fault] falló con Arena nativa liberada sin completion acreditada · 2026-10-11 · b01-red
RED: test_fix1_postclose_reserves_idempotence_without_none_retry[fault] falló con CloseHandle no puede repetirse con None · 2026-10-11 · b02-red-corrected
RED: test_fix1_postsuccess_open_keeps_acquisition_arena_owner[fault] falló con Arena nativa liberada sin completion acreditada · 2026-10-11 · b03-red
RED: test_fix1_entered_typed_exception_still_retains falló con Tipo del error no acredita completion · 2026-10-11 · typed-entered-red
RED: test_observation_close_beforecall_fault_is_unknown_child falló con causas distintas de KeyboardInterrupt · 2026-10-11 · close-beforecall-regression


## QA independiente U2b1 en ejecución — 2026-10-11T09:54:02.676802+00:00

ROOT autoriza y delega a qa_u2b1_current tras revisión2 A/B/C sin gaps. Release450e23fafb38f6d35c95fb3d2b6f07a88d00098c197085cf3cbbf5b3166bf305,24fuentes readonly; candidatoaf192/f36ada. QA actual Windows/Linux unidadCPU, cobertura whole e imports/procesos/artefactos auténticos pendientes; no adelantar resultados. Canon91e279/6671db permanece intacto. Marker m1/T05-U2b1-QA activo, review2 cerrado09:48:33Z/reloj11m noIAmedida. Sólo ROOT ledger; tokens/eur/horas reales null. T05/M1 abiertos.

Contenedores QA próximos: exportar/verificar evidencia y PID0 antes de retirar únicamente el contenedor propio. Los históricos se retiran cuando su archivo está verificado; ACE y otros stacks intactos. No prune global.


## QA U2b1 intento1 rojoLinux y release FIX2 — 2026-10-11T10:04:46.269785+00:00

Windows139PASS; Linux105PASS29SKIP5FAIL. Whole90,6555/78,1032/combinada92,3291%0exclusiones: gatecobertura0, funcional1. ROOT392payload/1reparse/24fuentes/54hijos/TAR134/imports/streams/PID0rm verifica. Causa fixture ctypes.set_last_error ausenteLinux, closed[],retained; cuatrocascadas. No bugkernelWindows demostrado ni aceptaciónconjunta. [Informe](testing/t05/storage-nt-observation-u2b1-current-qa-2026-10-11.md).

ROOT autoriza FIX2fresco sólo test false_query/canal last_error scoped Linux; runtimeaf192 fijo, canon91e279/6671db intacto. debug-root-cause F1–F3/controlanteseditar y regresión real; nofalseTDD nuevo runtime. Revisión y QA intento2 pendientes. Marker m1/T05-U2b1-fix2; T05/M1 abiertos, tokens/eur/horas reales null. Cuatrocontenedoresbackenddetenidos conTARverificadosretirados; ACE intacto. Git integración pendiente: HEAD8663287 desde6octubre, rama compartidam1/t-02-esquema dirty; no mezclar archivos pendientes ni hacer stageglobal/pushciego.


## Git: primer lote aceptado commiteado y subido — 2026-10-11T10:09:35.132654+00:00

ROOTcommit7822b4d88519fa852d3987795fc3d32a3520dcb5 en m1/t-02-esquema, push a origin y ls-remote exacto. Cincoarchivos: runtime/test U2a91e279/6671db y tres informes revisión1/revisión2/QA. Sólo componente seguridad yaROOTaceptado; no declaraT05/M1cerrados ni publicaU2b1privado. Índicevacío antes/después; stage explícito cincoarchivos, sin stageglobal/reset/checkout/merge/forcepush. Worktreefuentes byteexactas despuéscommit. Esto es excepción ROOT acotada al guard de integración de checkout compartido: todoslos demás cambios pendientes permanecen fuera delcommit; actores trabajan sólo snapshotspropios sinGit. Contenedores4backendretirados trasTARverificados, informesintactos/ACEUp.

FIX2test-only actor informaWin139PASS/Linux110PASS29SKIP, candidato020aeffe612e1c43aa1c420c4f969babfabf277f269ca96050d6d6c7d9c5adfe/runtimeaf192 sin cambio; informe/freeze, ROOTverificación, revisión nueva y QAintento2 aún pendientes. No adoptar ni cerrar por el resumen. MarkerFIX2activo.


## T-05/U2b1 FIX2 verificado; revisión 3 en curso — 2026-10-11T10:21:08.615505+00:00

ROOT verificó 470 payloads regulares y 1 reparse por stat, 25 fuentes privadas y cambio exclusivo a false_query. Runtime af192 byte exacto; tests020aeffe. QA1 frozen392 permanece íntegro. F1 reproduce fallo de fixture Linux sobre f36ada, F3 control mismo SHA pasa; F2 propio posterior F3 (diagnóstico QA1 ya leído). Harness inicial reconstruido posterior declarado, sin atribuir sello contemporáneo. TAR/streams/reaps verificados; 27 hijos nuevos Windows y 27 Linux reaped exit0. Actor final139PASSWindows/110PASS29SKIPLinux, mismos139nodos y29skips; resultados actor no sustituyen QA.

Scope-check revisión3:1 fichero,0 fuera de alcance/avisos; C/D auto false. Base privada9e27683. Lentes frescas A/B despachadas. Código canónico U2a91e279/6671db intacto, sin CAS. Revisiones anteriores conservadas; sólo se reevalúa FIX2 con evidencia nueva. T-05/M1 abiertos, ext4/store/ACK/lifecycle/E2E/manuales pendientes. Marker ROOT activo m1/T05-U2b1-review3; FIX2 cerrado. Tokens/eur/horas IA reales null.

Evidencia: `.cache/dev-cycle/m1/storage-nt-observation-u2b1-review3-20261011/verification-root.receipt.json`, `prepare-root.receipt.json` y `record-root.receipt.json`.


## Revisión de dos lentes — intento 3: T-05/U2b1 FIX2 — A/B sin gaps

ROOT 2026-10-11T10:26:29.465093+00:00:0Critical/Important/Minor; C/Dauto false, un test modificado, runtimeaf192 intacto. Cuatro gaps intento1 conservados como corregidos en2; regresión de fixture Linux corregida. [Informe y tablas completas](testing/t05/storage-nt-observation-u2b1-review3-2026-10-11.md).

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito antes RED | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact; FIX1 seis pares y revisión2 A/B/C |
| B01 | Important | Custodia posPENDING perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B02 | Important | Retry cierre con None | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B03 | Important | Adquisición SUCCESS antes registro perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| QA1-FIX2 | Fallo de fixture | FALSE Linux no alcanza retorno por ctypes ausente | T05/U2b1 | corregido por emulación scoped del nodo | F1fallo/F3controlpreimageexacta; A/Bpropios comprueban FALSE5/cierre202/restauración |

QA2Windows/Linux autorizada y pendiente; noCAS ni cierreT05/M1. A auditoresrealWindows/Linuxsimulado; B18PASS+probe simulado, no Linux nativo propio. Un auditorAlecturaUTF8exit1 conservado yrelecturabyte-safe0. ROOT payloads/AST/JUnit/recibos verificados. Meterreview3 sigue activo hastareleaseQA2.


## T-05/U2b1: QA2 aceptada y componente incorporado — 2026-10-11T10:35:13.197152+00:00

ROOT verifica361payload/1reparsestat-only/26sources/JUnit/imports/27childreaps porplataforma/TAR134/PID0rm. Windows139PASS0SKIP, Linux110PASS29SKIP0FAIL/ERROR; mismo139nodes y29skiprazones QA1. WholeWindows/combinada90,655509%;Linux77,684798%separado,0excl/omit; unión oficial946Win/780Linux/946combined autenticada. Gate funcional0 yWindows/combinada>=80gate0.

CAS2fuentesaf192/020aeffe ejecutado después revisión3A/Blimpia+QA2; Ruffposterior sólo formato(test3de1e82,ASTidéntico, runtimeexacto). Check0/format--check0 finales, falloformato1inicial preservado; sin repetir suite verde porformato. [Informe vigente de componente](testing/t05/storage-nt-observation-u2b1-current-qa2-2026-10-11.md). QA1rojo íntegro, no resultado viejo atribuido a nuevoSHA.

M1NO-VERDE/T05en-progreso: geometry/store/writer/ACK/bootstrap/fullchain/ext4/lifecycle/E2E/manuales pendientes. QA2marker cerrado; no pausa del objetivoM0–M5. PróximaunidadT05U2b2 necesitaADRcontratoNTantesimplementación; M2T02briefCPUindependientegenerado pero no iniciado. Gitincremental del componente pendiente de este registro, restantes cambios sin integrar. Tokens/eur/horasIA realesnull.


## Git incremental U2b1 y avance CPU independiente ? 2026-10-11T10:38:20.945968+00:00

Commit/push 67e1f09fae4d2d2b1931dc66c0e349f3938fe270 verificado en origin/m1/t-02-esquema; siete ficheros aceptados(runtime/tests/reviews1?3/QA1?2), index vac?o. Sin stageglobal, checkout, mainmerge ni otros cambios pendientes incorporados. M1/T05 siguen abiertos.

M2/T02 pas? aen-progreso conforme dependenciaT01yADR0037; briefdeterminista f283d133 generadoexit0(warning tama?o conservado). Actor fresco implement_m2_t02_recipes posee s?lo cuatroficheros declarados+evidencia propia. MarkerROOT activo m2/T02-recetas-privadas; QA2U2b1cerrado. No aceptaci?nM2 ni30generaciones fingidas, ning?nmodeloGPUcargado. Geometr?aT05U2b2 a?npropuesta, constantesNT primarias verificadasen .cache/dev-cycle/m1/storage-u2b-contract-refinement-20261011/, noADRratificado/implementaci?n.


## T-02: contexto previo al RED en concreci?n ? 2026-10-11T10:40:29.472328+00:00

Implementerfresco devolvi? NEEDS_CONTEXT justificado, fuentesintactas/noRED/no c?digo: CPUdesign exige fijarDTO/envelope/readersantesRED. Actorarchitectfresco design_m2_t02_recipe_contract trabaja s?lo propuestaen .cache/dev-cycle/m2/creative-recipes-t02-contract-20261011/, opciones+contratocerrado. ROOT escoger? bajo delegaci?ndelpropietario y ratificar? antes?nicoredispatch. No solicitud alhumano ausente ni bloqueo delobjetivo, T02en-progreso/M2noaceptado. Marker?nicoROOTm2/T02-recetas-privadas incluyeconcreci?ncontractual; m?tricasrealesnull. U2b1aceptado/push67e1f09 siguevigente, M1noaceptado.


## T-05/U2b2: elección G2 de ROOT antes de revisión — 2026-10-11T11:41:07.427379+00:00

ROOT elige G2 bajo delegación vigente del propietario: dos consultas NT diferenciadas sobre la misma adquisición propia retenida y derivador puro de B candidato. Resuelve la dependencia geométrica del writer conservando respuestas raw, identidad y custodia; el writer posterior deberá acreditar su propia adquisición, modos, buffers y gates S1. No cambia O2/ADR-0075, S1/ADR-0076 ni el wire U1.

Se incorporan al campo Archivos el diseño específico de geometría y ADR-0078 por cambio de autoridad documentada. Candidatos privados en `.cache/dev-cycle/m1/storage-nt-geometry-design-20261011/`; primera entrega preservada, elección y enlaces corregidos pendientes de snapshot/revisión A+B y QA documental independientes antes de adopción/release TDD. La opción está elegida; el contrato aún no está ratificado ni implementado. TDD n/a: decisión/prosa. T-05/M1 permanecen en-progreso; geometría nativa, store/writer/ACK, ext4 persistente, recovery y E2E integral siguen pendientes.


## T-05/U2b2: revisión documental fresca G2 en curso — 2026-10-11T11:46:39.277081+00:00

ROOT verifica entrega seleccionada frozen19134995:18artefactos, primera entrega21exactos,20fuentes M1 protegidas. ElecciónG2 y enlaces contra destinos canónicos incorporados a candidatos; design aprobado privado/ADR0078propuesta, sin adopción ni runtime. Copia durable: sólo cuatro líneas154/376/390/415.

Snapshot aislado27ficheros/25guardas, base privada c529e57ae4ea8f841a3871767557a54a8e20a266. Scope-check oficial:4documentos,0fuera/0avisos/0exclusionesusuario; C/Dauto false. Lentes frescas A/B efectivamente despachadas a review_m1_geometry_a1 y review_m1_geometry_b1; resultados y QA pendientes. Tier reviewer frontmatter sin override. TDD n/a: prosa; no cobertura de producto ni queries nativas atribuidas a este contrato.

Evidencia `.cache/dev-cycle/m1/storage-nt-geometry-review1-20261011/prepare-root.receipt.json`, source.diff, scope/lenses/tier stdout/stderr/exit. Preparación y revisión paralelas a la implementación M2/T02; sin marker propio ni horas/tokens/coste reales inventados. Ledger conserva estados y criterios abiertos. M1 NO-VERDE: ext4 persistente/store/writer/ACK/fullchain/recovery/E2E siguen pendientes.


## Revisión de dos lentes — intento 1: T-05/U2b2 contrato G2 — A/B sin gaps técnicos

ROOT 2026-10-11T11:51:55.162094+00:00:0Critical/0Important/1Minor; C/Dauto false sobre cuatro documentos. ROOT27snapshot/25guardas/nueve primarias verificados. Tablas completas A31/B10 y evidencia declarada se conservan en [informe](testing/t05/storage-nt-geometry-contract-review1-2026-10-11.md).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Minor | Frase W1 larga, docs-style regla1 | T05/U2b2 documental | Anotado sin bloquear, no se afirma corregido | storage-durable-design.md:415; informe completo |

Propuesta técnicamente conforme; QA documental independiente pendiente antes de adopción/release. Estados/criterios del hito abiertos, sin implementar queries/writer/ACK ni acreditar ext4/M1. TDD n/a prosa. Preparación/revisión paralelas sin marker propio ni reales inventados. Evidencia `.cache/dev-cycle/m1/storage-nt-geometry-review1-20261011/fusion-root.receipt.json`.


**QA documental G2 despachada ROOT 2026-10-11T11:53:03.449161+00:00:** actor fresco qa_m1_geometry_contract_20261011, namespace exclusivo `.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/`. Snapshot y candidatos permanecen congelados, A01Minor anotado; no release ni adopción hasta verificar QA. Tier qa sonnet/medium frontmatter, ningún override. Paralela a implementación M2T02; sin marker propio ni métricas reales inventadas.


## T-05/U2b2: contrato G2 adoptado tras QA documental — 2026-10-11T12:16:41.617978+00:00

ROOT verifica QA documental33/33 gate0,53artefactos actuales,14+14preservados de intentos1/2,18selected/21originales,27snapshot/25guardas y nueve fuentes Microsoft. Únicamente DOC19 corrigió búsqueda falsa del arnés; no cambios del contrato. Revisión1A/B:0Critical/0Important/1Minor A01 anotado sin afirmar corregido. [QA y adopción](testing/t05/storage-nt-geometry-contract-qa-2026-10-11.md).

ADR0078 libre verificada y aceptada; storage-nt-geometry-design.md aprobado/adoptado, §4 normativo byte exacto a candidato revisado. Durable cambia sólo154/376/390/415; journal U1 y runtime/tests U2a/U2b1 intactos. Index actualizado mediante delta ROOT explícito. TDD n/a prosa. Implementación U2b2 pendiente de despacho fresco: queriesNT11/17+derivador puro; sin writer/ACK/store ni fullchain/ext4 acreditados. T05/M1 abiertos.

Recibos `.cache/dev-cycle/m1/storage-nt-geometry-adoption-root-20261011/qa-verification-root.receipt.json` y `adoption-root.receipt.json`. Preparación documental paralela a M2FIX1 sin marker propio, métricas reales null.


## T-05/U2b2: implementación G2 liberada a actor fresco — 2026-10-11T12:21:21.605647+00:00

Actor implement_m1_geometry_u2b2 efectivamente despachado tras contratoG2/ADR0078 adoptados. Brief determinista22046bytes conserva warning tamaño; tierimplementerfrontmatter. Snapshot27 fuentes y dos destinos editables privados, canonical runtimeaf192/tests3de1e82 intactos. Ownership exclusivamente snapshot/scripts/storage_journal_windows.py y snapshot/tests/test_storage_journal_windows.py; otras25 fuentes readonly. ROOT único ledger/CAS/marker/Git.

Entrega exigida: queriesNT11/17 reales sobre misma adquisición retenida, arenas/custodia/completion/metadata conforme§4.1–4.6 y derivador puro B sinwriter/admission. RED causal propio por criterio antes código, nativeWindowsreadonly+Linuxportable/regresión/whole>=80/Ruff con pins y receipts, reviewfresh/QAindependiente posteriores. PENDING únicamente doubles en hijos propios reaped; no promesa nativa. SinbootstrapTI/store/writer/ACK/adopciónproducción/admin/GPU/datos. M1/T05 abiertos.

Preparación `.cache/dev-cycle/m1/storage-nt-geometry-implementation-20261011/prepare-root.receipt.json`; despacho/release en `release-root.receipt.json`. Implementación paralela no solapa archivos con M2FIX1. Único markerROOT de lote m1-m2/lote-geometria-recetas-implementacion, sin horas/tokens/coste reales disponibles.


## T-05/U2b2: candidato verificado; revisión de producto 1 en curso — 2026-10-11T12:55:36.261177+00:00

ROOT verifica2369archivos regulares y5reparsestat-only,2374entradas totales;27fuentes snapshot/25readonly intactos. Canon af192/runtime y3de1e82/tests permanecen aceptados sin CAS. Candidato privado4f543c4f/de2e7283 tiene405PASSWindows/208PASScodec, Linux297PASS29SKIP79deselected; imports reales/pins/streams/JUnit verificados. Cobertura oficial módulo completo líneas90,410959%/ramas89,0625%/combinada90,0608519%,0excl. Ruff0/format0. ROOT verifica40recibos hijos terminated/wait/reaped,12testigos propios de ambasqueriesNT/raw/metadata/ABI; candidato65536 sólo numérico sinS1/admission/writer. TAR Linux comparado byteexacto con export, procesoUID10001 exit0/waited, propio contenedor removidoPid0; imagenCPU fijada, networknone/readonly/capdrop/no-new-privileges.

Scope2/0fuera/0avisos/0exclusionesusuario; C/DautoFALSE sobre diffcompleto. Lentes frescas efectivamente despachadas review_m1_geometry_product_a1/b1, revisión PRODUCTOintento1de3, distinta de revisión documentalG2 yaadoptada. Snapshotprivado base 18631c786d3e32f70d8abe40dae423306f0f0f71. MatrizR01–R21/contratoG2/S1/U2b1 íntegros. ParesRED observados con recibos ypreimágenes, conformidadcausal completa aún la evalúa lenteA, no se declara aceptada por suiteverde. Tresdeltasprivados autorizados retain/originalacquisition/signatures; call/open/closeAST ytodosviejosnodos tests preservados.

Diagnósticosactores preservados: impresión cp1252, primera instrumentacióncoverage sin datos ycodec faltante receipt.py; este último reparado sólo suministrando copiareadonly en snapshotcodec separado,208PASS finales. PrimerverificadorROOT esperaba docker run pero comandosreales soncreate/start/wait/rm; corregido lector antes mutarcanon/snapshot, sin lanzarcontendor ni tocarproducto. No son RED deproducto.

T05en-progreso/M1NO-VERDE: QAindependiente deU2b2 yCAS pendientes; bootstrap/store/writer/ACK/fullchain/ext4/lifecycle/E2E/manuales no probados. No cambio de datos/BD,administración/GPU/Ollama oservicios ajenos. Evidencia `.cache/dev-cycle/m1/storage-nt-geometry-product-review1-20261011/prepare-root.receipt.json`. Único marker mixto conQA M2; tiempo reloj noIAmedida, métricasrealesnull.


## Revisión de dos lentes — intento 1: T-05/U2b2 producto — cuatro Important — 2026-10-11T13:12:38.084904+00:00

| # | Grado | Gap | Tarea | Veredicto | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Clases y longitudes exactas sin RED causal | T-05/U2b2 R02 | pendiente FIX1 | A: bootstrap ausente no prueba clases11/17 y longitudes28/4; preimágenes y UTC |
| A02 | Important | Cuatro DTO frozen escritos antes del test | T-05/U2b2 R17 | pendiente FIX1 | A: green-abi12:21:35 frente characterization12:29:17 |
| B01 | Important | Parent original no fijado al adquirir child | T-05/U2b2 R11 | pendiente FIX1 | B: parent101→303 e ID distinto antes de entrar; devuelve4096 |
| B02 | Important | Retención descarta arena metadata incierta | T-05/U2b2 R09/R19 | pendiente FIX1 | B: FALSE997/interrupt+GC pierde buffer; control U2b1 lo conserva |


Lentes A+B frescas efectivas; C/D auto false. ROOT verifica los cuatro recibos y streams B, incluida comparación U2b1 que retiene el buffer; no PENDING nativo. [Respuestas completas y arbitraje](testing/t05/storage-nt-geometry-product-review1-2026-10-11.md). FIX1 autorizado sólo en snapshot privado de dos fuentes; exige RED funcional y reescritura de comportamiento nuevo sin TDD para A01/A02. Original2374 intacto, canon af192/3de1e82 intacto. T05en-progreso/M1NO-VERDE; QA/CAS pendientes. Sin deuda aceptada ni cierre por suite verde. Jira desactivado, no comentario externo.


## T-05/U2b2 FIX1: evidencia causal verificada y revisión de producto 2 — 2026-10-11T13:39:55.143152+00:00

ROOT verifica el candidato privado sin incorporarlo al canon: 1259 archivos regulares y dos reparses sólo por stat, 27 fuentes del snapshot, original2369+5 intacto, 140 recibos de hijos esperados/reapeados, cuatro testigos NT ordinarios y TAR Linux. Windows419PASS, Linux301PASS29SKIP89deselected, codec208PASS; coverage módulo completo90,060852%, líneas90,410959% y ramas89,0625%,0exclusiones. Resultados del implementer, no QA independiente. Los 68 nodos función/clase anteriores y los 87 nodos superiores de tests se conservan; sólo tres métodos antiguos autorizados cambian.

- RED: test_geometry_exact_query_arguments_functional falló con AssertionError 0!=28/4/11/17 con reader, bindings y HANDLE ya adquiridos · 2026-10-11T13:15:49Z. Reescritura posterior y cuatro GREEN mismo SHA de tests.
- RED: test_geometry_all_four_dto_mutations_rejected falló con DID NOT RAISE FrozenInstanceError en los cuatro DTO · 2026-10-11T13:17:16Z. Reescritura posterior y cuatro GREEN mismo SHA de tests.
- RED: test_geometry_parent_acquisition_fixed_before_reader_child falló porque se aceptaba sustituir el padre original antes de la lectura · 2026-10-11T13:16:49Z. Fix posterior y tres GREEN mismo SHA de tests.
- RED: test_geometry_postmetadata_native_buffer_retained_child falló al perder el buffer de metadata en FALSE997/KeyboardInterrupt · 2026-10-11T13:17:18Z. Fix posterior y dos GREEN mismo SHA de tests.

ROOT contrasta recibos terminales, preimágenes, streams, JUnit, SHA por par y orden RED→reescritura→GREEN. Replays suplementarios con retirada propia están diferenciados de causalidad primaria. El diagnóstico b02-red-parent-retire con fuentes cambiadas mientras corría se conserva inválido, sin crédito TDD. Tres errores de preparación del verificador ROOT son diagnósticos privados corregidos; no afectaron producto ni snapshots aceptados.

Despachadas lentes frescas review_m1_geometry_product_a2 y review_m1_geometry_product_b2, intento producto2de3. Scope-check dos archivos,0fuera/avisos/exclusiones; selector real C/Dauto false. Tabla previa A01/A02/B01/B02 cuatroImportant permanece pendiente de juicio independiente. Snapshot base a2b5027211353e237b183d2fd54d3c43b02551d5; evidencia `.cache/dev-cycle/m1/storage-nt-geometry-product-review2-20261011/verification-root.receipt.json`. Canon runtimeaf192/test3de1e82 intacto; sin CAS/QA/cierreT05/M1. Sin GPU/Ollama/admin/producción/datos/BD. Jira desactivado.


## Revisión de dos lentes — intento 2: T05/U2b2 producto FIX1 — sin gaps — 2026-10-11T13:47:04.577957+00:00

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Clases y longitudes sin RED causal | T05/U2b2 | corregido | A2 valida cuatro RED funcionales 0!=28/4/11/17, reescritura posterior y mismos tests GREEN |
| A02 | Important | DTO frozen sin RED causal | T05/U2b2 | corregido | A2 valida cuatro mutaciones reales sin excepción en RED y rechazo tras reescritura |
| B01 | Important | Parent original perdido antes entrada | T05/U2b2 | corregido | B2 compara parent101→303/ID; FIX1 cero metadata/query, cierre child ordinario único |
| B02 | Important | Buffer metadata incierta perdido | T05/U2b2 | corregido | B2 seis contingencias comparativas: metadata arena y dosbuffers/dosIOSB conservados, poison, closeunknown sin retry |

LentesA/B frescas verificadas por ROOT, C/Dauto false, scope2/0fuera/0avisos. A280PASS/B41PASS únicos, B14contrapruebas,71hijos con streams/reaps y27fuentes porauditor comprobados. [Respuestas completas y fusión](testing/t05/storage-nt-geometry-product-review2-2026-10-11.md). SiguienteQA Windows/Linux/codec independiente; runtimeaf192/test3de1e82 canónicos intactos, sinCAS. T05en-progreso/M1NO-VERDE. Sin writer/ACK/ext4/E2E acreditados por review. Jira desactivado.


## T-05/U2b2 geometría: QA independiente aceptada e incorporación — 2026-10-11T14:06:03.528523+00:00

ROOT verifica769artefactos/27fuentes/imports/JUnit/100childreaps/4testigosNT/TAR154/PID0rm. Windows419PASS0SKIP, codec208PASS, Linux301PASS29SKIP89deselected0FAIL/ERROR. qa-gate funcionalVERDE928PASS29SKIP; wholeWindows líneas90,410959%/ramas89,0625%, codec95%/90,55944%,0excl. Linux73,69863%/67,1875%separado, no unión ni gate80fingido. Revisiónproducto2A/B sin gaps y cuatroImportant anteriores corregidos.

CAS2fuentes runtime8f0e7bd/tests145a883 tras guardas exactas af192/3de1e82; codec5db83 y parser811a578 intactos. [QA vigente y aceptación acotada](testing/t05/storage-nt-geometry-current-qa1-2026-10-11.md) · [PDF independiente,3páginas](testing/t05/storage-nt-geometry-current-qa1-2026-10-11.pdf). PDF estructural/previewprint verificados; no rasterización. Diagnósticos del verificador ROOT: etiqueta reparse-stat-only y pin adicional parser codec resueltos, sin defecto de producto ni mutación de evidencia.

Componente readonly incorporado, T05en-progreso/M1NO-VERDE. Bootstrap/S1 completo/store/writer/ACK/crash/lifecycle/ext4/E2E/manuales siguen obligatorios pendientes; ninguna cargaGPU/admin/producción/BD. Git incremental pendiente.


## Git incremental geometría y concreción store — 2026-10-11T14:13:57.781879+00:00

Commit/push538e19c983b8d891813e776ea34cd9894abd1483 verificado en origin/m1/t-02-esquema; seisficheros del componente aceptado, indexvacío, restantes cambios preservados, sin mergeamain. ROOT inicia actorfresco design_m1_journal_store_contract1 sobre17fuentes readonly; concretará organización del store nativo completo O2/S1/G2, exclusividad/custodia/buffers/PREPARE-COMMIT-ACK/recovery. Diseño aúnpropuesta, sin writer ni efectos. Namespace .cache/dev-cycle/m1/storage-journal-store-contract-20261011. T05/M1 abiertos; S1fullchain/ext4/ACK/E2E/manuales siguenpendientes.


## Store nativo: organización elegida y segunda pasada — 2026-10-11T14:41:23.309932+00:00

ROOT eligeO2kernelIOprivado/store separado bajo delegación, preservando durableO2/S1/G2. Originaldesign d296448 intacto/snapshot17verificado; actor design_m1_journal_store_contract1 reanudadoen segunda pasada, sólo selected-design/ADR0081propuestos privados. No writer/código/ACK ni pruebasnativas nuevas autorizadas por ese documento. Producciónfullchain/bootstrap/lifecycle/causalrecovery/ext4/E2E/manuales pendientes; T05/M1 abiertos.


## Revisión de dos lentes — intento 1: contrato store Windows — un Important — 2026-10-11T14:55:23.433358+00:00

A1Important enlacesprivadosspec/plan/adr/fuente noresuelven desde destinoscanónicos. ROOTconfirmasinrebate/deuda; B1sin defectoscorrectitud. [Respuestas completas y fusión](testing/t05/storage-journal-store-contract-review1-2026-10-11.md). Snapshot20/diffexactos; planextra congelado ahora paraFIX21, sinpin retrospectivo. FIX1fresco ownership2docsprosa, contratonativo/decisiónO2preservados. Revisión2/QA/adopción/código/storefull pendientes; T05/M1 abiertos.


## Store contrato FIX1: referencias corregidas y revisión2 — 2026-10-11T15:05:36.552142+00:00

Architectfresco fix_m1_store_contract_links1 entregó propuesta exacta readonly por límite de rol,0writes. ROOTaplicó sólo sustitucionesdefrontmatter/links/párrafo en2docsprivados: diseño2d221e15/ADR91438f75, hashescoincidenpropuesta.19no-owned exactos/snapshot21(originalreview20másplanextraactual); originalreview20intacto. Links/metadatos6resuelven dentro snapshot sinfallbackexterno; no cambia contrato nativo/durableO2/S1/G2/ACK. ScopeT05 declaraexplícitamente documentos parareview2. A01Importantpendienteveredictosegunda revisión yQA; sinadopciónni producto/T05close.


## Revisión de dos lentes — intento 2: T-05 contrato del store — A/B sin gaps

ROOT 2026-10-11T15:29:24.916384+00:00:0Critical/Important/Minor, A01Importantcorregido. Scope4docs,0fuera/avisos/excl,C/DautoFalse. [Informe completo](testing/t05/storage-journal-store-contract-review2-2026-10-11.md). QA documental independiente pendiente; ninguna implementación nativa ni cierreT05/M1 acreditado.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important anterior | Referencias privadas rotas | T-05 | corregido FIX1/review2 | seis refs y tres aristas verificados; contratoD76+conservado |


## T-05: contrato store incorporado tras QA documental — 2026-10-11T15:37:47.375671+00:00

ROOTverifica60payload/21fuentes/19guardas/2seams/7tools y95checks,gateverde. DiseñoO2/ADR0081incorporados; [QA independiente](testing/t05/storage-journal-store-contract-current-qa1-2026-10-11.md). Sinstorecódigo, nativeFlush/ACK/fullchainS1/bootstrap/lifecycle/recoverycausal/ext4/E2E/manuales; T05/M1en-progreso. Próximas unidades requieren liberaciónROOT, TDD ypruebasnativaspropias.


## T-05: testigo funcional nativo de WRITE_DATA sin APPEND y flush — 2026-10-11T15:56:18.283475+00:00

ROOT45payload/13fuentes/3testigos3controles/PIDs0verificados. [Informe](testing/t05/storage-journal-store-flush-native-2026-10-11.md). Access0x00120083/share0/mode0x2a/B65536/131072Bwrite-flush-readexactos. Exits1global+1conservados,10handlespropios/1arena cerradosporproceso; UUIDcontroldeltas1/0/0coherentes,sinidentificarhandle. NoS1full/ACK/powerloss/store/bootstrap/lifecycle/recovery/ext4/T05/M1. Próximaunidadkernel productorequierecontratoconcreto+TDD/reviewQA.


## T-05: elección de concreción K1 y alcance de revisión — 2026-10-11T16:43:01.811811+00:00

ROOT elige C2 bajo delegación del propietario: fachada de custodia/memoria y binder Windows separado. Se añaden cinco rutas explícitas a Archivos T05; sólo el diseño nuevo y enlace del contrato padre forman el diff documental actual, las cuatro fuentes K1 siguen futuras. El arquitecto no libera producto ni altera O2/S1/G2. Revisión A/B y QA documental independientes preceden adopción/RED. K1 conserva ABI, arena opaca propia y cierre único; no archivo/I/O/trust/ACK. Full-chain, store, recovery causal, bootstrap/lifecycle/ext4/E2E y manuales siguen obligatorios. T05/M1 abiertos, TDD n/a: diseño/prosa, uso real null.


## Revisión de dos lentes — intento 1: T-05/K1 contrato kernel privado — sin gaps

ROOT fusiona A+B frescas sobre diff documental2files/18fuentes, base23898bdce3799156d6088365b94f7865d626088d. Scope0 sinexclusiones/avisos; C/D auto false. Doce criterios K1 conformes documentalmente, ejecución futura no acreditada. Respuestas íntegras en .cache/dev-cycle/m1/storage-journal-kernel-contract-review1-20261011/response-a1.md y response-b1.md. A plantea ambigüedad de palabra reservado vs redondeoOS de VirtualAlloc; B no acredita defecto de corrección. La cuota aritmética r=n+B-1 describe bytes solicitados incluyendo padding; no se afirma medición de compromiso físicoOS. QA documental debe contrastar y señalar si es preciso concretar antesRED; no puede convertir ese número en cotaOS o prueba de memoria native. No gaps de corrección pendientes por estas lentes. Diseño elegidoC2 aún sinadopción/implementación, QA independiente siguiente. T05/M1 abiertos, fullstore/S1/ACK/bootstrap/lifecycle/recovery/ext4/E2E/manuales siguen obligatorios. 2026-10-11T16:50:31.912594+00:00


## T-05/K1: QA1 NO-VERDE conservada y FIX1 para revisión 2 — 2026-10-11T16:59:22.166831+00:00

ROOT verifica QA1 57payload/18fuentes y qa-gate oficial exit1:66PASS1FAIL. QA1-01Important nuevo de QA no se atribuye retrospectivamente a revisión1 A/B limpia. La cuota9437176 sin requested podía interpretarse como cotaOS;8r1179647 redondeados4096 dan9437184. ROOT confirma gap, no lo rebaja ni lo tapa con notaexterna. FIX1 arquitecto fresco 34payload/17nonowned intactos; preimagen dc4c5cb8 y candidato7ceae414. Normativa fija sum(n)<=8912896 y sum(r)<=9437176, r=n+B-1, count8; contabiliza bytes solicitados incluyendo padding, no cota físicaOS. Estados/API/objetivoFullchain/store/ACK/ext4 conservados; revisión2/QA2/adopción/RED pendientes, sin unidad implementada ni cierreT05/M1.


## T-05/K1: contrato incorporado y release de implementación — 2026-10-11T17:15:43.986178+00:00

ROOT autentica81payload/18fuentes/91checksdoc/JUnit91/gateoficial0, QA1roja57payloadintacta. Review2A/Bsin gaps, QA1-01corregidofuentenormativa7ceae414. C2contratoadoptadoconmetadataactaROOT; normativasAPI/ABI/custodia/cuotaswhole80 intactas. InformeQA2fueescrito porQA directamente en destino canónicoaunquebriefsólosnapshot; ROOTpreservasourceSHA d1db822f yregistra placementdrift,noCASprevioficticio. LiberadoactorimplementerfrescoK1 cuatrofuentesnuevoABI/AlignedArena, RED-GREEN causal; memoria volátil propiaWindowsnative permitidaensupervisorhijolimitadoVirtualAllocFree/copias,reapsySHA; ningúnarchivo NTIO/ACL/admin/RootContext/grants/GPU/servicios. ProductoK1pendientereviewQA/CAS,T05M1 abiertos. Evidencia .cache/dev-cycle/m1/storage-journal-kernel-contract-qa2-root-20261011/acceptance-root.receipt.json.


## T-05/K1: candidato verificado por ROOT, revisión producto pendiente — 2026-10-11T17:53:07.174962+00:00

ROOT autentica186artefactos/23preimágenes/21recibos de ejecución,91PASSWindows y cobertura whole completa fachada354/362=97,790055%líneas/95de106ramas; ABI70/70=100%líneas/10de10ramas,0exclusiones. Runtimead8ca095/6a444d03, tests6915b382/d55fba92 privados, sinCASniaceptaciónK1/T05/M1. LimitaciónTDD declarada: REDtempranos conservan runtime/nodos/tracebacks pero no snapshot completo de test; desde supplemental-controls sí existe. No recrear pasado; lenteA juzga suficiencia/ley de reescritura. Otra limitación corregida para evidencia actual: actor importspid19224 y Popen30628 no fueron relacionados en vivo; actorretira30628comoownernativo. ROOTconsulta ambos ausentes, no reconstruye esa relación. Nuevo testigo contemporáneo .cache/dev-cycle/m1/storage-journal-kernel-k1-pid-witness-root-attempt2-20261011 acredita launcher17324→intérprete29416 vivo, tres positivos sobre los mismosSHA, freebaseoriginalx1, exit0 y ambos ausentes despuéswait. PrimerwitnessROOTfallópor encodingutf8-sig delauditor antesGO, procesos propios expiraron sin nativecases y ausencia verificada; preservado,no fallo producto. Native sólo memoria propia, no archivos/NTIO/GPU/admin/ACL/RootContext/ACK. Whole/report son del actor; Linuxreal/revisión/QA independiente pendientes. Uso realnull.


## Revisión de dos lentes — intento 1: T-05/K1 — un Important confirmado · 2026-10-11T18:01:47.185855+00:00

Lentes A+B frescas, scope0/sinavisos/C-Dauto false; diff4fuentes completas, base7256bace. [Fusión completa](testing/t05/storage-journal-kernel-k1-review1-2026-10-11.md), normalización ROOT no literal con todos los criterios y límites del retorno conservados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01/B01 | Important | Publicación prematura closed antes del registro completo | T-05/K1-07/08 | pendiente, FIX1 fresco | fuente499–502; cortesconstructor/charge/remove despuésTRUE; free1 y closed con inflight1/contextunknown |

ROOT valida contra C2§4.6, sin rebate. ActorFIX1 trabaja aislado sólo fachada/testIO con TDD causal y preimágenes completas. ABI/testABI/23contextos guardados. NoCAS niQA niaceptaciónK1/T05/M1. Testigo nativoROOT actual acredita relación launcher17324→intérprete29416 y retirada, no pasado30628/19224. Uso realnull.


## T-05/K1 FIX1: TDD verificado, revisión2 pendiente — 2026-10-11T18:08:13.013040+00:00

RED: test_fix1_release_finalization_cut falló con 15FAIL funcionales antes del fix; fuentead8ca095 y tests completos contemporáneos conservados · 2026-10-11. RED: publicación/rollback falló con6FAIL/4PASS antes del fix; los4ya verdes no se cuentan comoRED · 2026-10-11. GREEN25regresiones/112CPU/4native deselected. ROOT verifica90payloads/25guards/186históricos y cuatro ejecuciones con preimages+raw+JUnit. Fachada0d23e8f6/teste2a249fd; wholeIO368/376=97,87%líneas100/108ramas; ABIreadonly68/70=97,14%líneas10/10ramas,0excl. Estado/outcome unknown reservado, accounting/inflight restaurados conservadoramente sinfreeextra, contexto/rollback incluidos. A01/B01 candidato corregido, no adjudicaciónfinal niCAS. Revisión2 recibe tabla completa previa, scope/diff4fuentes. Nativo nuevoSHA/Linuxreal/QA independientes pendientes; testigo anterior no se atribuye al nuevoSHA. T05/M1 abiertos, actualusagenull.


## Revisión de dos lentes — intento 2: T-05/K1 — sin gaps pendientes · 2026-10-11T18:15:27.684337+00:00

A2/B2frescas leen diffcompleto4fuentes71549bytes, scope0sinavisos/C-Dauto false ytablapreviacompleta. [Fusión íntegra normalizadaROOT](testing/t05/storage-journal-kernel-k1-review2-2026-10-11.md), no transcripciónliteral. A2/B2cada112CPU4native deselected; B2probes17+opcode111PASS; diagnósticosdelharness preservados,no fallosproducto.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01/B01 | Important | Closed antesregistrocompleto | T05/K1-07/08 | corregido | IO500–514/554,25regresiones,unknown/cuota/calls/free1/retry0,closedpreviosyprimariaseparados |

0nuevosCritical/Important/Minor, sinrebates ni deuda. Linuxreal/nativoactualSHA/QA independiente siguen pendientes; noCAS niaceptaciónK1/T05/M1. HistoriaTDDtemprana limitada no reconstruida; FIX1preimagescompletas. Uso realnull.


## T-05/K2: adquisición propia en concreción — 2026-10-11T18:17:48.301220+00:00

Contrato K1C2 exige cerrar adquisición/ancla/callingarenas/profiles/descriptor/IOSB/output/lifetime antes del REDK2. ROOTabreconcrecióndocumental aislada mientrasQA K1sigue: NOliberación runtimeK2 niK1adoptado aún. Arquitectofresco comparaopciones; sólo storage-journal-acquisition-design.md candidato, sin nuevo grant, llamadasnativas, RootContextni ACLremediada. Callingseams S1/G2/U2readonly yseparaciónfake/acquisiciónreal permanecen. Ownership documentonew declaradoT05; usuario delega decisiones. ReviewQAadopciónconcreción yreleaseK2posteriores; T05/M1 abiertos. Uso realnull.


## T-05/K1 QA1: funcional verde, formato pendiente — 2026-10-11T18:23:43.588690+00:00

QA independiente informa Windows116PASS yLinux106PASS10SKIP exclusivosWindows, mismos116nodos yruntime0d23e8f6. Predicción ROOT4SKIP fue incorrecta: hay6controlesABI/ctypesWindowsademás de4positivos; no modificarplataforma ni ocultarskips. Nativo vivo launcher26876→intérprete18844 connonce yretiro verificados porQA; tresextraspropioscopyindependent/freebase1/charge0. WholeWindowsIO370/376=98,40%/ABI70/70=100%; LinuxIO361/376=96,01%/ABI36/70=51,43%; combinaciónoficial porSHA no promueve51%Linuxaéxito. Ruffcheck0 peroformatcheck1enregresiones testIO839+. SinCAS; nuevoFIX2 estrictamenteformato testIO, AST completoidéntico yambosruntime/ABI/testABIbyteexactos. TDDn/aformato, no nuevoREDconductual ni modificaciónsemántica. Gateformato exige0 antesadopción; QA1raw/limitaciónBOMauditorintacto, QA2por nuevosSHA trascorrección. No hitoaceptado; usage realnull.


## T-05/K1 FIX2 formato verificado ROOT — 2026-10-11T18:28:52.341582+00:00

SólotestIOe2a249fd→b1e23428 reformateado, AST íntegroidéntico (8fbcf14f),37testfunctions/fixtures/assertions/params/casesconservados,26readonlyguards yambosruntimes+testABIbyteexactos. RuffformatRED1→formatter→check4sources0/formatcheck4sources0; pre/postenterosyrawsauténticos. TDDn/aformato, ningúnREDconductualnuevo ni pytest delactor. A01/B01review2corregido preservado; review3 sóloformatdelta/sinreabriraprobado. QA1funcional116Windows/106Linux10skip, formato1,harnessdiagnósticos/spillruffcachedeclarados,sinCAS. QA2actualSHA con fuenteactual requerido. T05/M1abiertos.


## T-05/K2: ROOT elige owner único O1 — 2026-10-11T18:33:31.816708+00:00

ArquitectocomparóO1ownerúnico/O2directory+leafpins; ROOTeligeO1porcustodia/locks/registro/cierre sintransferencias. Campospropuestosconclarificaciones en .cache/dev-cycle/m1/storage-journal-k2-acquisition-concretion-20261011/choice-root.receipt.json. Principaladmission K4a se concreta antesK2nativo, sinRootContext/cadena; fullchainK4b después, CREATEsólotrasparentS1nominal. Cuotas/tombstones/rotación supervisada/gatesG1/no-follow exactos yhelpersABIcerrados antesRED. Rolarchitectrestringíaoptions/customfilename: ROOTmaterializóoptions-root.mdnormalizado,no literal; candidatoarquitectoenruta design.mdpermitida; mapeo canónicoROOTsólotrasreviewQA. C2/O2/S1/G2intactos; noauthority/ACL/runtimeporprosa. T05/M1abiertos.


## Revisión de dos lentes — intento 3: T-05/K1 — formato sin regresión · 2026-10-11T18:36:03.095925+00:00

A3/B3frescas difffull4fuentes71638bytes, scope0/CDfalse,sóloformato; tablas22A/11Bpreviasconservadas yactualizacionesQA1runtimeexplícitas. [Fusión completaROOT normalizada](testing/t05/storage-journal-kernel-k1-review3-2026-10-11.md). ASTfull8fbcf14f/37tests/149asserts/26guards, runtime0d23/6a44 ytestABIbyteexactos.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01/B01 | Important | Closedantesregistro | T05/K1 | corregido conservado | Mismosruntime/asserts deFIX1 |
| QA1-formato | incidenciadegate | Formato testIO | T05/K1 | corregido | Ruff--no-cache check4/format4=0, ASTenteroidéntico |

0gaps nuevos, sin deuda/rebates. ROOTverifica530payloadQA1; funcional116Windows/106Linux10SKIP, forma1histórico preservado; QA2testb1pending, noCAS niT05/M1aceptado. ROOToriginal4SKIPpredictionrectificadapor10sinplataformafingida. Uso realnull.


## T-05/K1: componente de memoria adoptado por ROOT — 2026-10-11T18:57:43.747304+00:00

ROOTverifica518payloadsQA2/27fuentes y131importsWindows/113Linux, mismos116nodosJUnit. QA2Windows116PASS/Linux106PASS10WindowsSKIP, ambosgatesoficiales0,Ruffcheck/format--no-cache0,ledger0/coverage0. WholeporfuenteWindows/combinadaIO370/376=98,4043%líneas/100de108ramas,ABI70/70=100%/10de10ramas;LinuxIO361/376=96,0106%/ABI36/70=51,4286% explícito,no promedio ni skipconvertido. Supreal24512→36000 y32184→40852 liveCIMnonce,wait0/ambosausentes;4nativosJUnit y3extrasmemoriapropia/freeoriginalbase1/charge0,2negativosLinuxsinctypes. ROOTCAS4newfilesSHA0d23e8f6/6a444d03/b1e23428/d55fba92 y112focalesCPUcanónicos0conimportsdeRactual, U1/U2byteexactos. [QA2vigente](testing/t05/storage-journal-kernel-k1-current-qa2-2026-10-11.md).

Review1A01/B01Importantclosedprematuro→FIX1TDD15RED+6RED4yaGREEN→25GREEN,review2clean;QA1funcionalverde/formato1→FIX2ASTenteroigual→review3clean/QA2completoverde. Historiaoriginal186/FIX190/FIX2prepostenteros yQA1530 conservados; nofulltesttemprano originalreconstruido. Receipts deauditoresCPU nofabricanownernative; testigoROOTantiguo sólo SHAanterior,historia19224/30628retirada. QA1BOM/extraerrado/inspectquoting/ruffcache yQA2wrongcontainerpath127/PDFdefaultexeausente sonharnessdiagnósticospreservados,nofallosproducto;reportSHAfinalactualprevalece.

K1aceptado SÓLOmemoriapropia/ABI/custodia/copies/cierres; NOarchivoNTIO/RootContext/grant/K2/K3/K4/K5/store/ACK/recuperacióncausal/bootstrap/lifecycle/ext4/E2E/manualesniT05/M1completado. K2ownerúnicoO1enconcreción,releasespropiaspendientes;M1formal0/17. NoGPU/Ollama/admin/ACL/servicios/dataproducción ni mainmerge. Uso realnull.


## Git incremental K1 — 2026-10-11T19:08:02.117683+00:00

Commit/push ddc509b911191e7bc7f5a73dbcaa4fc63ab11f65 verificado en origin/m1/t-02-esquema, 11archivosaceptados,índicevacío, sin rutas personales ni data/modelos. Rama compartida bajoexcepciónya registrada; nostageglobal/reset/checkout/mainmerge. Componenteaceptado K1, no clone/CI autónomo ni hito completado; no incorporadoscambiosajenos. Uso realnull.


## T-05/K2: contrato de adquisición O1 en revisión1 — 2026-10-11T19:14:00.498296+00:00

Arquitectofrescoretornaúnicodesign.mdpermittedrole63074B/SHA110f291d/27guardssinalterar/25pinsSDKprimarios. ROOTmapeaBYTEEXACTOalcandidatoprivados storage-journal-acquisition-design.md; namespacealiasno autoridad ni cambiosemántico. K1yaadoptadoypusheado ddc509b, cuatrofuentesSHAactualesigualesalsnapshotK2; codefuenteK2pending.noreleaseNative. O1ownerúnico/SDK/estructuras/masks/quotas/poolconslotspreregistrados/principalScopes/custodia/cierrescerrados. Gates K4aissuer/G1DIRECTORYno-follow/K3/K4b/K5/rotación/store/ACK futuros; noemisorprovenniNativeRootContext/G1positiveporprosa. RevisiónA/Bfreshscope1doc conoverlayROOTactualychoice; QA documental/adopciónantesREDK2. T05/M1abiertos,M3=2/42documentales,nohitoaceptado/usagenull.


## T-05/K2: contrato de adquisición O1 en revisión1 — 2026-10-11T19:14:48.221059+00:00

Arquitectofrescoretornaúnicodesign.mdpermittedrole63074B/SHA110f291d/27guardssinalterar/25pinsSDKprimarios. ROOTmapeaBYTEEXACTOalcandidatoprivados storage-journal-acquisition-design.md; namespacealiasno autoridad ni cambiosemántico. K1yaadoptadoypusheado ddc509b, cuatrofuentesSHAactualesigualesalsnapshotK2; codefuenteK2pending.noreleaseNative. O1ownerúnico/SDK/estructuras/masks/quotas/poolconslotspreregistrados/principalScopes/custodia/cierrescerrados. Gates K4aissuer/G1DIRECTORYno-follow/K3/K4b/K5/rotación/store/ACK futuros; noemisorprovenniNativeRootContext/G1positiveporprosa. RevisiónA/Bfreshscope1doc conoverlayROOTactualychoice; QA documental/adopciónantesREDK2. T05/M1abiertos,M3=2/42documentales,nohitoaceptado/usagenull.


## Revisión de dos lentes — intento 1: T-05/K2 contrato — sin gaps · 2026-10-11T19:27:44.687117+00:00

ROOT fusiona íntegramente criterios A33/B10, normalización explícita no transcripción; ambas lentes frescas DONE antes/logout. 0Critical/Important/Minor, scope1/fuera0/avisos0 y C/Dfalse. Candidato110f291d744líneas63074B/28pins/25fuentesSDK; tablas completas en testing/t05/storage-journal-k2-acquisition-review1-2026-10-11.md. QA documental independiente siguiente; no adopción ni runtime K2/G1/K4a por revisión. T05/M1abiertos y fullstore/S1/recovery/ext4/E2E/manuales obligatorios. Uso realnull.


## T-05/K2: contrato de adquisición O1 adoptado — 2026-10-11T19:37:41.224496+00:00

ROOT verifica313payload/34inputs/107imports,28snapshot/27guards y matrizQA119/119, tresgates0, A/Bintento1sin gaps. Fuente110f291d preservada privada; metadata/rootacta vigente distinguen K1aceptado del cortehistórico. Contrato nuevo storage-journal-acquisition-design.md adoptado, sin RED/runtime/native/G1/RootContextgrants; K4aemisor/principal/pin debe cerrarse antesK2nativo, no añadir emisor desde path/SID/flag. T05/M1abiertos, O2/S1/C2 y restantesstore/fullchain/recovery/ext4/E2E/manuales intactos. Informe testing/t05/storage-journal-k2-acquisition-current-qa1-2026-10-11.md; PDFprivado sóloHTMLpreviewinspeccionado, noPDFraster. Uso realnull.


## T-05/K4a: principal efectivo previo a adquisición nativa — 2026-10-11T19:39:03.319113+00:00

K2contratoadoptado/QA119/119 ycommitpush755b476d007ae87cb253b53f0dea1a87635778a9 verificado,3docsaceptados/índicevacío; no runtimeK2. ROOTdeclara ownershipcontratoprincipal/identityfuture/tests y abreconcreción K4a emisor/principal/epoch/pin/revocación; comparaciónopciones anteselección, noauthorityporSID/path/flag/hash/DTO ni delegar emisor aotrafronterasinnombre. Observación efectivaWindowsownprocess/thread ybootstrap privado deben concretarse antesRED/nativetestK2. CadenasS1/K4b posteriores no requeridasparacandidatoreadonlyni concedidasporK4a; CREATE sigueguardK4b. HostancestorsMODIFYno remediados. Sin ACL/admin/tokenajeno/GPU/DB/servicios tocados; T05/M1abiertos,restantesstore/fullchain/recovery/ext4/E2E/manualesobligatorios. Usorealnull.


## T05/K4a: O1 completo y coordinación propuesta ADR0084 en revisión1 — 2026-10-11T20:15:37.285638+00:00

ArchitectDONEsource24deb33e60443B/38readonly/12SDKpins/18criteriosfuturos; emisor privadofinito/tokenefectivo/pin yscope nongrant. ROOTreservaADR0084 privado porqueañadefronteracomún/locks/registro aC2yK2documentados, guardAGENTSdecisiones; no cambiaConstitución/fronteraS1/RootContext posterior ni ejecutaNative. Difffull5docs:newK4a+apéndicesbyteexactextraídosC2/K2+ADR/index; sourceoriginal/opcionesd2d0e intactos. SharedKernelBoundary→owner→session→context/mismoPoison/callerpinrequiresalreadyownerlock/registrybreve; runtimeK1actualNOimplementa nuevo preludio niAQAnuevaporprosa. T05/M1abiertos,K4bnativefullS1/G1/K3/K5/store/recovery/ext4/E2E/manualsobligatorios. ReviewQAadopciónantesRED/currentnativepids; uso realnull.


## Revisión de dos lentes — intento1 K4a — B01Important confirmado · 2026-10-11T20:25:28.516338+00:00

ROOTnormaliza44A/18Bcriterios completos; B01allocation131328/8rechazaanteK1C2min512/modulo, control131584/512validaprefijo puroAST/backend0. Aconformidadworkspace/positive acotadaporB; 0Critical/1Important/0Minor,sinrebate. FIX1fresco sóloalineación/budget: lógico131328, n131584/B512, requested132095B, SDKalign8subranges/tail256realnoreinterpretadoSDK. Propagaralllimits/cases/apéndice/ADRcandidato,norelajarC2/nativeruntimeno cambiado. Fuente24deb33e/41pins originalesintactos; sourcecurrentPID nativoseQA futura. T05/M1abiertos, ADR84proposalprivada/reviewQAadopciónpending/usorealnull.


## T05/K4a FIX1: revisión documental2 preparada — 2026-10-11T20:31:07.282723+00:00

Fuente fresca 3c20d078/70176B congelada;41readonly intactos, original24deb33e preservado. B01corrige workspace sin relajarC2: lógicoSDK131328,n131584,B512,requested132095,tail256; SDKfieldalign8 y límitesSDK65536 conservados. Revisión2 recibe tabla completa44A/18B+B01 con evidenciaAST previa; no native/QA/RED/adopción. Diff5docs/ADR0084propuesta privada; K1actual no cambiado, T05/M1 abiertos. Uso realnull.


## Revisión de dos lentes — intento 2: T05/K4a — B01 corregido documentalmente · 2026-10-11T20:36:28.078401+00:00

ROOTfusion44A/18B completas:0Critical/Important/Minorpendientes, sinrebates/deuda. workspace lógicoSDK131328/arena131584/B512/r132095/tail256,source3c20d07870176B41pins,ASTactualguardsconfirmadas sinbackend/importnative. Prosa noQAproducto/currentK1whole/native; datos/gates futurosintactos. QA documental preparada, despachopendiente; contrato/ADR84noadopted.T05/M1abiertos.Uso realnull.


## T05/K4a contrato y ADR0084 ratificados documentalmente por ROOT — 2026-10-11T20:45:39.188502+00:00

QA232/232/gatesledgertrazabilidadQA0,41snapshot39guards2ausencias/34payloadsverificadosROOT. Revisión2A44B18limpia/B01corregido; fuente3c20d07870176B adoptadabyteexacta. C2/K2preservanprefijos ycoordinationexacta; ADR0084estadoaceptada/index ynotaratificaciónsonmetadataROOT añadida, no cambiarnormaSDK/native. QAHTMLfirstlastprintpreviewverificada, PDFgeneradohashsí/noraster; procesosChromepropiosretirados. NoK4anative/kernelqueriesactualesporprosa. K1actualsinnewboundary hastaTDDimplnueva,currentSHAwhole/nativerealPIDreap pendientes. K4b/G1/K3/K5/fullS1/store/ACK/recovery/bootstrap/lifecycle/ext4/E2E/manuals/T05/M1 siguen abiertos. Uso realnull.


## T-05/K4a — RED nativo propio verificado por ROOT — 2026-10-11T21:29:46.934069+00:00

RED: native_identity_child.py::bootstrap_current_deployer falló con IdentityError ABI_UNACCREDITED (funcionalidad ausente; sin binding/DLL/query de producto) · 2026-10-11T21:05:30Z. ROOT verificó nonce READY/RUN, cadena CIM manager→launcher10668→interpreter37252, seis fuentes congeladas y ausencia/reap de ambos PID. Recibo `.cache\dev-cycle\m1\storage-journal-principal-k4a-bootstrap-native-red-root-20261011\receipt.json` SHA `86b5a2e5b5b1bbf2a1bfda06357231f73bc4a6a8f82b8689703ee6710f4fae4e`.

GREEN posterior propio 2026-10-11T21:21:32.998788+00:00: bootstrap→issue READ_ONLY→precheck→close→close idempotente, manager→launcher34216→interpreter21044, exit0/reap y ausencia CIM. Recibo `.cache\dev-cycle\m1\storage-journal-principal-k4a-bootstrap-native-green-root-20261011\receipt.json` SHA `4b360270642e98a0695b100fc9d401ada9db366c4f56d75017c34145d040c751`. Sólo prueba su corte histórico identityf25570e7/IO66a6ce03/ABI85a93733; no acredita fuentes posteriores, unión de cobertura ni QA de K4a completo. El nuevo corte final deberá tener prueba y cobertura propia antes de revisión/QA/CAS.

Incidente de alcance preservado: el actor incluyó tres pruebas K1 de memoria propia en pytest antes del launcher auditado ROOT. No se cuentan como validación nativa autorizada; siguientes CPU filtran `-k "not native"`. No hubo consultas de archivos/ACL/otros procesos. Native ROOT separado usa exclusivamente tokens del proceso/thread propio y memoria propia, con auditoría previa. K2 owner/pin real, K3/K4b/K5/G1/fullS1, store/ACK/recovery/ext4/bootstrap/lifecycle/E2E/manuales siguen pendientes. T05/M1 abiertos. Uso real null.


## T-05/K4a — prueba propia final2 y cobertura histórica ROOT — 2026-10-11T21:37:56.570800+00:00

ROOT verifica corte identity5a35098d/IO6c1cb2e4/ABI85a93733: proceso propio launcher30652→interpreter13540, nonceREADY/RUN/cadenaCIM, bootstrap→main+thread propio READ_ONLY→precheck→K5rechazo0calls→close/idempotencia→reloadrechazo,3observaciones/66subcalls/6cierrestoken, charge0, exit0/reap/ambosPIDausentes. Recibo `.cache/dev-cycle/m1/storage-journal-principal-k4a-final2-native-root-20261011/receipt.json` SHA `79256584d71050923941fa2f9482e6e04ff6b0cdadf21bc67caa502684d710a8`.

Unión oficial coverage con branch=True mismo corte6fuentes: CPU162PASS12deselected y nativeROOT propio. Coverage usa preimagenCPU contemporánea verificada before=after y snapshotROOT congelado. Whole líneas identity737/855=86,1988%, IO448/467=95,9315%, ABI110/118=93,2203%; líneas+ramas82,4050/93,8023/91,4286%,0omit/exclude. Recibo coverage-union-root.receipt.json SHA `5060ffa57b20b8055b39ee0ef172625ee577d937e527bb71100cd42389aa0c06`. Sólo cortehistórico final2, noQAindependiente ni código posterior.

DiagnósticosROOT preservados: primera unión se detuvo por cambio test del actor hacia final3 después anunciarfreeze; unión usa preimagenCPU auténtica en vez fuente mutable. Primer reporte de unión resolvió path JSON relativo desde cwdR en vez cwdA; se corrigió sólo harnessadministrativo, sin repetir native ni cambiar datoscoverage/producto. Fixfinal3 por causa primaria+cleanupunknown está en progreso, exige nuevo freeze/native/coverage/revisión/QA. K2owner/pin real sigue no liberado/failclosed; T05/M1 abiertos. Uso real null.


## T05/K4a núcleo — final3 autenticado ROOT y revisión1 preparada — 2026-10-11T22:05:23.976070+00:00

ROOT62recibos+preimágenes/argv/streams/JUnit y40readonly/6fuentes verificados, source85328c3b/IO6c1cb2e4/ABI85a93733. CPU164PASS12deselected/vecinosU2397PASS22deselectedactor. Nativefinal3ROOTlauncher33100→real1548nonceREADY/RUN+CIM+reap/ausencias,3obs/66subcalls/6closes/carga0. Uniónoficialbranch-mode mismo6SHAwholeidentity751/875=85,8286%líneas/81,9433%líneas+ramas,IO95,9315/93,8023,ABI93,2203/91,4286%,0omit/excl. Recibos `.cache/dev-cycle/m1/storage-journal-principal-k4a-final3-native-root-20261011/`. QAindependiente/Linuxe integración aúnpendientes.

Reportactor18criterios/7pares/TDDreportadosnoequivaleal18/18productoconforme: K2owner/pinsactualesnoexisten/failclosed, K4b/K5/K3/G1/fullS1/store/ACK/recovery/ext4/bootstraplifecycle/supervisor/M1E2E/manualespendientes. GroupREDs requierenjuiciofreshAporcriterio, no se certificanmonofocalessólo porcontarlos. Incidentesgreen13memoriadirecta ymutaciónfreeze2conservados, no positivosautorizados. T05/M1abiertos,nocodeCAS.

RED reportado: red01-platform · 2026-10-11T20:58:24.335864+00:00 · casos fallidos 1: test_native_bootstrap_platform_gate_before_loader
RED reportado: red01-run · 2026-10-11T20:56:03.264190+00:00 · casos fallidos 1: test_identity_bootstrap_claim_never_recycled_by_reload
RED reportado: red03 · 2026-10-11T20:58:23.913900+00:00 · casos fallidos 1: test_cpu_authority_is_separate_and_native_precheck_denies
RED reportado: red03-call-reference · 2026-10-11T21:13:35.871761+00:00 · casos fallidos 1: test_call_registry_uses_reference_not_dataclass_equality
RED reportado: red03-cpu-records · 2026-10-11T21:13:34.971787+00:00 · casos fallidos 1: test_cpu_records_have_nominal_issuer_policy_epoch
RED reportado: red04 · 2026-10-11T20:57:39.551109+00:00 · casos fallidos 1: test_identity_sdk_layouts_exact
RED reportado: red04-bindings · 2026-10-11T21:04:59.115251+00:00 · casos fallidos 1: test_identity_bindings_fake_sdk_and_call_wall
RED reportado: red04-ranges · 2026-10-11T21:17:22.697455+00:00 · casos fallidos 1: test_sdk_ranges_do_not_expand_into_other_buffer_or_tail
RED reportado: red05-07-11 · 2026-10-11T21:00:17.928485+00:00 · casos fallidos 9: test_cpu_observation_causal_rejection[thread_denied]; test_cpu_observation_causal_rejection[thread_false_output]; test_cpu_observation_causal_rejection[thread_true]; test_cpu_observation_causal_rejection[stats_drift]; test_cpu_observation_causal_rejection[stats_type]; test_cpu_observation_causal_rejection[fixed_length]; test_cpu_observation_causal_rejection[variable_capacity]; test_cpu_observation_causal_rejection[bad_result]; test_cpu_observation_causal_rejection[close_unknown]
RED reportado: red06 · 2026-10-11T20:56:35.824277+00:00 · casos fallidos 1: test_sid_output_only_current_returnlength
RED reportado: red06-sid · 2026-10-11T20:56:48.801242+00:00 · casos fallidos 4: test_sid_revision_count_and_attributes[\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]; test_sid_revision_count_and_attributes[\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]; test_sid_revision_count_and_attributes[\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]; test_sid_revision_count_and_attributes[\x01\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]
RED reportado: red08-dependency · 2026-10-11T20:58:24.752020+00:00 · casos fallidos 1: test_k2_future_owner_seams_fail_closed
RED reportado: red09 · 2026-10-11T20:59:57.571188+00:00 · casos fallidos 1: test_cpu_issue_requires_fresh_observation_and_scope
RED reportado: red09-epoch · 2026-10-11T21:16:27.030426+00:00 · casos fallidos 4: test_cpu_source_and_epoch_reject_before_callbacks[source]; test_cpu_source_and_epoch_reject_before_callbacks[issuer]; test_cpu_source_and_epoch_reject_before_callbacks[policy]; test_cpu_source_and_epoch_reject_before_callbacks[epoch]
RED reportado: red11-a4 · 2026-10-11T21:15:29.716195+00:00 · casos fallidos 1: test_cpu_post_true_before_ownership_cut_retains_preimage
RED reportado: red11-compaction · 2026-10-11T21:04:12.749643+00:00 · casos fallidos 1: test_cpu_known_frame_discards_raw_but_unknown_keeps_it
RED reportado: red11-primary-cleanup · 2026-10-11T21:32:34.950803+00:00 · casos fallidos 2: test_primary_principal_rejection_survives_unknown_cleanup[false]; test_primary_principal_rejection_survives_unknown_cleanup[cut]
RED reportado: red12 · 2026-10-11T21:02:56.785951+00:00 · casos fallidos 1: test_identity_poison_and_workspace_reject_unregistered_cpu
RED reportado: red12-alias · 2026-10-11T21:28:22.821527+00:00 · casos fallidos 1: test_alias_cannot_enter_another_native_domain
RED reportado: red13 · 2026-10-11T20:57:07.852851+00:00 · casos fallidos 1: test_boundary_precedes_memory_context_lock
RED reportado: red13-factory · 2026-10-11T21:02:56.279342+00:00 · casos fallidos 1: test_boundary_precedes_memory_factory
RED reportado: red14 · 2026-10-11T21:02:12.544890+00:00 · casos fallidos 1: test_cpu_admissions_lifetime_quota_before_calls
RED reportado: red14-frame · 2026-10-11T21:16:27.544686+00:00 · casos fallidos 1: test_cpu_raw_frame_already_active_rejects_before_calls
RED reportado: red14-metadata · 2026-10-11T21:17:22.215381+00:00 · casos fallidos 1: test_workspace_metadata_types_and_tail_are_exact
RED reportado: red14-observation · 2026-10-11T21:04:12.277341+00:00 · casos fallidos 4: test_cpu_observation_quota_reserves_before_sdk[observations-8192]; test_cpu_observation_quota_reserves_before_sdk[subcalls-229376]; test_cpu_observation_quota_reserves_before_sdk[observations-True]; test_cpu_observation_quota_reserves_before_sdk[subcalls--1]
RED reportado: red16 · 2026-10-11T21:02:12.980644+00:00 · casos fallidos 1: test_diagnostic_dto_sanitizes_rejects_unbounded_data
RED reportado: red16-seams · 2026-10-11T21:13:35.445029+00:00 · casos fallidos 1: test_future_native_seams_emit_typed_sanitized_diagnostic
RED reportado: red42-keyword · 2026-10-11T21:28:22.293025+00:00 · casos fallidos 4: test_root_seams_accept_deployer_authority_keyword[_issue_acquisition_admission]; test_root_seams_accept_deployer_authority_keyword[_revoke_deployer_authority]; test_root_seams_accept_deployer_authority_keyword[_close_deployer_authority]; test_root_seams_accept_deployer_authority_keyword[_identity_info]


## Revisión de dos lentes — intento 1: T05/K4a-core — cuatroImportantconfirmados — 2026-10-11T22:17:27.280236+00:00

FULL30A(5common+18K4a+7pares)/18B: A01guard04/05/07/11REDdummy_getattrsin callbacks, A02DTOguards antesREDsanitization; B01ValueErrorA4TRUEoutputdiscardspermitefalseknown/free, B02KernelDomainpoisonescapeKernelMemoryErrorallocatevsIdentityErrorissue. ROOTreproduce2CPUactualB01+ASTactualB02sinNativegrant/SDK y46pinssame. [Informe](testing/t05/storage-journal-principal-k4a-core-review1-2026-10-12.md). 0Critical4Important0Minor;AconformidadacotadaB. FIX1fresh6filesprivados, guardsborradocompleto/reescritratrasmonofocalREDcausal, custodyunknownretieneoutputsinfree/retry/reset/sibling,typedboundaryfailure;nativecutnuevoROOTQApendiente. Source85328historical/164CPU/ownNactual/whole80 noCAS niQCfullporverdeestrecho. K2owner/pins realesno existen/failclosed; restantesgatesT05/M1/store/ext4/production pendientes. Uso realnull.


## T05/K4a núcleo FIX1: prueba nativa actual y revisión2 preparada — 2026-10-12T04:15:14.634414+00:00

ROOT1734payload/40readonly/78RED causales/268CPU verificados, fuentea2eb1c3f y5pins actuales. Ownnative3hijos: normal66calls6closes ycuts postTRUEValueError/IdentityError retienenframe131328/preimage/raw/error/backing hastaREAP,0close/freeenunknown; los3PIDsretirados/ausentes. UniónofficialCPU+nativemismoSHAwholelines86,8367/96,1456/93,2203%,linesbranches83,8060/94,1374/91,4286%,0omit/excl. CandidatoNOQA/NOcanon/T05 abierto. Revisión2FULL30A/18B+4gapsactuales; K2/K4b/G1/store/ext4/lifecycle/E2E pendientes.


## Revisión de dos lentes — intento2 K4a core: FIX2 liberado — 2026-10-12T04:25:43.072099+00:00

FULL30A18Bconservado, A01/A02/B01/B02corregidos; nuevosB03mismosemanticobjantescleanupdejalive/siblingyB04pierdeprimaryeninterrupción, ROOT3CPUprobesactualesconfirmadossinSDK/grant. 0Critical2Importantnuevos0Minor. [Informe](testing/t05/storage-journal-principal-k4a-core-review2-2026-10-12.md). FIX2fresh2fuentesprivadas,44readonly; REDcausal→rewrite→nativeROOTnuevoSHA→review3→QAantesCAS. T05/M1abiertos/fullscopependiente.


## T05/K4a núcleo FIX2: prueba nativa actual y revisión3 preparada — 2026-10-12T08:33:00.366342+00:00

ROOT303payload/44readonly/25RED causales/293CPU verificados, fuente0cf68907/test34aeb06f y4pins actuales; original268preservado. Ownnative13hijos: normal66calls6closes,knownrejectrevoked/charge0 ycuts postTRUE2/cleanup9antesdespuésrevocar retienenframe131328/preimage/raw/error/backing hastaREAP,0close/freeenunknown; los13PIDsretirados/ausentes. UniónofficialCPU+nativemismoSHAwholelines88,0402/96,1456/93,2203%,linesbranches85,1064/94,1374/91,4286%,0omit/excl. CandidatoNOQA/NOcanon/T05 abierto. Revisión3FULL30A/18B+6gapshistory; K2/K4b/G1/store/ext4/lifecycle/E2E pendientes.


## K4a review3 — lenteA limpia yBfreshen curso — 2026-10-12T08:41:58.562155+00:00

A3FULL30A/18Bconsiderados/6gapsconservados0gapsA;CPUpropio293PASS12deselected/46pins/25causalREDvalidados. Native13actualROOTsameSHA sólo leído. B3freshse despachóalterminarA3 trasrechazos previosagentthreadlimit; todavíaNOQA/NOcanonT05abierto.


## Revisión de dos lentes — intento3 K4a núcleo: A/B sin gaps, QA liberada — 2026-10-12T08:47:08.949234+00:00

FULL30A18B6gapsconservados,A01A02B01B02corregidosR2/B03B04corregidosR3. AmbaslentesCPUpropio293PASS12deselect/46pinsstable,13ownnativeROOTcurrentSHA leído. [Informe](testing/t05/storage-journal-principal-k4a-core-review3-2026-10-12.md). C/Dauto false, QAindependienteactual46frozenpinsbeforeCAS6sources; fullK4a/T05/M1NOcerrado.


## T05 K4a núcleo — componente adoptado después QA independiente — 2026-10-12T09:09:42.011549+00:00

ROOT288payload/46pins/preimages/imports484Win479Linux/JUnit/rawcov/current13ownnativeCIMnonce/reaps auditados,source6SHAexact. QAWin293P0skip12deselect;Linux290P3WinAMD64skip12deselect+2actualplatformguards,containerownretired. OfficialQAWindowsCPU+13ROOTnative same6SHAwhole3line88,0402/96,1456/93,2203 andlinebranch85,1064/94,1374/91,4286>=80noomitexcl,Ruff/format/helper0. FULL30A18B6historygapsR3clean. CAS6sources0cf6/34ae/6c1c/85a9/c60a/1f9b accepted; T05M1openK2real/G1K3K4bK5storeext4controllerlifecycleE2Emanualpending. [QA vigente](testing/t05/storage-journal-principal-k4a-core-current-qa-2026-10-12.md). Uso realnull.


## T05 K2 runtime — implementación liberada tras K4a núcleo aceptado — 2026-10-12T09:15:26.255923+00:00

K4anúcleocanon0cf6/34ae/IO6c1c/ABI85a9 liberado trasQAactualWin293/Linux290+13ownnative; nofullK4aclaim. K2O1contratoaceptado/K4aownerpin handshake realaquí, 8ownedprivados2new+6baseline,CPUbackendnominal separado/NOFakeNativegrants. Definir owner,facadeABI,admissionpins bajo boundary-owner-session-context; TDD18criteriosK2yK4a08/13/14/18gates. ActorNO SDK/native/fileACL/DB/GPU; ROOTnativoprivatefiles propio sóloafterfreeze/audit, CREATEreal sóloK4bparentadmissionauthentic pendiente/failclosed. FULLK2norma+K4apinCPU/native implementation no contrato reducido. R3K4acausalgreenspreservadossamecurrentnorm; sourcefutureSHAfullcoverage/ownnativefreshreviewQAantesCAS8. T05M1abiertosfullchainstoreext4controllerlifecycleE2E/manuales. Uso realnull.


## T-05/K2 — creación nativa verificada y RED previo del pin — 2026-10-12T11:03:23.662597+00:00

ROOT auditó el checkpoint03 inmutable (52 SHA, stat sin reparse y AST). Fuente de adquisición c5039316; identidad f8e49b30; manifest2c77886e. Ejecución real del propietario: GREEN, 17 comprobaciones de capacidad nominal, registro, admisión, identidad y control propios. Frame preregistrado por API cerrada del propietario y lease kernel real: 11 comprobaciones, antes de ENTRY.

RED: `_pin_current_acquisition_admission` falló con `IdentityError: ADMISSION_REQUIRED/pin` en el stub real, con issuer K4a registrado y propietario Windows reales · 2026-10-12T11:03:23.662597+00:00. No se sustituyeron capacidades ni observaciones por dobles. Después del RED, ROOT autoriza implementar el pin nativo completo; no se atribuye este resultado a fuentes posteriores.

Hijo propio 39952: READY/RUN/RESULT conservado mientras seguía vivo/REAP_ACK/exit0/reaped y ausencia CIM contemporánea. Owner y autoridad cerrados; workspace [0,0,0], sesiones vivas0, tokens operativos0, poison false; VirtualAlloc132095 y VirtualFree de base original reales. No se consultará ese PID histórico. El camino auditado no invocó backend K2 ni archivos/ACL/GPU/servicios; la ausencia de calls K2 procede del AST de ese camino, no de un SDK trace inexistente.

Recibo: `.cache/dev-cycle/m1/storage-journal-k2-owner-pin-native-red-root-20261012/ROOT-native-pin-RED.receipt.json`; conserva audit, argv/UTC/exit, raw stdout/stderr, recibo del hijo y prueba posterior de ausencia. Pin/complete/abort, final SHA GREEN, revisión fresca, QA independiente y cobertura whole siguen pendientes. T-05 y M1 abiertos; ninguna aceptación de almacenamiento integral ni actualización de checkbox.


## T-05/K2 — pin previo nativo GREEN y RED de abort/guard complete — 2026-10-12T11:14:35.734024+00:00

ROOT auditó el checkpoint05 inmutable: manifest43079008,52payloads/42readonly; adquisición6313148e, identidad863b9061. En dos procesos propios, las factories reales pasaron17comprobaciones, la preregistración11 y el pin previo10: issuer K4a nominal, observación propia registrada, owner/frame/kernel lease reales, session lock retenido y reserva de cuota1/2048. Ninguna observación o capability nativa simulada.

RED: `_abort_acquisition_admission_pin` falló con `IdentityError: ADMISSION_REQUIRED/complete` en el stub real sobre pin activo y target RESERVED legítimo antes de ENTRY · 2026-10-12T11:14:35.734024+00:00. Autoriza implementar abort pre-ENTRY.

RED: `_complete_acquisition_admission_pin` devolvió `IdentityError: ADMISSION_REQUIRED/complete` donde el guard de un target todavía RESERVED debe rechazar `CAPABILITY_INVALID/complete` sin nuevas queries · 2026-10-12T11:14:35.734024+00:00. Autoriza implementar ese guard; NO acredita post-backend ni un complete positivo. El positivo real/postcheck exige una operación cerrada real futura, sin falsificar phase o outputs. Esta precisión proviene de la auditoría ROOT y la aclaración expresa del implementador antes de ejecutar.

Ambos resultados retuvieron pin activo1, frame/control y workspace [1,131584,132095], session lock y referencias hasta REAP_ACK. Owner/authority close UNKNOWN; cleanup local conocido FALSE. No se borró el registry ni se llamó VirtualFree para fingir cierre: una VirtualAlloc132095 real seguía custodiada. Token calls operativos0. Los dos hijos propios fueron realmente reaped, exit0 y CIM ausente inmediatamente. La retirada del proceso no se llama cierre local conocido; esos PIDs históricos no se volverán a consultar.

Recibo `.cache/dev-cycle/m1/storage-journal-k2-pin-terminal-native-red-root-20261012/ROOT-native-terminal-RED.receipt.json`; subdirs pin-abort y pin-complete conservan raws/argv/UTC/exit/receipts/ausencia. Prueba sin K2 backend ni archivos por call-path auditado, no por trace SDK inventado. Metadato pin_stub heredado del03 sigue histórico y no describe el05: stubs terminales acreditados por AST. Freeze04 incompleto por KeyError de preparación conservado sin ejecución ni manifest;05 fresh no lo sobrescribe. Final-SHA GREEN/revisión/QA/cobertura whole y fullT05/M1 siguen pendientes, sin actualización de checkbox.


## T-05/K2 — aborto nativo GREEN y RED del cierre tras pin terminal — 2026-10-12T11:21:41.154618+00:00

ROOT ejecutó checkpoint06 inmutable manifest0cab3fb7/52payloads/42readonly tras auditar los cambios exactos frente al05. Dos hijos propios comprobaron Nativefactory17 + frame11 + pinpre10 + abort5 GREEN reales. Abort se repite sin nuevas queries, conserva pin aborted registrado y reserva lifetime1, y libera su lease de session. Complete sobre RESERVED devuelve CAPABILITY_INVALID/complete sin queries y deja el pin active hasta abort: guard GREEN, no post-backend positivo. Native postcheck RETURNED aún es stub NATIVE_POSTCHECK_REQUIRED.

RED: `_close_deployer_authority` devolvió outcome `unknown` después de abort real y owner close `closed`, donde el contrato exige `closed` para summaries terminales · 2026-10-12T11:21:41.154618+00:00. El handler sigue AST exacto del core aceptado: su `if session.pins` rechaza el pin terminal conservado. Pin active0, owner inflight0/controlNone, kernel poisonfalse y session state distinto de unknown descartan las otras causas del guard; no se vació el registry ni se rebajó cuota para pasar.

ROOT autoriza ahora modificar ese handler para consultar summaries terminales de owners/pins bajo boundary/session sin adquirir owner lock desde session, preservando historial y lifetimequota. Dos propias creaciones29088/33300: READY/RUN/RESULT vivo/REAP_ACK/exit0/reaped/CIM ausente inmediatamente. Cleanup local del workspace conocido FALSE; VM [1,131584,132095] retenida hasta reap, una VirtualAlloc real sin VirtualFree antes del retiroSO. Token operativo0. No se reconsultarán esos PIDs históricos ni se atribuirá la evidencia a fuentes posteriores.

Recibo `.cache/dev-cycle/m1/storage-journal-k2-pin-close-native-red-root-20261012/ROOT-native-close-RED.receipt.json`, raws/argv/UTC/exit/receipts/ausencia por pin-abort y pin-complete. Ningún K2 backend/archivo/ACL/GPU/servicio por este camino auditado; no SDK trace inventado. Full finalSHA GREEN, post-backend real, review/QA/cobertura whole y T05/M1 permanecen abiertos; sin checkboxes cerrados. ROOT decidió seam CPU explícito bind para pruebas de pipeline con CpuAdmission nominal y source cpu_double, sin hacerlo autoridad nativa.


## T-05/K2 — validación backend y postcheck sobre locator Windows real — 2026-10-12T12:22:00.264135+00:00

RED: `_validate_acquisition_backend_pin` falló con `NotImplementedError: NATIVE_BACKEND_PIN_REQUIRED` en su stub real después de facade locator, frame preregistrado, prepin K4a real y ENTRY desde código cerrado · 2026-10-12T12:22:00.264135+00:00. ROOT07 verificó19checks y SDKsubcalls0, con primary fuerte retenido y public RESOURCE_UNKNOWN/locate. Autoriza wiringvalidator nominal despuésRED; no NameError ni fakeframes.

RED: `_complete_acquisition_admission_pin` falló con `NotImplementedError: NATIVE_POSTCHECK_REQUIRED` tras operación locator SDK real y facade RETURNED real · 2026-10-12T12:22:00.264135+00:00. ROOT08 verificó20checks,7SDKreadonly ACK, LocatorCompletion nominal successTrue; ninguna phase falsificada. GetVolumePathNameW/GetDriveTypeW/GetVolumeNameForVolumeMountPointW y4QueryDosDeviceW, sobre snapshotpropio. No NtCreateFile/fileopen/SD/fileACL/foreignprocess/GPU/services. Autoriza postcheck despuésRED, sin atribuir a nuevosSHAs.

Los propios hijos07/08 se mantuvieron vivos hasta RESULT persistido/CIM, REAP_ACK, exit0/reaped/ausencia CIM contemporánea. Contexto unknown/poison y pin/frame/buffers/workspace custodiados hasta retiroSO; cleanupLOCALknownFALSE. No se reconsultarán PIDs históricos. El08 verifica records/secuencia/phases/typedreturn durantevida, pero NO exporta todos los scalars/buffers SDK después muerte: no claimtracefull ni cobertura oficial. Recibos storage-journal-k2-backend-pin-native-red-root-20261012/ROOT-native-backend-pin-RED.receipt.json y storage-journal-k2-locator-postcheck-native-red-root-20261012/ROOT-native-postcheck-RED.receipt.json, audit/argv/raw/reap. Checkpoints52pinsafterigual/42readonly, inmutables. CódigoCPU posterior647PASS/14deselected reportadoactor, ABI/identity siguen bajo80CPU; finalSHANativeGREEN+rawcoverageunión/RQA pendientes. FullK2/T05/M1 sin cierre ni checkbox.


## T-05 K2 checkpoint09 — primer GREEN nativo readonly/pre-post/cleanup conocido — 2026-10-12T12:59:31.332333+00:00

ROOT auditó y ejecutó09 fuente-freeze2047613bfe4bd047d363d98a23f2049e219e4cd149359b773153b9d4b0b007cb;52payloads/42readonly exactos. Padrece84c7eb/hijofd169c46 gestionados-B/nonceREADY-RUN-RESULT-REAP_ACK/CIM whileheld/reap/ausenciapropia contemporánea.17factory/20locator-prebackend-postACKcompacción/4close todosGREEN; issuer/admission/owner ydosobservaciones efectivas reales distintas, mismo principal/group/tokenstamp, pincompletedterminal/cuotalifetime1/repeatsinqueries, frameACKcompactado conservandoidentidad/control. SieteSDKreadonly volumenlocatordesnapshotpropio, ningúnFILEopen/NtCreateFile/CREATE/SD/ACL. Observer sys.trace exclusivamentelectura guarda scalars/subcallordinal/preimages/outputranges/rawhex genuinos antescompaction: NO coberturaoficial/union. Cierreowner/authorityclosed, VirtualAlloc132095→VirtualFreebaseoriginalsuccess,workspace[0,0,0]/operationaltokens0/sessions0/poisonfalse. CleanupLOCALconocido real, no mera muerteSO. PropioPID25160 retiradoyCIMausenteentonces, no reconsultarPIDhistórico. Recibo `.cache/dev-cycle/m1/storage-journal-k2-locator-postcheck-native-green-root-20261012/ROOT-native-postcheck-GREEN.receipt.json` SHA97b86691f82b2e03fb8279451198e5aeca1ddee67d370013e666f5ad017f2003, argv/raw/actualchildreceipt conservados,52pinsafterequal.

ROOT ACKliberó freezeactualpara8ownedCPU;09 y08inmutables. Noatribución alcodeCPU posterior ni cierre18criterios: OPEN/CREATE/K4b/SD/sharing/closeprincipalchanged/argumentosordinalSDK/offsetL+7/carreraThreads/finalsameSHAofficialrawcoveragewhole≥80/freshreviewQA/CAS/fullK2/T05/M1 pendientes. Hipótesiserror997 descartadaporactor trasverificar guardactual/pruebaexistente, sinfixciego. Pruebas nuevasCPUoffset/concurrency se atribuirán sólo a sus propias preimágenes; no Nativeauthorityfabricada. ObjetivoM0–M5activo/ningúnhitocompleto/IAactualnull.


## T-05 K2 — ROOT Native10 y unión oficial de cobertura — 2026-10-12T14:08:57.345895+00:00

Checkpoint10 ff92ea4a9733ad03ccf7f58d1812d22d53049ccbcd4ed54cd01d0f4ffd1e6d33: ROOT auditó52payloads/42readonly y los cambios AST09→10; ejecutó proceso propio gestionado directo con nonce, READY/RUN/RESULT/REAP_ACK, CIM en vida, reap por handle de creación y ausencia propia contemporánea.17+20+4GREEN, siete SDK readonly sobre el locator de snapshot propio, cero FILE; cleanup local conocido, VirtualFree original exitoso, poisonfalse y recursos operativos cero. Perfil observador readonly restaurado; Coverage7.16.2 empezó antes de importar runtime y conservó raw propio real. No reconsultar el PID histórico. Recibo .cache/dev-cycle/m1/storage-journal-k2-locator-postcheck-native-coverage-root-20261012/ROOT-native-postcheck-GREEN.receipt.json SHA813a778a2e4974d3b383d9b4dfda974e4ea0ad1353acc48af9220a79003f86b6.

ROOT combinó raw oficial CPU717PASS/16deselected y Native10 únicamente después de verificar las ocho SHA idénticas; PathAliases oficial sólo relocaliza actor/snapshot→checkpoint10/snapshot, cero excluidos y cero partial-exclusions. Whole acquisition91.98%líneas/81.85%ramas/89.79%total e IO96.19/86.92/94.19 pasan; ABI65.17/61.11/64.27 e identity84.32/72.54/81.14 no pasan80. Sin medias, AST recompilado ni crédito de otras SHA históricas. Receipt .cache/dev-cycle/m1/storage-journal-k2-locator-postcheck-native-coverage-root-20261012/combined/ROOT-union-coverage.receipt.json SHAb5d97d39d5f36afbb6f7370bbed9bdc9140f9c6c8260d86d467923064f88ba7d. Primer assert ROOT de stdout falló antes de combinar porque el raw PowerShell tiene BOM UTF16; se preservó y se decodificó sólo para examinar el log, sin normalizar fuente/hash.

ACK10 autoriza volver a editar ocho fuentes privadas;10 permanece inmutable. Propiedades directas del schema sólo stub importable→RED funcional→derivadas sin nueva autoridad. Hacen falta más recorridos Native oficiales para ABI/identity, OPEN/CREATE/K4b/descriptor/error-cuts y todos18criterios; revisión fresca/QA/CAS/finalSHA pendientes, T05/M1 abiertos.


## T-05 K2 — Native11/12/14 y cobertura oficial — 2026-10-12T15:31:21.635456+00:00

ROOT11 descriptor propio:17factory+28descriptor+4knowncloseGREEN; CPU83 722PASS16deselected, misma8SHA. ROOT12 lectura metadata exacta snapshot/ancestros/volume GUID, FILE_OPENreadonly/CandidateReadOnly:17factory+28descriptor+12open+4knowncloseGREEN,13opens y13closes reales, cero escritura/CREATE/ACL de objeto, cierre local conocido y VirtualFreeoriginal. ROOT14E1/E2/E3: cada17factory+9fault+4unknowncleanupGREEN, una interrupción sólo tras retorno SDKreal, cero errores de observador, ceroFILE. UNKNOWN retiene recursos locales hasta reap propio del proceso por handle de creación; CIM ausencia contemporánea registrada. No se declara cleanup local ni cambio de principal físico. Native13 anterior fallóexit4 antes del sitio previsto:0fired/0captured; causaDTO inferida del código, no traceback AttributeError exportado. Recibos ROOT-native13-failure-preserved.receipt.json preservan fallos; no se reejecutaron ni reconsultaron PIDs históricos.

Unión oficial Coverage7.16.2 CPU83+Native11/12/14 sólo8SHA iguales y PathAliases oficial, módulos enteros0excluidos, sin AST ni Native13 fallido: ABI87.19líneas/73.02ramas/84.06total e identity85.83/75.20/82.96 aún fallan80; acquisition93.30/83.90/91.29 e IO97.03/86.92/94.85 pasan. Recibo .cache/dev-cycle/m1/storage-journal-k2-native11-12-14-union-root-20261012/ROOT-union-coverage.receipt.json SHAf4812046e4204c20f42fd403acbedcdc5c82a64352cc6264b52a11f6922843cd incluye missinglines/branches. Todos18criterios/K4bCREATE/G1/K5/QA/revisión/CAS y T05/M1 pendientes.


## T-05 K2 — calificación de atribución AST en cobertura histórica — 2026-10-12T15:41:24.680041+00:00

ROOT comprobó en freeze11 tres exec(compile(tree, inspect.getsourcefile(m),...)) del test identity líneas707/1100/1479. Los codeobjects AST usan filenameoriginal y pueden ser atribuidos al módulo original porCoverage, de modo que AST_recompile_credit=False del recibo unión CPU83+Native11/12/14 NO queda demostrado paraCPU83. Se conserva raw y matemáticas originales, pero se retira todo crédito formal de gatewhole de esa unión hasta auditoría completa de filenames y nuevaCPUlimpia. No se cambian bytes históricos ni se restan arcos manualmente. Recibo .cache/dev-cycle/k2-ast-qualification-protocol-green-progress-root-20261012/ROOT-coverage-qualification.receipt.json. Actor audita todoscompile/exec, cambia sólo filenamesAST a simbólicos<CPU-AST> preservandoaserciones, añade casos puros handleroriginal sin grantsNative; nuevaCPU+NativeROOT con8SHA actuales requeridos. NativeSDK11/12/14 propios permanece evidencia de sus criterios reales sin que valide elgatewhole. No admitir cambio guards/issuer/caps ni exclusiones.


## T-05 K2 — guard87 y medición limpia15 real — 2026-10-12T16:06:50.035098+00:00

RED: ENTRYboundCPU callbacklocate real antesretorno y RESERVEDboundCPU completaban incorrectamente: dos monofocales DIDNOTRAISE/87-RED0/1 causales preservados. Principal-design305 y acquisition-design419 exigenpinpre→unafrontera→CompleteQpost; ROOTeligió boundexactCpuAdmission phaseRETURNED, unboundRESERVED mecánicaCPU histórica preservada/noauthorityNative. Guardmínimoidentity4líneas antesquery;3GREEN ENTRY/RESERVEDrechazanCAPINVALIDsinpostqueries yRETURNEDdespuéscallbackrealcompleta. Nativecompletebodyliteral sin cambio, noSourceNativegrantCPU.

Se corrigieron3compilefilenameASToriginal a simbólicos<CPU-AST>, controlsemántico3PASSantes/después; audittodos24py×2versiones/12sites,current0original-dynamic conplantillas simbólicas demostradas. RAWCPU83antiguo siguecalificado sincrédito. ROOT15 capturóCPUoficialnuevo en freezeinmutable15:762PASS16deselected, source8SHApre/post reales, Coverage7.16.2 antesimports, toda configuraciónsinexcl/omit/partial/tempspropios. PreflightROOT inicial clasificador rechazó filename simbólico concatenado<CPU-SYNTHETIC>; fallóantesarea/runner/SDK, se corrigió sóloharness. Recibo .cache/dev-cycle/m1/storage-journal-k2-cpu15-clean-root-20261012/ROOT-CPU-clean.receipt.json SHA7e07405c25900a0d8df966e24b8fe9190e9084dac331d2647f0fbaf51bb27efd. ROOTNative15normal+3faults mismos8SHA actuales:normal13opens13closesreadonly/knownlocal;E1E2E3unointerruptafterSDKreal,UNKNOWNlocal hastaownOSreap+CIMausencia, noquerieshistóricos.52payloads42ROiguales/harnessbytes12normal14faultsame.

Unión oficialCPUROOT15+Native15clean, NO historical83/11/12/14/failed13/ASToriginalcredit, módulosenteros0excl:ABI88.99L79.365B86.865total requiere1rama adicional;identity87.045L77.869B84.569total requiere11ramas;acquisition93.30L83.904B91.295total eIO97.034L86.923B94.850total pasan. Recibo .cache/dev-cycle/m1/storage-journal-k2-native15-clean-union-root-20261012/ROOT-union-coverage.receipt.json SHA862834939348383a6ee76c1815a59be4a967a0e81a80d04ce5fa686438301360. ACK15libera8mutable para casos funcionalespuros/guardrealCPUobjects sinmintsNative; nuevasfuentes necesitanfreshCPU+NativeROOTmatching. Gates18K4b/G1/K5/reviewQA/CAS/T05/M1abiertos.


## T-05 K2 — ROOT17 y revisión de dos lentes, intento 1 — 2026-10-12T16:54:04.001126+00:00

ROOT ejecutó 776 PASS / 16 deselected CPU con ocho SHA PRE/POST iguales; cuatro pruebas nativas propias ROOT17 verdes. Unión oficial Coverage7.16.2, módulos enteros sin exclusiones: ABI90.7865% líneas/80.9524% ramas/88.6165% total; acquisition93.3023/83.9041/91.2948; identity87.9545/80.12295081967213/85.8407; IO97.0339/86.9231/94.8505. Gate80 verde en cada dimensión de cada módulo, sin redondear ni crédito CPU83/ASTfilenameoriginal/histórico11–14/failed13. Recibo: .cache/dev-cycle/m1/storage-journal-k2-native17-clean-union-root-20261012/ROOT-union-coverage.receipt.json.

ROOT auditó los 3496 payloads del inventario93; misma fuente8 actual. Revisión1 privada component-review1 preparada:51pins/7ficheros modificados/alcance0avisos/C-Dfalse. LenteA fresca en curso, B pendiente de plaza; no cierre T05/M1. Mantener los18criterios y K4b/G1/CREATE/SDCREATE/sharing/K5positivo pendientes. Actor entrega soporte final sin modificar fuentes17. Incidente89metadata restaurado byteexact15 por ROOT a26fc827/6161B;91preserva preparación16 f47a0c, inventario91 anterior alrestore calificado, sin alterar raw/fuentes ni reconsultar PID histórico.


## T-05 K2 — revisión de dos lentes, intento1: cuatro Important — 2026-10-12T17:07:38.303669+00:00

FreshA1 FULL18+6,0Critical/2Important/0Minor: A01 faltan bordes UTF16 ASCII/astral510B vs512 y locator16383/16384 con componentes válidos; actual negativo excesivo falla antes por componente. A02 falta requestedporbacking131071fit/131079reject. Sondas propias confirman actualcomportamiento correcto, no subsanan testcontractual ausente. CPU776PASS16desel24.83s/51pinsintactos. FreshB1 FULLcriterios,0Critical/2Important/0Minor: B01 NOT_FOUND conocido devuelvehandle/inflight pero retienearenanombre, seisfallos pool2→8 y séptimoACQUISITION_LIMIT; B02 closeparentpinneado revoca sóloancestro, descendantPARENT_EXISTING aún publicaREADcandidate. Probes propios37CPU y51pinsintactos. Informes lens-a1-root.md/lens-b1-root.md en component-review1.

ROOT verificó código/normativa y acepta cuatrogaps, sinrebate. FIX1 implementer fresco fix_m1_k2_component_current_1 ennamespace storage-journal-k2-component-fix1-root-20261012:2ownedacquisition/test,48ROincluyendootros6candidatos17, decisiónROOT/PriorFULL18+4gaps. B01/B02 testREDcausal antesfix/GREEN; A01/A02 controlesyaGREEN sininventarRED. GuardasNative/custodiaUNKNOWN/locks/pins/counters intactas; sin newK4b/G1/K5grant. Nuevasfuentes requierenCPUmatching+4ROOTNative oficiales sinoldcredits/review2/QA/CAS. FullT05 abierto.

Incidente B1: selector inicialpytest -m intentóexcluir skipifaliasNative y salida parcial≈197/792, sessionid perdidoal reducir.output; sincréditoCPU/Native/cobertura niPIDhistóricoquery ni suite repetida. Root17independiente no afectado. Declaraciónenreport conservada; nuevasselecciones -k notnativeexactas.


## T-05 K2 — revisión de dos lentes, intentos 2 y 3; QA del componente — 2026-10-12T18:14:12.908507+00:00

FIX1 corrigió revocación del subárbol y devolvió las cargas tras errores reconocidos, con bordes UTF16/locator/requested comprobados. Revisión2 confirmó A01/A02/B02, pero B01 conservaba siete buffers originales (1225 bytes) por before_arena dentro del traceback. ROOT verificó y aceptó el defecto. RED: cuatro variantes fallaron con unaccounted_original_buffers=7/unaccounted_bytes=1225/charged=2; raw, preimagen y UTC preservados. FIX2 libera esa referencia únicamente tras ACK reconocido; cuatro GREEN y dos controles de ACK incierto preservan custodia. Fuentes actuales acquisition e4a91032 y test16e0a06c.

ROOT independiente:792PASS/16deselected CPU y cuatro pruebas Native propias actuales, ocho SHA iguales. Normal13 aperturas/13cierres; E1–E3 conservan UNKNOWN local hasta reap propio. Unión oficial Coverage7.16.2 sin exclusiones ni crédito histórico: ABI90.7865/80.9524/88.6165; acquisition93.5542/83.7748/91.4729;identity87.9545/80.1230/85.8407;IO97.0339/86.9231/94.8505 (líneas/ramas/total). Cada dimensión pasa80 sin redondear.

Revisión3 A/B con contexto fresco:0Critical/0Important/0Minor; tablas18criterios y seis comunes conservadas en component-review3/lens-a3-root.md y lens-b3-root.md,51pins sin drift. Los cuatro hallazgos anteriores quedan corregidos; integración física completa sigue no verificable. QA independiente despachada en storage-journal-k2-component-qa1-root-20261012, sólo componente sinUI, no el hito conUI. QA/CAS aún pendientes. K4b/G1/CREATE/SDCREATE/sharing bilateral/K5positivo/concurrencia Native/T05/M1 abiertos. Ninguna tarea se cierra con estas pruebas parciales.


## T-05 K2 — QA verde y adopción del componente — 2026-10-12T18:22:20.684627+00:00

QA independiente792PASS16deselected, JUnit792nodos→qa-gateexit0(PYTESTCPUderived/noUI), PREPOSTFINAL51SHA iguales; cuatro Native ROOT actuales auditados y unión5 oficial recomputada idéntica, módulosenteros≥80L/B/total0excl. ROOT contrastó49payloadsentrega+290soportes y adoptó7ficheros modificados contra preimágenes exactas, dejando testIOsin cambio. Acquisitione4a91032/test16e0a06c y otras6fuentes coinciden conQA; informe público testing/t05/storage-journal-k2-runtime-qa-2026-10-12.md. Revisiones3FULLA/B0gaps. PDF6pageobjects/estructura válida, no texto/rasterlayoutinspeccionado. Adopción y copiasprevias en .cache/dev-cycle/m1/storage-journal-k2-component-acceptance-root-20261012. PublicaciónGitpendiente; sin cierreT05/M1 ni K4b/G1/CREATE/SDCREATE/sharing/K5positivo/concurrenciaNative/worker-manifest-ready-analysis-cleanup. IAactualNULL.


## T-05 K2 — publicación aislada — 2026-10-12T18:31:26.588311+00:00

Commit2d1c7207b81bbe5e991f6b5721c2785c66bbd9db publicado y remoto contrastado en m1/t-05-k2-adquisicion. Ochoarchivosallowlist:7fuentesmodificadasaceptadas+informeQA público. SharedHEAD603e7c83/rama m1/t-02-esquema/índicebyteexacto conservados. Recibo storage-journal-k2-component-git-root-20261012/ROOT-published-component.receipt.json. Sinmergeamain/T05M1pendientes. DospreflightROOT de adopción fallaron antes de área/canon por claves Coverageconbackslashyprefijosnapshot; tercero utiliza mappingexacto cuatrokeys normalizados contra qa/snapshot. Sóloharness corregido, raws/preimágenes conservados; no fallo de producto ni rerunQA.


## K3: diseño técnico O2 elegido — 2026-10-12T19:13:31.978219+00:00

ROOT eligió O2 bajo la delegación del propietario: módulo observation separado, adquisiciones y frames K2, arenas y pins K1, continuidad K4a y poison compartido. Diseño privado d0416ead y ADR0089propuesta a4cc0333 en storage-journal-k3-metadata-design-root-20261012; callingseams concretos,15/14/26queries,21entradasPREPOSTexactas. No código ni SDK ni adopción por arquitectura. Próximo preparar corte documental canónico con vínculos de spec/plan y cuatro diseños, revisiónA/B y QA antesreleaseTDD. Índice89 deberá splicearse contra versión vigente trasADR88, preservando sus filas. G1/K3/K4b/K5/store/bootstrap/fullT05M1 siguenpendientes; componenteK2yaaceptado/publicado2d1c7207noaprobaréstasporarrastre.


## T-05 — corte documental K3 O2 para revisión — 2026-10-12T19:27:45.516300+00:00

ROOT prepara diseño observation y ADR0089 con enlaces canónicos específicos de spec/plan y apéndices de kernel/acquisition/principal/store. O2 elegida bajo delegación del propietario; sólo prosa/config, TDD n/a. Cuerpos de los cuatro contratos preservados byte a byte. Índice ADR89 se inserta contra la versión vigente después de ADR88, sin sustituir su fila. Archivos declara módulo/test futuros antes del release; ningún código ni SDK ni autoridad Native ni cierre T05/M1 por esta preparación. Revisión A/B documental y QA pendientes, implementación no liberada. IA actual desconocida.


## Parada solicitada: K3 preparado para revisión — 2026-10-12T19:32:07.616370+00:00

El propietario pidió «acaba esta última prueba y para». No se despachan revisores ni se libera implementación nueva. El corte documental K3 O2 está preparado en `.cache/dev-cycle/m1/storage-journal-k3-document-review1-root-20261012/`: 9 documentos propuestos, 28 fuentes fijadas, scope sin fuera de alcance ni avisos y lentes C/D no aplicables. Spec/plan reciben vínculos específicos; los cuatro cuerpos previos se conservan íntegros; la fila ADR89 preserva ADR88 vigente. La propuesta permanece privada y pendiente de revisión A/B, QA y adopción ROOT. No SDK ni runtime K3. Los fallos de preparación por LF/CRLF y EOF están conservados y corregidos sólo en la propuesta. K2 continúa aceptado y publicado en2d1c7207. G1/K4b/K5/store/bootstrap y T05/M1 siguen abiertos.
