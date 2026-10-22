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

## Almacenamiento operativo

[ADR-0089](../decisiones/ADR-0089-reencauce-tras-codex.md) aparca el VHDX ext4 y el journal Windows de ADR-0069/0075. Los datos viven en `data/`, montado en los contenedores. Cada take se publica así:

1. Se escribe en un directorio de staging.
2. Se mueve con `rename` normal a `data/songs/<song_id>/<take_ulid>/`. El id es único, así que no hay colisión y no hace falta `NOREPLACE`.
3. Se confirma la fila en SQLite. Esa fila es la autoridad: un directorio sin fila es huérfano y se limpia al arrancar.

## Procedencia CPU autónoma y formatos v2 (M2)

[ADR-0074](../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) fija el contrato pendiente de implementación: una única Take con `origin_kind` discriminado. En `inference`, `model_id`, `model_version` y `seed` siguen siendo obligatorios; sólo `cpu_edit` permite los tres NULL. Cero, cadena vacía e identidad del padre no representan ausencia. Los padres se preservan mediante linaje y hashes, no como inferencia ejecutada por el edit.

La excepción SQL alcanza únicamente `take` (esos tres campos), `publication_intent` (`seed`) y `publication_intent_revision` (`generation_job_id`, `winning_attempt_id`, `winning_ordinal`, `terminal_seq`, `terminal_sha256`, `seed`). Guardas SQL/ORM/import discriminadas conservan requisitos de inferencia y unicidad CPU propia ante NULL. No se reconstruyen otras tablas. Se preservan datos, IDs, FK entrantes/diferidas, índices, checks, triggers e invalidación de snapshots. Migración después del head real, exclusividad, backup con WAL restaurable, rollback e integridad/FK comprobados; `foreign_keys=ON` antes de runtime. Downgrade con CPU no representable rechaza antes de efectos.

La ejecución CPU posee receta/resultado propios y autoridad durable revalidada, sin JobAttempt ficticio. Publicación final conserva CAS, no-clobber y transacción assets/ready/committed; custodia UNKNOWN bloquea publicación, serving, limpieza y liberación de slot/staging. El post CPU de una generación M1 mantiene su autoridad musical original y formato v1.

CPU autónomo usa manifiesto v2 con executor del server, receta, entradas y herramientas/pins reales, derechos y `commercial_use` combinado. Un cierre portable de canción que incluya CPU usa song v2; cierre de inferencia conserva proyección v1 y hashes. Lectores nuevos despachan v1/v2, los antiguos rechazan versión desconocida; export/import conserva cierre completo sin PIDs/leases/custodia ni reactivación de procesos.

Las previews CPU A/B también usan v2. Son temporales autorizados del job, resueltos por recibo/contexto privado y CAS vigente: no crean Take, intención por toma ni `asset.subject_type=job`, valor excluido del schema actual. El plan/recibo tipado se fija antes de su RED. Detalle, listado, PATCH y restore de API server v2 exponen TakeV2; operaciones M1 que incluyan CPU rechazan 409 explícito después de autorización y antes de efectos, sin ocultar filas. Modelo y contratos de producto aún pendientes; este apartado documenta la decisión, no una migración aplicada.



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


#### Procedencia CPU durable — O1/ADR-0074

Take conserva entidad única. `origin_kind=inference` mantiene modelo/versión/seed reales obligatorios; `cpu_edit` usa tres NULL y exige `cpu_execution_id`/`cpu_plan_sha256` desde PRE-render. CPU task audio.edit y derivation edit tienen root mínimo original alcanzable, source o ambas crossfade_a/crossfade_b, contexto single/instrumental/composite sin versión única inventada. Queued no usa duración solicitada como medida.

Take.batch_id CPU es ULID no-null igual a cpu_pre_render_reservation.id de la ejecución activa, agrupación real propia de esta operación. Plan.reservation.reservation_ref.id y receipt/binding/authority.reservation_id derivan el mismo grupo sin otro campo batch duplicado. batch_id no es FK ni requiere tabla Batch; conserva VARCHAR26 NOT NULL/CHECK ULID/ix_take_batch_id y todos valores/semántica M1 históricos. NULL, batch padre/arbitrario/malformed/otra reserva/cross-owner o ordinal activo distinto rechaza en SQL/ORM/lectores/import. La relajación ADR-0074 de Take sigue limitada a modelo/versión/seed.

Tabla aditiva `cpu_pre_render_reservation` / `CPUPreRenderReservation` contiene exactamente id/owner_id/song_id/job_id/cpu_execution_id/execution_ordinal/take_id/root_id/output_index, binding CpuTakeReservationV2, request/recipe/composition/provenance/plan_sha256 y created_at/updated_at/deleted_at. IDs son ULID/VARCHAR26, ordinal PositiveInt/output0 INTEGER, hashes VARCHAR64, binding JSON estricto, timestamps UTC. FK diferidas NO ACTION a user/song/job/execution/take/root; UNIQUE execution/output y job/ordinal/output. CpuExecution añade cpu_take_id/cpu_reservation_id diferidas no-null sólo edit, result_receipt/result_receipt_sha256 nullable pareja. PRE-render crea job+Take+aristas+reserva+ejecución prepared completas, sin intent/revision/raw/receipt ficticios. Binding del plan nunca contiene IDs PUB futuros.

PublicationIntent final nace en reservePUB después de raw/receipt/cierre reales: origin CPU/seed NULL, cpu_reserved_revision_id FK diferida obligatoria y active_revision_id NULL inicialmente. Revision final añade cpu_reservation_id FK, cpu_recipe/composition/plan/receipt_sha256 y cpu_bound_execution_revision/cpu_bound_intent_revision PositiveInt; todos NULL sólo inferencia. Source/provenance SHA mantienen dominio y NOT NULL, nunca SHA marcador/padre ni rebind posterior. Generation/winner/terminal engine/seed NULL sólo CPU. UNIQUE inferencia se conserva, CPU intent/execution/output y reserva final únicos. El ciclo intent↔revision se cierra en esta fase, nunca PRE-render. Guardas recíprocas/reader final binding impiden mover paquetes entre intentos.

Sólo take/intent/revision pueden reconstruirse bajo ADR-0074; CpuExecution sólo ALTER aditivo y reserva nueva sólo CREATE. Se mantienen FK/checks/índices/triggers/linaje/historia. CAS exacto/lost ACK recupera mismos IDs; cada retry previo a ready tiene nueva ejecución/reserva/plan/ordinal/receipt. CAS retargetea juntos Take execution/hash/batch hacia nueva reserva.id con capturas y destino exactos; cada reserva histórica conserva su grupo propio derivado. Historia final inmutable y ningún rebind ready, tampoco batch. Source SHA puede igualar padre sólo con evidencia real propia. §4.4 fija definición completa e índices sin duplicar inversas.

CpuExecution distingue inference_post, cpu_edit y cpu_preview; plan edit tuple audio.edit/1/2 es CpuEditPlanV2 cerrado. Recibo real separado y paquete PreparedPackageCPU v2 ligan receta, plan, fuente medida, padres/derechos/herramientas y cierre propio. PostPlan/PreparedPackage M1 conservan bytes y significado. UNKNOWN bloquea publicación, serving, cleanup y slot. Refs/hash aparentes o recipe puro no prueban ejecución.

Replay 0006 mantiene install legado congelado por revisión/columnas existentes sin metadata nueva; nuevas guardas sólo en revisión CPU posterior al head revalidado. Migración exige entry exclusiva, backup WAL restaurado y full inventory; FK OFF antes BEGIN, reconstrucción create-copy-drop-rename transaccional sólo tres tablas, rollback probado y FK ON antes runtime. Downgrade con cualquier CPU no representable rechaza antes de efectos; no borra.

API TakeV2 es unión code-first y cuatro operaciones v2; CpuProvenanceDTO añade reservation_id real junto a execution_id y receipt nullable antes de resultado. TakeCpuEditV2.batch_id obligatorio ULID iguala esa reservation_id activa; PATCH/restore no lo edita. M1 tras autorización rechaza CPU 409 antes de update/restore; lista entera no oculta filas. Song v2 conserva todas reservas PRE-render/ejecuciones/ordinals/antecedentes/rights/history por inversas, aun prepared/failed/deleted sin PUB, y revisiones finales sólo cuando existen. Schema/reader/import exigen batch propio activo y derivación propia por cada ordinal histórico. Excluye posesión operativa; v1 sin CPU omite tabla nueva/defaults y conserva proyección/digests/batch exactos. Import valida grafo/fases/hashes antes de writes, no reactiva procesos y exige reconciliación real antes de servir.


## Apéndice normativo M3 — Persistencia tipada D-03 (propuesta seleccionada)

PD-O1 mantiene el baseline y añade40tablas propias `m3_*`. Su especificación de columnas, tipos, nullability, PK/UNIQUE/FK/checks, índices, guards, readers, fases y rollback está en §4 del contrato `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md`. Fuente seleccionada bajo delegación ROOT, pendiente revisión/QA/adopción; no DDL ejecutado ni función M3 acreditada.

| Familia aditiva | Tablas y obligación |
|---|---|
| Scope/capturas | m3_scope, m3_capture, m3_capture_dependency, m3_source_snapshot, m3_rights_snapshot. Song existente o reserva import propia; biblioteca binding propio sin Song/Take ficticios. Bytes/reader/hash y dependencias cerrados; derechos verificables |
| Letra/audio | m3_lyrics_context, m3_lyrics_member, m3_lyrics_binding, m3_audio_binding. Historia none/single/composite y audio efectivo medido: hash/rate/channels/frames/duración exacta; mapa puro no acredita salida |
| Stems/mix | m3_stem_set, m3_stem_member, m3_mix_revision, m3_mix_stem, m3_mix_head.4roles completos y formato/origen común; revisiones inmutables; mute domina solo, cualquier solo filtra no solos; ganancias lineales finitas; bytes de master/stems intactos |
| Analysis/timing | m3_analysis_result, m3_analysis_head, m3_timing_revision, m3_timing_line, m3_timing_word, m3_timing_region, m3_timing_head. Resultados por método/outcome y correcciones con tokens/bindings/initial/audio originales, tiempos dentro de duración e incertidumbre/missing/instrumental honestos |
| Preset/video | m3_preset_revision, m3_preset_source, m3_preset_head, m3_video_revision. Edición sella revisión nueva y cada uso congela valores/refs; timeline rev/hash conserva autoridad histórica |
| Request | m3_request, m3_request_source, m3_request_parent, m3_request_rights, m3_request_revision. Índices exactos de recipe D-02, sin sidecar/doble autoridad ni JSON libre;19parejas/7sujetos |
| Ejecución/autoridad | m3_intent, m3_execution, m3_execution_stage, m3_custody, m3_intent_revision, m3_phase_evidence. Reserva revision1 y evidencia existente antes de efectos; CAS de identidad/estado/revisión/cursor; custodia separada; UNKNOWN bloquea efectos y serving |
| Recibos/publicación | m3_receipt, m3_receipt_artifact, m3_seal, m3_result. Raw/CPU/upload y final publication/import/maintenance discriminados; cierre sellado, roles exactos y entidad/resultado/receipt en mismo commit SQLite; no FS+SQLite atomicidad inventada |

`analysis` sigue UNIQUE(take_id,kind,analyzer_id), con analyzer_version fuera de la clave. Ninguna corrección ni método nuevo reescribe fila/data original. Asset.subject_type sigue take/artwork/shot_version/render/export/character/lora/cli_run; no job/analysis/import/backup. Preview temporal sigue privado del job; import/backup tienen capturas/recibos propios, no Asset ni entidad ficticia.

Todas las FK nuevas son diferidas con NO ACTION; cada referencia tiene índices y validación forward/inverse de owner y pertenencia transitiva. Content roots/children/capturas son append-only; seal único impide añadir children posteriores. Head/intent/custody son los únicos cursores mutables por CAS; scope sólo materializa Song reservada en commit import íntegro. Rights, tokens/texto histórico, audio y receipts sellados no se sobrescriben. Baseline current master/letra/portada y preset actual pueden cambiar sin retargetear historia.

FIX1 B01 fija para las11familias internas source/rights/lyrics/audio/stems/mix/analysis/timing/preset/video/result el conjunto exacto de todos los campos root/H, NULLs, rows hijas tipadas y ordenadas, más JSON reservado `seal_kind=m3_seal.kind` y `schema_version=1`. Root.kind se conserva cuando existe; nunca se añade a roots sin esa columna. Namespace reservado cerrado seal_kind/schema_version/members/bindings/stems/lines/words/regions/sources, con arrays sólo por familia §4.11 del contrato, disjunto de las40listas de columnas/H/header capture. No extras, gaps, claves duplicadas ni overwrite. Request/recipe/receipt D-02, wrappers, perfiles, fases e históricos mantienen schemas originales y no reciben seal_kind. G02/G09 validan reader/family/version, bytes canónicos completos y SHA del payload con ambos discriminantes cuando aplican, comparando SQL sin alterar kind. Hashes originales de fuente/evidencia conservan su dominio; no hash autorreferente ni alias/default de la proyección ambigua anterior no adoptada. No renombra columnas SQL ni crea versión histórica. Casos positivos/negativos FIX1 por todas las familias quedan en PD-01/04/10/17.

Estados intent reserved/prepared/committed/failed/cancelled y fases reserved/executing/executed/prepared/renamed/committed/failed/cancelled tienen evidencia existente propia. `result_evidence_ref` no es nullable: reserved usa reservation1 sin receipt succeeded, execution usa hechos reales y sólo commit usa terminal final. Cancel previo impide commit; commit durable prevalece ante cancel tardío/ACK perdido con replay exacto. Retry explícito conserva captura/result_key y añade execution ordinal/revisión, después de reconciliar custodia; UNKNOWN nunca autoriza limpieza ni nueva ejecución.

Migración aditiva sobre head revalidado (snapshot0007), sin editar0001–0007 ni ampliar la excepción ADR-0074 más allá de take/publication_intent/publication_intent_revision. Sin backfill ficticio de revisiones, mediciones, rights o ganadores. Downgrade sólo si todas las tablas M3 están vacías y no hay custodia/refs/medios pendientes, tras comprobación anterior a cualquier DROP. Con datos se conserva historia/readers o se restaura corte completo en biblioteca nueva, jobs/leases inertes y activación raíz/BD conjunta bajo D-09.

Readers cerrados D-03 se registran en **todas** las conexiones antes de DML; ausencia, versión desconocida o gate externo faltante falla cerrada. D-04 fija paquetes/readers de publicación; D-05/06/07 perfiles y mediciones; D-08 catálogo/cierre/importmap; D-09 cut/binding/restore/rollback. Esos gates bloquean consumo concreto hasta ratificación; no completan con defaults ni alteran históricos v1/v2, schema/DTO M1 o /v1. Matriz PD-01..PD-20 del contrato exige pruebas futuras SQL/migration/races/rollback/legacy/privacy y conserva E2E/M-48 del plan.


Los datos de D-03 conservan las40tablas/11sellos/guards y FIX1: `root.kind` SQL intacto y `seal_kind` reservado sólo en sus schemas internos. D-04 agrega formats/readers, no columnas, tipos ORM ni excepción SQL. Asset no admite job/analysis/import/backup; Analysis original UNIQUE/data permanece inmutable. CPUv2 no se amplía a sujetos M3 por analogía. Import/backup usan capturas propias, preview temporal no crea Asset/Take ficticios.

Song con cierre CPU/historia mixta usa SongCPUv2 original de ADR-0074; Song sin CPU conserva Songv1. Todos los índices portables M3 usan **siempre** `production.song_bundle/1` como familia nueva que envuelve snapshot_ref y originals ByteRef, sin redefinir song1/song2. Closer conserva todos los takes/masters/ancestros, aristas/roles/maps, letras/context/tokens/revisiones, Analysis/Mix/artwork/vid/exports/presets/refs/metadata/rights/media/manifests y causalidad necesaria. Catálogo/proyección/mapa/cuotas D-08 sigue gate propio. Una proyección remapeada nueva posee IDs/hash propios y referencias a originals byte-exactos; no reescribe source IDs/owner/manifests ni crea inferencia del importador.

Package preparado→prepared artifact sin publication_ref→evidencia previa evita ciclo SHA; import/backup usa validación/maintenance_execution previa D-08/D-09 y no receipt final anticipado. Final receipt referencia package y artifact final referencia final receipt, fuera del package. Sólo final committed propio acredita visibilidad tras autoridad real/CAS/custodia. Historia imported de receipts/requests/planes permanece inerte sin tokens/leases/PIDs/custody viva. Biblioteca restaura en destino nuevo validado y activa BD/raíz juntas sólo D-09; pending reader/gate bloquea, no default/alias/rewriting históricos.

Export audio/stems/video/lyrics exige metadata_ref ByteRef production.export_metadata/1 ligado al Take efectivo. Export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package, incluso con Takes; título/letra/portada/revisiones se recuperan por closure Songv1/SongCPUv2/SongBundleM31. Song válida master NULL/takes [] conserva historia sin metadata de Take ni Take/audio ficticios. Operation/kind/payload/profile deben coincidir con D-02; gate ausente bloquea antes efectos.
