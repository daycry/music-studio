---
estado: aprobado
candidato: false
design: design.md
test-plan: test-plan.md
spec: spec.md
evaluation: n/a
generacion:
  inicio: null
  fin: null
  fuente: estimado
  tokens_reales: { entrada: null, salida: null, cache_creacion: null, cache_lectura: null }
  eur: null
  horas_ia: null
  duracion: null
  ratio_usado: null
  nota: "Ventana y medición a cargo de ROOT; no hay telemetría real atribuible al planner."
---

# 2026-10-11-m3-produccion-portada-video-letra

> Producir canciones con stems, mezcla, análisis, letra sincronizada, portadas, audio y vídeo N0; conservar portabilidad y recuperación real.

| | |
|---|---|
| **Fecha** | 2026-10-11 |
| **Estado** | aprobado |
| **Tipo** | Nueva funcionalidad e integración local |
| **Prioridad** | Media |
| **Solicitante** | Propietario de music-studio |
| **Responsable** | ROOT/orquestador; implementers y QA frescos por tarea |
| **Spec** | [spec.md](spec.md), aprobada: 49 CA/14 funciones |
| **Evaluación** | n/a económica, ADR0001 |
| **Diseño** | [design.md](design.md), O1 ratificada; [ADR0080](../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md) canónica |

Plan aprobado e incorporado por ROOT tras revisión y QA documental. No modifica spec/design/índices ni sustituye ledger alguno ahora. El snapshot readonly de47fuentes es baseline; recibo release-root.receipt.json identifica sus SHA. La ratificación documental previa no acepta producto M3.

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|---|---|---|---|
| Tiempo humano orientativo | 930h base;1116h con +20 % | null | Baja |
| Tiempo IA (ejecución) | n/a | null | n/a |
| Supervisión | n/a | null | n/a |
| Coste total | n/a (ADR0001; tarifa0€/h) | null | n/a |
| Tokens IA input/output | n/a | null | n/a |
| Multiplicador productividad | n/a | null | n/a |
| Tareas | 42 | 0 hechas | Alcance confirmado; esfuerzo incierto |

## Estimación por fase

| Fase | Estimado base (h) | Con +20 % (h) | Tokens (in/out) | Coste € |
|---|---|---|---|---|
| 1 — Contratos y decisiones previas al RED | 130 | 156.0 | n/a | n/a |
| 2 — Autoridad, datos y publicación | 60 | 72.0 | n/a | n/a |
| 3 — Stems, mixer y exportación de audio | 96 | 115.2 | n/a | n/a |
| 4 — Análisis, alineación y karaoke | 76 | 91.2 | n/a | n/a |
| 5 — Portadas Comfy y uploads | 52 | 62.4 | n/a | n/a |
| 6 — Escena N0, renderer y montaje | 88 | 105.6 | n/a | n/a |
| 7 — Audio propio, calidad alta y presets | 72 | 86.4 | n/a | n/a |
| 8 — Portabilidad y biblioteca | 120 | 144.0 | n/a | n/a |
| 9 — Recovery, GPU y runtime offline | 52 | 62.4 | n/a | n/a |
| 10 — Conformidad real y evaluación humana | 164 | 196.8 | n/a | n/a |
| 11 — QA global y cierre | 20 | 24.0 | n/a | n/a |
| **Total** | **930** | **1116** | **n/a** | **n/a** |

## Presupuesto económico

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|---|---|---|
| Economía | n/a | ADR0001, proyecto personal; no presupuesto económico |
| Tarifa | 0€/h | Snapshot .claude/rates.json; no convertir tokens desconocidos en 0€ |
| Horas | Orientativas, confianza baja | Trabajo equivalente humano, no tiempo medido ni promesa de calendario |
| Tokens/horasIA/supervisión | n/a; reales null | No extrapolar reloj, ratio no calibrado o tarifa de otro modelo |
| Margen | +20 % sobre930h | Total1116h; base de tareas sin colchón |
| Modelo/precio/cambio | n/a para presupuesto | rates histórico disponible; no usado para inventar consumo de esta ejecución |
| FTE/productividad | n/a | No calcular ahorro sin mediciones fiables |
| Jira/Confluence | Desactivados | Sin publicación ni sync en esta pasada |

### Desglose

| Concepto | Cálculo | Importe |
|---|---|---|
| Horas orientativas base | Σ42tareas =930h | n/a |
| Margen orientativo | 930×0,20 =186h | n/a |
| Total con margen | 930+186 =1116h | n/a |
| Tokens input/output y ejecución real | null | null |

Las tareas contractuales necesitan6–20h según número de sujetos, fronteras y spikes. Implementación necesita18–32h por unidad por tests causales, integración y errores. QA real necesita24–32h por cohorte/capacidad y recovery; cierre20h. La suma de tasks.md determina los totales; no incluye tiempos de M1/M2 ni esperas por permisos/hardware/personas. Una evaluación económica inexistente no aporta cifras a heredar.

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|---|---|---|---|---|
| 1 — Contratos y decisiones previas al RED | n/a | n/a | n/a | n/a |
| 2 — Autoridad, datos y publicación | n/a | n/a | n/a | n/a |
| 3 — Stems, mixer y exportación de audio | n/a | n/a | n/a | n/a |
| 4 — Análisis, alineación y karaoke | n/a | n/a | n/a | n/a |
| 5 — Portadas Comfy y uploads | n/a | n/a | n/a | n/a |
| 6 — Escena N0, renderer y montaje | n/a | n/a | n/a | n/a |
| 7 — Audio propio, calidad alta y presets | n/a | n/a | n/a | n/a |
| 8 — Portabilidad y biblioteca | n/a | n/a | n/a | n/a |
| 9 — Recovery, GPU y runtime offline | n/a | n/a | n/a | n/a |
| 10 — Conformidad real y evaluación humana | n/a | n/a | n/a | n/a |
| 11 — QA global y cierre | n/a | n/a | n/a | n/a |
| **Total** | **n/a** | **n/a** | **n/a** | **n/a** |

**Método:** no hay previsión ni telemetría de tokens atribuible al planner. ROOT controla la ventana común; reales null. No confundir hashes/checks de prosa con métricas de ejecución.

## Productividad IA (humano vs. IA)

| KPI | Valor |
|---|---|
| Horas humanas orientativas | 930h base;1116h con margen |
| Horas IA/supervisión/totales | n/a |
| Horas ahorradas/ahorro/multiplicador/FTE | n/a |

## Resumen ejecutivo

M3 convierte contenido autorizado de una canción en derivados tipados y revisionados. O1 reutiliza la cola SQLite y el server publicador. La escena N0 compartida alimenta preview y export offline. Las 14 funciones permanecen obligatorias; modelos, almacenamiento y experiencia humana se verifican con pruebas reales antes de aceptación.

### Objetivos

- Conservar los49CA y14funciones de la spec aprobada con tarea y escenario individual.
- Preservar canción raíz, takes/antecedentes inmutables, selección de maestro explícita y autoridad server única.
- Producir audio/N0 completos offline en5070/12GB con pins/derechos y recuperación de biblioteca real.

## Datos necesarios para un informe completo

- [x] Requisitos funcionales, scope y49criterios aprobados.
- [x] O1/ADR0080 canónicos ratificados tras revisión/QA documental, producto pendiente.
- [x] Constitución, locks, seams y dependencias congelados por snapshot47SHA.
- [x] Economía n/a y configuración personal; Jira/Confluence desactivados.
- [x] ROOT bajo delegación del propietario como autoridad de decisiones/adopción.
- [ ] D02–D09 contratos/métricas/perfiles/cuotas cerrados por T02–09 antes RED dependiente.
- [ ] D10/D11 modelos/workflows/modes/licencias/conformidad real por T10/T11 y gatesT36–40.
- [ ] D12 liberaciones M1/M2 por unidad y M2 cerrado para aceptación finalT42.
- [ ] D13 cohorte privada, anotaciones independientes y personas disponibles porT06.
- [ ] Docker persistente ext4/UUID/M1store/lifecycle y GPU libre autorizados para ejecución futura.

Los pendientes son trabajo explícito del plan; no impiden redactarlo ni justifican recortar alcance. Bloquean únicamente sus dependientes y la aceptación de producto.

## Análisis de impacto

- **apps/server/app**: modelos/migraciones, production nuevo, queue/worker, rutas/DTO, backup/snapshots/closure. Único escritor SQLite sin torch.
- **packages/audio-post**: mezcla/export, medición final y manifiestos con autoridad CPU propia.
- **packages/contracts**: code-first aditivo/compatibilidad v1/v2, nuevos schemas ratificados, TimelineV2; preservar publicados.
- **apps/engines**: ACE por capacidades, análisis y nuevo Comfy headless; raw/v1/child/unload/seguridad/offline.
- **apps/web**: mixer transporte común, karaoke/editor, artwork, N0, audio propio/calidad, presets y portable/recovery; cadenas castellanas next-intl.
- **packages/n0-scene**: nuevo bundle Canvas temporal común; server empaqueta browser/font/codec local, no runtime browser del usuario.
- **scripts/eval/docs**: instrumentos de conformance real, cohortes privadas, licencias/pins, documentación y matriz final.

## Cambios arquitectónicos

O1 de design.md/ADR0080 ya cierra la alternativa. No se reabre O2 ni se añade Kafka/Redis/otro escritor. Constitución§2 exige GPU1/CPU2 y engines/v1 compatibles, server sin torch y derivados raw. Presets y revisiones capturan valores por acción; VideoProject.timeline sigue autoridad, el plan N0 es derivado.

D02–09 se concretan antes de RED. CPUv2 se evalúa por sujeto; si no cubre un derivado se decide formato nuevo mediante ADR. No relajar Analysis/Asset por analogía con ADR0074 ni añadir propiedades a TimelineV1 cerrado. Nuevas decisiones documentadas requieren ADR aprobado y fuentes actualizadas por ROOT; este candidato no crea otra decisión canónica.

Mixer usa origen temporal común, no cuatro audio independientes. Escena N0 evalúa t explícito, audio clock en preview y frame_index/fps en export. Features se calculan sobre audio final elegido. Stems no crean take; mix musical publicado como take es hijo CPU de todos sus padres. No se inventa ganador de inferencia para export/render/mantenimiento.

Original mantiene bytes. Export destinos mide final decodificado con lector independiente. Tratamiento dinámico sólo si explícitamente ratificado y visible; objetivo imposible falla honestamente. Backup biblioteca añade corte SQLite+assets con exclusividad y rollback; no confundir backup diario de BD con biblioteca ni copiar VHDX activo.

## Archivos a crear/modificar

Paths existentes siguen tabla de impacto O1. Paths nuevos son destinos propuestos y declarados en Archivos por tarea. T01 registra seams actuales por SHA antes de integración.

| Archivo/área | Acción | Propósito |
|---|---|---|
| apps/server/app/production/ | Crear | Requests/handlers/recibos/revisiones/formats/helpers M3 |
| apps/server/app/models/__init__.py y migrations/versions/ | Modificar/aditivo | Entidades y relaciones ratificadas; conservar históricos |
| apps/server/app/queue/{chains,runtime,resolver,recovery}.py | Modificar | Compositores, derechos/contexto y recovery |
| apps/server/app/worker/{contracts,planning,execution,packages,publications}.py | Modificar selectivo | Autoridad/publicador sin inferencia ficticia |
| apps/server/app/{domain_routes,api_models,snapshots,closure_rows,backup}.py | Modificar | DTO, cierre portable y biblioteca |
| packages/audio-post/audio_post/{pipeline,manifest}.py | Modificar | Mezcla, destinos y métricas finales |
| packages/contracts/ y apps/web/lib/generated/api.d.ts | Generar/añadir schemas | API code-first y formatos compatibles ratificados |
| apps/engines/acestep/ y analysis/ | Modificar | Capacidades, métodos y segmentación validada |
| apps/engines/comfy/ y docker-compose.yml | Crear/modificar | Servicio headless raw/v1 con pins auditados |
| packages/n0-scene/ y apps/server/Dockerfile | Crear/empaquetar | Escena común y renderer offline local |
| apps/web/components/ y app/songs/[id]/page.tsx | Crear/modificar | Producción, revisiones, controles y UI honesta |
| apps/web/messages/es.json y e2e/ | Modificar/crear | next-intl y34GWT individuales |
| models/models.lock.json, tools/tools.lock.json, uv.lock, docs/legal/licencias.md | Actualizar tras decisión | Pesos/formato seguro/pins/licencias; herramientas dentro proyecto |
| scripts/m3_verify_*.py, eval/m3/ | Crear | Instrumentos reales/cohortes/actas privadas; nunca medios en Git |
| scripts/m3_coverage_gate.py, tests/test_m3_coverage_gate.py | Crear en T-06 | Gate estricto de inventario completo y raw oficial por fichero; casos adversos, RED causal y revisión/QA antes del cierre de Fase 1 |
| docs/arquitectura/produccion.md, docs/usuario/produccion.md y documentos contractuales de iniciativa | Crear/actualizar | Decisiones y guía de producto; enlace desde docs/README |

No se tocan agents/commands/hooks: interop no aplica. Cada pieza generada de API/DTO/lock y su documento afectado están dentro del alcance; no hay scope de plugin.

## Dependencias y prerequisitos

T01 verifica D01/D12 y la disponibilidad real por unidad. M1/T05 fullstore/bootstrap/ext4/lifecycle sigue abierto. M2 compositor/publicación/migraciones/render/UI/LLM sigue abierto. Los contratos/unidades puras autorizados por ADR0037 pueden avanzar independientemente tras adopción del plan; integración dependiente espera liberación ROOT por SHA. Ningún hito se cierra por una unidad aceptada.

| Gate | Tarea que lo concreta | Dependientes antes de RED/integración |
|---|---|---|
| D-01 | T-01 | O1 ratificada; verificar sin reabrir |
| D-02 | T-02 | T12,T14 y handlers por sujeto |
| D-03 | T-03 | T13,T16,T20,T29 y SQL |
| D-04 | T-04 | T13,T18,T20,T24,T30,T31 y lectores |
| D-05 | T-05 | T15–18 y T36 |
| D-06 | T-06 | T19–21,T24 y T37 |
| D-07 | T-07 | T24–26 y T39 |
| D-08 | T-08 | T30–31 y T41 |
| D-09 | T-09 | T32–33 y T41 |
| D-10 | T-10 | T15,T27,T28 y T40 |
| D-11 | T-11 | T22–23 y T38 |
| D-12 | T-01 | Toda integración con seam M1/M2 liberado |
| D-13 | T-06 | Spikes/conformance/humanos T10,T11,T36–41 |

Las cifras D05–D08 son propuestas, no valores ratificados por este plan. Cada tarea recoge el texto de design y la decisión ROOT; no se ajustan tras ver los resultados. T10/T11 incluyen descarga/auditoría/spike/conformance como trabajo necesario; un modelo ausente no reduce F18/F19/F35.

## Criterios de aceptación (global)

- [ ] Cada uno de49CA/14F tiene tareas, escenario individual y evidencia vigente por SHA.
- [ ] M2 cerrado y gates heredados M0/M1/M2 cumplidos; ADR0037 no exime aceptaciónM3.
- [ ] Ningún take/manifest histórico reescrito; master explícito, todas las fuentes/roles/rights/hashes presentes y commercial_use conjuntivo.
- [ ] Todas las fases con RED causal, cobertura oficial≥80% ficheros cambiados, revisiónA/B C/Dauto y QA independiente.
- [ ] Docker persistente/ext4/UUID/FFmpeg/lectores/GPU5070/offline y humanos acreditados separadamente; fixtures nunca reemplazan producto.

### Matriz de los49CA

El texto normativo completo permanece en spec.md y se conserva en criterios de tasks.md y bloques de test-plan.md. Esta tabla sólo muestra ubicación; todos están pendientes.

| CA | Tareas | Escenario 1:1 | Evidencia/estado |
|---|---|---|---|
| CA-01 | T-01, T-42 | M-01 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-02 | T-02, T-03, T-12, T-14 | E2E-02 | Pendiente; E2E individual + conformance real relacionado |
| CA-03 | T-12, T-35 | E2E-03 | Pendiente; E2E individual + conformance real relacionado |
| CA-04 | T-06, T-12, T-23, T-27 | E2E-04 | Pendiente; E2E individual + conformance real relacionado |
| CA-05 | T-12, T-23, T-27 | E2E-05 | Pendiente; E2E individual + conformance real relacionado |
| CA-06 | T-14, T-15 | E2E-06 | Pendiente; E2E individual + conformance real relacionado |
| CA-07 | T-05, T-10, T-15, T-36 | M-07 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-08 | T-03, T-13, T-16 | E2E-08 | Pendiente; E2E individual + conformance real relacionado |
| CA-09 | T-17 | E2E-09 | Pendiente; E2E individual + conformance real relacionado |
| CA-10 | T-05, T-16, T-17, T-36 | M-10 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-11 | T-05, T-18, T-36 | E2E-11 | Pendiente; E2E individual + conformance real relacionado |
| CA-12 | T-04, T-05, T-18, T-36 | E2E-12 | Pendiente; E2E individual + conformance real relacionado |
| CA-13 | T-04, T-18, T-36 | E2E-13 | Pendiente; E2E individual + conformance real relacionado |
| CA-14 | T-05, T-18, T-36 | E2E-14 | Pendiente; E2E individual + conformance real relacionado |
| CA-15 | T-14, T-19 | E2E-15 | Pendiente; E2E individual + conformance real relacionado |
| CA-16 | T-19 | E2E-16 | Pendiente; E2E individual + conformance real relacionado |
| CA-17 | T-06, T-19, T-37 | M-17 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-18 | T-03, T-04, T-13, T-20, T-21 | E2E-18 | Pendiente; E2E individual + conformance real relacionado |
| CA-19 | T-21 | E2E-19 | Pendiente; E2E individual + conformance real relacionado |
| CA-20 | T-03, T-13, T-20, T-21 | E2E-20 | Pendiente; E2E individual + conformance real relacionado |
| CA-21 | T-06, T-20, T-21, T-37 | M-21 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-22 | T-11, T-14, T-22, T-23 | E2E-22 | Pendiente; E2E individual + conformance real relacionado |
| CA-23 | T-11, T-22, T-23 | E2E-23 | Pendiente; E2E individual + conformance real relacionado |
| CA-24 | T-23 | E2E-24 | Pendiente; E2E individual + conformance real relacionado |
| CA-25 | T-06, T-11, T-22, T-23, T-38 | M-25 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-26 | T-04, T-07, T-14, T-24, T-25, T-26, T-39 | E2E-26 | Pendiente; E2E individual + conformance real relacionado |
| CA-27 | T-07, T-24, T-25, T-26, T-39 | E2E-27 | Pendiente; E2E individual + conformance real relacionado |
| CA-28 | T-06, T-07, T-25, T-26, T-39 | M-28 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-29 | T-06, T-07, T-25, T-26, T-39 | M-29 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-30 | T-10, T-27 | E2E-30 | Pendiente; E2E individual + conformance real relacionado |
| CA-31 | T-06, T-10, T-27, T-40 | M-31 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-32 | T-10, T-28 | E2E-32 | Pendiente; E2E individual + conformance real relacionado |
| CA-33 | T-06, T-10, T-28, T-40 | M-33 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-34 | T-03, T-13, T-29 | E2E-34 | Pendiente; E2E individual + conformance real relacionado |
| CA-35 | T-29 | E2E-35 | Pendiente; E2E individual + conformance real relacionado |
| CA-36 | T-04, T-08, T-29, T-30, T-31, T-41 | E2E-36 | Pendiente; E2E individual + conformance real relacionado |
| CA-37 | T-08, T-31, T-41 | E2E-37 | Pendiente; E2E individual + conformance real relacionado |
| CA-38 | T-04, T-08, T-31, T-41 | E2E-38 | Pendiente; E2E individual + conformance real relacionado |
| CA-39 | T-04, T-08, T-30, T-31, T-41 | E2E-39 | Pendiente; E2E individual + conformance real relacionado |
| CA-40 | T-09, T-32, T-41 | E2E-40 | Pendiente; E2E individual + conformance real relacionado |
| CA-41 | T-09, T-29, T-33, T-41 | E2E-41 | Pendiente; E2E individual + conformance real relacionado |
| CA-42 | T-09, T-32, T-33, T-41 | E2E-42 | Pendiente; E2E individual + conformance real relacionado |
| CA-43 | T-06, T-09, T-33, T-41 | M-43 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-44 | T-02, T-09, T-14, T-25, T-31, T-32, T-33, T-34 | E2E-44 | Pendiente; E2E individual + conformance real relacionado |
| CA-45 | T-09, T-14, T-31, T-32, T-33, T-34, T-41 | M-45 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-46 | T-10, T-11, T-15, T-22, T-27, T-28, T-35, T-36, T-37, T-38, T-40 | M-46 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-47 | T-07, T-12, T-22, T-25, T-35 | E2E-47 | Pendiente; E2E individual + conformance real relacionado |
| CA-48 | T-01, T-02, T-03, T-04, T-12, T-13, T-14, T-17, T-30, T-31, T-41 | M-48 | Pendiente; instrumento real/acta independiente/ROOT |
| CA-49 | T-06, T-42 | M-49 | Pendiente; instrumento real/acta independiente/ROOT |

### Matriz de las14funciones

| Función | Tareas de implementación y aceptación | CA conservados | Gate obligatorio |
|---|---|---|---|
| F-06 | T-30, T-31, T-34, T-41 | 36–39,44,48 | Roundtrip real multiversión, negativos ZIP y reproducción, pendiente |
| F-18 | T-10, T-28, T-35, T-40 | 32–33,46 | Modo M0 conforme y escucha emparejada, pendiente |
| F-19 | T-10, T-12, T-27, T-35, T-40 | 04–05,30–31,46 | Ruta real audio propio y escucha, pendiente |
| F-30 | T-10, T-15, T-35, T-36 | 06–07,46 | Separación real muestras/suma/aislamiento, pendiente |
| F-31 | T-16, T-17, T-36 | 08–10 | Transporte y equivalencia export/escucha, pendiente |
| F-32 | T-18, T-36 | 11–14,48 | FFmpeg final y lector independiente, pendiente |
| F-33 | T-19, T-37 | 15–17 | Anotaciones/medidor independientes, pendiente |
| F-34 | T-20, T-21, T-37 | 18–21 | Canto castellano real/corrección/seek, pendiente |
| F-35 | T-11, T-22, T-23, T-35, T-38 | 22–25 | Generación y edición ref DockerCUDA/visual, pendiente |
| F-40 | T-24, T-25, T-26, T-34, T-39 | 26,28–29,44 | Canción completa sync/legibilidad/perfil/recovery, pendiente |
| F-41 | T-24, T-26, T-39 | 27–29 | Audio efectivo/silencio/seek en tres modos, pendiente |
| F-44c | T-12, T-23, T-26, T-38, T-39 | 04–05,24,26 | Upload derechos/fondo sin generación, pendiente |
| F-70 | T-29, T-30, T-33, T-41 | 34–35,36,41 | Valores/refs congelados y restore, pendiente |
| F-85 | T-09, T-32, T-33, T-34, T-41 | 40–43,45 | Biblioteca real coherente/ext4/rollback, pendiente |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Seams M1/M2 todavía no liberados | Alta | Alto | T01 liberación por SHA; unidades puras independientes, aceptación con M2 cerrado |
| Modelos/modos no caben o no mejoran calidad | Alta | Alto | Spikes/seguridad/licencias/cohortes T10/T11, obligaciones F18/F19/F35 intactas |
| WSL desborda VRAM a RAM silenciosamente | Media | Alto | Libre−margen, modo explícito, picos/compartida/spill y unload por capacidad |
| Renderer/codec lento o incompatible | Alta | Alto | D07 previo, canción completa Libre4:15, browser/lector y presupuesto congelado |
| ZIP/concurrencia/restore corrompe historia | Media | Alto | D08/D09, staging/intenciones/custodia, guardas y fault injection ext4 |
| Simulación se confunde con conformance | Media | Alto | Matriz por entorno y SHA; no habilitar descriptor por fixture ni autoaprobar |
| Choque en checkout compartido | Alta | Alto | Actor fresco/ownership/brief, snapshots privados/CAS ROOT; no stageglobal ni rollback ajeno |

## Métricas de éxito

- 49/49criterios y14/14funciones aceptados con matriz de evidencia; ningún gate sustituido por prosa.
- 34GWT:34E2E individuales;15CA técnicos/perceptuales:15M completos; tests vinculados a42tareas.
- Cobertura whole oficial≥80% de cada fichero de producción vigente cambiado, por stack y SHA de fase, con inventario completo ROOT y raw oficial; sin medias/exclusiones/omisiones ni missing aprobado. Procedimiento y CLI futura del gate estricto en tasks.md; instrumento y pruebas declarados en T-06.
- Métricas de suma/mezcla/LUFS/TP/timing/beat/key/sections/N0 y minutos cumplen sólo los umbrales D05–07 previamente ratificados.
- Ext4/recovery/restore y GPU/unload/offline probados con recursos propios; biblioteca original intacta y actas humanas reales.

## Changelog del plan

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-10-11 | Candidato completo:42tareas,11fases,49CA/14F,34E2E/15M; ninguna implementación iniciada | planner privado |
| 2026-10-11 | FIX1 privado G01/G02/G03: preparación sin autocierre, ledger sólo ROOT y gate whole por fichero con inventario/raw oficial; mismas horas orientativas, sin producto ni actas inventadas | planner FIX1 |

## Siguiente paso

ROOT revisa los tres candidatos, ejecuta puertas documentales/revisión fresca/QA y decide adopción concreta. Al adoptar, resuelve links en carpeta canónica, actualiza spec plan/callout, design plan y READMEroadmap en un cambio acotado; economía n/a, estado borrador. Sólo después libera T01–11 y unidades independientes por ADR0037. Implementer ejecuta mediante briefs frescos y entrega evidencia; sólo ROOT actualiza tasks.md. El orden de conformidad es contratos/seams → instrumentos y artefactos candidatos → actas humanas → revisión/QA → cierre ROOT; las tareas que necesitan actas permanecen abiertas hasta reunirlas. M2 cerrado/gates heredados y la matriz final siguen siendo requisitos de T-42. QA independiente conserva evidencias reales/humanas. No se publica en Jira/Confluence.



## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.
