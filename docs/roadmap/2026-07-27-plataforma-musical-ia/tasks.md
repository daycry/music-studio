---
tasks: tasks.md
titulo: Tareas — Plataforma musical IA (Fase 0 + Fase 1)
slug: plataforma-musical-ia
fecha: 2026-08-18
actualizado: 2026-09-02
autor: planner
plan: ./improvement-plan.md
generacion:
  fuente: estimado
  motivo: "usage-meter.py no encontrado en agent-kits/shared del entorno de ejecución. Misma medición que improvement-plan.md."
---

# Tareas: Plataforma propia de generación musical por IA — Fase 0 + Fase 1

> ⚠️ **Este fichero es el ledger canónico de progreso de la iniciativa.** El estado de cada tarea (`pendiente` → `en-progreso` → `en-revision` → `completado`/`cancelado`) se actualiza **aquí**, no en otro sitio. Lo consumen `implementer`, `qa` y cualquier orquestador de ciclo de desarrollo (incl. SDD externos) — ver `docs/CONVENTIONS.md` regla 4. No crear un ledger paralelo.
>
> 🔒 **Extensión de pre-planificación (2026-08-18).** Las tareas `T-54`…`T-84` (Fases F10 y F11, más abajo) son **pre-planificación condicionada**: describen el trabajo de la Fase 2 y la Fase 3 de `evaluation.md` con el mismo detalle que `T-01`…`T-53`, pero **ninguna autoriza gasto**. Nacen en estado `bloqueada (gate)` y no pueden pasar a `pendiente`/`en-progreso` hasta que su gate se supere (ver la cabecera de cada fase). La Fase 4 **no tiene tareas** en este documento — es un anexo informativo en `improvement-plan.md` §13, no planificación ejecutable.

**Plan asociado:** [`improvement-plan.md`](./improvement-plan.md). **Spec:** [`spec.md`](./spec.md) §5.2 (criterios de aceptación por característica). **Evaluación:** [`evaluation.md`](./evaluation.md) §7 (fichas por característica, origen de los desgloses de horas de este documento).

---

## 1. Resumen de progreso

| Sub-fase | Tareas | Estado | Horas est. (base) | Coste € (c/margen) |
|---|---|---|---|---|
| F1 · Gate G2 y gobernanza | T-01, T-02 | completado | 0 h | 0 € |
| F2 · Fase 0 — spikes y protocolo G1 | T-03…T-08 | **en-progreso** *(2026-09-02: `T-05`, `T-06`, `T-07` **completadas** · `T-03` y `T-04` `en-progreso`, les falta la mitad que exige pod de RunPod —aparcado por presupuesto— · `T-08` `en-revision`, pendiente de la firma del propietario)* | 67 h | 4.020 € |
| F3 · Gate G1 (escucha) | T-09 | pendiente | 0 h | 0 € |
| F4 · Cimientos de plataforma (C-13) | T-10…T-25 | pendiente | 214 h | 12.840 € |
| F5 · Trazabilidad + registry (C-10a + C-11) | T-26…T-34 | pendiente | 145 h | 8.700 € |
| F6 · Infraestructura GPU (C-14) | T-35…T-41, T-85 | pendiente *(adelanto parcial de `T-85` hecho en F2: `gpu_tiers.py` — ver su ficha)* | 112 h | 6.720 € |
| F7 · Generación end-to-end (C-01) | T-42…T-48 | pendiente *(adelanto parcial de `T-45` hecho en F2: limitador de picos — ver su ficha)* | 78 h | 4.680 € |
| F8 · Instrumental + auth (C-02 + C-12) | T-49…T-52 | pendiente | 40 h | 2.400 € |
| F9 · Verificación final y cierre | T-53 | pendiente | 0 h | 0 € |
| **Subtotal aprobado y ejecutable (F1–F9)** | **54 tareas** | — | **656 h** | **39.360 €** |
| 🔒 F10 · Fase 2 — Trazabilidad completa, stems, asistente de letras (C-10b+C-06+C-05) | T-54…T-66 | bloqueada (gate) | 131 h | 7.860 € |
| 🔒 F11 · Fase 3 — Control creativo avanzado (C-07+C-08+C-03) | T-67…T-84 | bloqueada (gate) | 276 h | 16.560 € |
| **Subtotal condicionado a gates (F10+F11)** | **31 tareas** | — | **407 h** | **24.420 €** |
| ❌ F12 · Fase 4 (anexo, no-go) | — sin tareas — | n/a | *(575 h, informativo, ver `improvement-plan.md` §13)* | *(34.500 €, no suma)* |
| **TOTAL LEDGER (F1–F11)** | **85 tareas** | — | **1.063 h** | **63.780 €** |
| ⏳ *Ampliación **propuesta** (T-86 · instalador del runner GPU local, D-30) — **no ratificada**, no suma arriba* | *T-86* | *pendiente (sin ratificar)* | *+32 h* | *+1.920 €* |
| *TOTAL LEDGER **si** se ratifica T-86* | *86 tareas* | — | *1.095 h* | *65.700 €* |

✅ **F6 incluye la ampliación de alcance del 2026-08-18 (`T-85`, modo GPU local, D-29): +16 h base / +960 € con margen, ratificada por el usuario el mismo día.** Sin ella, F6 serían 96 h / 5.760 € (cifra original del 2026-07-27).

⏳ **Ampliación PROPUESTA el 2026-09-01 (`T-86`, instalador del runner GPU local, D-30): +32 h base / +38,4 h con margen / +1.920 € — PENDIENTE de ratificación económica.** **No está sumada en las cifras ratificadas**, que siguen siendo **656 h / 39.360 €** (F1–F9) y **1.063 h / 63.780 €** (ledger completo). Si el usuario la ratifica: F6 pasaría de 112 h/6.720 € a **144 h/8.640 €**, Fase 0+1 de 656 h/39.360 € a **688 h base / 825,6 h / 41.280 €** y el ledger completo a **1.095 h / 65.700 €**. Hasta entonces, `T-86` **no se ejecuta**. Rango estimado 24–40 h según el cierre de **I-22** (SO objetivo).

**Léase con la distinción intacta:** de los 63.780 € del ledger completo, **656 h / 39.360 € (F1–F9) son ejecutables hoy y están íntegramente ratificados** (2026-08-18, incluida la ampliación `T-85`/D-29). Los 24.420 € de F10+F11 son pre-planificación bloqueada por gate — no autorizan gasto. F12 (Fase 4) no tiene tareas y no forma parte del total del ledger; se muestra solo como referencia.

> 🔄 **Pasada de coherencia del 2026-09-02 (cierre de F2).** La fila de F2 decía «`T-03`…`T-07` pendientes, bloqueadas por CS-36» y llevaba desfasada desde el 2026-09-01: **CS-36 (pesos) se cerró ese mismo día** y las cinco tareas han avanzado. Estado real hoy: **3 completadas** (`T-05`, `T-06`, `T-07`), **2 en progreso** (`T-03`, `T-04` — a las dos les falta exactamente lo mismo, el pod de RunPod, **aparcado por presupuesto el 2026-09-02**) y **1 en revisión** (`T-08`, esperando la ratificación firmada del propietario). **Ninguna hora ni cifra ratificada cambia** (656 h / 39.360 €). Dos adelantos de alcance de fases posteriores, hechos porque el spike los necesitaba, quedan anotados en su ficha de origen y **no se cobran ni se descuentan de F2**: `gpu_tiers.py` (parte de `T-85`, F6) y el limitador de picos (parte de `T-45`, F7).

**Vocabulario de estados:** `pendiente` · `en-progreso` · `en-revision` · `completado` · `cancelado` · **`bloqueada (gate)`** (estado exclusivo de `T-54`…`T-84`: no puede pasar a `pendiente` hasta que su gate correspondiente se supere). **Prioridad por defecto:** `Alta` (heredada de la spec) salvo que se indique otra.

---

## F1 · Gate G2 y gobernanza previa (0 h dev — bloqueante)

### T-01 · Gate G2 — consulta a legal (procedencia + protegibilidad)

**Descripción:** Formular a legal las dos preguntas del gate (I-05: ¿acepta legal audio con `training_data_declaration: no divulgada` para uso interno y para producciones comerciales de cliente?; I-05b: ¿es protegible/licenciable en exclusiva el output generado sin autoría humana?), con la matriz de resultados pre-acordada (`evaluation.md` §10.1) ya escrita antes de preguntar.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| — (no-dev) | **completado** | ninguna | 0 h dev *(32 h de legal, reservadas y sin consumir)* | — |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g2-matriz-resultados.md`

**Entregable creado:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g2-matriz-resultados.md` (2026-08-18) — consulta escrita completa, en estado `resuelto-favorable`: dos preguntas (I-05 con sus ramas a1/a2, I-05b), contexto técnico para un lector no familiarizado, matriz de resultados de `evaluation.md` §10.1 íntegra, RACI con timebox de 10 días laborables, Anexo A de aceptación de §10.7 (exigido por R-01), acción paralela de las dos ofertas con indemnización y tabla vacía de registro de la respuesta.

**Criterios de aceptación**
- [ ] Las dos preguntas (I-05, I-05b) se han formulado por escrito a legal con la matriz de resultados adjunta. — ⚠️ **deuda documental**: el documento existe y está listo, pero **no consta envío registrado**.
- [ ] Legal responde dentro del timebox de 10 días laborables (o se documenta la escalada a dirección general). — ⚠️ **deuda documental**: no consta informe escrito de asesoría jurídica archivado. **I-05b (protegibilidad/exclusividad) sigue sin respuesta.**
- [x] La decisión resultante (una de las tres de la matriz) queda registrada por escrito y enlazada desde este documento. *(2026-08-18 — `gates/g2-matriz-resultados.md` §10: **fila 1, «sí total»**, decidida por Daycry, propietario de la iniciativa)*

**Subtareas**
- [x] Redactar el documento de consulta con las dos preguntas y la matriz de resultados. *(2026-08-18 — `gates/g2-matriz-resultados.md`)*
- [ ] Enviar a legal con el RACI de `evaluation.md` §10.1 (decisor, timebox, escalado). *(⚠️ no ejecutado: el gate se levantó sin envío formal registrado)*
- [x] Registrar la respuesta y la decisión pre-acordada aplicada. *(2026-08-18 — §10 del documento, fila 1 «sí total»)*

**Notas:** Es la tarea 1 del proyecto entero. Ninguna tarea de F2 en adelante puede iniciarse antes de que esta quede `completado` con resultado favorable (o «sí solo interno» con la decisión de dirección tomada).

> 🆕 **Candidato añadido al lote de preguntas (2026-08-18, hallazgo HF, informativo — no reabre la tarea).** Tercera pregunta candidata para una futura consulta a legal, junto a I-05/I-05b: *¿acepta legal los términos de la **MiniMax-Music3 Community License** (atribución prominente en UI + cláusulas AUP/salvaguardas + umbral de 20 M$) para uso interno y para producciones de cliente?* Motivo: MiniMax-Music3 (huggingface.co/MiniMaxAI/MiniMax-Music3) se apunta como candidato condicional a tercer adapter junto a YuE (`spec.md` §5.3, §11.1). No crea tarea nueva ni cambia el estado `completado` de `T-01`.

**Nota de progreso (2026-08-18, `implementer`):** el entregable documental se redactó y la tarea pasó a `en-progreso`. Ningún criterio marcado en ese momento: los tres dependían de acciones humanas.

**🟢 Cierre (2026-08-18, orquestador `/dev-cycle`):** **el gate G2 queda levantado.** Daycry (7590335+daycry@users.noreply.github.com), propietario de la iniciativa, comunicó que **legal ya no es un bloqueo** y seleccionó la **fila 1 de la matriz — «sí total»**. Consecuencia: **Fase 1 completa según lo ratificado, 656 h / 39.360 €**, sin recorte de alcance ni tope adicional. Registrado en `gates/g2-matriz-resultados.md` (banner de cabecera + §10).

> ⚠️ **Desviación de la regla de cierre, declarada y no disimulada.** `CLAUDE.md` exige que una tarea se cierre solo con **todos** sus criterios de aceptación verificados. Aquí se cierra con **1 de 3**: la tarea pasa a `completado` **por autoridad del propietario de la iniciativa**, no por evidencia documental completa. Queda esta **deuda documental** con dueño y momento de cierre:
>
> | Deuda | Quién | Cuándo, como muy tarde |
> |---|---|---|
> | Archivar el **informe escrito de asesoría jurídica** sobre I-05 | Propietario de la iniciativa | Antes de entregar audio generado a una **producción de cliente** |
> | Obtener respuesta a **I-05b** (¿es protegible y licenciable en exclusiva el output sin autoría humana?) | Asesoría jurídica | Antes de **firmar cualquier exclusividad** con un cliente. No bloquea construir |
> | Verificar los **ToS de Suno** (2 h) | Asesoría jurídica | **Antes de G1**: sin esto no se puede usar la salida de Suno como línea base ciega, y el protocolo la exige |
> | Firmar el **Anexo A** (§8.3, «verdad incómoda») | Dirección | Antes del cierre de la Fase 1 — es la mitigación del riesgo R-01 |
>
> **Lo que este cierre NO desbloquea:** la Fase 0 sigue bloqueada por `T-02` — faltan **2 de los 3 evaluadores** de G1, y el umbral «al menos 2 de 3 evaluadores» es inalcanzable con uno solo.

---

### T-02 · Gobernanza previa — nombramiento de supervisor musical y usuarios piloto

**Descripción:** *(adaptada al modo solo el 2026-09-01 — decisión del propietario: proyecto personal en solitario)* Cerrar la gobernanza de la iniciativa en modo solo: el propietario asume el rol de **evaluador único** de G1/G1-bis (protocolo numérico íntegro, riesgo de independencia aceptado por escrito), el de **usuario piloto** (G3 reinterpretado en modo solo) y documenta la **decisión construir-vs-comprar** (I-20). La versión corporativa original (supervisor musical + 3 evaluadores, 3–5 usuarios piloto con ≥ 2 h/semana, dos ofertas con indemnización de `evaluation.md` §6.5b) se conserva en el gate de comercialización **GC-01** (`gates/gobernanza.md` §8).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| — (no-dev) | **completado** (2026-09-01) | T-01 | 0 h dev | — |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/gobernanza.md`

**Entregable creado:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/gobernanza.md` (2026-08-18) — acta de nombramientos en estado `pendiente-de-nombramientos`: ficha del supervisor musical con sus encargos y la ratificación de los umbrales de `evaluation.md` §10.2 antes de la Fase 0, las 3 filas de evaluadores de G1, las 5 filas de usuarios piloto con los cuatro números de G3, hueco de la decisión construir-vs-comprar con las dos ofertas a archivar, RACI de los gates con nombres, y las reservas sin dueño (propietario operativo/I-16, OPEX ≈ 6.900 €/año, tarifa interna/I-18, 116 h de no-desarrollo).

**Criterios de aceptación** *(adaptados al modo solo el 2026-09-01; los tres verificables en `gates/gobernanza.md`)*
- [x] Rol de **evaluador único** asumido por el propietario y registrado en `gates/gobernanza.md` §2, con el protocolo numérico de G1 íntegro y el riesgo aceptado por escrito. *(2026-09-01)*
- [x] **Usuario piloto = propietario**; G3 reinterpretado en modo solo (≥ 100 generaciones propias, ≥ 1 pista usada en algo real, autoevaluación ≥ 4/5) en `gates/gobernanza.md` §3. *(2026-09-01)*
- [x] **Decisión construir-vs-comprar documentada** en `gates/gobernanza.md` §4 («construir»: aprendizaje, control total y self-hosting; ofertas con indemnización diferidas a GC-01). *(2026-09-01)*

**Subtareas** *(adaptadas al modo solo el 2026-09-01)*
- [x] Registrar en el acta el rol de evaluador único, el riesgo aceptado y la opción recomendada de 1–2 oyentes externos informales. *(2026-09-01 — `gates/gobernanza.md` §2)*
- [x] Reinterpretar G3 en modo solo y dejar sus cuatro números por escrito. *(2026-09-01 — `gates/gobernanza.md` §3)*
- [x] Documentar construir-vs-comprar; las dos ofertas con indemnización pasan a GC-01 (sin sentido en ámbito personal). *(2026-09-01 — `gates/gobernanza.md` §4 y §8)*

**Notas:** Condición del veredicto, no tarea opcional (`evaluation.md` §4, I-20). Sin ella, F2 no arranca.

**Nota de progreso (2026-08-18, `implementer`):** la plantilla del acta se creó (`gates/gobernanza.md`) a la espera de nombramientos, con todos los campos como `⚠️ pendiente`.

**Actualización (2026-08-18, orquestador `/dev-cycle`) — 1 de 3 criterios cubierto:** **Daycry** (7590335+daycry@users.noreply.github.com) asume el rol de **supervisor musical**, además del de responsable de la iniciativa que ya tenía. Registrado en `gates/gobernanza.md` §2.1, §2.3 y §5. La tarea **sigue `en-progreso`**.

> ⚠️ **Tres consecuencias registradas como riesgo, no validadas** (la aceptación es decisión de dirección):
> 1. **G1 no es convocable hoy.** El protocolo exige **3 evaluadores**, al menos 2 supervisor musical o editor de una producción real. Hay **1 de 3**. El umbral de aprobado se define sobre «al menos **2 de 3** evaluadores»: con un solo evaluador es aritméticamente inalcanzable. **Esto, y no legal, es lo que hoy bloquea la Fase 0.**
> 2. **Los votos de calidad y de continuidad quedan en la misma persona.** `evaluation.md` §10.1 los separa a propósito como contrapeso entre «suena lo bastante bien» y «sigue adelante». La regla «el desarrollador no puntúa ni vota» se mantiene intacta.
> 3. **Sin usuarios piloto**, los cuatro números del gate **G3** no serán medibles cuando toque.
>
> **Falta para cerrar `T-02`:** 2 evaluadores más · 3–5 usuarios piloto con ≥ 2 h/semana autorizadas por su responsable · decisión construir-vs-comprar documentada con las dos ofertas archivadas · fechas de disponibilidad comprometidas para G1 y G1-bis. *(Nota histórica: superado por la adaptación a modo solo del 2026-09-01, ver el cierre más abajo.)*

**🟢 Cierre (2026-09-01, modo solo):** **Adaptación a proyecto personal (2026-09-01): la versión corporativa de estos criterios (3 evaluadores, 3–5 pilotos, ofertas) se traslada al gate de comercialización GC-01 de gobernanza.md.** Motivo: decisión del propietario — proyecto personal en solitario, con posible comercialización futura. El propietario (Daycry) asume evaluador único y usuario piloto, y la decisión construir-vs-comprar queda documentada («construir»). Los umbrales numéricos de G1 (7/10 ≥ 4/5, WER ≤ 15 %) y el stop-loss **no cambian**: pasan a ser autodisciplina. `T-02` → `completado`. **El bloqueo de gobernanza de la Fase 0 queda levantado**; el bloqueo restante es de entorno (máquina GPU local, toolkit, pesos — `pre-dev-checklist.md` §A, ítems 5–7).

---

## F2 · Fase 0 — spikes de viabilidad y protocolo de G1 (67 h)

### T-03 · Spike de tiempos de inferencia, VRAM y arranque en frío

**Descripción:** Medir tiempos reales de inferencia de ACE-Step 1.5 en la GPU objetivo, VRAM pico con y sin offloading, y tiempo real de arranque en frío (con y sin caché de imagen de contenedor). Cierra S-01, S-02 e I-07. **Decisión 2026-08-18:** la medición de inferencia y VRAM se ejecuta preferentemente en **GPU local** (máquina de desarrollo ≥ 8 GB, `docker run --gpus all` directo sobre el contenedor de `T-05`, sin la abstracción de proveedor de `T-85`). El **arranque en frío** (scheduling, pull de imagen, pesos) no se puede reproducir en local y **sigue midiéndose contra el pod real de RunPod** — es el único consumo de GPU cloud de esta tarea.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | **en-progreso** (2026-09-02) — pipeline completo y medido en GPU local; falta el arranque en frío de S-01 contra RunPod | T-02 *(completado)* | 24 h | 1,50 M in / 0,21 M out |

**Avance del 2026-09-01 (orquestador `/dev-cycle`).** Se ha construido y verificado el **artefacto de pesos** que esta tarea necesitaba y que no existía publicado (ver `pre-dev-checklist.md` ítem 7-bis / CS-50): `apps/runner/tools/build_artifact.py` fusiona los cuatro componentes upstream de la revisión fijada en `D:\srv\ace-step\weights\ace_step_1_5.safetensors` (6.163.551.450 B, 1.177 tensores, SHA-256 `3faa5ac9…5812d947`), con conversión BF16→FP16 offline (**0 desbordamientos**, 2.181 flush-to-zero sobre 3.074.063.112 elementos) y el latente de silencio convertido **sin ejecutar su pickle**. `--selftest` y `--verify` en verde. También se corrigió el suelo de VRAM (CS-51) con `VRAM_FLOOR_TOLERANCE_MB`, con 13 tests nuevos.
**Lo que sigue abierto y es el grueso de la tarea:** *ninguna* de las mediciones que definen `T-03` está hecha. Falta el **shim `ace_step_shim.py`** (sin él `_resolve_pipeline_factory()` aborta antes de mapear los pesos), y con él los tiempos de inferencia, el perfil de VRAM y el arranque en frío. **Riesgo nº 1 identificado y NO medido:** GP104 ejecuta FP16 nativo a 1/64 del FP32; si cuBLAS no promociona a FP32 en `sm_61`, las 10 pistas de G1 pasan de ~20 min a un orden de horas. **Obligatorio un smoke test cronometrado a 30 s antes de comprometer las 10 pistas.**

**Avance del 2026-09-02 (`implementer`) — arreglado el defecto abierto mas grande de F2: `vram_load`.** El arranque en frio medido el 2026-09-02 era de **709,08 s de `vram_load`** (~12 min solo de cargar el artefacto), lo que rompia la promesa de arranque en frio de 2–6 min que `ui-design.md` le hace al usuario **antes de escribirla en codigo**. Causa medida, no supuesta: el adapter mapeaba el artefacto con `load_file(ruta, device="cpu")` y el shim materializaba **tensor a tensor**, o sea fallos de pagina de 4 KiB sobre el bind mount de Docker, a **10,9–11,9 MiB/s** (`apps/runner/spikes/medir_carga.py`).

Arreglo: **lectura contigua** (`apps/runner/adapters/ace_step/carga_contigua.py`). Los tensores de un `safetensors` estan uno detras de otro, asi que se lee el rango entero de cada tramo de una vez (`readinto`) y los tensores del artefacto son **vistas** de ese buffer, sin una sola copia extra. El plan de tramos se recalcula desde la cabecera en cada arranque y **corta en cuanto un rango deja de ser contiguo**: no se supone el orden, se comprueba (en el artefacto real: 1.492 tensores, cero huecos, nueve tramos por componente). `dit.decoder` se lee **directo a VRAM** por una escalera con buffer de escala de 32 MiB, para no pasar por un pico de 3.005 MiB de RAM en un contenedor de 7,9 GiB.

Dos hallazgos de medicion que van en el codigo por si alguien los deshace:
- **Paralelizar la lectura la hunde.** Con 4–32 hilos la tasa cae a 12–28 MiB/s (D: es un disco mecanico y los hilos lo vuelven acceso aleatorio). Se lee con **un hilo y hacia delante**; 103–119 MiB/s (`apps/runner/spikes/probe_io.py`). El techo fisico son 141–144 MiB/s leyendo el mismo rango desde Windows fuera de Docker.
- **La alineacion del buffer no es un detalle.** Con `bytearray` (que devuelve `pagina + 16`) la carga daba 86,7 MiB/s y el warm-up **subia** a 80,0 s, porque el planificador de 5 Hz corre en CPU. Con el buffer reservado por el asignador de PyTorch (64 bytes) son 118,8 MiB/s y el warm-up baja a 36,8 s.

**A/B completo, misma orden y misma pista de 25 s** (GTX 1070, `ace_step_1_5_lm.safetensors`, 7.181 MiB; el respaldo se activa con `ACE_STEP_CARGA_CONTIGUA=0`, que es como se midio la columna izquierda **hoy**, no de memoria):

| | `load_file` (antes) | contigua (ahora) |
|---|---|---|
| `vram_load` | **641,97 s** | **72,93 / 77,25 s** *(dos corridas)* |
| warm-up | 39,14 s | 36,76 / 39,11 s |
| **arranque en frio** | **681,11 s** | **109,70 / 116,37 s** |
| generacion de 25 s | 127,75 s | 110,63 / 113,06 s |

La pista sale identica antes y despues (RMS -18,22 dBFS, pico -1,0 dBFS, correlacion L/R 0,8656, 13/13 comprobaciones del smoke en verde): esto es una optimizacion de E/S, no un cambio de modelo.

El reparto por componente **no cambia** (`dit.decoder` residente en VRAM, 3.007 MiB; el resto en RAM) ni el guardarrail de VRAM, que ahora tambien se aplica antes de reservar el buffer del cargador. Picos de VRAM de la generacion, iguales o mejores: condicionamiento 7.514 MiB (antes 7.606), difusion 4.217 (4.221), decode 5.583 (5.583). Suite: **423 tests en verde** (376 previos + 47 nuevos en `apps/runner/tests/test_carga_contigua.py`, incluida una ida y vuelta comparada tensor a tensor contra `load_file` y un guardarrail que impide que el reparto del shim y el plan del cargador se separen).

**Sigue abierto:** el arranque en frio de S-01 contra el pod de RunPod (pull de imagen y descarga de pesos) no esta medido y **ningun criterio de aceptacion de esta ficha se marca por esto**: lo medido aqui es el termino de carga del modelo, con imagen y pesos ya locales.

**Avance del 2026-09-02 (cierre de F2) — de «ninguna medición hecha» a «el pipeline genera audio real y está medido».** Todo lo de abajo está ejecutado en la máquina de referencia (GTX 1070 `sm_61`, 8.191 MiB, imagen `ace-step-runner:t05`, `ACE_STEP_REQUIRE_GPU=1`); los informes JSON viven en `D:\srv\ace-step\out\`.

1. **Artefacto con planificador, construido y verificado.** `D:\srv\ace-step\weights\ace_step_1_5_lm.safetensors` — **7.529.590.739 B, 1.492 tensores** (comprobado hoy leyendo la cabecera: `dit` 677 + `text_encoder` 310 + `lm` 310 + `vae` 182 + `aux` 13). El artefacto sin planificador (`ace_step_1_5.safetensors`, 6.163.551.450 B, 1.177 tensores, CS-50) sigue al lado y se conserva.
2. **Viabilidad en Pascal medida — el riesgo nº 1 de esta ficha se cierra en la dirección buena.** fp16 **sí promociona**: no se cae al 1/64 de FP32 que se temía. El que sí muerde es otro y no estaba previsto: **SDPA cae al kernel *mem-efficient* y tarda 282,20 ms frente a 21,87 ms de la atención eager con softmax en fp32**, a las formas reales del DiT. Son **12,9×**, y es silencioso. Por eso `sm_61` fuerza atención eager (`adapters/ace_step/gpu_tiers.py`, punto 3 de su cabecera).
3. **El pipeline completo genera audio real**, 240 s con letra en castellano — con tildes y eñes, que no es cosmético: «sonar» y «soñar» son palabras distintas para el tokenizador. Los metadatos `bpm`/`keyscale`/`timesignature` se envían; antes iban a `N/A`.
4. **Planificador de 5 Hz conectado, con su efecto medido contra una vara de medir honesta.** El contraste no es «suena mejor» sino `d_lm / d_semilla`: cuánto mueve el planificador frente a lo que mueve cambiar la semilla (`apps/runner/spikes/medir_ab.py`, `out/ab-medidas.json`). Ratios sobre el par de 25 s: `rolloff95` **6,5×** · flujo espectral 5,6× · cambios de sección 5,0× · centroide 4,7× · factor de cresta 4,3× · RMS 3,8× · pulso (`acf_env_pico`) 3,7×. **Dos descriptores caen por debajo de 1** (`rango_rms_1s` 0,12 · `std_rms_1s` 0,30): en dinámica de largo plazo el planificador mueve **menos** que la semilla. Va siempre puesto, pero **no sale gratis en esta tarjeta**: ver el punto 6.
5. **Limitador de picos integrado** (`ace_step_shim.py`, `TECHO_LIMITADOR_DB = -1,0` dBFS, ventana de 10 ms de anticipación). Verificado en `out/con-limitador-informe.json`: `pico_dbfs` exactamente **−1,0** y `pico_dentro_de_escala: true`. Es un **adelanto parcial de `T-45`** (F7) — anotado en su ficha.
6. **Perfil por etapas de una pista de 240 s** (`out/libre-informe.json`, planificador activo). Aquí está el dato que faltaba en toda descripción previa de esta tarea:

| Etapa | Tiempo | VRAM pico |
|---|---:|---:|
| **planificación (LM de 5 Hz)** | **615,320 s** | 4.779 MiB |
| condicionamiento | 11,917 s | **7.606 MiB** ← pico real de la generación |
| difusión | 37,363 s | 5.941 MiB |
| decode | 25,099 s | 5.547 MiB |
| escritura | 0,633 s | 4.075 MiB |
| **total** | **690,348 s** | — |

> **La planificación es el 89 % del tiempo**, no la difusión. Cualquier lectura de estos números que cite solo «11,9 + 37,3 + 24,8 s» está describiendo el 11 % de la pista. Corrida de control (`libre-canonica`, mismo brief con etiquetas canónicas): planificación 553,488 s · condicionamiento 7,040 · difusión 36,792 · decode 24,827 · total **622,857 s**. Y **el pico de VRAM está en el condicionamiento (7.606 MiB), no en la difusión (5.941)** — es la distinción que sostiene la aritmética de `T-04`.

**Lo que esto significa para S-02, sin maquillar:** S-02 dice **150 s por pista en GPU de ≥ 24 GB**. Aquí una pista de 240 s cuesta **623–690 s** con planificador, sobre una tarjeta de 2016 con offloading obligatorio. **No es un factor de conversión defendible**: cambian arquitectura (`sm_61` vs `sm_89`), nivel de GPU (`tier3` vs el `tier6b` de la spec) y dtype a la vez. Por eso el criterio 5 sigue abierto.

**Archivos:** `apps/runner/spikes/inference_timing.md` *(⚠️ **no existe todavía**, comprobado el 2026-09-02: hoy las mediciones viven en los informes JSON de `D:\srv\ace-step\out\` y en esta ficha, que **no** es donde el criterio 4 las pide)*, `apps/runner/spikes/vram_profile.py` *(existe)*. Escritos por el camino y no previstos en la ficha: `apps/runner/spikes/{generate_smoke,medir_ab,medir_carga,probe_io,pascal_speed_probe,dit_forward_bench,capability_probe}.py`, `apps/runner/adapters/ace_step/{ace_step_shim,text_conditioning,carga_contigua,gpu_tiers}.py` y `apps/runner/tools/build_artifact.py`

**Criterios de aceptación** *(revisados uno a uno el 2026-09-02: 1 de 6 cumplido, 4 parciales, 1 no cumplido)*
- [ ] ⛔ Tiempo de inferencia por pista medido en GPU ≥ 24 GB (referencia S-02: 150 s totales, ~90 s de inferencia pura de ACE-Step). — **NO cumplido.** Lo medido es en **8 GB**, que no es lo que el criterio pide.
- [ ] 🟡 VRAM pico medida con y sin offloading, documentada frente al suelo de 8 GB y el confort de 24 GB (spec §11.1). — **Parcial:** perfil por etapas medido **con** offloading (pico 7.606 MiB, en el condicionamiento). **Sin** offloading es imposible en esta tarjeta: el suelo residente por proceso ya son 4.013 MiB de 8.191 (ver `T-04`).
- [ ] 🟡 Arranque en frío medido con imagen cacheada (rango esperado 2–6 min) y sin cachear (5–12 min). — **Parcial:** medido el **término de carga del modelo**, con imagen y pesos ya locales: 755,5–778,7 s antes del arreglo de lectura contigua y **109,7–140,2 s después** (reverificado hoy en `out/t05-health-informe.json`: 140,24 s = `vram_load` 83,34 + warm-up 52,48). **Falta lo que S-01 mide de verdad**: *scheduling* del pod, *pull* de la imagen y descarga de pesos, que solo existen en RunPod. Consecuencia registrada como **CS-55** en `pre-dev-checklist.md`.
- [ ] 🟡 Resultados documentados en `apps/runner/spikes/inference_timing.md`, con recomendación de ajuste a S-02/S-02b si los valores medidos difieren. — **Parcial:** los números están medidos y trazados (informes JSON + esta ficha), pero **el fichero no existe**. No es un formalismo: es donde debe vivir la recomendación sobre S-02/S-02b.
- [ ] 🟡 Tiempos de inferencia y perfil de VRAM medidos en **GPU local**; si la GPU local difiere de la L40S objetivo, se documenta el **factor de conversión** aplicado a S-02/S-02b. — **Parcial:** medidos en GPU local, sí. **Factor de conversión, no**: extrapolar de `sm_61` con offloading a `sm_89` sin él sería inventarse un número. Se cierra midiendo, o declarando por escrito que S-02 no se recalibra desde esta tarjeta.
- [x] ✅ El coste cloud de esta tarea se limita a la medición de arranque en frío (imagen cacheada / no cacheada); la medición de inferencia/VRAM no genera gasto de GPU cloud. *(2026-09-02 — **0 € de cloud consumidos**: artefacto, pipeline, planificador, limitador, A/B y perfiles, todo en GPU local. Lo único que habría gastado —la medición de S-01— es justamente lo que sigue sin hacerse.)*

**Subtareas**
- [x] Instrumentar el runner con temporizadores por etapa (scheduling, pull de imagen, descarga de pesos, carga a VRAM, warm-up, inferencia). *(2026-09-02 — `spikes/_timing.py` más el muestreador de VRAM a 40 ms de `generate_smoke.py`: cada informe trae ventana y pico por etapa. `scheduling` y `pull` existen en el instrumento y salen a cero en local, que es lo correcto: no hay pod que planificar.)*
- [ ] 🟡 Ejecutar 10 inferencias con offloading y 10 sin offloading en GPU local, registrar VRAM pico de cada una. — **Parcial:** varias corridas con offloading, con pico por etapa registrado. La rama «sin offloading» **no es ejecutable en 8 GB**: o se declara N/A por hardware, o se ejecuta en una GPU mayor.
- [ ] ⛔ Medir arranque en frío en 3 escenarios contra el pod de RunPod: imagen cacheada, imagen no cacheada, pesos no cacheados. — **Bloqueada:** RunPod **aparcado por presupuesto (2026-09-02)**. Es lo único que separa a esta tarea de estar cerrada.
- [ ] Documentar el factor de conversión entre la GPU local usada y la L40S objetivo, si difieren.
- [ ] 🆕 *(opcional, hallazgo HF 2026-08-18)* Considerar también las variantes **XL de ACE-Step** (`xl-base`/`xl-sft`/`xl-turbo`, DiT 4B, ≥12 GB con offload/≥20 GB recomendado) en la medición, si la VRAM local lo permite.

**Notas:** Los valores medidos aquí recalibran linealmente todo el §6 de `evaluation.md` (coste de GPU). Si difieren de forma material, documentarlo como entrada para una futura revisión de la evaluación, no corregir la evaluación desde esta tarea. GPU local preferente decidida el 2026-08-18 (D-29, `spec.md` confirmación 13); no requiere `T-85` (que añade la abstracción de proveedor en F6) — aquí basta invocar el contenedor de `T-05` directamente.

---

### T-04 · Medición de 2 inferencias concurrentes en la L40S

**Descripción:** Comprobar si caben 2 inferencias simultáneas de ACE-Step en los 48 GB de la L40S sin degradar el tiempo por pista. Si caben, el throughput se dobla a coste cero (`evaluation.md` §6.3, §12.1). **Decisión 2026-08-18:** se ejecuta preferentemente en **GPU local** si su VRAM permite reproducir 2 inferencias simultáneas; si la GPU local no alcanza (referencia: L40S 48 GB frente a los 24 GB típicos de una GPU de desarrollo), se ejecuta contra el pod de RunPod como excepción documentada del modo local preferente de la Fase 0.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | **en-progreso** (2026-09-02) — mitad local cerrada, falta L40S | T-03 | 3 h | 0,19 M in / 0,03 M out |

**Archivos:** `spikes/concurrencia.md` *(escrito)* · `apps/runner/spikes/concurrency_profile.py` *(no creado — solo hará falta para la medición en L40S, ver abajo)*

**🟡 Cierre parcial (2026-09-02, `implementer`) — `en-progreso`, NO `completado`. La tarea tiene dos mitades y solo una está medida.**

La ficha mezclaba dos preguntas distintas y conviene separarlas:

| | Pregunta | Estado |
|---|---|---|
| **P1** | ¿Caben 2 inferencias en la **GPU local de 8 GB**? | ✅ **Medida y cerrada: NO caben** |
| **P2** | ¿Caben 2 (o más) en la **L40S de 48 GB**, y con qué degradación por pista? — *es lo que `T-39` necesita* | ⛔ **PENDIENTE, bloqueada por presupuesto** |

**P1 — medido en GPU local el 2026-09-02** (GTX 1070, 8.191 MiB, `tier3` con offloading, artefacto `ace_step_1_5_lm.safetensors`, pista de 240 s). Aritmética completa en [`spikes/concurrencia.md`](./spikes/concurrencia.md); resumen:

- **Suelo por proceso, en reposo y sin generar nada: 4.013 MiB** (3.007 de `dit.decoder` residente + 1.007 de contexto CUDA/asignador). Deja 4.178 MiB libres de 8.192.
- **Pico de una inferencia: 7.606 MiB, en el condicionamiento** (no en la difusión, que son 5.941 MiB). Reproducido a 7.596 MiB en una segunda ejecución de control.
- **Dos procesos *parados* = 8.026 MiB de 8.191 (98,0 %)**, quedan 165 MiB. El transitorio mínimo de una sola difusión son 1.928 MiB. **Déficit 1.763 MiB, 10,7× el margen.**
- Los dos en difusión: 11.882 MiB (145,1 %). Los dos en su pico: 15.212 MiB (185,7 %).
- **No es un problema de sincronización de etapas, es de suelo:** ni escalonando perfectamente las fases cabe, porque el proceso parado no puede soltar sus 4.013 MiB sin descargar el modelo (709 s de `vram_load` entonces; 72,9 s desde la lectura contigua del 2026-09-02, que no cambia la conclusion).
- **No se lanzaron dos inferencias**, deliberadamente: la aritmética lo desaconsejaba antes de intentarlo y forzarlo tumba el demonio de Docker (ya ocurrió una vez en esta máquina).

**P2 — por qué no se ha medido.** La VRAM local insuficiente **sí es** la causa que esta ficha acepta para ir al pod de RunPod. Pero **el propietario aparcó RunPod por presupuesto (decisión del 2026-09-02)**: la excepción cloud está técnicamente justificada y **no financiada**. La degradación del tiempo por pista con N procesos **no es extrapolable** desde una GTX 1070 `sm_61` a una L40S `sm_89` — hay que medirla. Se desbloquea si se contrata el pod para el arranque en frío de `T-03` y se aprovecha la misma sesión, o con cualquier GPU de ≥ 24 GB.

**Criterios de aceptación**
- [ ] ⛔ Se ejecutan 2 inferencias simultáneas (en GPU local si la VRAM lo permite, o en el pod de RunPod si no) y se mide el tiempo por pista de cada una frente a la ejecución en solitario. — **NO cumplido.** En local es físicamente imposible (dos procesos en reposo ocupan el 98,0 %); en L40S no se ha ejecutado. **El tiempo por pista concurrente sigue sin medir en ningún hardware.**
- [ ] 🟡 Se mide el VRAM pico simultáneo de ambas inferencias. — **Parcial:** medido el pico por proceso (7.606 MiB, ±10 MiB entre repeticiones) y derivada la suma. **No es una medida simultánea**, es una suma de dos medidas individuales.
- [ ] 🟡 Resultado (cabe / no cabe, y con qué degradación) documentado y usado como entrada de `T-39` (despacho FIFO+RR). — **Parcial:** el «no cabe» está cuantificado para 8 GB y el contrato para `T-39` escrito (`concurrencia.md` §8: 1 por GPU por defecto, `max_inferencias_concurrentes` configurable con valor 1, prohibido subirlo sin medición). **Falta la degradación.**
- [x] ✅ Se documenta si la medición se ejecutó en GPU local o en el pod de RunPod, y por qué (VRAM local insuficiente es la única causa aceptada para usar cloud en esta tarea). — **GPU local**, con la causa cloud justificada pero no financiada (`concurrencia.md` §5).

**Subtareas**
- [x] Comprobar la VRAM disponible en la GPU local y decidir si soporta 2 inferencias simultáneas. — **8.191 MiB; no las soporta.**
- [ ] Lanzar 2 procesos de inferencia en paralelo (en local o en el pod de RunPod) y cronometrar. — **Bloqueada:** imposible en local, sin pod por presupuesto.
- [x] Comparar contra la línea base de `T-03` (una sola inferencia). — Perfil por etapas de la pista de 240 s en `concurrencia.md` §3.
- [ ] 🆕 Escribir `apps/runner/spikes/concurrency_profile.py` (arnés de N procesos) **cuando haya GPU de ≥ 24 GB**. No se ha creado: para P1 no hacía falta código, sumar dos perfiles es aritmética.

**Notas:** 3 h que pueden ahorrar un pod completo (~128 €/mes) si el resultado es favorable. Documentar igualmente si no lo es — es una decisión de arquitectura para `T-39`, no una tarea opcional. Es la tarea de F2 con más probabilidad de necesitar el pod de RunPod, por el propio objeto de la medición (capacidad de la L40S, no de la GPU local).

> **Actualización 2026-09-02.** La previsión de la nota se ha confirmado en la peor forma: es la única tarea de F2 que **necesita** el pod y no lo tiene. **El ahorro de ~128 €/mes no se materializa y no debe darse por ganado** en ninguna proyección de `evaluation.md` §6.3/§12.1: en local el resultado es desfavorable y en L40S sigue sin saberse. Consumidas ~1,5 h de las 3 h estimadas (mitad local); la mitad restante se gasta cuando haya GPU de ≥ 24 GB. **`T-04` no bloquea el gate G1** — G1 es escucha de calidad, no capacidad — pero **sí es prerrequisito de `T-39`** (F6), que hasta entonces despacha 1 trabajo por pod.

---

### T-05 · Contenerización mínima de ACE-Step 1.5

**Descripción:** Empaquetar ACE-Step 1.5 en un contenedor mínimo (CUDA, dependencias, pesos en `safetensors`) suficiente para ejecutar el spike y el gate G1. La contenerización completa (con HeartMuLa y refinamientos de producción) se completa en `T-29`, dentro de F5. **Decisión 2026-08-18:** para la Fase 0, este contenedor se ejecuta preferentemente con **`docker run --gpus all` directo sobre una GPU local**, sin la capa de abstracción de proveedor (`GPU_PROVIDER=local|runpod|mock`) — esa abstracción es alcance de `T-85` en F6, no de esta tarea.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | **completado** (2026-09-02) | T-02 *(completado)* | 16 h | 0,80 M in / 0,11 M out |

**Avance del 2026-09-01 (orquestador `/dev-cycle`) — 2 de 4 criterios cumplidos y verificados.** `apps/runner/adapters/ace_step/Dockerfile` (+ `apps/runner/.dockerignore`, en la raíz del contexto, que es donde BuildKit lo busca). Imagen `ace-step-runner:t05` construida (11,5 GB) y **ejecutada con `--gpus all`** sobre la GTX 1070. Elección de base dictada por Pascal: CUDA 13.0 eliminó sm_50–sm_72 y las ruedas cu128 (torch 2.7+) dejaron de traer Pascal, así que se fija `pytorch/pytorch:2.13.0-cuda12.6-cudnn9-runtime` **por digest**, con dos aserciones de build sobre `torch.cuda.get_arch_list()` para que una rueda sin Pascal rompa el build en vez de dejar la GPU muerta en silencio. Evidencia medida dentro del contenedor: `torch 2.13.0+cu126` · CUDA 12.6 · **cuDNN 9.10.2** (por debajo de 9.12.0, que retiró CC 6.1) · `arch_list` con `sm_60` (binariamente compatible con `sm_61`) · GPU detectada `GTX 1070 sm_61` · **matmul fp16 en GPU correcto** · `total_memory = 8.589.672.448 B = 8191 MiB`, que confirma el off-by-one de CS-51 dentro del contenedor. Incidencia resuelta: el primer build falló por **PEP 668** (la base ya no trae conda, sino un Python 3.12 de Debian gestionado por el sistema) → `--break-system-packages`, documentado en el fichero; torch **sigue sin instalarse por pip**.
**Lo que faltaba para cerrar** *(histórico, resuelto el 2026-09-02)*: los dos criterios que dependían del **shim `ace_step_shim.py`** (entregable de `T-03`) — que el contenedor expusiera `load()/generate()/health()/unload()` y que `health()` respondiera tras el arranque en frío. El 2026-09-01 `load()` abortaba en `_resolve_pipeline_factory()` con «shim ausente», que era el fallo correcto y esperado.

**🟢 Cierre (2026-09-02, `implementer`) — los 4 criterios verificados con ejecución, no por lectura de código.**

El shim existe desde el 2026-09-02 y con él se cerró el ciclo de vida entero. Dos evidencias distintas, porque cubren cosas distintas:

| Qué | Cómo se ejercitó | Evidencia |
|---|---|---|
| `load()` + `generate()` | Generación real de 240 s con letra en castellano, planificador de 5 Hz y limitador | `out/libre-informe.json`, `out/libre-canonica-informe.json` (`codigo_salida: 0`, WAV de 48 kHz / estéreo / PCM 16 verificados fuera del contenedor) |
| `health()` + `unload()` | Sonda del ciclo de vida completo, ejecutada hoy en el contenedor | `out/t05-health-informe.json` |

La sonda de `health()` merece detalle, porque es lo que el criterio 3 pide de verdad — no «devuelve algo» sino «contesta **durante** el arranque en frío», que es cuando el orquestador necesita saber si el pod está vivo:

* **antes de `load()`** → `ready=False` con mensaje accionable («sin cargar: llama a `load(ctx)`») y `vram_total_mb=8191`, `vram_free_mb=8191`;
* **durante la carga**, sondeada cada 20 s → `ready=False` a los 20 / 40 / 60 / 80 / 100 / 120 s, cada una informando los segundos transcurridos. La corrutina **no se bloquea** mientras `load()` corre en su hilo;
* **tras el arranque en frío** (140,24 s = `vram_load` 83,34 + warm-up 52,48) → `ready=True`, `vram_free_mb=5149`, con el aviso de tiempos degradados por offloading;
* **tras `unload()`** → vuelve a `ready=False`. La VRAM se suelta.

Un detalle del contenedor que conviene no perder: el `Dockerfile` fija `pytorch/pytorch:2.13.0-cuda12.6-cudnn9-runtime` **por digest** y rompe el build si `torch.cuda.get_arch_list()` no trae Pascal. Es lo que impide que una actualización de rueda deje esta GPU muerta en silencio — CUDA 13.0 eliminó `sm_50`–`sm_72` y cuDNN 9.12.0 retiró CC 6.1.

**Archivos:** `apps/runner/adapters/ace_step/Dockerfile`, `apps/runner/adapters/ace_step/adapter.py`

**Criterios de aceptación** *(los 4 verificados el 2026-09-02)*
- [x] El contenedor arranca y expone `load()`, `generate()`, `health()`, `unload()` según el `MusicModelAdapter` de la spec §3.3. *(2026-09-02 — los cuatro **ejercitados de verdad**, no solo declarados: `load`/`generate` en las generaciones de 240 s, `health`/`unload` en la sonda de ciclo de vida. `apps/runner/contracts.py` define el `Protocol` y `AceStepAdapter` lo satisface.)*
- [x] Los pesos se cargan exclusivamente desde `safetensors` (D-14); ningún `pickle`/`torch.load` sobre checkpoints no confiables. *(2026-09-02 — `assert_safetensors()` en el camino de carga; el artefacto es un único `.safetensors` construido offline por `tools/build_artifact.py`; el único pickle de upstream, `silence_latent.pt`, se convirtió **sin ejecutarlo** y su original vive en cuarentena fuera del volumen montado.)*
- [x] `health()` responde correctamente tras el arranque en frío medido en `T-03`. *(2026-09-02 — `out/t05-health-informe.json`: responde antes, **durante** (cada 20 s, sin bloquearse) y después del arranque en frío, y vuelve a `ready=False` tras `unload()`.)*
- [x] El contenedor arranca con `docker run --gpus all` sobre una **GPU local de desarrollo** (≥ 8 GB) sin necesitar la abstracción de proveedor de `T-85`. *(2026-09-01, reconfirmado el 2026-09-02 en cada corrida: `docker run --rm --gpus all` directo sobre la GTX 1070, sin `GPU_PROVIDER`.)*

**Subtareas**
- [x] Escribir el `Dockerfile` con CUDA + torch + dependencias de ACE-Step. *(2026-09-01 — base fijada por digest, con aserciones de build sobre `get_arch_list()`.)*
- [x] Implementar el adapter mínimo (`load`, `generate`, `health`, `unload`) sin `provenance` completo aún (llega con C-10a en F5). *(2026-09-02 — el propio informe declara en `adapter.no_incluye` lo que **no** trae: manifiesto/`provenance` (T-27), loudness y transcode (T-19/T-45), registry (T-30) y la abstracción `GPU_PROVIDER` (T-85). Es contenerización mínima, y lo dice de sí misma.)*
- [ ] 🟡 Verificar arranque en GPU local con `docker run --gpus all` y, para la medición de arranque en frío de `T-03`, también en el pod de pruebas de RunPod. — **GPU local: hecho.** **RunPod: no**, aparcado por presupuesto (2026-09-02). Esta mitad pertenece al criterio de `T-03`, no a los de esta ficha, y por eso no impide su cierre.
- [ ] 🆕 *(opcional, hallazgo HF 2026-08-18)* Considerar también las variantes **XL de ACE-Step** (`xl-base`/`xl-sft`/`xl-turbo`) en la contenerización de prueba, si la VRAM local lo permite.

**Notas:** Es contenerización **mínima** — suficiente para generar audio con calidad evaluable en G1, no el adapter de producción completo (que incluye `provenance`, validado contra el esquema firmado por legal en `T-27`). El **mismo contenedor** de esta tarea es el que usan `T-04`, `T-09` y, más adelante, `T-85` (D-29) — en Fase 0 se invoca directo, sin la abstracción de proveedor que añade `T-85` en F6.

---

### T-06 · Spike comparativo de modelos

**Descripción:** Comparar de forma estructurada ACE-Step, HeartMuLa y YuE (documentalmente, sin necesidad de contenerizar los tres) contra los criterios de la spec §11.1: licencia, VRAM, arquitectura, fortalezas. Confirma la elección de D-06.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | **completado** (2026-09-02) | T-05 *(completado)* | 8 h | 0,40 M in / 0,06 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/comparativa-modelos.md`

**Entregable creado:** [`spikes/comparativa-modelos.md`](./spikes/comparativa-modelos.md) (2026-09-02, 366 líneas, estado `completado`) — comparativa de ACE-Step 1.5, HeartMuLa y YuE 7B (más MiniMax-Music3 como candidato condicional) con **tres niveles de evidencia marcados en cada afirmación** — `[M]` medido aquí, `[D]` documental de fuente primaria, `[C]` calculado — para que se distinga lo verificado de lo leído. Incluye §8, el eje que de verdad decide: el encaje de cada modelo con la GPU local de 8 GB.

**Criterios de aceptación** *(verificados contra el documento el 2026-09-02; el propio §10 del entregable los recorre)*
- [x] Comparativa documentada de ACE-Step, HeartMuLa y YuE 7B contra licencia, VRAM mínima/confort y capacidades declaradas. *(§2 tabla maestra, §4 ACE-Step, §8 VRAM contra el hardware real.)*
- [x] Confirmación explícita de que ACE-Step es el modelo de G1 y HeartMuLa el segundo adapter (D-06), o documentación de por qué cambia el orden. *(§7 — **D-06 se confirma sin cambios**, con cuatro razones y sin apelar a fe; YuE se queda tercero y condicional.)*

**Subtareas**
- [x] Revisar documentación oficial de los tres modelos (licencia, requisitos de hardware, arquitectura). *(§11, fuentes primarias con fecha de consulta y, donde aplica, revisión fijada.)*
- [x] Contrastar contra los resultados preliminares del contenedor de ACE-Step (`T-05`). *(§3, incluida la comprobación cruzada que identifica el checkpoint empaquetado como `acestep-v15-turbo`.)*

**🟢 Cierre (2026-09-02) — lo que este spike destapa y no estaba en ningún sitio.** El documento no solo confirma D-06; corrige la ficha del modelo. **`spec.md` §11.1 describe, campo por campo, a ACE-Step v1 3.5B y no a ACE-Step 1.5**: seis inexactitudes, de las cuales la primera importa más allá de la pulcritud — **la licencia es MIT, no Apache 2.0**. El manifiesto de procedencia de cada generación registra la licencia de los pesos, y escribir «Apache 2.0» sobre un modelo MIT sería un dato falso en un artefacto que existe **precisamente para ser auditable**. Corregirlo antes de la primera generación con manifiesto (F5) es acción A-1 del spike, y no la cierra esta tarea porque toca `spec.md`.

Otras dos que sí cambian planificación futura, registradas aquí para que no se pierdan:

* **A-2 — `T-29` y `T-34` (G1-bis) no son ejecutables en GPU local.** HeartMuLa declara 4B en F32 (**15,8 GB** de pesos) más HeartCodec 2B en F32 que upstream desaconseja bajar a bf16: el segundo adapter **vuelve a depender de RunPod**, en contra del criterio de coste cloud cero de D-29. Con RunPod aparcado, eso es un bloqueo real de F5, no un matiz.
* **A-3 — `HeartCLAP` no está publicado** (comprobado: ninguno de los repos de la organización en HF lo es; hay issue abierto pidéndolo). `gates/g1-protocolo.md` §6.1 lo nombra **candidato principal para medir CLAP**, que es uno de los umbrales de G1. **Hay que designar suplente antes de `T-09`**, o el gate llega a la sala sin instrumento para uno de sus números. Contrapeso: **HeartTranscriptor-oss sí cabe en local** (0,8B) y es independiente del adapter, así que el **WER de G1 no queda bloqueado** por A-2.

**Notas:** Documental en su mayor parte; no requiere contenerizar HeartMuLa ni YuE en esta tarea. *(2026-09-02: se cumplió así — de los tres modelos **solo uno se ha ejecutado**, y el documento lo dice en su cabecera para que nadie lea §2 como una comparación de calidad. La calidad la decide G1, no este spike.)*

---

### T-07 · Matriz de capacidades verificadas

**Descripción:** Probar empíricamente (no de README) si ACE-Step y, documentalmente, HeartMuLa soportan `SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING` y `CONTINUATION`, con evidencia por modelo. Decide si C-07/C-08 (276 h de Fase 3, fuera de este plan) son viables.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| test | **completado** (2026-09-02) | T-05 *(completado)* | 12 h | 0,60 M in / 0,08 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/spikes/matriz-capacidades.md`

**Entregable creado:** [`spikes/matriz-capacidades.md`](./spikes/matriz-capacidades.md) (2026-09-02, 384 líneas, estado `completado`) — las cuatro capacidades sondeadas **sobre los pesos reales y la GPU real**, no leídas del README, con línea de fondo de ruido establecida antes de interpretar nada (repetir la misma generación en otro proceso da −80,49 dBFS de diferencia: sin ese dato ninguna de las cifras de abajo significaría nada).

| Capacidad | ACE-Step 1.5 turbo | HeartMuLa (documental) |
|---|---|---|
| `SECTION_INPAINT` | **Sí** — región de 5 s regenerada; fuera de ella **100,0000 % de muestras bit-idénticas** tras el empalme | No |
| `CONTINUATION` | **Sí** — 30 s → 45 s, cabeza preservada (coseno 0,997), cola nueva no silenciosa | No hoy |
| `AUDIO_TO_AUDIO` | **Sí, pero degradado** — la fuente dirige la salida (corr. 0,364 frente a 0,022 del control), pero el canal es de **≈ 80 bit/s** | No |
| `VOICE_CONDITIONING` | **Parcial** — el codificador de timbre está entrenado y mueve la salida, pero ocupa **1 de 125 tokens** y no se ha podido probar con una voz real | No (`NotImplementedError` en el pipeline oficial) |

**Criterios de aceptación** *(verificados contra el documento y su evidencia el 2026-09-02)*
- [x] Cada capacidad (`SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING`, `CONTINUATION`) probada empíricamente en ACE-Step, con resultado sí/no y evidencia (audio de prueba). *(2026-09-02 — **9 WAV + 2 informes JSON + 2 sondas + 2 registros** en `D:\srv\ace-step\out\`, con SHA-256 y tamaño de cada fichero en §8 del documento y comando de reproducción publicado. Comprobado hoy: los 15 ficheros `t07-*` están en su sitio.)*
- [x] Matriz documentada y enlazada como entrada de decisión para una futura Fase 3 (no se planifica aquí, solo se deja el dato). *(2026-09-02 — §10 del documento enlaza los tres puntos que la reclaman por nombre: la cabecera del gate de **F11**, `T-70` (C-07) y `T-77` (C-08). El propio documento declara que **no marca tareas ni autoriza gasto**, que es lo correcto.)*

**Subtareas**
- [x] Diseñar un caso de prueba mínimo por capacidad. *(2026-09-02 — §1.2: sin codificador de VAE no hay audio de entrada, así que cada camino se probó con latentes propios del modelo. El límite del método está declarado en §1.4, no escondido.)*
- [x] Ejecutar cada prueba contra el contenedor de `T-05` y registrar el resultado con evidencia de audio. *(2026-09-02 — dos corridas, `codigo_salida: 0`; el código ejercitado es el **de la imagen** (`/app`), con SHA-256 de cada módulo en el informe, y las sondas montadas de fuera en `/probe` sin tocar el repositorio.)*

**🟢 Cierre (2026-09-02) — tres consecuencias que valen dinero.**

1. **C-07 y C-08 no se caen.** Era la pregunta de las 12 h: `SECTION_INPAINT` y `AUDIO_TO_AUDIO` existen, así que la cabecera del gate de F11 («si la matriz sale vacía, C-07/C-08 se replantean») **no se activa**. Pero `AUDIO_TO_AUDIO` viene con la expectativa recalibrada por escrito: lo que hace es *«genera una pista nueva guiada por un boceto de ~80 bit/s de la tuya»*, que **no es lo mismo** que reinterpretar tu grabación. Son dos productos distintos con el mismo nombre, y conviene decidir cuál es C-08 **antes** de las 80 h.
2. **Bloqueo común identificado: falta el codificador del VAE.** El artefacto tiene `vae.decoder.*` (182 tensores) y **cero** `vae.encoder.*`; sin él no hay forma de meter audio del usuario en ninguna de las cuatro. No es un muro: los pesos ya están descargados y verificados en la instantánea local (183 tensores `encoder.*`, **licencia MIT**, 160,8 MiB). El documento estima **15–28 h orientativas** de trabajo destapado, **todo en Fase 3** y **sin incorporar a ninguna estimación** — eso lo hará el `evaluator` cuando F11 se desbloquee.
3. **⚠️ Lo medido es el techo del *checkpoint*, no el del modelo.** La matriz se ejecutó sobre `acestep-v15-turbo`, y el Model Zoo de upstream marca `Extract`/`Lego`/`Complete` como **no soportadas en turbo y sí en `acestep-v15-base`**. Un negativo de esta matriz puede ser propiedad del checkpoint empaquetado y no de ACE-Step. Registrado como **CS-54** en `pre-dev-checklist.md`, con la pista que lo hace caro de ignorar: **`extract` (separación de pistas) está en el vocabulario de tareas del modelo y bajo licencia MIT**, justo el agujero que dejó abierto el hallazgo de los pesos CC-BY-NC de Demucs (I-13b, que hoy bloquea C-06).

**Notas:** 12 h que, según `evaluation.md` §10.3, son la mejor relación información/coste del plan: evitan descubrir en la Fase 3 que 276 h no eran viables. *(2026-09-02: se comportó como se esperaba — no salvó las 276 h de un no-go, pero sí cambió lo que hay dentro de ellas y destapó un prerrequisito de 8–16 h que nadie había visto.)*

---

### T-08 · Protocolo escrito del gate G1

**Descripción:** *(adaptada al modo solo el 2026-09-01, según `gates/gobernanza.md` §2.2)* Redactar el protocolo completo de G1 (`evaluation.md` §10.2): 10 briefs, líneas base ciegas (Suno + librería), rúbrica de 5 dimensiones **con descriptores por nivel**, umbrales numéricos (7/10 con D5 ≥ 4/5, ninguna dimensión con media < 3,0, CLAP ≥ librería en 7/10, WER ≤ 15 % medio / 25 % peor caso), criterio de no-go explícito. **Ratificado por el propietario —evaluador único en modo solo— antes de escuchar nada.** Tres adaptaciones declaradas: (1) evaluador único sin quórum «2 de 3», con los números intactos; (2) los 10 briefs son **propios y realistas** (vídeos, maquetas, encargos ficticios concretos) en lugar de producciones cerradas de Daycry; (3) la verificación de los **ToS de Suno se traslada a GC-01 §8c** y **no se cumple antes de G1**.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | **en-revision** (2026-09-01) | T-02 *(completado)* | 4 h | 0,20 M in / 0,03 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md`

**Entregable creado:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md` (2026-09-01, estado `pendiente-de-ratificacion`) — protocolo ejecutable de G1 en 11 secciones: adaptaciones a modo solo declaradas (§0), bloqueo cuantificado (589 h / 35.340 € de F4–F9, §1), **umbrales fijados el 2026-09-01 con regla de inmutabilidad y precisiones aritméticas** (§2), **rúbrica de las 5 dimensiones con descriptores por nivel 1/3/5 y regla anti-inflación** (§3 — lo que no existía en ningún documento previo), **10 briefs propios propuestos** con seis ejes verificables cada uno (§4), procedimiento de sesión con 3 tomas por serie, reglas anti-sesgo para elegir la línea base de librería, anonimización por script, condiciones de escucha y **normalización de loudness de sesión a −16 LUFS / ≤ −1 dBTP** distinguida del objetivo por destino D-23 (§5), **variante B sin línea base de Suno con los cinco umbrales intactos** (§5.6), medición reproducible de CLAP y WER con lo indeterminable declarado como dependencia de `T-09` (§6), hoja de puntuaciones vacía (§7), regla de decisión go/no-go/replanteo sin ambigüedad con tope de 2 repeticiones (§8), bloque de ratificación pendiente (§9) y política de retención S-11 con prohibición explícita de uso comercial de la línea base de Suno hasta GC-01 §8c (§10).

**Criterios de aceptación** *(reinterpretados al modo solo el 2026-09-01; ver `gates/gobernanza.md` §2.2)*
- [x] Protocolo escrito con los 10 briefs identificados, la rúbrica de 5 dimensiones y los umbrales numéricos de `evaluation.md` §10.2. *(2026-09-01 — `gates/g1-protocolo.md` §2, §3 y §4. Los briefs quedan **redactados y propuestos**; su ratificación es el criterio 2, no este.)*
- [ ] ⚠️ **ABIERTO** — Umbrales ratificados por escrito **antes de la primera escucha**. En modo solo los ratifica el **propietario** (evaluador único, `gobernanza.md` §2.1), no un supervisor musical. **Dueño: el propietario. Momento: antes de que `T-09` reproduzca la primera pista** — preferiblemente antes de generarlas. Bloque de firma preparado y vacío en `g1-protocolo.md` §9; sin él, la sesión **no es válida** (§8.1 del protocolo).
- [ ] 🔁 **REINTERPRETADO — trasladado a GC-01 §8c** — ToS de Suno verificados por legal antes de usar su salida como línea base (S-11). **No se cumple antes de G1 y no se dará por cumplido**: `gobernanza.md` §2.2 (nota final) y `pre-dev-checklist.md` ítem 11 / CS-03 lo trasladan al **gate de comercialización GC-01 §8c**. Mientras siga abierto, el protocolo (§10.4) fija que la línea base de Suno se usa **bajo responsabilidad personal y solo para uso personal**, **prohíbe** cualquier uso comercial o con terceros de resultados comparados contra ella, y ofrece la **variante B** (§5.6) que ejecuta el gate **sin Suno y sin tocar ningún umbral**. **Dueño: el propietario (consulta legal real). Momento: GC-01.**

**Subtareas** *(adaptadas al modo solo el 2026-09-01)*
- [x] Redactar la rúbrica de 5 dimensiones **con descriptores por nivel** y el criterio de no-go. *(2026-09-01 — `g1-protocolo.md` §3 y §2/§8.2)*
- [x] Redactar los 10 briefs **propios realistas** (sustituyen a «producciones ya cerradas de Daycry», `gobernanza.md` §2.2.1), con género, tempo, instrumentación, idioma del canto, duración y uso final. *(2026-09-01 — `g1-protocolo.md` §4, **propuestos, pendientes de ratificación**)*
- [ ] 🔁 ~~Enviar a legal la verificación de ToS de Suno (en paralelo a G2)~~ → **trasladada a GC-01 §8c**; declarada y acotada en `g1-protocolo.md` §10.4.
- [ ] ⚠️ Obtener la ratificación por escrito del **propietario** sobre los umbrales, los briefs, el loudness de sesión y la decisión de usar o no la línea base de Suno. *(Bloque preparado: `g1-protocolo.md` §9.)*

**Notas:** Escribir el protocolo **antes** de escuchar es la corrección explícita de la revisión 1 (`evaluation.md` §10.2): «un gate sin número lo decide quien esté en la sala». En modo solo esa regla **gana peso**, no lo pierde: es la principal mitigación que queda en pie tras perder la independencia desarrollador/juez (`gobernanza.md` §2.1, mitigación 1).

**Nota del 2026-09-02 (cierre de F2) — sigue `en-revision`, y es correcto que siga.** La tarea **no se cierra hoy**: le falta exactamente lo mismo que el 2026-09-01, la **ratificación firmada del propietario** sobre umbrales, briefs, loudness de sesión y uso o no de la línea base de Suno (bloque vacío en `g1-protocolo.md` §9). Nadie que no sea el propietario puede marcar ese criterio. Con `T-05`, `T-06` y `T-07` cerradas, **`T-08` es el único artefacto de F2 que depende de una firma humana**, y por tanto lo que separa a la iniciativa de la puerta de G1.

Tres entradas nuevas de hoy que el protocolo tiene que absorber **antes** de la primera escucha, ninguna de las cuales toca un umbral:

* **Formato de las etiquetas de sección en los 10 briefs.** Medido hoy que cambiar el formato cambia el resultado con todo lo demás idéntico (CS-52). El protocolo no dice hoy qué formato usan los briefs, y si cada uno usa el suyo, la sesión compara cosas distintas.
* **Los briefs no pueden pedir reparto de voces por sección** (dúo hombre/mujer, coro): ACE-Step no lo soporta (CS-53). Un brief que lo pida penalizaría al modelo por no hacer algo que nunca pudo hacer — eso no es medir calidad, es medir mal.
* **`HeartCLAP` no está publicado** y `g1-protocolo.md` §6.1 lo nombra candidato principal para medir CLAP (acción A-3 de `T-06`). Hay que designar suplente **antes de `T-09`**.

**🟡 Cierre parcial (2026-09-01, `implementer`) — `en-revision`, no `completado`.** De los tres criterios de aceptación, **solo el primero está cumplido**: el protocolo existe, con la rúbrica descriptiva, los 10 briefs y los umbrales sin degradar. Los otros dos **no los puede cerrar quien redacta el documento**: el criterio 2 exige la **firma del propietario antes de la primera escucha** y el criterio 3 quedó **trasladado a GC-01 §8c** por la propia acta de gobernanza. Por eso la tarea queda en **`en-revision`** y no en `completado`. **Ningún umbral se ha degradado** (7/10 ≥ 4/5 · ninguna dimensión < 3,0 · CLAP ≥ librería en 7/10 · WER ≤ 15 % medio y ≤ 25 % peor caso · no-go si pierde contra librería en D5 en > 5/10). **Deuda declarada detectada al redactar:** la decisión de **loudness por destino (D-23)** que `gobernanza.md` §2.2.5 exige por escrito **antes de G1** **no tiene tarea propia en F2** (`T-20`, en F4, solo implementa la parametrización); queda registrada como **precondición de `T-09`** en `g1-protocolo.md` §5.5 y §9.1 (ítem 6), con los valores de D-23 propuestos por defecto. **`T-09` sigue bloqueada** por el resto de F2 y, antes que nada, por `pre-dev-checklist.md` ítem 7 / CS-36 (pesos `safetensors` de ACE-Step sin descargar).

---

## F3 · Gate G1 — escucha ciega de ACE-Step (0 h dev — checkpoint)

### T-09 · Ejecutar el gate G1 — escucha ciega y decisión

**Descripción:** Ejecutar el protocolo de `T-08`: generar las 10 pistas con ACE-Step (usando el contenedor de `T-05`), preparar las líneas base ciegas (Suno + librería), anonimizar y presentar a los 3 evaluadores. Recoger la hoja de puntuaciones firmada y aplicar el criterio de decisión. **Decisión 2026-08-18:** las 10 pistas se generan preferentemente en **GPU local** (mismo contenedor de `T-05`, `docker run --gpus all`), a coste cloud cero; solo si la GPU local resulta insuficiente se recurre al pod de RunPod.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| — (no-dev) | pendiente | T-03, T-04, T-05, T-06, T-07, T-08 | 0 h dev *(~9 h de escucha del supervisor musical + 2 evaluadores, fuera de este presupuesto)* | — |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-resultado.md`

**Criterios de aceptación**
- [ ] 10 pistas de ACE-Step generadas + 10 de Suno + 10 de librería, anonimizadas en la misma sesión.
- [ ] Hoja de puntuaciones firmada por los 3 evaluadores archivada.
- [ ] Resultado evaluado contra el umbral (7/10 ≥ 4/5 por 2 de 3, ninguna dimensión < 3,0, CLAP/WER dentro de umbral).
- [ ] Decisión (go / no-go / replanteo) documentada por el supervisor musical y el responsable de la iniciativa. El desarrollador no vota.
- [ ] Las 10 pistas de ACE-Step se generan en **GPU local** salvo excepción documentada; el coste cloud de la Fase 0 en esta tarea es 0 €, al margen del ya contabilizado en `T-03` (medición de arranque en frío).

**Subtareas**
- [ ] Generar las 10 pistas de ACE-Step en GPU local (`docker run --gpus all` sobre el contenedor de `T-05`) con los briefs identificados en `T-08`.
- [ ] Preparar y anonimizar las líneas base de Suno (ToS verificados) y de librería.
- [ ] Sesión de escucha con los 3 evaluadores y recogida de puntuaciones.
- [ ] Aplicar el criterio de decisión y documentar el resultado.

**Notas:** **Bloqueante.** Ninguna tarea de F4 en adelante puede empezar antes de que este checkpoint quede `completado` con resultado favorable. Las pistas de esta tarea viven en la carpeta segregada de evaluación con retención de 12 meses (S-11), no en la biblioteca de trabajo. GPU local preferente decidida el 2026-08-18 (D-29, `spec.md` confirmación 13).

**Nota 2026-09-02 — herramienta de la subtarea 1 lista; la tarea sigue `pendiente` y ningún criterio se marca.** Existe `apps/runner/spikes/g1_generar.py` (documentado en `apps/runner/spikes/README.md` §5.5, 50 tests en `apps/runner/tests/test_g1_generar.py`; suite total 473): lee los 10 briefs de `g1-protocolo.md` §4 en cada arranque —no los copia—, deriva el prompt de estilo de §4.2, valida las letras (etiquetas canónicas, tildes, extensión de §4.1), genera de una en una tras una sola carga con planificador de 5 Hz y metadatos poblados, deja las pistas con nombre ciego y sella el mapa con SHA-256 (§5.4/§5.6), y escribe el árbol de §10.2 con el manifiesto retroactivo simplificado. **Verificado solo hasta el ensayo en seco** (`--dry-run`, exit 0, dentro del contenedor `ace-step-runner:t05`): **no se ha generado ni una pista**, que es decisión del propietario. Estimación medida de la tanda completa (30 pistas, 3 tomas por brief según §5.2): **124-159 min**, carga en frío incluida. **Nivel de GPU detectado en la máquina de desarrollo: `tier3` de 8** (`gpu_tiers.py`) — el script lo escribe en el informe y en cada pista porque un `no-go` medido en tier3 solo dice «no sirve en tier3»; el hardware de referencia de la spec es `tier6b`. **Sigue abierto y no lo cierra ninguna herramienta:** ratificación firmada de §9 (sin ella la sesión no es válida, §8.1), decisión D-23 de loudness por destino, las 10 letras del propietario, las líneas base de librería y la normalización de loudness de sesión de las 30 pistas.

---

## F4 · Cimientos de plataforma — C-13 (214 h)

### T-10 · Monorepo, tooling y contrato OpenAPI

**Descripción:** Estructura del monorepo (apps/web, apps/api, apps/runner, packages/schemas), tooling compartido (linters, tipos), y contrato OpenAPI inicial entre frontend y backend.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-09 | 16 h | 0,60 M in / 0,08 M out |

**Archivos:** `package.json`, `pnpm-workspace.yaml`, `apps/web/`, `apps/api/`, `apps/runner/`, `packages/schemas/openapi.yaml`

**Criterios de aceptación**
- [ ] `docker compose up` (o equivalente) levanta el entorno de desarrollo completo (web + api + postgres + redis + minio/s3 local).
- [ ] Contrato OpenAPI publicado y consumido por tipos compartidos en `packages/schemas`.
- [ ] Linters y formateadores configurados y ejecutándose en pre-commit.

**Subtareas**
- [ ] Configurar workspace del monorepo y herramientas compartidas.
- [ ] Definir el esqueleto de `docker-compose.yml` con todos los servicios locales.
- [ ] Publicar el primer contrato OpenAPI (`/generations`, `/models`, `/library`, `/auth`).

**Notas:** Base de la que dependen prácticamente todas las tareas siguientes.

---

### T-11 · Esquema Postgres y migraciones Alembic

**Descripción:** Esquema inicial: usuarios, proyectos, trabajos, generaciones, voces, modelos registrados, registros de auditoría. Migraciones reversibles con Alembic.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| db | pendiente | T-10 | 20 h | 0,75 M in / 0,11 M out |

**Archivos:** `apps/api/db/models.py`, `apps/api/db/migrations/`

**Criterios de aceptación**
- [ ] Esquema cubre usuarios, proyectos, trabajos, generaciones, voces, modelos registrados y auditoría.
- [ ] Migraciones probadas como reversibles (`upgrade` + `downgrade`) en `stage`.

**Subtareas**
- [ ] Modelar entidades principales y sus relaciones.
- [ ] Escribir la migración inicial con Alembic.
- [ ] Probar `downgrade` sobre una base de datos de prueba.

**Notas:** El linaje (`T-12`) se añade sobre este esquema en la misma sub-fase, no en una migración posterior.

---

### T-12 · Linaje en el esquema desde la primera migración (D-22)

**Descripción:** Añadir `parent_id`, `root_id`, `derivation_kind`, `section_map` (nullable) a la tabla de generaciones, y `source_generation` al manifiesto v1 (coordinar con `T-27`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| db | pendiente | T-11 | 8 h | 0,30 M in / 0,04 M out |

**Archivos:** `apps/api/db/models.py`, `apps/api/db/migrations/xxxx_add_lineage.py`

**Criterios de aceptación**
- [ ] Campos `parent_id`, `root_id`, `derivation_kind`, `section_map` presentes en la tabla de generaciones desde la primera migración.
- [ ] Prueba automatizada de que una generación derivada referencia correctamente a su padre (`parent_id`) y a la raíz de la cadena (`root_id`).

**Subtareas**
- [ ] Extender el esquema de `T-11` con los campos de linaje.
- [ ] Escribir el test de referencia padre→hijo.

**Notas:** D-22. Evita que C-07 (Fase 3, fuera de este plan) tenga que migrar en producción sobre tablas con valor legal.

---

### T-13 · Object storage, URLs firmadas y escritura en dos fases

**Descripción:** Integración con S3-compatible: subida de artefactos con URLs firmadas de alcance por trabajo, y patrón de escritura en dos fases (registro `pending` → subida → confirmación) para evitar huérfanos.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-10 | 16 h | 0,60 M in / 0,08 M out |

**Archivos:** `apps/api/storage/client.py`, `apps/api/storage/two_phase_write.py`

**Criterios de aceptación**
- [ ] Un artefacto solo se considera `succeeded` tras confirmación explícita de subida (registro `pending` → subida → confirmación).
- [ ] Reconciliación diaria detecta y limpia ficheros sin registro y registros `pending` caducados (GC de huérfanos).
- [ ] URLs firmadas tienen alcance por trabajo y caducidad corta (soporta D-15).

**Subtareas**
- [ ] Implementar cliente de storage con generación de URLs firmadas.
- [ ] Implementar el patrón de escritura en dos fases.
- [ ] Job de reconciliación diaria (GC de huérfanos).

**Notas:** Precondición de `T-19` (transcode) y de `T-45` (post-proceso de C-01).

---

### T-14 · Redis + cola de trabajos (idempotencia, DLQ, cuarentena)

**Descripción:** Cola de trabajos con `arq`/Celery, claves de idempotencia, reintentos, DLQ con runbook de reproceso, y cuarentena de *poison jobs* tras 3 intentos fallidos.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-10 | 24 h | 0,90 M in / 0,13 M out |

**Archivos:** `apps/api/queue/client.py`, `apps/api/queue/dlq.py`

**Criterios de aceptación**
- [ ] Un trabajo con la misma `idempotency_key` no se duplica al reencolarse.
- [ ] Tras 3 fallos con el mismo hash de parámetros, el trabajo entra en cuarentena (DLQ) y no se reencola automáticamente.
- [ ] Runbook de reproceso de DLQ documentado (inspección, corrección, reproceso por lotes, registro de quién reprocesó qué).

**Subtareas**
- [ ] Configurar cola con `arq`/Celery sobre Redis.
- [ ] Implementar idempotencia por clave.
- [ ] Implementar cuarentena de poison jobs y DLQ con runbook.

**Notas:** Base de `T-15` (máquina de estados) y de todo el despacho de `T-39` en F6.

---

### T-15 · Máquina de estados del trabajo

**Descripción:** Estados del ciclo de vida de un trabajo (`queued`, `starting`, `running`, `succeeded`, `failed`) y transiciones válidas.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-14 | 12 h | 0,45 M in / 0,06 M out |

**Archivos:** `apps/api/jobs/state_machine.py`

**Criterios de aceptación**
- [ ] Todas las transiciones de estado del flujo de la spec §4 están cubiertas y las inválidas se rechazan.
- [ ] Un trabajo fallido con reintento no consume cuota (criterio de C-01, verificado aquí a nivel de máquina de estados).

**Subtareas**
- [ ] Definir el diagrama de estados y transiciones válidas.
- [ ] Implementar guardas de transición y tests de la máquina de estados.

---

### T-16 · Progreso en tiempo real por SSE/WebSocket

**Descripción:** Canal de progreso en tiempo real desde el worker hasta el frontend (posición en cola, `starting`, `running`, `succeeded`/`failed`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-15 | 12 h | 0,45 M in / 0,06 M out |

**Archivos:** `apps/api/realtime/sse.py`

**Criterios de aceptación**
- [ ] El frontend recibe actualizaciones de estado sin hacer polling.
- [ ] La estimación de espera mostrada incluye el arranque en frío si el pod está apagado (según lo medido en `T-03`).

**Subtareas**
- [ ] Implementar endpoint SSE de progreso por trabajo.
- [ ] Publicar eventos de cambio de estado desde el worker.

---

### T-17 · Biblioteca: listado, filtros, búsqueda

**Descripción:** Vista de biblioteca de pistas generadas, con filtros por proyecto, fecha, modelo, y búsqueda.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-11, T-13 | 16 h | 0,60 M in / 0,08 M out |

**Archivos:** `apps/web/app/library/page.tsx`, `apps/web/components/library/`

**Criterios de aceptación**
- [ ] La biblioteca lista, filtra (por proyecto, fecha, modelo) y permite reproducir cada pista.
- [ ] Los filtros funcionan sobre datos reales de Postgres, no mockeados.

**Subtareas**
- [ ] Endpoint de listado con filtros en la API.
- [ ] Componente de biblioteca en el frontend con filtros y búsqueda.

---

### T-18 · Reproductor persistente y base multipista

**Descripción:** Reproductor persistente (barra inferior tipo Suno) que sigue sonando al navegar, más la base del reproductor multipista que reutilizará C-06 (Fase 2, fuera de este plan).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-17 | 18 h | 0,675 M in / 0,095 M out |

**Archivos:** `apps/web/components/player/PersistentPlayer.tsx`, `apps/web/components/player/MultitrackBase.tsx`

**Criterios de aceptación**
- [ ] El reproductor persiste al navegar entre páginas de la aplicación.
- [ ] Controles básicos (play/pause, seek, volumen) accesibles por teclado (componentes accesibles por defecto, D-25).

**Subtareas**
- [ ] Implementar el reproductor persistente global.
- [ ] Dejar la base de componentes multipista lista para que C-06 la extienda en Fase 2.

---

### T-19 · ffmpeg: transcode FLAC/MP3/WAV + loudness EBU R128 base

**Descripción:** Pipeline de post-proceso base con ffmpeg: transcode a FLAC (almacén) y MP3 320 (descarga), normalización EBU R128.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-13 | 14 h | 0,525 M in / 0,0735 M out |

**Archivos:** `apps/runner/postprocess/transcode.py`, `apps/runner/postprocess/loudness.py`

**Criterios de aceptación**
- [ ] Toda pista generada se transcodea a FLAC + MP3 320 sin pérdida de metadatos.
- [ ] Loudness normalizado a EBU R128 (objetivo por destino se añade en `T-20`).

**Subtareas**
- [ ] Implementar el paso de transcode a FLAC + MP3.
- [ ] Implementar normalización de loudness EBU R128 base.

---

### T-20 · Exportación a 48 kHz con soxr y loudness por destino (D-23)

**Descripción:** Resample a 48 kHz con soxr para exportación WAV a demanda, y objetivo de loudness parametrizado por destino: broadcast −23 LUFS, streaming −14 LUFS, stems sin normalizar.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-19 | 6 h | 0,225 M in / 0,0315 M out |

**Archivos:** `apps/runner/postprocess/resample.py`

**Criterios de aceptación**
- [ ] Exportación WAV disponible a demanda, resampleada a 48 kHz con soxr.
- [ ] Loudness dentro de ±1 LU del objetivo del destino elegido (broadcast −23 / streaming −14 / stems sin normalizar).
- [ ] Objetivo de loudness por destino parametrizable, no un valor único hardcodeado.

**Subtareas**
- [ ] Implementar resample a 48 kHz con soxr.
- [ ] Implementar selección de objetivo de loudness por destino, a definir con el supervisor musical en F2.

**Notas:** El objetivo de loudness por destino se decide con el supervisor musical durante F2 (spec D-23); esta tarea implementa la parametrización, no el valor final si aún no está decidido.

---

### T-21 · Compartición por URL de la app + i18n con next-intl (D-24, D-25)

**Descripción:** «Compartir» devuelve la URL de la pista dentro de la aplicación (requiere sesión), nunca una URL firmada. UI completa en castellano desde el día 1 con `next-intl`, sin cadenas hardcodeadas.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-17, T-18 | 8 h | 0,30 M in / 0,042 M out |

**Archivos:** `apps/web/app/track/[id]/page.tsx`, `apps/web/i18n/es.json`, `apps/web/i18n/config.ts`

**Criterios de aceptación**
- [ ] El botón «compartir» copia/genera la URL de la pista en la aplicación (requiere sesión), no una URL firmada.
- [ ] `next-intl` configurado desde el arranque; ninguna cadena de UI hardcodeada fuera del sistema de traducción.
- [ ] El detalle de pista muestra el certificado de procedencia: hash, nº de registro del ledger y verificación de cadena (E2E-14). *(criterio añadido 2026-09-01 para cerrar hueco de trazabilidad con test-plan; sin cambio de horas)*

**Subtareas**
- [ ] Implementar la vista de pista compartible con control de sesión.
- [ ] Configurar `next-intl` y migrar todas las cadenas de UI existentes a los ficheros de traducción.

---

### T-22 · CI/CD: pruebas, build, despliegue a stage

**Descripción:** Pipeline de CI que ejecuta pruebas (unitarias + integración) y despliega automáticamente a `stage`.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-10 | 16 h | 0,60 M in / 0,08 M out |

**Archivos:** `.github/workflows/ci.yml`, `.github/workflows/deploy-stage.yml`

**Criterios de aceptación**
- [ ] CI ejecuta la suite de pruebas en cada push/PR.
- [ ] Un merge a la rama principal despliega automáticamente a `stage`.

**Subtareas**
- [ ] Configurar el pipeline de pruebas.
- [ ] Configurar el pipeline de despliegue a `stage`.

---

### T-23 · IaC básica y entornos

**Descripción:** Infraestructura como código para `dev`/`stage`/`prod` (Terraform/Pulumi u equivalente ligero).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-10 | 10 h | 0,375 M in / 0,0525 M out |

**Archivos:** `infra/main.tf`, `infra/environments/`

**Criterios de aceptación**
- [ ] Los tres entornos (`dev`, `stage`, `prod`) se pueden crear/destruir de forma reproducible desde IaC.
- [ ] `stage` usa pods GPU efímeros con tope de gasto propio, distinto del de `prod`.

**Subtareas**
- [ ] Definir los recursos base por entorno.
- [ ] Documentar el coste de infraestructura no-GPU por entorno (I-15, `⚠️ no presupuestado` más allá de esta estimación).

---

### T-24 · Observabilidad OTel y coste por generación

**Descripción:** Trazas OpenTelemetry de extremo a extremo (petición → cola → pod → adapter → post-proceso → storage), métricas de cola, `gpu_seconds` y coste por generación.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-14 | 16 h | 0,60 M in / 0,08 M out |

**Archivos:** `apps/api/observability/otel.py`, `apps/runner/observability/otel.py`

**Criterios de aceptación**
- [ ] Existe una traza OTel completa de una generación con `gpu_seconds` y coste asociados, visible de extremo a extremo.
- [ ] Métrica de coste por generación, coste acumulado del mes y coste por usuario/proyecto disponibles.

**Subtareas**
- [ ] Instrumentar API, cola y runner con OTel.
- [ ] Construir la métrica de coste por generación, base de `T-41` (tope de gasto).

---

### T-25 · Checkpoint de stop-loss + runbook de desmantelamiento (D-28)

**Descripción:** Ejecutar el checkpoint obligatorio al cierre de C-13: verificar si se ha consumido > 60 % del presupuesto de Fase 1 con < 40 % del alcance entregado. Escribir el runbook de desmantelamiento de una página.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | pendiente | T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19, T-20, T-21, T-22, T-23, T-24 | 2 h | 0,075 M in / 0,0105 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/runbooks/stop-loss-checkpoint.md`, `docs/roadmap/2026-07-27-plataforma-musical-ia/runbooks/desmantelamiento.md`

**Criterios de aceptación**
- [ ] Presupuesto consumido y alcance entregado de la Fase 1 medidos y comparados contra el umbral (> 60 % gasto / < 40 % alcance).
- [ ] Runbook de desmantelamiento escrito (qué se conserva, baja del proveedor GPU y cierre de facturación, destrucción del resto con constancia).
- [ ] Decisión documentada: continuar o parar, con quién la tomó.

**Subtareas**
- [ ] Calcular el % de presupuesto consumido y el % de alcance entregado a fecha del cierre de C-13.
- [ ] Redactar el runbook de desmantelamiento.
- [ ] Obtener decisión de dirección si el umbral se dispara.

**Notas:** D-28. No es opcional aunque el checkpoint no se dispare: el runbook debe existir igualmente, escrito **antes** de necesitarlo.

---

## F5 · Trazabilidad mínima y model registry — C-10a + C-11 (145 h)

### T-26 · Firma del esquema del manifiesto por legal

**Descripción:** Preparar el documento del esquema del manifiesto v1 e integrar el criterio de legal **antes** de implementar la regla 4 del contrato del registry (D-20).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | pendiente | T-25 | 3 h | 0,15 M in / 0,021 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/manifiesto-v1-esquema.md`

**Criterios de aceptación**
- [ ] Documento del esquema del manifiesto v1 (campos, `manifest_schema_version`, `lyrics_declaration`, `source_generation`) preparado y enviado a legal.
- [ ] Firma/aprobación de legal obtenida y archivada, **antes** de iniciar `T-29`/`T-30` (contenerización de HeartMuLa y contrato del registry).

**Subtareas**
- [ ] Redactar el documento del esquema con todos los campos previstos.
- [ ] Enviar a legal e incorporar su criterio.
- [ ] Archivar la aprobación firmada.

**Notas:** Precondición dura de F5 completa. La regla 4 del contrato del registry (`T-30`) obliga a los adapters a emitir `provenance` en un formato ya firmado — al revés invalidaría la regla (`evaluation.md` D-20).

---

### T-27 · Manifiesto v1: esquema, emisión y verificador multi-versión

**Descripción:** Implementar el esquema del manifiesto v1 (una vez firmado en `T-26`), emisión en cada generación desde la primera pista, invariante en CI de que ninguna pista existe sin manifiesto, `manifest_schema_version` con verificador multi-versión y corpus de manifiestos en CI.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-26 | 23 h | 1,15 M in / 0,161 M out |

**Archivos:** `apps/api/provenance/manifest_v1.py`, `apps/api/provenance/verifier.py`, `apps/api/tests/provenance/corpus/`

**Criterios de aceptación**
- [ ] Invariante en CI: ninguna generación puede existir en la base de datos sin manifiesto asociado.
- [ ] Todo manifiesto emitido incluye `manifest_schema_version`.
- [ ] Verificador multi-versión implementado, con test de CI que corre contra un corpus de manifiestos de todas las versiones emitidas.

**Subtareas**
- [ ] Implementar el modelo de datos del manifiesto v1 según el esquema firmado.
- [ ] Implementar la emisión automática en cada generación.
- [ ] Implementar el verificador multi-versión y el test de CI con corpus.

**Notas:** El manifiesto incluye `lyrics_declaration` (D-21, ver `T-43`) y `source_generation` (D-22, coordina con `T-12`).

---

### T-28 · Ledger append-only con cadena de hashes

**Descripción:** Ledger append-only donde cada registro incluye el hash del anterior, validando la cadena de extremo a extremo desde la primera generación de la Fase 1.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-27 | 12 h | 0,60 M in / 0,084 M out |

**Archivos:** `apps/api/provenance/ledger.py`, `apps/api/tests/provenance/test_ledger_chain.py`

**Criterios de aceptación**
- [ ] Cada registro del ledger incluye el hash del registro anterior.
- [ ] Test que verifica la cadena de extremo a extremo desde la primera generación y detecta una manipulación intermedia.

**Subtareas**
- [ ] Implementar la estructura de encadenamiento de hashes.
- [ ] Implementar el validador de cadena y su test de manipulación.

**Notas:** Object lock (WORM real) y sello diario firmado llegan en C-10b (Fase 2, fuera de este plan) sobre esta misma cadena — «una cadena WORM no admite backfill» es la razón de que esta tarea vaya aquí y no en Fase 2 (D-20).

---

### T-29 · Completar contenerización de HeartMuLa

**Descripción:** Completar la contenerización del segundo adapter (HeartMuLa), sobre la base establecida en `T-05` para ACE-Step.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-27 | 34 h | 1,70 M in / 0,238 M out |

**Archivos:** `apps/runner/adapters/heartmula/Dockerfile`, `apps/runner/adapters/heartmula/adapter.py`

**Criterios de aceptación**
- [ ] El contenedor de HeartMuLa arranca y expone la interfaz `MusicModelAdapter`.
- [ ] Pesos exclusivamente en `safetensors` (D-14).
- [ ] Health check operativo tras arranque en frío.

**Subtareas**
- [ ] Escribir el `Dockerfile` de HeartMuLa (CUDA + torch + HeartCodec).
- [ ] Implementar el adapter con `provenance` emitido contra el esquema ya firmado (`T-26`/`T-27`).

---

### T-30 · Contrato, descriptor, persistencia y versionado inmutable

**Descripción:** Implementar `ModelDescriptor`, `MusicModelAdapter` y las reglas del contrato del registry (spec §3.3), incluido el versionado inmutable `id@version`.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-27 | 24 h | 1,20 M in / 0,168 M out |

**Archivos:** `apps/api/registry/descriptor.py`, `apps/api/registry/contract.py`, `apps/api/registry/versioning.py`

**Criterios de aceptación**
- [ ] Un descriptor con pesos en formato distinto de `safetensors` es rechazado (D-14, regla 9).
- [ ] Un descriptor con `commercial_use: false` es rechazado en producción (regla 5).
- [ ] Un descriptor sin `manifest_schema_version` en su `provenance` es rechazado (regla 4, depende del esquema firmado en `T-26`).
- [ ] `id@version` nunca se reescribe; una actualización publica una versión nueva.

**Subtareas**
- [ ] Implementar `ModelDescriptor` y sus validaciones.
- [ ] Implementar el registro/rechazo de modelos según las reglas del contrato.
- [ ] Implementar versionado inmutable.

---

### T-31 · Dos adapters reales sobre el contrato

**Descripción:** Integrar los adapters de ACE-Step (`T-05`) y HeartMuLa (`T-29`) contra el contrato definitivo de `T-30`, con `provenance` obligatorio emitido correctamente.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-29, T-30 | 24 h | 1,20 M in / 0,168 M out |

**Archivos:** `apps/api/registry/adapters/ace_step.py`, `apps/api/registry/adapters/heartmula.py`

**Criterios de aceptación**
- [ ] Ambos adapters registrados pasan las validaciones de invariantes exactos (esquema, duración, sample rate, canales, loudness objetivo, ausencia de NaN/silencio).
- [ ] Ambos emiten `provenance` completo contra el esquema firmado por legal.

**Subtareas**
- [ ] Conectar el adapter de ACE-Step al contrato definitivo.
- [ ] Conectar el adapter de HeartMuLa al contrato definitivo.

---

### T-32 · Suite de conformidad perceptual

**Descripción:** Suite de conformidad por tolerancia perceptual (D-13): invariantes exactos + CLAP audio-texto y WER de la letra cantada dentro de umbral sobre briefs fijos. Incluye la prueba negativa de aislamiento de credenciales del runner (D-15).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| test | pendiente | T-31 | 20 h | 1,00 M in / 0,14 M out |

**Archivos:** `apps/api/registry/conformance/suite.py`, `apps/api/registry/conformance/test_isolation.py`

**Criterios de aceptación**
- [ ] Los dos adapters registrados pasan la suite de conformidad perceptual.
- [ ] Un tercer adapter ficticio con `commercial_use: false` es rechazado por la suite.
- [ ] Prueba negativa: el runner no puede acceder a artefactos de otro trabajo (D-15).
- [ ] La suite nunca compara por igualdad bit a bit con semilla fija (D-13); la semilla se registra solo para trazabilidad.

**Subtareas**
- [ ] Implementar los invariantes exactos (esquema, duración, sample rate, loudness, ausencia de NaN/silencio, procedencia emitida).
- [ ] Implementar la comparación perceptual (CLAP/WER) sobre briefs fijos.
- [ ] Implementar la prueba negativa de aislamiento de credenciales.

---

### T-33 · Fichas de licencia verificada de las herramientas de Fase 1 (I-13b)

**Descripción:** Ficha de licencia verificada de cada herramienta del pipeline que no es un generador: ffmpeg y sus codificadores, HeartCodec/HeartTranscriptor, pesos de ambos modelos.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | pendiente | T-29 | 5 h | 0,25 M in / 0,035 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/fichas-licencia-fase1.md`

**Criterios de aceptación**
- [ ] Ficha de licencia de ffmpeg/codificadores, HeartCodec/HeartTranscriptor y pesos de ACE-Step/HeartMuLa, cada una con veredicto de uso comercial explícito.
- [ ] Ninguna herramienta con licencia no comercial se integra sin sustitución previa documentada.

**Subtareas**
- [ ] Verificar licencia de ffmpeg y sus codificadores.
- [ ] Verificar licencia de HeartCodec/HeartTranscriptor y de los pesos de ambos modelos.

**Notas:** La regla 5 del registry aplica al pipeline completo, no solo a los generadores (I-13b).

---

### T-34 · Gate G1-bis — escucha ciega de HeartMuLa

**Descripción:** Ejecutar el mismo protocolo de G1 (`T-08`) sobre HeartMuLa, como condición de que su adapter se dé por entregado (D-27).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| — (no-dev) | pendiente | T-29, T-31, T-32 | 0 h dev *(mismo protocolo de G1, ~9 h de escucha, fuera de este presupuesto)* | — |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-bis-resultado.md`

**Criterios de aceptación**
- [ ] Mismo protocolo de `T-08`/`T-09` ejecutado sobre HeartMuLa.
- [ ] Resultado favorable requerido para dar el adapter de HeartMuLa por entregado.
- [ ] Si la adherencia a la letra de ambos adapters resulta insuficiente, se documenta como disparador de la partida condicional de Fase 2 (tercer adapter YuE + router, ≈ 50 h, fuera de este plan).

**Subtareas**
- [ ] Generar las pistas de HeartMuLa con el mismo protocolo de G1.
- [ ] Sesión de escucha con el mismo panel de evaluadores.
- [ ] Documentar la decisión.

**Notas:** Si falla, el adapter de HeartMuLa no se cierra y se replantea el segundo modelo — no bloquea necesariamente el avance a F6/F7 con ACE-Step en solitario, pero sí el cierre completo de F5.

---

## F6 · Infraestructura GPU y orquestación — C-14 (112 h, íntegramente ratificadas — incluida la ampliación T-85, D-29, ratificada 2026-08-18) · + `T-86` **propuesta 2026-09-01, no ratificada, fuera de estas 112 h**

### T-35 · Imagen del runner y caché de imagen en el host

**Descripción:** Imagen del runner (CUDA + torch + dependencias) con caché de imagen en el host — el término dominante del arranque en frío (S-01b).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-25, T-32 | 20 h | 1,25 M in / 0,175 M out |

**Archivos:** `apps/runner/Dockerfile`, `infra/runner/image-cache.tf`

**Criterios de aceptación**
- [ ] La imagen del runner está cacheada en el host, no solo los pesos.
- [ ] El arranque en frío con imagen cacheada cae dentro del rango medido en `T-03` (2–6 min).

**Subtareas**
- [ ] Optimizar el `Dockerfile` del runner para minimizar el tamaño de la imagen.
- [ ] Configurar la caché de imagen persistente en el host/proveedor.

---

### T-36 · Caché de pesos en volumen persistente

**Descripción:** Pesos de los modelos cacheados en volumen persistente, evitando re-descarga entre trabajos del mismo pod.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-35 | 6 h | 0,375 M in / 0,0525 M out |

**Archivos:** `infra/runner/weights-volume.tf`

**Criterios de aceptación**
- [ ] Los pesos de ACE-Step y HeartMuLa persisten entre reinicios del pod en el mismo host.
- [ ] Un pod nuevo sobre el mismo host no vuelve a descargar pesos ya cacheados.

**Subtareas**
- [ ] Configurar volumen persistente para pesos.
- [ ] Verificar persistencia entre reinicios de pod.

---

### T-37 · Aprovisionamiento multiproveedor

**Descripción:** Adaptador de aprovisionamiento on-demand/serverless sobre al menos 2 proveedores de GPU (RunPod como primario).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-35 | 20 h | 1,25 M in / 0,175 M out |

**Archivos:** `apps/runner/provisioning/runpod.py`, `apps/runner/provisioning/secondary_provider.py`

**Criterios de aceptación**
- [ ] El runner puede aprovisionar un pod en el proveedor primario (RunPod) y en un proveedor secundario.
- [ ] La interfaz de aprovisionamiento es común a ambos (no acoplada a RunPod).

**Subtareas**
- [ ] Implementar el adaptador de aprovisionamiento para RunPod.
- [ ] Implementar el adaptador para un segundo proveedor.

---

### T-38 · Keep-warm con idle timeout y pod caliente programado

**Descripción:** Keep-warm de 10 min tras cada trabajo, más pod caliente programado en horario `Europe/Madrid`, laborables, con calendario ajustable por el administrador (D-05b, opción G).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-35, T-36 | 12 h | 0,75 M in / 0,105 M out |

**Archivos:** `apps/runner/scheduling/keep_warm.py`, `apps/runner/scheduling/hot_pod_calendar.py`

**Criterios de aceptación**
- [ ] Tras cada trabajo, el pod permanece activo 10 min (keep-warm) antes de apagarse.
- [ ] El pod caliente sigue el horario `Europe/Madrid`, laborables, con calendario ajustable (festivos, rodajes) por un administrador.
- [ ] Es **un** pod caliente + un efímero de desborde (D-26), nunca 2 pods calientes por defecto.

**Subtareas**
- [ ] Implementar el temporizador de keep-warm.
- [ ] Implementar el calendario de pod caliente con horario configurable.

---

### T-39 · Despacho FIFO con fairness round-robin por usuario

**Descripción:** Política de despacho cola→pod: FIFO con fairness round-robin por usuario (D-26), respetando `max_gpu_seconds` por trabajo.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-37, T-38 | 14 h | 0,875 M in / 0,1225 M out |

**Archivos:** `apps/api/queue/dispatch.py`

**Criterios de aceptación**
- [ ] Un usuario con 20 trabajos encolados no bloquea a los otros usuarios con trabajos pendientes (round-robin).
- [ ] Un trabajo que excede `max_gpu_seconds` se aborta con coste registrado.
- [ ] Si `T-04` confirmó 2 inferencias concurrentes viables, el despacho las aprovecha; si no, se despacha 1 por pod.

**Subtareas**
- [ ] Implementar la cola FIFO con round-robin por usuario.
- [ ] Implementar el corte por `max_gpu_seconds`.

---

### T-40 · Circuit breaker y failover sin pérdida de trabajos

**Descripción:** Circuit breaker por proveedor: con el proveedor primario caído, conmuta al secundario sin pérdida de trabajos en curso.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-37 | 14 h | 0,875 M in / 0,1225 M out |

**Archivos:** `apps/api/resilience/circuit_breaker.py`

**Criterios de aceptación**
- [ ] Con el proveedor primario simulado como caído, el circuit breaker conmuta al secundario y ningún trabajo en curso se pierde.
- [ ] La degradación se anuncia en la UI (estimación de espera ajustada).

**Subtareas**
- [ ] Implementar el circuit breaker con detección de caída del proveedor.
- [ ] Prueba de failover simulando caída del proveedor primario.

---

### T-41 · Telemetría de coste, tope de gasto agregado y kill switch

**Descripción:** Telemetría de `gpu_seconds` y coste por generación; tope de gasto mensual agregado con kill switch en el proveedor (D-17), alertas al 50 % y 80 %.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-39, T-40 | 10 h | 0,625 M in / 0,0875 M out |

**Archivos:** `apps/api/billing/spend_cap.py`, `apps/api/billing/kill_switch.py`

**Criterios de aceptación**
- [ ] El tope de gasto mensual dispara el kill switch en pruebas: al 100 %, se pausa el despacho y se apagan los pods; los trabajos quedan `queued`, no `failed`.
- [ ] Alertas al 50 % y 80 % con destinatario nombrado.
- [ ] El panel de administración permite editar la cuota mensual de un usuario y el cambio se refleja de inmediato (E2E-19). *(criterio añadido 2026-09-01 para cerrar hueco de trazabilidad con test-plan; sin cambio de horas)*

**Subtareas**
- [ ] Implementar el contador de gasto agregado mensual.
- [ ] Implementar el kill switch y las alertas.
- [ ] Prueba de disparo del kill switch en un entorno de pruebas.

---

### T-85 · Proveedor GPU local (`GPU_PROVIDER=local`) con NVIDIA Container Toolkit (D-29)

**Descripción:** Ampliación de alcance del 2026-08-18, **ratificada por el usuario el mismo día**. Añadir un tercer proveedor de aprovisionamiento —`local`— a la abstracción de `T-37`, ejecutando el **mismo contenedor** del runner sobre la GPU del propio host mediante **NVIDIA Container Toolkit**. Perfil `docker compose --profile gpu-local` con detección de GPU/VRAM al arrancar y **offloading automático si < 24 GB** (D-06), selección de proveedor por `GPU_PROVIDER=local|runpod|mock`, y documentación de requisitos (driver NVIDIA, NVIDIA Container Toolkit, VRAM mínima 8 GB).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-35, T-36 | 16 h | 1,00 M in / 0,14 M out |

**Archivos:** `infra/compose/docker-compose.gpu-local.yml`, `apps/runner/provisioning/local.py`, `apps/runner/provisioning/gpu_detect.py`, `docs/roadmap/2026-07-27-plataforma-musical-ia/runbooks/gpu-local-requisitos.md`

**Criterios de aceptación**
- [ ] `GPU_PROVIDER=local` selecciona el adaptador de aprovisionamiento local implementando la misma interfaz que `T-37` (RunPod/proveedor secundario), sin cambios en el resto del pipeline.
- [ ] En una máquina con GPU física ≥ 8 GB, `docker compose --profile gpu-local up` levanta el runner con NVIDIA Container Toolkit y genera **una pista real end-to-end con los mismos contratos observables que el modo cloud** (mismo manifiesto v1, mismos formatos FLAC/MP3, misma cadena del ledger) — validado por `E2E-GPU-04` (`test-plan.md`).
- [ ] Al arrancar, el runner detecta la VRAM disponible; si es < 24 GB activa offloading automático y registra un aviso de tiempos degradados (D-06); si no hay GPU o el driver NVIDIA no está disponible, el **arranque falla con un mensaje claro** (nunca silencioso) indicando el requisito incumplido.
- [ ] Sin GPU física y sin proveedor cloud configurado, el mensaje de fallo es explícito; si `GPU_PROVIDER=runpod` está configurado como alternativa, se documenta cómo redirigir el trabajo (tabla de errores, `spec.md` §6).
- [ ] `max_gpu_seconds` por trabajo se respeta igual que en el modo cloud; se documenta que el tope de gasto agregado mensual (D-17) no aplica en local (no hay facturación por hora de proveedor).
- [ ] Documentación de requisitos (driver NVIDIA, NVIDIA Container Toolkit, VRAM mínima 8 GB / confort 24 GB) publicada en el runbook.

**Subtareas**
- [ ] Implementar el adaptador `local` de la interfaz de aprovisionamiento de `T-37`, sin credenciales de proveedor cloud.
- [ ] Escribir `docker-compose.gpu-local.yml` con el perfil `gpu-local` y la integración de NVIDIA Container Toolkit.
- [ ] Implementar la detección de GPU/VRAM al arrancar y el offloading automático si < 24 GB.
- [ ] Implementar la selección de proveedor por `GPU_PROVIDER=local|runpod|mock`.
- [ ] Redactar el runbook de requisitos (driver, toolkit, VRAM mínima).
- [ ] Verificar en una máquina con GPU real que el flujo end-to-end genera contratos idénticos al modo cloud (soporta `E2E-GPU-04`).

> ⏩ **Adelanto parcial hecho en F2 (2026-09-02) — la tarea sigue en F6 y sigue `pendiente`.** Existe ya `apps/runner/adapters/ace_step/gpu_tiers.py` con **26 tests propios** (`apps/runner/tests/test_gpu_tiers.py`), en verde dentro de la suite del runner. Cubre **una parte** del tercer criterio de esta ficha: la configuración del runner **por nivel de GPU detectado**, en vez de por valores clavados a mano.
>
> **Por qué se adelantó.** Durante `T-03` se fueron fijando a mano decisiones que en realidad dependen de la máquina — si se usa planificador y cuál, qué se descarga a CPU, duración máxima, tamaño de lote — con los valores de una **GTX 1070, que es `tier3` de ocho tramos**. Eso contradice D-29 («detección de GPU/VRAM al arrancar, offloading automático si < 24 GB») y además **falsea cualquier juicio sobre la calidad del modelo**: el hardware de referencia de la spec es `tier6b`, que corre en bf16 sin cuantizar, sin offloading y con el planificador grande. No es el mismo modelo funcionando peor; es otra configuración.
>
> **Qué trae y qué no.** La tabla de tramos está **vendorizada de upstream (MIT) con su procedencia escrita**, no inventada, con cuatro desviaciones documentadas y su motivo: INT8 no existe en Pascal (upstream lo da por hecho de `tier1` a `tier6a`), BF16 tampoco, `sm_61` obliga a atención eager (**12,9×** frente a SDPA, medido) y el suelo de VRAM se calcula sobre el nominal redondeado por CS-51. El módulo **no toca la GPU**: recibe VRAM y capacidad de cómputo como argumentos, y por eso se prueba entero sin tarjeta.
>
> **Lo que sigue pendiente de `T-85`, que es casi todo:** el proveedor `local` de la interfaz de `T-37`, `docker-compose.gpu-local.yml` con el perfil `gpu-local`, la selección por `GPU_PROVIDER=local|runpod|mock`, el runbook de requisitos y `E2E-GPU-04`. **Ninguno de los seis criterios de aceptación se marca** y **no se descuenta ninguna hora de las 16 h**: lo adelantado es un módulo de decisión por nivel de GPU, no la abstracción de proveedor. Cuando se ejecute `T-85`, `gpu_tiers.py` es la entrada natural de su `gpu_detect.py`, no un duplicado a reescribir.

**Notas:** D-29. El runner es el mismo contenedor en los tres modos (cloud, local, mock), no una reimplementación: hereda D-14 (solo `safetensors`), D-15 (aislamiento de credenciales) y D-20 (manifiesto/ledger idénticos) igual que RunPod. Ampliación de alcance registrada en `spec.md` §13 y `improvement-plan.md` §14 — **ratificada por el usuario el 2026-08-18** (delta +16 h base / +19,2 h con margen / +960 €), integrada en los 39.360 € ratificados de Fase 0+1. Distinta de la decisión, misma fecha, de que **la Fase 0 (F2/F3)** use ya GPU local preferente sin esperar a esta tarea: ahí basta invocar el contenedor de `T-05` directamente (`docker run --gpus all`), sin la abstracción de proveedor que introduce `T-85`.

---

### T-86 · Instalador del runner GPU local — preflight, pesos verificados, configuración y desinstalación (D-30)

> ⚠️ **Ampliación propuesta 2026-09-01, PENDIENTE de ratificación económica — no ejecutar sin ella.** Delta: **+32 h base / +38,4 h con margen / +1.920 €** (rango 24–40 h). **No está incluida** en las 112 h de F6 ni en las 656 h / 39.360 € ratificadas de Fase 0+1. Mientras no se ratifique, esta tarea no pasa a `en-progreso` aunque sus dependencias estén cerradas.

**Descripción:** Ampliación de alcance del 2026-09-01 (**D-30**). **CLI/script de instalación** que implanta el runner en **modo GPU local** (`GPU_PROVIDER=local`, D-29) sobre una **máquina nueva**, convirtiendo en repetible lo que hoy es un runbook manual. Cuatro piezas: (a) **preflight automatizado** — detección de GPU, VRAM, driver NVIDIA, Docker y **NVIDIA Container Toolkit** con la comprobación real (`docker run --rm --gpus all …`), y un mensaje accionable por cada carencia; (b) **descarga y colocación de los pesos `safetensors`** con **verificación SHA-256** contra hashes esperados (invariante **D-14**: jamás `pickle`); (c) **selección del modo y escritura de la configuración local** (`GPU_PROVIDER=local|runpod|mock`, perfil `docker compose --profile gpu-local`) con el guardarraíl **G-01** (`ACE_STEP_REQUIRE_GPU=1`) en todos los modos de **medición**; (d) **desinstalación limpia básica**. **Fuera de alcance:** interfaz gráfica, auto-update y empaquetado firmado de Windows (delta aparte si algún SO objetivo lo exigiera).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | pendiente | T-05, T-36, T-85, **+ ratificación económica del delta** | 32 h | 2,00 M in / 0,28 M out |

**Archivos:** `tools/installer/install.py`, `tools/installer/preflight.py`, `tools/installer/weights.py`, `tools/installer/config_writer.py`, `tools/installer/uninstall.py`, `tools/installer/expected_weights.sha256`, `docs/roadmap/2026-07-27-plataforma-musical-ia/runbooks/instalador-gpu-local.md`

**Criterios de aceptación**
- [ ] En una máquina **sin driver NVIDIA**, **sin NVIDIA Container Toolkit**, **sin Docker** o con **VRAM < 8 GB**, el preflight **detecta cada carencia por separado** y la explica con requisito incumplido, valor observado y comando de remedio; termina con código de salida ≠ 0 y **no escribe nada** en el sistema.
- [ ] El preflight comprueba el toolkit **ejecutando** `docker run --rm --gpus all …` (no solo la presencia del binario) y **distingue** «driver ausente» de «toolkit ausente» de «GPU presente con VRAM insuficiente»; si la VRAM está entre 8 y 24 GB, avisa de que se activará offloading y de los tiempos degradados (D-06).
- [ ] Los pesos se colocan **verificados por SHA-256** contra la lista de hashes esperados: un hash que no cuadra **aborta la instalación** y deja el fichero en cuarentena, nunca en la ruta de uso; un fichero que no sea `safetensors` se **rechaza sin cargarse** (D-14). La ruta y el hash de cada peso quedan registrados en el log de instalación.
- [ ] Instalación desde cero en una **máquina limpia** (SO objetivo, I-22): al terminar, la comprobación de sanidad del runner (`probe`) sale **en verde** y `docker compose --profile gpu-local up` levanta el runner **sin ningún paso manual adicional**.
- [ ] La configuración escrita fija el modo (`GPU_PROVIDER=local|runpod|mock`) y el perfil compose `gpu-local`, y **todos los modos de medición quedan con `ACE_STEP_REQUIRE_GPU=1`** (guardarraíl **G-01**), verificable leyendo la config generada.
- [ ] La **desinstalación no deja restos**: verificado con inventario antes/después (`docker ps -a`, `docker volume ls`, rutas de configuración y de pesos), que vuelve al estado previo. Lo que el instalador **no** gestiona (driver NVIDIA, Docker) no se toca y se declara explícitamente en la salida.
- [ ] Re-ejecutar el instalador sobre una instalación existente es **idempotente**: no duplica volúmenes ni vuelve a descargar pesos ya verificados.
- [ ] Runbook de instalación y desinstalación publicado, con la **matriz de SO soportados** que resulte del cierre de **I-22**.

**Subtareas**
- [ ] Esqueleto del CLI: subcomandos `preflight` / `install` / `uninstall`, modo no interactivo y registro de log (**4 h**).
- [ ] Preflight: detección de GPU/VRAM reutilizando `gpu_detect.py` de `T-85`, driver, Docker y NVIDIA Container Toolkit con la comprobación real; catálogo de mensajes accionables por carencia (**8 h**).
- [ ] Descarga/colocación de pesos con verificación SHA-256, cuarentena del fichero que no cuadra y rechazo de todo lo que no sea `safetensors` (**6 h**).
- [ ] Selección de modo y escritura de la config local (`GPU_PROVIDER`, perfil `gpu-local`, `ACE_STEP_REQUIRE_GPU=1` en los modos de medición) (**5 h**).
- [ ] Desinstalación limpia con inventario antes/después (**3 h**).
- [ ] Pruebas manuales de instalación en máquina limpia en 1–2 SO objetivo + runbook (**6 h**).

**Notas:** D-30 (ampliación **propuesta**, no ratificada). **Método de estimación:** desglose ascendente 4+8+6+5+3+6 = **32 h base**, dentro de un rango **24–40 h** — 24 h si el objetivo es **un solo SO** (Linux nativo) reutilizando el `gpu_detect.py` de `T-85`; 40 h si hay que soportar además **Windows 11 + WSL2** (paso de GPU por WSL2, rutas y permisos distintos, segunda ronda de pruebas manuales en máquina limpia). El punto medio asume **dos SO objetivo**, supuesto conservador mientras **I-22** siga abierta. **Coherencia con `T-85`** (16 h): aquella pagó la abstracción de proveedor y la detección de VRAM, **sin** instalación, sin gestión de pesos ni desinstalación; este instalador **reutiliza** esa detección —por eso el preflight no cuesta de cero— y añade preflight accionable, pesos con SHA-256, escritura de config, desinstalación verificada y pruebas en máquina limpia. **Tokens** con el ratio de C-14 (0,25, igual que `T-85`): `horas_IA = 32 × 0,25 = 8 h`; `in = 8 × 0,25 = 2,00 M`, `out = 8 × 0,035 = 0,28 M` (≈ 16 € base de coste de tokens, ruido frente a las horas). **No sustituye a CS-34/CS-35/CS-36 en la máquina de referencia**: el instalador vive en F6 y F2 arranca antes, así que la comprobación manual del entorno de los spikes sigue haciendo falta **una vez**; lo que `T-86` elimina es repetirla a mano en **cada máquina destino** posterior. Ratificación pendiente registrada en `pre-dev-checklist.md` (sección B) y `improvement-plan.md` §5/§14.

---

## F7 · Generación letra + estilo end-to-end — C-01 (78 h)

> **Orden interno deliberado:** primero backend completo (`T-42`–`T-45`) para alcanzar el hito de la canción end-to-end por CLI, después frontend (`T-46`–`T-48`).

### T-42 · API `/generations`: validación, params_schema, idempotencia

**Descripción:** Endpoint `POST /generations`: validación de la petición, comprobación de cuota/concurrencia/cola (§12.1 de la spec), validación de `model_params` contra `params_schema`, resolución de modelo por capacidades, `idempotency_key`.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-25, T-28, T-32, T-41 | 12 h | 0,75 M in / 0,105 M out |

**Archivos:** `apps/api/routes/generations.py`

**Criterios de aceptación**
- [ ] Una petición inválida devuelve 422 con el campo concreto que falla; nada se encola.
- [ ] Cuota agotada devuelve 429 con fecha de reinicio y cuota restante.
- [ ] Cola demasiado profunda devuelve 429 con la espera estimada; el trabajo no se encola.
- [ ] `idempotency_key` repetida no duplica el trabajo ni el artefacto.

**Subtareas**
- [ ] Implementar validación de entrada con Pydantic + `params_schema`.
- [ ] Implementar comprobación de cuota, concurrencia y profundidad de cola.
- [ ] Implementar idempotencia por clave.

---

### T-43 · Gate de derechos de la letra (D-21)

**Descripción:** Declaración de autoría/derechos de la letra como bloqueo duro: propia, generada por el asistente, o con permiso documentado. Registro en auditoría (usuario, fecha, contenido) y `lyrics_declaration` en el manifiesto.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-42, T-27 | 8 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/api/routes/generations.py`, `apps/api/audit/lyrics_declaration.py`

**Criterios de aceptación**
- [ ] Sin `lyrics_declaration`, la API rechaza la petición y no se encola nada (bloqueo duro).
- [ ] La declaración queda registrada en auditoría con usuario, fecha y contenido.
- [ ] El campo `lyrics_declaration` se propaga al manifiesto v1 (`T-27`).

**Subtareas**
- [ ] Implementar la validación de bloqueo duro en la API.
- [ ] Implementar el registro de auditoría.
- [ ] Propagar `lyrics_declaration` al manifiesto.

**Notas:** D-21, mismo patrón que C-08 (Fase 3, fuera de este plan) para el audio subido. El filtro automático de similitud de letras queda fuera de alcance (mejora futura no bloqueante).

---

### T-44 · Worker: invocación del adapter, progreso SSE, reintentos

**Descripción:** Worker que invoca al adapter seleccionado, reporta progreso por `T-16`, y reintenta con nueva semilla en caso de fallo de inferencia (máx. 2) sin consumir cuota.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-42, T-41, T-31 | 12 h | 0,75 M in / 0,105 M out |

**Archivos:** `apps/api/workers/generation_worker.py`

**Criterios de aceptación**
- [ ] Un fallo de inferencia se reintenta (máx. 2, con semilla nueva) y no consume cuota del usuario.
- [ ] El progreso se reporta por SSE (`T-16`) durante `starting`/`running`.

**Subtareas**
- [ ] Implementar la invocación del adapter desde el worker.
- [ ] Implementar la lógica de reintento con nueva semilla.

---

### T-45 · Post-proceso: loudness al destino + transcode FLAC/MP3

**Descripción:** Aplicar la normalización de loudness al objetivo del destino elegido (`T-20`) y transcode a FLAC + MP3 320 (`T-19`) sobre el resultado de la inferencia.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-44, T-19, T-20 | 8 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/runner/postprocess/pipeline.py`

**Criterios de aceptación**
- [ ] La pista resultante tiene la duración pedida ±5 % y loudness dentro de ±1 LU del objetivo del destino.
- [ ] Artefactos disponibles en FLAC + MP3 320 (y WAV a 48 kHz si se pide exportación).

**Subtareas**
- [ ] Conectar el resultado de inferencia con el pipeline de post-proceso.
- [ ] Verificar duración y loudness contra los criterios de C-01.

> ⏩ **Adelanto parcial hecho en F2 (2026-09-02) — la tarea sigue en F7 y sigue `pendiente`.** Al medir `T-03` salió que **la pista de 180 s se salía de escala antes del recorte (pico 1,280)**: sin limitador, el WAV llega recortado por la vía dura y cualquier escucha de G1 estaría juzgando el *clipping*, no el modelo. Se adelantó por eso **solo el limitador de picos** — `apps/runner/adapters/ace_step/ace_step_shim.py`, `TECHO_LIMITADOR_DB = -1,0` dBFS con ventana de 10 ms de anticipación, verificado en `out/con-limitador-informe.json` (`pico_dbfs` exactamente **−1,0**, `pico_dentro_de_escala: true`).
>
> **Lo que este adelanto NO es.** Un limitador de picos **no es normalización de loudness**: no hay medición LUFS, ni objetivo por destino (D-23/`T-20`), ni transcode a FLAC/MP3 320, ni WAV de 48 kHz a demanda. **Los dos criterios de aceptación de esta ficha siguen sin cumplirse** y **no se descuenta ninguna hora de las 8 h estimadas**: lo adelantado es un techo de seguridad para que las pistas de G1 sean escuchables, no el post-proceso de C-01. Cuando se ejecute `T-45`, revisar que el limitador y la cadena de loudness **no se pisen** (limitar después de normalizar, no antes).

---

> ### 🎯 HITO INTERMEDIO — Primera canción end-to-end por CLI
>
> Tras `T-45`, ejecutar un script de línea de comandos que llama a `POST /generations` con un brief real (letra con `lyrics_declaration`, prompt de estilo, duración, destino), sin usar ninguna pieza de frontend. Debe completarse el ciclo íntegro: encolado (`T-14`) → despacho al pod caliente o efímero (`T-38`, `T-39`) → inferencia con ACE-Step (`T-05`, `T-31`) → post-proceso (`T-45`) → manifiesto v1 sellado y encadenado al ledger (`T-27`, `T-28`) → artefacto FLAC/MP3 descargable con URL firmada (`T-13`).
>
> **Criterio de verificación:** el artefacto resultante cumple el criterio de aceptación de C-01 de `spec.md` §5.2 (duración ±5 %, loudness ±1 LU, manifiesto completo, hash encadenado, < 10 min p95 con pod caliente). Si falla, se corrige aquí — antes de construir `T-46`–`T-48` (38 h de frontend) sobre un backend no verificado de punta a punta.

---

### T-46 · Editor de letras con etiquetas de sección

**Descripción:** Editor de letras con etiquetas de sección (`[verso]`, `[estribillo]`, `[puente]`), compatible con el formato que valida C-01 y que produce el asistente de C-05 (Fase 2, fuera de este plan).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-10 | 16 h | 1,00 M in / 0,14 M out |

**Archivos:** `apps/web/components/editor/LyricsEditor.tsx`

**Criterios de aceptación**
- [ ] El editor produce letra con etiquetas de sección válidas y parseables por la API.
- [ ] Componentes accesibles por defecto (D-25), aunque WCAG AA no sea objetivo de esta fase.

**Subtareas**
- [ ] Implementar el editor de texto con soporte de etiquetas de sección.
- [ ] Implementar el parser/validador de etiquetas compartido con la API.

**Notas:** Puede desarrollarse en paralelo a `T-42`–`T-45` una vez exista el contrato OpenAPI de `T-10`; la integración completa se valida después del hito intermedio.

---

### T-47 · Formulario de creación a mano

**Descripción:** Formulario de creación con etiquetas de dominio: estilo, duración, destino (fija el objetivo de loudness), instrumental, opciones de voz. Escrito a mano, no generado desde `params_schema` (D-16).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-46 | 14 h | 0,875 M in / 0,1225 M out |

**Archivos:** `apps/web/components/create/CreationForm.tsx`

**Criterios de aceptación**
- [ ] El formulario valida contra `params_schema` en la API antes de encolar.
- [ ] La selección de destino determina el objetivo de loudness aplicado en `T-45`.
- [ ] Incluye el gate de derechos de la letra (`T-43`) como bloqueo duro visible en la UI.

**Subtareas**
- [ ] Implementar el formulario con los campos de dominio.
- [ ] Conectar la selección de destino con el pipeline de loudness.

---

### T-48 · Panel de resultado, variantes en pares, estados de error

**Descripción:** Panel de resultado con variantes en pares (referencia de UX de Suno, D-12), estados de error legibles, y verificación visual de que el flujo completo (incluido el hito de `T-45`) funciona desde la UI.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | pendiente | T-42, T-46, T-47 | 8 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/web/components/create/ResultPanel.tsx`

**Criterios de aceptación**
- [ ] El panel muestra variantes en pares y estados de error comprensibles (cuota agotada, cola profunda, modelo sin capacidad, etc., según la tabla de errores de la spec §6).
- [ ] Una generación completada desde la UI reproduce el mismo resultado verificado en el hito intermedio por CLI.
- [ ] Marcar una variante como favorita (★) persiste tras recargar (E2E-13). *(criterio añadido 2026-09-01 para cerrar hueco de trazabilidad con test-plan; sin cambio de horas)*

**Subtareas**
- [ ] Implementar el panel de resultado con variantes en pares.
- [ ] Mapear los códigos de error de la API a mensajes legibles.

**Notas:** El estudio guiado de la interfaz de Suno (D-12, con ToS verificados en F2/`T-08`) informa la disposición de este panel y del formulario de `T-47`; la identidad visual es de Daycry (D-12b).

---

## F8 · Instrumental y autenticación — C-02 + C-12 (40 h)

### T-49 · Modo instrumental sin voz

**Descripción:** Variante de la petición de generación con `instrumental: true`, valores por defecto propios de estilo, sin voz detectable.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-45 | 12 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/api/routes/generations.py`, `apps/web/components/create/CreationForm.tsx`

**Criterios de aceptación**
- [ ] Con `instrumental: true`, la pista resultante tiene energía de la pista vocal por debajo del umbral definido en `T-03` (verificado con separación de fuentes).
- [ ] Conmutador visible en la UI y valores de estilo por defecto propios del modo instrumental.

**Subtareas**
- [ ] Implementar el parámetro `instrumental` en la API y el adapter.
- [ ] Implementar el conmutador en el formulario de creación.
- [ ] Verificar ausencia de voz con separación de fuentes sobre una muestra.

---

### T-50 · Auth.js: OAuth social y corporativo + credenciales

**Descripción:** Autenticación doble vía: SSO social/corporativo y usuario+contraseña, con Auth.js.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-10 | 10 h | 0,357 M in / 0,05 M out |

**Archivos:** `apps/web/auth/config.ts`, `apps/api/auth/jwks.py`

**Criterios de aceptación**
- [ ] Las dos vías de acceso (SSO y credenciales) funcionan correctamente.
- [ ] Un colaborador externo puede acceder por credenciales sin necesitar SSO corporativo.

**Subtareas**
- [ ] Configurar Auth.js con proveedores OAuth social y corporativo.
- [ ] Configurar el flujo de usuario+contraseña.

---

### T-51 · TOTP y códigos de respaldo

**Descripción:** 2FA configurable con TOTP (`otplib`), códigos de respaldo de un solo uso, flujo de recuperación.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-50 | 10 h | 0,357 M in / 0,05 M out |

**Archivos:** `apps/api/auth/totp.py`, `apps/api/db/models.py`

**Criterios de aceptación**
- [ ] El 2FA es activable y desactivable, con reautenticación exigida para desactivarlo.
- [ ] Códigos de respaldo de un solo uso, y un flujo de recuperación probado de extremo a extremo.

**Subtareas**
- [ ] Implementar TOTP con `otplib`.
- [ ] Implementar la tabla y lógica de códigos de respaldo de un solo uso.
- [ ] Implementar y probar el flujo de recuperación.

---

### T-52 · JWT/JWKS, roles y auditoría de accesos

**Descripción:** Validación de JWT vía JWKS en FastAPI, roles de usuario, auditoría de accesos.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | pendiente | T-50 | 8 h | 0,286 M in / 0,04 M out |

**Archivos:** `apps/api/auth/jwks.py`, `apps/api/auth/roles.py`

**Criterios de aceptación**
- [ ] FastAPI rechaza JWT inválidos o caducados.
- [ ] Roles aplicados correctamente a los endpoints protegidos.
- [ ] Accesos (login, fallos de autenticación) quedan registrados en auditoría.

**Subtareas**
- [ ] Implementar la validación de JWT vía JWKS.
- [ ] Implementar el modelo de roles y su aplicación a los endpoints.
- [ ] Implementar la auditoría de accesos.

---

## F9 · Verificación final y cierre (0 h dev — checkpoint)

### T-53 · Verificación final de criterios de aceptación y ritual de cierre

**Descripción:** Verificar sistemáticamente todos los criterios de aceptación de `spec.md` §5.2 para C-01, C-02, C-10a, C-11, C-12, C-13 y C-14; actualizar el estado de las 54 tareas a `completado`; preparar el handoff escrito hacia la Fase 2.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| — (no-dev) | pendiente | T-01…T-52, T-85 | 0 h dev *(checklist de cierre, sin desarrollo nuevo)* | — |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/handoff-fase2.md`

**Criterios de aceptación**
- [ ] Cada criterio de `spec.md` §5.2 de C-01, C-02, C-10a, C-11, C-12, C-13 y C-14 verificado con evidencia (no solo marcado).
- [ ] Las 54 tareas de este documento están en `completado` o `cancelado` con justificación.
- [ ] Handoff escrito hacia la Fase 2 (C-10b, C-06, C-05), condicionado explícitamente a I-13 e I-13b.
- [ ] `docs/roadmap/README.md` actualizado con el estado final del plan.

**Subtareas**
- [ ] Recorrer cada criterio de aceptación de `spec.md` §5.2 y adjuntar evidencia.
- [ ] Actualizar el estado de todas las tareas en este documento.
- [ ] Redactar el handoff hacia la Fase 2.

**Notas:** No añade horas de desarrollo nuevas: es el cierre administrativo del plan, no una tarea de construcción. El total de horas de desarrollo del plan es **656 h base / 787,2 h con margen / 39.360 €**, íntegramente ratificados el 2026-08-18 (incluida la ampliación `T-85`, modo GPU local), sin otra desviación.

---

## F10 · Fase 2 (pre-planificación condicionada) — Trazabilidad completa, stems y asistente de letras — C-10b + C-06 + C-05 (131 h)

> 🔒 **Bloqueada por gate compuesto.** Ninguna tarea de esta sub-fase pasa de `bloqueada (gate)` a `pendiente` hasta que se cumplan **todas** estas condiciones: **G1 y G1-bis superados** (ya lo estarían al cerrar F5 de este mismo plan) **+ Fase 1 en uso** (usuarios piloto activos y criterios de aceptación de C-01…C-14 verificados con evidencia, `T-53`) **+ I-13 resuelta** (licencia de watermarking comercialmente limpia y robusta a transcode) **+ I-13b resuelta** (licencia de los pesos de Demucs). Ver `improvement-plan.md` §12.1.

### T-54 · C2PA: firma y verificador de la cadena de confianza

**Descripción:** Implementar la firma C2PA real del manifiesto (más allá del manifiesto propio de C-10a) y el verificador de la cadena de confianza, sobre el manifiesto v1 ya firmado y encadenado en la Fase 1. Incluye la migración a `manifest_schema_version` v2 con los campos C2PA.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-26, T-27, T-53 + Gate de Fase 2 (evaluación: G1/G1-bis + Fase 1 en uso + I-13/I-13b) | 18 h | 0,90 M in / 0,13 M out |

**Archivos:** `apps/api/provenance/c2pa.py`, `apps/api/provenance/c2pa_verifier.py`

**Criterios de aceptación**
- [ ] El manifiesto se firma con C2PA y la firma es verificable con un verificador independiente.
- [ ] El verificador de cadena de confianza valida la firma contra el certificado emisor.
- [ ] La migración a `manifest_schema_version` v2 (campos C2PA) pasa el verificador multi-versión de `T-27` sin invalidar las pistas ya emitidas en la Fase 1.

**Subtareas**
- [ ] Implementar la firma C2PA sobre el manifiesto.
- [ ] Implementar el verificador de cadena de confianza.
- [ ] Añadir el corpus de manifiestos v2 al test de CI del verificador multi-versión.

**Notas:** Depende de que la firma legal del esquema (`T-26`) siga vigente; C2PA añade campos sobre el esquema v1, no lo sustituye (D-20).

---

### T-55 · Gestión de certificados y custodia de clave en KMS con rotación anual

**Descripción:** Gestión de certificados X.509 para la firma C2PA, custodia de la clave privada en un KMS gestionado, rotación anual automática y procedimiento de revocación documentado.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | bloqueada (gate) | T-54 | 14 h | 0,70 M in / 0,098 M out |

**Archivos:** `infra/kms/c2pa-key.tf`, `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/c2pa-revocacion.md`

**Criterios de aceptación**
- [ ] La clave privada de firma nunca sale del KMS gestionado (custodia, no exportación).
- [ ] Rotación anual automática configurada y probada.
- [ ] Procedimiento de revocación documentado y probado en un entorno de pruebas.

**Subtareas**
- [ ] Configurar el KMS gestionado y la política de acceso a la clave.
- [ ] Configurar la rotación anual automática.
- [ ] Documentar y probar el procedimiento de revocación.

---

### T-56 · WORM: object lock + sello diario firmado sobre el ledger

**Descripción:** Activar object lock con retención sobre el bucket del ledger ya encadenado (`T-28`) y un sello diario firmado, sin backfill de los registros de la Fase 1 (D-18).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| devops | bloqueada (gate) | T-28, T-54 | 5 h | 0,25 M in / 0,035 M out |

**Archivos:** `infra/storage/ledger-worm.tf`, `apps/api/provenance/daily_seal.py`

**Criterios de aceptación**
- [ ] El bucket del ledger tiene object lock con retención activa.
- [ ] Sello diario firmado generado automáticamente cada día.
- [ ] Los registros de la Fase 1 (previos a esta tarea) permanecen encadenados sin reescritura — sin backfill.

**Subtareas**
- [ ] Activar object lock con retención sobre el bucket del ledger.
- [ ] Implementar el sello diario firmado.
- [ ] Verificar que no hay reescritura de los registros previos.

**Notas:** La cadena de hashes, que es el grueso del trabajo, ya está construida en `T-28`; aquí solo se activa el candado y el sello — por eso son 5 h y no las 20 h que costaría construir la cadena desde cero.

---

### T-57 · Watermarking robusto a transcode MP3 320 — condicionado a I-13

**Descripción:** Integrar una librería de watermarking de audio robusta a transcode a MP3 320, con licencia comercial limpia verificada (I-13). Invariante en CI de que ninguna pista puede existir sin watermark.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-45, I-13 resuelta | 20 h | 1,00 M in / 0,14 M out |

**Archivos:** `apps/runner/postprocess/watermark.py`

**Criterios de aceptación**
- [ ] Toda pista generada lleva watermark, verificado como invariante en CI.
- [ ] El watermark sobrevive al transcode a MP3 320 (prueba automatizada de robustez).
- [ ] La licencia de la librería de watermarking está verificada como comercialmente utilizable (I-13), sin conflicto con la regla 5 del registry (`commercial_use: false` rechazado).
- [ ] Si no hay librería con licencia comercial limpia disponible al ejecutar esta tarea, el invariante se replanifica y se declara explícitamente — no se integra una librería de licencia dudosa para cumplir el plazo.

**Subtareas**
- [ ] Verificar la licencia de la librería candidata contra la regla 5 del registry (I-13).
- [ ] Integrar el watermarking en el pipeline de post-proceso.
- [ ] Implementar la prueba de robustez frente a transcode MP3 320.

**Notas:** ⚠️ Tarea de mayor riesgo de replanificación de toda F10: I-13 sigue **abierta** a fecha de esta pre-planificación (`evaluation.md` §4). Riesgo de licencia circular ya advertido en la ficha de C-10b: varios watermarkers de referencia tienen términos que hay que verificar contra la propia regla 5 del registry.

---

### T-58 · Certificado exportable JSON/PDF y cierre legal del formato firmado

**Descripción:** Generar un certificado de procedencia exportable en JSON y PDF por pista, y obtener la revisión final de legal del formato firmado (manifiesto v2 + C2PA).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-54, T-56, T-57 | 10 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/api/provenance/certificate_export.py`, `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/c2pa-formato-firmado.md`

**Criterios de aceptación**
- [ ] Certificado exportable en JSON y PDF, generado por pista, con los campos del manifiesto v2 y la firma C2PA.
- [ ] Documento del formato firmado revisado y aprobado por legal (revisión final, distinta de la firma inicial del esquema en `T-26`).
- [ ] El verificador multi-versión (`T-27`) valida indistintamente manifiestos v1 y v2.

**Subtareas**
- [ ] Implementar la exportación del certificado en JSON.
- [ ] Implementar la exportación del certificado en PDF.
- [ ] Enviar el formato firmado a legal para su revisión final y archivar la aprobación.

**Notas:** Cierra C-10b. Con esta tarea, `spec.md` §5.2 C-10b queda cubierto salvo el watermarking, que depende explícitamente de `T-57`/I-13.

---

### T-59 · Ficha de licencia verificada de los pesos de Demucs (I-13b)

**Descripción:** Verificar la licencia de los pesos publicados de Demucs (el código es MIT, pero los pesos llevan términos propios que en algunos casos son no comerciales) antes de integrarlos como separador de fuentes.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | bloqueada (gate) | T-53 + Gate de Fase 2 (evaluación; I-13b) | 5 h | 0,31 M in / 0,044 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/ficha-licencia-demucs.md`

**Criterios de aceptación**
- [ ] Ficha de licencia de los pesos de Demucs con veredicto explícito de uso comercial.
- [ ] Si los pesos no son utilizables comercialmente, se documenta el separador alternativo antes de continuar con `T-60`.

**Subtareas**
- [ ] Revisar los términos de licencia publicados de los pesos de Demucs.
- [ ] Documentar el veredicto y, si es negativo, identificar un separador alternativo con licencia limpia.

**Notas:** La regla 5 del registry aplica al pipeline completo, no solo a los generadores (I-13b). Esto se descubre **antes** de escribir el reproductor multipista, no después.

> ⚠️ **Hallazgo 2026-08-18:** pesos de Demucs **CC-BY-NC confirmado** (issue #327 de `facebookresearch/demucs`) — la selección del separador queda condicionada a I-13b; candidatos alternativos **MDX-Net (UVR5)** / **Mel-Band RoFormer** con pesos MIT verificados.

---

### T-60 · Integración de Demucs como post-proceso (separación en 4 stems)

**Descripción:** Integrar Demucs (o el separador nativo si el modelo declara `STEM_OUTPUT`) como etapa de post-proceso, generando voz, batería, bajo y otros.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-59, T-45 | 12 h | 0,75 M in / 0,105 M out |

**Archivos:** `apps/runner/postprocess/stems.py`

**Criterios de aceptación**
- [ ] Los 4 stems (voz, batería, bajo, otros) se generan alineados con la mezcla original dentro de ±10 ms.
- [ ] La etapa de separación se ejecuta como paso GPU adicional (≈ 30 s) sin bloquear el resto del pipeline.

**Subtareas**
- [ ] Integrar Demucs en el pipeline de post-proceso del runner.
- [ ] Verificar la alineación temporal de los 4 stems contra la mezcla.

---

### T-61 · Reproductor multipista sincronizado

**Descripción:** Extender la base multipista dejada en `T-18` (Fase 1) a un reproductor completo: 4 pistas alineadas, controles por pista, solo/mute.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-60, T-18 | 15 h | 0,94 M in / 0,131 M out |

**Archivos:** `apps/web/components/player/MultitrackPlayer.tsx`

**Criterios de aceptación**
- [ ] Las 4 pistas reproducen sincronizadas (±10 ms) con controles independientes de volumen, solo y mute por pista.
- [ ] La reproducción multipista es accesible por teclado, en línea con el resto de componentes (D-25).

**Subtareas**
- [ ] Extender `MultitrackBase.tsx` (`T-18`) con reproducción sincronizada real de 4 pistas.
- [ ] Implementar los controles de solo/mute por pista.

---

### T-62 · Empaquetado y descarga de stems a demanda

**Descripción:** Empaquetar los 4 stems para descarga y generar stems **solo a demanda**, nunca por defecto, según la decisión de política de almacenamiento (`evaluation.md` §6.6).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-60, T-13 | 8 h | 0,50 M in / 0,07 M out |

**Archivos:** `apps/api/routes/stems.py`

**Criterios de aceptación**
- [ ] Los stems no se generan ni almacenan automáticamente en cada generación; solo al solicitarse explícitamente.
- [ ] La descarga empaquetada (zip o equivalente) incluye los 4 stems con metadatos consistentes con la pista original.

**Subtareas**
- [ ] Implementar el endpoint de generación de stems a demanda.
- [ ] Implementar el empaquetado para descarga.

**Notas:** Coste oculto declarado en `evaluation.md` §6.6: los stems multiplican por ×4,5 el almacenamiento (55→245 MB); de ahí que la decisión sea «a demanda», no un checkbox de UX.

---

### T-63 · Llamada LLM con streaming y plantilla de prompt de letra estructurada

**Descripción:** Implementar la llamada al LLM con streaming y la plantilla de prompt para generar letra estructurada por secciones.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-46, T-53 + Gate de Fase 2 (evaluación) | 8 h | 0,30 M in / 0,042 M out |

**Archivos:** `apps/api/assistant/lyrics_prompt.py`, `apps/api/assistant/lyrics_stream.py`

**Criterios de aceptación**
- [ ] La llamada al LLM devuelve texto en streaming consumible por el frontend.
- [ ] La plantilla de prompt produce letra ya estructurada por secciones (`[verso]`, `[estribillo]`, `[puente]`).

**Subtareas**
- [ ] Implementar la llamada al LLM con streaming.
- [ ] Diseñar la plantilla de prompt de letra estructurada.

---

### T-64 · UI de asistente: streaming, edición e inserción en el editor

**Descripción:** UI del asistente de letras que muestra el streaming, permite editar el resultado e insertarlo en el editor de letras de C-01 (`T-46`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-63 | 6 h | 0,225 M in / 0,0315 M out |

**Archivos:** `apps/web/components/assistant/LyricsAssistant.tsx`

**Criterios de aceptación**
- [ ] El texto generado se muestra progresivamente (streaming) en la UI.
- [ ] El resultado es editable e insertable directamente en `LyricsEditor.tsx` (`T-46`).

**Subtareas**
- [ ] Implementar el componente de streaming en la UI.
- [ ] Implementar la inserción del resultado en el editor de letras.

---

### T-65 · Rate limit, contabilidad de tokens y guardrails

**Descripción:** Rate limit de 30 peticiones/usuario/día (spec §12.1), contabilidad de tokens consumidos por usuario, y guardrails básicos sobre el contenido generado.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-63 | 6 h | 0,225 M in / 0,0315 M out |

**Archivos:** `apps/api/assistant/rate_limit.py`, `apps/api/assistant/usage.py`

**Criterios de aceptación**
- [ ] Un usuario que supera 30 peticiones/día recibe un error claro y no puede seguir generando hasta el reinicio.
- [ ] El coste de tokens por usuario queda registrado y consultable.

**Subtareas**
- [ ] Implementar el rate limit por usuario y día.
- [ ] Implementar la contabilidad de tokens consumidos por usuario.

---

### T-66 · Endurecimiento del prompt de sistema y validación de salida parseable

**Descripción:** Prohibición explícita en el prompt de sistema de reproducir letras existentes, y validación de que la salida es letra etiquetada parseable por C-01, con regeneración automática si no lo es.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-63, T-43 | 4 h | 0,15 M in / 0,021 M out |

**Archivos:** `apps/api/assistant/lyrics_prompt.py`, `apps/api/assistant/lyrics_validator.py`

**Criterios de aceptación**
- [ ] El prompt de sistema prohíbe explícitamente reproducir letras existentes.
- [ ] Una salida no parseable por el validador de etiquetas de sección (`T-46`) se regenera automáticamente, no se entrega tal cual.
- [ ] La letra generada por el asistente rellena `lyrics_declaration` automáticamente (D-21), reutilizando el gate de `T-43`.

**Subtareas**
- [ ] Endurecer el prompt de sistema.
- [ ] Implementar la validación de salida parseable con regeneración en caso de fallo.
- [ ] Conectar la autoría del asistente con `lyrics_declaration`.

**Notas:** Estas 4 h cierran F10 (131 h). Una salida que no parsea no es «una letra mejorable»: es una generación que fallaría en C-01 después de haber pagado GPU — de ahí que la validación sea condición de cierre, no una mejora opcional.

---

## F11 · Fase 3 (pre-planificación condicionada) — Control creativo avanzado — C-07 + C-08 + C-03 (276 h)

> 🔒 **Bloqueada por el gate G3 de adopción.** Ninguna tarea de esta sub-fase pasa de `bloqueada (gate)` a `pendiente` hasta que se supere **G3** (`evaluation.md` §10.1): ≥ 100 generaciones acumuladas, ≥ 3 usuarios activos, ≥ 1 pista usada en una producción real entregada, encuesta de satisfacción ≥ 4/5 — medido tras 1 mes de uso real de la Fase 1+2. Además, la **matriz de capacidades verificadas** de `T-07` debe confirmar `SECTION_INPAINT` y `AUDIO_TO_AUDIO`; si sale vacía, C-07/C-08 se replantean o se caen antes de ejecutar estas tareas. Ver `improvement-plan.md` §12.2.

### T-67 · Editor de forma de onda: render, zoom y selección de regiones (I)

**Descripción:** Primera mitad del editor de forma de onda: renderizado de la forma de onda, zoom y selección de regiones sobre la pista.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-12, T-66 + Gate G3 (adopción) | 22 h | 1,65 M in / 0,231 M out |

**Archivos:** `apps/web/components/editor/WaveformEditor.tsx`

**Criterios de aceptación**
- [ ] La forma de onda se renderiza con zoom fluido sobre pistas de duración variable.
- [ ] Se puede seleccionar una región `[t0, t1]` sobre la forma de onda con precisión de al menos 100 ms.

**Subtareas**
- [ ] Implementar el renderizado de la forma de onda con zoom.
- [ ] Implementar la selección de regiones por arrastre.

**Notas:** Primera tarea de F11: depende del cierre de F10 (`T-66`) **y** del gate G3 — no arranca solo porque F10 esté técnicamente terminada.

---

### T-68 · Editor de forma de onda: snap a secciones y navegación por teclado (II)

**Descripción:** Segunda mitad del editor de forma de onda: snap de la selección a los límites de sección (`[verso]`, `[estribillo]`...) y navegación/edición completa por teclado.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-67 | 22 h | 1,65 M in / 0,231 M out |

**Archivos:** `apps/web/components/editor/WaveformEditor.tsx`

**Criterios de aceptación**
- [ ] La selección de región puede ajustarse (snap) a los límites de sección detectados.
- [ ] El editor es operable por teclado (selección, zoom, confirmación) sin depender del ratón.

**Subtareas**
- [ ] Implementar el snap a límites de sección.
- [ ] Implementar la navegación y edición por teclado.

**Notas:** Con `T-67`, cierra las 44 h del subsistema «editor de forma de onda con regiones» de `evaluation.md` §7 (ficha C-07).

---

### T-69 · Alineado letra-audio con HeartTranscriptor

**Descripción:** Alinear la letra con el audio generado para saber dónde empieza y termina cada sección, usando HeartTranscriptor.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-68, T-07 | 20 h | 1,50 M in / 0,21 M out |

**Archivos:** `apps/api/editing/lyrics_alignment.py`

**Criterios de aceptación**
- [ ] El alineado devuelve, para cada sección de la letra, el intervalo `[t0, t1]` correspondiente en el audio con un margen de error documentado.
- [ ] El resultado del alineado alimenta directamente la selección de regiones de `T-67`/`T-68`.

**Subtareas**
- [ ] Integrar HeartTranscriptor para transcripción con timestamps.
- [ ] Implementar el mapeo de las etiquetas de sección de la letra a los intervalos de audio.

---

### T-70 · Inpaint/continuación — verificación de capacidad y llamada al adapter

**Descripción:** Verificar contra la matriz de capacidades del spike de Fase 0 (`T-07`) si el modelo registrado soporta `SECTION_INPAINT`/`CONTINUATION`, e implementar la llamada al adapter para regenerar la región seleccionada.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-69, T-07 | 16 h | 1,20 M in / 0,168 M out |

**Archivos:** `apps/api/registry/capabilities.py`, `apps/api/editing/inpaint.py`

**Criterios de aceptación**
- [ ] Antes de encolar la regeneración, se comprueba la capacidad declarada **y verificada** (`T-07`) del modelo, no solo su descriptor.
- [ ] Si el modelo soporta `SECTION_INPAINT`/`CONTINUATION`, la llamada al adapter regenera únicamente la región seleccionada.

**Subtareas**
- [ ] Implementar la comprobación de capacidad contra la matriz verificada de `T-07`.
- [ ] Implementar la llamada al adapter para inpaint/continuación.

**Notas:** Si `T-07` no confirmó `SECTION_INPAINT` en ningún modelo registrado, esta tarea (y las siguientes de C-07) se replantean **antes** de ejecutarse — es exactamente la información que la matriz de capacidades del spike de Fase 0 se pagó para tener con antelación (`evaluation.md` §7, ficha C-11).

---

### T-71 · Inpaint/continuación — gestión de fallos y fallback

**Descripción:** Gestión de fallos cuando el modelo no soporta la capacidad requerida o la inferencia de inpaint falla, con mensaje claro y sin dejar la pista en estado inconsistente.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-70 | 12 h | 0,90 M in / 0,126 M out |

**Archivos:** `apps/api/editing/inpaint.py`

**Criterios de aceptación**
- [ ] Si ningún modelo soporta la capacidad, la UI comunica la limitación (según el patrón de `spec.md` §5.2 C-03) en lugar de fallar sin explicación.
- [ ] Un fallo de inferencia durante el inpaint no corrompe la pista original.

**Subtareas**
- [ ] Implementar el fallback cuando la capacidad no está disponible.
- [ ] Implementar la gestión de fallos de inferencia sin corromper el estado.

---

### T-72 · Empalme con crossfade y validación de costura

**Descripción:** Empalmar la región regenerada con el resto de la pista mediante crossfade, con validación automática de que no hay costura audible.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-70, T-71 | 20 h | 1,50 M in / 0,21 M out |

**Archivos:** `apps/runner/postprocess/crossfade.py`

**Criterios de aceptación**
- [ ] El empalme usa crossfade configurable y no introduce clics ni saltos de fase detectables por análisis automático.
- [ ] 2 de 3 evaluadores no identifican el punto de empalme en escucha ciega (criterio de `spec.md` §5.2 C-07).

**Subtareas**
- [ ] Implementar el crossfade configurable.
- [ ] Implementar la validación automática de costura (análisis de fase/clics).

---

### T-73 · Preservación bit-idéntica fuera de la región editada

**Descripción:** Garantizar y probar que el audio fuera de la región `[t0, t1]` editada permanece bit-idéntico tras la regeneración.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| test | bloqueada (gate) | T-72 | 12 h | 0,90 M in / 0,126 M out |

**Archivos:** `apps/api/tests/editing/test_bitexact_preservation.py`

**Criterios de aceptación**
- [ ] Un test automatizado compara byte a byte el audio fuera de la región editada antes y después de la regeneración, y falla si difiere.
- [ ] El criterio de `spec.md` §5.2 C-07 («resto del audio bit-idéntico fuera de la región») queda cubierto con evidencia de test, no solo con inspección manual.

**Subtareas**
- [ ] Implementar el test de comparación bit a bit.
- [ ] Integrar el test en la suite de CI de C-07.

---

### T-74 · Línea de tiempo por secciones, máquina de estados de edición y linaje de la derivada

**Descripción:** Línea de tiempo por secciones para la edición, máquina de estados del flujo de edición (selección → regeneración → validación → confirmación), y registro de `source_generation`/`parent_id` en el manifiesto de la pista derivada, reutilizando el linaje ya presente en el esquema (`T-12`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-70, T-71, T-72, T-73, T-12 | 16 h | 1,20 M in / 0,168 M out |

**Archivos:** `apps/api/editing/edit_state_machine.py`, `apps/api/provenance/manifest_v1.py`

**Criterios de aceptación**
- [ ] La máquina de estados de edición cubre selección → regeneración → validación → confirmación, con transiciones inválidas rechazadas.
- [ ] Toda pista derivada de una regeneración referencia a su padre (`parent_id`) y a la raíz (`root_id`) usando el esquema de `T-12`, sin migración adicional.
- [ ] El manifiesto de la derivada incluye `source_generation` correctamente enlazado.

**Subtareas**
- [ ] Implementar la máquina de estados de edición.
- [ ] Implementar la línea de tiempo por secciones en la UI.
- [ ] Conectar la regeneración con el linaje del esquema (`T-12`) y el manifiesto (`T-27`).

**Notas:** Cierra C-07 (140 h). Gracias al linaje ya presente en el esquema desde la Fase 1 (D-22), esta tarea **no requiere una migración de datos en producción** — que es como se habría planificado sin la corrección de la revisión 3 de `evaluation.md`.

---

### T-75 · Ingesta de audio subido + gate de titularidad obligatorio

**Descripción:** Endpoint de subida de audio para cover/remezcla, con declaración de titularidad como **bloqueo duro** (mismo patrón que `T-43` para la letra), registrada en auditoría.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-43, T-74 + Gate G3 | 16 h | 1,20 M in / 0,168 M out |

**Archivos:** `apps/api/routes/uploads.py`, `apps/api/audit/audio_declaration.py`

**Criterios de aceptación**
- [ ] Sin declaración de titularidad del audio subido, la API rechaza la ingesta y no se procesa nada (bloqueo duro, mismo patrón que D-21 en `T-43`).
- [ ] La declaración queda registrada en auditoría con usuario, fecha y contenido.

**Subtareas**
- [ ] Implementar el endpoint de subida de audio.
- [ ] Implementar el bloqueo duro de titularidad, reutilizando el patrón de `T-43`.

**Notas:** «El riesgo aquí es legal, no técnico» (`evaluation.md` §7, ficha C-08): construir esto sin gate de titularidad sería contradictorio con la motivación de la iniciativa.

---

### T-76 · Separación de fuentes y extracción de melodía/estructura

**Descripción:** Reutilizar la separación de fuentes de C-06 (`T-60`) sobre el audio subido, y extraer melodía y estructura para condicionar la generación `AUDIO_TO_AUDIO`.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-75, T-60 | 20 h | 1,50 M in / 0,21 M out |

**Archivos:** `apps/api/editing/audio_analysis.py`

**Criterios de aceptación**
- [ ] La separación de fuentes reutiliza el pipeline de `T-60` sin duplicar código.
- [ ] La extracción de melodía y estructura produce una representación consumible por el adapter de `T-77`.

**Subtareas**
- [ ] Conectar el pipeline de separación de `T-60` a la ingesta de `T-75`.
- [ ] Implementar la extracción de melodía y estructura.

---

### T-77 · Generación AUDIO_TO_AUDIO según matriz de capacidades

**Descripción:** Invocar la capacidad `AUDIO_TO_AUDIO` en el adapter registrado, verificada previamente contra la matriz de capacidades del spike de Fase 0 (`T-07`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-76, T-07, T-31 | 24 h | 1,80 M in / 0,252 M out |

**Archivos:** `apps/api/editing/audio_to_audio.py`

**Criterios de aceptación**
- [ ] La generación se invoca solo si `AUDIO_TO_AUDIO` está confirmada en la matriz verificada de `T-07`, no solo declarada en el descriptor.
- [ ] El resultado conserva la estructura y melodía extraídas en `T-76` dentro de una tolerancia perceptual acordada con el supervisor musical.

**Subtareas**
- [ ] Implementar la invocación de `AUDIO_TO_AUDIO` contra el contrato del registry (`T-30`).
- [ ] Validar el resultado contra la estructura/melodía de entrada.

**Notas:** Si `T-07` no confirmó `AUDIO_TO_AUDIO`, C-08 se replantea antes de llegar aquí — mismo razonamiento que `T-70` para C-07.

---

### T-78 · Registro en auditoría y manifiesto de la pista derivada

**Descripción:** Registrar en auditoría la operación de cover/remezcla completa y emitir el manifiesto de la pista derivada con `source_generation` enlazado a la ingesta original.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-77 | 12 h | 0,90 M in / 0,126 M out |

**Archivos:** `apps/api/audit/cover_audit.py`, `apps/api/provenance/manifest_v1.py`

**Criterios de aceptación**
- [ ] Cada operación de cover/remezcla queda registrada en auditoría con usuario, fecha, declaración de titularidad y resultado.
- [ ] El manifiesto de la pista derivada incluye `source_generation` referenciando el audio subido y su declaración de titularidad.

**Subtareas**
- [ ] Implementar el registro de auditoría de la operación completa.
- [ ] Enlazar el manifiesto de la derivada con la declaración de titularidad de `T-75`.

---

### T-79 · Mezcla del resultado y validación de calidad

**Descripción:** Mezclar/empalmar el resultado de `AUDIO_TO_AUDIO` con la pista de referencia cuando aplique, y validar la calidad del resultado antes de entregarlo.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-77 | 8 h | 0,60 M in / 0,084 M out |

**Archivos:** `apps/runner/postprocess/cover_mix.py`

**Criterios de aceptación**
- [ ] El resultado final pasa la suite de conformidad perceptual de `T-32` (invariantes exactos + tolerancia perceptual).
- [ ] Se documenta un criterio de calidad mínima antes de habilitar la entrega al usuario.

**Subtareas**
- [ ] Implementar la mezcla/empalme final.
- [ ] Conectar la validación con la suite de conformidad de `T-32`.

**Notas:** Cierra C-08 (80 h).

---

### T-80 · Catálogo curado de ≥ 8 presets de voz

**Descripción:** Construir un catálogo de al menos 8 presets de voz, restringidos a condicionamiento por etiquetas o por audio sintético generado por el propio modelo — **nunca** grabaciones de voces reales sin verificación de derechos (restricción de `evaluation.md` §7, ficha C-03, equivalente a B-11 del catálogo de riesgos).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| backend | bloqueada (gate) | T-11, T-31 + Gate G3 | 20 h | 1,96 M in / 0,275 M out |

**Archivos:** `apps/api/voices/presets.py`

**Criterios de aceptación**
- [ ] El catálogo tiene ≥ 8 presets, cada uno basado en condicionamiento por etiquetas o audio sintético del propio modelo.
- [ ] Ningún preset se construye a partir de una grabación de voz real sin la verificación de derechos de `T-82`.

**Subtareas**
- [ ] Definir y curar los ≥ 8 presets con sus etiquetas.
- [ ] Implementar el condicionamiento `VOICE_CONDITIONING` sobre el adapter registrado.

---

### T-81 · Previsualización de preset con audio de muestra

**Descripción:** Añadir audio de muestra escuchable en la UI para cada preset del catálogo, con reproducción antes de generar.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-80 | 8 h | 0,79 M in / 0,11 M out |

**Archivos:** `apps/web/components/create/VoicePresetPicker.tsx`

**Criterios de aceptación**
- [ ] Cada preset del catálogo tiene una muestra de audio reproducible directamente en la UI, sin necesidad de generar antes.

**Subtareas**
- [ ] Generar/curar la muestra de audio de cada preset.
- [ ] Implementar el selector con previsualización en la UI.

---

### T-82 · Verificación documentada de derechos por preset

**Descripción:** Para cualquier preset que derivase de una grabación real, verificar y documentar los derechos por preset como criterio de aceptación explícito (sin ella, el preset no se publica).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| docs | bloqueada (gate) | T-80 | 8 h | 0,79 M in / 0,11 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/legal/fichas-derechos-presets.md`

**Criterios de aceptación**
- [ ] Cada preset del catálogo tiene su origen documentado (etiqueta/síntesis vs. grabación real).
- [ ] Ningún preset derivado de grabación real se publica sin verificación de derechos documentada.

**Subtareas**
- [ ] Revisar el origen de cada preset del catálogo de `T-80`.
- [ ] Documentar la verificación de derechos de los presets que lo requieran.

**Notas:** Mismo riesgo que C-04 (RGPD/biometría) entrando por la puerta de una característica de 56 h en lugar de por la de 175 h (`evaluation.md` §7, ficha C-03) — de ahí que esta tarea sea criterio de aceptación, no un trámite.

---

### T-83 · Integración del selector de voz en el formulario de generación

**Descripción:** Integrar el catálogo de presets de `T-80`/`T-81` en el formulario de creación de C-01 (`T-47`).

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| frontend | bloqueada (gate) | T-80, T-47 | 12 h | 1,18 M in / 0,165 M out |

**Archivos:** `apps/web/components/create/CreationForm.tsx`

**Criterios de aceptación**
- [ ] El formulario de creación permite elegir un preset de voz del catálogo antes de generar.
- [ ] La selección de preset se propaga correctamente a `params_schema` y al adapter (`VOICE_CONDITIONING`).

**Subtareas**
- [ ] Añadir el selector de preset al formulario de `T-47`.
- [ ] Conectar la selección con la validación de `params_schema`.

---

### T-84 · Escucha ciega de validación de reconocibilidad del preset

**Descripción:** Ejecutar el protocolo de escucha ciega (mismo patrón que G1/G1-bis, `T-08`/`T-09`) para verificar que cada preset es reconocible por 2 de 3 evaluadores.

| Tipo | Estado | Dependencias | Tiempo estimado (base) | Tokens previstos |
|---|---|---|---|---|
| test | bloqueada (gate) | T-80, T-08 | 8 h | 0,79 M in / 0,11 M out |

**Archivos:** `docs/roadmap/2026-07-27-plataforma-musical-ia/gates/c-03-escucha-presets.md`

**Criterios de aceptación**
- [ ] Cada preset del catálogo se evalúa en escucha ciega por los mismos 3 evaluadores de G1/G1-bis.
- [ ] Un preset reconocible por menos de 2 de 3 evaluadores **no se promete** como tal: se documenta la limitación en la UI en lugar de eliminarlo (criterio de `spec.md` §5.2 C-03).

**Subtareas**
- [ ] Preparar las muestras de escucha ciega por preset.
- [ ] Ejecutar la sesión de escucha y documentar el resultado por preset.

**Notas:** Cierra C-03 (56 h) y F11 (276 h). No es un gate bloqueante de F11 completo (es evaluación por preset, no una decisión go/no-go de fase), pero sí condición de aceptación de `spec.md` §5.2 C-03 para cada preset publicado.

---

## F12 · Fase 4 — anexo condicional (sin tareas, no-go vigente)

> ❌ **Esta sub-fase no tiene tareas `T-XX` en este documento.** C-09 (fine-tuning, 400 h) y C-04 (clonación de voz, 175 h) están bloqueadas por I-03, I-01 y por la falta de DPIA/base jurídica RGPD (`evaluation.md` §7, §10.1). El detalle de qué contendría y qué la desbloquearía está en `improvement-plan.md` §13, como marcador informativo. Crear tareas ejecutables para esta fase requiere una **nueva evaluación y ratificación** — no una extensión de este ledger.

---

## Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-08-18 | Creación de las 53 tareas a partir de `improvement-plan.md`, con desglose heredado de las fichas por característica de `evaluation.md` §7. Suma exacta: 640 h base. Estado inicial de todas las tareas: `pendiente`. | planner |
| 2026-08-18 | **Extensión de pre-planificación** (misma fecha, a petición expresa): añadidas 31 tareas nuevas `T-54`…`T-84` en dos sub-fases nuevas — **F10** (Fase 2: C-10b+C-06+C-05, 131 h, `T-54`…`T-66`) y **F11** (Fase 3: C-07+C-08+C-03, 276 h, `T-67`…`T-84`) — más **F12**, un marcador sin tareas para la Fase 4 (575 h, informativo, ver `improvement-plan.md` §13). Todas las tareas nuevas nacen en estado `bloqueada (gate)`: F10 bloqueada por G1/G1-bis + Fase 1 en uso + I-13/I-13b; F11 bloqueada por G3 de adopción. `T-01`…`T-53` no se modifican. Tabla resumen y vocabulario de estados actualizados para reflejar el ledger completo (84 tareas, 1.047 h base / 62.820 € con margen, de los cuales solo 640 h / 38.400 € siguen aprobadas y ejecutables). | planner |
| 2026-08-18 | **Ampliación: modo GPU local (D-29, T-85, E2E-GPU-04).** Nueva tarea `T-85` en F6 (C-14): proveedor de aprovisionamiento `local` vía NVIDIA Container Toolkit, con detección de VRAM y offloading automático, además de RunPod (cloud) y mock (D-29, `spec.md` confirmación 12). Delta: **+16 h base / +19,2 h con margen / +960 €**. F6 pasa de 96 h/5.760 € a **112 h/6.720 €**; Fase 0+1 (F1–F9) de 640 h/38.400 € a **656 h base / 787,2 h con margen / 39.360 €** — de los cuales **38.400 € eran lo ya ratificado** y **960 € eran, en ese momento, ampliación de alcance a la espera de ratificación económica del usuario**. Ledger completo: 85 tareas, **1.063 h base / 63.780 € con margen**. `test-plan.md` añade `E2E-GPU-04` (generación real en modo local). | planner |
| 2026-08-18 | **Ratificación de la ampliación GPU local (+960 €) y decisión: Fase 0 en GPU local preferente** (misma fecha). Los **39.360 € de Fase 0+1 (F1–F9) quedan íntegramente ratificados**, incluida `T-85` — se elimina del resumen de progreso (§1) y de F6 cualquier marcador de ampliación sin ratificar. Además, nueva decisión del usuario: `T-03`, `T-04`, `T-05` (spikes de F2) y `T-09` (generación de las 10 pistas de G1, F3) pasan a ejecutarse **preferentemente en GPU local**, a coste cloud cero salvo la medición de arranque en frío de `T-03` (S-01/S-01b), que sigue exigiendo el pod real de RunPod; `T-04` documenta la excepción si la GPU local no tiene VRAM suficiente para 2 inferencias simultáneas. `T-85` no se adelanta ni se mueve: sigue siendo la abstracción de proveedor completa de F6. Ninguna hora de desarrollo cambia. | planner |
| 2026-08-18 | **Hallazgos HF 2026-08-18 registrados como candidatos** (SilentCipher/AudioSeal para I-13, Demucs CC-BY-NC confirmado en I-13b, MiniMax-Music3 candidato condicional con pregunta añadida a G2, vía LoRA en anexo F4, XL en spikes). Registro informativo verificado contra fuentes primarias, **sin cambio de horas, coste, fases ni estados**: siguen vigentes 656 h base / 39.360 € (F1–F9) y 1.063 h / 63.780 € (ledger completo F1–F11). Nota añadida en `T-01` (tercera pregunta candidata para el lote de G2), checkbox opcional en `T-03` y `T-05` (variantes XL de ACE-Step) y nota de hallazgo en `T-59` (Demucs CC-BY-NC confirmado). Ningún estado de tarea cambia. | planner |
| 2026-09-01 | **Corrección de coherencia tras revisión integral (`revision-2026-09-01.md`).** (a) Renombrado el atajo ambiguo «Gate F2» de las dependencias de `T-54`, `T-59` y `T-63` a **«Gate de Fase 2 (evaluación)»**, para que no colisione con la sub-fase F2 del plan (Fase 0, spikes). (b) Cerrados tres huecos de trazabilidad E2E↔T-XX añadiendo un criterio de aceptación (marcado «criterio añadido 2026-09-01…; sin cambio de horas»): `T-41` ← E2E-19 (editar cuota desde el panel admin), `T-48` ← E2E-13 (favorito ★ persistente), `T-21` ← E2E-14 (certificado de procedencia en el detalle de pista). **Ningún estado ni horas de tarea cambian.** | revision-2026-09-01 |
| 2026-09-01 | **Adaptación a proyecto personal en solitario — cierre de `T-02` en modo solo.** Motivo: decisión del propietario (Daycry): proyecto personal de una sola persona, con posible comercialización futura. `T-02` pasa de `en-progreso` a **`completado`** con criterios adaptados y verificados: evaluador único = propietario (protocolo numérico de G1 íntegro — 7/10 ≥ 4/5, WER ≤ 15 % — sin degradar; riesgo de independencia aceptado por escrito), usuario piloto = propietario (G3 reinterpretado: ≥ 100 generaciones propias, ≥ 1 pista en algo real, autoevaluación ≥ 4/5) y construir-vs-comprar documentada («construir»: aprendizaje, control, self-hosting). La versión corporativa de los criterios (3 evaluadores, 3–5 pilotos, ofertas con indemnización) se traslada al nuevo **gate de comercialización GC-01** (`gates/gobernanza.md` §8). §1: F1 pasa a `completado` (completado 1→2, en-progreso 1→0). Ninguna hora ni cifra ratificada cambia (656 h / 39.360 €). | propietario (Daycry) |
| 2026-09-01 | **`T-08` ejecutada — protocolo escrito del gate G1 (`gates/g1-protocolo.md`), `pendiente` → `en-revision`.** Entregable creado con los umbrales de `evaluation.md` §10.2 y `gobernanza.md` §2.2 **sin degradar ninguno** (7/10 con D5 ≥ 4/5 · ninguna dimensión con media < 3,0 · CLAP ≥ librería en 7/10 · WER ≤ 15 % medio y ≤ 25 % peor caso · no-go si pierde contra librería en D5 en > 5/10), con **regla de inmutabilidad** y precisiones aritméticas (medias a 2 decimales sin redondear, escala entera, empate no es derrota, brief sin línea base cuenta como derrota). **Aportación principal: la rúbrica de las 5 dimensiones con descriptores por nivel** — hasta hoy la escala 1–5 estaba enunciada pero sin definición operativa. Además: **10 briefs propios realistas** redactados y marcados `propuestos — pendientes de ratificación` (adaptación de `gobernanza.md` §2.2.1 al modo solo), procedimiento completo de sesión ciega (3 tomas por serie, reglas anti-sesgo para elegir la línea base de librería antes de generar, mapa ciego por script, condiciones de escucha y fatiga, **loudness de sesión −16 LUFS / ≤ −1 dBTP** distinguido del objetivo por destino D-23, ruptura del ciego con sellado SHA-256 de las hojas), **variante B sin línea base de Suno con los cinco umbrales intactos**, medición reproducible de CLAP y WER (identificadores y SHA-256 de pesos **declarados como dependencia de `T-09`**, no inventados), hoja de puntuaciones vacía, regla de decisión go/no-go/replanteo con tope de 2 repeticiones, y política de retención S-11. **Tres adaptaciones a modo solo declaradas** (evaluador único sin quórum «2 de 3» · briefs propios en vez de producciones de Daycry · **ToS de Suno trasladados a GC-01 §8c**). **`T-08` queda `en-revision` y no `completado`**: de sus tres criterios, solo el primero lo cierra el implementador; el segundo (**ratificación firmada del propietario antes de la primera escucha**) y el tercero (**ToS de Suno**, ahora en GC-01) quedan abiertos con dueño y momento. **Deuda nueva declarada:** la decisión de **loudness por destino (D-23)**, exigida por escrito antes de G1 (`gobernanza.md` §2.2.5), **no tiene tarea propia en F2**; queda como precondición de `T-09`. §1: F2 pasa a `en-progreso`. **Ninguna hora, cifra ratificada ni umbral cambia** (656 h / 39.360 €). | implementer (`T-08`) |
| 2026-09-01 | **Ampliación PROPUESTA: instalador del runner GPU local (`T-86`, D-30) — pendiente de ratificación económica.** Nueva tarea `T-86` en F6 (C-14): CLI/script de instalación del modo `GPU_PROVIDER=local` en una máquina nueva — **preflight automatizado** (GPU/VRAM/driver NVIDIA/Docker/NVIDIA Container Toolkit con `docker run --rm --gpus all …` y mensaje accionable por carencia), **pesos `safetensors` verificados por SHA-256** (D-14), **escritura de la config local** (`GPU_PROVIDER`, perfil compose `gpu-local`, guardarraíl **G-01** `ACE_STEP_REQUIRE_GPU=1` en los modos de medición) y **desinstalación limpia**; fuera de alcance GUI, auto-update y empaquetado firmado de Windows. Delta: **+32 h base / +38,4 h con margen / +1.920 €** (rango 24–40 h, punto medio por desglose ascendente 4+8+6+5+3+6; tokens 2,00 M in / 0,28 M out con el ratio 0,25 de C-14). **Ninguna cifra ratificada cambia:** F6 sigue en **112 h / 6.720 €**, Fase 0+1 en **656 h / 39.360 €** y el ledger completo en **1.063 h / 63.780 €**; el delta se registra como **fila y nota separadas** en §1 y como aviso destacado en la propia tarea (si se ratificase: F6 144 h/8.640 €, Fase 0+1 688 h/41.280 €, ledger 1.095 h/65.700 €). Nueva incógnita **I-22** en `spec.md` (SO objetivo del instalador y quién lo mantiene tras la entrega) como principal fuente de dispersión del rango. Ningún estado de tarea existente cambia. | evaluator |
| 2026-09-02 | **F2 avanza a la puerta de G1 — `T-05`, `T-06` y `T-07` cerradas con evidencia ejecutada.** `T-05` → **`completado`**: los 4 criterios verificados ejercitando el ciclo de vida entero del adapter, no leyéndolo — `load()`/`generate()` en generaciones reales de 240 s y **`health()`/`unload()` en una sonda dedicada** (`out/t05-health-informe.json`) que confirma lo que el criterio 3 pide de verdad: `health()` contesta **durante** el arranque en frío (cada 20 s, sin bloquearse), pasa a `ready=True` al terminar (140,24 s = `vram_load` 83,34 + warm-up 52,48) y vuelve a `ready=False` tras `unload()`. `T-06` → **`completado`** (`spikes/comparativa-modelos.md`, D-06 confirmado sin cambios; destapa que **`spec.md` §11.1 describe a ACE-Step v1 3.5B y no a 1.5**, y que **la licencia es MIT, no Apache 2.0** — dato que el manifiesto de procedencia va a registrar). `T-07` → **`completado`** (`spikes/matriz-capacidades.md`, 4 capacidades sondeadas sobre pesos y GPU reales con 9 WAV de evidencia; **C-07 y C-08 no se caen**, y aparece un prerrequisito de 8–16 h que no estaba en ninguna estimación: falta el codificador del VAE). `T-03` sigue **`en-progreso`** con 1 de 6 criterios cumplido: el pipeline genera audio real y está perfilado, pero **el arranque en frío de S-01 contra RunPod no está medido** y RunPod queda **aparcado por presupuesto**. `T-08` sigue **`en-revision`**: le falta la firma del propietario y nadie más puede darla. Corregida la fila de F2 del §1, que seguía diciendo «bloqueadas por CS-36» desde antes de que CS-36 se cerrara. **Ninguna hora ni cifra ratificada cambia** (656 h / 39.360 €). | implementer (cierre de F2) |
| 2026-09-02 | **Dos adelantos de alcance de fases posteriores, anotados donde nacen y sin cobrar horas.** (a) **`T-45`** (F7): se adelantó **solo el limitador de picos** (techo −1,0 dBFS, verificado) porque la pista de 180 s se salía de escala antes del recorte y, sin él, la escucha de G1 juzgaría el *clipping* en vez del modelo. **No es normalización de loudness**: sin LUFS, sin objetivo por destino, sin transcode. (b) **`T-85`** (F6): existe `gpu_tiers.py` con **26 tests**, que cubre una parte del tercer criterio — configuración por nivel de GPU detectado en vez de valores clavados a los de una GTX 1070 (`tier3` de ocho tramos), tabla vendorizada de upstream con procedencia y cuatro desviaciones documentadas por Pascal. **Ambas tareas siguen `pendiente` en su fase, ningún criterio marcado y ninguna hora descontada** (F7 78 h, F6 112 h). | implementer (cierre de F2) |
| 2026-09-02 | **Cuatro cabos sueltos nuevos registrados en `pre-dev-checklist.md` — sección D, CS-52 a CS-55** (51 → 55 ítems). **CS-52** etiquetas de sección: ACE-Step espera las canónicas y el formato Suno va **verbatim** al modelo; A/B limpio hoy con misma semilla y mismo cuerpo de letra — afecta al validador de `T-46` y al protocolo de G1. **CS-53** ACE-Step **no reparte voces por sección** (dúo, coro): un único vector de timbre global; es una diferencia de capacidad frente a Suno y acota lo que se le puede prometer al usuario. **CS-54** la matriz de `T-07` puede estar midiendo el techo del **turbo** y no el de ACE-Step (`Extract`/`Lego`/`Complete` marcadas no soportadas en turbo y sí en `base`), con la pista de que **`extract` bajo MIT** sería candidato a desbloquear C-06. **CS-55** el arranque en frío medido contradecía la promesa de 2–6 min de `ui-design.md`: 12,6–13,0 min antes del arreglo de lectura contigua, 1,8–2,3 min después — pero **eso es solo el término de carga local** y el S-01 real sigue sin medir, con la copia «2-6 min» ya escrita en `adapter.health()`. Actualizados además CS-38/CS-39 (RunPod aparcado por presupuesto) y el ítem 44 (entregables de F2: dos de tres escritos). **Ninguna cifra ratificada ni umbral de gate cambia.** | implementer (cierre de F2) |
