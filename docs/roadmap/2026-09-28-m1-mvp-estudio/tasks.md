---
generacion:
  fuente: estimado
verificacion: obligatoria
---

# Checklist de Tareas — M1 · MVP del estudio web (recortado)

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-28 · recortado 2026-10-22 ([ADR-0089](../../decisiones/ADR-0089-reencauce-tras-codex.md), [spec §Recorte](./spec.md#recorte-del-2026-10-22-adr-0089)) |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | [design.md](design.md) · [database-design.md](database-design.md) · [lyrics-contract-design.md](lyrics-contract-design.md) |
| **Historial** | [`../../archive/codex-2026-10/m1-tasks.md`](../../archive/codex-2026-10/m1-tasks.md): ledger completo con revisiones e intentos hasta 2026-10-12. Las evidencias crudas están en el commit `36d4e99` |

> **Ledger canónico.** Aquí solo va el estado, los criterios y la salida resumida de la Verificación. El diario de intentos y los recibos de revisión no entran (ADR-0089). Solo el orquestador actualiza este fichero.
>
> **Punto de partida (2026-10-22):** el árbol trae unas 23k líneas de server y 33k de tests escritas con Codex. Ninguna tarea está cerrada. Antes de dar nada por bueno, hay que revisarlo y recortarlo contra la spec recortada. **El camino mínimo no funciona hoy de punta a punta:** la publicación usa `renameat2(NOREPLACE)`, que falla sobre el bind de Docker Desktop (ADR-0069 → T-05).

### Línea base de tests (2026-10-22, Windows, `-m "not gpu"`, tras el reencauce)

| Área | Resultado |
|---|---|
| `packages/engine-contract` · `audio-post` · `weights` · `storage-guard` | 15 · 185 (9 skip) · 24 · 173 (42 skip) en verde |
| `apps/engines/common` · `mock` | 27 · 3 en verde |
| `apps/server/tests` | **2517 en verde · 4 fallos · 68 errores**, en 13 min. Todos los fallos y errores están en `test_worker_{native_custody,private_context_integration,actual_execution}.py`: exigen Linux real (`assert 'win32' == 'linux'`), la variable del arnés `CUSTODY_SOURCE_SHA256` o `renameat2` NOREPLACE. Se resuelven en **T-05** |
| `apps/web` (vitest) | 24 ficheros · 260 en verde |
| `tests/` | 518 en verde hasta `test_web_build_inputs.py`, que copia el árbol web y supera los 7 min. `test_web_tool_entrypoints.py` falla en `@swc/core` (binding nativo) en el entorno aislado. Ambos son de T-08 |
| `scripts/eval/tests` | 3 errores de recogida (`KeyError: STUDIO_CANONICAL_TEST_ROOT`, arnés del benchmark de M0/T-09) |

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Canceladas |
|------|------------|-------|----------|-----------|
| Fase 1 — Server base | 0 | 4 | 0% | 1 (T-00) |
| Fase 2 — Cola y post-proceso | 0 | 3 | 0% | 0 |
| Fase 3 — API | 0 | 1 | 0% | 0 |
| Fase 4 — Web | 0 | 7 | 0% | 1 (T-14) |
| Fase 5 — Pruebas y cierre | 1 | 3 | 33% | 0 |
| **TOTAL** | **1** | **18** | **6%** | **2** |

**Orden recomendado:**

1. T-05 (desbloquea el camino de punta a punta).
2. T-04, T-06 y T-07 con el mock.
3. T-08 a T-13 en la web.
4. T-15 en E2E.
5. T-16 con ACE-Step real, cuando M0/T-13 esté cerrado.

---

## Fase 1 — Server base

### T-00 — Apertura técnica condicionada (ADR-0037)
- **Descripción**: La sustituye ADR-0089: un hito activo a la vez. M1 se construye contra el mock y se acepta con ACE-Step real.
- **Estado**: cancelado
- **Dependencias**: ninguna
- **Verificación**: n/a (sustituida por ADR-0089).

### T-01 — Esqueleto del server: configuración, seguridad local y logs
- **Descripción**: FastAPI sin torch, `Settings`, validación de `Host`/`Origin`, `problem+json` y logs estructurados.
- **Estado**: en-revision
- **Dependencias**: ninguna
- **Archivos**: `apps/server/app/{main,settings,security,errors,logging}.py`
- **Verificación**: `uv run pytest apps/server/tests -k "security or settings or errors or health" -m "not gpu"` en verde · `curl -H "Host: evil" http://127.0.0.1:8000/health` → 403.

### T-02 — Esquema completo, migración inicial y FTS
- **Descripción**: Primera migración Alembic con el esquema de datos.md y FTS de canciones. El backup diario existe en el código, pero no bloquea el cierre.
- **Estado**: en-revision
- **Dependencias**: T-01
- **Archivos**: `apps/server/app/models/`, `apps/server/app/migrations/`, `apps/server/app/db.py`
- **Verificación**: `uv run pytest apps/server/tests -k "migration or schema or fts" -m "not gpu"` en verde.

### T-03 — Contratos exportados y parser de letras compartido
- **Descripción**: `openapi.json` y `engine-v1.json` exportados y comprobados en CI, y el parser de letras compartido server/web con `lyrics-cases.json`.
- **Estado**: en-revision
- **Dependencias**: T-01
- **Verificación**: `uv run scripts/export_contracts.py --check` sin diferencias · `uv run pytest apps/server/tests -k lyrics` y `pnpm --filter web test lyrics` en verde.

## Fase 2 — Cola y post-proceso

### T-04 — Cola de un carril: reintentos, cancelación y recuperación
- **Descripción**: **Recortado.** Un carril GPU y uno CPU, reintento `retryable` ×2, cancelación y recuperación al arrancar. Las dependencias entre jobs (análisis) quedan fuera.

  El mapa del 2026-10-22 dice qué está hecho y qué falta:
  - **Ya funciona:** los carriles (GPU 1, CPU 2), el retry ×2 del engine con la semilla congelada, la cancelación del engine y el reenvío del mismo attempt cuando el engine confirma que no lo tiene y no hay salida previa.
  - **Huecos:**
    - un `post.audio` interrumpido no tiene camino de vuelta;
    - dos `post.audio` interrumpidos bloquean para siempre el carril CPU;
    - un post interrumpido no se puede cancelar;
    - cancelar no limpia `data/tmp`;
    - un job GPU dudoso queda `interrupted` para siempre;
    - `reconcile_startup` no es idempotente (gap 6 de T-05).

  **Decisiones del propietario (2026-10-22):**
  - El post interrumpido se **reanuda** sobre la misma `cpu_execution`, sin migración (opción A, frente a B «ordinal 2 + migración» y C «fallar y regenerar la GPU»).
  - Un job GPU dudoso usa **reintento acotado**: si el engine confirma que no lo tiene, pasa a `failed` retryable y lo recoge el retry ×2.
- **Estado**: en-revision
- **Tipo**: backend
- **Dependencias**: T-02, T-05
- **Archivos**: `apps/server/app/queue/`, `apps/server/app/worker/execution.py`, `apps/server/app/worker/publications.py`, `apps/server/app/worker/audio_child.py` (salta las takes ya empaquetadas al reanudar: `resume-skip.json`), `apps/server/tests/test_dispatcher_*.py`, `apps/server/tests/test_queue_*.py`, `apps/server/tests/test_worker_*.py`
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → 0 failed, 0 errors. Antes hay que cargar el entorno con `source scripts/env.sh`.
  - Docker (orquestador):
    - `server` + `engine-mock` sobre `.cache/`; SIGKILL del server con el post a mitad y arranque de nuevo → el **mismo take llega a `ready`** sin intervención y `verify_manifest.py` da `all valid`.
    - Cancelar un post interrumpido → `cancelled` y sin `data/tmp/<attempt>`.
    - Tests de Linux real del worker en verde.

**Criterios de aceptación**
- [x] CA-1 (reanudar, opción A):
  - Tras un reinicio, un `post.audio` `interrupted` cuyo proceso anterior se **prueba** muerto (epoch de supervisor o arranque nuevo, sin ningún `owner` vivo) pasa la custodia de `unknown` a `confirmed`, transiciona `interrupted → prepared` con lease nuevo y se re-ejecuta desde el WAV crudo de `data/tmp`.
  - Las intents `reserved` se vuelven a procesar y las `prepared` se republican desde su staging, que T-05 conserva.
  - El take termina `ready` con su manifiesto válido.
  - Sin prueba de muerte, no se confirma nada y el post sigue `interrupted`.
  - No hay migración: solo transiciones que ya permiten los triggers de `cpu_publication_invariants.py`.
- [x] CA-2: el carril CPU no se bloquea. `claim_job` cuenta como ocupadas solo las ejecuciones vivas (no `interrupted` sin owner, ni borradas, ni de otro owner).
- [x] CA-3 (cancelar):
  - Un post `interrupted` tras un reinicio se puede cancelar y queda `cancelled`, con sus intents y su `cpu_execution` en estados finales válidos.
  - Cancelar cualquier job (engine o CPU) borra su `data/tmp/<attempt>` cuando ya no lo necesita ningún otro job (el WAV crudo lo usa el post, que depende de la generación). El borrado sigue las reglas de T-05: no sigue symlinks/junctions, se queda dentro de `data/` y los errores son eventos.
- [x] CA-4 (GPU dudoso): un job de engine en recuperación `uncertain`:
  - si el engine confirma que no lo tiene → `failed` con `retryable` y lo recoge el retry ×2 existente (attempt nuevo, misma semilla, respetando `max_attempts`);
  - si el engine no responde → sigue esperando como ahora.
- [x] CA-5 (gap 6): `reconcile_startup` es idempotente. Un segundo arranque sin cambios no incrementa `revision` ni reescribe filas ya `interrupted`.
- [x] CA-6: la suite de cola (`-k "queue or dispatcher or retry or recovery or cancel"`) y la del server completa siguen en verde.
- **Implementación** (2026-10-22, 3,05 h IA medidas). Commits `2917030` (GPU dudoso y borrado de `data/tmp` al cancelar) y `b613714` (reanudar `post.audio`).
  - **RED → GREEN por CA** (implementer):
    - CA-2: `test_ca2_*`, `assert False is True`.
    - CA-5: `test_ca5_reconcile_startup_is_idempotent`, `1 == 0`.
    - CA-4: `test_ca4_*`, `'interrupted' == 'failed'`.
    - CA-3: 6 tests de `sweep_cancelled` en rojo y `test_ca3_interrupted_post_can_be_cancelled`.
    - CA-1: 9 tests `test_ca1_*`, por falta de `resumable_jobs`/`claim_resume`.
  - **Prueba de muerte del proceso:** compara el `starttime` de `/proc/<leader>` con el `birth` guardado. En Windows, sin `/proc`, no prueba nada y la custodia sigue `unknown`.
  - **Suite completa del server en Windows** (implementer): `2570 passed, 75 skipped`, 0 failed, 0 errors. Focales comprobados por el orquestador: 63 passed. `ruff` limpio.
- **Verificación en Docker** (orquestador, 2026-10-22):
  - **Linux real:** resume_linux, resume, cancel_cleanup, gpu_doubt, los worker_* y los dispatcher cpu/recovery dan **92 passed, 5 skipped** (junctions). Los tests de cola necesitan que exista `.cache/dev-cycle/m1/t04-queue-tests` dentro de `/studio`.
  - **CA-1 de punta a punta:** SIGKILL con el `.pending-*` presente y arranque de nuevo → el **mismo take** pasa a `ready`, el post queda `succeeded` en la misma `cpu_execution` (ordinal 1, `finished/confirmed`) y la intent `committed`. `verify_manifest.py` da `all valid`.
  - **CA-3 de punta a punta:** `POST /api/jobs/<post>/cancel` con el post en curso → 202. Job, `cpu_execution` y take quedan `cancelled` (`confirmed`), sin `.pending`, con `_server_cpu/<exec>` y `_server_inputs/<exec>` borrados y sin el tmp crudo de la generación.
  - **Hallazgo H5 (anterior a T-04):** una generación **correcta** deja en `data/tmp` el `_server_inputs/<exec>/0.wav` (copia del WAV), `_server_cpu/<exec>/` con sus JSON, la salida `output-0.json` del attempt de `audio.beats` y directorios `_server_inputs/<hex>`. Es una fuga de disco que crece con cada canción.
- **Fix1** (2026-10-22, 4,87 h IA medidas). Commit `a1a7a8c`:
  - **I1:** los posts sin `cpu_execution` vuelven a `queued`, también sin backends.
  - **I2:** 13 tests de reanudación mixta (intent A `prepared` republicada desde el staging y B `reserved` reprocesada) con hash y `write_once` reales, y validación de `resume-skip.json` falsificado (`PROVENANCE_MISMATCH`).
  - **B1:** un único orden de locks, sin `_guard` dentro de la barrera.
  - **B2:** solo se invalida el feed si se escribe algo, con backoff de 5 s ante un rechazo.
  - **B3:** los owners vivos o retenidos ocupan carril.
  - **m1:** marca `launching` antes de lanzar el grupo. Un post muerto en esa ventana queda `interrupted` hasta intervención manual: es conservador a propósito.
  - **B4:** la muerte exige también que no quede ningún proceso del grupo o la sesión en `/proc`.
  - **D1:** `CancelSweeper` incremental.
  - **Tests:**
    - Suite completa del server en Windows (implementer): `2603 passed, 75 skipped`, 0 failed.
    - Focales (orquestador): 80 passed; `ruff` limpio.
    - **Docker, Linux real: 125 passed, 5 skipped** (junctions).
- **Verificación en Docker del fix1** (orquestador, 2026-10-22):
  - **CA-1:** SIGKILL a mitad del post y arranque de nuevo → el mismo take pasa a `ready`.
  - **CA-3 / I3 (cancelar un post interrumpido):** SIGKILL a mitad del post; con el server parado se marca `cancel_requested_at` (contenedor puntual) y se vuelve a arrancar. Resultado:
    - post `cancelled`;
    - `cpu_execution` `cancelled/confirmed`;
    - intent `cancelled`;
    - **no queda ningún fichero** de esa ejecución en `data/`;
    - sin `.pending-*`;
    - `verify_manifest.py` da `all valid`.
- **Fix2** (2026-10-22, 5,36 h IA medidas). Commit `a9fc73d`:
  - **N1:** si el lanzamiento falla sin hijo, se limpia la marca `launching`. Tras un reinicio, `launching` solo prueba la muerte si ningún proceso de `/proc` lleva el id de ejecución en su `cmdline`.
  - **N2:** reintento de los borrados fallidos.
  - **N3:** se limpia el `_server_cpu/<ULID>` huérfano.
  - **N4:** test `linux_real` de republicación de `prepared` sin simulaciones.
  - **N5:** backoff de las sondas y poda.
  - **Tests:**
    - El repro del revisor (`test_m1_stuck.py`) ahora cancela: `LIVE True ... cancelled`.
    - Focales (orquestador): 87 passed.
    - Suite completa del server (implementer): `2616 passed, 76 skipped`, 0 failed.
    - **Docker Linux: 139 passed, 5 skipped**, incluido el nuevo de N4.
  - **De punta a punta en Docker:** reanudar tras SIGKILL dio el take `ready` en 6 de 6 ejecuciones y una generación normal también; `verify_manifest.py`: `all valid`.
  - **Observado una vez de 6 (N6, Minor):** tras una reanudación quedó un `.pending-<exec>` (sin `worker.cleanup.failed` en las repeticiones). No se reproduce. Está acotado: la limpieza del siguiente arranque lo elimina.
- **QA** (2026-10-22, orquestador, modo sin UI acotado a T-04; mismo criterio que el propietario fijó para T-05):
  - `ledger-lint`: 0 incoherencias.
  - `coverage-check`: exit 0, 0 referencias rotas.
  - **`qa-gate.py`: exit 1** («sin resultados»). Las E2E que cubren T-04 (E2E-04 reintento, E2E-05 cancelar, E2E-06 recuperación) son de T-15.
  - T-04 queda `en-revision`, se integra en `main` y pasa a `completado` cuando T-15 las ejecute con `qa-gate` en verde.
  - Deuda abierta: N6 (`.pending` residual en 1 de 6 reanudaciones; lo elimina el siguiente arranque), N7 y B5 (con H5).
- **Changelog**: Si el server se reinicia a mitad de una canción, el post-proceso se reanuda solo hasta dejar el take listo. Los trabajos se pueden cancelar sin dejar restos, y la cola no se queda bloqueada.

### T-05 — Post-proceso y publicación sencilla de takes
- **Descripción**: **Rediseño (ADR-0089 §2).** Hoy la publicación final (`publications.py::rename_noreplace`) exige `renameat2(RENAME_NOREPLACE)`, que devuelve `EINVAL` sobre el bind 9p de Docker Desktop, y por eso ningún take llega a `ready` en el despliegue real. Se sustituye por una publicación sencilla:
  - el destino `data/songs/<song>/takes/<take_ulid>` es único por construcción;
  - se usa `renameat2` si el filesystem lo soporta y, si devuelve `EINVAL`/`ENOSYS`, comprobación de ausencia más `os.rename`;
  - la fila SQLite sigue siendo la autoridad;
  - al arrancar se limpian los staging huérfanos.

  Fuera de alcance: simplificar la custodia de procesos (`custody_*`, `pipe_protocol`), que funciona y no bloquea. `packages/storage-guard` se mantiene opcional (solo con `STUDIO_STORAGE_UUID`).
- **Estado**: en-revision
- **Tipo**: backend
- **Dependencias**: T-04
- **Archivos**: `apps/server/app/worker/publications.py`, `apps/server/app/worker/execution.py`, `apps/server/tests/test_worker_*.py`, `apps/server/tests/conftest.py` y `pytest.ini` (marcadores de CA-4), `apps/server/tests/fixtures/creative/fixture-index.json` (hash LF del esquema, `406f259`), `apps/server/app/logging.py` y `apps/server/app/queue/runtime.py` (eventos `worker.*` y logger del worker, fix2), `scripts/verify_manifest.py` y `packages/audio-post/tests/test_manifest_errors.py` (H2), `README.md` (aviso de WAL, H4)
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → **0 failed, 0 errors** (los tests Linux-only aparecen como `skipped` con motivo).
  - Docker: `docker compose run --rm server uv run pytest apps/server/tests -m "not gpu" -k "worker or publication"` en verde, incluidos los tests nativos Linux.
  - Punta a punta: `scripts/e2e_stack.py up` y una generación con `engine-mock` deja el take `ready` en `data/songs/` sobre el bind de Windows · `uv run scripts/verify_manifest.py data/songs/` en verde · `scripts/e2e_stack.py restart-server` a mitad del post-proceso no deja `.pending-*` huérfanos.

**Criterios de aceptación**
- [x] CA-1: la publicación funciona donde `renameat2(NOREPLACE)` devuelve `EINVAL`/`ENOSYS`, con un fallback de comprobación de ausencia más `rename`. Un test simula `EINVAL` y comprueba que el take se publica.
- [x] CA-2: se mantiene el no-clobber. Un destino ajeno existente (fichero, directorio o directorio vacío) se rechaza sin tocarlo, con y sin fallback, y el cross-device se rechaza antes del rename (los tests `test_native_noreplace_preserves_foreign_destination*` y `test_native_publication_rejects_cross_device_before_rename` pasan, adaptados si hace falta).
- [x] CA-3: al arrancar, se eliminan los directorios `takes/.pending-<execution>/` de las ejecuciones no confirmadas. *(Reducido el 2026-10-22: reencolar un `post.audio` interrumpido exige cambiar la máquina de estados (`claim_job` solo acepta `queued`/`attempt=0`, más `UNIQUE(job_id, ordinal)` y `UNIQUE(take_id)` en la intent). Ese trabajo pasa a **T-04**, que ya cubre «interrupted → reencolar».)*
- [x] CA-4: los tests que exigen Linux real o el arnés de custodia Windows de Codex (`CUSTODY_SOURCE_SHA256`) se marcan con un marcador explícito y se saltan con motivo cuando no aplican, en lugar de fallar o dar error.
- [x] CA-5: verificación de punta a punta en Docker con `engine-mock` (bloque **Verificación**). *(`verify_manifest.py` del host en verde tras fix3 y fix4.)*
- **RED → GREEN** (2026-10-22, implementer):
  - RED: `test_worker_publication_fallback.py` → 6 failed (`AttributeError: _native_noreplace`). GREEN: 6 passed.
  - RED: `test_worker_startup_staging.py::test_startup_removes_orphan_pending_staging` falló porque `.pending-<exec>` seguía existiendo. GREEN: con `test_dispatcher_cpu_worker.py`, 7 passed.
- **Verificación parcial** (Windows, 2026-10-22):
  - `uv run pytest apps/server/tests -m "not gpu"` → `1 failed, 2526 passed, 73 skipped in 708s`. El fallo era el hash CRLF del índice de fixtures creativo, corregido en `406f259`: `test_creative_contract_compatibility.py` da 69 passed.
  - Los 4 fallos y 68 errores del worker de la línea base pasan a `skipped` con motivo (`linux_real` / `custody_harness`).
  - **Pendiente:** la parte en Docker (los tests nativos de Linux de CA-2 y el recorrido de punta a punta de CA-5). Docker Desktop está parado.
- **Verificación en Docker** (2026-10-22, imagen `music-studio/server:m1-t01`, solo CPU):
  - **Linux real** (tests montados en la imagen, grupo dev instalado en el contenedor, ffmpeg fijado, `/proof` en tmpfs con un dispositivo distinto): `test_worker_{publication_fallback,startup_staging,private_context_integration,actual_execution}.py` y `test_dispatcher_cpu_worker.py` dan **47 passed, 3 skipped** (las junctions son de Windows). Se ejecutan de verdad el no-clobber nativo con `renameat2`, el cross-device y la ejecución real con ffmpeg (CA-2).
  - **De punta a punta** (`server` y `engine-mock` sobre el bind de Windows `.cache/e2e-t05*`):
    - `POST /api/generations` → 202 y take **`ready`**, con `master.flac`, `listen.mp3`, `peaks.json` y `manifest.json` en `data/songs/<song>/takes/<take>/`.
    - `audio_post.verify_manifest(manifest, "/", private_context_root="/data")` en el contenedor → `valid: True`.
    - SIGKILL del server en cuanto aparece el `.pending-*` (intent `reserved`) y arranque de nuevo: el staging se elimina (`worker.staging.removed` en `server.log`) y el post queda `interrupted`/`CPU_CUSTODY_UNKNOWN`, sin huérfanos. El reencolado es de T-04.
  - **Hallazgos de la prueba real:**
    - (H1) Si se omite `params.duration_s`, la generación se acepta, pero el post falla con `AUDIO_DURATION_MISSING`, y la web no envía `duration_s` → **T-07/T-09**.
    - (H2) `scripts/verify_manifest.py` resuelve las salidas respecto al directorio del manifiesto, pero los manifiestos del server usan rutas `data/...` → `OUTPUT_MISSING` → fix3.
    - (H3) Tras publicar con éxito queda un `.pending-<exec>` vacío hasta el siguiente arranque → fix3.
    - (H4) **Abrir `data/db/studio.sqlite` desde Windows mientras el contenedor lo usa en WAL sobre 9p borra el `-wal`/`-shm`, que el contenedor sigue usando, y se pierden escrituras.** Se reprodujo durante esta verificación, solo en `.cache`: la limpieza movió el take sin fila a `trash/orphans` y no se perdieron ficheros. → aviso en el README (fix3) y gotcha.
- **Fix3 + fix4** (2026-10-22, 2,3 h IA medidas). Commits `4f3d284` y `a8bff17`:
  - H2: `verify_manifest.py` autodetecta la raíz con `data/` y admite `--data-dir`.
  - H3: `rmdir` del `.pending-<exec>` vacío tras el commit final.
  - H4: aviso del WAL en el README.
  - **Comprobado por el orquestador:**
    - Docker Linux: **50 passed, 4 skipped**.
    - De punta a punta: take `ready` sin `.pending-*` residual.
    - SIGKILL a mitad: staging eliminado, sin papelera; el post queda `interrupted` (T-04).
    - `verify_manifest.py` sobre el take real: `all valid` con `--data-dir` del directorio aislado. *(Corregido en la revisión, intento 3, gap 4: la autodetección se comprobó con una **copia** del take en una estructura `<raíz>/data/`, no sobre el take en su sitio. Sin `--data-dir`, el take aislado da `PRIVATE_CONTEXT_INVALID`.)*
    - `test_manifest_errors.py` + `test_generate.py`: 109 passed.
    - Suite completa del server tras fix3 (informe del implementer): `2542 passed, 73 skipped`.
- **Fix5** (2026-10-22, 0,61 h IA medidas). Commit `5d989b4`; lo autoriza el propietario tras el 3.er intento:
  - `verify_manifest.py` deriva la raíz de datos del propio manifiesto, sin buscar ancestros.
  - Todas las salidas `data/...` tienen que estar en la carpeta del manifiesto (`OUTPUT_OUTSIDE_TAKE`).
  - No se admite mezclar rutas `data/` y relativas (`OUTPUT_MIXED_PATHS`).
  - **Comprobado por el orquestador:**
    - Escenarios del revisor: S1, S2, S2b, S3 y S4b dan rc=1; S4 (M0) da rc=0.
    - Los takes reales de `.cache/e2e-t05` y `.cache/e2e-t05c` y la copia `<x>/data/` dan `all valid` **sin opciones**.
    - `test_manifest_errors.py` + `test_generate.py`: 115 passed.
- **Fix6** (2026-10-22, 0,1 h IA medidas). Commit `3ec7112`:
  - Se valida el esquema sobre el manifiesto original.
  - Las rutas `data/` se tratan como texto crudo canónico, sin partes vacías, `.`, `..` ni barra final.
  - Los errores se capturan por manifiesto.
  - Las rutas se comparan con `normcase`.
  - **Comprobado por el orquestador:**
    - Sondas del revisor: P1–P5 y P8–P11 dan rc=1 sin traceback; P6, P7 y P7b (mayúsculas) dan rc=0; P13 (junction) da `UNSAFE_PATH`.
    - S1–S4b como se esperaba.
    - Takes reales: `all valid`.
    - `test_manifest_errors.py` + `test_generate.py`: 125 passed; `ruff` limpio.
- **QA** (2026-10-22, modo sin UI acotado a T-05; informe en `testing/report-T-05.md`):
  - `ledger-lint`: 0 incoherencias.
  - `coverage-check`: exit 0, 0 referencias rotas.
  - **`qa-gate.py`: exit 1** («sin resultados: results.json no existe»). El gate solo admite resultados de Playwright, y las E2E que cubren T-05 (E2E-01, E2E-09) son de T-15, que aún no está hecha.
  - **Decisión del propietario (2026-10-22):** T-05 queda `en-revision` y se integra en `main` para que T-04, T-06 y T-07 construyan encima. Pasa a `completado` cuando T-15 ejecute E2E-01/E2E-09 con `qa-gate` en verde. No se rebaja el gate.
- **Commits**: `65e8156` (publicación con fallback, limpieza de staging y marcadores), `406f259` (hash del fixture), `6045e79` (fix1 de la revisión, gaps 1–4).
- **Fix1** (2026-10-22, 0,88 h IA medidas):
  - Limpieza de arranque después del commit.
  - Conserva el staging de intents `prepared`.
  - Elimina el `.pending-*` sin ejecución o de ejecuciones terminales.
  - Mueve a `data/trash/orphans/` los `takes/<id>` sin fila.
  - Salta las ejecuciones vivas y registra en el log los errores por directorio.
  - RED → GREEN por gap: 7 tests nuevos en `test_worker_startup_staging.py`; los focales dan 20 passed.
  - **Suite completa del server en Windows: `2534 passed, 73 skipped` en 595 s, con 0 failed y 0 errors.**
- **Fix2** (2026-10-22, 1,02 h IA medidas). Commits `a0856c2` y `ece84d1`:
  - La limpieza ya no sigue symlinks ni junctions y comprueba que todo resuelve dentro de `data/` (N1).
  - Eventos fijos `worker.*` en `SAFE_EVENTS`, que llegan a `server.log` sin rutas (N2).
  - RED → GREEN con `mklink /J` real.
  - Focales (verificado por el orquestador): 30 passed, 3 skipped. `ruff check` limpio.
  - Suite completa del server sobre `a0856c2`: `2538 passed, 73 skipped` en 938 s, con 0 failed y 0 errors.
- **Changelog**: Los takes se publican de forma fiable sobre la carpeta de datos de Docker Desktop, sin sobrescribir nada ajeno y limpiando restos tras un reinicio.

### T-06 — SSE de eventos
- **Descripción**: Etapas reales del job por SSE, con reconexión y estado inicial.
- **Estado**: en-progreso
- **Dependencias**: T-04
- **Archivos**: `apps/server/app/sse.py`, `apps/server/app/event_routes.py`, `apps/server/app/queue/events.py` (sobre del evento y suscripción), `apps/server/tests/test_sse_*.py`, `apps/web/lib/events.ts` y su test (reinicio del contador de reintentos)
- **Verificación**: `uv run pytest apps/server/tests -k "sse or event" -m "not gpu"` en verde · vitest de `lib/events` en verde.
- **Revisión de cierre (2026-10-24, lente B sobre el código heredado):** tres defectos que rompen el progreso en vivo de la web → CA-1 a CA-3.

**Criterios de aceptación**
- [ ] CA-1 (Critical): los eventos `job.*` que publica `EventConsumer` llevan `song_id`, así que una suscripción con `?song_id=` (la que usa la web) los recibe en directo y en el replay. Un test HTTP se suscribe con `?song_id=` y recibe `job.stage`, `job.progress` y `job.done` publicados por el productor real, no por un sobre sintético.
- [ ] CA-2 (Important): un heartbeat sin eventos no cierra la suscripción. Que venza el timeout de espera no cancela ni cierra `subscription.next()`. Un test con heartbeat corto recibe dos o más `: keep-alive` y después un evento. En la web, una conexión que termina bien reinicia el contador de reintentos (`lib/events.ts`).
- [ ] CA-3 (Important): `/api/events` no da 422 cuando el dueño o la canción tienen más de 64 jobs. El ámbito incluye solo los jobs vivos (no terminales), o el límite deja de aplicarse a los terminales. Hay un test con 69 jobs (68 terminados).
- [ ] CA-4: la Verificación está en verde, sin tocar el contrato de tipos ni de campos SSE que ya consume la web (`sse.py:13-25`).

## Fase 3 — API

### T-07 — API mínima: canciones, letras, generaciones, takes y sistema
- **Descripción**: **Recortado.** CRUD de canciones con papelera simple, versiones de letra, `POST` de generaciones, takes (valorar y marcar maestro), descargas MP3/FLAC y `GET /system` mínimo. Las colecciones quedan fuera: el código existente se conserva, pero no se amplía.

  El mapa del 2026-10-22 dice qué está hecho y qué falta:
  - **Ya funciona:** todas las rutas tienen handler real con sesión y owner-scope. Las descargas sirven `listen.mp3`/`master.flac` con Range 206/416, comprueban la pertenencia del asset y usan `safe_path`. `export_contracts.py --check` da `up to date`. La API pasa (`-k "routes or api"`): 69 passed, 7 skipped.
  - **Huecos:**
    - H1: falta `duration_s`;
    - no hay modo «descargar» (`attachment`);
    - `_take_dict` genera `/api/takes/{id}/{role}` para roles sin ruta;
    - `/api/system`, `/api/models`, `/estimate`, `/peaks` y el PATCH de canción/take no tienen esquema de respuesta en OpenAPI, y el cliente web se genera de ahí;
    - la cola de `/api/system` no filtra por owner;
    - no hay tests de H1, Range inválido ni path traversal desde la API.

  **Decisiones del propietario (2026-10-22):**
  - **Duración por defecto: 30 s** si no viene; 422 si viene fuera de (0, 600].
  - **Se elimina el código creativo de M2 del server** (`apps/server/app/creative/` y sus 4 tests). Sigue en `36d4e99` y en el archivo de M2. Con esto se cierra la consecuencia de ADR-0089 que delegaba esa decisión en T-07.
- **Hallazgo H1 de T-05**: el post falla con `AUDIO_DURATION_MISSING` si la petición no trae `params.duration_s`.
- **Estado**: en-revision
- **Tipo**: backend
- **Dependencias**: T-04, T-05
- **Archivos**: `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/app/creative/` (se elimina), `apps/server/tests/test_domain_routes*.py`, `apps/server/tests/test_openapi_t03.py`, `apps/server/tests/test_creative_*.py` (se eliminan), `apps/server/tests/test_api_*.py` (nuevos), `packages/contracts/openapi.json`, `docs/arquitectura/iteracion-creativa.md` (nota de retirada), `apps/web/lib/generated/api.d.ts` (cliente regenerado con `pnpm gen`), `apps/server/tests/fixtures/creative/` y `packages/contracts/creative-recipe-v1.schema.json` (eliminados: solo los usaban los tests de M2)
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → 0 failed, 0 errors · `uv run scripts/export_contracts.py --check` → `up to date`.
  - Docker (orquestador): `server` + `engine-mock`; `POST /api/generations` **sin** `params.duration_s` → take `ready`. Descargar MP3 y FLAC con `?download=1` → `attachment`, y el hash coincide con el manifiesto.

**Criterios de aceptación**
- [x] CA-1 (H1):
  - `POST /api/generations` y `/estimate` sin `params.duration_s` usan **30 s**, que queda persistido en `job.request.params` y en los `take.params`, así que el post y el reintento lo encuentran.
  - Con `duration_s` no numérico o fuera de (0, 600] → **422 `INVALID_PARAMS`** antes de crear nada.
  - Si el descriptor del modelo fija límites más estrictos (ACE-Step: 10–600), el resolver los sigue aplicando.
- [x] CA-2 (descargas):
  - `GET /api/takes/{id}/audio` y `/master` con `?download=1` → `Content-Disposition: attachment; filename="<song-title-saneado>-<take>.mp3|flac"` (nombre seguro en ASCII o con `filename*` RFC 5987). Sin el parámetro sigue `inline`.
  - Tests:
    - Range inválido o múltiple → 416;
    - un asset de otro take u owner → 404;
    - un `asset.path` manipulado con `..`, ruta absoluta o symlink → error controlado, nunca servido.
- [x] CA-3: `_take_dict` solo genera URLs de assets que tienen ruta real; un rol sin ruta no publica URL rota. Test.
- [x] CA-4 (contrato tipado):
  - `/api/system`, `/api/models`, `/api/generations/estimate`, `/api/takes/{id}/peaks`, `PATCH /api/songs/{id}` y `PATCH /api/takes/{id}` declaran su modelo de respuesta en OpenAPI.
  - `/api/system` mínimo: GPU/VRAM, engines, modelos y cola **filtrada por owner**.
  - `openapi.json` regenerado, `--check` en verde y `test_openapi_t03.py` en verde.
- [x] CA-5: eliminados `apps/server/app/creative/` y los tests `test_creative_{composition,recipes,contract_compatibility,persistence}.py`, sin romper modelos ni migraciones. `docs/arquitectura/iteracion-creativa.md` lleva una nota de que el código se retiró de `main` (ADR-0089) y dónde recuperarlo.
- [x] CA-6: la suite del server completa en verde y `-k "routes or api"` en verde.
- **Implementación** (2026-10-22). Commit `511c9e7`; borra unas 11.700 líneas, casi todas del código de M2:
  - **RED → GREEN** (implementer):
    - CA-1: `KeyError: 'duration_s'`.
    - CA-2: `inline` cuando se esperaba `attachment`.
    - CA-3: URLs rotas `beats`/`cover`.
    - CA-4: OpenAPI sin `$ref` (6 casos) y cola sin filtro de owner.
  - **Nuevo `test_api_t07.py`** (43 tests):
    - 422 con 13 valores inválidos de `duration_s` sin crear nada;
    - Range 416;
    - assets ajenos;
    - rutas manipuladas;
    - el test del symlink se salta en Windows.
  - **Interpretación de CA-2:** un take de otro owner responde **403 `FORBIDDEN_SCOPE`** (convención actual de `_owned_take`) y no 404. Un take sin asset de ese rol responde 404.
  - **Tests:**
    - Suite completa del server en Windows (implementer): `1978 passed, 77 skipped`, 0 failed. Baja respecto a 2616 porque se eliminaron unos 680 casos de los tests de M2 (171 funciones, 72 parametrizaciones).
    - Focales (orquestador): 93 passed.
    - `export_contracts.py --check`: `up to date` (verificado por el orquestador).
- **Fix1** (2026-10-22). Commit `e10ae0e`:
  - Entero enorme → 422 en generations y estimate.
  - `take.assets` conserva todas las entradas (`manifest` con `sha256`) y solo publica `url` en los roles con ruta; en el esquema, `url` pasa a ser opcional.
  - **Comprobado por el orquestador:** focales 105 passed, 1 skipped (symlink en Windows); `export_contracts.py --check` `up to date`; `tsc --noEmit` exit 0.
  - `pnpm` hay que ejecutarlo desde PowerShell: el wrapper de bash rechaza Git Bash.
- **Verificación en Docker** (orquestador, 2026-10-22; imagen reconstruida, `server` + `engine-mock` sobre `.cache/`):
  - `POST /api/generations` **sin** `duration_s` → 202 y take **`ready`** con `params.duration_s: 30`.
  - `duration_s: 601` → 422 `INVALID_PARAMS`.
  - `take.assets` lleva `master`, `listen`, `peaks` (con `url`) y `manifest` (con `sha256`, sin `url`).
  - `?download=1` en `/audio` y `/master` → `attachment; filename="Sin titulo-<take>.mp3|flac"; filename*=UTF-8''Sin%20t%C3%ADtulo-…`, y **el hash coincide con el manifiesto** en los dos casos. Sin el parámetro → `inline`.
- **QA** (2026-10-22, orquestador, modo sin UI acotado a T-07, mismo criterio que T-04 y T-05):
  - `ledger-lint`: 0 incoherencias.
  - `coverage-check`: exit 0.
  - **`qa-gate.py`: exit 1** («sin resultados»). Las E2E que cubren T-07 (E2E-01, E2E-02, E2E-07, E2E-08, E2E-10, E2E-11) son de T-15.
  - T-07 queda `en-revision`, se integra y pasa a `completado` cuando T-15 las ejecute en verde.
- **Changelog**: Las generaciones sin duración usan 30 s en lugar de fallar. Los MP3/FLAC se pueden descargar como fichero y la API publica un contrato tipado para la web.

## Fase 4 — Web

### T-08 — Web: esqueleto, tokens, tema oscuro, i18n, layout y cliente de API
- **Descripción**: Next.js con `next-intl` (castellano), tokens de diseño, layout y cliente generado desde `openapi.json`. El tema claro queda fuera.

  El mapa del 2026-10-23 dice qué está hecho y qué falta:
  - **Ya funciona:**
    - next-intl (`locale es`, 245 claves) y la regla ESLint `studio/no-ui-literals`;
    - tokens (`styles/tokens.css`, copiados de `ux.md`);
    - tema oscuro;
    - layout con skip-link, nav y `PlayerDock`;
    - `lint` y `tsc` en verde; `test` en verde (24 ficheros, 260 tests).
  - **Huecos:**
    - el cliente `lib/api.ts` está tipado **a mano**: solo `getHealth` usa `api.d.ts`;
    - desajustes con el contrato: `gpu.limit_mb` frente a `cap_mb`, `asset.url` obligatoria en el cliente y opcional en el server, y campos que faltan o sobran en `SystemInfo`, `Estimate`, `GenerationInput`, `Song`, `Take`, `Peaks` y la sesión;
    - las respuestas 202 de generations, cancel/retry y unload no tienen esquema en el server;
    - dos hex fuera de tokens;
    - no hay test de contraste AA;
    - `'MiB'`/`'—'` en template strings y valores de estado (`ready`, `music.song`) mostrados sin traducir;
    - **`build` falla** con `ERR_SWC_NATIVE_CACHE`. La causa resultó ser doble:
      1. dos ACE huérfanas en la raíz del proyecto, que se quitaron con autorización del propietario;
      2. el lock de SWC medía 263 caracteres, por encima del MAX_PATH de 260, y se corrigió con cachés en rutas cortas (`f80382b`).

  **Decisión del propietario (2026-10-23):** las funciones web que quedan fuera del M1 recortado (colecciones, papelera y filtros, página Sistema completa, procedencia, diff de letra, beats y A/B, cola y atajos, chips de estilo, tema claro) **se dejan tal cual, sin ampliarlas**. T-08 a T-14 solo arreglan lo que esté roto.
- **Pendiente detectado en la revisión de T-07**: `SystemInfo.gpu.limit_mb` frente a `cap_mb` → CA-1.
- **Estado**: en-revision
- **Tipo**: frontend
- **Dependencias**: T-03, T-07
- **Archivos**: `apps/web/lib/api.ts`, `apps/web/lib/api.test.ts`, `apps/web/lib/generated/api.d.ts`, `apps/web/app/**` (solo los usos de tipos y textos), `apps/web/components/**` (ídem), `apps/web/styles/*.css`, `apps/web/messages/es.json`, `apps/web/**/*.test.ts(x)` (nuevos: contraste, contrato, i18n), `apps/server/app/domain_routes.py` y `apps/server/app/api_models.py` (solo los DTO de respuesta de CA-2), `packages/contracts/openapi.json`, `scripts/fetch_web_tools.py`, `scripts/web_build_inputs.py` y `scripts/pnpm.*` (solo si CA-5 lo exige). Añadidos al revisar (2026-10-23, justificados): `apps/web/lib/enum-labels.ts` (i18n de estados, CA-4), `apps/web/lib/{contract,contrast,enum-labels,i18n-keys}.test.ts`, `apps/web/eslint.config.mjs` (regla de literales de UI, CA-4), `docs/producto/ux.md` (tokens AA), `tests/test_web_tool_entrypoints.py`, `.gitignore` y `.dockerignore` (raíz corta del test de SWC, CA-5)
- **Verificación** (PowerShell; el wrapper de bash de `pnpm` rechaza Git Bash):
  - `. .\scripts\env.ps1; pnpm --filter ./apps/web lint` → 0 errores;
  - `… test` en verde;
  - `… exec tsc --noEmit` → exit 0;
  - `… build` → exit 0;
  - `uv run scripts/export_contracts.py --check` → `up to date`;
  - `uv run pytest apps/server/tests -k "routes or api or openapi" -m "not gpu"` en verde.

**Criterios de aceptación**
- [x] CA-1 (cliente tipado):
  - `lib/api.ts` deriva sus tipos de `components['schemas']`/`paths` de `lib/generated/api.d.ts` para todo endpoint con esquema, sin `as` sin validar donde haya tipo generado.
  - Quedan corregidos los desajustes: `cap_mb`, `asset.url` opcional (sin romper donde se usaba `asset.url.startsWith`), campos obligatorios u opcionales según el contrato y campos que faltaban.
  - La página Sistema muestra el tope real.
  - Hay un test que falla si `api.d.ts` no coincide con lo que genera `pnpm gen` sobre `openapi.json`.
- [x] CA-2 (contrato de las respuestas sin esquema):
  - El server declara el modelo de respuesta de `POST /api/generations` (202), `POST /api/jobs/{id}/cancel`, `POST /api/jobs/{id}/retry` y `POST /api/system/unload`, reflejando lo que devuelven hoy, sin cambiar los datos.
  - `openapi.json` y `api.d.ts` están regenerados y el cliente los usa.
  - `GET /takes/{id}/analysis` queda fuera (beats está fuera del M1 recortado).
- [x] CA-3 (tokens y AA):
  - Los dos hex sueltos de `globals.css` pasan a tokens.
  - Hay un test de contraste **WCAG AA** (≥ 4,5:1 en texto normal, ≥ 3:1 en texto grande y UI) sobre los pares texto/fondo del **tema oscuro** definidos en `tokens.css`.
  - Si algún par no llega, se ajusta el token **dentro de la paleta de `ux.md`**; si `ux.md` cambia, se actualiza en el mismo commit.
- [x] CA-4 (i18n):
  - Sin literales de UI en template strings (`'MiB'`, `'—'`).
  - Los estados y tareas que se muestran (`ready`, `failed`, `music.song`…) se traducen desde `messages/es.json`.
  - Un test comprueba que toda clave usada estáticamente existe en `es.json`.
- [x] CA-5 (`build`):
  - `pnpm --filter ./apps/web build` termina con exit 0.
  - La causa del `ERR_SWC_NATIVE_CACHE` se diagnostica con evidencia. Si es un permiso o caché local, se corrige el script de bootstrap o de herramientas que la crea, o se documenta el paso, **sin desactivar la comprobación de seguridad** que lo detecta.
- [x] CA-6: `lint`, `test` y `tsc` en verde; `export_contracts.py --check` en verde; tests de API del server en verde.
- **Changelog**: La web usa el contrato generado de la API (la página Sistema muestra el tope de VRAM real), cumple el contraste AA en el tema oscuro, no muestra textos sin traducir y vuelve a compilar.
- **Evidencia de la Verificación** (2026-10-23, orquestador, PowerShell, rama `m1/t-08-web` en `43f1d3f`):
  - `lint` exit 0;
  - `tsc --noEmit` exit 0;
  - `test`: 29 ficheros, 312 passed;
  - `build` exit 0 (rutas `/`, `/create`, `/songs`, `/songs/[id]` y `/system`);
  - `export_contracts.py --check`: `openapi.json up to date`;
  - pytest de API del server: 117 passed y 8 skipped;
  - SWC, caché y Playwright: `tests/test_web_tool_entrypoints.py -k "native or cache or swc or playwright or environment"` dio 28 passed.
- **QA** (2026-10-23, orquestador, modo sin UI acotado a T-08, el mismo criterio que en T-04, T-05 y T-07):
  - la Verificación está en verde;
  - **`qa-gate.py` sale con exit 1** («sin resultados»), porque las E2E de la web son de T-15;
  - T-08 queda `en-revision`, se integra en `main` y pasa a `completado` cuando T-15 ejecute las E2E en verde.

### T-09 — Crear: letra, estilo, autoría y avanzado
- **Descripción**: Editor de letra con validación en vivo, estilo, autoría obligatoria, instrumental y avanzado según el `params_schema`. Chips y estilos a excluir quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-08, T-07
- **Archivos**: `apps/web/app/create/page.tsx` y su test, `apps/web/components/LyricsEditor/**`, `apps/web/lib/api.ts` (lectura del `code`), `apps/web/messages/es.json`
- **Verificación** (PowerShell): `pnpm --filter ./apps/web lint`, `exec tsc --noEmit`, `test` y `build` en verde; E2E-crear de T-15.
- **Mapa del 2026-10-24:** funcionan el parser compartido, la autoría obligatoria (botón deshabilitado y 422 traducido), el instrumental y el avanzado filtrado por `params_schema`. Fallan los puntos de CA-1 a CA-6.

**Criterios de aceptación**
- [ ] CA-1: la duración arranca vacía con el placeholder de 30. Vacía no envía `duration_s` y el server aplica 30 s. Nunca se envía `duration_s: 0`.
- [ ] CA-2: las variantes arrancan en 1. El 2 solo se ofrece si la estimación (`vram_mb`) cabe en la VRAM libre de `/api/system`. Si no hay datos, solo 1.
- [ ] CA-3: con el botón deshabilitado se ve un texto con cada motivo (letra vacía o inválida, estilo, autoría, idioma, avanzado inválido), enlazado con `aria-describedby`.
- [ ] CA-4: un error de envío muestra el `code` del problem+json y su texto, no un mensaje genérico (CA-10 de la spec).
- [ ] CA-5: el resaltado de etiquetas de `LyricsEditor` sale de `parseLyrics(...)`, sin una regex propia que contradiga la validación.
- [ ] CA-6: si `/api/system` no responde, no se muestran parámetros avanzados inventados ni un `model_id` fijo: el formulario explica que el sistema no está disponible.

### T-10 — Tarjeta de generación en vivo
- **Descripción**: La tarjeta muestra las etapas por SSE, los errores con `code`, `job_id` y reintentar, y la onda al terminar. El feed A/B queda fuera.
- **Estado**: en-progreso
- **Dependencias**: T-09, T-06
- **Archivos**: `apps/web/components/GenerationCard.tsx`, `apps/web/components/GenerationFeed.tsx`, `apps/web/lib/generation-feed.ts`, `apps/web/lib/event-reducer.ts`, `apps/web/app/create/page.tsx` (solo el feed), sus tests y `apps/web/messages/es.json`
- **Verificación** (PowerShell): `pnpm --filter ./apps/web lint`, `exec tsc --noEmit`, `test` y `build` en verde; E2E-generar de T-15 contra `engine-mock`.
- **Mapa del 2026-10-24:** el parser y el reducer SSE, el snapshot, y el `code` con `job_id` y Reintentar sin toast funcionan. Que no llegue ningún evento en vivo es culpa del server (T-06 CA-1).

**Criterios de aceptación**
- [ ] CA-1: el stepper refleja las etapas reales del engine (`loading_model`, `generating`, `decoding`) y la del post-proceso, con la misma correspondencia para el mock y para ACE-Step. Una etapa desconocida no deja el stepper sin marcar.
- [ ] CA-2: la tarjeta pasa a «Lista» solo cuando el take está `ready` (siguiendo el `post_job_id` o el estado del take), no cuando acaba la generación.
- [ ] CA-3: la onda final usa los pares [min,max] reales, sin recortar los negativos a 0.
- [ ] CA-4: si Reintentar o Cancelar fallan (409 o 503), la tarjeta muestra el `code`, sin tragarse el error.

### T-11 — Biblioteca de canciones
- **Descripción**: Lista con búsqueda FTS y preescucha del maestro. Grid, filtros avanzados y papelera en la UI quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-07, T-08
- **Archivos**: `apps/web/app/songs/page.tsx`, `apps/web/components/MasterPreview.tsx`, sus tests y `apps/web/messages/es.json`; en el server, la consulta FTS de `GET /api/songs` (`apps/server/app/domain_routes.py`) y su test
- **Verificación**: `uv run pytest apps/server/tests -k "songs or fts" -m "not gpu"` en verde; web (PowerShell): `lint`, `tsc`, `test` y `build` en verde; E2E-biblioteca de T-15.
- **Decisión (orquestador, 2026-10-24, reversible):** una canción sin maestro usa en la preescucha su último take `ready`, y la UI lo indica.

**Criterios de aceptación**
- [ ] CA-1 (server): las búsquedas `hip-hop`, `rock & roll`, `it's`, `AC/DC` y `amo` devuelven 200. Las cuatro primeras encuentran su canción y `amo` encuentra «amor» (por prefijo). Cada término se escapa antes de `MATCH` y una búsqueda nunca da 422 por la sintaxis de FTS5.
- [ ] CA-2: Enter busca, y que se recarguen las dependencias no borra la búsqueda en curso.
- [ ] CA-3: la preescucha funciona en canciones sin maestro, con su último take `ready`, y si no hay ninguno lo dice.

### T-12 — Vista de canción
- **Descripción**: Takes con valoración y maestro, onda con seek, letra y descarga MP3/FLAC.
- **Estado**: en-progreso
- **Dependencias**: T-11
- **Archivos**: `apps/web/app/songs/[id]/page.tsx` y su test nuevo, `apps/web/components/Waveform.tsx`, `apps/web/lib/api.ts` (descarga y PATCH), `apps/web/messages/es.json`; en el server, `PATCH /api/takes/{id}` (`domain_routes.py`: borrar la valoración con `null` y devolver `assets`) y su test
- **Verificación**: `uv run pytest apps/server/tests -k "take" -m "not gpu"` en verde; web (PowerShell): `lint`, `tsc`, `test` y `build` en verde; E2E-cancion de T-15.

**Criterios de aceptación**
- [ ] CA-1: la onda usa todos los bins del canal 0 de los peaks, no solo el primero.
- [ ] CA-2: la valoración se elige de 1 a 5 y volver a pulsar la misma la borra (`rating: null`, que el server acepta). Nunca se envía `0` y los errores se muestran.
- [ ] CA-3: tras valorar o elegir maestro, el take conserva `assets` y sigue reproduciéndose. El PATCH devuelve el take con sus `assets`, o el cliente fusiona la respuesta.
- [ ] CA-4: «Marcar maestro» solo se habilita en takes `ready` y su error se muestra.
- [ ] CA-5: la descarga usa `?download=1` y el nombre que da el `Content-Disposition` del server.
- [ ] CA-6: la página tiene test unitario (takes, valoración, maestro, onda y descarga).

### T-13 — Reproductor persistente
- **Descripción**: El reproductor sobrevive a la navegación. La cola y los atajos quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-08
- **Archivos**: `apps/web/components/PlayerContext.tsx`, `apps/web/components/PlayerDock.tsx` y sus tests; `apps/web/app/create/page.tsx` (solo la lectura de localStorage)
- **Verificación** (PowerShell): `lint`, `tsc`, `test` y `build` en verde; E2E-reproductor de T-15.

**Criterios de aceptación**
- [ ] CA-1: no hay desajuste de hidratación: localStorage se lee en un efecto, no en el inicializador de `useState`.
- [ ] CA-2: el `<audio>` nunca carga un `src` sin token. Play se habilita cuando el blob autenticado está listo.
- [ ] CA-3: un test comprueba que la pista sigue al navegar entre `/songs` y `/create`.

### T-14 — Colecciones y página Sistema
- **Descripción**: Aplazada (ADR-0089); el código parcial se conserva.
- **Estado**: cancelado
- **Dependencias**: T-07, T-08
- **Verificación**: n/a (cancelada).

## Fase 5 — Pruebas y cierre

### T-15 — Suite E2E del camino mínimo (Playwright + engine-mock)
- **Descripción**: E2E de crear, generar, biblioteca, canción, reproductor y errores contra `engine-mock` (actualizar `test-plan.md` al recorte).
- **Cierra también T-04, T-05 y T-07**: cuando E2E-01 y E2E-09 (T-05), E2E-04, E2E-05 y E2E-06 (T-04) y E2E-01, E2E-02, E2E-07, E2E-08, E2E-10 y E2E-11 (T-07) pasen con `qa-gate` en verde, esas tareas pasan a `completado`.
- **Estado**: en-progreso
- **Dependencias**: T-09 a T-13
- **Verificación**: `pnpm --filter web exec playwright test` en verde; informe de `qa` con 0 fallos.

### T-16 — Prueba real con ACE-Step, README y cierre
- **Descripción**: Canción real generada desde la web con ACE-Step (modelo de M0/T-13), escuchada por el propietario, y README de puesta en marcha.
- **Estado**: en-progreso
- **Dependencias**: T-15, M0/T-13
- **Verificación**: take real `ready` con manifiesto válido, escuchado y aceptado por el propietario · README seguido desde cero.


### T-17 — Fuga de temporales en `data/tmp` (vía rápida)
- **Descripción**: Vía rápida (`quick-implement`, 2026-10-22). Recoge los hallazgos H5 de T-04, B5 de T-04/ADR-0090 y N7 de T-04. Hoy cada canción correcta deja en `data/tmp`:
  - la copia del WAV en `_server_inputs/<exec>/`;
  - los JSON de `_server_cpu/<exec>/`;
  - la salida `tmp/<attempt>` de `audio.beats`;
  - directorios `_server_inputs/<hex>` de engine.

  Además, el reintento de ADR-0090 abandona `tmp/<attempt>`, y `CancelSweeper` reintenta para siempre los fallos permanentes de borrado.
- **Estado**: completado
- **Tipo**: backend
- **Dependencias**: T-04, T-05
- **Archivos**: `apps/server/app/worker/execution.py`, `apps/server/app/queue/cleanup.py`, `apps/server/app/queue/runtime.py`, `apps/server/app/queue/events.py`, `apps/server/app/queue/inputs.py`, `apps/server/tests/test_tmp_cleanup_t17.py` (nuevo), `apps/server/tests/test_queue_cancel_cleanup.py`
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → 0 failed, 0 errors.
  - Docker (orquestador):
    - una generación correcta con `engine-mock` → tras `ready` (y el beats), en `data/tmp` no queda **nada** de esa canción;
    - un SIGKILL a mitad y la reanudación, igual;
    - `verify_manifest.py` → `all valid`.

**Criterios de aceptación**
- [x] CA-1 (H5): cuando un job llega a un estado terminal (`succeeded`, `failed` o `cancelled`), el server borra lo que ese job dejó en `data/tmp` y ya no necesita ningún job vivo (dependiente, hermano, reintento manual o automático pendiente). Cubre:
  - `tmp/<attempt>` de los jobs de engine (generación y `audio.beats`) y de **todos** sus attempts;
  - `_server_inputs/<exec>` y `_server_cpu/<exec>` de los posts;
  - los `_server_inputs/<hex>` que crea `queue/inputs.py`.

  Un `failed` que todavía puede reintentarse conserva lo que necesita el reintento.
- [x] CA-2 (B5): el `tmp/<attempt>` de un intento abandonado por el reintento acotado (ADR-0090) se borra como parte de CA-1.
- [x] CA-3 (N7): los fallos **permanentes** de borrado (destino symlink o junction, no-directorio, fuera de `data/`) se registran **una vez** (`worker.cleanup.failed`) y salen de `deferred`. Solo se reintentan los transitorios (`OSError` de `rmtree`), con un tope de intentos.
- [x] CA-4: las reglas de borrado seguro de T-05 siguen intactas (no seguir enlaces, quedarse dentro de `data/`, errores como evento) y no se borra nada que use un job vivo. Hay tests de regresión: post vivo, `audio.beats` pendiente y reintento manual posible.
- **Implementación** (2026-10-22, 2,95 h IA medidas). Commit `face3d2`:
  - `TerminalSweeper` generaliza el barrido incremental de cancelados a todos los terminales.
  - `remove_data_dir` distingue `True`, `False`, `None` (transitorio, tope de 5) y `PERMANENT` (se registra una vez).
  - Los `_server_inputs/<hex>` se atribuyen por `engine_request.inputs[].path`; los que no se pueden atribuir se conservan.
  - **RED → GREEN:** `test_tmp_cleanup_t17.py` en rojo contra el alias de `CancelSweeper` (aserciones de CA-1/CA-3, `AttributeError: MAX_RETRIES`) → 14 passed.
  - **Tests:** suite completa del server (implementer): `1993 passed, 77 skipped`, 0 failed. Focales (orquestador): 55 passed; `ruff` limpio.
- **Verificación en Docker** (orquestador, 2026-10-22): imagen reconstruida, `server` + `engine-mock`.
  - Generación correcta, y aparte SIGKILL a mitad con reanudación: tras `ready` y `audio.beats` `succeeded`, en `data/tmp` **solo quedan los contenedores vacíos** `_server_cpu/` y `_server_inputs/`, sin `.pending-*`.
  - `verify_manifest.py`: `all valid (2 manifests)`.
- **Fix1** (2026-10-22, 4,84 h IA medidas). Commit `dc733e0`:
  - Conjunto en memoria de jobs **resueltos** en lugar del cursor por `updated_at`, que dependía del reloj del engine.
  - Consulta solo de ids y trozos de 200, de más nuevos a más viejos.
  - El barrido inicial ya no bloquea `start()`.
  - Lectura por columnas (`json_extract`) sin hidratar `JobAttempt`.
  - Un único `worker.cleanup.failed` por proceso.
  - Tests de regresión con un `audio.beats` real pendiente y con reintento manual tras el barrido.
  - **Medido con 9.000 terminales:** antes, 10,5 s bloqueando `start()`; ahora, 3,0 s repartidos en 46 pasadas de unos 66 ms. En régimen, unos 14 ms por pasada cada 2 s.
  - **Tests:**
    - Suite completa del server (implementer): `2001 passed, 77 skipped`, 0 failed.
    - Focales (orquestador): 96 passed.
    - Repro del revisor: 2 passed.
    - **Docker Linux:** 90 passed, 2 skipped.
  - **De punta a punta en Docker:**
    - En 3 secuencias de «canción normal y después SIGKILL con reanudación» el take llega a `ready` (reanudación en 31–60 s), y al terminar quedan **0 ficheros en `data/tmp`**; `verify_manifest.py`: `all valid (6 manifests)`.
    - Una primera ejecución se cortó con el take aún `queued` a los 180 s: era una espera demasiado corta para un post de 600 s de audio. Con el seguimiento cada 20 s se vio que los temporales se conservan mientras el post está vivo y se borran al terminar.
- **Fix2** (2026-10-22, 3,34 h IA medidas). Commits `5ec56c5` y `9c147e3` (este último, retoque de ruff SIM103 hecho por el orquestador):
  - **Aparcar:** los jobs `needed`/`waiting` se aparcan y se reevalúan cada `PARK_S=10 s` con su propio presupuesto.
  - **Cadencia:** la rápida solo mientras quede histórico nuevo.
  - **Alineación con `Retry.eligible`:** `waiting` sigue sus condiciones (lane, estado del attempt, offload `VRAM_EXCEEDED`).
  - **Registro único:** un fallo permanente se registra una vez por proceso y destino, por todas las vías.
  - **`IN` troceados:** de 500 en 500, y un fallo del barrido ya no se salta `_remove_stages`.
  - **Test con la cadena real** beats→post.
  - **Gap 5 no se toca:** con «solo ids mayores» se perderían los terminales de ids antiguos. Queda lineal y sin índice; ver deuda.
  - **Tests:**
    - Suite completa del server (implementer): `2010 passed, 77 skipped`, 0 failed.
    - Focales (orquestador): 105 passed; `ruff` limpio.
  - **Bench del revisor, 2.000 viejos + 250 `waiting`** (orquestador): 12 pasadas en 2,4 s, `pending=0`, `resolved=2001`, `oldest_dir_exists=False`. Régimen estable: 4,2 ms. Pico de memoria: 1,4 MB.
  - **Docker** (orquestador):
    - 2 secuencias de canción normal y SIGKILL con reanudación dan 4 takes `ready`, **0 ficheros en `data/tmp`** y `all valid (4 manifests)`.
    - Linux real: 99 passed, 2 skipped.
- **QA** (2026-10-22, orquestador, modo sin UI):
  - `ledger-lint`: 0 incoherencias.
  - `coverage-check`: exit 0.
  - T-17 no tiene E2E en `test-plan.md`: es una tarea interna sin interfaz. Su evidencia es la verificación en Docker de arriba (0 ficheros en `data/tmp` tras 2 secuencias de canción normal y SIGKILL con reanudación; manifiestos válidos) y la suite.
  - Se cierra como `completado`.
  - Deuda: el Minor 1 del intento 3 y el gap 5 del intento 2 (consulta lineal sin índice).
- **Changelog**: El estudio ya no acumula copias de audio ni ficheros temporales en `data/tmp` tras cada canción.

## Revisión de dos lentes — intento 1: Fase 2 (T-05) — dos Important pendientes

Lentes: A, B y D. D se activó por la ruta `worker`; C no aplica. Diff `b72be24..65e8156+406f259`.

**Veredicto de la Lente A por criterio:**
- CA-1 ✓.
- CA-2 pendiente declarado. El fallback está cubierto; la parte nativa queda para Docker.
- CA-3 ✓ en su letra, con el gap 1.
- CA-4 ✓.
- CA-5 pendiente declarado.
- Alcance ✓ y constitución ✓.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | La limpieza al arrancar no cubre lo que dice ADR-0089 §2 («directorio sin fila → huérfano»). Quedan sin limpiar el `.pending-*` de ejecuciones desconocidas o terminales y el `takes/<id>` final sin fila `ready` (rename hecho pero el commit no) | T-05 | pendiente | `execution.py:187-197`, `test_worker_startup_staging.py:100,113` (lente A) |
| 2 | Important | Borra el staging de intents en `prepared`, que es la única copia del paquete, sin hacer transicionar la fila. Un reanudado posterior falla con `FileNotFoundError` en `publications.py:594`/`:309` y el take queda colgado | T-05 | pendiente | `execution.py:212,226`; `publications.py:546-568,583,594` (lente B) |
| 3 | Minor | `rmtree` dentro de `session.begin()`, antes del commit, con `ignore_errors=True`. Si hay rollback ya se ha borrado y los fallos no dejan rastro | T-05 | pendiente (se corrige junto a 1–2) | `execution.py:187,226` (lente B) |
| 4 | Minor | No consulta `self.owners` antes de borrar el staging de una ejecución viva en el mismo proceso | T-05 | pendiente (se corrige junto a 1–2) | `execution.py:207-212` (lente B) |
| 5 | Minor | ADR-0089 encarga a T-05/T-07 decidir si el código creativo de M2 se queda; no consta la decisión | T-05 | anotado: se queda mientras lo importen `models` y las migraciones; decide T-07 | ADR-0089 §Consecuencias (lente A) |
| 6 | Minor | `reconcile_startup` vuelve a procesar en cada arranque las ejecuciones que ya están `interrupted` (`revision += 1`). Es preexistente | T-04 | deuda anotada en T-04 | `execution.py:191-196` (lente D, fuera de su lente) |

## Revisión de dos lentes — intento 2: Fase 2 (T-05) — sin gaps Important; dos Minor nuevos

Lentes A y B en un revisor de contexto fresco, sobre el diff `406f259..6045e79`.

**Gaps del intento 1:** 1 ✓ · 2 ✓ · 3 ✓ · 4 ✓ · 5 ✓ · 6 (deuda de T-04).

- **Gap 2:** se revisaron todos los estados de la intent (`reserved`, `prepared`, `renamed`, `committed`, `failed`, `cancelled`, `quarantined`). Solo en `prepared` el staging es la única copia.
- **Focales:** 20 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| N1 | Minor | El recorrido de limpieza solo filtra `is_symlink()` y sigue las junctions de Windows. Una junction dentro de `data/songs/*/takes` haría mover a la papelera contenido de fuera de `data/` (CWE-59). Lo mismo pasa si `data/trash` es una junction | T-05 | corregido (`a0856c2`) | Reproducido con `mklink /J`. `execution.py:229,255,258,287-289` |
| N2 | Minor | El logger `app.worker.execution` no cuelga de `configure_logging`, así que los INFO/WARNING de la limpieza no llegan a `server.log`. Además, el `LOG.error` incluye la ruta absoluta | T-05 | corregido (`a0856c2`, `ece84d1`) | `execution.py:42,265,270-272,279`; `app/logging.py:50-52` |

## Revisión de dos lentes — intento 3: Fase 2 (T-05) — un Important pendiente; decide el propietario

Lentes A y B en un revisor de contexto fresco, sobre el diff `860f0a3..a8bff17`.
- **H2:** `--data-dir` ✓, M0 ✓, escape del prefijo ✓, rc≠0 ✓.
- **H3:** solo tras el commit ✓, sin carreras ✓, errores como evento ✓.
- **H4:** ✓.
- **Evidencia:** 126 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | La autodetección de `verify_manifest.py` valida contra el primer ancestro con `data/` y no contra los ficheros que acompañan al manifiesto. Así, una copia corrupta de un take fuera de `data/` (por ejemplo en `.cache/` o en un backup) da «all valid» si el take vivo está bien | T-05 (H2) | el propietario elige corregir y volver a revisar (fix5, 2026-10-22) | Escenario S1 reproducido: `scripts/verify_manifest.py:32-35` |
| 2 | Minor | Ni la autodetección ni `--data-dir` exigen que las salidas `data/...` estén en el take del propio manifiesto, y no rechazan mezclar salidas `data/` y relativas | T-05 (H2) | pendiente (se corrige junto al 1) | S2b/S3: `verify_manifest.py:21-31` |
| 3 | Minor | Si una toma falla después de `process_audio`, su `.pending-<exec>/<take>` queda con ficheros, `rmdir` falla y se emite `worker.cleanup.failed` (error) en una ejecución `mixed`. El staging dura hasta el siguiente arranque | T-05 (H3) | deuda aceptable: la limpieza de arranque lo cubre | `execution.py:244-247` |
| 4 | Minor | El ledger decía «autodetección sobre el take real» | T-05 | corregido en el ledger | `tasks.md` (Fix3 + fix4) |

## Revisión de dos lentes — intento 4: Fase 2 (T-05) — fix5 cierra el gap; regresión Important

Revisión corta autorizada por el propietario, con lentes A y B sobre el diff `93971b1..5d989b4`. Los criterios (1) a (5) del contrato del fix5 se cumplen. Escenarios S1–S4b ✓; comparación por partes, no por sufijo ✓; junctions ✓.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | La vista sustituye `path` por el nombre base **antes** de validar el esquema, y `PurePosixPath` normaliza `./`, `//` y la barra final. La CLI da «all valid» a manifiestos que el esquema y `safe_path` rechazan; con `93971b1` daban rc=1 `MANIFEST_SCHEMA` | T-05 | corregido (`3ec7112`) | `verify_manifest.py:33,52-57`; sondas P1–P3 |
| 2 | Minor | Una salida que no es dict o que no tiene `path` produce `TypeError`/`KeyError` sin capturar y aborta el recorrido del directorio | T-05 | corregido (`3ec7112`) | `verify_manifest.py:55,94` |
| 3 | Minor | En Windows, la comparación de la carpeta distingue mayúsculas (`absolute()`): un take legítimo da un falso negativo, pero falla cerrado | T-05 | corregido (`3ec7112`) | `verify_manifest.py:37-40` |

## Revisión de dos lentes — intento 5: Fase 2 (T-05) — sin gaps Critical/Important

Revisión corta del fix6 (`5d989b4..3ec7112`), lentes A y B:
- Los tres gaps del intento 4 están corregidos ✓.
- El esquema se valida sobre el original antes de cualquier rama ✓.
- rc≠0 en todo fallo ✓.
- Sin regresión de S1–S4b ni de las junctions ✓.
- Tests: 125 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | `normcase` iguala mayúsculas también en carpetas de Windows que las distinguen. Un gemelo en minúsculas creado a mano (`songs/s/takes/t`), con un manifiesto que declara `songs/S/takes/T`, da «valid» aunque las salidas verificadas son las del gemelo. Los ULID del server van siempre en mayúsculas; el contexto privado se busca por hash | T-05 | deuda aceptada (Minor; no bloquea) | `verify_manifest.py:47,54-56`; sonda `cs5probe.py` con `fsutil … setCaseSensitiveInfo` |

## Revisión de dos lentes — intento 1: Fase 2 (T-04) — siete Important pendientes

Lentes A, B y D (D por la ruta `worker`/`queue`; C no aplica), sobre el diff `e5974f1..b613714`.

**Lente A por criterio:**
- CA-1 parcial (gaps I1, I2).
- CA-2 ✓.
- CA-3 ✓ en código; falta la evidencia en Docker (I3).
- CA-4 ✓ en código; falta el ADR (I3b).
- CA-5 ✓.
- CA-6 sin verificar por RAM; según el implementer, 2570 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| I1 | Important | Un post que muere tras `claim_job` y antes de crear su `cpu_execution` se queda `interrupted` para siempre, o `running` ocupando un carril si no hay backends. `resumable_jobs`, `claim_resume` y `claim_job` lo ignoran | T-04 | corregido (`a1a7a8c`) | `execution.py:411-446,118-119,674-706,779`; reproducido (lente A) |
| I2 | Important | La reanudación con intents `prepared` (republicar desde el staging y `resume-skip.json`) no tiene ningún test | T-04 | corregido (`a1a7a8c`) | `execution.py:804-818,1034-1047`; `audio_child.py:181-190,232` |
| I3 | Important | No hay evidencia en Docker de cancelar un post **interrumpido**: la pegada era de un post en curso | T-04 | corregido: evidencia en Docker (fix1) | `tasks.md` (verificación de T-04) |
| I3b | Important | CA-4 (fallo sintético retryable que consume un intento) contradice ADR-0018 §20, ADR-0043 §16 y `sistema.md:103,106`. Falta un ADR y actualizar esos documentos | T-04 | corregido: ADR-0090, con ADR-0018, ADR-0043 y `sistema.md` actualizados | `recovery.py:51-68`, `runtime.py:248-255` |
| B1 | Important | Inversión del orden de los locks: `claim_resume` toma `_guard` dentro de la barrera y `execute` los toma al revés. Resultado: `PublicationTimeout` y un post nuevo `failed` para siempre | T-04 | corregido (`a1a7a8c`) | `execution.py:84,504,963-969,779`; reproducido (lente B) |
| B2 | Important | Una reanudación o cancelación rechazada se repite cada 0,1 s y cada transacción sin efecto hace `mark_gap`, que corta todos los SSE (también lo señala D) | T-04 | corregido (`a1a7a8c`) | `publications.py:346-352`, `execution.py:533,1242`, `runtime.py:563-569`; reproducido |
| B3 | Important | `_occupied_slots` mira `job_executions` y no los `owners` retenidos, y filtra `deleted_at` aunque el proceso siga vivo. Puede haber 3 grupos CPU vivos | T-04 | corregido (`a1a7a8c`) | `execution.py:84-100,576,1086-1088` |
| m1 | Minor | Una identidad nula cuenta como muerte sin sondear; el ledger decía «en Windows sigue `unknown`» | T-04 | corregido (`a1a7a8c`), conservador | `execution.py:393-394,973-1005` |
| m2 | Minor | La cláusula de CA-2 «ni de otro owner» no tiene test | T-04 | corregido (test de regresión) | `test_worker_resume.py:53-90` |
| B4 | Minor | Un líder zombi o un `/proc` ausente cuenta como muerte aunque el grupo siga vivo (otro espacio de PID) | T-04 | corregido (`a1a7a8c`) | `execution.py:58-59,133` |
| B5 | Minor | El reintento de CA-4 deja huérfano el `data/tmp/<attempt antiguo>` | T-04 | se trata junto a H5 | `runtime.py:247-255`, `recovery.py:108` |
| D1 | Minor | `sweep_cancelled` relee cada 2 s todos los cancelados del histórico (N+1). Con 500, unos 125 ms cada 2 s en el pool de 2 hilos | T-04 | corregido (`a1a7a8c`) | `cleanup.py:91-124`, `runtime.py:772`; medido |

## Revisión de dos lentes — intento 2: Fase 2 (T-04) — un Important nuevo

Lentes A y B sobre el fix1 (`7a6ed52..a1a7a8c`).

**Gaps del intento 1:**
- I1 ✓ · I2 ✓ parcial · B1 ✓ · B2 ✓ · B3 ✓ · m1 ✓ (regresión: N1) · m2 ✓ · B4 ✓ · D1 ✓.
- Focales: 59 passed.
- La frase del ledger «I2 con hash y `write_once` reales» es inexacta para la republicación: `publisher.reconcile` está simulado en el test. Ese paso sí lo ejecuta de verdad el E2E de CA-1 en Docker.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| N1 | Important | Con la marca `{"launching": true}` el post no se puede cancelar ni reanudar nunca, ni en caliente ni tras un reinicio. Pasa también cuando `LinuxGroup` falla antes de `Popen` y no se llegó a lanzar ningún proceso. Antes del fix1 funcionaba. Además retiene para siempre el `data/tmp` de la generación | T-04 | corregido (`a9fc73d`) | `execution.py:1107-1118,503-505,1355-1359,541`; reproducido (`scratchpad/m1/test_m1_stuck.py`) |
| N2 | Minor | Un borrado fallido no se reintenta: `since` avanza y el fallo no se aplaza | T-04 | corregido (`a9fc73d`) | `cleanup.py:176-179,55` |
| N3 | Minor | Un post reencolado (I1) deja huérfano `data/tmp/_server_cpu/<exec_viejo>/` | T-04 | corregido (`a9fc73d`) | `execution.py:839-841,346-369` |
| N4 | Minor | La republicación de intents `prepared` no tiene test sin simulaciones (`publisher.reconcile` simulado) | T-04 | corregido (`a9fc73d`) | `test_worker_resume_prepared.py:446,466,141` |
| N5 | Minor | `_probe_group` recorre todo `/proc` por cada post `interrupted` en cada tick sin backoff, y `_backoff` crece sin podarse | T-04 | corregido (`a9fc73d`) | `runtime.py:563`, `execution.py:119-121` |

## Revisión de dos lentes — intento 3: Fase 2 (T-04) — sin gaps Critical/Important

Lentes A y B sobre el fix2 (`b61878f..a9fc73d`).
- N1(a) ✓: la detección de «sin Popen» es fiable, porque el grupo se registra antes de `Popen` y `process` solo existe cuando `Popen` vuelve.
- N1(b) ✓: no es plausible un falso «muerto»; un `PermissionError` no prueba nada.
- N2 ✓ · N3 ✓ · N5 ✓.
- N4 se verificó en Docker (139 passed).
- Focales: 41 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| N7 | Minor | Los fallos **permanentes** de borrado (symlink o junction como destino, un no-directorio o algo fuera de `data/`) entran en `deferred` para siempre y registran `worker.cleanup.failed` (ERROR) cada 2 s, sin tope | T-04 | deuda aceptada; se trata con H5/B5 (mismo barrido) | `cleanup.py:50,55,142,183`; repro `scratchpad/n2_perm.py` |

## Revisión de dos lentes — intento 1: Fase 3 (T-07) — sin gaps Critical/Important

Lentes A, B y C. C la activó el orquestador a mano porque el diff construye `Content-Disposition` con el título de la canción y sirve ficheros. Diff `2d3f0a5..511c9e7`.

- **Lente A:** CA-1 a CA-5 ✓.
  - CA-2: el 403 para un take ajeno no contradice ningún documento vigente.
  - CA-4: `tsc --noEmit` limpio y el `api.d.ts` regenerado es idéntico.
  - CA-6 y Docker: sin verificar por la lente.
- **Lente C:** sin hallazgos.
  - `Content-Disposition` saneado frente a CRLF, comillas, `..` y caracteres bidi.
  - Owner-scope intacto.
  - Los DTO solo documentan, no filtran.
- **Lente B:** los 30 s por defecto también se aplican a `music.instrumental`; el retry y la compensación funcionan.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | Un entero JSON de más de unos 309 dígitos en `duration_s` → `OverflowError` → 500 (generations) / 503 (estimate), en vez de 422 | T-07 | corregido (`e10ae0e`) | `domain_routes.py:143,867-870,1453-1456` (lentes B y C) |
| 2 | Minor | CA-3 quitaba la entrada `manifest` entera de `take.assets` (con su `sha256`), que `ProvenancePanel.tsx` muestra y exporta. Regresión | T-07 | corregido (`e10ae0e`) | `domain_routes.py:361-371` (lente B) |
| 3 | Minor | ADR-0089 seguía diciendo que el código M2 «no se borra» | T-07 | corregido: nota de resolución en ADR-0089 y en el índice | `ADR-0089:61` (lente A) |

**Fuera de T-07:** el tipo a mano `SystemInfo` de la web espera `gpu.limit_mb`, pero el server envía `cap_mb`. Es anterior a T-07 → se corrige en **T-08**.

## Revisión de dos lentes — intento 1: Fase 5 (T-17) — cuatro Important pendientes

Lentes A+B (un revisor) y D (por la ruta `queue`), sobre el diff `81e38b9..face3d2`.

**Sin borrados indebidos.** Los casos revisados:
- **Reintento manual:** vuelve a resolver las entradas desde `data/songs` y `data/uploads` con un `<hex>` nuevo (`uuid4`).
- **Reintento automático:** reutiliza el `<hex>` solo dentro del mismo job, y ese job se conserva.
- **`audio.beats`:** lee el asset publicado.
- **Generación con el post `queued`:** se aplaza.
- **`<hex>` compartido:** imposible.

Veredicto por criterio:
- CA-1 ✓ en su letra.
- CA-2 ✓.
- CA-3 ✗ en «una vez».
- CA-4 ✗ en los tests prometidos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Un fallo permanente se registra varias veces: con `MARGIN_S=5` de producción y un barrido cada 2 s se reexamina mientras `updated_at >= since`, y también en cada arranque. El test lo ocultaba con `MARGIN_S=0` | T-17 | corregido (`dc733e0`) | `cleanup.py:142,247-248`; `test_tmp_cleanup_t17.py:30`; repro: COUNT 3 |
| 2 | Important | El `updated_at` de un terminal viene del `ts` del engine (reloj del contenedor). Si el engine va ≥ 5 s por detrás (deriva de WSL2), el barrido incremental no lo ve nunca hasta el siguiente arranque. Es una fuga | T-17 | corregido (`dc733e0`) | `events.py:250,447`, `cleanup.py:142`; repro: RAW EXISTS True |
| 3 | Important | CA-4 pide tests con un `audio.beats` real pendiente y con reintento manual tras el barrido. El test `…pending_beats…` crea un `post.audio` | T-17 | corregido (`dc733e0`) | `test_tmp_cleanup_t17.py:193-210` |
| 4 | Important | El barrido hidrata el `JobAttempt` completo (validación pydantic de provenance, contratos y terminal) cuando solo necesita `id` y `engine_request.inputs`. Medido con 9.000 jobs: 7,06 s frente a 1,03 s con columnas | T-17 | corregido (`dc733e0`) | `cleanup.py:103-109,152-156` (lente D) |
| 5 | Minor | El barrido de arranque recorre todo el histórico de terminales dentro de `runtime.start()`, y el server no atiende HTTP hasta que termina (3,5 s con 3.000; 9,9 s con 9.000) | T-17 | corregido (`dc733e0`) | `runtime.py:169`, `main.py:72` (lente D) |

## Revisión de dos lentes — intento 2: Fase 5 (T-17) — un Important nuevo

Lentes A, B y D sobre el fix1 (`19cffeb..dc733e0`).
- Gaps del intento 1: 1 ✓ · 2 ✓ · 3 ✓ parcial · 4 ✓ · 5 ✓.
- **Ventana inicial sin Critical**: `LIVE` incluye `interrupted` y `queued`, así que el WAV de una generación con un post por reanudar o reencolado se conserva.
- `json_extract` es equivalente al contrato.
- Memoria de los resueltos: unos 0,5 MB con 10⁴.
- Tests: 48 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Con 200 jobs o más que nunca se resuelven (`waiting`/`deferred`), el presupuesto se agota siempre en ellos: los antiguos no se barren nunca y, con `pending>0`, el barrido corre cada 0,1 s en lugar de cada 2 s (~30 % del bucle). Hay causas reales de `waiting` eterno: offload `VRAM_EXCEEDED`, cambio de engine o modelo, carril `remote` | T-17 | corregido (`5ec56c5`) | `cleanup.py:268-270,278-279`; `runtime.py:609-610,44`; bench `rev2/bench2.py` (2000+250: `resolved=0`) |
| 2 | Minor | El test de «beats real» usa la arista beats→generación, pero producción crea beats→post | T-17 | corregido (`5ec56c5`) | `test_tmp_cleanup_t17.py:457-461` frente a `chains.py:133` |
| 3 | Minor | `sweep_cancelled` (la vía de la cancelación CPU) vuelve a registrar los fallos permanentes en cada cancelación | T-17 | corregido (`5ec56c5`) | `execution.py:1486`, `cleanup.py:232-236` |
| 4 | Minor | `sweep_cancelled` mete todos los cancelados en un `IN (...)`; por encima de 32.766 falla con `too many SQL variables` y se salta `_remove_stages` | T-17 | corregido (`5ec56c5`) | `cleanup.py:135-136,151,167`; `execution.py:1485-1490` |
| 5 | Minor (D) | La consulta de ids crece de forma lineal con el histórico, sin índice sobre `status`: 15 ms con 10⁴ y unos 150 ms extrapolados con 10⁵ | T-17 | deuda aceptada: sin migración no es barato (un terminal puede tener un id antiguo); unos 20 ms por pasada con 10⁴ | `cleanup.py:97-100` |

## Revisión de dos lentes — intento 3: Fase 5 (T-17) — sin gaps Critical/Important

Lentes A, B y D sobre el fix2 (`7ba155e..9c147e3`).

- Gaps del intento 2: 1 ✓ · 2 ✓ · 3 ✓ · 4 ✓.
- **`_will_retry` frente a `Retry.eligible`/`reserve`:** no hay ningún caso que borre las entradas de un job que el reintento automático sí va a reservar. `not_before` futuro es conservador; VRAM en bf16 se conserva; VRAM ya en offload no se reintenta nunca.
- `_REPORTED` no oculta fallos nuevos, porque las rutas de `tmp/` no se reutilizan.
- Tests: 148 passed (t17, cancel_cleanup, dispatcher_retry).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | Algunos jobs nunca se reintentarán y aun así quedan aparcados para siempre: VRAM en bf16 sin modo `offload` en el catálogo, engine o modelo retirado del catálogo, o `not_before` ilegible. Su `tmp/` no se limpia nunca. El coste está acotado (≤200 por pasada, sin bucle caliente). Es una decisión explícita y conservadora (docstring `cleanup.py:152-154`) | T-17 | deuda aceptada | `cleanup.py:146-155,243-245` |

## Revisión de dos lentes — intento 1: Fase 4 (T-08) — dos Important pendientes

Lentes A, B y C sobre `main..m1/t-08-web` (`6b4b466..46490f4`). La lente C se activó por la ruta de `.dockerignore` y de `tokens.css` (en este caso, tokens de diseño); no halló nada. La lente D no aplicó.

- **Lente A, ✓:** CA-1, CA-2 (0 cambios rompedores de 12 según `openapi-lint --diff`), CA-3 y CA-4a. CA-5 y CA-6 quedan pendientes de pegar aquí su Verificación.
- **Lente C, sin hallazgos:** `safe_path` y `native_cache` siguen rechazando enlaces y junctions bajo `.cache/swc` y `.cache/la`. Los DTO no exponen rutas del host.
- **Tests de las lentes:**
  - API, 117 passed y 8 skipped;
  - 256 passed y 3 skipped (unload/cancel/retry/create/openapi);
  - vitest de los ficheros nuevos, 53 passed;
  - SWC/cache, 6 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | CA-4b: la página Sistema muestra `engine.state` y los ids de tarea (`ready`, `music.song`) sin traducir | T-08 | corregido (`43f1d3f`) | `apps/web/app/system/page.tsx:53` |
| 2 | Important | Regresión: al mover `LOCALAPPDATA` a `.cache/la`, Playwright ya no encuentra los navegadores instalados en `.cache/web-runtime/local-appdata/ms-playwright` y la Verificación E2E falla con «Executable doesn't exist» | T-08 | corregido (`840a227`) | `scripts/pnpm.py:312`; `chromium.executablePath()` da false con el nuevo `LOCALAPPDATA` y true con el antiguo |
| 3 | Minor | `jobAction` hace un cast a `JobRetryResponse` validando solo que la respuesta sea un objeto: un 202 `{}` deja `take_ids` en undefined en `create/page.tsx:247` | T-08 | corregido (`43f1d3f`) | `apps/web/lib/api.ts:128` |
| 4 | Minor | `es.json` todavía tiene `"submitting": "Encolando?"` | T-08 | corregido (`43f1d3f`) | `apps/web/messages/es.json:65` |
| 5 | Minor | La raíz corta `.t/<1 carácter>` solo admite 16 valores; `mkdir` va sin `exist_ok` y `rmtree` usa `ignore_errors`, así que un resto de una ejecución anterior o dos ejecuciones en paralelo dan `FileExistsError` intermitente | T-08 | corregido (`840a227`) | `tests/test_web_tool_entrypoints.py:23-28` |
| 6 | Minor | El test de claves i18n solo mira `t(` cuando viene de `useTranslations`: una clave que falte en `te(...)` o `tUnits(...)` no lo hace fallar | T-08 | corregido (`43f1d3f`) | `apps/web/lib/i18n-keys.test.ts:21,44` |
| 7 | Minor | `authedGet`, `authedMutation` y `listSongs` devuelven `response.json()` sin validar (el cast implícito de antes) | T-08 | deuda aceptada: el contrato tipado lo cubre en compilación; la validación en runtime de todas las lecturas queda para cuando T-10 a T-12 toquen esas vistas | `apps/web/lib/api.ts:148,158,166,189-199` |
| 8 | Minor | Quedan hex sueltos en `Waveform.tsx:25-27` y `GenerativeViz.tsx:56`; CA-3 solo pedía `globals.css` | T-08 | deuda aceptada: fuera de CA-3; se tratan en T-13 (reproductor) | `apps/web/components/Waveform.tsx:25-27` |

## Revisión de dos lentes — intento 2: Fase 4 (T-08) — sin gaps Critical/Important

Lentes A y B sobre `46490f4..43f1d3f` (commits `840a227` y `43f1d3f`). Las lentes C y D no aplican (`review-lens-select`). `scope-check` sale con exit 0.

- **Gaps del intento 1:** 1 ✓ · 2 ✓ · 3 ✓ · 4 ✓ · 5 ✓ · 6 ✓.
- **Estados del engine:** cubren el `Literal` del contrato (`idle|loading|busy|error`) y el `error` sintético del server. Sobran dos (`ready` y `unavailable`), lo que no es un fallo.
- **`PLAYWRIGHT_BROWSERS_PATH`:** no rompe en un checkout limpio, porque `safe_path` no es estricto con los ancestros que no existen. Además, `chromium.executablePath()` existe.
- **`jobAction`:** no rechaza ninguna respuesta real (`Cancellation.request` y `add_dependents`).
- **Tests de las lentes:**
  - server cancel/retry: 217 passed y 3 skipped;
  - SWC/Playwright: 4 passed;
  - vitest de los tres ficheros tocados: 10 passed.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | En Sistema, toda tarea verificada distinta de `music.song` o `music.instrumental` sale como «Desconocido». Con el mock salen 19 iguales | T-08 | deuda aceptada: el propietario decidió no ampliar Sistema y el M1 recortado solo usa song e instrumental. Se etiquetan cuando M2 active esas tareas | `apps/web/lib/enum-labels.ts:4`; `apps/web/app/system/page.tsx:55` |
| 2 | Minor | Ningún test comprueba que las claves `enums.engineState.*` existan en `es.json`, porque el test de alias salta las llamadas dinámicas `te(...)` | T-08 | deuda aceptada: se cubre al revisar T-09 a T-13, que añaden más etiquetas de estado | `apps/web/lib/i18n-keys.test.ts:56-61` |

