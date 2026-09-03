---
documento: spike-comparativa-modelos
titulo: "T-06 — Spike comparativo de modelos: ACE-Step 1.5, HeartMuLa y YuE 7B (+ MiniMax-Music3 condicional)"
iniciativa: "Plataforma propia de generación musical por IA (proyecto personal)"
slug: plataforma-musical-ia
tarea: T-06
estado: completado
fecha: 2026-09-02
autor: implementer
decision-que-confirma: D-06
spec: ../spec.md
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
gate-g1: ../gates/g1-protocolo.md
gate-g2: ../gates/g2-matriz-resultados.md
fuentes-consultadas: "2026-09-02; addendum §12 reverificado el 2026-09-03"
mediciones-propias: 2026-09-01 (T-03 / T-05)
actualizado: 2026-09-03
addendum: "§12 — reevaluación de MiniMax-Music3 (la condición «hasta G2» quedó huérfana, no resuelta)"
gate-comercializacion: ../gates/gobernanza.md
---

# T-06 · Spike comparativo de modelos

> **Qué es este documento.** La comparación estructurada que pide `tasks.md` T-06 entre **ACE-Step 1.5**, **HeartMuLa** y **YuE 7B** contra licencia, VRAM mínima y de confort, arquitectura y capacidades declaradas; más **MiniMax-Music3** como candidato condicional (`spec.md` §5.3 y §11.1). Cierra con la **confirmación explícita de D-06**.
>
> **Qué NO es.** No es una comparación de calidad musical. La calidad se decide por escucha humana en G1 (`gates/g1-protocolo.md`), no aquí, y de los tres modelos **solo uno se ha ejecutado**.

## 0. Método y regla de honestidad

Tres niveles de evidencia, marcados en todo el documento:

| Marca | Significado |
|---|---|
| **[M]** | **Medido por nosotros** en esta máquina, con el número y la fecha. Es la evidencia más fuerte y solo existe para ACE-Step 1.5. |
| **[D]** | **Declarado por upstream** (model card, README, licencia, paper). Verificado contra la fuente primaria el 2026-09-02, no comprobado en ejecución. |
| **[C]** | **Cálculo propio** a partir de datos [D] (por ejemplo, pasar de tamaño de fichero en F32 a huella estimada en fp16). Aritmética, no medición. |

Nada de este documento etiquetado **[D]** o **[C]** vale como resultado de spike: los spikes ejecutables son T-03, T-05, T-07 y T-09. Lo que sí hace este documento es **evitar gastar horas de contenerización en un modelo que ya se sabe que no cabe**.

Un aviso que conviene tener por escrito: **el desequilibrio de evidencia es enorme y no se compensa leyendo más READMEs**. De ACE-Step 1.5 tenemos artefacto construido, hashes, tiempos, picos de VRAM y dos WAV en disco. De HeartMuLa y de YuE tenemos lo que sus autores dicen de sí mismos. Cualquier conclusión que compare «calidad» entre ellos sería inventada; las conclusiones de aquí son sobre **licencia, tamaño, arquitectura y encaje con el hardware**, que sí se pueden establecer documentalmente.

---

## 1. Resultado en una página

1. **D-06 se confirma sin cambios de orden.** ACE-Step 1.5 es el modelo de G1; HeartMuLa es el segundo adapter; YuE 7B sigue siendo candidato condicional de Fase 2. Fundamento en §7.
2. **Corrección de licencia (afecta a la trazabilidad, §5).** **ACE-Step 1.5 es MIT, no Apache 2.0.** Apache 2.0 es la licencia de **ACE-Step v1 3.5B**, que es otro modelo. `spec.md` §11.1 arrastra el dato mal y hay que corregirlo.
3. **La ficha de ACE-Step 1.5 en `spec.md` §11.1 describe, en realidad, a ACE-Step v1** (3,5B, Apache 2.0). El modelo que hemos construido y ejecutado es **un DiT de 2B + Qwen3-Embedding-0.6B + decoder VAE = 3.074.063.112 parámetros** **[M]**, con una tabla de VRAM upstream de seis tramos, no de dos cifras. §5 lista las seis correcciones.
4. **HeartMuLa no cabe en la GPU local.** Sus pesos son **15,8 GB en F32** (LM) más un codec de **2B en F32** que upstream **desaconseja** bajar a bf16 por pérdida de calidad **[D]**. En fp16 el LM solo ya son ~7,9 GB **[C]**, y en esta máquina hay **7.202 MiB libres** **[M]**. Consecuencia real: **T-29 y T-34 (G1-bis) no son ejecutables en local**; o RunPod, o cuantización que upstream no ofrece. Esto **no cambia el orden de D-06**, cambia el supuesto de coste de esas dos tareas. §8.
5. **Hallazgo que toca el protocolo de G1: HeartCLAP no está publicado.** La organización `HeartMuLa` en Hugging Face tiene **seis repos y ninguno es HeartCLAP** **[D]**; el propio equipo de open source de Hugging Face lo pidió por escrito en el issue #4 de `heartlib`. `gates/g1-protocolo.md` §6.1 lo nombra **candidato principal** para medir CLAP. Hay que elegir suplente antes de T-09. §9, acción A-3.
6. **Aviso para T-07: nuestro checkpoint es el que menos capacidades de edición declara.** `acestep-v15-turbo` declara Repaint y Cover pero **no** Extract / Lego / Complete; esas tres son exclusivas de los checkpoints `base` (50 pasos + CFG) **[D]**. Probar `CONTINUATION` sobre turbo y concluir «ACE-Step no lo soporta» sería un falso negativo del modelo. §4.3.
7. **MiniMax-Music3 sigue siendo candidato condicional, no alcance.** Su licencia comunitaria (atribución en UI, umbral de 20 M$, AUP y salvaguardas obligatorias) está verificada contra el fichero `LICENSE` y confirmada palabra por palabra: §6. **(Reevaluado el 2026-09-03 — ver §12: la condición «bloqueado hasta G2» estaba rota, porque MiniMax nunca entró en G2.)**

---

## 2. Tabla comparativa maestra

Los tres modelos de D-06, más el condicional. **VRAM «mínima»** = el suelo que el proyecto acepta (con offloading, degradado); **VRAM «de confort»** = configuración de trabajo sin penalización.

| | **ACE-Step 1.5** | **HeartMuLa (oss-3B)** | **YuE 7B** | **MiniMax-Music3** *(condicional)* |
|---|---|---|---|---|
| **Papel en D-06** | **Modelo de G1** — el único ejecutado | **Segundo adapter** (T-29, G1-bis en T-34) | Tercer adapter **condicional**, F2 | Candidato condicional adicional (§5.3) |
| **Licencia del código** | **MIT** **[D]** | Apache 2.0 **[D]** | Apache 2.0 **[D]** | MiniMax-Music3 **Community License** **[D]** |
| **Licencia de los pesos** | **MIT** (tag `license: mit`; el repo HF **no publica fichero `LICENSE`**) **[D]** + copia local verificada **[M]** | Apache 2.0, explícito: el equipo actualizó la licencia del repo **y de todos los pesos** a Apache 2.0 **[D]** | Apache 2.0: «The YuE model (including its weights) is now released under the Apache License, Version 2.0» **[D]** | Misma Community License; componentes upstream con licencia propia (Qwen3-8B Apache 2.0, DiT-2B de Stable Audio tools MIT, VAE de DAC MIT) **[D]** |
| **¿Uso comercial?** | Sí, sin condiciones de licencia. Además declara entrenamiento sobre catálogo licenciado / royalty-free / sintético **[D]** — declaración del proveedor, **no verificable por nosotros** | Sí, sin condiciones de licencia | Sí. Los autores **piden** (no exigen) crédito «YuE by HKUST/M-A-P» y etiquetado «AI-generated» **[D]** | Sí, **con obligaciones**: atribución en UI, autorización previa por escrito por encima de 20 M$/año, AUP y salvaguardas técnicas **[D]** |
| **VRAM mínima** | **≤ 6 GB**: DiT 2B turbo solo, INT8 + offload total. **6–8 GB**: turbo + LM 0.6B, backend `pt` **[D]**. **Medido aquí: pico 7.455 MiB de 8.191** con DiT turbo + Qwen3-Embedding-0.6B, fp16, sin LM planner **[M]** | Upstream **no publica cifra**. Solo dice: reparte LM y codec en dos GPU (ej. 2×4090) o usa `--lazy_load` **[D]**. Sitio del operador (no upstream): 16 GB mín. / 24 GB+ recomendado **[D]** | **≤ 24 GB → máximo 2 sesiones** (≈1 estrofa + 1 estribillo). FlashAttention 2 «is mandatory» para ahorrar memoria **[D]** | **8 GB** con `apply_group_offloading` (`leaf_level`, `use_stream=True`) sobre el LM: «slower, but fits in 8 GB» **[D]** |
| **VRAM de confort** | **≥ 24 GB**: DiT XL sft + LM planner 4B, backend `vllm`, sin offload **[D]** | 24 GB+ (LM bf16 ~7,9 GB **[C]** + codec F32 ~8 GB **[C]** + activaciones) | **≥ 80 GB** para canción completa (4+ sesiones): «H800, A100, or multiple RTX4090s with tensor parallel» **[D]** | 24 GB sin offload; ~22 GB con offload automático de CPU **[D]** |
| **Arquitectura** | Híbrida **LM planner + DiT de difusión**, desacopladas. DiT destilado a **8 pasos sin CFG** (turbo). El LM planner es opcional | **LM de música autorregresivo** condicionado a letra + tags, sobre tokens de **HeartCodec a 12,5 Hz** | **Dos etapas**: LM de 7B (LLaMA) sobre codebook-0 de `xcodec` + LM de 1B para codebooks residuales + **upsampler Vocos 16 kHz → 44,1 kHz** | **Jerárquica**: LLM global 8B (desde Qwen3-8B) + LLM local 0,6B + Flow Matching 2,4B + Flow-VAE decoder 123M |
| **Parámetros** | **3.074.063.112 en nuestro artefacto** (DiT 2,394 G + text encoder 0,596 G + VAE decoder 0,084 G), todo FP16 **[M]**. Upstream: DiT 2B (~4,7 GB) o XL 4B (~9 GB bf16); LM planner 0,6B / 1,7B / 4B **[D]** | HF declara **4B params, F32**, pese al «3B» del nombre; 15,8 GB en 4 shards **[D]** | s1: 7B en el nombre, **6B en los metadatos de HF**, BF16; s2: 1B; + upsampler **[D]** | Suma de componentes ≈ 11,1B; los metadatos de HF dicen «2B params», **contradicción no resuelta en la ficha** **[D]** |
| **Idiomas declarados** | **50+**, con adherencia de prompt declarada en todos **[D]** | **5**, enumerados en el *frontmatter*: `zh`, `en`, `ja`, `ko`, **`es`** **[D]** | en, zh (mandarín + cantonés), ja, ko, «including but not limited to». **Checkpoints *annealed* solo en `en`, `zh`, `jp-kr`** **[D]** | **No enumerados en ninguna parte de la ficha** **[D]** |
| **Duración** | 10 s – 600 s (10 min) **[D]**. **Techo medido aquí: 420 s pasa, 480 s revienta** **[M]** | `--max_audio_length_ms` por defecto **240000** (4 min); no se documenta techo duro **[D]** | Sin techo publicado; se genera por secciones de ~30 s (`--max_new_tokens 3000`), y el límite práctico es la VRAM **[D]** | 5 min (ficha) / 9.000 frames acústicos a 25 fps ≈ 6 min. **La propia ficha se contradice** **[D]** |
| **Salida** | **48.000 Hz · 2 canales · PCM 16 bit**, verificado en los dos WAV entregados **[M]**. Upstream no publica sample rate | `.mp3`; sample rate **no publicado** **[D]** | 44,1 kHz tras el upsampler; el codec es 16 kHz mono. Entrega además **stems** de voz y acompañamiento **[D]** | 32 kHz · 16 bit · WAV estéreo **[D]** |
| **Velocidad** | **[M] 30 s de audio → 7,38 s. 180 s → 42,97 s** en GTX 1070 (Pascal, sin tensor cores). Upstream declara <2 s en A100 y <10 s en RTX 3090 **[D]** | **RTF ≈ 1,0** (~tiempo real), GPU no identificada **[D]** | **30 s de audio → 150 s en H800; ~360 s en RTX 4090** **[D]** | La ficha no da tiempos propios reproducibles |
| **Formato de pesos** | `safetensors` **[M]** (artefacto propio, 1.169 tensores F16 + 7 U8 + 1 F32) | `safetensors`, 4 shards **[D]** | `safetensors` **[D]** | `safetensors` **[D]** |
| **Pila de inferencia** | `transformers` + código vendorizado; sin `diffusers` en nuestra imagen **[M]** | `heartlib` (repo propio), Python 3.10, CUDA obligatorio **[D]** | Repo propio + `xcodec_mini_infer` clonado aparte + FlashAttention 2 **[D]** | `diffusers` (PR #14456, commit fijado), SGLang-Omni, ComfyUI. CUDA obligatorio, solo no-streaming **[D]** |

---

## 3. Contraste contra lo único que hemos medido

Todo lo de esta sección es **[M]**, del 2026-09-01 (T-03 / T-05), sobre `NVIDIA GeForce GTX 1070` (Pascal `sm_61`, 8.191 MiB totales, **7.202 MiB libres**) y la imagen `ace-step-runner:t05` (torch 2.13.0+cu126, transformers 5.16.1).

### 3.1 Qué contiene realmente nuestro artefacto

Cabecera de `D:\srv\ace-step\weights\ace_step_1_5.safetensors` (6.163.551.450 B, sha256 `3faa5ac9…12d947`), leída y agregada por prefijo:

| Prefijo | Tensores | Parámetros | Qué es |
|---|---:|---:|---|
| `dit.decoder.*` | 476 | 1.575.458.880 | Bloques de difusión (decoder) |
| `dit.encoder.*` | 140 | 608.367.616 | Condicionamiento |
| `dit.tokenizer.*` | 32 | 105.032.198 | Tokenizador **de audio** (FSQ), no de texto |
| `dit.detokenizer.*` | 28 | 105.011.776 | |
| `dit.null_condition_emb` | 1 | 2.048 | Embedding nulo (CFG) |
| **`dit.*` (total)** | **677** | **2.393.872.518** | **= la serie «2B» de upstream** |
| `text_encoder.*` | 310 | 595.776.512 | **Qwen3-Embedding-0.6B** |
| `vae.decoder.*` | 182 | 84.414.082 | OobleckDecoder (**sin encoder**: no hace falta para text2music) |
| `aux.*` | 8 | 12.401.666 | Configs, `tokenizer.json`, latente de silencio F32 `[1,64,15000]`, manifiesto |
| **Total (sin `aux`)** | **1.169** | **3.074.063.112** | Todo **FP16** |

**Comprobación cruzada que cierra la identificación del checkpoint:** upstream declara «~4.7GB for 2B» de pesos. Nuestro `dit.*` son 2.393.872.518 parámetros × 2 B = **4,788 GB**. Coincide. El artefacto es **`acestep-v15-turbo`**, la variante 2B de 8 pasos sin CFG, y **no** lleva LM planner (`acestep-5Hz-lm-*`): lo que llamamos `text_encoder` es el **Qwen3-Embedding-0.6B**, que es otra cosa.

### 3.2 Dónde nos sitúa eso en la tabla de VRAM de upstream

| Tramo upstream | DiT recomendado | LM planner | Backend / notas |
|---|---|---|---|
| ≤ 6 GB | 2B turbo | ninguno (solo DiT) | INT8 + offload total de CPU |
| **6–8 GB ← estamos aquí** | **2B turbo** | `acestep-5Hz-lm-0.6B` | `pt` |
| 8–16 GB | 2B turbo/sft | 0.6B / 1.7B | `vllm` |
| 16–20 GB | 2B sft o XL turbo | 1.7B | `vllm`; XL exige offload por debajo de 20 GB |
| 20–24 GB | XL turbo/sft | 1.7B | `vllm`; XL cabe sin offload |
| ≥ 24 GB | XL sft (o `xl-base` para extract/lego/complete) | 4B | `vllm`; todo cabe sin offload |

Estamos en el tramo **6–8 GB**, y además **sin el LM planner de 0.6B** que ese tramo contempla. Es decir: corremos una configuración **más ligera** que la recomendada para nuestra tarjeta, en fp16 sin cuantizar, y aun así el pico visible por el driver es **7.455 MiB de 8.191** — quedan **737 MiB**. Añadir el planner 0.6B (≈1,2 GB en fp16 **[C]**) **no cabe** sin offload. La ficha de `spec.md` §11.1, que resume esto como «8 GB suelo / 24 GB confort», no es falsa, pero es demasiado gruesa para planificar: el suelo real depende de **qué combinación** de DiT + LM se cargue.

### 3.3 Lo que solo se sabe por haberlo ejecutado

Cuatro cosas que **no** están en ningún README y que condicionan cualquier comparación con los otros dos modelos en esta máquina:

| Hallazgo **[M]** | Por qué importa para T-06 |
|---|---|
| **SDPA en `sm_61` cae al kernel *mem-efficient* y es 12,9× más lento que eager** (282,20 ms frente a 21,87 ms a `[1,16,2250,128]`), **en silencio**. Hay que forzar `_attn_implementation = "eager"` a mano | Cualquier modelo que asuma atención acelerada en esta tarjeta **rinde ~10× peor de lo que su README sugiere**. Aplica a HeartMuLa y, de forma terminal, a YuE (§8.2) |
| **fp16 no cae por el camino lento de Pascal**: cuBLAS promociona a FP32, ratio fp16/fp32 = 0,80–1,11 | Descarta el miedo de que Pascal obligue a fp32. Los cálculos [C] de huella en fp16 de este documento son legítimos como suelo |
| **El pico de VRAM lo pone el condicionamiento, no la difusión**, y **no crece con la duración**: 7.455 MiB tanto a 30 s como a 180 s | Los presupuestos de VRAM por duración son engañosos. Lo que empuja el pico es el tamaño del bloque de condicionamiento (letra + prompt), no los minutos |
| **El decode monolítico del VAE no cabe por encima de ~40–46 s: hay que trocearlo** | Es una restricción de *nuestro* pipeline, no del modelo, y hay que replicarla en cualquier adapter futuro que decodifique en un solo tensor |

---

## 4. Ficha ampliada — ACE-Step 1.5 (modelo de G1)

### 4.1 Licencia

- **MIT**, para código y pesos. `github.com/ace-step/ACE-Step-1.5`: sidebar «MIT license» y README «This project is licensed under [MIT]» **[D]**.
- **El repo de Hugging Face `ACE-Step/Ace-Step1.5` no publica fichero `LICENSE`** (HTTP 404); solo el tag de metadatos `license: mit` **[D]**. Por eso la evidencia se recuperó de GitHub y se archivó en local: `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt`, 1.064 B, sha256 `05a6bce42a62636d2cfb24139cc008b6b899754e244175814bb5dd2f4a485357`, cabecera «MIT License / Copyright (c) 2026 ACEStep» **[M]**.
- **Qwen3-Embedding-0.6B**, que viaja dentro de nuestro artefacto, es **Apache 2.0**, archivada en `D:\srv\ace-step\provenance\LICENSE.qwen3-embedding.apache-2.0.txt` **[M]**.
- Declaración de procedencia del entrenamiento (licenciado + royalty-free/dominio público + sintético MIDI-to-audio) y afirmación de que la salida es usable comercialmente **[D]**. **Es una declaración del proveedor.** No la hemos verificado ni podemos; `spec.md` §11.4 ya dice que el self-hosting no limpia la procedencia, y esta declaración **no cambia** la matriz de G2.

### 4.2 Arquitectura

«Decoupled Usability-Generation Architecture»: un **LM que planifica** (convierte la consulta del usuario en un plano de canción: metadatos, letra, captions vía Chain-of-Thought) y un **DiT que renderiza**. La destilación comprime la trayectoria de inferencia del DiT de 50 pasos a **4–8**, que es lo que hace viable la generación en hardware de consumo **[D]**.

Del `config.json` vendorizado (`apps/runner/adapters/ace_step/vendor/config.json`, sha256 `74745ff7…`) se lee la estructura real del DiT turbo **[M]**: `hidden_size` 2048 · `num_hidden_layers` 24 · `num_attention_heads` 16 con `head_dim` 128 · `num_key_value_heads` 8 (GQA) · `intermediate_size` 6144 · `max_position_embeddings` 32768 · atención deslizante con `sliding_window` 128 · cuantización FSQ con `fsq_input_levels [8,8,8,5,5,5]` · `is_turbo: true`, `model_version: "turbo"`.

Y tres campos que son **evidencia estructural directa** para T-07, porque describen encoders dedicados:

- `num_lyric_encoder_hidden_layers: 8` → **encoder de letra** propio.
- `num_timbre_encoder_hidden_layers: 4`, `timbre_hidden_dim: 64`, `timbre_fix_frame: 750` → **encoder de timbre** propio, que es el sustrato plausible de `VOICE_CONDITIONING`.
- `audio_acoustic_hidden_dim: 64`, coherente con `aux.silence_latent` de forma `[1, 64, 15000]` **[M]**.

### 4.3 Capacidades declaradas por checkpoint — aviso para T-07

Matriz del README de upstream **[D]**:

| Checkpoint | Pasos | CFG | Refer audio | Text2Music | Cover | Repaint | Extract | Lego | Complete |
|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `acestep-v15-base` | 50 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `acestep-v15-sft` | 50 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **`acestep-v15-turbo` ← el nuestro** | **8** | **❌** | ✅ | ✅ | ✅ | ✅ | **❌** | **❌** | **❌** |
| `acestep-v15-xl-base` | 50 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `acestep-v15-xl-sft` | 50 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `acestep-v15-xl-turbo` | 8 | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

Traducido al enum que T-07 va a sondear:

| Capacidad de T-07 | Equivalente upstream | ¿En nuestro turbo? |
|---|---|---|
| `SECTION_INPAINT` | Repaint | **Sí** **[D]** |
| `AUDIO_TO_AUDIO` | Cover / Refer audio | **Sí** **[D]** |
| `VOICE_CONDITIONING` | Refer audio + encoder de timbre | **Plausible** — hay estructura en el config **[M]**, pero no es una capacidad nombrada en la matriz. Sondear |
| `CONTINUATION` | Complete | **No en turbo** — solo en `base` / `xl-base` **[D]** |

> **Riesgo concreto de T-07.** Si se sondea `CONTINUATION` sobre `turbo` y sale que no, el resultado correcto es «**el checkpoint que hemos empaquetado** no lo soporta», no «ACE-Step 1.5 no lo soporta». Para el segundo enunciado haría falta `acestep-v15-base` — 50 pasos y CFG, es decir, **entre 6 y 12 veces más cómputo por pista** que los 8 pasos sin CFG de turbo, sobre una GTX 1070 donde 180 s ya cuestan 22,6 s solo de difusión **[M]**. Recomendación: **T-07 declara `CONTINUATION` como no soportada *por la configuración de Fase 1*, con la nota de que es una propiedad del checkpoint y no del modelo**, y no se abre spike de `base` en Fase 0.

### 4.4 Riesgos abiertos

- El arranque en frío medido está dominado por la carga de pesos (**386–390 s**, tensor a tensor sobre bind mount de Windows) y deja el total en **6,6 min**, por encima del rango 2–6 min de S-01 **[M]**. Es un defecto de nuestro `adapter.py`, no del modelo, y ya está localizado (lectura contigua + una copia H2D → ~27 s).
- La pista de 180 s **sale de escala antes del recorte (pico 1,280)** **[M]**: la normalización EBU R128 de T-19/T-45 no es cosmética.
- **Sample rate no documentado por upstream**; nosotros medimos **48 kHz** en la salida real **[M]**. Nuestro dato es más fuerte que el suyo, pero conviene no propagarlo como propiedad del modelo sin decir que es medido en nuestra configuración.

---

## 5. Correcciones que `spec.md` §11.1 debe absorber

La ficha actual de ACE-Step en §11.1 describe, campo por campo, a **ACE-Step v1 3.5B**, no a ACE-Step 1.5. Seis correcciones:

| # | Dice hoy `spec.md` §11.1 | Verdad verificada | Evidencia |
|---|---|---|---|
| **1** | ACE-Step 1.5 — Licencia **Apache 2.0** | **MIT.** Apache 2.0 es de **ACE-Step v1 3.5B** (`ACE-Step/ACE-Step-v1-3.5B`, tag `license: apache-2.0`; `github.com/ace-step/ACE-Step`, «This project is licensed under [Apache License 2.0]») | **[D]** ambos repos + **[M]** copia local `LICENSE.acestep.mit.txt` |
| **2** | ACE-Step 1.5 — **3,5B** params | 3,5B es **v1**. En 1.5 la serie base es **DiT 2B** (~4,7 GB) y la XL **DiT 4B** (~9 GB bf16), con LM planner **opcional** de 0,6B / 1,7B / 4B aparte. Nuestro bundle ejecutable son **3.074.063.112** parámetros | **[D]** + **[M]** |
| **3** | «8 GB suelo / 24 GB confort», dos cifras | Upstream publica **seis tramos** (§3.2). El suelo depende de la combinación DiT+LM, no del modelo. Medido aquí: **7.455 MiB de pico** con turbo 2B + Qwen3-Embedding-0.6B sin planner | **[D]** + **[M]** |
| **4** | «LM-planner + diffusion-renderer híbrido» | Correcto, **pero el LM planner es opcional y nosotros no lo cargamos**. Conviene decirlo: nuestra Fase 1 usa el renderer sin planner | **[M]** |
| **5** | HeartMuLa «~3B, 10–12 GB con HeartCodec cargado» | HF declara **4B params en F32**, **15,8 GB** de pesos, más **HeartCodec de 2B en F32** que upstream desaconseja bajar a bf16. Los 10–12 GB son **optimistas**; ver §8.1 | **[D]** + **[C]** |
| **6** | Tabla sin columna de idiomas | ACE-Step 1.5 declara **50+**; HeartMuLa **5** (`zh,en,ja,ko,es`); YuE **4–5 pero solo tres grupos de checkpoints (`en`, `zh`, `jp-kr`)**. Para un producto **en castellano** esto es criterio de selección de primer orden, no una nota al pie | **[D]** |

> Estas correcciones **no cambian ninguna cifra de presupuesto, fase ni estado**. Son de exactitud documental. La #1 sí es relevante para la trazabilidad: el manifiesto de procedencia de cada generación (invariante innegociable de `CLAUDE.md`) registra la licencia de los pesos, y **registrar «Apache 2.0» sobre un modelo MIT sería un dato falso en un artefacto que existe precisamente para ser auditable**.

---

## 6. Ficha ampliada — MiniMax-Music3 (candidato condicional)

Se documenta aquí por exigencia de `spec.md` §5.3 y §11.1. **No es alcance, no está presupuestado y no sustituye a YuE**: lo complementa como alternativa condicional si G1-bis lo justifica.

**Licencia — verificada contra el fichero `LICENSE` del repo, no contra la ficha [D]:**

- Título literal: **«MiniMax-Music3 COMMUNITY LICENSE»**, «Copyright (c) 2026 MiniMax». El *frontmatter* de la model card **no lleva** clave `license`; el identificador solo existe dentro del propio fichero.
- **Atribución en UI**: hay que «prominently display "MiniMax-Music3"» en la interfaz de todo producto o servicio comercial que lo use.
- **Umbral de 20 M$** (§3.2, *Commercial Terms*): si los ingresos anuales combinados del licenciatario **y sus afiliadas** superan **20 millones de dólares** (o equivalente), hace falta **autorización previa por escrito** solicitada a `api@minimax.io` con el asunto «MiniMax-Music3 licensing - authorization request».
- **AUP (Exhibit A)** de cumplimiento obligatorio, con lista de usos prohibidos que el licenciante **se reserva el derecho a actualizar**.
- **Salvaguardas técnicas y organizativas**: quien ofrezca a terceros la generación con el modelo debe implementarlas **antes del lanzamiento** y mantenerlas, probarlas y revisarlas periódicamente, sin desactivarlas ni permitir que se eludan.
- **Indemnización** a favor del licenciante y entrega «AS IS».
- Componentes con licencia propia declarada: Qwen3-8B (Apache 2.0), DiT-2B derivado de Stable Audio tools (MIT), VAE derivado de DAC (MIT).

**Lectura para este proyecto (no es dictamen legal; el dictamen es de G2):**

1. La cláusula de **atribución en UI** choca de frente con `ui-design.md`: obliga a poner una marca de terceros en la interfaz de un producto cuya identidad visual es propia y deliberada. Es una **decisión de producto**, no solo legal.
2. El umbral de 20 M$ es **irrelevante en la práctica** para un proyecto personal, pero deja de serlo si se activa GC-01 (comercialización) y hay afiliadas.
3. Las **salvaguardas obligatorias** son la cláusula cara: no es una obligación pasiva de licencia, es **trabajo de ingeniería recurrente** (implementar, mantener, probar y revisar periódicamente). Si se adopta, deja de ser «un adapter más».
4. La **AUP modificable unilateralmente** es un riesgo de dependencia: las condiciones de uso pueden cambiar después de haber integrado el modelo.
5. Nota técnica llamativa: **es el único de los cuatro que declara caber en 8 GB con *group offloading*** — mejor encaje con nuestra GPU local que HeartMuLa. A cambio entrega **32 kHz** frente a los 48 kHz medidos de ACE-Step.

> **Acción viva:** la pregunta para el lote de G2 (T-01) ya está registrada en `spec.md` §11.1. Este spike la confirma palabra por palabra y **añade el matiz 3**: la pregunta a legal debería incluir explícitamente la obligación de salvaguardas técnicas continuas, no solo la atribución y el umbral.
>
> ⚠️ **Superado el 2026-09-03 (§12).** **No existe tal «lote de G2»**: el gate se cerró el 2026-08-18 por decisión del propietario, **sin dictamen jurídico**, y MiniMax **nunca entró en él** (cero menciones en todo `gates/`). La acción se reancla a **GC-01 (h)** de `gates/gobernanza.md` §8. Además, el disparador de cada cláusula matiza el punto 3: **la obligación de salvaguardas (§4 de la licencia) no se activa en uso estrictamente personal**, solo al ofrecer generación a terceros.

---

## 7. Confirmación de D-06

> **D-06 se confirma sin cambios.** **ACE-Step 1.5 es el modelo del gate G1. HeartMuLa es el segundo adapter. YuE 7B sigue siendo candidato condicional de tercer adapter, fuera de Fase 1.** No hay motivo para alterar el orden, y sí motivos nuevos y verificados para mantenerlo.

### 7.1 ACE-Step 1.5 como modelo de G1 — cuatro razones, ninguna de fe

1. **Es el único que se ha ejecutado.** Artefacto construido y verificado (sha256 `3faa5ac9…`), imagen contenerizada, dos WAV en disco con duración exacta a 30 s y 180 s (**0,000 % de desviación**) y las diez comprobaciones bloqueantes en verde **[M]**. Los otros dos son documentación.
2. **Es el único que cabe en la GPU disponible.** Pico de **7.455 MiB de 8.191** **[M]**. HeartMuLa no cabe (§8.1) y YuE no cabe ni de lejos (§8.2).
3. **Es el que menos fricción de licencia tiene.** MIT, sin obligaciones de atribución ni umbrales, con copia del texto archivada localmente **[M]**.
4. **Es el que mejor cubre el castellano.** 50+ idiomas declarados **[D]** frente a los 5 de HeartMuLa y los 3 grupos de checkpoints de YuE. Para un producto con i18n en castellano desde el día 1, es criterio de primer orden.

Con una salvedad honesta: **nada de lo anterior dice que suene bien**. Eso lo decide G1 por escucha, con los umbrales ya fijados y sin degradarlos.

### 7.2 HeartMuLa como segundo adapter — se mantiene, y por qué

Sigue siendo la elección correcta, por cuatro razones y a pesar de un problema serio:

- **Licencia limpia y explícita.** Apache 2.0 para repo **y** pesos, con el cambio de licencia anunciado en el propio README (HeartTranscriptor pasó de `cc-by-nc-4.0` a `apache-2.0` en el historial de commits de HF) **[D]**. Cero obligaciones añadidas.
- **Cubre castellano de forma declarada y explícita** (`es` en el *frontmatter*) **[D]**. Es una segunda opinión útil, no redundante.
- **Aporta herramientas que no habría que construir**: **HeartTranscriptor-oss** (0,8B, base Whisper, Apache 2.0, `safetensors`) es el candidato principal para el **WER** del protocolo de G1 (`g1-protocolo.md` §6.2), y es **independiente del adapter**: se puede usar aunque HeartMuLa como generador nunca llegue a integrarse.
- **Aporta diversidad arquitectónica real.** ACE-Step es difusión; HeartMuLa es LM autorregresivo sobre codec. Es exactamente el *trade-off* que justifica D-02 (registry pluggable): un segundo adapter que fuera otro modelo de difusión no demostraría nada.

**El problema, que no cambia el orden pero sí el plan:** **no cabe en la GPU local** (§8.1). Consecuencia sobre `tasks.md`: **T-29** (contenerización de HeartMuLa) y **T-34** (G1-bis) **no son ejecutables en modo GPU local** y vuelven a depender de RunPod, en contra del criterio de coste cloud cero de D-29. Se registra como acción A-2, no como cambio de D-06: si hubiera que reordenar por hardware, el sustituto natural sería MiniMax-Music3 (8 GB con group offloading) — y **está bloqueado por licencia hasta G2**, así que no es sustituto disponible hoy.

> ⚠️ **Corregido el 2026-09-03 (§12), dos veces.** (i) **No está «bloqueado hasta G2»**: G2 nunca preguntó por esta licencia, así que la condición quedó **huérfana, no resuelta a favor**. (ii) **No está establecido que sea sustituto**: el «8 GB» es nominal de tarjeta y declarado por upstream sin verificar, mientras que aquí hay **7.202 MiB libres [M]**. Léase «candidato a comprobar», no «sustituto natural».

### 7.3 YuE 7B se queda donde está — condicional y tercero

Cuatro razones convergentes, y las dos primeras son descalificatorias por sí solas para Fase 1:

1. **Hardware imposible en local, y caro en cloud.** «For full song generation (many sessions, e.g., 4 or more): Use GPUs with at least 80GB memory» **[D]**. Con ≤24 GB solo se pueden encadenar **2 sesiones**, es decir, ni una canción completa.
2. **Dependencia dura de FlashAttention 2**, que upstream declara «mandatory» para no reventar por memoria **[D]**. FA2 exige **compute capability 8.0 (Ampere) o superior**; **Pascal `sm_61` está excluido** **[D]**. Y la alternativa obvia, SDPA, es en esta tarjeta **12,9× más lenta que eager** **[M]**. La combinación es terminal: en esta máquina, YuE no es lento, es inviable.
3. **Coste temporal desproporcionado**: **360 s de cómputo por cada 30 s de audio en una RTX 4090** **[D]**. Extrapolar eso a una GTX 1070 no tiene sentido ni como ejercicio.
4. **Cobertura de castellano débil.** Los checkpoints *annealed* publicados son `en`, `zh`, `jp-kr` **[D]**. Su fortaleza —adherencia a la letra— es precisamente la que peor se transfiere a un idioma sin checkpoint dedicado.

Su ventaja declarada (mejor adherencia a la letra, canciones completas, stems de voz y acompañamiento) **sigue siendo la razón de mantenerlo como condicional**: es la carta a jugar si G1-bis muestra que ni ACE-Step ni HeartMuLa dan adherencia suficiente. Pero el disparador de esa carta es un **fallo medido**, no una preferencia, y su ejecución exige cloud de 80 GB. Queda en Fase 2, sin presupuestar, exactamente como está hoy.

### 7.4 Los que no compiten

Por cerrar el catálogo de `spec.md` §11.1: **MusicGen Stereo** sigue **descartado** (CC BY-NC, incompatible con el invariante de licencias comerciales). **DiffRhythm 2** y **Stable Audio Open 1.5** no se comparan aquí: el primero no está en D-06 y el segundo tiene un límite declarado de 47 s por muestra que lo excluye de «canción completa». Ninguno de los dos tiene tarea asignada; se dejan como referencia de §11.1.

---

## 8. Encaje con la GPU local (GTX 1070, 8 GB) — el eje que decide

Esta sección existe porque el criterio «VRAM mínima y de confort» sin contrastar contra **la máquina que tenemos** no sirve para decidir nada.

### 8.1 HeartMuLa: los números

| Componente | Tamaño publicado **[D]** | Huella estimada **[C]** | ¿Cabe en 7.202 MiB libres **[M]**? |
|---|---|---|---|
| `HeartMuLa-oss-3B` (LM) | 15,8 GB en 4 shards, **F32**, «4B params» | **≈ 7,9 GB** en fp16 | **No**, ni él solo |
| `HeartCodec-oss-20260123` | «2B params», **F32** | ≈ 4 GB en fp16 — pero **upstream desaconseja bf16 en el codec**: «degrades audio quality», por defecto fp32 → ≈ **8 GB** | **No** |
| `HeartTranscriptor-oss` | 0,8B, F32 | ≈ 3,2 GB en F32 | **Sí** (y es el que necesita G1 para el WER) |

Upstream **no publica cifra de VRAM**; lo que ofrece son dos mitigaciones **[D]**: repartir LM y codec en GPU distintas («e.g. 2 4090s») o `--lazy_load true`, que carga y descarga módulos por etapa. `--lazy_load` **no resuelve nuestro caso**: no reduce el pico de la etapa más pesada, y esa etapa —el LM en fp16, ~7,9 GB— **ya excede** los 7.202 MiB libres por sí sola. Upstream no ofrece cuantización.

> **Conclusión operativa.** Con la GPU actual, **HeartMuLa como generador no es ejecutable en local**. Sus **herramientas auxiliares sí**: HeartTranscriptor-oss (0,8B) cabe holgadamente y es lo que G1 necesita para el WER. La dependencia que la Fase 0 tiene de la familia HeartMuLa **no es la del generador**.

### 8.2 YuE: ni con mitigaciones

Suma mínima de pesos: s1 de 7B en BF16 (≈ 12–14 GB **[C]**) + s2 de 1B + `xcodec_mini_infer` + upsampler Vocos. Antes de llegar a la VRAM, **el bloqueo es FlashAttention 2** (§7.3, punto 2). Existen ports comunitarios (`YuE-UI` con modelos cuantizados dice funcionar en 8 GB; hay un port *legacy* de FA2 para Pascal/Volta), pero son **de terceros, sin licencia verificada y sin mantenimiento acreditado**: integrarlos chocaría con el invariante de licencias verificadas ANTES de integrar. **No se abre esa vía.**

### 8.3 Tabla de decisión

| Modelo | ¿Ejecutable en GTX 1070 8 GB? | Camino si se necesita |
|---|---|---|
| **ACE-Step 1.5** (turbo 2B, fp16, sin planner) | **Sí, verificado** — pico 7.455/8.191 MiB, 737 MiB de margen **[M]** | Ninguno. Es el camino actual |
| ACE-Step 1.5 + LM planner 0.6B | **No sin offload** — ≈1,2 GB adicionales **[C]** sobre 737 MiB de margen | Offload de CPU, o GPU mayor |
| ACE-Step 1.5 XL (DiT 4B) | **No** — ~9 GB solo de pesos **[D]**; upstream pide ≥12 GB con offload | GPU de ≥20 GB. Candidata de spike, no de Fase 1 |
| **HeartMuLa oss-3B** | **No** — ~7,9 GB solo el LM **[C]** | RunPod ≥24 GB para T-29 / T-34 |
| HeartTranscriptor-oss | **Sí** — 0,8B **[D]** | Ninguno. Es la herramienta de WER de G1 |
| **YuE 7B** | **No**, doble bloqueo: VRAM + FA2 exige `sm_80+` **[D]** | Cloud ≥80 GB para canción completa. Fase 2 condicional |
| MiniMax-Music3 | **Declarado que sí** con group offloading **[D]** — sin verificar. **Ojo (§12):** ese «8 GB» es capacidad **nominal**; aquí hay **7.202 MiB libres [M]** | **Condición sin resolver** (§12): la licencia **nunca entró en G2**. Evaluación legal anclada a **GC-01 (h)**; necesidad técnica, a **G1-bis** |

---

## 9. Acciones que salen de este spike

Ninguna requiere decisión del propietario salvo A-4. Ninguna cambia cifras de presupuesto.

| # | Acción | Dónde | Prioridad |
|---|---|---|---|
| **A-1** | Corregir las seis inexactitudes de `spec.md` §11.1 (§5 de este documento). La #1 —MIT, no Apache 2.0— **antes** de que el manifiesto de procedencia registre licencia de pesos en una generación real | `spec.md` §11.1 | **Alta** |
| **A-2** | Registrar que **T-29 y T-34 (G1-bis) no son ejecutables en GPU local**: el segundo adapter vuelve a depender de RunPod, en contra del criterio de coste cloud cero de D-29 | `tasks.md` T-29 / T-34, nota | **Alta** |
| **A-3** | **HeartCLAP no está publicado** (6 repos en la organización de HF, ninguno es HeartCLAP; issue #4 de `heartlib` abierto por el equipo de HF pidiéndolo). `g1-protocolo.md` §6.1 lo nombra candidato principal para medir CLAP: hay que designar suplente **antes de T-09** | `gates/g1-protocolo.md` §6.1 | **Alta — bloquea G1** |
| **A-4** | ~~Ampliar la pregunta de G2 sobre MiniMax-Music3 para incluir la **obligación continua de salvaguardas técnicas** y la **AUP modificable unilateralmente**, no solo atribución y umbral de 20 M$~~ — **⚠️ inejecutable: no hay lote de G2. Sustituida por A-4′ (§12.7), con destino `gates/gobernanza.md` §8, GC-01 (h)** | ~~`tasks.md` T-01 / `gates/g2-matriz-resultados.md`~~ → `gates/gobernanza.md` §8 | ~~Media~~ → **Baja** (no bloquea hasta GC-01) |
| **A-5** | Anotar en T-07 que `CONTINUATION` (Complete) **no está en `turbo`**, solo en `base`/`xl-base`: un negativo ahí es propiedad del checkpoint, no del modelo | `tasks.md` T-07 | Media |
| **A-6** | Registrar que **HeartTranscriptor-oss sí cabe en local** (0,8B) y es independiente del adapter de HeartMuLa: el WER de G1 **no** queda bloqueado por A-2 | `gates/g1-protocolo.md` §6.2 | Media |

---

## 10. Criterios de aceptación de T-06

| Criterio del ledger | Estado | Dónde |
|---|---|---|
| Comparativa documentada de ACE-Step, HeartMuLa y YuE 7B contra **licencia**, **VRAM mínima y de confort**, **arquitectura** y **capacidades declaradas** | **Cumplido** | §2 (tabla maestra), §4 (ACE-Step), §8 (VRAM contra hardware real) |
| Confirmación explícita de que **ACE-Step es el modelo de G1 y HeartMuLa el segundo adapter (D-06)**, o documentación de por qué cambia el orden | **Cumplido — se confirma sin cambios** | §7 |
| *Subtarea:* revisar documentación oficial de los tres modelos (licencia, requisitos de hardware, arquitectura) | **Cumplido** — fuentes primarias en §11 | §2, §4, §6, §11 |
| *Subtarea:* contrastar contra los resultados preliminares del contenedor de ACE-Step (T-05) | **Cumplido** | §3, incluida la comprobación cruzada que identifica el checkpoint como `acestep-v15-turbo` |

---

## 11. Fuentes consultadas

Todas verificadas el **2026-09-02** salvo indicación. Se listan solo las que sostienen alguna afirmación **[D]** del documento.

**ACE-Step**
- `github.com/ace-step/ACE-Step-1.5` — README: licencia MIT, tabla de tramos de VRAM, matriz de capacidades por checkpoint, tamaños 2B/XL, duración 10–600 s, 50+ idiomas.
- `huggingface.co/ACE-Step/Ace-Step1.5` — tag `license: mit`; contenido del repo (Qwen3-Embedding-0.6B, `acestep-5Hz-lm-1.7B`, `acestep-v15-turbo`, `vae`); declaración de procedencia del entrenamiento. **Sin fichero `LICENSE` (404).**
- `arxiv.org/abs/2602.00744` — «ACE-Step 1.5: Pushing the Boundaries of Open-Source Music Generation»: arquitectura desacoplada LM/DiT, destilación de 50 a 4–8 pasos.
- `github.com/ace-step/ACE-Step` y `huggingface.co/ACE-Step/ACE-Step-v1-3.5B` — **ACE-Step v1 3.5B, Apache 2.0**: el origen de la confusión de licencia.

**HeartMuLa**
- `github.com/HeartMuLa/heartlib` — «We update the license of this repo and all related model weights to Apache 2.0»; `--lazy_load`; reparto en 2 GPU; bf16 desaconsejado en el codec; `--max_audio_length_ms` 240000; RTF ≈ 1,0; versión 7B no publicada.
- `huggingface.co/HeartMuLa` (organización) — **6 repos, ninguno HeartCLAP**.
- `huggingface.co/HeartMuLa/HeartMuLa-oss-3B` (+ `/raw/main/README.md`) — Apache 2.0; 4 shards, 15,8 GB, F32, «4B params»; idiomas `zh, en, ja, ko, es`.
- `huggingface.co/HeartMuLa/HeartCodec-oss-20260123` — Apache 2.0, «2B params», F32, `safetensors`, model card **vacía**.
- `huggingface.co/HeartMuLa/HeartTranscriptor-oss` — Apache 2.0, 0,8B, F32, tag `whisper`, 5 idiomas.
- `arxiv.org/abs/2601.10547` — familia de 4 componentes; HeartCodec a 12,5 Hz; HeartCLAP descrito pero **no publicado**.
- `github.com/HeartMuLa/heartlib` issue #4 — el equipo de open source de Hugging Face pide la publicación de HeartCLAP y del 7B.
- `heart-mula.com/install` — **sitio de operador, no upstream**: 16 GB mín. / 24 GB+ recomendado. Citado como estimación de tercero, no como especificación.

**YuE**
- `github.com/multimodal-art-projection/YuE` — Apache 2.0 código y pesos; ≤24 GB → 2 sesiones; ≥80 GB para canción completa; FA2 «mandatory»; H800 30 s → 150 s; RTX 4090 30 s → ~360 s; `xcodec_mini_infer`; idiomas.
- `huggingface.co/m-a-p/YuE-s1-7B-anneal-en-cot` — Apache 2.0, BF16, `safetensors`, metadatos «6B params», tag `llama`.
- `arxiv.org/abs/2503.08638` — dos etapas, codebook-0 y residuales, upsampler Vocos 16 kHz → 44,1 kHz, modos single-track y dual-track.
- `github.com/Dao-AILab/flash-attention` — FA2 exige Ampere/Ada/Hopper, **compute capability ≥ 8.0**; Pascal y Volta excluidos.

**MiniMax-Music3**
- `huggingface.co/MiniMaxAI/MiniMax-Music3` — arquitectura y tamaños por componente; 32 kHz 16 bit estéreo; 9.000 frames a 25 fps; VRAM 24 GB / ~22 GB con offload / 8 GB con group offloading; `diffusers` PR #14456, SGLang-Omni, ComfyUI.
- `huggingface.co/MiniMaxAI/MiniMax-Music3/raw/main/LICENSE` — **«MiniMax-Music3 COMMUNITY LICENSE»**; atribución en UI; §3.2 umbral de 20 M$; Exhibit A (AUP); salvaguardas técnicas y organizativas; indemnización; licencias de los componentes upstream.

**Evidencia propia (no web)**
- `D:\srv\ace-step\weights\ace_step_1_5.safetensors` — cabecera parseada el 2026-09-02: 1.169 tensores F16 + 7 U8 + 1 F32; **3.074.063.112 parámetros** sin `aux`.
- `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt` (1.064 B, sha256 `05a6bce4…85357`) y `LICENSE.qwen3-embedding.apache-2.0.txt`.
- `apps/runner/adapters/ace_step/vendor/config.json` (sha256 `74745ff7…`) — parámetros de arquitectura del DiT turbo.
- Mediciones de T-03 / T-05 del 2026-09-01: tiempos, picos de VRAM, techo de duración, comportamiento de SDPA frente a eager en `sm_61`; informes en `D:\srv\ace-step\out\t03-smoke-*-informe.json`.

---

## 12. Addendum 2026-09-03 — MiniMax-Music3 reevaluado: el bloqueo no está resuelto, está **sin resolver**

> **Por qué existe este addendum.** El 2026-09-03 se plantea reabrir MiniMax-Music3 con el razonamiento «G2 cerró el 2026-08-18, luego el candidato se desbloquea». **Ese razonamiento es falso**, y comprobarlo era el primer trabajo de este addendum, antes de escribir ninguna recomendación. Lo que sigue reevalúa el candidato con la misma regla de honestidad de §0: cada afirmación marcada **[M]**, **[D]** o **[C]**. Fuentes primarias reverificadas hoy.
>
> **Este addendum no reescribe §2, §6, §7.2 ni §8.3.** Los deja como estaban el 2026-09-02 y declara en §12.6 qué frases suyas quedan superadas. Nada se corrige a posteriori en silencio.

### 12.1 Qué preguntó G2 y qué no preguntó

**La comprobación, y dónde se hizo.** Tres verificaciones sobre los ficheros del repositorio, todas del 2026-09-03:

| # | Comprobación | Resultado |
|---|---|---|
| 1 | `grep -ci minimax gates/g2-matriz-resultados.md` | **0**. Ni una mención en el documento del gate |
| 2 | `grep -rni minimax gates/` (directorio completo: `g2-matriz-resultados.md`, `gobernanza.md`, `g1-protocolo.md`) | **0 resultados.** Tampoco aparecen «salvaguard», «atribuci» ni «20 M» en ningún fichero de `gates/` |
| 3 | `grep -rni minimax` en toda la iniciativa | Aparece en `spec.md` (§5.3, §11.1), `evaluation.md` (§2, §11, changelog), `improvement-plan.md` (changelog), `tasks.md` (nota de `T-01`, changelog) y en este spike. **En `gates/` no aparece nunca** |

**Lo que G2 sí preguntó** (`gates/g2-matriz-resultados.md` §3 y §4) son exactamente dos cosas, y ninguna es esta **[D]**:

- **I-05 — procedencia**: ¿se acepta usar audio de modelos cuya declaración de datos de entrenamiento es `no divulgada`, en uso interno (a1) y en producciones de cliente (a2)?
- **I-05b — protegibilidad**: ¿es protegible y licenciable en exclusiva el output generado sin autoría humana?

Su matriz de resultados de §6 tiene cuatro filas, y las cuatro hablan de esas dos preguntas. **La fila 1, «sí total», que es la que se aplicó, es una respuesta sobre procedencia — no sobre términos de licencia de ningún modelo concreto.**

**Cómo entró la pregunta de MiniMax y por qué nunca salió.** La nota está en `tasks.md`, en `T-01`, con fecha 2026-08-18, y su propio texto se autoanula **[D]**:

> «Candidato añadido al lote de preguntas (2026-08-18, hallazgo HF, **informativo — no reabre la tarea**). […] **No crea tarea nueva ni cambia el estado `completado` de `T-01`**.»

Es decir: la pregunta se anotó **el mismo día** en que `T-01` se cerraba, **en una tarea ya cerrada**, con la instrucción explícita de no reabrirla. Nunca llegó al documento del gate, nunca se formuló y nunca se respondió. La acción **A-4** de §9 de este spike —redactada el 2026-09-02— pedía precisamente repararlo, y **sigue sin ejecutar**.

**Y hay un segundo motivo, más fuerte, por el que «ampliar la pregunta de G2» ya no es posible.** G2 no se cerró con un dictamen jurídico: se cerró **por decisión del propietario** (`g2-matriz-resultados.md`, banner y §10) **[D]**. Sus propios criterios de aceptación quedaron en **1 de 3**, y el propio documento lo declara sin maquillar:

- «El **informe escrito de asesoría jurídica no está archivado**.»
- «La **pregunta 2 (I-05b) no tiene respuesta**.»
- «Los **ToS de Suno no están verificados**.»
- «El **Anexo A no está firmado**.»

**No existe un dictamen de legal al que añadirle una pregunta.** El canal «G2» está cerrado y vacío. Esa deuda se trasladó el 2026-09-01 al **gate de comercialización GC-01** (`gates/gobernanza.md` §1 y §8), cuyas condiciones (a), (b) y (c) son literalmente las tres deudas de arriba **[D]**.

> **Conclusión de §12.1.** La condición «bloqueado por licencia **hasta** dictamen de G2» **no se resolvió a favor: quedó huérfana**. El gate al que apuntaba se cerró sin haberla mirado y sin producir dictamen alguno. Un candidato condicional cuya condición apunta a un gate cerrado no está desbloqueado — **está apuntando a una referencia muerta**, y eso es peor que estar bloqueado, porque parece resuelto.

### 12.2 La licencia comunitaria, releída contra el fichero (2026-09-03)

Reverificada hoy contra `huggingface.co/MiniMaxAI/MiniMax-Music3/raw/main/LICENSE`. Confirma §6 palabra por palabra y **añade un matiz decisivo que §6 registró pero no explotó: el disparador de cada cláusula**.

| Cláusula | Texto de la fuente **[D]** | ¿Se dispara **hoy** (proyecto personal, un solo usuario, sin terceros)? | ¿Se dispara en **GC-01**? |
|---|---|---|---|
| **§3.1 — atribución en UI** | «prominently display "MiniMax-Music3" on user interface commercial product or service uses Software» | **No.** El disparador es «commercial product or service». Hoy no hay ninguno | **Sí** |
| **§3.2 — umbral de ingresos** | Autorización previa por escrito si los ingresos anuales combinados del licenciatario y sus afiliadas superan **20 M$**; solicitud a `api@minimax.io` | **No** | **Casi con seguridad no.** Es ruido para un proyecto de una persona |
| **§4 — salvaguardas técnicas y organizativas** | «implement, maintain, test, periodically review reasonable proportionate technical organizational safeguards». Aplica a quien ofrezca «a third-party product, service, or hosted service» que permita a otros generar. Prohibido desactivarlas, debilitarlas materialmente o permitir que se eludan; la responsabilidad de hacerlas cumplir es del licenciatario | **No.** El disparador es *ofrecer generación a terceros*. En modo solo no hay terceros | **Sí — y es la que duele** |
| **§2 + Exhibit A — AUP** | Uso condicionado al cumplimiento de la AUP; «MiniMax reserves right update» | **Sí**, ya | **Sí** |
| **Indemnización + AS IS** | «INDEMNIFY AND HOLD HARMLESS MINIMAX»; responsabilidad exclusiva del licenciatario sobre si usar, reproducir, modificar o distribuir el Software **o sus outputs** es apropiado | **Sí**, ya | **Sí** |

**Qué implica cada una, en concreto y sin dramatizar:**

1. **La atribución en UI es barata — en horas.** Es una línea de crédito visible en la interfaz: horas despreciables. Lo que cuesta no es implementarla, es **decidirla**: `ui-design.md` define una identidad visual propia y deliberada («estudio nocturno», acento `#34D399`, firma de condensación de onda) y esta cláusula mete una marca de tercero de forma **prominente** dentro de ella. Es una decisión de producto del propietario, no un ticket. **Y no se dispara hasta que haya producto comercial.**
2. **El umbral de 20 M$ es irrelevante hoy y casi con seguridad también mañana.** Un proyecto personal de una persona no se acerca a esa cifra ni en el escenario optimista de GC-01. Conviene decirlo sin rodeos para que no siga apareciendo en las listas como si fuera un riesgo: **no lo es**. Ocupa espacio en la conversación que merecen las otras dos.
3. **Las salvaguardas continuas de §4 son la única cláusula que puede doler de verdad, y hoy no se dispara.** Cuatro razones por las que, cuando se dispare, no es «un adapter más»:
   - **No es una obligación pasiva de licencia, es un régimen operativo**: implementar *antes* del lanzamiento y después **mantener, probar y revisar periódicamente**. Una obligación con verbo en presente continuo no se cierra con una tarea del ledger; se paga cada mes que el servicio esté vivo.
   - **La licencia no acota «periodically» ni «reasonable proportionate»**. El coste no tiene techo escrito: lo fija quien lo interprete, y en una disputa no sería el licenciatario.
   - **La responsabilidad de hacerlas cumplir es explícitamente del licenciatario**, incluida la prohibición de permitir que se eludan. En una plataforma abierta a terceros eso significa moderación de entradas y salidas, no solo un filtro.
   - **Ninguna fase del plan presupuesta trabajo recurrente de este tipo.** El ledger presupuesta tareas, no obligaciones perpetuas. Adoptar §4 abre una partida de OPEX que hoy no existe en ningún documento.
4. **La AUP modificable unilateralmente es riesgo de dependencia**, y es el más incómodo de mitigar: las condiciones pueden endurecerse **después** de haber integrado el modelo y generado pistas con él. Mitigación posible y barata: archivar copia fechada del `LICENSE` y de la Exhibit A el día de la integración, igual que ya se hizo con `LICENSE.acestep.mit.txt` **[M]**. No evita el cambio; deja constancia de bajo qué términos se generó cada pista, que es exactamente para lo que existe el manifiesto de procedencia.
5. **La indemnización va en dirección contraria a la alternativa que el proyecto evaluó.** `evaluation.md` §6.5b estudiaba comprar a un proveedor **con indemnización a favor de Daycry**. Aquí la indemnización es **a favor de MiniMax**, y el licenciatario asume además la responsabilidad exclusiva de juzgar si distribuir los outputs es apropiado. No descalifica —ACE-Step, siendo MIT, también se entrega «AS IS»—, pero conviene no confundir «licencia con uso comercial permitido» con «riesgo transferido»: aquí el riesgo se retiene entero.

> **Resumen honesto de §12.2 para un proyecto personal con posible comercialización futura (GC-01):** hoy la Community License impone, en la práctica, **AUP + indemnización + AS IS**. Eso es sensiblemente **menos** de lo que sugería la lectura del 2026-09-02, que presentaba las tres obligaciones como si aplicaran ya. Lo que no cambia es que **todas se activan a la vez el día que se cruce GC-01**, y la de §4 es de coste abierto e indefinido.

### 12.3 Encaje en hardware: lo declarado sigue siendo declarado

**El estado no ha cambiado desde el 2026-09-02: «declarado que sí, sin verificar».** No se ha descargado el modelo, no se ha parseado su cabecera `safetensors`, no se ha construido imagen y **no se ha ejecutado ni una sola vez**. Todo lo de este apartado es **[D]** de la ficha o **[C]** de aritmética sobre ella.

**Tamaños por componente que constan en la fuente primaria [D]** (reverificados el 2026-09-03 en `huggingface.co/MiniMaxAI/MiniMax-Music3`):

| Componente | Tamaño declarado **[D]** | Huella en fp16 **[C]** |
|---|---:|---:|
| Global LLM (inicializado desde Qwen3-8B) | 8 B | 16,0 GB |
| Local LLM (detalle acústico por frame) | 0,6 B | 1,2 GB |
| Flow Matching | 2,4 B | 4,8 GB |
| Flow-VAE Decoder | 123 M | 0,246 GB |
| **Total** | **11,123 B** | **≈ 22,2 GB** |

*Aritmética: parámetros × 2 B, con GB = 10⁹ B, misma convención que §8.1 de este documento.*

**Comprobación cruzada que da confianza al cálculo [C].** La ficha declara «~22 GB» con offloading automático de CPU **[D]**. Nuestro cálculo de pesos residentes en fp16 da **22,2 GB**. Coinciden: la cifra de 22 GB de upstream es, esencialmente, **todos los pesos residentes en fp16 y poco más**. Es la misma clase de comprobación que en §3.1 identificó nuestro checkpoint de ACE-Step (4,788 GB frente a los «~4.7GB for 2B» declarados).

**La contradicción de metadatos sigue abierta y hoy se confirma [D].** La barra lateral de HF declara **«2B params», tipo de tensor F32**; el cuerpo de la ficha describe 8B + 0,6B + 2,4B + 123M. Son incompatibles entre sí, y además con el propio «~22 GB» (11,1 B en F32 serían ~44,5 GB de descarga **[C]**). **No podemos resolverlo**: con ACE-Step lo resolvimos parseando la cabecera del `safetensors` **[M]**, y aquí no hay fichero descargado que parsear. Importa porque el manifiesto de procedencia registra tamaño y hash de pesos, y **no se puede citar un metadato que se contradice con su propia ficha**.

**Qué dice exactamente la afirmación de 8 GB, y contra qué presupuesto [D]:**

- «makes fit even 8 GB video cards», con el comentario de código «slower, but fits in 8 GB».
- El mecanismo es `apply_group_offloading` con `offload_type="leaf_level"` y `use_stream=True`, **aplicado al modelo de lenguaje**: «streaming the language model layer by layer».

**Por qué esto NO permite decir que cabe en nuestra máquina.** Cuatro razones, ninguna opinable:

1. **El «8 GB» de upstream es capacidad nominal de tarjeta; el nuestro es memoria libre.** La GTX 1070 tiene **8.191 MiB totales** pero **7.202 MiB libres** con el escritorio de Windows cargado **[M]**: **989 MiB (12 %) ya consumidos** antes de cargar nada. La afirmación se mide contra un presupuesto que en esta máquina no existe.
2. **El componente mayor, solo él, es 2,3× la tarjeta entera.** El Global LLM son **16,0 GB en fp16 [C]** frente a 8.191 MiB totales. Toda la afirmación descansa **íntegramente** en que el *streaming* por capas funcione; no hay margen de error en esa hipótesis.
3. **Aritmética del conjunto residente, si el offloading solo alcanza al LM como dice la fuente [C]:** en la etapa de flow matching harían falta 2,4 B + 123 M = **2,523 B → 5,05 GB ≈ 4.812 MiB** de pesos residentes, sobre **7.202 MiB libres [M]** → quedarían **~2.390 MiB** para activaciones, la capa del LM en tránsito, sus búferes y el contexto CUDA. Para calibrar: ACE-Step, con 5.863 MiB de pesos residentes, midió un pico de **7.455 MiB [M]**, es decir **~1.600 MiB de sobrecoste no-pesos**. El margen de MiniMax es del **mismo orden que ese sobrecoste**. Aritméticamente no está descartado; tampoco está establecido.
4. **Hay un término que la aritmética de arriba no cubre y la ficha no desglosa:** el **KV cache** de un LLM de 8 B autorregresivo sobre hasta **9.000 frames acústicos [D]**. Crece con la longitud de la secuencia y no aparece en ninguna cifra publicada. La afirmación «fits in 8 GB» no dice a qué duración de canción corresponde.

**Y dos avisos que salen de lo único que hemos medido en esta tarjeta [M], aplicados aquí como razonamiento, no como medición:**

- El *streaming* por capas mueve pesos de CPU a GPU **repetidamente durante la generación**. En esta máquina, la carga de pesos de ACE-Step, tensor a tensor sobre bind mount de Windows, costó **386–390 s [M]**. El «slower» del comentario de upstream, en esta máquina y por este camino, tiene una escala que nadie ha medido y que las cifras de upstream (obtenidas en tarjetas modernas) no predicen.
- Ya nos pasó una vez que una ruta acelerada asumida por el README **degradara en silencio** en `sm_61`: SDPA cae al kernel *mem-efficient* y es **12,9× más lento que eager [M]**. `use_stream=True` es exactamente la misma clase de hipótesis: un camino optimizado cuya viabilidad en Pascal **nadie ha comprobado**.

**Otras restricciones declaradas hoy [D]**, por completitud: inferencia **requiere CUDA**; **solo generación no-streaming**; prompt de texto limitado a **5.000 tokens**; audio limitado a **9.000 frames acústicos**; los tags de sección «provide generative control rather than strict symbolic guarantees». Salida **32 kHz · 16 bit · estéreo**, frente a los **48 kHz medidos** de ACE-Step **[M]** — para una plataforma cuyo almacén es FLAC y cuya exportación premium es WAV/48 kHz, adoptar 32 kHz es un techo de banda de 16 kHz que **ningún remuestreo posterior recupera**. La ruta de integración sigue **sin versión publicada de `diffusers`**: la ficha sigue apuntando hoy al commit fijado `dafe3733fcfdbf3c48915fe77be3aef65b5d6a2d` del PR #14456, aún sin mergear **[D]**; la vía documentada como principal es SGLang-Omni. Los idiomas **siguen sin enumerarse en ninguna parte de la ficha [D]** — para un producto en castellano, sigue siendo una incógnita abierta, no un dato.

> **Estado de §12.3, sin adornos: NO se afirma que MiniMax-Music3 quepa en 8 GB, ni en esta tarjeta.** Se afirma que upstream lo declara, que la aritmética de pesos no lo contradice, que el margen es estrecho y que **la única forma de saberlo es ejecutarlo, cosa que no se ha hecho**.

### 12.4 Veredicto

**El candidato ni se desbloquea ni se descarta hoy: se le repara la condición, que estaba rota.** MiniMax-Music3 sigue siendo **candidato condicional**, exactamente el mismo estatus que tenía el 2026-08-18 — pero por un motivo distinto del que consta escrito, y con la condición apuntando a un gate vivo en vez de a uno cerrado.

### 12.5 Las tres opciones y su coste

| Opción | Qué implica | Coste |
|---|---|---|
| **(a) Dejarlo condicional, reparando la condición** | Sigue fuera de alcance y sin presupuestar. Se sustituye «bloqueado hasta dictamen de G2» (referencia muerta) por dos disparadores vivos: **G1-bis** para la necesidad técnica y **GC-01** para la licencia. A-4 se reancla a GC-01 | **0 h de desarrollo, 0 €.** Solo este addendum y las notas de §12.6 |
| **(b) Hacer ahora la consulta legal que A-4 pedía** | Consulta profesional sobre la Community License, por separado y de forma anticipada | **Gasto externo de bolsillo, sin cifra y sin presupuestar.** Las 32 h de asesoría de `evaluation.md` §6.5d **dejaron de existir como partida el 2026-09-01**: `gobernanza.md` §7 las declara «N/A en modo personal» y las reagrupa en GC-01. A-4 se escribió cuando esas horas parecían una reserva interna ya pagada; hoy no lo son |
| **(c) Descartarlo** | Sale del catálogo, como MusicGen | **0 h**, y cierra A-4 de un plumazo |

**Se recomienda (a)**, y las razones son de coste y de método, no de preferencia:

1. **(b) pagaría hoy por una respuesta que hoy no cambia ninguna decisión.** La cláusula cara —§4, salvaguardas continuas— **no se dispara en el ámbito actual** (§12.2). Preguntar ahora es pedir dictamen sobre una obligación que aún no aplica, para un modelo que **no es alcance** (Fase 2 está `bloqueada (gate)`), cuyo disparador técnico es un **G1-bis que aún no ha ocurrido** — y **G1 tampoco**. Es gastar contra una hipótesis.
2. **(b) tiene además un momento mucho más barato, y ya está reservado.** GC-01 condición (a) exige de todos modos «una consulta a un profesional y su informe escrito archivado» sobre la procedencia. **La pregunta de MiniMax cabe como un punto más de esa misma consulta, con coste marginal prácticamente nulo** — que es exactamente el argumento con el que `g2-matriz-resultados.md` §4 justificó añadir la pregunta 2 a la pregunta 1: «el coste marginal de añadir la segunda es cero (misma consulta, mismas 32 h)». Aplicar hoy ese mismo criterio dice: **no una consulta aparte, sino un punto (h) dentro de GC-01**.
3. **(c) descartaría por una cláusula que hoy no aplica y sobre un modelo que nunca se ha medido.** El precedente del proyecto para descartar es MusicGen: **CC BY-NC, un descalificador verificado y absoluto** frente al invariante de licencias comerciales. Aquí no hay nada equivalente: la Community License **permite uso comercial**, con condiciones que hoy no se activan. Descartar por incomodidad, sin medición y sin que la obligación aplique, sería el mismo error que el documento evita en todas partes: **confundir «no verificado» con «malo»**.
4. **(a) no cuesta nada mantenerlo abierto, y el hueco ya existe.** El candidato vive en una partida condicional **no presupuestada** de Fase 2 (`evaluation.md` §2 y §11). Mantenerlo cuesta cero euros y cero horas; el único coste real de tenerlo ahí era **la referencia muerta**, y este addendum la elimina.
5. **Ninguna opción degrada ningún gate ni umbral.** (a) los refuerza: sustituye un bloqueo huérfano por dos condiciones verificables, ancladas a gates que existen y tienen dueño.

**Los dos disparadores, escritos para que no se improvisen:**

| Disparador | Condición | Consecuencia |
|---|---|---|
| **Técnico** | **G1-bis** muestra adherencia a la letra insuficiente en ACE-Step **y** en HeartMuLa | Se abre la evaluación técnica de un tercer adapter. Orden de magnitud de referencia del ledger para tercer adapter + router: **≈ 50 h → 2.500 € base / 3.000 € con margen del 20 % [C]** (`.claude/rates.json`). Sigue sin presupuestar |
| **Legal** | Se activa **GC-01** (comercialización o uso con terceros) | La consulta sobre la Community License entra **como punto de la consulta de GC-01 (a)**, no como consulta aparte. Coste marginal ≈ 0 |

**Regla de precedencia, porque el orden importa:** si se dispara el técnico y **no** el legal (uso estrictamente personal), lo que aplica es solo AUP + indemnización + AS IS, y **no hace falta consulta para probarlo**. Si se dispara el legal, la consulta es **obligatoria antes de integrarlo**, se haya disparado el técnico o no. **Lo que no puede pasar es integrarlo y preguntar después**: la AUP es modificable unilateralmente y el ledger de procedencia no admite reescritura retroactiva.

### 12.6 Qué queda superado de la versión del 2026-09-02

Se corrige aquí, no allí. Las frases originales se conservan íntegras en sus secciones:

| Dónde | Decía | Estado tras este addendum |
|---|---|---|
| **§2**, fila «VRAM mínima», columna MiniMax | «**8 GB** con `apply_group_offloading` […] «slower, but fits in 8 GB» **[D]**» | **Correcto como cita, insuficiente como dato.** Ese «8 GB» es capacidad **nominal** de tarjeta; en esta máquina hay **7.202 MiB libres [M]**. Ver §12.3 |
| **§6**, punto 3 de la lectura | «Las **salvaguardas obligatorias** son la cláusula cara» | **Cierto, pero incompleto: no se dispara hoy.** Su disparador es ofrecer generación a terceros (§4 de la licencia). Aplica en GC-01, no en modo personal. Ver §12.2 |
| **§6**, «Acción viva» | «la pregunta a legal debería incluir explícitamente la obligación de salvaguardas técnicas continuas» | **Sigue vigente en el fondo, muerta en la forma.** No hay lote de G2 al que añadirla: el gate se cerró sin dictamen. Se reancla a **GC-01 (h)** |
| **§7.2**, final | «el sustituto natural sería MiniMax-Music3 (8 GB con group offloading) — y **está bloqueado por licencia hasta G2**» | **Doble corrección.** (i) No está «bloqueado hasta G2»: la condición quedó huérfana, no resuelta (§12.1). (ii) **No está establecido que sea sustituto**: su encaje en esta tarjeta es declarado y no verificado, con margen estrecho (§12.3). Léase «candidato a comprobar», no «sustituto» |
| **§8.3**, fila MiniMax | «**Bloqueado por licencia** hasta dictamen de G2» | **Sustitúyase por:** «Condición **sin resolver** — la licencia nunca entró en G2. Evaluación legal anclada a **GC-01 (h)**; necesidad técnica, a **G1-bis**» |
| **§9**, acción **A-4** | «Ampliar la pregunta de G2 sobre MiniMax-Music3 […]. Prioridad Media — firma del propietario» | **Reformulada** (§12.7). El destino ya no es `gates/g2-matriz-resultados.md` sino `gates/gobernanza.md` §8. Prioridad **baja**: no bloquea nada hasta GC-01 |

### 12.7 Acciones que salen de este addendum

Ninguna consume presupuesto. Ninguna cambia estado de tarea, fase ni cifra ratificada (656 h / 39.360 € intactos).

| # | Acción | Dónde | Prioridad |
|---|---|---|---|
| **A-4′** | **Sustituir A-4.** Añadir a `gobernanza.md` §8 una condición **(h)**: «Términos de la **MiniMax-Music3 Community License** (§3.1 atribución en UI, §3.2 umbral de 20 M$, **§4 salvaguardas técnicas continuas**, Exhibit A modificable unilateralmente, indemnización a favor del licenciante) evaluados **antes de integrar el modelo**, como punto de la misma consulta de GC-01 (a)» | `gates/gobernanza.md` §8 | Baja — **no bloquea hasta GC-01** |
| **A-7** | Corregir en `spec.md` §5.3 y §11.1 la frase «Añade una pregunta al lote del gate G2 (ver `tasks.md` T-01)»: **ese lote no existe**, G2 se cerró sin dictamen. Reapuntar a GC-01 (h) | `spec.md` §5.3, §11.1 | Media — es una referencia muerta en la fuente de verdad |
| **A-8** | Anotar en `tasks.md`, junto a la nota de `T-01` del 2026-08-18, que **la tercera pregunta candidata nunca se formuló** y que su destino pasa a ser GC-01 (h). No reabre `T-01` | `tasks.md` `T-01` | Media |
| **A-9** | Si algún día se dispara el criterio técnico, **el primer trabajo no es contenerizar: es descargar los pesos y parsear la cabecera `safetensors`**, como se hizo con ACE-Step (§3.1), para resolver la contradicción «2B params / F32» frente a los 11,1 B de la ficha. Es barato y decide si merece la pena seguir | Spike futuro, no de Fase 0 | Baja — condicional |

### 12.8 Método de este addendum: qué se comprobó y qué no

**Comprobado (verde):**

- `gates/g2-matriz-resultados.md` y el directorio `gates/` completo, leídos y buscados por `grep`: **cero menciones a MiniMax, salvaguardas, atribución o umbral de 20 M$**.
- `gates/g2-matriz-resultados.md` §3, §4, §6 y §10: las dos preguntas reales de G2 y el estado real de su cierre (1 de 3 criterios, sin informe archivado).
- `tasks.md` `T-01`: el texto literal de la nota del 2026-08-18 que se autoanula, y los tres criterios de aceptación con su estado.
- `gates/gobernanza.md` §1, §7 y §8: traslado de la deuda legal a **GC-01**, sus siete condiciones (a)–(g), y la declaración de que las 32 h de asesoría son **N/A en modo personal**.
- `.claude/rates.json`: 50 €/h, margen 20 %.
- Fuentes primarias reverificadas el **2026-09-03**: ficha de `huggingface.co/MiniMaxAI/MiniMax-Music3` (tamaños por componente, VRAM 24 GB / ~22 GB / 8 GB con su redacción literal, 32 kHz 16 bit estéreo, 25 fps, 9.000 frames, 5.000 tokens, limitaciones, PR #14456 con commit fijado y aún sin mergear, idiomas ausentes, contradicción «2B params» del panel lateral) y el fichero `LICENSE` (§3.1, §3.2, §4, §2 + Exhibit A, indemnización).

**No comprobado, y por eso nada de lo anterior lo afirma (rojo):**

- **No se ha descargado, construido ni ejecutado MiniMax-Music3.** Ni un byte de pesos, ni una imagen, ni una generación. **No hay ningún [M] de este modelo en este documento, ni en este addendum.**
- **No se ha parseado su cabecera `safetensors`**, así que la contradicción de metadatos sigue sin resolver.
- **No se ha verificado que `use_stream=True` funcione en `sm_61`**, ni el coste real del *streaming* por capas en esta máquina.
- **No hay dictamen jurídico** sobre esta licencia. §12.2 es lectura del texto por el equipo técnico, **no asesoramiento legal** — la misma reserva que ya hacía §6.
- **No se ha verificado si la afirmación «fits in 8 GB» corresponde a una canción de 5 minutos o a un fragmento corto.** La ficha no lo dice.

---

## 13. Registro de cambios

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-02 | Creación (T-06). Comparativa de ACE-Step 1.5, HeartMuLa y YuE 7B + MiniMax-Music3 condicional. **D-06 confirmado sin cambios.** Seis correcciones propuestas a `spec.md` §11.1, encabezadas por **ACE-Step 1.5 = MIT, no Apache 2.0**. Seis acciones abiertas (§9), de las que **A-3 (HeartCLAP no publicado) bloquea el protocolo de G1**. | implementer |
| 2026-09-03 | **Addendum §12 — reevaluación de MiniMax-Music3.** Se comprueba y se refuta la premisa «G2 cerró, luego MiniMax se desbloquea»: **cero menciones a MiniMax en todo `gates/`**, G2 preguntó solo I-05 e I-05b, la nota de `T-01` se autoanulaba («no reabre la tarea») y el gate se cerró **sin dictamen jurídico** (1 de 3 criterios). La condición «hasta G2» quedó **huérfana, no resuelta a favor**. Licencia releída contra el `LICENSE` con el **disparador de cada cláusula**: atribución (§3.1) y salvaguardas continuas (§4) **no se disparan en modo personal**; se disparan en **GC-01**. Encaje en hardware: sigue **declarado y sin verificar** — tamaños por componente **[D]** y **≈ 22,2 GB en fp16 [C]**, que cuadra con los «~22 GB» de upstream; **no se afirma que quepa en 8 GB** (el «8 GB» de upstream es nominal; aquí hay **7.202 MiB libres [M]**). Veredicto: **seguir condicional con la condición reparada**, anclada a **G1-bis** (técnico) y **GC-01 (h)** (legal); **A-4 reformulada como A-4′** más A-7, A-8 y A-9. **Sin cambios de horas, coste, fases, estados ni gates: 656 h / 39.360 € intactos.** | implementer |
