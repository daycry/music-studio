---
documento: contrato-engines
titulo: Contrato /v1 entre el server y los engines
estado: vigente — contrato /v1 con ampliaciones opcionales compatibles
fecha: 2026-09-28
actualizado: 2026-10-05
---

# Contrato `/v1` de los engines

Todo engine implementa este contrato, sea local (contenedor GPU/CPU) o un adapter de proveedor externo que vive en el server ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)). Para el server son intercambiables.

El contrato es **genérico por tarea**, no específico de audio. La misma interfaz sirve para música, imagen, vídeo, texto (LLM) y análisis.

**Fuente única:** los [modelos Pydantic de `engine_contract`](../../packages/engine-contract/engine_contract/__init__.py). El paquete no depende de torch y declara Python ≥3.11. La suite de Fase 2 se ejecutó con Python 3.12 y comprobó la gramática AST 3.11. T-05/T-06 acreditan ejecución real con Python 3.11.14 en el contenedor ACE-Step, incluida su factoría `/v1` y las pruebas CPU del adaptador. [ADR-0019](../decisiones/ADR-0019-contratos-code-first.md) fija la compatibilidad requerida.

[export_contracts.py](../../scripts/export_contracts.py) genera [engine-v1.json](../../packages/contracts/engine-v1.json). [test_contract.py](../../packages/engine-contract/tests/test_contract.py) comprueba su igualdad con `contract_schema()`. La factoría ACE-Step usa este contrato; T-06 acredita carga BF16, generación real de 30 s y descarga del proceso hijo ([QA](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/report.md)). La API del server de M1 y los demás adaptadores quedan para tareas posteriores.

## 1. Principios

1. **El engine no tiene estado ni conoce el dominio.** No sabe qué es una canción ni un take. Recibe `job_id`, tarea, entradas y parámetros, y devuelve **salida en crudo** en `data/tmp/<job_id>/` junto con su telemetría. El post-proceso, el manifiesto y el traslado a la biblioteca son cosa del server ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)).
2. **El server asigna `job_id`**, que es idempotente. Si se reenvía el mismo `job_id`, se engancha al trabajo existente en lugar de crear uno nuevo.
3. **Un trabajo a la vez por engine.** Si el engine está ocupado responde `409 BUSY`. La cola vive en el server.
4. **Descarga real de VRAM.** El modelo se ejecuta en un **proceso hijo** del engine. `unload` termina ese proceso, lo que libera también el contexto CUDA (0,3–0,5 GB). El proceso padre **no inicializa CUDA** nunca. La VRAM total y libre que informa `/v1/health` la lee mediante **NVML** (`nvidia-ml-py`), que no crea contexto CUDA.
4-bis. **Carga implícita.** `POST /v1/jobs` carga el `model_id`/`mode` pedido si no es el que está cargado (descargando el anterior) y lo anuncia con el evento `stage: loading_model`. `POST /v1/load` solo sirve para precargar.
5. **Tope de VRAM.** Al cargar, el proceso hijo aplica `set_per_process_memory_fraction(cap / total)`, con `cap = VRAM libre medida justo antes de cargar − STUDIO_VRAM_MARGIN_MB` (512 MB por defecto). Nunca se usa una fracción fija: en WSL2, un exceso de VRAM no da OOM, sino que se desborda a la RAM sin avisar ([ADR-0007](../decisiones/ADR-0007-gpu-local-12gb.md)).
6. **Compatibilidad hacia delante.** Dentro de `/v1` solo se añaden campos opcionales. Quien lee ignora los campos que no conoce. Un cambio que rompa el contrato obliga a pasar a `/v2`.

## 2. Endpoints

| Método | Ruta | Respuesta |
|---|---|---|
| `GET` | `/v1/health` | `{contract_version, engine_id, engine_version, image_digest, state: idle\|loading\|busy\|error, loaded?: {model_id, mode}, gpu: {total_mb, free_mb, cap_mb}, job_id?}` |
| `GET` | `/v1/models` | `[ModelDescriptor]` (§4) |
| `POST` | `/v1/load` | `{model_id, mode}` → `200` cuando está cargado. Es idempotente |
| `POST` | `/v1/unload` | Termina el proceso hijo. Devuelve `{freed_mb}` |
| `POST` | `/v1/estimate` | `JobRequest` → `{eta_s, vram_mb, cost_eur?}` sin ejecutar nada |
| `POST` | `/v1/jobs` | `JobRequest` → `202 {job_id}` · `409 BUSY` · `422 INVALID_PARAMS` |
| `GET` | `/v1/jobs/{job_id}` | Estado actual y último `seq` |
| `GET` | `/v1/jobs/{job_id}/events?after=<seq>` | Flujo **NDJSON** de eventos (§3). Permite reengancharse desde cualquier `seq` |
| `DELETE` | `/v1/jobs/{job_id}` | Cancelación cooperativa: el adapter comprueba el flag entre pasos |

## 3. Petición y eventos

```text
JobRequest {
  job_id: ULID                       # lo asigna el server
  task: str                          # ver §5, p. ej. "music.song", "image.edit", "text.generate"
  model_id: str                      # "ace-step-1.5-turbo"
  mode?: str                         # "bf16" | "offload" | "int8" | … (los declarados en el descriptor)
  inputs: [ {role, path, sha256, media_type} ]   # rutas relativas a data/ (p. ej. "songs/…/master.flac")
  params: {}                         # validado contra tasks[task].params_schema
  seed?: int                         # semilla base: la salida i usa seed + i (anotado en artifact.meta.seed)
  n_outputs: int = 1                 # variantes (en batch o en serie, a criterio del adapter)
  output_dir: str                    # "tmp/<job_id>/"
  timeout_s: int
}

Evento {seq: int, ts: ISO-8601, job_id, type, data}
  type = stage     data {stage: "loading_model"|"generating"|"decoding"|…}   # las etapas las marca el engine
       | progress  data {fraction: 0..1, step?, total?, output_index?, eta_s?}
       | delta     data {text}                                  # streaming de texto (LLM)
       | artifact  data {output_index, path, media_type, sha256, meta}
       | log       data {level, message}
  terminal ÚNICO:
       | done      data {artifacts: [...], result?: {}, telemetry: Telemetry}
       | error     data {code, message, retryable: bool}
       | cancelled data {telemetry}

Telemetry {load_s, run_s, rtf?, vram_peak_mb, vram_cap_mb, spilled: bool, mode, model_revision, extra{}}
```

- `spilled` es `true` si el pico se acercó al tope o si el RTF cayó por encima de 1,5× el valor de referencia medido. En ese caso la UI avisa de un posible desbordamiento a RAM.
- **Códigos de error** (estables): `INVALID_PARAMS`, `MODEL_NOT_FOUND`, `WEIGHTS_MISMATCH`, `VRAM_EXCEEDED`, `BUSY`, `CANCELLED`, `TIMEOUT`, `PROVIDER_ERROR`, `INTERNAL`. Si `retryable` es `true`, el server puede reintentar hasta 2 veces.

## 4. Descriptor de modelo

```text
ModelDescriptor {
  id, family, version, revision            # revisión del repo de pesos fijada en models.lock.json
  license, commercial_use: bool, training_data: str   # literal del proveedor
  provider: {type: "local"|"external", name?}
  weights: [{path, sha256, bytes, format: "safetensors"|"gguf"|"onnx"}]
  remote_code?: [{path, sha256}]           # opcional, [] por defecto; path relativo a models/
  modes: [{id, vram_mb, notes}]            # medidos en M0/M4; "desconocido" hasta entonces
  tasks: {
    "<task>": { verified: bool, checkpoint?: str, device: "gpu"|"cpu", params_schema: JSONSchema,
                features?: {"<feature>": {verified: bool}},   # sub-capacidades: timbre_ref, lora, negative_prompt, bpm, key…
                inputs: [{role, media_types, required}], outputs: [{media_type, count}],
                limits: {duration_s?: [min,max], resolution?, languages_tested?: []},
                cost_model?: {…} }         # solo proveedores externos
  }
}
```

Las **capacidades** que usa la lógica de negocio son las claves de `tasks` que tienen `verified: true`, y dentro de cada una, sus `features` verificadas: la UI solo muestra los controles de las features verificadas. El server resuelve «qué engine y qué modelo» buscando la tarea, nunca por el nombre del modelo.

`remote_code` conserva los hashes del código cargado con `trust_remote_code`, obtenidos del lock
y comprobados por el engine antes de cargarlo. No sustituye esa comprobación. Las rutas siguen
la validación de `weights` y los hashes son SHA-256 en minúsculas. Es una ampliación opcional
compatible de `/v1` ([ADR-0024](../decisiones/ADR-0024-hashes-de-codigo-remoto-en-descriptores.md));
los descriptores existentes sin ese campo siguen siendo válidos.

- **`device`**: una tarea `cpu` (p. ej. `audio.beats` con beat_this) no necesita la VRAM en exclusiva. El dispatcher la manda por el carril `cpu` sin descargar el modelo que ocupa la GPU.
- **Mientras el adapter no la verifique en M0**, una tarea puede declararse con `verified: false`. En ese caso el resolver no la usa, salvo con `STUDIO_ALLOW_UNVERIFIED=1` (solo desarrollo).

## 5. Catálogo de tareas

En la preparación de M0/T-18, ACE-Step admite además el parámetro opcional `time_signature`, que el adaptador transmite como `timesignature`; `key` sigue siendo opcional y llega como `keyscale`. La CLI expone `--time-signature` y `--key`. Omitirlos no inventa compás ni tónica. No se modifica la estructura obligatoria de `/v1` ni se activa una feature `verified` por transportar un campo. La limpieza de Markdown y los recibos privados pertenecen a la preparación del llamante, no a una reescritura silenciosa dentro del engine. [Pipeline y preparación](./pipeline-audio.md#preparación-local-antes-de-generar--t-18).

| Tarea | Entradas | Salida | Hito | Engine por defecto |
|---|---|---|---|---|
| `music.song` | opcional `timbre` (feature `timbre_ref`) · letra y estilo en `params` · LoRA en `params.lora` (feature `lora`) | audio | M0 | acestep |
| `music.instrumental` | — (sin letra; no exige `lyrics_declaration`) | audio | M0 (verificada) · M1 (UI) | acestep |
| `music.retake` (variación) | audio `source` | audio | M2 | acestep |
| `music.extend` | audio `source` | audio | M2 | acestep |
| `music.repaint` | audio `source` + `[t0,t1]` | audio | M2 | acestep |
| `music.cover` | audio `source` | audio | M2 | acestep |
| `music.complete` (acompañamiento para una voz) | audio `vocals` | audio | M3 | acestep (checkpoint base) |
| `audio.stems` | audio `source` | N audios | M3 | acestep (extract, base) / separador |
| `audio.beats` | audio | JSON (beats, downbeats, bpm) | M1 | analysis |
| `audio.key` | audio | JSON | M3 | analysis |
| `audio.transcribe` | audio | JSON (texto y tiempos) | M0 | analysis |
| `audio.align_lyrics` | audio + texto | JSON (tiempos por palabra) | M3 | analysis |
| `audio.clap` · `audio.aesthetics` | audio + texto | JSON (puntuaciones) | M0 | analysis |
| `text.generate` | — (mensajes en `params`) | texto en `delta` + `result` | M2 | llm |
| `image.generate` · `image.edit` | imágenes de referencia opcionales | imagen | M3 | comfy |
| `image.depth` | imagen | imagen (mapa de profundidad) | M4 | comfy |
| `video.i2v` · `video.flf2v` · `video.t2v` | imagen o imágenes | vídeo | M4 | comfy |
| `video.lipsync` | imagen + audio `vocals` | vídeo | M4 | comfy |
| `video.upscale` | vídeo | vídeo | M4 | comfy |
| `train.lora` | dataset | pesos LoRA | M5 | comfy / acestep |

Añadir una tarea **no rompe** `/v1`: basta con declararla en el descriptor. El render final del vídeo **no es una tarea de engine**: lo hace el server con ffmpeg en el carril CPU ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)).

## 6. Engines, puertos y contenedores

| Engine | Puerto (solo `127.0.0.1`) | Base | Tareas |
|---|---|---|---|
| `engine-acestep` | 8101 | `nvidia/cuda:12.8.1-runtime-ubuntu22.04` + Python 3.11 (uv) + `torch 2.10+cu128` | `music.*`, `audio.stems` |
| `engine-comfy` | 8110 | `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime` + ComfyUI fijado | `image.*`, `video.*` |
| `engine-llm` | 8120 | llama.cpp (build CUDA) fijado | `text.generate` |
| `engine-analysis` | 8130 | `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime` | `audio.beats`, `audio.key`, `audio.transcribe`, `audio.align_lyrics`, `audio.clap`, `audio.aesthetics` |
| `engine-mock` | 8199 | Python 3.12 (sin GPU) | Todas las tareas, con salidas sintéticas (§7) |
| Adapters externos | — (dentro del server, carril `remote`) | — | Los que se activen ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)) |

El mapa lo configura el server: `STUDIO_ENGINES=acestep=http://127.0.0.1:8101,comfy=http://127.0.0.1:8110,…`. En `docker-compose.yml` los puertos se publican **siempre** como `127.0.0.1:PUERTO:PUERTO`.

**Montajes y token (todos los engines):**

| Ruta del host | Montaje en el contenedor | Modo |
|---|---|---|
| `models/` | `/models` | solo lectura |
| `data/` | `/data` | **solo lectura**: las entradas de `JobRequest.inputs` son rutas relativas a `data/` |
| `data/tmp/` | `/data/tmp` | lectura y escritura: única ruta en la que el engine escribe |

- **Entradas que viven fuera de `data/`** (por ejemplo, las tomas de `eval/`): el llamante las copia antes a `data/tmp/<job_id>/in/`.
- **Token:** `STUDIO_ENGINE_TOKEN` en `.env`, persistente. Lo genera una sola vez `scripts/init_env.py` (M0 T-01) y lo usan tanto el CLI como el server.
- **Server:** habla con los engines a través del protocolo Python `EngineBackend` (`health`, `models`, `load`, `unload`, `estimate`, `submit`, `events`, `cancel`).
  - `HttpEngineBackend` implementa este contrato para los engines locales.
  - Los adapters externos (carril `remote`) implementan el mismo protocolo dentro del server ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)).
  - El dispatcher solo conoce `EngineBackend`.

## 7. engine-mock

- Implementa el contrato completo sin GPU:
  - audio: barrido senoidal a 48 kHz estéreo con la duración pedida;
  - texto: *lorem* en `delta` con letra etiquetada válida;
  - imagen: PNG degradado;
  - vídeo: MP4 de color;
  - JSON de análisis: beats a 120 BPM.
- Opciones de prueba:
  - `MOCK_STAGE_DELAY_MS` fija el retardo de cada etapa.
  - Directivas dentro del prompt de estilo, que solo interpreta el mock para que los E2E las puedan inyectar desde la UI:
    - `@mock:fail=<CODE>`: falla siempre con ese código;
    - `@mock:fail_once=<CODE>`: falla la primera vez que ve ese prompt y acierta después, para probar el reintento manual;
    - `@mock:retryable`: marca el fallo como reintentable.
  - Las mismas opciones se pueden pasar en `params._mock` cuando la llamada es directa.
- El descriptor declara **todas** las tareas del catálogo §5 con `verified: true` y todas sus features, para poder probar cada pantalla. `audio.beats` se declara con `device: cpu`, igual que en el engine real.
- Es el engine por defecto en los E2E y en el desarrollo de UI.

## 8. Uso de la implementación Python

Las secciones anteriores fijan el contrato y los destinos previstos. T-03 implementa el paquete, el servidor común y el mock. T-05 proporciona el contenedor ACE-Step; T-06 añade su adaptador y factoría con pruebas CPU y generación GPU BF16 de 30 s acreditadas. Las capacidades de producto conservan `verified: false` hasta la evaluación de T-10. Los adaptadores externos quedan para tareas posteriores.

| Unidad | API y responsabilidad | Fuente |
|---|---|---|
| `engine_contract` | `JobRequest`, `Event`, `ModelDescriptor`, `Health`, `Telemetry`, `contract_schema()` | [Modelos](../../packages/engine-contract/engine_contract/__init__.py) |
| `engine_common` | `create_app(descriptors, adapter_factory, ...)`: autenticación, rutas, trabajos y eventos | [Servidor](../../apps/engines/common/engine_common/server.py) |
| `engine_common` | `ProcessSupervisor`, `VramGuard`, `NvmlGpu`, `CpuGpu`: proceso hijo y control de recursos | [Runtime](../../apps/engines/common/engine_common/runtime.py), [worker](../../apps/engines/common/engine_common/worker.py) |
| `engine_mock` | `create_mock_app(...)`, `MockAdapter`, `descriptor()`: salidas sintéticas sin GPU | [Mock](../../apps/engines/mock/engine_mock/__init__.py) |
| `engine_acestep` | `create_app()`, `AceStepAdapter`, descriptor: API `/v1` y ejecución del modelo en el proceso hijo | [Factoría](../../apps/engines/acestep/engine_acestep.py), [adaptador](../../apps/engines/acestep/adapter.py), [descriptor](../../apps/engines/acestep/descriptor.py) |

`create_mock_app` admite `token`, `data_dir`, `stage_delay_ms`, `gpu` y `margin_mb`. Usa `CpuGpu` por defecto. El descriptor ofrece el modelo `mock`, modo `cpu`; todas sus tareas son CPU. El audio sintético es WAV PCM de 16 bits, 48 kHz y dos canales. Las imágenes son PNG de 64 × 64 y el vídeo MP4 requiere el ffmpeg local. `train.lora` devuelve un safetensors sintético; no entrena pesos.

El servidor exige `X-Studio-Engine-Token` en las rutas. La factoría usa `STUDIO_ENGINE_TOKEN` si no recibe `token` y rechaza un valor vacío. Los trabajos y eventos viven en memoria: la idempotencia y la reanudación duran hasta reiniciar el proceso. Esto respeta la ausencia de persistencia del engine; la cola duradera corresponderá al server.

Las entradas se verifican por SHA-256. `output_dir` debe coincidir con `tmp/<job_id>/`; el servidor rechaza rutas inseguras y salidas preexistentes. En el host, `STUDIO_DATA_DIR` debe quedar dentro del proyecto; en Docker se admite el montaje contractual `/data`. Véase [server.py](../../apps/engines/common/engine_common/server.py).

### Arrancar el mock en local

Ejecuta desde la raíz en PowerShell. `env.ps1` prepara el entorno, pero no carga `.env`: copia el token a la variable del proceso sin imprimirlo.

```powershell
. .\scripts\env.ps1
$tokenLine = Get-Content .env | Where-Object { $_ -match '^STUDIO_ENGINE_TOKEN=' } | Select-Object -First 1
if (-not $tokenLine) { throw 'Falta STUDIO_ENGINE_TOKEN en .env' }
$env:STUDIO_ENGINE_TOKEN = ($tokenLine -split '=', 2)[1]
uv run --frozen --package engine-mock uvicorn engine_mock:create_mock_app --factory --host 127.0.0.1 --port 8199
```

En otra consola, carga el entorno y el token de la misma forma. Esta petición carga implícitamente el mock y devuelve el `job_id`. Usa un ULID nuevo para cada prueba independiente.

```powershell
$headers = @{ 'X-Studio-Engine-Token' = $env:STUDIO_ENGINE_TOKEN }
$jobId = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
$body = @{
    job_id = $jobId; task = 'music.instrumental'; model_id = 'mock'; mode = 'cpu'
    inputs = @(); params = @{ duration_s = 3 }; seed = 42; n_outputs = 1
    output_dir = "tmp/$jobId/"; timeout_s = 30
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8199/v1/health -Headers $headers
Invoke-RestMethod http://127.0.0.1:8199/v1/jobs -Method Post -Headers $headers -ContentType application/json -Body $body
Invoke-WebRequest "http://127.0.0.1:8199/v1/jobs/$jobId/events?after=0" -Headers $headers | Select-Object -ExpandProperty Content
```

El flujo devuelve NDJSON con `seq` creciente y un solo terminal. En caso de éxito, `artifact.path` señala la salida cruda relativa a `data/`, con su hash. Para simular un error usa `params._mock = @{ fail = 'INTERNAL'; retryable = $true }` o las directivas del §7. `fail_once` se recuerda durante la vida del adapter; una descarga pierde esa memoria.

### Comprobar el contrato

```powershell
. .\scripts\env.ps1
uv run --frozen --all-packages scripts/export_contracts.py --check
uv run --frozen --all-packages pytest packages/engine-contract/tests apps/engines/common/tests apps/engines/mock/tests -q
```

El [informe de QA de Fase 2](../roadmap/2026-09-28-m0-entorno-y-motor/testing/report.md) recoge las comprobaciones y sus límites. El arranque HTTP descrito es reproducible con la API existente; la QA independiente no abrió un host ni probó Docker o una GPU real.
