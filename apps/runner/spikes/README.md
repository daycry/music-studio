# Spikes de la Fase 0 — runbook de ejecución

Guía para **ejecutar** los spikes de viabilidad en una máquina con GPU sin tener que leer
el código. Si solo vas a lanzar comandos, con este fichero te basta.

Fecha: **2026-08-18**. Alcance: **Fase 0** (`T-03`, `T-04`, `T-05`, `T-07`). El ledger de
progreso es `docs/roadmap/2026-07-27-plataforma-musical-ia/tasks.md`; anota ahí cada tarea
(`pendiente → en-progreso → completado`) y **no** crees ledgers paralelos.

---

## 0. Aviso de honestidad, antes de nada

**Actualización del 2026-09-03.** Lo que sigue en esta sección describe la situación del
2026-08-18, cuando se escribieron los tres primeros scripts. Desde el 2026-09-01 hay **GPU
local** (GTX 1070, 8 GB, Pascal sm_61), `torch` está instalado en el host y en la imagen, y
todos los números de `tasks.md` T-03/T-05/T-06/T-07 están **medidos** en ella. Los puntos 1–4
se conservan como registro de cómo se validó el arnés antes de tener GPU, no como estado.

**En la máquina donde se escribió este código no había GPU** (2026-08-18). `nvidia-smi` no
existía ahí y `torch` no estaba instalado. Consecuencias, todas deliberadas:

1. Los scripts se han verificado **solo en modo `--mock`**, que recorre el camino completo
   (carga → generación → telemetría → informe) con **la biblioteca estándar únicamente**.
   Eso valida la **forma del contrato y el arnés de medición**, no el modelo.
2. **Los números de los documentos de resultados están vacíos a propósito.** Nadie ha
   medido todavía tiempos, VRAM ni arranque en frío. Rellenarlos con las cifras del mock
   sería inventarse los datos que recalibran el §6 de `evaluation.md` (el coste de GPU de
   todo el proyecto).
3. Todo informe generado en modo mock lleva `"source": "mock"` y un `aviso` en la cabecera
   del JSON. **Si ves esa marca, no es una medición.** No la cites en ninguna decisión.
4. Los pines de versión de `requirements.txt` **no se han resuelto ni compilado aquí**:
   verifícalos contra el driver de tu GPU antes de fiarte de ellos.

---

## 1. Estado del árbol y qué tarea cierra cada fichero

| Fichero | Tarea | Qué hace | Estado a 2026-08-18 |
|---|---|---|---|
| `../contracts.py` | cimiento | Contrato mínimo del adapter, validadores de D-14 y D-17 | entregado |
| `_timing.py` | cimiento | Cronómetro por etapas, VRAM, estadísticas sin numpy, informes JSON | entregado |
| `_mock.py` | cimiento | Adapter mock determinista (modo `--mock`) | entregado |
| `../adapters/ace_step/adapter.py` | `T-05` | Adapter mínimo de ACE-Step 1.5 | entregado |
| `../adapters/ace_step/Dockerfile` | `T-05` | Imagen CUDA del runner | **pendiente** |
| `vram_profile.py` | `T-03` | Tiempos de inferencia, perfil de VRAM, arranque en frío | entregado |
| `concurrency_profile.py` | `T-04` | Dos inferencias simultáneas | **pendiente** |
| `capability_probe.py` | `T-07` | Matriz de capacidades verificadas | entregado |
| `g1_generar.py` | `T-09` (preparación) | Kit de G1: genera la serie propia de los 10 briefs de §4, anonimizada y con mapa sellado. **No ejecuta el gate** | entregado (§5.5) |
| `requirements.txt` | — | Dependencias de spikes y adapter (el mock no necesita ninguna) | entregado |

Orden de ejecución: **`T-05` (contenedor) → `T-03` (línea base) → `T-04` (concurrencia,
usa la línea base de `T-03`) → `T-07` (capacidades)**. Los cuatro son requisito de `T-09`,
el gate **G1**.

**Estado a 2026-09-03 — los 16 ficheros del directorio.** La tabla de arriba es la de la
entrega inicial; esta es la real. Para las banderas exactas de cada uno, `python <script> --help`.

| Fichero | Tarea | Qué hace | Dónde escribe |
|---|---|---|---|
| `_timing.py` | cimiento | Cronómetro por etapas, muestreo de VRAM, estadísticas, informes JSON atómicos | — |
| `_mock.py` | cimiento | Adapter mock determinista (`--mock`), mismo contrato M-3 que el real | — |
| `generate_smoke.py` | `T-03` | Generación real de extremo a extremo; `--matriz` para el A/B 2×2 del planificador; `verificar_wav` de contratos observables. Es lo que lanza `generar.cmd` | `/outputs` (= `D:\srv\ace-step\out`) |
| `vram_profile.py` | `T-03` | Arnés de tiempos de inferencia, perfil de VRAM y arranque en frío; protección C1 | `--out` |
| `medir_carga.py` | `T-03`/`T-05` | Dónde se va el tiempo al cargar el artefacto (defecto `vram_load`) | stdout / JSON |
| `probe_io.py` | `T-05` | Sonda de E/S: qué estrategia de lectura saca más MiB/s del bind mount | stdout |
| `pascal_speed_probe.py` | `T-03` | Microbenchmark de torch puro (fp16/fp32, SDPA, formas reales del DiT) para decidir dtype y atención en Pascal | JSON |
| `dit_forward_bench.py` | `T-03` | Cronometra un forward del DiT real con los pesos reales, por longitud | JSON |
| `diag_conditioning.py` | diagnóstico | H3: qué condicionamiento de texto ve el DiT (tildes, metadatos) | JSON |
| `diag_pasos.py` | diagnóstico | D-PASOS: cuánto de la falta de finura es el precio de la destilación del turbo | JSON |
| `medir_ab.py` | `T-03` | Análisis de señal sin GPU del A/B del planificador: descriptores, contrastes 2×2, `efecto_relativo_pct`, bloque de ritmo | `--salida` |
| `comparar_variantes.py` | `T-06` | Compara dos pistas del A/B de variante de pesos (turbo/sft). n = 1 por rama: ver `tasks.md` T-06 | JSON |
| `capability_probe.py` | `T-07` | Sonda empírica de capacidades: matriz verificada | JSON |
| `g1_generar.py` | `T-09` (prep.) | Kit de G1: serie propia de las 10 pistas, cegado por testigo, mapa sellado. **No ejecuta el gate** | carpeta de sesión |
| `requirements.txt` | — | Dependencias de referencia para correr en el host; **la fuente de verdad de versiones es el `Dockerfile`** | — |
| `README.md` | — | Este runbook | — |

Regla operativa desde el 2026-09-02, tras tumbar Docker Desktop con cuatro procesos GPU en
paralelo: **un solo contenedor con GPU a la vez** en esta máquina. Las pistas dentro de un
proceso van en serie y no son el problema; los procesos concurrentes sí. No hay lock que lo
imponga: es una regla de quien lanza.

> Este runbook se escribió **en paralelo** a los tres scripts. Para cualquier bandera, la
> fuente de verdad es `python <script> --help`; si un comando de aquí no cuadra con la
> ayuda del script, manda la ayuda del script y corrige este fichero.

---

## 2. Prerrequisitos reales

### GPU

| Cifra | Valor | Qué implica |
|---|---|---|
| Suelo absoluto | **8 GB** de VRAM | ACE-Step 1.5 (3,5B) arranca **con offloading** y **tiempos degradados**. Por debajo, el runner **aborta con mensaje claro**, nunca en silencio |
| Confort | **24 GB** | RTX 4090 / 5090. Sin offloading; tiempos comparables con la línea base de S-02 |
| Referencia cloud | **L40S 48 GB** | Es el objetivo del presupuesto. Si mides en otra GPU, hay que documentar el **factor de conversión** |

El offloading se activa **automáticamente** por debajo de 24 GB y se avisa de la
degradación: no es una opción que se elija a mano salvo que fuerces `--offload`.

### Software del host

```bash
nvidia-smi                       # driver visible + version de CUDA soportada
docker --version                 # Docker Engine
docker info | grep -i runtime    # debe aparecer 'nvidia'
```

Comprobación de que el **NVIDIA Container Toolkit** funciona de verdad (que Docker vea la
GPU, no solo que exista):

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Si eso no lista tu GPU, **para aquí**: nada de lo que sigue medirá nada real. Instala el
toolkit (`nvidia-container-toolkit`) y reinicia el demonio de Docker.

### Pesos del modelo

Los pesos **se montan como volumen, nunca viajan en la imagen** (es lo que hace medible el
arranque en frío de `T-03`):

```
/srv/ace-step/weights/ace_step_1_5.safetensors
```

**Solo `safetensors` (D-14).** El adapter valida la extensión antes de abrir el fichero y
rechaza cualquier formato basado en pickle (`.pt`, `.bin`, `.ckpt`, `.pkl`, `.joblib`):
cargar uno **ejecuta** el código que lleve dentro. El hash verifica **integridad, no
inocuidad**.

### Si ejecutas en el host en vez de en el contenedor

Python **3.13** y, solo para el modo real:

```bash
python -m venv .venv-spikes && . .venv-spikes/bin/activate
pip install -r apps/runner/spikes/requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cu124
```

Para el modo `--mock` **no instales nada**: biblioteca estándar.

---

## 3. Comprobación en dos minutos, sin GPU

Sirve para saber si el arnés está sano antes de ocupar una GPU. Desde la **raíz del repo**:

```bash
python apps/runner/spikes/capability_probe.py --mock
python apps/runner/spikes/vram_profile.py --mock --runs 2 --both
python apps/runner/adapters/ace_step/adapter.py probe
```

En PowerShell son los mismos comandos en una línea (no hay continuaciones con `\`).

Qué debes ver: los tres terminan con éxito, el informe de `capability_probe` da
**`NO_CONCLUYENTE` en las cuatro capacidades** y todos los JSON llevan `"source": "mock"`.
Eso es el resultado **correcto** en mock, no un fallo: ver §5.3.

---

## 4. El contenedor de `T-05`

El `Dockerfile` está en `../adapters/ace_step/Dockerfile` (`T-05`, completado el 2026-09-02).
El contexto de construcción es **`apps/runner`** (así lo invoca `generar.cmd`: `docker build -t
ace-step-runner:t05 -f apps\runner\adapters\ace_step\Dockerfile apps\runner`), porque la imagen necesita
`apps/runner/contracts.py` y `apps/runner/spikes/` además del adapter:

```bash
# desde la raiz del repo
docker build \
  -f apps/runner/adapters/ace_step/Dockerfile \
  -t daycry/ace-step-spike:t05 \
  .
```

Diagnóstico de hardware sin cargar pesos (lo primero que hay que ejecutar):

```bash
docker run --rm --gpus all \
  -e ACE_STEP_REQUIRE_GPU=1 \
  daycry/ace-step-spike:t05 probe
```

Generación de una pista, extremo a extremo:

```bash
docker run --rm --gpus all \
  -v /srv/ace-step/weights:/weights:ro \
  -v "$PWD/evaluacion-segregada:/outputs" \
  -e ACE_STEP_REQUIRE_GPU=1 \
  daycry/ace-step-spike:t05 \
  generate --duration 180 --instrumental --report /outputs/generate.json
```

Notas que evitan una tarde perdida:

- **`ACE_STEP_REQUIRE_GPU=1` siempre.** Sin esa variable, el adapter que no ve CUDA
  **cae al mock** y te devuelve silencio con aspecto de resultado. Con ella, aborta y te
  dice por qué.
- Los pesos van en **`:ro`** (solo lectura). El runner no escribe en ellos.
- **Ninguna credencial entra en el contenedor** (D-15): ni fichero de secretos, ni claves
  en el `Dockerfile`, ni `-e AWS_...`. Para generar no hace falta red de salida: los pesos
  están montados.
- Los subcomandos del adapter son `serve`, `generate`, `probe` y `healthcheck`
  (`adapter.py --help`). La consola de `serve` **no tiene autenticación**: escucha en
  loopback y solo se publica en `127.0.0.1`. No es la API de plataforma (eso es `T-11`).
- El punto de integración con el código del modelo es un **shim**
  (`ACE_STEP_PIPELINE_FACTORY`, por defecto `ace_step_shim:build_pipeline`). Ese fichero
  **no existe todavía**: se escribe en la máquina con GPU, con la release delante, como
  parte de `T-03`. Sin él, el modo real **falla con mensaje explícito en lugar de fingir**.

### Ejecutar los spikes dentro del contenedor

Los spikes necesitan estar donde está la GPU. La forma robusta —que no depende de cómo el
`Dockerfile` copie el árbol— es montar el repo y sustituir el entrypoint:

```bash
docker run --rm --gpus all \
  -v /srv/ace-step/weights:/weights:ro \
  -v "$PWD:/work" -w /work \
  -e ACE_STEP_REQUIRE_GPU=1 \
  --entrypoint python \
  daycry/ace-step-spike:t05 \
  apps/runner/spikes/vram_profile.py --runs 10 --both --skip-cold-start \
    --gpu-label "RTX 4090" --weights-dir /weights
```

En una **GPU local de desarrollo** (D-29) puedes lanzar los mismos scripts directamente en
el host con el venv de §2; el contenedor es obligatorio para el arranque en frío y
recomendable para todo lo demás, porque es el entorno que se mide.

---

## 5. Comando exacto de cada spike

Todos los comandos se lanzan **desde la raíz del repo**.

### 5.1 `T-03` — tiempos de inferencia, VRAM y arranque en frío

**Con GPU (local, sin gasto cloud):**

```bash
python apps/runner/spikes/vram_profile.py \
  --runs 10 --both \
  --duration-s 180 \
  --gpu-label "RTX 4090" \
  --weights-dir /weights \
  --skip-cold-start
```

`--both` mide los dos escenarios que pide `T-03`: 10 inferencias **sin** offloading y 10
**con** offloading. `--gpu-label` es lo que permite calcular el **factor de conversión** a
la L40S objetivo; si mides en una L40S, el factor es 1,0. `--skip-cold-start` es
obligatorio en local: ver §6.

**Arranque en frío (solo tiene sentido en el pod de RunPod):** el mismo comando **sin**
`--skip-cold-start`, ejecutado en el pod, en los tres escenarios de `T-03` (imagen
cacheada, imagen no cacheada, pesos no cacheados).

**Sin GPU:** `python apps/runner/spikes/vram_profile.py --mock --runs 2 --both`

**Dónde caen los resultados (estado real a 2026-09-03):** los informes JSON de todas las
corridas viven en `D:\srv\ace-step\out\` (montado como `/outputs` en el contenedor), fuera del
repo, o donde diga `--out`. `apps/runner/spikes/results/` **no existe**. Las conclusiones están
hoy en las fichas de `tasks.md` (T-03, T-05, T-06, T-07); `apps/runner/spikes/inference_timing.md`
**todavía no existe** (lo dice la propia ficha de T-03).

> **Contrato de telemetría (cambio M-3).** `gpu_seconds` y `stage_timings` de cada
> generación cubren **solo esa generación** (la etapa `inference`). El coste del arranque
> (`weights_download`, `vram_load`, `warmup`) se paga **una vez** por carga y el adapter lo
> reporta aparte: `load_stage_timings_s` / `load_gpu_seconds` en su cabecera
> (`describe()` / `report_metadata()`), en los bloques `load_*` de cada escenario de
> `vram_profile.py` y en `presupuesto_gpu.load_gpu_seconds` de `capability_probe.py`. Para
> el presupuesto de D-17 el arranque sigue contando, pero **una sola vez**: los informes
> anteriores a este cambio lo repetían en cada run y los agregados salían inflados.

### 5.2 `T-04` — dos inferencias concurrentes

El script (`concurrency_profile.py`) **no está en el árbol** en el momento de escribir esto.
Cuando esté, **empieza por su ayuda**, que es la fuente de verdad de sus banderas:

```bash
python apps/runner/spikes/concurrency_profile.py --help
python apps/runner/spikes/concurrency_profile.py --mock      # verificacion del arnes
```

Lo que la tarea exige medir, con independencia de cómo se llamen las banderas: **dos
inferencias simultáneas**, el **tiempo por pista de cada una** frente a la ejecución en
solitario (la línea base es el resultado de `T-03`), y el **VRAM pico simultáneo de las
dos**. Ojo con esto último: `_timing.vram_snapshot_mb()` mide el **proceso actual**, así
que el pico simultáneo de dos procesos hay que leerlo del sistema:

```bash
nvidia-smi --query-gpu=memory.used --format=csv -l 1
```

### 5.3 `T-07` — matriz de capacidades verificadas

**Con GPU, contra el contenedor de `T-05`:**

```bash
python apps/runner/spikes/capability_probe.py \
  --duration 30 \
  --weights-dir /weights \
  --out evaluacion-segregada/T-07-matriz-capacidades \
  --keep-audio
```

Una sola capacidad (las cuatro son `section_inpaint`, `audio_to_audio`,
`voice_conditioning`, `continuation`; la bandera se puede repetir):

```bash
python apps/runner/spikes/capability_probe.py --capability continuation --keep-audio
```

**Sin GPU:** `python apps/runner/spikes/capability_probe.py --mock`

**Dónde caen los resultados:** `evaluacion-segregada/T-07-matriz-capacidades/` en la raíz
del repo por defecto (`--out` lo cambia), con `matriz-capacidades-t07.json` y las
evidencias de audio en `audio/`. La tabla en Markdown que imprime por consola está lista
para pegarla en `docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/matriz-capacidades.md`.

**Cómo se leen los tres veredictos** (esto es el valor entero de la tarea):

| Veredicto | Significa | Qué hacer |
|---|---|---|
| **SI** | La capacidad se invocó y el audio muestra el efecto estructural esperado, medido | Escuchar la evidencia antes de anotarlo: que sea *utilizable* es juicio humano |
| **NO** | La pila del **modelo** declara que esa tarea no existe | **Leer la traza** guardada en `excepcion` antes de darlo por definitivo: un NO puede tumbar 276 h de Fase 3 |
| **NO_CONCLUYENTE** | No se pudo saber | Es un **resultado**, no un fallo. Incluye el caso clave: el adapter mínimo de Fase 0 **no expone** el parámetro, así que no se distingue «el modelo no lo soporta» de «aún no lo hemos cableado» |

Dos topes que el script se impone y no puedes saltarte con una bandera:

- En **`--mock` ningún veredicto puede ser SI ni NO.** El informe conserva el veredicto
  bruto y marca `clamp_mock_aplicado` para que se vea que la medición corrió.
- **`voice_conditioning` nunca sale SI de forma automática.** Verificar que el timbre se
  parece a la referencia exige escucha humana ciega o un modelo de similitud de locutor, y
  ninguno de los dos está en el alcance de la Fase 0.

Si las cuatro salen `NO_CONCLUYENTE` con el motivo «el adapter aceptó el parámetro y lo
ignoró», la matriz **no está cerrada**: hay que hacer que el adapter de `T-05` reenvíe
`model_params` al pipeline (o exponga su punto de entrada de tareas) y repetir la sonda.
El propio informe lo dice en `recomendaciones`.

**Códigos de salida** de `capability_probe.py`: `0` informe completo · `1` informe escrito
pero **parcial** (por ejemplo, se agotó `--max-gpu-seconds-total`) · `2` fallo operativo
(no hay adapter, VRAM insuficiente, `health()` no listo) y no se escribe matriz.

### 5.4 A/B del planificador de 5 Hz — `generate_smoke.py --matriz`

Mide **si el planificador cambia la calidad**. Hasta el 2026-09-02 el planificador de
upstream estaba desconectado y `src_latents` era un recorte del latente de **silencio**: el
DiT componía a ciegas. Ahora el plan entra en su sitio y se enciende o se apaga con
`model_params["usar_lm"]`.

Requiere el artefacto **con** planificador (`--incluir-lm`, 7,0 GiB, 1.492 tensores):

```bash
python apps/runner/tools/build_artifact.py --incluir-lm \
  --out "D:\srv\ace-step\weights\ace_step_1_5_lm.safetensors"
python apps/runner/tools/build_artifact.py --verify --incluir-lm \
  --out "D:\srv\ace-step\weights\ace_step_1_5_lm.safetensors"
```

#### Un par no basta: hace falta la vara de medir

Generar una pista con planificador y otra sin él **no responde a la pregunta**. Ya está
medido en este proyecto que cambiar la semilla mueve mucho el audio, así que dos pistas
distintas no demuestran nada: si el planificador mueve el audio *menos* que un cambio de
semilla, su efecto no se distingue del azar. Por eso el experimento mínimo honesto cruza
**dos ejes** —planificador sí/no × dos semillas— y añade un par largo, porque lo que se le
supone al planificador es **estructura**, y a 25 s puede no haber estructura que planificar.

`--matriz` ejecuta ese cruce **tras una sola carga**, que es lo que lo hace viable: el
arranque en frío son ~643 s, y seis contenedores serían ~64 min de cargar seis veces el
mismo artefacto.

```bash
MSYS_NO_PATHCONV=1 docker run --rm --gpus all --name ab-planificador \
  -e ACE_STEP_REQUIRE_GPU=1 \
  -v "D:\srv\ace-step\weights:/weights:ro" -v "D:\srv\ace-step\out:/outputs" \
  -v "C:\...\apps\runner:/work:ro" \
  --entrypoint python ace-step-runner:t05 -u /work/spikes/generate_smoke.py \
  --fichero-pesos ace_step_1_5_lm.safetensors \
  --matriz "lm-si-s1:25:20260902:si,lm-no-s1:25:20260902:no,lm-si-s2:25:771013:si,lm-no-s2:25:771013:no,lm-si-60:60:20260902:si,lm-no-60:60:20260902:no" \
  --seguir-tras-fallo --max-gpu-seconds 2400 --etiqueta ab-planificador
```

Cada celda es `etiqueta:duracion_s:semilla:si|no`. Prompt, letra, BPM, tonalidad y compás
son comunes a todas: lo único que varía son los dos ejes.

> **El `-u` no es decorativo.** Si rediriges la salida a un fichero (`> ab.log`), Python
> pasa a bufferear por bloques y el log se queda mudo durante minutos: parece que la carga
> se ha colgado cuando en realidad va avanzando. Con un arranque en frío de ~11 min esa
> confusión cuesta cara. `-u` (o `PYTHONUNBUFFERED=1`) hace que cada hito aparezca al
> instante.

**Que las seis pistas salgan del mismo proceso no contamina la comparación**, y está
verificado en el código, no supuesto:

* El ruido de difusión sale de `prepare_noise`, que construye un `torch.Generator` propio
  sembrado con la semilla (`modeling_acestep_v15_turbo.py`). No lee el RNG global.
* El bucle ODE vendorizado (`vendor/pipeline/diffusion.py`) no vuelve a sortear nada:
  llama a `prepare_noise` una vez y sigue.
* El planificador siembra el RNG global él mismo (`torch.manual_seed`) al entrar, así que
  su plan tampoco depende de lo que corrió antes.

De ahí la propiedad que hace válido el A/B: **a igual semilla, la rama CON y la rama SIN
reciben exactamente el mismo ruido inicial**. Lo único distinto entre las dos es
`src_latents`.

#### Medir el resultado — `medir_ab.py`

```bash
python apps/runner/spikes/medir_ab.py \
  --directorio "D:\srv\ace-step\out" --salida "D:\srv\ace-step\out\ab-medidas.json"
```

No necesita GPU. Mide nivel (RMS, pico, factor de cresta), espectro (centroide, rolloff
95 %, energía sobre 4 kHz, planitud, flujo) y —lo que de verdad importa aquí— **estructura**
(autocorrelación de la envolvente de energía, dispersión del RMS por segundo, y curva de
novedad sobre la matriz de autosimilitud para contar fronteras de sección).

Y sobre todo **compara contrastes, no pistas sueltas**:

| contraste | qué es |
|---|---|
| `d_lm` | diferencia CON − SIN a igual semilla. El efecto del planificador. |
| `d_semilla` | diferencia s1 − s2 dentro de la misma rama. El ruido de referencia. |
| `d_cruzado` | distinta rama y distinta semilla. Cota superior. |
| `ratio_lm_semilla` | `d_lm / d_semilla`. **Menor que 1 = el planificador mueve menos que el azar.** |

> Los descriptores están verificados contra señales de valor teórico conocido en
> `tests/test_medir_ab.py` (centroide de ruido blanco = `sr/4`, rolloff 95 % = `0,95·sr/2`,
> factor de cresta de un seno = 3,01 dB). Un centroide mal calculado no da un error: da un
> número plausible y una conclusión falsa.

**Lo que cuesta, medido en la GTX 1070 (2026-09-02):** arranque en frío 614 s
(`vram_load` 571 s + warm-up 43 s, el warm-up ya con planificador), así que el A/B completo
son ~21 min de los que ~20 son cargar dos veces. El planificador corre **en CPU** y cuesta
342-448 ms por código: a 5 códigos por segundo de pista, una de 25 s son ~50 s de
planificación frente a ~1,4 s de difusión. `--lm-cfg 1.0` lo divide por dos a cambio de
perder el guiado.

> **El presupuesto de D-17 incluye la carga.** Por eso `--max-gpu-seconds` pasó de 600 a
> 1800: con 600 el trabajo se abortaba tras cargar y antes de generar nada. El techo sigue
> siendo un techo.

---

### 5.5 Kit de ejecución de G1 — `g1_generar.py`

Genera la **serie propia** de las 10 pistas del gate G1 leyendo los briefs directamente de
`docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md` §4.

> **Este script prepara el gate; no lo ejecuta.** No puntúa, no compara, no abre el mapa
> ciego y no escribe veredicto. Escuchar y puntuar lo hace **el propietario**, y los
> umbrales de §2 tienen que estar **ratificados y firmados (§9) antes de la primera
> escucha** — sin eso la sesión no es válida (§8.1) por muy bien que salga el audio.
> Tampoco genera las líneas base de Suno ni de librería: eso es §5.1 y viene de fuera.

#### Qué hace, en orden

1. **Lee los 10 briefs de §4** del protocolo en cada arranque y anota su SHA-256. No están
   copiados en el código a propósito: §4 los declara *propuestos, pendientes de
   ratificación*, y el propietario puede sustituir cualquiera antes de generar. Si
   estuvieran duplicados, una sustitución en el protocolo no llegaría al audio.
2. **Deriva el prompt de estilo** de forma mecánica de las columnas (§4.2) — el mismo
   literal que luego va a Suno, a la búsqueda en librería y a CLAP.
3. **Valida las letras** que le pases: etiquetas canónicas, tildes, extensión mínima de
   §4.1. Si alguna falla, **no genera nada** y sale con código `3`.
4. **Genera de una en una**, tras una sola carga, con el planificador de 5 Hz puesto y los
   metadatos poblados.
5. **Anonimiza** cada pista y sella el mapa con SHA-256.
6. Deja el árbol de carpetas de §10.2 (`01-briefs/`, `02-generado/propio/`, `05-ciego/`,
   `08-manifiestos/`) fuera del repo.

#### Las letras las escribes tú

`--letras` es obligatorio. §4.1 y la precondición 7 de §9.1 ponen las 10 letras del lado
del propietario, y el script **no inventa ninguna**: una letra inventada haría que la
dimensión 4 y el WER midieran otra cosa. Lo único que se da hecho son los esqueletos con
las etiquetas ya puestas, sin un solo verso dentro:

```bash
python apps/runner/spikes/g1_generar.py --escribir-plantillas D:/srv/ace-step/letras/g1
```

Deja `B-01.txt` … `B-10.txt` con `[verse]`/`[chorus]` vacíos y, al lado, `B-NN.BRIEF.txt`
con el brief delante para escribir sin ir al protocolo. **No pisa ficheros existentes.**

Tres cosas se comprueban y **bloquean**, porque las tres costaron una tanda de GPU el
2026-09-02:

| Comprobación | Por qué bloquea |
|---|---|
| Solo `[intro] [verse] [chorus] [bridge] [outro]`, en minúsculas | Las etiquetas de estilo Suno (`[VERSO 1 - HOMBRE, entra el beat]`) **viajan verbatim al modelo y se cantan**. Con las canónicas el pulso salió un 47 % más marcado. Una pista generada con etiquetas malas no se distingue por el nombre del fichero |
| Letra en castellano con al menos una tilde o eñe | «soñar» y «sonar» son palabras distintas y secuencias de tokens distintas. Una letra castellana sin ni una tilde casi siempre es una a la que se le han caído, y hundiría el WER por un fallo nuestro. Escape consciente: `--permitir-sin-tildes` |
| ≥ 1:30 → dos `[verse]` y un `[chorus]`; más corta → dos frases | Es la extensión mínima que fija §4.1 |

#### Ensayo en seco (haz siempre esto primero)

No carga los pesos ni genera audio: lo único que le pide a la GPU es su nombre y su VRAM
para detectar el nivel.

```bash
MSYS_NO_PATHCONV=1 docker run --rm --gpus all -e ACE_STEP_REQUIRE_GPU=1 \
  -v "D:\srv\ace-step\weights:/weights:ro" \
  -v "D:\srv\ace-step\out:/outputs" \
  -v "D:\srv\ace-step\letras\g1:/letras-g1:ro" \
  -v "C:\Users\daycr\OneDrive\Development\claude\suno\apps\runner:/work:ro" \
  -v "C:\Users\daycr\OneDrive\Development\claude\suno\docs\roadmap\2026-07-27-plataforma-musical-ia\gates:/protocolo:ro" \
  --entrypoint python ace-step-runner:t05 /work/spikes/g1_generar.py \
    --dry-run --letras /letras-g1 --raiz-evaluacion /outputs/g1-2026
```

Fíjate en que hay **un montaje nuevo**: `gates/` en `/protocolo`. Sin él el script no
encuentra los briefs y aborta diciéndolo (el repo entero no está montado en el contenedor).

El ensayo en seco también corre **fuera del contenedor**, en el portátil, sin GPU ni torch
con CUDA — ahí el nivel sale «no detectado» y lo dice:

```bash
python apps/runner/spikes/g1_generar.py --dry-run --letras D:/srv/ace-step/letras/g1
```

#### Generación real

**Idéntico, quitando `--dry-run` y añadiendo `--si`.** El `--si` es deliberado: sin
terminal interactiva el script se niega a arrancar una tanda de horas sin que nadie haya
visto la estimación.

```bash
MSYS_NO_PATHCONV=1 docker run --rm --gpus all -e ACE_STEP_REQUIRE_GPU=1 \
  -v "D:\srv\ace-step\weights:/weights:ro" \
  -v "D:\srv\ace-step\out:/outputs" \
  -v "D:\srv\ace-step\letras\g1:/letras-g1:ro" \
  -v "C:\Users\daycr\OneDrive\Development\claude\suno\apps\runner:/work:ro" \
  -v "C:\Users\daycr\OneDrive\Development\claude\suno\docs\roadmap\2026-07-27-plataforma-musical-ia\gates:/protocolo:ro" \
  --entrypoint python ace-step-runner:t05 /work/spikes/g1_generar.py \
    --letras /letras-g1 --raiz-evaluacion /outputs/g1-2026 --si
```

Si se corta a media tanda, se reanuda por brief y **no se repite lo ya hecho**:

```bash
    ... /work/spikes/g1_generar.py --letras /letras-g1 --desde B-06 --si
    ... /work/spikes/g1_generar.py --letras /letras-g1 --solo B-03,B-07 --si
```

La **semilla maestra manda sobre todo**: con la misma `--semilla-maestra` (20260902 por
defecto) salen las mismas semillas, las mismas etiquetas ciegas y el mismo barajado. Es lo
que hace reproducible una repetición de §8.5.

#### Cuánto tarda — está medido, no estimado a ojo

El script imprime la estimación **antes de pedir confirmación**, calibrada con **9
mediciones reales** de esta misma máquina (`libre-canonica`, `t05-final`, `ab-planificador`,
`con-limitador`…) y no con un factor inventado. Da un rango porque el planificador de 5 Hz
es autorregresivo y **su coste varía entre corridas de la misma duración**: cinco pistas de
25 s costaron entre 42,5 s y 113,1 s.

| Tomas por brief | Pistas | Audio | Optimista | Central | Pesimista |
|---|---|---|---|---|---|
| **3** (§5.2) | 30 | 3.000 s | 124 min | **133 min** | 159 min |
| 1 (`--tomas 1`) | 10 | 1.000 s | 41 min | **46 min** | 56 min |

Carga en frío incluida (~113 s, **una sola vez** para toda la tanda). La pendiente robusta
son **~2,7 s de cómputo por segundo de audio**; lo que varía es el término fijo.

> **`--tomas` vale 3 por defecto, no 1.** §5.2 fija «3 tomas por brief y por serie
> (semillas distintas, todas registradas)» y que el propietario elija una comparando solo
> dentro de la serie, **al menos 24 h antes** de la sesión. Con una sola toma no hay nada
> que elegir y el material no cumple el protocolo. `--tomas 1` existe para un ensayo, y
> entonces el informe queda marcado `sesion_no_conforme_5_2`.

#### El ciego empieza aquí, y por qué

§5.4 anonimiza **series** (propia / Suno / librería) y eso pasa después. Pero hay un ciego
**antes**: §5.2 te obliga a elegir una toma de tres, y si los ficheros se llamaran
`B01-toma1/2/3` esa elección estaría anclada por el orden. Por eso:

- el nombre es **opaco y no ordenado** — `B01-3f9a2c.wav`, con
  `sha256(semilla_maestra|brief|toma)[:6]`;
- el **orden de generación se baraja** dentro de cada brief, para que el `mtime` tampoco
  reconstruya el índice de toma;
- **`02-generado/propio/registro-tecnico.json` se puede abrir** sin romper nada: lleva
  tiempos por etapa, pico de VRAM, duración real y nivel de GPU, pero **ni semillas ni
  índices de toma**;
- la semilla y el índice viven **solo** en `05-ciego/mapa-tomas.csv` y en
  `08-manifiestos/`, sellados con SHA-256 (§5.6).

```bash
# comprobar el sello antes de abrir el mapa (§5.6)
cd D:/srv/ace-step/out/g1-2026/05-ciego && sha256sum -c mapa-tomas.sha256
```

> **Riesgo residual declarado**, en la línea de §5.4.5: con 3 tomas, el barajado deja el
> orden original **1 de cada 6 veces**, así que ordenar por `mtime` da un acierto ocasional.
> Y quien lanza el script ve la consola mientras corre. Si eso te importa, redirige la
> salida a fichero y no la mires. **Lo que no se puede eliminar se escribe.**

#### El nivel de GPU va en el acta, y no es un adorno

El script resuelve el nivel con `adapters/ace_step/gpu_tiers.py` y lo escribe en el informe,
en el registro técnico **y en cada pista**. En esta máquina sale:

```
nivel detectado: tier3 de 8 niveles
nivel=tier3 vram=8191 MiB dtype=float16 atencion=eager
planificador=acestep-5Hz-lm-0.6B lote<=2 duracion<=480s offload_dit=True cuantizar=False
```

**tier3 es el tercer nivel por abajo de ocho**: sin BF16, sin INT8, atención `eager` y
planificador de 0,6B. El hardware de referencia de la spec (RTX 4090/5090) es **tier6b** y
corre otra configuración — no es el mismo modelo más despacio, es **una configuración
distinta**. Consecuencia directa para el acta: **un `NO-GO` medido en tier3 dice «no sirve
en tier3», no «no sirve»**, y una decisión sobre 589 h no se puede tomar sobre una medición
mal atribuida. Si el nivel no aparece encima del veredicto, esa distinción se pierde.

`--forzar-nivel` existe para pruebas y **grita en el informe**: un acta no puede decir que
se generó en un nivel que no era.

#### Qué queda escrito

```
D:\srv\ace-step\out\g1-2026\
  01-briefs\          brief JSON + prompt literal + letra literal + letra sin marcas (referencia del WER, §4.1)
  02-generado\propio\ los WAV con nombre ciego + registro-tecnico.json  <- se puede abrir
  05-ciego\           mapa-tomas.csv + mapa-tomas.sha256 + sello.json + LEEME-NO-ABRIR.txt
  08-manifiestos\     manifiesto retroactivo simplificado por toma (§10.2)  <- lleva semilla
  g1-generacion-informe.json
```

El **manifiesto retroactivo simplificado** de §10.2 (modelo, SHA-256 de pesos, semilla,
prompt, letra, fecha, hardware, parámetros) se escribe por pista. Es *retroactivo y
simplificado* porque el manifiesto v1 real llega con C-10a (`T-26`, F5) y estas pistas nacen
antes de que exista el ledger: una cadena WORM **no admite backfill** (D-20), así que la
trazabilidad de G1 es documental y no pretende otra cosa.

#### Códigos de salida

| Código | Significado |
|---|---|
| `0` | Todo bien (o ensayo en seco correcto, o cancelado en la confirmación) |
| `1` | Se generó, pero alguna pista falló sus comprobaciones observables |
| `2` | Excepción durante la tanda — el informe y el mapa se escriben igual |
| `3` | **Letras inválidas o ausentes. No se generó nada y no se tocó la GPU** |

#### Lo que sigue abierto y no lo cierra este script

- **Ratificación firmada de los umbrales y de los briefs (§9)** — sin ella la sesión no es
  válida (§8.1). Es del propietario y va **antes** de generar.
- **Decisión D-23 de loudness por destino**, por escrito antes de la primera escucha
  (§5.5, deuda declarada).
- **Líneas base de librería elegidas antes de generar** (§5.1, regla anti-sesgo), y la
  decisión de usar Suno o ir a la **variante B** (§5.6).
- **Normalización de loudness de sesión** (−16 LUFS / ≤ −1 dBTP), recodificación uniforme y
  borrado de metadatos de las 30 pistas (§5.4-§5.5): eso es `ffmpeg` sobre las tres series
  juntas, y aquí solo existe una.
- **CLAP y WER** (§6): dependen de identificadores y SHA-256 de pesos que `T-09` fija al
  ejecutar.

> **La tonalidad no la declara ningún brief.** El script deriva el **modo** del carácter
> declarado en §4 («melancólico», «oscuro», «solemne» → menor) pero la **tónica es una
> convención fija** (A menor / C mayor, igual para los diez), no una decisión musical. Se
> mantiene constante porque §5.2 manda congelar lo que no sea un eje del brief. Para
> cambiarla en algún brief: `--extra` con
> `{"B-10": {"keyscale": "F# minor"}}`, y el informe registra que vino de ahí.

---

## 6. Qué criterio de aceptación cierra cada comando

| Tarea | Criterio de aceptación | Comando que lo cierra | Dónde |
|---|---|---|---|
| `T-05` | El contenedor arranca y expone `load/generate/health/unload` | `docker run --gpus all ... probe` y `... generate` | consola + `--report` |
| `T-05` | Pesos solo desde `safetensors` (D-14) | cualquiera de los anteriores (el adapter valida antes de abrir) | traza de error si se le pasa un pickle |
| `T-05` | Arranca con `docker run --gpus all` en GPU local ≥ 8 GB | `... probe` con `ACE_STEP_REQUIRE_GPU=1` | consola |
| `T-03` | Tiempo de inferencia por pista en GPU ≥ 24 GB | `vram_profile.py --runs 10 --no-offload` | `results/*.json` + `inference_timing.md` |
| `T-03` | VRAM pico con y sin offloading frente a 8/24 GB | `vram_profile.py --runs 10 --both` | ídem |
| `T-03` | Arranque en frío cacheado (2–6 min) y sin cachear (5–12 min) | `vram_profile.py` **sin** `--skip-cold-start`, **en el pod de RunPod** | ídem |
| `T-03` | Factor de conversión si la GPU local no es la L40S | `--gpu-label "<tu GPU>"` | ídem |
| `T-04` | 2 inferencias simultáneas cronometradas frente a la ejecución en solitario | `concurrency_profile.py` (ver su `--help`) | su informe |
| `T-04` | VRAM pico simultáneo | ídem + `nvidia-smi --query-gpu=memory.used` | ídem |
| `T-04` | Se documenta si se midió en local o en RunPod, y por qué | se escribe en el informe | ídem |
| `T-07` | Cada capacidad probada empíricamente con evidencia de audio | `capability_probe.py --keep-audio` | `evaluacion-segregada/T-07-.../` |
| `T-07` | Matriz documentada y enlazada como entrada de decisión | pegar la tabla en `spikes/matriz-capacidades.md` | `docs/roadmap/...` |

Cerrar una tarea es marcar sus casillas en `tasks.md` **con el informe delante**, no
porque el comando terminara con éxito.

---

## 7. Lo que NO se puede medir en local (sección honesta)

### El arranque en frío, no del todo

De las seis etapas instrumentadas (`scheduling`, `image_pull`, `weights_download`,
`vram_load`, `warmup`, `inference`), las **dos primeras son propiedades del proveedor**, no
del modelo:

- **`scheduling`** es el tiempo que RunPod tarda en asignarte una máquina. En local es ≈ 0.
  Medir 0 y apuntarlo como resultado sería falsear S-01.
- **`image_pull`** en local es un `docker pull` desde tu red y tu caché de capas; en el pod
  es la descarga contra el registro del proveedor, y es el **término dominante** del
  arranque en frío sin caché (S-01b).

Por eso: **en local se ejecuta con `--skip-cold-start`**, y los tres escenarios de arranque
en frío (imagen cacheada / imagen no cacheada / pesos no cacheados) **se miden contra el
pod real de RunPod**. Es el **único gasto de GPU cloud de toda la Fase 0** (decisión del
2026-08-18). Los rangos a confirmar son 2–6 min con imagen cacheada y 5–12 min sin ella.

### `T-04`, si tu GPU no llega

`T-04` pregunta si caben **2 inferencias simultáneas en los 48 GB de una L40S**. Con una
GPU de desarrollo de 24 GB puede que no quepan, y entonces la medición **no es
concluyente en local**: se ejecuta en el pod de RunPod como **excepción documentada** del
modo local preferente. **VRAM local insuficiente es la única causa aceptada** para gastar
cloud en esta tarea, y hay que escribirla en el informe. Antes de decidir, mide el pico de
una sola inferencia con `T-03` y compáralo con tu VRAM total.

### Una RTX 4090 no es una L40S

Cualquier tiempo medido en otra GPU necesita un **factor de conversión documentado**
(`--gpu-label`) para poder compararse con S-02/S-02b. El factor es una aproximación lineal,
no una equivalencia: dilo así en `inference_timing.md`.

### La semilla no reproduce el audio

`seed` se registra **por trazabilidad**, no como garantía de salida idéntica: la difusión
en GPU depende del driver, cuDNN, los kernels de atención y el orden de reducción en coma
flotante. **No escribas ninguna comprobación de igualdad bit a bit**: sería inestable por
construcción. Los spikes comparan por tolerancia y por métrica agregada, nunca byte a byte.

### El mock no mide

Los tiempos y la VRAM del modo `--mock` son **derivados de un hash de la petición**.
Son deterministas y plausibles; **no son datos**. Y su audio es **silencio**: por eso la
sonda de `T-07` en modo mock no puede concluir nada, y lo dice.

### La calidad musical no se mide aquí

Ninguno de estos spikes juzga si la música es buena. Eso es **G1** (`T-08`/`T-09`):
escucha ciega humana con protocolo numérico (7/10 ≥ 4/5, WER ≤ 15 %), y **la juzga el
propietario en modo solo** (`gates/gobernanza.md` §2, desde el 2026-09-01), con los umbrales
fijados antes de escuchar y el riesgo de independencia aceptado por escrito.

---

## 8. Política de las pistas que generes (S-11)

Todo el audio de spikes y de G1:

- vive en una **carpeta segregada de evaluación** (`evaluacion-segregada/` en la raíz, o la
  que indiques con `--out`);
- **retención de 12 meses**;
- **no entra en la biblioteca de trabajo ni en ninguna producción**;
- las pistas propias llevan **manifiesto retroactivo simplificado**. El manifiesto de
  procedencia v1 completo lo aporta **`T-27` en la Fase 5**, sobre el esquema **firmado por
  legal** (D-20): ningún adapter de la Fase 0 emite procedencia, y eso es intencionado
  (una cadena WORM no admite backfill).

Esa carpeta la crean los scripts en tiempo de ejecución y **no forma parte del monorepo**;
las reglas de exclusión llegan con `T-10`. Las pistas fuente que usa `T-07` las **genera el
propio modelo**: nunca material de terceros (habría gate de titularidad) y nunca la voz de
una persona real (la clonación de voz es **no-go vigente**).

---

## 9. Invariantes que no se negocian al ejecutar

| Invariante | Qué significa en la práctica |
|---|---|
| **D-14** solo `safetensors` | Si un comando falla porque le pasaste un `.ckpt`, el fallo es correcto. No busques la forma de saltarlo |
| **D-15** sin credenciales | Nada de secretos en el `Dockerfile`, en `-e` ni en ficheros montados. El runner no persiste credenciales |
| **D-17** presupuesto de GPU | Todo trabajo lleva `max_gpu_seconds` y se aborta al excederlo. `capability_probe.py` añade además un tope **agregado** (`--max-gpu-seconds-total`) |
| **D-06 / D-29** hardware | Por debajo de 24 GB, offloading automático con aviso de tiempos degradados; por debajo de 8 GB, **abortar con mensaje claro** |
| Gates | **Ningún umbral se degrada para «pasar».** G1 lo juzga el propietario en modo solo (`gates/gobernanza.md` §2) |

---

## 10. Problemas frecuentes

| Síntoma | Causa y arreglo |
|---|---|
| El informe dice `"source": "mock"` y tú querías medir | El adapter no vio CUDA y cayó al mock, o tienes `ACE_STEP_MOCK=1` en el entorno. Pon `ACE_STEP_REQUIRE_GPU=1` y quita `ACE_STEP_MOCK`. Tanto `capability_probe.py` como `vram_profile.py` detectan esta degradación, avisan a gritos y **degradan el modo (y el informe entero) a `mock`** para no etiquetar simulación como medición |
| `capability_probe.py` aborta con código 2 y «no hay GPU detectada» | Correcto: sin GPU solo es válido `--mock`. Dentro del contenedor, comprueba `--gpus all` y el NVIDIA Container Toolkit (§2) |
| «NO VIABLE: … por debajo del suelo de 8192 MB» | La GPU no llega al suelo de D-06. No hay arreglo local: usa una GPU mayor o el pod de RunPod |
| El modo real falla diciendo que falta el shim del pipeline | Esperado: `ace_step_shim.py` se escribe en la máquina con GPU (parte de `T-03`). Preferimos fallar así a fingir una medición |
| `GpuBudgetExceeded` a media matriz | El tope agregado de D-17 hizo su trabajo. El informe queda **parcial** y lo declara; sube `--max-gpu-seconds-total` y repite |
| El perfil de energía sale vacío con artefactos FLAC/MP3 | La biblioteca estándar no decodifica esos formatos. Instala `soundfile` (`requirements.txt`, más `libsndfile1` en el sistema) |
| Las cuatro capacidades salen `NO_CONCLUYENTE` con «lo ignoró» | El adapter no reenvía `model_params` al pipeline. Ver §5.3: la matriz no está cerrada, y **no** puedes anotarlo como `NO` |
| Los WAV ocupan una barbaridad | 44,1 kHz estéreo de 16 bit son ~10,6 MB por minuto. Baja `--duration` en `T-07` (30 s bastan: mide capacidad, no calidad) |

---

## 11. Al terminar

1. Anota el resultado en **`docs/roadmap/2026-07-27-plataforma-musical-ia/tasks.md`**
   (ledger canónico) marcando solo las casillas que puedas verificar con el informe.
2. Redacta las conclusiones donde toca: `inference_timing.md` (`T-03`) y
   `docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/matriz-capacidades.md` (`T-07`).
3. Si los valores medidos difieren de forma material de S-01/S-02, **documéntalo como
   entrada** para una futura revisión de `evaluation.md`; no corrijas la evaluación desde
   una tarea de spike.
4. Recuerda que `T-07` **solo deja el dato**. C-07 y C-08 siguen en Fase 3, **bloqueadas
   por el gate G3**: esta matriz no autoriza a planificarlas.
