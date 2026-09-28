---
plan: improvement-plan.md
titulo: Plan de implementación — Plataforma musical IA (Fase 0 + Fase 1, walking skeleton)
slug: plataforma-musical-ia
fecha: 2026-08-18
actualizado: 2026-09-01
autor: planner
estado: en-progreso
spec: ./spec.md
evaluacion: ./evaluation.md
test-plan: ./test-plan.md
prioridad: Alta
generacion:
  fuente: estimado
  motivo: "usage-meter.py no encontrado en agent-kits/shared del entorno de ejecución (búsqueda sin resultados). Horas y tokens de generación de este documento estimados a juicio, no medidos por el medidor."
---

# Plan de implementación: Plataforma propia de generación musical por IA — Fase 0 + Fase 1

> **Cadena de artefactos**
> **Spec**: [`spec.md`](./spec.md) (`aprobada`, revisión 3) → **Evaluación**: [`evaluation.md`](./evaluation.md) (`completado`, revisión 3, **ratificada 2026-08-18**) → **Plan** (este documento, `en-progreso`) → **Test plan**: [`test-plan.md`](./test-plan.md) (`borrador`, 34 bloques `E2E-xx` + 4 bloques `E2E-GPU-xx` nocturnos — `E2E-GPU-04` añadido con D-29 — + 6 `M-xx` manuales)
>
> Este plan cubre **exclusivamente lo aprobado**: Fase 0 (spikes de viabilidad) + Fase 1 (walking skeleton), **656 h base / 787,2 h con margen / 39.360 € con margen**, ratificados íntegramente el 2026-08-18. Las Fases 2 y 3 se detallan en el **§12** como **pre-planificación condicionada** (bloqueada por gate, sin autorización de gasto); la Fase 4 se referencia en el **§13** como anexo, sin tareas planificadas.
>
> ⚠️ **Este plan no autoriza a empezar a construir.** El **gate G2 (legal)** es la primera tarea (`T-01`) y bloquea todo lo demás — incluida la Fase 0. Mientras I-05, I-05b e I-20 (supervisor musical y usuarios piloto nombrados) no tengan respuesta, las fechas de este plan son de trabajo relativo, no un compromiso de calendario (I-01 sigue abierta).
>
> 🔒 **Extensión de pre-planificación (2026-08-18).** A petición expresa, este documento amplía el detalle a **toda** la iniciativa (Fases 2 y 3, §12) y añade un marcador de la Fase 4 (§13). **La aprobación económica vigente no cambia: sigue siendo únicamente Fase 0 + Fase 1, 39.360 €.** El detalle de §12 (407 h / 24.420 € en Fases 2+3) **no autoriza ningún gasto**: cada sub-fase queda bloqueada por su gate y sus tareas nacen en `tasks.md` con estado `bloqueada (gate)`.
>
> ✅ **Ampliación de alcance ratificada (2026-08-18) — modo GPU local (D-29).** `T-85` (16 h base / 19,2 h con margen / 960 €) en F6 (C-14): proveedor de aprovisionamiento `local` con NVIDIA Container Toolkit, además del cloud RunPod ya planificado. La Fase 0+1 pasa de 640 h/38.400 € a **656 h base / 787,2 h con margen / 39.360 €**, **ratificados en su totalidad por el usuario el mismo día**. `test-plan.md` añade `E2E-GPU-04`.
>
> 🖥️ **Decisión (2026-08-18): Fase 0 en GPU local preferente.** Los spikes (`T-03`–`T-08`) y la generación de las 10 pistas del gate G1 (`T-09`) se ejecutan preferentemente en GPU local, a coste cloud cero — salvo la medición de arranque en frío (S-01/S-01b), que sigue requiriendo el pod real de RunPod. No cambia las horas de desarrollo de F2 (67 h): cambia dónde corre el spike, no cuánto cuesta construirlo. Ver F2 en §5 y detalle por tarea en `tasks.md`.

---

## 1. Cuadro de mando

| Campo | Valor |
|---|---|
| **Spec** | [`spec.md`](./spec.md) — aprobada, revisión 3 (2026-07-27) |
| **Evaluación** | [`evaluation.md`](./evaluation.md) — completado, revisión 3, ratificada por el usuario el **2026-08-18** |
| **Alcance de este plan** | Fase 0 (spikes) + Fase 1 (walking skeleton): C-13, **C-10a**, C-11 (recortado), C-14, C-01, C-12, C-02 |
| **Esfuerzo** | **656 h base / 787,2 h con margen (+20 %)** — **íntegramente ratificadas el 2026-08-18** (640 h / 768 h originales + 16 h / 19,2 h de la ampliación `T-85`, D-29) |
| **Coste** | **32.800 € base / 39.360 € con margen — íntegramente ratificado el 2026-08-18** (38.400 € originales + 960 € de la ampliación `T-85`). Banda vigente de la evaluación (2026-09-01): **33.900–45.000 €**, que ya incluye la ampliación |
| **Tokens IA previstos** | 32,34 M in / 4,53 M out (base) · **38,80 M in / 5,43 M out** (con margen) |
| **Coste de tokens** | ≈ 253 € base / ≈ 303 € con margen (Claude Opus 5, 5 $/M in · 25 $/M out, 0,92 EUR/USD — `.claude/rates.json`) |
| **Nº de tareas** | **54** (`T-01`…`T-53` + `T-85`), agrupadas en 9 sub-fases del plan · **+ 31 tareas de pre-planificación** (`T-54`…`T-84`, §12), bloqueadas por gate |
| **🔒 Pre-planificación condicionada (2026-08-18)** | **Fase 2** (F10, 131 h / 7.860 €) y **Fase 3** (F11, 276 h / 16.560 €) detalladas en §12, cada una bloqueada por su gate — no autorizan gasto. **Fase 4** referenciada solo como anexo en §13, sin tareas |
| **Ledger completo (Fases 0–3)** | **1.063 h base / 1.275,6 h con margen / 63.780 € con margen** — de los cuales **ejecutable hoy y ratificado: 656 h / 39.360 €**; **condicionado a gates: 407 h / 24.420 €** |
| **Precondiciones bloqueantes** | **G2 legal** (I-05, I-05b) · **supervisor musical y 3–5 usuarios piloto nombrados** (I-20) · equipo asignado (I-01, condiciona el calendario, no el presupuesto) |
| **Hito intermedio demostrable** | **Primera canción end-to-end por CLI** (tras `T-45`, dentro de la sub-fase F7) |
| **Camino crítico** | G2 → Gobernanza → Fase 0 (spikes) → G1 → C-13 → C-10a → C-11 (+G1-bis) → C-14 → C-01 backend → **hito CLI** → C-01 frontend → cierre |
| **Estado** | `en-progreso` — **`T-01` (gate G2 legal) `completado`**: G2 levantado el 2026-08-18 con la **fila 1 de la matriz («sí total»)**. **El bloqueo vigente es de gobernanza, no legal**: `T-02` sigue `en-progreso` (I-20) — faltan **2 de los 3 evaluadores de G1** y los **usuarios piloto siguen sin nombrar**. **Ninguna tarea de desarrollo iniciada**: F2 en adelante sigue bloqueada por `T-02` |

---

## 2. Resumen ejecutivo

Este plan traduce a tareas ejecutables la **petición ratificada el 2026-08-18**: construir el walking skeleton de la plataforma musical IA (**640 h / 38.400 € con margen**; **656 h / 39.360 €** tras la ampliación `T-85`/D-29 ratificada el mismo día), sin tocar las Fases 2–4, que quedan fuera de alcance de este documento.

No hay margen de interpretación sobre el orden: la evaluación (D-20, D-27, D-28) impone una secuencia **no negociable** entre características, y este plan la respeta al pie de la letra. Las tres restricciones estructurales que gobiernan toda la planificación:

1. **Nada de desarrollo empieza antes de G2.** El gate legal (dos preguntas: procedencia del audio e I-05b protegibilidad del output) es la tarea `T-01`, con coste cero de desarrollo y capacidad de anular el 100 % del presupuesto.
2. **La trazabilidad (C-10a) va antes que el registry (C-11), y el registry antes que la generación (C-01).** El esquema del manifiesto lo firma legal **antes** de implementar la regla 4 del contrato del registry — al revés de como se planificó en la revisión 2, que dejaba 2+ semanas de audio sin ledger en una cadena que no admite backfill.
3. **G1 evalúa solo ACE-Step**, y HeartMuLa no se da por entregado hasta pasar **G1-bis** con el mismo protocolo. Ningún desarrollador vota en ninguno de los dos gates.

El plan añade un elemento que ni la spec ni la evaluación fijan explícitamente pero que reduce el riesgo de ejecución: un **hito intermedio verificable a mitad de la Fase 1** — una canción generada de extremo a extremo **por línea de comandos**, sin depender de que el frontend esté terminado. Permite validar la arquitectura completa (cola, GPU runner, adapter, post-proceso, manifiesto, ledger) antes de invertir las ~46 h de frontend de C-01 en un backend que aún no se sabe si funciona de punta a punta.

**Lo que este plan hace y no hace, tras la extensión del 2026-08-18.** Sí **detalla como pre-planificación condicionada** C-10b, C-06 y C-05 (Fase 2, §12.1) y C-07, C-08 y C-03 (Fase 3, §12.2): tareas, criterios de aceptación y presupuesto con el mismo nivel de granularidad que F1–F9, pero **bloqueadas por gate y sin autorización de gasto**. Sigue sin planificar C-09 ni C-04 (Fase 4, no-go, §13): ahí no hay tareas `T-XX`, solo un marcador de lo que la desbloquearía y la advertencia de que necesita una evaluación y ratificación nuevas antes de convertirse en plan.

**Extensión de pre-planificación (2026-08-18).** A petición expresa, este documento incorpora en el §12 el detalle ejecutable de la Fase 2 (131 h / 7.860 €) y la Fase 3 (276 h / 16.560 €), con 31 tareas nuevas (`T-54`…`T-84`) que nacen en `tasks.md` en estado `bloqueada (gate)`. **Esto no cambia el veredicto ni la aprobación económica**: sigue aprobado únicamente lo de §1–§11 (39.360 €, incl. `T-85`); el resto es planificación a la espera de que cada gate se supere — G1/G1-bis + Fase 1 en uso + I-13/I-13b para la Fase 2, G3 de adopción para la Fase 3.

---

## 3. Impacto

| Dimensión | Impacto de este plan |
|---|---|
| **Usuarios afectados** | 1–5 usuarios internos de Daycry (producción audiovisual). Sin usuarios piloto nombrados (I-20), no hay a quién entregar el walking skeleton ni forma de medir G3 más adelante |
| **Procesos** | Introduce un flujo nuevo de generación musical con trazabilidad legal desde la primera pista — sustituye parcialmente el recurso a librerías de producción para necesidades que hoy no encajan bien con el catálogo existente |
| **Legal / Compliance** | Depende íntegramente de la respuesta de G2. Introduce el primer artefacto con valor legal del proyecto: el manifiesto v1 + ledger de C-10a, firmado por legal antes de construir el registry |
| **Infraestructura** | Alta una postura de GPU nueva (pod caliente + efímero en RunPod, ≈ 128 €/mes) y un pipeline de object storage con política de retención desde el día uno. **Ampliación ratificada 2026-08-18 (D-29):** el runner también se puede ejecutar en local con GPU propia (`GPU_PROVIDER=local`, NVIDIA Container Toolkit), sin coste de proveedor cloud, para desarrollo/demos y como contingencia si RunPod no está disponible (`T-85`, en F6). **Además, la Fase 0 (F2) usa GPU local preferente desde spikes y G1**, sin esperar a `T-85`: casi todo el consumo cloud previsto de la Fase 0 desaparece, salvo la medición de arranque en frío |
| **Equipo** | Requiere un perfil full-stack senior con Next.js + FastAPI + CUDA + DSP de audio (S-04); el calendario de este plan asume una única persona ejecutando el camino crítico secuencialmente (ver riesgos, §8) |
| **Presupuesto** | 39.360 € con margen (38.400 € + 960 € de la ampliación `T-85`/D-29, ratificados íntegramente el 2026-08-18), dentro de la banda vigente 33.900–45.000 €. Las 116 h de no-desarrollo (legal, supervisor musical) **no están incluidas** en este presupuesto — se gestionan aparte |

---

## 4. Arquitectura

### 4.1 Vista de componentes — alcance de este plan

Diagrama recortado al alcance de Fase 0+1: sin C2PA/WORM/watermarking (C-10b, Fase 2), sin stems (C-06), sin clonación de voz (C-04), sin fine-tuning (C-09), sin router de capacidades ni tercer adapter (D-16, D-06).

```
┌───────────────────────────────────────────────────────────────┐
│  Next.js (App Router) — UI en castellano desde el día 1        │
│  (next-intl, D-25)                                              │
│  editor de letras + gate de derechos (D-21) · prompt de estilo  │
│  biblioteca · reproductor · descargas · panel de procedencia    │
└───────────────┬───────────────────────────────────────────────┘
                │ HTTPS + JWT (Auth.js, C-12)       ▲ SSE (progreso)
                ▼                                   │
┌───────────────────────────────────────────────────────────────┐
│  FastAPI — API de orquestación (C-13 + C-01)                    │
│  /generations · /models · /library · /auth                      │
│  validación · gate de derechos de la letra (D-21) · cuotas      │
└───┬───────────────┬───────────────┬─────────────────────────────┘
    ▼               ▼               ▼
┌────────┐   ┌──────────────┐   ┌──────────────────────┐
│Postgres│   │ Redis + cola │   │ Object storage S3     │
│+ linaje│   │ de jobs      │   │ FLAC + MP3 320         │
│(D-22)  │   │ idempotencia,│   │ (WAV a demanda, 48 kHz,│
│        │   │ DLQ (C-13)   │   │  D-09 / D-23)          │
└───┬────┘   └──────┬───────┘   └──────────────────────┘
    │               │ dispatch FIFO + round-robin (D-26)
    │               ▼
    │   ┌─────────────────────────────────────────────────────┐
    │   │  GPU Runner (C-14): pod caliente Europe/Madrid        │
    │   │  + efímero de desborde · keep-warm 10 min (D-05b)     │
    │   │  credenciales aisladas: URL firmada por trabajo (D-15)│
    │   │  ┌───────────── MODEL REGISTRY (C-11, D-16) ─────────┐│
    │   │  │ adapter: ace-step-1.5 (G1) · heartmula (G1-bis)    ││
    │   │  │ solo safetensors (D-14) · sin router (D-16)        ││
    │   │  └─────────────────────────────────────────────────────┘│
    │   │  post-proceso: ffmpeg — loudness EBU R128 por destino  ││
    │   │  (D-23) · resample soxr a 48 kHz                       ││
    │   └─────────────────────────┬───────────────────────────┘│
    │                             │ provenance (GenerationResult)
    │                             ▼
    │                   ┌───────────────────────────┐
    └──────────────────►│ Ledger append-only         │
                         │ cadena de hashes (D-18)    │
                         │ manifiesto v1 (C-10a, D-20)│
                         │ WORM/C2PA llegan en Fase 2 │
                         └───────────────────────────┘
```

### 4.2 Decisiones de diseño heredadas relevantes para este plan

| ID | Decisión | Por qué condiciona la ejecución de este plan |
|---|---|---|
| D-02, D-16 | Model registry pluggable, **recortado**: contrato + 2 adapters, sin router ni formulario dinámico | Fija el alcance de C-11 (`T-29`–`T-33`): no se construye lo que D-16 excluye explícitamente |
| D-05b, D-26 | Pod caliente en horario `Europe/Madrid` + un efímero de desborde, FIFO + round-robin | Fija el alcance de C-14 (`T-35`–`T-41`); «2 pods por defecto» de la spec queda invalidado |
| D-06, D-27 | ACE-Step como referencia; HeartMuLa segundo adapter sujeto a G1-bis; YuE fuera de alcance | El plan solo contiene dos adapters; el tercero es partida condicional de Fase 2, no de este plan |
| D-09, D-23 | FLAC + MP3 como almacén; WAV solo a demanda, a 48 kHz con soxr; loudness por destino | Fija criterios de aceptación de `T-19`, `T-20` y `T-45` |
| D-13, D-14, D-15 | Conformidad por tolerancia perceptual; solo `safetensors`; aislamiento de credenciales del runner | Invariantes de CI que `T-32` debe probar explícitamente, incluida la prueba negativa de aislamiento |
| D-20 | C-10 partida en C-10a (este plan) y C-10b (Fase 2, fuera de alcance) | Determina que `T-26`–`T-28` preceden a `T-29`–`T-31` (regla 4 del contrato) |
| D-21 | Gate de derechos de la letra en C-01, bloqueo duro | Fija `T-43` como precondición de que cualquier generación pueda encolarse |
| D-22 | Linaje en el esquema desde la primera migración | Fija `T-12` dentro de C-13, antes de que exista ninguna generación |
| D-24, D-25 | Compartir = URL de la app; i18n con `next-intl` desde el día 1 | Fija `T-21` |
| D-28 | Stop-loss al cierre de C-13 | Fija `T-25` como checkpoint obligatorio, no opcional, al final de la sub-fase F4 |
| **D-29** | **Proveedor GPU local además de cloud RunPod, mismo contenedor** (2026-08-18) | Añade `T-85` en F6 (C-14): perfil `docker compose --profile gpu-local`, detección de VRAM y offloading automático. Ampliación de alcance **ratificada el 2026-08-18**; no cambia el contrato del runner ni del registry. Decisión relacionada del mismo día: F2 (Fase 0) usa **GPU local preferente** para spikes y G1 sin esperar a `T-85` — ahí basta `docker run --gpus all` directo sobre el contenedor de `T-05`, sin la abstracción de proveedor |

---

## 5. Sub-fases del plan

> Numeración propia del plan (`F1`…`F9`), distinta de las «Fases 0–4» de la evaluación para no confundir ambos niveles. `F2` a `F8` son las siete piezas que suman las 640 h aprobadas; `F1`, `F3` y `F9` son gates/checkpoints sin coste de desarrollo.

### F1 · Gate G2 y gobernanza previa — 0 h dev (bloqueante)

Primer paso del proyecto entero. Sin resultado de G2, **nada de lo que sigue se ejecuta**. Incluye el nombramiento del supervisor musical y de 3–5 usuarios piloto (I-20), condición del veredicto, no tarea opcional.

**Criterio de salida:** matriz de resultados de G2 resuelta con una de las tres decisiones pre-acordadas (`evaluation.md` §10.1); supervisor musical y usuarios piloto nombrados por escrito.

### F2 · Fase 0 — spikes de viabilidad y protocolo de G1 — 67 h

Contenerización mínima de ACE-Step, medición real de tiempos/VRAM/concurrencia, matriz de capacidades verificadas y el protocolo de G1 **escrito y ratificado antes de escuchar nada**.

> 🖥️ **GPU local preferente (decisión 2026-08-18).** `T-03`–`T-05` ejecutan la inferencia, el perfil de VRAM y la contenerización sobre una **GPU local de desarrollo** (`docker run --gpus all` directo sobre el contenedor de `T-05`, sin la abstracción de proveedor de `T-85`), a coste cloud cero. **Excepción:** la medición de **arranque en frío** (S-01/S-01b: scheduling, pull de imagen, pesos) no se puede reproducir en local y sigue midiéndose contra el pod real de RunPod — es el único consumo de GPU cloud que queda en F2. Si la GPU local difiere de la L40S objetivo, `T-03` documenta el factor de conversión. Esta decisión **ahorra prácticamente todo el consumo cloud previsto de la Fase 0**; las 67 h de desarrollo de F2 **no cambian** — es dónde corre el spike, no cuánto cuesta construirlo.

**Criterio de salida:** las 6 tareas de `T-03` a `T-08` completadas; protocolo de G1 con umbrales numéricos ratificados por el supervisor musical.

> 🆕 **Nota informativa (2026-08-18, hallazgo HF).** El repo oficial `ACE-Step-1.5` publica también la serie **XL** (`xl-base`/`xl-sft`/`xl-turbo`, DiT 4B, ≥12 GB con offload/≥20 GB recomendado, mayor calidad de audio que la base 3,5B). Candidata a incluirse en la medición de `T-03`/`T-05` si la VRAM local lo permite — ver checkbox opcional en `tasks.md`. No cambia las 67 h de F2 ni el criterio de salida.

### F3 · Gate G1 — escucha ciega de ACE-Step — 0 h dev (checkpoint)

Las 10 pistas de ACE-Step para la escucha (`T-09`) se generan igualmente en **GPU local preferente**, sobre el mismo contenedor de `T-05`, a coste cloud cero.

**Criterio de salida:** ≥ 7 de 10 pistas con ≥ 4/5 en la dimensión 5 por al menos 2 de 3 evaluadores; ninguna dimensión con media < 3,0; CLAP y WER dentro de umbral (`evaluation.md` §10.2). Si falla: no-go de la iniciativa o replanteo del catálogo de modelos — el plan se detiene aquí.

### F4 · Cimientos de plataforma (C-13) — 214 h

El suelo sin el cual nada de lo siguiente existe: monorepo, esquema con linaje, storage, cola, biblioteca, reproductor, CI/CD, IaC, observabilidad, 48 kHz/loudness por destino, compartición, i18n. Termina con el **checkpoint de stop-loss** obligatorio.

**Criterio de salida:** 16 tareas (`T-10`–`T-25`) completadas; `docker compose up` levanta el entorno completo; CI despliega a `stage`; checkpoint de stop-loss ejecutado y runbook de desmantelamiento archivado.

### F5 · Trazabilidad mínima y model registry (C-10a + C-11) — 145 h

El orden interno es la parte no negociable: el esquema del manifiesto se firma por legal **antes** de implementar la regla 4 del contrato del registry. Termina con **G1-bis** al registrar HeartMuLa.

**Criterio de salida:** 8 tareas (`T-26`–`T-33`) completadas; G1-bis (`T-34`) superado por HeartMuLa con el mismo protocolo de G1.

### F6 · Infraestructura GPU y orquestación (C-14) — 112 h (íntegramente ratificadas, incluida la ampliación `T-85`)

Runner con caché de imagen y pesos, aprovisionamiento multiproveedor, keep-warm + pod caliente con calendario, despacho FIFO + round-robin, circuit breaker, tope de gasto y kill switch. **Ampliación 2026-08-18 (D-29):** un tercer proveedor de aprovisionamiento, `local`, que ejecuta el mismo contenedor sobre la GPU del propio host vía NVIDIA Container Toolkit.

**Criterio de salida:** 8 tareas (`T-35`–`T-41`, `T-85`) completadas; kill switch disparado en pruebas; failover sin pérdida de trabajos verificado; en una máquina con GPU propia, el modo `gpu-local` genera una pista con contratos idénticos al modo cloud (`E2E-GPU-04`).

> ⏳ **Ampliación PROPUESTA el 2026-09-01 — instalador del runner GPU local (`T-86`, D-30). NO autorizada: pendiente de ratificación económica.** Un **CLI/script de instalación** que implanta el modo `GPU_PROVIDER=local` en una **máquina nueva**: **preflight automatizado** (GPU, VRAM, driver NVIDIA, Docker y **NVIDIA Container Toolkit** con la comprobación real `docker run --rm --gpus all …`, con mensaje accionable por cada carencia), **pesos `safetensors` colocados y verificados por SHA-256** (D-14), **escritura de la configuración local** (`GPU_PROVIDER=local|runpod|mock`, perfil `gpu-local`, guardarraíl **G-01** `ACE_STEP_REQUIRE_GPU=1` en los modos de medición) y **desinstalación limpia**. Fuera de alcance: GUI, auto-update y empaquetado firmado de Windows. **Delta: +32 h base / +38,4 h con margen / +1.920 €** (rango **24–40 h** según el cierre de **I-22**: uno o dos SO objetivo). **Mientras no se ratifique, F6 sigue siendo 112 h / 6.720 € y la Fase 0+1 sigue siendo 656 h / 39.360 €**; `T-86` no entra en el criterio de salida de esta sub-fase ni puede pasar a `en-progreso`. Si se ratificase: F6 144 h / 8.640 €, Fase 0+1 688 h base / 825,6 h / **41.280 €**, ledger completo 1.095 h / 65.700 €. Justificación: D-29 dejó el runner ejecutable en local, pero implantarlo sigue siendo un runbook manual; los ítems 6–7 del `pre-dev-checklist.md` (CS-35/CS-36) se comprueban hoy a mano y sin dueño. **No sustituye a CS-34**: la comprobación manual de la máquina de referencia de los spikes sigue haciendo falta una vez (F2 arranca antes que F6).

### F7 · Generación letra + estilo end-to-end (C-01) — 78 h

**Incluye el hito intermedio del plan.** Orden interno deliberado: primero el backend completo (API, gate de derechos, worker, post-proceso) para poder demostrar una canción de extremo a extremo **por CLI**, y solo después el frontend (editor de letras, formulario, panel de resultado).

> **🎯 Hito intermedio demostrable: primera canción end-to-end por CLI.**
> Tras `T-45`, un script de línea de comandos que llama a `POST /generations` con un brief válido (letra + `lyrics_declaration` + prompt de estilo) debe completar el ciclo completo sin ninguna pieza de frontend: encolado → despacho al pod (caliente o efímero) → inferencia con ACE-Step → post-proceso (loudness + transcode) → manifiesto v1 sellado y encadenado al ledger → artefacto FLAC/MP3 descargable con URL firmada. Es la validación de que C-13 + C-10a + C-11 + C-14 + el backend de C-01 funcionan juntos **antes** de invertir las 38 h de frontend restantes de esta sub-fase. Si el hito falla, se para y se corrige aquí — no al final de la Fase 1.

**Criterio de salida:** 7 tareas (`T-42`–`T-48`) completadas; hito CLI verificado; criterio de aceptación de C-01 de `spec.md` §5.2 cumplido íntegramente (duración ±5 %, loudness ±1 LU, <10 min p95 con pod caliente, manifiesto completo, gate de derechos operativo).

### F8 · Instrumental y autenticación (C-02 + C-12) — 40 h

Quick wins paralelizables entre sí y con el cierre de F7: instrumental es casi gratis sobre C-01 ya construido; autenticación es terreno conocido.

**Criterio de salida:** 4 tareas (`T-49`–`T-52`) completadas; las dos vías de acceso funcionan; 2FA activable/desactivable con reautenticación.

### F9 · Verificación final y cierre — 0 h dev (checkpoint)

**Criterio de salida:** todos los criterios de aceptación de `spec.md` §5.2 para C-01, C-02, C-10a, C-11, C-12, C-13 y C-14 verificados con checkbox marcado; `tasks.md` con todas las tareas en `completado`; handoff escrito hacia la Fase 2 (condicionada a I-13/I-13b).

---

## 6. Presupuesto por sub-fase

| Sub-fase | Horas base | Horas c/margen (+20 %) | Coste € (c/margen) | Tokens in (M, margen) | Tokens out (M, margen) |
|---|---|---|---|---|---|
| F1 · Gate G2 + gobernanza | 0 | 0 | 0 € *(32 h de legal + tiempo de gobernanza, fuera de este presupuesto de desarrollo)* | — | — |
| F2 · Fase 0 — spikes + protocolo G1 | 67 | 80,4 | **4.020 €** | 4,43 | 0,62 |
| F3 · Gate G1 (escucha) | 0 | 0 | 0 € *(≈ 9 h de escucha del supervisor musical, no-dev)* | — | — |
| F4 · Cimientos (C-13) | 214 | 256,8 | **12.840 €** | 9,63 | 1,35 |
| F5 · Trazabilidad + registry (C-10a + C-11) | 145 | 174,0 | **8.700 €** | 8,70 | 1,22 |
| F6 · Infraestructura GPU (C-14) | 112 | 134,4 | **6.720 €** | 8,40 | 1,18 |
| F7 · Generación end-to-end (C-01) | 78 | 93,6 | **4.680 €** | 5,85 | 0,82 |
| F8 · Instrumental + auth (C-02 + C-12) | 40 | 48,0 | **2.400 €** | 1,80 | 0,25 |
| F9 · Verificación final y cierre | 0 | 0 | 0 € | — | — |
| **TOTAL** | **656** | **787,2** | **39.360 €** | **38,80** | **5,43** |

✅ **F6 incluye la ampliación de alcance del 2026-08-18 (`T-85`, modo GPU local, D-29): 16 h base / 19,2 h con margen / 960 €, ratificada por el usuario el mismo día.** Sin ella, F6 serían 96 h/115,2 h/5.760 € (cifra original del 2026-07-27); con ella, F6 son las 112 h/6.720 € de esta tabla, ya ratificadas.

⏳ **La tabla NO incluye la ampliación propuesta `T-86`** (instalador del runner GPU local, D-30, 2026-09-01: +32 h base / +38,4 h con margen / **+1.920 €**, tokens +2,40 M in / +0,34 M out con margen): está **pendiente de ratificación económica** y no suma en ninguna fila ni en el TOTAL. Detalle en §5 (F6) y en `tasks.md` (`T-86`).

**Cuadra con lo ratificado:** los 656 h/39.360 € de esta tabla **coinciden con la cifra ratificada el 2026-08-18** (640 h/768 h/38.400 € originales de `evaluation.md` §9.1/§9.4 + 16 h/960 € de la ampliación `T-85`). Los 54 `T-XX` de este plan suman 656 h exactas (ver `tasks.md` §1).

**Método de tokens:** `horas_IA = horas_base × ratio` (ratio heredado de la ficha de cada característica en `evaluation.md` §7: C-13 0,15 · C-11 0,20 · C-14 0,25 · C-01 0,25 · C-10a 0,20 · C-02 0,167 · C-12 0,143); `tokens_in (M) = horas_IA × 0,25`; `tokens_out (M) = horas_IA × 0,035`. Coste: `(tokens_in × 5 + tokens_out × 25) × 0,92` en €, precio verificado de `.claude/rates.json`. `T-85` usa el ratio de C-14 (0,25). El desglose por tarea está en `tasks.md`.

**Coste de tokens agregado:** ≈ 253 € base / **≈ 303 €** con margen (incluye el delta de `T-85`: ≈ 8 € base / ≈ 9 € con margen). El 0,77 % del coste humano con margen — inmaterial, consistente con la conclusión de `evaluation.md` §9.1.

---

## 7. ⚡ Productividad IA

| Métrica | Base | Con margen (+20 %) |
|---|---|---|
| Horas humanas (referencia) | 656 h | 787,2 h |
| Horas IA | 129,35 h | 155,22 h |
| Supervisión humana (25 %) | 32,34 h | 38,81 h |
| **Horas totales** (IA + supervisión) | **161,69 h** | **194,03 h** |
| **Horas ahorradas** | **494,31 h** | **593,17 h** |
| **Ahorro** | **75,4 %** | **75,4 %** |
| **Multiplicador** | **4,06×** | **4,06×** |
| FTE equivalente ahorrado (160 h/mes) | 3,09 empleado-mes | 3,71 empleado-mes |

✅ **Estas cifras incluyen la ampliación `T-85` (16 h base, D-29), ratificada el 2026-08-18 junto con el resto de Fase 0+1.** Sin ella (cifra original del 2026-07-27): 640 h/768 h humanas, 125,35 h/150,42 h IA, 156,69 h/188,02 h totales, 483,31 h/579,98 h ahorradas, 75,5 % de ahorro, 4,08×.

**Por qué el ahorro de este plan (≈ 75 %) es más alto que el del catálogo completo (62,2 %, `evaluation.md` §9.2).** Las siete características de Fase 0+1 (más el proveedor GPU local de la ampliación) son, en su mayoría, trabajo de aplicación altamente comprimible por un agente (C-13 con ratio 0,15, C-12 con 0,143, C-14 —y su ampliación `T-85`— con 0,25): monorepo, esquema, cola, CI/CD, auth, infraestructura. El catálogo completo arrastra la media hacia abajo por C-09 (fine-tuning, ratio 0,45) y C-04 (clonación de voz, ratio 0,40), que son investigación empírica y escucha humana — precisamente las dos características que este plan **no** incluye. La cifra de este plan es coherente con esa composición, no una desviación.

> ⚠️ **Estimación, no medición.** Horas IA y tokens son un supuesto parametrizado (`evaluation.md` §5, `.claude/rates.json`), no algo medido con `usage-meter.py` (no disponible en este entorno). La supervisión del 25 % es un promedio; en las tareas de escucha y calibración (F2, F3) la evaluación recomienda tratarla como 50 % (`evaluation.md` §9.3) — no aplica aquí porque F2/F3 son en su mayoría horas de coordinación y gate, no desarrollo asistido por IA.

---

## 8. Gates y criterios de salida

| Gate / checkpoint | Cuándo (sub-fase) | Quién decide | Criterio de paso | Si falla |
|---|---|---|---|---|
| **G2 — Legal** | F1, antes de todo | Dirección, con informe de Legal | Dos preguntas resueltas (I-05, I-05b) contra la matriz de resultados pre-acordada | Ver matriz de tres respuestas (`evaluation.md` §10.1); puede ser stop total con 0 € gastados |
| **Gobernanza** | F1 | Dirección | Supervisor musical y 3–5 usuarios piloto nombrados por escrito (I-20) | No se arranca F2 |
| **G1 — Calidad (solo ACE-Step)** | F3, tras F2 | Supervisor musical (voto de calidad) + responsable de iniciativa | 7/10 pistas ≥ 4/5 en dimensión 5 por 2 de 3 evaluadores; ninguna dimensión < 3,0; CLAP/WER dentro de umbral | No-go o replanteo del catálogo de modelos antes de F4 |
| **G1-bis — Calidad HeartMuLa** | Fin de F5, al registrar el adapter | Mismo panel que G1 | Mismo protocolo que G1, aplicado a HeartMuLa | El adapter no se da por entregado; se replantea el segundo modelo |
| **Stop-loss intra-fase** | Fin de F4 (cierre de C-13) | Dirección | > 60 % del presupuesto de Fase 1 consumido con < 40 % del alcance entregado → parada | Runbook de desmantelamiento (`T-25`) ya escrito: qué se conserva, baja del proveedor GPU, destrucción de datos |
| **Verificación final** | F9 | Responsable técnico + responsable de iniciativa | Todos los criterios de `spec.md` §5.2 de C-01/C-02/C-10a/C-11/C-12/C-13/C-14 verificados | Se documentan los huecos y se reabren tareas antes de declarar la Fase 1 cerrada |

---

## 9. Riesgos operativos del plan

> Estos son riesgos **de ejecución de este plan concreto** — secuenciación, dependencias entre tareas, disponibilidad de personas. Los 29 riesgos transversales del proyecto (R-01…R-29) ya están tratados en `evaluation.md` §11 y no se repiten aquí.

| # | Riesgo | Prob. | Impacto | Mitigación en el plan |
|---|---|---|---|---|
| **RP-01** | El camino crítico (G2 → Gobernanza → F2 → G1 → F4 → F5 → F6 → F7) es **estrictamente secuencial**: no hay forma de paralelizar sub-fases con una sola persona ejecutando (S-04, I-01 abierta) | Alta | Alto | F8 (C-02 + C-12, 40 h) y parte del frontend de F7 (`T-46`–`T-48`) sí son paralelizables si hay una segunda persona; declarado explícitamente en el orden de tareas de `tasks.md` |
| **RP-02** | El gate G2 se agota el timebox de 10 días laborables sin respuesta clara, dejando F2 bloqueada indefinidamente | Media | Alto | RACI de `evaluation.md` §10.1 con escalado a dirección general; `T-01` no se cierra por silencio |
| **RP-03** | La firma legal del esquema del manifiesto (`T-26`) se demora más de lo previsto (3 h de preparación, pero depende de agenda de legal), bloqueando `T-27`–`T-33` (toda F5) | Media | Alto | `T-26` se agenda con antelación dentro de F4, no al empezar F5; el documento del esquema puede prepararse en paralelo al cierre de C-13 |
| **RP-04** | El spike de concurrencia (`T-04`) revela que **no** caben 2 inferencias simultáneas en la L40S, invalidando el supuesto de throughput doblado a coste cero usado para dimensionar las esperas de `T-39` | Media | Medio | `T-39` (despacho FIFO+RR) se diseña primero para el caso conservador (1 inferencia por pod); la mejora de concurrencia es un ajuste de configuración, no de arquitectura |
| **RP-05** | G1 no se supera con ACE-Step | Baja-Media | **Crítico** | El plan se detiene en F3 explícitamente; ninguna tarea de F4 en adelante debe iniciarse antes de que G1 esté cerrado — riesgo de arranque anticipado si hay presión de calendario |
| **RP-06** | El checkpoint de stop-loss (`T-25`, fin de F4) se dispara: > 60 % del presupuesto de Fase 1 consumido con < 40 % del alcance entregado | Baja | **Crítico** | Runbook de desmantelamiento ya escrito como parte de `T-25`; la decisión de parar la toma dirección, no el equipo técnico |
| **RP-07** | El hito intermedio (canción end-to-end por CLI, tras `T-45`) revela un fallo de integración entre C-11, C-14 y C-01 que obliga a retrabajar tareas ya dadas por cerradas en F5 o F6 | Media | Medio | Es precisamente la función del hito: encontrar este fallo **antes** de construir el frontend (`T-46`–`T-48`, 38 h), no después |
| **RP-08** | Sin usuarios piloto activos al cierre de F8, no hay forma de iniciar la «puesta en uso» que precede a la Fase 2 y al cómputo futuro de G3 | Media | Medio | Nombrar usuarios piloto es condición de F1, verificada antes de arrancar cualquier desarrollo — no es una tarea de F9 |

---

## 10. Criterios de cierre del plan

Este plan se considera `completado` cuando:

- [ ] Las 54 tareas de `tasks.md` (incluida `T-85`, ampliación ratificada el 2026-08-18) están en estado `completado` o `cancelado` (con justificación documentada si se cancela alguna).
- [ ] G1 y G1-bis están superados con acta firmada por el supervisor musical (`evaluation.md` §10.2).
- [ ] El checkpoint de stop-loss (`T-25`) se ejecutó sin disparar la parada, o si se disparó, la decisión de dirección quedó documentada.
- [ ] Todos los criterios de aceptación de `spec.md` §5.2 para C-01, C-02, C-10a, C-11, C-12, C-13 y C-14 están verificados con evidencia (no solo marcados).
- [ ] El hito intermedio (canción end-to-end por CLI) quedó documentado con su evidencia (logs, artefacto generado, manifiesto emitido).
- [ ] El runbook de desmantelamiento y el checkpoint de stop-loss están archivados en `docs/runbooks/`.
- [ ] Existe handoff escrito hacia la Fase 2 (C-10b, C-06, C-05), condicionado explícitamente a que I-13 e I-13b tengan respuesta.
- [ ] `docs/roadmap/README.md` refleja el plan como `completado` y enlaza la evidencia de cierre.

**Nota sobre `test-plan.md`.** Generado el 2026-08-18 a petición expresa: [`test-plan.md`](./test-plan.md) cubre con 23 bloques `E2E-01`…`E2E-23` la Fase 0+1 (aprobado y ejecutable), con 11 bloques `E2E-24`…`E2E-34` la Fase 2 (F10) y Fase 3 (F11) marcados como bloqueados hasta que sus gates se superen, con 4 bloques `E2E-GPU-01`…`E2E-GPU-04` la suite nocturna con GPU real y presupuesto acotado (`E2E-GPU-04` añadido en la ampliación del mismo día: generación real con `GPU_PROVIDER=local`), y con 6 checklists `M-01`…`M-06` la parte manual (escucha de humo, UX de espera honesta, accesibilidad con lector, revisión visual, certificado por legal, teclado del reproductor). Lo consume el agente `qa` del ciclo. `T-01`…`T-84` de `tasks.md` no se han modificado más allá de `T-85`; la trazabilidad E2E↔T-XX↔criterio vive en `test-plan.md` §9.

**Nota sobre Jira.** No se ha encontrado `.claude/jira.json` con opt-in activado, así que no se ha volcado ninguna tarea a Jira. El volcado está disponible vía la skill `jira-sync` en cuanto el proyecto lo active.

---

## 12. Fases condicionadas (pre-planificación)

> 🔒 **Esto no es una autorización de gasto.** Lo único aprobado sigue siendo Fase 0 + Fase 1 (§1–§11, 39.360 € incl. `T-85`). Esta sección detalla, con el mismo nivel de granularidad que F1–F9, el trabajo de las Fases 2 y 3 de `evaluation.md` §7–§10, a petición expresa del usuario para tener **toda la iniciativa planificada** de antemano. Cada sub-fase (`F10`, `F11`) está **bloqueada por su gate**, y sus tareas en `tasks.md` nacen en estado `bloqueada (gate)`. Nada de lo que sigue se ejecuta sin que su gate se supere primero, y tener el detalle escrito no cambia ese hecho.

### 12.1 F10 · Fase 2 — Trazabilidad completa, stems y asistente de letras (131 h)

**Bloqueada por:** G1 y G1-bis ya superados (heredado de F3/F5 de este mismo plan) **+ Fase 1 en uso** (usuarios piloto activos, criterios de aceptación de C-01…C-14 verificados con evidencia) **+ I-13 resuelta** (licencia de watermarking comercialmente limpia) **+ I-13b resuelta** (licencia de los pesos de Demucs).

| Característica | Horas base | Horas c/margen | Coste € (c/margen) | Tokens in/out (M, base) | Tareas |
|---|---|---|---|---|---|
| C-10b — C2PA, WORM, certificado, watermarking | 67 | 80,4 | 4.020 € | 3,35 / 0,47 | `T-54`…`T-58` |
| C-06 — Stems separados | 40 | 48,0 | 2.400 € | 2,50 / 0,35 | `T-59`…`T-62` |
| C-05 — Asistente IA de letras | 24 | 28,8 | 1.440 € | 0,90 / 0,13 | `T-63`…`T-66` |
| **Total F10** | **131** | **157,2** | **7.860 €** | **6,75 / 0,95** | **13 tareas** |

**Riesgo declarado sin resolver.** I-13 (licencia de watermarking) sigue **abierta** a fecha de esta pre-planificación (`evaluation.md` §4); `T-57` (20 h) es la tarea con mayor probabilidad de replanificarse si no aparece una librería con licencia comercial limpia y robusta a transcode MP3 320 — ver la ficha de C-10b en `evaluation.md` §7, que ya advierte del riesgo de licencia circular contra la regla 5 del registry.

**Dependencia hacia atrás.** La primera tarea de F10 (`T-54`) depende de `T-53` (verificación final y cierre de la Fase 1) además del gate compuesto de arriba: no tiene sentido firmar C2PA sobre un manifiesto cuya propia Fase 1 aún no ha superado su verificación de cierre.

### 12.2 F11 · Fase 3 — Control creativo avanzado (276 h)

**Bloqueada por:** el gate **G3 de adopción** (`evaluation.md` §10.1), medido tras **1 mes de uso real** de la Fase 1+2: ≥ 100 generaciones acumuladas, ≥ 3 usuarios activos (que hayan generado en las últimas 2 semanas), ≥ 1 pista usada en una producción real entregada, y encuesta de satisfacción ≥ 4/5 entre los usuarios piloto. Además, la **matriz de capacidades verificadas** de `T-07` debe confirmar `SECTION_INPAINT` y `AUDIO_TO_AUDIO` en los adapters registrados; si sale vacía, C-07 y C-08 se replantean o se caen antes de gastar estas 220 h combinadas.

| Característica | Horas base | Horas c/margen | Coste € (c/margen) | Tokens in/out (M, base) | Tareas |
|---|---|---|---|---|---|
| C-07 — Extender / regenerar secciones | 140 | 168,0 | 8.400 € | 10,50 / 1,47 | `T-67`…`T-74` |
| C-08 — Cover / remezcla | 80 | 96,0 | 4.800 € | 6,00 / 0,84 | `T-75`…`T-79` |
| C-03 — Selector de voz | 56 | 67,2 | 3.360 € | 5,50 / 0,77 | `T-80`…`T-84` |
| **Total F11** | **276** | **331,2** | **16.560 €** | **22,00 / 3,08** | **18 tareas** |

**Dependencia hacia atrás.** La primera tarea de F11 (`T-67`) depende del cierre de F10 (`T-66`) **y** del gate G3: ninguna tarea de control creativo avanzado arranca solo porque F10 esté técnicamente terminada — hace falta adopción demostrada.

### 12.3 Presupuesto ampliado — ledger completo (Fases 0–3)

| Bloque | Horas base | Horas c/margen | Coste € (c/margen) | Estado presupuestario |
|---|---|---|---|---|
| Fase 0 + Fase 1 (F1–F9, §1–§11) | 656 | 787,2 | **39.360 €** | ✅ **Ratificado íntegramente el 2026-08-18** (640 h/38.400 € originales + 16 h/960 € de `T-85`, D-29) |
| Fase 2 (F10, §12.1) | 131 | 157,2 | **7.860 €** | 🔒 Condicionado a gate (G1/G1-bis + Fase 1 en uso + I-13/I-13b) |
| Fase 3 (F11, §12.2) | 276 | 331,2 | **16.560 €** | 🔒 Condicionado a gate (G3 de adopción) |
| **Subtotal condicionado a gates (F10+F11)** | **407** | **488,4** | **24.420 €** | — |
| **TOTAL ledger planificado (Fases 0–3)** | **1.063** | **1.275,6** | **63.780 €** | 39.360 € están aprobados/ratificados hoy; 24.420 € son pre-planificación condicionada a gate |
| Fase 4 (anexo, §13, informativo) | 575 | 690,0 | 34.500 € | ❌ No-go — sin tareas; no suma al total anterior |

**Léase sin ambigüedad:** el importe **ratificado** que se puede gastar hoy es **39.360 €** (Fase 0+1 completa, incluida la ampliación `T-85`/D-29, ratificada el 2026-08-18). Los **24.420 €** de Fases 2+3 son una estimación planificada para que dirección no tenga que encargar un plan nuevo cuando cada gate se supere — no son un compromiso de gasto, y la línea de Fase 4 se muestra solo para que el lector entienda la magnitud completa de la iniciativa, no porque forme parte del ledger ejecutable.

### 12.4 Tokens y productividad IA — Fases 2+3

| Métrica | F10 (Fase 2) | F11 (Fase 3) | F10+F11 |
|---|---|---|---|
| Horas humanas base | 131 h | 276 h | 407 h |
| Horas IA (ratios de `evaluation.md` §7: C-10b 0,20 · C-06 0,25 · C-05 0,15 · C-07 0,30 · C-08 0,30 · C-03 0,39) | 27,0 h | 82,4 h | 109,4 h |
| Supervisión (25 %) | 6,75 h | 20,6 h | 27,35 h |
| Horas totales (IA + supervisión) | 33,75 h | 103,0 h | 136,75 h |
| Horas ahorradas | 97,25 h | 173,0 h | 270,25 h |
| **Ahorro** | **74,2 %** | **62,7 %** | **66,4 %** |

**Por qué F11 ahorra menos que F10.** C-03 (ratio 0,39) es trabajo de curación y escucha, poco comprimible por un agente — el mismo patrón que explica por qué el catálogo completo (62,2 %, `evaluation.md` §9.2) ahorra menos que la Fase 0+1 de este plan (75,5 %, §7). F10 y F11 confirman esa tendencia, no la contradicen.

> ⚠️ **Estimación, no medición**, igual que el resto de este documento (§7). Estas cifras usan los mismos ratios y supuestos de `evaluation.md` §5 y no se han recalibrado con datos reales porque **F10 y F11 no se han ejecutado todavía**.

---

## 13. Anexo — Fase 4 (marcador condicional, no forma parte de este plan)

> ❌ **No-go vigente.** Esta sección **no es un plan**: es un marcador de qué contendría la Fase 4 y qué la desbloquearía, para que quede constancia sin generar tareas ejecutables. `tasks.md` **no tiene** tareas `T-XX` para esta fase, y así debe seguir hasta que exista una **nueva evaluación y ratificación explícita**, igual que se hizo con la Fase 0+1 el 2026-08-18.

| Característica | Horas base (rango) | Coste € base | Qué contendría | Qué la desbloquearía |
|---|---|---|---|---|
| **C-09 — Fine-tuning de modelos propios** | 400 h (300–500) | 20.000 € (+ 626–1.095 €/ciclo de GPU de entrenamiento) | Pipeline de dataset con metadatos de licencia por pista, captioning automático (HeartCLAP) con control de calidad, arnés de entrenamiento LoRA/completo con checkpointing, orquestación de GPU de entrenamiento, tracking de experimentos, protocolo de evaluación contra el modelo base (método de G1), publicación en el registry con promoción y rollback en un paso | **I-03** (catálogo musical licenciado con derechos de entrenamiento, hoy sin respuesta) **+** un perfil de ML engineer contratado o subcontratado (I-01 confirma que no consta hoy en el equipo) |
| **C-04 — Clonación de voz propia** | 175 h (150–200) | 8.750 € | RVC v2 / YingMusic-SVC, segunda etapa GPU, subida y validación de dataset de voz por locutor, flujo de consentimiento (identidad, alcance, fecha, texto firmado) como bloqueo duro, borrado efectivo del derivado (audio + dataset + **pesos**) con prueba automatizada, watermarking (mismo condicionante I-13 que C-10b), bucle de evaluación de calidad, panel de gestión de voces y permisos | **DPIA archivada** antes de la primera línea de código, **base jurídica RGPD** explícita para el tratamiento de un dato biométrico (la voz), y el **flujo de consentimiento y de borrado** diseñados y aprobados por legal/DPO antes de construir nada |
| **Total Fase 4** | **575 h** | **34.500 €** | — | — |

**Antes de que esta fase pueda convertirse en un plan con tareas ejecutables** hace falta, como mínimo:

1. Respuesta a **I-03** (¿existe catálogo musical licenciado?) — sin ella, C-09 no tiene con qué entrenar, y entrenar con material no licenciado reproduciría exactamente el problema que motivó la iniciativa.
2. **Perfil de ML engineer confirmado** en el equipo (I-01) — C-09 es ingeniería de ML con evaluación empírica, no desarrollo de aplicaciones.
3. **DPIA y base jurídica RGPD** para C-04 — la voz identificable es dato biométrico; no es un formulario de consentimiento genérico.
4. Una **nueva evaluación** (`evaluator`) que ratifique estas 575 h con la información anterior ya resuelta, y su **ratificación explícita por el usuario**.

**Esta cifra (575 h / 34.500 €) es la misma de `evaluation.md` §8–§9** — no se ha reestimado aquí porque no hay información nueva que la cambie; se referencia únicamente para que el ledger de la iniciativa quede completo sin fingir que existe un plan donde no lo hay.

> 🆕 **Nota informativa (2026-08-18, hallazgo HF — no cambia el no-go ni las 575 h/34.500 €).** El repo oficial `ACE-Step-1.5` (MIT) incluye entrenamiento **LoRA de un clic** desde su Gradio: 8 canciones, ≈1 hora en una RTX 3090 de 12 GB, con tutorial oficial y toolkit CLI avanzado (LoKR, optimización de VRAM). Esta vía **reduciría potencialmente el esfuerzo de C-09 en un orden de magnitud** frente a las 400 h estimadas para fine-tuning completo — pero **el bloqueo real sigue siendo I-03** (catálogo licenciado): sin dataset, un arnés más barato no resuelve nada, y por tanto **el no-go de la Fase 4 no cambia**. Existe además la serie **XL** de ACE-Step (`xl-base`/`xl-sft`/`xl-turbo`, DiT 4B, ≥12 GB con offload/≥20 GB recomendado, mayor calidad de audio), candidata a considerarse en el spike de Fase 0 (`T-03`/`T-05`, §5 F2) y en el gate G1 si la VRAM local lo permite.

---

## 14. Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-08-18 | Creación del plan a partir de `spec.md` (revisión 3, aprobada) y `evaluation.md` (revisión 3, ratificada por el usuario el 2026-08-18). Alcance: Fase 0 + Fase 1 (640 h base / 768 h con margen / 38.400 €). 53 tareas en 9 sub-fases. Hito intermedio propio del plan: primera canción end-to-end por CLI. Estado `borrador`. | planner |
| 2026-08-18 | **Extensión de pre-planificación** (misma fecha, a petición expresa): añadidos §12 (Fase 2 = F10, 131 h/7.860 €, y Fase 3 = F11, 276 h/16.560 €, con 31 tareas `T-54`…`T-84` bloqueadas por gate) y §13 (anexo informativo de Fase 4, 575 h/34.500 €, sin tareas, no-go vigente). `T-01`…`T-53` y el presupuesto aprobado de Fase 0+1 (38.400 €) quedan intactos. Ledger completo planificado: 1.047 h base / 62.820 € con margen, de los cuales solo 38.400 € están aprobados. Changelog renumerado a §14 por la inserción de §12–§13. | planner |
| 2026-08-18 | **Generación de `test-plan.md`** (misma fecha): 34 bloques `E2E-xx` (23 de Fase 0+1 ejecutables, 11 de Fase 2/3 bloqueados hasta gate) + 3 `E2E-GPU-xx` nocturnos con presupuesto acotado + 6 `M-xx` manuales, modo `MOCK_GPU=1` con adapter determinista, criterios de salida por fase y tabla de trazabilidad E2E↔T-XX↔criterio. Cabecera de cadena de artefactos y §10 actualizados con el enlace. `tasks.md` no se ha modificado. | planner |
| 2026-08-18 | **Ampliación: modo GPU local (D-29, T-85, E2E-GPU-04).** Nueva tarea `T-85` en F6 (C-14): proveedor de aprovisionamiento `local` vía NVIDIA Container Toolkit, con detección de VRAM y offloading automático, además de RunPod (cloud) y mock. Delta: **+16 h base / +19,2 h con margen / +960 €**. Fase 0+1: 640→656 h base, 768,0→787,2 h con margen, 38.400 €→**39.360 €** con margen (38.400 € eran lo ya ratificado; 960 € eran, en ese momento, ampliación de alcance a la espera de ratificación económica). Tokens: 37,60/5,26 M → 38,80/5,43 M in/out con margen. Productividad IA (§7) recalculada con las nuevas horas. Ledger completo (§12.3): 1.047→1.063 h base, 62.820 €→63.780 € con margen. `test-plan.md` añade `E2E-GPU-04`. Cuadro de mando (§1), impacto (§3), decisiones heredadas (§4.2), sub-fase F6 (§5) y presupuesto por sub-fase (§6) actualizados en consecuencia. | planner |
| 2026-08-18 | **Ratificación de la ampliación GPU local (+960 €) y decisión: Fase 0 en GPU local preferente** (misma fecha). Daycry ratifica el delta de `T-85`/D-29: los **39.360 € de Fase 0+1 (656 h/787,2 h) quedan íntegramente ratificados**, sin cifras pendientes — se elimina de §1, §3, §4.2, §5 (F6), §6, §7, §10 y §12.3 cualquier marcador de ampliación sin ratificar. Además, nueva decisión del usuario: **F2 (Fase 0) ejecuta los spikes (`T-03`–`T-08`) y la generación de las pistas de G1 (`T-09`) preferentemente en GPU local**, sin coste cloud salvo la medición de arranque en frío (S-01/S-01b, exclusiva de RunPod); `T-85` (proveedor local de producción con abstracción completa) no se adelanta y sigue en F6. No cambian las horas de desarrollo de F2 (67 h): cambia dónde corre el spike, no cuánto cuesta construirlo. Nota añadida en §3 (impacto) y §5 (F2/F3). | planner |
| 2026-08-18 | **Arranque del ciclo de desarrollo (`/dev-cycle`, Modo B nativo). Transición de estado del plan: `borrador` → `en-progreso`.** Superada la puerta de OK del plan (presupuesto de Fase 0+1 ratificado el 2026-08-18), el ciclo entra en ejecución por su primera sub-fase: **F1 · gate G2 y gobernanza**, cuyas dos tareas (`T-01`, `T-02`) son **no-dev (0 h de desarrollo)**. Se marca `en-progreso` la sub-fase activa y sus dos tareas en `tasks.md` (ledger canónico), y se redactan sus entregables en `gates/`. ⚠️ **`en-progreso` no significa que haya empezado el desarrollo**: `T-01` (gate G2 legal) sigue bloqueando F2 en adelante, y ninguna tarea de F2–F9 puede pasar a `en-progreso` hasta que legal responda por escrito (I-05, I-05b) y estén nombrados supervisor musical y usuarios piloto (I-20). Referencias cruzadas del estado del plan actualizadas en `spec.md`, `evaluation.md` y `docs/roadmap/README.md`. El `test-plan.md` permanece en `borrador` (no se ha ejecutado ningún bloque `E2E-xx`; el agente `qa` no ha intervenido). | dev-cycle (orquestador) |
| 2026-08-18 | **Gate G2 levantado y gobernanza parcial. F1 cerrada a medias; la Fase 0 sigue bloqueada, pero ya no por legal.** El propietario de la iniciativa (Daycry) comunica que **legal no es un bloqueo** y aplica la **fila 1 de la matriz de G2 («sí total»)**: se ejecuta la **Fase 1 completa, 656 h / 39.360 €**, sin recorte ni tope adicional. `T-01` → `completado` con **deuda documental declarada** (informe escrito de legal sin archivar, **I-05b sin respuesta**, ToS de Suno sin verificar —lo que bloquea la línea base ciega de G1—, Anexo A sin firmar). Además, Daycry asume el rol de **supervisor musical** acumulándolo al de responsable de la iniciativa: `T-02` → sigue `en-progreso` con **1 de 3 criterios**, y quedan registradas tres consecuencias como riesgo no validado (acumulación de los votos de calidad y continuidad; **faltan 2 de los 3 evaluadores**, con lo que **G1 no es convocable** y el umbral «2 de 3 evaluadores» es inalcanzable; sin usuarios piloto, G3 no será medible). **El bloqueo real de la Fase 0 pasa de ser legal a ser de gobernanza.** Decisión asociada del mismo día: **se respeta el gate G1** — no se adelanta nada de C-13 (`T-10`…`T-25`), y de la Fase 0 se construye solo lo que es código. | dev-cycle (orquestador) |
| 2026-08-18 | **Hallazgos HF 2026-08-18 registrados como candidatos** (SilentCipher/AudioSeal para I-13, Demucs CC-BY-NC confirmado en I-13b, MiniMax-Music3 candidato condicional con pregunta añadida a G2, vía LoRA en anexo F4, XL en spikes). Registro informativo verificado contra fuentes primarias, **sin cambio de horas, coste, fases ni estados**: siguen vigentes 656 h base / 39.360 € (Fase 0+1) y 1.063 h / 63.780 € (ledger completo). Nota añadida en §5 (F2, vía XL de ACE-Step) y en §13 (anexo Fase 4, vía LoRA); ver también `spec.md` §10/§11.1, `evaluation.md` §4/§7 y `tasks.md` (nota en `T-01` y checkbox opcional en `T-03`). | planner |
| 2026-09-01 | **Corrección de coherencia tras revisión integral (`revision-2026-09-01.md`).** (a) Fila «Estado» del cuadro de mando (§1) reescrita para reflejar la realidad vigente: `T-01` está `completado` (G2 levantado el 2026-08-18, fila 1 «sí total») y el bloqueo vigente es de **gobernanza** (`T-02` en-progreso, I-20: faltan 2 de 3 evaluadores de G1 y usuarios piloto sin nombrar); F2 en adelante bloqueada por `T-02`, no por `T-01`. (b) Banner de cadena de artefactos: «3 `E2E-GPU-xx`» → **4 bloques `E2E-GPU-xx`** (`E2E-GPU-04` añadido con D-29). (c) Frontmatter `actualizado: 2026-09-01`. Sin cambio de horas, coste ni alcance. | revision-2026-09-01 |
| 2026-09-01 | **Ampliación PROPUESTA: instalador del runner GPU local (`T-86`, D-30) — pendiente de ratificación económica, NO autorizada.** Registrada en §5 (F6) y §6 como propuesta separada: CLI/script que implanta el modo `GPU_PROVIDER=local` (D-29) en una máquina nueva — preflight automatizado de GPU/VRAM/driver NVIDIA/Docker/NVIDIA Container Toolkit con mensaje accionable por carencia, pesos `safetensors` verificados por **SHA-256** (D-14), escritura de la config local (perfil compose `gpu-local`, guardarraíl **G-01** `ACE_STEP_REQUIRE_GPU=1` en los modos de medición) y desinstalación limpia; fuera de alcance GUI, auto-update y empaquetado firmado de Windows. **Delta +32 h base / +38,4 h con margen / +1.920 €**, rango 24–40 h según el cierre de la nueva incógnita **I-22** (SO objetivo y quién mantiene el instalador tras la entrega, ligada a I-16). **Ninguna cifra de este plan cambia**: F6 sigue en 112 h/6.720 €, el presupuesto de §6 en **656 h / 787,2 h / 39.360 €** y el ledger ampliado de §12.3 intacto; el cuadro de mando (§1), la productividad IA (§7) y los criterios de cierre (§10) **no se recalculan** hasta que el delta se ratifique. Si se ratificase: F6 144 h/8.640 €, Fase 0+1 688 h/825,6 h/**41.280 €**, ledger completo 1.095 h/65.700 €. Ítem de ratificación añadido a `pre-dev-checklist.md` (sección B, CS-49). | evaluator |
