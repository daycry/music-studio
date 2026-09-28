---
documento: spike-matriz-capacidades
titulo: "Matriz de capacidades verificadas — SECTION_INPAINT · AUDIO_TO_AUDIO · VOICE_CONDITIONING · CONTINUATION"
iniciativa: "Plataforma propia de generación musical por IA (proyecto personal)"
slug: plataforma-musical-ia
tarea: T-07
estado: completado
fecha: 2026-09-02
autor: implementer
modelos-evaluados:
  - "ACE-Step 1.5 turbo — empíricamente, sobre el artefacto y la GPU reales"
  - "HeartMuLa-oss-3B — documentalmente (código y tarjetas oficiales), sin ejecutar"
decide: "C-07 (140 h) y C-08 (80 h) de la Fase 3 — 276 h con C-03, `tasks.md` F11"
depende-de: T-03, T-05
spec: ../spec.md
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
evidencia: "D:\\srv\\ace-step\\out\\ (9 WAV + 2 informes JSON + 2 sondas + 2 registros)"
---

# Matriz de capacidades verificadas (T-07)

> **Para qué existe este documento.** `evaluation.md` §10.3 y la ficha C-11 de §7 pagaron 12 h por adelantado para no descubrir **en la Fase 3, con 276 h ya comprometidas**, que el modelo no sabía hacer lo que C-07 y C-08 prometen. Esto es la respuesta, medida hoy sobre los pesos reales y no leída de un README.
>
> **Veredicto en una línea:** los cuatro caminos **existen en el modelo y tres de ellos funcionan y se pueden medir hoy**; ninguno de los dos rasgos que bloqueaban la Fase 3 (`SECTION_INPAINT` y `AUDIO_TO_AUDIO`) sale vacío, **pero los cuatro comparten una dependencia que el artefacto actual no tiene: el codificador del VAE**, y `AUDIO_TO_AUDIO` transporta muchísima menos información de la pista original de lo que la palabra «cover» sugiere.

---

## 0. La matriz

Leyenda: **Sí** = camino ejercitado sobre los pesos reales, con control, y con efecto medido en la salida. **Parcial** = el camino corre y altera la salida, pero la capacidad *de producto* no queda demostrada. **No** = no existe o no está implementado. Todo lo de ACE-Step lleva número y fichero de audio; lo de HeartMuLa es documental por mandato de la tarea.

| Capacidad | ACE-Step 1.5 turbo | HeartMuLa-oss-3B | Evidencia principal |
|---|---|---|---|
| **`SECTION_INPAINT`** | **Sí** — región de 5 s regenerada; fuera de ella, coseno 0,996 en latente y **100,0000 % de muestras bit-idénticas** tras el empalme de onda | **No** — LM autorregresivo causal sin esquema de relleno enmascarado; nada en el repo oficial lo menciona | §3.1 · `t07-02/03/04-*.wav` |
| **`CONTINUATION`** | **Sí** — 30 s → 45 s, duración exacta, cabeza preservada (coseno 0,997) y cola nueva no silenciosa (−24,7 dBFS) | **No** hoy — arquitectura AR compatible en teoría, pero ni la API lo expone ni el codec publicado ofrece audio→tokens | §3.2 · `t07-05-continuacion.wav` |
| **`AUDIO_TO_AUDIO`** | **Sí, pero degradado** — el camino corre y la fuente **sí** dirige la salida (corr. de envolvente 0,364 frente a 0,022 del control), pero el canal es de **≈ 80 bit/s** | **No** — sin codificador expuesto en `HeartCodec` no hay forma de meter audio | §3.3 · `t07-06-cover.wav` vs `t07-07-cover-control.wav` |
| **`VOICE_CONDITIONING`** | **Parcial** — el codificador de timbre está entrenado, ocupa **1 de los 125 tokens** del condicionamiento y cambia la salida (coseno 0,834 frente a 1,000 de una repetición), pero **no se ha podido probar con una voz real** | **No** — `raise NotImplementedError("ref_audio is not supported yet.")` en el pipeline oficial, y TODO abierto en el README | §3.4 · `t07-08-timbre-referencia.wav` |

**Bloqueo común a las cuatro (ACE-Step): el codificador del VAE no viaja en el artefacto.** Los cuatro caminos consumen *latentes* de audio; convertir un WAV del usuario en latentes exige `vae.encoder.*`, que **no está** en `ace_step_1_5.safetensors` (0 de 1.177 tensores) aunque **sí existe** en la instantánea upstream ya descargada (183 tensores). Ver §4: es trabajo acotado, no un muro.

### Qué decide esto sobre la Fase 3

| Pregunta del ledger | Respuesta con evidencia |
|---|---|
| ¿Se cae C-07 (140 h, `T-67`…`T-74`)? | **No.** `SECTION_INPAINT` y `CONTINUATION` funcionan, y el criterio duro de `spec.md` §5.2 («el resto del audio **bit-idéntico** fuera de la región») **es alcanzable**: medido 100,0000 %. Pero **no sale gratis del modelo**: exige empalme de onda explícito (§3.1). |
| ¿Se cae C-08 (80 h, `T-75`…`T-79`)? | **No, pero hay que recalibrar la expectativa.** «Cover» aquí significa *el modelo escucha un boceto semántico de ~80 bit/s de tu pista*, no *reinterpreta tu grabación*. Si lo que se espera es lo segundo, C-08 se replantea **ahora** y no en la semana 20. |
| ¿Hay trabajo no presupuestado que aparece por esto? | **Sí, cuatro cosas** (§7.3): codificador del VAE, empalme de onda, arreglo de dtype del tokenizador FSQ y una rama rota en upstream. Estimación **orientativa** 15–28 h, dentro de la Fase 3, no de la Fase 1. |
| ¿Cambia algo del alcance ya aprobado (Fases 0–1)? | **No.** Ninguna tarea `T-01`…`T-53` depende de estas capacidades. Este documento **no autoriza nada**: F11 sigue `bloqueada (gate)` por G3. |

---

## 1. Método, y sus límites

### 1.1 Qué se ejecutó

Dos corridas en el contenedor de `T-05` sobre la GPU local, sin coste cloud:

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Sonda | `t07_probe.py` (sha256 `93b5f2ea…`) | `t07_probe2.py` (sha256 `21e51b19…`) |
| Cubre | P1 base · P2 repetibilidad · P3/P4 inpaint · P5 continuación | P1′ base · P6 tokenizador · P7 cover · P8 timbre · P9 referencia |
| Carga del artefacto | 384,2 s | 386,6 s |
| Resultado | murió en P6 (§6.1), P1–P5 completos y guardados | completa, `codigo_salida: 0`, 0 errores |
| Informe | `t07-matriz-capacidades.json` | `t07-matriz-capacidades-2.json` |

Entorno idéntico al de `T-03`: imagen `ace-step-runner:t05` (construida 2026-09-02 03:52:39), torch 2.13.0+cu126, GTX 1070 (sm_61, 8.192 MiB, 7.202 MiB libres al arrancar), artefacto `D:\srv\ace-step\weights\ace_step_1_5.safetensors` (sha256 `3faa5ac9caeb06b5778aa86ac7246c16d560d73dffff50b94a097bf15812d947`, 1.177 tensores, fp16). Pico de VRAM de la sonda: **6.182 MiB** — cabe con el mismo margen que una generación normal.

El código ejercitado es el **de la imagen** (`/app`), no el del bind mount: `ace_step_shim.py` `4d6a43e4…`, `vendor/pipeline/conditioning.py` `7d9052ef…`, `vendor/modeling_acestep_v15_turbo.py` `c1ab0dd5…`. Las sondas se montaron de fuera en `/probe` y no tocan ni un fichero del repositorio.

### 1.2 Cómo se probó cada camino sin tener audio de entrada

El artefacto no trae codificador de VAE, así que **no se puede convertir un WAV externo en latentes** (§4). La sonda evita ese muro por la única vía que no inventa nada: **usa como «audio de entrada» los latentes de una pista que el propio modelo acaba de generar**. Son latentes del mismo espacio que consume el decoder, es decir, exactamente el tipo de tensor que produciría el codificador. Esto prueba el camino de punta a punta salvo el primer eslabón, y esa salvedad está declarada en cada veredicto.

Pista base (P1): 30 s, prompt de estilo en castellano, letra de 4 versos, `seed=4242`, 8 pasos, `shift=3`. Salida `t07-01-base.wav`, 30,0000 s, 48 kHz, estéreo, 16 bit, RMS 0,10671, pico 0,99997; secuencia de atención cruzada `L_enc = 125` tokens; difusión 3,246 s.

### 1.3 La línea de fondo del ruido (sin esto, ningún número de abajo significa nada)

* **Dentro del mismo proceso, con la misma semilla, la salida es idéntica bit a bit**: `rmse = 0,0`, `max_abs = 0,0`, coseno `1,0` (P2). Por tanto cualquier diferencia medida después es **señal, no ruido numérico**.
* **Entre procesos distintos no lo es, pero da igual**: la misma generación repetida en la corrida 2 difiere en −80,49 dBFS frente a una señal de −19,44 dBFS (61 dB por debajo; máximo 56 LSB de 32.768; 13,1 % de muestras idénticas). Es selección de kernel/orden de reducción, no otra toma. **Consecuencia práctica para C-07: la reproducibilidad bit a bit de una pista no se puede prometer entre procesos** — otra razón para el empalme de onda de §3.1.

### 1.4 Lo que este método NO prueba

1. **Nada sobre calidad musical.** No hay escucha ciega aquí; eso es G1 (`gates/g1-protocolo.md`). Los números miden *contratos observables*, como manda `CLAUDE.md`.
2. **Nada sobre audio del usuario.** Todas las «entradas» son latentes propios. El primer eslabón (WAV → latente) está sin ejercitar por falta del codificador.
3. **Nada sobre las tareas declaradas de upstream que no se han tocado**: `extract`, `lego`, `complete`, `cover-nofsq`, el modo `chunk_mask = 2.0` («auto») y la mezcla `audio_cover_strength < 1`. Se documentan en §6.5 como pistas, con su incertidumbre.
4. **Nada sobre HeartMuLa medido.** Es documental por mandato de la tarea; ni se ha descargado ni se ha ejecutado.
5. La sonda llama a `build_pipeline()` **directamente**, no a través de `adapter.py`. El contrato del adapter ya lo cubre `T-03`; aquí sobraba la capa.

---

## 2. Dónde vive cada capacidad dentro del modelo

Todo lo que sigue está leído en el código vendorizado (`vendor/modeling_acestep_v15_turbo.py`, sha256 `c1ab0dd5…`) y confirmado con la firma real de los objetos en memoria.

El DiT recibe, además del latente ruidoso, un tensor `context_latents` que **se concatena por el eje de canal** (`AceStepDiTModel.forward`, línea 1344):

```
context_latents = cat([src_latents (64 ch), chunk_masks (64 ch)], dim=-1)   # 128 ch
hidden_states   = cat([context_latents, xt (64 ch)], dim=-1)                # 192 ch = config.in_channels
```

Es decir: **el modelo ve, fotograma a fotograma, qué audio ya existe y qué zonas debe rellenar**. Eso es la raíz de `SECTION_INPAINT`, `CONTINUATION` y `AUDIO_TO_AUDIO`. Y el codificador de condición (`AceStepConditionEncoder`) empaqueta tres fuentes en la secuencia de atención cruzada — letra, **timbre de un audio de referencia** y estilo —, que es la raíz de `VOICE_CONDITIONING`.

| Pieza | Clase | Tensores en el artefacto | Papel |
|---|---|---|---|
| Máscara de región y latente de origen | `AceStepDiTModel` | — (entrada, no pesos) | inpaint / continuación / cover |
| Codificador de timbre | `AceStepTimbreEncoder` | **48** (`dit.encoder.timbre_encoder.*`) | audio de referencia → 1 vector de 2.048 |
| Tokenizador de audio (FSQ) | `AceStepAudioTokenizer` | **32** (`dit.tokenizer.*`), 201 MiB | latente → códigos discretos de 5 Hz |
| Detokenizador | `AudioTokenDetokenizer` | **28** (`dit.detokenizer.*`), 200 MiB | códigos → pistas («LM hints») de 25 Hz |
| Decoder del VAE | `OobleckDecoder` | **182** (`vae.decoder.*`) | latente → onda |
| **Codificador del VAE** | `OobleckEncoder` | **0 — ausente** | **onda → latente (el eslabón que falta)** |

La semántica de la máscara **no se ha adivinado**: está escrita en upstream y se ha confirmado midiendo. `conditioning_masks.py` (revisión `ca1e85fe…`, blob SHA-1 `7973c6a4285af2f072506d3673e0edff547d24ac`, el mismo hash que ya registró el vendorizado de `T-03`) dice literalmente:

> `repaint_mask` is a boolean `[B, T]` tensor (**True = generate, False = preserve source**)

y construye, para repintar, `chunk_mask = zeros` con `True` solo en `[start, end)`, poniendo además **silencio** en esa región de `src_latents`. La sonda replica eso exactamente.

---

## 3. Capacidad por capacidad (ACE-Step 1.5 turbo)

### 3.1 `SECTION_INPAINT` — **Sí**

**Caso de prueba.** Pista base de 30 s. Se regenera la ventana **15,0–20,0 s** (fotogramas latentes 375–500 de 750) con el mismo prompt, la misma letra y otra semilla; `src_latents` = base con esa ventana borrada a silencio; `chunk_masks` = `True` solo ahí. Dos variantes: **(P3)** solo contexto, y **(P4)** contexto **más** la inyección por paso de upstream (`xt = where(mask, xt, t_next·ruido + (1−t_next)·origen)`).

**Latentes, por regiones** (coseno y RMSE contra la base):

| Región | P3 solo contexto | P4 con inyección |
|---|---|---|
| Preservada 0–15 s (375 tramas) | coseno **0,99504** · RMSE 0,10374 | coseno **0,99647** · RMSE 0,08751 |
| **Regenerada 15–20 s** (125 tramas) | coseno **0,28728** · corr. envolvente **−0,0585** | coseno **0,29017** · corr. envolvente **−0,04157** |
| Preservada 20–30 s (250 tramas) | coseno **0,99590** · RMSE 0,09505 | coseno **0,99675** · RMSE 0,08442 |

**Audio, medido fuera del contenedor sobre los WAV entregados:**

* Fuera de la región, la diferencia contra la base es **−40,86 dBFS** (P3) y **−41,60 dBFS** (P4), sobre una señal de −21,79 dBFS: es decir, **~19 dB por debajo de la señal, no cero**. Solo 1,1–1,2 % de las muestras coinciden. **El audio «preservado» se vuelve a renderizar y suena distinto.**
* Dentro de la región, la diferencia es tan fuerte como la propia señal (−14,0 dBFS frente a −14,53 dBFS de la base): contenido nuevo de verdad, no una variación.
* La inyección por paso **apenas ayuda** (0,7 dB). Tiene explicación: el último paso salta directo a `x0` sin restricción, así que la deriva vuelve a entrar por ahí.

**Lo que cierra el criterio de `spec.md` §5.2.** Upstream no confía en el modelo para esto: después de decodificar **empalma la onda original** (`repaint_waveform_splice.py`, blob `802bfb36…`: *«non-repaint regions still carry VAE reconstruction error»*). La sonda lo replicó con 10 ms de crossfade y lo verificó de forma independiente:

> **1.199.040 de 1.199.040 muestras fuera de la región (y de su crossfade) son bit-idénticas a la base: 100,0000 %.** Dentro de la región, 240.000 de 240.000 idénticas a la toma generada. Fichero: `t07-04-inpaint-empalmado.wav`.

**Veredicto.** `SECTION_INPAINT` **sí**, con dos condiciones que C-07 debe presupuestar: (1) el empalme de onda es **obligatorio**, no cosmético — sin él, «bit-idéntico fuera de la región» es falso; (2) para audio del usuario hace falta el codificador del VAE (§4). Lo que el modelo **no** garantiza es que la costura sea inaudible: eso es escucha humana, y el criterio de `spec.md` («2 de 3 evaluadores no identifican el empalme») sigue siendo un gate de oído, no de test.

### 3.2 `CONTINUATION` — **Sí**

**Caso de prueba.** Condicionamiento nuevo para 45 s; `src_latents` = [base de 30 s | silencio de 15 s]; máscara `False` en los primeros 750 fotogramas y `True` en los 375 restantes; inyección por paso activada.

* Duración exacta: **45,0000 s** (2.160.000 muestras), sin desviación.
* Cabeza preservada (30 s): coseno **0,99672**, RMSE 0,0857 — el mismo comportamiento que en §3.1, con la misma consecuencia (empalme obligatorio si se quiere idéntica).
* Cola nueva: RMS latente **1,05355**, comparable al del resto de la pista; en audio, **−24,7 dBFS con pico 0,643**. No es silencio ni ruido residual: es música.
* Por segundos: la base ya se apagaba en 28–30 s (−64 dBFS), la cola arranca en −31,0 dBFS, sube hasta **−15,96 dBFS** en 34–35 s y vuelve a apagarse a partir de 40 s.

**Veredicto.** `CONTINUATION` **sí**, y es literalmente el mismo camino que el inpaint con la región al final. **Limitación honesta de esta evidencia:** la costura cayó justo donde la pista base ya había hecho fade-out, así que **este experimento no demuestra continuidad musical a través de un empalme «en caliente»**. Para C-07 hay que repetirlo con una fuente que no termine — cuesta una generación, no una tarea.

### 3.3 `AUDIO_TO_AUDIO` — **Sí, y mucho más pobre de lo que suena**

El camino de cover de upstream (`is_covers = True`) **no** le pasa al modelo el audio original: le pasa el resultado de **tokenizarlo y destokenizarlo** (`prepare_condition`, líneas 1639–1646). La sonda ejercitó exactamente esa cadena sobre los pesos reales.

**El tokenizador (P6).** Cuantizador FSQ de niveles `[8,8,8,5,5,5]`, **1 codebook**:

| Medida | Valor |
|---|---|
| Latente de 750 tramas (30 s) → | `[1, 150, 2048]` cuantizado, `[1, 150, 1]` índices |
| Tasa | **5 Hz** (5 fotogramas latentes por token) |
| Índices | 16 … 63.811, **138 distintos** de 150 posibles |
| Espacio de códigos | 8·8·8·5·5·5 = **64.000** ⇒ 15,97 bits/token |
| **Ancho de banda de la fuente** | **≈ 79,8 bit/s** |

Para comparar: el latente que sí describe la pista es de 25 Hz × 64 canales. **La «pista de origen» que ve el modelo en un cover está comprimida unas 300 veces.** Y se nota en la reconstrucción: las pistas destokenizadas frente al latente original dan coseno **0,29755** y correlación de envolvente **0,03322**. No reconstruyen la pista; son un boceto.

**La generación (P7).** Con el prompt cambiado a algo deliberadamente opuesto (*techno industrial agresivo* frente a *balada de piano*), misma semilla, `chunk_masks` todo a `True`, y como control la misma generación sin fuente:

| Comparación | Coseno | Corr. de envolvente |
|---|---|---|
| **Cover** vs pista fuente | **0,45510** | **0,36437** |
| **Control** (sin fuente) vs pista fuente | 0,33930 | **0,02247** |
| Cover vs control | 0,61225 | 0,11882 |

**La fuente sí dirige la salida**: la correlación de envolvente pasa de 0,022 (control, es decir, nada) a 0,364. Es una influencia real y medible, del orden de lo que cabe esperar de 80 bit/s.

**Veredicto.** `AUDIO_TO_AUDIO` **sí** — el camino existe, está entrenado y funciona. Lo que hay que decidir **antes** de gastar las 80 h de C-08 es si «cover» significa *que la máquina se inspire en la estructura de mi pista* (esto lo hace) o *que reinterprete mi grabación* (esto **no** lo hace; para eso haría falta el camino `repaint`/`lego` sobre latentes completos, que es otra cosa y usa el mecanismo de §3.1). Añadir: sin el codificador del VAE no hay entrada de usuario (§4), y el tokenizador **no arranca en fp16** (§6.1).

### 3.4 `VOICE_CONDITIONING` — **Parcial: el camino está vivo; la capacidad, sin demostrar**

**Lo que sí está probado.** El codificador de timbre (48 tensores, entrenados) recibe latentes de audio de referencia y produce **un vector de 2.048 dimensiones** que se empaqueta en la secuencia de atención cruzada:

| Medida (P8) | Valor | Lectura |
|---|---|---|
| coseno(referencia = silencio, referencia = pista base) | **0,21113** | referencias distintas dan embeddings distintos |
| coseno(pista base, la misma pista **invertida en el tiempo**) | 0,83814 | captura sobre todo carácter global, poco orden temporal |
| coseno(referencia de 30 s, referencia de 10 s de la misma pista) | 0,59967 | **la longitud de la referencia importa mucho** |
| formas con 2 referencias empaquetadas | `[1, 2, 2048]` + máscara `[1, 2]` | **admite varias referencias por pista** |
| norma del embedding (silencio / base) | 27,62 / 30,93 | ninguno es degenerado |

**Y cambia la salida (P9).** Misma semilla, mismo prompt, misma letra, mismo contexto; **lo único que cambia es el audio de referencia**:

* De los **125 tokens** de la secuencia de condicionamiento, **cambia exactamente 1** (máx. |Δ| = 6,418). El timbre ocupa el 0,8 % del condicionamiento.
* La pista resultante frente a la base: coseno **0,83396**, correlación de envolvente 0,68127, RMSE 0,62178 — recordando que una repetición exacta daría 1,000 y 0,000. **Es otra toma, claramente influida.**

**Lo que NO está probado, y es lo que C-03/C-04 querrían.** (a) La referencia usada es una pista **generada por el propio modelo**, no una voz real: sin codificador de VAE no hay forma de meter una voz de verdad. (b) Un vector global de 2.048 dimensiones que además sobrevive casi igual a invertir el audio en el tiempo se parece mucho más a un **descriptor de timbre/producción** que a una identidad vocal. (c) No hay ninguna métrica de similitud de locutor aquí, ni escucha.

**Veredicto.** **Parcial**, con la incertidumbre marcada: *el enganche existe, está entrenado y mueve la salida; que sirva para «poner esta voz» está sin verificar*. Para la Fase 3 esto significa que `VOICE_CONDITIONING` **no puede darse por bueno** como base de un rasgo de producto sin repetir la prueba con voces reales una vez exista el codificador; y recordando que la Fase 4 (clonación de voz) sigue en **no-go**.

---

## 4. El bloqueo común: falta el codificador del VAE

**El hecho.** El artefacto tiene `vae.decoder.*` (182 tensores) y **cero** `vae.encoder.*` (comprobado sobre la cabecera del `.safetensors`, 1.177 claves). Fue una decisión consciente de `T-03`: en `text2music` el latente objetivo es un recorte del latente de silencio y el codificador **no interviene** (lo dice el propio `vendor/pipeline/conditioning.py`).

**Por qué afecta a las cuatro capacidades.** Upstream mete cualquier audio del usuario por ahí: `conditioning_target.py` llama a `_encode_audio_to_latents` para toda pista no silenciosa, y `conditioning_embed.py::infer_refer_latent` (blob `ef9e4a57…`) encoda el audio de referencia con `tiled_encode` **dentro de** `with self._load_model_context("vae")`. Sin ese paso: no hay pista que repintar, ni que continuar, ni que versionar, ni voz que referenciar.

**Por qué no es un muro.** Los pesos ya están descargados y verificados en la instantánea local `19671f40…`:

| Dato | Valor |
|---|---|
| Fichero | `…\upstream\19671f40…\vae\diffusion_pytorch_model.safetensors` (sha256 `da17edb6…`) |
| Contenido | 365 tensores: **183 `encoder.*`** + 182 `decoder.*` |
| Salida del codificador | `encoder.conv2.weight_v` = `[128, 2048, 3]` ⇒ 128 canales = **64 de media + 64 de escala**, que es el espacio latente de 64 canales que el DiT consume |
| Tamaño | 168.562.688 B (**160,8 MiB**) en bf16 upstream ⇒ **el mismo tamaño en fp16** (ambos ocupan 2 bytes): el artefacto pasaría de 6,16 a ≈ 6,33 GB, y en VRAM se puede despachar como ya se despacha el decoder |
| Licencia | **MIT**, la misma del resto de ACE-Step (`LICENSE.acestep.mit.txt`, ya archivada) |
| Configuración | `AutoencoderOobleck`, `downsampling_ratios [2,4,4,6,10]` = 1.920 muestras/fotograma, 48 kHz, estéreo |

**Lo que costaría** (estimación orientativa para el planificador, **no** un compromiso): vendorizar `OobleckEncoder` con su cabecera de procedencia, reconstruir el artefacto con 183 tensores más y bf16→fp16 como el resto, y añadir un `tiled_encode` por trozos (el decode ya está troceado por la misma razón de VRAM). **8–16 h**, más el encaje en el adapter. Nada de esto es Fase 1: es Fase 3, y esta matriz existe precisamente para que aparezca en la estimación de C-07/C-08 **antes** de empezarlas.

---

## 5. HeartMuLa — evaluación documental

Fuentes primarias consultadas hoy (2026-09-02), sin ejecutar nada: repositorio oficial `github.com/HeartMuLa/heartlib` en `main` = **`3783bdb8441f2c298b1e64c8651173aac200361c`** (2026-04-10) y las tarjetas de Hugging Face de la familia. Licencia Apache-2.0 y `safetensors` **confirmados** (coherente con `spec.md` §11.1).

**Qué es.** `HeartMuLa-oss-3B` es un **LM autorregresivo** (Llama-3.2-3B vía `torchtune`, con `setup_caches`, máscara causal y `generate_frame`) que predice códigos en paralelo de **HeartCodec**, un codec de 12,5 Hz; el audio sale por *flow matching* + decodificador escalar. El prompt es: `<tag>…</tag>` + **un hueco para un embedding continuo de audio** + letra.

| Capacidad | Veredicto documental | Cita |
|---|---|---|
| `VOICE_CONDITIONING` | **No** | `src/heartlib/pipelines/music_generation.py` (sha256 `cfe716eb…`), líneas 219–221: `ref_audio = inputs.get("ref_audio", None)` / `if ref_audio is not None: raise NotImplementedError("ref_audio is not supported yet.")`. El hueco existe (`muq_embed`, `muq_idx`) pero se rellena con **ceros**. README, sección TODOs: «⏳ Support **reference audio conditioning**…» |
| `AUDIO_TO_AUDIO` | **No** | El envoltorio `HeartCodec` publicado expone **solo** `__init__` y `detokenize` (`modeling_heartcodec.py`, sha256 `3a182358…`). Existe un `ScalarModel.encode` en `models/sq_codec.py`, pero ni el envoltorio lo expone ni hay documentación de que su espacio coincida con los códigos que predice el LM |
| `CONTINUATION` | **No hoy** | La API arranca siempre del prompt de texto; no hay parámetro de prefijo de audio. *Arquitecturalmente* un AR con caché KV admitiría continuación, pero exige (a) audio→códigos del LM y (b) código de inferencia que no existe. Es una hipótesis, no una capacidad |
| `SECTION_INPAINT` | **No** | LM causal sin esquema de relleno enmascarado documentado; el repo no menciona repaint/inpaint/edit en ninguna parte. Solo cabría «regenerar y empalmar», que no es lo mismo |

**Consecuencia para el plan.** HeartMuLa entra en el registry por lo que `evaluation.md` §7 dice que aporta —multilingüe y, sobre todo, **HeartTranscriptor** para alinear letra y audio, que es justo lo que C-07 necesita para saber dónde empieza el estribillo—, **no** como alternativa de inpaint. Si G1-bis lo tumbara, C-07 perdería su herramienta de alineado, no su motor. Y `spec.md` §11.1 marca la ficha de licencia de HeartCodec/HeartTranscriptor (I-13b) como pendiente: la etiqueta Apache-2.0 de las tarjetas está confirmada, la revisión formal sigue siendo de legal.

---

## 6. Hallazgos secundarios (cosas que cuestan dinero si se descubren tarde)

### 6.1 El tokenizador FSQ **no funciona en fp16** — reproducido dos veces

```
RuntimeError: mat1 and mat2 must have the same dtype, but got Float and Half
  … vector_quantize_pytorch/residual_fsq.py:245  quantized_out = self.project_out(quantized_out)
```

Causa: en `vector_quantize_pytorch` 1.31.1 el FSQ promociona a fp32 dentro de un `autocast(enabled=False)` (`force_f32`, `allowed_dtypes=(float32, float64)`) y devuelve fp32, que choca con el `project_out` de fp16 del artefacto. La sonda lo reprodujo a propósito y luego midió el arreglo: **con `modelo.tokenizer.float()` funciona**. Coste: ~200 MiB de fp16 → ~400 MiB en fp32, solo mientras se tokeniza. **Es una línea de código, pero hoy `AUDIO_TO_AUDIO` no arranca sin ella.**

### 6.2 La rama `audio_codes` de `prepare_condition` está rota en upstream

Línea 1640 del modelo vendorizado: `lm_hints_5Hz = self.tokenize.quantizer.get_output_from_indices(audio_codes)`. `self.tokenize` es un **método**, no el submódulo `self.tokenizer`: no tiene `.quantizer`. Comprobado en memoria (`hasattr(modelo.tokenize, "quantizer") == False`). Quien implemente C-08 con códigos precalculados (el atajo obvio para no re-tokenizar en cada variante) se dará de bruces con un `AttributeError`. Arreglo trivial; conviene que esté escrito **antes**.

### 6.3 Un parámetro entrenado que no se usa, y otro declarado que nadie lee

* `dit.encoder.timbre_encoder.special_token` **está en el artefacto** pero su uso está **comentado** en el modelo (línea 1084); el embedding de timbre se toma de la posición 0 de la propia referencia. Verificado empíricamente: poniéndolo a cero, el embedding no cambia **en absoluto** (`max |Δ| = 0,0`).
* `config.timbre_fix_frame = 750` se declara y **no lo lee nadie** en el código del modelo. Los 750 fotogramas (30 s) vienen solo del camino de silencio. Es decir, **la longitud de la referencia no está fijada por arquitectura** — pero sí importa al resultado (coseno 0,600 entre una referencia de 30 s y una de 10 s de la misma pista): quien exponga esto en la UI tiene que fijar la duración de referencia como parámetro, no como detalle.

### 6.4 El arranque en frío sigue mandando

384,2 s y 386,6 s de carga frente a **~13 s** de todas las pruebas de capacidad juntas. Confirma el hallazgo 1 de `T-03`: la lectura tensor a tensor sobre el bind mount domina el arranque en frío. Aquí solo se cita como coste de operación de futuros spikes; el arreglo pertenece a `adapter.py`.

### 6.5 Pista que no es de T-07 pero vale dinero: `extract` está en el vocabulario de tareas del modelo

`acestep/constants.py` (blob `9e6df532…`) declara diez instrucciones de tarea: `text2music`, `repaint`, `cover`, `cover-nofsq`, **`extract`** («Extract the {TRACK_NAME} track from the audio»), `lego`, `complete` y sus variantes por defecto, con **12 nombres de pista** (`vocals`, `drums`, `bass`, `guitar`, `keyboard`, `strings`, `synth`, `fx`, `brass`, `woodwinds`, `percussion`, `backing_vocals`).

Si el checkpoint turbo respondiera a esa instrucción, **ACE-Step haría separación de stems bajo licencia MIT** — justo el agujero que dejó abierto el hallazgo de 2026-08-18 sobre los pesos CC-BY-NC de Demucs (`spec.md` I-13b, que hoy bloquea C-06). **No está probado**: la instrucción existe en el repositorio de inferencia, no hay confirmación de que estos pesos la soporten, y verificarlo exige el codificador del VAE (§4). Coste estimado de la prueba una vez exista el codificador: **una generación**. Recomendación: engancharlo a la tarea que reabra C-06, no crear tarea nueva.

---

## 7. Lectura para la Fase 3

> Recordatorio: **F11 sigue `bloqueada (gate)`** por G3 (`tasks.md` §F11, `improvement-plan.md` §12.2). Este documento aporta el dato que ese gate exige; **no lo abre ni autoriza gasto**.

### 7.1 C-07 — Extender / regenerar secciones (140 h, `T-67`…`T-74`)

**Sigue viable.** El condicionante duro que el ledger puso a `T-70` («si `T-07` no confirmó `SECTION_INPAINT`, se replantea») queda **satisfecho**. Matices que deben entrar en la ejecución:

1. **El «bit-idéntico fuera de la región» de `spec.md` §5.2 no lo da el modelo, lo da el empalme.** Medido: sin empalme, la zona preservada cambia ~19 dB por debajo de la señal; con empalme, 100,0000 % de muestras idénticas. `T-72` debe testear el empalme, no la fe.
2. **La costura audible sigue siendo un problema de audio**, y el criterio sigue siendo de oído. La inyección por paso de upstream ayuda poco (0,7 dB); el crossfade es lo que evita el clic.
3. **Repetir la prueba de continuación con una fuente que no termine** antes de dar por buena la extensión (§3.2).
4. **Codificador del VAE** (§4) y alineado letra-audio (HeartTranscriptor, ya previsto).

### 7.2 C-08 — Cover / remezcla (80 h, `T-75`…`T-79`)

**Sigue viable, con la expectativa recalibrada por escrito.** `AUDIO_TO_AUDIO` está confirmada, así que el condicionante de `T-77` queda satisfecho. Pero el producto que sale de este camino es *«genera una pista nueva guiada por un boceto de ~80 bit/s de la tuya»*. Antes de gastar las 80 h conviene decidir si eso es C-08 o si C-08 era en realidad un caso de §3.1 (repintar/versionar la pista completa manteniendo el audio). **Son dos productos distintos con el mismo nombre.** Nada de esto toca el riesgo real de C-08, que `evaluation.md` §7 ya identifica como **legal**: el gate de titularidad del audio de entrada sigue siendo obligatorio y es independiente de esta matriz.

### 7.3 Trabajo que esta matriz destapa y que hoy no está en ninguna tarea

| Trabajo | Dónde encaja | Estimación **orientativa** |
|---|---|---|
| Vendorizar `OobleckEncoder` + rehacer el artefacto con `vae.encoder.*` + `tiled_encode` | Prerrequisito de C-07 y C-08 | 8–16 h |
| Empalme de onda con crossfade + su test de regresión | Dentro de `T-72` | 3–5 h |
| Arreglo de dtype del tokenizador FSQ (§6.1) y de la rama `audio_codes` (§6.2) | Dentro de C-08 | 1–2 h |
| Repetir la prueba de continuación con fuente sin fade-out | Dentro de `T-70`/`T-71` | 1–2 h |
| Verificar `VOICE_CONDITIONING` con voz real (cuando exista el codificador) | Antes de comprometer nada de C-03 | 2–3 h |

Total orientativo **15–28 h**, todo en Fase 3. **No se incorpora a ninguna estimación aquí**: eso lo hace el `evaluator` cuando F11 se desbloquee, y esta tabla es su entrada.

---

## 8. Evidencia

Todo en `D:\srv\ace-step\out\` (carpeta de material de spikes, política de retención S-11). Los WAV se verificaron **fuera del contenedor** con el módulo `wave`: los nueve son 48.000 Hz, 2 canales, PCM 16 bit, duración exacta.

| Fichero | sha256 | Bytes | Qué demuestra |
|---|---|---|---|
| `t07-01-base.wav` | `e10edc9bb2f05360…` | 5.760.044 | Pista base (30,0000 s). Referencia de todas las comparaciones |
| `t07-01b-base-reproducida.wav` | `e6442e719f80382a…` | 5.760.044 | La misma, en otro proceso: −80,49 dBFS de diferencia (§1.3) |
| `t07-02-inpaint-solo-contexto.wav` | `f56cf69f8e5aa106…` | 5.760.044 | Inpaint con solo `chunk_masks` |
| `t07-03-inpaint-con-inyeccion.wav` | `88c2f2ba0e544d89…` | 5.760.044 | Inpaint con la inyección por paso de upstream |
| `t07-04-inpaint-empalmado.wav` | `35ef8a0b9eaf08b7…` | 5.760.044 | **100,0000 % bit-idéntico fuera de la región** |
| `t07-05-continuacion.wav` | `8b2b932e5056d736…` | 8.640.044 | 30 s → 45,0000 s con cola nueva |
| `t07-06-cover.wav` | `9cbd299de04ac504…` | 5.760.044 | `AUDIO_TO_AUDIO` con pista fuente |
| `t07-07-cover-control.wav` | `666e9785fa40a082…` | 5.760.044 | Control del anterior, **sin** fuente |
| `t07-08-timbre-referencia.wav` | `9cef445b64eb2917…` | 5.760.044 | `VOICE_CONDITIONING` con audio de referencia |
| `t07-matriz-capacidades.json` | `b2a30e53167e6ff9…` | 9.571 | Informe de la corrida 1 (P1–P5 + el fallo de P6) |
| `t07-matriz-capacidades-2.json` | `8e34b185d1e1883f…` | 4.393 | Informe de la corrida 2 (P1′, P6–P9), `codigo_salida: 0` |
| `t07_probe.py` / `t07_probe2.py` | `93b5f2ea…` / `21e51b19…` | 22.891 / 13.280 | Las sondas, tal cual se ejecutaron |
| `t07_run.log` / `t07_run2.log` | `cfc19be4…` / `e28c2726…` | 13.511 / 1.232 | Salida completa de las dos corridas |

**Escucha recomendada** (10 minutos, sin instrumental): `t07-01-base` → `t07-04-inpaint-empalmado` (¿se oye la costura en 15 s y 20 s?) → `t07-05-continuacion` (¿la cola pega con la cabeza?) → `t07-06-cover` **contra** `t07-07-cover-control` (¿se reconoce la fuente?). Nada de esto puntúa en G1; es para calibrar la expectativa antes de decidir sobre C-07 y C-08.

**Reproducir** (Git Bash; `MSYS_NO_PATHCONV=1` es obligatorio):

```bash
MSYS_NO_PATHCONV=1 docker run --rm --gpus all -e ACE_STEP_REQUIRE_GPU=1 \
  -v "D:\srv\ace-step\weights:/weights:ro" \
  -v "D:\srv\ace-step\out:/outputs" \
  -v "<carpeta con las sondas>:/probe:ro" \
  --entrypoint python ace-step-runner:t05 /probe/t07_probe2.py
```

Coste: ~6,5 min de carga + ~1 min de pruebas por corrida, **0 € de cloud**.

---

## 9. Procedencia de las fuentes documentales

Las citas de upstream se descargaron hoy de `raw.githubusercontent.com` a la revisión fijada y **solo se han leído**: no se ha ejecutado ni importado nada de ese código (invariante de `CLAUDE.md`).

**ACE-Step**, `github.com/ace-step/ACE-Step-1.5` @ `ca1e85fe9430179831e6bc6be790c332190a3866` (la misma revisión que ya vendorizó `T-03`), licencia MIT:

| Fichero | blob SHA-1 | Para qué se cita |
|---|---|---|
| `acestep/core/generation/handler/conditioning_masks.py` | `7973c6a4285af2f072506d3673e0edff547d24ac` | Semántica de la máscara (True = generar) |
| `acestep/core/generation/handler/repaint_step_injection.py` | `0db9a3261b76d3456cd44310cb0c7da6a60a3730` | Inyección por paso |
| `acestep/core/generation/handler/repaint_waveform_splice.py` | `802bfb36372de2cf4d5241c4a1f9de1382c8bf40` | Empalme de onda tras el decode |
| `acestep/core/generation/handler/conditioning_embed.py` | `ef9e4a572233ce3646782f8cd397c1ae080e0121` | El audio de referencia pasa por el VAE |
| `acestep/constants.py` | `9e6df5323d7e0a2f43237a63910d55ebbf2b39e8` | Vocabulario de tareas (`repaint`, `cover`, `extract`, `lego`…) |

Tres de esos cinco hashes (`7973c6a4…`, `ef9e4a57…`, `9e6df532…`) **coinciden exactamente** con los que las cabeceras de `vendor/pipeline/*.py` ya habían registrado contra la atestación de la API de GitHub: la descarga de hoy queda cruzada con la de `T-03`.

**HeartMuLa**, `github.com/HeartMuLa/heartlib` @ `3783bdb8441f2c298b1e64c8651173aac200361c`, Apache-2.0: `README.md` (sha256 `630fe964…`), `src/heartlib/pipelines/music_generation.py` (`cfe716eb…`), `src/heartlib/heartcodec/modeling_heartcodec.py` (`3a182358…`). Tarjeta de `HeartMuLa/HeartMuLa-oss-3B` (`ddaa917f…`): Apache-2.0, `safetensors`, 4 shards, `arxiv:2601.10547`.

---

## 10. Enlaces de decisión

Este documento es la entrada de decisión que ya reclaman, por nombre, tres puntos del ledger y del plan:

* `tasks.md` §F11 (cabecera del gate): «la **matriz de capacidades verificadas** de `T-07` debe confirmar `SECTION_INPAINT` y `AUDIO_TO_AUDIO`; si sale vacía, C-07/C-08 se replantean» → **no sale vacía**; ver §0 y §7.
* `tasks.md` `T-70` (C-07) y `T-77` (C-08): la comprobación de capacidad debe hacerse «contra la matriz verificada de `T-07`, no solo contra el descriptor» → los valores a registrar en el descriptor del adapter son los de §0, **con sus matices**, no un booleano suelto.
* `improvement-plan.md` §12.2 y `spec.md` §5.2 C-11: la matriz forma parte del criterio de aceptación del model registry.

**Lo que este documento NO hace:** no marca ninguna tarea en `tasks.md` (lo hace quien orquesta), no desbloquea G3, no autoriza gasto y no toca ningún fichero de `apps/`.

---

## Registro de cambios

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-02 | Primera versión. Cuatro capacidades probadas empíricamente en ACE-Step 1.5 turbo (dos corridas en GPU local, 9 WAV y 2 informes JSON de evidencia) y evaluadas documentalmente en HeartMuLa. Veredicto: `SECTION_INPAINT` sí · `CONTINUATION` sí · `AUDIO_TO_AUDIO` sí pero degradado (~80 bit/s) · `VOICE_CONDITIONING` parcial. Bloqueo común identificado (codificador del VAE ausente del artefacto, presente y con licencia MIT en la instantánea upstream). C-07 y C-08 **no se caen**; se documentan 15–28 h orientativas de trabajo destapado y una pista de alto valor para C-06 (`extract` bajo MIT). | implementer |
