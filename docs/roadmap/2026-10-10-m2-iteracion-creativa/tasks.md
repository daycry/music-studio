---
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
# ventana compartida con improvement-plan.md
verificacion: obligatoria
estado: en-progreso
---

# Checklist de Tareas — M2: iteración creativa

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-10-10 |
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseño** | [design.md](design.md) — O2 / ADR-0073 aceptada |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente implementer, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente. En este proyecto solo el orquestador actualiza el ledger; subagentes entregan evidencia y no escriben aquí.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|---|---|---|---|---|---|---|---|
| Fase 1 — Contratos y unidades CPU independientes | 4 | 4 | 100% | — / 54h | — / 20h | — / 5h | — / 800000 |
| Fase 2 — Integración durable y audio CPU | 0 | 5 | 0% | — / 104h | — / 38h | — / 9.5h | — / 1520000 |
| Fase 3 — Derivaciones musicales | 0 | 5 | 0% | — / 84h | — / 30h | — / 7.5h | — / 1200000 |
| Fase 4 — Texto local y providers | 0 | 5 | 0% | — / 100h | — / 37h | — / 9.25h | — / 1480000 |
| Fase 5 — Interfaz creativa | 0 | 6 | 0% | — / 120h | — / 41h | — / 10.25h | — / 1640000 |
| Fase 6 — QA y aceptación real | 0 | 5 | 0% | — / 128h | — / 35h | — / 8.75h | — / 1400000 |
| **TOTAL** | **4** | **30** | **13%** | **— / 590h** | **— / 201h** | **— / 50.25h** | **— / 8040000** |

> Horas y tokens de tareas/fases son BASE aproximada. Margen global +20%: humano 708h; IA 241.2h; supervisión 60.3h. No hay reales observados. Presupuesto formal n/a por ADR-0001; euros son simulación informativa de rates.json. Jira/Confluence desactivados.

## Reglas de ejecución y dependencias

- Plan aprobado por el orquestador el 2026-10-10 bajo la delegación del propietario, tras contrastar las diez funcionalidades, los 32 CA y sus gates reales. No representa una aprobación personal nueva del usuario ni el cierre de M1/M2.
- T-01 prepara decisión con architect fresco y la acepta el orquestador; no el planner. T-02/T-03/T-04 pueden iniciar en archivos nuevos CPU tras contrato de interfaz, sin nueva migración ni wiring. Un gate de integración pendiente no bloquea esas unidades independientes.
- Integración T-05..T-14/T-17..T-25 requiere liberación explícita del seam M1 y relectura del árbol actual. M1 está abierto, 0/17 cerrado. No editar fuentes concurrentes ni selladas M0/T-09. No usar un worktree divergente como permiso de merge.
- No estás solo: conservar cambios ajenos y reconfirmar ownership por unidad. Una rama m2/t-XX; commits castellanos Conventional Commits [M2/T-XX]. Orquestador coordina FF a main sin PR.
- TDD RED conductual antes de producto; reviews fresh A/B, C/D auto y QA/cobertura cambiada≥80% por fase. Rojos/greens/terminales y hashes se entregan al orquestador. No cierre por test mock con requisito real pendiente.
- Comandos se ejecutan desde la raíz tras cargar scripts/env.ps1 o env.sh. Destinos test nuevos son entregables de las tareas, no tests existentes ni ejecutados durante planificación. Adaptador ACE usa su entorno gestionado/contenedor después de liberar T-09, nunca Python global.
- Todo cambio de API regenera OpenAPI y tipos: uv run python scripts/export_contracts.py; pnpm --dir apps/web gen; export --check. Copias de manifest/song schemas se sincronizan en el mismo commit. /v1 añade solo opcionales.
- Verificación de contrato en cada cambio: `uv run python <plugin>/skills/api-contract/scripts/openapi-lint.py packages/contracts/openapi.json` y `--diff <baseline-exportado.json> packages/contracts/openapi.json`; resolver `<plugin>` en la instalación local de custom-agents, sin versionar rutas personales. Exit 0 sin breaking. Baseline desde revisión aceptada en `.cache/dev-cycle/m2/T-XX/`, nunca inventada. JSON de engine y schemas se valida además con sus tests. El lint mínimo puede encontrar deuda previa: registrar baseline y resolver defectos en alcance, sin silenciar ni atribuir deuda M1 a M2.
- Real GPU/Docker/WSL/descargas se hacen en ventana propia futura, coordinada por root. No ejecutadas en planificación. M0/T-13/M1 cerrado/30 generaciones propias/escucha siguen gates finales.

## Fase 1 — Contratos y unidades CPU independientes

**Estado**: completado · **Estimado**: 54h base · **Real**: — · **Coste est.**: 5.89 € informativo · **Tokens est.**: 800000

### T-01 — Resolver representación contractual CPU y compatibilidad

- **Descripción**: Comparar una representación de procedencia discriminada con modelo/versión/semilla opcionales solo para CPU frente a una variante compatible. La opción elegida O1 discrimina inference/cpu_edit: sólo CPU permite NULL, inferencia conserva tres campos obligatorios. ADR-0074 delimita tres tablas y garantías previas antes de alterar NOT NULL o reconstruir SQLite. Documentar impacto sobre DTO/schema/snapshots/manifiestos y lectores históricos. Si exige relajación o reconstrucción de tablas, aprobar ADR nuevo y excepción precisa a migraciones estrictamente aditivas antes de tocar producto; no modificar baseline M1.
- **Estado**: completado
- **Tiempo humano**: est. 12h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 4h (estimado) · real —
- **Supervisión**: est. 1h (25 % IA) · real —
- **Previsión IA**: 120000 in / 40000 out tok · 1.18 € informativo
- **Dependencias**: ninguna; primera unidad viable tras aprobación del plan
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md`, `docs/decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md`, `docs/decisiones/README.md`, `docs/arquitectura/datos.md`, `docs/arquitectura/pipeline-audio.md`, `docs/CONSTITUTION.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/spec.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/improvement-plan.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/test-plan.md`, `docs/decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md`, `docs/roadmap/README.md`
- **Changelog**: Contrato CPU discriminado y formatos/API v2 definidos sin identidad ficticia; conserva historia M1 y delimita tres tablas con garantías de migración.
- **Cubre (tests)**: M-08
- **Criterios spec**: CA-29, CA-32
- **Verificación**: lectura: comparar esquema Take vigente, PostPlan y lectores M1; ADR aceptado y matriz de compatibilidad sin identidad ficticia → acta y compatibilidad revisadas por el orquestador

**Criterios de aceptación**

- [x] Contrato especifica cómo almacenar un edit en Take sin engine/modelo/semilla ficticios ni atribuir antecedentes como ejecución; vieja inferencia sigue exigiendo los tres campos.
- [x] ADR y documentos afectados aceptados por orquestador bajo delegación, antes de T-05/T-07; si la opción preferida no prueba compatibilidad, resolver alternativa sin falsear datos.
- [x] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [x] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [x] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [x] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-29, CA-32. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

**Verificación ejecutada (orquestador, 2026-10-10):** matriz contrastada contra Take/PostPlan/DTO/manifest/song actuales y sondas privadas de NOT NULL/API/SQLite; decisión O1/ADR-0074 aceptada y once fuentes compartidas integradas. Revisión A/B intento 2 sin gaps tras corregir B01; QA documental independiente 16/16, 201 enlaces existentes, once fuentes y trece documentos sin drift. Root comprobó 23 artefactos de inventario, 13 hashes, gate exit0 y negativo API exit1 esperado a las 19:25:05 UTC. TDD n/a: prosa; cobertura de producto porcentual n/a. Informe `testing/t01/contract-qa-2026-10-10.md`; recibos `.cache/dev-cycle/m2/t01-cpu-contract-20261010/`. Sólo cierra la decisión contractual, no migración, render, E2E, M-08 integral ni aceptación musical M2. Tiempo/tokens/coste reales desconocidos.

### T-02 — Recetas privadas tipadas, versionadas e inmutables

- **Descripción**: Crear DTO privado cerrado y schema_version, JSON canónico/hash, receta capturada en job.request y lectores por versión. Capturar owner/song/job/take, referencias/hashes y letra histórica efectiva, derechos, parámetros, roles/mapas y pins. No expresiones, paths navegador ni grafo editable.
- **Estado**: completado
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-01 para representación; puede empezar contra contrato provisional sin runtime M1
- **Tipo**: backend
- **Archivos**: `apps/server/app/creative/__init__.py`, `apps/server/app/creative/recipes.py`, `apps/server/tests/test_creative_recipes.py`, `docs/arquitectura/iteracion-creativa.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md`, `docs/decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md`
- **Changelog**: Captura recetas creativas inmutables con padres, derechos y parámetros efectivos; comprueba sus hashes y lee peticiones históricas sin reescribirlas.
- **Cubre (tests)**: E2E-03, E2E-04, E2E-05, E2E-07
- **Criterios spec**: CA-07, CA-09, CA-11, CA-15, CA-29
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_recipes.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [x] Mutar nested params después de captura no cambia bytes/hash; rechaza extras, secretos, NaN e IDs/refs inválidas.
- [x] Receta conserva todos los padres y campos efectivos; snapshot legacy se interpreta sin reescritura.
- [x] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [x] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [x] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [x] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-07, CA-09, CA-11, CA-15, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

**Verificación ejecutada (ROOT, 2026-10-11T13:16:22.427044+00:00):** `uv run pytest -q apps/server/tests/test_creative_recipes.py` → **183 passed, exit0**, ejecutada por QA independiente con recibo/argv/cwd/UTC/stdout exactos; cobertura separada183PASS, paquete creative completo88,502269%,0exclusiones,3probes propios sinI/O. Revisión de producto A+B intento3sin gaps tras corregir A01/B01/B02/B03, C/Dauto false; C1limpia conservada. ROOT verifica60artefactosQA/158fuentes sin drift/JUnit/imports/gates final0 e inicialrojo1/Ruff0/format0. La incidencia PDF de entrega está resuelta: informe MD y PDF de8páginas verificados; capturas deHTML en impresión sin desbordamiento y textoPDFUTF8 completo, sin afirmar rasterPDF. [QA actual](testing/t02/creative-recipes-current-qa-2026-10-11.md), [PDF](testing/t02/creative-recipes-current-qa-2026-10-11.pdf), [revisión3](testing/t02/creative-recipes-product-review3-2026-10-11.md). RecibosROOT `.cache/dev-cycle/m2/creative-recipes-t02-current-qa1-root-20261011/verification-root.receipt.json` y `publication-root.receipt.json`; originales219/FIX1244/FIX2136/reviews/QA60preservados. Cierra solamente esta unidadCPU pura conforme ADR0037: job.request conserva el envelope mediante la proyección que la integración futura almacenará; no se afirma SQL/render/admission/publicación/E2E03/04/05/07/audio ni aceptaciónM2. Métricas reales desconocidas, sin imputar tiempo de reloj como IA.

### T-03 — Compositores cerrados y mapas temporales puros

- **Descripción**: Planificar keep, fades, crossfade, regenerate y extend. Distinción salida completa/región de cada adapter: no ensamblar dos veces. Resolver índices una vez con round-half-up, rango semiabierto; duración efectiva viene de muestras, no request. Mapas por arista y raíz menor ULID original.
- **Estado**: completado
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-02; nuevo módulo CPU independiente, sin modificar cola M1
- **Tipo**: backend
- **Archivos**: `apps/server/app/creative/composition.py`, `apps/server/tests/test_creative_composition.py`, `docs/arquitectura/iteracion-creativa.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md`, `docs/decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md`
- **Changelog**: Planificador puro por muestras para ocho operaciones creativas, mapas de ambos padres, conversión explícita y codec/replay inmutable con errores sanitizados.
- **Cubre (tests)**: E2E-04, E2E-05, E2E-07
- **Criterios spec**: CA-09, CA-11, CA-13, CA-14, CA-15
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_composition.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [x] Negativos finitos/intervalos/duraciones y respuesta completa/región quedan probados antes de render.
- [x] Crossfade conserva ambos roles y canales/rate explícitos; convert nunca aparece como keep puro.
- [x] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [x] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [x] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [x] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-09, CA-11, CA-13, CA-14, CA-15. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.


**Verificación ejecutada ROOT** (2026-10-11T16:01:36.792725+00:00): uv run --frozen --no-sync --all-packages pytest -q apps/server/tests/test_creative_composition.py (temporales/JUnitdentrorepo) →91passed,exit0. QAindependienteWindows274PASS/Linux274PASS,91focal183regresiónT02,mismos274IDs; whole94,7917%líneas/88,4615%ramas cadaentorno,0excl. [Informevigente](testing/composition-product-current-qa1-2026-10-11.md). Revisión2A/Bsin gaps,A01corregido conTDDreescrituraguardaexistente; contrato18AC. CASruntimef2b5a79/tests2c5464e trasverificaciónROOT168payload/97fuentes. AlcancepuroT03: noE2E04/05/07/render/audio/publicación/qualitymodel. Tarea cerrada sinaceptaciónhitoM2.

### T-04 — Arnés contractual y fixtures de regresión M1

- **Descripción**: Congelar fixtures sintéticos versionados desde contratos/recibos históricos, hashes y pares viejo/nuevo. Diseñar contratos code-first antes de endpoints; fixture se identifica como sintético. Preparar diff de OpenAPI exportado desde revisión base aislada, sin sobrescribir fuente concurrente.
- **Estado**: completado
- **Tiempo humano**: est. 10h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 4h (estimado) · real —
- **Supervisión**: est. 1h (25 % IA) · real —
- **Previsión IA**: 120000 in / 40000 out tok · 1.18 € informativo
- **Dependencias**: T-01..T-03; fuentes compartidas solo lectura hasta liberación
- **Tipo**: test
- **Archivos**: `apps/server/tests/test_creative_contract_compatibility.py`, `apps/server/tests/fixtures/creative/`, `packages/contracts/creative-recipe-v1.schema.json`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/contract-baseline.md`
- **Cubre (tests)**: E2E-12, M-08
- **Criterios spec**: CA-20, CA-29, CA-32
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_contract_compatibility.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [x] Regresión carga engine PostPlan histórico, recipe CPU nueva y lectores de snapshot manifiesto/song; diferencia contractual incompatible falla.
- [x] Fixtures no contienen datos privados; resultado es compatibilidad contractual, no custodia real.
- [x] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [x] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [x] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [x] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-20, CA-29, CA-32. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

## Fase 2 — Integración durable y audio CPU

**Estado**: en-progreso · **Estimado**: 104h base · **Real**: — · **Coste est.**: 11.19 € informativo · **Tokens est.**: 1520000

**Verificación ejecutada ROOT** (2026-10-11T17:21:59.150137+00:00): uv run pytest -q apps/server/tests/test_creative_contract_compatibility.py →69 passed, exit0; entorno gestionado y temporales/JUnit propios. QA independiente Windows343PASS/LinuxDocker343PASS, mismos343casos únicos por plataforma, y3controles privados cada una. Revisión2A/B sin gaps B01/B02/A01 corregidos. Schema code-first05ef38f2 y22goldens originales; alcance contractual CPU/config, no E2E-12/M-08 ni custodia/audio/modelo/hito. [Informe vigente](testing/contract-current-qa1-2026-10-11.md).

- **Changelog**: Añade fixtures sintéticos y pruebas de compatibilidad de contratos históricos, junto al esquema privado de recetas con límites efectivos de listas y números.

### T-05 — Schema durable y procedencia diferenciada

- **Descripción**: Implementar solo schema elegido T-01, migración nueva idempotente y replay histórico. Por defecto aditiva; excepción específica únicamente si ADR aprobado. No renombrar/borrar datos, no modificar 0001. Revalidar seam actual antes de definir nombre de nueva revisión.
- **Estado**: en-progreso
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-01 ADR aceptado, T-04; liberar models/migrations/snapshot M1 antes de editar
- **Tipo**: db
- **Archivos**: `apps/server/app/models/__init__.py`, `apps/server/app/migrations/versions/`, `apps/server/app/api_models.py`, `apps/server/app/snapshots.py` (si exige el lector vigente), `apps/server/tests/test_creative_persistence.py`, `packages/contracts/song-v1.schema.json`, `apps/server/app/models/song-v1.schema.json`, `packages/contracts/song-v2.schema.json`, `apps/server/app/models/song-v2.schema.json`, `apps/server/app/domain_routes.py`, `apps/web/lib/api.ts`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `docs/arquitectura/datos.md`, `docs/arquitectura/iteracion-creativa.md`, `apps/server/app/migrations/cpu_publication_invariants.py`, `apps/server/app/migrations/env.py`, `apps/server/app/db.py` (si la entrada exclusiva lo exige), `apps/server/app/creative/durable_contracts.py`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/creative-persistence-contract.md`, `apps/server/tests/test_creative_legacy_registry.py`, `apps/server/app/migrations/fix1_invariants.py`, `apps/server/app/migrations/fix2_invariants.py`, `apps/server/app/migrations/legacy_m1_registry.py`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/creative-legacy-freeze-*.md`, `apps/server/app/migrations/creative_persistence_invariants.py`, `apps/server/app/migrations/versions/0008_cpu_creative.py`, `apps/server/tests/test_creative_schema.py`, `apps/server/tests/test_creative_migration.py`, `apps/server/tests/test_schema_t02.py`, `apps/server/tests/test_attempt_json_guard_upgrade.py`, `apps/server/app/main.py`, `apps/server/app/publication.py`, `apps/server/app/queue/runtime.py`, `apps/server/app/migration_coordinator.py`, `apps/server/tests/test_cpu_migration_coordinator.py`, `apps/server/tests/test_cpu_migration_startup.py`, `apps/server/app/worker/execution.py`, `apps/server/app/worker/custody_linux.py`, `apps/server/app/worker/custody_linux_supervisor.py`, `apps/server/app/worker/audio_child.py`, `apps/server/app/worker/migration_lease.py`, `apps/server/tests/test_cpu_migration_child_admission.py`, `apps/server/app/backup.py`, `apps/server/tests/test_persistence_t02.py`, `apps/server/tests/test_worker_snapshots.py`, `apps/server/tests/test_job_attempt_schema.py`, `apps/server/tests/test_review_fix1_t02.py`, `apps/server/tests/test_review_fix2_t02.py`, `apps/server/tests/test_review_fix3_t02.py`
- **Cubre (tests)**: E2E-08, M-08
- **Criterios spec**: CA-16, CA-17, CA-29
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_persistence.py apps/server/tests/test_schema_t02.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Biblioteca M1 antes/después conserva IDs, filas, restricciones, hashes y maestro; backup/restauración prueba versión.
- [ ] CPU durable distingue herramientas ejecutadas de antecedentes; inferencia no acepta campos requeridos ausentes.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-16, CA-17, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-06 — Admisión y cadenas de derivación transaccionales

- **Descripción**: Resolver refs propias listas y capturar receta efectiva en una transacción; derechos/letra/capacidad verificada antes de encolar. Crear dependencias generation→construction→post sin scheduler nuevo; CPU 2/GPU 1. CAS protege confirmación y reintento.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-02..T-05; liberar chains/references/inputs/resolver/provenance M1
- **Tipo**: backend
- **Archivos**: `apps/server/app/queue/chains.py`, `apps/server/app/queue/references.py`, `apps/server/app/queue/inputs.py`, `apps/server/app/queue/resolver.py`, `apps/server/app/queue/provenance.py`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/tests/test_creative_admission.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `docs/arquitectura/iteracion-creativa.md`, `docs/arquitectura/datos.md`
- **Cubre (tests)**: E2E-03, E2E-04, E2E-05, E2E-06, E2E-12
- **Criterios spec**: CA-06, CA-13, CA-16, CA-20, CA-30
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_admission.py apps/server/tests/test_queue_inputs.py apps/server/tests/test_queue_chains.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Take ajeno/borrado/no listo, rights ausentes y verified=false no crean ni envían job.
- [ ] Variantes guardan nuevo ID y todos los parents, sin promoción de maestro; fallo transaccional no deja cadena parcial.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-06, CA-13, CA-16, CA-20, CA-30. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-07 — Autoridad CPU y publicación/recovery compartidos

- **Descripción**: Plan CPU separado o variante discriminada elegida, sin winning_attempt_id engine. Recibo execution_id/recipe/hash/pins/parents/derechos propio, hijo supervisado, terminal y CLOSED_CONFIRMED antes CAS/no-clobber. Revalidar contexto histórico capturado, no letra actual. UNKNOWN bloquea publicar y limpiar.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 9h (estimado) · real —
- **Supervisión**: est. 2.25h (25 % IA) · real —
- **Previsión IA**: 270000 in / 90000 out tok · 2.65 € informativo
- **Dependencias**: T-05/T-06; aceptación seam M1/T-05 custody/publications; integración bloqueada mientras concurrente
- **Tipo**: backend
- **Archivos**: `apps/server/app/worker/contracts.py`, `apps/server/app/worker/planning.py`, `apps/server/app/worker/execution.py`, `apps/server/app/worker/publications.py`, `apps/server/app/worker/audio_child.py`, `apps/server/app/creative/cpu_execution.py`, `apps/server/tests/test_creative_publication.py`, `packages/audio-post/audio_post/private_context.py`, `packages/audio-post/audio_post/manifest.py`, `packages/contracts/manifest-v1.schema.json`, `packages/audio-post/audio_post/manifest-v1.schema.json`, `packages/contracts/manifest-v2.schema.json`, `packages/audio-post/audio_post/manifest-v2.schema.json`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-07, E2E-11, M-05, M-08
- **Criterios spec**: CA-16, CA-29, CA-30
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_publication.py apps/server/tests/test_worker_publication_invariants.py apps/server/tests/test_worker_recovery_regression.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Replay tras muerte antes/después rename/commit no duplica takes/assets ni toca padre o maestro; no ready parcial.
- [ ] Manifest v2 CPU nuevo/inmutable y v1 histórico intacto combinan commercial_use; no CPU terminal sintético ni presencia de archivos como autoridad.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-16, CA-29, CA-30. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-08 — Render CPU de recorte, fades y crossfade

- **Descripción**: Render real FFmpeg en hijo CPU. Canonical PCM24 FLAC, rate/canales iguales conserva formato; distintos convierten explícitamente a 48kHz estéreo con soxr fijado y conversión declarada. Fade lineal, crossfade complementario; duración <= entradas, true peak medido <=−1dBTP o rechazo explícito, sin normalizar padre.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-03/T-07; FFmpeg fijado y runner CPU propio liberado
- **Tipo**: backend
- **Archivos**: `packages/audio-post/audio_post/creative_render.py`, `packages/audio-post/tests/test_creative_render.py`, `apps/server/app/creative/composition.py`, `apps/server/tests/test_creative_edit.py`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-07, M-01, M-05
- **Criterios spec**: CA-13, CA-14, CA-15, CA-16, CA-29
- **Verificación**: `uv run pytest -q packages/audio-post/tests/test_creative_render.py apps/server/tests/test_creative_edit.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Keep sin conversión: error absoluto por muestra <=1 LSB PCM24 alineado; no afirma bit identity. Con conversión compara referencia FFmpeg fijada <=2 LSB y etiqueta convert.
- [ ] Mapa medido/duración ±1 muestra; cero carga GPU; clips, vacío, clipping o render incompleto rechazan sin tocar originales.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-13, CA-14, CA-15, CA-16, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-09 — Previews A/B medidos y custodia temporal

- **Descripción**: Medir masters via measure_audio/FFmpeg ebur128 fijado, fórmula ADR0073, ganancias solo <=0. Preview WAV PCM24 sin pérdida a 48kHz tras prueba decoder T-24. Re-medición salida: ≤0,5LU y ≤−1dBTP. Máximo 3 renders con objetivo común reducido; fallo/silencio/no finite/<3s deshabilita igualación. Caché clave owner+song+hashes+policy/pins, TTL24h y 1GiB configurable, lectores/custodia impiden cleanup.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 9h (estimado) · real —
- **Supervisión**: est. 2.25h (25 % IA) · real —
- **Previsión IA**: 270000 in / 90000 out tok · 2.65 € informativo
- **Dependencias**: T-07/T-08; almacenamiento persistente M1 antes de aceptar integración
- **Tipo**: backend
- **Archivos**: `packages/audio-post/audio_post/comparison.py`, `packages/audio-post/tests/test_comparison.py`, `apps/server/app/creative/comparisons.py`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/tests/test_comparison_cache.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `packages/contracts/manifest-v1.schema.json`, `packages/audio-post/audio_post/manifest-v1.schema.json`, `packages/contracts/manifest-v2.schema.json`, `packages/audio-post/audio_post/manifest-v2.schema.json`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-09, E2E-11, M-02, M-05
- **Criterios spec**: CA-18, CA-19, CA-29, CA-30
- **Verificación**: `uv run pytest -q packages/audio-post/tests/test_comparison.py apps/server/tests/test_comparison_cache.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Manifest propio sujeto job autorizado resuelto conforme T-01; ningún preview se sirve parcial ni inserta como maestro.
- [ ] Cambio de hash/derechos/borrado invalida caché; Range/propiedad comprobados; límites no borran lectores ni recursos ajenos.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-18, CA-19, CA-29, CA-30. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

## Fase 3 — Derivaciones musicales

**Estado**: borrador · **Estimado**: 84h base · **Real**: — · **Coste est.**: 8.83 € informativo · **Tokens est.**: 1200000

### T-10 — Variación de petición con semilla nueva

- **Descripción**: Recuperar petición efectiva seleccionada y versión histórica, no campos actuales song. Nueva seed validada y resto preservado; derivation variant. Esta ruta no necesita retake ni confunde audio source con repetición.
- **Estado**: borrador
- **Tiempo humano**: est. 12h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 4h (estimado) · real —
- **Supervisión**: est. 1h (25 % IA) · real —
- **Previsión IA**: 120000 in / 40000 out tok · 1.18 € informativo
- **Dependencias**: T-06/T-07; gate music.song/instrumental real independiente
- **Tipo**: backend
- **Archivos**: `apps/server/app/creative/variations.py`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/tests/test_creative_variations.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-03, M-03
- **Criterios spec**: CA-06, CA-07, CA-16
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_variations.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Test muta letra/style actual y conserva petición elegida; semilla efectiva queda en manifest.
- [ ] Padre/master/hash inmutables e instrumental sin declaración de letra.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-06, CA-07, CA-16. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-11 — Adapter y cadena music.retake

- **Descripción**: Adapter retake con source exacto master elegido y params_schema/limits reales. Tests de traducción sintéticos no marcan verified; T-27 conserva conformidad/escucha.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-06/T-07; fuentes ACE liberadas por M0/T-09, descriptor real por verificar
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_creative_retake.py`, `apps/server/app/creative/derivations.py`, `apps/server/tests/test_creative_retake.py`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/modelos.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-03, E2E-12, M-03
- **Criterios spec**: CA-08, CA-16, CA-20, CA-21
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_retake.py` → focal server pasa · `docker compose run --rm --no-deps engine-acestep uv run pytest -m "not gpu" -q tests/test_creative_retake.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Input source/hash corresponde al padre capturado; UI/API gate false sin envío.
- [ ] Descriptor solo admite controles demostrados; versión/pins y provenance del hijo correctos.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-08, CA-16, CA-20, CA-21. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-12 — Adapter y construcción music.extend

- **Descripción**: Validar final/punto, letra/style efectivos y respuesta completa/región del modelo. Componer conforme schema, sin crossfade automático no pedido; maps keep/extend efectivos.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-03/T-06/T-07; ACE/T-09 liberado, gate extend real T-27
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_creative_extend.py`, `apps/server/app/creative/derivations.py`, `apps/server/tests/test_creative_extend.py`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-04, E2E-12, M-03
- **Criterios spec**: CA-09, CA-13, CA-16, CA-20, CA-21
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_extend.py` → focal server pasa · `docker compose run --rm --no-deps engine-acestep uv run pytest -m "not gpu" -q tests/test_creative_extend.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Inicio/final, límites y NaN no duplican piezas; duration/map desde samples medidos.
- [ ] Unknown response shape no publica; capacidad queda false hasta conformidad real/escucha.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-09, CA-13, CA-16, CA-20, CA-21. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-13 — Adapter y construcción music.repaint

- **Descripción**: Inputs y región capturados, letra/style opcionales resueltos antes de inferencia. Contrato completo/región; maps conservadas/regeneradas medidos y fidelidad keep conforme T-08 cuando se ensambla CPU.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-03/T-06/T-07; ACE/T-09 liberado, gate repaint real T-27
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_creative_repaint.py`, `apps/server/app/creative/derivations.py`, `apps/server/tests/test_creative_repaint.py`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-05, E2E-12, M-03
- **Criterios spec**: CA-11, CA-13, CA-16, CA-20, CA-21
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_repaint.py` → focal server pasa · `docker compose run --rm --no-deps engine-acestep uv run pytest -m "not gpu" -q tests/test_creative_repaint.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Las partes conservadas no se regeneran por accidente ni falsifican keep ante respuesta completa distinta.
- [ ] Padre íntegro y controles por descriptor; continuidad musical pendiente escucha real.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-11, CA-13, CA-16, CA-20, CA-21. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-14 — Adapter y cadena music.cover

- **Descripción**: Source/style propios y filiación cover; no imagen. Fidelidad disponible solo schema/feature verificados; no inventar escala ni soporte público desde parámetro interno.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-06/T-07; ACE/T-09 liberado, gate cover real T-27
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_creative_cover.py`, `apps/server/app/creative/derivations.py`, `apps/server/tests/test_creative_cover.py`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-06, E2E-12, M-03
- **Criterios spec**: CA-12, CA-16, CA-20, CA-21
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_cover.py` → focal server pasa · `docker compose run --rm --no-deps engine-acestep uv run pytest -m "not gpu" -q tests/test_creative_cover.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] feature false retira control y rechaza parámetro; verified false no envío.
- [ ] Origen/style/seed reales y derechos en nuevo hijo; prueba de fidelidad estilística pendiente.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-12, CA-16, CA-20, CA-21. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

## Fase 4 — Texto local y providers

**Estado**: borrador · **Estimado**: 100h base · **Real**: — · **Coste est.**: 10.89 € informativo · **Tokens est.**: 1480000

### T-15 — Adaptador LLM /v1 y cliente Ollama controlado

- **Descripción**: Autenticación engine, load/unload/estimate/jobs/event replay/delta y terminal único, cancelación/timeouts, salida cruda texto privada. Cliente HTTP sustituible CPU sin lanzar Ollama. No CUDA propio/BD/cloud/otro almacén. Model descriptor honestamente false hasta T-28.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-04; nuevos módulos propios CPU; common solo tras liberación
- **Tipo**: backend
- **Archivos**: `apps/engines/llm/`, `apps/engines/common/engine_common/server.py` (si exige hook), `packages/engine-contract/engine_contract/__init__.py` (solo ampliaciones opcionales necesarias), `packages/contracts/engine-v1.json`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/iteracion-creativa.md`, `docs/legal/licencias.md`
- **Cubre (tests)**: E2E-02, M-04, M-08
- **Criterios spec**: CA-22, CA-23, CA-29
- **Verificación**: `uv run pytest -q apps/engines/llm/tests/test_contract.py apps/engines/llm/tests/test_client.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Falso servidor Ollama prueba parsing streaming/backpressure y terminal único; no equivale a red WSL.
- [ ] Revisión/licencia del cliente/runtime registradas; unload delegado no usa ProcessSupervisor como prueba suficiente.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-22, CA-23, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-16 — Recibo durable y recovery de residencia compartida

- **Descripción**: Recibo privado durable en data/residency/<execution_id>/ con owner/observación nombre+revision/VRAM/intervención/resultados/state y hashes, CAS propio. Timeout observación5s, descarga/carga120s configurables, muestreo1s sin inventar métrica desconocida. NVML real mediante control autorizado; no setting como mutex global. UNKNOWN/reinicio re-observa y bloquea nuevo turno/restauración hasta reconciliar.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 9h (estimado) · real —
- **Supervisión**: est. 2.25h (25 % IA) · real —
- **Previsión IA**: 270000 in / 90000 out tok · 2.65 € informativo
- **Dependencias**: T-15; módulo nuevo independiente, wiring dispatcher M1 liberado más tarde
- **Tipo**: backend
- **Archivos**: `apps/server/app/creative/residency.py`, `apps/server/app/creative/residency_receipts.py`, `apps/server/tests/test_creative_residency.py`, `apps/engines/llm/runtime.py`, `apps/engines/llm/tests/test_residency.py`, `docs/arquitectura/iteracion-creativa.md`, `docs/arquitectura/contrato-engines.md`
- **Cubre (tests)**: E2E-11, M-04
- **Criterios spec**: CA-24, CA-30
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_residency.py apps/engines/llm/tests/test_residency.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Restore solo observados realmente descargados, después unload propio/VRAM compatible; estado inicial vacío permanece vacío.
- [ ] Recarga ajena genera espera/error; no stop service/delete model ni cargas paralelas; pruebas crash en cada frontera.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-24, CA-30. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-17 — Integración Compose y carril LLM local

- **Descripción**: Servicio adaptador y destino Ollama lista cerrada configurado después de probe privado; host ports127.0.0.1 sin LAN. Runtime offline, pesos solo propios verificados. Coordinar música también con residentes ajenos. Tests config CPU no afirman Compose real.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-15/T-16; liberar Compose/settings/runtime/dispatcher M1; red real T-28
- **Tipo**: devops
- **Archivos**: `docker-compose.yml`, `.env.example`, `apps/server/app/settings.py`, `apps/server/app/queue/dispatcher.py`, `apps/server/app/queue/runtime.py`, `apps/server/tests/test_creative_llm_wiring.py`, `apps/engines/llm/Dockerfile`, `docs/arquitectura/entorno.md`, `docs/arquitectura/sistema.md`, `docs/arquitectura/diagramas.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: E2E-01, E2E-11, M-04
- **Criterios spec**: CA-23, CA-24, CA-25
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_llm_wiring.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Config no revela clave ni permite URL arbitraria; remote default false/no fallback.
- [ ] T-28 acredita Docker→WSL y VRAM; este test wiring no cierra CA23/24.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-23, CA-24, CA-25. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-18 — Acciones del asistente y aceptación versionada

- **Descripción**: Generar, reescribir sección, continuar, tono y estructura. Deltas borrador; terminal validado produce propuesta sin música. Captura texto/base/rev/style/idioma/tags; reescribir conserva exterior byte/texto esperado. Aceptar con If-Match crea LyricsVersion parent/source assistant/autoría; instrumental no borra texto.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 9h (estimado) · real —
- **Supervisión**: est. 2.25h (25 % IA) · real —
- **Previsión IA**: 270000 in / 90000 out tok · 2.65 € informativo
- **Dependencias**: T-06/T-15/T-17; lyrics/domain/SSE M1 liberados
- **Tipo**: backend
- **Archivos**: `apps/server/app/creative/text_assistance.py`, `apps/server/app/lyrics.py`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/app/queue/chains.py`, `apps/server/tests/test_text_assistance.py`, `packages/contracts/lyrics-cases.json`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `docs/arquitectura/iteracion-creativa.md`, `docs/arquitectura/datos.md`
- **Cubre (tests)**: E2E-01, E2E-02, E2E-11
- **Criterios spec**: CA-02, CA-03, CA-04, CA-05, CA-06, CA-22, CA-25
- **Verificación**: `uv run pytest -q apps/server/tests/test_text_assistance.py apps/server/tests/test_lyrics.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Todos cinco modos validan etiquetas; fallos/truncado/tag inválido preservan letra;409 no pisa concurrente.
- [ ] Cancelación y reconnect conservan seq/terminal único; desconectar SSE no cancela ni genera música.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-02, CA-03, CA-04, CA-05, CA-06, CA-22, CA-25. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-19 — Proveedores por función y coste previo

- **Descripción**: Registry+adapter interface server-side; remote apagado por función. No API música. Require verified/enabled/key/estimación fiable vigente y confirmación request/coste antes envío; reject unknown cost. Test adapter sintético sin red prueba provenance model/request_id/cost y sanitización. Ausente adapter real queda disabled; no seleccionar proveedor durante M2.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-06; provider/settings/domain M1 liberados; no proveedor concreto seleccionado
- **Tipo**: backend
- **Archivos**: `apps/server/app/providers/`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/app/settings.py`, `apps/server/tests/test_provider_preflight.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `.env.example`, `docs/arquitectura/iteracion-creativa.md`, `docs/arquitectura/datos.md`, `docs/seguridad/providers.md`
- **Cubre (tests)**: E2E-10, E2E-12, M-06
- **Criterios spec**: CA-25, CA-26, CA-27, CA-28, CA-29
- **Verificación**: `uv run pytest -q apps/server/tests/test_provider_preflight.py` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Claves solo env server, sin config/log/URL/DTO/manifiesto/engine/browser; fallo local jamás fallback.
- [ ] CA27 real es condicional a integrar proveedor autorizado, no prerequisite contratar API; registry disabled satisface alcance sin fingir llamada real.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-25, CA-26, CA-27, CA-28, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

## Fase 5 — Interfaz creativa

**Estado**: borrador · **Estimado**: 120h base · **Real**: — · **Coste est.**: 12.07 € informativo · **Tokens est.**: 1640000

### T-20 — Modo simple y editor de propuestas

- **Descripción**: Descripción/idioma/instrumental/duración y letra/style editables. Acciones por sección y propuesta comparar/aceptar/descartar; autoría explícita aplicable. SSE real no timers progreso. Inputs previos instrumental intactos, teclado/foco/anuncios next-intl.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 8h (estimado) · real —
- **Supervisión**: est. 2h (25 % IA) · real —
- **Previsión IA**: 240000 in / 80000 out tok · 2.36 € informativo
- **Dependencias**: T-18; liberar create/LyricsEditor/lib/messages M1
- **Tipo**: frontend
- **Archivos**: `apps/web/app/create/page.tsx`, `apps/web/components/LyricsEditor/LyricsEditor.tsx`, `apps/web/components/LyricsEditor/LyricsEditor.test.tsx`, `apps/web/lib/lyrics.ts`, `apps/web/lib/lyrics.test.ts`, `apps/web/lib/api.ts`, `apps/web/messages/es.json`, `apps/web/e2e/creative-text.spec.ts`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-01, E2E-02, E2E-11, M-07
- **Criterios spec**: CA-02, CA-03, CA-04, CA-05, CA-06, CA-22, CA-31
- **Verificación**: `pnpm --dir apps/web test components/LyricsEditor/LyricsEditor.test.tsx lib/lyrics.test.ts; pnpm --dir apps/web typecheck` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] No auto-genera al terminar texto ni aceptar; instrumental preserves letra no exige declaración.
- [ ] Errores/tags/409/desconexión visibles y versiones recuperables; pruebas teclado.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-02, CA-03, CA-04, CA-05, CA-06, CA-22, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-21 — Región, bucle y controles de derivación musical

- **Descripción**: Región editable en segundos por arrastre y teclado, loop, snap beats solo reales, snap sections solo boundaries reales. Variación request/source distintas, extensión final/punto, repaint, cover/style/features según descriptor.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 8h (estimado) · real —
- **Supervisión**: est. 2h (25 % IA) · real —
- **Previsión IA**: 240000 in / 80000 out tok · 2.36 € informativo
- **Dependencias**: T-10..T-14; Waveform/song/lib M1 liberados; gates reales siguen falsos hasta T-27
- **Tipo**: frontend
- **Archivos**: `apps/web/components/Waveform.tsx`, `apps/web/components/Waveform.test.tsx`, `apps/web/components/CreativeOperations.tsx`, `apps/web/components/CreativeOperations.test.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/lib/api.ts`, `apps/web/messages/es.json`, `apps/web/e2e/creative-music.spec.ts`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-03, E2E-04, E2E-05, E2E-06, E2E-12, M-03, M-07
- **Criterios spec**: CA-07, CA-08, CA-09, CA-10, CA-11, CA-12, CA-13, CA-20, CA-31
- **Verificación**: `pnpm --dir apps/web test components/Waveform.test.tsx components/CreativeOperations.test.tsx; pnpm --dir apps/web typecheck` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Intervalo vacío/NaN/out-of-duration no se envía; cap false muestra motivo y API sigue rechazo.
- [ ] source y petición elegida explicitados; fidelidad sin escala inventada; next-intl/foco/estado.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-07, CA-08, CA-09, CA-10, CA-11, CA-12, CA-13, CA-20, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-22 — Edición CPU y crossfade de dos padres

- **Descripción**: UI recorte/fade-in/out y crossfade con dos takes de canción; muestra nuevos hijos y no auto-promoción. Validación de límites y nombres de operaciones.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-08; song/Waveform M1 liberados
- **Tipo**: frontend
- **Archivos**: `apps/web/components/AudioEditForm.tsx`, `apps/web/components/AudioEditForm.test.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/lib/api.ts`, `apps/web/messages/es.json`, `apps/web/e2e/creative-edits.spec.ts`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-07, E2E-11, M-01, M-07
- **Criterios spec**: CA-13, CA-14, CA-15, CA-16, CA-31
- **Verificación**: `pnpm --dir apps/web test components/AudioEditForm.test.tsx; pnpm --dir apps/web typecheck` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Recibe duración efectiva/mapas y presenta ambos padres; fallo/clipping no oculta rechazo.
- [ ] Teclado y foco/error en castellano; padre/master siguen iguales al reload.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-13, CA-14, CA-15, CA-16, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-23 — Árbol multipadre y procedencia navegables

- **Descripción**: Consultar aristas reales con propiedad y límites/paginación; representar DAG con crossfade ambos parents/roles/root, operación y maestro. Nodo abre audio/provenance; promover solo endpoint explícito.
- **Estado**: borrador
- **Tiempo humano**: est. 20h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 7h (estimado) · real —
- **Supervisión**: est. 1.75h (25 % IA) · real —
- **Previsión IA**: 210000 in / 70000 out tok · 2.06 € informativo
- **Dependencias**: T-05/T-06; endpoints/song page M1 liberados
- **Tipo**: frontend
- **Archivos**: `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `apps/server/tests/test_creative_lineage_tree.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`, `apps/web/components/VersionTree.tsx`, `apps/web/components/VersionTree.test.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/creative-tree.spec.ts`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-08, E2E-11, M-07
- **Criterios spec**: CA-16, CA-17, CA-29, CA-31
- **Verificación**: `uv run pytest -q apps/server/tests/test_creative_lineage_tree.py; pnpm --dir apps/web test components/VersionTree.test.tsx` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Reload conserva relaciones/maestro y permisos; ningún árbol inventado single-parent.
- [ ] CPU muestra tools reales y antecedentes separados, sin modelo ficticio; navegación teclado.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-16, CA-17, CA-29, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-24 — Transporte A/B y compatibilidad decoder

- **Descripción**: Dos audios precargados un audible, reloj absoluto común hasta min(duration). Probar WAV PCM24 decoder Chromium antes render; si no soporta resolver formato sin pérdida en gate documentado, sin fallback MP3. Política preliminar drift≤50ms/alternancia≤150ms después preload, medir real antes fijar thresholds finales y no aflojarlos para tapar fallo.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 8h (estimado) · real —
- **Supervisión**: est. 2h (25 % IA) · real —
- **Previsión IA**: 240000 in / 80000 out tok · 2.36 € informativo
- **Dependencias**: T-09; PlayerContext/Dock/Waveform M1 liberados; prueba audio real T-29
- **Tipo**: frontend
- **Archivos**: `apps/web/components/ComparisonPlayer.tsx`, `apps/web/components/ComparisonPlayer.test.tsx`, `apps/web/components/PlayerContext.tsx`, `apps/web/components/PlayerDock.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/creative-comparison.spec.ts`, `apps/web/e2e/fixtures/comparison/`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-09, E2E-11, M-02, M-07
- **Criterios spec**: CA-18, CA-19, CA-30, CA-31
- **Verificación**: `pnpm --dir apps/web test components/ComparisonPlayer.test.tsx; pnpm --dir apps/web typecheck` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] No promete alineación musical; fin común para, loading/error visible y no superposición.
- [ ] Audio servido corresponde preview medido; latencia/clicks/pausas requieren M-02 real.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-18, CA-19, CA-30, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-25 — Ajustes de providers y disponibilidad

- **Descripción**: Activar función con adapter real disponible, estado key/coste preflight y confirmación; no textbox clave almacenada. Provider ausente/unverified/unknown coste disabled con motivo; música solo local.
- **Estado**: borrador
- **Tiempo humano**: est. 12h · real — · confianza Media
- **Tiempo IA (ejec.)**: est. 4h (estimado) · real —
- **Supervisión**: est. 1h (25 % IA) · real —
- **Previsión IA**: 120000 in / 40000 out tok · 1.18 € informativo
- **Dependencias**: T-19; system/messages/lib M1 liberados
- **Tipo**: frontend
- **Archivos**: `apps/web/app/system/page.tsx`, `apps/web/components/ProviderSettings.tsx`, `apps/web/components/ProviderSettings.test.tsx`, `apps/web/lib/api.ts`, `apps/web/messages/es.json`, `apps/web/e2e/creative-providers.spec.ts`, `docs/producto/ux.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-10, E2E-12, M-06, M-07
- **Criterios spec**: CA-25, CA-26, CA-27, CA-28, CA-31
- **Verificación**: `pnpm --dir apps/web test components/ProviderSettings.test.tsx; pnpm --dir apps/web typecheck` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Cambiar función no activa otras; runtime offline/fallo local no envía remote.
- [ ] Secretos no DOM/devtools/URL; keyboard y foco; no solicitud cloud durante QA sintética.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-25, CA-26, CA-27, CA-28, CA-31. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

## Fase 6 — QA y aceptación real

**Estado**: borrador · **Estimado**: 128h base · **Real**: — · **Coste est.**: 10.30 € informativo · **Tokens est.**: 1400000

### T-26 — E2E reproducibles y puertas técnicas por fase

- **Descripción**: QA fresco Playwright en Compose local con mock explícitamente sintético; fixtures propietarios. Ejecutar rechazo de cada flujo, TDD/reviews A/B+C/D auto y cobertura cambiada80% por fase. Gates no esperan última tarea para revisar código; snapshots y recibos propios.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Baja
- **Tiempo IA (ejec.)**: est. 9h (estimado) · real —
- **Supervisión**: est. 2.25h (25 % IA) · real —
- **Previsión IA**: 270000 in / 90000 out tok · 2.65 € informativo
- **Dependencias**: T-04..T-25; Compose CPU aislado y seams liberados; no interferir T-09
- **Tipo**: test
- **Archivos**: `apps/web/e2e/creative-*.spec.ts`, `apps/server/tests/test_creative_*.py`, `apps/engines/mock/tests/test_creative_mock.py`, `apps/engines/mock/engine_mock/` (si requiere descriptor sintético), `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08, E2E-09, E2E-10, E2E-11, E2E-12, M-08
- **Criterios spec**: CA-20, CA-25, CA-28, CA-29, CA-30, CA-31, CA-32
- **Verificación**: `pnpm --dir apps/web exec playwright test e2e/creative-text.spec.ts e2e/creative-music.spec.ts e2e/creative-edits.spec.ts e2e/creative-tree.spec.ts e2e/creative-comparison.spec.ts e2e/creative-providers.spec.ts; uv run python scripts/export_contracts.py --check` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Todos E2E positivos/negativos pasan y mocks no cambian descriptors reales; manifiesto/TS/OpenAPI sincronizados.
- [ ] Informe separa CPU/mock/real/manual pendiente; no cerrar unidad con criterios pendientes, sin omisiones que oculten falta de integración.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-20, CA-25, CA-28, CA-29, CA-30, CA-31, CA-32. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-27 — Conformidad real musical por operación

- **Descripción**: Crear primero runner/receipt parser TDD CPU; ejecutar después audio real retake/extend final+punto/repaint/cover por separado, pesos/pins/hash/licencias/inputs propios. Medir duración/maps/fidelidad keep y revisar continuidad/estilo por escucha; registrar fallo honesto, no forzar verified.
- **Estado**: borrador
- **Tiempo humano**: est. 32h · real — · confianza Baja
- **Tiempo IA (ejec.)**: est. 8h (estimado) · real —
- **Supervisión**: est. 2h (25 % IA) · real —
- **Previsión IA**: 240000 in / 80000 out tok · 2.36 € informativo
- **Dependencias**: T-10..T-14/T-21/T-26; liberar T-09/GPU, M0 elección válida y seams aceptados; escucha humana
- **Tipo**: test
- **Archivos**: `scripts/eval/creative_music.py`, `scripts/eval/tests/test_creative_music_plan.py`, `eval/m2/ (privado)`, `apps/engines/acestep/descriptor.py`, `docs/arquitectura/modelos.md`, `docs/arquitectura/contrato-engines.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/music-conformance.md`
- **Cubre (tests)**: M-03, M-05
- **Criterios spec**: CA-07, CA-08, CA-09, CA-11, CA-12, CA-20, CA-21, CA-29
- **Verificación**: `uv run python scripts/eval/creative_music.py --check-receipts --report eval/m2/music/index.json` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Cada task/feature verified solo tras recibos reales y escucha conforme; falta una operación deja gate y M2 abiertos.
- [ ] No sobrescribir padres ni matriz T-09; informe sanitizado no contiene letras/data privadas.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-07, CA-08, CA-09, CA-11, CA-12, CA-20, CA-21, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-28 — Modelo LLM y despliegue/residencia reales

- **Descripción**: Selección local comparada sin ganador supuesto: al menos20 prompts españoles/10 idioma alternativo declarado, cinco acciones/tags/reescritura exterior, latencia p50/p95 medida, cancelación, VRAM libre/pico y licencia comercial. Registrar revisión/hash/pesos propios GGUF o formato seguro, no nombre histórico como evidencia. Conectar Docker→WSL y alternar LLM/música con recibos vacíos/ocupados/recarga ajena/reinicio.
- **Estado**: borrador
- **Tiempo humano**: est. 32h · real — · confianza Baja
- **Tiempo IA (ejec.)**: est. 8h (estimado) · real —
- **Supervisión**: est. 2h (25 % IA) · real —
- **Previsión IA**: 240000 in / 80000 out tok · 2.36 € informativo
- **Dependencias**: T-15..T-18/T-26; T-09 libera GPU, endpoint privado aprobado y modelos seleccionados/pins/licencias; no descarga runtime
- **Tipo**: test
- **Archivos**: `scripts/eval/creative_text.py`, `scripts/eval/tests/test_creative_text_plan.py`, `eval/m2/ (privado)`, `models/models.lock.json`, `scripts/fetch_models.py`, `apps/engines/llm/descriptor.py`, `docs/legal/licencias.md`, `docs/arquitectura/modelos.md`, `docs/arquitectura/entorno.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/llm-conformance.md`
- **Cubre (tests)**: M-04, M-05
- **Criterios spec**: CA-04, CA-22, CA-23, CA-24, CA-25, CA-29
- **Verificación**: `uv run python scripts/eval/creative_text.py --check-receipts --report eval/m2/text/index.json; uv run python scripts/eval/creative_text.py --check-model-lock --report eval/m2/text/index.json` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] 100% etiquetas válidas en corpus contractual y conservación exterior exacta; calidad/idioma juzgada humana, latencia reportada sin umbral ficticio.
- [ ] Unload real ausencia+VRAM, restauración exacta solo own list; no LAN/servicio stop/borrado/otro modelstore. Network y VRAM nunca acreditados por mock.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-04, CA-22, CA-23, CA-24, CA-25, CA-29. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-29 — Audio real, replay persistente y escucha A/B

- **Descripción**: Clips controlados distintos LUFS, transitorios/clipping, formatos mixtos, silencio/<3s y hash baseline; medir previews servidas, TruePeak/PCM/drift/switch. Edit real/render y replay en persistencia correcta, kill own child/rollback/restart/readers/cache inval.
- **Estado**: borrador
- **Tiempo humano**: est. 24h · real — · confianza Baja
- **Tiempo IA (ejec.)**: est. 6h (estimado) · real —
- **Supervisión**: est. 1.5h (25 % IA) · real —
- **Previsión IA**: 180000 in / 60000 out tok · 1.77 € informativo
- **Dependencias**: T-08/T-09/T-24/T-26; M1 ext4/VHDX aceptado, audios propios y persona escucha
- **Tipo**: test
- **Archivos**: `scripts/eval/creative_audio.py`, `scripts/eval/tests/test_creative_audio_plan.py`, `eval/m2/ (privado)`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/audio-conformance.md`, `docs/guias/iteracion-creativa.md`
- **Cubre (tests)**: M-01, M-02, M-05
- **Criterios spec**: CA-14, CA-15, CA-16, CA-18, CA-19, CA-29, CA-30
- **Verificación**: `uv run python scripts/eval/creative_audio.py --check-receipts --report eval/m2/audio/index.json` → todas las pruebas focales pasan (conteo real registrado al ejecutar)

**Criterios de aceptación**

- [ ] Diferencia≤0,5LU, truepeak≤−1dBTP sobre salida servida; sin limiter ni ganancia positiva; masters/manifests iguales.
- [ ] Keep/convert/maps tolerancias T-08 y escucha unión/clicks/uso A/B conformes; tmpfs diagnóstico nunca persistent acceptance.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-14, CA-15, CA-16, CA-18, CA-19, CA-29, CA-30. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.

### T-30 — Aceptación M2, trazabilidad y cierre documental

- **Descripción**: Orquestador verifica gates reales y ledger; QA fresh, documenter/changelog-sync/retro con misma fuente canónica. No cerrar M2 con mock ni declaraciones de capacidad; M1 sigue hoy0/17 cerrado. Documentar cada operación y disponibilidad, límites y provider absent.
- **Estado**: borrador
- **Tiempo humano**: est. 16h · real — · confianza Baja
- **Tiempo IA (ejec.)**: est. 4h (estimado) · real —
- **Supervisión**: est. 1h (25 % IA) · real —
- **Previsión IA**: 120000 in / 40000 out tok · 1.18 € informativo
- **Dependencias**: Todas tareas y CA; M1 cerrado+30 generaciones propias reales+M0/T-13 cerrado+escucha humana
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/final-report.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/improvement-plan.md`, `docs/roadmap/README.md`, `docs/README.md`, `docs/RAG-INDEX.md`, `docs/guias/iteracion-creativa.md`, `docs/producto/funcionalidades.md`, `docs/producto/ux.md`, `CHANGELOG.md`, `docs/knowledge/candidates/pending/`, `docs/roadmap/2026-10-10-m2-iteracion-creativa/retro.md`
- **Cubre (tests)**: M-03, M-04, M-05, M-07, M-08
- **Criterios spec**: CA-01, CA-21, CA-23, CA-24, CA-29, CA-31, CA-32
- **Verificación**: lectura: matriz CA-01..CA-32 con recibos+hashes+terminales y escucha; ledger-lint/coverage-check exit 0; cierre documental por orquestador → acta y compatibilidad revisadas por el orquestador

**Criterios de aceptación**

- [ ] 32/32 CA acreditados o rama opcional explicitly n/a con motivo autorizado; CA01/21/23/24/19 jamás n/a.
- [ ] M1/M0 y30 propias comprobadas, sin sintéticas; final report evidencia manual separada y aceptación humana, ningún falso completado.
- [ ] Verificación propia ejecutada, evidencia entregada y puertas de revisión/QA de la unidad conformes. Un requisito real pendiente impide completado.

**Subtareas**

- [ ] Releer seam/contratos actuales y acordar ownership; test RED antes de implementar, o TDD n/a: prosa para documento.
- [ ] Implementar alcance descrito y casos negativos; actualizar documentos/copies generadas declaradas cuando aplique.
- [ ] Verificar, medir sin inventar reales y entregar recibos al orquestador para revisión fresh y QA.

**Notas**: CA-01, CA-21, CA-23, CA-24, CA-29, CA-31, CA-32. El detalle técnico y los gates no se reducen a los escenarios sintéticos. Coste informativo a tarifa 0 €/h; in/out multiplican precios guardados, no un coste real.




## Aprobación del plan e inicio T-01 — 2026-10-10

El orquestador contrasta diez funcionalidades y 32 CA contra la spec aprobada y conserva todas las puertas reales. Plan aprobado bajo delegación; T-01 pasa a en-progreso, TDD n/a: prosa. Ledger-lint 0 incoherencias/0 avisos, exit 0; coverage-check 0 referencias rotas y 24/24 GWT cubiertos, exit 0. Se retira una ruta personal del comando de contrato y se usa resolución local de <plugin>. No se afirma ejecución de las restantes 29 tareas ni cierre de M1/M2. Architect fresco compara opciones antes de fijar la representación CPU; no se autoriza aún una migración.

## Revisión de dos lentes — intento 1: M2 T-01 contrato CPU — un Important

Lentes A+B; C/D no aplican según selector oficial (13 documentos, ningún motivo). Scope sobre snapshot de preimágenes exactas de esta unidad: exit0, 13 en alcance, cero fuera/excluidos/avisos. No gate global del checkout. A: conformidad contractual y documentos sincronizados; aceptación ADR/QA final aún pendientes, ninguna tarea cerrada. B leyó diff completo y verificó 13 hashes documentales y once fuentes de la sonda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important | cpu-contract-design.md:158 exige SHA de salida diferente de los padres; un fade válido en silencio conserva bytes y SHA. | T-01 | Pendiente: exigir ejecución propia/ID/asset/hash verificado, sin desigualdad de contenido. Architect corrige fila antes de revisión 2. | RAM4s, intro1s muda/tono3s, fade0,5s: arrays y dos codificaciones FLAC PCM24 iguales; SHA b85506512c94e6b174e7ae083ae3f2c624971cae79138994af018b78822a7a0d. Root cotejó fila y CA14/CA16; gap confirmado. |

Evidencia `.cache/dev-cycle/m2/t01-cpu-contract-20261010/source.diff`, source-receipt.json, scope-receipt.json, lenses-receipt.json y sondas architect. TDD n/a: prosa; cobertura de producto/interop/OpenAPI real n/a. Veredictos contractuales no acreditan migración, render, API o GPU implementados. T-01 en-progreso, ADR propuesta; corrección y revisión fresca antes de QA.
## Revisión de dos lentes — intento 2: M2 T-01 contrato CPU — sin gaps pendientes

Lentes A+B frescas; C/D n/a (selector documental sin motivos). Diff13documentos en alcance sin exclusiones/avisos. Delta respecto intento1: dos aclaraciones en diseño y notasledger; veredictos aprobados conservados, no reabiertos. A y B comprobaron 13 hashes actuales y leyeron delta completo; B reprodujo RAM fade0,5s en intro muda de audio4s con arrays/bytesFLACPCM24/SHA iguales.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important anterior | Desigualdad SHA obligatoria rechazaba fundidos válidos sobre silencio. | T-01 | Corregido: diseño:158 permite coincidencia, :164 exige ejecución/Take/asset/IDs/custodia propios; igualdad no acredita autoridad. | architect/fix1/prose-fix.diff y receipt; review2/source-receipt.json13/13; reproducción B2RAM SHA bd661ec40fb1029855d9676f3e52b41c596ea94e0aa2743f3265705b54d001b9. |

Criterios contractuales identidad/guardas/NULLunicidad/backups/historia/API/previews/UNKNOWN/Constitución/CA29/CA32 conformes; aceptación ADR y QA final pendientes. Fuente diseño e42933ff343b6f0e4a4475088bb55b90588f6250cd81753a94f1c3ad7c3e05c9. Ledger-lint de A exit0 0incoherencias/0avisos. TDD n/a: prosa; no cobertura de producto/GPU/migración atribuida. T-01 sigue abierta hasta QA y aceptación root; ADR propuesta.
## QA y cierre contractual — T-01 — 2026-10-10

PASS documental16/16, gate0; 201 enlaces locales/0rotos, 13 documentos y11 fuentes estables. Ledger-lint0 incoherencias/0avisos, coverage-check0rotas/24GWT declarados, candidatoAPIaditivo0 y negativoM1nullable1 esperado. Inventario23 y sources13 verificados por root; informe testing/t01/contract-qa-2026-10-10.md. Tras revisión2 A/B sin gaps, root acepta ADR0074 y documentos, marca T-01 completada y conserva todas las puertas de producto. No cierre M-08 integral, M1/M2, migración/API/render/GPU ni calidad. Promoción cambia únicamente estados/acta, sin ampliar decisiones aprobadas.


## Inicio T-02: recetas privadas CPU independientes ? 2026-10-11T10:38:20.945968+00:00

Commit/push 67e1f09fae4d2d2b1931dc66c0e349f3938fe270 verificado en origin/m1/t-02-esquema; siete ficheros aceptados(runtime/tests/reviews1?3/QA1?2), index vac?o. Sin stageglobal, checkout, mainmerge ni otros cambios pendientes incorporados. M1/T05 siguen abiertos.

M2/T02 pas? aen-progreso conforme dependenciaT01yADR0037; briefdeterminista f283d133 generadoexit0(warning tama?o conservado). Actor fresco implement_m2_t02_recipes posee s?lo cuatroficheros declarados+evidencia propia. MarkerROOT activo m2/T02-recetas-privadas; QA2U2b1cerrado. No aceptaci?nM2 ni30generaciones fingidas, ning?nmodeloGPUcargado. Geometr?aT05U2b2 a?npropuesta, constantesNT primarias verificadasen .cache/dev-cycle/m1/storage-u2b-contract-refinement-20261011/, noADRratificado/implementaci?n.


## T-02: contexto previo al RED en concreci?n ? 2026-10-11T10:40:29.472328+00:00

Implementerfresco devolvi? NEEDS_CONTEXT justificado, fuentesintactas/noRED/no c?digo: CPUdesign exige fijarDTO/envelope/readersantesRED. Actorarchitectfresco design_m2_t02_recipe_contract trabaja s?lo propuestaen .cache/dev-cycle/m2/creative-recipes-t02-contract-20261011/, opciones+contratocerrado. ROOT escoger? bajo delegaci?ndelpropietario y ratificar? antes?nicoredispatch. No solicitud alhumano ausente ni bloqueo delobjetivo, T02en-progreso/M2noaceptado. Marker?nicoROOTm2/T02-recetas-privadas incluyeconcreci?ncontractual; m?tricasrealesnull. U2b1aceptado/push67e1f09 siguevigente, M1noaceptado.


## T-02: enfoque contractual elegido antes del RED — 2026-10-11T10:47:43.789905+00:00

ROOT elige O1 bajo la delegación del propietario: envelope privado exclusivo y versionado en `job.request`, con proyección explícita a la petición de engine. O2 (sidecar junto a params/inputs) se descarta por doble autoridad; O3 (registro de recetas separado) añade persistencia fuera de T-02. Es la elección del enfoque; los campos del DTO y sus reglas aún no están ratificados.

El arquitecto fresco `design_m2_t02_recipe_contract` continúa la segunda pasada exclusivamente privada en `.cache/dev-cycle/m2/creative-recipes-t02-contract-20261011/`. ROOT capturó y verificó 19 autoridades actuales, incluidas chains/resolver y ADR-0073/0074, en `.cache/dev-cycle/m2/creative-recipes-t02-contract-review1-20261011/authority-capture-root.receipt.json`. Legacy conservará sus formas reales (post.audio sin params, beats con params vacío), sin defaults inventados ni reescritura de históricos. El lector nuevo no acreditará admisión ni ejecución por la presencia de receta/hash.

TDD n/a: selección y preparación documental. No hay RED ni código de recetas; el único re-despacho del implementer espera el contrato completo. T-02 en-progreso, M2 no aceptado y M1 sigue abierto. Marcador único ROOT `m2/T02-recetas-privadas`; tokens, euros y horas IA reales no disponibles. Sin GPU, modelos, servicios ni cambios de datos.


**Concreción contractual T-02 (ROOT):** el alcance incluye diseño de receta, ADR y sus enlaces/índice antes del RED; no modifica código M1 ni anticipa ejecución/publicación. La propuesta se revisa en un snapshot privado antes de adoptarse.


## Revisión de dos lentes — intento 1: T-02 contrato de recetas — cuatro Important pendientes

ROOT 2026-10-11T11:03:44.243356+00:00: A+B sobre cuatro documentos; C/D auto false. Scope oficial 4 en alcance, 0 fuera/avisos/exclusiones de usuario. Revisión sólo documental, no producto. [Informe](testing/t02/recipe-contract-review1-2026-10-11.md).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Links frontmatter fuera del destino | T-02 | pendiente | recipe-contract-design:7/9/10; rutas no existentes |
| A02 | Important | Mapa solicitado contradice mapa efectivo del diseño | T-02 | pendiente | design:153 vs recipe-contract-design:278/292; Constitución:73 |
| B01 | Important | Capturador M1 contradice política de schema M2 | T-02 | pendiente | _json_guard substring token; nueva política igualdad/namespaces |
| B02 | Important | Proyección no comprueba inputs del descriptor | T-02 | pendiente | source FLAC vs descriptor WAV; resolver:328–341 |
| A03 | Minor | Tres reglas de secreto en una frase | T-02 | pendiente | docs-style regla1; recipe-contract-design:365 |

T-02 en-progreso, contrato sin ratificar y ningún RED/código escrito. ROOT confirma los gaps; no rebates/deuda ni cierre. Originales y fuentes congeladas intactos. FIX documental conservará M1 y sincronizará el diseño global, declarando esa ruta antes del nuevo scope. Revisión cerrada antes de abrir marcador de FIX; valores reales de tokens/eur/horas no disponibles.


**FIX1 contractual T-02 (ROOT):** el alcance incorpora también `design.md` para corregir A02 en el mismo cambio, según Constitución §2. Mantiene O2 global y distingue intenciones capturadas de mapas efectivos de ejecución; no adelanta render/publicación.


## Revisión de dos lentes — intento 2: T-02 contrato de recetas — sin gaps pendientes

ROOT 2026-10-11T11:22:01.942969+00:00: A+B frescos, cinco docs en alcance,0fuera/avisos/exclusiones; C/Dauto false. [Informe completo con tablas A21/B8](testing/t02/recipe-contract-review2-2026-10-11.md).

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Links frontmatter fuera destino | T02 | corregido | recipe7/9/10; overlay y destinos |
| A02 | Important | Mapas efectivos dentro receta sellada | T02 | corregido | global153/recipe311/ADR30 |
| B01 | Important | Guard substring M1 contra schema M2 | T02 | corregido documentalmente | capturador nuevo aislado235/248/250/252 |
| B02 | Important | Inputs proyectados incompatibles | T02 | corregido documentalmente | roles/required/media336/338/340/342 |
| A03 | Minor | Tres reglas en frase única | T02 | corregido | reglas394/395/396 |

0Critical/Important/Minor pendientes; sin rebates/deuda. TDD n/a prosa; sin código/RED ni Verificación producto. T02 permanece en-progreso; QA documental y ratificación ROOT pendientes. Ledger0incoherencias/29avisos Changelog abiertos. Fuentes M1 intactas y M1 NO-VERDE. Métricas reales null; reloj no mide IA.


## T-02: contrato ratificado antes del RED — 2026-10-11T11:30:04.875828+00:00

ROOT bajo delegación acepta ADR0077 y cinco documentos revisados. Revisión2 A+B sin gaps; [QA documental vigente18/18/gate0](testing/t02/recipe-contract-current-qa-2026-10-11.md). Intento1 16/18/gate1 preservado: dos fallos del arnés literal, corregidos en intento2 sin modificar fuentes. ROOT50entradas/34canon/36snapshot verificados. Metadatos de aceptación posteriores no añaden reglas funcionales.

T02 sigue en-progreso y seis casillas pendientes. No hay código/test/RED aún. El siguiente despacho es la única reanudación NEEDS_CONTEXT con contrato concreto solicitado, sin inventar compatibilidad. TDD activo; captura/readers/proyecciones puros; admisión/SQL/render/custodia/exportschema pertenecen a otras unidades. M1NO-VERDE/ext4/store/writer/ACK/E2Ependientes. Arquitecto privado design_m1_nt_geometry_u2b2 prepara geometría en paralelo, sin cambios M1 ni marker propio; trabajo no medido. Tokens/eur/horas reales null.


## T-02: RED inicial observado — 2026-10-11T11:34:42.022611+00:00

RED: `test_capture_freezes_nested_context` falló con `NotImplementedError` del stub de captura/reader · 2026-10-11T11:32:22.3751422Z · pytest1/JUnit1fallo.

RED: `test_legacy_preserves_raw_and_absence` falló con `NotImplementedError` del stub de captura/reader · 2026-10-11T11:32:24.0355914Z · pytest1/JUnit1fallo.

ROOT leyó los logs/JUnit de los dos casos y sus recibos; son RED funcionales iniciales, no ImportError de colección. No acredita todavía todos los comportamientos, GREEN, cobertura ni cumplimiento completo de TDD; se validará la secuencia y los snapshots al recibir la implementación. T02 en-progreso, seis casillas pendientes. Evidencia en .cache/dev-cycle/m2/creative-recipes-t02-implementation-20261011/.


## T-02: entrega CPU verificada y revisión producto fresca — 2026-10-11T12:02:37.415829+00:00

ROOT verifica manifest555a195e:219artefactos,4destinos nuevos y3guardas de compatibilidad intactas. Recibos finales2 y JUnit:144PASS/0FAIL/ERROR/SKIP; gate oficial cobertura completa líneas+ramas88,1578947368%,0exclusiones, Ruffcheck0 yformat3alreadyformatted.53nodosRED fallidos originales aparecenGREEN en final; su causalidad específica y preimágenes se entregan también a lenteA, no se atribuye un RED genérico a todo el código. red-expanded/collection/braces son diagnósticos preservados y no pruebanTDD funcional.

Snapshot158fuentes/baseprivada296c19ac30f9313e6ee063000c32cf7e3f5339cd, scope4files/0fuera/0avisos/0exclusionesusuario. LentesA/B/C efectivamente despachadas:review_m2_recipes_a1/b1/c1. Cauto true por patrónprivate-key en recipes.py124; Dauto false. Reviewerfrontmatter sinoverride. Artefactos y recibos en `.cache/dev-cycle/m2/creative-recipes-t02-product-review1-20261011/`. PureCPU, noSQL/admission/render/GPU ni derechos/custodia reales probados. T02 sigue en-progreso; revisión yQA independiente pendientes antes de aceptación.

Preparación/revisión M1 paralelas conservan propio alcance; no nuevas métricas reales inventadas. Ventana ROOT implementación se cierra y review1 se abre con único marker, reloj no equivale a horasIA; tokens/eur/horas realesnull.


## Revisión de dos lentes — intento 1: T-02 producto recetas — tres Important pendientes

ROOT 2026-10-11T12:13:18.659462+00:00: A/B/C completas, Dauto false; 0Critical/3Important/0Minor. Fuentes actuales exactas al freeze de revisión, ninguna aceptación por 144PASS. Tablas completas y evidencia en [informe](testing/t02/creative-recipes-product-review1-2026-10-11.md).

| # | Grado | Gap | Tarea | Veredicto ROOT | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Fade sin RED causal previo | T-02 | Pendiente; borrar sólo la implementación afectada y reescribir tras RED | recipes.py:827; preimagen red3 y dos casos ya verdes, lente A |
| B01 | Important | Objeto en type union no cerrado | T-02 | Pendiente; reproducir y cerrar schemas de objeto en unions | recipes.py:965; payload type object/null acepta undeclared, lente B |
| B02 | Important | Mapas y valores const confundidos con schemas | T-02 | Pendiente; recorrer posiciones reales de schema | recipes.py:969; propiedad llamada properties y const objeto válidos rechazados, lente B |

Se libera corrección FIX1 por implementer fresco en los mismos cuatro destinos; originales/snapshot/219artefactos permanecen intactos. No re-despacho del actor de implementación original ni reapertura del diseño. TDD obligatorio por criterio: B01/B02 reproducidos en fuente previa; fade retirado y reescrito sólo tras rojo funcional propio, manteniendo consumidores y hashes contractuales. Verificación, cobertura completa >=80%, Ruff, nueva revisión2 y QA independiente pendientes. T02/M2 abiertos.

Marcador review1 cerrado antes FIX1, reloj no atribuido a horasIA. Tokens/eur/horas reales null; sin operaciones GPU, Docker, WSL, BD o Git compartido.


## T-02: corrección FIX1 paralela a unidad M1 independiente — 2026-10-11T12:21:21.605647+00:00

fix_m2_recipes_product1 sigue ownership cuatro archivos creativos; implement_m1_geometry_u2b2 sólo dos fuentes privadas distintas. ROOT registra delta documental M1/G2 y único marker lote m1-m2/lote-geometria-recetas-implementacion para evitar imputación doble; no mediciones reales individuales. A01/B01/B02 siguen pendientes de entrega/verificación, revisión2 y QA. Sin cambio de requisitos ni cierreT02/M2.


## T-02: FIX1 verificado y revisión producto intento2 en curso — 2026-10-11T12:25:18.142847+00:00

ROOT verifica244artefactosFIX1,219originales intactos,158fuentes snapshot/base21a30e8dac7deb97ac22c676351f5eebe99fcf17.169PASS/0FAIL/ERROR/SKIP, wholelíneas+ramas88,4935654807%,0exclusiones; Ruffcheck0/formatcheck0. Cuatro destinos finales pinneados, __init__intacto; correctiondiff tresarchivos. Scope3/0fuera/0avisos/0exclusionesusuario. C/DautoFALSE sobrecorrección; lenteC1clean conservada. Lentesfrescas review_m2_recipes_a2/b2 efectivamente despachadas con tabla anterior completa, sin reabriraprobado salvoevidencianueva.

- RED: `apps/server/tests/test_creative_recipes.py::test_schema_object_union_must_be_closed` falló con `Failed: DID NOT RAISE RecipeError` · 2026-10-11T12:14:45.529117+00:00; artefactos `red-b01`→`green-b01`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_property_named_properties_is_data_map_entry` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:14:47.188459+00:00; artefactos `red-b02-properties`→`green-b02-properties`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_const_object_is_data_not_schema` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:14:48.935163+00:00; artefactos `red-b02-const`→`green-b02-const`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_recursive_local_ref_is_supported[#]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:17:53.566690+00:00; artefactos `red-local-recursion`→`green-local-recursion`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_recursive_local_ref_is_supported[#node]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:17:53.566690+00:00; artefactos `red-local-recursion`→`green-local-recursion`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_partition_preserves_parent_coordinates` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:17:01.903196+00:00; artefactos `red2-fade-partition`→`green2-fade-partition`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_omits_zero_length_pieces[10-None-pieces0]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:16:14.996652+00:00; artefactos `red-test_fix1_fade_omits_zero_length_pieces`→`green-test_fix1_fade_omits_zero_length_pieces`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_omits_zero_length_pieces[None-10-pieces1]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:16:14.996652+00:00; artefactos `red-test_fix1_fade_omits_zero_length_pieces`→`green-test_fix1_fade_omits_zero_length_pieces`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_omits_zero_length_pieces[4-6-pieces2]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:16:14.996652+00:00; artefactos `red-test_fix1_fade_omits_zero_length_pieces`→`green-test_fix1_fade_omits_zero_length_pieces`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_omits_zero_length_pieces[None-2-pieces3]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:16:14.996652+00:00; artefactos `red-test_fix1_fade_omits_zero_length_pieces`→`green-test_fix1_fade_omits_zero_length_pieces`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_requires_at_least_one_envelope` falló con `Failed: DID NOT RAISE RecipeError` · 2026-10-11T12:16:16.530896+00:00; artefactos `red-test_fix1_fade_requires_at_least_one_envelope`→`green-test_fix1_fade_requires_at_least_one_envelope`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_rejects_exceeding_parent_duration[11-None]` falló con `Failed: DID NOT RAISE RecipeError` · 2026-10-11T12:16:17.834878+00:00; artefactos `red-test_fix1_fade_rejects_exceeding_parent_duration`→`green-test_fix1_fade_rejects_exceeding_parent_duration`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_rejects_exceeding_parent_duration[None-11]` falló con `Failed: DID NOT RAISE RecipeError` · 2026-10-11T12:16:17.834878+00:00; artefactos `red-test_fix1_fade_rejects_exceeding_parent_duration`→`green-test_fix1_fade_rejects_exceeding_parent_duration`, exit1→0 y preimágenes/pins conservados.
- RED: `apps/server/tests/test_creative_recipes.py::test_fix1_fade_rejects_exceeding_parent_duration[6-5]` falló con `Failed: DID NOT RAISE RecipeError` · 2026-10-11T12:16:17.834878+00:00; artefactos `red-test_fix1_fade_rejects_exceeding_parent_duration`→`green-test_fix1_fade_rejects_exceeding_parent_duration`, exit1→0 y preimágenes/pins conservados.

Estos14casos corresponden a ocho pares ejecutados con receipt/UTC/exit/preimage/pytestJUnit verificados, no prueban todavía conformidad de toda causalidad: lenteA audita el cuerpo fade retirado/rehecho y la secuencia. Diagnóstico primera expectativa de código errónea preservado, no contabilizado comoGREEN. Caracterizacionesposteriores no se atribuyen comoRED. A01/B01/B02 quedan en corrección propuesta pendiente revisión2 y QAindependiente, no aceptadas por reporteactor.

ROOT contabiliza deltas documentales autorizados M1/ADR0078 e index mediante adoption/release receipts; ningún helperM1 cambió. M1U2b2 trabaja sólo snapshotprivado en paralelo. Único marker del lote, sin métricas reales atribuibles individualmente. T02/M2 abiertos; no derechos reales, música, SQL/admission/render o M1integral probados. Evidencia `.cache/dev-cycle/m2/creative-recipes-t02-product-review2-20261011/prepare-root.receipt.json`.


## Revisión de dos lentes — intento 2: T-02 producto recetas — B03 Important nuevo

ROOT 2026-10-11T12:31:28.885655+00:00: A/B frescas completas, C/DautoFALSE; A01/B01/B02anteriores corregidos,0Critical/1Importantnuevo/0Minor. [Informe completo](testing/t02/creative-recipes-product-review2-2026-10-11.md). A valida causalidadfade nueve casos y14casos totales, importsreales169PASS; B169PASS+22probes y tres comparativosprior→current acreditan regresión nueva, no reabre casos aprobados sin evidencia.

| # | Grado anterior/actual | Gap | Veredicto ROOT | Evidencia |
|---|---|---|---|---|
| A01 | Important anterior | Fade sin RED causal | corregido intento2 | A2 reproduce nueve fade originalPASS→retiradoFAIL→reescritoPASS y secuencia propia |
| B01 | Important anterior | Unión objeto abierta | corregido intento2 | A2/B2; diez posiciones negativas y RED original→GREEN |
| B02 | Important anterior | Mapas/const tratados como schemas | corregido contraejemplos originales intento2 | A2/B2; literals/property-names y refs positivos; nuevo caso distinto en B03 |
| B03 | Important nuevo | Guarda exige cierre a tipos que excluyen objeto | pendiente FIX2 | recipes.py:996; string/required[], integer/minProperties0 y array/propertyNames válidos; prior ACCEPT→FIX1 RECIPE_INVALID |

FIX2 liberada a implementer fresco sobre mismoscuatroarchivos; B03 reproducir fuenteFIX1exacta con RED funcional por tres variantes, mínima corrección semántica de tipos explícitos sin perder closednessobject/unions/refs, luego GREEN/verificación/cobertura/Ruff. No cambiar contrato aprobado ni helpersM1; originales244FIX1/219originales intactos. Revisiónproducto3de3 yQAindependiente posteriores. T02/M2en-progreso, nada aceptado por tests propios. PreparacióndocumentalT20reparó dosURLsM1tasks por byte-splice registrado, sin cambios runtime ni fuentes de este snapshot.

LoteROOT pasa de geometríaimplementación/recetasreview2 a geometríaimplementación/recetasFIX2, markerúnico sin métricasreales individuales. Evidencia `.cache/dev-cycle/m2/creative-recipes-t02-product-review2-20261011/fusion-root.receipt.json`.


## T-02: FIX2 efectivamente despachada — 2026-10-11T12:33:06.155101+00:00

Actor fresco fix_m2_recipes_product2 iniciado por ROOT, briefdeterminista25682bytes, tierfrontmatter. Ownership originalcuatroarchivos+namespace privadoFIX2; M1geometría sólosnapshotdistinto. B03 únicoImportantnuevo pendiente; A01/B01/B02conservadoscorregidos. TestsREDtresvariantesantescódigo/verificación/cobertura/Ruff/manifest exigidos, luego reviewproducto3de3 yQAindependiente. Originales/snapshots sinreescritura. No cierreT02/M2 ni nuevo marker; único lote m1-m2/lote-geometria-implementacion-recetas-fix2, realesnull.


## T-02: FIX2 verificado; revisión de producto intento 3 en curso — 2026-10-11T12:42:41.704612+00:00

ROOT verificó 136 artefactos FIX2, 219 originales y 244 FIX1 intactos, y las 158 fuentes del snapshot anterior. Verificación exacta declarada: 183 PASS con argv, salida completa y pins antes/después; ese comando no emite JUnit. Cobertura separada sí contiene 183 casos JUnit sin FAIL/ERROR/SKIP, whole líneas+ramas 88,50226928895613%, cero exclusiones. Ruff check y format --check exit0. Sólo tres archivos cambian respecto a FIX1; __init__ intacto. Scope3/0fuera/0avisos/0exclusiones usuario; C/D auto false sobre esta corrección, C1 limpia conservada.

- RED: `apps/server/tests/test_creative_recipes.py::test_schema_object_keywords_do_not_close_explicit_nonobjects[string-required]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:33:28.914169+00:00; `red-final-string`→`green-string`, exit1→0, mismos tests y preimágenes fijadas.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_object_keywords_do_not_close_explicit_nonobjects[integer-minProperties]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:33:30.175961+00:00; `red-final-integer`→`green-integer`, exit1→0, mismos tests y preimágenes fijadas.
- RED: `apps/server/tests/test_creative_recipes.py::test_schema_object_keywords_do_not_close_explicit_nonobjects[array-propertyNames]` falló con `app.creative.recipes.RecipeError: RECIPE_INVALID` · 2026-10-11T12:33:31.431979+00:00; `red-final-array`→`green-array`, exit1→0, mismos tests y preimágenes fijadas.

Los tres casos fallaron funcionalmente sobre runtime FIX1 intacto antes de modificarlo, con tests idénticos en el GREEN. Once controles ya verdes son caracterizaciones, no RED ficticios. La primera preparación ROOT asumió un JUnit inexistente del comando declarado; diagnóstico conservado y verificador corregido antes de crear snapshot o mutar canon. No se cambiaron tests/producto por ese diagnóstico.

Lentes frescas efectivamente despachadas: review_m2_recipes_a3 y review_m2_recipes_b3, revisión producto intento3de3. Reciben la tabla completa de revisión2; A01/B01/B02 corregidos previamente, B03 sólo corrección propuesta hasta revisión3. Snapshot privado base b52b72dfa155aa971e346279d42adff5f00c34f4, diff tres archivos completo. QA independiente posterior pendiente; T02 sigue en-progreso y M2 no aceptado. M1 geometría nativa continúa en snapshot separado; su regresión adicional incompleta por dependencia readonly ausente no se atribuye al runtime ni se oculta, y se autorizó suministro privado fijado. Ningún modelo GPU, dato/BD o servicio ajeno tocado.

Evidencia: `.cache/dev-cycle/m2/creative-recipes-t02-product-review3-20261011/prepare-root.receipt.json`. Una sola medición del lote mixto; tokens, euros y horas IA reales no medidos.


## Revisión de dos lentes — intento 3: T-02 producto — A/B sin gaps — 2026-10-11T12:49:07.125071+00:00

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Fade sin RED causal | T-02 | corregido intento2, conservado | FIX2 no toca fade; juicio A2/paresFIX1 conservados |
| B01 | Important | Unión objeto abierta | T-02 | corregido intento2, conservado | A3/B3 negativos de objetos/uniones/implícitos |
| B02 | Important | Mapas/const tratados como schemas | T-02 | originales corregidos intento2, conservado | A3/B3 mapas/literales/refs locales |
| B03 | Important | Cierre exigido a tipos no objeto | T-02 | corregido intento3 | tres REDGREEN causales, comparativos independientes A3/B3 |

Lentes A+B reales, 0Critical/Important/Minor; C/DautoFALSE sobrecorrección y C1clean conservada. Tablas completas por criterio y evidencia en [informe](testing/t02/creative-recipes-product-review3-2026-10-11.md). T02 pasa a en-revision para QA CPU independiente de esta unidad; no cierre ni aceptación M2, sin UI/E2E fingidos. Todos los escenarios M2 integrales quedan pendientes hasta sus implementaciones. Jira/Confluence desactivados. No candidatos de conocimiento nuevos que promocionar.


## T-02 — aceptación de unidad CPU y entrega completa — 2026-10-11T13:16:22.427044+00:00

ROOT acepta T02 tras revisión3A/B limpia y QA independiente real183PASS+3probes/88,502269%0excl; resolvióPDF pendiente8páginas. Históricos y diagnóstico inicialNumPy/cp1252 intactos, sin repetir suite verde por formato. Corrección de cita RED en informe publicado trazable: fallo real RECIPE_INVALID; no cambian tests ni juicio. 60artefactos y158fuentes verificados nuevamente antescierre. M2 2/30; hito abierto por28tareas, M1 abierto. PróximaT03 requiere concretar contrato de construcción por muestras antes producto; ownership separado de FIX1M1. Git del loteM2 aún pendiente de revisión de fuentes y documentos necesarios, sinstageglobal. SóloROOTestados/meter; coste/tokens/horasIA realesnull.


## T-03 — concreción de contrato antes del RED — 2026-10-11T13:17:21.689290+00:00

DependenciaT02completada unidadCPU. T03 pasaen-progreso para fijar esquema de composición por muestras/formatos/shape antes implementación; architectfresco trabaja exclusivamente propuesta privada, ROOTelige alternativa bajo delegación del propietario y ratifica con revisión documental/QA antes producto. No cambia contratosT02sellados, schemas públicos, SQL, cola ni renderer. M1FIX1 sigue independiente. TDDn/a para propuesta de prosa; el producto posterior exigeREDconductual. M2sigue2/30, no E2E/audio real acreditados.


## Revisión de dos lentes — intento 1: T03 contrato composición — tres Important y un Minor — 2026-10-11T14:11:53.608696+00:00

A01Important resumenextend110no140, A02Minor tablaopciones, B01Important cola convertida81con fuente nominal[160,160), B02Important región global[6,8]frenteengine local2s. ROOT confirma sin rebate/deuda; sondasCPU de capturaT02 válidas2/2 y aritmética, no audio medido. [Respuestas y fusión](testing/t03/composition-contract-review1-2026-10-11.md). FIX1 actorfresco fix_m2_t03_composition_contract1 DONE, sólo3docs privados; originales26/26 y23no-owned intactos.

ROOT selecciona bajo delegación la representación propuesta nominal_src paraBconvertido y conversion_scope completo, separada de spans estrictos de render/src/dst y sin footprintsoxr ficticio. Aceptación contractual depende de revisión2 yQA; no se publica contrato ni código antes. ArchivosT03 amplía explícitamente cinco documentos de su concreción; no cambian dependencias/casillas/estadoen-progreso.


## T03 contrato FIX1: revisión documental2 iniciada — 2026-10-11T14:13:57.781879+00:00

ROOT verifica26guardas FIX1 y original26exactas; sólo3docs changed,23no-owned intactos. O1con nominal_src/conversion_scope elegida como propuesta tras corregir casosB01/B02; representaciónfinal pendiente revisión/QA. Scopeoficial6docs/0fuera/0avisos/0exclusiones, C/Dautofalse, reviewerfrontmatter. Snapshot26/base597a7d6 congelados. LenteAfresca review_m2_composition_contract_a2 efectiva; B2 pendiente de slot, no se atribuye ejecución. Fuenteprosa/noRED/no código ni render. T03en-progreso/M2noaceptado; contrato canónico noincorporado.


## Revisión de dos lentes — intento 2: contrato composición FIX1 — sin gaps — 2026-10-11T14:20:19.281981+00:00

| Gap | Grado anterior | Veredicto | Evidencia |
|---|---|---|---|
| A01 | Important | corregido | Extend region sin sufijo antiguo, 110frames. |
| A02 | Minor | corregido | O1/O2/O3 comparadas en una tabla. |
| B01 | Important | corregido contractualmente | nominal_src vacío, render/dst positivos, conversion_scope completo, 101frames. |
| B02 | Important | corregido contractualmente | Padre global y buffers engine locales separados, 100frames. |

LentesA/B frescas efectivas review_m2_composition_contract_a2 y review_m2_composition_contract_b2,0Critical/Important/Minor. Scope6/0fuera/0avisos/0excl,C/Dfalse; snapshot26/T02 exactos. [Respuestas completas y fusión](testing/t03/composition-contract-review2-2026-10-11.md). Controles de auditores son prosa, no producto ni audio; ninguna suite/TDD/E2E deT03 acreditada. QA documental independiente siguiente; canoncontrato/ADR todavía pendientes. T03en-progreso/M2noaceptado.


## QA documental T03: recuperación de despacho — 2026-10-11T14:41:23.309932+00:00

Revisión2A/B0gaps registrada y snapshot26 congelado. Primerdespacho qa_m2_composition_contract1 terminó porHTTP400 invalid_request_error: modelo gpt-6.1-sol no soportado en aquella sesión de cuentaChatGPT; sin resultadosQA. Tras reanudación explícita de usuario, ROOT inspeccionó namespace sólo preparación y reanudó el mismo actor. EjecuciónQA actual confirmada por herramienta colaboración y archivos de checks/gate nuevos; terminal/manifest/informe pendientes, no se acepta por progreso parcial. No cambio de configuración de cuenta/modelo, ningún resultado del turno fallido se acredita.


## T03: contrato ratificado antes del RED — 2026-10-11T14:46:46.675900+00:00

ROOT verifica84artefactos/26sources/60checks/gate0/streams/recibos/reportPDF6páginas estructural/previewprint sin rasterización. RevisionesA/Bintento2 sin gaps, previos3Important1Minor corregidos. [QA documental y ratificación](testing/t03/composition-contract-current-qa1-2026-10-11.md). ADR0079 aceptada/contratoO1 aprobado; seisdocs incorporados, T02codebytes intactos.

T03 sigueen-progreso, casillas/productVerificaciónpendientes; noREDni compositor aún. Siguiente actorfresco implementará sólo composition.py/test_creative_composition.py contra contrato ratificado con TDD causal y cobertura80sinexclusiones. Render/conversiónreal/publicaciónSQL/capacidadmusical/E2E/gatesM1 siguen pendientes, no seedfake.


## T03: implementación liberada a actor fresco — 2026-10-11T14:49:19.198878+00:00

Actor implement_m2_t03_composition efectivo con briefdeterminista/TDD, snapshot95fuentes yownership2nuevas composition.py/test_creative_composition.py privados. ContratoO1/ADR0079ratificados; noREDtodavía acreditado ni código canónico. RED/GREEN causales por18AC con preimages/argvUTC/streams/JUnit/whole80sinexcl; sóloROOTledger/CAS/review/QA. T03en-progreso, noVerificaciónproducto/cierreM2.


## T03: primer RED funcional verificado por ROOT — 2026-10-11T14:57:39.011562+00:00

- RED: apps/server/tests/test_creative_composition.py::test_ac02_decimal_half_up falló con NotImplementedError en round_frame al exigir0.05@10→1 · 2026-10-11T14:50:01.963066+00:00

ROOT verifica preimage runtime/testSHAexactos, stdout/stderr,JUnit1FAILywait/reap. Módulo/símbolo stub existen; fallo es comportamiento ausente, noImportError. Primerdiagnóstico uv cwd snapshot/miembroworkspaceausente preservadoy nocuentaRED. Este registro preliminar no acredita restoTDD/Green/coverage, actor continúa, producto canónico aúnnoincorporado.


## T-03: verificación del candidato y RED observados — 2026-10-11T15:26:54.147153+00:00

ROOT verifica660artefactos/95fuentes existentes/92recibos de ejecución,89focal+183regresión=272casos combinados únicos; whole94,618%líneas/88,077%ramas,0exclusiones. Importación actual independiente sobre SHAfinal f2b5a79/67eb475; observación antigua no atribuida a bytes finales. T03sigueen-progreso, sinadopción ni cierre. Revisión fresh pendiente.

- RED: `test_ac01_trim_and_fade_counts` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:53:09.168850+00:00 · criterioAC01 · preimagen3c2be4a6b3708b6b5c40ee52ba8576fb4f6a7dd0aae8f87e98e9ddf448b4ef9e · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC01-RED/receipt.json`; GREEN `AC01-GREEN` exit0. AST del test igual: True.
- RED: `test_ac02_decimal_half_up` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:50:01.963066+00:00 · criterioAC02 · preimagenc90d12a940bcb847aa3d05e74e5893af53f5d9e76c7284895d6ea91e193eed98 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC02-RED-causal/receipt.json`; GREEN `AC02-GREEN` exit0. AST del test igual: True.
- RED: `test_ac03_envelope_minimum` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:54:28.390986+00:00 · criterioAC03 · preimagendbd45e24581bdff85186ee7c12253d15950e21da32eb991c400913424d5855c3 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC03-RAMP-RED/receipt.json`; GREEN `AC03-RAMP-GREEN` exit0. AST del test igual: True.
- RED: `test_ac04_exact_numbers` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:50:24.436965+00:00 · criterioAC04 · preimagen3e8fd7cdf46179c18e859907e57ca87e23634a561f51e0cecdc8b935b112d129 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC04-RED/receipt.json`; GREEN `AC04-GREEN` exit0. AST del test igual: True.
- RED: `test_ac05_round_limits` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:50:39.211905+00:00 · criterioAC05 · preimagena2c67a0b82ec49fbdcd5e30bc8a934ab57027fbc078943c2b96f8a8fcfc6ebba · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC05-RED/receipt.json`; GREEN `AC05-GREEN` exit0. AST del test igual: True.
- RED: `test_ac06_measured_duration` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:52:09.604717+00:00 · criterioAC06 · preimagen391c03a9fa45799178fd5978613ee0fd7bdd06b140b5bfb40e389da0c99e23fb · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC06-RED-refined/receipt.json`; GREEN `AC06-GREEN` exit0. AST del test igual: True.
- RED: `test_ac07_anchored_bounds` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:52:12.911592+00:00 · criterioAC07 · preimagen99472e58639d57faa4906957ebf26a5be1f463f77b1b608dc055de8f987abf99 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC07-RED/receipt.json`; GREEN `AC07-GREEN` exit0. AST del test igual: True.
- RED: `test_ac08_crossfade_dual_edges` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:54:54.802469+00:00 · criterioAC08 · preimagenb4873bb96c44908b33759ee618435dbf59df85985091dcdf1e9a0ee70ea1ae6b · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC08-RED/receipt.json`; GREEN `AC08-GREEN` exit0. AST del test igual: True.
- RED: `test_ac09_conversion_preflight_and_closed_facts` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:55:34.614377+00:00 · criterioAC09 · preimagen11ad64b6e986f4ac4bcb81ba1782de61cde3c6801c61b63bdfe7894cf8b8eb11 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC09-RED/receipt.json`; GREEN `AC09-GREEN` exit0. AST del test igual: True.
- RED: `test_ac10_empty_nominal_tail_is_real_dependency` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:56:33.329761+00:00 · criterioAC10 · preimagen535b5864833a478947482ef3069e3881cd9b56fd77b0d52162ff5566e16c5bf0 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC10-RED/receipt.json`; GREEN `AC10-GREEN` exit0. AST del test igual: True.
- RED: `test_ac11_repaint_region_and_full_counts` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:57:52.049545+00:00 · criterioAC11 · preimagen2cf90af9b6daad337e996d5208e39022f3a4e9ea1dc2a02506350591ec6a263e · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC11-RED-refined/receipt.json`; GREEN `AC11-GREEN` exit0. AST del test igual: True.
- RED: `test_ac12_engine_binding_and_shape` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:57:07.765259+00:00 · criterioAC12 · preimagend31af8dd863c7acb3cc268b842d0b9906d799a18b7ee7964c492559bc7238b0b · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC12-RED/receipt.json`; GREEN `AC12-GREEN` exit0. AST del test igual: True.
- RED: `test_ac13_extend_edges_and_measured_output` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:58:25.399444+00:00 · criterioAC13 · preimagenfc005d145f237712dc488fbd186bbed7e6b33a4e5f9735bc88b3ca1415d10ac4 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC13-RED/receipt.json`; GREEN `AC13-GREEN` exit0. AST del test igual: True.
- RED: `test_ac14_full_keep_is_not_proven_copy` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T14:58:22.174818+00:00 · criterioAC14 · preimagen76076fddb29d6b5c80abba41135ba006262d50f5b338ce2ff856383cb355328a · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC14-RED/receipt.json`; GREEN `AC14-GREEN` exit0. AST del test igual: True.
- RED: `test_ac15_frozen_nested_and_wrapper` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T15:00:29.320289+00:00 · criterioAC15 · preimagen29d0290cbc8f4746ada9842d80a1520386c138d569c5c55fd518dba1d39ad627 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC15-RED/receipt.json`; GREEN `AC15-GREEN-refined` exit0. AST del test igual: False.
- RED: `test_ac16_codec_replay_rejects_tampered_plan` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T15:02:26.327740+00:00 · criterioAC16 · preimagen44e5f58a81d14dd116f8f0741c1f63e846e033c2eb98bc1a3170fa58a78fdd4b · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC16-RED-refined/receipt.json`; GREEN `AC16-GREEN` exit0. AST del test igual: True.
- RED: `test_ac17_pure_wrapper_boundary` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T15:00:32.821835+00:00 · criterioAC17 · preimagenfae0adea4bdf337ad62495b1f37c1377e35830de7fe41dac5517a756a3fefc40 · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC17-RED/receipt.json`; GREEN `AC17-GREEN` exit0. AST del test igual: True.
- RED: `test_ac18_sanitized_api_errors` falló con fallo causal JUnit (exit1, sin ImportError/SyntaxError) · 2026-10-11T15:01:49.747838+00:00 · criterioAC18 · preimagenbe0414dd815906f88f0eb2a1fd8206deef19acd131180413406278e9823b506e · `.cache/dev-cycle/m2/creative-composition-t03-implementation-20261011/evidence/AC18-RED/receipt.json`; GREEN `AC18-GREEN` exit0. AST del test igual: True.

AC15 tiene cambio de AST entreRED yGREEN-refined: el actor declara traslado de assertions ajenas a su fixture. No se acredita automáticamente como TDD conforme; revisiónA debe juzgar preimágenes. AC17pureza inherente es regresión, elRED sólo corresponde a revalidación dewrapper. Diagnósticos previos conservados; no sonRED. ROOTcomparaciónJSON/ASTdeimports falló enverificador, corregida con parser y nuevo testigo actual; no fallo deproducto.


## Revisión de dos lentes — intento 1: T-03 compositor — 1 Important

ROOT 2026-10-11T15:35:46.493130+00:00: A/B frescas,C/DautoFalse,0Critical/1Important/0Minor. A01 confirmado: AC01contrato273 exige fade sum>N rechazado trasresolución, runtime895correcto pero negativo ausente. [Informe completo](testing/composition-product-review1-2026-10-11.md). FIX1 fresco autorizado, sinCAS/cierreT03.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Suma fades redondeados excedeN sinregresión | T-03 | pendiente | padre100@10,4.95/5.05→101>N100 |


## T-03 FIX1 verificado por ROOT; revisión2 pendiente — 2026-10-11T15:43:20.043313+00:00

ROOT213payload/95nonowned/recibos/91focal183T02274combinados verificados; runtimef2b5a79byteexact, tests2c5464eañaden2regresiones sin alterar89anteriores. RED: test_ac01_fade_sum_exceeds_frames_after_rounding falló AssertionError INVALID≠OUT_OF_BOUNDS · 2026-10-11T15:38:03.625651+00:00 · borradasóloguarda2líneasprivada, preimagenae2467c2a457c6a946f3757fe2f9df65ec044adafa588e90ea42aac658792dd0, reescrituraexactadespuésreap→GREENexit0. No bugactual ni fakeREDimports. Whole94,7917%líneas/88,4615%ramas,0excl; diagnósticoscoverageNumPy77/Ruffpreservados, nofalloproducto. A01pendienteveredictoreview2/QA,CAS/cierreT03.


## Revisión de dos lentes — intento 2: T-03 compositor — A/B sin gaps

ROOT 2026-10-11T15:51:38.984405+00:00: A01Importantcorregido;0Critical/Important/Minor,C/DautoFalse,scope2sinavisos/excl. [Informecompleto](testing/composition-product-review2-2026-10-11.md). B2encabezadobasereview1corregidoporsuautor; evidenciasactualesreview2autenticadas, originalesconservados. QAindependienteWindows/Linux autorizada, noCAS/cierreT03hastaROOTgate.

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Negativofade sum>N ausente | T03 | corregidoFIX1/review2 | nuevo test/control,TDDcausalreescritura;runtimeexacto |


## Git incremental T-03 — 2026-10-11T16:08:19.316069+00:00

Commit/push cc6efaf66bbf75aad53e0c26a809616f58b06cec verificado origin/m1/t-02-esquema,5ficheros(runtime/tests/reviews1–2/QAactual), indexvacío. Excepcióncoordinada decheckoutcompartido preservaajenos sincheckout/stageglobal/mainmerge. **Commit de componente, no árbol autónomo**: dependeT02/M1presenteslocalmente pero no todosintegradosGit, conforme auditoríadependenciasT02yaexistente. No se afirma clone/CI/mainverde por estepush. Ledgers/ADRs/plan/depscompartidas restantes siguen pendientes de integracióncoherente; hitoM2noaceptado.


## T-04: candidato congelado y revisión completa — 2026-10-11T16:39:18.589293+00:00

ROOT verifica 196 payloads originales y 7 de autoría QA, 113 fuentes del implementer y 142 del snapshot QA; 48 pruebas focales y 274 vecinas pasan sin fallos, errores ni skips; siete comandos exit0/reaped. El guardrail DENY original de testing/contract-baseline.md permanece registrado y no se reintentó. QA produjo el documento en namespace distinto para la revisión completa, sin QA final ni aceptación. El arnés conserva lectores reales, 22 fixtures JSON e índice no autorreferente, schema privado code-first y dos exportaciones OpenAPI aisladas iguales f42adb4a con lint/diff oficial0. No runtime modificado: TDD n/a configuración/prosa y regresiones de lectores existentes; el rojo diagnóstico era una suposición del test, no una modificación de producto ni RED atribuido. Cobertura changed-runtime n/a. T04 en-revision; sin adopción, cierre, E2E/audio/GPU/DB/custodia real. Evidencia privada: .cache/dev-cycle/m2/creative-contract-harness-t04-review1-20261011/.


## Revisión de dos lentes — intento 1: M2 T-04 — 2 Important y 1 Minor

Lentes A+B frescas; C/D auto false. Scope27files0fuera/avisos/exclusiones; revisión del arnés test/config y baseline de autoría QA. ROOT conserva respuestas íntegramente en creative-contract-harness-t04-review1-20261011/response-a1.md y response-b1.md. La conformidad A no sustituye los negativos de corrección B.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B01 | Important | Arrays usan minLength/maxLength ignorados, no minItems/maxItems | T-04 | pendiente FIX1 | schema:110/409/1280/1797; diez mutantes y cinco DTO locales reproducidos por B |
| B02 | Important | Números usan gt/ge ignorados, no keywords Draft202012 | T-04 | pendiente FIX1 | schema:128/207/230/242/746; controles locales rechazados por DTO y aceptados por schema |
| A01 | Minor | Link del baseline resuelve evidence-checks.json fuera de su namespace de autoría | T-04 | pendiente corrección por QA al producir versión final | baseline:58; original de QA conservado |

T04 vuelve a en-progreso. No runtime fallido ni cambiado: schema/config se corregirá sin tocar DTOs ni lectores. Negativos de restricciones locales y positivos emparejados, no falsa equivalencia con reglas relacionales/hash/secretos. El documento testing/ continúa propiedad QA; el implementer FIX1 sólo entrega propuesta factual, no reintenta la escritura denegada. No aceptación E2E/audio/storage/hitos. 2026-10-11T16:46:51.186906+00:00


## T-04: FIX1 verificado por ROOT, baseline QA2 en preparación — 2026-10-11T17:00:47.351846+00:00

ROOT autentica238payloads/140snapshot:4ownedchanges136nonowned,22JSONoriginalesintactos. Schema05ef38f2/test78921e08. RED20casos18FAIL2PASS→generaciónconfig posteriorreap→GREEN20PASS; focalactual69PASS,vecinos274PASS,generador3PASS. B01/B02corregidosencandidatoprivadopendienterevisión2;A01enlacesbaselinependienteautorQA2. TipoErrorauditorfocal68+1preservadonocausalproducto. No runtimecambia/TDDnaconfig/coberturana, noadopciónni cierreT04.


## T-04: baseline QA versión2 verificado; revisión2 completa — 2026-10-11T17:02:49.900196+00:00

ROOT autentica8payloads de autoríaQA2 y139nonowned intactos. Baseline2d3a11c6 corrige A01link y describeFIX1schema05ef38/test78921e/índice7b20e/README9f4dec con historial48original y69actual separado. B01/B02pendingverdictreview2, docQAproducer noQAfinal. Snapshotreview2candidato27files, fuentesruntime intactas, caso causal18FAILconfig→20GREENrawJunit verificadoROOT238. T04en-revision sinadopción/cierre.


## Revisión de dos lentes — intento 2: M2 T-04 — sin gaps pendientes

Lentesfrescas A2/B2 apruebanfixB01array/B02numeric/A01links;0CriticalImportantMinor,scope27files0avisos/CDfalse. TransferenciaROOTestructuradano literal en .cache/dev-cycle/m2/creative-contract-harness-t04-review2-20261011/verdict-transfer-root.md, tablaspreviasíntegrasconservadas. A2ejec21nuevos+3privados/B2ejec69focal+3privados,actual140pins/238FIXpayload/8QA2authenticados; schema05ef38f2byteexact310nodes9changes11constraints. QAfinalindependiente siguiente; ningúnruntimecambia,cov/TDDna-config;T04en-revision noadopción/cierre/audioE2E/custodia.


## T-04: adopción y cierre contractual por ROOT — 2026-10-11T17:21:59.150137+00:00

ROOT verifica199payloads/140fuentes/27candidatos/449históricos, JUnit343+343 mismosIDs y3privadosporplataforma, gatesoficiales0, containerown retirado/reaps. CAS27 nuevos archivos tras review2/QA independiente; focalcanónica69PASS confirmaimportación desdeárbol actual. Fase1M2 4/4, total4/30; noaceptaciónhitoM2 ni E2E/audio/custodia. QA produjo informe directamente en ruta canónica pesebriefsnapshot; ROOTautentica hash0d85b069 ypreserva copia antesadopción, sin simular CASROOT previo. Git componente pendiente, cierre no prueba clone/CI autónomo ni depsM1T02integradas. RuntimeDTO/lector no cambia; TDD/cobertura na config/prosa, causalregresión18fail→config→20green intacta. Uso realnull.


## Git incremental T-04 — 2026-10-11T17:23:20.004651+00:00

Commit/push 18ed5dc1e16c5e4ed476e9b849b874b6e0a15111 verificado en origin/m1/t-02-esquema:30archivos de componente aceptado, índice vacío. Se conserva excepción de rama compartida ya registrada; sin mainmerge, stageglobal, reset ni cambios ajenos incorporados. Fixtures sintéticos, schema/test/baseline y revisiones/QA; ningún dato/modelo/ruta personal incluido. Clone/CI autónomo pendiente de integrar dependencias M1/T02; este commit no acredita ese cierre ni hito M2.


## T-05: inicio de schema durable bajo O1 — 2026-10-11T19:32:59.977770+00:00

T01–04cerradas4/30. Consulta fresca readonly audit_m2_t05_schema_readiness confirma headestático0007, distinto de versiónBDreal; no writer canónico models/migrations activo. O1/ADR0074 ya ratificado, no reapertura de alternativas. Discriminación/NULL/preservación están definidos; wire durable CpuEditPlan/resultado/paquete/readers y entrada exclusiva de upgrade deben concretarse antesREDrespectivo, no dictlibre ni autoridad inferida de receta/hash. ROOTañade ownershipseams de instalaciónSQL/env/db/codec puro y contrato nuevo. Arquitectofresco completa esos límites en design.mdprivado; no ORM/SQL/DB ejecutados ni modificación baseline0001–0007; sólo3tablasreconstruibles segúnADR0074. T05enprogreso/M2abierto, TDDn/a prosaenconcreción; implementaciónTDDdespuésrelease/reviewQA.


## T-05: contrato durable O1 en revisión documental1 — 2026-10-11T19:49:36.468423+00:00

Actorconcrete_m2_t05_persistence_contractDONE/frozen source5f695a6d y119sourcesreadonly; ROOTautenticafuentesyextrae apéndices datos/iteracion byteexactos. O1/ADR0074conservadas; planedit/receipt/packageCPUv2, reservas/FKs/SQLguards/CAS/exclusivemigrationbackuprollback/install0006frozen/TakeV2/Songv2/409M1 cerrados enprosa, no tests/SQLruntime ejecutados. Sólo3docsDiff; T05continúaenprogreso,M2=4/30. RevisiónfrescaA/B yQA preceden adopción yREDschema; T07mantienegateexecutor/custodia/publicadorreal. Uso realnull.


## Revisión de dos lentes — intento 1: T05contrato — ImportantA01/B01 confirmado · 2026-10-11T19:57:27.450769+00:00

ROOTnormaliza32A/11Bcriterios completos, source5f695a6d ybase484b83fd. Revisión frescas0Critical/1Importantdedup/1MinorA02; noproducciónniQAacreditadas. Reserva PUBRevision antesrender exigeSourceSHArealNOTNULL y luegoinmutable: triadaincompatible (NULL/padre/marcadorrechazados). ROOTseleccionareservaCPUpreejecuciónaditivaseparada yrevisiónfinal sólotrasfuentereal/receiptverificados, dentroO1/ADR0074sinexcepciónsourceNULL. FIX1architectfresco sólo prosa/private; cerraráplan/refs/schema/CAS/retry/portable/APIs/cases/apéndices antesrevisión2. Tabla completa testing/creative-persistence-contract-review1-2026-10-11.md. T05enprogreso,M2=4/30; implementación/schemaTDDaúnpending,uso realnull.


## T05contratoFIX1: revisión2 preparada — 2026-10-11T20:13:04.202021+00:00

FIX1architectfrescoDONE source dc29562e88428B443líneas/120readonlyhashesintactos. A01/B01reservaSOURCEcorrigidodocumentalmente mediante cpu_pre_render_reservation aditiva/plan sinPUBIDsfuturos; finalRevisiontrasrawreceipt/cierre reales conSourceSHArealNOTNULLinmutable desdebirth. CAS/retry/refs/closurev2/API/testmatrix/apéndices completos; A02inventario preservadoprimerafrase21palabras. ROOT remapea nuevas3docs/prefijoscanónicos exactos; revisión2 incluye TABLAcompleta32A/11B y2gapsprevios,sin omisiones ni replayviejoasactual. T05enprogreso/M2=4/30; QAadopción/REDschema pendienteshasta puertas. Usorealnull.


## Revisión de dos lentes — intento 2: T05 — B02Important confirmado · 2026-10-11T20:20:02.270160+00:00

A01=B01 yA02corregidos enFIX1dc29562e; tablas32A/11B originales yactualesíntegras normalizadasROOT. NuevoB02(C219) exigebatch_idNULL contradiceNOTNULL/ULIDbaseline fueraexcepciónADR74; 0Critical/1Important/0Minorpendiente. A2conforme acotadopor nuevaevidenciaB2ROOT, sinrebateniQAgreen. FIX2fresco mínimo usa batch_id=cpu_pre_render_reservation.id propiaagrupaciónCPUreal/sinFK/Batchentity niinferenciapadre; intactosNOTNULL/checks/índice. Propagarbindings/plan/reservation/DTO/SQL/portable/matrix/apéndices antesreview3 completa+QA. Sourceoriginaldc29562e120pinsintactos. T05/M2abiertos4/30;usorealnull.


## T05contratoFIX2: revisión3 preparada — 2026-10-11T20:26:50.861998+00:00

FIX2architectfrescoDONE source a608b81f97459B461líneas/120readonlyhashesintactos. B02batchNULLcorrigidoconULIDreserva.id yA01/B01reservaSOURCEcorreccionconservada mediante cpu_pre_render_reservation aditiva/plan sinPUBIDsfuturos; finalRevisiontrasrawreceipt/cierre reales conSourceSHArealNOTNULLinmutable desdebirth. CAS/retry/refs/closurev2/API/testmatrix/apéndices completos; A02inventario preservadoprimerafrase21palabras. ROOT remapea nuevas3docs/prefijoscanónicos exactos; revisión3 incluye TABLAcompleta32A/11B y3gapsprevios,sin omisiones ni replayviejoasactual. T05enprogreso/M2=4/30; QAadopción/REDschema pendienteshasta puertas. Usorealnull.


## Revisión de dos lentes — intento 3: T05 contrato durable CPU — limpio documentalmente · 2026-10-11T20:33:26.120755+00:00

ROOTfusioncompleta32A/11B; A01=B01Important/A02Minor corregidos2conservados3; B02ImportantbatchNULL corregido3 conULIDreserva/CASexecution/hash/batch antesReady ygrupos históricosporordinal.0Critical/Important/Minor pendientes, sinrebates/deuda. sourcea608b81f97459B461líneas/120pins/prior/diff/extractconformes; scope3/fuera0avisos0/CfalseDfalse. VerificaciónT05/coberturaSQL/ORM/API/import/migraciónbackup reales aún pendientes; QA documental fresca liberada antesadopción/RED. T05enprogreso/M2=4/30; executorT07nograntporprosa. Uso realnull.


## T05 contrato durable aceptado por ROOT; inicio del codec puro con TDD — 2026-10-11T20:40:51.548438+00:00

QA documental34/34/qa-gateprosa0/ledger0trazabilidad0,120snapshot119guards1ausencia/177payloadsverificadosROOT.3documentos adoptadosconCASprefijos,sourcea608b81f97459B; revisión3A32B11limpia,todos3gaps corregidos. PrimerharnessQA7rojos deauditorpreservados, no bugsproducto. PDFgenerado/hashverificado, norasterPDFinspeccionado, browserPIDpropio ausente; perfilconservadopor rechazoautomático del borrado sinmotivoespecífico. No revisiónvisualPDFniQAproducto ficticias.

PrimercomponenteT05: codecs/closedreaders en durable_contracts.py ytests test_creative_persistence.py, sólo snapshotprivado/actorfresco/TDDcausal porcriterio, sinDB/SQL/renderer/custodiareal. FullT05preserva freezelegacy0006/additiveExecutionPRE/3rebuildespecíficos/guardSQLORM/backupWALrestaurado/APIv2y409M1/Songv1v2closureimport/Verificacióndeclarada real/M1beforeafter/independentreviewQA. Ningúncodecemiteautoridad real porflags; T07executor/publication gates intactos. T05enprogreso/M2=4/30, no checkboxcerrado. SóloROOTledger/CAS/Git. Uso realnull.


## T05 codec puro — primer RED funcional confirmado por ROOT · 2026-10-11T20:43:50.557485+00:00

RED: apps/server/tests/test_creative_persistence.py::test_plan_roundtrip_all_fields_and_three_cpu_operations falló con NotImplementedError: CPU edit plan codec no implementado · 2026-10-11. Comando managedPython/run-component1.py child/selectorúnico, UTC2026-10-11T20:42:58.103799+00:00→2026-10-11T20:43:00.188449+00:00, exit1/JUnit1FAIL0ERROR, fixtures/imports válidos y125readonlybeforeafter iguales. Evidencia/preimage/argv/streams/imports propios en creative-persistence-t05-runtime-preparation-20261011/component1/red-plan. No ImportError ni testvacío; implementar mínimo despuésRED. Producto/sourcecanon/SQL/API/migración aúnsinaceptar, T05M2abiertos.


## Revisión de dos lentes — intento 1: T05 codecs — A01/B01Important confirmados · 2026-10-11T21:15:32.623016+00:00

ROOT37A/14B completas; A01guardas antesRED específicas/ASTpreimagen+UTCconfirmed; B01nestedlyrics32k→8kconfirmadoROOTAST6casos.0Critical/2Important/0Minor,sinrebatesdeuda. source126bea1b/tests71a4ea38 congelados/213payload+156readonly+559JUnit99.8407%whole0excl; resultadoshistóricos no correctedgreen.11REDfuncionales sonauténticosperoinsuficientespara guardasantesnegativos. FIX1fresh retira/reescribe despuésREDcada nuevo criterio, B01contextualsinrelajarT02/globalresource,secrecy/depthsize. T05enprogreso/M2=4/30/schemaAPIimportlibraryVerificaciónT07pending. Uso realnull.

REDoriginales reportados/verificados(ROOT), no se reatribuyen aFIX:


Cada directorio RED conserva preimagen runtime/tests, argv, UTC, stdout/stderr, JUnit,
pins antes/después e imports observados; GREEN posteriores prueban las APIs reales.
Los primeros directorios guardan 125 pins; tras extensión ROOT, los posteriores guardan 156.

- RED: `test_plan_roundtrip_all_fields_and_three_cpu_operations` falló con `NotImplementedError: CPU edit plan codec no implementado` · 2026-10-11 (`red-plan` → `green-plan`).
- RED: `test_capture_plan_revalidates_wrappers_and_preserves_synthetic_preflight` falló con `NotImplementedError: CPU plan capture no implementado` · 2026-10-11 (`red-capture` → `green-capture`).
- RED: `test_receipt_roundtrip_own_domains_measured_source_and_synthetic_claims` falló con `NotImplementedError: CPU receipt codec no implementado` · 2026-10-11 (`red-receipt` → `green-receipt`).
- RED: `test_package_roundtrip_final_ids_are_separate_from_plan_and_receipt` falló con `NotImplementedError: CPU package codec no implementado` · 2026-10-11 (`red-package` → `green-package`).
- RED: `test_package_rejects_other_final_publication_binding` falló con `DID NOT RAISE ValueError` · 2026-10-11 (`red-package-binding` → gate posterior).
- RED: `test_preview_plan_is_own_typed_namespace_without_fake_take` falló con `NotImplementedError: CPU preview plan codec no implementado` · 2026-10-11 (`red-preview-plan` → `green-preview-plan`).
- RED: `test_preview_receipt_full_roundtrip_and_attenuation_claims` falló con `NotImplementedError: CPU preview receipt codec no implementado` · 2026-10-11 (`red-preview-receipt` → `green-preview-receipt`).
- RED: `test_outcomes_reject_ready_without_receipt_and_failed_without_code` falló con `DID NOT RAISE ValueError` · 2026-10-11 (`red-outcome` → `green-dispatch-outcomes`).
- RED: `test_dispatch_exact_cpu_tuples_and_package_branch` falló con `NotImplementedError: Execution plan dispatcher no implementado` · 2026-10-11 (`red-dispatch` → `green-dispatch-outcomes`).
- RED: `test_legacy_dispatch_preserves_golden_bytes_hash_and_original_reader_shape` falló con `NotImplementedError: Legacy dispatcher no implementado` · 2026-10-11 (`red-legacy` → `green-legacy`).
- RED: `test_unknown_cpu_versions_and_cpu_to_m1_fail_with_contract_unsupported` falló con `AssertionError: None != CPU_CONTRACT_UNSUPPORTED` · 2026-10-11 (`red-unsupported` → `green-unsupported`).




## T05 codecs — FIX1 validado ROOT y revisión2 preparada — 2026-10-11T21:50:27.068934+00:00

ROOT verifica4085payloads/156readonly/2fuentespropias,87paresliteralesRED1FAIL0ERROR→reescritura→GREEN1PASS ypreimágenes/UTC/argv/JUnit. CPU748PASS0FAIL0ERROR0SKIP,whole601/601líneas61/62ramas99,8492%0omit/exclude. Source2f49f5ec/tests908195df privados; noCAS/canon. A01/B01corregidos porimplementador, aceptaciónrequierelentesfreshFULL37A14B/tablagapsoriginal. Originales559/11RED y171ciclosenforcement preservados, no sustituircausalidadliteral. T05abierto/M2=4/30/SQL/API/import/ejecutorrealpendientes. Uso realnull.

RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-262-provenance_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:38:47.964066+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-262
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-267-root_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:38:50.844010+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-267
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-271-stage_path]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:38:53.743312+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-271
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-275-final_path]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:38:56.539929+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-275
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-248-owner_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:38:59.354476+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-248
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-287-parent_ref]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:02.150268+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-287
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditPlanV2-292-role]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:04.908187+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditPlanV2-292
RED: `test_coherence_rejects_independent_invalid_binding[MeasuredCpuSourceV2-394-frames]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:07.650776+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-MeasuredCpuSourceV2-394
RED: `test_coherence_rejects_independent_invalid_binding[MeasuredCpuSourceV2-395-role]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:10.509150+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-MeasuredCpuSourceV2-395
RED: `test_coherence_rejects_independent_invalid_binding[MeasuredCpuSourceV2-396-media_type]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:13.332776+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-MeasuredCpuSourceV2-396
RED: `test_coherence_rejects_independent_invalid_binding[EffectiveCpuEdgeV2-407-map]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:16.129443+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-EffectiveCpuEdgeV2-407
RED: `test_coherence_rejects_independent_invalid_binding[ExecutedToolV2-419-runtime_verified]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:18.906378+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-ExecutedToolV2-419
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditReceiptV2-456-job_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:21.959041+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditReceiptV2-456
RED: `test_coherence_rejects_independent_invalid_binding[CpuEditReceiptV2-460-role]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:24.729622+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuEditReceiptV2-460
RED: `test_coherence_rejects_independent_invalid_binding[CpuClosureBindingV2-528-evidence_kind]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:27.469067+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuClosureBindingV2-528
RED: `test_coherence_rejects_independent_invalid_binding[CpuPublicationAuthorityV2-582-cpu_execution_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:30.310999+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPublicationAuthorityV2-582
RED: `test_coherence_rejects_independent_invalid_binding[CpuMasterMeasurementV2-601-frames]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:33.070864+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuMasterMeasurementV2-601
RED: `test_coherence_rejects_independent_invalid_binding[PreparedPackageCPU-624-receipt_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:35.873068+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreparedPackageCPU-624
RED: `test_coherence_rejects_independent_invalid_binding[PreparedPackageCPU-642-source_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:38.649682+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreparedPackageCPU-642
RED: `test_coherence_rejects_independent_invalid_binding[PreparedPackageCPU-641-reservation_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:41.550831+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreparedPackageCPU-641
RED: `test_coherence_rejects_independent_invalid_binding[PreparedPackageCPU-661-path]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:44.333549+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreparedPackageCPU-661
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewRequestV2-774-commercial_use]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:47.092363+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewRequestV2-774
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewRequestV2-753-owner_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:49.917222+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewRequestV2-753
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewRequestV2-758-role]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:52.841589+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewRequestV2-758
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewRequestV2-763-manifest_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:55.617550+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewRequestV2-763
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewPlanV2-795-request_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:39:58.379823+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewPlanV2-795
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewPlanV2-794-owner_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:01.313368+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewPlanV2-794
RED: `test_coherence_rejects_independent_invalid_binding[PreviewMeasureV2-849-gain_db]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:04.090001+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewMeasureV2-849
RED: `test_coherence_rejects_independent_invalid_binding[PreviewPassV2-863-side]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:06.864292+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewPassV2-863
RED: `test_coherence_rejects_independent_invalid_binding[PreviewPassV2-869-target_lufs]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:09.646776+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewPassV2-869
RED: `test_coherence_rejects_independent_invalid_binding[PreviewOutputV2-891-frames]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:12.452051+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewOutputV2-891
RED: `test_coherence_rejects_independent_invalid_binding[PreviewOutputV2-895-side]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:15.206897+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewOutputV2-895
RED: `test_coherence_rejects_independent_invalid_binding[PreviewOutputV2-899-media_type]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:17.978628+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-PreviewOutputV2-899
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewClosureV2-913-evidence_kind]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:20.839965+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewClosureV2-913
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-949-plan_sha256]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:23.736120+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-949
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-964-target_lufs]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:26.509788+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-964
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-974-max_lufs_delta]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:29.336085+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-974
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-995-manifest]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:32.170839+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-995
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-966-index]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:34.923407+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-966
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-982-source_parent_id]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:37.725973+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-982
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-987-path]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:40.615806+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-987
RED: `test_coherence_rejects_independent_invalid_binding[CpuPreviewReceiptV2-969-ceiling_dbtp]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:43.474771+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-coherent-CpuPreviewReceiptV2-969
RED: `test_coherence_rejects_consistently_resigned_invalid_context[provenance_execution]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:46.239541+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuEditPlanV2-253
RED: `test_coherence_rejects_consistently_resigned_invalid_context[provenance_recipe]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:48.993707+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuEditPlanV2-254
RED: `test_coherence_rejects_consistently_resigned_invalid_context[provenance_composition]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:51.867444+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuEditPlanV2-255
RED: `test_coherence_rejects_consistently_resigned_invalid_context[provenance_parents]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:54.659380+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuEditPlanV2-256
RED: `test_coherence_rejects_consistently_resigned_invalid_context[package_owner]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:40:57.503527+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-PreparedPackageCPU-648
RED: `test_coherence_rejects_consistently_resigned_invalid_context[package_job]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:00.461427+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-PreparedPackageCPU-649
RED: `test_coherence_rejects_consistently_resigned_invalid_context[distinct_parent_refs]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:03.249539+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuPreviewRequestV2-745
RED: `test_coherence_rejects_consistently_resigned_invalid_context[distinct_tools]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:06.021181+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuPreviewRequestV2-750
RED: `test_coherence_rejects_consistently_resigned_invalid_context[unique_edges]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:08.834059+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuEditPlanV2-277
RED: `test_coherence_rejects_consistently_resigned_invalid_context[output_order]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:11.761259+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuPreviewReceiptV2-954
RED: `test_coherence_rejects_consistently_resigned_invalid_context[last_peak_a]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:14.567656+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuPreviewReceiptV2-978
RED: `test_coherence_rejects_consistently_resigned_invalid_context[manifest_namespace]` falló con Failed: DID NOT RAISE ValueError · 2026-10-11T21:41:17.319850+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-correlated-CpuPreviewReceiptV2-991
RED: `test_literal_integer_fields_reject_boolean_before_pydantic_coercion[version]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:20.142598+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-literal-version
RED: `test_literal_float_fields_reject_integer_before_pydantic_coercion[ceiling_dbtp]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:23.019277+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-literal-ceiling_dbtp
RED: `test_integer_contract_rejects_each_independent_invalid_domain[True]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:25.687698+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-integer-True
RED: `test_integer_contract_rejects_each_independent_invalid_domain[-1]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:28.420733+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-integer--1
RED: `test_integer_contract_rejects_each_independent_invalid_domain[9223372036854775808]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:31.173472+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-integer-9223372036854775808
RED: `test_integer_contract_rejects_each_independent_invalid_domain[1.0]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:33.865034+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-integer-1_0
RED: `test_float_contract_rejects_each_independent_invalid_domain[1]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:36.576336+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-float-1
RED: `test_float_contract_rejects_each_independent_invalid_domain[True]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:39.339203+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-float-True
RED: `test_float_contract_rejects_each_independent_invalid_domain[nan]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:42.117854+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-float-nan
RED: `test_float_contract_rejects_each_independent_invalid_domain[inf]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:44.830613+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-float-inf
RED: `test_float_contract_rejects_each_independent_invalid_domain[-inf]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:47.536948+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-float--inf
RED: `test_encoder_rejects_large_total_payload_with_bounded_individual_fields` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:50.351722+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-encode-size
RED: `test_decoder_requires_matching_hash_before_accepting_payload` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:53.326860+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-decode-hash-functional
RED: `test_decoder_requires_object_and_canonical_bytes[scalar]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:56.030398+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-decode-scalar
RED: `test_decoder_requires_object_and_canonical_bytes[spacing]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:41:58.839154+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-decode-spacing
RED: `test_decoder_requires_object_and_canonical_bytes[newline]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:01.720192+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-decode-newline
RED: `test_cpu_array_guard_rejects_nonarray_and_excess_entries[object]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:04.567267+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-array-object
RED: `test_cpu_array_guard_rejects_nonarray_and_excess_entries[string]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:07.347932+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-array-string
RED: `test_cpu_array_guard_rejects_nonarray_and_excess_entries[excess]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:10.149443+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-primitive-array-excess
RED: `test_cpu_decoder_discriminator_is_exact[kind-wrong]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:12.927311+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-discriminator-kind-wrong
RED: `test_cpu_decoder_discriminator_is_exact[version-True]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:15.648786+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-discriminator-version-True
RED: `test_cpu_decoder_discriminator_is_exact[version-3]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:18.346184+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-discriminator-version-3
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[receipt-CpuEditOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:21.129053+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuEditOutcomeV2-receipt
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[ready_code-CpuEditOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:23.929489+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuEditOutcomeV2-ready_code
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[failed_code-CpuEditOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:26.946290+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuEditOutcomeV2-failed_code
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[cancelled_code-CpuEditOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:29.771826+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuEditOutcomeV2-cancelled_code
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[receipt-CpuPreviewOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:32.558248+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuPreviewOutcomeV2-receipt
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[ready_code-CpuPreviewOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:35.278872+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuPreviewOutcomeV2-ready_code
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[failed_code-CpuPreviewOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:37.989921+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuPreviewOutcomeV2-failed_code
RED: `test_cpu_outcome_status_binds_receipt_and_failure_code[cancelled_code-CpuPreviewOutcomeV2]` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:40.856874+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-extra-outcome-CpuPreviewOutcomeV2-cancelled_code
RED: `test_cpu_plan_rejects_valid_inference_recipe_and_matching_composition` falló con Failed: DID NOT RAISE CpuContractError · 2026-10-11T21:42:43.697401+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-final-admit-inference
RED: `test_reservation_cardinality_reports_cpu_contract_error_before_zip` falló con ValueError: zip() argument 2 is shorter than argument 1 · 2026-10-11T21:42:46.516147+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-final-reservation-cardinality
RED: `test_decoder_bytes_type_has_private_cpu_error_taxonomy` falló con app.creative.recipes.RecipeError: RECIPE_INVALID · 2026-10-11T21:42:49.328173+00:00 → GREEN1PASS; literal borrado/reescritura, red-literal-bytes-taxonomy


## Revisión de dos lentes — intento 2: T05 codecs — B02Importantnuevo — 2026-10-11T22:00:14.958411+00:00

FULL37A14B, A01TDDcorregido87literales/7482importpins, B01nestedlyrics32kcorregidoA2/B2. B02D80dict.getkind[]/{}→TypeErrorunhashableantesvalidación;baselineCPU_CONTRACT_UNSUPPORTED. ROOTASTreal2casesconfirma antesr/contextcallbacks; A2conformidaddispatchacotadaROOTanteB2. [Informe](testing/creative-persistence-codec-review2-2026-10-11.md). FIX2freshcentralguardtipoanteslookup+REDfuncional+preservar8192/32768/secrecy/depth/size/canonical/fieldsets/M1. Source2f49f5ec/tests908195df/748PASS/99,8492%históricos sinCAS. T05/M2abiertos, próximo reviewintento3/3, noSQL/API/nativeGPUmodels/librarypub. Usorealnull.


## T05 codecs — FIX2 validadoROOT y revisión3/3 preparada — 2026-10-12T04:01:09.118014+00:00

ROOT310payloads/156readonly/2fuentes50e1c0ac/de3a3c20verificados. Guardcentral exactkindstranteshashlookup, testsheredadosbyteexactos. REDlist/dictunhashable1FAIL0ERRORcada→GREEN2PASSporleyTDD. Gate757PASS0FAIL0ERROR0SKIPwhole601lines61/62branches99,8492%0omit/exclRuff0. Todosresultadosactorauditados,nuevacomprobaciónROOTNOQAindependiente. FULL37A14B/A01B01corregidos/B02candidatefix, revisión3fresh+QAantesCAS. T05/M2abiertos,noSQL/API/import/library/native/publishreal. Uso realnull.


## T05 codec — revisión3 A/B sin gaps; QA independiente liberada — 2026-10-12T04:11:21.738867+00:00

FULL37A/14B conservados, A01/B01 corregidos R2, B02 corregido R3. Scope2/fuera0/avisos0, C/D auto false. Candidato50e1c0ac/de3a3c20, QA copia158pins/156readonly; sin CAS todavía. T05/M2 abiertos: SQL/ORM/migración/API/importación/publicación/biblioteca real pendientes. [Informe](testing/creative-persistence-codec-review3-2026-10-12.md).


## T05 codec — componente adoptado tras QA independiente — 2026-10-12T04:19:36.465658+00:00

ROOT236payload/158pins/43imports/raw+JUnit/preimagesverificados; revisión3FULL37A/14B sin gaps, 757PASSWindows,whole601/601lines61/62branches99,8492%0omit/exclRuff0. CAS2fuentes50e1c0ac/de3a3c20 adoptado; fullSQL/API/importación/publicación/library/M1integration pendientes. T05enprogreso/M2=4/30. [QA actual](testing/creative-persistence-codec-current-qa-2026-10-12.md). Incidenteharnesstmpfuera raíz756+1FAILconservado, finalconfinadosinmutarproducto. Uso realnull.


## T05 persistencia — componente2A freeze legado liberado — 2026-10-12T04:27:30.867181+00:00

Trascodecaceptado, implementarindependenciadeinstall0006 yproyecciónv1 frente metadatafutura, antesdeORM/migraciónv2. Ownershiplegacy_m1_registrynuevo/cpu_publication_invariants/snapshots/test_creative_legacy_registrynuevo. TDDMIG01+PORTv1+regresionesSQLrealesprivadas; noalterarmigraciones0001..0007 ni datosbibliotecaproducción. M2T05continúacompletoSQLv2/API/publicación/integraciónpendiente, componente2Aacotadonoes cierre.


## T05 componente2A — alcance de freeze legado ampliado por RED real — 2026-10-12T04:33:32.494965+00:00

La metadataSonglive también afectainstall_dirty(fix1_invariants)yinstall(fix2_invariants): replay completoMIG01exige congelarlos, noexcepciónalcontract. ROOTlibera2helpersadicionales declaradosbajoArchivosmigrations/,6ownedtotales/211readonlybaseline215(2nuevosabsent), sinmodificarmigraciones0001..0007niBase/models. MismoTDD/whole80/review/QA obligatorio. SóloBDprivadasdelcomponente; no datosproducción.


ROOT corrección administrativa del scope2A: migrations/versions/ no incluye helpers hermanos; declarados fix1/fix2/legacy_m1_registry explícitos en ArchivosT05, sin exclusiones ni ampliar comportamientos. Primer scope rojo se conserva; fuentes privadas/frozen intactas.


## T05 legacyfreeze — candidato preparado para revisión1 — 2026-10-12T08:38:13.556130+00:00

ROOT1481payload/211readonly/6sources/inmutables0001..7/coverage5runtime80 verificados. Actor698PASS1skiphistórico y23focalPASS(4nuevostestsposteriores), noatribuir698altestSHAfinal. Private217pins/scope6fuera0avisos0,C/Dsegúnselector. Revisiónfresh/QAantesCAS; plataformaagent threadlimit rechazódespacho, nogatebypass. T05M2abiertosSQLv2/API/import/publicación/libraryrealpendientes. Uso realnull.


## Revisión de dos lentes — intento 1: M2/T05 legado2A: A/B/D sin gaps — 2026-10-12T09:01:55.245163+00:00

FULL43A14B6D0gaps,Cfalse/Dtrueconditional;actor698P1SKbefore4cases/focal23current. Apropio23/Bpropio66/DloadactualSQLbatch400constantqueries. [Informe](testing/creative-legacy-freeze-review1-2026-10-12.md). QAindependienteactual217pins6fuentes,fullfinaltestSHA703casesexpectedWindows/Linuxlegitplatform;whole5runtime80inclbranches/noomitexcl; noCASaún/T05M2abiertos.


## M2/T05 legado2A adoptado tras QA independiente — 2026-10-12T09:27:49.742785+00:00

ROOT audita1950payloads/1reparseStatOnly/217pins/63imports porplataforma, rawcoverage/JUnit/SQLitefixtures exactos. Windows702PASS1SKIP/Linux703PASS mismo703nodes y23focalactuales. Cinco runtime enteros≥80líneas/ramas/total0excl; review1FULL43A14B6D0gaps preservada. CAS6fuentes exactas adoptadas, version0001..0007 y modelo histórico intactos. [QA](testing/creative-legacy-freeze-current-qa-2026-10-12.md). SQL/ORMv2/API/Songv2/import/publicación/librarypersonal/WALbackup/restauración/PORT01full/manuales siguen pendientes: T05en-progreso/M2=4/30. GateCPU scope, noE2E/UI/GPU/audio. Uso realnull.


## M2/T05 SQL/ORM/migración2B liberación de runtime — 2026-10-12T09:36:20.886089+00:00

ROOT componente2A aceptado ypublicado e3df878; cada sourcecanónico revalidado. GraphAlembicliteral0001..0007 tiene únicohead0007, se asigna nueva0008_cpu_creative sóloahora trasausenciaverificada. Snapshotprivado/baseline/ownership10: modelo, DB/env, CPUguards, newcreativeguards/newmigration y4tests. Frozenregistryv1 yversiones0001..0007 readonly; onlyrebuildTake/Intent/Revision, CpuExecutionALTERaditivo yPREnueva, foreign_keysOFFantesBEGIN/exclusivebackuprestore/failureinjection conformecontratoa608b81f. TDD porcriterio+freshreviews/QA requeridos antesCAS, sin efectosBDproducto. FullAPI/Songv2/import/publicación/PORT01/librarypersonal/manuales pendientes, T05enprogreso. Uso realnull.


## M2/T05 migración2B — suplemento coordinador/caller real — 2026-10-12T09:48:25.440743+00:00

NEEDS_CONTEXTactor: PublicationCoordinator RLocksolo noacredita quiescence niSQLiteBEGINEXCLUSIVEenWALlectores. ROOTelige mantenimientooffline real con admisión exclusivaporproyecto compartidaporentradasconfiables y registros workers/readers/custodia reales; nohotmaintenance ni flags/dataclasscomoauthority. Scopeañade main/publication/queueRuntime/newmigration_coordinator y2tests, mismosnapshot/pinsanteswrites. Migracióna0008sin sesión nominal respaldadaporrecursosvivos/barrerareal/backuprestaurable rechaza0DDL, rawAlembicnoissuer. Autoridadnoinferirporpropiosworkersnoarrancados mientrasotra instancia puedevivir. Startupopciónobtiene sesión sólo si prueba exclusividad real ytodosgates; nofactoryporSID/path/bool. Libera admisión sólotrasDBintegrity/FKON+recursospropioscerrados, desconocidobloquea. ActornoBDpersonal/servicios niDLL/ACL/GPU. Todoproducto2BfullpendientehastaQA; ningún claimcomplete niADRratificado por scope.


## M2/T05 migración2B — retención real del lease de grupos CPU — 2026-10-12T09:58:39.235102+00:00

ROOTamplía6sources anteswrites paraquiescencecrossprocessreal: execution/custody_linux/supervisor/audio_child/newmigration_lease/newtestchildadmission. LinuxproductDocker usaMISMOarchivo flock shared de runtime/grupo vs exclusive demaintenance. FDgroup heredable retenidosupervisorhastawait/reapdetodosloshijos reales,inclparentcrash;ACKleaseantesefecto,close_exceptno pierdefd, FFmpegcierradesconocidosrequierekeeper untilwait, no confiarenleaderexit. Windowsfixturelease no acreditaWindowschildproduct,noFakeNativegrant. HistóricosSQLflagsconfirmed nuncaclosureproof. Datosfixturehistóricosnoidentidadesvivascap; BDpersonallegacy sinquiescenceissuerreal permanececerrada. RuntimepropioCPUhijoscontroladosprivateSTDnonce/argv/READY/reappermitidos; nativeespecíficosROOTdespuésfreezeaudits, GPU/modelservicios0. Totalownership22sources; no schema/DTOv1 ext parafd privado. Contract/gatesoriginales intactos,hitoabierto.


## T-05 — suplemento de lectores backup y restauración — 2026-10-12T11:42:13.928241+00:00

ROOT confirma backup.py8a677bd8 abre SQLite raw en backup/due/restore_backup sin lease de proyecto, bypass del requisito de exclusividad aunque create_db_engine ya participe. Asigna ese fichero como23º owned al actorSQL2B después del RED nativo real/preservación226sources. Debe adquirir lease real antes de efectos de backup/lector y mantenerla hasta cierre; due también tiene lector standalone. Restore conserva destino nuevo/exclusivo y admite ambos recursos durante lectura/copia, sin fabricar autoridad de migración ni adopción de histories por clonar o restaurar head7. Tests focales en coordinator/childadmission ya owned, causalRED antes de modificar runtime, full backup legacy assertions intactas y whole≥80 cada módulo cambiado. Ninguna llamada a BD/copia personal, servicio o histórico0001..7. Originalrelease/suplementos anteriores/freeze1/pins204 inmutables como entradas; nuevo suplemento declara única excepciónreadonly de este fichero. T05 completo no aceptado.


## T-05 — suplemento de fixture del ciclo histórico M1 — 2026-10-12T12:00:50.322820+00:00

ROOT confirma test_persistence_t02.pye2814ef3/37374B y test_schema_populated_migration_cycle724–738 usa rawAlembic head dos veces. Head ahora0008 exige autoridad/coordinador, y el rojo MIGRATION_AUTHORITY_REQUIRED es esperado; no se rebaja guarda para hacerlo pasar. Se asigna fichero24ºowned, cambio limitado a preparar una BD M1privada real en0007 y ejecutar ciclo histórico hasta0007 explícito, manteniendo assertTake2/Take0/FKcheck y replay poblado0001..7. Si fixture database ahora inicializa0008, se crea fixture local nuevo real para este ciclo sin degradar/alterar fixture general. Ningún otro caso/assertion se reduce o borra. 0008 tiene tests completos por entrycoordinador autorizado aparte. No es paseverde global por33passed1skip ni nuevaaceptación. TDDn/a adaptaciónfixture/test-only, evidencia regresión y sourcebefore/after obligatoria.


## T-05/SQL2B — RED nativo real de liberación del lease tras reap — 2026-10-12T12:22:00.264135+00:00

RED: `test_native_group_close_releases_project_only_after_actual_reap` falló con `MIGRATION_PROJECT_BUSY` en segunda admisión offline, DESPUÉS cierre LinuxGroup real y descendants_waited=True · 2026-10-12T12:22:00.264135+00:00. ROOT ejecutó privateDockerCPU imagen7c65/networknone/pullnever/ROsource/privatecacheRW; native prctl/pidfd y silent stdlib propios, sin audio/GPU/services. Supervisorjournal subreaper/confirmed/registered/waited y árbol real conservados. --rmCID ausente tras ejecución. Source22owned+204readonly iguales before/after; ROOT preservó226files/helper/freeze antesACK. Parent migration_admission aún abierta era causa; wire release sólo tras cierre/reap conocido ahora autorizado despuésRED. No claim de custodia audioFFmpeg o libraryreal porfixture silent.

Recibo `.cache/dev-cycle/m2/creative-persistence-native-close-red-root-20261012/ROOT-native-close-RED.receipt.json`; rawargv/stdout/stderr/tree/journal/receipt/pinsinmutables. Actor24owned tras suplementosbackupreader23/historicalcycletest24, fullSQLguards/NativeGREEN/actualCPUv2PUBfixture/coberturas/reviewQA/migraciónpersonal siguen pendientes. T05 completo abierto, no checkboxverde ni head8rawpermission.


## T-05 SQL/ORM2B — GREEN nativo causal de admisión Linux — 2026-10-12T12:47:38.042734+00:00

RED causal ROOT anterior continúa inmutable: después reap real el parentFD retenía lease y MIGRATION_PROJECT_BUSY. GREEN ROOT en copia fresca independiente `creative-persistence-native-close-green-frozen-root-20261012`, freeze5c9d79b8c4db8e40ae3fa4f6ea1b50608c68630e620cd1d50e1c28557d8a21b8:226sources/24owned/202readonly +harness/four supplements auditados. AST del nodo `test_native_group_close_releases_project_only_after_actual_reap` exactamente igual al RED; módulo custody_linux.py sólo añade cierre de migration_admission después terminate/wait/reap de árbol propio. La prueba real DockerLinux de ROOT dio1passed/exit0: busy con grupo vivo, `close(5)`/descendants_waited y después `exclusive.require_live` exitosos. Journal real subreaper/confirmed/registered/waited, container--rm conocido eliminado,226sourcesafterequal. Receipt `.cache/dev-cycle/m2/creative-persistence-native-close-green-root-20261012/ROOT-native-close-GREEN.receipt.json`, SHA d746b7884364107f3cf589475f70317792280163210ab94cb716bd4128e3800c;argv/UTC/raw/tree/journal/ownCIDabsence preservados. ImagenCPU existente/networknone/pullnever/sourceRO/cacheRW, nadaGPU/audio/FFmpeg/servicios. No se ejecutó original mutable; GREEN sólo atribuido a copia exacta.

Hallazgo posterior ROOT de corte de cierre delease queda abierto para REDCPU: custodyLinux410–414 marca closed/elimina registry antes GroupAdmission.close, que llamaos.close y puede lanzar. Un fallo antesACKdellease permitiría retrygroup.close=True con descriptor aún retenido. Actor debe verificar/reparar con causalRED y conservarunknown/retención/registry; la pruebaGREEN normal no cubre este corte. No cerrar fullgroupcustody por normal1PASS.

Raw privados adicionales inspeccionados por ROOT, ejecución CPU del actor sin claimROOTNative: regression-migration-full-fault-current16passed223.52s; regression-backup-legacy-cycle-current34passed1skipped25.19s; green-denied-fk-recovery-error1passed1.47s. Son preimágenes/fuentes de cada recibo, no cobertura de cambios posteriores ni aceptación de toda2B. DOWNfullfault/startuplegacy7bajoEX/rutaaudio-keeper-FFmpeg/PUBauténtico/wholecoverage≥80/freshrevisiónQA/CAS/fullT05/M2 pendientes. Mantener0001..0007/3rebuilds/CPU-PREaditivos/backupreal/autoridadnoautodeclarada. T05 y objetivoM0–M5 activos, sin cerrarhitos; métricasIAactualnull.


## T-05 — suplemento de seis preparativos de regresión histórica — 2026-10-12T14:04:24.161029+00:00

ROOT revisó el JUnit del ciclo legado actual: 28FAILED/674PASS/1SKIP, no verde global. Se asignan seis ficheros privados de tests adicionales (30 owned, 196 readonly, 226 fuentes); el código canónico permanece intacto. Cambios limitados a las funciones nominadas en legacy-regression-tests-scope-supplement-root.receipt.json y sus preparativos locales: BD M1 real hasta0007 explícito, mapper Take legado congelado sólo donde la BD histórica lo requiera y restaurado al salir. Se conservan todas las aserciones de DDL/SHA, filas, proyecciones, FK, FTS, custodia, JSON, rollback y revisiones0001..0007. No rebajar el head global0008 ni las guardas de autoridad/coordinador. El caso startup debe presentar autoridad real del preparativo propio antes de AppFactory, nunca un flag Creator; snapshots.restore_new y demás runtime fuera del ownership siguen readonly. Si no basta el preparativo, se registra el fallo causal y se pide contexto al orquestador. El fichero ya owned test_attempt_json_guard_upgrade.py puede usar preparativo local0007 manteniendo los tres casos históricos y toda comprobación de rollback/guardas. TDD n/a: adaptación de tests/preparativos; la regresión posterior y comparación exacta de fuentes son obligatorias, sin reclamar cobertura productiva por modificar tests.

Se conserva además la incidencia del harness anterior --noconftest sin --basetemp: 1FAILED/756PASS escribió preparativos en Temp del usuario, fuera del proyecto. No cuenta como pase confinado; no se borra Temp compartido. El segundo intento tuvo seis errores de setup. El tercero, regression-codec-all757-confined-process, pasó757 con basetemp/TMP/TEMP/TMPDIR propios; no sustituye las evidencias fallidas. Ninguna BD personal, audio, GPU ni instalación se tocó. Las copias congeladas anteriores y sus helpers siguen inmutables.


## T-05 SQL/ORM2B — ROOT RED causal de admisión de hoja Linux — 2026-10-12T14:08:57.345895+00:00

Copia congelada d0775de5d81f375e058b7c929d74a59f1eaecd8f9c5c822416bab1cec9d369c4,226sources24owned202readonly: ROOT ejecutó dos casos del nodo test_native_audio_leaf_admission_requires_actual_owned_kernel_tree. Árbol stdlib propio leader→keeper→leaf, nonce/READY/gates, parent/birth/PGID comprobados en kernel antes de abrir pidfd propios leader/keeper; ambos llegaron al stub NotImplementedError CPU_AUDIO_LEAF_KERNEL_ADMISSION_NOT_IMPLEMENTED y dieron2FAILED/exit1 causal. Imagen CPU propia existente/networknone/sourceRO/cacheRW, sin audio/FFmpeg/prctl/GPU/servicios/procesos ajenos. Fuente226afterequal y container--rm eliminado. Receipt .cache/dev-cycle/m2/creative-persistence-native-audio-leaf-red-root-20261012/ROOT-native-audio-leaf-RED.receipt.json SHA4ee2ab198431278fcae549b1e9b2f091343b231c0469e32cec09258ad6677d20.

Límite explícito: RED se corta antes de exportación JSON de árbol/reap por descendiente; finally envíaR y espera al líder/cierra streams y pidfd, pero no existe recibo independiente por cada descendiente. No se declara custodia completa conocida. ROOT autorizó implementación trasRED, actor no ejecutará Native. GREEN posterior necesita copia nueva y parent/birth/PGID y anclajes pidfd/fdinfo/fstat reales antes/después, recurso pendiente bajo unknown y ACK sólo tras registro real. SQL continúa aparte, ahora30owned/196readonly tras suplemento seis tests históricos exactos; revisión703 todavía28FAILED/674PASS/1SKIP, no verde global.


## T-05 SQL/ORM2B — GREEN admisión kernel y RED protocolo keeper/leaf — 2026-10-12T15:31:21.635456+00:00

ROOT obtuvo2PASS reales con freeze9520f399 de admisión hoja normal/birth: árbol propio/nonce/kernel parent-birth-PGID/pidfd, waitpid hoja/keeper y waitleader0, FDcount restaurado y lease exclusivo require_live después del cierre. Fuente226igual,30owned196readonly, contenedor CPU --rm eliminado. Recibo .cache/dev-cycle/m2/creative-persistence-native-audio-leaf-green-root-20261012/ROOT-native-audio-leaf-GREEN.receipt.json SHA1ae6e89ad9486779c63c1cbc57a11661b0c5eb28a2ed31ca7c20a5c48bbcabce. No prueba de audio/FFmpeg completo. Post-audit ROOT buscó inicialmente journal en subcarpeta equivocada; finalizador audit-only encontró ambos journals propios bajo.cache y preservó fallo, sin repetir Native.

Protocolo keeper/leaf freeze3d2ca9df: ROOT ejecutó2casos normal/status que llegaron causalmente a NotImplementedError CPU_AUDIO_LEAF_PROTOCOL_NOT_IMPLEMENTED;2FAILEDexit1 con fuentes226iguales, contenedor propio eliminado. Recibo .cache/dev-cycle/m2/creative-persistence-native-keeper-leaf-protocol-red-root-20261012/ROOT-native-keeper-leaf-protocol-RED.receipt.json SHAeede9ae94c321b0c2a47cfe8d0361954f0c6d1e965bd764e785e3938bca80a68. Stub corta antes de journals de éxito, límite explícito:finally envíaREW restante,waitleader y closes propios; no se declara custodia completa. ACK autoriza sólo implementación privada de protocolo después de RED; Native posterior sólo ROOT sobre nuevofreeze. Regresión histórica actor702PASS1SKIP376.35s,26focal+4startupPASS, pendiente auditoría final/cobertura/revisiónQA/CAS y fullSQL/PUB/dual-slot/audio.


## T-05 SQL/ORM2B — protocolo kernel GREEN2 independiente — 2026-10-12T15:41:24.680041+00:00

ROOT auditófreezeGREEN2fa4a15b2/226sources30owned196RO y ejecutó dos casos keeper/leaf reales:normal registra3anchorsleader/keeper/leaf,pidfdZ/birthparentPGID/status0,E despuésexitreal,W sólo despuésfdinfoPid-1 ycloseACK antesretirarregistro,reaped_count1; EXrequire_live despuésclose. Wrongstatus1 frenteactual0 rechaza yretieneUNKNOWN/leafFD/registro/reaped_count0,noEXproductorecoveryclaim; fixtureownOSreap cierraFDpropios despuéswaitleader/keeper/leaf0. FDcountafter=before,noncecadaárboldistinto,todasfuentes226iguales/30preimages196readonly; ownCPUcontainer--rmremoved. Recibo .cache/dev-cycle/m2/creative-persistence-native-keeper-leaf-protocol-green2-root-20261012/ROOT-native-keeper-leaf-protocol-GREEN.receipt.json SHA6d223efa8eb4f28353effe8956fdca8eee822a9059e389b1b4a8cd11e5038cd2. CandidatepreauditGREEN1importselectfaltante conservado y corregido antesROOTexec, noRED/GREENclaimdeproducto. ACKactor sólo privado, fullsupervisor/audio/FFmpeg/PUB/sqlcoverage/revisiónQA/CAS pendientes. ROOTauditoría histórica703confirma702PASS1SKIP/JUnit703zeroerrorsfailures/30preimage196readonly; nofuenteactualmutable ni full2Bclaim.


## T-05 SQL/ORM2B — RED causal del supervisor real — 2026-10-12T16:06:50.035098+00:00

ROOTfreeze b505ee38/226sources30owned196RO: audio_supervisorreal en hijopropio CPUcontainer,prctlsubreaper sóloesehijo,pidfd/registry/cleanupguardasintactas. Fixture sustituye únicamenteexecveleader trasargvexactcheck por árbolstdlibnonce con keeperreal run_registered_admission_keeper; IDs/hash modelled NOplan/SourceVerified/grant,audioFFmpeg0. Actualsupervisorregistrakeeper pero rechaza register_leaf porsecuencia:1FAILED registered_count1!=2 causal,noREADY. JournalconfirmedFALSE; own supervisorwait0, FDcountbeforeafterigual yEXfixtureactualsólodespuésownOSwaitparentdescriptorclose, NOpromoverUNKNOWN a knownproductrecovery. Contenedor--rmremoved,todasfuentes226prepostiguales. Recibo .cache/dev-cycle/m2/creative-persistence-native-supervisor-route-red-root-20261012/ROOT-native-supervisor-route-RED.receipt.json SHA7637bbc92933914800496d95776481a7cc5cba4ccc434e3db5facf55e7fa4e4a. ACKautorizawiringprivado despuésRED haciahelperkernel ya probadoGREEN2; actualGREENnuevo debeROOT-onlyfreshfreeze/nodoexacto; fullaudio negativo/restart/custody/PUB/coverage/RQA/CASpendientes. ActorCPU201→216PASS parciales schema/ORM/coordinator,startup/migration20PASS2loopexhaustivosdeselect, últimasguardasfuturocounter/unitnogrants; todavía nofullfaultmatrixlatest.


## T-05 SQL/ORM2B — causa raíz del supervisor acreditada — 2026-10-12T16:54:04.001126+00:00

GREEN candidato9ab falló realmente:1FAILED registered_count1!=2; no Timeout ni READY. Fuentes226 verificadas después y contenedor propio eliminado; ROOT-failed-GREEN-qualification.receipt.json conserva fallo sin crédito verde. Aplicación a demanda de custom-agents:debug-root-cause, fases1–3. Diagnóstico real dd7631d30: mismo producto225fuentes, único driver test con sys.setprofile sólo lectura. Leader pidfd4 válido pasa anchor; keeper pidfd1 válido anon_inode:[pidfd]/fdinfoPID/fstat real retorna en línea693 por descriptor<3. Supervisor había cerrado0/1/2; reutilización kernel1 legítima prueba hipótesis, no fallo de transporte ni identidad kernel. Recibo .cache/dev-cycle/m2/creative-persistence-native-supervisor-route-descriptor-diagnostic-root-20261012/ROOT-cause-proved.receipt.json.

ACK fix mínimo privado: pidfd tipo int exacto no negativo, manteniendo readlink/fdinfo/birth/PGID/identidad completos; transportlease>=3 es distinto y no cambia. Regresión causal/freeze fresco sin observer temporal/GREEN ROOT todavía pendientes. Árbol stdlib propio no certifica audio/FFmpeg/ToolPlan/SourceVerified/publicación. Custodia UNKNOWN/SQLwhole/faultmatrix/review/QA/CAS/T05/M2 abiertos.


## T-05 SQL/ORM2B — supervisor real GREEN2 — 2026-10-12T17:07:38.303669+00:00

ROOT freeze65547546/226fuentes30owned196RO actual:1PASS,2registered=2reaped/confirmed/descendants_waited, READYstdlibpropiosólodespuésACK. Mismo nodo ASTexact9ab/b505, sinobserver temporal; supervisor sólodescriptor<3→<0 despuéscausa acreditada. OwnOSwait0/FDcountsrestored/EXfixtureafterclose/containerremoved/todasfuentesprepostexactas. Recibo .cache/dev-cycle/m2/creative-persistence-native-supervisor-route-green2-root-20261012/ROOT-native-supervisor-route-GREEN2.receipt.json. El fallo9ab ydiagnósticodd7631 se conservan; no equivocarlosconGREEN.

ROOT preflight inicial suponíauna fuente/whole-testSHAexacta:fallóantescrearhelper/area/Native. Actualfreeze6554incluye cincofuentes:guardmínimo, invariantsJSONtypeoftext, audio_childkeeperwiring yaTDD, añadido testlauncher yschemaBLOBnegativos; ROOT leyó todosdiff5 yadaptóharness aASTdelnodointacto,nocódigo. Fuenteactual6554PREPOSTpropia seobserva, no retag9ab. No fullaudio/FFmpeg/ToolPlan/SourceVerified/ready/render/closureproductocredit porárbolstdlib. Regresiónfull703/757/faultmatrix/cobertura/review/QA/CAS aún pendiente; actor congela30durante suite. Debug-root-cause fase4 regresiónmínimaGREEN pero suitesintegrales/candidato gotcha pendiente.


## T-05 SQL/ORM2B — regresiones auditadas y descriptores kernel bajos — 2026-10-12T18:14:12.908507+00:00

ROOT auditó ejecución completa702PASS1SKIP (703casos),757PASS y matrizUP/DOWN22PASS sin deselect de sus dos bucles exhaustivos. JUnit/raw/SHA/30preimágenes/196readonly contrastados. Después se modificaron lectores e invariantes privados; esas tres ejecuciones se conservan como históricas de sus perfiles, no verde de las nuevas fuentes. Actor30owned continúa lectores coherentes COMMITTED/owner/song/plan/batch/ordinal y refreshparcial, equivalenciaSQL/ORM, lint local y cobertura; no alterar migraciones históricas ni conceder SourceVerified por datos modelados.

ROOT ejecutó12casos kernel reales del descriptor pidfd0/1/2: tres válidos y nueve negativos (bool/negativo/no-pidfd), procesosstdlib propios en contenedorCPU aislado, sinGPU. Nonce/birth/parent/PGID/pidfd, wait propio, restauración stdio, FDcounts y cierre real comprobados;226SHA PREPOST iguales, contenedor propio retirado. Freeze5b08b85b/recibo creative-persistence-native-low-pidfd-root-20261012/ROOT-native-low-pidfd.receipt.json. SupervisorGREEN2 anterior y causa pidfd1 se conservan. No certifica audio/FFmpeg/ToolPlan/PUB ni supervisor completo. Falta prueba causal de cleanup dual-slot UNKNOWN, perfil final estable/suites/whole80/revisión/QA/CAS. T05/M2 abiertos.


## T-05: custodia UNKNOWN real y regresiones nativas actuales — 2026-10-12T19:13:31.978219+00:00

ROOTREDf83 real1FAILED causal:2registered/confirmedFalse/reaped0, faltaban keeper+leaf en inventarioUNKNOWN. OwnOSwait0/FDrestaurados/EXfixtureafterparentclose/226SHAexactos/containerretirado. ActorCPUclose/querycuts2RED→2GREEN yfixcaptura nominal/identidad/parent/PGID +finallysignals/wait/closeACK reales. ROOTpreaudit6aa6 detectó helper despuésentrypoint: importfixtureocultaríaNameError de script; noSDK6aa6, fuenteinmutable conservada y funciónreordenadabodyexacto antesmain. Nuevofreeze8e96.

ROOT8e96UNKNOWN1PASS con ambosrefsactuales retenidos/confirmedFalse/sin avanzarWcounter porcleanupOS, y mismo8e96 normal+lowpidfd13PASS:normal2registered=2reaped/confirmed/descendants_waited;12pidfd0/1/2valid/invalidactuales. Todosownwait/FDrestore/EXfixtureafterclose/226SHAprepostexactos/container--rmremoved. Total14casosNative actuales sobre8e96. Recibos unknown-green2-root/ROOT-native-supervisor-unknown-GREEN2.receipt.json yunknown-regressions-root/ROOT-native-regression.receipt.json. SinFullaudio/ToolPlan/SourceVerified/PUB/Ready ni productUNKNOWNrecovery porfixturestdlib.

Actor continúa30owned196readonly:equivalenciaDTO↔SQL necessary-shape/relaciones con JSON UNIT deliberadamente malformado y discriminantesmeasured/truecomo datosrechazados, nunca plan_wire(verified=True) ni emisorauténtico. WholeWindows267PASS33SKIP/JUnit300 actualperfil anterior a nuevospreview/package/reader/4assetguard, sin80claim ynoNativeactors.703/757/22fullfaultmatrix históricos conservados, no retag nuevosperfiles. Remainingrawcrypto/assetreciprocal/finalprofilewhole80/RQA/CAS;2Bpersistencia no satisfacecapturadorT07/writeratómico todavía.


## Parada solicitada tras la última suite — 2026-10-12T19:32:07.616370+00:00

Última suite de cuatro ficheros: 376 PASS, 33 SKIP, 0 FAIL, 0 ERROR;52,08s, JUnit409 y exit0. ROOT coteja raw, XML,7artefactos y226 fuentes finales:30owned/196readonly exactas. Checkpoint privado `creative-persistence-t05-schema-runtime-20261012/checkpoint-stop-last-suite-20261012.json`, SHA6b9d2e7feb73c090fdd4bd360a6b92ac28bf5cf8f5c7580f4455ca89d73a01cb. Ambas sesiones propias de estas pruebas terminaron; el actor confirma ninguna prueba propia activa y ningún cambio posterior.

El fallo anterior42FAIL/333PASS/33SKIP queda conservado: CREATE TRIGGER compuesto tenía una coma rechazada por un paréntesis extra. Reproducción realDDL1RED→1GREEN y14focalPASS; el fix cambia sólo un delimitador en invariants. La suite final comprueba la corrección sin sustituir la cobertura exigida:≥80por cada módulo,703/757/22 sobre fuentes finales y revisión/QA/CAS aún pendientes. Native14freeze8e96 es evidencia separada limitada, sin audio/FFmpeg/PUB/SourceVerified auténtico. No cierre T05/2B ni crédito a capturadorT07. Parada explícita del propietario; no se inicia más trabajo.
