---
documento: arquitectura-sistema
titulo: Arquitectura del sistema
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Arquitectura del sistema

Documentos relacionados:
- [`diagramas.md`](./diagramas.md)
- [`contrato-engines.md`](./contrato-engines.md): contrato de los engines
- [`datos.md`](./datos.md): modelo de datos
- [`convenciones.md`](./convenciones.md)

## 1. Procesos

Todo corre en la misma máquina (Windows 11 con una RTX 5070 de 12 GB) y escucha solo en `127.0.0.1`.

| Proceso | Dónde | Qué hace | Qué no hace |
|---|---|---|---|
| **web** (Next.js, :3000) | nativo | Toda la interfaz, el estado de la UI y la reproducción. Las formas de onda se pintan a partir de picos precalculados | No habla nunca con los engines ni decodifica audio completo |
| **server** (FastAPI, :8000) | nativo, Python 3.12 | Fuente de verdad (SQLite): canciones, takes, letras, vídeos, jobs, linaje y manifiestos. Contiene la API, el SSE, el **dispatcher** y el **worker CPU** (post-proceso, manifiestos, render con ffmpeg y backups). También aloja los adapters de proveedores externos (carril `remote`) | Nada de torch ni de inferencia |
| **engine-acestep** (:8101) | Docker, GPU | Música (`music.*`, `audio.stems`) | No guarda estado; no accede a la BD ni descarga nada |
| **engine-analysis** (:8130) | Docker, GPU/CPU | Beats, tonalidad, transcripción, alineamiento de la letra, CLAP y estética | Igual que el anterior |
| **engine-llm** (:8120) | Docker, GPU | `text.generate` (letras y guion) | Igual que el anterior |
| **engine-comfy** (:8110) | Docker, GPU | Imagen y vídeo (ComfyUI sin interfaz) | Igual que el anterior |
| **engine-mock** (:8199) | Docker o nativo, sin GPU | Todas las tareas, con salida sintética | — |

**Por qué los engines van aparte, uno por cada familia de modelo:**
- Cada upstream fija versiones que chocan entre sí: ACE-Step pide Python 3.11 y `torch 2.10+cu128`, ComfyUI pide cu130 y HeartMuLa `torch<2.11`, entre otros.
- Sus imágenes pesan ~10 GB y tardan en arrancar, mientras que el server se reinicia en un segundo.
- Así el código de terceros queda aislado de la BD.

Todos implementan el mismo contrato `/v1`, de modo que para el server son intercambiables ([ADR-0003](../decisiones/ADR-0003-stack.md)).

## 2. Estructura del repositorio

```
music-studio/
├── CLAUDE.md · README.md · .env.example · docker-compose.yml (perfil `engines`)
├── apps/
│   ├── web/                    # Next.js (App Router, TS, Tailwind, shadcn/ui, next-intl, wavesurfer.js)
│   ├── server/                 # FastAPI (Python 3.12, uv, SQLAlchemy 2, Alembic, Pydantic 2)
│   └── engines/
│       ├── common/             # servidor /v1, supervisor de proceso hijo, VramGuard, verificación de pesos
│       ├── mock/
│       ├── acestep/            # adapter + Dockerfile
│       ├── analysis/           # beat_this, Qwen3-ASR, ForcedAligner, CLAP, Audiobox
│       ├── llm/                # llama.cpp + envoltorio /v1 (M2)
│       └── comfy/              # ComfyUI + workflows/ versionados + envoltorio /v1 (M3–M4)
├── packages/
│   ├── engine-contract/        # modelos Pydantic del contrato /v1 (Py 3.11 y 3.12, sin torch)
│   ├── audio-post/             # validación, loudness, true peak, transcode, picos (lo usa el server)
│   ├── weights/                # lock de modelos, verificación SHA-256, auditor y conversor de pickle
│   └── contracts/              # generados y versionados: openapi.json, engine-v1.json,
│                               # manifest-v1 / timeline-v1 / song-v1 .schema.json, lyrics-cases.json
├── scripts/                    # fetch_models.py, generate.py (CLI), verify_manifest.py, eval/
├── models/                     # pesos (git-ignored) + models.lock.json (versionado)
├── data/                       # ver datos.md §2 (git-ignored)
├── eval/                       # se versionan briefs/ y results/*.md; el resto va a git-ignore
└── docs/
```

## 3. Flujo de un trabajo

1. La **web** llama a `POST /api/generations` (o a otra operación). El **server**:
   - valida la petición contra el `params_schema` de la tarea;
   - comprueba las declaraciones de derechos;
   - crea o reutiliza la canción y la versión de letra;
   - crea los takes en estado `queued` y un `job`;
   - responde con los IDs.
2. El **dispatcher** ([ADR-0018](../decisiones/ADR-0018-cola-de-jobs.md)) toma el siguiente job elegible del carril `gpu`.
   - Si el engine con el modelo cargado es otro, le envía `POST /v1/unload` y comprueba en `/v1/health` que la VRAM libre ha subido.
   - Después lanza `POST /v1/jobs` y consume `GET /v1/jobs/{id}/events` (NDJSON; se puede reenganchar por `seq`).
3. Cada evento actualiza el job y se reenvía a la web por **SSE** (`GET /api/events`).
4. Cuando llega `done`, el engine ha dejado la salida en crudo en `data/tmp/<job_id>/`. A partir de ahí trabaja el **worker CPU** del server:
   - `audio-post` valida el audio, mide loudness y true peak, y genera `master.flac`, `listen.mp3` y `peaks.json`;
   - mueve los ficheros a `data/songs/<song>/takes/<take>/` (movimiento atómico dentro del mismo volumen);
   - escribe el **manifiesto** y registra los `asset`;
   - marca el take como `ready` y encola los jobs que dependían de él (el análisis `audio.beats`).
5. Si hay un error, el take queda en `failed` con el `code` visible. Solo se reintenta automáticamente si el error es `retryable`, y como mucho 2 veces.

**Jobs de una petición** ([ADR-0018](../decisiones/ADR-0018-cola-de-jobs.md)). Una petición de generación con N variantes crea, en la misma transacción, esta cadena de jobs:

| Orden | Job | Carril | Qué hace | Estado inicial |
|---|---|---|---|---|
| 1 | `music.song` / `music.instrumental` | `gpu` | Genera los N takes. Los takes comparten `job_id`; `take.variant_index = i` y `take.seed = seed_base + i` | `queued` |
| 2 | `post.audio` | `cpu` | Post-procesa y registra los N takes | `blocked`, depende del 1 |
| 3 | `audio.beats` | `cpu`, porque su tarea declara `device: cpu` | Analiza cada take | `blocked`, un job por take, depende del 2 |

- Las `inputs` de un job bloqueado se guardan como **referencias** (`{ref: {type: take, id}, role: master}`). El worker las convierte en rutas concretas justo al desbloquearlo.
- **Reintento manual** (`POST /api/jobs/{id}/retry`): crea un job nuevo con la misma `request` y **reutiliza los takes `failed`**, que vuelven a `queued` con el nuevo `job_id`. El job anterior queda en el historial.
- **Recuperación tras un reinicio:** se reenvía **el mismo `job_id`** (idempotente). Si el engine todavía lo tiene, el server se reengancha con `GET /v1/jobs/{id}/events?after=`; si no, se relanza.

**Al arrancar el server:**
- los jobs que estaban `running` pasan a `interrupted` y se vuelven a encolar si son idempotentes (generación con semilla fija);
- los `queued` se conservan;
- se borran de `data/tmp/` los directorios de jobs que ya no existen.

**Cancelación:** `DELETE /api/jobs/{id}` rellena `cancel_requested_at` y el dispatcher llama a `DELETE /v1/jobs/{id}`. Los `gpu_seconds` consumidos quedan registrados en la telemetría.

## 4. Registry de modelos

- Cada modelo tiene un `ModelDescriptor` que declara sus **tareas**. Para cada una indica `verified`, `params_schema`, entradas, salidas y límites ([contrato-engines.md](./contrato-engines.md) §4). La lógica de negocio pide tareas, nunca nombres de modelo.
- **Añadir un modelo** requiere:
  - un adapter y su descriptor;
  - pasar la batería de conformidad de cada tarea: duración y formato correctos, sin silencio ni NaN, telemetría completa y VRAM por debajo del tope;
  - una fila en [`../legal/licencias.md`](../legal/licencias.md).
- **Pesos** ([ADR-0006](../decisiones/ADR-0006-seguridad-de-pesos.md)):
  - formatos admitidos: `safetensors`, `gguf` y `onnx`, fijados por revisión en `models/models.lock.json`;
  - el SHA-256 se comprueba al descargar, y al cargar basta un sello rápido (tamaño + mtime);
  - un pickle solo entra después de pasar por el conversor con auditor;
  - el código remoto (`trust_remote_code`) queda fijado en el lock con su SHA-256.
- **VRAM:** un solo modelo residente a la vez, con tope por proceso y liberación real de memoria mediante un proceso hijo ([ADR-0007](../decisiones/ADR-0007-gpu-local-12gb.md)).
- **Acceso a los engines:** el dispatcher solo conoce el protocolo `EngineBackend`. `HttpEngineBackend` implementa el contrato `/v1` para los engines locales y los adapters externos implementan el mismo protocolo ([contrato-engines.md](./contrato-engines.md) §6).

**Workspaces de Python** (evitan que torch entre en el server):
- **Workspace uv de la raíz:** `packages/*`, `apps/server`, `apps/engines/common` y `apps/engines/mock`. Ninguno depende de torch.
- **Proyectos independientes**, cada uno con su `pyproject.toml` y su `uv.lock`, que solo se instalan dentro de su imagen: `apps/engines/acestep`, `apps/engines/analysis` y los futuros `llm` y `comfy`.
  - Cada imagen copia `packages/engine-contract` y `apps/engines/common` y los instala en su entorno (`uv pip install ./packages/engine-contract ./apps/engines/common`).
  - Sus tests se ejecutan **dentro del contenedor**: `docker compose run --rm <engine> uv run pytest`.

## 5. API del server (resumen)

Las convenciones (errores, paginación, SSE, OpenAPI) están en [`convenciones.md`](./convenciones.md) §3.

| Método | Ruta | Uso | Hito |
|---|---|---|---|
| `GET/POST/PATCH/DELETE` | `/api/songs` · `/api/songs/{id}` | Canciones: título, artista, estado, estilo, colección, etiquetas y notas | M1 |
| `POST` | `/api/songs/{id}/master` | Fija el take maestro | M1 |
| `GET/POST` | `/api/songs/{id}/lyrics` | Versiones de la letra | M1 |
| `POST` | `/api/generations` | Genera takes (`song_id?`; sin él se crea una canción borrador). En M1 solo `music.song` y `music.instrumental`. `lyrics_declaration` es obligatorio cuando hay letra; el instrumental no la pide | M1 |
| `POST` | `/api/takes/{id}/retake` · `/extend` · `/repaint` · `/cover` | Operaciones derivadas: crean takes hijos con linaje | M2 |
| `POST` | `/api/takes/{id}/stems` | Genera los stems como `asset` del take; no crea un take nuevo | M3 |
| `GET/PATCH/DELETE` | `/api/takes/{id}` | Detalle, manifiesto y linaje; favorito, valoración y etiqueta; papelera | M1 |
| `GET` | `/api/takes/{id}/audio?format=mp3\|flac` · `/peaks` · `/analysis` | Streaming con `Range`, picos y análisis | M1 |
| `GET/POST` | `/api/uploads` | Subida de audio o imagen con declaración de derechos | M3 |
| `POST` | `/api/songs/{id}/exports` | WAV 48 kHz por destino, stems, letra y zip del proyecto | M3 |
| `GET/POST` | `/api/songs/{id}/artwork` | Portadas | M3 |
| `GET/POST/PATCH` | `/api/songs/{id}/videos` · `/api/videos/{id}` (timeline con `rev`) · `/api/videos/{id}/shots/{key}/generate` · `/api/videos/{id}/renders` | Vídeo ([video.md](./video.md)) | M3 (N0) · M4 |
| `GET/POST/PATCH` | `/api/characters` · `/api/collections` · `/api/presets` | Bibliotecas globales | M1 (colecciones) · M3–M4 |
| `POST` | `/api/lyrics/assist` | Asistente de letras: crea un job `text.generate` con prioridad interactiva; el texto llega por SSE (`job.delta`) | M2 |
| `GET/DELETE` | `/api/jobs` · `/api/jobs/{id}` | Cola de trabajos; cancelar | M1 |
| `POST` | `/api/jobs/{id}/retry` | Reintento manual (reutiliza los takes `failed`) | M1 |
| `POST` | `/api/generations/estimate` | Tiempo y VRAM estimados antes de crear (proxy a `POST /v1/estimate`) | M1 |
| `POST` | `/api/system/unload` | Descargar el modelo que ocupa la VRAM | M1 |
| `GET` | `/api/events` | SSE | M1 |
| `GET` | `/api/models` · `/api/system` | Modelos y tareas verificadas; GPU, VRAM, RAM, disco y estado de los engines | M1 |
| `GET/PATCH` | `/api/settings` · `/api/providers` | Ajustes y proveedores externos opcionales | M2 |

## 6. Seguridad

Resumen de [ADR-0020](../decisiones/ADR-0020-seguridad-local.md) y de [convenciones.md](./convenciones.md) §5:
- todo escucha en `127.0.0.1` y los puertos de Docker se publican como `127.0.0.1:P:P`;
- el server valida las cabeceras `Host` y `Origin`;
- los engines exigen un token interno y no descargan nada en ejecución (`HF_HUB_OFFLINE=1`; no hay aislamiento de red a nivel Docker);
- los ficheros subidos se validan por su contenido real;
- los secretos solo viven en el `.env` del server.

## 7. Observabilidad

- Logs en JSON en `data/logs/`.
- La telemetría de cada job (carga, ejecución, RTF, pico de VRAM, tope y desbordamiento) se guarda en `job.telemetry` y en el manifiesto.
- La página **Sistema** muestra GPU, VRAM, RAM, el modelo cargado, el estado de cada engine, la cola y el espacio en disco de `data/` y `models/`.
