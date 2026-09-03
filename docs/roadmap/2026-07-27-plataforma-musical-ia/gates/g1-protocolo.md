---
documento: gate-g1-protocolo
titulo: "Gate G1 — Protocolo de escucha ciega y decisión de calidad (ACE-Step 1.5), modo solo"
iniciativa: "Plataforma propia de generación musical por IA (proyecto personal)"
slug: plataforma-musical-ia
tarea: T-08
ejecutado-por: T-09
estado: pendiente-de-ratificacion
fecha: 2026-09-01
actualizado: 2026-09-01
autor: implementer
evaluador: "Daycry (propietario) — evaluador único en modo solo (gobernanza.md §2.1)"
umbrales-fijados: 2026-09-01
umbrales-ratificados: "⚠️ pendiente — propietario, antes de la primera escucha (§9)"
spec: ../spec.md
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
gobernanza: ./gobernanza.md
gate-g2: ./g2-matriz-resultados.md
gate-comercializacion: "GC-01 (gobernanza.md §8)"
---

# Gate G1 — Protocolo de escucha ciega y decisión de calidad

> **Estado del documento: `pendiente-de-ratificación` (2026-09-01).** Este texto es el **protocolo**, no el resultado. **No contiene ninguna puntuación**: las hojas de §7 están deliberadamente vacías y el veredicto se escribirá en `g1-resultado.md` cuando `T-09` ejecute la sesión. Su función es la que `evaluation.md` §10.2 exige literalmente: **poner los números por escrito antes de escuchar**, porque «un gate sin número lo decide quien esté en la sala, y quien está en la sala siempre decide *sigamos*».
>
> **Dos cosas quedan abiertas, con dueño y momento** (§9 y §10.4): la **ratificación firmada de los umbrales** por el propietario —que **debe** ocurrir antes de la primera escucha— y la **verificación formal de los ToS de Suno**, trasladada al gate de comercialización **GC-01 §8c** (`gobernanza.md`, `pre-dev-checklist.md` ítem 11 / CS-03). Ninguna de las dos la puede cerrar quien redacta el protocolo.

---

## 0. Adaptaciones a modo solo, declaradas

Este protocolo desarrolla `evaluation.md` §10.2 **sin degradar un solo umbral**, aplicando las tres adaptaciones que el acta de gobernanza del 2026-09-01 (`gobernanza.md`) introdujo al declararse el proyecto **personal y en solitario**. Se declaran aquí, en la cabecera, por el mismo motivo por el que se declararon al cerrar `T-02`: **lo que cambia tiene que verse, y lo que no cambia también.**

| # | Elemento de `evaluation.md` §10.2 | Adaptación en modo solo | Qué **no** cambia |
|---|---|---|---|
| **A-1** | «**3 evaluadores**, al menos 2 supervisor musical o editor de producción real; el desarrollador no puntúa»; umbral verificado «por al menos **2 de 3** evaluadores» | **El propietario es evaluador único** (`gobernanza.md` §2.1), con la **pérdida de independencia desarrollador/juez aceptada por escrito**. Desaparece el **quórum entre personas**, porque no hay tres personas. Opción **recomendada, no obligatoria**: invitar a **1–2 oyentes externos informales** (§5.7) | **El número no se toca**: siguen siendo **7 de 10 pistas con ≥ 4/5 en la dimensión 5** y **ninguna dimensión con media < 3,0**. Lo que se pierde es el contraste entre juicios, no el listón |
| **A-2** | «**10 briefs reales** extraídos de producciones de **Daycry** ya cerradas, con su brief musical original» | `gobernanza.md` §2.2.1 lo redefine como **10 briefs propios realistas** — vídeos, maquetas y encargos ficticios pero **concretos**. Los 10 están redactados en §4 y quedan **propuestos, pendientes de ratificación del propietario** | Siguen siendo **10**, con **género, tempo, instrumentación, idioma del canto, duración y uso final declarados antes de generar**, para que «adecuación al brief» (D1) sea una medida y no una impresión |
| **A-3** | «**Verificar los ToS de Suno** antes de usar su salida como línea base (2 h de legal en la semana de G2)» | **No se cumple antes de G1, y se declara.** `gobernanza.md` §2.2 (nota final) y `pre-dev-checklist.md` ítem 11 / CS-03 trasladan la verificación al **gate de comercialización GC-01 §8c**. Hasta entonces: línea base de Suno **bajo responsabilidad personal del propietario y solo para uso personal**, y **prohibido** cualquier uso comercial o con terceros de resultados comparados contra ella (§10.4) | El protocolo **funciona igual sin Suno** (§5.6): ningún umbral depende de esa línea base. **La que decide el criterio de no-go es la línea base de librería**, y esa se conserva |

**Regla que gobierna las tres:** una adaptación puede cambiar **quién** hace algo o **de dónde sale** el material; **no puede cambiar un número**. Si en algún punto de este documento una adaptación pareciera rebajar un umbral, prevalece `gobernanza.md` §2.2 y el umbral original.

---

## 1. Propósito del gate y qué decisión bloquea exactamente

**G1 responde a una sola pregunta:** ¿la calidad de lo que genera **ACE-Step 1.5** en este hardware, con estos briefs, alcanza el nivel exigible para construir una plataforma sobre él — o es mejor no gastar el resto?

- **Qué se evalúa:** **solo ACE-Step 1.5** (D-27). HeartMuLa no se evalúa aquí porque no está contenerizado hasta la Fase 1; pasa **G1-bis** con **este mismo protocolo** al registrarse su adapter.
- **Qué NO se evalúa:** nada que sea contrato observable (formatos, duración ±5 %, loudness, manifiesto, estados de la máquina). Eso lo verifican los E2E de `test-plan.md`. **G1 es escucha humana**, y solo escucha humana.
- **Cuándo:** al cierre de la **Fase 0** (F2 del ledger), una vez completadas `T-03`…`T-08`. Lo ejecuta **`T-09`**, que produce `g1-resultado.md`.

### 1.1 El bloqueo, en cifras

> **Ninguna tarea de `F4` en adelante puede empezar antes de que `T-09` quede `completado` con resultado favorable.**

| Lo que G1 desbloquea o cancela | Tareas | Horas base | Coste con margen |
|---|---|---|---|
| F4 · Cimientos de plataforma (C-13) | `T-10`…`T-25` | 214 h | 12.840 € |
| F5 · Trazabilidad + registry (C-10a + C-11) | `T-26`…`T-34` | 145 h | 8.700 € |
| F6 · Infraestructura GPU (C-14, incl. `T-85`) | `T-35`…`T-41`, `T-85` | 112 h | 6.720 € |
| F7 · Generación end-to-end (C-01) | `T-42`…`T-48` | 78 h | 4.680 € |
| F8 · Instrumental + auth (C-02 + C-12) | `T-49`…`T-52` | 40 h | 2.400 € |
| F9 · Verificación final y cierre | `T-53` | 0 h | 0 € |
| **Total bloqueado por G1** | **45 tareas** | **589 h** | **35.340 €** |

Y, aguas abajo, las **407 h / 24.420 €** de F10 y F11 (Fases 2 y 3, hoy `bloqueada (gate)`), que además dependen de G1-bis y de G3.

**Por eso este documento existe y por eso cuesta 4 h:** decide, con una tarde de escritura y una sesión de escucha, sobre **589 de las 656 h ratificadas** de F1–F9. En palabras de `evaluation.md` §10.1: *el 4,1 % del esfuerzo compra la información que decide el otro 95,9 %*.

### 1.2 Lo que este gate NO decide

- **No decide si el proyecto es legalmente viable** — eso fue **G2** (`g2-matriz-resultados.md`, cerrado el 2026-08-18, fila 1 «sí total», con su deuda documental trasladada a GC-01).
- **No decide si la plataforma se usa** — eso es **G3** (`gobernanza.md` §3), y se mide con uso real, no con escucha.
- **No decide si algo se puede vender** — eso es **GC-01** (`gobernanza.md` §8). Un `go` en G1 **no autoriza ningún uso comercial ni con terceros**.

---

## 2. Umbrales — fijados ANTES de escuchar

> ## 🔒 UMBRALES FIJADOS EL **2026-09-01**
>
> **Fecha de fijación:** 2026-09-01 (redacción de `T-08`).
> **Fecha de ratificación firmada:** ⚠️ **pendiente** — bloque de firma en §9, a rellenar por el propietario **antes de la primera escucha**.
> **Origen literal:** `evaluation.md` §10.2 · `gobernanza.md` §2.2 y §5.
>
> ### ✅ Umbral de aprobado (subjetivo)
> 1. **7 de las 10 pistas propias** obtienen **≥ 4/5 en la dimensión 5** («¿la usarías tal cual?»).
> 2. **Ninguna de las 5 dimensiones** tiene **media < 3,0** sobre las 10 pistas propias.
>
> ### ✅ Umbrales objetivos (medidos, no opinados)
> 3. **CLAP** audio-texto de la pista propia **≥** el de la línea base de **librería** en **al menos 7 de los 10** briefs.
> 4. **WER** de la letra cantada: **≤ 15 % de media** sobre las 10 pistas propias **y ≤ 25 % en el peor caso** individual.
>
> ### ❌ Criterio de no-go explícito
> 5. Si la pista propia queda **por debajo de la de librería en la dimensión 5** en **más de 5 de los 10** briefs → **NO-GO**, con independencia de todo lo demás. *(Significa que la plataforma no mejora lo que ya se tiene: la conclusión correcta es no construirla.)*
>
> ### 🚫 Regla de inmutabilidad
> **Estos cinco números no se tocan después de escuchar. Ni una décima.** Cambiarlos a la vista del resultado convierte el gate en una justificación. Si tras la sesión el propietario cree que un umbral estaba mal calibrado, **el cambio no se aplica a esa sesión**: se documenta como propuesta razonada, se ratifica por escrito con fecha y solo rige a partir de la **siguiente** ejecución completa del gate (G1-bis, o una repetición según §8.4). El resultado ya celebrado se archiva **con los umbrales que tenía**.

### 2.1 Precisiones aritméticas (para que no las decida el momento)

| Cuestión | Regla fijada hoy |
|---|---|
| Cómo se calculan las medias de dimensión | Media aritmética de las **10 pistas propias**, calculada **con dos decimales** y comparada **sin redondear**: `2,95` **incumple** el `< 3,0`. Las medias se publican en la hoja con dos decimales |
| Qué significa «≥ 4/5 en la dimensión 5» | Puntuación entera **4 o 5**. La escala es entera: **no se admiten medios puntos** en ninguna dimensión |
| Qué significa «por debajo de la librería» (no-go) | **Estrictamente menor**: `D5(propia) < D5(librería)`. El **empate no cuenta como derrota** |
| Qué pasa si un brief no tiene línea base de librería utilizable | Ese brief **cuenta como derrota** en el criterio 5 y como **no cumplido** en el criterio 3. Un brief sin línea base es un brief sin evidencia, y la carga de la prueba la tiene el modelo propio, no la librería |
| Pistas propias evaluadas | **Una por brief** (la seleccionada según §5.2). Las tomas descartadas se archivan pero **no puntúan** |
| Empates o dudas al puntuar | Se puntúa **a la baja**. Si el propietario duda entre 3 y 4, es **3** |

### 2.2 Nota sobre el quórum desaparecido

`evaluation.md` §10.2 escribía el umbral de aprobado como «7 de las 10 pistas con ≥ 4/5 en la dimensión 5, **por al menos 2 de 3 evaluadores**». En modo solo **no hay 2 de 3**: hay **1 de 1**. Conviene ser explícito sobre qué se pierde y qué no:

- **Se pierde** el contraste entre juicios independientes — la mitigación que impedía que un mal día, un sesgo o un autoengaño de una sola persona bastaran para pasar el gate. `gobernanza.md` §2.1 acepta esa pérdida **por escrito**.
- **No se pierde** el listón: **7**, **4/5**, **3,0**, **7 de 10**, **15 %**, **25 %** y **> 5 de 10** son exactamente los mismos números.
- **Compensaciones que se conservan y son obligatorias:** umbrales por escrito **antes** de escuchar (§2 y §9); **escucha a ciegas** con mapa sellado generado por script (§5.4); **hoja sellada por hash antes de romper el ciego** (§5.5); **anotación obligatoria** en cada pista de D5 (§3.5); y **criterio de no-go comparativo** que no depende de la autoestima del evaluador, sino de una pista de librería que existe (§2, criterio 5).
- **Compensación recomendada, no obligatoria:** 1–2 oyentes externos informales (§5.7). No son evaluadores formales, **no bloquean ni desbloquean el gate**, y sus hojas se archivan junto a la del propietario si participan.

La versión corporativa (3 evaluadores, ≥ 2 con perfil de supervisión musical o edición real, quórum 2 de 3) **no se borra**: vive en `gobernanza.md` §8g, dentro de GC-01, para el escenario comercial.

---

## 3. Rúbrica — 5 dimensiones, escala 1–5, con descriptores

Escala **entera de 1 a 5** en las cinco dimensiones. Los descriptores de abajo son **la definición operativa de la escala**: sin ellos, «un 4» significa lo que el evaluador quiera que signifique el día de la sesión — que es exactamente lo que este gate existe para impedir.

**Cómo se usan:** se sube por la escala hasta encontrar el primer descriptor que **deja de cumplirse**; se puntúa el anterior. Los niveles **2** y **4** son intermedios y se definen por contraste con sus vecinos. Ante la duda, **se puntúa a la baja** (§2.1).

**Regla anti-inflación (obligatoria):** todo **5** exige escribir, en la casilla de notas, **una frase que explique por qué no es un 4**. Todo **4 o 5 en la dimensión 5** exige nombrar **el uso concreto** (qué pieza, qué brief) en el que se usaría. Sin esa frase, la puntuación **se rebaja en un punto** al consolidar la hoja.

### 3.1 D1 · Adecuación al brief

*¿Responde esto a lo que se pidió? Se juzga contra el brief escrito en §4, no contra el gusto del evaluador.*

| Nivel | Descriptor |
|---|---|
| **1** | **No responde al brief.** Género, carácter o instrumentación equivocados de raíz. No serviría ni como referencia para explicarle la idea a otra persona |
| **2** | **Responde de oído a alguna palabra del brief, pero falla en dos o más ejes declarados** (p. ej. el género está, pero el tempo se desvía > 15 %, la instrumentación pedida no aparece o el idioma del canto no es el pedido) |
| **3** | **Cumple el género y el carácter general; falla en un eje declarado** — tempo fuera de rango, un instrumento nombrado en el brief ausente, o duración desviada más de un 5 % del objetivo. Aceptable como punto de partida |
| **4** | **Cumple todos los ejes declarados** (género, tempo, instrumentación, idioma, duración ±5 %). El matiz emocional o el encaje con el uso final quedan cortos o genéricos |
| **5** | **Cumple el brief entero, incluido el matiz emocional y el uso final.** Si alguien hubiera encargado esto, esta pista sería una respuesta legítima al encargo, no una aproximación |

### 3.2 D2 · Calidad de mezcla y ausencia de artefactos

*Se juzga en el sistema de escucha declarado en §5.3, al nivel fijado, sin EQ ni realce de ningún tipo.*

| Nivel | Descriptor |
|---|---|
| **1** | **Artefactos evidentes y constantes**: timbre metálico o «acuático» permanente, aliasing, saturación digital, colapso a ruido, voz desintegrada. Inescuchable de principio a fin |
| **2** | **Artefactos audibles y frecuentes en escucha casual** (más de tres eventos claros en la pista), **o** balance roto de forma estructural: voz enterrada, bajo inexistente, agudos estridentes. No se arregla con retoque |
| **3** | **Artefactos audibles solo con atención**, o localizados en **uno o dos puntos** concretos. Balance aceptable, imagen estéreo plausible. **Usable con retoque real** (editar el punto, comprimir, ecualizar) |
| **4** | **Sin artefactos audibles en escucha atenta** en el sistema declarado. Mezcla correcta: los elementos se distinguen, el rango dinámico es razonable, no hay bombeo ni sobrecompresión evidente. Retoque cosmético a lo sumo |
| **5** | **La mezcla no delata el origen sintético.** Balance, profundidad, estéreo y dinámica al nivel de una pista de librería comercial: se puede poner debajo de una locución o de una imagen sin tocarla |

### 3.3 D3 · Coherencia estructural

*Se juzga la pista como pieza completa, en la duración pedida.*

| Nivel | Descriptor |
|---|---|
| **1** | **Sin estructura reconocible**: deriva, bucle sin desarrollo o secuencia arbitraria de ideas. Corte abrupto al final o desvanecimiento aleatorio |
| **2** | **Hay secciones, pero no están ligadas**: cambios sin transición, tonalidad o tempo que se descuadran, un estribillo que no vuelve, un final que no cierra |
| **3** | **Estructura reconocible** (entrada — cuerpo — cierre, o verso/estribillo según el brief) con **una transición floja o un final poco resuelto**. Se entiende la pieza |
| **4** | **Estructura clara y coherente de principio a fin**, con transiciones limpias y final resuelto. El desarrollo es previsible o plano, pero funciona |
| **5** | **Estructura con intención**: desarrollo, contraste y resolución. El arco tiene sentido por sí solo **y encaja en la duración pedida** sin sobrar ni faltar; el punto de mayor energía cae donde el uso final lo necesita |

### 3.4 D4 · Inteligibilidad y prosodia de la letra cantada

*Se juzga **sin leer la letra** en la primera pasada; la letra de referencia solo se consulta para desempatar entre dos niveles. El **WER medido** de §6 es una comprobación **independiente**: no sustituye a esta puntuación y **no se mira antes de puntuarla**.*

| Nivel | Descriptor |
|---|---|
| **1** | **No se entiende la letra.** Fonemas inventados, idioma irreconocible o canto ininteligible. Habría que sustituir la voz entera |
| **2** | **Se entienden palabras sueltas.** Sílabas comidas, acentos desplazados, frases que no se sostienen. Hay que leer la letra para poder seguirla |
| **3** | **Se entiende la mayor parte a la primera escucha.** Errores puntuales de acentuación o articulación que **no rompen el sentido**. Una escucha distraída pierde algún verso |
| **4** | **Se entiende entera a la primera escucha**, con acentuación natural salvo **un giro forzado** identificable. La voz suena cantada, no recitada ni estirada |
| **5** | **Inteligible al 100 %** y con prosodia que respeta el acento natural del idioma pedido: las frases respiran donde deben, el estribillo cae en su sitio y la melodía no maltrata ninguna palabra |

> **Regla de aplicabilidad (fijada hoy):** los **10 briefs de §4 llevan letra cantada**, precisamente para que D4 y el WER sean medibles sobre las 10 pistas y los umbrales del §2 se calculen sobre la muestra completa. La generación instrumental (C-02) es una característica del producto, **no es lo que G1 juzga**. Si en la ratificación (§9) el propietario decide sustituir algún brief por uno instrumental, debe declararlo **antes de generar** y anotar en la hoja que D4 y el WER se calculan sobre la submuestra cantada: **el mismo umbral, sobre menos pistas y, por tanto, con menos evidencia**. Esa reducción se documenta como debilidad de la sesión, nunca como flexibilización del umbral.

### 3.5 D5 · «¿La usarías tal cual en la pieza?»

*La dimensión que decide el gate: sobre ella se aplican el umbral de aprobado (criterio 1) y el criterio de no-go (criterio 5). **La casilla de notas es obligatoria en todas las pistas**, no solo en las altas.*

| Nivel | Equivale a | Descriptor |
|---|---|---|
| **1** | **no** | **No, y no la arreglaría.** Se descarta en el primer pase: arreglarla cuesta más que buscar otra cosa |
| **2** | **no** | **No.** Sirve como maqueta para explicarle la idea a otra persona («algo así»), no como pista que suene en la pieza |
| **3** | **no** | **No tal cual.** La usaría **tras un retoque real**: reeditar la estructura, remezclar, regenerar una sección, sustituir la voz. Trabajo medible, no cosmético |
| **4** | **sí** | **Sí, con retoque cosmético**: recorte, fundido, ajuste de nivel. **No volvería a generar** |
| **5** | **sí** | **Sí, tal cual, sin tocar nada.** Es la pista que entrega. Exige la frase que explique por qué no es un 4 |

**Correspondencia con el «sí/no» de `evaluation.md` §10.2:** **≥ 4 = sí**, **≤ 3 = no**. La nota escrita responde siempre a la misma pregunta: **¿qué le falta para subir un punto?**

### 3.6 Cómo se rellena una pista

Por cada pista — las **tres** de cada brief (propia, Suno y librería), sin saber cuál es cuál:

1. Escucha completa **sin puntuar** (primera pasada del brief, §5.3).
2. Segunda pasada: se puntúan **D1 → D2 → D3 → D4 → D5** en ese orden, **sin volver atrás** a corregir puntuaciones de la misma pista una vez escrita la siguiente dimensión.
3. Se escribe la nota de D5 (obligatoria) y, si hay algún 5, su frase justificativa.
4. **No se comparan las tres pistas del brief entre sí mientras se puntúan.** La comparación la hace la aritmética de §8 al final, no el evaluador en caliente.

---

## 4. Los 10 briefs

> ⚠️ **Estado: PROPUESTOS — pendientes de ratificación del propietario** (§9). Redactados en `T-08` como desarrollo de `gobernanza.md` §2.2.1, que en modo solo sustituye «10 briefs reales de producciones ya cerradas de Daycry» por **briefs propios realistas: vídeos, maquetas y encargos ficticios pero concretos**. El propietario puede sustituir cualquiera de ellos **antes de generar**; una vez generado, el conjunto queda congelado para toda la sesión y para sus eventuales repeticiones (§8.4).

**Por qué son tan específicos:** la dimensión 1 puntúa «adecuación al brief». Un brief que diga «algo alegre con guitarras» hace que D1 no signifique nada — cualquier salida lo cumple. Cada brief de abajo declara **seis ejes verificables** (género, tempo, instrumentación, idioma del canto, duración objetivo y uso final) más el destino de loudness, y esos seis ejes son los que D1 comprueba uno a uno.

| ID | Uso final imaginado | Género / carácter | Tempo | Instrumentación pedida | Voz / idioma | Duración | Destino (§5.5) | Exigencia específica que D1 comprueba |
|---|---|---|---|---|---|---|---|---|
| **B-01** | Cabecera de un vídeo-ensayo de YouTube («Cuaderno de ruido») | Indie-rock luminoso, urgente pero amable | 112 BPM | Batería acústica, bajo eléctrico, dos guitarras eléctricas con *chorus*, sin teclados | Masculina media, doblada en el estribillo · **castellano** | **45 s** con final resuelto (no *fade*) | Streaming | El gancho vocal debe entrar **antes del segundo 15** |
| **B-02** | Maqueta de canción propia («La última parada del 27») | Cantautor / folk-pop melancólico | 84 BPM | Guitarra acústica, contrabajo, batería con escobillas, coros al final | Femenina media, cercana · **castellano** | **3:00** | Streaming | Estructura **verso – estribillo – verso – estribillo – puente – estribillo**, con el puente contrastando de verdad |
| **B-03** | Encargo ficticio: sintonía de un pódcast de divulgación histórica («Voces de piedra») | Folk oscuro / neomedieval, solemne | 96 BPM | Percusión de marco, zanfona o cuerda frotada grave, coro grave de fondo | Masculina grave, casi salmodiada · **castellano** | **30 s** | Broadcast | Debe **seguir funcionando cortada a 10 s** desde el principio |
| **B-04** | Fondo musical de un vídeo de cocina / *lifestyle* | *Bedroom pop* / lo-fi cálido | 92 BPM | Rhodes, caja de ritmos suave, bajo sintético redondo, sin agudos agresivos | Femenina susurrada · **inglés** | **2:00** | Streaming | La voz debe estar presente **sin competir con una locución** superpuesta |
| **B-05** | Créditos finales de un cortometraje («Lo que quedó del verano») | Balada de piano y cuerdas, contenida | 68 BPM | Piano, cuarteto de cuerda, sin percusión hasta el último tercio | Masculina en registro alto, frágil · **castellano** | **2:30** | Broadcast | *Crescendo* en el último tercio y **final que se apaga**, no corte |
| **B-06** | Encargo ficticio: cuña de 30 s de una tienda de bicicletas | Pop electrónico optimista, publicitario | 124 BPM | Sintetizadores brillantes, palmas, bajo sintético, batería electrónica seca | Femenina, enérgica · **castellano** | **30 s exactos** | Broadcast | **Gancho vocal repetible** y espacio en el último tramo para un cierre hablado |
| **B-07** | Tema para partidas de rol grabadas / *stream* («Las minas de Vardhal») | Metal sinfónico ligero, épico | 140 BPM | Guitarras distorsionadas, doble bombo, cuerdas sintéticas, coro épico | Masculina potente, con cuerpo · **inglés** | **2:30** | Streaming | **Estribillo coreable** y sección instrumental identificable en el centro |
| **B-08** | Encargo ficticio: cuña de radio de una feria de artesanía | Cumbia / latin pop luminoso | 100 BPM | Acordeón, güira, bajo eléctrico, guitarra con línea melódica | Femenina, cálida · **castellano** | **40 s** | Broadcast | **Groove estable** de principio a fin, sin bajar la energía a mitad |
| **B-09** | Montaje de fotografías familiar | Soul / R&B lento, cálido | 76 BPM | Órgano Hammond, batería con *groove*, bajo eléctrico, vientos discretos | Femenina con melismas · **inglés** | **2:45** | Streaming | Los melismas no deben comerse la inteligibilidad (cruce directo con D4) |
| **B-10** | Sintonía de presentación de un canal de tecnología | *Synthwave* ochentero | 110 BPM | Arpegios analógicos, batería con reverb de los 80, bajo sintético, *pads* | Masculina procesada (vocoder ligero) solo en el estribillo · **inglés** | **1:30** | Streaming | La voz procesada **solo en el estribillo**; los versos, instrumentales |

**Reparto de la muestra (comprobado):** 6 briefs en castellano / 4 en inglés · 4 destino broadcast / 6 streaming · duraciones de 30 s a 3:00 · 10 géneros distintos, ninguno repetido · 3 encargos ficticios con cliente imaginado, 4 piezas audiovisuales propias, 2 maquetas y 1 pieza de uso personal. La variedad no es adorno: un conjunto homogéneo mide el modelo en un solo punto y **exagera tanto los aciertos como los fallos**.

### 4.1 Las letras

- Las letras de los 10 briefs **las escribe el propietario** antes de generar, o son de **dominio público verificado**. **No se usan letras de terceros protegidas, ni siquiera en evaluación** — es el mismo principio que D-21 convierte en bloqueo duro (`lyrics_declaration`) dentro de C-01, y no hay motivo para relajarlo aquí solo porque el gate del producto aún no esté construido.
- Extensión mínima por brief con duración ≥ 1:30: **dos estrofas y un estribillo**. Para los briefs de 30–45 s: **un bloque cantado completo** con al menos dos frases.
- Cada letra se archiva **literal, en texto plano**, en `01-briefs/` (§10.2): es la **referencia contra la que se calcula el WER** (§6.2). Si la letra que se envía al modelo lleva marcas de sección (`[verse]`, `[chorus]`), la referencia de WER es la versión **sin marcas**.
- **La misma letra se usa para las tres versiones del brief** (propia, Suno y, cuando sea posible, librería). Si la pista de librería es instrumental o tiene otra letra, se anota y **D4 no se puntúa en la pista de librería** — pero **sí en la propia**, que es la que rige el umbral.

### 4.2 El prompt de estilo

Cada brief se traduce a **un único prompt de estilo escrito antes de generar**, derivado de forma mecánica de las columnas de la tabla (género, tempo, instrumentación, carácter). **Ese mismo prompt literal** es el que:

1. se envía a ACE-Step,
2. se envía a Suno (si se usa la línea base, §5.6),
3. se usa como **consulta de búsqueda** en la librería (§5.1),
4. y se usa como **texto de referencia en la medición de CLAP** (§6.1).

**No se reescribe el prompt entre modelos**, ni se afina buscando un resultado mejor. Un prompt distinto por modelo mide la habilidad del propietario escribiendo prompts, no la del modelo.

---

## 5. Procedimiento de la sesión

Lo ejecuta **`T-09`**. La preparación (§5.1–§5.4) es trabajo previo; la sesión de escucha (§5.5) ocurre en un día distinto.

### 5.1 Material: 3 series de 10, y de dónde sale cada una

| Serie | Origen | Cómo se obtiene |
|---|---|---|
| **Propia** | ACE-Step 1.5 en el contenedor de `T-05` | `docker run --gpus all` en **GPU local** (D-29, decisión del 2026-08-18), con el guardarraíl **G-01** `ACE_STEP_REQUIRE_GPU=1` activo para que un entorno mal configurado **falle en el arranque** en vez de degradar al mock. Coste cloud objetivo: **0 €**. Si la GTX 1070 (8 GB, Pascal, sin BF16) resulta impracticable por tiempo de inferencia, se documenta la excepción y se recurre al pod de RunPod, igual que en `T-04` |
| **Suno** | Suno, cuenta personal del propietario | **Opcional y condicionada** — ver §5.6 y §10.4. Mismo prompt literal y misma letra |
| **Librería** | Librería de producción / *royalty-free* que el propietario ya usa o podría usar | **Se elige ANTES de generar nada** (regla anti-sesgo, abajo) |

> ### ⚠️ Regla anti-sesgo en la elección de la línea base de librería
>
> La pista de librería es **la que decide el criterio de no-go**. Si se elige mal, el gate no mide nada. Por eso:
>
> 1. Se selecciona **antes** de generar la serie propia — **nunca después de escucharla**.
> 2. Se busca en la librería **con el prompt de estilo literal del brief** (§4.2) como consulta, más los filtros de tempo/duración que la librería ofrezca.
> 3. Se toman los **3 primeros candidatos plausibles** del resultado y se elige uno **como se elegiría en un encargo real**: el que uno pondría en la pieza. **No el peor que se encuentre.**
> 4. Se anota **origen, identificador, autor, licencia y fecha de descarga** de la elegida y de las dos descartadas.
> 5. **Sesgo declarado:** el propietario elige la línea base contra la que se va a medir a sí mismo. Es el mismo riesgo de independencia que `gobernanza.md` §2.1 acepta por escrito; estas cinco reglas lo acotan, no lo eliminan. Registrar las descartadas permite auditar la elección después.
>
> **Licencia:** la pista de librería debe poder descargarse y escucharse en privado bajo la licencia con la que se obtiene. Si la fuente no lo permite ni siquiera para evaluación privada, **se usa una alternativa *royalty-free* con licencia permisiva** y se anota. Estas pistas **no entran en la biblioteca de trabajo ni se usan en ninguna producción** (S-11, §10).

### 5.2 Cuántas tomas, y cómo se elige la que puntúa

Generar una sola toma y quedarse con ella no refleja el uso real; generar veinte y quedarse con la mejor es hacer trampa. **Simetría fijada de antemano:**

- **3 tomas por brief y por serie.** Tres de ACE-Step (semillas distintas, **todas registradas**), tres de Suno (si se usa), tres candidatos de librería (§5.1).
- La **selección dentro de cada serie** la hace el propietario **comparando solo dentro de esa serie**, sin escuchar aún las otras dos, **al menos 24 h antes** de la sesión de escucha. Es el criterio de trabajo normal: «de estas tres, ¿cuál mandaría?».
- Las **6 tomas descartadas por brief se archivan** en `02-generado/` y `03-lineas-base/` (§10.2). No puntúan y no se citan en el resultado, pero existen: sin ellas, la selección no es auditable.
- **El resto de parámetros de inferencia se congela antes de empezar** (versión del modelo, pasos, *guidance*, *sampler*, duración objetivo, offloading) y es **idéntico para los 10 briefs**. Cualquier ajuste posterior invalida la serie y obliga a regenerarla entera.

### 5.3 Condiciones de escucha (fijadas antes, anotadas en la hoja)

| Parámetro | Regla |
|---|---|
| Sistema | **Uno solo para toda la sesión**, anotado en la cabecera de la hoja (marca y modelo de monitores o auriculares). Preferentemente **por cable**; nada de Bluetooth, cuyo códec varía |
| Nivel de reproducción | **Fijado antes del primer brief y no tocado durante la sesión.** Si hay que subir el volumen para una pista, esa pista tiene un problema de mezcla — y eso lo puntúa D2, no el mando |
| Cadena de audio | **Sin EQ, sin realce, sin *loudness*, sin ecualización de la sala, sin normalización del reproductor.** Reproductor con salida directa |
| Entorno | Misma sala, mismo ruido de fondo, para toda la sesión |
| Fatiga auditiva | **Máximo 5 briefs por bloque** (15 pistas), **≥ 15 min de descanso** entre bloques y **≤ 2 h de sesión total**. Si hace falta un segundo día, se anota y se repiten las condiciones exactas |
| Orden | **Aleatorizado** (§5.4): el orden de los 10 briefs y, dentro de cada brief, el de sus 3 pistas |
| Pasadas | Por brief: **una pasada completa de las 3 pistas sin puntuar** y luego **una segunda pasada puntuando** (§3.6) |

### 5.4 Anonimización y ciego

El evaluador **debe** saber a qué brief responde cada pista — sin eso, D1 no es puntuable. Lo que **no** puede saber es **de qué serie viene**.

1. **Normalización de loudness para comparación justa** — ver §5.5.
2. **Recodificación uniforme:** las 30 pistas se recodifican al **mismo formato, misma frecuencia de muestreo y misma profundidad**, con **todos los metadatos eliminados** (`ffmpeg -map_metadata -1`). Un tag `TSSE` o un códec distinto delata el origen sin necesidad de escuchar.
3. **Nombres opacos:** `B03-x1`, `B03-x2`, `B03-x3`. El brief es visible; la serie, no.
4. **El mapa `x → {propia, suno, libreria}` lo genera un script con semilla aleatoria**, por brief, y se escribe en `05-ciego/mapping.csv` junto con la semilla usada. **Lo genera la máquina, no la mano del propietario**, y el fichero **no se abre** hasta §5.6.
5. **Riesgo residual declarado:** el propietario puede reconocer el timbre de su propio modelo. Es una consecuencia directa e inevitable de la pérdida de independencia que `gobernanza.md` §2.1 acepta. Se acota con (a) el mapa generado por script, (b) las **≥ 24 h** entre la selección de tomas y la sesión, y (c) el orden aleatorizado. **No se puede eliminar, y por eso se escribe aquí.**
6. Si algún oyente externo participa (§5.7), el ciego es **real** para él, y su hoja vale como contraste cualitativo.

### 5.5 Loudness: igualar para comparar

> **Comparar sin igualar el loudness mide sonoridad, no calidad: gana siempre la pista más alta.** La línea base de librería viene masterizada a nivel comercial y aplastaría a cualquier salida de modelo por el simple hecho de sonar más fuerte.

| Cuestión | Regla |
|---|---|
| **Nivel de la sesión** *(propuesto, ratificable en §9)* | Las **30 pistas** se normalizan a **−16 LUFS integrados** con **true peak ≤ −1 dBTP**, medición **EBU R128**, con `ffmpeg loudnorm` **en dos pasadas** (análisis + aplicación) para que la corrección sea exacta y no estimada. El valor exacto medido de cada pista se anota en `04-sesion/loudness.csv` |
| **Qué NO es este número** | **No** es el objetivo de loudness del producto. El de producto es **por destino** (D-23): **broadcast −23 LUFS**, **streaming −14 LUFS**, **stems sin normalizar**. El de la sesión es un nivel **único** para todas, precisamente porque su función es **eliminar** la variable |
| **Sin limitador ni compresión** | La normalización es **solo ganancia** (más el ajuste de true peak). Nada de limitar ni comprimir: eso alteraría D2 |

> ### ⚠️ Deuda declarada — decisión de loudness por destino (D-23)
>
> `gobernanza.md` §2.2.5 exige que **el objetivo de loudness por destino lo decida el propietario en la Fase 0 y quede por escrito antes de G1**. A fecha de hoy **esa decisión no está escrita en ningún sitio y no tiene tarea propia en F2**: `T-20` (F4) *implementa* la parametrización y dice explícitamente que el valor «se decide con el supervisor musical durante F2».
>
> - **Valores por defecto propuestos** (los de D-23, `spec.md`): **broadcast −23 LUFS · streaming −14 LUFS · stems sin normalizar**.
> - **Dueño:** el propietario. **Momento:** **antes de la primera escucha de `T-09`**, en el mismo acto de ratificación de §9.
> - **Efecto sobre este protocolo:** ninguno sobre los umbrales. Los briefs de §4 ya declaran su destino, de modo que el resultado de G1 queda registrado con el destino que le corresponde a cada pista, aunque el nivel **de la sesión** sea uno solo.

### 5.6 Cómo se rompe el ciego — y la variante sin Suno

**Ruptura del ciego (orden estricto, no negociable):**

1. Se completan **todas** las hojas de puntuación de los 10 briefs, incluidas las notas obligatorias.
2. Se exportan las hojas a fichero y se calcula su **SHA-256**, que se anota en la cabecera de la propia sesión y en `06-hojas/hashes.txt`. *(Mismo principio que la cadena de hashes del ledger de la plataforma: barato, verificable y suficiente para que una modificación posterior sea evidente.)*
3. **Solo entonces** se abre `05-ciego/mapping.csv`.
4. Se aplica la aritmética de §8. **Ninguna puntuación se modifica después de abrir el mapa.** Si al ver el mapa el propietario cambia de opinión sobre una pista, **eso no se corrige: se anota como observación** en el resultado, y es en sí mismo un dato sobre la fiabilidad de la sesión.

> ### Variante B — el protocolo **sin** la línea base de Suno
>
> Si el propietario decide **prescindir de Suno** (por prudencia respecto a sus ToS, §10.4, o por cualquier otro motivo), **el gate se ejecuta igual**, sin tocar un solo umbral. Es un cambio de material, no de criterio:
>
> - **Material:** **20 pistas** en vez de 30 — 2 por brief (`propia`, `librería`), anonimizadas y aleatorizadas exactamente igual.
> - **Criterio 1** (7 de 10 con D5 ≥ 4) — **absoluto**, no depende de ninguna línea base. **Intacto.**
> - **Criterio 2** (ninguna dimensión < 3,0) — se calcula sobre las 10 propias. **Intacto.**
> - **Criterio 3** (CLAP ≥ librería en 7 de 10) — se mide **contra librería**. **Intacto.**
> - **Criterio 4** (WER ≤ 15 % / ≤ 25 %) — se mide **solo sobre las propias**. **Intacto.**
> - **Criterio 5, el no-go** (perder en D5 contra **librería** en > 5 de 10) — **es contra librería, no contra Suno. Intacto.**
>
> **Ninguno de los cinco umbrales depende de Suno.** Suno aporta **contexto** — saber a qué distancia está el modelo propio del estado del arte comercial —, y ese contexto es valioso para decidir *qué hacer* tras un `replanteo`, pero **no decide el gate**. Lo que decide es la línea base de librería, que es también la alternativa real: si el modelo propio no supera a lo que ya se puede descargar, la plataforma no aporta.
>
> **Si se ejecuta la variante B**, se anota en la cabecera de la hoja (`líneas base: librería únicamente`) y en `g1-resultado.md`. La ausencia de Suno **no es un defecto de la sesión**; es una decisión registrada.

### 5.7 Oyentes externos informales (recomendado, no obligatorio)

`gobernanza.md` §2.1, mitigación 3. Si participan 1–2 personas con oído (amistades, otros músicos):

- Reciben **el mismo material anonimizado** y **la misma hoja** (§7), con la rúbrica de §3 delante.
- Para ellos el ciego es **real**, lo que hace su hoja especialmente valiosa como contraste.
- **No son evaluadores formales: no bloquean ni desbloquean el gate**, no votan y sus puntuaciones **no entran en el cálculo de §8**.
- **Sus hojas se archivan** junto a la del propietario en `06-hojas/` y se resumen en `g1-resultado.md`. Si divergen de forma sistemática de la del propietario (p. ej. puntúan la serie propia más baja en D5), esa divergencia **se escribe en el resultado** como observación: es exactamente el tipo de información que el modo solo pierde y conviene recuperar cuando se pueda.

---

## 6. Medición de CLAP y WER

Son los **criterios 3 y 4**: números medidos, no opinados. Se calculan **después** de la sesión de escucha (o antes, siempre que **no se miren** hasta que las hojas estén selladas, §5.6) para que no contaminen las puntuaciones de D1 y D4.

### 6.1 CLAP — similitud audio-texto

| Elemento | Definición |
|---|---|
| **Qué mide** | La similitud **coseno** entre el *embedding* de audio de la pista y el *embedding* de texto del **prompt de estilo literal del brief** (§4.2). Es una comprobación objetiva de «esto suena a lo que se pidió» — la contraparte medida de D1 |
| **Qué se compara** | `CLAP(propia_i)` **vs** `CLAP(libreria_i)` para cada brief `i`. Se cuenta en **cuántos de los 10** se cumple `propia ≥ libreria`. **Umbral: ≥ 7** |
| **Qué se publica** | **Los valores brutos de los 20 (o 30) pares**, no solo la cuenta. Un `7 de 10` con diferencias de 0,001 y un `7 de 10` con diferencias de 0,15 son resultados distintos, y el segundo dice mucho más |
| **Herramienta — candidato principal** | **HeartCLAP**, de la familia **HeartMuLa** (`spec.md` §11.1: Apache 2.0, `safetensors`, publicada en Hugging Face). Es coherente con el resto del proyecto: mismo ecosistema que HeartTranscriptor, licencia permisiva, pesos verificables |
| **Herramienta — alternativa** | Un modelo **CLAP de la familia LAION** (`clap-htsat-*`) si HeartCLAP no resulta utilizable. **Condición previa (regla 5 del registry, I-13b): ficha de licencia verificada de la herramienta elegida antes de usarla** — la regla aplica a **todo el pipeline**, no solo a los generadores |
| **Reproducibilidad** | Se anota **modelo, versión, SHA-256 de los pesos, frecuencia de muestreo de entrada, política de ventanas y política de agregación**, y se archiva el script de cálculo junto a los resultados. Sin esos datos, la cifra no es reproducible en G1-bis |
| **Ventanas** | Los modelos CLAP consumen fragmentos de longitud fija. **Regla:** ventanas **no solapadas** que cubren la pista entera, y **media** de las similitudes. Si el modelo elegido impone otra política, **se declara antes de calcular** y se aplica **idéntica a las tres series** |
| **Dónde se ejecuta** | Indiferente: **CPU es aceptable**. Es una medición, no un proceso sensible a latencia, y libera la VRAM de los 8 GB de la GPU local |

> **Dependencia declarada de `T-09`, no un valor inventado:** el **identificador exacto del modelo, su versión, el SHA-256 de sus pesos y la longitud de ventana** **no pueden fijarse hoy** sin ejecutar el entorno de `T-05` y sin la ficha de licencia de I-13b. Este protocolo fija **el procedimiento, la comparación y el umbral** — que es lo que un gate necesita tener escrito antes de escuchar. `T-09` fija los identificadores **antes de calcular la primera cifra** y los archiva en `07-metricas/README.md`. **Lo que no se puede saber hoy se declara pendiente; no se rellena con un número plausible.**

### 6.2 WER — inteligibilidad medida de la letra cantada

| Elemento | Definición |
|---|---|
| **Qué mide** | *Word Error Rate* de la letra cantada: `WER = (S + D + I) / N`, donde `S`, `D`, `I` son sustituciones, borrados e inserciones frente a la letra de referencia, y `N` el número de palabras de la referencia |
| **Sobre qué pistas** | Sobre las **10 propias** — el umbral es sobre el modelo. Opcionalmente sobre las de Suno **como contexto informativo**; **nunca como umbral**. La línea base de librería queda fuera (suele tener otra letra o ser instrumental) |
| **Referencia** | La letra **literal enviada al modelo**, archivada en `01-briefs/` (§4.1), **sin marcas de sección** |
| **Normalización antes de comparar** *(fijada aquí para que no la improvise nadie)* | Minúsculas · sin signos de puntuación · números escritos en palabras · sin marcas de sección ni acotaciones · se conservan las tildes y la «ñ» · las contracciones se dejan tal cual · espacios colapsados. **La misma normalización se aplica a la transcripción y a la referencia** |
| **Herramienta — candidato principal** | **HeartTranscriptor-oss** (base Whisper, ≈ 3 GB, **Apache 2.0 y `safetensors`**, verificado contra fuente primaria el 2026-08-18 — `spec.md` §11.1). Es el que `evaluation.md` §10.2 nombra explícitamente para esta medición |
| **Cálculo** | `jiwer` o equivalente con la definición estándar de WER. Se publica el **WER por pista**, la **media de las 10** y el **peor caso**. **Umbrales: media ≤ 15 % · peor caso ≤ 25 %** |
| **Idioma** | Se transcribe **forzando el idioma declarado del brief** (castellano o inglés, §4). Dejar que el modelo detecte idioma introduce una fuente de error que no es del generador musical |
| **Qué se archiva** | Transcripción literal de cada pista · letra de referencia · texto normalizado de ambas · WER por pista · media y peor caso · modelo, versión, **SHA-256 de pesos** y parámetros de transcripción · el script |

> **Dependencia declarada de `T-09`:** igual que en CLAP, la **versión concreta y el SHA-256 de los pesos** de HeartTranscriptor se anotan al ejecutar, no hoy. Y **una advertencia honesta que conviene tener escrita antes de ver el número**: un WER medido con un transcriptor sobre **voz cantada** no es un WER de voz hablada; el transcriptor **también se equivoca**. Los umbrales del **15 %/25 %** vienen de `evaluation.md` §10.2 y **se aplican tal cual**; si `T-09` observa que el transcriptor falla sobre pistas cuya letra el propietario entiende perfectamente al oírlas, eso **se documenta como observación en `g1-resultado.md`** —y como entrada para calibrar G1-bis— pero **no altera el umbral de esta sesión** (§2, regla de inmutabilidad).

### 6.3 Invariante de seguridad

Todo peso que se descargue para estas mediciones (HeartTranscriptor, CLAP) se carga **exclusivamente desde `safetensors`**, **nunca** vía `pickle`/`torch.load` sobre checkpoints no confiables (D-14, invariante innegociable del proyecto). El **SHA-256 se anota** — verifica integridad, no inocuidad. La regla vale para las herramientas de medición **exactamente igual** que para los generadores.

---

## 7. Hoja de puntuaciones — plantilla

Se rellena **una copia por evaluador** (el propietario y, si los hay, cada oyente externo informal). Se archiva en `06-hojas/` con su SHA-256 (§5.6).

### 7.1 Cabecera de la sesión

| Campo | Valor |
|---|---|
| Evaluador | |
| Papel | `evaluador único (propietario)` / `oyente externo informal (no vinculante)` |
| Fecha de la sesión | |
| Hora de inicio / fin · descansos | |
| Sistema de escucha (marca y modelo) | |
| Conexión | `cable` / `otra (indicar)` |
| Nivel de reproducción fijado | |
| Sala / entorno | |
| Líneas base incluidas | `propia + Suno + librería` / `propia + librería (variante B, §5.6)` |
| Loudness de sesión aplicado | `−16 LUFS int. / ≤ −1 dBTP` (o el ratificado en §9) |
| Modelo evaluado · versión | `ACE-Step 1.5 @ …` |
| SHA-256 de los pesos | |
| Parámetros de inferencia congelados | |
| Semillas de las tomas seleccionadas | |
| Hardware de generación | `GPU local (…)` / `RunPod (excepción documentada)` |
| Guardarraíl G-01 activo (`ACE_STEP_REQUIRE_GPU=1`) | `sí` / `no` |
| Umbrales ratificados con fecha | `sí — ver §9, fecha: ………` / **`no → sesión no válida`** |
| Fichero de mapa ciego (sin abrir) | `05-ciego/mapping.csv` · semilla: |
| SHA-256 de esta hoja **antes** de abrir el mapa | |

### 7.2 Puntuaciones (10 briefs × 3 pistas)

Escala entera **1–5**. Nota de D5 **obligatoria** en todas las filas. **Se rellena sin saber qué serie es cada `x`.**

| Brief | Pista | D1 · Brief | D2 · Mezcla | D3 · Estructura | D4 · Letra | D5 · ¿La usarías? | Nota de D5 (obligatoria) · «¿qué le falta para subir un punto?» |
|---|---|---|---|---|---|---|---|
| B-01 | x1 | | | | | | |
| B-01 | x2 | | | | | | |
| B-01 | x3 | | | | | | |
| B-02 | x1 | | | | | | |
| B-02 | x2 | | | | | | |
| B-02 | x3 | | | | | | |
| B-03 | x1 | | | | | | |
| B-03 | x2 | | | | | | |
| B-03 | x3 | | | | | | |
| B-04 | x1 | | | | | | |
| B-04 | x2 | | | | | | |
| B-04 | x3 | | | | | | |
| B-05 | x1 | | | | | | |
| B-05 | x2 | | | | | | |
| B-05 | x3 | | | | | | |
| B-06 | x1 | | | | | | |
| B-06 | x2 | | | | | | |
| B-06 | x3 | | | | | | |
| B-07 | x1 | | | | | | |
| B-07 | x2 | | | | | | |
| B-07 | x3 | | | | | | |
| B-08 | x1 | | | | | | |
| B-08 | x2 | | | | | | |
| B-08 | x3 | | | | | | |
| B-09 | x1 | | | | | | |
| B-09 | x2 | | | | | | |
| B-09 | x3 | | | | | | |
| B-10 | x1 | | | | | | |
| B-10 | x2 | | | | | | |
| B-10 | x3 | | | | | | |

*(Variante B, §5.6: se eliminan las filas `x3` y quedan 20.)*

### 7.3 Consolidación — se rellena DESPUÉS de romper el ciego

**Serie propia, pista a pista:**

| Brief | Etiqueta ciega | D1 | D2 | D3 | D4 | D5 | ¿D5 ≥ 4? | D5 librería | ¿D5 propia < librería? | WER propia | CLAP propia | CLAP librería | ¿CLAP propia ≥ librería? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-01 | | | | | | | | | | | | | |
| B-02 | | | | | | | | | | | | | |
| B-03 | | | | | | | | | | | | | |
| B-04 | | | | | | | | | | | | | |
| B-05 | | | | | | | | | | | | | |
| B-06 | | | | | | | | | | | | | |
| B-07 | | | | | | | | | | | | | |
| B-08 | | | | | | | | | | | | | |
| B-09 | | | | | | | | | | | | | |
| B-10 | | | | | | | | | | | | | |

**Comprobación de los cinco umbrales:**

| # | Criterio | Umbral | Valor obtenido | ¿Cumple? |
|---|---|---|---|---|
| 1 | Pistas propias con **D5 ≥ 4** | **≥ 7 de 10** | | |
| 2 | Media de D1 · D2 · D3 · D4 · D5 (2 decimales, sin redondear) | **ninguna < 3,0** | D1: … · D2: … · D3: … · D4: … · D5: … | |
| 3 | Briefs con **CLAP propia ≥ CLAP librería** | **≥ 7 de 10** | | |
| 4 | **WER** media / peor caso | **≤ 15 % / ≤ 25 %** | media: … % · peor: … % | |
| 5 | Briefs con **D5 propia < D5 librería** | **≤ 5 de 10** (si > 5 → **NO-GO**) | | |

**Medias de referencia de las líneas base** *(informativas, no umbral)*:

| Serie | D1 | D2 | D3 | D4 | D5 |
|---|---|---|---|---|---|
| Propia | | | | | |
| Suno *(si aplica)* | | | | | |
| Librería | | | | | |

**Veredicto:** `GO` / `NO-GO` / `REPLANTEO` → **se traslada a `g1-resultado.md` con la justificación de §8.**

---

## 8. Regla de decisión

Se aplica **en este orden**, sin margen de interpretación. Todo el cálculo se hace sobre la tabla de §7.3, **después** de romper el ciego.

### 8.1 Paso 0 — validez de la sesión (si falla, no hay veredicto)

La sesión **no es válida** si:

- los umbrales **no estaban ratificados por escrito con fecha anterior** a la primera escucha (§9); **o**
- falta alguna de las pistas (30, o 20 en variante B), o alguna se escuchó fuera de las condiciones de §5.3; **o**
- el mapa ciego **se abrió antes** de sellar las hojas por hash (§5.6); **o**
- alguna puntuación **se modificó** después de romper el ciego; **o**
- los parámetros de inferencia **no fueron idénticos** para los 10 briefs (§5.2).

**Consecuencia:** la sesión se anula y se repite. **Una sesión inválida no produce ni `go` ni `no-go`**: produce una repetición. Anular una sesión es barato; cerrar el gate con una sesión mal hecha cuesta 589 h.

### 8.2 Paso 1 — criterio de no-go (se evalúa el primero, y manda sobre todo lo demás)

> **Si el número de briefs con `D5(propia) < D5(librería)` es mayor que 5 → `NO-GO`.**

Se aplica **antes** que ningún otro criterio y **no admite compensación**: da igual que se cumplan los cuatro restantes. Perder contra la librería en «¿la usarías tal cual?» en 6 o más de 10 briefs significa que **la plataforma no mejora lo que ya se tiene**, y esa es información suficiente para no gastar el resto del presupuesto.

**Si dispara:** veredicto `NO-GO`, se documenta en `g1-resultado.md`, **F4 no arranca** y se abre la decisión de qué hacer (que puede ser abandonar, cambiar de modelo base y repetir G1 con **estos mismos briefs y umbrales**, o replantear el proyecto). Esa decisión es del propietario y **se escribe**; no se toma por inercia.

### 8.3 Paso 2 — los cuatro umbrales de aprobado

Si el paso 1 no ha disparado, se comprueban **los cuatro**, sin ponderaciones ni compensaciones entre ellos:

| # | Criterio | Cumple si |
|---|---|---|
| 1 | Subjetivo principal | **≥ 7** pistas propias con **D5 ≥ 4** |
| 2 | Subjetivo de suelo | **Ninguna** de las 5 medias `< 3,0` (2 decimales, sin redondear) |
| 3 | Objetivo — CLAP | **≥ 7** briefs con `CLAP(propia) ≥ CLAP(librería)` |
| 4 | Objetivo — WER | media **≤ 15 %** **y** peor caso **≤ 25 %** |

### 8.4 Veredicto

| Veredicto | Condición | Qué ocurre |
|---|---|---|
| ✅ **GO** | Paso 1 no dispara **y** se cumplen los **cuatro** criterios del paso 2 | **G1 superado.** `T-09` → `completado`. **F4 queda desbloqueada** (589 h / 35.340 €). El resultado, las hojas y las métricas se archivan. `GO` en G1 **no autoriza ningún uso comercial** (eso es GC-01) |
| ❌ **NO-GO** | Paso 1 dispara | **G1 no superado.** F4 **no arranca**. Decisión escrita del propietario sobre qué hacer con la iniciativa |
| 🟡 **REPLANTEO** | Paso 1 **no** dispara, pero falla **uno o más** de los cuatro criterios del paso 2 | **Única zona intermedia.** Ver §8.5. **No es un `go` con matices: F4 sigue bloqueada** |

**No existen otras categorías.** «Casi», «go condicionado», «go con reservas» **no son veredictos de este gate**. Un `go` que no cumple los cuatro criterios es un `replanteo` con otro nombre, y ese renombrado es exactamente el fallo que `evaluation.md` §10.2 describe cuando dice que «quien está en la sala siempre decide *sigamos*».

### 8.5 Qué es exactamente un `replanteo`

1. **Se documenta qué falló**, criterio por criterio, con los números.
2. **Se formula UNA hipótesis de corrección acotada** y se escribe **antes** de aplicarla. Candidatas naturales: parámetros de inferencia (pasos, *guidance*, duración), **variantes XL de ACE-Step** (`xl-base`/`xl-sft`/`xl-turbo`, si la VRAM local lo permite — hallazgo del 2026-08-18 ya anotado en `T-03`/`T-05`), formulación de los prompts de estilo, o calidad y métrica de las letras.
3. **Se aplica la hipótesis y se repite el gate completo**: mismos 10 briefs, mismas letras, mismos prompts, **mismos umbrales**, mismo procedimiento. Se regenera **solo la serie propia**; las líneas base **no se regeneran** — se reutilizan las ya archivadas, para que la comparación se haga sobre el mismo suelo.
4. **Máximo 2 repeticiones.** Si la **tercera** pasada tampoco supera los cuatro criterios → **`NO-GO`**. Sin este tope, «replanteo» se convierte en un bucle indefinido que gasta el presupuesto sin decidir nada — la versión lenta de no tener gate.
5. **Timebox:** 10 días laborables por pasada (heredado de `evaluation.md` §10.2). En modo solo el calendario es **orientativo** (`gobernanza.md` §2.1, I-01), pero **el tope de 2 repeticiones no lo es**.
6. Cada pasada produce su **propia hoja archivada** y su entrada en `g1-resultado.md`. **No se sobrescribe la anterior:** la secuencia de intentos es parte del resultado.

### 8.6 Relación con el stop-loss

Si el gate entra en repeticiones, **el contador de esfuerzo sigue corriendo**. El stop-loss de `gobernanza.md` §5 (> 60 % del presupuesto de la Fase 1 con < 40 % del alcance entregado → parada y decisión escrita) se evalúa formalmente al cierre de C-13, pero un G1 que necesita tres pasadas es **exactamente la clase de señal** que el stop-loss existe para no ignorar. Se anota en `g1-resultado.md` si se llega a la segunda repetición.

### 8.7 Alcance del veredicto: a qué queda atado, y qué lo obliga a repetirse

> **Decidido el 2026-09-03 (P-01 del ledger), a petición del propietario.** Se decide **antes** de generar, y no con el resultado delante, que es la única forma de que valga.

**El problema.** El gate se va a medir en la máquina de referencia: GTX 1070, `tier3`, con el artefacto convertido a **fp16 porque Pascal no admite bf16**. En un servidor moderno lo correcto es **refundir los mismos pesos en bf16**, lo que produce otro artefacto con otro SHA-256. Si eso contase como «cambio de versión de adapter», migrar reabriría el gate y ejecutarlo ahora sería trabajo a repetir.

**La regla.** El veredicto queda atado al **modelo y su adapter**, identificados por los **SHA-256 de las fuentes upstream** que registra `<artefacto>.provenance.json` por componente — **no** por el hash del artefacto fusionado ni por su dtype.

Esto no es un criterio nuevo: es el que el propio fusor ya declara en su manifiesto («el criterio de identidad real son los `sha256` de las fuentes, no el del artefacto»), porque el hash del artefacto depende de la ruta absoluta del anfitrión y de la marca de tiempo de construcción. Hasta hoy ese criterio no se había conectado con esta pregunta.

Por tanto, **refundir los mismos pesos upstream en otro dtype no es un adapter nuevo**: es el mismo modelo empaquetado para otra tarjeta, y **no** dispara la repetición del protocolo.

**La asimetría, que es lo que hace la regla defendible y no una comodidad.** No se aplica igual en los dos sentidos, y así debe quedar:

| Veredicto en `tier3` | ¿Se transfiere a hardware mejor? | Por qué |
|---|---|---|
| **`GO`** | **Sí** | Hardware mejor solo le da al modelo *más*: más pasos, planificador mayor, sin descarga de componentes. Si ya bastaba en el peor nivel medible, basta a fortiori en uno mejor. |
| **`NO-GO`** | **No** | Condenaría al modelo por la máquina. Un `NO-GO` medido en `tier3` solo dice «no sirve en `tier3`», y obliga a repetir el protocolo en hardware de la clase objetivo antes de concluir nada sobre el modelo. |
| **`REPLANTEO`** | **No** | Mismo motivo: las palancas del replanteo (§8.5) incluyen parámetros que el nivel de GPU limita. |

Esta asimetría ya estaba implícita en el proyecto («un no-go medido en `tier3` no sería válido»); aquí queda escrita como regla del gate.

**Consecuencia práctica: `G1` se puede ejecutar ya**, sin esperar a tener servidor. Si sale `GO`, vale para el servidor. Si sale `NO-GO`, no se pierde el trabajo: se aprende que hay que repetirlo con hardware decente, que es información igualmente y llega antes.

**Lo que esta regla NO cubre**, para que nadie la estire: un **adapter distinto** (HeartMuLa, MiniMax, YuE) sigue exigiendo `G1-bis` completo; una **revisión upstream distinta** de los pesos cambia los `sha256` de las fuentes y por tanto es otro modelo; y la **retención de 12 meses** del material de medida (§10) sigue corriendo, así que un `GO` de hoy deja de ser comparable cuando el patrón se borre.

---

## 9. Ratificación de los umbrales — ANTES de la primera escucha

> ### ⚠️ BLOQUE PENDIENTE — no lo puede rellenar quien redacta el protocolo
>
> **Estado: `pendiente`.** **Dueño: el propietario (Daycry).** **Momento: antes de la primera escucha de `T-09`** — y, preferiblemente, **antes incluso de generar la serie propia**, para que ni siquiera exista la tentación de ajustar un número a la vista del material.
>
> Sin este bloque firmado y fechado, **la sesión no es válida** (§8.1) y su resultado no cierra el gate. Es el mecanismo que sustituye, en modo solo, al contrapeso que en la versión corporativa daban tres evaluadores: **un número escrito y fechado antes de escuchar es más difícil de autoengañar que una impresión** (`gobernanza.md` §2.1, mitigación 1).

**Declaración a firmar:**

> *He leído íntegramente este protocolo. **Ratifico los cinco umbrales del §2 sin modificarlos** y me comprometo a no alterarlos durante ni después de la sesión. **Ratifico los 10 briefs del §4** (o anoto abajo las sustituciones, todas ellas anteriores a cualquier generación). **Declaro que a esta fecha no he escuchado ninguna de las pistas de G1.** Asumo, tal como recoge `gobernanza.md` §2.1, que evalúo lo que yo mismo desarrollo y que esa pérdida de independencia es un riesgo aceptado por escrito, no un defecto ignorado.*

| Campo | Valor |
|---|---|
| Nombre | **Daycry (propietario)** |
| Fecha y hora de la ratificación | ⚠️ **pendiente** |
| ¿Ha escuchado ya alguna pista de G1? | ⚠️ **pendiente** — debe ser `no` |
| Umbrales del §2 ratificados sin cambios | ⚠️ **pendiente** |
| Briefs del §4 ratificados | ⚠️ **pendiente** — indicar sustituciones, si las hay |
| Loudness de sesión ratificado (§5.5) | ⚠️ **pendiente** — propuesto: −16 LUFS int. / ≤ −1 dBTP |
| **Loudness por destino (D-23) decidido y escrito** (`gobernanza.md` §2.2.5) | ⚠️ **pendiente** — propuesto: broadcast −23 · streaming −14 · stems sin normalizar |
| Líneas base que se usarán | ⚠️ **pendiente** — `propia + Suno + librería` o **variante B** `propia + librería` (§5.6) |
| Oyentes externos informales (opcional) | ⚠️ **pendiente** — nombres o `ninguno` |
| Firma | ⚠️ **pendiente** |

### 9.1 Precondiciones de `T-09` (lista de comprobación antes de convocar la sesión)

| # | Precondición | Estado a 2026-09-01 | Dueño |
|---|---|---|---|
| 1 | `T-03`…`T-07` completadas | ⏳ pendientes (F2 no arrancada) | Propietario |
| 2 | **Pesos `safetensors` de ACE-Step 1.5 descargados, ruta y SHA-256 anotados** | ❌ **abierto — `pre-dev-checklist.md` ítem 7 / CS-36. Bloquea el arranque de F2** | Propietario |
| 3 | Contenedor de `T-05` arrancando con `docker run --gpus all` en la GPU local | ⏳ pendiente (`T-05`) | Propietario |
| 4 | Guardarraíl **G-01** (`ACE_STEP_REQUIRE_GPU=1`) en todos los comandos de generación | ✅ regla escrita (`pre-dev-checklist.md` §A) | Propietario |
| 5 | **Ratificación de §9 firmada y fechada** | ❌ **abierto** | Propietario |
| 6 | **Decisión de loudness por destino (D-23) por escrito** | ❌ **abierto** (§5.5, deuda declarada) | Propietario |
| 7 | 10 letras propias escritas y archivadas (§4.1) | ⏳ pendiente | Propietario |
| 8 | 10 líneas base de librería elegidas **antes de generar**, con licencia anotada (§5.1) | ⏳ pendiente | Propietario |
| 9 | Ficha de licencia de las herramientas de medición (CLAP, HeartTranscriptor — I-13b, regla 5) | ⏳ pendiente | Propietario |
| 10 | Decisión sobre la línea base de Suno (usarla bajo responsabilidad personal, o **variante B**) | ⏳ pendiente (§10.4) | Propietario |
| 11 | Carpeta segregada de evaluación creada con su `RETENCION.md` (§10) | ⏳ pendiente | Propietario |

---

## 10. Custodia, retención y ubicación de las pistas (S-11)

`spec.md` **S-11** y `evaluation.md` §10.2 fijan la política. Aquí se concreta.

### 10.1 Reglas

| Regla | Detalle |
|---|---|
| **Carpeta segregada** | Las pistas de G1 (30, o 20 en variante B) **más las de los spikes** viven en una **carpeta de evaluación separada**, **fuera de la biblioteca de trabajo**. No se mezclan nunca con material de producción |
| **Retención: 12 meses** | Desde la fecha de la sesión. Al vencer, **se borran con constancia escrita** (fecha, quién, qué se borró) en `RETENCION.md`. La constancia se conserva aunque el audio no |
| **Manifiesto retroactivo simplificado — solo para las propias** | Por cada pista propia: `modelo@versión` · SHA-256 de los pesos · semilla · prompt de estilo literal · letra · fecha y hora · hardware · parámetros de inferencia. Es **retroactivo y simplificado** porque el manifiesto v1 real llega con C-10a (`T-26`, F5): estas pistas nacen **antes** de que exista el ledger, y una cadena WORM **no admite backfill** (D-20) — de ahí que la trazabilidad de G1 sea documental y no se pretenda otra cosa |
| **Suno y librería: no entran en producción** | **No** se usan en ninguna producción, **ni siquiera personal**; **no** entran en la biblioteca de trabajo; **no** se comparten. Solo existen dentro de la carpeta de evaluación y solo durante los 12 meses |
| **Nada de audio en el repositorio git** | El repo contiene **documentos**, no pistas. Ni las propias (peso) ni, mucho menos, las de Suno o de librería (redistribución de material de terceros). En el repo van este protocolo, `g1-resultado.md`, las hojas y las tablas de métricas |
| **Copia de seguridad** | Si se hace copia, va **a la misma carpeta segregada** y **caduca en la misma fecha**. Una copia que sobrevive al borrado anula la retención |

### 10.2 Estructura de la carpeta

```
<raíz de evaluación>/g1-2026/
  RETENCION.md                 fecha de creación · fecha de borrado (+12 meses) · responsable · constancia de borrado
  01-briefs/                   los 10 briefs, sus letras literales y sus prompts de estilo
  02-generado/propio/          3 tomas por brief (30) + registro de semillas y parámetros
  03-lineas-base/suno/         3 tomas por brief, si se usa la línea base (§5.6)
  03-lineas-base/libreria/     3 candidatos por brief + origen, ID, autor, licencia y fecha
  04-sesion/                   las 30 (o 20) pistas anonimizadas, normalizadas y sin metadatos + loudness.csv
  05-ciego/                    mapping.csv + semilla del aleatorizado  — NO ABRIR hasta §5.6
  06-hojas/                    hojas de puntuación rellenadas + hashes.txt (SHA-256 previos a romper el ciego)
  07-metricas/                 transcripciones, WER por pista, valores CLAP, scripts, versiones y SHA-256 de pesos
  08-manifiestos/              manifiesto retroactivo simplificado de las 10 pistas propias
```

### 10.3 Reutilización en G1-bis y en escuchas de regresión

Todo lo anterior **se conserva mientras dure la retención** porque **G1-bis reutiliza el mismo material**: `gobernanza.md` §2.2.4 y `evaluation.md` §10.2 exigen repetir este protocolo **por cada adapter nuevo** (HeartMuLa) y **en cada cambio de versión de adapter** (escuchas de regresión, métrica de deriva de `spec.md` §12.3). Un G1-bis con **otros** briefs no sería comparable con G1 y no mediría deriva alguna. **Los 10 briefs, sus letras y sus líneas base son el patrón de medida del proyecto**, no material desechable de una sesión.

### 10.4 ⚠️ Línea base de Suno — condición de uso y prohibición explícita

> **Estado: verificación formal de los ToS PENDIENTE.** **Dueño:** el propietario, mediante **consulta legal real**. **Momento:** **gate de comercialización GC-01 §8c** (`gobernanza.md`; `pre-dev-checklist.md` ítem 11 / CS-03; `spec.md` S-11).

`evaluation.md` §10.2 y `spec.md` S-11 pedían verificar los ToS de Suno **antes** de usar su salida como línea base, con 2 h de legal en la semana de G2. **Eso no ha ocurrido y no va a ocurrir antes de G1**: el acta de gobernanza del 2026-09-01 trasladó esa verificación a GC-01. Este protocolo **no la da por cumplida**. Condiciones de uso mientras siga abierta:

| # | Condición |
|---|---|
| **a** | La línea base de Suno se usa **bajo responsabilidad personal del propietario** y **exclusivamente para uso personal** (escuchar y puntuar en una sesión privada de evaluación). Es la misma decisión que `gobernanza.md` §2.2 registra en su nota final |
| **b** | **PROHIBIDO** usar resultados comparados contra esa línea base en **cualquier contexto comercial o con terceros** —presentaciones, propuestas, material de venta, publicaciones, comparativas públicas— **hasta cerrar GC-01 §8c**. La prohibición alcanza a las **cifras derivadas**, no solo al audio: «nuestro modelo puntúa por encima de Suno en X de 10» **no se dice fuera de este repositorio** mientras GC-01 siga abierto |
| **c** | Las pistas de Suno **no entran en la biblioteca de trabajo**, **no se usan en ninguna producción** y **se borran** al vencer la retención de 12 meses (§10.1) |
| **d** | El propietario puede **prescindir de la línea base de Suno** en cualquier momento, incluso el mismo día de la sesión: **el gate se ejecuta igual con la variante B** (§5.6) y **ningún umbral cambia**, porque los cinco se apoyan en la línea base de **librería** — que es, además, la alternativa realmente disponible si la plataforma no se construye |
| **e** | Si GC-01 §8c concluye que los ToS **no** permiten ese uso, **G1 no se invalida retroactivamente**: se anota la conclusión en `g1-resultado.md`, se borran las pistas de Suno y **se marca como no utilizable toda cifra comparada contra ellas**. El veredicto del gate se sostiene por sí solo, porque **nunca dependió de Suno** |

---

## 11. Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-01 | **Creación del protocolo de G1 (`T-08`).** Umbrales de `evaluation.md` §10.2 y `gobernanza.md` §2.2 fijados sin degradación (7/10 con D5 ≥ 4 · ninguna dimensión < 3,0 · CLAP ≥ librería en 7/10 · WER ≤ 15 % medio y ≤ 25 % peor caso · no-go si pierde contra librería en D5 en > 5/10), con regla de inmutabilidad y precisiones aritméticas. **Aportación nueva de esta tarea: la rúbrica de las 5 dimensiones con descriptores por nivel (§3)** — antes la escala 1–5 estaba enunciada pero sin definición operativa, de modo que la interpretaba quien puntuase. Se añaden regla anti-inflación, orden de puntuación y regla de puntuar a la baja. **10 briefs propios realistas redactados (§4), en estado `propuestos — pendientes de ratificación`**, con seis ejes verificables cada uno, letras propias obligatorias y prompt de estilo único compartido por las tres series. Procedimiento de sesión completo (§5): 3 tomas por serie con selección simétrica, elección de la línea base de librería **antes** de generar con cinco reglas anti-sesgo, anonimización con mapa generado por script, condiciones de escucha y fatiga, **normalización de loudness de sesión a −16 LUFS / ≤ −1 dBTP** distinguida del objetivo por destino D-23, y ruptura del ciego con **sellado por SHA-256 de las hojas**. **Variante B sin línea base de Suno (§5.6), con los cinco umbrales intactos.** Medición de CLAP y WER (§6) con herramienta candidata, normalización de texto y qué se archiva; **identificadores y SHA-256 de pesos declarados como dependencia de `T-09`, no inventados**. Hoja de puntuaciones vacía (§7), regla de decisión sin ambigüedad con validez de sesión, no-go primero y `replanteo` acotado a 2 repeticiones (§8), bloque de ratificación pendiente (§9) y política de retención S-11 con estructura de carpeta y prohibición explícita de uso comercial de la línea base de Suno hasta GC-01 §8c (§10). **Tres adaptaciones a modo solo declaradas en §0** (evaluador único sin quórum · briefs propios en vez de producciones de Daycry · ToS de Suno trasladados a GC-01). **Deuda declarada:** la decisión D-23 de loudness por destino, que `gobernanza.md` §2.2.5 exige por escrito antes de G1, **no tiene tarea propia en F2**; queda como precondición de `T-09` (§9.1, ítem 6). | implementer (`T-08`) |
