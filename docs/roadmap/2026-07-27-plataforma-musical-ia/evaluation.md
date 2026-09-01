---
titulo: Evaluación — Plataforma propia de generación musical por IA
slug: plataforma-musical-ia
fecha: 2026-07-27
actualizado: 2026-09-01
autor: evaluator
estado: completado
completado: 2026-07-27
prioridad: Alta
spec: ./spec.md
plan: ./improvement-plan.md
generacion:
  fuente: estimado
  motivo: "usage-meter.py no disponible en el entorno de ejecución. Horas y tokens de generación de este documento estimados a juicio, no medidos. Bloque añadido el 2026-09-01 por coherencia con improvement-plan.md y tasks.md."
---

# Evaluación: Plataforma propia de generación musical por IA

> **Cadena de artefactos**
> **Spec**: [`spec.md`](./spec.md) (estado `aprobada`) → **Evaluación** (este documento, `completado`) → **Plan**: [`improvement-plan.md`](./improvement-plan.md) (`en-progreso`, Fase 0 + Fase 1 — sub-fase F1 activa)
>
> Este documento sirve para **decidir**, no para ejecutar. El plan paso a paso lo genera `planner` sobre las características que se aprueben.
>
> **Revisión 2 (2026-07-27)** — incorpora las correcciones de una auditoría independiente. La aritmética de la revisión 1 era correcta, pero el **criterio** tenía cuatro fallos graves: el gate legal estaba después de gastar 22.800 €, faltaba la comparación construir-vs-comprar de la decisión de 65.040 €, el gate de calidad G1 no tenía ningún número, y los cimientos estaban subestimados por debajo de su suelo. Consecuencia: **la estimación sube de 1.084 h a 1.566 h base** y la Fase 1 de 22.800 € a **33.000 €**. Cambios detallados en §13.
>
> ✅ **Revisión 3 (2026-07-27) — el estado sigue siendo `completado`; las cifras nuevas fueron ratificadas por el usuario el 2026-08-18.** Dos auditorías más (coherencia y adversarial de **secuenciación**) encontraron que el problema de la revisión 2 no era la aritmética ni el criterio económico, sino **el orden**: toda la trazabilidad estaba en la Fase 2 mientras la Fase 1 generaba audio sin ledger (y **una cadena WORM no admite backfill**), G1 era **inejecutable** tal como estaba escrito, no había gate de derechos sobre la **letra** de entrada, el esquema no modelaba **linaje**, y los gates no tenían **gobernanza ni matriz de resultados**. Consecuencia: **1.566 → 1.622 h base** (81.100 € · **97.320 €** con margen) y **Fase 1 de 33.000 € → 38.400 €** (banda **32.940–44.040 €**), porque entra **C-10a** y cinco huecos de alcance que estaban fuera de presupuesto. Lo aprobado el 2026-07-27 fueron 33.000 €; ✅ **la cifra nueva (38.400 €) fue ratificada por el usuario el 2026-08-18.** Detalle en §13.

---

## 1. Cuadro de mando

| Campo | Valor |
|-------|-------|
| **Spec de origen** | [`docs/roadmap/2026-07-27-plataforma-musical-ia/spec.md`](./spec.md) |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) — `en-progreso`, Fase 0 + Fase 1 (2026-08-18; sub-fase F1 activa desde 2026-08-18) |
| **Estado** | **completado** (2026-07-27) — spec `aprobada`, ciclo PM cerrado. **Revisión 3 ratificada el 2026-08-18** |
| **Prioridad** | Alta |
| **Características evaluadas** | **14** = **10 del usuario** (C-01…C-10) + **4 transversales** (C-11 registry, C-12 auth, C-13 cimientos, C-14 infra GPU). Se presupuestan como **15 fichas**: C-10 se parte en **C-10a** (Fase 1) y **C-10b** (Fase 2) por irreversibilidad del ledger (D-20) |
| **🎯 Cifra que se pide aprobar** | **39.360 €** — Fase 0 + Fase 1 **incluyendo C-10a** y la **ampliación GPU local** (`T-85`/D-29, +960 €, ratificada el 2026-08-18), con margen (banda realista **33.900–45.000 €**). *Revisión 3: eran 33.000 € → 38.400 €; con `T-85`: 39.360 €* |
| **Escenario de catálogo completo** (referencia, **no** es la petición) | **1.638 h base / 81.900 €** · **1.965,6 h / 98.280 €** con margen del 20 % *(incluye las +16 h de `T-85`/D-29)* |
| **Coste con ejecución asistida por IA** (catálogo completo, con margen) | **7.356 €** de supervisión humana + **1.151 €** de tokens (precio verificado, §9.1) + infraestructura |
| **Previsión de tokens** | **122,61 M input / 17,17 M output** (base, sin margen) *(no incluye el delta de `T-85`, efecto ≪ 1 % — ver nota de §8)* |
| **Coste de infraestructura GPU recomendado** | **≈ 128 €/mes** (**un** pod caliente en horario laboral `Europe/Madrid`, L40S RunPod, + un pod efímero bajo demanda) · ≈ 63 €/mes en neo-cloud barato · ≈ 45 €/mes solo con keep-warm |
| **Coste de almacenamiento** | **≈ 0,7 €/mes** el mes 1 → **≈ 8 €/mes** el mes 12 con la política recomendada; **62 €/mes** el mes 12 sin ella (§6.6) |
| **OPEX de mantenimiento** (hoy no presupuestado) | **≈ 7.100 €/año** sobre Fases 1+2 · ≈ 14.700 €/año sobre el catálogo completo (§6.5c) |
| **Horas de no-desarrollo** (hoy a cero) | **116 h** de legal, DPO y supervisor musical (§6.5d) — **no son horas de desarrollo y no están en las 1.638 h** |
| **Veredicto** | **Go condicionado, y el primer paso no cuesta desarrollo.** Gate legal **G2 en la semana 0**, antes de gastar, **con dos preguntas** (I-05 e I-05b) y **matriz de resultados pre-acordada**. Después: Fase 1 (**39.360 €**, incl. `T-85`) go · Fase 2 (**7.860 €**) go condicionado · Fase 3 (16.560 €) en revisión tras **G3 de adopción** · Fase 4 (34.500 €) **no-go**. **Condiciones nuevas del go:** supervisor musical **nombrado** y **3–5 usuarios piloto nombrados** con ≥ 2 h/semana (I-20). |

---

## 2. Resumen ejecutivo

La iniciativa es **técnicamente viable**, pero el alcance declarado no es un MVP y la primera estimación se quedó corta en los cimientos.

**Los números, con las bases declaradas.** Las **10 características que marcó el usuario** (C-01…C-10) suman **1.110 h / 55.500 €** base. Las **cuatro transversales sin las que ninguna de las diez existe** (C-11 model registry, C-12 autenticación, C-13 cimientos de plataforma, C-14 infraestructura GPU) suman **528 h / 26.400 €** *(incluidas las +16 h de `T-85`/D-29 en C-14, ampliación ratificada el 2026-08-18)*. Juntas: **1.638 h / 81.900 €** base, o **1.965,6 h / 98.280 €** con el margen de contingencia del 20 %. Eso son **≈ 12,3 meses de una persona a jornada completa**, o **≈ 735 h de reloj** en ejecución asistida por agentes. No es una fase 1: es un producto maduro, comparable en superficie funcional a Suno, para **1–5 usuarios internos**.

> **Corrección de la revisión 1.** El resumen anterior afirmaba que «las 10 características marcadas como fase 1 suman 1.084 h (54.200 €)». Era **falso**: mezclaba las 10 del usuario con las 4 transversales en una sola cifra. Y las 1.084 h estaban además subestimadas. Ahora las dos bases van separadas, siempre.

**El primer paso de este proyecto no es software.** Es una consulta de dos semanas a legal (**gate G2**, §10.1: consulta + timebox de decisión, como la fila de §9.4). El self-hosting no limpia la procedencia del output: Apache 2.0 cubre pesos y código, no los datos de entrenamiento. El manifiesto de C-10 dirá `training_data_declaration: no divulgada` para ACE-Step y para YuE, porque sus autores no publican el corpus. Es el **único gate capaz de anular el 100 % del presupuesto**, y en la revisión 1 estaba programado *después* de gastar 22.800 €. Ahora va primero, y cuesta cero horas de desarrollo.

**La verdad incómoda, dicha entera** (§10.7): las Fases 1 y 2 entregan una plataforma con **la misma exposición de derechos que Suno** — mejor auditada, no más limpia. La única vía a procedencia realmente limpia es C-09 (fine-tuning sobre catálogo propio licenciado), que es precisamente lo que esta evaluación recomienda **no** hacer ahora. Si el criterio de legal es «garantizar derechos limpios al cliente», C-10 **documenta** el problema en lugar de resolverlo.

**Dónde está el dinero, y dónde no.** Con 100–1.000 generaciones al mes, el coste de GPU es ruido: **45–128 €/mes**. Una GPU dedicada 24/7 tendría una utilización del **5,79 %** sobre segundos de GPU útiles (**9,3 %** sobre horas de pod facturadas). El debate de infraestructura **no es donde está el dinero de este proyecto**: está en las horas de las cinco características más caras. Lo que sí faltaba en la revisión 1 era comparar **7 opciones de GPU para una decisión de 5–48 €/mes** —las cifras que la propia revisión 1 manejaba— **y cero opciones para la decisión de 65.040 €**, que era su total con margen. Esa comparación está ahora en §6.5, y no es cómoda: los **98.280 €** del catálogo completo equivalen a **≈ 27 años** de una suscripción enterprise de librería de producción a 300 €/mes, y un proveedor generativo con **indemnización comercial contractual** compra exactamente el mitigante de riesgo que motiva la iniciativa sin construir nada.

**Las tres características que concentran el riesgo** (715 h, 35.750 € base, el **44 %** del presupuesto) *(la revisión 2 escribía «575 h, 28.750 €, 37 %» y a continuación listaba tres características: 575 h eran solo C-09 + C-04. Corregido)*: 

- **C-09 Fine-tuning propio (400 h, 20.000 €)** — reestimada al alza desde 200 h, porque un pipeline de dataset con captioning, arnés de entrenamiento, tracking y protocolo de evaluación no cabe en 200 h. La reestimación **refuerza** la recomendación de aplazarla: está bloqueada por I-03 (catálogo licenciado) y por I-01 (no consta perfil ML).
- **C-04 Clonación de voz (175 h, 8.750 €)** — RGPD y biometría, consentimiento, borrado efectivo del derivado, watermarking y bucle de evaluación.
- **C-07 Extender/regenerar secciones (140 h, 7.000 €)** — el editor de forma de onda con regiones es media característica por sí solo.

Frente a eso, hay un **walking skeleton de 656 h (32.800 € base / 39.360 € con margen, incluida la ampliación GPU local `T-85`)** que ya entrega valor real. Es el **40 %** del presupuesto para el 100 % de la propuesta de valor central. **La estimación de la revisión 1 (22.800 €) no cubría esa fase ni en su suelo, y la de la revisión 2 (33.000 €) tampoco**, porque dejaba fuera la trazabilidad mínima (C-10a), el gate de derechos de la letra, el linaje del esquema y la matriz de capacidades del spike — cuatro cosas sin las que la Fase 1 **no se puede entregar**, no cuatro mejoras.

> **Lo que la revisión 3 cambia, en una frase.** No es un problema de precio: es que **el orden estaba mal**. La Fase 1 iba a generar audio durante ≥ 2 semanas sin ledger de procedencia, y **una cadena WORM no admite backfill**: ese audio habría quedado fuera de la cadena de custodia **para siempre**, en el proyecto cuya razón de ser es la trazabilidad. Adelantar **C-10a** a la Fase 1 cuesta 38 h; no adelantarlo no cuesta nada y arruina el entregable.

---

## 3. Requerimientos recibidos

| ID | Requerimiento | Sección de la spec | Estado |
|----|---------------|--------------------|--------|
| C-01 | Generación a partir de letra + prompt de estilo | §5.1, §5.2, §4 | Claro, **con un hueco cerrado en la revisión 3**: aceptaba **cualquier letra sin declaración de derechos** mientras C-08 sí exigía titularidad del audio. Ahora lleva gate de derechos de la letra (D-21, +8 h) |
| C-02 | Instrumental sin voz | §5.1, §5.2 | Claro |
| C-03 | Selector de tipo de voz (timbre, género, registro) | §5.1, §5.2 | **Ambiguo**: los modelos disponibles no exponen mandos limpios de timbre/registro; el control es indirecto y hay que definir qué se le promete al usuario |
| C-04 | Clonación de voz propia | §5.1, §11.2 | **Incompleto**: falta política de consentimiento, retención y base jurídica (RGPD/biometría) |
| C-05 | Asistente IA de letras | §5.1 | Claro |
| C-06 | Descarga de stems separados | §5.1 | Claro |
| C-07 | Extender / regenerar secciones concretas | §5.1, §3.3 | **Ambiguo**: el soporte de inpaint/continuación varía por modelo; puede no estar disponible en el elegido |
| C-08 | Cover / remezcla de una pista existente | §5.1 | **Incompleto**: falta la política de derechos del material que sube el usuario |
| C-09 | Fine-tuning de modelos propios | §5.1, §3.2, §11.1 | **Bloqueado**: depende de I-03 (catálogo licenciado) y de I-01 (perfil ML) |
| C-10 | Trazabilidad de licencias y derechos del audio generado | §5.1, §3.2, D-07, **D-20** | Claro en el qué; **el criterio de aceptación lo pone legal** (I-05). **Watermarking: candidatos MIT identificados (SilentCipher/AudioSeal), robustez en música por validar** (I-13). **Partida en la revisión 3**: **C-10a** (38 h, Fase 1 — esquema firmado, manifiesto desde la primera pista, ledger con cadena de hashes, `manifest_schema_version`) y **C-10b** (67 h, Fase 2 — C2PA, WORM, PDF, watermarking) |
| C-11 | Model registry pluggable | §3.3, D-02, D-16 | Claro, y **recortado a lo defendible en fase 1** (fuera: router de capacidades y formulario dinámico) |
| C-12 | Autenticación SSO social + usuario/contraseña + 2FA configurable | §5.1, D-08 | Claro. **Estaba inflado**: reestimado de 48 h a 28 h |
| C-13 | Cimientos de plataforma | §3.2 | **Derivado**: no estaba en la lista del usuario, pero ninguna de las 10 existe sin esto. **Estaba subestimado**: 120 h → 190 h (rev. 2) → **214 h** (rev. 3: linaje D-22, 48 kHz y loudness por destino D-23, compartición D-24, i18n D-25, stop-loss D-28) |
| C-14 | Infraestructura GPU y orquestación de inferencia | §3.1, §3.2, D-05, D-05b, **D-26** | **Derivado + decisión abierta**: el usuario pide comparativa (§6). **Estaba subestimado**: 80 h → 120 h (rev. 2) → **123 h** (rev. 3: medición de 2 inferencias concurrentes en la L40S) |
| — | **Hardware de ACE-Step: RTX 4090/5090, 24 GB de confort, offloading con menos** | §8 conf. 10, §11.1, §11.3 | **Información nueva del usuario.** No contradice el mínimo de 8 GB: 8 GB es el suelo con offloading, 24 GB la cifra de confort. Afecta a la elección de GPU (§6.2, opción H) |
| — | **La UX debe ser equivalente a la de Suno**, con estudio de su interfaz en implementación | §8 conf. 11, D-12, D-12b | **Información nueva del usuario.** Registrada como referencia funcional. Nota de PI: derivar el modelo de interacción es de bajo riesgo; copiar la identidad visual no (§11, R-20) |

**Nota de alcance.** Las cuatro transversales **no eran opcionales**: C-12 es requisito explícito del usuario; C-13 y C-14 son requisitos implícitos sin los que no hay plataforma. Presupuestarlas por separado es lo que hace comparable el resto — y lo que impide volver a escribir «las 10 suman 1.622 h», que sería falso otra vez.

**Nota de secuenciación (revisión 3).** Tres requisitos que la spec ya prometía **no tenían sitio en ninguna fase** y por eso no estaban presupuestados: el **manifiesto de procedencia** que el criterio de aceptación de C-01 (Fase 1) exigía vivía entero en la Fase 2; el **linaje de variantes** que el flujo de §4 promete en la Fase 1 no existía en el esquema hasta C-07 (Fase 3); y la **matriz de capacidades** que decide si C-07 y C-08 son viables se iba a descubrir **en la Fase 3, con 276 h ya comprometidas**. Un requisito prometido y no planificado no es alcance ahorrado: es alcance que aparece tarde y caro.

---

## 4. Datos necesarios (pendientes de respuesta)

| # | Dato | Bloquea | Criticidad |
|---|------|---------|-----------|
| **I-05** | **Posición de legal sobre la procedencia del audio generado** con modelos cuya declaración de datos de entrenamiento es «no divulgada» | **Gate G2, semana 0. El 100 % del presupuesto.** Es lo primero que hay que preguntar | **Crítica** |
| **🆕 I-05b** | **¿Es protegible y licenciable en exclusiva el output generado por IA sin autoría humana?** En la UE la música sin intervención autoral humana **puede carecer de protección** | **Segunda pregunta del mismo gate G2**, coste marginal cero (mismas 32 h de legal). Determina qué se puede **prometer contractualmente** a un cliente: quien exige exclusividad no la puede obtener sobre una obra no protegible, **aunque legal apruebe la procedencia** | **Crítica** |
| **🆕 I-20** | **¿Quién es el supervisor musical nombrado y quiénes son los 3–5 usuarios piloto** con ≥ 2 h/semana comprometidas? | **Condición del veredicto**, no un detalle del plan: sin supervisor musical **G1 no existe**; sin usuarios piloto **G3 no se puede medir** y la Fase 2 se construye a ciegas | **Crítica** |
| I-01 | Tamaño y composición del equipo. **¿Hay un ML engineer? ¿Hay más de una persona?** | Todo el calendario (§9.4) y la viabilidad de C-03, C-04, C-09. Riesgo de persona clave (R-15) | **Crítica** |
| I-03 | ¿Existe catálogo musical licenciado con derechos de entrenamiento? | **C-09 al completo** — y con ella, la única vía a procedencia limpia | **Crítica** |
| I-13 | **¿Qué librería de watermarking es robusta a transcode a MP3 320 y tiene licencia comercial limpia?** **🆕 Hallazgo 2026-08-18 (verificado):** dos candidatos con licencia MIT (código y pesos) — **SilentCipher** (Sony, robusto a MP3/OGG/AAC, umbral psicoacústico, mensaje 40 bits) y **AudioSeal** (Meta, MIT desde abril 2024, pensado para voz, robustez en música por validar). **No se cierra**: falta la prueba de robustez sobre música transcodificada, prevista en F10 (`T-57`) | **C-10b** y C-04. **Riesgo de licencia circular**, rebajado: pasa de «sin solución identificada» a «candidatos con licencia MIT, robustez en música por validar» contra la regla 5 del propio registry | **Alta** |
| **🆕 I-13b** | **Ficha de licencia verificada de TODA herramienta del pipeline**, no solo de los generadores: **pesos de Demucs** (código MIT, **modelos con términos no comerciales**), **RVC** (licencia confusa), **HeartCodec / HeartTranscriptor**. **🆕 Hallazgo 2026-08-18 (confirmado, issue #327 de `facebookresearch/demucs`):** los pesos de Demucs (htdemucs/htdemucs_ft/htdemucs_6s) son **CC-BY-NC 4.0** — código MIT, pesos no comerciales. Candidatos alternativos por verificar: MDX-Net (UVR5), Mel-Band RoFormer con pesos MIT | El watermarking no es el único punto de licencia circular: **Demucs es C-06 (Fase 2) y RVC es C-04**. Cada fase se abre con la ficha de sus herramientas (**4–6 h por fase**, dentro de las horas de la característica que las integra) | **Alta** |
| I-11 | **Presupuesto máximo aprobado** | Determina la segmentación en fases y si la decisión de §6.5 es de compra o de construcción | Alta |
| I-02 | ¿Daycry tiene GPUs propias o capacidad GPU en su cloud corporativo? | Cierre de la decisión de infraestructura (§6) | Alta |
| I-07 | Tiempos reales de inferencia por modelo y GPU, **y VRAM pico con y sin offloading** | Precisión del coste (S-02) y elección de GPU. Se cierra en el spike de Fase 0 | Alta |
| I-16 | **¿Quién es el propietario operativo tras la entrega?** | OPEX de mantenimiento: ≈ **7.100 €/año** sin dueño ni partida (§6.5c) | Alta |
| I-14 | Precio de una GPU cloud de 24 GB (RTX 4090/5090) en el proveedor elegido | Opción H de §6.2: puede reducir el coste GPU a la mitad | Media |
| I-15 | **Plan de entornos** dev/stage/prod: cuántos, dónde y con qué coste | Coste de infraestructura no-GPU, hoy sin presupuestar (§6.7) | Media |
| I-18 | **Tarifa interna de las horas de no-desarrollo**: supervisor musical, legal, DPO | Convierte en euros las 116 h de §6.5d | Media |
| I-04 | ¿Es obligatoria la integración con MAM u otros sistemas internos en fase 1? | Alcance no presupuestado | Media |
| I-08 | Coste real de object storage, egress y política de retención corporativa | Coste operativo a 24 meses (§6.6 lo calcula a tarifa S3 de referencia) | Media |
| I-09 | Latencia máxima aceptable de extremo a extremo | Valida o invalida la postura de GPU y el gasto de ≈ 83 €/mes del pod caliente (§6.4) | Media |
| I-10 | ¿Política corporativa que exija watermarking? | Prioridad de C-10 y del componente de marca | Media |
| I-12 | Idiomas requeridos para el canto | Elección de modelo (HeartMuLa para multilingüe) | Media |
| I-17 | Política corporativa de retención de logs y datos personales | Configuración de observabilidad y RGPD | Media |
| **🆕 I-19** | **Idiomas de la interfaz** más allá del castellano (catalán, inglés) | Alcance de i18n en Fase 2. La Fase 1 arranca con `next-intl` (D-25), así que añadir idioma es traducir, no refactorizar | Baja |
| ~~I-06~~ | ~~Precio vigente de tokens~~ | ✅ **CERRADA el 2026-07-27.** Verificado contra la documentación oficial: Claude Opus 5 a **5 $/M input · 25 $/M output**, escrito en `.claude/rates.json`. Coste real: **1.151 €** con margen (§9.1, recalculado en la revisión 3 sobre 1.622 h) | — |

Mientras **I-05** e **I-05b** no tengan respuesta, **nada debe empezar**. Mientras **I-20** no tenga respuesta, **la Fase 1 no se aprueba** (sin supervisor musical no hay G1 y sin usuarios piloto no hay G3). Mientras **I-03** no tenga respuesta, **C-09 no se puede planificar**.

---

## 5. Supuestos económicos

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Tarifa de desarrollo | **50 €/h** | `.claude/rates.json` (confirmada por el usuario) |
| Moneda | EUR | `.claude/rates.json` |
| Modelo IA asumido | `claude-opus-5` | `.claude/rates.json` |
| Precio de tokens input/output | **5 $/M · 25 $/M** ✅ verificado 2026-07-27 | `.claude/rates.json`, contra la [documentación oficial](https://platform.claude.com/docs/en/about-claude/pricing). Claude Opus 5, precio estándar (sin batch ni caché) |
| Tipo de cambio | **1 USD = 0,92 €** | `.claude/rates.json` |
| Ratio de supervisión | **25 % de las horas IA** | `.claude/rates.json`. Sensibilidad en §9.3: en investigación y escucha lo realista es el 50 % |
| Margen de contingencia | **+20 %** sobre horas base humanas e IA | `.claude/rates.json` |
| Jornada | 8 h/día, 40 h/semana | `.claude/rates.json` |
| Horas/FTE-mes | 160 h | `.claude/rates.json` |

**Métodos de estimación empleados:**

- **Horas humanas**: descomposición por característica en subsistemas identificables (cada ficha de §7 lleva su desglose), **punto medio de un rango explícito**, sin colchón. El margen se aplica después y por separado. El rango de cada característica está declarado en su ficha y agregado en §8. **Excepción declarada (2026-09-01):** en **C-03 y C-08** el valor central **no** es el punto medio aritmético de su rango — el rango se sesga deliberadamente al alza (48–80 y 68–110 h) por su confianza baja, como ya justifica la nota de §8 sobre el sesgo de las estimaciones de confianza baja; se declara aquí para que el método aplicado y el declarado coincidan.
- **Horas IA**: ratio `horas_IA / horas_humanas` según la naturaleza del trabajo — **0,15** para boilerplate, UI, CRUD e integraciones estándar; **0,20–0,25** para lógica de dominio e integración de modelos; **0,30–0,45** para investigación ML, tuning y evaluación empírica (poco automatizable: exige ciclos de GPU y escucha humana).
- **Tokens**: supuesto parametrizado de **250.000 input y 35.000 output por hora de agente**. `⚠️ Es un supuesto, no una medición`; escala linealmente si se recalibra.
- **Coste de GPU**: precios verificados de julio 2026 (spec §11.3) sobre el supuesto S-02 (**150 s de GPU por pista entregada**). **Debe medirse en el spike de Fase 0**; todo el §6 escala linealmente con él.
- **Factor de facturación de GPU**: **1,90×** sobre el tiempo útil (S-02b), no 1,60×. La revisión 1 usaba el extremo optimista de su propio supuesto de arranque en frío. Desglose en §6.4.

**Por qué esta revisión sube las horas.** El margen de contingencia del 20 % es un colchón para imprevistos, **no un sustituto de estimar bien**. Cuatro características estaban por debajo de su suelo defendible y dos por encima:

| Característica | Rev. 1 | Rev. 2 | Δ | Motivo |
|---|---|---|---|---|
| C-13 Cimientos | 120 h | **190 h** (160–220) | +70 | Son 8–12 subsistemas, no uno |
| C-11 Model registry | 72 h | **130 h** (110–150) | +58 | Contenerizar ACE-Step y HeartMuLa ya son 40–60 h |
| C-14 Infra GPU | 80 h | **120 h** (100–140) | +40 | 56 h netas no dan para multiproveedor + circuit breaker + failover |
| C-01 Generación | 48 h | **70 h** (60–80) | +22 | Es la superficie de producto completa |
| C-10 Trazabilidad | 72 h | **105 h** (90–120) | +33 | C2PA real (firma, certificados, cadena de confianza) + watermarking + PDF |
| C-07 Secciones | 96 h | **140 h** (120–160) | +44 | El editor de forma de onda con regiones ya es media característica |
| C-04 Clonación de voz | 120 h | **175 h** (150–200) | +55 | RVC + consentimiento + borrado del derivado + watermarking + evaluación |
| C-09 Fine-tuning | 200 h | **400 h** (300–500) | +200 | Dataset + captioning + arnés + tracking + protocolo de evaluación |
| C-12 Auth + 2FA | 48 h | **28 h** (24–32) | **−20** | **Inflada.** Auth.js + otplib + tabla de códigos: TOTP y recuperación son 8–12 h con librerías maduras |
| C-05 Asistente de letras | 40 h | **20 h** (16–24) | **−20** | **Inflada ~1,7×.** Es una llamada a un LLM con streaming y una plantilla de prompt |
| C-06 Stems | 40 h | **40 h** ✔ | 0 | Correcta. Demucs es maduro; lo que la justifica es el reproductor multipista sincronizado |
| C-02, C-03, C-08 | sin cambio | sin cambio | 0 | Se mantienen; se les añade rango explícito |
| | **1.084 h** | **1.566 h** | **+482** | |

**Por qué la revisión 3 sube 56 h más.** Aquí no hay reestimación de nada: hay **alcance que estaba prometido y no presupuestado**, y una **repartición** de C-10 entre fases que no cambia su total.

| Característica | Rev. 2 | Rev. 3 | Δ | Qué se añade y por qué |
|---|---|---|---|---|
| C-01 Generación | 70 h | **78 h** (68–88) | **+8** | **Gate de derechos de la letra** (D-21): declaración de autoría/derechos como bloqueo duro, registro en auditoría, campo `lyrics_declaration` en el manifiesto. C-08 lo tenía para el audio y C-01 no lo tenía para la letra |
| C-05 Asistente de letras | 20 h | **24 h** (20–28) | **+4** | Endurecer el prompt de sistema (prohibición explícita de reproducir letras existentes) y **validar que la salida es letra etiquetada parseable** por C-01, con regeneración si no lo es |
| C-11 Model registry | 130 h | **147 h** (127–167) | **+17** | **+12 h matriz de capacidades verificadas** en el spike de Fase 0 (`SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING`, `CONTINUATION`): es la información que decide si C-07 y C-08 (276 h de Fase 3) son viables, y hoy se descubriría **en la Fase 3**. **+5 h fichas de licencia** del pipeline de Fase 1 (I-13b) |
| C-13 Cimientos | 190 h | **214 h** (184–244) | **+24** | **+8 h linaje en el esquema** (D-22: `parent_id`, `root_id`, `derivation_kind`, `section_map`, `source_generation`) para no migrar en producción en C-07 · **+6 h exportación a 48 kHz con soxr y loudness por destino** (D-23) · **+4 h compartición por URL de la app** (D-24) · **+4 h i18n con `next-intl`** (D-25) · **+2 h checkpoint de stop-loss y runbook de desmantelamiento** (D-28) |
| C-14 Infra GPU | 120 h | **123 h** (103–143) | **+3** | Medir en el spike si caben **2 inferencias concurrentes** en los 48 GB de la L40S. Si caben, el throughput se dobla a coste cero: 3 h que pueden ahorrar un pod |
| C-10 → **C-10a + C-10b** | 105 h (Fase 2) | **38 h (Fase 1) + 67 h (Fase 2)** | **0** | **No sube: se reparte.** C-10a adelanta a la Fase 1 el esquema firmado por legal, la emisión del manifiesto desde la primera pista, el ledger append-only con cadena de hashes, el invariante de CI y `manifest_schema_version` con verificador multi-versión. C-10b se queda con C2PA, WORM, PDF y watermarking. **Motivo: una cadena WORM no admite backfill** |
| | **1.566 h** | **1.622 h** | **+56** | Efecto en fases: **Fase 1 550 → 640 h** (por C-10a y los añadidos) y **Fase 2 165 → 131 h** |

**Lo que la revisión 3 deliberadamente NO presupuesta**, y deja declarado como condicional para que no aparezca como sorpresa: el **tercer adapter (YuE) más el router de capacidades** (≈ 50 h, Fase 2, solo si G1-bis muestra adherencia insuficiente a la letra) — **🆕 con MiniMax-Music3 apuntado el 2026-08-18 como candidato condicional adicional** (Community License con uso comercial permitido bajo condiciones: atribución prominente en UI + cláusulas AUP/salvaguardas + umbral de 20 M$; requiere dictamen de legal, pregunta añadida al lote de G2 en `tasks.md` T-01), el **filtro automático de similitud de letras** (mejora futura), la **conformidad WCAG AA** (fuera de objetivo en Fase 1) y los **idiomas de UI adicionales** (I-19).

**Calibración con histórico:** no existe `docs/roadmap/CALIBRATION.md` — es la primera iniciativa del repositorio. Sin histórico propio, se mantiene el margen estándar del 20 %, se declara el rango de cada estimación y se **baja la confianza** en C-03, C-04, C-07, C-08 y C-09 (851 h, el **52 %** del total). Ejecutar `/retro` al cierre de cada fase es la única forma de que la próxima estimación no se apoye solo en criterio.

---

## 6. Infraestructura y coste total de propiedad

Es la decisión que el usuario pidió expresamente resolver (§8, confirmación 5). Empezamos por el dato que la determina, y terminamos por la comparación que faltaba: la de **construir contra comprar**.

### 6.1 Carga real de trabajo

| Magnitud | 100 gen/mes | 1.000 gen/mes |
|----------|-------------|---------------|
| Segundos de GPU **útiles** por pista entregada (S-02, `⚠️ medir`) | 150 s | 150 s |
| **Horas de GPU útiles al mes** | **4,2 h** | **41,7 h** |
| Horas de **pod facturadas** al mes (factor 1,90×, S-02b) | 7,9 h | **79,2 h** |
| **Utilización sobre GPU útil** (720 h/mes) | 0,6 % | **5,79 %** |
| **Utilización sobre horas de pod facturadas** (factor 1,6× / 1,90×) | 0,9 % / 1,1 % | **9,3 % / 11,0 %** |

> **Declaración de base (corrección de la revisión 1).** El 5,79 % es utilización sobre **segundos de GPU útiles**. Sobre **horas de pod facturadas** —que es lo que se paga— la utilización es del **9,3 %** con factor 1,6× y del **11,0 %** con factor 1,90×. La conclusión no cambia; la base sí hay que decirla.

Supuestos de inferencia por modelo, a validar en el spike: ACE-Step 1.5 ≈ 60–120 s por pista en GPU de ≥ 24 GB (base 90 s); HeartMuLa ≈ 120–240 s; YuE 7B ≈ 300–600 s. Post-proceso: stems ≈ 30 s, conversión de voz ≈ 60 s. **Con 8 GB y offloading estos tiempos suben de forma material** (confirmación 10 del usuario, I-07).

**Una utilización del 11 % en el escenario más alto de volumen es la respuesta a la pregunta del usuario: una GPU dedicada 24/7 no está justificada.**

### 6.2 Opciones comparadas

**Once posturas** de infraestructura: A, A-bis, B, B-bis, C, C-bis, D, E, F, G y H. Las tres últimas (F, G, H) se añadieron en la revisión 2. *(La revisión 2 escribía «ocho posturas» sobre una tabla de once filas: corregido en la revisión 3, y el changelog dice once.)*

| Opción | Configuración | Coste/mes a 1.000 gen | Coste/mes a 100 gen | €/generación | Arranque en frío | Valoración |
|--------|---------------|----------------------|---------------------|--------------|------------------|------------|
| **A. Dedicada 24/7, on-demand** | L40S RunPod 0,79 $/h × 720 h | **523 €** | **523 €** | 0,52 € / 5,23 € | Ninguno | Se paga el 89 % del tiempo por no hacer nada |
| **A-bis. Dedicada 24/7, neo-cloud** | L40S 0,39 $/h × 720 h | **258 €** | **258 €** | 0,26 € / 2,58 € | Ninguno | Misma objeción, la mitad de precio. **Es la referencia del punto de equilibrio real** (§6.3) |
| **B. Pod efímero por trabajo** | L40S 0,79 $/h × 79,2 h (factor 1,90×) | **58 €** | **6 €** | 0,058 € | **En cada trabajo**: 2–6 min | El coste sigue al uso, pero el usuario paga el arranque **en cada variante**. Con factor 1,6× serían 48 €; con 3,10×, 94 € |
| **B-bis. Ídem, neo-cloud** | L40S 0,39 $/h × 79,2 h | **28 €** | **3 €** | 0,028 € | En cada trabajo | Más barato, menos garantías de disponibilidad |
| **C. Serverless** | RunPod A100 2,72 $/h × 41,7 h de compute activo | **104 €** | **10 €** | 0,104 € | Gestionado por el proveedor | Cero gestión del ciclo de vida del pod. Cuesta ~2× la B y lo compensa en simplicidad |
| **C-bis. Serverless H100** | 4,55 $/h × 41,7 h | **175 €** | **17 €** | 0,175 € | Gestionado | Solo si el spike demuestra que la H100 reduce lo suficiente el tiempo por pista |
| **D. On-premise** | Compra de tarjeta + hospedaje | **CAPEX `⚠️ no verificado`** + operación | — | — | Ninguno | Con la confirmación 10 del usuario esto ya **no significa «GPU profesional de datacenter»**: una estación con una tarjeta de consumo de 24 GB es un CAPEX de otro orden. Sigue sin amortizar con 41,7 h de GPU/mes, pero la cifra la da Compras, no nosotros. Solo gana si Daycry **ya tiene** GPUs infrautilizadas (I-02), donde el coste marginal es ≈ 0 |
| **E. Cloud corporativo (hyperscaler vía IT)** | A100 on-demand en el extremo alto verificado (4,10 $/h) | **299 €** por demanda / **2.716 €** dedicada | 30 € por demanda | 0,299 € | Igual que B | 5× la B, precio exacto `⚠️ verificar` con IT. **A cambio da lo que ningún neo-cloud da**: contrato marco, residencia del dato, cumplimiento. Si legal o seguridad lo exigen, el sobrecoste (≈ 240 €/mes) es despreciable frente a **98.280 €** de desarrollo |
| **🆕 F. Pod efímero + keep-warm 10 min** | L40S 0,79 $/h × 61,7 h (222 s/gen facturados en ráfagas de 10) | **45 €** | **5 €** | 0,045 € | **Solo en la primera** de cada ráfaga | **Más barato que B y con mejor UX.** En generación musical el usuario itera 5–10 variantes seguidas: el keep-warm hace instantáneas las variantes 2..N (§6.4) |
| **🆕 G. Pod caliente en horario laboral** ✅ | **Un** pod L40S 0,79 $/h × 176 h (8 h × 22 días, `Europe/Madrid`, calendario ajustable) + keep-warm fuera de horario + **segundo pod efímero bajo demanda** | **128 €** | **128 €** | 0,128 € / 1,28 € | **Ninguno mientras alguien trabaja**; el trabajo que desborda el pod caliente sí lo paga | **Recomendada.** Cubre hasta ~4.200 gen/mes dentro del horario. Cuesta ≈ 83 €/mes más que F y **elimina el único problema de UX del diseño**. En neo-cloud (0,39 $/h): **63 €/mes**. **Es un pod, no dos** (D-26; la spec §12.1 decía «2 por defecto» y contradecía este presupuesto). Dos pods calientes serían ≈ 256 €/mes |
| **🆕 H. GPU de 24 GB clase consumo (RTX 4090/5090)** | Marketplace, precio **`⚠️ verificar` (I-14)** | `= (p / 0,79) × coste de F o G` | ídem | ídem | ídem | La **cifra de confort de ACE-Step son 24 GB** (confirmación 10): la L40S de 48 GB está sobredimensionada. **No inventamos el precio**; a modo de sensibilidad, a la mitad del precio de la L40S la opción G bajaría a ≈ 64 €/mes. **Contrapartidas reales**: los marketplaces de GPU de consumo dan **menos garantías de disponibilidad**, y los **términos de licencia del driver para uso en datacenter son un punto a verificar** antes de comprometerse |

### 6.3 Recomendación de infraestructura

**Opción G: un pod caliente en horario laboral (176 h/mes, `Europe/Madrid`, calendario ajustable por el admin) con keep-warm de 10 min fuera de ese horario y un segundo pod efímero bajo demanda.** Coste: **≈ 128 €/mes** en L40S de RunPod, **≈ 63 €/mes** en neo-cloud barato, menos aún si I-14 confirma que una GPU de 24 GB es más económica. **Opción F (solo keep-warm, ≈ 45 €/mes)** como postura de arranque mientras el uso es esporádico; **opción C (serverless)** como plan B si no se quiere gestionar el ciclo de vida del pod.

> **Reconciliación con los límites de uso (revisión 3).** La spec §12.1 declaraba «**2 pods** GPU en paralelo por defecto» y este presupuesto paga **uno**. Se resuelve así (D-26): **un pod caliente** en horario + **un pod efímero bajo demanda** para el desborde, que **paga arranque en frío de 2–6 min** y así se muestra en la espera estimada de la UI. Política de despacho: **FIFO con fairness round-robin por usuario**, para que un usuario con 20 trabajos encolados no bloquee a los otros cuatro. Y una medida de 3 h en el spike de Fase 0 que puede valer un pod entero: **¿caben 2 inferencias concurrentes en los 48 GB de la L40S?** Si caben, el throughput se dobla **a coste cero** y las esperas de §12.1 se parten por dos.

Argumentos:

1. **El coste es ruido presupuestario en cualquiera de las tres.** 45 €, 128 € o 258 €/mes frente a **98.280 €** de desarrollo son diferencias del **0,5 %–3 % anual** del presupuesto del proyecto. Discutirlas más de una tarde es mala asignación de atención.
2. **Punto de equilibrio, esta vez calculado de verdad.** La revisión 1 daba «≈ 10.800 generaciones/mes» comparando la GPU dedicada con la efímera **al mismo precio por hora**. Eso no es un cálculo económico, es una **identidad**: al mismo precio/hora, el equilibrio es por construcción el 100 % de uptime. La comparación que informa es **dedicada barata (A-bis: 0,39 $/h → 258 €/mes) contra efímera recomendada (0,79 $/h)**:

   | Comparación | Coste marginal/gen | Punto de equilibrio | Margen sobre el techo de 1.000 gen/mes |
   |---|---|---|---|
   | A-bis vs. B con factor 1,6× | 0,0485 €/gen | **≈ 5.300 gen/mes** | **×5,3** |
   | A-bis vs. B con factor 1,90× | 0,0575 €/gen | **≈ 4.500 gen/mes** | **×4,5** |
   | A-bis vs. F (keep-warm) | 0,0448 €/gen | ≈ 5.760 gen/mes | ×5,8 |

   **El margen real es ×5, no ×10.** Sigue siendo holgado, pero la mitad de lo que decía la revisión 1.
3. **Regla de cambio con la base declarada.** Migrar a dedicada cuando las **horas de pod facturadas** superen el 35 % del mes (**252 h de 720**), que a factor 1,6× son **≈ 3.780 gen/mes** y a factor 1,90× son **≈ 3.183 gen/mes**. *(La revisión 1 decía «> 35 % ≈ 250 h GPU/mes ≈ 6.000 gen/mes», mezclando horas facturadas con segundos útiles.)* La métrica de `gpu_seconds` y de horas de pod debe estar instrumentada desde el día uno.
4. **El arranque en frío deja de ser un problema de producto**, que es exactamente lo que la opción G compra (§6.4).
5. **Salvedades.** Si I-02 revela GPUs propias infrautilizadas, la opción D pasa a ser la mejor por coste marginal cero. Si legal o seguridad exigen residencia del dato, se va a **E** asumiendo ≈ 240 €/mes extra — irrelevante en este contexto.
6. **Tope de gasto obligatorio (D-17).** Cualquiera de estas opciones se opera con **límite de gasto mensual agregado y kill switch en el proveedor**, no solo con `max_gpu_seconds` por trabajo. Un bucle de reintentos en un proveedor medido es la forma clásica de fundir el presupuesto un fin de semana (R-17).

### 6.4 Arranque en frío: es un problema de UX, no de coste

La revisión 1 daba **1–3 min** de arranque en frío. Era **optimista ~2×**. Desglose realista para ACE-Step 1.5 (3,5 B, ~7 GB en fp16):

| Etapa | Tiempo | Nota |
|-------|--------|------|
| Scheduling / asignación del pod | 10–60 s | Depende de la disponibilidad del proveedor |
| **Pull de la imagen CUDA + torch (8–15 GB)** | **120–300 s si no está cacheada en el host** | **Término dominante.** La spec cacheaba los pesos en volumen persistente y **no la imagen**: hueco concreto que C-14 debe cerrar (S-01b) |
| Descarga de pesos | 20–120 s | Cacheables en volumen persistente |
| Contexto CUDA + carga a VRAM | 30–60 s | |
| Warm-up de kernels | 30–120 s | La primera inferencia siempre es más lenta |
| **Total con imagen cacheada** | **2–6 min** | El suelo teórico de la suma es ~90 s; en la práctica no baja de ~2 min |
| **Total en el peor caso** | **5–12 min** | Sin imagen cacheada, proveedor cargado |

**Impacto en coste (irrelevante).** El factor de facturación es `(150 s útiles + arranque + 15 s de cierre) / 150 s`:

| Arranque asumido | Factor | Coste/mes a 1.000 gen (opción B) |
|---|---|---|
| 75 s (lo que implicaba el ×1,6 de la revisión 1) | 1,60× | 48 € |
| **120 s (realista con imagen cacheada)** | **1,90×** | **58 €** |
| 300 s (peor caso) | 3,10× | 94 € |

**Impacto en UX (material).** En generación musical el usuario **itera 5–10 variantes seguidas**. Con pod por trabajo paga el arranque **cada vez**: diez variantes son diez esperas de 2–6 min, entre 20 y 60 minutos de espera acumulada para una tarea de una tarde. Dos medidas cierran el problema, y ninguna estaba en la revisión 1:

- **Keep-warm con idle timeout de 10 min** tras cada trabajo (opción F). Amortiza los ~720 s de sobrecarga por ráfaga (120 s de arranque + 600 s de idle) entre las generaciones de la ráfaga: en ráfagas de 10, **222 s/gen facturados frente a 285 s** con pod por trabajo. Es **más barato y con mejor UX**: 45 €/mes frente a 58 €/mes. Las variantes 2..N son **instantáneas**.
- **Pod caliente en horario laboral** (opción G): 176 h/mes, **128 €/mes, cero arranque en frío mientras alguien trabaja**.

**La decisión, puesta en su escala:** sobre un presupuesto de **98.280 €**, pagar **≈ 83 €/mes más** (996 €/año, el **1,0 %** del desarrollo) para eliminar el único problema de UX que el diseño no resuelve por sí solo es una **compra evidente**. Se pone delante de dirección así, no enterrada en una tabla de precios por hora. `Validar con I-09`.

### 6.5 Construir vs. comprar: el TCO que faltaba

La revisión 1 comparaba **siete opciones de GPU para una decisión de 5–48 €/mes** y **cero opciones para la decisión de 65.040 €**. Esta sección corrige eso. No cambia el veredicto, pero es la sección que dirección tiene derecho a leer antes de aprobar.

#### (a) No hacer nada: seguir con la librería de producción actual

| Concepto | Cifra |
|---|---|
| Suscripción enterprise de librería de producción (referencia, `⚠️ verificar`) | **300 €/mes** = 3.600 €/año |
| Catálogo completo de esta iniciativa (**98.280 €**) equivale a | **≈ 27 años** de suscripción |
| Solo Fase 1 (**39.360 €**) equivale a | **≈ 10,9 años** |
| Fases 1+2 (**47.220 €**) equivalen a | **≈ 13,1 años** |

Lo que **no** compra la librería: música hecha al brief exacto de la pieza, iteración en minutos, y la opción futura de C-09. Lo que **sí** compra y esta plataforma no: derechos limpios, contractualmente garantizados, hoy. Ese es literalmente el criterio que motiva la iniciativa, y la librería lo cumple mejor que las Fases 1–3 (§10.7).

#### (b) Comprar el mitigante: proveedor generativo con indemnización comercial contractual

Es la opción que compra **exactamente** el riesgo que motiva el proyecto, sin construir nada. Varios proveedores generativos de nivel empresarial ofrecen indemnización contractual por reclamaciones de PI sobre el output. Precio `⚠️ verificar` (es tarifa negociada, no de catálogo). Puntos de equilibrio frente al build:

| Precio del proveedor | Equivale a Fase 1 (**39.360 €**) | A Fases 1+2 (**47.220 €**) | Al catálogo completo (**98.280 €**) |
|---|---|---|---|
| 500 €/mes | 6,6 años | 7,9 años | 16,4 años |
| 1.000 €/mes | 3,3 años | 3,9 años | 8,2 años |
| 2.000 €/mes | 1,6 años | 2,0 años | 4,1 años |

**A favor:** transfiere el riesgo por contrato, cero desarrollo, cero OPEX, disponible mañana. **En contra:** dependencia de proveedor, la indemnización suele tener **topes y exclusiones** que hay que leer con legal, no da control de procedencia ni fine-tuning propio, y no elimina el riesgo — lo reasigna. Además, la motivación declarada de Daycry nace precisamente de un litigio sobre un proveedor generativo. **Recomendación: pedir dos ofertas con cláusula de indemnización en la misma semana en que se consulta a legal (G2)**, y preguntar en ellas **también por I-05b** (¿la oferta garantiza exclusividad sobre el output?, ¿sobre qué base, si la obra puede no ser protegible?). Cuestan una llamada y pueden ahorrar 98.280 €.

#### (c) OPEX de mantenimiento: la partida que el documento no tenía

La revisión 1 presentaba **CAPEX de desarrollo como coste total**. Un sistema con GPU, cola, proveedor externo, modelos versionados y un ledger con valor legal no se mantiene solo:

| Base | OPEX a ≈ 15 %/año | Nota |
|---|---|---|
| Fases 1+2 (**47.220 €**) — el escenario realista | **≈ 7.100 €/año** | Actualizaciones de modelos y drivers, roturas de proveedor, parches de seguridad, atención a alertas. **Y una partida nueva de la revisión 3**: mantener el **verificador multi-versión de manifiestos** vivo mientras el esquema evolucione |
| Catálogo completo (**98.280 €**) | ≈ 14.700 €/año | Si se acaban aprobando las Fases 3 y 4 |

**Hoy no tiene dueño ni partida** (I-16, R-16). Sin propietario operativo nombrado, esta cifra no desaparece: se convierte en tiempo robado a la siguiente iniciativa.

#### (d) Horas de no-desarrollo: hoy están a cero

El documento afirmaba que «la revisión de legal y los ciclos de escucha no se comprimen» y **acto seguido no los presupuestaba**. Estas son las horas que hacen falta y que **no** son de desarrollo:

| Rol | Horas | Cuándo | Por qué es imprescindible |
|-----|-------|--------|---------------------------|
| **Legal** (gate G2 con sus **dos** preguntas —I-05 e I-05b—, **firma del esquema del manifiesto de C-10a antes de implementar C-11**, gates de titularidad de C-08 y de la letra de C-01, y **verificación de los ToS de Suno** para las líneas base de G1 y el estudio de UI de D-12: **2 h dentro de estas 32**) | **32 h** (24–40) | **Semana 0** y al inicio de la Fase 1 (firma del esquema) | Es el único gate que puede anular el 100 % del presupuesto. **La firma del esquema es ahora precondición de C-11**, no un trámite posterior (D-20) |
| **Supervisor musical** (briefs de prueba, rúbrica, escucha ciega de **G1 y G1-bis**, decisión del objetivo de loudness por destino en la Fase 0, regresiones al cambiar de adapter) | **40 h** (32–48) | Fase 0, Fase 1 (G1-bis) y en cada versión de adapter | **El gate G1 no se puede ejecutar sin él.** No lo puede juzgar el desarrollador. **Debe estar nombrado antes de aprobar la Fase 1** (I-20) |
| **DPO / DPIA** (solo si se aprueba C-04) | **20 h** (16–24) | Antes de una línea de código de C-04 | Voz identificable = dato biométrico |
| **Propietario operativo** (traspaso, runbooks, guardias) | **24 h** | Cierre de Fase 2 | Sin esto, la entrega no tiene a quién entregarse |
| **Total** | **116 h** (96 h sin C-04) | | **€ a tarifa interna: `⚠️ verificar` (I-18)** |

A la tarifa de referencia de 50 €/h serían **4.800–5.800 €**; a tarifas internas de legal, más. **No son horas de desarrollo: no están en las 1.638 h** y hay que reservarlas explícitamente. Las **32 h de legal** y las **40 h de supervisor musical** siguen siendo las mismas en la revisión 3 — las tareas nuevas que se les asignan (segunda pregunta de G2, firma del esquema, ToS de Suno, G1-bis, loudness por destino) **caben dentro de esas horas**, no las amplían.

#### (e) TCO a 24 meses del escenario recomendado (Fases 0+1+2)

| Concepto | 24 meses |
|----------|----------|
| Desarrollo Fases 0+1+2, con margen | **47.220 €** |
| OPEX de mantenimiento (15 %/año) | **≈ 14.200 €** |
| GPU (opción G, 128 €/mes) | **3.072 €** |
| Almacenamiento (política recomendada, §6.6) | **≈ 210 €** |
| Horas de no-desarrollo (96 h a 50 €/h, `⚠️ I-18`) | **≈ 4.800 €** |
| Entornos dev/stage/prod no-GPU (`⚠️ I-15`, orden de magnitud 80–250 €/mes) | **1.920–6.000 €** |
| **TCO 24 meses** | **≈ 71.000–75.000 €** |
| *Comparación:* librería de producción a 300 €/mes | 7.200 € |
| *Comparación:* proveedor generativo con indemnización a 1.000 €/mes | 24.000 € |

**Dicho sin adornos: construir cuesta entre 3 y 10 veces más que comprar, a 24 meses.** Lo que se compra con esa diferencia es control de procedencia, capacidad de auditoría propia y la **opción** de C-09. Si esas tres cosas valen ≈ **47.000 €** para Daycry, el build está justificado. Si no, no lo está — y esa es una decisión de dirección, no de ingeniería. **Y con I-05b sobre la mesa hay una pregunta más:** si el output pudiera no ser protegible, parte de lo que se compra construyendo (control) sigue en pie, pero **la exclusividad frente al cliente no la da ninguna de las dos vías**.

### 6.6 Almacenamiento: la única partida que crece sin techo

La revisión 1 daba volumetría y dejaba el coste en «a verificar». Es calculable. Volumetría: **~55 MB/generación sin stems**, **~245 MB con stems**. A tarifa S3 estándar de referencia (**0,023 $/GB-mes**, 1 USD = 0,92 €) y 1.000 gen/mes, el gasto es **acumulativo**:

| Escenario | Mes 1 | Mes 12 | Mes 24 | Acumulado 12 m | Acumulado 24 m |
|-----------|-------|--------|--------|----------------|----------------|
| **Stems por defecto (245 MB/gen)** | 5 €/mes | **62 €/mes** | **124 €/mes** | **404 €** | **1.555 €** |
| Stems a demanda (55 MB/gen) | 1,2 €/mes | 14 €/mes | 28 €/mes | 91 € | 349 € |
| **Recomendado: stems a demanda + FLAC en vez de WAV** | 0,7 €/mes | **8 €/mes** | **17 €/mes** | **55 €** | **210 €** |

**La conclusión que faltaba: el almacenamiento adelanta a la GPU, y luego no para.** La GPU es plana; el almacenamiento sube un escalón cada mes. Con la base declarada:

| Postura de GPU | Coste/mes | El almacenamiento con stems por defecto la supera en… |
|---|---|---|
| F (keep-warm) | 45 € | **mes 9** |
| B (efímera, factor 1,6×) | 48 € | **mes 10** |
| B (efímera, factor 1,90×) | 58 € | mes 12 |
| **G (recomendada)** | 128 € | mes 25 |

Con la **política recomendada** (FLAC + stems a demanda) el almacenamiento se queda en **17 €/mes al mes 24** y no adelanta a ninguna postura de GPU en el horizonte de la fase 1. Medidas obligatorias desde el día uno (spec §12.2):

- [ ] **Stems a demanda, nunca por defecto** — ×4,5 de volumen.
- [ ] **FLAC como formato de almacén, no WAV 24 bit** (D-09). Un ahorro gratis: el audio **sintetizado no contiene 24 bits de información real**, así que guardar WAV es pagar ~40 % más por cero información. FLAC es lossless y estándar en post-producción. WAV se mantiene **como exportación a demanda**, no como formato de almacén.
- [ ] **Política de retención con números**: no-favoritas → frío a los 30 días, borrado a los 180 salvo pertenencia a producción entregada. Favoritas y pistas usadas: indefinido con su manifiesto.
- [ ] **Ciclo de vida automático** a clase frío (configuración de bucket, no proceso propio).
- [ ] **GC de artefactos huérfanos** por reconciliación diaria contra Postgres — sin él, la inconsistencia de doble escritura deja ficheros que **se pagan para siempre y nadie ve**.
- [ ] **Egress medido y presupuestado** (`⚠️ verificar`, I-08).

### 6.7 Otros costes de infraestructura no presupuestados

| Concepto | Estimación | Nota |
|----------|-----------|------|
| **GPU de entrenamiento (solo C-09)** | **≈ 626 €** por ciclo en spot (A100 80 GB a 0,68 $/h × 1.000 GPU-h) — **≈ 1.095 €** en on-demand | Supuesto: 10 experimentos × 100 GPU-h. **Solo compute**; no incluye adquisición ni licenciamiento del dataset, que puede ser el coste dominante (I-03) |
| **Entornos dev/stage/prod no-GPU** | **`⚠️ no presupuestado`** (I-15). Orden de magnitud 80–250 €/mes | Postgres y Redis gestionados, hosting de Next.js y FastAPI, dominio, certificados |
| Egress de descargas | `⚠️ verificar` (I-08) | Con 1–5 usuarios es marginal; instrumentar antes de la fase 2 |
| Gestor de secretos / Vault | `⚠️ verificar` | Coste menor, requisito de D-15 |
| Tope de gasto y kill switch | Sin coste directo | **Requisito, no opción** (D-17, R-17) |

---

## 7. Evaluación por característica

Horas y coste **base** (sin margen), con el **rango** de cada estimación declarado. Tokens en millones. Confianza: Alta / Media / Baja.

### C-01 · Generación a partir de letra + prompt de estilo

| Campo | Valor |
|-------|-------|
| Complejidad | Media-alta |
| Esfuerzo | **78 h** (rango **68–88**) · Confianza **Media** · *rev. 1: 48 h · rev. 2: 70 h* |
| Coste | **3.900 €** |
| Tokens | 4,88 M in / 0,68 M out (19,5 h IA, ratio 0,25) |
| Impacto | Editor de letras con etiquetas de sección, **gate de derechos de la letra**, formulario de creación, API `/generations`, worker, adapter de ACE-Step, post-proceso y transcode |
| Dependencias | C-11, C-13, C-14, **C-10a** (el manifiesto que su criterio de aceptación exige) |

**Por qué sube de 48 h a 70 h (rev. 2) y a 78 h (rev. 3).** 48 h era el coste de «encender el modelo». C-01 es **la superficie de producto completa**, y esto es lo que hay dentro:

| Subsistema | Horas |
|---|---|
| Editor de letras con etiquetas de sección (`[verso]`, `[estribillo]`, `[puente]`) | 16 h |
| Formulario de creación a mano, con etiquetas de dominio (estilo, duración, destino, voz, instrumental) | 14 h |
| API `/generations`: validación, `params_schema`, resolución de modelo, idempotencia | 12 h |
| Worker: invocación del adapter, progreso por SSE, reintentos con semilla nueva | 12 h |
| Post-proceso: loudness EBU R128 **al objetivo del destino** + transcode FLAC/MP3 | 8 h |
| Panel de resultado, variantes en pares (referencia de UX de Suno, D-12), estados de error | 8 h |
| **🆕 Gate de derechos de la letra** (D-21): UI de declaración, bloqueo duro en la API, registro en auditoría con usuario/fecha/contenido, campo `lyrics_declaration` en el manifiesto | **8 h** |

Es **el corazón del producto** y el hito que demuestra el ciclo completo.

> **⚠️ El hueco legal que la revisión 3 cierra.** C-08 exigía declaración de titularidad para el audio subido y **C-01 aceptaba cualquier letra sin nada**. Un usuario podía pegar una letra con copyright y el sistema generaba **una obra derivada con manifiesto impecable sobre un input infractor** — el peor de los mundos: trazabilidad perfecta de una infracción. Ocho horas y una casilla con bloqueo duro lo cierran. El **filtro automático de similitud** contra corpus de letras queda como **mejora futura no bloqueante**, no como requisito de Fase 1.

**Riesgos.** La adherencia del audio a la letra depende del modelo. *(Corrección de la revisión 3: la mitigación anterior decía «enrutar a YuE 7B», y **ni el router ni el adapter de YuE están en el alcance** — era una mitigación que apuntaba a código inexistente.)* La mitigación real, con lo que sí habrá en la Fase 1: **HeartMuLa como segunda opinión** sobre el mismo brief y **regeneración con otra semilla**. Si **G1-bis** muestra que la adherencia de los dos adapters es insuficiente, entonces —y solo entonces— se activa la **partida condicional de Fase 2: tercer adapter (YuE 7B) + router de capacidades, ≈ 50 h no presupuestadas aquí** (D-06, D-16).

### C-02 · Instrumental sin voz

| Campo | Valor |
|-------|-------|
| Complejidad | Baja |
| Esfuerzo | **12 h** (rango **10–16**) · Confianza **Alta** · *sin cambio* |
| Coste | **600 €** |
| Tokens | 0,50 M in / 0,07 M out (2 h IA) |
| Impacto | Un modo en la petición, variante de prompt, valores por defecto propios, conmutador en la UI |
| Dependencias | C-01 |

**Quick win.** Prácticamente gratis una vez existe C-01, con demanda real en producción audiovisual (fondos, camas musicales). Su criterio de aceptación es verificable: energía de la pista vocal por debajo de umbral tras separación de fuentes (spec §5.2).

### C-03 · Selector de tipo de voz (timbre, género, registro)

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **56 h** (rango **48–80**) · Confianza **Baja** · *sin cambio* |
| Coste | **2.800 €** |
| Tokens | 5,50 M in / 0,77 M out (22 h IA, ratio 0,39) |
| Impacto | Catálogo curado de ≥ 8 presets (etiquetas + audio de muestra), previsualización, posible pasada de SVC, capacidad `VOICE_CONDITIONING` |
| Dependencias | C-01, C-11; posible acoplamiento con el pipeline de C-04 |

**Hay un desajuste de expectativas que conviene decir claro:** los modelos disponibles **no exponen mandos limpios de timbre, género y registro**. El control es indirecto (etiquetas en el prompt, audio de referencia) y solo parcialmente predecible. Alcanzar algo que un usuario perciba como «selector de voz» exige **curar presets y evaluarlos empíricamente uno a uno** — trabajo de escucha, no de código. De ahí la confianza baja y el rango asimétrico al alza (hasta 80 h).

El criterio de aceptación acordado es honesto: si un preset no es reconocible en escucha ciega por 2 de 3 evaluadores, **se documenta la limitación en la UI** en lugar de prometerla (spec §5.2).

> **Restricción de derechos añadida en la revisión 3.** Los presets se limitan a **condicionamiento por etiquetas o por audio sintético generado por el propio modelo**. Un «catálogo de ≥ 8 presets de voz» construido a partir de **grabaciones de voces reales** es, en la práctica, clonación de voz sin el aparato de consentimiento de C-04: el mismo riesgo de RGPD y biometría entrando por la puerta de una característica de 56 h en lugar de por la de 175 h. Si algún preset derivase de grabaciones reales, la **verificación documentada de derechos por preset** es criterio de aceptación y, sin ella, el preset no se publica. Y con **I-13b** abierta, la licencia de RVC/YingMusic-SVC se verifica **antes** de integrarlos, no después.

### C-04 · Clonación de voz propia

| Campo | Valor |
|-------|-------|
| Complejidad | **Crítica** |
| Esfuerzo | **175 h** (rango **150–200**) · Confianza **Baja** · *rev. 1: 120 h* |
| Coste | **8.750 €** |
| Tokens | 17,50 M in / 2,45 M out (70 h IA, ratio 0,40) |
| Impacto | RVC v2 / YingMusic-SVC, segunda etapa GPU, dataset de voz, consentimiento, retención y borrado del derivado, watermarking, bucle de evaluación, panel de voces |
| Dependencias | C-01, C-14; **gate de legal + DPIA**; watermarking de C-10 (I-13) |

**Por qué sube de 120 h a 175 h.** Las 120 h cubrían la integración técnica y dejaban fuera lo que hace la característica legalmente utilizable:

| Subsistema | Horas |
|---|---|
| Integración RVC v2 / YingMusic-SVC + segunda etapa GPU | 40 h |
| Subida y validación de dataset de voz, trabajo de entrenamiento por voz | 32 h |
| **Flujo de consentimiento** (identidad, alcance, fecha, texto firmado) como **bloqueo duro** | 24 h |
| **Borrado efectivo del derivado** (audio + dataset + **pesos**) con prueba automatizada | 28 h |
| Watermarking de la voz clonada (⚠️ condicionado a I-13; **candidatos MIT identificados 2026-08-18** — SilentCipher/AudioSeal, robustez en música por validar) | 16 h |
| Bucle de evaluación de calidad (escucha + métricas) | 24 h |
| Panel de gestión de voces y permisos | 11 h |

- **RGPD y biometría**: la voz identificable es dato biométrico. Consentimiento explícito e informado, base jurídica, **DPIA**, límites de finalidad, retención y **borrado del modelo derivado**, no solo del audio. Es trabajo de legal y de arquitectura, no un formulario.
- **Calidad irregular** en el open source de este terreno, con requisitos altos de GPU y sin control emocional.
- **Sin safety ni watermarking de fábrica**; para el watermarking hay **candidatos con licencia MIT identificados** (SilentCipher y AudioSeal, hallazgo verificado 2026-08-18), con la **robustez en música por validar** (I-13, prueba prevista en F10/`T-57`).
- **Riesgo de dependencia**: so-vits-svc tiene el fork realtime con mantenimiento limitado desde primavera de 2023. Preferir **RVC v2** o **YingMusic-SVC**.

**No la descartamos**: 8.750 € es asumible *si* hay una necesidad de negocio concreta (la voz de un locutor propio con contrato). Lo que no recomendamos es construirla especulativamente.

### C-05 · Asistente IA de letras

| Campo | Valor |
|-------|-------|
| Complejidad | Baja-media |
| Esfuerzo | **24 h** (rango **20–28**) · Confianza **Alta** · *rev. 1: 40 h — **estaba inflada ~1,7×** · rev. 2: 20 h* |
| Coste | **1.200 €** |
| Tokens | 0,90 M in / 0,13 M out (3,6 h IA, ratio 0,15) |
| Impacto | Llamada a un LLM con streaming, plantilla de prompt de letra estructurada, UI de asistente, rate limit y contabilidad de tokens, **validación de la salida como letra etiquetada parseable** |
| Dependencias | C-13, C-01 (comparte el parser de letra etiquetada) |

**Corrección de la revisión 1.** 40 h no se sostienen: esto es **una llamada a un LLM con streaming y una plantilla de prompt**. Desglose: llamada + plantilla 8 h · UI de streaming, edición e inserción en el editor 6 h · rate limit, contabilidad de tokens por usuario y guardrails 6 h · **🆕 endurecimiento del prompt de sistema (prohibición explícita de reproducir letras existentes) y validación de que la salida es letra etiquetada parseable por C-01, con regeneración si no lo es: 4 h** (revisión 3).

**Por qué esas 4 h no son cosmética.** El asistente es la vía por la que entra la mayor parte de las letras, así que es también el sitio más barato para reducir el riesgo de D-21: una letra generada por el asistente rellena `lyrics_declaration` automáticamente. Y una salida que no parsea no es «una letra mejorable»: es un trabajo de generación que **falla en C-01 después de haber pagado GPU**.

**Quick win de altísimo valor percibido y ahora la mitad de precio.** Resuelve la página en blanco, no necesita GPU, y genera letras **ya etiquetadas por secciones**, lo que mejora directamente el resultado de C-01. Su rate limit está numerado en la spec (§12.1): 30 peticiones/usuario/día.

### C-06 · Descarga de stems separados

| Campo | Valor |
|-------|-------|
| Complejidad | Media |
| Esfuerzo | **40 h** (rango **34–52**) · Confianza **Media** · *sin cambio — verificada como correcta* |
| Coste | **2.000 €** |
| Tokens | 2,50 M in / 0,35 M out (10 h IA, ratio 0,25) |
| Impacto | Demucs como post-proceso (o stems nativos si el modelo declara `STEM_OUTPUT`), etapa GPU extra ≈ 30 s, empaquetado, **reproductor multipista sincronizado** |
| Dependencias | C-01, C-14, C-13 (reproductor) |

Las 40 h **no** son por Demucs, que es maduro y estable: lo que las justifica es el **reproductor multipista sincronizado** (4 pistas alineadas ±10 ms, controles por pista, solo/mute) y el empaquetado. Es la única característica de la revisión 1 cuya estimación resiste la auditoría sin tocarla.

**Alto valor para el caso de uso de Daycry**: en post-producción, bajar la voz o quedarse con la batería es la diferencia entre pista usable y descartada. **Coste oculto**: ×4,5 el almacenamiento (55 → 245 MB). Decisión tomada: **stems a demanda, nunca por defecto** (§6.6).

> **⚠️ Precondición de licencia (I-13b, revisión 3).** «Demucs es maduro» es cierto del **código** (MIT); **los pesos publicados llevan términos propios que en algunos casos son no comerciales**. La regla 5 del registry aplica al pipeline completo, así que la **ficha de licencia verificada de los pesos de Demucs** es precondición de la Fase 2, con las 4–6 h de verificación dentro de estas 40 h. Si los pesos no son utilizables comercialmente, C-06 necesita otro separador — y eso se descubre antes de escribir el reproductor multipista, no después.
>
> **🆕 Hallazgo 2026-08-18 (confirmado, issue #327 de `facebookresearch/demucs`):** ya no es una hipótesis a verificar — los pesos preentrenados de Demucs (`htdemucs`/`htdemucs_ft`/`htdemucs_6s`) son **CC-BY-NC 4.0** confirmado. C-06 tal como está descrita **no puede lanzarse comercialmente con esos pesos**. Candidatos alternativos con licencia por verificar peso a peso: **MDX-Net (UVR5)** y variantes **Mel-Band RoFormer** con pesos MIT (p. ej. `silverdaw/mel-band-roformer-vocals-onnx` en HF; muchos pesos RoFormer de la comunidad no declaran licencia). La selección del separador de C-06 queda condicionada a completar I-13b con uno de estos candidatos — ver nota en `T-59` de `tasks.md`.

### C-07 · Extender / regenerar secciones concretas

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **140 h** (rango **120–160**) · Confianza **Baja** · *rev. 1: 96 h* |
| Coste | **7.000 €** |
| Tokens | 10,50 M in / 1,47 M out (42 h IA, ratio 0,30) |
| Impacto | Editor de forma de onda con regiones, alineado letra-audio, inpaint/continuación, empalme con crossfade, preservación fuera de la región |
| Dependencias | C-01, C-11; capacidades `SECTION_INPAINT` / `CONTINUATION` |

**Por qué sube de 96 h a 140 h: el editor de forma de onda con regiones ya es media característica por sí solo.**

| Subsistema | Horas |
|---|---|
| **Editor de forma de onda con regiones** (render, selección, zoom, snap a secciones, teclado) | 44 h |
| Alineado letra-audio con HeartTranscriptor | 20 h |
| Inpaint / continuación según capacidad declarada del modelo | 28 h |
| Empalme con crossfade y validación de costura | 20 h |
| Preservación bit-idéntica fuera de la región editada | 12 h |
| Línea de tiempo por secciones y máquina de estados de edición | 16 h |

Tres problemas encadenados: (1) el soporte de inpaint **no es universal** y puede no existir en el modelo elegido; (2) hay que **alinear la letra con el audio** para saber dónde empieza el estribillo — aquí **HeartTranscriptor ayuda de fábrica**, y es un argumento fuerte para tener HeartMuLa en el registry; (3) el empalme sin costura audible es un problema de audio, no de software. **Sigue siendo la candidata número uno a desviarse.**

**Dos cosas que la revisión 3 le quita de encima.** (a) El **linaje ya está en el esquema** desde la Fase 1 (D-22: `parent_id`, `root_id`, `derivation_kind`, `section_map`), así que C-07 **no arranca con una migración en producción** sobre tablas con valor legal — que es como iba a arrancar. (b) La **matriz de capacidades verificadas** del spike de Fase 0 dice **en la semana 4** si `SECTION_INPAINT` y `CONTINUATION` existen de verdad en los modelos registrados; con el plan anterior se descubría aquí, en la semana 20, con las 140 h ya comprometidas. Si la matriz sale vacía, **esta característica se replantea o se cae antes de gastarla**.

### C-08 · Cover / remezcla de una pista existente

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **80 h** (rango **68–110**) · Confianza **Baja** · *sin cambio* |
| Coste | **4.000 €** |
| Tokens | 6,00 M in / 0,84 M out (24 h IA, ratio 0,30) |
| Impacto | Ingesta de audio, separación de fuentes, extracción de melodía y estructura, `AUDIO_TO_AUDIO`, **gate de derechos en la ingesta** |
| Dependencias | C-01, C-06 (separación), C-10 (derechos) |

**El riesgo aquí es legal, no técnico.** Es literalmente una puerta de entrada para que alguien suba una canción con copyright y genere una obra derivada. Para una empresa cuya motivación es *reducir* riesgo de derechos, construir esto sin un **gate de titularidad obligatorio y auditable en la ingesta** sería contradictorio. Criterio de aceptación acordado: la declaración de titularidad es **bloqueo duro**, no una casilla (spec §5.2).

**Y el mismo patrón, ahora también en C-01.** Este gate era el **único** de su clase en todo el catálogo: la revisión 3 lo replica sobre la **letra** de entrada (D-21, +8 h en C-01), porque una letra con copyright produce una obra derivada exactamente igual que un audio con copyright — solo que con manifiesto impecable y sin nadie mirando. C-08 hereda el mismo componente de declaración, así que parte de sus 80 h se apoyan en trabajo ya hecho en la Fase 1.

### C-09 · Fine-tuning de modelos propios

| Campo | Valor |
|-------|-------|
| Complejidad | **Crítica** |
| Esfuerzo | **400 h** (rango **300–500**) · Confianza **Baja** · *rev. 1: 200 h — **estaba subestimada al 50 %*** |
| Coste | **20.000 €** (+ **626–1.095 €** de GPU por ciclo de iteración) |
| Tokens | 45,00 M in / 6,30 M out (180 h IA, ratio 0,45) |
| Impacto | Pipeline de dataset, captioning, arnés de entrenamiento, orquestación de GPU, tracking de experimentos, protocolo de evaluación, publicación con promoción y rollback |
| Dependencias | C-11 (`FINE_TUNABLE`); **I-03 bloqueante**; **I-01 bloqueante** |

**Por qué se dobla de 200 h a 400 h — y por qué eso refuerza aplazarla.** 200 h eran el arnés de entrenamiento; el trabajo real es el pipeline de datos:

| Subsistema | Horas |
|---|---|
| Pipeline de dataset: ingesta, limpieza, segmentación, deduplicación, **metadatos de licencia por pista** | 90 h |
| Captioning automático (HeartCLAP) + control de calidad de etiquetas | 60 h |
| Arnés de entrenamiento (LoRA y completo), configuración, checkpointing | 80 h |
| Orquestación de GPU de entrenamiento y reanudación | 40 h |
| Tracking de experimentos, comparación y reproducibilidad | 40 h |
| Protocolo de evaluación contra el modelo base (método de G1) | 50 h |
| Publicación en el registry, promoción y rollback en un paso | 40 h |

**Es ahora, con diferencia, la característica más cara del proyecto: ≈ el 24 % del presupuesto (400 h de 1.638).** Tres bloqueos, en orden de gravedad:

1. **Sin dataset no hay nada** (I-03). Y entrenar con material no licenciado reproduciría exactamente el problema que motivó la iniciativa.
2. **Perfil de equipo** (I-01). Esto es ingeniería de ML con evaluación empírica, no desarrollo de aplicaciones. No consta ese perfil. Contratarlo o subcontratarlo es coste **adicional** a estas 400 h.
3. **Compute recurrente**: ≈ 626 € por ciclo en spot, y rara vez basta un ciclo.

**Y aquí está la ironía del proyecto entero.** C-09 es la **única vía a una procedencia de datos realmente limpia** — lo único que resolvería el problema que motiva la iniciativa (§10.7). Que sea la característica más cara, la peor estimada y la única bloqueada por completo es el hecho más importante de esta evaluación. Merece iniciativa y presupuesto propios, no un hueco en la fase 1.

> **🆕 Nota informativa 2026-08-18 (vía LoRA, no cambia el no-go).** El repo oficial `ACE-Step-1.5` (MIT) incluye entrenamiento **LoRA de un clic** desde su Gradio (8 canciones, ≈1 hora en una RTX 3090 de 12 GB, con tutorial oficial y toolkit CLI avanzado — LoKR, optimización de VRAM). Esta vía **reduciría potencialmente el esfuerzo de C-09 en un orden de magnitud** frente a las 400 h estimadas para fine-tuning completo. **El bloqueo real sigue siendo I-03** (catálogo licenciado): sin dataset, un arnés de entrenamiento más barato no cambia nada. El no-go de la Fase 4 **no cambia**. Existe además la serie **XL** de ACE-Step (`xl-base`/`xl-sft`/`xl-turbo`, DiT 4B, ≥12 GB con offload/≥20 GB recomendado, mayor calidad de audio), candidata a considerarse en el spike de Fase 0 (`T-03`/`T-05`) y en el gate G1 si la VRAM local lo permite — ver `improvement-plan.md` §13.

### C-10 · Trazabilidad de licencias y derechos del audio generado → **partida en C-10a (Fase 1) + C-10b (Fase 2)**

> **🔴 Cambio estructural de la revisión 3 (D-20).** La revisión 2 ponía **las 105 h en la Fase 2**. Eso producía tres contradicciones que ninguna cantidad de margen arregla:
>
> 1. El **criterio de aceptación de C-01** (Fase 1) exigía «manifiesto de procedencia completo» — **que no existía hasta la Fase 2**. La Fase 1 no se podía cerrar.
> 2. La **regla 4 del contrato del registry** obligaba a los adapters a emitir `provenance` **en un formato que legal no había firmado**. Se implementaba primero y se pedía permiso después.
> 3. La Fase 1 corre **≥ 2 semanas generando audio sin ledger**, y **una cadena WORM no admite backfill**. Ese audio —el de las primeras pruebas reales, el que se enseña para justificar la Fase 2— habría quedado **fuera de la cadena de custodia para siempre**, en el proyecto cuya razón de ser es la trazabilidad. Y a G2 se le prometía «el registro de C-10».
>
> **El total de C-10 no cambia: 105 h.** Cambia **cuándo**: 38 h en la Fase 1, 67 h en la Fase 2.

#### C-10a · Manifiesto v1 + ledger append-only (**Fase 1**)

| Campo | Valor |
|-------|-------|
| Complejidad | Media-alta |
| Esfuerzo | **38 h** (rango **33–44**) · Confianza **Media** |
| Coste | **1.900 €** |
| Tokens | 1,90 M in / 0,27 M out (7,6 h IA, ratio 0,20) |
| Impacto | Esquema del manifiesto **firmado por legal**, emisión en **cada** generación desde la primera pista, ledger **append-only con cadena de hashes**, invariante en CI, `manifest_schema_version` con verificador multi-versión |
| Dependencias | C-13. **Y es dependencia de C-11 y de C-01**, no al revés: el esquema se firma **antes** de implementar el contrato del registry |

| Subsistema | Horas |
|---|---|
| Manifiesto v1: esquema (incluye `lyrics_declaration` y `source_generation`), emisión en cada generación, invariante en CI | 23 h |
| **Ledger append-only con cadena de hashes** (cada registro incluye el hash del anterior) y validación de extremo a extremo | 12 h |
| **Firma del esquema por legal** antes de implementar C-11: preparación del documento e integración de su criterio | 3 h |

De esas 23 h, **3 h son el `manifest_schema_version` y su verificador multi-versión con corpus de manifiestos en CI**. Es la pieza que hace que subir la versión del esquema en la Fase 2 (cuando llegue C2PA) **no invalide la verificación de las pistas de la Fase 1** — que es exactamente lo que el ledger promete que no pasará.

#### C-10b · C2PA, WORM, certificado y watermarking (**Fase 2**)

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **67 h** (rango **57–76**) · Confianza **Media** |
| Coste | **3.350 €** |
| Tokens | 3,35 M in / 0,47 M out (13,4 h IA, ratio 0,20) |
| Impacto | **C2PA real** (firma, certificados, **custodia de clave en KMS**), WORM con object lock y sello diario, certificado JSON/PDF, watermarking |
| Dependencias | **C-10a** (mismo manifiesto versionado, sin backfill), C-11; **I-13 abierta**, **I-13b** para la licencia del watermarker |

| Subsistema | Horas |
|---|---|
| **C2PA real**: firma, gestión de certificados, cadena de confianza, verificador, **custodia de la clave en KMS gestionado con rotación anual y revocación documentada** | 32 h |
| **WORM** (D-18): object lock con retención sobre el ledger ya encadenado + sello diario firmado | 5 h |
| **Watermarking robusto a transcode a MP3 320** | **20 h `⚠️ condicionadas a I-13`** |
| Certificado exportable JSON + PDF | 8 h |
| Revisión final de legal del formato firmado | 2 h |

**Por qué C-10 subió de 72 h a 105 h en la revisión 2** (y sigue en 105): «manifiesto estilo C2PA» y «C2PA real» no son lo mismo — lo segundo lleva firma criptográfica, gestión de certificados y cadena de confianza verificable. Las 5 h de WORM de C-10b son menos que las 20 h originales **porque la cadena de hashes, que es el grueso, ya está construida en C-10a**: aquí solo queda activar el object lock y el sello diario.

> **⚠️ Advertencia de presupuesto sobre el watermarking.** Las 20 h asumen **integrar una librería existente**. **Actualización 2026-08-18 (verificada contra fuentes primarias):** ya hay **dos candidatos con licencia MIT** (código y pesos) — **SilentCipher** (Sony, robusto a MP3/OGG/AAC, umbral psicoacústico, mensaje de 40 bits) y **AudioSeal** (Meta, MIT desde abril 2024, pensado para voz, robustez en música por validar). La trampa circular de licencia que motivaba esta advertencia **queda mitigada con estos dos candidatos**, pero I-13 **no se cierra**: falta ejecutar la prueba de robustez sobre música transcodificada, que es precisamente el trabajo de `T-57` en F10. Si esa prueba falla en ambos candidatos, la advertencia original (trabajo de nivel investigación, no cabe en 20 h) vuelve a aplicar.

**Sigue siendo la característica con mejor relación valor/coste del catálogo**, y su criterio de aceptación **lo pone legal, no ingeniería** (I-05): hay que involucrarlos en el diseño del manifiesto, no presentárselo terminado — y ahora eso tiene fecha: **la firma del esquema es precondición de C-11**. Pero conviene no confundirse sobre qué entrega: **C-10 documenta el problema de procedencia; no lo resuelve** (§10.7).

### C-11 · Model registry pluggable

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **147 h** (rango **127–167**) · Confianza **Media** · *rev. 1: 72 h · rev. 2: 130 h* |
| Coste | **7.350 €** |
| Tokens | 7,35 M in / 1,03 M out (29,4 h IA, ratio 0,20) |
| Impacto | Contenerización de dos modelos, contrato y descriptor, dos adapters, **suite de conformidad perceptual**, versionado inmutable, protocolo de G1, **matriz de capacidades verificadas**, **fichas de licencia del pipeline** |
| Dependencias | C-13, **C-10a** (el esquema del manifiesto que la regla 4 exige, firmado por legal **antes** de implementar este contrato) |

**Por qué sube de 72 h a 130 h (rev. 2) y a 147 h (rev. 3).** Las 72 h no contaban el trabajo real de poner dos modelos a funcionar: **solo contenerizar ACE-Step y HeartMuLa (CUDA, dependencias, pesos) son 40–60 h**, lo que dejaba ~56 h netas para contrato + 2 adapters + router + formulario dinámico + versionado + conformidad. No daba.

| Subsistema | Horas |
|---|---|
| **Contenerización de ACE-Step 1.5 y HeartMuLa** (CUDA, deps, pesos, solo `safetensors`) | 50 h |
| Contrato, descriptor, persistencia y **versionado inmutable** `id@version` | 24 h |
| **Dos adapters reales** sobre el contrato | 24 h |
| **Suite de conformidad perceptual** (invariantes exactos + CLAP/WER sobre briefs fijos) | 20 h |
| **Protocolo escrito del gate G1** (rúbrica, muestras, umbrales, evaluadores) | 4 h |
| Spike comparativo de modelos (Fase 0) | 8 h |
| **🆕 Matriz de capacidades verificadas** en el spike de Fase 0: probar de verdad `SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING` y `CONTINUATION` en ACE-Step y HeartMuLa, con evidencia por modelo | **12 h** |
| **🆕 Fichas de licencia verificada de las herramientas de la Fase 1** (I-13b): ffmpeg y codificadores, HeartCodec/HeartTranscriptor, pesos de ambos modelos | **5 h** |

> **Por qué 12 h en la Fase 0 valen 276 h en la Fase 3.** Un descriptor puede **declarar** capacidades; el spike las **verifica**. C-07 (140 h) y C-08 (80 h) dependen de que `SECTION_INPAINT` y `AUDIO_TO_AUDIO` existan de verdad en el modelo elegido — y con el plan de la revisión 2 eso **se descubría en la Fase 3, con las 276 h ya comprometidas**. Es la definición de información barata que llega tarde: 12 h en la semana 4 en lugar de una sorpresa en la semana 20. Si la matriz sale vacía, C-07 y C-08 **se replantean o se caen**, y esa es una decisión de 16.560 € tomada con datos.
>
> **G1 y G1-bis (D-27).** El protocolo de §10.2 decía que cada brief se genera «con ACE-Step 1.5 **y HeartMuLa**», pero la contenerización de HeartMuLa está **aquí**, en la Fase 1, **después** de G1. El gate era inejecutable como estaba escrito. Se resuelve: **G1 evalúa solo ACE-Step** (el único modelo de la Fase 0), y **HeartMuLa pasa G1-bis** con el mismo protocolo al registrarse su adapter, como **condición de sus horas**: si no pasa, no se cierra el adapter y se replantea el segundo modelo antes de seguir.

**Recorte de alcance: qué entra y qué no (D-16).** Se abstrae en la **segunda** instancia, no en la primera.

- ✅ **Dentro de fase 1**: contrato y descriptor con `provenance` **obligatorio** (barato y alimenta C-10) · **dos adapters reales** — es la única forma de saber si la abstracción es correcta · suite de conformidad · versionado inmutable.
- ❌ **Fuera de fase 1: el router de capacidades.** Con un modelo desplegado es un `return "ace-step"`. Se construye cuando haya un tercer modelo que lo justifique (≈ 12 h, **no presupuestadas aquí**).
- ❌ **Fuera, y no por coste: el formulario dinámico desde `params_schema`.** Cuesta más que escribir 2–3 formularios a mano **y da peor UX**: widgets genéricos, sin etiquetas de dominio, sin orden, sin validación cruzada. `params_schema` se queda como **validación de contrato en la API**, que es donde aporta.

**Dos correcciones de fondo al contrato de la revisión 1:**

1. **La regla 2 era falsa.** «Añadir un modelo = cero cambios en frontend» solo es cierto para un modelo que aporte capacidades **ya soportadas** por la UI. Un modelo que estrene `AUDIO_TO_AUDIO` o `SECTION_INPAINT` **necesita affordances nuevas sí o sí** (subida de audio, selección de región sobre la forma de onda). El registry evita reescribir el backend; no hace magia en el frontend.
2. **La suite de conformidad no puede basarse en «casos dorados por semilla fija».** Ese diseño se apoyaba en un supuesto no verificado y probablemente falso: **la inferencia de difusión en GPU no es bit-reproducible** entre versiones de driver, cuDNN o kernels de atención. Sería *flaky* en el primer `pip upgrade` — y como es el **gate obligatorio para registrar modelos**, se convertiría en un **single point of failure del proceso de desarrollo**. Redefinida como **tolerancia perceptual**: CLAP y WER dentro de umbral, más invariantes exactos de esquema, duración, sample rate, loudness y procedencia emitida (D-13).

**Dos invariantes de seguridad que faltaban** y que ahora son condición de registro:

- **Solo `safetensors`. Nunca `pickle` / `torch.load` sobre checkpoints no confiables** (D-14): eso es **ejecución remota de código** directa. `weights_sha256` verifica **integridad**, no **inocuidad**.
- **Aislamiento de las credenciales de storage del runner** (D-15): hoy el runner corre **código de adapter de terceros** con acceso al almacenamiento. Solo URLs firmadas de alcance por trabajo, token efímero, prefijo de bucket por trabajo y red de salida restringida. La prueba negativa de aislamiento es criterio de aceptación (spec §5.2).

Sigue siendo **la decisión de arquitectura mejor justificada del proyecto** — el trade-off documentado LM vs. difusión significa que ningún modelo va a ganar en todo — pero **dos adapters bastan para demostrarlo**.

### C-12 · Autenticación (SSO social + usuario/contraseña + 2FA configurable)

| Campo | Valor |
|-------|-------|
| Complejidad | Baja-media |
| Esfuerzo | **28 h** (rango **24–32**) · Confianza **Alta** · *rev. 1: 48 h — **estaba inflada*** |
| Coste | **1.400 €** |
| Tokens | 1,00 M in / 0,14 M out (4 h IA, ratio 0,14) |
| Impacto | Auth.js con OAuth social y corporativo + credenciales, TOTP con otplib, códigos de respaldo, JWKS en FastAPI, roles, auditoría de accesos |
| Dependencias | C-13 |

**Corrección de la revisión 1.** Se justificaban 48 h diciendo que «el 2FA con códigos de respaldo se lleva la mitad del esfuerzo». No es cierto con librerías maduras: **TOTP + recuperación son 8–12 h**, no 24. Desglose: Auth.js con proveedores OAuth y credenciales 10 h · **otplib + tabla de códigos de respaldo de un solo uso** 10 h · validación de JWT vía JWKS, roles y auditoría 8 h.

Requisito explícito del usuario, terreno bien pisado, confianza alta. Este es el ejemplo de por qué el margen del 20 % no arregla una estimación: **compensar 20 h infladas aquí contra 70 h que faltaban en C-13 daría un total plausible y dos números falsos.**

### C-13 · Cimientos de plataforma

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **214 h** (rango **184–244**) · Confianza **Media** · *rev. 1: 120 h · rev. 2: 190 h* |
| Coste | **10.700 €** |
| Tokens | 8,03 M in / 1,12 M out (32,1 h IA, ratio 0,15) |
| Impacto | Todo el suelo de la plataforma: monorepo, datos **con linaje**, storage, cola, estados, tiempo real, biblioteca, reproductor, audio **a 48 kHz con loudness por destino**, compartición, i18n, CI/CD, IaC, observabilidad |
| Dependencias | Ninguna (es la base) |

**Por qué sube de 120 h a 190 h (rev. 2) y a 214 h (rev. 3): no es un subsistema, son doce — y cinco decisiones que había que dejar tomadas.** Presupuestar 120 h para esto era presupuestar el suelo por debajo de su suelo.

| Subsistema | Horas |
|---|---|
| Monorepo, tooling, tipos compartidos, contrato OpenAPI | 16 h |
| Esquema Postgres + migraciones Alembic reversibles | 20 h |
| Object storage, URLs firmadas y **escritura en dos fases** | 16 h |
| Redis + cola (`arq`/Celery) + **idempotencia, DLQ y cuarentena de poison jobs** | 24 h |
| Máquina de estados del trabajo | 12 h |
| Progreso en tiempo real por SSE/WebSocket | 12 h |
| Biblioteca: listado, filtros, búsqueda | 16 h |
| **Reproductor persistente** (+ base multipista que C-06 reutiliza) | 18 h |
| ffmpeg: transcode FLAC/MP3/WAV + **loudness EBU R128** | 14 h |
| CI/CD: pruebas, build, despliegue a `stage` | 16 h |
| IaC básica y entornos | 10 h |
| Observabilidad OTel, métricas de cola y **coste por generación** | 16 h |
| **🆕 Linaje en el esquema desde la primera migración** (D-22): `parent_id`, `root_id`, `derivation_kind`, `section_map` nullable, y `source_generation` en el manifiesto v1 | **8 h** |
| **🆕 Exportación a 48 kHz** con resample **soxr** vía ffmpeg + **objetivo de loudness parametrizado por destino** (broadcast −23 / streaming −14 / stems sin normalizar) | **6 h** |
| **🆕 Compartición correcta** (D-24): la URL compartible es la de la pista **en la aplicación** (requiere sesión); las URLs firmadas quedan como mecanismo interno del reproductor | **4 h** |
| **🆕 i18n con `next-intl`** desde el día 1, UI en castellano, cero cadenas hardcodeadas (D-25) | **4 h** |
| **🆕 Checkpoint de stop-loss al cierre de C-13 + runbook de desmantelamiento** de una página (D-28) | **2 h** |

**No estaba en la lista de 10, pero sin esto ninguna de las 10 existe.** Es greenfield: no hay código, ni pipeline, ni esquema. Incluye la instrumentación de coste por generación, que es lo que permite aplicar la regla de cambio de §6.3 — y sin la cual el tope de gasto de D-17 no se puede implementar.

> **Las 8 h de linaje son las que más se ahorran a sí mismas.** El flujo de la spec §4 ya promete **variantes y extensión en la Fase 1**, y la UX de referencia trabaja con **pares de variantes**. Con el esquema de la revisión 2, C-07 (Fase 3) habría empezado con **una migración de datos en producción** sobre tablas con valor legal, y los manifiestos de las derivadas **no habrían podido referenciar a su padre**. Ocho horas en la semana 6 contra una migración de linaje en la semana 20.
>
> **Y las 6 h de 48 kHz son la diferencia entre entregable y reprocesable.** Los modelos generan a 44,1 kHz; el estándar de Avid/Premiere/broadcast es **48 kHz**. Sin resample, cada pista se retoca a mano en la sala de montaje — que es exactamente el trabajo que esta plataforma dice ahorrar. El objetivo de loudness por destino se fija con el supervisor musical en la Fase 0, no se adivina.

### C-14 · Infraestructura GPU y orquestación de inferencia

| Campo | Valor |
|-------|-------|
| Complejidad | Alta |
| Esfuerzo | **139 h** (rango **119–159**) · Confianza **Media** · *rev. 1: 80 h · rev. 2: 120 h · rev. 3: 123 h* · **(+16 h `T-85`/D-29, ampliación 2026-08-18)** |
| Coste | **6.950 €** (+ coste de GPU, §6) |
| Tokens | 7,70 M in / 1,08 M out (30,8 h IA, ratio 0,25) — *corresponden a las 123 h previas a `T-85`; el delta (+4 h IA ≈ +1,00 M in / +0,14 M out) no está propagado a los agregados, ver nota de §8* |
| Impacto | Runner GPU, **caché de imagen y de pesos**, aprovisionamiento multiproveedor, keep-warm y **un** pod caliente con calendario, **despacho FIFO + round-robin por usuario**, presupuesto de GPU, circuit breaker, tope de gasto y kill switch |
| Dependencias | C-13, C-11 |

**Por qué sube de 80 h a 120 h (rev. 2) y a 123 h (rev. 3).** Descontando el spike de 24 h, quedaban **56 h netas** para aprovisionamiento multiproveedor, circuit breaker y failover. No daba. **La ampliación `T-85`/D-29 (2026-08-18, ratificada) añade 16 h más: 139 h.**

| Subsistema | Horas |
|---|---|
| Imagen del runner (CUDA + torch + deps) y **caché de imagen en el host** (S-01b, el término dominante del arranque en frío) | 20 h |
| Caché de pesos en volumen persistente | 6 h |
| Aprovisionamiento multiproveedor (adaptador on-demand/serverless, 2 proveedores) | 20 h |
| **Keep-warm con idle timeout + pod caliente programado** con **horario `Europe/Madrid`, laborables y calendario ajustable por el admin** (D-05b) | 12 h |
| Despacho cola→pod, timeouts, reintentos, `max_gpu_seconds`, **FIFO con fairness round-robin por usuario** (D-26) | 14 h |
| **Circuit breaker por proveedor y failover** sin pérdida de trabajos | 14 h |
| Telemetría de coste, **tope de gasto agregado y kill switch** (D-17) | 10 h |
| **Spike de Fase 0**: tiempos de inferencia, VRAM con y sin offloading, arranque en frío real | 24 h |
| **🆕 Medición de 2 inferencias concurrentes en los 48 GB de la L40S** (throughput y VRAM pico simultáneo) | **3 h** |
| **🆕 Modo GPU local (`T-85`/D-29, ampliación 2026-08-18)**: proveedor `GPU_PROVIDER=local` con NVIDIA Container Toolkit, perfil compose `gpu-local`, detección de VRAM y offloading automático | **16 h** |

**El hueco concreto que la revisión 2 cerró:** la revisión 1 cacheaba **los pesos** en volumen persistente y **no la imagen del contenedor**, que es el término dominante del arranque en frío (120–300 s de pull de 8–15 GB). Está ahora dentro de las 20 h de la primera línea.

El spike valida S-02, cierra I-07 y mide el **VRAM pico con y sin offloading**, que es lo que la confirmación 10 del usuario obliga a comprobar antes de elegir GPU (§6.2, opción H).

> **Las 3 h nuevas más rentables del presupuesto.** La L40S tiene **48 GB** y ACE-Step ocupa ~7 GB en fp16: si caben **dos inferencias concurrentes** sin degradar el tiempo por pista, el **throughput se dobla a coste cero** y las esperas de la spec §12.1 (≈ 8 h para el último de 100 trabajos encolados) se parten por dos **sin pagar un segundo pod**. Tres horas de medición para responder a una pregunta que, si sale bien, evita ≈ 128 €/mes de pod extra y una queja recurrente de usuario.

---

## 8. Tabla comparativa

Ordenada por fase propuesta. Horas y coste **base**, con rango.

| ID | Característica | Compl. | Horas | Rango | Coste | Tokens (M in/out) | Confianza | Valor | Riesgo | Fase |
|----|----------------|--------|-------|-------|-------|-------------------|-----------|-------|--------|------|
| C-13 | Cimientos de plataforma | Alta | **214** | 184–244 | 10.700 € | 8,03 / 1,12 | Media | Habilitante | Bajo | **1** |
| C-11 | Model registry (recortado, D-16) | Alta | **147** | 127–167 | 7.350 € | 7,35 / 1,03 | Media | **Muy alto** (estructural) | Medio | **1** |
| C-14 | Infraestructura GPU + orquestación (incl. `T-85`/D-29) | Alta | **139** | 119–159 | 6.950 € | 7,70 / 1,08 | Media | Habilitante | Medio | **1** |
| C-01 | Generación letra + prompt de estilo | Media-alta | **78** | 68–88 | 3.900 € | 4,88 / 0,68 | Media | **Muy alto** (núcleo) | Medio | **1** |
| **C-10a** | **Manifiesto v1 + ledger append-only** (D-20) | Media-alta | **38** | 33–44 | 1.900 € | 1,90 / 0,27 | Media | **Muy alto** (razón de ser) | Medio | **1** |
| C-12 | Autenticación + 2FA | Baja-media | **28** | 24–32 | 1.400 € | 1,00 / 0,14 | **Alta** | Alto (requisito) | Bajo | **1** |
| C-02 | Instrumental sin voz | Baja | **12** | 10–16 | 600 € | 0,50 / 0,07 | **Alta** | Alto | Bajo | **1** |
| **C-10b** | **C2PA + WORM + PDF + watermarking** | Alta | **67** | 57–76 | 3.350 € | 3,35 / 0,47 | Media | Alto | Medio (**I-13 abierta**) | **2** |
| C-06 | Stems separados | Media | **40** | 34–52 | 2.000 € | 2,50 / 0,35 | Media | Alto | Bajo (**I-13b**) | **2** |
| C-05 | Asistente IA de letras | Baja-media | **24** | 20–28 | 1.200 € | 0,90 / 0,13 | **Alta** | Alto | Bajo | **2** |
| C-07 | Extender / regenerar secciones | Alta | **140** | 120–160 | 7.000 € | 10,50 / 1,47 | **Baja** | Medio-alto | **Alto** | **3** |
| C-08 | Cover / remezcla | Alta | **80** | 68–110 | 4.000 € | 6,00 / 0,84 | **Baja** | Medio | **Alto (legal)** | **3** |
| C-03 | Selector de tipo de voz | Alta | **56** | 48–80 | 2.800 € | 5,50 / 0,77 | **Baja** | Medio | Alto | **3** |
| C-09 | Fine-tuning de modelos propios | **Crítica** | **400** | 300–500 | **20.000 €** | 45,00 / 6,30 | **Baja** | Alto a medio plazo | **Muy alto (bloqueado)** | **4** |
| C-04 | Clonación de voz propia | **Crítica** | **175** | 150–200 | 8.750 € | 17,50 / 2,45 | **Baja** | Medio | **Muy alto (RGPD)** | **4** |
| | **Subtotal: 10 del usuario** (C-01…C-10, con C-10 = C-10a + C-10b) | | **1.110** | 908–1.354 | **55.500 €** | 98,53 / 13,80 | | | | |
| | **Subtotal: 4 transversales** (C-11…C-14) | | **528** | 454–602 | **26.400 €** | 24,08 / 3,37 | | | | |
| | **TOTAL** | | **1.638** | **1.362–1.956** | **81.900 €** | **122,61 / 17,17** | | | | |

> **Correcciones de aritmética de la revisión 3 en esta tabla.** El subtotal «10 del usuario» de la revisión 2 declaraba **98,88 / 13,84 M** de tokens y un rango de **906–1.362 h**; las sumas reales de C-01…C-10 eran **97,88 / 13,71 M** y **896–1.342 h** (se había colado C-12 en la suma de tokens). El TOTAL de 120,00 / 16,80 M sí era correcto. Las cifras de arriba son las de la revisión 3, ya recalculadas con el alcance nuevo, y **cada columna suma sus filas**.

> **Nota de tokens (2026-09-01).** Los agregados de tokens de esta tabla y de §9 **no incluyen el delta de `T-85` (+16 h)**: con el ratio 0,25 de C-14 serían **+4 h IA ≈ +1,00 M input / +0,14 M output** — efecto ≪ 1 %. Se deja constancia visible en lugar de recalcular toda la cascada de tokens y supervisión.

**Nota sobre el rango agregado.** El total de 1.638 h es la **suma de los puntos medios**, no el centro del rango agregado (1.659 h): las estimaciones de confianza baja están **sesgadas al alza**, así que el escenario pesimista está 318 h por encima del punto medio y el optimista solo 276 h por debajo. Con margen del 20 %, el rango es **1.634,4–2.347,2 h** = **81.720–117.360 €**.

---

## 9. Presupuesto total

### 9.1 Esfuerzo y coste

| Concepto | Base | Con margen (+20 %) |
|----------|------|--------------------|
| **Esfuerzo humano** | **1.638 h** | **1.965,6 h** |
| **Coste humano** (× 50 €/h) | **81.900 €** | **98.280 €** |
| Horas de agente IA | 490,4 h | 588,5 h |
| Supervisión humana (25 %) | 122,6 h | 147,1 h |
| **Coste de supervisión** (× 50 €/h) | **6.130 €** | **7.356 €** |
| Tokens input | 122,61 M | 147,13 M |
| Tokens output | 17,17 M | 20,60 M |
| **Coste de tokens** (precio **verificado**) | **959 €** | **1.151 €** |
| Infraestructura GPU de inferencia | **45–128 €/mes** (§6.3) | ídem |
| GPU de entrenamiento (solo C-09) | 626–1.095 € por ciclo | ídem |
| Almacenamiento | 0,7 € → 8 €/mes (mes 1 → mes 12, §6.6) | ídem |
| **OPEX de mantenimiento** (≈ 15 %/año) | 7.100 €/año (Fases 1+2) | 14.700 €/año (catálogo completo) |
| **Horas de no-desarrollo** (legal, DPO, supervisor musical) | **116 h** (§6.5d) — **no son horas de desarrollo** | `⚠️ tarifa interna I-18` |

> **Nota (2026-09-01).** Las filas de esfuerzo y coste humano incluyen ya las +16 h de `T-85`/D-29; las filas de horas IA, supervisión y tokens **no incluyen el delta de `T-85`** (+4 h IA ≈ +1,00 M in / +0,14 M out; efecto ≪ 1 %, ver nota de §8). El coste de supervisión con margen se corrige de 7.350 € a **7.356 €** (490,4 × 1,2 × 0,25 × 50): era un redondeo, no una reestimación.

**Coste de tokens: precio verificado, ya no es una sensibilidad.** La revisión 1 dejaba el precio a 0 (un hueco parece gratis); la revisión 2 lo acotó por sensibilidad; el 2026-07-27 se **verificó contra la documentación oficial** y se escribió en `.claude/rates.json`. **I-06 y R-14 quedan cerradas.** *(La revisión 3 recalcula el importe —938 → **959 €** base y 1.126 → **1.151 €** con margen— porque las horas de agente suben de 480 a 490,4 con el alcance nuevo; el precio unitario es el mismo.)*

```
Coste_IA (€) = (Tokens_in × Pin + Tokens_out × Pout) × 0,92     [Pin/Pout en USD por millón]
Modelo: Claude Opus 5 · Pin = 5 $/M · Pout = 25 $/M · verificado 2026-07-27
```

| Base | Cálculo | Coste |
|---|---|---|
| Sin margen | (122,61 × 5 + 17,17 × 25) × 0,92 = 1.042 $ | **959 €** |
| Con margen (+20 %) | (147,13 × 5 + 20,60 × 25) × 0,92 = 1.251 $ | **1.151 €** |

El resultado cae en la mitad baja de la banda estimada en la revisión 2 (676–3.378 €) y confirma que **el coste de tokens es inmaterial: el 1,2 % del coste humano**. Dos palancas documentadas si algún día dejara de serlo: la **Batch API** descuenta el 50 % sobre input y output en trabajo no interactivo, y un **acierto de caché** cuesta 0,1× el precio de input. Precio de referencia: [documentación oficial de precios](https://platform.claude.com/docs/en/about-claude/pricing).

### 9.2 Productividad IA

| Métrica | Base | Con margen (+20 %) |
|---------|------|--------------------|
| Horas humanas (referencia) | 1.638 h | 1.965,6 h |
| Horas IA | 490,4 h | 588,5 h |
| Supervisión (25 %) | 122,6 h | 147,1 h |
| **Horas totales** (IA + supervisión) | **613 h** | **735,6 h** |
| **Horas ahorradas** | **1.025 h** | **1.230 h** |
| **Ahorro** | **62,6 %** | **62,6 %** |
| **Multiplicador** | **2,67×** | **2,67×** |
| **FTE equivalente ahorrado** | 6,4 empleado-mes | 7,7 empleado-mes |

*(El multiplicador pasa de 2,74× (rev. 1) a 2,61× (rev. 2) y a **2,65×** (rev. 3). Sube ligeramente porque el alcance nuevo de la revisión 3 —linaje en el esquema, i18n, gate de derechos de la letra, compartición, resample— es trabajo de aplicación **bastante comprimible por un agente**, al contrario que los cimientos y el dataset que dominaban la subida de la revisión 2. Las horas de escucha y de investigación siguen sin comprimirse: ver §9.3. Con la ampliación `T-85` en las horas de referencia y su delta IA sin propagar —nota de §8—, el multiplicador queda en **2,67×** desde el 2026-09-01.)*

### 9.3 Sensibilidad de la supervisión (lectura honesta)

El 25 % de `rates.json` es un buen promedio para desarrollo de aplicaciones, pero **no para investigación de ML ni para evaluación de calidad de audio**: ahí la supervisión es escucha humana y criterio, y no se comprime. En C-03, C-04, C-07, C-08 y C-09 hay **338 h IA de las 490,4**; si en ellas la supervisión real es del 50 %:

| Métrica | Escenario 25 % uniforme | Escenario diferenciado (50 % en investigación) |
|---------|------------------------|----------------------------------------------|
| Supervisión total | 122,6 h | **207,1 h** |
| Horas totales | 613 h | **697,5 h** |
| Coste de supervisión | 6.130 € | **10.355 €** |
| Multiplicador | 2,65× | **2,33×** |
| Ahorro | 62,2 % | **57,0 %** |

La conclusión no cambia (la ejecución asistida sigue ahorrando más de la mitad), pero **el segundo escenario es el que conviene presupuestar** si se aprueban las Fases 3 y 4. Y por si quedaba duda: **las 40 h de supervisor musical de §6.5d no están en ninguno de los dos escenarios** — son horas de otra persona, con otra tarifa.

### 9.4 Duración de trabajo (no es un calendario comprometido)

> **⚠️ Aquí no hay fechas, y es a propósito.** La revisión 1 daba trece semanas con fechas concretas mientras **I-01 («¿quién lo hace?») seguía sin respuesta**. Un calendario con fechas y sin equipo asignado es una promesa que alguien va a citar. Esta tabla da **duraciones de trabajo en semanas relativas**; las fechas absolutas se fijan cuando I-01 tenga respuesta.

> **🔴 Corrección de la revisión 3 (suelo corregido a 25 el 2026-09-01): el calendario real son 25–28 semanas, no ~22.** La tabla de la revisión 2 sumaba **solo las semanas de desarrollo** y dejaba fuera, en una nota al pie, todo lo que no se comprime: la semana de G2, el timebox de decisión de los gates, y —el error más grave— **el «1 mes de uso real» que la propia tabla declaraba como precondición de la Fase 3**. Con la Fase 2 cerrando en S+15, la Fase 3 **no puede empezar antes de S+16**. Aquí las esperas son **filas**, no notas.

| Fase / gate | Contenido | Horas humanas base | c/margen | Coste c/margen | Horas IA+sup. | Duración | Semana | Precondición |
|------|-----------|--------------------|----------|----------------|---------------|----------|--------|--------------|
| **🔴 G2** | **Consulta a legal, dos preguntas** (I-05 procedencia + I-05b protegibilidad). 32 h de legal, **0 h de desarrollo** | — | — | `⚠️ I-18` | — | **~2 semanas** (consulta + timebox de decisión de 10 días laborables) | **S+0–S+1** | **Ninguna. Es lo primero** |
| **⏸️ Espera** | **Gobernanza**: decisión de dirección construir-vs-comprar con dos ofertas con indemnización sobre la mesa; **nombramiento del supervisor musical y de 3–5 usuarios piloto** (I-20) | — | — | — | — | ~1 semana | S+2 | G2 favorable |
| **0** | Spikes de viabilidad + **matriz de capacidades verificadas** + medición de 2 inferencias concurrentes + protocolo de G1 + contenerización mínima de ACE-Step *(sub-fila de la Fase 1: sus 67 h **están dentro** de las 640 h de abajo)* | *(67 h)* | *(80,4 h)* | *(4.020 €)* | *~23 h* | ~2 semanas | S+3–S+4 | Supervisor musical nombrado |
| **🟠 G1** | **Escucha ciega de ACE-Step** con el protocolo de §10.2 (10 briefs, líneas base de Suno y de librería, 3 evaluadores) + ratificación de umbrales + decisión | — | — | ~9 h de escucha (§6.5d) | — | ~2 semanas (timebox 10 días) | S+5–S+6 | Fase 0 cerrada |
| **1** | Walking skeleton: C-13, **C-10a**, C-11, C-14 (incl. `T-85`/D-29), C-01, C-12, C-02. Incluye **G1-bis** al registrar HeartMuLa y el **stop-loss al cierre de C-13** | **656 h** *(incl. las 67 h de Fase 0 y las 16 h de `T-85`)* | **787,2 h** | **39.360 €** | ~188 h | ~5 semanas de desarrollo tras la Fase 0 | S+7–S+11 | **G1 aprobado** |
| **⏸️ Espera** | **Puesta en uso**: alta de los usuarios piloto, verificación de criterios de aceptación, primeras pistas reales con manifiesto | — | — | — | — | ~1 semana | S+12 | Fase 1 entregada |
| **2** | Valor alto / coste medio: **C-10b**, C-06, C-05 | **131 h** | **157,2 h** | **7.860 €** | ~41 h | ~3 semanas | S+13–S+15 | Fase 1 en uso · **I-13** para el watermarking · **I-13b** para Demucs |
| **⏸️ Espera + 🟡 G3** | **1 mes de uso real** y **gate G3 de adopción** con números (§10.1): ≥ 100 generaciones, ≥ 3 usuarios activos, ≥ 1 pista usada en una producción real, encuesta ≥ 4/5. **0 h de desarrollo** | — | — | — | — | **~4 semanas** | S+16–S+19 | Fase 2 en uso |
| **3** | Control creativo avanzado: C-07, C-08, C-03 | **276 h** | **331,2 h** | **16.560 €** | ~132 h | ~5 semanas | S+20–S+24 | **G3 superado** + matriz de capacidades favorable |
| **4** | Alto coste / alto riesgo: C-09, C-04 | **575 h** | **690 h** | **34.500 €** | ~375 h | ~10 semanas | condicionada | I-03, I-05, I-01, DPIA |
| | **TOTAL** (Fases 0–4) | **1.638 h** | **1.965,6 h** | **98.280 €** | **~736 h** | **25–28 semanas hasta el cierre de la Fase 3** (+ ~10 si se aprobara la Fase 4) | | |

> **Nota sobre la base de las semanas (2026-09-01).** Las semanas por fase son **juicio experto, no se derivan de horas/semana constantes**; la Fase 1 asume dedicación intensiva (~2 FTE).

**Cómo se reparten esas 25–28 semanas.** ≈ **15 semanas de desarrollo** (2 de Fase 0 + 5 de Fase 1 + 3 de Fase 2 + 5 de Fase 3) y ≈ **10 semanas de gates y esperas** (2 de G2 + 1 de gobernanza + 2 de G1 + 1 de puesta en uso + 4 de uso real y G3). La banda de 25–28 recoge que los timebox de decisión pueden agotarse y que la escucha depende de la agenda de un supervisor musical que tiene otro trabajo. **Ninguna de estas semanas se puede comprimir con más agentes**: son decisiones humanas y uso real.

**Banda de la Fase 1, que es la cifra que se pide aprobar:**

| Escenario | Horas base | c/margen | Coste |
|---|---|---|---|
| Suelo (mínimos de cada rango) | **565 h** | 678 h | **33.900 €** |
| **Punto medio (petición)** | **656 h** | **787,2 h** | **39.360 €** |
| Techo (máximos de cada rango) | **750 h** | 900 h | **45.000 €** |

**Dicho explícitamente: la Fase 1 pasa de 22.800 € (rev. 1) a 33.000 € (rev. 2), a 38.400 € (rev. 3) y a 39.360 € con la ampliación GPU local (`T-85`/D-29, +960 €, ratificada el 2026-08-18).** *(La banda de la revisión 2 estaba además mal sumada: decía 466–634 h → 27.960–38.040 €, y la suma real de los rangos de sus seis características era **464–638 h → 27.840–38.280 €**. La banda de arriba corresponde ya a las **siete** características de la Fase 1 con el alcance nuevo.)*

**Lo que sube la Fase 1 de 550 h a 640 h:** **C-10a** (38 h, que estaban en la Fase 2 y no podían estar allí), el **gate de derechos de la letra** (8 h en C-01), **linaje, 48 kHz, compartición, i18n y stop-loss** (24 h en C-13), la **matriz de capacidades y las fichas de licencia** (17 h en C-11) y la **medición de concurrencia** (3 h en C-14). La Fase 2 baja de 165 h a **131 h** porque C-10b se queda con 67 de las 105 h de C-10. **La ampliación `T-85`/D-29 (2026-08-18) añade después 16 h más en C-14: 656 h / 39.360 €.**

**Lo que no se comprime, y por tanto ya está en la tabla como filas:** las dos semanas de legal (G2), los ciclos de escucha del supervisor musical (G1 y G1-bis), la puesta en uso, el mes de uso real con G3 y la DPIA de la Fase 4. Referencia sin IA: 1.965,6 h son **≈ 12,3 meses** de una persona a jornada completa, o **≈ 6,1 meses** con dos.

---

## 10. Recomendación

### 10.1 Veredicto y gates

**Go condicionado, por fases, y con una decisión de construir-vs-comprar tomada explícitamente antes de empezar.** El primer paso no cuesta desarrollo.

**Los gates, en el orden correcto** *(la revisión 1 los tenía al revés)*:

| Gate | Cuándo | Coste hasta ese punto | Criterio | Si falla |
|------|--------|----------------------|----------|----------|
| **🔴 G2 — Legal** | **Semana 0. ANTES de la Fase 0 y de cualquier gasto de desarrollo** | **0 € de desarrollo** · 32 h de legal | **Dos preguntas, misma consulta:** (a) **I-05** — ¿acepta legal por escrito audio generado por modelos cuya `training_data_declaration` es **«no divulgada»**, con el registro de C-10, para (a1) uso interno y (a2) **producciones comerciales de cliente**? · (b') **I-05b** — **¿es protegible y licenciable en exclusiva el output generado por IA sin autoría humana?** | Ver **matriz de resultados** abajo. No hay un único «si falla» |
| **🟠 G1 — Calidad (solo ACE-Step)** | Fin de la Fase 0 | **80,4 h / 4.020 €** de desarrollo + ~9 h de escucha | El protocolo numérico de §10.2, con línea base ciega contra Suno y contra la librería actual. **Evalúa solo ACE-Step**, que es el único modelo contenerizado en la Fase 0 (D-27) | **No-go de la iniciativa** o replanteo del catálogo de modelos |
| **🟠 G1-bis — Calidad del segundo adapter** | Dentro de la Fase 1, **al registrar el adapter de HeartMuLa** | Coste de la Fase 1 en curso | **Mismo protocolo de §10.2** aplicado a HeartMuLa. Es **condición de las horas del adapter**: sin pasarlo, el adapter no se da por entregado | Se replantea el segundo modelo. Si además la **adherencia a la letra** es insuficiente en ambos adapters, se activa la partida condicional del **tercer adapter (YuE) + router, ≈ 50 h no presupuestadas** |
| **🟡 G3 — Adopción** | **Entre la Fase 2 y la Fase 3**, tras **1 mes de uso real** | Fases 0+1+2 = **47.220 €** | Cuatro números, no impresiones: **≥ 100 generaciones** acumuladas · **≥ 3 usuarios activos** (que hayan generado en las últimas 2 semanas) · **≥ 1 pista usada en una producción real entregada** · **encuesta de satisfacción ≥ 4/5** entre los usuarios piloto | **No se aprueba la Fase 3 (16.560 €).** Si nadie la usa con lo ya entregado, el problema no se arregla con control creativo avanzado |
| **⏱️ Stop-loss intra-fase** | **Al cierre de C-13**, dentro de la Fase 1 | Parcial de la Fase 1 | **> 60 % del presupuesto de la Fase 1 consumido con < 40 % del alcance entregado** → parada y decisión de dirección, con el **runbook de desmantelamiento** de una página ya escrito (D-28) | Parada ordenada: se conserva ledger, manifiestos y pistas de producción; se da de baja el proveedor GPU; se destruye el resto con constancia |

#### Matriz de resultados de G2 (decidida **antes** de preguntar)

Un gate cuya única respuesta prevista es «sí» o «no» no es un gate: la respuesta más probable de un departamento legal ante esta pregunta es **intermedia**, y hay que tener la decisión tomada de antemano para que no la improvise quien esté en la sala.

| Respuesta de legal | Decisión pre-acordada |
|---|---|
| **«Sí total»** — vale para uso interno **y** para producciones comerciales de cliente | **Fase 1 completa según esta evaluación: 38.400 €.** Sigue el plan tal cual. ⚠️ *Cifra vigente: **39.360 €** — los 38.400 € son de la revisión 3, antes de la ampliación GPU local (`T-85`/D-29, +960 €) ratificada el 2026-08-18. Ver `tasks.md` §1. Nota de coherencia añadida por el orquestador `/dev-cycle` el 2026-08-18; esta fila es la que se aplicó al levantar G2.* |
| **«Sí solo interno / no para cliente»** — **la respuesta más probable** | **Decisión de dirección entre dos caminos, no continuación automática:** (a) **pivotar a compra** con indemnización contractual (§6.5b), que es lo que cubre el caso de cliente; o (b) **Fase 1 recortada con tope duro ≤ 20.000 €** y **reevaluación del caso de negocio** antes de cualquier fase posterior — una herramienta interna de maquetación y referencia musical vale mucho menos que una plataforma de producción, y el presupuesto tiene que reflejarlo |
| **«No»** | **Stop con 0 € de desarrollo gastados.** La iniciativa se reformula en torno a C-09 (bloqueada por I-03) o se sustituye por la opción de compra (§6.5b) |
| **Respuesta a I-05b: «el output puede no ser protegible»** | **No bloquea el build, pero cambia lo que se le promete al cliente.** Se documenta como limitación contractual y se traslada a la conversación comercial **antes** de firmar exclusividades. Afecta igual a la opción de compra: ningún proveedor puede licenciar en exclusiva lo que no está protegido |

> ⚠️ **Nota de coherencia (2026-08-18, orquestador `/dev-cycle`).** El **tope duro de ≤ 20.000 €** de la fila 2 se fijó contra la base de **38.400 €** de la revisión 3. Tras la ampliación GPU local (`T-85`/D-29, +960 €, ratificada el 2026-08-18) la base vigente es **39.360 €**. Si algún día se aplicara la fila 2, dirección debe confirmar si el tope sigue siendo 20.000 € o se reescala. **No aplica hoy**: el 2026-08-18 se aplicó la fila 1 («sí total») — ver `gates/g2-matriz-resultados.md` §10.

#### RACI de los gates (a rellenar con nombres antes de arrancar)

| Gate | Quién convoca | **Quién decide** | Timebox | Escalado |
|---|---|---|---|---|
| **G2** | Responsable de la iniciativa | **Dirección** (con el informe escrito de Legal) `⚠️ nombre pendiente` | **10 días laborables** desde la consulta | A dirección general si se agota |
| **G1 / G1-bis** | Responsable técnico | **Supervisor musical** (voto de calidad) + responsable de la iniciativa (voto de continuidad) `⚠️ nombre pendiente` | **10 días laborables** desde la entrega de las muestras | A dirección si no hay quórum de 3 evaluadores |
| **G3** | Responsable de la iniciativa | **Dirección**, con los cuatro números de adopción sobre la mesa `⚠️ nombre pendiente` | **10 días laborables** tras el mes de uso | A dirección general |
| **Stop-loss** | Responsable técnico (obligado a convocarlo al cierre de C-13) | **Dirección** | 5 días laborables | Inmediato |

**Regla común:** el desarrollador **no vota** en G1, G1-bis ni G3. Y ningún gate se cierra «por silencio»: agotado el timebox, escala.

**Por qué G2 va primero.** En la revisión 1 estaba «antes de producción, no antes del fin de la Fase 1», lo que autorizaba a gastar **33.000–38.400 €** antes de saber si el output es utilizable. **G2 no es una entrega de software: es una consulta de dos semanas**, y es el **único gate capaz de anular el 100 % del presupuesto**. Ponerlo después era una inversión del orden de riesgo difícil de defender.

**Que G1 cueste 80,4 h y 4.020 € frente a las 1.965,6 h del catálogo completo sigue siendo el mejor argumento a favor de este plan** — el **4,1 %** del esfuerzo compra la información que decide el otro **95,9 %**. *(La revisión 1 escribía «48 h invertidas, no 1.084», mezclando horas con margen contra horas base. Aquí las dos cifras están en la misma base: 80,4 h con margen frente a 1.965,6 h con margen.)*

**Fases, con la cifra de cada una:**

- ✅ **Go a Fase 0 + Fase 1** — 787,2 h / **39.360 €** con margen (banda 33.900–45.000 €, incl. la ampliación `T-85`/D-29). Entrega un producto usable de extremo a extremo, con la arquitectura correcta **y con trazabilidad desde la primera pista**.
- ✅ **Go a Fase 2 condicionado** a que la Fase 1 pase G1 y G1-bis y a que **I-13 e I-13b tengan respuesta** — 157,2 h / **7.860 €**. Mejor relación valor/coste del proyecto, pero C-10b arrastra el watermarking con candidatos MIT aún por validar en música (I-13) y C-06 la licencia de los pesos de Demucs.
- 🟡 **Fase 3 en revisión, ahora con gate propio** — 331,2 h / **16.560 €**. **Solo si G3 se supera** y si la matriz de capacidades del spike confirma que `SECTION_INPAINT` y `AUDIO_TO_AUDIO` existen. Aprobar característica a característica.
- ❌ **Fase 4 en no-go** — 690 h / **34.500 €** más compute de entrenamiento. **C-09 bloqueada por I-03**, **C-04 por RGPD**. La reestimación de C-09 a 400 h **refuerza** la recomendación: es ≈ el 24 % del presupuesto en lo único que hoy no se puede ni empezar.

**Antes de aprobar la Fase 1, cuatro decisiones que no son de ingeniería:**

1. **Construir o comprar** (§6.5). Pedir dos ofertas con cláusula de **indemnización comercial** en la misma semana de G2, y preguntar en ellas por la exclusividad (I-05b). Cuestan una llamada y pueden ahorrar 98.280 €.
2. **Reservar las 116 h de no-desarrollo y el OPEX de ≈ 7.100 €/año** (§6.5c, §6.5d). Sin propietario operativo (I-16), la entrega no tiene a quién entregarse.
3. **🆕 Nombrar al supervisor musical** (I-20). **Sin él, G1 no existe** — y sin G1 no hay decisión de calidad, solo una factura. Es **condición del veredicto**, no una tarea del plan.
4. **🆕 Nombrar 3–5 usuarios piloto con ≥ 2 h/semana comprometidas** (I-20). Sin ellos no hay **G3** que medir, la Fase 2 se construye a ciegas y la Fase 3 se aprueba por inercia.

### 10.2 Protocolo del gate G1 (esto es el gate; antes no había ninguno)

La revisión 1 vendía G1 como el mejor argumento del plan por fases y **no lo definía**: «la escucha ciega confirma que alcanzan el nivel exigible» no es un criterio, es una intención. **Un gate sin número lo decide quien esté en la sala, y quien está en la sala siempre decide «sigamos».** Escribirlo cuesta **4 h** (ya presupuestadas en C-11).

| Elemento | Definición |
|----------|-----------|
| **Muestras** | **10 briefs reales** extraídos de producciones de Daycry ya cerradas, con su brief musical original. **Cada brief se genera con ACE-Step 1.5 y solo con ACE-Step 1.5** *(corrección de la revisión 3: el protocolo decía «con ACE-Step 1.5 **y HeartMuLa**», pero la contenerización de HeartMuLa está en C-11, Fase 1, **después** de este gate — el protocolo era **inejecutable**. HeartMuLa pasa **G1-bis** con este mismo protocolo al registrarse su adapter, D-27)* |
| **Líneas base ciegas** | Para cada brief: (a) la salida de **Suno** y (b) **la pista de librería de producción que se usó realmente** en esa pieza. Total ≈ 30 pistas (10 de ACE-Step + 10 de Suno + 10 de librería), aleatorizadas y anonimizadas en la misma sesión. **Verificar los ToS de Suno** antes de usar su salida como línea base (2 h de legal en la semana de G2, dentro de las 32 h de §6.5d) |
| **Política de las pistas de evaluación** (S-11) | Las ≈ 30 pistas de G1 más las de los spikes viven en una **carpeta segregada de evaluación**, con **retención de 12 meses** y **manifiesto retroactivo simplificado solo para las propias**. Las de Suno y de librería **no se usan en ninguna producción** y no entran en la biblioteca de trabajo |
| **Quién juzga** | **3 evaluadores**, al menos 2 de ellos **supervisor musical o editor de una producción real**. **El desarrollador no puntúa** |
| **Escala** | 1–5 por dimensión, con rúbrica escrita |
| **Rúbrica (5 dimensiones)** | (1) adecuación al brief · (2) calidad de mezcla y ausencia de artefactos · (3) coherencia estructural · (4) inteligibilidad y prosodia de la letra cantada · (5) **«¿lo usarías tal cual en la pieza?»** (sí/no + nota) |
| **✅ Umbral de aprobado** | **7 de las 10 pistas de ACE-Step con ≥ 4/5 en la dimensión 5, por al menos 2 de 3 evaluadores**, y **ninguna dimensión con media < 3,0** |
| **✅ Umbrales objetivos** | **CLAP** audio-texto ≥ el de la línea base de librería en al menos **7 de 10** briefs · **WER** de la letra cantada (HeartTranscriptor) **≤ 15 % de media y ≤ 25 % en el peor caso** |
| **❌ Criterio de no-go explícito** | Si ACE-Step queda **por debajo de la librería de producción** en la dimensión 5 en **más de 5 de 10 briefs**, es **no-go**: significa que la plataforma no mejora lo que ya se tiene |
| **Coste** | 4 h de redacción del protocolo + 8 h de preparación de muestras + **~9 h de escucha** (3 evaluadores × 3 h, §6.5d) |
| **Registro** | Hoja de puntuaciones firmada, archivada junto a esta evaluación. Se repite en **G1-bis** (HeartMuLa) y al cambiar de versión de adapter (métrica de deriva, spec §12.3) |
| **Quién decide** | **Supervisor musical** (voto de calidad) + responsable de la iniciativa (voto de continuidad). **El desarrollador no vota.** Timebox de **10 días laborables**, con escalado a dirección (RACI de §10.1) |

Los umbrales numéricos son una **propuesta a ratificar por el supervisor musical** antes de la Fase 0 — pero deben quedar fijados **antes** de escuchar, no después. Y el supervisor musical tiene que **estar nombrado antes de aprobar la Fase 1** (I-20): sin él, este protocolo es un documento sin ejecutor.

### 10.3 Quick wins (hacer sí o sí)

| ID | Característica | Horas | Coste | Por qué |
|----|----------------|-------|-------|---------|
| C-02 | Instrumental sin voz | **12 h** | 600 € | Casi gratis sobre C-01, con demanda real en post-producción |
| C-05 | Asistente IA de letras | **24 h** | 1.200 € | Reestimada a la mitad en la rev. 2, +4 h en la rev. 3 por el endurecimiento del prompt y la validación de salida. Riesgo bajo, valor percibido altísimo, **mejora el resultado de C-01** |
| C-12 | Autenticación + 2FA | **28 h** | 1.400 € | Reestimada a la mitad. Requisito explícito, terreno pisado |
| **C-10a** | **Manifiesto v1 + ledger** | **38 h** | 1.900 € | **El quick win menos evidente y más importante.** 38 h que hacen que el audio de la Fase 1 nazca dentro de la cadena de custodia; no hacerlas cuesta 0 € y deja ese audio fuera **para siempre** (una cadena WORM no admite backfill) |
| C-06 | Stems separados | 40 h | 2.000 € | Demucs es maduro; en post marca la diferencia entre pista usable y descartada. **Con la ficha de licencia de sus pesos verificada primero** (I-13b) |
| — | **Matriz de capacidades verificadas** (dentro de C-11) | **12 h** | 600 € | 12 h en la semana 4 que dicen si C-07 y C-08 (**276 h, 16.560 €**) son viables. La mejor relación información/coste de todo el plan |

### 10.4 Características costosas (decisión explícita, no arrastre)

| ID | Característica | Horas | Coste | Recomendación |
|----|----------------|-------|-------|---------------|
| C-09 | Fine-tuning propio | **400 h** | 20.000 € + 626–1.095 €/ciclo | **Aplazar.** Se dobla respecto a la revisión 1, lo que **refuerza** la decisión. Bloqueada por I-03 y por falta de perfil ML (I-01). Es la vía a la procedencia limpia: merece iniciativa y presupuesto propios |
| C-13 | Cimientos de plataforma | **214 h** | 10.700 € | **Inevitable, y hay que aceptar su precio.** Es el suelo; recortarlo es pagarlo después con intereses. Las 24 h nuevas de la rev. 3 son cinco decisiones que se pagan ×5 si se toman tarde (linaje, 48 kHz, compartición, i18n, stop-loss) |
| C-04 | Clonación de voz | **175 h** | 8.750 € | **Aplazar.** Solo con caso de negocio concreto, consentimiento resuelto y DPIA. **RVC v2** o **YingMusic-SVC** (con licencia verificada, I-13b); **evitar so-vits-svc** |
| C-11 | Model registry | **147 h** | 7.350 € | **Fase 1, pero recortado** (D-16): fuera el router de capacidades y el formulario dinámico. Dentro: dos adapters reales, `provenance` obligatorio **contra un esquema ya firmado por legal**, matriz de capacidades verificadas y fichas de licencia |
| C-07 | Extender / regenerar secciones | **140 h** | 7.000 € | **Fase 3, y solo tras G3.** El editor de forma de onda es media característica. Candidata número uno a desviarse. Ya no arranca con una migración de linaje en producción (D-22) |
| C-10 | Trazabilidad de licencias | **105 h** = **38 (F1)** + **67 (F2)** | 5.250 € | **Partida (D-20).** C-10a en Fase 1 porque **el ledger no admite backfill**; C-10b en Fase 2 **con I-13 como condición** — las 20 h de watermarking asumen integrar una librería: **candidatos MIT identificados (2026-08-18), robustez en música por validar** (I-13/`T-57`) |
| C-08 | Cover / remezcla | 80 h | 4.000 € | **Fase 3, y solo con gate de titularidad obligatorio.** Sin él, contradice la motivación del proyecto. Reutiliza el componente de declaración construido en C-01 (D-21) |

### 10.5 Orden sugerido

1. **G2 — consulta a legal, con sus dos preguntas** (I-05 e I-05b). Semanas 0–1. Cero desarrollo. En paralelo: **pedir dos ofertas con indemnización** (§6.5b) y **verificar los ToS de Suno** (líneas base de G1 y estudio de UI de D-12).
2. **Gobernanza** — decisión construir-vs-comprar según la **matriz de resultados de G2**, y **nombramiento del supervisor musical y de los 3–5 usuarios piloto** (I-20). Sin esto no se arranca la Fase 0.
3. **Fase 0** — contenerización mínima de ACE-Step, spike de tiempos y VRAM (con y sin offloading), **medición de 2 inferencias concurrentes**, **matriz de capacidades verificadas**, decisión del objetivo de loudness por destino con el supervisor musical, **protocolo de G1 escrito antes de escuchar**.
4. **G1 — escucha ciega de ACE-Step** con el protocolo de §10.2, juzgada por el supervisor musical (el desarrollador no vota).
5. **C-13** Cimientos → sin esto no hay nada. **Con linaje en la primera migración** (D-22) e i18n desde el primer componente (D-25). **Al cerrarlo: checkpoint de stop-loss** (D-28).
6. **C-10a** Manifiesto v1 + ledger → **el esquema lo firma legal ANTES de implementar C-11**, porque la regla 4 del contrato obliga a los adapters a emitirlo. *(En la revisión 2 este paso era el número 9, dos fases más tarde.)*
7. **C-11** Model registry recortado → antes de C-01, para no acoplar la lógica a un modelo. **G1-bis al registrar HeartMuLa.**
8. **C-14** Infraestructura GPU → con **caché de imagen del contenedor**, keep-warm, **un** pod caliente con calendario, despacho round-robin y tope de gasto desde el primer día.
9. **C-01** Generación letra + estilo → primer valor de extremo a extremo, **con gate de derechos de la letra** (D-21) y manifiesto emitido desde la primera pista. **Estudio de la UI de Suno** aquí (D-12), con identidad visual de Daycry (D-12b).
10. **C-02** Instrumental (12 h) y **C-12** Autenticación (28 h) → se aprovecha el impulso.
11. *Puesta en uso con los usuarios piloto: primeras pistas reales con manifiesto y ledger.*
12. **C-10b** C2PA + WORM + PDF + watermarking → condicionada a I-13. **C-06** Stems (con licencia de Demucs verificada, I-13b) y **C-05** Asistente de letras → paralelizables, riesgo bajo.
13. ***Gate G3 de adopción*** tras **un mes de uso real**: ≥ 100 generaciones, ≥ 3 usuarios activos, ≥ 1 pista en producción entregada, encuesta ≥ 4/5. **Sin G3 no se aprueba la Fase 3.**
14. **C-03** → **C-07** → **C-08**, y solo si la matriz de capacidades del paso 3 lo avala.
15. *Punto de decisión de negocio, con I-03 e I-05 resueltas:* **C-04** y **C-09**.

### 10.6 Sobre «las 10 en fase 1»

Dicho sin rodeos: **las 10 características juntas no son una fase 1, son el producto completo.** Suno no nació con clonación de voz, stems, inpaint por secciones y fine-tuning propio.

Para 1–5 usuarios internos, intentar las 10 de una vez tiene un coste concreto y evitable: **retrasa en torno a seis meses el momento en que alguien usa la plataforma por primera vez**, y con ello el aprendizaje de qué características hacen falta de verdad. La Fase 1 propuesta pone una herramienta en manos del equipo en **~12 semanas por el 40 % del presupuesto** (y de esas 12, cinco son gates y esperas que no se pueden comprimir: 2 de G2, 1 de gobernanza y 2 de G1, según la tabla de §9.4). Lo que se aprenda ahí vale más que cualquier estimación de este documento — incluida esta, que ya ha tenido que corregirse **un 50 % al alza en dos revisiones** (1.084 → 1.566 → 1.622 h). Y esa es también la razón del **gate G3**: si tras un mes de uso real nadie ha usado la plataforma, el problema no se arregla añadiendo control creativo avanzado por 16.560 €.

### 10.7 La verdad incómoda, hasta el final

Esto no debería estar enterrado en un anexo, porque es la tensión central de la iniciativa:

1. **Las Fases 1+2 entregan una plataforma con la misma exposición de derechos que Suno** — mejor auditada, **no más limpia**. El manifiesto de C-10 dirá, literalmente, `training_data_declaration: no divulgada` para ACE-Step y para YuE, porque sus autores no publican el corpus.
2. **El self-hosting no cambia el estatus legal del output.** Apache 2.0 cubre pesos y código; no limpia la procedencia de los datos de entrenamiento. Suno y Udio fueron demandados en 2025 **por los datos**, no por el modo de despliegue.
3. **La única vía a procedencia realmente limpia es C-09** (fine-tuning sobre catálogo propio licenciado) — que es precisamente lo que esta evaluación pone en **no-go**, porque está bloqueada por I-03 y cuesta 400 h.
4. Por tanto: **si el criterio de legal es «garantizar derechos limpios al cliente», C-10 documenta el problema en lugar de resolverlo**, y ninguna de las Fases 1–3 cumple ese criterio. Lo cumplirían, cada una a su manera, la librería de producción actual (§6.5a) o un proveedor con indemnización contractual (§6.5b) — las dos opciones que la revisión 1 no comparaba.
5. **🆕 Y hay una segunda verdad incómoda, del otro lado del problema (I-05b).** Todo lo anterior habla de si Daycry puede **usar** el output sin infringir. La pregunta simétrica es si puede **proteger** lo que genera: en la UE, la música **sin intervención autoral humana puede carecer de protección**. Un cliente que exige **exclusividad** sobre la sintonía de su programa **no la puede obtener** sobre una obra no protegible — y eso es cierto **aunque legal apruebe la procedencia**, y cierto también **si se compra a un proveedor con indemnización**: nadie licencia en exclusiva lo que no está protegido. Por eso G2 lleva **dos** preguntas y no una: la primera decide si se puede construir; la segunda, qué se puede vender. Coste marginal de añadirla: **cero** — misma consulta, mismas 32 h.

Nada de esto invalida la iniciativa: **auditabilidad, control del modelo, coste marginal casi nulo y la opción futura de C-09 son valor real.** Pero hay que aprobarla sabiendo qué se compra y qué no. De ahí que **G2 vaya en la semana 0**: la pregunta a legal no es «¿te parece bien el manifiesto?», son **«¿aceptas audio cuya declaración de datos de entrenamiento dice *no divulgada*?»** y **«¿es protegible en exclusiva lo que salga de aquí?»**. Si la respuesta es no, se han gastado 32 h de legal en lugar de **39.360 €**.

---

## 11. Riesgos transversales

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| **R-01** | **Procedencia legal del output.** El self-hosting no cambia el estatus legal del audio: Apache 2.0 cubre pesos y código, no los datos de entrenamiento | **Alta** | **Crítico** | **Gate G2 en la semana 0, antes de gastar** (I-05); C-10 no negociable; `training_data_declaration` obligatoria; C-09 como única vía a procedencia limpia; **§10.7 aceptado por escrito antes de aprobar** |
| **R-02** | **RGPD y biometría de voz** (C-04): consentimiento, base jurídica, DPIA, retención, borrado del derivado | Alta | **Crítico** | Aplazar C-04 a Fase 4; consentimiento como bloqueo duro; **DPIA antes de una línea de código**; borrado del derivado (audio + dataset + pesos) con prueba automatizada |
| **R-03** | **La calidad open source no alcanza el nivel exigible.** Nadie lo ha validado para producción audiovisual de Daycry | Media | **Crítico** | **Gate G1 con protocolo numérico** (§10.2) tras 80,4 h; línea base ciega contra Suno **y contra la librería actual**; criterio de no-go explícito; **G1-bis para el segundo adapter** (D-27) |
| **R-04** | **Watermarking: candidatos identificados con licencia MIT; robustez en música por validar** (I-13). *(Rebajado el 2026-08-18: era «sin solución identificada»; hoy hay dos candidatos — SilentCipher y AudioSeal, ambos MIT — pendientes de prueba de robustez a transcode MP3/OGG/AAC sobre música, prevista en F10/`T-57`)* | Media | Alto | **Ejecutar la prueba de robustez de `T-57` antes de comprometer I-13 como cerrada.** Las 20 h de **C-10b** y 16 h de C-04 asumen *integración*, no construcción — sigue siendo un supuesto razonable con los dos candidatos ya identificados. Confirmar si hay política corporativa que lo exija (I-10). **Ya no bloquea la trazabilidad**: el manifiesto y el ledger viven en C-10a (Fase 1) y no dependen del watermarking |
| **R-05** | **Dependencias abandonadas.** so-vits-svc: fork realtime con mantenimiento limitado desde primavera de 2023 | Media | Medio | Preferir RVC v2 / YingMusic-SVC; fijar versiones; el registry aísla el resto del sistema |
| **R-06** | **Ningún modelo cubre bien todos los casos** (LM: mejor letra, lento; difusión: rápido, peor coherencia) | **Alta** | Medio | **Es la justificación de C-11** — pero **dos adapters bastan** para demostrarlo (D-16). Router de capacidades cuando haya un tercero. **Mitigación de adherencia a la letra sin código inexistente** (corrección de la rev. 3): HeartMuLa como segunda opinión + regeneración con otra semilla; el **tercer adapter (YuE) + router es partida condicional de Fase 2 (≈ 50 h)** activada por G1-bis, no una mitigación disponible hoy |
| **R-07** | **Perfil de equipo insuficiente.** No consta ML engineer; C-09, C-04 y C-03 lo requieren | Alta | Alto | Cerrar I-01; excluir C-09 del alcance inmediato; presupuestar contratación o subcontrata aparte |
| **R-08** | **Dataset inexistente para C-09** (I-03) | Media | **Crítico** para C-09 | Resolver I-03 **antes** de planificar C-09; sin respuesta, C-09 queda fuera |
| **R-09** | **Material con copyright subido en C-08** | Media | Alto | Gate de titularidad obligatorio y auditable; C-08 no antes de C-10 |
| **R-10** | **El arranque en frío no es tolerable** (S-01, I-09). Es **2–6 min, no 1–3**, y con pod por trabajo se paga **en cada variante** | Media | Medio | **Keep-warm 10 min + pod caliente en horario laboral** (§6.4): ≈ 83 €/mes, el 1,0 % del presupuesto anual de desarrollo. Cachear **la imagen del contenedor**, no solo los pesos (S-01b) |
| **R-11** | **Deriva de alcance hacia el SaaS de fase 2** (multi-tenancy, facturación, moderación, antiabuso) | Media | Alto | Fuera de alcance explícito (spec §5.3); el diseño deja la puerta abierta sin pagar el coste ahora |
| **R-12** | **El almacenamiento crece sin techo y adelanta a la GPU.** Con stems por defecto supera a la **GPU efímera de 48 €/mes** (opción B, factor 1,6×) en el **mes 10**; frente a la **opción G recomendada de 128 €/mes**, en torno al **mes 25** | **Alta** | Medio | Política de retención con números, ciclo a frío, **GC de huérfanos**, **FLAC en vez de WAV** (−40 %), stems a demanda (§6.6). Cerrar I-08. **Con la política recomendada el cruce queda fuera del horizonte de la Fase 1** |
| **R-13** | **Desviación de las estimaciones de baja confianza**: C-03, C-04, C-07, C-08, C-09 = **851 h, el 52 % del total** | **Alta** | Alto | Rango declarado por característica (§8); margen del 20 %; reestimar tras Fase 0 **con la matriz de capacidades en la mano**; puntos de decisión antes de Fases 3 y 4 (**G3**); **stop-loss intra-fase** en la Fase 1 (D-28); `/retro` para construir `CALIBRATION.md` |
| ~~R-14~~ | ~~Precio de tokens sin verificar~~ (I-06) | — | — | ✅ **CERRADO el 2026-07-27.** Precio verificado y escrito en `rates.json`. Coste real **1.151 €** con margen = 1,2 % del coste humano (§9.1) |
| **🆕 R-15** | **Riesgo de persona clave.** S-04 supone un full-stack senior que domine **Next.js + FastAPI + CUDA + DSP de audio + procedencia legal**. Ese perfil combinado es **raro**, y hoy **una sola persona sostendría el 100 % del proyecto** | **Alta** | **Alto** | Cerrar I-01 **antes de fijar fechas**; el calendario de §9.4 no tiene fechas absolutas por esto; documentación y runbooks como entregable, no como buena intención; considerar dos perfiles (aplicación + ML/audio) en lugar de uno |
| **🆕 R-16** | **OPEX de mantenimiento sin dueño ni partida**: ≈ 7.100 €/año sobre Fases 1+2 (I-16) | **Alta** | Medio | Nombrar propietario operativo antes del cierre de la Fase 2; presupuestar el 15 %/año explícitamente (§6.5c) |
| **🆕 R-17** | **Fuga de gasto en el proveedor de GPU.** Hay `max_gpu_seconds` por trabajo y **ningún límite agregado**: un bucle de reintentos en un proveedor medido funde el presupuesto un fin de semana | Media | Medio | **Tope de gasto mensual + kill switch en el proveedor** (D-17), alertas al 50 % y 80 % con destinatario nombrado, prueba de disparo en resiliencia |
| **🆕 R-18** | **Horas de no-desarrollo a cero.** Legal, DPO y sobre todo **supervisor musical** son 116 h que **no son horas de desarrollo y no están en las 1.638 h** — y **sin el supervisor musical G1 no se puede ejecutar** | **Alta** | Alto | Reservar las 116 h y su coste a tarifa interna (§6.5d, I-18) **antes** de arrancar la Fase 0. **El supervisor musical debe estar nombrado antes de aprobar la Fase 1** (I-20, condición del veredicto) |
| **🆕 R-19** | **Construir lo que se podía comprar.** La decisión de 98.280 € no tenía ninguna alternativa comparada | Media | **Alto** | §6.5 completa; **pedir dos ofertas con indemnización en la semana de G2**; decisión de dirección documentada antes de la Fase 1 |
| **🆕 R-20** | **Identidad visual al derivar la UX de Suno.** Replicar el **modelo de interacción** es práctica normal y de bajo riesgo; **copiar píxel a píxel la identidad visual de un producto propietario no lo es**, y el riesgo crece si la fase 2 llega a SaaS público | Baja | Medio | **D-12b**: se deriva la UX (flujos, estados, disposición, affordances), **no la marca**. Identidad visual propia de Daycry. Réplica visual literal declarada fuera de alcance (spec §5.3) |
| **🆕 R-21** | **Suite de conformidad *flaky* como single point of failure.** La igualdad bit a bit por semilla fija no se sostiene: la inferencia de difusión en GPU no es bit-reproducible entre versiones de driver/cuDNN/kernels | Media | Alto | **D-13**: conformidad por **tolerancia perceptual** (CLAP/WER dentro de umbral) + invariantes exactos. La semilla se registra para trazabilidad, no como garantía |
| **🆕 R-22** | **Seguridad del registry**: cargar checkpoints `pickle` de terceros es **RCE directa**, y el runner ejecuta **código de adapter de terceros con credenciales de storage** | Media | **Crítico** | **D-14** solo `safetensors` · **D-15** URLs firmadas de alcance por trabajo, token efímero, red de salida restringida, prefijo de bucket por trabajo · prueba negativa de aislamiento en CI |
| **🆕🔴 R-23** | **Audio de la Fase 1 fuera de la cadena de custodia para siempre.** Con toda la trazabilidad en la Fase 2, la Fase 1 generaba ≥ 2 semanas de audio sin ledger — y **una cadena WORM no admite backfill**: ese audio (el de las primeras pruebas reales, el que se enseña para justificar la Fase 2) nunca podría auditarse. En el proyecto cuya razón de ser es la trazabilidad | **Alta** (era certeza con el plan de la rev. 2) | **Crítico e irreversible** | **D-20: C-10a en la Fase 1** (38 h). Manifiesto y cadena de hashes desde la primera pista; `manifest_schema_version` con verificador multi-versión para que C-10b no invalide lo emitido antes |
| **🆕🔴 R-24** | **Letra con copyright como entrada.** C-08 exigía titularidad del audio subido y **C-01 no exigía nada sobre la letra**: una letra ajena producía una obra derivada **con manifiesto impecable sobre un input infractor** | **Alta** | **Alto** | **D-21**: declaración de autoría/derechos como **bloqueo duro** en C-01 (+8 h), `lyrics_declaration` en el manifiesto, fila propia en la tabla de errores; prompt de sistema endurecido y validación de salida en C-05 (+4 h). Filtro automático de similitud: **mejora futura, declarada no bloqueante** |
| **🆕 R-25** | **Migración de linaje en producción.** El esquema no modelaba variantes ni derivadas, así que C-07 (Fase 3) habría empezado migrando tablas con valor legal en producción, y los manifiestos de las derivadas no podrían referenciar a su padre | Media | Alto | **D-22**: `parent_id`, `root_id`, `derivation_kind`, `section_map` y `source_generation` **en la primera migración** (+8 h en C-13) |
| **🆕 R-26** | **Gate G2 con respuesta intermedia y sin decisión pre-acordada.** «Sí solo interno / no para cliente» es **la respuesta más probable**, y no estaba prevista: quien estuviera en la sala habría decidido «sigamos» con el presupuesto completo | **Alta** | **Alto** | **Matriz de resultados de G2** (§10.1) con las tres respuestas y su decisión pre-acordada, incluido el camino de **Fase 1 recortada con tope ≤ 20.000 €** y reevaluación del caso de negocio; **RACI con decisor nombrado y timebox de 10 días** |
| **🆕 R-27** | **Licencias del pipeline más allá del watermarker.** Los **pesos de Demucs** pueden llevar términos no comerciales aunque el código sea MIT; **RVC** tiene licencia confusa; HeartCodec/HeartTranscriptor sin verificar. La regla 5 del registry aplica al pipeline completo | **Alta** | Alto | **I-13b**: ficha de licencia verificada de **toda** herramienta **antes** de la fase que la integra (4–6 h por fase, dentro de las horas de la característica). Si un componente no es utilizable comercialmente, se sustituye **antes** de construir sobre él |
| **🆕 R-28** | **Adopción cero.** Se construyen Fases 1 y 2 (47.220 €) y nadie las usa; sin usuarios piloto comprometidos, la Fase 3 se aprueba por inercia | Media | **Alto** | **Gate G3 con cuatro números** (≥ 100 generaciones, ≥ 3 usuarios activos, ≥ 1 pista en producción real, encuesta ≥ 4/5) y **3–5 usuarios piloto nombrados con ≥ 2 h/semana antes de aprobar la Fase 1** (I-20) |
| **🆕 R-29** | **El output puede no ser protegible** (I-05b). En la UE, música sin intervención autoral humana puede carecer de protección: un cliente que exige **exclusividad** no la obtiene, **aunque legal apruebe la procedencia** | Media | **Alto** | **Segunda pregunta de G2**, coste marginal cero. Si la respuesta es «no protegible», se documenta como limitación contractual y se traslada a la conversación comercial **antes** de firmar exclusividades. Afecta igual a la opción de compra (§6.5b) |

---

## 12. Handoff a `planner`

> ✅ **Revisión 3 ratificada por el usuario el 2026-08-18: la petición vigente de Fase 0+1 es de 39.360 € (38.400 € de la revisión 3 + 960 € de la ampliación GPU local `T-85`/D-29, ratificados íntegramente el mismo día) y está aprobada.** Este handoff está listo para `planner` / `/dev-cycle` en cuanto G2 (legal) responda.

**Aprobado para planificar (pendiente de re-confirmación del usuario):**

- **G2 (legal) en las semanas 0–1** como primer elemento del plan, **con sus dos preguntas** (I-05 procedencia + I-05b protegibilidad), su **matriz de resultados pre-acordada** y su **RACI con decisor nombrado y timebox de 10 días laborables**. Posibilidad de **no-go total**. No es una tarea de desarrollo, pero es la tarea 1.
- **Gobernanza previa a la Fase 0**: decisión construir-vs-comprar y **nombramiento del supervisor musical y de 3–5 usuarios piloto** (I-20). **Son condiciones del veredicto, no tareas opcionales.**
- **Fase 0 + Fase 1** — C-13, **C-10a**, C-11, C-14 (incl. `T-85`/D-29), C-01, C-12, C-02 → **787,2 h / 39.360 €** con margen (banda 33.900–45.000 €). Incluye **G1-bis** al registrar HeartMuLa y el **checkpoint de stop-loss al cierre de C-13**.
- El plan debe incluir el **protocolo de G1 de §10.2 escrito y ratificado antes de la primera escucha**, con sus umbrales numéricos, y **evaluando solo ACE-Step**.
- **Orden no negociable dentro de la Fase 1**: C-13 → **C-10a (esquema firmado por legal)** → C-11 → C-14 → C-01. La regla 4 del contrato del registry exige un esquema de manifiesto ya firmado.

**Aprobado condicionalmente (planificar tras G1/G1-bis y con I-13 e I-13b respondidas):**

- **Fase 2** — **C-10b**, C-06, C-05 → 157,2 h / **7.860 €**. Las 20 h de watermarking de C-10b quedan **condicionadas** a I-13; la ficha de licencia de los **pesos de Demucs** es precondición de C-06 (I-13b).
- **Partida condicional no presupuestada**: tercer adapter (YuE 7B) + router de capacidades, **≈ 50 h**, solo si G1-bis muestra adherencia a la letra insuficiente. **🆕 MiniMax-Music3 (2026-08-18)** se apunta como candidato condicional adicional, sujeto a dictamen de legal sobre su Community License — no presupuestado, no sustituye a YuE.

**No planificar todavía:**

- **Fase 3** (C-07, C-08, C-03): **requiere superar el gate G3 de adopción** tras un mes de uso real, y que la **matriz de capacidades verificadas** del spike confirme `SECTION_INPAINT` y `AUDIO_TO_AUDIO`. Reestimar C-07 tras el spike.
- **Fase 4** (C-09, C-04): bloqueada por I-03, I-05 e I-01. Requiere decisión de negocio y presupuesto propio.

**Decisiones que el plan debe dar por tomadas:**

1. **Infraestructura: opción G** — **un** pod caliente en horario laboral (176 h/mes, `Europe/Madrid`, laborables, **calendario ajustable por el admin**) + keep-warm de 10 min fuera de horario + **un segundo pod efímero bajo demanda**, **≈ 128 €/mes**. Opción F (keep-warm solo, ≈ 45 €/mes) como postura de arranque; C (serverless) como plan B. Revisar si I-02 revela GPUs propias y si I-14 abarata una GPU de 24 GB.
2. **Cachear la imagen del contenedor**, no solo los pesos (S-01b). Es el término dominante del arranque en frío.
3. **Tope de gasto mensual agregado con kill switch** desde el primer despliegue (D-17), además de `max_gpu_seconds`.
4. Modelo inicial **ACE-Step 1.5**; **HeartMuLa** como segundo adapter (multilingüe + HeartTranscriptor para el alineado que C-07 necesitará), **sujeto a G1-bis**. **YuE 7B es candidato condicional de Fase 2, no alcance de Fase 1** (D-06). **MusicGen Stereo excluido** por licencia CC BY-NC.
5. **C-11 recortado (D-16)**: dos adapters reales y `provenance` obligatorio dentro; **router de capacidades y formulario dinámico fuera**. Formularios de parámetros **a mano**. **Matriz de capacidades verificadas en el spike**, no capacidades declaradas de confianza.
6. **Conformidad por tolerancia perceptual** (D-13), nunca por igualdad bit a bit con semilla fija.
7. **Solo `safetensors`** (D-14) y **aislamiento de credenciales del runner** (D-15) como invariantes de CI, con prueba negativa.
8. **FLAC como formato de almacén**, WAV solo como exportación a demanda **y a 48 kHz con soxr** (D-09, D-23), **objetivo de loudness por destino** (broadcast −23 / streaming −14 / stems sin normalizar) y política de retención con números desde el día uno.
9. **Límites de uso con los valores de la spec §12.1** (cuota 200 gen/usuario/mes, concurrencia 2, cola 20/60, **1 pod caliente + 1 efímero bajo demanda**, máximo 4), con **despacho FIFO + fairness round-robin por usuario** (D-26) y **UI de administración de cuotas**.
10. **La UX de Suno es la referencia funcional** (D-12) con **identidad visual de Daycry** (D-12b). El estudio de su interfaz se hace en C-01, **con los ToS verificados por legal en la semana de G2**.
11. Instrumentar `gpu_seconds`, coste por generación y horas de pod facturadas desde el primer despliegue.
12. **Trazabilidad desde la primera pista** (D-20): manifiesto v1 con `manifest_schema_version`, `lyrics_declaration` y `source_generation`, ledger append-only con cadena de hashes, verificador multi-versión con corpus en CI. **El esquema lo firma legal antes de implementar C-11.**
13. **Gate de derechos de la letra en C-01** (D-21) como bloqueo duro, con el mismo patrón que C-08. Filtro de similitud automático **fuera de alcance**.
14. **Linaje en la primera migración** (D-22) y **compartir = URL de la pista en la app** (D-24), nunca la URL firmada.
15. **UI en castellano con `next-intl` desde el día 1**; **WCAG AA no es objetivo de la Fase 1**, pero el reproductor y la forma de onda usan componentes accesibles por defecto y la deuda queda registrada (D-25).
16. **Custodia de la clave C2PA en KMS gestionado** con rotación anual y revocación documentada (C-10b, spec §12.4).
17. **Stop-loss al cierre de C-13** y **runbook de desmantelamiento de una página** escrito en la Fase 1 (D-28).

**Antes de arrancar, hace falta respuesta a:** **I-05** e **I-05b** (legal, bloqueantes absolutos), **I-20** (supervisor musical y usuarios piloto nombrados — condición del veredicto), **I-01** (equipo — sin ella el plan no puede llevar fechas), **I-11** (presupuesto máximo), **I-13** e **I-13b** (watermarking y licencias del pipeline, para poder comprometer C-10b y C-06), I-02 (GPUs propias), I-09 (latencia aceptable), I-16 (propietario operativo), I-18 (tarifa de las horas de no-desarrollo).

---

## 13. Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-07-27 | Creación de la evaluación sobre [`spec.md`](./spec.md). 14 características, 1.084 h base / 54.200 €; 1.300,8 h / 65.040 € con margen. Comparativa de 7 opciones de infraestructura; recomendada GPU efímera bajo demanda (≈ 48 €/mes a 1.000 gen/mes). Segmentación en 4 fases con dos gates. Estado `en-revision`. | evaluator |
| 2026-07-27 | **Revisión 2 tras auditoría independiente.** La aritmética de la revisión 1 se verificó íntegra y era correcta; lo que falló fue el criterio. **Correcciones de texto:** el resumen ejecutivo ya no atribuye 1.084 h a «las 10 características» (eran 10 del usuario + 4 transversales, con bases ahora separadas); el gate G1 compara horas en la misma base; la regla de cambio de infraestructura ya no mezcla horas de pod facturadas con segundos de GPU útiles (35 % = 252 h = **3.780 gen/mes**, no 6.000); se declara la base de la utilización (5,79 % útil / **9,3 % facturada**). **Reestimación:** C-13 120→190 h, C-11 72→130 h, C-14 80→120 h, C-01 48→70 h, C-10 72→105 h, C-07 96→140 h, C-04 120→175 h, C-09 200→400 h, C-12 48→**28** h, C-05 40→**20** h, C-06 sin cambio. Total **1.084 → 1.566 h base** (78.300 €); **1.879,2 h / 93.960 €** con margen. **Fase 1: 22.800 € → 33.000 €** (banda 27.960–38.040 €); la cifra anterior no la cubría ni en su suelo. Rango declarado por característica y desglose por subsistemas en cada ficha. **Criterio:** gate legal **G2 movido a la semana 0**, antes de cualquier gasto (§10.1) y verdad incómoda sobre la procedencia escrita entera (§10.7); nueva sección **§6.5 construir-vs-comprar con TCO** (librería actual, proveedor con indemnización, OPEX 15 %/año, 116 h de no-desarrollo); **§6.4 arranque en frío** corregido a 2–6 min / 5–12 min peor caso, factor de facturación **1,90×**, keep-warm y **opción G de pod caliente** (128 €/mes) añadidas; **§10.2 protocolo numérico del gate G1** (rúbrica, 10 briefs reales, líneas base ciegas contra Suno y librería, umbral 7/10 ≥ 4/5 por 2 de 3, WER ≤ 15 %, criterio de no-go); registry recortado (fuera router y formulario dinámico), regla 2 corregida, conformidad redefinida por tolerancia perceptual, invariantes de seguridad `safetensors` y aislamiento de credenciales; **§6.6 almacenamiento calculado** (62 €/mes al mes 12, adelanta a la GPU efímera en el mes 10, FLAC en vez de WAV); calendario sin fechas absolutas mientras I-01 esté abierta; **cifra de aprobación declarada** (33.000 €); sensibilidad de tokens (676–3.378 €) en lugar del hueco a 0. **Riesgos nuevos:** R-15 a R-22. **Información nueva del usuario:** hardware de ACE-Step (24 GB de confort → opción H de GPU de consumo) y UX de Suno como referencia funcional con identidad visual propia (R-20). | evaluator |
| 2026-07-27 | **Revisión 3 tras dos auditorías independientes (coherencia + adversarial de secuenciación).** El estado sigue `completado`, pero **las cifras cambian y requieren re-ratificación del usuario**: la petición pasa de **33.000 € a 38.400 €** y el catálogo completo de 1.566 h / 93.960 € a **1.622 h / 97.320 €** con margen (base 81.100 €). **Defectos de coherencia corregidos (aritmética y atribución):** subtotal «10 del usuario» de §8 con tokens **98,88/13,84 → 97,88/13,71 M** y rango **906–1.362 → 896–1.342 h** (se había colado C-12 en la suma de tokens; el TOTAL 120,00/16,80 era correcto) — ambas cifras ya recalculadas al alcance nuevo; banda de Fase 1 de la revisión 2 mal sumada (**466–634 h / 27.960–38.040 € → 464–638 h / 27.840–38.280 €**), recalculada al alcance nuevo; §2 dejaba de atribuir a la revisión 1 cifras que no eran suyas (**45–128 €/mes → 5–48 €/mes** y **93.960 € → 65.040 €**); §6.2 «ocho posturas» → **once** (A, A-bis, B, B-bis, C, C-bis, D, E, F, G, H); §2 «tres características de riesgo, 575 h / 28.750 € / 37 %» → **715 h / 35.750 € / 44 %** (575 h eran solo C-09 + C-04); coste de tokens recalculado **938 → 959 €** base y **1.126 → 1.151 €** con margen. **Secuenciación y alcance (el fondo de la revisión):** **C-10 partida en C-10a (38 h, Fase 1) y C-10b (67 h, Fase 2)** — total invariable — porque una **cadena WORM no admite backfill** y la Fase 1 generaba ≥ 2 semanas de audio sin ledger, además de que el criterio de aceptación de C-01 exigía un manifiesto inexistente y la regla 4 del registry obligaba a emitir un formato **sin firmar por legal** (R-23, D-20); **gobernanza de gates**: matriz de resultados de G2 con la respuesta intermedia «sí solo interno / no cliente» y su decisión pre-acordada (pivotar a compra o Fase 1 recortada con tope ≤ 20.000 €), **RACI con decisor nombrado y timebox de 10 días laborables**, y supervisor musical **nombrado como condición del veredicto** (R-26, I-20); **G1 evalúa solo ACE-Step** y **HeartMuLa pasa G1-bis** (el protocolo anterior era inejecutable), más **matriz de capacidades verificadas** (+12 h) que adelanta a la semana 4 la información que decidía 276 h de Fase 3; **gate de derechos de la letra en C-01** (+8 h) y endurecimiento de C-05 (+4 h) (R-24, D-21); **linaje en el esquema desde el día 1** (+8 h en C-13) para no migrar en producción en C-07 (R-25, D-22); **segunda pregunta de G2 sobre protegibilidad del output** (I-05b, R-29, coste cero). **Correcciones importantes:** reconciliación de **1 pod caliente + 1 efímero** contra el «2 pods» de la spec, medición de **2 inferencias concurrentes** en la L40S (+3 h) y despacho **FIFO + round-robin**; mitigación de C-01 reescrita (dependía del router y del adapter de YuE, **ambos fuera de alcance**) y YuE degradado a **partida condicional de ≈ 50 h**; **§9.4 reescrita con las esperas como filas** y banda declarada de **24–28 semanas** (la Fase 3 exige un mes de uso real tras la Fase 2); política de las ~40 pistas de spikes y G1 con **verificación de los ToS de Suno** (S-11); **I-13b** licencias de todo el pipeline (Demucs, RVC, HeartCodec) (R-27); **exportación a 48 kHz** con soxr y **loudness por destino** (+6 h); **compartición por URL de la app** (+4 h); **gate G3 de adopción** con cuatro números y **3–5 usuarios piloto nombrados** (R-28); **stop-loss intra-fase al cierre de C-13** con runbook de desmantelamiento (+2 h); restricción de los presets de voz de C-03 a etiquetas/audio sintético. **Decisiones baratas ya escritas:** i18n con `next-intl` (+4 h), WCAG AA fuera de objetivo con componentes accesibles por defecto, Fase 0 como sub-fila de la Fase 1 en §9.4, horario `Europe/Madrid` con calendario ajustable, custodia de la clave C2PA en KMS. **Efecto por fase:** Fase 1 **550 → 640 h (33.000 → 38.400 €)**, Fase 2 **165 → 131 h (9.900 → 7.860 €)**, Fases 3 y 4 sin cambio. **Riesgos nuevos:** R-23 a R-29. **Incógnitas nuevas:** I-05b, I-13b, I-19, I-20. Las **32 h de legal y 40 h de supervisor musical** siguen siendo las mismas y **no son horas de desarrollo**. | evaluator |
| 2026-08-18 | **Nota de coherencia, sin cambio de veredicto ni de aritmética.** El estado sigue siendo `completado` y las cifras de la revisión 3 no se tocan. Se añaden dos avisos en §10.1 porque la matriz de G2 nunca se actualizó tras la ampliación GPU local (`T-85`/D-29, +960 €, ratificada el 2026-08-18): (a) la **fila 1** de la matriz dice «38.400 €» y la cifra vigente de Fase 0+1 es **39.360 €**; (b) el **tope duro de ≤ 20.000 €** de la fila 2 se fijó contra la base de 38.400 €, así que si algún día se aplicara esa fila, dirección debe confirmar si el tope se mantiene o se reescala. Contexto: el **2026-08-18 se aplicó la fila 1 («sí total»)** y el gate G2 quedó levantado por decisión del propietario de la iniciativa — registrado en `gates/g2-matriz-resultados.md` §10, no en este documento. | dev-cycle (orquestador) |
| 2026-08-18 | **Hallazgos HF 2026-08-18 registrados como candidatos** (SilentCipher/AudioSeal para I-13, Demucs CC-BY-NC confirmado en I-13b, MiniMax-Music3 candidato condicional con pregunta añadida a G2, vía LoRA en anexo F4, XL en spikes). Registro informativo verificado contra fuentes primarias, **sin cambio de horas, coste, fases ni estados**: siguen vigentes 1.622 h base / 97.320 € y la Fase 0+1 de 39.360 €. Riesgo **R-04 rebajado** de «sin solución identificada» a «candidatos con licencia MIT, robustez en música por validar»; I-13 e I-13b actualizadas en §4; notas en las fichas de C-04, C-06, C-09, C-10b (§7) y en la partida condicional del tercer adapter (§2, §11). | dev-cycle (orquestador) |
| 2026-09-01 | **Corrección de coherencia tras revisión integral (`revision-2026-09-01.md`).** La frase de la entrada anterior «siguen vigentes 1.622 h base / 97.320 € y la Fase 0+1 de 39.360 €» era **incoherente**: no se pueden mantener a la vez los agregados sin `T-85` y una Fase 0+1 que lo incluye. Desde hoy **todos los agregados vigentes incorporan `T-85`/D-29 (+16 h)**: C-14 **123 → 139 h** (6.950 €, fila nueva «Modo GPU local: 16 h» en su desglose), transversales **512 → 528 h / 26.400 €**, catálogo completo **1.622 → 1.638 h base / 81.900 €** → **1.965,6 h / 98.280 €** con margen (§1, §2, §6, §8, §9, §10, §12); Fase 1 **640 → 656 h** → **787,2 h / 39.360 €**, banda **565/656/750 h → 33.900/39.360/45.000 €**; Fases 0+1+2 **46.260 → 47.220 €** (G3, §10.1) y OPEX derivado ≈ 7.100/14.700 €/año. **Los agregados de tokens y de horas IA no incluyen el delta de `T-85`** (+4 h IA ≈ +1,00 M in / +0,14 M out, efecto ≪ 1 %): nota visible en §8 y §9.1. Otras correcciones: coste de supervisión **7.350 → 7.356 €** (490,4 × 1,2 × 0,25 × 50, redondeo); C-09 unificada a **≈ 24 %** del presupuesto (400/1.638) en §7 y §10.1; ficha C-04 alineada con la I-13 actualizada (candidatos MIT, robustez por validar — ya no «sin solución identificada»); duración de G2 unificada a **2 semanas** (§2); §10.6 corregida a **~12 semanas / 40 % / 5 semanas de gates** para cuadrar con §9.4; banda de calendario **24–28 → 25–28 semanas** (las filas de §9.4 suman 25); R-10 unificado a **1,0 %** (996/98.280); §5 declara la excepción de método de C-03/C-08 (rango sesgado al alza); nota al pie en §9.4 (las semanas son juicio experto, ~2 FTE en Fase 1); frontmatter con `actualizado: 2026-09-01` y bloque `generacion:`. | revision-2026-09-01 |
