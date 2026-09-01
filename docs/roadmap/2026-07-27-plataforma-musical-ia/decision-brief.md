# Plataforma propia de generación musical por IA

**Brief de decisión** · 27 de julio de 2026 · Daycry (7590335+daycry@users.noreply.github.com)  
Iniciativa `plataforma-musical-ia` · Spec **aprobada** · Evaluación **completada** · Revisión 3

---

## Lo que se pide decidir

> **Aprobar 39.360 € para la Fase 0 + Fase 1** *(38.400 € de Fase 0+1 + 960 € de la ampliación GPU local `T-85`/D-29, ratificados íntegramente el 2026-08-18)*, banda realista de la Fase 1 **33.900–45.000 €**, **condicionado a que legal responda primero**.

No se pide aprobar el catálogo completo (98.280 €). Las Fases 3 y 4 se deciden más adelante, con información que hoy no existe.

*Nota: la cifra ratificada originalmente fueron 33.000 €. La revisión 3 — dos auditorías independientes de coherencia y secuenciación — adelantó la trazabilidad mínima a la Fase 1 (era una contradicción tenerla después del audio que debe cubrir) y añadió alcance de bajo coste que evita migraciones futuras. El incremento de 5.400 € compra que **la primera pista generada ya nazca dentro del ledger de procedencia**. La cifra de 38.400 € fue **ratificada el 18 de agosto de 2026**, junto con los **+960 € de la ampliación GPU local (`T-85`/D-29)** decididos y ratificados el mismo día: la cifra vigente de aprobación es **39.360 €**.*

---

## Qué es

Una plataforma web interna donde un usuario escribe **una letra**, **un prompt de estilo** y **opciones de voz**, y obtiene una **canción completa descargable** (MP3, FLAC; WAV y 48 kHz como exportación), con un registro de trazabilidad por pista **desde la primera generación**. Funcionalmente equivalente a Suno, pero con los modelos corriendo en infraestructura de Daycry.

Motor: modelos open source **self-hosted** con licencia Apache 2.0 (ACE-Step 1.5 como referencia, HeartMuLa como segundo adapter), sobre una arquitectura que trata el modelo como un plugin sustituible. Stack Next.js + Python/FastAPI. Fase 1: uso interno, 1–5 usuarios, 100–1.000 generaciones/mes.

## Por qué se plantea

Daycry necesita música al brief exacto de cada pieza, con procedencia de derechos controlada. Hoy eso se cubre con librerías de producción (limitan la creatividad) o con servicios de terceros como Suno y Udio, **a los que las grandes discográficas demandaron en 2025** por infracción de copyright en sus datos de entrenamiento. Incorporar audio de procedencia dudosa en una producción comercial es un riesgo que no se puede trasladar al cliente.

---

## La objeción que hay que resolver antes de gastar

**Construir esto con los modelos open source disponibles hoy no produce audio con procedencia más limpia que Suno. Produce audio mejor auditado.**

El manifiesto de trazabilidad dirá `training_data_declaration: no divulgada` para ACE-Step, porque sus autores no publican el corpus de entrenamiento. La licencia Apache 2.0 cubre los pesos y el código; **no limpia el origen de los datos**. Self-hostear no cambia el estatus legal del output.

La única vía a procedencia realmente limpia es el fine-tuning sobre catálogo propio licenciado — que es precisamente lo que esta evaluación recomienda **no** hacer todavía, por falta de catálogo licenciado disponible y de perfil de ML en el equipo.

**Consecuencia práctica:** si el criterio de legal es «poder garantizar derechos limpios al cliente», las Fases 1–3 no lo cumplen, y la librería de producción actual lo cumple mejor. Eso hay que saberlo **antes** de gastar, no después.

---

## Los gates

| Gate | Cuándo | Coste | Qué decide |
|---|---|---|---|
| **G2 — Legal** | **Semana 0, antes de cualquier gasto de desarrollo** | **0 € de desarrollo** · 32 h de legal | **Dos preguntas por escrito**: (1) ¿acepta legal audio de modelos con procedencia «no divulgada», con el registro de trazabilidad, para uso interno y para producciones de cliente? (2) ¿Es protegible/licenciable en exclusiva el output generado sin autoría humana? Con **matriz de resultados pre-acordada** — incluida la respuesta más probable, «sí interno / no cliente» |
| **G1 — Calidad** | Fin de la Fase 0 (~2 semanas) | **4.020 €** + ~9 h de escucha | Escucha ciega de 10 briefs reales, **solo ACE-Step**, contra la salida de Suno y contra la librería actual. Umbral: 7 de 10 pistas &ge; 4/5 por 2 de 3 evaluadores; WER de la letra &le; 15 % |
| **G1-bis — Segundo adapter** | Dentro de la Fase 1 | incluido | HeartMuLa pasa el mismo protocolo al registrarse; si ambos modelos fallan en adherencia a la letra, se activa la partida condicional (YuE + router, ~50 h) |
| **G3 — Adopción** | Entre Fase 2 y Fase 3 | 0 € | &ge;100 generaciones, &ge;3 usuarios activos, &ge;1 pista usada en una producción real, encuesta &ge;4/5. **Sin estos números, la Fase 3 no se aprueba «porque toca»** |
| **Stop-loss** | Al cierre de C-13 (~33 % de la Fase 1) | 0 € | Si se ha consumido >60 % del presupuesto con <40 % del alcance: parada y decisión, con runbook de desmantelamiento ya escrito |

**G2 va primero porque es el único gate capaz de anular el 100 % del presupuesto, y no es una entrega de software: es una consulta de dos semanas (consulta + timebox de decisión)** con decisor nombrado y timebox de 10 días laborables. **G1 cuesta el 4,1 % del esfuerzo total y decide sobre el otro 95,9 %.** Lo juzga un supervisor musical de una producción real, no el desarrollador.

**Dos condiciones del veredicto antes de aprobar la Fase 1:** supervisor musical nombrado (sin él G1 no existe) y 3–5 usuarios piloto con nombre y &ge;2 h/semana comprometidas (sin ellos G3 no puede medirse).

---

## Fases y coste

| Fase | Contenido | Coste (c/ margen) | Veredicto |
|---|---|---|---|
| **0** | Spikes de viabilidad (tiempos, VRAM, concurrencia, **matriz de capacidades** que decide la Fase 3) + protocolo y escucha de G1 | 4.020 € *(incluido en Fase 1)* | **Go**, tras G2 |
| **1** | Cimientos (con linaje de versiones y export 48 kHz), **trazabilidad mínima C-10a** (manifiesto firmado por legal + ledger desde la primera pista), registry de modelos, infraestructura GPU, generación letra+estilo (con declaración de derechos de la letra), instrumental, auth con 2FA — incl. el modo GPU local `T-85`/D-29 (+960 €) | **39.360 €** | **GO** |
| **2** | Trazabilidad completa C-10b (C2PA, WORM, certificado PDF, watermarking), stems, asistente de letras | **7.860 €** | **Go** condicionado a licencias (watermarker, Demucs) |
| **3** | Selector de voz, extender/regenerar secciones, cover de pista existente | 16.560 € | Solo tras **G3** |
| **4** | Clonación de voz propia + fine-tuning de modelos propios | 34.500 € | **NO-GO** |
| | **Total catálogo completo** | **98.280 €** (1.965,6 h) | |

**Por qué la Fase 4 va a no-go:** el fine-tuning propio (400 h) está bloqueado por la ausencia de catálogo licenciado y de perfil de ML en el equipo; la clonación de voz (175 h) por RGPD — es dato biométrico, exige consentimiento explícito, DPIA y borrado del modelo derivado. Están presupuestadas con su coste real, no descartadas por decreto.

**Calendario realista: 25–28 semanas** hasta cerrar la Fase 3 (15 de desarrollo + gates y esperas, incluido el mes de uso real que exige G3). El calendario no es compromiso hasta que se responda quién ejecuta.

---

## Antes de aprobar: las alternativas

| Alternativa | Coste | Qué compra | Qué no compra |
|---|---|---|---|
| **No hacer nada** — seguir con la librería de producción | ~300 €/mes. La Fase 1 equivale a **≈ 10,9 años** de suscripción (39.360 €); el catálogo completo a **≈ 27 años** | Derechos limpios, contractualmente garantizados, hoy | Música al brief exacto, iteración en minutos |
| **Comprar el mitigante** — proveedor generativo con **indemnización comercial contractual** | A 1.000 €/mes, la Fase 1 equivale a 3,3 años | Transfiere el riesgo de PI por contrato. Cero desarrollo, cero OPEX, disponible mañana | Control de procedencia, fine-tuning propio. Las indemnizaciones tienen topes y exclusiones que hay que leer con legal |
| **Construir** (esta propuesta) | 39.360 € + recurrentes | Control total, música al brief, trazabilidad desde la primera pista, opción futura de modelo propio | Derechos garantizados — ver la objeción de arriba |

**Recomendación operativa: pedir dos ofertas con cláusula de indemnización en la misma semana en que se consulta a legal.** Cuestan una llamada y pueden ahorrar 98.280 €.

---

## Costes recurrentes

| Concepto | Cifra |
|---|---|
| Infraestructura GPU | **~128 €/mes** con pod caliente en horario laboral (elimina la espera de arranque en frío); 45 €/mes solo con keep-warm |
| Almacenamiento | 0,7 €/mes el mes 1 → ~8 €/mes el mes 12 con la política de retención recomendada. **Sin ella (stems por defecto): 62 €/mes el mes 12 y creciendo sin techo** |
| **OPEX de mantenimiento** (~15 %/año) | **~7.100 €/año** sobre Fases 1+2. Requiere propietario operativo nombrado |
| Horas de no-desarrollo | **116 h** de legal, DPO y supervisor musical |
| Tokens de IA (ejecución asistida) | 1.151 € en total — ~1,2 % del coste humano. Precio verificado contra la documentación oficial |

Una GPU dedicada 24/7 no se justifica: tendría **5,8 % de utilización** al volumen previsto y no compensa hasta unas 5.300 generaciones/mes con el factor de facturación optimista (1,6×) — con el factor conservador que recomienda la evaluación (1,9×), unas **4.500 generaciones/mes** —, entre 4,5 y 5,3 veces el techo estimado.

---

## Riesgos principales

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | **Procedencia legal del output.** Es el riesgo que motiva el proyecto y el que el proyecto no elimina | Gate G2 en la semana 0, con dos preguntas y matriz de resultados; ledger de procedencia desde la primera pista (C-10a en Fase 1) |
| 2 | **La calidad no está validada.** Ningún modelo se ha escuchado con criterio de negocio | Gate G1 con protocolo numérico y línea base ciega; G1-bis por cada adapter nuevo |
| 3 | **Construir lo que se podía comprar.** | Dos ofertas con indemnización, decisión documentada antes de la Fase 1 |
| 4 | **Una sola persona clave.** El perfil (Next.js + FastAPI + CUDA + DSP de audio) es raro y no está definido quién ejecuta | Sin respuesta a «¿quién lo hace?», el calendario no es un compromiso |
| 5 | **Input infractor.** Un usuario puede pegar una letra con copyright y generar una obra derivada con manifiesto impecable sobre un input infractor | Declaración de derechos de la letra en cada generación (Fase 1), registrada en auditoría |
| 6 | **Watermarking: candidatos con licencia MIT identificados** (SilentCipher, AudioSeal — 2026-08-18); **robustez en música por validar** (I-13). Licencias del resto del pipeline por verificar | Condiciona la Fase 2; verificación extendida a todas las herramientas del pipeline (Demucs, RVC) |

---

## Próximos pasos

1. **Consultar a legal (G2)** con las dos preguntas y la matriz de resultados. Sin respuesta escrita, no arranca nada. Timebox: 10 días laborables.
2. **Pedir dos ofertas con indemnización** en la misma semana. Coste: una llamada.
3. **Nombrar** al supervisor musical, a los 3–5 usuarios piloto y a quien ejecuta. Son condiciones del veredicto, no formalidades.
4. Si G2 es favorable: **Fase 0** (2 semanas, 4.020 €) y gate de calidad G1 con escucha ciega.

---

*Documentación completa: `spec.md` (decisiones de diseño y arquitectura) y `evaluation.md` (estimación por característica con rangos, 11 posturas de infraestructura, 29 riesgos, incógnitas). Tres revisiones: aritmética verificada programáticamente, secuenciación auditada de forma adversarial, precio de tokens contrastado con la documentación oficial del proveedor.*

*Actualizado el 2026-09-01 tras revisión de coherencia (`revision-2026-09-01.md`): cifra de aprobación 39.360 € (incl. `T-85`/D-29), catálogo completo 98.280 €, stop-loss al cierre de C-13, watermarking con candidatos MIT (I-13). **El PDF adjunto (`decision-brief.pdf`) se regeneró el 2026-09-01 con estas cifras.***
