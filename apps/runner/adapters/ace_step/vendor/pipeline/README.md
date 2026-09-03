# Pipeline de inferencia vendorizado — ACE-Step 1.5 turbo, `text2music`

La otra mitad de `vendor/`. En el directorio padre esta la **definicion del modelo**
(`modeling_acestep_v15_turbo.py`, `configuration_acestep_v15.py`) y el **decoder del VAE**
(`oobleck_decoder.py`); aqui esta el **pipeline de inferencia**: preparacion del
condicionamiento, programacion de pasos de tiempo, bucle de difusion Euler ODE y el puente hacia
el decoder.

Esta aqui, y no se descarga en tiempo de ejecucion, por lo mismo que el resto de `vendor/`:
`CLAUDE.md` prohibe `trust_remote_code` y `auto_map`. El codigo de terceros que se ejecuta tiene
que estar en el repositorio, fijado por hash y revisable en un diff.

## Alcance: solo `text2music` del turbo

Traido: lote 1, en las dos variantes de pesos.

* `turbo` (produccion): 8 pasos, `shift=3.0`, **sin guia**.
* `sft` (modelo base sin destilar, anadido el 2026-09-02): N pasos (50 por defecto),
  `shift=1.0` y **guia APG** con pasada gemela SECUENCIAL. OJO: verificado el 2026-09-02
  que el `sft` desborda fp16 en la GTX 1070 y no llega a producir audio; el detalle, en
  `../sft/README.md`.

**NO** traido, a proposito: `cover`, `cover-nofsq`, `repaint`, `lego`, `extract`, `complete`,
LoRA, audio2audio, `audio_code_hints`, `precomputed_lm_hints_25Hz`, `flow_edit`, correccion DCW,
muestreador de Heun, recorte de norma de velocidad, EMA de velocidad, `infer_method="sde"`,
caminos MLX/MPS y todo el aparato de descarga por niveles de VRAM de upstream. Cada exclusion
esta justificada en el docstring del modulo correspondiente.

## Procedencia

Dos origenes distintos, y no son intercambiables:

| Campo | Valor |
|---|---|
| Repositorio de codigo | `github.com/ace-step/ACE-Step-1.5` |
| **Revision fijada** | **`ca1e85fe9430179831e6bc6be790c332190a3866`** (2026-08-29) |
| Repositorio de pesos y modelo | `ACE-Step/Ace-Step1.5` (huggingface.co) |
| Revision fijada | `19671f406d603126926c1b7e2adc169acbcade22` |
| Licencia | **MIT** — `LICENSE` de la raiz de GitHub, blob SHA-1 `600451d484a555c1273baa2602f32a37fdd0d0ab` (1.064 bytes), «Copyright (c) 2026 ACEStep». Copia en `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt`. El repo de HuggingFace **no publica `LICENSE`** (HTTP 404) |
| Copiado el | 2026-09-02 |

El **bucle de difusion** sale del `modeling_acestep_v15_turbo.py` ya vendorizado (revision de
HuggingFace), no de la copia de GitHub, porque es la revision que corresponde a **nuestros pesos**.
Comprobado que la tabla `SHIFT_TIMESTEPS` es identica en las dos revisiones, asi que en este punto
concreto no hay deriva; el resto del fichero de GitHub (108.712 bytes) si difiere del nuestro
(96.036 bytes) y por eso no se usa.

### Ficheros de upstream de los que deriva cada modulo

Todos los `blob SHA-1` estan **verificados contra la atestacion de la API de GitHub** para esa
ruta en ese commit: se recalculo `sha1("blob <n>\0" + contenido)` sobre los bytes descargados y se
comparo con el `sha` del arbol. Los 10 coinciden.

| Fichero de upstream | Bytes | SHA-256 | blob SHA-1 |
|---|---|---|---|
| `acestep/constants.py` | 8333 | `7b8d4ce49649c819d1b3be87a434be2d90768308768d4620639328f906209b22` | `9e6df5323d7e0a2f43237a63910d55ebbf2b39e8` |
| `acestep/core/generation/handler/prompt_utils.py` | 6826 | `242835ae29cc1bfcc40aadf1c46d8156230349d6e2f05436b2c85b3491484fae` | `f51a49c622f60b048c96e27aa48292321aeade63` |
| `acestep/core/generation/handler/metadata_utils.py` | 3062 | `b8485fe9c3a8ffdf0ee0147df68366770abfe6b68e6cd286dd4722d9379cdc5b` | `2dee45ea724c80f899ab7aa224473efc4c406844` |
| `acestep/core/generation/handler/task_utils.py` | 5568 | `a5c90c6af54d1eb207cbf79db39535e115361542cb37735ed4359287bd257a66` | `e39b09e16bb6de0cf3f028300df40fa89745923b` |
| `acestep/core/generation/handler/conditioning_batch.py` | 6868 | `5bc46879830c5e35a48e7ef4a18ca41b4c3f30f7887928b31cea3cf259e82958` | `9a4115adfc6c4fb6caa7e8072adb2ad0090197d9` |
| `acestep/core/generation/handler/conditioning_target.py` | 8663 | `472b302837800f54972b5b5a3d6374b7855ee3eac9e05762757fcb41d5455068` | `4446b2897e818c8f3ac55b1b152035a41720a6aa` |
| `acestep/core/generation/handler/conditioning_masks.py` | 4738 | `5d9c1fdb249931794af76db83166347be0e8a081f958338c9a7963131e87a365` | `7973c6a4285af2f072506d3673e0edff547d24ac` |
| `acestep/core/generation/handler/conditioning_text.py` | 9177 | `0313ef5fc5ade1baa5a806f3748e5c853961768d057045e040fcb28a33a153b6` | `5641afdb921d4393aa6f3c842e238a3a8c141543` |
| `acestep/core/generation/handler/conditioning_embed.py` | 6741 | `45e80702219496edcef5712fa8403583c61f0df128833b9657d0d129d035a3f2` | `ef9e4a572233ce3646782f8cd397c1ae080e0121` |
| `acestep/core/generation/handler/generate_music_decode.py` | 10402 | `5ebe4dfd65635a687a5692d37ab377ab959170e764fbedf54d6e35711cc40416` | `b7330503c1c8277cdb72281c14ed6b711be2414c` |

Y, del directorio padre (revision de HuggingFace, hash ya registrado en `vendor/README.md`):

| Fichero | Bytes | SHA-256 | Que se toma |
|---|---|---|---|
| `modeling_acestep_v15_turbo.py` | 96036 | `c1ab0dd547124fee7ada449b2b86eae8201dc7d15889932643bbb67e3c982444` | `generate_audio` (tabla de pasos + bucle Euler) y `prepare_condition` |

## Ficheros de este directorio y hashes

| Fichero | Bytes | SHA-256 | Deriva de |
|---|---|---|---|
| `__init__.py` | 3372 | `a9df70b724d578686a1183b8f9bcf4212827e99a0602147175c06b8414f8cb2f` | nada (fachada nuestra, imports perezosos) |
| `constants.py` | 10240 | `2470ce0af5d0dae7581383996425d4821e9103589f73d2b380b46fec0f137594` | `constants.py`, `prompt_utils.py`, `metadata_utils.py` |
| `scheduler.py` | 21346 | `379bc1e1506b3dc38519b2aad957096d9a04635466aadd116ccaea4a3af191b2` | `generate_audio` del turbo (`VALID_SHIFTS`, `SHIFT_TIMESTEPS`) **y del base** (`linspace` + desplazamiento) |
| `conditioning.py` | 25357 | `6990193812435794d7848d675c33f3d93e18959d783d77bd0abb813725845ef6` | los cinco `conditioning_*.py`, `task_utils.py`, `prepare_condition` — **fila actualizada el 2026-09-03**: el fichero cambio el 2026-09-02 (argumento `lm_hints_25Hz`, commit `555ea42`) y la tabla se quedo con el hash anterior (22269 bytes, `7d9052ef…`) hasta que la revision lo destapo |
| `diffusion.py` | 26100 | `fd4fe9b0b2832d0f89d3d8bcd63f3383694426648e41c71ef33053bc4eaf0ed6` | `generate_audio` (bucle del turbo **y del base, con guia**), `generate_music_decode.py` (validacion). La guia APG **se importa** de `../sft/apg_guidance.py`, no se copia |
| `decode.py` | 7763 | `ba859a2ee185d48caaf80e0a98115ebb1737ebb2db9b0b205c66fdc4083846d4` | `generate_music_decode.py` (transposicion y dtype) |

## El VAE NO esta duplicado aqui

`decode.py` **importa** `../oobleck_decoder.py`, que ya estaba vendorizado y verificado en la GPU
(su hash esta en la tabla de `../README.md`, no aqui).
No hay una segunda implementacion del decoder: dos implementaciones del mismo decoder serian una
deuda, no una red de seguridad. Un intento anterior dejo aqui `vae_oobleck.py` y `vae_decode.py`;
**estan borrados**.

## Marcado de modificaciones

La licencia lo exige (Apache-2.0 §4(b) para el fichero del modelo, que lleva su propia cabecera;
MIT para el resto) y ademas hace el diff auditable. Cada cambio respecto a upstream lleva un
comentario `MODIFICADO respecto a upstream: que y por que` en el punto exacto del codigo. Los
avisos de copyright se reproducen **verbatim**, incluida la errata `ACESTEO` del propio upstream.

Resumen de las modificaciones, para no tener que leer los seis ficheros:

| Modulo | Modificaciones |
|---|---|
| `constants.py` | mixins convertidos en funciones de modulo; cinco numeros magicos con nombre (`SAMPLE_RATE`, `LATENT_HOP`, `LATENT_HZ`, `MIN_LATENT_LENGTH`, `REFER_AUDIO_LATENT_FRAMES`, `MAX_*_TOKENS`); `construir_meta_dict` acepta `None` donde upstream revienta con `AttributeError` |
| `scheduler.py` | el redondeo del `shift` se devuelve al llamante (`programacion_efectiva`) en vez de quedar en un log que nadie lee durante una generacion; la programacion continua del base se calcula en doble y no en el dtype del modelo (el modulo tiene que importarse sin `torch`); `shift<=0` y `pasos` fuera de rango se **rechazan** en vez de clamparse en silencio como hace `GenerationParams` |
| `conditioning.py` | solo la rama trivial de `text2music`; sin lote; se omiten `model.tokenize()`/`detokenize()` (con `is_covers=False` su resultado se descarta, es numericamente irrelevante); `longitud_latente` calcula el entero en vez de materializar 115 MB de ceros; se quita el kwarg `lyric_attention_mask=None` que upstream cuela por `**kwargs` de `Qwen3Model.forward`; el codificador de texto puede vivir en **otro dispositivo** que el DiT (en 8 GB no caben a la vez); `.clone()` de los estados ocultos al salir de `inference_mode` |
| `diffusion.py` | callback `on_step(paso, total)` en cada paso, que es el punto de control de **D-17** y no existe en upstream; el condicionamiento llega ya calculado; sin ramas de cover ni SDE; se valida el latente al salir de la difusion y no mas tarde, en el decode; la pasada gemela de la guia es **secuencial** (dos llamadas de lote 1, dos caches) y no de lote 2, con la medida que lo justifica en el docstring; fuera de `cfg_interval` no se calcula la incondicional en vez de calcularla y tirarla |
| `decode.py` | siempre trocea (el decode monolitico de 180 s no cabe en 8 GB); sin caminos MLX/MPS/CPU; sin `latent_shift`/`latent_rescale` (identidad en sus valores neutros); el decoder llega por argumento en vez de por `self.vae` |

## Estado de revision — lease antes de confiar

**Estos ficheros NO han pasado todavia una revision de seguridad linea a linea.** Vale exactamente
lo mismo que se dice en `vendor/README.md`: vendorizarlos no los vuelve seguros, los vuelve
*inmutables y auditables*, que es un requisito previo distinto y necesario.

Lo que si esta garantizado hoy:

- No se resuelven por `trust_remote_code` ni `auto_map`: se importan desde esta ruta.
- Estan fijados por hash, asi que cualquier cambio aparece en un diff.
- No se descargan en tiempo de ejecucion ni en el arranque del contenedor.
- No hay `pickle`, `torch.load`, `eval`, `exec`, red ni escritura en disco en tiempo de
  importacion. Esto es una lectura del diff, **no** una revision formal.

Lo que falta, y es trabajo de `T-03` (el mismo criterio de aceptacion que cubre `vendor/`):

- Revision escrita con alcance y criterios, buscando en particular ejecucion en tiempo de
  importacion, red, escritura en disco y `eval`/`exec`.
- Criterio de aceptacion que exija un diff contra los hashes de arriba en cada reconstruccion.

## Verificacion ejecutada (2026-09-02, GPU real)

Todo lo de abajo se **ejecuto** dentro de `ace-step-runner:t05` sobre la GTX 1070 (sm_61, 8.192 MiB,
7.202 MiB libres) con el artefacto `D:\srv\ace-step\weights\ace_step_1_5.safetensors`. No son
estimaciones.

**Importacion y logica pura** — 10 bloques, `FALLOS: ninguno`:

- `import vendor.pipeline` (paquete de espacio de nombres) e `import pipeline` con `vendor/` en
  `sys.path` (la forma que usara el shim). Las dos funcionan.
- `decode.py` resuelve `/app/adapters/ace_step/vendor/oobleck_decoder.py`.
- Los 19 nombres publicos de `__all__` se resuelven por el `__getattr__` perezoso.
- La tabla `shift=3.0` coincide con la forma cerrada `s·t/(1+(s-1)·t)` con `t = 1 - i/8` con error
  maximo `< 1e-12`.
- `validar_latentes` detecta NaN y latente identicamente cero.

**`text2music` de punta a punta**, `shift=3.0`, 8 pasos, sin CFG, B=1, fp16:

| Etapa | 30 s | 180 s |
|---|---|---|
| Condicionamiento | 4,3 s | 4,8 s |
| Difusion (8 pasos) | 3,08 s (0,37 s/paso) | **22,54 s (2,67 s/paso)** |
| Pico VRAM en difusion | 4.613 MiB | **5.291 MiB** (modelo 4.567 + activaciones 724) |
| Decode del VAE | 3,5 s | 18,5 s |
| Salida | `(1, 2, 1.440.000)` fp32, 30,0 s @ 48 kHz, rms 0,130 | `(1, 2, 8.640.000)` fp32, 180,0 s @ 48 kHz, rms 0,190 |
| Finito | si | si |

Concuerda con las mediciones previas de `T-03` (2.867 ms por forward del DiT a `L=2250`, 23,05 s
por pista, 18,8 s de decode con pico 1.421,6 MiB). Ademas se comprobo que una excepcion levantada
desde `on_step` **aborta el bucle y se propaga**, que es como el adapter aplica el tope de
segundos de GPU (**D-17**).

Longitudes: 180 s son **4.500** fotogramas latentes a 25 Hz; la atencion del DiT ve `L=2.250`
porque `config.patch_size = 2`. Las dos cifras son correctas y no hay que confundirlas.

### Aviso para quien escriba el shim: `to_empty()` mata RoPE en silencio

Encontrado midiendo, no leyendo. Construir el modelo en `meta`, hacer `to_empty(device=...)` y
`load_state_dict(..., strict=True)` **parece** correcto —`strict=True` no se queja— y sin embargo
deja el modelo roto:

`AceStepConditionGenerationModel` declara **15 buffers NO persistentes** que, por definicion, no
viajan en el `state_dict` y que `to_empty()` deja **sin inicializar**:

```
decoder.rotary_emb.inv_freq / .original_inv_freq
encoder.lyric_encoder.rotary_emb.inv_freq / .original_inv_freq
encoder.timbre_encoder.rotary_emb.inv_freq / .original_inv_freq
tokenizer.attention_pooler.rotary_emb.inv_freq / .original_inv_freq
detokenizer.rotary_emb.inv_freq / .original_inv_freq
tokenizer.quantizer.{scales, soft_clamp_input_value}
tokenizer.quantizer.layers.0.{_levels, _basis, implicit_codebook}
```

`Qwen3Model` (el codificador de texto) tiene el mismo problema con su propio
`rotary_emb.inv_freq`.

Sintomas observados, los dos en la misma configuracion y sin tocar nada:

- con la memoria a cero: `inv_freq = 0` -> `cos = 1`, `sin = 0` -> **RoPE sin informacion de
  posicion**. La generacion termina, no hay NaN, `validar_latentes` pasa, y el audio sale a
  rms 0,00069 (unos -63 dBFS): basura silenciosa.
- con basura en la memoria: `text_hidden_states` sale **todo NaN** y el condicionamiento revienta.

Es decir: **falla de forma no determinista y una de las dos caras no levanta ningun error**. Tras
reinicializar los `inv_freq` de los 5 modulos del DiT y del `Qwen3Model`, el rms pasa de 0,00069 a
0,130 (30 s) y 0,190 (180 s). Los cinco buffers del cuantizador FSQ no afectan a `text2music`
—este pipeline no llama a `tokenize`/`detokenize`— pero seguirian mal.

Este pipeline **no puede** defenderse de eso: recibe el modelo ya instanciado. Es responsabilidad
del shim reinicializar esos buffers despues de `to_empty()`, o construir el modelo por un camino
que no los deje huerfanos.

## Que NO esta aqui

- **El shim** (`ace_step_shim.py`): instanciar el modelo, el codificador de texto, el tokenizador y
  el decoder desde el `state_dict`, fijar `model.config._attn_implementation = "eager"` a mano
  (en sm_61 `set_attn_implementation("eager")` devuelve `"sdpa"` sin avisar y la ruta SDPA va 12,9x
  mas lenta), y convertir la forma de onda al `pcm16` que espera `RenderedAudio`.
- **El post-proceso de audio** (loudness EBU R128, resample, FLAC/MP3): `T-19`/`T-45`.
- **El manifiesto de procedencia**: `T-27`, sobre el esquema que firme legal (D-20).
