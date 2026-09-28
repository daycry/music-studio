---
documento: funcionalidades
titulo: Catálogo de funcionalidades
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Catálogo de funcionalidades

Cada funcionalidad tiene un ID estable (`F-xx`), el hito en que entra ([roadmap](../roadmap/README.md)) y la pieza que necesita. **Por defecto todo es local**; las APIs externas son alternativas opcionales ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)). 🆕 = no estaba en la planificación anterior.

**Hitos:**

| Hito | Contenido |
|---|---|
| **M0** | Entorno y motor (CLI) |
| **M1** | MVP del estudio |
| **M2** | Iteración creativa |
| **M3** | Producción, portada y vídeo con letra |
| **M4** | Vídeo musical |
| **M5** | Personalización avanzada |
| **—** | Futuro sin planificar |

## Canción = proyecto ([ADR-0013](../decisiones/ADR-0013-cancion-como-proyecto.md))

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-01 | 🆕 **Vista de canción**: pestañas Audio · Letra (M1) · Vídeo · Portada · Exportar (M3–M4). Recoge título, artista, estado (borrador/en curso/final/archivada), estilo, notas y etiquetas | M1 | `song` |
| F-02 | 🆕 **Take maestro**: marcar qué versión es «la canción». Vídeo, portada, stems y exportaciones la usan por defecto | M1 | `master_take_id` |
| F-03 | 🆕 **Versiones de la letra** con historial, comparación entre versiones y qué letra cantó cada take | M1 | `lyrics_version` |
| F-04 | 🆕 **Colecciones** (álbum/carpeta) con portada propia | M1 | `collection` |
| F-05 | 🆕 **Valorar y etiquetar takes** (1–5 ★, etiqueta «v3 estribillo nuevo») para decidir entre versiones | M1 | `take.rating/label` |
| F-06 | 🆕 **Exportar e importar la canción completa** como zip portable (audio, letra, portada, vídeo, manifiestos) | M3 | carpeta `data/songs/<id>/` |

## Crear audio

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-10 | **Modo personalizado**: letra con secciones (`[verse]`, `[chorus]`, `[bridge]`…) + estilo → takes con voz. Si no hay canción abierta, crea una canción borrador | M0 (CLI) · M1 | `music.song` |
| F-11 | **Instrumental** | M1 | `music.instrumental` |
| F-12 | **Variantes**: de 1 a 4 por petición (2 por defecto), agrupadas A/B | M1 | batch o N semillas |
| F-13 | **Controles avanzados**: duración, BPM, tonalidad, idioma, semilla, fuerza del estilo y pasos. Solo aparecen los que declara la tarea (`params_schema`) y sus features verificadas | M1 | `params_schema` + `features` |
| F-14 | 🆕 **Estilos a excluir** (prompt negativo) | M1 | feature `negative_prompt` (si está verificada) |
| F-15 | Chips de género y estilo | M1 | estático |
| F-16 | 🆕 **Modo simple**: describes la canción y el asistente propone letra y estilo, editables antes de generar | M2 | LLM local |
| F-17 | **Asistente de letras**: generar, reescribir una sección, continuar, cambiar el tono o sugerir la estructura. Salida en etiquetas válidas | M2 | LLM local; API opcional |
| F-18 | 🆕 **Calidad alta**: regenerar con más pasos o con el modelo grande (ACE-Step XL) | M3 | modo de VRAM |
| F-19 | 🆕 **Canción a partir de un audio propio** (tarareo, maqueta o voz) como referencia o para añadir acompañamiento. Exige declarar los derechos | M3 | `music.complete` / `music.cover` |

## Iterar sobre un take

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-20 | 🆕 **Variación**: misma petición con otra semilla, o ligeras variaciones del take | M2 | `music.retake` |
| F-21 | **Extender** desde el final o desde un punto, con letra y estilo para la continuación | M2 | `music.extend` |
| F-22 | **Regenerar una sección** `[t0, t1]` seleccionada en la onda | M2 | `music.repaint` |
| F-23 | **Cover / reinterpretar** con otro estilo, con control de fidelidad al original | M2 | `music.cover` |
| F-24 | 🆕 **Recortar, fundidos y crossfade** sin IA | M2 | post-proceso |
| F-25 | **Árbol de versiones** navegable (original → variantes → extensiones → secciones) | M2 (datos desde M1) | linaje |
| F-26 | 🆕 **Comparador A/B** de dos takes con el loudness igualado | M2 | web |

## Producción

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-30 | **Stems** (voz, batería, bajo, otros) a demanda | M3 | `audio.stems` (extract de ACE-Step o RoFormer) |
| F-31 | **Mezclador de stems**: mute, solo, volumen y exportar la mezcla | M3 | Web Audio |
| F-32 | **Exportación**: MP3 y FLAC en M1. Desde M3: destinos (−14/−23/−16 LUFS), WAV 48 kHz, zip de stems, metadatos y letra embebida | M1 · M3 | [pipeline-audio.md](../arquitectura/pipeline-audio.md) |
| F-33 | 🆕 **Análisis del take**: BPM y beats (M1); tonalidad, secciones y loudness (M3). Se calcula al terminar cada take y alimenta el vídeo | M1 (básico) · M3 | `audio.beats` (beat_this), librosa, estructura de la letra |
| F-34 | 🆕 **Letra sincronizada** (tiempos por palabra y línea): vista karaoke y exportación `.lrc`/`.srt` | M3 | `audio.align_lyrics` (Qwen3-ForcedAligner) |
| F-35 | 🆕 **Portada**: generada desde el estilo y la letra (o subida), con varias opciones y edición con referencia; se exporta con el audio | M3 | engine-comfy (Z-Image / Qwen-Image) |

## Vídeo ([video.md](../arquitectura/video.md), [ADR-0015](../decisiones/ADR-0015-video-musical-por-niveles.md))

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-40 | 🆕 **Vídeo con letra (N0)**: tipografía cinética sincronizada palabra a palabra sobre la portada, un fondo o un visualizador. En minutos | M3 | análisis + ffmpeg/ASS |
| F-41 | 🆕 **Visualizador reactivo** (onda, espectro, partículas) como fondo o vídeo propio | M3 | ffmpeg / WebGL |
| F-42 | 🆕 **Proyecto de vídeo** por canción: formato (16:9, 9:16, 1:1), estilo visual (cinematográfico, sci-fi, ciudad, abstracto…), tratamiento en texto libre y nivel N0–N3 | M4 | `video_project` |
| F-43 | 🆕 **Guion automático**: lista de planos cortados al beat y a las secciones, con fragmento de letra, descripción, cámara y tipo de plano. Editable | M4 | LLM local + análisis |
| F-44 | 🆕 **Personajes coherentes**: biblioteca global de personajes reutilizables en cualquier canción. Un personaje = nombre + descripción + imágenes de referencia (subidas o generadas) + LoRA opcional | M4 | Qwen-Image-Edit / FLUX.2 klein |
| F-44b | 🆕 **Protagonista desde tus fotos**: subir 1–10 fotos (tuyas, de un personaje dibujado, de una mascota…) para que el protagonista del vídeo sea ese. Con 1–3 fotos se usan como referencia directa; con 10–20 se puede entrenar un LoRA para más fidelidad (F-73). Exige **declarar los derechos o el consentimiento** de la persona que aparece | M4 | edición con referencia + I2V + InfiniteTalk |
| F-44c | 🆕 **Imágenes propias como plano o fondo**: subir fotos o ilustraciones y usarlas tal cual como imagen clave de un plano (animadas con 2.5D o I2V), como fondo del vídeo con letra o como portada | M3 (portada, N0) · M4 | `artwork.source = upload` |
| F-45 | 🆕 **Guion gráfico (N1)**: imagen clave por plano, animada con Ken Burns y parallax 2.5D. Regenerar cualquier plano por separado | M4 | engine-comfy + Depth Anything V2 Small |
| F-46 | 🆕 **Planos generativos (N2/N3)**: imagen a vídeo desde la imagen clave, con transiciones ancladas entre planos | M4 | Wan 2.2 / 2.1 FLF2V |
| F-47 | 🆕 **Cantante con sincronía labial**: el personaje canta la voz separada del take | M4 | InfiniteTalk (+ LatentSync para retocar) |
| F-48 | 🆕 **Editor de línea de tiempo**: reordenar planos, ajustar cortes (con imán al beat), transiciones, pista de subtítulos con la letra, títulos y créditos | M4 | `timeline.json` + web |
| F-49 | 🆕 **Render**: 16:9 y 9:16 con reencuadre por plano, clips cortos del estribillo, subtítulos quemados o `.srt`, cola nocturna para N3 y reescalado opcional | M4 | ffmpeg + cola |
| F-50 | 🆕 **Aviso de audio desfasado**: si cambia el take maestro, el vídeo ofrece reanalizar y reajustar | M4 | `video_project.take_id` |
| F-51 | 🆕 **Proveedor externo por plano** (opcional): enviar planos concretos a una API de vídeo, con el coste visible | M4 | adapter externo (server, carril `remote`) |

## Biblioteca y reproducción

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-60 | **Biblioteca de canciones**: grid o lista con portada, búsqueda (título, letra, estilo), filtros (colección, estado, fecha, modelo, etiquetas) y favoritas. Los takes se ven dentro de cada canción | M1 | server |
| F-61 | **Reproductor persistente** con cola y salto A/B entre variantes | M1 | web |
| F-62 | **Papelera** de 30 días (canciones y takes) | M1 | server |
| F-63 | Preescucha al pasar el cursor (desactivable) | M1 | web |

## Personalización

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-70 | 🆕 **Presets** («personas»): estilo, parámetros, referencia de timbre y estilo visual con nombre | M3 | server |
| F-71 | 🆕 **Referencia de timbre o estilo por audio** (fragmento propio o con derechos) | M5 | `music.song` feature `timbre_ref` |
| F-72 | 🆕 **LoRA de estilo musical personal** entrenado con música propia (con derechos) | M5 | `music.song` feature `lora` + `train.lora` |
| F-73 | 🆕 **LoRA de personaje visual** para máxima coherencia en vídeo | M5 | entrenamiento en 12 GB (block swap) |
| F-74 | **Segundo motor musical** seleccionable (HeartMuLa si gana en castellano en M0) | M5 | engine de otra familia |

## Sistema

| ID | Funcionalidad | Hito | Pieza |
|---|---|---|---|
| F-80 | **Gestión de modelos**: descarga fijada por revisión, SHA-256, licencia, tamaño y VRAM visibles | M0 (script) · M1 (UI) | `models.lock.json` |
| F-81 | **Cola** visible, cancelar, reintentar y 🆕 prioridad y trabajos «nocturnos» | M1 · M4 | dispatcher |
| F-82 | **Manifiesto de procedencia** por take, imagen y plano de vídeo, con su panel | M1 | [datos.md](../arquitectura/datos.md) |
| F-83 | **Página de sistema**: GPU, VRAM, RAM, modelo cargado, disco | M1 | engines + server |
| F-84 | 🆕 **Batería de evaluación automatizada** (10 briefs, loudness igualado, anonimizada, WER/CLAP) | M0 | `scripts/eval/` |
| F-85 | 🆕 **Copia de seguridad** de la biblioteca y restauración | M3 | server |
| F-86 | 🆕 **Ajustes de proveedores**: activar o desactivar alternativas externas por función, con clave y coste | M2 | ADR-0014 |

## Futuro (sin planificar)

- Acceso desde otros dispositivos de la LAN con token (PWA en el móvil) y **publicar en redes** (YouTube, TikTok) desde la app.
- Multiusuario y comercialización ([gate GC](../legal/comercializacion.md)).
- «Studio»: línea de tiempo multipista de audio con generación por pista.
- Exportación a MIDI.
- Baile al ritmo (Wan-Dancer) y avatares de cuerpo entero.
- **Fuera de alcance:** clonar la **voz** de personas reales, y usar la **imagen** de terceros sin su consentimiento. Tu propia imagen, o la de alguien que consiente (declarado en la app), sí se permite (F-44b).

## Correspondencia con Suno y Sondo

| Suno / Sondo | Aquí |
|---|---|
| Create (custom / simple) | F-10 / F-16 |
| Instrumental | F-11 |
| Extend · Replace section · Cover | F-21 · F-22 · F-23 |
| Add vocals / Add instrumental | F-19 |
| Remaster | F-18 |
| Stems | F-30, F-31 |
| Personas | F-70, F-71 |
| Lyrics generator | F-17 |
| Workspaces / library | F-01…F-05, F-60 |
| Sondo · análisis de la canción y guion al beat | F-33, F-43 |
| Sondo · biblioteca de personajes | F-44, F-44b |
| Sondo · estilos visuales y prompt de escenas | F-42 |
| Sondo · editor de línea de tiempo, subtítulos | F-48 |
| Sondo · 16:9 / 9:16 / recortes cortos | F-49 |
| Sondo · vídeo con letra, visualizador | F-40, F-41 |
