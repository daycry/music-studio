---
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — M1 · MVP del estudio web

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | 2026-09-28 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | n/a |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.
>
> **No se empieza hasta cerrar M0 (T-13).** M1 reutiliza tal cual `packages/engine-contract`, `packages/audio-post`, `packages/weights`, el escritor del manifiesto, `engine-mock`, `engine-acestep` y `engine-analysis`.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Server base | 0 | 3 | 0% | 0 / 20h | 0 / 10h | 0 / 2.5h | 0 / — |
| Fase 2 — Cola y post-proceso | 0 | 3 | 0% | 0 / 26h | 0 / 13h | 0 / 3.3h | 0 / — |
| Fase 3 — API de dominio | 0 | 1 | 0% | 0 / 12h | 0 / 6h | 0 / 1.5h | 0 / — |
| Fase 4 — Web | 0 | 7 | 0% | 0 / 86h | 0 / 43h | 0 / 10.8h | 0 / — |
| Fase 5 — Pruebas y cierre | 0 | 2 | 0% | 0 / 9h | 0 / 4.5h | 0 / 1.1h | 0 / — |
| **TOTAL** | **0** | **16** | **0%** | **0 / 153h** | **0 / 76.5h** | **0 / 19.2h** | **0 / —** |

---

## Fase 1 — Server base

**Estado**: borrador · **Estimado**: 20h · **Real**: —

### T-01 — Esqueleto del server: configuración, seguridad local y logs

- **Descripción**: App FastAPI con la configuración `STUDIO_*`, validación de `Host` y `Origin`, CORS con lista cerrada, errores `problem+json` y logs JSON.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: M0 cerrado
- **Tipo**: backend
- **Archivos**: `apps/server/` (`main.py`, `settings.py`, `errors.py`, `security.py`, `logging.py`), tests
- **Cubre (tests)**: API-01
- **Verificación**:
  - `uv run pytest apps/server -k "security or errors or settings" -q` → verde
  - `curl -s -o /dev/null -w "%{http_code}" -X POST -H "Origin: http://evil.test" http://127.0.0.1:8000/api/songs` → `403`

**Criterios de aceptación**
- [ ] `pydantic-settings` con las variables de [convenciones.md](../../arquitectura/convenciones.md) §4. `STUDIO_ENGINES` se interpreta como un mapa familia→URL.
- [ ] `Host ∈ {127.0.0.1:8000, localhost:8000}` y `Origin == STUDIO_WEB_ORIGIN` en todos los métodos salvo GET/HEAD y en el SSE; en caso contrario, `403 FORBIDDEN_ORIGIN`. CORS con lista cerrada.
- [ ] Errores RFC 9457 con `code` estable. Logs JSON en `data/logs/server.log` con rotación.
- [ ] Token de engines generado en `.env` la primera vez y enviado en `X-Studio-Engine-Token`.

### T-02 — Esquema completo, migración inicial, FTS y backup

- **Descripción**: La primera migración Alembic con **todas** las tablas de [datos.md](../../arquitectura/datos.md) §1, triggers FTS5 y la tarea de backup diario.
- **Estado**: borrador
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 5h · real —
- **Supervisión**: est. 1.3h (≈25 % IA) · real —
- **Dependencias**: T-01
- **Tipo**: db
- **Archivos**: `apps/server/models/`, `apps/server/alembic/versions/0001_initial.py`, `apps/server/backup.py`, `packages/contracts/song-v1.schema.json`, tests
- **Cubre (tests)**: M-03
- **Verificación**:
  - `uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head` → sin errores
  - `uv run pytest apps/server -k "schema or lineage or fts or backup" -q` → verde

**Criterios de aceptación**
- [ ] Tablas: `user` (fila `local`), `collection`, `song`, `lyrics_version`, `take`, `lineage_edge`, `asset`, `upload`, `analysis`, `artwork`, `character`, `character_ref`, `preset`, `video_project`, `video_character`, `shot`, `shot_version`, `render`, `export`, `job`, `job_dependency`, `setting` y `provider`. Todas con ULID, `owner_id`, `created_at`, `updated_at` y `deleted_at`.
- [ ] SQLite en modo WAL con `foreign_keys=ON`. Tabla virtual FTS5 `song_fts`, mantenida por triggers.
- [ ] `song.json` (esquema `song-v1`) se regenera al cambiar la canción y permite reconstruir sus filas.
- [ ] Backup diario con `sqlite3 .backup` en `data/backups/` y rotación de 14 días. Test de restauración.
- [ ] Tests:
  - un take derivado tiene una arista en `lineage_edge` y un `root_id` correcto;
  - varios padres (crossfade);
  - papelera sin romper a los hijos;
  - FTS por letra.

### T-03 — Contratos exportados y parser de letras compartido

- **Descripción**: `openapi.json` code-first versionado, generación de tipos TypeScript y parser de etiquetas en Python y TS sobre los mismos casos.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `scripts/export_contracts.py`, `packages/contracts/openapi.json`, `packages/contracts/lyrics-cases.json`, `apps/server/lyrics.py`, `apps/web/lib/lyrics.ts`, tests
- **Cubre (tests)**: E2E-03, API-02
- **Verificación**:
  - `uv run scripts/export_contracts.py --check` → `openapi.json up to date · engine-v1.json up to date`
  - `uv run pytest apps/server -k lyrics -q` → verde · `pnpm --filter web test lyrics` → verde

**Criterios de aceptación**
- [ ] `export_contracts.py` genera `openapi.json` desde FastAPI; un test falla si el fichero versionado difiere del generado.
- [ ] `pnpm gen` genera los tipos de la web (`openapi-typescript`).
- [ ] `lyrics-cases.json` cubre etiquetas válidas e inválidas, secciones vacías, mayúsculas y alias en castellano (`[estribillo]` → `[chorus]`). Los dos parsers pasan exactamente los mismos casos.

---

## Fase 2 — Cola y post-proceso

**Estado**: borrador · **Estimado**: 26h · **Real**: —

### T-04 — Dispatcher: carriles, prioridades, dependencias, reintentos y recuperación

- **Descripción**: La cola de [ADR-0018](../../decisiones/ADR-0018-cola-de-jobs.md) sobre la tabla `job`, con el cliente del contrato `/v1`.
- **Estado**: borrador
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 7h · real —
- **Supervisión**: est. 1.8h (≈25 % IA) · real —
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `apps/server/queue/` (dispatcher, `backends/` con el protocolo `EngineBackend` y `HttpEngineBackend`, `resolver`), tests
- **Cubre (tests)**: E2E-01, E2E-04, E2E-05, E2E-06, E2E-09, M-01
- **Verificación**:
  - `uv run pytest apps/server -k "dispatcher or queue" -q` → verde con `engine-mock`: éxito, error `retryable` reintentado, error no reintentable, cancelación, reinicio a mitad (`interrupted` → reencolado), dependencia `blocked`→`succeeded` y dependencia fallida → `DEPENDENCY_FAILED`

**Criterios de aceptación**
- [ ] Carriles `gpu` (1) y `cpu` (2). La columna `lane=remote` existe, pero sin adapters todavía. Prioridad y después FIFO. `not_before` se respeta. Las tareas con `device: cpu` en el descriptor (`audio.beats`) van por el carril `cpu` y no descargan la GPU.
- [ ] El dispatcher solo habla con el protocolo **`EngineBackend`** (`health`, `models`, `load`, `unload`, `estimate`, `submit`, `events`, `cancel`). `HttpEngineBackend` implementa `/v1`, y en M2 los adapters externos entrarán sin tocar el dispatcher.
- [ ] **Cadena de jobs por petición** ([sistema.md](../../arquitectura/sistema.md) §3): generación (N salidas, `seed + i`) → `post.audio` (cpu) → un `audio.beats` por take, creados en `blocked` y con sus `inputs` como referencias que se resuelven al desbloquear.
- [ ] El resolver elige engine y modelo por **tarea verificada** en los descriptores (`GET /v1/models` en caché).
- [ ] Antes de despachar a otro engine: `POST /v1/unload` al que tiene el modelo cargado y comprobación de `free_mb` en `/v1/health`.
- [ ] Consume el NDJSON con reenganche por `seq`. Actualiza `stage`, `progress` y `telemetry`, y publica los eventos en el bus interno del SSE.
- [ ] Reintentos solo si el error es `retryable`, con un máximo de 2. `VRAM_EXCEEDED` se reintenta una vez en modo `offload` si existe.
- [ ] Recuperación al arrancar según ADR-0018: se reenvía **el mismo `job_id`** y el dispatcher se reengancha si el engine lo conserva. Reintento manual: job nuevo que reutiliza los takes `failed`. Variantes en batch o en serie según I-01 (benchmark de M0).

### T-05 — Worker CPU: post-proceso, manifiesto, traslado y análisis dependiente

- **Descripción**: El carril `cpu` que convierte la salida cruda en takes `ready` ([ADR-0017](../../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)).
- **Estado**: borrador
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `apps/server/worker/`, tests
- **Cubre (tests)**: E2E-01, E2E-09, M-01
- **Verificación**:
  - `uv run pytest apps/server -k worker -q` → verde
  - `uv run scripts/verify_manifest.py data/songs/` → `all valid` (tras un E2E)

**Criterios de aceptación**
- [ ] Ejecuta `audio-post` con el ffmpeg de `tools/`. Mueve el resultado de forma atómica a `data/songs/<song>/takes/<take>/`. Registra los `asset` y escribe el manifiesto v1 `audio_take`.
- [ ] Marca el take `ready`, regenera `song.json` y desbloquea el job `audio.beats` dependiente, cuyo resultado se guarda como fila `analysis(kind=beats)`.
- [ ] Limpia `data/tmp/<job_id>/`. Si el post-proceso falla (validación), el take queda `failed` con su `code`.

### T-06 — SSE de eventos

- **Descripción**: `GET /api/events` según [convenciones.md](../../arquitectura/convenciones.md) §3.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `apps/server/events.py`, tests
- **Cubre (tests)**: E2E-01, E2E-06
- **Verificación**:
  - `uv run pytest apps/server -k sse -q` → verde (reconexión con `Last-Event-ID` sin perder eventos)

**Criterios de aceptación**
- [ ] Sobre de evento `{id: seq, type, ts, data}` con los tipos `job.*`, `entity.updated` y `system.status`. Keep-alive cada 15 s.
- [ ] `Last-Event-ID` reenvía los eventos perdidos desde un buffer. Si el buffer se agotó, envía el estado actual de los jobs activos.

---

## Fase 3 — API de dominio

**Estado**: borrador · **Estimado**: 12h · **Real**: —

### T-07 — API: canciones, letras, generaciones, takes, colecciones, modelos y sistema

- **Descripción**: Los endpoints de M1 de [sistema.md](../../arquitectura/sistema.md) §5.
- **Estado**: borrador
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-04, T-05
- **Tipo**: backend
- **Archivos**: `apps/server/api/` (`songs`, `lyrics`, `generations`, `takes`, `collections`, `jobs`, `models`, `system`), tests
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

**Estado**: borrador · **Estimado**: 86h · **Real**: —

### T-08 — Web: esqueleto, tokens, temas, i18n, layout y cliente de API

- **Descripción**: Base de `apps/web` según [ux.md](../../producto/ux.md) §2–§3.
- **Estado**: borrador
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 7h · real —
- **Supervisión**: est. 1.8h (≈25 % IA) · real —
- **Dependencias**: T-03
- **Tipo**: frontend
- **Archivos**: `apps/web/` (App Router, Tailwind, shadcn/ui, next-intl, `styles/tokens.css`, `lib/api.ts`, `lib/events.ts`), `apps/web/messages/es.json`, `apps/web/playwright.config.ts`, `apps/web/e2e/fixtures/`, `scripts/e2e_stack.py` (levanta server en modo prueba + engine-mock + seed), `apps/server/scripts/seed_e2e.py`
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

### T-09 — Crear: editor de letra, estilo, autoría, avanzado y variantes

- **Descripción**: El panel de creación de [ux.md](../../producto/ux.md) §4.1 (modo personalizado).
- **Estado**: borrador
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

### T-10 — Tarjeta de generación y feed A/B

- **Descripción**: La firma visual de [ux.md](../../producto/ux.md) §4.2.
- **Estado**: borrador
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
- [ ] `GenerativeViz` en canvas de 96 columnas, movida **solo** por el progreso real. Al terminar se transforma en los picos reales. Un único rAF, 30 fps como máximo, en pausa fuera del viewport.
- [ ] Stepper con las etapas que envía el engine. La etapa «Modelo» solo aparece si hay que cargar el modelo.
- [ ] Feed con las variantes agrupadas. Error en la tarjeta con `code`, `job_id` y botón de reintentar. Cancelar desde la tarjeta.

### T-11 — Biblioteca de canciones

- **Descripción**: [ux.md](../../producto/ux.md) §4.3.
- **Estado**: borrador
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
- [ ] Vistas en grid y en lista, búsqueda, filtros, scroll infinito con skeletons y estado vacío con llamada a la acción.
- [ ] Preescucha del maestro (400 ms de espera, 10 s, se puede desactivar). Miniatura de la visualización en las canciones que están generando.
- [ ] Papelera con restaurar y purgar.

### T-12 — Vista de canción (Audio y Letra)

- **Descripción**: [ux.md](../../producto/ux.md) §4.4, pestañas Audio y Letra. Las demás pestañas aparecen deshabilitadas con su hito.
- **Estado**: borrador
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
- [ ] Lista de takes con valoración, etiqueta y **marcar maestro**. Cabecera con título, artista, estado, BPM y maestro.
- [ ] `Waveform` sobre wavesurfer.js alimentado con `peaks.json`: seek, zoom, marcas de beat y el plugin Regions ya cargado para M2.
- [ ] Pestaña Letra: versiones, diferencias y qué takes cantaron cada una.
- [ ] `ProvenancePanel` siempre visible, con los hashes copiables y exportación a JSON. Descarga en MP3 y FLAC.

### T-13 — Reproductor persistente, cola y atajos

- **Descripción**: [ux.md](../../producto/ux.md) §4.10 y §5.
- **Estado**: borrador
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
- [ ] El reproductor persiste al navegar. Cola reordenable. `⏭` sobre una variante salta a su pareja.
- [ ] Atajos de §5 y hoja de ayuda con `?`. Onda con `role="slider"` operable con el teclado.

### T-14 — Colecciones y página Sistema

- **Descripción**: CRUD de colecciones en la UI y [ux.md](../../producto/ux.md) §4.9.
- **Estado**: borrador
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
- [ ] Colecciones: crear, renombrar y mover canciones, individualmente o en lote. Filtro por colección.
- [ ] Sistema: GPU, VRAM (total, libre y tope), RAM, engines, modelos con sus tareas verificadas, licencia y hash ✓, cola y disco. Botón para descargar el modelo.

---

## Fase 5 — Pruebas y cierre

**Estado**: borrador · **Estimado**: 9h · **Real**: —

### T-15 — Suite E2E (Playwright + engine-mock)

- **Descripción**: Completar y estabilizar la suite: los E2E que no haya escrito ya su tarea web (E2E-06 recuperación, API-01/02), eliminar la inestabilidad y dejar la suite en verde.
- **Estado**: borrador
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
- [ ] Un spec por bloque E2E-xx con sus aserciones, y seed reproducible.
- [ ] Tres ejecuciones seguidas en verde.

### T-16 — README de puesta en marcha y cierre del hito

- **Descripción**: Dejar el proyecto arrancable desde cero (engines en Docker, server y web en nativo) y cerrar M1 con evidencias. El perfil «todo en contenedores» queda fuera de M1 (ver Notas).
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Supervisión**: est. 0.4h (≈25 % IA) · real —
- **Dependencias**: T-15
- **Tipo**: devops
- **Archivos**: `README.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md`
- **Cubre (tests)**: M-01, M-03
- **Verificación**:
  - lectura: seguir el README desde un clon limpio lleva a la app funcionando
  - lectura: M-01 (generación real con GPU) y M-03 (backup y restauración) hechos y anotados

**Criterios de aceptación**
- [ ] README de puesta en marcha según [entorno.md](../../arquitectura/entorno.md) §5.
- [ ] Todos los CA de la spec verificados con evidencia; spec en `implementada` tras la retro del plugin.

**Notas**: un perfil «todo en contenedores» (server en Linux) obliga a resolver tres cosas que no hacen falta en M1: ffmpeg Linux en la imagen del server, `STUDIO_ENGINES` con nombres de servicio en vez de 127.0.0.1, y `STUDIO_ALLOWED_HOSTS` configurable. Se abre como tarea propia si se necesita (p. ej. para el futuro acceso por LAN).
