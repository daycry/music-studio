---
documento: gobernanza
titulo: "Gobernanza en modo solo — acta de adaptación (evaluador único, usuario piloto = propietario, construir-vs-comprar) + gate de comercialización GC-01"
iniciativa: "Plataforma propia de generación musical por IA (proyecto personal)"
slug: plataforma-musical-ia
tarea: T-02
estado: cerrado-modo-solo
fecha: 2026-08-18
actualizado: 2026-09-01
supervisor-musical: "Daycry (propietario) — evaluador único en modo solo (riesgo aceptado, ver §2.1)"
usuarios-piloto: "el propietario (modo solo, ver §3)"
incognita: I-20
evaluacion: ../evaluation.md
plan: ../improvement-plan.md
tareas: ../tasks.md
gate-g2: ./g2-matriz-resultados.md
gate-comercializacion: "GC-01 (§8 de este documento)"
---

# Gobernanza — modo solo (proyecto personal)

> **Estado del documento: `cerrado-modo-solo` (2026-09-01).** El 2026-09-01 el propietario real del proyecto (alias **Daycry**) declaró que esto es un **proyecto personal de una sola persona**, con **posible comercialización futura**. Toda la gobernanza corporativa que esta acta pedía (3 evaluadores, 3–5 usuarios piloto con responsable que autorice horas, ofertas con indemnización, DPO, 116 h de no-desarrollo a tarifa interna) estaba sobredimensionada respecto a esa realidad. **Los nombramientos quedan CERRADOS en modo solo: todos los papeles los asume el propietario.** Los gates y sus umbrales numéricos **se conservan íntegros como autodisciplina** — ningún número se degrada. Lo corporativo-legal **no se borra: se reagrupa** en el **gate de comercialización GC-01** (§8), que solo aplica si el proyecto pasa a ser comercial o a usarse con terceros.
>
> Motivo del cambio: **decisión del propietario: proyecto personal en solitario** (2026-09-01). Versión corporativa anterior: historial git y changelog (§9).

---

## 1. Por qué existe este documento (y qué cambia en modo solo)

Nombrar evaluadores, usuarios piloto y decidir construir-vs-comprar era condición del veredicto de la evaluación (`evaluation.md` §4, incógnita **I-20**; §10.1). En modo solo la condición **se satisface de otra forma**: no desaparecen los papeles, se concentran en la única persona que existe.

| Papel corporativo | Resolución en modo solo |
|---|---|
| **Supervisor musical / 3 evaluadores de G1** | **El propietario es el único evaluador** (§2). El protocolo numérico de G1 se conserva íntegro. Riesgo aceptado: se pierde la independencia desarrollador/juez. |
| **3–5 usuarios piloto** | **El propietario es el usuario piloto** (§3). G3 se reinterpreta en modo solo sin degradar su exigencia de uso real. |
| **Decisión construir-vs-comprar** | **Documentada** (§4): construir, por aprendizaje, control y self-hosting. |
| **Propietario operativo (I-16)** | **El propietario** (§6). El OPEX es su tiempo, decidido por él. |

**Relación con el gate G2:** `T-01` quedó cerrada el 2026-08-18 (fila 1, «sí total»). Su deuda documental legal (informe escrito de I-05, respuesta a I-05b, ToS de Suno) **se traslada al gate de comercialización GC-01** (§8): en ámbito estrictamente personal no bloquea; antes de cualquier uso comercial o con terceros, sí.

---

## 2. Evaluador de G1 / G1-bis: el propietario (evaluador único)

**Rol:** voz de calidad de la iniciativa en los gates G1 y G1-bis (`evaluation.md` §10.1 y §10.2). En modo solo, **el propietario puntúa y decide**.

### 2.1 Registro del rol y riesgo aceptado

| Campo | Valor |
|---|---|
| Evaluador único | **Daycry (propietario del proyecto)** |
| Fecha de asunción del rol en modo solo | **2026-09-01** (esta acta; sustituye al nombramiento corporativo parcial del 2026-08-18) |
| Disponibilidad | La agenda es del propietario; el calendario del plan pasa a ser **orientativo** (ver I-01 en `spec.md` §10) |

> ### ⚠️ Riesgo aceptado por escrito (2026-09-01)
>
> **Al puntuar G1 la misma persona que desarrolla, se pierde la independencia desarrollador/juez** que `evaluation.md` §10.1 establecía a propósito («el desarrollador no puntúa y no vota»). En modo solo esa separación es imposible. Mitigaciones que se conservan para que el gate siga teniendo dientes:
>
> 1. **El protocolo numérico se conserva íntegro** (§2.2): los umbrales se fijan por escrito **antes** de escuchar, la escucha es a ciegas (pistas anonimizadas) y la hoja de puntuaciones se archiva. Un número escrito antes de escuchar es más difícil de autoengañar que una impresión.
> 2. **Criterio de no-go intacto**: si el modelo propio pierde contra la librería en la dimensión 5 en más de 5 de 10 briefs, es no-go — también en modo solo.
> 3. **Opción recomendada (no obligatoria): invitar 1–2 oyentes externos informales** (amistades con oído, otros músicos) a la escucha ciega si es posible. No son evaluadores formales ni bloquean el gate, pero reducen el sesgo del auto-juicio. Si participan, sus hojas se archivan junto a la del propietario.
>
> La versión corporativa (3 evaluadores, ≥ 2 con perfil de supervisor musical o editor de producción real, quórum «2 de 3») **se conserva en GC-01** (§8g) para el escenario comercial.

### 2.2 Protocolo numérico de G1 — SE CONSERVA ÍNTEGRO (lo puntúa el propietario)

El protocolo de `evaluation.md` §10.2 no se degrada; solo cambia quién puntúa:

1. **10 briefs reales** (en modo solo: briefs propios realistas — vídeos, maquetas, encargos ficticios pero concretos), con **escucha a ciegas contra Suno y la pista de librería donde sea posible** (las líneas base se anonimizan en la misma sesión).
2. **Rúbrica de 5 dimensiones, escala 1–5**: adecuación al brief · calidad de mezcla y ausencia de artefactos · coherencia estructural · inteligibilidad y prosodia de la letra cantada · «¿lo usarías tal cual en la pieza?».
3. **Umbrales numéricos, fijados ANTES de escuchar:**
   - **Umbral de aprobado:** 7 de las 10 pistas del modelo propio con **≥ 4/5 en la dimensión 5**, y **ninguna dimensión con media < 3,0**.
   - **Umbrales objetivos:** similitud **CLAP** audio-texto ≥ la de la línea base de librería en al menos **7 de 10** briefs · **WER** de la letra cantada **≤ 15 % de media** y **≤ 25 % en el peor caso**.
   - **Criterio de no-go explícito:** si el modelo propio queda **por debajo de la librería** en la dimensión 5 en **más de 5 de 10** briefs, es **no-go**.
4. **Hoja de puntuaciones archivada** junto a la evaluación; se repite en **G1-bis** (cada adapter nuevo) y en cada cambio de versión de adapter (escuchas de regresión).
5. **Loudness por destino (EBU R128):** lo decide el propietario en la Fase 0, y queda por escrito antes de G1.

> **Nota sobre la línea base de Suno:** usar la salida de Suno como línea base ciega en ámbito personal es responsabilidad del propietario; la **verificación formal de los ToS de Suno se traslada a GC-01 (§8c)** — obligatoria antes de cualquier uso comercial de resultados comparados contra esa línea base.

---

## 3. Usuario piloto: el propietario — G3 reinterpretado en modo solo

**El propietario es el usuario piloto.** El gate **G3 (adopción)** conserva su función — impedir que la Fase 3 (16.560 € equivalentes de esfuerzo) se apruebe por inercia — pero sus cuatro números corporativos se reinterpretan así:

| # | Número de G3 en modo solo | Umbral | Estado |
|---|---|---|---|
| 1 | Generaciones propias acumuladas | **≥ 100** | `pendiente de medir` (tras 1 mes de uso real) |
| 2 | ~~Usuarios activos ≥ 3~~ → **uso propio sostenido** (ha generado en las últimas 2 semanas) | **sí/no** | `pendiente de medir` |
| 3 | Pistas usadas en **algo real** (un vídeo publicado, una maqueta terminada, una pieza entregada) | **≥ 1** | `pendiente de medir` |
| 4 | ~~Encuesta a pilotos~~ → **autoevaluación honesta** del propietario, por escrito | **≥ 4/5** | `pendiente de medir` |

**Sin encuesta de terceros.** La autoevaluación se escribe **antes** de decidir sobre la Fase 3, no después. Si los números no salen, la Fase 3 no se aprueba — también en modo solo. La versión corporativa (3–5 pilotos con ≥ 2 h/semana y encuesta) **se conserva en GC-01** (§8g).

---

## 4. Decisión construir-vs-comprar — DOCUMENTADA

**Tercer criterio de aceptación de `T-02` — cerrado el 2026-09-01:**

| Campo | Valor |
|---|---|
| Decisión tomada | **Construir** |
| Quién decide | **Daycry, propietario del proyecto** |
| Fecha | **2026-09-01** |
| Motivación | **Proyecto personal: objetivo de aprendizaje, control total y self-hosting.** La alternativa comprar (suscripción a Suno/Udio u otro proveedor) se descartó por esos motivos: lo que se compra construyendo es precisamente lo que una suscripción no da — entender el pipeline, controlar la procedencia y poder auto-alojarlo. |
| Ofertas con indemnización | **Sin ofertas con indemnización en ámbito personal** — carecen de sentido sin cliente al que indemnizar. **Se reevaluará en el gate de comercialización GC-01** (§8), donde la comparativa TCO de `evaluation.md` §6.5b/§6.5e vuelve a ser pertinente. |
| Relación con G2 | Fila 1 de la matriz («sí total»), aplicada el 2026-08-18 — ver [`g2-matriz-resultados.md`](./g2-matriz-resultados.md) §10 |

---

## 5. RACI de los gates en modo solo

**Todos los papeles = el propietario.** Lo que se conserva no son los nombres sino **los umbrales y el acto de decidir por escrito**: ningún gate se cierra «por sensación», y **los números no se degradan**.

| Gate | Quién convoca / decide | Umbral (intacto) | Registro exigido |
|---|---|---|---|
| **G2 — Legal** | Propietario | ✅ Levantado el 2026-08-18 (fila 1, «sí total»). Deuda documental → **GC-01** (§8) | `g2-matriz-resultados.md` §10 |
| **G1 / G1-bis — Calidad** | Propietario (evaluador único, §2) | **7/10 ≥ 4/5 · ninguna dimensión < 3,0 · CLAP ≥ librería en 7/10 · WER ≤ 15 % medio / 25 % peor caso · no-go si pierde contra librería en > 5/10** | Hoja de puntuaciones archivada, umbrales fijados antes de escuchar |
| **G3 — Adopción** | Propietario | **≥ 100 generaciones propias · uso sostenido · ≥ 1 pista en algo real · autoevaluación ≥ 4/5** (§3) | Autoevaluación por escrito antes de decidir Fase 3 |
| **Stop-loss** (cierre de C-13) | Propietario — **obligado a ejecutar el checkpoint** | **> 60 % del presupuesto de la Fase 1 consumido con < 40 % del alcance entregado → parada y decisión por escrito** | Runbook de desmantelamiento de una página ya escrito (D-28) |

**Criterio del stop-loss (intacto, como autodisciplina):** > 60 % del presupuesto de la Fase 1 consumido con < 40 % del alcance entregado → **parada y decisión escrita** antes de seguir gastando, con el runbook de desmantelamiento (D-28): se conserva ledger, manifiestos y pistas usadas; se da de baja el proveedor GPU si lo hay; el resto se destruye con constancia. Que quien para y quien es parado sean la misma persona no elimina el valor del umbral: **el número obliga a mirar**.

---

## 6. Reservas — actualización a modo personal

### 6.1 Propietario operativo (I-16) y OPEX

| Campo | Valor |
|---|---|
| **Propietario operativo tras la entrega** | **El propietario (Daycry)** — cerrado 2026-09-01 |
| OPEX (≈ 6.900 €/año estimado en la versión corporativa) | **Informativo en modo personal**: es tiempo del propietario, no una partida. La cifra se conserva como referencia para GC-01 |

### 6.2 Tarifa interna y 116 h de no-desarrollo — N/A en modo personal

Las **116 h de no-desarrollo** (legal 32 h, supervisor musical 40 h, DPO 20 h, propietario operativo 24 h) y la **tarifa interna** (I-18) eran construcciones corporativas: **N/A en modo personal** — todo ese trabajo es tiempo del propietario, sin tarifa que imputar. El **DPO** solo volvería a existir en el escenario de GC-01 §8e (clonación de voz, Fase 4, hoy en no-go). Las horas de legal renacen, como consulta real de pago, en GC-01 §8a/§8b.

**I-18 queda cerrada** (ver `spec.md` §10): no hay tarifa interna que averiguar.

---

## 7. Cierre de `T-02` (2026-09-01)

**Criterios de aceptación de `T-02`, adaptados al modo solo y verificables en este documento:**

- [x] **Rol de evaluador único asumido por el propietario** y registrado con su riesgo aceptado y el protocolo numérico íntegro → §2 (2026-09-01).
- [x] **Usuario piloto = propietario**, con G3 reinterpretado en modo solo sin degradar su función → §3 (2026-09-01).
- [x] **Decisión construir-vs-comprar documentada** → §4 (2026-09-01).

| Campo | Valor |
|---|---|
| Quién firma el acta | **Daycry, propietario del proyecto** |
| Fecha | **2026-09-01** |
| Riesgos aceptados por escrito | (1) pérdida de la independencia desarrollador/juez en G1/G1-bis (§2.1); (2) G3 sin terceros: autoevaluación en lugar de encuesta (§3); (3) sin ofertas comparadas: la comparativa comprar se difiere a GC-01 (§4) |

> **Estado de `T-02` en el ledger: `completado` (2026-09-01).** La versión corporativa de los criterios (3 evaluadores, 3–5 pilotos con horas autorizadas, ofertas con indemnización) **no se borra: se traslada a GC-01** (§8g).

> **Secuencia:** con `T-01` cerrado (fila 1, «sí total») y `T-02` cerrado en modo solo, **el bloqueo de gobernanza de la Fase 0 queda levantado**. El bloqueo restante para arrancar F2 es **de entorno**: máquina GPU local confirmada, NVIDIA Container Toolkit verificado y pesos `safetensors` de ACE-Step (ver `pre-dev-checklist.md` §A, ítems 5–7).

---

## 8. Gate de comercialización (GC-01) 🆕

> **Condición dura: NINGÚN uso comercial ni con terceros** (vender pistas, usarlas en encargos de cliente, ofrecer la plataforma a otras personas, prometer exclusividad a nadie) **antes de cumplir TODO lo siguiente.** En ámbito estrictamente personal, nada de esta lista bloquea. Este gate agrupa, sin pérdida, todo lo corporativo-legal que el modo solo desactiva.

| # | Condición | Origen (qué reagrupa) |
|---|---|---|
| **a** | **Consulta legal real sobre la procedencia del audio** (I-05): la respuesta de G2 se dio de forma informal por el propietario; antes de comercializar hace falta una consulta a un profesional y su **informe escrito archivado** | Deuda documental de `T-01` (`g2-matriz-resultados.md` §10) |
| **b** | **Respuesta a I-05b**: ¿es protegible y licenciable en exclusiva el output generado sin autoría humana? Sin ella, no prometer exclusividad a ningún cliente | `spec.md` I-05b · `evaluation.md` R-29 |
| **c** | **ToS de Suno verificados**, si su salida se usó como línea base de G1 | `spec.md` S-11 · deuda de `T-01` |
| **d** | **Re-verificación de licencias de TODO el pipeline para uso comercial** (I-13/I-13b): watermarker, separación de stems (Demucs confirmado CC-BY-NC — no comercial), codecs, modelos. Lo que vale para uso personal puede no valer para vender | `spec.md` I-13/I-13b · regla 5 del registry |
| **e** | **RGPD/DPIA con DPO** si algún día se tocara clonación de voz (C-04, Fase 4 — hoy en **no-go**): voz identificable = dato biométrico | `evaluation.md` §6.5d · Fase 4 |
| **f** | **Firma del «Anexo A»** (la verdad incómoda de la procedencia, `g2-matriz-resultados.md` §8.3) como **aceptación consciente propia** del propietario | Mitigación de R-01 |
| **g** | **Revisitar la gobernanza con personas reales**: evaluadores independientes para G1 (protocolo corporativo de 3 evaluadores conservado en el historial de este documento), usuarios piloto reales para G3, ofertas con indemnización para la comparativa comprar (§4), y propietario operativo si deja de ser el propio Daycry | §2.1, §3, §4 y §6 de esta acta |

**Quién ejecuta GC-01:** el propietario, cuando (y solo si) decida comercializar. **Hasta entonces, este gate no bloquea nada** — pero tampoco se olvida: está aquí, con sus siete condiciones numeradas, para que la decisión de comercializar no se tome por inercia igual que ningún otro gate de este proyecto.

---

## 9. Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-08-18 | Creación del acta corporativa (plantilla de nombramientos): supervisor musical, 3 evaluadores de G1, 3–5 usuarios piloto, construir-vs-comprar, RACI, reservas. Daycry asume supervisor musical (1 de 3 evaluadores); resto `⚠️ pendiente`. | implementer / orquestador |
| 2026-09-01 | **Reescritura a modo solo — decisión del propietario: proyecto personal en solitario.** El propietario (Daycry) es evaluador único de G1/G1-bis (protocolo numérico íntegro: 10 briefs, escucha a ciegas, 7/10 ≥ 4/5, WER ≤ 15 %; riesgo de pérdida de independencia desarrollador/juez aceptado por escrito, con opción recomendada de 1–2 oyentes externos informales), usuario piloto único (G3 reinterpretado: ≥ 100 generaciones propias, ≥ 1 pista en algo real, autoevaluación ≥ 4/5), decisión construir-vs-comprar documentada (construir: aprendizaje, control, self-hosting; sin ofertas con indemnización en ámbito personal). RACI: todos los papeles = propietario; stop-loss y umbrales intactos como autodisciplina. 116 h de no-desarrollo, tarifa interna y DPO: N/A en modo personal. **Nuevo §8: gate de comercialización GC-01** con las 7 condiciones (a–g) que reagrupan lo corporativo-legal para el escenario comercial futuro. `T-02` pasa a `completado`. Estado del documento: `cerrado-modo-solo`. | propietario (Daycry) |
