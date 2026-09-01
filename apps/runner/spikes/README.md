# Spikes de la Fase 0 — runbook de ejecución

Guía para **ejecutar** los spikes de viabilidad en una máquina con GPU sin tener que leer
el código. Si solo vas a lanzar comandos, con este fichero te basta.

Fecha: **2026-08-18**. Alcance: **Fase 0** (`T-03`, `T-04`, `T-05`, `T-07`). El ledger de
progreso es `docs/roadmap/2026-07-27-plataforma-musical-ia/tasks.md`; anota ahí cada tarea
(`pendiente → en-progreso → completado`) y **no** crees ledgers paralelos.

---

## 0. Aviso de honestidad, antes de nada

**En la máquina donde se escribió este código no había GPU.** `nvidia-smi` no existe ahí y
`torch` no está instalado. Consecuencias, todas deliberadas:

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
| `requirements.txt` | — | Dependencias de spikes y adapter (el mock no necesita ninguna) | entregado |

Orden de ejecución: **`T-05` (contenedor) → `T-03` (línea base) → `T-04` (concurrencia,
usa la línea base de `T-03`) → `T-07` (capacidades)**. Los cuatro son requisito de `T-09`,
el gate **G1**.

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

El `Dockerfile` **todavía no está en el árbol** (lo entrega `T-05`). Cuando esté, el
contexto de construcción es la **raíz del repo**, porque la imagen necesita
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

**Dónde caen los resultados:** informe JSON en `apps/runner/spikes/results/` (relativo al
script, no al directorio de trabajo), o donde diga `--out`. Las conclusiones se redactan a
mano en `apps/runner/spikes/inference_timing.md`.

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
supervisor musical, nunca el desarrollador**.

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
| Gates | **Ningún umbral se degrada para «pasar».** G1 lo juzga el supervisor musical |

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
