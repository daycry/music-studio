# Planificador de 5 Hz vendorizado — ACE-Step 1.5 (`acestep-5Hz-lm-0.6B`)

El tercer bloque de `vendor/`. En el directorio padre esta la **definicion del modelo** de difusion
y el decoder del VAE; en `vendor/pipeline/` esta el **pipeline de inferencia** `text2music`; aqui
esta el **planificador**: un Qwen3 de 0,6 B que escribe los metadatos de la pieza y despues emite
una secuencia de codigos de audio a 5 Hz que el DiT usa como latente de origen.

Esta aqui, y no se descarga en tiempo de ejecucion, por lo mismo que el resto de `vendor/`:
`CLAUDE.md` prohibe `trust_remote_code` y `auto_map`. El codigo de terceros que se ejecuta tiene
que estar en el repositorio, fijado por hash y revisable en un diff.

## Por que existe este directorio

Hoy el planificador esta **desconectado**. La consecuencia, leida en el codigo y no supuesta:

`vendor/modeling_acestep_v15_turbo.py`, `prepare_condition`, lineas 1635-1646:

```python
if precomputed_lm_hints_25Hz is not None:
    lm_hints_25Hz = precomputed_lm_hints_25Hz[:, :src_latents.shape[1], :]
else:
    if audio_codes is not None:
        lm_hints_5Hz = self.tokenize.quantizer.get_output_from_indices(audio_codes)
    else:
        lm_hints_5Hz, indices, llm_mask = self.tokenize(hidden_states, silence_latent, attention_mask)
    lm_hints_25Hz = self.detokenize(lm_hints_5Hz)
    lm_hints_25Hz = lm_hints_25Hz[:, :src_latents.shape[1], :]
src_latents = torch.where(is_covers.unsqueeze(-1).unsqueeze(-1) > 0, lm_hints_25Hz, src_latents)
```

Sin planificador no hay `audio_codes`, `src_latents` es el **latente de silencio** y el DiT compone
a ciegas. Con planificador, compone sobre un boceto de 5 Hz. Medir esa diferencia es el objetivo.

Y upstream lo activa **por defecto justo en nuestra tarjeta**: `acestep/gpu_config.py`, `tier3`
(6-8 GB) trae `init_lm_default: True`, `available_lm_models: ["acestep-5Hz-lm-0.6B"]`,
`max_duration_with_lm: 480`. `tier1` y `tier2` lo traen en `False`: es especifico de 6-8 GB.

### Correccion a la nota de encargo: el sentido de `is_covers` esta al reves

El encargo de esta tarea describia la linea como
`torch.where(is_covers == 0, lm_hints_25Hz, src_latents)` — «cuando NO es un cover, el modelo
sustituye los latentes de origen por los hints». **La condicion real es la contraria**: los hints
entran cuando `is_covers` es CIERTO (`> 0`), tal como se lee arriba y como esta ya anotado en
`vendor/pipeline/conditioning.py` lineas 449-457.

La conclusion del encargo sigue siendo correcta, pero por otro camino. Lo que hace que los hints
entren en una generacion normal es que **upstream marca el elemento como cover en cuanto hay
codigos**, en `acestep/core/generation/handler/conditioning_masks.py` linea 70:

```python
is_cover = (task_type == "cover") or has_code_hint
```

Es decir: `is_covers` no significa «el usuario ha pedido una version»; significa «el latente de
origen viene de fuera del ruido». Ademas, `conditioning_target.py` linea 79 mete esos mismos hints
como `target_latents`, asi que `src_latents` y `lm_hints_25Hz` acaban siendo lo mismo.

**Consecuencia operativa, y es la parte que se puede hacer mal sin que nada falle:** no basta con
pasar los codigos. Hay que poner `is_covers = True`. Con `is_covers = False` el `torch.where`
descarta los hints y el DiT sigue componiendo sobre el latente de silencio: mismo audio, sin error,
sin aviso y sin diferencia en el log.

## La decodificacion restringida no es un extra

Un codigo de 5 Hz son 0,2 s de audio. Si el LM decide cuantos emite, la duracion pedida deja de ser
un contrato y el `+-5 %` de la spec se rompe de raiz. `decodificacion_restringida.py` impone dos
cosas en la fase de codigos:

1. **Lista blanca de vocabulario.** Solo los 64.000 tokens `<|audio_code_N|>` con `N <= 63999`, mas
   el EOS. El vocabulario del tokenizador tiene **65.535** de esos tokens: los 1.535 sobrantes
   existen, el modelo puede emitirlos y `quantizer.get_output_from_indices` los indexaria fuera del
   libro de codigos FSQ (`8*8*8*5*5*5 = 64000`). Ademas se bloquean los 153.204 tokens de texto,
   que si no compiten por la masa de probabilidad.
2. **Contador de duracion.** Mientras `codigos_emitidos < int(duracion * 5)` el EOS esta a `-inf`;
   al alcanzarlo, el EOS es el **unico** token permitido. No es una parada blanda: es una igualdad,
   y `planificador.py` la comprueba antes de devolver el plan.

En la fase de razonamiento el mismo automata fuerza la forma del bloque `<think>` campo a campo
(bpm 30-300, duracion 10-600 —o 10-480 si se aplica el tope de `tier3` con
`fijar_duracion_maxima(480)`—, una de 70 tonalidades, uno de 51 idiomas, compas 2/3/4/6).

Efecto secundario de la aritmetica: el LM solo puede expresar duraciones **multiplo de 0,2 s**. Una
peticion de 25,5 s sale como 25,4 s (127 codigos), un 0,39 % de error. Muy dentro del +-5 %, pero
conviene saberlo antes de perseguir el fantasma.

## Alcance: que se trae y que no

**Traido:** construccion del prompt (fases de razonamiento y de codigos, condicional e
incondicional), decodificacion restringida completa, bucle de generacion con y sin CFG, orquestacion
en dos fases, lectura de la salida y conversion `codigos -> lm_hints_25Hz`.

**NO traido, a proposito:** el campo `genres` (vocabulario, trie y recarga en caliente del fichero
—~500 lineas y una lectura de disco en tiempo de construccion—, que upstream ademas desactiva
siempre desde `generate_with_stop_condition`), la fase `understand` (audio -> metadatos + letra),
`inspiration` y `format`, el lote (`batch_size > 1`), `infer_type="dit"`, las rutas vLLM /
nano-vllm / MLX, la descarga de pesos desde el hub, el catalogo de modelos por nivel de GPU, la
gestion de descarga a CPU por presion de VRAM y el interruptor A/B `use_legacy_cfg_prompt`. Cada
exclusion esta justificada en el docstring del modulo correspondiente.

## Procedencia

Dos origenes distintos, y no son intercambiables.

### Codigo

| Campo | Valor |
|---|---|
| Repositorio de codigo | `github.com/ace-step/ACE-Step-1.5` |
| **Revision fijada** | **`ca1e85fe9430179831e6bc6be790c332190a3866`** (2026-08-29) |
| Licencia | **MIT** — `LICENSE` de la raiz de GitHub, blob SHA-1 `600451d484a555c1273baa2602f32a37fdd0d0ab` (1.064 bytes), «Copyright (c) 2026 ACEStep». Copia en `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt` |
| Copiado el | 2026-09-02 |

Es la misma revision que ya fija `vendor/pipeline/README.md`, y a fecha de hoy sigue siendo `HEAD`
de `main` (comprobado contra la API de GitHub).

Todos los `blob SHA-1` estan **verificados contra la atestacion de la API de GitHub** para esa ruta
en ese commit: se recalculo `sha1("blob <n>\0" + contenido)` sobre los bytes descargados y se
comparo con el `sha` del arbol. Los cuatro coinciden.

| Fichero de upstream | Bytes | SHA-256 | blob SHA-1 |
|---|---|---|---|
| `acestep/constants.py` | 8333 | `7b8d4ce49649c819d1b3be87a434be2d90768308768d4620639328f906209b22` | `9e6df5323d7e0a2f43237a63910d55ebbf2b39e8` |
| `acestep/constrained_logits_processor.py` | 114461 | `84cf84ad894130397ba53a4cbd8666961bf578c77295b79599b288a3825faa32` | `69eeffb56ebb4c1e54b106f25f237ba0fbf6b2ae` |
| `acestep/llm_inference.py` | 192383 | `afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6` | `3690af56d8fe5c6a51844917e8e56c54fc088953` |
| `acestep/core/generation/handler/audio_codes.py` | 4456 | `7dec268778c6c6d493aafc8253ae1374bff43459bbd62fb3c16fcd47fefb747a` | `31d6835c9b79104a8ebae0425d9b9055f75c37b1` |

Consultados para entender el cableado, pero **sin derivar codigo de ellos** (van aqui porque las
afirmaciones de este README dependen de su contenido):

| Fichero de upstream | Bytes | SHA-256 | blob SHA-1 |
|---|---|---|---|
| `acestep/gpu_config.py` | 62678 | `01987e28eef138fa27191adcfb1ee46ff2bf96540eafca8887d5243599bf549a` | `554529fa3e1e8b7d5bcd191c08050b416539d2d9` |
| `acestep/core/generation/handler/conditioning_masks.py` | 4738 | `5d9c1fdb249931794af76db83166347be0e8a081f958338c9a7963131e87a365` | `7973c6a4285af2f072506d3673e0edff547d24ac` |

> **Aviso sobre la copia previa de `D:\srv\ace-step\out\hyp4\acestep\`.** Esos cinco ficheros
> **no** casan con la atestacion: tienen finales de linea CRLF y por tanto un byte de mas por linea
> (`constants.py` 8.551 en vez de 8.333, `constrained_logits_processor.py` 116.800 en vez de
> 114.461, `llm_inference.py` 196.636 en vez de 192.383, `gpu_config.py` 64.266 en vez de 62.678).
> Se comprobo que son **identicos tras normalizar los finales de linea**, asi que el contenido es
> el bueno; pero el codigo de este directorio deriva de la copia con LF del tarball del commit, que
> es la que se puede verificar contra el hash del publicador.

### Pesos

| Campo | Valor |
|---|---|
| Repositorio de pesos | `ACE-Step/acestep-5Hz-lm-0.6B` (huggingface.co) |
| **Revision fijada** | **`148d8ea0225bdab342ee1ae3a354275ccd60ca80`** |
| Licencia | **MIT** declarada en el frontmatter del `README.md` del modelo (`license: mit`) y en las etiquetas del repositorio. **El repositorio NO publica fichero `LICENSE`** (HTTP 404), igual que el del DiT; la evidencia utilizable es la MIT de GitHub ya citada |
| `gated` / `private` | `false` / `false` |
| Arquitectura | `Qwen3ForCausalLM`, 662.884.352 parametros, BF16, vocabulario 217.204 |
| Descargado en | `D:\srv\ace-step\upstream\lm-0.6B-148d8ea0\` |
| Total | 1.372.702.240 bytes (1,373 GB) |

Los 11 ficheros se verificaron **uno a uno contra la atestacion de la API de HuggingFace** para esa
revision: `lfs.oid` (que es un SHA-256) para los tres ficheros LFS, blob SHA-1 de git para los
ocho restantes. Los 11 coinciden, y el tamano tambien.

| Fichero | Bytes | SHA-256 | Atestacion usada |
|---|---|---|---|
| `model.safetensors` | 1325804024 | `5d92a60806e2e88c04de58ddc6dde93f2bc8f1336162b3ad5853886c9bcc6b82` | `lfs.oid` |
| `tokenizer.json` | 24321939 | `35af56c3f5cb3ea2cc578aa28a8937770981d504f183ac5c8c38baf4bbd4af4d` | `lfs.oid` |
| `tokenizer_config.json` | 14072925 | `6cd70cdd89425971794f5235562edcc608b0629a6c4686ae51a8b8c8b8ba5e95` | `lfs.oid` |
| `vocab.json` | 2776833 | `ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910` | blob SHA-1 `4783fe10ac3adce15ac8f358ef5462739852c569` |
| `added_tokens.json` | 2217787 | `db08b66a515fb5d6acca0b3492d25bb44e0deda6241fc1113ac0679d40558c48` | blob SHA-1 `584075018edeacd6dcc031b3e2cbbf90836eba41` |
| `merges.txt` | 1671853 | `8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5` | blob SHA-1 `31349551d90c7606f325fe0f11bbb8bd5fa0d7c7` |
| `special_tokens_map.json` | 1824199 | `76e233bfc357b0b03d7b6e6ba8e799244f358552575a7cdadb78d3d19106b298` | blob SHA-1 `aa26266349a0f38be608e07138c9047356309551` |
| `config.json` | 1386 | `873ca63808b74e1e008ab950114765553b898b489b9e077e80db83348a118384` | blob SHA-1 `6353b68df0e93bfec5764e42ede605552ec54116` |
| `chat_template.jinja` | 4168 | `a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8` | blob SHA-1 `01be9b307daa2d425f7c168c9fb145a286e0afb4` |
| `README.md` | 5498 | `ed42093e8f7903f23bd45ea56bea8f484c8aee47820ae8880d6da752681a1da7` | blob SHA-1 `09b1e911e95bb4543e08bfa19ad93bf53e2bc05f` |
| `.gitattributes` | 1628 | `deeeb9e4ddcc13c09872c2e1768bb9bbfa752c00ec1a3d233ab056bed4365048` | blob SHA-1 `744ea4af9d05a1d2de292e5b0d3eae6441c064dc` |

Ni `config.json` ni `tokenizer_config.json` declaran `auto_map`, y no hay ningun `.py` en el
repositorio de pesos: la carga no ejecuta codigo de terceros. `planificador.py` lo **comprueba**
antes de cargar en vez de darlo por hecho.

## Ficheros de este directorio y hashes

| Fichero | Bytes | SHA-256 | Deriva de |
|---|---|---|---|
| `__init__.py` | 4465 | `5dad3106f38f6b12acc3eed40de44257926c0216f5e30b33133669532f68f546` | nada (fachada nuestra, imports perezosos) |
| `constants.py` | 9422 | `923bd312dbaec39ca3d72b4d72fab51b92ea1654612f2e7e4d1a6f6507641645` | `acestep/constants.py` |
| `decodificacion_restringida.py` | 43128 | `6fee271115b025da91ffb7462eab4e5569d6409aa819fa9912de0561dd900388` | `constrained_logits_processor.py` |
| `prompt.py` | 10389 | `9a5ec77ca1f0c3999b080f1026f039cd1f2ad80329ac7bec76d04e1a0faae824` | `llm_inference.py` (construccion de prompts y lectura de salida) |
| `generacion.py` | 14837 | `3bd8dc089eb3750da330ea355b4e84f20f2586e1934eca9c6bd6ac3fe7580fc3` | `llm_inference.py` (bucles de muestreo) |
| `planificador.py` | 22697 | `e50ac24c8a5a07ac6de37e8be5a08fd8d4686913afa97ab25ba662aabfd541f9` | `llm_inference.py` (dos fases) + `audio_codes.py` |

Total 104.938 bytes, todos con finales de linea LF.

## Marcado de modificaciones

La licencia MIT lo exige y ademas hace el diff auditable. Cada cambio respecto a upstream lleva un
comentario `MODIFICADO respecto a upstream: que y por que` en el punto exacto del codigo; lo que no
procede de upstream lleva `ANADIDO (no procede de upstream)`. Los ficheros origen **no** llevan
cabecera de copyright propia (a diferencia del fichero del modelo, que es Apache-2.0): aplica la
MIT del repositorio, reproducida en la cabecera de cada modulo.

Resumen, para no tener que leer los seis ficheros:

| Modulo | Modificaciones |
|---|---|
| `constants.py` | solo las constantes del LM (las del DiT/VAE ya estan en `pipeline/constants.py`, sin solapamiento); `VALID_KEYSCALES` por comprension en vez de tres bucles sueltos que dejan `note`/`acc`/`mode` como variables publicas del modulo; siete numeros magicos con nombre (`CODIGOS_POR_SEGUNDO`, `VENTANA_AGRUPACION`, `TAMANO_LIBRO_CODIGOS`, `MAX_AUDIO_CODE`, `MAX_TOKENS_CAPTION`, `MARGEN_TOKENS_*`) que upstream repite como literales en tres ficheros |
| `decodificacion_restringida.py` | fuera el campo `genres` completo, la fase `understand`, `diagnose_keyscale_prefix_tree`, `_should_end_numeric_field`, `_get_allowed_digit_tokens`, `_should_end_text_field` (codigo muerto) y la herencia de `transformers...LogitsProcessor`; los tokens de codigo se descubren con `get_vocab()` (un dict) en vez de 217.204 llamadas a `decode`, lo que de paso deja construida la biyeccion codigo<->token; **se aborta** si el vocabulario no tiene exactamente 64.000 codigos validos (upstream solo avisa); memo de `_tokens_de_cadena_fija`; sin `loguru` ni el log por token; cuando el arbol de prefijos no ofrece continuacion en BPM/duracion/compas se cierra el campo con un salto de linea en vez de poner **todo** el vocabulario a `-inf` (upstream deja ahi un `multinomial` sobre una distribucion vacia) |
| `prompt.py` | fuera `use_legacy_cfg_prompt` y los prompts de `understand`/`inspiration`/`format`; `timesignature` se normaliza a texto antes de mirar el sufijo `/4` (upstream revienta con `AttributeError` si llega como entero, que es como sale de un `--compas 4`) |
| `generacion.py` | callback `on_token(paso, total)` en lugar de `tqdm`, que es el punto de control de **D-17**; sin `streamer`; sin vLLM/nano-vllm/MLX; la penalizacion de repeticion se importa solo si se pide (con el valor por defecto 1,0 no se toca `transformers.generation`); los bucles devuelven **solo los tokens nuevos** en vez de la secuencia entera mas la aritmetica de longitudes del prompt |
| `planificador.py` | sin lote, sin `infer_type="dit"`, sin descarga desde el hub; `Qwen3ForCausalLM` importado por nombre con `use_safetensors=True` en vez de `AutoModelForCausalLM(trust_remote_code=True)`, y comprobacion explicita de que no hay `auto_map`; `tiene_metas_suficientes` exige **valor** y no solo presencia de la clave (upstream se salta el razonamiento con `{"bpm": None, ...}`); semilla explicita para poder comparar dos versiones del pipeline; **se comprueba** que el numero de codigos es exactamente el pedido antes de devolver el plan |

## Dependencias

Todas estan en la imagen (`transformers 5.16.1`, `tokenizers 0.23.1`, `safetensors 0.8.0`, `torch
2.13.0+cu126`, `numpy 2.4.6`). Este paquete **no** usa `einops`, `vector-quantize-pytorch`,
`diffusers`, `loguru` (no esta) ni `tqdm`.

**Un hueco, y conviene cerrarlo:** `prompt.py` importa `yaml` (PyYAML 6.0.3), que esta en la imagen
pero llega de forma **transitiva** por `huggingface-hub`, no por un pin del `Dockerfile`. Se usa a
proposito en vez de reimplementarlo: `yaml.dump(..., sort_keys=True, allow_unicode=True)` pliega los
captions largos en lineas de continuacion indentadas de 80 columnas, y ese plegado **forma parte del
formato que vio el modelo al entrenarse** (se observa en la verificacion de abajo, bloque `d`).
Reimplementarlo a mano produciria un prompt distinto sin que nada fallase. **Recomendacion: anadir
`pyyaml==6.0.3` a la lista de pines del `Dockerfile`**, por el mismo motivo por el que ya estan
fijados `safetensors`, `tokenizers` y `huggingface-hub`.

## Estado de revision — lease antes de confiar

**Estos ficheros NO han pasado todavia una revision de seguridad linea a linea.** Vale exactamente
lo mismo que se dice en `vendor/README.md` y en `vendor/pipeline/README.md`: vendorizarlos no los
vuelve seguros, los vuelve *inmutables y auditables*, que es un requisito previo distinto y
necesario.

Lo que si esta garantizado hoy:

- No se resuelven por `trust_remote_code` ni `auto_map`: se importan desde esta ruta, y
  `planificador.py` **aborta** si el checkpoint declara `auto_map`.
- Estan fijados por hash, asi que cualquier cambio aparece en un diff.
- No se descargan en tiempo de ejecucion ni en el arranque del contenedor.
- No hay `pickle`, `torch.load`, `eval`, `exec`, `compile`, `__import__`, red (`urllib`,
  `requests`, `socket`, `http`, `ftplib`), `subprocess` ni `shutil`. Esto **si** esta comprobado de
  forma mecanica: se recorre el **arbol sintactico** de los seis modulos, no el texto (un `grep`
  daria falsos positivos con las propias notas de modificacion, que citan `trust_remote_code=True`
  para explicar por que no se usa). Bloque 19 de la verificacion.
- El paquete **no lee del disco al importarse ni al construir el procesador**: se quito la carga
  de `genres_vocab.txt` de upstream. El unico acceso a disco es la carga explicita del checkpoint
  en `PlanificadorLM.cargar`.

Lo que falta, y es trabajo de `T-03` (el mismo criterio de aceptacion que cubre `vendor/`):

- Revision escrita con alcance y criterios, buscando en particular ejecucion en tiempo de
  importacion, red, escritura en disco y `eval`/`exec`.
- Criterio de aceptacion que exija un diff contra los hashes de arriba en cada reconstruccion.

## Verificacion ejecutada (2026-09-02, **sin GPU**)

Todo lo de abajo se **ejecuto** dentro de `ace-step-runner:t05` con `docker run` **sin `--gpus`**
(`torch.cuda.is_available() == False`), con los pesos del LM montados en `/lm:ro` y el artefacto del
DiT en `/weights:ro`. No son estimaciones. Ningun contenedor toco la GPU.

### 1) Importacion y logica pura — 20 bloques, `FALLOS: ninguno`

- `import vendor.lm` (paquete de espacio de nombres) e `import lm` con `vendor/` en `sys.path` (la
  forma que usara el shim). Las dos funcionan.
- Los **34** nombres publicos de `__all__` se resuelven por el `__getattr__` perezoso.
- Constantes coherentes con el `config.json` del DiT: `pool_window_size = 5`,
  `8*8*8*5*5*5 = 64000`, `audio_acoustic_hidden_dim = 64`. 70 tonalidades, 51 idiomas.
- `VALID_KEYSCALES` identico al triple bucle de upstream; `CAMPOS_COT` en orden alfabetico (que es
  el que produce `yaml.dump(sort_keys=True)`: coincidencia comprobada, no supuesta).
- Tokenizador: `Qwen2Tokenizer`, `len = 217.204`, `eos = 151645`, sin `auto_map` en ningun JSON.
- `ProcesadorRestringido` se construye en **0,5 s**. Lista blanca de **64.001** tokens
  (64.000 codigos + EOS); **1.535** tokens `<|audio_code_N|>` con `N >= 64000` quedan excluidos.
  Arboles de prefijos: tonalidad 106 prefijos (**70 de 70** tonalidades con camino completo), BPM
  302, duracion 602, compas 6, idioma 53.
- **El contrato de duracion, medido:** con objetivo de 30 codigos, en los codigos 1..30 el EOS esta
  a `-inf` y quedan exactamente 64.000 candidatos finitos; en el codigo 31 el **unico** token
  finito es el EOS.
- **El contraejemplo:** con `duracion_objetivo = None` el EOS esta disponible desde el primer
  codigo, es decir, la longitud la elige el modelo.
- Prompts: turno de asistente abierto, `</think>\n\n` antes del primer codigo, prompt incondicional
  con `NO USER INPUT` crudo y `<think>\n\n</think>`.
- `parsear_salida` reconstruye los seis campos y aplana el caption multilinea.

### 2) Rango dinamico de los pesos (BF16 -> FP16 o FP32)

Recorriendo los 662.884.352 valores del `model.safetensors` con `safetensors` (sin `pickle`, sin
`torch.load`), 189 s:

| Medida | Valor |
|---|---|
| `max |w|` | **99,5** (`model.layers.0.self_attn.k_norm.weight`) |
| `min |w|` no nulo | 8,09e-11 |
| Valores por encima del maximo de FP16 (65.504) | **0** |
| Valores que se irian a cero en FP16 (< 6e-8) | 508 de 662.884.352 (7,7e-7) |

**Los pesos caben en FP16 con holgura de casi tres ordenes de magnitud.** Esto NO es permiso para
convertir sin mas: lo que nos mordio en `encoder.lyric_encoder` fue el rango de las **activaciones**,
no el de los pesos, y eso solo se puede medir ejecutando. Pero descarta el riesgo obvio y deja la
decision documentada: FP32 en CPU es lo que hay implementado por defecto; FP16 en GPU es viable
desde el punto de vista de los pesos y habria que medir activaciones antes.

### 3) Planificador de punta a punta, CPU, FP32, 10 hilos — `TODO OK`

Carga del modelo: 62,4 s. 662.884.352 parametros, `torch.float32`, dispositivo `cpu`.

| Bloque | Duracion pedida | Codigos | Esperados | fase 1 | fase 2 |
|---|---|---|---|---|---|
| a) metas dadas (sin fase 1), CFG 2,0 | 6 s | **30** | 30 | 0,00 s | 31,5 s (en frio) |
| b) idem con la misma semilla | 6 s | **30** | 30 | 0,00 s | 12,1 s |
| c) sin CFG (escala 1,0) | 6 s | **30** | 30 | 0,00 s | 12,2 s |
| d) fase 1 + fase 2 | 8 s | **40** | 40 | 17,7 s | 14,5 s |
| e) fase 1 + fase 2 | 12 s | **60** | 60 | 18,3 s | 18,0 s |

- **(b) reproduce (a) codigo a codigo** con la misma semilla.
- **(c) difiere de (a) en 23 de 30 posiciones**: el CFG no es decorativo.
- **(d)** el LM escribio los seis campos y **los seis respetan su vocabulario cerrado**
  (`bpm: 33`, `keyscale: G major`, `language: unknown`, `timesignature: 4`, duracion exacta 8). El
  caption salio plegado por YAML en lineas de continuacion indentadas, que es justo el formato que
  el automata sabe leer:

  ```
  caption: A brief musical statement featuring a clean, warm electric piano playing
    a gentle, jazzy chord progression. A subtle bass guitar underpins the harmony with
    a simple root-note pattern. ...
  ```

- **(f)** una excepcion levantada desde `on_token` **aborta el bucle y se propaga**, que es como el
  adapter aplicara el tope de segundos (**D-17**).

### 4) Codigos de 5 Hz -> `lm_hints_25Hz`, con los pesos **reales** del artefacto

Se construyeron el cuantizador FSQ (`ResidualFSQ(dim=2048, levels=[8,8,8,5,5,5], nq=1)`) y el
`AudioTokenDetokenizer`, y se cargaron **32 de los 1.177 tensores** del artefacto
(`dit.tokenizer.quantizer.*` 4 y `dit.detokenizer.*` 28) con `strict=False`: **0 claves
inesperadas y 0 claves faltantes**. Despues se llamo a `lm.hints_25Hz` tal cual.

| Duracion | Codigos | Planificacion (CFG 2,0) | `indices` | `quantized` | `hints_25Hz` | rms | finito |
|---|---|---|---|---|---|---|---|
| 6 s | 30 | 12,4 s (413 ms/codigo) | `(1, 30, 1)` int64 | `(1, 30, 2048)` | **`(1, 150, 64)`** en 0,42 s | 1,3068 | si |
| 30 s | 150 | 42,8 s (285 ms/codigo) | `(1, 150, 1)` int64 | `(1, 150, 2048)` | **`(1, 750, 64)`** en 0,79 s | 1,3222 | si |

750 fotogramas a 25 Hz son exactamente 30,0 s, que es lo que se pidio. La cadena
`5 Hz -> x5 -> 25 Hz -> x1920 -> 48 kHz` cuadra de punta a punta.

Y la comparacion que da sentido a todo esto — **los hints no se parecen al latente de silencio**,
que es lo que el DiT recibe hoy:

| Tensor | Forma | rms | min | max |
|---|---|---|---|---|
| `aux.silence_latent` (lo que ve el DiT hoy) | `(1, 64, 15000)` | 0,9843 | **-6,727** | **+1,621** |
| `lm_hints_25Hz` de una pista de 30 s | `(1, 750, 64)` | 1,3222 | -5,825 | **+6,746** |

El latente de silencio es un punto degenerado y **asimetrico** (su maximo es +1,62); los hints del
planificador ocupan un rango simetrico y mas ancho. Son distribuciones distintas, no dos versiones
de lo mismo.

### Coste, y es una cifra incomoda

285 ms por codigo en CPU FP32 con CFG 2,0 extrapola a **~4,3 minutos para una pista de 180 s** (900
codigos) y ~43 s para una de 30 s. La difusion medida en T-03 son 23 s por pista. Es decir: en CPU,
**el planificador costaria varias veces mas que la generacion entera**. Las opciones, sin recomendar
ninguna aqui porque la decision es del shim:

- Pistas cortas (25-30 s), que es lo que pide el protocolo de escucha de G1: +43 s por pista.
- El LM en la GPU en FP16 (1,33 GB): no cabe a la vez que el artefacto (hoy 6,16 GB sobre ~6.988
  MiB libres, 810 MiB de holgura), asi que exigiria cargarlo **antes** que el DiT y liberarlo, o
  cargar el artefacto a CPU y que el shim coloque cada componente consumiendo el diccionario con
  `pop`.
- Aceptar el coste en CPU y medir la calidad primero, que es lo que la tarea pide decidir.

## Estado del cableado (actualizado el 2026-09-02)

Las tres precondiciones que este README dejaba abiertas estan **resueltas**. Se documentan aqui
con lo que se midio al cerrarlas, porque cada una escondia algo que no se veia desde este paquete.

- **El cableado con el shim: HECHO.** `ace_step_shim.py` monta la cadena en
  `PipelineAceStep._planificar` y la sustitucion ocurre en
  `vendor/pipeline/conditioning.py`, que acepta un argumento `lm_hints_25Hz`. No se propaga
  ninguna bandera `is_covers`: con B=1 ese `torch.where` es una eleccion entre dos tensores
  completos, asi que el codigo dice lo que hace — si hay plan, `src_latents` ES el plan. La
  longitud sale de los codigos (`ceil(tramas/5)` codigos, luego se recorta a `tramas`), no de dos
  fuentes de verdad. La perilla es `model_params["usar_lm"]`.
- **La colocacion de los pesos: HECHO, por la via del `device="cpu"`.** `adapter.py` mapea ahora el
  artefacto en CPU y el shim coloca y **materializa** cada componente. Se descarto el fichero
  aparte porque rompia el «un solo artefacto» y dejaba intactos los 810 MiB de holgura, que eran el
  problema de fondo. El LM viaja dentro del artefacto (`lm.*`, 310 tensores) junto con **cinco**
  blobs `aux.lm*`: el quinto, `chat_template.jinja`, resulto ser obligatorio y no estaba —
  `tokenizer_config.json` de esta revision NO lleva `chat_template`, y sin el fichero
  `apply_chat_template` (que es como se construyen TODOS los prompts de `prompt.py`) levanta
  `ValueError`. Comprobado montando los dos directorios: con 4 ficheros falla, con 5 funciona.
- **Los bufferes NO persistentes del FSQ: verificados en su sitio.** `_instanciar_dit` los
  materializa construyendo `ResidualFSQ` en CPU, y se ha comprobado sobre el artefacto real que
  ninguno queda en `meta` y que sus valores no son cero (`_levels` suma 39, `_basis` 15.945,
  `implicit_codebook` -46,875, `scales` 6, `soft_clamp_input_value` 7,178).
- **Y uno que no estaba previsto: el dtype de `quantizer.scales`.** Al usar de verdad la cadena
  aparecio `RuntimeError: mat1 and mat2 must have the same dtype, but got Float and Half`.
  `vector_quantize_pytorch` construye `scales` como `levels_tensor.float() ** -ind` — el `.float()`
  es explicito, o sea fp32 pase lo que pase — mientras que `project_out` lleva los pesos fp16 del
  artefacto. Se corrige con `Module.to(dtype)` sobre `dit.tokenizer` y `dit.detokenizer`, que
  convierte solo los tensores en coma flotante y **deja `_levels` y `_basis` en int32** (en fp16
  `_basis`, que llega a ~10^4, dejaria de ser exacto y corromperia `indices // _basis` en
  silencio). Medido que fp16 basta: la cadena completa en fp16 frente a fp32 da
  `max|diff| = 0,0031` sobre un `|max|` de 5,77 (0,053 %) y correlacion 0,99999946.

## Que NO esta aqui

- **La medida de calidad.** Este directorio permite hacer el experimento; no lo hace.
