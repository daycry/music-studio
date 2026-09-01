---
documento: registro-decisiones
titulo: "Registro de decisiones — 2026-09-01 (licencias del pipeline, coste e infraestructura, producto y alcance, datos y operación, gates y umbrales)"
iniciativa: "Plataforma propia de generación musical por IA (equivalente funcional Suno)"
slug: plataforma-musical-ia
fecha: 2026-09-01
actualizado: 2026-09-01
autor: "revisión en cinco líneas (agentes) — propuestas de decisión; las firmas del propietario están pendientes"
estado: propuesta
decisiones: 49
firmas-pendientes-propietario: 34
decisiones-ejecutables-por-agente: 15
contradicciones-resueltas: 9
spec: ./spec.md
tasks: ./tasks.md
checklist: ./pre-dev-checklist.md
gobernanza: ./gates/gobernanza.md
gate-g1-protocolo: ./gates/g1-protocolo.md
gate-g2: ./gates/g2-matriz-resultados.md
plan: ./improvement-plan.md
evaluacion: ./evaluation.md
---

# Registro de decisiones — 2026-09-01

> **Qué es este documento.** El acta de las **49 decisiones** que quedaron sobre la mesa tras la revisión del 2026-09-01, cada una con su criterio, su evidencia, su recomendación, el coste de no decidirla y quién debe firmarla. **No ratifica nada.** Es el material sobre el que el propietario firma: 34 de las 49 son suyas por gobernanza (gates, umbrales de la spec, gasto, alcance); las 15 restantes las puede ejecutar un agente sin firma porque son correcciones de coherencia, de dato o de higiene.
>
> **Regla de no usurpación (`gates/gobernanza.md` §2.1).** El propietario es evaluador único de G1 precisamente para que quien construye no ratifique la calidad. **Ninguna observación de este registro mueve un umbral ni una décima, con una excepción declarada: la opción (2) de A-13 cambiaría cómo se calcula el criterio 5 de no-go de G1** — sustituye el denominador «> 5 de **los 10** briefs» por «> 5 de los briefs **comparables**», y con `N_comparables` ≤ 5 el NO-GO pasa a ser **matemáticamente imposible**. **Está marcada como tal en su ficha, lleva cláusula de suelo obligatoria (`N_comparables` ≥ 8 o la sesión no cierra el gate) y requiere firma del propietario; ninguna otra ficha de este registro toca un número.** La propia A-13 ofrece como preferente la opción **(0)**, que no toca el denominador. Los cinco umbrales de G1, los diez briefs, las cifras ratificadas (**656 h / 39.360 €** de Fase 0+1; **407 h / 24.420 €** bloqueadas por gate; Fase 4 en no-go) y el estado de `T-08` (`en-revision`) siguen exactamente donde estaban. Ver §5, «Lo que NO decide este documento».

**Cómo se produjo.** Cinco líneas de trabajo en paralelo, todas con verificación contra fuente el 2026-09-01: **(1)** licencias del pipeline (separación en stems, watermarking, `T-33`, `adapter.py:410`); **(2)** coste e infraestructura (precios de RunPod, R2/S3, librerías de producción, instalador `T-86`); **(3)** producto y alcance (idiomas, audio de entrada, latencia, incógnitas heredadas del modo corporativo); **(4)** datos, entornos y operación (retención, entornos, GPU propia, repositorio, herramientas); **(5)** gates y umbrales (suelo de VRAM, protocolo de G1, loudness por destino, los cinco diferimientos a GC-01).

**Marcadores de verificación usados en todo el documento**

| Marcador | Significado |
|---|---|
| ✅ | Verificado el 2026-09-01 contra fuente primaria citada (fichero:línea, API del host, cláusula de licencia, cifra medida o test ejecutado) |
| ⚠️ | **No verificado o no verificable hoy.** Se dice explícitamente en vez de rellenar con plausibilidad |
| 🔒 | Requiere firma del propietario por gobernanza (gate, umbral de la spec, gasto o alcance) |

**Orden del documento.** Por **urgencia real**, no por tema: **§2 Bloque A** — lo que bloquea hoy (F2 está en marcha, `T-08` en `en-revision`, `T-03`/`T-05` en `en-progreso`); **§3 Bloque B** — lo que tiene fecha en un gate (F4, F5, F6/F7, F10, F11, GC-01); **§4 Bloque C** — higiene documental, que no bloquea nada pero cuesta atención en cada revisión.

---

## 1. Tabla resumen

**Firma:** 🔒 = propietario · ⚙️ = agente. **Estado:** `pendiente de firma` = redactada, sin firmar · `lista para ejecutar` = un agente puede aplicarla sin firma.

| # | ID | Decisión (una línea) | Firma | Estado |
|---|---|---|---|---|
| **A · Bloquea hoy** | | | | |
| A-01 | **D-31** (cierra CS-51 / ítem 7-ter) | Conservar `VRAM_FLOOR_MB = 8192` y añadir `VRAM_FLOOR_TOLERANCE_MB = 64` (suelo efectivo 8128 MB): corrige la unidad de medida, no el requisito de hardware | 🔒 | pendiente de firma |
| A-02 | CS-51-b | Corregir «294.912 B» → **262.144 B** en `_timing.py:122` y hacer que los tres mensajes al operador citen el suelo efectivo, no el nominal | ⚙️ | lista para ejecutar |
| A-03 | CS-51-c | Dejar escrito que D-31 **no ratifica viabilidad**: la restricción real es la VRAM **libre** (~6988 MiB) frente a los 5878 MiB del artefacto | ⚙️ | lista para ejecutar |
| A-04 | CS-13 / I-02 | Cerrar I-02 con respuesta partida: **sí** para F2/F3 en la GTX 1070, **no** como sustituto de la postura de producción, con **regla de conmutación** a RunPod escrita | 🔒 | pendiente de firma |
| A-05 | CS-19 / I-11 | No hay un techo: hay **dos**, y de unidades distintas. Techo de esfuerzo = 656 h (stop-loss reexpresado en horas); techo de **caja** = número nuevo; y falta el instrumento que mide horas reales | 🔒 | pendiente de firma |
| A-06 | CS-39 | RunPod **no tiene tope mensual**: el único kill switch agregado real es el saldo prepago con auto-pay desactivado. Se cierra hoy, sin esperar a `T-41` | 🔒 | pendiente de firma |
| A-07 | CS-38 | Dar de alta la cuenta de RunPod **después** de CS-39, con 20 € prepagados: no por medir el arranque en frío, sino como seguro ante el riesgo FP16 1/64 de la Pascal | 🔒 | pendiente de firma |
| A-08 | CS-20 / I-12 | Idiomas de canto de Fase 1 = **{castellano, inglés}** y nada más, porque es lo único que G1 puede demostrar; prohibir la frase «50+ idiomas» | 🔒 | pendiente de firma |
| A-09 | **D-23** | Loudness por destino: −23 y −14 LUFS son norma y solo hay que aceptarlas; la elección real es el **tercer destino (podcast, −16)**, la tolerancia de broadcast y qué significa «stems sin normalizar» | 🔒 | pendiente de firma |
| A-10 | T-08 / G1-01 | El protocolo se contradice: la regla anti-inflación modifica puntuaciones **después** de romper el ciego, lo que el propio §8.1 declara causa de invalidez | 🔒 | pendiente de firma |
| A-11 | T-08 / G1-02 | El límite de 2 h de sesión es aritméticamente imposible con 30 pistas (~2 h 40 min solo de audio y puntuación); con 20 pistas sí cabe | 🔒 | pendiente de firma |
| A-12 | T-08 / G1-03 | `ffmpeg loudnorm` **no** garantiza «solo ganancia»: revierte a modo dinámico y comprimiría justo la serie propia, alterando D2 | 🔒 | pendiente de firma |
| A-13 | T-08 / G1-04 | La línea base de librería puede predeterminar el veredicto en las dos direcciones (auto-NO-GO o no-go inerte). ⚠️ **Única ficha del registro que puede cambiar cómo se calcula un umbral**: su opción (2) sustituye el denominador del **criterio 5 de no-go** («> 5 de los **10** briefs») por «> 5 de los briefs **comparables**», lo que con `N_comparables` ≤ 5 hace el NO-GO **imposible**. Se ofrece solo con cláusula de suelo (`N_comparables` ≥ 8); la recomendada es la **opción (0)**, que no toca el denominador | 🔒 | pendiente de firma |
| A-14 | T-08 / G1-05 | El criterio 3 (CLAP) favorece estructuralmente a la serie propia: declararlo **antes** de la sesión, sin tocar el umbral | 🔒 | pendiente de firma |
| A-15 | T-08 / G1-06 | El WER del 15 % no es interpretable sin medir antes el **suelo del transcriptor** sobre voz cantada (calibración de < 1 h, no toca el umbral) | 🔒 | pendiente de firma |
| A-16 | T-08 / G1-07 | La rúbrica es sólida en D2/D3/D5, pero D1 mezcla hechos medibles por script con juicio perceptual y penaliza a la librería por la duración | 🔒 | pendiente de firma |
| A-17 | T-08 / G1-08 | Los diez briefs son variados y verificados, pero **ninguno mide una canción completa** y cuatro dependen de control de estructura que la Fase 1 no ofrece | 🔒 | pendiente de firma |
| A-18 | T-08 / G1-09 | El manifiesto retroactivo de §10.1 incumple el invariante de `CLAUDE.md` (faltan `manifest_schema_version`, declaración de derechos y el hash del artefacto) | 🔒 | pendiente de firma |
| A-19 | T-08 / G1-10 | Ejecutar la **variante B** (propia + librería, sin Suno): no cuesta nada, cierra CS-03 y resuelve de paso el problema de las 2 h | 🔒 | pendiente de firma |
| A-20 | CS-22 (hallazgo) | Adelantar a F2 las fichas de licencia de **CLAP y HeartTranscriptor**: son precondición 9 de `T-09` y hoy viven en `T-33` (F5) — dependencia invertida | ⚙️ | lista para ejecutar |
| A-21 | CS-04 | Revertir el diferimiento del **Anexo A**: su función es el consentimiento informado **antes** del gasto, y el gasto ya está corriendo. Coste de firmar: 0 € | 🔒 | pendiente de firma |
| A-22 | CS-53 | El repositorio es **público** y se llama `suno-sondo-clone`: privatizar y renombrar hoy. La exposición medida es cero y la reversión deja de ser barata en cuanto haya un fork | 🔒 | pendiente de firma |
| A-23 | CS-46 | Mergear a `main` ahora (fast-forward limpio) **después** de A-22, y escribir la regla de cadencia de merge que hoy falta en `CLAUDE.md` | ⚙️ | lista para ejecutar |
| **B · Con fecha en un gate** | | | | |
| B-01 | D-adapter-410 | `adapter.py:410` declara Apache 2.0: es la licencia de ACE-Step **v1**; los pesos de 1.5 son **MIT**. El descriptor de `T-30` debe llevar lista por componente, no un `license` escalar | ⚙️ | lista para ejecutar |
| B-02 | CS-26 / I-17 | Retención en 5 cubos y, sobre todo, **seudonimizar el ledger**: letra por hash y usuario por referencia opaca, porque una cadena WORM no se puede rectificar | 🔒 | pendiente de firma |
| B-03 | CS-41 | El diferimiento de la firma del esquema del manifiesto está **mal fundado en un punto**: contradice un invariante vivo de `CLAUDE.md` y muerde antes de F5, en las pistas de G1 | 🔒 | pendiente de firma |
| B-04 | T-33 (ffmpeg) | Fijar build **LGPL-2.1+** (`--disable-gpl --disable-nonfree`) con aserción de build que falle si entra GPL: `apt-get install ffmpeg` trae una build GPL | ⚙️ | lista para ejecutar |
| B-05 | T-33 (dependencias) | Dar por verificado el bloque pip contra PyPI (cero copyleft) y cerrar el ítem ABIERTO del `Dockerfile` sobre Qwen3-Embedding (Apache-2.0 confirmado) | ⚙️ | lista para ejecutar |
| B-06 | CS-24 / I-15 | **Dos entornos, no tres**: el único artefacto irreversible es el ledger. `stage` se difiere a GC-01, que es literalmente su razón de ser | 🔒 | pendiente de firma |
| B-07 | CS-49 (T-86 / D-30) | Descartar `T-86` con su alcance actual (32 h / 1.920 €): no amortiza contra **una** máquina destino. D-30 se reclasifica a bloqueada por GC-01 | 🔒 | pendiente de firma |
| B-08 | CS-17 / I-09 | Fijar la **opción F** (keep-warm, 45 €/mes) como postura de referencia y descartar la G (128 €/mes): los 83 €/mes solo compran la primera espera del día | 🔒 | pendiente de firma |
| B-09 | CS-40 | No dar de alta el pod de producción ahora; corregir `evaluation.md` §6.2/§6.3 con la doble tarifa verificada y retirar el argumento «es ruido frente a 98.280 €» | 🔒 | pendiente de firma |
| B-10 | CS-23 / I-14 | La hipótesis de I-14 es falsa: bajar a 24 GB ahorra el 25 %, no el 50 %. Lo barato es **A40 48 GB a 0,44 $/h** (−55,6 % sobre L40S en el mismo tier) | ⚙️ | lista para ejecutar |
| B-11 | CS-16 / I-08 | Storage + egress a escala personal = **5–21 € en 24 meses**: cerrar I-08 y elegir **Cloudflare R2**, que elimina la incógnita de egress por construcción | ⚙️ | lista para ejecutar |
| B-12 | CS-48 | Los 300 €/mes de la librería de producción son el tier **corporativo con indemnización**; el que aplica a este proyecto cuesta **15,25 €/mes**. La comparación está inflada ~20× | 🔒 | pendiente de firma |
| B-13 | CS-22 / I-13b (raíz) | La causa raíz no es Demucs: es **MUSDB18**. Registrar el **criterio de tres ejes** (grant de pesos · dataset sin NC · formato **safetensors/ONNX sin excepciones**, `CLAUDE.md`:50) como regla del registry; los checkpoints en pickle se **convierten** con el auditor de opcodes de `build_artifact.py`, nunca se ejecutan | 🔒 | pendiente de firma |
| B-14 | CS-22 / I-13b (matriz) | Ningún separador del mercado pasa los tres ejes. Retirar de `tasks.md:1512` la afirmación no verificada sobre «pesos MIT verificados» | ⚙️ | lista para ejecutar |
| B-15 | CS-22 / I-13b (J-1) | La elección de separador depende de **una pregunta jurídica** (¿la NC del dataset se propaga a los pesos?), no de una comparación técnica | 🔒 | pendiente de firma |
| B-16 | CS-22 / I-13b (opción cero) | Antes de integrar un separador externo, spike de 2 h sobre la capacidad **Extract** que ACE-Step declara: superficie de licencia nueva = 0 gana a cualquier SDR | ⚙️ | lista para ejecutar |
| B-17 | CS-18 / I-13 | **Watermarking: no hoy.** El único candidato con licencia limpia (AudioSeal) es de voz a 16 kHz; el único de música (SilentCipher) no tiene grant de pesos. Degradar `T-57` a opt-in | 🔒 | pendiente de firma |
| B-18 | CS-47 | Audio de entrada: **30 s** fijos de referencia de timbre y **180 s** provisionales de cover — y el artefacto **no tiene encoder del VAE**, sin el cual C-08 no arranca | ⚙️ | lista para ejecutar |
| B-19 | CS-01 | Diferimiento **bien fundado**: el informe escrito de legal (I-05) no bloquea construir. Anotar en GC-01 §8a las 32 h ya reservadas | ⚙️ | lista para ejecutar |
| B-20 | CS-02 | Diferimiento **bien fundado**: I-05b condiciona lo que se puede **prometer**, no lo que se puede construir. Añadir la regla de «no prometer exclusividad» | ⚙️ | lista para ejecutar |
| B-21 | CS-03 | Diferimiento formalmente correcto pero más arriesgado de lo que sugiere «uso personal»: la salida barata es **no usar Suno** (ver A-19) | 🔒 | pendiente de firma |
| **C · Higiene** | | | | |
| C-01 | CS-28 / I-19 | UI **solo castellano en F1 y F2** (hoy la spec deja I-19 viva para F2 sin motivo), con un check de CI que rompa el build ante cadenas hardcodeadas | 🔒 | pendiente de firma |
| C-02 | CS-15 / I-04 | Cerrar I-04 (integración MAM) como **N/A en modo personal**, con la fórmula que el proyecto ya usó tres veces el 2026-09-01 | 🔒 | pendiente de firma |
| C-03 | CS-14 / I-03 | **No** cerrar I-03 como «no aplica»: no está fuera de alcance. Reclasificar de «Crítica» a inactiva y **reubicar** a las condiciones de reapertura de la Fase 4 | 🔒 | pendiente de firma |
| C-04 | CS-44 + CS-45 | Confluence y Jira: **no**, y cerrados con condición de reapertura escrita. Un ledger paralelo violaría la regla de ledger canónico de `CLAUDE.md` | ⚙️ | lista para ejecutar |
| C-05 | CS-52 | `to-pdf`: usar el Chrome del sistema — pero la variable **no está persistida en ningún sitio**, así que hoy la generación de PDF no es reproducible | 🔒 | pendiente de firma |

**Reparto:** 34 firmas del propietario · 15 ejecutables por un agente *(B-13 reclasificada de ⚙️ a 🔒 el 2026-09-01)*. **Ninguna** de las 49 mueve un umbral, una cifra ratificada ni el alcance aprobado **sin firma**; y **una sola de ellas —la opción (2) de A-13— podría mover el cálculo de un umbral incluso con firma**: está marcada, acotada por cláusula de suelo y tiene alternativa preferente que no lo toca.

---

## 1-bis. Contradicciones entre líneas: resueltas y con constancia

Las cinco líneas trabajaron en paralelo y se contradicen en nueve puntos. Se resuelven aquí, con el criterio de resolución explícito, y cada ficha afectada remite a este apartado. **Ninguna resolución cambia un umbral**; donde la resolución implica gasto, postura o alcance, sigue siendo del propietario.

### X-1 · Postura de producción: opción G vs. F vs. B

- **Línea 2 (CS-40)**: sustituir la G por la F «o directamente por la B».
- **Línea 3 (CS-17/I-09)**: fijar la **F** y descartar la G; y declara la **B explícitamente NO tolerable** (obliga a un arranque en frío en cada iteración de una ráfaga).
- **Línea 4 (CS-13/I-02)**: «la postura de producción recomendada sigue siendo la opción G, 128 €/mes».

**Resolución.** Prevalece **CS-17: opción F**. CS-13 no estaba recomendando la G, estaba *describiendo* el estado documental vigente (`evaluation.md` §6.2 la marca «Recomendada ✅»); ese estado es precisamente lo que B-08 y B-09 mandan corregir. La **B queda descartada por UX**, no por precio: sus cifras (3–8 €/mes a 100 gen/mes, ✅ recalculadas con tarifa verificada) se conservan solo como cota inferior de referencia. **Firma: propietario** (es postura de gasto) — fichas B-08 y B-09.

### X-2 · Umbral de conmutación GPU local → RunPod: 20 min/pista vs. 10 min/pista

- **Línea 2 (CS-38)**: conmutar a RunPod si el tiempo extrapolado por pista supera los **20 minutos**.
- **Línea 4 (CS-13)**: conmutar si supera los **10 minutos**, reutilizando una cifra **ya ratificada** (C-01, `spec.md`:284, p95 extremo a extremo).

**Resolución.** Prevalece **10 min**: CS-13 aporta procedencia para su número y CS-38 no aporta ninguna para el suyo, y la regla de este registro es no inventar cifras. Se hace constar que **no es un umbral de gate**: no toca G1 (7/10 ≥ 4/5, WER ≤ 15 %), solo decide **dónde** se generan las pistas que G1 juzga. Aun así lo firma el propietario, porque cambia dónde se ejecuta un gate — ficha A-04.

### X-3 · «CS-38 es opcional» vs. los criterios de aceptación de `T-03`

- **`pre-dev-checklist.md` §A ítem 8** marca la cuenta de RunPod como **opcional**.
- **`tasks.md` `T-03`** exige medir el arranque en frío contra el pod real y dice que «no se puede reproducir en local»; **CS-13** añade que `T-04` (2 inferencias concurrentes en 48 GB) va a RunPod **por definición**.

**Resolución.** Las dos cosas no pueden ser verdad a la vez. O se financia la cuenta (20 € prepagados, A-07) **o** se descoman formalmente esos criterios a una tarea nueva `bloqueada (recursos)`, anotando que S-01/S-01b quedan sin cerrar y que `evaluation.md` §6 pasa a informativo. **Lo que no se admite es el estado ambiguo**: una tarea permanentemente incompletable corrompe el numerador del alcance en el stop-loss. **Firma: propietario** — ficha A-07.

### X-4 · «Mandar J-1 al canal legal de G2» vs. el diferimiento de lo legal a GC-01

- **Línea 1 (CS-22/J-1)**: mandar la pregunta jurídica J-1 «al mismo canal legal de G2, como tercera consulta».
- **Línea 5 (CS-01, CS-02)** y `gobernanza.md` §8a/§8b: la deuda legal de G2 (informe escrito de I-05, respuesta de I-05b) está **diferida a GC-01**, porque G2 se cerró el 2026-08-18 con respuesta **informal del propietario**.

**Resolución.** En modo solo **no existe un canal legal externo**: ese canal es el propietario. J-1 no se «manda», se **acumula al lote de GC-01 §8**, junto a I-05 e I-05b y junto a las 32 h de asesoría ya reservadas (`g2-matriz-resultados.md` §1). Mientras J-1 no tenga dictamen profesional rige la **rama conservadora** (se asume que la NC del dataset se propaga): ningún separador entrenado sobre MUSDB18 entra en el pipeline. Lo que **sí** se puede hacer hoy y a coste cero es la consulta a Deezer / el comentario en el *issue* #898 de Spleeter. Fichas B-15 y B-19/B-20.

### X-5 · `training_data_declaration`: «no divulgada» vs. «declarada-por-el-proveedor-sin-auditar»

- **Línea 1 (D-adapter-410)**: «no divulgada» es **inexacto** — el model card de ACE-Step 1.5 ✅ **sí declara categorías** (Licensed Data / Royalty-Free-No-Copyright / Synthetic MIDI-to-Audio); el valor correcto es `declarada-por-el-proveedor-sin-auditar`, que es además el que ya escribe `D:\srv\ace-step\provenance\MANIFEST.json`.
- **Línea 5 (G1-09 y CS-04)**, `spec.md` §1.1 y el Anexo A de `g2-matriz-resultados.md` §8.1: dan por hecho que el manifiesto dirá **`no divulgada`**.

**Resolución.** El valor del campo es **`declarada-por-el-proveedor-sin-auditar`**. Hay que corregir la redacción en `spec.md` §1.1 y en el Anexo A para que los documentos no se contradigan. **La corrección no reabre G2 ni invalida la firma del Anexo A**: el riesgo sustantivo que ese anexo obliga a aceptar (corpus no auditable; alojar el modelo en casa no limpia la procedencia) es idéntico con una redacción o con la otra. Corrección de redacción: **agente** (B-01). Firma del Anexo A: **propietario** (A-21).

### X-6 · El denominador del stop-loss: 656 h o 688 h

No es una contradicción entre líneas, sino una **ambigüedad viva del ledger** que dos líneas señalan por separado (CS-49 y CS-19): `tasks.md`:43-48 mantiene las dos cifras porque `T-86` está propuesta y sin ratificar, y el stop-loss D-28 (>60 % del presupuesto) dispara a **394 h o a 413 h** según cuál se use.

**Resolución.** Hasta que el propietario firme B-07, el denominador único es **656 h / 39.360 €** — la cifra ratificada. Ninguna de las dos se toca sin firma. Un gate cuyo umbral depende de una decisión sin tomar no es un gate: por eso B-07 y A-05 deben cerrarse juntas.

### X-7 · La build de ffmpeg razona sobre un repositorio público que se va a privatizar

- **Línea 1 (T-33)**: la obligación de distribución del copyleft «se dispara al distribuir», y el repo **es público** (`github.com/daycry/suno-sondo-clone`), lo que agrava el riesgo de una build GPL.
- **Línea 4 (CS-53)**: privatizar el repositorio hoy.

**Resolución.** No se anulan. Privatizar (A-22) hace que **hoy** la respuesta a «¿distribuimos?» sea *no*; la build LGPL se fija igual (B-04), porque GC-01 sigue contemplando comercialización y porque cambiar de build **después** de que existan pistas obliga a revisar la ficha de procedencia de esas pistas. **Orden de ejecución: A-22 (privatizar y renombrar) → A-23 (merge) → B-04 (fijar la build).**

### X-8 · Dos versiones vivas del mismo invariante (firma del esquema del manifiesto)

- **`CLAUDE.md`**: «El esquema del manifiesto lo firma legal antes de implementarse».
- **`pre-dev-checklist.md` ítem 12 (CS-41)**: en modo personal la firma de legal se difiere a GC-01 y el propietario valida el esquema.
- **`tasks.md` `T-26`** sigue titulándose «Firma del esquema del manifiesto por legal» y exigiendo firma de legal archivada.

**Resolución.** Hay que **elegir una** y escribirla en los tres sitios. Un agente no puede hacerlo: cambia un invariante declarado innegociable. **Firma: propietario** — ficha B-03. Mientras tanto, la contradicción queda registrada aquí para que no se lea como «ya resuelto».

### X-9 · Watermarking: la válvula de escape de `T-57` **no** se activa

La lectura fácil es que `T-57` ya trae pre-autorizado el replanteo («si no hay librería con licencia comercial limpia disponible… el invariante se replanifica»). **No aplica**: ✅ AudioSeal **sí** tiene licencia limpia de código y de pesos (MIT explícito desde 2024-04-02). El motivo para no construirlo es **idoneidad y coste/beneficio** —watermarker de voz a 16 kHz sobre música a 44,1 kHz en FLAC/MP3-320—, no licencia.

**Resolución.** Al no caer en el supuesto pre-autorizado, la degradación de `T-57` a capacidad opt-in es un **cambio de alcance** y la firma el propietario — ficha B-17.
---

## 2. Bloque A — Bloquea hoy

> F2 está `en-progreso`, `T-08` está `en-revision` y `T-03`/`T-05` están a medias. Todo lo de este bloque o para el teclado hoy, o tiene una ventana que se mide en días.

### A-01 · D-31 — Banda de tolerancia de medida en el suelo de VRAM (cierra CS-51 / ítem 7-ter)

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** bloquea F2 entera desde ya

**(a) CRITERIO.** Una tolerancia de medida es legítima si y solo si cumple dos cotas comprobables por un tercero: **cota inferior** — es estrictamente mayor que la máxima discrepancia posible entre la VRAM de catálogo y la que reporta el driver para una tarjeta legítima de esa clase; **cota superior** — es estrictamente menor que la distancia al siguiente escalón comercial inferior, de modo que ninguna clase de tarjeta distinta entre por la banda. Si cumple ambas, corrige una unidad de medida y **no** relaja el requisito de hardware; si incumple la segunda, es una rebaja encubierta del umbral y debe tratarse como cambio de spec.

**(b) FUNDAMENTO.** ✅ Verificado ejecutando el 2026-09-01. Implementación: `apps/runner/spikes/_timing.py:111` mantiene `VRAM_FLOOR_MB = 8*1024 = 8192`; `:156` añade `VRAM_FLOOR_TOLERANCE_MB = 64`; la comparación real está en `:438` → `if vram_total_mb + VRAM_FLOOR_TOLERANCE_MB < VRAM_FLOOR_MB`. Evidencia medida (`_timing.py:118-124`): `cuDeviceTotalMem_v2 = 8.589.672.448 B = 8191,75 MiB` → truncado a **8191 MB**; `nvidia-smi` Total 8192 MiB, Reserved 132 MiB, libre ~6988 MiB. Aritmética recomprobada: `8*1024³ = 8.589.934.592`; la diferencia es **262.144 B = 0,25 MiB**. Tests: `pytest tests/test_vram_floor.py -q` → **13 passed**; suite completa → **85 passed in 2,87 s**, cubriendo el caso frontera 8191, el borde inclusivo 8128, el 8127 que debe abortar y el 6144 que debe seguir abortando. Umbral de spec afectado: `spec.md`:60 (D-06) y :84 (D-29). ✅ No existe ninguna D-31 ni D-32 en la documentación (grep sin resultados): el identificador libre es **D-31**.

**(c) RECOMENDACIÓN.** Ratificar el siguiente texto, para `spec.md` §2 y para el cierre de CS-51:

> **D-31 — Banda de tolerancia de medida en el suelo de VRAM (no altera el suelo de 8 GB de D-06)**
>
> *Decisión.* Se **conserva sin cambios** `VRAM_FLOOR_MB = 8192` (8 GB, suelo con offloading de D-06 / `spec.md` §11.1, reforzado por D-29) como **suelo declarado del proyecto**. Se añade `VRAM_FLOOR_TOLERANCE_MB = 64` como **banda de tolerancia de medida**: la comprobación pasa de `vram_reportada_mb < 8192` a `vram_reportada_mb + 64 < 8192`, es decir, un **suelo efectivo de 8128 MB medidos**. La magnitud comparada es `torch.cuda.get_device_properties(0).total_memory` truncada por división entera a MB.
>
> *Qué corrige.* No relaja el requisito de hardware: corrige una **incoherencia de unidad de medida**. Los 8192 de D-06 son VRAM **de catálogo**; lo que el código compara es VRAM **reportada por el driver**, que en toda tarjeta real de 8 GB es menor. Medido en la máquina de referencia dentro del contenedor: 8.589.672.448 B = **8191 MB**. Con la comparación estricta anterior, `decide_offloading()` devolvía `NO VIABLE` y `adapter._load_sync()` abortaba antes de tocar los pesos: **el suelo de 8 GB de D-06 era inalcanzable por construcción para exactamente la clase de tarjetas que D-06 quería admitir**.
>
> *Por qué 64 MB y no otra cifra.* **(1) Cota inferior**: la discrepancia medida es 0,25 MiB; 64 MiB deja un margen de **256×** sobre lo observado, para cubrir variaciones de driver y plataforma (WDDM/TCC, Linux) que hoy no se pueden medir. **(2) Cota superior**: el escalón inmediato inferior son 6 GB (6144 MB), a **2048 MB** de distancia; 64 es **1/32** de esa distancia. Cualquier valor entre 1 y 2047 cumpliría ambas de forma trivial; **64 es el mayor valor redondo que además mantiene fuera a las tarjetas de 8 GB con ECC activado** (~7680 MB utilizables): con tolerancia 512 el suelo efectivo caería a 7680 y admitiría esa clase, que **no** cumple D-06 en memoria realmente utilizable.
>
> *Qué queda fuera con el suelo efectivo de 8128 MB.* Toda tarjeta que reporte menos de 8128 MB: **6 GB y por debajo** (GTX 1060 6 GB, GTX 1660/Super/Ti, RTX 2060 6 GB, RTX 3050 6 GB, y todo lo de 4 GB o 2 GB); **tarjetas de 8 GB con ECC activado** (remedio documentado: `nvidia-smi -e 0`, o no usarlas); y **todo entorno sin CUDA detectable**, que sigue cayendo en la rama `None`, solo válida con `--mock`. **Entran** —y ese es el objetivo— todas las tarjetas de 8 GB reales, que reportan entre ~8188 y 8191 MB.
>
> *Qué NO ratifica esta decisión.* No ratifica que ACE-Step 1.5 sea ejecutable en la GTX 1070. Ver A-03.
>
> *Condición de falsación.* Si aparece una tarjeta de 8 GB legítima y sin ECC que reporte **menos de 8128 MB**, esta decisión queda falsada y exige una **nueva decisión explícita**, nunca un ensanchamiento silencioso de la banda.
>
> *Arrastres que esta decisión manda cerrar.* Ver A-02.
>
> *Trazabilidad.* `apps/runner/tests/test_vram_floor.py`, 13 tests en verde; suite completa del runner, 85 tests en verde (verificado 2026-09-01).
>
> | Campo | Valor |
> |---|---|
> | Decide | **Daycry (propietario)** — toca un umbral citado en `spec.md` §11.1 |
> | Fecha | ⚠️ pendiente |
> | Firma | ⚠️ pendiente |

**(d) CONSECUENCIA DE NO DECIDIR.** Bloqueo total e inmediato de F2: `T-03` (`ace_step_shim.py`) y `T-05` no pueden ejecutar **ninguna** medición real, porque `decide_offloading()` devuelve `NO VIABLE` y el adapter aborta antes de cargar pesos. Sin `T-03`…`T-07` no hay `T-09`, y sin `T-09` no se desbloquean las **589 h / 35.340 €** de F4–F9 (`g1-protocolo.md` §1.1). El código del arreglo ya está escrito y en verde: **el coste del retraso es exactamente el tiempo que tarde la firma**. La única alternativa a firmar es revertir la tolerancia y aceptar que el proyecto no tiene GPU, lo que empuja toda la Fase 0 a RunPod, rompe la decisión del 2026-08-18 de coste cloud cero y activa A-06/A-07 como obligatorios.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Toca un umbral citado en `spec.md` §11.1 (D-06) y D-29. Un agente puede implementarlo y probarlo —ya lo hizo—, pero no puede ratificar el número.

---

### A-02 · CS-51-b — Corrección factual en `_timing.py` y arrastre del «8192» en dos mensajes al operador

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Ventana:** con A-01

**(a) CRITERIO.** Un comentario que documenta una decisión de umbral es **parte de la evidencia**: si su cifra es falsa, la evidencia no es auditable. Y un mensaje de error que cita un mínimo distinto del aplicado manda al operador a comprar hardware que no necesita.

**(b) FUNDAMENTO.** ✅ `apps/runner/spikes/_timing.py:122` dice «frente a los 8192 MB del envase: faltan **294.912 B**». Recomprobado: `8*1024³ − 8.589.672.448 = 262.144 B` (256 KiB). El propio comentario de `_timing.py:150-155` reconoce el arrastre: `capability_probe.py:2095` y `adapters/ace_step/adapter.py:582-583` imprimen «Mínimo exigido: {VRAM_FLOOR_MB} MB» = 8192 mientras el mínimo aplicado es 8128.

**(c) RECOMENDACIÓN.** Dos ediciones de una línea, sin cambio de comportamiento: **(1)** corregir 294.912 → **262.144 B** en `_timing.py:122`; **(2)** en `capability_probe.py:2095` y `adapter.py:582-583`, imprimir el suelo efectivo (`VRAM_FLOOR_MB - VRAM_FLOOR_TOLERANCE_MB`) y, entre paréntesis, el nominal — exactamente como ya hace `decide_offloading()` en `_timing.py:441-444`. Añadir un test que asegure que los tres mensajes citan la misma cifra, para que no vuelvan a divergir. **Nota de semántica que hay que anotar y no unificar:** `apps/runner/spikes/vram_profile.py:987` compara `fits_floor_8gb` contra 8192 como techo de **pico**, que es otra magnitud; se conserva a propósito.

**(d) CONSECUENCIA DE NO DECIDIR.** Impacto técnico bajo, impacto de credibilidad alto: la primera persona que audite D-31 comprobará la resta y encontrará un número inventado en el fichero que sostiene la decisión. Y en cada arranque fallido el operador leerá un mínimo que no es el aplicado.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Corrección factual y de mensajería, sin efecto sobre el comportamiento ni sobre el umbral.

---

### A-03 · CS-51-c — Ratificar D-31 no ratifica viabilidad: la restricción real es la VRAM **libre**

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Ventana:** antes de leer D-31 como un «GO»

**(a) CRITERIO.** Un umbral solo es útil si mide la magnitud que restringe. Si el umbral mide memoria **total** y lo que impide ejecutar es la memoria **libre**, pasar el umbral no informa de nada y crea una falsa sensación de vía libre.

**(b) FUNDAMENTO.** ✅ Artefacto fusionado ACE-Step 1.5 fp16 = **6.163.551.450 B = 5.878 MiB**, depositado íntegro en VRAM por `load_file()` **antes** de que exista el pipeline que decidiría el offloading (razonamiento explícito en `_timing.py:444-452` y en `pre-dev-checklist.md` ítem 7-bis/CS-50). VRAM libre medida con el escritorio de Windows arrancado: **~6988 MiB** (`_timing.py:123-124`). Margen resultante: **~1110 MiB** para activaciones, contexto CUDA, tokenizer y decodificación del VAE. ⚠️ **Sin medir.** Además la GTX 1070 es Pascal sm_61: sin BF16 ni tensor cores (`spec.md` I-21), así que **S-02 (150 s/pista) no aplica** a esta máquina.

**(c) RECOMENDACIÓN.** Incluir el párrafo «Qué NO ratifica esta decisión» dentro del texto de D-31 y añadir a `T-03` un criterio de aceptación explícito: **medir y publicar** VRAM libre antes de cargar, pico durante inferencia y tiempo por pista en las duraciones de los diez briefs de G1 (30 s a 3:00). Si el pico supera la libre, la salida correcta es **documentar la excepción y medir en RunPod** (confirmación 13 de `spec.md` §8), **nunca** volver a tocar el suelo.

**(d) CONSECUENCIA DE NO DECIDIR.** Riesgo de leer el «GO» de D-31 como «la máquina sirve», arrancar `T-09`, generar 30 pistas y descubrir a mitad de la sesión de G1 que la serie propia no es reproducible en ese hardware. Eso invalida la sesión (`g1-protocolo.md` §8.1 exige parámetros de inferencia idénticos en los diez briefs) y obliga a repetirla entera: ~9 h de escucha más la regeneración.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Es una aclaración de alcance de una decisión ajena, no una decisión de umbral.

---

### A-04 · CS-13 / I-02 — GPU propia o cloud: respuesta partida, con regla de conmutación escrita

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes del primer lote largo de `T-03` — esta semana

**(a) CRITERIO.** Una GPU propia sustituye al cloud solo si cumple las tres a la vez: **(a)** supera el suelo declarado en la spec, **(b)** entrega el rendimiento **medido** que exige el contrato del producto, **(c)** puede reproducir lo que se necesita medir. Falla una, no sustituye. Y para la Fase 0 hay un segundo criterio que zanja el debate: **cuando el coste cloud de una fase es inferior al coste de deliberar sobre él, se alquila y se deja de deliberar**.

**(b) FUNDAMENTO.** **(a) Suelo**: ✅ la GTX 1070 reporta 8191 MiB frente al `VRAM_FLOOR_MB = 8192`; pasa, pero literalmente raspando (ver A-01). **(b) Rendimiento**: ⚠️ **NO MEDIDO**, y es el núcleo de la respuesta. `tasks.md`:151 lo dice sin ambigüedad: «ninguna de las mediciones que definen `T-03` está hecha», falta el shim, y el riesgo nº 1 está identificado y **no medido** — «GP104 ejecuta FP16 nativo a 1/64 del FP32; si cuBLAS no promociona a FP32 en sm_61, las 10 pistas de G1 pasan de ~20 min a un orden de horas». No es teórico: el artefacto construido es fp16 sobre una arquitectura sin tensor cores. **(c) Reproducibilidad**: imposible por dos vías — el arranque en frío no se puede medir en local (criterio de aceptación explícito de `T-03`, `tasks.md`:158-161; excepción declarada en `improvement-plan.md`:169) y `T-04` mide 2 inferencias concurrentes en los 48 GB de una L40S (`tasks.md`:174-188), pregunta que 8 GB no pueden responder ni en principio. **Economía calculada**: ✅ L40S RunPod 0,79 $/h (`evaluation.md`:219) × 0,92 (`.claude/rates.json`) = **0,727 €/h**; todo el consumo cloud residual de F2+F3 cabe en 15–20 GPU-h ⇒ **11–15 €**. Contra la tarifa de 50 €/h de `rates.json`, **15 minutos de tiempo del propietario compran 17 GPU-h de L40S**. `evaluation.md`:225 ya condicionaba la opción D on-premise a «solo gana si Daycry YA TIENE GPUs infrautilizadas»: tiene una, pero no de la clase que esa opción contemplaba (Pascal de 2016, 8 GB, sin BF16).

**(c) RECOMENDACIÓN.** Cerrar I-02 en **dos mitades**. **Mitad 1 — SÍ para F2/F3**: la GTX 1070 es la máquina de desarrollo y contenerización, coste marginal ~0, y ya ha dado resultado verificado (imagen `ace-step-runner:t05` construida y ejecutada con `--gpus all` sobre la GPU real). **Mitad 2 — NO como sustituto de la postura de producción**: la 1070 falla (b) por medir y (c) por diseño. **Regla de conmutación, para que esto no se rediscuta cada semana**: ejecutar primero el *smoke test* cronometrado de 30 s que `tasks.md`:151 ya declara obligatorio, extrapolar linealmente a una pista de 180 s y, **si el reloj extrapolado de una pista supera los 10 minutos, las 10 pistas de G1 y el resto de `T-03` se generan en RunPod**, documentando el factor de conversión (que es justo lo que pide `tasks.md`:160). Los 10 minutos son una cifra **ya ratificada** (C-01, `spec.md`:284, p95 extremo a extremo con pod caliente), reutilizada como referencia operativa: **no se crea ningún umbral nuevo ni se toca ningún gate** — ver **X-2**, que descarta el 20 min propuesto por la línea 2 por no tener procedencia. `T-04` va a RunPod por definición, sin discusión: es la excepción que su propio criterio de aceptación contempla (`tasks.md`:188). Y no reabrir la opción D (comprar tarjeta): con ~41,7 h de GPU/mes no amortiza (`evaluation.md`:225).

**(d) CONSECUENCIA DE NO DECIDIR.** **Bloquea ahora mismo**, y es el único ítem de su línea que lo hace. `T-03` está `en-progreso` y su siguiente paso es el shim; sin regla de conmutación escrita, el escenario realista es descubrir a mitad de la generación de G1 que una pista tarda horas, tras haber quemado días de reloj del propietario — a 50 €/h, cientos de euros de tiempo para ahorrar 11–15 € de GPU. Peor: la tentación en ese punto sería recortar el número de pistas o su duración para que quepan, y eso ya no es infraestructura, es **degradar la muestra de G1**. La regla existe para que esa tentación no llegue a plantearse.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Decide dónde se ejecuta un gate y compromete gasto cloud, por pequeño que sea.

---

### A-05 · CS-19 / I-11 — No hay un techo de presupuesto: hay dos, y de unidades distintas

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** el riesgo se materializa el día que se abra la cuenta de RunPod (A-07)

**(a) CRITERIO.** Un techo presupuestario es un control útil solo si **(i)** la unidad medida es el recurso escaso real, **(ii)** superarlo produce una consecuencia que alguien ejecuta y **(iii)** existe un instrumento que mida el consumo. Si falla (i) es teatro; si falla (iii) el gate es indecidible aunque esté escrito. **Corolario en modo personal**: si el € es una transformación lineal de las horas y el propietario es el único ejecutor, el techo en € y el techo en horas son **el mismo control con distinta etiqueta** —uno de los dos sobra— pero **el desembolso en caja es una magnitud independiente que ninguno de los dos mide**.

**(b) FUNDAMENTO.** **(1)** ✅ El € es una identidad, no una medida independiente: `.claude/rates.json`:3,17 (`tarifaHora` 50, `margenContingencia` 0.2) → 656 × 1,2 × 50 = **39.360 €** exactamente. Un grado de libertad, no dos. **(2)** ✅ `spec.md`:422 (I-11): «el presupuesto lo decide el propietario; las cifras en € son informativas en modo personal»; `spec.md`:429 (I-18, cerrada): «N/A en modo personal». **(3)** ✅ **El stop-loss no protege la caja, y es aritmética**: `evaluation.md`:934 (D-28) dispara con «>60 % del **presupuesto** de la Fase 1 con <40 % del alcance»; quemar 500 € de GPU en un fin de semana es el **1,3 %** de 39.360 € → el gate no dispara. Y `evaluation.md` §6.3 punto 6 nombra ese riesgo exacto (R-17): «un bucle de reintentos en un proveedor medido es la forma clásica de fundir el presupuesto un fin de semana». **(4)** ✅ **El instrumento no existe**: no hay ningún registro de horas reales en `tasks.md` ni en `improvement-plan.md`, solo estimaciones. El stop-loss está escrito y **hoy es indecidible**. **(5)** ✅ El techo real del proveedor es peor de lo que asume el plan: `docs.runpod.io/accounts-billing/billing` — «Runpod accounts have a default spend limit of **$80 per hour** across all resources». Es horario, no mensual; RunPod **no ofrece** tope mensual. **(6)** Caja real en modo personal, con precios verificados: GPU cloud 0–160 €/mes según postura; almacenamiento <5 €/mes; electricidad de la GPU local 0,036–0,052 €/h (300 W a PVPC medio 2026 de 0,1429 €/kWh; media de los tres últimos meses 0,1722). La caja total puede mantenerse **por debajo de 25 €/mes o dispararse a 200+ €/mes sin que ninguna cifra del plan se entere**.

**(c) RECOMENDACIÓN.** Cerrar I-11 con esta redacción, **que no toca el umbral del gate**: «No existe techo en euros. Existen dos techos, en unidades distintas.»

- **(A) Techo de esfuerzo** = las **656 h** ya ratificadas. No es un número nuevo. Reexpresar el stop-loss D-28 en horas para hacerlo decidible, con esta redacción exacta: **dispara si `horas_reales > 393,6 h` Y `alcance entregado ponderado por horas < 40 % de 656 h`** (es decir, **< 262,4 h** de esfuerzo estimado acumulado en tareas cerradas), sobre un denominador de **54 tareas / 656 h** y con la ponderación tomada de las horas estimadas que **ya existen tarea a tarea** en `tasks.md` — no hay que inventar ningún dato nuevo.
  - ⚙️ **Errores de dato corregidos hoy (agente), los tres en dirección permisiva.** **(i) El denominador son 54 tareas, no 53**: `tasks.md`:37 («Subtotal aprobado y ejecutable (F1–F9) | **54 tareas** | 656 h | 39.360 €»), `tasks.md`:1356 («Las **54 tareas** de este documento…»), `improvement-plan.md`:304 («Las **54 tareas** de `tasks.md`, incluida `T-85`») y `CLAUDE.md` («T-01…T-53 + T-85» = 54). El «53» solo sobrevive en `tasks.md`:2055, un apunte de changelog **anterior** a la ratificación de `T-85` del 2026-08-18. **(ii) Redondeo de horas**: 60 % de 656 h = **393,6 h**, no «> 394 h». **(iii) Redondeo del alcance**: 40 % de 54 = **21,6**; escribir «< 21» significa que con 21 tareas cerradas (**38,9 %**, por debajo del 40 %) el gate **no** dispararía, que es exactamente lo que el gate existe para impedir.
  - **Por qué ponderado por horas y no por conteo de tareas.** De las 54, **cuatro valen 0 h** — `T-01` y `T-02` (`tasks.md`:28), `T-09` (`:30`) y `T-53` (`:36`) — y dos de ellas ya están **completadas**. Un conteo equiponderado marcaría **3,7 % de «alcance entregado» el día 1 de F2, con cero horas de trabajo hechas**, e introduciría un sesgo permanente a favor de no disparar. Si aun así se quiere conservar el conteo simple como criterio **subsidiario**, la redacción correcta es «**≤ 21 de 54** tareas» **excluyendo del numerador las cuatro tareas de 0 h**, porque cerrarlas no entrega alcance; nunca «< 21 de 53».
  - Con estas tres correcciones aplicadas, la reexpresión es una **traducción** fiel del 60 %/40 % original a la unidad medible, **no una relajación** — que es lo que la redacción anterior sí era, por cuatro vías acumulativas. 🔒 La **redacción final del gate la firma el propietario**, porque toca la *redacción* de un gate aunque no su umbral; las correcciones de dato (i)–(iii) son ⚙️ y ya están aplicadas aquí.
- **(B) Techo de caja** = número **nuevo** y pequeño, que hoy no existe en ningún documento y es el único que puede vaciar una cuenta sin avisar. Propuesta a ratificar: **25 €/mes duros** mientras la Fase 0 corra en GPU local, ampliables por decisión explícita al activar F6/F7. Se implementa con el mecanismo de A-06 (saldo prepago con auto-pay desactivado), no con un documento. Coherencia: los **20 €** prepagados de A-07 caben bajo este techo.
- **(C) Instrumento**: añadir una columna **«horas reales»** a `tasks.md` y anotarla al cerrar cada tarea. Sin esto, (A) no es ejecutable. Coste: minutos por tarea.
- **(D)** Descartar explícitamente por escrito la idea de un techo en € agregado: en modo personal es indistinguible del techo de horas y añade una cifra más que mantener sincronizada.

**(d) CONSECUENCIA DE NO DECIDIR.** Tres cosas, todas ya en curso: **(1)** el stop-loss está escrito y no se puede evaluar por falta de contador de horas — el checkpoint al cierre de C-13 llegará y no habrá dato con el que convocarlo; **(2)** no hay ningún límite de caja en ningún sitio y el único disponible en el proveedor es de **80 $/hora**, que a L40S permite ~101 pods simultáneos antes de frenar: un fallo de bucle podría gastar cientos de euros en horas sin que nada lo pare, y el kill switch agregado `T-41` no llega hasta F6; **(3)** la ambigüedad 39.360/41.280 de B-07 se propaga al denominador (ver **X-6**). El riesgo (2) se materializa **el mismo día que se abra la cuenta de RunPod**, lo que fija el orden correcto: **primero A-06, después A-07**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** (A) reescribe la redacción de un gate; (B) fija un límite de gasto nuevo.

---

### A-06 · CS-39 — Tope de gasto: el único techo duro real es el saldo prepago con auto-pago desactivado

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de A-07, siempre

**(a) CRITERIO.** Un tope de gasto solo cuenta como control si es un **mecanismo que el proveedor ejecuta**, no un propósito escrito en un documento. **Regla de verificación**: antes de dar por bueno un control, hay que leer qué mecanismo ofrece realmente el proveedor y **con qué granularidad**, porque un control con la granularidad equivocada (por trabajo, por hora) no acota el gasto **agregado**, que es el que arruina.

**(b) FUNDAMENTO.** ✅ Fuente oficial `docs.runpod.io/accounts-billing/billing` (obtenido 2026-09-01), citas literales: **(1)** «Runpod accounts have a default spend limit of **$80 per hour** across all resources» — horario, no mensual; a L40S Secure (0,99 $/h) permite ~80 pods concurrentes antes de frenar. **(2)** «When your balance reaches $0, Runpod automatically stops all of your running Pods» — **este es el único mecanismo de parada dura y agregado que existe**. **(3)** «Auto-pay automatically reloads your account balance when it falls below a threshold» — el auto-pago **desactiva** el mecanismo (2) y convierte el saldo en un grifo. **(4)** «Pods without a network volume are terminated, and their data can't be recovered» cuando el saldo llega a 0. **(5)** «Storage charges continue to accrue on network volumes while your Pods are stopped»: 30 GB × 0,07 $/GB-mes = **2,10 $/mes** de fuga residual tras el corte. **(6)** RunPod **no publica** tope mensual en ninguna página de su documentación de facturación. Contraste con el plan: `pre-dev-checklist.md` §A ítem 9 diagnostica bien («solo hay `max_gpu_seconds` por trabajo; el kill switch agregado `T-41` llega en F6») pero asume que hay que esperar a `T-41`, y la evidencia dice que no.

**(c) RECOMENDACIÓN.** Cerrar CS-39 **hoy**, con un control de cuatro líneas ejecutable en la propia alta de la cuenta y sin escribir código: **(1)** prepagar un importe fijo y pequeño (**20 €**, coherente con A-05 y A-07); **(2)** **no** guardar tarjeta / dejar auto-pay **desactivado** — el saldo es el kill switch; **(3)** adjuntar *network volume* a cualquier pod cuyo estado importe (sin él, el corte por saldo **termina** el pod y los datos no se recuperan) y **borrarlo al cerrar la sesión**, para que no siga facturando; **(4)** anotar el límite horario por defecto de 80 $/h como conocido y **no solicitar su ampliación**. Documentarlo en `apps/runner/spikes/README.md` §9, que es donde el checklist ya apunta. **Consecuencia de alcance que merece firmarse:** esto **no sustituye a `T-41`** (kill switch agregado de F6, dentro de las 112 h ratificadas de C-14); es un control provisional para F2 que evita adelantar `T-41`. Dejarlo escrito así para que nadie descome `T-41` pensando que ya está resuelto.

**(d) CONSECUENCIA DE NO DECIDIR.** Si A-07 se ejecuta antes que A-06 —que es el orden que sugiere la numeración del checklist— se abre una cuenta con tarjeta y sin tope agregado: literalmente el escenario **R-17** que `evaluation.md` §6.3 punto 6 declara obligatorio prevenir. Con el tope por defecto de 80 $/h, un fin de semana de 48 h con un bucle de reintentos tiene un techo teórico de **3.840 $ ≈ 3.533 €**: el 9 % del presupuesto completo de Fase 0+1, en caja real, por un fallo de software. Coste de evitarlo: **cero euros y unos minutos de configuración**. Es la mejor relación coste/riesgo de todo este registro.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Fija un límite de gasto y una postura de facturación.

---

### A-07 · CS-38 — Cuenta de RunPod: sí, pero como seguro ante el riesgo FP16 1/64, no por el arranque en frío

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** `T-03` está `en-progreso` y no puede cerrarse sin ella

**(a) CRITERIO.** Una medición se ejecuta cuando su coste es menor que (coste de decidir mal sin ella) × P(decidir mal). Y se ejecuta **ahora** cuando su resultado cambia una decisión que se está tomando ahora. **Regla añadida, específica de ledgers**: una tarea cuyos criterios de aceptación son imposibles de satisfacer con los recursos disponibles **no puede quedar en estado ambiguo** — o se financia o se descoma formalmente, porque una tarea permanentemente incompletable corrompe el numerador del alcance en el stop-loss.

**(b) FUNDAMENTO.** **(1) La medición por sí sola no se paga a volumen personal**: lo que informa S-01/S-01b es el factor de facturación (1,60× / 1,90× / 3,10×, `evaluation.md` §6.4) que separa la opción B de la F; a 1.000 gen/mes son 13 €/mes, pero a 100 gen/mes son **1,3 €/mes** — con coste de medir ~10 €, el equilibrio está a ~8 meses. Y en modo GPU local no hay arranque en frío en absoluto. **(2) Pero `T-03` no puede cerrarse sin ella**, y es un hecho del ledger: ✅ `tasks.md` `T-03` (estado `en-progreso`) exige «Arranque en frío medido con imagen cacheada (rango esperado 2-6 min) y sin cachear (5-12 min)» y «Medir arranque en frío en 3 escenarios contra el pod de RunPod», y la descripción es explícita: «no se puede reproducir en local y SIGUE MIDIÉNDOSE contra el pod real». Marcar CS-38 como «opcional» (`pre-dev-checklist.md` §A ítem 8) **contradice** esos criterios — ver **X-3**. **(3) La razón de peso es otra**, y el propio repo la nombra: `tasks.md` `T-03`, «Lo que sigue abierto»: «Riesgo nº 1 identificado y NO medido: GP104 ejecuta FP16 nativo a 1/64 del FP32…». ✅ Verificación externa: NVIDIA Pascal Tuning Guide — «On GP104, FP16 throughput is lower, 1/64th that of FP32». Y el artefacto está **forzado** a FP16 por aritmética de VRAM (`build_artifact.py`, docstring: fp16 = 5.878 MiB cabe con 810 MiB de holgura; BF16 → OOM garantizado; FP32 = 9.132 MiB → imposible). Es decir: **la máquina de referencia está obligada al dtype en el que su silicio es peor por un factor documentado de 64**. **(4) Coste verificado del seguro**: L40S Community 0,79 $/h → 10 pistas de G1 aunque tarden 10 min cada una = **1,32 $**; sesión completa de exploración de 8 h = **6,32 $ = 5,81 €**; medición de arranque en frío (10 arranques, ~2 h de pod) = **1,45 €**; *network volume* de 30 GB = **1,93 €/mes**. **Total por debajo de 15 €.** Egress 0 $ (✅ verificado).

**(c) RECOMENDACIÓN.** Dar de alta la cuenta, **en este orden estricto**: **(1)** primero cerrar **A-06** (abrir la cuenta antes que el tope es exactamente el orden que produce R-17); **(2)** prepagar **20 €**, sin tarjeta guardada; **(3)** **disparador escrito para usar el crédito**, no para dejarlo aparcado: la regla de conmutación de **A-04** (10 min/pista extrapolados). ⚠️ La línea 2 proponía 20 min/pista; se descarta por falta de procedencia — ver **X-2**. **(4)** Corregir la contradicción del ledger: si aun así se decide **no** abrir cuenta, hay que descomar formalmente de `T-03` los dos criterios de arranque en frío a una tarea nueva `bloqueada (recursos)` y anotar que S-01/S-01b quedan sin cerrar y que `evaluation.md` §6 pasa a informativo. **Lo que no es aceptable es dejar `T-03` con criterios que nadie puede satisfacer.** **(5)** Higiene: borrar el *network volume* al terminar la sesión — ✅ sigue facturando con los pods apagados.

**(d) CONSECUENCIA DE NO DECIDIR.** Bloqueo concreto y con fecha: `T-03` está `en-progreso` y **no puede pasar a `completado`, ni hoy ni nunca**, sin un pod real. Como `T-03` bloquea `T-04` (3 h) y alimenta S-02/S-02b, la Fase 0 queda con una tarea arrastrándose indefinidamente. Efecto de segundo orden sobre el gate: el stop-loss se evalúa como «<40 % del **alcance** entregado»; una tarea incompletable por construcción hace que el numerador nunca llegue, lo que a la larga **dispara el stop-loss por un motivo administrativo en vez de por un motivo real**. Coste del retraso: 0 € de caja, pero el riesgo FP16 1/64 sigue sin cuantificar y sin plan B. Coste de la alternativa: **20 € y ~30 min de alta**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Alta de proveedor, gasto y —vía el disparador— dónde se ejecuta el gate G1.

---

### A-08 · CS-20 / I-12 — Idiomas del canto en Fase 1: castellano + inglés, porque es lo único que G1 puede demostrar

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** bloquea `T-08` → `T-09`; `T-08` está `en-revision` HOY

**(a) CRITERIO.** Fase 1 declara «soportado» un idioma de canto **solo** si se cumplen dos condiciones: **(a)** hay al menos un brief de G1 en ese idioma y **(b)** su WER medido cumple el umbral ya fijado de G1 (≤ 15 % medio, ≤ 25 % peor caso). Ni la model card ni el tokenizer sirven como fundamento: el tokenizer **no restringe nada** y la model card no publica ni lista ni métrica por idioma. Todo lo demás es «permitido sin garantía», etiquetado como tal en la UI. **Regla derivada: el alcance de idiomas no lo fija un deseo ni un README, lo fija el instrumento de medida que ya existe.**

**(b) FUNDAMENTO.** Evidencia local primaria (pesos descargados, revisión `19671f40…`): **(1)** ✅ La model card **no enumera idiomas ni publica métrica**: `README.md:47` dice literalmente «- **Language(s):** [50+ languages]», y `:43` ata el «50+ languages» a «strict adherence to prompts», no a la pronunciación cantada; la guía oficial (`docs/en/ace_step_musicians_guide.md`) nombra ~19 idiomas en lista indiferenciada, sin ranking, sin *caveats* y sin decir si los 50+ son probados o nominales. **(2)** ✅ **El tokenizer no pone ningún límite**: `modeling_acestep_v15_turbo.py:585-586` define `self.embed_tokens = nn.Linear(config.text_hidden_dim, config.hidden_size)` y `:615-617` impone `input_ids is None` + `inputs_embeds is not None` — el *lyric encoder* ingiere **embeddings**, no tokens; `text_hidden_dim: 1024` == `hidden_size: 1024` de Qwen3-Embedding-0.6B, cuyo `tokenizer.json` es BPE **ByteLevel** (vocab 151.643): cualquier texto Unicode codifica sin OOV. Conclusión dura: **la cobertura de idiomas es una cuestión empírica de datos de entrenamiento, no una capacidad declarada por ningún config** (el `vocab_size: 64003` del config no se usa en el modelo turbo: grep sin resultados). **(3)** ✅ **No existe selector de idioma en nuestro pipeline**: `generate_audio(...)` (`:1780-1801`) no tiene ningún argumento de idioma; el «select vocal language in interface» de la guía pasa por el **LM planner** (`acestep-5Hz-lm-*`), que **no está en nuestro artefacto** (`ace_step_1_5.provenance.json`: dit 677 + text_encoder 310 + vae_decoder 182 + aux 8). El idioma solo se transmite por el texto literal de la letra y por el prompt de estilo, y eso hay que **probarlo**, no suponerlo. **(4)** ✅ La decisión ya está escrita y a punto de ratificarse: `g1-protocolo.md`:228 «Reparto de la muestra (comprobado): **6 briefs en castellano / 4 en inglés**» y `:388` «Se transcribe **forzando el idioma declarado del brief**»; el idioma ya es eje puntuable (`:141` penaliza «el idioma del canto no es el pedido»; `:180` premia la prosodia del idioma pedido). **(5) Riesgo que hay que decir antes de ratificar** (no una recomendación de cambiarlo): el 60 % de la muestra es castellano y ⚠️ las fuentes de terceros (no verificadas de primera mano) sitúan [es] en el top-10 pero por detrás de [en]/[zh]/[ru]. **G1 quedará dominado por el rendimiento en castellano.** Si ACE-Step canta flojo en castellano, G1 falla, y la respuesta honesta a ese escenario es **no-go o cambio de adapter (G1-bis), nunca re-pesar la muestra**.

**(c) RECOMENDACIÓN.** **(1)** Fijar el alcance de canto de Fase 1 en **{castellano, inglés}** y nada más, adoptando tal cual el reparto 6/4 de `T-08`. Cerrar I-12 con ese texto. **(2)** Ratificar `T-08` **sin tocar el reparto ni los umbrales**: el reparto es parte de la muestra y cambiarlo después de conocer resultados sería manipular el gate. **(3)** Añadir a la UI una tercera categoría explícita: «**otros idiomas: permitidos, sin garantía y sin medición**». **(4)** **Prohibir en nuestra documentación y UI la frase «50+ idiomas»**: es una afirmación de un tercero sin lista ni métrica, y repetirla nos hace responsables de ella. **(5)** Añadir a `T-03`/`T-07` una comprobación de 15 minutos que hoy no está: verificar **cómo se transmite el idioma sin LM planner** (¿basta la letra?, ¿hay que declararlo en el prompt de estilo?). Si sin planner el modelo canta castellano con fonética inglesa, eso cambia el diseño del prompt **antes** de generar las diez pistas, no después. **(6)** Ampliar a un tercer idioma (catalán) cuesta 1 brief + 1 verificación de ASR, pero ⚠️ el WER de HeartTranscriptor en catalán **está sin verificar**: no ampliar hasta que ese dato exista.

**(d) CONSECUENCIA DE NO DECIDIR.** Bloquea `T-08` → `T-09` de forma inmediata, no diferida: el umbral de WER de G1 no está bien definido si no se ha fijado antes **en qué idioma se mide** (`g1-protocolo.md`:388 fuerza el idioma del brief en la transcripción; sin decisión no hay parámetro que forzar). `T-08` está `en-revision` hoy y `T-09` es el gate. Si se generan las diez pistas antes de fijar el idioma y luego se cambia, hay que regenerarlas y volver a escuchar: **~9 h de escucha del propietario más la GPU**, y peor, se contamina el ciego de la sesión (los umbrales se fijan **antes** de escuchar, `gobernanza.md` §2.2).

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Fija alcance de producto y condiciona la muestra de un gate.

---

### A-09 · D-23 — Loudness por destino: los dos valores de la spec son estándar; la elección real está en otras tres cosas

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** precondición 6 de `g1-protocolo.md` §9.1 — **ninguna tarea de F2 la produce**

**(a) CRITERIO.** Un valor de destino no se elige por gusto: **se copia de la especificación pública del destino**. Solo hay decisión real donde **(a)** el proyecto tiene un destino que ninguna norma cubre, **(b)** dos normas aplicables discrepan, o **(c)** la spec propia es más laxa que la norma que dice seguir.

**(b) FUNDAMENTO.** ✅ **Broadcast −23 LUFS**: EBU R128 fija target −23,0 LUFS integrado, tolerancia ±0,5 LU (±1,0 LU solo cuando el material no permite más precisión) y máximo −1 dBTP (`tech.ebu.ch/docs/r/r128.pdf`). ✅ **Streaming −14 LUFS**: Spotify normaliza a −14 LUFS (ITU-R BS.1770) y recomienda masterizar a −14 con true peak por debajo de −1 dBTP; YouTube, Tidal y Amazon coinciden en −14; Apple Music (Sound Check) normaliza a −16, más silencioso, por lo que un master a −14 no se penaliza. ✅ **Podcast −16 LUFS**: la guía de Apple recomienda ~−16 LUFS estéreo (−19 mono) con true peak ≤ −1 dBFS. **Discrepancia interna del proyecto**: ✅ `spec.md`:284 (criterio C-01) fija «±1 LU del objetivo del destino», **más laxo que el ±0,5 LU de EBU R128 para broadcast**, siendo que la normalización es una ganancia determinista y alcanzar ±0,1 no cuesta nada. **Clasificación errónea en los briefs**: ✅ `g1-protocolo.md` §4 asigna «broadcast» a **B-03 (sintonía de podcast)** — un podcast no es broadcast: su norma es −16, no −23.

**(c) RECOMENDACIÓN.** Cerrar D-23 con esta tabla:

| Destino | Objetivo integrado (EBU R128 / BS.1770) | Tolerancia | True peak máximo | Origen |
|---|---|---|---|---|
| **broadcast** (radio/TV, Europa) | **−23,0 LUFS** | **±0,5 LU** | **−1,0 dBTP** | EBU R128 |
| **streaming musical** (Spotify, YouTube, Tidal, Amazon) | **−14,0 LUFS** | ±1,0 LU | **−1,0 dBTP** | Spotify / YouTube |
| **podcast / música bajo locución** *(destino nuevo — ver abajo)* | **−16,0 LUFS** estéreo (−19 mono) | ±1,0 LU | **−1,0 dBTP** | Apple Podcasts |
| **stems** | **sin normalizar** | — | se **aborta** la exportación si el material supera −0,1 dBTP, en vez de limitar | D-23 |
| **sesión de escucha ciega** (G1/G1-bis, interno, **no** es objetivo de producto) | **−16,0 LUFS**, o el que resulte de `T = min(−16, mínᵢ(Iᵢ − TPᵢ − 1))` si alguna pista requiriese ganancia positiva | exacto, solo ganancia | **−1,0 dBTP** | `g1-protocolo.md` §5.5 + A-12 |

**Dónde hay elección real** (esto es lo que el propietario decide, no acepta): **(1) ¿Se añade el tercer destino «podcast / música bajo locución» (−16)?** El proyecto ya lo necesita: B-03 (sintonía de podcast) y B-04 (fondo bajo locución) no son ni broadcast −23 ni streaming musical −14. Si se añade, hay que tocar la enumeración de destinos de `spec.md`:235 y el criterio C-01 (`:284`), y `T-20` (F4) debe parametrizar **tres** valores en vez de dos. Coste: prácticamente nulo ahora; **una migración de datos si se decide después de C-01**. **(2) ¿Se aprieta la tolerancia de broadcast a ±0,5 LU** (norma EBU) en vez del ±1 LU que hoy dice C-01? Es gratis en implementación y es lo que un difusor exigirá; cambia un criterio de aceptación de la spec. **(3) ¿Qué significa exactamente «stems sin normalizar»** cuando la salida cruda satura? Propuesta: no se toca la ganancia y se **aborta** con mensaje, nunca se limita en silencio. **Lo que no es elección**: −23 y −14 son las cifras de las normas públicas citadas; el propietario solo tiene que aceptarlas y fechar la aceptación.

**(d) CONSECUENCIA DE NO DECIDIR.** **Bloqueo duro e inmediato de `T-09`**: la decisión de loudness por destino es la **precondición 6** de `g1-protocolo.md` §9.1 y `gobernanza.md` §2.2.5 la exige «por escrito antes de G1». Hoy **no existe en ningún sitio** y **ninguna tarea de F2 la produce** (`T-20` está en F4 y solo implementa la parametrización, `tasks.md`:549): sin este acto, **la Fase 0 no puede cerrarse aunque todo lo demás salga bien**. Aguas abajo, decidir el tercer destino después de C-01 convierte un cambio de configuración en una migración del campo `destino` de todas las pistas ya generadas.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Precondición escrita de un gate y, en los puntos (1) y (2), cambio de un criterio de aceptación de la spec.
---

> **Nota de conjunto sobre A-10…A-19.** Son diez observaciones sobre `gates/g1-protocolo.md` (`T-08`, hoy `en-revision`). **Todas deben cerrarse ANTES de firmar §9 y antes de generar una sola pista**, porque `g1-protocolo.md` §8.1 invalida la sesión si los umbrales no estaban ratificados por escrito con fecha anterior a la primera escucha. **Ninguna de las diez mueve un umbral**: son contradicciones internas, imposibilidades aritméticas, defectos de instrumento y de muestra. El protocolo, en conjunto, está mejor construido que la mayoría de su especie; estas diez son lo que le falta para ser ejecutable tal cual.

### A-10 · T-08 / G1-01 — La regla anti-inflación modifica puntuaciones después de romper el ciego, lo que el propio protocolo declara causa de invalidez

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Un protocolo con dos reglas que se contradicen **no lo resuelve el documento: lo resuelve quien esté en la sala el día de la sesión** — que es exactamente el fallo que este gate existe para impedir. Toda contradicción interna se cierra **antes** de la firma, no durante la sesión.

**(b) FUNDAMENTO.** ✅ Cuatro reglas del mismo documento, incompatibles entre sí: §3 (regla anti-inflación) «Sin esa frase, la puntuación se rebaja en un punto **al consolidar la hoja**»; §7.3 «Consolidación — se rellena DESPUÉS de romper el ciego»; §5.6.4 «Ninguna puntuación se modifica después de abrir el mapa»; §8.1 «alguna puntuación se modificó después de romper el ciego» → **sesión NO VÁLIDA**. Aplicar la regla anti-inflación invalida la sesión.

**(c) RECOMENDACIÓN.** Antes de firmar §9, **mover la aplicación de la regla anti-inflación al paso 1 de §5.6** («se completan todas las hojas… incluidas las notas obligatorias»), es decir **antes del sellado por SHA-256 y con el ciego intacto**. Redacción sugerida para §3: «La rebaja por falta de justificación se aplica **al cerrar la hoja de cada brief**, con el ciego intacto y antes del sellado por hash; después del sellado ninguna puntuación se toca». **No cambia ningún umbral.**

**(d) CONSECUENCIA DE NO DECIDIR.** La sesión se ejecuta y al consolidar aparece la disyuntiva: o se ignora la regla anti-inflación (y D5 queda inflada justo en la dimensión que decide el gate) o se aplica (y la sesión es inválida por §8.1). Cualquiera de las dos salidas cuesta **repetir la sesión**: ~9 h de escucha más la regeneración de la serie propia, con **589 h / 35.340 €** bloqueadas mientras tanto.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Modifica el procedimiento de un gate, aunque no su umbral.

---

### A-11 · T-08 / G1-02 — El límite de 2 h de sesión es aritméticamente imposible con 30 pistas

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Un límite de fatiga que el propio material no puede cumplir no protege del cansancio: **garantiza que se incumpla algo el día de la sesión**. Antes de firmar hay que comprobar que el plan de sesión cabe en sus propias reglas.

**(b) FUNDAMENTO.** ✅ Duraciones declaradas en §4: 45+180+30+120+150+30+150+40+165+90 = **1.000 s por serie**. Con 3 series = 3.000 s = **50 min de audio por pasada**, y §5.3 exige **dos** pasadas por brief (una sin puntuar, una puntuando) = **100 min solo de reproducción**. Más puntuación (30 pistas × 5 dimensiones + nota obligatoria de D5, ~1 min/pista = 30 min) y descansos obligatorios (≥ 15 min entre bloques de 5 briefs; en la práctica 2) → **~2 h 40 min**. §5.3 fija «≤ 2 h de sesión total». En **variante B** (20 pistas) el cálculo da **~1 h 42 min y sí cabe**.

**(c) RECOMENDACIÓN.** Decidir explícitamente en §9, antes de firmar, una de estas dos: **(a)** declarar la sesión en **dos días desde el principio**, con la composición de bloques (qué briefs en qué bloque) fijada por escrito **antes** de escuchar, para que no la decida el cansancio; o **(b)** ejecutar la **variante B** (§5.6), que cabe en las 2 h sin tocar nada — ver **A-19**, que la recomienda por otros motivos convergentes. Sea cual sea, dejar escrito el reparto en la cabecera de la hoja (§7.1) antes de la primera escucha.

**(d) CONSECUENCIA DE NO DECIDIR.** Se llega a la pista 24 de 30 con la regla de fatiga ya incumplida y la decisión de continuar o parar la toma el evaluador **cansado, sobre la marcha**. Las últimas 6 pistas puntuadas en fatiga son el **20 % de la muestra** que decide 589 h; si por sorteo caen ahí varias pistas propias, el resultado del gate depende del orden aleatorio y no de la calidad.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Composición y ejecución de la sesión del gate.

---

### A-12 · T-08 / G1-03 — `ffmpeg loudnorm` en dos pasadas NO garantiza «solo ganancia»

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de firmar §9 y antes de preparar el material

**(a) CRITERIO.** Si el procedimiento de preparación del material **puede aplicar procesado dinámico no declarado a una serie y no a otra**, la comparación mide el procesado y no el modelo. Toda herramienta del procedimiento se verifica contra su documentación antes de firmarlo.

**(b) FUNDAMENTO.** `g1-protocolo.md` §5.5 promete: «La normalización es solo ganancia (más el ajuste de true peak). Nada de limitar ni comprimir: eso alteraría D2», usando `ffmpeg loudnorm` en dos pasadas. ✅ La documentación oficial del filtro dice lo contrario: con `linear=true`, si el cambio de loudness integrado produjera un true peak por encima del objetivo (o si la LRA de origen supera la de destino), «**normalization mode will revert to dynamic**» (`ffmpeg.org/ffmpeg-filters.html#loudnorm`; `slhck.info/ffmpeg-normalize/usage/normalization-options/`). Aritmética del disparo: ganancia = T − I; se revierte si `TPᵢ + (T − Iᵢ) > TP_objetivo`. Caso típico aquí: pista de librería masterizada a ~−9 LUFS → ganancia negativa, se queda lineal; **pista propia del modelo a ~−18 LUFS con TP −0,5 → ganancia +2 dB → TP resultante +1,5 dBTP > −1 → modo dinámico solo en la serie propia**. ⚠️ **Incertidumbre declarada:** no se pudo ejecutar (no hay `ffmpeg` en el PATH de esta máquina), así que el disparo concreto depende de los valores reales de las 30 pistas; **lo verificable hoy es la regla documentada, no las pistas**.

**(c) RECOMENDACIÓN.** Sustituir el procedimiento de §5.5 por uno determinista: **(1)** medir I y TP de las 30 pistas (`ffmpeg -af ebur128=peak=true` o `loudnorm` en pasada de análisis); **(2)** calcular el nivel único de sesión con la fórmula cerrada **`T = min(−16, mínᵢ(Iᵢ − TPᵢ − 1))`**, que se deriva de exigir `TPᵢ + (T − Iᵢ) ≤ −1 dBTP` para todas; **(3)** aplicar **solo ganancia** con el filtro `volume=<delta>dB`, idéntica lógica para las 30; **(4)** volver a medir y **abortar** si alguna supera −1 dBTP, en vez de limitarla. Si se prefiere seguir con `loudnorm`, añadir como criterio de validez de §8.1 que las 30 pistas reporten `Normalization Type: Linear` en `print_format=summary`, y **anular la sesión si alguna dice Dynamic**. Registrar en `04-sesion/loudness.csv`: I medido, TP medido, ganancia aplicada, TP final y tipo de normalización.

**(d) CONSECUENCIA DE NO DECIDIR.** La serie propia llega a la sesión con **compresión dinámica no declarada** y la de librería sin ella. D2 («calidad de mezcla y ausencia de artefactos») deja de comparar modelos y compara **procesados**, y D2 entra en el criterio 2 (ninguna media < 3,0). El resultado del gate sería irreproducible y, si se descubre después, obliga a repetir la sesión entera.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Cambia el procedimiento de preparación del material de un gate.

---

### A-13 · T-08 / G1-04 — La línea base de librería puede predeterminar el veredicto en las dos direcciones

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** **ahora**, antes de firmar §9 y antes de generar nada

**(a) CRITERIO.** El criterio de no-go es el único que **no admite compensación**; por tanto la línea base contra la que se aplica tiene que ser **(a)** existente para los diez briefs y **(b)** comparable en la dimensión que se puntúa. Si la regla de «no hay línea base» o la naturaleza típica de la línea base determinan el resultado con independencia de la calidad, **el gate no mide nada**.

**(b) FUNDAMENTO.** Dos ramas, ambas verificables en el texto. **Rama A (auto-NO-GO)**: ✅ §2.1 fija «Un brief sin línea base de librería utilizable cuenta como **derrota** en el criterio 5», y el criterio 5 dispara NO-GO con más de 5 derrotas de 10; **6 de los 10 briefs de §4 piden canto en castellano** (B-01, B-02, B-03, B-05, B-06, B-08), y la música de stock *royalty-free* con voz cantada en castellano, al género y tempo pedidos, es escasa. Si 6 briefs quedan sin línea base utilizable, **el gate da NO-GO por construcción** — el mismo patrón que CS-51, donde el suelo de 8 GB era inalcanzable por construcción. **Rama B (no-go inerte)**: si se admiten como «utilizables» pistas de librería instrumentales, D5 de la librería («¿la usarías tal cual?») para un brief que exige voz cantada será ~2 casi siempre, y la pista propia solo tendrá que batir un 2: **el único criterio sin compensación se vuelve trivial de pasar**. ✅ §4.1 ya reconoce el problema a medias («Si la pista de librería es instrumental o tiene otra letra… D4 no se puntúa en la pista de librería») pero **no dice nada de D5**, que es la que decide.

**(c) RECOMENDACIÓN.** Ejecutar **ahora**, antes de firmar §9 y antes de generar nada (§5.1 ya obliga a elegir las líneas base primero): **buscar las diez líneas base y contar cuántos briefs tienen candidato con voz cantada en el idioma pedido** — ese número es `N_comparables`. Con él sobre la mesa, el propietario decide por escrito una de estas cuatro, **no en caliente**:

- **⭐ (0) — PREFERENTE. No toca el denominador ni el umbral.** Mantener el criterio 5 **literalmente como está** — `gates/g1-protocolo.md`:97: «por debajo de la de librería en la dimensión 5 en **más de 5 de los 10** briefs → NO-GO» — y resolver la escasez **por el lado de la muestra, no del cálculo**: **(i)** buscar línea base **instrumental declarada como tal** para los briefs sin candidato vocal en el idioma pedido, anotando la asimetría en el acta y puntuando D5 de la librería con la pregunta real del protocolo («¿la usarías tal cual para este brief?»), de modo que la instrumental no entre disfrazada de comparable vocal; y **(ii)** si aun así falta línea base, **aceptar la derrota tal y como ya está escrita** en `gates/g1-protocolo.md`:109 («Ese brief **cuenta como derrota** en el criterio 5 […] la carga de la prueba la tiene el modelo propio, no la librería»). Ventaja decisiva: es la **única** opción que no altera ningún umbral ni su aritmética, y por tanto la única que no tiene que justificarse ante la regla de inmutabilidad del §2 del protocolo. Coste: horas de búsqueda de catálogo, cero riesgo de gobernanza.
- **(1)** Definir «línea base utilizable» como «con voz principal cantada en el idioma del brief» y aceptar que los briefs sin ella cuentan como derrota (mantiene §2.1 intacto, con el riesgo de auto-NO-GO explícito y asumido por escrito antes de escuchar).
- **⚠️ (2) — CAMBIA CÓMO SE CALCULA EL CRITERIO 5. Es la única propuesta de todo este registro que toca la aritmética de un umbral.** Mantener §2.1 para el criterio 3 (CLAP, donde la carga de la prueba en el modelo propio sí tiene sentido) y, **para el criterio 5**, sustituir «derrota» por «**brief no comparable**», recalculando el no-go como «> 5 de los briefs **comparables**», con `N_comparables` **fijado y escrito antes de escuchar**. **Aritmética que hay que ver antes de firmarla:** con N comparables hacen falta **≥ 6 derrotas** para disparar el NO-GO, luego **si `N_comparables` ≤ 5 el NO-GO es matemáticamente imposible**; y el escenario que esta misma ficha declara probable en la rama A (6 de los 10 briefs sin línea base utilizable → `N_comparables` = 4) dejaría **inerte el único criterio que no admite compensación**. Por eso esta opción **solo se ofrece con cláusula de suelo obligatoria e inseparable**: **si `N_comparables` < 8, el criterio 5 no se puede evaluar y la sesión NO cierra el gate** — se suspende, se amplía la búsqueda de líneas base y se repite según §8.4, sin puntuar nada como aprobado entretanto. **Sin esa cláusula escrita en §6 y §9 del protocolo, la opción (2) no debe ofrecerse ni firmarse.**
- **(3)** Rebalancear los briefs hacia idiomas con stock vocal disponible — pero eso reduce la representatividad del uso real y choca con la i18n castellano del proyecto.

**Recomendación del analista: la (0)**, precisamente porque es la única que deja el umbral **y su denominador** donde están. El argumento que antes sostenía a la (2) —«si para un brief no hay nada descargable, la plataforma **sí** aporta, y contarlo como derrota dice lo contrario de lo que ocurre»— sigue siendo cierto, pero **se resuelve buscando línea base instrumental declarada, no cambiando el denominador**: el protocolo ya eligió su respuesta a ese dilema en `gates/g1-protocolo.md`:109 y esa elección es un umbral, no una errata. Si el propietario prefiere aun así la (2), su firma **debe** incluir explícitamente la cláusula de suelo `N_comparables ≥ 8`. **No se ratifica ninguna**: la elección es del propietario y la (2) afecta a **cómo se calcula un umbral** — está declarada como excepción en el encabezado de este documento y en §5.1.

**(d) CONSECUENCIA DE NO DECIDIR.** El resultado del gate queda decidido por **la disponibilidad de stock musical en castellano** y no por la calidad del modelo, en un sentido o en el otro. Coste del error: **589 h / 35.340 €** aprobadas sobre un gate inerte, o el proyecto abandonado por un NO-GO que no midió lo que decía medir. **Es la única de estas diez observaciones que puede, por sí sola, invertir el veredicto.**

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Afecta al cálculo de un umbral de gate.

---

### A-14 · T-08 / G1-05 — El criterio 3 (CLAP) es el menos discriminante y casi con seguridad pasará

**Estado:** 🔒 pendiente de firma · **Confianza:** media · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Un umbral que se va a cumplir **con independencia de la calidad** no es evidencia; es ruido que se lee como confirmación. Si se conserva —y debe conservarse, porque no se degradan umbrales—, hay que **declarar por escrito antes de la sesión que pasarlo no constituye validación**.

**(b) FUNDAMENTO.** ✅ §6.1 compara CLAP(propia) vs. CLAP(librería) usando como texto **el prompt de estilo literal del brief** (§4.2). Asimetría estructural: la pista propia fue **generada condicionada a ese mismo texto** (ACE-Step 1.5 usa el text encoder Qwen3-Embedding-0.6B, verificado en `D:\srv\ace-step\provenance\MANIFEST.json` y en `pre-dev-checklist.md` ítem 7), mientras que la de librería solo tuvo que sobrevivir a una búsqueda por palabras clave en un catálogo. No es optimización directa de la métrica CLAP (el modelo no condiciona con CLAP), **pero sí es la misma tarea —seguir una descripción textual— para una serie y no para la otra**. El propio protocolo ya obliga a publicar los valores brutos «no solo la cuenta», que es la mitigación correcta.

**(c) RECOMENDACIÓN.** **No tocar el umbral** (≥ 7 de 10, intacto). Añadir una línea en §6.1, antes de la firma: «Se declara de antemano que el criterio 3 favorece estructuralmente a la serie propia por ser generada a partir del mismo texto que se usa como referencia; su cumplimiento **no** se lee como evidencia de calidad musical, solo como comprobación de sanidad (que la pista responde al prompt). El criterio con poder discriminante real es el 5, y el subjetivo de suelo es el 2». Publicar además el **tamaño del efecto** (diferencia media y mediana propia − librería), que el protocolo ya pide.

**(d) CONSECUENCIA DE NO DECIDIR.** Un 10/10 en CLAP entra en el acta como si fuera **prueba objetiva de calidad** y compensa psicológicamente un D5 flojo. En modo solo, sin contraste entre evaluadores, ese sesgo **no lo corrige nadie** — es justo el hueco que `gobernanza.md` §2.1 reconoce haber abierto.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Añade una declaración interpretativa al acta de un gate.

---

### A-15 · T-08 / G1-06 — El WER del 15 % no es interpretable sin medir antes el suelo del transcriptor

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Un umbral objetivo solo es objetivo si se conoce **el error del instrumento que lo mide**. Medir el suelo del instrumento **no es degradar el umbral**: es saber si el umbral es alcanzable por algo.

**(b) FUNDAMENTO.** ✅ §6.2 fija WER ≤ 15 % de media y ≤ 25 % peor caso, medido con HeartTranscriptor-oss (base Whisper) sobre **voz cantada**, y el propio documento avisa: «un WER medido con un transcriptor sobre voz cantada no es un WER de voz hablada; el transcriptor también se equivoca». Pero luego **solo mide las diez pistas propias** (Suno «como contexto», librería fuera): **no hay ninguna medida de referencia** que permita saber si el 15 % es exigente o inalcanzable con ese transcriptor. ⚠️ Incógnita declarada y no resuelta: el identificador y el SHA-256 del modelo se fijan en `T-09`, no hoy, así que **hoy no se puede dar una cifra de suelo** — solo se puede planificar medirla.

**(c) RECOMENDACIÓN.** Añadir a §6.2, antes de firmar, una **medición de calibración que no toca el umbral**: transcribir con la misma configuración (mismo modelo, mismo idioma forzado, misma normalización de texto) entre 3 y 5 grabaciones comerciales publicadas cuya letra sea conocida y perfectamente inteligible al oído, en los dos idiomas de los briefs, y publicar su WER como «**suelo del instrumento**» en `07-metricas/`. Coste: **< 1 h**, con el mismo script. Los umbrales 15 %/25 % se aplican tal cual pase lo que pase (regla de inmutabilidad, §2); la calibración solo sirve para que, si falla el criterio 4, el `replanteo` de §8.5 apunte a la hipótesis correcta (**modelo vs. instrumento**) en vez de gastar una de las dos repeticiones permitidas a ciegas.

**(d) CONSECUENCIA DE NO DECIDIR.** Si el suelo del transcriptor sobre canto fuera, por ejemplo, del 20 %, el criterio 4 sería **imposible de cumplir** y el gate entraría en `replanteo` por una propiedad del medidor. §8.5 solo permite **dos** repeticiones antes de NO-GO obligatorio: quemar una persiguiendo una hipótesis equivocada equivale a **la mitad del margen de recuperación del gate**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Añade un paso al procedimiento de medición de un gate.

---

### A-16 · T-08 / G1-07 — La rúbrica discrimina bien en D2/D3/D5, pero D1 mezcla hechos medibles con juicio perceptual

**Estado:** 🔒 pendiente de firma · **Confianza:** media · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Una dimensión de escucha debe puntuar **lo que el oído decide**. Todo eje que sea un **hecho verificable por script** (duración, tempo, presencia de un instrumento nombrado) sale del juicio y entra en la medición; si se deja dentro, la dimensión mide la habilidad del evaluador estimando BPM, no la calidad del modelo.

**(b) FUNDAMENTO.** ✅ §3.1: los descriptores de D1 incluyen «el tempo se desvía > 15 %», «duración desviada más de un 5 % del objetivo» y «un instrumento nombrado en el brief ausente» — **dos de los tres son medibles con `ffprobe` y un detector de pulso**. Además hay asimetría: la duración es un **parámetro de generación** en ACE-Step, así que la serie propia acierta la duración **por construcción**, mientras que una pista de librería tiene la duración que tiene: **D1 penaliza a la librería por algo que no es calidad**. En el resto la rúbrica es sólida: los descriptores de D2, D3 y D5 son operativos y contrastables (§3.2-§3.5), la correspondencia ≥ 4 = sí / ≤ 3 = no de D5 es inequívoca, la regla de puntuar a la baja y la nota obligatoria en todas las filas de D5 son buenas defensas anti-inflación, y el orden D1→D5 sin volver atrás está bien pensado.

**(c) RECOMENDACIÓN.** Antes de firmar: **(1)** medir duración (`ffprobe`) y tempo de las 30 pistas **antes** de la sesión y guardarlo en `04-sesion/` **sin abrir**; **(2)** reformular D1 para que el evaluador puntúe **solo lo perceptual** (género, carácter, instrumentación, idioma, encaje con el uso final) y aplicar los ejes medidos como **tope automático** al consolidar: si la duración se desvía > 5 % del objetivo, **D1 no puede superar 3**; **(3)** en §3.6, sustituir «No se comparan las tres pistas del brief entre sí mientras se puntúan» —regla incumplible, porque se presentan consecutivas— por «**Puntúa cada pista contra la rúbrica, no contra las otras; si adviertes que estás comparando, anótalo en la casilla de notas**». Una regla que no se puede cumplir erosiona la credibilidad de las que sí.

**(d) CONSECUENCIA DE NO DECIDIR.** D1 entra en el criterio 2 (ninguna dimensión con media < 3,0) **mezclando ruido de estimación perceptual con hechos ya verificables**, y hace que la comparación propia-vs-librería en D1 esté sesgada a favor de la propia. No invierte el veredicto por sí solo, pero **contamina uno de los cuatro criterios de aprobado**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Reformula una dimensión de la rúbrica del gate.

---

### A-17 · T-08 / G1-08 — Los diez briefs: la variedad es real y verificada, pero falta una canción completa

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de generar

**(a) CRITERIO.** Un conjunto de briefs es adecuado si **(a)** cubre los ejes que el producto promete y **(b)** no concentra su dificultad en capacidades que el producto **no ofrece en la fase evaluada**. Si mide sobre todo lo segundo, un fallo se leerá como «el modelo no vale» cuando lo correcto sería «falta esta función».

**(b) FUNDAMENTO.** ✅ **Variedad comprobada contando sobre §4** (la nota de reparto del documento es correcta): 6 castellano / 4 inglés; 4 broadcast / 6 streaming; 5 voces masculinas / 5 femeninas; tempos de 68 a 140 BPM; 10 géneros sin repetir; duraciones 30 s, 30 s, 40 s, 45 s, 1:30, 2:00, 2:30, 2:30, 2:45, 3:00. Cada brief declara los seis ejes verificables. **Es un conjunto bien construido.** **Defectos:** **(1)** el brief más largo es 3:00 y cuatro son ≤ 45 s, pero el producto se define en `spec.md` §1.2 como «una canción completa descargable»: **ningún brief mide el caso de uso central**. **(2)** Cuatro briefs dependen de **control de estructura a nivel de sección que la Fase 1 no ofrece** — B-03 «debe seguir funcionando cortada a 10 s», B-05 «crescendo en el último tercio y final que se apaga», B-06 «espacio en el último tramo para un cierre hablado», B-10 «voz procesada solo en el estribillo; los versos, instrumentales» —, y el `section_map` está en el esquema (D-22) pero su explotación no es de Fase 1. **(3)** B-06 pide «30 s exactos» mientras D1 tolera ±5 % (±1,5 s): contradicción menor pero puntuable. **(4)** Ningún brief es instrumental, **y está bien**: §3.4 lo justifica por escrito para que D4 y el WER se midan sobre las diez.

**(c) RECOMENDACIÓN.** Antes de ratificar §4: **(a)** sustituir uno de los cuatro briefs de ≤ 45 s por una **canción completa de 3:00–3:30 con estructura de canción**, **o** declarar por escrito en §9 que G1 evalúa deliberadamente formato corto y que **la capacidad de canción completa queda sin evaluar en este gate** (opción legítima, pero debe estar escrita: hoy no lo está); **(b)** añadir a la tabla de §4 una columna «**eje que depende de control fino de estructura, no disponible en Fase 1**», marcando B-03, B-05, B-06 y B-10, para que un fallo ahí apunte al `replanteo` correcto (**función de producto**) y no a «el modelo no vale»; **(c)** fijar en B-06 «30 s ±1 s» o declarar que se le aplica la tolerancia general de ±5 %. **Ninguna de las tres toca un umbral.** El propietario puede sustituir briefs libremente según §4 y §9, pero **solo antes de generar**.

**(d) CONSECUENCIA DE NO DECIDIR.** Escenario concreto y probable: el modelo saca 3/5 en D1 en cuatro briefs por no colocar el crescendo o la voz solo en el estribillo; D1 baja de 3,0 de media, falla el criterio 2, veredicto `replanteo`, y **se gasta una de las dos repeticiones permitidas cambiando parámetros de inferencia que no van a arreglar algo que es una función de producto ausente**. Coste: una pasada completa del gate (generación + sesión) por un diagnóstico mal orientado.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** La composición de la muestra es suya y solo puede tocarse antes de generar.

---

### A-18 · T-08 / G1-09 — El manifiesto retroactivo de las pistas de G1 incumple el invariante de `CLAUDE.md`

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de generar la primera pista

**(a) CRITERIO.** Los invariantes de `CLAUDE.md` son innegociables por definición; si un protocolo los incumple, **o se corrige el protocolo o se cambia el invariante por decisión escrita** — nunca se deja la contradicción en pie. Y los campos de un manifiesto son declaraciones **del momento de la generación**: lo que no se capture al generar no se puede añadir después sin mentir sobre la fecha.

**(b) FUNDAMENTO.** ✅ `CLAUDE.md`, invariantes: «Manifiesto de procedencia en cada generación desde la primera pista, con `manifest_schema_version` y ledger append-only». ✅ `g1-protocolo.md` §10.1 define el manifiesto retroactivo con: modelo@versión, SHA-256 de los pesos, semilla, prompt literal, letra, fecha y hora, hardware, parámetros de inferencia. **Faltan**: `manifest_schema_version` (exigido **literalmente** por el invariante), `lyrics_declaration` (bloqueo duro de D-21), `training_data_declaration` y el **SHA-256 del artefacto realmente cargado** (`3faa5ac9…5812d947`, `pre-dev-checklist.md` ítem 7-bis) además de los hashes de los componentes upstream y la revisión fijada `19671f40…`. Coste de añadirlos al generar: **minutos**. Coste de añadirlos después: **imposible sin falsear la fecha** — D-20 establece que una cadena WORM no admite backfill.

**(c) RECOMENDACIÓN.** Antes de firmar, ampliar la lista de campos de §10.1 con: `manifest_schema_version` (valor «0-pre-v1» o el que se prefiera, **pero presente**), `lyrics_declaration` (valor real: letra propia del propietario), `training_data_declaration` con el valor **`declarada-por-el-proveedor-sin-auditar`** (⚠️ **no** «no divulgada»: ver **X-5** y B-01), `sha256` del artefacto fusionado y la revisión upstream fijada. Y añadir a `T-26` (F5) un criterio de aceptación: «el esquema v1 se valida contra los manifiestos retroactivos de G1; si algún campo obligatorio de v1 no existe en ellos, se documenta como limitación conocida antes de firmar el esquema».

**(d) CONSECUENCIA DE NO DECIDIR.** Las **diez primeras pistas del proyecto** —las que deciden el gate y las que se reutilizan en G1-bis y en las escuchas de regresión durante 12 meses (§10.3)— nacen **fuera del invariante que el proyecto declara innegociable**, y no hay forma de arreglarlo después. Además obliga a `T-26` a firmar un esquema v1 sabiendo que su primer corpus no lo cumple.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Toca un invariante declarado innegociable y el contenido del manifiesto.

---

### A-19 · T-08 / G1-10 — Recomendación neta sobre Suno: ejecutar la variante B

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de firmar §9

**(a) CRITERIO.** Entre dos opciones que producen **el mismo veredicto bajo los mismos umbrales**, se elige la que elimina deuda abierta y riesgos no cuantificados. Si una opción solo aporta contexto informativo y arrastra una incógnita legal sin verificar, **su valor esperado es negativo**.

**(b) FUNDAMENTO.** ✅ §5.6 lo demuestra explícitamente: «**Ninguno de los cinco umbrales depende de Suno**» — los criterios 1 y 2 son absolutos, el 3 y el 5 se miden contra librería y el 4 solo sobre las propias. Beneficios verificables de prescindir: **(a)** cierra la única dependencia viva de CS-03 en el gate (`pre-dev-checklist.md` ítem 11, hoy diferido a GC-01 §8c **sin verificar**); **(b)** el material baja de 30 a 20 pistas y la sesión pasa de ~2 h 40 min a **~1 h 42 min**, cabiendo por primera vez en el límite de fatiga de §5.3 (aritmética en **A-11**); **(c)** elimina la prohibición permanente y difícil de vigilar de §10.4b (no citar «puntuamos por encima de Suno» fuera del repositorio) y la limpieza de §10.4e. **Pérdida:** solo el contexto de «a qué distancia está el modelo del estado del arte comercial», que **no decide nada**. ⚠️ **Incertidumbre declarada:** no se han verificado los ToS de Suno y no se cita cláusula (ver B-21); **esa imposibilidad es, en sí misma, parte del argumento**.

**(c) RECOMENDACIÓN.** Marcar en el bloque de firma de §9, casilla «Líneas base que se usarán», la opción **variante B (propia + librería)**, y anotar en `g1-resultado.md` que la ausencia de Suno es **una decisión registrada y no un defecto de la sesión** (el propio §5.6 lo dice). Si aun así se quiere el contexto de Suno, generarlo **después** de cerrar el gate y archivarlo fuera de la hoja de puntuaciones, para que no toque el veredicto.

**(d) CONSECUENCIA DE NO DECIDIR.** Se ejecuta con 30 pistas: se **incumple el límite de fatiga**, se arrastra CS-03 sin verificar dentro de un gate que decide 589 h, y toda cifra comparada contra Suno queda bajo la prohibición de §10.4b de forma **indefinida hasta GC-01** — incluida la propia lectura del acta si algún día se enseña a alguien.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Elige la composición de las líneas base del gate.

---

### A-20 · CS-22 (hallazgo) — Las fichas de licencia de CLAP y HeartTranscriptor son precondición de `T-09` (F2) y están asignadas a `T-33` (F5)

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Ventana:** antes de convocar `T-09`

**(a) CRITERIO.** Si un entregable es **precondición escrita** de una tarea de F2 y su única tarea productora está en F5, hay una **dependencia invertida**. Se detecta comparando la lista de precondiciones del gate con el plazo asignado en el checklist.

**(b) FUNDAMENTO.** ✅ `g1-protocolo.md` §9.1, **precondición 9**: «Ficha de licencia de las herramientas de medición (CLAP, HeartTranscriptor — I-13b, regla 5)», con estado `pendiente` y dueño el propietario, **antes** de convocar la sesión de `T-09` (F2). ✅ `pre-dev-checklist.md` ítem 19 (CS-22) asigna esa verificación así: «para Fase 1, la verificación de ffmpeg/HeartCodec/HeartTranscriptor vive en `T-33`», y **`T-33` está en F5, después de G1**. Además §6.1 condiciona el uso de la alternativa LAION a «ficha de licencia verificada de la herramienta elegida antes de usarla». Datos favorables **ya verificados**: HeartTranscriptor-oss es Apache 2.0 y `safetensors` (`spec.md` §11.1, verificado contra fuente primaria el 2026-08-18); HeartCLAP se declara Apache 2.0 en la misma sección. **Lo que falta es la ficha archivada, no la licencia.**

**(c) RECOMENDACIÓN.** Añadir la ficha de licencia de las dos herramientas de medición como **entregable explícito dentro de F2** —lo natural es colgarlo de `T-08` o de `T-09`, **no crear tarea nueva**— y anotar en CS-22 que ese subconjunto **se adelanta a F2** mientras el resto del pipeline sigue en `T-33`. Trabajo real: **1–2 h**, porque las licencias ya están identificadas; lo que falta es archivarlas con URL, fecha y SHA-256 de los pesos que se descarguen.

**(d) CONSECUENCIA DE NO DECIDIR.** `T-09` no puede convocarse sin incumplir su propia precondición 9; o se convoca incumpliéndola, y entonces la sesión arrastra un **invariante del proyecto sin cumplir** («licencias comerciales verificadas ANTES de integrarla», `CLAUDE.md`) precisamente en las herramientas que producen **dos de los cinco umbrales**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Es una reubicación de un entregable ya presupuestado, sin cambio de alcance ni de gasto.

---

### A-21 · CS-04 — Anexo A: revertir el diferimiento y firmarlo ahora

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** antes de que F2 genere la primera pista

**(a) CRITERIO.** Una mitigación cuya función es que **la aprobación se tome sabiendo qué se compra** debe firmarse **antes** de aprobar, no en un gate posterior. Diferir una firma que cuesta cero al gate que llega **después** del gasto no la difiere: **la vacía**.

**(b) FUNDAMENTO.** ✅ `g2-matriz-resultados.md` §8: «El riesgo R-01 de la evaluación exige que los cinco puntos de `evaluation.md` §10.7 queden aceptados por escrito **ANTES DE APROBAR** la iniciativa»; §8.3: «Con la firma de este anexo, dirección declara haber leído y aceptado los cinco puntos… **antes** de aprobar la ejecución». **Estado real hoy**: los cuatro campos del bloque de firma siguen en «pendiente», mientras que los **39.360 €** de Fase 0+1 están ratificados desde el 2026-08-18 y F2 está `en-progreso` (`tasks.md`:29). Es decir: **la aprobación y el gasto ya ocurrieron; la aceptación consciente que debía precederlos está aparcada en GC-01 §8f**. En modo solo la firma es **autoaceptación del propietario: coste 0 €, 10 minutos de lectura**.

**(c) RECOMENDACIÓN.** Sacar CS-04 de GC-01 y **firmarlo ahora**, antes de que F2 genere la primera pista: leer los cinco puntos de §8.1 —el más importante: el manifiesto declarará que el corpus de entrenamiento es **declarado por el proveedor y sin auditar** (⚠️ redacción a corregir, ver **X-5**), y alojar el modelo en casa **no** limpia la procedencia— y rellenar los cuatro campos de §8.3 con nombre, fecha y constancia. En GC-01 §8f se conserva lo que ahí sí corresponde: la **re-firma en contexto comercial**, que es un acto distinto porque el riesgo cambia de destinatario. **Es la única de las cinco diferidas en la que se recomienda revertir el diferimiento.**

**(d) CONSECUENCIA DE NO DECIDIR.** El proyecto gasta su presupuesto más caro (**589 h / 35.340 €** desbloqueadas por G1) con **la única mitigación documentada de R-01 sin firmar**. Y en modo solo el coste de firmar es literalmente cero, así que el diferimiento no compra tiempo ni dinero: **solo aplaza mirar el punto incómodo**. Si algún día el proyecto se comercializa, el orden de las firmas (primero gastar, después aceptar) será visible en el historial de git.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Es literalmente una firma suya: aceptación de riesgo.

---

### A-22 · CS-53 — El repositorio es público y se llama `suno-sondo-clone`

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Ventana:** **horas, no semanas** — el coste crece cada día

**(a) CRITERIO.** La visibilidad se decide **por el lector adversario, no por el previsto**: ¿qué gana quien lo lea con la peor intención, y algo de eso es irreversible? A ello se suma una asimetría que zanja el caso: **privado → público es reversible en cualquier momento; público → privado no lo es**, porque los clones, forks, mirrors y archivadores que ya existan quedan fuera de control para siempre. Ante una asimetría así, **el defecto es la opción reversible**.

**(b) FUNDAMENTO.** ✅ Verificado vía `gh api` el 2026-09-01. **(1) Exposición real hoy = CERO**, y esto es lo que hace la decisión barata: forks 0, stars 0, watchers 0, y el tráfico de clones de los últimos 14 días devuelve `count 0 / uniques 0` **todos los días**. El repo se creó el `2026-09-01T12:21:21Z` y el último push fue `2026-09-01T18:05:35Z`: lleva público **unas 8 horas** y nadie lo ha tocado. **Es el momento más barato posible para revertirlo.** **(2) El nombre y la descripción son el hallazgo principal**: el repositorio se llama **`suno-sondo-clone`** y su descripción pública es «**Clone de suno y sondo**». Contrástese con `CLAUDE.md`, que ordena lo contrario: «La UX de Suno es referencia **funcional**; la identidad visual es propia — **prohibido clonarla**». Un repositorio público titulado «clone de suno» es **una declaración de intención de clonar, escrita por el propio autor, indexable y citable**, sobre un producto de terceros con marca — en un proyecto cuyo gate G2 entero versa sobre defendibilidad jurídica y cuya condición GC-01 §8c exige verificar los ToS de Suno. **(3) Sin licencia**: `licenseInfo = null`. Público y sin licencia = todos los derechos reservados: nadie puede reutilizarlo legalmente, pero cualquiera puede leerlo entero. Es la peor combinación de las dos posturas. **(4) Lo que se está publicando**: `git ls-files` da 38 ficheros, entre ellos **`.claude/rates.json`** (tarifa 50 €/h, margen 20 %, supervisión 25 %) y `evaluation.md` (157.899 B) con el presupuesto ratificado de 39.360 €, el TCO de 71.000–75.000 € y la comparativa construir-vs-comprar. Si GC-01 llega a activarse, **la contraparte negocia conociendo la base de coste y el margen**. **(5) Lo que NO es un problema**, y se dice para que la recomendación no suene alarmista: **no hay filtración de secretos**. `.gitignore` excluye `.claude/settings.local.json`, `*.safetensors`, `*.pt`, `*.bin`, `weights/` y las salidas de spikes; los 38 ficheros son documentación y código. **No hay nada que remediar, solo exposición que detener.** **(6) Beneficio actual de ser público**: ninguno operativo — sin colaboradores, sin usuarios, sin CI que dependa de la visibilidad, y los repos privados admiten colaboradores ilimitados sin coste.

**(c) RECOMENDACIÓN.** Tres acciones, hoy y **en este orden**, antes del merge de A-23: **(1) privatizar** — `gh repo edit daycry/suno-sondo-clone --visibility private`; coste operativo cero, reversible el día que se quiera. **(2) Renombrar** el repositorio y reescribir la descripción para que no nombren un producto de terceros — el propio slug de la iniciativa sirve: `plataforma-musical-ia`. Esto es **independiente de la visibilidad y hay que hacerlo aunque se decidiera seguir público**; es el punto con peor relación daño/coste de todo el proyecto. **(3) Diferir la publicación** a una decisión explícita en GC-01 y, si algún día se publica, publicar un subconjunto **curado** (documentación técnica + código) **sin** `.claude/rates.json` ni las cifras de presupuesto, y **con** un `LICENSE` explícito. **Ventaja táctica de privatizar hoy**: mientras el repo no haya sido copiado por nadie —y los datos de tráfico dicen que no lo ha sido— **no hace falta reescribir historia** para sacar `rates.json`; basta con dejar de publicarlo. Si se espera, esa opción barata desaparece.

**(d) CONSECUENCIA DE NO DECIDIR.** Es el único ítem de este registro cuyo coste **crece por día transcurrido**, y de forma no lineal: hoy la exposición medida es cero, pero basta una indexación, un scraper de código o un fork para que «público → privado» deje de ser una reversión y pase a ser **un intento de reversión**. Lo que quedaría expuesto de forma permanente: la base de coste y el margen, el presupuesto ratificado, y —lo más caro— **una declaración pública y fechada de intención de clonar un producto de terceros con marca**, justo en el proyecto cuya defensa jurídica se está construyendo con gates. No bloquea ninguna tarea técnica; bloquea, si se materializa, **la posición negociadora y la narrativa legal de GC-01**. Coste de ejecutar: **dos comandos**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Toca la superficie comercial y por tanto GC-01 (`gobernanza.md` §8). Un agente deja los comandos preparados y la justificación escrita; **no ejecuta**.

---

### A-23 · CS-46 — Merge a `main`: sí ahora, y escribir la regla de cadencia que falta

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Ventana:** después de A-22, hoy

**(a) CRITERIO.** En un flujo sin PR, **`main` = lo verificado, no lo último**. Un commit se mergea cuando es **verificable en aislamiento**: sus pruebas pasan y no depende de trabajo a medio hacer. El estado del ledger (`en-progreso` / `completado`) es **ortogonal** al merge — una tarea en curso puede tener commits verdes y cerrados. **Regla adicional, que es la que de verdad protege un flujo solo**: nunca mergear un cambio que mueva el estado de una tarea en el ledger sin que sus checkboxes lo respalden. Sin PR, el ledger es el único control que queda; falsearlo no tiene red.

**(b) FUNDAMENTO.** ✅ Estado verificado: `main` = `3739d20` (importación inicial), `feature/plataforma-musical-ia` = `ec9a175`, **tres commits por delante**, diff de 5 ficheros / +124 / −21 líneas. Los tres son autocontenidos y verificados: `9e9df9a` construye el fusor del artefacto y cierra CS-50 (`--selftest` y `--verify` en verde, 0 desbordamientos en la conversión BF16→FP16 sobre 3.074.063.112 elementos, 13 tests nuevos); `316b00a` contenerización `T-05`, imagen construida y ejecutada con `--gpus all` sobre la GPU real; `ec9a175` actualización de ledger. El trabajo realmente en vuelo **no está comprometido**: `apps/runner/spikes/pascal_speed_probe.py` figura como *untracked*. **Argumento que no vale y se descarta explícitamente**: no hay riesgo de pérdida de trabajo, porque `origin/feature/plataforma-musical-ia` ya apunta a `ec9a175`. `CLAUDE.md` fija el flujo («merge directo a `main` sin PR») pero **no fija el cuándo**: ese es el hueco.

**(c) RECOMENDACIÓN.** Mergear ahora (fast-forward limpio de `3739d20` a `ec9a175`, sin conflicto posible) y dejar `pascal_speed_probe.py` sin commitear hasta que mida algo. Añadir a `CLAUDE.md`, junto a la línea del flujo solo, la **regla de cadencia** que hoy falta: «se mergea a `main` **(a)** cuando un commit es verificable en aislamiento y **(b)** obligatoriamente al cerrar cada sub-fase del plan, porque es donde `improvement-plan.md` define criterios de salida; **nunca** se mergea un cambio de estado de tarea en el ledger cuyos checkboxes no lo respalden». **Secuencia obligatoria**: `main` es la rama por defecto de un repositorio **público**; ejecutar este merge **después** de A-22, no antes (ver **X-7**). Es un minuto de diferencia y evita publicar tres commits más bajo un nombre de repo que hay que cambiar.

**(d) CONSECUENCIA DE NO DECIDIR.** Riesgo bajo pero creciente: cuanto más se separa la rama, más trabajo verificado queda fuera de la rama por defecto, que es lo que cualquiera —incluido el propio propietario dentro de seis meses— lee primero. **El coste real de no fijar la cadencia es mayor que el de no mergear hoy**: sin regla escrita, en un flujo sin PR el criterio de merge acaba siendo el humor del día, y ahí es donde un flujo solo se degrada — precisamente el escenario que `gobernanza.md` aceptó por escrito como riesgo al eliminar la revisión por terceros.

**(e) QUIÉN FIRMA.** ⚙️ **Agente** para el merge (operativa de rama ya fijada por `CLAUDE.md`). La adición de la regla de cadencia a `CLAUDE.md` se propone como texto; **modificar `CLAUDE.md` lo aprueba el propietario**.
---

## 3. Bloque B — Con fecha en un gate

> Nada de aquí bloquea el teclado hoy. Todo tiene un plazo concreto —F4, F5, F6/F7, F10, F11 o GC-01— y un coste que crece si se decide **después** de ese plazo en vez de antes. El orden dentro del bloque es por proximidad del plazo.

### B-01 · D-adapter-410 — `adapter.py:410` declara Apache 2.0: los pesos de ACE-Step 1.5 son MIT

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** F5 (`T-30`) — **pero cuesta 5 minutos hoy**

**(a) CRITERIO.** La licencia de un artefacto de pesos se toma de **la revisión fijada del repo que lo publica**, no de la versión anterior del modelo ni del repo de código. **Licencia de PESOS y licencia de CÓDIGO son campos distintos y se registran por separado.**

**(b) FUNDAMENTO.** ✅ Verificado vía API de HuggingFace: `ACE-Step/Ace-Step1.5` con `sha=19671f406d603126926c1b7e2adc169acbcade22` (**exactamente la revisión fijada del proyecto**) declara `cardData.license = 'mit'`; el fichero `raw/main/LICENSE` devuelve **HTTP 404** (no hay fichero: la licencia vive en el frontmatter del card). Respaldo: GitHub `ace-step/ACE-Step-1.5` = MIT («MIT License / Copyright (c) 2026 ACEStep»). En contraste: `ACE-Step/ACE-Step-v1-3.5B` = `apache-2.0` y GitHub `ace-step/ACE-Step` (código) = Apache-2.0 — **de ahí salió el error**. ✅ El repo ya se contradice: `apps/runner/tools/build_artifact.py:290` declara `('acestep','MIT','LICENSE.acestep.mit.txt')` mientras `adapter.py:410` dice Apache 2.0; y `acestep_analysis/README_upstream.md:3` dice `license: mit`. **Segundo error en la misma frase**: «declaración de datos de entrenamiento no divulgada» — ✅ el model card **sí** declara categorías (Licensed Data / Royalty-Free-No-Copyright / Synthetic MIDI-to-Audio) y afirma «You can strictly use the generated music for commercial purposes»; no nombra datasets ni es auditable, pero «no divulgada» es **inexacto** (ver **X-5**).

**(c) RECOMENDACIÓN.** Parche exacto en `apps/runner/adapters/ace_step/adapter.py` líneas 409-411, sustituyendo el comentario por:

```python
#: Versión del modelo, no de este adapter. El descriptor completo (con
#: `weights_sha256`, licencia MIT y declaración de datos de entrenamiento
#: "declarada-por-el-proveedor-sin-auditar") lo construye `T-30` en la F5.
#: Apache-2.0 es la licencia de ACE-Step v1 (3.5B) y la del código upstream
#: (`ace-step/ACE-Step`), NO la de los pesos de 1.5: `ACE-Step/Ace-Step1.5`
#: @19671f40 publica `cardData.license = "mit"` (no hay fichero LICENSE en
#: el repo de HF: 404). El artefacto redistribuye DOS licencias — ver
#: `build_artifact.py:FICHAS_LICENCIA`.
```

**Recomendación de diseño que evita la reincidencia:** el descriptor de `T-30` **no debe llevar un campo `license` escalar**. El artefacto es una **fusión de componentes con dos licencias** (DiT+VAE MIT, Qwen3-Embedding Apache-2.0, decoder Oobleck vendorizado Apache-2.0 de `diffusers`, LM derivado de Qwen3-1.7B), así que debe llevar **lista por componente**. `build_artifact.py` **ya lo hace bien** (array `licenses` con SPDX + `license_file_sha256`): `T-30` debe **consumir** esa estructura, no reinventarla. **Conflatar código y pesos en un escalar es exactamente el mecanismo que produjo este error.**

**(d) CONSECUENCIA DE NO DECIDIR.** **¿Afecta al manifiesto? Hoy no, y no por suerte**: ✅ `D:\srv\ace-step\provenance\MANIFEST.json` (generado `2026-09-01T16:15:11Z`) ya registra `licencias.ace_step.spdx = 'MIT'` y un campo literal `correccion_pendiente = 'adapter.py:410 declara licencia Apache 2.0 - es la de ACE-Step v1 (3.5B), NO la de 1.5. Corregir en T-06/T-33'`, y `training_data_declaration` ya trae el valor corregido. No existe ningún manifiesto de generación (`T-26`/`T-30` están en F5), así que **no hay nada emitido que reparar**. **Mañana sí, y caro**: la línea 410 es literalmente el **insumo de diseño del descriptor de `T-30`**; si sobrevive, cada manifiesto declararía Apache-2.0 para un artefacto MIT —y el manifiesto es la pieza sobre la que descansa toda la defensa legal—, afirmaría una obligación de NOTICE (Apache-2.0 §4(d)) que MIT no impone, omitiría la que MIT sí impone y alimentaría `commercial_use` de la regla 5 del registry con una premisa falsa. Corregirlo **después** de que existan pistas obliga a bump de `manifest_schema_version` con verificador multiversión (`T-27`). **Ahora cuesta 5 minutos.**

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Corrección de un dato verificado contra fuente primaria, sin efecto de alcance ni de gasto.

---

### B-02 · CS-26 / I-17 — Retención de logs y datos personales: el RGPD no aplica hoy, pero hay una mina antipersona en el manifiesto

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo duro:** la parte (1) + el cambio de diseño, **antes de `T-26`**; los cubos (2) y (3), antes de `T-24`

**(a) CRITERIO.** Dos reglas encadenadas. **(1) Aplicabilidad**: el RGPD solo aplica si hay dato personal **y** el tratamiento no es «actividad exclusivamente personal o doméstica» (Reg. UE 2016/679, **Art. 2.2.c**; Considerando 18). Con un único usuario que es a la vez responsable, interesado y titular de la infraestructura self-hosted, la excepción se cumple limpiamente: no hay encargado externo que «proporcione los medios» (el matiz del Considerando 18). **(2) Retención**: aunque el RGPD no aplique, cada categoría de dato se retiene el tiempo que sirva a su propósito declarado, y **nunca más del tiempo que se pueda revertir**. La regla operativa que decide todo el diseño: **solo es indefinido lo que es inmutable por diseño; todo lo demás lleva número**. Corolario: **lo indefinido no puede contener identificadores directos, porque lo indefinido no se puede borrar**.

**(b) FUNDAMENTO.** Aplicabilidad: `CLAUDE.md` («plataforma web personal/self-hosted»), `gobernanza.md` (`cerrado-modo-solo`, usuario piloto único = propietario) y GC-01 §8e, que ya reserva RGPD/DPIA solo para el escenario de clonación de voz. **Lo que el sistema genera realmente**, verificado: **(a)** ledger de procedencia C-10a — append-only con cadena de hashes desde la primera pista, y ✅ `spec.md`:552 dice literalmente que «una cadena WORM no admite backfill»: **indefinido e irreversible por diseño**; **(b)** trazas OTel `T-24` (`tasks.md`:633-645) con `gpu_seconds`, coste por generación, coste acumulado del mes y «coste por usuario/proyecto»; **(c)** auditoría de accesos `T-52` (`tasks.md`:1333: «login, fallos de autenticación»); **(d)** artefactos de audio, que **ya tienen números decididos** en `spec.md`:530 (no favoritas: frío a 30 días, borrado a 180 salvo producción entregada; favoritas indefinido); **(e)** datos personales estrictos: email + hash de password + secreto TOTP (`T-50`/`T-51`). La propuesta vigente para logs es `spec.md`:544 («30 días en caliente, 12 meses en frío, datos personales minimizados»), marcada ⚠️ definir. **Hallazgo que no estaba en el tablero**: ✅ `spec.md`:341 especifica que la declaración de derechos de la letra «se registra en auditoría con usuario, fecha y contenido, **y viaja en el manifiesto**», y `spec.md`:284 exige `lyrics_declaration` en el manifiesto v1. Cruzado con `spec.md`:552 (WORM sin backfill), eso significa que **el texto íntegro de la letra y el identificador del usuario quedan inmortalizados en una cadena que por construcción no se puede rectificar ni borrar**. En uso personal es inocuo. En el escenario GC-01 colisiona de frente con el **Art. 17** (supresión) y el **Art. 16** (rectificación): sería un incumplimiento **estructural**, no corregible con una migración.

**(c) RECOMENDACIÓN.** Política en **cinco cubos**, para escribir en `spec.md` §12.3 sustituyendo el «⚠️ definir» de la línea 544: **(1) Ledger + manifiestos**: indefinido e inmutable — es el artefacto con valor legal, es el producto. **(2) Trazas OTel**: **30 días, sin capa fría** — se recortan los «12 meses en frío» porque su único propósito sería el forense multi-tenant, que con un usuario no existe. **(3) Métricas agregadas** (`gpu_seconds`, coste/mes, tasa de éxito): **13 meses** — no son logs, alimentan `T-41` y el checkpoint de stop-loss, que son mensuales y necesitan comparación interanual. **(4) Auditoría de accesos**: **90 días** — su única utilidad real es detectar acceso no autorizado a una app self-hosted expuesta a internet. **(5) Cuenta** (email, hash, TOTP): mientras exista la cuenta; purga a los **30 días** del cierre. Y el borrado a 180 días de (d) debe propagarse a **backups en ≤ 30 días** (`spec.md`:551), para que «borrado» signifique borrado.

**Cambio de diseño que se pide ratificar aparte, y es el importante:** en el manifiesto y el ledger, guardar **la letra por HASH** y **el usuario por seudónimo opaco estable** (`owner_ref`), no en claro. La letra en claro y el email viven en Postgres, siguiendo la retención de (d)/(5). **Esto no degrada ningún invariante**: la declaración de derechos sigue siendo bloqueo duro (D-21), el hash sigue probando que se declaró y sobre qué texto, y la cadena sigue verificando. Lo que hace es que **el ledger deje de ser un almacén indefinido de datos personales**. Coste hoy: cero. Coste si se decide después de `T-26`: **imposible de reparar hacia atrás**.

**(d) CONSECUENCIA DE NO DECIDIR.** Los cubos 2–5 no bloquean nada hoy: `T-24` está en F4 y su coste de decidir tarde son horas de reconfiguración (16 h). **El cubo 1 es distinto**: si el manifiesto v1 se firma y emite con letra en claro + identificador de usuario, cada pista generada a partir de ese momento entra en una cadena que `spec.md`:552 declara **no rectificable**. Corregirlo después obliga a subir `manifest_schema_version`, ampliar el corpus multiversión del verificador de CI (`T-27`) y **convivir para siempre con dos formatos** — y aun así las entradas antiguas quedan como están. **El coste de decidir tarde no se mide en horas: es permanente.** La ventana se cierra el día que se firme `T-26`. Si además se llega a GC-01 con el ledger así, la condición §8e deja de ser «solo si Fase 4» y pasa a **bloquear cualquier comercialización**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Fija política de retención y cambia el diseño del manifiesto, que es invariante del proyecto.

---

### B-03 · CS-41 — El diferimiento de la firma del esquema del manifiesto está mal fundado en un punto

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** antes de F5 (`T-26`), pero muerde en F2

**(a) CRITERIO.** Un diferimiento está bien fundado si **(a)** nada anterior al nuevo plazo depende de él y **(b)** no contradice una regla declarada innegociable. Basta que falle una para que el diferimiento deba **reescribirse**, aunque la conclusión práctica sea la misma.

**(b) FUNDAMENTO.** **(a) Dependencia anterior**: ✅ `pre-dev-checklist.md` ítem 12 fija el plazo «antes de iniciar F5 (`T-26`)», pero `g1-protocolo.md` §10.1 **ya exige emitir un manifiesto retroactivo por cada pista propia de G1**, que ocurre en **F2** — y con campos que no coinciden con los de v1 (ver **A-18**). **(b) Contradicción declarativa**: ✅ `CLAUDE.md` dice literalmente «El esquema del manifiesto lo firma legal antes de implementarse», y el ítem 12 lo sustituye por «en modo personal la firma formal de legal se difiere a GC-01 (el propietario valida el esquema)». Esa sustitución es defendible en modo solo, **pero hoy `CLAUDE.md` sigue diciendo lo contrario: la contradicción está viva en la fuente de invariantes**. Y `T-26` (`tasks.md`:679) sigue titulándose «Firma del esquema del manifiesto **por legal**» con criterio de aceptación «Firma/aprobación de legal obtenida y archivada, antes de iniciar `T-29`/`T-30`». Ver **X-8**.

**(c) RECOMENDACIÓN.** Tres actos pequeños: **(1)** actualizar el invariante de `CLAUDE.md` para que diga lo que de verdad rige en modo solo («el propietario valida el esquema; la firma de legal se traslada a GC-01 §8/§8d antes de cualquier uso comercial»), **o bien** mantener el invariante y aceptar que `T-26` bloquea F5 — pero **elegir**, no dejar las dos versiones; **(2)** reescribir el título y los criterios de `T-26` en consecuencia; **(3)** **adelantar a F2 la lista de campos obligatorios del manifiesto** (no el esquema completo, solo la lista) para que las pistas de G1 nazcan capturándolos. No es una tarea nueva de peso: son **horas de `T-26` que se adelantan**, no horas añadidas.

**(d) CONSECUENCIA DE NO DECIDIR.** Se llega a `T-26` con un corpus de **diez manifiestos que no cumplen el esquema que se va a firmar** y sin poder corregirlos (D-20: la cadena WORM no admite backfill). Y el proyecto conserva **un invariante escrito que ya no cumple**, lo que devalúa la palabra «innegociable» para todos los demás invariantes de la lista, **incluido el de `safetensors`**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Modifica un invariante de `CLAUDE.md` y el título/criterios de una tarea del ledger.

---

### B-04 · T-33 (ffmpeg) — Una build LGPL cubre el 100 % de la Fase 1; el riesgo real es que `apt-get install` trae una build GPL

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** F5 (`T-33`), pero **la ficha se fija hoy**

**(a) CRITERIO.** **(1)** Nada con término no comercial. **(2)** Nada con copyleft fuerte (GPL/AGPL) que alcance al código propio. **(3)** Copyleft débil (LGPL) admisible **solo** si el uso es a distancia (proceso separado) y se cumple la checklist del titular. **(4)** Se verifica **contra metadatos publicados**, no contra el README de nadie.

**(b) FUNDAMENTO.** ✅ `ffmpeg.org/legal.html`, literal: «FFmpeg is licensed under the GNU Lesser General Public License (LGPL) version 2.1 or later. However, FFmpeg incorporates several optional parts and optimizations that are covered by the GNU General Public License (GPL) version 2 or later. **If those parts get used the GPL applies to all of FFmpeg**». Checklist de la misma página: «Compile FFmpeg **without `--enable-gpl` and without `--enable-nonfree`**»; «Go through all the items again for any LGPL external library you compiled into FFmpeg (for example **LAME**)»; «Make sure your program is not using any GPL libraries (notably libx264)». **Mapeo a lo que la Fase 1 necesita**: FLAC de almacén = codificador **nativo** de ffmpeg (LGPL); MP3 320 = **libmp3lame**, y la propia página cita LAME como ejemplo de librería externa **LGPL**; WAV 48 kHz = **libsoxr** (LGPL-2.1); loudness EBU R128 = **loudnorm/ebur128 nativos** (LGPL). Ninguno exige `--enable-gpl`. Lo que fuerza GPL son códecs de vídeo (x264, x265, frei0r, libvidstab) **que este proyecto no usa jamás**. **Riesgo concreto**: el paquete `ffmpeg` de Debian/Ubuntu y las builds estáticas populares (BtbN, John Van Sickle) **son builds GPL**; un `apt-get install ffmpeg` en la imagen del runner mete GPL en el artefacto. En despliegue puramente self-hosted que nunca se distribuye las obligaciones GPL no se disparan (se disparan **al distribuir**), pero el repo es público y GC-01 contempla comercialización — ver **X-7**. ⚠️ **No verificado hoy y así se marca**: la expiración de las patentes de MP3 (2017); el *Patent Mini-FAQ* de ffmpeg advierte explícitamente sobre uso comercial y MPEG LA.

**(c) RECOMENDACIÓN.** **(1)** Fijar en la ficha de `T-33`: build **LGPL-2.1+** con `--disable-gpl --disable-nonfree`, solo **libmp3lame + libsoxr + FLAC nativo + loudnorm**. **(2)** Añadir una **aserción de build** en el mismo estilo que la aserción de `arch_list` que ya existe en `apps/runner/adapters/ace_step/Dockerfile` (el mejor patrón del repo): **que el build FALLE si `ffmpeg -version` muestra `--enable-gpl` o `--enable-nonfree`**. Coste: 3 líneas; es la única forma de que la propiedad no se pierda en el siguiente rebuild. **(3)** Registrar el aviso LGPL («This software uses libraries from the FFmpeg project under the LGPLv2.1») donde el manifiesto lleva los avisos: `build_artifact.py` ya tiene el mecanismo (`license_notes`). **(4)** Dejar escrita en la ficha la pregunta «**¿distribuimos o no?**» (repo público, GC-01, patentes MP3) aunque hoy la respuesta sea «no distribuimos».

**(d) CONSECUENCIA DE NO DECIDIR.** `T-33` son 5 h = 250 € base / 300 € con margen. **El momento importa**: si la build GPL entra ahora y se descubre en F10, cambiar de build **después** de que existan pistas generadas obliga a **revisar la ficha de procedencia de esas pistas**. Ahora cuesta 3 líneas.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Es una decisión técnica de build dentro de una tarea ya presupuestada, con criterio verificado contra la fuente del titular.

---

### B-05 · T-33 (dependencias) — Todas permisivas, ninguna contamina: verificado contra PyPI, no contra el comentario del `Dockerfile`

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** F5 (`T-33`); el ítem ABIERTO del `Dockerfile` se cierra hoy en 10 minutos

**(a) CRITERIO.** Verificar contra **los metadatos publicados del paquete** (API JSON de PyPI: `license_expression` / classifiers), no contra la lista escrita a mano en el `Dockerfile`.

**(b) FUNDAMENTO.** ✅ Consultado el 2026-09-01 en `pypi.org/pypi/<pkg>/json`: `transformers` 5.16.1 = «Apache 2.0 License»; `tokenizers` 0.23.1 = classifier «Apache Software License»; `safetensors` 0.8.0 = classifier «Apache Software License»; `huggingface-hub` 1.29.0 = «Apache-2.0»; `einops` 0.8.2 = MIT; `vector-quantize-pytorch` 1.31.1 = MIT; `einx` 0.4.3 = MIT; `torch-einops-utils` 0.1.22 = MIT; `numpy` = «BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0» (compuesta, toda permisiva); `torch` 2.13.0 (de la imagen base, no por pip) = «Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-…». **Coinciden al 100 %** con la lista de `apps/runner/adapters/ace_step/Dockerfile` líneas 180-188. **Cero copyleft** en el conjunto pip; el único copyleft de todo el pipeline de Fase 1 es **ffmpeg**, y solo si se elige mal la build (B-04).

**(c) RECOMENDACIÓN.** Dar por verificado el bloque de dependencias de `T-33` con esta evidencia (ahorra parte de sus 5 h). Además, **cerrar el ítem que el `Dockerfile` líneas 191-192 deja marcado como ABIERTO** («ficha de licencia del snapshot de Qwen3-Embedding-0.6B: la copia local no trae LICENSE ni NOTICE»): ✅ HF `Qwen/Qwen3-Embedding-0.6B` declara `cardData.license = 'apache-2.0'`, verificado hoy; la copia vendorizada dentro del repo de ACE-Step no trae LICENSE pero **el upstream sí**, y `build_artifact.py:291` ya lo registra correctamente como `('qwen3_embedding','Apache-2.0','LICENSE.qwen3-embedding.apache-2.0.txt')`.

**(d) CONSECUENCIA DE NO DECIDIR.** Un ítem marcado **ABIERTO** en el `Dockerfile` bloquea **conceptualmente** el uso del artefacto de pesos («hay que cerrarlo antes de usar el artefacto»), pese a estar de hecho resuelto. **Cuesta 10 minutos y desbloquea la ficha.**

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Verificación documental contra fuente primaria.

---

### B-06 · CS-24 / I-15 — Plan de entornos: dos, no tres

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** antes de arrancar `T-23` (F4)

**(a) CRITERIO.** Un entorno se justifica solo si **(a)** protege un artefacto que no se puede recrear, o **(b)** valida algo que ningún otro entorno puede validar. **Se cuentan los entornos por artefactos irreversibles y por audiencias, no por convención de la industria.** Corolario: `stage` existe para proteger a **terceros** de un despliegue roto; sin terceros, `stage` valida para un público que no existe.

**(b) FUNDAMENTO.** ✅ El único artefacto irreversible del sistema está identificado: el **ledger de procedencia**, porque `spec.md`:552 establece que «una cadena WORM no admite backfill». Todo lo demás (Postgres, Redis, artefactos de audio, imágenes de contenedor) es reconstruible. **Audiencia**: `gobernanza.md` deja cerrado que el usuario piloto único es el propietario, y `spec.md`:505 dimensiona cuotas «con 5 usuarios» **que hoy no existen**. Lo que `stage` aporta según el plan es exactamente: `tasks.md`:605 («un merge a la rama principal despliega automáticamente a stage») y `tasks.md`:625 («stage usa pods GPU efímeros con tope de gasto propio»). **Coste**: `evaluation.md`:384 estima los tres entornos no-GPU en **80–250 €/mes** y `:344` lo proyecta a **1.920–6.000 € a 24 meses**, marcado ⚠️ **no presupuestado** — está **fuera** de los 39.360 € ratificados. **Y una contradicción de premisa que nadie había señalado**: `CLAUDE.md` define el producto como «personal/self-hosted», mientras que `evaluation.md`:384 presupuesta «Postgres y Redis gestionados, hosting de Next.js y FastAPI» — es decir, **se estaba presupuestando SaaS gestionado para un producto cuya tesis es el self-hosting**. El propio plan ya asume lo contrario en `improvement-plan.md`:185, cuyo criterio de salida de F4 es «`docker compose up` levanta el entorno completo». ⚠️ **No verificable hoy**: no se han podido confirmar precios de hosting ni de dominio a fecha de hoy; **no se inventan**. La única cifra citada es la del propio repo.

**(c) RECOMENDACIÓN.** **Dos entornos**, distinguidos por durabilidad del dato y por canonicidad del ledger, no por infraestructura: **(1) `dev`** — local, `docker compose`, `GPU_PROVIDER=local|mock`, base de datos efímera, y su **ledger marcado explícitamente como NO CANÓNICO** (bandera en el propio registro, para que un manifiesto de dev nunca pueda confundirse con uno bueno); **(2) `prod`** — la misma máquina, volúmenes persistentes, backup PITR según `spec.md`:551, y **único dueño del ledger canónico**. **`stage` se difiere a GC-01**: se reactiva el día que haya un tercero a quien un despliegue roto pueda perjudicar, que es literalmente su razón de ser. **Efecto económico**: la partida ⚠️ no presupuestada de 1.920–6.000 €/24 m baja a dominio + certificado (Let's Encrypt, 0 €) + electricidad; ⚠️ esos dos no se cifran porque no se han verificado hoy. **Consecuencia de alcance que hay que asumir explícitamente, y por eso firma el propietario**: esto **contradice dos criterios de aceptación ya escritos** — `tasks.md`:605 (CI despliega a stage) y `tasks.md`:624 («los tres entornos dev/stage/prod se pueden crear/destruir de forma reproducible desde IaC»). Hay que **reescribirlos a dos entornos, no ignorarlos**: un criterio de aceptación que se deja escrito y no se cumple es peor que uno que se cambia con firma. **No se reclama ahorro de horas** en `T-23` (10 h) ni en `T-22`: reestimar es trabajo del `evaluator`.

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea hoy — `T-23` vive en F4. Pero si no se decide **antes de escribir `T-23`**, el IaC se escribe para tres entornos y después se reescribe: horas tiradas y, sobre todo, un `stage` que existe, cuesta y nadie usa (**el patrón clásico: el entorno que nadie mira acumula deriva hasta que deja de validar nada**). Coste de no decidir nunca: la partida de 1.920–6.000 €/24 m sigue fuera del presupuesto ratificado y, cuando aparezca, aparecerá como **sobrecoste y no como decisión**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Cambia criterios de aceptación escritos y toca una partida no presupuestada.

---

### B-07 · CS-49 (T-86 / D-30) — Descartar el instalador del runner GPU local con su alcance actual

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** F6 — **pero el denominador del stop-loss está ambiguo desde hoy**

**(a) CRITERIO.** **Regla de amortización de automatización**, enunciada antes de mirar el resultado: una automatización se paga si `(horas_manuales_por_ejecución × nº_ejecuciones_previstas_en_el_horizonte_del_plan) > horas_de_construcción`, **más** un término de riesgo por los fallos que la automatización detecta y el camino manual no puede detectar. **Si el término de riesgo ya está cubierto por código existente y el nº de ejecuciones previstas es 1, la automatización no se paga por ningún valor de horas manuales.** Corolario: la pregunta correcta no es «¿aporta valor?» sino «**¿para cuántas máquinas destino, y qué fallo previene que hoy no se detecte?**».

**(b) FUNDAMENTO.** **(1) Nº de ejecuciones previstas = 1, hoy.** ✅ `spec.md`:434 (I-22, **abierta**): «la máquina de desarrollo es Windows… el despliegue final puede quedarse en esta máquina o ir a otra». **No hay ninguna segunda máquina comprometida en ningún documento.** **(2) El término de riesgo ya está a cero.** Las dos únicas cosas que `T-86` previene y el runbook no: **(a)** integridad de pesos — **ya cubierta** por `apps/runner/tools/build_artifact.py` (2.792 líneas; `sha256_fichero` en `:353`, `--selftest` y `--verify` en verde, cuarentena del pickle con lista blanca de opcodes vía `pickletools.genops`, artefacto sellado con SHA-256 `3faa5ac9…5812d947`); **(b)** degradación silenciosa a mock — **ya cubierta** por el guardarraíl G-01 (`ACE_STEP_REQUIRE_GPU=1`), que cuesta 0 h. **(3) El preflight manual ya se ejecutó hoy y quedó atestiguado**: ✅ ítem 6/CS-35 CERRADO (driver 582.66, Docker Engine 29.7.2 sobre WSL2, `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` lista la GTX 1070 con 8192 MiB **dentro del contenedor**); ✅ ítem 7/CS-36 CERRADO (17/17 hashes, 6,333 GB, revisión fijada, `MANIFEST.json`). **(4) Detección de GPU/VRAM parcialmente existente**: `apps/runner/spikes/_timing.py` (`VRAM_FLOOR_MB`, `VRAM_FLOOR_TOLERANCE_MB`, `vram_snapshot_mb`, `decide_offloading`) + 13 tests. **(5) Aritmética del punto de equilibrio** con el desglose ascendente de `tasks.md`:1057ss (4+8+6+5+3+6 = 32 h): si el preflight manual cuesta 1 h/máquina el equilibrio está en **32 máquinas**; a 2 h/máquina, en **16**; a 3 h/máquina, en **11**. Contra **1 máquina conocida**, el margen de error es de **11× a 32×** — no es una decisión ajustada. **(6)** Además `T-86` declara explícitamente en sus criterios que **no** gestiona driver NVIDIA ni Docker («no se toca y se declara explícitamente en la salida»), que es justamente donde se va la mayor parte del tiempo manual de una máquina limpia.

**(c) RECOMENDACIÓN.** **Descartar `T-86` tal como está estimada.** Acciones: **(a)** marcarla en `tasks.md` como **«descartada (no amortiza)»** con el cálculo de equilibrio, **no borrarla** —el rastro vale—; **(b)** conservar D-30 en `spec.md`:85 como decisión de diseño **reclasificada a `bloqueada (gate GC-01)`**: el instalador solo tiene sentido si el proyecto se entrega a un tercero, que es exactamente el gate de comercialización; **(c)** sustituirla por **2 h dentro de las 16 h ya ratificadas de `T-85`**: volcar la evidencia verificada hoy (versiones de driver/Docker, comando exacto del toolkit, ruta y hash del artefacto, procedimiento de `build_artifact.py`) en `runbooks/gpu-local-requisitos.md`, **convirtiendo el runbook en reproducible sin gastar 1.920 €**; **(d)** fijar el **disparador de reapertura** por escrito: reabrir `T-86` **solo** si I-22 se cierra con **≥ 3 máquinas destino** o si el proyecto pasa GC-01. Si aun así se quiere algo ejecutable, el subalcance defendible es únicamente el subcomando **`preflight`** (sin `install`, sin `uninstall`, sin descarga de pesos —`build_artifact.py` ya es dueño de eso—), reutilizando `_timing.py`: **6–8 h, no 32 h**. **Nota de coherencia**: si se descarta, el ledger queda limpio en **1.063 h / 63.780 €** y Fase 0+1 en **656 h / 39.360 €**, sin la cifra fantasma.

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea nada operativamente: `T-86` depende de `T-05`/`T-36`/`T-85`, todas en F6, y hoy estamos en F2. **Pero sí tiene un coste inmediato**: mientras el delta siga sin ratificar, el presupuesto de Fase 0+1 es ambiguo (656 h/39.360 € **o** 688 h/41.280 €, `tasks.md`:43-48), y eso **corrompe el denominador del stop-loss D-28**: el gate dispara a **394 h o a 413 h** según cuál se use (ver **X-6**). **Un gate cuyo umbral depende de una decisión sin tomar no es un gate.** Coste del retraso: cero euros hoy, pero **un gate inoperante desde ya** hasta que se cierre.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Es alcance y presupuesto: descarta 32 h / 1.920 € propuestos y reclasifica una decisión de diseño de la spec.

---

### B-08 · CS-17 / I-09 — Descartar el pod caliente (128 €/mes) y quedarse en keep-warm (45 €/mes)

**Estado:** 🔒 pendiente de firma · **Confianza:** media · **Plazo:** F6/F7

**(a) CRITERIO.** Un gasto recurrente de latencia se justifica solo si elimina una espera que **rompe el bucle creativo** *y* esa espera ocurre **con frecuencia**. Se paga por eliminar esperas **repetidas**, no por eliminar la primera espera de la sesión. **Regla operativa aplicable por cualquiera**: si la espera se paga **una vez por sesión** de trabajo y la UI la dice honestamente, es tolerable; si se paga **en cada iteración de una ráfaga**, no lo es.

**(b) FUNDAMENTO.** **(1)** ✅ Opciones cuantificadas en el propio expediente: **F** (pod efímero + keep-warm 10 min) = **45 €/mes**; **G** (pod caliente en horario laboral) = **128 €/mes**; delta **83 €/mes ≈ 996 €/año** (`evaluation.md`:228). **(2)** Lo que compra cada una está escrito y es distinto: F — «en generación musical el usuario itera 5-10 variantes seguidas: el keep-warm hace **instantáneas las variantes 2..N**»; G — «Ninguno mientras alguien trabaja». Traducción: **G solo elimina la primera espera de la sesión, que es la única que F no cubre**. Los 83 €/mes compran exactamente eso y nada más. **(3)** El dimensionado de G asume **176 h/mes** de pod encendido (8 h × 22 días) para «1-5 usuarios en horario». En modo solo hay **1 usuario** con cuota de 200 gen/mes: a S-02 = 150 s/gen son **8,3 h de GPU útil al mes frente a 176 h pagadas = 4,7 % de utilización**, ~15,4 €/h efectivos frente a 0,79 $/h de tarifa. ✅ El propio `decision-brief.md`:97 ya usa ese razonamiento para descartar la GPU dedicada 24/7 («5,8 % de utilización»): **con un solo usuario, la opción G cae bajo la misma objeción que el brief ya aceptó**. **(4)** ✅ La UI ya está construida para **absorber** esa espera, no para esconderla: `ui-design.md` §3.3 activa el modo espera-larga a partir de 60 s con «**La GPU está arrancando en frío: entre 2 y 6 minutos.** Tu pista no ha empezado a generarse todavía», cronómetro **hacia arriba** («2:14 de ~2-6 min»), y §8 regla 4 prohíbe barras que fingen precisión. **El coste de UX de la opción F ya está pagado en diseño; lo que no está construido es el ahorro de 83 €/mes.** **(5)** Hoy no hay nada que pagar: D-29 pone Fase 0 y G1 en GPU local a coste cloud cero. **(6)** ⚠️ **Lo que no se puede saber hoy**: **S-02 (150 s/gen) no está medido** — la propia spec ordena «Debe medirse en el spike» y el shim no existe. Y hay un dato que apunta en dirección contraria al supuesto: la model card declara «under 10 seconds on an RTX 3090» para el turbo de 8 pasos. Si eso se confirma en hardware moderno, **el tiempo de generación deja de ser el término dominante y toda la latencia percibida es arranque en frío** — lo que refuerza aún más elegir F (que ataca el arranque) antes que pagar 176 h de tarjeta ociosa.

**(c) RECOMENDACIÓN.** **(1) No tocar el SLO ya escrito**: p95 extremo a extremo ≤ 10 min (`spec.md` §12.3) se queda como está. **(2)** Cerrar I-09 añadiendo el **presupuesto de espera expresado por estructura**, no por segundos inventados sobre un S-02 sin medir: **TOLERABLE = un arranque en frío por sesión de trabajo** (2–6 min; hasta 12 min en el peor caso de S-01), siempre que la UI lo muestre con el cronómetro de `ui-design.md` §3.3. **NO TOLERABLE = arranque en frío en cada iteración de una ráfaga** (opción B) — eso es lo que compran los 45 €/mes de F. **(3) Fijar la opción F como postura de referencia y descartar la G** para cuando llegue F6/F7 (ver **X-1**, que resuelve el desacuerdo entre líneas). Actualizar en consecuencia `spec.md` §12.1 («1 pod caliente + 1 efímero» → keep-warm + efímero bajo demanda) y S-12, hoy dimensionados para 1-5 usuarios en horario laboral, premisa que I-01 ya invalidó. **(4) Cláusula de reapertura falsable**, para que esto sea una decisión y no una opinión: durante el mes de uso real que G3 ya exige (≥ 100 generaciones), instrumentar `cold_starts/mes` y `p95 de espera en estado starting` (métricas de `T-24`, ya presupuestadas). Se reabre G si se cumple **cualquiera** de: > 20 arranques en frío/mes · p95 de `starting` > 6 min · el propietario registra por escrito ≥ 3 sesiones abandonadas por la espera. **(5)** Ojo al alcance de lo que se firma: se decide **postura**, no gasto. El alta real del proveedor sigue siendo un acto del propietario en F6/F7 (B-09).

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea nada hoy. Bloquea al llegar a F6/F7: sin postura, la tarea de aprovisionar el proveedor no tiene destino y el ítem 22 del checklist no se puede cerrar, lo que retrasa el arranque de F7. **El coste del retraso no es dinero perdido, es dinero gastado de más**: cada mes que se opere con la opción G por inercia —que es la que `spec.md` §12.1 tiene escrita hoy como valor por defecto— son **83 € que no compran nada medible para un solo usuario**: 996 €/año, el 2,5 % del presupuesto ratificado de Fase 0+1, en OPEX invisible.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Postura de gasto recurrente y cambio de `spec.md` §12.1.

---

### B-09 · CS-40 — El pod de producción: la cifra de 128 €/mes es exacta pero solo en Community Cloud, y la postura está sobredimensionada ~20×

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** F6/F7 — **y la recomendación es precisamente no decidirlo ahora**

**(a) CRITERIO.** Una postura de infraestructura se elige **por el perfil de carga y por el problema de UX que compra**, no por su precio absoluto. **Regla de dimensionamiento**: si el coste de la postura excede en más de **5×** el coste de la postura mínima que satisface el requisito de UX declarado, la postura está sobredimensionada y hay que reexaminar el requisito. **Regla de honestidad presupuestaria en modo personal**: no es válido justificar un gasto de caja diciendo que es «ruido» frente a una cifra de esfuerzo, **porque son unidades distintas** (ver A-05).

**(b) FUNDAMENTO.** **(1)** ✅ `runpod.io/pricing` (obtenido 2026-09-01, pie «Updated July 27, 2026»): **L40S 48 GB = 0,99 $/h en Secure Cloud y 0,79 $/h en Community Cloud** (este último solo aparece en el bloque de datos estructurados de la página, no en la tabla visible). ⚠️ RunPod **no publica tarifario spot**: «spot capacity still exists as an API flag» pero **sin precio público**; el ~50 % de descuento que circula es crowd-sourced y **no verificable**. **(2)** Recálculo de la opción G (176 h/mes): L40S Community 176 × 0,79 = 139,04 $ = **127,92 €/mes** → la cifra de 128 €/mes de `evaluation.md` §6.3 **sigue siendo exacta al euro**, pero descubre su **supuesto oculto**: usó la tarifa que hoy es la de **Community Cloud**. En Secure Cloud son 176 × 0,99 = 174,24 $ = **160,30 €/mes (+25 %)**. El propio documento advierte de Community solo para la opción H («menos garantías de disponibilidad»), **no para la G que recomienda**. **(3) Sobredimensionamiento**: la opción G se justificó por «cero arranque en frío mientras alguien trabaja» y por cubrir «hasta ~4.200 gen/mes» — **un escenario multiusuario**. Con un usuario único, `evaluation.md` §6.1 da 7,9 h/mes facturadas a 100 gen/mes → **5,74 €/mes** en L40S Community o **3,20 €/mes** en A40 (ver B-10). Es decir: **la opción G cuesta 22× la opción B a volumen personal**, y la propia tabla §6.2 ya lo dice sin sacar la conclusión (G a 100 gen/mes = 1,28 €/generación frente a 0,058 €/generación de B). **(4)** El argumento nº 1 de `evaluation.md` §6.3 («45, 128 o 258 €/mes frente a 98.280 € de desarrollo son el 0,5-3 % anual») queda **invalidado en modo personal**: los 98.280 € son coste de oportunidad de horas propias (`spec.md`:422), los 128 €/mes son **caja**. Comparar ambos es un **error de categoría**, y es el argumento sobre el que se apoya toda la recomendación. **(5)** ✅ Egress verificado como **gratis** en fuente oficial: «All compute and storage charges are billed per second, with **no fees for data transfer**». **(6)** ✅ Almacenamiento persistente en RunPod: network volume **0,07 $/GB-mes** bajo 1 TB, 0,05 sobre 1 TB; volume disk 0,10 $/GB-mes en marcha y 0,20 parado; **el network volume sigue facturando con los pods apagados**.

**(c) RECOMENDACIÓN.** **(a)** Actualizar `evaluation.md` §6.2/§6.3 con la doble tarifa verificada y **declarar explícitamente que los 128 €/mes son la cifra de Community Cloud**, con su contrapartida de disponibilidad — hoy el documento la presenta como si fuera la tarifa a secas. **(b)** Sustituir la opción G por la **F** como postura de producción por defecto en modo personal (**B-08**; ver **X-1**: la opción B, aunque más barata, queda descartada por UX). Reservar la G para el supuesto que la justificaba —varios usuarios concurrentes—, que hoy no existe y que solo aparecería tras GC-01. **(c)** Retirar el argumento «es ruido frente a 98.280 €» de §6.3 y sustituirlo por la comparación honesta en caja: **128 €/mes son 1.536 €/año de desembolso real**, más que el coste anual de cualquier librería de producción del tier personal (ver B-12). Eso reordena la conclusión. **(d) No dar de alta el pod de producción ahora**: CS-40 está fechado «antes de F6/F7» y estamos en F2; darlo de alta hoy solo inicia el reloj de facturación. **(e)** Añadir la **partida olvidada**: si se cachea imagen+pesos en network volume para matar el arranque en frío, son ~30 GB × 0,07 $ = **1,93 €/mes que se pagan estén los pods encendidos o no**; a volumen personal esa partida es **comparable al coste de compute**, y hoy no está en ninguna tabla.

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna consecuencia inmediata —vence en F6/F7— **y esa es precisamente la recomendación: no decidirlo ahora es lo correcto, siempre que quede escrito por qué**. El riesgo real de no anotarlo es distinto: que en F6 alguien ejecute la opción G **por inercia documental** (está escrita como «Recomendada ✅» en `evaluation.md` §6.2) y se comprometa a **1.536–1.924 €/año** de caja para un usuario que genera unas decenas de pistas al mes. El coste del error, si se materializa, es **~1.500 €/año** — casi el importe completo del delta de `T-86` que sí se está discutiendo con lupa (B-07).

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Gasto recurrente y corrección de la recomendación de la evaluación.

---

### B-10 · CS-23 / I-14 — La hipótesis de I-14 es falsa: lo barato no es bajar a 24 GB, es cambiar de generación de tarjeta

**Estado:** ⚙️ lista para ejecutar · **Confianza:** media · **Plazo:** F6

**(a) CRITERIO.** El coste por generación es `precio_hora / pistas_hora`, **no** `precio_hora`. Una tarjeta más barata solo mejora el modelo de coste si **su penalización de velocidad es menor que su descuento de precio**. Regla de decisión: elegir la tarjeta con **mínimo `precio_hora × factor_lentitud_relativa`**, y declarar el factor de lentitud como **no medido** mientras no exista S-02 real, aplicando análisis de sensibilidad en vez de un número inventado.

**(b) FUNDAMENTO.** ✅ Precios verificados en `runpod.io/pricing` (2026-09-01, Secure Cloud salvo indicación): L40S 48 GB **0,99** (Community 0,79); L40 48 GB **0,82**; RTX 5090 32 GB **0,99**; RTX 4090 24 GB **0,74** (Community 0,34); L4 24 GB **0,49**; **A40 48 GB 0,44**; RTX A6000 48 GB **0,53**. ⚠️ **A10G no existe** en el catálogo de RunPod (es una SKU específica de AWS g5): no procede cotizarla en este proveedor. **Conclusiones aritméticas**: **(1)** A igualdad de tier, bajar de 48 GB a 24 GB ahorra el **25,3 %**, no el 50 % (4090 0,74 vs. L40S 0,99): **la hipótesis de `spec.md`:425 / `evaluation.md` §6.2 opción H («a la mitad del precio de la L40S la opción G bajaría a ~64 €/mes») no se cumple en Secure Cloud**. **(2)** El 57 % de ahorro que se le atribuye a los 24 GB (4090 Community 0,34 vs. L40S Community 0,79) es real, **pero procede del TIER, no de la VRAM**: atribuirlo a la VRAM es un **error de causalidad**. **(3) El hallazgo que faltaba**: **A40 48 GB a 0,44 $/h es un 55,6 % más barata que la L40S en el mismo tier Secure**, conservando los 48 GB, arquitectura Ampere (sm_86: **tiene BF16 y tensor cores**, a diferencia de la Pascal local) y sin bajar a Community. RTX A6000 48 GB a 0,53 da −46,5 % con las mismas propiedades. **(4)** L4 24 GB a 0,49 es una trampa: más cara que la A40 de 48 GB y es una tarjeta de 72 W, muy inferior en throughput. **Descartarla.** **(5) Sensibilidad** (⚠️ el s/pista **no está medido**: falta el shim): la A40 sigue siendo más barata por pista que la L40S mientras sea **menos de 2,25× más lenta**; a 1,3× el coste/pista es el 58 % del de la L40S; a 1,8×, el 80 %. Dado el ratio de ancho de banda de memoria, 1,3–1,8× es el rango plausible, ⚠️ **pero no verificado**. **(6)** Recálculo de la opción G con A40: 176 × 0,44 = **71,24 €/mes** frente a 160,30 €/mes en L40S Secure.

**(c) RECOMENDACIÓN.** **(a)** Cerrar I-14 con la formulación **corregida**: la pregunta útil no es «¿cuánto cuesta una GPU de 24 GB?» sino «**¿cuál es la tarjeta más barata que cabe el modelo con holgura?**», y la respuesta hoy es **A40 48 GB a 0,44 $/h en Secure Cloud**, no una tarjeta de 24 GB. **(b)** Sustituir la opción H de `evaluation.md` §6.2 (hoy con precio «⚠️ verificar») por una fila con los siete precios verificados **y la advertencia de causalidad tier-vs-VRAM**. **(c) No cambiar la tarjeta de referencia todavía**: la elección definitiva exige el s/pista de S-02, que no existe. Dejar escrito el criterio de elección para que en F6 se decida con el dato en la mano y no por defecto. **(d)** Añadir la A40 y la A6000 como candidatas explícitas a medir en `T-04`/`T-09`, ya que hoy solo se contempla la L40S. **(e) Coherencia con B-08/B-09**: si se adopta A40 + postura F/B en vez de L40S + postura G, el coste de producción a volumen personal pasa de ~128–160 €/mes a **unos pocos euros al mes** — **un factor mayor que cualquier ahorro discutido en el resto de este registro**.

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna hoy: la elección de tarjeta se ejecuta en F6 y no gasta nada en F2. El coste de no anotarlo es el **sobrecoste por inercia**: si en F6 se despliega la L40S porque es lo que dice el documento, se paga **0,55 $/h de más (55,6 %) durante toda la vida del despliegue**. En la postura G eso son 89 €/mes = **1.068 €/año**; en la postura B a volumen personal, 2,54 €/mes = 30 €/año. **La magnitud del error depende enteramente de qué se decida en B-09, lo que refuerza que B-09 y B-10 deben cerrarse juntas.**

**(e) QUIÉN FIRMA.** ⚙️ **Agente** para la corrección de la tabla y el cierre de I-14 con dato verificado. 🔒 La **elección definitiva de tarjeta** en F6 es del propietario, porque es gasto.

---

### B-11 · CS-16 / I-08 — Storage y egress: a escala personal la partida entera son 5–21 € en 24 meses

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** F4/F6; en F2 el coste es 0 € si no se despliega

**(a) CRITERIO.** Una partida de coste merece modelado detallado **solo** si su magnitud a 24 meses es comparable al resto de partidas del mismo presupuesto. Si es **dos órdenes de magnitud menor**, la decisión correcta es **eliminar la incógnita por construcción** (elegir un proveedor donde la variable no exista) en vez de medirla. **Regla añadida**: cuando una partida crece de forma acumulativa, lo que hay que controlar no es el precio unitario sino **la política de retención** — el precio se negocia una vez, el volumen se paga para siempre.

**(b) FUNDAMENTO.** ✅ **Cloudflare R2** (`developers.cloudflare.com/r2/pricing/`): Standard **0,015 $/GB-mes**; Infrequent Access 0,010 + 0,01 $/GB de recuperación con mínimo de 30 días; Class A (escrituras) 4,50 $/millón; Class B (lecturas) 0,36 $/millón; **EGRESS: «Free»** en ambas clases; capa gratuita permanente de **10 GB-mes** + 1 M Class A + 10 M Class B. **AWS S3**: ⚠️ las tablas regionales **no renderizan** — el 0,023 $/GB-mes de `evaluation.md` §6.6 queda corroborado **solo por terceros**, se marca como **no verificado en fuente primaria**; ✅ sí verificado en fuente oficial: «The Data Transfer out charge from Amazon S3 in Europe (Ireland) to internet is **$0.09 per GB**» y los primeros 100 GB/mes de salida gratis. ⚠️ **Backblaze B2** ~0,006 $/GB-mes con egress gratis hasta 3× lo almacenado: **solo terceros, no verificado**. ✅ RunPod network volume 0,07 $/GB-mes. **Recálculo a escala personal** con la política ya recomendada en §6.6 (FLAC + stems a demanda) y 100 gen/mes: mes 24 = 1,36 €/mes en S3, 0,89 en R2, 0,36 en B2; **acumulado 24 meses = 17,05 € (S3) / 11,12 € (R2) / 4,45 € (B2)**. Con los 10 GB gratis de R2, los primeros meses son **literalmente 0 €**. Egress a escala personal (~5 GB/mes): **0 €** en los tres. **Contraste con el antipatrón**: 1.000 gen/mes con stems por defecto (245 MB/gen) da **1.518 €** acumulados en 24 meses en S3 — coherente con los 1.555 € de §6.6. Es decir: **el rango entre la mejor y la peor política es 4,45 € vs. 1.518 €, un factor de 341; el rango entre proveedores a escala personal es 12 € en dos años**.

**(c) RECOMENDACIÓN.** **(a)** Cerrar I-08 así: «a escala personal, storage + egress a 24 meses = **entre 5 y 21 € totales**; deja de ser una partida presupuestaria y pasa a ser ruido. **Se reabre solo si el volumen almacenado supera 500 GB**». **(b)** Elegir **Cloudflare R2** como proveedor por defecto, **no por precio sino porque su egress gratuito elimina la variable desconocida**: la incógnita de egress de I-08 desaparece **por construcción** en vez de quedarse en «⚠️ verificar» para siempre; además su capa gratuita cubre los primeros meses a coste cero y **mantiene el invariante de API compatible con S3** del stack (`CLAUDE.md` nombra «S3» como patrón de almacén, no como proveedor). Vigilar la única partida no obvia de R2: Class A a 4,50 $/millón de escrituras. **(c) No tocar ninguna de las seis medidas obligatorias de §6.6** (stems a demanda, FLAC, retención 30/180 días, ciclo de vida a frío, GC de huérfanos, egress instrumentado): la evidencia **refuerza** que el control valioso es la **política** (factor 341), no el precio (factor 3,8). **(d)** Corregir el marcado de fuentes en `evaluation.md` §6.6 y `spec.md`:486: el 0,023 $/GB-mes de S3 **no** está verificado en fuente primaria; el 0,015 de R2 **sí**. **(e)** En Fase 0, con GPU local, **considerar posponer el object storage del todo**: el artefacto y las salidas ya viven en `D:\srv`. El coste en F2 es 0 € si no se despliega.

**(d) CONSECUENCIA DE NO DECIDIR.** **Económica: nula** — ninguna decisión de esta ficha cambia el gasto en más de ~15 € en dos años. La consecuencia real es de **higiene y de atención**: I-08 lleva abierta desde la revisión 1 con prioridad Media, aparece marcada «⚠️ verificar» en **cuatro puntos distintos** (`spec.md`:419, :486, :533 y `evaluation.md` §6.6/§6.7) y consume atención en cada revisión del plan para una partida de 15 €. **El riesgo material no está en el precio sino en el antipatrón**: si los stems se activaran por defecto y nadie lo notara, la partida pasa de 4 € a 1.518 € a 24 meses — por eso **lo que hay que blindar con tests es la política, no la tarifa**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Cierra una incógnita con dato verificado y elige un proveedor equivalente en API sin comprometer gasto material (< 21 € a 24 meses).

---

### B-12 · CS-48 — Los 300 €/mes de la librería de producción son el tier corporativo: el que aplica aquí cuesta 15,25 €/mes

**Estado:** 🔒 pendiente de firma · **Confianza:** media · **Plazo:** antes de que el dato se use en el stop-loss o en GC-01

**(a) CRITERIO.** Al comparar **construir contra comprar**, el precio del comparador debe ser el del **tier que la organización real está obligada a contratar**, no el del tier más caro del catálogo. **Regla de verificación**: identificar el **disparador contractual** que fuerza cada tier (nº de empleados, uso publicitario, exigencia de indemnización por escrito) y aplicar el que corresponda. **Regla de honestidad**: si al corregir un número la conclusión **empeora** para la opción ya elegida, se corrige igual y se declara — corregir solo los números que confirman la decisión es sesgo, no evaluación.

**(b) FUNDAMENTO.** ✅ Precios verificados 2026-09-01 (`cchound.com/artlist/artlist-subscription-plans-and-pricing`, página actualizada 2026-05-14; USD facturado anualmente): **Artlist Music Pro 16,58 $/mes = 15,25 €/mes = 183 €/año**; Music & SFX Pro 24,92 $ = 22,93 €/mes; **Artlist Max 39,99 $ = 36,79 €/mes**; **Artlist Max Business: 399 $/mes = 367,08 €/mes**, y es **el único que incluye indemnización legal por escrito**. ✅ **Disparador contractual** (`help.artlist.io`): Max Business/Enterprise es **obligatorio solo** si se trabaja para una entidad de **más de 50 empleados**, para broadcasters, para publicidad exterior (OOH) o para apps/juegos. ✅ Texto de la indemnización: Artlist «will defend, indemnify and hold the Customer harmless» frente a reclamaciones de terceros por infracción de PI, limitado a uso autorizado y sin alterar. **Consecuencia aritmética**: el supuesto de `evaluation.md` §6.5a (300 €/mes, «⚠️ verificar») **no es incorrecto como proxy del tier corporativo indemnizado** —300 frente a los 367 €/mes verificados es un 18 % bajo—, **pero es incorrecto por un factor de 20 para el tier que aplica a este proyecto**: propietario en solitario, sin empresa de 50+ empleados, sin cliente exigiendo indemnización (`gobernanza.md`; `spec.md`:429 cierra I-18 como «N/A en modo personal»). **Equivalencias recalculadas** con Artlist Music Pro (183 €/año): Fase 1 (39.360 €) = **215 años** de suscripción, no 10,9; Fases 1+2 (47.220 €) = **258 años**, no 13,1; catálogo completo (98.280 €) = **537 años**, no 27,3. Con Artlist Max (441 €/año): 89 / 107 / 223 años. Con Max Business (4.405 €/año): 8,9 / 10,7 / 22,3 años — **que es donde encajan casi exactamente las cifras del documento actual, confirmando que §6.5a coticó el tier corporativo**. ⚠️ **No verificable hoy**: Epidemic Sound (`epidemicsound.com/pricing` devuelve el bloque de planes vacío, precios renderizados por JS; solo consta que Creator/Pro/Enterprise existen y que la publicidad está limitada a Pro y Enterprise); Musicbed (cifras de terceros contradictorias: 29,99 $ de entrada vs. 16,99 $/mes vs. 120 $/año). ⚠️ Conflicto menor declarado: una segunda fuente da Artlist Max a 50,66 $/mes en vez de 39,99 $.

**(c) RECOMENDACIÓN.** **(a)** Corregir `evaluation.md` §6.5a sustituyendo el «300 €/mes ⚠️ verificar» por la **escala verificada de tres tiers** (personal 15,25 / completo 36,79 / corporativo indemnizado 367,08 €/mes), con el disparador contractual de cada uno citado, y recalcular las tres equivalencias. Es corrección de dato, no de criterio. **(b)** Declararlo en el changelog: la comparación construir-vs-comprar del brief estaba usando el **comparador corporativo**, lo que hacía parecer barato construir. Con el comparador correcto, comprar en modo personal cuesta **183 €/año** frente a **656 horas de vida del propietario**. **Corregirlo empeora la posición económica de construir, y por eso hay que corregirlo.** **(c) Lo que esto NO hace**: no reabre la decisión de construir. ✅ `gobernanza.md` §4 (CS-07, cerrado el 2026-09-01) ya documentó «construir» sobre bases **explícitamente no económicas** — aprendizaje, control total, self-hosting. Esa justificación sigue intacta y no depende del precio de Artlist; de hecho **es más honesta cuando el número está bien, porque deja de fingir un caso económico que no existe**. **(d)** La comparación que sí es válida en modo personal y que hoy **no está en ningún documento**: comprar = **183 €/año de caja y 0 horas**; construir = entre ~40 y ~200 €/año de caja (GPU bajo demanda + storage + electricidad, todo verificado en este registro) **más 656 horas de esfuerzo** y el OPEX de mantenimiento indefinido. **En caja las dos opciones son comparables; la diferencia entera son las 656 horas.** Esa es la frase que debería estar en el `decision-brief.md`, y hoy no está. **(e)** Marcar Epidemic Sound y Musicbed como **no verificados** en vez de citarlos con cifras de terceros.

**(d) CONSECUENCIA DE NO DECIDIR.** `decision-brief.md` y `evaluation.md` §6.5a seguirán afirmando que el catálogo completo «equivale a ~27 años de suscripción» cuando la cifra correcta para este proyecto es **~537 años**. No bloquea ninguna tarea ni gasta un euro, pero **es la clase de error que envenena una decisión futura**: si en algún momento se convoca el stop-loss (D-28) o el gate GC-01, la pregunta «¿qué habríamos pagado por comprar en su lugar?» se contestará con un número **20 veces inflado**, y eso sesga la decisión de parar hacia **seguir**. Coste del retraso: cero hoy y potencialmente el proyecto entero el día que se use el dato para decidir si continuar.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Corrige una cifra del `decision-brief.md` ya ratificado y toca el material de una decisión de continuidad.
---

> **Nota de conjunto sobre B-13…B-17.** Las cinco fichas siguientes cierran las dos condiciones de licencia del **gate compuesto de F10 sub-fase 2** (I-13b separación en stems, I-13 watermarking). F10 está `bloqueada (gate)`, así que **el retraso hoy cuesta 0 € directos**; lo que se decide aquí es si esas 131 h (7.860 € con margen) se desbloquean con una premisa verdadera o con una falsa.

### B-13 · CS-22 / I-13b (raíz) — La causa raíz no es Demucs: es MUSDB18

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** F10 · *(reclasificada de ⚙️ a 🔒 el 2026-09-01, ver apartado (e))*

**(a) CRITERIO.** Un checkpoint es admisible para C-06 **solo si supera los TRES ejes**: **L1** — *grant* explícito sobre el artefacto de **PESOS**, emitido por quien lo entrenó (no vale «el LICENSE del repo es MIT» si ese LICENSE habla del **código**; no vale un re-upload de terceros); **L2** — dataset de entrenamiento **sin término no comercial**, o dictamen escrito de que la NC no se propaga; **L3** — formato **safetensors** (o, en su defecto, **ONNX**), **sin excepciones**. El invariante se cita tal cual está: `CLAUDE.md`:50 — «**Solo `safetensors`** — jamás `pickle`/`torch.load` sobre checkpoints no confiables (es RCE). `weights_sha256` verifica integridad, no inocuidad», reiterado como decisión de diseño en `spec.md`:69 (D-14). **No existe en el proyecto la figura de «excepción documentada con mitigación» para este eje**, y este registro no la crea.

**(b) FUNDAMENTO.** ✅ `facebookresearch/demucs` issue **#327**, adefossez (autor), 2022-05-23, literal: «**The model weights are not covered by the MIT license, they are provided only for scientific purposes.**» Motivo dado por CarlGao4 (2024-06-09): «models are trained using the **MusDB dataset**, which requires the result model be only used for research purpose». ✅ Verificado por API de Zenodo: **MUSDB18-HQ (record 3338373)** y **MUSDB18 (record 1117372)** tienen `license.id = 'other-nc'`. **Consecuencia**: todo separador entrenado sobre MUSDB18 **hereda el problema tenga la licencia de pesos que tenga**. **Segundo bloqueo independiente**: todos los checkpoints del ecosistema son `.ckpt`/`.pth`/`.th` = **pickle de torch**, lo que choca con el invariante de `CLAUDE.md`; **única excepción encontrada: MDX-Net, que distribuye ONNX**.

**(c) RECOMENDACIÓN.** Registrar el **criterio de tres ejes** como regla del registry (extensión de la regla 5) y aplicarlo a todo candidato **antes** de integrarlo. Para **L3 no hay procedimiento de excepción que inventar: la vía ya existe, está escrita y ya se ha usado en este proyecto.** Si un candidato distribuye los pesos en `.ckpt`/`.pth`/`.th`, se convierten a `safetensors` con el **auditor de opcodes** de `apps/runner/tools/build_artifact.py` (§«Sección 2 — conversión segura del pickle en cuarentena»), que **no llama nunca** a `pickle.load`, `torch.load`, `joblib`, `dill` ni `np.load(allow_pickle=True)`: desensambla el flujo con `pickletools.genops` —un **parser**, no un intérprete— y aplica cuatro capas: lista blanca **de opcodes inertes** (no de GLOBALs) con denegación explícita de los letales, cotas de recuento sobre los tres opcodes que pueden referenciar un callable (`GLOBAL`/`STACK_GLOBAL`, `BINPERSID`, `REDUCE`), un mini-intérprete inerte que hace *pattern matching* en `REDUCE` en vez de invocar nada, y validación semántica del tensor con SHA-256 del almacén. Rechaza con `PickleRechazado`. **Precedente real, ya ejecutado:** así se trató el `silence_latent.pt` del artefacto de ACE-Step; no es un diseño sobre el papel. Reglas de la conversión: el fichero original **queda en cuarentena fuera del volumen** que monta el runner y no se carga jamás, **solo el `safetensors` resultante** entra en el registry, y la conversión con su SHA-256 se registra en el manifiesto. Esto se añade al `pre-dev-checklist.md` **como procedimiento de conversión sin ejecución**, no como excepción al invariante. **Y si un candidato solo distribuye pesos en formato pickle y no se puede convertir por esta vía** —porque el flujo exige opcodes letales o `REDUCE` sobre formas no admitidas—, la conclusión correcta es **descartarlo, o escalarlo como decisión del propietario (🔒) junto con B-14/B-15**; nunca abrir una excepción al invariante.

**(d) CONSECUENCIA DE NO DECIDIR.** Sin criterio explícito **se repite el error del 2026-08-18**: se elige por SDR y se descubre la licencia después. Y **el coste del pickle no está presupuestado en ninguna tarea de F10** (`T-60` son 12 h y no contempla conversión ni cuarentena).

**(e) QUIÉN FIRMA.** 🔒 **Propietario** *(reclasificada de ⚙️ a 🔒 el 2026-09-01)*. La formalización del criterio de tres ejes se deriva de invariantes ya escritos y, por sí sola, sería de agente. Pero al retirar del eje **L3** la coletilla «o excepción documentada con mitigación» —que no existe en `CLAUDE.md`:50— la ficha deja de ser neutra en alcance: combinada con **B-14** (ningún separador del mercado pasa los tres ejes), el criterio implica **descartar candidatos** para C-06 y, en el límite, dejar la separación en stems **sin ninguna opción integrable** hasta que **B-15** resuelva la pregunta jurídica. Eso es una decisión de alcance y de licencia, y la firma el propietario.

---

### B-14 · CS-22 / I-13b (matriz) — Ningún separador pasa los tres ejes: la correlación entre SDR y limpieza de licencia es perfecta e inversa

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** F10 — **pero la corrección de `tasks.md`:1512 es hoy**

**(a) CRITERIO.** Verificar la licencia de **PESOS** contra el registro del host que los publica (Zenodo / HuggingFace / GitHub releases), **no** contra el README del repo de código; y verificar **el dataset por separado**.

**(b) FUNDAMENTO.** ✅ Verificado el 2026-09-01 vía API:

| Candidato | L1 · grant de pesos | L2 · dataset | L3 · formato | Veredicto |
|---|---|---|---|---|
| **Demucs / htdemucs** | ❌ sin grant (#327); código MIT (fork vivo `adefossez/demucs`, push 2026-08-31) | ❌ MUSDB18-HQ | ❌ `.th` | **falla L1+L2+L3** |
| **Open-Unmix `umxl`** | ❌ Zenodo 5069601 = CC-BY-NC-SA-4.0; README:86 «the weights are only licensed for non-commercial use» | ❌ | ❌ `.pth` | **falla** |
| **Open-Unmix `umxhq`/`umx`** | ✅ Zenodo 3370489 / 3370486 = **MIT** | ❌ MUSDB18-HQ / MUSDB18 | ❌ `.pth` | **falla L2+L3** |
| **Banquet** | ❌ Zenodo 13694558 = CC-BY-NC-SA-4.0 | ❌ MoisesDB (CC-BY-NC-SA-4.0) | — | **falla** (su README afirma «released under permissive licenses»: **afirmación refutada**) |
| **Bandit v2** | ✅ Zenodo 12701995 = CC-BY-SA-4.0 | ✅ DnR (Zenodo 5574713 = CC-BY-4.0; LibriSpeech+FMA+FSD50K) | — | **tarea equivocada**: voz/música/efectos, no VDBO |
| **KUIELab-MDX-Net** | ✅ Zenodo 5717356 = **CC-BY-4.0** | ❌ Leaderboard A del MDX Challenge 2021 permite entrenar «exclusively on the training part of MUSDB18-HQ» | ✅ **ONNX** (`onnx_A.zip` + `mixer.ckpt`) | **falla solo L2** |
| **UVR** | ⚠️ *grant por declaración de autor*: README `Anjok07/ultimatevocalremovergui`:271-273 «The UVR GUI code is MIT-licensed. Please Note: if all third-party application developers wish to use our models, please honor the MIT license by providing credit…» **pero** `TRvlvr/model_repo` **no tiene fichero LICENSE** (API GitHub: `license=null`) | ⚠️ datos de entrenamiento **no declarados** | — | **indeterminado** |
| **SCNet XL / BS-RoFormer / Mel-Band (MSST)** | ❌ `ZFTurbo/Music-Source-Separation-Training` LICENSE MIT cubre el **código**; **ninguna licencia de pesos en ningún sitio** | ❌ `docs/pretrained_models.md`: «Trained on MUSDB18HQ dataset (100 songs in train data)» | ❌ | **falla** |
| **Spleeter** | ✅ LICENSE MIT (Deezer SA) — ⚠️ acotado a código en el README:114; issue #898 abierto desde 2024-04-26, re-preguntado 2026-05-26, **sin respuesta** | ✅ `paper.md`:52 «The models were trained on **Deezer internal datasets** (noteworthily the Bean dataset)», **NO MUSDB** | ✅ TF checkpoint (protobuf, **no pickle de Python**) | **único superviviente si L2 es estricto** |

✅ El paper de MSST (arXiv 2607.23395), consultado, **no dice nada de licencias de pesos**. **SDR (fuentes propias)**: Spleeter MWF voz 6,86 / bajo 5,51 / batería 6,71 / otros 4,55 = **5,91 avg** (`paper.md` de Spleeter); SCNet XL IHF **10,08 avg** MUSDB (MSST). ❌ **La nota de `tasks.md`:1512 —«MDX-Net (UVR5) / Mel-Band RoFormer con pesos MIT verificados»— es INCORRECTA** y hay que retirarla.

**(c) RECOMENDACIÓN.** **(1)** Retirar de `tasks.md`:1512 la afirmación no verificada. **(2)** Reescribir `T-59` de «ficha de licencia de los pesos de Demucs» a «**ficha de licencia del separador seleccionado**», usando esta matriz como **entregable ya hecho** (ahorra ~4 de sus 5 h). **(3) Nota crítica**: **la rama «o hay que licenciar» del enunciado original NO EXISTE** — no hay oferta de licencia comercial de los pesos de Demucs por parte de Meta, ni contacto de licenciamiento, ni declaración posterior a #327 en ninguno de los dos repos.

**(d) CONSECUENCIA DE NO DECIDIR.** Se mantiene en el ledger **una afirmación falsa** que, si alguien la ejecuta, **mete pesos sin licencia en el pipeline y contamina el manifiesto de procedencia** — el invariante nº 2 del proyecto.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Retira una afirmación no verificada y reescribe el enunciado de una tarea `bloqueada (gate)`, sin cambiar sus horas.

---

### B-15 · CS-22 / I-13b (bifurcación J-1) — La elección de separador depende de una pregunta jurídica, no de una comparación técnica

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** F10 (gate compuesto sub-fase 2)

**(a) CRITERIO.** Cuando dos candidatos difieren **solo en un eje** y ese eje es **una cuestión de derecho no resuelta**, no se elige técnicamente: **se formula la pregunta y se pre-acuerda la matriz de resultados** (mismo patrón que G2 / `T-01`).

**(b) FUNDAMENTO.** **Pregunta J-1**: «¿La cláusula no comercial de la licencia de un **dataset de entrenamiento** se propaga a los **pesos** del modelo entrenado con él, y de ahí a las **salidas**?». **Si J-1 = NO se propaga** → **KUIELab-MDX-Net** (Zenodo 5717356) es el único candidato con grant explícito, comercial y emitido por los propios entrenadores (CC-BY-4.0), en **ONNX** (cumple L3 sin excepción), SDR ~7,2 > Spleeter 5,91. **Si J-1 = SÍ se propaga** → **Spleeter es el único superviviente del mercado entero** (ver matriz en B-14); su único defecto es documental, y ⚠️ el issue #898 sigue **sin respuesta del mantenedor**.

**(c) RECOMENDACIÓN.** **(1)** Acumular J-1 al **lote de GC-01 §8**, junto a I-05 e I-05b — ⚠️ **corrección respecto de la propuesta original**, que hablaba de «mandarla al mismo canal legal de G2»: **en modo solo ese canal no existe** (G2 se cerró con respuesta informal del propietario). Ver **X-4**. El `MANIFEST.json` en disco ya contempla «tercera pregunta candidata para el lote de G2», así que la trazabilidad se conserva. **(2)** En paralelo y **a coste cero**, mandar la pregunta a Deezer / comentar en el issue #898 para cerrar la ambigüedad de Spleeter (~2 semanas de espera, 0 €). **(3) Restricción de integración si sale MDX-Net**: usar **solo** los ONNX por stem de `onnx_A.zip` + `mixer.ckpt`; **NO ejecutar `python download_demucs.py`**, que el README de la rama `leaderboard_A` incluye en la instalación y que **re-introduce los pesos contaminados de Demucs por la puerta de atrás**. **(4)** Mientras J-1 no tenga dictamen, rige la **rama conservadora** (se asume propagación): ningún modelo entrenado sobre MUSDB18 entra en el pipeline.

**(d) CONSECUENCIA DE NO DECIDIR.** I-13b bloquea el **gate compuesto de F10 sub-fase 2 COMPLETA** (C-10b + C-06 + C-05: **131 h = 6.550 € base / 7.860 € con margen**), no solo `T-59`+`T-60` (17 h = 850/1.020 €), y en cascada `T-61`. Como F10 ya está bloqueada por gate, **el retraso hoy cuesta 0 € directos**; pero si J-1 se resuelve tarde y la respuesta es «sí se propaga», **Spleeter obliga a rehacer las expectativas de calidad de C-06 en `spec.md`, y eso sí se paga**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Es una consulta legal y una condición de un gate.

---

### B-16 · CS-22 / I-13b (opción cero) — No integrar ningún separador externo: ACE-Step declara capacidad `Extract` nativa

**Estado:** ⚙️ lista para ejecutar · **Confianza:** media · **Plazo:** al **entrar** en F10, no ahora

**(a) CRITERIO.** Antes de añadir **superficie de licencia nueva**, comprobar si el modelo que **ya está en el pipeline** cubre el requisito. **Superficie de licencia nueva = 0 gana a cualquier SDR.**

**(b) FUNDAMENTO.** ✅ El model card de `ACE-Step/Ace-Step1.5` lista, en su tabla de DiT Models, las capacidades **`Extract`** y **`Lego`** para `acestep-v15-base` (la variante `acestep-v15-turbo` que usa el proyecto las tiene a **No**). ✅ El README de `github.com/ace-step/ACE-Step` describe además **StemGen**: «controlnet-lora trained on multi-track data to generate individual instrument stems», y **Singing2Accompaniment**. Todo ello es **MIT** y con datos ya declarados. ⚠️ **Incertidumbre declarada, no rellenada con plausibilidad**: **ninguna** de las fuentes leídas define **qué hace `Extract`** — podría ser extracción de stems o extracción de estilo/melodía. **No se puede saber hoy y no es medible hoy**: falta el shim `ace_step_shim.py`, `acestep-v15-base` es 50 pasos con CFG (~2× el cómputo del turbo de 8 pasos) y la GPU es una GTX 1070 de 8 GB (8191 MiB reales, por debajo del `VRAM_FLOOR_MB` — ver A-01).

**(c) RECOMENDACIÓN.** Añadir a `T-60` una **subtarea previa**: spike de **2 h**, «qué hace `Extract` en `acestep-v15-base`», **a ejecutar al entrar en F10** (no ahora), **antes** de tocar `T-59`/`T-60`. Si `Extract` hace separación de stems, **C-06 se resuelve dentro del modelo que ya está en el pipeline y `T-59`/`T-60` desaparecen enteros**.

**(d) CONSECUENCIA DE NO DECIDIR.** Se arriesga gastar **17 h (850 € base / 1.020 € con margen)** integrando un separador de terceros con licencia discutible para una función que **quizá el modelo propio ya da gratis y con licencia limpia**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Añade una subtarea de investigación dentro de una tarea existente, sin ampliar el alcance ni el presupuesto.

---

### B-17 · CS-18 / I-13 — Watermarking: no merece la pena hoy

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** F10 (condición del gate compuesto)

**(a) CRITERIO.** Un control de seguridad **solo se construye si supera los cuatro**: **(i)** mitiga una amenaza real de **este** despliegue; **(ii)** código **y pesos** comercialmente limpios; **(iii)** sobrevive a las transformaciones que el producto realmente aplica (MP3 320, 44,1/48 kHz, **música**); **(iv)** su coste es menor que el del riesgo que elimina. **Un control que falla (i) no se construye aunque pase (ii) y (iii).**

**(b) FUNDAMENTO.** ✅ **AudioSeal (Meta)**: código MIT y **pesos MIT explícitos** — README changelog 2024-04-02, literal: «updated our license to **full MIT license (including license of model weights)**! Now you can use AudioSeal in commercial applications too!»; HF `facebook/audioseal` `cardData.license='mit'`. **PERO es de VOZ**: arXiv 2401.17264 se titula «**Proactive Detection of Voice Cloning** with Localized Watermarking», resolución 1/16.000 s = **16 kHz nativo**; y sus pesos son `generator_base.pth` / `detector_base.pth` / `audioseal_encodec_32khz.th` = **PICKLE** (choca con el invariante de `CLAUDE.md`). ✅ **SilentCipher (Sony)**: **dominio correcto** (44,1 kHz nativo, capas de compresión pseudo-diferenciables, Interspeech 2024, arXiv 2406.03822) **pero SIN grant sobre los pesos** — README §License: «The **code** in this repository is released under the MIT license» (acotado a código) y HF `Sony/SilentCipher` tiene `cardData=null` y **cero etiquetas de licencia**; ficheros `.ckpt` (pickle). ✅ **audiowmark**: **GPL-3.0** (API GitHub) → copyleft, descartado. ⚠️ **Robustez MP3 — evidencia de TERCEROS, marcada como tal y no verificada de primera mano**: AudioMarkBench (NeurIPS 2024 D&B) sitúa a AudioSeal como el más robusto de los tres open source evaluados, con MP3 entre sus fuertes, y documenta fallos en Opus, AAC, paso-alto y colapso a azar (~0,574) frente a códecs neuronales — **toda esa evidencia es sobre voz**. ⚠️ **Se buscó y NO EXISTE** un benchmark 2026 que cruce dominio musical + robustez MP3 + filtrado por licencia. **Sobre (i)**: despliegue personal self-hosted de un único propietario, **sin terceros subiendo contenido**, sin responsabilidad de plataforma y sin obligación regulatoria invocada en la documentación; y el proyecto **ya tiene un mecanismo de procedencia más fuerte y más barato** (manifiesto append-only con cadena de hashes, invariante desde la primera pista, + C2PA en `T-58`) que **además no toca la señal de audio** — nada menor en un proyecto cuyo gate G1 es escucha ciega con umbral 4/5.

**(c) RECOMENDACIÓN.** **Degradar `T-57`**: quitar el criterio de aceptación «Toda pista generada lleva watermark, verificado como invariante en CI» y **re-anclar la parte obligatoria de C-10b en manifiesto + C2PA** (`T-54`/`T-56`/`T-58`). Dejar `T-57` como **capacidad activable (opt-in)**. **Matiz que cambia quién decide**: la válvula de escape ya pre-acordada en `T-57` («Si no hay librería con licencia comercial limpia disponible… el invariante se replanifica») **NO se activa, porque AudioSeal sí es limpio**; el motivo para no hacerlo es **idoneidad y coste/beneficio** (watermarker de voz a 16 kHz sobre música a 44,1 kHz en FLAC/MP3-320), no licencia. **Por eso no cae en lo pre-autorizado** — ver **X-9**. Si en el futuro se activa (GC-01, comercialización o exigencia regulatoria), **AudioSeal es el único candidato**, y antes de integrarlo hay que **medir su robustez sobre música real a 44,1 kHz pasada por el codificador MP3-320 del propio proyecto** — no fiarse de las cifras del paper, que son de voz. Presupuestar ese ensayo en **~4 h**.

**(d) CONSECUENCIA DE NO DECIDIR.** `T-57` son **20 h = 1.000 € base / 1.200 € con margen** hoy reservadas para integrar **un watermarker de voz sobre música**. Peor: I-13 es una de las cuatro condiciones del gate compuesto de F10, así que **mantenerla artificialmente abierta bloquea las 131 h de la sub-fase 2 completa**. **Cerrarla con un «no, y por estas razones» desbloquea más de lo que cuesta.**

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Degrada un criterio de aceptación y cambia el alcance de `T-57`, sin caer en el supuesto pre-autorizado.

---

### B-18 · CS-47 — Audio de entrada para C-08: son dos límites, no uno; y falta el encoder del VAE

**Estado:** ⚙️ lista para ejecutar · **Confianza:** media · **Plazo:** antes de F11 (checklist: «antes de Fase 3»)

**(a) CRITERIO.** El límite se fija **por el recurso que primero se agota**, se publica junto a la aritmética que lo produce y la medición que lo confirmaría, y **mientras esa medición no exista se elige el valor que NO puede fallar**, no el que probablemente funcione. **Segundo criterio, específico de covers**: si la longitud de salida está atada a la de entrada, el límite de entrada y el de salida deben ser **el mismo número**, o la UI promete algo que el backend no puede entregar.

**(b) FUNDAMENTO.** Aritmética derivada de los configs locales, no de memoria. **(1)** ✅ Tasa del latente = **25 Hz**, verificada por dos caminos: `vae/config.json` `downsampling_ratios [2,4,4,6,10]` → producto 1920 y `sampling_rate 48000` → 48000/1920 = 25; y `modeling_acestep_v15_turbo.py:2010-2012` («25 Hz hidden states → 10 s = 250 frames»). **(2)** ✅ `patch_size: 2` → tokens DiT = `s × 12,5`; **180 s → 4.500 frames → 2.250 tokens**, que **coincide al dígito** con la cifra que arrastra el plan: la aritmética queda validada. **(3)** ✅ **Techo duro del modelo = 600 s**: el *silence latent* tiene shape `[1, 64, 15000]` → 15.000/25 = 600 s, coherente con el «10-minute compositions» del README. Por encima **no hay latente de silencio y el camino text2music aborta**. **(4)** Por qué el techo cae cerca de 240 s en 8 GB: 12 de las 24 capas son `full_attention` y 12 `sliding_attention` con `sliding_window: 128`; matriz de atención fp16 de **una** capa full: 180 s → 162 MB · 240 s → 288 MB · 300 s → 450 MB · 600 s → 1,8 GB (crece con T²). **Pero el término dominante no es la atención: es el decoder del VAE**, que sube 64 ch@25 Hz a 2 ch@48 kHz; su nivel más fino (24 kHz × 128 canales) cuesta ~6,1 MB por segundo de audio y por copia → decodificar de una pasada 180 s son **~2,2–4,4 GB** y 240 s **~3,0–5,9 GB** de activaciones fp16. Sobre una tarjeta de 8.191 MiB donde el artefacto ya ocupa **5.878 MiB**, quedan ~2.313 MiB antes del contexto CUDA: **por eso el offloading es obligatorio (I-21) y por eso ~240 s es plausible como techo de una pasada**. **(5) Consecuencia clave, y es la que cambia la decisión**: **~240 s no es una propiedad del modelo, es una propiedad de la implementación**. Si el shim decodifica el VAE **por bloques con solape** (trivial y estándar), ese muro desaparece y el límite vuelve a marcarlo la atención del DiT. **Comprometer 240 s hoy es congelar un número que depende de código que todavía no existe.** **(6) Lo que de verdad bloquea C-08 y no está en ningún sitio del plan**: ✅ el artefacto **no tiene encoder del VAE** — `ace_step_1_5.provenance.json`: `"vae_encoder_included": false` y la nota «Este artefacto NO incluye el encoder del VAE (183 tensores, 161 MiB)». **Sin encoder no hay forma de convertir audio de entrada en latentes.** Y el camino cover lo exige: `modeling:1646` `src_latents = torch.where(is_covers > 0, lm_hints_25Hz, src_latents)` y `modeling:1867` `latent_length = src_latents.shape[1]` — es decir, **la longitud de salida de un cover es exactamente la de la entrada**: no existe «subo 5 minutos y genero 30 s». **(7) El otro límite, ese sí fijado por arquitectura**: ✅ `timbre_fix_frame: 750` y el arnés usa `refer_audio_acoustic_hidden_states_packed` de forma `(3, 750, 64)` (`modeling:2008`) → **750/25 = 30 s exactos por audio de referencia de timbre**. Ese número no se negocia.

**(c) RECOMENDACIÓN.** Escribir en `spec.md` §12.1 **tres líneas** donde hoy hay un «⚠️ definir en C-08»: **(a) Audio de referencia de timbre: 30 s**, fijo por arquitectura (`timbre_fix_frame=750`); lo que exceda se recorta en servidor y se avisa en la UI, **no se rechaza el fichero**. **(b) Audio de entrada para cover/remezcla (C-08): 180 s provisional**, máximo configurable 300 s, techo infranqueable 600 s. Se elige 180 y no 240 **por el segundo criterio**: la salida de un cover mide lo que mide la entrada, así que el límite de entrada debe ser **el mismo** que el «180 s por defecto» de pista generada que la spec ya ratifica; además no abre una discusión nueva. **(c) Validación del endpoint**: tope de subida **100 MB** (180 s de WAV 48 kHz/24 bit estéreo ≈ 62 MB; FLAC ≈ 35 MB) y **validar la duración DESPUÉS de decodificar, nunca por tamaño de fichero** — un MP3 de 10 MB pueden ser 40 minutos. Rechazo con **413/422 antes de tocar la GPU**. Y **dos añadidos al plan de F11 sin los cuales C-08 no arranca**: **(d)** tarea previa de **reconstruir el artefacto incluyendo el encoder del VAE** (183 tensores, 161 MiB) — el fusor ya existe, es reejecutarlo con otro alcance, **pero cambia el SHA-256 del artefacto y por tanto el `weights_sha256` del manifiesto**; **(e)** marcar la dependencia de `T-07`: `improvement-plan.md`:340 ya dice que si la matriz de capacidades no confirma `AUDIO_TO_AUDIO`, «C-07 y C-08 se replantean o se caen antes de gastar estas 220 h». **Revisión del número**: `T-03` (VRAM pico medida) y la decisión de implementar o no decodificación del VAE por bloques. **El 180 s es un valor de planificación, no un compromiso.**

**(d) CONSECUENCIA DE NO DECIDIR.** Hoy, ninguna: F11 está bloqueada por G3. **El daño aparece si se llega a F11 sin esto**: C-08 son **80 h base / 96 h con margen / 4.800 €** (`improvement-plan.md`:345, `T-75`…`T-79`) que arrancarían **sin contrato de entrada**. El escenario es predecible: se implementa la validación con un número inventado, se descubre en integración que **el encoder del VAE no está en el artefacto**, hay que reconstruirlo, **cambia el hash y con él el manifiesto**, y se rediseña el endpoint porque la salida resulta estar atada a la entrada. Coste realista del descubrimiento tardío: **8–16 h = 400–800 €**, más el retrabajo del manifiesto de procedencia, **que es invariante innegociable y no admite chapuzas**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente** para escribir los límites y la validación como valores de planificación provisionales, y para añadir las dos dependencias al plan. 🔒 Si el 180 s se quisiera fijar como **compromiso de producto** en `spec.md` §12.1, eso es alcance y lo firma el propietario.

---

### B-19 · CS-01 — Diferimiento bien fundado: el informe escrito de legal (I-05) no bloquea construir

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** GC-01

**(a) CRITERIO.** Una obligación documental **solo bloquea el build** si alguna tarea del build no puede ejecutarse ni verificarse sin ella. Si su única función es **soportar un compromiso frente a terceros**, su plazo natural es el gate que introduce a esos terceros.

**(b) FUNDAMENTO.** ✅ G2 quedó cerrado el 2026-08-18 por la fila 1 («sí total») de `g2-matriz-resultados.md` §10, y su banner registra explícitamente la deuda: **la respuesta se dio de forma informal por el propietario**. `gobernanza.md` §8a reagrupa esa deuda en GC-01. ✅ **Ninguna tarea de F2–F9 en `tasks.md` tiene a CS-01 como dependencia.** El riesgo que cubre (procedencia del corpus de entrenamiento de ACE-Step) es **de exposición frente a terceros, no de ejecución**: en ámbito estrictamente personal no hay tercero que reclame.

**(c) RECOMENDACIÓN.** **Confirmar el diferimiento tal cual está.** Una sola mejora, gratis: **anotar en GC-01 §8a el presupuesto ya reservado** (32 h de asesoría jurídica, `g2-matriz-resultados.md` §1) para que la consulta **no se descubra como coste nuevo** el día que se decida comercializar. Ahí es también donde se acumula **J-1** (ver B-15 y **X-4**).

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna antes de GC-01. Después: cualquier uso comercial o con terceros se haría sobre **una posición legal que nunca fue escrita por un profesional**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Confirma un diferimiento ya acordado y añade una anotación de trazabilidad.

---

### B-20 · CS-02 — Diferimiento bien fundado: I-05b (protegibilidad y exclusividad del output) no bloquea construir

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** GC-01

**(a) CRITERIO.** Igual que B-19: la pregunta condiciona **lo que se puede PROMETER**, no lo que se puede construir.

**(b) FUNDAMENTO.** ✅ `g2-matriz-resultados.md` §10 lo dice literalmente: «**No bloquea el build; determina qué se puede prometer contractualmente a un cliente**». ✅ `gobernanza.md` §8b lo sitúa en GC-01 con la coletilla correcta: «sin ella, no prometer exclusividad a ningún cliente». ✅ Ninguna tarea de `tasks.md` depende de CS-02.

**(c) RECOMENDACIÓN.** Confirmar el diferimiento. Añadir en GC-01 §8b **una regla operativa de una línea que hoy no está**: mientras I-05b siga abierta, **no se firma ningún compromiso de exclusividad ni de cesión en exclusiva sobre ninguna pista generada, ni siquiera de forma verbal o gratuita**.

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna antes de GC-01. El único escenario de daño es **prometer exclusividad sobre una obra que puede no ser protegible** — que es precisamente lo que la regla propuesta impide por escrito.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Confirma un diferimiento y añade una regla defensiva que no compromete nada.

---

### B-21 · CS-03 — ToS de Suno: diferimiento formalmente correcto, pero más arriesgado de lo que sugiere «uso personal»

**Estado:** 🔒 pendiente de firma · **Confianza:** media · **Plazo:** GC-01 — **pero la exposición se elimina hoy con A-19**

**(a) CRITERIO.** Un diferimiento de una verificación legal es aceptable si **el uso que se hace mientras tanto queda dentro del supuesto que justifica el diferimiento**. Si el uso real **excede** ese supuesto, el diferimiento hay que **rehacerlo, no ampliarlo**.

**(b) FUNDAMENTO.** El supuesto declarado es «**uso estrictamente personal**» (`gobernanza.md` §2.2 nota final; `g1-protocolo.md` §10.4a). Pero el uso real es **usar la salida de un servicio comercial como línea base para evaluar un producto** que `CLAUDE.md` describe como «equivalente funcional a Suno» y sobre el que el mismo documento anota «posible comercialización futura». ⚠️ Muchos ToS de servicios de IA generativa incluyen cláusulas de uso no competitivo o de prohibición de *benchmarking*; **no se puede verificar si los de Suno las tienen** — no se ha consultado el documento y **no se cita cláusula**; **esa es exactamente la incertidumbre que CS-03 registra**. Lo que sí es verificable: ✅ `g1-protocolo.md` §5.6 demuestra que **ninguno de los cinco umbrales depende de Suno**, y §10.4d dice que se puede prescindir de esa línea base «**en cualquier momento, incluso el mismo día de la sesión**».

**(c) RECOMENDACIÓN.** Mantener el diferimiento a GC-01 (es correcto: nada del build depende de ello) y, a la vez, **quitar la exposición en lugar de gestionarla**: ejecutar la **variante B** (**A-19**). Con esa elección, CS-03 **deja de tener consecuencia práctica alguna antes de GC-01** y desaparecen §10.4b y §10.4e del protocolo. Si el propietario prefiere usar Suno, entonces la condición §10.4b («no se dice fuera de este repositorio») **debe repetirse en la cabecera de `g1-resultado.md`**, porque en 12 meses nadie recordará que existía.

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna sobre el build ni sobre el calendario. La consecuencia es **de exposición**: cifras comparadas contra Suno atrapadas por una prohibición de uso **indefinida hasta GC-01**, sobre un gate que se reutiliza en G1-bis durante 12 meses (§10.3). **Coste de la alternativa recomendada: cero** — de hecho ahorra 10 generaciones y ~1 h de sesión.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Decide la composición de las líneas base del gate y asume (o elimina) una exposición legal no verificada.
---

## 4. Bloque C — Higiene

> Nada de aquí bloquea ninguna tarea ni cambia un euro de forma material. Está en el registro porque **su coste es recurrente**: cada una de estas filas se vuelve a leer, evaluar y arrastrar en **cada** revisión del expediente. Una lista de cabos sueltos donde algunos son ruido **pierde autoridad**; cuando la lista deja de ser creíble, deja de leerse, y entonces sí se pierden los cabos que importaban.

### C-01 · CS-28 / I-19 — Idiomas de la UI: castellano y solo castellano en F1 **y F2**

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** ninguno duro; la barandilla sí se erosiona con el tiempo

**(a) CRITERIO.** Un *locale* de UI se añade **cuando existe una persona nombrada que no puede usar el actual**. No antes. La i18n se justifica **por audiencia, no por elegancia técnica**. Corolario operativo: mientras la audiencia sea N=1, el trabajo correcto no es traducir, es **garantizar que traducir siga costando lo mismo dentro de un año** (cero cadenas hardcodeadas, formato por `Intl`).

**(b) FUNDAMENTO.** **(1)** ✅ El estado actual ya lo dice y es coherente: `ui-design.md`:456 «Castellano como único locale de F1 (`es`), estructura de claves preparada para `ca`/`en` (I-19)»; `spec.md` §5.3 lista «Idiomas de la UI distintos del castellano (I-19)» como fuera de alcance; `spec.md`:431 clasifica I-19 con criticidad **Baja** y razona que «añadir un idioma es traducir, no refactorizar». **(2)** ✅ La audiencia es **N=1 y su idioma es castellano**: I-01 e I-20 se cerraron el 2026-09-01 con «evaluador único y usuario piloto = el propietario» (`spec.md`:411, :432; `gobernanza.md` §2-§3). Usuarios que necesitan otro locale hoy: **cero**. **No es una estimación, es un censo.** **(3)** ✅ Las barandillas ya son criterio de aceptación, no buenas intenciones: `ui-design.md`:456 exige «`next-intl` desde el primer componente; **ninguna cadena hardcodeada** (criterio de aceptación de C-13), incluidos los mensajes de la tabla de errores, los estados del stepper y los tooltips de fase» y «Fechas y números con `Intl` (`es-ES`), coste en formato `0,04 €`». **(4) Asimetría deliberada con A-08, que conviene dejar escrita para que nadie la «arregle»**: el **inglés** entra en alcance como idioma **cantado** y no como idioma de **interfaz**. No es incoherencia: el idioma cantado es **una capacidad del modelo que hay que medir** (es la mitad de la muestra de G1); el idioma de la interfaz es **una pregunta sobre la audiencia**, y la audiencia es una persona hispanohablante.

**(c) RECOMENDACIÓN.** **(1)** Cerrar I-19 para **F1 y F2** con «solo `es`», no solo para F1 — hoy la spec la deja como «alcance de Fase 2» y eso **la mantiene viva sin motivo**: la audiencia de F2 en modo solo sigue siendo la misma persona. **(2) Convertir la barandilla en algo que falle solo**: añadir al CI un check que **rompa el build ante un literal de texto en JSX/TSX fuera de los ficheros de mensajes**. Sin eso, «ninguna cadena hardcodeada» es una intención que se erosiona en el commit 300; con eso, añadir `en` o `ca` seguirá siendo **traducir**. Coste ~2 h, **dentro de `T-10`** (monorepo y tooling), no una tarea nueva. **(3) Disparadores de reapertura**, para que la decisión sea revisable sin ser discutible: **(a)** GC-01 — cualquier movimiento hacia comercialización (`en` pasaría a ser obligatorio antes que `ca`); **(b)** aparece un segundo usuario real que no lee castellano. **Ningún otro motivo reabre esto.** **(4)** Marcar el ítem 36 del `pre-dev-checklist.md` como ☑.

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea ninguna tarea: F1 arranca en `es` por D-25 con o sin esta decisión. El coste de dejarla abierta es de segundo orden pero real: I-19 sigue figurando como alcance pendiente de Fase 2 y **cualquier planificación de F2 tendrá que volver a evaluarla desde cero**. **El riesgo material no es no traducir, es que la barandilla se erosione sin que nadie lo note**: si se acumulan cadenas hardcodeadas durante F1-F2, añadir un locale deja de ser «traducir» y pasa a ser **refactorizar**, que es exactamente lo que `spec.md`:431 da por descartado. Ese coste no aparece hasta que se intenta, **y entonces es de decenas de horas**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Cierra una incógnita de alcance para dos fases.

---

### C-02 · CS-15 / I-04 — Sí se puede cerrar: integración con MAM es N/A en modo personal

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** ninguno

**(a) CRITERIO.** Una incógnita se cierra cuando **desaparece la pregunta**, no cuando desaparecen las ganas de contestarla. Desaparece la pregunta si se cumplen las tres: **(a)** su objeto ya no existe en el contexto actual, **(b)** el documento que la citaba ya la declara fuera de alcance, **(c)** existe un registro donde reaparecería si el contexto cambiara. **Con las tres, cerrar no pierde información.**

**(b) FUNDAMENTO.** **(a)** ✅ El objeto no existe: I-04 pregunta por «Integración con MAM u otros sistemas internos **de Daycry**» (`spec.md`:414); el enunciado **presupone una organización con sistemas internos**, y esa premisa está muerta desde el 2026-09-01, cuando I-01 se cerró con «el equipo es el propietario en solitario» (`spec.md`:411). **(b)** ✅ Ya está fuera de alcance por escrito: `spec.md` §5.3 la lista como «no presupuestada», y `pre-dev-checklist.md`:85 la marca «Solo si cambia el alcance». **(c)** ✅ Existe el registro de reapertura: **GC-01** (`gobernanza.md` §8). Y **existe precedente exacto con redacción reutilizable**: I-16 e I-18 se cerraron el mismo día con la fórmula «✅ CERRADA el 2026-09-01: **N/A en modo personal** (decisión del propietario: proyecto personal en solitario)» (`spec.md`:427, :429). **No hay que inventar mecanismo: hay que aplicar el que ya funcionó tres veces.**

**(c) RECOMENDACIÓN.** Cerrar replicando literalmente el patrón existente: tachar la fila en `spec.md` §10 y sustituir el campo «Qué desbloquea» por «✅ **CERRADA el 2026-09-XX**: **N/A en modo personal** — no existe MAM ni sistema interno con el que integrarse (consecuencia directa de I-01). Se conserva en §5.3 como fuera de alcance; reaparecería solo si **GC-01** abriera un contexto organizativo». Marcar el ítem 37 del checklist como ☑. **Coste: minutos. Riesgo: cero** — ✅ no hay ninguna tarea, ningún € ni ningún criterio de aceptación que dependa de I-04 (grep sin resultados en `tasks.md`).

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna consecuencia técnica: nada se bloquea y nada se retrasa. El coste es **de higiene documental, pequeño pero acumulativo**, con el efecto de segundo orden descrito en la cabecera de este bloque. **Unos minutos de decisión ahora contra unos minutos por revisión, indefinidamente.**

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Cierra una incógnita de la spec.

---

### C-03 · CS-14 / I-03 — NO cerrarla como «no aplica»: hay que **reubicarla** a las condiciones de reapertura de la Fase 4

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** ninguno

**(a) CRITERIO.** Mismo criterio que C-02, aplicado con honestidad, **y da un resultado distinto**. «Fuera de alcance» y «bloqueada detrás de un no-go» **no son lo mismo**. Regla de separación: **se CIERRA lo que ya no puede volver; se REUBICA lo que sí podría volver pero no condiciona nada hoy.** Y una incógnita cuya **criticidad declarada no se corresponde con lo que realmente bloquea** está mal clasificada, no sobra.

**(b) FUNDAMENTO.** **(1) Corrección al planteamiento de la pregunta**: ✅ I-03 **no** está declarada fuera de alcance. `spec.md` §5.3 (líneas 300-317) lista SaaS público, apps móviles, mastering, vídeo, colaboración en tiempo real, integración MAM, distribución en streaming, modelos no comerciales, réplica visual de Suno, filtro de similitud, WCAG AA, tercer adapter e idiomas de UI. **El catálogo licenciado no aparece.** La premisa «ambas declaradas fuera de alcance» es cierta para I-04 y **falsa para I-03**. **(2)** ✅ Lo que I-03 dice de sí misma: «resolver I-03 es precondición de una **nueva evaluación**, no de planificar» (`spec.md`:413), con la Fase 4 en **no-go decidido**. **(3) La incoherencia real, que es de clasificación y no de existencia**: I-03 conserva criticidad **«Crítica»** mientras condiciona **0 tareas y 0 €** del presupuesto autorizado. Una fila «Crítica» que no bloquea nada **devalúa la palabra «crítica» en toda la tabla**, donde sí hay críticas de verdad (I-05, I-05b). **(4) Precedente exacto de reubicación, ya usado para una pieza de la MISMA fase**: ✅ `gobernanza.md` §8e traslada el RGPD/DPIA de la clonación de voz (C-04, Fase 4, hoy en no-go) a GC-01 **en lugar de borrarlo**. **(5)** ✅ El propio checklist ya apunta a la solución sin nombrarla: `pre-dev-checklist.md`:86 dice «Sin acción salvo revisión del no-go» — **eso describe una condición de reapertura, no una incógnita activa**.

**(c) RECOMENDACIÓN.** **No cerrar como «no aplica»; reclasificar y reubicar**: **(a)** cambiar la criticidad de I-03 de «Crítica» a «**Inactiva — precondición de reapertura de la Fase 4**», que es lo que de verdad es; **(b)** mover el contenido íntegro a un bloque explícito de «**condiciones de reapertura del no-go de Fase 4**», junto a `gobernanza.md` §8e, que ya custodia la pieza de RGPD de esa misma fase, dejando en `spec.md` §10 solo un puntero de una línea; **(c)** marcar el ítem 38 del checklist como ☑ **con la etiqueta «reubicada», no «cerrada»** — porque esa es la verdad y **la etiqueta correcta es lo único que evita que dentro de un año alguien la lea como resuelta**. Motivo de no borrarla, sin adornos: si algún día se reabre la Fase 4, **la primera pregunta será exactamente esta**; conservarla reubicada cuesta una línea, redescubrirla cuesta rehacer el razonamiento entero.

**(d) CONSECUENCIA DE NO DECIDIR.** Ninguna consecuencia técnica, más un efecto de segundo orden que sí es material: mientras I-03 figure como **«Crítica»**, cualquier lectura externa del expediente —**o cualquier agente que priorice por criticidad, que es exactamente lo que hacen las skills de backlog de este repo**— concluirá que hay una incógnita CRÍTICA abierta, sin dueño y sin fecha, y gastará tiempo en ella o la esgrimirá como argumento de riesgo. **Ese fallo ya ocurrió una vez** con las filas heredadas del modo corporativo, que hubo que cerrar en bloque el 2026-09-01. El coste no es de horas de desarrollo: es que **la tabla de incógnitas deje de significar lo que dice**.

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Reclasifica una incógnita de la spec y toca las condiciones de reapertura de un no-go.

---

### C-04 · CS-44 + CS-45 — Confluence y Jira: no, y cerrados con condición de reapertura escrita

**Estado:** ⚙️ lista para ejecutar · **Confianza:** alta · **Plazo:** ninguno

**(a) CRITERIO.** Una herramienta de coordinación se justifica **cuando elimina un coste de coordinación entre personas o sistemas** que el montaje actual no puede eliminar. Con N=1 y una regla de ledger canónico ya en vigor, cualquier gestor de tareas es **por construcción un espejo**: beneficio de coordinación cero, coste de sincronización estrictamente positivo. Y un cabo suelto **se cierra con una decisión reversible más su condición de reapertura**; dejarlo «abierto» es la única opción que garantiza volver a gastar atención en él.

**(b) FUNDAMENTO.** ✅ Verificado hoy: `ls .claude/` contiene `rates.json`, `settings.local.json` y los ficheros de headroom — **no existen `confluence.json` ni `jira.json`**, luego el opt-in está genuinamente desactivado, tal como declara `CLAUDE.md`. ✅ La regla que hace redundante a Jira es explícita y es de este repo: «Los ledgers propios de otras herramientas son **espejo, no fuente**. No crear ledgers paralelos» — un Jira sincronizado con `tasks.md` **no añade información; añade una superficie de deriva**. Para Confluence, el propio caso de uso declarado por la skill `confluence-pull` es «una persona **NO técnica** (p. ej. un PM sin git)», persona que **en este proyecto no existe**: `gobernanza.md` cierra el RACI con «todos los papeles = el propietario». ✅ Volumen que se estaría espejando: **12 artefactos, 139.622 B solo `tasks.md`**, en constante reescritura — el peor perfil posible para una sincronización manual.

**(c) RECOMENDACIÓN.** Marcar CS-44 y CS-45 como ☑ cerrados en `pre-dev-checklist.md`:88-89, con el texto de decisión «**NO activar**» y su condición de reapertura escrita al lado, para que la decisión sea auditable y no haya que repensarla: **Jira** se reabre cuando haya **≥ 2 personas ejecutando tareas en paralelo** (escenario de GC-01 §8g, «revisitar la gobernanza con personas reales»); **Confluence** se reabre cuando exista **un lector recurrente de la documentación que no use git**. Ninguna de las dos se cumple hoy ni se cumplirá antes de GC-01. **Nota operativa**: aunque se reabrieran, la regla de ledger canónico sigue mandando — `tasks.md` seguiría siendo la fuente y Jira el espejo, **nunca al revés**.

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea nada, **y esa es precisamente la razón para cerrarlo hoy en vez de arrastrarlo**: son dos de los 51 ítems del checklist que consumen atención cada vez que se revisa y que **jamás van a pasar a «hecho» por sí solos**. El coste de no decidir es puro ruido de gestión, pero recurrente. Si alguien lo activara **sin** decidirlo, el coste sí es real: **dos ledgers divergentes y la violación directa de la regla de ledger canónico**.

**(e) QUIÉN FIRMA.** ⚙️ **Agente.** Cierra dos ítems de checklist confirmando el estado por defecto ya declarado en `CLAUDE.md`; no activa nada ni cambia configuración.

---

### C-05 · CS-52 — `to-pdf` y Chromium: usar el Chrome del sistema, pero la variable no está persistida en ningún sitio

**Estado:** 🔒 pendiente de firma · **Confianza:** alta · **Plazo:** el próximo PDF que haga falta

**(a) CRITERIO.** Ante dos dependencias que hacen lo mismo, se elige **la que ya está instalada, se mantiene sola y no añade un binario más al equipo** — salvo que la **reproducibilidad byte a byte** del artefacto sea un requisito. Y regla previa a cualquier elección: **una configuración que solo existe en la sesión en la que se usó no es una configuración, es una casualidad.**

**(b) FUNDAMENTO.** ✅ Verificado en esta máquina, no supuesto. **(1)** El Chrome del sistema **existe**: `C:\Program Files\Google\Chrome\Application\chrome.exe`. **(2)** El Chromium de puppeteer **no está descargado**: `ls -d /c/Users/*/.cache/puppeteer` no devuelve ninguna ruta en ningún perfil. **(3) Hallazgo — `PUPPETEER_EXECUTABLE_PATH` no está persistida en ningún sitio localizable**: no está en el entorno del proceso (vacía), no está en `HKCU\Environment` (`reg query` → «no se ha podido encontrar la clave o el valor»), no está en `.claude/settings.local.json` (leído: solo `ANTHROPIC_BASE_URL` y `ENABLE_TOOL_SEARCH`) y no aparece en ningún fichero del repositorio (`grep -rn PUPPETEER` → cero resultados). Sin embargo `decision-brief.pdf` existe (219.027 B, 2026-09-01 19:35). **Conclusión forzosa: se generó con la variable puesta a mano en aquella sesión, y esa configuración se ha perdido.** La premisa «mantener la variable» describe **un estado que hoy no existe en disco**. ⚠️ **No verificado**: la versión exacta de Chrome instalada (`wmic` no devolvió salida en este shell); es irrelevante para la decisión.

**(c) RECOMENDACIÓN.** No descargar el Chromium de puppeteer (~150 MB) y **persistir la ruta al Chrome del sistema**, que es el paso que falta. Sitio correcto: **`.claude/settings.local.json`**, que `.gitignore` ya excluye, **porque es configuración de máquina y no debe viajar en un repo que además hoy es público** (ver A-22). Añadir dentro del bloque `"env"` existente: `"PUPPETEER_EXECUTABLE_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"`. **A favor**: cero descarga y, sobre todo, **se evita un segundo navegador headless que nadie parchea** (Chrome del sistema se autoactualiza; un Chromium en una caché local no), lo cual importa en un proyecto cuyo `CLAUDE.md` ya trata la superficie de ejecución como asunto de seguridad. **En contra, dicho honestamente**: si algún día se exigiera que los PDF salgan **idénticos byte a byte** en cualquier máquina y fecha, lo correcto sería fijar el Chromium de puppeteer; **no es el caso**: estos PDF los lee una persona. **Riesgo aceptado y barato**: una actualización de Chrome podría romper la invocación; el fallo sería ruidoso e inmediato (el PDF no se genera) y el plan B (dejar que puppeteer descargue) sigue disponible.

**(d) CONSECUENCIA DE NO DECIDIR.** No bloquea ninguna tarea del plan. Lo que se paga es que **la próxima vez que haga falta un PDF** —el candidato inmediato es el protocolo de G1 y el acta de la sesión de escucha— **el flujo fallará o disparará una descarga de 150 MB no prevista, en medio de otra cosa**; y con la advertencia de disco ya registrada en el checklist (C: llegó a ~5 GB libres durante la sesión) esa descarga puede llegar en el peor momento. **Coste de decidir: dos minutos. Coste de no decidir: una interrupción cada vez.**

**(e) QUIÉN FIRMA.** 🔒 **Propietario.** Escribir en `settings.local.json` es **un cambio de configuración del entorno**: un agente deja el snippet preparado, **no lo aplica por indicación de otro agente**.

---

## 5. 🚧 Lo que NO decide este documento

> **Sección deliberadamente separada.** Todo lo anterior son **propuestas**. Nada de esta sección está decidido, ratificado ni implícitamente aceptado por el hecho de aparecer escrito.

`gates/gobernanza.md` §2.1 nombra al propietario **evaluador único de G1** precisamente para que **quien construye no ratifique la calidad**; el mismo documento concentra en él los papeles de supervisor, usuario piloto y decisor de construir-vs-comprar (§2, §3, §4), conservando **íntegros los gates y sus umbrales numéricos como autodisciplina** — «**ningún número se degrada**». Y `gates/g1-protocolo.md` §9 encabeza su bloque de firma con «**BLOQUE PENDIENTE — no lo puede rellenar quien redacta el protocolo**», mientras §8.1 declara **inválida** la sesión si los umbrales no estaban ratificados por escrito **con fecha anterior a la primera escucha**. De ahí se sigue, literalmente, lo que este registro **no** hace:

### 5.1 · Los umbrales de G1 — intactos y sin firmar

Siguen exactamente como estaban, **sin una décima de diferencia**: **7/10 con D5 ≥ 4** · **ninguna dimensión con media < 3,0** · **CLAP ≥ librería en 7/10** · **WER ≤ 15 % medio y ≤ 25 % peor caso** · **no-go si pierde en D5 contra librería en > 5/10**. Las diez observaciones A-10…A-19 son **contradicciones internas, imposibilidades aritméticas, defectos de instrumento y de muestra**, y ninguna toca un número — **con una excepción declarada, que se señala aquí para que nadie firme sin verla: la opción (2) de A-13** sustituiría el denominador del criterio 5 («> 5 de **los 10** briefs») por «> 5 de los briefs **comparables**». Eso **cambia cómo se calcula ese umbral**: con `N_comparables` ≤ 5 el NO-GO se vuelve **matemáticamente imposible**. La opción está marcada como tal en su ficha, se ofrece **solo** con cláusula de suelo obligatoria (`N_comparables` ≥ 8, o la sesión no cierra el gate) y la ficha recomienda en su lugar la opción **(0)**, que no toca el denominador y resuelve el caso con `g1-protocolo.md`:109. **Ninguna otra ficha de este registro toca un número.** **Por qué es del propietario:** `gobernanza.md` §2.1-§2.2 y `g1-protocolo.md` §8.1.

### 5.2 · Los diez briefs y el estado de `T-08`

Los briefs de `g1-protocolo.md` §4 siguen **`propuestos`**; `T-08` sigue **`en-revision`** y **no debe pasar a `completado`** hasta que exista la firma fechada de §9. Las sustituciones que A-17 sugiere solo pueden hacerse **antes de generar**, y las hace el propietario. **Por qué es del propietario:** la composición de la muestra determina el veredicto (A-13 lo demuestra), y §9 reserva expresamente ese bloque.

### 5.3 · D-31 y D-23 son **textos propuestos**, no decisiones registradas

Los dos traen su tabla de firma con **⚠️ pendiente** en fecha y firma. D-31 toca un umbral citado en `spec.md` §11.1 (D-06) y D-29; D-23 es **precondición 6** de `g1-protocolo.md` §9.1 y está exigida «por escrito antes de G1» por `gobernanza.md` §2.2.5. **Por qué son del propietario:** un agente puede implementarlos y probarlos —D-31 ya está implementado y con 85 tests en verde—, pero **no puede ratificar el número**.

### 5.4 · El gasto — todo, incluso el pequeño

No se ha abierto ninguna cuenta, no se ha prepagado nada, no se ha dado de alta ningún pod y **no se ha gastado un euro**. Quedan pendientes de firma: el **techo de caja** (A-05), el **saldo prepago y la desactivación del auto-pay** (A-06), el **alta de la cuenta de RunPod** (A-07), la **postura de producción** (B-08, B-09), la **elección definitiva de tarjeta** en F6 (B-10) y el **descarte de las 32 h / 1.920 €** de `T-86` (B-07). **Por qué es del propietario:** `spec.md`:422 (I-11) — «el presupuesto lo decide el propietario; las cifras en € de la evaluación son informativas».

### 5.5 · El alcance — ni se amplía ni se recorta aquí

No se descarta `T-86`, no se degrada `T-57`, no se pasa de tres entornos a dos, no se fija el alcance de idiomas, no se cierra ni se reubica ninguna incógnita de la spec, no se retira ningún criterio de aceptación escrito. **Todo eso son propuestas** (B-07, B-17, B-06, A-08, C-01, C-02, C-03). **Por qué es del propietario:** `gobernanza.md` concentra en él la decisión de alcance, y `CLAUDE.md` fija que las tareas se cierran solo cuando sus criterios de aceptación están verificados: **cambiar un criterio escrito es un acto de firma, no de mantenimiento**.

### 5.6 · Los invariantes de `CLAUDE.md`

Dos fichas señalan que hay **invariantes en contradicción con la práctica vigente**: la firma del esquema del manifiesto por legal (B-03 / **X-8**) y la regla de cadencia de merge que falta (A-23). **Ninguna de las dos se aplica aquí.** Modificar `CLAUDE.md` —la fuente de invariantes— **lo aprueba el propietario**; un agente solo puede señalar la contradicción y proponer la redacción.

### 5.7 · Lo legal y lo comercial: GC-01

`gobernanza.md` §8 reagrupa en el **gate de comercialización GC-01** siete condiciones (a–g) que solo aplican si el proyecto pasa a ser comercial o a usarse con terceros. Este registro **no activa GC-01, no lo anticipa y no lo da por cumplido**. Lo que sí hace es **acumular material** en él: el informe escrito de legal (B-19 → §8a), la protegibilidad del output (B-20 → §8b), los ToS de Suno (B-21 → §8c), la pregunta jurídica **J-1** sobre propagación de la NC de un dataset (B-15, ver **X-4**), el instalador `T-86` reclasificado (B-07), el entorno `stage` (B-06) y la **visibilidad del repositorio** (A-22). **Por qué es del propietario:** GC-01 es suyo por definición — es la puerta de la comercialización.

### 5.8 · La única inversión de un diferimiento que se propone, y por qué no la toma un agente

**A-21 (CS-04, Anexo A)** es la única de las cinco diferidas donde se recomienda **revertir** el diferimiento y firmar ahora. Aun así **no se firma aquí**: es literalmente una **aceptación de riesgo del propietario** (`g2-matriz-resultados.md` §8.3), y su valor entero consiste en que **la firme quien asume el riesgo**. Un agente que la diera por hecha destruiría exactamente aquello que la mitigación protege.

### 5.9 · Las cifras ratificadas, sin tocar

**Fase 0+1: 656 h base / 39.360 € con margen.** **Pre-planificado y bloqueado por gate (F10+F11): 407 h / 24.420 €.** **Ledger completo: 1.063 h / 63.780 €.** **Fase 4: no-go vigente, sin tareas.** Este documento **no suma, no resta y no reasigna** ninguna de esas cifras; cuando una ficha propone descartar horas (B-07) o ahorrar parte de una tarea (B-14, B-05), lo hace **como propuesta y sin reestimar** — reestimar es trabajo del `evaluator`, no de este registro.

---

## 6. Orden de ejecución sugerido (no es una decisión: es una secuencia)

Las dependencias de orden que aparecen en las fichas, juntas y en un solo sitio:

1. **A-06 antes que A-07** — el tope de caja antes que la cuenta. Al revés es el escenario R-17.
2. **A-22 antes que A-23** — privatizar y renombrar el repositorio antes de mergear a `main`, que es la rama por defecto de un repo hoy público.
3. **A-01 antes que cualquier medición** — sin la firma de D-31, `T-03` y `T-05` no arrancan.
4. **A-04 antes del primer lote largo de `T-03`** — la regla de conmutación tiene que existir antes de que aparezca la tentación de recortar la muestra.
5. **A-13 antes de generar nada** — las líneas base se eligen primero (§5.1 del protocolo); su disponibilidad puede invertir el veredicto.
6. **A-08, A-09, A-10…A-19 y A-20 antes de firmar §9** — y §9 antes de la primera escucha, por §8.1.
7. **A-18 y B-03 antes de generar la primera pista** — los campos del manifiesto no se pueden añadir después: la cadena WORM no admite backfill.
8. **A-21 antes de que F2 genere la primera pista** — la aceptación de riesgo precede al uso, no al revés.
9. **B-09 y B-10 se cierran juntas** — la magnitud del error de tarjeta depende de la postura elegida.
10. **B-07 y A-05 se cierran juntas** — mientras `T-86` siga sin resolver, el denominador del stop-loss es ambiguo.

## 7. Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-01 | Creación del registro con **49 decisiones** ordenadas por urgencia (23 bloquean hoy, 21 con fecha en un gate, 5 de higiene), **9 contradicciones entre líneas resueltas y documentadas** (§1-bis) y sección §5 «Lo que NO decide este documento». **33 firmas pendientes del propietario**; 16 fichas ejecutables por agente. **Ningún umbral, cifra ratificada ni alcance modificado.** | revisión en cinco líneas (agentes) |
| 2026-09-01 | **Pase adversarial de tres jueces sobre la primera versión de este registro: tres defectos bloqueantes encontrados y corregidos antes de someterlo a firma.** **(1) A-13 degradaba el criterio 5 de no-go de G1** — su opción recomendada (2) cambiaba el denominador de «> 5 de los **10** briefs» a «> 5 de los **comparables**», lo que con `N_comparables` ≤ 5 hace el NO-GO **matemáticamente imposible**, mientras el propio documento afirmaba dos veces (encabezado y §5.1) que ninguna ficha movía un umbral. Corregido: excepción declarada en el encabezado, en §5.1, en la fila de la tabla resumen y en la ficha; la opción (2) solo se ofrece con **cláusula de suelo `N_comparables` ≥ 8** (si no, la sesión no cierra el gate); se añade la **opción (0)**, preferente, que no toca el denominador y resuelve el caso con `g1-protocolo.md`:109. **(2) A-05 relajaba el stop-loss D-28 por cuatro vías mientras decía no relajarlo** — denominador **53** en vez de **54** tareas (`tasks.md`:37/:1356, `improvement-plan.md`:304, `CLAUDE.md`; el «53» solo vive en `tasks.md`:2055, changelog previo a la ratificación de `T-85`), redondeos permisivos («> 394 h» por 393,6 h; «< 21» por el 40 % = 21,6) y definición de alcance por conteo equiponderado que marcaría 3,7 % de entrega el día 1 de F2 con cero horas hechas (cuatro tareas valen 0 h). Corregido: el gate se reexpresa como `horas_reales > 393,6 h` **Y** `alcance ponderado por horas < 40 % de 656 h`, sobre **54 tareas / 656 h**. **(3) B-13 escribía una excepción dentro de un invariante innegociable, apoyada en una cita falsa** — el eje L3 decía «safetensors u ONNX **o excepción documentada con mitigación**» (`CLAUDE.md`:50 no admite excepción) y su apartado (c) proponía **ejecutar** el `torch.load` en contenedor efímero invocando el «patrón D-15», que es aislamiento de credenciales (`spec.md`:70) y no autoriza nada de eso. Corregido: se retira la coletilla, se retira el procedimiento y la cita falsa, y se sustituyen por la vía ya existente y probada — conversión con el **auditor de opcodes** de `apps/runner/tools/build_artifact.py` (precedente: `silence_latent.pt`), original en cuarentena fuera del volumen, y **descarte o escalado al propietario** si un candidato no se puede convertir. **B-13 se reclasifica de ⚙️ a 🔒** por implicar decisión de alcance/licencia: reparto 33/16 → **34/15**. Ninguna otra ficha se ha tocado. | pase adversarial (3 jueces) + agente corrector |
| ⚠️ pendiente | Firma del propietario sobre las 34 fichas 🔒, o devolución con instrucciones | Daycry (propietario) |
