---
design: design.md
test-plan: test-plan.md
estado: en-progreso
spec: spec.md
evaluacion: n/a (proyecto personal; ADR-0001)
generacion:
  artefacto: docs/roadmap/2026-10-10-m2-iteracion-creativa/improvement-plan.md
  inicio: '2026-10-10T18:35:31Z'
  fin: '2026-10-10T18:45:35Z'
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  duracion: null
  duracion_reloj: 10m
  ratio_usado: 300000
  ratio_origen: default no calibrado (300000)
  nota: El medidor no detectó respuestas; consumo real, horas IA y coste desconocidos. No se rellenan como medición.
  avisos:
    - 'usage-meter: ventana sin respuestas del modelo; no acredita consumo real.'
---

# 2026-10-10-m2-iteracion-creativa

> Iterar canciones mediante propuestas de texto, takes hijos, edición CPU y comparación A/B, sin perder originales.

| | |
|---|---|
| **Fecha** | 2026-10-10 |
| **Estado** | en-progreso |
| **Tipo** | Nueva funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | Propietario local |
| **Responsable** | Orquestador custom-agents; implementer/QA frescos por unidad |
| **Spec** | [spec.md](spec.md), aprobada, 32 CA |
| **Evaluación** | n/a (proyecto personal; [ADR-0001](../../decisiones/ADR-0001-reinicio-desde-cero.md)) |
| **Diseño** | [design.md](design.md), O2 aprobada; [ADR-0073](../../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md) aceptada |

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|---|---|---|---|
| Tiempo humano | **708h** = 590h base +20% | desconocido | Media/baja |
| Tiempo IA ejecución | **241,2h** = 201h base +20%; supervisión **60,3h** | desconocido | Baja |
| Coste total | Presupuesto formal n/a; **59,17 €** simulación tokens base | desconocido | Baja |
| Tokens IA | **8.040.000** (in 6.030.000 / out 2.010.000) base | desconocido | Baja |
| Multiplicador productividad | **×2,35** | — | Baja |
| Tareas | **30** | 0 hechas | — |

El orquestador aprueba el plan el 2026-10-10 bajo la delegación ya concedida por el propietario, tras revisar las diez funcionalidades, los 32 CA, su matriz de pruebas y los gates reales. No registra una aprobación personal nueva del usuario ni el cierre de M2. M1 permanece abierto, 0/17 tareas completas; se permiten unidades técnicas independientes conforme ADR-0037.

## Estimación por fase

| Fase | Humano base (h) | IA base (h) | Supervisión base (h) | Tokens in / out | Coste informativo € |
|---|---|---|---|---|---|
| 1 — Contratos y unidades CPU independientes | 54 | 20 | 5 | 600000 / 200000 | 5.89 |
| 2 — Integración durable y audio CPU | 104 | 38 | 9.5 | 1140000 / 380000 | 11.19 |
| 3 — Derivaciones musicales | 84 | 30 | 7.5 | 900000 / 300000 | 8.83 |
| 4 — Texto local y providers | 100 | 37 | 9.25 | 1110000 / 370000 | 10.89 |
| 5 — Interfaz creativa | 120 | 41 | 10.25 | 1230000 / 410000 | 12.07 |
| 6 — QA y aceptación real | 128 | 35 | 8.75 | 1050000 / 350000 | 10.30 |
| **Total base** | **590** | **201** | **50,25** | **6.030.000 / 2.010.000** | **59,17** |
| **Total con margen horas +20%** | **708** | **241,2** | **60,3** | Misma previsión base; contingencia tokens aparte | **59,17** |

## Presupuesto económico

**Coste = horas × tarifa + tokens × precio.** ADR-0001 excluye presupuesto formal corporativo. Estas cifras orientan el esfuerzo y no condicionan la ejecución ni simulan factura real.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|---|---|---|
| Tarifa | 0 €/h | .claude/rates.json, proyecto personal |
| Modelo de referencia económica | claude-opus-5-5 | Valor guardado en config; no afirma modelo ejecutor o disponibilidad actual |
| Input/output | 4/20 USD por millón | Config verificada 2026-09-28; precio heredado, revalidar antes de facturación; no consultado en esta planificación |
| Cambio guardado | 0,92 EUR/USD | Supuesto, no cotización actual |
| Cache | No estimada | Medir cuando exista evidencia; no restar caché ficticia |
| Margen | +20% horas humanas e IA | Tokens base mostrados sin inflación; si se consumen +20%, simulación sube a 71,01 € |
| Supervisión / FTE | 25% IA / 160h mes | Supervisión incluye revisiones y escucha; escucha puede ampliar plazo |
| Ratio generación | 300.000 tokens/h, no calibrado | Solo meter; horas ejecución se estiman por tareas, incluyen tests/audio/review |
| Previsión tarea | IA base ×30k entrada +10k salida | Lectura iterativa 6–20 archivos de 1–3k tokens, código/tests y contexto fresh A/B/QA; no tokens medidos |
| Horas | Esfuerzo base humano 10–32h y IA 4–9h/tarea | Confianza baja en seams, modelo, audio y pruebas reales; margen no acredita calidad |

### Desglose

| Concepto | Cálculo | Importe |
|---|---|---|
| Humano base | 590h ×0 | 0 € |
| Contingencia humana | 118h ×0 | 0 € |
| Input | 6,03M ×4 ×0,92 | 22,19 € |
| Output | 2,01M ×20 ×0,92 | 36,98 € |
| **Total con margen de horas** | Horas recalculadas con tarifa 0; tokens base | **59,17 € informativo** |

Los costes reales de API externa son desconocidos y no hay un provider seleccionado. Ninguna petición remote se habilita sin estimación fiable. No hay evaluación económica que heredar ni tarifa nueva elegida por el planner.

## Previsión de tokens (por fase)

| Fase | Input | Output | Total | Coste informativo € |
|---|---|---|---|---|
| 1 | 600000 | 200000 | 800000 | 5.89 |
| 2 | 1140000 | 380000 | 1520000 | 11.19 |
| 3 | 900000 | 300000 | 1200000 | 8.83 |
| 4 | 1110000 | 370000 | 1480000 | 10.89 |
| 5 | 1230000 | 410000 | 1640000 | 12.07 |
| 6 | 1050000 | 350000 | 1400000 | 10.30 |
| **Total** | **6.030.000** | **2.010.000** | **8.040.000** | **59,17** |

Método: estimación a juicio por número de archivos, iteraciones de TDD y rondas de revisión/QA frescas. Horas IA no se calculan automáticamente desde estos tokens de ejecución; esperan CPU, herramientas y evaluación real. La medición de generación de documentos, separada, queda en frontmatter con consumo desconocido si el medidor no lo detecta.

## Productividad IA (humano vs. IA)

| KPI | Valor con +20% |
|---|---|
| Humano | 708h (590 base) |
| IA | 241,2h (201 base) |
| Supervisión | 60,3h (50,25 base) |
| **Total IA + supervisión** | **301,5h** |
| Ahorro aproximado | 406,5h |
| Ahorro | 57,42% |
| Multiplicador | ×2,35 |
| FTE equivalentes | 2,54 meses de 160h |

Son hipótesis de esfuerzo, no calendario ni rendimiento probado. La aceptación humana y la ventana GPU pueden ser la ruta crítica aunque exista ahorro de código.

## Resumen ejecutivo

M2 incorpora las diez funcionalidades F-16, F-17, F-20..F-26 y F-86 completas. El server captura recetas privadas inmutables y produce takes hijos con todos sus padres. La asistencia local devuelve propuestas editables, el worker CPU edita y mide audio, y el comparador sirve previews medidas sin alterar masters. La aceptación exige las cuatro capacidades musicales reales, LLM Docker→Ollama WSL2, escucha y los gates previos de M1/M0.

### Objetivos

- Acreditar 32 CA con trazabilidad explícita en [test-plan.md](test-plan.md).
- Conservar padres, maestro, hashes y manifiestos al derivar, cancelar, reiniciar y comparar.
- Mantener gates por capacidad real y música local; providers optional/off sin fallback.

## Datos necesarios para un informe completo

- [x] Requisitos y diez funcionalidades: spec aprobada.
- [x] Alcance y O2: diseño/ADR-0073 aprobados bajo delegación.
- [x] Criterios: 32 CA, con GWT y audio real.
- [x] Responsable: root, propietario valida escucha; configuración TDD/subagentes/80% leída.
- [x] Restricciones, contratos y dependencias M1/M0 identificados.
- [x] Tarifa 0 y supuestos guardados; evaluación n/a.
- [ ] Modelo LLM/pins/licencia/idiomas/latencia: T-28, no bloquea recipes CPU.
- [ ] Destino privado Docker→WSL2 y controles VRAM reales: T-28.
- [ ] Representación durable CPU y ADR si exige excepción: T-01 antes de T-05/T-07/T-08.
- [ ] Seams M1 liberados/aceptados para integrar y ext4/VHDX persistente: T-05..T-09.
- [ ] M1 cerrado, M0/T-13 y 30 generaciones reales propias: gate T-30; no bloquean unidades independientes.

## Análisis de impacto

El recon local leyó models.Take, PostPlan, export_contracts, package.json, Waveform/Player por diseño, arquitectura/datos/convenciones/contrato y los ADR. La tabla de diseño detalla las rutas existentes; las nuevas siguientes son destinos propuestos. No se ejecutaron suites, GPU, Docker, WSL ni descargas.

- Server/domain/queue: admisión y receta capturada, padres/derechos/letra efectiva, capacidades y CAS.
- Worker/audio-post: autoridad CPU distinta, render/muestras/mapas, medición y replay propio.
- engine-llm: adaptador /v1 sin CUDA hacia servicio externo compartido; residencia con recibos sin mutex global.
- ACE-Step: cuatro adapters con conformidad individual después de liberar fuentes T-09.
- Web: simple/asistente, selección/loop, operaciones, DAG, previews A/B y ajustes por función.
- Contratos/docs: OpenAPI/TS/engine/schema copies, migraciones nuevas y compatibilidad histórica.

## Cambios arquitectónicos

Se aplica O2/ADR-0073; no se rediseña ni añade scheduler/grafo persistente. El contrato privado versionado incluye receta/hash/parents/pins/contexto efectivo. Un lector por versión mantiene planes y recibos M1. No se convierte un edit CPU en una inferencia ficticia.

T-01 concreta O1 de cpu-contract-design.md: Take discriminada, CPU sin modelo/versión/semilla ejecutados y formatos/API v2 conforme ADR-0074. La excepción SQL se limita a take/publication_intent/publication_intent_revision; backup/rollback/FK e históricos se prueban antes de integrar. Cualquier cambio documentado lleva ADR nuevo en docs/decisiones/ y actualiza sus fuentes. No se introduce cpu_take paralelo que rompa FK, master o la canción raíz. Contratos code-first antes de endpoints; engine /v1 solo opcionales y DTO/operaciones M1 intactos. Se añaden cuatro operaciones API server v2 y schemas CPU/song v2, con despacho de lectores; v1 emitido no se reescribe. ADR-0073 no autoriza por sí sola cambiar Constitución.

Audio CPU: índices semiabiertos round-half-up, precisión medida y keep separado de conversión. Crossfade lineal complementario con adaptación explícita, truepeak medido y ambos padres. Estas políticas se validan en T-08/T-29; si el instrumento/pin no las soporta se revisa decisión antes de RED, no se finge capacidad.

A/B: desde masters, T=min(LA,LB,LA+C−PA,LB+C−PB), C=−1dBTP; ganancias≤0. Previews WAV PCM24 sin pérdida, prueba decoder previa; medir tras render, diferencia≤0,5LU y peak≤−1dBTP, 3 intentos máximo con objetivo común menor. Silencio/<3s/no finite deshabilita igualación. TTL24h/1GiB propios, hashes/derechos/lectores revalidados. Manifiesto v2 propio con sujeto job autorizado según ADR-0074, desde recibo/contexto privado sin insertar asset job ni Take ficticia, no take maestro ni modificación retrospectiva.

Residencia: recibo durable privado propio en data/residency, observación/acciones/resultado por execution_id. UNKNOWN no concede propiedad. Descargar y comprobar antes de cargar, vigilar recarga ajena; descargar propio antes de restaurar solo observados realmente retirados por ese turno. Un lock local no excluye otros clientes. Timeout5s observación/120s cambio configurables y lectura1s requieren confirmación real; nunca servicio stop/borrar ni otro almacén.

F-86 añade registro y preflight por función, sin seleccionar provider concreto. F-17 opcional remote requiere adapter verified, key server-only y coste previo fiable/confirmación; local failure no fallback. CA-27 se prueba sintéticamente como contrato condicional; un futuro provider real necesita conformidad/pins/licencia antes de habilitar. Ausencia no bloquea aceptación local, sí impide declarar llamada real.

## Archivos a crear/modificar

| Archivo / grupo | Acción | Propósito |
|---|---|---|
| apps/server/app/creative/ y tests nuevos | Crear | Recipes/compositores/receipts/render orchestration/texto |
| apps/server/app/models/ + migrations/versions/ | Modificar/nueva revisión | Solo tras T-01, compatibilidad durable CPU |
| domain_routes.py/api_models.py/lyrics.py/queue/ | Modificar | Endpoints, admission, historical context, texto y providers |
| worker/contracts/planning/execution/publications/audio_child | Modificar al liberar seam | Autoridad CPU y Publisher M1 |
| packages/audio-post/audio_post/creative_render.py/comparison.py | Crear | Render real/medición sin masters modificados |
| apps/engines/llm/ | Crear | Adapter Docker /v1→Ollama |
| apps/engines/acestep/adapter.py/descriptor.py/tests | Modificar tras T-09 | Gates individuales retake/extend/repaint/cover |
| apps/server/app/providers/ | Crear | Registry/preflight y saneamiento server-only |
| apps/web/app/create,songs,system + componentes y lib | Modificar/crear | Diez features UI castellano |
| packages/contracts/openapi.json, engine-v1.json, manifest-v1.schema.json, song-v1.schema.json, manifest-v2.schema.json, song-v2.schema.json, creative-recipe-v1.schema.json | Regenerar/ampliar | Code-first y schemas versionados opcionales |
| apps/web/lib/generated/api.d.ts y copias schemas audio-post/server | Regenerar/sincronizar | Compatibilidad M1 y cliente |
| docker-compose.yml/.env.example/settings.py | Modificar tras liberación | Adapter local/destino privado |
| models/models.lock.json/scripts/fetch_models.py/docs/legal/licencias.md | Modificar tras selección | Pins/hash/licencia LLM y tools propias |
| docs/arquitectura/iteracion-creativa.md, docs/guias/iteracion-creativa.md, docs/seguridad/providers.md | Crear | Contratos y uso real documentados |
| docs arquitectura/producto/README/RAG-INDEX/changelog | Actualizar por tareas/cierre | Fuentes que describen cambios y límites |

El campo Archivos de cada tarea declara archivos generados y documentos que describen lo modificado. Paths nuevos y revisión de migración se concretan en su unidad; releer contrato real evita archivos imaginarios. No toca agents/commands/hooks del plugin, interop n/a. No se escribe código durante planificación.

## Dependencias y prerequisitos

| Puerta | Se permite | Sigue bloqueado |
|---|---|---|
| Plan aprobado root | T-01; T-02/T-03/T-04 en archivos nuevos contra interfaces CPU | Ninguna integración sin aceptación del seam |
| Contrato CPU y ADR aceptado | Schema nuevo/procedencia honestas T-05 tras release | Edits/publicación sin representación aprobada |
| Seam M1 cola/domain liberado | T-06/T-10 y contratos DTO | No asumir task M1 completada por componente |
| Seam M1/T-05 custodia/publicación aceptado | T-07..T-09 integración con recibos históricos | No bypass de custody/no-clobber/UNKNOWN |
| Fuentes T-09/GPU liberadas | Adapters y conformidad real T-11..T-14/T-27/T-28 | No nueva inferencia ni cambios de imágenes/weights sellados |
| ext4/VHDX/UUID operativo | T-29 persistencia/recovery real | tmpfs no acredita despliegue |
| M1 cerrado, M0/T-13,30 propias+escucha | T-30 aceptación M2 | Mock/CPU solo no cierra hito |

No se cierran tareas con CA pendiente. Si una integración espera seam M1, orquestador puede ejecutar la siguiente unidad nueva independiente y mantener la dependiente en borrador/en-progreso conforme evidencia, sin registrar un segundo ledger. AGENTS regula ownership y actualización exclusiva root.

## Criterios de aceptación (global)

- [ ] 32/32 CA trazados y acreditados conforme matriz test-plan, los diez features completos.
- [ ] Parents/multi-parent/master y manifiestos inmutables, commercial_use combinado, CPU con herramientas reales.
- [ ] Conformidad/escucha retake/extend/repaint/cover individual; descriptor no verified por mocks.
- [ ] LLM Docker/Ollama privado/residencia real, modelo/pins/licencia propios y cinco acciones/tags.
- [ ] A/B salida servida medida y escucha útil, no master modificado ni limitadores ocultos.
- [ ] M1 cerrado,30 generaciones propias reales y M0/T-13 aceptado antes del cierre.
- [ ] TDD/reviews/QA/cobertura≥80%/contratos sincronizados y ledger verificaciones ejecutadas.

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| NULL/variante CPU rompe lectores o FK | Alta | Alto | T-01 contrato/ADR gate, datos M1 regression, no sentinel |
| Seams M1 concurrentes | Alta | Alto | Read-only nuevas unidades primero; release y reread antes integración |
| Mock false positive de capacidades | Alta | Alto | Descriptor real false, individual T-27/T-28 y manuales pendientes |
| Render/mapas/AB incorrectos | Media | Alto | Fixtures audio real, samples/truepeak y escucha antes aceptación |
| Ollama externo recarga/reinicio | Alta | Alto | Recibo durable propio, UNKNOWN/error y restauración condicionada |
| Coste/secreto remote | Media | Alto | Off/función, preflight fiable, server-only/no fallback |
| Falta aceptación M1/30/escucha | Alta | Alto | Gate T-30 explícito sin quitar alcance |

## Métricas de éxito

- 30 tareas, diez funcionalidades y32 CA cubiertos; cero criterios GWT sin escenario.
- Por fase ≥80% cobertura cambiada medida, reviews sin gaps pendientes y QA válido.
- Parent/manifest hashes iguales antes/después en todas derivaciones, edición, preview y recovery.
- A/B≤0,5LU y≤−1dBTP real servido; keep error/latencia/drift según pruebas y escucha, no promesa perfecta.
- Cuatro capabilities musicales conformes y modelo LLM evaluado con resultados reales/versionados; sin modelo global mutex ficticio.

## Changelog del plan

Validación documental del borrador, 2026-10-10: `ledger-lint.py tasks.md` → **0 incoherencias, 0 avisos, exit 0**. `coverage-check.py tasks.md test-plan.md spec.md` → **0 referencias rotas, todos los 24 criterios GWT cubiertos, 0 tareas/escenarios sin referencia, exit 0**. Comprobación local: **34 enlaces comprobados, 0 rotos; 32 filas CA únicas; 30 tareas; bloques generacion idénticos**. `rg -n '\{\{' improvement-plan.md tasks.md test-plan.md` → vacío (exit 1 de búsqueda sin coincidencias). No se ejecutó código de producto, suites, GPU, Docker, WSL ni descargas. Meter cerrado: 10m de reloj; tokens/horas/coste real desconocidos.

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-10-10 | Plan O2 completo en30 tareas; CPU contrato-first, seams condicionados y aceptación real intacta | planner |

## Siguiente paso

Plan aprobado bajo delegación; se inicia T-01, contrato CPU con architect fresco en prosa y pruebas de compatibilidad planificadas. T-02 recipes nuevas puede progresar sin migración/wiring tras interfaz, luego T-03/T-04. No se editan fuentes M1 concurrentes. Implementer fresco ejecuta TDD por unidad; root mantiene ledger, revisiones y QA. Jira y Confluence están desactivados: no envío externo.

