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
  - `scripts/env.ps1` (PowerShell: `. .\scripts\env.ps1`) y `scripts/env.sh` (bash: `source scripts/env.sh`) fijan lo que `uv.toml` no admite: `UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_INSTALL_BIN=0` (sin accesos directos en `%USERPROFILE%\.local\bin`), `UV_PROJECT_ENVIRONMENT`, `HF_HOME`, `TORCH_HOME` y `npm_config_store_dir`, y activan `.venv`. **Todo comando de desarrollo se ejecuta con ese entorno cargado.**
  - Sin esto se descargan gigas a `%USERPROFILE%` ([ADR-0005](../decisiones/ADR-0005-todo-en-la-carpeta.md)).
- En ejecución normal, los engines corren con `HF_HUB_OFFLINE=1` y `TRANSFORMERS_OFFLINE=1`. Las descargas solo ocurren en `scripts/fetch_models.py`.

## 5. Seguridad local ([ADR-0020](../decisiones/ADR-0020-seguridad-local.md))

- El server valida `Host` contra la lista cerrada de loopback y servicios internos autorizados; un Host único y bien formado ajeno recibe403. Los mensajes HTTP mal formados rechazados antes de ASGI reciben400 según RFC9112 ([ADR-0040](../decisiones/ADR-0040-frontera-parser-http-y-aplicacion.md)). Todo Origin presente debe ser el único `STUDIO_WEB_ORIGIN`; un Origin ajeno o duplicado recibe403 en cualquier método. GET/HEAD ordinarios pueden omitir Origin; SSE y los demás métodos lo exigen. CORS mantiene una lista cerrada ([ADR-0038](../decisiones/ADR-0038-rechazo-explicito-host-origin.md)).
- Los engines se publican solo en `127.0.0.1` y exigen la cabecera `X-Studio-Engine-Token` con el valor de `STUDIO_ENGINE_TOKEN`: un secreto **persistente** en `.env`, generado una sola vez por `scripts/init_env.py` y compartido por el CLI, el server y los engines. No cambia entre arranques.
- Las subidas se validan por contenido real (ffprobe o Pillow), no por extensión. Límites: audio 50 MB / 10 min, imagen 20 MB / 8192 px.

## 6. Logs

JSON en `data/logs/<proceso>.log`, rotación diaria y 14 días de retención. Cada línea lleva `ts`, `level`, `proc`, `job_id?`, `song_id?` y `msg`. No se registran letras completas ni rutas de fotos de personas reales (solo sus IDs).

La preparación de instrucciones de M0 guarda originales, texto efectivo y diffs en recibos privados dentro de `data/preparations/` ([ADR-0028](../decisiones/ADR-0028-preparacion-fiel-de-instrucciones.md)). No se versionan esos textos ni se copian a logs o informes públicos. Un hash de bytes del archivo original y un hash de texto UTF-8 efectivo son conceptos distintos; la procedencia debe identificarlos por separado. La preparación offline no se presenta como validación de tokens ni como prueba de cumplimiento musical.

## 7. Git y proceso

- La rama `main` siempre funciona. Se trabaja en una rama por tarea: `m0/t-04-engine-common`, `fix/<slug>`, `docs/<slug>`. Al cerrar la tarea: **merge fast-forward a `main` sin PR** y push (rebase antes si `main` avanzó) ([ADR-0021](../decisiones/ADR-0021-repositorio-publico.md)).
- **Commits** en castellano con el formato Conventional Commits y la tarea al final: `feat(server): dispatcher con cancelación [M1/T-04]`.
- **Remoto:** `https://github.com/daycry/music-studio`, **público** ([ADR-0021](../decisiones/ADR-0021-repositorio-publico.md)); git se autentica con `gh` (helper local del repo). Es la copia de seguridad del código: el `.git` sincronizado por Synology **no** se considera copia fiable. Al ser público, antes de cada push se comprueba que no entra nada de `.env`, `data/` ni `models/`. El nombre y la descripción no incluyen marcas de terceros ([gate GC-f](../legal/comercializacion.md)).
- **Definition of Done de una tarea:**
  1. Criterios de aceptación marcados, cada uno con su evidencia.
  2. La `Verificación` de la tarea ejecutada y su salida pegada en el ledger.
  3. `uv run pytest -m "not gpu"` en verde en los paquetes Python que toque.
  4. `pnpm lint && pnpm test` en verde si toca la web; los E2E si toca un flujo de UI.
  5. ADR y documentos actualizados si la tarea cambia algo ya documentado.
  6. Contratos regenerados (`openapi.json`, `engine-v1.json`) sin diferencias pendientes.
- Los hitos se implementan con `/dev-cycle` del plugin custom-agents (ver [roadmap/README.md](../roadmap/README.md) §Cómo implementar).


## SSE: replay y recuperación de estado

[ADR-0056](../decisiones/ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md) decide ampliar el bus existente con buffer256, epoch y secuencia global, suscriptores acotados y reset/snapshot autorizado desde SQLite cuando el cursor expira o hay un hueco de publicación. La secuencia del stream no sustituye la del intento de engine. El body mantiene id numérico positivo seguro y el identificador SSE incluye epoch; keep-alive15s sin avance de progreso. Desconectar al lector no cancela su job.

La primera unidad implementará sólo bus y framing. Antes del endpoint se validarán OpenAPI, pertenencia y credencial pública dedicada, sin reutilizar engine_token ni poner tokens en URL. La barrera de escritores/snapshot, el cliente y E2E siguen pendientes. O1 no promete historia durable de todos los progress después del reinicio; recupera el estado real. No Kafka/Redis ni nueva tabla.


### Sesión pública local de eventos (ADR-0058)

La integración prevista utiliza bootstrap automático con Origin/Host locales y header no simple; una credencial efímera pública en memoria autoriza SSE mediante header, nunca URL ni token de engines. Registro/DTOs preceden a HTTP/CORS/contrato y cliente; esta decisión no acredita endpoints implementados. [Decisión](../decisiones/ADR-0058-sesion-publica-local-para-eventos.md).

## Almacenamiento operativo persistente (ADR-0069)

[ADR-0069](../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md)
fija ext4 respaldado por `data/_storage/studio-data.vhdx`, dentro del
proyecto. Server y engines comparten la misma raíz lógica montada; sus
paths de dominio/manifiestos siguen relativos. El punto de montaje WSL es
una vista virtual, no persistencia adicional fuera del proyecto. Código,
modelos y herramientas conservan sus ubicaciones.

La provisión de plataforma requiere privilegios de montaje; el server no
recibe SYS_ADMIN, loop ni socket Docker. Sin mount/UUID correcto o sin
NOREPLACE nativo, startup aborta antes de publicar. No hay fallback a
rename ordinario, directorio parcial, tmpfs o volumen externo. La biblioteca
NTFS existente no se migra ni se borra automáticamente. Acceso Windows y
verificadores usan la vista WSL/Docker o exportación explícita al proyecto.
Backup de VHDX requiere quiesce/flush/detach propios; no copiarlo activo ni
parar servicios ajenos. Implementación y QA persistente siguen pendientes.


Los formatos nuevos de producción usan lectores cerrados por family/reader/version; una versión desconocida o gate no liberado rechaza antes efectos. El número de versión no es global. Inferencia manifest1, CPUv2/SongCPUv2, timeline1 y sus bytes originales conservan semántica. M3 usa ProductionArtifact1/Package1 con7readers por sujeto cuando no cabe en familias históricas; no redefine CPUv2 ni añade inferencia ficticia a CPU/upload/import/maintenance. Las refs privadas D-02/D-03 y los11sellos `seal_kind` conservan campos/hashes propios. Un hash/receipt importado es historia, no autoridad activa.

TimelineV2/SceneN01 N0 liga VideoRevision/audio final/timing/context/features/fonts/perfil capturados, sin letra privada en el índice ni master actual como default. El reloj de audio y cuadro racional alimentan la misma escena temporal offline. Bytes v1/timeline1 no se convierten silenciosamente. Original conserva bytes y usa metadata sidecar; embedding exige export derivada cuando cambiaría original. Stems48k conservan4roles/amplitud/alineación común sin normalizar. Metadatos/lyrics usan la versión histórica solicitada; omit no embebe.

Paquetes privados conservan cierre completo de Song/historia/ancestros/roles/maps/refs/rights/media/manifiestos por versiones exactas. Ningún secreto, path absoluto, lease/PID/autoridad viva viaja en el paquete; letras/fotos necesarias sólo payload privado autorizado. Import revalida owner y usa receipt propio, mapa source→local completo y no-clobber/CAS; no dedup global por hash ni overwrite. Backup de biblioteca exige cut/SQLite/media juntos y restore/binding/rollback D-09, sin reactivar procesos históricos.

Export audio/stems/video/lyrics exige metadata_ref ByteRef production.export_metadata/1 ligado al Take efectivo. Export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package, incluso con Takes; título/letra/portada/revisiones se recuperan por closure Songv1/SongCPUv2/SongBundleM31. Song válida master NULL/takes [] conserva historia sin metadata de Take ni Take/audio ficticios. Operation/kind/payload/profile deben coincidir con D-02; gate ausente bloquea antes efectos.
