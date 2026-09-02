---
documento: spike-concurrencia
titulo: "Concurrencia de inferencias — ¿caben 2 a la vez?"
iniciativa: "Plataforma propia de generación musical por IA (proyecto personal)"
slug: plataforma-musical-ia
tarea: T-04
estado: parcial
fecha: 2026-09-02
autor: implementer
decide: "T-39 (despacho FIFO+RR) — cuántas inferencias por GPU"
depende-de: T-03, T-05
spec: ../spec.md
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
evidencia: "D:\\srv\\ace-step\\out\\libre-informe.json · libre-canonica-informe.json · ab-planificador-informe.json · lm-on.log · ab-planificador.log"
---

# Concurrencia de inferencias de ACE-Step 1.5 (T-04)

> **Veredicto en una línea.** En la GPU local (GTX 1070, 8.191 MiB) **no caben dos inferencias**, y no por poco: dos procesos *parados*, con el modelo cargado y sin generar nada, ya ocupan **8.026 de 8.191 MiB**. La pregunta que T-39 realmente necesita —cuántas caben en la **L40S de 48 GB**— **sigue sin medir** y queda bloqueada por presupuesto.
>
> **Esta tarea NO está completada.** Tiene dos mitades y solo una está cerrada. Ver §7 y §10.

---

## 0. Las dos preguntas, separadas

La ficha de T-04 se titula «Medición de 2 inferencias concurrentes **en la L40S**». La decisión D-29 (2026-08-18) añadió que se intentara primero en GPU local. Eso creó dos preguntas distintas que conviene no mezclar:

| # | Pregunta | Para qué sirve | Estado |
|---|---|---|---|
| **P1** | ¿Caben 2 inferencias en la **GPU local de 8 GB**? | Saber si el desarrollo local puede paralelizar; y si el suelo de 8 GB de la spec (§11.1, D-06) admite concurrencia | ✅ **Medida y cerrada — NO caben** |
| **P2** | ¿Caben 2 (o más) inferencias en la **L40S de 48 GB**, y con qué degradación por pista? | **Es la entrada real de T-39**: cuántos trabajos despacha el planificador por pod | ⛔ **PENDIENTE — bloqueada por presupuesto** |

P1 responde por qué no se ejecutó P2 en local. **No la sustituye.**

---

## 1. Qué se midió y qué NO se ejecutó, deliberadamente

**No se lanzaron dos inferencias simultáneas.** No es una omisión: es la conclusión aritmética de §4, tomada *antes* de intentarlo. Forzar dos procesos CUDA sobre 8.191 MiB cuando el suelo conjunto ya son 8.026 MiB produce un `CUDA out of memory` en el mejor caso y, como ya ocurrió una vez en esta máquina, tumba el demonio de Docker en el peor. **Ningún contenedor se ejecutó para redactar este documento**; todos los números salen de ejecuciones ya realizadas hoy y archivadas en `D:\srv\ace-step\out\`.

Los criterios de aceptación de T-04 anticipan este desenlace: exigen documentar «cabe / no cabe, y con qué degradación» y «si la medición se ejecutó en GPU local o en el pod de RunPod, **y por qué**». Aquí está el porqué, con la aritmética entera.

---

## 2. Aparato de medida

| Elemento | Valor |
|---|---|
| GPU | NVIDIA GTX 1070, `sm_61` (Pascal) |
| VRAM total | **8.191 MiB** según `torch.cuda` (`total_memory = 8.589.672.448 B`); 8.192 MiB nominales. El off-by-one es CS-51, confirmado dentro del contenedor en T-05 |
| Nivel de la política de VRAM | `tier3` (6–8 GB) de los ocho de `adapters/ace_step/gpu_tiers.py` → **offloading activo por defecto** |
| Imagen | `ace-step-runner:t05` (`torch 2.13.0+cu126`, CUDA 12.6, cuDNN 9.10.2) |
| Artefacto | `ace_step_1_5_lm.safetensors` — 7.529.590.739 B, **1.492 tensores** |
| Instrumentación | muestreador de VRAM por etapa a **40 ms** (`apps/runner/spikes/generate_smoke.py`, arnés de `vram_profile.py` de T-03) + contador de `torch.cuda` |

### 2.1 Reparto del artefacto (leído de la cabecera `safetensors`, sin cargar nada)

| Prefijo | Tensores | Bytes | MiB | dtype |
|---|---:|---:|---:|---|
| `dit.*` | 677 | 4.787.745.036 | **4.565,9** | F16 |
| `lm.*` (planificador 5 Hz) | 310 | 1.325.768.704 | 1.264,4 | BF16 |
| `text_encoder.*` (Qwen3) | 310 | 1.191.553.024 | 1.136,4 | F16 |
| `vae.*` | 182 | 168.828.164 | 161,0 | F16 |
| `aux.*` | 13 | 55.514.475 | 52,9 | F32 + U8 |
| **Total** | **1.492** | **7.529.409.403** | **7.180,6** | — |

Desglose del DiT: `dit.decoder` 3.004,9 MiB (476 tensores) · `dit.encoder` 1.160,4 MiB (140) · `dit.tokenizer` 200,3 MiB (32) · `dit.detokenizer` 200,3 MiB (28) · `dit.null_condition_emb` 1 tensor.

**Nota sobre los «4.574 MiB de todo `dit.*`»:** los 4.565,9 MiB de la tabla son los bytes crudos del artefacto. La cifra de 4.574 MiB que aparece como `reservado_pico_mb` en varias ejecuciones (`ab-planificador-informe.json`, `lm-on-informe.json`, `con-limitador-informe.json`) es el pico del *asignador* de torch, 8,1 MiB por encima — consistente con tener `dit.decoder` y `dit.encoder` reservados a la vez, más alineación. Las dos cifras describen lo mismo con y sin sobrecoste del asignador; **ninguna de las dos incluye el contexto CUDA**, que se cuenta aparte en §3.

---

## 3. Huella de VRAM de UNA sola inferencia

### 3.1 El suelo: el proceso en reposo

Con el pipeline cargado y **antes de generar nada**, el shim deja residente en VRAM únicamente `dit.decoder`; el resto vive en RAM. Registro literal (`D:\srv\ace-step\out\lm-on.log`, repetido idéntico en `ab-planificador.log`):

```
Pipeline listo en 562.22 s. Residente en VRAM: dit.decoder (3007 MiB).
En RAM: dit.encoder 1932 MiB, text_encoder 1136 MiB, vae.decoder 161 MiB.
VRAM libre: 4178 MiB de 8192 MiB.
```

De donde:

```
  ocupado en reposo   = 8.192 - 4.178 =  4.014 MiB
  de eso, pesos       =                  3.007 MiB  (dit.decoder)
  ---------------------------------------------------------------
  sobrecoste fijo     =                  1.007 MiB  (contexto CUDA, cuBLAS/cuDNN,
                                                     bloques del asignador)
```

El muestreador lo confirma por vía independiente: `carga.etapas.vram_load.vram.usado_pico_mb = usado_final_mb = 4.013 MiB`. **Se usa 4.013 MiB como suelo por proceso** en toda la aritmética que sigue.

### 3.2 Los picos por etapa (pista de 240 s)

Ejecución `libre-informe.json` (2026-09-02T14:22Z, pista de 240 s, offloading activo, planificador de 5 Hz puesto):

| Etapa | Duración | VRAM usada (pico) | Asignado | Reservado | Transitorio sobre el suelo |
|---|---:|---:|---:|---:|---:|
| planificación (LM 5 Hz) | 615,320 s | 4.779 MiB | 3.491 | 3.586 | +766 MiB |
| **condicionamiento** | 11,917 s | **7.606 MiB** | 6.156 | 6.314 | **+3.593 MiB** |
| difusión | 37,363 s | 5.941 MiB | 4.095 | 4.930 | +1.928 MiB |
| decode del VAE | 25,099 s | 5.547 MiB | 3.808 | 4.536 | +1.534 MiB |
| escritura | 0,633 s | 4.075 MiB | 3.014 | 3.064 | +62 MiB |

Segunda ejecución de control (`libre-canonica-informe.json`, 15:00Z, misma pista con etiquetas de sección canónicas): condicionamiento 7,039 s / **7.596 MiB**, difusión 36,792 s / 5.661 MiB, decode 24,827 s / 5.547 MiB. **Los picos se reproducen dentro de ±10 MiB en condicionamiento y son idénticos en decode.**

> **Corrección de un dato que circulaba.** El pico de una inferencia **no** son los 5.941 MiB de la difusión: es **7.606 MiB, y ocurre en el condicionamiento**, cuando conviven `dit.decoder` (3.007) + `dit.encoder` (1.932 al materializarse) + el text encoder Qwen3 (1.136) más el sobrecoste. El propio encabezado de `ace_step_shim.py` ya lo advertía para la pista de 60 s (6.190 MiB en condicionamiento, «no en la difusión»). Usar 5.941 MiB subestima el pico real en 1.665 MiB. Toda la aritmética de §4 se da con **ambas** cifras para que el veredicto no dependa de cuál se elija.

**Lo importante: estos picos ya son los del modo con offloading.** No hay margen que rascar apagándolo — apagarlo empeora. Sin offloading la residencia sería el modelo entero sobre GPU: `dit` 4.565,9 + `text_encoder` 1.136,4 + `vae` 161,0 = **5.863,3 MiB** de pesos + 1.007 de contexto = **6.870 MiB en reposo**, que dejarían 1.321 MiB para todos los transitorios de una sola inferencia. (El `lm.*` nunca sube a GPU: «662884352 parametros en bf16 sobre CPU (1264 MiB de RAM). El LM NO sube a el».)

---

## 4. La aritmética de dos inferencias concurrentes

Dos inferencias simultáneas = **dos procesos CUDA independientes**. Cada uno paga su propio contexto CUDA y su propio asignador; no comparten pesos residentes ni caché. La suma es literal.

Presupuesto disponible: **8.191 MiB**.

| # | Escenario | Cálculo | Necesario | % del presupuesto | Resultado |
|---|---|---|---:|---:|---|
| **A** | Los dos en su pico (condicionamiento) | 2 × 7.606 | **15.212 MiB** | **185,7 %** | ❌ faltan **7.021 MiB** |
| **B** | Los dos en difusión | 2 × 5.941 | **11.882 MiB** | **145,1 %** | ❌ faltan **3.691 MiB** |
| **C** | Uno en difusión, el otro **parado** con el modelo cargado | 5.941 + 4.013 | **9.954 MiB** | **121,5 %** | ❌ faltan **1.763 MiB** |
| **D** | Los **dos parados**, sin generar nada | 2 × 4.013 | **8.026 MiB** | **98,0 %** | ⚠️ quedan **165 MiB** |

Los escenarios A y B son los esperables. **El que cierra la discusión es el D**, y por eliminación el C:

```
  dos procesos en reposo ............................  8.026 MiB
  presupuesto .......................................  8.191 MiB
  ---------------------------------------------------------------
  margen para TODA la actividad de los dos ..........    165 MiB

  transitorio minimo de una sola difusion ...........  1.928 MiB
  deficit ...........................................  1.763 MiB  (10,7x el margen)
```

Es decir: **aunque el planificador escalonara perfectamente las etapas** para que nunca coincidieran dos fases pesadas, en el instante en que *uno* de los dos procesos entra en difusión ya no cabe, porque el otro —sin hacer absolutamente nada— retiene 4.013 MiB que no puede soltar sin descargar el modelo. Y descargarlo y recargarlo costaba los 709 s de `vram_load` medidos en la misma ejecución —72,9 s desde la lectura contigua de pesos del 2026-09-02—, que sigue siendo mucho peor que serializar.

**No es un problema de sincronización. Es un problema de suelo.**

### 4.1 Qué haría falta para que cupieran dos

| Requisito | VRAM mínima | Comentario |
|---|---:|---|
| Dos en reposo + un transitorio de difusión | 9.954 MiB | ni siquiera permite generar en paralelo |
| Dos difusiones simultáneas (escenario B) | 11.882 MiB | tarjeta de 12 GB **sin margen alguno** |
| Dos inferencias completas seguras (escenario A) | 15.212 MiB | **≥ 16 GB nominales**, y aun así con ~1,1 GB de holgura |
| Dos inferencias completas con margen operativo | ~20–24 GB | recomendable |

Sobre 8 GB no hay configuración, offloading ni orden de etapas que lo arregle.

---

## 5. Respuesta a P1 (GPU local): NO caben, y por qué se decidió aquí y no en la nube

**Se midió en GPU local.** Se decidió **no** ir al pod de RunPod, y los criterios de T-04 admiten exactamente una causa para usar cloud —«VRAM local insuficiente»— que **sí se cumple**. Aun así no se ha usado, por un motivo posterior a la redacción de la ficha:

> **El propietario aparcó RunPod por presupuesto (decisión del 2026-09-02).** No hay pod contratado, no hay gasto cloud autorizado, y esta tarea no es la que justifica reabrirlo.

Consecuencia registrada sin adornos: la excepción cloud que la ficha preveía **estaba justificada técnicamente pero no está financiada**. Por eso T-04 no se cierra: se cierra su mitad local y se deja la otra abierta con dueño y causa.

---

## 6. Lo que sí queda demostrado para el suelo de 8 GB de la spec

`spec.md` §11.1 y D-06 fijan 8 GB como suelo con offloading. Esta medición lo acota con precisión:

- ✅ **Una** inferencia de 240 s cabe en 8 GB con offloading: pico 7.606 MiB de 8.191 (92,9 %), margen 585 MiB.
- ❌ **Dos** no caben, con 3.691 a 7.021 MiB de déficit según la fase.
- ⚠️ El margen de la ejecución única es **585 MiB (7,1 %)**. Es estrecho: cualquier aumento del texto de entrada, del contexto o de la longitud puede comerlo. Registrar como riesgo para `T-85`/`T-86` (runner GPU local): en `tier3`, **1 trabajo por GPU es un invariante, no una preferencia**.

---

## 7. ⛔ Lo que queda PENDIENTE: la L40S de 48 GB

**Esto es lo que T-39 necesita y no se ha medido.**

| Qué falta | Por qué no se puede deducir de lo anterior |
|---|---|
| VRAM pico real por proceso en L40S | En una L40S la política de VRAM sería `tier1`, **sin offloading**: la residencia por proceso cambia de 4.013 MiB a ~6.870 MiB (§3.2). No es la misma medición escalada |
| **Degradación del tiempo por pista con N procesos** | Es el dato decisivo de T-39 y **no es extrapolable en absoluto**. Dos procesos en la misma GPU compiten por SM, ancho de banda de memoria y planificador; la penalización depende de la arquitectura (`sm_89` frente a `sm_61`), del tamaño de la caché L2 y de si se usa MPS/MIG. Medirlo en una GTX 1070 no dice nada de una L40S |
| Interacción con `max_gpu_seconds` y el kill switch | El tope por trabajo y el límite global agregado se comportan distinto con N trabajos concurrentes por pod |

**Extrapolación orientativa, explícitamente NO vinculante** (sirve para dimensionar la expectativa, no para decidir): 48 GB nominales ≈ 46.000 MiB útiles con ECC; a ~6.870 MiB de residencia sin offloading más ~3.600 MiB de transitorio de condicionamiento, saldrían ~10.500 MiB por proceso → **4 procesos por VRAM**. Pero *caber* no es *rendir*: si cuatro procesos concurrentes multiplican por 3,5 el tiempo por pista, el throughput no mejora y la latencia percibida empeora. **Eso solo lo dice la medición.**

**Bloqueo:** presupuesto. Sin pod de RunPod contratado no hay L40S que medir. Se desbloquea si (a) se contrata el pod para `T-03` (arranque en frío, único gasto cloud autorizado de la Fase 0) y se aprovecha la misma sesión, o (b) se accede a una GPU de ≥ 24 GB por otra vía.

---

## 8. Entrada para T-39 (despacho FIFO+RR) — contrato

El criterio de T-39 dice: «Si `T-04` confirmó 2 inferencias concurrentes viables, el despacho las aprovecha; si no, se despacha 1 por pod». La respuesta que T-39 debe implementar hoy:

1. **Por defecto, 1 inferencia por GPU.** No es provisional para el `tier3` local: ahí es un invariante duro (§6).
2. **La concurrencia es configuración, no constante.** T-39 expone un `max_inferencias_concurrentes` por tipo de GPU, con valor **1** hasta que exista medición. Prohibido codificar 2 «porque en 48 GB seguro que caben».
3. **Elevar ese valor por encima de 1 requiere la medición de §7**, con las dos cifras: VRAM pico conjunta **y** degradación del tiempo por pista. Sin la segunda, el número no se sube.
4. **Regla de admisión.** Antes de asignar un trabajo a una GPU ocupada, el despachador comprueba `vram_libre ≥ pico_esperado_del_perfil`, no `vram_libre > 0`. El escenario D demuestra que una GPU al 98 % con dos procesos en reposo se presenta como «viva» y falla en cuanto uno trabaja.
5. **La economía de T-04 no se materializa.** La nota de la ficha estimaba «~128 €/mes ahorrables si el resultado es favorable». En local no lo es. En L40S sigue sin saberse — y ese ahorro **no debe darse por ganado** en ninguna proyección de `evaluation.md` §6.3/§12.1.

---

## 9. Trazabilidad de la evidencia

Todo lo numérico de este documento sale de estos ficheros, generados hoy 2026-09-02 en `D:\srv\ace-step\out\`:

| Fichero | Qué aporta |
|---|---|
| `libre-informe.json` (14:22Z) | Picos y tiempos por etapa de la pista de 240 s — tabla de §3.2 |
| `libre-canonica-informe.json` (15:00Z) | Repetición de control con etiquetas canónicas — reproducibilidad de los picos |
| `lm-on.log` · `ab-planificador.log` | Registro literal de residencia y VRAM libre — suelo de §3.1 |
| `ab-planificador-informe.json` · `lm-on-informe.json` · `con-limitador-informe.json` | `reservado_pico_mb = 4.574` en decode — nota de §2.1 |
| `D:\srv\ace-step\weights\ace_step_1_5_lm.safetensors` | Cabecera leída sin cargar pesos — tabla de §2.1 |
| `apps/runner/adapters/ace_step/ace_step_shim.py` (cabecera) | Verificación previa en pistas de 30/60/180 s: pico en condicionamiento, no en difusión |

**Sobre `apps/runner/spikes/concurrency_profile.py`:** el fichero que la ficha lista **no existe y no se ha creado**. La medición no lo necesitaba: la instrumentación por etapas que ya trae `generate_smoke.py` (arnés de `vram_profile.py`, T-03) da el perfil completo por proceso, y sumar dos procesos es aritmética, no código. Si algún día se mide P2 en la L40S, ahí sí hará falta el arnés de dos procesos — y ese será el momento de escribirlo.

---

## 10. Estado de los criterios de aceptación de T-04

| # | Criterio | Estado | Justificación |
|---|---|---|---|
| 1 | Se ejecutan 2 inferencias simultáneas y se mide el tiempo por pista frente a la ejecución en solitario | ⛔ **NO cumplido** | En local es físicamente imposible (§4): dos procesos en reposo ocupan el 98,0 % de la VRAM. En L40S no se ha ejecutado: sin pod por presupuesto. **El tiempo por pista concurrente sigue sin medir** |
| 2 | Se mide el VRAM pico simultáneo de ambas inferencias | 🟡 **Parcial** | Medido el pico por proceso con precisión (7.606 MiB, ±10 MiB entre repeticiones) y derivada la suma. **No es una medida simultánea**: es una suma de dos medidas individuales, y así consta |
| 3 | Resultado (cabe / no cabe, y con qué degradación) documentado y usado como entrada de `T-39` | 🟡 **Parcial** | «No cabe» está documentado y cuantificado para 8 GB, y el contrato para T-39 está escrito (§8). **La degradación no se ha medido en ningún hardware**, porque en local no hay concurrencia posible que degradar |
| 4 | Se documenta si se ejecutó en GPU local o en RunPod, y por qué | ✅ **Cumplido** | GPU local. La VRAM insuficiente justificaba la excepción cloud, pero el propietario aparcó RunPod por presupuesto el 2026-09-02 (§5) |

**Conclusión de estado: T-04 queda `en-progreso`, no `completado`.** Un criterio sin cumplir y dos parciales. Lo que falta no es redacción: es una medición sobre hardware que hoy no está disponible.

---

## 11. Cómo se cierra esta tarea

Cuando exista acceso a una GPU de ≥ 24 GB (L40S del pod, o equivalente):

1. Escribir `apps/runner/spikes/concurrency_profile.py`: lanza N procesos del runner con la misma pista, muestrea VRAM global del dispositivo (no por proceso) y cronometra cada pista.
2. Medir N = 1, 2 y, si cabe, 3 y 4. Registrar VRAM pico global y **tiempo por pista de cada uno**.
3. Calcular la degradación: `t_pista(N) / t_pista(1)`. El throughput real es `N / degradación`. Si ese cociente no supera 1,3 respecto a N = 1, **la concurrencia no compensa** y T-39 se queda en 1 por pod.
4. Actualizar §7 y §8 de este documento y el estado de `T-04` en `tasks.md`.

Coste estimado del cierre: ~1,5 h de las 3 h de la ficha (la mitad local ya está gastada), más el tiempo de pod.
