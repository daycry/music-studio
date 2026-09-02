# Código upstream vendorizado — ACE-Step 1.5 **sft** (modelo base, sin destilar)

Copia **fijada y verificada** del código del modelo `acestep-v15-sft` publicado por ACE Studio /
StepFun. Mismas razones que en `../README.md`: `CLAUDE.md` prohíbe `trust_remote_code` y `auto_map`,
así que el código de terceros que se ejecuta tiene que estar en el repositorio, fijado por hash y
revisable en un diff, no resolverse contra un hub que puede cambiar bajo nuestros pies.

Este directorio existe para una pregunta concreta: **si la destilación a 8 pasos del turbo se dejó
por el camino el encaje de la voz con el beat**. El `sft` es el mismo entrenamiento SIN destilar —
50 pasos y con guía— así que sirve de control. Es una hipótesis a descartar o confirmar, no una
decisión de cambiar de modelo.

## Procedencia

| Campo | Valor |
|---|---|
| Repositorio | `ACE-Step/acestep-v15-sft` (huggingface.co) |
| Revisión fijada | `c410d249e71ea9385a7b586865e65b1473e1098d` |
| Licencia | **MIT** — declarada en la tarjeta del modelo (`license: mit`). La evidencia archivada es `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt`, del repo de GitHub `ace-step/ACE-Step-1.5`; **no hay un fichero `LICENSE` propio en este repo de HuggingFace**, igual que pasaba con el turbo |
| Copiado el | 2026-09-02 |

## Ficheros y hashes

| Fichero | Bytes | SHA-256 | blob SHA-1 (atestación) |
|---|---|---|---|
| `modeling_acestep_v15_base.py` | 95910 | `5e3b475d46965dcd5b0d037e53a9af359305a7dbd78e2ee08b39e94c4b02ca48` | `3be5113ad1a9bce551c456b8d54073b6c96faac9` |
| `apg_guidance.py` | 7956 | `0c0ce9755952c99307ecad2fac67863d43258e34541cd37ce2f2221f59e76b15` | `0448a3436bb42b0a667a4090087dd688e65229fb` |

Verificados idénticos a la copia upstream de `D:\srv\ace-step\upstream\sft-c410d249\` (`cmp` byte a
byte, 2/2 sin diferencias), que a su vez se verificó contra la atestación del publicador. La columna
`blob SHA-1` es el identificador de git que publica la API de HuggingFace, y es el que aparece en
`.cache/huggingface/download/*.metadata` de la descarga.

**Sin modificaciones locales.** Los ficheros están tal cual se descargaron.

## Qué NO se duplica, y por qué

`configuration_acestep_v15.py` **no se copia aquí**: es byte-idéntico al que ya está vendorizado en
`../configuration_acestep_v15.py`. Comprobado, no supuesto:

- blob SHA-1 del fichero ya vendorizado = `965a1b73afb1c89d0959c7d80691e487fdfde505`, que es
  exactamente el que la atestación del publicador da para `configuration_acestep_v15.py` en la
  revisión `c410d249…` del repo `sft`.
- SHA-256 = `b89870c5c7a7ce060eb0bcdbb5ffc86b0b1a324ca325a26be552ea1b42496dc5` en ambas copias, y
  `cmp` byte a byte sin diferencias.

Es decir: el mismo fichero se publica sin cambios en el repo del turbo y en el del `sft`. Duplicarlo
solo crearía dos hashes que mantener sincronizados.

`config.json` tampoco se copia. El del `sft` **sí difiere** del vendorizado, pero solo en tres
campos, ninguno de ellos arquitectural:

| Campo | turbo | sft | Efecto |
|---|---|---|---|
| `is_turbo` | `true` | `false` | **Ninguno**: `grep` confirma que ni el código upstream ni el nuestro lee jamás ese campo |
| `auto_map` | apunta a `modeling_acestep_v15_turbo` | apunta a `modeling_acestep_v15_base` | Ninguno: `auto_map` está prohibido por `CLAUDE.md` y no se usa |
| `model_version` | presente | ausente | Informativo |

Todos los hiperparámetros de arquitectura son idénticos, lo que es coherente con que ambos modelos
compartan las mismas 677 claves de `state_dict` con las mismas formas.

## Trampa de importación — léase antes de integrar

`modeling_acestep_v15_base.py` resuelve sus dos dependencias locales en **un solo** `try/except`:

```python
try:
    from .configuration_acestep_v15 import AceStepConfig
    from .apg_guidance import adg_forward, apg_forward, MomentumBuffer
except ImportError:
    from configuration_acestep_v15 import AceStepConfig
    from apg_guidance import adg_forward, apg_forward, MomentumBuffer
```

Como aquí **no** hay `configuration_acestep_v15.py`, la primera línea del bloque falla siempre y se
ejecuta el ramal absoluto **entero**. Consecuencia contraintuitiva: la rama relativa `.apg_guidance`
nunca llega a usarse aunque el fichero esté justo al lado, y el importador tiene que ofrecer
**ambos** módulos como nivel superior. Medido: sin hacerlo, el import muere con
`ModuleNotFoundError: No module named 'apg_guidance'`.

Lo que funciona (verificado en el contenedor):

```python
import vendor.configuration_acestep_v15 as cfgmod
import vendor.sft.apg_guidance as apg
sys.modules["configuration_acestep_v15"] = cfgmod
sys.modules["apg_guidance"] = apg
base = importlib.import_module("vendor.sft.modeling_acestep_v15_base")
```

El alias sobre `sys.modules` tiene además la ventaja de que `AceStepConfig` es **la misma clase**
que usa el turbo, en vez de dos clases distintas cargadas del mismo fichero por dos rutas.

## Paridad estructural con el turbo — verificado, no supuesto

Ejecutado en `ace-step-runner:t05` **sin `--gpus`** (`torch.cuda.is_available() == False`),
instanciando ambos modelos en `meta` con el **mismo** config para que cualquier diferencia sea
atribuible al código:

| Comprobación | base (sft) | turbo | Resultado |
|---|---|---|---|
| Clase del modelo | `AceStepConditionGenerationModel` | igual | idéntica |
| Claves de `state_dict` | 677 | 677 | **conjuntos idénticos**, diferencia simétrica vacía |
| Buffers **no persistentes** | 15 | 15 | **listas idénticas** (5 pares `inv_freq`/`original_inv_freq` de RoPE + 5 del FSQ) |
| Símbolos solo en base | `tqdm`, `apg_forward`, `adg_forward`, `MomentumBuffer` | — | solo los imports nuevos |

Los pesos del `sft` (`D:\srv\ace-step\upstream\sft-c410d249\model.safetensors`) tienen las mismas
677 claves con las mismas formas que las `dit.*` del artefacto turbo, y son BF16 —igual que el
turbo upstream—. El F16 del artefacto es **nuestra** conversión deliberada de `build_artifact.py`,
no una diferencia entre modelos.

La advertencia de `../ace_step_shim.py` sobre los 15 buffers no persistentes que
`load_state_dict(strict=True)` **no** detecta aplica aquí **exactamente igual**. No hay atajo.

## BLOQUEO MEDIDO: el `sft` NO corre en fp16 en la GTX 1070

Fecha de la medición: **2026-09-02**. Artefacto `D:\srv\ace-step\weights\ace_step_1_5_sft_lm.safetensors`,
GPU GTX 1070 (sm_61), dtype fp16, atención `eager`.

**Síntoma**: la salida del DiT es NaN en su **primera** pasada, con las entradas finitas
(`x` |max| 4,16; `encoder_hidden_states` |max| 55,7; `context_latents` |max| 6,7). Cualquier
generación muere en `validar_latentes()` — de hecho muere ya en el *warm-up*, que ni siquiera usa la
programación nueva.

**No es del código nuevo**, y esto está aislado, no supuesto. Con el mismo artefacto cargado una
sola vez se probaron cuatro configuraciones y **las cuatro fallan en el paso 0**:

| Configuración | Resultado |
|---|---|
| Programación del turbo (8 pasos), **sin** guía | NaN en el paso 0 |
| 50 pasos, **sin** guía | NaN en el paso 0 |
| 50 pasos, guía APG 7,0 | NaN en el paso 0 |
| 50 pasos, guía APG 3,0 | NaN en el paso 0 |

Es decir: falla igual por el camino que existía antes de tocar nada. Ni el planificador de 50 pasos
ni `apg_forward` intervienen.

**Tampoco son los pesos.** Escaneados los 677 tensores `dit.*` del artefacto (2.393,9 M parámetros):
**0 NaN, 0 Inf**, y el mayor valor absoluto es 5,03 (`dit.decoder.layers.5.cross_attn.o_proj.weight`).
La conversión BF16→F16 de `build_artifact.py` no desbordó.

**Causa, localizada con ganchos de `forward` sobre los 575 módulos del decoder**: la corriente
residual crece capa a capa y se sale del rango de fp16 en **`layers.20`** (de 24):

```
PRIMER MODULO NO FINITO: layers.20  (AceStepDiTLayer)   [posicion 500 de 575]
  entrada: shape=(1, 313, 2048) |max_fin|=6000    nan=0 inf=0
  salida : shape=(1, 313, 2048) |max_fin|=6.4e+04 nan=0 inf=10
```

6.4e4 es el techo de fp16 (65.504). Diez elementos pasan a Inf en la suma residual y las cuatro
capas siguientes los convierten en NaN, que acaba contaminando las 40.000 posiciones del latente.
El turbo, destilado, no llega a esas magnitudes: con el mismo pipeline, el mismo condicionamiento y
la misma tarjeta genera sin un solo valor no finito.

**Qué significa**: la comparación turbo-vs-sft **no se puede ejecutar en esta tarjeta tal cual**. No
es un fallo de integración pendiente de arreglar en el pipeline; es rango numérico. Las salidas
posibles, ninguna de ellas trabajo de esta tarea:

1. **Otra GPU.** En Ampere o posterior el modelo corre en bf16 (su dtype nativo, mismo rango que
   fp32) sin tocar una línea. Es el escenario de GPU local de D-29.
2. **Corriente residual en fp32** dentro del DiT, dejando los `matmul` en fp16. El tensor residual
   es `[1, 313, 2048]` = 2,5 MiB en fp32, así que la memoria no es el problema; hay que verificar
   que ningún producto intermedio desborde por su cuenta.
3. **DiT entero en fp32**: 2,39 G parámetros × 4 B = 9,6 GiB. No cabe en los 8 GiB de la tarjeta.

Lo que **sí** queda hecho y verificado en el repositorio: la programación de 50 pasos, la guía APG
con pasada gemela secuencial y la perilla de variante. Ver `../pipeline/scheduler.py`,
`../pipeline/diffusion.py` y los tests `tests/test_scheduler_variantes.py` y
`tests/test_diffusion_guia.py`.

## Estado de revisión — léase antes de confiar

**Estos ficheros NO han pasado todavía una revisión de seguridad línea a línea.** Son 102 KB de
Python que se **ejecutan** al importarse. Vendorizarlos no los vuelve seguros: los vuelve
*inmutables y auditables*, que es un requisito previo distinto y necesario.

Lo que sí está garantizado hoy:

- No se resuelven por `trust_remote_code` ni `auto_map`: se importan desde esta ruta.
- Están fijados por hash, así que cualquier cambio aparece en un diff.
- No se descargan en tiempo de ejecución ni en el arranque del contenedor.
- Observación **parcial y no sustitutiva de la revisión**: `apg_guidance.py` (221 líneas) solo
  importa `torch` a nivel de módulo y no tiene efectos en tiempo de importación; el diff de
  `modeling_acestep_v15_base.py` contra el turbo ya revisado son 281 líneas concentradas en un
  único método. Eso reduce la superficie nueva, **no la revisa**.

Lo que falta, y es trabajo de `T-03`:

- Revisión escrita con alcance y criterios, buscando en particular ejecución en tiempo de
  importación, red, escritura en disco y `eval`/`exec`.
- Criterio de aceptación que exija un diff contra los hashes de arriba en cada reconstrucción.

## Qué NO está aquí

El **pipeline de inferencia** del `sft` no está en estos ficheros: `generate_audio` trae el bucle de
difusión y la guía, pero el scheduler, el condicionamiento y el decode son los de `../pipeline/`.

*(Actualizado el 2026-09-02.)* Cuando se escribió este apartado, `../pipeline/` **solo sabía de 8
pasos** y **no ejecutaba pasada incondicional gemela**. Las dos cosas ya están:

- `../pipeline/scheduler.py` — programación continua (`construir_programacion_continua`,
  `programacion_de_variante`), 50 pasos por defecto para el `sft`. La tabla de 8 del turbo sigue
  intacta y hay un test que la congela valor a valor.
- `../pipeline/diffusion.py` — guía APG **importando** `apg_guidance.py` de este directorio, con la
  pasada gemela **secuencial** (dos llamadas de lote 1 con dos cachés) en vez de la de lote 2 de
  upstream. Comparadas las dos y verificado que dan lo mismo.
- `../ace_step_shim.py` y `spikes/generate_smoke.py` — perilla `variante` (`turbo`|`sft`), más
  `pasos` y `guidance_scale`.

Lo que **no** está resuelto es el rango numérico: ver el apartado «BLOQUEO MEDIDO» de arriba.
