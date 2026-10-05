---
documento: video
titulo: Vídeo musical — pipeline, niveles y modelos
estado: vigente — a validar con el spike de vídeo (M4)
fecha: 2026-09-28
actualizado: 2026-10-05
fuentes-consultadas: 2026-10-05 (nota §9; resto consultado 2026-09-28)
---

# Vídeo musical

Cada canción puede tener uno o varios **proyectos de vídeo**, al estilo de [Sondo](https://www.sondo.ai/). El sistema analiza la canción (beats, secciones, ambiente y letra), escribe un guion con **planos sincronizados al ritmo**, mantiene **personajes coherentes** entre escenas, genera los clips, permite montarlos en una **línea de tiempo** con la letra como subtítulos y exporta en **16:9 y 9:16**, con recortes para formatos cortos.

Marcas: **[V]** = verificado en fuente primaria (URL en §8) · **[NV]** = estimación o fuente secundaria · **[M4]** = se mide en el spike. Nada está medido todavía en la 5070.

## 1. La restricción real: tiempo de render en 12 GB

Un videoclip de 3 minutos tiene unos 36–45 planos de 4–5 s. Con repeticiones, hay que generar entre 1,5 y 2 veces esa cantidad.

| Enfoque | Tiempo estimado para 3 min en la 5070 [NV] |
|---|---|
| Visualizador o vídeo con letra (sin difusión) | **3–10 min** |
| Imágenes fijas coherentes + movimiento 2.5D + unos pocos planos generativos protagonistas | **≈ 1,5–3 h** |
| Todo generativo a 480p (Wan 14B + LoRA de 4 pasos) | **3–6 h** |
| Todo generativo a 720p | **10–20 h** (una noche o más) |

Por eso el vídeo se diseña **por niveles**. Siempre hay una vista previa inmediata, y lo caro se genera solo donde aporta, o en una cola nocturna. Sondo, que usa GPUs en la nube, tarda 10–18 min por vídeo según los usuarios [NV].

## 2. Niveles

| Nivel | Qué produce | Cómo | Tiempo |
|---|---|---|---|
| **N0 · Vídeo con letra / visualizador** | Tipografía cinética sincronizada palabra a palabra sobre fondo, portada o visualizador reactivo al audio (forma de onda, espectro, partículas) | Análisis + render propio: ffmpeg con subtítulos ASS con karaoke `\k` y filtros `showcqt`/`showwaves`, o shaders WebGL renderizados sin interfaz | Minutos |
| **N1 · Guion gráfico animado** | Una imagen clave por plano, con personajes coherentes, animada con Ken Burns, parallax 2.5D (mapa de profundidad) y cortes al beat | Modelo de imagen + edición con referencia + Depth Anything V2 Small + montaje propio | ≈ 20–45 min |
| **N2 · Planos protagonistas** | N1 + clips generativos en los estribillos y momentos clave, y planos del **cantante con sincronía labial** | Imagen→vídeo (Wan 2.2) desde la imagen clave del plano; cantante con InfiniteTalk sobre la **voz separada** | ≈ 1,5–3 h |
| **N3 · Todo generativo** | Todos los planos generados como clips de vídeo, con reescalado final opcional | Wan 2.2 en **cola nocturna** | 3–20 h |

Los niveles son **acumulativos por plano**: cada plano de la línea de tiempo tiene un tipo (`lyric`, `still`, `still_motion`, `i2v`, `singer`, `t2v`) y se puede subir o bajar de nivel individualmente. N0–N3 son solo ajustes predefinidos de ese reparto.

## 3. Pipeline

```
Take maestro (audio)
  │
  ├─ 1. Análisis ──────────── beats/downbeats y BPM (beat_this) · secciones (estructura de la
  │                           letra alineada + energía, librosa) · tiempos por palabra
  │                           (Qwen3-ForcedAligner con la letra conocida)
  ├─ 2. Guion (LLM local) ─── estilo visual + tratamiento → lista de planos:
  │                           [t0,t1] cortados al beat/downbeat · sección · fragmento de letra
  │                           · descripción · tipo de plano · personajes · cámara
  ├─ 3. Personajes ────────── desde FOTOS SUBIDAS (1–10) o desde una descripción: hoja de
  │                           personaje (Qwen-Image-Edit / FLUX.2 klein multi-referencia)
  │                           guardada en la biblioteca global; opcional LoRA (10–20 fotos)
  ├─ 4. Imágenes clave ────── una por plano, generada con referencia al personaje
  │                           (edición con referencia) → revisión y regeneración en la UI
  ├─ 5. Clips por plano ───── still_motion (2.5D) · i2v (Wan 2.2) · singer (InfiniteTalk)
  │                           · t2v; cada clip, un job de la cola con su manifiesto
  ├─ 6. Montaje ───────────── timeline.json: clips, transiciones al beat, subtítulos de letra,
  │                           título/créditos
  └─ 7. Render (server) ───── ffmpeg LGPL en el worker CPU: 16:9 · 9:16 (reencuadre por plano)
                              · clips cortos del estribillo · subtítulos quemados o .srt/.ass
```

- **El timeline es la fuente de verdad** y vive en la BD (`video_project.timeline` con `rev`; en disco solo una instantánea `timeline.json`, [datos.md](./datos.md) §1.3). Los clips son artefactos regenerables (`shot_version`), y cambiar un plano no obliga a regenerar el resto. Cada plano es **un job** con dependencias: imagen clave → clip → render ([ADR-0018](../decisiones/ADR-0018-cola-de-jobs.md)).
- **Coherencia**:
  - cada plano guarda su semilla, prompt, imagen clave y referencias;
  - «regenerar plano» respeta los planos vecinos;
  - el primer y el último fotograma pueden anclarse a los planos contiguos con FLF2V o VACE para suavizar las transiciones.
- **Protagonista desde fotos** (F-44b): las fotos subidas son la referencia de identidad. Con **edición multi-referencia** se generan las imágenes clave de cada plano manteniendo la cara y la ropa; a partir de ellas se animan los planos (I2V) y el cantante (InfiniteTalk usa la imagen clave como primer fotograma). Con pocas fotos la fidelidad es buena en planos medios y peor en planos lejanos o de perfil; un LoRA de personaje (entrenable en 12 GB) la mejora. **Una foto también puede usarse tal cual** como imagen clave, fondo o portada (F-44c). Sin declaración de derechos o consentimiento no se procesa una foto de una persona real.
- **Reencuadre 9:16**: se decide por plano (punto de interés marcado sobre la imagen clave), no recortando el centro a ciegas. Los planos generativos pueden generarse directamente en vertical si el vídeo se pide solo en 9:16.
- **Audio**: el vídeo siempre usa el **master** del take (no el MP3). Si el take maestro de la canción cambia, el vídeo se marca como **desfasado** y ofrece reanalizar y reajustar los tiempos.

## 4. Modelos (local por defecto, [ADR-0014](../decisiones/ADR-0014-local-por-defecto.md))

| Función | Por defecto | Licencia de los pesos | Notas |
|---|---|---|---|
| Beats y downbeats | **beat_this** | MIT (código y pesos) [V]; `.ckpt` convertido por el auditor | madmom descartado: sus modelos son CC BY-NC-SA [V] |
| Secciones | **Estructura de la letra** (`[verse]`/`[chorus]`…) alineada al audio con Qwen3-ForcedAligner; refinada con cambios de energía (librosa) | Apache 2.0 / ISC | allin1 (MIT) queda en laboratorio: exige Demucs (pesos solo investigación), madmom y NATTEN |
| Tiempos por palabra | **Qwen3-ForcedAligner-0.6B** sobre la voz (stem vocal o mezcla) con la letra conocida | Apache 2.0 [V] | Los pesos MMS_FA probablemente son NC [NV]: no usarlos |
| Guion | LLM local de [ADR-0012](../decisiones/ADR-0012-llm-de-letras.md) (Gemma 4 12B) | Apache 2.0 | Salida JSON validada contra el esquema de planos |
| Imágenes clave (texto→imagen) | **Z-Image-Turbo** (rápido) · **Qwen-Image-2512** (calidad) | Apache 2.0 [V] | FLUX.1/2-dev descartado: pesos no comerciales [V] |
| Personajes y edición con referencia | **Qwen-Image-Edit-2511** · **FLUX.2 [klein] 4B** (multi-referencia) | Apache 2.0 [V] | klein 4B ≈ 13 GB en BF16 → FP8/GGUF en 12 GB [NV]. LoRA de personaje entrenable en 12 GB con block swap [NV] |
| Profundidad (2.5D) | **Depth Anything V2 Small** | Apache 2.0 [V] | Base y Large son CC-BY-NC [V]: no usarlas |
| Imagen→vídeo / texto→vídeo, rápido | **Wan 2.2 TI2V-5B** (VAE y T5 en `.pth` → convertidos) | Apache 2.0 [V] | 1280×704 a 24 fps; cabe en 8 GB con offload [V]; destilado (FastWan) para velocidad [NV] |
| Imagen→vídeo, calidad | **Wan 2.2 A14B I2V** GGUF Q4–Q5 + LoRA Lightning de 4 pasos | Apache 2.0 [V] | ~6–8 GB a 480p con T5 en CPU [NV]; **exige RAM** (§5) |
| Transiciones entre planos | Wan 2.1 **FLF2V / VACE** | Apache 2.0 [V] | Primer y último fotograma, referencias |
| Cantante con sincronía labial | **InfiniteTalk** (sobre Wan 2.1) | Apache 2.0 [V] | Duración ilimitada, 480p/720p; lento en 12 GB [NV]. Retoque de labios sobre un clip existente: LatentSync 1.6 (OpenRAIL++) [V] |
| Baile al ritmo (futuro) | Wan-Dancer-14B | Apache 2.0 [V] | Sin integración ni cifras de VRAM todavía |
| Reescalado | Por decidir en el spike (Real-ESRGAN, SeedVR2…) | por verificar | Solo en N3 |

**Laboratorio** (evaluar y comparar, nunca por defecto):

- **LTX-2.5**: audio→vídeo nativo y tomas múltiples coherentes. Pero su licencia prohíbe «productos que compitan con Lightricks» sin una licencia aparte y obliga a indicar que el contenido es generado [V].
- **SkyReels V3** (R2V con 1–4 referencias; A2V con canto hasta 200 s): licencia Skywork con cláusula de registro para servicios online [V].
- **Kandinsky 5 Lite** (MIT, 2B): alternativa ligera.

**Descartados**:

- **HunyuanVideo 1.5 / HunyuanVideo-Avatar / HunyuanImage 3**: la licencia **excluye la UE** [V], y el proyecto está en España.
- **Sonic** (NC).
- **FramePack**: los pesos no tienen licencia declarada y probablemente heredan la de Hunyuan.
- **FLUX.1/2-dev, Kontext-dev y klein 9B**: pesos no comerciales.
- **Qwen-Image-2.1**: Research License.
- **CogVideoX y Hallo3**: licencia propia heredada.
- **Wan 2.5/2.6/3.0**: solo por API (§6).

## 5. Motor: ComfyUI como backend headless

Para imagen y vídeo se usa **ComfyUI dentro de un contenedor** (`engine-comfy`), controlado **solo por su API**. La UI de ComfyUI no la usa el usuario ([ADR-0016](../decisiones/ADR-0016-comfyui-como-motor-de-imagen-y-video.md)).

- **Motivo**: es donde de verdad se consigue que los modelos de 14B quepan en 12 GB: GGUF, block swap, FP8/NVFP4, offload asíncrono. Los nodos de Wan, InfiniteTalk y Qwen-Image llegan antes allí que a diffusers.
- **Envoltorio `/v1`**: el engine-comfy implementa el mismo contrato que los demás. Cada tipo de plano es un **workflow JSON versionado** en `apps/engines/comfy/workflows/`, con parámetros inyectados. Los nodos personalizados van **fijados por commit** en el Dockerfile.
- **Todo dentro de la carpeta**: `models/comfy/` es el directorio de modelos de ComfyUI (checkpoints, loras, vae, clip, gguf), montado en el contenedor. La salida va a `data/tmp/<job>/`.
- **Particularidades en la 5070**:
  - usar PyTorch **cu130**; FP8/NVFP4 solo si el spike de M4 los valida ([ADR-0007](../decisiones/ADR-0007-gpu-local-12gb.md), [ADR-0016](../decisiones/ADR-0016-comfyui-como-motor-de-imagen-y-video.md)) — NVFP4 solo rinde con cu130 [V];
  - SageAttention 2.2 por nodo (Patch Sage), no global, porque puede dar salida negra en Wan/Qwen [NV];
  - en WSL2/Docker, `--disable-pinned-memory` para evitar cuelgues por falta de memoria [V];
  - vigilar que ComfyUI no fije el modelo entero en «memoria de GPU compartida» [V].
- **RAM**: la máquina tiene **32 GB**. Los modelos de 14B con offload y el codificador de texto en la CPU van justos. Hace falta subir `memory=` y `swap=` en `.wslconfig`, y **se recomiendan 64 GB** si N2/N3 se usan a menudo [NV]. El spike de M4 medirá si con 32 GB basta usando Q4 y el 5B.
- **Licencia de ComfyUI: GPL-3.0.** Se ejecuta como proceso aparte vía API y no se distribuye: sin problema en uso personal. Antes de comercializar hay que revisarlo ([`../legal/comercializacion.md`](../legal/comercializacion.md)). Si hiciera falta, la salida es reimplementar los workflows usados con diffusers.

## 6. Alternativas externas (opcionales, desactivadas de fábrica)

Para planos que la 5070 no puede generar con la calidad o el tiempo deseados. Un adapter por proveedor, con el mismo tipo de plano, el coste visible antes de lanzar y el proveedor anotado en el manifiesto del plano. Candidatos a evaluar cuando se implemente: la API oficial de Wan 2.5+/3.0 y otros proveedores de vídeo generativo. Sus términos de uso se registran en `licencias.md` antes de activarlos.

## 7. Datos

Ver [`datos.md`](./datos.md) §4: `video_project` (formato, estilo visual, tratamiento, nivel, estado, take usado), `shot` (tiempo, sección, letra, tipo, prompt, personajes, imagen clave, clip, semilla, estado) y `render`.

## 8. Fuentes

- Wan: https://huggingface.co/api/models?author=Wan-AI · https://github.com/Wan-Video/Wan2.2 · https://docs.comfy.org/tutorials/video/wan/wan2_2 · https://huggingface.co/Wan-AI/Wan2.2-S2V-14B · https://huggingface.co/Wan-AI/Wan-Dancer-14B
- InfiniteTalk: https://huggingface.co/api/models/MeiGen-AI/InfiniteTalk
- LTX-2.5: https://huggingface.co/Lightricks/LTX-2.5 · https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x
- HunyuanVideo 1.5 (exclusión UE): https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
- SkyReels V3: https://github.com/SkyworkAI/SkyReels-V3/blob/main/LICENSE.txt · Kandinsky 5: https://huggingface.co/api/models/kandinskylab/Kandinsky-5.0-I2V-Lite-5s
- Imagen: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B · https://huggingface.co/black-forest-labs/FLUX.2-dev · https://huggingface.co/api/models?author=Qwen&search=Image · https://huggingface.co/api/models?author=Tongyi-MAI · https://huggingface.co/Qwen/Qwen-Image-2.1
- Profundidad: https://huggingface.co/api/models?author=depth-anything
- Análisis: https://github.com/CPJKU/beat_this · https://github.com/CPJKU/madmom · https://github.com/mir-aidj/all-in-one · https://github.com/m-bain/whisperX
- Render: https://ffmpeg.org/ffmpeg-filters.html · Remotion (no se usa por defecto): https://github.com/remotion-dev/remotion/blob/main/LICENSE.md
- Blackwell/ComfyUI: https://github.com/thu-ml/SageAttention · https://blog.comfy.org/p/new-comfyui-optimizations-for-nvidia · https://github.com/Comfy-Org/ComfyUI/issues/11531 · https://github.com/Comfy-Org/ComfyUI/issues/15679 · https://github.com/deepbeepmeep/Wan2GP
- Sondo (referencia de producto): https://www.sondo.ai/ · https://www.sondo.ai/mv-creation

## 9. Aportación del propietario — investigación para M4 (2026-10-05)

El [chat aportado y conservado para M4](../roadmap/referencias/2026-10-05-video-local-por-planos.md) encaja con los niveles y el pipeline anteriores: clips independientes, personaje de referencia, aprobación por plano, borrador antes del render final y recuperación tras una interrupción. Son ideas para contrastar al especificar M4, sin sustituir la arquitectura vigente ni incorporar modelos ahora. ComfyUI sigue detrás de `/v1`; el server conserva BD, cola y montaje FFmpeg. No se añade Redis ni un motor nuevo por esta nota.

Para cuatro minutos, planos de 5–6 s implican aproximadamente 40–48 posiciones en el montaje. Las posiciones no equivalen a generaciones únicas: pueden contener imágenes animadas o recursos reutilizados. Los tiempos se obtienen del audio maestro y de la letra alineada; los tags marcan intención/secciones, pero no son timestamps. La mezcla completa permanece como banda sonora continua. Un clip de cantante utiliza el fragmento vocal correspondiente, sin reemplazar el audio final por el generado por el modelo de vídeo.

Al reanudar, la existencia de un archivo no basta para saltar un trabajo: habrá que comprobar resultado terminal, integridad, procedencia y referencias vigentes. Una aprobación se vincula a una versión del plano. Un cambio de audio, prompt, referencia o workflow requiere resolver la invalidación de dependencias. Son criterios propuestos para la spec de M4, compatibles con `shot_version`, linaje y `timeline.rev` existentes.

| Fuente primaria revisada | Qué permite concluir | Consecuencia para la 5070 de 12 GB |
|---|---|---|
| [ComfyUI: Wan 2.2](https://docs.comfy.org/tutorials/video/wan/wan2_2) | El workflow TI2V-5B declara funcionamiento con 8 GB mediante offload nativo | Candidato inicial del spike; consumo, RAM, duración y calidad locales pendientes |
| [Wan 2.2 oficial](https://github.com/Wan-Video/Wan2.2) | S2V-14B usa imagen, audio y prompt; su receta de referencia declara al menos 80 GB | Esa receta no es viable directamente aquí. Cualquier variante optimizada necesita evaluación propia, incluyendo canto y dueto |
| [LTX Desktop oficial](https://github.com/Lightricks/LTX-Desktop) | LTX 2.5 Fast ofrece T2V/I2V/A2V local; Windows/Linux requieren al menos 16 GB de VRAM | Desktop deja esta GPU en modo API. No prueba que otra ruta ComfyUI cuantizada sea imposible, ni acredita que funcione aquí |

Dividir reduce el coste de regenerar y la memoria de activaciones frente a clips largos, pero no reduce el tamaño de los pesos. El presupuesto real incluye los 16 GB de RAM asignados actualmente a WSL, no los 32 GB totales del host. No se cambian esos límites automáticamente ni se prometen tiempos a partir del chat.

La [licencia vigente LTX-2.x](https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE-2_x), aplicable a versiones LTX-2.5 desde el 11 de agosto de 2026, conserva condiciones de ingresos, transparencia y competencia (Attachment A, punto 20); sigue como candidato de laboratorio. HunyuanVideo 1.5 mantiene la exclusión territorial de la UE en su [licencia oficial](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE), por lo que el chat no cambia su descarte para este proyecto. No se incorporan pesos ni herramientas sin revisar su versión exacta y registrar licencia/lock.

Draft/preview/final son calidades por plano, distintas de N0–N3, que indican cómo se construye el vídeo. No se fuerza una progresión universal 480p→720p→1080p: depende del workflow validado. Reescalar a 4K no convierte el origen en generación 4K nativa. La proporción de cantante, narrativa y recursos se decidirá por canción; los porcentajes del chat son ejemplos.

Prioridad actual: terminar la auditoría de fidelidad musical T-17 y corregir preparación/metadata antes de cambiar modelos. El vídeo sigue en M3/M4; no se inicia M4 ni se abre un ledger paralelo.
