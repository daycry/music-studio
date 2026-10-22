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
- **Archivos**: `apps/server/app/worker/publications.py`, `apps/server/app/worker/execution.py`, `apps/server/tests/test_worker_*.py`, `pyproject.toml` (marcador de pytest)
- **Verificación**:
  - Windows: `uv run pytest apps/server/tests -m "not gpu"` → **0 failed, 0 errors** (los tests Linux-only aparecen como `skipped` con motivo).
  - Docker: `docker compose run --rm server uv run pytest apps/server/tests -m "not gpu" -k "worker or publication"` en verde, incluidos los tests nativos Linux.
  - Punta a punta: `scripts/e2e_stack.py up` y una generación con `engine-mock` deja el take `ready` en `data/songs/` sobre el bind de Windows · `uv run scripts/verify_manifest.py data/songs/` en verde · `scripts/e2e_stack.py restart-server` a mitad del post-proceso no deja `.pending-*` huérfanos.

**Criterios de aceptación**
- [ ] CA-1: la publicación funciona donde `renameat2(NOREPLACE)` devuelve `EINVAL`/`ENOSYS`, con un fallback de comprobación de ausencia más `rename`. Un test simula `EINVAL` y comprueba que el take se publica.
- [ ] CA-2: se mantiene el no-clobber. Un destino ajeno existente (fichero, directorio o directorio vacío) se rechaza sin tocarlo, con y sin fallback, y el cross-device se rechaza antes del rename (los tests `test_native_noreplace_preserves_foreign_destination*` y `test_native_publication_rejects_cross_device_before_rename` pasan, adaptados si hace falta).
- [ ] CA-3: al arrancar, los directorios `takes/.pending-<execution>/` de ejecuciones no confirmadas se eliminan y el `post.audio` interrumpido puede reintentarse (automático o con el reintento manual existente) hasta dejar el take en `ready`.
- [ ] CA-4: los tests que exigen Linux real o el arnés de custodia Windows de Codex (`CUSTODY_SOURCE_SHA256`) se marcan con un marcador explícito y se saltan con motivo cuando no aplican, en lugar de fallar o dar error.
- [ ] CA-5: verificación de punta a punta en Docker con `engine-mock` (bloque **Verificación**).
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
