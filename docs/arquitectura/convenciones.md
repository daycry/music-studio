---
documento: convenciones
titulo: Convenciones de código, API y proceso
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Convenciones

## 1. Idioma

| Qué | Idioma |
|---|---|
| Documentación, UI (vía `next-intl`), commits, comentarios de producto | **Castellano** |
| Identificadores de código, tablas y columnas, rutas de API, campos JSON, tipos de evento, códigos de error, nombres de fichero | **Inglés** (`song`, `take`, `master_take_id`, `job.progress`) |

## 2. Datos y unidades

- **IDs:** ULID en texto (26 caracteres), generados por el server.
- **Fechas:** ISO-8601 en UTC con milisegundos (`2026-10-02T18:22:11.123Z`).
- **Tiempo de audio y vídeo:** segundos en `float`. Los fps se guardan como racional (`"24000/1001"`).
- **Loudness:** LUFS y dBTP. **Tamaños:** bytes (`int`).
- **Rutas guardadas:** siempre relativas a `data/` y con `/` (`songs/01JA…/takes/01JB…/master.flac`). El server las resuelve a `C:\…\data\…` y el engine a `/data/…`. Nunca se guardan rutas absolutas.

## 3. API del server (`/api`)

- `/api` no lleva versión (hay un único cliente). El contrato de los engines sí: `/v1` ([contrato-engines.md](./contrato-engines.md)).
- **Errores:** RFC 9457 `application/problem+json` → `{type, title, status, detail, code, job_id?, field?}`. El `code` es estable, en inglés y en MAYÚSCULAS (`LYRICS_DECLARATION_REQUIRED`, `RIGHTS_DECLARATION_REQUIRED`, `CAPABILITY_UNAVAILABLE`, `QUEUE_FULL`, `NOT_FOUND`, `CONFLICT`…).
- **Paginación** por cursor: `GET …?cursor=&limit=` → `{items: [...], next_cursor: str|null}`.
- **Concurrencia optimista** en recursos editables grandes (timeline, letra): campo `rev` e `If-Match` / `409 CONFLICT`.
- **SSE** (`GET /api/events`):
  - Formato de cada evento: `{id: seq, type, ts, data}`. Admite `Last-Event-ID` para reanudar.
  - Tipos genéricos: `job.created`, `job.stage`, `job.progress`, `job.delta`, `job.done`, `job.failed`, `job.cancelled`, `entity.updated {type, id}`, `system.status`.
- **OpenAPI code-first:** FastAPI genera `openapi.json`, que se versiona en `packages/contracts/openapi.json`. Un test falla si el fichero versionado no coincide con el generado. Los tipos TypeScript de la web se generan desde ese fichero con `pnpm gen` ([ADR-0019](../decisiones/ADR-0019-contratos-code-first.md)).

## 4. Configuración

- Todas las variables llevan el prefijo **`STUDIO_`**. Se leen de `.env` (git-ignored) con `pydantic-settings`. `.env.example` se versiona.
- Variables clave: `STUDIO_DATA_DIR=./data`, `STUDIO_MODELS_DIR=./models`, `STUDIO_ENGINES=…` (mapa familia=url), `STUDIO_VRAM_MARGIN_MB=512`, `STUDIO_NIGHTLY_WINDOW=01:00-07:00`, `STUDIO_WEB_ORIGIN=http://127.0.0.1:3000`, `STUDIO_PROVIDER_<NOMBRE>_API_KEY` (solo si se activa un proveedor externo).
- **Python aislado del de la máquina:** nunca se instala nada en el Python del sistema. El intérprete (3.12, gestionado por uv) vive en `.cache/uv/python/` y el entorno en `.venv/`, ambos dentro de la carpeta.
  - `uv.toml` (versionado) fija `cache-dir = .cache/uv`, `python-preference = only-managed` y `python-downloads = manual`: uv nunca usa el Python de la máquina ni descarga intérpretes a `%APPDATA%` por su cuenta.
  - `scripts/env.ps1` (PowerShell: `. .\scripts\env.ps1`) y `scripts/env.sh` (bash: `source scripts/env.sh`) fijan lo que `uv.toml` no admite: `UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_INSTALL_BIN=0` (sin accesos directos en `%USERPROFILE%\.local\bin`), `UV_PROJECT_ENVIRONMENT`, `HF_HOME`, `TORCH_HOME` y `PNPM_STORE_DIR`, y activan `.venv`. **Todo comando de desarrollo se ejecuta con ese entorno cargado.**
  - Sin esto se descargan gigas a `%USERPROFILE%` ([ADR-0005](../decisiones/ADR-0005-todo-en-la-carpeta.md)).
- En ejecución normal, los engines corren con `HF_HUB_OFFLINE=1` y `TRANSFORMERS_OFFLINE=1`. Las descargas solo ocurren en `scripts/fetch_models.py`.

## 5. Seguridad local ([ADR-0020](../decisiones/ADR-0020-seguridad-local.md))

- El server valida `Host ∈ {127.0.0.1:8000, localhost:8000}` (protege contra DNS rebinding) y `Origin == STUDIO_WEB_ORIGIN` en todo método que no sea GET (protege contra CSRF). CORS con una lista cerrada.
- Los engines se publican solo en `127.0.0.1` y exigen la cabecera `X-Studio-Engine-Token` con el valor de `STUDIO_ENGINE_TOKEN`: un secreto **persistente** en `.env`, generado una sola vez por `scripts/init_env.py` y compartido por el CLI, el server y los engines. No cambia entre arranques.
- Las subidas se validan por contenido real (ffprobe o Pillow), no por extensión. Límites: audio 50 MB / 10 min, imagen 20 MB / 8192 px.

## 6. Logs

JSON en `data/logs/<proceso>.log`, rotación diaria y 14 días de retención. Cada línea lleva `ts`, `level`, `proc`, `job_id?`, `song_id?` y `msg`. No se registran letras completas ni rutas de fotos de personas reales (solo sus IDs).

## 7. Git y proceso

- La rama `main` siempre funciona. Se trabaja en una rama por tarea: `m0/t-04-engine-common`, `fix/<slug>`, `docs/<slug>`.
- **Commits** en castellano con el formato Conventional Commits y la tarea al final: `feat(server): dispatcher con cancelación [M1/T-04]`.
- **Remoto privado** como copia de seguridad del código (GitHub privado u otro). El `.git` sincronizado por Synology **no** se considera copia fiable. El nombre del repositorio no incluye marcas de terceros ([gate GC-f](../legal/comercializacion.md)).
- **Definition of Done de una tarea:**
  1. Criterios de aceptación marcados, cada uno con su evidencia.
  2. La `Verificación` de la tarea ejecutada y su salida pegada en el ledger.
  3. `uv run pytest -m "not gpu"` en verde en los paquetes Python que toque.
  4. `pnpm lint && pnpm test` en verde si toca la web; los E2E si toca un flujo de UI.
  5. ADR y documentos actualizados si la tarea cambia algo ya documentado.
  6. Contratos regenerados (`openapi.json`, `engine-v1.json`) sin diferencias pendientes.
- Los hitos se implementan con `/dev-cycle` del plugin custom-agents (ver [roadmap/README.md](../roadmap/README.md) §Cómo implementar).
