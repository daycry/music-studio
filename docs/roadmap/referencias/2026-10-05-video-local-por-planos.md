---
documento: referencia-video-local-por-planos
fecha: 2026-10-05
tipo: material aportado por el propietario
uso: revisar al definir M4
validacion: propuestas del chat; no son requisitos aprobados ni benchmarks locales
---

# Referencia aportada: videoclip local por planos

El propietario pidió conservar este chat para revisarlo cuando llegue la generación de vídeo. Se recoge su contenido, tablas, ejemplos y propuesta de flujo, reorganizado en Markdown. Los rótulos «GitHub» recibidos no incluían URLs; los enlaces identificados y comprobaciones están en [video.md §9](../../arquitectura/video.md#9-aportación-del-propietario--investigación-para-m4-2026-10-05).

**Material de referencia, pendiente de revisión para M4.** Las estrellas y recomendaciones son opiniones del chat. El equipo real es una RTX 5070 de 12 GB, no la 5080 citada. Guardarlo no elige modelos, contratos, Redis, porcentajes, resoluciones ni presupuestos. No instala herramientas ni adelanta M4. El estado sigue en el ledger del hito correspondiente.

## Chat aportado: alternativas para vídeo musical

Para hacer videoclips musicales localmente, tipo Sondo.ai, el chat distingue dos cosas: generar clips visuales a partir de prompts/imágenes y hacer que esos clips respondan a una canción.

| Modelo | Local | Audio → vídeo | Personajes | Calidad | Hardware |
|---|---|---|---|---|---|
| Wan 2.2 S2V 14B | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Alto |
| Wan 2.2 Animate 14B | ✅ | indirecto | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Alto |
| LTX 2.5 Fast | ✅ | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ≥16 GB VRAM |
| Wan 2.2 TI2V 5B | ✅ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐½ | Medio |
| HunyuanVideo 1.5 | ✅ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐½ | ~14 GB+ optimizado |

### Wan 2.2 S2V

El chat propone Wan 2.2 S2V como opción especialmente interesante. S2V significa Speech-to-Video: usa audio para conducir movimiento y expresiones sincronizadas. Afirma que Wan2.2-S2V-14B tiene pesos e inferencia locales y salida 480p/720p.

```text
ACE-Step 1.5
     ↓
cancion.wav
     ↓
separación
 ┌──────────────┐
 voz.wav    instrumental.wav
     ↓
Wan 2.2 S2V
     ↓
cantante / personaje
sincronizado con audio
```

La propuesta no exige una persona real: generar primero una cantante virtual consistente, mantener su aspecto y hacer diferentes planos.

### LTX 2.5 y LTX Desktop

El chat señala una aplicación oficial de escritorio, LTX Desktop. Indica que LTX 2.5 Fast admite T2V, I2V y A2V localmente, con un mínimo de 16 GB de VRAM para Windows/Linux. Lo propone para canción → escenas → videoclip, y lo describe como rápido frente a otros modelos. Estas comparaciones requieren prueba del workflow exacto.

### Videoclip mediante planos

El chat recomienda construir el videoclip por planos en lugar de generar tres minutos de una vez. Ejemplo:

```text
Canción 3:32
 │
 ├── Intro       0:00 - 0:12
 │      └─ plano ciudad
 ├── Verse 1     0:12 - 0:42
 │      ├─ cantante
 │      ├─ travelling
 │      └─ detalle
 ├── Chorus      0:42 - 1:08
 │      ├─ cantante
 │      ├─ banda
 │      └─ plano cinematográfico
 ├── Verse 2
 │      └─ ...
 └── Outro
```

Clips de 5–10 segundos, ensamblados mediante FFmpeg siguiendo la canción. Si un plano sale mal, descartar o regenerar únicamente ese plano.

### Automatización propuesta: «Suno + Sondo» local

```text
              PROMPT
                 │
                 ▼
             LLM local
        ┌────────┴────────┐
        │                 │
      LETRA          STORYBOARD
        │                 │
        ▼                 │
   ACE-Step 1.5           │
        │                 │
        ▼                 │
    canción.wav           │
        │                 │
        ├──► Demucs       │
        │    stems        │
        │                 │
        ▼                 ▼
       análisis BPM / estructura
                 │
                 ▼
          Director Agent
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
 Wan 2.2 S2V          LTX 2.5
 cantante             escenas/B-roll
       │                   │
       └─────────┬─────────┘
                 ▼
              FFmpeg
                 │
                 ▼
        videoclip_final.mp4
```

El Director Agent leería `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, junto con BPM y duración, y propondría planos. Ejemplo del chat:

```text
00:00-00:06
Wide cinematic shot, woman walking alone
through Barcelona at night, neon reflections

00:06-00:12
Close-up of singer looking toward camera

00:12-00:18
Slow tracking shot, rain, cinematic lighting
```

Después se generaría cada clip. El chat propone ComfyUI + Wan + LTX para elegir capacidades según la escena:

- LTX → planos cinematográficos rápidos.
- Wan I2V → mantener consistencia del personaje.
- Wan S2V → cantante siguiendo la canción.
- Wan Animate → baile/movimiento corporal y transferencia desde referencia.
- FFmpeg → montaje, transiciones, sincronización y salida 4K.

Afirma que Wan ofrece T2V, I2V, TI2V, S2V y Animate. Para una RTX 5080, sugiere offloading/cuanti­zación en Wan y LTX nativo, señalando VRAM como limitación. Este ejemplo de hardware no corresponde al equipo del proyecto.

## Pregunta del propietario en el chat

> había pensado que como un videoclip de 4 minutos puede consumir mucho, hacerlo a trozos

## Chat aportado: producción incremental por planos

El chat recomienda planos de aproximadamente 4–8 segundos para cuatro minutos, y estima 30–50 generaciones. Propone reutilizar planos, cámara lenta, invertir algunos recursos, imágenes animadas y alternar cantante con B-roll. Los recuentos dependen de cuánto se reutilice y de la duración de cada posición; no son una garantía de coste.

### La canción completa como fuente de sincronización

```text
Canción 4:00
│
├── 00:00–00:08   INTRO
├── 00:08–00:14   plano 01
├── 00:14–00:20   plano 02
├── 00:20–00:26   cantante
├── 00:26–00:32   plano 04
│
├── ...
│
└── 03:54–04:00   OUTRO
```

### Ejemplo de plano independiente

```text
SHOT 17

Inicio:     01:34.200
Fin:        01:40.200
Duración:   6 s

Tipo:       Singer
Personaje:  singer_01
Referencia: singer.png

Prompt:
"Close-up of female singer performing emotionally,
dark cinematic stage, shallow depth of field,
slow camera movement"

Modelo:
Wan S2V

Audio:
song.wav [94.2 → 100.2]

Seed:
238474
```

Si el plano 17 sale mal, regenerar esos seis segundos.

### Mantener la misma cantante

Crear una Character Sheet con vista frontal, izquierda, derecha y cuerpo completo. Referencias sugeridas:

```text
characters/
└── singer_01/
    ├── face.png
    ├── front.png
    ├── profile.png
    ├── full_body.png
    ├── outfit_01.png
    └── outfit_02.png
```

Usar Image-to-Video, referencia de personaje o el mecanismo equivalente del modelo en cada plano, en vez de reinventar a la cantante desde texto. El chat presenta esto como una mejora de coherencia; habrá que comprobar identidad, ropa y continuidad.

### Sincronía labial solo en parte del videoclip

Alternar cantante, historia/B-roll y recursos:

```text
4 minutos
████████████████████████████████████████

Cantante / lip-sync
██████      ██████       ███████      ██

Historia / B-roll
      ██████      ███████       ██████

Paisajes / recursos
  ███        ████       ███
```

Proporciones orientativas del chat:

- 30–40 % cantante.
- 40–50 % narrativa/B-roll.
- 10–20 % recursos, transiciones y planos ambientales.

La finalidad es reducir las generaciones difíciles. No se fijan esos porcentajes para todas las canciones.

### División automática a partir de letra estructurada

El chat propone aprovechar `[Intro]`, `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Verse 2]`, `[Bridge]`, `[Final Chorus]`, `[Outro]`. Un LLM los transformaría en un esquema temporal. Ejemplo denominado `song.json` en el chat, no contrato de music-studio:

```json
{
  "duration": 241.3,
  "bpm": 118,
  "shots": [
    { "start": 0, "duration": 6, "type": "establishing" },
    { "start": 6, "duration": 6, "type": "singer" },
    { "start": 12, "duration": 5, "type": "story" }
  ]
}
```

De ahí se crearían todos los trabajos.

### Cola por plano y recuperación

```text
VIDEO PROJECT
Punto y seguido

✓ Shot 001     6 sec
✓ Shot 002     5 sec
✓ Shot 003     6 sec
⟳ Shot 004     generating...
○ Shot 005     pending
○ Shot 006     pending
...
○ Shot 038     pending
```

El chat propone apagar el PC y continuar después, saltando archivos ya existentes:

```text
shots 1-3 → existen → SKIP
shot 4     → existe → SKIP
shot 5     → generar
...

shot_017
⭐ approved
```

La idea es conservar planos aprobados sin regenerarlos. El criterio «archivo existe» debe revisarse: no prueba que haya terminado ni que corresponda a los parámetros actuales.

### Calidad progresiva

```text
DRAFT
480p · pocos steps · rápido

PREVIEW
720p · steps medios

FINAL
1080p · máxima calidad

MASTER
1080p generación → upscale → 4K
```

Primero generar el videoclip barato, verlo entero, regenerar los planos malos y después realizar render final, upscale, interpolación y montaje. El chat propone evitar cuarenta planos caros si se van a descartar quince. Las resoluciones dependen del workflow; reescalado no equivale a generación nativa.

### Aplicación tipo Sondo

Propuesta de interfaz: canción, personaje, estilo visual, resolución y botón «Generate Video»; cuadrícula de planos con estados pendiente/generando/completado; vista previa del plano seleccionado, prompt editable y acciones «Approve», «Regenerate», «Edit».

```text
AI MUSIC VIDEO
Song: punto_y_seguido.wav
Character: [ Singer 01 ▼ ]
Style: [ Cinematic ▼ ]
Resolution: [ Draft 480p ▼ ]
[ GENERATE VIDEO ]

🎬 01 ✓  🎬 02 ✓  🎬 03 ⟳  🎬 04 ○
🎬 05 ○  🎬 06 ○  🎬 07 ○  🎬 08 ○

Shot 03
[ VIDEO PREVIEW ]
Prompt: ...
[👍 Approve] [↻ Regenerate] [✏ Edit]
```

Backend propuesto por el chat: Python/FastAPI → ComfyUI API → Wan/LTX → FFmpeg, con Redis/una cola para que cada plano sea un job independiente.

El chat concluye que la GPU solo necesita generar un plano cada vez; el coste total de cómputo sigue existiendo, pero la recuperación y la memoria se vuelven más manejables. Sugiere clips base de 5–6 segundos.

## Observación del propietario al aportar el chat

> pero no se si se desvía del proyecto

## Revisión pendiente cuando toque M4

La [arquitectura de vídeo](../../arquitectura/video.md) ya contempla planos, personajes, ComfyUI headless, cola y montaje FFmpeg. Al definir M4, revisar este material junto con [datos](../../arquitectura/datos.md), [roadmap](../README.md) y [licencias](../../legal/licencias.md). Los tags no proporcionan timestamps: se requiere alineación con el audio maestro. Preservar mezcla continua, integridad/procedencia en la reanudación, aprobación por versión e invalidación cuando cambia el take. Medir canto/rap/dueto, identidad entre planos, memoria y tiempos con 12 GB de VRAM y la RAM de WSL vigente. No interpretar JSON, Redis, estrellas ni cifras del chat como decisiones aprobadas.
