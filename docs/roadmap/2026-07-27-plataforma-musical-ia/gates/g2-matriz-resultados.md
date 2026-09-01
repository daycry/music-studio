---
documento: gate-g2
titulo: "Gate G2 — Consulta escrita a legal: procedencia y protegibilidad del audio generado por IA"
iniciativa: "Plataforma propia de generación musical por IA (Daycry)"
slug: plataforma-musical-ia
tarea: T-01
estado: resuelto-favorable
fecha: 2026-08-18
resuelto: 2026-08-18
resultado: "Fila 1 de la matriz de §6 — «sí total»"
resuelto-por: "Daycry (7590335+daycry@users.noreply.github.com), propietario de la iniciativa"
timebox: "10 días laborables desde el envío"
spec: ../spec.md
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
destinatario: "Asesoría jurídica de Daycry — ⚠️ interlocutor pendiente"
remitente: "Responsable de la iniciativa — ⚠️ nombre pendiente"
decisor: "Dirección — ⚠️ nombre pendiente"
---

# Gate G2 — Consulta escrita a legal: ¿podemos usar este audio, y podemos venderlo en exclusiva?

> **Estado del documento: `pendiente-de-envio`.** Este texto está redactado para **enviarse tal cual** a asesoría jurídica, una vez rellenados los campos marcados `⚠️ pendiente`. **No contiene ninguna respuesta de legal**: los apartados de respuesta y decisión están deliberadamente vacíos (§10). Lo redacta el equipo técnico; **lo envía una persona** y **lo decide dirección**.
>
> **Campos que hay que rellenar antes de enviar:** interlocutor de legal, responsable de la iniciativa (remitente), decisor por dirección, y fecha de envío en la tabla de §10.

**Documentos de referencia adjuntos a esta consulta:** [`spec.md`](../spec.md) (especificación funcional; §3.2 contrato del registry, §5.1 características), [`evaluation.md`](../evaluation.md) (evaluación y presupuesto; §4 incógnitas, §6.5 construir-vs-comprar, §10.1 gates y matriz, §10.2 protocolo de calidad, §10.7 «la verdad incómoda»), [`tasks.md`](../tasks.md) (ledger de tareas; esta consulta es la tarea `T-01`).

---

> ## 🟢 Gate G2 levantado — 2026-08-18
>
> **Resultado aplicado: fila 1 de la matriz de §6, «sí total».** El propietario de la iniciativa, **Daycry** (7590335+daycry@users.noreply.github.com), comunicó el 2026-08-18 que **legal ya no es un bloqueo** y seleccionó esa fila. Consecuencia: se ejecuta la **Fase 1 completa** según lo ratificado — **656 h / 39.360 € con margen** — sin recorte de alcance ni tope adicional, y la sub-fase F2 del ledger (Fase 0, `T-03` en adelante) queda desbloqueada **por el lado legal**.
>
> ⚠️ **Lo que sigue sin constar por escrito** (deuda de gate, registrada con detalle en §10):
>
> 1. El **informe escrito de asesoría jurídica no está archivado**. Los criterios 1 y 2 de `T-01` («formulada por escrito» y «respondida dentro del timebox») se cierran por decisión del propietario, no por evidencia documental.
> 2. La **pregunta 2 (I-05b — protegibilidad y exclusividad) no tiene respuesta.** No bloquea construir, pero determina **qué se le puede prometer a un cliente**: nadie licencia en exclusiva una obra que puede no estar protegida. Debe trasladarse a la conversación comercial antes de firmar exclusividades.
> 3. Los **ToS de Suno (§5.1) no están verificados.** Sin eso **no se puede usar la salida de Suno como línea base ciega de G1**, y el protocolo de G1 la exige ([`g1-protocolo.md`](./g1-protocolo.md)).
> 4. El **Anexo A (§8.3) no está firmado por dirección.** Es la mitigación documentada del riesgo R-01.
>
> **Este documento se conserva íntegro**, con la consulta y la matriz tal como estaban escritas *antes* de preguntar. Nada se reescribe a posteriori: lo único que se añade es este banner y el registro de §10.

---

## Resumen para quien solo lea esta página

- Daycry estudia construir una plataforma interna de generación musical con IA, con modelos open source alojados por Daycry (self-hosted).
- **Antes de escribir una línea de código** se pide a legal una respuesta escrita a **dos preguntas**: (1) si acepta usar audio generado por modelos cuyos autores **no publican** con qué datos se entrenaron, y (2) si el resultado generado **es protegible y licenciable en exclusiva**.
- ~~**Nada del desarrollo ha empezado ni empezará hasta que haya respuesta.**~~ **Actualizado el 2026-08-18:** el gate se levantó por decisión del propietario de la iniciativa (ver el banner de arriba). El coste de desarrollo consumido hasta ese momento fue de **0 €**. Las **32 h de asesoría jurídica** siguen reservadas y pendientes de consumir si la consulta se formaliza.
- La decisión que depende de la respuesta vale **39.360 €** de presupuesto ya ratificado (Fase 0 + Fase 1), y hasta **97.320 €** si se aprobaran todas las fases del catálogo.
- Las decisiones posibles **ya están pre-acordadas** en la matriz de §6, para no improvisarlas en la reunión de cierre.
- Timebox: **10 días laborables** desde el envío. **Ningún gate se cierra por silencio.**

---

## 1. Qué se pregunta y por qué ahora

**G2 es el único gate de esta iniciativa capaz de anular el 100 % del presupuesto.** Por eso se sitúa en la **semana 0**, antes de la Fase 0 y de cualquier gasto de desarrollo (`evaluation.md` §10.1).

| Concepto | Cifra |
|---|---|
| Presupuesto **ratificado** y ejecutable (Fase 0 + Fase 1, tareas `T-01`…`T-53` + `T-85`) | **656 h base / 39.360 €** con margen |
| Coste de desarrollo **ya consumido** al hacer esta consulta | **0 €** |
| Coste de la consulta | **32 h de asesoría jurídica** (`evaluation.md` §6.5d), fuera del presupuesto de desarrollo |
| Presupuesto en juego si se aprobaran todas las fases del catálogo | 97.320 € |

> **Nota de cifras (para evitar confusión al leer los documentos de origen).** La evaluación (`evaluation.md` §10.1) habla de **38.400 €** para «Fase 0 + Fase 1». La cifra ratificada el 2026-08-18 es **39.360 €**: los 960 € de diferencia son la ampliación de alcance `T-85` (modo de ejecución en GPU local, decisión D-29), aprobada ese mismo día. **Ambas cifras son correctas en su contexto**; la vigente para decidir es **39.360 €**.

**La versión corta del riesgo:** en la revisión inicial de la evaluación este gate legal estaba previsto «antes de producción», lo que habría autorizado gastar entre 33.000 € y 38.400 € **antes de saber si el resultado es utilizable**. G2 no es una entrega de software: es una consulta de dos semanas. Si la respuesta es «no», se habrán gastado **32 h de asesoría jurídica en lugar de 39.360 €**.

**Qué necesita el proyecto de legal:** una **respuesta por escrito**, aunque sea breve y con reservas. No se pide un dictamen exhaustivo ni una garantía absoluta; se pide una **posición** que permita decidir entre construir, comprar o parar. Si la respuesta honesta es «depende del caso de uso», eso ya es una respuesta útil: es exactamente la fila 2 de la matriz de §6.

---

## 2. Contexto técnico mínimo (sin jerga innecesaria)

Este apartado está escrito para alguien que **no conoce el proyecto**. Cinco hechos, y qué significa cada uno.

### 2.1 Qué se quiere construir

Una aplicación web **interna** de Daycry donde un usuario escribe una letra y una descripción de estilo («balada de piano, melancólica, 90 segundos») y obtiene una canción descargable. El modelo de IA que genera el audio **no es un servicio externo**: los ficheros del modelo se descargan y se ejecutan en infraestructura controlada por Daycry (*self-hosted*). El modelo de referencia es **ACE-Step 1.5**, publicado bajo licencia **Apache 2.0**; el segundo previsto es **HeartMuLa**. Solo se integran herramientas cuya licencia permite uso comercial (por eso, por ejemplo, MusicGen está descartado: su licencia es CC BY-NC, no comercial).

### 2.2 La licencia del modelo cubre el software, no los datos con los que se entrenó

Este es el punto central de la consulta y conviene leerlo dos veces:

> **Apache 2.0 cubre los pesos del modelo y su código. No dice nada sobre la procedencia de los datos con los que ese modelo se entrenó.**

Los autores de ACE-Step y de otros modelos abiertos comparables (YuE, entre otros) **no publican el corpus de entrenamiento**. En consecuencia, el registro de procedencia que la plataforma emitirá por cada canción contendrá, **literalmente**, el valor:

```
training_data_declaration: no divulgada
```

No es una omisión de la plataforma ni un campo pendiente de rellenar: es un **campo obligatorio del contrato técnico** (`spec.md` §3.2, `ModelDescriptor`) cuyo valor real, hoy, es «no divulgada» para los modelos disponibles, y así queda escrito en cada generación. El diseño obliga a declararlo en lugar de permitir esconderlo.

### 2.3 Alojarlo en casa no cambia el estatus legal del resultado

**Suno y Udio fueron demandados en 2025 por los datos de entrenamiento, no por el modo de despliegue.** Ejecutar el modelo en infraestructura propia mejora el control, la auditoría y el coste; **no limpia la procedencia del corpus**. Cualquiera que lea este proyecto como «igual que Suno pero legalmente seguro porque es nuestro» lo está leyendo mal, y ese malentendido es precisamente lo que esta consulta quiere evitar (ver Anexo A).

### 2.4 Qué prueba y qué no prueba el registro de trazabilidad (característica C-10a)

La plataforma incorpora, **desde la primera pista generada** (no como añadido posterior), lo siguiente:

- Un **manifiesto de procedencia versionado** por cada generación (con `manifest_schema_version` explícito): qué modelo y versión exactos la produjeron, el hash del fichero de pesos usado, la licencia del modelo, su declaración de datos de entrenamiento, los parámetros y las entradas (letra, prompt de estilo), la **declaración de derechos de la letra** que el usuario firmó, y el linaje si la pista deriva de otra.
- Un **ledger de solo-añadido (append-only) con cadena de hashes**: cada asiento incluye el hash del anterior, de modo que borrar o alterar un registro antiguo rompe la cadena y es detectable.

| Lo que **sí** prueba este registro | Lo que **no** prueba |
|---|---|
| **Auditabilidad**: para cualquier pista, y años después, se puede reconstruir con qué modelo, versión, parámetros y entradas se generó | **No** prueba que el corpus de entrenamiento del modelo sea limpio ni que se obtuviera con licencia |
| **Cadena de custodia**: el registro es íntegro y no reescribible sin dejar rastro | **No** convierte en lícito un uso que no lo sea |
| **Diligencia demostrable**: Daycry puede acreditar qué sabía y qué declaró en cada momento | **No** sustituye una garantía contractual de un tercero (indemnización) |
| **Declaración de derechos de la letra** de entrada, con bloqueo duro en la interfaz | **No** aporta protegibilidad al resultado (eso es la pregunta 2) |

Dicho de forma directa, y esto es una conclusión del propio equipo técnico, no algo que se pida confirmar: **el registro documenta el problema con precisión; no lo resuelve.** Ver el Anexo A.

### 2.5 Qué se hará con el audio generado

Dos escenarios muy distintos, y por eso la pregunta 1 se parte en dos ramas:

- **(a1) Uso interno**: maquetas, referencias musicales para presentar una idea, pistas de trabajo en montajes internos, pruebas de concepto. No sale de Daycry como parte de un entregable.
- **(a2) Producciones comerciales de cliente**: sintonías, cortinillas y música de fondo incorporadas a piezas que se entregan y facturan a un cliente, con las obligaciones contractuales habituales (titularidad, cesión y, a veces, exclusividad).

---

## 3. Pregunta 1 (incógnita I-05) — procedencia: ¿podemos usarlo?

> **Pregunta 1.** ¿Acepta la asesoría jurídica de Daycry, **por escrito**, el uso de audio generado por modelos de IA cuya declaración de datos de entrenamiento es **«no divulgada»**, acompañado del registro de procedencia y del ledger descritos en §2.4?
>
> Se pide la respuesta **por separado** para cada rama:
>
> - **1.a1 — Uso interno** (maquetas, referencias, pruebas; material que no sale de Daycry): **¿sí / no / sí con condiciones?** ¿Qué condiciones?
> - **1.a2 — Producciones comerciales entregadas a cliente**: **¿sí / no / sí con condiciones?** ¿Qué condiciones? ¿Cambia la respuesta si el contrato con el cliente incluye una declaración de que parte del material es generado por IA?

**Por qué se pide separado:** son dos niveles de exposición muy distintos, y la respuesta más probable es «sí a uno y no al otro». Si la respuesta llega fundida en un solo «depende», el proyecto no puede decidir.

**Información adicional que puede condicionar la respuesta, por si es relevante:**

- ¿Hay diferencia si el audio se usa **con** o **sin** letra cantada (instrumental frente a canción con voz)?
- ¿Hay diferencia según el **destino** (emisión en abierto, plataforma, uso corporativo interno del cliente)?
- ¿Requiere legal alguna **cláusula tipo** o **aviso** en los contratos de cliente para el escenario a2?
- ¿Hay algún **dato del registro de §2.4 que legal quiera añadir o modificar** para poder dar el «sí»? Esta es la pregunta más útil de todas: si falta un dato, añadirlo ahora es mucho más barato que después (ver §5.2: el ledger no admite reescritura retroactiva).

**Lo que el proyecto necesita como mínimo:** una posición escrita sobre a1 y sobre a2. Un «sí condicionado a X» es una respuesta perfectamente utilizable, siempre que X esté escrito.

---

## 4. Pregunta 2 (incógnita I-05b) — protegibilidad: ¿podemos venderlo en exclusiva?

> **Pregunta 2.** ¿Es **protegible** por derecho de autor, y por tanto **licenciable en exclusiva** a un cliente, el audio generado por IA **sin intervención autoral humana** significativa?

**Contexto de la pregunta.** En el marco de la UE, una obra requiere una creación intelectual propia de una persona; la música generada **sin intervención autoral humana puede carecer de protección**. La consecuencia práctica es concreta y no es técnica:

> Un cliente que exige **exclusividad** sobre la sintonía de su programa **no la puede obtener** sobre una obra que no está protegida. Y eso es cierto **aunque** legal apruebe la pregunta 1, y **también** si Daycry compra el audio a un proveedor externo con cláusula de indemnización: **nadie puede licenciar en exclusiva lo que no está protegido.**

Por eso G2 lleva dos preguntas y no una: **la primera decide si se puede construir; la segunda, qué se puede vender.** El coste marginal de añadir la segunda es cero (misma consulta, mismas 32 h).

**Sub-preguntas concretas:**

- **2.a** ¿Cuál es la posición de legal sobre la protegibilidad del output puramente generado?
- **2.b** ¿Qué grado de **intervención humana** consideraría legal suficiente para sostener autoría (por ejemplo: letra escrita por una persona, selección y edición del resultado entre variantes, mezcla y edición posterior, arreglo)? Esto tiene traducción directa en el diseño del producto y en lo que se registra por generación: si la intervención humana documentada aporta protegibilidad, **conviene registrarla en el manifiesto**, y decidirlo antes de implementarlo es incomparablemente más barato que después.
- **2.c** ¿Qué **se puede prometer** contractualmente a un cliente hoy: cesión de derechos, exclusividad, exclusividad limitada, o solo un compromiso de no reutilización por parte de Daycry?
- **2.d** ¿Recomienda legal una **cláusula tipo** para los contratos en los que intervenga música generada por IA?

**Aviso sobre el efecto de esta respuesta:** una respuesta del tipo «puede no ser protegible» **no bloquea el desarrollo** (ver fila 4 de la matriz de §6). Cambia lo que el equipo comercial puede prometer, y hay que trasladarlo a la conversación con el cliente **antes** de firmar exclusividades.

---

## 5. Dos encargos menores, dentro de las mismas 32 h

**Estos dos puntos no son preguntas del gate y no condicionan su resultado.** Se incluyen aquí porque caben dentro de las mismas 32 h de asesoría jurídica ya reservadas (`evaluation.md` §6.5d) y porque pedirlos ahora evita dos paradas más adelante.

### 5.1 Verificación de los términos de servicio de Suno (2 h) — supuesto S-11, decisión D-12

**Qué se necesita:** confirmar si los términos de servicio de Suno permiten (a) usar audio generado con Suno como **línea base ciega de comparación** en una prueba de calidad interna, y (b) hacer un **estudio de su interfaz** con fines de referencia funcional de diseño.

**Por qué importa:**

- La prueba de calidad de la iniciativa (gate G1, `evaluation.md` §10.2) compara, a ciegas, 10 pistas generadas por el modelo propio contra 10 de Suno y 10 de la librería de producción que se usó realmente en esas piezas. **Si los términos no permiten ese uso comparativo, G1 pierde una de sus dos referencias y hay que rediseñar el protocolo antes de escuchar, no después.**
- Las pistas de Suno y de librería usadas en esa prueba viven en una **carpeta segregada de evaluación** con retención de 12 meses y **no se usan en ninguna producción** (supuesto S-11).
- Sobre el estudio de interfaz, la posición del proyecto es explícita: se deriva el **modelo de interacción** (flujos, estados, disposición), **no** la identidad visual, que es propia de Daycry (decisiones D-12 y D-12b). Se pide a legal confirmar que ese límite es el correcto.

### 5.2 Reserva de agenda: firma del esquema del manifiesto v1 (decisión D-20)

**Qué se necesita:** que legal sepa desde ahora que, **al inicio de la Fase 1**, deberá **revisar y firmar el esquema del manifiesto de procedencia v1** (los campos concretos que se registrarán por cada generación) **antes** de que se implemente el contrato técnico del registry (característica C-11).

**Por qué es una reserva de agenda y no un trámite posterior:** el ledger es de solo-añadido y **no admite reescritura retroactiva**. El audio generado antes de que exista el esquema firmado quedaría **fuera de la cadena de custodia para siempre**, en el proyecto cuya razón de ser es la trazabilidad. Por eso la firma del esquema es **precondición** de la implementación, no una revisión a posteriori.

**Esto no forma parte de la decisión del gate G2.** Solo requiere que legal bloquee unas horas en la semana de arranque de la Fase 1.

---

## 6. Matriz de resultados pre-acordada (decidida **antes** de preguntar)

> **Por qué esta matriz está escrita antes de tener la respuesta.** Un gate cuya única respuesta prevista es «sí» o «no» no es un gate: **la respuesta más probable de un departamento legal ante esta consulta es intermedia**, y hay que tener la decisión tomada de antemano **para que no la improvise quien esté en la sala** el día del cierre. Cada fila de abajo está pre-acordada y forma parte de esta consulta: quien responda debe saber qué consecuencia tiene su respuesta.

| Respuesta de legal | Decisión pre-acordada |
|---|---|
| **«Sí total»** — vale para uso interno **y** para producciones comerciales de cliente | **Fase 1 completa según esta evaluación: 38.400 €** (cifra vigente ratificada: **39.360 €**, con `T-85`/D-29 — ver la nota de §1). Sigue el plan tal cual. |
| **«Sí solo interno / no para cliente»** — **la respuesta más probable** | **Decisión de dirección entre dos caminos, no continuación automática:** (a) **pivotar a compra** con indemnización contractual (§9 de este documento, `evaluation.md` §6.5b), que es lo que cubre el caso de cliente; o (b) **Fase 1 recortada con tope duro ≤ 20.000 €** y **reevaluación del caso de negocio** antes de cualquier fase posterior — una herramienta interna de maquetación y referencia musical vale mucho menos que una plataforma de producción, y el presupuesto tiene que reflejarlo. |
| **«No»** | **Stop con 0 € de desarrollo gastados.** La iniciativa se reformula en torno a C-09 (fine-tuning sobre catálogo propio licenciado, hoy bloqueada por la incógnita I-03: si existe o no catálogo con derechos de entrenamiento) o se sustituye por la opción de compra (`evaluation.md` §6.5b). |
| **Respuesta a la pregunta 2 (I-05b): «el output puede no ser protegible»** | **No bloquea el build, pero cambia lo que se le promete al cliente.** Se documenta como limitación contractual y se traslada a la conversación comercial **antes** de firmar exclusividades. Afecta igual a la opción de compra: **ningún proveedor puede licenciar en exclusiva lo que no está protegido.** |

**Nota sobre la fila 2.** «Sí solo interno» **no** es una autorización para seguir con el plan completo reduciendo la ambición por el camino. Es un **punto de decisión de dirección** con dos salidas escritas y un **tope duro de 20.000 €** en una de ellas. Si nadie toma esa decisión de forma explícita, el gate no está cerrado.

---

## 7. RACI y reglas de cierre del gate

| Elemento | Definición |
|---|---|
| **Quién convoca** | Responsable de la iniciativa — `⚠️ nombre pendiente` |
| **Quién decide** | **Dirección**, con el informe escrito de legal sobre la mesa — `⚠️ nombre pendiente` |
| **Quién responde** | Interlocutor de asesoría jurídica — `⚠️ nombre pendiente` |
| **Timebox** | **10 días laborables** desde el envío de esta consulta |
| **Escalado** | A **dirección general** si se agota el timebox sin respuesta escrita |
| **Coste de legal previsto** | 32 h (banda 24–40 h), incluidas las 2 h del encargo de §5.1 |

**Reglas comunes a todos los gates de la iniciativa** (`evaluation.md` §10.1):

1. **Ningún gate se cierra por silencio.** Agotado el timebox, se escala; no se interpreta la ausencia de respuesta como aprobación tácita. Ninguna tarea de desarrollo arranca por caducidad del plazo.
2. **El desarrollador no vota** en los gates de calidad (G1, G1-bis) ni en el de adopción (G3). En G2 el desarrollador tampoco decide: prepara la información y ejecuta la decisión.
3. La decisión se registra **por escrito** y se enlaza desde este documento (§10).

**Nombres a rellenar antes de enviar** (los tres son personas reales, no roles genéricos):

| Rol | Nombre | Correo |
|---|---|---|
| Decisor por dirección (cierra G2) | `⚠️ pendiente` | `⚠️ pendiente` |
| Responsable de la iniciativa (convoca y envía) | `⚠️ pendiente` | `⚠️ pendiente` |
| Interlocutor de asesoría jurídica (responde) | `⚠️ pendiente` | `⚠️ pendiente` |

*Rellena estos campos la persona que envía la consulta (responsable de la iniciativa), con el visto bueno de dirección. Los mismos nombres deben quedar en [`gobernanza.md`](./gobernanza.md) §5.*

---

## 8. Anexo A — Aceptación por escrito de la «verdad incómoda» (`evaluation.md` §10.7)

> **Por qué existe este anexo.** El riesgo **R-01** de la evaluación exige que los cinco puntos de `evaluation.md` §10.7 queden **aceptados por escrito antes de aprobar** la iniciativa. No es un trámite defensivo del equipo técnico: es la única forma de garantizar que la aprobación se toma **sabiendo qué se compra y qué no**. Este anexo está redactado para que dirección lo lea y lo firme.

### 8.1 Los cinco puntos

1. **Las Fases 1 y 2 entregan una plataforma con la misma exposición de derechos que Suno: mejor auditada, no más limpia.** El manifiesto de procedencia dirá, literalmente, `training_data_declaration: no divulgada` para ACE-Step y para YuE, porque sus autores no publican el corpus de entrenamiento.

2. **Alojar el modelo en infraestructura propia no cambia el estatus legal del resultado.** La licencia Apache 2.0 cubre los pesos y el código; **no limpia la procedencia de los datos de entrenamiento**. Suno y Udio fueron demandados en 2025 **por los datos**, no por el modo de despliegue.

3. **La única vía a una procedencia realmente limpia es C-09** — fine-tuning sobre catálogo propio licenciado —, que es precisamente lo que la evaluación pone en **no-go**: está bloqueada por la incógnita I-03 (¿existe catálogo con derechos de entrenamiento?) y cuesta 400 h.

4. **Por tanto: si el criterio de legal es «garantizar derechos limpios al cliente», el registro de trazabilidad (C-10) documenta el problema en lugar de resolverlo, y ninguna de las Fases 1 a 3 cumple ese criterio.** Lo cumplirían, cada una a su manera, **la librería de producción actual** (`evaluation.md` §6.5a) o **un proveedor generativo con indemnización contractual** (§6.5b). Estas dos alternativas están evaluadas y comparadas; no se descartan por omisión.

5. **Y hay una segunda verdad incómoda, del otro lado del problema (pregunta 2, I-05b).** Todo lo anterior habla de si Daycry puede **usar** el resultado sin infringir. La pregunta simétrica es si puede **proteger** lo que genera: en la UE, la música sin intervención autoral humana **puede carecer de protección**. Un cliente que exige **exclusividad** sobre la sintonía de su programa **no la puede obtener** sobre una obra no protegible — y eso es cierto **aunque** legal apruebe la procedencia, y cierto **también** si se compra a un proveedor con indemnización.

### 8.2 Lo que sí se compra construyendo

Nada de lo anterior invalida la iniciativa, pero hay que aprobarla sabiendo que lo que se compra es esto y no otra cosa:

- **Auditabilidad real**: para cualquier pista, y años después, se sabe con qué modelo, versión, parámetros y entradas se hizo, en un registro íntegro y no reescribible.
- **Control del modelo**: qué modelo se usa, con qué versión y con qué parámetros lo decide Daycry, no un proveedor que puede cambiarlo sin avisar.
- **Coste marginal por pista casi nulo** una vez construida la plataforma, con música hecha al brief exacto de cada pieza e iteración en minutos.
- **La opción futura de C-09**: si algún día existe catálogo propio licenciado, la plataforma ya estará construida para entrenar sobre él — y esa es la única vía conocida a procedencia limpia.

### 8.3 Bloque de firma

Con la firma de este anexo, dirección declara haber leído y aceptado los cinco puntos de §8.1 y la delimitación de §8.2, **antes** de aprobar la ejecución de la iniciativa.

| Campo | Valor |
|---|---|
| Nombre y cargo | `⚠️ pendiente` |
| Fecha de aceptación | `⚠️ pendiente` |
| Firma o constancia escrita (correo, acta, documento firmado) | `⚠️ pendiente` |
| Observaciones o reservas manifestadas | `⚠️ pendiente` |

*Rellena este bloque la persona que decide por dirección. Mientras esté sin firmar, el riesgo R-01 sigue abierto.*

---

## 9. Acción paralela (no dirigida a legal): dos ofertas con indemnización comercial

**Destinatario de esta acción: el responsable de la iniciativa, no legal.** Se ejecuta **en la misma semana** que la consulta de G2 (`evaluation.md` §6.5b) porque es la única alternativa que compra exactamente el riesgo que motiva el proyecto, sin construir nada — y porque **cuesta una llamada y puede ahorrar hasta 97.320 €**.

**Qué pedir:** dos ofertas de proveedores generativos de nivel empresarial **con cláusula de indemnización contractual** por reclamaciones de propiedad intelectual sobre el output. Precio a verificar (es tarifa negociada, no de catálogo).

**Qué preguntar en las ofertas, además del precio:**

1. **Alcance exacto de la indemnización**: qué cubre, con qué **topes** y qué **exclusiones**. (Las indemnizaciones de este tipo suelen tener ambas cosas; hay que leerlas con legal.)
2. **Exclusividad (pregunta 2 / I-05b)**: ¿la oferta **garantiza exclusividad** sobre el output entregado? Y, sobre todo, **¿sobre qué base jurídica la garantiza, si la obra puede no ser protegible?** Esta pregunta es la que separa una oferta seria de un folleto.
3. **Uso comercial** en producciones entregadas a cliente: ¿está incluido sin restricciones?
4. **Trazabilidad**: ¿qué información de procedencia entrega el proveedor por cada pista?

**Puntos de equilibrio frente a construir** (`evaluation.md` §6.5b):

| Precio del proveedor | Equivale a Fase 1 (**38.400 €**) | A Fases 1+2 (**46.260 €**) | Al catálogo completo (**97.320 €**) |
|---|---|---|---|
| 500 €/mes | 6,4 años | 7,7 años | 16,2 años |
| 1.000 €/mes | 3,2 años | 3,9 años | 8,1 años |
| 2.000 €/mes | 1,6 años | 1,9 años | 4,1 años |

**A favor de comprar:** transfiere el riesgo por contrato, cero desarrollo, cero OPEX, disponible mañana. **En contra:** dependencia de proveedor, topes y exclusiones en la indemnización, ningún control de procedencia ni posibilidad de fine-tuning propio, y no elimina el riesgo — lo reasigna. Además, la motivación declarada de esta iniciativa nace precisamente de un litigio sobre un proveedor generativo.

**Las dos ofertas se archivan aunque no se acepten**: son parte del cierre de la tarea `T-02` (ver [`gobernanza.md`](./gobernanza.md) §4), porque documentan que la decisión de construir se tomó comparando y no por defecto.

---

## 10. Registro de la respuesta

> **Rellenado el 2026-08-18.** El gate se cerró por **decisión del propietario de la iniciativa**, no por un informe escrito de asesoría jurídica archivado. Las filas marcadas `⚠️ pendiente de archivar` son **deuda documental**: no impiden construir, pero deben cerrarse **antes de entregar audio generado a una producción de cliente**.

| Campo | Valor |
|---|---|
| Fecha de envío de la consulta | `⚠️ no consta` — la decisión llegó por vía del propietario de la iniciativa, sin registro de envío formal |
| Interlocutor de legal al que se envía | `⚠️ pendiente de archivar` |
| Fecha límite del timebox (envío + 10 días laborables) | n/a — no se agotó ningún timebox: la decisión se comunicó el 2026-08-18 |
| Fecha de respuesta recibida | **2026-08-18** (comunicación del propietario de la iniciativa) |
| **Respuesta a la pregunta 1 (I-05)** — ¿cuál de las filas de §6? | **Fila 1 — «sí total»**: vale para uso interno **y** para producciones comerciales de cliente |
| Condiciones impuestas por legal a la pregunta 1 (si las hay) | Ninguna comunicada — `⚠️ pendiente de archivar` |
| **Respuesta a la pregunta 2 (I-05b)** — protegibilidad y exclusividad | `⚠️ pendiente` — **sin respuesta**. No bloquea el build; determina qué se puede **prometer contractualmente** a un cliente (ver §4 y Anexo A punto 5) |
| Resultado del encargo §5.1 (ToS de Suno) | `⚠️ pendiente` — **bloquea la línea base ciega de Suno en G1** ([`g1-protocolo.md`](./g1-protocolo.md)) |
| Confirmación de agenda del encargo §5.2 (firma del esquema del manifiesto v1) | `⚠️ pendiente` — es **precondición de `T-26`/`T-27`** en la Fase 1, antes de que se implemente C-11 |
| **Decisión aplicada** (fila de §6) | **Fase 1 completa según el plan ratificado: 656 h / 39.360 € con margen** (`tasks.md` §1). Sin recorte de alcance ni tope adicional |
| **Quién decidió** (nombre y cargo) y fecha de la decisión | **Daycry** (7590335+daycry@users.noreply.github.com), propietario de la iniciativa — **2026-08-18** |
| Enlace o referencia al documento de respuesta de legal | `⚠️ pendiente de archivar` |
| ¿Se agotó el timebox? ¿Se escaló a dirección general? | No |
| Anexo A firmado por dirección (§8.3) | `⚠️ pendiente` — es la mitigación documentada del riesgo R-01 |

**Criterios de cierre de `T-01`** — estado real, sin maquillar:

1. ⚠️ **No consta** que las dos preguntas se hayan formulado por escrito a legal con esta matriz adjunta. El documento existe y está listo para enviarse; el envío no está registrado.
2. ⚠️ **No consta** respuesta escrita de legal, ni escalada. El gate se cerró por decisión del propietario de la iniciativa.
3. ✅ La decisión resultante (**fila 1 de §6**) queda registrada por escrito en la tabla de arriba, con autor y fecha.

`T-01` pasa a `completado` en el ledger porque **el propietario de la iniciativa tiene autoridad para levantar el gate y lo hizo de forma explícita**. Los puntos 1 y 2 quedan como **deuda documental**, enlazada desde `tasks.md`.
