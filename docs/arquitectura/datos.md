---

documento: arquitectura-datos

titulo: Modelo de datos, ficheros, linaje y manifiesto

estado: vigente — baseline implementado; ampliaciones futuras señaladas

fecha: 2026-09-28

actualizado: 2026-10-07

---



# Modelo de datos



**Reglas** ([CONSTITUTION](../CONSTITUTION.md) §2):

- Solo el server escribe en la base de datos.

- La primera migración de M1 crea **todas las tablas definidas inicialmente**, incluidas las previstas para M3–M5: baseline de 23 tablas de ADR-0041. Las nuevas relaciones decididas posteriormente, como `job_attempt` (ADR-0043), se añaden mediante otra migración; no se reescribe el baseline histórico.

- Desde esa migración, las demás son **aditivas**, salvo la excepción CPU delimitada de [ADR-0074](../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) para tres tablas. Renombrar o borrar una columna que ya tiene datos exige un ADR. El baseline y sus migraciones no se reescriben.



## 1. Entidades



```

user (1 fila «local»)

collection 1───* song

song ─┬─* lyrics_version            versiones de la letra (linaje propio)

      ├─* take                      cada audio generado; árbol por lineage_edge

      │    ├─* analysis             beats, secciones, tonalidad, tiempos de la letra (filas por tipo)

      │    └─* asset (role master/listen/peaks/stem:*)

      ├── master_take_id            la versión «elegida»

      ├─* artwork ──1 asset         portadas, imágenes clave, fondos

      ├─* video_project ─┬─* shot ──* shot_version ──* asset (keyframe, clip)

      │                  └─* render ──1 asset

      └─* export ──1 asset

character (global) ─* character_ref ──1 asset/upload

preset (global) · upload (global) · job ─* job_dependency · lineage_edge · setting · provider

```



### 1.1 Tablas



Todas las tablas de contenido comparten estas columnas: `id` (ULID), `owner_id` (FK a `user`), `created_at`, `updated_at` y `deleted_at?`. La papelera es un borrado lógico que se purga a los 30 días.



| Tabla | Campos propios |

|---|---|

| `user` | `name`. Tiene una sola fila, `local`, hasta que llegue el multiusuario |

| `collection` | `name`, `cover_artwork_id?` |

| `song` | `collection_id?`, `title`, `artist?`, `status` (`draft`/`in_progress`/`final`/`archived`), `style_prompt`, `negative_prompt?`, `language?`, `current_lyrics_version_id?`, `master_take_id?`, `cover_artwork_id?`, `tags` (JSON), `notes?`, `rev` |

| `lyrics_version` | `song_id`, `text` (con etiquetas de sección), `source` (`manual`/`assistant`/`import`), `declaration` (`own`/`assistant`/`public_domain`/`licensed`), `parent_id?`, `sha256` |

| `take` | `song_id`, `job_id`, `lyrics_version_id?`, `status` (`queued`/`running`/`ready`/`failed`/`cancelled`), `batch_id` (variantes de una misma petición), `variant_index`, `root_id`, `derivation` (`original`/`variant`/`extend`/`repaint`/`cover`/`complete`/`remaster`/`edit`), `task`, `model_id`, `model_version`, `seed`, `params` (JSON), `duration_s?`, `sample_rate?`, `rating?` (1–5), `favorite`, `label?`, `commercial_use` |

| `lineage_edge` | `child_type`, `child_id`, `parent_type`, `parent_id`, `role` (`source`/`vocals`/`reference`/`crossfade_a`/`crossfade_b`…), `section_map?` (§1.2). Admite **varios padres**, para crossfade, cover desde una subida o un plano con varias referencias. `take.root_id` se deriva de estas aristas y se guarda desnormalizado para las consultas |

| `asset` | `subject_type` (`take`/`artwork`/`shot_version`/`render`/`export`/`character`/`lora`/`cli_run`), `subject_id` (sujeto del manifiesto; `owner_id` común sigue siendo usuario), `role` (`master`/`listen`/`peaks`/`manifest`/`stem:vocals`/`keyframe`/`clip`/`video`/`zip`…), `path` (relativa a `data/`), `media_type`, `sha256`, `bytes`, `meta` (JSON: sample_rate, channels, lufs, true_peak, width, height, fps, duration_s) |

| `upload` | `kind` (`audio`/`image`), `path`, `sha256`, `media_type`, `meta`, `rights` (`own`/`licensed`/`consented`/`public_domain`), `real_person` (bool), `consent` (`self`/`consented`/`n_a`), `note?` |

| `analysis` | `take_id`, `kind` (`beats`/`sections`/`key`/`loudness`/`lyrics_timing`), `analyzer_id`, `analyzer_version`, `lyrics_version_id?`, `data` (JSON). Es única por (`take_id`, `kind`, `analyzer_id`). M1 crea `beats`; M3 añade el resto como filas nuevas |

| `artwork` | `song_id?`, `kind` (`cover`/`keyframe`/`background`), `source` (`generated`/`upload`), `upload_id?`, `job_id?`, `prompt?`, `model_id?`, `seed?`, `rights` |

| `character` | `name`, `description`, `kind` (`real_person`/`fictional`/`animal`/`object`), `consent` (`self`/`consented`/`fictional`; obligatorio si es `real_person`), `consent_note?`, `sheet_artwork_id?`, `lora_asset_id?` |

| `character_ref` | `character_id`, `upload_id?` \| `artwork_id?`, `view?` (`front`/`profile`/`full`/`expression`) |

| `preset` | `kind` (`style`/`voice`/`visual`/`full`), `name`, `payload` (JSON) |

| `video_project` | `song_id`, `take_id` (el audio que usa: si no coincide con el maestro, el vídeo está «desfasado»), `title`, `aspect` (`16:9`/`9:16`/`1:1`), `level_preset` (`N0`…`N3`), `visual_style`, `treatment`, `status` (`planning`/`generating`/`editing`/`rendered`), **`timeline` (JSON, la fuente de verdad)**, `rev` |

| `video_character` | `video_project_id`, `character_id`, `role` (`performer`/`cast`) |

| `shot` | `video_project_id`, `key` (estable dentro del timeline), `kind` (`lyric`/`still`/`still_motion`/`i2v`/`singer`/`t2v`), `current_version_id?`. Los tiempos del plano **no** se guardan aquí, sino en el `timeline` |

| `shot_version` | `shot_id`, `job_id?`, `prompt`, `camera?`, `seed?`, `model_id?`, `provider` (`local`/nombre), `status`, `keyframe_asset_id?`, `clip_asset_id?`, `focus_point?` (x, y para el reencuadre a 9:16) |

| `render` | `video_project_id`, `timeline_rev`, `aspect`, `resolution`, `kind` (`full`/`short`/`preview`), `subtitles` (`burned`/`srt`/`none`), `status`, `asset_id?` |

| `export` | `song_id`, `kind` (`audio`/`stems`/`video`/`lyrics`/`project_zip`), `target?` (`streaming`/`broadcast`/`podcast`), `asset_id?`, `expires_at` |

| `job` | `task`, `lane` (`gpu`/`cpu`/`remote`), `priority` (`interactive`/`normal`/`batch`/`nightly`), `not_before?`, `status` (`queued`/`blocked`/`running`/`succeeded`/`failed`/`cancelled`/`interrupted`), `attempt`, `max_attempts`, `engine_id?`, `model_id?`, `request` (petición de dominio, con referencias aún no resueltas; cada envío contractual se congela en `job_attempt`), `stage?`, `progress?`, `error_code?`, `error?`, `telemetry?` (JSON), `song_id?`, `started_at?`, `finished_at?`, `cancel_requested_at?` |

| `job_attempt` | Migración aditiva posterior al baseline de 23 tablas ([ADR-0043](../decisiones/ADR-0043-identidad-durable-de-intentos.md)); campos comunes más `job_id`, `ordinal`, `engine_id`, `model_id`, `mode`, `engine_request` contractual congelada, opciones de carga validadas, `last_seq`, `status` (`prepared`/`submitted`/`succeeded`/`failed`/`cancelled`), `terminal?`. ID de envío distinto del job lógico; pertenencia al mismo usuario y ordinal único por job. Implementación pendiente en T-04. |

| `job_dependency` | `job_id`, `depends_on_job_id`. Forma el grafo de dependencias: take → análisis; imagen clave → clip → render ([ADR-0018](../decisiones/ADR-0018-cola-de-jobs.md)) |

| `setting` | `key`, `value` (JSON) |

| `provider` | `function` (`text`/`image`/`video`…), `name`, `enabled`, `config` (JSON sin secretos: las claves van en `.env`) |



**Búsqueda:** tabla virtual FTS5 `song_fts(title, style_prompt, lyrics)`, mantenida al día con triggers.



**Aclaraciones de primera migración ([ADR-0041](../decisiones/ADR-0041-esquema-inicial-y-snapshots-del-server.md)):** `local` es el nombre de un usuario con ID ULID; `owner_id` identifica siempre al usuario. Assets separan el sujeto mediante `subject_type/subject_id`. Los sujetos externos no tienen FK ficticia y exigen validación especializada antes de insertarse. Raíz canónica con varios padres: menor ULID entre raíces originales, sin perder aristas. FTS usa sólo canción activa/letra vigente; snapshots son derivados y reconciliables tras commit. Backup diario mediante la API nativa `sqlite3.Connection.backup()`, con restauración real y rotación propia14días, mientras el backend está activo y en el siguiente arranque si estuvo parado.



### 1.2 `section_map`



Describe cómo se construye el audio de un take hijo a partir del de su padre. Se usa en `extend`, `repaint`, `edit` y crossfade:



```json

{"ops": [

  {"op": "keep",  "src": [0.0, 58.0],   "dst": [0.0, 58.0]},

  {"op": "regen", "src": null,          "dst": [58.0, 84.0]},

  {"op": "keep",  "src": [84.0, 180.0], "dst": [84.0, 180.0]}

]}

```



Valores de `op`: `keep`, `regen`, `append` y `fade`. Los tiempos van en segundos.



### 1.3 Timeline del vídeo



`video_project.timeline` es la **fuente de verdad del montaje** y vive en la BD. El `timeline.json` que hay en disco es solo una **instantánea derivada**; nunca se lee para reconstruir el montaje. Su esquema está en `packages/contracts/timeline-v1.schema.json`:



```json

{"version": 1, "fps": "24/1", "duration_s": 180.0,

 "shots": [{"key": "s07", "t0": 58.0, "t1": 62.1, "section": "chorus", "lyrics": "luz de neón…",

            "transition_in": {"type": "cut"}, "characters": ["01JC…"]}],

 "subtitles": {"style": "karaoke", "position": "bottom", "font": "Inter"},

 "titles": []}

```



Cada edición sube `rev`, y cada render guarda el `timeline_rev` con el que se generó.



## 2. Ficheros en disco



```

data/

├── db/studio.sqlite            # WAL; NO se sincroniza con Synology (entorno.md §4)

├── backups/                    # API SQLite backup diaria + rotación de 14 días (SÍ se sincroniza)

├── songs/<song_id>/            # una carpeta por canción = el proyecto en disco (SÍ se sincroniza)

│   ├── song.json               # instantánea legible y versionada (song-v1.schema.json), regenerada al cambiar

│   ├── takes/<take_id>/        # master.flac · listen.mp3 · peaks.json · manifest.json · stems/

│   ├── artwork/<artwork_id>.png (+ .manifest.json)

│   ├── video/<video_project_id>/

│   │   ├── shots/<shot_id>/<shot_version_id>/   # keyframe.png · clip.mp4 · manifest.json

│   │   ├── timeline.json       # instantánea derivada de la BD

│   │   └── renders/<render_id>.mp4

│   └── exports/                # WAV 48 kHz, zips (caducan a los 7 días)

├── characters/<character_id>/  # hoja de personaje, referencias generadas, LoRA

├── uploads/<yyyy>/<mm>/<upload_id>.<ext>   # audio e imágenes subidos (con su declaración de derechos)

├── cli/<fecha>/<run_id>/       # salidas del CLI de M0 (sin canción asociada)

├── tmp/<attempt_id>/           # salida cruda del engine; cleanup sólo tras reconciliar el intento

├── tmp/_server_inputs/<uuid>/  # copias verificadas propias del server, fuera del rawdir (ADR-0049)

├── trash/                      # ficheros de entidades borradas (30 días)

└── logs/

```



- **Cada canción es portable:** su carpeta contiene todo (audio, portada, vídeo, manifiestos y un `song.json` con las letras, los takes, las valoraciones, el linaje y el timeline). «Exportar proyecto» comprime esa carpeta; «Importar» reconstruye las filas de la BD a partir de `song.json`.

- **No se guarda WAV:** el FLAC es sin pérdida y ocupa en torno a un 40 % menos. El WAV a 48 kHz se genera al exportar.



## 3. Manifiesto de procedencia v1



Cada artefacto generado tiene su manifiesto: take, imagen, versión de plano, render y export. Lo escribe **el server** al terminar el post-proceso ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)) y lo guarda como `asset` con `role=manifest`, junto con su SHA-256. Esquema histórico y de inferencia: `packages/contracts/manifest-v1.schema.json`. La ampliación CPU autónoma v2 de ADR-0074 requiere un schema nuevo y despacho por versión; los archivos v1 emitidos siguen inmutables.



```json

{

  "manifest_version": 1,

  "kind": "audio_take",

  "subject": {"type": "take", "id": "01JB…"},

  "song_id": "01JA…",

  "created_at": "2026-10-02T18:22:11.123Z",

  "commercial_use": true,

  "provider": {"type": "local"},

  "models": [

    {"role": "dit", "id": "ace-step-1.5-turbo", "revision": "…", "license": "MIT",

     "training_data": "literal del proveedor",

     "weights": [{"path": "ace-step-1.5/turbo/model.safetensors", "sha256": "…"}]},

    {"role": "lm", "id": "acestep-5Hz-lm-0.6B", "revision": "…", "license": "MIT", "weights": []}

  ],

  "pipeline": {"engine_id": "acestep", "engine_version": "0.1.0", "image_digest": "sha256:…",

               "workflow_id": null, "workflow_sha256": null, "custom_nodes": [], "remote_code": []},

  "request": {"task": "music.song", "params": {"duration_s": 180, "vocal_language": "es"},

              "seed": 84920117, "lyrics_sha256": "…", "lyrics_declaration": "own",

              "style_prompt": "…"},

  "inputs": [],

  "lineage": {"parents": [], "derivation": "original", "section_map": null},

  "post": {"lufs_in": -9.8, "gain_db": -4.2, "limiter": false, "true_peak_dbtp": -1.3},

  "outputs": [{"role": "master", "path": "master.flac", "media_type": "audio/flac", "sha256": "…",

               "meta": {"sample_rate": 48000, "channels": 2, "duration_s": 180.02}}],

  "run": {"gpu": "RTX 5070 12GB", "mode": "bf16", "load_s": 14.1, "run_s": 38.2,

          "vram_peak_mb": 9120, "vram_cap_mb": 10200, "spilled": false},

  "tools": [{"name": "ffmpeg", "version": "7.1", "license": "LGPL-2.1", "build": "lgpl-shared"}]

}

```



- **Valores de los campos:**

  - `kind`: `audio_take`, `stems`, `image`, `video_clip`, `render`, `export`, `lora` o `cli_run`.

  - `song_id`: `null` en `cli_run` y en los artefactos de personaje.

  - `provider` externo: `{"type":"external","name","model","request_id","cost_eur"}`.

  - `inputs[]`: `{role, ref:{type,id}, sha256, rights, consent}`.

  - `pipeline.remote_code[]`: ficheros `.py` que se cargan con `trust_remote_code`, con su SHA-256.

- **`commercial_use`** es el AND de todos los modelos, herramientas e inputs usados. Basta con que uno no permita uso comercial para que el manifiesto diga `false`.

- **Reglas de v1:** solo se añaden campos opcionales, y el verificador ignora los que no conoce. Un manifiesto ya emitido **nunca** se reescribe; si el esquema cambia, sube `manifest_version`.

- **Qué nunca va en el manifiesto:**

  - la letra: se referencia por hash, para poder compartir el manifiesto sin exponerla;

  - las fotos de personas reales: solo se guarda el ID de la subida y el tipo de consentimiento.

- `scripts/verify_manifest.py` valida todas las versiones emitidas y los hashes de las salidas.





## 4. Persistencia técnica verificada hasta 0004

La [QA4 de T02](../roadmap/2026-09-28-m1-mvp-estudio/testing/t02/qa4-report.md) acredita la implementación técnica de ADR-0041 y ADR-0044. Conserva las 23 tablas del baseline histórico. `job_attempt` sigue pendiente en T04.

`0002` añade metadatos de soporte, dirty y generación, membresía de consumidores e identidad FTS estable. `0003` añade `snapshot_clock` y `snapshot_import`. `0004` impide promoción ordinaria del soporte y degradación de raíces. Esta infraestructura local queda fuera del payload canónico.

Los snapshots incluyen una raíz completa, referencias globales y un cierre dirigido de soporte mediante `dependencies.rows/provenance`. No expanden otros proyectos completos. Los triggers invalidan consumidores ante ORM, SQL, Core, bulk y movimientos OLD/NEW. El callback Session publica después del commit; SQL/Core deja reparación durable para reconciliación.

El publicador captura revisión y generación y usa CAS después del reemplazo para limpiar dirty. Una carrera o fallo mantiene la reparación pendiente. BD y filesystem no forman una transacción conjunta. El arranque repara derivados ausentes, inválidos u obsoletos.

La restauración adquiere el escritor antes de leer colisiones y consulta por lotes de hasta 400 identidades dentro de la misma transacción. Un conflicto revierte todo. Sólo una importación completa compatible promueve su raíz; editar una canción no puede promover soporte ni degradar raíces. El soporte no entra en FTS ni se publica como proyecto. `dispatchable_job` prepara el filtrado del futuro dispatcher; no acredita una cola ejecutable.

El backup usa `sqlite3.Connection.backup()`, valida integridad, FK y FTS antes de publicar y rota sólo copias propias de más de 14 días. Un fallo del origen mantiene la copia válida anterior. El scheduler comprueba al arrancar y cada hora si han transcurrido 24 horas; opera fuera del event loop sin solapamientos. La parada cancela mediante el callback de progreso y espera el hilo propio.

`restore_backup` exige backend parado y destino nuevo sin BD/WAL/SHM. Los backups no contienen medios. La restauración de snapshots comprueba el hash de medios presentes; no recupera medios ausentes. Consulta APIs, fuentes y límites en la [guía de desarrollo](../desarrollo/server-y-contratos.md).

## Ejecución CPU local y publicación por toma

[ADR-0055](../decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) decide la ampliación aditiva posterior a 0005: `cpu_execution`, `publication_intent` y `publication_intent_revision`, junto con procedencia opcional en `job_attempt` y código de error opcional en `take`. Implementación y pruebas pendientes. Los intentos locales no son intentos de un engine. El contenido de cada revisión de publicación es inmutable; cambios de estado exigen CAS y autoridad vigente. Las revisiones preservan el historial de retry y los índices/semillas originales; una toma lista no se sobrescribe.

Los snapshots agregan estas tablas de forma opcional, conservan su historia y causalidad y excluyen capacidades de lease e identidad operativa de procesos. Restaurar no reactiva procesos; exige reconciliación de ejecuciones interrumpidas. La copia SQLite conserva los campos privados. Assets/toma lista/intención confirmada comparten una transacción BD; el rename de archivos y esa transacción se recuperan mediante la intención y no constituyen una transacción atómica conjunta.

El post agregado termina cuando cada toma solicitada tiene un resultado durable, incluso si el resultado es mixto o todas fallan por validación. El éxito musical y los estados por toma siguen siendo independientes. La futura importación durable del análisis y sus campos de causalidad se implementarán en una unidad posterior, sin falsear el terminal del engine.


La frontera de captura se concreta en [ADR-0060](../decisiones/ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md): la pareja nullable provenance/provenance_sha256 sólo se fija una vez antes de enviar; los reenvíos conservan esa evidencia y no reconstruyen intentos históricos desde el catálogo actual. La observación pre-send se distingue de los parámetros efectivamente ejecutados. Implementación y QA pendientes.


[ADR-0062](../decisiones/ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md) distingue evidencia sintética registrada por el server y procedencia aprendida. La clasificación y su binding se conservan en el contenido privado de provenance y su SHA, sin ampliar la DDL ni /v1. No acredita inferencia aprendida ni permite completar intentos legacy desde el catálogo actual.

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


## Procedencia CPU autónoma y formatos v2 (M2)

[ADR-0074](../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) fija el contrato pendiente de implementación: una única Take con `origin_kind` discriminado. En `inference`, `model_id`, `model_version` y `seed` siguen siendo obligatorios; sólo `cpu_edit` permite los tres NULL. Cero, cadena vacía e identidad del padre no representan ausencia. Los padres se preservan mediante linaje y hashes, no como inferencia ejecutada por el edit.

La excepción SQL alcanza únicamente `take` (esos tres campos), `publication_intent` (`seed`) y `publication_intent_revision` (`generation_job_id`, `winning_attempt_id`, `winning_ordinal`, `terminal_seq`, `terminal_sha256`, `seed`). Guardas SQL/ORM/import discriminadas conservan requisitos de inferencia y unicidad CPU propia ante NULL. No se reconstruyen otras tablas. Se preservan datos, IDs, FK entrantes/diferidas, índices, checks, triggers e invalidación de snapshots. Migración después del head real, exclusividad, backup con WAL restaurable, rollback e integridad/FK comprobados; `foreign_keys=ON` antes de runtime. Downgrade con CPU no representable rechaza antes de efectos.

La ejecución CPU posee receta/resultado propios y autoridad durable revalidada, sin JobAttempt ficticio. Publicación final conserva CAS, no-clobber y transacción assets/ready/committed; custodia UNKNOWN bloquea publicación, serving, limpieza y liberación de slot/staging. El post CPU de una generación M1 mantiene su autoridad musical original y formato v1.

CPU autónomo usa manifiesto v2 con executor del server, receta, entradas y herramientas/pins reales, derechos y `commercial_use` combinado. Un cierre portable de canción que incluya CPU usa song v2; cierre de inferencia conserva proyección v1 y hashes. Lectores nuevos despachan v1/v2, los antiguos rechazan versión desconocida; export/import conserva cierre completo sin PIDs/leases/custodia ni reactivación de procesos.

Las previews CPU A/B también usan v2. Son temporales autorizados del job, resueltos por recibo/contexto privado y CAS vigente: no crean Take, intención por toma ni `asset.subject_type=job`, valor excluido del schema actual. El plan/recibo tipado se fija antes de su RED. Detalle, listado, PATCH y restore de API server v2 exponen TakeV2; operaciones M1 que incluyan CPU rechazan 409 explícito después de autorización y antes de efectos, sin ocultar filas. Modelo y contratos de producto aún pendientes; este apartado documenta la decisión, no una migración aplicada.


## Autoridad del ciclo de almacenamiento

[ADR-0075](../decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md) concreta el journal de infraestructura por handle elegido para el controller de plataforma. El journal tendrá generaciones con PREPARE/COMMIT, CAS nativo e intenciones previas a los efectos; el server conserva la autoridad exclusiva sobre SQLite de producto. El recibo v1 publicado se conserva como semilla histórica y los consumidores nuevos deberán resolver la cadena sellada vigente. Un recibo leído o un hash aislado no autorizan mutaciones.

La implementación, recuperación y QA física del controller siguen pendientes. El diseño distingue fallos de proceso de power loss y mantiene cerrada la admisión ante commit/cierre inciertos. No cambia los componentes readonly aceptados ni promueve el VHDX de prueba a producción.


## Apéndice normativo M3 — Autoridad por sujeto D-02 (candidato seleccionado)

ROOT eligió PR-O1 el2026-10-11T18:10:35.263982+00:00 bajo delegación vigente. El [contrato completo](../roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md) fija envelope/recipe/receipt privados1,19parejas operation/subject, captura única y reglas owner/terminal/CAS/fallos. La adopción de estos requisitos para implementación futura espera revisión/QA/ROOT. No se anuncia migración aplicada, writer/grant/store publicado ni producto M3; este apéndice conserva byteexacto el prefijo anterior.

| Resultado de request | Pertenencia, unidad y autoridad |
|---|---|
| Asset | subject.kind asset no es nuevo valor Asset.subject_type. Stems son assets del Take, con roles stem:vocals/drums/bass/other y set completo requerido; no Take nuevo. Preview job es temporal privado con receipt/expiry/invalidation, sin Asset.subject_type job. Features se ligan al audio final |
| Analysis | Resultado por método y binding audio hash; revisión timing nueva con tokens/lyrics históricos. No overwrite encubierto de la unicidad actual take/kind/analyzer. Crudo engine no certifica import Analysis; D-03 cierra persistencia/revisiones |
| Artwork | Song y fuentes/rights/workflow congelados. Upload source upload no inventa modelo/seed. Elegir portada requiere acción explícita/CAS Song aparte |
| Render | VideoProject timeline/rev/hash conserva autoridad; plan derivado captura audio final/timing/artwork/features/perfiles/pins. Render/assets propios con receipt CPU real, sin ganador ficticio |
| Export | Export propio y paquete completo/audio final medido o original byteexacto. Sin Take/seed/JobAttempt ficticios; mezcla publicada como Take hijo pertenece a CPU M2 con todos sus padres |
| Import | Sujeto privado de operación por paquete y cierre íntegro, no enum Asset. Replay exige receipt propio; hash igual ajeno o colisión conflictiva rechaza. Source→local separado y manifiestos originales intactos; D-08 fija remap/catalog/quotas |
| Backup | Scope biblioteca/binding propio, sin Song/Take ficticios. Corte exclusivo SQLite+medios, restore nuevo y activación raíz/BD con intención/rollback propios. Backup diario sólo BD sigue operación distinta; D-09 cierra protocolos |

Sources/parents/lyrics/rights/profiles/revisions/execution_selection están exclusivamente en recipe. Los profiles capturan valores efectivos y readers cerrados, nunca alias al preset vivo ni dict abierto. Request hash y contexto runtime de intent/expected_revision/lease/custodia permanecen fuera recipe/envelope. Contexto activo no viaja portable ni restore reactiva jobs/leases. Cambiar maestro/letra/preset después no retargetea captura; revocar/eliminar fuente puede bloquear autoridad actual, sin reemplazo silencioso.

Intención lógica por unidad reserva owner/scope/request/result_key antes de efectos. Revisión int estricta inicial1 y monotónica≤2^63−1; CAS compara identidad/hashes/result/revisión activa/estado esperado con autoridad/custodia/binding actuales. Revisiones de entidad siguen su lector y D-03, sin default/coerción. Contenido de revisión y committed son inmutables; retry explícito conserva request/historia y crea ejecución/ordinal/revisión nuevos sólo tras reconciliación, nunca overwrite de ready.

Receipt privado distingue engine_raw, cpu_result, upload_result, publication, import y maintenance. Terminal de ejecución no equivale a commit durable. Lost ACK o cancel posterior al commit reproducen el mismo éxito sin regenerar/doble publicación; cancel anterior bloquea nuevo commit y reconcilia efectos propios. UNKNOWN conserva custodia y bloquea efectos/publicación/serving/cleanup/slot/staging. No se asume transacción conjunta FS/SQLite; rename→commit exige intención/evidencia propias y replay bajo CAS. No se adopta un medio por SHA/path.

Límites nuevos de captura ratificados: request2097152bytes, recipe1048576bytes, depth32, sources/parents/required_roles64, profiles16/payload65536bytes, lyrics64/text32768caracteres; labels512, paths1024, rev≤9223372036854775807. Presupuestos agregados se verifican antes enqueue y overflow rechaza sin truncar/chunking implícito. No cambian límites históricos ni cuotas media/catalog/biblioteca, que fija D-08/D-09.

Commercial_use es AND de derechos de entradas/padres/letra/herramientas y modelo sólo si se ejecutó; evidencias legales/consent siguen exigibles. CPU/upload no copia modelos de ancestros como ejecutados. Familias/private1 no se confunden con manifest/song1/2 ni input_receipt2. Readers históricos conservan bytes/versiones/hashes. Si una ausencia/sujeto no cabe en formatos vigentes, D-04 define formato discriminado y lector antes RED; TimelineV1 cerrado no recibe extras.

D-02 no modifica DDL ni amplía la excepción de ADR-0074 más allá de sus tres tablas; D-03 cierra SQL/constraints/revisiones y cualquier decisión adicional. Baseline23tablas inmutable, cambios futuros aditivos salvo excepción expresamente aceptada. Contratos públicos siguen code-first, DTO M1 compatible y engine/v1 sólo adición opcional. Gates D-03–09 pendientes bloquean ramas sin catch-all. O1/ADR-0080 y D-12 siguen vigentes; M1formal0/17, M2=4/30, M3contractual1/42 y funcionesM3=0; ni este documento ni K1 candidato habilitan runtime.
