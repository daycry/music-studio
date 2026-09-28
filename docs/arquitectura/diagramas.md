---
documento: diagramas
titulo: Diagramas — arquitectura y workflow de canciones
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Diagramas

## 1. Arquitectura

```mermaid
flowchart TB
    user(["👤 Usuario<br/>navegador en 127.0.0.1"])

    subgraph WEB["web · Next.js :3000"]
        ui["Crear · Canciones · Vista de canción<br/>Editor de vídeo · Personajes · Sistema"]
        player["Reproductor persistente<br/>wavesurfer.js · Web Audio"]
    end

    subgraph SERVER["server · FastAPI :8000 (sin torch)"]
        api["API REST<br/>/songs /takes /videos /characters"]
        sse["SSE /events<br/>progreso en vivo"]
        disp["Dispatcher<br/>1 trabajo GPU a la vez<br/>prioridad · nocturnos"]
        db[("SQLite WAL<br/>data/db/studio.sqlite")]
        post["Worker CPU<br/>audio-post · ffmpeg LGPL<br/>loudness · FLAC/MP3 · picos<br/>manifiestos · render · backups"]
        remote["Adapters externos<br/>(carril remote)<br/>OPCIONALES"]
    end

    subgraph ENGINES["Engines · Docker · 127.0.0.1 · offline (sin descargas) · contrato /v1 · 1 modelo en VRAM"]
        ace["engine-acestep :8101<br/>ACE-Step 1.5 (MIT)<br/>música"]
        comfy["engine-comfy :8110<br/>ComfyUI headless<br/>Wan 2.2 · InfiniteTalk<br/>Qwen-Image · FLUX.2 klein"]
        llm["engine-llm :8120<br/>Gemma 4 12B Q4 (GGUF)<br/>letras · guion"]
        ana["engine-analysis :8130<br/>beat_this · Qwen3-ASR<br/>ForcedAligner · CLAP · Audiobox"]
        mock["engine-mock :8199<br/>tests y desarrollo UI"]
    end

    subgraph EXT["Servicios externos · OPCIONALES · apagados por defecto"]
        claude["Claude API<br/>(letras)"]
        vapi["APIs de vídeo<br/>(planos concretos)"]
    end

    subgraph FS["Carpeta del proyecto (todo dentro)"]
        models[("models/<br/>safetensors · gguf · onnx<br/>models.lock.json · SHA-256")]
        songs[("data/songs/‹song_id›/<br/>takes · artwork · video<br/>manifest.json · song.json")]
        tmp[("data/tmp/‹job_id›/")]
    end

    gpu{{"RTX 5070 · 12 GB<br/>sm_120 · BF16"}}

    user --> ui
    user --> player
    ui -- "HTTP JSON" --> api
    sse -- "eventos" --> ui
    player -- "audio con Range" --> api
    api <--> db
    api --> disp
    disp -- "progreso" --> sse
    disp -- "POST /v1/jobs · NDJSON<br/>/v1/unload" --> ENGINES
    disp -- "carril remote" --> remote
    remote -. "solo si está activado" .-> EXT
    ENGINES --> gpu
    ENGINES -- "leen pesos (ro)" --> models
    ENGINES -- "escriben salida" --> tmp
    tmp -- "salida cruda" --> post
    disp -- "carril cpu" --> post
    post --> songs
    post --> db
    api -- "sirve ficheros" --> songs
```

**Claves de diseño**

- El **server** es la única fuente de verdad y el único que escribe en la base de datos. Su **worker CPU** hace el post-proceso, los manifiestos y el render ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)); los engines solo devuelven salida cruda.
- Los **engines** no guardan estado ni tocan la base de datos. Cada familia de modelo va en su propio contenedor, porque necesitan versiones de dependencias incompatibles entre sí.
- El **dispatcher** descarga el modelo del engine activo antes de usar otro (`POST /v1/unload`), porque solo cabe uno en 12 GB.
- Lo **externo** va con línea discontinua: los adapters viven en el server (carril `remote`), están apagados de fábrica y quedan registrados en el manifiesto ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)).

## 2. Workflow de una canción

```mermaid
flowchart TD
    start(["Nueva idea"]) --> mode{"¿Cómo empiezo?"}
    mode -- "Modo simple" --> simple["Describo la canción<br/>el LLM local propone letra y estilo"]
    mode -- "Modo personalizado" --> custom["Escribo la letra con secciones<br/>[verse] [chorus] [bridge] y el estilo"]
    mode -- "Desde audio propio" --> upload["Subo tarareo, maqueta o voz<br/>+ declaración de derechos"]
    simple --> edit["Reviso y edito letra y estilo"]
    custom --> edit
    upload --> edit
    edit --> decl["Declaro la autoría de la letra<br/>propia · asistente · dominio público · con permiso"]
    decl --> song[("🎵 CANCIÓN = PROYECTO<br/>se crea (borrador) o se reutiliza")]

    song --> gen["Generar takes<br/>1–4 variantes A/B"]
    gen --> queue["Cola → engine-acestep<br/>progreso real por SSE"]
    queue --> postp["Post-proceso en el server<br/>validación · FLAC + MP3 · picos · manifiesto"]
    postp --> analysis["Análisis<br/>BPM · beats · secciones · tiempos de la letra"]
    analysis --> review{"Escucho y valoro<br/>★ · etiqueta · comparador A/B"}

    review -- "No me convence" --> iterate{"¿Qué cambio?"}
    iterate -- "Otra semilla" --> var["Variación"]
    iterate -- "Alargar" --> ext["Extender"]
    iterate -- "Un tramo" --> rep["Regenerar sección t0–t1"]
    iterate -- "Otro estilo" --> cov["Cover / reinterpretar"]
    iterate -- "La letra" --> lyr["Nueva versión de la letra<br/>(asistente o a mano)"]
    var & ext & rep & cov --> child["Take hijo<br/>linaje: parent · root · derivation"]
    lyr --> gen
    child --> queue

    review -- "Esta es" --> master["⭐ Marcar TAKE MAESTRO"]

    master --> prod{"Producción"}
    prod --> stems["Stems + mezclador"]
    prod --> cover["Portada<br/>generada o subida"]
    prod --> lrc["Letra sincronizada<br/>.lrc · .srt · karaoke"]
    prod --> video["🎬 Proyecto de vídeo"]
    prod --> export["Exportar<br/>streaming −14 · vídeo −23 · podcast −16<br/>WAV 48 kHz · stems · zip de la canción"]

    video --> vcfg["Formato 16:9 / 9:16 · estilo visual<br/>tratamiento · nivel N0–N3"]
    vcfg --> chars["Personajes<br/>de la biblioteca o desde mis fotos<br/>+ consentimiento"]
    chars --> script["Guion automático<br/>planos cortados al beat y a las secciones"]
    script --> shots["Por plano: imagen clave<br/>→ movimiento 2.5D · clip I2V · cantante con sincronía labial"]
    shots --> tl["Editor de timeline<br/>reordenar · ajustar al beat · subtítulos de la letra"]
    tl -- "Regenerar un plano" --> shots
    tl --> render["Render<br/>16:9 · 9:16 · clips cortos · cola nocturna"]

    stems & cover & lrc & render & export --> final(["✅ Canción en estado final"])
    master -. "si cambio el maestro después" .-> stale["⚠ El vídeo avisa: audio desfasado<br/>→ reanalizar y reajustar"]
    stale -.-> tl
```

**Lectura del diagrama**

- Todo cuelga de la **canción** ([ADR-0013](../decisiones/ADR-0013-cancion-como-proyecto.md)).
- Iterar nunca sobrescribe: siempre crea un **take hijo** en el árbol de versiones.
- El **take maestro** es la bisagra: stems, portada, vídeo y exportación trabajan sobre él.
- El vídeo es incremental por plano: se regenera solo lo que cambia ([video.md](./video.md)).
