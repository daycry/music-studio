---
estado: en-progreso
candidato: false
verificacion: obligatoria
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
# ventana compartida con improvement-plan.md
---

# Checklist de Tareas — M3: producción, portada y vídeo con letra

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-10-11 |
| **Plan** | [improvement-plan.md](./improvement-plan.md) |
| **Diseño** | [design.md](./design.md) — opción O1 |

> **⚠️ Ledger canónico de progreso.** Tras adopción, este fichero es la **fuente única de verdad** del avance del plan. Sólo ROOT, como orquestador, marca aquí cada tarea (checkbox + estado) y actualiza el resumen. Los subagentes entregan candidatos y evidencia por SHA; no escriben el ledger. No existen otros ledgers de progreso.

> Plan incorporado por ROOT. El orquestador registra el progreso; todas las tareas permanecen pendientes hasta sus verificaciones.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|---|---|---|---|---|---|---|---|
| Fase 1 — Contratos y decisiones previas al RED | 5 | 11 | 45% | — / 130h | — / n/a | — / n/a | — / n/a |
| Fase 2 — Autoridad, datos y publicación | 0 | 3 | 0% | — / 60h | — / n/a | — / n/a | — / n/a |
| Fase 3 — Stems, mixer y exportación de audio | 0 | 4 | 0% | — / 96h | — / n/a | — / n/a | — / n/a |
| Fase 4 — Análisis, alineación y karaoke | 0 | 3 | 0% | — / 76h | — / n/a | — / n/a | — / n/a |
| Fase 5 — Portadas Comfy y uploads | 0 | 2 | 0% | — / 52h | — / n/a | — / n/a | — / n/a |
| Fase 6 — Escena N0, renderer y montaje | 0 | 3 | 0% | — / 88h | — / n/a | — / n/a | — / n/a |
| Fase 7 — Audio propio, calidad alta y presets | 0 | 3 | 0% | — / 72h | — / n/a | — / n/a | — / n/a |
| Fase 8 — Portabilidad y biblioteca | 0 | 4 | 0% | — / 120h | — / n/a | — / n/a | — / n/a |
| Fase 9 — Recovery, GPU y runtime offline | 0 | 2 | 0% | — / 52h | — / n/a | — / n/a | — / n/a |
| Fase 10 — Conformidad real y evaluación humana | 0 | 6 | 0% | — / 164h | — / n/a | — / n/a | — / n/a |
| Fase 11 — QA global y cierre | 0 | 1 | 0% | — / 20h | — / n/a | — / n/a | — / n/a |
| **TOTAL** | **2** | **42** | **5%** | **— / 930h** | **— / n/a** | **— / n/a** | **— / n/a** |

Las horas son orientativas base, confianza baja; total con +20 %:1116h. Economía n/a por ADR0001, tarifa0€/h; tokens/horasIA/supervisión/productividad no estimados ni medidos. Jira/Confluence desactivados.

## Puertas comunes y orden de ejecución

- ROOT aprueba/adopta el plan y cada decisión D01–13. Una lectura no ratifica un umbral propuesto. D01 es O1 ya aprobada; T01 sólo verifica trazabilidad y disponibilidad.
- T01–11 son contratos/spikes previos al RED dependiente. Prosa: TDD n/a. Un spike con lógica propia sí exige RED causal y gates. Descargas, GPU y provisión requieren ejecución futura controlada, nunca esta planificación.
- ADR0037 permite T02–09, schemas puros y escena aislada con contrato ratificado aunque M1/M2 sigan abiertos. T12–14/17/25/30–34 requieren seams M1/M2 liberados por SHA y ROOT; si falta uno, no empiezan su integración ni cierran por fixture.
- T10/T11 requieren M0/gates y turno GPU real cuando se ejecuten. D06/D13 preceden RED de cada método; D07 precede RED renderer; D08 precede RED import; D09 precede RED backup/activación.
- Cada comportamiento se ejecuta con TDD causal: prueba que falla por comportamiento ausente → código → verde → refactor; conservar comandos, error, UTC y SHA. Código escrito antes del test se reescribe tras el rojo.
- Al cerrar cada fase: orquestador registra salidas de Verificación, Ruff/formato, contrato generado y tests de regresión. Cobertura oficial de todos los ficheros cambiados ≥80 %, sin omit/exclude para aumentar porcentaje; base de fase fijada por SHA, no el checkout compartido completo.
- Gate por fichero: aplicar el procedimiento reproducible «Cobertura estricta de fase» inferior a cada paquete/engine cambiado y apps/web. ROOT resuelve STUDIO_PLUGIN al plugin1.21.1. El helper con `--json` es diagnóstico: su media y su exit0 nunca sustituyen el cotejo completo de informes oficiales con el inventario ROOT; missing/avisos no son verde y herramienta ausente/exit2 queda pendiente.
- Orden de aceptación: contratos ratificados y seams liberados → instrumento y artefacto candidato listo → evaluación y acta humana → revisión fresca y QA independiente → ROOT cierra la tarea. Las tareas que necesitan actas permanecen en-progreso o en-revision hasta reunirlas. T01–11 registran concreciones; no exigen que las tareas de conformidad dependientes ya estén cerradas. M2 cerrado y gates heredados siguen siendo requisitos finales de M-01/M-49 y T-42; T-42 permanece abierto hasta reconciliar actas, matriz y QA.
- Tests JS/escena y engines nuevos requieren runner/cobertura oficial en sus package.json/pyproject y lock. No instalar fuera del proyecto; ninguna instalación en Python de máquina.
- Contratos code-first: `uv run python scripts/export_contracts.py --check` y `pnpm --dir apps/web gen` conforme CLI vigente comprobada antes de ejecución; si --check no existe, comparar regeneración en copia privada byte a byte. DTO M1/engine-v1 compatibles y schemas históricos intactos.
- Contrato API: ejecutar openapi-lint.py sobre packages/contracts/openapi.json y --diff contra snapshot de fase; exit0 y ruptura explicitada antes implementar. No crear API-xx smoke ni A11Y-xx sin opt-in; los negativos HTTP son tests unitarios/integración obligatorios.
- Revisión fresca A/B por fase; C/D seleccionadas por script auto. QA independiente y qa-gate, nunca autoaprobar. Errores repetidos usan debug-root-cause; alcance no se rebaja.
- Salidas se registran por SHA/versión/método/entorno. Fixture/CPU no marca GPU, ext4, FFmpeg, navegador ni escucha humana como cumplidos. Cada Changelog se escribe al cierre, no se inventa ahora.

## Cobertura estricta de fase

Contrato de implementación futura en T-06: `scripts/m3_coverage_gate.py` y sus pruebas `tests/test_m3_coverage_gate.py`. El script aún no existe ni se ha ejecutado como producto. La instrumentación se prepara y prueba sobre su candidato antes del cierre de Fase 1; prosa/config/test-only se exceptúan explícitamente, nunca lógica de producción del propio gate.

ROOT fija `$env:M3_PHASE_BASE` y `$env:M3_PHASE_DIR` en una copia privada de fase, además del SHA candidato. Genera `changed-inventory.json` comparando ambos árboles completos: todos los paths añadidos/modificados/eliminados, SHA base/candidato, stack/paquete, clasificación producción/test/config/prosa y motivo de cada excepción. Renombres conservan ambos paths; código nuevo/untracked se incluye. Producción eliminada requiere justificante de eliminación; todo fichero de producción vigente cambiado se mide completo, no sólo líneas del diff. ROOT verifica que el inventario reproduce la diferencia byte a byte; no se toma el diff del checkout compartido. Ningún fichero queda fuera de stack/inventario por el filtro del helper.

En esa copia, con entorno gestionado cargado y dependencias ya bloqueadas, repetir por cada stack/paquete afectado (variables ROOT con rutas reales del candidato):

```powershell
. ./scripts/env.ps1
uv run --frozen --no-sync --all-packages python -X utf8 -B "$env:STUDIO_PLUGIN/skills/unit-tests/scripts/coverage-gate.py" $env:M3_PACKAGE --min 80 --changed-only --base $env:M3_PHASE_BASE --json --runner $env:M3_COVERAGE_RUNNER > "$env:M3_PHASE_DIR/helper.json"
$helperExit = $LASTEXITCODE
uv run --frozen --no-sync --all-packages python -X utf8 -B scripts/m3_coverage_gate.py --inventory "$env:M3_PHASE_DIR/changed-inventory.json" --reports "$env:M3_PHASE_DIR/official-reports.json" --helper "$env:M3_PHASE_DIR/helper.json" --helper-exit $helperExit --min 80 --json > "$env:M3_PHASE_DIR/strict-gate.json"
```

`M3_COVERAGE_RUNNER` se congela con argv, cwd, entorno, UTC, SHA y exit en `official-reports.json`: pytest usa `uv run --frozen --no-sync --all-packages python -X utf8 -B -m pytest --cov=<raíces producción del paquete> --cov-report=json:<paquete>/coverage.json` más los nodos de prueba ratificados; Jest usa su binario local `jest --coverage --coverageReporters=json --coverageReporters=json-summary`; Vitest usa su binario local `vitest run --coverage.enabled --coverage.reporter=json --coverage.reporter=json-summary`. No se usa npx con descarga implícita. Cada runner produce el informe esperado por el helper y el raw completo (coverage.py JSON o Istanbul `coverage-final.json`) con contadores por fichero; el registro enlaza informes, configuración efectiva e inventario por SHA. Múltiples plataformas se reportan por separado y, si el contrato requiere unión, mediante herramienta oficial de combinación, conservando los raws; ninguna media sustituye esa unión.

El gate estricto valida esquema, recibos de ejecución exit0 y hashes, SHA base/candidato, inventario completo y configuración efectiva de cobertura sin omit/exclude/ignore/pragmas que reduzcan producción medida. Comprueba mapas y contadores oficiales, incluidas `excluded_lines` y source maps JS, contra las fuentes completas del inventario. Cada path debe corresponder de forma exacta y única a un fichero raw del stack; aliases/sufijos ambiguos, missing, unmeasured, denominador cero en producción, datos stale o cualquier exclusión/omisión se rechazan. Cobertura whole de líneas/statements por fichero se calcula de contadores sin redondear y debe ser ≥80; se conservan mínimos de ramas adicionales si el contrato de fase los exige. No se usa ni la media ni `detalle.ficheros` redondeado como autoridad. Helper exit0 con avisos/missing no da verde; exit1 da rojo y exit2 o herramienta/report ausente deja pendiente. Se verifica que reports cubre todos los stacks declarados y que no hay una excepción producción encubierta como test/config/prosa.

CLI del gate: `--inventory` recibe el inventario ROOT completo; `--reports` el registro de raws/recibos/configuración por stack; `--helper`/`--helper-exit` el diagnóstico conservado; `--min 80` y `--json` son obligatorios. Exit0 sólo si todo fichero de producción vigente cambiado medido cumple; exit1 para incumplimiento/exclusión/ambigüedad o ausencia de un fichero en un raw existente; exit2 para herramienta/report/recibo ausente o inválido (pendiente). Inventario válido sin producción devuelve exit0 con `applies:false` y excepciones explícitas, nunca un porcentaje inventado. El JSON enumera todos los paths, contadores, porcentaje exacto, exceptions, missing, ambiguous, exclusions, stacks y veredicto; no permite aprobar entradas desconocidas o no clasificadas.

Verificación futura reproducible: `uv run --frozen --no-sync --all-packages python -X utf8 -B -m pytest tests/test_m3_coverage_gate.py` → casos independientes con raws oficiales y recibos: 70/100 da exit1 aunque helper promedio85/exit0; 100/100 da exit0; missing da exit1 aunque helper exit0; ningún fichero medido con producción da exit1; sin herramienta/raw da exit2 pendiente; inventario vacío de producción validado da exit0/applies:false; ambigüedad/exclude/omit/source-map inválido/stack no cubierto/SHA stale/80 redondeado desde79,999 dan no-verde. Antes de implementar el script, TDD exige RED causal; estos casos son criterios del plan, no resultados obtenidos.

## Fase 1 — Contratos y decisiones previas al RED

**Estado**: en-progreso · **Estimado**: 130h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-01 — Liberar seams M1/M2 por unidad

- **Descripción**: Releer las fuentes liberadas de M1/T05 y M2: storage, bootstrap, lifecycle, compositor, publicación, migraciones, DTO y UI. Registrar SHA y contrato usable por unidad.
- **Estado**: completado
- **Tiempo humano**: est. 6h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: plan adoptado y decisión ROOT; D-01, D-12 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/dependency-contract.md`, `docs/arquitectura/iteracion-creativa.md`
- **Cubre (tests)**: M-01, M-48
- **Verificación**: lectura: dependency-contract.md → cada seam tiene autoridad, versión, gate y liberación ROOT; M1/M2 abiertos figuran como tales.

**Criterios de aceptación**

- [x] Tabla explícita disponible/no disponible con SHA y gate, sin convertir T02 puro en producto M2.
- [x] CA-01: — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [x] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [x] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [x] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

**Verificación ejecutada ROOT** (2026-10-11T17:42:04.104230+00:00): lectura dependency-contract.md →25seams con autoridad,versión,SHA,gate y liberación/no disponibilidad;77fuentes históricas y78pinsQA autenticados. D12ratificada conformeADR0037, M1/M2 abiertos explícitos. Revisión1A/B sin gaps yQA422/422 controles/gateoficial0. [Informe vigente](testing/dependency-contract-current-qa1-2026-10-11.md). Cierre documental; ninguna función ni CA producto se acepta aquí.

- **Changelog**: Documenta qué componentes y contratos pueden consumir las funciones de producción y qué validaciones siguen pendientes.

### T-02 — Concretar ProductionRequest y autoridad por sujeto

- **Descripción**: Cerrar discriminantes de operación, recipe/hash, captura privada, roles, revisiones, perfiles, recibos e intenciones para Asset/Analysis/Artwork/Render/Export/import/backup. No adaptar PostPlan con una inferencia ficticia.
- **Estado**: completado
- **Tiempo humano**: est. 10h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01; D-02 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/datos.md`, `docs/decisiones/ADR-0082-peticion-privada-de-produccion-y-autoridad-por-resultado.md`, `docs/decisiones/README.md`
- **Cubre (tests)**: E2E-02, E2E-44, M-48
- **Verificación**: lectura: production-request-contract.md → ejemplos válidos e inválidos por sujeto y decisión ROOT trazada.

**Criterios de aceptación**

- [x] ROOT ratifica tabla campo/tipo/versión/owner/terminal/CAS y fallos por frontera antes de T12/T14.
- [x] CA-02: — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [x] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [x] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [x] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

**Verificación ejecutada ROOT** (2026-10-11T19:03:55.596469+00:00): lectura production-request-contract.md →7sujetosconcasosválidos/inválidos,19parejas,campos/tipos/versiones/owner/terminal/CAS/fallos y elecciónPR-O1 ratificados. ROOTautentica317payload/81snapshot/79guards sellados,2prefijosbyteexactos,138enlaces/131unique yQA403/403/gate0. [Informe vigente](testing/production-request-current-qa1-2026-10-11.md). ADR0082/apéndicesadoptados; sólo contrato,34E2E/15manuales/runtimependientes.

- **Changelog**: Fija una petición privada única de producción con autoridad, revisiones y recibos propios para cada resultado y conserva los contratos históricos.

### T-03 — Concretar migraciones y revisiones inmutables

- **Descripción**: Fijar MixRevision, LyricsTimingRevision, producción/publicación, FK/unique/CAS y pertenencia. Preservar baseline y excepción delimitada ADR0074.
- **Estado**: completado
- **Tiempo humano**: est. 10h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01, T-02; D-03 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md`, `docs/arquitectura/datos.md`, `docs/decisiones/ADR-0083-persistencia-tipificada-y-revisiones-inmutables-de-produccion.md`, `docs/decisiones/README.md`
- **Cubre (tests)**: E2E-02, E2E-08, E2E-18, E2E-20, E2E-34, M-48
- **Verificación**: lectura: production-data-contract.md → matriz SQL y concurrencia, migración reversible y prohibición de reescribir Analysis original.

**Criterios de aceptación**

- [x] Plan Alembic aditivo con upgrade/rollback, FK/índices/checks/triggers y coherencia single/composite; cualquier contradicción exige ADR aprobado.
- [x] CA-02: — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-08: — Dados stems listos, cuando se ajustan mute, solo y volumen, entonces reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-18: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-20: — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-34: — Dado preset con nombre, cuando se crea/edita/selecciona, entonces conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [x] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [x] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [x] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.


**Verificación ejecutada ROOT** (2026-10-11T20:57:46.782766+00:00): lectura production-data-contract.md → matriz SQL/concurrencia, migración reversible y AnalysisUNIQUE original sin reescritura. PD-O1/ADR0083 ratificados; discriminantes seal_kind/root.kind separados y contratos D02/históricos intactos. QA579/579/gate0;206payloads/101snapshots/guards/ausencias yprefijosM2/ADR84verificadosROOT. Revisión2A29/B25sin gaps/B01corregido. CensoQA150FK explícitas(145simples+5compuestas),22H separadas;148histórico preservado ydosabreviadasidentificadasC266. SinSQL/DDL ni funciones M3 aceptadas. [Informe vigente](testing/production-data-contract-current-qa1-2026-10-11.md). TDD n/a: prosa.

- **Changelog**: Define revisiones inmutables de producción, sus relaciones y controles de concurrencia; conserva los datos históricos y separa el tipo del sello del tipo del resultado.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

### T-04 — Concretar formatos multiversión y cierre portable

- **Descripción**: Evaluar CPUv2 y SongCPUv2 para cada sujeto; definir dispatch lectores, TimelineV2 y escena N0. Conservar bytes históricos v1/v2.
- **Estado**: completado
- **Changelog**: Formatos tipados de producción y cierre portable ratificados; exportar un proyecto sin tomas conserva letra y portada.
- **Tiempo humano**: est. 12h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-02, T-03; D-04 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-format-contract.md`, `docs/arquitectura/convenciones.md`, `docs/arquitectura/datos.md`, `docs/decisiones/ADR-0085-formatos-tipados-y-cierre-portable-de-produccion.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/production-format-contract-*.md`
- **Cubre (tests)**: E2E-12, E2E-13, E2E-18, E2E-26, E2E-36, E2E-38, E2E-39, M-48
- **Verificación**: lectura: production-format-contract.md → cada sujeto tiene formato/lector; v1 cerrado e historia sin reescritura.

**Criterios de aceptación**

- [x] ROOT cierra compatibilidad y ejemplos golden por origen; formato incompatible requiere ADR específico antes de schemas/código.
- [x] CA-12: — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-13: — Dados título/artista/año, take, portada y letra embebida solicitada, cuando se exporta, entonces un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-18: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-38: — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-39: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [x] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [x] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [x] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.


**Verificación ejecutada ROOT** (2026-10-12T04:36:08.008220+00:00): lectura contractual exacta; PF-O1/ADR85 ratificados, revisión2 FULL32A/5B sin gaps/A01B01corregidos y QA46/46. ROOT7artefactos/130pins/22fixtures5históricos/4derivados/gates0 verificados. [QA vigente](testing/production-format-contract-current-qa1-2026-10-12.md). TDD n/a prosa, sin readers/goldens/funciones ejecutados; M3 producto0.

### T-05 — Ratificar medición de stems, mezcla y export

- **Descripción**: Ratificar LUFS/TP y tratamiento visible; métricas de suma/alineación de stems y equivalencia mixer/PCM, casos silencio y codec final.
- **Estado**: completado
- **Changelog**: Ratifica medición conservadora de audio, suma de stems, equivalencia del mixer y conformidad del archivo final, preservando derechos e historia.
- **Tiempo humano**: est. 8h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-02; D-05 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/audio-measurement-contract.md`, `docs/arquitectura/pipeline-audio.md`, `docs/decisiones/ADR-0086-medicion-conservadora-del-audio-de-produccion.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/audio-measurement-*.md`
- **Cubre (tests)**: M-07, M-10, E2E-11, E2E-12, E2E-14
- **Verificación**: lectura: audio-measurement-contract.md → fórmulas, medidor/pin, tolerancias, clipping/silencio y política no conforme ratificados.

**Criterios de aceptación**

- [x] Objetivos −14/−23/−16 LUFS; streaming/podcast ±0,5 LU y broadcast ±0,2 LU QC, TP≤−1 dBTP, suma<−30dB, mezcla≤1muestra/residual<−60dB se ratifican antes de medir. Sin limitador oculto.
- [x] CA-07: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-10: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-11: — Dado destino streaming, broadcast o podcast, cuando se exporta, entonces el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-12: — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [x] CA-14: — Dado post/export cuyo objetivo no se alcanza, cuando termina, entonces no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [x] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [x] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [x] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.


**Verificación ejecutada ROOT** (2026-10-12T10:41:06.440274+00:00): lectura exacta del contrato15608698/94564B;AM-O1/ADR86 ratificadas, revisión2FULL60A34B/B01B02corregidos y QA47/47. ROOT22payloads/141pins/4derivados/gates0 verificados. [QA vigente](testing/audio-measurement-current-qa1-2026-10-12.md). TDD n/a prosa; aplicación/audioAV/capabilities0, aceptación de producto en tareas reales.

### T-06 — Preparar cohorte autorizada y métricas independientes

- **Descripción**: Definir cohortes privadas con derechos/consentimiento, canto castellano, omisiones/repeticiones/silencios y canciones completas incluida Libre4:15. Separar anotadores de resultados del modelo.
- **Estado**: en-progreso
- **Tiempo humano**: est. 12h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01; D-06, D-13 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/cohort-metrics-contract.md`, `eval/m3/cohorts/`, `eval/m3/annotations/`, `scripts/m3_coverage_gate.py`, `tests/test_m3_coverage_gate.py`, `scripts/m3_coverage_collect.py`, `tests/test_m3_coverage_collect.py`, `docs/decisiones/ADR-0087-cohortes-independientes-y-aceptacion-de-produccion.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/cohort-metrics-*.md`, `docs/decisiones/ADR-0088-salidas-externas-y-custodia-del-recolector-python.md`, `scripts/eval/m3_coverage_runner.py`, `scripts/eval/tests/test_m3_coverage_runner.py`
- **Cubre (tests)**: E2E-04, M-17, M-21, M-25, M-28, M-29, M-31, M-33, M-43, M-49
- **Verificación**: lectura: cohort-metrics-contract.md → anotaciones independientes, revisión humana asignada, duración íntegra y umbrales congelados antes de RED de métodos; `uv run --frozen --no-sync --all-packages python -X utf8 -B -m pytest tests/test_m3_coverage_gate.py` → casos de «Cobertura estricta de fase» pasan con sus exits esperados; comando del gate estricto por fase → inventario completo y cada fichero de producción vigente cambiado ≥80 sin exclusiones.

**Criterios de aceptación**

- [ ] Instrumento de cobertura implementado con RED causal, raw oficial, inventario ROOT y casos adversos del contrato; sin aprobar medias ni missing. Está listo antes del cierre de Fase 1, sin afirmar conformidad musical ni completar tareas dependientes.

- [x] ROOT fija rúbricas y umbrales de beats/key/sections, loudness y timings. Propuesta palabra mediana≤100ms/P95≤250ms y beat70ms/F1 requiere ratificación numérica completa; unmatched se cuenta aparte. RatificaciónROOTCM-O1/CM-P1 2026-10-12T13:23:49.279192+00:00, ADR0087/QA287; todosvalores §§4–8 fuente6cc06770.
- [ ] CA-04: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-17: — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-21: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-25: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-28: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-29: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-31: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-33: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-43: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-49: — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Preparar el instrumento de gate sobre su candidato, con RED causal para los casos del contrato, GREEN y raw oficial por fichero; revisión/QA antes de que ROOT cierre T-06 y Fase 1.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.


**Adopción normativa ROOT** (2026-10-12T13:23:49.279192+00:00):3docs/ADR0087aceptada/CM-O1-P1ratificadas, fuente6cc06770/99562B intacta, revisión2A/B y QA287/287/26payloads auditados. [QA ylímites](testing/cohort-metrics-current-qa1-2026-10-12.md). T06full sigue en-progreso: instrumentoTDD/raw80/revisiónQA/Verificación yD13adquisición no ejecutados. A03proveniencia aclarada enADR sin atribuir QA a cambios de fuente.

### T-07 — Ratificar perfiles N0 y herramientas licenciadas

- **Descripción**: Inventariar codec/container/browser/font con probes offline, pins y licencias. Cerrar layout, fps, resolución, sincronía y objetivo minutos por duración.
- **Estado**: borrador
- **Tiempo humano**: est. 12h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-04, T-06; D-07 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/n0-profile-contract.md`, `tools/tools.lock.json`, `docs/legal/licencias.md`, `docs/arquitectura/modelos.md`
- **Cubre (tests)**: E2E-26, E2E-27, M-28, M-29, E2E-47
- **Verificación**: lectura: n0-profile-contract.md → codec reproducible en browser y lector independiente, bundle local, fuente licenciada y objetivos previos al RED renderer.

**Criterios de aceptación**

- [ ] ROOT ratifica perfiles horizontales/verticales, 30/1fps/1080p propuestos, sync/deriva≤1cuadro y presupuesto para Libre4:15 completa; FFmpeg LGPL no presume H264.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-27: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-28: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-29: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-47: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

### T-08 — Ratificar ZIP seguro y colisiones

- **Descripción**: Cerrar catálogo, cuotas de expansión/disco, normalización/case, enlaces, IDs, remapeo source→local y replay propio. Conservar bytes originales e inferencias históricas.
- **Estado**: borrador
- **Tiempo humano**: est. 8h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-04; D-08 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/portable-import-contract.md`, `docs/arquitectura/datos.md`
- **Cubre (tests)**: E2E-36, E2E-37, E2E-38, E2E-39
- **Verificación**: lectura: portable-import-contract.md → límites exactos, amenazas, deduplicación/remapeo, concurrencia e import all-or-nothing.

**Criterios de aceptación**

- [ ] ROOT ratifica límites propuestos 100000 entradas/100GiB/2GiB/100:1/profundidad16 o los sustituye explícitamente; colisión rechaza salvo remapeo contractual.
- [ ] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-37: — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno, cuando se importa, entonces se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-38: — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-39: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

### T-09 — Ratificar corte de biblioteca y activación

- **Descripción**: Cerrar exclusividad de todos los mutadores, journal/quiesce, binding BD/raíz, catálogo y rollback. Backup nativo SQLite más assets; no copiar VHDX activo.
- **Estado**: borrador
- **Tiempo humano**: est. 12h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01, T-03, T-08; D-09 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/library-maintenance-contract.md`, `docs/arquitectura/datos.md`
- **Cubre (tests)**: E2E-40, E2E-41, E2E-42, M-43, E2E-44, M-45
- **Verificación**: lectura: library-maintenance-contract.md → estados/fallos/locks/binding/rollback y distinción backup diario BD vs biblioteca.

**Criterios de aceptación**

- [ ] ROOT ratifica corte coherente, restore nuevo propio ext4, jobs/leases inertes y activación con copia restaurable previa; última válida retenida sin purga automática inicial.
- [ ] CA-40: — Dada biblioteca con commits en WAL y medios/referencias, cuando se crea backup, entonces produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-41: — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-42: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-43: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

### T-10 — Seleccionar modos musicales mediante spikes reales

- **Descripción**: Reusar evidencia M0 sólo después de gates; planificar/ejecutar spikes autorizados de separador, music.complete/cover y calidad alta en5070. Auditar formato seguro, SHA/licencia y modo explícito.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01, T-05, T-06; D-10 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/music-capabilities-contract.md`, `models/models.lock.json`, `docs/legal/licencias.md`, `eval/m3/music/`
- **Cubre (tests)**: M-07, E2E-30, M-31, E2E-32, M-33, M-46
- **Verificación**: lectura: music-capabilities-contract.md y recibos de spike → selección ROOT por capacidad, calidad/VRAM reales pendientes hasta prueba propia.

**Criterios de aceptación**

- [ ] Tres capacidades obligatorias tienen candidato/método/adapter/cohorte y conformance reproducible. Ausencia mantiene gate y trabajo abierto; nunca permite cierre F18/F19 deshabilitado.
- [ ] CA-07: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-30: — Dado tarareo/maqueta/voz propio validado, cuando se solicita referencia/acompañamiento mediante `music.complete`/`music.cover` o capacidad equivalente comprobada, entonces el server resuelve entrada y crea hijo con upload/padres/roles y derechos reales, sin identidad vocal prometida ni cambio automático de maestro. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-31: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-32: — Dado modo de calidad alta validado en M0, cuando se regenera, entonces sólo ofrece parámetros/perfil/pasos/modelo comprobados que caben con margen y publica hijo con valores efectivos; modo ausente queda deshabilitado con motivo y gate abierto. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-33: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

### T-11 — Seleccionar Comfy generación y edición por referencia

- **Descripción**: Comparar modelos/workflows/nodos cerrados para generar varias opciones y editar con referencia. Auditar pins/código/hash/weights y árbol de procesos propietario.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06; D-11 se cierra aquí antes del RED dependiente
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/comfy-capabilities-contract.md`, `models/models.lock.json`, `tools/tools.lock.json`, `docs/legal/licencias.md`, `eval/m3/comfy/`
- **Cubre (tests)**: E2E-22, E2E-23, M-25, M-46
- **Verificación**: lectura: comfy-capabilities-contract.md → licencias/pins/seguridad/inputs/outputs y evidencia de selección; conformance final todavía obligatoria.

**Criterios de aceptación**

- [ ] ROOT decide adapter y workflows compatibles con12GB; dos gates generación/ref independientes y unload de árbol propio, sin checkpoints elegidos por nombre.
- [ ] CA-22: — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-23: — Dada portada/referencia autorizada, cuando se edita con referencia, entonces produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-25: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos. Su concreción queda registrada; la aceptación de producto pertenece a las tareas reales relacionadas.

**Subtareas**

- [ ] Preparar contrato, casos/fallos y alternativas con fuentes SHA; elevar decisión concreta a ROOT.
- [ ] Ratificar campos, límites o métricas y actualizar fuentes/ADR si cambia una decisión documentada.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Esta tarea cierra una incertidumbre; no declara conforme la función ni habilita capacidades por documentación.

## Fase 2 — Autoridad, datos y publicación

**Estado**: borrador · **Estimado**: 60h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-12 — Capturar peticiones y validar derechos/propiedad

- **Descripción**: Implementar namespace ProductionRequest privado y DTO aditivo, captura de fuentes/hashes/revisiones, derechos/consentimiento y validación de contenido/tamaño/duración.
- **Estado**: borrador
- **Tiempo humano**: est. 18h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-02, T-03, T-04; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/requests.py`, `apps/server/tests/test_m3_requests.py`, `apps/server/app/domain_routes.py`, `apps/server/app/api_models.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`
- **Cubre (tests)**: E2E-02, E2E-03, E2E-04, E2E-05, E2E-47, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_requests.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Cambio concurrente de maestro no retargetea; acceso ajeno y feature no verificada rechazan antes de cola/carga sin eco privado.
- [ ] CA-02: — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo.
- [ ] CA-03: — Dada tarea/feature no verificada, cuando UI/API solicita cualquier acción M3, entonces se explica/rechaza sin carga ni envío; una prueba sintética identificada no habilita el modelo real.
- [ ] CA-04: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado.
- [ ] CA-05: — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena, cuando se valida, entonces se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
- [ ] CA-47: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-13 — Migrar revisiones y proyecciones de contenido

- **Descripción**: Añadir revisiones y schemas ratificados; conservar datos/IDs/FK/FTS y lectores históricos. El nombre final de nuevos formatos depende D04, no del ejemplo de ruta.
- **Estado**: borrador
- **Tiempo humano**: est. 18h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-03, T-04; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/models/__init__.py`, `apps/server/app/migrations/versions/`, `apps/server/tests/test_m3_migrations.py`, `packages/contracts/timeline-v2.schema.json`, `packages/contracts/song-v2.schema.json`
- **Cubre (tests)**: E2E-08, E2E-18, E2E-20, E2E-34, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_migrations.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Upgrade/rollback en copia y concurrencia CAS prueban inmovilidad de historia; ningún relax fuera de ADR0074.
- [ ] CA-08: — Dados stems listos, cuando se ajustan mute, solo y volumen, entonces reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master.
- [ ] CA-18: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
- [ ] CA-20: — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
- [ ] CA-34: — Dado preset con nombre, cuando se crea/edita/selecciona, entonces conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-14 — Componer jobs y publicar por sujetos M3

- **Descripción**: Implementar compositores cerrados, CPU2/GPU1, resolución de roles y recibos propios por resultado. Reutilizar primitivas liberadas sin exigir ganador de inferencia para CPU.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01, T-02, T-03, T-04, T-12, T-13; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/publication.py`, `apps/server/tests/test_m3_publication.py`, `apps/server/app/queue/chains.py`, `apps/server/app/queue/runtime.py`, `apps/server/app/queue/resolver.py`, `apps/server/app/worker/contracts.py`, `apps/server/app/worker/planning.py`, `apps/server/app/worker/execution.py`, `apps/server/app/worker/packages.py`, `apps/server/app/worker/publications.py`
- **Cubre (tests)**: E2E-02, E2E-06, E2E-15, E2E-22, E2E-26, E2E-44, M-45, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_publication.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Custodia/NOREPLACE/CAS/replay probados; UNKNOWN bloquea promoción/serving/cleanup; jobs no esperan hijos ocupando slots.
- [ ] CA-02: — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo.
- [ ] CA-06: — Dado un take listo y separación verificada, cuando se solicitan stems, entonces se publican voz/batería/bajo/otros como assets y manifiesto ligado al take, sin take nuevo ni cambio de master/padres.
- [ ] CA-15: — Dado un take recién terminado, cuando se analiza, entonces BPM/beats, tonalidad, secciones y loudness quedan ligados a sus hashes, métodos/versiones y letra aplicable, visibles y utilizables por N0.
- [ ] CA-22: — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 3 — Stems, mixer y exportación de audio

**Estado**: borrador · **Estimado**: 96h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-15 — Integrar separador y publicar cuatro stems

- **Descripción**: Integrar ganador por capacidad, raw autorizado y server publica voz/batería/bajo/otros con muestras/tasa/canales. Añadir sólo campos opcionales /v1.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-05, T-10, T-12, T-14; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_m3_stems.py`, `apps/server/app/production/stems.py`, `apps/server/tests/test_m3_stems.py`, `packages/engine-contract/engine_contract/__init__.py`, `packages/contracts/engine-v1.json`
- **Cubre (tests)**: E2E-06, M-07, M-46
- **Verificación**: `docker compose run --rm engine-acestep uv run pytest tests/test_m3_stems.py -m 'not gpu' -q` → contrato/raw/terminal válidos; `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_stems.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Stems son assets del take, ningún take nuevo ni master modificado; verificación modelo real depende T36.
- [ ] CA-06: — Dado un take listo y separación verificada, cuando se solicitan stems, entonces se publican voz/batería/bajo/otros como assets y manifiesto ligado al take, sin take nuevo ni cambio de master/padres.
- [ ] CA-07: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-16 — Construir mixer con transporte común

- **Descripción**: Implementar Web Audio común y origen temporal único, ganancias finitas/mute/solo, seek/pausa y persistencia MixRevision. Definir presupuesto PCM y worklet si memoria lo exige.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-05, T-13, T-15; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/web/components/StemMixer.tsx`, `apps/web/components/PlayerContext.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-mixer.spec.ts`
- **Cubre (tests)**: E2E-08, M-10
- **Verificación**: `pnpm --dir apps/web exec playwright test e2e/m3-mixer.spec.ts` → controles, seek, reload y byte guards pasan

**Criterios de aceptación**

- [ ] Mute prevalece; silencio/solos múltiples funcionan; reload conserva estado sin mutar stems/master; equivalencia real T36.
- [ ] CA-08: — Dados stems listos, cuando se ajustan mute, solo y volumen, entonces reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master.
- [ ] CA-10: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-17 — Publicar mezcla CPU y linaje de todos los padres

- **Descripción**: Aplicar selección/ganancias efectivas sin normalización oculta; publicar Export o hijo CPU conforme D02/D04 y todos sus padres/roles.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-05, T-14, T-16; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/mix.py`, `apps/server/tests/test_m3_mix.py`, `packages/audio-post/audio_post/pipeline.py`, `packages/audio-post/audio_post/manifest.py`
- **Cubre (tests)**: E2E-09, M-10, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_mix.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Bytes originales intactos, hashes/mediciones y recipe vinculados; master sólo cambia por acción explícita.
- [ ] CA-09: — Dada mezcla elegida, cuando se exporta, entonces el server produce el resultado con ganancias/selección efectivas, fuentes/hashes y mediciones; cualquier take musical nuevo es hijo con todos sus padres, nunca reemplazo.
- [ ] CA-10: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-18 — Exportar perfiles, originales, ZIP y metadatos

- **Descripción**: Procesar destinos streaming/broadcast/podcast, medir final decodificado, original byte exacto y stems48kHz sin normalización. Embebido de letra sólo por solicitud histórica.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-04, T-05, T-14, T-17; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/export.py`, `apps/server/tests/test_m3_export.py`, `packages/audio-post/audio_post/pipeline.py`, `packages/audio-post/audio_post/manifest.py`, `apps/web/components/AudioExport.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-export.spec.ts`
- **Cubre (tests)**: E2E-11, E2E-12, E2E-13, E2E-14
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_export.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-export.spec.ts` → destinos y error visible pasan

**Criterios de aceptación**

- [ ] Lector independiente recupera metadatos/take/portada/letra; objetivo inalcanzable conserva original y error, no publica conforme.
- [ ] CA-11: — Dado destino streaming, broadcast o podcast, cuando se exporta, entonces el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando.
- [ ] CA-12: — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos.
- [ ] CA-13: — Dados título/artista/año, take, portada y letra embebida solicitada, cuando se exporta, entonces un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe.
- [ ] CA-14: — Dado post/export cuyo objetivo no se alcanza, cuando termina, entonces no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 4 — Análisis, alineación y karaoke

**Estado**: borrador · **Estimado**: 76h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-19 — Completar análisis por método y parcialidad

- **Descripción**: BPM/beats/key/sections/loudness ligados a hash/método/versiones y contexto textual. Publicar resultados parciales sin números sintéticos.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-12, T-14; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/analysis/engine_analysis/descriptor.py`, `apps/engines/analysis/engine_analysis/backend.py`, `apps/engines/analysis/tests/test_m3_methods.py`, `apps/server/app/production/analysis.py`, `apps/server/tests/test_m3_analysis.py`, `apps/web/components/AudioAnalysis.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-analysis.spec.ts`
- **Cubre (tests)**: E2E-15, E2E-16, M-17
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_analysis.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-analysis.spec.ts` → parcialidad visible pasa

**Criterios de aceptación**

- [ ] Etiqueta textual conserva origen y no acredita sección medida; descriptor sólo verified después T37.
- [ ] CA-15: — Dado un take recién terminado, cuando se analiza, entonces BPM/beats, tonalidad, secciones y loudness quedan ligados a sus hashes, métodos/versiones y letra aplicable, visibles y utilizables por N0.
- [ ] CA-16: — Dado fallo parcial o audio instrumental/no analizable, cuando se consulta análisis, entonces se identifica cada resultado ausente/incierto y su motivo, sin valores sintéticos de reemplazo; no se bloquea la consulta de los resultados válidos.
- [ ] CA-17: — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-20 — Alinear letra histórica y revisionar correcciones

- **Descripción**: Bindings single/composite, tokens estables y tiempos globales; segmentar largas canciones conservando solapes/offsets, no truncar180s. Correcciones tienen origen y padre propio.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-03, T-04, T-06, T-14, T-19; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/analysis/engine_analysis/backend.py`, `apps/engines/analysis/tests/test_m3_alignment.py`, `apps/server/app/production/alignment.py`, `apps/server/tests/test_m3_alignment.py`
- **Cubre (tests)**: E2E-18, E2E-20, M-21
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_alignment.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Cambio de letra vigente no modifica alineación; omitted/repeated/unmatched/instrumental son explícitos; análisis original intacto.
- [ ] CA-18: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
- [ ] CA-20: — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
- [ ] CA-21: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-21 — Ofrecer karaoke, editor temporal y LRC/SRT

- **Descripción**: Sincronizar palabra/línea por revisión elegida, seek/pausa, incertidumbre y corrección. Exportar formatos parseables con tiempos finitos ordenados dentro duración.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-20; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/web/components/LyricsKaraoke.tsx`, `apps/web/components/TimingEditor.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-karaoke.spec.ts`, `apps/server/app/production/subtitles.py`, `apps/server/tests/test_m3_subtitles.py`
- **Cubre (tests)**: E2E-18, E2E-19, E2E-20, M-21
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_subtitles.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-karaoke.spec.ts` → palabra, línea, seek y corrección pasan

**Criterios de aceptación**

- [ ] No reescribe audio/texto histórico/evidencia; canto real y utilidad T37.
- [ ] CA-18: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
- [ ] CA-19: — Dados tiempos válidos, cuando se reproduce/se busca/pausa en karaoke y se exportan LRC/SRT, entonces líneas/palabras corresponden al audio y la revisión elegida; formatos se parsean, tiempos son ordenados/finitos y no exceden duración.
- [ ] CA-20: — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
- [ ] CA-21: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 5 — Portadas Comfy y uploads

**Estado**: borrador · **Estimado**: 52h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-22 — Empaquetar engine-comfy headless y adapter /v1

- **Descripción**: Nuevo módulo Docker con workflows/nodos cerrados y proceso hijo CUDA, generación múltiple y edición por referencia; raw propio sin BD ni descargas runtime.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-11, T-12, T-14; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/comfy/`, `docker-compose.yml`, `pyproject.toml`, `uv.lock`, `apps/server/app/production/artwork.py`, `apps/server/tests/test_m3_artwork.py`, `models/models.lock.json`, `tools/tools.lock.json`, `docs/legal/licencias.md`
- **Cubre (tests)**: E2E-22, E2E-23, M-25, M-46, E2E-47
- **Verificación**: `docker compose run --rm engine-comfy uv run pytest -m 'not gpu'` → conformidad de adapter/procesos/raw; `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_artwork.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Cancel/unload reap árbol propio y liberar VRAM; terminal/seq /v1 único, sin rutas/workflows arbitrarios; gate real T38.
- [ ] CA-22: — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
- [ ] CA-23: — Dada portada/referencia autorizada, cuando se edita con referencia, entonces produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4.
- [ ] CA-25: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
- [ ] CA-47: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-23 — Mostrar portadas y aceptar uploads autorizados

- **Descripción**: Mostrar opciones distintas, antecedentes/ref y seleccionar portada explícitamente con CAS. Upload source=upload conserva derechos/consentimiento y sirve de fondo N0.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-12, T-22; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/web/components/ArtworkPicker.tsx`, `apps/web/components/ArtworkUpload.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-artwork.spec.ts`
- **Cubre (tests)**: E2E-04, E2E-05, E2E-22, E2E-23, E2E-24, M-25
- **Verificación**: `pnpm --dir apps/web exec playwright test e2e/m3-artwork.spec.ts` → opciones/ref/upload/rechazos/CAS pasan

**Criterios de aceptación**

- [ ] Imagen previa intacta; upload no inventa seed/modelo ni activa I2V; no promete coherencia personaje M4.
- [ ] CA-04: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado.
- [ ] CA-05: — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena, cuando se valida, entonces se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
- [ ] CA-22: — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
- [ ] CA-23: — Dada portada/referencia autorizada, cuando se edita con referencia, entonces produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4.
- [ ] CA-24: — Dada imagen subida válida con derechos/consentimiento, cuando se usa, entonces `source=upload` y su referencia/procedencia se conservan como portada o fondo N0; no requiere generación ni habilita I2V.
- [ ] CA-25: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 6 — Escena N0, renderer y montaje

**Estado**: borrador · **Estimado**: 88h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-24 — Construir escena N0 compartida y features reales

- **Descripción**: Paquete temporal Canvas puro t explícito, layout/line wrap/fonts y cinética por timing_revision. Onda/espectro/partículas consumen features del audio final, semilla visual explícita.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-04, T-06, T-07, T-19, T-20; puertas comunes y seams liberados antes de integración
- **Archivos**: `packages/n0-scene/`, `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `apps/web/package.json`, `apps/server/app/production/features.py`, `apps/server/tests/test_m3_features.py`, `apps/web/components/N0Preview.tsx`
- **Cubre (tests)**: E2E-26, E2E-27
- **Verificación**: `pnpm --dir packages/n0-scene test` → fixtures temporales/layout/reactividad; `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_features.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Seek reconstruye estado, silencio distinto de señal, tiempo frame_index/fps y audio clock convergen; no animación prefabricada como prueba.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] CA-27: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-25 — Empaquetar renderer offline y publicar Render

- **Descripción**: Bundle cerrado assets/fonts locales; browser hijo propio fija frame_index/fps y espera fuentes/assets. FFmpeg codifica/muxea audio final y server mide/publica.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-07, T-14, T-18, T-24; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/render.py`, `apps/server/tests/test_m3_render.py`, `apps/server/Dockerfile`, `tools/tools.lock.json`, `apps/server/app/production/renderer/`, `packages/n0-scene/`, `docs/legal/licencias.md`
- **Cubre (tests)**: E2E-26, E2E-27, M-28, M-29, E2E-44, E2E-47
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_render.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Sin browser del usuario/web viva/Internet; perfiles reales ratificados, principio/fin completos; recuperación no duplica ni sirve parcial.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] CA-27: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
- [ ] CA-28: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- [ ] CA-29: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-47: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-26 — Ofrecer montaje N0 y export en canción

- **Descripción**: Crear revisión VideoProject/TimelineV2, elegir take/audio/timing/fondo y perfiles; preview/export congelan la misma escena. Eventos reales de progreso.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-21, T-23, T-24, T-25; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/web/components/N0Editor.tsx`, `apps/web/components/N0Preview.tsx`, `apps/web/app/songs/[id]/page.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-n0.spec.ts`, `apps/server/app/domain_routes.py`, `packages/contracts/openapi.json`, `apps/web/lib/generated/api.d.ts`
- **Cubre (tests)**: E2E-26, E2E-27, M-28, M-29
- **Verificación**: `pnpm --dir apps/web exec playwright test e2e/m3-n0.spec.ts` → revisión, audio efectivo, seek y export pasan

**Criterios de aceptación**

- [ ] Incertidumbre visible, estilos onda/espectro/partículas y tipografía legibles; canción completa sin truncar.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] CA-27: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
- [ ] CA-28: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- [ ] CA-29: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 7 — Audio propio, calidad alta y presets

**Estado**: borrador · **Estimado**: 72h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-27 — Integrar audio propio como referencia y acompañamiento

- **Descripción**: Capacidad comprobada music.complete/cover o equivalente, resolución upload/roles/derechos y conversión explícita. Hijo con padres reales, sin identidad vocal prometida.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-10, T-12, T-14; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_m3_own_audio.py`, `apps/server/app/production/own_audio.py`, `apps/server/tests/test_m3_own_audio.py`, `apps/web/components/OwnAudioProduction.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-own-audio.spec.ts`
- **Cubre (tests)**: E2E-04, E2E-05, E2E-30, M-31, M-46
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_own_audio.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-own-audio.spec.ts` → admisión y linaje pasan

**Criterios de aceptación**

- [ ] No cambia master ni reemplaza upload; ausencia mantiene trabajo abierto F19 hasta integración/escucha T40.
- [ ] CA-04: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado.
- [ ] CA-05: — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena, cuando se valida, entonces se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
- [ ] CA-30: — Dado tarareo/maqueta/voz propio validado, cuando se solicita referencia/acompañamiento mediante `music.complete`/`music.cover` o capacidad equivalente comprobada, entonces el server resuelve entrada y crea hijo con upload/padres/roles y derechos reales, sin identidad vocal prometida ni cambio automático de maestro.
- [ ] CA-31: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-28 — Integrar regeneración de calidad alta comprobada

- **Descripción**: Selector usa perfil/pasos/modelo efectivo validado M0 y margen5070. Regenera hijo conservando contexto; registrar límites y valores efectivos.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-10, T-12, T-14; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_m3_high_quality.py`, `apps/server/app/production/high_quality.py`, `apps/server/tests/test_m3_high_quality.py`, `apps/web/components/HighQualityProduction.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-quality.spec.ts`
- **Cubre (tests)**: E2E-32, M-33, M-46
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_high_quality.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-quality.spec.ts` → perfil efectivo/rechazos pasan

**Criterios de aceptación**

- [ ] UI ausente deshabilitada con gate abierto es estado intermedio; F18 sólo se cierra con comparación/escucha T40.
- [ ] CA-32: — Dado modo de calidad alta validado en M0, cuando se regenera, entonces sólo ofrece parámetros/perfil/pasos/modelo comprobados que caben con margen y publica hijo con valores efectivos; modo ausente queda deshabilitado con motivo y gate abierto.
- [ ] CA-33: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-29 — Gestionar presets globales y congelar usos

- **Descripción**: Crear/editar/seleccionar nombre, estilo/parámetros/ref/estilo visual. Uso copia valores y refs autorizadas; edición no reescribe jobs/takes/renders.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-12, T-13; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/presets.py`, `apps/server/tests/test_m3_presets.py`, `apps/web/components/ProductionPresets.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-presets.spec.ts`
- **Cubre (tests)**: E2E-34, E2E-35, E2E-36, E2E-41
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_presets.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-presets.spec.ts` → captura y fallos pasan

**Criterios de aceptación**

- [ ] Ref ausente/permisos/incompatible rechaza antes envío; no simula LoRA/F71.
- [ ] CA-34: — Dado preset con nombre, cuando se crea/edita/selecciona, entonces conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores.
- [ ] CA-35: — Dado preset con referencia no disponible, permisos ausentes o parámetro incompatible, cuando se aplica, entonces muestra/rechaza el problema antes de envío; no omite silenciosamente referencia ni simula F-71/LoRA.
- [ ] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- [ ] CA-41: — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 8 — Portabilidad y biblioteca

**Estado**: borrador · **Estimado**: 120h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-30 — Exportar cierre portable privado multiversión

- **Descripción**: Cerrar DAG de takes CPU/inferencia/letras/maps/master/portadas/N0/valoraciones/refs/presets/declaraciones. Catálogo y bytes originales versionados.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-04, T-08, T-14, T-18, T-20, T-25, T-29; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/portable.py`, `apps/server/tests/test_m3_portable.py`, `apps/server/app/snapshots.py`, `apps/server/app/closure_rows.py`, `packages/contracts/song-v2.schema.json`, `apps/web/components/SongTransfer.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-transfer.spec.ts`
- **Cubre (tests)**: E2E-36, E2E-39, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_portable.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Sin secretos/path personales/leases/PID/autoridad activa; letra/fotos necesarias sólo payload privado autorizado.
- [ ] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- [ ] CA-39: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-31 — Importar seguro con remapeo y publicación atómica

- **Descripción**: Prevalidar paths/quotas/ownership/hash/versión/DAG en staging propio, intent durable por paquete y remapeo ratificado. Preservar bytes/procedencia originales.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-08, T-14, T-30; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/import_song.py`, `apps/server/tests/test_m3_import_song.py`, `apps/server/app/snapshots.py`, `apps/server/app/queue/recovery.py`, `apps/web/components/SongTransfer.tsx`, `apps/web/e2e/m3-transfer.spec.ts`
- **Cubre (tests)**: E2E-36, E2E-37, E2E-38, E2E-39, E2E-44, M-45, M-48
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_import_song.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-transfer.spec.ts` → roundtrip y negativos pasan

**Criterios de aceptación**

- [ ] Traversal/enlace/junction/duplicate/case/bomba/ajeno rechaza sin escape ni promoción parcial; concurrencia/replay nunca clobber.
- [ ] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- [ ] CA-37: — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno, cuando se importa, entonces se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación.
- [ ] CA-38: — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador.
- [ ] CA-39: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-32 — Crear backup coherente SQLite y assets

- **Descripción**: Mantenimiento exclusivo quiesce todos los mutadores; backup SQLite nativo corte WAL más assets/refs/locks/catálogo y hashes.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-09, T-14, T-30; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/library_backup.py`, `apps/server/tests/test_m3_library_backup.py`, `apps/server/app/backup.py`, `apps/server/app/closure_rows.py`, `apps/web/components/LibraryRecovery.tsx`, `apps/web/messages/es.json`, `apps/web/e2e/m3-library.spec.ts`
- **Cubre (tests)**: E2E-40, E2E-42, E2E-44, M-45
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_library_backup.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio

**Criterios de aceptación**

- [ ] Integridad/FK/FTS y versión comprobadas antes validar; fallo/disco/cancel conserva última válida, sin VHDX activo.
- [ ] CA-40: — Dada biblioteca con commits en WAL y medios/referencias, cuando se crea backup, entonces produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca.
- [ ] CA-42: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-33 — Restaurar destino nuevo y activar con rollback

- **Descripción**: Restore en raíz propia nueva ext4 con binding DB/raíz; jobs/leases históricos inertes y dependencias herramientas/modelos diferenciadas. Activación exclusiva con backup restaurable previo.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-09, T-31, T-32; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/library_restore.py`, `apps/server/tests/test_m3_library_restore.py`, `apps/server/app/backup.py`, `apps/server/app/queue/recovery.py`, `apps/web/components/LibraryRecovery.tsx`, `apps/web/e2e/m3-library.spec.ts`
- **Cubre (tests)**: E2E-41, E2E-42, M-43, E2E-44, M-45
- **Verificación**: `. ./scripts/env.ps1; uv run pytest apps/server/tests/test_m3_library_restore.py -q` → todos los casos del contrato pasan, sin skip de comportamiento obligatorio · `pnpm --dir apps/web exec playwright test e2e/m3-library.spec.ts` → consulta/errores/recovery visibles pasan

**Criterios de aceptación**

- [ ] Fallo antes/después binding revierte biblioteca previa; no borra medios ajenos, reintento sin doble publicación.
- [ ] CA-41: — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.
- [ ] CA-42: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
- [ ] CA-43: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 9 — Recovery, GPU y runtime offline

**Estado**: borrador · **Estimado**: 52h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-34 — Probar recovery causal en cada frontera

- **Descripción**: Inyectar cancel/acuse perdido/crash en raw/post/rename/commit/render/import/backup. Comparar recibos y guardas before/after en Compose persistente propio.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-14, T-18, T-25, T-31, T-32, T-33; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/recovery.py`, `apps/server/tests/test_m3_recovery.py`, `apps/server/app/queue/recovery.py`, `apps/server/app/worker/publications.py`, `scripts/m3_verify_recovery.py`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/recovery/`
- **Cubre (tests)**: E2E-44, M-45
- **Verificación**: `uv run python scripts/m3_verify_recovery.py --profile persistent --report eval/m3/recovery/report.json` → matriz completa de fronteras pasa con guardas intactas

**Criterios de aceptación**

- [ ] Ext4/UUID/NOREPLACE/CAS/replay/restart reales; montaje equivocado aborta; UNKNOWN impide serving/publicar/limpiar.
- [ ] CA-44: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-35 — Coordinar GPU y comprobar offline/privacidad

- **Descripción**: Una residencia GPU; libre−margen/BF16/modos explícitos, picos VRAM/RAM/spill, unload. Turno Ollama observa y restaura sólo su propia intervención, nunca servicio/modelos.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-15, T-19, T-22, T-27, T-28; puertas comunes y seams liberados antes de integración
- **Archivos**: `apps/server/app/production/runtime_guards.py`, `apps/server/tests/test_m3_runtime_guards.py`, `apps/server/app/queue/runtime.py`, `apps/server/app/queue/resolver.py`, `scripts/m3_verify_runtime.py`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/runtime/`
- **Cubre (tests)**: E2E-03, M-46, E2E-47
- **Verificación**: `uv run python scripts/m3_verify_runtime.py --profile real-5070 --report eval/m3/runtime/report.json` → offline/privacidad/residencia/unload/restauración propios acreditados

**Criterios de aceptación**

- [ ] Flows sin Internet ni claves externas/descargas runtime; logs/errores/manifiestos sin letra/fotos/secretos; progreso sólo eventos reales.
- [ ] CA-03: — Dada tarea/feature no verificada, cuando UI/API solicita cualquier acción M3, entonces se explica/rechaza sin carga ni envío; una prueba sintética identificada no habilita el modelo real.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
- [ ] CA-47: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 10 — Conformidad real y evaluación humana

**Estado**: borrador · **Estimado**: 164h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-36 — Validar stems, mixer y audio final reales

- **Descripción**: Separación real y cuatro stems; comparar mixer/PCM/export, luego codecs finales mediante medidor y lector independiente. Escucha isolamento/artefactos/clipping/silencio.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-05, T-06, T-15, T-16, T-17, T-18, T-34, T-35; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_audio.py`, `eval/m3/audio/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/audio/`
- **Cubre (tests)**: M-07, M-10, E2E-11, E2E-12, E2E-13, E2E-14, M-46
- **Verificación**: `uv run python scripts/m3_verify_audio.py --cohort eval/m3/cohorts/audio.json --report eval/m3/audio/report.json` → métricas finales y bytes pasan; lectura: acta humana → aislamiento/equivalencia/útil acreditados

**Criterios de aceptación**

- [ ] Ratificados D05 y métricas sin ajuste de offset/ganancia que esconda error; humanos registran utilidad, no resultado simulado.
- [ ] CA-07: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
- [ ] CA-10: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
- [ ] CA-11: — Dado destino streaming, broadcast o podcast, cuando se exporta, entonces el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando.
- [ ] CA-12: — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos.
- [ ] CA-13: — Dados título/artista/año, take, portada y letra embebida solicitada, cuando se exporta, entonces un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe.
- [ ] CA-14: — Dado post/export cuyo objetivo no se alcanza, cuando termina, entonces no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-37 — Validar análisis y karaoke con anotación independiente

- **Descripción**: Evaluar beats/key/sections/loudness y tiempos en canto castellano completo, omisiones/repeticiones/silencios e instrumental, con evaluador independiente.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-19, T-20, T-21, T-35; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_analysis.py`, `eval/m3/analysis/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/analysis/`
- **Cubre (tests)**: M-17, M-21, M-46
- **Verificación**: `uv run python scripts/m3_verify_analysis.py --cohort eval/m3/cohorts/analysis.json --report eval/m3/analysis/report.json` → umbrales ratificados por método pasan; lectura: acta canto real → utilidad acreditada

**Criterios de aceptación**

- [ ] Ratificados D06, mediana/P95 y errores unmatched por cohorte; humanos comprueban seek/pausa/corrección y utilidad.
- [ ] CA-17: — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.
- [ ] CA-21: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-38 — Validar Comfy real y revisión visual

- **Descripción**: Docker/CUDA5070 generación y edit/ref offline con múltiples opciones, nodos/pesos/hash/licencia. Medir VRAM/RAM/tiempos y árbol unload.
- **Estado**: borrador
- **Tiempo humano**: est. 24h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-11, T-22, T-23, T-35; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_comfy.py`, `eval/m3/comfy/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/comfy/`
- **Cubre (tests)**: M-25, M-46
- **Verificación**: `uv run python scripts/m3_verify_comfy.py --cohort eval/m3/cohorts/artwork.json --report eval/m3/comfy/report.json` → generación/ref y memoria/unload pasan; lectura: acta visual → opciones útiles

**Criterios de aceptación**

- [ ] Dos capacidades pasan por producto; revisión humana registra legibilidad/calidad sin promesa M4.
- [ ] CA-25: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-39 — Validar N0 completo, perfiles y rendimiento

- **Descripción**: Renderizar canciones completas incluida Libre4:15 en Docker/FFmpeg persistente, decode de principio a fin, browser y reproductor independiente.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-07, T-24, T-25, T-26, T-34, T-36, T-37, T-38; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_n0.py`, `eval/m3/n0/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/n0/`
- **Cubre (tests)**: E2E-26, E2E-27, M-28, M-29
- **Verificación**: `uv run python scripts/m3_verify_n0.py --cohort eval/m3/cohorts/n0.json --report eval/m3/n0/report.json` → todos los perfiles y presupuesto ratificado pasan; lectura: acta audiovisual → sin texto cortado ni deriva

**Criterios de aceptación**

- [ ] Duración/fps/res/LUFS/TP/word-screen/deriva/legibilidad/onda/espectro/partículas/silencio/seek y recursos cumplen perfil congelado; sin abreviar.
- [ ] CA-26: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] CA-27: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
- [ ] CA-28: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- [ ] CA-29: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-40 — Validar F19 y F18 con escucha emparejada

- **Descripción**: Ruta de producto real de audio propio y regeneración alta calidad, recibos efectivos y comparación misma letra/metadata con escucha nivelada.
- **Estado**: borrador
- **Tiempo humano**: est. 28h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-10, T-27, T-28, T-35; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_music.py`, `eval/m3/music/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/music/`
- **Cubre (tests)**: M-31, M-33, M-46
- **Verificación**: `uv run python scripts/m3_verify_music.py --cohort eval/m3/cohorts/music.json --report eval/m3/music/report.json` → conformance/perfiles/no spill pasan; lectura: actas humanas F19/F18 → rúbrica ratificada cumplida

**Criterios de aceptación**

- [ ] Motivo/estructura/acompañamiento/artefactos y mejora/compromisos constan en actas; más pasos/XL/nombre no acreditan mejora. Ambos gates obligatorios.
- [ ] CA-31: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
- [ ] CA-33: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
- [ ] CA-46: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

### T-41 — Ejercitar portable y recuperación de biblioteca real

- **Descripción**: Copia/cohorte autorizada de biblioteca real con WAL/medios/versiones CPU/inferencia; roundtrip y restore a destino nuevo propio ext4. Guardas originales before/after.
- **Estado**: borrador
- **Tiempo humano**: est. 32h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-06, T-30, T-31, T-32, T-33, T-34; puertas comunes y seams liberados antes de integración
- **Archivos**: `scripts/m3_verify_library.py`, `eval/m3/library/`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/library/`
- **Cubre (tests)**: E2E-36, E2E-37, E2E-38, E2E-39, E2E-40, E2E-41, E2E-42, M-43, M-45, M-48
- **Verificación**: `uv run python scripts/m3_verify_library.py --cohort eval/m3/cohorts/library.json --report eval/m3/library/report.json` → integridad/roundtrip/recovery/faults/ext4 pasan; lectura: acta recuperación → biblioteca real reproducida

**Criterios de aceptación**

- [ ] Búsqueda/consulta/master/linaje/letra/presets/reproducción reales; jobs inertes; activación requiere backup restaurable+exclusividad y rollback, nunca destruir original.
- [ ] CA-36: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- [ ] CA-37: — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno, cuando se importa, entonces se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación.
- [ ] CA-38: — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador.
- [ ] CA-39: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
- [ ] CA-40: — Dada biblioteca con commits en WAL y medios/referencias, cuando se crea backup, entonces produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca.
- [ ] CA-41: — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.
- [ ] CA-42: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
- [ ] CA-43: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
- [ ] CA-45: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- [ ] CA-48: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.

## Fase 11 — QA global y cierre

**Estado**: borrador · **Estimado**: 20h base · **Real**: — · **Coste est.**: n/a (ADR0001) · **Tokens est.**: n/a

### T-42 — Cerrar matriz 49CA, QA y documentación de M3

- **Descripción**: ROOT reconcilia dependencias M2 cerrado/heredados y evidencia por SHA. QA independiente, revisión A/B C/Dauto, documentación, changelog y retro antes aceptación.
- **Estado**: borrador
- **Tiempo humano**: est. 20h orientativas base (confianza baja) · real —
- **Tiempo IA (ejec.)**: est. n/a · real —
- **Supervisión**: est. n/a · real —
- **Previsión IA**: n/a in / n/a out tok · n/a € (ADR0001; reales null)
- **Dependencias**: T-01, T-34, T-35, T-36, T-37, T-38, T-39, T-40, T-41; puertas comunes y seams liberados antes de integración
- **Archivos**: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/testing/report.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/improvement-plan.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/tasks.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/test-plan.md`, `docs/roadmap/README.md`, `docs/README.md`, `docs/arquitectura/produccion.md`, `docs/producto/funcionalidades.md`, `docs/usuario/produccion.md`, `CHANGELOG.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/spec.md`, `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md`
- **Cubre (tests)**: M-01, M-49
- **Verificación**: lectura: testing/report.md y tasks.md → 49 CA/14 F con evidencias vigentes, gates heredados y aceptación ROOT; ledger-lint y coverage-check → exit0

**Criterios de aceptación**

- [ ] 49 CA/14F completos con evidencia CPU/fixtures/E2E/DockerFFmpeg/ext4/GPU/browser/lector/humana separada; ninguno satisfecho sólo por cobertura.
- [ ] CA-01: — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre.
- [ ] CA-49: — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente.

**Subtareas**

- [ ] Fijar baseline/brief/ownership y escribir RED causal por comportamiento conforme al contrato ratificado.
- [ ] Implementar el alcance declarado, GREEN y refactor; preservar originales y cambios ajenos.
- [ ] Ejecutar Verificación, gates de fase y revisión/QA correspondientes; registrar evidencia por SHA y escribir Changelog al cerrar.

**Notas**: Los paths nuevos son propuestas de implementación; los existentes proceden de seams O1. Cualquier ajuste de scope/contrato se declara antes de editar.




## Integración privada ROOT del plan candidato

ROOT conecta spec y design al plan propuesto en su layout futuro y declara ambos enArchivosT42. Esta integración sólo modifica enlaces/estado textual de propuesta y scope; conserva49CA/14F,42tareas,34E2E/15M y no apruebaimplementación. Originales delplanner yspec/designcanónicos intactos.


## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.


## T-01: concreción de disponibilidad por seam — 2026-10-11T16:55:17.175557+00:00

ROOT inicia contrato documental de dependencias sobre plan M3 aprobado. T01 no implementa ninguna función ni libera integración bloqueada de M1/M2: clasifica disponible/no disponible por componente, autoridad, SHA y gate. O1/D01 ya ratificada; D12 se concretará sobre fuentes actuales. Documenter fresco produce candidato privado con ownership dependency-contract.md y enlace de iteracion-creativa.md, TDD n/a prosa. Ledger sólo ROOT, sin permisos de servicio/GPU/DB/instalación ni cambios a modelos/schema/runtime. Revisión/QA y cierre T01 pendientes.


## T-01: candidato de dependencias verificado, revisión pendiente — 2026-10-11T17:26:43.427889+00:00

ROOT autentica4payloads y76fuentes no owned, contrato353b0df5 y arquitectura cbed2d35 que conserva prefijo original.25seams/77fuentes fijan corte histórico2026-10-11T16:55:17Z; no authority porhash. ROOT elige disponibilidad por componentes puros conformeADR0037/O1 para la evaluación de D12; ratificación final trasreview/QA/adopción. El corte no se atribuye al estado actual: desde entonces T04M2 cerrada4/30 y K1contrato incorporado, implementación aún pendiente. Revisión recibe overlayROOT actual, ninguna integración ni función M3 aceptada. T01en-revision, D12pendienteadopción, uso realnull.


## Revisión de dos lentes — intento 1: M3 T-01 — sin gaps

Lentes frescas A/B, alcance2documentos, scope0 yC/Dauto false. Tabla completa general/CA/D12/seams transferida de forma estructurada porROOT en .cache/dev-cycle/m3/dependency-contract-t01-review1-20261011/verdict-transfer-root.md, sin atribuir transcripción literal.0Critical/Important/Minor. Corte histórico77fuentes preservado y overlayROOT vigente leído, no ficticia autoridad por hashes. QA independiente422controles/gate0 posterior,50payloads/78fuentes autenticados. ROOTratificaD12/adopta2docs/cierraT01; M3=1/42. Sólo contrato de dependencias, no funciones ni integración. Diagnósticos auditores deUnicode/quoting/tablas/enlaces conservados y corregidos sólo en auditor; no fallos deproducto. TDD/cobertura n/a prosa. Uso realnull.


## T-02: concreción de ProductionRequest iniciada — 2026-10-11T18:02:56.726776+00:00

T01documental cerrada1/42. D02 requiere contrato por sujeto Asset/Analysis/Artwork/Render/Export/import/backup: campos/tipos/versiones/owner/terminal/CAS/fallos, captures y derechos, sin inferencia ficticia dePostPlan. Arquitecto fresco compara2–3opciones en snapshot privado; ROOTelige por delegación usuario y exige review/QA antesCAS. Sólo3documentos deT02; no modelos/migraciones/runtime ni derechos/custodia liberados porprosa. M1/K1revisión1A01Important pendienteFIX; M2=4/30. Todo productoM3/T12/T14 sigue bloqueado por sus gates; uso realnull.


## Git incremental T-01 — 2026-10-11T18:06:16.753962+00:00

Commit/push 08d7f3861d0951fca73eafae0c6dd7f246f24c47 verificado en origin/m1/t-02-esquema: cuatro documentos aceptados (contrato/apéndice/fusión explícitamente normalizada/QA), sin rutas personales; índice vacío. Se conserva excepción de rama compartida registrada, sin stageglobal/reset/checkout/mainmerge. Sólo componente documental. Planes/ledgers y dependencias aún pendientes de cierre Git; no se afirma clone/CI autónomo ni funciones M3.


## T-02/D-02: ROOT elige PR-O1 — 2026-10-11T18:10:35.263982+00:00

Delegación del usuario permite elegir alternativas. ROOT compara PR-O1/PR-O2 y selecciona captura única y ramas tipadas con reglas comunes de replay/CAS. Ratifica19pares operación/sujeto, versiones privadas1, serialización estricta sólo de nuevas capturas y límites de admisión request2MiB/recipe1MiB/text32768 porversión/sources64/parents64/roles64/profiles16/depth32, sin truncado ni cuotas ficticias de medios. Sources/lyrics/rights/perfiles sólo dentrorecipe; intent/revision runtime separados, no authority importable. Commitdurable prevalece sobreacuseperdido/cancelaciónposterior; UNKNOWN bloquea. Importcierrecompleto/maintenanceexclusivo/previewprivado preservados. Acta exhaustiva .cache/dev-cycle/m3/production-request-t02-concretion-20261011/choice-root.receipt.json; contrato/apéndices/ADR candidato/revisión/QA/adopción pendientes; T02no cerrado, productoM3no aceptado.


## T-02: PR-O1/ADR-0082 candidato verificado, revisión1 — 2026-10-11T18:39:37.290480+00:00

ROOTautentica9payload/76nonowned/2prefijosbyteexactos,19pares y7sujetosconcasisvalidos/invalidos,54linksdesdeDESTINOreportados. Contrato28b7de91/apéndices4b93f92f/d38fe199 yADRcandidato07c37ca6. ROOTreservaADR0082sóloparacandidatoprivado/añadeownershipT02ADR+índice, no canon publicado; sourceactororiginal9artefactosíntgros, numeración/punterocanónico metadataderivadosROOT. NormanPR-O1/choiceexactaantesRED, código/migration/rights/admission/UI/Enginev1no tocados. Snapshotreviewmezcla77? fuentesactuales másnormcandidateconoverlaydrifts; historicalinputpins declarados ycutsourcecanonicalactualsinfalseauthority. T02en-revision,1/42cerradaM3,nofuncionesM3aceptadas. QA independiente/adopciónpendientes, usagerealnull.


## Revisión de dos lentes — intento 1: T-02 ProductionRequest — sin gaps · 2026-10-11T18:48:30.954943+00:00

A/Bfrescas leen5docscompletos, scope0sinavisos/C-Dfalse. [Fusión completaROOT normalizada](testing/production-request-review1-2026-10-11.md),30criteriaA/9B ytodoslímites/noverifiedruntimeconservados; no transcripciónliteral. 81snapshot/9actorpayload/2prefixes/138links/19pairs7subjects auténticos.0Critical/Important/Minor, sinrebates/deuda; hipótesisresult_evidence_refdescartadano defecto demostrado. Sourceguardreadonly,dosdiagnósticosauditoresCRLF/render_n0no producto. QA documental siguiente paraD02/ADR0082,T02no cerrada/M3producto no aceptado/usagenull.


## Git incremental T02 — 2026-10-11T19:08:04.950329+00:00

Commit/push 23ec7207181788733e18fef5be9be702e1d278f2 verificado en origin/m1/t-02-esquema, 7archivosaceptados,índicevacío, sin rutas personales ni data/modelos. Rama compartida bajoexcepciónya registrada; nostageglobal/reset/checkout/mainmerge. Componenteaceptado T02, no clone/CI autónomo ni hito completado; no incorporadoscambiosajenos. Uso realnull.


## T-03/D-03: concreción de datos y migraciones iniciada — 2026-10-11T19:20:00.846060+00:00

T01/T02documentalescerradas2/42, ADR0082accepted/source23ec7207publicado. Arquitectofresco compara2–3opciones SQLaditivas/revisiones/owner/CAS/rollback antesROOTelegiryantesRED de T12/T14. BaselineAnalysis originalyexcepciónADR0074 intocadasporanalogía; datos/MixRevision/LyricsTimingRevision/Profile/intent/receipt propios, sin ORM/migraciones ejecutadas enestaconcreción. Rolarchitectproducedesign.mdprivadoyrutacandidatoaliasROOTproduction-data-contract.mdaladoptar; apéndicedatos propuesto comodiseño,copiaROOT trasreviewQA. Sourcecuts/current metadata liberaciónporcomponent/nofullM3grants; T03abierta,uso realnull.


## T-03/D03: PD-O1 contrato congelado, revisión1 preparada — 2026-10-11T19:52:18.912652+00:00

Architectfreshresume_m3_t03_data_contractDONE/sourcef982b1bd105751B592líneas/99pinsintactos,40tablas/14familiasguards/19pares7sujetos/20grupostestfuturos. ROOTextrae apéndicedatos yADRcandidatomarcados byteexactos; reserva0083sólonamespaceprivadopararevisión,noadopción; fuenteoriginal/opciones428b5c ychoicec0c651ce intactas. Contrato/dataprefijo/ADR/index4docsdiff; canon sóloledgerROOT. T03enrevision,M3=2/42documentales,funciones0, noSQL/DDL/ORM/DB nativocustodia ni derechos otorgadosporprosa. M2T05contratoactualprivado5f695a6d enreview yK2docadoptadopublicado755b476/K4aconcreción, noheadmigrationcambiado. Readers/gatesD04/05–09/11/12posterioresobligatorios; baselineAnalysis/Asset/ADR0074conservados. Reviewfresca/QA/adopciónpendientes; usorealnull.


## Revisión de dos lentes — intento 1: D03 — ImportantB01 confirmado · 2026-10-11T20:11:41.906146+00:00

ROOTnormaliza29A/25Bcriterioscompletos yconfirma colisión kindseal/root(C350/354) en6familias; noCapturedRefenumgapadicional. 0Critical/1Important/0Minor, sinrebates. FIX1frescoescogeJSONseal_kindreservado distinto dekindroot, sin cambiarSQL/históricos/outerD02/PKFK/domaines. Propagarreader/proyección/G09/casos/apéndice/ADRcandidato. Fuente f982 original/101pins permanecen intactos; sinQA/adopciónD03/ADR83/cierreT03/DDL/M3green. T03enprogreso/M3=2/42functions0. Tabla completa testing/production-data-contract-review1-2026-10-11.md; uso realnull.


## T03/D03 FIX1: revisión2 preparada — 2026-10-11T20:22:01.002729+00:00

FIX1frescoDONE/sourceca094b15124361B/101readonlyintactos; B01 colisiónJSON corregidodocumentalmente conseal_kindreservado distinto dekindroot. 40tablasintactas/11fieldsets384columnas/0reservedcollisionsreportados; exactclosedprojections/decoder/G09/allfamilies/examples/apéndice/ADRcandidato propagados, SQL/outerD02/históricos sinreescritura. ROOTverificasources yextraetodosapéndicesbyteexact; ADR0083/indexprivadoreviewnoadopción. Revisión2 recibe29A/25B completos+ImportantB01previo; scope4docs/noSQL. T03enreview,M3=2/42functions0;QAadopción/DDLproducto pendientes; uso realnull.


## Revisión de dos lentes — intento 2: T03/D03 — B01 corregido documentalmente · 2026-10-11T20:43:17.548818+00:00

ROOT29A/25Bcriterioscompletosnormalizados,0Critical/Important/Minor nuevosopendientes/sinrebatesdeuda. JSONseal_kindreserved independiente dekindroot sin cambiosSQL/outerD02/históricos;101pins/sourceca094b15124361B/40tablas384cols/11fieldsets0reservedcollisions/prefix4.10SQLexactos. QAdocumental/adopciónROOTpendientes; fullT03/DDL/readersrealnoacreditados, M3done2/functions0. ROOTM2datosapéndiceadoptado despuéssnapshot se preservará enQAoverlay declarado. Uso realnull.


## T03/D03: QA documental independiente preparada tras revisión2 limpia · 2026-10-11T20:46:45.125029+00:00

29A/25B completas/B01JSONkindcorregido conseal_kindreservado.0gaps nuevos/pendientes. ROOTpreserva datosapéndiceM2durable reciénadoptado yADR0084/indexratificados;apéndiceD03 yADRcuerpo normativos siguenexactos/sourceca094b15124361B. ContextoQA se rebasa sóloenROOTdocumentosaceptados/ledgeradministrativo, no SQL/modelschemahead0007changes. Diff4docs/scopepuertasreales; T03enreview/M3done2/functions0. Noadopción/procesos/servicios/GPU/códigocanónico. Uso realnull.


## T03/D03 cerrado documentalmente por ROOT — 2026-10-11T20:57:46.782766+00:00

10criterios/subtareasdeconcreciónverificados; fuenteca094b15124361B/40tablas384cols/11fieldsets yQA579/579. ROOTadopta4docs conmetadataADR83/indexestadoaceptada,datosprefijoM2preservado/ADR84rowindexintacta. Revisión2A29B25clean,B01corregido. SQL/ORM/custodia/media/timing/mix/cover/video/exportsE2E15manuales siguen pendientes; M3=3/42DOCUMENTAL/functions0. D04formatportable siguiente; código productorequiereD04..12 ydeps reales. PDFgenerado/hash verificado HTMLprintfirstlast inspeccionado, norasterPDF;procesosChromepropiosausentes. Uso realnull.


## T-04/D04 — despacho documental con contexto fresco — 2026-10-11T21:29:46.934069+00:00

TDD n/a: prosa de formatos/compatibilidad; no implementa codecs, migración ni productores. Dependencias T02/D02 y T03/D03 aceptadas; T03 fuente ca094b15 y QA579/579. ROOT libera snapshot privado readonly y un único candidato production-format-contract.md. Formatos por sujeto, dispatch histórico y goldens por origen deben conservar bytes v1/v2 y las condiciones CPU sin inferencia ficticia. Alternativas se comparan y ROOT ratifica por delegación del usuario; ADR específico antes de cualquier formato incompatible. No cambia schemas/runtime/canon por el despacho. M3=3/42 documentales, funciones0. Uso real null en el medidor único del lote.


## T-04/D04 — candidato PF-O1 congelado y revisión1 preparada — 2026-10-11T21:43:55.590486+00:00

Architect fresco DONE fuente48db6312/69274bytes/128readonlySHAestables. ROOT ratificó PF-O1: registry family/reader/version, formatos M3 tipados sin ampliar v1/v2 históricos; índice SongBundleM31 siempre familia nueva. PF-O2manifiestouniversalv3 descartado. Verificación del actor documental; 21vectoresnormativos/12gruposnegativos no equivalen a goldens ejecutados ni producto. ROOT prepara5docsdiff y reserva ADR0085 sóloprivado por decisiónformatsdocumentada; amplía ArchivosconADR/index/reportesdeestaunidad porAGENTS§3, sinexclusionesglobsdeproducto. Nada adoptado ni código liberado. T04enrevision/M3=3/42documental/functions0. Uso realnull.


## Revisión de dos lentes — intento 1: T04/D04 — B01Important confirmado — 2026-10-11T21:53:15.020435+00:00

FULL32A/5B/0Critical1Important1Minor. B01metadata_refTake/audioforzado enprojectZip rechazaSongválidasinTake: ROOTconfirmaPR116/PF147/233; AconformidadacotadaanteB. A01Minorfrase45palabrasPF159. [Informe](testing/production-format-contract-review1-2026-10-11.md). Source48dbhistórico/130pins/21vectores12negativos, runtime0. FIX1fresh sourceúnicoconO1intacto: metadata_refNULL literal sólo project_zip, closurepreservaSonghistoria sinTake/audioficticios, otrosmetadataTakeexactos; prepared/final/goldens/negativos/ADR/apéndicescoherentes. Fuentescanónicasnoadoptadas, T04enprogreso/M3=3/42documental/functions0. Usorealnull.


## T-04/D04 — candidato PF-O1 congelado y revisión2 preparada — 2026-10-12T04:17:23.298658+00:00

Documenter FIX1 DONE fuente cf967985/76811bytes/129readonly SHA estables; anterior architect READ_ONLY sin escrituras, incidente de despacho conservado. ROOT ratificó PF-O1: registry family/reader/version, formatos M3 tipados sin ampliar v1/v2 históricos; índice SongBundleM31 siempre familia nueva. PF-O2manifiestouniversalv3 descartado. Verificación del actor documental; 22vectoresnormativos/13gruposnegativos no equivalen a goldens ejecutados ni producto. ROOT prepara5docsdiff y reserva ADR0085 sóloprivado por decisiónformatsdocumentada; amplía ArchivosconADR/index/reportesdeestaunidad porAGENTS§3, sinexclusionesglobsdeproducto. Nada adoptado ni código liberado. T04enrevision/M3=3/42documental/functions0. Uso realnull.


## T04 formatos — revisión2 A/B sin gaps; QA documental liberada — 2026-10-12T04:27:32.366541+00:00

FULL32A/5Bpreservado,A01/B01corregidosdocumentalmente. Fuentecf967985/130pins/5docsdiff22vectores13negativos,0runtimegoldensejecutados. [Informe](testing/production-format-contract-review2-2026-10-12.md). QAindependiente antesadopción5docsycierreT04documental. M3=3/42/functions0.


## T04 formatos adoptados — 2026-10-12T04:36:08.008220+00:00

ROOTCAS5docs/ADR85aceptada,4/42tareasdocumentalesM3/functions0. QA46/46/R2FULL32A5B0gaps. M0/M1/M2/fullM3/M4M5 pendientes; objetivo completo no logrado. Uso realnull.


## T05 medición audio — concreción D05 liberada — 2026-10-12T04:38:14.858470+00:00

T04documentalaceptada. PrepararcontratoLM/TP/SNRsuma/alineación/equivalenciamixPCM/silencioclipcodecfinal con medidor/pin/fórmulas exactosyfailclosed, antesmediciones realesdependientes. ROOTdelegacióneligepreferenciaO1herramientalocalFFmpegexistente+PCMdeterminista, sujetaafactibilidadverificada; no nuevasdependencias ni normalización/limitador oculto. Candidatoprivadodocumental→revisión→QA→ratificaciónROOT. T05enprogreso/M3=4/42documental/functions0.


## M3/T05 D05 candidato congelado; revisión1 preparada — 2026-10-12T09:33:16.440147+00:00

GenericTask brief-only compatible DONE contrato07767756/80070B;139readonly intactos/10payloads/30checks. ROOT eligeAM-O1 por delegación; proponeADR0086/pipeline derivados exactos. Incidentes implementerDENY ydocumenterREADONLY íntegros, ninguna suplantación niALLOWinventado. Cuatrodocsdiff; seis métodos/11perfiles/17errores/4estados privados cerrados,22vectors especificados0ejecutados. A/Bfrescos+QApending, noadopción nihabilitarcapacidad. T05enrevision sólo documental/M3=4/42funciones0; uso realnull.


## Revisión de dos lentes — intento 1: M3/T05 D05: dosImportant — 2026-10-12T09:50:35.089053+00:00

FULL60A34B,scopecuatrodocs0fuera/C-Dfalse. A0gaps,B01rights_refCapturedRefD02familyexcluyerightsproduction.rightsD03;B02sentinel/insuficiencia/originalfailedstatesdisjuntos. [Tablasfull](testing/audio-measurement-review1-2026-10-12.md). Metadatamodeomitindicio descartado,noigualdadexplícitaentreM/Tagsydependenciespermitidas. T05vuelveenprogreso;ROOTreleaseFIX1genericTaskcompatible sólo contrato1fuente141snapshot140readonly,derivadosregeneraráROOTdespués. Rawcapacityretry/fallostdoutcp1252preservados, audioactual0. NoQA/adopción/cierreM3.


| # | Grado | Gap | Tarea | Corrección aplicada | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B01 rights_ref no admite family rights de production.rights/1 D03 | T-05 | pendiente | C147/153; D02CapturedRef81 vs D03reader414; FULL60A/34B testing/audio-measurement-review1-2026-10-12.md |
| 2 | Important | B02 Estados sentinel/insuficiencia/originalfailed disjuntos sin precedencia | T-05 | pendiente | Fs48000 N19199: C63/238vs87; original SOURCE_MISMATCH: C196/242vs235; FIX1 privado aún no validado |


## T-05 D05 FIX1 congelado y revisión2 preparada — 2026-10-12T10:04:42.713842+00:00

ROOTaudita19ownedpayloads/140readonlySHA; fuente15608698/94564B,43checks/14negative-doccases/22AV0audio. RightsSnapshotRefD05tipoexactoseparado4keys/familyrightsreaderproduction.rights1; estadosporfase/methodyoriginalnot_requested sinsentinel−70falsoI. Revisión1FULL60A34B+2ImportantB01/B02conservadospendienteshastaA2/B2; noQA niadopción. ROOTregeneraADR86/pipelineindexdesde fuenteactual, noactorderivativesviejos. Scope4docs, aplicación0. T05enrevision/M3=4/42;actualusagenull.


## Revisión de dos lentes — intento 2: T-05 D05 — B01/B02 corregidos — 2026-10-12T10:22:25.227171+00:00

FULL60A/34B;0Critical/Important/Minor, C/Dfalse/scope4/0/0. [Informe completo](testing/audio-measurement-review2-2026-10-12.md). B01tipoRightsSnapshotRefexact/D02enumintacto yB02precedencias método/fase/originalnot_requested corregidos; metadataomit nunca gap. QAindependiente fuente15608698/94564B/4docspending, ningúnmedio/funciónactualliberado.

| # | Grado | Gap | Tarea | Corrección aplicada | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B01 CapturedRefD02familyexcluyerights | T-05 | corregido | C147/153/262 nuevoRightsSnapshotRefD05cuatrokeys,D0281intacto,D03414coincide; A2/B2independientes |
| 2 | Important | B02 estados de ausencia/originalfailed disjuntos | T-05 | corregido | C63/87/196/233–258N19199/−70ambiguous/originalalwaysnot_requested; A2/B2independientes |


## T-05 D05 documental adoptado — 2026-10-12T10:41:06.440274+00:00

ROOTCAS4docs/ADR86aceptada/T05completadodocumental;M3=5/42,funciones0. QA47/47/R2FULL60A34B0gapsactuales,B01B02historiacorregidos. Derechos/método/intervalos/cola/originalstates fijados antesREDproducto. Audio/AV/readers/SQL/render/E2E/manuales ytodosotrosM0–M5 pendientes: objetivo no logrado. Uso realnull.


## T-06 D06/D13 candidato documental; revisión preparada — 2026-10-12T11:25:56.556747+00:00

Fuente163e3863/70034B,31checks documentales/141readonlydiff0/142snapshot y12artefactos verificables. ROOT propone CM-O1/CM-P1 para revisión, sin ratificación todavía. D13material/personas/anotaciones, runtimegatecoverageTDD/QA y producto siguen pendientes. T06 en-revision del componente contractual; no cierre ni claimmusical. PREfinal4536 supersedido sin bytes contemporáneos, metadata/stdout preservados y declarado; FINAL nuevo31/31 con copiaexacta contract-final.bin. Scope3docs y revisión independiente A/B; agenda secuencial por4slots con2implementaciones vivas, mismos bytes y sin compartirveredictoentrecontextos. La diferencia de agenda no reemplaza independencia, lensesauto deterministas. T06full/M3/Fase1 siguen abiertos; IA actualnull.


## Revisión de dos lentes — intento 1: T-06 D06/D13 — dos Important — 2026-10-12T11:55:31.921050+00:00

A/Bfrescos FULL leídos y fusionados,143pins0diff/3docs/scope0fuera/C-Dfalse. [Tablas completas](testing/cohort-metrics-review1-2026-10-12.md). A01 score0..1 vsrating1..5/min4; A02/B01 cicloSHAinventario↔ROOTreceipt deduplicado. B's ✓genérico no rebate elcasoA01 específico. T06 vuelveenprogreso; FIX1freshgenericTaskcompatible1owned143snapshot142readonly. Ningunaadopción/QA/cierre, actualgatecode/D13/personas/material/human/productopendientes.31DOCno pruebas musical/cov, thresholds siguen propuestasROOT.

| # | Grado | Gap | Tarea | Corrección aplicada | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A01 Metric.score0..1 no admite ratingshumanos1..5/min4 | T-06 | pendiente | CM61,79,110,118,132,136,138,140; A1casoscore4 yunidadcerrada |
| 2 | Important | A02/B01 inventario y ROOTreceipt exigen hashes completosmutuos | T-06 | pendiente | CM167,171,175; A/Bindependientes I→SHA(R)→SHA(I), valid100/100 noemitible |


## T-06 corrección contractual auditada; revisión intento 2 preparada — 2026-10-12T12:30:32.661730+00:00

ROOT verifica los61artefactos completos,142readonly sin diferencias/reparse y contratoFINAL6cc06770/99562B/532líneas. Copias before/intermediate/FINAL y fallos de harness preservados;56DOC y ejemplo sintético39artefactos/7ciclos no son TDD/producto/cobertura oficial. A01 rating humano1..5 separado delscore0..1 y A02/B01 cadena acíclica fullbyte propuestos; no se consideran corregidos hasta revisión independiente. ADR0087/index privados regenerados literalmente desde FINAL. Revisores frescos reciben tablas FULL A/B y ambosgaps previos, sin otros veredictos del intento2; agenda A luegoB por4slots con2implementaciones vivas. CM-O1/P1 siguen propuestas, no ratificadas; instrumentoactual/raw/coverage/QA/Verificación y D13material/personas/anotaciones/actas/producto pendientes. T06full/Fase1/M3 abiertos; alcanceM0–M5 intacto y métricasIAactualnull.


## Revisión de dos lentes — intento 2: T-06 D06/D13 — A01/A02 corregidos — 2026-10-12T12:56:09.996549+00:00

A2/B2 FULL independientes fuente6cc06770/143pins/3docs,scope0fuera0warnings/C-Dfalse;0Critical/0Important actuales/1MinorA03. [Informe completo](testing/cohort-metrics-review2-2026-10-12.md). Agenda secuencialpor4slots/capacityretries declarados, sinveredictoA2aB2. QA documental pendiente, sinadopción/ratificación/cierreT06/Fase1/M3. InstrumentoTDD/raw/oficialwhole80/Verificación yD13material/personas/anotaciones/actas/producto siguenpendientes; fixture39 no ejecuciónoficial. IAactualnull.

| # | Grado | Gap | Tarea | Corrección aplicada | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A01 Metric.score0..1 vs ratinghumano1..5/min4 | T-06 | corregido | CM61/65/82 ratinginteger separado,completo/NULL/count;A2/B2 |
| 2 | Important | A02/B01 SHA completocíclicoI↔R | T-06 | corregido | CM169/177/185/206–233 ordenacíclico/hashbytesíntegros/custodiaindependiente;A2/B2 |
| 3 | Minor | A03 descripciónCM522derivadosprivadosprevios | T-06 | pendiente,no bloquea | CM522frenteCM502–514=ADR87:7–19;aclarar corteWorker vsderivaciónROOT |


## T-06 adopción normativa parcial — 2026-10-12T13:23:49.279192+00:00

ROOTCAS3documentos;no cierreT06/Fase1/M3 ni incremento de tareascompletadas. CM-O1/P1 ydominios/umbrales completos ratificados antesREDinstrumento. Source6cc06770 intacto, overlaysADR/index declarados, QA287/26own/143pins/61supports/213inputs; A03provenienciaaclaradaexternamente. Instrumentocode yD13/producto pendientes; objetivoM0–M5activo/IAactualnull.


## T-06 instrumento real — despacho a implementer fresco — 2026-10-12T13:37:46.919874+00:00

Contrato6cc06770/CM-O1-P1/ADR87ratificados/QA287 adopciónnormativa aceptada; se implementan **scripts/m3_coverage_gate.py ytests/test_m3_coverage_gate.py** con causalRED-GREEN-REFACTOR porcriterio. Snapshotprivado151readonly/2ownednuevos inicialmenteausentes, branchm3/t-06-coverage-instrument/privateGitbasef17b5e08cba567ceb55f49016fd3d8717c163e28; actorúnicamentecode2owned/evidencecache. GuardsimplementerWrite2ALLOW real enbranch, nolib/newdeps/Native/GPU/servicios/media. ROOTúnicoledger/Git/canon; actorreportaTDDrawpreimages/comandos/exits/reason yROOTregistra. Debenimplementartodaslasformas/casos§8,CLIexits0/1/2,whole80porcadafuentereal sinomit/excl/missing,officialraw/config/maps/source/pins/ROOTcustodyreal. Fixtures39sirvennegativos/structural,noauthRootfabricada/niflagbool/pureJSON→productionpass. Si lacustodiaconcreta exigeadaptador, proponerantescodecódigo,seguirnegativosindependientes; positivooficial necesitaejecuciónrealROOTconmismaSHA. Freshrevisiónselector/ABCDcuandoaplique/QA antesCAS. Instrumentonoacreditaconformidadmusical/D13adquisición niT06full. ObjetivoM0–M5activo/IAactualnull.


## T-06 — instrumento con observación independiente en desarrollo — 2026-10-12T14:08:57.345895+00:00

Componente normativo adoptado tras freshA2/B2 y QA287; contrato6cc06770 exacto, ADR87aceptado y commit603e7c83 publicados. T06 sigue en-progreso. Implementer fresco trabaja en cohort-metrics-t06-gate-runtime-20261012/snapshot,151readonly y sólo scripts/m3_coverage_gate.py/tests/test_m3_coverage_gate.py owned. CLI productivo sin collectorROOT independiente produce pending/exit2 aunque reciba100/100 JSON; tests con SyntheticObserver no acreditan observación ROOT real. ROOT aprueba API interna main/evaluate(...,observation=collector) con mismos flags/stdout/exits y observaciones de preaprobación/ejecución/branch-N/A; SourceMap completo requiere mapper oficial y pairing verificado por observe_mapping, nunca flags/JSON ni mapper inventado. Prueba positiva real, toda Verificación literal en contexto independiente, cobertura whole80, freshreview y QA siguen pendientes. Ausencia de mapper/custodia→pending, corrupción demostrada→fail. Los tags, rúbricas y métricas aún no son evaluación de audio real ni acreditan naturalidad/Suno.


## T-06 — instrumento: revisión adversarial inicial preparada — 2026-10-12T14:26:42.506029+00:00

Nueva unidad funcional del instrumento, intento1 separado de las revisiones del componente normativo ya aceptado. ROOT auditó151readonly, dos fuentes nuevas f99b35f7/a58783b0 y933payloads declarados de soporte/cache. Actor102PASS/1SKIP Windows symlink1314, whole715/815líneas y388/478ramas sin excluidos,25paresRED/GREEN; sigue sin QA independiente. ROOT ejecutó collector propio externo con hijos reales de inventario y Coverage7.16.2, preaprobación por bytes antes de run, ambos caminos4/4líneas2/2ramas, contexto in-memory independiente y relectura de todas las fuentes/outputs. Fuente438ce0 falló RAW_ALIAS_AMBIGUOUS por separador nativo Windows; raíz freeze1 preservada865payloads. Fuentef99b35f7 corrigió exactOSpairing trasREDfocal y obtuvo Rootgreen4exit0/pass, sin editar el raw oficial. HarnessROOT fallidos anteriores1/2 y rawRED3 conservados, no declarados TDD de producto.

FreshA/B y lentesC/D decididas por selector se harán sobre copia153pins, diff completo sólo dos nuevos módulos, aislada del checkout compartido. Objeto revisado: instrumento§8 y su integración de collector externa aún pendiente; no pedir verde de fullD13/T06/M3 ni de música a partir de este fixture. CLIstandalone continúa pending2 sin collector, un APIpositivo observado no prueba wiring de uso real; TS/map oficial, Combined y branch-N/A oficiales adicionales siguen limitaciones explícitas. ROOT único canon/ledger/Git, IAactualNULL.


## Revisión de dos lentes — intento 1: T-06 instrumento funcional — siete Important pendientes

ROOT fusiona freshA1/B1 sin compartir veredictos entre lentes; ambos recorrieron3032líneas completas,153pins intactos, C/Dauto false, scope2/0fuera/0avisos. La revisión normativa previa está aceptada por separado; esta es la primera revisión de código. A102PASS1SKIP/B102PASS1SKIP CPU no suplen Verificación/QA. FULLtablas normalizadas en `.cache/dev-cycle/m3/cohort-metrics-t06-instrument-review1-root-20261012/lens-a1-root.md` y `lens-b1-root.md`.0Critical/7Important/0Minor, todos pendientes; taskT06 sigue en-progreso.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A01: CLI no conecta collector al entrypoint | T-06 | pendiente | scripts/m3_coverage_gate.py:1574; Rootgreen4 APIpass0, standalonepending2; nueva integración trusted embedding por memoria, jamás JSON/env/flag como permiso |
| 2 | Important | A02: Reportschema inválido devuelvefail1 | T-06 | pendiente | scripts/m3_coverage_gate.py:768; P={schema_version:1}→CLOSED_SCHEMA1, debe2; bindingmismatch demostrado sigue1 |
| 3 | Important | A03: Rounded/frontera test no causal | T-06 | pendiente | tests/test_m3_coverage_gate.py:720; raw100000/fuente200→RAW_SOURCE_RANGE antes umbral; probar BELOW_MINIMUM79999/100000 yPASS80/100 con fuente/rangos válidos |
| 4 | Important | B01: raw/meta get sin validar tipo | T-06 | pendiente | scripts/m3_coverage_gate.py:832; raw[] o meta[] AttributeError/stdout0; debeJSONnoverdesegúninvalidez |
| 5 | Important | B02: sourcesContent elemento no string | T-06 | pendiente | scripts/m3_coverage_gate.py:1203; sourcesContent[1] AttributeError/stdout0; mapaexistente corruptoJSONfail1 |
| 6 | Important | B03: UTCorden lexical incorrecto | T-06 | pendiente | scripts/m3_coverage_gate.py:1097; 00Z→00.500Z falla yordeninversopasa; comparar datetimeUTC real |
| 7 | Important | B04: Istanbulversión ignorada | T-06 | pendiente | scripts/m3_coverage_gate.py:1178; vitest9999.0.0→pass0sintético; unsupportedreader pending2 |

ROOT decisión de implementación A01 — 2026-10-12T14:57:38.424372+00:00: mantener flags/exits/schemas y el default sin contexto pending2. El CLI podrá ejecutarse como __main__ mediante embedding confiado de ROOT con factory/observer exclusivamente in-memory fijado por el caller externo después de sus observaciones reales; nunca cargar autoridad desde argv, JSON, env, fichero de import dinámico ni boolean. El factory recibe el constructor ObservedEvidence de la ejecución actual para evitar falsa identidad de clase entre import y runpy; no realiza captura ni preaprobación dentro del código evaluado. ROOT repetirá collector propio ejecutando el entrypoint real con los mismos flags y __main__, fuente congelada y bytes reobservados, stdoutJSON/exit reales; un seam unitario no completa ese gate. Si esta integración no satisface la Verificación literal bajo contexto independiente, continúa pendiente, no se rebaja contrato. Implementer puede proponer brecha reproducible de este mecanismo, nunca introducir permisos de datos.

B04 se corrige de manera conservadora con perfiles fijados explícitos: Python7.13.1normativo/7.16.2observado; Istanbul perfilnormativo de fixtures vitest3.0.0. El checkout actual declara vitest/@vitestcoverage-v8=5.0.3; no se presenta como perfil oficial soportado sin raw/mapping real de esa versión. Unknown toolname/version permanecepending2; ningún tag boolean o permissive regex admite9999. No instalar deps ni ampliar tool locks. Futura calibración real JS se mantiene pendiente.

Fix1 subagente fresco privado sólo G/T; TDDREDcausal porcada gap y fuentes antes de verde, sin modificar payloads anteriores/review/Rootfixtures. Último READMECLI, TS/Combined/N/A reales/D13/fullT06/QA/producto siguen pendientes. MetricsIAactualNULL.


## T-06 — instrumento: segunda revisión preparada — 2026-10-12T15:25:52.796748+00:00

ROOT auditó 151readonly y3955payloads FIX1; fuentes6b435684/4cd44a91. Diez RED causales y GREEN preservados;114PASS/1SKIP y cobertura oficial entera734/831líneas395/482ramas0excluidos. Los siete Important del intento1 requieren nueva evaluación fresca, no quedan cerrados por autoevaluación. ROOTmainGreen5 ejecutó __main__ real mediante runpy e in-memory factory de collector externo con hijos reales Coverage7.16.2; exit0/pass, fixture4/4líneas2/2ramas. Standalone sin collector sigue pending2; no producto/IPC/JS5.0.3/Combined/branch-N/A/música acreditados. FreshA2/B2 reciben FULLtablas anteriores y Rootdecisión; QA independiente y adopción acotada aún pendientes. T06/D13/Fase1/M3 abiertos; IAactualNULL.


## T-06 instrumento — revisión fresca2 en curso — 2026-10-12T15:31:21.635456+00:00

ROOT verificó153pins y3955payloads FIX1, fuentes6b435684/4cd44a91,114PASS1SKIP,whole734/831L395/482B0excluidos y10RED causales. Collector externo ROOTmainGreen5 ejecutó __main__ real confiado con factory in-memory de observaciones independientes,4/4L2/2B/exit0pass, sin grants argv/env/JSON. Standalone sin collector siguepending2; no installedorchestrator/IPC/JS5.0.3/Combined/N-A/música acreditados. FreshA2/B2 paralelos reciben FULLtablas1 y7Important; no cierre por autovaloración. Scope2files0fuera0avisos;C/Dfalse; prepare .cache/dev-cycle/m3/cohort-metrics-t06-instrument-review2-root-20261012/prepare-root.receipt.json SHA2dcaa33fba554151930a9743f7a5226f2df96cbba12776f3143a7fe99934e528. Preparación corrigió filename asumido antes de ledger/Git, payloads íntegros re-auditados por recovery sin repetir pruebas. QA/adopciónCASCódigo/D13/Verificación/T06/M3 pendientes. IAactualNULL.


## Revisión de dos lentes — intento 2: T-06 instrumento funcional — un Important residual

FreshA2/B2 completos,2files3327difflineas153pins/3955support/37ROOTpayloads iguales,C-Dfalse,scope0fuera0avisos. A0Critical0Important0Minor,114PASS1SKIP53.04s; B0Critical1Important0Minor,114PASS1SKIP47.10s. FULLtablas lens-a2-root.md/lens-b2-root.md en cohort-metrics-t06-instrument-review2-root-20261012. A01/A02/A03 yB02/B03/B04 corregidos; B01runner corregido pero Combined conserva .get antes de tipo. Dos pruebas __main__ sintéticas reatanSHA/Ec/Cc/P después de raw[]/meta[], dandoexit1stdout0AttributeErrorG1445; ROOT verificó fuente y raws. No prueba de collectorrealCombined, no se confunden permisos sintéticos con autoridad.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B01-R: Combined raw/meta get antes de validar tipo rompe JSON | T-06 | pendiente | scripts/m3_coverage_gate.py:1445; probes.json ycombined_raw_array/meta_array entrypoint.stderr bajo cohort-metrics-t06-b2-evidence-20261012 |

Fix2 fresco privado G/T sólo: reproducir ambas variantes RED causal antes de corregir, validar tipos antes de acceso usando misma clasificación contractual RAW_INVALIDpending2 en runner/combined; nunca blanket-except que oculte corrupción probada. FULLtablas2 y1 se conservan; freshreview3 reevaluará sólocorregido salvo nuevoevidencia. Mantener factory exclusivamente in-memory del collectorROOTexterno, CLIflags/schemas/exits/unsupportedJS5.0.3/guards/map y UTCDecimal exactos. ≥80 wholefichero líneas/ramas/total enrawoficial7.16.2 sinexclusiones. ROOTreal__main__ despuésfreeze aún requerido; QA/CAS/D13/fullT06/M3pendientes. UsoIAactualNULL.


## T-06 instrumento — FIX2 fresco iniciado — 2026-10-12T15:41:24.680041+00:00

Freshimplementer fix_m3_t06_instrument_runtime_2 en cohort-metrics-t06-instrument-fix2-root-20261012/snapshot,2owned151RO/releaseROOT/branchprivate/guardrailssilentALLOWactivo. Corrige sóloB01-RCombinedraw/meta tipo→JSONpending sinblanketcatch; REDfuncionalprevio paraambos, noauthorityschema/CLI/UTC/map/profilechange. RecibeFULL4tablas de reviews1/2 y Rootdecisión; revisión3fresh despuésfreeze/Rootreal__main__ y QAaúnpendientes, T06D13M3abiertos. Recibo .cache/dev-cycle/m3/cohort-metrics-t06-instrument-fix2-root-20261012/release-root.receipt.json SHA1f257d1288f37cf46ce5eba9bfcf5e2ea0171f6b018a768afe14a947495b362a.


## T-06 — instrumento: tercera revisión preparada — 2026-10-12T15:50:57.426565+00:00

ROOT auditó151readonly/6216payloads FIX2; fuentes e18dd17b/9fb5c1c, dosRED causales __main__ Combinedraw[]/meta[] conDAGreatado.116PASS1SKIPwhole738/833L397/484B0excl. Literalactor sinSHApre propia, correlaciónCoverageconcurrenteguard declarada; no inventar observación y QAindependiente ejecutaráliteralconguardpre/postreal. ROOTmainGreen6__main__trustedfactoryparentexterno,hijosinventario/Coverage7.16.2reales4/4L2/2Bexit0pass. B01-Rrequierefreshreview3; FULLveredictos1/2 se conservan. A3/B3secuencialporROOT+M1+M2/cuatroplazas; segundo no recibeveredictoA3. Standalonepending2/productIPC/JS5.0.3/CombinedN-Areal/músicalímitesintactos;QA/CAS/D13/T06/M3abiertos,IAactualNULL.


## T-06 instrumento — revisión3 A verde, B en curso — 2026-10-12T16:06:50.035098+00:00

ROOTauditoríaFIX2fuentes e18dd17b/9fb5c1c/151RO6216payloads;mainGreen6colecciónindependienterealhijosinventory/Coverage7.16.2 antes__main__trustedfactory/4L2B0pass. Recibo .cache/dev-cycle/m3/cohort-metrics-t06-root-real-main-green6-20261012/ROOT-result.json SHAb9336f229bae5b90d0eac74f99a712807d7d5d2b15787a97093de5907358bff2. Revisión3private153pins/2files3384difflineas/scope0fueraavisos/C-Dfalse. FreshA3fullcriterios0Critical0Important0Minor,116PASS1SKIP60.50s/probesCombinedrawmeta2JSON/mismatchcorruption1; fuentesintactas, FULLA3 ROOTpersistidoincluyendo todoscriteriosprevios+actualización yNV. Report ROOT inicialPSstdinunicode se codificólossily sóloencontenido nuevo; recoveryUTF8exacta conpreimagepreservada, tablaFULLprevia/runtime/evidenciaintactos. FreshB3secuencial vivo y NOrecibeA3veredicto.

Literalactor116PASS1SKIP73.56sexit0carecepreSHApropia,corrCoverageconcurrenteguard NOpreobservacióndirecta. QAindependiente posterior ejecutaráliteralconguardPREPOST; no se rebaja criterio ni se declarafullT06. standalonepending2/JS5.0.3/TSmapper/CombinedN-Aoficial/música/installedIPCsinclaim. QA+CASCódigo/D13T06M3pendientes, G/Tcanonicaltodavíaausentes.


## Revisión de dos lentes — intento 3: T-06 instrumento funcional — cero gaps pendientes del componente

FreshA3/B3 completos ysecuencialespor4plazas; B3no recibióA3veredicto.0Critical0Important0Minor ambaslentes;FULLtablas lens-a3-root.md/lens-b3-root.md en cohort-metrics-t06-instrument-review3-root-20261012.2files3384difflineas,sóloFIX2cuatrolíneasguardG+65T;153pins6216actorpayloads37ROOTpayloads intactos,scope0fuera0avisos,C-Dfalse. A116PASS1SKIP60.50s/B116PASS1SKIP60.25s;B9subprocessCombinedbaseline0y6malformed2JSON,mismatch/formatcorrupt1. B01-Rcorregido, A01A02A03B02B03B04conservados; ningúnNVoficial/humano/producto aprobado por esteveredicto.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B01-R: Combined raw/meta malformed rompía JSON | T-06 | corregido en componente | scripts/m3_coverage_gate.py:1443–1446;tests/test_m3_coverage_gate.py:1220; freshB3nueveprobes __main__,raw[]/meta[]/NULL/scalar→2RAW_INVALIDJSON1236Bstderr0 |

QAindependiente del componente CLI/CPU, sinUIpor diseño de este componente, NOdelhitoM3conUI: copia153pinsRO yprofile/plancomponente privado. Debe ejecutarVerificaciónliteralUVdeclaredconPREPOSTSHApropia(exigencia pendiente poractorcorrelaciónCoverage), wholeGoficialantesimports≥80L/B/total0excl/omit/partial, raw/XMLySHAexactos. Si qa-gate.py recibeadapterdeJUnit/CLI, éste tieneque declararPYTEST/CLIderived/noPlaywright y cadaestadoderivarse deejecuciónreal, NOinventarE2Eraw/URL/verdeM3; agente puededeclararmismogategreenacotado delcomponente yfullM3pending. NoGPU/Ollama/servicios/audio/browser. ROOTmainGreen6realpreexistente4L2B/seamtrustednoinstalledIPC,JS5.0.3TS/CombinedN-Areal/D13/cohortrights/música/T06full/Verificaciónfull pendientes. CanonG/Tabsente,CASdespuésQAyactualpreimages. IAactualNULL.


## T-06 — adopción del componente CLI/CPU tras revisión3 y QA independiente — 2026-10-12T16:39:45.568048+00:00

ROOT verificó398payloadsQA/153sources/6216support/37ROOTrefs, sources G=e18dd17b/T9fb5c1c exactos y canonicalambosABSENT antesCASexclusive. LiteralUVexacto ejecutado porQA conPREPOST153propios yimport.snapshot/.venvreal;116PASS1SKIP73.48s y observado76.99s. CoverageQAcalificada88.42s116PASS1SKIP, antesimportG/harnessPythonCoverageentry hashesPREPOST/configsourcePREPOST, rawwhole738/833L397/484B0excl,≥80sinmedias/omit/pragmas/partial. Gatekitrealexit0 sobreJUnitrealadaptadoPYTESTnoE2E116pass0fail0flaky1skip. FreshA3/B3FULL0gaps. ReportmdPDF398manifestexactos; PDF12pagesestructura/renderexit0,NOrasterlayoutclaim. Todosfallosdeauditor/preparationpriorpreservados,no fakeproducerpermission.

ROOTCAS adoptó sóloG/T exactSHA conxb(nooverwrite), másQAresumen público sinrutas personales: testing/cohort-metrics-instrument-qa-2026-10-12.md. Instrumento parcialCPUaceptado; criterioT06instrumentoantesFase1sigueunticked hastaorquestación/perfilesoficiales/Verificaciónestrictafasecompleta. Standalonepending2sincollector,JS5.0.3TS/CombinedN-Aoficial/installedIPC/cohortderechosD13/música/UI/GPU/cierreT06/M3pendientes. IAactualNULL. ReciboROOTcohort-metrics-t06-instrument-acceptance-root-20261012.


## T-06 — componente implementado y publicado — 2026-10-12T16:54:04.001126+00:00

ROOT adoptó scripts/m3_coverage_gate.py e18dd17b y tests/test_m3_coverage_gate.py 9fb5c1c tras reviews3 A/B FULL sin gaps y QA independiente116PASS1SKIP. QA propia:738/833 líneas,397/484 ramas,1135/1317 total,0exclusiones; PRE/POST153 y398payloads auditados. Literal exacta/coverage/qa-gate0; componente sinUI. PDF12páginas generado sin verificación raster independiente declarada. Adopción .cache/dev-cycle/m3/cohort-metrics-t06-instrument-acceptance-root-20261012/ROOT-acceptance.receipt.json.

Commit aislado8cdc90c429891a8a7318f90a088657dad468c279 publicado rama m3/t-06-cohort-instrument,3archivos allowlist exactos incluyendo informe público. Worktree compartido mantiene HEAD603e7c83/rama m1/t-02-esquema/índice intacto; no merge a main con tarea abierta. Publicación .cache/dev-cycle/m3/cohort-metrics-t06-instrument-git-root-20261012/ROOT-published-component.receipt.json. Criterio integral T06 sin marcar: integración observador instalado/JS5.0.3/TSmapper/CombinedN-A reales/D13/Verificación y producto pendientes; ninguna función audiovisual cerrada por componente CPU.


## T-06 — siguiente unidad técnica: colector Python externo — 2026-10-12T17:14:06.498495+00:00

ROOT incorpora dosficheros al alcance de T06 porque el criterio integral ya exige orquestación independiente: scripts/m3_coverage_collect.py y tests/test_m3_coverage_collect.py. Es implementación CM-O1/P1/ADR0087 vigente, no nuevo diseño ni cambio de schemas/gate. G e18dd17b/T9fb5c1c aceptados permanecen readonly. Componente mínimo:un packagePython/una plataforma/unrunneroficial conramasreales/wholeárbolescompletos y dosmódulos (cambiado+producciónno modificada); sinuniónrequerida conforme CM197. CallerROOTexterno confiado preaprobado fuera runtimeevaluado, registros sóloenmemoria despuésobservacionesreales, __main__G seamactual. Ningunaautoridad porJSON/argv/env/ficherodeimportdinámico/bool/SyntheticObserver.

Fuente bootstrap/collector nuevo no certifica su propia evaluación; ROOTmedirá candidato con observador externo independiente actual y fuentes/tools/pinscontrastados, seguido revisiónfresh/QA. Runtime nuevo requiere TDD/whole80 propio/noexcl. JS5.0.3/TSmapper/Combined/N-Areal/D13/Verificaciónintegral/T06full siguenpendientes. No instalación niUI/GPUservicios por estaunidad; canon/ledger/Git sóloROOT, implementerprivate2owned.


## T-06 — recolector Python privado y medición externa — 2026-10-12T18:14:12.908507+00:00

Implementer entrega dos nuevas fuentes congeladas: scripts/m3_coverage_collect.py f908b0c6 y tests/test_m3_coverage_collect.py f17e73fd;18readonly intactos. AuditoríaROOT de5343payloads SHA/bytes/nlink del manifiesto final2. Actor150PASS1SKIP y literalG116PASS1SKIP son evidencias privadas conservadas, no autorización propia. Alcance mínimo: un paquete/plataforma Python con producción existente modificada y no modificada; added/deleted/rename/config-test se rechazan; hook efectivo byte-ratificado obligatorio. GateG/T aceptados siguen readonly.

ROOT independiente midió el recolector completo con Coverage7.16.2 antes de importarlo:34PASS,290/309líneas (93.8511%),80/94ramas(85.1064%),370/403total(91.8114%),0exclusiones/partial/omit.21fuentes PREPOST iguales. Primera copia omitió dependencia scripts/test_workspace.py y falló en colección sin crédito; segunda copia la fijó readonly. La generaciónJSON tuvo opciones tras source y falló; se corrigió únicamente argv de report, conservando raw/fallo sin repetir tests. Recibo cohort-metrics-t06-python-collector-outer2-root-20261012/ROOT-outer-result.receipt.json.

Pendiente bootstrapROOT propio preaprobado fuera del runtime de fixture, revisión fresca/QA/CAS del recolector. No nuevo código canónico adoptado. InstrumentoG/T previamente publicado8cdc90c4 permanece; JS5.0.3/mapperTS/Combined/N-A reales/D13/derechos/cohorte musical/Verificaciónintegral/T06/M3 siguen pendientes. IAactualNULL.


## T-06 — revisión de dos lentes, intento 1 del recolector — 2026-10-12T18:31:26.588311+00:00

ROOTbootstrap propio preaprobado fuera de dosmódulos evaluados: fuentes/tools/argv/environment/outputs fijados antesimportcollector; callback contrasta bytes/bindingsantesA/E0/runner. RealUVpytestwhole2módulos4ramas y __main__G pass0; mismosartefactosstandalonepending2ROOT_CUSTODY_MISSING. Recibo cohort-metrics-t06-python-collector-bootstrap-root-20261012/ROOT-real-bootstrap.receipt.json. Observaciónreal sólofixtureCPU, sin conformidad musical ni certificación propia del recolector.

RevisiónA1/B1 fresca21SHAexactos:0Critical/2Important/0Minor. A01 CM177exige rawexternoalárbol;collector265–266/312genera candidate/src/coverage.json/effective-raw.json y omiteesos2paths501 durantecaptura, trasladándolos639–677despuéswait. CM464a la vezfijaargrelativoconcwdcandidate; noADRprevioexceptúa177. ROOToperationalallow2outputs NOesnormativeoverride. B01 collector517–520 timeout60mata sóloUV,segundo communicate sin timeout:pytestdescendantpropiofinito65scontinúavivo yvuelve66s;stdoutstderr/custodiano persistidos. ProbeB1actualsourcebyteexact/argvUVliteral ymarkerreal, rawpreservado. ROOTcontrasta código/textos/recibo y aceptaambosgaps, sinrebate.

FULLA1incluye15criterioscomponentes+6comunes+11integrales yFULLB1tabla18;informes lens-a1-root.md/lens-b1-root.md encohort-metrics-t06-python-collector-review1-root-20261012. Arquitecto fresco design_m3_collector_outputs_custody activo sólo privado coveragecorrection-design para comparar salidasabsolutasexternas/staging/excepción ycustodiaárbolpropio; ROOTelijeporautorizaciónautónoma delusuario. ADR0088reservadopropuesta,nadaadoptado. No código corrective ni cambiosnormativos hasta decisión concretarevisada; despuésTDDfix1/ROOTactualpruebas/review2/QA/CAS. Collectorcanonicalausente/T06M3integralabiertos.


## T-06 — opción O1 para corregir salidas y custodia — 2026-10-12T18:50:27.414776+00:00

ROOT elige O1 bajo la delegación autónoma del propietario: salidas absolutas externas desde nacimiento y OwnedProcess/Job propio Windows ya existente, sin ampliar API/admisiones/readers. Arquitecto compara O1/O2staging/O3excepcióninternayentrega diseño aprobadoROOT+ADR0088propuesta+CMcandidato2f9c0bef/índice4a98b593.17readonly PREPOSTexactos/41checks/93links/65schemas11readers3bloquesCM intactos;10payloadsfinales auditados. Norma canónica aún6cc06770, código collector f908/f17sigueprivado/noaceptado; A01/B01Important permanecen hasta norma+runtimecorregidos y pruebasnuevas.

Archivos incorpora ADR0088 y Factory/tests scripts/eval/m3_coverage_runner.py y scripts/eval/tests/test_m3_coverage_runner.py por el defecto causal de árboltimeout. Es concreto del instrumento existente; no serviciosmodelosniGPU. Próximo revisiónA/B documental/QA/adopciónnormativaROOT antesfix1freshTDD. Windowsprimerbackend;Linux/Dockerpending sinfallbackni fakeportableclaim. CM/ADR/índice nuevos se revisan como corte distinto, manteniendo oldraw/sourceSHA. IAactualNULL/T06M3integralabiertos.


## T-06: normativa O1 revisada y QA documental en curso — 2026-10-12T19:13:31.978219+00:00

NormReview1 frescoA0Critical0Important1Minor índiceADR88filaaislada;B0gaps. FULLtablas e incidenciascheckers ennormative-review1/lens-a1-root.md/lens-b1-root.md. ROOT mueve sólolamismafila albloquecontiguoheaderADR, demásbytesexactos;A recheckconfirma0gaps/20SHA/otros19intactos. CM2f9c0bef,ADR88propuestade8e6c98,índicef92b8f2c. Arquitecto17PREPOST/10payloads/41checks;sourceG/Tsinchange. PrivateGitbaseaddlongpathfallóantescandidatecopy, recuperacióncore.longpathsLOCALprivado,sinGitcompartido. QAindexpreflightafter87fallóantesindexwrite (historicalrowsblankseparated), recoveryfirstheadertablepreservaotrosbytes.

QA documental independiente qa_m3_collector_normative_current_1 activa ennormative-qa1-root-20261012/qa-worker,20snapshotRO. Sólocomponenteprosa/sinUI/noruntime; gateDOC_CHECKS_DERIVED explícito,noPlaywright. Primercoveragecheckerleyóshared47diffreadonly/sincrédito; rerunaisladoGIT_CEILING/componentplan. LinkscannerQA91realesresueltosfrente93previosscope/regex eninvestigación,nofabricarlíneasparaigualar. CanonCM6cc/ADR88ausente hastaQA+ROOTadopción. NuevaFactory/runtimefixA01B01TDD/rootNative/whole80/review2QA/CASsiguenpendientes. NingúncierreT06M3niinstrumentointegral/D13.


## T-06 — ratificación ADR0088 tras QA documental — 2026-10-12T19:17:22.666677+00:00

ROOTaudita36payloadsQA/20snapshotSHA/84checksDOC_CHECKS_DERIVED/qa-gateexit0.65schemas11readers3codeblocksintactos,91linksnormativosvs93incluyendodesign2links extra,fixture39/6/7sinruntimeauthority. FreshA/B0gapsdespuésMinoríndicecorregido. Adoptados CM/ADR88/índicecontra6cc/c933preimágenesyADRantesabsent;metadatospropuesta→aceptada ytextoestado ratificado porROOTdocumentadoscomo5splices,ningúnschema/cláusulatécnicacambia. QA SHApropuestos2f9/de8/f92quedaninmutables, nofingirQAdebytesratificadosidénticos. Informe público testing/cohort-metrics-collector-normative-qa-2026-10-12.md. PDF11markersfirmaEOF/noparserfullnoraster.

Sigueunitpartial/noT06M3closure. NuevaFactory+collectorfix1 TDD causalantesfuncional,NativeROOTownprocessJobactual/whole80permodule/review2/QA/CASpendientes. Diagnóstico UNKNOWN/fallosnoECPsuccess. Sourcef908/f17+rawsold conservados; noadopciónruntimeporestadecisión. UsoIAactualNULL.


## Parada solicitada: norma publicada y corrección runtime parcial — 2026-10-12T19:32:07.616370+00:00

La norma O1/ADR88 está ratificada tras revisión documental A/B sin gaps pendientes y QA84/84. Publicada en rama `m3/t-06-colector-norma`, commit15878b5fc4b4313bdee8948035eac50e649281d5, cuatro archivos permitidos; remoto verificado, HEAD603e7c83/rama compartida/index intactos. El diff-check inicial rechazó una línea vacía al final del índice: ROOT retiró sólo saltos de línea sobrantes, preservando contenido y recibo de aceptación previo. Recibo de publicación califica este cambio de formato posterior a QA.

FIX1 runtime permanece privado en `cohort-metrics-t06-python-collector-fix1-root-20261012/`. RED funcional2 y ausenciaFactory1 conservados; GREEN1 tres y GREEN2 36PASS24,88s. ROOT verifica23readonly intactos y4fuentes finales contra `actor-stop-checkpoint.json`. Job/cierre modelados CPU: sin custodia Native. Tests nuevos del runner añadidos después de GREEN2 aún sin ejecutar; lint, whole80, freeze, pruebas Windows ROOT, revisión2 y QA pendientes. No adopción runtime ni cierreT06/M3;JS/TSmapper,Combined/N-A,D13/producto siguen pendientes. Actor detenido por petición del propietario, sin prueba propia activa.
