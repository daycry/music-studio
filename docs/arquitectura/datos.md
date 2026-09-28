---
documento: arquitectura-datos
titulo: Modelo de datos, ficheros, linaje y manifiesto
estado: vigente — el esquema completo entra en la primera migración de M1
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Modelo de datos

**Reglas** ([CONSTITUTION](../CONSTITUTION.md) §2):
- Solo el server escribe en la base de datos.
- La primera migración de M1 crea **todas** las tablas de este documento, también las que no se usarán hasta M3–M5. Crearlas vacías no cuesta nada y evita migraciones que rompan datos más adelante.
- Desde esa migración, todas las demás son **aditivas**. Renombrar o borrar una columna que ya tiene datos exige un ADR.

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
| `asset` | `owner_type` (`take`/`artwork`/`shot_version`/`render`/`export`/`character`/`lora`/`cli_run`), `owner_id`, `role` (`master`/`listen`/`peaks`/`manifest`/`stem:vocals`/`keyframe`/`clip`/`video`/`zip`…), `path` (relativa a `data/`), `media_type`, `sha256`, `bytes`, `meta` (JSON: sample_rate, channels, lufs, true_peak, width, height, fps, duration_s) |
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
| `job` | `task`, `lane` (`gpu`/`cpu`/`remote`), `priority` (`interactive`/`normal`/`batch`/`nightly`), `not_before?`, `status` (`queued`/`blocked`/`running`/`succeeded`/`failed`/`cancelled`/`interrupted`), `attempt`, `max_attempts`, `engine_id?`, `model_id?`, `request` (JSON completo), `stage?`, `progress?`, `error_code?`, `error?`, `telemetry?` (JSON), `song_id?`, `started_at?`, `finished_at?`, `cancel_requested_at?` |
| `job_dependency` | `job_id`, `depends_on_job_id`. Forma el grafo de dependencias: take → análisis; imagen clave → clip → render ([ADR-0018](../decisiones/ADR-0018-cola-de-jobs.md)) |
| `setting` | `key`, `value` (JSON) |
| `provider` | `function` (`text`/`image`/`video`…), `name`, `enabled`, `config` (JSON sin secretos: las claves van en `.env`) |

**Búsqueda:** tabla virtual FTS5 `song_fts(title, style_prompt, lyrics)`, mantenida al día con triggers.

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
├── backups/                    # `sqlite3 .backup` diario + rotación de 14 días (SÍ se sincroniza)
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
├── tmp/<job_id>/               # salida en crudo de los engines; se limpia al terminar
├── trash/                      # ficheros de entidades borradas (30 días)
└── logs/
```

- **Cada canción es portable:** su carpeta contiene todo (audio, portada, vídeo, manifiestos y un `song.json` con las letras, los takes, las valoraciones, el linaje y el timeline). «Exportar proyecto» comprime esa carpeta; «Importar» reconstruye las filas de la BD a partir de `song.json`.
- **No se guarda WAV:** el FLAC es sin pérdida y ocupa en torno a un 40 % menos. El WAV a 48 kHz se genera al exportar.

## 3. Manifiesto de procedencia v1

Cada artefacto generado tiene su manifiesto: take, imagen, versión de plano, render y export. Lo escribe **el server** al terminar el post-proceso ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)) y lo guarda como `asset` con `role=manifest`, junto con su SHA-256. Esquema: `packages/contracts/manifest-v1.schema.json`.

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
