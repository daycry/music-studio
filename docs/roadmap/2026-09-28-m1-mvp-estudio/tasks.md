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
| Fase 5 — Pruebas y cierre | 0 | 2 | 0% | 0 |
| **TOTAL** | **0** | **17** | **0%** | **2** |

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
- **Descripción**: **Recortado.** Un carril GPU y uno CPU, reintento `retryable` ×2, cancelar, e `interrupted` → reencolar al arrancar. Las dependencias entre jobs (análisis) quedan fuera.
- **Deuda de la revisión de T-05 (gap 6)**: `reconcile_startup` vuelve a procesar en cada arranque las ejecuciones ya `interrupted`.
- **Pendiente heredado de T-05**: reencolar el `post.audio` interrumpido tras un reinicio (hoy queda `interrupted`/`CPU_CUSTODY_UNKNOWN` sin camino de vuelta). Hay que decidir entre reutilizar `cpu_execution` y la intent o abrir el ordinal 2.
- **Estado**: en-progreso
- **Dependencias**: T-02
- **Archivos**: `apps/server/app/queue/`
- **Verificación**: `uv run pytest apps/server/tests -k "queue or dispatcher or retry or recovery or cancel" -m "not gpu"` en verde.

### T-05 — Post-proceso y publicación sencilla de takes
- **Descripción**: **Rediseño (ADR-0089 §2).** Hoy la publicación final (`publications.py::rename_noreplace`) exige `renameat2(RENAME_NOREPLACE)`, que devuelve `EINVAL` sobre el bind 9p de Docker Desktop, y por eso ningún take llega a `ready` en el despliegue real. Se sustituye por una publicación sencilla:
  - el destino `data/songs/<song>/takes/<take_ulid>` es único por construcción;
  - se usa `renameat2` si el filesystem lo soporta y, si devuelve `EINVAL`/`ENOSYS`, comprobación de ausencia más `os.rename`;
  - la fila SQLite sigue siendo la autoridad;
  - al arrancar se limpian los staging huérfanos.

  Fuera de alcance: simplificar la custodia de procesos (`custody_*`, `pipe_protocol`), que funciona y no bloquea. `packages/storage-guard` se mantiene opcional (solo con `STUDIO_STORAGE_UUID`).
- **Estado**: en-progreso
- **Tipo**: backend
- **Dependencias**: T-04
- **Archivos**: `apps/server/app/worker/publications.py`, `apps/server/app/worker/execution.py`, `apps/server/tests/test_worker_*.py`, `apps/server/tests/conftest.py` y `pytest.ini` (marcadores de CA-4), `apps/server/tests/fixtures/creative/fixture-index.json` (hash LF del esquema, `406f259`)
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → **0 failed, 0 errors** (los tests Linux-only aparecen como `skipped` con motivo).
  - Docker: `docker compose run --rm server uv run pytest apps/server/tests -m "not gpu" -k "worker or publication"` en verde, incluidos los tests nativos Linux.
  - Punta a punta: `scripts/e2e_stack.py up` y una generación con `engine-mock` deja el take `ready` en `data/songs/` sobre el bind de Windows · `uv run scripts/verify_manifest.py data/songs/` en verde · `scripts/e2e_stack.py restart-server` a mitad del post-proceso no deja `.pending-*` huérfanos.

**Criterios de aceptación**
- [x] CA-1: la publicación funciona donde `renameat2(NOREPLACE)` devuelve `EINVAL`/`ENOSYS`, con un fallback de comprobación de ausencia más `rename`. Un test simula `EINVAL` y comprueba que el take se publica.
- [ ] CA-2: se mantiene el no-clobber. Un destino ajeno existente (fichero, directorio o directorio vacío) se rechaza sin tocarlo, con y sin fallback, y el cross-device se rechaza antes del rename (los tests `test_native_noreplace_preserves_foreign_destination*` y `test_native_publication_rejects_cross_device_before_rename` pasan, adaptados si hace falta).
- [x] CA-3: al arrancar, se eliminan los directorios `takes/.pending-<execution>/` de las ejecuciones no confirmadas. *(Reducido el 2026-10-22: reencolar un `post.audio` interrumpido exige cambiar la máquina de estados (`claim_job` solo acepta `queued`/`attempt=0`, más `UNIQUE(job_id, ordinal)` y `UNIQUE(take_id)` en la intent). Ese trabajo pasa a **T-04**, que ya cubre «interrupted → reencolar».)*
- [x] CA-4: los tests que exigen Linux real o el arnés de custodia Windows de Codex (`CUSTODY_SOURCE_SHA256`) se marcan con un marcador explícito y se saltan con motivo cuando no aplican, en lugar de fallar o dar error.
- [ ] CA-5: verificación de punta a punta en Docker con `engine-mock` (bloque **Verificación**).
- **RED → GREEN** (2026-10-22, implementer):
  - RED: `test_worker_publication_fallback.py` → 6 failed (`AttributeError: _native_noreplace`). GREEN: 6 passed.
  - RED: `test_worker_startup_staging.py::test_startup_removes_orphan_pending_staging` falló porque `.pending-<exec>` seguía existiendo. GREEN: con `test_dispatcher_cpu_worker.py`, 7 passed.
- **Verificación parcial** (Windows, 2026-10-22):
  - `uv run pytest apps/server/tests -m "not gpu"` → `1 failed, 2526 passed, 73 skipped in 708s`. El fallo era el hash CRLF del índice de fixtures creativo, corregido en `406f259`: `test_creative_contract_compatibility.py` da 69 passed.
  - Los 4 fallos y 68 errores del worker de la línea base pasan a `skipped` con motivo (`linux_real` / `custody_harness`).
  - **Pendiente:** la parte en Docker (los tests nativos de Linux de CA-2 y el recorrido de punta a punta de CA-5). Docker Desktop está parado.
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
- **Archivos**: `apps/server/app/sse.py`, `apps/server/app/event_routes.py`
- **Verificación**: `uv run pytest apps/server/tests -k sse -m "not gpu"` en verde.

## Fase 3 — API

### T-07 — API mínima: canciones, letras, generaciones, takes y sistema
- **Descripción**: **Recortado.** CRUD de canciones con papelera simple, versiones de letra, `POST` de generaciones, takes (valorar y marcar maestro), descargas MP3/FLAC y `GET /system` mínimo. Las colecciones quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-04, T-05
- **Archivos**: `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`
- **Verificación**: `uv run pytest apps/server/tests -k "routes or api" -m "not gpu"` en verde · `openapi.json` regenerado sin diferencias.

## Fase 4 — Web

### T-08 — Web: esqueleto, tokens, tema oscuro, i18n, layout y cliente de API
- **Descripción**: Next.js con `next-intl` (castellano), tokens de diseño, layout y cliente generado desde `openapi.json`. El tema claro queda fuera.
- **Estado**: en-progreso
- **Dependencias**: T-03
- **Verificación**: `pnpm lint` y `pnpm test` en verde · `pnpm --filter web build` sin errores.

### T-09 — Crear: letra, estilo, autoría y avanzado
- **Descripción**: Editor de letra con validación en vivo, estilo, autoría obligatoria, instrumental y avanzado según el `params_schema`. Chips y estilos a excluir quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-08, T-07
- **Verificación**: `pnpm test` en verde (unitarios del formulario) y E2E-crear de T-15.

### T-10 — Tarjeta de generación en vivo
- **Descripción**: La tarjeta muestra las etapas por SSE, los errores con `code`, `job_id` y reintentar, y la onda al terminar. El feed A/B queda fuera.
- **Estado**: en-progreso
- **Dependencias**: T-09, T-06
- **Verificación**: E2E-generar de T-15 contra `engine-mock`.

### T-11 — Biblioteca de canciones
- **Descripción**: Lista con búsqueda FTS y preescucha del maestro. Grid, filtros avanzados y papelera en la UI quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-07, T-08
- **Verificación**: E2E-biblioteca de T-15.

### T-12 — Vista de canción
- **Descripción**: Takes con valoración y maestro, onda con seek, letra y descarga MP3/FLAC.
- **Estado**: en-progreso
- **Dependencias**: T-11
- **Verificación**: E2E-cancion de T-15.

### T-13 — Reproductor persistente
- **Descripción**: El reproductor sobrevive a la navegación. La cola y los atajos quedan fuera.
- **Estado**: en-progreso
- **Dependencias**: T-08
- **Verificación**: E2E-reproductor de T-15.

### T-14 — Colecciones y página Sistema
- **Descripción**: Aplazada (ADR-0089); el código parcial se conserva.
- **Estado**: cancelado
- **Dependencias**: T-07, T-08
- **Verificación**: n/a (cancelada).

## Fase 5 — Pruebas y cierre

### T-15 — Suite E2E del camino mínimo (Playwright + engine-mock)
- **Descripción**: E2E de crear, generar, biblioteca, canción, reproductor y errores contra `engine-mock` (actualizar `test-plan.md` al recorte).
- **Estado**: en-progreso
- **Dependencias**: T-09 a T-13
- **Verificación**: `pnpm --filter web exec playwright test` en verde; informe de `qa` con 0 fallos.

### T-16 — Prueba real con ACE-Step, README y cierre
- **Descripción**: Canción real generada desde la web con ACE-Step (modelo de M0/T-13), escuchada por el propietario, y README de puesta en marcha.
- **Estado**: en-progreso
- **Dependencias**: T-15, M0/T-13
- **Verificación**: take real `ready` con manifiesto válido, escuchado y aceptado por el propietario · README seguido desde cero.

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
